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
fake_frappe.defaults = types.SimpleNamespace(
    get_user_default=lambda *args, **kwargs: None,
    get_default=lambda *args, **kwargs: None,
)
fake_frappe.get_roles = lambda *args, **kwargs: []
fake_frappe.get_list = lambda *args, **kwargs: []
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.generate_hash = lambda length=10: "x" * length
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe._ = lambda message: message
fake_frappe._dict = lambda value=None, **kwargs: types.SimpleNamespace(**dict(value or {}, **kwargs))
fake_frappe.scrub = lambda value: str(value or "").strip().lower().replace(" ", "_")
fake_frappe.format_value = lambda value, df=None, doc=None: str(value)

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

fake_utils_data = types.ModuleType("frappe.utils.data")
fake_utils_data.get_timespan_date_range = lambda timespan: (None, None)

fake_query_report = types.ModuleType("frappe.desk.query_report")
fake_query_report.run = lambda *args, **kwargs: {}

fake_desk = types.ModuleType("frappe.desk")
fake_erpnext = types.ModuleType("erpnext")
fake_erpnext_controllers = types.ModuleType("erpnext.controllers")
fake_erpnext_trends = types.ModuleType("erpnext.controllers.trends")
fake_erpnext_trends.get_columns = lambda filters, trans: {"columns": []}
fake_erpnext_trends.get_data = lambda filters, conditions: []

sys.modules.setdefault("frappe", fake_frappe)
sys.modules.setdefault("frappe.utils", fake_utils)
sys.modules.setdefault("frappe.utils.data", fake_utils_data)
sys.modules.setdefault("frappe.desk", fake_desk)
sys.modules.setdefault("frappe.desk.query_report", fake_query_report)
sys.modules.setdefault("erpnext", fake_erpnext)
sys.modules.setdefault("erpnext.controllers", fake_erpnext_controllers)
sys.modules.setdefault("erpnext.controllers.trends", fake_erpnext_trends)

from erp_workspace_ui.sales_console import report, worklist


