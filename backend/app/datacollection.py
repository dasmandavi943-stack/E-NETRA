import csv
from pathlib import Path

CSV_PATH = Path("frontend/e-netra.csv")  # Change to "data/e-netra.csv" if moved

FIELDNAMES = [
    "project_id", "mp_name", "district", "work_category",
    "estimated_cost", "sanctioned_amount", "amount_released",
    "sanction_date", "completion_date", "status",
    "vendor_id", "vendor_name", "vendor_address", "vendor_phone",
    "bank_account_id", "site_lat", "site_lon",
    "photo_lat", "photo_lon", "photo_path"
]

def load_projects():
    if not CSV_PATH.exists():
        return []
    with open(CSV_PATH, mode="r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def add_project(row_dict):
    existing = load_projects()
    existing_ids = {r["project_id"] for r in existing}
    if row_dict["project_id"] in existing_ids:
        print(f"Skipped duplicate ID: {row_dict['project_id']}")
        return
    file_exists = CSV_PATH.exists() and CSV_PATH.stat().st_size > 0
    with open(CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_dict)
    print(f"Added: {row_dict['project_id']}")

if __name__ == "__main__":
    projects = load_projects()
    print("Current project count:", len(projects))

    # Example: add a second sample row (replace with real e-SAKSHI / synthetic data)
    new_row = {
        "project_id": "MPLAD_002",
        "mp_name": "MP_Representative_2",
        "district": "Bhopal",
        "work_category": "Culvert",
        "estimated_cost": "500000",
        "sanctioned_amount": "500000",
        "amount_released": "250000",
        "sanction_date": "2026-07-10",
        "completion_date": "",
        "status": "In Progress",
        "vendor_id": "VEND_102",
        "vendor_name": "Malwa Builders",
        "vendor_address": "45 Arera Colony Bhopal",
        "vendor_phone": "9826000102",
        "bank_account_id": "BANK_HASH_02",
        "site_lat": "23.2167",
        "site_lon": "77.4333",
        "photo_lat": "23.2169",
        "photo_lon": "77.4335",
        "photo_path": "images/work_002.jpg",
    }
    add_project(new_row)