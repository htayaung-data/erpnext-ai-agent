import sys
import types
import unittest


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.contracts import NormalizedFamilyArtifactContract
from ai_assistant_ui.qwen_chat.family_followup import render_local_family_followup
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response


class TestMasterDataRenderingContracts(unittest.TestCase):
	def _artifact(
		self,
		*,
		report_name: str = "Customer Master List",
		scope_id: str = "customer_master",
		entity_type: str = "customer",
		entity_label: str = "Customer",
		entity_plural_label: str = "Customers",
		region_label: str = "Territory",
		group_label: str = "Customer Group",
		row: dict | None = None,
		lookup_projection: str,
		requested_columns: list[str] | None = None,
		requested_column_alias_map: dict | None = None,
	) -> NormalizedFamilyArtifactContract:
		directory_row = dict(
			row
			or {
				"entity": "Ko Nay Lin Mobile Center",
				"region": "Mandalay",
				"group": "Wholesale",
				"creation": "2026-02-12",
				"status": "Active",
				"payment_terms": "30 Days - MMOB",
			}
		)
		return NormalizedFamilyArtifactContract(
			request_id=f"master-data-{lookup_projection}",
			family_id="master_data_directory",
			artifact_type="normalized_family_artifact",
			source_reports=[report_name],
			period={"as_of_date": "2026-04-16"},
			filters={"company": "Mingalar Mobile Distribution Co., Ltd."},
			dimensions={
				"scope_id": scope_id,
				"entity_type": entity_type,
				"entity_label": entity_label,
				"entity_plural_label": entity_plural_label,
				"region_label": region_label,
				"group_label": group_label,
				"lookup_mode": "directory_list",
				"lookup_projection": lookup_projection,
				"requested_columns": list(requested_columns or []),
				"requested_column_alias_map": dict(requested_column_alias_map or {}),
			},
			metrics={},
			sections={
				"directory_rows": [directory_row]
			},
			warnings=[],
		)

	def test_names_only_projection_renders_name_list(self):
		rendered = render_normalized_family_response(
			request_id="render-master-data-names-only",
			artifact_contract=self._artifact(lookup_projection="names_only"),
		)
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("Customer Names", answer_text)
		self.assertIn("Ko Nay Lin Mobile Center", answer_text)
		self.assertNotIn("| Created Date |", answer_text)

	def test_standard_directory_projection_uses_projection_registry_columns(self):
		rendered = render_normalized_family_response(
			request_id="render-master-data-standard-directory",
			artifact_contract=self._artifact(lookup_projection="standard_directory"),
		)
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("| Customer | Created Date | Territory | Customer Group | Status |", answer_text)
		self.assertIn("| Ko Nay Lin Mobile Center | 2026-02-12 | Mandalay | Wholesale | Active |", answer_text)

	def test_selected_columns_projection_respects_explicit_requested_columns(self):
		rendered = render_normalized_family_response(
			request_id="render-master-data-selected-columns",
			artifact_contract=self._artifact(
				lookup_projection="selected_columns",
				requested_columns=["entity", "payment_terms"],
			),
		)
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("| Customer | Payment Terms |", answer_text)
		self.assertIn("| Ko Nay Lin Mobile Center | 30 Days - MMOB |", answer_text)
		self.assertNotIn("Created Date", answer_text)

	def test_item_directory_projection_uses_brand_and_item_group_columns(self):
		rendered = render_normalized_family_response(
			request_id="render-item-master-standard-directory",
			artifact_contract=self._artifact(
				report_name="Item Master List",
				scope_id="item_master",
				entity_type="item",
				entity_label="Item",
				entity_plural_label="Items",
				region_label="Brand",
				group_label="Item Group",
				row={
					"entity": "Demo Item",
					"region": "Demo Brand",
					"group": "Accessories",
					"creation": "2026-02-15",
					"status": "Active",
				},
				lookup_projection="standard_directory",
			),
		)
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("| Item | Created Date | Brand | Item Group | Status |", answer_text)
		self.assertIn("| Demo Item | 2026-02-15 | Demo Brand | Accessories | Active |", answer_text)

	def test_local_followup_normalizes_item_brand_alias_projection(self):
		artifact = self._artifact(
			report_name="Item Master List",
			scope_id="item_master",
			entity_type="item",
			entity_label="Item",
			entity_plural_label="Items",
			region_label="Brand",
			group_label="Item Group",
			row={
				"entity": "Demo Item",
				"region": "Demo Brand",
				"group": "Accessories",
				"creation": "2026-02-15",
				"status": "Active",
			},
			lookup_projection="names_only",
			requested_columns=["entity"],
			requested_column_alias_map={
				"item": "entity",
				"product": "entity",
				"brand": "region",
				"item_group": "group",
			},
		)
		rendered = render_local_family_followup(
			request_id="render-item-master-followup-brand-only",
			artifact_payload=artifact.to_payload(),
			requested_columns=["item", "brand"],
			requested_modes=["column_refinement"],
		)
		answer_text = str(rendered.get("answer_text") or "")
		self.assertIn("| Item | Brand |", answer_text)
		self.assertIn("| Demo Item | Demo Brand |", answer_text)
		self.assertNotIn("Item Group", answer_text)


if __name__ == "__main__":
	unittest.main()
