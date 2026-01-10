"""
Intake Manager: LLM-Assisted Structured Input Collection

This module implements the intake layer that uses an LLM ONLY to collect
structured inputs from users. The LLM is NOT allowed to infer, interpret,
or make any decisions about the data.

CRITICAL RULES:
- LLM asks ONE question at a time
- LLM maps each question to exactly ONE field
- LLM does NOT infer or guess values
- LLM does NOT explain, analyze, or advise
- LLM does NOT rephrase user answers
- All output is JSON only
- Invalid JSON is rejected
- Partial objects are rejected
- Inferred values are rejected

ARCHITECTURE:
1. Session management (in-memory, thread-safe)
2. LLM question generation (constrained by system prompt)
3. Pydantic validation (strict)
4. Logging (prompts, responses, failures)
"""

import json
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, ValidationError
import threading

logger = logging.getLogger(__name__)

# Thread-safe session storage
_sessions_lock = threading.Lock()
_sessions: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# INTAKE SCHEMA (SOURCE OF TRUTH)
# ============================================================================

class ProblemInput(BaseModel):
    problem: str
    target_user: str
    user_claimed_frequency: str


class SolutionInput(BaseModel):
    core_action: str
    input_required: str
    output_type: str
    target_user: str
    automation_level: str


class LeverageInput(BaseModel):
    replaces_human_labor: bool
    step_reduction_ratio: float  # Changed to float to accept numbers
    delivers_final_answer: bool
    unique_data_access: bool
    works_under_constraints: bool


class CompleteIntakeSchema(BaseModel):
    problem_input: ProblemInput
    solution_input: SolutionInput
    leverage_input: LeverageInput


# ============================================================================
# FIELD DEFINITIONS WITH QUESTIONS
# ============================================================================

FIELD_QUESTIONS = {
    # Problem Input Fields
    "problem": {
        "section": "problem_input",
        "question": "What problem are you trying to solve? Describe it briefly.",
        "type": "string",
        "validation": lambda v: len(v.strip()) > 10,
        "validation_error": "Problem description must be at least 10 characters."
    },
    "target_user": {
        "section": "problem_input",
        "question": "Who experiences this problem? (e.g., 'startup founders', 'small business owners')",
        "type": "string",
        "validation": lambda v: len(v.strip()) > 3,
        "validation_error": "Target user must be at least 3 characters."
    },
    "user_claimed_frequency": {
        "section": "problem_input",
        "question": "How often does this problem occur? (e.g., 'daily', 'weekly', 'monthly')",
        "type": "string",
        "validation": lambda v: len(v.strip()) > 2,
        "validation_error": "Frequency must be at least 2 characters."
    },
    
    # Solution Input Fields
    "core_action": {
        "section": "solution_input",
        "question": "What is the core action your solution performs? (e.g., 'validate', 'generate', 'analyze')",
        "type": "string",
        "validation": lambda v: len(v.strip()) > 3,
        "validation_error": "Core action must be at least 3 characters."
    },
    "input_required": {
        "section": "solution_input",
        "question": "What input does your solution require from the user? (e.g., 'startup idea text', 'business plan')",
        "type": "string",
        "validation": lambda v: len(v.strip()) > 3,
        "validation_error": "Input required must be at least 3 characters."
    },
    "output_type": {
        "section": "solution_input",
        "question": "What type of output does your solution provide? (e.g., 'validation report', 'competitor list')",
        "type": "string",
        "validation": lambda v: len(v.strip()) > 3,
        "validation_error": "Output type must be at least 3 characters."
    },
    "solution_target_user": {
        "section": "solution_input",
        "question": "Who is your solution designed for? (e.g., 'startup founders', 'product managers')",
        "type": "string",
        "validation": lambda v: len(v.strip()) > 3,
        "validation_error": "Solution target user must be at least 3 characters.",
        "field_name": "target_user"  # Maps to target_user in solution_input
    },
    "automation_level": {
        "section": "solution_input",
        "question": "What is the automation level of your solution? (e.g., 'AI-powered', 'automated', 'manual', 'semi-automated')",
        "type": "string",
        "validation": lambda v: len(v.strip()) > 3,
        "validation_error": "Automation level must be at least 3 characters."
    },
    
    # Leverage Input Fields
    "replaces_human_labor": {
        "section": "leverage_input",
        "question": "Does your solution replace work currently done by humans? Answer 'yes' or 'no'.",
        "type": "boolean",
        "validation": lambda v: v in [True, False],
        "validation_error": "Answer must be 'yes' or 'no'.",
        "parse": lambda v: v.lower().strip() in ['yes', 'true', '1']
    },
    "step_reduction_ratio": {
        "section": "leverage_input",
        "question": "How many manual steps does your solution eliminate or reduce? Provide a number (0 if none).",
        "type": "number",
        "validation": lambda v: isinstance(v, (int, float)) and v >= 0,
        "validation_error": "Step reduction must be a number >= 0.",
        "parse": lambda v: float(v) if v else 0
    },
    "delivers_final_answer": {
        "section": "leverage_input",
        "question": "Does your solution provide a complete, actionable answer requiring no further analysis? Answer 'yes' or 'no'.",
        "type": "boolean",
        "validation": lambda v: v in [True, False],
        "validation_error": "Answer must be 'yes' or 'no'.",
        "parse": lambda v: v.lower().strip() in ['yes', 'true', '1']
    },
    "unique_data_access": {
        "section": "leverage_input",
        "question": "Does your solution have access to proprietary or exclusive data not publicly available? Answer 'yes' or 'no'.",
        "type": "boolean",
        "validation": lambda v: v in [True, False],
        "validation_error": "Answer must be 'yes' or 'no'.",
        "parse": lambda v: v.lower().strip() in ['yes', 'true', '1']
    },
    "works_under_constraints": {
        "section": "leverage_input",
        "question": "Does your solution work under constraints where alternatives cannot? Answer 'yes' or 'no'.",
        "type": "boolean",
        "validation": lambda v: v in [True, False],
        "validation_error": "Answer must be 'yes' or 'no'.",
        "parse": lambda v: v.lower().strip() in ['yes', 'true', '1']
    }
}

