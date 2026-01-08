"""
NLP Hardening Utilities for Signal Extraction

This module provides DETERMINISTIC NLP preprocessing techniques:
- Tokenization
- Porter/Snowball Stemming
- Stopword removal
- N-gram extraction
- Rule-based phrase detection

NO semantic reasoning, embeddings, ML models, or AI judgment.
"""

import re
from typing import List, Set, Tuple, Dict, Any
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.util import ngrams

# Initialize stemmer (deterministic algorithm)
stemmer = PorterStemmer()

# Initialize lemmatizer for query normalization
lemmatizer = WordNetLemmatizer()

# English stopwords (deterministic list)
STOPWORDS = set(stopwords.words('english'))

# Excluded phrases - phrases where keywords should NOT match
# Format: (keyword_stem, excluded_phrase_pattern)
EXCLUDED_PHRASES = {
    'autom': [  # automation/automate stem
        'automation bias',
        'automation paradox',
        'automated testing',  # Not a workaround, it's about testing
        'test automation',
    ],
    'critic': [  # critical stem
        'critical acclaim',
        'critical thinking',
        'critical review',
        'critically acclaimed',
    ],
    'seriou': [  # serious stem
        'serious developer',
        'serious programmer',
        'serious gamer',
    ],
    'block': [  # blocking stem
        'blocking ads',
        'ad blocking',
        'ad blocker',
    ],
    'cost': [  # costing stem
        'low cost',
        'no cost',
        'at cost',
        'cost effective',
    ],
    'pain': [  # painful stem
        # Note: "pain point" is actually valid for complaints, so we don't exclude it
        # We only exclude painting-related terms
        'painting',
    ],
    'problem': [
        'no problem',
        'not a problem',
    ],
}

