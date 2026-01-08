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
    
    # Social media platforms (LinkedIn, Facebook)
    # BLOCKING BUG FIX: These sites host discussions/posts about products, not first-party products
    'linkedin.com', 'facebook.com',
    
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

# ============================================================================
# LEGACY CONSTANTS (kept for backwards compatibility, not used by new logic)
# ============================================================================
# These constants were used by the old keyword-based classification logic.
# The new principled reasoning approach (classify_result_type) defines its own
# patterns inline with better organization by signal category.

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
# BLOCKING BUG FIX: Added newsletter, guide variations to prevent misclassification
# NOTE: Compound phrases (e.g., 'weekly newsletter') are intentional and necessary
# because pattern matching looks for exact substring matches in text
CONTENT_KEYWORDS = {
    'review', 'comparison', 'vs', 'versus', 'best', 'top',
    'guide', 'blog', 'article', 'post', 'discussion', 'forum',
    'thread', 'comment', 'opinion', 'thoughts on', 'what do you think',
    'listicle', 'roundup', 'collection',
    # Newsletter-specific keywords
    'newsletter', 'subscribe', 'weekly newsletter', 'monthly newsletter',
    # Guide variations
    'buyer\'s guide', 'buyers guide', 'ultimate guide', 'complete guide',
    'how-to guide', 'beginner\'s guide', 'beginners guide'
}

# ============================================================================
# CLASSIFICATION THRESHOLDS (new principled reasoning approach)
# ============================================================================
# Minimum number of signals required for DIY classification
# If DIY patterns are found but we also have this many product signals,
# it's likely a commercial product page, not a tutorial
MIN_SIGNALS_FOR_DIY_OVERRIDE = 2


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


