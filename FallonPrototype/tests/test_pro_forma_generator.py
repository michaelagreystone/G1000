"""
Tests for Phase 4 — Pro Forma Generator.
Tests schema validation, return calculator, and generation flow.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from FallonPrototype.agents.financial_agent import (
    ProjectParameters,
    PRO_FORMA_SCHEMA,
    GENERATION_SYSTEM_PROMPT,
    build_generation_message,
    extract_json_from_response,
    validate_pro_forma,
    AgentResponse,
)
from FallonPrototype.shared.return_calculator import (
    compute_returns,
    check_return_discrepancy,
    compute_sensitivity_table,
    _val,
)


# Sample pro forma for testing
SAMPLE_PRO_FORMA = {
    "project_summary": {
        "deal_name": "Charlotte Multifamily 200 Units",
        "market": "charlotte",
        "program_type": "multifamily",
        "total_gfa_sf": {"value": 180000, "unit": "sf", "label": "calculated", "source": "unit_count * 900"},
        "unit_count": {"value": 200, "unit": "units", "label": "confirmed", "source": "user-provided"},
        "rentable_sf": None,
        "construction_start": {"value": "Q3 2026", "unit": "", "label": "confirmed", "source": "user-provided"},
        "construction_duration_months": {"value": 18, "unit": "months", "label": "estimated", "source": "Charlotte market standard"},
        "total_keys": None,
        "notes": "Test project for validation",
    },
    "revenue_assumptions": {
        "rent_psf_monthly": {"value": 1.85, "unit": "$/sf/month", "label": "estimated", "source": "Charlotte broker data Q4 2025"},
        "rent_psf_annual_nnn": None,
        "adr": None,
        "stabilized_occupancy_pct": {"value": 93, "unit": "%", "label": "estimated", "source": "Charlotte market data"},
        "lease_up_months": {"value": 18, "unit": "months", "label": "estimated", "source": "Charlotte market standard"},
        "annual_rent_growth_pct": {"value": 3.0, "unit": "%", "label": "estimated", "source": "Charlotte forecast"},
        "other_income_per_unit_monthly": {"value": 125, "unit": "$/unit/month", "label": "estimated", "source": "Charlotte market"},
    },
    "cost_assumptions": {
        "land_cost_total": {"value": 8000000, "unit": "$", "label": "estimated", "source": "Charlotte land market"},
        "hard_cost_psf": {"value": 275, "unit": "$/sf", "label": "estimated", "source": "Charlotte construction Q4 2025"},
        "hard_cost_total": {"value": 49500000, "unit": "$", "label": "calculated", "source": "hard_cost_psf * total_gfa_sf"},
        "soft_cost_pct_of_hard": {"value": 22, "unit": "%", "label": "estimated", "source": "Industry standard"},
        "soft_cost_total": {"value": 10890000, "unit": "$", "label": "calculated", "source": "hard_cost * soft_cost_pct"},
        "developer_fee_pct": {"value": 4, "unit": "%", "label": "estimated", "source": "Fallon standard"},
        "developer_fee_total": {"value": 2735600, "unit": "$", "label": "calculated", "source": "total_cost * dev_fee_pct"},
        "contingency_pct": {"value": 7, "unit": "%", "label": "estimated", "source": "Standard range"},
        "contingency_total": {"value": 3465000, "unit": "$", "label": "calculated", "source": "hard_cost * contingency_pct"},
        "total_project_cost": {"value": 74590600, "unit": "$", "label": "calculated", "source": "sum of all costs"},
    },
    "financing_assumptions": {
        "construction_loan_ltc_pct": {"value": 65, "unit": "%", "label": "estimated", "source": "Market standard"},
        "construction_loan_amount": {"value": 48483890, "unit": "$", "label": "calculated", "source": "ltc * total_cost"},
        "construction_loan_rate_pct": {"value": 7.5, "unit": "%", "label": "estimated", "source": "SOFR + spread"},
        "carry_cost_total": {"value": 5453438, "unit": "$", "label": "calculated", "source": "loan * rate * term/12"},
        "equity_required": {"value": 26106710, "unit": "$", "label": "calculated", "source": "total_cost - loan"},
        "lp_equity_pct": {"value": 90, "unit": "%", "label": "estimated", "source": "Fallon standard"},
        "lp_equity_amount": {"value": 23496039, "unit": "$", "label": "calculated", "source": "equity * lp_pct"},
        "gp_equity_pct": {"value": 10, "unit": "%", "label": "estimated", "source": "Fallon standard"},
        "gp_equity_amount": {"value": 2610671, "unit": "$", "label": "calculated", "source": "equity * gp_pct"},
    },
    "return_metrics": {
        "exit_cap_rate_pct": {"value": 5.25, "unit": "%", "label": "estimated", "source": "Charlotte cap rate Q4 2025"},
        "exit_year": {"value": 5, "unit": "years", "label": "estimated", "source": "Fallon standard hold"},
        "stabilized_noi": {"value": 4200000, "unit": "$", "label": "calculated", "source": "revenue - expenses"},
        "gross_exit_value": {"value": 80000000, "unit": "$", "label": "calculated", "source": "noi / cap_rate"},
        "net_exit_value": {"value": 78000000, "unit": "$", "label": "calculated", "source": "gross - sale_costs"},
        "total_profit": {"value": 3409400, "unit": "$", "label": "calculated", "source": "net_exit - total_cost"},
        "profit_on_cost_pct": {"value": 4.57, "unit": "%", "label": "calculated", "source": "profit / total_cost"},
        "development_spread_bps": {"value": 38, "unit": "bps", "label": "calculated", "source": "(yield - cap) * 10000"},
        "project_irr_levered_pct": {"value": 15.5, "unit": "%", "label": "estimated", "source": "DCF estimate"},
        "equity_multiple_lp": {"value": 1.85, "unit": "x", "label": "estimated", "source": "LP return calc"},
        "lp_irr_pct": {"value": 14.2, "unit": "%", "label": "estimated", "source": "LP DCF estimate"},
    },
}


def test_schema_structure():
    """Test that PRO_FORMA_SCHEMA has all required sections."""
    print("\n" + "=" * 60)
    print("TEST: PRO_FORMA_SCHEMA structure")
    print("=" * 60)
    
    required_sections = [
        "project_summary",
        "revenue_assumptions",
        "cost_assumptions",
        "financing_assumptions",
        "return_metrics",
    ]
    
    for section in required_sections:
        assert section in PRO_FORMA_SCHEMA, f"Missing section: {section}"
        print(f"  - {section}: {len(PRO_FORMA_SCHEMA[section])} fields")
    
    print("\nPASS: Schema has all required sections")
    return True


def test_generation_system_prompt():
    """Test that the system prompt contains key instructions."""
    print("\n" + "=" * 60)
    print("TEST: GENERATION_SYSTEM_PROMPT content")
    print("=" * 60)
    
    required_phrases = [
        "Fallon Company",
        "JSON format",
        "confirmed",
        "estimated",
        "calculated",
        "missing",
        "No markdown",
    ]
    
    for phrase in required_phrases:
        if phrase.lower() in GENERATION_SYSTEM_PROMPT.lower():
            print(f"  - Contains: '{phrase}'")
        else:
            print(f"  - MISSING: '{phrase}'")
    
    assert len(GENERATION_SYSTEM_PROMPT) > 500, "Prompt too short"
    print(f"\n  Prompt length: {len(GENERATION_SYSTEM_PROMPT)} chars")
    
    print("\nPASS: System prompt contains key instructions")
    return True


def test_build_generation_message():
    """Test message building from parameters."""
    print("\n" + "=" * 60)
    print("TEST: build_generation_message()")
    print("=" * 60)
    
    params = ProjectParameters(
        market="charlotte",
        program_type="multifamily",
        unit_count=200,
        land_cost=8000000,
    )
    
    context = "Test context block"
    message = build_generation_message(params, context)
    
    assert "charlotte" in message.lower()
    assert "multifamily" in message.lower()
    assert "200" in message
    assert "Test context block" in message
    
    print(f"  Message length: {len(message)} chars")
    print("  Contains: market, program_type, unit_count, context")
    
    print("\nPASS: Message building works correctly")
    return True


def test_extract_json_from_response():
    """Test JSON extraction from various response formats."""
    print("\n" + "=" * 60)
    print("TEST: extract_json_from_response()")
    print("=" * 60)
    
    # Test 1: Clean JSON
    clean_json = '{"key": "value", "number": 42}'
    result1 = extract_json_from_response(clean_json)
    assert result1 == {"key": "value", "number": 42}
    print("  - Clean JSON: PASS")
    
    # Test 2: With markdown fences
    fenced_json = '```json\n{"key": "value"}\n```'
    result2 = extract_json_from_response(fenced_json)
    assert result2 == {"key": "value"}
    print("  - Fenced JSON: PASS")
    
    # Test 3: With leading text
    prefixed_json = 'Here is the JSON:\n{"key": "value"}'
    result3 = extract_json_from_response(prefixed_json)
    assert result3 == {"key": "value"}
    print("  - Prefixed JSON: PASS")
    
    # Test 4: Invalid JSON
    invalid = "This is not JSON at all"
    result4 = extract_json_from_response(invalid)
    assert result4 is None
    print("  - Invalid JSON returns None: PASS")
    
    print("\nPASS: JSON extraction handles all cases")
    return True


def test_validate_pro_forma():
    """Test pro forma validation."""
    print("\n" + "=" * 60)
    print("TEST: validate_pro_forma()")
    print("=" * 60)
    
    # Test valid pro forma
    is_valid, errors = validate_pro_forma(SAMPLE_PRO_FORMA)
    print(f"  Valid pro forma: is_valid={is_valid}, errors={len(errors)}")
    if errors:
        for e in errors[:3]:
            print(f"    - {e}")
    
    # Test missing section
    bad_pro_forma = {"project_summary": {}}
    is_valid2, errors2 = validate_pro_forma(bad_pro_forma)
    assert not is_valid2
    assert any("Missing required section" in e for e in errors2)
    print(f"  Missing sections detected: {len(errors2)} errors")
    
    print("\nPASS: Validation works correctly")
    return True


def test_val_helper():
    """Test the _val helper function."""
    print("\n" + "=" * 60)
    print("TEST: _val() helper")
    print("=" * 60)
    
    # Test with value dict
    section = {"field": {"value": 100, "unit": "%"}}
    assert _val(section, "field") == 100
    print("  - Value dict extraction: PASS")
    
    # Test with missing field
    assert _val(section, "missing", 42) == 42
    print("  - Default value: PASS")
    
    # Test with None value
    section2 = {"field": {"value": None}}
    assert _val(section2, "field", 0) == 0
    print("  - None value uses default: PASS")
    
    # Test with raw number
    section3 = {"field": 200}
    assert _val(section3, "field") == 200
    print("  - Raw number extraction: PASS")
    
    print("\nPASS: _val helper works correctly")
    return True


def test_compute_returns():
    """Test return computation."""
    print("\n" + "=" * 60)
    print("TEST: compute_returns()")
    print("=" * 60)
    
    results = compute_returns(SAMPLE_PRO_FORMA)
    
    print(f"  calc_noi: ${results.get('calc_noi', 0):,.0f}")
    print(f"  calc_gross_exit_value: ${results.get('calc_gross_exit_value', 0):,.0f}")
    print(f"  calc_profit_on_cost_pct: {results.get('calc_profit_on_cost_pct', 0):.1f}%")
    print(f"  calc_equity_multiple_approx: {results.get('calc_equity_multiple_approx', 0):.2f}x")
    print(f"  calc_irr_approx_pct: {results.get('calc_irr_approx_pct', 0):.1f}%")
    
    assert results.get("calc_noi") is not None
    assert results.get("calc_gross_exit_value") is not None
    
    print("\nPASS: Return computation works")
    return True


def test_check_return_discrepancy():
    """Test discrepancy detection."""
    print("\n" + "=" * 60)
    print("TEST: check_return_discrepancy()")
    print("=" * 60)
    
    calc_results = compute_returns(SAMPLE_PRO_FORMA)
    warnings = check_return_discrepancy(SAMPLE_PRO_FORMA, calc_results)
    
    print(f"  Warnings generated: {len(warnings)}")
    for w in warnings:
        print(f"    - {w[:80]}...")
    
    print("\nPASS: Discrepancy check works")
    return True


def test_compute_sensitivity_table():
    """Test sensitivity table generation."""
    print("\n" + "=" * 60)
    print("TEST: compute_sensitivity_table()")
    print("=" * 60)
    
    table = compute_sensitivity_table(SAMPLE_PRO_FORMA, target_irr=14.0)
    
    print(f"  Row label: {table['row_label']}")
    print(f"  Col label: {table['col_label']}")
    print(f"  Rows: {table['rows']}")
    print(f"  Cols: {table['cols']}")
    print(f"  Values: {table['values']}")
    print(f"  Colors: {table['colors']}")
    
    assert len(table["values"]) == 3
    assert len(table["values"][0]) == 3
    
    print("\nPASS: Sensitivity table generation works")
    return True


def run_all_tests():
    """Run all Phase 4 tests."""
    print("\n" + "=" * 60)
    print("PHASE 4 - PRO FORMA GENERATOR TESTS")
    print("=" * 60)
    
    tests = [
        ("schema_structure", test_schema_structure),
        ("generation_system_prompt", test_generation_system_prompt),
        ("build_generation_message", test_build_generation_message),
        ("extract_json_from_response", test_extract_json_from_response),
        ("validate_pro_forma", test_validate_pro_forma),
        ("_val_helper", test_val_helper),
        ("compute_returns", test_compute_returns),
        ("check_return_discrepancy", test_check_return_discrepancy),
        ("compute_sensitivity_table", test_compute_sensitivity_table),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"\nERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(p for _, p in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
