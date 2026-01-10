"""
STAGE 3: DETERMINISTIC LEVERAGE ENGINE

This module implements Stage 3 as a pure, deterministic, rule-based engine.
It MUST work identically with the LLM disabled.

CRITICAL CONSTRAINTS:
- Pure function/module (no side effects)
- Rule-based only (no LLM, no NLP, no ML)
- Auditable and testable
- Deterministic (same inputs → same outputs)
- Independent of Stages 1, 2, and 4

INPUTS (FIXED):
From Stage 2:
- automation_relevance: str ("LOW", "MEDIUM", "HIGH")
- substitute_pressure: str ("LOW", "MEDIUM", "HIGH")
- content_saturation: str ("LOW", "MEDIUM", "HIGH")

From user leverage inputs (STRUCTURED ONLY):
- replaces_human_labor: bool
- step_reduction_ratio: int (>= 0)
- delivers_final_answer: bool
- unique_data_access: bool
- works_under_constraints: bool

OUTPUTS:
- leverage_flags: list of str (may contain multiple flags)
  Possible values: COST_LEVERAGE, TIME_LEVERAGE, COGNITIVE_LEVERAGE, 
                   ACCESS_LEVERAGE, CONSTRAINT_LEVERAGE

FORBIDDEN:
- Inferring leverage from text
- Using LLM or NLP in Stage 3
- Scoring or ranking leverage
- Collapsing leverage into a single metric
- Suppressing leverage due to competition
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class LeverageInput:
    """
    Structured input for Stage 3 leverage determination.
    
    All inputs must be structured (boolean or integer), no free text allowed.
    """
    
    def __init__(
        self,
        # From Stage 2 (market reality)
        automation_relevance: str,
        substitute_pressure: str,
        content_saturation: str,
        # From user leverage inputs
        replaces_human_labor: bool,
        step_reduction_ratio: int,
        delivers_final_answer: bool,
        unique_data_access: bool,
        works_under_constraints: bool
    ):
        """
        Initialize leverage input with validation.
        
        Args:
            automation_relevance: Must be "LOW", "MEDIUM", or "HIGH"
            substitute_pressure: Must be "LOW", "MEDIUM", or "HIGH"
            content_saturation: Must be "LOW", "MEDIUM", or "HIGH"
            replaces_human_labor: Boolean flag
            step_reduction_ratio: Integer >= 0
            delivers_final_answer: Boolean flag
            unique_data_access: Boolean flag
            works_under_constraints: Boolean flag
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Validate Stage 2 inputs
        valid_levels = {"LOW", "MEDIUM", "HIGH"}
        
        if automation_relevance not in valid_levels:
            raise ValueError(
                f"automation_relevance must be one of {valid_levels}, "
                f"got '{automation_relevance}'"
            )
        
        if substitute_pressure not in valid_levels:
            raise ValueError(
                f"substitute_pressure must be one of {valid_levels}, "
                f"got '{substitute_pressure}'"
            )
        
        if content_saturation not in valid_levels:
            raise ValueError(
                f"content_saturation must be one of {valid_levels}, "
                f"got '{content_saturation}'"
            )
        
        # Validate user leverage inputs
        if not isinstance(replaces_human_labor, bool):
            raise ValueError(
                f"replaces_human_labor must be boolean, got {type(replaces_human_labor)}"
            )
        
        if not isinstance(step_reduction_ratio, int) or step_reduction_ratio < 0:
            raise ValueError(
                f"step_reduction_ratio must be integer >= 0, got {step_reduction_ratio}"
            )
        
        if not isinstance(delivers_final_answer, bool):
            raise ValueError(
                f"delivers_final_answer must be boolean, got {type(delivers_final_answer)}"
            )
        
        if not isinstance(unique_data_access, bool):
            raise ValueError(
                f"unique_data_access must be boolean, got {type(unique_data_access)}"
            )
        
        if not isinstance(works_under_constraints, bool):
            raise ValueError(
                f"works_under_constraints must be boolean, got {type(works_under_constraints)}"
            )
        
        # Store validated inputs
        self.automation_relevance = automation_relevance
        self.substitute_pressure = substitute_pressure
        self.content_saturation = content_saturation
        self.replaces_human_labor = replaces_human_labor
        self.step_reduction_ratio = step_reduction_ratio
        self.delivers_final_answer = delivers_final_answer
        self.unique_data_access = unique_data_access
        self.works_under_constraints = works_under_constraints


