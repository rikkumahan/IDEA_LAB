# Stage 3 Leverage Engine Documentation

## Overview

Stage 3 is the **Deterministic Leverage Engine** that detects competitive advantages in a startup idea based on structured inputs. It is completely rule-based, with NO LLM or NLP involvement.

## Architecture Principles

### CRITICAL CONSTRAINTS
- **Deterministic**: Same inputs ALWAYS produce same outputs
- **NO LLM/NLP**: Pure rule-based logic only
- **NO Text Inference**: Only structured boolean/integer inputs
- **Auditable**: Every decision is traceable to explicit rules
- **Independent**: Works identically with LLM disabled

## Leverage Flags

Stage 3 can emit 5 leverage flags (multiple flags may be active simultaneously):

### 1. COST_LEVERAGE
**Rule**: `replaces_human_labor == True AND automation_relevance == HIGH`

**Meaning**: Solution replaces expensive human labor with automation

**Example**: AI-powered data entry replacing manual typists

### 2. TIME_LEVERAGE
**Rule**: `step_reduction_ratio >= 5 OR (automation_relevance == HIGH AND substitute_pressure >= MEDIUM)`

**Meaning**: Solution significantly reduces time/steps OR automates in markets with substitute pressure

**Example**: 
- Reducing 10-step process to 3 steps (7 steps eliminated)
- High automation in markets where users actively seek alternatives

### 3. COGNITIVE_LEVERAGE
**Rule**: `delivers_final_answer == True AND content_saturation >= MEDIUM`

**Meaning**: Solution delivers actionable final answer (not just data/analysis) in spaces with existing content

**Example**: "Approved/Rejected" decision vs providing data for user to decide

### 4. ACCESS_LEVERAGE
**Rule**: `unique_data_access == True`

**Meaning**: Solution has proprietary/exclusive data access

**Note**: Public data, web scraping, and open APIs do NOT qualify

**Example**: Exclusive partnership with data provider, proprietary dataset

### 5. CONSTRAINT_LEVERAGE
**Rule**: `works_under_constraints == True`

**Meaning**: Solution operates in environments where competitors cannot

**Example**: HIPAA-compliant, offline operation, high-security environments

## Input Requirements

### User Inputs (Structured Only)
All inputs are REQUIRED. No free text allowed.

| Input | Type | Description | Example |
|-------|------|-------------|---------|
| `replaces_human_labor` | boolean | Does solution replace human work? | `true` for automation |
| `step_reduction_ratio` | integer >= 0 | Number of manual steps eliminated | `8` for 8-step reduction |
| `delivers_final_answer` | boolean | Provides final actionable answer? | `true` for "Approved/Rejected" |
| `unique_data_access` | boolean | Has proprietary data access? | `true` for exclusive data |
| `works_under_constraints` | boolean | Works under special constraints? | `true` for HIPAA-compliant |

### Market Inputs (from Stage 2)
These are computed deterministically in Stage 2.

| Input | Type | Values | Source |
|-------|------|--------|--------|
| `automation_relevance` | enum | LOW, MEDIUM, HIGH | Stage 2 market analysis |
| `substitute_pressure` | enum | LOW, MEDIUM, HIGH | Stage 2 competitor analysis |
| `content_saturation` | enum | LOW, MEDIUM, HIGH | Stage 2 content analysis |

## Validation

### Input Validation (Dual Layer)

#### 1. Type Validation
- Booleans must be `True` or `False` (not `None`, not strings)
- Integers must be `int >= 0` (not `None`, not floats, not negatives)
- Enums must be valid values (LOW/MEDIUM/HIGH)

#### 2. Sanity Validation
- Cross-field consistency checks
- Example: `step_reduction_ratio == 0` with `automation_relevance == HIGH` is suspicious

**On Validation Failure**: Return error with question to re-ask

## Usage

### Basic Usage
```python
from stage3_leverage import detect_leverage_flags

result = detect_leverage_flags(
    # User inputs
    replaces_human_labor=True,
    step_reduction_ratio=8,
    delivers_final_answer=True,
    unique_data_access=False,
    works_under_constraints=False,
    # Market inputs (from Stage 2)
    automation_relevance="HIGH",
    substitute_pressure="HIGH",
    content_saturation="HIGH"
)

# Output
print(result["leverage_flags"])  # ['COST_LEVERAGE', 'TIME_LEVERAGE', 'COGNITIVE_LEVERAGE']
print(result["leverage_details"])  # Detailed reasons for each flag
```

