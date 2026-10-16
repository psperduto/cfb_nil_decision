import csv
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

API_KEY = os.environ.get("CFBD_API_KEY")
if not API_KEY:
    raise SystemExit("CFBD_API_KEY is missing. Set it in this terminal first.")

YEARS = range(2016, 2026)
RAW_DIR = Path("data/raw/cfbd")
PROCESSED_DIR = Path("data/processed")

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def fetch_season(year):
    url = (
        "https://api.collegefootballdata.com/stats/player/season"
        f"?year={year}&seasonType=regular"
    )
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {API_KEY}"}
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise

def write_csv(path, records):
    if not records:
        print(f"  No records; CSV not created: {path}")
        return

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

for year in YEARS:
    raw_path = RAW_DIR / f"player_stats_{year}_regular.json"
    csv_path = PROCESSED_DIR / f"player_stats_{year}_regular.csv"

    # Reuse a saved raw response so reruns don't repeatedly call the API.
    if raw_path.exists():
        records = json.loads(raw_path.read_text(encoding="utf-8"))
        print(f"{year}: using existing raw JSON")
    else:
        print(f"{year}: downloading...")
        records = fetch_season(year)
        raw_path.write_text(
            json.dumps(records, indent=2), encoding="utf-8"
        )
        time.sleep(1)

    write_csv(csv_path, records)
    print(
        f"  Records: {len(records):,} | "
        f"JSON: {raw_path.stat().st_size:,} bytes | "
        f"CSV: {csv_path.stat().st_size if csv_path.exists() else 0:,} bytes"
    )

print("\nHistorical season download complete.")
