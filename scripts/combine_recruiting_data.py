from pathlib import Path
import pandas as pd

source_dir = Path("data/processed/recruiting")
output_path = Path("data/processed/recruiting_players_2000_2025.csv")

files = sorted(source_dir.glob("recruits_*_high_school.csv"))

if not files:
    raise FileNotFoundError(f"No recruiting CSVs found in {source_dir}")

frames = []
for path in files:
    df = pd.read_csv(path, low_memory=False)
    df["source_file"] = path.name
    frames.append(df)

combined = pd.concat(frames, ignore_index=True, sort=False)

# Preserve source records and identifiers; do not drop rows with missing IDs.
combined.to_csv(output_path, index=False)

print(f"Files combined: {len(files)}")
print(f"Rows: {len(combined):,}")
print(f"Columns: {len(combined.columns)}")
print(f"Missing athleteId: {combined['athleteId'].isna().sum():,}"
      if "athleteId" in combined.columns else "athleteId column not found")
print(f"Unique nonmissing athleteId: {combined['athleteId'].nunique():,}"
      if "athleteId" in combined.columns else "")
print(f"Output: {output_path}")
print(f"Output size: {output_path.stat().st_size / (1024 * 1024):.2f} MB")
print("\nRecruiting year counts:")
if "year" in combined.columns:
    print(combined.groupby("year").size().to_string())