def classify_result_type(result):
    """
    Classify search result as commercial, diy, content, or unknown.
    
    REDESIGNED WITH PRINCIPLED REASONING (no keyword frequency alone):
    
    PHILOSOPHY: 
    - Accuracy > speed: Take time to properly analyze
    - Under-counting > over-counting: When uncertain, classify as non-commercial
    - Multi-step reasoning: Prove each classification step-by-step
    - Structural signals > textual signals: Look for page structure patterns
    
    CLASSIFICATION APPROACH:
    
    STEP 1: PROVE page is informational (eliminates false positives)
       → Check domain: Is it Reddit, Medium, LinkedIn, etc?
       → Check content patterns: Review, comparison, guide, newsletter?
       → If YES to either → CONTENT (never commercial)
    
    STEP 2: PROVE page is first-party product (requires multiple signals)
       → Structural signals: Navigation patterns, pricing page indicators
       → Product offering: Direct signup/trial CTAs, pricing tiers
       → Business indicators: Legal footer, enterprise features
       → Requires MULTIPLE signals from different categories
    
    STEP 3: Verify DIRECT offering (not just mention)
       → Must be offering the solution ON THIS PAGE
       → Not just discussing or linking to other solutions
    
    STEP 4: Fallback for uncertainty
       → If we cannot confidently prove commercial → default to non-commercial
       → Bias toward false negatives to avoid over-counting
    
    Args:
        result: Search result dict with 'title', 'snippet', and optionally 'url'
        
    Returns:
        'commercial', 'diy', 'content', or 'unknown'
    """
    url = result.get('url', '')
    title = (result.get("title") or "").lower()
    snippet = (result.get("snippet") or "").lower()
    text = title + " " + snippet
    
    # ========================================================================
    # STEP 1: PROVE this is INFORMATIONAL content (highest priority)
    # ========================================================================
    # Reasoning: Content sites discuss/review products but never offer them directly
    # If domain matches known content sites → CANNOT be commercial
    
    if is_content_site(url):
        logger.debug(f"STEP 1 RESULT: CONTENT (known content site domain)")
        logger.debug(f"  → URL: {url}")
        logger.debug(f"  → Reasoning: Content sites discuss products but don't sell them")
        return 'content'
    
    # Check for strong informational patterns that prove this is content
    # These patterns indicate the page is TALKING ABOUT products, not SELLING one
    informational_patterns = {
        # Comparison/review patterns - discussing multiple products
        'comparison': ['vs', 'versus', 'comparison', 'compare'],
        'review': ['review', 'reviews', 'reviewed'],
        
        # List/roundup patterns - aggregating multiple solutions
        'list': ['best tool', 'best software', 'best app', 'best product', 
                 'top tool', 'top software', 'top app', 'top product',
                 'best crm', 'best platform', 'best solution', 'best service'],
        'roundup': ['roundup', 'listicle', 'alternatives to', 'list of'],
        
        # Educational content patterns - teaching, not selling
        'guide': ['ultimate guide', 'complete guide', 'buyer\'s guide', 'buyers guide',
                  'beginner\'s guide', 'beginners guide', 'how-to guide', 'step-by-step guide'],
        
        # Newsletter/publication patterns - curated content
        'newsletter': ['newsletter', 'weekly newsletter', 'monthly newsletter', 
                       'subscribe to newsletter', 'subscribe to our newsletter'],
        
        # Blog/article patterns - editorial content
        'blog': ['blog post', 'article about', 'read more', 'written by', 'posted by'],
    }
    
    # Track which patterns matched for better debugging
    matched_patterns = []
    for category, patterns in informational_patterns.items():
        for pattern in patterns:
            if pattern in text:
                matched_patterns.append(f"{category}:{pattern}")
    
    if matched_patterns:
        logger.debug(f"STEP 1 RESULT: CONTENT (informational patterns detected)")
        logger.debug(f"  → URL: {url}")
        logger.debug(f"  → Matched patterns: {matched_patterns[:3]}")  # Show first 3
        logger.debug(f"  → Reasoning: Page is discussing/reviewing products, not selling one")
        return 'content'
    
    # ========================================================================
    # STEP 2: PROVE this is a FIRST-PARTY PRODUCT page (requires multiple signals)
    # ========================================================================
    # Reasoning: A commercial page must have structural evidence of being a product
    # We need MULTIPLE signals from DIFFERENT categories to be confident
    
    # NOTE: These patterns are defined inline (not using legacy global constants)
    # because the new approach organizes signals by CATEGORY and PURPOSE,
    # making the classification logic more transparent and maintainable.
    
    # Category 1: Structural/Navigation signals (strongest)
    # These prove the page is structured like a product site
    structural_signals = {
        'pricing_page': ['pricing', 'plans', 'subscription', 'choose your plan'],
        'signup_page': ['sign up', 'signup', 'create account', 'register now'],
        'product_access': ['dashboard', 'login', 'log in', 'access your account', 'get started'],
    }
    
    structural_matches = []
    for signal_type, patterns in structural_signals.items():
        for pattern in patterns:
            if pattern in text:
                structural_matches.append(signal_type)
                break  # Only count each signal type once
    
    # Category 2: Product offering signals (medium strength)
    # These prove the page is directly offering something
    offering_signals = {
        'trial': ['free trial', 'start free trial', 'try it free', '14-day trial', 'trial'],
        'demo': ['request demo', 'book demo', 'schedule demo'],
        'immediate_action': ['get started', 'start now', 'join now'],
        'purchase': ['purchase', 'buy now', 'buy', 'license'],
    }
    
    offering_matches = []
    for signal_type, patterns in offering_signals.items():
        for pattern in patterns:
            if pattern in text:
                offering_matches.append(signal_type)
                break
    
    # Category 3: Business/enterprise signals (weakest alone)
    # These support commercial classification but aren't sufficient alone
    business_signals = {
        'saas': ['saas', 'software as a service', 'platform'],
        'enterprise': ['enterprise', 'for teams', 'for businesses', 'for organizations'],
    }
    
    business_matches = []
    for signal_type, patterns in business_signals.items():
        for pattern in patterns:
            if pattern in text:
                business_matches.append(signal_type)
                break
    
    # Count total signals across all categories
    total_signals = len(structural_matches) + len(offering_matches) + len(business_matches)
    
    # Also check if signals span multiple categories (stronger evidence)
    categories_with_signals = 0
    if structural_matches:
        categories_with_signals += 1
    if offering_matches:
        categories_with_signals += 1
    if business_matches:
        categories_with_signals += 1
    
    logger.debug(f"STEP 2 ANALYSIS: Product signal detection")
    logger.debug(f"  → Structural signals: {structural_matches}")
    logger.debug(f"  → Offering signals: {offering_matches}")
    logger.debug(f"  → Business signals: {business_matches}")
    logger.debug(f"  → Total signals: {total_signals}, Categories: {categories_with_signals}")
    
    # ========================================================================
    # STEP 3: CHECK for DIY/Tutorial content
    # ========================================================================
    # Reasoning: DIY content teaches users to build their own solution
    # This is different from both commercial and content
    
    diy_patterns = [
        'how to build', 'how to create', 'diy', 'do it yourself',
        'open source', 'github', 'code snippet', 'build your own',
        'create your own', 'tutorial', 'step by step', 'homebrew'
    ]
    
    diy_matches = [p for p in diy_patterns if p in text]
    
    if diy_matches:
        # DIY content is not commercial unless it ALSO has strong product signals
        # If it's just tutorial content, classify as DIY
        if total_signals < MIN_SIGNALS_FOR_DIY_OVERRIDE:
            logger.debug(f"STEP 3 RESULT: DIY (tutorial/open source)")
            logger.debug(f"  → Matched DIY patterns: {diy_matches[:2]}")
            logger.debug(f"  → Reasoning: Teaching users to build, not selling a product")
            return 'diy'
    
    # ========================================================================
    # STEP 4: MAKE FINAL CLASSIFICATION DECISION
    # ========================================================================
    # Reasoning: Only classify as commercial if we have HIGH CONFIDENCE
    
    # COMMERCIAL requires strong evidence of being a first-party product:
    # OPTION 1: Multiple structural signals (2+) - proves page structure is product-focused
    # OPTION 2: Structural + offering signals - proves both structure AND direct offering
    # OPTION 3: Multiple signals (2+) across multiple categories - proves diverse evidence
    
    has_multiple_structural = len(structural_matches) >= 2
    has_strong_structural = len(structural_matches) >= 1
    has_offering = len(offering_matches) >= 1
    has_multiple_categories = categories_with_signals >= 2
    has_sufficient_signals = total_signals >= 2
    
    # STRONGEST evidence: Multiple structural signals (pricing + signup + dashboard)
    # This proves the page has first-party product infrastructure
    if has_multiple_structural:
        logger.debug(f"STEP 4 RESULT: COMMERCIAL (multiple structural signals)")
        logger.debug(f"  → URL: {url}")
        logger.debug(f"  → Structural signals: {structural_matches}")
        logger.debug(f"  → Reasoning: Multiple navigation/structure patterns prove first-party product")
        logger.debug(f"  → This is not a blog/review - it has pricing, signup, or dashboard access")
        return 'commercial'
    
    # STRONG evidence: Structural + offering signals combined
    # Page has both infrastructure AND direct call-to-action
    if has_strong_structural and has_offering:
        logger.debug(f"STEP 4 RESULT: COMMERCIAL (structural + offering signals)")
        logger.debug(f"  → URL: {url}")
        logger.debug(f"  → Reasoning: Page has both structural navigation AND direct offering")
        logger.debug(f"  → This proves it's a first-party product page")
        return 'commercial'
    
    # MODERATE evidence: Multiple signals across different categories
    # Diverse signals from different aspects prove first-party product
    if has_sufficient_signals and has_multiple_categories:
        logger.debug(f"STEP 4 RESULT: COMMERCIAL (multiple signals across categories)")
        logger.debug(f"  → URL: {url}")
        logger.debug(f"  → Signals: {total_signals} across {categories_with_signals} categories")
        logger.debug(f"  → Reasoning: Multiple independent signals prove first-party product")
        return 'commercial'
    
    # ========================================================================
    # FALLBACK: When uncertain, prefer false negatives
    # ========================================================================
    # Reasoning: Better to under-count commercial competitors than over-count
    # If we can't confidently prove it's commercial, default to safer classification
    
    # Weak signals suggest content/discussion rather than product
    weak_content_indicators = ['article', 'post', 'blog', 'discussion', 'thread', 'comment']
    has_weak_content = any(indicator in text for indicator in weak_content_indicators)
    
    if has_weak_content:
        logger.debug(f"FALLBACK RESULT: CONTENT (weak signals + content indicators)")
        logger.debug(f"  → Cannot confidently prove this is commercial")
        logger.debug(f"  → Defaulting to CONTENT to avoid false positives")
        return 'content'
    
    # If we have some signals but not enough for commercial, it's unclear
    if total_signals > 0:
        logger.debug(f"FALLBACK RESULT: UNKNOWN (insufficient signals for commercial)")
        logger.debug(f"  → Signals detected but not enough to prove commercial")
        logger.debug(f"  → Following under-counting principle")
        return 'unknown'
    
    # No signals at all
    logger.debug(f"FALLBACK RESULT: UNKNOWN (no classification signals detected)")
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


