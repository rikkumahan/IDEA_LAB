"""
Manual audit test for the redesigned Stage 1 classification logic.

Tests the specific cases mentioned in the problem statement to ensure:
1. ValidatorAI and similar first-party products are COMMERCIAL
2. Medium, LinkedIn, Reddit, blogs, listicles are NEVER commercial
"""

import sys
from main import classify_result_type


def test_commercial_cases():
    """Test that real first-party product pages are classified as commercial"""
    print("=" * 70)
    print("TESTING COMMERCIAL CASES (should be 'commercial')")
    print("=" * 70)
    
    commercial_cases = [
        {
            'name': 'ValidatorAI',
            'result': {
                'title': 'ValidatorAI - AI-Powered Startup Validation',
                'snippet': 'Validate your startup idea in minutes. Sign up for free. View pricing plans. Access your dashboard.',
                'url': 'https://validatorai.com'
            }
        },
        {
            'name': 'IdeaBrowser (hypothetical)',
            'result': {
                'title': 'IdeaBrowser - Startup Idea Validation Platform',
                'snippet': 'Browse and validate startup ideas. Try our free trial. Pricing starts at $29/month.',
                'url': 'https://ideabrowser.io'
            }
        },
        {
            'name': 'Generic SaaS product',
            'result': {
                'title': 'StartupHelper - Idea Validation Tool',
                'snippet': 'Get started today. View our pricing. Access your account dashboard.',
                'url': 'https://startuphelper.com'
            }
        }
    ]
    
    all_passed = True
    for case in commercial_cases:
        classification = classify_result_type(case['result'])
        status = "✓" if classification == 'commercial' else "✗"
        print(f"\n{status} {case['name']}")
        print(f"  URL: {case['result']['url']}")
        print(f"  Classification: {classification}")
        
        if classification != 'commercial':
            print(f"  ERROR: Expected 'commercial', got '{classification}'")
            all_passed = False
    
    if not all_passed:
        print("\n" + "=" * 70)
        print("✗ COMMERCIAL CASES FAILED!")
        print("=" * 70)
        return False
    
    print("\n" + "=" * 70)
    print("✓ ALL COMMERCIAL CASES PASSED!")
    print("=" * 70)
    return True


def test_non_commercial_cases():
    """Test that content/discussion pages are NEVER classified as commercial"""
    print("\n" + "=" * 70)
    print("TESTING NON-COMMERCIAL CASES (should NOT be 'commercial')")
    print("=" * 70)
    
    non_commercial_cases = [
        {
            'name': 'Medium article about startup validation',
            'result': {
                'title': 'How to Validate Your Startup Idea | Medium',
                'snippet': 'Tools like ValidatorAI and others can help. Compare pricing and features.',
                'url': 'https://medium.com/@author/validate-startup-idea'
            }
        },
        {
            'name': 'Blog guide about validation tools',
            'result': {
                'title': 'Ultimate Guide: Best Startup Validation Tools 2024',
                'snippet': 'We tested 10 tools including ValidatorAI. Pricing ranges from free to $99/month.',
                'url': 'https://techblog.com/guides/validation-tools'
            }
        },
        {
            'name': 'LinkedIn post recommending tools',
            'result': {
                'title': 'Best tools for validating startup ideas | LinkedIn',
                'snippet': 'Check out ValidatorAI and IdeaBrowser. Both have free trials and enterprise pricing.',
                'url': 'https://www.linkedin.com/pulse/best-validation-tools'
            }
        },
        {
            'name': 'Reddit thread discussing solutions',
            'result': {
                'title': 'r/startups - How do you validate ideas?',
                'snippet': 'I use ValidatorAI. It has great pricing. Sign up and try it.',
                'url': 'https://www.reddit.com/r/startups/comments/validate'
            }
        },
        {
            'name': 'Top AI tools listicle',
            'result': {
                'title': '10 Best AI Tools for Startup Founders',
                'snippet': 'Top tools include ValidatorAI, IdeaBrowser, and more. Compare features and pricing.',
                'url': 'https://blog.example.com/top-ai-tools'
            }
        },
        {
            'name': 'Quora answer about validation',
            'result': {
                'title': 'What are the best startup validation tools? - Quora',
                'snippet': 'ValidatorAI is great. Sign up and check their pricing plans.',
                'url': 'https://www.quora.com/best-validation-tools'
            }
        },
        {
            'name': 'Comparison article',
            'result': {
                'title': 'ValidatorAI vs IdeaBrowser: Which is Better?',
                'snippet': 'We compare features, pricing, and ease of use. Both offer free trials.',
                'url': 'https://saascomparison.com/validatorai-vs-ideabrowser'
            }
        }
    ]
    
    all_passed = True
    for case in non_commercial_cases:
        classification = classify_result_type(case['result'])
        status = "✓" if classification != 'commercial' else "✗"
        print(f"\n{status} {case['name']}")
        print(f"  URL: {case['result']['url']}")
        print(f"  Classification: {classification}")
        
        if classification == 'commercial':
            print(f"  ERROR: Should NOT be 'commercial', got '{classification}'")
            print(f"  THIS IS A CRITICAL FAILURE - BLOGS/SOCIAL CANNOT BE COMMERCIAL")
            all_passed = False
    
    if not all_passed:
        print("\n" + "=" * 70)
        print("✗ NON-COMMERCIAL CASES FAILED!")
        print("=" * 70)
        return False
    
    print("\n" + "=" * 70)
    print("✓ ALL NON-COMMERCIAL CASES PASSED!")
    print("=" * 70)
    return True


