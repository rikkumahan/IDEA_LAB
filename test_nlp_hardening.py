"""
Test suite for NLP hardening improvements.
Tests deterministic NLP preprocessing and signal extraction.
"""

import sys
sys.path.insert(0, '/home/runner/work/IDEA_LAB/IDEA_LAB')

from nlp_utils import (
    tokenize_text,
    remove_stopwords,
    stem_tokens,
    stem_word,
    preprocess_text,
    match_keyword_with_context,
    match_keywords_with_deduplication,
    check_excluded_phrase,
    check_required_context,
)


def test_stemming():
    """Test that stemming captures morphological variants"""
    print("Testing stemming...")
    
    # Test complaint variants
    assert stem_word("frustrated") == stem_word("frustrating")
    assert stem_word("problem") == stem_word("problems")
    
    # Test workaround variants
    assert stem_word("automate") == stem_word("automation")
    assert stem_word("automate") == stem_word("automated")
    assert stem_word("script") == stem_word("scripted")
    assert stem_word("script") == stem_word("scripting")
    
    # Test intensity variants
    assert stem_word("blocking") == stem_word("blocked")
    assert stem_word("critical") == stem_word("critically")
    
    print("✓ Stemming tests passed")


def test_false_positive_prevention():
    """Test that false positives are prevented"""
    print("\nTesting false positive prevention...")
    
    # Test "automation bias" should NOT match "automation"
    text1 = "This article discusses automation bias in decision making"
    preprocessed1 = preprocess_text(text1)
    assert not match_keyword_with_context("automation", preprocessed1), \
        "Should not match 'automation' in 'automation bias'"
    
    # Test "critical acclaim" should NOT match "critical"
    text2 = "This movie received critical acclaim from reviewers"
    preprocessed2 = preprocess_text(text2)
    assert not match_keyword_with_context("critical", preprocessed2), \
        "Should not match 'critical' in 'critical acclaim'"
    
    # Test "blocking ads" should NOT match "blocking"
    text3 = "Chrome extension for blocking ads effectively"
    preprocessed3 = preprocess_text(text3)
    assert not match_keyword_with_context("blocking", preprocessed3), \
        "Should not match 'blocking' in 'blocking ads'"
    
    print("✓ False positive prevention tests passed")


def test_valid_matches():
    """Test that valid signals are correctly matched"""
    print("\nTesting valid matches...")
    
    # Test valid complaint
    text1 = "This manual process is very frustrating"
    preprocessed1 = preprocess_text(text1)
    assert match_keyword_with_context("frustrating", preprocessed1), \
        "Should match 'frustrating' in complaint context"
    assert match_keyword_with_context("manual", preprocessed1), \
        "Should match 'manual' in complaint context"
    
    # Test valid workaround
    text2 = "Looking for automation solution to this problem"
    preprocessed2 = preprocess_text(text2)
    assert match_keyword_with_context("automation", preprocessed2), \
        "Should match 'automation' when not in 'automation bias'"
    
    # Test valid intensity with required context
    text3 = "This is a critical issue that needs urgent attention"
    preprocessed3 = preprocess_text(text3)
    assert match_keyword_with_context("critical", preprocessed3), \
        "Should match 'critical' in 'critical issue'"
    assert match_keyword_with_context("urgent", preprocessed3), \
        "Should match 'urgent' in 'urgent attention'"
    
    print("✓ Valid match tests passed")


def test_morphological_variants():
    """Test that morphological variants are caught"""
    print("\nTesting morphological variant matching...")
    
    # Test frustrated vs frustrating
    text1 = "Users are frustrated with this manual process"
    preprocessed1 = preprocess_text(text1)
    assert match_keyword_with_context("frustrating", preprocessed1), \
        "Should match 'frustrating' keyword when text has 'frustrated'"
    
    # Test problems vs problem
    text2 = "We have serious problems with data entry"
    preprocessed2 = preprocess_text(text2)
    assert match_keyword_with_context("problem", preprocessed2), \
        "Should match 'problem' keyword when text has 'problems'"
    
    # Test scripted vs script
    text3 = "Looking for scripted solution to automate this"
    preprocessed3 = preprocess_text(text3)
    assert match_keyword_with_context("script", preprocessed3), \
        "Should match 'script' keyword when text has 'scripted'"
    
    print("✓ Morphological variant tests passed")


def test_tokenization():
    """Test token-based matching prevents substring false positives"""
    print("\nTesting tokenization...")
    
    # Test that "costly" doesn't match "costing" when used differently
    text1 = "This is a costly mistake but not about time"
    preprocessed1 = preprocess_text(text1)
    tokens = preprocessed1['tokens']
    assert 'costly' in tokens or 'costli' in preprocessed1['stems']
    
    print("✓ Tokenization tests passed")


