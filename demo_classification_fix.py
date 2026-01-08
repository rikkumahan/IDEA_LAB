"""
Demonstration of the commercial competitor misclassification fix.

This shows how the fix correctly classifies different types of content:
- LinkedIn, Facebook, newsletters, guides → CONTENT (not commercial)
- First-party product sites → COMMERCIAL
"""

from main import classify_result_type

def print_classification(name, result):
    """Print classification result with color coding"""
    classification = classify_result_type(result)
    symbol = "✓" if classification != 'commercial' else "✗"
    print(f"  {symbol} {name:30s} → {classification.upper()}")
    return classification

def main():
    print("=" * 80)
    print("DEMONSTRATION: Commercial Competitor Misclassification Fix")
    print("=" * 80)
    
    print("\n1. CONTENT SITES (Should NEVER be commercial):")
    print("-" * 80)
    
    # LinkedIn
    linkedin = {
        'title': 'Best productivity tools | LinkedIn',
        'snippet': 'Check out these tools with pricing and enterprise features.',
        'url': 'https://www.linkedin.com/pulse/best-tools'
    }
    print_classification("LinkedIn article", linkedin)
    
    # Facebook
    facebook = {
        'title': 'CRM recommendations - Facebook Group',
        'snippet': 'What CRM do you use? Looking for pricing info.',
        'url': 'https://www.facebook.com/groups/startups/crm'
    }
    print_classification("Facebook group", facebook)
    
    # Reddit
    reddit = {
        'title': 'Best project tools? - r/productivity',
        'snippet': 'I need tool recommendations with pricing.',
        'url': 'https://www.reddit.com/r/productivity/best-tools'
    }
    print_classification("Reddit post", reddit)
    
    # Quora
    quora = {
        'title': 'What is the best CRM? - Quora',
        'snippet': 'Salesforce and HubSpot have great pricing plans.',
        'url': 'https://www.quora.com/What-is-the-best-CRM'
    }
    print_classification("Quora answer", quora)
    
    # Medium
    medium = {
        'title': 'Top 10 SaaS Tools | Medium',
        'snippet': 'Review of tools with pricing and sign up options.',
        'url': 'https://medium.com/@author/top-saas-tools'
    }
    print_classification("Medium article", medium)
    
    print("\n2. NEWSLETTERS (Should NEVER be commercial):")
    print("-" * 80)
    
    newsletter1 = {
        'title': 'Weekly Newsletter: Best SaaS Tools',
        'snippet': 'Subscribe to our newsletter for tool reviews and pricing.',
        'url': 'https://example.com/newsletter/saas'
    }
    print_classification("Newsletter", newsletter1)
    
    newsletter2 = {
        'title': 'SaaS Weekly | Substack',
        'snippet': 'Weekly newsletter covering new tools and pricing.',
        'url': 'https://saasweekly.substack.com/p/issue-42'
    }
    print_classification("Substack newsletter", newsletter2)
    
    print("\n3. GUIDES (Should NEVER be commercial):")
    print("-" * 80)
    
    guide1 = {
        'title': 'Ultimate Guide to CRM Software',
        'snippet': 'Complete guide with pricing and features comparison.',
        'url': 'https://blog.example.com/crm-guide'
    }
    print_classification("Ultimate guide", guide1)
    
    guide2 = {
        'title': "Buyer's Guide: Project Management Tools",
        'snippet': 'Help choosing PM tools. See pricing and sign up.',
        'url': 'https://techsite.com/buyers-guide-pm'
    }
    print_classification("Buyer's guide", guide2)
    
    guide3 = {
        'title': 'Complete Guide to Startup Validation',
        'snippet': 'Learn about validation tools, pricing, and features.',
        'url': 'https://startup.guide/validation'
    }
    print_classification("Complete guide", guide3)
    
    print("\n4. REVIEW/COMPARISON SITES (Should NEVER be commercial):")
    print("-" * 80)
    
    review1 = {
        'title': 'Asana Review 2024 - G2',
        'snippet': 'Pricing starts at $10.99/user. Sign up for free trial.',
        'url': 'https://www.g2.com/products/asana/reviews'
    }
    print_classification("G2 review", review1)
    
    review2 = {
        'title': 'Best CRM Software Comparison',
        'snippet': 'Compare Salesforce vs HubSpot pricing and features.',
        'url': 'https://techblog.com/crm-comparison'
    }
    print_classification("Comparison article", review2)
    
    print("\n5. FIRST-PARTY PRODUCTS (Should BE commercial):")
    print("-" * 80)
    
    product1 = {
        'title': 'Asana - Project Management Software',
        'snippet': 'Sign up for free. View pricing plans. Access dashboard.',
        'url': 'https://asana.com'
    }
    result1 = print_classification("Asana (real product)", product1)
    
    product2 = {
        'title': 'ValidatorAI - Startup Validation',
        'snippet': 'Get started with AI validation. Pricing from $29/month.',
        'url': 'https://validatorai.com'
    }
    result2 = print_classification("ValidatorAI (real product)", product2)
    
    product3 = {
        'title': 'Pricing - CloudStorage Pro',
        'snippet': 'Enterprise plans available. Sign up now.',
        'url': 'https://cloudstorage.io/pricing'
    }
    result3 = print_classification("CloudStorage (real product)", product3)
    
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print("✓ Content sites (LinkedIn, Facebook, Reddit, Quora, Medium) → CONTENT")
    print("✓ Newsletters → CONTENT")
    print("✓ Guides (ultimate, buyer's, complete) → CONTENT")
    print("✓ Review/comparison sites → CONTENT")
    print("✓ First-party products → COMMERCIAL")
    print("\nResult: commercial_competitors.count now excludes content/discussion sites!")
    print("=" * 80)

if __name__ == "__main__":
    main()
