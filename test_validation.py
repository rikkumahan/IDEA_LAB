"""
Test suite for Validation Logic

This test suite verifies that the validation logic:
1. Correctly determines problem validity (REAL vs WEAK)
2. Correctly determines leverage presence (PRESENT vs NONE)
3. Correctly determines validation class (STRONG_FOUNDATION, etc.)
4. Works deterministically
5. Includes market data for context but doesn't let it affect validation
"""

from validation import (
    determine_problem_validity,
    determine_leverage_presence,
    determine_validation_class,
    compute_validation_state,
    get_validation_explanation,
    is_strong_validation
)


def test_problem_validity_determination():
    """Test problem validity determination"""
    print("\n" + "=" * 70)
    print("TEST: Problem Validity Determination")
    print("=" * 70)
    
    # Test DRASTIC → REAL
    print("\n1. Testing DRASTIC → REAL...")
    validity = determine_problem_validity("DRASTIC")
    assert validity == "REAL", f"Expected REAL, got {validity}"
    print("   ✓ DRASTIC → REAL")
    
    # Test SEVERE → REAL
    print("\n2. Testing SEVERE → REAL...")
    validity = determine_problem_validity("SEVERE")
    assert validity == "REAL", f"Expected REAL, got {validity}"
    print("   ✓ SEVERE → REAL")
    
    # Test MODERATE → WEAK
    print("\n3. Testing MODERATE → WEAK...")
    validity = determine_problem_validity("MODERATE")
    assert validity == "WEAK", f"Expected WEAK, got {validity}"
    print("   ✓ MODERATE → WEAK")
    
    # Test LOW → WEAK
    print("\n4. Testing LOW → WEAK...")
    validity = determine_problem_validity("LOW")
    assert validity == "WEAK", f"Expected WEAK, got {validity}"
    print("   ✓ LOW → WEAK")
    
    # Test invalid input
    print("\n5. Testing invalid problem_level...")
    try:
        determine_problem_validity("INVALID")
        print("   ✗ Invalid input accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   ✓ Invalid input rejected: {e}")
    
    print("\n" + "=" * 70)
    print("✓ Problem Validity Determination Tests Passed")
    print("=" * 70)


def test_leverage_presence_determination():
    """Test leverage presence determination"""
    print("\n" + "=" * 70)
    print("TEST: Leverage Presence Determination")
    print("=" * 70)
    
    # Test empty list → NONE
    print("\n1. Testing empty leverage_flags → NONE...")
    presence = determine_leverage_presence([])
    assert presence == "NONE", f"Expected NONE, got {presence}"
    print("   ✓ Empty list → NONE")
    
    # Test single flag → PRESENT
    print("\n2. Testing single leverage flag → PRESENT...")
    presence = determine_leverage_presence(["COST_LEVERAGE"])
    assert presence == "PRESENT", f"Expected PRESENT, got {presence}"
    print("   ✓ Single flag → PRESENT")
    
    # Test multiple flags → PRESENT
    print("\n3. Testing multiple leverage flags → PRESENT...")
    presence = determine_leverage_presence([
        "COST_LEVERAGE",
        "TIME_LEVERAGE",
        "COGNITIVE_LEVERAGE"
    ])
    assert presence == "PRESENT", f"Expected PRESENT, got {presence}"
    print("   ✓ Multiple flags → PRESENT")
    
    # Test all 5 flags → PRESENT
    print("\n4. Testing all 5 leverage flags → PRESENT...")
    presence = determine_leverage_presence([
        "COST_LEVERAGE",
        "TIME_LEVERAGE",
        "COGNITIVE_LEVERAGE",
        "ACCESS_LEVERAGE",
        "CONSTRAINT_LEVERAGE"
    ])
    assert presence == "PRESENT", f"Expected PRESENT, got {presence}"
    print("   ✓ All 5 flags → PRESENT")
    
    # Test invalid input (not a list)
    print("\n5. Testing invalid leverage_flags (not a list)...")
    try:
        determine_leverage_presence("COST_LEVERAGE")
        print("   ✗ Invalid input accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   ✓ Invalid input rejected: {e}")
    
    print("\n" + "=" * 70)
    print("✓ Leverage Presence Determination Tests Passed")
    print("=" * 70)