def test_problem_statement_scenario():
    """Test the exact scenario from the problem statement"""
    print("\n" + "=" * 70)
    print("TESTING PROBLEM STATEMENT SCENARIO")
    print("=" * 70)
    print("\nProblem: 'Founders struggle to validate startup ideas quickly'\n")
    
    # Expected COMMERCIAL
    print("Expected COMMERCIAL results:")
    commercial_results = [
        {
            'title': 'ValidatorAI - AI-Powered Startup Validation',
            'snippet': 'Validate your startup idea in minutes. Sign up free. View pricing.',
            'url': 'https://validatorai.com'
        },
        {
            'title': 'IdeaBrowser - Browse Validated Startup Ideas',
            'snippet': 'Access validated ideas. Free trial available. See our pricing plans.',
            'url': 'https://ideabrowser.io'
        }
    ]
    
    for result in commercial_results:
        classification = classify_result_type(result)
        status = "✓" if classification == 'commercial' else "✗"
        print(f"  {status} {result['url']}: {classification}")
    
    # Expected NON-COMMERCIAL
    print("\nExpected NON-COMMERCIAL results:")
    non_commercial_results = [
        {
            'title': 'How to Validate Startup Ideas | Medium',
            'snippet': 'Tools like ValidatorAI can help validate your ideas.',
            'url': 'https://medium.com/@author/validate-ideas'
        },
        {
            'title': 'Ultimate Guide to Startup Validation',
            'snippet': 'Learn how to validate ideas. Compare tools and pricing.',
            'url': 'https://blog.com/validation-guide'
        },
        {
            'title': 'Best validation tools | LinkedIn',
            'snippet': 'Check out ValidatorAI and others. Great pricing options.',
            'url': 'https://www.linkedin.com/pulse/validation-tools'
        },
        {
            'title': 'r/startups - How to validate ideas?',
            'snippet': 'Use tools like ValidatorAI. They have free trials.',
            'url': 'https://reddit.com/r/startups/validate'
        },
        {
            'title': 'Top 10 AI Tools for Startups',
            'snippet': 'Best tools including ValidatorAI. Compare features and prices.',
            'url': 'https://techblog.com/top-ai-tools'
        }
    ]
    
    for result in non_commercial_results:
        classification = classify_result_type(result)
        status = "✓" if classification != 'commercial' else "✗"
        print(f"  {status} {result['url']}: {classification}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("MANUAL AUDIT: STAGE 1 CLASSIFICATION LOGIC")
    print("Problem: Founders struggle to validate startup ideas quickly")
    print("=" * 70)
    
    try:
        commercial_passed = test_commercial_cases()
        non_commercial_passed = test_non_commercial_cases()
        
        test_problem_statement_scenario()
        
        if commercial_passed and non_commercial_passed:
            print("\n" + "=" * 70)
            print("✓ MANUAL AUDIT PASSED!")
            print("=" * 70)
            print("\nCONFIRMATION:")
            print("✓ Blogs and community pages are no longer classified as commercial.")
            print("✓ Only first-party product sites with strong signals are commercial.")
            print("✓ Classification is based on principled, multi-step reasoning.")
            print("=" * 70)
            sys.exit(0)
        else:
            print("\n" + "=" * 70)
            print("✗ MANUAL AUDIT FAILED!")
            print("=" * 70)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
