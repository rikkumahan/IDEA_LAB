"""
Stage 3: Deterministic Leverage Detection

This module implements Stage 3 of the decision engine:
- Collects structured leverage inputs via questioning layer
- Performs deterministic leverage detection
- Generates leverage_flags output

CRITICAL RULES:
- All logic is deterministic and rule-based
- No LLM reasoning or inference
- Same inputs ALWAYS produce same outputs
- LLM used ONLY for question wording (not decisions)
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CANONICAL QUESTION DEFINITIONS
# ============================================================================
# These are the SOURCE OF TRUTH for Stage 3 inputs.
# Each question has a fixed semantic meaning that MUST NOT change.
# ============================================================================

class CanonicalQuestion(BaseModel):
    """
    Canonical question definition.
    
    This defines the EXACT semantic meaning of each input.
    LLM may reword for clarity, but MUST NOT change the meaning.
    """
    id: str  # Unique identifier
    semantic_meaning: str  # Exact meaning (source of truth)
    answer_type: str  # "boolean" or "integer"
    validation_rules: Dict[str, Any]  # Validation constraints
    
    # Example question wording (can be adapted by LLM)
    default_wording: str
    
    # Context hints for LLM adaptation (optional)
    domain_hints: Optional[List[str]] = None


# Define canonical questions (FIXED - do not modify without careful review)
CANONICAL_QUESTIONS: Dict[str, CanonicalQuestion] = {
    "replaces_human_labor": CanonicalQuestion(
        id="replaces_human_labor",
        semantic_meaning=(
            "Does your solution automate or replace work that humans "
            "currently do manually?"
        ),
        answer_type="boolean",
        validation_rules={
            "type": "bool",
            "required": True
        },
        default_wording=(
            "Does your solution replace or automate work that is currently "
            "done manually by humans?"
        ),
        domain_hints=[
            "automation", "human labor", "manual work", "workforce"
        ]
    ),
    
    "step_reduction_ratio": CanonicalQuestion(
        id="step_reduction_ratio",
        semantic_meaning=(
            "How many manual steps does your solution eliminate? "
            "Count the number of steps in the current process that become "
            "unnecessary with your solution."
        ),
        answer_type="integer",
        validation_rules={
            "type": "int",
            "required": True,
            "min": 0,
            "max": 1000  # Reasonable upper bound
        },
        default_wording=(
            "How many manual steps or actions does your solution eliminate "
            "from the current process? (Enter a number, 0 if none)"
        ),
        domain_hints=[
            "process steps", "workflow", "manual actions", "efficiency"
        ]
    ),
    
    "delivers_final_answer": CanonicalQuestion(
        id="delivers_final_answer",
        semantic_meaning=(
            "Does your solution provide a complete, ready-to-use output "
            "that requires no further processing by the user?"
        ),
        answer_type="boolean",
        validation_rules={
            "type": "bool",
            "required": True
        },
        default_wording=(
            "Does your solution deliver a final, ready-to-use answer or output "
            "that requires no further work?"
        ),
        domain_hints=[
            "complete output", "final result", "ready to use", "no post-processing"
        ]
    ),
    
    "unique_data_access": CanonicalQuestion(
        id="unique_data_access",
        semantic_meaning=(
            "Does your solution have access to proprietary data, specialized "
            "databases, or unique information sources that competitors cannot "
            "easily replicate?"
        ),
        answer_type="boolean",
        validation_rules={
            "type": "bool",
            "required": True
        },
        default_wording=(
            "Does your solution use proprietary data or unique information "
            "sources that others cannot easily access?"
        ),
        domain_hints=[
            "proprietary data", "exclusive access", "unique database", 
            "specialized information"
        ]
    ),
    
    "works_under_constraints": CanonicalQuestion(
        id="works_under_constraints",
        semantic_meaning=(
            "Can your solution operate effectively under resource constraints "
            "(limited time, budget, connectivity, etc.) where traditional "
            "approaches fail?"
        ),
        answer_type="boolean",
        validation_rules={
            "type": "bool",
            "required": True
        },
        default_wording=(
            "Does your solution work effectively under constraints (time, budget, "
            "connectivity) where traditional approaches struggle?"
        ),
        domain_hints=[
            "resource constraints", "limited resources", "offline capable",
            "low-bandwidth", "time-limited"
        ]
    ),
}


# ============================================================================
# LEVERAGE INPUT MODEL
# ============================================================================

class LeverageInput(BaseModel):
    """
    Validated leverage inputs for Stage 3.
    
    These inputs have passed:
    1. Type validation (boolean/integer)
    2. Sanity validation (cross-field checks)
    
    FIREWALL: This model ensures no unvalidated data reaches Stage 3 logic.
    """
    replaces_human_labor: bool
    step_reduction_ratio: int = Field(ge=0)  # >= 0
    delivers_final_answer: bool
    unique_data_access: bool
    works_under_constraints: bool
    
    @validator('step_reduction_ratio')
    def validate_step_reduction(cls, v, values):
        """
        Sanity check: step_reduction_ratio consistency with automation.
        
        RULE: If step_reduction_ratio == 0, automation should be minimal.
        However, we don't have direct access to automation_relevance here,
        so this check is implemented in validate_leverage_inputs_sanity.
        """
        if v < 0:
            raise ValueError("step_reduction_ratio must be >= 0")
        if v > 1000:
            raise ValueError("step_reduction_ratio seems unreasonably high (>1000)")
        return v


# ============================================================================
# LEVERAGE FLAGS OUTPUT
# ============================================================================

class LeverageFlag(BaseModel):
    """Single leverage flag with explanation."""
    name: str
    present: bool
    reason: str  # Brief explanation (deterministic)


class LeverageFlags(BaseModel):
    """
    Leverage flags output from Stage 3.
    
    This is a list of specific leverage advantages detected.
    Each flag is backed by deterministic rules.
    """
    flags: List[LeverageFlag]
    
    def is_empty(self) -> bool:
        """Check if any leverage is present."""
        return all(not flag.present for flag in self.flags)
    
    def get_present_flags(self) -> List[LeverageFlag]:
        """Get only the flags that are present."""
        return [flag for flag in self.flags if flag.present]


# ============================================================================
# STAGE 3: DETERMINISTIC LEVERAGE DETECTION
# ============================================================================

def detect_leverage(inputs: LeverageInput) -> LeverageFlags:
    """
    Detect leverage based on validated inputs using deterministic rules.
    
    CRITICAL: This function is PURE and DETERMINISTIC.
    - No randomness
    - No LLM calls
    - No external dependencies
    - Same inputs ALWAYS produce same outputs
    
    LEVERAGE DETECTION RULES:
    
    1. AUTOMATION_LEVERAGE:
       - replaces_human_labor == True
       - step_reduction_ratio >= 3
       
    2. COMPLETENESS_LEVERAGE:
       - delivers_final_answer == True
       - step_reduction_ratio >= 5 (significant elimination)
       
    3. DATA_LEVERAGE:
       - unique_data_access == True
       
    4. CONSTRAINT_LEVERAGE:
       - works_under_constraints == True
       - step_reduction_ratio >= 2 (meaningful improvement)
    
    Args:
        inputs: Validated leverage inputs
        
    Returns:
        LeverageFlags with detected advantages
    """
    flags = []
    
    # Rule 1: AUTOMATION_LEVERAGE
    if inputs.replaces_human_labor and inputs.step_reduction_ratio >= 3:
        flags.append(LeverageFlag(
            name="AUTOMATION_LEVERAGE",
            present=True,
            reason=(
                f"Replaces manual labor and eliminates {inputs.step_reduction_ratio} "
                "steps, providing significant efficiency gains"
            )
        ))
    
    # Rule 2: COMPLETENESS_LEVERAGE
    if inputs.delivers_final_answer and inputs.step_reduction_ratio >= 5:
        flags.append(LeverageFlag(
            name="COMPLETENESS_LEVERAGE",
            present=True,
            reason=(
                f"Delivers complete solution and eliminates {inputs.step_reduction_ratio} "
                "steps, removing need for post-processing"
            )
        ))
    
    # Rule 3: DATA_LEVERAGE
    if inputs.unique_data_access:
        flags.append(LeverageFlag(
            name="DATA_LEVERAGE",
            present=True,
            reason="Has access to unique or proprietary data that competitors cannot easily replicate"
        ))
    
    # Rule 4: CONSTRAINT_LEVERAGE
    if inputs.works_under_constraints and inputs.step_reduction_ratio >= 2:
        flags.append(LeverageFlag(
            name="CONSTRAINT_LEVERAGE",
            present=True,
            reason=(
                f"Operates effectively under resource constraints and eliminates "
                f"{inputs.step_reduction_ratio} steps where traditional approaches struggle"
            )
        ))
    
    # If no flags detected, return empty list
    if not flags:
        logger.info("No leverage flags detected based on inputs")
    else:
        logger.info(f"Detected {len(flags)} leverage flag(s): {[f.name for f in flags]}")
    
    return LeverageFlags(flags=flags)


# ============================================================================
# INPUT VALIDATION
# ============================================================================

class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


def validate_leverage_inputs_sanity(inputs: Dict[str, Any]) -> None:
    """
    Sanity validation: Check for logical inconsistencies.
    
    RULES:
    1. If step_reduction_ratio == 0, automation should be minimal
       (Cannot eliminate 0 steps AND have high automation leverage)
    
    2. If replaces_human_labor == False, step_reduction_ratio should be low
       (How can you eliminate many steps without automation?)
    
    These are WARNINGS, not hard errors. We log them but don't reject.
    
    Args:
        inputs: Raw input dictionary
        
    Raises:
        ValidationError: If critical inconsistency detected
    """
    step_reduction = inputs.get('step_reduction_ratio', 0)
    replaces_labor = inputs.get('replaces_human_labor', False)
    
    # Rule 1: Zero steps but claims automation
    if step_reduction == 0 and replaces_labor:
        logger.warning(
            "Potential inconsistency: replaces_human_labor=True but "
            "step_reduction_ratio=0. How does automation not reduce steps?"
        )
    
    # Rule 2: Many steps eliminated without automation
    if step_reduction >= 5 and not replaces_labor:
        logger.warning(
            f"Potential inconsistency: step_reduction_ratio={step_reduction} "
            "but replaces_human_labor=False. How are steps eliminated without automation?"
        )
    
    # No hard errors - let the leverage detection rules handle edge cases


def validate_and_parse_inputs(raw_inputs: Dict[str, Any]) -> LeverageInput:
    """
    Validate and parse raw inputs into LeverageInput model.
    
    DUAL VALIDATION:
    1. Type validation (via Pydantic)
    2. Sanity validation (logical consistency)
    
    FIREWALL: This is the entry point to Stage 3. No unvalidated data passes.
    
    Args:
        raw_inputs: Raw input dictionary from questioning layer
        
    Returns:
        Validated LeverageInput
        
    Raises:
        ValidationError: If validation fails
    """
    # Sanity validation BEFORE type validation
    try:
        validate_leverage_inputs_sanity(raw_inputs)
    except Exception as e:
        logger.error(f"Sanity validation failed: {e}")
        raise ValidationError(f"Input sanity check failed: {e}")
    
    # Type validation via Pydantic
    try:
        inputs = LeverageInput(**raw_inputs)
    except Exception as e:
        logger.error(f"Type validation failed: {e}")
        raise ValidationError(f"Input type validation failed: {e}")
    
    logger.info("Leverage inputs validated successfully")
    return inputs


# ============================================================================
# STAGE 3 MAIN ENTRY POINT
# ============================================================================

def run_stage3_leverage_detection(raw_inputs: Dict[str, Any]) -> LeverageFlags:
    """
    Stage 3 main entry point: Validate inputs and detect leverage.
    
    This is the complete Stage 3 pipeline:
    1. Validate inputs (type + sanity)
    2. Detect leverage (deterministic rules)
    3. Return leverage flags
    
    FIREWALL: All inputs are validated before processing.
    DETERMINISM: Same inputs always produce same outputs.
    
    Args:
        raw_inputs: Raw input dictionary from questioning layer
        
    Returns:
        LeverageFlags with detected advantages
        
    Raises:
        ValidationError: If inputs are invalid
    """
    # Validate and parse inputs
    inputs = validate_and_parse_inputs(raw_inputs)
    
    # Detect leverage using deterministic rules
    flags = detect_leverage(inputs)
    
    logger.info(f"Stage 3 complete: {len(flags.get_present_flags())} leverage flags detected")
    
    return flags
