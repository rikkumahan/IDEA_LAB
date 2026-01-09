"""
Test suite for severity classification guardrails.

Tests for:
- ISSUE 1: SEVERE requires intensity_count >= 1
- ISSUE 2: Workaround cap when intensity/complaints are minimal
- ISSUE 4: Zero signals should always be LOW
"""

import sys
from main import classify_problem_level, normalize_signals


def test_zero_signals_guardrail():
    """
    ISSUE 4: Zero signals of all types should always be LOW
    
    GUARDRAIL:
    - If all signal counts == 0, return LOW immediately
    
    TEST:
    - Verify zero signals → LOW
    - Verify this is an early exit (defensive programming)
    """
    print("Testing ISSUE 4: Zero signals guardrail...")
    
    # Test case 1: All zeros
    signals1 = {'intensity_count': 0, 'complaint_count': 0, 'workaround_count': 0}
    problem_level1 = classify_problem_level(signals1)
    assert problem_level1 == "LOW", \
        f"Zero signals should always be LOW, got {problem_level1}"
    
    print("✓ ISSUE 4 tests passed")


def test_severe_intensity_guardrail():
    """
    ISSUE 1: SEVERE requires intensity_count >= 1
    
    GUARDRAIL:
    - If score >= 8 but intensity_count == 0, downgrade to MODERATE
    
    TEST:
    - Verify SEVERE with intensity=0 is downgraded
    - Verify SEVERE with intensity>=1 is preserved
    """
    print("\nTesting ISSUE 1: SEVERE requires intensity_count >= 1...")
    
    # Test case 1: Score=8 from complaints only (intensity=0)
    # NOTE: With invariants, 4 total signals:
    # - Floor: < 6 for SEVERE → downgrade to MODERATE
    # - Ceiling: 3-5 signals → MODERATE max
    # - Result: MODERATE (not LOW, as 4 signals meets MODERATE threshold of >= 3)
    signals1 = {'intensity_count': 0, 'complaint_count': 4, 'workaround_count': 0}
    problem_level1 = classify_problem_level(signals1)
    score1 = 3*0 + 2*4 + 1*0
    
    assert score1 == 8, f"Score should be 8, got {score1}"
    # Updated: With invariants, 4 total signals allows MODERATE (>= 3 floor, 3-5 ceiling)
    assert problem_level1 == "MODERATE", \
        f"Score=8 with intensity=0 and 4 total signals should be MODERATE (invariant allows), got {problem_level1}"
    
    # Test case 2: Score=8 from complaints+workarounds (intensity=0) with >= 6 total
    signals2 = {'intensity_count': 0, 'complaint_count': 4, 'workaround_count': 2}
    problem_level2 = classify_problem_level(signals2)
    score2 = 3*0 + 2*4 + 1*2
    
    assert score2 == 10, f"Score should be 10, got {score2}"
    # Updated: With 6 total signals and intensity=0, SEVERE guardrail downgrades to MODERATE
    assert problem_level2 == "MODERATE", \
        f"Score=10 with intensity=0 and 6 total signals should be MODERATE, got {problem_level2}"
    
    # Test case 3: Score=8 with intensity>=1 should remain SEVERE (if total >= 6)
    signals3 = {'intensity_count': 1, 'complaint_count': 3, 'workaround_count': 2}
    problem_level3 = classify_problem_level(signals3)
    score3 = 3*1 + 2*3 + 1*2
    
    assert score3 == 11, f"Score should be 11, got {score3}"
    # Updated: With 6 total signals and intensity >= 1, SEVERE is allowed
    assert problem_level3 == "SEVERE", \
        f"Score=11 with intensity>=1 and 6 total signals should be SEVERE, got {problem_level3}"
    
    # Test case 4: Score=11 with intensity=0 and >= 6 total
    signals4 = {'intensity_count': 0, 'complaint_count': 5, 'workaround_count': 1}
    problem_level4 = classify_problem_level(signals4)
    score4 = 3*0 + 2*5 + 1*1
    
    assert score4 == 11, f"Score should be 11, got {score4}"
    assert problem_level4 == "MODERATE", \
        f"Score=11 with intensity=0 should be MODERATE, got {problem_level4}"
    
    # Test case 5: Edge case - Score=7 with intensity=0 should be MODERATE anyway
    signals5 = {'intensity_count': 0, 'complaint_count': 3, 'workaround_count': 1}
    problem_level5 = classify_problem_level(signals5)
    score5 = 3*0 + 2*3 + 1*1
    
    assert score5 == 7, f"Score should be 7, got {score5}"
    assert problem_level5 == "MODERATE", \
        f"Score=7 should be MODERATE, got {problem_level5}"
    
    print("✓ ISSUE 1 tests passed")


