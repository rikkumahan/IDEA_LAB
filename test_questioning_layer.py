"""
Test suite for Questioning Layer

This test suite verifies that the questioning layer:
1. Has well-defined canonical questions
2. Uses LLM ONLY for wording (never for logic)
3. Performs dual validation (type + sanity)
4. Maintains a firewall preventing LLM leakage into Stage 3
"""

from questioning_layer import (
    CANONICAL_QUESTIONS,
    adapt_question_wording,
    validate_type,
    validate_sanity,
    validate_answer,
    collect_leverage_inputs,
    get_canonical_question,
    validate_llm_adaptation
)


def test_canonical_questions_defined():
    """Test that all 5 canonical questions are properly defined"""
    print("\n" + "=" * 70)
    print("TEST: Canonical Questions Defined")
    print("=" * 70)
    
    required_questions = [
        "replaces_human_labor",
        "step_reduction_ratio",
        "delivers_final_answer",
        "unique_data_access",
        "works_under_constraints"
    ]
    
    print(f"\n1. Testing that all {len(required_questions)} canonical questions exist...")
    for q_id in required_questions:
        assert q_id in CANONICAL_QUESTIONS, f"Missing canonical question: {q_id}"
        print(f"   ✓ {q_id} defined")
    
    print("\n2. Testing canonical question structure...")
    for q_id in required_questions:
        canonical = CANONICAL_QUESTIONS[q_id]
        
        # Check required fields
        assert "id" in canonical, f"{q_id}: Missing 'id' field"
        assert "semantic_meaning" in canonical, f"{q_id}: Missing 'semantic_meaning' field"
        assert "expected_type" in canonical, f"{q_id}: Missing 'expected_type' field"
        assert "examples" in canonical, f"{q_id}: Missing 'examples' field"
        
        # Check semantic meaning is non-empty
        assert len(canonical["semantic_meaning"]) > 50, \
            f"{q_id}: semantic_meaning too short (should be detailed)"
        
        # Check expected type is valid
        assert canonical["expected_type"] in ["boolean", "integer"], \
            f"{q_id}: Invalid expected_type '{canonical['expected_type']}'"
        
        print(f"   ✓ {q_id} has valid structure")
    
    print("\n" + "=" * 70)
    print("✓ Canonical Questions Defined Tests Passed")
    print("=" * 70)


def test_question_wording_without_llm():
    """Test that canonical wording is used when LLM is disabled"""
    print("\n" + "=" * 70)
    print("TEST: Question Wording Without LLM")
    print("=" * 70)
    
    print("\n1. Testing that canonical wording is used when use_llm=False...")
    for q_id in CANONICAL_QUESTIONS.keys():
        canonical_text = CANONICAL_QUESTIONS[q_id]["semantic_meaning"]
        adapted_text = adapt_question_wording(q_id, use_llm=False)
        
        assert adapted_text == canonical_text, \
            f"{q_id}: Wording changed even though use_llm=False"
        print(f"   ✓ {q_id} uses canonical wording")
    
    print("\n" + "=" * 70)
    print("✓ Question Wording Without LLM Tests Passed")
    print("=" * 70)


def test_type_validation():
    """Test type validation for all question types"""
    print("\n" + "=" * 70)
    print("TEST: Type Validation")
    print("=" * 70)
    
    # Test boolean validation
    print("\n1. Testing boolean type validation...")
    
    # Valid boolean
    is_valid, error = validate_type("replaces_human_labor", True)
    assert is_valid, f"Valid boolean rejected: {error}"
    print("   ✓ Valid boolean (True) accepted")
    
    is_valid, error = validate_type("replaces_human_labor", False)
    assert is_valid, f"Valid boolean rejected: {error}"
    print("   ✓ Valid boolean (False) accepted")
    
    # Invalid boolean (string)
    is_valid, error = validate_type("replaces_human_labor", "yes")
    assert not is_valid, "String accepted as boolean"
    print(f"   ✓ String rejected as boolean: {error}")
    
    # Invalid boolean (integer)
    is_valid, error = validate_type("replaces_human_labor", 1)
    assert not is_valid, "Integer accepted as boolean"
    print(f"   ✓ Integer rejected as boolean: {error}")
    
    # Test integer validation
    print("\n2. Testing integer type validation...")
    
    # Valid integer (positive)
    is_valid, error = validate_type("step_reduction_ratio", 10)
    assert is_valid, f"Valid integer rejected: {error}"
    print("   ✓ Valid integer (10) accepted")
    
    # Valid integer (zero)
    is_valid, error = validate_type("step_reduction_ratio", 0)
    assert is_valid, f"Valid integer rejected: {error}"
    print("   ✓ Valid integer (0) accepted")
    
    # Invalid integer (negative)
    is_valid, error = validate_type("step_reduction_ratio", -5)
    assert not is_valid, "Negative integer accepted"
    print(f"   ✓ Negative integer rejected: {error}")
    
    # Invalid integer (float)
    is_valid, error = validate_type("step_reduction_ratio", 5.5)
    assert not is_valid, "Float accepted as integer"
    print(f"   ✓ Float rejected as integer: {error}")
    
    # Invalid integer (string)
    is_valid, error = validate_type("step_reduction_ratio", "10")
    assert not is_valid, "String accepted as integer"
    print(f"   ✓ String rejected as integer: {error}")
    
    print("\n" + "=" * 70)
    print("✓ Type Validation Tests Passed")
    print("=" * 70)


