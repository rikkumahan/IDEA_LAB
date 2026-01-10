# Stage 3 & 4 Implementation: Leverage Detection and Validation

## Overview

This implementation adds **Stage 3 (Leverage Detection)** and **Stage 4 (Validation + Explanation)** to the deterministic decision engine, integrating LLM-based UX and explanation WITHOUT compromising determinism, correctness, or auditability.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DETERMINISTIC PIPELINE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Stage 1: Problem Reality (NLP-assisted, deterministic)          │
│    ├─ Query generation (fixed templates)                         │
│    ├─ Signal extraction (rule-based keyword matching)            │
│    └─ Problem level classification (DRASTIC/SEVERE/MODERATE/LOW) │
│                                                                   │
│  Stage 2: Market Reality (deterministic)                         │
│    ├─ Solution modality classification                           │
│    ├─ Competitor detection                                       │
│    └─ Market strength parameters                                 │
│                                                                   │
│  Stage 3: Leverage Detection (NEW - rule-based, LLM-free)        │
│    ├─ Questioning layer (LLM for wording ONLY)                   │
│    ├─ Input validation firewall                                  │
│    ├─ Deterministic leverage rules                               │
│    └─ Leverage flags output                                      │
│                                                                   │
│  Stage 4: Validation (NEW - derived + narrated)                  │
│    ├─ Problem validity (REAL/WEAK)                               │
│    ├─ Leverage presence (PRESENT/NONE)                           │
│    ├─ Validation class (3 outcomes)                              │
│    └─ Explanation layer (LLM narration ONLY)                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## LLM Integration Points

### ✅ ALLOWED (Language Layer Only)
1. **Question Wording** (Stage 3 input collection)
   - Adapt canonical questions for clarity
   - Domain-specific wording
   - NO change to semantic meaning

2. **Explanation Generation** (Stage 4 output)
   - Narrate deterministic results
   - Human-readable summary
   - NO advice, judgment, or new facts

### ❌ PROHIBITED (Decision Logic)
- Deciding leverage presence
- Inferring problem severity
- Modifying validation outcomes
- Adding recommendations
- Suggesting pivots or strategies

## Stage 3: Leverage Detection

### Canonical Questions (Fixed, Immutable)

| ID | Question | Type | Purpose |
|----|----------|------|---------|
| `replaces_human_labor` | Does your solution automate or replace work currently done manually? | boolean | Detect automation advantage |
| `step_reduction_ratio` | How many manual steps does your solution eliminate? | integer (≥0) | Quantify efficiency gains |
| `delivers_final_answer` | Does your solution provide complete, ready-to-use output? | boolean | Detect completeness advantage |
| `unique_data_access` | Does your solution use proprietary data others cannot access? | boolean | Detect data moat |
| `works_under_constraints` | Does your solution work under constraints where alternatives fail? | boolean | Detect constraint advantage |

### Leverage Detection Rules (Deterministic)

| Flag | Condition | Meaning |
|------|-----------|---------|
| `AUTOMATION_LEVERAGE` | `replaces_human_labor == True` AND `step_reduction_ratio >= 3` | Significant manual labor replacement |
| `COMPLETENESS_LEVERAGE` | `delivers_final_answer == True` AND `step_reduction_ratio >= 5` | Complete solution with major efficiency |
| `DATA_LEVERAGE` | `unique_data_access == True` | Proprietary data advantage |
| `CONSTRAINT_LEVERAGE` | `works_under_constraints == True` AND `step_reduction_ratio >= 2` | Works where alternatives struggle |

### Input Validation Firewall

**Dual Validation:**
1. **Type Validation** - Pydantic models ensure correct types
2. **Sanity Validation** - Cross-field consistency checks

**Rejected Inputs:**
- Negative step_reduction_ratio
- Missing required fields
- Invalid types (e.g., strings for integers)
- Null/ambiguous values

## Stage 4: Validation

### Validation Classification Rules (Deterministic)

```python
# Rule 1: Problem Validity
problem_validity = REAL if problem_level in ["DRASTIC", "SEVERE"] else WEAK

# Rule 2: Leverage Presence
leverage_presence = PRESENT if len(leverage_flags) > 0 else NONE

# Rule 3: Validation Class
if problem_validity == WEAK:
    validation_class = WEAK_FOUNDATION
elif leverage_presence == PRESENT:
    validation_class = STRONG_FOUNDATION
else:
    validation_class = REAL_PROBLEM_WEAK_EDGE
```

