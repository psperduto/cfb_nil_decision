import pandas as pd

path = "data/processed/draft_recruiting_match_candidates_scored.csv"
df = pd.read_csv(path, low_memory=False)

id_num = pd.to_numeric(df["athleteId"], errors="coerce")
df["id_positive"] = id_num.gt(0)
df["id_negative"] = id_num.lt(0)
df["id_missing"] = id_num.isna()

print("MATCH TIER AUDIT")
print("=" * 70)

summary = df.groupby("match_tier", dropna=False).agg(
    candidate_rows=("pick", "size"),
    distinct_draft_picks=("pick", "count"),
    positive_ids=("id_positive", "sum"),
    negative_ids=("id_negative", "sum"),
    missing_ids=("id_missing", "sum"),
    college_exact=("college_exact_normalized", "sum"),
    college_alias=("college_alias_agreement", "sum"),
    plausible_timing=("plausible_class_to_draft_timing", "sum"),
).reset_index()

print(summary.to_string(index=False))

print("\nID TYPES IN CURRENT STRONG TIER")
strong = df[df["match_tier"].astype(str).str.startswith("strong candidate")]
print("Rows:", len(strong))
print("Positive IDs:", strong["id_positive"].sum())
print("Negative IDs:", strong["id_negative"].sum())
print("Missing IDs:", strong["id_missing"].sum())

print("\nACTUAL COLUMNS")
print(pd.read_csv(path, nrows=0).columns.tolist())
