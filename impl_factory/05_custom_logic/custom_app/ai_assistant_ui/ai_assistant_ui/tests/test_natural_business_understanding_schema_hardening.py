import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_contracts import (
	ALLOWED_ACTION_DECISIONS,
)
from ai_assistant_ui.qwen_chat.natural_business_understanding_front_controller_cases import (
	list_nbu_front_controller_baseline_cases,
)
from ai_assistant_ui.qwen_chat.natural_business_understanding_response_renderer import (
	render_nbu_professional_response,
)
from ai_assistant_ui.qwen_chat.natural_business_understanding_schema_hardening import (
	list_nbu_action_schema_hardening_rules,
	nbu_confidence_threshold_for_action,
	validate_nbu_action_schema_hardening_rules,
	validate_nbu_front_controller_schema_hardening,
	validate_nbu_trace_schema_hardening,
)


class NaturalBusinessUnderstandingSchemaHardeningTests(unittest.TestCase):
	def test_action_schema_rules_cover_all_allowed_actions(self):
		validation = validate_nbu_action_schema_hardening_rules()

		self.assertTrue(validation["ok"], validation["errors"])
		self.assertEqual(
			{rule["action"] for rule in list_nbu_action_schema_hardening_rules()},
			set(ALLOWED_ACTION_DECISIONS),
		)

	def test_front_controller_baseline_actions_have_hardening_rules(self):
		validation = validate_nbu_front_controller_schema_hardening()

		self.assertTrue(validation["ok"], validation["errors"])
		self.assertGreaterEqual(validation["baseline_case_count"], 10)
		self.assertTrue(
			{
				case["expected_action"]
				for case in list_nbu_front_controller_baseline_cases()
			}.issubset(
				{rule["action"] for rule in list_nbu_action_schema_hardening_rules()}
			)
		)

	def test_current_artifact_answer_requires_resolved_context_and_visible_evidence(self):
		trace = {
			"selected_candidate_id": "candidate-1",
			"candidate_interpretations": [
				{
					"candidate_id": "candidate-1",
					"target_reference": "rank_n",
					"evidence_need": "current_artifact_ok",
					"authority_class": "safe_explanation",
				}
			],
			"system_confidence": {"final_confidence": 0.86},
			"conversation_action_decision": {
				"action": "answer_from_current_artifact",
				"response_mode": "direct_answer",
				"safe_to_execute": True,
			},
			"evidence_plan": {
				"evidence_need": "current_artifact_ok",
				"current_artifact_supported": True,
			},
			"authority_plan": {"authority_class": "safe_explanation"},
			"context_resolution": {"status": "resolved", "target_reference": "rank_n"},
		}

		validation = validate_nbu_trace_schema_hardening(trace)

		self.assertTrue(validation["ok"], validation["errors"])
		self.assertEqual(
			validation["min_final_confidence"],
			nbu_confidence_threshold_for_action("answer_from_current_artifact"),
		)

	def test_current_artifact_answer_fails_when_context_reference_is_unresolved(self):
		trace = {
			"selected_candidate_id": "candidate-1",
			"candidate_interpretations": [
				{
					"candidate_id": "candidate-1",
					"target_reference": "rank_n",
					"evidence_need": "current_artifact_ok",
					"authority_class": "safe_explanation",
				}
			],
			"system_confidence": {"final_confidence": 0.86},
			"conversation_action_decision": {
				"action": "answer_from_current_artifact",
				"response_mode": "direct_answer",
				"safe_to_execute": True,
			},
			"evidence_plan": {
				"evidence_need": "current_artifact_ok",
				"current_artifact_supported": True,
			},
			"authority_plan": {"authority_class": "safe_explanation"},
			"context_resolution": {"status": "ambiguous", "target_reference": "rank_n"},
		}

		validation = validate_nbu_trace_schema_hardening(trace)

		self.assertFalse(validation["ok"])
		self.assertIn("answer_from_current_artifact:context_reference_not_resolved:ambiguous", validation["errors"])

	def test_low_confidence_fresh_query_is_not_hardened_for_execution(self):
		trace = {
			"selected_candidate_id": "candidate-1",
			"candidate_interpretations": [
				{
					"candidate_id": "candidate-1",
					"evidence_need": "needs_governed_requery",
					"authority_class": "safe_read",
				}
			],
			"system_confidence": {"final_confidence": 0.30},
			"conversation_action_decision": {
				"action": "execute_fresh_governed_query",
				"response_mode": "governed_query",
				"requires_routing_change": True,
				"safe_to_execute": True,
			},
			"evidence_plan": {
				"evidence_need": "needs_governed_requery",
				"governed_requery_available": True,
			},
			"authority_plan": {"authority_class": "safe_read"},
			"context_resolution": {"status": "not_evaluated"},
			"governed_requery_plan": {"status": "ready_shadow", "shadow_execution_ready": True},
		}

		validation = validate_nbu_trace_schema_hardening(trace)

		self.assertFalse(validation["ok"])
		self.assertTrue(
			any(error.startswith("execute_fresh_governed_query:confidence_below_threshold") for error in validation["errors"])
		)

	def test_governed_requery_requires_ready_requery_support(self):
		trace = {
			"selected_candidate_id": "candidate-1",
			"candidate_interpretations": [
				{
					"candidate_id": "candidate-1",
					"target_reference": "selected_entity",
					"evidence_need": "needs_governed_requery",
					"authority_class": "governed_requery",
				}
			],
			"system_confidence": {"final_confidence": 0.76},
			"conversation_action_decision": {
				"action": "execute_governed_requery",
				"response_mode": "governed_query",
				"requires_routing_change": True,
				"safe_to_execute": True,
			},
			"evidence_plan": {
				"evidence_need": "needs_governed_requery",
				"governed_requery_available": False,
			},
			"authority_plan": {"authority_class": "governed_requery"},
			"context_resolution": {"status": "resolved", "target_reference": "selected_entity"},
			"governed_requery_plan": {"status": "unsupported", "shadow_execution_ready": False},
		}

		validation = validate_nbu_trace_schema_hardening(trace)

		self.assertFalse(validation["ok"])
		self.assertIn("execute_governed_requery:governed_requery_not_ready", validation["errors"])

	def test_boundary_action_rejects_direct_answer_response_mode(self):
		trace = {
			"selected_candidate_id": "candidate-1",
			"candidate_interpretations": [
				{
					"candidate_id": "candidate-1",
					"evidence_need": "needs_governed_requery",
					"authority_class": "prediction",
				}
			],
			"system_confidence": {"final_confidence": 0.90},
			"conversation_action_decision": {
				"action": "reject_with_boundary",
				"response_mode": "direct_answer",
			},
			"evidence_plan": {"evidence_need": "needs_governed_requery"},
			"authority_plan": {
				"authority_class": "prediction",
				"boundary_reason": "Prediction requires approved policy.",
			},
		}

		validation = validate_nbu_trace_schema_hardening(trace)

		self.assertFalse(validation["ok"])
		self.assertIn("reject_with_boundary:response_mode_not_allowed:direct_answer", validation["errors"])

	def test_boundary_renderer_output_passes_business_quality_gate(self):
		trace = {
			"selected_candidate_id": "candidate-1",
			"candidate_interpretations": [
				{
					"candidate_id": "candidate-1",
					"evidence_need": "needs_governed_requery",
					"authority_class": "prediction",
				}
			],
			"system_confidence": {"final_confidence": 0.90},
			"conversation_action_decision": {
				"action": "reject_with_boundary",
				"response_mode": "boundary",
			},
			"evidence_plan": {"evidence_need": "needs_governed_requery"},
			"authority_plan": {
				"authority_class": "prediction",
				"boundary_reason": "Prediction requires an approved company rule.",
			},
			"governed_requery_plan": {"status": "blocked_by_authority_policy"},
		}
		response = render_nbu_professional_response(trace)

		validation = validate_nbu_trace_schema_hardening(trace, response_payload=response)

		self.assertTrue(validation["ok"], validation["errors"])
		self.assertEqual(response["title"], "Decision Not Available Yet")

	def test_business_quality_gate_blocks_internal_user_text(self):
		trace = {
			"selected_candidate_id": "candidate-1",
			"candidate_interpretations": [
				{
					"candidate_id": "candidate-1",
					"evidence_need": "needs_governed_requery",
					"authority_class": "prediction",
				}
			],
			"system_confidence": {"final_confidence": 0.90},
			"conversation_action_decision": {
				"action": "reject_with_boundary",
				"response_mode": "boundary",
			},
			"evidence_plan": {"evidence_need": "needs_governed_requery"},
			"authority_plan": {
				"authority_class": "prediction",
				"boundary_reason": "Prediction requires an approved company rule.",
			},
		}

		validation = validate_nbu_trace_schema_hardening(
			trace,
			response_payload={
				"title": "Governed Boundary",
				"answer_text": "The contract cannot execute this runtime action.",
				"next_steps": [],
			},
		)

		self.assertFalse(validation["ok"])
		self.assertTrue(any(error.startswith("reject_with_boundary:user_text_violation") for error in validation["errors"]))


if __name__ == "__main__":
	unittest.main()