### Validation Classes

| Class | Meaning | Conditions |
|-------|---------|------------|
| `STRONG_FOUNDATION` | Real problem + leverage | REAL problem AND leverage PRESENT |
| `REAL_PROBLEM_WEAK_EDGE` | Real problem, no edge | REAL problem AND leverage NONE |
| `WEAK_FOUNDATION` | Weak problem | WEAK problem (regardless of leverage) |

**CRITICAL:** Market data is contextual ONLY. High competition does NOT invalidate a real problem.

## API Endpoints

### 1. Get Leverage Questions

```bash
GET /leverage-questions?context=<domain>&use_llm=<true|false>
```

**Purpose:** Get questions for Stage 3 input collection

**Response:**
```json
{
  "questions": [
    {
      "id": "replaces_human_labor",
      "question": "Does your solution automate or replace work...",
      "answer_type": "boolean",
      "hint": "Expected answer: boolean"
    },
    ...
  ],
  "use_llm": true,
  "context": "fintech"
}
```

### 2. Complete Validation Pipeline

```bash
POST /validate-complete
```

**Purpose:** Run Stages 1-4 and get complete validation

**Request:**
```json
{
  "problem": "manual data entry wasting hours every day",
  "target_user": "small business owners",
  "user_claimed_frequency": "daily",
  "solution": {  // Optional (for Stage 2)
    "core_action": "automate data entry",
    "input_required": "receipts and invoices",
    "output_type": "structured database entries",
    "target_user": "small business owners",
    "automation_level": "AI-powered"
  },
  "leverage_inputs": {  // Required (for Stage 3)
    "replaces_human_labor": true,
    "step_reduction_ratio": 10,
    "delivers_final_answer": true,
    "unique_data_access": false,
    "works_under_constraints": false
  },
  "use_llm": true,  // Optional (default: true)
  "user_context": "accounting software"  // Optional
}
```

**Response:**
```json
{
  "problem_reality": {
    "problem_level": "SEVERE",
    "signals": {...},
    "normalized_signals": {...}
  },
  "market_reality": {  // Only if solution provided
    "solution_modality": "SOFTWARE",
    "market_strength": {...},
    "competitors": {...}
  },
  "leverage_reality": {
    "leverage_flags": [
      {
        "name": "AUTOMATION_LEVERAGE",
        "present": true,
        "reason": "Replaces manual labor and eliminates 10 steps..."
      },
      {
        "name": "COMPLETENESS_LEVERAGE",
        "present": true,
        "reason": "Delivers complete solution and eliminates 10 steps..."
      }
    ]
  },
  "validation_state": {
    "problem_validity": "REAL",
    "leverage_presence": "PRESENT",
    "validation_class": "STRONG_FOUNDATION",
    "reasoning": "Problem is REAL (level: SEVERE) and 2 leverage..."
  },
  "explanation": "## Problem Reality\n\nThe problem shows strong..."
}
```

## Testing

### Test Suites

1. **test_stage3_validation.py** (16 tests)
   - Determinism verification
   - LLM isolation checks
   - Validation logic tests
   - Leverage detection tests
   - Input validation tests
   - Explanation independence tests

2. **test_offline_pipeline.py** (6 tests)
   - End-to-end flow tests
   - Questioning session tests
   - Market independence verification
   - Explanation independence verification

### Key Test Results

✅ **Determinism:** Same inputs always produce same outputs
✅ **LLM Isolation:** LLM ON vs OFF produces identical validation_class
✅ **Market Independence:** High competition doesn't invalidate real problems
✅ **Explanation Safety:** Explanations don't affect validation logic
✅ **Firewall:** Invalid inputs are rejected before Stage 3

### Running Tests

```bash
# All tests
python test_stage3_validation.py
python test_offline_pipeline.py

# Specific test class
python test_stage3_validation.py TestDeterminism -v

# Specific test
python test_offline_pipeline.py TestCompleteValidationOffline.test_end_to_end_strong_foundation -v
```

## Usage Examples

### Example 1: Minimal Usage (No Market Analysis)

