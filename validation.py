"""
Stage 4: Validation - Synchronize Problem, Market, and Leverage Reality

This module implements the final validation logic that combines:
- Stage 1: Problem Reality
- Stage 2: Market Reality  
- Stage 3: Leverage Reality

Into a final validation state.

CRITICAL RULES:
- All validation logic is deterministic
- Market pressure does NOT invalidate the problem
- Market data is contextual only
- Same inputs ALWAYS produce same validation class
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# VALIDATION ENUMS
# ============================================================================

class ProblemValidity(str, Enum):
    """Problem validity classification."""
    REAL = "REAL"  # problem_level >= SEVERE
    WEAK = "WEAK"  # problem_level < SEVERE


class LeveragePresence(str, Enum):
    """Leverage presence classification."""
    PRESENT = "PRESENT"  # leverage_flags is non-empty
    NONE = "NONE"  # leverage_flags is empty


class ValidationClass(str, Enum):
    """Final validation class."""
    STRONG_FOUNDATION = "STRONG_FOUNDATION"  # REAL problem + PRESENT leverage
    REAL_PROBLEM_WEAK_EDGE = "REAL_PROBLEM_WEAK_EDGE"  # REAL problem + NONE leverage
    WEAK_FOUNDATION = "WEAK_FOUNDATION"  # WEAK problem


# ============================================================================
# VALIDATION STATE
# ============================================================================

class ValidationState(BaseModel):
    """
    Final validation state combining all stages.
    
    This is the deterministic output of the entire pipeline.
    """
    problem_validity: ProblemValidity
    leverage_presence: LeveragePresence
    validation_class: ValidationClass
    
    # Reasoning (deterministic, not LLM-generated)
    reasoning: str


# ============================================================================
# STAGE OUTPUTS
# ============================================================================

class ProblemReality(BaseModel):
    """Stage 1 output structure."""
    problem_level: str  # "DRASTIC", "SEVERE", "MODERATE", "LOW"
    signals: Dict[str, Any]
    normalized_signals: Dict[str, Any]


class MarketReality(BaseModel):
    """Stage 2 output structure."""
    solution_modality: str
    market_strength: Dict[str, Any]
    competitors: Dict[str, Any]


class LeverageReality(BaseModel):
    """Stage 3 output structure."""
    leverage_flags: list  # List of LeverageFlag dicts
    
    def is_empty(self) -> bool:
        """Check if any leverage is present."""
        return len(self.leverage_flags) == 0


# ============================================================================
# VALIDATION LOGIC (DETERMINISTIC)
# ============================================================================

def classify_problem_validity(problem_reality: ProblemReality) -> ProblemValidity:
    """
    Classify problem validity based on Stage 1 output.
    
    RULE (deterministic):
    - REAL if problem_level in ["DRASTIC", "SEVERE"]
    - WEAK otherwise
    
    Args:
        problem_reality: Stage 1 output
        
    Returns:
        ProblemValidity classification
    """
    problem_level = problem_reality.problem_level.upper()
    
    if problem_level in ["DRASTIC", "SEVERE"]:
        logger.info(f"Problem classified as REAL (level: {problem_level})")
        return ProblemValidity.REAL
    else:
        logger.info(f"Problem classified as WEAK (level: {problem_level})")
        return ProblemValidity.WEAK


def classify_leverage_presence(leverage_reality: LeverageReality) -> LeveragePresence:
    """
    Classify leverage presence based on Stage 3 output.
    
    RULE (deterministic):
    - PRESENT if leverage_flags is non-empty
    - NONE otherwise
    
    Args:
        leverage_reality: Stage 3 output
        
    Returns:
        LeveragePresence classification
    """
    if leverage_reality.is_empty():
        logger.info("Leverage classified as NONE (no flags present)")
        return LeveragePresence.NONE
    else:
        logger.info(f"Leverage classified as PRESENT ({len(leverage_reality.leverage_flags)} flags)")
        return LeveragePresence.PRESENT


def classify_validation_class(
    problem_validity: ProblemValidity,
    leverage_presence: LeveragePresence
) -> ValidationClass:
    """
    Classify final validation class based on problem and leverage.
    
    RULES (deterministic):
    1. STRONG_FOUNDATION: REAL problem AND PRESENT leverage
    2. REAL_PROBLEM_WEAK_EDGE: REAL problem AND NONE leverage
    3. WEAK_FOUNDATION: WEAK problem (regardless of leverage)
    
    CRITICAL: Market pressure does NOT invalidate the problem.
    Market data is contextual only.
    
    Args:
        problem_validity: Problem validity classification
        leverage_presence: Leverage presence classification
        
    Returns:
        ValidationClass
    """
    if problem_validity == ProblemValidity.WEAK:
        # Weak problem → WEAK_FOUNDATION regardless of leverage
        logger.info("Validation class: WEAK_FOUNDATION (weak problem)")
        return ValidationClass.WEAK_FOUNDATION
    
    # Real problem - check leverage
    if leverage_presence == LeveragePresence.PRESENT:
        logger.info("Validation class: STRONG_FOUNDATION (real problem + leverage)")
        return ValidationClass.STRONG_FOUNDATION
    else:
        logger.info("Validation class: REAL_PROBLEM_WEAK_EDGE (real problem, no leverage)")
        return ValidationClass.REAL_PROBLEM_WEAK_EDGE


def generate_validation_reasoning(
    problem_validity: ProblemValidity,
    leverage_presence: LeveragePresence,
    validation_class: ValidationClass,
    problem_level: str,
    leverage_count: int
) -> str:
    """
    Generate deterministic reasoning for validation result.
    
    This is NOT LLM-generated. It's a deterministic template.
    
    Args:
        problem_validity: Problem validity
        leverage_presence: Leverage presence
        validation_class: Final validation class
        problem_level: Original problem level
        leverage_count: Number of leverage flags
        
    Returns:
        Reasoning string
    """
    if validation_class == ValidationClass.STRONG_FOUNDATION:
        return (
            f"Problem is {problem_validity.value} (level: {problem_level}) and "
            f"{leverage_count} leverage advantage(s) detected. This represents a "
            "strong foundation for a defensible solution."
        )
    elif validation_class == ValidationClass.REAL_PROBLEM_WEAK_EDGE:
        return (
            f"Problem is {problem_validity.value} (level: {problem_level}) but "
            "no significant leverage advantages detected. The problem is real, "
            "but competitive edge may be limited."
        )
    else:  # WEAK_FOUNDATION
        return (
            f"Problem is {problem_validity.value} (level: {problem_level}). "
            "Foundation may be insufficient for a viable startup."
        )


# ============================================================================
# VALIDATION PIPELINE
# ============================================================================

def validate_startup_idea(
    problem_reality: ProblemReality,
    market_reality: Optional[MarketReality],
    leverage_reality: LeverageReality
) -> ValidationState:
    """
    Validate startup idea by combining all stages.
    
    This is the main validation function that produces the final
    deterministic classification.
    
    IMPORTANT:
    - Market reality is OPTIONAL and CONTEXTUAL ONLY
    - Market data does NOT invalidate the problem
    - Validation is based on problem + leverage only
    
    Args:
        problem_reality: Stage 1 output
        market_reality: Stage 2 output (optional, contextual)
        leverage_reality: Stage 3 output
        
    Returns:
        ValidationState with final classification
    """
    logger.info("Starting validation pipeline")
    
    # Step 1: Classify problem validity
    problem_validity = classify_problem_validity(problem_reality)
    
    # Step 2: Classify leverage presence
    leverage_presence = classify_leverage_presence(leverage_reality)
    
    # Step 3: Classify validation class
    validation_class = classify_validation_class(
        problem_validity,
        leverage_presence
    )
    
    # Step 4: Generate reasoning
    reasoning = generate_validation_reasoning(
        problem_validity,
        leverage_presence,
        validation_class,
        problem_reality.problem_level,
        len(leverage_reality.leverage_flags)
    )
    
    # Log market context if available (but don't use in validation)
    if market_reality:
        logger.info(
            f"Market context (informational only): "
            f"modality={market_reality.solution_modality}, "
            f"competitor_density={market_reality.market_strength.get('competitor_density')}"
        )
        logger.info("NOTE: Market data is contextual and does not affect validation class")
    
    # Build validation state
    state = ValidationState(
        problem_validity=problem_validity,
        leverage_presence=leverage_presence,
        validation_class=validation_class,
        reasoning=reasoning
    )
    
    logger.info(f"Validation complete: {validation_class.value}")
    
    return state


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

def format_validation_output(
    problem_reality: ProblemReality,
    market_reality: Optional[MarketReality],
    leverage_reality: LeverageReality,
    validation_state: ValidationState
) -> Dict[str, Any]:
    """
    Format complete validation output.
    
    This matches the required output structure:
    {
      "problem_reality": {...},
      "market_reality": {...},
      "leverage_reality": {...},
      "validation_state": {...}
    }
    
    Args:
        problem_reality: Stage 1 output
        market_reality: Stage 2 output (optional)
        leverage_reality: Stage 3 output
        validation_state: Validation result
        
    Returns:
        Complete output dict
    """
    output = {
        "problem_reality": {
            "problem_level": problem_reality.problem_level,
            "signals": problem_reality.signals,
            "normalized_signals": problem_reality.normalized_signals
        },
        "leverage_reality": {
            "leverage_flags": leverage_reality.leverage_flags
        },
        "validation_state": {
            "problem_validity": validation_state.problem_validity.value,
            "leverage_presence": validation_state.leverage_presence.value,
            "validation_class": validation_state.validation_class.value,
            "reasoning": validation_state.reasoning
        }
    }
    
    # Add market reality if available
    if market_reality:
        output["market_reality"] = {
            "solution_modality": market_reality.solution_modality,
            "market_strength": market_reality.market_strength,
            "competitors": market_reality.competitors
        }
    
    return output
