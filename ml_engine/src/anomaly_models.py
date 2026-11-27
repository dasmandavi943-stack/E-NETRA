from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

INPUT_PATH = Path("data/engineered_features.csv")
MODEL_PATH = Path("ml_engine/models/isolation_forest.joblib")
SCALER_PATH = Path("ml_engine/models/feature_scaler.joblib")
REPORT_PATH = Path("data/anomaly_predictions.csv")

FEATURE_COLS = [
    "cost_overrun_ratio",
    "release_ratio",
    "category_cost_zscore",
    "duration_days",
    "payout_per_day",
    "vendors_per_bank",
    "near_threshold_flag",
    "gps_mismatch_km",
]


def train_and_score(df: pd.DataFrame) -> pd.DataFrame:
    """Train Isolation Forest on engineered MPLADS features and compute 0-100 risk scores."""
    X = df[FEATURE_COLS].fillna(0.0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Contamination ~0.09 matches the ~9% injected anomaly rate (45 of 500 rows)
    model = IsolationForest(
        n_estimators=200,
        contamination=0.09,
        random_state=42,
    )
    preds = model.fit_predict(X_scaled)  # -1 = anomaly, 1 = normal
    raw_scores = -model.decision_function(X_scaled)  # higher = more anomalous

    # Normalize raw scores into a clean 0-100 Financial & Operational Risk Score
    min_s, max_s = raw_scores.min(), raw_scores.max()
    risk_score = ((raw_scores - min_s) / (max_s - min_s + 1e-9)) * 100.0

    result = df.copy()
    result["is_anomaly"] = (preds == -1).astype(int)
    result["ml_risk_score"] = np.round(risk_score, 2)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    return result


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing {INPUT_PATH}. Run feature_engineering.py first.")

    df = pd.read_csv(INPUT_PATH)
    scored_df = train_and_score(df)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    scored_df.to_csv(REPORT_PATH, index=False)

    flagged = scored_df[scored_df["is_anomaly"] == 1].sort_values("ml_risk_score", ascending=False)
    print(f"Trained IsolationForest & saved artifacts to {MODEL_PATH.parent}")
    print(f"Total records scored: {len(scored_df)} | Flagged anomalies: {len(flagged)}")
    print("\nTop 10 Highest-Risk Flagged Projects:")
    display_cols = [
        "project_id",
        "work_category",
        "sanctioned_amount",
        "cost_overrun_ratio",
        "gps_mismatch_km",
        "ml_risk_score",
    ]
    print(flagged[display_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()