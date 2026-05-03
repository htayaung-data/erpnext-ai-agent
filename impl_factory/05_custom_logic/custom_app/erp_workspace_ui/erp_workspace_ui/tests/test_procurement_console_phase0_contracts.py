import sys
import types
import unittest


fake_frappe = types.ModuleType("frappe")
CURRENT_ROLES = []
READABLE_DOCTYPES = {"Supplier", "Material Request", "Purchase Order"}
CAPTURED_GET_LIST_CALLS = []


def _identity_whitelist(*args, **kwargs):
    if args and callable(args[0]) and len(args) == 1 and not kwargs:
        return args[0]

    def decorator(fn):
        return fn

    return decorator


class _FakePermissionError(Exception):
    pass


def _throw(message, exc=None):
    raise (exc or Exception)(message)


def _has_permission(doctype, ptype=None, *args, **kwargs):
    return ptype == "read" and doctype in READABLE_DOCTYPES


def _count(doctype, filters=None):
    return 3 if doctype in READABLE_DOCTYPES else 0


def _get_list(doctype, fields=None, filters=None, order_by=None, limit_page_length=None, **kwargs):
    CAPTURED_GET_LIST_CALLS.append(
        {
            "doctype": doctype,
            "fields": fields,
            "filters": filters,
            "order_by": order_by,
            "limit_page_length": limit_page_length,
        }
    )
    if doctype == "Supplier":
        return [
            {
                "name": "SUP-001",
                "supplier_name": "Alpha Supplier",
                "supplier_group": "All Supplier Groups",
                "disabled": 0,
                "modified": "2026-05-03",
            }
        ]
    if doctype == "Material Request":
        return [
            {
                "name": "MAT-MR-001",
                "title": "Purchase Material",
                "material_request_type": "Purchase",
                "company": "Demo Company",
                "transaction_date": "2026-05-02",
                "schedule_date": "2026-05-10",
                "status": "Submitted",
                "per_ordered": 0,
                "per_received": 0,
                "modified": "2026-05-03",
            }
        ]
    if doctype == "Purchase Order":
        return [
            {
                "name": "PUR-ORD-001",
                "supplier": "SUP-001",
                "supplier_name": "Alpha Supplier",
                "company": "Demo Company",
                "transaction_date": "2026-05-02",
                "schedule_date": "2026-05-10",
                "status": "To Receive and Bill",
                "workflow_state": "Pending Purchase Approval",
                "per_received": 0,
                "per_billed": 0,
                "grand_total": 1000,
                "currency": "MMK",
                "modified": "2026-05-03",
            }
        ]
    return []


fake_frappe.whitelist = _identity_whitelist
fake_frappe.PermissionError = _FakePermissionError
fake_frappe.ValidationError = Exception
fake_frappe.throw = _throw
fake_frappe.session = types.SimpleNamespace(user="purchase@example.com")
fake_frappe.db = types.SimpleNamespace(
    get_value=lambda *args, **kwargs: None,
    exists=lambda *args, **kwargs: False,
    get_single_value=lambda *args, **kwargs: None,
    count=_count,
)
fake_frappe.defaults = types.SimpleNamespace(
    get_user_default=lambda *args, **kwargs: None,
    get_default=lambda *args, **kwargs: None,
)
fake_frappe.get_roles = lambda *args, **kwargs: list(CURRENT_ROLES)
fake_frappe.has_permission = _has_permission
fake_frappe.get_list = _get_list
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
fake_utils.getdate = lambda value=None: value or "2026-05-03"
fake_utils.now_datetime = lambda: "2026-05-03 00:00:00"
fake_utils.nowdate = lambda: "2026-05-03"

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

sys.modules["frappe"] = fake_frappe
sys.modules["frappe.utils"] = fake_utils
sys.modules["frappe.utils.data"] = fake_utils_data
sys.modules["frappe.desk"] = fake_desk
sys.modules["frappe.desk.query_report"] = fake_query_report
sys.modules["erpnext"] = fake_erpnext
sys.modules["erpnext.controllers"] = fake_erpnext_controllers
sys.modules["erpnext.controllers.trends"] = fake_erpnext_trends

