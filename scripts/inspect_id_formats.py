from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parents[1]
stats_path = root / "data" / "processed" / "player_stats_2016_regular.csv"
candidate_path = root / "data" / "processed" / "draft_recruiting_match_candidates_scored.csv"

stats = pd.read_csv(stats_path, usecols=["playerId", "player"], dtype={"playerId": "string"})
candidates = pd.read_csv(candidate_path, dtype={"athleteId": "string"})

print("=== COLLEGE STATS IDS ===")
print(stats[stats["player"].eq("Jared Goff")].head().to_string(index=False))
print("Sample ID values:", stats["playerId"].dropna().head(10).tolist())

print("\n=== RECRUITING CANDIDATE IDS ===")
print(
    candidates[candidates["draft_player_name"].eq("Jared Goff")][
        ["draft_player_name", "athleteId", "recruit_name"]
    ].to_string(index=False)
)

stats_ids = set(stats["playerId"].dropna().str.strip())
recruit_ids = set(candidates["athleteId"].dropna().str.strip())

print("\nExact ID overlap in this season:", len(stats_ids & recruit_ids))
print("Stats ID example:", repr(next(iter(stats_ids), None)))
print("Recruit ID example:", repr(next(iter(recruit_ids), None)))
