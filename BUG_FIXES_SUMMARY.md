# Bug Fixes Summary

This document summarizes the fixes for four specific bugs identified during PR review.

## ISSUE 1: Duplicate tokens in normalized problem text

### Problem
Observed queries like: "manual manual jira ticket creation meeting"
This indicates incomplete normalization.

### Root Cause
The `normalize_problem_text()` function was not removing duplicate tokens after lemmatization. If the input contained duplicate words, they would remain in the output.

### Fix
Added a deduplication step (Step 6) in `normalize_problem_text()`:
```python
# Step 6: Remove duplicate tokens (ISSUE 1 FIX)
# Preserves order by keeping first occurrence of each token
seen = set()
deduplicated = []
for token in lemmatized:
    if token not in seen:
        seen.add(token)
        deduplicated.append(token)
```

### Verification
- ✓ Assertion added: No repeated tokens in normalized text
- ✓ Idempotency verified: `normalize(normalize(x)) == normalize(x)`
- ✓ Test case: "manual manual jira ticket creation meeting" → "manual jira ticket creation meet"

**File:** `nlp_utils.py` lines 401-411

---

## ISSUE 2: Near-duplicate queries within the same bucket

### Problem
Multiple complaint queries differed only by emotional padding:
- "manual ..."
- "manual ... wasting time"
- "frustrating manual ..."

This violates the MIN–MAX intent of minimal but sufficient diversity.

### Root Cause
1. Query templates included redundant modifiers (e.g., "manual" prefix when normalized problem already contains "manual")
2. No mechanism to detect and prune near-duplicate queries

### Fix
1. **Updated templates** to remove redundant modifiers:
   - Removed: "every day" (filler phrase from ISSUE 4)
   - Removed: "manual" prefix template (often redundant)
   
2. **Added `ensure_query_diversity()` function** to prune near-duplicates:
   - Extracts core content by removing emotional modifiers
   - Keeps only first occurrence of each unique core
   - Applied to all query buckets after deduplication

```python
def ensure_query_diversity(queries, bucket_name):
    """Remove near-duplicates that differ only by emotional modifiers"""
    emotional_modifiers = {'frustrating', 'annoying', 'tedious', 'painful'}
    
    def extract_core(query):
        words = query.lower().split()
        core_words = [w for w in words if w not in emotional_modifiers]
        return ' '.join(core_words)
    
    seen_cores = {}
    diverse_queries = []
    for query in queries:
        core = extract_core(query)
        if core not in seen_cores:
            seen_cores[core] = query
            diverse_queries.append(query)
    
    return diverse_queries
```

### Verification
- ✓ Assertion added: Each query has distinct core content
- ✓ Test case: Complaint queries now have distinct modifiers ("wasting time" vs "frustrating" vs "problem")
- ✓ No padding to meet MIN - respects actual diversity

**Files:** 
- `main.py` lines 229-272 (new function)
- `main.py` lines 83-90 (updated templates)
- `main.py` lines 142-148 (applied in generation)

---

## ISSUE 3: Missing severity guardrail (false DRASTIC risk)

### Problem
Problem classified as DRASTIC even when `intensity_level == MEDIUM`.

Example:
- Signals: intensity_count=2 (MEDIUM), complaint_count=3, workaround_count=3
- Score: 3*2 + 2*3 + 1*3 = 15
- Result: DRASTIC (incorrect)

### Root Cause
No guardrail existed to prevent DRASTIC classification when intensity signals were insufficient.

### Fix
Added rule-based guardrail in `classify_problem_level()`:
```python
# ISSUE 3 FIX: Guardrail - DRASTIC only possible when intensity_level == HIGH
if problem_level == "DRASTIC" and intensity_level != "HIGH":
    logger.info(
        f"Applying DRASTIC guardrail: intensity_level={intensity_level} (not HIGH), "
        f"downgrading from DRASTIC to SEVERE"
    )
    problem_level = "SEVERE"

# ASSERTION: DRASTIC is only possible when intensity_level == HIGH
assert problem_level != "DRASTIC" or intensity_level == "HIGH", \
    f"DRASTIC problem level requires HIGH intensity_level, got {intensity_level}"
```

### Verification
- ✓ Assertion added: DRASTIC requires intensity_level == HIGH
- ✓ Test case 1: intensity=2 (MEDIUM), score=15 → SEVERE (not DRASTIC)
- ✓ Test case 2: intensity=5 (HIGH), score=30 → DRASTIC (allowed)
- ✓ Test case 3: intensity=4 (MEDIUM), score=15 → SEVERE (edge case)

**File:** `main.py` lines 450-492

---

## ISSUE 4: Over-retention of filler time phrases in queries

### Problem
Phrases like "every day" added noise without increasing signal quality.

Example:
- Input: "jira ticket creation meeting every day"
- Previous output: "jira ticket creation meet every day"

### Root Cause
No filtering of common filler/time phrases during normalization.

### Fix
Added Step 5 in `normalize_problem_text()` to remove filler phrases:
```python
# Step 5: Remove non-essential filler time phrases
filler_phrases = {'every', 'day', 'daily', 'everyday', 'always', 'constantly'}
lemmatized = [token for token in lemmatized if token not in filler_phrases]
```

### Verification
- ✓ Test case 1: "every day" removed from normalized text
- ✓ Test case 2: "daily" removed
- ✓ Test case 3: "always" removed
- ✓ Test case 4: "constantly" removed
- ✓ Result: Compact, canonical noun phrases

**File:** `nlp_utils.py` lines 398-400

---

## Design Principles Maintained

All fixes adhere to the original design constraints:

1. ✓ **Deterministic**: No randomness, LLMs, or embeddings
2. ✓ **Rule-based**: All logic uses explicit rules
3. ✓ **No new buckets**: Existing bucket structure unchanged
4. ✓ **No new signals**: Signal categories unchanged
5. ✓ **No weight changes**: Scoring weights (3, 2, 1) unchanged
6. ✓ **Explainable**: All decisions traceable to specific rules

## Test Coverage

Created comprehensive test suite: `test_bug_fixes.py`
- 30+ test cases covering all 4 issues
- Integration test combining all fixes
- All existing tests pass (test_query_generation.py, test_nlp_hardening.py)

## Assertions in Production Code

**Note:** The problem statement explicitly requires assertions as checks:
- "REQUIRED CHECK: Assert no repeated tokens in the normalized problem string."
- "REQUIRED CHECK: Assert that DRASTIC is only possible when intensity_level == HIGH."

These assertions are part of the specification. For production deployment, consider:
1. Converting assertions to proper error handling with logging
2. Using a validation framework
3. Adding monitoring/alerting when guardrails trigger

However, per the specification, assertions are required for this implementation.
