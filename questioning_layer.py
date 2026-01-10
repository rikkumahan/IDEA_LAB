"""
QUESTIONING LAYER: Safe Input Collection for Stage 3

This module safely collects structured leverage inputs from users.
It uses LLM ONLY for wording adaptation, never for logic or decisions.

CRITICAL CONSTRAINTS:
- LLM can rewrite wording ONLY (never change meaning)
- All answers must be structured (boolean or integer)
- No free text reaches Stage 3
- Dual validation (type + sanity checks)
- Firewall prevents LLM leakage into Stage 3

INPUTS REQUIRED (FIXED):
- replaces_human_labor: bool
- step_reduction_ratio: int (>= 0)
- delivers_final_answer: bool
- unique_data_access: bool
- works_under_constraints: bool

OUTPUTS:
- Validated structured inputs ready for Stage 3
"""

import logging
from typing import Dict, Any, Optional
from llm_factory import get_llm_client

logger = logging.getLogger(__name__)


# ============================================================================
# CANONICAL QUESTIONS (SOURCE OF TRUTH)
# ============================================================================
# These definitions are the single source of truth for what each input means.
# LLM may rewrite wording, but CANNOT change these semantic meanings.
# ============================================================================

CANONICAL_QUESTIONS = {
    "replaces_human_labor": {
        "id": "replaces_human_labor",
        "semantic_meaning": (
            "Does your solution replace or eliminate work that would otherwise "
            "be done by a human? This means automating tasks that currently "
            "require human time and effort, NOT augmenting or assisting humans."
        ),
        "expected_type": "boolean",
        "examples": {
            "yes": [
                "Automatically processes invoices (no human data entry needed)",
                "Generates reports without human involvement",
                "Schedules meetings without a human scheduler"
            ],
            "no": [
                "Provides recommendations but human makes final decision",
                "Assists human with research but doesn't replace them",
                "Speeds up human work but human still does the task"
            ]
        }
    },
    
    "step_reduction_ratio": {
        "id": "step_reduction_ratio",
        "semantic_meaning": (
            "How many manual steps or actions does your solution eliminate? "
            "Count the number of steps a user would need to do manually "
            "that your solution does automatically. Enter 0 if your solution "
            "doesn't eliminate steps but improves them."
        ),
        "expected_type": "integer",
        "examples": {
            "high": [
                "Manual process: 20 steps → Your solution: 1 step → Answer: 19",
                "Manual: 10 clicks → Your solution: 0 clicks → Answer: 10"
            ],
            "medium": [
                "Manual: 8 steps → Your solution: 3 steps → Answer: 5"
            ],
            "low": [
                "Manual: 5 steps → Your solution: 2 steps → Answer: 3",
                "No step reduction, just faster → Answer: 0"
            ]
        }
    },
    
    "delivers_final_answer": {
        "id": "delivers_final_answer",
        "semantic_meaning": (
            "Does your solution provide a complete, actionable answer that "
            "requires no further processing, research, or decision-making? "
            "The user should be able to use the output directly without "
            "additional work or interpretation."
        ),
        "expected_type": "boolean",
        "examples": {
            "yes": [
                "Generates a complete report ready to share",
                "Provides validated startup idea with go/no-go decision",
                "Outputs final invoice ready to send"
            ],
            "no": [
                "Provides insights that user must interpret",
                "Gives recommendations user must choose from",
                "Outputs data that needs further processing"
            ]
        }
    },
    
    "unique_data_access": {
        "id": "unique_data_access",
        "semantic_meaning": (
            "Does your solution use proprietary, exclusive, or non-public data "
            "that competitors cannot easily access? This means data you own, "
            "data from exclusive partnerships, or data that requires special "
            "access. Public data, scraped data, and openly available APIs "
            "do NOT qualify."
        ),
        "expected_type": "boolean",
        "examples": {
            "yes": [
                "Proprietary database you've built over years",
                "Exclusive partnership with data provider",
                "Private customer data (with permission)",
                "Unique sensors or hardware collecting data"
            ],
            "no": [
                "Public APIs (Google, Twitter, etc.)",
                "Web scraping publicly available data",
                "Open datasets anyone can access",
                "Data available through standard paid APIs"
            ]
        }
    },
    
    "works_under_constraints": {
        "id": "works_under_constraints",
        "semantic_meaning": (
            "Does your solution specifically work in constrained environments "
            "where other solutions fail? This means handling limitations like "
            "poor connectivity, low resources, strict regulations, or extreme "
            "conditions that prevent alternatives from working."
        ),
        "expected_type": "boolean",
        "examples": {
            "yes": [
                "Works offline when internet is unavailable",
                "Runs on low-powered devices (old phones, embedded systems)",
                "Complies with strict regulations (HIPAA, GDPR, military)",
                "Operates in extreme conditions (temperature, remote locations)"
            ],
            "no": [
                "Works better than others but in normal conditions",
                "More efficient but doesn't handle special constraints",
                "Standard online solution requiring good connectivity"
            ]
        }
    }
}


# ============================================================================
# LLM WORDING ADAPTATION
# ============================================================================
# LLM is used ONLY to adapt question wording for clarity/context.
# LLM MUST NOT change meaning, suggest answers, or add bias.
# ============================================================================

