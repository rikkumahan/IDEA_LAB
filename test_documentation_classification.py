#!/usr/bin/env python3
"""
COMPREHENSIVE TEST: Documentation and Guide Classification Fix

This test verifies that the CROSS-PROBLEM INVARIANT is enforced:

    INVARIANT: Documentation ≠ Commercial Competitor
    
    A page is COMMERCIAL only if ALL of:
    1. First-party product/SaaS site
    2. Directly offers acquisition (pricing/signup/purchase)
    3. NOT primarily documentation/explanation/instruction
    
    Documentation pages explain HOW TO USE products, they don't SELL them.
    
This invariant MUST hold across ALL problem domains:
- Founder startup idea validation
- Jira ticket automation
- Data processing automation
- ANY other problem domain

FAILURE MODE: If ANY documentation page is classified as commercial,
the ENTIRE fix is INCOMPLETE.
"""

import sys
from main import classify_result_type

def test_documentation_invariant():
    """
    Test the core invariant: Documentation pages MUST NOT be commercial.
    
    This tests various documentation patterns that were being misclassified.
    """
    print("=" * 80)
    print("TEST 1: DOCUMENTATION INVARIANT")
    print("=" * 80)
    print("\nINVARIANT: Documentation ≠ Commercial Competitor")
    print("\nDocumentation pages explain products, they don't sell them.")
    print("This must hold regardless of domain or product.\n")
    
    documentation_cases = [
        # Product documentation sites (docs subdomain)
        {
            'name': 'Oracle Database Documentation',
            'result': {
                'title': 'Oracle Database Documentation - Getting Started',
                'snippet': 'Learn how to use Oracle Database. Complete reference guide with enterprise features.',
                'url': 'https://docs.oracle.com/database/getting-started'
            }
        },
        {
            'name': 'GitHub Actions Documentation',
            'result': {
                'title': 'GitHub Actions Documentation',
                'snippet': 'Documentation for GitHub Actions. Get started with workflows.',
                'url': 'https://docs.github.com/actions'
            }
        },
        {
            'name': 'Jira Automation Documentation',
            'result': {
                'title': 'Jira Automation Documentation',
                'snippet': 'Learn how to automate Jira. Documentation for Jira automation rules.',
                'url': 'https://support.atlassian.com/jira/docs/automation'
            }
        },
        {
            'name': 'AWS Documentation',
            'result': {
                'title': 'AWS Lambda Documentation',
                'snippet': 'AWS Lambda documentation. Learn how to use Lambda functions.',
                'url': 'https://docs.aws.amazon.com/lambda/'
            }
        },
        # Support/help pages with documentation
        {
            'name': 'Salesforce Help Documentation',
            'result': {
                'title': 'Salesforce Help & Documentation',
                'snippet': 'Get help with Salesforce. Complete documentation and guides.',
                'url': 'https://help.salesforce.com/documentation'
            }
        },
        # Tutorial pages
        {
            'name': 'Tutorial: Building Apps',
            'result': {
                'title': 'Tutorial: Building Web Applications',
                'snippet': 'A complete tutorial on building web apps. Step-by-step guide.',
                'url': 'https://example.com/tutorials/web-apps'
            }
        },
        # Introductory guides
        {
            'name': 'Introduction to Data Science',
            'result': {
                'title': 'Introduction to Data Science',
                'snippet': 'An introductory guide to data science. Learn the fundamentals.',
                'url': 'https://example.com/intro-data-science'
            }
        },
        {
            'name': 'Getting Started with API',
            'result': {
                'title': 'Getting Started with Our API',
                'snippet': 'Getting started guide for developers. API documentation and examples.',
                'url': 'https://api.example.com/docs/getting-started'
            }
        },
        # User guides
        {
            'name': 'User Guide for CRM',
            'result': {
                'title': 'User Guide: CRM Software',
                'snippet': 'Complete user guide for our CRM. Learn how to manage contacts.',
                'url': 'https://example.com/help/user-guide'
            }
        },
        # Reference documentation
        {
            'name': 'API Reference',
            'result': {
                'title': 'API Reference Guide',
                'snippet': 'Complete API reference documentation. All endpoints and parameters.',
                'url': 'https://api.example.com/reference'
            }
        }
    ]
    
    all_passed = True
    failed_cases = []
    
    for case in documentation_cases:
        classification = classify_result_type(case['result'])
        is_correct = classification != 'commercial'
        status = "✓" if is_correct else "✗"
        
        print(f"{status} {case['name']:40s} → {classification}")
        
        if not is_correct:
            all_passed = False
            failed_cases.append(case['name'])
            print(f"   ERROR: Documentation classified as COMMERCIAL!")
            print(f"   URL: {case['result']['url']}")
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ DOCUMENTATION INVARIANT PASSED")
        print("All documentation pages correctly classified as non-commercial.")
    else:
        print("❌ DOCUMENTATION INVARIANT FAILED")
        print(f"Failed cases: {failed_cases}")
    print("=" * 80)
    
    return all_passed


