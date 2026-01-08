"""
Test suite for competition and content saturation analysis.

Tests the new functions added to address issues identified in
COMPETITION_SATURATION_AUDIT.md:
- ISSUE 1: Query bucket mixing (tool vs workaround)
- ISSUE 2: Competition and content saturation computation
- ISSUE 3: Content saturation interpretation (negative vs neutral)
- ISSUE 4: Competition pressure thresholds
- ISSUE 5: Workaround type classification (seeking vs found)

All tests verify deterministic behavior (no ML, no probabilistic logic).
"""

import sys
from main import (
    classify_result_type,
    separate_tool_workaround_results,
    compute_competition_pressure,
    classify_saturation_signal,
    deduplicate_results
)


def test_classify_result_type_commercial():
    """Test classification of commercial product results"""
    print("Testing commercial result classification...")
    
    # Test case 1: Clear commercial indicators
    result1 = {
        'title': 'Acme Software - Enterprise Solution',
        'snippet': 'Try our 14-day free trial. Pricing starts at $99/month.'
    }
    assert classify_result_type(result1) == 'commercial'
    
    # Test case 2: SaaS platform
    result2 = {
        'title': 'CloudTool - SaaS Platform for Teams',
        'snippet': 'Sign up today and get 20% off your subscription.'
    }
    assert classify_result_type(result2) == 'commercial'
    
    # Test case 3: Company name
    result3 = {
        'title': 'DataCorp Inc. - Business Intelligence',
        'snippet': 'Purchase our enterprise license for your company.'
    }
    assert classify_result_type(result3) == 'commercial'
    
    print("✓ Commercial result classification tests passed")


def test_classify_result_type_diy():
    """Test classification of DIY/open source results"""
    print("\nTesting DIY result classification...")
    
    # Test case 1: How-to guide
    result1 = {
        'title': 'How to Build Your Own Data Pipeline',
        'snippet': 'Learn how to create a custom script using Python.'
    }
    assert classify_result_type(result1) == 'diy'
    
    # Test case 2: Open source
    result2 = {
        'title': 'Free Open Source Tool on GitHub',
        'snippet': 'DIY solution for automating tasks. Self-hosted and free.'
    }
    assert classify_result_type(result2) == 'diy'
    
    # Test case 3: Custom script
    result3 = {
        'title': 'Manual Workflow Automation with Custom Code',
        'snippet': 'Build your own automation using this tutorial.'
    }
    assert classify_result_type(result3) == 'diy'
    
    print("✓ DIY result classification tests passed")


def test_classify_result_type_unknown():
    """Test classification of ambiguous results"""
    print("\nTesting unknown result classification...")
    
    # Test case 1: No clear indicators
    result1 = {
        'title': 'Data Processing Best Practices',
        'snippet': 'Common approaches to handling large datasets.'
    }
    assert classify_result_type(result1) == 'unknown'
    
    # Test case 2: Mixed signals (both commercial and DIY)
    result2 = {
        'title': 'Open Source SaaS Platform - Free Trial',
        'snippet': 'DIY customization available. Pricing for enterprise.'
    }
    assert classify_result_type(result2) == 'unknown'
    
    print("✓ Unknown result classification tests passed")