def compute_leverage_flags(leverage_input: LeverageInput) -> List[str]:
    """
    Compute leverage flags using DETERMINISTIC rules (MANDATORY, EXACT).
    
    This is the CORE of Stage 3. All logic must be:
    - Deterministic (same inputs → same outputs)
    - Rule-based (no LLM, no NLP, no ML)
    - Auditable (clear, documented rules)
    - Independent (no external state or side effects)
    
    LEVERAGE RULES (MANDATORY, EXACT):
    
    1. COST_LEVERAGE
       Trigger if:
       - replaces_human_labor == true
       AND
       - automation_relevance == HIGH
    
    2. TIME_LEVERAGE
       Trigger if:
       - step_reduction_ratio >= 5
       OR
       - (automation_relevance == HIGH AND substitute_pressure >= MEDIUM)
    
    3. COGNITIVE_LEVERAGE
       Trigger if:
       - delivers_final_answer == true
       AND
       - content_saturation >= MEDIUM
    
    4. ACCESS_LEVERAGE
       Trigger if:
       - unique_data_access == true
       NOTE: Public or scraped web data does NOT qualify.
    
    5. CONSTRAINT_LEVERAGE
       Trigger if:
       - works_under_constraints == true
    
    Multiple flags may be emitted simultaneously.
    
    Args:
        leverage_input: LeverageInput with validated structured inputs
        
    Returns:
        List of leverage flag strings (may be empty, may contain multiple flags)
    """
    leverage_flags = []
    
    # ========================================================================
    # RULE 1: COST_LEVERAGE
    # ========================================================================
    # Trigger if replaces_human_labor AND automation_relevance == HIGH
    if (leverage_input.replaces_human_labor and 
        leverage_input.automation_relevance == "HIGH"):
        leverage_flags.append("COST_LEVERAGE")
        logger.info(
            "COST_LEVERAGE triggered: replaces_human_labor=true AND "
            "automation_relevance=HIGH"
        )
    
    # ========================================================================
    # RULE 2: TIME_LEVERAGE
    # ========================================================================
    # Trigger if step_reduction_ratio >= 5 OR 
    # (automation_relevance == HIGH AND substitute_pressure >= MEDIUM)
    
    # Part A: step_reduction_ratio >= 5
    step_reduction_trigger = leverage_input.step_reduction_ratio >= 5
    
    # Part B: automation_relevance == HIGH AND substitute_pressure >= MEDIUM
    # Note: substitute_pressure >= MEDIUM means MEDIUM or HIGH
    automation_substitute_trigger = (
        leverage_input.automation_relevance == "HIGH" and
        leverage_input.substitute_pressure in {"MEDIUM", "HIGH"}
    )
    
    if step_reduction_trigger or automation_substitute_trigger:
        leverage_flags.append("TIME_LEVERAGE")
        if step_reduction_trigger:
            logger.info(
                f"TIME_LEVERAGE triggered: step_reduction_ratio={leverage_input.step_reduction_ratio} >= 5"
            )
        if automation_substitute_trigger:
            logger.info(
                f"TIME_LEVERAGE triggered: automation_relevance=HIGH AND "
                f"substitute_pressure={leverage_input.substitute_pressure} (>= MEDIUM)"
            )
    
    # ========================================================================
    # RULE 3: COGNITIVE_LEVERAGE
    # ========================================================================
    # Trigger if delivers_final_answer AND content_saturation >= MEDIUM
    if (leverage_input.delivers_final_answer and
        leverage_input.content_saturation in {"MEDIUM", "HIGH"}):
        leverage_flags.append("COGNITIVE_LEVERAGE")
        logger.info(
            f"COGNITIVE_LEVERAGE triggered: delivers_final_answer=true AND "
            f"content_saturation={leverage_input.content_saturation} (>= MEDIUM)"
        )
    
    # ========================================================================
    # RULE 4: ACCESS_LEVERAGE
    # ========================================================================
    # Trigger if unique_data_access == true
    # NOTE: The determination of whether data is truly "unique" (not public/scraped)
    # is the responsibility of the questioning layer. Stage 3 only checks the flag.
    if leverage_input.unique_data_access:
        leverage_flags.append("ACCESS_LEVERAGE")
        logger.info(
            "ACCESS_LEVERAGE triggered: unique_data_access=true"
        )
    
    # ========================================================================
    # RULE 5: CONSTRAINT_LEVERAGE
    # ========================================================================
    # Trigger if works_under_constraints == true
    if leverage_input.works_under_constraints:
        leverage_flags.append("CONSTRAINT_LEVERAGE")
        logger.info(
            "CONSTRAINT_LEVERAGE triggered: works_under_constraints=true"
        )
    
    # ========================================================================
    # RETURN: Leverage flags (may be empty, may contain multiple flags)
    # ========================================================================
    if not leverage_flags:
        logger.info("No leverage flags triggered")
    else:
        logger.info(f"Leverage flags: {leverage_flags}")
    
    return leverage_flags