def test_seller_vs_explainer():
    """
    Test ISSUE 2: Seller vs Explainer confusion
    
    Pages that EXPLAIN products should not be classified as SELLING them.
    """
    print("\n" + "=" * 80)
    print("TEST 2: SELLER VS EXPLAINER")
    print("=" * 80)
    print("\nRULE: Talking about a solution ≠ Selling the solution")
    print("Explainer pages (blogs, tutorials, guides) are NOT competitors.\n")
    
    explainer_cases = [
        {
            'name': 'Medium article explaining tools',
            'result': {
                'title': 'How to Choose the Right CRM | Medium',
                'snippet': 'Tools like Salesforce have great pricing. Sign up and try them.',
                'url': 'https://medium.com/@author/choose-crm'
            },
            'expected': 'content'
        },
        {
            'name': 'Blog post about automation',
            'result': {
                'title': 'Best Automation Tools for 2024',
                'snippet': 'Explore tools like Zapier. Pricing starts at $20/month.',
                'url': 'https://blog.example.com/automation-tools'
            },
            'expected': 'content'
        },
        {
            'name': 'Tutorial mentioning products',
            'result': {
                'title': 'Tutorial: Automating Jira Tickets',
                'snippet': 'Use Jira automation. Sign up for Jira and get started.',
                'url': 'https://example.com/tutorial/jira-automation'
            },
            'expected': 'content'
        }
    ]
    
    all_passed = True
    for case in explainer_cases:
        classification = classify_result_type(case['result'])
        is_correct = classification == case['expected']
        status = "✓" if is_correct else "✗"
        
        print(f"{status} {case['name']:40s} → {classification}")
        
        if not is_correct:
            all_passed = False
            print(f"   ERROR: Expected '{case['expected']}', got '{classification}'")
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ SELLER VS EXPLAINER TEST PASSED")
    else:
        print("❌ SELLER VS EXPLAINER TEST FAILED")
    print("=" * 80)
    
    return all_passed


def test_cross_problem_consistency():
    """
    Test ISSUE 3: Cross-problem consistency
    
    The same classification logic should work consistently across different
    problem domains:
    - Founder startup idea validation
    - Jira ticket automation
    - Data processing
    """
    print("\n" + "=" * 80)
    print("TEST 3: CROSS-PROBLEM CONSISTENCY")
    print("=" * 80)
    print("\nINVARIANT: Classification rules must be consistent across all domains.")
    print("Similar content should classify the same way regardless of topic.\n")
    
    # Test across different domains
    domains = {
        'Founder Validation': [
            {
                'name': 'ValidatorAI (product)',
                'result': {
                    'title': 'ValidatorAI - Startup Validation',
                    'snippet': 'Sign up for AI validation. Pricing from $29/month.',
                    'url': 'https://validatorai.com'
                },
                'expected': 'commercial'
            },
            {
                'name': 'Medium blog about validation',
                'result': {
                    'title': 'How to Validate Ideas | Medium',
                    'snippet': 'Tools like ValidatorAI can help. Check pricing.',
                    'url': 'https://medium.com/@author/validate'
                },
                'expected': 'content'
            }
        ],
        'Jira Automation': [
            {
                'name': 'Jira product page',
                'result': {
                    'title': 'Jira Software - Atlassian',
                    'snippet': 'Sign up for Jira. View pricing plans. Get started.',
                    'url': 'https://www.atlassian.com/software/jira'
                },
                'expected': 'commercial'
            },
            {
                'name': 'Jira documentation',
                'result': {
                    'title': 'Jira Automation Documentation',
                    'snippet': 'Learn how to automate Jira. Complete documentation.',
                    'url': 'https://support.atlassian.com/jira/docs/'
                },
                'expected': 'content'
            }
        ],
        'Data Processing': [
            {
                'name': 'DataProcessor (product)',
                'result': {
                    'title': 'DataProcessor - Automated Processing',
                    'snippet': 'Start free trial. View pricing. Enterprise available.',
                    'url': 'https://dataprocessor.io'
                },
                'expected': 'commercial'
            },
            {
                'name': 'Data processing tutorial',
                'result': {
                    'title': 'Tutorial: Data Processing Best Practices',
                    'snippet': 'Learn how to process data efficiently. Tools and techniques.',
                    'url': 'https://example.com/tutorials/data-processing'
                },
                'expected': 'content'
            }
        ]
    }
    
    all_passed = True
    for domain, cases in domains.items():
        print(f"\nDomain: {domain}")
        print("-" * 80)
        
        for case in cases:
            classification = classify_result_type(case['result'])
            is_correct = classification == case['expected']
            status = "✓" if is_correct else "✗"
            
            print(f"  {status} {case['name']:35s} → {classification:12s} (expected: {case['expected']})")
            
            if not is_correct:
                all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ CROSS-PROBLEM CONSISTENCY PASSED")
        print("Classification is consistent across all domains.")
    else:
        print("❌ CROSS-PROBLEM CONSISTENCY FAILED")
    print("=" * 80)
    
    return all_passed


