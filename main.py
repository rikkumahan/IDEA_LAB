import os
import requests
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from nlp_utils import preprocess_text, match_keywords_with_deduplication, normalize_problem_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# This defines what data we expect from the user
class IdeaInput(BaseModel):
    problem: str
    target_user: str
    user_claimed_frequency: str

@app.post("/analyze-idea")
def analyze_idea(data: IdeaInput):
    queries = generate_search_queries(data.problem)

    # 1. Run multiple complaint-related searches
    complaint_results = run_multiple_searches(
        queries["complaint_queries"]
    )

    # 2. Deduplicate
    complaint_results = deduplicate_results(complaint_results)

    # 3. Extract signals
    signals = extract_signals(complaint_results)

    problem_level = classify_problem_level(signals)
    normalized = normalize_signals(signals)

    return {
        "queries_used": queries["complaint_queries"],
        "unique_results_count": len(complaint_results),
        "raw_signals": signals,
        "normalized_signals": normalized,
        "problem_level": problem_level
    }


def generate_search_queries(problem: str):
    """
    Generate search queries with deterministic normalization and strict MIN-MAX bounds.
    
    DESIGN PRINCIPLES:
    1. Normalize problem text BEFORE query generation (lowercase, lemmatize, remove stopwords)
    2. Use ONLY fixed query templates per bucket (no overlap between buckets)
    3. Enforce STRICT MIN-MAX bounds per bucket
    4. Deduplicate queries AFTER normalization and BEFORE execution
    5. NO LLM-based rewriting, synonym expansion, or semantic reasoning
    
    BUCKET BOUNDS (STRICT):
    - complaint_queries: MIN=3, MAX=4
    - workaround_queries: MIN=3, MAX=4
    - tool_queries: MIN=2, MAX=3
    - blog_queries: MIN=2, MAX=3
    
    Each bucket serves ONE purpose only. Templates must never overlap in intent.
    """
    
    # STEP 1: Normalize problem text using deterministic NLP
    # This reduces the problem to core noun/verb phrase for consistent queries
    normalized_problem = normalize_problem_text(problem)
    
    logger.info(f"Original problem: '{problem}'")
    logger.info(f"Normalized problem: '{normalized_problem}'")
    
    # STEP 2: Generate queries using FIXED templates per bucket
    # Each template is designed for ONE specific bucket purpose
    
    # COMPLAINT QUERIES: Human pain, frustration, time waste
    # Purpose: Detect people actively complaining about the problem
    # Templates focus on negative emotions and inefficiency
    complaint_templates = [
        f"{normalized_problem} every day",           # Frequency indicator
        f"{normalized_problem} wasting time",        # Time waste indicator
        f"frustrating {normalized_problem}",         # Emotional frustration
        f"manual {normalized_problem}",              # Tedious manual work
    ]
    
    # WORKAROUND QUERIES: DIY solutions, substitutes, hacks
    # Purpose: Detect people seeking or building their own solutions
    # Templates focus on solution-seeking behavior
    workaround_templates = [
        f"how to automate {normalized_problem}",     # Solution seeking
        f"{normalized_problem} workaround",          # Explicit workaround
        f"{normalized_problem} script",              # DIY scripting
        f"{normalized_problem} automation",          # Automation seeking
    ]
    
    # TOOL QUERIES: Existing commercial solutions, competitors
    # Purpose: Detect existing products/tools that solve this problem
    # Templates focus on product discovery
    tool_templates = [
        f"{normalized_problem} tool",                # Generic tool search
        f"{normalized_problem} software",            # Software product
        f"{normalized_problem} chrome extension",    # Browser tool
    ]
    
    # BLOG QUERIES: Content saturation, thought leadership
    # Purpose: Detect if people are writing about this problem
    # Templates focus on content/discussion discovery
    blog_templates = [
        f"{normalized_problem} blog",                # Blog posts
        f"{normalized_problem} guide",               # How-to guides
        f"{normalized_problem} best practices",      # Educational content
    ]
    
    # STEP 3: Enforce MIN-MAX bounds per bucket
    # If templates < MIN: Log warning (DO NOT invent new queries)
    # If templates > MAX: Trim to MAX (deterministic - keep first N)
    
    complaint_queries = enforce_bounds(
        complaint_templates, 
        min_count=3, 
        max_count=4, 
        bucket_name="complaint_queries"
    )
    
    workaround_queries = enforce_bounds(
        workaround_templates, 
        min_count=3, 
        max_count=4, 
        bucket_name="workaround_queries"
    )
    
    tool_queries = enforce_bounds(
        tool_templates, 
        min_count=2, 
        max_count=3, 
        bucket_name="tool_queries"
    )
    
    blog_queries = enforce_bounds(
        blog_templates, 
        min_count=2, 
        max_count=3, 
        bucket_name="blog_queries"
    )
    
    # STEP 4: Deduplicate queries AFTER normalization
    # This ensures we don't run the same query multiple times
    all_queries = (
        complaint_queries + 
        workaround_queries + 
        tool_queries + 
        blog_queries
    )
    deduplicated = deduplicate_queries(all_queries)
    
    # Split back into buckets (maintain original bucket assignments)
    # Deduplication only removes exact duplicates, preserving bucket structure
    complaint_queries = deduplicate_queries(complaint_queries)
    workaround_queries = deduplicate_queries(workaround_queries)
    tool_queries = deduplicate_queries(tool_queries)
    blog_queries = deduplicate_queries(blog_queries)
    
    return {
        "complaint_queries": complaint_queries,
        "workaround_queries": workaround_queries,
        "tool_queries": tool_queries,
        "blog_queries": blog_queries,
    }