def compute_leverage_reality(
    stage2_market_strength: Dict[str, Any],
    user_leverage_inputs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main entry point for Stage 3 leverage computation.
    
    This function:
    1. Extracts required inputs from Stage 2 and user inputs
    2. Validates all inputs
    3. Computes leverage flags using deterministic rules
    4. Returns structured output
    
    CRITICAL: This function is PURE and DETERMINISTIC.
    - No side effects (except logging)
    - No LLM, NLP, or ML
    - Same inputs → same outputs (always)
    
    Args:
        stage2_market_strength: Dict from Stage 2 with market strength parameters
            Required keys: automation_relevance, substitute_pressure, content_saturation
        user_leverage_inputs: Dict with user-provided leverage inputs
            Required keys: replaces_human_labor, step_reduction_ratio,
                          delivers_final_answer, unique_data_access,
                          works_under_constraints
    
    Returns:
        Dict with:
        - leverage_flags: List of str (leverage flags)
        - inputs_used: Dict (for auditability/debugging)
    
    Raises:
        ValueError: If required inputs are missing or invalid
    """
    # Extract and validate Stage 2 inputs
    try:
        automation_relevance = stage2_market_strength["automation_relevance"]
        substitute_pressure = stage2_market_strength["substitute_pressure"]
        content_saturation = stage2_market_strength["content_saturation"]
    except KeyError as e:
        raise ValueError(f"Missing required Stage 2 input: {e}")
    
    # Extract and validate user leverage inputs
    try:
        replaces_human_labor = user_leverage_inputs["replaces_human_labor"]
        step_reduction_ratio = user_leverage_inputs["step_reduction_ratio"]
        delivers_final_answer = user_leverage_inputs["delivers_final_answer"]
        unique_data_access = user_leverage_inputs["unique_data_access"]
        works_under_constraints = user_leverage_inputs["works_under_constraints"]
    except KeyError as e:
        raise ValueError(f"Missing required user leverage input: {e}")
    
    # Create LeverageInput (validates types and values)
    leverage_input = LeverageInput(
        automation_relevance=automation_relevance,
        substitute_pressure=substitute_pressure,
        content_saturation=content_saturation,
        replaces_human_labor=replaces_human_labor,
        step_reduction_ratio=step_reduction_ratio,
        delivers_final_answer=delivers_final_answer,
        unique_data_access=unique_data_access,
        works_under_constraints=works_under_constraints
    )
    
    # Compute leverage flags (deterministic)
    leverage_flags = compute_leverage_flags(leverage_input)
    
    # Return structured output
    return {
        "leverage_flags": leverage_flags,
        "inputs_used": {
            "automation_relevance": automation_relevance,
            "substitute_pressure": substitute_pressure,
            "content_saturation": content_saturation,
            "replaces_human_labor": replaces_human_labor,
            "step_reduction_ratio": step_reduction_ratio,
            "delivers_final_answer": delivers_final_answer,
            "unique_data_access": unique_data_access,
            "works_under_constraints": works_under_constraints
        }
    }
