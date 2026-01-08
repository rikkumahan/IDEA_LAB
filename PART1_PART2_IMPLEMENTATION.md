# Commercial vs Content Misclassification Fix & Stage 2 Implementation

## Summary

This document describes the implementation of two major features:

**Part 1**: Fix commercial vs content misclassification in Stage 1
**Part 2**: Add Stage 2 competitor detection using user's solution

## Part 1: Commercial vs Content Misclassification Fix

### Problem

Blogs, Reddit, Quora, and review sites were being incorrectly classified as "commercial competitors" when they merely DISCUSS tools rather than offer them directly.

### Solution

Added strict classification rules that NEVER classify content/discussion sites as commercial:

#### 1. Content Site Domain Check

Added `CONTENT_SITE_DOMAINS` list containing:
- Social/Discussion: Reddit, Quora, Stack Overflow, Hacker News
- Blogging: Medium, Substack, WordPress, Dev.to
- Review sites: G2, Capterra, TrustPilot, ProductHunt

**Rule**: Any URL from these domains is ALWAYS classified as 'content', never 'commercial'.

#### 2. Enhanced Classification Function

Updated `classify_result_type()` to return four types:
- `'commercial'` - First-party product sites with strong signals
- `'diy'` - Tutorials, open source, DIY solutions
- `'content'` - Blogs, discussions, reviews, comparisons
- `'unknown'` - Ambiguous or no clear signals

#### 3. Strong Product Signals

Commercial classification requires:
- Strong product signals (signup, pricing, dashboard, free trial)
- NOT a content site domain
- NOT a comparison/review article (no "vs", "review", "best tool", etc.)

#### 4. Classification Precedence

When signals conflict: **commercial > diy > content > unknown**

However, content site domains and comparison articles are checked FIRST to prevent misclassification.

### Code Changes

1. **New Constants**:
   - `CONTENT_SITE_DOMAINS` - Domains that should never be commercial
   - `STRONG_PRODUCT_SIGNALS` - Required for commercial classification
   - `CONTENT_KEYWORDS` - Weak content indicators
   - Strong content patterns (inline in function)

2. **New Function**:
   - `is_content_site(url)` - Check if URL is from a content/discussion site

3. **Updated Function**:
   - `classify_result_type(result)` - Now returns 4 types with strict rules
   - `separate_tool_workaround_results()` - Excludes content sites from competition analysis

### Testing

New test file: `test_classification_fix.py`

Tests verify:
- ✅ Reddit NEVER classified as commercial
- ✅ Quora NEVER classified as commercial
- ✅ Medium NEVER classified as commercial
- ✅ Review sites NEVER classified as commercial
- ✅ Comparison articles classified as content
- ✅ First-party products correctly identified as commercial
- ✅ Precedence rules work correctly
- ✅ Deterministic behavior

## Part 2: Stage 2 - User Solution Competitor Detection

### Problem

Stage 1 only detects competitors for the PROBLEM space (e.g., "manual data entry"). 
We needed Stage 2 to detect competitors for the user's specific SOLUTION (e.g., "AI-powered data entry automation software").

### Solution

Added Stage 2 that:
1. Takes structured solution attributes (NOT prose)
2. Generates deterministic solution-class queries
3. Uses SAME classifier from Stage 1
4. Returns ONLY commercial products

### Architecture

Stage 1 and Stage 2 are STRICTLY SEPARATED:

**Stage 1** (Problem Analysis):
- Input: Problem text
- Queries: Problem-focused ("manual data entry wasting time")
- Output: Problem severity, market competition

**Stage 2** (Solution Analysis):
- Input: Structured solution attributes
- Queries: Solution-focused ("AI-powered data entry software")
- Output: Competitors offering similar solutions

### New Data Model

```python
class UserSolution(BaseModel):
    core_action: str          # e.g., "validate", "generate", "analyze"
    input_required: str       # e.g., "startup idea text"
    output_type: str          # e.g., "validation report"
    target_user: str          # e.g., "startup founders"
    automation_level: str     # e.g., "AI-powered", "automated"
```

**Important**: These are structured fields, NOT marketing prose.

### New Functions

#### 1. `generate_solution_class_queries(solution: UserSolution) -> List[str]`

Generates 3-5 deterministic queries using fixed templates:

Templates:
- `"{automation_level} {core_action} software"`
- `"{core_action} {output_type} tool"`
- `"{target_user} {core_action} platform"`
- `"automated {core_action} service"`

**Characteristics**:
- Deterministic (same input = same output)
- Rule-based templates only
- No LLM, no semantic expansion
- Deduplicates automatically

#### 2. `extract_pricing_model(result) -> str`

Extracts pricing model from search result:
- `'free'` - Free forever, completely free
- `'freemium'` - Free trial, free + paid tiers
- `'paid'` - Pricing, subscription, $ amount
- `'unknown'` - No pricing information

**Characteristics**:
- Deterministic keyword matching
- No AI/ML involved

#### 3. `analyze_user_solution_competitors(solution: UserSolution) -> dict`

Main Stage 2 analysis function:

Process:
1. Generate solution-class queries
2. Run searches
3. Deduplicate results
4. Classify using `classify_result_type()` (same as Stage 1)
5. Filter to ONLY commercial products
6. Extract product information