# Required context phrases - keyword must appear with these patterns
# Format: (keyword_stem, required_context_pattern)
# Only highly ambiguous keywords should require context
REQUIRED_CONTEXT = {
    'critic': ['critical issue', 'critical problem', 'critical bug', 'critical error', 'critical failure'],
    'sever': ['severe issue', 'severe problem', 'severe bug', 'severe error'],
    'block': ['blocking issue', 'blocking problem', 'blocking bug', 'blocking error', 'blocked by', 'blocker'],
}


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize text into words using NLTK word_tokenize.
    This is a deterministic, rule-based tokenization.
    
    Args:
        text: Input text string
        
    Returns:
        List of tokens (words)
    """
    if not text:
        return []
    
    # Convert to lowercase for normalization
    text = text.lower()
    
    # Tokenize using NLTK (rule-based)
    tokens = word_tokenize(text)
    
    return tokens


def remove_stopwords(tokens: List[str]) -> List[str]:
    """
    Remove common English stopwords from token list.
    Uses deterministic stopword list from NLTK.
    
    Args:
        tokens: List of word tokens
        
    Returns:
        List of tokens with stopwords removed
    """
    return [token for token in tokens if token not in STOPWORDS]


def stem_tokens(tokens: List[str]) -> List[str]:
    """
    Apply Porter stemming to normalize word forms.
    This is a deterministic algorithm, no ML involved.
    
    Examples:
        frustrated, frustrating → frustrat
        problems, problem → problem
        automation, automate, automated → automat
    
    Args:
        tokens: List of word tokens
        
    Returns:
        List of stemmed tokens
    """
    return [stemmer.stem(token) for token in tokens]


def stem_word(word: str) -> str:
    """
    Stem a single word using Porter stemmer.
    
    Args:
        word: Single word to stem
        
    Returns:
        Stemmed word
    """
    return stemmer.stem(word.lower())


def extract_ngrams(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
    """
    Extract n-grams from token list for phrase detection.
    This is deterministic sequence extraction.
    
    Args:
        tokens: List of tokens
        n: Size of n-grams (2 for bigrams, 3 for trigrams, etc.)
        
    Returns:
        List of n-gram tuples
    """
    if len(tokens) < n:
        return []
    
    return list(ngrams(tokens, n))


def check_excluded_phrase(keyword_stem: str, text: str, tokens: List[str]) -> bool:
    """
    Check if keyword appears in an excluded phrase context.
    Uses deterministic phrase matching.
    
    Args:
        keyword_stem: Stemmed keyword to check
        text: Original text (lowercase)
        tokens: Tokenized text
        
    Returns:
        True if keyword appears in excluded context (should NOT match)
    """
    if keyword_stem not in EXCLUDED_PHRASES:
        return False
    
    # Check each excluded phrase pattern
    for excluded_pattern in EXCLUDED_PHRASES[keyword_stem]:
        # Simple substring check in original text
        if excluded_pattern.lower() in text:
            return True
    
    return False


def check_required_context(keyword_stem: str, text: str, tokens: List[str]) -> bool:
    """
    Check if keyword appears with required context.
    Some keywords should only match in specific phrase patterns.
    
    Args:
        keyword_stem: Stemmed keyword to check
        text: Original text (lowercase)
        tokens: Tokenized text
        
    Returns:
        True if keyword appears in required context (or no context required)
    """
    if keyword_stem not in REQUIRED_CONTEXT:
        # No required context for this keyword
        return True
    
    # Check if any required context pattern is present
    for required_pattern in REQUIRED_CONTEXT[keyword_stem]:
        if required_pattern.lower() in text:
            return True
    
    # Required context not found
    return False


def preprocess_text(text: str) -> Dict[str, Any]:
    """
    Complete deterministic NLP preprocessing pipeline.
    
    Steps:
    1. Tokenization
    2. Stemming
    3. Stopword removal (optional for matching)
    4. N-gram extraction for phrase detection
    
    Args:
        text: Input text to preprocess
        
    Returns:
        Dictionary with:
        - original_text: Original text (lowercased)
        - tokens: List of tokens
        - tokens_no_stopwords: Tokens with stopwords removed
        - stems: Stemmed tokens
        - stems_no_stopwords: Stemmed tokens with stopwords removed
        - bigrams: List of bigrams for phrase detection
        - trigrams: List of trigrams for phrase detection
    """
    if not text:
        return {
            'original_text': '',
            'tokens': [],
            'tokens_no_stopwords': [],
            'stems': [],
            'stems_no_stopwords': [],
            'bigrams': [],
            'trigrams': [],
        }
    
    # Lowercase original text
    text_lower = text.lower()
    
    # Tokenize
    tokens = tokenize_text(text_lower)
    
    # Remove stopwords
    tokens_no_stopwords = remove_stopwords(tokens)
    
    # Stem tokens
    stems = stem_tokens(tokens)
    stems_no_stopwords = stem_tokens(tokens_no_stopwords)
    
    # Extract n-grams for phrase detection
    bigrams = extract_ngrams(tokens, 2)
    trigrams = extract_ngrams(tokens, 3)
    
    return {
        'original_text': text_lower,
        'tokens': tokens,
        'tokens_no_stopwords': tokens_no_stopwords,
        'stems': stems,
        'stems_no_stopwords': stems_no_stopwords,
        'bigrams': bigrams,
        'trigrams': trigrams,
    }


def match_keyword_with_context(keyword: str, preprocessed: Dict[str, Any]) -> bool:
    """
    Check if keyword matches in preprocessed text with proper context validation.
    
    This function:
    1. Stems the keyword
    2. Checks if stem appears in preprocessed stems
    3. Validates it's not in excluded phrase context
    4. Validates required context is present (if any)
    
    Args:
        keyword: Keyword to match (will be stemmed)
        preprocessed: Result from preprocess_text()
        
    Returns:
        True if keyword matches with valid context
    """
    keyword_stem = stem_word(keyword)
    
    # Check if stem appears in text
    if keyword_stem not in preprocessed['stems']:
        return False
    
    # Check if in excluded phrase context
    if check_excluded_phrase(keyword_stem, preprocessed['original_text'], 
                             preprocessed['tokens']):
        return False
    
    # Check if required context is present
    if not check_required_context(keyword_stem, preprocessed['original_text'],
                                   preprocessed['tokens']):
        return False
    
    return True


def match_keywords_with_deduplication(keywords: List[str], preprocessed: Dict[str, Any]) -> bool:
    """
    Check if ANY keyword from list matches in preprocessed text.
    Returns True on first match (for efficiency).
    
    Args:
        keywords: List of keywords to check
        preprocessed: Result from preprocess_text()
        
    Returns:
        True if at least one keyword matches with valid context
    """
    for keyword in keywords:
        if match_keyword_with_context(keyword, preprocessed):
            return True
    
    return False


def normalize_problem_text(problem: str) -> str:
    """
    Normalize problem text BEFORE query generation using deterministic NLP.
    
    This function:
    1. Converts to lowercase
    2. Tokenizes
    3. Removes stopwords (excluding important negations like 'not', 'no', 'never')
    4. Lemmatizes (reduces words to base forms)
    5. Removes filler time phrases (e.g., "every day") unless required for meaning
    6. Removes duplicate tokens (preserves order, keeps first occurrence)
    7. Joins back into a normalized phrase
    
    This is DETERMINISTIC - same input always produces same output.
    NO LLM, embeddings, or semantic reasoning.
    
    IDEMPOTENCY: Applying normalization twice yields the same output.
    
    Args:
        problem: Raw problem text from user input
        
    Returns:
        Normalized problem text (lowercase, lemmatized, core content words)
        
    Example:
        Input:  "Managing multiple spreadsheets daily"
        Output: "manage multiple spreadsheet daily"
        
        Input:  "Frustrated with manual data entry"
        Output: "frustrate manual data entry"
        
        Input:  "manual manual jira ticket creation meeting"
        Output: "manual jira ticket creation meet"
    """
    if not problem or not problem.strip():
        return ""
    
    # Step 1: Lowercase
    text = problem.lower().strip()
    
    # Step 2: Tokenize
    tokens = word_tokenize(text)
    
    # Step 3: Remove stopwords (but keep important ones for context)
    # We keep some stopwords that might be meaningful in problem descriptions
    minimal_stopwords = STOPWORDS - {'not', 'no', 'never', 'cannot', 'can\'t'}
    tokens_filtered = [t for t in tokens if t.isalnum() and t not in minimal_stopwords]
    
    # Step 4: Lemmatize (reduce to base forms)
    # Try both noun and verb lemmatization to get the most common form
    lemmatized = []
    for token in tokens_filtered:
        # Try verb lemmatization first (often more specific)
        verb_form = lemmatizer.lemmatize(token, pos='v')
        # Try noun lemmatization
        noun_form = lemmatizer.lemmatize(token, pos='n')
        # Use the shorter form (usually the base form)
        if len(verb_form) <= len(noun_form):
            lemmatized.append(verb_form)
        else:
            lemmatized.append(noun_form)
    
    # Step 5: Remove non-essential filler time phrases
    # These add noise without increasing signal quality
    filler_phrases = {'every', 'day', 'daily', 'everyday', 'always', 'constantly'}
    lemmatized = [token for token in lemmatized if token not in filler_phrases]
    
    # Step 6: Remove duplicate tokens (ISSUE 1 FIX)
    # Preserves order by keeping first occurrence of each token
    # This ensures idempotency: normalize(normalize(x)) == normalize(x)
    seen = set()
    deduplicated = []
    for token in lemmatized:
        if token not in seen:
            seen.add(token)
            deduplicated.append(token)
    
    # Step 7: Join back into normalized phrase
    normalized = ' '.join(deduplicated)
    
    # ASSERTION: No repeated tokens in normalized text
    tokens_list = normalized.split()
    assert len(tokens_list) == len(set(tokens_list)), \
        f"Normalized text contains duplicate tokens: {normalized}"
    
    return normalized
