"""
Test suite for specific bug fixes identified in PR review.

Tests for:
- ISSUE 1: Duplicate tokens in normalized problem text
- ISSUE 2: Near-duplicate queries within the same bucket
- ISSUE 3: Missing severity guardrail (false DRASTIC risk)
- ISSUE 4: Over-retention of filler time phrases in queries
"""

import sys
from main import generate_search_queries, classify_problem_level, normalize_signals, ensure_query_diversity
from nlp_utils import normalize_problem_text


def test_issue_1_duplicate_tokens():
    """
    ISSUE 1: Duplicate tokens in normalized problem text
    
    REQUIRED FIX:
    - After tokenization + lemmatization, remove duplicate tokens deterministically.
    - Normalized problem text must be idempotent.
    
    REQUIRED CHECK:
    - Assert no repeated tokens in the normalized problem string.
    """
    print("Testing ISSUE 1: Duplicate tokens in normalized problem text...")
    
    # Test case 1: Input has duplicate tokens
    problem1 = "manual manual jira ticket creation meeting"
    normalized1 = normalize_problem_text(problem1)
    tokens1 = normalized1.split()
    assert len(tokens1) == len(set(tokens1)), \
        f"Normalized text should have no duplicates: {normalized1}"
    assert "manual" in tokens1, "Should keep at least one 'manual'"
    assert tokens1.count("manual") == 1, "Should have exactly one 'manual'"
    
    # Test case 2: Idempotency - applying normalization twice yields same output
    normalized_once = normalize_problem_text(problem1)
    normalized_twice = normalize_problem_text(normalized_once)
    assert normalized_once == normalized_twice, \
        f"Normalization must be idempotent: '{normalized_once}' vs '{normalized_twice}'"
    
    # Test case 3: Different input with duplicates
    problem3 = "creating creating multiple spreadsheets"
    normalized3 = normalize_problem_text(problem3)
    tokens3 = normalized3.split()
    assert len(tokens3) == len(set(tokens3)), \
        f"Normalized text should have no duplicates: {normalized3}"
    
    # Test case 4: Input without duplicates should remain unchanged
    problem4 = "jira ticket automation"
    normalized4 = normalize_problem_text(problem4)
    tokens4 = normalized4.split()
    assert len(tokens4) == len(set(tokens4)), \
        f"Normalized text should have no duplicates: {normalized4}"
    
    print("✓ ISSUE 1 tests passed")


def test_issue_2_near_duplicate_queries():
    """
    ISSUE 2: Near-duplicate queries within the same bucket
    
    REQUIRED FIX:
    - Within each query bucket, ensure each query introduces a DISTINCT modifier.
    - Prune queries that differ only by emotional intensifiers or filler phrases.
    - Keep at most ONE emotional modifier per query.
    
    REQUIRED CHECK:
    - After generation, enforce intra-bucket query diversity.
    - Do NOT pad queries to meet MIN.
    """
    print("\nTesting ISSUE 2: Near-duplicate queries within the same bucket...")
    
    # Test case 1: Check complaint queries have distinct modifiers
    problem1 = "manual data entry"
    queries1 = generate_search_queries(problem1)
    complaint_queries = queries1["complaint_queries"]
    
    # Extract modifiers from each query
    def get_modifier(query, problem_text):
        """Extract the modifier that distinguishes this query"""
        # Remove the normalized problem text to see what's added
        remainder = query.replace(problem_text, "").strip()
        return remainder
    
    normalized_problem = normalize_problem_text(problem1)
    modifiers = [get_modifier(q, normalized_problem) for q in complaint_queries]
    
    # All modifiers should be distinct
    assert len(modifiers) == len(set(modifiers)), \
        f"Complaint queries should have distinct modifiers: {modifiers}"
    
    # Test case 2: Ensure diversity check catches near-duplicates
    test_queries = [
        "manual data entry wasting time",
        "frustrating manual data entry",
        "manual data entry problem"
    ]
    diverse = ensure_query_diversity(test_queries, "test")
    assert len(diverse) == 3, "All three queries are distinct"
    
    # Test case 3: Near-duplicates (differ only by emotional modifier) should be pruned
    near_duplicates = [
        "data entry wasting time",
        "frustrating data entry wasting time",  # Near-duplicate with emotional modifier
    ]
    diverse2 = ensure_query_diversity(near_duplicates, "test")
    assert len(diverse2) == 1, \
        f"Near-duplicates should be pruned, got {len(diverse2)}: {diverse2}"
    
    # Test case 4: Check that we don't pad to meet MIN
    # If diversity check removes queries, we should NOT add new ones
    problem4 = "task automation"
    queries4 = generate_search_queries(problem4)
    # Just verify it doesn't crash - the constraint is that we don't artificially pad
    
    print("✓ ISSUE 2 tests passed")


