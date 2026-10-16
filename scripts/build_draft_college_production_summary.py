import pandas as pd
from pathlib import Path

P = Path("data/processed")

history = pd.read_csv(P / "draft_college_season_history.csv")
master = pd.read_csv(P / "draft_player_master.csv")
coverage = pd.read_csv(P / "draft_college_season_history_coverage.csv")

history["season"] = pd.to_numeric(history["season"], errors="coerce")

# These fields represent totals that can be summed across observed seasons.
sum_fields = [
    "passing_ATT", "passing_COMPLETIONS", "passing_YDS",
    "passing_TD", "passing_INT",
    "rushing_CAR", "rushing_YDS", "rushing_TD",
    "receiving_REC", "receiving_YDS", "receiving_TD",
    "defensive_TOT", "defensive_SOLO", "defensive_SACKS",
    "defensive_TFL", "defensive_PD", "defensive_QB_HUR",
    "defensive_TD", "interceptions_INT", "interceptions_YDS",
    "interceptions_TD", "fumbles_FUM", "fumbles_LOST",
    "fumbles_REC", "kickReturns_NO", "kickReturns_YDS",
    "kickReturns_TD", "puntReturns_NO", "puntReturns_YDS",
    "puntReturns_TD", "kicking_FGA", "kicking_FGM",
    "kicking_XPA", "kicking_XPM", "kicking_PTS",
    "punting_NO", "punting_YDS", "punting_TB", "punting_In_20",
]

# Only aggregate columns actually present in the source.
sum_fields = [c for c in sum_fields if c in history.columns]

group_keys = ["draft_year", "round", "pick"]
grouped = history.groupby(group_keys, dropna=False)

summary = grouped.agg(
    observed_team_season_rows=("season", "size"),
    observed_seasons=("season", "nunique"),
    first_observed_season=("season", "min"),
    last_observed_season=("season", "max"),
).reset_index()

# Sum totals only where a statistic was observed; all-missing groups remain NaN.
totals = grouped[sum_fields].sum(min_count=1).reset_index()
summary = summary.merge(totals, on=group_keys, how="left", validate="one_to_one")

# Carry through rates from the latest observed season, rather than averaging rates.
rate_fields = [
    "passing_PCT", "passing_YPA", "rushing_YPC", "receiving_YPR",
    "interceptions_AVG", "kickReturns_AVG", "puntReturns_AVG",
    "kicking_PCT", "punting_YPP",
]
rate_fields = [c for c in rate_fields if c in history.columns]

latest = (
    history.sort_values("season")
    .groupby(group_keys, dropna=False)
    .tail(1)[group_keys + rate_fields]
)
summary = summary.merge(latest, on=group_keys, how="left", validate="one_to_one")

# Attach draft and recruiting context.
context_cols = [
    "draft_year", "round", "pick", "player_name", "position",
    "college", "team", "recruit_name", "recruit_class_year",
    "recruit_stars", "recruit_rating", "recruit_ranking",
    "recruit_match_status", "college_stats_coverage",
]
context_cols = [c for c in context_cols if c in master.columns]
context = master[context_cols].drop_duplicates(group_keys)
summary = summary.merge(
    context,
    on=group_keys,
    how="right",
    validate="one_to_one",
)

summary = summary.merge(
    coverage[
        ["draft_year", "pick", "college_history_status", "history_window_note"]
    ],
    on=["draft_year", "pick"],
    how="left",
    validate="one_to_one",
)

summary["observed_seasons"] = summary["observed_seasons"].fillna(0).astype(int)
summary["observed_team_season_rows"] = (
    summary["observed_team_season_rows"].fillna(0).astype(int)
)

output = P / "draft_college_production_summary.csv"
summary.to_csv(output, index=False)

print("DRAFT COLLEGE PRODUCTION SUMMARY")
print("Rows:", len(summary))
print("Unique draft picks:", summary[["draft_year", "pick"]].drop_duplicates().shape[0])
print("Columns:", len(summary.columns))
print("Output:", output)

print("\nObserved season coverage:")
print(summary["college_history_status"].value_counts(dropna=False).to_string())

print("\nObserved seasons per draft pick:")
print(summary["observed_seasons"].describe().round(2).to_string())

print("\nSample output:")
sample_cols = [
    c for c in [
        "draft_year", "pick", "player_name", "college",
        "observed_seasons", "passing_YDS", "rushing_YDS",
        "receiving_YDS", "defensive_TOT",
    ] if c in summary.columns
]
print(summary[sample_cols].head(15).to_string(index=False))
