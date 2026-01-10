"""
Explanation Layer - LLM Narration of Deterministic Outputs

This module implements safe LLM-based explanation of validation results.

CRITICAL RULES:
- LLM explains ONLY what is given
- LLM does NOT add advice
- LLM does NOT add new facts
- LLM does NOT judge the startup
- LLM does NOT suggest what to build
- Explanation does NOT affect downstream logic
"""

from typing import Dict, Any
import logging
from llm_factory import get_llm_client

logger = logging.getLogger(__name__)


# ============================================================================
# EXPLANATION GENERATION
# ============================================================================

def generate_explanation(
    problem_reality: Dict[str, Any],
    market_reality: Dict[str, Any],
    leverage_reality: Dict[str, Any],
    validation_state: Dict[str, Any],
    use_llm: bool = True
) -> str:
    """
    Generate human-readable explanation of deterministic outputs.
    
    INPUT TO LLM (READ-ONLY):
    - Stage 1 output (problem reality)
    - Stage 2 output (market reality)
    - Stage 3 output (leverage flags)
    - Validation result
    
    LLM CONSTRAINTS (enforced in prompt):
    - Explain only what is given
    - Do NOT add advice
    - Do NOT add new facts
    - Do NOT judge the startup
    - Do NOT suggest what to build
    
    OUTPUT:
    Human-readable explanation of:
    - Problem reality
    - Market context
    - Leverage presence or absence
    - Validation class
    
    The explanation MUST NOT affect any downstream logic.
    
    Args:
        problem_reality: Stage 1 output
        market_reality: Stage 2 output
        leverage_reality: Stage 3 output
        validation_state: Validation result
        use_llm: Whether to use LLM (True) or stub (False)
        
    Returns:
        Human-readable explanation string
    """
    # Build context for LLM
    context = {
        "stage_1_problem": problem_reality,
        "stage_2_market": market_reality,
        "stage_3_leverage": leverage_reality,
        "validation": validation_state
    }
    
    if not use_llm:
        logger.info("LLM disabled, using deterministic explanation")
        return generate_deterministic_explanation(
            problem_reality,
            market_reality,
            leverage_reality,
            validation_state
        )
    
    try:
        # Get LLM client
        llm = get_llm_client()
        
        # Generate explanation
        explanation = llm.explain(context)
        
        logger.info("LLM explanation generated successfully")
        
        return explanation
    
    except Exception as e:
        logger.warning(f"LLM explanation failed: {e}, using deterministic fallback")
        
        # Fallback to deterministic explanation
        return generate_deterministic_explanation(
            problem_reality,
            market_reality,
            leverage_reality,
            validation_state
        )


def generate_deterministic_explanation(
    problem_reality: Dict[str, Any],
    market_reality: Dict[str, Any],
    leverage_reality: Dict[str, Any],
    validation_state: Dict[str, Any]
) -> str:
    """
    Generate deterministic (template-based) explanation.
    
    This is used when LLM is disabled or fails.
    
    Args:
        problem_reality: Stage 1 output
        market_reality: Stage 2 output
        leverage_reality: Stage 3 output
        validation_state: Validation result
        
    Returns:
        Template-based explanation string
    """
    # Extract key values
    problem_level = problem_reality.get("problem_level", "UNKNOWN")
    leverage_flags = leverage_reality.get("leverage_flags", [])
    validation_class = validation_state.get("validation_class", "UNKNOWN")
    problem_validity = validation_state.get("problem_validity", "UNKNOWN")
    leverage_presence = validation_state.get("leverage_presence", "UNKNOWN")
    
    # Build explanation sections
    sections = []
    
    # Section 1: Problem Reality
    sections.append("## Problem Reality")
    sections.append(f"Problem Level: {problem_level}")
    sections.append(f"Problem Validity: {problem_validity}")
    
    if problem_level in ["DRASTIC", "SEVERE"]:
        sections.append(
            "The problem shows strong signals of severity, indicating "
            "significant pain or frustration among users."
        )
    else:
        sections.append(
            "The problem shows limited signals of severity. Market validation "
            "may require deeper investigation."
        )
    
    # Section 2: Market Context (if available)
    if market_reality:
        sections.append("\n## Market Context")
        modality = market_reality.get("solution_modality", "UNKNOWN")
        sections.append(f"Solution Modality: {modality}")
        
        market_strength = market_reality.get("market_strength", {})
        if market_strength:
            sections.append("\nMarket Strength Parameters:")
            for key, value in market_strength.items():
                sections.append(f"- {key}: {value}")
        
        sections.append(
            "\nNote: Market parameters are contextual and do not affect "
            "the validation classification."
        )
    
    # Section 3: Leverage Reality
    sections.append("\n## Leverage Reality")
    sections.append(f"Leverage Presence: {leverage_presence}")
    
    if leverage_flags:
        sections.append(f"\n{len(leverage_flags)} leverage advantage(s) detected:")
        for flag in leverage_flags:
            name = flag.get("name", "UNKNOWN")
            reason = flag.get("reason", "No reason provided")
            sections.append(f"- {name}: {reason}")
    else:
        sections.append(
            "\nNo significant leverage advantages detected. "
            "Competitive differentiation may be limited."
        )
    
    # Section 4: Validation Result
    sections.append("\n## Validation Result")
    sections.append(f"Classification: {validation_class}")
    sections.append(f"\n{validation_state.get('reasoning', 'No reasoning provided')}")
    
    # Join all sections
    explanation = "\n".join(sections)
    
    return explanation


# ============================================================================
# SAFETY CHECKS
# ============================================================================

def validate_explanation_safety(explanation: str) -> bool:
    """
    Validate that LLM explanation doesn't contain unsafe content.
    
    SAFETY CHECKS:
    1. No advice or recommendations
    2. No judgments about startup viability
    3. No suggestions about what to build
    
    This is a basic safety check. More sophisticated checks could be added.
    
    Args:
        explanation: Generated explanation text
        
    Returns:
        True if safe, False if potentially unsafe
    """
    # Check for advice/recommendation keywords
    unsafe_keywords = [
        "you should",
        "i recommend",
        "my advice",
        "consider building",
        "pivot to",
        "don't build",
        "avoid building"
    ]
    
    explanation_lower = explanation.lower()
    
    for keyword in unsafe_keywords:
        if keyword in explanation_lower:
            logger.warning(f"Unsafe content detected in explanation: '{keyword}'")
            return False
    
    return True
