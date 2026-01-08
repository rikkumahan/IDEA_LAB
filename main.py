import os
import requests
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse, parse_qs, quote
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

def normalize_url(url):
    """
    Normalize URL to canonical form using deterministic rules.
    
    This prevents duplicate counting of the same content that appears with:
    - Different schemes (http vs https)
    - Different URL parameters (tracking codes, utm_*, fbclid, etc.)
    - Different fragments (#section)
    - Trailing slashes
    
    Steps:
    1. Parse URL into components
    2. Force HTTPS scheme (unless localhost/IP)
    3. Lowercase domain
    4. Remove trailing slash from path
    5. Remove fragment (#section)
    6. Remove tracking parameters (utm_*, fbclid, etc.)
    7. Sort remaining parameters alphabetically
    8. Reconstruct canonical URL
    
    This is DETERMINISTIC - same input always produces same output.
    NO ML, probabilistic logic, or AI judgment.
    
    Args:
        url: URL string to normalize
        
    Returns:
        Canonical URL string, or None if URL is invalid
    """
    if not url or not isinstance(url, str):
        return None
    
    try:
        # Parse URL into components
        parsed = urlparse(url.strip())
        
        # Skip if no scheme or netloc
        if not parsed.scheme or not parsed.netloc:
            return None
        
        # Force HTTPS (unless localhost or IP address)
        scheme = parsed.scheme.lower()
        if scheme in ('http', 'https'):
            # Extract just the hostname (without port) for checking
            netloc_parts = parsed.netloc.lower().split(':')
            hostname = netloc_parts[0]
            
            # Keep http for localhost/IPs, otherwise use https
            is_local = (
                hostname.startswith('localhost') or 
                hostname.startswith('127.0.0.1') or
                hostname.startswith('192.168.') or
                hostname.startswith('10.')
            )
            
            # Check for 172.16.0.0/12 range (172.16.x.x through 172.31.x.x)
            # Safely handle potential parsing errors
            if not is_local and hostname.startswith('172.'):
                try:
                    parts = hostname.split('.')
                    if len(parts) >= 2:
                        second_octet = int(parts[1])
                        if 16 <= second_octet <= 31:
                            is_local = True
                except (ValueError, IndexError):
                    # Not a valid IP, treat as public hostname
                    pass
            
            if not is_local:
                scheme = 'https'
        
        # Lowercase domain (case-insensitive per RFC 3986)
        netloc = parsed.netloc.lower()
        
        # Remove trailing slash from path (unless path is just "/" for root)
        path = parsed.path
        if path and len(path) > 1 and path.endswith('/'):
            path = path.rstrip('/')
        elif not path:
            # Root path should be '/'
            path = '/'
        
        # Remove fragment (e.g., #section1)
        # Fragments are client-side only and don't affect content
        fragment = ''
        
        # Parse and filter query parameters
        params = parse_qs(parsed.query, keep_blank_values=False)
        
        # Remove tracking parameters (deterministic list)
        # These don't change content, only track referrers
        tracking_params = {
            # Google Analytics
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            '_ga', '_gid', '_gac',
            # Facebook
            'fbclid', 'fb_action_ids', 'fb_action_types', 'fb_source',
            # Microsoft/Bing
            'msclkid', 'mc_cid', 'mc_eid',
            # Generic tracking
            'ref', 'source', 'campaign', 'channel',
            # Social media
            'share', 'via',
        }
        filtered_params = {k: v for k, v in params.items() 
                          if k.lower() not in tracking_params}
        
        # Sort parameters alphabetically for consistency
        # URL semantics: ?a=1&b=2 should equal ?b=2&a=1
        sorted_params = sorted(filtered_params.items())
        
        # Reconstruct query string with proper URL encoding
        if sorted_params:
            # Take first value if parameter has multiple values, and encode it
            query_parts = []
            for k, v in sorted_params:
                value = v[0] if isinstance(v, list) else v
                # Encode parameter name and value
                encoded_k = quote(str(k), safe='')
                encoded_v = quote(str(value), safe='')
                query_parts.append(f"{encoded_k}={encoded_v}")
            query = '&'.join(query_parts)
        else:
            query = ''
        
        # Reconstruct canonical URL
        canonical = urlunparse((scheme, netloc, path, '', query, fragment))
        
        return canonical
        
    except Exception as e:
        # If URL parsing fails, log and return None
        logger.debug(f"Failed to normalize URL '{url}': {e}")
        return None