def test_workaround_cap_guardrail():
    """
    ISSUE 2: Workaround absolute cap (INVARIANT)
    
    UPDATED GUARDRAIL:
    - Workaround cap is now ABSOLUTE at 5 (unconditional)
    - Replaces old conditional cap (intensity=0 AND complaints<=1 → cap at 3)
    
    TEST:
    - Verify absolute cap applies to all cases
    - Verify cap is unconditional (doesn't depend on intensity/complaint ratios)
    """
    print("\nTesting ISSUE 2: Workaround absolute cap (INVARIANT)...")
    
    # Test case 1: intensity=0, complaints=0, high workarounds → absolute cap at 5
    signals1 = {'intensity_count': 0, 'complaint_count': 0, 'workaround_count': 8}
    problem_level1 = classify_problem_level(signals1)
    # With absolute cap: effective_workaround = 5
    # score = 3*0 + 2*0 + 1*5 = 5 → MODERATE (not LOW as with old cap=3)
    
    assert problem_level1 == "MODERATE", \
        f"Workaround-only (count=8) with absolute cap=5 should be MODERATE, got {problem_level1}"
    
    # Test case 2: intensity=0, complaints=1, high workarounds → absolute cap at 5
    signals2 = {'intensity_count': 0, 'complaint_count': 1, 'workaround_count': 10}
    problem_level2 = classify_problem_level(signals2)
    # With absolute cap: effective_workaround = 5
    # score = 3*0 + 2*1 + 1*5 = 7 → MODERATE
    
    assert problem_level2 == "MODERATE", \
        f"Capped workarounds (10→5) + 1 complaint should be MODERATE, got {problem_level2}"
    
    # Test case 3: intensity=1, complaints=0, high workarounds → STILL capped at 5 (unconditional)
    signals3 = {'intensity_count': 1, 'complaint_count': 0, 'workaround_count': 10}
    problem_level3 = classify_problem_level(signals3)
    # Absolute cap applies even with intensity>0: effective_workaround = 5
    # score = 3*1 + 2*0 + 1*5 = 8 → SEVERE
    
    assert problem_level3 == "SEVERE", \
        f"Capped workarounds (10→5) + intensity=1 should be SEVERE, got {problem_level3}"
    
    # Test case 4: intensity=0, complaints=2, high workarounds → STILL capped at 5 (unconditional)
    signals4 = {'intensity_count': 0, 'complaint_count': 2, 'workaround_count': 10}
    problem_level4 = classify_problem_level(signals4)
    # Absolute cap applies: effective_workaround = 5
    # score = 3*0 + 2*2 + 1*5 = 9 → SEVERE, but SEVERE guardrail downgrades to MODERATE
    
    assert problem_level4 == "MODERATE", \
        f"NO workaround cap when complaints>1, but SEVERE guardrail applies, got {problem_level4}"
    
    # Test case 5: Edge case - workaround_count <= 3, cap doesn't matter
    signals5 = {'intensity_count': 0, 'complaint_count': 0, 'workaround_count': 2}
    problem_level5 = classify_problem_level(signals5)
    # score = 3*0 + 2*0 + 1*2 = 2 → LOW
    
    assert problem_level5 == "LOW", \
        f"Workaround count=2 (no cap needed) should be LOW, got {problem_level5}"
    
    # Test case 6: Exactly at cap boundary (workaround_count=3)
    signals6 = {'intensity_count': 0, 'complaint_count': 0, 'workaround_count': 3}
    problem_level6 = classify_problem_level(signals6)
    # score = 3*0 + 2*0 + 1*3 = 3 → LOW
    
    assert problem_level6 == "LOW", \
        f"Workaround count=3 should be LOW, got {problem_level6}"
    
    print("✓ ISSUE 2 tests passed")


