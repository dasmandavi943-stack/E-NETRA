from fastapi.testclient import TestClient
from app.src.api_inference import app


def test_health_endpoint():
    with TestClient(app) as c:
        res = c.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


def test_predict_financial_anomaly_valid():
    payload = {
        "project_id": "MPLAD-2026-001",
        "sanctioned_amount": 2500000.0,
        "estimated_cost": 2450000.0,
        "disbursed_amount": 1200000.0,
        "unit_rate_billed": 1020.0,
        "sor_benchmark_rate": 1000.0,
        "planned_days": 180,
        "actual_days_elapsed": 90,
        "physical_progress_pct": 50.0,
    }
    with TestClient(app) as c:
        res = c.post("/predict/financial-anomaly", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["project_id"] == "MPLAD-2026-001"
        assert 0.0 <= body["financial_risk_score"] <= 100.0
        assert isinstance(body["is_anomaly"], bool)
        assert isinstance(body["top_reasons"], list)


def test_calculate_risk_score_bands():
    with TestClient(app) as c:
        red_res = c.post(
            "/calculate-risk-score",
            json={
                "project_id": "MPLAD-2026-009",
                "financial_score": 85.0,
                "graph_score": 80.0,
                "visual_score": 75.0,
            },
        )
        assert red_res.status_code == 200
        assert red_res.json()["risk_band"] == "RED"
        assert red_res.json()["cri_score"] == 80.5

        green_res = c.post(
            "/calculate-risk-score",
            json={
                "project_id": "MPLAD-2026-010",
                "financial_score": 15.0,
                "graph_score": 20.0,
                "visual_score": 10.0,
            },
        )
        assert green_res.status_code == 200
        assert green_res.json()["risk_band"] == "GREEN"


def test_validation_error_on_invalid_score():
    with TestClient(app) as c:
        res = c.post(
            "/calculate-risk-score",
            json={
                "project_id": "MPLAD-BAD",
                "financial_score": 150.0,
                "graph_score": 20.0,
                "visual_score": 10.0,
            },
        )
        assert res.status_code == 422