### Integration with Questioning Layer
```python
from leverage_questions import collect_leverage_inputs, format_for_stage3

# Collect inputs with validation
collection_result = collect_leverage_inputs(
    llm_client=None,  # Optional: LLM for question wording only
    user_context={"industry": "SaaS"},  # Optional
    market_data=stage2_market_strength,  # For sanity checks
    user_answers={
        "replaces_human_labor": True,
        "step_reduction_ratio": 8,
        "delivers_final_answer": True,
        "unique_data_access": False,
        "works_under_constraints": False
    }
)

if collection_result["success"]:
    # Format for Stage 3
    stage3_inputs = format_for_stage3(collection_result["inputs"])
    
    # Run Stage 3
    leverage_result = detect_leverage_flags(
        **stage3_inputs,
        automation_relevance="HIGH",
        substitute_pressure="HIGH",
        content_saturation="HIGH"
    )
else:
    # Validation failed - re-ask question
    print(collection_result["question_to_reask"])
```

## Validation Logic (Post-Stage 3)

### Classification Rules

#### Problem Validity
- **REAL**: `problem_level >= SEVERE`
- **WEAK**: `problem_level < SEVERE` (MODERATE, LOW)

#### Leverage Presence
- **PRESENT**: At least one leverage flag detected
- **NONE**: No leverage flags detected

#### Validation Class (Final Classification)
- **STRONG_FOUNDATION**: REAL problem + PRESENT leverage
- **REAL_PROBLEM_WEAK_EDGE**: REAL problem + NONE leverage
- **WEAK_FOUNDATION**: WEAK problem (regardless of leverage)

### Critical Rules
1. **Market pressure does NOT invalidate problems**
   - High competition + REAL problem = REAL_PROBLEM_WEAK_EDGE (not WEAK_FOUNDATION)
2. **Market data is CONTEXTUAL only**
   - Provides context but doesn't change validation class
3. **Weak problems always → WEAK_FOUNDATION**
   - Even with leverage, weak problem lacks foundation

## Testing

### Run Stage 3 Tests
```bash
python test_stage3.py
```

Tests include:
- Individual leverage rule tests
- Input validation tests
- Multiple leverage flags
- Determinism audit
- Edge cases

### Run Validation Tests
```bash
python test_validation.py
```

Tests include:
- Problem validity classification
- Leverage presence classification
- Validation class classification
- Market context (doesn't invalidate)
- Validation invariants

### Run End-to-End Integration Tests
```bash
python test_end_to_end.py
```

Tests include:
- STRONG_FOUNDATION scenario
- REAL_PROBLEM_WEAK_EDGE scenario
- WEAK_FOUNDATION scenario
- Determinism (LLM ON vs OFF)

## API Endpoints

### Complete Validation Endpoint
```
POST /validate-complete-idea
```

**Input**: Problem, Solution, and Leverage inputs

**Output**: Complete validation with all 3 stages + explanation

**Example**:
```json
{
  "validation_result": {
    "problem_reality": {...},
    "market_reality": {...},
    "leverage_reality": {
      "leverage_flags": ["COST_LEVERAGE", "TIME_LEVERAGE"],
      "leverage_details": {...}
    },
    "validation_state": {
      "problem_validity": "REAL",
      "leverage_presence": "PRESENT",
      "validation_class": "STRONG_FOUNDATION"
    }
  },
  "explanation": "...",
  "metadata": {
    "solution_modality": "SOFTWARE",
    "stages_completed": ["Stage 1: Problem Reality", "Stage 2: Market Reality", "Stage 3: Leverage Detection"],
    "deterministic": true,
    "llm_used": "explanation_only"
  }
}
```

### Stage 3 Only Endpoint (for testing)
```
POST /detect-leverage
```

**Input**: Leverage inputs + market strength

**Output**: Leverage detection results only

## Architectural Boundaries

### What Stage 3 Does
✅ Detect leverage based on exact rules
✅ Validate inputs (type + sanity)
✅ Emit multiple leverage flags simultaneously
✅ Work identically with LLM disabled

### What Stage 3 Does NOT Do
❌ Use LLM or NLP
❌ Infer from text
❌ Score or rank leverage
❌ Aggregate into single metric
❌ Suppress leverage due to competition
❌ Make strategic recommendations

## Security & Auditability

### Determinism Guarantee
- Same inputs → Same outputs (ALWAYS)
- No randomness, no ML, no probabilistic logic
- Fully auditable decision trail

### LLM Firewall
- LLM output NEVER reaches Stage 3
- LLM used ONLY for question wording (optional)
- Stage 3 consumes only validated structured inputs

### Input Validation
- Dual validation (type + sanity)
- Rejects null, ambiguous, or inconsistent inputs
- Forces re-asking on validation failure

## Confirmation Statement

**"Stage 3 leverage is deterministic, and LLM is used only for language."**

This confirms that:
1. Stage 3 leverage detection is rule-based and deterministic
2. LLM is confined to language layer (question wording, explanation)
3. LLM never affects logic, validation, or leverage detection
4. System works identically with LLM disabled
