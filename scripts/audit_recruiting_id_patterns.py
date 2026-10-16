import pandas as pd

recruits = pd.concat(
    [
        pd.read_csv(f"data/processed/recruiting/recruits_{year}_high_school.csv")
        for year in range(2000, 2026)
    ],
    ignore_index=True
)

stats = pd.concat(
    [
        pd.read_csv(f"data/processed/player_stats_{year}_regular.csv",
                    usecols=["playerId", "player", "season"])
        for year in range(2016, 2026)
    ],
    ignore_index=True
)

recruits["athleteId_num"] = pd.to_numeric(
    recruits["athleteId"], errors="coerce"
)

print("RECRUITING ID COUNTS")
print("Total recruiting rows:", len(recruits))
print("Missing IDs:", recruits["athleteId_num"].isna().sum())
print("Negative IDs:", (recruits["athleteId_num"] < 0).sum())
print("Zero IDs:", (recruits["athleteId_num"] == 0).sum())
print("Positive IDs:", (recruits["athleteId_num"] > 0).sum())

print("\nNEGATIVE-ID EXAMPLES")
cols = [c for c in ["name", "year", "committedTo", "athleteId", "id"] if c in recruits.columns]
print(recruits.loc[recruits["athleteId_num"] < 0, cols].head(25).to_string(index=False))

stats_ids = set(pd.to_numeric(stats["playerId"], errors="coerce").dropna())
recruit_ids = set(recruits["athleteId_num"].dropna())

print("\nID OVERLAP")
print("Unique positive recruiting IDs:", sum(x > 0 for x in recruit_ids))
print("Positive recruiting IDs found in stats:", sum(x > 0 and x in stats_ids for x in recruit_ids))
print("Negative recruiting IDs found in stats:", sum(x < 0 and x in stats_ids for x in recruit_ids))
