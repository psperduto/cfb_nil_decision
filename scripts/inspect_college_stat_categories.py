import pandas as pd
from pathlib import Path

files = sorted(Path("data/processed").glob("player_stats_*_regular.csv"))

stats = pd.concat(
    [pd.read_csv(f, usecols=["category", "statType", "stat"]) for f in files],
    ignore_index=True
)

print("TOTAL OBSERVATIONS:", len(stats))
print("\nCATEGORY COUNTS")
print(stats["category"].value_counts(dropna=False).to_string())

print("\nSTAT TYPES BY CATEGORY")
pairs = (
    stats.groupby(["category", "statType"], dropna=False)
    .size()
    .rename("observations")
    .reset_index()
    .sort_values(["category", "statType"])
)
print(pairs.to_string(index=False))

print("\nSTAT VALUE EXAMPLES")
for category in sorted(stats["category"].dropna().unique()):
    subset = stats.loc[stats["category"].eq(category)]
    print(f"\n{category}")
    print(
        subset[["statType", "stat"]]
        .drop_duplicates()
        .head(15)
        .to_string(index=False)
    )
