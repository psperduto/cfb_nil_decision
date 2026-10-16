import pandas as pd
from pathlib import Path

draft = pd.read_csv("data/processed/draft_results_2016_2025.csv")
diagnostic = pd.read_csv("data/processed/draft_missing_history_diagnostic.csv")

print("DRAFT ROWS:", len(draft))
print("DIAGNOSTIC ROWS:", len(diagnostic))
print("DRAFT UNIQUE YEAR/PICK:", draft[["draft_year", "pick"]].drop_duplicates().shape[0])
print("DIAGNOSTIC UNIQUE YEAR/PICK:", diagnostic[["draft_year", "pick"]].drop_duplicates().shape[0])

print("\nDuplicate draft year/pick records:")
print(draft[draft.duplicated(["draft_year", "pick"], keep=False)]
      .sort_values(["draft_year", "pick"])
      .to_string(index=False))

print("\nDuplicate diagnostic year/pick records:")
print(diagnostic[diagnostic.duplicated(["draft_year", "pick"], keep=False)]
      .sort_values(["draft_year", "pick"])
      .to_string(index=False))

print("\nDiagnostic categories:")
print(diagnostic["diagnostic_status"].value_counts(dropna=False).to_string())