```python
import requests

response = requests.post("http://localhost:8000/validate-complete", json={
    "problem": "organizing meeting notes",
    "target_user": "professionals",
    "user_claimed_frequency": "daily",
    "leverage_inputs": {
        "replaces_human_labor": True,
        "step_reduction_ratio": 5,
        "delivers_final_answer": True,
        "unique_data_access": False,
        "works_under_constraints": False
    },
    "use_llm": False  # Use deterministic mode
})

result = response.json()
print(f"Validation class: {result['validation_state']['validation_class']}")
# Output: STRONG_FOUNDATION (if problem is REAL)
```

### Example 2: Complete Analysis (With Market)

```python
response = requests.post("http://localhost:8000/validate-complete", json={
    "problem": "scheduling conflicts in teams",
    "target_user": "remote teams",
    "user_claimed_frequency": "daily",
    "solution": {
        "core_action": "schedule meetings",
        "input_required": "calendar events",
        "output_type": "optimized schedule",
        "target_user": "remote teams",
        "automation_level": "AI-powered"
    },
    "leverage_inputs": {
        "replaces_human_labor": True,
        "step_reduction_ratio": 8,
        "delivers_final_answer": True,
        "unique_data_access": False,
        "works_under_constraints": True
    },
    "use_llm": True  # Use LLM for wording and explanation
})

result = response.json()

# Access different stages
print(f"Problem level: {result['problem_reality']['problem_level']}")
print(f"Solution modality: {result['market_reality']['solution_modality']}")
print(f"Leverage flags: {len(result['leverage_reality']['leverage_flags'])}")
print(f"Validation: {result['validation_state']['validation_class']}")
print(f"\nExplanation:\n{result['explanation']}")
```

### Example 3: Get Questions First

```python
# Step 1: Get questions
response = requests.get("http://localhost:8000/leverage-questions?use_llm=true")
questions = response.json()["questions"]

# Step 2: Display questions to user and collect answers
answers = {}
for q in questions:
    print(f"{q['question']} ({q['answer_type']})")
    # Collect user input...
    answers[q['id']] = user_input

# Step 3: Run validation
response = requests.post("http://localhost:8000/validate-complete", json={
    "problem": "...",
    "target_user": "...",
    "user_claimed_frequency": "...",
    "leverage_inputs": answers
})
```

## Safety Guarantees

### 1. Determinism
- Same inputs → same validation_class
- No randomness in decision logic
- Reproducible results

### 2. LLM Isolation
- LLM output NEVER reaches decision logic
- Firewall prevents contamination
- System works identically with LLM disabled

### 3. Input Validation
- Dual validation (type + sanity)
- Invalid inputs rejected before processing
- No unvalidated data in Stage 3

### 4. Market Independence
- Market data is contextual only
- High competition ≠ invalid problem
- Validation based on problem + leverage only

### 5. Explanation Safety
- LLM cannot add facts or advice
- Strict prompt constraints
- Deterministic fallback always available

## File Structure

```
IDEA_LAB/
├── stage3_leverage.py          # Stage 3 leverage detection
├── questioning_layer.py        # Question wording and collection
├── validation.py               # Stage 4 validation logic
├── explanation_layer.py        # LLM explanation generation
├── llm_stub.py                 # Stub LLM (no API key needed)
├── llm_azure.py                # Azure OpenAI integration
├── llm_factory.py              # LLM client factory
├── main.py                     # FastAPI endpoints
├── test_stage3_validation.py  # Regression tests (16 tests)
├── test_offline_pipeline.py   # Integration tests (6 tests)
└── STAGE3_IMPLEMENTATION.md   # This document
```

## Configuration

### Environment Variables

```bash
# Optional: Enable Azure OpenAI for LLM features
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_VERSION=2023-05-15
AZURE_OPENAI_DEPLOYMENT=your_deployment

# Required: For Stage 1 & 2 (market research)
SERPAPI_KEY=your_serpapi_key
```

### Without LLM

The system works perfectly without any LLM configuration:
- Uses default question wording
- Uses deterministic explanation templates
- All decision logic remains identical

## Architectural Confirmation

✅ **LLM is used only for language; all decisions remain deterministic.**

- Question wording: LLM adapts for clarity (semantic meaning unchanged)
- Explanation: LLM narrates results (no new facts, no advice)
- Leverage detection: 100% rule-based (no LLM)
- Validation: 100% deterministic (no LLM)
- Problem classification: Existing deterministic rules (no change)
- Market analysis: Existing deterministic rules (no change)

**Regression guarantee:** LLM ON vs OFF produces identical validation_class (verified by tests).
