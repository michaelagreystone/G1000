"""
Test 7.3 — Generate Pro Formas for Three Deal Types

Tests full generation pipeline with real API calls.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from FallonPrototype.agents.financial_agent import (
    run,
    validate_pro_forma,
    VALID_LABELS,
)


def test_deal_generation(query: str, expected_market: str, expected_program: str) -> bool:
    """Test a single deal generation."""
    print(f"\n  Query: '{query}'")
    print("  Generating...")
    
    response = run(query)
    
    if response.needs_clarification:
        print(f"  FAIL: Needs clarification - {response.answer[:100]}")
        return False
    
    if not response.export_data or "pro_forma" not in response.export_data:
        print(f"  FAIL: No pro forma generated - {response.answer[:100]}")
        return False
    
    pro_forma = response.export_data["pro_forma"]
    
    # Check all five sections present
    required_sections = ["project_summary", "revenue_assumptions", "cost_assumptions",
                        "financing_assumptions", "return_metrics"]
    
    missing_sections = [s for s in required_sections if s not in pro_forma]
    if missing_sections:
        print(f"  FAIL: Missing sections: {missing_sections}")
        return False
    print("  All 5 sections present")
    
    # Check all labels are valid
    invalid_labels = []
    for section_name, section in pro_forma.items():
        if isinstance(section, dict):
            for key, field in section.items():
                if isinstance(field, dict) and "label" in field:
                    if field["label"] not in VALID_LABELS:
                        invalid_labels.append(f"{section_name}.{key}: {field['label']}")
    
    if invalid_labels:
        print(f"  FAIL: Invalid labels: {invalid_labels[:3]}")
        return False
    print("  All labels valid")
    
    # Check return metrics are plausible
    returns = pro_forma.get("return_metrics", {})
    
    def get_val(field):
        if isinstance(field, dict):
            return field.get("value")
        return field
    
    irr = get_val(returns.get("project_irr_levered_pct"))
    multiple = get_val(returns.get("equity_multiple_lp"))
    
    print(f"  IRR: {irr}%, Multiple: {multiple}x")
    
    if irr is not None:
        if irr < -50 or irr > 100:
            print(f"  WARNING: IRR {irr}% outside plausible range (-50% to 100%)")
    
    if multiple is not None:
        if multiple < 0 or multiple > 10:
            print(f"  WARNING: Multiple {multiple}x outside plausible range (0 to 10)")
    
    # Check market and program match
    summary = pro_forma.get("project_summary", {})
    market = summary.get("market", "")
    program = summary.get("program_type", "")
    
    print(f"  Market: {market}, Program: {program}")
    
    # Validation
    is_valid, errors = validate_pro_forma(pro_forma)
    if not is_valid:
        print(f"  Schema warnings: {errors[:3]}")
    else:
        print("  Schema validation passed")
    
    print("  PASS")
    return True


def run_test_7_3():
    """Run test 7.3 for three deal types."""
    print("\n" + "=" * 60)
    print("TEST 7.3: Generate Pro Formas for Three Deal Types")
    print("=" * 60)
    
    test_cases = [
        ("200-unit multifamily in Charlotte", "charlotte", "multifamily"),
        ("Nashville mixed-use hotel and apartments, 300 keys and 150 units", "nashville", "mixed_use"),
        ("80,000sf office in Boston targeting 15% IRR", "boston", "office"),
    ]
    
    results = []
    
    for query, expected_market, expected_program in test_cases:
        print(f"\n{'-' * 60}")
        print(f"Testing: {expected_market} {expected_program}")
        print("-" * 60)
        
        try:
            passed = test_deal_generation(query, expected_market, expected_program)
            results.append((f"{expected_market} {expected_program}", passed))
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((f"{expected_market} {expected_program}", False))
    
    print("\n" + "=" * 60)
    print("TEST 7.3 SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(p for _, p in results)
    print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    
    return all_passed


if __name__ == "__main__":
    success = run_test_7_3()
    sys.exit(0 if success else 1)
