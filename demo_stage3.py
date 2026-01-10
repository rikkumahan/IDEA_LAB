#!/usr/bin/env python3
"""
Demonstration of Stage 3 & 4 Implementation

This script demonstrates the complete validation pipeline without
requiring network access or API keys.
"""

from stage3_leverage import run_stage3_leverage_detection
from validation import (
    ProblemReality,
    MarketReality,
    LeverageReality,
    validate_startup_idea,
    format_validation_output
)
from explanation_layer import generate_explanation
from questioning_layer import create_questioning_session, CANONICAL_QUESTIONS
from llm_stub import StubLLMClient

def print_section(title):
    """Print a section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def demo_questioning_layer():
    """Demonstrate the questioning layer."""
    print_section("DEMO 1: Questioning Layer")
    
    print("This demonstrates how questions are presented to users.\n")
    
    # Create LLM client (stub for demo)
    llm = StubLLMClient()
    
    # Create questioning session
    session = create_questioning_session(llm, use_llm=False)
    
    # Get questions
    questions = session.get_questions_for_presentation()
    
    print(f"Found {len(questions)} canonical questions:\n")
    
    for i, q in enumerate(questions, 1):
        print(f"{i}. ID: {q['id']}")
        print(f"   Question: {q['question']}")
        print(f"   Answer Type: {q['answer_type']}")
        print()
    
    print("These questions collect structured inputs for Stage 3 leverage detection.")
    print("LLM can adapt wording for clarity, but semantic meaning never changes.")


def demo_leverage_detection():
    """Demonstrate leverage detection."""
    print_section("DEMO 2: Leverage Detection (Stage 3)")
    
    print("This demonstrates deterministic leverage detection.\n")
    
    # Example leverage inputs
    print("INPUT: Leverage characteristics of a solution")
    print("  - Replaces human labor: YES")
    print("  - Steps eliminated: 10")
    print("  - Delivers final answer: YES")
    print("  - Has unique data: YES")
    print("  - Works under constraints: NO")
    print()
    
    leverage_inputs = {
        "replaces_human_labor": True,
        "step_reduction_ratio": 10,
        "delivers_final_answer": True,
        "unique_data_access": True,
        "works_under_constraints": False
    }
    
    # Run Stage 3
    leverage_flags = run_stage3_leverage_detection(leverage_inputs)
    
    print("OUTPUT: Detected leverage flags\n")
    
    present_flags = leverage_flags.get_present_flags()
    
    if present_flags:
        for flag in present_flags:
            print(f"✓ {flag.name}")
            print(f"  Reason: {flag.reason}")
            print()
    else:
        print("No leverage flags detected.")
    
    print(f"Total: {len(present_flags)} leverage advantage(s) detected")
    print("\nThese flags are 100% deterministic - same inputs always produce same flags.")


def demo_validation():
    """Demonstrate complete validation."""
    print_section("DEMO 3: Complete Validation (Stage 4)")
    
    print("This demonstrates the complete validation pipeline.\n")
    
    # Stage 1: Problem Reality (simulated)
    print("STAGE 1: Problem Reality")
    print("  Problem Level: SEVERE")
    print("  (Based on deterministic signal extraction)\n")
    
    problem_reality = ProblemReality(
        problem_level="SEVERE",
        signals={
            "intensity_count": 8,
            "complaint_count": 15,
            "workaround_count": 10
        },
        normalized_signals={
            "intensity_level": "HIGH",
            "complaint_level": "HIGH",
            "workaround_level": "HIGH"
        }
    )
    
    # Stage 2: Market Reality (optional)
    print("STAGE 2: Market Reality (optional)")
    print("  Solution Modality: SOFTWARE")
    print("  Competitor Density: MEDIUM")
    print("  (Market data is contextual only)\n")
    
    market_reality = MarketReality(
        solution_modality="SOFTWARE",
        market_strength={
            "competitor_density": "MEDIUM",
            "market_fragmentation": "FRAGMENTED",
            "substitute_pressure": "LOW",
            "content_saturation": "LOW",
            "solution_class_maturity": "EMERGING",
            "automation_relevance": "HIGH"
        },
        competitors={
            "software": [{"name": "Competitor A", "url": "http://a.com", "pricing_model": "freemium"}],
            "services_expected": False
        }
    )
    
    # Stage 3: Leverage Detection
    print("STAGE 3: Leverage Detection")
    
    leverage_inputs = {
        "replaces_human_labor": True,
        "step_reduction_ratio": 10,
        "delivers_final_answer": True,
        "unique_data_access": True,
        "works_under_constraints": False
    }
    
    leverage_flags = run_stage3_leverage_detection(leverage_inputs)
    
    leverage_reality = LeverageReality(
        leverage_flags=[
            {
                "name": flag.name,
                "present": flag.present,
                "reason": flag.reason
            }
            for flag in leverage_flags.flags
        ]
    )
    
    print(f"  Leverage Flags: {len(leverage_flags.get_present_flags())} detected\n")
    
    # Stage 4: Validation
    print("STAGE 4: Validation")
    
    validation_state = validate_startup_idea(
        problem_reality,
        market_reality,
        leverage_reality
    )
    
    print(f"  Problem Validity: {validation_state.problem_validity.value}")
    print(f"  Leverage Presence: {validation_state.leverage_presence.value}")
    print(f"  Validation Class: {validation_state.validation_class.value}")
    print()
    print(f"  Reasoning: {validation_state.reasoning}")
    
    # Generate output
    output = format_validation_output(
        problem_reality,
        market_reality,
        leverage_reality,
        validation_state
    )
    
    # Generate explanation
    print("\n" + "-"*70)
    print("EXPLANATION (Deterministic):")
    print("-"*70 + "\n")
    
    explanation = generate_explanation(
        output["problem_reality"],
        output["market_reality"],
        output["leverage_reality"],
        output["validation_state"],
        use_llm=False
    )
    
    print(explanation)


def demo_determinism():
    """Demonstrate determinism."""
    print_section("DEMO 4: Determinism Verification")
    
    print("This demonstrates that same inputs always produce same outputs.\n")
    
    leverage_inputs = {
        "replaces_human_labor": True,
        "step_reduction_ratio": 5,
        "delivers_final_answer": True,
        "unique_data_access": False,
        "works_under_constraints": False
    }
    
    print("Running leverage detection 5 times with identical inputs...\n")
    
    results = []
    for i in range(5):
        leverage_flags = run_stage3_leverage_detection(leverage_inputs)
        flag_names = sorted([f.name for f in leverage_flags.flags if f.present])
        results.append(tuple(flag_names))
        print(f"  Run {i+1}: {flag_names}")
    
    # Check if all results are identical
    if len(set(results)) == 1:
        print("\n✓ SUCCESS: All runs produced identical results")
        print("  This proves determinism - same inputs always produce same outputs.")
    else:
        print("\n✗ FAILURE: Results differ (should never happen)")


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("  STAGE 3 & 4 IMPLEMENTATION DEMONSTRATION")
    print("  Deterministic Decision Engine with LLM Language Layer")
    print("="*70)
    
    print("\nThis demo shows the complete implementation WITHOUT requiring:")
    print("  - Network access (no SERPAPI calls)")
    print("  - API keys (uses stub LLM)")
    print("  - External dependencies")
    print("\nAll decision logic is deterministic and verifiable.\n")
    
    input("Press Enter to start...")
    
    demo_questioning_layer()
    input("\nPress Enter to continue...")
    
    demo_leverage_detection()
    input("\nPress Enter to continue...")
    
    demo_validation()
    input("\nPress Enter to continue...")
    
    demo_determinism()
    
    print_section("DEMONSTRATION COMPLETE")
    
    print("Key Takeaways:")
    print("  1. LLM is used ONLY for language (question wording, explanation)")
    print("  2. All decision logic is deterministic (proven by tests)")
    print("  3. Market data is contextual only (doesn't invalidate problems)")
    print("  4. System works identically with LLM disabled")
    print()
    print("Run tests to verify:")
    print("  python test_stage3_validation.py -v")
    print("  python test_offline_pipeline.py -v")
    print()


if __name__ == "__main__":
    main()
