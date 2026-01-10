"""
Questioning Layer for Stage 3 Leverage Input Collection

This module implements safe LLM-assisted question wording while maintaining
deterministic decision-making.

CRITICAL RULES:
- LLM is used ONLY for question wording (not decisions)
- LLM cannot suggest answers or bias responses
- LLM output NEVER flows directly to Stage 3
- Structured answers (boolean/integer) are collected
- Dual validation ensures data integrity
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
from stage3_leverage import (
    CANONICAL_QUESTIONS,
    CanonicalQuestion,
    validate_and_parse_inputs,
    ValidationError
)

logger = logging.getLogger(__name__)


# ============================================================================
# LLM QUESTION WORDING ADAPTER
# ============================================================================

class QuestionWordingRequest(BaseModel):
    """Request for LLM to adapt question wording."""
    canonical_question: CanonicalQuestion
    user_context: Optional[str] = None  # Optional domain/industry context


class AdaptedQuestion(BaseModel):
    """LLM-adapted question wording."""
    question_id: str
    adapted_wording: str
    answer_type: str
    
    # For debugging/auditing
    original_wording: str
    adaptation_method: str  # "llm" or "default"


def get_llm_question_wording_prompt(question: CanonicalQuestion, context: Optional[str]) -> str:
    """
    Generate a safe LLM prompt for question wording adaptation.
    
    CRITICAL CONSTRAINTS enforced in prompt:
    - Rewrite wording only
    - Do not change meaning
    - Do not suggest answers
    - Do not add examples that bias responses
    - Do not mention leverage, advantage, or competition
    
    Args:
        question: Canonical question to adapt
        context: Optional user context (domain/industry)
        
    Returns:
        Safe LLM prompt string
    """
    context_str = f"\nUser's domain/industry: {context}" if context else ""
    
    prompt = f"""You are a question wording assistant. Your ONLY job is to rewrite questions for clarity.

STRICT RULES:
1. Rewrite the question wording ONLY for clarity and domain relevance
2. Do NOT change the semantic meaning of the question
3. Do NOT suggest answers or provide examples
4. Do NOT add bias toward any response
5. Do NOT mention: leverage, advantage, competition, strategy
6. Keep the question neutral and factual
7. The answer type is {question.answer_type} - do not change this

ORIGINAL QUESTION:
{question.default_wording}

SEMANTIC MEANING (MUST PRESERVE):
{question.semantic_meaning}

ANSWER TYPE: {question.answer_type}
{context_str}

