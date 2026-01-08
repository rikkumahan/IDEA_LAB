"""
Test suite for blocking bug: misclassification of content as commercial.

Tests that LinkedIn, Facebook, newsletters, and guides are NEVER classified
as commercial competitors.
"""

import sys
from main import classify_result_type


def test_linkedin_never_commercial():
    """Test that LinkedIn posts/articles are NEVER classified as commercial"""
    print("Testing LinkedIn classification...")
    
    # Test case 1: LinkedIn article mentioning products
    result1 = {
        'title': 'Best productivity tools for 2024 | LinkedIn',
        'snippet': 'Check out these amazing tools with pricing plans and enterprise features.',
        'url': 'https://www.linkedin.com/pulse/best-productivity-tools'
    }
    classification = classify_result_type(result1)
    assert classification != 'commercial', \
        f"LinkedIn should NEVER be commercial, got {classification}"
    print(f"  LinkedIn article classified as: {classification}")
    
    # Test case 2: LinkedIn post with product mention
    result2 = {
        'title': 'Announcing our new SaaS platform | LinkedIn Post',
        'snippet': 'Sign up now for free trial. Enterprise pricing available.',
        'url': 'https://linkedin.com/posts/user-announcing-product'
    }
    classification = classify_result_type(result2)
    assert classification != 'commercial', \
        f"LinkedIn should NEVER be commercial, got {classification}"
    print(f"  LinkedIn post classified as: {classification}")
    
    print("✓ LinkedIn never commercial tests passed")


def test_facebook_never_commercial():
    """Test that Facebook groups/posts are NEVER classified as commercial"""
    print("\nTesting Facebook classification...")
    
    # Test case 1: Facebook group discussion
    result1 = {
        'title': 'Best CRM tools? - Facebook Group',
        'snippet': 'What are the best CRM tools? I need pricing info and features.',
        'url': 'https://www.facebook.com/groups/saas-tools/best-crm'
    }
    classification = classify_result_type(result1)
    assert classification != 'commercial', \
        f"Facebook should NEVER be commercial, got {classification}"
    print(f"  Facebook group classified as: {classification}")
    
    # Test case 2: Facebook page promoting product
    result2 = {
        'title': 'Try our new software | Facebook',
        'snippet': 'Sign up for free trial. View our pricing plans.',
        'url': 'https://facebook.com/pages/product-name'
    }
    classification = classify_result_type(result2)
    assert classification != 'commercial', \
        f"Facebook should NEVER be commercial, got {classification}"
    print(f"  Facebook page classified as: {classification}")
    
    print("✓ Facebook never commercial tests passed")


def test_newsletter_never_commercial():
    """Test that newsletters are NEVER classified as commercial"""
    print("\nTesting newsletter classification...")
    
    # Test case 1: Newsletter mentioning products
    result1 = {
        'title': 'Weekly Newsletter: Top 5 SaaS Tools',
        'snippet': 'Our newsletter covers the best tools. Get pricing info and sign up links.',
        'url': 'https://example.com/newsletter/top-tools'
    }
    classification = classify_result_type(result1)
    # Newsletters should be content, not commercial
    assert classification != 'commercial', \
        f"Newsletter discussing tools should not be commercial, got {classification}"
    print(f"  Newsletter classified as: {classification}")
    
    # Test case 2: Substack newsletter
    result2 = {
        'title': 'Best productivity tools - Newsletter | Substack',
        'snippet': 'Subscribe to our newsletter for tool recommendations and pricing comparisons.',
        'url': 'https://newsletter.substack.com/p/productivity-tools'
    }
    classification = classify_result_type(result2)
    assert classification != 'commercial', \
        f"Substack newsletter should not be commercial, got {classification}"
    print(f"  Substack newsletter classified as: {classification}")
    
    print("✓ Newsletter never commercial tests passed")


def test_guide_never_commercial():
    """Test that guides are NEVER classified as commercial"""
    print("\nTesting guide classification...")
    
    # Test case 1: How-to guide
    result1 = {
        'title': 'Complete Guide to Project Management Tools',
        'snippet': 'This guide covers pricing, features, and how to choose the right tool.',
        'url': 'https://example.com/guides/project-management-tools'
    }
    classification = classify_result_type(result1)
    assert classification != 'commercial', \
        f"Guide should not be commercial, got {classification}"
    print(f"  Guide classified as: {classification}")
    
    # Test case 2: Ultimate guide
    result2 = {
        'title': 'Ultimate Guide: Startup Validation Tools',
        'snippet': 'Learn about the best tools for validating startup ideas. Compare pricing and features.',
        'url': 'https://blog.example.com/ultimate-guide-validation'
    }
    classification = classify_result_type(result2)
    assert classification != 'commercial', \
        f"Ultimate guide should not be commercial, got {classification}"
    print(f"  Ultimate guide classified as: {classification}")
    
    # Test case 3: Buyer's guide
    result3 = {
        'title': 'Buyer\'s Guide: CRM Software 2024',
        'snippet': 'This buyer\'s guide helps you choose CRM software. See pricing and sign up.',
        'url': 'https://techsite.com/buyers-guide-crm'
    }
    classification = classify_result_type(result3)
    assert classification != 'commercial', \
        f"Buyer's guide should not be commercial, got {classification}"
    print(f"  Buyer's guide classified as: {classification}")
    
    print("✓ Guide never commercial tests passed")


def test_only_first_party_is_commercial():
    """Test that only first-party product sites with ALL requirements are commercial"""
    print("\nTesting first-party requirements...")
    
    # Test case 1: Blog mentioning tools (has pricing keywords but not first-party)
    result1 = {
        'title': 'Best project management tools comparison',
        'snippet': 'Comparing Asana, Monday, and ClickUp. All have pricing plans and sign up options.',
        'url': 'https://blog.techsite.com/pm-tools'
    }
    classification = classify_result_type(result1)
    assert classification != 'commercial', \
        f"Blog comparing tools should not be commercial, got {classification}"
    print(f"  Comparison blog classified as: {classification}")
    
    # Test case 2: List article with product mentions
    result2 = {
        'title': '10 Best Productivity Tools You Need',
        'snippet': 'These tools offer free trials, pricing plans, and enterprise features.',
        'url': 'https://website.com/10-best-tools'
    }
    classification = classify_result_type(result2)
    assert classification != 'commercial', \
        f"Listicle should not be commercial, got {classification}"
    print(f"  Listicle classified as: {classification}")
    
    # Test case 3: Real first-party product (should be commercial)
    result3 = {
        'title': 'ValidatorAI - AI-Powered Startup Validation',
        'snippet': 'Sign up for free. View pricing plans. Access your dashboard.',
        'url': 'https://validatorai.com'
    }
    classification = classify_result_type(result3)
    assert classification == 'commercial', \
        f"Real first-party product should be commercial, got {classification}"
    print(f"  Real product classified as: {classification}")
    
    print("✓ First-party requirements tests passed")


if __name__ == "__main__":
    print("=" * 70)
    print("Running Blocking Bug Tests: Content Misclassification")
    print("=" * 70)
    
    try:
        test_linkedin_never_commercial()
        test_facebook_never_commercial()
        test_newsletter_never_commercial()
        test_guide_never_commercial()
        test_only_first_party_is_commercial()
        
        print("\n" + "=" * 70)
        print("✓ ALL BLOCKING BUG TESTS PASSED!")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