def test_separate_tool_workaround_results():
    """Test bucket separation to fix mixing issue"""
    print("\nTesting tool/workaround bucket separation...")
    
    # Simulate mixed results in tool bucket
    tool_results = [
        # Should stay in tool bucket (commercial)
        {
            'url': 'https://example.com/product1',
            'title': 'Acme Tool - SaaS Platform',
            'snippet': 'Sign up for our subscription plan.'
        },
        # Should move to workaround bucket (DIY)
        {
            'url': 'https://github.com/user/script',
            'title': 'Custom Python Script',
            'snippet': 'Free open source automation script.'
        },
        # Should stay in tool bucket (commercial)
        {
            'url': 'https://example.com/product2',
            'title': 'DataCorp Enterprise Software',
            'snippet': 'Try our 30-day free trial.'
        }
    ]
    
    # Simulate mixed results in workaround bucket
    workaround_results = [
        # Should stay in workaround bucket (DIY)
        {
            'url': 'https://blog.com/how-to',
            'title': 'How to Build Your Own Automation',
            'snippet': 'Custom solution using Python code.'
        },
        # Should move to tool bucket (commercial)
        {
            'url': 'https://example.com/product3',
            'title': 'Automation Platform Inc.',
            'snippet': 'Purchase our business license.'
        },
        # Should stay in workaround bucket (DIY)
        {
            'url': 'https://tutorial.com/guide',
            'title': 'DIY Data Processing Guide',
            'snippet': 'Manual steps to automate your workflow.'
        }
    ]
    
    # Separate results
    corrected_tool, corrected_workaround = separate_tool_workaround_results(
        tool_results, workaround_results
    )
    
    # Verify tool bucket contains only commercial results
    # Expected: 3 commercial (2 from tool + 1 from workaround)
    assert len(corrected_tool) == 3, f"Expected 3 commercial, got {len(corrected_tool)}"
    
    # Verify workaround bucket contains only DIY results
    # Expected: 3 DIY (1 from tool + 2 from workaround)
    assert len(corrected_workaround) == 3, f"Expected 3 DIY, got {len(corrected_workaround)}"
    
    print("✓ Bucket separation tests passed")


def test_compute_competition_pressure_commercial():
    """Test competition pressure thresholds for commercial competitors"""
    print("\nTesting commercial competition pressure thresholds...")
    
    # Test case 1: LOW (0-3 competitors)
    assert compute_competition_pressure(0, 'commercial') == "LOW"
    assert compute_competition_pressure(1, 'commercial') == "LOW"
    assert compute_competition_pressure(3, 'commercial') == "LOW"
    
    # Test case 2: MEDIUM (4-9 competitors)
    assert compute_competition_pressure(4, 'commercial') == "MEDIUM"
    assert compute_competition_pressure(6, 'commercial') == "MEDIUM"
    assert compute_competition_pressure(9, 'commercial') == "MEDIUM"
    
    # Test case 3: HIGH (10+ competitors)
    assert compute_competition_pressure(10, 'commercial') == "HIGH"
    assert compute_competition_pressure(15, 'commercial') == "HIGH"
    assert compute_competition_pressure(50, 'commercial') == "HIGH"
    
    print("✓ Commercial competition pressure tests passed")


def test_compute_competition_pressure_diy():
    """Test competition pressure thresholds for DIY alternatives"""
    print("\nTesting DIY competition pressure thresholds...")
    
    # Test case 1: LOW (0-6 alternatives) - 2x tolerance
    assert compute_competition_pressure(0, 'diy') == "LOW"
    assert compute_competition_pressure(3, 'diy') == "LOW"
    assert compute_competition_pressure(6, 'diy') == "LOW"
    
    # Test case 2: MEDIUM (7-19 alternatives)
    assert compute_competition_pressure(7, 'diy') == "MEDIUM"
    assert compute_competition_pressure(12, 'diy') == "MEDIUM"
    assert compute_competition_pressure(19, 'diy') == "MEDIUM"
    
    # Test case 3: HIGH (20+ alternatives)
    assert compute_competition_pressure(20, 'diy') == "HIGH"
    assert compute_competition_pressure(30, 'diy') == "HIGH"
    assert compute_competition_pressure(100, 'diy') == "HIGH"
    
    print("✓ DIY competition pressure tests passed")


def test_classify_saturation_signal_low_count():
    """Test that low content count is always NEUTRAL"""
    print("\nTesting low content saturation...")
    
    # Rule 1: Low count (<6) is always NEUTRAL
    blog_results = [
        {'title': 'Article 1', 'snippet': 'Content 1'},
        {'title': 'Article 2', 'snippet': 'Content 2'},
        {'title': 'Article 3', 'snippet': 'Content 3'},
    ]
    
    assert classify_saturation_signal(3, blog_results) == "NEUTRAL"
    assert classify_saturation_signal(5, blog_results) == "NEUTRAL"
    
    print("✓ Low content saturation tests passed")