def test_validation_class_determination():
    """Test validation class determination"""
    print("\n" + "=" * 70)
    print("TEST: Validation Class Determination")
    print("=" * 70)
    
    # Test STRONG_FOUNDATION (REAL + PRESENT)
    print("\n1. Testing STRONG_FOUNDATION (REAL problem + PRESENT leverage)...")
    val_class = determine_validation_class("REAL", "PRESENT")
    assert val_class == "STRONG_FOUNDATION", f"Expected STRONG_FOUNDATION, got {val_class}"
    print("   ✓ REAL + PRESENT → STRONG_FOUNDATION")
    
    # Test REAL_PROBLEM_WEAK_EDGE (REAL + NONE)
    print("\n2. Testing REAL_PROBLEM_WEAK_EDGE (REAL problem + NONE leverage)...")
    val_class = determine_validation_class("REAL", "NONE")
    assert val_class == "REAL_PROBLEM_WEAK_EDGE", f"Expected REAL_PROBLEM_WEAK_EDGE, got {val_class}"
    print("   ✓ REAL + NONE → REAL_PROBLEM_WEAK_EDGE")
    
    # Test WEAK_FOUNDATION (WEAK + PRESENT)
    print("\n3. Testing WEAK_FOUNDATION (WEAK problem + PRESENT leverage)...")
    val_class = determine_validation_class("WEAK", "PRESENT")
    assert val_class == "WEAK_FOUNDATION", f"Expected WEAK_FOUNDATION, got {val_class}"
    print("   ✓ WEAK + PRESENT → WEAK_FOUNDATION")
    
    # Test WEAK_FOUNDATION (WEAK + NONE)
    print("\n4. Testing WEAK_FOUNDATION (WEAK problem + NONE leverage)...")
    val_class = determine_validation_class("WEAK", "NONE")
    assert val_class == "WEAK_FOUNDATION", f"Expected WEAK_FOUNDATION, got {val_class}"
    print("   ✓ WEAK + NONE → WEAK_FOUNDATION")
    
    # Test invalid problem_validity
    print("\n5. Testing invalid problem_validity...")
    try:
        determine_validation_class("INVALID", "PRESENT")
        print("   ✗ Invalid input accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   ✓ Invalid input rejected: {e}")
    
    # Test invalid leverage_presence
    print("\n6. Testing invalid leverage_presence...")
    try:
        determine_validation_class("REAL", "INVALID")
        print("   ✗ Invalid input accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   ✓ Invalid input rejected: {e}")
    
    print("\n" + "=" * 70)
    print("✓ Validation Class Determination Tests Passed")
    print("=" * 70)


