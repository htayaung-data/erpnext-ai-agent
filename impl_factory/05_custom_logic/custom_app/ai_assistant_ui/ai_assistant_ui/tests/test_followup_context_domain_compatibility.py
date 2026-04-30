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

from ai_assistant_ui.qwen_chat.followup_interpreter import (
	assess_context_isolation,
	build_followup_boundary_contract_from_context,
)


class TestFollowupContextDomainCompatibility(unittest.TestCase):
	def test_collection_priority_breaks_out_from_supplier_master_listing(self):
		grounded_turn = {
			"grounded": True,
			"source_name": "Supplier Master List",
			"artifact_family_id": "master_data_directory",
			"artifact_source_reports": ["Supplier Master List"],
		}

		boundary = build_followup_boundary_contract_from_context(
			"who should we collect from first?",
			grounded_turn=grounded_turn,
		)
		scope = assess_context_isolation(
			"who should we collect from first?",
			grounded_turn=grounded_turn,
		)

		self.assertIn("receivable", boundary.requested_domains)
		self.assertIn("supplier", boundary.grounded_context_domains)
		self.assertEqual(boundary.recommended_boundary_decision, "force_fresh_query")
		self.assertTrue(scope.force_new_query)


if __name__ == "__main__":
	unittest.main()
