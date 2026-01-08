"""
Demonstration of the redesigned Stage 1 commercial classification logic.

Shows how the new principled reasoning approach classifies different types
of search results with detailed explanations of the decision-making process.
"""

import logging
from main import classify_result_type

# Enable debug logging to see the classification reasoning
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger('main')


def demo_classification(title, description, result):
    """Demonstrate classification with detailed output"""
    print("\n" + "=" * 70)
    print(f"DEMO: {title}")
    print("=" * 70)
    print(f"Description: {description}")
    print(f"\nURL: {result.get('url', 'N/A')}")
    print(f"Title: {result.get('title', 'N/A')}")
    print(f"Snippet: {result.get('snippet', 'N/A')}")
    print("\nClassification reasoning:")
    print("-" * 70)
    
    classification = classify_result_type(result)
    
    print("-" * 70)
    print(f"FINAL RESULT: {classification.upper()}")
    print("=" * 70)


def main():
    print("\n" + "=" * 70)
    print("REDESIGNED STAGE 1 CLASSIFICATION LOGIC - DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows how the new multi-step reasoning approach works.")
    print("Watch for STEP 1, STEP 2, STEP 3, and STEP 4 in the output.")
    
    # DEMO 1: First-party product (should be COMMERCIAL)
    demo_classification(
        "First-Party Product Page",
        "A real SaaS product with multiple structural signals",
        {
            'title': 'ValidatorAI - AI-Powered Startup Validation',
            'snippet': 'Validate your startup idea in minutes. Sign up for free. View pricing plans. Access your dashboard.',
            'url': 'https://validatorai.com'
        }
    )
    
    # DEMO 2: Medium article (should be CONTENT, NOT commercial)
    demo_classification(
        "Medium Article Discussing Products",
        "A blog post that mentions products but doesn't sell them",
        {
            'title': 'How to Validate Your Startup Idea | Medium',
            'snippet': 'Tools like ValidatorAI and others can help. Compare pricing and features to find the best fit.',
            'url': 'https://medium.com/@author/validate-startup-idea'
        }
    )
    
    # DEMO 3: LinkedIn post (should be CONTENT, NOT commercial)
    demo_classification(
        "LinkedIn Post with Product Mentions",
        "A social media post recommending tools",
        {
            'title': 'Best tools for validating startup ideas | LinkedIn',
            'snippet': 'Check out ValidatorAI and IdeaBrowser. Both have free trials and enterprise pricing plans.',
            'url': 'https://www.linkedin.com/pulse/best-validation-tools'
        }
    )
    
    # DEMO 4: Blog listicle (should be CONTENT, NOT commercial)
    demo_classification(
        "Listicle Comparing Products",
        "A top 10 list article discussing multiple products",
        {
            'title': '10 Best AI Tools for Startup Founders in 2024',
            'snippet': 'Top tools include ValidatorAI, IdeaBrowser, and more. Compare features, pricing, and user reviews.',
            'url': 'https://blog.example.com/top-ai-tools'
        }
    )
    
    # DEMO 5: Review/comparison article (should be CONTENT)
    demo_classification(
        "Product Comparison Article",
        "An article comparing two products head-to-head",
        {
            'title': 'ValidatorAI vs IdeaBrowser: Which is Better?',
            'snippet': 'We compare features, pricing, and ease of use. Both offer free trials and subscription plans.',
            'url': 'https://saascomparison.com/validatorai-vs-ideabrowser'
        }
    )
    
    # DEMO 6: Product with minimal signals (should be UNKNOWN or CONTENT)
    demo_classification(
        "Page with Weak Signals",
        "Not enough evidence to confidently classify as commercial",
        {
            'title': 'Startup Tools Platform',
            'snippet': 'We help founders succeed with the best tools and resources.',
            'url': 'https://example.com/tools'
        }
    )
    
    # DEMO 7: DIY tutorial (should be DIY, NOT commercial)
    demo_classification(
        "DIY Tutorial",
        "Teaching users to build their own solution",
        {
            'title': 'How to Build Your Own Startup Validator',
            'snippet': 'Step-by-step tutorial using Python. Open source code available on GitHub. Build your own solution.',
            'url': 'https://techblog.com/build-validator'
        }
    )
    
    # DEMO 8: Another first-party product (should be COMMERCIAL)
    demo_classification(
        "SaaS Platform with Pricing",
        "Clear product page with multiple structural signals",
        {
            'title': 'IdeaBrowser - Browse Validated Startup Ideas',
            'snippet': 'Access thousands of validated ideas. Try our free trial. Pricing starts at $29/month for teams.',
            'url': 'https://ideabrowser.io/pricing'
        }
    )
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("1. STEP 1 eliminates false positives by proving content sites")
    print("2. STEP 2 looks for MULTIPLE signals across CATEGORIES")
    print("3. STEP 3 handles DIY/tutorial content separately")
    print("4. STEP 4 requires HIGH CONFIDENCE for commercial classification")
    print("5. Fallback logic defaults to non-commercial when uncertain")
    print("\nResult: Blogs, social media, and listicles are NO LONGER commercial!")
    print("=" * 70)


if __name__ == "__main__":
    main()
