"""
Test suite for data aggregation and deduplication.

Tests URL normalization to prevent inflated signal counts from:
- URL variations (http vs https, trailing slashes, parameters)
- Cross-query duplicates within a bucket
- Proper deduplication ordering

All tests verify deterministic behavior (no ML, no probabilistic logic).
"""

import sys
from main import normalize_url, deduplicate_results


def test_url_normalization_basic():
    """Test basic URL normalization"""
    print("Testing basic URL normalization...")
    
    # Test case 1: HTTPS normalization
    assert normalize_url("http://example.com/page") == "https://example.com/page"
    assert normalize_url("https://example.com/page") == "https://example.com/page"
    
    # Test case 2: Lowercase domain
    assert normalize_url("https://Example.COM/page") == "https://example.com/page"
    assert normalize_url("https://EXAMPLE.com/Page") == "https://example.com/Page"  # Path case preserved
    
    # Test case 3: Trailing slash removal
    assert normalize_url("https://example.com/page/") == "https://example.com/page"
    assert normalize_url("https://example.com/page") == "https://example.com/page"
    assert normalize_url("https://example.com/") == "https://example.com/"  # Root path preserved
    
    # Test case 4: Fragment removal
    assert normalize_url("https://example.com/page#section1") == "https://example.com/page"
    assert normalize_url("https://example.com/page#") == "https://example.com/page"
    
    # Test case 5: Empty/invalid URLs
    assert normalize_url("") is None
    assert normalize_url(None) is None
    assert normalize_url("not-a-url") is None
    
    print("✓ Basic URL normalization tests passed")


def test_url_normalization_tracking_parameters():
    """Test removal of tracking parameters"""
    print("\nTesting tracking parameter removal...")
    
    base_url = "https://example.com/page"
    
    # Test case 1: Google Analytics parameters
    assert normalize_url(f"{base_url}?utm_source=twitter") == base_url
    assert normalize_url(f"{base_url}?utm_medium=social") == base_url
    assert normalize_url(f"{base_url}?utm_campaign=spring") == base_url
    assert normalize_url(f"{base_url}?utm_term=keyword") == base_url
    assert normalize_url(f"{base_url}?utm_content=banner") == base_url
    assert normalize_url(f"{base_url}?_ga=1.234567") == base_url
    assert normalize_url(f"{base_url}?_gid=1.234567") == base_url
    
    # Test case 2: Facebook parameters
    assert normalize_url(f"{base_url}?fbclid=IwAR123") == base_url
    assert normalize_url(f"{base_url}?fb_action_ids=123") == base_url
    assert normalize_url(f"{base_url}?fb_source=share") == base_url
    
    # Test case 3: Microsoft/Bing parameters
    assert normalize_url(f"{base_url}?msclkid=abc123") == base_url
    assert normalize_url(f"{base_url}?mc_cid=campaign123") == base_url
    
    # Test case 4: Generic tracking parameters
    assert normalize_url(f"{base_url}?ref=homepage") == base_url
    assert normalize_url(f"{base_url}?source=newsletter") == base_url
    assert normalize_url(f"{base_url}?campaign=email") == base_url
    
    # Test case 5: Multiple tracking parameters
    assert normalize_url(f"{base_url}?utm_source=google&fbclid=123&ref=link") == base_url
    
    print("✓ Tracking parameter removal tests passed")


def test_url_normalization_preserved_parameters():
    """Test that non-tracking parameters are preserved"""
    print("\nTesting preservation of content parameters...")
    
    # Test case 1: Query parameters preserved (sorted)
    url1 = normalize_url("https://example.com/search?q=test&page=2")
    assert "q=test" in url1
    assert "page=2" in url1
    
    # Test case 2: Parameter order normalized (sorted alphabetically)
    url2 = normalize_url("https://example.com/search?page=2&q=test")
    url3 = normalize_url("https://example.com/search?q=test&page=2")
    assert url2 == url3, "Parameter order should be normalized"
    
    # Test case 3: Tracking parameters removed, content parameters kept
    url4 = normalize_url("https://example.com/search?q=test&utm_source=google&page=2")
    assert "q=test" in url4
    assert "page=2" in url4
    assert "utm_source" not in url4
    
    # Test case 4: Special characters in parameters
    # parse_qs decodes URL encoding, and we re-encode with quote()
    url5 = normalize_url("https://example.com/search?q=hello+world")
    # After normalization, space should be encoded as %20
    assert "q=hello%20world" in url5, f"Expected encoded space, got: {url5}"
    
    print("✓ Content parameter preservation tests passed")


