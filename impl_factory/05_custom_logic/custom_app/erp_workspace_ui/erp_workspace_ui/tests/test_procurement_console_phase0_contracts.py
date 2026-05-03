import sys
import types
import unittest


fake_frappe = types.ModuleType("frappe")
CURRENT_ROLES = []


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


fake_frappe.whitelist = _identity_whitelist
fake_frappe.PermissionError = _FakePermissionError
fake_frappe.ValidationError = Exception
fake_frappe.throw = _throw
fake_frappe.session = types.SimpleNamespace(user="purchase@example.com")
fake_frappe.db = types.SimpleNamespace(
    get_value=lambda *args, **kwargs: None,
    exists=lambda *args, **kwargs: False,
    get_single_value=lambda *args, **kwargs: None,
)
fake_frappe.defaults = types.SimpleNamespace(
    get_user_default=lambda *args, **kwargs: None,
    get_default=lambda *args, **kwargs: None,
)
fake_frappe.get_roles = lambda *args, **kwargs: list(CURRENT_ROLES)
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


class TestProcurementConsolePhase0Contracts(unittest.TestCase):
    def setUp(self):
        _set_user("purchase@example.com", ["Purchase User"])

    def test_guest_bootstrap_raises_permission_error(self):
        _set_user("Guest", [])

        with self.assertRaises(_FakePermissionError):
            service.get_procurement_console_bootstrap()

    def test_procurement_bootstrap_returns_unavailable_placeholder(self):
        payload = service.get_procurement_console_bootstrap()

        self.assertEqual(payload["workspace"]["workspace_id"], "procurement")
        self.assertEqual(payload["state"]["kind"], "unavailable")
        self.assertEqual(payload["scope"]["default_routing_enabled"], False)
        self.assertEqual(payload["queues"], [])
        self.assertEqual(payload["reports_catalog"], [])
        self.assertEqual(
            [item["key"] for item in payload["sidebar"]["items"]],
            ["procurement_console_home"],
        )

    def test_purchase_roles_do_not_receive_default_app_in_phase0(self):
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

    def test_sidebar_context_uses_placeholder_state(self):
        payload = service.get_procurement_console_sidebar_context()

        self.assertEqual(payload["state"]["kind"], "unavailable")
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

    def test_unknown_worklist_returns_unavailable_not_error(self):
        payload = worklist.get_procurement_console_worklist_context("unknown_queue")

        self.assertEqual(payload["results"]["state"]["kind"], "unavailable")
        self.assertNotEqual(payload["results"]["state"]["kind"], "error")
        self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["refresh"])

    def test_reserved_worklist_returns_unavailable_not_ready(self):
        payload = worklist.get_procurement_console_worklist_context("supplier_directory")

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
