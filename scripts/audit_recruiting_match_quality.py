from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RECRUIT_DIR = ROOT / "data" / "processed" / "recruiting"
STATS_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "data" / "processed"

def normalize_name(value):
    if pd.isna(value):
        return ""
    value = str(value).lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]", "", value)

recruit_frames = [
    pd.read_csv(path, dtype={"athleteId": "string", "id": "string"})
    for path in sorted(RECRUIT_DIR.glob("recruits_*_high_school.csv"))
]
recruits = pd.concat(recruit_frames, ignore_index=True)

stat_frames = []
for path in sorted(STATS_DIR.glob("player_stats_*_regular.csv")):
    df = pd.read_csv(path, dtype={"playerId": "string"})
    stat_frames.append(df[["playerId", "player", "season", "team"]])
stats = pd.concat(stat_frames, ignore_index=True)

recruits["athleteId"] = recruits["athleteId"].astype("string").str.strip()
stats["playerId"] = stats["playerId"].astype("string").str.strip()

recruits = recruits[
    recruits["athleteId"].notna() & recruits["athleteId"].ne("")
].copy()
stats = stats[
    stats["playerId"].notna() & stats["playerId"].ne("")
].copy()

recruits["normalized_recruit_name"] = recruits["name"].map(normalize_name)
stats["normalized_player_name"] = stats["player"].map(normalize_name)

# One row per athlete ID, with all distinct names and recruiting classes.
recruit_id_audit = (
    recruits.groupby("athleteId")
    .agg(
        recruit_records=("id", "size"),
        recruit_names=("name", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
        recruit_classes=("year", lambda s: " | ".join(map(str, sorted(set(s.dropna().astype(int)))))),
        committed_teams=("committedTo", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
        recruit_name_variants=("normalized_recruit_name", "nunique"),
        recruit_class_variants=("year", "nunique"),
    )
    .reset_index()
)

# Summarize each stats ID across the observed seasons.
stats_id_audit = (
    stats.groupby("playerId")
    .agg(
        stats_records=("player", "size"),
        stats_names=("player", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
        stats_name_variants=("normalized_player_name", "nunique"),
        first_stats_season=("season", "min"),
        last_stats_season=("season", "max"),
        stat_teams=("team", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
    )
    .reset_index()
)

matched = recruit_id_audit.merge(
    stats_id_audit,
    left_on="athleteId",
    right_on="playerId",
    how="inner",
)

matched["recruit_name_set"] = matched["recruit_names"].map(
    lambda s: {normalize_name(x) for x in s.split(" | ") if x}
)
matched["stats_name_set"] = matched["stats_names"].map(
    lambda s: {normalize_name(x) for x in s.split(" | ") if x}
)
matched["any_name_agreement"] = matched.apply(
    lambda r: bool(r["recruit_name_set"] & r["stats_name_set"]), axis=1
)

matched["recruit_class_list"] = matched["recruit_classes"].map(
    lambda s: [int(x) for x in s.split(" | ") if x]
)
matched["earliest_recruit_class"] = matched["recruit_class_list"].map(min)
matched["years_until_first_observed_stats"] = (
    matched["first_stats_season"] - matched["earliest_recruit_class"]
)
matched["plausible_timing_1_to_7_years"] = (
    matched["years_until_first_observed_stats"].between(1, 7)
)

print("=== MATCH QUALITY SUMMARY ===")
print(f"Overlapping IDs: {len(matched):,}")
print(f"IDs with any normalized name agreement: {matched['any_name_agreement'].sum():,} "
      f"({matched['any_name_agreement'].mean():.1%})")
print(f"IDs with plausible 1–7 year timing: "
      f"{matched['plausible_timing_1_to_7_years'].sum():,} "
      f"({matched['plausible_timing_1_to_7_years'].mean():.1%})")
print(f"IDs with both name agreement and plausible timing: "
      f"{(matched['any_name_agreement'] & matched['plausible_timing_1_to_7_years']).sum():,}")

print("\n=== EXAMPLE NAME DISAGREEMENTS ===")
bad_names = matched[~matched["any_name_agreement"]]
print(bad_names[
    ["athleteId", "recruit_names", "recruit_classes", "stats_names",
     "first_stats_season", "years_until_first_observed_stats"]
].head(25).to_string(index=False))

print("\n=== DUPLICATE RECRUITING IDENTIFIERS ===")
duplicate_recruits = recruits[
    recruits.duplicated("athleteId", keep=False)
].sort_values(["athleteId", "year"])
print(f"Recruiting rows with a repeated athleteId: {len(duplicate_recruits):,}")
print(duplicate_recruits[
    ["athleteId", "id", "name", "year", "committedTo"]
].head(25).to_string(index=False))

matched.drop(columns=["recruit_name_set", "stats_name_set", "recruit_class_list"]).to_csv(
    OUT_DIR / "cfbd_recruiting_match_quality.csv", index=False
)
print("\nDetailed audit saved: data/processed/cfbd_recruiting_match_quality.csv")
