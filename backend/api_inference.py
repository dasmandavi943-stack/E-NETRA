import os
from pathlib import Path
from typing import List
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.src.anomaly_models import FinancialAnomalyDetector
from app.src.risk_scorer import calculate_composite_risk

MODEL_PATH = Path(os.getenv("ML_MODEL_PATH", "app/models/isolation_forest_v1.joblib"))
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app = FastAPI(
    title="E-NETRA ML & Composite Risk Scoring API",
    version="1.0.0",
    description="Financial anomaly detection and Composite Risk Index (CRI) endpoints for MPLAD monitoring.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProjectFinancialInput(BaseModel):
    project_id: str = Field(..., min_length=1)
    sanctioned_amount: float = Field(..., gt=0)
    estimated_cost: float = Field(..., ge=0)
    disbursed_amount: float = Field(..., ge=0)
    unit_rate_billed: float = Field(..., ge=0)
    sor_benchmark_rate: float = Field(..., gt=0)
    planned_days: float = Field(..., gt=0)
    actual_days_elapsed: float = Field(..., ge=0)
    physical_progress_pct: float = Field(..., ge=0, le=100)


class FinancialAnomalyResponse(BaseModel):
    project_id: str
    financial_risk_score: float
    is_anomaly: bool
    top_reasons: List[str]


class CompositeRiskRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    financial_score: float = Field(..., ge=0, le=100)
    graph_score: float = Field(..., ge=0, le=100)
    visual_score: float = Field(..., ge=0, le=100)


class CompositeRiskResponse(BaseModel):
    project_id: str
    cri_score: float
    risk_band: str
    recommended_action: str
    component_scores: dict


def _bootstrap_fallback_detector() -> FinancialAnomalyDetector:
    """Train a baseline model on synthetic records if no pre-saved artifact exists yet."""
    rng = np.random.default_rng(42)
    n = 300
    df = pd.DataFrame(
        {
            "sanctioned_amount": rng.uniform(500_000, 5_000_000, n),
            "estimated_cost": rng.uniform(480_000, 5_100_000, n),
            "disbursed_amount": rng.uniform(100_000, 4_500_000, n),
            "unit_rate_billed": rng.uniform(900, 1200, n),
            "sor_benchmark_rate": np.full(n, 1000.0),
            "planned_days": rng.integers(60, 365, n).astype(float),
            "actual_days_elapsed": rng.integers(30, 380, n).astype(float),
            "physical_progress_pct": rng.uniform(10, 100, n),
        }
    )
    detector = FinancialAnomalyDetector().fit(df)
    detector.save(MODEL_PATH)
    return detector


@app.on_event("startup")
def load_artifacts() -> None:
    try:
        if MODEL_PATH.exists():
            app.state.detector = FinancialAnomalyDetector.load(MODEL_PATH)
        else:
            app.state.detector = _bootstrap_fallback_detector()
        app.state.model_ready = True
    except Exception as exc:
        app.state.detector = None
        app.state.model_ready = False
        app.state.startup_error = str(exc)


@app.get("/health")
def health_check():
    if not getattr(app.state, "model_ready", False):
        raise HTTPException(
            status_code=503,
            detail=f"Model unavailable: {getattr(app.state, 'startup_error', 'not loaded')}",
        )
    return {"status": "ok", "model_loaded": True, "model_path": str(MODEL_PATH)}


@app.post("/predict/financial-anomaly", response_model=FinancialAnomalyResponse)
def predict_financial_anomaly(payload: ProjectFinancialInput):
    if not getattr(app.state, "model_ready", False) or app.state.detector is None:
        raise HTTPException(status_code=503, detail="Anomaly detection model is not ready.")

    score, is_anomaly, reasons = app.state.detector.predict_single(payload.model_dump())
    return FinancialAnomalyResponse(
        project_id=payload.project_id,
        financial_risk_score=score,
        is_anomaly=is_anomaly,
        top_reasons=reasons,
    )


@app.post("/calculate-risk-score", response_model=CompositeRiskResponse)
def calculate_risk_score(payload: CompositeRiskRequest):
    result = calculate_composite_risk(
        financial_score=payload.financial_score,
        graph_score=payload.graph_score,
        visual_score=payload.visual_score,
    )
    return CompositeRiskResponse(
        project_id=payload.project_id,
        cri_score=result["cri_score"],
        risk_band=result["risk_band"],
        recommended_action=result["recommended_action"],
        component_scores=result["component_scores"],
    )
