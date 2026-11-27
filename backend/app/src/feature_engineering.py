import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "budget_variance_ratio",
    "sor_deviation_index",
    "execution_delay_ratio",
    "disbursement_velocity",
    "disbursement_to_progress_gap",
]


def engineer_financial_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform raw MPLAD project/transaction records into numerical ML features.

    Expected input columns:
      - sanctioned_amount (float)
      - estimated_cost (float)
      - disbursed_amount (float)
      - unit_rate_billed (float)
      - sor_benchmark_rate (float)
      - planned_days (int/float)
      - actual_days_elapsed (int/float)
      - physical_progress_pct (float, 0 to 100)
    """
    data = df.copy()

    sanctioned = data["sanctioned_amount"].replace(0, np.nan)
    planned_days = data["planned_days"].replace(0, np.nan)
    sor_rate = data["sor_benchmark_rate"].replace(0, np.nan)

    # 1. Budget Variance Ratio
    data["budget_variance_ratio"] = (
        (data["sanctioned_amount"] - data["estimated_cost"]).abs() / sanctioned
    ).fillna(0.0)

    # 2. Schedule of Rates (SoR) Deviation Index
    data["sor_deviation_index"] = (
        (data["unit_rate_billed"] - data["sor_benchmark_rate"]) / sor_rate
    ).fillna(0.0)

    # 3. Execution Velocity Delta (positive means slower than planned)
    data["execution_delay_ratio"] = (
        (data["actual_days_elapsed"] - data["planned_days"]) / planned_days
    ).fillna(0.0)

    # 4. Disbursement Velocity (fraction of sanctioned funds released per day elapsed)
    days_safe = np.maximum(data["actual_days_elapsed"], 1.0)
    data["disbursement_velocity"] = (
        (data["disbursed_amount"] / sanctioned) / days_safe
    ).fillna(0.0)

    # 5. Gap between funds disbursed (%) and physical completion (%)
    disbursed_pct = ((data["disbursed_amount"] / sanctioned) * 100.0).fillna(0.0)
    data["disbursement_to_progress_gap"] = (
        disbursed_pct - data["physical_progress_pct"]
    )

    return data[FEATURE_COLUMNS].replace([np.inf, -np.inf], 0.0).fillna(0.0)
