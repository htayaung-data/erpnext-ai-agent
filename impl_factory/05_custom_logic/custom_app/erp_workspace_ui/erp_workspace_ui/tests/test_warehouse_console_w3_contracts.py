import datetime as _dt
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
    "Purchase Order Item",
    "Pick List",
    "Material Request",
    "Purchase Receipt",
    "Purchase Receipt Item",
}
COUNT_CALLS = []
LIST_CALLS = []
GET_ALL_CALLS = []
GET_DOC_CALLS = []

PO_ROWS = [
    {
        "name": "PO-OVERDUE",
        "supplier": "SUP-001",
        "supplier_name": "Acme Supply",
        "transaction_date": "2026-05-15",
        "schedule_date": "2026-05-24",
        "status": "To Receive",
        "per_received": 0,
        "set_warehouse": "Stores - M",
        "modified": "2026-05-25 08:00:00",
    },
    {
        "name": "PO-TODAY",
        "supplier": "SUP-002",
        "supplier_name": "Today Trading",
        "transaction_date": "2026-05-20",
        "schedule_date": "2026-05-27",
        "status": "To Receive and Bill",
        "per_received": 0,
        "set_warehouse": "Receiving - M",
        "modified": "2026-05-26 08:00:00",
    },
    {
        "name": "PO-PARTIAL",
        "supplier": "SUP-003",
        "supplier_name": "Partial Goods",
        "transaction_date": "2026-05-20",
        "schedule_date": "2026-06-02",
        "status": "To Receive",
        "per_received": 35,
        "set_warehouse": "Main - M",
        "modified": "2026-05-26 09:00:00",
    },
    {
        "name": "PO-SOON",
        "supplier": "SUP-004",
        "supplier_name": "Soon Supply",
        "transaction_date": "2026-05-21",
        "schedule_date": "2026-06-05",
        "status": "To Receive",
        "per_received": 0,
        "set_warehouse": "Main - M",
        "modified": "2026-05-26 10:00:00",
    },
    {
        "name": "PO-FAR",
        "supplier": "SUP-005",
        "supplier_name": "Future Supply",
        "transaction_date": "2026-05-21",
        "schedule_date": "2026-07-20",
        "status": "To Receive",
        "per_received": 0,
        "set_warehouse": "Future - M",
        "modified": "2026-05-26 11:00:00",
    },
]

PR_ROWS = [
    {"name": "PR-0001", "posting_date": "2026-05-25", "status": "Completed", "docstatus": 1, "modified": "2026-05-25 12:00:00"},
]

PR_ITEM_ROWS = [
    {
        "parent": "PR-0001",
        "item_code": "ITEM-003",
        "item_name": "Valve Set",
        "qty": 7,
        "warehouse": "Main - M",
        "purchase_order": "PO-PARTIAL",
        "purchase_order_item": "POI-0003",
        "stock_uom": "Nos",
        "uom": "Nos",
    },
]

