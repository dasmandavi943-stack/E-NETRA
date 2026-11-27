from pathlib import Path
from typing import List
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ml_engine.src.feature_engineering import build_features

MODEL_PATH = Path("ml_engine/models/isolation_forest.joblib")
SCALER_PATH = Path("ml_engine/models/feature_scaler.joblib")
DATASET_PATH = Path("data/mplads_master_dataset.csv")

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

app = FastAPI(title="E-NETRA Financial ML Inference API", version="1.0.0")


class ProjectRecord(BaseModel):
    project_id: str
    mp_name: str
    district: str
    work_category: str
    estimated_cost: float
    sanctioned_amount: float
    amount_released: float
    sanction_date: str
    completion_date: str
    status: str
    vendor_id: str
    vendor_name: str
    vendor_address: str
    vendor_phone: str
    bank_account_id: str
    site_lat: float
    site_lon: float
    photo_lat: float
    photo_lon: float
    photo_path: str


class FinancialPredictionResponse(BaseModel):
    project_id: str
    is_anomaly: bool
    financial_risk_score: float
    reasons: List[str]


def generate_reasons(row: pd.Series) -> List[str]:
    """Generate human-readable audit flags explaining why a project scored high risk."""
    reasons = []
    if row["cost_overrun_ratio"] >= 1.5:
        reasons.append(f"Sanctioned cost is {row['cost_overrun_ratio']:.2f}x the initial estimate")
    if row["category_cost_zscore"] >= 2.0:
        reasons.append(f"Cost is significantly above {row['work_category']} category average")
    if row["duration_days"] <= 7 and row["release_ratio"] >= 0.85:
        reasons.append(
            f"Rapid disbursement: {row['release_ratio']*100:.0f}% released within {int(row['duration_days'])} days"
        )
    if row["vendors_per_bank"] > 1:
        reasons.append(f"Shared bank account linked to {int(row['vendors_per_bank'])} distinct vendors")
    if row["near_threshold_flag"] == 1:
        reasons.append("Sanctioned amount sits just below the ₹5 Lakh tender threshold")
    if row["gps_mismatch_km"] >= 1.0:
        reasons.append(f"Site photo GPS is {row['gps_mismatch_km']:.1f} km away from official project site")

    if not reasons:
        reasons.append("Within normal financial and operational parameters")
    return reasons


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model_loaded": MODEL_PATH.exists() and SCALER_PATH.exists(),
    }


@app.post("/predict/financial", response_model=FinancialPredictionResponse)
def predict_financial_risk(record: ProjectRecord):
    if not MODEL_PATH.exists() or not SCALER_PATH.exists():
        raise HTTPException(status_code=503, detail="Model artifacts not found. Run anomaly_models.py first.")

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    incoming_df = pd.DataFrame([record.model_dump()])
    if DATASET_PATH.exists():
        base_df = pd.read_csv(DATASET_PATH)
        combined_df = pd.concat([base_df, incoming_df], ignore_index=True)
    else:
        combined_df = incoming_df

    featured_df = build_features(combined_df)
    target_row = featured_df.iloc[-1:]

    X_scaled = scaler.transform(target_row[FEATURE_COLS].fillna(0.0))
    pred = int(model.fit_predict(X_scaled)[0]) if len(featured_df) == 1 else int(model.predict(X_scaled)[0])
    raw_score = float(-model.decision_function(X_scaled)[0])

    normalized_score = float(np.clip((raw_score + 0.15) / 0.35 * 100.0, 0.0, 100.0))

    return FinancialPredictionResponse(
        project_id=record.project_id,
        is_anomaly=(pred == -1),
        financial_risk_score=round(normalized_score, 2),
        reasons=generate_reasons(target_row.iloc[0]),
    )