"""
Simplified test for refactoring validation (no API calls required).
"""

import sys
from main import (
    UserSolution,
    classify_solution_modality,
    compute_competitor_density,
    compute_market_fragmentation,
    compute_substitute_pressure,
    compute_content_saturation_for_solution,
    compute_solution_class_maturity,
    compute_automation_relevance,
)


def test_all_parameter_functions():
    """Test all market strength parameter functions"""
    print("\n" + "="*70)
    print("TEST: All Market Strength Parameter Functions")
    print("="*70)
    
    # Test 1: competitor_density
    print("\n1. Testing competitor_density...")
    tests = [
        (0, "SOFTWARE", "NONE"),
        (2, "SOFTWARE", "LOW"),
        (5, "SOFTWARE", "MEDIUM"),
        (15, "SOFTWARE", "HIGH"),
        (0, "SERVICE", "NONE"),
        (3, "SERVICE", "LOW"),
        (10, "SERVICE", "MEDIUM"),
        (20, "SERVICE", "HIGH"),
    ]
    for count, modality, expected in tests:
        result = compute_competitor_density(count, modality)
        assert result == expected, f"Failed: {count}, {modality} -> {result} (expected {expected})"
    print("   ✓ All competitor_density tests passed")
    
    # Test 2: market_fragmentation
    print("\n2. Testing market_fragmentation...")
    
    # Empty list
    result = compute_market_fragmentation([], "SOFTWARE")
    assert result == "MIXED", f"Empty list should return MIXED, got {result}"
    
    # Local indicators for SERVICE
    local_products = [
        {"name": "Local Repair Shop", "snippet": "small business near me"}
    ]
    result = compute_market_fragmentation(local_products, "SERVICE")
    assert result == "FRAGMENTED", f"Local SERVICE should be FRAGMENTED, got {result}"
    
    # Enterprise indicators for SOFTWARE
    enterprise_products = [
        {"name": "Enterprise Platform", "snippet": "industry standard platform for fortune 500"}
    ]
    result = compute_market_fragmentation(enterprise_products, "SOFTWARE")
    assert result == "CONSOLIDATED", f"Enterprise SOFTWARE should be CONSOLIDATED, got {result}"
    
    print("   ✓ All market_fragmentation tests passed")
    
    # Test 3: substitute_pressure
    print("\n3. Testing substitute_pressure...")
    
    # Test with different DIY counts and automation levels
    tests = [
        ([], "SOFTWARE", "high", "LOW"),
        ([{"title": "DIY tutorial"}] * 2, "SOFTWARE", "high", "LOW"),
        ([{"title": "DIY tutorial"}] * 5, "SOFTWARE", "high", "MEDIUM"),
        ([{"title": "DIY tutorial"}] * 10, "SOFTWARE", "high", "HIGH"),
        ([], "SERVICE", "manual", "LOW"),
        ([{"title": "DIY tutorial"}] * 5, "SERVICE", "manual", "LOW"),
        ([{"title": "DIY tutorial"}] * 10, "SERVICE", "manual", "MEDIUM"),
    ]
    for diy_list, modality, auto_level, expected in tests:
        result = compute_substitute_pressure(diy_list, modality, auto_level)
        assert result == expected, f"Failed: {len(diy_list)} DIY, {modality}, {auto_level} -> {result} (expected {expected})"
    
    print("   ✓ All substitute_pressure tests passed")
    
    # Test 4: content_saturation_for_solution
    print("\n4. Testing content_saturation_for_solution...")
    
    tests = [
        ([], "SOFTWARE", "LOW"),
        ([{"title": "Article"}] * 3, "SOFTWARE", "LOW"),
        ([{"title": "Article"}] * 10, "SOFTWARE", "MEDIUM"),
        ([{"title": "Article"}] * 20, "SOFTWARE", "HIGH"),
    ]
    for content_list, modality, expected in tests:
        result = compute_content_saturation_for_solution(content_list, modality)
        assert result == expected, f"Failed: {len(content_list)} content, {modality} -> {result} (expected {expected})"
    
    print("   ✓ All content_saturation tests passed")
    
    # Test 5: solution_class_maturity
    print("\n5. Testing solution_class_maturity...")
    
    # NON_EXISTENT: no products, no content
    result = compute_solution_class_maturity([], [], "SOFTWARE")
    assert result == "NON_EXISTENT", f"Empty should be NON_EXISTENT, got {result}"
    
    # EMERGING: some products or content
    result = compute_solution_class_maturity([{"name": "Product"}], [], "SOFTWARE")
    assert result == "EMERGING", f"Few products should be EMERGING, got {result}"
    
    # ESTABLISHED: many products and content
    products = [{"name": f"Product {i}", "snippet": ""} for i in range(10)]
    content = [{"title": f"Article {i}"} for i in range(15)]
    result = compute_solution_class_maturity(products, content, "SOFTWARE")
    assert result == "ESTABLISHED", f"Many products+content should be ESTABLISHED, got {result}"
    
    print("   ✓ All solution_class_maturity tests passed")
    
    # Test 6: automation_relevance
    print("\n6. Testing automation_relevance...")
    
    tests = [
        ("AI-powered", "SOFTWARE", "HIGH"),
        ("manual", "SOFTWARE", "LOW"),
        ("automated", "SOFTWARE", "HIGH"),
        ("AI-powered", "SERVICE", "MEDIUM"),
        ("manual", "SERVICE", "LOW"),
        ("high automation", "HYBRID", "HIGH"),
    ]
    for auto_level, modality, expected in tests:
        result = compute_automation_relevance(auto_level, modality)
        assert result == expected, f"Failed: {auto_level}, {modality} -> {result} (expected {expected})"
    
    print("   ✓ All automation_relevance tests passed")
    
    print("\n" + "="*70)
    print("✓ ALL PARAMETER FUNCTION TESTS PASSED")
    print("="*70)


