import sys
import types
import unittest
from datetime import date
from unittest.mock import patch


fake_frappe = types.ModuleType("frappe")


def _identity_whitelist(*args, **kwargs):
    if args and callable(args[0]) and len(args) == 1 and not kwargs:
        return args[0]

    def decorator(fn):
        return fn

    return decorator


class _FakePermissionError(Exception):
    pass


fake_frappe.whitelist = _identity_whitelist
fake_frappe.PermissionError = _FakePermissionError
fake_frappe.throw = lambda message, exc=None: (_ for _ in ()).throw((exc or Exception)(message))
fake_frappe.session = types.SimpleNamespace(user="Administrator")
fake_frappe.db = types.SimpleNamespace(
    get_value=lambda *args, **kwargs: None,
    exists=lambda *args, **kwargs: False,
    get_single_value=lambda *args, **kwargs: None,
)
fake_frappe.get_roles = lambda *args, **kwargs: []
fake_frappe.get_list = lambda *args, **kwargs: []
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe._ = lambda message: message

fake_utils = types.ModuleType("frappe.utils")
fake_utils.get_fullname = lambda user=None: user or ""
fake_utils.getdate = lambda value=None: value
fake_utils.now_datetime = lambda: "2026-04-10 00:00:00"
fake_utils.nowdate = lambda: "2026-04-10"

sys.modules.setdefault("frappe", fake_frappe)
sys.modules.setdefault("frappe.utils", fake_utils)

from erp_workspace_ui.sales_console import service