# Order of fields (defines question sequence)
FIELD_ORDER = [
    "problem",
    "target_user",
    "user_claimed_frequency",
    "core_action",
    "input_required",
    "output_type",
    "solution_target_user",
    "automation_level",
    "replaces_human_labor",
    "step_reduction_ratio",
    "delivers_final_answer",
    "unique_data_access",
    "works_under_constraints"
]


# ============================================================================
# LLM SYSTEM PROMPT (CRITICAL - DO NOT MODIFY)
# ============================================================================

LLM_SYSTEM_PROMPT = """You are a structured intake assistant.

Your job is to collect required inputs for a startup analysis system.

Rules:
- Ask only ONE question at a time.
- Each question must map to exactly ONE field.
- Do NOT infer or guess values.
- Do NOT explain, analyze, or advise.
- Do NOT rephrase user answers.
- Output JSON only.

If a user gives extra information:
- Ignore it.
- Ask the required question again.

When all fields are collected:
- Return a single JSON object matching the schema.

Your response format:
{
  "question": "Your question here",
  "field": "field_name",
  "complete": false
}

When intake is complete:
{
  "complete": true,
  "data": { complete intake schema }
}
"""


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class IntakeSession:
    """Represents an active intake session."""
    
    def __init__(self, session_id: str, initial_text: Optional[str] = None):
        self.session_id = session_id
        self.created_at = datetime.utcnow()
        self.current_field_index = 0
        self.collected_data = {}
        self.conversation_history = []
        self.initial_text = initial_text
        self.complete = False
        self.llm_client = None
        
    def get_current_field(self) -> Optional[str]:
        """Get the current field to collect."""
        if self.current_field_index >= len(FIELD_ORDER):
            return None
        return FIELD_ORDER[self.current_field_index]
    
    def get_next_question(self) -> Optional[Dict[str, Any]]:
        """Get the next question to ask."""
        current_field = self.get_current_field()
        if not current_field:
            return None
        
        field_def = FIELD_QUESTIONS[current_field]
        return {
            "question": field_def["question"],
            "field": current_field,
            "type": field_def["type"]
        }
    
    def record_answer(self, field: str, value: Any) -> None:
        """Record an answer for a field."""
        field_def = FIELD_QUESTIONS[field]
        section = field_def["section"]
        field_name = field_def.get("field_name", field)
        
        # Initialize section if needed
        if section not in self.collected_data:
            self.collected_data[section] = {}
        
        # Store the value
        self.collected_data[section][field_name] = value
        
        # Add to conversation history
        self.conversation_history.append({
            "field": field,
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Move to next field
        self.current_field_index += 1
        
        # Check if complete
        if self.current_field_index >= len(FIELD_ORDER):
            self.complete = True
    
    def is_complete(self) -> bool:
        """Check if all fields are collected."""
        return self.complete
    
    def get_collected_schema(self) -> Optional[CompleteIntakeSchema]:
        """Get the collected data as a validated schema."""
        if not self.is_complete():
            return None
        
        try:
            return CompleteIntakeSchema(**self.collected_data)
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e}")
            return None


def create_session(initial_text: Optional[str] = None) -> IntakeSession:
    """Create a new intake session."""
    session_id = str(uuid.uuid4())
    session = IntakeSession(session_id, initial_text)
    
    with _sessions_lock:
        _sessions[session_id] = session
    
    logger.info(f"Created intake session: {session_id}")
    return session


def get_session(session_id: str) -> Optional[IntakeSession]:
    """Get an existing session."""
    with _sessions_lock:
        return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    """Delete a session."""
    with _sessions_lock:
        if session_id in _sessions:
            del _sessions[session_id]
            logger.info(f"Deleted intake session: {session_id}")


# ============================================================================
# INTAKE PROCESSING
# ============================================================================

def validate_answer(field: str, raw_answer: str) -> tuple[bool, Any, Optional[str]]:
    """
    Validate and parse a user answer.
    
    Returns:
        (is_valid, parsed_value, error_message)
    """
    field_def = FIELD_QUESTIONS[field]
    
    # Parse the answer if needed
    if "parse" in field_def:
        try:
            parsed_value = field_def["parse"](raw_answer)
        except Exception as e:
            return False, None, f"Could not parse answer: {str(e)}"
    else:
        parsed_value = raw_answer.strip()
    
    # Validate
    try:
        is_valid = field_def["validation"](parsed_value)
        if not is_valid:
            return False, None, field_def["validation_error"]
        return True, parsed_value, None
    except Exception as e:
        return False, None, f"Validation error: {str(e)}"


def start_intake(initial_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Start a new intake session.
    
    Args:
        initial_text: Optional initial user text (startup idea or problem)
        
    Returns:
        {
            "session_id": str,
            "question": str,
            "field": str,
            "type": str
        }
    """
    session = create_session(initial_text)
    next_q = session.get_next_question()
    
    return {
        "session_id": session.session_id,
        **next_q
    }


def process_answer(session_id: str, answer: str) -> Dict[str, Any]:
    """
    Process a user's answer and return the next question or completion status.
    
    Args:
        session_id: Session identifier
        answer: User's answer to the current question
        
    Returns:
        {
            "question": str (if not complete),
            "field": str (if not complete),
            "type": str (if not complete),
            "complete": bool,
            "data": dict (if complete)
        }
    """
    session = get_session(session_id)
    if not session:
        return {"error": "Invalid session ID"}
    
    if session.is_complete():
        return {"error": "Session already complete"}
    
    # Get current field
    current_field = session.get_current_field()
    if not current_field:
        return {"error": "No more fields to collect"}
    
    # Validate answer
    is_valid, parsed_value, error_msg = validate_answer(current_field, answer)
    
    if not is_valid:
        # Return same question with error
        next_q = session.get_next_question()
        return {
            **next_q,
            "error": error_msg,
            "retry": True
        }
    
    # Record the answer
    session.record_answer(current_field, parsed_value)
    
    # Check if complete
    if session.is_complete():
        schema = session.get_collected_schema()
        if not schema:
            return {"error": "Failed to validate complete schema"}
        
        return {
            "complete": True,
            "data": schema.dict()
        }
    
    # Get next question
    next_q = session.get_next_question()
    return next_q


def get_complete_data(session_id: str) -> Optional[Dict[str, Any]]:
    """Get the complete collected data for a session."""
    session = get_session(session_id)
    if not session or not session.is_complete():
        return None
    
    schema = session.get_collected_schema()
    if not schema:
        return None
    
    return schema.dict()