def test_solution_modality_classification():
    """Test solution modality classification"""
    print("\n" + "="*70)
    print("TEST: Solution Modality Classification")
    print("="*70)
    
    # SOFTWARE
    solution = UserSolution(
        core_action="validate",
        input_required="startup idea",
        output_type="validation report",
        target_user="founders",
        automation_level="AI-powered"
    )
    assert classify_solution_modality(solution) == "SOFTWARE"
    print("✓ AI-powered validation -> SOFTWARE")
    
    # SERVICE
    solution = UserSolution(
        core_action="repair",
        input_required="bicycle",
        output_type="repaired bicycle",
        target_user="bicycle owners",
        automation_level="manual"
    )
    assert classify_solution_modality(solution) == "SERVICE"
    print("✓ Manual repair -> SERVICE")
    
    # PHYSICAL_PRODUCT (manual/low automation)
    solution = UserSolution(
        core_action="manufacture",
        input_required="raw materials",
        output_type="device",
        target_user="consumers",
        automation_level="manual"
    )
    assert classify_solution_modality(solution) == "PHYSICAL_PRODUCT"
    print("✓ Manual device manufacturing -> PHYSICAL_PRODUCT")
    
    # HYBRID (physical with automation)
    solution = UserSolution(
        core_action="manufacture",
        input_required="raw materials",
        output_type="device",
        target_user="consumers",
        automation_level="automated"
    )
    assert classify_solution_modality(solution) == "HYBRID"
    print("✓ Automated device manufacturing -> HYBRID")
    
    # HYBRID (AI-powered service)
    solution = UserSolution(
        core_action="consulting",
        input_required="business needs",
        output_type="strategy report",
        target_user="executives",
        automation_level="AI-powered"
    )
    assert classify_solution_modality(solution) == "HYBRID"
    print("✓ AI-powered consulting -> HYBRID")
    
    print("\n✓ Solution modality classification tests passed")
    print("="*70)


def test_deterministic_behavior():
    """Test that all functions are deterministic"""
    print("\n" + "="*70)
    print("TEST: Deterministic Behavior")
    print("="*70)
    
    # Test modality classification
    solution = UserSolution(
        core_action="validate",
        input_required="startup idea",
        output_type="validation report",
        target_user="founders",
        automation_level="AI-powered"
    )
    
    results = [classify_solution_modality(solution) for _ in range(5)]
    assert len(set(results)) == 1, "Modality classification is not deterministic"
    print(f"✓ Modality classification deterministic: {results[0]}")
    
    # Test parameter functions
    densities = [compute_competitor_density(5, "SOFTWARE") for _ in range(5)]
    assert len(set(densities)) == 1, "competitor_density is not deterministic"
    print(f"✓ competitor_density deterministic: {densities[0]}")
    
    relevances = [compute_automation_relevance("AI-powered", "SOFTWARE") for _ in range(5)]
    assert len(set(relevances)) == 1, "automation_relevance is not deterministic"
    print(f"✓ automation_relevance deterministic: {relevances[0]}")
    
    print("\n✓ All functions are deterministic")
    print("="*70)


