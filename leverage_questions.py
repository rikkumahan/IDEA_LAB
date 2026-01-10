"""
Leverage Questioning Layer: Safe Input Collection for Stage 3

This module collects structured leverage inputs safely, with optional LLM assistance
for question wording ONLY.

ARCHITECTURE:
1. CANONICAL QUESTIONS: Immutable source of truth (semantic meaning + type)
2. LLM WORDING ADAPTER: Optionally rewrites wording (meaning unchanged)
3. DUAL VALIDATION: Type validation + Sanity validation
4. FIREWALL: LLM output NEVER reaches Stage 3

CRITICAL CONSTRAINTS:
- LLM is used ONLY for question wording (optional)
- LLM must NOT change meaning
- LLM must NOT suggest answers
- LLM must NOT add bias
- Structured answers only (boolean/integer)
- No free text reaches Stage 3
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CANONICAL QUESTION DEFINITIONS (SOURCE OF TRUTH)
# ============================================================================
# These definitions are IMMUTABLE.
# They define the exact semantic meaning and expected answer type.
# LLM may reword these, but MUST preserve the exact meaning.
# ============================================================================

CANONICAL_QUESTIONS = {
    "replaces_human_labor": {
        "id": "replaces_human_labor",
        "canonical_wording": (
            "Does your solution replace work that is currently done by humans?"
        ),
        "semantic_meaning": (
            "Determine if the solution automates or replaces tasks that humans "
            "currently perform manually. This is about labor substitution, not "
            "augmentation or assistance."
        ),
        "answer_type": "boolean",
        "examples": {
            True: "Automated data entry replacing manual typing",
            False: "Tool that helps humans work faster (augmentation, not replacement)"
        },
        "sanity_check": None  # No cross-field dependency
    },
    
    "step_reduction_ratio": {
        "id": "step_reduction_ratio",
        "canonical_wording": (
            "How many manual steps does your solution eliminate or reduce? "
            "(Enter a number: 0 if no reduction, or positive integer for number of steps reduced)"
        ),
        "semantic_meaning": (
            "Count the number of distinct manual steps or actions that users "
            "NO LONGER need to perform. If solution adds steps, enter 0. "
            "This is a concrete count, not a percentage or relative measure."
        ),
        "answer_type": "integer",
        "examples": {
            0: "No step reduction (solution may improve quality but not reduce steps)",
            3: "Reduces 10-step process to 7 steps (3 steps eliminated)",
            10: "Eliminates 10 manual steps entirely"
        },
        "sanity_check": "automation_relevance"  # Cross-validate with market data
    },
    
    "delivers_final_answer": {
        "id": "delivers_final_answer",
        "canonical_wording": (
            "Does your solution provide a complete, actionable answer "
            "that requires no further analysis or decision-making?"
        ),
        "semantic_meaning": (
            "Determine if the solution delivers a FINAL, ACTIONABLE answer "
            "versus partial information, analysis, or recommendations that "
            "still require human interpretation/decision-making."
        ),
        "answer_type": "boolean",
        "examples": {
            True: "Solution outputs 'Approved' or 'Rejected' with no further action needed",
            False: "Solution provides data/analysis that user must interpret to make decision"
        },
        "sanity_check": None
    },
    
    "unique_data_access": {
        "id": "unique_data_access",
        "canonical_wording": (
            "Does your solution have access to proprietary or exclusive data "
            "that is NOT publicly available or easily scraped from the web?"
        ),
        "semantic_meaning": (
            "Determine if the solution has unique data access advantage. "
            "Public data, web scraping, and open APIs do NOT qualify. "
            "This must be truly proprietary/exclusive data."
        ),
        "answer_type": "boolean",
        "examples": {
            True: "Exclusive partnership with data provider, proprietary dataset",
            False: "Uses public APIs, web scraping, or generally available data"
        },
        "sanity_check": None
    },
    
    "works_under_constraints": {
        "id": "works_under_constraints",
        "canonical_wording": (
            "Does your solution work in environments with special constraints "
            "where most competitors cannot operate? "
            "(e.g., regulatory, offline, low-bandwidth, high-security)"
        ),
        "semantic_meaning": (
            "Determine if the solution operates under special constraints that "
            "create barriers to competition. This could be regulatory compliance, "
            "offline operation, extreme performance requirements, etc."
        ),
        "answer_type": "boolean",
        "examples": {
            True: "Works offline in high-security environments, HIPAA-compliant for healthcare",
            False: "Standard web application with no special constraints"
        },
        "sanity_check": None
    }
}


# ============================================================================
# LLM WORDING ADAPTER (OPTIONAL, CONSTRAINED)
# ============================================================================

def get_llm_adapted_question(
    question_id: str,
    llm_client: Optional[Any] = None,
    user_context: Optional[Dict[str, str]] = None
) -> str:
    """
    Optionally adapt question wording using LLM (WORDING ONLY, meaning unchanged).
    
    LLM CONSTRAINTS (enforced in prompt):
    - Rewrite wording only
    - Do NOT change meaning
    - Do NOT suggest answers
    - Do NOT add biasing examples
    - Do NOT mention leverage, advantage, or competition
    
    If LLM is unavailable or fails, returns canonical wording (safe fallback).
    
    Args:
        question_id: ID of canonical question
        llm_client: Optional LLM client (if None, returns canonical wording)
        user_context: Optional context (e.g., industry, solution type) for adaptation
        
    Returns:
        Adapted question wording (or canonical wording if LLM unavailable)
    """
    # Get canonical question definition
    if question_id not in CANONICAL_QUESTIONS:
        logger.error(f"Unknown question_id: {question_id}")
        return f"[ERROR: Unknown question {question_id}]"
    
    canonical_q = CANONICAL_QUESTIONS[question_id]
    canonical_wording = canonical_q["canonical_wording"]
    
    # If no LLM client provided, return canonical wording
    if llm_client is None:
        logger.debug(f"No LLM client provided, using canonical wording for {question_id}")
        return canonical_wording
    
    # Build LLM prompt with STRICT constraints
    try:
        system_prompt = (
            "You are a question rewording assistant.\n"
            "STRICT RULES:\n"
            "- Rewrite question wording ONLY (improve clarity/readability)\n"
            "- Do NOT change the semantic meaning\n"
            "- Do NOT suggest answers or provide examples\n"
            "- Do NOT add biasing language\n"
            "- Do NOT mention 'leverage', 'advantage', or 'competition'\n"
            "- Keep the question neutral and factual\n"
            "- Preserve the question type (yes/no or numeric)\n"
        )
        
        user_prompt_parts = [
            f"Original question: {canonical_wording}",
            f"Semantic meaning (preserve this): {canonical_q['semantic_meaning']}",
            f"Answer type (preserve this): {canonical_q['answer_type']}",
        ]
        
        if user_context:
            user_prompt_parts.append(f"Context for adaptation: {user_context}")
        
        user_prompt_parts.append(
            "\nRewrite the question for better clarity while preserving exact meaning. "
            "Return ONLY the rewritten question, nothing else."
        )
        
        user_prompt = "\n\n".join(user_prompt_parts)
        
        # Call LLM (implementation depends on llm_client interface)
        # Assuming llm_client has a .generate() or similar method
        adapted_wording = llm_client.reword_question(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        # Validate LLM output (basic sanity checks)
        if not adapted_wording or len(adapted_wording) < 10:
            logger.warning(f"LLM returned invalid wording for {question_id}, using canonical")
            return canonical_wording
        
        # Check if LLM violated constraints (basic keyword check)
        forbidden_keywords = ["leverage", "advantage", "competitive", "edge", "moat"]
        if any(keyword in adapted_wording.lower() for keyword in forbidden_keywords):
            logger.warning(
                f"LLM output contains forbidden keywords for {question_id}, using canonical"
            )
            return canonical_wording
        
        logger.info(f"LLM adapted wording for {question_id}: {adapted_wording[:50]}...")
        return adapted_wording
        
    except Exception as e:
        logger.warning(f"LLM wording adaptation failed for {question_id}: {e}, using canonical")
        return canonical_wording


# ============================================================================
# INPUT VALIDATION (DUAL: TYPE + SANITY)
# ============================================================================

def validate_answer_type(question_id: str, answer: Any) -> Dict[str, Any]:
    """
    Validate answer type matches expected type for question.
    
    TYPE VALIDATION:
    - Boolean questions: answer must be True or False (not None, not string)
    - Integer questions: answer must be int >= 0 (not None, not float, not string)
    
    Args:
        question_id: ID of canonical question
        answer: User's answer to validate
        
    Returns:
        Dict with validation result:
        {
            "valid": True/False,
            "error": Error message if invalid (None if valid)
        }
    """
    if question_id not in CANONICAL_QUESTIONS:
        return {
            "valid": False,
            "error": f"Unknown question_id: {question_id}"
        }
    
    expected_type = CANONICAL_QUESTIONS[question_id]["answer_type"]
    
    # TYPE VALIDATION: Boolean
    if expected_type == "boolean":
        if not isinstance(answer, bool):
            return {
                "valid": False,
                "error": (
                    f"Expected boolean answer (True/False), "
                    f"got {type(answer).__name__}: {answer}"
                )
            }
        return {"valid": True, "error": None}
    
    # TYPE VALIDATION: Integer
    elif expected_type == "integer":
        if not isinstance(answer, int):
            return {
                "valid": False,
                "error": (
                    f"Expected integer answer, "
                    f"got {type(answer).__name__}: {answer}"
                )
            }
        if answer < 0:
            return {
                "valid": False,
                "error": f"Integer answer must be >= 0, got {answer}"
            }
        return {"valid": True, "error": None}
    
    # Unknown type (should never happen)
    else:
        return {
            "valid": False,
            "error": f"Unknown expected type: {expected_type}"
        }


def validate_answer_sanity(
    question_id: str,
    answer: Any,
    market_data: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Perform sanity checks on answer (cross-field validation).
    
    SANITY CHECKS:
    - step_reduction_ratio == 0 → automation_relevance should NOT be HIGH
    - null or ambiguous answers are rejected
    
    Args:
        question_id: ID of canonical question
        answer: User's answer (already type-validated)
        market_data: Optional market data from Stage 2 (for cross-validation)
        
    Returns:
        Dict with validation result:
        {
            "valid": True/False,
            "warning": Warning message if suspicious (None if okay)
        }
    """
    if question_id not in CANONICAL_QUESTIONS:
        return {"valid": True, "warning": None}  # Skip sanity check if question unknown
    
    sanity_check_field = CANONICAL_QUESTIONS[question_id].get("sanity_check")
    
    # No sanity check defined for this question
    if not sanity_check_field:
        return {"valid": True, "warning": None}
    
    # SANITY CHECK: step_reduction_ratio with automation_relevance
    if question_id == "step_reduction_ratio" and market_data:
        automation_relevance = market_data.get("automation_relevance")
        
        if answer == 0 and automation_relevance == "HIGH":
            return {
                "valid": False,
                "warning": (
                    "Sanity check failed: You indicated 0 step reduction, "
                    "but market data shows HIGH automation relevance. "
                    "If your solution doesn't reduce steps, automation shouldn't be highly relevant. "
                    "Please review your answer."
                )
            }
    
    return {"valid": True, "warning": None}


