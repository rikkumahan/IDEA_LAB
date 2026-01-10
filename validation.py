"""
Validation Module: Post-Stage 3 Validation Logic

This module synchronizes Stage 1 (Problem Reality), Stage 2 (Market Reality),
and Stage 3 (Leverage Reality) into a final validation state.

CRITICAL CONSTRAINTS:
- All validation logic is DETERMINISTIC and RULE-BASED
- NO LLM or NLP reasoning
- Market pressure must NOT invalidate problems
- Market data is CONTEXTUAL only

VALIDATION OUTPUT:
{
  "problem_validity": "REAL" | "WEAK",
  "leverage_presence": "PRESENT" | "NONE",
  "validation_class": "STRONG_FOUNDATION" | "REAL_PROBLEM_WEAK_EDGE" | "WEAK_FOUNDATION"
}
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# VALIDATION RULES (DETERMINISTIC)
# ============================================================================

def classify_problem_validity(problem_level: str) -> str:
    """
    Classify problem validity based on Stage 1 problem_level.
    
    RULE:
    - REAL if problem_level >= SEVERE
    - WEAK otherwise (MODERATE, LOW)
    
    This is INDEPENDENT of market data.
    Market pressure does NOT invalidate real problems.
    
    Args:
        problem_level: Problem severity from Stage 1 (DRASTIC, SEVERE, MODERATE, LOW)
        
    Returns:
        "REAL" or "WEAK"
    """
    # Valid problem levels (from Stage 1)
    valid_levels = {"DRASTIC", "SEVERE", "MODERATE", "LOW"}
    
    if problem_level not in valid_levels:
        logger.warning(f"Invalid problem_level '{problem_level}', defaulting to WEAK")
        return "WEAK"
    
    # RULE: DRASTIC or SEVERE = REAL problem
    if problem_level in ["DRASTIC", "SEVERE"]:
        result = "REAL"
        logger.info(f"Problem validity: REAL (problem_level={problem_level})")
    else:
        result = "WEAK"
        logger.info(f"Problem validity: WEAK (problem_level={problem_level})")
    
    return result


def classify_leverage_presence(leverage_flags: List[str]) -> str:
    """
    Classify leverage presence based on Stage 3 leverage flags.
    
    RULE:
    - PRESENT if leverage_flags is non-empty (has at least one flag)
    - NONE if leverage_flags is empty
    
    Args:
        leverage_flags: List of leverage flags from Stage 3
        
    Returns:
        "PRESENT" or "NONE"
    """
    if leverage_flags and len(leverage_flags) > 0:
        result = "PRESENT"
        logger.info(
            f"Leverage presence: PRESENT "
            f"({len(leverage_flags)} flag(s): {', '.join(leverage_flags)})"
        )
    else:
        result = "NONE"
        logger.info("Leverage presence: NONE (no leverage flags detected)")
    
    return result


def classify_validation_class(
    problem_validity: str,
    leverage_presence: str
) -> str:
    """
    Classify validation class based on problem validity and leverage presence.
    
    RULES (deterministic):
    
    1. STRONG_FOUNDATION:
       - REAL problem AND leverage PRESENT
       - This is the ideal case: real problem + competitive edge
    
    2. REAL_PROBLEM_WEAK_EDGE:
       - REAL problem AND leverage NONE
       - Real problem exists but solution lacks competitive leverage
    
    3. WEAK_FOUNDATION:
       - WEAK problem (regardless of leverage)
       - Problem is not severe enough to build on
    
    NOTE: Market pressure does NOT invalidate problems.
    High competition + REAL problem = REAL_PROBLEM_WEAK_EDGE or STRONG_FOUNDATION
    (depending on leverage), NOT WEAK_FOUNDATION.
    
    Args:
        problem_validity: "REAL" or "WEAK"
        leverage_presence: "PRESENT" or "NONE"
        
    Returns:
        "STRONG_FOUNDATION", "REAL_PROBLEM_WEAK_EDGE", or "WEAK_FOUNDATION"
    """
    # Validate inputs
    if problem_validity not in ["REAL", "WEAK"]:
        logger.warning(f"Invalid problem_validity '{problem_validity}', treating as WEAK")
        problem_validity = "WEAK"
    
    if leverage_presence not in ["PRESENT", "NONE"]:
        logger.warning(f"Invalid leverage_presence '{leverage_presence}', treating as NONE")
        leverage_presence = "NONE"
    
    # Apply validation class rules
    if problem_validity == "WEAK":
        # RULE 3: WEAK problem → WEAK_FOUNDATION (regardless of leverage)
        result = "WEAK_FOUNDATION"
        logger.info(
            f"Validation class: WEAK_FOUNDATION "
            f"(problem is not severe enough)"
        )
    elif problem_validity == "REAL" and leverage_presence == "PRESENT":
        # RULE 1: REAL problem + leverage → STRONG_FOUNDATION
        result = "STRONG_FOUNDATION"
        logger.info(
            f"Validation class: STRONG_FOUNDATION "
            f"(real problem + competitive leverage)"
        )
    elif problem_validity == "REAL" and leverage_presence == "NONE":
        # RULE 2: REAL problem + no leverage → REAL_PROBLEM_WEAK_EDGE
        result = "REAL_PROBLEM_WEAK_EDGE"
        logger.info(
            f"Validation class: REAL_PROBLEM_WEAK_EDGE "
            f"(real problem but lacking competitive edge)"
        )
    else:
        # Should never reach here due to validation above, but defensive programming
        logger.error(
            f"Unexpected validation state: "
            f"problem_validity={problem_validity}, leverage_presence={leverage_presence}"
        )
        result = "WEAK_FOUNDATION"
    
    return result


# ============================================================================
# MAIN VALIDATION FUNCTION
# ============================================================================

def validate_idea(
    # Stage 1: Problem Reality
    problem_level: str,
    problem_signals: Dict[str, Any],
    
    # Stage 2: Market Reality
    market_strength: Dict[str, Any],
    
    # Stage 3: Leverage Reality
    leverage_flags: List[str],
    leverage_details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate idea by synchronizing all three stages.
    
    This is the FINAL validation step that combines:
    - Stage 1: Problem Reality (is problem severe?)
    - Stage 2: Market Reality (what's the market landscape?)
    - Stage 3: Leverage Reality (does solution have competitive edge?)
    
    PROCESS:
    1. Classify problem validity (based on Stage 1)
    2. Classify leverage presence (based on Stage 3)
    3. Classify validation class (combination of 1 + 2)
    
    CRITICAL RULES:
    - Market data is CONTEXTUAL, not DECISIVE
    - High competition does NOT invalidate real problems
    - Validation is deterministic (same inputs → same output)
    
    Args:
        problem_level: Problem severity from Stage 1
        problem_signals: Full Stage 1 output (for context)
        market_strength: Stage 2 market strength parameters
        leverage_flags: Stage 3 leverage flags
        leverage_details: Stage 3 detailed leverage info
        
    Returns:
        Complete validation output with all stages synchronized
    """
    logger.info("=" * 70)
    logger.info("FINAL VALIDATION: Synchronizing all stages")
    logger.info("=" * 70)
    
    # ========================================================================
    # STEP 1: Classify problem validity (Stage 1)
    # ========================================================================
    problem_validity = classify_problem_validity(problem_level)
    
    # ========================================================================
    # STEP 2: Classify leverage presence (Stage 3)
    # ========================================================================
    leverage_presence = classify_leverage_presence(leverage_flags)
    
    # ========================================================================
    # STEP 3: Classify validation class (combination)
    # ========================================================================
    validation_class = classify_validation_class(problem_validity, leverage_presence)
    
    # ========================================================================
    # STEP 4: Build validation state
    # ========================================================================
    validation_state = {
        "problem_validity": problem_validity,
        "leverage_presence": leverage_presence,
        "validation_class": validation_class
    }
    
    logger.info(
        f"Validation complete: {validation_class} "
        f"(problem={problem_validity}, leverage={leverage_presence})"
    )
    logger.info("=" * 70)
    
    # ========================================================================
    # STEP 5: Assemble complete output
    # ========================================================================
    # This matches the required output structure from the specification
    return {
        "problem_reality": {
            "problem_level": problem_level,
            "signals": problem_signals
        },
        "market_reality": {
            "market_strength": market_strength
        },
        "leverage_reality": {
            "leverage_flags": leverage_flags,
            "leverage_details": leverage_details
        },
        "validation_state": validation_state
    }