def test_classify_saturation_signal_clickbait():
    """Test NEGATIVE classification for clickbait content"""
    print("\nTesting clickbait content detection...")
    
    # Create 10 blog results, 5 with clickbait signals (50% clickbait)
    blog_results = [
        {'title': 'Top 10 Best Tools You Won\'t Believe', 'snippet': 'Ultimate guide'},
        {'title': 'One Simple Trick to Automate Everything', 'snippet': 'Secret hack'},
        {'title': 'This Will Change Your Workflow Forever', 'snippet': 'Must read'},
        {'title': 'Shocking Data Processing Secrets', 'snippet': 'Best of collection'},
        {'title': 'The Ultimate Listicle of Automation', 'snippet': 'Roundup article'},
        {'title': 'How to Process Data', 'snippet': 'Technical guide'},
        {'title': 'Data Automation Tutorial', 'snippet': 'Step by step'},
        {'title': 'Processing Best Practices', 'snippet': 'Documentation'},
        {'title': 'Workflow Optimization', 'snippet': 'Implementation guide'},
        {'title': 'Data Pipeline Architecture', 'snippet': 'Technical solution'},
    ]
    
    # 5/10 = 50% clickbait (>40% threshold) → NEGATIVE
    assert classify_saturation_signal(10, blog_results) == "NEGATIVE"
    
    print("✓ Clickbait detection tests passed")


def test_classify_saturation_signal_trend():
    """Test NEGATIVE classification for trend/year-specific content"""
    print("\nTesting trend content detection...")
    
    # Create 10 blog results, 6 with trend signals (60% trend)
    blog_results = [
        {'title': 'Best Tools for 2025', 'snippet': 'Latest automation trends'},
        {'title': 'Data Processing in 2026', 'snippet': 'Brand new techniques'},
        {'title': 'Trending Workflows This Month', 'snippet': 'Hot topic'},
        {'title': 'Latest Automation Just Released', 'snippet': '2025 guide'},
        {'title': 'This Week\'s Best Practices', 'snippet': 'Trending now'},
        {'title': 'New Normal Data Pipeline', 'snippet': 'Post-pandemic workflow'},
        {'title': 'How to Process Data', 'snippet': 'Technical guide'},
        {'title': 'Data Automation Tutorial', 'snippet': 'Step by step'},
        {'title': 'Processing Best Practices', 'snippet': 'Documentation'},
        {'title': 'Workflow Optimization', 'snippet': 'Implementation guide'},
    ]
    
    # 6/10 = 60% trend (>50% threshold) → NEGATIVE
    assert classify_saturation_signal(10, blog_results) == "NEGATIVE"
    
    print("✓ Trend content detection tests passed")


def test_classify_saturation_signal_technical():
    """Test NEUTRAL classification for technical evergreen content"""
    print("\nTesting technical content detection...")
    
    # Create 10 blog results, 6 with technical signals (60% technical)
    blog_results = [
        {'title': 'How to Build Data Pipeline', 'snippet': 'Step by step tutorial'},
        {'title': 'Automation Implementation Guide', 'snippet': 'Technical documentation'},
        {'title': 'Troubleshooting Data Issues', 'snippet': 'Debugging solution'},
        {'title': 'Optimize Workflow Performance', 'snippet': 'Fix common problems'},
        {'title': 'Data Processing Architecture', 'snippet': 'Implementation example'},
        {'title': 'Automate Your Workflow Guide', 'snippet': 'How to improve process'},
        {'title': 'Best Automation Tools 2025', 'snippet': 'Latest trends'},
        {'title': 'Top 10 Data Hacks', 'snippet': 'Secret tricks'},
        {'title': 'Data Processing News', 'snippet': 'General article'},
        {'title': 'Workflow Overview', 'snippet': 'Basic introduction'},
    ]
    
    # 6/10 = 60% technical (>50% threshold) → NEUTRAL
    assert classify_saturation_signal(10, blog_results) == "NEUTRAL"
    
    print("✓ Technical content detection tests passed")