# ============================================================================
# MAIN QUESTIONING FLOW
# ============================================================================

def collect_leverage_inputs(
    llm_client: Optional[Any] = None,
    user_context: Optional[Dict[str, str]] = None,
    market_data: Optional[Dict[str, str]] = None,
    user_answers: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Collect all leverage inputs with validation and optional LLM wording adaptation.
    
    PROCESS:
    1. For each canonical question:
       a. Optionally adapt wording using LLM (if provided)
       b. Get user answer (from user_answers dict)
       c. Validate answer type
       d. Validate answer sanity (cross-field checks)
       e. On validation failure → return error with question for re-asking
    2. Return validated structured inputs (ready for Stage 3)
    
    FIREWALL: LLM output (adapted wording) NEVER flows into Stage 3.
    Only validated structured answers reach Stage 3.
    
    Args:
        llm_client: Optional LLM client for question wording adaptation
        user_context: Optional context for LLM adaptation
        market_data: Optional market data from Stage 2 (for sanity checks)
        user_answers: Dict mapping question_id to user's answer
        
    Returns:
        Dict with either:
        - Success: {"success": True, "inputs": {...validated inputs...}}
        - Failure: {"success": False, "error": "...", "question_to_reask": "..."}
    """
    if user_answers is None:
        user_answers = {}
    
    validated_inputs = {}
    questions_asked = []
    
    # Process each canonical question in order
    for question_id in CANONICAL_QUESTIONS.keys():
        canonical_q = CANONICAL_QUESTIONS[question_id]
        
        # ====================================================================
        # STEP 1: Get question wording (optionally LLM-adapted)
        # ====================================================================
        question_wording = get_llm_adapted_question(
            question_id=question_id,
            llm_client=llm_client,
            user_context=user_context
        )
        
        questions_asked.append({
            "id": question_id,
            "wording": question_wording,
            "answer_type": canonical_q["answer_type"]
        })
        
        # ====================================================================
        # STEP 2: Get user answer
        # ====================================================================
        if question_id not in user_answers:
            # Answer missing - return error with question to ask
            return {
                "success": False,
                "error": f"Missing answer for question: {question_id}",
                "question_to_ask": {
                    "id": question_id,
                    "wording": question_wording,
                    "answer_type": canonical_q["answer_type"]
                }
            }
        
        answer = user_answers[question_id]
        
        # ====================================================================
        # STEP 3: Validate answer TYPE
        # ====================================================================
        type_validation = validate_answer_type(question_id, answer)
        
        if not type_validation["valid"]:
            # Type validation failed - return error with question to re-ask
            return {
                "success": False,
                "error": type_validation["error"],
                "question_to_reask": {
                    "id": question_id,
                    "wording": question_wording,
                    "answer_type": canonical_q["answer_type"],
                    "previous_invalid_answer": answer
                }
            }
        
        # ====================================================================
        # STEP 4: Validate answer SANITY
        # ====================================================================
        sanity_validation = validate_answer_sanity(
            question_id=question_id,
            answer=answer,
            market_data=market_data
        )
        
        if not sanity_validation["valid"]:
            # Sanity validation failed - return warning with question to re-ask
            return {
                "success": False,
                "error": sanity_validation["warning"],
                "question_to_reask": {
                    "id": question_id,
                    "wording": question_wording,
                    "answer_type": canonical_q["answer_type"],
                    "previous_suspicious_answer": answer
                }
            }
        
        # ====================================================================
        # STEP 5: Store validated answer
        # ====================================================================
        validated_inputs[question_id] = answer
        logger.info(f"Question {question_id} answered and validated: {answer}")
    
    # All questions answered and validated successfully
    logger.info(
        f"All {len(validated_inputs)} leverage questions answered and validated successfully"
    )
    
    return {
        "success": True,
        "inputs": validated_inputs,
        "questions_asked": questions_asked  # For audit trail
    }


# ============================================================================
# CONVENIENCE FUNCTION: Direct Stage 3 Input Format
# ============================================================================

def format_for_stage3(validated_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format validated inputs into Stage 3 function signature.
    
    This is a convenience function that maps validated question answers
    to the exact parameter names expected by Stage 3.
    
    Args:
        validated_inputs: Dict from collect_leverage_inputs()["inputs"]
        
    Returns:
        Dict ready to be unpacked as kwargs for stage3_leverage.detect_leverage_flags()
    """
    return {
        "replaces_human_labor": validated_inputs["replaces_human_labor"],
        "step_reduction_ratio": validated_inputs["step_reduction_ratio"],
        "delivers_final_answer": validated_inputs["delivers_final_answer"],
        "unique_data_access": validated_inputs["unique_data_access"],
        "works_under_constraints": validated_inputs["works_under_constraints"]
    }
