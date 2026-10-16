from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# Inspect the recruiting record from the raw API response.
raw_path = ROOT / "data" / "raw" / "cfbd" / "recruiting" / "recruits_2013_high_school.json"

with raw_path.open("r", encoding="utf-8") as f:
    recruits = json.load(f)

print("=== RAW RECRUITING RECORD ===")
for r in recruits:
    if "jared goff" in str(r.get("name", "")).lower():
        print(r)

# Search the full college-stat dataset by player name, not ID.
stat_files = sorted((ROOT / "data" / "processed").glob("player_stats_*_regular.csv"))
matches = []

for path in stat_files:
    df = pd.read_csv(
        path,
        dtype={"playerId": "string"},
        usecols=["playerId", "player", "season", "team"],
    )
    found = df[df["player"].astype("string").str.contains(
        "Jared Goff", case=False, na=False
    )]
    if not found.empty:
        matches.append(found)

print("\n=== COLLEGE-STAT NAME SEARCH ===")
if matches:
    result = pd.concat(matches, ignore_index=True).drop_duplicates()
    print(result.to_string(index=False))
else:
    print("No Jared Goff rows found in the downloaded 2016–2025 stats.")
