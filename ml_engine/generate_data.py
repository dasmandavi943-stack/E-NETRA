import random
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from faker import Faker

fake = Faker("en_IN")
random.seed(42)
np.random.seed(42)

NUM_ROWS = 500
OUTPUT_PATH = Path("data/mplads_master_dataset.csv")

CATEGORIES = {
    "Road": (400000, 1500000),
    "Water Tank": (150000, 600000),
    "School Room": (300000, 1200000),
    "Solar Light": (50000, 250000),
    "Community Hall": (500000, 2000000),
}

DISTRICTS = ["Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain"]
MP_NAMES = [
    "Shri Alok Sharma",
    "Smt. Sandhya Ray",
    "Shri Shankar Lalwani",
    "Shri Bharat Singh Kushwah",
    "Shri Anil Firojiya",
]

# Create a pool of 60 vendors
vendors = [
    {
        "vendor_id": f"VEND_{100 + i}",
        "vendor_name": f"{fake.last_name()} {random.choice(['Infra', 'Constructions', 'Enterprises', 'Builders', 'Engineering'])}",
        "vendor_address": fake.address().replace("\n", ", "),
        "vendor_phone": f"98{random.randint(10000000, 99999999)}",
        "bank_account_id": f"BANK_HASH_{1000 + i}",
    }
    for i in range(60)
]

rows = []
base_date = datetime(2025, 1, 1)

for i in range(1, NUM_ROWS + 1):
    category = random.choice(list(CATEGORIES.keys()))
    low, high = CATEGORIES[category]
    estimated_cost = round(random.uniform(low, high), -3)
    sanctioned_amount = round(estimated_cost * random.uniform(0.95, 1.08), -3)

    sanction_dt = base_date + timedelta(days=random.randint(0, 500))
    duration_days = random.randint(45, 240)
    completion_dt = sanction_dt + timedelta(days=duration_days)

    status = random.choices(
        ["Completed", "In Progress", "Sanctioned"], weights=[0.55, 0.30, 0.15]
    )[0]

    if status == "Sanctioned":
        amount_released = round(sanctioned_amount * random.uniform(0.10, 0.30), -3)
    elif status == "In Progress":
        amount_released = round(sanctioned_amount * random.uniform(0.40, 0.75), -3)
    else:
        amount_released = round(sanctioned_amount * random.uniform(0.90, 1.00), -3)

    vendor = random.choice(vendors)
    site_lat = round(random.uniform(22.5, 26.2), 4)
    site_lon = round(random.uniform(75.5, 80.5), 4)
    # Normal photo GPS is within ~20 meters of the site
    photo_lat = round(site_lat + random.uniform(-0.0002, 0.0002), 4)
    photo_lon = round(site_lon + random.uniform(-0.0002, 0.0002), 4)

    rows.append(
        {
            "project_id": f"MPLAD_{i:03d}",
            "mp_name": random.choice(MP_NAMES),
            "district": random.choice(DISTRICTS),
            "work_category": category,
            "estimated_cost": int(estimated_cost),
            "sanctioned_amount": int(sanctioned_amount),
            "amount_released": int(amount_released),
            "sanction_date": sanction_dt.strftime("%Y-%m-%d"),
            "completion_date": completion_dt.strftime("%Y-%m-%d"),
            "status": status,
            "vendor_id": vendor["vendor_id"],
            "vendor_name": vendor["vendor_name"],
            "vendor_address": vendor["vendor_address"],
            "vendor_phone": vendor["vendor_phone"],
            "bank_account_id": vendor["bank_account_id"],
            "site_lat": site_lat,
            "site_lon": site_lon,
            "photo_lat": photo_lat,
            "photo_lon": photo_lon,
            "photo_path": f"images/work_{i:03d}.jpg",
        }
    )

df = pd.DataFrame(rows)

# --- INJECT CONTROLLED ANOMALIES (~8% of dataset) ---

# 1. Financial Fraud (Indices 10 to 24): 3x cost inflation + rapid full payout
for idx in range(10, 25):
    df.loc[idx, "sanctioned_amount"] = int(df.loc[idx, "estimated_cost"] * random.uniform(2.8, 3.6))
    df.loc[idx, "amount_released"] = int(df.loc[idx, "sanctioned_amount"] * 0.98)
    s_dt = datetime.strptime(df.loc[idx, "sanction_date"], "%Y-%m-%d")
    df.loc[idx, "completion_date"] = (s_dt + timedelta(days=random.randint(2, 5))).strftime("%Y-%m-%d")
    df.loc[idx, "status"] = "Completed"

# 2. Vendor Cartel / Collusion (Indices 50 to 64): Distinct vendors sharing 1 bank account & split-tenders
shared_bank = "BANK_HASH_CARTEL_999"
shared_phone = "9826099999"
for idx in range(50, 65):
    df.loc[idx, "bank_account_id"] = shared_bank
    df.loc[idx, "vendor_phone"] = shared_phone
    df.loc[idx, "sanctioned_amount"] = 490000  # Just under 5 Lakh tender threshold

# 3. Ghost / GPS Mismatch (Indices 100 to 114): Completed status but photo GPS is ~15-30 km away
for idx in range(100, 115):
    df.loc[idx, "status"] = "Completed"
    df.loc[idx, "photo_lat"] = round(df.loc[idx, "site_lat"] + random.uniform(0.15, 0.30), 4)
    df.loc[idx, "photo_lon"] = round(df.loc[idx, "site_lon"] + random.uniform(0.15, 0.30), 4)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False)
print(f"Generated {len(df)} records at {OUTPUT_PATH}")