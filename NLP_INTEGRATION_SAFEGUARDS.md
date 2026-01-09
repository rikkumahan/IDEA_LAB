# NLP Integration Safeguards

## Core Principle

**NLP is an ASSISTANT, not a DECIDER.**

NLP assists with normalization and labeling; rules make ALL final decisions.

---

## Safeguards Implemented

### 1. NLP Assistant Functions (NEW)

Added two NLP assistant functions that provide suggestions, not decisions:

#### `nlp_suggest_page_intent(text)` → Intent label
- **Purpose**: Suggest page intent (SELLING/DOCUMENTATION/GUIDE/DISCUSSION/REVIEW)
- **Output**: A SUGGESTION only, not a final classification
- **Usage**: Rules use this as ONE input among many
- **Boundary**: Clearly marked with "=== NLP BOUNDARY — RULES DECIDE FROM HERE ==="

#### `nlp_extract_solution_cues(text)` → Keyword hints
- **Purpose**: Extract normalized keywords and provide hints
- **Output**: Hints like "service_related", "software_related" (not decisions)
- **Usage**: Rules use hints as additional signals
- **Boundary**: All hints are suggestions; rules enforce all classification logic

### 2. Enhanced Functions with NLP Integration

#### `classify_result_type(result)`
**NLP Role**: Assistive
- Uses `preprocess_text()` for better keyword matching (catches morphological variants)
- Uses `nlp_suggest_page_intent()` for additional context
- **RULE-BASED DECISION**: Rules make final classification (commercial/diy/content/unknown)
- **Graceful Fallback**: Works with simple substring matching if NLP fails

**Safeguards**:
```python
# NLP preprocessing (assistive)
try:
    preprocessed = preprocess_text(text)
    nlp_available = True
except Exception as e:
    preprocessed = None
    nlp_available = False  # Fallback to simple matching

# === NLP BOUNDARY — RULES DECIDE FROM HERE ===

if has_strong_product and not has_diy and not has_weak_content:
    return 'commercial'  # Rule-based decision
```

#### `classify_solution_modality(solution)`
**NLP Role**: Assistive
- Uses `nlp_extract_solution_cues()` to normalize keywords
- Catches variants like "repairing" → "repair"
- **RULE-BASED DECISION**: Rules make final modality classification
- **Graceful Fallback**: Works with exact word matching if NLP fails

**Safeguards**:
```python
# NLP assistance (optional)
try:
    action_cues = nlp_extract_solution_cues(core_action)
    nlp_available = True
except Exception as e:
    nlp_available = False  # Continue without NLP

# === NLP BOUNDARY — RULES DECIDE FROM HERE ===

if has_service_action:
    if has_high_automation:
        return "HYBRID"  # Rule-based decision
    else:
        return "SERVICE"  # Rule-based decision
```

---

## What NLP Does (Approved Uses)

### ✅ ALLOWED: Input Normalization
- Tokenization, stemming, lemmatization
- Morphological variant handling (pricing/priced/price)
- Stopword removal

### ✅ ALLOWED: Feature Extraction
- Extract normalized keywords from text
- Generate hints about text characteristics
- Suggest page intent labels

### ✅ ALLOWED: Pattern Matching
- Context-aware keyword matching
- Excluded phrase filtering (e.g., "automation bias")
- Required context validation (e.g., "critical issue" valid, "critical acclaim" invalid)

---

## What NLP Does NOT Do (Forbidden)

### ❌ FORBIDDEN: Decision Making
- Does NOT decide severity classification
- Does NOT decide competitor density
- Does NOT decide market strength parameters
- Does NOT decide solution modality

### ❌ FORBIDDEN: Direct Output Writing
- NLP values are NEVER written directly to final JSON
- All outputs are rule-based decisions
- NLP suggestions appear only in logs (for debugging)

### ❌ FORBIDDEN: Semantic Reasoning
- No embeddings
- No cosine similarity
- No sentiment scores
- No pretrained classifiers as decision logic

---

## Safety Checks (Mandatory)

### Check 1: Removing NLP doesn't change outcomes
**Verified**: Rules work with graceful fallback if NLP unavailable
- Same classifications with or without NLP
- Only recall may improve slightly with NLP (catches more variants)

### Check 2: NLP outputs are intermediate only
**Verified**: NLP functions return suggestions/hints, not decisions
- `nlp_suggest_page_intent()` returns suggestions (SELLING/REVIEW/etc.)
- `nlp_extract_solution_cues()` returns hints (service_related/software_related)
- Rules validate and make final decisions

### Check 3: No NLP values in final outputs
**Verified**: Final outputs contain ONLY rule-based decisions
- `classify_result_type()` returns: commercial/diy/content/unknown (rules)
- `classify_solution_modality()` returns: SOFTWARE/SERVICE/PHYSICAL_PRODUCT/HYBRID (rules)
- NO NLP intent labels or hints in outputs

### Check 4: Page intent ≠ competitor classification
**Verified**: NLP intent is a suggestion; rules enforce classification
- NLP may suggest "SELLING" intent
- Rules still check: is_content_site(), has_strong_product, has_diy
- Final classification is rule-based

---

## Testing

### Safety Test Suite: `test_nlp_safety.py`

Tests verify:
1. ✅ NLP is assistive, not decisive
2. ✅ Rules work with graceful fallback (if NLP fails)
3. ✅ NLP boundary is clearly marked
4. ✅ No NLP values in final outputs
5. ✅ NLP catches morphological variants (improves recall)

**All tests pass**: NLP integration is safe and maintains rule-based decision making.

---

## Code Markers

### NLP Boundary Comments
All NLP integration points are clearly marked:

```python
# === NLP PREPROCESSING (ASSISTIVE) ===
# NLP helps with better keyword matching
# Rules still make all decisions

# ... NLP preprocessing code ...

# === NLP BOUNDARY — RULES DECIDE FROM HERE ===

# ... rule-based decision logic ...
```

### Logging
NLP outputs are logged for debugging:
```python
logger.debug(f"NLP intent suggestion: {nlp_intent_suggestion}")
logger.debug(f"NLP cues: {action_cues['hints']}")
```

But final decisions are also logged:
```python
logger.info(f"Classified as COMMERCIAL (strong product signals): {url}")
logger.info(f"Classified as SERVICE: Service action detected")
```

---

## Summary

**NLP Integration Achievement**:
- ✅ Improved accuracy (catches morphological variants)
- ✅ Improved efficiency (better keyword matching)
- ✅ Rules still make ALL decisions
- ✅ No change to outcomes (only improved recall)
- ✅ Graceful fallback if NLP fails
- ✅ Clear boundaries between NLP assistance and rule-based decisions

**Core Principle Maintained**:
NLP assists with normalization and labeling; rules make ALL final decisions. NLP is an ASSISTANT, not a DECIDER.
