"""
Deep analysis of RELATIVE RATIO issues in problem severity classification.

The user suspects that relative ratios (not absolute counts) may cause
unintended behavior. This test focuses on the scoring system.
"""

import sys
from main import classify_problem_level


def test_score_ratio_dependency():
    """
    Test if problem level depends on RELATIVE ratios or ABSOLUTE thresholds.
    
    POTENTIAL ISSUE: The scoring system uses weights:
    - intensity_count * 3
    - complaint_count * 2
    - workaround_count * 1
    
    This means the RATIO between these counts affects the final level,
    not just the absolute totals.
    """
    print("=" * 80)
    print("TEST: Score Calculation - Ratio Dependency Analysis")
    print("=" * 80)
    
    # Test cases with same TOTAL signal count but different DISTRIBUTIONS
    test_cases = [
        {
            'name': 'Balanced distribution',
            'signals': {'intensity_count': 2, 'complaint_count': 2, 'workaround_count': 2},
            'total': 6,
        },
        {
            'name': 'Intensity-heavy',
            'signals': {'intensity_count': 4, 'complaint_count': 1, 'workaround_count': 1},
            'total': 6,
        },
        {
            'name': 'Workaround-heavy',
            'signals': {'intensity_count': 1, 'complaint_count': 1, 'workaround_count': 4},
            'total': 6,
        },
        {
            'name': 'Complaint-heavy',
            'signals': {'intensity_count': 1, 'complaint_count': 4, 'workaround_count': 1},
            'total': 6,
        },
    ]
    
    print("\n🔍 Testing cases with SAME TOTAL (6 signals) but DIFFERENT RATIOS:\n")
    
    results = []
    for case in test_cases:
        level = classify_problem_level(case['signals'])
        score = (
            3 * case['signals']['intensity_count'] +
            2 * case['signals']['complaint_count'] +
            1 * case['signals']['workaround_count']
        )
        results.append((case['name'], level, score))
        
        print(f"{case['name']:25s}: {case['signals']}")
        print(f"  → Level: {level:10s} (score: {score})")
    
    # Check if all same
    levels = [r[1] for r in results]
    scores = [r[2] for r in results]
    
    print("\n" + "-" * 80)
    if len(set(levels)) == 1:
        print("✓ All cases have SAME level despite different ratios")
        print("  (Unlikely - scoring uses weights)")
    else:
        print("✗ INVARIANT VIOLATED: Different ratios produce different levels!")
        print(f"  Levels: {set(levels)}")
        print(f"  Scores: {set(scores)}")
        print("\n  🚨 ISSUE: Same total signal count produces different severity levels")
        print("     depending on signal TYPE ratio, not just absolute counts.")
        return False
    
    return True


def test_absolute_vs_relative():
    """
    Test if two problems with different absolute counts but same RATIOS
    produce proportional severity levels.
    
    INVARIANT QUESTION: Should severity scale with absolute counts,
    or with signal ratios?
    """
    print("\n" + "=" * 80)
    print("TEST: Absolute Counts vs Relative Ratios")
    print("=" * 80)
    
    # Test: 2x the signals with same ratio
    case_a = {'intensity_count': 2, 'complaint_count': 4, 'workaround_count': 2}
    case_b = {'intensity_count': 4, 'complaint_count': 8, 'workaround_count': 4}
    
    level_a = classify_problem_level(case_a)
    level_b = classify_problem_level(case_b)
    
    score_a = 3 * 2 + 2 * 4 + 1 * 2
    score_b = 3 * 4 + 2 * 8 + 1 * 4
    
    print(f"\nCase A: {case_a}")
    print(f"  → Level: {level_a} (score: {score_a})")
    
    print(f"\nCase B (2x counts, same ratio): {case_b}")
    print(f"  → Level: {level_b} (score: {score_b})")
    
    print("\n" + "-" * 80)
    if level_a == level_b:
        print("⚠ SAME level despite 2x absolute counts!")
        print("  This means severity depends on SCORE THRESHOLDS, not signal counts.")
    else:
        print("✓ Different levels: Severity scales with absolute counts")


