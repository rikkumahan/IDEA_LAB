"""
Regression Test: COST_LEVERAGE Bug Fix

This test validates that COST_LEVERAGE is ONLY triggered when there are
explicit cost advantage signals, not just automation or labor replacement.

BUG FIXED:
- Old behavior: COST_LEVERAGE triggered on replaces_human_labor=True AND automation=HIGH
- New behavior: COST_LEVERAGE requires at least one explicit signal:
  * has_pricing_delta (e.g., "10x cheaper")
  * has_infrastructure_shift (e.g., serverless vs self-hosted)
  * has_distribution_shift (e.g., new channel unavailable to incumbents)
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stage3_leverage import detect_leverage_flags, detect_cost_leverage


def test_automation_without_cost_advantage():
    """
    REGRESSION TEST 1: Automation alone should NOT trigger COST_LEVERAGE.
    
    Scenario: High automation that replaces human labor, but no explicit
    cost advantage through pricing, infrastructure, or distribution.
    
    Expected: COST_LEVERAGE should NOT be flagged.
    """
    print("=" * 70)
    print("REGRESSION TEST: Automation without cost advantage")
    print("=" * 70)
    
    result = detect_leverage_flags(
        # User inputs - high automation, replaces labor
        replaces_human_labor=True,
        step_reduction_ratio=10,
        delivers_final_answer=True,
        unique_data_access=False,
        works_under_constraints=False,
        # NO explicit cost advantage signals
        has_pricing_delta=False,
        has_infrastructure_shift=False,
        has_distribution_shift=False,
        # Market inputs - high automation relevance
        automation_relevance="HIGH",
        substitute_pressure="MEDIUM",
        content_saturation="MEDIUM"
    )
    
    leverage_flags = result.get("leverage_flags", [])
    
    print(f"\nLeverage flags detected: {leverage_flags}")
    
    # ASSERTION: COST_LEVERAGE should NOT be in the flags
    assert "COST_LEVERAGE" not in leverage_flags, (
        "BUG: COST_LEVERAGE triggered without explicit cost advantage signals. "
        "Automation alone does NOT imply cost leverage."
    )
    
    print("✓ PASS: COST_LEVERAGE correctly NOT triggered (no explicit signals)")
    print()


def test_pricing_delta_triggers_cost_leverage():
    """
    REGRESSION TEST 2: Explicit pricing delta should trigger COST_LEVERAGE.
    
    Scenario: Solution has significant pricing advantage (e.g., 10x cheaper).
    
    Expected: COST_LEVERAGE should be flagged.
    """
    print("=" * 70)
    print("REGRESSION TEST: Pricing delta triggers cost leverage")
    print("=" * 70)
    
    result = detect_leverage_flags(
        # User inputs
        replaces_human_labor=False,  # Doesn't even need to replace labor
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False,
        # Explicit pricing advantage
        has_pricing_delta=True,
        has_infrastructure_shift=False,
        has_distribution_shift=False,
        # Market inputs
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW"
    )
    
    leverage_flags = result.get("leverage_flags", [])
    leverage_details = result.get("leverage_details", {})
    
    print(f"\nLeverage flags detected: {leverage_flags}")
    
    # ASSERTION: COST_LEVERAGE should be in the flags
    assert "COST_LEVERAGE" in leverage_flags, (
        "BUG: COST_LEVERAGE not triggered despite explicit pricing advantage"
    )
    
    # Check reason includes pricing_delta
    reason = leverage_details.get("COST_LEVERAGE", {}).get("reason", "")
    assert "pricing advantage" in reason.lower(), (
        f"Reason should mention pricing advantage, got: {reason}"
    )
    
    print(f"✓ PASS: COST_LEVERAGE correctly triggered (pricing advantage)")
    print(f"   Reason: {reason}")
    print()


def test_infrastructure_shift_triggers_cost_leverage():
    """
    REGRESSION TEST 3: Infrastructure shift should trigger COST_LEVERAGE.
    
    Scenario: Solution uses serverless vs competitors' self-hosted architecture.
    
    Expected: COST_LEVERAGE should be flagged.
    """
    print("=" * 70)
    print("REGRESSION TEST: Infrastructure shift triggers cost leverage")
    print("=" * 70)
    
    result = detect_leverage_flags(
        # User inputs
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False,
        # Explicit infrastructure advantage
        has_pricing_delta=False,
        has_infrastructure_shift=True,
        has_distribution_shift=False,
        # Market inputs
        automation_relevance="MEDIUM",
        substitute_pressure="LOW",
        content_saturation="LOW"
    )
    
    leverage_flags = result.get("leverage_flags", [])
    leverage_details = result.get("leverage_details", {})
    
    print(f"\nLeverage flags detected: {leverage_flags}")
    
    # ASSERTION: COST_LEVERAGE should be in the flags
    assert "COST_LEVERAGE" in leverage_flags, (
        "BUG: COST_LEVERAGE not triggered despite infrastructure shift"
    )
    
    # Check reason includes infrastructure_shift
    reason = leverage_details.get("COST_LEVERAGE", {}).get("reason", "")
    assert "infrastructure shift" in reason.lower(), (
        f"Reason should mention infrastructure shift, got: {reason}"
    )
    
    print(f"✓ PASS: COST_LEVERAGE correctly triggered (infrastructure shift)")
    print(f"   Reason: {reason}")
    print()


def test_distribution_shift_triggers_cost_leverage():
    """
    REGRESSION TEST 4: Distribution shift should trigger COST_LEVERAGE.
    
    Scenario: Solution uses unique distribution channel (e.g., Slack integration).
    
    Expected: COST_LEVERAGE should be flagged.
    """
    print("=" * 70)
    print("REGRESSION TEST: Distribution shift triggers cost leverage")
    print("=" * 70)
    
    result = detect_leverage_flags(
        # User inputs
        replaces_human_labor=False,
        step_reduction_ratio=0,
        delivers_final_answer=False,
        unique_data_access=False,
        works_under_constraints=False,
        # Explicit distribution advantage
        has_pricing_delta=False,
        has_infrastructure_shift=False,
        has_distribution_shift=True,
        # Market inputs
        automation_relevance="LOW",
        substitute_pressure="LOW",
        content_saturation="LOW"
    )
    
    leverage_flags = result.get("leverage_flags", [])
    leverage_details = result.get("leverage_details", {})
    
    print(f"\nLeverage flags detected: {leverage_flags}")
    
    # ASSERTION: COST_LEVERAGE should be in the flags
    assert "COST_LEVERAGE" in leverage_flags, (
        "BUG: COST_LEVERAGE not triggered despite distribution shift"
    )
    
    # Check reason includes distribution_shift
    reason = leverage_details.get("COST_LEVERAGE", {}).get("reason", "")
    assert "distribution shift" in reason.lower(), (
        f"Reason should mention distribution shift, got: {reason}"
    )
    
    print(f"✓ PASS: COST_LEVERAGE correctly triggered (distribution shift)")
    print(f"   Reason: {reason}")
    print()


def test_multiple_signals_trigger_cost_leverage():
    """
    REGRESSION TEST 5: Multiple cost signals should trigger COST_LEVERAGE.
    
    Scenario: Solution has both pricing advantage AND infrastructure shift.
    
    Expected: COST_LEVERAGE should be flagged with both signals in reason.
    """
    print("=" * 70)
    print("REGRESSION TEST: Multiple signals trigger cost leverage")
    print("=" * 70)
    
    result = detect_leverage_flags(
        # User inputs
        replaces_human_labor=True,
        step_reduction_ratio=5,
        delivers_final_answer=True,
        unique_data_access=False,
        works_under_constraints=False,
        # Multiple cost advantage signals
        has_pricing_delta=True,
        has_infrastructure_shift=True,
        has_distribution_shift=False,
        # Market inputs
        automation_relevance="HIGH",
        substitute_pressure="MEDIUM",
        content_saturation="HIGH"
    )
    
    leverage_flags = result.get("leverage_flags", [])
    leverage_details = result.get("leverage_details", {})
    
    print(f"\nLeverage flags detected: {leverage_flags}")
    
    # ASSERTION: COST_LEVERAGE should be in the flags
    assert "COST_LEVERAGE" in leverage_flags, (
        "BUG: COST_LEVERAGE not triggered despite multiple signals"
    )
    
    # Check reason mentions both signals
    reason = leverage_details.get("COST_LEVERAGE", {}).get("reason", "")
    assert "pricing advantage" in reason.lower(), (
        f"Reason should mention pricing advantage, got: {reason}"
    )
    assert "infrastructure shift" in reason.lower(), (
        f"Reason should mention infrastructure shift, got: {reason}"
    )
    
    print(f"✓ PASS: COST_LEVERAGE correctly triggered (multiple signals)")
    print(f"   Reason: {reason}")
    print()


def test_cost_leverage_direct():
    """
    REGRESSION TEST 6: Direct test of detect_cost_leverage function.
    """
    print("=" * 70)
    print("REGRESSION TEST: Direct cost leverage detection")
    print("=" * 70)
    
    # Test 1: No signals
    result = detect_cost_leverage(
        has_pricing_delta=False,
        has_infrastructure_shift=False,
        has_distribution_shift=False
    )
    assert result is False, "Should not trigger with no signals"
    print("✓ Test 1: No signals = no cost leverage")
    
    # Test 2: Only pricing delta
    result = detect_cost_leverage(
        has_pricing_delta=True,
        has_infrastructure_shift=False,
        has_distribution_shift=False
    )
    assert result is True, "Should trigger with pricing delta"
    print("✓ Test 2: Pricing delta = cost leverage")
    
    # Test 3: Only infrastructure shift
    result = detect_cost_leverage(
        has_pricing_delta=False,
        has_infrastructure_shift=True,
        has_distribution_shift=False
    )
    assert result is True, "Should trigger with infrastructure shift"
    print("✓ Test 3: Infrastructure shift = cost leverage")
    
    # Test 4: Only distribution shift
    result = detect_cost_leverage(
        has_pricing_delta=False,
        has_infrastructure_shift=False,
        has_distribution_shift=True
    )
    assert result is True, "Should trigger with distribution shift"
    print("✓ Test 4: Distribution shift = cost leverage")
    
    # Test 5: All signals
    result = detect_cost_leverage(
        has_pricing_delta=True,
        has_infrastructure_shift=True,
        has_distribution_shift=True
    )
    assert result is True, "Should trigger with all signals"
    print("✓ Test 5: All signals = cost leverage")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("COST_LEVERAGE BUG FIX - REGRESSION TEST SUITE")
    print("=" * 70)
    print()
    
    try:
        # Run all regression tests
        test_automation_without_cost_advantage()
        test_pricing_delta_triggers_cost_leverage()
        test_infrastructure_shift_triggers_cost_leverage()
        test_distribution_shift_triggers_cost_leverage()
        test_multiple_signals_trigger_cost_leverage()
        test_cost_leverage_direct()
        
        print("=" * 70)
        print("ALL REGRESSION TESTS PASSED ✓")
        print("=" * 70)
        print()
        print("Summary:")
        print("- COST_LEVERAGE now requires explicit cost advantage signals")
        print("- Automation alone does NOT trigger COST_LEVERAGE")
        print("- Pricing, infrastructure, or distribution signals required")
        print()
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
