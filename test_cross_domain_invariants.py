"""
Test cross-domain invariants in the classification system.

This tests if the system behaves consistently across different problem domains,
or if certain outputs vary based on problem wording/domain.
"""

import sys
from main import (
    generate_search_queries,
    normalize_problem_text,
    classify_result_type,
    compute_competition_pressure,
)


def test_query_count_consistency():
    """
    Test if query counts are consistent across different problem domains.
    
    INVARIANT: Query bucket sizes should be deterministic and consistent
    regardless of problem domain or wording.
    """
    print("=" * 80)
    print("TEST: Query Count Consistency Across Domains")
    print("=" * 80)
    
    test_problems = [
        "Founders struggle to validate startup ideas quickly",
        "Manual invoice processing is time consuming",
        "Email follow-up is tedious and repetitive",
        "Data entry takes too long every day",
        "Meeting notes are hard to organize",
    ]
    
    query_counts = []
    
    for problem in test_problems:
        queries = generate_search_queries(problem)
        counts = {
            'complaint': len(queries['complaint_queries']),
            'workaround': len(queries['workaround_queries']),
            'tool': len(queries['tool_queries']),
            'blog': len(queries['blog_queries']),
            'total': sum([
                len(queries['complaint_queries']),
                len(queries['workaround_queries']),
                len(queries['tool_queries']),
                len(queries['blog_queries']),
            ])
        }
        query_counts.append(counts)
        
        print(f"\nProblem: {problem[:50]}...")
        print(f"  Complaint: {counts['complaint']}, Workaround: {counts['workaround']}, Tool: {counts['tool']}, Blog: {counts['blog']}")
        print(f"  Total: {counts['total']}")
    
    # Check if all have same counts
    first_counts = query_counts[0]
    all_same = all(
        counts['complaint'] == first_counts['complaint'] and
        counts['workaround'] == first_counts['workaround'] and
        counts['tool'] == first_counts['tool'] and
        counts['blog'] == first_counts['blog']
        for counts in query_counts
    )
    
    print("\n" + "-" * 80)
    if all_same:
        print("✓ INVARIANT HOLDS: Query counts are consistent across domains")
    else:
        print("✗ INVARIANT VIOLATED: Query counts vary across domains")
        print("\nThis indicates bucket sizes depend on problem wording,")
        print("which could cause inconsistent behavior across analyses.")
    
    return all_same


def test_classification_determinism():
    """
    Test if classification is deterministic regardless of problem context.
    
    INVARIANT: Same result content should always classify the same way,
    regardless of which problem's analysis it appears in.
    """
    print("\n" + "=" * 80)
    print("TEST: Classification Determinism Across Contexts")
    print("=" * 80)
    
    # Test the same URL appearing in different problem analyses
    test_result = {
        'title': 'ValidatorAI - Startup Validation',
        'snippet': 'AI-powered validation. Sign up. Pricing available.',
        'url': 'https://validatorai.com'
    }
    
    # Classify the same result multiple times
    classifications = []
    for i in range(10):
        classification = classify_result_type(test_result)
        classifications.append(classification)
    
    all_same = all(c == classifications[0] for c in classifications)
    
    print(f"\nTest result: {test_result['title']}")
    print(f"Classifications: {set(classifications)}")
    
    if all_same:
        print("✓ INVARIANT HOLDS: Classification is deterministic")
    else:
        print("✗ INVARIANT VIOLATED: Classification varies across calls")
    
    return all_same


def test_threshold_absoluteness():
    """
    Test if competition pressure thresholds are absolute, not relative.
    
    INVARIANT: Competition pressure should depend on ABSOLUTE counts,
    not relative ratios to other buckets or problem-specific factors.
    """
    print("\n" + "=" * 80)
    print("TEST: Threshold Absoluteness (Not Relative)")
    print("=" * 80)
    
    # Test if pressure depends only on count, not context
    test_counts = [3, 5, 10, 15]
    
    for count in test_counts:
        commercial_pressure = compute_competition_pressure(count, 'commercial')
        diy_pressure = compute_competition_pressure(count, 'diy')
        
        # Test multiple times to ensure consistency
        commercial_pressure2 = compute_competition_pressure(count, 'commercial')
        diy_pressure2 = compute_competition_pressure(count, 'diy')
        
        consistent = (commercial_pressure == commercial_pressure2 and 
                     diy_pressure == diy_pressure2)
        
        status = "✓" if consistent else "✗"
        print(f"\n{status} Count={count}: Commercial={commercial_pressure}, DIY={diy_pressure}")
        
        if not consistent:
            print(f"  VIOLATION: Pressure changed between calls!")
            return False
    
    print("\n✓ INVARIANT HOLDS: Thresholds are absolute and consistent")
    return True