def test_compute_validation_state():
    """Test complete validation state computation"""
    print("\n" + "=" * 70)
    print("TEST: Compute Validation State")
    print("=" * 70)
    
    # Test STRONG_FOUNDATION case
    print("\n1. Testing STRONG_FOUNDATION validation...")
    stage1 = {
        "problem_level": "DRASTIC",
        "raw_signals": {"intensity_count": 10, "complaint_count": 15, "workaround_count": 8},
        "normalized_signals": {"intensity_level": "HIGH", "complaint_level": "HIGH", "workaround_level": "HIGH"}
    }
    stage2 = {
        "automation_relevance": "HIGH",
        "substitute_pressure": "MEDIUM",
        "content_saturation": "MEDIUM"
    }
    stage3 = {
        "leverage_flags": ["COST_LEVERAGE", "TIME_LEVERAGE"]
    }
    
    result = compute_validation_state(stage1, stage2, stage3)
    
    assert "validation_state" in result, "Missing validation_state in result"
    assert result["validation_state"]["problem_validity"] == "REAL"
    assert result["validation_state"]["leverage_presence"] == "PRESENT"
    assert result["validation_state"]["validation_class"] == "STRONG_FOUNDATION"
    
    # Verify all stages are included in output
    assert "problem_reality" in result
    assert "market_reality" in result
    assert "leverage_reality" in result
    
    print("   ✓ STRONG_FOUNDATION validation computed correctly")
    print(f"   ✓ Validation state: {result['validation_state']}")
    
    # Test REAL_PROBLEM_WEAK_EDGE case
    print("\n2. Testing REAL_PROBLEM_WEAK_EDGE validation...")
    stage1 = {"problem_level": "SEVERE"}
    stage2 = {"automation_relevance": "LOW"}
    stage3 = {"leverage_flags": []}  # No leverage
    
    result = compute_validation_state(stage1, stage2, stage3)
    
    assert result["validation_state"]["problem_validity"] == "REAL"
    assert result["validation_state"]["leverage_presence"] == "NONE"
    assert result["validation_state"]["validation_class"] == "REAL_PROBLEM_WEAK_EDGE"
    
    print("   ✓ REAL_PROBLEM_WEAK_EDGE validation computed correctly")
    print(f"   ✓ Validation state: {result['validation_state']}")
    
    # Test WEAK_FOUNDATION case (WEAK problem)
    print("\n3. Testing WEAK_FOUNDATION validation (WEAK problem)...")
    stage1 = {"problem_level": "MODERATE"}
    stage2 = {"automation_relevance": "HIGH"}
    stage3 = {"leverage_flags": ["ACCESS_LEVERAGE"]}
    
    result = compute_validation_state(stage1, stage2, stage3)
    
    assert result["validation_state"]["problem_validity"] == "WEAK"
    assert result["validation_state"]["leverage_presence"] == "PRESENT"
    assert result["validation_state"]["validation_class"] == "WEAK_FOUNDATION"
    
    print("   ✓ WEAK_FOUNDATION validation computed correctly")
    print(f"   ✓ Validation state: {result['validation_state']}")
    
    # Test WEAK_FOUNDATION case (WEAK problem + no leverage)
    print("\n4. Testing WEAK_FOUNDATION validation (WEAK problem + no leverage)...")
    stage1 = {"problem_level": "LOW"}
    stage2 = {"automation_relevance": "LOW"}
    stage3 = {"leverage_flags": []}
    
    result = compute_validation_state(stage1, stage2, stage3)
    
    assert result["validation_state"]["problem_validity"] == "WEAK"
    assert result["validation_state"]["leverage_presence"] == "NONE"
    assert result["validation_state"]["validation_class"] == "WEAK_FOUNDATION"
    
    print("   ✓ WEAK_FOUNDATION validation computed correctly")
    print(f"   ✓ Validation state: {result['validation_state']}")
    
    # Test missing Stage 1 input
    print("\n5. Testing missing Stage 1 input...")
    try:
        incomplete_stage1 = {}  # Missing problem_level
        compute_validation_state(incomplete_stage1, stage2, stage3)
        print("   ✗ Missing input accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   ✓ Missing input rejected: {e}")
    
    # Test missing Stage 3 input
    print("\n6. Testing missing Stage 3 input...")
    try:
        incomplete_stage3 = {}  # Missing leverage_flags
        compute_validation_state(stage1, stage2, incomplete_stage3)
        print("   ✗ Missing input accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   ✓ Missing input rejected: {e}")
    
    print("\n" + "=" * 70)
    print("✓ Compute Validation State Tests Passed")
    print("=" * 70)


def test_market_data_is_contextual():
    """Test that market data is included but doesn't affect validation"""
    print("\n" + "=" * 70)
    print("TEST: Market Data is Contextual Only")
    print("=" * 70)
    
    print("\n1. Testing that different market data produces same validation...")
    
    stage1 = {"problem_level": "DRASTIC"}
    stage3 = {"leverage_flags": ["COST_LEVERAGE"]}
    
    # Market data variant 1: HIGH competition
    stage2_high_competition = {
        "automation_relevance": "HIGH",
        "substitute_pressure": "HIGH",
        "content_saturation": "HIGH",
        "competitor_density": "HIGH"
    }
    
    # Market data variant 2: LOW competition
    stage2_low_competition = {
        "automation_relevance": "LOW",
        "substitute_pressure": "LOW",
        "content_saturation": "LOW",
        "competitor_density": "NONE"
    }
    
    # Compute validation with both market variants
    result1 = compute_validation_state(stage1, stage2_high_competition, stage3)
    result2 = compute_validation_state(stage1, stage2_low_competition, stage3)
    
    # Validation state should be IDENTICAL
    assert result1["validation_state"] == result2["validation_state"], \
        "Market data affected validation (should be contextual only)"
    
    print("   ✓ HIGH competition market → Same validation")
    print("   ✓ LOW competition market → Same validation")
    print(f"   ✓ Both produce: {result1['validation_state']['validation_class']}")
    
    # Market data should be preserved in output (for context)
    assert result1["market_reality"] == stage2_high_competition
    assert result2["market_reality"] == stage2_low_competition
    print("   ✓ Market data preserved in output (for context)")
    
    print("\n" + "=" * 70)
    print("✓ Market Data Contextual Tests Passed")
    print("=" * 70)


