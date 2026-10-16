import math
from collections import defaultdict

import nflreadpy
import polars as pl


START_YEAR = 2016
END_YEAR = 2025

OUTPUT_PATH = (
    "data/processed/draft_rookie_contracts_2016_2025.csv"
)


def to_int(value):
    """Convert a usable value to int; return None for missing values."""
    if value is None:
        return None
    try:
        number = float(value)
        if not math.isfinite(number):
            return None
        return int(number)
    except (TypeError, ValueError):
        return None


def to_float(value):
    """Convert a usable value to float; return None for missing values."""
    if value is None:
        return None
    try:
        number = float(value)
        if not math.isfinite(number):
            return None
        return number
    except (TypeError, ValueError):
        return None


def distinct_values(records, field):
    """Return sorted distinct nonmissing values for one financial field."""
    values = {
        record[field]
        for record in records
        if record[field] is not None
    }
    return sorted(values)


def agreed_value(records, field):
    """
    Return a field only when all available nonmissing values agree.
    """
    values = distinct_values(records, field)
    return values[0] if len(values) == 1 else None


# Contract amounts are reported in millions. Ten dollars is therefore
# 0.00001 million. This tolerance affects conflict detection only.
TOLERANCE_MILLIONS = 10 / 1_000_000


def financial_conflict(records, field):
    """Flag financial differences greater than ten actual dollars."""
    values = distinct_values(records, field)
    return (
        len(values) > 1
        and max(values) - min(values) > TOLERANCE_MILLIONS
    )


def resolved_financial_value(records, field):
    """
    Keep a reported value when records agree within ten dollars.
    Return null for material conflicts; never average source values.
    """
    values = distinct_values(records, field)

    if not values:
        return None

    if max(values) - min(values) <= TOLERANCE_MILLIONS:
        return min(values)

    return None


# ------------------------------------------------------------
# 1. Load contract history and collect draft-year records.
# ------------------------------------------------------------

source = nflreadpy.load_contracts()

candidates = defaultdict(list)

for row in source.iter_rows(named=True):
    draft_year = to_int(row.get("draft_year"))
    pick = to_int(row.get("draft_overall"))

    if draft_year is None or pick is None:
        continue

    if not START_YEAR <= draft_year <= END_YEAR:
        continue

    for contract in row.get("contract_history") or []:
        signed_year = to_int(contract.get("year_signed"))

        if signed_year != draft_year:
            continue

        contract_type = contract.get("contract_type")

        if contract_type not in {"Drafted", "SFA"}:
            continue

        candidates[(draft_year, pick)].append({
            "player": row.get("player"),
            "gsis_id": row.get("gsis_id"),
            "otc_id": row.get("otc_id"),
            "contract_type": contract_type,
            "years": to_int(contract.get("yrs")),
            "value": to_float(contract.get("total")),
            "apy": to_float(contract.get("apy")),
            "guarantees": to_float(contract.get("guarantees")),
            "team": contract.get("team"),
            "status": contract.get("status"),
        })


# ------------------------------------------------------------
# 2. Resolve each draft pick using explicit selection rules.
# ------------------------------------------------------------

def build_contract_record(draft_year, pick, records):
    drafted = [
        record for record in records
        if record["contract_type"] == "Drafted"
    ]

    if drafted:
        selected_type = "Drafted"
        selected = drafted
    else:
        selected_type = "SFA"
        selected = [
            record for record in records
            if record["contract_type"] == "SFA"
        ]

    # Remove repeated representations of the same financial terms.
    # Team and status are intentionally excluded from this key.
    unique_profiles = {}

    for record in selected:
        profile = (
            record["years"],
            record["value"],
            record["apy"],
            record["guarantees"],
        )
        unique_profiles.setdefault(profile, record)

    profiles = list(unique_profiles.values())

    # If there is a unique longest term, discard shorter alternative
    # profiles. If the longest term is tied, retain the tied profiles
    # and resolve each financial field independently below.
    known_years = [
        record["years"] for record in profiles
        if record["years"] is not None
    ]

    if known_years:
        longest = max(known_years)
        longest_profiles = [
            record for record in profiles
            if record["years"] == longest
        ]

        if len(longest_profiles) == 1:
            profiles = longest_profiles

    years_values = distinct_values(profiles, "years")
    value_values = distinct_values(profiles, "value")
    apy_values = distinct_values(profiles, "apy")
    guarantee_values = distinct_values(profiles, "guarantees")

    years = agreed_value(profiles, "years")
    value = resolved_financial_value(profiles, "value")
    apy = resolved_financial_value(profiles, "apy")
    guarantees = resolved_financial_value(profiles, "guarantees")

    has_record = bool(profiles)

    return {
        "draft_year": draft_year,
        "pick": pick,
        "source_player_count": len({
            record["player"]
            for record in selected
            if record["player"]
        }),
        "source_player_names": "|".join(sorted({
            str(record["player"])
            for record in selected
            if record["player"]
        })),
        "gsis_ids": "|".join(sorted({
            str(record["gsis_id"])
            for record in selected
            if record["gsis_id"]
        })),
        "otc_ids": "|".join(sorted({
            str(record["otc_id"])
            for record in selected
            if record["otc_id"] is not None
        })),
        "selected_contract_type": selected_type if has_record else None,
        "distinct_financial_profiles": len(profiles),
        "contract_record_status": (
            "no_rookie_contract_record"
            if not has_record
            else (
                "contract_terms_conflict"
                if (
                    len(years_values) > 1
                    or financial_conflict(profiles, "value")
                    or financial_conflict(profiles, "apy")
                    or financial_conflict(profiles, "guarantees")
                )
                else "consistent_reported_terms"
            )
        ),
        "rookie_contract_years": years,
        "rookie_contract_value_millions": value,
        "rookie_contract_apy_millions": apy,
        "rookie_contract_guarantees_millions": guarantees,
        "years_conflict": len(years_values) > 1,
        "contract_value_conflict": financial_conflict(profiles, "value"),
        "apy_conflict": financial_conflict(profiles, "apy"),
        "guarantees_conflict": financial_conflict(profiles, "guarantees"),
    }


