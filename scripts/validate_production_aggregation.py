import pandas as pd
import numpy as np

P = "data/processed/"
history = pd.read_csv(P + "draft_college_season_history.csv")
summary = pd.read_csv(P + "draft_college_production_summary.csv")

fields = [
    "passing_YDS", "passing_TD", "passing_INT",
    "rushing_YDS", "rushing_TD",
    "receiving_REC", "receiving_YDS", "receiving_TD",
    "defensive_TOT", "defensive_SACKS",
]

print("AGGREGATION CONSISTENCY CHECK")
issues = 0

for field in fields:
    if field not in history.columns or field not in summary.columns:
        print(f"{field}: missing from history or summary")
        issues += 1
        continue

    direct = history.groupby(
        ["draft_year", "round", "pick"], dropna=False
    )[field].sum(min_count=1)

    compare = summary.set_index(
        ["draft_year", "round", "pick"]
    )[field]

    aligned = pd.concat(
        [direct.rename("direct"), compare.rename("summary")],
        axis=1,
    )
    both_missing = aligned["direct"].isna() & aligned["summary"].isna()
    equal = np.isclose(
        aligned["direct"].fillna(0),
        aligned["summary"].fillna(0),
    )
    mismatches = aligned[~(both_missing | equal)]

    print(f"{field}: {len(mismatches)} mismatches")
    if len(mismatches):
        print(mismatches.head(5).to_string())
        issues += len(mismatches)

print("\nTOTAL ISSUES:", issues)
if issues == 0:
    print("All tested totals match the season-history source.")
