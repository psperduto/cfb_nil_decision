import pandas as pd

base = "data/processed/"
master = pd.read_csv(base + "draft_player_master.csv")
candidates = pd.read_csv(
    base + "draft_recruiting_match_candidates_scored.csv"
)

strong_tier = "strong candidate: name + college + timing + athlete ID"

strong = candidates[
    candidates["match_tier"].eq(strong_tier)
].copy()

strong_keys = strong[["draft_year", "pick"]].drop_duplicates()
master_keys = master[["draft_year", "pick", "recruit_match_status"]]

check = master_keys.merge(
    strong_keys.assign(strong_candidate_available=True),
    on=["draft_year", "pick"],
    how="left",
)
check["strong_candidate_available"] = (
    check["strong_candidate_available"].fillna(False)
)

print("DRAFT PICKS:", len(master))
print("PICKS WITH A STRONG CANDIDATE AVAILABLE:",
      int(check["strong_candidate_available"].sum()))
print("\nSTRONG CANDIDATE AVAILABILITY VS MASTER STATUS")
print(pd.crosstab(
    check["strong_candidate_available"],
    check["recruit_match_status"].fillna("no_candidate"),
    margins=True
).to_string())

missed = check[
    check["strong_candidate_available"]
    & check["recruit_match_status"].ne("strong_candidate")
]
print("\nPICKS WITH STRONG CANDIDATES BUT NOT MARKED STRONG:",
      len(missed))
print(missed.head(30).to_string(index=False))
