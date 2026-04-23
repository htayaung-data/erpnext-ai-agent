import sys
import types
import unittest


def _fake_get_all(doctype, *args, **kwargs):
	if doctype == "Company":
		if kwargs.get("pluck") == "name":
			return ["Mingalar Mobile Distribution Co., Ltd."]
		return [{"name": "Mingalar Mobile Distribution Co., Ltd."}]
	if doctype == "Fiscal Year":
		return [
			{
				"name": "FY-2026",
				"year_start_date": "2025-04-01",
				"year_end_date": "2026-03-31",
			}
		]
	return []


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = _fake_get_all
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.contracts import NormalizedFamilyArtifactContract
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response


class InventorySnapshotRenderingContractsTest(unittest.TestCase):
	def _artifact(self, snapshot_dimension: str = "warehouse") -> NormalizedFamilyArtifactContract:
		return NormalizedFamilyArtifactContract(
			request_id="inventory-render",
			family_id="inventory_snapshot",
			artifact_type="normalized_family_artifact",
			source_reports=["Warehouse Wise Stock Balance"],
			period={"to_date": "2026-04-17"},
			filters={"company": "Mingalar Mobile Distribution Co., Ltd."},
			dimensions={"snapshot_dimension": snapshot_dimension},
			metrics={
				"balance_qty": 120.0,
				"balance_value": 950000.0,
				"warehouse_count": 3,
				"item_count": 1,
			},
			sections={
				"summary": [
					{"label": "Total Balance Qty", "metric_key": "balance_qty", "amount": 120.0},
					{"label": "Total Balance Value", "metric_key": "balance_value", "amount": 950000.0},
					{"label": "Warehouse Count", "metric_key": "warehouse_count", "value": 3},
				],
				"warehouse_totals": [
					{"warehouse": "Main Warehouse - MMD", "balance_qty": 80.0, "balance_value": 600000.0},
					{"warehouse": "Outlet Warehouse - YGN", "balance_qty": 30.0, "balance_value": 250000.0},
					{"warehouse": "Transit Warehouse - MMD", "balance_qty": 10.0, "balance_value": 100000.0},
				],
				"item_totals": [
					{"item": "Type-C Cable 1m Fast Charge", "balance_qty": 120.0, "balance_value": 950000.0},
				],
			},
			warnings=[],
		)

	def test_inventory_renderer_accepts_shared_response_overrides(self):
		artifact = self._artifact()
		rendered = render_normalized_family_response(
			request_id="render-inventory-overrides",
			artifact_contract=artifact,
			response_overrides={"top_n": 2, "suppress_summary": True},
		)
		self.assertEqual(rendered.status, "rendered")
		payload = rendered.contract.to_payload() if rendered.contract is not None else {}
		answer_text = str(payload.get("answer_text") or "")
		self.assertIn("Inventory Snapshot as of 2026-04-17", answer_text)
		self.assertIn("Top Warehouses", answer_text)
		self.assertIn("Main Warehouse - MMD", answer_text)
		self.assertIn("Outlet Warehouse - YGN", answer_text)
		self.assertNotIn("Transit Warehouse - MMD", answer_text)
		self.assertNotIn("Summary", answer_text)

	def test_inventory_renderer_keeps_summary_by_default(self):
		artifact = self._artifact(snapshot_dimension="item")
		rendered = render_normalized_family_response(
			request_id="render-inventory-default",
			artifact_contract=artifact,
		)
		self.assertEqual(rendered.status, "rendered")
		payload = rendered.contract.to_payload() if rendered.contract is not None else {}
		answer_text = str(payload.get("answer_text") or "")
		self.assertIn("Summary", answer_text)
		self.assertIn("Type-C Cable 1m Fast Charge", answer_text)
		self.assertIn("950,000", answer_text)


if __name__ == "__main__":
	unittest.main()