def test_classify_saturation_signal_mixed():
    """Test NEUTRAL default for mixed content quality"""
    print("\nTesting mixed content quality...")
    
    # Create 10 blog results with balanced signals (no majority)
    blog_results = [
        {'title': 'Top 10 Tools', 'snippet': 'Best of list'},  # Clickbait
        {'title': 'Latest 2025 Trends', 'snippet': 'Brand new'},  # Trend
        {'title': 'How to Automate', 'snippet': 'Tutorial guide'},  # Technical
        {'title': 'Data Processing', 'snippet': 'General article'},
        {'title': 'Best Practices', 'snippet': 'Overview'},
        {'title': 'Workflow Tips', 'snippet': 'Advice'},
        {'title': 'Automation News', 'snippet': 'Updates'},
        {'title': 'Data Guide', 'snippet': 'Introduction'},
        {'title': 'Processing Methods', 'snippet': 'Comparison'},
        {'title': 'Workflow Strategies', 'snippet': 'Approaches'},
    ]
    
    # Mixed signals, no majority → NEUTRAL (default)
    assert classify_saturation_signal(10, blog_results) == "NEUTRAL"
    
    print("✓ Mixed content quality tests passed")


def test_deterministic_behavior():
    """Test that all functions are deterministic"""
    print("\nTesting deterministic behavior...")
    
    # Test result classification is deterministic
    result = {
        'title': 'Test Product - SaaS Platform',
        'snippet': 'Sign up for trial. Pricing available.'
    }
    
    assert classify_result_type(result) == classify_result_type(result)
    assert classify_result_type(result) == 'commercial'
    
    # Test competition pressure is deterministic
    assert compute_competition_pressure(5, 'commercial') == "MEDIUM"
    assert compute_competition_pressure(5, 'commercial') == "MEDIUM"
    
    # Test saturation classification is deterministic
    blog_results = [
        {'title': f'Article {i}', 'snippet': 'How to guide'}
        for i in range(10)
    ]
    
    result1 = classify_saturation_signal(10, blog_results)
    result2 = classify_saturation_signal(10, blog_results)
    assert result1 == result2
    
    print("✓ Deterministic behavior tests passed")


def test_boundary_conditions():
    """Test boundary conditions for thresholds"""
    print("\nTesting boundary conditions...")
    
    # Test commercial competition boundaries
    assert compute_competition_pressure(3, 'commercial') == "LOW"
    assert compute_competition_pressure(4, 'commercial') == "MEDIUM"
    assert compute_competition_pressure(9, 'commercial') == "MEDIUM"
    assert compute_competition_pressure(10, 'commercial') == "HIGH"
    
    # Test DIY competition boundaries
    assert compute_competition_pressure(6, 'diy') == "LOW"
    assert compute_competition_pressure(7, 'diy') == "MEDIUM"
    assert compute_competition_pressure(19, 'diy') == "MEDIUM"
    assert compute_competition_pressure(20, 'diy') == "HIGH"
    
    # Test content saturation boundaries
    assert classify_saturation_signal(5, []) == "NEUTRAL"
    assert classify_saturation_signal(6, []) == "NEUTRAL"  # At minimum for classification
    
    print("✓ Boundary condition tests passed")


def run_all_tests():
    """Run all test suites"""
    print("=" * 70)
    print("Running Competition and Content Saturation Test Suite")
    print("=" * 70)
    
    try:
        # Result type classification tests
        test_classify_result_type_commercial()
        test_classify_result_type_diy()
        test_classify_result_type_unknown()
        
        # Bucket separation tests
        test_separate_tool_workaround_results()
        
        # Competition pressure tests
        test_compute_competition_pressure_commercial()
        test_compute_competition_pressure_diy()
        
        # Content saturation tests
        test_classify_saturation_signal_low_count()
        test_classify_saturation_signal_clickbait()
        test_classify_saturation_signal_trend()
        test_classify_saturation_signal_technical()
        test_classify_saturation_signal_mixed()
        
        # General tests
        test_deterministic_behavior()
        test_boundary_conditions()
        
        print("\n" + "=" * 70)
        print("✓ ALL COMPETITION/SATURATION TESTS PASSED!")
        print("=" * 70)
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
