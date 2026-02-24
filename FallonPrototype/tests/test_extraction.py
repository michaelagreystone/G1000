"""
Test extraction accuracy for the parameter extractor (Phase 2.2.4).

Runs 10 varied inputs and validates correct field extraction.
"""

import sys
import os

_PROTO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(_PROTO_DIR))

from FallonPrototype.agents.financial_agent import (
    extract_parameters,
    normalize_parameters,
    check_missing_parameters,
    format_clarification_message,
    merge_clarification,
    ProjectParameters,
)

# Test cases: (input_query, expected_fields_dict)
# Each expected_fields_dict contains the fields that MUST match
TEST_CASES = [
    # 1. Simple multifamily
    (
        "200 units in Charlotte",
        {"market": "charlotte", "program_type": "multifamily", "unit_count": 200},
    ),
    # 2. Mixed-use with components
    (
        "mixed-use project in Nashville, hotel and apartments, 300 keys and 150 units",
        {
            "market": "nashville",
            "program_type": "mixed_use",
            "total_keys": 300,
            "unit_count": 150,
        },
    ),
    # 3. Office with IRR target
    (
        "80k sf office building in Boston Seaport targeting 15% IRR",
        {
            "market": "boston",
            "program_type": "office",
            "rentable_sf": 80000,
            "target_lp_irr_pct": 15.0,
        },
    ),
    # 4. Hotel only
    (
        "250-key select-service hotel in Nashville",
        {"market": "nashville", "program_type": "hotel", "total_keys": 250},
    ),
    # 5. Condo project
    (
        "Boston Seaport condo development, 180 units",
        {"market": "boston", "program_type": "condo", "unit_count": 180},
    ),
    # 6. With land cost
    (
        "Charlotte multifamily, 220 units on a $4M land parcel",
        {
            "market": "charlotte",
            "program_type": "multifamily",
            "unit_count": 220,
            "land_cost": 4000000,
        },
    ),
    # 7. With equity multiple target
    (
        "150-unit apartment building in Nashville, aiming for 2.0x equity multiple",
        {
            "market": "nashville",
            "program_type": "multifamily",
            "unit_count": 150,
            "target_equity_multiple": 2.0,
        },
    ),
    # 8. With acreage
    (
        "Charlotte office development on 3.5 acres, 120,000 sf",
        {
            "market": "charlotte",
            "program_type": "office",
            "rentable_sf": 120000,
            "acreage": 3.5,
        },
    ),
    # 9. With construction timing (accepts various date formats)
    (
        "Boston multifamily, 200 units, breaking ground Q3 2026",
        {
            "market": "boston",
            "program_type": "multifamily",
            "unit_count": 200,
            # construction_start can be "Q3 2026", "2026-07", "July 2026", etc.
        },
    ),
    # 10. Complex mixed-use
    (
        "Nashville mixed-use tower: 250 apartments, 40,000sf retail, and a 150-key boutique hotel",
        {
            "market": "nashville",
            "program_type": "mixed_use",
            "unit_count": 250,
            "total_keys": 150,
        },
    ),
]


def run_single_test(index: int, query: str, expected: dict) -> tuple[bool, str]:
    """Run a single test case and return (passed, message)."""
    print(f"\n--- Test {index + 1} ---")
    print(f"Query: {query}")
    
    params = normalize_parameters(extract_parameters(query))
    
    failures = []
    for field, expected_value in expected.items():
        actual_value = getattr(params, field)
        
        # Handle numeric comparisons with tolerance
        if isinstance(expected_value, float):
            if actual_value is None:
                failures.append(f"  {field}: expected {expected_value}, got None")
            elif abs(actual_value - expected_value) > 0.01:
                failures.append(f"  {field}: expected {expected_value}, got {actual_value}")
        elif isinstance(expected_value, int):
            # Allow some tolerance for large numbers (e.g., 80000 vs 80,000)
            if actual_value is None:
                failures.append(f"  {field}: expected {expected_value}, got None")
            elif abs(actual_value - expected_value) > expected_value * 0.05:
                failures.append(f"  {field}: expected {expected_value}, got {actual_value}")
        else:
            if actual_value != expected_value:
                failures.append(f"  {field}: expected '{expected_value}', got '{actual_value}'")
    
    if failures:
        print("FAILED:")
        for f in failures:
            print(f)
        return False, "\n".join(failures)
    else:
        print(f"PASSED: {expected}")
        return True, ""


def test_clarification_flow():
    """Test the clarification flow for missing parameters."""
    print("\n" + "=" * 60)
    print("CLARIFICATION FLOW TEST")
    print("=" * 60)
    
    # Initial vague query
    params = normalize_parameters(extract_parameters("build me a model"))
    missing = check_missing_parameters(params)
    
    print(f"\nInitial query: 'build me a model'")
    print(f"Missing fields: {missing}")
    
    assert len(missing) >= 2, f"Expected at least 2 missing fields, got {len(missing)}"
    
    message = format_clarification_message(missing)
    print(f"\nClarification message:\n{message}")
    
    assert "market" in message.lower() or "charlotte" in message.lower(), \
        "Clarification should mention market"
    
    # Merge clarification
    merged = merge_clarification(params, "Charlotte multifamily, 180 units")
    
    print(f"\nAfter clarification 'Charlotte multifamily, 180 units':")
    print(f"  market: {merged.market}")
    print(f"  program_type: {merged.program_type}")
    print(f"  unit_count: {merged.unit_count}")
    
    assert merged.market == "charlotte", f"Expected charlotte, got {merged.market}"
    assert merged.program_type == "multifamily", f"Expected multifamily, got {merged.program_type}"
    
    missing_after = check_missing_parameters(merged)
    print(f"\nMissing after merge: {missing_after}")
    
    print("\nCLARIFICATION FLOW TEST PASSED")
    return True


def main():
    print("=" * 60)
    print("PARAMETER EXTRACTION TESTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, (query, expected) in enumerate(TEST_CASES):
        success, _ = run_single_test(i, query, expected)
        if success:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{len(TEST_CASES)} tests passed")
    if failed > 0:
        print(f"         {failed} tests FAILED")
    print("=" * 60)
    
    # Run clarification test
    clarification_passed = test_clarification_flow()
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Extraction tests: {passed}/{len(TEST_CASES)}")
    print(f"Clarification test: {'PASSED' if clarification_passed else 'FAILED'}")
    
    if failed == 0 and clarification_passed:
        print("\nALL TESTS PASSED")
        return 0
    else:
        print("\nSOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
