import sys
import types
import unittest


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

from ai_assistant_ui.qwen_chat.followup_interpreter import assess_context_isolation


class TestFollowupInterpreterContracts(unittest.TestCase):
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
