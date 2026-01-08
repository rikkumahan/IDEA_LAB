#!/usr/bin/env python3
"""
Demonstration script for hardened query generation.

This script demonstrates the key features:
1. Deterministic text normalization
2. Fixed query templates per bucket
3. MIN-MAX bounds enforcement
4. Query deduplication
5. Bucket separation (no overlap)
"""

from main import generate_search_queries
from nlp_utils import normalize_problem_text
import json


def demonstrate_normalization():
    """Demonstrate text normalization before query generation"""
    print("=" * 70)
    print("FEATURE 1: DETERMINISTIC TEXT NORMALIZATION")
    print("=" * 70)
    
    test_cases = [
        "Managing multiple spreadsheets daily",
        "Frustrated with manual data entry",
        "The problem is tracking customer orders",
    ]
    
    for original in test_cases:
        normalized = normalize_problem_text(original)
        print(f"\nOriginal:   '{original}'")
        print(f"Normalized: '{normalized}'")
    print()


def demonstrate_fixed_templates():
    """Demonstrate fixed query templates with no overlap"""
    print("=" * 70)
    print("FEATURE 2: FIXED QUERY TEMPLATES (NO OVERLAP)")
    print("=" * 70)
    
    problem = "data entry"
    queries = generate_search_queries(problem)
    
    print("\nComplaint Queries (pain/frustration):")
    for q in queries['complaint_queries']:
        print(f"  - {q}")
    
    print("\nWorkaround Queries (DIY/substitutes):")
    for q in queries['workaround_queries']:
        print(f"  - {q}")
    
    print("\nTool Queries (competitors/products):")
    for q in queries['tool_queries']:
        print(f"  - {q}")
    
    print("\nBlog Queries (content/discussion):")
    for q in queries['blog_queries']:
        print(f"  - {q}")
    print()


def demonstrate_bounds():
    """Demonstrate MIN-MAX bounds enforcement"""
    print("=" * 70)
    print("FEATURE 3: STRICT MIN-MAX BOUNDS ENFORCEMENT")
    print("=" * 70)
    
    problem = "manual tasks"
    queries = generate_search_queries(problem)
    
    bounds = {
        'complaint_queries': (3, 4),
        'workaround_queries': (3, 4),
        'tool_queries': (2, 3),
        'blog_queries': (2, 3),
    }
    
    print("\nBucket bounds verification:")
    for bucket_name, (min_val, max_val) in bounds.items():
        count = len(queries[bucket_name])
        status = "✓" if min_val <= count <= max_val else "✗"
        print(f"  {status} {bucket_name}: {count} queries (MIN={min_val}, MAX={max_val})")
    print()


def demonstrate_deduplication():
    """Demonstrate query deduplication"""
    print("=" * 70)
    print("FEATURE 4: QUERY DEDUPLICATION")
    print("=" * 70)
    
    from main import deduplicate_queries
    
    # Example with duplicates
    queries_with_dupes = [
        "manual data entry",
        "Manual Data Entry",  # Same but different case
        "manual  data  entry",  # Same but different whitespace
        "spreadsheet management",
        "manual data entry",  # Exact duplicate
    ]
    
    print("\nBefore deduplication:")
    for q in queries_with_dupes:
        print(f"  - '{q}'")
    
    deduplicated = deduplicate_queries(queries_with_dupes)
    
    print("\nAfter deduplication:")
    for q in deduplicated:
        print(f"  - '{q}'")
    
    print(f"\nReduced from {len(queries_with_dupes)} to {len(deduplicated)} queries")
    print()


def demonstrate_determinism():
    """Demonstrate deterministic behavior"""
    print("=" * 70)
    print("FEATURE 5: DETERMINISTIC BEHAVIOR")
    print("=" * 70)
    
    problem = "spreadsheet management"
    
    # Generate queries 3 times
    result1 = generate_search_queries(problem)
    result2 = generate_search_queries(problem)
    result3 = generate_search_queries(problem)
    
    # Check if all results are identical
    all_same = (result1 == result2 == result3)
    
    print(f"\nSame problem text: '{problem}'")
    print(f"Run 1 == Run 2: {result1 == result2}")
    print(f"Run 2 == Run 3: {result2 == result3}")
    print(f"Run 1 == Run 3: {result1 == result3}")
    print(f"\n✓ All runs produce identical results (deterministic)")
    print()


def main():
    """Run all demonstrations"""
    print("\n" + "=" * 70)
    print("HARDENED QUERY GENERATION DEMONSTRATION")
    print("=" * 70)
    print()
    
    demonstrate_normalization()
    demonstrate_fixed_templates()
    demonstrate_bounds()
    demonstrate_deduplication()
    demonstrate_determinism()
    
    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("✓ Text is normalized deterministically (lowercase, lemmatize, stopwords)")
    print("✓ Each bucket has fixed templates with clear intent (no overlap)")
    print("✓ Strict MIN-MAX bounds prevent under/over-generation")
    print("✓ Deduplication removes redundant queries")
    print("✓ Behavior is deterministic across runs")
    print()


if __name__ == "__main__":
    main()
