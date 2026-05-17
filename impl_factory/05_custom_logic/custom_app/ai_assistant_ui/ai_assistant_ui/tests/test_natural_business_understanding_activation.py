import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_activation import (
	build_nbu_activation_assessment,
)


class NaturalBusinessUnderstandingActivationTests(unittest.TestCase):
	def test_boundary_response_is_eligible_for_presentation_only_activation(self):
		assessment = build_nbu_activation_assessment(
			{
				"shadow_mode": True,
				"candidate_interpretations": [{"candidate_id": "candidate-1"}],
				"system_confidence": {"final_confidence": 0.86},
				"validation_result": {"status": "blocked_by_authority_policy"},
				"conversation_action_decision": {
					"action": "reject_with_boundary",
					"response_mode": "boundary",
				},
				"professional_response": {
					"action": "reject_with_boundary",
					"response_mode": "boundary",
					"safe_to_show": True,
					"quality_warnings": [],
				},
				"governed_requery_plan": {"status": "blocked_by_authority_policy"},
			}
		)

		self.assertEqual(assessment["activation_state"], "eligible_shadow")
		self.assertEqual(assessment["activation_mode"], "presentation_only")
		self.assertTrue(assessment["eligible_for_controlled_activation"])
		self.assertFalse(assessment["live_execution_enabled"])
		self.assertEqual(assessment["blockers"], [])

	def test_quality_warnings_block_presentation_activation(self):
		assessment = build_nbu_activation_assessment(
			{
				"shadow_mode": True,
				"candidate_interpretations": [{"candidate_id": "candidate-1"}],
				"system_confidence": {"final_confidence": 0.8},
				"validation_result": {"status": "accepted"},
				"conversation_action_decision": {
					"action": "ask_clarification",
					"response_mode": "clarification",
				},
				"professional_response": {
					"action": "ask_clarification",
					"response_mode": "clarification",
					"safe_to_show": True,
					"quality_warnings": ["user_text_internal_term:shadow"],
				},
				"governed_requery_plan": {"status": "needs_clarification"},
			}
		)

		self.assertEqual(assessment["activation_state"], "blocked_shadow")
		self.assertFalse(assessment["eligible_for_controlled_activation"])
		self.assertIn("professional_response_quality_warnings", assessment["blockers"])
		self.assertIn("user_text_internal_term:shadow", assessment["warnings"])

	def test_current_artifact_direct_answer_is_delegated_to_existing_renderer(self):
		assessment = build_nbu_activation_assessment(
			{
				"shadow_mode": True,
				"candidate_interpretations": [{"candidate_id": "candidate-1"}],
				"system_confidence": {"final_confidence": 0.92},
				"validation_result": {"status": "accepted"},
				"conversation_action_decision": {
					"action": "answer_from_current_artifact",
					"response_mode": "direct_answer",
				},
				"professional_response": {
					"action": "answer_from_current_artifact",
					"response_mode": "direct_answer",
					"safe_to_show": False,
					"quality_warnings": [],
				},
				"governed_requery_plan": {"status": "not_required"},
			}
		)

		self.assertEqual(assessment["activation_state"], "blocked_shadow")
		self.assertIn("delegated_to_existing_artifact_renderer", assessment["blockers"])
		self.assertIn("professional_response_not_safe_to_show", assessment["blockers"])

	def test_governed_requery_execution_is_not_presentation_activated(self):
		assessment = build_nbu_activation_assessment(
			{
				"shadow_mode": True,
				"candidate_interpretations": [{"candidate_id": "candidate-1"}],
				"system_confidence": {"final_confidence": 0.84},
				"validation_result": {"status": "accepted"},
				"conversation_action_decision": {
					"action": "execute_governed_requery",
					"response_mode": "governed_query",
				},
				"professional_response": {
					"action": "execute_governed_requery",
					"response_mode": "governed_query",
					"safe_to_show": True,
					"quality_warnings": [],
				},
				"governed_requery_plan": {"status": "ready_shadow"},
			}
		)

		self.assertEqual(assessment["activation_state"], "blocked_shadow")
		self.assertIn("requires_execution_lane_activation", assessment["blockers"])
		self.assertFalse(assessment["eligible_for_controlled_activation"])


if __name__ == "__main__":
	unittest.main()
