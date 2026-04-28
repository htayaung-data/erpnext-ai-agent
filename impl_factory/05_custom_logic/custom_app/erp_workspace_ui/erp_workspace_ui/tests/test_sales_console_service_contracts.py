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
fake_utils.add_months = lambda value, months: value
fake_utils.cint = lambda value=0: int(value or 0)
fake_utils.cstr = lambda value="": "" if value is None else str(value)
fake_utils.flt = lambda value=0, precision=None: float(value or 0)
fake_utils.fmt_money = lambda value, currency=None, precision=None: str(value)
fake_utils.formatdate = lambda value=None, format_string=None: str(value or "")
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

    def test_sidebar_context_builds_role_aware_sections_and_hides_hidden_actions(self):
        navigation = {
            "actions": {
                "new_quotation": {"kind": "new_doc", "doctype": "Quotation"},
                "new_sales_order": {"kind": "new_doc", "doctype": "Sales Order"},
                "open_customer": {"kind": "worklist", "queue_key": "customer_directory"},
                "open_item": {"kind": "worklist", "queue_key": "item_directory"},
            },
            "browse": {
                "quotation_directory": {"kind": "worklist", "queue_key": "quotation_directory"},
                "sales_order_directory": {"kind": "worklist", "queue_key": "sales_order_directory"},
                "customer_directory": {"kind": "worklist", "queue_key": "customer_directory"},
                "item_directory": {"kind": "worklist", "queue_key": "item_directory"},
            },
            "insights": {
                "open_orders": {"kind": "worklist", "queue_key": "open_orders"},
                "awaiting_approval": {"kind": "worklist", "queue_key": "orders_blocked_by_approval"},
            },
            "work": {
                "quotations_waiting_action": {"kind": "worklist", "queue_key": "quotations_waiting_action"},
                "customer_follow_up_tasks": {"kind": "worklist", "queue_key": "customer_follow_up_tasks"},
            },
            "lifecycle": {},
            "blockers": {},
            "queues": {},
            "reports": {
                "sales_order_analysis": {"kind": "report_page", "report_key": "sales_order_analysis"},
                "quotation_trends": {"kind": "report_page", "report_key": "quotation_trends"},
                "collections_status": {"kind": "report_page", "report_key": "collections_status"},
                "lost_quotations": {"kind": "report_page", "report_key": "lost_quotations"},
            },
        }
        reports_catalog = [
            {"key": "sales_order_analysis", "title": "Sales Order Analysis", "icon": "order"},
            {"key": "quotation_trends", "title": "Quotation Trends", "icon": "quotation"},
            {"key": "collections_status", "title": "Collections Status", "icon": "chart"},
            {"key": "lost_quotations", "title": "Lost Quotations", "icon": "quotation"},
        ]

        with patch.object(service, "_build_context", return_value={"role_variant": "sales_executive", "primary_role": "Sales"}), patch.object(
            service,
            "_build_scope",
            return_value={"scope_label": "Assigned account scope"},
        ), patch.object(
            service,
            "_build_ui_profile",
            return_value={
                "mode_label": "Execution Mode",
                "hidden_actions": ["new_sales_order"],
                "queue_order": ["quotations_waiting_action", "customer_follow_up_tasks"],
                "show_reports": True,
            },
        ), patch.object(service, "_build_navigation", return_value=navigation), patch.object(
            service,
            "_build_reports_catalog",
            return_value=reports_catalog,
        ):
            result = service.get_sales_console_sidebar_context()

        self.assertEqual(result["ui_profile"]["mode_label"], "Execution Mode")
        sections = {section["key"]: section for section in result["sidebar"]["sections"]}
        self.assertEqual(
            [item["label"] for item in sections["browse"]["items"]],
            ["Sales Console", "Quotations", "Sales Orders", "Customers", "Items"],
        )
        self.assertNotIn("workspace", sections)
        self.assertNotIn("create", sections)
        self.assertNotIn("review", sections)
        self.assertNotIn("reports", sections)

    def test_sidebar_context_omits_create_and_reports_when_profile_hides_them(self):
        navigation = {
            "actions": {
                "new_quotation": {"kind": "new_doc", "doctype": "Quotation"},
                "new_sales_order": {"kind": "new_doc", "doctype": "Sales Order"},
                "open_customer": {"kind": "worklist", "queue_key": "customer_directory"},
                "open_item": {"kind": "worklist", "queue_key": "item_directory"},
            },
            "browse": {
                "quotation_directory": {"kind": "worklist", "queue_key": "quotation_directory"},
                "sales_order_directory": {"kind": "worklist", "queue_key": "sales_order_directory"},
                "customer_directory": {"kind": "worklist", "queue_key": "customer_directory"},
                "item_directory": {"kind": "worklist", "queue_key": "item_directory"},
            },
            "insights": {
                "open_orders": {"kind": "worklist", "queue_key": "open_orders"},
                "awaiting_approval": {"kind": "worklist", "queue_key": "orders_blocked_by_approval"},
            },
            "work": {},
            "lifecycle": {},
            "blockers": {},
            "queues": {},
            "reports": {
                "sales_analytics": {"kind": "report_page", "report_key": "sales_analytics"},
            },
        }

        with patch.object(service, "_build_context", return_value={"role_variant": "executive_review", "primary_role": "Sales"}), patch.object(
            service,
            "_build_scope",
            return_value={"scope_label": "Executive review scope"},
        ), patch.object(
            service,
            "_build_ui_profile",
            return_value={
                "mode_label": "Executive Review Mode",
                "hidden_actions": ["new_quotation", "new_sales_order"],
                "queue_order": [],
                "show_reports": False,
            },
        ), patch.object(service, "_build_navigation", return_value=navigation), patch.object(
            service,
            "_build_reports_catalog",
            return_value=[{"key": "sales_analytics", "title": "Sales Analytics", "icon": "chart"}],
        ):
            result = service.get_sales_console_sidebar_context()

        section_keys = [section["key"] for section in result["sidebar"]["sections"]]
        self.assertIn("browse", section_keys)
        self.assertNotIn("workspace", section_keys)
        self.assertNotIn("create", section_keys)
        self.assertNotIn("review", section_keys)
        self.assertNotIn("reports", section_keys)

    def test_sales_console_workspace_search_returns_scoped_targets(self):
        def fake_fieldnames(doctype):
            field_map = {
                "Customer": {"name", "customer_name", "territory", "modified", "disabled"},
                "Item": {"name", "item_code", "item_name", "item_group", "modified", "disabled", "is_sales_item"},
                "Quotation": {"name", "customer_name", "status", "transaction_date", "modified", "docstatus", "owner"},
                "Sales Order": {"name", "customer", "status", "transaction_date", "modified", "docstatus", "owner"},
            }
            return field_map.get(doctype, {"name"})

        def fake_get_list(doctype, **kwargs):
            if doctype == "Customer":
                return [
                    {
                        "name": "CUST-ACME",
                        "customer_name": "Acme Trading",
                        "territory": "Yangon",
                        "modified": "2026-04-24 09:00:00",
                    }
                ]
            if doctype == "Item":
                return [
                    {
                        "name": "ITEM-ACME-1",
                        "item_code": "ITEM-ACME-1",
                        "item_name": "Acme Camera",
                        "item_group": "Security",
                        "modified": "2026-04-24 08:00:00",
                    }
                ]
            if doctype == "Quotation":
                return [
                    {
                        "name": "QTN-0001",
                        "customer_name": "Acme Trading",
                        "status": "Open",
                        "transaction_date": "2026-04-20",
                        "modified": "2026-04-24 10:00:00",
                    }
                ]
            if doctype == "Sales Order":
                return [
                    {
                        "name": "SO-0001",
                        "customer": "Acme Trading",
                        "status": "To Deliver",
                        "transaction_date": "2026-04-21",
                        "modified": "2026-04-24 07:00:00",
                    }
                ]
            return []

        with patch.object(
            service,
            "_build_context",
            return_value={"role_variant": "sales_executive", "primary_role": "Sales"},
        ), patch.object(
            service,
            "_build_scope",
            return_value={"scope_mode": "permission_scope", "owner_user_ids": ["Administrator"], "apply_branch_filter": False, "branch_name": None},
        ), patch.object(service, "_can_read", return_value=True), patch.object(
            service,
            "_fieldnames",
            side_effect=fake_fieldnames,
        ), patch.object(service.frappe, "get_list", side_effect=fake_get_list):
            result = service.search_sales_console_workspace("Acme", limit=8)

        self.assertEqual(result["state"], "ready")
        results_by_doctype = {item["doctype"]: item for item in result["results"]}
        self.assertEqual(results_by_doctype["Customer"]["target"]["kind"], "worklist")
        self.assertEqual(results_by_doctype["Customer"]["target"]["queue_key"], "customer_directory")
        self.assertEqual(results_by_doctype["Customer"]["target"]["filters"]["keyword"], "CUST-ACME")
        self.assertEqual(results_by_doctype["Item"]["target"]["kind"], "worklist")
        self.assertEqual(results_by_doctype["Item"]["target"]["queue_key"], "item_directory")
        self.assertEqual(results_by_doctype["Quotation"]["target"]["kind"], "form")
        self.assertEqual(results_by_doctype["Quotation"]["target"]["doctype"], "Quotation")
        self.assertEqual(results_by_doctype["Sales Order"]["target"]["kind"], "form")
        self.assertEqual(results_by_doctype["Sales Order"]["target"]["doctype"], "Sales Order")

    def test_sales_console_workspace_search_stays_idle_for_short_query(self):
        result = service.search_sales_console_workspace("a")

        self.assertEqual(result["state"], "idle")
        self.assertEqual(result["results"], [])


if __name__ == "__main__":
    unittest.main()