def enforce_bounds(queries, min_count, max_count, bucket_name):
    """
    Enforce strict MIN-MAX bounds on query count per bucket.
    
    If queries < MIN: Log warning (DO NOT create new queries)
    If queries > MAX: Trim to MAX (deterministic - keep first N)
    
    This is DETERMINISTIC - no randomness, no intelligence.
    """
    query_count = len(queries)
    
    # Check minimum bound
    if query_count < min_count:
        logger.warning(
            f"[{bucket_name}] Template count ({query_count}) is below MIN ({min_count}). "
            f"Cannot generate sufficient queries. Consider adding more templates."
        )
        # Return what we have - DO NOT invent new queries
        return queries
    
    # Enforce maximum bound (trim excess deterministically)
    if query_count > max_count:
        logger.info(
            f"[{bucket_name}] Trimming queries from {query_count} to MAX ({max_count})"
        )
        return queries[:max_count]  # Keep first N queries (deterministic)
    
    # Within bounds - return as is
    return queries


def deduplicate_queries(queries):
    """
    Deduplicate queries while preserving order.
    
    This is DETERMINISTIC - maintains the order of first occurrence.
    Uses case-insensitive comparison after whitespace normalization.
    """
    seen = set()
    deduplicated = []
    
    for query in queries:
        # Normalize for comparison (lowercase, strip, collapse whitespace)
        normalized = ' '.join(query.lower().split())
        
        if normalized not in seen:
            seen.add(normalized)
            deduplicated.append(query)
        else:
            logger.debug(f"Removing duplicate query: '{query}'")
    
    return deduplicated

def serpapi_search(query: str):
    api_key = os.getenv("SERPAPI_KEY")

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "google_domain": "google.com",
        "gl": "in",
        "hl": "en",
        "safe": "off",
        "start": "0"
    }

    response = requests.get("https://serpapi.com/search", params=params)

    if response.status_code != 200:
        return {"error": response.text}

    data = response.json()

    results = []

    for item in data.get("organic_results", []):
        results.append({
            "title": item.get("title"),
            "snippet": item.get("snippet"),
            "url": item.get("link")
        })

    return results

# Improved keyword lists with better coverage
# These will be stemmed during matching to catch variants

WORKAROUND_KEYWORDS = [
    # Direct action keywords
    "how to",
    "workaround",
    "work around",
    "automation",
    "automate",
    "automated",
    "script",
    "scripted",
    "scripting",
    "tool",
    "tools",
    # Solution-seeking patterns
    "solution",
    "solve",
    "fix",
    "hack",
    "trick",
    "bypass",
]

