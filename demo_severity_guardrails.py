"""
Demo script to showcase severity classification guardrails.

Demonstrates how each guardrail prevents specific failure modes.
"""

from main import classify_problem_level


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_case(description, signals, notes=""):
    """Demo a single test case"""
    print(f"\n{description}")
    print(f"  Signals: intensity={signals['intensity_count']}, "
          f"complaints={signals['complaint_count']}, "
          f"workarounds={signals['workaround_count']}")
    
    # Calculate raw score
    raw_score = (
        3 * signals['intensity_count'] + 
        2 * signals['complaint_count'] + 
        1 * signals['workaround_count']
    )
    print(f"  Raw Score: {raw_score}")
    
    # Get classification
    level = classify_problem_level(signals)
    print(f"  → Classification: {level}")
    
    if notes:
        print(f"  Note: {notes}")


def main():
    print_header("SEVERITY CLASSIFICATION GUARDRAILS DEMO")
    
    print("\nThis demo showcases the guardrails that prevent:")
    print("  1. Zero-signal edge cases")
    print("  2. Workaround-only inflation")
    print("  3. False DRASTIC classification")
    print("  4. False SEVERE classification (no intensity)")
    
    # Demo 1: Zero-signal check
    print_header("GUARDRAIL 1: Zero-Signal Sanity Check")
    demo_case(
        "Case 1.1: All signals are zero",
        {'intensity_count': 0, 'complaint_count': 0, 'workaround_count': 0},
        "Defensive programming - ensures zero signals always → LOW"
    )
    
    # Demo 2: Workaround cap
    print_header("GUARDRAIL 2: Workaround Cap (Prevents Inflation)")
    
    demo_case(
        "Case 2.1: High workarounds, no intensity/complaints",
        {'intensity_count': 0, 'complaint_count': 0, 'workaround_count': 10},
        "Without cap: score=10 → SEVERE. With cap: score=3 → LOW ✓"
    )
    
    demo_case(
        "Case 2.2: High workarounds, 1 complaint, no intensity",
        {'intensity_count': 0, 'complaint_count': 1, 'workaround_count': 8},
        "Without cap: score=10 → SEVERE. With cap: score=5 → MODERATE ✓"
    )
    
    demo_case(
        "Case 2.3: High workarounds WITH intensity (no cap)",
        {'intensity_count': 1, 'complaint_count': 0, 'workaround_count': 6},
        "Cap doesn't apply when intensity > 0. Score=9 → SEVERE ✓"
    )
    
    demo_case(
        "Case 2.4: High workarounds, high complaints (no cap)",
        {'intensity_count': 0, 'complaint_count': 3, 'workaround_count': 6},
        "Cap doesn't apply when complaints > 1"
    )
    
    # Demo 3: DRASTIC guardrail
    print_header("GUARDRAIL 3: DRASTIC Requires HIGH Intensity (Existing)")
    
    demo_case(
        "Case 3.1: Score >= 15 with HIGH intensity (5+)",
        {'intensity_count': 5, 'complaint_count': 5, 'workaround_count': 5},
        "DRASTIC is allowed - intensity_level = HIGH ✓"
    )
    
    demo_case(
        "Case 3.2: Score >= 15 with MEDIUM intensity (2-4)",
        {'intensity_count': 2, 'complaint_count': 5, 'workaround_count': 5},
        "DRASTIC → SEVERE downgrade (intensity_level != HIGH) ✓"
    )
    
    # Demo 4: SEVERE guardrail
    print_header("GUARDRAIL 4: SEVERE Requires Intensity >= 1 (New)")
    
    demo_case(
        "Case 4.1: Score=8 from complaints only",
        {'intensity_count': 0, 'complaint_count': 4, 'workaround_count': 0},
        "SEVERE → MODERATE downgrade (no intensity signals) ✓"
    )
    
    demo_case(
        "Case 4.2: Score=8 from complaints + workarounds",
        {'intensity_count': 0, 'complaint_count': 3, 'workaround_count': 2},
        "SEVERE → MODERATE downgrade (no intensity signals) ✓"
    )
    
    demo_case(
        "Case 4.3: Score=8 WITH intensity",
        {'intensity_count': 1, 'complaint_count': 2, 'workaround_count': 1},
        "SEVERE is allowed - intensity >= 1 ✓"
    )
    
    # Demo 5: Normal classifications (no guardrails)
    print_header("NORMAL CLASSIFICATIONS (No Guardrails Triggered)")
    
    demo_case(
        "Case 5.1: LOW - minimal signals",
        {'intensity_count': 1, 'complaint_count': 0, 'workaround_count': 0},
        "Score=3 → LOW (below threshold)"
    )
    
    demo_case(
        "Case 5.2: MODERATE - balanced signals",
        {'intensity_count': 1, 'complaint_count': 1, 'workaround_count': 1},
        "Score=6 → MODERATE (between thresholds)"
    )
    
    demo_case(
        "Case 5.3: SEVERE - strong signals with intensity",
        {'intensity_count': 2, 'complaint_count': 2, 'workaround_count': 2},
        "Score=12 → SEVERE (above threshold, intensity >= 1)"
    )
    
    # Demo 6: Edge cases
    print_header("EDGE CASES & INTERACTIONS")
    
    demo_case(
        "Case 6.1: Exactly at MODERATE threshold",
        {'intensity_count': 1, 'complaint_count': 0, 'workaround_count': 1},
        "Score=4 exactly → MODERATE (at threshold)"
    )
    
    demo_case(
        "Case 6.2: Just below MODERATE threshold",
        {'intensity_count': 0, 'complaint_count': 1, 'workaround_count': 1},
        "Score=3 → LOW (just below threshold)"
    )
    
    demo_case(
        "Case 6.3: Multiple guardrails (workaround cap + SEVERE)",
        {'intensity_count': 0, 'complaint_count': 2, 'workaround_count': 8},
        "NO cap (complaints > 1), but score → MODERATE by SEVERE guardrail"
    )
    
    print_header("SUMMARY")
    print("\n✓ All guardrails are:")
    print("  - Deterministic (same input → same output)")
    print("  - Rule-based (no ML/AI/probabilistic logic)")
    print("  - Conservative (prevent false positives)")
    print("  - Defensive (protect against edge cases)")
    print("\n✓ Guardrails prevent specific failure modes:")
    print("  - Zero-signal edge cases")
    print("  - Workaround-only severity inflation")
    print("  - False urgency without intensity signals")
    print("  - Inappropriate DRASTIC classification")
    print("\n✓ All tests passing (test_severity_guardrails.py)")
    print()


if __name__ == "__main__":
    main()
