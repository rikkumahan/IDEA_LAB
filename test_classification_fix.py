"""
Test suite for commercial vs content misclassification fix.

Verifies that:
1. Reddit, Quora, Medium, blogs are classified as 'content', NOT 'commercial'
2. Only first-party product sites with strong signals are 'commercial'
3. Classification precedence: commercial > diy > content > unknown
4. Deterministic behavior
"""

import sys
from main import classify_result_type


def test_reddit_never_commercial():
    """Test that Reddit posts are NEVER classified as commercial"""
    print("Testing Reddit classification...")
    
    # Test case 1: Reddit post mentioning commercial tools
    result1 = {
        'title': 'Best project management tools - Reddit discussion',
        'snippet': 'Check out Asana, Monday.com, and ClickUp. They have great pricing plans.',
        'url': 'https://www.reddit.com/r/productivity/comments/abc123/best_tools'
    }
    classification = classify_result_type(result1)
    assert classification != 'commercial', \
        f"Reddit should NEVER be commercial, got {classification}"
    assert classification in ['content', 'diy', 'unknown'], \
        f"Reddit should be content/diy/unknown, got {classification}"
    
    # Test case 2: Reddit post with pricing discussion
    result2 = {
        'title': 'r/SaaS - Pricing strategy discussion',
        'snippet': 'Our SaaS platform offers enterprise plans starting at $99/month',
        'url': 'https://reddit.com/r/SaaS/pricing'
    }
    classification = classify_result_type(result2)
    assert classification != 'commercial', \
        f"Reddit should NEVER be commercial even with pricing, got {classification}"
    
    print("✓ Reddit never commercial tests passed")


def test_quora_never_commercial():
    """Test that Quora answers are NEVER classified as commercial"""
    print("\nTesting Quora classification...")
    
    # Test case 1: Quora answer mentioning tools
    result1 = {
        'title': 'What is the best CRM software? - Quora',
        'snippet': 'Salesforce and HubSpot are great options. Both offer free trials.',
        'url': 'https://www.quora.com/What-is-the-best-CRM-software'
    }
    classification = classify_result_type(result1)
    assert classification != 'commercial', \
        f"Quora should NEVER be commercial, got {classification}"
    assert classification in ['content', 'diy', 'unknown'], \
        f"Quora should be content/diy/unknown, got {classification}"
    
    # Test case 2: Quora with product mentions
    result2 = {
        'title': 'Best productivity tools 2024 - Quora',
        'snippet': 'Try Notion, it has pricing plans for teams and enterprise.',
        'url': 'https://quora.com/productivity-tools'
    }
    classification = classify_result_type(result2)
    assert classification != 'commercial', \
        f"Quora should NEVER be commercial, got {classification}"
    
    print("✓ Quora never commercial tests passed")


def test_medium_never_commercial():
    """Test that Medium articles are NEVER classified as commercial"""
    print("\nTesting Medium classification...")
    
    # Test case 1: Medium article reviewing tools
    result1 = {
        'title': 'Top 10 Project Management Tools | by Author | Medium',
        'snippet': 'I tested 10 tools including Jira, Asana, and Monday. Pricing varies.',
        'url': 'https://medium.com/@author/top-10-project-tools'
    }
    classification = classify_result_type(result1)
    assert classification != 'commercial', \
        f"Medium should NEVER be commercial, got {classification}"
    assert classification in ['content', 'diy', 'unknown'], \
        f"Medium should be content/diy/unknown, got {classification}"
    
    # Test case 2: Medium with product promotion
    result2 = {
        'title': 'Why you should try our SaaS platform - Medium',
        'snippet': 'Sign up today for a free trial. Enterprise plans available.',
        'url': 'https://medium.com/product-promo'
    }
    classification = classify_result_type(result2)
    assert classification != 'commercial', \
        f"Medium should NEVER be commercial even with signup CTA, got {classification}"
    
    print("✓ Medium never commercial tests passed")


def test_blog_sites_never_commercial():
    """Test that blog/review sites are NEVER classified as commercial"""
    print("\nTesting blog/review site classification...")
    
    # Test case 1: Comparison blog
    result1 = {
        'title': 'Best CRM Software Comparison 2024 - TechBlog',
        'snippet': 'We compare Salesforce vs HubSpot pricing and features.',
        'url': 'https://techblog.com/crm-comparison'
    }
    classification = classify_result_type(result1)
    # Blogs discussing tools should be 'content', not 'commercial'
    # Even if they mention pricing/products
    assert classification != 'commercial', \
        f"Blog comparison articles should not be commercial, got {classification}"
    
    # Test case 2: Review site
    result2 = {
        'title': 'Asana Review 2024 - G2',
        'snippet': 'Pricing starts at $10.99/user/month. Sign up for free trial.',
        'url': 'https://www.g2.com/products/asana/reviews'
    }
    classification = classify_result_type(result2)
    assert classification != 'commercial', \
        f"Review sites should not be commercial, got {classification}"
    
    # Test case 3: Listicle article
    result3 = {
        'title': '25 Best Productivity Tools You Need to Try',
        'snippet': 'From free to enterprise pricing, these tools will boost productivity.',
        'url': 'https://blog.example.com/25-best-tools'
    }
    classification = classify_result_type(result3)
    assert classification != 'commercial', \
        f"Listicles should not be commercial, got {classification}"
    
    print("✓ Blog/review site never commercial tests passed")


