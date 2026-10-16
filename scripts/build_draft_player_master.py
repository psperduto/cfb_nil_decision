import pandas as pd
from pathlib import Path

ROOT = Path(".")
PROCESSED = ROOT / "data" / "processed"
OUTPUT = PROCESSED / "draft_player_master.csv"
AUDIT = PROCESSED / "draft_player_master_match_audit.csv"

draft = pd.read_csv(PROCESSED / "draft_results_2016_2025.csv")
candidates = pd.read_csv(
    PROCESSED / "draft_recruiting_match_candidates_scored.csv",
    low_memory=False,
)

# Normalize IDs. Only positive athlete IDs are eligible for ID-based joins.
candidates["athleteId"] = pd.to_numeric(
    candidates["athleteId"], errors="coerce"
)
candidates.loc[candidates["athleteId"] <= 0, "athleteId"] = pd.NA
candidates["athlete_id_positive"] = candidates["athleteId"].notna()

# Normalize numeric fields.
for col in [
    "recruit_class_year",
    "draft_year",
    "years_from_recruit_class_to_draft",
]:
    candidates[col] = pd.to_numeric(candidates[col], errors="coerce")

# Keep the existing assessment, but do not allow a negative or missing ID
# to qualify for the strong-candidate status.
tier_priority = {
    "strong candidate: name + college + timing + athlete ID": 0,
    "name + college alias + timing": 1,
    "name + timing; college mismatch or transfer": 2,
    "review": 3,
}

candidates["_tier_priority"] = (
    candidates["match_tier"].map(tier_priority).fillna(4)
)

# A strong-tier row without a positive ID is downgraded for selection purposes.
candidates["_selection_tier"] = candidates["match_tier"]
invalid_strong = (
    candidates["match_tier"].eq(
        "strong candidate: name + college + timing + athlete ID"
    )
    & ~candidates["athlete_id_positive"]
)
candidates.loc[invalid_strong, "_selection_tier"] = "review"
candidates["_tier_priority"] = (
    candidates["_selection_tier"].map(tier_priority).fillna(3)
)

# Rank candidates using tier, school agreement, timing, and valid ID.
candidates = candidates.sort_values(
    [
        "draft_year",
        "pick",
        "_tier_priority",
        "college_exact_normalized",
        "college_alias_agreement",
        "plausible_class_to_draft_timing",
        "athlete_id_positive",
    ],
    ascending=[True, True, True, False, False, False, False],
    na_position="last",
)

# Preserve every candidate in the audit file.
candidates.to_csv(AUDIT, index=False)

# Select one provisional candidate per draft pick.
best = candidates.drop_duplicates(
    ["draft_year", "pick"], keep="first"
).copy()

is_strong = (
    best["match_tier"].eq(
        "strong candidate: name + college + timing + athlete ID"
    )
    & best["athlete_id_positive"]
)
best["recruit_match_status"] = "needs_review"
best.loc[is_strong, "recruit_match_status"] = "strong_candidate"

recruit_columns = [
    "draft_year", "pick", "recruit_name", "recruit_class_year",
    "recruit_committed_to", "recruit_position", "recruit_stars",
    "recruit_rating", "recruit_ranking", "athleteId",
    "match_tier", "recruit_match_status",
]
best = best[recruit_columns]

master = draft.merge(
    best,
    on=["draft_year", "pick"],
    how="left",
    validate="one_to_one",
)

# Audit whether positive recruiting IDs appear in the available college-stat
# source window. This indicates ID presence, not complete career coverage.
stat_ids = set()
for year in range(2016, 2026):
    path = PROCESSED / f"player_stats_{year}_regular.csv"
    if not path.exists():
        continue
    ids = pd.read_csv(path, usecols=["playerId"])["playerId"]
    ids = pd.to_numeric(ids, errors="coerce").dropna()
    stat_ids.update(ids.astype("int64").tolist())

master["athleteId"] = pd.to_numeric(master["athleteId"], errors="coerce")
master["athleteId"] = master["athleteId"].where(master["athleteId"] > 0)
master["has_linked_stats_id"] = master["athleteId"].isin(stat_ids)

master["college_stats_coverage"] = "no_verified_recruiting_id"
master.loc[
    master["athleteId"].notna() & ~master["has_linked_stats_id"],
    "college_stats_coverage",
] = "recruiting_id_not_found_in_2016_2025_stats"
master.loc[
    master["has_linked_stats_id"],
    "college_stats_coverage",
] = "player_id_present_in_stats_window"

master.to_csv(OUTPUT, index=False)

print("MASTER TABLE")
print("Rows:", len(master))
print(
    "Unique draft year/pick:",
    master[["draft_year", "pick"]].drop_duplicates().shape[0],
)
print("Output:", OUTPUT)

print("\nRecruiting match status:")
print(master["recruit_match_status"].value_counts(dropna=False).to_string())

print("\nCollege stats coverage:")
print(master["college_stats_coverage"].value_counts(dropna=False).to_string())

print("\nDraft year coverage:")
print(
    master.groupby("draft_year")
    .agg(
        drafted_players=("pick", "size"),
        strong_recruit_matches=(
            "recruit_match_status",
            lambda x: (x == "strong_candidate").sum(),
        ),
        players_with_stats_id=("has_linked_stats_id", "sum"),
    )
    .to_string()
)
print("\nCandidate audit:", AUDIT)
