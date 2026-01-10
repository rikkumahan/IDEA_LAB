"""
Stage 3: Deterministic Leverage Engine

This module implements the CORE logic for leverage detection.
It is PURE, DETERMINISTIC, and RULE-BASED.

CRITICAL CONSTRAINTS:
- NO LLM or NLP allowed in this module
- NO inference from text
- ONLY structured boolean/integer inputs
- Same inputs ALWAYS produce same outputs
- Completely independent of Stages 1 and 2

SUPPORTED LEVERAGE FLAGS (EXHAUSTIVE LIST):
- COST_LEVERAGE
- TIME_LEVERAGE
- COGNITIVE_LEVERAGE
- ACCESS_LEVERAGE
- CONSTRAINT_LEVERAGE

INPUTS (from Stage 2 market reality):
- automation_relevance: "LOW", "MEDIUM", "HIGH"
- substitute_pressure: "LOW", "MEDIUM", "HIGH"
- content_saturation: "LOW", "MEDIUM", "HIGH"

INPUTS (from user, structured only):
- replaces_human_labor: boolean
- step_reduction_ratio: integer >= 0
- delivers_final_answer: boolean
- unique_data_access: boolean
- works_under_constraints: boolean
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# LEVERAGE INPUT VALIDATION
# ============================================================================

def validate_leverage_inputs(
    # User leverage inputs (structured)
    replaces_human_labor: bool,
    step_reduction_ratio: int,
    delivers_final_answer: bool,
    unique_data_access: bool,
    works_under_constraints: bool,
    # Market inputs (from Stage 2)
    automation_relevance: str,
    substitute_pressure: str,
    content_saturation: str
) -> Dict[str, Any]:
    """
    Validate all leverage inputs before processing.
    
    This is a DEFENSIVE programming layer that catches invalid inputs
    before they reach the leverage detection rules.
    
    TYPE VALIDATION:
    - Boolean fields must be True or False (not None, not string)
    - Integer fields must be integers >= 0 (not None, not float)
    - Enum fields must be valid enum values
    
    SANITY VALIDATION:
    - step_reduction_ratio == 0 AND automation_relevance == HIGH is suspicious
    - null or ambiguous values are rejected
    
    Args:
        All leverage inputs (user + market)
        
    Returns:
        Dict with validation result:
        {
            "valid": True/False,
            "errors": List of error messages (empty if valid)
        }
    """
    errors = []
    
    # TYPE VALIDATION: User inputs
    if not isinstance(replaces_human_labor, bool):
        errors.append(f"replaces_human_labor must be boolean, got {type(replaces_human_labor).__name__}")
    
    if not isinstance(step_reduction_ratio, int):
        errors.append(f"step_reduction_ratio must be integer, got {type(step_reduction_ratio).__name__}")
    elif step_reduction_ratio < 0:
        errors.append(f"step_reduction_ratio must be >= 0, got {step_reduction_ratio}")
    
    if not isinstance(delivers_final_answer, bool):
        errors.append(f"delivers_final_answer must be boolean, got {type(delivers_final_answer).__name__}")
    
    if not isinstance(unique_data_access, bool):
        errors.append(f"unique_data_access must be boolean, got {type(unique_data_access).__name__}")
    
    if not isinstance(works_under_constraints, bool):
        errors.append(f"works_under_constraints must be boolean, got {type(works_under_constraints).__name__}")
    
    # TYPE VALIDATION: Market inputs (enum values)
    valid_levels = {"LOW", "MEDIUM", "HIGH"}
    
    if automation_relevance not in valid_levels:
        errors.append(f"automation_relevance must be one of {valid_levels}, got '{automation_relevance}'")
    
    if substitute_pressure not in valid_levels:
        errors.append(f"substitute_pressure must be one of {valid_levels}, got '{substitute_pressure}'")
    
    if content_saturation not in valid_levels:
        errors.append(f"content_saturation must be one of {valid_levels}, got '{content_saturation}'")
    
    # SANITY VALIDATION: Check for suspicious combinations
    # If type validation passed, perform sanity checks
    if not errors:
        # Sanity check: step_reduction_ratio == 0 should mean LOW automation_relevance
        if step_reduction_ratio == 0 and automation_relevance == "HIGH":
            errors.append(
                "Sanity check failed: step_reduction_ratio is 0 but automation_relevance is HIGH. "
                "If the solution doesn't reduce steps, automation shouldn't be highly relevant."
            )
    
    # Return validation result
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


# ============================================================================
# DETERMINISTIC LEVERAGE RULES
# ============================================================================
# These functions implement the EXACT leverage detection rules specified
# in the requirements. They are PURE functions with NO side effects.
# ============================================================================

def detect_cost_leverage(
    replaces_human_labor: bool,
    automation_relevance: str
) -> bool:
    """
    RULE 1: COST_LEVERAGE
    
    Trigger if:
    - replaces_human_labor == True
    AND
    - automation_relevance == HIGH
    
    REASONING:
    Cost leverage comes from replacing expensive human labor with automation.
    Only triggers when automation is HIGHLY relevant to the solution.
    
    Args:
        replaces_human_labor: Does solution replace human labor?
        automation_relevance: How relevant is automation? (LOW/MEDIUM/HIGH)
        
    Returns:
        True if COST_LEVERAGE should be flagged, False otherwise
    """
    result = replaces_human_labor and automation_relevance == "HIGH"
    
    if result:
        logger.info(
            "COST_LEVERAGE detected: "
            f"replaces_human_labor={replaces_human_labor}, "
            f"automation_relevance={automation_relevance}"
        )
    
    return result


def detect_time_leverage(
    step_reduction_ratio: int,
    automation_relevance: str,
    substitute_pressure: str
) -> bool:
    """
    RULE 2: TIME_LEVERAGE
    
    Trigger if:
    - step_reduction_ratio >= 5
    OR
    - (automation_relevance == HIGH AND substitute_pressure >= MEDIUM)
    
    REASONING:
    Time leverage comes from significantly reducing steps (5+ reduction)
    OR from high automation in markets with substitute pressure (indicating
    users are actively seeking time-saving alternatives).
    
    Args:
        step_reduction_ratio: How many steps does solution reduce?
        automation_relevance: How relevant is automation?
        substitute_pressure: Market pressure from substitutes (LOW/MEDIUM/HIGH)
        
    Returns:
        True if TIME_LEVERAGE should be flagged, False otherwise
    """
    # Condition 1: Significant step reduction (5+)
    condition1 = step_reduction_ratio >= 5
    
    # Condition 2: High automation + medium/high substitute pressure
    condition2 = (
        automation_relevance == "HIGH" and
        substitute_pressure in ["MEDIUM", "HIGH"]
    )
    
    result = condition1 or condition2
    
    if result:
        logger.info(
            "TIME_LEVERAGE detected: "
            f"step_reduction_ratio={step_reduction_ratio}, "
            f"automation_relevance={automation_relevance}, "
            f"substitute_pressure={substitute_pressure}, "
            f"condition1={condition1}, condition2={condition2}"
        )
    
    return result


def detect_cognitive_leverage(
    delivers_final_answer: bool,
    content_saturation: str
) -> bool:
    """
    RULE 3: COGNITIVE_LEVERAGE
    
    Trigger if:
    - delivers_final_answer == True
    AND
    - content_saturation >= MEDIUM
    
    REASONING:
    Cognitive leverage comes from delivering final answers (reducing mental load)
    in spaces where content exists but doesn't provide direct answers.
    Medium/high content saturation indicates the problem is discussed but
    not necessarily solved with actionable answers.
    
    Args:
        delivers_final_answer: Does solution deliver final answer (vs partial info)?
        content_saturation: Amount of content about this solution (LOW/MEDIUM/HIGH)
        
    Returns:
        True if COGNITIVE_LEVERAGE should be flagged, False otherwise
    """
    result = delivers_final_answer and content_saturation in ["MEDIUM", "HIGH"]
    
    if result:
        logger.info(
            "COGNITIVE_LEVERAGE detected: "
            f"delivers_final_answer={delivers_final_answer}, "
            f"content_saturation={content_saturation}"
        )
    
    return result


def detect_access_leverage(
    unique_data_access: bool
) -> bool:
    """
    RULE 4: ACCESS_LEVERAGE
    
    Trigger if:
    - unique_data_access == True
    
    NOTE: Public or scraped web data does NOT qualify.
    This must be truly unique/proprietary data.
    
    REASONING:
    Access leverage comes from exclusive access to data/resources
    that competitors cannot easily replicate.
    
    Args:
        unique_data_access: Does solution have unique/proprietary data access?
        
    Returns:
        True if ACCESS_LEVERAGE should be flagged, False otherwise
    """
    result = unique_data_access
    
    if result:
        logger.info(
            "ACCESS_LEVERAGE detected: "
            f"unique_data_access={unique_data_access}"
        )
    
    return result


def detect_constraint_leverage(
    works_under_constraints: bool
) -> bool:
    """
    RULE 5: CONSTRAINT_LEVERAGE
    
    Trigger if:
    - works_under_constraints == True
    
    REASONING:
    Constraint leverage comes from working in environments where
    competitors cannot operate (regulatory, technical, or physical constraints).
    
    Args:
        works_under_constraints: Does solution work under special constraints?
        
    Returns:
        True if CONSTRAINT_LEVERAGE should be flagged, False otherwise
    """
    result = works_under_constraints
    
    if result:
        logger.info(
            "CONSTRAINT_LEVERAGE detected: "
            f"works_under_constraints={works_under_constraints}"
        )
    
    return result


# ============================================================================
# MAIN LEVERAGE DETECTION FUNCTION
# ============================================================================

def detect_leverage_flags(
    # User leverage inputs (structured only, NO free text)
    replaces_human_labor: bool,
    step_reduction_ratio: int,
    delivers_final_answer: bool,
    unique_data_access: bool,
    works_under_constraints: bool,
    # Market inputs (from Stage 2)
    automation_relevance: str,
    substitute_pressure: str,
    content_saturation: str
) -> Dict[str, Any]:
    """
    Detect all applicable leverage flags using deterministic rules.
    
    This is the MAIN ENTRY POINT for Stage 3 leverage detection.
    
    PROCESS:
    1. Validate all inputs (type + sanity checks)
    2. Apply each leverage detection rule independently
    3. Collect all triggered leverage flags
    4. Return structured output
    
    CRITICAL GUARANTEES:
    - Same inputs ALWAYS produce same outputs (deterministic)
    - NO LLM or NLP allowed
    - NO text inference
    - Multiple flags may be emitted simultaneously
    - Empty flag list is valid (no leverage detected)
    
    Args:
        User inputs (structured):
            replaces_human_labor: Does solution replace human labor?
            step_reduction_ratio: How many steps does solution reduce? (integer >= 0)
            delivers_final_answer: Does solution deliver final answer?
            unique_data_access: Does solution have unique data access?
            works_under_constraints: Does solution work under constraints?
        
        Market inputs (from Stage 2):
            automation_relevance: How relevant is automation? (LOW/MEDIUM/HIGH)
            substitute_pressure: Pressure from substitutes (LOW/MEDIUM/HIGH)
            content_saturation: Content about solution (LOW/MEDIUM/HIGH)
    
    Returns:
        Dict with:
        {
            "leverage_flags": List[str],  # List of detected flags
            "leverage_details": Dict,      # Per-flag detection details
            "validation": Dict             # Input validation results
        }
    """
    # ========================================================================
    # STEP 1: Validate inputs
    # ========================================================================
    validation_result = validate_leverage_inputs(
        replaces_human_labor=replaces_human_labor,
        step_reduction_ratio=step_reduction_ratio,
        delivers_final_answer=delivers_final_answer,
        unique_data_access=unique_data_access,
        works_under_constraints=works_under_constraints,
        automation_relevance=automation_relevance,
        substitute_pressure=substitute_pressure,
        content_saturation=content_saturation
    )
    
    # If validation fails, return error immediately
    if not validation_result["valid"]:
        logger.error(f"Leverage input validation failed: {validation_result['errors']}")
        return {
            "leverage_flags": [],
            "leverage_details": {},
            "validation": validation_result,
            "error": "Input validation failed"
        }
    
    # ========================================================================
    # STEP 2: Apply each leverage detection rule independently
    # ========================================================================
    # Each rule is a pure function that returns True/False
    # Rules are applied independently (no dependencies between them)
    
    leverage_flags = []
    leverage_details = {}
    
    # Rule 1: COST_LEVERAGE
    if detect_cost_leverage(replaces_human_labor, automation_relevance):
        leverage_flags.append("COST_LEVERAGE")
        leverage_details["COST_LEVERAGE"] = {
            "triggered": True,
            "reason": "Replaces human labor with high automation relevance"
        }
    
    # Rule 2: TIME_LEVERAGE
    if detect_time_leverage(step_reduction_ratio, automation_relevance, substitute_pressure):
        leverage_flags.append("TIME_LEVERAGE")
        leverage_details["TIME_LEVERAGE"] = {
            "triggered": True,
            "reason": (
                f"Step reduction ratio is {step_reduction_ratio} (>= 5 triggers) "
                f"OR high automation with medium/high substitute pressure"
            )
        }
    
    # Rule 3: COGNITIVE_LEVERAGE
    if detect_cognitive_leverage(delivers_final_answer, content_saturation):
        leverage_flags.append("COGNITIVE_LEVERAGE")
        leverage_details["COGNITIVE_LEVERAGE"] = {
            "triggered": True,
            "reason": "Delivers final answer with medium/high content saturation"
        }
    
    # Rule 4: ACCESS_LEVERAGE
    if detect_access_leverage(unique_data_access):
        leverage_flags.append("ACCESS_LEVERAGE")
        leverage_details["ACCESS_LEVERAGE"] = {
            "triggered": True,
            "reason": "Has unique/proprietary data access"
        }
    
    # Rule 5: CONSTRAINT_LEVERAGE
    if detect_constraint_leverage(works_under_constraints):
        leverage_flags.append("CONSTRAINT_LEVERAGE")
        leverage_details["CONSTRAINT_LEVERAGE"] = {
            "triggered": True,
            "reason": "Works under special constraints"
        }
    
    # ========================================================================
    # STEP 3: Return structured output
    # ========================================================================
    logger.info(
        f"Stage 3 leverage detection complete: {len(leverage_flags)} flag(s) detected - "
        f"{leverage_flags if leverage_flags else 'NONE'}"
    )
    
    return {
        "leverage_flags": leverage_flags,
        "leverage_details": leverage_details,
        "validation": validation_result
    }


# ============================================================================
# AUDIT FUNCTION: Verify determinism
# ============================================================================

def audit_determinism(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Audit function to verify that leverage detection is deterministic.
    
    This runs the same inputs through detect_leverage_flags() multiple times
    and verifies that the output is identical each time.
    
    USAGE:
    This should be called in test suites to verify Stage 3 determinism.
    
    Args:
        test_cases: List of test input dictionaries
        
    Returns:
        Audit report with pass/fail status
    """
    audit_results = {
        "deterministic": True,
        "test_count": len(test_cases),
        "failed_cases": []
    }
    
    for i, test_case in enumerate(test_cases):
        # Run same inputs 3 times
        results = []
        for _ in range(3):
            result = detect_leverage_flags(**test_case)
            # Convert to tuple for comparison (lists aren't hashable)
            results.append(tuple(result["leverage_flags"]))
        
        # Verify all results are identical
        if not all(r == results[0] for r in results):
            audit_results["deterministic"] = False
            audit_results["failed_cases"].append({
                "case_index": i,
                "inputs": test_case,
                "results": results
            })
    
    return audit_results
