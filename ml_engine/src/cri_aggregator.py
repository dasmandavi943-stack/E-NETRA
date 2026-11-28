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
    if cri >= 60.0:
        return "RED"
    if cri >= 35.0:
        return "YELLOW"
    return "GREEN"


def build_audit_summary(row: pd.Series) -> str:
    """Combine financial, relational graph, and spatial flags into one readable string."""
    notes = []
    if row.get("cost_overrun_ratio", 1.0) >= 1.5:
        notes.append(f"Cost overrun {row['cost_overrun_ratio']:.2f}x")
    if row.get("duration_days", 30) <= 7 and row.get("release_ratio", 0.0) >= 0.85:
        notes.append(f"Rapid payout ({int(row['duration_days'])}d)")
    if row.get("near_threshold_flag", 0) == 1:
        notes.append("Split tender (<₹5L)")
    if row.get("vendors_per_bank", 1) > 1:
        notes.append(f"Shared bank ({int(row['vendors_per_bank'])} vendors)")

    graph_flags = row.get("graph_flags", "")
    if isinstance(graph_flags, list) and graph_flags:
        notes.extend([str(f) for f in graph_flags if f != "No collusion anomalies detected"])
    elif isinstance(graph_flags, str) and graph_flags.strip() not in ("", "[]", "None", "nan"):
        notes.append(graph_flags.strip())

    if row.get("gps_mismatch_km", 0.0) >= 1.0:
        notes.append(f"GPS mismatch {row['gps_mismatch_km']:.1f} km")

    return " | ".join(dict.fromkeys(notes)) if notes else "Normal audit parameters"


def build_composite_risk() -> None:
    if not ANOMALY_PATH.exists():
        raise FileNotFoundError(f"Missing {ANOMALY_PATH}. Run anomaly_models.py first.")
    if not GRAPH_PATH.exists():
        raise FileNotFoundError(f"Missing {GRAPH_PATH}. Run git pull origin main first.")

    ml_df = pd.read_csv(ANOMALY_PATH)

    with GRAPH_PATH.open("r", encoding="utf-8") as f:
        graph_raw = json.load(f)

    graph_records = graph_raw["scores"] if isinstance(graph_raw, dict) and "scores" in graph_raw else graph_raw
    graph_df = pd.DataFrame(graph_records)

    keep_cols = [c for c in ["project_id", "relational_graph_risk", "risk_level", "flags"] if c in graph_df.columns]
    graph_df = graph_df[keep_cols].rename(columns={"risk_level": "graph_risk_level", "flags": "graph_flags"})

    # Normalize numeric ID suffix so MPLAD_1 and MPLAD_001 both match cleanly
    ml_df["_join_id"] = ml_df["project_id"].astype(str).str.extract(r"(\d+)")[0].astype(int)
    graph_df["_join_id"] = graph_df["project_id"].astype(str).str.extract(r"(\d+)")[0].astype(int)
    merged = ml_df.merge(graph_df.drop(columns=["project_id"]), on="_join_id", how="left").drop(columns=["_join_id"])

    merged["relational_graph_risk"] = merged["relational_graph_risk"].fillna(0.0)
    merged["spatial_risk_score"] = np.round(compute_spatial_risk(merged["gps_mismatch_km"]), 2)

    merged["composite_risk_index"] = np.round(
        (0.40 * merged["ml_risk_score"])
        + (0.30 * merged["relational_graph_risk"])
        + (0.30 * merged["spatial_risk_score"]),
        2,
    )
    merged["cri_band"] = merged["composite_risk_index"].apply(assign_risk_band)
    merged["audit_summary"] = merged.apply(build_audit_summary, axis=1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved {len(merged)} unified project risk scores to {OUTPUT_PATH}")
    print("\nRisk Band Distribution:")
    print(merged["cri_band"].value_counts().to_string())


if __name__ == "__main__":
    build_composite_risk()