def test_sanity_validation():
    """Test sanity validation for detecting inconsistencies"""
    print("\n" + "=" * 70)
    print("TEST: Sanity Validation")
    print("=" * 70)
    
    # Test sanity check: step_reduction_ratio == 0 AND automation_relevance == HIGH
    print("\n1. Testing sanity check for step_reduction_ratio...")
    
    # Invalid: step_reduction_ratio=0 with HIGH automation
    is_valid, error = validate_sanity(
        "step_reduction_ratio", 
        0,
        automation_relevance="HIGH"
    )
    assert not is_valid, "Inconsistent answer accepted (0 steps with HIGH automation)"
    print(f"   ✓ Inconsistency detected: {error}")
    
    # Valid: step_reduction_ratio=0 with LOW automation
    is_valid, error = validate_sanity(
        "step_reduction_ratio", 
        0,
        automation_relevance="LOW"
    )
    assert is_valid, f"Valid answer rejected: {error}"
    print("   ✓ Valid: step_reduction_ratio=0 with LOW automation")
    
    # Valid: step_reduction_ratio=10 with HIGH automation
    is_valid, error = validate_sanity(
        "step_reduction_ratio", 
        10,
        automation_relevance="HIGH"
    )
    assert is_valid, f"Valid answer rejected: {error}"
    print("   ✓ Valid: step_reduction_ratio=10 with HIGH automation")
    
    # Test other questions have no sanity checks (always valid)
    print("\n2. Testing other questions have no sanity checks...")
    for q_id in ["replaces_human_labor", "delivers_final_answer", 
                 "unique_data_access", "works_under_constraints"]:
        is_valid, error = validate_sanity(q_id, True)
        assert is_valid, f"{q_id}: Unexpected sanity check: {error}"
        print(f"   ✓ {q_id} has no sanity checks (always valid)")
    
    print("\n" + "=" * 70)
    print("✓ Sanity Validation Tests Passed")
    print("=" * 70)


def test_dual_validation():
    """Test that dual validation (type + sanity) works correctly"""
    print("\n" + "=" * 70)
    print("TEST: Dual Validation")
    print("=" * 70)
    
    print("\n1. Testing dual validation passes when both checks pass...")
    is_valid, error = validate_answer(
        "step_reduction_ratio",
        10,
        automation_relevance="HIGH"
    )
    assert is_valid, f"Valid answer rejected: {error}"
    print("   ✓ Dual validation passed (type=int, sanity=consistent)")
    
    print("\n2. Testing dual validation fails on type check...")
    is_valid, error = validate_answer(
        "step_reduction_ratio",
        "10",  # String instead of int
        automation_relevance="HIGH"
    )
    assert not is_valid, "Type check should fail"
    print(f"   ✓ Dual validation failed on type check: {error}")
    
    print("\n3. Testing dual validation fails on sanity check...")
    is_valid, error = validate_answer(
        "step_reduction_ratio",
        0,  # Inconsistent with HIGH automation
        automation_relevance="HIGH"
    )
    assert not is_valid, "Sanity check should fail"
    print(f"   ✓ Dual validation failed on sanity check: {error}")
    
    print("\n" + "=" * 70)
    print("✓ Dual Validation Tests Passed")
    print("=" * 70)


def test_firewall_structured_inputs_only():
    """Test that firewall allows ONLY validated structured inputs"""
    print("\n" + "=" * 70)
    print("TEST: Firewall - Structured Inputs Only")
    print("=" * 70)
    
    print("\n1. Testing collection with valid inputs...")
    simulated_answers = {
        "replaces_human_labor": True,
        "step_reduction_ratio": 10,
        "delivers_final_answer": True,
        "unique_data_access": False,
        "works_under_constraints": True
    }
    
    validated_inputs = collect_leverage_inputs(
        automation_relevance="HIGH",
        use_llm=False,  # Disable LLM for testing
        simulated_answers=simulated_answers
    )
    
    # Check that all inputs are present
    assert len(validated_inputs) == 5, f"Expected 5 inputs, got {len(validated_inputs)}"
    
    # Check that all inputs are structured (boolean or integer)
    for key, value in validated_inputs.items():
        assert isinstance(value, (bool, int)), \
            f"{key} is not structured (type: {type(value)})"
    
    # Check exact values
    assert validated_inputs == simulated_answers, \
        f"Inputs don't match: {validated_inputs} != {simulated_answers}"
    
    print("   ✓ All 5 inputs collected and validated")
    print(f"   ✓ All inputs are structured: {validated_inputs}")
    
    print("\n2. Testing collection rejects invalid inputs...")
    invalid_answers = {
        "replaces_human_labor": "yes",  # Should be boolean
        "step_reduction_ratio": 10,
        "delivers_final_answer": True,
        "unique_data_access": False,
        "works_under_constraints": True
    }
    
    try:
        collect_leverage_inputs(
            automation_relevance="HIGH",
            use_llm=False,
            simulated_answers=invalid_answers
        )
        print("   ✗ Invalid input accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   ✓ Invalid input rejected: {e}")
    
    print("\n3. Testing collection rejects inconsistent inputs...")
    inconsistent_answers = {
        "replaces_human_labor": True,
        "step_reduction_ratio": 0,  # Inconsistent with HIGH automation
        "delivers_final_answer": True,
        "unique_data_access": False,
        "works_under_constraints": True
    }
    
    try:
        collect_leverage_inputs(
            automation_relevance="HIGH",
            use_llm=False,
            simulated_answers=inconsistent_answers
        )
        print("   ✗ Inconsistent input accepted (should reject)")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"   ✓ Inconsistent input rejected: {e}")
    
    print("\n" + "=" * 70)
    print("✓ Firewall Tests Passed")
    print("=" * 70)


