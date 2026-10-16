import pandas as pd
from pathlib import Path

P = Path("data/processed")

master = pd.read_csv(P / "draft_player_master.csv")
season_stats = pd.read_csv(P / "college_player_season_stats.csv")

master["athleteId"] = pd.to_numeric(master["athleteId"], errors="coerce")
season_stats["playerId"] = pd.to_numeric(
    season_stats["playerId"], errors="coerce"
)
master["draft_year"] = pd.to_numeric(master["draft_year"], errors="coerce")
season_stats["season"] = pd.to_numeric(
    season_stats["season"], errors="coerce"
)

# Only use strong recruiting matches with positive IDs.
eligible = master[
    master["recruit_match_status"].eq("strong_candidate")
    & master["athleteId"].gt(0)
].copy()

# Keep the one-to-one draft record and its verified recruiting ID.
eligible = eligible[
    ["draft_year", "round", "pick", "player_name", "college",
     "position", "athleteId", "recruit_class_year",
     "recruit_stars", "recruit_rating", "recruit_ranking"]
].drop_duplicates(["draft_year", "pick"])

# Link player IDs to the season-level statistics.
history = eligible.merge(
    season_stats,
    left_on="athleteId",
    right_on="playerId",
    how="left",
    suffixes=("_draft", "_stats"),
    validate="one_to_many",
)

# College seasons must occur before the player's NFL draft year.
history = history[
    history["season"].isna()
    | (history["season"] < history["draft_year"])
].copy()

# Build an audit at the original draft-pick grain.
observed = (
    history.dropna(subset=["season"])
    .groupby(["draft_year", "pick"])
    .agg(
        observed_college_seasons=("season", "nunique"),
        first_observed_season=("season", "min"),
        last_observed_season=("season", "max"),
        observed_team_seasons=("season", "size"),
    )
    .reset_index()
)

audit = master[
    ["draft_year", "round", "pick", "player_name", "college",
     "recruit_match_status"]
].merge(
    observed,
    on=["draft_year", "pick"],
    how="left",
    validate="one_to_one",
)

audit["observed_college_seasons"] = (
    audit["observed_college_seasons"].fillna(0).astype(int)
)
audit["observed_team_seasons"] = (
    audit["observed_team_seasons"].fillna(0).astype(int)
)
audit["college_history_status"] = "linked_history_observed"
audit.loc[
    audit["observed_college_seasons"].eq(0),
    "college_history_status",
] = "no_linked_seasons_observed"

# The source starts in 2016, so this flag is not a claim of complete career data.
audit["history_window_note"] = (
    "Stats source covers regular seasons 2016-2025; earlier seasons unavailable"
)

history_path = P / "draft_college_season_history.csv"
audit_path = P / "draft_college_season_history_coverage.csv"

history.to_csv(history_path, index=False)
audit.to_csv(audit_path, index=False)

print("DRAFT-LINKED SEASON HISTORY")
print("Rows:", len(history))
print("Rows with observed season:", int(history["season"].notna().sum()))
print("Draft picks represented:", history[["draft_year", "pick"]].drop_duplicates().shape[0])
print("Output:", history_path)

print("\nCOVERAGE AUDIT")
print("Draft picks:", len(audit))
print(audit["college_history_status"].value_counts().to_string())
print("\nBy draft year:")
print(
    audit.groupby("draft_year")
    .agg(
        drafted_players=("pick", "size"),
        with_history=("observed_college_seasons",
                      lambda s: (s > 0).sum()),
        mean_observed_seasons=("observed_college_seasons", "mean"),
    )
    .round(2)
    .to_string()
)
print("Output:", audit_path)
