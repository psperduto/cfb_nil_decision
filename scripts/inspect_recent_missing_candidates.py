import pandas as pd

diagnostic = pd.read_csv(
    "data/processed/draft_missing_history_diagnostic.csv"
)
candidates = pd.read_csv(
    "data/processed/draft_recruiting_match_candidates_scored.csv"
)

missing = diagnostic[
    diagnostic["diagnostic_status"].eq(
        "recruiting ID exists but not found in college stats"
    )
    & diagnostic["draft_year"].between(2023, 2025)
][["draft_year", "pick", "player_name", "college"]]

print("RECENT DRAFT PLAYERS WITH NO LINKED COLLEGE STATS")
print(missing.sort_values(["draft_year", "pick"]).to_string(index=False))

print("\nCANDIDATE DETAILS")
possible_keys = ["draft_year", "pick"]
details = candidates.merge(missing, on=possible_keys, suffixes=("_candidate", "_diagnostic"))

columns = [
    c for c in [
        "draft_year", "pick",
        "player_name_diagnostic", "college_diagnostic",
        "recruiting_class", "recruit_name", "recruiting_school",
        "committedTo", "athleteId", "stars", "rating",
        "match_tier", "match_reason"
    ] if c in details.columns
]

print(details[columns].sort_values(["draft_year", "pick"]).to_string(index=False))