# ============================================================================
# CONTEXT INTERPRETATION (READ-ONLY)
# ============================================================================
# These functions provide CONTEXT about the validation outcome.
# They do NOT change the validation logic or affect the output.
# They are INFORMATIONAL only, for logging and debugging.
# ============================================================================

def interpret_validation_context(
    validation_class: str,
    market_strength: Dict[str, Any]
) -> Dict[str, str]:
    """
    Provide CONTEXTUAL interpretation of validation outcome.
    
    This is INFORMATIONAL only. It does NOT affect validation logic.
    
    PURPOSE:
    Help developers understand what the validation class means in the
    context of market conditions.
    
    CRITICAL: This is READ-ONLY context, not decision logic.
    
    Args:
        validation_class: The validation class from validation
        market_strength: Market strength parameters from Stage 2
        
    Returns:
        Dict with contextual interpretations (for logging/debugging only)
    """
    context = {
        "validation_class": validation_class,
        "interpretation": ""
    }
    
    # Get market context
    competitor_density = market_strength.get("competitor_density", "UNKNOWN")
    substitute_pressure = market_strength.get("substitute_pressure", "UNKNOWN")
    
    # Provide interpretation based on validation class
    if validation_class == "STRONG_FOUNDATION":
        context["interpretation"] = (
            "Real problem with competitive leverage. "
            f"Market context: {competitor_density} competitor density, "
            f"{substitute_pressure} substitute pressure."
        )
    elif validation_class == "REAL_PROBLEM_WEAK_EDGE":
        context["interpretation"] = (
            "Real problem but lacking competitive leverage. "
            f"Market context: {competitor_density} competitor density, "
            f"{substitute_pressure} substitute pressure. "
            "Consider strengthening solution's unique value proposition."
        )
    elif validation_class == "WEAK_FOUNDATION":
        context["interpretation"] = (
            "Problem is not severe enough to build a strong foundation. "
            "Consider validating problem severity with more research."
        )
    else:
        context["interpretation"] = "Unknown validation class"
    
    return context


def get_validation_summary(validation_output: Dict[str, Any]) -> str:
    """
    Generate human-readable summary of validation output.
    
    This is for LOGGING/DEBUGGING only. Does NOT affect logic.
    
    Args:
        validation_output: Complete validation output from validate_idea()
        
    Returns:
        Human-readable summary string
    """
    validation_state = validation_output.get("validation_state", {})
    problem_reality = validation_output.get("problem_reality", {})
    leverage_reality = validation_output.get("leverage_reality", {})
    
    problem_level = problem_reality.get("problem_level", "UNKNOWN")
    validation_class = validation_state.get("validation_class", "UNKNOWN")
    leverage_flags = leverage_reality.get("leverage_flags", [])
    
    summary_lines = [
        "=" * 70,
        "VALIDATION SUMMARY",
        "=" * 70,
        f"Problem Level: {problem_level}",
        f"Validation Class: {validation_class}",
        f"Leverage Flags: {', '.join(leverage_flags) if leverage_flags else 'NONE'}",
        "=" * 70
    ]
    
    return "\n".join(summary_lines)
