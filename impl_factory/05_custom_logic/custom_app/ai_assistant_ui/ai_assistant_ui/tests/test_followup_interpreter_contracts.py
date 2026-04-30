import sys
import types
import unittest
from unittest.mock import patch

fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.followup_interpreter import (
	ArtifactContextSignal,
	_entity_navigation_breakout_signal,
	_same_grain_master_data_followup_signal,
	assess_context_isolation,
	build_followup_boundary_contract_from_context,
)


class FollowupInterpreterContractsTests(unittest.TestCase):
	def setUp(self):
		self.customer_detail_grounded_turn = {
			"grounded": True,
			"source_name": "Customer Detail",
			"artifact_family_id": "entity_detail",
			"dimensions": ["Customer"],
			"metrics": [],
			"known_entities": [
				{
					"entity_type": "customer",
					"name": "Zegyo Mobile Supply House",
					"code": "Zegyo Mobile Supply House",
				}
			],
		}
		self.financial_statement_grounded_turn = {
			"grounded": True,
			"source_name": "Profit and Loss Statement",
			"artifact_family_id": "financial_statement",
			"dimensions": ["Account", "Section"],
			"metrics": ["Total Income", "Total Expense", "Net Profit"],
			"known_entities": [],
		}

	def test_same_grain_master_data_followup_accepts_customer_master_listing_family(self):
		artifact_signal = ArtifactContextSignal(
			has_grounded_turn=True,
			report_name="Customer Master List",
			family_id="customer_master_list",
			context_concepts=set(),
			available_dimensions={},
			available_metrics={},
			available_metric_keys=set(),
		)
		with patch(
			"ai_assistant_ui.qwen_chat.followup_interpreter.entity_grain_for_report_name",
			return_value="customer",
		):
			self.assertTrue(
				_same_grain_master_data_followup_signal(
					"show me customers",
					artifact_signal=artifact_signal,
				)
			)

	def test_entity_navigation_breakout_does_not_force_fresh_query_for_same_customer_master_listing(self):
		artifact_signal = ArtifactContextSignal(
			has_grounded_turn=True,
			report_name="Customer Master List",
			family_id="customer_master_list",
			context_concepts={"customer"},
			available_dimensions={},
			available_metrics={},
			available_metric_keys=set(),
		)
		with patch(
			"ai_assistant_ui.qwen_chat.followup_interpreter.entity_grain_for_report_name",
			return_value="customer",
		):
			self.assertFalse(
				_entity_navigation_breakout_signal(
					"show me customers",
					artifact_signal=artifact_signal,
					grounded_turn={"known_entities": [], "dimensions": ["customer"]},
				)
			)

	def test_entity_detail_item_followup_boundary_uses_extracted_context_domain_helper(self):
		contract = build_followup_boundary_contract_from_context(
			"how many stocks do we have for that product, and in which warehouse?",
			request_id="item-stock-followup-boundary",
			session_id="session-1",
			grounded_turn={
				"grounded": True,
				"artifact_family_id": "entity_detail",
				"source_name": "Item Detail",
				"known_entities": [
					{"entity_type": "item", "entity_key": "ACC-CBL-UGR-TC2M"}
				],
				"dimensions": ["item"],
				"metrics": ["balance_qty"],
			},
		)

		payload = contract.to_payload()
		self.assertEqual(payload.get("source_family_id"), "entity_detail")
		self.assertIn("product", payload.get("grounded_context_domains") or [])
		self.assertIn("inventory", payload.get("grounded_context_domains") or [])

	def test_composite_declared_entity_detail_family_keeps_customer_followup_grounded(self):
		with patch(
			"ai_assistant_ui.qwen_chat.followup_entity_domain_support.list_composite_family_specs",
			return_value=[
				{
					"family_id": "customer_risk_as_of",
					"subject_alias_value": "customer",
					"entity_grain": "customer",
					"local_followup_family_id": "customer_entity_detail",
					"followup_affordances": ["customer_detail", "aging_breakdown"],
				}
			],
		):
			contract = build_followup_boundary_contract_from_context(
				"why is this customer risky?",
				request_id="risk-customer-followup",
				session_id="session-1",
				grounded_turn={
					"grounded": True,
					"artifact_family_id": "customer_entity_detail",
					"source_name": "Customer Risk As-Of",
					"known_entities": [
						{
							"entity_type": "customer",
							"name": "Ko Nay Lin Mobile Center",
							"rank": 1,
						}
					],
					"dimensions": ["Customer"],
					"metrics": ["Overdue Amount", "Outstanding Amount", "Overdue Ratio"],
				},
			)

		payload = contract.to_payload()
		self.assertEqual(payload.get("source_family_id"), "customer_entity_detail")
		self.assertTrue(payload.get("grounded_followup_supported"))
		self.assertIn("customer", payload.get("grounded_context_domains") or [])
		decision = assess_context_isolation(
			"why is this customer risky?",
			grounded_turn={
				"grounded": True,
				"artifact_family_id": "customer_entity_detail",
				"source_name": "Customer Risk As-Of",
				"known_entities": [
					{
						"entity_type": "customer",
						"name": "Ko Nay Lin Mobile Center",
						"rank": 1,
					}
				],
				"dimensions": ["Customer"],
				"metrics": ["Overdue Amount", "Outstanding Amount", "Overdue Ratio"],
			},
		)
		self.assertFalse(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)

	def test_entity_detail_breaks_out_for_self_contained_customer_resolution_request(self):
		decision = assess_context_isolation(
			"do u have customer name similar to Nay Lin Mobile",
			grounded_turn=self.customer_detail_grounded_turn,
		)
		self.assertTrue(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)
		self.assertIn("entity-navigation", decision.reason)

	def test_entity_detail_breaks_out_for_supplier_directory_request(self):
		decision = assess_context_isolation(
			"give me some supplier names",
			grounded_turn=self.customer_detail_grounded_turn,
		)
		self.assertTrue(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)
		self.assertIn("entity-navigation", decision.reason)

	def test_entity_detail_keeps_deictic_customer_followup_grounded(self):
		decision = assess_context_isolation(
			"what is this customer's tenure?",
			grounded_turn=self.customer_detail_grounded_turn,
		)
		self.assertFalse(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)

	def test_financial_statement_breaks_out_for_top_level_statement_request(self):
		decision = assess_context_isolation(
			"show me statement",
			grounded_turn=self.financial_statement_grounded_turn,
		)
		self.assertTrue(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)
		self.assertIn("fresh governed erp question", decision.reason.lower())

	def test_financial_statement_keeps_deictic_line_question_grounded(self):
		decision = assess_context_isolation(
			"what is the top expense line in this statement?",
			grounded_turn=self.financial_statement_grounded_turn,
		)
		self.assertFalse(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)

	def test_financial_statement_breaks_out_for_direct_balance_sheet_request(self):
		decision = assess_context_isolation(
			"Balance Sheet",
			grounded_turn=self.financial_statement_grounded_turn,
		)
		self.assertTrue(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)

	def test_financial_statement_breaks_out_for_direct_statement_alias_request(self):
		decision = assess_context_isolation(
			"P & L",
			grounded_turn=self.financial_statement_grounded_turn,
		)
		self.assertTrue(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)


if __name__ == "__main__":
	unittest.main()
