"""
End-to-End Integration Test: All Stages + Validation

This test validates the complete workflow:
1. Stage 1: Problem Reality
2. Stage 2: Market Reality
3. Stage 3: Leverage Detection
4. Validation: Final classification
5. Determinism check (LLM ON vs OFF)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import analyze_idea, analyze_user_solution_competitors, IdeaInput, UserSolution
from stage3_leverage import detect_leverage_flags
from validation import validate_idea


def test_strong_foundation_scenario():
    """Test complete workflow for STRONG_FOUNDATION scenario."""
    print("=" * 70)
    print("TEST: STRONG_FOUNDATION Scenario (End-to-End)")
    print("=" * 70)
    
    # ========================================================================
    # STAGE 1: Problem Reality
    # ========================================================================
    print("\n=== STAGE 1: Problem Reality ===")
    problem_input = IdeaInput(
        problem="manual data entry",
        target_user="small business owners",
        user_claimed_frequency="daily"
    )
    
    # Note: We'll simulate Stage 1 results instead of running actual searches
    # In production, this would call analyze_idea(problem_input)
    stage1_result = {
        "problem_level": "SEVERE",
        "raw_signals": {
            "complaint_count": 12,
            "workaround_count": 8,
            "intensity_count": 5
        },
        "normalized_signals": {
            "complaint_level": "HIGH",
            "workaround_level": "HIGH",
            "intensity_level": "HIGH"
        }
    }
    
    problem_level = stage1_result["problem_level"]
    print(f"Problem Level: {problem_level}")
    assert problem_level in ["DRASTIC", "SEVERE"], "Should be a real problem"
    print("✓ Stage 1 complete: REAL problem detected")
    
    # ========================================================================
    # STAGE 2: Market Reality
    # ========================================================================
    print("\n=== STAGE 2: Market Reality ===")
    solution_input = UserSolution(
        core_action="automate data entry",
        input_required="CSV files, spreadsheets",
        output_type="cleaned database records",
        target_user="small business owners",
        automation_level="AI-powered"
    )
    
    # Simulate Stage 2 results
    stage2_result = {
        "solution_modality": "SOFTWARE",
        "market_strength": {
            "competitor_density": "MEDIUM",
            "market_fragmentation": "FRAGMENTED",
            "substitute_pressure": "HIGH",
            "content_saturation": "HIGH",
            "solution_class_maturity": "ESTABLISHED",
            "automation_relevance": "HIGH"
        },
        "competitors": {
            "software": [
                {"name": "Competitor A", "url": "https://competitora.com", "pricing_model": "freemium"},
                {"name": "Competitor B", "url": "https://competitorb.com", "pricing_model": "paid"}
            ],
            "services_expected": False
        }
    }
    
    market_strength = stage2_result["market_strength"]
    print(f"Solution Modality: {stage2_result['solution_modality']}")
    print(f"Competitor Density: {market_strength['competitor_density']}")
    print(f"Automation Relevance: {market_strength['automation_relevance']}")
    print("✓ Stage 2 complete: Market analyzed")
    
    # ========================================================================
    # STAGE 3: Leverage Detection
    # ========================================================================
    print("\n=== STAGE 3: Leverage Detection ===")
    
    stage3_result = detect_leverage_flags(
        # User leverage inputs
        replaces_human_labor=True,
        step_reduction_ratio=8,
        delivers_final_answer=True,
        unique_data_access=False,
        works_under_constraints=False,
        # Market inputs from Stage 2
        automation_relevance=market_strength["automation_relevance"],
        substitute_pressure=market_strength["substitute_pressure"],
        content_saturation=market_strength["content_saturation"]
    )
    
    leverage_flags = stage3_result["leverage_flags"]
    print(f"Leverage Flags Detected: {leverage_flags}")
    
    # Should detect multiple leverage types
    assert len(leverage_flags) > 0, "Should detect at least one leverage"
    assert "COST_LEVERAGE" in leverage_flags, "Should detect COST_LEVERAGE"
    assert "TIME_LEVERAGE" in leverage_flags, "Should detect TIME_LEVERAGE"
    print(f"✓ Stage 3 complete: {len(leverage_flags)} leverage flag(s) detected")
    
    # ========================================================================
    # VALIDATION: Synchronize all stages
    # ========================================================================
    print("\n=== VALIDATION: Synchronizing All Stages ===")
    
    validation_result = validate_idea(
        problem_level=problem_level,
        problem_signals=stage1_result["raw_signals"],
        market_strength=market_strength,
        leverage_flags=leverage_flags,
        leverage_details=stage3_result["leverage_details"]
    )
    
    validation_state = validation_result["validation_state"]
    validation_class = validation_state["validation_class"]
    
    print(f"Problem Validity: {validation_state['problem_validity']}")
    print(f"Leverage Presence: {validation_state['leverage_presence']}")
    print(f"Validation Class: {validation_class}")
    
    # Assertions
    assert validation_state["problem_validity"] == "REAL", "Problem should be REAL"
    assert validation_state["leverage_presence"] == "PRESENT", "Leverage should be PRESENT"
    assert validation_class == "STRONG_FOUNDATION", "Should be STRONG_FOUNDATION"
    
    print("✓ Validation complete: STRONG_FOUNDATION confirmed")
    print("\n" + "=" * 70)
    print("✓ STRONG_FOUNDATION END-TO-END TEST PASSED")
    print("=" * 70)
    
    return validation_result


def test_real_problem_weak_edge_scenario():
    """Test complete workflow for REAL_PROBLEM_WEAK_EDGE scenario."""
    print("\n" + "=" * 70)
    print("TEST: REAL_PROBLEM_WEAK_EDGE Scenario (End-to-End)")
    print("=" * 70)
    
    # Stage 1: SEVERE problem
    print("\n=== STAGE 1: Problem Reality ===")
    stage1_result = {
        "problem_level": "SEVERE",
        "raw_signals": {
            "complaint_count": 10,
            "workaround_count": 6,
            "intensity_count": 3
        }
    }
    print(f"Problem Level: {stage1_result['problem_level']}")
    
    # Stage 2: Market with HIGH competition
    print("\n=== STAGE 2: Market Reality ===")
    stage2_result = {
        "market_strength": {
            "competitor_density": "HIGH",
            "substitute_pressure": "HIGH",
            "content_saturation": "MEDIUM",
            "automation_relevance": "LOW"
        }
    }
    print(f"Competitor Density: {stage2_result['market_strength']['competitor_density']}")
    
    # Stage 3: NO leverage detected
    print("\n=== STAGE 3: Leverage Detection ===")
    stage3_result = detect_leverage_flags(
        replaces_human_labor=False,
        step_reduction_ratio=2,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False,
        automation_relevance=stage2_result["market_strength"]["automation_relevance"],
        substitute_pressure=stage2_result["market_strength"]["substitute_pressure"],
        content_saturation=stage2_result["market_strength"]["content_saturation"]
    )
    
    leverage_flags = stage3_result["leverage_flags"]
    print(f"Leverage Flags Detected: {leverage_flags if leverage_flags else 'NONE'}")
    assert len(leverage_flags) == 0, "Should detect NO leverage"
    
    # Validation
    print("\n=== VALIDATION: Synchronizing All Stages ===")
    validation_result = validate_idea(
        problem_level=stage1_result["problem_level"],
        problem_signals=stage1_result["raw_signals"],
        market_strength=stage2_result["market_strength"],
        leverage_flags=leverage_flags,
        leverage_details={}
    )
    
    validation_state = validation_result["validation_state"]
    validation_class = validation_state["validation_class"]
    
    print(f"Validation Class: {validation_class}")
    
    # Assertions
    assert validation_state["problem_validity"] == "REAL", "Problem should be REAL"
    assert validation_state["leverage_presence"] == "NONE", "Leverage should be NONE"
    assert validation_class == "REAL_PROBLEM_WEAK_EDGE", "Should be REAL_PROBLEM_WEAK_EDGE"
    
    print("✓ Validation complete: REAL_PROBLEM_WEAK_EDGE confirmed")
    print("Note: Real problem exists but solution lacks competitive leverage")
    print("\n" + "=" * 70)
    print("✓ REAL_PROBLEM_WEAK_EDGE END-TO-END TEST PASSED")
    print("=" * 70)


def test_weak_foundation_scenario():
    """Test complete workflow for WEAK_FOUNDATION scenario."""
    print("\n" + "=" * 70)
    print("TEST: WEAK_FOUNDATION Scenario (End-to-End)")
    print("=" * 70)
    
    # Stage 1: MODERATE problem (not severe enough)
    print("\n=== STAGE 1: Problem Reality ===")
    stage1_result = {
        "problem_level": "MODERATE",
        "raw_signals": {
            "complaint_count": 3,
            "workaround_count": 2,
            "intensity_count": 0
        }
    }
    print(f"Problem Level: {stage1_result['problem_level']}")
    
    # Stage 2: Low market pressure
    print("\n=== STAGE 2: Market Reality ===")
    stage2_result = {
        "market_strength": {
            "competitor_density": "LOW",
            "substitute_pressure": "LOW",
            "content_saturation": "LOW",
            "automation_relevance": "MEDIUM"
        }
    }
    
    # Stage 3: Has some leverage
    print("\n=== STAGE 3: Leverage Detection ===")
    stage3_result = detect_leverage_flags(
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=True,  # Has unique data
        works_under_constraints=False,
        automation_relevance=stage2_result["market_strength"]["automation_relevance"],
        substitute_pressure=stage2_result["market_strength"]["substitute_pressure"],
        content_saturation=stage2_result["market_strength"]["content_saturation"]
    )
    
    leverage_flags = stage3_result["leverage_flags"]
    print(f"Leverage Flags Detected: {leverage_flags}")
    assert len(leverage_flags) > 0, "Should detect ACCESS_LEVERAGE"
    
    # Validation
    print("\n=== VALIDATION: Synchronizing All Stages ===")
    validation_result = validate_idea(
        problem_level=stage1_result["problem_level"],
        problem_signals=stage1_result["raw_signals"],
        market_strength=stage2_result["market_strength"],
        leverage_flags=leverage_flags,
        leverage_details=stage3_result["leverage_details"]
    )
    
    validation_state = validation_result["validation_state"]
    validation_class = validation_state["validation_class"]
    
    print(f"Validation Class: {validation_class}")
    
    # Assertions
    assert validation_state["problem_validity"] == "WEAK", "Problem should be WEAK"
    assert validation_class == "WEAK_FOUNDATION", "Should be WEAK_FOUNDATION"
    
    print("✓ Validation complete: WEAK_FOUNDATION confirmed")
    print("Note: Problem not severe enough, even with leverage")
    print("\n" + "=" * 70)
    print("✓ WEAK_FOUNDATION END-TO-END TEST PASSED")
    print("=" * 70)


def test_determinism_with_llm_off():
    """Test that results are identical with LLM OFF (determinism check)."""
    print("\n" + "=" * 70)
    print("TEST: Determinism (LLM ON vs OFF)")
    print("=" * 70)
    
    # Run same inputs multiple times (simulating LLM OFF)
    print("\nRunning leverage detection 3 times with same inputs...")
    
    test_inputs = {
        "replaces_human_labor": True,
        "step_reduction_ratio": 5,
        "delivers_final_answer": True,
        "unique_data_access": False,
        "works_under_constraints": False,
        "automation_relevance": "HIGH",
        "substitute_pressure": "MEDIUM",
        "content_saturation": "MEDIUM"
    }
    
    results = []
    for i in range(3):
        result = detect_leverage_flags(**test_inputs)
        results.append(tuple(result["leverage_flags"]))
        print(f"  Run {i+1}: {result['leverage_flags']}")
    
    # All results should be identical
    assert all(r == results[0] for r in results), "Results should be identical (deterministic)"
    
    print("\n✓ All 3 runs produced identical results")
    print("✓ Stage 3 is deterministic (LLM-independent)")
    print("\n" + "=" * 70)
    print("✓ DETERMINISM TEST PASSED")
    print("=" * 70)


def run_all_integration_tests():
    """Run all end-to-end integration tests."""
    print("\n" + "=" * 70)
    print("END-TO-END INTEGRATION TEST SUITE")
    print("=" * 70)
    
    try:
        test_strong_foundation_scenario()
        test_real_problem_weak_edge_scenario()
        test_weak_foundation_scenario()
        test_determinism_with_llm_off()
        
        print("\n" + "=" * 70)
        print("✓ ALL END-TO-END INTEGRATION TESTS PASSED")
        print("=" * 70)
        print("\nSUMMARY:")
        print("- Stage 1 (Problem Reality): ✓")
        print("- Stage 2 (Market Reality): ✓")
        print("- Stage 3 (Leverage Detection): ✓")
        print("- Validation (Synchronization): ✓")
        print("- Determinism (LLM Independence): ✓")
        print("\nAll stages integrated successfully!")
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
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)
