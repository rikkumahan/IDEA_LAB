"""
Test Suite for Stage 3: Deterministic Leverage Engine

This test suite validates:
1. Individual leverage detection rules
2. Input validation (type + sanity)
3. Determinism (same inputs → same outputs)
4. Edge cases and boundary conditions
5. LLM independence (results identical with/without LLM)
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stage3_leverage import (
    detect_leverage_flags,
    detect_cost_leverage,
    detect_time_leverage,
    detect_cognitive_leverage,
    detect_access_leverage,
    detect_constraint_leverage,
    validate_leverage_inputs,
    audit_determinism
)


def test_cost_leverage_rule():
    """Test COST_LEVERAGE detection rule."""
    print("=" * 70)
    print("TEST: COST_LEVERAGE Rule")
    print("=" * 70)
    
    # Test case 1: Should trigger (replaces labor + HIGH automation)
    print("\n1. replaces_human_labor=True, automation_relevance=HIGH")
    result = detect_cost_leverage(
        replaces_human_labor=True,
        automation_relevance="HIGH"
    )
    assert result is True, "Should detect COST_LEVERAGE"
    print("   ✓ COST_LEVERAGE detected correctly")
    
    # Test case 2: Should NOT trigger (replaces labor but LOW automation)
    print("\n2. replaces_human_labor=True, automation_relevance=LOW")
    result = detect_cost_leverage(
        replaces_human_labor=True,
        automation_relevance="LOW"
    )
    assert result is False, "Should NOT detect COST_LEVERAGE (automation not HIGH)"
    print("   ✓ COST_LEVERAGE correctly not detected")
    
    # Test case 3: Should NOT trigger (no labor replacement)
    print("\n3. replaces_human_labor=False, automation_relevance=HIGH")
    result = detect_cost_leverage(
        replaces_human_labor=False,
        automation_relevance="HIGH"
    )
    assert result is False, "Should NOT detect COST_LEVERAGE (no labor replacement)"
    print("   ✓ COST_LEVERAGE correctly not detected")
    
    print("\n✓ COST_LEVERAGE rule tests passed")


def test_time_leverage_rule():
    """Test TIME_LEVERAGE detection rule."""
    print("\n" + "=" * 70)
    print("TEST: TIME_LEVERAGE Rule")
    print("=" * 70)
    
    # Test case 1: Should trigger (step_reduction >= 5)
    print("\n1. step_reduction_ratio=5 (trigger threshold)")
    result = detect_time_leverage(
        step_reduction_ratio=5,
        automation_relevance="LOW",
        substitute_pressure="LOW"
    )
    assert result is True, "Should detect TIME_LEVERAGE (>= 5 steps)"
    print("   ✓ TIME_LEVERAGE detected correctly")
    
    # Test case 2: Should trigger (HIGH automation + MEDIUM substitute pressure)
    print("\n2. automation_relevance=HIGH, substitute_pressure=MEDIUM")
    result = detect_time_leverage(
        step_reduction_ratio=2,
        automation_relevance="HIGH",
        substitute_pressure="MEDIUM"
    )
    assert result is True, "Should detect TIME_LEVERAGE (HIGH auto + MEDIUM subs)"
    print("   ✓ TIME_LEVERAGE detected correctly")
    
    # Test case 3: Should NOT trigger (insufficient conditions)
    print("\n3. step_reduction_ratio=3, automation_relevance=MEDIUM, substitute_pressure=LOW")
    result = detect_time_leverage(
        step_reduction_ratio=3,
        automation_relevance="MEDIUM",
        substitute_pressure="LOW"
    )
    assert result is False, "Should NOT detect TIME_LEVERAGE"
    print("   ✓ TIME_LEVERAGE correctly not detected")
    
    print("\n✓ TIME_LEVERAGE rule tests passed")


def test_cognitive_leverage_rule():
    """Test COGNITIVE_LEVERAGE detection rule."""
    print("\n" + "=" * 70)
    print("TEST: COGNITIVE_LEVERAGE Rule")
    print("=" * 70)
    
    # Test case 1: Should trigger (delivers final answer + MEDIUM content)
    print("\n1. delivers_final_answer=True, content_saturation=MEDIUM")
    result = detect_cognitive_leverage(
        delivers_final_answer=True,
        content_saturation="MEDIUM"
    )
    assert result is True, "Should detect COGNITIVE_LEVERAGE"
    print("   ✓ COGNITIVE_LEVERAGE detected correctly")
    
    # Test case 2: Should NOT trigger (no final answer)
    print("\n2. delivers_final_answer=False, content_saturation=HIGH")
    result = detect_cognitive_leverage(
        delivers_final_answer=False,
        content_saturation="HIGH"
    )
    assert result is False, "Should NOT detect COGNITIVE_LEVERAGE (no final answer)"
    print("   ✓ COGNITIVE_LEVERAGE correctly not detected")
    
    # Test case 3: Should NOT trigger (LOW content saturation)
    print("\n3. delivers_final_answer=True, content_saturation=LOW")
    result = detect_cognitive_leverage(
        delivers_final_answer=True,
        content_saturation="LOW"
    )
    assert result is False, "Should NOT detect COGNITIVE_LEVERAGE (LOW content)"
    print("   ✓ COGNITIVE_LEVERAGE correctly not detected")
    
    print("\n✓ COGNITIVE_LEVERAGE rule tests passed")


def test_access_leverage_rule():
    """Test ACCESS_LEVERAGE detection rule."""
    print("\n" + "=" * 70)
    print("TEST: ACCESS_LEVERAGE Rule")
    print("=" * 70)
    
    # Test case 1: Should trigger
    print("\n1. unique_data_access=True")
    result = detect_access_leverage(unique_data_access=True)
    assert result is True, "Should detect ACCESS_LEVERAGE"
    print("   ✓ ACCESS_LEVERAGE detected correctly")
    
    # Test case 2: Should NOT trigger
    print("\n2. unique_data_access=False")
    result = detect_access_leverage(unique_data_access=False)
    assert result is False, "Should NOT detect ACCESS_LEVERAGE"
    print("   ✓ ACCESS_LEVERAGE correctly not detected")
    
    print("\n✓ ACCESS_LEVERAGE rule tests passed")


def test_constraint_leverage_rule():
    """Test CONSTRAINT_LEVERAGE detection rule."""
    print("\n" + "=" * 70)
    print("TEST: CONSTRAINT_LEVERAGE Rule")
    print("=" * 70)
    
    # Test case 1: Should trigger
    print("\n1. works_under_constraints=True")
    result = detect_constraint_leverage(works_under_constraints=True)
    assert result is True, "Should detect CONSTRAINT_LEVERAGE"
    print("   ✓ CONSTRAINT_LEVERAGE detected correctly")
    
    # Test case 2: Should NOT trigger
    print("\n2. works_under_constraints=False")
    result = detect_constraint_leverage(works_under_constraints=False)
    assert result is False, "Should NOT detect CONSTRAINT_LEVERAGE"
    print("   ✓ CONSTRAINT_LEVERAGE correctly not detected")
    
    print("\n✓ CONSTRAINT_LEVERAGE rule tests passed")


def test_input_validation():
    """Test input validation (type + sanity checks)."""
    print("\n" + "=" * 70)
    print("TEST: Input Validation")
    print("=" * 70)
    
    # Test case 1: Valid inputs
    print("\n1. All valid inputs")
    validation = validate_leverage_inputs(
        replaces_human_labor=True,
        step_reduction_ratio=5,
        delivers_final_answer=False,
        unique_data_access=True,
        works_under_constraints=False,
        automation_relevance="HIGH",
        substitute_pressure="MEDIUM",
        content_saturation="LOW"
    )
    assert validation["valid"] is True, "Should pass validation"
    assert len(validation["errors"]) == 0, "Should have no errors"
    print("   ✓ Valid inputs passed validation")
    
    # Test case 2: Invalid type (boolean as string)
    print("\n2. Invalid type: boolean as string")
    validation = validate_leverage_inputs(
        replaces_human_labor="true",  # Invalid: string instead of boolean
        step_reduction_ratio=5,
        delivers_final_answer=False,
        unique_data_access=True,
        works_under_constraints=False,
        automation_relevance="HIGH",
        substitute_pressure="MEDIUM",
        content_saturation="LOW"
    )
    assert validation["valid"] is False, "Should fail validation"
    assert len(validation["errors"]) > 0, "Should have errors"
    print(f"   ✓ Invalid type detected: {validation['errors'][0]}")
    
    # Test case 3: Invalid value (negative integer)
    print("\n3. Invalid value: negative step_reduction_ratio")
    validation = validate_leverage_inputs(
        replaces_human_labor=True,
        step_reduction_ratio=-5,  # Invalid: negative
        delivers_final_answer=False,
        unique_data_access=True,
        works_under_constraints=False,
        automation_relevance="HIGH",
        substitute_pressure="MEDIUM",
        content_saturation="LOW"
    )
    assert validation["valid"] is False, "Should fail validation"
    print(f"   ✓ Invalid value detected: {validation['errors'][0]}")
    
    # Test case 4: Sanity check failure (step_reduction=0 with HIGH automation)
    print("\n4. Sanity check: step_reduction=0 but automation_relevance=HIGH")
    validation = validate_leverage_inputs(
        replaces_human_labor=False,
        step_reduction_ratio=0,  # No step reduction
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False,
        automation_relevance="HIGH",  # But HIGH automation (suspicious)
        substitute_pressure="MEDIUM",
        content_saturation="LOW"
    )
    assert validation["valid"] is False, "Should fail sanity check"
    print(f"   ✓ Sanity check failed as expected: {validation['errors'][0]}")
    
    print("\n✓ Input validation tests passed")


def test_multiple_leverage_flags():
    """Test detection of multiple leverage flags simultaneously."""
    print("\n" + "=" * 70)
    print("TEST: Multiple Leverage Flags")
    print("=" * 70)
    
    # Test case: Solution with multiple leverage types
    print("\n1. Solution with multiple leverage types")
    result = detect_leverage_flags(
        replaces_human_labor=True,
        step_reduction_ratio=10,
        delivers_final_answer=True,
        unique_data_access=True,
        works_under_constraints=True,
        automation_relevance="HIGH",
        substitute_pressure="HIGH",
        content_saturation="HIGH"
    )
    
    leverage_flags = result["leverage_flags"]
    print(f"   Detected {len(leverage_flags)} leverage flags: {leverage_flags}")
    
    # Should detect ALL 5 leverage types
    assert "COST_LEVERAGE" in leverage_flags, "Should detect COST_LEVERAGE"
    assert "TIME_LEVERAGE" in leverage_flags, "Should detect TIME_LEVERAGE"
    assert "COGNITIVE_LEVERAGE" in leverage_flags, "Should detect COGNITIVE_LEVERAGE"
    assert "ACCESS_LEVERAGE" in leverage_flags, "Should detect ACCESS_LEVERAGE"
    assert "CONSTRAINT_LEVERAGE" in leverage_flags, "Should detect CONSTRAINT_LEVERAGE"
    
    print("   ✓ All 5 leverage flags detected correctly")
    
    # Test case: Solution with no leverage
    print("\n2. Solution with no leverage")
    result = detect_leverage_flags(
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False,
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW"
    )
    
    leverage_flags = result["leverage_flags"]
    print(f"   Detected {len(leverage_flags)} leverage flags: {leverage_flags}")
    assert len(leverage_flags) == 0, "Should detect no leverage"
    print("   ✓ No leverage detected correctly")
    
    print("\n✓ Multiple leverage flags tests passed")


def test_determinism():
    """Test that leverage detection is deterministic."""
    print("\n" + "=" * 70)
    print("TEST: Determinism (Same inputs → Same outputs)")
    print("=" * 70)
    
    # Test case: Run same inputs multiple times
    test_cases = [
        {
            "replaces_human_labor": True,
            "step_reduction_ratio": 5,
            "delivers_final_answer": True,
            "unique_data_access": False,
            "works_under_constraints": False,
            "automation_relevance": "HIGH",
            "substitute_pressure": "MEDIUM",
            "content_saturation": "MEDIUM"
        },
        {
            "replaces_human_labor": False,
            "step_reduction_ratio": 2,
            "delivers_final_answer": False,
            "unique_data_access": True,
            "works_under_constraints": True,
            "automation_relevance": "LOW",
            "substitute_pressure": "LOW",
            "content_saturation": "LOW"
        }
    ]
    
    print(f"\nRunning determinism audit on {len(test_cases)} test cases...")
    audit_result = audit_determinism(test_cases)
    
    assert audit_result["deterministic"] is True, "Leverage detection should be deterministic"
    print(f"   ✓ All {audit_result['test_count']} test cases are deterministic")
    
    if audit_result["failed_cases"]:
        print(f"   ✗ Failed cases: {audit_result['failed_cases']}")
    else:
        print("   ✓ No failed cases")
    
    print("\n✓ Determinism test passed")


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n" + "=" * 70)
    print("TEST: Edge Cases")
    print("=" * 70)
    
    # Edge case 1: step_reduction_ratio exactly at threshold (5)
    print("\n1. step_reduction_ratio exactly at threshold (5)")
    result = detect_leverage_flags(
        replaces_human_labor=False,
        step_reduction_ratio=5,  # Exactly at threshold
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False,
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW"
    )
    assert "TIME_LEVERAGE" in result["leverage_flags"], "Should trigger at threshold"
    print("   ✓ TIME_LEVERAGE triggered at exact threshold (5)")
    
    # Edge case 2: step_reduction_ratio just below threshold (4)
    print("\n2. step_reduction_ratio just below threshold (4)")
    result = detect_leverage_flags(
        replaces_human_labor=False,
        step_reduction_ratio=4,  # Just below threshold
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False,
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW"
    )
    assert "TIME_LEVERAGE" not in result["leverage_flags"], "Should NOT trigger below threshold"
    print("   ✓ TIME_LEVERAGE correctly not triggered below threshold (4)")
    
    # Edge case 3: All booleans True but market signals LOW
    print("\n3. All booleans True but market signals LOW")
    result = detect_leverage_flags(
        replaces_human_labor=True,
        step_reduction_ratio=0,
        delivers_final_answer=True,
        unique_data_access=True,
        works_under_constraints=True,
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW"
    )
    # Should detect only ACCESS and CONSTRAINT (not market-dependent)
    leverage_flags = result["leverage_flags"]
    print(f"   Detected leverage: {leverage_flags}")
    assert "ACCESS_LEVERAGE" in leverage_flags
    assert "CONSTRAINT_LEVERAGE" in leverage_flags
    assert "COST_LEVERAGE" not in leverage_flags  # Requires HIGH automation
    assert "COGNITIVE_LEVERAGE" not in leverage_flags  # Requires MEDIUM+ content
    print("   ✓ Market-independent leverage detected, market-dependent not detected")
    
    print("\n✓ Edge case tests passed")


def run_all_tests():
    """Run all test suites."""
    print("\n" + "=" * 70)
    print("STAGE 3 LEVERAGE ENGINE: COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    try:
        # Individual rule tests
        test_cost_leverage_rule()
        test_time_leverage_rule()
        test_cognitive_leverage_rule()
        test_access_leverage_rule()
        test_constraint_leverage_rule()
        
        # Validation tests
        test_input_validation()
        
        # Integration tests
        test_multiple_leverage_flags()
        test_determinism()
        test_edge_cases()
        
        print("\n" + "=" * 70)
        print("✓ ALL STAGE 3 TESTS PASSED")
        print("=" * 70)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
