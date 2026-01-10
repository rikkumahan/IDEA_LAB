"""
Test suite for Explanation Layer

This test suite verifies that the explanation layer:
1. Generates explanations without affecting validation logic
2. Works with LLM disabled (fallback)
3. Is truly read-only (doesn't modify inputs)
4. Rejects forbidden phrases
"""

from explanation_layer import (
    generate_explanation,
    fallback_explanation,
    contains_forbidden_phrases,
    verify_explanation_independence
)


def test_fallback_explanation():
    """Test fallback explanation generation (no LLM)"""
    print("\n" + "=" * 70)
    print("TEST: Fallback Explanation")
    print("=" * 70)
    
    # Create test validation output
    validation_output = {
        "problem_reality": {
            "problem_level": "DRASTIC",
            "raw_signals": {"intensity_count": 10, "complaint_count": 15}
        },
        "market_reality": {
            "automation_relevance": "HIGH",
            "substitute_pressure": "MEDIUM"
        },
        "leverage_reality": {
            "leverage_flags": ["COST_LEVERAGE", "TIME_LEVERAGE"]
        },
        "validation_state": {
            "problem_validity": "REAL",
            "leverage_presence": "PRESENT",
            "validation_class": "STRONG_FOUNDATION"
        }
    }
    
    print("\n1. Testing fallback explanation generation...")
    explanation = fallback_explanation(validation_output)
    
    assert isinstance(explanation, str), "Explanation should be a string"
    assert len(explanation) > 100, "Explanation should be detailed"
    assert "STRONG_FOUNDATION" in explanation or "Strong Foundation" in explanation
    print(f"   ✓ Fallback explanation generated ({len(explanation)} chars)")
    
    print("\n2. Testing explanation mentions key concepts...")
    # Check for key concepts (not exact strings)
    assert "real" in explanation.lower() or "severe" in explanation.lower()
    assert "leverage" in explanation.lower() or "advantage" in explanation.lower()
    print("   ✓ Explanation mentions key validation concepts")
    
    print("\n" + "=" * 70)
    print("✓ Fallback Explanation Tests Passed")
    print("=" * 70)


def test_explanation_with_llm_disabled():
    """Test explanation generation with LLM disabled"""
    print("\n" + "=" * 70)
    print("TEST: Explanation with LLM Disabled")
    print("=" * 70)
    
    validation_output = {
        "problem_reality": {"problem_level": "SEVERE"},
        "market_reality": {"automation_relevance": "LOW"},
        "leverage_reality": {"leverage_flags": []},
        "validation_state": {
            "problem_validity": "REAL",
            "leverage_presence": "NONE",
            "validation_class": "REAL_PROBLEM_WEAK_EDGE"
        }
    }
    
    print("\n1. Testing explanation with use_llm=False...")
    explanation = generate_explanation(validation_output, use_llm=False)
    
    assert isinstance(explanation, str), "Explanation should be a string"
    assert len(explanation) > 50, "Explanation should have content"
    print(f"   ✓ Explanation generated with LLM disabled ({len(explanation)} chars)")
    
    print("\n" + "=" * 70)
    print("✓ Explanation with LLM Disabled Tests Passed")
    print("=" * 70)


def test_forbidden_phrases():
    """Test forbidden phrase detection"""
    print("\n" + "=" * 70)
    print("TEST: Forbidden Phrases")
    print("=" * 70)
    
    # Valid explanation (no forbidden phrases)
    print("\n1. Testing valid explanation (no forbidden phrases)...")
    valid_text = "The validation shows a strong foundation. The problem is real and leverage is present."
    assert not contains_forbidden_phrases(valid_text)
    print("   ✓ Valid explanation accepted")
    
    # Invalid explanations (contain forbidden phrases)
    print("\n2. Testing invalid explanations (contain forbidden phrases)...")
    
    invalid_texts = [
        "You should pivot to a different problem.",
        "I recommend focusing on cost leverage.",
        "You need to improve your competitive edge.",
        "Based on my analysis, this will succeed.",
        "In my opinion, the market is too competitive."
    ]
    
    for text in invalid_texts:
        assert contains_forbidden_phrases(text), f"Should detect forbidden phrase in: {text}"
        print(f"   ✓ Forbidden phrase detected in: '{text[:50]}...'")
    
    print("\n" + "=" * 70)
    print("✓ Forbidden Phrases Tests Passed")
    print("=" * 70)


def test_explanation_independence():
    """Test that explanation generation doesn't modify validation output"""
    print("\n" + "=" * 70)
    print("TEST: Explanation Independence")
    print("=" * 70)
    
    validation_output = {
        "problem_reality": {"problem_level": "MODERATE"},
        "market_reality": {"automation_relevance": "MEDIUM"},
        "leverage_reality": {"leverage_flags": ["ACCESS_LEVERAGE"]},
        "validation_state": {
            "problem_validity": "WEAK",
            "leverage_presence": "PRESENT",
            "validation_class": "WEAK_FOUNDATION"
        }
    }
    
    print("\n1. Testing that explanation generation doesn't modify inputs...")
    is_independent = verify_explanation_independence(validation_output)
    
    assert is_independent, "Explanation generation modified validation output"
    print("   ✓ Validation output unchanged after explanation generation")
    
    print("\n" + "=" * 70)
    print("✓ Explanation Independence Tests Passed")
    print("=" * 70)


def test_all_validation_classes():
    """Test explanation generation for all validation classes"""
    print("\n" + "=" * 70)
    print("TEST: All Validation Classes")
    print("=" * 70)
    
    validation_classes = [
        ("STRONG_FOUNDATION", "REAL", "PRESENT"),
        ("REAL_PROBLEM_WEAK_EDGE", "REAL", "NONE"),
        ("WEAK_FOUNDATION", "WEAK", "PRESENT"),
        ("WEAK_FOUNDATION", "WEAK", "NONE")
    ]
    
    for i, (val_class, problem_val, leverage_pres) in enumerate(validation_classes, 1):
        print(f"\n{i}. Testing explanation for {val_class}...")
        
        validation_output = {
            "problem_reality": {"problem_level": "DRASTIC" if problem_val == "REAL" else "LOW"},
            "market_reality": {"automation_relevance": "HIGH"},
            "leverage_reality": {
                "leverage_flags": ["COST_LEVERAGE"] if leverage_pres == "PRESENT" else []
            },
            "validation_state": {
                "problem_validity": problem_val,
                "leverage_presence": leverage_pres,
                "validation_class": val_class
            }
        }
        
        explanation = generate_explanation(validation_output, use_llm=False)
        
        assert isinstance(explanation, str), f"Explanation should be string for {val_class}"
        assert len(explanation) > 50, f"Explanation too short for {val_class}"
        assert val_class.replace("_", " ") in explanation or val_class in explanation
        
        print(f"   ✓ Explanation generated for {val_class}")
    
    print("\n" + "=" * 70)
    print("✓ All Validation Classes Tests Passed")
    print("=" * 70)


def run_all_tests():
    """Run all explanation layer tests"""
    print("\n" + "#" * 70)
    print("# EXPLANATION LAYER - TEST SUITE")
    print("#" * 70)
    
    test_fallback_explanation()
    test_explanation_with_llm_disabled()
    test_forbidden_phrases()
    test_explanation_independence()
    test_all_validation_classes()
    
    print("\n" + "#" * 70)
    print("# ALL EXPLANATION LAYER TESTS PASSED ✓")
    print("#" * 70)


if __name__ == "__main__":
    run_all_tests()
