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


# ============================================================================
# PART 2: STAGE 2 - USER SOLUTION COMPETITOR DETECTION
# ============================================================================
#
# This is Stage 2 ONLY. Stage 1 behavior remains unchanged.
# 
# PURPOSE: Detect competitors specific to the user's solution (not just the problem)
#
# INPUT: Structured solution attributes (NOT marketing prose)
# OUTPUT: List of commercial competitors offering similar solutions
#
# CONSTRAINTS:
# - All logic is deterministic and rule-based
# - No LLM reasoning, no embeddings, no AI judgment
# - Stage 1 and Stage 2 are strictly separated
# ============================================================================

class UserSolution(BaseModel):
    """
    Structured description of the user's solution.
    
    This is NOT marketing prose - it's structured attributes that can be
    used to generate deterministic search queries.
    
    All fields are required to generate precise competitor queries.
    """
    core_action: str  # e.g., "validate", "generate", "analyze", "automate"
    input_required: str  # e.g., "startup idea text", "business plan", "meeting notes"
    output_type: str  # e.g., "validation report", "competitor list", "summary"
    target_user: str  # e.g., "startup founders", "product managers", "developers"
    automation_level: str  # e.g., "AI-powered", "automated", "manual", "semi-automated"

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


def extract_canonical_domain(url):
    """
    Extract canonical domain from URL for competitor deduplication.
    
    ISSUE 1 FIX: Use canonical domain as unique key for competitors.
    This prevents the same competitor from appearing multiple times
    (e.g., ValidatorAI from different pages/paths).
    
    Rules:
    - Extract domain without www prefix
    - Lowercase for case-insensitive comparison
    - Remove port if present
    - Return None for invalid URLs
    
    Examples:
    - "https://www.validatorai.com/pricing" → "validatorai.com"
    - "https://ValidatorAI.com/about" → "validatorai.com"
    - "http://www.example.com:8080/path" → "example.com"
    
    Args:
        url: URL string
        
    Returns:
        Canonical domain string, or None if invalid
    """
    if not url or not isinstance(url, str):
        return None
    
    try:
        parsed = urlparse(url.strip())
        
        if not parsed.netloc:
            return None
        
        # Extract domain (netloc might include port)
        domain = parsed.netloc.lower()
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Remove www prefix for canonical form
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    except Exception as e:
        logger.debug(f"Failed to extract domain from URL '{url}': {e}")
        return None


def deduplicate_competitors_by_domain(competitors):
    """
    ISSUE 1 FIX: Deduplicate competitors using canonical domain as unique key.
    
    This prevents the same competitor from appearing multiple times in the list
    (e.g., ValidatorAI appearing twice from different pages).
    
    CRITICAL: This MUST be called BEFORE:
    - competitor_density calculation
    - market_fragmentation inference
    
    Args:
        competitors: List of competitor dicts with 'url' and other fields
        
    Returns:
        List of unique competitors (first occurrence kept per domain)
    """
    seen_domains = set()
    unique_competitors = []
    duplicates_removed = 0
    
    for competitor in competitors:
        url = competitor.get('url', '')
        domain = extract_canonical_domain(url)
        
        if domain and domain not in seen_domains:
            seen_domains.add(domain)
            unique_competitors.append(competitor)
        elif domain in seen_domains:
            # Duplicate competitor found
            duplicates_removed += 1
            logger.debug(
                f"Removing duplicate competitor: {competitor.get('name', 'Unknown')} "
                f"(domain: {domain}, duplicate of existing competitor)"
            )
        else:
            # Invalid URL - keep competitor but warn
            logger.warning(
                f"Competitor has invalid URL, keeping anyway: "
                f"{competitor.get('name', 'Unknown')}"
            )
            unique_competitors.append(competitor)
    
    if duplicates_removed > 0:
        logger.info(
            f"Removed {duplicates_removed} duplicate competitor(s) "
            f"(reduced from {len(competitors)} to {len(unique_competitors)})"
        )
    
    return unique_competitors


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


# ============================================================================
# COMPETITION AND CONTENT SATURATION ANALYSIS
# ============================================================================

# ============================================================================
# PART 1: COMMERCIAL VS CONTENT CLASSIFICATION FIX
# ============================================================================
# 
# ISSUE: Blogs, Reddit, and Quora are being misclassified as "commercial competitors"
# 
# FIX: A result may be classified as COMMERCIAL ONLY IF ALL conditions are true:
# 1. The page is a FIRST-PARTY product or SaaS site (not a content/discussion site)
# 2. The page explicitly offers the solution directly
# 3. Strong product signals are present (pricing, signup, dashboard)
# 4. The source is NOT: Reddit, Quora, Medium, review sites, listicles, blogs
# 
# PRECEDENCE: commercial > diy > content > unknown
# ============================================================================

# Content site domains that should NEVER be classified as commercial
# These are sites that DISCUSS or REVIEW products, not first-party product sites
CONTENT_SITE_DOMAINS = {
    # Social/Discussion platforms
    'reddit.com', 'quora.com', 'stackexchange.com', 'stackoverflow.com',
    'hackernews.com', 'news.ycombinator.com',
    
    # Blogging platforms
    'medium.com', 'substack.com', 'wordpress.com', 'blogger.com', 
    'dev.to', 'hashnode.com', 'ghost.io',
    
    # Review/Comparison sites
    'g2.com', 'capterra.com', 'trustpilot.com', 'producthunt.com',
    'getapp.com', 'softwareadvice.com', 'trustradius.com',
    
    # Video platforms (reviews/tutorials)
    'youtube.com', 'vimeo.com',
    
    # Q&A and forums
    'answers.com', 'yahoo.com/answers',
}

# Strong product signals that indicate a FIRST-PARTY commercial site
# These must be present along with other indicators
STRONG_PRODUCT_SIGNALS = {
    # Direct purchase/signup actions
    'sign up', 'signup', 'get started', 'start free trial', 'free trial',
    'create account', 'register now', 'join now', 'start now',
    
    # Pricing indicators
    'pricing', 'plans', 'subscription', 'price', 'cost',
    
    # Product access
    'dashboard', 'login', 'log in', 'access your account',
    
    # Business model
    'saas', 'platform', 'software as a service',
    
    # Enterprise/commercial focus
    'enterprise', 'business', 'teams', 'organizations',
}

# Commercial supporting keywords (weaker signals)
COMMERCIAL_KEYWORDS = {
    'buy', 'purchase', 'license', 'trial', 'demo',
    'company', 'inc', 'corp', 'llc', 'plan'
}

# DIY/tutorial keywords
DIY_KEYWORDS = {
    'how to', 'diy', 'custom', 'manual', 'open source',
    'github', 'python script', 'bash script', 'shell script', 'javascript code',
    'code snippet', 'build your own', 'create your own',
    'homebrew', 'self-hosted', 'tutorial', 'free and open',
    'completely free', 'totally free', 'free forever', 'diy solution'
}

# Content/discussion keywords
CONTENT_KEYWORDS = {
    'review', 'comparison', 'vs', 'versus', 'best', 'top',
    'guide', 'blog', 'article', 'post', 'discussion', 'forum',
    'thread', 'comment', 'opinion', 'thoughts on', 'what do you think',
    'listicle', 'roundup', 'collection'
}


