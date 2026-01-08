"""
Test suite for hardened query generation with deterministic normalization.
Tests MIN-MAX bounds enforcement, query deduplication, and bucket separation.
"""

import sys
from main import generate_search_queries, enforce_bounds, deduplicate_queries
from nlp_utils import normalize_problem_text


def test_text_normalization():
    """Test deterministic text normalization"""
    print("Testing text normalization...")
    
    # Test case 1: Basic normalization
    result1 = normalize_problem_text("Managing multiple spreadsheets")
    assert "manage" in result1, f"Expected 'manage' in '{result1}'"
    assert "multiple" in result1, f"Expected 'multiple' in '{result1}'"
    assert "spreadsheet" in result1, f"Expected 'spreadsheet' in '{result1}'"
    
    # Test case 2: Stopword removal
    result2 = normalize_problem_text("The problem is with the data entry")
    assert "the" not in result2.split(), "Stopword 'the' should be removed"
    assert "is" not in result2.split(), "Stopword 'is' should be removed"
    assert "with" not in result2.split(), "Stopword 'with' should be removed"
    assert "data" in result2, "Content word 'data' should remain"
    assert "entry" in result2, "Content word 'entry' should remain"
    
    # Test case 3: Lemmatization
    result3 = normalize_problem_text("Managing multiple spreadsheets daily")
    # "Managing" -> "manage", "spreadsheets" -> "spreadsheet"
    assert "manage" in result3, "Should lemmatize 'Managing' to 'manage'"
    assert "spreadsheet" in result3, "Should lemmatize 'spreadsheets' to 'spreadsheet'"
    
    # Test case 4: Lowercase
    result4 = normalize_problem_text("MANUAL DATA ENTRY")
    assert result4 == result4.lower(), "Should be lowercase"
    
    # Test case 5: Empty input
    result5 = normalize_problem_text("")
    assert result5 == "", "Empty input should return empty string"
    
    # Test case 6: Deterministic (same input = same output)
    text = "Frustrated with manual tasks"
    result6a = normalize_problem_text(text)
    result6b = normalize_problem_text(text)
    assert result6a == result6b, "Normalization must be deterministic"
    
    print("✓ Text normalization tests passed")


def test_min_max_bounds_enforcement():
    """Test strict MIN-MAX bounds per bucket"""
    print("\nTesting MIN-MAX bounds enforcement...")
    
    # Test case 1: Within bounds (no change)
    queries1 = ["query1", "query2", "query3"]
    result1 = enforce_bounds(queries1, min_count=2, max_count=4, bucket_name="test")
    assert len(result1) == 3, "Should not change when within bounds"
    assert result1 == queries1, "Should return same list when within bounds"
    
    # Test case 2: Below minimum (warning logged, return as-is)
    queries2 = ["query1"]
    result2 = enforce_bounds(queries2, min_count=3, max_count=4, bucket_name="test")
    assert len(result2) == 1, "Should return what we have when below MIN"
    assert result2 == queries2, "Should not add queries when below MIN"
    
    # Test case 3: Above maximum (trim to MAX)
    queries3 = ["query1", "query2", "query3", "query4", "query5"]
    result3 = enforce_bounds(queries3, min_count=2, max_count=3, bucket_name="test")
    assert len(result3) == 3, "Should trim to MAX when above maximum"
    assert result3 == queries3[:3], "Should keep first N queries (deterministic)"
    
    # Test case 4: At minimum
    queries4 = ["query1", "query2", "query3"]
    result4 = enforce_bounds(queries4, min_count=3, max_count=5, bucket_name="test")
    assert len(result4) == 3, "Should not change when at MIN"
    
    # Test case 5: At maximum
    queries5 = ["query1", "query2", "query3", "query4"]
    result5 = enforce_bounds(queries5, min_count=2, max_count=4, bucket_name="test")
    assert len(result5) == 4, "Should not change when at MAX"
    
    print("✓ MIN-MAX bounds enforcement tests passed")


