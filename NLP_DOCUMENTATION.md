# NLP Hardening Implementation - Complete Documentation

## Overview

This implementation improves signal extraction robustness using **DETERMINISTIC NLP techniques only**. No semantic reasoning, embeddings, ML models, or AI judgment are used.

## Implemented Techniques

### 1. Porter Stemming
**What:** Deterministic algorithm that reduces words to their root form
**Why:** Captures morphological variants without missing signals
**Example:**
- "frustrated", "frustrating", "frustration" → all stem to "frustrat"
- "automate", "automated", "automation" → all stem to "autom"
- "problems", "problem" → both stem to "problem"

### 2. Token-Based Matching
**What:** Match whole words only, not substrings
**Why:** Prevents false positives from substring matches
**Example:**
- "automation bias" is tokenized into ["automation", "bias"]
- We can detect this phrase and exclude "automation" from matching

### 3. Stopword Removal
**What:** Remove common words like "the", "is", "at"
**Why:** Improves signal quality and n-gram detection
**Example:**
- "the problem is urgent" → tokens: ["problem", "urgent"] (stopwords removed)

### 4. N-gram Extraction
**What:** Extract sequences of words (bigrams, trigrams)
**Why:** Enables phrase-level pattern detection
**Example:**
- "critical issue" → bigram that validates "critical" in proper context
- "critical acclaim" → bigram that excludes "critical" from matching

### 5. Rule-Based Phrase Detection
**What:** Explicit rules for excluded and required contexts
**Why:** Distinguishes valid signals from false positives
**Examples:**

**Excluded Phrases:**
- "automation bias" → "automation" does NOT match (cognitive bias context)
- "critical acclaim" → "critical" does NOT match (praise context)
- "blocking ads" → "blocking" does NOT match (ad blocker context)
- "serious developer" → "serious" does NOT match (expertise context)

**Required Context (for ambiguous keywords):**
- "critical" must appear with: "critical issue", "critical problem", "critical bug", etc.
- "blocking" must appear with: "blocking issue", "blocking bug", "blocked by", etc.
- "severe" must appear with: "severe issue", "severe problem", etc.

### 6. Signal Priority and Deduplication
**What:** Each document contributes to AT MOST one signal category
**Why:** Ensures statistical independence, prevents cascade inflation
**Priority Order:** intensity > complaint > workaround

**Example:**
```python
Document: "This critical issue is frustrating and needs automation"
Old behavior: intensity_count += 1, complaint_count += 1, workaround_count += 1
New behavior: intensity_count += 1 only (highest priority wins)
```

## Improvements Summary

| Issue | Old Behavior | New Behavior | Technique |
|-------|--------------|--------------|-----------|
| Morphological variants | "frustrated" ≠ "frustrating" | Both match | Stemming |
| False positives | "automation bias" → match | No match | Phrase detection |
| Double counting | One doc → 3 signals | One doc → 1 signal | Priority rules |
| Substring matching | "costly mistake" → match | Only matches in context | Tokenization |
| Missing context | "critical thinking" → match | No match (wrong context) | Required context |

## Keyword Lists

### Workaround Keywords (17 keywords)
Direct action, solution-seeking patterns:
- how to, workaround, work around
- automation, automate, automated
- script, scripted, scripting, tool, tools
- solution, solve, fix, hack, trick, bypass

### Complaint Keywords (19 keywords)
Problems, frustration, time waste, difficulty:
- problem, problems, issue, issues
- frustrating, frustrated, frustration
- wasting time, waste time, time consuming, time-consuming, tedious
- manual, manually, repetitive, repeatedly
- difficult, hard, challenging, struggle, struggling, annoying, annoyed

### Intensity Keywords (21 keywords)
Urgency, severity, impact, costs:
- urgent, urgently
- critical, critically, severe, severely, serious, seriously
- blocking, blocked, blocker
- wasting, waste, costing
- unusable, painful, nightmare, terrible, awful, horrible
- losing, loss

## Testing

Run the test suite:
```bash
python test_nlp_hardening.py
```

### Test Coverage
- ✅ Stemming captures morphological variants
- ✅ False positives are prevented (automation bias, critical acclaim, etc.)
- ✅ Valid matches work correctly
- ✅ Token-based matching prevents substring issues
- ✅ Stopword removal works
- ✅ Excluded phrase detection works
- ✅ Required context validation works
- ✅ Signal extraction integration (one doc → one signal max)

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Download NLTK data:
```bash
python download_nltk_data.py
```

3. Run tests:
```bash
python test_nlp_hardening.py
```

## API Changes

The `extract_signals()` function now returns:
```python
{
    "workaround_count": int,
    "complaint_count": int,
    "intensity_count": int,
    "_signal_tracking": {  # Optional debug info
        "intensity": [list of URLs],
        "complaint": [list of URLs],
        "workaround": [list of URLs]
    }
}
```

## Examples

### Example 1: Morphological Variants
**Input:** "Users are frustrated with manual problems"
**Old:** No match (only "frustrating" in keyword list)
**New:** ✓ Matches complaint signal (stems "frustrated" → "frustrat")

### Example 2: False Positive Prevention
**Input:** "Article about automation bias in decision making"
**Old:** ✓ Matches workaround (substring "automation")
**New:** ✗ No match (phrase detection excludes "automation bias")

### Example 3: Signal Deduplication
**Input:** "Critical urgent issue with manual work"
**Old:** intensity=1, complaint=1, workaround=0 (double count)
**New:** intensity=1 only (highest priority)

### Example 4: Context Validation
**Input:** "Movie received critical acclaim"
**Old:** ✓ Matches intensity (substring "critical")
**New:** ✗ No match (wrong context, needs "critical issue/problem/bug")

## Performance Characteristics

- **Deterministic:** Same input always produces same output
- **Fast:** Stemming and tokenization are O(n) operations
- **Predictable:** No black-box models, all rules are explicit
- **Maintainable:** Easy to add new keywords or exclusion rules

## Maintenance

To add new keywords:
1. Add to appropriate keyword list in `main.py`
2. Check if it needs exclusion rules in `nlp_utils.py` EXCLUDED_PHRASES
3. Check if it needs required context in `nlp_utils.py` REQUIRED_CONTEXT
4. Add test cases to `test_nlp_hardening.py`
5. Run tests to verify

## No Forbidden Techniques Used

✅ **Used:** Tokenization, Stemming, Stopwords, N-grams, Rule-based patterns
❌ **Not Used:** Semantic similarity, Sentiment analysis, ML models, AI judgment

All techniques are deterministic, rule-based, and explainable.
