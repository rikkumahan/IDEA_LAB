"""
Test suite for MANDATORY SELF-CHECK from problem statement.

This validates that the classification system correctly handles the exact case
specified in the problem statement:

Problem: "Founders struggle to validate startup ideas quickly"

Expected COMMERCIAL competitors:
- ValidatorAI
- Ideabrowser (if detected)

Expected NON-COMMERCIAL:
- Medium articles
- Blog guides
- LinkedIn posts
- Reddit threads
- "AI tools for market research" articles

If any blog or social page is classified as COMMERCIAL, the task has FAILED.
"""

import sys
from main import classify_result_type


def test_mandatory_commercial_detection():
    """Test that true commercial products are correctly detected"""
    print("Testing COMMERCIAL competitor detection...")
    
    # ValidatorAI - First-party product with clear commercial signals
    validator_ai = {
        'title': 'ValidatorAI - AI-Powered Startup Validation',
        'snippet': 'Validate your startup idea with AI. Sign up for free trial. Pricing starts at $29/month.',
        'url': 'https://validatorai.com'
    }
    result = classify_result_type(validator_ai)
    assert result == 'commercial', f"ValidatorAI should be COMMERCIAL, got {result}"
    print("  ✓ ValidatorAI correctly classified as COMMERCIAL")
    
    # IdeaBrowser - First-party product
    ideabrowser = {
        'title': 'IdeaBrowser - Browse and Validate Startup Ideas',
        'snippet': 'Enterprise idea validation platform. Get started today. View pricing and plans.',
        'url': 'https://ideabrowser.com'
    }
    result = classify_result_type(ideabrowser)
    assert result == 'commercial', f"IdeaBrowser should be COMMERCIAL, got {result}"
    print("  ✓ IdeaBrowser correctly classified as COMMERCIAL")
    
    # Generic first-party product with strong signals
    generic_product = {
        'title': 'StartupValidator Pro - Idea Validation Software',
        'snippet': 'Professional startup validation tool. Free trial available. Subscription plans from $49/mo.',
        'url': 'https://startupvalidator.com/pricing'
    }
    result = classify_result_type(generic_product)
    assert result == 'commercial', f"Generic product should be COMMERCIAL, got {result}"
    print("  ✓ Generic first-party product correctly classified as COMMERCIAL")
    
    print("✓ COMMERCIAL detection tests PASSED\n")


def test_mandatory_medium_never_commercial():
    """Test that Medium articles are NEVER classified as COMMERCIAL"""
    print("Testing Medium articles (must be CONTENT, never COMMERCIAL)...")
    
    test_cases = [
        {
            'name': 'Medium article mentioning tools',
            'result': {
                'title': 'How to Validate Your Startup Idea | Medium',
                'snippet': 'A comprehensive guide on startup validation. Try ValidatorAI for best results.',
                'url': 'https://medium.com/@author/how-to-validate-startup-idea'
            }
        },
        {
            'name': 'Medium article with pricing keywords',
            'result': {
                'title': 'Best Tools for Startup Validation | Medium',
                'snippet': 'Top tools with pricing comparison. Sign up to read more.',
                'url': 'https://medium.com/startup-tools-pricing'
            }
        },
        {
            'name': 'Medium post discussing products',
            'result': {
                'title': 'ValidatorAI vs IdeaBrowser: Which is Better? | Medium',
                'snippet': 'Comparison of startup validation platforms. Get started with either tool today.',
                'url': 'https://medium.com/product-comparison'
            }
        },
    ]
    
    for test in test_cases:
        result = classify_result_type(test['result'])
        assert result == 'content', \
            f"{test['name']}: Expected CONTENT, got {result}. FAILURE: Medium classified as COMMERCIAL!"
        print(f"  ✓ {test['name']}: CONTENT")
    
    print("✓ Medium article tests PASSED\n")


