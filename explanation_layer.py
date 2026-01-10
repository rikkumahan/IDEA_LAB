"""
EXPLANATION LAYER: LLM Narration (Read-Only)

This module uses LLM to explain deterministic results to the user.
The LLM is STRICTLY READ-ONLY - it cannot affect logic or decisions.

CRITICAL CONSTRAINTS:
- LLM INPUT is read-only (Stage 1, 2, 3, validation outputs)
- LLM can ONLY explain what is given
- LLM cannot add advice, facts, judgments, or actions
- LLM cannot modify any stage outputs
- Explanation must never affect validation logic

System prompt enforces: "You are an explanation layer, not a decision-maker."
"""

import logging
from typing import Dict, Any
from llm_factory import get_llm_client

logger = logging.getLogger(__name__)


# ============================================================================
# LLM EXPLANATION PROMPT (STRICT READ-ONLY)
# ============================================================================

EXPLANATION_SYSTEM_PROMPT = """You are an explanation layer for a deterministic startup validation system.

YOUR ROLE:
- Explain the validation results that have already been computed
- Make the technical outputs understandable to users
- Provide context for what the results mean

STRICT CONSTRAINTS (YOU MUST FOLLOW):
1. You are READ-ONLY - you explain results, you do NOT make decisions
2. You MUST explain ONLY what is given in the input data
3. You MUST NOT add advice, recommendations, or strategic guidance
4. You MUST NOT add new facts or make inferences beyond the data
5. You MUST NOT judge whether the startup will succeed or fail
6. You MUST NOT suggest actions the user should take
7. You MUST NOT modify or reinterpret the validation class

YOUR OUTPUT SHOULD:
- Explain what the validation class means
- Summarize the problem reality findings
- Summarize the market reality findings
- Summarize the leverage reality findings
- Connect how these led to the validation conclusion
- Use clear, neutral language

FORBIDDEN PHRASES:
- "You should..."
- "I recommend..."
- "This will succeed/fail..."
- "Based on my analysis..." (it's not your analysis, it's predetermined)
- "In my opinion..."
- "You need to..."

REMEMBER: You are explaining predetermined results, not providing advice.
"""


EXPLANATION_USER_PROMPT_TEMPLATE = """Explain the following startup validation results:

PROBLEM REALITY (Stage 1):
{problem_reality}

MARKET REALITY (Stage 2):
{market_reality}

LEVERAGE REALITY (Stage 3):
{leverage_reality}

VALIDATION STATE:
- Problem Validity: {problem_validity}
- Leverage Presence: {leverage_presence}
- Validation Class: {validation_class}

Explain these results in 3-4 paragraphs. Focus on:
1. What the validation class means
2. Summary of problem reality
3. Summary of market reality
4. Summary of leverage reality
5. How these factors led to this validation

Be clear, neutral, and explanatory. Do NOT add advice or recommendations.
"""


def generate_explanation(
    validation_output: Dict[str, Any],
    use_llm: bool = True
) -> str:
    """
    Generate human-readable explanation of validation results.
    
    This function uses LLM to narrate deterministic results.
    
    CRITICAL: LLM is READ-ONLY.
    - LLM input: validation_output (read-only)
    - LLM output: explanation text (for display only)
    - LLM CANNOT affect any logic or validation
    
    If LLM is disabled or fails, a fallback explanation is used.
    
    Args:
        validation_output: Complete validation output from validation.compute_validation_state
        use_llm: Whether to use LLM for explanation
        
    Returns:
        Human-readable explanation text
    """
    # Extract data for explanation
    try:
        problem_reality = validation_output["problem_reality"]
        market_reality = validation_output["market_reality"]
        leverage_reality = validation_output["leverage_reality"]
        validation_state = validation_output["validation_state"]
        
        problem_validity = validation_state["problem_validity"]
        leverage_presence = validation_state["leverage_presence"]
        validation_class = validation_state["validation_class"]
    except KeyError as e:
        logger.error(f"Missing required key in validation_output: {e}")
        return fallback_explanation(validation_output)
    
    # If LLM disabled, use fallback
    if not use_llm:
        logger.info("LLM disabled - using fallback explanation")
        return fallback_explanation(validation_output)
    
    # Try to generate LLM explanation
    try:
        llm = get_llm_client()
        
        # Format prompt with validation data (READ-ONLY)
        user_prompt = EXPLANATION_USER_PROMPT_TEMPLATE.format(
            problem_reality=format_dict_for_display(problem_reality),
            market_reality=format_dict_for_display(market_reality),
            leverage_reality=format_dict_for_display(leverage_reality),
            problem_validity=problem_validity,
            leverage_presence=leverage_presence,
            validation_class=validation_class
        )
        
        # Get LLM explanation
        # System prompt enforces READ-ONLY constraints
        explanation = llm.chat(
            system_prompt=EXPLANATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=500
        )
        
        # Clean up response
        explanation = explanation.strip()
        
        # Fallback if LLM returns invalid output
        if not explanation or len(explanation) < 50:
            logger.warning("LLM returned invalid explanation - using fallback")
            return fallback_explanation(validation_output)
        
        # Verify LLM didn't violate constraints (basic check)
        if contains_forbidden_phrases(explanation):
            logger.warning(
                "LLM explanation contains forbidden phrases - using fallback"
            )
            return fallback_explanation(validation_output)
        
        logger.info("LLM explanation generated successfully")
        return explanation
        
    except Exception as e:
        # Fallback on any error
        logger.warning(f"LLM explanation failed: {e}")
        logger.info("Using fallback explanation")
        return fallback_explanation(validation_output)