def test_url_normalization_localhost():
    """Test localhost/IP addresses keep HTTP scheme"""
    print("\nTesting localhost/IP handling...")
    
    # Test case 1: Localhost keeps http
    assert normalize_url("http://localhost:8080/page") == "http://localhost:8080/page"
    assert normalize_url("https://localhost:8080/page") == "https://localhost:8080/page"
    
    # Test case 2: 127.0.0.1 keeps http
    assert normalize_url("http://127.0.0.1:8080/page") == "http://127.0.0.1:8080/page"
    
    # Test case 3: Private IPs keep http (192.168.x.x)
    assert normalize_url("http://192.168.1.1/page") == "http://192.168.1.1/page"
    assert normalize_url("http://192.168.1.1:8080/page") == "http://192.168.1.1:8080/page"
    
    # Test case 4: Private IPs keep http (10.x.x.x)
    assert normalize_url("http://10.0.0.1/page") == "http://10.0.0.1/page"
    assert normalize_url("http://10.1.2.3:3000/page") == "http://10.1.2.3:3000/page"
    
    # Test case 5: Private IPs keep http (172.16-31.x.x)
    assert normalize_url("http://172.16.0.1/page") == "http://172.16.0.1/page"
    assert normalize_url("http://172.31.255.255/page") == "http://172.31.255.255/page"
    assert normalize_url("http://172.20.0.1:8080/page") == "http://172.20.0.1:8080/page"
    
    # Test case 6: Public IP gets https
    assert normalize_url("http://8.8.8.8/page") == "https://8.8.8.8/page"
    
    print("✓ Localhost/IP handling tests passed")


def test_url_normalization_edge_cases():
    """Test edge cases and special scenarios"""
    print("\nTesting edge cases...")
    
    # Test case 1: URL with port
    assert normalize_url("https://example.com:443/page") == "https://example.com:443/page"
    assert normalize_url("http://example.com:8080/page") == "https://example.com:8080/page"
    
    # Test case 2: URL with subdomain
    assert normalize_url("https://www.example.com/page") == "https://www.example.com/page"
    assert normalize_url("https://blog.example.com/page") == "https://blog.example.com/page"
    
    # Test case 3: Deep paths
    assert normalize_url("https://example.com/a/b/c/d") == "https://example.com/a/b/c/d"
    assert normalize_url("https://example.com/a/b/c/d/") == "https://example.com/a/b/c/d"
    
    # Test case 4: URLs with username/password (rarely used)
    url_with_auth = normalize_url("https://user:pass@example.com/page")
    assert url_with_auth is not None  # Should still parse
    
    # Test case 5: Very long URLs
    long_path = "/a" * 100
    long_url = f"https://example.com{long_path}"
    assert normalize_url(long_url) == long_url
    
    # Test case 6: Root path should be '/'
    assert normalize_url("https://example.com") == "https://example.com/"
    assert normalize_url("https://example.com/") == "https://example.com/"
    
    # Test case 7: Special characters in query parameters are encoded
    url_special = normalize_url("https://example.com/page?name=John Doe")
    assert "name=John%20Doe" in url_special, f"Expected encoded space, got: {url_special}"
    
    # Test case 8: Malformed IP-like hostnames (should force HTTPS)
    assert normalize_url("http://172.abc.1.1/page") == "https://172.abc.1.1/page"
    assert normalize_url("http://172.invalid/page") == "https://172.invalid/page"
    
    print("✓ Edge case tests passed")