def deduplicate_results(results):
    """
    Deduplicate search results by canonical URL.
    
    Uses URL normalization to detect duplicates that differ only in:
    - Scheme (http vs https)
    - Tracking parameters (utm_*, fbclid, etc.)
    - Fragments (#section)
    - Trailing slashes
    - Parameter order
    
    This is DETERMINISTIC - same input always produces same output.
    
    Args:
        results: List of search result dictionaries with 'url' key
        
    Returns:
        List of unique results (first occurrence kept when duplicates found)
    """
    seen_urls = set()
    unique_results = []

    for r in results:
        url = r.get("url")
        
        # Normalize URL to canonical form
        canonical = normalize_url(url)
        
        # Only keep if we haven't seen this canonical URL before
        if canonical and canonical not in seen_urls:
            seen_urls.add(canonical)
            unique_results.append(r)
        else:
            # Log duplicate for debugging (optional)
            if canonical and canonical in seen_urls:
                logger.debug(f"Removing duplicate URL: {url} (canonical: {canonical})")

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
    
    Guardrails (in order of application):
    1. Zero-signal check: All counts == 0 → LOW (defensive programming)
    2. Workaround cap: intensity==0 AND complaints<=1 → cap workaround at 3
    3. DRASTIC guardrail: intensity_level != HIGH → downgrade to SEVERE
    4. SEVERE guardrail: intensity_count == 0 → downgrade to MODERATE
    
    All guardrails are deterministic and rule-based, NOT weight changes.
    
    Args:
        signals: Dictionary with intensity_count, complaint_count, workaround_count
        
    Returns:
        Problem level string: "DRASTIC", "SEVERE", "MODERATE", or "LOW"
    """
    # Input validation: ensure all required keys exist with default 0
    intensity_count = signals.get("intensity_count", 0)
    complaint_count = signals.get("complaint_count", 0)
    workaround_count = signals.get("workaround_count", 0)
    
    # GUARDRAIL 1: Zero-signal sanity check (defensive programming)
    total_signals = intensity_count + complaint_count + workaround_count
    
    if total_signals == 0:
        logger.info("Zero signals detected - returning LOW")
        return "LOW"
    
    # GUARDRAIL 2: Workaround cap when intensity/complaints are minimal
    # Prevents workaround-only problems from inflating severity
    effective_workaround = workaround_count
    if intensity_count == 0 and complaint_count <= 1:
        effective_workaround = min(workaround_count, 3)
        if effective_workaround < workaround_count:
            logger.info(
                f"Applying workaround cap: intensity=0, complaints={complaint_count}, "
                f"capping workaround from {workaround_count} to {effective_workaround}"
            )
    
    # Calculate score with capped workaround count
    score = (
        3 * intensity_count +
        2 * complaint_count +
        1 * effective_workaround
    )
    
    # Compute intensity level for guardrail checks
    intensity_level = normalize_level(intensity_count)
    
    # Initial classification based on score
    if score >= 15:
        problem_level = "DRASTIC"
    elif score >= 8:
        problem_level = "SEVERE"
    elif score >= 4:
        problem_level = "MODERATE"
    else:
        problem_level = "LOW"
    
    # GUARDRAIL 3: DRASTIC only possible when intensity_level == HIGH
    if problem_level == "DRASTIC" and intensity_level != "HIGH":
        logger.info(
            f"Applying DRASTIC guardrail: intensity_level={intensity_level} (not HIGH), "
            f"downgrading from DRASTIC to SEVERE"
        )
        problem_level = "SEVERE"
    
    # GUARDRAIL 4: SEVERE requires intensity_count >= 1
    # Prevents false urgency from complaint/workaround volume alone
    if problem_level == "SEVERE" and intensity_count == 0:
        logger.info(
            f"Applying SEVERE guardrail: intensity_count=0, "
            f"downgrading from SEVERE to MODERATE"
        )
        problem_level = "MODERATE"
    
    # ASSERTIONS: Verify guardrail invariants
    assert problem_level != "DRASTIC" or intensity_level == "HIGH", \
        f"DRASTIC problem level requires HIGH intensity_level, got {intensity_level}"
    
    assert problem_level != "SEVERE" or intensity_count >= 1, \
        f"SEVERE problem level requires intensity_count >= 1, got {intensity_count}"
    
    return problem_level
