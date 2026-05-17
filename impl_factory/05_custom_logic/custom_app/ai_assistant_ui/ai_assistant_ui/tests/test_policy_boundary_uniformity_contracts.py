import unittest

from ai_assistant_ui.qwen_chat.policy_boundary_uniformity import (
	POLICY_BOUNDARY_UNIFORMITY_CONTRACT_TYPE,
	build_policy_boundary_uniformity_contract,
)


class PolicyBoundaryUniformityContractTests(unittest.TestCase):
	def test_visible_prediction_boundary_normalizes_to_prediction_contract(self):
		contract = build_policy_boundary_uniformity_contract(
			raw_message="Will the top customer default next month?",
			route="visible_context_followup",
			visible_authority_intent="prediction_boundary",
			selected_report_family="accounts_receivable_aging",
			entity_type="customer",
			evidence_scope="visible_rendered_table",
			visible_metric_lines=["Overdue Amount: 35,274,500 MMK"],
		)

		self.assertEqual(contract["type"], POLICY_BOUNDARY_UNIFORMITY_CONTRACT_TYPE)
		self.assertTrue(contract["boundary_applies"])
		self.assertEqual(contract["source"], "visible_context_authority_intent")
		self.assertEqual(contract["policy_intent_class"], "prediction")
		self.assertEqual(contract["policy_boundary"], "prediction_boundary")
		self.assertEqual(contract["allowed_answer_mode"], "bounded_current_evidence")
		self.assertTrue(contract["approved_model_required"])
		self.assertTrue(contract["approved_policy_required"])
		self.assertIn("unsupported_prediction", contract["blocked_claim_types"])
		self.assertIn("Overdue Amount: 35,274,500 MMK", contract["allowed_visible_facts"])

	def test_business_reasoning_policy_payload_normalizes_to_same_prediction_class(self):
		contract = build_policy_boundary_uniformity_contract(
			raw_message="Will this customer default next month?",
			route="business_reasoning_policy",
			business_policy_payload={
				"policy_state": "blocked",
				"requested_authority": "prediction",
				"blocked_variation": "predictive_default_probability",
				"safe_next_action": "Use an approved prediction model first.",
				"metric_rows": [
					{"label": "Overdue Amount", "value": "35,274,500 MMK"},
				],
				"authority_policy": {
					"required_evidence_metrics": ["payment_history", "credit_limit_utilization"],
					"required_governed_artifacts": ["accounts_receivable_aging"],
				},
				"authority_policy_gate": {
					"available_evidence_metrics": ["overdue_amount"],
					"missing_evidence_metrics": ["payment_history"],
				},
			},
			selected_report_family="customer_risk_as_of",
		)

		self.assertTrue(contract["boundary_applies"])
		self.assertEqual(contract["source"], "business_reasoning_authority_policy")
		self.assertEqual(contract["policy_intent_class"], "prediction")
		self.assertEqual(contract["policy_boundary"], "predictive_default_probability")
		self.assertEqual(contract["required_evidence_scope"]["required_metrics"], ["payment_history", "credit_limit_utilization"])
		self.assertEqual(contract["available_evidence_scope"]["missing_metrics"], ["payment_history"])
		self.assertIn("Overdue Amount: 35,274,500 MMK", contract["allowed_visible_facts"])

	def test_nbu_recommendation_boundary_normalizes_to_action_contract(self):
		contract = build_policy_boundary_uniformity_contract(
			route="natural_business_understanding",
			nbu_authority_plan={
				"authority_class": "recommendation",
				"authority_allowed": False,
				"approval_state": "blocked_by_authority_policy",
				"policy_artifact_required": "approved_policy_artifact_required",
			},
			selected_report_family="accounts_receivable_aging",
			entity_type="customer",
		)

		self.assertTrue(contract["boundary_applies"])
		self.assertEqual(contract["source"], "nbu_authority_plan")
		self.assertEqual(contract["policy_intent_class"], "recommendation_action")
		self.assertTrue(contract["approved_policy_required"])
		self.assertFalse(contract["approved_model_required"])
		self.assertIn("unsupported_recommendation", contract["blocked_claim_types"])

	def test_safe_visible_fact_contract_does_not_apply_boundary(self):
		contract = build_policy_boundary_uniformity_contract(
			route="visible_context_followup",
			visible_authority_intent="safe_visible_fact",
			selected_report_family="product_revenue_ranking",
			entity_type="item",
		)

		self.assertFalse(contract["boundary_applies"])
		self.assertEqual(contract["policy_intent_class"], "none")
		self.assertEqual(contract["policy_boundary"], "none")
		self.assertEqual(contract["allowed_answer_mode"], "allowed")
		self.assertEqual(contract["blocked_claim_types"], [])


if __name__ == "__main__":
	unittest.main()
