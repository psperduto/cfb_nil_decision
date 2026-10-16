import csv
import json
import os
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "cfbd" / "recruiting"
PROCESSED_DIR = ROOT / "data" / "processed" / "recruiting"
AUDIT_PATH = ROOT / "data" / "processed" / "cfbd_recruiting_download_audit.csv"

START_YEAR = 2000
END_YEAR = 2025

API_URL = "https://api.collegefootballdata.com/recruiting/players"
API_KEY = os.getenv("CFBD_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "CFBD_API_KEY is not set in this PowerShell session."
    )

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {API_KEY}"})


def get_recruits(year):
    response = session.get(
        API_URL,
        params={"year": year, "classification": "HighSchool"},
        timeout=90,
    )

    for attempt in range(5):
        if response.status_code != 429 and response.status_code < 500:
            break

        wait = min(2 ** (attempt + 1), 30)
        print(f"  HTTP {response.status_code}; retrying in {wait}s...")
        time.sleep(wait)
        response = session.get(
            API_URL,
            params={"year": year, "classification": "HighSchool"},
            timeout=90,
        )

    response.raise_for_status()
    return response.json()


def flatten_recruit(recruit):
    row = dict(recruit)
    hometown = row.pop("hometownInfo", None) or {}

    if isinstance(hometown, dict):
        row["hometownLatitude"] = hometown.get("latitude")
        row["hometownLongitude"] = hometown.get("longitude")
        row["hometownFipsCode"] = hometown.get("fipsCode")

    return row


audit_rows = []
all_columns = set()

for year in range(START_YEAR, END_YEAR + 1):
    raw_path = RAW_DIR / f"recruits_{year}_high_school.json"
    csv_path = PROCESSED_DIR / f"recruits_{year}_high_school.csv"

    if raw_path.exists():
        with raw_path.open("r", encoding="utf-8") as file:
            recruits = json.load(file)
        print(f"{year}: using existing raw JSON")
    else:
        print(f"{year}: requesting recruiting records...")
        recruits = get_recruits(year)

        with raw_path.open("w", encoding="utf-8") as file:
            json.dump(recruits, file, ensure_ascii=False)

        time.sleep(0.25)

    if not isinstance(recruits, list):
        raise ValueError(f"Unexpected API response for {year}")

    rows = [flatten_recruit(r) for r in recruits]
    columns = sorted({key for row in rows for key in row})
    all_columns.update(columns)

    if rows:
        with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

    missing_ids = sum(not row.get("id") for row in rows)
    missing_names = sum(not row.get("name") for row in rows)
    missing_years = sum(not row.get("year") for row in rows)
    unique_ids = len({
        str(row["id"]) for row in rows if row.get("id") is not None
    })
    unique_athlete_ids = len({
        str(row["athleteId"])
        for row in rows
        if row.get("athleteId") is not None
    })

    audit_rows.append({
        "year": year,
        "records": len(rows),
        "unique_recruit_ids": unique_ids,
        "unique_athlete_ids": unique_athlete_ids,
        "missing_recruit_ids": missing_ids,
        "missing_names": missing_names,
        "missing_years": missing_years,
        "raw_json_bytes": raw_path.stat().st_size,
        "csv_bytes": csv_path.stat().st_size if csv_path.exists() else 0,
        "columns": len(columns),
    })

    print(
        f"  {len(rows):,} records | "
        f"{unique_athlete_ids:,} unique athlete IDs | "
        f"missing IDs: {missing_ids} | missing names: {missing_names}"
    )

with AUDIT_PATH.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=list(audit_rows[0].keys()))
    writer.writeheader()
    writer.writerows(audit_rows)

print("\nRecruiting download complete.")
print(f"Total records: {sum(row['records'] for row in audit_rows):,}")
print(f"Years: {START_YEAR}-{END_YEAR}")
print(f"Audit: {AUDIT_PATH.relative_to(ROOT)}")
print(f"Recruiting CSV directory: {PROCESSED_DIR.relative_to(ROOT)}")
