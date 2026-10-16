from pathlib import Path
import pandas as pd

path = Path("data/processed/recruiting_players_2000_2025.csv")
out_dir = Path("data/processed")
df = pd.read_csv(path, low_memory=False)

# Normalize identifiers without treating missing or negative IDs as valid IDs.
df["athlete_id_num"] = pd.to_numeric(df["athleteId"], errors="coerce")
valid_id = df["athlete_id_num"].notna() & (df["athlete_id_num"] > 0)

print("RECRUITING IDENTITY AUDIT")
print(f"Rows: {len(df):,}")
print(f"Unique positive athlete IDs: {df.loc[valid_id, 'athlete_id_num'].nunique():,}")
print(f"Rows with missing/nonpositive athlete IDs: {(~valid_id).sum():,}")

# Repeated positive IDs across records/years.
with_id = df.loc[valid_id].copy()
id_summary = (
    with_id.groupby("athlete_id_num")
    .agg(
        record_count=("athlete_id_num", "size"),
        distinct_years=("year", "nunique"),
        names=("name", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
        years=("year", lambda s: " | ".join(map(str, sorted(set(s.dropna().astype(int)))))),
        schools=("committedTo", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
    )
    .reset_index()
)

repeated_ids = id_summary[id_summary["record_count"] > 1].copy()
repeated_ids.to_csv(out_dir / "recruiting_repeated_positive_ids.csv", index=False)

# Same normalized name in multiple recruiting classes; this is a candidate list,
# not proof that the records refer to the same person.
df["normalized_name"] = (
    df["name"].fillna("").astype(str).str.lower()
    .str.replace(r"[^a-z0-9]+", " ", regex=True)
    .str.strip()
)
named = df[df["normalized_name"] != ""].copy()
name_summary = (
    named.groupby("normalized_name")
    .agg(
        record_count=("normalized_name", "size"),
        distinct_years=("year", "nunique"),
        names=("name", lambda s: " | ".join(sorted(set(s.astype(str))))),
        years=("year", lambda s: " | ".join(map(str, sorted(set(s.astype(int)))))),
        athlete_ids=("athleteId", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
    )
    .reset_index()
)

repeated_names = name_summary[
    (name_summary["record_count"] > 1) | (name_summary["distinct_years"] > 1)
].copy()
repeated_names.to_csv(out_dir / "recruiting_repeated_names_review.csv", index=False)

print(f"\nPositive IDs appearing in multiple records: {len(repeated_ids):,}")
print(f"IDs appearing across multiple recruiting years: {(repeated_ids['distinct_years'] > 1).sum():,}")
print(f"Repeated-name groups for manual review: {len(repeated_names):,}")

print("\nLargest repeated-ID groups:")
print(
    repeated_ids.sort_values(["record_count", "distinct_years"], ascending=False)
    .head(10).to_string(index=False)
)

print("\nLargest repeated-name groups:")
print(
    repeated_names.sort_values(["record_count", "distinct_years"], ascending=False)
    .head(10).to_string(index=False)
)

print("\nOutputs:")
print(out_dir / "recruiting_repeated_positive_ids.csv")
print(out_dir / "recruiting_repeated_names_review.csv")
