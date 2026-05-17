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

from ai_assistant_ui.qwen_chat import recent_focus_support as recent_focus_support_module


class TestRecentFocusReferenceTerms(unittest.TestCase):
	def test_recent_focus_affordance_exposes_customer_reference_terms(self):
		contract = recent_focus_support_module.build_recent_focus_affordance_contract_from_snapshot(
			request_id="rf-reference-customer-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_family": "entity_detail",
				"source_capability": "customer_credit_profile",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)
		payload = contract.to_payload()
		reference_terms = payload.get("reference_terms") or {}

		self.assertIn("that customer", reference_terms.get("deictic_terms") or [])
		self.assertIn("Ko Nay Lin Mobile Center", reference_terms.get("explicit_reference_terms") or [])
		self.assertTrue(bool(payload.get("deictic_reference_allowed")))

	def test_recent_focus_affordance_exposes_product_reference_terms_for_item(self):
		contract = recent_focus_support_module.build_recent_focus_affordance_contract_from_snapshot(
			request_id="rf-reference-item-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "item",
				"focus_label": "Type-C Cable 2m Fast Charge",
				"focus_key": "ACC-CBL-UGR-TC2M",
				"source_family": "entity_detail",
				"source_capability": "item_sales_detail",
				"source_report": "Item Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)
		payload = contract.to_payload()
		reference_terms = payload.get("reference_terms") or {}

		self.assertIn("that product", reference_terms.get("deictic_terms") or [])
		self.assertIn("that item", reference_terms.get("deictic_terms") or [])
		self.assertIn("Type-C Cable 2m Fast Charge", reference_terms.get("explicit_reference_terms") or [])

	def test_recent_focus_affordance_exposes_collection_terms_for_supplier_listing(self):
		contract = recent_focus_support_module.build_recent_focus_affordance_contract_from_snapshot(
			request_id="rf-reference-supplier-list-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "supplier",
				"focus_label": "Supplier Master List",
				"focus_key": "supplier",
				"source_family": "master_data_directory",
				"source_capability": "supplier_master_read",
				"source_report": "Supplier Master List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
		)
		payload = contract.to_payload()
		reference_terms = payload.get("reference_terms") or {}

		self.assertIn("that supplier list", reference_terms.get("deictic_terms") or [])
		self.assertIn("supplier directory", reference_terms.get("collection_reference_terms") or [])
		self.assertEqual(reference_terms.get("explicit_reference_terms") or [], [])

	def test_resolved_focus_target_carries_affordance_reference_terms(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "entity",
			"focus_grain": "item",
			"focus_label": "Type-C Cable 1m Fast Charge",
			"focus_key": "ACC-CBL-BAS-TC1M",
			"source_family": "entity_detail",
			"source_capability": "item_sales_detail",
			"source_report": "Item Detail",
			"deictic_allowed": True,
			"explicit_named_allowed": True,
		}
		affordance_payload = recent_focus_support_module.build_recent_focus_affordance_contract_from_snapshot(
			request_id="rf-reference-target-1",
			recent_focus_state=recent_focus_state,
		).to_payload()

		target = recent_focus_support_module.conversation_control_focus_target_from_recent_focus_state(
			recent_focus_state,
			recent_focus_affordance_payload=affordance_payload,
		)

		self.assertIn("that product", (target.get("reference_terms") or {}).get("deictic_terms") or [])
		self.assertIn(
			"Type-C Cable 1m Fast Charge",
			(target.get("reference_terms") or {}).get("explicit_reference_terms") or [],
		)


if __name__ == "__main__":
	unittest.main()
