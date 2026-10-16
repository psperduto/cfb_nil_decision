from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "data" / "processed" / "draft_recruiting_match_candidates.csv"
out = ROOT / "data" / "processed" / "draft_recruiting_match_candidates_scored.csv"
summary_path = ROOT / "data" / "processed" / "draft_recruiting_match_quality_summary.csv"

df = pd.read_csv(path)

def normalize_college(value):
    if pd.isna(value):
        return ""
    value = "".join(ch.lower() for ch in str(value) if ch.isalnum())

    aliases = {
        "olemiss": "mississippi",
        "mississippi": "mississippi",
        "miami": "miamifl",
        "miamifl": "miamifl",
        "miamioh": "miamioh",
        "lsu": "lsu",
        "louisianastate": "lsu",
        "ucf": "ucf",
        "centralflorida": "ucf",
        "usc": "usc",
        "southerncalifornia": "usc",
        "pitt": "pittsburgh",
        "pittsburgh": "pittsburgh",
        "byu": "byu",
        "brighamyoung": "byu",
        "olemissrebels": "mississippi",
    }
    return aliases.get(value, value)

df["college_alias_agreement"] = (
    df["draft_college"].map(normalize_college)
    == df["recruit_committed_to"].map(normalize_college)
) & df["draft_college"].notna() & df["recruit_committed_to"].notna()

df["years_from_recruit_class_to_draft"] = pd.to_numeric(
    df["years_from_recruit_class_to_draft"], errors="coerce"
)
df["plausible_class_to_draft_timing"] = (
    df["years_from_recruit_class_to_draft"].between(1, 7)
)

df["match_tier"] = "review"
df.loc[
    df["plausible_class_to_draft_timing"]
    & df["college_alias_agreement"],
    "match_tier",
] = "name + college alias + timing"

df.loc[
    df["plausible_class_to_draft_timing"]
    & df["college_alias_agreement"]
    & df["athleteId"].notna(),
    "match_tier",
] = "strong candidate: name + college + timing + athlete ID"

df.loc[
    df["plausible_class_to_draft_timing"]
    & ~df["college_alias_agreement"],
    "match_tier",
] = "name + timing; college mismatch or transfer"

df.to_csv(out, index=False)

# Summarize per draft selection, not per candidate row.
player_summary = (
    df.groupby(["draft_year", "pick", "draft_player_name"], dropna=False)
    .agg(
        candidate_count=("recruit_name", "size"),
        any_college_agreement=("college_alias_agreement", "max"),
        any_plausible_timing=("plausible_class_to_draft_timing", "max"),
        any_college_and_timing=(
            "college_alias_agreement",
            lambda s: False,
        ),
    )
    .reset_index()
)

both = (
    df.assign(
        college_and_timing=(
            df["college_alias_agreement"]
            & df["plausible_class_to_draft_timing"]
        )
    )
    .groupby(["draft_year", "pick", "draft_player_name"])["college_and_timing"]
    .any()
    .reset_index()
)

player_summary = player_summary.drop(columns="any_college_and_timing").merge(
    both, on=["draft_year", "pick", "draft_player_name"], how="left"
)

summary = pd.DataFrame([{
    "drafted_players": 2563,
    "players_with_name_candidates": len(player_summary),
    "players_with_one_candidate": int((player_summary["candidate_count"] == 1).sum()),
    "players_with_multiple_candidates": int((player_summary["candidate_count"] > 1).sum()),
    "players_with_college_and_timing_candidate": int(player_summary["college_and_timing"].sum()),
    "candidate_rows_with_college_alias_agreement": int(df["college_alias_agreement"].sum()),
    "candidate_rows_with_plausible_timing": int(df["plausible_class_to_draft_timing"].sum()),
}])
summary.to_csv(summary_path, index=False)

print("=== MATCH QUALITY SUMMARY ===")
print(summary.to_string(index=False))

print("\n=== MATCH TIER COUNTS ===")
print(df["match_tier"].value_counts(dropna=False).to_string())

print("\n=== MULTIPLE-CANDIDATE EXAMPLES ===")
print(
    player_summary[player_summary["candidate_count"] > 1]
    .head(15)
    .to_string(index=False)
)

print(f"\nScored candidates: {out.relative_to(ROOT)}")
print(f"Summary: {summary_path.relative_to(ROOT)}")
