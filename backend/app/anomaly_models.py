from pathlib import Path
from typing import Any, Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.src.feature_engineering import FEATURE_COLUMNS, engineer_financial_features


class FinancialAnomalyDetector:
    """Unsupervised Isolation Forest wrapper with feature scaling and explanations."""

    def __init__(self, contamination: float = 0.05, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=150,
            contamination=self.contamination,
            random_state=self.random_state,
        )
        self.is_fitted = False

    def fit(self, raw_df: pd.DataFrame) -> "FinancialAnomalyDetector":
        features = engineer_financial_features(raw_df)
        scaled = self.scaler.fit_transform(features)
        self.model.fit(scaled)
        self.is_fitted = True
        return self

    def predict_single(self, record: Dict[str, Any]) -> Tuple[float, bool, List[str]]:
        """
        Return (financial_risk_score_0_to_100, is_anomaly, top_reasons).
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted or loaded.")

        df = pd.DataFrame([record])
        features = engineer_financial_features(df)
        scaled = self.scaler.transform(features)[0]

        raw_decision = float(self.model.decision_function([scaled])[0])
        pred_label = int(self.model.predict([scaled])[0])

        normalized = np.clip((0.15 - raw_decision) / 0.35, 0.0, 1.0)
        risk_score = round(float(normalized * 100.0), 2)
        is_anomaly = pred_label == -1 or risk_score >= 70.0

        z_magnitudes = np.abs(scaled)
        ranked_indices = np.argsort(z_magnitudes)[::-1]

        reason_map = {
            "budget_variance_ratio": f"High budget variance ({features.iloc[0]['budget_variance_ratio']:.2f})",
            "sor_deviation_index": f"Rate deviation from SoR ({features.iloc[0]['sor_deviation_index']:.2f})",
            "execution_delay_ratio": f"Schedule delay ratio ({features.iloc[0]['execution_delay_ratio']:.2f})",
            "disbursement_velocity": f"Unusual fund disbursement pace ({features.iloc[0]['disbursement_velocity']:.4f}/day)",
            "disbursement_to_progress_gap": f"Fund vs. progress gap ({features.iloc[0]['disbursement_to_progress_gap']:.1f}%)",
        }

        reasons: List[str] = []
        for idx in ranked_indices[:3]:
            col_name = FEATURE_COLUMNS[idx]
            if z_magnitudes[idx] > 1.0:
                reasons.append(reason_map[col_name])

        if not reasons:
            reasons.append("Transaction metrics within expected baseline range")

        return risk_score, is_anomaly, reasons

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "scaler": self.scaler,
                "model": self.model,
                "contamination": self.contamination,
                "random_state": self.random_state,
            },
            target,
        )

    @classmethod
    def load(cls, path: str | Path) -> "FinancialAnomalyDetector":
        bundle = joblib.load(path)
        instance = cls(
            contamination=bundle.get("contamination", 0.05),
            random_state=bundle.get("random_state", 42),
        )
        instance.scaler = bundle["scaler"]
        instance.model = bundle["model"]
        instance.is_fitted = True
        return instance
    