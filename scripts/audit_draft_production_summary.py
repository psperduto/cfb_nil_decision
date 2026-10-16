import pandas as pd

P = "data/processed/"

summary = pd.read_csv(P + "draft_college_production_summary.csv")
history = pd.read_csv(P + "draft_college_season_history.csv")

keys = ["draft_year", "pick"]

print("ROW AND KEY CHECKS")
print("Summary rows:", len(summary))
print("Duplicate summary keys:", int(summary.duplicated(keys).sum()))
print("History rows:", len(history))

print("\nNEGATIVE PRODUCTION VALUES")
production_cols = [
    "passing_YDS", "passing_TD", "rushing_YDS", "rushing_TD",
    "receiving_REC", "receiving_YDS", "receiving_TD",
    "defensive_TOT", "defensive_SACKS",
]
for col in production_cols:
    if col in summary.columns:
        bad = summary[summary[col] < 0]
        if not bad.empty:
            print(f"\n{col}: {len(bad)} negative values")
            print(
                bad[["draft_year", "pick", "player_name", "college", col]]
                .head(10).to_string(index=False)
            )

print("\nCHECK SAMPLE PLAYERS AGAINST SEASON HISTORY")
names = ["Ashton Jeanty", "Tetairoa McMillan", "Colston Loveland"]
for name in names:
    rows = history[history["player_name"].eq(name)]
    print(f"\n{name}: {len(rows)} history rows")
    cols = [
        c for c in [
            "draft_year", "pick", "player_name", "season",
            "player", "team", "passing_YDS", "rushing_YDS",
            "receiving_YDS",
        ] if c in rows.columns
    ]
    print(rows[cols].to_string(index=False))

print("\nSTAT CATEGORY COVERAGE IN HISTORY")
for col in production_cols:
    if col in history.columns:
        print(f"{col}: {history[col].notna().sum():,} nonmissing rows")
