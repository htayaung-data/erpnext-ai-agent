import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.evidence_expansion_support import (
	build_evidence_expansion_plan,
	evidence_expansion_user_guidance,
)


def _expansion_context():
	return {
		"evidence_policy": "evidence_expansion_preferred",
		"answer_obligation": "expand_grounded_detail",
		"grounded_source": {
			"family_id": "accounts_receivable",
			"source_name": "Accounts Receivable Aging",
		},
	}


def _entity_activation(entity_grain: str):
	return {
		"scope_id": f"{entity_grain}_scope",
		"entity_grain": entity_grain,
		"entity_label": entity_grain.replace("_", " ").title(),
		"entity_plural_label": f"{entity_grain.replace('_', ' ').title()}s",
		"identity_field": entity_grain,
		"display_field": f"{entity_grain}_name",
		"runtime_policy": {"can_execute": True},
	}


class EvidenceExpansionSupportTests(unittest.TestCase):
	@patch("ai_assistant_ui.qwen_chat.evidence_expansion_support.list_active_entity_detail_scope_activations")
	def test_entity_row_maps_to_executable_detail_from_registry(self, activations):
		activations.return_value = [_entity_activation("customer")]

		plan = build_evidence_expansion_plan(
			grounding_context=_expansion_context(),
			focused_row={
				"Customer": "35th Street Mobile Wholesale",
				"Outstanding Amount": "84,837,000",
				"Overdue Amount": "58,212,000",
			},
		)

		self.assertEqual(plan["status"], "entity_detail_available")
		self.assertTrue(plan["can_execute_expansion"])
		self.assertEqual(plan["target_entity"]["entity_type"], "customer")
		self.assertEqual(plan["target_entity"]["entity_label"], "35th Street Mobile Wholesale")

	@patch("ai_assistant_ui.qwen_chat.evidence_expansion_support.list_active_entity_detail_scope_activations")
	def test_entity_expansion_is_cross_family_registry_driven(self, activations):
		cases = [
			("supplier", "Supplier", "Sunflower Accessories Co."),
			("item", "Item", "Xiaomi Redmi Note 13"),
			("sales_invoice", "Sales Invoice", "ACC-SINV-2026-00205"),
		]
		activations.return_value = [_entity_activation(grain) for grain, _column, _label in cases]

		for entity_grain, column, label in cases:
			with self.subTest(entity_grain=entity_grain):
				plan = build_evidence_expansion_plan(
					grounding_context=_expansion_context(),
					focused_row={
						column: label,
						"Amount": "10,000",
					},
				)

				self.assertEqual(plan["status"], "entity_detail_available")
				self.assertTrue(plan["can_execute_expansion"])
				self.assertEqual(plan["target_entity"]["entity_type"], entity_grain)
				self.assertEqual(plan["target_entity"]["entity_label"], label)

	@patch("ai_assistant_ui.qwen_chat.evidence_expansion_support.list_active_entity_detail_scope_activations")
	def test_summary_line_does_not_claim_unproven_detail_source(self, activations):
		activations.return_value = [_entity_activation("customer"), _entity_activation("supplier")]

		plan = build_evidence_expansion_plan(
			grounding_context=_expansion_context(),
			focused_row={
				"Account": "Cost of Goods Sold - MMOB",
				"Account Name": "Cost of Goods Sold",
				"2026": "51,764,064.95",
				"Currency": "MMK",
			},
		)

		self.assertEqual(plan["status"], "summary_row_only")
		self.assertFalse(plan["can_execute_expansion"])
		self.assertNotIn("target_entity", plan)
		guidance = evidence_expansion_user_guidance(plan)
		self.assertIn("supports impact analysis", guidance)
		self.assertIn("approved ERP detail view", guidance)
		self.assertNotIn("runtime", guidance.lower())
		self.assertNotIn("contract", guidance.lower())

	@patch("ai_assistant_ui.qwen_chat.evidence_expansion_support.list_active_entity_detail_scope_activations")
	def test_inactive_or_unsupported_entity_grain_is_not_treated_as_executable(self, activations):
		activations.return_value = [
			{
				"entity_grain": "account",
				"entity_label": "Account",
				"identity_field": "account",
				"runtime_policy": {"can_execute": True},
			}
		]

		plan = build_evidence_expansion_plan(
			grounding_context=_expansion_context(),
			focused_row={
				"Account": "Cost of Goods Sold - MMOB",
				"2026": "51,764,064.95",
			},
		)

		self.assertEqual(plan["status"], "summary_row_only")
		self.assertFalse(plan["can_execute_expansion"])

	@patch("ai_assistant_ui.qwen_chat.evidence_expansion_support.list_active_entity_detail_scope_activations")
	def test_non_expansion_intent_does_not_run_detail_planning(self, activations):
		plan = build_evidence_expansion_plan(
			grounding_context={
				"evidence_policy": "current_result_only",
				"answer_obligation": "explain_grounded_meaning",
			},
			focused_row={"Customer": "Capital Telecom (NPT)", "Outstanding Amount": "97,309,500"},
		)

		self.assertEqual(plan["status"], "not_applicable")
		self.assertFalse(plan["can_execute_expansion"])
		activations.assert_not_called()


if __name__ == "__main__":
	unittest.main()