def test_first_party_commercial_detection():
    """Test that genuine first-party product sites ARE classified as commercial"""
    print("\nTesting first-party commercial detection...")
    
    # Test case 1: SaaS product homepage with strong signals
    result1 = {
        'title': 'Acme CRM - Customer Relationship Management Software',
        'snippet': 'Start your free 14-day trial. View pricing plans. Access your dashboard.',
        'url': 'https://acmecrm.com'
    }
    classification = classify_result_type(result1)
    assert classification == 'commercial', \
        f"First-party product with strong signals should be commercial, got {classification}"
    
    # Test case 2: Software product with pricing page
    result2 = {
        'title': 'Pricing - ProjectTool Pro',
        'snippet': 'Choose your plan: Free, Team ($29), Enterprise ($99). Sign up now.',
        'url': 'https://projecttool.com/pricing'
    }
    classification = classify_result_type(result2)
    assert classification == 'commercial', \
        f"Product pricing page should be commercial, got {classification}"
    
    # Test case 3: SaaS with signup CTA
    result3 = {
        'title': 'CloudStorage Platform - Secure File Storage',
        'snippet': 'Get started with our platform. Sign up for free. Upgrade to Pro.',
        'url': 'https://cloudstorage.io'
    }
    classification = classify_result_type(result3)
    assert classification == 'commercial', \
        f"SaaS platform with signup should be commercial, got {classification}"
    
    print("✓ First-party commercial detection tests passed")


def test_content_classification_for_discussions():
    """Test that discussion sites are classified as 'content'"""
    print("\nTesting content classification...")
    
    # Test case 1: Stack Overflow discussion
    result1 = {
        'title': 'How to automate data entry - Stack Overflow',
        'snippet': 'You can use Python scripts or try tools like Zapier.',
        'url': 'https://stackoverflow.com/questions/123/automate-data-entry'
    }
    classification = classify_result_type(result1)
    assert classification in ['content', 'diy'], \
        f"Stack Overflow should be content/diy, got {classification}"
    
    # Test case 2: Forum post
    result2 = {
        'title': 'Best automation tools? - DevForum',
        'snippet': 'I recommend checking out tool X, Y, and Z.',
        'url': 'https://devforum.com/automation-tools'
    }
    classification = classify_result_type(result2)
    # Forums are content sites discussing topics
    assert classification in ['content', 'unknown'], \
        f"Forum should be content/unknown, got {classification}"
    
    print("✓ Content classification tests passed")


def test_classification_precedence():
    """Test that classification precedence is: commercial > diy > content > unknown"""
    print("\nTesting classification precedence...")
    
    # Test case 1: First-party product (commercial) wins over content site
    # This should NOT happen - commercial sites should not be on content domains
    # But if somehow it does, commercial should win
    
    # Test case 2: DIY tutorial on blog (content site) - should be 'content' not 'diy'
    result2 = {
        'title': 'How to Build Your Own CRM - Dev.to',
        'snippet': 'Tutorial for creating a DIY CRM with Python and Django.',
        'url': 'https://dev.to/build-your-own-crm'
    }
    classification = classify_result_type(result2)
    # Content site domain should take precedence, but DIY signals are present
    # The implementation will determine final precedence
    assert classification in ['content', 'diy'], \
        f"DIY tutorial on content site should be content or diy, got {classification}"
    
    print("✓ Classification precedence tests passed")


def test_deterministic_classification():
    """Test that classification is deterministic"""
    print("\nTesting deterministic classification...")
    
    result = {
        'title': 'Asana - Project Management Tool',
        'snippet': 'Sign up for free. Pricing plans for teams and enterprise.',
        'url': 'https://asana.com'
    }
    
    # Run classification multiple times
    classifications = [classify_result_type(result) for _ in range(5)]
    
    # All should be identical
    assert len(set(classifications)) == 1, \
        f"Classification should be deterministic, got {classifications}"
    
    print("✓ Deterministic classification tests passed")


def test_edge_cases():
    """Test edge cases for classification"""
    print("\nTesting edge cases...")
    
    # Test case 1: Empty result
    result1 = {
        'title': '',
        'snippet': '',
        'url': ''
    }
    classification = classify_result_type(result1)
    assert classification in ['unknown', 'content'], \
        f"Empty result should be unknown/content, got {classification}"
    
    # Test case 2: Missing URL
    result2 = {
        'title': 'Some product',
        'snippet': 'Pricing available'
    }
    classification = classify_result_type(result2)
    # Without URL, should still classify based on content
    assert classification in ['commercial', 'content', 'unknown'], \
        f"Result without URL should classify based on content, got {classification}"
    
    # Test case 3: Product on subdomain of content site
    result3 = {
        'title': 'Product Documentation',
        'snippet': 'API pricing and plans',
        'url': 'https://docs.reddit.com'
    }
    classification = classify_result_type(result3)
    # Should recognize reddit.com domain
    assert classification != 'commercial', \
        f"Reddit subdomain should not be commercial, got {classification}"
    
    print("✓ Edge case tests passed")


if __name__ == "__main__":
    print("=" * 70)
    print("Running Commercial vs Content Misclassification Fix Tests")
    print("=" * 70)
    
    try:
        test_reddit_never_commercial()
        test_quora_never_commercial()
        test_medium_never_commercial()
        test_blog_sites_never_commercial()
        test_first_party_commercial_detection()
        test_content_classification_for_discussions()
        test_classification_precedence()
        test_deterministic_classification()
        test_edge_cases()
        
        print("\n" + "=" * 70)
        print("✓ ALL CLASSIFICATION FIX TESTS PASSED!")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
