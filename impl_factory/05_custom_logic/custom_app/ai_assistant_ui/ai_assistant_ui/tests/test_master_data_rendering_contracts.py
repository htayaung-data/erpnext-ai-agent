import sys
import types
import unittest


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.contracts import NormalizedFamilyArtifactContract
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response


class TestMasterDataRenderingContracts(unittest.TestCase):
	def test_supplier_names_listing_states_found_record_count_and_as_of_date(self):
		artifact = NormalizedFamilyArtifactContract(
			request_id="supplier-list-wording-1",
			family_id="master_data_directory",
			artifact_type="normalized_family_artifact",
			source_reports=["Supplier Master List"],
			period={"to_date": "2026-04-27"},
			filters={"company": "Mingalar Mobile Distribution Co., Ltd."},
			dimensions={
				"scope_id": "supplier_master",
				"entity_type": "supplier",
				"entity_label": "Supplier",
				"entity_plural_label": "Suppliers",
				"lookup_projection": "names_only",
			},
			metrics={},
			sections={
				"directory_rows": [
					{"entity": "Shan Yoma Electronics"},
					{"entity": "Myanmar Tech Import Services"},
				]
			},
			warnings=[],
		)

		outcome = render_normalized_family_response(
			request_id="supplier-list-wording-1",
			artifact_contract=artifact,
		)

		self.assertEqual(outcome.status, "rendered")
		answer = outcome.contract.answer_text
		self.assertIn("2 Suppliers Found as of 2026-04-27", answer)
		self.assertNotIn("Suppliers as of 2026-04-27 Here are", answer)
		self.assertIn("Supplier Names", answer)
		self.assertIn("Myanmar Tech Import Services", answer)


if __name__ == "__main__":
	unittest.main()
