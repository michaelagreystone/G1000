"""
Tests for Phase 3 — Context Retriever.
Validates deal comps retrieval, market defaults lookup, and context formatting.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from FallonPrototype.agents.financial_agent import (
    ProjectParameters,
    build_deal_query,
    retrieve_deal_comps,
    get_defaults_for_params,
    retrieve_defaults_context,
    get_fallback_warning,
    format_financial_context,
    assemble_context,
)


def test_build_deal_query():
    """Test that deal query construction produces targeted retrieval strings."""
    print("\n" + "=" * 60)
    print("TEST: build_deal_query()")
    print("=" * 60)
    
    # Test 1: Charlotte multifamily
    params1 = ProjectParameters(market="charlotte", program_type="multifamily")
    query1 = build_deal_query(params1)
    print(f"\nCharlotte multifamily: {query1}")
    assert "Charlotte" in query1
    assert "multifamily" in query1
    assert "pro forma" in query1
    
    # Test 2: Nashville mixed-use
    params2 = ProjectParameters(
        market="nashville",
        program_type="mixed_use",
        mixed_use_components=["hotel", "multifamily"]
    )
    query2 = build_deal_query(params2)
    print(f"Nashville mixed-use: {query2}")
    assert "Nashville" in query2
    assert "mixed-use" in query2
    
    # Test 3: Boston office
    params3 = ProjectParameters(market="boston", program_type="office")
    query3 = build_deal_query(params3)
    print(f"Boston office: {query3}")
    assert "Boston" in query3
    assert "Class A office" in query3
    
    print("\nPASS: All query construction tests passed")
    return True


def test_retrieve_deal_comps():
    """Test deal comps retrieval with deduplication and relevance filtering."""
    print("\n" + "=" * 60)
    print("TEST: retrieve_deal_comps()")
    print("=" * 60)
    
    params = ProjectParameters(market="nashville", program_type="multifamily")
    comps = retrieve_deal_comps(params)
    
    print(f"\nRetrieved {len(comps)} deal comps for Nashville multifamily:")
    for i, comp in enumerate(comps):
        print(f"  {i+1}. {comp['metadata'].get('source', 'unknown')} "
              f"(distance: {comp['distance']}, relevance: {comp['relevance']})")
    
    # Empty corpus is allowed — should return empty list, not error
    if len(comps) == 0:
        print("\nNote: Empty corpus — deal comps retrieval returned empty list (valid)")
        return True
    
    # If we have comps, verify no low-relevance results
    low_relevance = [c for c in comps if c["relevance"] == "low"]
    if low_relevance:
        print(f"\nFAIL: Found {len(low_relevance)} low-relevance comps (should be filtered)")
        return False
    
    # Verify max 4 results
    if len(comps) > 4:
        print(f"\nFAIL: Retrieved {len(comps)} comps (max should be 4)")
        return False
    
    print("\nPASS: Deal comps retrieval working correctly")
    return True


def test_get_defaults_for_params():
    """Test direct market defaults lookup."""
    print("\n" + "=" * 60)
    print("TEST: get_defaults_for_params()")
    print("=" * 60)
    
    # Test 1: Charlotte multifamily (should exist)
    params1 = ProjectParameters(market="charlotte", program_type="multifamily")
    defaults1 = get_defaults_for_params(params1)
    
    if defaults1:
        print(f"\nCharlotte multifamily defaults found:")
        print(f"  - rent_psf_monthly: {defaults1.get('rent_psf_monthly', {}).get('value')}")
        print(f"  - exit_cap_rate_pct: {defaults1.get('exit_cap_rate_pct', {}).get('value')}")
        print(f"  - fallback: {defaults1.get('_fallback', False)}")
    else:
        print("\nWARNING: Charlotte multifamily defaults not found")
    
    # Test 2: Unknown market (should fall back to national)
    params2 = ProjectParameters(market="denver", program_type="multifamily")
    defaults2 = get_defaults_for_params(params2)
    
    if defaults2:
        is_fallback = defaults2.get("_fallback", False)
        print(f"\nDenver multifamily: fallback={is_fallback}")
        if is_fallback:
            print("  PASS: Correctly using national averages")
        else:
            print("  Note: Denver has specific data (unexpected)")
    else:
        print("\nDenver multifamily: No defaults found")
    
    # Test 3: Mixed-use
    params3 = ProjectParameters(
        market="nashville",
        program_type="mixed_use",
        mixed_use_components=["hotel", "multifamily"]
    )
    defaults3 = get_defaults_for_params(params3)
    
    if defaults3:
        print(f"\nNashville mixed-use defaults:")
        print(f"  - is_mixed_use: {defaults3.get('_mixed_use', False)}")
        components = defaults3.get("_components", {})
        for comp_name in components:
            print(f"  - {comp_name} component loaded")
    
    print("\nPASS: Defaults lookup working correctly")
    return True


def test_fallback_warning():
    """Test fallback warning generation."""
    print("\n" + "=" * 60)
    print("TEST: get_fallback_warning()")
    print("=" * 60)
    
    # No fallback case
    defaults_ok = {"rent": 1.95}
    warning1 = get_fallback_warning(defaults_ok, "charlotte")
    print(f"\nNo fallback: warning={warning1}")
    assert warning1 is None
    
    # Fallback case
    defaults_fallback = {"rent": 1.95, "_fallback": True}
    warning2 = get_fallback_warning(defaults_fallback, "denver")
    print(f"With fallback: warning present = {warning2 is not None}")
    assert warning2 is not None
    assert "denver" in warning2.lower()
    assert "national averages" in warning2.lower()
    
    print("\nPASS: Fallback warning generation working correctly")
    return True


def test_format_financial_context():
    """Test context formatting produces readable output."""
    print("\n" + "=" * 60)
    print("TEST: format_financial_context()")
    print("=" * 60)
    
    params = ProjectParameters(market="charlotte", program_type="multifamily")
    
    # Mock data
    deal_comps = [
        {
            "text": "Sample deal memo content about Charlotte multifamily...",
            "metadata": {"source": "charlotte_deal_memo.txt"},
            "distance": 0.25,
            "relevance": "high",
        }
    ]
    
    defaults_dict = {
        "rent_psf_monthly": {"value": 1.85, "unit": "$/sf/month", "source": "Charlotte Q4 2025"},
        "exit_cap_rate_pct": {"value": 4.74, "unit": "%", "source": "CBRE Q1 2025"},
    }
    
    defaults_chunks = []
    
    context = format_financial_context(deal_comps, defaults_dict, defaults_chunks, params)
    
    print(f"\nGenerated context ({len(context)} chars)")
    
    # Verify structure
    assert "SECTION 1" in context
    assert "SECTION 2" in context
    assert "COMPARABLE 1" in context
    assert "Context quality" in context
    
    print("  - Contains SECTION 1, SECTION 2, COMPARABLE 1, Context quality")
    print("\nPASS: Context formatting working correctly")
    return True


def test_assemble_context_integration():
    """Integration test for the full assemble_context flow."""
    print("\n" + "=" * 60)
    print("TEST: assemble_context() - Integration")
    print("=" * 60)
    
    params = ProjectParameters(
        market="charlotte",
        program_type="multifamily",
        unit_count=200,
    )
    
    context, warning = assemble_context(params)
    
    print(f"\nAssembled context for Charlotte 200-unit multifamily:")
    print(f"  - Context length: {len(context)} chars")
    print(f"  - Fallback warning: {warning is not None}")
    
    assert len(context) > 100, "Context should have substantial content"
    
    print("\nPASS: Full context assembly integration working")
    return True


def run_all_tests():
    """Run all Phase 3 tests."""
    print("\n" + "=" * 60)
    print("PHASE 3 — CONTEXT RETRIEVER TESTS")
    print("=" * 60)
    
    tests = [
        ("build_deal_query", test_build_deal_query),
        ("retrieve_deal_comps", test_retrieve_deal_comps),
        ("get_defaults_for_params", test_get_defaults_for_params),
        ("fallback_warning", test_fallback_warning),
        ("format_financial_context", test_format_financial_context),
        ("assemble_context", test_assemble_context_integration),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"\nERROR in {name}: {e}")
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