def test_mandatory_blog_guides_never_commercial():
    """Test that blog guides are NEVER classified as COMMERCIAL"""
    print("Testing blog guides (must be CONTENT, never COMMERCIAL)...")
    
    test_cases = [
        {
            'name': 'Ultimate guide',
            'result': {
                'title': 'Ultimate Guide to Startup Idea Validation',
                'snippet': 'Complete guide with best practices and tools. Sign up for our newsletter.',
                'url': 'https://startupblog.com/ultimate-guide-validation'
            }
        },
        {
            'name': 'Complete guide with pricing mentions',
            'result': {
                'title': 'Complete Guide to Validation Tools',
                'snippet': 'Guide covering tools, pricing, and best practices for founders.',
                'url': 'https://entrepreneurblog.com/complete-guide'
            }
        },
        {
            'name': 'Buyer\'s guide',
            'result': {
                'title': 'Buyer\'s Guide: Startup Validation Software',
                'snippet': 'Compare options and pricing. Get started with the right tool.',
                'url': 'https://techblog.com/buyers-guide-validation'
            }
        },
        {
            'name': 'How-to guide',
            'result': {
                'title': 'How-to Guide: Validate Your Startup Idea',
                'snippet': 'Step-by-step guide. Try tools like ValidatorAI. Sign up to learn more.',
                'url': 'https://founderblog.com/how-to-validate'
            }
        },
    ]
    
    for test in test_cases:
        result = classify_result_type(test['result'])
        assert result == 'content', \
            f"{test['name']}: Expected CONTENT, got {result}. FAILURE: Blog guide classified as COMMERCIAL!"
        print(f"  ✓ {test['name']}: CONTENT")
    
    print("✓ Blog guide tests PASSED\n")


def test_mandatory_linkedin_never_commercial():
    """Test that LinkedIn posts are NEVER classified as COMMERCIAL"""
    print("Testing LinkedIn posts (must be CONTENT, never COMMERCIAL)...")
    
    test_cases = [
        {
            'name': 'LinkedIn article mentioning tools',
            'result': {
                'title': 'AI Tools for Market Research | LinkedIn',
                'snippet': 'Check out ValidatorAI, IdeaBrowser, and other tools for validation.',
                'url': 'https://linkedin.com/pulse/ai-tools-market-research'
            }
        },
        {
            'name': 'LinkedIn post with pricing',
            'result': {
                'title': 'Best Startup Validation Tools | LinkedIn',
                'snippet': 'Top tools with pricing. Sign up for free trials. Get started today.',
                'url': 'https://www.linkedin.com/posts/best-startup-tools'
            }
        },
        {
            'name': 'LinkedIn company page',
            'result': {
                'title': 'Startup Validation Platform | LinkedIn',
                'snippet': 'Our platform helps founders validate ideas. Pricing available.',
                'url': 'https://linkedin.com/company/startup-validator'
            }
        },
    ]
    
    for test in test_cases:
        result = classify_result_type(test['result'])
        assert result == 'content', \
            f"{test['name']}: Expected CONTENT, got {result}. FAILURE: LinkedIn classified as COMMERCIAL!"
        print(f"  ✓ {test['name']}: CONTENT")
    
    print("✓ LinkedIn post tests PASSED\n")


def test_mandatory_reddit_never_commercial():
    """Test that Reddit threads are NEVER classified as COMMERCIAL"""
    print("Testing Reddit threads (must be CONTENT, never COMMERCIAL)...")
    
    test_cases = [
        {
            'name': 'Reddit discussion',
            'result': {
                'title': 'Tools for validating startup ideas? : r/startups',
                'snippet': 'Looking for tools to validate my idea. Any recommendations?',
                'url': 'https://reddit.com/r/startups/comments/validate-tools'
            }
        },
        {
            'name': 'Reddit recommendation thread',
            'result': {
                'title': 'Best startup validation platforms : r/Entrepreneur',
                'snippet': 'Try ValidatorAI, it has great pricing. Sign up for free trial.',
                'url': 'https://www.reddit.com/r/Entrepreneur/comments/validation-platforms'
            }
        },
        {
            'name': 'Reddit comparison thread',
            'result': {
                'title': 'ValidatorAI vs IdeaBrowser? : r/startups',
                'snippet': 'Which platform should I use? Both have pricing plans available.',
                'url': 'https://reddit.com/r/startups/comments/compare-tools'
            }
        },
    ]
    
    for test in test_cases:
        result = classify_result_type(test['result'])
        assert result == 'content', \
            f"{test['name']}: Expected CONTENT, got {result}. FAILURE: Reddit classified as COMMERCIAL!"
        print(f"  ✓ {test['name']}: CONTENT")
    
    print("✓ Reddit thread tests PASSED\n")