from erp_workspace_ui import boot
from erp_workspace_ui.procurement_console import report, service, worklist


def _set_user(user, roles):
    fake_frappe.session.user = user
    CURRENT_ROLES[:] = list(roles)


def _set_readable_doctypes(*doctypes):
    READABLE_DOCTYPES.clear()
    READABLE_DOCTYPES.update(doctypes)


def _filter_contains(filters, condition):
    return list(condition) in [list(item) for item in filters]


class TestProcurementConsolePhase1Contracts(unittest.TestCase):
    def setUp(self):
        _set_user("purchase@example.com", ["Purchase User"])
        _set_readable_doctypes("Supplier", "Material Request", "Purchase Order")
        CAPTURED_GET_LIST_CALLS.clear()

    def test_guest_bootstrap_raises_permission_error(self):
        _set_user("Guest", [])

        with self.assertRaises(_FakePermissionError):
            service.get_procurement_console_bootstrap()

    def test_procurement_bootstrap_returns_ready_buyer_workbench(self):
        payload = service.get_procurement_console_bootstrap()

        self.assertEqual(payload["workspace"]["workspace_id"], "procurement")
        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["scope"]["default_routing_enabled"], False)
        self.assertEqual(payload["reports_catalog"], [])
        self.assertEqual(
            [item["key"] for item in payload["sidebar"]["items"]],
            [
                "procurement_console_home",
                "supplier_directory",
                "purchase_request_directory",
                "purchase_order_directory",
            ],
        )
        self.assertEqual(
            sorted(payload["work"].keys()),
            [
                "purchase_orders_late_or_unreceived",
                "purchase_orders_open",
                "purchase_orders_pending_approval",
                "requests_to_source",
            ],
        )
        self.assertEqual(
            sorted(payload["directories"].keys()),
            ["purchase_order_directory", "purchase_request_directory", "supplier_directory"],
        )

    def test_purchase_roles_do_not_receive_default_app_in_phase1(self):
        _set_user("purchase@example.com", ["Purchase User"])

        self.assertIsNone(boot.resolve_default_app("purchase@example.com"))

    def test_non_procurement_bootstrap_returns_restricted(self):
        _set_user("sales@example.com", ["Sales User"])

        payload = service.get_procurement_console_bootstrap()

        self.assertEqual(payload["state"]["kind"], "restricted")
        self.assertEqual(payload["scope"]["scope_mode"], "restricted")

    def test_finance_and_executive_approvers_do_not_get_broad_access(self):
        _set_user("approver@example.com", ["Finance Lead Approver", "Executive Approver"])

        payload = service.get_procurement_console_bootstrap()

        self.assertEqual(payload["state"]["kind"], "restricted")
        self.assertEqual(payload["context"]["role_variant"], "restricted")

    def test_sidebar_context_is_ready_for_procurement_user(self):
        payload = service.get_procurement_console_sidebar_context()

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["sidebar"]["active_key"], "procurement_console_home")

    def test_search_placeholder_is_unavailable_for_procurement_user(self):
        payload = service.search_procurement_console_workspace("supplier")

        self.assertEqual(payload["state"], "unavailable")
        self.assertEqual(payload["results"], [])

    def test_search_is_restricted_for_non_procurement_user(self):
        _set_user("sales@example.com", ["Sales User"])

        payload = service.search_procurement_console_workspace("supplier")

        self.assertEqual(payload["state"], "restricted")
        self.assertEqual(payload["results"], [])

    def test_supplier_directory_uses_ready_read_only_list_contract(self):
        payload = worklist.get_procurement_console_worklist_context("supplier_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["refresh", "reset_filters", "apply_filters"])
        self.assertIn("No create or edit action", payload["controls"]["scopeChips"])
        self.assertEqual(payload["results"]["rows"][0]["actions"], [{"key": "open_record", "label": "Open"}])
        self.assertNotIn("create_supplier", str(payload))
        self.assertEqual(payload["action_targets"]["row:SUP-001:open_record"]["kind"], "form")

    def test_supplier_directory_restricted_without_supplier_read_permission(self):
        _set_readable_doctypes("Material Request", "Purchase Order")

        payload = worklist.get_procurement_console_worklist_context("supplier_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "restricted")
        self.assertEqual(payload["results"]["rows"], [])

    def test_material_request_directory_is_purchase_only(self):
        payload = worklist.get_procurement_console_worklist_context("purchase_request_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Material Request", "material_request_type", "=", "Purchase"]))

    def test_requests_to_source_enforces_purchase_and_not_fully_ordered(self):
        worklist.get_procurement_console_worklist_context("requests_to_source")

        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Material Request", "material_request_type", "=", "Purchase"]))
        self.assertTrue(_filter_contains(filters, ["Material Request", "docstatus", "=", 1]))
        self.assertTrue(_filter_contains(filters, ["Material Request", "per_ordered", "<", 100]))

    def test_purchase_order_pending_approval_is_visibility_only(self):
        payload = worklist.get_procurement_console_worklist_context("purchase_orders_pending_approval")

        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertTrue(_filter_contains(filters, ["Purchase Order", "workflow_state", "=", "Pending Purchase Approval"]))
        self.assertIn("No approval actions", payload["summary"]["chips"][0]["label"])
        self.assertNotIn("approve", str(payload).lower())
        self.assertNotIn("reject", str(payload).lower())

    def test_purchase_order_late_queue_uses_receipt_visibility_without_warehouse_ownership(self):
        worklist.get_procurement_console_worklist_context("purchase_orders_late_or_unreceived")

        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Purchase Order", "docstatus", "=", 1]))
        self.assertTrue(_filter_contains(filters, ["Purchase Order", "per_received", "<", 100]))

    def test_unknown_worklist_returns_unavailable_not_error(self):
        payload = worklist.get_procurement_console_worklist_context("unknown_queue")

        self.assertEqual(payload["results"]["state"]["kind"], "unavailable")
        self.assertNotEqual(payload["results"]["state"]["kind"], "error")
        self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["refresh"])

    def test_phase2_worklist_is_still_unavailable_not_ready(self):
        payload = worklist.get_procurement_console_worklist_context("rfq_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "unavailable")
        self.assertEqual(payload["results"]["rows"], [])

    def test_worklist_restricted_for_non_procurement_user(self):
        _set_user("sales@example.com", ["Sales User"])

        payload = worklist.get_procurement_console_worklist_context("supplier_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "restricted")

    def test_guest_worklist_raises_permission_error(self):
        _set_user("Guest", [])

        with self.assertRaises(_FakePermissionError):
            worklist.get_procurement_console_worklist_context("supplier_directory")

    def test_unknown_report_returns_unavailable_not_error(self):
        payload = report.get_procurement_console_report_context("unknown_report")

        self.assertEqual(payload["results"]["state"]["kind"], "unavailable")
        self.assertNotEqual(payload["results"]["state"]["kind"], "error")
        self.assertEqual(
            [action["key"] for action in payload["controls"]["actions"]],
            ["refresh", "back_to_console"],
        )

    def test_reserved_report_returns_unavailable_not_ready(self):
        payload = report.get_procurement_console_report_context("purchase_order_analysis")

        self.assertEqual(payload["results"]["state"]["kind"], "unavailable")
        self.assertEqual(payload["results"]["rows"], [])

    def test_report_restricted_for_non_procurement_user(self):
        _set_user("sales@example.com", ["Sales User"])

        payload = report.get_procurement_console_report_context("purchase_order_analysis")

        self.assertEqual(payload["results"]["state"]["kind"], "restricted")

    def test_guest_report_raises_permission_error(self):
        _set_user("Guest", [])

        with self.assertRaises(_FakePermissionError):
            report.get_procurement_console_report_context("purchase_order_analysis")


if __name__ == "__main__":
    unittest.main()
