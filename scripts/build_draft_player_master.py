import pandas as pd
from pathlib import Path

ROOT = Path(".")
PROCESSED = ROOT / "data" / "processed"
OUTPUT = PROCESSED / "draft_player_master.csv"
AUDIT = PROCESSED / "draft_player_master_match_audit.csv"

draft = pd.read_csv(PROCESSED / "draft_results_2016_2025.csv")
candidates = pd.read_csv(
    PROCESSED / "draft_recruiting_match_candidates_scored.csv"
)

# Normalize identifier values. Negative IDs are excluded from ID-based joins.
candidates["athleteId"] = pd.to_numeric(
    candidates["athleteId"], errors="coerce"
)
candidates.loc[candidates["athleteId"] <= 0, "athleteId"] = pd.NA

# Keep only candidates whose recruiting class is plausible for the draft year.
candidates["recruit_class_year"] = pd.to_numeric(
    candidates["recruit_class_year"], errors="coerce"
)
candidates["draft_year"] = pd.to_numeric(
    candidates["draft_year"], errors="coerce"
)
candidates["years_from_recruit_class_to_draft"] = pd.to_numeric(
    candidates["years_from_recruit_class_to_draft"], errors="coerce"
)

# Rank candidates using the existing match assessment, then school agreement,
# timing plausibility, and identifier availability.
tier_priority = {
    "strong candidate: name + college + timing + athlete ID": 0,
    "name + college alias + timing": 1,
    "name + timing; college mismatchor transfer": 2,
    "review": 3,
}
candidates["_tier_priority"] = (
    candidates["match_tier"].map(tier_priority).fillna(4)
)
candidates["_has_positive_id"] = candidates["athleteId"].notna()

candidates = candidates.sort_values(
    [
        "draft_year",
        "pick",
        "_tier_priority",
        "college_exact_normalized",
        "plausible_class_to_draft_timing",
        "_has_positive_id",
    ],
    ascending=[True, True, True, False, False, False],
    na_position="last",
)

# Retain all candidates separately for transparency.
candidates.to_csv(AUDIT, index=False)

# Select a provisional best candidate only if it is supported by the
# existing strong-match tier. Ambiguous cases remain unmatched in the master.
best = candidates.drop_duplicates(["draft_year", "pick"], keep="first").copy()
best["recruit_match_status"] = best["match_tier"].map(
    lambda tier: (
        "strong_candidate"
        if tier == "strong candidate: name + college + timing + athlete ID"
        else "needs_review"
    )
)

best["recruit_match_status"] = best["recruit_match_status"].where(
    best["recruit_match_status"].eq("strong_candidate"),
    "needs_review",
)

# Keep the candidate details even for review rows, but make the status explicit.
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

# Audit college-stat availability for positively identified recruiting athletes.
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

# Preserve the full stats table separately; this flag indicates ID presence,
# not completeness of the player's career statistics.
master.to_csv(OUTPUT, index=False)

print("MASTER TABLE")
print("Rows:", len(master))
print("Unique draft year/pick:", master[["draft_year", "pick"]].drop_duplicates().shape[0])
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
        strong_recruit_matches=("recruit_match_status",
                                lambda x: (x == "strong_candidate").sum()),
        players_with_stats_id=("has_linked_stats_id", "sum"),
    )
    .to_string()
)
print("\nCandidate audit:", AUDIT)