def test_deduplication_with_variations():
    """Test deduplication catches URL variations"""
    print("\nTesting deduplication with URL variations...")
    
    # Same content, different URL forms
    results = [
        {'url': 'https://example.com/page', 'title': 'Test 1', 'snippet': 'Content 1'},
        {'url': 'https://example.com/page?utm_source=twitter', 'title': 'Test 2', 'snippet': 'Content 2'},
        {'url': 'http://example.com/page', 'title': 'Test 3', 'snippet': 'Content 3'},
        {'url': 'https://example.com/page#section1', 'title': 'Test 4', 'snippet': 'Content 4'},
        {'url': 'https://example.com/page/', 'title': 'Test 5', 'snippet': 'Content 5'},
    ]
    
    deduplicated = deduplicate_results(results)
    
    # Should deduplicate to 1 result (all are same canonical URL)
    assert len(deduplicated) == 1, f"Expected 1 result, got {len(deduplicated)}"
    
    # Should keep the first occurrence
    assert deduplicated[0]['title'] == 'Test 1'
    
    print("✓ Deduplication with variations test passed")


def test_deduplication_preserves_unique():
    """Test deduplication preserves actually unique URLs"""
    print("\nTesting deduplication preserves unique URLs...")
    
    results = [
        {'url': 'https://example.com/page1', 'title': 'Page 1'},
        {'url': 'https://example.com/page2', 'title': 'Page 2'},
        {'url': 'https://example.com/page3', 'title': 'Page 3'},
        {'url': 'https://different.com/page', 'title': 'Different domain'},
        {'url': 'https://example.com/page1?id=123', 'title': 'Page 1 with param'},
    ]
    
    deduplicated = deduplicate_results(results)
    
    # All URLs are unique (different paths or domains or meaningful params)
    assert len(deduplicated) == 5, f"Expected 5 unique results, got {len(deduplicated)}"
    
    print("✓ Unique URL preservation test passed")


def test_deduplication_order_preserved():
    """Test deduplication keeps first occurrence"""
    print("\nTesting deduplication order...")
    
    results = [
        {'url': 'https://example.com/page', 'title': 'First', 'snippet': 'A'},
        {'url': 'https://other.com/page', 'title': 'Different', 'snippet': 'B'},
        {'url': 'https://example.com/page?utm_source=google', 'title': 'Duplicate', 'snippet': 'C'},
        {'url': 'https://example.com/page#section', 'title': 'Also Duplicate', 'snippet': 'D'},
    ]
    
    deduplicated = deduplicate_results(results)
    
    # Should have 2 unique URLs
    assert len(deduplicated) == 2
    
    # First should be from index 0
    assert deduplicated[0]['title'] == 'First'
    
    # Second should be from index 1
    assert deduplicated[1]['title'] == 'Different'
    
    print("✓ Deduplication order preservation test passed")


def test_deduplication_handles_invalid_urls():
    """Test deduplication handles invalid/missing URLs gracefully"""
    print("\nTesting invalid URL handling...")
    
    results = [
        {'url': 'https://valid.com/page', 'title': 'Valid'},
        {'url': None, 'title': 'No URL'},
        {'url': '', 'title': 'Empty URL'},
        {'url': 'not-a-url', 'title': 'Invalid'},
        {'url': 'https://valid2.com/page', 'title': 'Valid 2'},
    ]
    
    deduplicated = deduplicate_results(results)
    
    # Should only keep valid URLs
    assert len(deduplicated) == 2
    assert deduplicated[0]['title'] == 'Valid'
    assert deduplicated[1]['title'] == 'Valid 2'
    
    print("✓ Invalid URL handling test passed")