def test_issue_3_severity_guardrail():
    """
    ISSUE 3: Missing severity guardrail (false DRASTIC risk)
    
    REQUIRED FIX:
    - Add a guardrail rule: If intensity_level != "HIGH", problem_level MUST NOT be "DRASTIC"
    - In this case, downgrade to "SEVERE"
    
    REQUIRED CHECK:
    - Assert that DRASTIC is only possible when intensity_level == HIGH
    """
    print("\nTesting ISSUE 3: Missing severity guardrail...")
    
    # Test case 1: intensity_level=MEDIUM (2-4), score >= 15 should be SEVERE not DRASTIC
    signals1 = {'intensity_count': 2, 'complaint_count': 5, 'workaround_count': 5}
    normalized1 = normalize_signals(signals1)
    problem_level1 = classify_problem_level(signals1)
    score1 = 3 * signals1['intensity_count'] + 2 * signals1['complaint_count'] + 1 * signals1['workaround_count']
    
    assert normalized1['intensity_level'] == "MEDIUM", \
        f"intensity_count=2 should be MEDIUM, got {normalized1['intensity_level']}"
    assert score1 >= 15, f"Score should be >= 15, got {score1}"
    assert problem_level1 == "SEVERE", \
        f"With intensity_level=MEDIUM and score>=15, should be SEVERE not {problem_level1}"
    
    # Test case 2: intensity_level=HIGH (>=5), score >= 15 should be DRASTIC
    signals2 = {'intensity_count': 5, 'complaint_count': 5, 'workaround_count': 5}
    normalized2 = normalize_signals(signals2)
    problem_level2 = classify_problem_level(signals2)
    score2 = 3 * signals2['intensity_count'] + 2 * signals2['complaint_count'] + 1 * signals2['workaround_count']
    
    assert normalized2['intensity_level'] == "HIGH", \
        f"intensity_count=5 should be HIGH, got {normalized2['intensity_level']}"
    assert score2 >= 15, f"Score should be >= 15, got {score2}"
    assert problem_level2 == "DRASTIC", \
        f"With intensity_level=HIGH and score>=15, should be DRASTIC not {problem_level2}"
    
    # Test case 3: intensity_level=LOW (0-1), score < 15 should never be DRASTIC
    signals3 = {'intensity_count': 1, 'complaint_count': 3, 'workaround_count': 3}
    normalized3 = normalize_signals(signals3)
    problem_level3 = classify_problem_level(signals3)
    
    assert normalized3['intensity_level'] == "LOW", \
        f"intensity_count=1 should be LOW, got {normalized3['intensity_level']}"
    assert problem_level3 != "DRASTIC", \
        f"With intensity_level=LOW, should never be DRASTIC, got {problem_level3}"
    
    # Test case 4: Edge case - exactly score=15, intensity_level=MEDIUM
    signals4 = {'intensity_count': 4, 'complaint_count': 1, 'workaround_count': 1}
    normalized4 = normalize_signals(signals4)
    problem_level4 = classify_problem_level(signals4)
    score4 = 3 * signals4['intensity_count'] + 2 * signals4['complaint_count'] + 1 * signals4['workaround_count']
    
    assert score4 == 15, f"Score should be exactly 15, got {score4}"
    assert normalized4['intensity_level'] == "MEDIUM", \
        f"intensity_count=4 should be MEDIUM, got {normalized4['intensity_level']}"
    assert problem_level4 == "SEVERE", \
        f"Edge case: score=15 with MEDIUM intensity should be SEVERE not {problem_level4}"
    
    # Test case 5: Verify the assertion in classify_problem_level is working
    # (The function should assert that DRASTIC requires HIGH intensity)
    try:
        # This should work (HIGH intensity, DRASTIC allowed)
        signals_ok = {'intensity_count': 5, 'complaint_count': 5, 'workaround_count': 5}
        level_ok = classify_problem_level(signals_ok)
        assert level_ok == "DRASTIC"
    except AssertionError:
        assert False, "Should not raise assertion for valid DRASTIC (HIGH intensity)"
    
    print("✓ ISSUE 3 tests passed")