def test_stopword_removal():
    """Test stopword removal"""
    print("\nTesting stopword removal...")
    
    text = "The problem is that we have issues"
    preprocessed = preprocess_text(text)
    
    # Check that stopwords are removed
    tokens_no_stopwords = preprocessed['tokens_no_stopwords']
    assert 'the' not in tokens_no_stopwords
    assert 'is' not in tokens_no_stopwords
    assert 'that' not in tokens_no_stopwords
    assert 'we' not in tokens_no_stopwords
    
    # Check that content words remain
    assert 'problem' in tokens_no_stopwords
    assert 'issues' in tokens_no_stopwords
    
    print("✓ Stopword removal tests passed")


def test_excluded_phrases():
    """Test excluded phrase detection"""
    print("\nTesting excluded phrase detection...")
    
    # Test automation bias (stem is 'autom')
    assert check_excluded_phrase('autom', 'automation bias discussion', [])
    assert not check_excluded_phrase('autom', 'automation solution', [])
    
    # Test critical acclaim
    assert check_excluded_phrase('critic', 'received critical acclaim', [])
    assert not check_excluded_phrase('critic', 'critical bug in system', [])
    
    print("✓ Excluded phrase tests passed")


def test_required_context():
    """Test required context validation"""
    print("\nTesting required context validation...")
    
    # Test critical - needs context
    assert check_required_context('critic', 'critical issue found', [])
    assert not check_required_context('critic', 'critical thinking skills', [])
    
    # Test urgent - needs context
    assert check_required_context('urgent', 'urgent need for solution', [])
    
    print("✓ Required context tests passed")


def test_signal_extraction_integration():
    """Integration test for complete signal extraction"""
    print("\nTesting signal extraction integration...")
    
    # Import here to avoid circular dependency during initial setup
    from main import extract_signals
    
    # Test case 1: Document with intensity signal
    results1 = [
        {"title": "Critical issue blocking production", "snippet": "This is urgent", "url": "http://test1.com"}
    ]
    signals1 = extract_signals(results1)
    assert signals1['intensity_count'] == 1
    assert signals1['complaint_count'] == 0  # Should not double-count
    assert signals1['workaround_count'] == 0  # Should not double-count
    
    # Test case 2: Document with complaint signal (but no intensity)
    results2 = [
        {"title": "Manual data entry is frustrating", "snippet": "This is a problem for users", "url": "http://test2.com"}
    ]
    signals2 = extract_signals(results2)
    # Should count as complaint (frustrating, manual, problem are all complaint keywords)
    # Note: priority order means intensity > complaint, so this should be complaint
    assert signals2['complaint_count'] >= 1, f"Expected complaint, got {signals2}"
    
    # Test case 3: Document with workaround signal
    results3 = [
        {"title": "How to automate this task", "snippet": "Looking for automation solution", "url": "http://test3.com"}
    ]
    signals3 = extract_signals(results3)
    assert signals3['workaround_count'] >= 1  # Should count workaround
    
    # Test case 4: False positive - automation bias
    results4 = [
        {"title": "Understanding automation bias", "snippet": "Automation bias is a cognitive bias", "url": "http://test4.com"}
    ]
    signals4 = extract_signals(results4)
    assert signals4['workaround_count'] == 0, "Should not count 'automation bias' as workaround"
    
    # Test case 5: Multiple documents, each contributes once
    results5 = [
        {"title": "Urgent critical issue", "snippet": "This is a serious problem", "url": "http://test5a.com"},
        {"title": "Frustrating manual work", "snippet": "This problem is annoying", "url": "http://test5b.com"},
        {"title": "How to automate", "snippet": "Need scripting solution", "url": "http://test5c.com"}
    ]
    signals5 = extract_signals(results5)
    # Each document should contribute to exactly one category
    total_signals = signals5['intensity_count'] + signals5['complaint_count'] + signals5['workaround_count']
    assert total_signals == 3, f"Expected 3 total signals (one per document), got {total_signals}"
    
    print("✓ Signal extraction integration tests passed")


def run_all_tests():
    """Run all test suites"""
    print("=" * 60)
    print("Running NLP Hardening Test Suite")
    print("=" * 60)
    
    try:
        test_stemming()
        test_false_positive_prevention()
        test_valid_matches()
        test_morphological_variants()
        test_tokenization()
        test_stopword_removal()
        test_excluded_phrases()
        test_required_context()
        test_signal_extraction_integration()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
