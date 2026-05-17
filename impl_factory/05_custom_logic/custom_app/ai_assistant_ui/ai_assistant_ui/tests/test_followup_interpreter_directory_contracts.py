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


class TestFollowupInterpreterDirectoryContracts(unittest.TestCase):
	def setUp(self):
		self.customer_directory_grounded_turn = {
			"grounded": True,
			"source_name": "Customer Master List",
			"artifact_family_id": "master_data_directory",
			"dimensions": {"entity_type": "customer"},
			"metrics": {},
			"known_entities": [],
		}
		self.item_directory_grounded_turn = {
			"grounded": True,
			"source_name": "Item Master List",
			"artifact_family_id": "master_data_directory",
			"dimensions": {"entity_type": "item"},
			"metrics": {},
			"known_entities": [],
		}

	def test_master_data_directory_breaks_out_for_entity_grain_switch(self):
		decision = assess_context_isolation(
			"give me some supplier list",
			grounded_turn=self.customer_directory_grounded_turn,
		)
		self.assertTrue(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)
		self.assertIn("different entity list", decision.reason)

	def test_item_master_data_directory_keeps_same_grain_profile_followup_grounded(self):
		decision = assess_context_isolation(
			"tell me more about Demo Item",
			grounded_turn=self.item_directory_grounded_turn,
		)
		self.assertFalse(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)

	def test_item_master_data_directory_keeps_product_alias_followup_grounded(self):
		decision = assess_context_isolation(
			"show product names only",
			grounded_turn=self.item_directory_grounded_turn,
		)
		self.assertFalse(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)

	def test_item_master_data_directory_keeps_projection_followup_grounded(self):
		decision = assess_context_isolation(
			"show item and brand only",
			grounded_turn=self.item_directory_grounded_turn,
		)
		self.assertFalse(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)

	def test_item_master_data_directory_breaks_out_for_customer_list_switch(self):
		decision = assess_context_isolation(
			"give me some customer list",
			grounded_turn=self.item_directory_grounded_turn,
		)
		self.assertTrue(decision.force_new_query)
		self.assertFalse(decision.out_of_scope)
		self.assertIn("different entity list", decision.reason)


if __name__ == "__main__":
	unittest.main()