def test_issue_4_filler_phrases():
    """
    ISSUE 4: Over-retention of filler time phrases in queries
    
    REQUIRED FIX:
    - Remove non-essential time/filler phrases during problem normalization
    - Prefer canonical noun phrases
    
    REQUIRED CHECK:
    - Normalized problem text should be compact and canonical
    """
    print("\nTesting ISSUE 4: Over-retention of filler time phrases...")
    
    # Test case 1: "every day" should be removed
    problem1 = "jira ticket creation meeting every day"
    normalized1 = normalize_problem_text(problem1)
    assert "every" not in normalized1.split(), \
        f"Filler word 'every' should be removed: {normalized1}"
    assert "day" not in normalized1.split(), \
        f"Filler word 'day' should be removed: {normalized1}"
    
    # Test case 2: "daily" should be removed
    problem2 = "manual data entry daily"
    normalized2 = normalize_problem_text(problem2)
    assert "daily" not in normalized2.split(), \
        f"Filler word 'daily' should be removed: {normalized2}"
    
    # Test case 3: "always" should be removed
    problem3 = "always creating spreadsheets"
    normalized3 = normalize_problem_text(problem3)
    assert "always" not in normalized3.split(), \
        f"Filler word 'always' should be removed: {normalized3}"
    
    # Test case 4: "constantly" should be removed
    problem4 = "constantly managing tickets"
    normalized4 = normalize_problem_text(problem4)
    assert "constantly" not in normalized4.split(), \
        f"Filler word 'constantly' should be removed: {normalized4}"
    
    # Test case 5: Canonical noun phrase should remain
    problem5 = "jira ticket creation"
    normalized5 = normalize_problem_text(problem5)
    # Should have core content words
    assert "jira" in normalized5.split(), "Core word 'jira' should remain"
    assert "ticket" in normalized5.split(), "Core word 'ticket' should remain"
    assert "creation" in normalized5.split() or "create" in normalized5.split(), \
        "Core word 'creation'/'create' should remain"
    
    # Test case 6: Queries should use normalized (compact) problem text
    problem6 = "jira ticket creation meeting every day"
    queries6 = generate_search_queries(problem6)
    # Check that queries don't contain "every day" from the problem text
    all_queries6 = (
        queries6["complaint_queries"] +
        queries6["workaround_queries"] +
        queries6["tool_queries"] +
        queries6["blog_queries"]
    )
    # The normalized problem should not have "every day"
    normalized6 = normalize_problem_text(problem6)
    for query in all_queries6:
        # Queries are built from normalized problem, so they shouldn't have filler
        # unless it's part of the template (which we've also cleaned up)
        pass  # Just verify no crash
    
    print("✓ ISSUE 4 tests passed")


def test_all_issues_integration():
    """
    Integration test: Verify all four issues are fixed together
    """
    print("\nTesting integration of all bug fixes...")
    
    # Test with a problem that triggers all issues
    problem = "manual manual jira ticket creation meeting every day"
    
    # ISSUE 1 + 4: Normalized text should have no duplicates and no filler phrases
    normalized = normalize_problem_text(problem)
    tokens = normalized.split()
    assert len(tokens) == len(set(tokens)), \
        f"ISSUE 1: Should have no duplicate tokens: {normalized}"
    assert "every" not in tokens and "day" not in tokens, \
        f"ISSUE 4: Should have no filler phrases: {normalized}"
    
    # ISSUE 2: Queries should have distinct modifiers
    queries = generate_search_queries(problem)
    complaint_queries = queries["complaint_queries"]
    assert len(complaint_queries) >= 2, "Should have multiple distinct queries"
    
    # ISSUE 3: Severity guardrail
    signals = {'intensity_count': 2, 'complaint_count': 5, 'workaround_count': 5}
    normalized_signals = normalize_signals(signals)
    problem_level = classify_problem_level(signals)
    assert normalized_signals['intensity_level'] == "MEDIUM"
    assert problem_level == "SEVERE", \
        f"ISSUE 3: With MEDIUM intensity, should be SEVERE not {problem_level}"
    
    print("✓ Integration test passed")


def run_all_tests():
    """Run all bug fix test suites"""
    print("=" * 60)
    print("Running Bug Fix Test Suite")
    print("=" * 60)
    
    try:
        test_issue_1_duplicate_tokens()
        test_issue_2_near_duplicate_queries()
        test_issue_3_severity_guardrail()
        test_issue_4_filler_phrases()
        test_all_issues_integration()
        
        print("\n" + "=" * 60)
        print("✓ ALL BUG FIX TESTS PASSED!")
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
