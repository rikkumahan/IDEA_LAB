"""
Test Suite for Validation Module

This test suite validates:
1. Problem validity classification
2. Leverage presence classification
3. Validation class classification
4. Complete validation workflow
5. Market data context (does NOT invalidate problems)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validation import (
    classify_problem_validity,
    classify_leverage_presence,
    classify_validation_class,
    validate_idea,
    interpret_validation_context
)


def test_problem_validity_classification():
    """Test problem validity classification."""
    print("=" * 70)
    print("TEST: Problem Validity Classification")
    print("=" * 70)
    
    # Test case 1: DRASTIC problem → REAL
    print("\n1. Problem level: DRASTIC → REAL")
    result = classify_problem_validity("DRASTIC")
    assert result == "REAL", f"Expected REAL, got {result}"
    print("   ✓ DRASTIC correctly classified as REAL")
    
    # Test case 2: SEVERE problem → REAL
    print("\n2. Problem level: SEVERE → REAL")
    result = classify_problem_validity("SEVERE")
    assert result == "REAL", f"Expected REAL, got {result}"
    print("   ✓ SEVERE correctly classified as REAL")
    
    # Test case 3: MODERATE problem → WEAK
    print("\n3. Problem level: MODERATE → WEAK")
    result = classify_problem_validity("MODERATE")
    assert result == "WEAK", f"Expected WEAK, got {result}"
    print("   ✓ MODERATE correctly classified as WEAK")
    
    # Test case 4: LOW problem → WEAK
    print("\n4. Problem level: LOW → WEAK")
    result = classify_problem_validity("LOW")
    assert result == "WEAK", f"Expected WEAK, got {result}"
    print("   ✓ LOW correctly classified as WEAK")
    
    print("\n✓ Problem validity classification tests passed")


def test_leverage_presence_classification():
    """Test leverage presence classification."""
    print("\n" + "=" * 70)
    print("TEST: Leverage Presence Classification")
    print("=" * 70)
    
    # Test case 1: Has leverage flags → PRESENT
    print("\n1. Leverage flags: ['COST_LEVERAGE', 'TIME_LEVERAGE'] → PRESENT")
    result = classify_leverage_presence(["COST_LEVERAGE", "TIME_LEVERAGE"])
    assert result == "PRESENT", f"Expected PRESENT, got {result}"
    print("   ✓ Leverage correctly classified as PRESENT")
    
    # Test case 2: No leverage flags → NONE
    print("\n2. Leverage flags: [] → NONE")
    result = classify_leverage_presence([])
    assert result == "NONE", f"Expected NONE, got {result}"
    print("   ✓ No leverage correctly classified as NONE")
    
    # Test case 3: Single leverage flag → PRESENT
    print("\n3. Leverage flags: ['ACCESS_LEVERAGE'] → PRESENT")
    result = classify_leverage_presence(["ACCESS_LEVERAGE"])
    assert result == "PRESENT", f"Expected PRESENT, got {result}"
    print("   ✓ Single leverage flag correctly classified as PRESENT")
    
    print("\n✓ Leverage presence classification tests passed")


def test_validation_class_classification():
    """Test validation class classification."""
    print("\n" + "=" * 70)
    print("TEST: Validation Class Classification")
    print("=" * 70)
    
    # Test case 1: REAL problem + PRESENT leverage → STRONG_FOUNDATION
    print("\n1. REAL problem + PRESENT leverage → STRONG_FOUNDATION")
    result = classify_validation_class("REAL", "PRESENT")
    assert result == "STRONG_FOUNDATION", f"Expected STRONG_FOUNDATION, got {result}"
    print("   ✓ Correctly classified as STRONG_FOUNDATION")
    
    # Test case 2: REAL problem + NONE leverage → REAL_PROBLEM_WEAK_EDGE
    print("\n2. REAL problem + NONE leverage → REAL_PROBLEM_WEAK_EDGE")
    result = classify_validation_class("REAL", "NONE")
    assert result == "REAL_PROBLEM_WEAK_EDGE", f"Expected REAL_PROBLEM_WEAK_EDGE, got {result}"
    print("   ✓ Correctly classified as REAL_PROBLEM_WEAK_EDGE")
    
    # Test case 3: WEAK problem + PRESENT leverage → WEAK_FOUNDATION
    print("\n3. WEAK problem + PRESENT leverage → WEAK_FOUNDATION")
    result = classify_validation_class("WEAK", "PRESENT")
    assert result == "WEAK_FOUNDATION", f"Expected WEAK_FOUNDATION, got {result}"
    print("   ✓ Correctly classified as WEAK_FOUNDATION")
    
    # Test case 4: WEAK problem + NONE leverage → WEAK_FOUNDATION
    print("\n4. WEAK problem + NONE leverage → WEAK_FOUNDATION")
    result = classify_validation_class("WEAK", "NONE")
    assert result == "WEAK_FOUNDATION", f"Expected WEAK_FOUNDATION, got {result}"
    print("   ✓ Correctly classified as WEAK_FOUNDATION")
    
    print("\n✓ Validation class classification tests passed")


def test_complete_validation_workflow():
    """Test complete validation workflow with all stages."""
    print("\n" + "=" * 70)
    print("TEST: Complete Validation Workflow")
    print("=" * 70)
    
    # Test case 1: STRONG_FOUNDATION scenario
    print("\n1. STRONG_FOUNDATION scenario (SEVERE problem + leverage)")
    result = validate_idea(
        problem_level="SEVERE",
        problem_signals={
            "complaint_count": 10,
            "workaround_count": 8,
            "intensity_count": 5
        },
        market_strength={
            "competitor_density": "MEDIUM",
            "substitute_pressure": "HIGH",
            "content_saturation": "HIGH",
            "automation_relevance": "HIGH"
        },
        leverage_flags=["COST_LEVERAGE", "TIME_LEVERAGE"],
        leverage_details={
            "COST_LEVERAGE": {"triggered": True},
            "TIME_LEVERAGE": {"triggered": True}
        }
    )
    
    validation_state = result["validation_state"]
    assert validation_state["problem_validity"] == "REAL"
    assert validation_state["leverage_presence"] == "PRESENT"
    assert validation_state["validation_class"] == "STRONG_FOUNDATION"
    print("   ✓ Correctly validated as STRONG_FOUNDATION")
    print(f"   Problem Reality: {result['problem_reality']['problem_level']}")
    print(f"   Leverage Flags: {result['leverage_reality']['leverage_flags']}")
    
    # Test case 2: REAL_PROBLEM_WEAK_EDGE scenario
    print("\n2. REAL_PROBLEM_WEAK_EDGE scenario (SEVERE problem + no leverage)")
    result = validate_idea(
        problem_level="SEVERE",
        problem_signals={
            "complaint_count": 12,
            "workaround_count": 6,
            "intensity_count": 3
        },
        market_strength={
            "competitor_density": "HIGH",
            "substitute_pressure": "HIGH",
            "content_saturation": "MEDIUM",
            "automation_relevance": "LOW"
        },
        leverage_flags=[],
        leverage_details={}
    )
    
    validation_state = result["validation_state"]
    assert validation_state["problem_validity"] == "REAL"
    assert validation_state["leverage_presence"] == "NONE"
    assert validation_state["validation_class"] == "REAL_PROBLEM_WEAK_EDGE"
    print("   ✓ Correctly validated as REAL_PROBLEM_WEAK_EDGE")
    
    # Test case 3: WEAK_FOUNDATION scenario
    print("\n3. WEAK_FOUNDATION scenario (MODERATE problem)")
    result = validate_idea(
        problem_level="MODERATE",
        problem_signals={
            "complaint_count": 3,
            "workaround_count": 2,
            "intensity_count": 0
        },
        market_strength={
            "competitor_density": "LOW",
            "substitute_pressure": "LOW",
            "content_saturation": "LOW",
            "automation_relevance": "MEDIUM"
        },
        leverage_flags=["ACCESS_LEVERAGE"],
        leverage_details={"ACCESS_LEVERAGE": {"triggered": True}}
    )
    
    validation_state = result["validation_state"]
    assert validation_state["problem_validity"] == "WEAK"
    assert validation_state["leverage_presence"] == "PRESENT"
    assert validation_state["validation_class"] == "WEAK_FOUNDATION"
    print("   ✓ Correctly validated as WEAK_FOUNDATION")
    print("   (Note: Leverage present but problem too weak)")
    
    print("\n✓ Complete validation workflow tests passed")


def test_market_context_interpretation():
    """Test that market data provides context but doesn't invalidate problems."""
    print("\n" + "=" * 70)
    print("TEST: Market Context (Does NOT Invalidate Problems)")
    print("=" * 70)
    
    # Test case: REAL problem with HIGH competition + no leverage
    # Should be REAL_PROBLEM_WEAK_EDGE, NOT WEAK_FOUNDATION
    print("\n1. SEVERE problem + HIGH competition + NO leverage")
    result = validate_idea(
        problem_level="SEVERE",
        problem_signals={
            "complaint_count": 15,
            "workaround_count": 10,
            "intensity_count": 7
        },
        market_strength={
            "competitor_density": "HIGH",  # High competition
            "substitute_pressure": "HIGH",
            "content_saturation": "HIGH",
            "automation_relevance": "MEDIUM"
        },
        leverage_flags=[],  # No leverage
        leverage_details={}
    )
    
    validation_state = result["validation_state"]
    
    # Problem should still be REAL despite high competition
    assert validation_state["problem_validity"] == "REAL", \
        "Problem should be REAL despite high competition"
    
    # Classification should be REAL_PROBLEM_WEAK_EDGE, not WEAK_FOUNDATION
    assert validation_state["validation_class"] == "REAL_PROBLEM_WEAK_EDGE", \
        "Should be REAL_PROBLEM_WEAK_EDGE (real problem, needs leverage)"
    
    print("   ✓ Problem remained REAL despite HIGH competition")
    print("   ✓ Classification: REAL_PROBLEM_WEAK_EDGE (not WEAK_FOUNDATION)")
    print("   Market competition is CONTEXT, not a problem invalidator")
    
    # Test interpretation context
    context = interpret_validation_context(
        validation_state["validation_class"],
        result["market_reality"]["market_strength"]
    )
    print(f"\n   Context interpretation: {context['interpretation']}")
    
    print("\n✓ Market context interpretation tests passed")


