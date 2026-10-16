from pathlib import Path

path = Path("scripts/build_rookie_contract_dataset.py")
source = path.read_text(encoding="utf-8-sig")

old_helper = '''def agreed_value(records, field):
    """
    Return a field only when all available nonmissing values agree.
    Conflicting values become null instead of being averaged.
    """
    values = distinct_values(records, field)
    return values[0] if len(values) == 1 else None
'''

new_helper = '''def agreed_value(records, field):
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
'''

if old_helper not in source:
    raise SystemExit(
        "Expected agreed_value function was not found. "
        "No changes saved."
    )

source = source.replace(old_helper, new_helper, 1)

replacements = {
    '    value = agreed_value(profiles, "value")':
    '    value = resolved_financial_value(profiles, "value")',

    '    apy = agreed_value(profiles, "apy")':
    '    apy = resolved_financial_value(profiles, "apy")',

    '    guarantees = agreed_value(profiles, "guarantees")':
    '    guarantees = resolved_financial_value(profiles, "guarantees")',

    '                    or len(value_values) > 1\n'
    '                    or len(apy_values) > 1\n'
    '                    or len(guarantee_values) > 1':
    '                    or financial_conflict(profiles, "value")\n'
    '                    or financial_conflict(profiles, "apy")\n'
    '                    or financial_conflict(profiles, "guarantees")',

    '"contract_value_conflict": len(value_values) > 1':
    '"contract_value_conflict": financial_conflict(profiles, "value")',

    '"apy_conflict": len(apy_values) > 1':
    '"apy_conflict": financial_conflict(profiles, "apy")',

    '"guarantees_conflict": len(guarantee_values) > 1':
    '"guarantees_conflict": financial_conflict(profiles, "guarantees")',
}

for old, new in replacements.items():
    if old not in source:
        raise SystemExit(
            f"Expected code was not found:\n{old}\nNo changes saved."
        )
    source = source.replace(old, new, 1)

path.write_text(source, encoding="utf-8")
print(f"Updated {path}")
