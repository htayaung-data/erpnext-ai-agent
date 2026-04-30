import unittest
import sys
import types
from unittest.mock import patch


def _fake_get_all(doctype, *args, **kwargs):
    if doctype == "Company":
        if kwargs.get("pluck") == "name":
            return ["Enterprise Co"]
        return [{"name": "Enterprise Co"}]
    return []


fake_frappe = types.ModuleType("frappe")
fake_frappe.conf = {}
fake_frappe.get_all = _fake_get_all
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.db = types.SimpleNamespace(
    exists=lambda *args, **kwargs: False,
    get_value=lambda *args, **kwargs: None,
    sql=lambda *args, **kwargs: [],
)
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.fresh_query_interpreter import compile_from_fresh_query_message


def _runtime_transaction_listing_payload() -> dict:
    return {
        "ok": True,
        "interpretation": {
            "intent_class": "transaction_listing",
            "candidate_capability_ids": ["sales_read"],
            "candidate_reports": ["Sales Invoice List"],
            "requested_dimensions": ["Invoice"],
            "requested_metrics": ["Grand Total"],
            "requested_time_scope": "",
            "requested_presentation": ["table_presentation"],
            "extracted_slots": {},
            "ambiguity_flags": [],
            "ambiguity_reason": "",
            "confidence": 1.0,
        },
        "agent_meta": {},
    }


class TestTransactionListingFrontdoorScopeAliases(unittest.TestCase):
    def test_supplier_invoice_alias_reconciles_through_governed_scope_metadata(self):
        with patch(
            "ai_assistant_ui.qwen_chat.fresh_query_interpreter.call_qwen_runtime_fresh_query_interpretation",
            return_value=_runtime_transaction_listing_payload(),
        ):
            pipeline = compile_from_fresh_query_message(
                session_id="transaction-listing-supplier-invoice-alias",
                user_id="Administrator",
                site_name="test-site",
                message="show me supplier invoices",
                recent_messages=[],
            )

        semantic_payload = pipeline.get("fresh_query_interpretation") if isinstance(pipeline.get("fresh_query_interpretation"), dict) else {}
        interpretation = semantic_payload.get("interpretation") if isinstance(semantic_payload.get("interpretation"), dict) else {}
        resolution = pipeline.get("semantic_resolution_contract") if isinstance(pipeline.get("semantic_resolution_contract"), dict) else {}
        compiler_payload = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}

        self.assertEqual(interpretation.get("extracted_slots", {}).get("listing_view"), "purchase_invoice")
        self.assertEqual(resolution.get("resolved_slots", {}).get("listing_view"), "purchase_invoice")
        self.assertEqual(resolution.get("scope_id"), "purchase_invoice")
        self.assertEqual(compiler_payload.get("selected_report"), "Purchase Invoice List")

    def test_collection_alias_reconciles_payment_entry_from_governed_scope_metadata(self):
        with patch(
            "ai_assistant_ui.qwen_chat.fresh_query_interpreter.call_qwen_runtime_fresh_query_interpretation",
            return_value=_runtime_transaction_listing_payload(),
        ):
            pipeline = compile_from_fresh_query_message(
                session_id="transaction-listing-collection-alias",
                user_id="Administrator",
                site_name="test-site",
                message="show me collections",
                recent_messages=[],
            )

        semantic_payload = pipeline.get("fresh_query_interpretation") if isinstance(pipeline.get("fresh_query_interpretation"), dict) else {}
        interpretation = semantic_payload.get("interpretation") if isinstance(semantic_payload.get("interpretation"), dict) else {}
        resolution = pipeline.get("semantic_resolution_contract") if isinstance(pipeline.get("semantic_resolution_contract"), dict) else {}
        compiler_payload = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}

        self.assertEqual(interpretation.get("extracted_slots", {}).get("listing_view"), "payment_entry")
        self.assertEqual(resolution.get("resolved_slots", {}).get("listing_view"), "payment_entry")
        self.assertEqual(resolution.get("scope_id"), "payment_entry")
        self.assertEqual(compiler_payload.get("selected_report"), "Payment Entry List")


if __name__ == "__main__":
    unittest.main()
