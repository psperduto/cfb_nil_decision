import pandas as pd
from pathlib import Path

PROCESSED = Path("data/processed")
OUTPUT = PROCESSED / "college_player_season_stats.csv"

files = sorted(PROCESSED.glob("player_stats_*_regular.csv"))
if not files:
    raise FileNotFoundError("No player_stats_*_regular.csv files found.")

stats = pd.concat(
    [pd.read_csv(path) for path in files],
    ignore_index=True,
)

required = {
    "season", "playerId", "player", "position", "team",
    "conference", "category", "statType", "stat",
}
missing = required - set(stats.columns)
if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")

stats["stat"] = pd.to_numeric(stats["stat"], errors="coerce")
stats["season"] = pd.to_numeric(stats["season"], errors="coerce")
stats["playerId"] = pd.to_numeric(stats["playerId"], errors="coerce")

keys = ["season", "playerId", "player", "position", "team", "conference"]
duplicate_key = keys + ["category", "statType"]
duplicate_count = int(stats.duplicated(duplicate_key).sum())

print("Source rows:", len(stats))
print("Duplicate player-season-team-category-stat rows:", duplicate_count)

if duplicate_count:
    raise ValueError("Resolve duplicate source stat keys before pivoting.")

# Only observed combinations are retained; no Cartesian product is created.
wide = stats.pivot(
    index=keys,
    columns=["category", "statType"],
    values="stat",
)

wide.columns = [
    f"{category}_{stat_type}".replace(" ", "_").replace("/", "_")
    for category, stat_type in wide.columns
]
wide = wide.reset_index()
wide.columns.name = None

# Track whether each category was present for each player-season-team.
category_flags = (
    stats[keys + ["category"]]
    .drop_duplicates()
    .assign(observed=True)
    .pivot(
        index=keys,
        columns="category",
        values="observed",
    )
    .fillna(False)
    .reset_index()
)

category_flags.columns = [
    f"has_category_{col}" if col not in keys else col
    for col in category_flags.columns
]

result = wide.merge(
    category_flags,
    on=keys,
    how="left",
    validate="one_to_one",
)

if result.duplicated(keys).any():
    raise ValueError("Output is not unique at player-season-team grain.")

result = result.sort_values(["season", "player", "team"])
result.to_csv(OUTPUT, index=False)

print("\nPLAYER-SEASON DATASET")
print("Rows:", len(result))
print("Unique player IDs:", result["playerId"].nunique())
print("Seasons:", int(result["season"].min()), "to", int(result["season"].max()))
print("Columns:", len(result.columns))
print("Output:", OUTPUT)

print("\nCategory coverage flags:")
for col in [c for c in result.columns if c.startswith("has_category_")]:
    print(f"{col}: {int(result[col].sum()):,} rows")

print("\nExample columns:")
print(result.columns.tolist())
