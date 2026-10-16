import pandas as pd

path = "data/processed/college_player_season_stats.csv"
df = pd.read_csv(path)

keys = ["season", "playerId", "player", "position", "team", "conference"]

print("ROWS:", len(df))
print("DUPLICATE PLAYER-SEASON-TEAM KEYS:", int(df.duplicated(keys).sum()))
print("MISSING PLAYER IDs:", int(df["playerId"].isna().sum()))
print("MISSING SEASONS:", int(df["season"].isna().sum()))

print("\nROWS BY SEASON")
print(df.groupby("season").size().to_string())

print("\nPLAYERS WITH MULTIPLE TEAMS IN A SEASON")
team_counts = df.groupby(["season", "playerId"])["team"].nunique()
print("Player-season combinations:", len(team_counts))
print("With multiple teams:", int((team_counts > 1).sum()))
print("Maximum teams for one player in one season:", int(team_counts.max()))

print("\nMISSINGNESS OF CORE PRODUCTION FIELDS")
core = [
    "passing_YDS", "passing_TD", "passing_INT",
    "rushing_YDS", "rushing_TD",
    "receiving_REC", "receiving_YDS", "receiving_TD",
    "defensive_TOT", "defensive_SACKS",
]
for col in core:
    if col in df.columns:
        print(f"{col}: {df[col].isna().mean():.1%} missing")

print("\nSAMPLE PLAYER-SEASON ROWS")
print(
    df[["season", "player", "position", "team",
        "passing_YDS", "rushing_YDS", "receiving_YDS",
        "defensive_TOT"]]
    .head(12)
    .to_string(index=False)
)
