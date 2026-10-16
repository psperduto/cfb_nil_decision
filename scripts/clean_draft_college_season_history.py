import pandas as pd
from pathlib import Path

P = Path("data/processed")

history = pd.read_csv(P / "draft_college_season_history.csv")
audit = pd.read_csv(P / "draft_college_season_history_coverage.csv")

observed = history[history["season"].notna()].copy()
unobserved = history[history["season"].isna()].copy()

observed_path = P / "draft_college_season_history.csv"
unobserved_path = P / "draft_college_players_without_observed_seasons.csv"

observed.to_csv(observed_path, index=False)
unobserved.to_csv(unobserved_path, index=False)

# Aggregate only observed seasons, retaining the coverage count.
summary = (
    observed.groupby(
        ["draft_year", "round", "pick", "player_name", "college"],
        dropna=False,
    )
    .agg(
        observed_team_season_rows=("season", "size"),
        observed_seasons=("season", "nunique"),
        first_observed_season=("season", "min"),
        last_observed_season=("season", "max"),
    )
    .reset_index()
)

summary = summary.merge(
    audit[
        ["draft_year", "pick", "college_history_status", "history_window_note"]
    ],
    on=["draft_year", "pick"],
    how="left",
    validate="one_to_one",
)

summary_path = P / "draft_college_history_summary.csv"
summary.to_csv(summary_path, index=False)

print("OBSERVED SEASON HISTORY")
print("Rows:", len(observed))
print("Unique draft picks:", observed[["draft_year", "pick"]].drop_duplicates().shape[0])
print("Output:", observed_path)

print("\nPLAYERS WITHOUT OBSERVED SEASONS")
print("Rows:", len(unobserved))
print("Output:", unobserved_path)

print("\nCAREER HISTORY SUMMARY")
print("Rows:", len(summary))
print("Output:", summary_path)
print(summary["observed_seasons"].describe().round(2).to_string())
