"""
Script to download required NLTK data for signal extraction.
This only needs to be run once during setup.
"""

import nltk
import ssl

# Handle SSL certificate issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download required NLTK data
print("Downloading NLTK data...")
nltk.download('punkt', quiet=False)
nltk.download('stopwords', quiet=False)
nltk.download('punkt_tab', quiet=False)
nltk.download('wordnet', quiet=False)  # For lemmatization
print("NLTK data download complete!")