def test_guardrail_interactions():
    """
    Test interactions between multiple guardrails
    
    Scenarios:
    1. DRASTIC guardrail + SEVERE guardrail
    2. Workaround cap + SEVERE guardrail
    3. All guardrails inactive (normal path)
    """
    print("\nTesting guardrail interactions...")
    
    # Test case 1: DRASTIC downgrade + SEVERE downgrade
    # Score >= 15, intensity_level=MEDIUM, intensity_count > 0
    signals1 = {'intensity_count': 2, 'complaint_count': 5, 'workaround_count': 5}
    problem_level1 = classify_problem_level(signals1)
    normalized1 = normalize_signals(signals1)
    score1 = 3*2 + 2*5 + 1*5
    
    assert score1 == 21, f"Score should be 21, got {score1}"
    assert normalized1['intensity_level'] == "MEDIUM"
    # DRASTIC guardrail: intensity_level != HIGH → downgrade to SEVERE
    # SEVERE guardrail: intensity_count > 0 → no further downgrade
    assert problem_level1 == "SEVERE", \
        f"Should be SEVERE after DRASTIC downgrade (no SEVERE downgrade needed), got {problem_level1}"
    
    # Test case 2: Workaround cap brings score below SEVERE threshold
    signals2 = {'intensity_count': 0, 'complaint_count': 1, 'workaround_count': 10}
    problem_level2 = classify_problem_level(signals2)
    # With cap: effective_workaround = 3
    # score = 3*0 + 2*1 + 1*3 = 5 → MODERATE
    # SEVERE guardrail doesn't apply (score < 8)
    
    assert problem_level2 == "MODERATE", \
        f"Workaround cap should prevent SEVERE, got {problem_level2}"
    
    # Test case 3: Normal path - no guardrails triggered
    signals3 = {'intensity_count': 3, 'complaint_count': 3, 'workaround_count': 2}
    problem_level3 = classify_problem_level(signals3)
    score3 = 3*3 + 2*3 + 1*2
    
    assert score3 == 17, f"Score should be 17, got {score3}"
    # intensity_count=3 → intensity_level=MEDIUM
    # DRASTIC guardrail: intensity_level != HIGH → downgrade to SEVERE
    assert problem_level3 == "SEVERE", \
        f"Normal SEVERE path (after DRASTIC downgrade), got {problem_level3}"
    
    # Test case 4: HIGH intensity, high score → DRASTIC (no downgrade)
    # UPDATED: With invariants, DRASTIC requires >= 7 intensity (not just 5 for level=HIGH)
    signals4 = {'intensity_count': 7, 'complaint_count': 5, 'workaround_count': 5}
    problem_level4 = classify_problem_level(signals4)
    normalized4 = normalize_signals(signals4)
    
    assert normalized4['intensity_level'] == "HIGH"
    # Updated: Need >=7 intensity + >=10 total + >=20 total for DRASTIC ceiling
    # With 17 total, ceiling caps at SEVERE
    assert problem_level4 == "SEVERE", \
        f"HIGH intensity but < 20 total should be SEVERE (ceiling), got {problem_level4}"
    
    print("✓ Guardrail interaction tests passed")