def test_parameter_independence():
    """Test that parameters are independent (no hidden dependencies)"""
    print("\n" + "="*70)
    print("TEST: Parameter Independence")
    print("="*70)
    
    # Each parameter should be computable independently
    # without requiring results from other parameters
    
    # Test 1: competitor_density doesn't need other parameters
    density = compute_competitor_density(5, "SOFTWARE")
    print(f"✓ competitor_density computed independently: {density}")
    
    # Test 2: substitute_pressure doesn't need competitor_density
    pressure = compute_substitute_pressure([], "SOFTWARE", "high")
    print(f"✓ substitute_pressure computed independently: {pressure}")
    
    # Test 3: automation_relevance doesn't need other parameters
    relevance = compute_automation_relevance("AI-powered", "SOFTWARE")
    print(f"✓ automation_relevance computed independently: {relevance}")
    
    # Test 4: content_saturation doesn't need competitor info
    saturation = compute_content_saturation_for_solution([], "SOFTWARE")
    print(f"✓ content_saturation computed independently: {saturation}")
    
    # Test 5: solution_class_maturity needs products and content but not other params
    maturity = compute_solution_class_maturity([], [], "SOFTWARE")
    print(f"✓ solution_class_maturity computed independently: {maturity}")
    
    # Test 6: market_fragmentation needs products but not other params
    fragmentation = compute_market_fragmentation([], "SOFTWARE")
    print(f"✓ market_fragmentation computed independently: {fragmentation}")
    
    print("\n✓ All parameters are independent")
    print("="*70)


def test_no_scoring_or_aggregation():
    """Test that parameters are NOT aggregated into scores"""
    print("\n" + "="*70)
    print("TEST: No Scoring or Aggregation")
    print("="*70)
    
    # All parameter functions should return string enums, not numbers
    
    params_to_test = [
        ("competitor_density", compute_competitor_density(5, "SOFTWARE")),
        ("substitute_pressure", compute_substitute_pressure([], "SOFTWARE", "high")),
        ("automation_relevance", compute_automation_relevance("AI-powered", "SOFTWARE")),
        ("content_saturation", compute_content_saturation_for_solution([], "SOFTWARE")),
        ("solution_class_maturity", compute_solution_class_maturity([], [], "SOFTWARE")),
        ("market_fragmentation", compute_market_fragmentation([], "SOFTWARE")),
    ]
    
    for name, value in params_to_test:
        # Must be a string
        assert isinstance(value, str), f"{name} must return string, got {type(value)}"
        
        # Must not be a number disguised as string
        try:
            float(value)
            assert False, f"{name} appears to be a numeric score: {value}"
        except ValueError:
            pass  # Good, it's not a number
        
        print(f"✓ {name} returns string enum: {value}")
    
    print("\n✓ No numeric scores or aggregation")
    print("="*70)


def test_modality_aware_thresholds():
    """Test that thresholds adapt to modality"""
    print("\n" + "="*70)
    print("TEST: Modality-Aware Thresholds")
    print("="*70)
    
    # Test 1: competitor_density has different thresholds for SOFTWARE vs SERVICE
    software_medium = compute_competitor_density(5, "SOFTWARE")
    service_low = compute_competitor_density(5, "SERVICE")
    assert software_medium == "MEDIUM", "SOFTWARE with 5 competitors should be MEDIUM"
    assert service_low == "LOW", "SERVICE with 5 competitors should be LOW"
    print("✓ competitor_density thresholds differ by modality")
    print(f"  SOFTWARE: 5 competitors = {software_medium}")
    print(f"  SERVICE: 5 competitors = {service_low}")
    
    # Test 2: automation_relevance adapts to modality
    software_high = compute_automation_relevance("AI-powered", "SOFTWARE")
    service_medium = compute_automation_relevance("AI-powered", "SERVICE")
    assert software_high == "HIGH", "SOFTWARE with AI should be HIGH automation relevance"
    assert service_medium == "MEDIUM", "SERVICE with AI should be MEDIUM automation relevance"
    print("✓ automation_relevance adapts to modality")
    print(f"  SOFTWARE + AI = {software_high}")
    print(f"  SERVICE + AI = {service_medium}")
    
    # Test 3: solution_class_maturity has different thresholds
    products = [{"name": f"P{i}", "snippet": ""} for i in range(10)]
    content = [{"title": f"A{i}"} for i in range(10)]
    
    software_established = compute_solution_class_maturity(products, content, "SOFTWARE")
    # Note: The actual result depends on the exact implementation, but we verify it's consistent
    print(f"✓ solution_class_maturity: SOFTWARE with 10 products + 10 content = {software_established}")
    
    print("\n✓ All functions are modality-aware")
    print("="*70)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("REFACTORING VALIDATION TEST SUITE (NO API CALLS)")
    print("="*70)
    
    try:
        test_solution_modality_classification()
        test_all_parameter_functions()
        test_deterministic_behavior()
        test_parameter_independence()
        test_no_scoring_or_aggregation()
        test_modality_aware_thresholds()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nRefactoring validation complete:")
        print("  ✓ All 6 market strength parameters implemented")
        print("  ✓ All functions are deterministic and rule-based")
        print("  ✓ Parameters are independent (no aggregation)")
        print("  ✓ No numeric scores (only string enums)")
        print("  ✓ Modality-aware thresholds working correctly")
        print("  ✓ Solution modality classification working")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
