import json
from pathlib import Path
import numpy as np
import pandas as pd

ANOMALY_PATH = Path("data/anomaly_predictions.csv")
GRAPH_PATH = Path("graph_engine/data/graph_risk_scores.json")
OUTPUT_PATH = Path("data/final_risk_scores.csv")


def compute_spatial_risk(gps_mismatch_km: pd.Series) -> pd.Series:
    """Convert EXIF GPS distance mismatch (km) into a 0-100 visual/spatial risk score."""
    return np.clip((gps_mismatch_km / 10.0) * 100.0, 0.0, 100.0)


def assign_risk_band(cri: float) -> str:
    if cri >= 70.0:
        return "RED"
    if cri >= 35.0:
        return "YELLOW"
    return "GREEN"


def build_composite_risk() -> None:
    if not ANOMALY_PATH.exists():
        raise FileNotFoundError(f"Missing {ANOMALY_PATH}. Run anomaly_models.py first.")
    if not GRAPH_PATH.exists():
        raise FileNotFoundError(f"Missing {GRAPH_PATH}. Run git pull origin main first.")

    ml_df = pd.read_csv(ANOMALY_PATH)

    with GRAPH_PATH.open("r", encoding="utf-8") as f:
        graph_raw = json.load(f)

    # Handle either a top-level list or {"scores": [...]} wrapper
    graph_records = graph_raw["scores"] if isinstance(graph_raw, dict) and "scores" in graph_raw else graph_raw
    graph_df = pd.DataFrame(graph_records)

    # Keep relevant columns from Member 3
    keep_cols = [c for c in ["project_id", "relational_graph_risk", "risk_level", "flags"] if c in graph_df.columns]
    graph_df = graph_df[keep_cols].rename(columns={"risk_level": "graph_risk_level", "flags": "graph_flags"})

    merged = ml_df.merge(graph_df, on="project_id", how="left")
    merged["relational_graph_risk"] = merged["relational_graph_risk"].fillna(0.0)
    merged["spatial_risk_score"] = np.round(compute_spatial_risk(merged["gps_mismatch_km"]), 2)

    # E-NETRA Composite Risk Index: 40% Financial ML + 30% Vendor Graph + 30% Spatial/EXIF
    merged["composite_risk_index"] = np.round(
        (0.40 * merged["ml_risk_score"])
        + (0.30 * merged["relational_graph_risk"])
        + (0.30 * merged["spatial_risk_score"]),
        2,
    )
    merged["cri_band"] = merged["composite_risk_index"].apply(assign_risk_band)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(merged)} unified project risk scores to {OUTPUT_PATH}")
    print("\nRisk Band Distribution:")
    print(merged["cri_band"].value_counts().to_string())
    print("\nTop 10 Highest-CRI Projects:")
    cols = [
        "project_id",
        "ml_risk_score",
        "relational_graph_risk",
        "spatial_risk_score",
        "composite_risk_index",
        "cri_band",
    ]
    print(merged.sort_values("composite_risk_index", ascending=False)[cols].head(10).to_string(index=False))


if __name__ == "__main__":
    build_composite_risk()