from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RECRUIT_DIR = ROOT / "data" / "processed" / "recruiting"
STATS_DIR = ROOT / "data" / "processed"

DRAFT_PATH = STATS_DIR / "draft_results_2016_2025.csv"
OUT_PATH = STATS_DIR / "draft_recruiting_match_candidates.csv"
SUMMARY_PATH = STATS_DIR / "draft_recruiting_match_audit.csv"


def normalize(value):
    if pd.isna(value):
        return ""
    value = str(value).lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]", "", value)


draft = pd.read_csv(DRAFT_PATH)
recruits = pd.concat(
    [
        pd.read_csv(p, dtype={"athleteId": "string"})
        for p in sorted(RECRUIT_DIR.glob("recruits_*_high_school.csv"))
    ],
    ignore_index=True,
)

draft["name_key"] = draft["player_name"].map(normalize)
draft["college_key"] = draft["college"].map(normalize)
recruits["name_key"] = recruits["name"].map(normalize)
recruits["college_key"] = recruits["committedTo"].map(normalize)

# A draft player can have multiple recruiting candidates with the same
# normalized name, so preserve candidates rather than forcing a match.
candidate_rows = []

for _, player in draft.iterrows():
    candidates = recruits[recruits["name_key"] == player["name_key"]]

    for _, recruit in candidates.iterrows():
        class_year = pd.to_numeric(recruit.get("year"), errors="coerce")
        draft_year = pd.to_numeric(player.get("draft_year"), errors="coerce")
        years_to_draft = (
            draft_year - class_year
            if pd.notna(draft_year) and pd.notna(class_year)
            else None
        )

        candidate_rows.append({
            "draft_year": player["draft_year"],
            "round": player["round"],
            "pick": player["pick"],
            "draft_player_name": player["player_name"],
            "draft_college": player["college"],
            "draft_position": player["position"],
            "recruit_name": recruit["name"],
            "recruit_class_year": recruit["year"],
            "recruit_committed_to": recruit["committedTo"],
            "recruit_position": recruit["position"],
            "recruit_stars": recruit["stars"],
            "recruit_rating": recruit["rating"],
            "recruit_ranking": recruit["ranking"],
            "athleteId": recruit["athleteId"],
            "name_exact_normalized": True,
            "college_exact_normalized": (
                player["college_key"] != ""
                and player["college_key"] == recruit["college_key"]
            ),
            "years_from_recruit_class_to_draft": years_to_draft,
            "plausible_class_to_draft_timing": (
                years_to_draft is not None and 1 <= years_to_draft <= 7
            ),
        })

candidates = pd.DataFrame(candidate_rows)

if candidates.empty:
    candidates = pd.DataFrame(columns=[
        "draft_year", "round", "pick", "draft_player_name",
        "draft_college", "recruit_name", "recruit_class_year",
        "recruit_committed_to", "athleteId"
    ])
else:
    candidates = candidates.sort_values(
        ["draft_year", "pick", "college_exact_normalized",
         "plausible_class_to_draft_timing"],
        ascending=[True, True, False, False],
    )

candidates.to_csv(OUT_PATH, index=False)

matched_draft_keys = set(candidates["draft_year"].astype(str) + "|" +
                         candidates["pick"].astype(str)) if len(candidates) else set()
draft_keys = draft["draft_year"].astype(str) + "|" + draft["pick"].astype(str)

summary = pd.DataFrame([{
    "draft_rows": len(draft),
    "draft_players_with_exact_normalized_name_candidate": len(matched_draft_keys),
    "draft_players_without_name_candidate": len(draft) - len(matched_draft_keys),
    "candidate_rows": len(candidates),
    "candidates_with_college_agreement": int(
        candidates["college_exact_normalized"].sum()
    ) if len(candidates) else 0,
    "candidates_with_plausible_class_to_draft_timing": int(
        candidates["plausible_class_to_draft_timing"].sum()
    ) if len(candidates) else 0,
}])
summary.to_csv(SUMMARY_PATH, index=False)

print("=== DRAFT-TO-RECRUITING MATCH AUDIT ===")
print(summary.to_string(index=False))
print(f"\nCandidate file: {OUT_PATH.relative_to(ROOT)}")
print(f"Summary file: {SUMMARY_PATH.relative_to(ROOT)}")
print("\nFirst 20 candidate rows:")
if len(candidates):
    print(candidates.head(20).to_string(index=False))