class TestSalesConsoleServiceContracts(unittest.TestCase):
    def test_resolve_return_documents_blocks_customer_fallback_for_quotation_anchor(self):
        invoice_calls = []
        delivery_calls = []

        def fake_get_list(doctype, **kwargs):
            if doctype == "Sales Invoice":
                invoice_calls.append(kwargs)
                return []
            if doctype == "Delivery Note":
                delivery_calls.append(kwargs)
                return []
            return []

        def fake_fieldnames(doctype):
            base = {"name", "status", "posting_date", "customer", "is_return", "return_against"}
            return base

        with patch.object(service, "_can_read", return_value=True), patch.object(
            service,
            "_fieldnames",
            side_effect=fake_fieldnames,
        ), patch.object(service.frappe, "get_list", side_effect=fake_get_list):
            result = service._resolve_return_documents(
                {"doctype": "Quotation", "name": "QTN-1"},
                [],
                [],
                "CUST-1",
            )

        self.assertEqual(result, [])
        self.assertEqual(invoice_calls[0]["filters"], {"is_return": 1, "name": "__erpw_no_match__"})
        self.assertEqual(delivery_calls[0]["filters"], {"is_return": 1, "name": "__erpw_no_match__"})

    def test_resolve_return_documents_keeps_customer_scope_for_customer_anchor(self):
        captured = []

        def fake_get_list(doctype, **kwargs):
            captured.append((doctype, kwargs))
            if doctype == "Sales Invoice":
                return [{"name": "ACC-SINV-RET-1", "customer": "CUST-1", "status": "Return", "posting_date": "2026-04-10", "return_against": "ACC-SINV-1"}]
            return []

        with patch.object(service, "_can_read", return_value=True), patch.object(
            service,
            "_fieldnames",
            return_value={"name", "status", "posting_date", "customer", "is_return", "return_against"},
        ), patch.object(service.frappe, "get_list", side_effect=fake_get_list):
            result = service._resolve_return_documents(
                {"doctype": "Customer", "name": "CUST-1"},
                [],
                [],
                "CUST-1",
            )

        self.assertEqual(result[0]["doctype"], "Sales Invoice")
        invoice_call = next(item for item in captured if item[0] == "Sales Invoice")
        self.assertEqual(invoice_call[1]["filters"], {"is_return": 1, "customer": "CUST-1"})

    def test_resolve_commercial_chain_filters_return_docs_out_of_normal_stages(self):
        def fake_load_documents(doctype, names, order_date_field=None):
            if doctype == "Sales Order":
                return [{"doctype": "Sales Order", "name": "SO-1", "status": "To Deliver"}]
            if doctype == "Delivery Note":
                return [
                    {"doctype": "Delivery Note", "name": "DN-1", "status": "Completed", "is_return": 0},
                    {"doctype": "Delivery Note", "name": "DN-RET-1", "status": "Return", "is_return": 1, "return_against": "DN-1"},
                ]
            if doctype == "Sales Invoice":
                return [
                    {"doctype": "Sales Invoice", "name": "INV-1", "status": "Unpaid", "is_return": 0},
                    {"doctype": "Sales Invoice", "name": "INV-RET-1", "status": "Return", "is_return": 1, "return_against": "INV-1"},
                ]
            return []

        with patch.object(service, "_load_documents", side_effect=fake_load_documents), patch.object(
            service,
            "_delivery_notes_from_sales_order_names",
            return_value=["DN-1", "DN-RET-1"],
        ), patch.object(
            service,
            "_sales_invoices_from_sales_order_names",
            return_value=["INV-1", "INV-RET-1"],
        ), patch.object(service, "_quotations_from_sales_order_names", return_value=[]), patch.object(
            service,
            "_sales_orders_from_delivery_names",
            return_value=[],
        ), patch.object(service, "_sales_invoices_from_delivery_names", return_value=[]), patch.object(
            service,
            "_sales_orders_from_sales_invoice_names",
            return_value=[],
        ), patch.object(service, "_delivery_notes_from_sales_invoice_names", return_value=[]):
            _quotation_docs, _sales_order_docs, delivery_docs, sales_invoice_docs = service._resolve_commercial_chain(
                {"doctype": "Sales Order", "name": "SO-1", "customer": "CUST-1"}
            )

        self.assertEqual([doc["name"] for doc in delivery_docs], ["DN-1"])
        self.assertEqual([doc["name"] for doc in sales_invoice_docs], ["INV-1"])

    def test_sales_return_filters_exclude_future_dates(self):
        with patch.object(
            service,
            "_fieldnames",
            return_value={"docstatus", "is_return", "posting_date", "return_against"},
        ), patch.object(service, "_scoped_sales_chain_invoice_names", return_value=(["INV-1"], "scope note")):
            filters, scope_note = service._sales_return_filters("Sales Invoice", date(2026, 4, 10), {})

        self.assertIn(["posting_date", "<=", date(2026, 4, 10)], filters)
        self.assertIn(["return_against", "in", ["INV-1"]], filters)
        self.assertEqual(scope_note, "scope note")

    def test_sales_return_stage_uses_specific_label_and_item_status(self):
        return_docs = [{"doctype": "Sales Invoice", "name": "INV-RET-1", "status": "Return", "return_against": "INV-1"}]
        flow = service._build_document_flow(
            {"doctype": "Quotation", "name": "QTN-1"},
            [],
            [],
            [],
            [],
            [],
            return_docs,
        )
        sales_return_stage = flow[-1]
        current_status = service._build_current_status(
            {"doctype": "Quotation", "name": "QTN-1"},
            [],
            [],
            [],
            [],
            [],
            return_docs,
        )

        self.assertEqual(sales_return_stage["label"], "Sales Return")
        self.assertEqual(sales_return_stage["items"][0]["status"], "Against INV-1")
        self.assertIn("Sales Return", [row["label"] for row in current_status])
        self.assertNotIn("Return", [row["label"] for row in current_status])

    def test_related_documents_exclude_anchor_record(self):
        related = service._build_related_documents(
            {"doctype": "Sales Invoice", "name": "INV-1"},
            [],
            [],
            [],
            [{"doctype": "Sales Invoice", "name": "INV-1", "status": "Overdue"}],
            [{"doctype": "Payment Entry", "name": "PAY-1", "status": "Submitted"}],
            [],
        )

        self.assertEqual([item["name"] for item in related], ["PAY-1"])

    def test_payment_summary_prefers_business_status_over_raw_restriction_copy(self):
        summary = service._payment_summary(
            [{"doctype": "Sales Invoice", "name": "INV-1", "status": "Overdue", "grand_total": 100, "outstanding_amount": 21}],
            [{"doctype": "Payment Entry", "name": "PAY-1", "status": "Submitted"}],
        )

        self.assertEqual(summary, "79% settled; 1 payment record(s) linked")


if __name__ == "__main__":
    unittest.main()