def test_cross_query_deduplication():
    """Test that duplicates from multiple queries in same bucket are caught"""
    print("\nTesting cross-query deduplication...")
    
    # Simulate results from 3 different queries in complaint bucket
    query1_results = [
        {'url': 'https://example.com/article1', 'title': 'Article 1'},
        {'url': 'https://example.com/article2', 'title': 'Article 2'},
        {'url': 'https://example.com/article3', 'title': 'Article 3'},
    ]
    
    query2_results = [
        {'url': 'https://example.com/article2?utm_source=google', 'title': 'Article 2 again'},  # Duplicate
        {'url': 'https://example.com/article3/', 'title': 'Article 3 again'},  # Duplicate
        {'url': 'https://example.com/article4', 'title': 'Article 4'},
    ]
    
    query3_results = [
        {'url': 'https://example.com/article3#intro', 'title': 'Article 3 third time'},  # Duplicate
        {'url': 'https://example.com/article5', 'title': 'Article 5'},
        {'url': 'https://example.com/article6', 'title': 'Article 6'},
    ]
    
    # Simulate run_multiple_searches() aggregation
    all_results = []
    all_results.extend(query1_results)
    all_results.extend(query2_results)
    all_results.extend(query3_results)
    
    # Now deduplicate
    deduplicated = deduplicate_results(all_results)
    
    # Should have 6 unique articles (article1-6)
    assert len(deduplicated) == 6, f"Expected 6 unique articles, got {len(deduplicated)}"
    
    # Verify order: first occurrence of each kept
    titles = [r['title'] for r in deduplicated]
    assert titles[0] == 'Article 1'
    assert titles[1] == 'Article 2'
    assert titles[2] == 'Article 3'
    assert titles[3] == 'Article 4'
    assert titles[4] == 'Article 5'
    assert titles[5] == 'Article 6'
    
    print("✓ Cross-query deduplication test passed")


def test_deterministic_behavior():
    """Test that normalization is deterministic"""
    print("\nTesting deterministic behavior...")
    
    # Same input should always produce same output
    url = "https://Example.COM/page?utm_source=google&ref=link&id=123#section"
    
    result1 = normalize_url(url)
    result2 = normalize_url(url)
    result3 = normalize_url(url)
    
    assert result1 == result2
    assert result2 == result3
    
    # Deduplication should also be deterministic
    results = [
        {'url': 'https://example.com/page', 'title': 'Test 1'},
        {'url': 'https://example.com/page?utm_source=twitter', 'title': 'Test 2'},
        {'url': 'http://example.com/page', 'title': 'Test 3'},
    ]
    
    dedup1 = deduplicate_results(results.copy())
    dedup2 = deduplicate_results(results.copy())
    
    assert len(dedup1) == len(dedup2)
    assert dedup1[0]['title'] == dedup2[0]['title']
    
    print("✓ Deterministic behavior tests passed")


def test_parameter_sorting():
    """Test that URL parameters are sorted for consistency"""
    print("\nTesting parameter sorting...")
    
    # Same parameters, different order
    url1 = normalize_url("https://example.com/page?z=1&a=2&m=3")
    url2 = normalize_url("https://example.com/page?a=2&m=3&z=1")
    url3 = normalize_url("https://example.com/page?m=3&z=1&a=2")
    
    # All should normalize to same URL (alphabetically sorted)
    assert url1 == url2
    assert url2 == url3
    
    # Verify alphabetical order
    assert "a=" in url1
    assert "m=" in url1
    assert "z=" in url1
    # 'a' should come before 'm' in the string
    assert url1.index("a=") < url1.index("m=")
    assert url1.index("m=") < url1.index("z=")
    
    print("✓ Parameter sorting tests passed")


def run_all_tests():
    """Run all test suites"""
    print("=" * 60)
    print("Running Data Aggregation Test Suite")
    print("=" * 60)
    
    try:
        test_url_normalization_basic()
        test_url_normalization_tracking_parameters()
        test_url_normalization_preserved_parameters()
        test_url_normalization_localhost()
        test_url_normalization_edge_cases()
        test_deduplication_with_variations()
        test_deduplication_preserves_unique()
        test_deduplication_order_preserved()
        test_deduplication_handles_invalid_urls()
        test_cross_query_deduplication()
        test_deterministic_behavior()
        test_parameter_sorting()
        
        print("\n" + "=" * 60)
        print("✓ ALL AGGREGATION TESTS PASSED!")
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
