# Query Generation Hardening - Implementation Documentation

## Overview

This document describes the hardened query generation system with deterministic normalization and strict MIN-MAX bounds enforcement.

## Design Principles

1. **Deterministic Normalization**: Problem text is normalized BEFORE query generation using NLTK-based preprocessing
2. **Fixed Query Templates**: Each bucket has fixed templates with ONE clear purpose (no overlap)
3. **Strict MIN-MAX Bounds**: Query counts are bounded per bucket with loud failures for insufficient templates
4. **Query Deduplication**: Queries are deduplicated AFTER normalization and BEFORE execution
5. **No Intelligence**: NO LLM-based rewriting, synonym expansion, embeddings, or semantic reasoning

## Query Buckets

The system uses FOUR fixed query buckets, each serving ONE purpose only:

### 1. Complaint Queries (MIN=3, MAX=4)
**Purpose:** Detect human pain, frustration, time waste

**Templates:**
- `{normalized_problem} every day` - Frequency indicator
- `{normalized_problem} wasting time` - Time waste indicator
- `frustrating {normalized_problem}` - Emotional frustration
- `manual {normalized_problem}` - Tedious manual work

**Examples:**
```
Input: "Managing spreadsheets"
Output:
  - manage spreadsheet every day
  - manage spreadsheet wasting time
  - frustrating manage spreadsheet
  - manual manage spreadsheet
```

### 2. Workaround Queries (MIN=3, MAX=4)
**Purpose:** Detect DIY solutions, substitutes, hacks

**Templates:**
- `how to automate {normalized_problem}` - Solution seeking
- `{normalized_problem} workaround` - Explicit workaround
- `{normalized_problem} script` - DIY scripting
- `{normalized_problem} automation` - Automation seeking

**Examples:**
```
Input: "data entry"
Output:
  - how to automate data entry
  - data entry workaround
  - data entry script
  - data entry automation
```

### 3. Tool Queries (MIN=2, MAX=3)
**Purpose:** Detect existing commercial solutions, competitors

**Templates:**
- `{normalized_problem} tool` - Generic tool search
- `{normalized_problem} software` - Software product
- `{normalized_problem} chrome extension` - Browser tool

**Examples:**
```
Input: "spreadsheet management"
Output:
  - spreadsheet management tool
  - spreadsheet management software
  - spreadsheet management chrome extension
```

### 4. Blog Queries (MIN=2, MAX=3)
**Purpose:** Detect content saturation, thought leadership

**Templates:**
- `{normalized_problem} blog` - Blog posts
- `{normalized_problem} guide` - How-to guides
- `{normalized_problem} best practices` - Educational content

**Examples:**
```
Input: "customer tracking"
Output:
  - customer tracking blog
  - customer tracking guide
  - customer tracking best practices
```

## Text Normalization Pipeline

Problem text is normalized using a deterministic NLP pipeline BEFORE being inserted into query templates:

### Steps:

1. **Lowercase**: Convert all text to lowercase
2. **Tokenize**: Split into words using NLTK word_tokenize
3. **Remove Stopwords**: Filter out common words (the, is, with, etc.)
4. **Lemmatize**: Reduce words to base forms using NLTK WordNetLemmatizer
   - "managing" → "manage"
   - "spreadsheets" → "spreadsheet"
   - "frustrated" → "frustrate"
5. **Join**: Combine back into normalized phrase

### Examples:

```
"Managing multiple spreadsheets daily"
→ "manage multiple spreadsheet daily"

"Frustrated with manual data entry"
→ "frustrate manual data entry"

"The problem is tracking customer orders"
→ "problem track customer order"
```

### Important Notes:

- Normalization is DETERMINISTIC (same input = same output always)
- NO semantic reasoning or AI involved
- Uses only NLTK's rule-based algorithms (Porter stemming, WordNet lemmatization)

## MIN-MAX Bounds Enforcement

Each bucket has strict MIN-MAX bounds on query count:

| Bucket | MIN | MAX | Purpose |
|--------|-----|-----|---------|
| complaint_queries | 3 | 4 | Must have at least 3 complaint indicators |
| workaround_queries | 3 | 4 | Must have at least 3 workaround indicators |
| tool_queries | 2 | 3 | Must have at least 2 product indicators |
| blog_queries | 2 | 3 | Must have at least 2 content indicators |

### Enforcement Rules:

1. **Below MIN**: Log warning, return what we have (DO NOT invent new queries)
2. **Above MAX**: Trim to MAX (deterministic - keep first N queries)
3. **Within bounds**: Return as-is

### Example:

```python
# Template count = 5, MAX = 3
queries = ["q1", "q2", "q3", "q4", "q5"]
result = enforce_bounds(queries, min_count=2, max_count=3, bucket_name="test")
# Returns: ["q1", "q2", "q3"] (keeps first 3)

# Template count = 1, MIN = 3
queries = ["q1"]
result = enforce_bounds(queries, min_count=3, max_count=4, bucket_name="test")
# Returns: ["q1"] (with warning logged)
```

## Query Deduplication

Queries are deduplicated AFTER template generation to remove redundant searches:

### Deduplication Rules:

1. **Case-insensitive**: "Query1" and "query1" are considered duplicates
2. **Whitespace normalization**: "query  1" and "query 1" are considered duplicates
3. **Order preservation**: First occurrence is kept (deterministic)
4. **Per-bucket**: Applied to each bucket independently

### Example:

```python
queries = ["manual data entry", "Manual Data Entry", "spreadsheet management"]
deduplicated = deduplicate_queries(queries)
# Returns: ["manual data entry", "spreadsheet management"]
```