def test_determinism():
    """Test that validation is deterministic"""
    print("\n" + "=" * 70)
    print("TEST: Determinism")
    print("=" * 70)
    
    print("\n1. Testing determinism (run same inputs 100 times)...")
    
    stage1 = {
        "problem_level": "SEVERE",
        "raw_signals": {"intensity_count": 5, "complaint_count": 10, "workaround_count": 6}
    }
    stage2 = {
        "automation_relevance": "MEDIUM",
        "substitute_pressure": "MEDIUM",
        "content_saturation": "LOW"
    }
    stage3 = {
        "leverage_flags": ["TIME_LEVERAGE", "COGNITIVE_LEVERAGE"]
    }
    
    # Run 100 times and collect results
    results = []
    for i in range(100):
        result = compute_validation_state(stage1, stage2, stage3)
        results.append(str(result["validation_state"]))  # Convert to string for comparison
    
    # All results should be identical
    first_result = results[0]
    all_identical = all(result == first_result for result in results)
    
    assert all_identical, f"Non-deterministic results detected: {set(results)}"
    print(f"   ✓ All 100 runs produced identical validation state")
    
    print("\n" + "=" * 70)
    print("✓ Determinism Tests Passed")
    print("=" * 70)


def test_helper_functions():
    """Test helper functions"""
    print("\n" + "=" * 70)
    print("TEST: Helper Functions")
    print("=" * 70)
    
    # Test get_validation_explanation
    print("\n1. Testing get_validation_explanation...")
    
    explanation = get_validation_explanation("STRONG_FOUNDATION")
    assert "strong foundation" in explanation.lower()
    assert len(explanation) > 50  # Should be detailed
    print("   ✓ STRONG_FOUNDATION explanation generated")
    
    explanation = get_validation_explanation("REAL_PROBLEM_WEAK_EDGE")
    assert "weak edge" in explanation.lower()
    print("   ✓ REAL_PROBLEM_WEAK_EDGE explanation generated")
    
    explanation = get_validation_explanation("WEAK_FOUNDATION")
    assert "weak foundation" in explanation.lower()
    print("   ✓ WEAK_FOUNDATION explanation generated")
    
    # Test is_strong_validation
    print("\n2. Testing is_strong_validation...")
    
    assert is_strong_validation("STRONG_FOUNDATION") == True
    print("   ✓ STRONG_FOUNDATION → True")
    
    assert is_strong_validation("REAL_PROBLEM_WEAK_EDGE") == False
    print("   ✓ REAL_PROBLEM_WEAK_EDGE → False")
    
    assert is_strong_validation("WEAK_FOUNDATION") == False
    print("   ✓ WEAK_FOUNDATION → False")
    
    print("\n" + "=" * 70)
    print("✓ Helper Functions Tests Passed")
    print("=" * 70)


def run_all_tests():
    """Run all validation logic tests"""
    print("\n" + "#" * 70)
    print("# VALIDATION LOGIC - TEST SUITE")
    print("#" * 70)
    
    test_problem_validity_determination()
    test_leverage_presence_determination()
    test_validation_class_determination()
    test_compute_validation_state()
    test_market_data_is_contextual()
    test_determinism()
    test_helper_functions()
    
    print("\n" + "#" * 70)
    print("# ALL VALIDATION LOGIC TESTS PASSED ✓")
    print("#" * 70)


if __name__ == "__main__":
    run_all_tests()