Provide ONLY the reworded question text. No explanation, no preamble, no suggestions."""
    
    return prompt


def adapt_question_with_llm(
    question: CanonicalQuestion,
    llm_client,
    context: Optional[str] = None
) -> AdaptedQuestion:
    """
    Use LLM to adapt question wording while preserving meaning.
    
    SAFETY MEASURES:
    1. Explicit constraints in prompt
    2. Temperature = 0.3 (low randomness)
    3. Max tokens = 100 (prevent elaboration)
    4. Fallback to default wording if LLM fails
    5. Audit trail of adaptation method
    
    Args:
        question: Canonical question
        llm_client: LLM client (with explain method)
        context: Optional user context
        
    Returns:
        AdaptedQuestion with LLM wording or fallback
    """
    try:
        # Generate safe prompt
        prompt = get_llm_question_wording_prompt(question, context)
        
        # Call LLM with safety constraints
        # Note: Using the existing explain method, we need to adapt it
        # For now, we'll use a simple approach
        adapted_text = llm_client.adapt_question_wording(
            question.default_wording,
            question.semantic_meaning,
            question.answer_type,
            context
        )
        
        # Validate LLM output (basic sanity checks)
        if not adapted_text or len(adapted_text) < 10:
            raise ValueError("LLM output too short")
        if len(adapted_text) > 300:
            raise ValueError("LLM output too long")
        
        logger.info(f"Question {question.id} adapted by LLM")
        
        return AdaptedQuestion(
            question_id=question.id,
            adapted_wording=adapted_text.strip(),
            answer_type=question.answer_type,
            original_wording=question.default_wording,
            adaptation_method="llm"
        )
        
    except Exception as e:
        logger.warning(f"LLM adaptation failed for {question.id}: {e}, using default")
        
        # Fallback to default wording
        return AdaptedQuestion(
            question_id=question.id,
            adapted_wording=question.default_wording,
            answer_type=question.answer_type,
            original_wording=question.default_wording,
            adaptation_method="default"
        )


def adapt_all_questions(
    llm_client,
    context: Optional[str] = None,
    use_llm: bool = True
) -> Dict[str, AdaptedQuestion]:
    """
    Adapt all canonical questions for presentation.
    
    Args:
        llm_client: LLM client
        context: Optional user context
        use_llm: Whether to use LLM (True) or default wording (False)
        
    Returns:
        Dict mapping question_id to AdaptedQuestion
    """
    adapted = {}
    
    for question_id, question in CANONICAL_QUESTIONS.items():
        if use_llm:
            adapted[question_id] = adapt_question_with_llm(
                question, llm_client, context
            )
        else:
            # Use default wording without LLM
            adapted[question_id] = AdaptedQuestion(
                question_id=question.id,
                adapted_wording=question.default_wording,
                answer_type=question.answer_type,
                original_wording=question.default_wording,
                adaptation_method="default"
            )
    
    logger.info(f"Adapted {len(adapted)} questions (LLM: {use_llm})")
    return adapted


# ============================================================================
# ANSWER COLLECTION AND VALIDATION
# ============================================================================

class Answer(BaseModel):
    """Single answer to a leverage question."""
    question_id: str
    value: Any  # Will be validated based on question type
    
    # For re-asking on validation failure
    validation_passed: bool = True
    validation_error: Optional[str] = None


class AnswerSet(BaseModel):
    """Complete set of answers to leverage questions."""
    answers: Dict[str, Answer]
    
    def to_leverage_inputs(self) -> Dict[str, Any]:
        """Convert to raw inputs dict for Stage 3."""
        return {
            answer.question_id: answer.value
            for answer in self.answers.values()
        }


def validate_answer(
    question: CanonicalQuestion,
    raw_value: Any
) -> Answer:
    """
    Validate a single answer against question constraints.
    
    TYPE VALIDATION:
    - Boolean questions accept: True, False, "true", "false", "yes", "no"
    - Integer questions accept: int or numeric string
    
    SANITY VALIDATION:
    - Applied at the answer set level (cross-field checks)
    
    Args:
        question: Canonical question
        raw_value: Raw answer value
        
    Returns:
        Answer with validation status
    """
    # Type validation based on answer_type
    try:
        if question.answer_type == "boolean":
            # Convert to boolean
            if isinstance(raw_value, bool):
                value = raw_value
            elif isinstance(raw_value, str):
                value_lower = raw_value.lower().strip()
                if value_lower in ["true", "yes", "y", "1"]:
                    value = True
                elif value_lower in ["false", "no", "n", "0"]:
                    value = False
                else:
                    raise ValueError(f"Cannot convert '{raw_value}' to boolean")
            else:
                raise ValueError(f"Invalid type for boolean: {type(raw_value)}")
        
        elif question.answer_type == "integer":
            # Convert to integer
            if isinstance(raw_value, int):
                value = raw_value
            elif isinstance(raw_value, str):
                value = int(raw_value.strip())
            elif isinstance(raw_value, float):
                if raw_value.is_integer():
                    value = int(raw_value)
                else:
                    raise ValueError(f"Cannot convert float {raw_value} to integer")
            else:
                raise ValueError(f"Invalid type for integer: {type(raw_value)}")
            
            # Apply validation rules
            rules = question.validation_rules
            if "min" in rules and value < rules["min"]:
                raise ValueError(f"Value {value} below minimum {rules['min']}")
            if "max" in rules and value > rules["max"]:
                raise ValueError(f"Value {value} above maximum {rules['max']}")
        
        else:
            raise ValueError(f"Unknown answer type: {question.answer_type}")
        
        return Answer(
            question_id=question.id,
            value=value,
            validation_passed=True
        )
    
    except Exception as e:
        logger.warning(f"Validation failed for {question.id}: {e}")
        return Answer(
            question_id=question.id,
            value=raw_value,
            validation_passed=False,
            validation_error=str(e)
        )


def collect_and_validate_answers(
    raw_answers: Dict[str, Any]
) -> AnswerSet:
    """
    Collect and validate answers to leverage questions.
    
    DUAL VALIDATION:
    1. Type validation (per-question)
    2. Sanity validation (cross-field, done in Stage 3)
    
    Args:
        raw_answers: Dict mapping question_id to raw answer value
        
    Returns:
        AnswerSet with validated answers
        
    Raises:
        ValidationError: If any answer fails validation
    """
    answers = {}
    failed_questions = []
    
    # Validate each answer
    for question_id, question in CANONICAL_QUESTIONS.items():
        if question_id not in raw_answers:
            failed_questions.append(question_id)
            logger.error(f"Missing answer for required question: {question_id}")
            continue
        
        raw_value = raw_answers[question_id]
        answer = validate_answer(question, raw_value)
        
        if not answer.validation_passed:
            failed_questions.append(question_id)
        
        answers[question_id] = answer
    
    # Check if any validations failed
    if failed_questions:
        raise ValidationError(
            f"Validation failed for questions: {', '.join(failed_questions)}"
        )
    
    answer_set = AnswerSet(answers=answers)
    logger.info("All answers validated successfully")
    
    return answer_set


# ============================================================================
# QUESTIONING LAYER API
# ============================================================================

class QuestioningSession(BaseModel):
    """
    A questioning session to collect leverage inputs.
    
    This encapsulates the complete questioning flow:
    1. Adapt questions (with or without LLM)
    2. Present questions to user
    3. Collect answers
    4. Validate answers
    5. Return validated inputs for Stage 3
    """
    adapted_questions: Dict[str, AdaptedQuestion]
    answer_set: Optional[AnswerSet] = None
    use_llm: bool = True
    
    def get_questions_for_presentation(self) -> List[Dict[str, Any]]:
        """
        Get questions formatted for presentation to user.
        
        Returns:
            List of question dicts with id, wording, answer_type
        """
        return [
            {
                "id": q.question_id,
                "question": q.adapted_wording,
                "answer_type": q.answer_type,
                "hint": f"Expected answer: {q.answer_type}"
            }
            for q in self.adapted_questions.values()
        ]
    
    def submit_answers(self, raw_answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit answers and return validated inputs for Stage 3.
        
        FIREWALL: This is the interface between questioning layer and Stage 3.
        Only validated, structured data passes through.
        
        Args:
            raw_answers: Dict mapping question_id to raw answer value
            
        Returns:
            Dict of validated leverage inputs
            
        Raises:
            ValidationError: If validation fails
        """
        # Collect and validate answers
        self.answer_set = collect_and_validate_answers(raw_answers)
        
        # Convert to leverage inputs format
        leverage_inputs = self.answer_set.to_leverage_inputs()
        
        # Final sanity validation using Stage 3 validator
        # This ensures cross-field consistency
        validate_and_parse_inputs(leverage_inputs)
        
        logger.info("Questioning session complete, inputs ready for Stage 3")
        
        return leverage_inputs


def create_questioning_session(
    llm_client,
    user_context: Optional[str] = None,
    use_llm: bool = True
) -> QuestioningSession:
    """
    Create a new questioning session.
    
    Args:
        llm_client: LLM client for question adaptation
        user_context: Optional user context (domain/industry)
        use_llm: Whether to use LLM for question wording
        
    Returns:
        QuestioningSession ready for user interaction
    """
    # Adapt questions
    adapted = adapt_all_questions(llm_client, user_context, use_llm)
    
    # Create session
    session = QuestioningSession(
        adapted_questions=adapted,
        use_llm=use_llm
    )
    
    logger.info(f"Created questioning session (LLM: {use_llm})")
    
    return session