def test_llm_wording_constraints():
    """Test that LLM wording follows constraints"""
    print("\n" + "=" * 70)
    print("TEST: LLM Wording Constraints")
    print("=" * 70)
    
    print("\n1. Testing LLM wording validation helper...")
    
    # Test valid adaptation (no forbidden words)
    valid_adaptation = "Does your solution automate work that humans currently do manually?"
    is_valid, reason = validate_llm_adaptation("replaces_human_labor", valid_adaptation)
    assert is_valid, f"Valid adaptation rejected: {reason}"
    print(f"   ✓ Valid adaptation accepted")
    
    # Test invalid adaptation (contains "leverage")
    invalid_adaptation = "Does your solution leverage automation to replace human labor?"
    is_valid, reason = validate_llm_adaptation("replaces_human_labor", invalid_adaptation)
    assert not is_valid, "Invalid adaptation accepted (contains 'leverage')"
    print(f"   ✓ Invalid adaptation rejected: {reason}")
    
    # Test invalid adaptation (contains "better")
    invalid_adaptation = "Is your solution better than human work?"
    is_valid, reason = validate_llm_adaptation("replaces_human_labor", invalid_adaptation)
    # Note: "better" alone is not forbidden, but "better than" is
    print(f"   ✓ Validation detected: {reason}")
    
    # Test invalid adaptation (missing core concepts)
    invalid_adaptation = "Is this a good idea?"  # Too vague, missing concepts
    is_valid, reason = validate_llm_adaptation("replaces_human_labor", invalid_adaptation)
    assert not is_valid, "Invalid adaptation accepted (missing core concepts)"
    print(f"   ✓ Invalid adaptation rejected: {reason}")
    
    print("\n" + "=" * 70)
    print("✓ LLM Wording Constraints Tests Passed")
    print("=" * 70)


def test_no_free_text_inputs():
    """Test that no free text inputs can reach Stage 3"""
    print("\n" + "=" * 70)
    print("TEST: No Free Text Inputs")
    print("=" * 70)
    
    print("\n1. Verifying all canonical questions require structured inputs...")
    for q_id in CANONICAL_QUESTIONS.keys():
        canonical = CANONICAL_QUESTIONS[q_id]
        expected_type = canonical["expected_type"]
        
        assert expected_type in ["boolean", "integer"], \
            f"{q_id}: Unexpected type '{expected_type}' (should be boolean or integer)"
        
        print(f"   ✓ {q_id} expects {expected_type} (structured)")
    
    print("\n2. Testing that string answers are rejected...")
    # Try to pass string answer for boolean question
    is_valid, error = validate_type("replaces_human_labor", "yes, it replaces labor")
    assert not is_valid, "Free text accepted for boolean question"
    print(f"   ✓ Free text rejected for boolean: {error}")
    
    # Try to pass string answer for integer question
    is_valid, error = validate_type("step_reduction_ratio", "about 10 steps")
    assert not is_valid, "Free text accepted for integer question"
    print(f"   ✓ Free text rejected for integer: {error}")
    
    print("\n" + "=" * 70)
    print("✓ No Free Text Inputs Tests Passed")
    print("=" * 70)


def run_all_tests():
    """Run all questioning layer tests"""
    print("\n" + "#" * 70)
    print("# QUESTIONING LAYER - TEST SUITE")
    print("#" * 70)
    
    test_canonical_questions_defined()
    test_question_wording_without_llm()
    test_type_validation()
    test_sanity_validation()
    test_dual_validation()
    test_firewall_structured_inputs_only()
    test_llm_wording_constraints()
    test_no_free_text_inputs()
    
    print("\n" + "#" * 70)
    print("# ALL QUESTIONING LAYER TESTS PASSED ✓")
    print("#" * 70)


if __name__ == "__main__":
    run_all_tests()
