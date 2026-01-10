"""
Test suite for Stage 3: Deterministic Leverage Engine

This test suite verifies that Stage 3:
1. Implements all 5 leverage rules correctly (EXACT logic)
2. Works deterministically (same inputs → same outputs)
3. Handles edge cases properly
4. Works identically with LLM ON/OFF (no LLM used in Stage 3)
"""

from stage3_leverage import (
    LeverageInput,
    compute_leverage_flags,
    compute_leverage_reality
)


def test_leverage_input_validation():
    """Test that LeverageInput validates inputs correctly"""
    print("\n" + "=" * 70)
    print("TEST: Leverage Input Validation")
    print("=" * 70)
    
    # Valid inputs
    print("\n1. Testing valid inputs...")
    try:
        valid_input = LeverageInput(
            automation_relevance="HIGH",
            substitute_pressure="MEDIUM",
            content_saturation="LOW",
            replaces_human_labor=True,
            step_reduction_ratio=10,
            delivers_final_answer=False,
            unique_data_access=True,
            works_under_constraints=False
        )
        print("   ✓ Valid inputs accepted")
    except ValueError as e:
        print(f"   ✗ Valid inputs rejected: {e}")
        raise
    
    # Invalid automation_relevance
    print("\n2. Testing invalid automation_relevance...")
    try:
        LeverageInput(
            automation_relevance="INVALID",
            substitute_pressure="MEDIUM",
            content_saturation="LOW",
            replaces_human_labor=True,
            step_reduction_ratio=10,
            delivers_final_answer=False,
            unique_data_access=True,
            works_under_constraints=False
        )
        print("   ✗ Invalid automation_relevance accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("   ✓ Invalid automation_relevance rejected")
    
    # Invalid step_reduction_ratio (negative)
    print("\n3. Testing negative step_reduction_ratio...")
    try:
        LeverageInput(
            automation_relevance="HIGH",
            substitute_pressure="MEDIUM",
            content_saturation="LOW",
            replaces_human_labor=True,
            step_reduction_ratio=-5,
            delivers_final_answer=False,
            unique_data_access=True,
            works_under_constraints=False
        )
        print("   ✗ Negative step_reduction_ratio accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("   ✓ Negative step_reduction_ratio rejected")
    
    # Invalid type for boolean field
    print("\n4. Testing invalid type for boolean field...")
    try:
        LeverageInput(
            automation_relevance="HIGH",
            substitute_pressure="MEDIUM",
            content_saturation="LOW",
            replaces_human_labor="yes",  # Should be bool
            step_reduction_ratio=10,
            delivers_final_answer=False,
            unique_data_access=True,
            works_under_constraints=False
        )
        print("   ✗ String for boolean field accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("   ✓ String for boolean field rejected")
    
    print("\n" + "=" * 70)
    print("✓ Leverage Input Validation Tests Passed")
    print("=" * 70)


def test_cost_leverage_rule():
    """Test COST_LEVERAGE rule: replaces_human_labor AND automation_relevance == HIGH"""
    print("\n" + "=" * 70)
    print("TEST: COST_LEVERAGE Rule")
    print("=" * 70)
    
    # Test 1: Both conditions met → COST_LEVERAGE
    print("\n1. Testing COST_LEVERAGE trigger (both conditions met)...")
    leverage_input = LeverageInput(
        automation_relevance="HIGH",
        substitute_pressure="LOW",
        content_saturation="LOW",
        replaces_human_labor=True,  # ✓
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "COST_LEVERAGE" in flags, f"Expected COST_LEVERAGE, got {flags}"
    print(f"   ✓ COST_LEVERAGE triggered: {flags}")
    
    # Test 2: replaces_human_labor=False → No COST_LEVERAGE
    print("\n2. Testing COST_LEVERAGE not triggered (replaces_human_labor=False)...")
    leverage_input = LeverageInput(
        automation_relevance="HIGH",
        substitute_pressure="LOW",
        content_saturation="LOW",
        replaces_human_labor=False,  # ✗
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "COST_LEVERAGE" not in flags, f"Unexpected COST_LEVERAGE in {flags}"
    print(f"   ✓ COST_LEVERAGE not triggered: {flags}")
    
    # Test 3: automation_relevance=MEDIUM → No COST_LEVERAGE
    print("\n3. Testing COST_LEVERAGE not triggered (automation_relevance=MEDIUM)...")
    leverage_input = LeverageInput(
        automation_relevance="MEDIUM",  # ✗
        substitute_pressure="LOW",
        content_saturation="LOW",
        replaces_human_labor=True,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "COST_LEVERAGE" not in flags, f"Unexpected COST_LEVERAGE in {flags}"
    print(f"   ✓ COST_LEVERAGE not triggered: {flags}")
    
    print("\n" + "=" * 70)
    print("✓ COST_LEVERAGE Rule Tests Passed")
    print("=" * 70)


def test_time_leverage_rule():
    """Test TIME_LEVERAGE rule: step_reduction_ratio >= 5 OR (automation_relevance == HIGH AND substitute_pressure >= MEDIUM)"""
    print("\n" + "=" * 70)
    print("TEST: TIME_LEVERAGE Rule")
    print("=" * 70)
    
    # Test 1: step_reduction_ratio >= 5 → TIME_LEVERAGE
    print("\n1. Testing TIME_LEVERAGE trigger (step_reduction_ratio=5)...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW",
        replaces_human_labor=False,
        step_reduction_ratio=5,  # ✓ (exactly 5)
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "TIME_LEVERAGE" in flags, f"Expected TIME_LEVERAGE, got {flags}"
    print(f"   ✓ TIME_LEVERAGE triggered: {flags}")
    
    # Test 2: step_reduction_ratio=10 → TIME_LEVERAGE
    print("\n2. Testing TIME_LEVERAGE trigger (step_reduction_ratio=10)...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW",
        replaces_human_labor=False,
        step_reduction_ratio=10,  # ✓ (> 5)
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "TIME_LEVERAGE" in flags, f"Expected TIME_LEVERAGE, got {flags}"
    print(f"   ✓ TIME_LEVERAGE triggered: {flags}")
    
    # Test 3: automation_relevance=HIGH AND substitute_pressure=MEDIUM → TIME_LEVERAGE
    print("\n3. Testing TIME_LEVERAGE trigger (automation + substitute)...")
    leverage_input = LeverageInput(
        automation_relevance="HIGH",  # ✓
        substitute_pressure="MEDIUM",  # ✓
        content_saturation="LOW",
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "TIME_LEVERAGE" in flags, f"Expected TIME_LEVERAGE, got {flags}"
    print(f"   ✓ TIME_LEVERAGE triggered: {flags}")
    
    # Test 4: automation_relevance=HIGH AND substitute_pressure=HIGH → TIME_LEVERAGE
    print("\n4. Testing TIME_LEVERAGE trigger (substitute_pressure=HIGH)...")
    leverage_input = LeverageInput(
        automation_relevance="HIGH",  # ✓
        substitute_pressure="HIGH",  # ✓
        content_saturation="LOW",
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "TIME_LEVERAGE" in flags, f"Expected TIME_LEVERAGE, got {flags}"
    print(f"   ✓ TIME_LEVERAGE triggered: {flags}")
    
    # Test 5: step_reduction_ratio=4 AND no automation → No TIME_LEVERAGE
    print("\n5. Testing TIME_LEVERAGE not triggered (step_reduction_ratio=4)...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW",
        replaces_human_labor=False,
        step_reduction_ratio=4,  # ✗ (< 5)
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "TIME_LEVERAGE" not in flags, f"Unexpected TIME_LEVERAGE in {flags}"
    print(f"   ✓ TIME_LEVERAGE not triggered: {flags}")
    
    # Test 6: automation_relevance=HIGH BUT substitute_pressure=LOW → No TIME_LEVERAGE
    print("\n6. Testing TIME_LEVERAGE not triggered (substitute_pressure=LOW)...")
    leverage_input = LeverageInput(
        automation_relevance="HIGH",
        substitute_pressure="LOW",  # ✗
        content_saturation="LOW",
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "TIME_LEVERAGE" not in flags, f"Unexpected TIME_LEVERAGE in {flags}"
    print(f"   ✓ TIME_LEVERAGE not triggered: {flags}")
    
    print("\n" + "=" * 70)
    print("✓ TIME_LEVERAGE Rule Tests Passed")
    print("=" * 70)


def test_cognitive_leverage_rule():
    """Test COGNITIVE_LEVERAGE rule: delivers_final_answer AND content_saturation >= MEDIUM"""
    print("\n" + "=" * 70)
    print("TEST: COGNITIVE_LEVERAGE Rule")
    print("=" * 70)
    
    # Test 1: Both conditions met (content_saturation=MEDIUM) → COGNITIVE_LEVERAGE
    print("\n1. Testing COGNITIVE_LEVERAGE trigger (content_saturation=MEDIUM)...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="MEDIUM",  # ✓
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=True,  # ✓
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "COGNITIVE_LEVERAGE" in flags, f"Expected COGNITIVE_LEVERAGE, got {flags}"
    print(f"   ✓ COGNITIVE_LEVERAGE triggered: {flags}")
    
    # Test 2: Both conditions met (content_saturation=HIGH) → COGNITIVE_LEVERAGE
    print("\n2. Testing COGNITIVE_LEVERAGE trigger (content_saturation=HIGH)...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="HIGH",  # ✓
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=True,  # ✓
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "COGNITIVE_LEVERAGE" in flags, f"Expected COGNITIVE_LEVERAGE, got {flags}"
    print(f"   ✓ COGNITIVE_LEVERAGE triggered: {flags}")
    
    # Test 3: delivers_final_answer=False → No COGNITIVE_LEVERAGE
    print("\n3. Testing COGNITIVE_LEVERAGE not triggered (delivers_final_answer=False)...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="HIGH",
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,  # ✗
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "COGNITIVE_LEVERAGE" not in flags, f"Unexpected COGNITIVE_LEVERAGE in {flags}"
    print(f"   ✓ COGNITIVE_LEVERAGE not triggered: {flags}")
    
    # Test 4: content_saturation=LOW → No COGNITIVE_LEVERAGE
    print("\n4. Testing COGNITIVE_LEVERAGE not triggered (content_saturation=LOW)...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW",  # ✗
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=True,
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "COGNITIVE_LEVERAGE" not in flags, f"Unexpected COGNITIVE_LEVERAGE in {flags}"
    print(f"   ✓ COGNITIVE_LEVERAGE not triggered: {flags}")
    
    print("\n" + "=" * 70)
    print("✓ COGNITIVE_LEVERAGE Rule Tests Passed")
    print("=" * 70)


def test_access_leverage_rule():
    """Test ACCESS_LEVERAGE rule: unique_data_access == true"""
    print("\n" + "=" * 70)
    print("TEST: ACCESS_LEVERAGE Rule")
    print("=" * 70)
    
    # Test 1: unique_data_access=True → ACCESS_LEVERAGE
    print("\n1. Testing ACCESS_LEVERAGE trigger (unique_data_access=True)...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW",
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=True,  # ✓
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "ACCESS_LEVERAGE" in flags, f"Expected ACCESS_LEVERAGE, got {flags}"
    print(f"   ✓ ACCESS_LEVERAGE triggered: {flags}")
    
    # Test 2: unique_data_access=False → No ACCESS_LEVERAGE
    print("\n2. Testing ACCESS_LEVERAGE not triggered (unique_data_access=False)...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW",
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,  # ✗
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    assert "ACCESS_LEVERAGE" not in flags, f"Unexpected ACCESS_LEVERAGE in {flags}"
    print(f"   ✓ ACCESS_LEVERAGE not triggered: {flags}")
    
    print("\n" + "=" * 70)
    print("✓ ACCESS_LEVERAGE Rule Tests Passed")
    print("=" * 70)


def test_constraint_leverage_rule():
    """Test CONSTRAINT_LEVERAGE rule: works_under_constraints == true"""
    print("\n" + "=" * 70)
    print("TEST: CONSTRAINT_LEVERAGE Rule")
    print("=" * 70)
    
    # Test 1: works_under_constraints=True → CONSTRAINT_LEVERAGE
    print("\n1. Testing CONSTRAINT_LEVERAGE trigger (works_under_constraints=True)...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW",
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=True  # ✓
    )
    flags = compute_leverage_flags(leverage_input)
    assert "CONSTRAINT_LEVERAGE" in flags, f"Expected CONSTRAINT_LEVERAGE, got {flags}"
    print(f"   ✓ CONSTRAINT_LEVERAGE triggered: {flags}")
    
    # Test 2: works_under_constraints=False → No CONSTRAINT_LEVERAGE
    print("\n2. Testing CONSTRAINT_LEVERAGE not triggered (works_under_constraints=False)...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW",
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False  # ✗
    )
    flags = compute_leverage_flags(leverage_input)
    assert "CONSTRAINT_LEVERAGE" not in flags, f"Unexpected CONSTRAINT_LEVERAGE in {flags}"
    print(f"   ✓ CONSTRAINT_LEVERAGE not triggered: {flags}")
    
    print("\n" + "=" * 70)
    print("✓ CONSTRAINT_LEVERAGE Rule Tests Passed")
    print("=" * 70)


def test_multiple_leverage_flags():
    """Test that multiple leverage flags can be emitted simultaneously"""
    print("\n" + "=" * 70)
    print("TEST: Multiple Leverage Flags")
    print("=" * 70)
    
    # Test: All flags triggered
    print("\n1. Testing all leverage flags triggered simultaneously...")
    leverage_input = LeverageInput(
        automation_relevance="HIGH",
        substitute_pressure="HIGH",
        content_saturation="HIGH",
        replaces_human_labor=True,      # → COST_LEVERAGE
        step_reduction_ratio=10,        # → TIME_LEVERAGE
        delivers_final_answer=True,     # → COGNITIVE_LEVERAGE
        unique_data_access=True,        # → ACCESS_LEVERAGE
        works_under_constraints=True    # → CONSTRAINT_LEVERAGE
    )
    flags = compute_leverage_flags(leverage_input)
    
    expected_flags = {
        "COST_LEVERAGE",
        "TIME_LEVERAGE",
        "COGNITIVE_LEVERAGE",
        "ACCESS_LEVERAGE",
        "CONSTRAINT_LEVERAGE"
    }
    
    assert set(flags) == expected_flags, f"Expected {expected_flags}, got {set(flags)}"
    print(f"   ✓ All 5 leverage flags triggered: {flags}")
    
    # Test: No flags triggered
    print("\n2. Testing no leverage flags triggered...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW",
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False
    )
    flags = compute_leverage_flags(leverage_input)
    
    assert len(flags) == 0, f"Expected no flags, got {flags}"
    print(f"   ✓ No leverage flags triggered: {flags}")
    
    # Test: Partial flags (2 out of 5)
    print("\n3. Testing partial leverage flags (2 out of 5)...")
    leverage_input = LeverageInput(
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW",
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=True,        # → ACCESS_LEVERAGE
        works_under_constraints=True    # → CONSTRAINT_LEVERAGE
    )
    flags = compute_leverage_flags(leverage_input)
    
    expected_flags = {"ACCESS_LEVERAGE", "CONSTRAINT_LEVERAGE"}
    assert set(flags) == expected_flags, f"Expected {expected_flags}, got {set(flags)}"
    print(f"   ✓ 2 leverage flags triggered: {flags}")
    
    print("\n" + "=" * 70)
    print("✓ Multiple Leverage Flags Tests Passed")
    print("=" * 70)


def test_determinism():
    """Test that Stage 3 is deterministic (same inputs → same outputs)"""
    print("\n" + "=" * 70)
    print("TEST: Determinism")
    print("=" * 70)
    
    print("\n1. Testing determinism (run same inputs 100 times)...")
    
    leverage_input = LeverageInput(
        automation_relevance="HIGH",
        substitute_pressure="MEDIUM",
        content_saturation="MEDIUM",
        replaces_human_labor=True,
        step_reduction_ratio=7,
        delivers_final_answer=True,
        unique_data_access=False,
        works_under_constraints=True
    )
    
    # Run 100 times and collect results
    results = []
    for i in range(100):
        flags = compute_leverage_flags(leverage_input)
        results.append(tuple(sorted(flags)))  # Sort for comparison
    
    # All results should be identical
    first_result = results[0]
    all_identical = all(result == first_result for result in results)
    
    assert all_identical, f"Non-deterministic results detected: {set(results)}"
    print(f"   ✓ All 100 runs produced identical output: {list(first_result)}")
    
    print("\n" + "=" * 70)
    print("✓ Determinism Tests Passed")
    print("=" * 70)


def test_compute_leverage_reality():
    """Test the main entry point function"""
    print("\n" + "=" * 70)
    print("TEST: compute_leverage_reality Entry Point")
    print("=" * 70)
    
    # Test with valid inputs
    print("\n1. Testing compute_leverage_reality with valid inputs...")
    stage2_market_strength = {
        "automation_relevance": "HIGH",
        "substitute_pressure": "MEDIUM",
        "content_saturation": "HIGH"
    }
    
    user_leverage_inputs = {
        "replaces_human_labor": True,
        "step_reduction_ratio": 10,
        "delivers_final_answer": True,
        "unique_data_access": False,
        "works_under_constraints": True
    }
    
    result = compute_leverage_reality(stage2_market_strength, user_leverage_inputs)
    
    assert "leverage_flags" in result, "Missing leverage_flags in result"
    assert "inputs_used" in result, "Missing inputs_used in result"
    
    # Verify expected flags
    expected_flags = {"COST_LEVERAGE", "TIME_LEVERAGE", "COGNITIVE_LEVERAGE", "CONSTRAINT_LEVERAGE"}
    assert set(result["leverage_flags"]) == expected_flags, \
        f"Expected {expected_flags}, got {set(result['leverage_flags'])}"
    
    print(f"   ✓ leverage_flags: {result['leverage_flags']}")
    print(f"   ✓ inputs_used recorded for auditability")
    
    # Test with missing Stage 2 input
    print("\n2. Testing compute_leverage_reality with missing Stage 2 input...")
    try:
        incomplete_stage2 = {
            "automation_relevance": "HIGH",
            # Missing substitute_pressure
            "content_saturation": "HIGH"
        }
        compute_leverage_reality(incomplete_stage2, user_leverage_inputs)
        print("   ✗ Missing input accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   ✓ Missing input rejected: {e}")
    
    # Test with missing user input
    print("\n3. Testing compute_leverage_reality with missing user input...")
    try:
        incomplete_user = {
            "replaces_human_labor": True,
            # Missing step_reduction_ratio
            "delivers_final_answer": True,
            "unique_data_access": False,
            "works_under_constraints": True
        }
        compute_leverage_reality(stage2_market_strength, incomplete_user)
        print("   ✗ Missing input accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   ✓ Missing input rejected: {e}")
    
    print("\n" + "=" * 70)
    print("✓ compute_leverage_reality Entry Point Tests Passed")
    print("=" * 70)


def run_all_tests():
    """Run all Stage 3 tests"""
    print("\n" + "#" * 70)
    print("# STAGE 3 DETERMINISTIC LEVERAGE ENGINE - TEST SUITE")
    print("#" * 70)
    
    test_leverage_input_validation()
    test_cost_leverage_rule()
    test_time_leverage_rule()
    test_cognitive_leverage_rule()
    test_access_leverage_rule()
    test_constraint_leverage_rule()
    test_multiple_leverage_flags()
    test_determinism()
    test_compute_leverage_reality()
    
    print("\n" + "#" * 70)
    print("# ALL STAGE 3 TESTS PASSED ✓")
    print("#" * 70)


if __name__ == "__main__":
    run_all_tests()