resolved = []

for (draft_year, pick), records in candidates.items():
    resolved.append(
        build_contract_record(draft_year, pick, records)
    )

contract_df = pl.DataFrame(resolved) if resolved else pl.DataFrame()


# ------------------------------------------------------------
# 3. Join onto the complete official draft-pick table.
# ------------------------------------------------------------

draft = pl.read_csv(
    "data/processed/draft_results_2016_2025.csv"
)

draft = draft.with_columns([
    pl.col("draft_year").cast(pl.Int64),
    pl.col("pick").cast(pl.Int64),
])

result = draft.join(
    contract_df,
    on=["draft_year", "pick"],
    how="left",
)

result = result.with_columns([
    pl.col("contract_record_status").fill_null(
        "no_rookie_contract_record"
    ),
    pl.col("years_conflict").fill_null(False),
    pl.col("contract_value_conflict").fill_null(False),
    pl.col("apy_conflict").fill_null(False),
    pl.col("guarantees_conflict").fill_null(False),
])

# Exclude materially conflicting rookie-contract financial terms.
# Keep the draft picks in the dataset, but do not use disputed values.
excluded_players = {
    (2016, 232): "Steven Daniels",
    (2016, 248): "Austin Blythe",
    (2017, 73): "Jordan Willis",
}

for (year, pick), expected_name in excluded_players.items():
    mask = (
        (pl.col("draft_year") == year)
        & (pl.col("pick") == pick)
    )

    result = result.with_columns([
        pl.when(mask)
        .then(pl.lit("excluded_material_conflict"))
        .otherwise(pl.col("contract_record_status"))
        .alias("contract_record_status"),

        pl.when(mask)
        .then(pl.lit(None, dtype=pl.Float64))
        .otherwise(pl.col("rookie_contract_value_millions"))
        .alias("rookie_contract_value_millions"),

        pl.when(mask)
        .then(pl.lit(None, dtype=pl.Float64))
        .otherwise(pl.col("rookie_contract_apy_millions"))
        .alias("rookie_contract_apy_millions"),

        pl.when(mask)
        .then(pl.lit(None, dtype=pl.Float64))
        .otherwise(pl.col("rookie_contract_guarantees_millions"))
        .alias("rookie_contract_guarantees_millions"),
    ])

    matched = result.filter(mask)
    if matched.height != 1:
        raise ValueError(
            f"Expected exactly one draft pick for {year}, pick {pick}"
        )

    actual_name = matched["player_name"][0]
    if actual_name != expected_name:
        raise ValueError(
            f"Expected {expected_name} at {year}, pick {pick}; "
            f"found {actual_name}"
        )

result = result.sort(["draft_year", "pick"])

result.write_csv(OUTPUT_PATH)


# ------------------------------------------------------------
# 4. Print a compact validation summary.
# ------------------------------------------------------------

print(f"Saved: {OUTPUT_PATH}")
print(f"Draft picks: {result.height:,}")
print(
    "Unique draft picks: "
    f"{result.select(pl.struct(['draft_year', 'pick']).n_unique()).item():,}"
)

print("\nContract record status:")
print(
    result.group_by("contract_record_status")
    .len()
    .sort("contract_record_status")
)

print("\nField-level conflicts:")
for field in [
    "years_conflict",
    "contract_value_conflict",
    "apy_conflict",
    "guarantees_conflict",
]:
    print(
        f"{field}: "
        f"{result.filter(pl.col(field)).height:,}"
    )

print("\nRows with no rookie-contract record:")
print(
    result.filter(
        pl.col("contract_record_status") == "no_rookie_contract_record"
    ).select(["draft_year", "pick", "player_name"])
)