def analyze_competition(problem: str):
    """
    Analyze competition pressure for a problem.
    
    This implements ISSUE 2: Competition pressure computation.
    
    Returns:
        Dict with commercial and DIY competition metrics
    """
    queries = generate_search_queries(problem)
    
    # Run tool queries to find competitors
    tool_results = run_multiple_searches(queries["tool_queries"])
    tool_results = deduplicate_results(tool_results)
    
    # Run workaround queries to find DIY alternatives
    workaround_results = run_multiple_searches(queries["workaround_queries"])
    workaround_results = deduplicate_results(workaround_results)
    
    # Separate commercial vs DIY (fixes ISSUE 1: bucket mixing)
    tool_results, workaround_results = separate_tool_workaround_results(
        tool_results, workaround_results
    )
    
    commercial_count = len(tool_results)
    diy_count = len(workaround_results)
    
    # Compute pressure levels (ISSUE 4: deterministic thresholds)
    commercial_pressure = compute_competition_pressure(
        commercial_count, 
        competition_type='commercial'
    )
    diy_pressure = compute_competition_pressure(
        diy_count, 
        competition_type='diy'
    )
    
    # Overall pressure: worst of commercial or DIY
    if commercial_pressure == "HIGH" or diy_pressure == "HIGH":
        overall_pressure = "HIGH"
    elif commercial_pressure == "MEDIUM" or diy_pressure == "MEDIUM":
        overall_pressure = "MEDIUM"
    else:
        overall_pressure = "LOW"
    
    # Detect solution-class existence (product category maturity signal)
    solution_class = detect_solution_class_existence(tool_results)
    
    return {
        "commercial_competitors": {
            "count": commercial_count,
            "pressure": commercial_pressure,
            "top_5": [
                {'title': r.get('title'), 'url': r.get('url')}
                for r in tool_results[:5]
            ]
        },
        "diy_alternatives": {
            "count": diy_count,
            "pressure": diy_pressure,
            "top_5": [
                {'title': r.get('title'), 'url': r.get('url')}
                for r in workaround_results[:5]
            ]
        },
        "overall_pressure": overall_pressure,
        "solution_class_exists": solution_class,
        "queries_used": {
            "tool_queries": queries["tool_queries"],
            "workaround_queries": queries["workaround_queries"]
        }
    }