class TestSalesConsoleOperatingContracts(unittest.TestCase):
    def test_worklist_operating_contract_adds_standard_actions_and_filter_controls(self):
        payload = {
            "controls": {
                "fields": [{"key": "territory", "label": "Territory"}],
                "actions": [
                    {"key": "refresh", "label": "Refresh now"},
                    {"key": "open_native_list", "label": "Open Native List"},
                ],
            }
        }

        result = worklist._apply_worklist_operating_contract(payload)
        action_keys = [action["key"] for action in result["controls"]["actions"]]

        self.assertEqual(
            action_keys,
            ["refresh", "reset_filters", "apply_filters", "open_native_list"],
        )
        self.assertEqual(
            [action["key"] for action in result["controls"]["actions"]].count("refresh"),
            1,
        )
        self.assertEqual(result["controls"]["actions"][2]["kind"], "primary")

    def test_restricted_worklist_payload_exposes_native_fallback_action(self):
        payload = worklist._restricted_payload(
            "Items",
            "Restricted items queue",
            scope_note="Use the native list for this scope.",
            scope={"scope_mode": "permission_scope"},
            native_target={"kind": "list", "doctype": "Item"},
        )

        self.assertEqual(payload["results"]["state"]["action"]["key"], "open_native_list")
        self.assertEqual(payload["action_targets"]["open_native_list"]["doctype"], "Item")

    def test_worklist_route_unavailable_payload_keeps_standard_top_actions(self):
        with patch.object(worklist.service, "_build_context", return_value={}), patch.object(
            worklist.service,
            "_build_scope",
            return_value={"scope_mode": "permission_scope"},
        ):
            payload = worklist.get_sales_console_worklist_context("unknown_queue")

        self.assertEqual(
            [action["key"] for action in payload["controls"]["actions"]],
            ["refresh"],
        )

    def test_item_directory_uses_concise_sales_subtitle(self):
        with patch.object(worklist.service, "_can_read", return_value=True), patch.object(
            worklist,
            "_fetch_item_worklist_rows",
            return_value=[],
        ), patch.object(worklist, "_item_group_options", return_value=[]):
            payload = worklist._build_item_worklist({"scope_mode": "permission_scope"}, {})

        self.assertEqual(
            payload["summary"]["subtitle"],
            "Sales items available for quotation and order entry, with current stock posture.",
        )

    def test_item_detail_price_prefers_active_standard_selling_price(self):
        fields = {
            "name",
            "item_code",
            "price_list",
            "price_list_rate",
            "currency",
            "uom",
            "valid_from",
            "valid_upto",
            "selling",
        }

        with patch.object(worklist.service, "_doctype_exists", return_value=True), patch.object(
            worklist.service,
            "_can_read",
            return_value=True,
        ), patch.object(worklist.service, "_fieldnames", return_value=fields), patch.object(
            worklist.frappe,
            "get_list",
            return_value=[
                {
                    "item_code": "ITEM-1",
                    "price_list": "Retail Selling",
                    "price_list_rate": 900,
                    "currency": "MMK",
                    "uom": "Nos",
                    "valid_from": date(2026, 1, 1),
                },
                {
                    "item_code": "ITEM-1",
                    "price_list": "Standard Selling",
                    "price_list_rate": 1200,
                    "currency": "MMK",
                    "uom": "Nos",
                    "valid_from": date(2026, 2, 1),
                },
            ],
        ), patch.object(worklist, "nowdate", return_value=date(2026, 5, 3)), patch.object(
            worklist,
            "getdate",
            side_effect=lambda value=None: value if isinstance(value, date) else date.fromisoformat(str(value)),
        ):
            result = worklist._fetch_item_selling_price("ITEM-1", stock_uom="Nos")

        self.assertEqual(result["label"], "Standard Selling Price")
        self.assertEqual(result["value"], "1200")
        self.assertEqual(result["meta"], "Standard Selling · Nos")
        self.assertEqual(result["tone"], "positive")

    def test_report_operating_contract_adds_standard_actions_without_duplicates(self):
        payload = {
            "controls": {
                "actions": [
                    {"key": "refresh", "label": "Refresh now"},
                    {"key": "open_native_report", "label": "Open Native Report"},
                ]
            }
        }

        result = report._apply_report_operating_contract(payload)

        self.assertEqual(
            [action["key"] for action in result["controls"]["actions"]],
            ["refresh", "back_to_console", "open_native_report"],
        )

    def test_report_route_unavailable_payload_keeps_standard_top_actions(self):
        with patch.object(report.service, "_build_context", return_value={}), patch.object(
            report.service,
            "_build_scope",
            return_value={"scope_mode": "permission_scope"},
        ):
            payload = report.get_sales_console_report_context("unknown_report")

        self.assertEqual(
            [action["key"] for action in payload["controls"]["actions"]],
            ["refresh", "back_to_console"],
        )

    def test_hidden_report_direct_route_is_blocked_by_role_catalog(self):
        with patch.object(report.service, "_build_context", return_value={"role_variant": "sales_executive"}), patch.object(
            report.service,
            "_build_scope",
            return_value={"scope_mode": "permission_scope"},
        ), patch.object(
            report.service,
            "_build_reports_catalog",
            return_value=[
                {"key": "trend_analysis", "title": "Trend Analysis"},
                {"key": "sales_order_analysis", "title": "Sales Order Analysis"},
                {"key": "collections_status", "title": "Collections Status"},
            ],
        ):
            payload = report.get_sales_console_report_context("lost_quotations")

        self.assertEqual(payload["summary"]["title"], "Report restricted")
        self.assertEqual(payload["results"]["state"]["title"], "Report not available for this role")
        self.assertEqual(
            [action["key"] for action in payload["controls"]["actions"]],
            ["refresh", "back_to_console"],
        )

    def test_sales_order_analysis_defaults_to_rolling_operating_window(self):
        def fake_getdate(value=None):
            if isinstance(value, date):
                return value
            return date.fromisoformat(str(value))

        with patch.object(report, "nowdate", return_value="2026-05-02"), patch.object(
            report,
            "getdate",
            side_effect=fake_getdate,
        ), patch.object(report, "_default_company", return_value="Demo Company"):
            filters = report._sales_order_analysis_filters()

        self.assertEqual(filters["from_date"], "2026-04-02")
        self.assertEqual(filters["to_date"], "2026-05-02")

    def test_trend_analysis_uses_document_type_filter_and_sales_console_contract(self):
        trend_columns = {
            "columns": [
                "Customer:Link/Customer:120",
                "Customer Name:Data:120",
                "Territory:Link/Territory:120",
                "Currency:Link/Currency:120",
                "Apr (Qty):Float:120",
                "Apr (Amt):Currency/currency:120",
                "Total(Qty):Float:120",
                "Total(Amt):Currency/currency:120",
            ]
        }
        trend_rows = [
            ["CUST-1", "CUST-1", "Yangon", "MMK", 2, 1500, 2, 1500],
            ["'Total'", None, None, "MMK", 2, 1500, 2, 1500],
        ]

        with patch.object(report.service, "_build_context", return_value={}), patch.object(
            report.service,
            "_build_scope",
            return_value={"scope_mode": "permission_scope"},
        ), patch.object(report.service, "_can_read", return_value=True), patch.object(
            report, "_current_fiscal_year_window", return_value={"name": "2026-2027"}
        ), patch.object(report, "_fiscal_year_options", return_value=[{"label": "2026-2027", "value": "2026-2027"}]), patch.object(
            report, "_default_company", return_value="Demo Company"
        ), patch.object(report, "_company_currency", return_value="MMK"), patch.object(
            report, "get_trend_columns", return_value=trend_columns
        ), patch.object(report, "get_trend_data", return_value=trend_rows), patch.object(
            report, "_link_target_exists", return_value=False
        ):
            payload = report.get_sales_console_report_context("trend_analysis")

        self.assertEqual(payload["page"]["title"], "Trend Analysis")
        self.assertEqual(
            [field["key"] for field in payload["controls"]["fields"]],
            ["document_type", "based_on", "period", "fiscal_year"],
        )
        self.assertEqual(payload["controls"]["fields"][0]["value"], "Sales Invoice")
        self.assertEqual(payload["metrics"]["items"][0]["label"], "Billed value")
        self.assertEqual(payload["secondary"]["chart"]["points"][0]["label"], "Apr")
        self.assertEqual(
            [action["key"] for action in payload["controls"]["actions"]],
            ["refresh", "back_to_console"],
        )

    def test_legacy_quotation_trends_route_opens_trend_analysis_with_quotation_selected(self):
        with patch.object(report.service, "_build_context", return_value={}), patch.object(
            report.service,
            "_build_scope",
            return_value={"scope_mode": "permission_scope"},
        ), patch.object(report.service, "_can_read", return_value=False), patch.object(
            report, "_current_fiscal_year_window", return_value={"name": "2026-2027"}
        ), patch.object(report, "_fiscal_year_options", return_value=[{"label": "2026-2027", "value": "2026-2027"}]), patch.object(
            report, "_default_company", return_value="Demo Company"
        ):
            payload = report.get_sales_console_report_context("quotation_trends")

        self.assertEqual(payload["page"]["title"], "Trend Analysis")
        self.assertEqual(payload["controls"]["fields"][0]["value"], "Quotation")

    def test_quotation_directory_route_uses_shared_worklist_contract(self):
        def fake_fieldnames(doctype):
            if doctype == "Quotation":
                return {"name", "customer_name", "party_name", "transaction_date", "valid_till", "status", "workflow_state", "grand_total", "currency", "modified", "docstatus", "owner"}
            return {"name", "docstatus"}

        with patch.object(worklist, "nowdate", return_value=date(2026, 4, 23)), patch.object(
            worklist,
            "getdate",
            side_effect=lambda value=None: value if isinstance(value, date) else date.fromisoformat(str(value)),
        ), patch.object(worklist.service, "_build_context", return_value={}), patch.object(
            worklist.service,
            "_build_scope",
            return_value={"scope_mode": "permission_scope"},
        ), patch.object(worklist.service, "_can_read", return_value=True), patch.object(
            worklist.service,
            "_fieldnames",
            side_effect=fake_fieldnames,
        ), patch.object(
            worklist.service,
            "_apply_scope_filters",
            return_value=([["docstatus", "!=", 2]], "Permission scope."),
        ), patch.object(
            worklist.service,
            "_configured_pending_states",
            return_value=["Pending Approval"],
        ), patch.object(
            worklist.frappe,
            "get_list",
            return_value=[
                {
                    "name": "QTN-1",
                    "customer_name": "Acme",
                    "valid_till": date(2026, 4, 30),
                    "status": "Open",
                    "workflow_state": "",
                    "grand_total": 100,
                    "currency": "USD",
                }
            ],
        ):
            payload = worklist.get_sales_console_worklist_context("quotation_directory")

        self.assertEqual(payload["page"]["title"], "Quotations")
        self.assertEqual(
            [field["key"] for field in payload["controls"]["fields"]],
            ["view", "status", "date_start", "date_end", "keyword"],
        )
        self.assertEqual(
            [action["key"] for action in payload["controls"]["actions"]],
            ["refresh", "reset_filters", "apply_filters"],
        )

    def test_sales_order_directory_route_uses_shared_worklist_contract(self):
        def fake_fieldnames(doctype):
            if doctype == "Sales Order":
                return {"name", "customer", "transaction_date", "delivery_date", "status", "workflow_state", "per_delivered", "per_billed", "grand_total", "currency", "modified", "docstatus", "owner"}
            return {"name", "docstatus"}

        with patch.object(worklist, "nowdate", return_value=date(2026, 4, 23)), patch.object(
            worklist,
            "getdate",
            side_effect=lambda value=None: value if isinstance(value, date) else date.fromisoformat(str(value)),
        ), patch.object(worklist.service, "_build_context", return_value={}), patch.object(
            worklist.service,
            "_build_scope",
            return_value={"scope_mode": "permission_scope"},
        ), patch.object(worklist.service, "_can_read", return_value=True), patch.object(
            worklist.service,
            "_fieldnames",
            side_effect=fake_fieldnames,
        ), patch.object(
            worklist.service,
            "_apply_scope_filters",
            return_value=([["docstatus", "!=", 2]], "Permission scope."),
        ), patch.object(
            worklist.service,
            "_configured_pending_states",
            return_value=["Pending Approval"],
        ), patch.object(
            worklist.frappe,
            "get_list",
            return_value=[
                {
                    "name": "SO-1",
                    "customer": "Acme",
                    "delivery_date": date(2026, 4, 25),
                    "status": "To Deliver",
                    "workflow_state": "",
                    "per_delivered": 20,
                    "per_billed": 0,
                    "grand_total": 200,
                    "currency": "USD",
                }
            ],
        ):
            payload = worklist.get_sales_console_worklist_context("sales_order_directory")

        self.assertEqual(payload["page"]["title"], "Sales Orders")
        self.assertEqual(
            [field["key"] for field in payload["controls"]["fields"]],
            ["view", "status", "date_start", "date_end", "keyword"],
        )
        self.assertEqual(
            [action["key"] for action in payload["controls"]["actions"]],
            ["refresh", "reset_filters", "apply_filters"],
        )


if __name__ == "__main__":
    unittest.main()
