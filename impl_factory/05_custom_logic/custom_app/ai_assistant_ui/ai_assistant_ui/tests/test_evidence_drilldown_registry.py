import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.evidence_drilldown_registry import build_governed_drilldown_plan
from ai_assistant_ui.qwen_chat.evidence_expansion_support import (
	build_evidence_expansion_plan,
	evidence_expansion_user_guidance,
)


def _drilldown_context(**overrides):
	context = {
		"answer_goal": "expand_detail",
		"evidence_depth": "drilldown_preferred",
		"business_role": "collector",
		"target_reference": "current_row",
		"risk_level": "bounded_consultation",
		"evidence_policy": "evidence_expansion_preferred",
		"answer_obligation": "expand_grounded_detail",
			"grounded_source": {
				"family_id": "accounts_receivable",
				"capability_id": "accounts_receivable_read",
				"source_name": "Accounts Receivable Aging",
			},
			"artifact_metrics": {
				"statement_type": "profit_and_loss",
			},
			"artifact_filters": {
				"company": "Mingalar Mobile Distribution Co., Ltd.",
			},
			"artifact_period": {
				"from_date": "2026-04-01",
				"to_date": "2026-05-08",
			},
		}
	context.update(overrides)
	return context


def _entity_activation(entity_grain: str, *, can_execute: bool = True):
	return {
		"scope_id": f"{entity_grain}_scope",
		"entity_grain": entity_grain,
		"entity_label": entity_grain.replace("_", " ").title(),
		"entity_plural_label": f"{entity_grain.replace('_', ' ').title()}s",
		"identity_field": entity_grain,
		"display_field": f"{entity_grain}_name",
		"runtime_policy": {"can_execute": can_execute},
	}


class EvidenceDrilldownRegistryTests(unittest.TestCase):
	@patch("ai_assistant_ui.qwen_chat.evidence_drilldown_registry.list_active_entity_detail_scope_activations")
	def test_typed_detail_intent_maps_entity_row_to_executable_registry_source(self, activations):
		activations.return_value = [_entity_activation("customer")]

		plan = build_governed_drilldown_plan(
			grounding_context=_drilldown_context(),
			focused_row={
				"Customer": "35th Street Mobile Wholesale",
				"Outstanding Amount": "84,837,000",
				"Overdue Amount": "58,212,000",
			},
		)

		self.assertEqual(plan["type"], "qwen_governed_evidence_drilldown_plan")
		self.assertEqual(plan["status"], "entity_detail_available")
		self.assertTrue(plan["can_execute"])
		self.assertEqual(plan["execution_mode"], "entity_detail")
		self.assertEqual(plan["target_entity"]["entity_type"], "customer")
		self.assertEqual(plan["target_entity"]["entity_label"], "35th Street Mobile Wholesale")

	@patch("ai_assistant_ui.qwen_chat.evidence_drilldown_registry.list_active_entity_detail_scope_activations")
	def test_current_result_only_intent_does_not_open_drilldown_registry(self, activations):
		plan = build_governed_drilldown_plan(
			grounding_context=_drilldown_context(
				answer_goal="explain",
				evidence_depth="current_result_only",
				evidence_policy="current_result_only",
				answer_obligation="explain_grounded_meaning",
			),
			focused_row={"Customer": "Capital Telecom (NPT)", "Outstanding Amount": "97,309,500"},
		)

		self.assertEqual(plan["status"], "not_applicable")
		self.assertFalse(plan["can_execute"])
		activations.assert_not_called()

	@patch("ai_assistant_ui.qwen_chat.evidence_drilldown_registry.list_active_entity_detail_scope_activations")
	def test_financial_cogs_row_maps_to_registered_source_detail_report(self, activations):
		activations.return_value = [_entity_activation("customer"), _entity_activation("supplier")]

		plan = build_governed_drilldown_plan(
			grounding_context=_drilldown_context(
				business_role="controller",
				grounded_source={
					"family_id": "financial_statement",
					"capability_id": "financial_statement_read",
					"source_name": "Profit and Loss Statement",
				},
			),
			focused_row={
				"Account": "Cost of Goods Sold - MMOB",
				"Account Name": "Cost of Goods Sold",
				"2026": "65,245,820.70",
				"Currency": "MMK",
			},
		)

		self.assertEqual(plan["status"], "source_detail_available")
		self.assertTrue(plan["can_execute"])
		self.assertEqual(plan["execution_mode"], "source_detail_report")
		self.assertEqual(plan["drilldown_mode"], "source_detail")
		self.assertEqual(plan["target_report"]["report_name"], "GL Entry Account Detail")
		self.assertEqual(plan["target_report"]["filters"]["account"], "Cost of Goods Sold - MMOB")
		self.assertNotIn("target_entity", plan)

	@patch("ai_assistant_ui.qwen_chat.evidence_drilldown_registry.list_active_entity_detail_scope_activations")
	def test_inactive_entity_activation_fails_closed(self, activations):
		activations.return_value = [_entity_activation("customer", can_execute=False)]

		plan = build_governed_drilldown_plan(
			grounding_context=_drilldown_context(),
			focused_row={"Customer": "35th Street Mobile Wholesale", "Amount": "84,837,000"},
		)

		self.assertEqual(plan["status"], "source_detail_required")
		self.assertFalse(plan["can_execute"])
		self.assertNotIn("target_entity", plan)

	@patch("ai_assistant_ui.qwen_chat.evidence_expansion_support.list_active_entity_detail_scope_activations")
	def test_compatibility_adapter_preserves_existing_expansion_shape(self, activations):
		activations.return_value = [_entity_activation("supplier")]

		plan = build_evidence_expansion_plan(
			grounding_context=_drilldown_context(
				business_role="buyer",
				grounded_source={
					"family_id": "accounts_payable",
					"capability_id": "accounts_payable_read",
					"source_name": "Accounts Payable Aging",
				},
			),
			focused_row={"Supplier": "Sunflower Accessories Co.", "Outstanding Amount": "222,526,500"},
		)

		self.assertEqual(plan["type"], "qwen_evidence_expansion_plan")
		self.assertEqual(plan["status"], "entity_detail_available")
		self.assertTrue(plan["can_execute_expansion"])
		self.assertIn("governed_drilldown_plan", plan)
		self.assertEqual(plan["target_entity"]["entity_type"], "supplier")

	@patch("ai_assistant_ui.qwen_chat.evidence_expansion_support.list_active_entity_detail_scope_activations")
	def test_compatibility_adapter_keeps_summary_row_non_executable(self, activations):
		activations.return_value = [_entity_activation("customer")]

		plan = build_evidence_expansion_plan(
			grounding_context=_drilldown_context(),
			focused_row={"Account": "Cost of Goods Sold - MMOB", "2026": "65,245,820.70"},
		)

		self.assertEqual(plan["status"], "summary_row_only")
		self.assertFalse(plan["can_execute_expansion"])
		guidance = evidence_expansion_user_guidance(plan)
		self.assertIn("business interpretation", guidance)
		self.assertIn("approved ERP detail view", guidance)
		self.assertNotIn("runtime", guidance.lower())
		self.assertNotIn("contract", guidance.lower())


if __name__ == "__main__":
	unittest.main()