def is_content_site(url):
    """
    Check if URL belongs to a content/discussion site.
    
    Content sites discuss, review, or compare products but are NOT
    first-party product sites themselves.
    
    Args:
        url: URL string to check
        
    Returns:
        True if URL is from a content site, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    url_lower = url.lower()
    
    # Extract domain from URL (between :// and next /)
    # Handle URLs with or without paths
    if '://' not in url_lower:
        return False
    
    # Get the part after ://
    after_protocol = url_lower.split('://', 1)[1]
    
    # Extract domain (everything before first / or end of string)
    if '/' in after_protocol:
        domain_part = after_protocol.split('/')[0]
    else:
        domain_part = after_protocol
    
    # Remove port if present
    if ':' in domain_part:
        domain_part = domain_part.split(':')[0]
    
    # Check if domain matches any content site
    for content_domain in CONTENT_SITE_DOMAINS:
        # Match exact domain or any subdomain
        # e.g., reddit.com, www.reddit.com, old.reddit.com, docs.reddit.com
        if domain_part == content_domain or domain_part.endswith('.' + content_domain):
            return True
    
    return False


# ============================================================================
# NLP ASSISTANT FUNCTIONS
# ============================================================================
# These functions use NLP to SUGGEST features and labels.
# They are ASSISTANTS, not DECIDERS.
# 
# CRITICAL RULES:
# - NLP suggests candidates or features
# - Deterministic rules make ALL final decisions
# - NLP outputs are NEVER written directly to final JSON
# - If NLP fails, rules must still work (graceful fallback)
# ============================================================================

def nlp_suggest_page_intent(text: str) -> str:
    """
    NLP ASSISTANT: Suggest page intent based on text analysis.
    
    This function uses NLP to SUGGEST (not decide) the primary intent of a page.
    
    IMPORTANT: This is a SUGGESTION only. The calling function must apply
    deterministic rules to make the final classification decision.
    
    Possible intents:
    - SELLING: Page is trying to sell a product/service
    - DOCUMENTATION: Technical docs, API references
    - GUIDE: How-to guides, tutorials
    - DISCUSSION: Forums, Q&A, comments
    - REVIEW: Product reviews, comparisons
    - UNKNOWN: Cannot determine intent
    
    Args:
        text: Text to analyze (title + snippet)
        
    Returns:
        Intent label (suggestion only, NOT a final decision)
    """
    if not text or not text.strip():
        return "UNKNOWN"
    
    # === NLP PREPROCESSING ===
    # Use existing NLP utilities for consistent preprocessing
    preprocessed = preprocess_text(text)
    
    # === INTENT DETECTION USING NLP-ENHANCED MATCHING ===
    # These are SUGGESTIONS based on NLP analysis
    # Rules will validate and make final decisions
    
    # SELLING intent keywords
    selling_keywords = [
        'pricing', 'subscription', 'sign up', 'free trial',
        'get started', 'buy now', 'purchase', 'upgrade'
    ]
    
    # DOCUMENTATION intent keywords
    docs_keywords = [
        'documentation', 'api reference', 'developer guide',
        'api docs', 'technical specs'
    ]
    
    # GUIDE intent keywords
    guide_keywords = [
        'how to', 'tutorial', 'step by step', 'guide',
        'getting started', 'learn', 'beginners'
    ]
    
    # DISCUSSION intent keywords
    discussion_keywords = [
        'forum', 'thread', 'discussion', 'ask', 'question',
        'comment', 'reddit', 'stack overflow'
    ]
    
    # REVIEW intent keywords
    review_keywords = [
        'review', 'comparison', 'vs', 'versus', 'best',
        'alternatives', 'pros and cons'
    ]
    
    # Use NLP-enhanced matching for better accuracy
    has_selling = match_keywords_with_deduplication(selling_keywords, preprocessed)
    has_docs = match_keywords_with_deduplication(docs_keywords, preprocessed)
    has_guide = match_keywords_with_deduplication(guide_keywords, preprocessed)
    has_discussion = match_keywords_with_deduplication(discussion_keywords, preprocessed)
    has_review = match_keywords_with_deduplication(review_keywords, preprocessed)
    
    # Suggest intent based on strongest signal
    # This is a SUGGESTION - rules will decide final classification
    if has_review:
        return "REVIEW"
    elif has_discussion:
        return "DISCUSSION"
    elif has_guide:
        return "GUIDE"
    elif has_docs:
        return "DOCUMENTATION"
    elif has_selling:
        return "SELLING"
    else:
        return "UNKNOWN"


def nlp_extract_solution_cues(text: str) -> dict:
    """
    NLP ASSISTANT: Extract normalized keywords and cues from solution attributes.
    
    This function uses NLP to extract and normalize keywords that may hint at
    solution characteristics (e.g., "repairing" → "repair" → service-related).
    
    IMPORTANT: This provides HINTS only. The calling function must apply
    deterministic rules to make the final modality classification.
    
    Args:
        text: Solution attribute text (e.g., core_action, output_type)
        
    Returns:
        Dict with:
        - normalized_text: NLP-normalized text
        - stems: Stemmed tokens for matching variants
        - hints: Keyword hints (e.g., "service_related", "software_related")
    """
    if not text or not text.strip():
        return {
            'normalized_text': '',
            'stems': [],
            'hints': []
        }
    
    # === NLP PREPROCESSING ===
    # Use existing NLP utilities for consistent preprocessing
    preprocessed = preprocess_text(text)
    
    # Extract normalized text and stems
    normalized_text = preprocessed['original_text']
    stems = preprocessed['stems']
    
    # === HINT GENERATION ===
    # These are HINTS based on NLP analysis
    # Rules will use these as ONE input among many
    
    hints = []
    
    # Service-related hints (based on stemmed keywords)
    service_stems = {'repair', 'maintain', 'instal', 'clean', 'consult', 'train', 'servic'}
    if any(stem in service_stems for stem in stems):
        hints.append('service_related')
    
    # Software-related hints
    software_stems = {'automat', 'ai', 'algorithm', 'machin', 'intellig', 'platform', 'softwar'}
    if any(stem in software_stems for stem in stems):
        hints.append('software_related')
    
    # Physical product hints
    physical_stems = {'devic', 'hardwar', 'machin', 'gadget', 'product', 'equip'}
    if any(stem in physical_stems for stem in stems):
        hints.append('physical_related')
    
    return {
        'normalized_text': normalized_text,
        'stems': stems,
        'hints': hints
    }


# === NLP BOUNDARY — RULES DECIDE AFTER THIS POINT ===
# The functions above provide NLP-assisted suggestions and features.
# All classification decisions are made by deterministic rules below.


def classify_result_type(result):
    """
    Classify search result as commercial, diy, content, or unknown.
    
    CLASSIFICATION RULES (deterministic, no ML/AI):
    
    1. CONTENT (highest priority for content sites):
       - URL is from Reddit, Quora, Medium, review sites, blogs
       - These sites DISCUSS tools but don't offer them directly
       
    2. CONTENT (comparison/review articles):
       - Contains review/comparison keywords (vs, review, best, comparison)
       - Even if also contains product signals
       
    3. COMMERCIAL (only for first-party product sites):
       - NOT a content site (rules 1-2 don't apply)
       - Has STRONG product signals (signup, pricing, dashboard)
       - Explicitly offers the solution directly
       
    4. DIY:
       - Has DIY keywords (tutorials, open source, build your own)
       - Not classified as content or commercial
       
    5. UNKNOWN:
       - Doesn't match any of the above
    
    PRECEDENCE: commercial > diy > content > unknown
    (But content site check and review/comparison check happen FIRST)
    
    NLP INTEGRATION:
    - NLP assists with keyword matching (handles morphological variants)
    - NLP suggests page intent (ASSISTIVE only)
    - Rules make ALL final classification decisions
    
    Args:
        result: Search result dict with 'title', 'snippet', and optionally 'url'
        
    Returns:
        'commercial', 'diy', 'content', or 'unknown'
    """
    url = result.get('url', '')
    text = (
        (result.get("title") or "") + " " +
        (result.get("snippet") or "")
    ).lower()
    
    # === NLP PREPROCESSING (ASSISTIVE) ===
    # NLP helps with better keyword matching (morphological variants)
    # Rules still make all decisions
    try:
        preprocessed = preprocess_text(text)
        nlp_available = True
    except Exception as e:
        logger.debug(f"NLP preprocessing failed, falling back to simple matching: {e}")
        preprocessed = None
        nlp_available = False
    
    # Get NLP intent suggestion (ASSISTIVE only, rules decide)
    try:
        nlp_intent_suggestion = nlp_suggest_page_intent(text) if nlp_available else "UNKNOWN"
        logger.debug(f"NLP intent suggestion: {nlp_intent_suggestion}")
    except Exception as e:
        logger.debug(f"NLP intent suggestion failed: {e}")
        nlp_intent_suggestion = "UNKNOWN"
    
    # === NLP BOUNDARY — RULES DECIDE FROM HERE ===
    
    # RULE 1: Check if this is a content/discussion site FIRST
    # Content sites should NEVER be classified as commercial
    if is_content_site(url):
        logger.debug(f"Classified as CONTENT (content site domain): {url}")
        return 'content'
    
    # Check for signal presence using NLP-enhanced matching when available
    if nlp_available and preprocessed:
        # NLP-enhanced matching (catches morphological variants)
        has_strong_product = match_keywords_with_deduplication(
            list(STRONG_PRODUCT_SIGNALS), preprocessed
        )
        has_commercial = match_keywords_with_deduplication(
            list(COMMERCIAL_KEYWORDS), preprocessed
        )
        has_diy = match_keywords_with_deduplication(
            list(DIY_KEYWORDS), preprocessed
        )
    else:
        # Fallback to simple matching if NLP unavailable
        has_strong_product = any(signal in text for signal in STRONG_PRODUCT_SIGNALS)
        has_commercial = any(kw in text for kw in COMMERCIAL_KEYWORDS)
        has_diy = any(kw in text for kw in DIY_KEYWORDS)
    
    # RULE 2: Strong CONTENT indicators (comparison/review articles)
    # These should be classified as content even if they mention pricing
    # NLP intent suggestion helps identify review pages
    # ISSUE 2 FIX: Enhanced content patterns to catch blogs/guides about tools
    strong_content_patterns = [
        'vs', 'versus', 'comparison', 'compare', 'review', 'reviews',
        'best tool', 'best software', 'best app', 'best product', 'best solution',
        'best crm', 'best platform', 'best service',
        'top tool', 'top software', 'top app', 'top product',
        'roundup', 'listicle', 'alternatives to',
        # ISSUE 2 FIX: Add patterns for guides and prompts
        'guide to', 'how to use', 'prompts for', 'prompt collection',
        'ai prompts', 'tips for', 'tutorial on', 'blog post',
        'article about', 'everything you need to know', 'ultimate guide',
        'beginner guide', 'getting started with', 'introduction to'
    ]
    has_strong_content = any(pattern in text for pattern in strong_content_patterns)
    
    # Use NLP intent as additional signal (not decision)
    if nlp_intent_suggestion in ["REVIEW", "DISCUSSION", "GUIDE"]:
        has_strong_content = True  # NLP suggests review/discussion/guide
    
    # ISSUE 2 FIX: Weaker content signals - expanded to catch more explainer content
    weak_content_signals = [
        'review', 'comparison', 'guide', 'blog', 'article',
        'tips', 'tricks', 'prompts', 'examples', 'templates'
    ]
    has_weak_content = any(signal in text for signal in weak_content_signals)
    
    # ISSUE 2 FIX: Check for DIY BEFORE checking strong content
    # DIY tutorials (how to build, create your own) should be DIY, not content
    # Only check for strong content patterns that are NOT DIY-related
    diy_specific_patterns = [
        'how to build', 'build your own', 'create your own', 'diy',
        'open source', 'github', 'script', 'tutorial'
    ]
    has_diy_specific = any(pattern in text for pattern in diy_specific_patterns)
    
    # If has DIY-specific patterns, skip strong content check (DIY takes priority)
    if has_diy_specific and has_diy:
        logger.debug(f"Classified as DIY (tutorial/build-your-own): {url}")
        return 'diy'
    
    # ISSUE 2 FIX: When uncertain, prefer content over commercial
    # Implements "seller-vs-explainer" invariant with bias toward exclusion
    # If uncertain → EXCLUDE from commercial (classify as content)
    if has_strong_content:
        # This is a comparison/review/guide article, not a product page
        logger.debug(f"Classified as CONTENT (comparison/review/guide article): {url}")
        return 'content'
    
    # RULE 3: COMMERCIAL classification (strict requirements)
    # Must have STRONG product signals AND not be a content/review article
    # This prevents review articles from being commercial just because they mention pricing
    if has_strong_product and not has_diy and not has_weak_content:
        logger.debug(f"Classified as COMMERCIAL (strong product signals): {url}")
        return 'commercial'
    
    # RULE 4: DIY classification (fallback for cases not caught above)
    if has_diy and not has_strong_product:
        logger.debug(f"Classified as DIY (tutorial/open source): {url}")
        return 'diy'
    
    # RULE 5: CONTENT classification (based on weak content keywords)
    # Articles that discuss/review tools but aren't on known content domains
    # Only classify as content if there are weak content keywords but NO strong product signals
    if has_weak_content and not has_strong_product and not has_diy:
        logger.debug(f"Classified as CONTENT (review/comparison): {url}")
        return 'content'
    
    # RULE 6: Mixed signals or unclear
    if has_strong_product and has_diy:
        # Mixed signals - commercial wins (precedence rule)
        logger.debug(f"Classified as COMMERCIAL (mixed signals, precedence): {url}")
        return 'commercial'
    
    if has_commercial and not has_strong_product:
        # Weak commercial signals without strong product signals
        # Likely a review/discussion, classify as content
        logger.debug(f"Classified as CONTENT (weak commercial signals): {url}")
        return 'content'
    
    # Default: unknown
    logger.debug(f"Classified as UNKNOWN (no clear signals): {url}")
    return 'unknown'


def separate_tool_workaround_results(tool_results, workaround_results):
    """
    Re-classify tool and workaround results to ensure bucket purity.
    
    UPDATED for PART 1 FIX:
    - Move COMMERCIAL results to tool_results
    - Move DIY results to workaround_results  
    - EXCLUDE CONTENT results (blogs, Reddit, Quora, reviews)
    - Handle UNKNOWN results with logging
    
    This fixes ISSUE 1: Query bucket mixing + content misclassification.
    
    Args:
        tool_results: Results from tool_queries
        workaround_results: Results from workaround_queries
        
    Returns:
        Tuple of (corrected_tool_results, corrected_workaround_results)
    """
    corrected_tool = []
    corrected_workaround = []
    content_excluded_count = 0
    
    # Re-classify tool results
    for result in tool_results:
        result_type = classify_result_type(result)
        if result_type == 'commercial':
            # True commercial competitor - keep in tool bucket
            corrected_tool.append(result)
        elif result_type == 'diy':
            # DIY solution - move to workaround bucket
            corrected_workaround.append(result)
        elif result_type == 'content':
            # Content site (blog, Reddit, Quora, review) - EXCLUDE
            # These are NOT competitors, just discussing the problem
            content_excluded_count += 1
            logger.debug(f"Excluding CONTENT from competitors: {result.get('url', 'unknown')}")
        else:
            # Unknown - keep in original bucket with warning
            corrected_tool.append(result)
            logger.debug(f"Ambiguous tool result (unknown): {result.get('url', 'unknown')}")
    
    # Re-classify workaround results
    for result in workaround_results:
        result_type = classify_result_type(result)
        if result_type == 'diy':
            # DIY/tutorial - keep in workaround bucket
            corrected_workaround.append(result)
        elif result_type == 'commercial':
            # Commercial product - move to tool bucket
            corrected_tool.append(result)
        elif result_type == 'content':
            # Content site - EXCLUDE
            content_excluded_count += 1
            logger.debug(f"Excluding CONTENT from alternatives: {result.get('url', 'unknown')}")
        else:
            # Unknown - keep in original bucket
            corrected_workaround.append(result)
    
    # Log content exclusion statistics
    if content_excluded_count > 0:
        logger.info(
            f"Excluded {content_excluded_count} content sites "
            f"(blogs/Reddit/Quora/reviews) from competition analysis"
        )
    
    # Deduplicate after reclassification
    corrected_tool = deduplicate_results(corrected_tool)
    corrected_workaround = deduplicate_results(corrected_workaround)
    
    return corrected_tool, corrected_workaround


def compute_competition_pressure(competitor_count, competition_type='commercial'):
    """
    Compute competition pressure level based on competitor count.
    
    This implements ISSUE 4: Deterministic competition pressure rules.
    
    Thresholds:
    - Commercial: LOW (0-3), MEDIUM (4-9), HIGH (10+)
    - DIY: LOW (0-6), MEDIUM (7-19), HIGH (20+) [2x tolerance]
    
    Args:
        competitor_count: Number of competitors found
        competition_type: 'commercial' or 'diy'
        
    Returns:
        "LOW", "MEDIUM", or "HIGH"
    """
    # Adjust thresholds based on competition type
    if competition_type == 'diy':
        # DIY workarounds are less threatening than commercial competitors
        # Double the thresholds (more tolerance for workarounds)
        low_threshold = 6
        high_threshold = 20
    else:  # commercial
        # Standard thresholds for commercial competitors
        low_threshold = 3
        high_threshold = 10
    
    # Apply thresholds
    if competitor_count <= low_threshold:
        pressure = "LOW"
    elif competitor_count < high_threshold:
        pressure = "MEDIUM"
    else:
        pressure = "HIGH"
    
    logger.info(
        f"Competition pressure: {pressure} "
        f"({competitor_count} {competition_type} competitors)"
    )
    
    return pressure


# Content saturation classification keywords
CLICKBAIT_SIGNALS = {
    # Clickbait patterns
    'top 10', 'best of', 'you won\'t believe', 'shocking',
    'ultimate guide', 'secret', 'hack', 'trick',
    'one simple', 'this will change', 'must read',
    # Low-value patterns
    'listicle', 'roundup', 'collection', 'compilation'
}

TREND_SIGNALS = {
    # Year-specific (transient)
    '2024', '2025', '2026',
    # Event-specific
    'pandemic', 'covid', 'lockdown', 'new normal',
    # Trend/fad indicators
    'trending', 'hot topic', 'latest', 'brand new',
    'just released', 'this week', 'this month'
}

TECHNICAL_SIGNALS = {
    # Technical depth
    'how to', 'tutorial', 'guide', 'documentation',
    'implementation', 'architecture', 'algorithm',
    'step by step', 'walkthrough', 'example',
    # Problem-solving
    'solution', 'fix', 'debugging', 'troubleshooting',
    'optimize', 'improve', 'automate'
}


def classify_saturation_signal(content_count, blog_results):
    """
    Classify whether high content count is NEGATIVE or NEUTRAL.
    
    This implements ISSUE 3: Content saturation interpretation rules.
    
    Rules (deterministic, no ML):
    1. If content_count < 6: NEUTRAL (low saturation)
    2. If >40% clickbait content: NEGATIVE (low-quality)
    3. If >50% trend/year content: NEGATIVE (transient fad)
    4. If >50% technical content: NEUTRAL (evergreen)
    5. Otherwise: NEUTRAL (benefit of doubt)
    
    Args:
        content_count: Number of blog/guide results
        blog_results: List of search results from blog_queries
        
    Returns:
        "NEGATIVE" or "NEUTRAL"
    """
    # Rule 1: Low count is always neutral
    if content_count < 6:
        return "NEUTRAL"
    
    # Count signal occurrences
    clickbait_count = 0
    trend_count = 0
    technical_count = 0
    
    for result in blog_results:
        text = (
            (result.get('title') or '') + ' ' + 
            (result.get('snippet') or '')
        ).lower()
        
        if any(signal in text for signal in CLICKBAIT_SIGNALS):
            clickbait_count += 1
        
        if any(signal in text for signal in TREND_SIGNALS):
            trend_count += 1
        
        if any(signal in text for signal in TECHNICAL_SIGNALS):
            technical_count += 1
    
    # Compute ratios
    clickbait_ratio = clickbait_count / content_count
    trend_ratio = trend_count / content_count
    technical_ratio = technical_count / content_count
    
    # Rule 2: High clickbait ratio → NEGATIVE
    if clickbait_ratio > 0.4:
        logger.info(
            f"Content saturation is NEGATIVE: {clickbait_ratio:.1%} clickbait "
            f"({clickbait_count}/{content_count} results)"
        )
        return "NEGATIVE"
    
    # Rule 3: High trend ratio → NEGATIVE
    if trend_ratio > 0.5:
        logger.info(
            f"Content saturation is NEGATIVE: {trend_ratio:.1%} trend content "
            f"({trend_count}/{content_count} results)"
        )
        return "NEGATIVE"
    
    # Rule 4: High technical ratio → NEUTRAL
    if technical_ratio > 0.5:
        logger.info(
            f"Content saturation is NEUTRAL: {technical_ratio:.1%} technical "
            f"({technical_count}/{content_count} results)"
        )
        return "NEUTRAL"
    
    # Rule 5: Default to NEUTRAL
    logger.info("Content saturation is NEUTRAL: Mixed quality, defaulting to neutral")
    return "NEUTRAL"


# Solution-class existence detection keywords
# Organized by signal type for easier maintenance
COMPARISON_SIGNALS = {
    'vs', 'versus', 'comparison', 'alternatives to',
    'best', 'top', 'leading', 'compare'
}

MARKET_MATURITY_SIGNALS = {
    'market', 'industry', 'providers', 'vendors',
    'options', 'solutions available', 'choose from'
}

SOLUTION_CLASS_SIGNALS = {
    # Category/market indicators
    'software', 'platform', 'tool', 'solution', 'system',
    'service', 'product', 'application', 'app',
}.union(COMPARISON_SIGNALS).union(MARKET_MATURITY_SIGNALS)

# Category name extraction patterns
# Purpose: Used to extract potential category names from text (e.g., "CRM software")
# Overlap with SOLUTION_CLASS_SIGNALS is intentional - these patterns help identify
# specific category phrases like "project management software" or "CRM platform"
CATEGORY_NAME_PATTERNS = {
    'software', 'platform', 'tools', 'solution', 'system',
    'service', 'app', 'suite', 'management'
}

# Solution-class existence detection thresholds
# These determine confidence levels for category existence
SOLUTION_CLASS_THRESHOLDS = {
    # Minimum ratio of results with solution-class language for detection
    'solution_language_min': 0.3,       # 30% of results
    
    # Comparison article thresholds (strong indicator of established category)
    'comparison_high': 0.3,             # 30% comparison articles = HIGH confidence
    'comparison_medium': 0.2,           # 20% comparison articles = MEDIUM confidence
    
    # Market maturity thresholds (indicates recognized industry)
    'market_maturity_min': 0.2,         # 20% market/industry language
    
    # Solution language thresholds for different confidence levels
    'solution_medium': 0.5,             # 50% solution language = MEDIUM confidence
    'solution_low': 0.4,                # 40% solution language = LOW confidence
    
    # Output limits
    'category_indicators_limit': 10,    # Max unique category indicators to return
}


def detect_solution_class_existence(tool_results):
    """
    Detect whether a dedicated product category/solution-class exists.
    
    This is a product-agnostic market signal that indicates market maturity:
    - If a category exists (e.g., "CRM software", "project management tools"),
      the market has recognized this problem as worthy of specialized products
    - If no category exists, this may be a novel/emerging problem space
    
    Detection rules (deterministic):
    1. Check if results mention category/comparison language
    2. Look for multiple products being discussed together (comparison articles)
    3. Detect market/industry language suggesting established category
    
    Args:
        tool_results: Commercial product search results
        
    Returns:
        Dict with:
        - exists: True/False (category exists)
        - confidence: LOW/MEDIUM/HIGH
        - evidence: List of signals detected
    """
    if not tool_results:
        return {
            'exists': False,
            'confidence': 'NONE',
            'evidence': [],
            'category_indicators': []
        }
    
    # Count signal occurrences
    solution_class_count = 0
    comparison_count = 0
    market_maturity_count = 0
    category_indicators = []
    
    for result in tool_results:
        text = (
            (result.get('title') or '') + ' ' + 
            (result.get('snippet') or '')
        ).lower()
        
        # Check for solution-class signals
        if any(signal in text for signal in SOLUTION_CLASS_SIGNALS):
            solution_class_count += 1
        
        # Check for comparison signals (strong indicator of category)
        if any(signal in text for signal in COMPARISON_SIGNALS):
            comparison_count += 1
        
        # Check for market maturity signals
        if any(signal in text for signal in MARKET_MATURITY_SIGNALS):
            market_maturity_count += 1
        
        # Extract potential category names (e.g., "CRM software", "project management tools")
        for pattern in CATEGORY_NAME_PATTERNS:
            if pattern in text:
                # Extract a few words before and after the pattern
                words = text.split()
                for i, word in enumerate(words):
                    if pattern in word:
                        # Get context around the pattern (2 words before, pattern, 2 words after)
                        start = max(0, i - 2)
                        end = min(len(words), i + 3)
                        context = ' '.join(words[start:end])
                        if len(context) > 5:  # Meaningful context
                            category_indicators.append(context)
    
    total_results = len(tool_results)
    
    # Compute ratios
    solution_class_ratio = solution_class_count / total_results
    comparison_ratio = comparison_count / total_results
    market_maturity_ratio = market_maturity_count / total_results
    
    # Collect evidence
    evidence = []
    
    if solution_class_ratio > SOLUTION_CLASS_THRESHOLDS['solution_language_min']:
        evidence.append(f"{solution_class_ratio:.0%} of results mention solution/product language")
    
    if comparison_ratio > SOLUTION_CLASS_THRESHOLDS['comparison_medium']:
        evidence.append(f"{comparison_ratio:.0%} of results are comparison/review articles")
    
    if market_maturity_ratio > SOLUTION_CLASS_THRESHOLDS['market_maturity_min']:
        evidence.append(f"{market_maturity_ratio:.0%} of results mention market/industry")
    
    # Deterministic rules for existence and confidence
    # Rule 1: HIGH confidence - comparison articles + market language (established category)
    if (comparison_ratio > SOLUTION_CLASS_THRESHOLDS['comparison_high'] and 
        market_maturity_ratio > SOLUTION_CLASS_THRESHOLDS['market_maturity_min']):
        exists = True
        confidence = 'HIGH'
        evidence.append("Strong category signals: comparison articles + market maturity indicators")
    
    # Rule 2: MEDIUM confidence - solution-class language + some comparisons
    elif (solution_class_ratio > SOLUTION_CLASS_THRESHOLDS['solution_medium'] and 
          comparison_ratio > SOLUTION_CLASS_THRESHOLDS['comparison_medium']):
        exists = True
        confidence = 'MEDIUM'
        evidence.append("Moderate category signals: solution language + comparison articles")
    
    # Rule 3: LOW confidence - solution-class language but no comparisons
    elif solution_class_ratio > SOLUTION_CLASS_THRESHOLDS['solution_low']:
        exists = True
        confidence = 'LOW'
        evidence.append("Weak category signals: solution language present but limited comparisons")
    
    # Rule 4: No category detected
    else:
        exists = False
        confidence = 'NONE'
        evidence.append("No strong category signals detected - may be novel/emerging problem space")
    
    # Deduplicate category indicators (limit to configured max)
    # Deduplicate first, then limit to ensure we get up to limit unique items
    limit = SOLUTION_CLASS_THRESHOLDS['category_indicators_limit']
    unique_categories = list(set(category_indicators))[:limit]
    
    logger.info(
        f"Solution-class existence: {exists} (confidence: {confidence}) - "
        f"{len(evidence)} signals detected"
    )
    
    return {
        'exists': exists,
        'confidence': confidence,
        'evidence': evidence,
        'category_indicators': unique_categories
    }


# ============================================================================
# DISABLED: Problem-based competition analysis
# ============================================================================
# This function has been DISABLED as part of the Stage 1/Stage 2 separation.
# 
# REASON: Competition analysis MUST be driven by the USER SOLUTION, not the problem.
# Problem-based competitor search violates the architectural boundary:
#   - Stage 1 = Problem Reality Engine (no market signals)
#   - Stage 2 = User Solution Market Analysis (all market signals)
#
# Market analysis now happens ONLY in Stage 2 via analyze_user_solution_competitors()
# ============================================================================
def analyze_competition(problem: str):
    """
    DISABLED: Problem-based competition analysis.
    
    This function has been disabled to enforce Stage 1/Stage 2 separation.
    Competition analysis now happens ONLY in Stage 2 when a user solution is provided.
    
    DO NOT RE-ENABLE this function. It violates architectural boundaries.
    
    Args:
        problem: Problem statement (NOT used for competition analysis)
        
    Returns:
        Empty dict indicating no problem-based competition analysis
    """
    logger.warning(
        "analyze_competition() called but is DISABLED. "
        "Competition analysis must be done in Stage 2 with a user solution."
    )
    return {
        "disabled": True,
        "reason": "Competition analysis requires a user solution (Stage 2 only)",
        "message": "Use /analyze-user-solution endpoint with solution attributes"
    }


# ============================================================================
# DISABLED: Problem-based content saturation analysis
# ============================================================================
# This function has been DISABLED as part of the Stage 1/Stage 2 separation.
#
# REASON: Content saturation MUST be relative to the USER SOLUTION, not the problem.
# Problem-based content analysis violates the architectural boundary.
#
# Content saturation now happens ONLY in Stage 2 as a market strength parameter.
# ============================================================================
def analyze_content_saturation(problem: str):
    """
    DISABLED: Problem-based content saturation analysis.
    
    This function has been disabled to enforce Stage 1/Stage 2 separation.
    Content saturation analysis now happens ONLY in Stage 2 relative to the user solution.
    
    DO NOT RE-ENABLE this function. It violates architectural boundaries.
    
    Args:
        problem: Problem statement (NOT used for content saturation analysis)
        
    Returns:
        Empty dict indicating no problem-based content saturation analysis
    """
    logger.warning(
        "analyze_content_saturation() called but is DISABLED. "
        "Content saturation analysis must be done in Stage 2 relative to user solution."
    )
    return {
        "disabled": True,
        "reason": "Content saturation requires a user solution (Stage 2 only)",
        "message": "Use /analyze-user-solution endpoint with solution attributes"
    }


@app.post("/analyze-market")
def analyze_market(data: IdeaInput):
    """
    UPDATED: Market analysis endpoint (Stage 1 only - problem severity).
    
    ARCHITECTURAL CHANGE:
    This endpoint now returns ONLY Stage 1 problem severity analysis.
    Competition and content saturation have been removed from this endpoint.
    
    REASON: Market analysis must be driven by USER SOLUTION, not problem statement.
    - Stage 1 (this endpoint) = Problem Reality Engine (no market signals)
    - Stage 2 (/analyze-user-solution) = User Solution Market Analysis (all market signals)
    
    For market analysis, use /analyze-user-solution with solution attributes.
    
    Returns:
        Dict with problem severity analysis only (NO competition or content saturation)
    """
    # Problem severity analysis (Stage 1 - unchanged)
    problem_analysis = analyze_idea(data)
    
    return {
        "problem": problem_analysis,
        # NOTE: competition and content_saturation fields removed
        # These are now Stage 2 only (available via /analyze-user-solution)
    }


# ============================================================================
# STAGE 2: USER-SOLUTION COMPETITOR DETECTION
# ============================================================================

def normalize_core_action_to_verb(core_action: str) -> str:
    """
    ISSUE 3 FIX: Normalize core_action to verb+object form for internal use.
    
    This function converts noun-like phrases (e.g., "AI startup validator")
    to action-oriented verb phrases (e.g., "validate startups").
    
    CRITICAL RULES:
    - This is for INTERNAL logic only (query generation, modality inference)
    - Do NOT modify user-facing input
    - If already action-oriented, return as-is
    - Handles common noun→verb patterns deterministically
    
    Examples:
    - "AI startup idea validator" → "validate startup ideas"
    - "validator" → "validate"
    - "generator" → "generate"
    - "analyzer" → "analyze"
    - "validate" → "validate" (already verb)
    
    Args:
        core_action: Original core_action from user input
        
    Returns:
        Normalized action phrase (verb form)
    """
    text = core_action.lower().strip()
    
    # Common noun-to-verb transformations (deterministic mapping)
    # Order matters: check longer patterns first to avoid partial matches
    noun_to_verb_patterns = [
        # -ator suffix (validator → validate)
        ('validator', 'validate'),
        ('generator', 'generate'),
        ('analyzer', 'analyze'),
        ('creator', 'create'),
        ('optimizer', 'optimize'),
        ('automator', 'automate'),
        
        # -er suffix (checker → check)
        ('checker', 'check'),
        ('tester', 'test'),
        ('scanner', 'scan'),
        ('tracker', 'track'),
        ('builder', 'build'),
        ('finder', 'find'),
        ('manager', 'manage'),
        ('scheduler', 'schedule'),
        ('planner', 'plan'),
        
        # -tion suffix (validation → validate)
        ('validation', 'validate'),
        ('generation', 'generate'),
        ('analysis', 'analyze'),
        ('creation', 'create'),
        ('optimization', 'optimize'),
        ('automation', 'automate'),
        
        # -or suffix (advisor → advise)
        ('advisor', 'advise'),
        ('supervisor', 'supervise'),
    ]
    
    # Try to extract verb by pattern matching
    for noun_pattern, verb_form in noun_to_verb_patterns:
        if noun_pattern in text:
            # Replace the noun with verb form, keeping rest of phrase
            # E.g., "AI startup validator" → "AI startup validate"
            # Then clean up to get "validate startup"
            normalized = text.replace(noun_pattern, verb_form)
            
            # Clean up: remove common filler words and reorder if needed
            filler_words = {'ai', 'powered', 'smart', 'intelligent', 'automated'}
            words = normalized.split()
            meaningful_words = [w for w in words if w not in filler_words]
            
            # If we have multiple words, ensure verb comes first
            if len(meaningful_words) > 1 and meaningful_words[0] != verb_form:
                # Try to put verb first
                if verb_form in meaningful_words:
                    meaningful_words.remove(verb_form)
                    meaningful_words.insert(0, verb_form)
            
            result = ' '.join(meaningful_words)
            logger.debug(f"Normalized core_action: '{core_action}' → '{result}'")
            return result
    
    # If no pattern matched, check if it's already a verb phrase
    # Common action verbs that indicate it's already in correct form
    action_verbs = {
        'validate', 'generate', 'analyze', 'create', 'build', 'automate',
        'check', 'test', 'scan', 'track', 'manage', 'schedule', 'plan',
        'optimize', 'process', 'transform', 'convert', 'extract', 'parse',
        'summarize', 'classify', 'categorize', 'filter', 'sort', 'rank',
        'recommend', 'suggest', 'predict', 'forecast', 'estimate'
    }
    
    first_word = text.split()[0] if text.split() else ''
    if first_word in action_verbs:
        # Already in verb form, return cleaned up
        logger.debug(f"Core action already verb form: '{core_action}'")
        return text
    
    # No transformation found - return as-is with warning
    # This handles edge cases where user provides novel action phrases
    logger.debug(f"No normalization pattern found for: '{core_action}', using as-is")
    return text


def classify_solution_modality(solution: UserSolution):
    """
    Classify solution modality as SOFTWARE, SERVICE, PHYSICAL_PRODUCT, or HYBRID.
    
    This is a REQUIRED preprocessing step before Stage-2 query generation.
    Modality classification MUST be:
    - Rule-based (no ML/AI)
    - Deterministic (same input → same output)
    - Explainable (clear reasoning)
    - Independent of search results
    
    CLASSIFICATION RULES:
    
    1. SOFTWARE (high automation, digital output):
       - automation_level contains: "high", "AI", "automated", "AI-powered"
       - AND no service-specific keywords in core_action
    
    2. SERVICE (low automation, human-delivered):
       - automation_level contains: "low", "manual", "human"
       - OR core_action contains: "repair", "maintenance", "onsite", "doorstep", 
         "service", "install", "cleaning", "consulting", "training"
    
    3. PHYSICAL_PRODUCT (tangible output):
       - output_type contains: "product", "device", "hardware", "equipment",
         "machine", "gadget", "tool" (physical tool, not software)
    
    4. HYBRID (both software and service components):
       - Has characteristics of both SOFTWARE and SERVICE
       - E.g., "AI-powered consulting" or "automated repair scheduling"
    
    BIAS RULE: When uncertain, choose the LESS automated modality.
    Precedence: SERVICE > PHYSICAL_PRODUCT > HYBRID > SOFTWARE
    
    NLP INTEGRATION:
    - NLP assists with extracting normalized keywords (handles morphological variants)
    - NLP provides hints (e.g., "repair" → service-related)
    - Rules make ALL final classification decisions
    
    Args:
        solution: UserSolution with structured attributes
        
    Returns:
        str: "SOFTWARE", "SERVICE", "PHYSICAL_PRODUCT", or "HYBRID"
    """
    # Normalize attributes for matching
    automation_level = solution.automation_level.lower().strip()
    core_action = solution.core_action.lower().strip()
    output_type = solution.output_type.lower().strip()
    
    # === NLP ASSISTANCE (OPTIONAL) ===
    # NLP helps extract normalized keywords and hints
    # Rules still make all decisions
    try:
        action_cues = nlp_extract_solution_cues(core_action)
        output_cues = nlp_extract_solution_cues(output_type)
        automation_cues = nlp_extract_solution_cues(automation_level)
        
        logger.debug(f"NLP cues - action: {action_cues['hints']}, "
                    f"output: {output_cues['hints']}, "
                    f"automation: {automation_cues['hints']}")
        nlp_available = True
    except Exception as e:
        logger.debug(f"NLP cue extraction failed, using simple matching: {e}")
        action_cues = {'stems': [], 'hints': []}
        output_cues = {'stems': [], 'hints': []}
        automation_cues = {'stems': [], 'hints': []}
        nlp_available = False
    
    # === NLP BOUNDARY — RULES DECIDE FROM HERE ===
    
    def contains_keyword(text, keywords, nlp_stems=None):
        """
        Check if text contains any keyword using word boundary matching.
        Enhanced with NLP stem matching when available.
        
        NLP helps catch morphological variants (repair/repairing/repaired)
        but rules still make the final decision.
        """
        text_lower = text.lower()
        words = text_lower.split()
        
        # Rule-based matching (always executed)
        for keyword in keywords:
            # For multi-word keywords (e.g., "machine learning")
            if ' ' in keyword:
                if keyword in text_lower:
                    return True
            # For hyphenated keywords (e.g., "ai-powered")
            elif '-' in keyword:
                if keyword in text_lower:
                    return True
            # For single-word keywords, check exact word match
            else:
                if keyword in words:
                    return True
        
        # NLP-enhanced matching (if available) - catches morphological variants
        if nlp_stems:
            from nlp_utils import stem_word
            for keyword in keywords:
                keyword_stem = stem_word(keyword)
                if keyword_stem in nlp_stems:
                    logger.debug(f"NLP matched variant: {keyword} (stem: {keyword_stem})")
                    return True
        
        return False
    
    # Define keyword sets for classification
    # SERVICE indicators (highest priority - bias toward non-software)
    service_keywords = {
        'repair', 'maintenance', 'onsite', 'doorstep', 'service',
        'install', 'installation', 'cleaning', 'consulting', 'training',
        'coaching', 'therapy', 'treatment', 'care', 'support',
        'handyman', 'technician', 'specialist'
        # Note: 'manual' is in low_automation_keywords, not here
    }
    
    # PHYSICAL_PRODUCT indicators
    physical_output_keywords = {
        'product', 'device', 'hardware', 'equipment', 'machine',
        'gadget', 'appliance', 'furniture', 'clothing', 'food',
        'material', 'component', 'part'
    }
    
    # SOFTWARE indicators (lowest priority - only when clearly software)
    high_automation_keywords = {
        'high', 'ai', 'automated', 'ai-powered', 'automatic',
        'machine learning', 'ml', 'algorithm', 'intelligent'
    }
    
    # LOW automation indicators (supports SERVICE)
    low_automation_keywords = {
        'low', 'manual', 'human', 'person', 'handmade',
        'custom', 'bespoke', 'artisan'
    }
    
    # Check for SERVICE indicators FIRST (highest priority per bias rule)
    # Service actions take precedence over physical outputs
    # NLP helps catch variants like "repairing" → "repair"
    has_service_action = contains_keyword(
        core_action, service_keywords, 
        action_cues['stems'] if nlp_available else None
    )
    has_low_automation = contains_keyword(
        automation_level, low_automation_keywords,
        automation_cues['stems'] if nlp_available else None
    )
    
    if has_service_action:
        # Service action detected - check if also has high automation (HYBRID vs pure SERVICE)
        has_high_automation = contains_keyword(
            automation_level, high_automation_keywords,
            automation_cues['stems'] if nlp_available else None
        )
        
        if has_high_automation:
            # HYBRID: Service with automation components
            logger.info(
                f"Classified as HYBRID: Service action '{core_action}' "
                f"with automation '{automation_level}'"
            )
            return "HYBRID"
        else:
            # Pure SERVICE
            logger.info(
                f"Classified as SERVICE: Service action detected "
                f"(action='{core_action}')"
            )
            return "SERVICE"
    
    # Check for PHYSICAL_PRODUCT indicators (before low automation check)
    # Physical products take precedence over generic low automation
    has_physical_output = contains_keyword(
        output_type, physical_output_keywords,
        output_cues['stems'] if nlp_available else None
    )
    
    if has_physical_output:
        # Check if also has software/service components
        has_high_automation = contains_keyword(
            automation_level, high_automation_keywords,
            automation_cues['stems'] if nlp_available else None
        )
        
        if has_high_automation:
            # HYBRID: Physical product with software/service
            logger.info(
                f"Classified as HYBRID: Physical output '{output_type}' "
                f"with automation components"
            )
            return "HYBRID"
        else:
            # Pure PHYSICAL_PRODUCT
            logger.info(
                f"Classified as PHYSICAL_PRODUCT: Tangible output "
                f"(output='{output_type}')"
            )
            return "PHYSICAL_PRODUCT"
    
    # Check for low automation (without service action keywords)
    if has_low_automation:
        # Low automation without service action - still SERVICE by bias rule
        logger.info(
            f"Classified as SERVICE: Low automation "
            f"(automation='{automation_level}')"
        )
        return "SERVICE"
    
    # Check for clear SOFTWARE indicators
    has_high_automation = contains_keyword(
        automation_level, high_automation_keywords,
        automation_cues['stems'] if nlp_available else None
    )
    
    if has_high_automation:
        # SOFTWARE: High automation, no service/physical indicators
        logger.info(
            f"Classified as SOFTWARE: High automation "
            f"(automation='{automation_level}')"
        )
        return "SOFTWARE"
    
    # UNCERTAIN CASE: Apply bias toward less automated modality
    # Default to SERVICE (most conservative, least software-biased)
    logger.info(
        f"Uncertain modality - defaulting to SERVICE (bias toward non-software). "
        f"action='{core_action}', automation='{automation_level}', output='{output_type}'"
    )
    return "SERVICE"


def generate_solution_class_queries(solution: UserSolution, modality: str):
    """
    Generate deterministic, modality-aware search queries.
    
    This is STAGE 2 ONLY - generates queries specific to the user's solution,
    not the problem space.
    
    CRITICAL: Query terms MUST match solution_modality.
    SOFTWARE-specific terms (tool, software, platform, SaaS, AI, automation)
    MUST NEVER be used for SERVICE or PHYSICAL_PRODUCT modalities.
    
    ISSUE 3 FIX: Normalize core_action to verb form for query generation.
    This improves semantic precision and reduces false positives from content.
    
    RULES:
    - Queries are rule-generated and deterministic
    - Use static templates based on solution attributes AND modality
    - No free-text input, only structured attributes
    - No LLM rewriting or semantic expansion
    
    MODALITY-SPECIFIC QUERY TEMPLATES:
    
    SOFTWARE:
    - "{core_action} software"
    - "{core_action} tool"
    - "{core_action} platform"
    - "{automation_level} {core_action} SaaS"
    
    SERVICE:
    - "{core_action} service"
    - "{core_action} provider"
    - "{core_action} company"
    - "local {core_action} business"
    
    PHYSICAL_PRODUCT:
    - "{output_type} manufacturer"
    - "{output_type} supplier"
    - "{core_action} product"
    - "{output_type} brand"
    
    HYBRID:
    - "{core_action} service"
    - "{core_action} platform"
    - "{core_action} provider"
    
    Args:
        solution: UserSolution with structured attributes
        modality: "SOFTWARE", "SERVICE", "PHYSICAL_PRODUCT", or "HYBRID"
        
    Returns:
        List of search query strings (3-5 queries)
    """
    # ISSUE 3 FIX: Normalize core_action to verb form for internal query logic
    # User input is NOT modified - this is for query generation only
    normalized_core_action = normalize_core_action_to_verb(solution.core_action)
    
    # Extract and normalize other attributes
    core_action = normalized_core_action.lower().strip()
    output_type = solution.output_type.lower().strip()
    target_user = solution.target_user.lower().strip()
    automation_level = solution.automation_level.lower().strip()
    
    # Generate queries based on modality
    # HARD RULE: SOFTWARE terms MUST NOT appear in SERVICE/PHYSICAL_PRODUCT queries
    
    if modality == "SOFTWARE":
        # SOFTWARE modality: Use software-specific terms
        queries = [
            f"{core_action} software",
            f"{core_action} tool",
            f"{core_action} platform",
            f"{automation_level} {core_action} SaaS",
            f"{core_action} AI tool",
        ]
        logger.info(f"Generated SOFTWARE modality queries for '{core_action}'")
    
    elif modality == "SERVICE":
        # SERVICE modality: Use service-specific terms
        # NO software/tool/platform/SaaS terms allowed
        queries = [
            f"{core_action} service",
            f"{core_action} provider",
            f"{core_action} company",
            f"local {core_action} business",
            f"{core_action} near me",
        ]
        logger.info(f"Generated SERVICE modality queries for '{core_action}'")
    
    elif modality == "PHYSICAL_PRODUCT":
        # PHYSICAL_PRODUCT modality: Use product-specific terms
        # NO software/tool/platform/SaaS terms allowed
        queries = [
            f"{output_type} manufacturer",
            f"{output_type} supplier",
            f"{core_action} product",
            f"{output_type} brand",
            f"{output_type} wholesale",
        ]
        logger.info(f"Generated PHYSICAL_PRODUCT modality queries for '{output_type}'")
    
    elif modality == "HYBRID":
        # HYBRID modality: Mix SERVICE and SOFTWARE terms carefully
        queries = [
            f"{core_action} service",
            f"{core_action} platform",
            f"{core_action} provider",
            f"{automation_level} {core_action} service",
        ]
        logger.info(f"Generated HYBRID modality queries for '{core_action}'")
    
    else:
        # Fallback (should never happen if classify_solution_modality is correct)
        logger.warning(f"Unknown modality '{modality}', defaulting to SERVICE queries")
        queries = [
            f"{core_action} service",
            f"{core_action} provider",
            f"{core_action} company",
        ]
    
    # Deduplicate queries (case-insensitive)
    seen = set()
    unique_queries = []
    for query in queries:
        normalized = query.lower().strip()
        if normalized not in seen and len(normalized) > 5:  # Minimum length check
            seen.add(normalized)
            unique_queries.append(query)
    
    logger.info(f"Generated {len(unique_queries)} {modality} modality queries")
    logger.debug(f"Queries: {unique_queries}")
    
    return unique_queries


def extract_pricing_model(result):
    """
    Extract pricing model from search result.
    
    Deterministic keyword-based extraction (no AI).
    
    Args:
        result: Search result dict with 'title' and 'snippet'
        
    Returns:
        'free', 'freemium', 'paid', or 'unknown'
    """
    text = (
        (result.get("title") or "") + " " +
        (result.get("snippet") or "")
    ).lower()
    
    # Check for free indicators
    free_keywords = ['free forever', 'completely free', 'totally free', 'free plan', 'free tier']
    if any(kw in text for kw in free_keywords):
        return 'free'
    
    # Check for freemium indicators (free + paid tiers)
    freemium_keywords = ['free trial', 'freemium', 'free and paid', 'upgrade to', 'premium plan']
    if any(kw in text for kw in freemium_keywords):
        return 'freemium'
    
    # Check for paid indicators
    paid_keywords = ['pricing', 'subscription', 'price', '$', 'per month', 'per user']
    if any(kw in text for kw in paid_keywords):
        return 'paid'
    
    return 'unknown'


# ============================================================================
# STAGE 2: MARKET STRENGTH PARAMETERS
# ============================================================================
# These functions compute structured market strength parameters for Stage 2.
# 
# CRITICAL RULES:
# - All functions are deterministic and rule-based (no LLM, no ML)
# - Parameters are INDEPENDENT (no aggregation, no scoring)
# - Each parameter answers ONE specific market question
# - Output is structured facts, NOT conclusions or advice
#
# These parameters are consumed by downstream logic and LLM reasoning,
# but Stage 2 itself does NOT reason about success or strategy.
# ============================================================================

def compute_competitor_density(commercial_count: int, modality: str) -> str:
    """
    Compute competitor density based on number of direct competitors found.
    
    This is a FACTUAL market signal, not a judgment about startup viability.
    
    RULES (deterministic thresholds):
    - SOFTWARE: NONE (0), LOW (1-3), MEDIUM (4-9), HIGH (10+)
    - SERVICE/PHYSICAL_PRODUCT: More tolerance for fragmented markets
      NONE (0), LOW (1-5), MEDIUM (6-15), HIGH (16+)
    - HYBRID: Use SOFTWARE thresholds (stricter)
    
    Args:
        commercial_count: Number of commercial competitors found
        modality: Solution modality (SOFTWARE, SERVICE, PHYSICAL_PRODUCT, HYBRID)
        
    Returns:
        "NONE", "LOW", "MEDIUM", or "HIGH"
    """
    # Adjust thresholds based on modality
    if modality in ["SERVICE", "PHYSICAL_PRODUCT"]:
        # Service/physical markets are often fragmented with many local providers
        # Higher tolerance before considering density "high"
        if commercial_count == 0:
            return "NONE"
        elif commercial_count <= 5:
            return "LOW"
        elif commercial_count <= 15:
            return "MEDIUM"
        else:
            return "HIGH"
    else:
        # SOFTWARE and HYBRID: stricter thresholds (software markets consolidate faster)
        if commercial_count == 0:
            return "NONE"
        elif commercial_count <= 3:
            return "LOW"
        elif commercial_count <= 9:
            return "MEDIUM"
        else:
            return "HIGH"


def compute_market_fragmentation(
    commercial_products: list,
    modality: str
) -> str:
    """
    Compute market fragmentation based on competitor characteristics.
    
    Fragmented markets have many small, specialized competitors.
    Consolidated markets have few dominant players.
    
    ISSUE 4 FIX: Document density vs fragmentation invariant
    ========================================================
    HIGH competitor_density + CONSOLIDATED market_fragmentation CAN coexist.
    
    Interpretation:
    - HIGH density + CONSOLIDATED = Many competitors exist, but attention/revenue
      is dominated by a few major players (e.g., "CRM software" has 50+ tools
      but Salesforce/HubSpot dominate mindshare)
    
    - LOW density + FRAGMENTED = Few competitors found in search, but market
      is fragmented (e.g., local services with no online presence)
    
    - HIGH density + FRAGMENTED = Many competitors, no clear leaders
      (highly competitive, no dominant players)
    
    This relationship is valid and explicitly handled below.
    ========================================================
    
    RULES (deterministic heuristics):
    1. Count local/small business indicators vs enterprise indicators
    2. SERVICE/PHYSICAL_PRODUCT: Bias toward FRAGMENTED (local businesses)
    3. SOFTWARE: Look for consolidation signals (enterprise, platform, market leader)
    
    Args:
        commercial_products: List of competitor dicts with 'snippet' and 'name'
        modality: Solution modality
        
    Returns:
        "CONSOLIDATED", "FRAGMENTED", or "MIXED"
    """
    if not commercial_products:
        # No competitors found - cannot determine fragmentation
        return "MIXED"
    
    # Count fragmentation vs consolidation signals
    local_indicators = ['local', 'near me', 'small business', 'independent', 'boutique']
    enterprise_indicators = ['enterprise', 'platform', 'market leader', 'industry standard', 'fortune']
    
    local_count = 0
    enterprise_count = 0
    
    for product in commercial_products:
        text = (
            (product.get('name') or '') + ' ' +
            (product.get('snippet') or '')
        ).lower()
        
        if any(indicator in text for indicator in local_indicators):
            local_count += 1
        
        if any(indicator in text for indicator in enterprise_indicators):
            enterprise_count += 1
    
    # Modality-specific biases
    if modality in ["SERVICE", "PHYSICAL_PRODUCT"]:
        # SERVICE/PHYSICAL_PRODUCT markets are typically fragmented (local businesses)
        # Bias toward FRAGMENTED unless strong consolidation signals
        if enterprise_count > len(commercial_products) * 0.5:
            return "CONSOLIDATED"
        elif local_count > 0 or len(commercial_products) > 10:
            return "FRAGMENTED"
        else:
            return "MIXED"
    else:
        # SOFTWARE/HYBRID: More likely to consolidate
        if enterprise_count > local_count * 2:
            return "CONSOLIDATED"
        elif local_count > enterprise_count * 2:
            return "FRAGMENTED"
        else:
            return "MIXED"


def compute_substitute_pressure(
    diy_results: list,
    modality: str,
    automation_level: str
) -> str:
    """
    Compute substitute pressure from DIY solutions, manual processes, and human services.
    
    FACTUAL SIGNAL: How many non-commercial alternatives exist?
    - DIY tutorials, scripts, manual processes
    - Human services (for SOFTWARE solutions)
    - Manual/offline alternatives (for SERVICE solutions)
    
    RULES (deterministic thresholds):
    - Count DIY/workaround results
    - Adjust thresholds based on modality and automation level
    - HIGH automation means more sensitive to substitutes
    
    Args:
        diy_results: List of DIY/tutorial search results
        modality: Solution modality
        automation_level: Automation level from user solution
        
    Returns:
        "LOW", "MEDIUM", or "HIGH"
    """
    diy_count = len(diy_results)
    
    # Adjust thresholds based on automation level
    # High automation solutions are more vulnerable to manual/DIY substitutes
    if 'high' in automation_level.lower() or 'ai' in automation_level.lower():
        # Stricter thresholds for high automation (easier to substitute)
        if diy_count <= 3:
            return "LOW"
        elif diy_count <= 8:
            return "MEDIUM"
        else:
            return "HIGH"
    else:
        # Standard thresholds for low/medium automation
        if diy_count <= 6:
            return "LOW"
        elif diy_count <= 15:
            return "MEDIUM"
        else:
            return "HIGH"


def compute_content_saturation_for_solution(
    content_results: list,
    modality: str
) -> str:
    """
    Compute content saturation relative to THIS SOLUTION (not the problem).
    
    CRITICAL: This is solution-specific content saturation.
    - For SOFTWARE: blogs/articles about THIS type of solution
    - For SERVICE: educational content about THIS service type
    - NOT general problem-space content
    
    RULES (deterministic thresholds):
    - Count content results (blogs, guides, tutorials)
    - More content = more established solution category
    - Thresholds vary by modality
    
    Args:
        content_results: List of blog/guide search results
        modality: Solution modality
        
    Returns:
        "LOW", "MEDIUM", or "HIGH"
    """
    content_count = len(content_results)
    
    # Thresholds (modality-agnostic for simplicity)
    if content_count <= 5:
        return "LOW"
    elif content_count <= 15:
        return "MEDIUM"
    else:
        return "HIGH"


def compute_solution_class_maturity(
    commercial_products: list,
    content_results: list,
    modality: str
) -> str:
    """
    Compute solution-class maturity relative to THIS SOLUTION.
    
    FACTUAL SIGNAL: Does a recognized product category exist for this solution type?
    
    RULES (deterministic heuristics):
    1. NON_EXISTENT: No commercial products AND no content
    2. EMERGING: Few commercial products OR limited content
    3. ESTABLISHED: Many commercial products AND substantial content
    
    This is INDEPENDENT of problem severity or startup viability.
    
    Args:
        commercial_products: List of commercial competitor dicts
        content_results: List of content search results
        modality: Solution modality
        
    Returns:
        "NON_EXISTENT", "EMERGING", or "ESTABLISHED"
    """
    commercial_count = len(commercial_products)
    content_count = len(content_results)
    
    # Rule 1: No products AND no content = NON_EXISTENT
    if commercial_count == 0 and content_count <= 2:
        return "NON_EXISTENT"
    
    # Rule 2: ESTABLISHED requires both products AND content
    # Thresholds adjusted for modality
    if modality in ["SERVICE", "PHYSICAL_PRODUCT"]:
        # Service/physical markets establish differently (more fragmented)
        if commercial_count >= 10 and content_count >= 10:
            return "ESTABLISHED"
        elif commercial_count > 0 or content_count > 2:
            return "EMERGING"
        else:
            return "NON_EXISTENT"
    else:
        # SOFTWARE/HYBRID: stricter requirements for ESTABLISHED
        if commercial_count >= 5 and content_count >= 8:
            return "ESTABLISHED"
        elif commercial_count > 0 or content_count > 2:
            return "EMERGING"
        else:
            return "NON_EXISTENT"


def compute_automation_relevance(
    automation_level: str,
    modality: str
) -> str:
    """
    Compute automation relevance based on solution attributes.
    
    FACTUAL SIGNAL: How much does automation matter for this solution?
    - HIGH automation solutions compete on efficiency/speed
    - LOW automation solutions compete on quality/human touch
    
    RULES (deterministic mapping):
    - Check automation_level keywords
    - Adjust for modality (SERVICE/PHYSICAL_PRODUCT = lower relevance)
    
    Args:
        automation_level: Automation level from user solution
        modality: Solution modality
        
    Returns:
        "LOW", "MEDIUM", or "HIGH"
    """
    automation_lower = automation_level.lower().strip()
    
    # High automation keywords
    high_automation_keywords = ['high', 'ai', 'automated', 'ai-powered', 'automatic', 'machine learning']
    
    # Low automation keywords
    low_automation_keywords = ['low', 'manual', 'human', 'person', 'handmade']
    
    # Check for automation level keywords
    has_high_automation = any(kw in automation_lower for kw in high_automation_keywords)
    has_low_automation = any(kw in automation_lower for kw in low_automation_keywords)
    
    # Modality adjustment: SERVICE/PHYSICAL_PRODUCT have lower automation relevance by default
    if modality in ["SERVICE", "PHYSICAL_PRODUCT"]:
        if has_high_automation:
            # Even high automation matters less for service/physical
            return "MEDIUM"
        else:
            # Manual service/physical products
            return "LOW"
    else:
        # SOFTWARE/HYBRID: automation is more relevant
        if has_high_automation:
            return "HIGH"
        elif has_low_automation:
            return "LOW"
        else:
            # Medium automation or unclear
            return "MEDIUM"


def analyze_user_solution_competitors(solution: UserSolution):
    """
    STAGE 2: Detect competitors and compute market strength parameters for user's solution.
    
    This is STAGE 2 ONLY - analyzes the market for THIS SPECIFIC SOLUTION.
    Completely separated from Stage 1 (problem analysis).
    
    UPDATED PROCESS (with market strength parameters):
    1. Classify solution modality (SOFTWARE, SERVICE, PHYSICAL_PRODUCT, HYBRID)
    2. Generate modality-aware queries for competitors, DIY alternatives, and content
    3. Run searches and classify results
    4. Compute STRUCTURED market strength parameters (NO aggregation, NO scoring)
    5. Return formatted output with semantic corrections
    
    CRITICAL OUTPUT SEMANTICS:
    - For SOFTWARE modality: "competitors" = software competitors
    - For SERVICE/PHYSICAL_PRODUCT: "competitors.software" = software competitors
      (but services_expected = true indicates human/local/offline competition exists)
    
    MARKET STRENGTH PARAMETERS (all independent, no aggregation):
    - competitor_density: NONE, LOW, MEDIUM, HIGH
    - market_fragmentation: CONSOLIDATED, FRAGMENTED, MIXED
    - substitute_pressure: LOW, MEDIUM, HIGH (DIY, manual, human services)
    - content_saturation: LOW, MEDIUM, HIGH (relative to THIS solution)
    - solution_class_maturity: NON_EXISTENT, EMERGING, ESTABLISHED
    - automation_relevance: LOW, MEDIUM, HIGH
    
    CONSTRAINTS:
    - No ranking or scoring
    - No comparison to user's product
    - No LLM reasoning
    - No strategic advice or success prediction
    - Output is STRUCTURED FACTS only
    
    Args:
        solution: UserSolution with structured attributes
        
    Returns:
        Dict with solution_modality, market_strength parameters, and competitors
    """
    # ========================================================================
    # STEP 1: Classify solution modality
    # ========================================================================
    modality = classify_solution_modality(solution)
    logger.info(f"Stage 2: Solution modality classified as {modality}")
    
    # ========================================================================
    # STEP 2: Generate solution-specific queries
    # ========================================================================
    # Generate queries for competitors (commercial products)
    competitor_queries = generate_solution_class_queries(solution, modality)
    
    # Generate queries for DIY alternatives/workarounds
    # Use core_action to find DIY solutions for THIS solution
    core_action = solution.core_action.lower().strip()
    diy_queries = [
        f"how to {core_action} DIY",
        f"{core_action} tutorial",
        f"{core_action} open source",
        f"{core_action} script",
    ]
    
    # Generate queries for content (blogs, guides about THIS solution type)
    content_queries = [
        f"{core_action} guide",
        f"{core_action} blog",
        f"{core_action} best practices",
    ]
    
    # ========================================================================
    # STEP 3: Run searches
    # ========================================================================
    competitor_results = run_multiple_searches(competitor_queries)
    competitor_results = deduplicate_results(competitor_results)
    
    diy_results = run_multiple_searches(diy_queries)
    diy_results = deduplicate_results(diy_results)
    
    content_results = run_multiple_searches(content_queries)
    content_results = deduplicate_results(content_results)
    
    # ========================================================================
    # STEP 4: Classify results (using Stage 1 classifier)
    # ========================================================================
    commercial_products = []
    diy_alternatives = []
    
    # Classify competitor results
    for result in competitor_results:
        result_type = classify_result_type(result)
        
        if result_type == 'commercial':
            # Commercial product - add to competitors
            product_info = {
                'name': result.get('title', 'Unknown Product'),
                'url': result.get('url', ''),
                'pricing_model': extract_pricing_model(result),
                'snippet': result.get('snippet', ''),
            }
            commercial_products.append(product_info)
            logger.debug(f"Found commercial competitor: {product_info['name']}")
        elif result_type == 'diy':
            # DIY result in competitor queries - move to DIY alternatives
            diy_alternatives.append(result)
        # Exclude content, unknown
    
    # Classify DIY results
    for result in diy_results:
        result_type = classify_result_type(result)
        
        if result_type == 'diy':
            diy_alternatives.append(result)
        elif result_type == 'commercial':
            # Commercial product in DIY queries - move to competitors
            product_info = {
                'name': result.get('title', 'Unknown Product'),
                'url': result.get('url', ''),
                'pricing_model': extract_pricing_model(result),
                'snippet': result.get('snippet', ''),
            }
            commercial_products.append(product_info)
        # Exclude content, unknown
    
    # Deduplicate after reclassification
    diy_alternatives = deduplicate_results(diy_alternatives)
    
    # ========================================================================
    # ISSUE 1 FIX: Deduplicate competitors by canonical domain
    # ========================================================================
    # This MUST happen BEFORE computing market strength parameters
    # to prevent inflated competitor_density and incorrect market_fragmentation
    commercial_products = deduplicate_competitors_by_domain(commercial_products)
    
    # ========================================================================
    # STEP 5: Compute market strength parameters
    # ========================================================================
    # Each parameter is computed independently (no aggregation, no scoring)
    # ISSUE 1 FIX: competitor_density now reflects UNIQUE competitors only
    
    competitor_density = compute_competitor_density(
        len(commercial_products),
        modality
    )
    
    market_fragmentation = compute_market_fragmentation(
        commercial_products,
        modality
    )
    
    substitute_pressure = compute_substitute_pressure(
        diy_alternatives,
        modality,
        solution.automation_level
    )
    
    content_saturation = compute_content_saturation_for_solution(
        content_results,
        modality
    )
    
    solution_class_maturity = compute_solution_class_maturity(
        commercial_products,
        content_results,
        modality
    )
    
    automation_relevance = compute_automation_relevance(
        solution.automation_level,
        modality
    )
    
    logger.info(
        f"Stage 2 market strength: "
        f"density={competitor_density}, fragmentation={market_fragmentation}, "
        f"substitutes={substitute_pressure}, content={content_saturation}, "
        f"maturity={solution_class_maturity}, automation={automation_relevance}"
    )
    
    # ========================================================================
    # STEP 6: Format output with semantic corrections
    # ========================================================================
    # SEMANTIC CORRECTION for non-software solutions:
    # "no competitors found" means "no SOFTWARE competitors found"
    # NOT "no competition exists" (human/local/offline competition may exist)
    
    services_expected = modality in ["SERVICE", "PHYSICAL_PRODUCT"]
    
    if services_expected and len(commercial_products) == 0:
        logger.info(
            f"Modality is {modality}: No SOFTWARE competitors found, "
            f"but human/local/offline competition likely exists"
        )
    
    # Build competitor list (software competitors only)
    software_competitors = [
        {
            'name': p['name'],
            'url': p['url'],
            'pricing_model': p['pricing_model']
        }
        for p in commercial_products[:10]  # Limit to top 10
    ]
    
    # ========================================================================
    # RETURN: Structured output matching requirement specification
    # ========================================================================
    return {
        "solution_modality": modality,
        "market_strength": {
            "competitor_density": competitor_density,
            "market_fragmentation": market_fragmentation,
            "substitute_pressure": substitute_pressure,
            "content_saturation": content_saturation,
            "solution_class_maturity": solution_class_maturity,
            "automation_relevance": automation_relevance,
        },
        "competitors": {
            "software": software_competitors,
            "services_expected": services_expected,
        }
    }



@app.post("/analyze-user-solution")
def analyze_user_solution(solution: UserSolution):
    """
    Stage 2 endpoint: Analyze competitors for user's specific solution.
    
    This is STAGE 2 - detects competitors offering similar solutions.
    Strictly separated from Stage 1 (problem analysis).
    
    Args:
        solution: UserSolution with structured attributes
        
    Returns:
        Dict with user_solution_competitors analysis
    """
    competitors = analyze_user_solution_competitors(solution)
    
    return {
        'user_solution_competitors': competitors
    }
