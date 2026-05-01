import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_decision import (
	build_nbu_conversation_action_decision,
)
from ai_assistant_ui.qwen_chat.natural_business_understanding_validation import (
	evaluate_nbu_candidate_against_context,
)


def _decision_for(candidate, context):
	validation, confidence = evaluate_nbu_candidate_against_context(
		candidate_payload=candidate,
		interpretation_context=context,
	)
	return build_nbu_conversation_action_decision(
		candidate_payload=candidate,
		validation_payload=validation.to_payload(),
		system_confidence_payload=confidence.to_payload(),
	)


class NaturalBusinessUnderstandingDecisionTests(unittest.TestCase):
	def test_current_artifact_followup_becomes_direct_answer_decision(self):
		candidate = {
			"candidate_id": "candidate-1",
			"intent_scope": "context_reference",
			"business_domain": "customer_risk",
			"target_reference": "rank_n",
			"candidate_composite_family_ids": ["customer_risk_as_of"],
			"requested_metrics": ["overdue_amount"],
			"evidence_need": "current_artifact_ok",
			"authority_class": "safe_explanation",
			"model_confidence": 0.9,
		}
		decision, evidence_plan, authority_plan = _decision_for(
			candidate,
			{
				"current_artifact": {
					"family_id": "customer_risk_as_of",
					"columns": ["customer", "overdue_amount"],
				},
				"metadata_context": {
					"composite_family_ids": ["customer_risk_as_of"],
					"business_domains": ["customer_risk"],
					"composite_families": [
						{
							"family_id": "customer_risk_as_of",
							"entity_grain": "customer",
							"allowed_primary_metrics": ["overdue_amount"],
							"activation_state": "active",
						}
					],
				},
			},
		)

		self.assertEqual(decision.action, "answer_from_current_artifact")
		self.assertEqual(decision.response_mode, "direct_answer")
		self.assertTrue(decision.safe_to_execute)
		self.assertTrue(evidence_plan.current_artifact_supported)
		self.assertTrue(authority_plan.authority_allowed)

	def test_fresh_governed_query_becomes_query_decision(self):
		candidate = {
			"candidate_id": "candidate-2",
			"intent_scope": "fresh_query",
			"business_domain": "collections",
			"candidate_capability_ids": ["sales_read", "collections_read"],
			"candidate_report_names": ["Sales Invoice List", "Payment Entry List"],
			"requested_metrics": ["collection_ratio"],
			"requested_dimensions": ["company"],
			"evidence_need": "needs_governed_requery",
			"authority_class": "safe_read",
			"model_confidence": 0.82,
		}
		decision, evidence_plan, _authority_plan = _decision_for(
			candidate,
			{
				"metadata_context": {
					"capability_ids": ["sales_read", "collections_read"],
					"report_names": ["Sales Invoice List", "Payment Entry List"],
					"business_domains": ["collections"],
					"governed_kpi_executions": [
						{
							"execution_id": "collection_ratio_execution",
							"source_capabilities": ["sales_read", "collections_read"],
							"source_reports": ["Sales Invoice List", "Payment Entry List"],
							"required_dimensions": ["company"],
							"value_metric_mapping": {"value_metric": "collection_ratio"},
							"activation_state": "active",
						}
					],
				},
			},
		)

		self.assertEqual(decision.action, "execute_fresh_governed_query")
		self.assertEqual(decision.response_mode, "governed_query")
		self.assertTrue(decision.requires_routing_change)
		self.assertTrue(evidence_plan.governed_requery_available)

	def test_prediction_request_becomes_boundary_decision(self):
		candidate = {
			"candidate_id": "candidate-3",
			"intent_scope": "followup",
			"business_domain": "customer_risk",
			"target_reference": "rank_n",
			"candidate_composite_family_ids": ["customer_risk_as_of"],
			"requested_action": "predict",
			"evidence_need": "needs_governed_requery",
			"authority_class": "prediction",
			"model_confidence": 0.95,
		}
		decision, _evidence_plan, authority_plan = _decision_for(
			candidate,
			{
				"current_artifact": {"family_id": "customer_risk_as_of"},
				"metadata_context": {
					"composite_family_ids": ["customer_risk_as_of"],
					"business_domains": ["customer_risk"],
				},
			},
		)

		self.assertEqual(decision.action, "reject_with_boundary")
		self.assertEqual(decision.response_mode, "boundary")
		self.assertFalse(decision.safe_to_execute)
		self.assertEqual(authority_plan.policy_artifact_required, "approved_policy_artifact_required")

	def test_context_conflict_becomes_clarification_decision(self):
		candidate = {
			"candidate_id": "candidate-4",
			"intent_scope": "context_reference",
			"business_domain": "customer_risk",
			"target_reference": "rank_n",
			"candidate_composite_family_ids": ["customer_risk_as_of"],
			"requested_metrics": ["overdue_amount"],
			"evidence_need": "current_artifact_ok",
			"authority_class": "safe_explanation",
			"model_confidence": 0.9,
		}
		decision, evidence_plan, _authority_plan = _decision_for(
			candidate,
			{
				"current_artifact": {
					"family_id": "balance_sheet",
					"columns": ["account", "amount"],
				},
				"metadata_context": {
					"composite_family_ids": ["customer_risk_as_of"],
					"business_domains": ["customer_risk"],
					"composite_families": [
						{
							"family_id": "customer_risk_as_of",
							"entity_grain": "customer",
							"allowed_primary_metrics": ["overdue_amount"],
							"activation_state": "active",
						}
					],
				},
			},
		)

		self.assertEqual(decision.action, "ask_clarification")
		self.assertEqual(decision.response_mode, "clarification")
		self.assertFalse(evidence_plan.current_artifact_supported)

	def test_out_of_scope_candidate_becomes_out_of_scope_decision(self):
		decision, _evidence_plan, _authority_plan = build_nbu_conversation_action_decision(
			candidate_payload={
				"candidate_id": "candidate-5",
				"intent_scope": "out_of_scope",
				"evidence_need": "out_of_scope",
				"authority_class": "unknown",
			},
			validation_payload={"status": "insufficient_confidence"},
			system_confidence_payload={"final_confidence": 0.0},
		)

		self.assertEqual(decision.action, "out_of_scope_response")
		self.assertEqual(decision.response_mode, "out_of_scope")


if __name__ == "__main__":
	unittest.main()
