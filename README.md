# IDEA_LAB - Signal Extraction with NLP Hardening

A FastAPI-based service that extracts signals from search results to assess problem severity using deterministic NLP techniques.

## Features

- **Hardened Query Generation:** Deterministic text normalization with strict MIN-MAX bounds
- **Fixed Query Buckets:** Complaint, workaround, tool, and blog queries (no overlap)
- **Robust Signal Extraction:** Captures complaint, workaround, and intensity signals
- **Deterministic NLP:** Uses stemming, lemmatization, tokenization, and rule-based matching (no ML/AI)
- **False Positive Prevention:** Context-aware phrase detection prevents incorrect matches
- **Statistical Independence:** Each document contributes to at most one signal category

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Download NLTK data (required for stemming and tokenization)
python download_nltk_data.py
```

### Running Tests

```bash
# Run all tests
python test_nlp_hardening.py
python test_query_generation.py

# Run demonstration
python demo_hardening.py
```

### Running the API

```bash
uvicorn main:app --reload
```

## API Endpoint

### POST /analyze-idea

Analyzes a problem by searching the web and extracting signals.

**Request:**
```json
{
  "problem": "manual data entry",
  "target_user": "small business owners",
  "user_claimed_frequency": "daily"
}
```

**Response:**
```json
{
  "queries_used": ["manual data entry every day", "..."],
  "unique_results_count": 25,
  "raw_signals": {
    "workaround_count": 8,
    "complaint_count": 12,
    "intensity_count": 5
  },
  "normalized_signals": {
    "complaint_level": "HIGH",
    "workaround_level": "HIGH",
    "intensity_level": "HIGH"
  },
  "problem_level": "SEVERE"
}
```

## Signal Types

1. **Complaint Signals:** Problems, frustrations, time waste indicators
2. **Workaround Signals:** Solution-seeking behavior, automation attempts
3. **Intensity Signals:** Urgency, severity, business impact indicators

## Query Buckets

The system uses FOUR fixed query buckets with strict MIN-MAX bounds:

1. **Complaint Queries (3-4):** Detect human pain, frustration, time waste
   - Examples: "manual data entry every day", "frustrating spreadsheet management"
2. **Workaround Queries (3-4):** Detect DIY solutions, substitutes, hacks
   - Examples: "how to automate data entry", "spreadsheet script"
3. **Tool Queries (2-3):** Detect existing commercial solutions, competitors
   - Examples: "data entry tool", "spreadsheet software"
4. **Blog Queries (2-3):** Detect content saturation, thought leadership
   - Examples: "data entry blog", "spreadsheet guide"

## NLP Techniques

### Query Generation:
- **Text Normalization:** Lowercase, lemmatization, stopword removal
- **Fixed Templates:** One purpose per bucket, no overlap
- **MIN-MAX Bounds:** Strict query count enforcement (3-4, 3-4, 2-3, 2-3)
- **Deduplication:** Case-insensitive, whitespace-normalized

### Signal Extraction:
- **Stemming:** Captures morphological variants (e.g., "frustrated" = "frustrating")
- **Tokenization:** Prevents substring false positives
- **Stopword Removal:** Improves signal quality
- **N-gram Detection:** Identifies multi-word phrases
- **Rule-based Context:** Validates keyword usage (e.g., "critical issue" ✓, "critical acclaim" ✗)

## Documentation

- [QUERY_HARDENING_DOCS.md](QUERY_HARDENING_DOCS.md) - Query generation hardening details
- [NLP_DOCUMENTATION.md](NLP_DOCUMENTATION.md) - Complete NLP implementation details
- [nlp_audit.md](nlp_audit.md) - Audit report of issues and solutions

## Architecture

```
main.py                   - FastAPI application, query generation, and signal extraction
nlp_utils.py              - Deterministic NLP preprocessing utilities
test_nlp_hardening.py     - Signal extraction test suite
test_query_generation.py  - Query generation test suite
demo_hardening.py         - Interactive demonstration of hardening features
download_nltk_data.py     - NLTK data setup script
```

## Environment Variables

Create a `.env` file with:
```
SERPAPI_KEY=your_serpapi_key_here
```

## Testing Examples

### Valid Signals Detected:
- ✅ "Manual data entry is frustrating" → Complaint
- ✅ "How to automate this task" → Workaround
- ✅ "Critical issue blocking production" → Intensity

### False Positives Prevented:
- ❌ "Automation bias in decision making" → Not a workaround
- ❌ "Critical acclaim from reviewers" → Not intensity
- ❌ "Blocking ads effectively" → Not intensity

## License

MIT
