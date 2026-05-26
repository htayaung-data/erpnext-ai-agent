import sys
import types
import unittest


fake_frappe = types.ModuleType("frappe")
CURRENT_ROLES = []
READABLE_DOCTYPES = {
    "Warehouse",
    "Bin",
    "Item",
    "Purchase Order",
    "Pick List",
    "Material Request",
}
COUNT_CALLS = []


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
    COUNT_CALLS.append({"doctype": doctype, "filters": filters})
    return {
        "Warehouse": 4,
        "Bin": 8,
        "Purchase Order": 2,
        "Pick List": 1,
        "Material Request": 3,
    }.get(doctype, 0)


class _FakeMeta:
    def __init__(self, fields):
        self.fields = set(fields)

    def has_field(self, fieldname):
        return fieldname in self.fields


def _get_meta(doctype):
    fields = {
        "Warehouse": {"disabled", "is_group"},
        "Purchase Order": {"docstatus", "status", "per_received", "schedule_date"},
        "Pick List": {"docstatus", "status"},
        "Material Request": {"docstatus", "material_request_type", "status"},
    }
    return _FakeMeta(fields.get(doctype, set()))


fake_frappe.whitelist = _identity_whitelist
fake_frappe.PermissionError = _FakePermissionError
fake_frappe.throw = _throw
fake_frappe.session = types.SimpleNamespace(user="warehouse@example.com")
fake_frappe.get_roles = lambda *args, **kwargs: list(CURRENT_ROLES)
fake_frappe.has_permission = _has_permission
fake_frappe.get_meta = _get_meta
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.db = types.SimpleNamespace(count=_count)
fake_frappe._ = lambda message: message

fake_utils = types.ModuleType("frappe.utils")
fake_utils.cstr = lambda value="": "" if value is None else str(value)
fake_utils.now_datetime = lambda: "2026-05-26 00:00:00"
fake_utils.nowdate = lambda: "2026-05-26"

sys.modules["frappe"] = fake_frappe
sys.modules["frappe.utils"] = fake_utils

from erp_workspace_ui.warehouse_console import service
from erp_workspace_ui.workspace_registry import get_warehouse_workspace_definition


class TestWarehouseConsoleW3Contracts(unittest.TestCase):
    def setUp(self):
        CURRENT_ROLES[:] = ["Stock User"]
        READABLE_DOCTYPES.update({"Warehouse", "Bin", "Item", "Purchase Order", "Pick List", "Material Request"})
        COUNT_CALLS.clear()

    def test_warehouse_workspace_registry_definition_is_w3_only(self):
        workspace = get_warehouse_workspace_definition()

        self.assertEqual(workspace["workspace_id"], "warehouse")
        self.assertEqual(workspace["status"], "w3_read_only_overview")
        self.assertEqual(workspace["routes"], {"home": "warehouse-console", "home_path": "/desk/warehouse-console"})
        self.assertEqual(
            workspace["methods"]["overview"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview",
        )
        self.assertFalse(workspace["search"]["enabled"])
        self.assertEqual(
            workspace["fallback_items"],
            [
                {
                    "key": "warehouse_console_home",
                    "label": "Overview",
                    "icon": "item",
                    "target": {"kind": "page", "route": "warehouse-console"},
                }
            ],
        )

    def test_overview_payload_is_read_only_and_hides_valuation(self):
        payload = service.get_warehouse_console_overview()

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertTrue(payload["context"]["has_warehouse_access"])
        self.assertEqual(payload["valuation"], {"visible": False, "fields": []})
        self.assertEqual(payload["action_targets"], {})
        self.assertEqual(payload["allowed_actions"], [{"key": "refresh", "label": "Refresh", "kind": "read_only"}])
        self.assertEqual({metric["key"] for metric in payload["kpis"]}, {
            "active_warehouses",
            "stocked_items",
            "low_stock",
            "receiving_due",
            "outbound_due",
            "transfer_requests",
        })
        self.assertNotIn("stock_value", str(payload).lower())
        self.assertNotIn("valuation_rate", str(payload).lower())
        self.assertNotIn("doctype", str(payload).lower())

    def test_restricted_role_gets_controlled_state_and_no_sidebar_items(self):
        CURRENT_ROLES[:] = ["Purchase Manager"]

        payload = service.get_warehouse_console_overview()

        self.assertEqual(payload["state"]["kind"], "restricted")
        self.assertFalse(payload["context"]["has_warehouse_access"])
        self.assertEqual(payload["sidebar"]["sections"], [])
        self.assertEqual(payload["allowed_actions"], [])

    def test_permission_limited_sources_return_unavailable_metrics(self):
        READABLE_DOCTYPES.discard("Purchase Order")

        payload = service.get_warehouse_console_overview()
        metrics = {metric["key"]: metric for metric in payload["kpis"]}

        self.assertEqual(metrics["receiving_due"]["state"], "unavailable")
        self.assertIsNone(metrics["receiving_due"]["value"])
        self.assertTrue(any(call["doctype"] == "Bin" for call in COUNT_CALLS))
        self.assertFalse(any(call["doctype"] == "Purchase Order" for call in COUNT_CALLS))


if __name__ == "__main__":
    unittest.main()