COMPLAINT_KEYWORDS = [
    # Direct problem statements
    "problem",
    "problems",
    "issue",
    "issues",
    "frustrating",
    "frustrated",
    "frustration",
    # Time/effort waste indicators
    "wasting time",
    "waste time",
    "time consuming",
    "time-consuming",
    "tedious",
    "manual",
    "manually",
    "repetitive",
    "repeatedly",
    # Difficulty indicators
    "difficult",
    "hard",
    "challenging",
    "struggle",
    "struggling",
    "annoying",
    "annoyed",
]

INTENSITY_KEYWORDS = [
    # Urgency indicators
    "urgent",
    "urgently",
    # Severity indicators
    "critical",
    "critically",
    "severe",
    "severely",
    "serious",
    "seriously",
    # Impact indicators
    "blocking",
    "blocked",
    "blocker",
    # Cost/waste indicators
    "wasting",
    "waste",
    "costing",
    # Usability indicators
    "unusable",
    "painful",
    "nightmare",
    "terrible",
    "awful",
    "horrible",
    # Business impact
    "losing",
    "loss",
]

def extract_signals(search_results):
    """
    Extract signals from search results using deterministic NLP preprocessing.
    
    Key improvements:
    1. Uses stemming to catch morphological variants
    2. Token-based matching to prevent false positives
    3. Context-aware phrase detection
    4. ONE document contributes to AT MOST ONE signal category
    
    Priority order: intensity > complaint > workaround
    This ensures statistical independence of signals.
    """
    workaround_count = 0
    complaint_count = 0
    intensity_count = 0
    
    # Track which URLs contributed to which signal (for debugging/validation)
    signal_tracking = {
        'intensity': [],
        'complaint': [],
        'workaround': []
    }

    for result in search_results:
        # Combine title and snippet
        text = (
            (result.get("title") or "") + " " +
            (result.get("snippet") or "")
        )
        
        # Skip empty results
        if not text.strip():
            continue
        
        # Preprocess text using deterministic NLP pipeline
        preprocessed = preprocess_text(text)
        
        # Check each signal type in priority order
        # Each document contributes to AT MOST one signal category
        
        # Priority 1: Intensity (most specific)
        if match_keywords_with_deduplication(INTENSITY_KEYWORDS, preprocessed):
            intensity_count += 1
            signal_tracking['intensity'].append(result.get("url"))
            continue  # Don't check other signals for this document
        
        # Priority 2: Complaint (medium specificity)
        if match_keywords_with_deduplication(COMPLAINT_KEYWORDS, preprocessed):
            complaint_count += 1
            signal_tracking['complaint'].append(result.get("url"))
            continue  # Don't check workaround signal
        
        # Priority 3: Workaround (least specific, most common)
        if match_keywords_with_deduplication(WORKAROUND_KEYWORDS, preprocessed):
            workaround_count += 1
            signal_tracking['workaround'].append(result.get("url"))

    return {
        "workaround_count": workaround_count,
        "complaint_count": complaint_count,
        "intensity_count": intensity_count,
        # Include tracking for debugging (optional, can be removed in production)
        "_signal_tracking": signal_tracking
    }

def run_multiple_searches(queries):
    all_results = []

    for q in queries:
        results = serpapi_search(q)
        if isinstance(results, list):
            all_results.extend(results)

    return all_results

def deduplicate_results(results):
    seen_urls = set()
    unique_results = []

    for r in results:
        url = r.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)

    return unique_results

# Normalizing the count level.
def normalize_level(count):
    if count >= 5:
        return "HIGH"
    elif count >= 2:
        return "MEDIUM"
    else:
        return "LOW"


def normalize_signals(signals):
    return {
        "complaint_level": normalize_level(signals["complaint_count"]),
        "workaround_level": normalize_level(signals["workaround_count"]),
        "intensity_level": normalize_level(signals["intensity_count"])
    }

def classify_problem_level(signals):
    score = (
        3 * signals["intensity_count"] +
        2 * signals["complaint_count"] +
        1 * signals["workaround_count"]
    )

    if score >= 15:
        return "DRASTIC"
    elif score >= 8:
        return "SEVERE"
    elif score >= 4:
        return "MODERATE"
    else:
        return "LOW"
