"""
Unit tests for complete validation pipeline without network dependencies.

These tests verify core functionality without requiring SERPAPI access.
"""

import unittest
import logging
from stage3_leverage import (
    run_stage3_leverage_detection,
    ValidationError
)
from validation import (
    ProblemReality,
    MarketReality,
    LeverageReality,
    validate_startup_idea,
    ValidationClass,
    format_validation_output
)
from explanation_layer import generate_explanation
from questioning_layer import (
    create_questioning_session,
    CANONICAL_QUESTIONS
)
from llm_stub import StubLLMClient

logging.basicConfig(level=logging.INFO)


class TestCompleteValidationOffline(unittest.TestCase):
    """Test complete validation pipeline without network calls."""
    
    def test_end_to_end_strong_foundation(self):
        """Test end-to-end flow for STRONG_FOUNDATION outcome."""
        # Stage 1: Problem Reality (simulated)
        problem_reality = ProblemReality(
            problem_level="SEVERE",
            signals={
                "intensity_count": 8,
                "complaint_count": 15,
                "workaround_count": 10
            },
            normalized_signals={
                "intensity_level": "HIGH",
                "complaint_level": "HIGH",
                "workaround_level": "HIGH"
            }
        )
        
        # Stage 2: Market Reality (simulated, optional)
        market_reality = MarketReality(
            solution_modality="SOFTWARE",
            market_strength={
                "competitor_density": "MEDIUM",
                "market_fragmentation": "FRAGMENTED",
                "substitute_pressure": "LOW",
                "content_saturation": "LOW",
                "solution_class_maturity": "EMERGING",
                "automation_relevance": "HIGH"
            },
            competitors={
                "software": [
                    {"name": "Competitor A", "url": "http://a.com", "pricing_model": "freemium"}
                ],
                "services_expected": False
            }
        )
        
        # Stage 3: Leverage Detection
        leverage_inputs = {
            "replaces_human_labor": True,
            "step_reduction_ratio": 10,
            "delivers_final_answer": True,
            "unique_data_access": True,
            "works_under_constraints": False
        }
        
        leverage_flags = run_stage3_leverage_detection(leverage_inputs)
        
        leverage_reality = LeverageReality(
            leverage_flags=[
                {
                    "name": flag.name,
                    "present": flag.present,
                    "reason": flag.reason
                }
                for flag in leverage_flags.flags
            ]
        )
        
        # Stage 4: Validation
        validation_state = validate_startup_idea(
            problem_reality,
            market_reality,
            leverage_reality
        )
        
        # Verify result
        self.assertEqual(
            validation_state.validation_class,
            ValidationClass.STRONG_FOUNDATION
        )
        self.assertEqual(
            validation_state.problem_validity.value,
            "REAL"
        )
        self.assertEqual(
            validation_state.leverage_presence.value,
            "PRESENT"
        )
        
        # Verify leverage flags were detected
        self.assertGreater(len(leverage_reality.leverage_flags), 0)
        
        # Generate explanation
        output = format_validation_output(
            problem_reality,
            market_reality,
            leverage_reality,
            validation_state
        )
        
        explanation = generate_explanation(
            output["problem_reality"],
            output["market_reality"],
            output["leverage_reality"],
            output["validation_state"],
            use_llm=False
        )
        
        # Verify explanation was generated
        self.assertIsInstance(explanation, str)
        self.assertIn("Problem Reality", explanation)
        self.assertIn("Leverage Reality", explanation)
        self.assertIn("Validation Result", explanation)
    
    def test_end_to_end_real_problem_weak_edge(self):
        """Test end-to-end flow for REAL_PROBLEM_WEAK_EDGE outcome."""
        # Stage 1: REAL problem
        problem_reality = ProblemReality(
            problem_level="DRASTIC",
            signals={
                "intensity_count": 10,
                "complaint_count": 20,
                "workaround_count": 12
            },
            normalized_signals={
                "intensity_level": "HIGH",
                "complaint_level": "HIGH",
                "workaround_level": "HIGH"
            }
        )
        
        # Stage 3: NO leverage
        leverage_inputs = {
            "replaces_human_labor": False,
            "step_reduction_ratio": 0,
            "delivers_final_answer": False,
            "unique_data_access": False,
            "works_under_constraints": False
        }
        
        leverage_flags = run_stage3_leverage_detection(leverage_inputs)
        leverage_reality = LeverageReality(leverage_flags=[])
        
        # Stage 4: Validation
        validation_state = validate_startup_idea(
            problem_reality,
            None,  # No market analysis
            leverage_reality
        )
        
        # Verify result
        self.assertEqual(
            validation_state.validation_class,
            ValidationClass.REAL_PROBLEM_WEAK_EDGE
        )
        self.assertEqual(
            validation_state.problem_validity.value,
            "REAL"
        )
        self.assertEqual(
            validation_state.leverage_presence.value,
            "NONE"
        )
    
    def test_end_to_end_weak_foundation(self):
        """Test end-to-end flow for WEAK_FOUNDATION outcome."""
        # Stage 1: WEAK problem
        problem_reality = ProblemReality(
            problem_level="MODERATE",
            signals={
                "intensity_count": 2,
                "complaint_count": 3,
                "workaround_count": 4
            },
            normalized_signals={
                "intensity_level": "LOW",
                "complaint_level": "LOW",
                "workaround_level": "LOW"
            }
        )
        
        # Stage 3: Has leverage (but problem is weak)
        leverage_inputs = {
            "replaces_human_labor": True,
            "step_reduction_ratio": 5,
            "delivers_final_answer": True,
            "unique_data_access": False,
            "works_under_constraints": False
        }
        
        leverage_flags = run_stage3_leverage_detection(leverage_inputs)
        
        leverage_reality = LeverageReality(
            leverage_flags=[
                {
                    "name": flag.name,
                    "present": flag.present,
                    "reason": flag.reason
                }
                for flag in leverage_flags.flags
            ]
        )
        
        # Stage 4: Validation
        validation_state = validate_startup_idea(
            problem_reality,
            None,
            leverage_reality
        )
        
        # Verify result: WEAK problem overrides leverage
        self.assertEqual(
            validation_state.validation_class,
            ValidationClass.WEAK_FOUNDATION
        )
        self.assertEqual(
            validation_state.problem_validity.value,
            "WEAK"
        )
    
    def test_questioning_session_flow(self):
        """Test questioning session for leverage input collection."""
        llm = StubLLMClient()
        
        # Create session
        session = create_questioning_session(llm, use_llm=False)
        
        # Verify questions
        questions = session.get_questions_for_presentation()
        self.assertEqual(len(questions), 5)
        
        # Verify all canonical questions are present
        question_ids = {q["id"] for q in questions}
        expected_ids = set(CANONICAL_QUESTIONS.keys())
        self.assertEqual(question_ids, expected_ids)
        
        # Submit answers
        answers = {
            "replaces_human_labor": True,
            "step_reduction_ratio": 7,
            "delivers_final_answer": True,
            "unique_data_access": False,
            "works_under_constraints": True
        }
        
        validated_inputs = session.submit_answers(answers)
        
        # Verify all inputs are present
        self.assertEqual(set(validated_inputs.keys()), set(answers.keys()))
        
        # Verify types are correct
        self.assertIsInstance(validated_inputs["replaces_human_labor"], bool)
        self.assertIsInstance(validated_inputs["step_reduction_ratio"], int)
    
    def test_market_does_not_affect_validation(self):
        """Verify market data is contextual only."""
        problem_reality = ProblemReality(
            problem_level="SEVERE",
            signals={},
            normalized_signals={}
        )
        
        leverage_reality = LeverageReality(
            leverage_flags=[
                {"name": "AUTOMATION_LEVERAGE", "present": True, "reason": "test"}
            ]
        )
        
        # Validate without market data
        state_without_market = validate_startup_idea(
            problem_reality,
            None,
            leverage_reality
        )
        
        # Validate with high competition market
        high_competition_market = MarketReality(
            solution_modality="SOFTWARE",
            market_strength={
                "competitor_density": "HIGH",
                "market_fragmentation": "CONSOLIDATED",
                "substitute_pressure": "HIGH",
                "content_saturation": "HIGH",
                "solution_class_maturity": "ESTABLISHED",
                "automation_relevance": "HIGH"
            },
            competitors={"software": [], "services_expected": False}
        )
        
        state_with_market = validate_startup_idea(
            problem_reality,
            high_competition_market,
            leverage_reality
        )
        
        # Validation class should be identical
        self.assertEqual(
            state_without_market.validation_class,
            state_with_market.validation_class
        )
        
        # Both should be STRONG_FOUNDATION
        self.assertEqual(
            state_with_market.validation_class,
            ValidationClass.STRONG_FOUNDATION
        )
    
    def test_explanation_independence(self):
        """Verify explanation doesn't affect validation."""
        problem_reality = ProblemReality(
            problem_level="SEVERE",
            signals={},
            normalized_signals={}
        )
        
        leverage_reality = LeverageReality(
            leverage_flags=[
                {"name": "DATA_LEVERAGE", "present": True, "reason": "test"}
            ]
        )
        
        # Validate before explanation
        state1 = validate_startup_idea(problem_reality, None, leverage_reality)
        
        # Generate explanation
        output = format_validation_output(
            problem_reality,
            None,
            leverage_reality,
            state1
        )
        
        explanation = generate_explanation(
            output["problem_reality"],
            {},
            output["leverage_reality"],
            output["validation_state"],
            use_llm=False
        )
        
        # Validate after explanation
        state2 = validate_startup_idea(problem_reality, None, leverage_reality)
        
        # Should be identical
        self.assertEqual(state1.validation_class, state2.validation_class)
        self.assertEqual(state1.problem_validity, state2.problem_validity)
        self.assertEqual(state1.leverage_presence, state2.leverage_presence)
        
        # Explanation should exist
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 100)


if __name__ == '__main__':
    unittest.main()
