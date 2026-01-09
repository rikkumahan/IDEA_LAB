# NLP Integration Implementation Plan

## Core Principle
NLP is an ASSISTANT, not a DECIDER. NLP assists with normalization and labeling; rules make all final decisions.

## Implementation Strategy

### Phase 1: Add NLP Assistant Functions (New Helper Functions)
These functions use NLP to extract features and suggest labels, but NEVER make final decisions.

1. **`nlp_suggest_page_intent(text)`** → Intent label (SELLING/DOCUMENTATION/GUIDE/DISCUSSION/REVIEW)
   - Uses NLP preprocessing to analyze text
   - Returns a SUGGESTION, not a decision
   - Rules will use this as ONE input among many

2. **`nlp_extract_solution_cues(text)`** → Keyword hints
   - Extracts normalized keywords from solution attributes
   - Provides hints like "repair" → "service-related"
   - Rules still make final modality decision

### Phase 2: Integrate NLP Assistants (Modify Existing Functions)
Update existing functions to use NLP suggestions, with clear boundaries.

1. **`classify_result_type(result)`**
   - Add NLP preprocessing for keyword matching
   - Use `preprocess_text()` + `match_keywords_with_deduplication()`
   - Mark NLP boundary with comments
   - Rules make final classification

2. **`classify_solution_modality(solution)`**
   - Add NLP preprocessing for attribute analysis
   - Extract normalized keywords using NLP
   - Rules still enforce all classification logic

### Phase 3: Add Safety Checks
Ensure NLP cannot change outcomes.

1. Add logging to show NLP outputs vs rule decisions
2. Add inline comments marking "NLP boundary — rules decide after this point"
3. Ensure NLP outputs are never written directly to final JSON

## Files to Modify
- `main.py` - Add NLP assistant functions and integrate into existing logic

## Files to Create
- `test_nlp_integration.py` - Verify NLP doesn't change outcomes
- `NLP_INTEGRATION_SAFEGUARDS.md` - Document safety measures

## Testing Strategy
1. Run test suite with NLP enabled
2. Run test suite with NLP disabled (fallback to simple matching)
3. Verify outputs are identical in decision outcomes (only recall may differ)
