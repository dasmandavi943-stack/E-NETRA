import os
import random
import pandas as pd
from faker import Faker

fake = Faker("en_IN")
random.seed(42)

def generate_data():
    records = []
    categories = ["CC Road Construction", "Community Hall", "Solar Street Lights", "Drinking Water Borewell", "School Boundary Wall"]
    districts = ["Bhopal", "Raisen", "Sehore", "Vidisha", "Indore"]

    # 1. Generate 60 normal, honest project bids
    for i in range(1, 61):
        proj_id = f"MPLAD_2026_{i:03d}"
        tender_id = f"TND_{i:03d}"
        district = random.choice(districts)
        category = random.choice(categories)
        sanctioned_amt = random.randint(800000, 2500000)

        # 2 honest competing vendors per tender
        for v in range(1, 3):
            vendor_id = f"VND_{i:03d}_{v}"
            records.append({
                "project_id": proj_id,
                "tender_id": tender_id,
                "district": district,
                "work_category": category,
                "sanctioned_amount": sanctioned_amt,
                "contractor_id": vendor_id,
                "contractor_name": fake.company(),
                "gstin": f"23{fake.bothify(text='?????####?#Z#').upper()}",
                "registered_address": fake.address().replace("\n", ", "),
                "bank_account_hash": fake.sha256()[:16],
                "bid_amount": sanctioned_amt - random.randint(5000, 40000) if v == 1 else sanctioned_amt + random.randint(10000, 80000),
                "is_winner": True if v == 1 else False
            })

    # 2. Inject Fraud Pattern A: Shared Bank Account & Address Cartel (Projects 61 to 65)
    cartel_bank = "CARTEL_BANK_998877"
    cartel_address = "Plot 42, Industrial Area Phase 2, Bhopal, MP"
    cartel_vendors = [
        ("VND_CARTEL_01", "Shree Balaji Infra Pvt Ltd", "23AABCS1234F1Z5"),
        ("VND_CARTEL_02", "Narmada Builders & Suppliers", "23AAACN5678K1Z2"),
        ("VND_CARTEL_03", "Vindhya Construction Co", "23AAECV9012M1Z9")
    ]
    for idx, p_num in enumerate(range(61, 66)):
        proj_id = f"MPLAD_2026_{p_num:03d}"
        tender_id = f"TND_{p_num:03d}"
        winner_idx = idx % 3  # Rotating winners among the same 3 cartel companies
        for v_idx, (v_id, v_name, gst) in enumerate(cartel_vendors):
            records.append({
                "project_id": proj_id,
                "tender_id": tender_id,
                "district": "Bhopal",
                "work_category": "CC Road Construction",
                "sanctioned_amount": 1800000,
                "contractor_id": v_id,
                "contractor_name": v_name,
                "gstin": gst,
                "registered_address": cartel_address,
                "bank_account_hash": cartel_bank,
                "bid_amount": 1790000 if v_idx == winner_idx else 1850000 + (v_idx * 20000),
                "is_winner": True if v_idx == winner_idx else False
            })

    # 3. Inject Fraud Pattern B: Split Tendering below 10 Lakh threshold (Projects 66 to 68)
    for split_num in range(1, 4):
        proj_id = f"MPLAD_2026_06{5 + split_num}"
        tender_id = f"TND_SPLIT_0{split_num}"
        records.append({
            "project_id": proj_id,
            "tender_id": tender_id,
            "district": "Raisen",
            "work_category": "Solar Street Lights",
            "sanctioned_amount": 950000,  # Just under 10 Lakh limit
            "contractor_id": "VND_SPLIT_99",
            "contractor_name": "Apex Star Enterprises",
            "gstin": "23AABCA4455D1Z1",
            "registered_address": "Shop 12, Main Market, Raisen, MP",
            "bank_account_hash": "SPLIT_ACC_554433",
            "bid_amount": 948000,
            "is_winner": True
        })

    os.makedirs("graph_engine/data", exist_ok=True)
    df = pd.DataFrame(records)
    output_path = "graph_engine/data/sample_vendors.csv"
    df.to_csv(output_path, index=False)
    print(f"Success! Generated {len(df)} rows in {output_path}")

if __name__ == "__main__":
    generate_data()
