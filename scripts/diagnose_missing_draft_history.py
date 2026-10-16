from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
RECRUIT_DIR = DATA / "recruiting"

draft = pd.read_csv(DATA / "draft_results_2016_2025.csv")
candidates = pd.read_csv(
    DATA / "draft_recruiting_match_candidates_scored.csv",
    dtype={"athleteId": "string"},
)

def clean_id(series):
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .replace("", pd.NA)
    )

candidates["athleteId"] = clean_id(candidates["athleteId"])

# Build the set of IDs present in any downloaded college-stat season.
stat_ids = set()
for path in sorted(DATA.glob("player_stats_*_regular.csv")):
    ids = pd.read_csv(path, usecols=["playerId"], dtype={"playerId": "string"})
    stat_ids.update(clean_id(ids["playerId"]).dropna().tolist())

# One row per drafted player, retaining all recruiting candidates for diagnosis.
rows = []

for _, player in draft.iterrows():
    matches = candidates[
        (candidates["draft_year"] == player["draft_year"])
        & (candidates["pick"] == player["pick"])
        & (candidates["draft_player_name"] == player["player_name"])
    ]

    if matches.empty:
        status = "no exact normalized-name recruiting candidate"
        candidate_count = 0
        populated_id_count = 0
        linked_id_count = 0
        candidate_classes = ""
    else:
        candidate_count = len(matches)
        populated_id_count = int(matches["athleteId"].notna().sum())
        linked_id_count = int(
            matches["athleteId"].dropna().isin(stat_ids).sum()
        )
        candidate_classes = " | ".join(
            sorted(set(matches["recruit_class_year"].dropna().astype(str)))
        )

        if linked_id_count:
            status = "has at least one candidate ID in college stats"
        elif populated_id_count:
            status = "recruiting ID exists but not found in college stats"
        else:
            status = "candidate exists but athlete ID is missing"

    rows.append({
        "draft_year": player["draft_year"],
        "round": player["round"],
        "pick": player["pick"],
        "player_name": player["player_name"],
        "college": player["college"],
        "candidate_count": candidate_count,
        "candidates_with_athlete_id": populated_id_count,
        "candidate_ids_found_in_stats": linked_id_count,
        "candidate_recruiting_classes": candidate_classes,
        "diagnostic_status": status,
    })

report = pd.DataFrame(rows)
out_path = DATA / "draft_missing_history_diagnostic.csv"
report.to_csv(out_path, index=False)

print("=== MISSING-HISTORY DIAGNOSTIC ===")
print(report["diagnostic_status"].value_counts(dropna=False).to_string())

print("\n=== BY DRAFT YEAR ===")
print(
    report.pivot_table(
        index="draft_year",
        columns="diagnostic_status",
        values="pick",
        aggfunc="count",
        fill_value=0,
    ).to_string()
)

print("\n=== EXAMPLES: RECRUITING ID EXISTS, BUT NOT IN STATS ===")
print(
    report[report["diagnostic_status"] ==
           "recruiting ID exists but not found in college stats"]
    [["draft_year", "pick", "player_name", "college",
      "candidate_count", "candidates_with_athlete_id",
      "candidate_recruiting_classes"]]
    .head(20)
    .to_string(index=False)
)

print(f"\nDiagnostic saved: {out_path.relative_to(ROOT)}")