def test_edge_cases():
    """
    Test edge cases and boundary conditions
    """
    print("\nTesting edge cases...")
    
    # Test case 1: Exactly at MODERATE threshold (score=4) with >= 3 total
    # UPDATED: With invariants, MODERATE requires >= 3 total signals
    signals1 = {'intensity_count': 1, 'complaint_count': 1, 'workaround_count': 1}
    problem_level1 = classify_problem_level(signals1)
    score1 = 3*1 + 2*1 + 1*1
    
    assert score1 == 6, f"Score should be 6, got {score1}"
    # With 3 total signals and score >= 4, MODERATE is allowed
    assert problem_level1 == "MODERATE", \
        f"Score={score1} with 3 total should be MODERATE, got {problem_level1}"
    
    # Test case 2: Just below MODERATE threshold (score=3) with < 3 total
    # UPDATED: With < 3 total, ceiling caps at LOW
    signals2 = {'intensity_count': 1, 'complaint_count': 0, 'workaround_count': 0}
    problem_level2 = classify_problem_level(signals2)
    score2 = 3*1 + 2*0 + 1*0
    
    assert score2 == 3, f"Score should be 3, got {score2}"
    # With 1 total signal (< 3), ceiling caps at LOW
    assert problem_level2 == "LOW", \
        f"Score=3 with 1 total signal should be LOW (ceiling), got {problem_level2}"
    
    # Test case 3: Exactly at SEVERE threshold after SEVERE guardrail
    # Need score=8 with intensity=0 to test SEVERE guardrail activation
    signals3 = {'intensity_count': 0, 'complaint_count': 4, 'workaround_count': 0}
    problem_level3 = classify_problem_level(signals3)
    score3 = 3*0 + 2*4 + 1*0
    
    assert score3 == 8, f"Score should be 8, got {score3}"
    assert problem_level3 == "MODERATE", \
        f"Score=8 with intensity=0 should be downgraded to MODERATE, got {problem_level3}"
    
    # Test case 4: Maximum counts without triggering DRASTIC
    signals4 = {'intensity_count': 4, 'complaint_count': 10, 'workaround_count': 10}
    problem_level4 = classify_problem_level(signals4)
    normalized4 = normalize_signals(signals4)
    score4 = 3*4 + 2*10 + 1*10
    
    assert score4 == 42, f"Score should be 42, got {score4}"
    assert normalized4['intensity_level'] == "MEDIUM"
    # DRASTIC guardrail: intensity_level != HIGH → downgrade to SEVERE
    assert problem_level4 == "SEVERE", \
        f"High score with MEDIUM intensity should be SEVERE (after downgrade), got {problem_level4}"
    
    print("✓ Edge case tests passed")


def test_assertions():
    """
    Test that assertions in classify_problem_level are working
    """
    print("\nTesting assertions...")
    
    # Test case 1: Verify DRASTIC assertion still works
    # UPDATED: With invariants, DRASTIC requires >= 7 intensity AND >= 20 total
    signals1 = {'intensity_count': 10, 'complaint_count': 10, 'workaround_count': 5}
    try:
        level1 = classify_problem_level(signals1)
        assert level1 == "DRASTIC", f"Should be DRASTIC with HIGH intensity and >= 20 total, got {level1}"
    except AssertionError as e:
        if "DRASTIC problem level requires HIGH intensity_level" in str(e):
            assert False, "Assertion should not fail for valid DRASTIC case"
        raise
    
    # Test case 2: Verify SEVERE assertion (if added)
    # The guardrail should prevent intensity=0 from reaching SEVERE
    signals2 = {'intensity_count': 0, 'complaint_count': 4, 'workaround_count': 0}
    level2 = classify_problem_level(signals2)
    assert level2 == "MODERATE", "Should be downgraded to MODERATE"
    
    print("✓ Assertion tests passed")


def run_all_tests():
    """Run all severity guardrail test suites"""
    print("=" * 60)
    print("Running Severity Guardrail Test Suite")
    print("=" * 60)
    
    try:
        test_zero_signals_guardrail()
        test_severe_intensity_guardrail()
        test_workaround_cap_guardrail()
        test_guardrail_interactions()
        test_edge_cases()
        test_assertions()
        
        print("\n" + "=" * 60)
        print("✓ ALL SEVERITY GUARDRAIL TESTS PASSED!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
