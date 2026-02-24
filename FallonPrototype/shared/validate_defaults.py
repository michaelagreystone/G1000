"""
Validation script for market_defaults.json.
Run after any edit to ensure data integrity before ingestion.

Usage: python -m FallonPrototype.shared.validate_defaults

Checks:
  (a) Every required variable from the Phase 1.1.1 schema is present
      for each market/program combination
  (b) No value is null without a note explaining why
  (c) All percentage values are in the 0-100 range (not 0-1)
  (d) All source strings are non-empty
"""

import json
import os
import sys

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULTS_PATH = os.path.join(_BASE_DIR, "data", "market_defaults", "market_defaults.json")

# Required variables by program type (from Phase 1.1.1 spec)
REQUIRED_MULTIFAMILY = [
    "rent_psf_monthly", "avg_unit_size_sf", "stabilized_occupancy_pct",
    "annual_rent_growth_pct", "lease_up_months", "other_income_per_unit_monthly",
    "hard_cost_psf", "soft_cost_pct_of_hard", "developer_fee_pct_of_total_cost",
    "contingency_pct_of_hard", "carry_cost_months",
    "construction_loan_ltc_pct", "construction_loan_rate_pct",
    "construction_loan_term_months", "equity_split_lp_pct",
    "preferred_return_pct", "promote_pct",
    "exit_cap_rate_pct", "exit_sale_cost_pct", "exit_year",
]

REQUIRED_OFFICE = [
    "rent_psf_annual_nnn", "stabilized_occupancy_pct", "lease_up_months",
    "free_rent_months", "ti_allowance_psf", "leasing_commission_pct",
    "hard_cost_psf", "soft_cost_pct_of_hard", "developer_fee_pct_of_total_cost",
    "contingency_pct_of_hard", "carry_cost_months",
    "construction_loan_ltc_pct", "construction_loan_rate_pct",
    "construction_loan_term_months", "equity_split_lp_pct",
    "preferred_return_pct", "promote_pct",
    "exit_cap_rate_pct", "exit_sale_cost_pct", "exit_year",
]

REQUIRED_HOTEL = [
    "adr", "stabilized_occupancy_pct", "revpar", "total_keys",
    "management_fee_pct", "ff_and_e_reserve_pct",
    "hard_cost_psf", "soft_cost_pct_of_hard", "developer_fee_pct_of_total_cost",
    "contingency_pct_of_hard", "carry_cost_months",
    "construction_loan_ltc_pct", "construction_loan_rate_pct",
    "construction_loan_term_months", "equity_split_lp_pct",
    "preferred_return_pct", "promote_pct",
    "exit_cap_rate_pct", "exit_sale_cost_pct", "exit_year",
]

REQUIRED_BY_PROGRAM = {
    "multifamily": REQUIRED_MULTIFAMILY,
    "office": REQUIRED_OFFICE,
    "hotel": REQUIRED_HOTEL,
}

# Expected market/program combinations
EXPECTED_COMBOS = {
    "charlotte": ["multifamily", "office"],
    "nashville": ["multifamily", "office", "hotel"],
    "boston": ["multifamily", "office"],
    "national_average": ["multifamily", "office", "hotel"],
}

# Variables that should be in the 0-100 range (percentages)
PCT_VARIABLES = [
    "stabilized_occupancy_pct", "annual_rent_growth_pct",
    "soft_cost_pct_of_hard", "developer_fee_pct_of_total_cost",
    "contingency_pct_of_hard", "construction_loan_ltc_pct",
    "construction_loan_rate_pct", "equity_split_lp_pct",
    "preferred_return_pct", "promote_pct", "exit_cap_rate_pct",
    "exit_sale_cost_pct", "management_fee_pct", "ff_and_e_reserve_pct",
    "leasing_commission_pct",
]


def validate(defaults_path: str | None = None) -> tuple[bool, list[str]]:
    """Validate market_defaults.json. Returns (passed, list_of_errors)."""
    path = defaults_path or _DEFAULTS_PATH
    errors = []

    if not os.path.exists(path):
        return False, [f"File not found: {path}"]

    with open(path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]

    # Check all expected market/program combos exist
    for market, programs in EXPECTED_COMBOS.items():
        if market not in data:
            errors.append(f"MISSING MARKET: '{market}' not found in JSON")
            continue

        # Check _meta block
        if "_meta" not in data[market]:
            errors.append(f"MISSING META: '{market}._meta' block not found")
        else:
            meta = data[market]["_meta"]
            for key in ["last_updated", "data_quality", "update_notes"]:
                if key not in meta:
                    errors.append(f"MISSING META FIELD: '{market}._meta.{key}'")

        for program in programs:
            if program not in data[market]:
                errors.append(f"MISSING PROGRAM: '{market}.{program}' not found")
                continue

            required_vars = REQUIRED_BY_PROGRAM.get(program, [])
            program_data = data[market][program]

            for var in required_vars:
                if var not in program_data:
                    errors.append(f"MISSING VARIABLE: '{market}.{program}.{var}'")
                    continue

                entry = program_data[var]

                # Check structure: must have value, unit, source
                if not isinstance(entry, dict):
                    errors.append(f"BAD FORMAT: '{market}.{program}.{var}' is not a dict")
                    continue

                for key in ["value", "unit", "source"]:
                    if key not in entry:
                        errors.append(f"MISSING KEY: '{market}.{program}.{var}.{key}'")

                # Check null values
                if entry.get("value") is None:
                    errors.append(
                        f"NULL VALUE: '{market}.{program}.{var}' — "
                        "add a note explaining why or provide a value"
                    )

                # Check percentage range (0-100, not 0-1)
                if var in PCT_VARIABLES and entry.get("value") is not None:
                    val = entry["value"]
                    if isinstance(val, (int, float)) and (val < 0 or val > 100):
                        errors.append(
                            f"PCT OUT OF RANGE: '{market}.{program}.{var}' = {val} "
                            "(expected 0-100)"
                        )

                # Check source is non-empty
                if "source" in entry and (
                    not entry["source"] or not entry["source"].strip()
                ):
                    errors.append(
                        f"EMPTY SOURCE: '{market}.{program}.{var}' has blank source"
                    )

    return len(errors) == 0, errors


def main():
    print("=" * 60)
    print("MARKET DEFAULTS VALIDATION")
    print("=" * 60)
    print(f"File: {_DEFAULTS_PATH}\n")

    passed, errors = validate()

    if passed:
        print("RESULT: PASS — all checks passed")
        print(f"Validated {len(EXPECTED_COMBOS)} markets, "
              f"{sum(len(v) for v in EXPECTED_COMBOS.values())} program combinations")
    else:
        print(f"RESULT: FAIL — {len(errors)} issue(s) found:\n")
        for i, err in enumerate(errors, 1):
            print(f"  {i}. {err}")

    print("=" * 60)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
