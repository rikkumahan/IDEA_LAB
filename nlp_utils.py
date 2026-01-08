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
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.util import ngrams

# Initialize stemmer (deterministic algorithm)
stemmer = PorterStemmer()

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
