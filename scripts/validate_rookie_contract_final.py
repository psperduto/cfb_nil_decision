import polars as pl

path = "data/processed/draft_rookie_contracts_2016_2025.csv"
df = pl.read_csv(path)

assert df.height == 2563, f"Unexpected row count: {df.height}"

duplicate_keys = (
    df.group_by(["draft_year", "pick"])
    .len()
    .filter(pl.col("len") > 1)
)
assert duplicate_keys.height == 0, "Duplicate draft-pick keys found"

print(f"Rows: {df.height:,}")
print("Unique draft picks:", df.select(
    pl.struct(["draft_year", "pick"]).n_unique()
).item())

print("\nStatus counts:")
print(
    df.group_by("contract_record_status")
    .len()
    .sort("contract_record_status")
)

print("\nRemaining conflict rows:")
print(
    df.filter(
        pl.col("contract_record_status") == "contract_terms_conflict"
    ).select(["draft_year", "pick", "player_name"])
)

print("\nExcluded financial records:")
print(
    df.filter(
        pl.col("contract_record_status") == "excluded_material_conflict"
    ).select([
        "draft_year", "pick", "player_name",
        "rookie_contract_value_millions",
        "rookie_contract_apy_millions",
        "rookie_contract_guarantees_millions",
    ])
)