def test_mandatory_listicles_never_commercial():
    """Test that listicles/review articles are NEVER classified as COMMERCIAL"""
    print("Testing listicles and review articles (must be CONTENT, never COMMERCIAL)...")
    
    test_cases = [
        {
            'name': 'Top X tools article',
            'result': {
                'title': 'Top 10 Tools for Startup Validation',
                'snippet': 'Best tools reviewed. Compare pricing and features. Get started today.',
                'url': 'https://techreview.com/top-10-validation-tools'
            }
        },
        {
            'name': 'Best tools comparison',
            'result': {
                'title': 'Best Startup Validation Software 2025',
                'snippet': 'Compare the leading platforms. Sign up for free trials. View pricing.',
                'url': 'https://softwarereviews.com/best-validation-software'
            }
        },
        {
            'name': 'Alternatives article',
            'result': {
                'title': 'ValidatorAI Alternatives: Best Options',
                'snippet': 'Top alternatives to ValidatorAI. Compare features and pricing.',
                'url': 'https://saasreview.com/validatorai-alternatives'
            }
        },
        {
            'name': 'VS comparison article',
            'result': {
                'title': 'ValidatorAI vs IdeaBrowser vs Others',
                'snippet': 'Comprehensive comparison. See pricing, features, and trials.',
                'url': 'https://productcompare.com/validation-tools-comparison'
            }
        },
    ]
    
    for test in test_cases:
        result = classify_result_type(test['result'])
        assert result == 'content', \
            f"{test['name']}: Expected CONTENT, got {result}. FAILURE: Listicle classified as COMMERCIAL!"
        print(f"  ✓ {test['name']}: CONTENT")
    
    print("✓ Listicle and review article tests PASSED\n")


def test_edge_case_product_mentions_in_content():
    """
    Test edge case: Content that mentions products with strong commercial keywords
    should still be classified as CONTENT, not COMMERCIAL.
    
    This is critical: Mentioning tools ≠ being a competitor
    """
    print("Testing edge case: Product mentions in content (must be CONTENT)...")
    
    test_cases = [
        {
            'name': 'Blog post mentioning pricing',
            'result': {
                'title': 'Blog: How I Validated My Startup',
                'snippet': 'I used ValidatorAI with their $29/month pricing. Great tool! Sign up to read more.',
                'url': 'https://founderblog.com/my-validation-story'
            }
        },
        {
            'name': 'Article with trial mentions',
            'result': {
                'title': 'Article: Validation Tools Review',
                'snippet': 'ValidatorAI offers free trial. IdeaBrowser has signup. Compare platforms here.',
                'url': 'https://techblog.com/validation-review'
            }
        },
        {
            'name': 'Newsletter with product links',
            'result': {
                'title': 'Weekly Newsletter: Startup Tools',
                'snippet': 'This week: ValidatorAI pricing update. Sign up for our newsletter.',
                'url': 'https://startupnews.com/newsletter-tools'
            }
        },
    ]
    
    for test in test_cases:
        result = classify_result_type(test['result'])
        assert result == 'content', \
            f"{test['name']}: Expected CONTENT, got {result}. FAILURE: Content with product mentions classified as COMMERCIAL!"
        print(f"  ✓ {test['name']}: CONTENT (product mentions ignored)")
    
    print("✓ Edge case tests PASSED\n")