def test_query_deduplication():
    """Test query deduplication after normalization"""
    print("\nTesting query deduplication...")
    
    # Test case 1: No duplicates
    queries1 = ["query1", "query2", "query3"]
    result1 = deduplicate_queries(queries1)
    assert len(result1) == 3, "Should not remove unique queries"
    assert result1 == queries1, "Should preserve order"
    
    # Test case 2: Exact duplicates
    queries2 = ["query1", "query2", "query1", "query3"]
    result2 = deduplicate_queries(queries2)
    assert len(result2) == 3, "Should remove exact duplicates"
    assert result2 == ["query1", "query2", "query3"], "Should keep first occurrence"
    
    # Test case 3: Case-insensitive deduplication
    queries3 = ["Query1", "query1", "QUERY1"]
    result3 = deduplicate_queries(queries3)
    assert len(result3) == 1, "Should remove case-insensitive duplicates"
    
    # Test case 4: Whitespace normalization
    queries4 = ["query  1", "query 1", "query   1"]
    result4 = deduplicate_queries(queries4)
    assert len(result4) == 1, "Should normalize whitespace for deduplication"
    
    # Test case 5: Empty list
    queries5 = []
    result5 = deduplicate_queries(queries5)
    assert len(result5) == 0, "Should handle empty list"
    
    # Test case 6: Preserves order (deterministic)
    queries6 = ["zebra", "apple", "zebra", "banana", "apple"]
    result6 = deduplicate_queries(queries6)
    assert result6 == ["zebra", "apple", "banana"], "Should preserve first occurrence order"
    
    print("✓ Query deduplication tests passed")


def test_bucket_separation():
    """Test that query buckets have no overlap in intent"""
    print("\nTesting bucket separation...")
    
    problem = "manual data entry"
    queries = generate_search_queries(problem)
    
    # Get all queries from all buckets
    complaint_queries = set(queries["complaint_queries"])
    workaround_queries = set(queries["workaround_queries"])
    tool_queries = set(queries["tool_queries"])
    blog_queries = set(queries["blog_queries"])
    
    # Test case 1: No exact duplicates across buckets
    all_queries = (
        list(complaint_queries) +
        list(workaround_queries) +
        list(tool_queries) +
        list(blog_queries)
    )
    assert len(all_queries) == len(set(all_queries)), \
        "Queries should not be duplicated across buckets"
    
    # Test case 2: Complaint queries contain complaint indicators
    complaint_indicators = ["every day", "wasting time", "frustrating", "manual"]
    for query in complaint_queries:
        has_indicator = any(indicator in query.lower() for indicator in complaint_indicators)
        assert has_indicator, f"Complaint query '{query}' should contain complaint indicator"
    
    # Test case 3: Workaround queries contain workaround indicators
    workaround_indicators = ["automate", "workaround", "script", "automation"]
    for query in workaround_queries:
        has_indicator = any(indicator in query.lower() for indicator in workaround_indicators)
        assert has_indicator, f"Workaround query '{query}' should contain workaround indicator"
    
    # Test case 4: Tool queries contain tool indicators
    tool_indicators = ["tool", "software", "extension"]
    for query in tool_queries:
        has_indicator = any(indicator in query.lower() for indicator in tool_indicators)
        assert has_indicator, f"Tool query '{query}' should contain tool indicator"
    
    # Test case 5: Blog queries contain content indicators
    blog_indicators = ["blog", "guide", "best practices"]
    for query in blog_queries:
        has_indicator = any(indicator in query.lower() for indicator in blog_indicators)
        assert has_indicator, f"Blog query '{query}' should contain content indicator"
    
    print("✓ Bucket separation tests passed")


def test_bucket_bounds():
    """Test that all buckets respect their MIN-MAX bounds"""
    print("\nTesting bucket bounds...")
    
    problem = "manual data entry"
    queries = generate_search_queries(problem)
    
    # Test case 1: complaint_queries bounds (MIN=3, MAX=4)
    complaint_count = len(queries["complaint_queries"])
    assert 3 <= complaint_count <= 4, \
        f"complaint_queries count ({complaint_count}) must be between 3 and 4"
    
    # Test case 2: workaround_queries bounds (MIN=3, MAX=4)
    workaround_count = len(queries["workaround_queries"])
    assert 3 <= workaround_count <= 4, \
        f"workaround_queries count ({workaround_count}) must be between 3 and 4"
    
    # Test case 3: tool_queries bounds (MIN=2, MAX=3)
    tool_count = len(queries["tool_queries"])
    assert 2 <= tool_count <= 3, \
        f"tool_queries count ({tool_count}) must be between 2 and 3"
    
    # Test case 4: blog_queries bounds (MIN=2, MAX=3)
    blog_count = len(queries["blog_queries"])
    assert 2 <= blog_count <= 3, \
        f"blog_queries count ({blog_count}) must be between 2 and 3"
    
    print("✓ Bucket bounds tests passed")


