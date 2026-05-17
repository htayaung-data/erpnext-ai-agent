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

from ai_assistant_ui.qwen_chat.family_followup import (
	refine_local_family_artifact,
	supports_local_family_followup,
)


class TestFamilyFollowupContracts(unittest.TestCase):
	def setUp(self):
		self.master_data_directory_payload = {
			"request_id": "supplier-directory-base",
			"family_id": "master_data_directory",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Supplier Master List"],
			"period": {},
			"filters": {},
			"dimensions": {
				"requested_columns": ["entity"],
				"requested_column_alias_map": {
					"supplier": "entity",
					"supplier_name": "entity",
					"name": "entity",
					"supplier_group": "supplier_group",
					"payment_terms": "payment_terms",
				},
				"entity_type": "supplier",
			},
			"metrics": {},
			"sections": {
				"directory_rows": [
					{"name": "Myanmar Tech Import Services", "supplier_group": "Electronics Importer"},
					{"name": "Sunflower Accessories Co.", "supplier_group": "Accessories Supplier"},
				]
			},
			"warnings": [],
		}

	def test_master_data_directory_supports_safe_column_refinement(self):
		self.assertTrue(
			supports_local_family_followup(
				self.master_data_directory_payload,
				requested_columns=["supplier", "supplier_group"],
				requested_modes=["column_refinement"],
			)
		)

	def test_master_data_directory_refinement_preserves_explicit_selection(self):
		refined = refine_local_family_artifact(
			request_id="supplier-directory-refined",
			artifact_payload=self.master_data_directory_payload,
			requested_columns=["supplier", "supplier_group"],
			requested_modes=["column_refinement"],
		)
		self.assertEqual(refined.get("request_id"), "supplier-directory-refined")
		self.assertEqual(
			(refined.get("dimensions") or {}).get("requested_columns"),
			["entity", "supplier_group"],
		)
		self.assertEqual(
			(refined.get("dimensions") or {}).get("requested_projection_mode"),
			"explicit_selection",
		)


if __name__ == "__main__":
	unittest.main()
