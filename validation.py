"""
VALIDATION LOGIC: Synchronize Stage 1, Stage 2, and Stage 3

This module implements deterministic validation that combines:
- Stage 1: Problem Reality (problem_level)
- Stage 2: Market Reality (market strength parameters)
- Stage 3: Leverage Reality (leverage_flags)

Into a final validation state.

CRITICAL CONSTRAINTS:
- All logic is deterministic (no LLM, no ML)
- Market pressure does NOT invalidate the problem
- Market data is contextual only
- No strategic advice or success prediction

VALIDATION RULES (DETERMINISTIC):

1. problem_validity
   - REAL if problem_level >= SEVERE
   - WEAK otherwise

2. leverage_presence
   - PRESENT if leverage_flags is non-empty
   - NONE otherwise

3. validation_class
   - STRONG_FOUNDATION: REAL problem AND leverage PRESENT
   - REAL_PROBLEM_WEAK_EDGE: REAL problem AND leverage NONE
   - WEAK_FOUNDATION: WEAK problem

OUTPUT STRUCTURE:
{
  "problem_reality": {...},
  "market_reality": {...},
  "leverage_reality": {...},
  "validation_state": {
    "problem_validity": "...",
    "leverage_presence": "...",
    "validation_class": "..."
  }
}
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


# ============================================================================
# VALIDATION RULES (DETERMINISTIC)
# ============================================================================

def determine_problem_validity(problem_level: str) -> str:
    """
    Determine if problem is REAL or WEAK based on problem_level from Stage 1.
    
    DETERMINISTIC RULE:
    - REAL if problem_level >= SEVERE (i.e., SEVERE or DRASTIC)
    - WEAK otherwise (MODERATE or LOW)
    
    This is INDEPENDENT of market data. Market pressure does NOT invalidate
    a real problem - it only provides context.
    
    Args:
        problem_level: From Stage 1 ("DRASTIC", "SEVERE", "MODERATE", "LOW")
        
    Returns:
        "REAL" or "WEAK"
    """
    # Validate input
    valid_levels = {"DRASTIC", "SEVERE", "MODERATE", "LOW"}
    if problem_level not in valid_levels:
        raise ValueError(
            f"Invalid problem_level '{problem_level}', must be one of {valid_levels}"
        )
    
    # Deterministic rule: >= SEVERE is REAL
    if problem_level in {"DRASTIC", "SEVERE"}:
        problem_validity = "REAL"
        logger.info(
            f"Problem validity: REAL (problem_level={problem_level} >= SEVERE)"
        )
    else:
        problem_validity = "WEAK"
        logger.info(
            f"Problem validity: WEAK (problem_level={problem_level} < SEVERE)"
        )
    
    return problem_validity


def determine_leverage_presence(leverage_flags: List[str]) -> str:
    """
    Determine if leverage is PRESENT or NONE based on leverage_flags from Stage 3.
    
    DETERMINISTIC RULE:
    - PRESENT if leverage_flags is non-empty (at least one flag)
    - NONE if leverage_flags is empty
    
    Args:
        leverage_flags: From Stage 3 (list of leverage flag strings)
        
    Returns:
        "PRESENT" or "NONE"
    """
    # Validate input
    if not isinstance(leverage_flags, list):
        raise ValueError(
            f"leverage_flags must be a list, got {type(leverage_flags)}"
        )
    
    # Deterministic rule: non-empty list = PRESENT
    if len(leverage_flags) > 0:
        leverage_presence = "PRESENT"
        logger.info(
            f"Leverage presence: PRESENT ({len(leverage_flags)} flags: {leverage_flags})"
        )
    else:
        leverage_presence = "NONE"
        logger.info("Leverage presence: NONE (no flags)")
    
    return leverage_presence


def determine_validation_class(
    problem_validity: str,
    leverage_presence: str
) -> str:
    """
    Determine validation class based on problem validity and leverage presence.
    
    DETERMINISTIC RULES:
    1. STRONG_FOUNDATION: REAL problem AND leverage PRESENT
       (Both problem and leverage are strong)
    
    2. REAL_PROBLEM_WEAK_EDGE: REAL problem AND leverage NONE
       (Problem is real but competitive edge is weak)
    
    3. WEAK_FOUNDATION: WEAK problem
       (Problem itself is weak, regardless of leverage)
    
    Args:
        problem_validity: "REAL" or "WEAK"
        leverage_presence: "PRESENT" or "NONE"
        
    Returns:
        "STRONG_FOUNDATION", "REAL_PROBLEM_WEAK_EDGE", or "WEAK_FOUNDATION"
    """
    # Validate inputs
    if problem_validity not in {"REAL", "WEAK"}:
        raise ValueError(
            f"Invalid problem_validity '{problem_validity}', must be REAL or WEAK"
        )
    
    if leverage_presence not in {"PRESENT", "NONE"}:
        raise ValueError(
            f"Invalid leverage_presence '{leverage_presence}', must be PRESENT or NONE"
        )
    
    # Deterministic rules
    if problem_validity == "REAL" and leverage_presence == "PRESENT":
        validation_class = "STRONG_FOUNDATION"
        logger.info(
            "Validation class: STRONG_FOUNDATION "
            "(REAL problem + leverage PRESENT)"
        )
    
    elif problem_validity == "REAL" and leverage_presence == "NONE":
        validation_class = "REAL_PROBLEM_WEAK_EDGE"
        logger.info(
            "Validation class: REAL_PROBLEM_WEAK_EDGE "
            "(REAL problem + leverage NONE)"
        )
    
    else:  # problem_validity == "WEAK"
        validation_class = "WEAK_FOUNDATION"
        logger.info(
            f"Validation class: WEAK_FOUNDATION "
            f"(WEAK problem, leverage={leverage_presence})"
        )
    
    return validation_class


# ============================================================================
# MAIN VALIDATION FUNCTION
# ============================================================================

def compute_validation_state(
    stage1_problem_reality: Dict[str, Any],
    stage2_market_reality: Dict[str, Any],
    stage3_leverage_reality: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute final validation state by synchronizing all three stages.
    
    This function:
    1. Extracts required inputs from each stage
    2. Determines problem_validity (from Stage 1)
    3. Determines leverage_presence (from Stage 3)
    4. Determines validation_class (from problem_validity + leverage_presence)
    5. Returns complete validation output
    
    CRITICAL: This function is PURE and DETERMINISTIC.
    - No side effects (except logging)
    - No LLM, NLP, or ML
    - Same inputs → same outputs (always)
    - Market data is included for context but does NOT affect validation
    
    Args:
        stage1_problem_reality: Dict from Stage 1
            Required key: problem_level
        stage2_market_reality: Dict from Stage 2
            (Included for context, does NOT affect validation logic)
        stage3_leverage_reality: Dict from Stage 3
            Required key: leverage_flags
    
    Returns:
        Dict with complete validation output:
        {
          "problem_reality": {...},
          "market_reality": {...},
          "leverage_reality": {...},
          "validation_state": {
            "problem_validity": "...",
            "leverage_presence": "...",
            "validation_class": "..."
          }
        }
    
    Raises:
        ValueError: If required inputs are missing or invalid
    """
    # Extract Stage 1 inputs
    try:
        problem_level = stage1_problem_reality["problem_level"]
    except KeyError as e:
        raise ValueError(f"Missing required Stage 1 input: {e}")
    
    # Extract Stage 3 inputs
    try:
        leverage_flags = stage3_leverage_reality["leverage_flags"]
    except KeyError as e:
        raise ValueError(f"Missing required Stage 3 input: {e}")
    
    # Stage 2 is included for context but does NOT affect validation
    # No extraction needed - just pass through
    
    # Determine problem validity (from Stage 1)
    problem_validity = determine_problem_validity(problem_level)
    
    # Determine leverage presence (from Stage 3)
    leverage_presence = determine_leverage_presence(leverage_flags)
    
    # Determine validation class (from problem validity + leverage presence)
    validation_class = determine_validation_class(
        problem_validity,
        leverage_presence
    )
    
    # Build complete output
    validation_output = {
        "problem_reality": stage1_problem_reality,
        "market_reality": stage2_market_reality,
        "leverage_reality": stage3_leverage_reality,
        "validation_state": {
            "problem_validity": problem_validity,
            "leverage_presence": leverage_presence,
            "validation_class": validation_class
        }
    }
    
    logger.info(
        f"Validation complete: "
        f"problem={problem_validity}, "
        f"leverage={leverage_presence}, "
        f"class={validation_class}"
    )
    
    return validation_output


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_validation_explanation(validation_class: str) -> str:
    """
    Get human-readable explanation of validation class.
    
    This is a helper for explanation layer, NOT part of validation logic.
    
    Args:
        validation_class: Validation class from compute_validation_state
        
    Returns:
        Human-readable explanation string
    """
    explanations = {
        "STRONG_FOUNDATION": (
            "Strong foundation detected: The problem is real (SEVERE or DRASTIC severity) "
            "AND your solution has identifiable competitive leverage. This combination "
            "provides a solid foundation for potential success."
        ),
        "REAL_PROBLEM_WEAK_EDGE": (
            "Real problem, weak edge detected: The problem is real (SEVERE or DRASTIC severity) "
            "but your solution lacks clear competitive leverage. Consider strengthening your "
            "competitive advantages: cost savings, time savings, cognitive value, unique data access, "
            "or ability to work under constraints."
        ),
        "WEAK_FOUNDATION": (
            "Weak foundation detected: The problem severity is below SEVERE (MODERATE or LOW). "
            "This suggests the problem may not be significant enough to support a strong business, "
            "regardless of competitive leverage. Consider pivoting to a more severe problem."
        )
    }
    
    return explanations.get(
        validation_class,
        f"Unknown validation class: {validation_class}"
    )


def is_strong_validation(validation_class: str) -> bool:
    """
    Check if validation represents a strong foundation.
    
    This is a helper for downstream logic, NOT part of validation itself.
    
    Args:
        validation_class: Validation class from compute_validation_state
        
    Returns:
        True if validation_class is STRONG_FOUNDATION, False otherwise
    """
    return validation_class == "STRONG_FOUNDATION"