LLM_WORDING_PROMPT_TEMPLATE = """You are a question wording assistant. Your ONLY job is to rewrite the wording of a question to make it clearer and more natural.

STRICT RULES:
1. Rewrite wording only - do NOT change the semantic meaning
2. Do NOT suggest answers or provide hints about what answer is "better"
3. Do NOT mention leverage, advantage, or competition
4. Do NOT add biasing examples
5. Keep the question neutral and factual
6. The rewritten question should ask for the SAME information as the original

ORIGINAL QUESTION:
{canonical_question}

SEMANTIC MEANING (DO NOT CHANGE):
{semantic_meaning}

EXPECTED ANSWER TYPE: {expected_type}

Rewrite the question to be clearer and more natural while preserving the exact semantic meaning.
Output ONLY the rewritten question, nothing else.
"""


def adapt_question_wording(question_id: str, use_llm: bool = True) -> str:
    """
    Adapt question wording using LLM (if enabled) or use canonical wording.
    
    LLM is instructed to:
    - Rewrite wording only
    - Do NOT change meaning
    - Do NOT suggest answers
    - Do NOT add biasing examples
    - Do NOT mention leverage, advantage, or competition
    
    FIREWALL: LLM output is ONLY used for display, never for logic.
    If LLM fails or is disabled, canonical wording is used.
    
    Args:
        question_id: ID of the canonical question
        use_llm: Whether to use LLM for wording adaptation
        
    Returns:
        Question text (LLM-adapted or canonical)
    """
    if question_id not in CANONICAL_QUESTIONS:
        raise ValueError(f"Unknown question_id: {question_id}")
    
    canonical = CANONICAL_QUESTIONS[question_id]
    canonical_question = canonical["semantic_meaning"]
    
    # If LLM disabled, use canonical wording
    if not use_llm:
        logger.info(f"LLM disabled - using canonical wording for {question_id}")
        return canonical_question
    
    # Try to adapt wording with LLM
    try:
        llm = get_llm_client()
        
        # Format prompt with strict constraints
        prompt = LLM_WORDING_PROMPT_TEMPLATE.format(
            canonical_question=canonical_question,
            semantic_meaning=canonical["semantic_meaning"],
            expected_type=canonical["expected_type"]
        )
        
        # Get LLM response
        adapted_question = llm.complete(prompt, max_tokens=200)
        
        # Clean up response (remove quotes, extra whitespace)
        adapted_question = adapted_question.strip().strip('"').strip()
        
        # Fallback to canonical if LLM returns empty/invalid
        if not adapted_question or len(adapted_question) < 10:
            logger.warning(
                f"LLM returned invalid wording for {question_id} - using canonical"
            )
            return canonical_question
        
        logger.info(f"LLM adapted wording for {question_id}")
        return adapted_question
        
    except Exception as e:
        # Fallback to canonical on any error
        logger.warning(f"LLM wording adaptation failed for {question_id}: {e}")
        logger.info("Falling back to canonical wording")
        return canonical_question


# ============================================================================
# DUAL VALIDATION
# ============================================================================
# All inputs must pass BOTH type validation AND sanity validation.
# Invalid inputs trigger re-asking the question.
# ============================================================================

def validate_type(question_id: str, answer: Any) -> tuple[bool, Optional[str]]:
    """
    Validate that answer has the correct type.
    
    Returns:
        (is_valid, error_message)
    """
    expected_type = CANONICAL_QUESTIONS[question_id]["expected_type"]
    
    if expected_type == "boolean":
        if not isinstance(answer, bool):
            return False, f"Expected boolean (true/false), got {type(answer).__name__}"
        return True, None
    
    elif expected_type == "integer":
        if not isinstance(answer, int):
            return False, f"Expected integer, got {type(answer).__name__}"
        if answer < 0:
            return False, "Expected non-negative integer (>= 0)"
        return True, None
    
    else:
        return False, f"Unknown expected type: {expected_type}"


