import pandas as pd

source = "data/processed/draft_recruiting_match_candidates_scored.csv"
output = "data/processed/draft_recruiting_match_candidates_scored.csv"

df = pd.read_csv(source, low_memory=False)

athlete_id = pd.to_numeric(df["athleteId"], errors="coerce")
df["athlete_id_positive"] = athlete_id.gt(0)

df["identity_link_status"] = "review_required"

strong = df["match_tier"].eq(
    "strong candidate: name + college + timing + athlete ID"
)
alias = df["match_tier"].eq("name + college alias + timing")
timing = df["match_tier"].eq(
    "name + timing; college mismatch or transfer"
)

df.loc[strong & df["athlete_id_positive"], "identity_link_status"] = (
    "strong_candidate_positive_id"
)
df.loc[strong & ~df["athlete_id_positive"], "identity_link_status"] = (
    "strong_name_college_timing_but_invalid_id"
)
df.loc[alias & df["athlete_id_positive"], "identity_link_status"] = (
    "college_alias_candidate_positive_id"
)
df.loc[alias & ~df["athlete_id_positive"], "identity_link_status"] = (
    "college_alias_candidate_invalid_id"
)
df.loc[timing & df["athlete_id_positive"], "identity_link_status"] = (
    "name_timing_candidate_college_mismatch"
)

df.to_csv(output, index=False)

print("Identity link status counts:")
print(df["identity_link_status"].value_counts(dropna=False).to_string())

print("\nPositive-ID candidate rows:", int(df["athlete_id_positive"].sum()))
print("Negative-ID candidate rows:", int(athlete_id.lt(0).sum()))
print("Missing-ID candidate rows:", int(athlete_id.isna().sum()))
print("Saved:", output)