PO_ITEM_ROWS = [
    {
        "parent": "PO-OVERDUE",
        "item_code": "ITEM-001",
        "item_name": "Filter Kit",
        "schedule_date": "2026-05-24",
        "expected_delivery_date": "2026-05-24",
        "qty": 10,
        "received_qty": 0,
        "warehouse": "Stores - M",
        "stock_uom": "Nos",
        "uom": "Nos",
    },
    {
        "parent": "PO-TODAY",
        "item_code": "ITEM-002",
        "item_name": "Packing Roll",
        "schedule_date": "2026-05-27",
        "expected_delivery_date": "2026-05-27",
        "qty": 6,
        "received_qty": 0,
        "warehouse": "Receiving - M",
        "stock_uom": "Nos",
        "uom": "Nos",
    },
    {
        "parent": "PO-PARTIAL",
        "item_code": "ITEM-003",
        "item_name": "Valve Set",
        "schedule_date": "2026-06-02",
        "expected_delivery_date": "2026-06-02",
        "qty": 20,
        "received_qty": 7,
        "warehouse": "Main - M",
        "stock_uom": "Nos",
        "uom": "Nos",
    },
    {
        "parent": "PO-SOON",
        "item_code": "ITEM-004",
        "item_name": "Fastener Pack",
        "schedule_date": "2026-06-05",
        "expected_delivery_date": "2026-06-05",
        "qty": 12,
        "received_qty": 0,
        "warehouse": "Main - M",
        "stock_uom": "Nos",
        "uom": "Nos",
    },
    {
        "parent": "PO-FAR",
        "item_code": "ITEM-005",
        "item_name": "Future Part",
        "schedule_date": "2026-07-20",
        "expected_delivery_date": "2026-07-20",
        "qty": 4,
        "received_qty": 0,
        "warehouse": "Future - M",
        "stock_uom": "Nos",
        "uom": "Nos",
    },
]


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
        "Purchase Order": {
            "docstatus",
            "status",
            "per_received",
            "schedule_date",
            "supplier",
            "supplier_name",
            "transaction_date",
            "set_warehouse",
            "modified",
        },
        "Purchase Order Item": {
            "name",
            "parent",
            "item_code",
            "item_name",
            "schedule_date",
            "expected_delivery_date",
            "qty",
            "received_qty",
            "warehouse",
            "stock_uom",
            "uom",
            "idx",
        },
        "Purchase Receipt": {"posting_date", "status", "docstatus", "modified"},
        "Purchase Receipt Item": {
            "parent",
            "item_code",
            "item_name",
            "qty",
            "warehouse",
            "purchase_order",
            "purchase_order_item",
            "stock_uom",
            "uom",
        },
        "Pick List": {"docstatus", "status"},
        "Material Request": {"docstatus", "material_request_type", "status"},
    }
    return _FakeMeta(fields.get(doctype, set()))


def _selected(row, fields):
    if fields == ["name"]:
        return {"name": row.get("name")}
    return {field: row.get(field) for field in fields}


def _filter_purchase_orders(filters):
    rows = list(PO_ROWS)
    for condition in filters or []:
        if not isinstance(condition, list) or len(condition) < 4:
            continue
        _, field, operator, value = condition[:4]
        if field == "name" and operator == "like":
            needle = str(value).replace("%", "").lower()
            rows = [row for row in rows if needle in row["name"].lower()]
        if field == "name" and operator == "=":
            rows = [row for row in rows if row["name"] == value]
        if field == "supplier_name" and operator == "like":
            needle = str(value).replace("%", "").lower()
            rows = [row for row in rows if needle in row["supplier_name"].lower()]
        if field == "supplier" and operator == "like":
            needle = str(value).replace("%", "").lower()
            rows = [row for row in rows if needle in row["supplier"].lower()]
        if field == "status" and operator == "in":
            rows = [row for row in rows if row["status"] in set(value)]
        if field == "per_received" and operator == "<":
            rows = [row for row in rows if float(row["per_received"]) < float(value)]
        if field == "docstatus" and operator == "=":
            rows = [row for row in rows if int(value) == 1]
    return rows


def _get_list(doctype, fields=None, filters=None, order_by=None, limit_page_length=None, **kwargs):
    LIST_CALLS.append({"doctype": doctype, "fields": fields, "filters": filters, "limit": limit_page_length})
    if doctype == "Purchase Order":
        rows = _filter_purchase_orders(filters)
        return [_selected(row, fields or ["name"]) for row in rows[: limit_page_length or len(rows)]]
    return []


