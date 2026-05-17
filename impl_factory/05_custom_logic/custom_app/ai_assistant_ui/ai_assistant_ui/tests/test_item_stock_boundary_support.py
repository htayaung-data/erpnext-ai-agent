from __future__ import annotations

import sys
import types
import unittest


fake_frappe = types.ModuleType("frappe")
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat import boundary_support as boundary_support_module
from ai_assistant_ui.qwen_chat import item_stock_boundary_support as stock_support_module


class TestItemStockBoundarySupport(unittest.TestCase):
	def _stock_artifact(self):
		return {
			"request_id": "item-stock-1",
			"family_id": "entity_detail",
			"source_reports": ["Item", "Bin"],
			"dimensions": {
				"entity_type": "item",
				"entity_label": "Type-C Cable 2m Fast Charge",
				"entity_key": "ACC-CBL-UGR-TC2M",
			},
			"metrics": {
				"balance_qty": 88,
				"balance_value": 704000,
				"warehouse_count": 2,
			},
			"sections": {
				"summary": [{"label": "UOM", "value": "Nos"}],
				"stock_rows": [
					{
						"warehouse": "Mandalay Warehouse - MMOB",
						"balance_qty": 53,
						"balance_value": 424000,
					},
					{
						"warehouse": "Yangon Showroom Counter - MMOB",
						"balance_qty": 35,
						"balance_value": 280000,
					},
				],
			},
		}

	def _stock_request(self):
		return {
			"requested_metrics": ["balance_qty"],
			"requested_dimensions": ["warehouse"],
			"requested_concepts": ["inventory"],
			"entity_question_type": "item_stock_position",
		}

	def test_item_stock_direct_answer_uses_warehouse_rows(self):
		answer = stock_support_module.item_stock_direct_evidence_answer(
			raw_message="how many stocks do we have for that product, and in which warehouse?",
			artifact_payload=self._stock_artifact(),
			evidence_request_contract=self._stock_request(),
		)

		self.assertIn("88", answer)
		self.assertIn("2 warehouses", answer)
		self.assertIn("Stock by Warehouse:", answer)
		self.assertIn("- Mandalay Warehouse - MMOB: 53", answer)
		self.assertIn("- Yangon Showroom Counter - MMOB: 35", answer)

	def test_item_stock_rendered_payload_is_owned_by_stock_helper(self):
		payload = stock_support_module.item_stock_direct_evidence_rendered_payload(
			raw_message="show stock by warehouse",
			artifact_payload=self._stock_artifact(),
			evidence_request_contract=self._stock_request(),
		)

		self.assertEqual(payload.get("family_id"), "entity_detail")
		self.assertEqual(payload.get("title"), "Stock Position for Type-C Cable 2m Fast Charge")
		self.assertEqual((payload.get("blocks") or [])[0].get("title"), "Stock Summary")
		self.assertEqual((payload.get("blocks") or [])[1].get("title"), "Stock by Warehouse")

	def test_boundary_facade_delegates_item_stock_direct_answer(self):
		answer = boundary_support_module.grounded_artifact_direct_evidence_answer(
			raw_message="how many stocks do we have for that product, and in which warehouse?",
			artifact_payload=self._stock_artifact(),
			grounded_turn={},
			evidence_request_contract=self._stock_request(),
		)

		self.assertIn("Type-C Cable 2m Fast Charge", answer)
		self.assertIn("- Mandalay Warehouse - MMOB: 53", answer)

	def test_item_stock_boundary_answer_requests_refresh_when_rows_missing(self):
		artifact = self._stock_artifact()
		artifact["sections"] = {"summary": [{"label": "UOM", "value": "Nos"}]}
		answer = stock_support_module.item_stock_evidence_boundary_answer(
			raw_message="show stock by warehouse",
			artifact_payload=artifact,
			evidence_request_contract=self._stock_request(),
		)

		self.assertIn("does not include warehouse-level stock rows", answer)
		self.assertIn("refresh the stock view", answer)


if __name__ == "__main__":
	unittest.main()