def validate_sanity(
    question_id: str,
    answer: Any,
    automation_relevance: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """
    Perform sanity validation on answer.
    
    Sanity checks detect logically inconsistent answers:
    - step_reduction_ratio == 0 BUT automation_relevance == HIGH
      (If solution is highly automated, it should reduce steps)
    
    Returns:
        (is_valid, error_message)
    """
    # Sanity check for step_reduction_ratio
    if question_id == "step_reduction_ratio":
        if automation_relevance == "HIGH" and answer == 0:
            return False, (
                "Inconsistent: step_reduction_ratio is 0 but automation_relevance is HIGH. "
                "If your solution is highly automated, it should eliminate at least some steps."
            )
    
    # No other sanity checks needed for now
    return True, None


def validate_answer(
    question_id: str,
    answer: Any,
    automation_relevance: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """
    Dual validation: type check + sanity check.
    
    Returns:
        (is_valid, error_message)
    """
    # Type validation
    type_valid, type_error = validate_type(question_id, answer)
    if not type_valid:
        return False, type_error
    
    # Sanity validation
    sanity_valid, sanity_error = validate_sanity(question_id, answer, automation_relevance)
    if not sanity_valid:
        return False, sanity_error
    
    return True, None


# ============================================================================
# FIREWALL: Prevent LLM Leakage into Stage 3
# ============================================================================
# This firewall ensures that ONLY validated structured inputs reach Stage 3.
# No LLM output, no free text, no unvalidated data can pass through.
# ============================================================================

def collect_leverage_inputs(
    automation_relevance: str,
    use_llm: bool = True,
    simulated_answers: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Collect and validate structured leverage inputs.
    
    This function:
    1. Presents questions (with optional LLM wording adaptation)
    2. Collects answers (simulated for testing, or from user input)
    3. Validates answers (type + sanity checks)
    4. Returns ONLY validated structured inputs (FIREWALL)
    
    FIREWALL: Only validated structured data passes through.
    LLM output is used ONLY for question wording, never for answers or logic.
    
    Args:
        automation_relevance: From Stage 2 (for sanity validation)
        use_llm: Whether to use LLM for question wording
        simulated_answers: Dict of answers (for testing, None for interactive)
        
    Returns:
        Dict with validated structured inputs ready for Stage 3
    """
    validated_inputs = {}
    
    question_order = [
        "replaces_human_labor",
        "step_reduction_ratio",
        "delivers_final_answer",
        "unique_data_access",
        "works_under_constraints"
    ]
    
    for question_id in question_order:
        # Get question text (LLM-adapted or canonical)
        question_text = adapt_question_wording(question_id, use_llm=use_llm)
        
        # In production, would present question to user and collect answer
        # For now, use simulated answers
        if simulated_answers and question_id in simulated_answers:
            answer = simulated_answers[question_id]
        else:
            # Default fallback (in production, would prompt user)
            expected_type = CANONICAL_QUESTIONS[question_id]["expected_type"]
            if expected_type == "boolean":
                answer = False
            elif expected_type == "integer":
                answer = 0
            else:
                raise ValueError(f"Unknown expected type: {expected_type}")
        
        # Validate answer (type + sanity)
        is_valid, error_message = validate_answer(
            question_id, 
            answer,
            automation_relevance=automation_relevance
        )
        
        if not is_valid:
            # In production, would re-ask question
            # For now, log error and use default
            logger.error(
                f"Validation failed for {question_id}: {error_message}. "
                f"Answer: {answer}"
            )
            raise ValueError(f"Invalid answer for {question_id}: {error_message}")
        
        # FIREWALL: Store validated structured input
        validated_inputs[question_id] = answer
        logger.info(f"Collected and validated {question_id}: {answer}")
    
    # FIREWALL: Return ONLY validated structured inputs
    # No LLM output, no free text, no unvalidated data
    return validated_inputs


# ============================================================================
# TESTING UTILITIES
# ============================================================================

def get_canonical_question(question_id: str) -> Dict[str, Any]:
    """Get canonical question definition for testing/documentation"""
    if question_id not in CANONICAL_QUESTIONS:
        raise ValueError(f"Unknown question_id: {question_id}")
    return CANONICAL_QUESTIONS[question_id]


def validate_llm_adaptation(question_id: str, adapted_text: str) -> tuple[bool, str]:
    """
    Validate that LLM adaptation preserves semantic meaning.
    
    This is a helper for testing/auditing.
    Checks for forbidden patterns:
    - Mentions of "leverage", "advantage", "competition"
    - Biasing words like "better", "worse", "should"
    - Suggestions about correct answers
    
    Returns:
        (is_valid, reason)
    """
    canonical = CANONICAL_QUESTIONS[question_id]
    adapted_lower = adapted_text.lower()
    
    # Check for forbidden words
    forbidden_words = [
        "leverage", "advantage", "competitive", "competition",
        "better than", "worse than", "should answer", "you should",
        "correct answer", "right answer", "wrong answer"
    ]
    
    for forbidden in forbidden_words:
        if forbidden in adapted_lower:
            return False, f"Contains forbidden word/phrase: '{forbidden}'"
    
    # Check that core semantic concepts are preserved
    # This is a simple heuristic - in production would use more sophisticated checks
    semantic_meaning = canonical["semantic_meaning"].lower()
    core_concepts = []
    
    # Extract key concepts from semantic meaning
    if question_id == "replaces_human_labor":
        core_concepts = ["replace", "human", "work", "automat"]
    elif question_id == "step_reduction_ratio":
        core_concepts = ["step", "manual", "eliminate"]
    elif question_id == "delivers_final_answer":
        core_concepts = ["final", "complete", "actionable"]
    elif question_id == "unique_data_access":
        core_concepts = ["unique", "exclusive", "proprietary", "data"]
    elif question_id == "works_under_constraints":
        core_concepts = ["constraint", "limitation", "condition"]
    
    # Check if at least 50% of core concepts are present
    present_concepts = sum(1 for concept in core_concepts if concept in adapted_lower)
    if present_concepts < len(core_concepts) * 0.5:
        return False, f"Missing core concepts (only {present_concepts}/{len(core_concepts)} present)"
    
    return True, "Valid adaptation"