## Bucket Separation (No Overlap)

Templates are designed to ensure NO overlap in intent between buckets:

### Complaint Indicators (ONLY in complaint_queries):
- "every day" (frequency)
- "wasting time" (inefficiency)
- "frustrating" (emotion)
- "manual" (tedious work)

### Workaround Indicators (ONLY in workaround_queries):
- "how to automate" (solution seeking)
- "workaround" (DIY solution)
- "script" (custom code)
- "automation" (automated solution)

### Tool Indicators (ONLY in tool_queries):
- "tool" (generic product)
- "software" (commercial product)
- "chrome extension" (browser tool)

### Blog Indicators (ONLY in blog_queries):
- "blog" (blog posts)
- "guide" (how-to content)
- "best practices" (educational content)

### Validation:

If a template indicator appears in multiple buckets, it's a BUG and must be fixed.

## Deterministic Behavior

The system is FULLY DETERMINISTIC:

1. **Same input → Same output**: Same problem text always produces identical queries
2. **No randomness**: No random selection, shuffling, or sampling
3. **No LLM calls**: No calls to GPT, Claude, or any language model
4. **No embeddings**: No semantic similarity or vector operations
5. **No dynamic logic**: No adaptive query counts based on content

### Testing:

```python
# Run 3 times with same input
result1 = generate_search_queries("spreadsheet management")
result2 = generate_search_queries("spreadsheet management")
result3 = generate_search_queries("spreadsheet management")

# All results are identical
assert result1 == result2 == result3  # ALWAYS passes
```

## Implementation Details

### Main Functions:

1. **`normalize_problem_text(problem: str) -> str`**
   - Location: `nlp_utils.py`
   - Purpose: Normalize problem text using deterministic NLP
   - Returns: Lowercase, lemmatized, stopword-removed phrase

2. **`generate_search_queries(problem: str) -> dict`**
   - Location: `main.py`
   - Purpose: Generate queries for all buckets with normalization
   - Returns: Dict with 4 buckets (complaint, workaround, tool, blog)

3. **`enforce_bounds(queries, min_count, max_count, bucket_name) -> list`**
   - Location: `main.py`
   - Purpose: Enforce MIN-MAX bounds on query count
   - Returns: List of queries trimmed/validated to bounds

4. **`deduplicate_queries(queries: list) -> list`**
   - Location: `main.py`
   - Purpose: Remove duplicate queries (case-insensitive, whitespace-normalized)
   - Returns: Deduplicated list preserving order

### Dependencies:

- **NLTK**: Natural Language Toolkit
  - `word_tokenize`: Tokenization
  - `WordNetLemmatizer`: Lemmatization
  - `stopwords`: Stopword list
- **No other ML/AI dependencies**

## Testing

### Test Coverage:

1. **Text Normalization Tests** (`test_query_generation.py`)
   - Lowercase conversion
   - Lemmatization (managing → manage)
   - Stopword removal (the, is, with)
   - Deterministic behavior (same input = same output)

2. **MIN-MAX Bounds Tests** (`test_query_generation.py`)
   - Below MIN warning
   - Above MAX trimming
   - Within bounds preservation

3. **Deduplication Tests** (`test_query_generation.py`)
   - Exact duplicates
   - Case-insensitive duplicates
   - Whitespace-normalized duplicates
   - Order preservation

4. **Bucket Separation Tests** (`test_query_generation.py`)
   - No query duplicates across buckets
   - Each query has correct bucket indicator
   - Template intent is unique per bucket

5. **Integration Tests** (`test_nlp_hardening.py`)
   - Full signal extraction pipeline
   - Stemming and matching
   - False positive prevention

### Running Tests:

```bash
# Run all tests
python test_nlp_hardening.py && python test_query_generation.py

# Run demonstration
python demo_hardening.py
```

## Maintenance

### Adding New Templates:

1. Identify the bucket (complaint, workaround, tool, blog)
2. Ensure template indicator is UNIQUE to that bucket
3. Add template to the appropriate list in `generate_search_queries()`
4. Verify bounds still within MIN-MAX limits
5. Run tests to ensure no overlap

### Modifying Bounds:

1. Update MIN-MAX constants in `generate_search_queries()`
2. Update tests in `test_query_generation.py`
3. Run tests to verify enforcement

### Debugging:

- Enable logging to see normalization and bound enforcement:
  ```python
  import logging
  logging.basicConfig(level=logging.INFO)
  ```
- Use `demo_hardening.py` to visualize behavior

## Forbidden Practices

The following are EXPLICITLY FORBIDDEN in this system:

1. ❌ LLM-based query rewriting (GPT, Claude, etc.)
2. ❌ Synonym expansion (WordNet synsets, word2vec, etc.)
3. ❌ Embeddings or semantic similarity (BERT, sentence transformers, etc.)
4. ❌ Dynamic or adaptive query counts (varying queries based on content)
5. ❌ Adding "extra" queries just in case
6. ❌ Randomness or sampling
7. ❌ Template overlap between buckets
8. ❌ Inventing new queries when below MIN

If any change introduces these, it MUST be reverted.

## Summary

This hardened query generation system provides:

✅ **Deterministic normalization** using NLTK lemmatization and stopword removal  
✅ **Fixed query templates** with clear bucket separation (no overlap)  
✅ **Strict MIN-MAX bounds** with loud failures for insufficient templates  
✅ **Query deduplication** after normalization to prevent redundant searches  
✅ **Zero intelligence** - no LLMs, embeddings, or adaptive logic  

The system is MINIMAL but SUFFICIENT - generating exactly the queries needed for signal extraction without over-engineering or non-determinism.
