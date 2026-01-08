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
    # ISSUE 2 FIX: Each query must introduce a DISTINCT modifier
    # Removed: "every day" (filler phrase from ISSUE 4)
    # Removed: "manual" prefix (often redundant with normalized problem)
    complaint_templates = [
        f"{normalized_problem} wasting time",        # Time waste indicator
        f"frustrating {normalized_problem}",         # Emotional frustration
        f"{normalized_problem} problem",             # Direct problem statement
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
    complaint_queries = deduplicate_queries(complaint_queries)
    workaround_queries = deduplicate_queries(workaround_queries)
    tool_queries = deduplicate_queries(tool_queries)
    blog_queries = deduplicate_queries(blog_queries)
    
    # STEP 5: ISSUE 2 FIX - Ensure intra-bucket query diversity
    # Remove near-duplicates that differ only by emotional padding
    complaint_queries = ensure_query_diversity(complaint_queries, "complaint_queries")
    workaround_queries = ensure_query_diversity(workaround_queries, "workaround_queries")
    tool_queries = ensure_query_diversity(tool_queries, "tool_queries")
    blog_queries = ensure_query_diversity(blog_queries, "blog_queries")
    
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


def ensure_query_diversity(queries, bucket_name):
    """
    Ensure intra-bucket query diversity by removing near-duplicates.
    
    ISSUE 2 FIX: Within each query bucket, ensure each query introduces a DISTINCT modifier.
    Prune queries that differ only by emotional intensifiers or filler phrases.
    Keep at most ONE emotional modifier per query.
    
    This is DETERMINISTIC - uses rule-based core extraction and comparison.
    
    Args:
        queries: List of queries in a bucket
        bucket_name: Name of the bucket (for logging)
        
    Returns:
        List of queries with near-duplicates removed
    """
    if len(queries) <= 1:
        return queries
    
    # Emotional modifiers that should not create multiple near-duplicate queries
    emotional_modifiers = {'frustrating', 'annoying', 'tedious', 'painful'}
    
    # Extract core content (remove emotional modifiers only) for comparison
    def extract_core(query):
        """Extract core content by removing ONLY emotional modifiers"""
        words = query.lower().split()
        # Remove emotional modifiers
        core_words = [w for w in words if w not in emotional_modifiers]
        return ' '.join(core_words)
    
    # Track unique cores and keep only first occurrence of each core
    seen_cores = {}
    diverse_queries = []
    
    for query in queries:
        core = extract_core(query)
        
        if core not in seen_cores:
            seen_cores[core] = query
            diverse_queries.append(query)
        else:
            # This is a near-duplicate (differs only by emotional modifier)
            logger.debug(
                f"[{bucket_name}] Removing near-duplicate query: '{query}' "
                f"(similar to '{seen_cores[core]}')"
            )
    
    # ASSERTION: Each query should have distinct content
    cores = [extract_core(q) for q in diverse_queries]
    assert len(cores) == len(set(cores)), \
        f"[{bucket_name}] Query diversity check failed - near-duplicates remain"
    
    return diverse_queries

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
    """
    Classify problem level based on weighted signal scoring with guardrails.
    
    ISSUE 3 FIX: Added guardrail to prevent false DRASTIC classification.
    - If intensity_level != "HIGH", problem_level MUST NOT be "DRASTIC"
    - In this case, downgrade to "SEVERE"
    
    This is a rule-based guardrail, NOT a weight change.
    
    Args:
        signals: Dictionary with intensity_count, complaint_count, workaround_count
        
    Returns:
        Problem level string: "DRASTIC", "SEVERE", "MODERATE", or "LOW"
    """
    score = (
        3 * signals["intensity_count"] +
        2 * signals["complaint_count"] +
        1 * signals["workaround_count"]
    )
    
    # Compute intensity level for guardrail check
    intensity_level = normalize_level(signals["intensity_count"])
    
    # Initial classification based on score
    if score >= 15:
        problem_level = "DRASTIC"
    elif score >= 8:
        problem_level = "SEVERE"
    elif score >= 4:
        problem_level = "MODERATE"
    else:
        problem_level = "LOW"
    
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
    
    return problem_level
