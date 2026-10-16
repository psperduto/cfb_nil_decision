import pandas as pd

path = "data/processed/draft_missing_history_diagnostic.csv"
df = pd.read_csv(path)

missing = df[
    df["diagnostic_status"].eq(
        "recruiting ID exists but not found in college stats"
    )
].copy()

print("TOTAL:", len(missing))

print("\nBY DRAFT YEAR")
print(missing.groupby("draft_year").size().to_string())

print("\nBY RECRUITING CLASS")
classes = (
    missing["candidate_recruiting_classes"]
    .fillna("")
    .str.split(r"\s*\|\s*")
    .explode()
)
classes = classes[classes.ne("")]
print(classes.value_counts().sort_index().to_string())

print("\nSAMPLE RECORDS")
print(
    missing[["draft_year", "pick", "player_name", "college",
             "candidate_recruiting_classes"]]
    .sort_values(["draft_year", "pick"])
    .head(40)
    .to_string(index=False)
)