def test_precedence_content_over_all():
    """
    Test that CONTENT site check happens FIRST and overrides all other signals.
    
    Even if a LinkedIn/Medium post has ALL commercial signals (pricing, signup, etc.),
    it must STILL be classified as CONTENT because domain check comes first.
    """
    print("Testing precedence: CONTENT domain check overrides all signals...")
    
    # LinkedIn post with MAXIMUM commercial signals
    linkedin_maxsignals = {
        'title': 'Best Platform - Pricing and Plans | LinkedIn',
        'snippet': 'Enterprise platform. Sign up for free trial. Pricing available. Dashboard access. Get started.',
        'url': 'https://linkedin.com/pulse/best-platform-pricing'
    }
    result = classify_result_type(linkedin_maxsignals)
    assert result == 'content', \
        f"LinkedIn with max signals: Expected CONTENT, got {result}. FAILURE: Content site domain check failed!"
    print("  ✓ LinkedIn with max commercial signals: Still CONTENT")
    
    # Medium article with ALL product keywords
    medium_maxsignals = {
        'title': 'Product Platform - SaaS Solution | Medium',
        'snippet': 'Our platform offers enterprise features. Free trial, pricing, signup, dashboard, get started.',
        'url': 'https://medium.com/product-platform-saas'
    }
    result = classify_result_type(medium_maxsignals)
    assert result == 'content', \
        f"Medium with max signals: Expected CONTENT, got {result}. FAILURE: Content site domain check failed!"
    print("  ✓ Medium with max commercial signals: Still CONTENT")
    
    # Reddit with product language
    reddit_maxsignals = {
        'title': 'Our SaaS Platform - Pricing : r/startups',
        'snippet': 'Check out our platform. Free trial, enterprise plans, signup today.',
        'url': 'https://reddit.com/r/startups/comments/saas-platform'
    }
    result = classify_result_type(reddit_maxsignals)
    assert result == 'content', \
        f"Reddit with max signals: Expected CONTENT, got {result}. FAILURE: Content site domain check failed!"
    print("  ✓ Reddit with max commercial signals: Still CONTENT")
    
    print("✓ Precedence tests PASSED\n")


def run_all_tests():
    """Run all mandatory self-check tests"""
    print("=" * 80)
    print("MANDATORY SELF-CHECK TEST SUITE")
    print("Problem: 'Founders struggle to validate startup ideas quickly'")
    print("=" * 80)
    print()
    
    try:
        # Test commercial detection (positive cases)
        test_mandatory_commercial_detection()
        
        # Test non-commercial detection (negative cases)
        test_mandatory_medium_never_commercial()
        test_mandatory_blog_guides_never_commercial()
        test_mandatory_linkedin_never_commercial()
        test_mandatory_reddit_never_commercial()
        test_mandatory_listicles_never_commercial()
        
        # Test edge cases
        test_edge_case_product_mentions_in_content()
        test_precedence_content_over_all()
        
        print("=" * 80)
        print("✅ ALL MANDATORY SELF-CHECK TESTS PASSED!")
        print("=" * 80)
        print()
        print("VALIDATION RESULT:")
        print("  ✅ ValidatorAI and IdeaBrowser: Correctly classified as COMMERCIAL")
        print("  ✅ Medium articles: Never classified as COMMERCIAL")
        print("  ✅ Blog guides: Never classified as COMMERCIAL")
        print("  ✅ LinkedIn posts: Never classified as COMMERCIAL")
        print("  ✅ Reddit threads: Never classified as COMMERCIAL")
        print("  ✅ Listicles/reviews: Never classified as COMMERCIAL")
        print("  ✅ Edge cases: Product mentions in content handled correctly")
        print("  ✅ Precedence: Content site check overrides all other signals")
        print()
        print("CONCLUSION: Classification logic is CORRECT and meets all requirements.")
        print("=" * 80)
        return True
        
    except AssertionError as e:
        print("\n" + "=" * 80)
        print("❌ MANDATORY SELF-CHECK FAILED!")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        print("TASK HAS FAILED: A blog or social page was classified as COMMERCIAL.")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