def analyze_content_saturation(problem: str):
    """
    Analyze content saturation for a problem.
    
    This implements ISSUE 2: Content saturation computation.
    
    Returns:
        Dict with content saturation metrics
    """
    queries = generate_search_queries(problem)
    
    # Run blog queries to find educational content
    blog_results = run_multiple_searches(queries["blog_queries"])
    blog_results = deduplicate_results(blog_results)
    
    content_count = len(blog_results)
    
    # Deterministic thresholds for saturation level
    if content_count >= 15:
        saturation_level = "HIGH"
    elif content_count >= 6:
        saturation_level = "MEDIUM"
    else:
        saturation_level = "LOW"
    
    # Classify as NEGATIVE or NEUTRAL (ISSUE 3: interpretation rules)
    saturation_signal = classify_saturation_signal(content_count, blog_results)
    
    return {
        "content_count": content_count,
        "saturation_level": saturation_level,
        "saturation_signal": saturation_signal,
        "queries_used": queries["blog_queries"],
        "top_5": [
            {'title': r.get('title'), 'url': r.get('url')}
            for r in blog_results[:5]
        ]
    }


@app.post("/analyze-market")
def analyze_market(data: IdeaInput):
    """
    Comprehensive market analysis combining problem severity, competition, and content.
    
    This is the new endpoint that uses ALL query buckets:
    - complaint_queries → problem severity
    - tool_queries + workaround_queries → competition pressure
    - blog_queries → content saturation
    
    Returns:
        Dict with problem, competition, and content_saturation analyses
    """
    # Problem severity analysis (existing)
    problem_analysis = analyze_idea(data)
    
    # Competition analysis (new - ISSUE 2)
    competition_analysis = analyze_competition(data.problem)
    
    # Content saturation analysis (new - ISSUE 2)
    content_analysis = analyze_content_saturation(data.problem)
    
    return {
        "problem": problem_analysis,
        "competition": competition_analysis,
        "content_saturation": content_analysis
    }