def test_deterministic_behavior():
    """Test that query generation is deterministic across runs"""
    print("\nTesting deterministic behavior...")
    
    problem = "managing spreadsheets"
    
    # Generate queries multiple times
    result1 = generate_search_queries(problem)
    result2 = generate_search_queries(problem)
    result3 = generate_search_queries(problem)
    
    # All results should be identical
    assert result1 == result2, "Query generation must be deterministic (run 1 vs 2)"
    assert result2 == result3, "Query generation must be deterministic (run 2 vs 3)"
    assert result1 == result3, "Query generation must be deterministic (run 1 vs 3)"
    
    # Check each bucket individually
    assert result1["complaint_queries"] == result2["complaint_queries"], \
        "Complaint queries must be deterministic"
    assert result1["workaround_queries"] == result2["workaround_queries"], \
        "Workaround queries must be deterministic"
    assert result1["tool_queries"] == result2["tool_queries"], \
        "Tool queries must be deterministic"
    assert result1["blog_queries"] == result2["blog_queries"], \
        "Blog queries must be deterministic"
    
    print("✓ Deterministic behavior tests passed")


def test_no_duplicate_queries_within_buckets():
    """Test that there are no duplicate queries within each bucket"""
    print("\nTesting no duplicates within buckets...")
    
    problem = "data entry"
    queries = generate_search_queries(problem)
    
    # Test each bucket for internal duplicates
    for bucket_name, bucket_queries in queries.items():
        unique_queries = set(q.lower() for q in bucket_queries)
        assert len(unique_queries) == len(bucket_queries), \
            f"{bucket_name} contains duplicate queries: {bucket_queries}"
    
    print("✓ No duplicates within buckets tests passed")


def test_normalized_problem_in_queries():
    """Test that normalized problem text is used in queries"""
    print("\nTesting normalized problem in queries...")
    
    # Test with problem that needs normalization
    problem = "Managing Multiple Spreadsheets Daily"
    queries = generate_search_queries(problem)
    
    # All queries should contain the normalized form
    # "Managing" -> "manage", "Spreadsheets" -> "spreadsheet"
    all_queries = (
        queries["complaint_queries"] +
        queries["workaround_queries"] +
        queries["tool_queries"] +
        queries["blog_queries"]
    )
    
    for query in all_queries:
        # All queries should be lowercase (normalized)
        assert query == query.lower(), \
            f"Query should be lowercase (normalized): '{query}'"
        
        # Query should not be empty
        assert len(query) > 0, "Query should not be empty"
        
        # Query should contain at least one word from the normalized problem
        # This verifies that normalization was applied
        normalized = normalize_problem_text(problem)
        normalized_words = set(normalized.split())
        query_words = set(query.split())
        
        # Should have some overlap (query contains normalized problem text)
        overlap = normalized_words & query_words
        assert len(overlap) > 0, \
            f"Query '{query}' should contain words from normalized problem '{normalized}'"
    
    print("✓ Normalized problem in queries tests passed")


def run_all_tests():
    """Run all test suites"""
    print("=" * 60)
    print("Running Query Generation Hardening Test Suite")
    print("=" * 60)
    
    try:
        test_text_normalization()
        test_min_max_bounds_enforcement()
        test_query_deduplication()
        test_bucket_separation()
        test_bucket_bounds()
        test_deterministic_behavior()
        test_no_duplicate_queries_within_buckets()
        test_normalized_problem_in_queries()
        
        print("\n" + "=" * 60)
        print("✓ ALL QUERY GENERATION TESTS PASSED!")
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