def fallback_explanation(validation_output: Dict[str, Any]) -> str:
    """
    Generate fallback explanation without LLM.
    
    This is used when LLM is disabled or fails.
    
    Args:
        validation_output: Complete validation output
        
    Returns:
        Template-based explanation text
    """
    try:
        validation_state = validation_output["validation_state"]
        validation_class = validation_state["validation_class"]
        problem_validity = validation_state["problem_validity"]
        leverage_presence = validation_state["leverage_presence"]
        
        problem_reality = validation_output["problem_reality"]
        leverage_reality = validation_output["leverage_reality"]
        
        # Get problem level and leverage flags
        problem_level = problem_reality.get("problem_level", "UNKNOWN")
        leverage_flags = leverage_reality.get("leverage_flags", [])
        
        # Build explanation using template
        explanation_parts = []
        
        # Part 1: Validation class
        explanation_parts.append(
            f"**Validation Result: {validation_class.replace('_', ' ')}**"
        )
        
        # Part 2: Problem reality
        explanation_parts.append(
            f"\nProblem Reality: The problem was assessed as {problem_validity} "
            f"(severity level: {problem_level}). "
        )
        
        if problem_validity == "REAL":
            explanation_parts.append(
                "This indicates a significant problem that affects users meaningfully."
            )
        else:
            explanation_parts.append(
                "This suggests the problem may not be severe enough to build a strong business around."
            )
        
        # Part 3: Leverage reality
        if leverage_presence == "PRESENT":
            leverage_str = ", ".join(leverage_flags)
            explanation_parts.append(
                f"\nLeverage Reality: Your solution demonstrates {len(leverage_flags)} "
                f"type(s) of competitive leverage: {leverage_str}. "
                "This indicates identifiable competitive advantages."
            )
        else:
            explanation_parts.append(
                "\nLeverage Reality: No clear competitive leverage was identified. "
                "This suggests the solution may not have strong defensible advantages."
            )
        
        # Part 4: Validation class interpretation
        explanation_parts.append(f"\n{get_validation_class_description(validation_class)}")
        
        return "".join(explanation_parts)
        
    except Exception as e:
        logger.error(f"Fallback explanation failed: {e}")
        return (
            "Unable to generate explanation. Please review the validation output directly."
        )


def get_validation_class_description(validation_class: str) -> str:
    """Get description for validation class"""
    descriptions = {
        "STRONG_FOUNDATION": (
            "Strong Foundation means both the problem and the competitive edge are validated. "
            "The problem is real and significant, AND your solution has identifiable competitive advantages."
        ),
        "REAL_PROBLEM_WEAK_EDGE": (
            "Real Problem, Weak Edge means the problem is validated but the competitive edge is not. "
            "The problem is real and significant, but your solution lacks clear competitive advantages."
        ),
        "WEAK_FOUNDATION": (
            "Weak Foundation means the problem itself is not validated as sufficiently severe. "
            "Regardless of competitive advantages, the problem may not be significant enough."
        )
    }
    
    return descriptions.get(validation_class, f"Unknown validation class: {validation_class}")


def format_dict_for_display(data: Dict[str, Any], max_depth: int = 2) -> str:
    """
    Format dictionary for LLM prompt display.
    
    Simplified representation for LLM consumption.
    """
    if not isinstance(data, dict):
        return str(data)
    
    parts = []
    for key, value in data.items():
        if isinstance(value, dict) and max_depth > 0:
            nested = format_dict_for_display(value, max_depth - 1)
            parts.append(f"{key}: {nested}")
        elif isinstance(value, list):
            parts.append(f"{key}: {', '.join(map(str, value)) if value else 'none'}")
        else:
            parts.append(f"{key}: {value}")
    
    return "; ".join(parts)


def contains_forbidden_phrases(text: str) -> bool:
    """
    Check if explanation contains forbidden phrases.
    
    This is a basic safety check to ensure LLM didn't violate constraints.
    """
    forbidden = [
        "you should",
        "i recommend",
        "you need to",
        "you must",
        "based on my analysis",
        "in my opinion",
        "will succeed",
        "will fail",
        "guaranteed to"
    ]
    
    text_lower = text.lower()
    for phrase in forbidden:
        if phrase in text_lower:
            logger.warning(f"Found forbidden phrase in explanation: '{phrase}'")
            return True
    
    return False


# ============================================================================
# TESTING UTILITY
# ============================================================================

def verify_explanation_independence(validation_output: Dict[str, Any]) -> bool:
    """
    Verify that explanation generation does not affect validation output.
    
    This is a testing utility to ensure the explanation layer is truly read-only.
    
    Returns:
        True if validation_output is unchanged after explanation generation
    """
    import copy
    
    # Deep copy original validation output
    original = copy.deepcopy(validation_output)
    
    # Generate explanation (should not modify validation_output)
    generate_explanation(validation_output, use_llm=False)
    
    # Check if validation_output was modified
    return validation_output == original