def _get_all(doctype, fields=None, filters=None, order_by=None, limit_page_length=None, **kwargs):
    GET_ALL_CALLS.append({"doctype": doctype, "fields": fields, "filters": filters, "limit": limit_page_length})
    if doctype == "Purchase Order Item":
        parent_filter = (filters or {}).get("parent") if isinstance(filters, dict) else None
        if isinstance(parent_filter, list) and parent_filter[0] == "in":
            parents = set(parent_filter[1])
        elif parent_filter:
            parents = {parent_filter}
        else:
            parents = set()
        rows = [row for row in PO_ITEM_ROWS if not parents or row["parent"] in parents]
        return [_selected(row, fields or ["parent"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Purchase Receipt Item":
        purchase_order = (filters or {}).get("purchase_order") if isinstance(filters, dict) else None
        rows = [row for row in PR_ITEM_ROWS if not purchase_order or row["purchase_order"] == purchase_order]
        return [_selected(row, fields or ["parent"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Purchase Receipt":
        name_filter = (filters or {}).get("name") if isinstance(filters, dict) else None
        names = set(name_filter[1]) if isinstance(name_filter, list) and name_filter[0] == "in" else set()
        rows = [row for row in PR_ROWS if not names or row["name"] in names]
        return [_selected(row, fields or ["name"]) for row in rows[: limit_page_length or len(rows)]]
    return []


def _get_doc(doctype, name, *args, **kwargs):
    GET_DOC_CALLS.append({"doctype": doctype, "name": name})
    if doctype != "Purchase Order":
        raise Exception("Unsupported DocType")
    if not _has_permission(doctype, "read"):
        raise _FakePermissionError("No read permission")
    record = next((row for row in PO_ROWS if row["name"] == name), None)
    if not record:
        raise Exception("Missing Purchase Order")

    class _FakePurchaseOrderDoc:
        def get(self, fieldname, default=None):
            if fieldname == "items":
                return [dict(row) for row in PO_ITEM_ROWS if row["parent"] == name]
            return record.get(fieldname, default)

        def check_permission(self, ptype=None):
            if not _has_permission(doctype, ptype):
                raise _FakePermissionError("No read permission")
            return True

    return _FakePurchaseOrderDoc()


def _flt(value=0):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def _getdate(value=None):
    if isinstance(value, _dt.date):
        return value
    return _dt.datetime.strptime(str(value or "2026-05-27")[:10], "%Y-%m-%d").date()


fake_frappe.whitelist = _identity_whitelist
fake_frappe.PermissionError = _FakePermissionError
fake_frappe.throw = _throw
fake_frappe.session = types.SimpleNamespace(user="warehouse@example.com")
fake_frappe.get_roles = lambda *args, **kwargs: list(CURRENT_ROLES)
fake_frappe.has_permission = _has_permission
fake_frappe.get_meta = _get_meta
fake_frappe.get_list = _get_list
fake_frappe.get_all = _get_all
fake_frappe.get_doc = _get_doc
fake_frappe.db = types.SimpleNamespace(count=_count)
fake_frappe._ = lambda message: message

fake_utils = types.ModuleType("frappe.utils")
fake_utils.cstr = lambda value="": "" if value is None else str(value)
fake_utils.flt = _flt
fake_utils.getdate = _getdate
fake_utils.now_datetime = lambda: "2026-05-27 00:00:00"
fake_utils.nowdate = lambda: "2026-05-27"

sys.modules["frappe"] = fake_frappe
sys.modules["frappe.utils"] = fake_utils

from erp_workspace_ui.warehouse_console import service
from erp_workspace_ui.workspace_registry import get_warehouse_workspace_definition


class TestWarehouseConsoleW4BContracts(unittest.TestCase):
    def setUp(self):
        CURRENT_ROLES[:] = ["Stock User"]
        READABLE_DOCTYPES.update({
            "Warehouse",
            "Bin",
            "Item",
            "Purchase Order",
            "Purchase Order Item",
            "Pick List",
            "Material Request",
        })
        COUNT_CALLS.clear()
        LIST_CALLS.clear()
        GET_ALL_CALLS.clear()
        GET_DOC_CALLS.clear()

    def test_warehouse_workspace_registry_definition_has_w4b_receiving_route(self):
        workspace = get_warehouse_workspace_definition()

        self.assertEqual(workspace["workspace_id"], "warehouse")
        self.assertEqual(workspace["status"], "w4b_receiving_review")
        self.assertEqual(
            workspace["routes"],
            {
                "home": "warehouse-console",
                "home_path": "/desk/warehouse-console",
                "worklist": "warehouse-console-worklist",
                "worklist_path": "/desk/warehouse-console-worklist",
                "receiving": "warehouse-console-receiving",
                "receiving_path": "/desk/warehouse-console-receiving",
            },
        )
        self.assertEqual(
            workspace["methods"]["overview"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview",
        )
        self.assertEqual(
            workspace["methods"]["inbound_queue"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_inbound_receiving_queue",
        )
        self.assertEqual(
            workspace["methods"]["receiving_detail"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_receiving_review",
        )
        self.assertFalse(workspace["search"]["enabled"])
        self.assertEqual([item["key"] for item in workspace["fallback_items"]], [
            "warehouse_console_home",
            "inbound_receiving",
        ])

    def test_overview_payload_adds_inbound_preview_and_hides_valuation(self):
        payload = service.get_warehouse_console_overview()

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertTrue(payload["context"]["has_warehouse_access"])
        self.assertEqual(payload["valuation"], {"visible": False, "fields": []})
        self.assertEqual(payload["action_targets"], {})
        self.assertEqual(payload["allowed_actions"], [{"key": "refresh", "label": "Refresh", "kind": "read_only"}])
        self.assertIn("inbound", payload)
        self.assertEqual(payload["inbound"]["queue_route"], "warehouse-console-worklist")
        self.assertEqual(payload["inbound"]["counts"]["overdue"], 1)
        self.assertEqual(payload["inbound"]["counts"]["due_today"], 1)
        self.assertEqual(payload["inbound"]["counts"]["partially_received"], 1)
        self.assertEqual(payload["inbound"]["counts"]["expected_soon"], 1)
        self.assertLessEqual(len(payload["inbound"]["preview_rows"]), 6)
        self.assertIn("Inbound Work", {section["title"] for section in payload["sections"]})
        payload_text = str(payload).lower()
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("base_net_rate", payload_text)
        self.assertNotIn("amount", payload_text)
        self.assertNotIn("/app/", payload_text)

    def test_inbound_queue_payload_is_grouped_read_only_and_allowlisted(self):
        payload = service.get_warehouse_inbound_receiving_queue("inbound_receiving")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"], {"title": "Inbound Receiving", "key": "inbound_receiving"})
        self.assertEqual(payload["action_targets"], {})
        self.assertEqual(payload["valuation"], {"visible": False, "fields": []})
        self.assertEqual(len(payload["rows"]), 4)
        groups = {group["key"]: group for group in payload["groups"]}
        self.assertEqual(len(groups["overdue"]["rows"]), 1)
        self.assertEqual(len(groups["due_today"]["rows"]), 1)
        self.assertEqual(len(groups["partially_received"]["rows"]), 1)
        self.assertEqual(len(groups["expected_soon"]["rows"]), 1)

        allowed_row_keys = {
            "key",
            "name",
            "purchase_order",
            "supplier",
            "required_date",
            "target_warehouse",
            "line_count",
            "item_count",
            "received_percent",
            "remaining_summary",
            "status",
            "state_key",
            "state_label",
            "age_label",
            "lines",
        }
        for row in payload["rows"]:
            self.assertLessEqual(set(row), allowed_row_keys)
            self.assertNotIn("rate", row)
            self.assertNotIn("amount", row)
            self.assertNotIn("stock_value", row)
        self.assertTrue(any(call["doctype"] == "Purchase Order" for call in LIST_CALLS))
        self.assertTrue(any(call["doctype"] == "Purchase Order Item" for call in GET_ALL_CALLS))

    def test_receiving_review_uses_parent_purchase_order_when_child_table_read_is_unavailable(self):
        READABLE_DOCTYPES.discard("Purchase Order Item")

        payload = service.get_warehouse_receiving_review("PO-PARTIAL")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertGreaterEqual(len(payload["lines"]), 1)
        self.assertEqual(payload["lines"][0]["item_code"], "ITEM-003")
        self.assertFalse(any(call["doctype"] == "Purchase Order Item" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Purchase Order" for call in GET_DOC_CALLS))
        self.assertNotIn("valuation_rate", str(payload).lower())

    def test_inbound_queue_filters_stay_within_product_route_scope(self):
        payload = service.get_warehouse_inbound_receiving_queue(
            "inbound-receiving",
            {"state": "overdue", "supplier": "Acme"},
        )

        self.assertEqual([row["purchase_order"] for row in payload["rows"]], ["PO-OVERDUE"])
        self.assertEqual(payload["controls"]["fields"][1]["value"], "Acme")
        self.assertEqual(payload["controls"]["fields"][3]["value"], "overdue")
        self.assertEqual(payload["workspace"]["routes"]["worklist"], "warehouse-console-worklist")
        self.assertNotIn("native", str(payload).lower())


    def test_receiving_review_payload_is_read_only_allowlisted_and_history_bounded(self):
        payload = service.get_warehouse_receiving_review("PO-PARTIAL")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"]["purchase_order"], "PO-PARTIAL")
        self.assertEqual(payload["valuation"], {"visible": False, "fields": []})
        self.assertEqual(payload["action_targets"]["inbound_queue"]["route"], "warehouse-console-worklist")
        self.assertEqual(payload["header"]["supplier"], "Partial Goods")
        self.assertEqual(payload["header"]["received_percent"], "35%")
        self.assertGreaterEqual(len(payload["lines"]), 1)
        self.assertLessEqual(len(payload["lines"]), service.RECEIVING_DETAIL_LINE_LIMIT)
        self.assertLessEqual(len(payload["receipt_history"]), service.RECEIVING_DETAIL_HISTORY_LIMIT)

        allowed_line_keys = {
            "item_code",
            "item_name",
            "ordered_qty",
            "received_qty",
            "remaining_qty",
            "uom",
            "target_warehouse",
            "required_date",
            "status",
        }
        for line in payload["lines"]:
            self.assertLessEqual(set(line), allowed_line_keys)
        payload_text = str(payload).lower()
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("base_net_rate", payload_text)
        self.assertNotIn("tax", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertTrue(any(call["doctype"] == "Purchase Order" for call in LIST_CALLS))
        self.assertTrue(any(call["doctype"] == "Purchase Order Item" for call in GET_ALL_CALLS))

    def test_restricted_role_gets_controlled_state_and_no_sidebar_items(self):
        CURRENT_ROLES[:] = ["Purchase Manager"]

        overview = service.get_warehouse_console_overview()
        queue = service.get_warehouse_inbound_receiving_queue("inbound_receiving")
        detail = service.get_warehouse_receiving_review("PO-OVERDUE")

        self.assertEqual(overview["state"]["kind"], "restricted")
        self.assertFalse(overview["context"]["has_warehouse_access"])
        self.assertEqual(overview["sidebar"]["sections"], [])
        self.assertEqual(overview["allowed_actions"], [])
        self.assertEqual(queue["state"]["kind"], "restricted")
        self.assertEqual(queue["rows"], [])
        self.assertEqual(detail["state"]["kind"], "restricted")
        self.assertEqual(detail["lines"], [])

    def test_permission_limited_sources_return_controlled_empty_inbound_state(self):
        READABLE_DOCTYPES.discard("Purchase Order")

        overview = service.get_warehouse_console_overview()
        queue = service.get_warehouse_inbound_receiving_queue("inbound_receiving")
        metrics = {metric["key"]: metric for metric in overview["kpis"]}

        self.assertEqual(metrics["receiving_due"]["state"], "unavailable")
        self.assertIsNone(metrics["receiving_due"]["value"])
        self.assertEqual(queue["state"]["kind"], "restricted")
        self.assertEqual(queue["rows"], [])
        self.assertFalse(any(call["doctype"] == "Purchase Order" for call in LIST_CALLS))


if __name__ == "__main__":
    unittest.main()