Returns:
```python
{
    'exists': bool,              # Competitors found?
    'count': int,                # Number of commercial competitors
    'products': [                # List of commercial products
        {
            'name': str,
            'url': str,
            'pricing_model': str,
            'snippet': str
        }
    ],
    'queries_used': list         # Queries executed
}
```

**Important**: NO ranking, NO comparison to user's product, NO scoring.

### New API Endpoint

#### POST `/analyze-user-solution`

Request body:
```json
{
    "core_action": "validate",
    "input_required": "startup idea text",
    "output_type": "validation report",
    "target_user": "startup founders",
    "automation_level": "AI-powered"
}
```

Response:
```json
{
    "user_solution_competitors": {
        "exists": true,
        "count": 5,
        "products": [
            {
                "name": "IdeaValidator Pro",
                "url": "https://ideavalid ator.com",
                "pricing_model": "freemium",
                "snippet": "AI-powered startup idea validation..."
            }
        ],
        "queries_used": [
            "ai-powered validate software",
            "validate validation report tool",
            "startup founders validate platform"
        ]
    }
}
```

### Testing

New test file: `test_stage2.py`

Tests verify:
- ✅ Query generation is deterministic
- ✅ Different solutions generate different queries
- ✅ Pricing model extraction works
- ✅ Stage 2 uses same classifier as Stage 1
- ✅ Content sites (Reddit, Quora, etc.) are excluded
- ✅ Only commercial products are returned
- ✅ Stage 1 and Stage 2 are separated
- ✅ No ranking or comparison to user product
- ✅ Output format is correct

## Key Design Principles

### 1. Deterministic Behavior

- All logic is rule-based
- Same input ALWAYS produces same output
- No ML, no LLM, no probabilistic logic
- No embeddings or semantic reasoning

### 2. Strict Separation

- Stage 1: Problem analysis (complaint queries, workarounds)
- Stage 2: Solution analysis (solution-class queries)
- No mixing of stages
- Independent query generation

### 3. No AI Judgment

- Classification uses keyword matching only
- No "intelligence" or "understanding"
- No comparison of competitors
- No ranking or scoring

### 4. Conservative Classification

- Strict requirements for 'commercial' classification
- Content sites ALWAYS excluded from commercial
- Precedence rules prevent ambiguity

## Migration Guide

### For Existing Code

No breaking changes to existing endpoints:
- `/analyze-idea` - Works as before
- `/analyze-market` - Works as before

The only change is that competition analysis now correctly excludes content sites.

### For New Stage 2 Features

To use Stage 2 competitor detection:

1. **Define your solution** with structured attributes:
```python
solution = {
    "core_action": "analyze",
    "input_required": "meeting transcripts",
    "output_type": "action items",
    "target_user": "product managers",
    "automation_level": "AI-powered"
}
```

2. **Call the endpoint**:
```bash
curl -X POST http://localhost:8000/analyze-user-solution \
  -H "Content-Type: application/json" \
  -d '{
    "core_action": "analyze",
    "input_required": "meeting transcripts",
    "output_type": "action items",
    "target_user": "product managers",
    "automation_level": "AI-powered"
  }'
```

3. **Process the response**:
```python
response = {
    "user_solution_competitors": {
        "exists": True,
        "count": 3,
        "products": [...]
    }
}

if response["user_solution_competitors"]["exists"]:
    count = response["user_solution_competitors"]["count"]
    print(f"Found {count} competitors")
    
    for product in response["user_solution_competitors"]["products"]:
        print(f"- {product['name']} ({product['pricing_model']})")
```

## Testing

Run all tests:
```bash
# Part 1 tests (classification fix)
python test_classification_fix.py

# Stage 2 tests
python test_stage2.py

# Existing tests (should still pass)
python test_competition_saturation.py
python test_severity_guardrails.py
python test_query_generation.py
python test_nlp_hardening.py
```

## Files Changed

### Modified Files
- `main.py` - Added classification fixes, Stage 2 functions, new endpoint
- `test_competition_saturation.py` - Updated test for precedence rule

### New Files
- `test_classification_fix.py` - Tests for Part 1 (classification fix)
- `test_stage2.py` - Tests for Part 2 (Stage 2 implementation)
- `PART1_PART2_IMPLEMENTATION.md` - This documentation

## Constraints (Non-Negotiable)

As specified in the requirements:

- ✅ Do NOT change problem severity logic
- ✅ Do NOT change thresholds
- ✅ Do NOT compare competitors to the user's idea
- ✅ Do NOT introduce LLM reasoning or embeddings
- ✅ All logic must be deterministic and explainable
- ✅ Stage 1 and Stage 2 remain strictly separated

## Summary of Changes

**Part 1**:
- Fixed Reddit, Quora, Medium, blogs being misclassified as commercial
- Added strict commercial classification rules
- Content sites NEVER appear in commercial competitors
- Added comprehensive inline documentation

**Part 2**:
- Added Stage 2 user solution competitor detection
- Structured input (no prose)
- Deterministic query generation
- Uses same classifier as Stage 1
- Returns only commercial products
- No ranking or comparison

**Testing**:
- All existing tests pass
- New tests for classification fix
- New tests for Stage 2
- Comprehensive edge case coverage