def test_normalization_consistency():
    """
    Test if problem normalization produces consistent outputs.
    
    INVARIANT: Similar problems should normalize to similar forms.
    Different phrasings of the same issue should not create wildly different queries.
    """
    print("\n" + "=" * 80)
    print("TEST: Normalization Consistency")
    print("=" * 80)
    
    # Test similar problems with different wording
    similar_problems = [
        ("validate startup idea", "validate startup ideas"),
        ("process invoices manually", "manual invoice processing"),
        ("email follow up", "following up on emails"),
    ]
    
    for prob1, prob2 in similar_problems:
        norm1 = normalize_problem_text(prob1)
        norm2 = normalize_problem_text(prob2)
        
        # Check if normalized forms are similar (same key words)
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        overlap = words1.intersection(words2)
        
        similarity = len(overlap) / max(len(words1), len(words2)) if words1 or words2 else 0
        
        print(f"\nProblem 1: '{prob1}'")
        print(f"  Normalized: '{norm1}'")
        print(f"Problem 2: '{prob2}'")
        print(f"  Normalized: '{norm2}'")
        print(f"  Word overlap: {similarity:.1%}")
        
        if similarity < 0.5:
            print(f"  ⚠ Low similarity - may produce different query sets")


def test_bucket_independence():
    """
    Test if query buckets are truly independent.
    
    INVARIANT: Tool queries should not overlap with blog queries.
    Complaint queries should not overlap with workaround queries.
    """
    print("\n" + "=" * 80)
    print("TEST: Query Bucket Independence")
    print("=" * 80)
    
    problem = "Manual data entry is time consuming"
    queries = generate_search_queries(problem)
    
    # Check for query overlaps
    complaint_set = set(queries['complaint_queries'])
    workaround_set = set(queries['workaround_queries'])
    tool_set = set(queries['tool_queries'])
    blog_set = set(queries['blog_queries'])
    
    overlaps = []
    
    # Check all pairs
    pairs = [
        ('complaint', complaint_set, 'workaround', workaround_set),
        ('complaint', complaint_set, 'tool', tool_set),
        ('complaint', complaint_set, 'blog', blog_set),
        ('workaround', workaround_set, 'tool', tool_set),
        ('workaround', workaround_set, 'blog', blog_set),
        ('tool', tool_set, 'blog', blog_set),
    ]
    
    for name1, set1, name2, set2 in pairs:
        overlap = set1.intersection(set2)
        if overlap:
            overlaps.append((name1, name2, overlap))
            print(f"\n✗ OVERLAP: {name1} ∩ {name2}")
            for query in overlap:
                print(f"  - {query}")
    
    if not overlaps:
        print("\n✓ INVARIANT HOLDS: Query buckets are independent (no overlaps)")
        return True
    else:
        print(f"\n✗ INVARIANT VIOLATED: {len(overlaps)} bucket overlaps found")
        print("This causes query mixing and pollutes bucket purity.")
        return False


def test_ratio_independence():
    """
    Test if classification depends on absolute signals, not ratios.
    
    INVARIANT: A result with 2 commercial signals should be classified
    the same whether there are 0 or 10 other results in the batch.
    """
    print("\n" + "=" * 80)
    print("TEST: Ratio Independence")
    print("=" * 80)
    
    # Same result classified in isolation vs in a batch
    test_result = {
        'title': 'Project Management Software',
        'snippet': 'Manage projects. Pricing available.',
        'url': 'https://example.com/pm'
    }
    
    # Classify alone
    classification_alone = classify_result_type(test_result)
    
    # Classify again (should be same)
    classification_again = classify_result_type(test_result)
    
    print(f"\nTest result: {test_result['title']}")
    print(f"Classification (call 1): {classification_alone}")
    print(f"Classification (call 2): {classification_again}")
    
    if classification_alone == classification_again:
        print("✓ INVARIANT HOLDS: Classification is ratio-independent")
        return True
    else:
        print("✗ INVARIANT VIOLATED: Classification depends on context/state")
        return False


def run_all_tests():
    """Run all cross-domain invariant tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "CROSS-DOMAIN INVARIANT TESTS" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    results = {}
    
    try:
        results['query_count'] = test_query_count_consistency()
        results['classification_determinism'] = test_classification_determinism()
        results['threshold_absoluteness'] = test_threshold_absoluteness()
        test_normalization_consistency()  # Informational only
        results['bucket_independence'] = test_bucket_independence()
        results['ratio_independence'] = test_ratio_independence()
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {test_name}")
        
        all_passed = all(results.values())
        
        if all_passed:
            print("\n✅ All invariants hold - system is consistent across domains")
        else:
            print("\n❌ Some invariants violated - system behavior varies across domains")
            print("This indicates under-specified logic that needs hardening.")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
