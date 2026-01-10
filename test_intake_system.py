#!/usr/bin/env python3
"""
Test Script for LLM-Assisted Intake Layer + Frontend Integration

This script tests:
1. Backend /intake/start endpoint
2. Backend /intake/respond endpoint with validation
3. Backend /analyze endpoint
4. Complete happy-path flow
5. Garbage input handling
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_intake_start():
    """Test starting an intake session."""
    print("\n=== TEST 1: Starting Intake Session ===")
    response = requests.post(
        f"{API_BASE}/intake/start",
        json={"initial_text": None}
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    assert "session_id" in data, "Missing session_id"
    assert "question" in data, "Missing question"
    assert "field" in data, "Missing field"
    
    print(f"✓ Session started: {data['session_id']}")
    print(f"✓ First question: {data['question'][:50]}...")
    
    return data["session_id"]


def test_validation_error(session_id):
    """Test validation with invalid input."""
    print("\n=== TEST 2: Testing Validation (Invalid Input) ===")
    response = requests.post(
        f"{API_BASE}/intake/respond",
        json={
            "session_id": session_id,
            "answer": "x"  # Too short
        }
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    assert "error" in data, "Should have validation error"
    assert data.get("retry") == True, "Should allow retry"
    
    print(f"✓ Validation error detected: {data['error']}")
    print("✓ Retry allowed")


def test_complete_flow():
    """Test complete intake flow with all fields."""
    print("\n=== TEST 3: Complete Happy-Path Flow ===")
    
    # Start session
    response = requests.post(
        f"{API_BASE}/intake/start",
        json={"initial_text": None}
    )
    session_id = response.json()["session_id"]
    print(f"✓ Started session: {session_id}")
    
    # Answer all questions
    answers = [
        "Manual data entry is tedious and error-prone for small businesses",
        "small business owners",
        "daily",
        "validate data entries",
        "spreadsheet or CSV file",
        "validation report with errors highlighted",
        "small business accountants",
        "AI-powered automated validation",
        "yes",  # replaces_human_labor
        "5",  # step_reduction_ratio
        "yes",  # delivers_final_answer
        "no",  # unique_data_access
        "no"   # works_under_constraints
    ]
    
    for i, answer in enumerate(answers):
        print(f"\n  Answering question {i+1}/{len(answers)}: '{answer[:30]}...'")
        response = requests.post(
            f"{API_BASE}/intake/respond",
            json={
                "session_id": session_id,
                "answer": answer
            }
        )
        
        assert response.status_code == 200, f"Failed at question {i+1}"
        data = response.json()
        
        if data.get("complete"):
            print("  ✓ Intake complete!")
            break
        elif "error" in data:
            print(f"  ✗ Error: {data['error']}")
            return False
        else:
            print(f"  ✓ Next question: {data.get('question', '')[:50]}...")
    
    # Run analysis
    print("\n  Running analysis...")
    response = requests.post(
        f"{API_BASE}/analyze",
        json={"session_id": session_id}
    )
    
    if response.status_code != 200:
        print(f"  ✗ Analysis failed: {response.text}")
        return False
    
    result = response.json()
    print("  ✓ Analysis complete!")
    
    # Verify result structure
    assert "validation_result" in result, "Missing validation_result"
    assert "explanation" in result, "Missing explanation"
    
    validation = result["validation_result"]
    assert "problem_reality" in validation, "Missing problem_reality"
    assert "market_reality" in validation, "Missing market_reality"
    assert "leverage_reality" in validation, "Missing leverage_reality"
    assert "validation_state" in validation, "Missing validation_state"
    
    print(f"\n  ✓ Validation Class: {validation['validation_state']['validation_class']}")
    print(f"  ✓ Problem Level: {validation['problem_reality']['problem_level']}")
    
    return True


def test_garbage_input():
    """Test handling of garbage input."""
    print("\n=== TEST 4: Garbage Input Handling ===")
    
    # Start session
    response = requests.post(
        f"{API_BASE}/intake/start",
        json={"initial_text": None}
    )
    session_id = response.json()["session_id"]
    
    # Try various garbage inputs
    garbage_inputs = [
        "",  # Empty
        "a",  # Too short
        "   ",  # Only whitespace
    ]
    
    for garbage in garbage_inputs:
        response = requests.post(
            f"{API_BASE}/intake/respond",
            json={
                "session_id": session_id,
                "answer": garbage
            }
        )
        
        data = response.json()
        if "error" in data:
            print(f"  ✓ Rejected: '{garbage}' - {data['error']}")
        else:
            print(f"  ✗ Accepted invalid input: '{garbage}'")
            return False
    
    return True


def test_docs_endpoint():
    """Test that /docs endpoint is accessible."""
    print("\n=== TEST 5: /docs Endpoint ===")
    response = requests.get(f"{API_BASE}/docs")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
    
    print("✓ /docs endpoint is accessible")
    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("TESTING LLM-ASSISTED INTAKE LAYER")
    print("=" * 60)
    
    try:
        # Test 1: Start session
        session_id = test_intake_start()
        
        # Test 2: Validation
        test_validation_error(session_id)
        
        # Test 3: Complete flow
        test_complete_flow()
        
        # Test 4: Garbage input
        test_garbage_input()
        
        # Test 5: Docs endpoint
        test_docs_endpoint()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
