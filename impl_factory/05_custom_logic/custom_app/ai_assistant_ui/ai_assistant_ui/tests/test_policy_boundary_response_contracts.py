import unittest

from ai_assistant_ui.qwen_chat.policy_boundary_response import (
	POLICY_BOUNDARY_RESPONSE_CONTRACT_TYPE,
	render_policy_boundary_response,
)
from ai_assistant_ui.qwen_chat.policy_boundary_uniformity import build_policy_boundary_uniformity_contract


class PolicyBoundaryResponseContractTests(unittest.TestCase):
	def assertNoInternalLanguage(self, text):
		lowered = text.lower()
		for term in (
			"qwen",
			"contract",
			"ledger",
			"trace",
			"policy boundary",
			"unsupported claim",
			"blocked variation",
			"governed",
		):
			self.assertNotIn(term, lowered)

	def _render(self, intent):
		contract = build_policy_boundary_uniformity_contract(
			route="test",
			visible_authority_intent={
				"prediction": "prediction_boundary",
				"recommendation_action": "recommendation_boundary",
				"cause_attribution": "causal_boundary",
			}.get(intent, ""),
			nbu_authority_plan={} if intent in {"prediction", "recommendation_action", "cause_attribution"} else {
				"authority_class": intent,
				"approval_state": "blocked_by_authority_policy",
			},
			selected_report_family="accounts_receivable_aging",
			entity_type="customer",
			evidence_scope="visible_rendered_table",
			visible_metric_lines=["Outstanding Amount: 95,513,000 MMK", "Overdue Amount: 33,559,000 MMK"],
		)
		return render_policy_boundary_response(
			contract,
			rank_text="Rank 2",
			entity_label="Bayint Naung Wholesale Mobile",
		)

	def test_prediction_boundary_uses_enterprise_natural_language(self):
		response = self._render("prediction")

		self.assertEqual(response["type"], POLICY_BOUNDARY_RESPONSE_CONTRACT_TYPE)
		self.assertEqual(response["title"], "Evidence Limit")
		self.assertEqual(response["boundary_class"], "prediction")
		self.assertIn("can't forecast", response["answer_text"])
		self.assertIn("Bayint Naung Wholesale Mobile", response["answer_text"])
		self.assertIn("Outstanding Amount: 95,513,000 MMK", response["answer_text"])
		self.assertNotIn("Decision Not Available Yet", response["answer_text"])
		self.assertNoInternalLanguage(response["answer_text"])

	def test_recommendation_boundary_uses_same_contract_shape(self):
		response = self._render("recommendation_action")

		self.assertEqual(response["title"], "Evidence Limit")
		self.assertEqual(response["boundary_class"], "recommendation")
		self.assertIn("can't recommend", response["answer_text"])
		self.assertIn("approved company decision rule", response["answer_text"])
		self.assertNoInternalLanguage(response["answer_text"])

	def test_cause_boundary_uses_same_contract_shape(self):
		response = self._render("cause_attribution")

		self.assertEqual(response["title"], "Evidence Limit")
		self.assertEqual(response["boundary_class"], "cause")
		self.assertIn("can't attribute cause", response["answer_text"])
		self.assertIn("trend or event-history evidence", response["answer_text"])
		self.assertNoInternalLanguage(response["answer_text"])


if __name__ == "__main__":
	unittest.main()