def test_boundary_ratio_effects():
    """
    Test if crossing score thresholds depends on signal ratios.
    
    The system has thresholds:
    - score >= 15: DRASTIC
    - score >= 8: SEVERE
    - score >= 4: MODERATE
    - score < 4: LOW
    
    Different signal ratios can reach same score with different total counts.
    """
    print("\n" + "=" * 80)
    print("TEST: Boundary Crossing - Ratio Effects")
    print("=" * 80)
    
    # Ways to reach score = 8 (SEVERE threshold)
    ways_to_score_8 = [
        {'intensity_count': 2, 'complaint_count': 1, 'workaround_count': 0},  # 6+2+0=8
        {'intensity_count': 1, 'complaint_count': 2, 'workaround_count': 2},  # 3+4+2=9 (close)
        {'intensity_count': 0, 'complaint_count': 4, 'workaround_count': 0},  # 0+8+0=8
        {'intensity_count': 0, 'complaint_count': 3, 'workaround_count': 2},  # 0+6+2=8
        {'intensity_count': 0, 'complaint_count': 2, 'workaround_count': 4},  # 0+4+4=8
    ]
    
    print("\n🔍 Different ways to reach score ≈ 8 (SEVERE threshold):\n")
    
    for i, signals in enumerate(ways_to_score_8, 1):
        level = classify_problem_level(signals)
        score = (
            3 * signals['intensity_count'] +
            2 * signals['complaint_count'] +
            1 * signals['workaround_count']
        )
        total = sum(signals.values())
        
        print(f"Way {i}: {signals}")
        print(f"  Total signals: {total}, Score: {score}, Level: {level}")
    
    print("\n" + "-" * 80)
    print("⚠ OBSERVATION: Same score can be reached with different total signal counts")
    print("  depending on the signal type RATIO.")
    print("\n  Example: 2 intensity + 1 complaint (3 total) = 8 points = SEVERE")
    print("           0 intensity + 4 complaint (4 total) = 8 points = SEVERE")
    print("\n  🚨 ISSUE: Problem with fewer total signals can be rated HIGHER")
    print("     than problem with more signals, if ratio favors intensity.")


def test_workaround_cap_ratio_effect():
    """
    Test the workaround cap guardrail.
    
    The system caps workarounds at 3 when intensity=0 and complaints<=1.
    This affects the RELATIVE contribution of workarounds to the score.
    """
    print("\n" + "=" * 80)
    print("TEST: Workaround Cap - Ratio Guardrail")
    print("=" * 80)
    
    # Test cases where cap applies
    test_cases = [
        {
            'name': 'No cap (intensity > 0)',
            'signals': {'intensity_count': 1, 'complaint_count': 1, 'workaround_count': 10},
            'cap_applies': False,
        },
        {
            'name': 'Cap applies (intensity=0, complaints=1)',
            'signals': {'intensity_count': 0, 'complaint_count': 1, 'workaround_count': 10},
            'cap_applies': True,
        },
        {
            'name': 'Cap applies (intensity=0, complaints=0)',
            'signals': {'intensity_count': 0, 'complaint_count': 0, 'workaround_count': 10},
            'cap_applies': True,
        },
    ]
    
    print("\n🔍 Testing workaround cap (max 3 when intensity=0 and complaints<=1):\n")
    
    for case in test_cases:
        level = classify_problem_level(case['signals'])
        
        # Calculate effective workaround count
        effective_workaround = case['signals']['workaround_count']
        if case['cap_applies']:
            effective_workaround = min(effective_workaround, 3)
        
        score = (
            3 * case['signals']['intensity_count'] +
            2 * case['signals']['complaint_count'] +
            1 * effective_workaround
        )
        
        print(f"{case['name']}")
        print(f"  Signals: {case['signals']}")
        print(f"  Effective workaround: {effective_workaround} (cap: {case['cap_applies']})")
        print(f"  Score: {score}, Level: {level}")
    
    print("\n" + "-" * 80)
    print("⚠ OBSERVATION: Workaround cap is RATIO-DEPENDENT")
    print("  It only applies when intensity:complaint ratio is very low.")
    print("\n  🚨 ISSUE: Two problems with same workaround count can be scored")
    print("     differently based on intensity/complaint RATIO, not absolute values.")


def run_all_tests():
    """Run all ratio-dependency tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "RELATIVE RATIO DEPENDENCY ANALYSIS" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    try:
        test_score_ratio_dependency()
        test_absolute_vs_relative()
        test_boundary_ratio_effects()
        test_workaround_cap_ratio_effect()
        
        print("\n" + "=" * 80)
        print("FINDINGS")
        print("=" * 80)
        print("\n🚨 CRITICAL ISSUES IDENTIFIED:")
        print("\n1. Problem severity depends on SIGNAL TYPE RATIOS, not just totals")
        print("   - Same total signals → different levels based on intensity:complaint:workaround ratio")
        print("\n2. Score thresholds create RATIO-DEPENDENT boundaries")
        print("   - Fewer signals with high intensity > more signals with low intensity")
        print("\n3. Workaround cap is RATIO-CONDITIONAL")
        print("   - Applies only when intensity=0 AND complaints<=1")
        print("   - Same workaround count scored differently based on other signal ratios")
        print("\n4. No ABSOLUTE invariants on signal counts")
        print("   - System uses weighted scoring, so ratios matter more than totals")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        print("\nThe current system is RATIO-DEPENDENT by design (weighted scoring).")
        print("This may be intentional, but creates cross-domain variability.")
        print("\nConsider adding ABSOLUTE invariants like:")
        print("  - Minimum total signal threshold for each severity level")
        print("  - Maximum severity level based on total signals, regardless of ratio")
        print("  - Absolute caps/floors that apply universally, not conditionally")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
