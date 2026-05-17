import unittest

from ai_assistant_ui.qwen_chat.consultant_drilldown_playbook_registry import (
	build_consultant_drilldown_playbook_plan,
	consultant_drilldown_playbook_registry,
)


class ConsultantDrilldownPlaybookRegistryTests(unittest.TestCase):
	def test_registry_selects_working_capital_side_by_side_only_when_feature_and_source_match(self):
		plan = build_consultant_drilldown_playbook_plan(
			source_signature={
				"family_id": "working_capital",
				"capability_id": "working_capital_health_read",
				"source_report_count": 2,
				"composite_grounding": True,
			},
			evidence_features={"features": ["working_capital_summary"]},
		)

		self.assertEqual(plan["status"], "executable_playbook_available")
		self.assertTrue(plan["can_execute"])
		self.assertEqual(plan["playbook_id"], "working_capital_side_by_side_pressure")
		self.assertEqual(plan["next_action"]["action_id"], "compare_ar_ap_pressure_side_by_side")
		self.assertEqual(plan["next_action"]["execution_mode"], "current_governed_artifact")
		self.assertIn("customer collection pressure", plan["next_action"]["user_prompt"])
		self.assertNotIn("runtime", plan["next_action"]["user_prompt"].lower())
		self.assertNotIn("contract", plan["next_action"]["user_prompt"].lower())

	def test_registry_does_not_offer_working_capital_action_without_matching_source(self):
		plan = build_consultant_drilldown_playbook_plan(
			source_signature={
				"family_id": "sales",
				"capability_id": "sales_read",
				"source_report_count": 1,
				"composite_grounding": False,
			},
			evidence_features={"features": ["working_capital_summary"]},
		)

		self.assertEqual(plan["status"], "no_executable_playbook")
		self.assertFalse(plan["can_execute"])
		self.assertNotIn("next_action", plan)

	def test_registry_selects_customer_party_comparison_from_capability_scope(self):
		plan = build_consultant_drilldown_playbook_plan(
			source_signature={
				"family_id": "accounts_receivable",
				"capability_id": "accounts_receivable_read",
				"source_report_count": 1,
				"composite_grounding": False,
			},
			evidence_features={"features": ["ranked_parties"]},
		)

		self.assertEqual(plan["status"], "executable_playbook_available")
		self.assertEqual(plan["next_action"]["action_id"], "compare_listed_parties_by_overdue_and_intensity")
		self.assertEqual(plan["next_action"]["entity_scope"], "customers")
		self.assertIn("listed customers", plan["next_action"]["user_prompt"])
		self.assertEqual(plan["next_action"]["comparison_metrics"], ["overdue_amount", "overdue_intensity"])

	def test_registry_selects_supplier_party_comparison_from_capability_scope(self):
		plan = build_consultant_drilldown_playbook_plan(
			source_signature={
				"family_id": "accounts_payable",
				"capability_id": "accounts_payable_read",
				"source_report_count": 1,
				"composite_grounding": False,
			},
			evidence_features={"features": ["ranked_parties"]},
		)

		self.assertEqual(plan["status"], "executable_playbook_available")
		self.assertEqual(plan["next_action"]["entity_scope"], "suppliers")
		self.assertIn("listed suppliers", plan["next_action"]["user_prompt"])

	def test_registry_fails_closed_without_governed_artifact_features(self):
		plan = build_consultant_drilldown_playbook_plan(
			source_signature={
				"family_id": "accounts_receivable",
				"capability_id": "accounts_receivable_read",
				"source_report_count": 1,
				"composite_grounding": False,
			},
			evidence_features={"features": []},
		)

		self.assertEqual(plan["status"], "no_executable_playbook")
		self.assertFalse(plan["can_execute"])

	def test_registry_file_is_loaded_as_governed_playbook_metadata(self):
		registry = consultant_drilldown_playbook_registry()

		self.assertEqual(registry["type"], "qwen_consultant_drilldown_playbook_registry")
		self.assertGreaterEqual(len(registry.get("playbooks") or []), 2)
		self.assertIn("capability_entity_scopes", registry)


if __name__ == "__main__":
	unittest.main()
