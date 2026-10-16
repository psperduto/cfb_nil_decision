import pandas as pd

path = "data/processed/recruiting_players_2000_2025.csv"
df = pd.read_csv(path, low_memory=False)

print("SHAPE:", df.shape)
print("\nCOLUMNS:")
print(df.columns.tolist())

print("\nROWS BY RECRUITING YEAR:")
print(df.groupby("year").size().to_string())

print("\nRECRUIT TYPE:")
print(df["recruitType"].value_counts(dropna=False).to_string())

print("\nMISSINGNESS — KEY FIELDS:")
for col in ["athleteId", "name", "year", "position", "stars", "rating", "committedTo"]:
    if col in df.columns:
        print(f"{col}: {df[col].isna().sum():,} missing ({df[col].isna().mean():.1%})")

print("\nSOURCE FILES:", df["source_file"].nunique())
