from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RECRUIT_DIR = ROOT / "data" / "processed" / "recruiting"
STATS_DIR = ROOT / "data" / "processed"

recruit_frames = []
for path in sorted(RECRUIT_DIR.glob("recruits_*_high_school.csv")):
    df = pd.read_csv(path, dtype={"athleteId": "string", "id": "string"})
    df["source_file"] = path.name
    recruit_frames.append(df)

recruits = pd.concat(recruit_frames, ignore_index=True)

stat_frames = []
for path in sorted(STATS_DIR.glob("player_stats_*_regular.csv")):
    df = pd.read_csv(path, dtype={"playerId": "string"})
    stat_frames.append(df[["playerId", "player", "season", "team"]])

stats = pd.concat(stat_frames, ignore_index=True)

recruit_ids = set(
    recruits["athleteId"].dropna().astype(str).str.strip()
) - {""}
stat_ids = set(
    stats["playerId"].dropna().astype(str).str.strip()
) - {""}

overlap = recruit_ids & stat_ids

print("=== IDENTIFIER OVERLAP ===")
print(f"Recruiting records: {len(recruits):,}")
print(f"Unique recruiting athlete IDs: {len(recruit_ids):,}")
print(f"Unique college-stat player IDs: {len(stat_ids):,}")
print(f"IDs appearing in both datasets: {len(overlap):,}")
print(
    "Recruiting ID overlap rate: "
    f"{len(overlap) / len(recruit_ids):.1%}"
    if recruit_ids else "Recruiting ID overlap rate: N/A"
)

print("\n=== RECRUITING ID COVERAGE BY CLASS ===")
coverage = (
    recruits.groupby("year", dropna=False)
    .agg(
        records=("name", "size"),
        populated_athlete_ids=("athleteId", "count"),
        unique_athlete_ids=("athleteId", "nunique"),
        unique_recruit_ids=("id", "nunique"),
    )
    .reset_index()
)
coverage["athlete_id_coverage"] = (
    coverage["populated_athlete_ids"] / coverage["records"]
)
print(coverage.to_string(index=False))

print("\n=== SAMPLE MATCHES BY ID ===")
if overlap:
    matched_recruits = recruits[
        recruits["athleteId"].astype("string").isin(overlap)
    ][["name", "year", "athleteId", "committedTo", "position"]]

    matched_stats = stats[
        stats["playerId"].astype("string").isin(overlap)
    ][["playerId", "player", "season", "team"]].drop_duplicates()

    sample = matched_recruits.merge(
        matched_stats,
        left_on="athleteId",
        right_on="playerId",
        how="inner",
    )
    print(sample.head(20).to_string(index=False))
else:
    print("No overlapping IDs found; investigate alternative identifiers.")

out = ROOT / "data" / "processed" / "cfbd_recruiting_identifier_audit.csv"
coverage.to_csv(out, index=False)
print(f"\nCoverage audit saved: {out.relative_to(ROOT)}")
