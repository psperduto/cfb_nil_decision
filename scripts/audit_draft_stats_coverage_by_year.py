from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
RECRUIT_DIR = DATA / "recruiting"

draft = pd.read_csv(DATA / "draft_results_2016_2025.csv")
candidates = pd.read_csv(
    DATA / "draft_recruiting_match_candidates_scored.csv",
    dtype={"athleteId": "string"},
)

def clean_id(series):
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .replace("", pd.NA)
    )

candidates["athleteId"] = clean_id(candidates["athleteId"])

# Load the observed college-stat player IDs and names.
stat_frames = []
for path in sorted(DATA.glob("player_stats_*_regular.csv")):
    df = pd.read_csv(
        path,
        dtype={"playerId": "string"},
        usecols=["playerId", "player", "season", "team"],
    )
    df["playerId"] = clean_id(df["playerId"])
    stat_frames.append(df)

stats = pd.concat(stat_frames, ignore_index=True)
stats = stats.dropna(subset=["playerId"])

stats["normalized_name"] = (
    stats["player"].astype("string").str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
)

stats_by_id = (
    stats.groupby("playerId")
    .agg(
        stats_names=("player", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
        stats_teams=("team", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
        first_observed_season=("season", "min"),
        last_observed_season=("season", "max"),
    )
    .reset_index()
)

# Add college-stat history to each recruiting candidate.
candidate_history = candidates.merge(
    stats_by_id,
    left_on="athleteId",
    right_on="playerId",
    how="left",
)

candidate_history["has_stats_history"] = candidate_history["playerId"].notna()

# Count whether each draft selection has any linked candidate with stats history.
per_player = (
    candidate_history.groupby(
        ["draft_year", "pick", "draft_player_name"], dropna=False
    )
    .agg(
        candidate_count=("recruit_name", "size"),
        has_recruit_candidate=("recruit_name", "count"),
        has_any_stats_history=("has_stats_history", "max"),
    )
    .reset_index()
)

# Draft rows with no recruiting candidate at all also need to remain visible.
draft_keys = ["draft_year", "pick", "player_name"]
per_player = per_player.rename(columns={"draft_player_name": "player_name"})

draft_coverage = draft.merge(
    per_player,
    on=draft_keys,
    how="left",
)

draft_coverage["has_recruit_candidate"] = (
    draft_coverage["has_recruit_candidate"].fillna(0) > 0
)
draft_coverage["has_any_stats_history"] = (
    draft_coverage["has_any_stats_history"].fillna(False).astype(bool)
)

yearly = (
    draft_coverage.groupby("draft_year")
    .agg(
        drafted_players=("pick", "size"),
        with_recruit_candidate=("has_recruit_candidate", "sum"),
        with_linked_stats_history=("has_any_stats_history", "sum"),
    )
    .reset_index()
)

yearly["recruit_candidate_rate"] = (
    yearly["with_recruit_candidate"] / yearly["drafted_players"]
)
yearly["linked_stats_rate"] = (
    yearly["with_linked_stats_history"] / yearly["drafted_players"]
)

yearly.to_csv(DATA / "draft_college_stats_coverage_by_year.csv", index=False)

missing = draft_coverage[~draft_coverage["has_any_stats_history"]].copy()
missing.to_csv(DATA / "draft_players_missing_college_stats_history.csv", index=False)

print("=== COVERAGE BY DRAFT YEAR ===")
print(yearly.to_string(index=False))

print("\n=== OVERALL COVERAGE ===")
print(f"Draft rows: {len(draft_coverage):,}")
print(f"With recruiting candidate: {draft_coverage['has_recruit_candidate'].sum():,}")
print(f"With linked college-stat history: {draft_coverage['has_any_stats_history'].sum():,}")
print(f"Missing linked college-stat history: {(~draft_coverage['has_any_stats_history']).sum():,}")

print("\n=== OUTPUTS ===")
print("data/processed/draft_college_stats_coverage_by_year.csv")
print("data/processed/draft_players_missing_college_stats_history.csv")
