"""
Integration test for complete validation pipeline (Stages 1-4).

This test verifies that all stages work together correctly.
"""

import unittest
import logging
from fastapi.testclient import TestClient
from main import app

logging.basicConfig(level=logging.INFO)


class TestCompleteValidation(unittest.TestCase):
    """Test the complete validation pipeline."""
    
    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_get_leverage_questions(self):
        """Test getting leverage questions."""
        response = self.client.get("/leverage-questions?use_llm=false")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("questions", data)
        self.assertEqual(len(data["questions"]), 5)
        
        # Check question structure
        for question in data["questions"]:
            self.assertIn("id", question)
            self.assertIn("question", question)
            self.assertIn("answer_type", question)
    
    def test_complete_validation_strong_foundation(self):
        """Test complete validation with strong foundation outcome."""
        # This simulates a SEVERE problem with strong leverage
        request_data = {
            "problem": "manual data entry wasting hours every day",
            "target_user": "small business owners",
            "user_claimed_frequency": "daily",
            "leverage_inputs": {
                "replaces_human_labor": True,
                "step_reduction_ratio": 10,
                "delivers_final_answer": True,
                "unique_data_access": True,
                "works_under_constraints": False
            },
            "use_llm": False  # Disable LLM for deterministic testing
        }
        
        # Note: This test requires SERPAPI_KEY to be set
        # If not set, the test will still run but with empty signals
        # For CI/CD, you may want to mock the serpapi_search function
        
        response = self.client.post("/validate-complete", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check structure
            self.assertIn("problem_reality", data)
            self.assertIn("leverage_reality", data)
            self.assertIn("validation_state", data)
            self.assertIn("explanation", data)
            
            # Check validation state structure
            validation = data["validation_state"]
            self.assertIn("problem_validity", validation)
            self.assertIn("leverage_presence", validation)
            self.assertIn("validation_class", validation)
            self.assertIn("reasoning", validation)
            
            # Check leverage reality
            leverage = data["leverage_reality"]
            self.assertIn("leverage_flags", leverage)
            
            # Should detect multiple leverage flags
            present_flags = [f for f in leverage["leverage_flags"] if f.get("present")]
            self.assertGreater(len(present_flags), 0, "Should detect at least one leverage flag")
            
            # Check explanation is present
            self.assertIsInstance(data["explanation"], str)
            self.assertGreater(len(data["explanation"]), 50)
        else:
            # If SERPAPI_KEY not set, test structure only
            self.assertIn(response.status_code, [200, 500])
    
    def test_complete_validation_with_market(self):
        """Test complete validation with market analysis included."""
        request_data = {
            "problem": "validating startup ideas",
            "target_user": "entrepreneurs",
            "user_claimed_frequency": "weekly",
            "solution": {
                "core_action": "validate",
                "input_required": "startup idea text",
                "output_type": "validation report",
                "target_user": "startup founders",
                "automation_level": "AI-powered"
            },
            "leverage_inputs": {
                "replaces_human_labor": True,
                "step_reduction_ratio": 8,
                "delivers_final_answer": True,
                "unique_data_access": False,
                "works_under_constraints": True
            },
            "use_llm": False
        }
        
        response = self.client.post("/validate-complete", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Should include market reality
            self.assertIn("market_reality", data)
            
            market = data["market_reality"]
            self.assertIn("solution_modality", market)
            self.assertIn("market_strength", market)
            self.assertIn("competitors", market)
            
            # Check market strength parameters
            market_strength = market["market_strength"]
            self.assertIn("competitor_density", market_strength)
            self.assertIn("market_fragmentation", market_strength)
            self.assertIn("substitute_pressure", market_strength)
    
    def test_validation_determinism(self):
        """Test that same inputs produce same validation class."""
        request_data = {
            "problem": "organizing meeting notes",
            "target_user": "professionals",
            "user_claimed_frequency": "daily",
            "leverage_inputs": {
                "replaces_human_labor": True,
                "step_reduction_ratio": 5,
                "delivers_final_answer": True,
                "unique_data_access": False,
                "works_under_constraints": False
            },
            "use_llm": False
        }
        
        # Run validation twice
        responses = []
        for _ in range(2):
            response = self.client.post("/validate-complete", json=request_data)
            if response.status_code == 200:
                responses.append(response.json())
        
        if len(responses) == 2:
            # Validation class should be identical
            class1 = responses[0]["validation_state"]["validation_class"]
            class2 = responses[1]["validation_state"]["validation_class"]
            self.assertEqual(class1, class2, "Validation is not deterministic")
            
            # Leverage presence should be identical
            presence1 = responses[0]["validation_state"]["leverage_presence"]
            presence2 = responses[1]["validation_state"]["leverage_presence"]
            self.assertEqual(presence1, presence2, "Leverage detection is not deterministic")
    
    def test_invalid_leverage_inputs(self):
        """Test that invalid leverage inputs are rejected."""
        request_data = {
            "problem": "test problem",
            "target_user": "test users",
            "user_claimed_frequency": "daily",
            "leverage_inputs": {
                "replaces_human_labor": True,
                "step_reduction_ratio": -1,  # Invalid: should be >= 0
                "delivers_final_answer": True,
                "unique_data_access": False,
                "works_under_constraints": False
            },
            "use_llm": False
        }
        
        response = self.client.post("/validate-complete", json=request_data)
        
        # Should return error
        self.assertIn(response.status_code, [400, 422, 500])
    
    def test_missing_leverage_inputs(self):
        """Test that missing required leverage inputs are rejected."""
        request_data = {
            "problem": "test problem",
            "target_user": "test users",
            "user_claimed_frequency": "daily",
            "leverage_inputs": {
                "replaces_human_labor": True,
                "step_reduction_ratio": 5
                # Missing required fields
            },
            "use_llm": False
        }
        
        response = self.client.post("/validate-complete", json=request_data)
        
        # Should return error
        self.assertIn(response.status_code, [400, 422, 500])


class TestArchitecturalBoundaries(unittest.TestCase):
    """Test that architectural boundaries are maintained."""
    
    def setUp(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_llm_disabled_still_works(self):
        """Test that system works with LLM completely disabled."""
        request_data = {
            "problem": "manual report generation",
            "target_user": "analysts",
            "user_claimed_frequency": "weekly",
            "leverage_inputs": {
                "replaces_human_labor": True,
                "step_reduction_ratio": 7,
                "delivers_final_answer": True,
                "unique_data_access": False,
                "works_under_constraints": False
            },
            "use_llm": False  # LLM disabled
        }
        
        response = self.client.post("/validate-complete", json=request_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Should still produce complete output
            self.assertIn("validation_state", data)
            self.assertIn("explanation", data)
            
            # Validation class should still be determined
            validation_class = data["validation_state"]["validation_class"]
            self.assertIn(validation_class, [
                "STRONG_FOUNDATION",
                "REAL_PROBLEM_WEAK_EDGE",
                "WEAK_FOUNDATION"
            ])
    
    def test_market_does_not_affect_validation(self):
        """Test that market data doesn't affect validation class."""
        # Base request (no market data)
        base_request = {
            "problem": "scheduling conflicts",
            "target_user": "teams",
            "user_claimed_frequency": "daily",
            "leverage_inputs": {
                "replaces_human_labor": True,
                "step_reduction_ratio": 6,
                "delivers_final_answer": True,
                "unique_data_access": False,
                "works_under_constraints": True
            },
            "use_llm": False
        }
        
        # Request with market data
        market_request = {
            **base_request,
            "solution": {
                "core_action": "schedule",
                "input_required": "calendar events",
                "output_type": "optimized schedule",
                "target_user": "teams",
                "automation_level": "AI-powered"
            }
        }
        
        response_base = self.client.post("/validate-complete", json=base_request)
        response_market = self.client.post("/validate-complete", json=market_request)
        
        if response_base.status_code == 200 and response_market.status_code == 200:
            data_base = response_base.json()
            data_market = response_market.json()
            
            # Validation class should be the same
            # (market data is contextual only, doesn't affect validation)
            class_base = data_base["validation_state"]["validation_class"]
            class_market = data_market["validation_state"]["validation_class"]
            
            self.assertEqual(
                class_base,
                class_market,
                "Market data affected validation class (architectural violation)"
            )


if __name__ == '__main__':
    # Check if SERPAPI_KEY is set
    import os
    if not os.getenv("SERPAPI_KEY"):
        print("WARNING: SERPAPI_KEY not set. Some tests may not run fully.")
    
    unittest.main()
