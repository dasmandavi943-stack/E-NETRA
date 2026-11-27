from pathlib import Path
import numpy as np
import pandas as pd

INPUT_PATH = Path("data/mplads_master_dataset.csv")
OUTPUT_PATH = Path("data/engineered_features.csv")


def compute_haversine_km(lat1: pd.Series, lon1: pd.Series, lat2: pd.Series, lon2: pd.Series) -> pd.Series:
    """Calculate distance in kilometers between site coordinates and uploaded photo coordinates."""
    r = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    return 2 * r * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer numerical risk indicators from the master MPLADS dataset."""
    data = df.copy()

    # 1. Financial Ratios (safe against division by zero)
    est_safe = data["estimated_cost"].replace(0, np.nan)
    sanc_safe = data["sanctioned_amount"].replace(0, np.nan)

    data["cost_overrun_ratio"] = (data["sanctioned_amount"] / est_safe).fillna(1.0)
    data["release_ratio"] = (data["amount_released"] / sanc_safe).fillna(0.0)

    # 2. Category-Level Cost Z-Score (detects unusually expensive works for the same category)
    cat_mean = data.groupby("work_category")["sanctioned_amount"].transform("mean")
    cat_std = data.groupby("work_category")["sanctioned_amount"].transform("std").replace(0, np.nan)
    data["category_cost_zscore"] = ((data["sanctioned_amount"] - cat_mean) / cat_std).fillna(0.0)

    # 3. Timeline & Payout Speed
    sanction_dt = pd.to_datetime(data["sanction_date"], errors="coerce")
    completion_dt = pd.to_datetime(data["completion_date"], errors="coerce")
    data["duration_days"] = (completion_dt - sanction_dt).dt.days.clip(lower=1).fillna(30)
    data["payout_per_day"] = data["amount_released"] / data["duration_days"]

    # 4. Vendor & Threshold Signals
    data["vendors_per_bank"] = data.groupby("bank_account_id")["vendor_id"].transform("nunique")
    data["near_threshold_flag"] = (
        (data["sanctioned_amount"] >= 480000) & (data["sanctioned_amount"] < 500000)
    ).astype(int)

    # 5. Geolocation Distance (km between official site and photo EXIF GPS)
    data["gps_mismatch_km"] = compute_haversine_km(
        data["site_lat"], data["site_lon"], data["photo_lat"], data["photo_lon"]
    )

    return data


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {INPUT_PATH}. Run generate_data.py first.")

    raw_df = pd.read_csv(INPUT_PATH)
    featured_df = build_features(raw_df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    featured_df.to_csv(OUTPUT_PATH, index=False)

    feature_cols = [
        "project_id",
        "cost_overrun_ratio",
        "release_ratio",
        "category_cost_zscore",
        "duration_days",
        "vendors_per_bank",
        "gps_mismatch_km",
    ]
    print(f"Engineered features saved to {OUTPUT_PATH} ({len(featured_df)} rows).")
    print("\nSample engineered rows (including injected financial anomalies at index 10-14):")
    print(featured_df[feature_cols].iloc[8:15].to_string(index=False))


if __name__ == "__main__":
    main()