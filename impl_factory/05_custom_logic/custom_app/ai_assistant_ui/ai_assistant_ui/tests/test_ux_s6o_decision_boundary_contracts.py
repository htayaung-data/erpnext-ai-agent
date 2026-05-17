import unittest

from ai_assistant_ui.qwen_chat.business_reasoning_policy import (
	build_business_reasoning_authority_policy_payload,
	render_business_reasoning_policy_boundary_answer,
)


class UXS6ODecisionBoundaryContracts(unittest.TestCase):
	def _ar_aging_artifact(self):
		return {
			"family_id": "aging",
			"source_reports": ["Accounts Receivable Summary"],
			"dimensions": {
				"aging_type": "accounts_receivable",
				"party_dimension_label": "Customer",
			},
			"sections": {
				"parties": [
					{
						"rank": 1,
						"party": "Capital Telecom (NPT)",
						"party_type": "Customer",
						"outstanding": 97309500,
						"total_due": 63654500,
						"bucket_31_60": 12776500,
						"bucket_61_90": 15480000,
						"bucket_91_120": 2974000,
						"bucket_121_above": 4044000,
					},
					{
						"rank": 2,
						"party": "Bayint Naung Wholesale Mobile",
						"party_type": "Customer",
						"outstanding": 95513000,
						"total_due": 69287000,
						"bucket_31_60": 33559000,
						"bucket_61_90": 0,
						"bucket_91_120": 0,
						"bucket_121_above": 0,
					},
				]
			},
		}

	def _ap_aging_artifact(self):
		return {
			"family_id": "aging",
			"source_reports": ["Accounts Payable Summary"],
			"dimensions": {
				"aging_type": "accounts_payable",
				"party_dimension_label": "Supplier",
			},
			"sections": {
				"parties": [
					{
						"rank": 1,
						"party": "Myanmar Tech Import Services",
						"party_type": "Supplier",
						"outstanding": 268298000,
						"total_due": 250568000,
						"overdue_amount": 193478000,
					},
					{
						"rank": 2,
						"party": "Sunflower Accessories Co.",
						"party_type": "Supplier",
						"outstanding": 228576500,
						"total_due": 222526500,
						"overdue_amount": 207736500,
					},
				]
			},
		}

	def _payload(self, message: str, artifact: dict):
		return build_business_reasoning_authority_policy_payload(
			raw_message=message,
			artifact_payload=artifact,
			grounded_turn={},
		)

	def test_ar_default_prediction_is_policy_blocked_from_report_family(self):
		payload = self._payload(
			"Is the top customer at risk of defaulting next month?",
			self._ar_aging_artifact(),
		)

		self.assertEqual(payload.get("policy_state"), "blocked")
		self.assertEqual(payload.get("requested_authority"), "prediction")
		self.assertEqual(payload.get("blocked_variation"), "predictive_default_probability")
		self.assertEqual(payload.get("selected_row", {}).get("party"), "Capital Telecom (NPT)")

		gate = payload.get("authority_policy_gate", {})
		self.assertNotIn("overdue_amount", gate.get("missing_evidence_metrics", []))
		self.assertNotIn("outstanding_amount", gate.get("missing_evidence_metrics", []))
		self.assertIn("payment_behavior", gate.get("missing_evidence_metrics", []))
		self.assertNotIn("accounts_receivable_aging", gate.get("missing_governed_artifacts", []))

		rendered = render_business_reasoning_policy_boundary_answer(payload)
		self.assertIn("does not authorize a predictive default probability", rendered)
		self.assertIn("Default Prediction Policy", rendered)
		self.assertIn("Rank 1: Capital Telecom (NPT)", rendered)
		self.assertIn("35,274,500 MMK", rendered)

	def test_ar_collection_priority_is_policy_blocked_but_current_facts_remain_visible(self):
		payload = self._payload(
			"Which customer should be prioritized for collection?",
			self._ar_aging_artifact(),
		)

		self.assertEqual(payload.get("policy_state"), "blocked")
		self.assertEqual(payload.get("requested_authority"), "recommendation")
		self.assertEqual(payload.get("blocked_variation"), "collection_recommendation")
		self.assertEqual(payload.get("selected_row", {}).get("party"), "Capital Telecom (NPT)")

		gate = payload.get("authority_policy_gate", {})
		self.assertNotIn("overdue_amount", gate.get("missing_evidence_metrics", []))
		self.assertNotIn("aging_buckets", gate.get("missing_evidence_metrics", []))
		self.assertNotIn("accounts_receivable_aging", gate.get("missing_governed_artifacts", []))

		rendered = render_business_reasoning_policy_boundary_answer(payload)
		self.assertIn("does not authorize a collection recommendation", rendered)
		self.assertIn("Customer Collection Priority Policy", rendered)
		self.assertIn("Outstanding Amount: 97,309,500 MMK", rendered)
		self.assertIn("Overdue Ratio: 36.25%", rendered)

	def test_ap_supplier_payment_priority_is_policy_blocked_from_same_aging_family(self):
		payload = self._payload(
			"Which supplier should we pay first?",
			self._ap_aging_artifact(),
		)

		self.assertEqual(payload.get("policy_state"), "blocked")
		self.assertEqual(payload.get("requested_authority"), "recommendation")
		self.assertEqual(payload.get("blocked_variation"), "supplier_payment_priority_recommendation")
		self.assertEqual(payload.get("selected_row", {}).get("party"), "Myanmar Tech Import Services")

		gate = payload.get("authority_policy_gate", {})
		self.assertNotIn("overdue_amount", gate.get("missing_evidence_metrics", []))
		self.assertIn("supplier_criticality", gate.get("missing_evidence_metrics", []))
		self.assertNotIn("accounts_payable_aging", gate.get("missing_governed_artifacts", []))

		rendered = render_business_reasoning_policy_boundary_answer(payload)
		self.assertIn("does not authorize a supplier payment-priority recommendation", rendered)
		self.assertIn("Supplier Payment Priority Policy", rendered)
		self.assertIn("193,478,000 MMK", rendered)

	def test_ar_change_driver_question_is_bounded_to_current_facts(self):
		payload = self._payload(
			"What factors led to the increase in risk for the first customer?",
			self._ar_aging_artifact(),
		)

		self.assertEqual(payload.get("policy_state"), "blocked")
		self.assertEqual(payload.get("requested_authority"), "driver_analysis")
		self.assertIn(payload.get("blocked_variation"), {"causal_root_cause_driver", "trend_change_driver"})

		rendered = render_business_reasoning_policy_boundary_answer(payload)
		self.assertIn("does not authorize", rendered)
		self.assertIn("This is a data-safety limit", rendered)

	def test_ordinary_overdue_explanation_remains_allowed(self):
		payload = self._payload(
			"Explain the overdue risk in this accounts receivable summary.",
			self._ar_aging_artifact(),
		)

		self.assertEqual(payload.get("policy_state"), "allowed")
		self.assertTrue(payload.get("allowed_to_answer"))
		self.assertFalse(payload.get("blocked_variation"))


if __name__ == "__main__":
	unittest.main()