def test_validation_invariants():
    """Test validation invariants (rules that must always hold)."""
    print("\n" + "=" * 70)
    print("TEST: Validation Invariants")
    print("=" * 70)
    
    # Invariant 1: WEAK problem always → WEAK_FOUNDATION (regardless of leverage)
    print("\n1. WEAK problem + leverage → must be WEAK_FOUNDATION")
    result = classify_validation_class("WEAK", "PRESENT")
    assert result == "WEAK_FOUNDATION", "WEAK problem always → WEAK_FOUNDATION"
    print("   ✓ Invariant holds: WEAK problem → WEAK_FOUNDATION")
    
    # Invariant 2: REAL problem + leverage → must be STRONG_FOUNDATION
    print("\n2. REAL problem + leverage → must be STRONG_FOUNDATION")
    result = classify_validation_class("REAL", "PRESENT")
    assert result == "STRONG_FOUNDATION", "REAL + leverage → STRONG_FOUNDATION"
    print("   ✓ Invariant holds: REAL + leverage → STRONG_FOUNDATION")
    
    # Invariant 3: REAL problem + no leverage → must be REAL_PROBLEM_WEAK_EDGE
    print("\n3. REAL problem + no leverage → must be REAL_PROBLEM_WEAK_EDGE")
    result = classify_validation_class("REAL", "NONE")
    assert result == "REAL_PROBLEM_WEAK_EDGE", "REAL + no leverage → REAL_PROBLEM_WEAK_EDGE"
    print("   ✓ Invariant holds: REAL + no leverage → REAL_PROBLEM_WEAK_EDGE")
    
    print("\n✓ Validation invariants tests passed")


def run_all_tests():
    """Run all validation test suites."""
    print("\n" + "=" * 70)
    print("VALIDATION MODULE: COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    try:
        test_problem_validity_classification()
        test_leverage_presence_classification()
        test_validation_class_classification()
        test_complete_validation_workflow()
        test_market_context_interpretation()
        test_validation_invariants()
        
        print("\n" + "=" * 70)
        print("✓ ALL VALIDATION TESTS PASSED")
        print("=" * 70)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