def test_commercial_competitor_counts():
    """
    Test that commercial competitor counts are accurate after the fix.
    
    This simulates what happens in actual usage - we run searches and
    count commercial competitors, making sure documentation is excluded.
    """
    print("\n" + "=" * 80)
    print("TEST 4: COMMERCIAL COMPETITOR COUNT ACCURACY")
    print("=" * 80)
    print("\nTest that documentation pages don't inflate commercial counts.\n")
    
    # Simulate search results that include documentation
    mixed_results = [
        # Real commercial competitors (should be counted)
        {
            'title': 'ValidatorAI - Startup Validation',
            'snippet': 'Sign up for AI validation. Pricing from $29/month.',
            'url': 'https://validatorai.com'
        },
        {
            'title': 'IdeaBrowser - Startup Ideas',
            'snippet': 'Browse validated ideas. Free trial. View pricing.',
            'url': 'https://ideabrowser.io'
        },
        # Documentation (should NOT be counted)
        {
            'title': 'Startup Validation Documentation',
            'snippet': 'Learn how to validate startups. Complete guide.',
            'url': 'https://docs.example.com/validation'
        },
        {
            'title': 'Jira Automation Documentation',
            'snippet': 'Jira automation docs. Get started guide.',
            'url': 'https://support.atlassian.com/jira/docs/'
        },
        # Blogs (should NOT be counted)
        {
            'title': 'Best Validation Tools | Medium',
            'snippet': 'Tools like ValidatorAI. Check pricing and features.',
            'url': 'https://medium.com/@author/validation-tools'
        },
        {
            'title': 'Ultimate Guide to Startup Validation',
            'snippet': 'Complete guide with tool comparisons and pricing.',
            'url': 'https://blog.example.com/validation-guide'
        },
    ]
    
    commercial_count = 0
    non_commercial_count = 0
    
    print("Classifying search results:")
    print("-" * 80)
    
    for result in mixed_results:
        classification = classify_result_type(result)
        symbol = "💰" if classification == 'commercial' else "📄"
        
        print(f"{symbol} {classification:12s} | {result['title'][:50]}")
        
        if classification == 'commercial':
            commercial_count += 1
        else:
            non_commercial_count += 1
    
    print("\n" + "-" * 80)
    print(f"Commercial competitors: {commercial_count}")
    print(f"Non-commercial content: {non_commercial_count}")
    
    # Expected: 2 commercial (ValidatorAI, IdeaBrowser)
    # Expected: 4 non-commercial (2 docs + 2 blogs)
    expected_commercial = 2
    expected_non_commercial = 4
    
    counts_correct = (
        commercial_count == expected_commercial and 
        non_commercial_count == expected_non_commercial
    )
    
    print("\n" + "=" * 80)
    if counts_correct:
        print("✅ COMMERCIAL COUNTS ACCURATE")
        print(f"Documentation and blogs correctly excluded from commercial count.")
    else:
        print("❌ COMMERCIAL COUNTS INCORRECT")
        print(f"Expected {expected_commercial} commercial, {expected_non_commercial} non-commercial")
        print(f"Got {commercial_count} commercial, {non_commercial_count} non-commercial")
    print("=" * 80)
    
    return counts_correct


def main():
    """Run all tests and generate summary report"""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST: DOCUMENTATION CLASSIFICATION FIX")
    print("=" * 80)
    print("\nThis test verifies the fix for ISSUE 1, ISSUE 2, and ISSUE 3:")
    print("  ISSUE 1: Documentation misclassified as competitors")
    print("  ISSUE 2: Seller vs Explainer confusion")
    print("  ISSUE 3: Cross-problem inconsistency")
    print("\n" + "=" * 80)
    
    # Run all tests
    test1_passed = test_documentation_invariant()
    test2_passed = test_seller_vs_explainer()
    test3_passed = test_cross_problem_consistency()
    test4_passed = test_commercial_competitor_counts()
    
    # Generate summary
    all_passed = test1_passed and test2_passed and test3_passed and test4_passed
    
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    tests = [
        ("Documentation Invariant", test1_passed),
        ("Seller vs Explainer", test2_passed),
        ("Cross-Problem Consistency", test3_passed),
        ("Commercial Count Accuracy", test4_passed),
    ]
    
    for test_name, passed in tests:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:35s} {status}")
    
    print("=" * 80)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED - FIX IS COMPLETE")
        print("\nCONFIRMATION:")
        print("  ✓ Documentation pages are no longer classified as commercial")
        print("  ✓ Seller vs Explainer distinction is maintained")
        print("  ✓ Classification is consistent across problem domains")
        print("  ✓ Commercial competitor counts are accurate")
        print("\nINVARIANT ENFORCED: Documentation ≠ Commercial Competitor")
        print("=" * 80)
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - FIX IS INCOMPLETE")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
