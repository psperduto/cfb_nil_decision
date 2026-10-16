from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RECRUIT_DIR = ROOT / "data" / "processed" / "recruiting"
STATS_DIR = ROOT / "data" / "processed"
DRAFT_PATH = STATS_DIR / "draft_results_2016_2025.csv"

recruits = pd.concat(
    [
        pd.read_csv(p, dtype={"athleteId": "string"})
        for p in sorted(RECRUIT_DIR.glob("recruits_*_high_school.csv"))
    ],
    ignore_index=True,
)

draft = pd.read_csv(DRAFT_PATH)
stats = pd.concat(
    [
        pd.read_csv(p, dtype={"playerId": "string"})
        for p in sorted(STATS_DIR.glob("player_stats_*_regular.csv"))
    ],
    ignore_index=True,
)

print("Draft columns:", draft.columns.tolist())
print("Recruiting columns:", recruits.columns.tolist())
print("Stats columns:", stats.columns.tolist())
