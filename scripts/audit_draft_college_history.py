from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STATS_DIR = ROOT / "data" / "processed"
RECRUIT_DIR = STATS_DIR / "recruiting"

candidate_path = STATS_DIR / "draft_recruiting_match_candidates_scored.csv"
out_path = STATS_DIR / "draft_recruiting_college_history_audit.csv"
summary_path = STATS_DIR / "draft_recruiting_college_history_summary.csv"


def clean_id(series):
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .replace("", pd.NA)
    )


candidates = pd.read_csv(candidate_path, dtype={"athleteId": "string"})
candidates["athleteId"] = clean_id(candidates["athleteId"])

stat_files = sorted(STATS_DIR.glob("player_stats_*_regular.csv"))
stats = pd.concat(
    [
        pd.read_csv(
            path,
            dtype={"playerId": "string"},
            usecols=["playerId", "player", "season", "team", "position"],
        )
        for path in stat_files
    ],
    ignore_index=True,
)

stats["playerId"] = clean_id(stats["playerId"])
stats = stats.dropna(subset=["playerId"])

history = (
    stats.groupby("playerId")
    .agg(
        stats_names=("player", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
        stats_teams=("team", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
        stats_positions=("position", lambda s: " | ".join(sorted(set(s.dropna().astype(str))))),
        first_observed_season=("season", "min"),
        last_observed_season=("season", "max"),
        observed_seasons=("season", lambda s: " | ".join(
            map(str, sorted(set(pd.to_numeric(s, errors="coerce").dropna().astype(int))))
        )),
    )
    .reset_index()
)

audit = candidates.merge(
    history,
    left_on="athleteId",
    right_on="playerId",
    how="left",
    validate="many_to_one",
)

def normalize(value):
    if pd.isna(value):
        return ""
    return "".join(ch.lower() for ch in str(value) if ch.isalnum())


def normalize_college(value):
    key = normalize(value)
    aliases = {
        "olemiss": "mississippi",
        "mississippi": "mississippi",
        "louisianastate": "lsu",
        "lsu": "lsu",
        "centralflorida": "ucf",
        "ucf": "ucf",
        "southerncalifornia": "usc",
        "usc": "usc",
        "brighamyoung": "byu",
        "byu": "byu",
        "pitt": "pittsburgh",
        "pittsburgh": "pittsburgh",
        "miami": "miamifl",
        "miamifl": "miamifl",
    }
    return aliases.get(key, key)


team_keys = (
    stats.assign(team_key=stats["team"].map(normalize_college))
    .groupby("playerId")["team_key"]
    .agg(lambda values: {value for value in values.dropna() if value})
    .to_dict()
)

audit["draft_college_key"] = audit["draft_college"].map(normalize_college)
audit["draft_college_seen_in_stats"] = audit.apply(
    lambda row: (
        bool(row["draft_college_key"])
        and row["draft_college_key"]
        in team_keys.get(row["athleteId"], set())
    ),
    axis=1,
)
audit["has_college_history"] = audit["playerId"].notna()

audit["history_match_assessment"] = "no linked college-stat history"
audit.loc[
    audit["has_college_history"] & audit["draft_college_seen_in_stats"],
    "history_match_assessment",
] = "draft college found in linked stats"
audit.loc[
    audit["has_college_history"] & ~audit["draft_college_seen_in_stats"],
    "history_match_assessment",
] = "linked history found; draft college not observed"

audit.to_csv(out_path, index=False)

per_draft = (
    audit.groupby(["draft_year", "pick", "draft_player_name"], dropna=False)
    .agg(
        candidate_count=("recruit_name", "size"),
        any_college_history=("has_college_history", "max"),
        any_draft_college_seen=("draft_college_seen_in_stats", "max"),
    )
    .reset_index()
)

summary = pd.DataFrame([{
    "draft_players_with_name_candidates": len(per_draft),
    "players_with_any_linked_college_history": int(per_draft["any_college_history"].sum()),
    "players_with_draft_college_seen_in_stats": int(per_draft["any_draft_college_seen"].sum()),
    "candidate_rows": len(audit),
    "candidate_rows_with_college_history": int(audit["has_college_history"].sum()),
    "candidate_rows_with_draft_college_seen_in_stats": int(audit["draft_college_seen_in_stats"].sum()),
}])
summary.to_csv(summary_path, index=False)

print("=== COLLEGE HISTORY MATCH SUMMARY ===")
print(summary.to_string(index=False))

print("\n=== ASSESSMENTS ===")
print(audit["history_match_assessment"].value_counts().to_string())

print("\n=== JARED GOFF CHECK ===")
print(
    audit[audit["draft_player_name"].eq("Jared Goff")][
        ["draft_year", "draft_player_name", "athleteId", "stats_names",
         "stats_teams", "observed_seasons", "draft_college_seen_in_stats"]
    ].head(10).to_string(index=False)
)

print(f"\nAudit saved: {out_path.relative_to(ROOT)}")
print(f"Summary saved: {summary_path.relative_to(ROOT)}")