# ============================================================================
# STAGE 2: USER-SOLUTION COMPETITOR DETECTION
# ============================================================================

def generate_solution_class_queries(solution: UserSolution):
    """
    Generate deterministic search queries based on user's solution attributes.
    
    This is STAGE 2 ONLY - generates queries specific to the user's solution,
    not the problem space.
    
    RULES:
    - Queries are rule-generated and deterministic
    - Use static templates based on solution attributes
    - No free-text input, only structured attributes
    - No LLM rewriting or semantic expansion
    
    QUERY TEMPLATES:
    - "{automation_level} {core_action} software"
    - "{core_action} {output_type} tool"
    - "{target_user} {core_action} platform"
    - "automated {core_action} service"
    
    Args:
        solution: UserSolution with structured attributes
        
    Returns:
        List of search query strings (3-5 queries)
    """
    # Extract and normalize attributes
    core_action = solution.core_action.lower().strip()
    output_type = solution.output_type.lower().strip()
    target_user = solution.target_user.lower().strip()
    automation_level = solution.automation_level.lower().strip()
    
    # Generate queries using fixed templates
    # Each template focuses on a different aspect of the solution
    queries = [
        # Template 1: Focus on automation + action
        f"{automation_level} {core_action} software",
        
        # Template 2: Focus on action + output
        f"{core_action} {output_type} tool",
        
        # Template 3: Focus on target user + action
        f"{target_user} {core_action} platform",
        
        # Template 4: Generic automation + action
        f"automated {core_action} service",
    ]
    
    # Deduplicate queries (case-insensitive)
    seen = set()
    unique_queries = []
    for query in queries:
        normalized = query.lower().strip()
        if normalized not in seen and len(normalized) > 5:  # Minimum length check
            seen.add(normalized)
            unique_queries.append(query)
    
    logger.info(f"Generated {len(unique_queries)} solution-class queries")
    logger.debug(f"Solution-class queries: {unique_queries}")
    
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


def analyze_user_solution_competitors(solution: UserSolution):
    """
    Detect competitors specific to the user's solution (Stage 2).
    
    This is STAGE 2 ONLY - finds competitors offering similar solutions,
    not just addressing the same problem space (which is Stage 1).
    
    PROCESS:
    1. Generate solution-class queries (deterministic, template-based)
    2. Run searches using these queries
    3. Classify results using SAME classifier from Stage 1
    4. Return ONLY commercial products (no blogs, Reddit, Quora, reviews)
    
    CONSTRAINTS:
    - No ranking or scoring
    - No comparison to user's product
    - No LLM reasoning
    - Strictly separated from Stage 1
    
    Args:
        solution: UserSolution with structured attributes
        
    Returns:
        Dict with:
        - exists: bool (competitors found)
        - count: int (number of commercial competitors)
        - products: list of commercial product dicts
    """
    # Step 1: Generate solution-class queries
    queries = generate_solution_class_queries(solution)
    
    # Step 2: Run searches
    all_results = run_multiple_searches(queries)
    
    # Step 3: Deduplicate results
    unique_results = deduplicate_results(all_results)
    
    # Step 4: Classify and filter to ONLY commercial products
    commercial_products = []
    
    for result in unique_results:
        result_type = classify_result_type(result)
        
        # Only include COMMERCIAL products
        # Exclude: DIY, content (blogs/Reddit/Quora/reviews), unknown
        if result_type == 'commercial':
            # Extract product information
            product_info = {
                'name': result.get('title', 'Unknown Product'),
                'url': result.get('url', ''),
                'pricing_model': extract_pricing_model(result),
                'snippet': result.get('snippet', ''),
            }
            commercial_products.append(product_info)
            
            logger.debug(f"Found commercial competitor: {product_info['name']}")
        else:
            # Log excluded results for debugging
            logger.debug(
                f"Excluded from competitors (type={result_type}): "
                f"{result.get('url', 'unknown')}"
            )
    
    exists = len(commercial_products) > 0
    count = len(commercial_products)
    
    logger.info(
        f"Stage 2: Found {count} commercial competitors for user solution "
        f"(excluded {len(unique_results) - count} non-commercial results)"
    )
    
    return {
        'exists': exists,
        'count': count,
        'products': commercial_products,
        'queries_used': queries,
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
