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
    "Sales Order",
    "Sales Order Item",
    "Stock Entry",
    "Stock Entry Detail",
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

SO_ROWS = [
    {
        "name": "SO-OVERDUE",
        "customer": "CUST-001",
        "customer_name": "Apex Retail",
        "transaction_date": "2026-05-20",
        "delivery_date": "2026-05-24",
        "status": "To Deliver",
        "per_delivered": 0,
        "set_warehouse": "Stores - M",
        "modified": "2026-05-25 08:00:00",
    },
    {
        "name": "SO-TODAY",
        "customer": "CUST-002",
        "customer_name": "Today Retail",
        "transaction_date": "2026-05-21",
        "delivery_date": "2026-05-27",
        "status": "To Deliver and Bill",
        "per_delivered": 0,
        "set_warehouse": "Main - M",
        "modified": "2026-05-26 08:00:00",
    },
    {
        "name": "SO-READY",
        "customer": "CUST-003",
        "customer_name": "Ready Customer",
        "transaction_date": "2026-05-22",
        "delivery_date": "2026-06-01",
        "status": "To Deliver",
        "per_delivered": 0,
        "set_warehouse": "Main - M",
        "modified": "2026-05-26 09:00:00",
    },
    {
        "name": "SO-PARTIAL",
        "customer": "CUST-004",
        "customer_name": "Partial Customer",
        "transaction_date": "2026-05-23",
        "delivery_date": "2026-06-02",
        "status": "To Deliver",
        "per_delivered": 45,
        "set_warehouse": "Main - M",
        "modified": "2026-05-26 10:00:00",
    },
    {
        "name": "SO-REVIEW",
        "customer": "CUST-005",
        "customer_name": "Review Customer",
        "transaction_date": "2026-05-24",
        "delivery_date": "2026-06-03",
        "status": "To Deliver",
        "per_delivered": 0,
        "set_warehouse": "Short - M",
        "modified": "2026-05-26 11:00:00",
    },
    {
        "name": "SO-FAR",
        "customer": "CUST-006",
        "customer_name": "Future Customer",
        "transaction_date": "2026-05-25",
        "delivery_date": "2026-07-20",
        "status": "To Deliver",
        "per_delivered": 0,
        "set_warehouse": "Future - M",
        "modified": "2026-05-26 12:00:00",
    },
]

SO_ITEM_ROWS = [
    {"parent": "SO-OVERDUE", "item_code": "ITEM-101", "item_name": "Phone Case", "delivery_date": "2026-05-24", "qty": 4, "delivered_qty": 0, "warehouse": "Stores - M", "stock_uom": "Nos", "uom": "Nos"},
    {"parent": "SO-TODAY", "item_code": "ITEM-102", "item_name": "Screen Guard", "delivery_date": "2026-05-27", "qty": 6, "delivered_qty": 0, "warehouse": "Main - M", "stock_uom": "Nos", "uom": "Nos"},
    {"parent": "SO-READY", "item_code": "ITEM-103", "item_name": "Bluetooth Speaker", "delivery_date": "2026-06-01", "qty": 5, "delivered_qty": 0, "warehouse": "Main - M", "stock_uom": "Nos", "uom": "Nos"},
    {"parent": "SO-PARTIAL", "item_code": "ITEM-104", "item_name": "Cable Pack", "delivery_date": "2026-06-02", "qty": 10, "delivered_qty": 4, "warehouse": "Main - M", "stock_uom": "Nos", "uom": "Nos"},
    {"parent": "SO-REVIEW", "item_code": "ITEM-105", "item_name": "Power Bank", "delivery_date": "2026-06-03", "qty": 8, "delivered_qty": 0, "warehouse": "Short - M", "stock_uom": "Nos", "uom": "Nos"},
    {"parent": "SO-FAR", "item_code": "ITEM-106", "item_name": "Future Kit", "delivery_date": "2026-07-20", "qty": 3, "delivered_qty": 0, "warehouse": "Future - M", "stock_uom": "Nos", "uom": "Nos"},
]

BIN_ROWS = [
    {"item_code": "ITEM-101", "warehouse": "Stores - M", "actual_qty": 8, "reserved_qty": 0, "projected_qty": 8},
    {"item_code": "ITEM-102", "warehouse": "Main - M", "actual_qty": 6, "reserved_qty": 0, "projected_qty": 6},
    {"item_code": "ITEM-103", "warehouse": "Main - M", "actual_qty": 12, "reserved_qty": 0, "projected_qty": 12},
    {"item_code": "ITEM-104", "warehouse": "Main - M", "actual_qty": 12, "reserved_qty": 0, "projected_qty": 12},
    {"item_code": "ITEM-105", "warehouse": "Short - M", "actual_qty": 2, "reserved_qty": 0, "projected_qty": 2},
    {"item_code": "ITEM-106", "warehouse": "Future - M", "actual_qty": 8, "reserved_qty": 0, "projected_qty": 8},
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
        "parent": "PO-SOON",
        "item_code": "ITEM-105",
        "item_name": "Power Bank",
        "schedule_date": "2026-06-05",
        "expected_delivery_date": "2026-06-05",
        "qty": 10,
        "received_qty": 0,
        "warehouse": "Short - M",
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

STOCK_ENTRY_ROWS = [
    {
        "name": "MAT-MOV-0001",
        "purpose": "Material Transfer",
        "stock_entry_type": "Material Transfer",
        "posting_date": "2026-05-27",
        "posting_time": "09:15:00",
        "from_warehouse": "Stores - M",
        "to_warehouse": "Main - M",
        "docstatus": 1,
        "modified": "2026-05-27 09:15:00",
    },
    {
        "name": "MAT-MOV-0002",
        "purpose": "Material Receipt",
        "stock_entry_type": "Material Receipt",
        "posting_date": "2026-05-26",
        "posting_time": "10:20:00",
        "from_warehouse": "",
        "to_warehouse": "Receiving - M",
        "docstatus": 1,
        "modified": "2026-05-26 10:20:00",
    },
    {
        "name": "MAT-MOV-0003",
        "purpose": "Material Issue",
        "stock_entry_type": "Material Issue",
        "posting_date": "2026-05-25",
        "posting_time": "11:30:00",
        "from_warehouse": "Main - M",
        "to_warehouse": "",
        "docstatus": 1,
        "modified": "2026-05-25 11:30:00",
    },
    {
        "name": "MAT-MOV-0004",
        "purpose": "Repack",
        "stock_entry_type": "Repack",
        "posting_date": "2026-05-24",
        "posting_time": "12:40:00",
        "from_warehouse": "Main - M",
        "to_warehouse": "Main - M",
        "docstatus": 1,
        "modified": "2026-05-24 12:40:00",
    },
]

STOCK_ENTRY_DETAIL_ROWS = [
    {"parent": "MAT-MOV-0001", "idx": 1, "item_code": "ITEM-103", "item_name": "Bluetooth Speaker", "qty": 5, "s_warehouse": "Stores - M", "t_warehouse": "Main - M", "stock_uom": "Nos", "uom": "Nos"},
    {"parent": "MAT-MOV-0001", "idx": 2, "item_code": "ITEM-104", "item_name": "Cable Pack", "qty": 2, "s_warehouse": "Stores - M", "t_warehouse": "Main - M", "stock_uom": "Nos", "uom": "Nos"},
    {"parent": "MAT-MOV-0002", "idx": 1, "item_code": "ITEM-105", "item_name": "Power Bank", "qty": 10, "s_warehouse": "", "t_warehouse": "Receiving - M", "stock_uom": "Nos", "uom": "Nos"},
    {"parent": "MAT-MOV-0003", "idx": 1, "item_code": "ITEM-102", "item_name": "Screen Guard", "qty": 3, "s_warehouse": "Main - M", "t_warehouse": "", "stock_uom": "Nos", "uom": "Nos"},
    {"parent": "MAT-MOV-0004", "idx": 1, "item_code": "ITEM-101", "item_name": "Phone Case", "qty": 1, "s_warehouse": "Main - M", "t_warehouse": "Main - M", "stock_uom": "Nos", "uom": "Nos"},
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
        "Sales Order": 5,
        "Pick List": 1,
        "Material Request": 3,
        "Stock Entry": 4,
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
        "Sales Order": {
            "docstatus",
            "status",
            "per_delivered",
            "delivery_date",
            "customer",
            "customer_name",
            "transaction_date",
            "set_warehouse",
            "modified",
        },
        "Sales Order Item": {
            "parent",
            "item_code",
            "item_name",
            "delivery_date",
            "qty",
            "delivered_qty",
            "warehouse",
            "stock_uom",
            "uom",
            "idx",
        },
        "Bin": {"item_code", "warehouse", "actual_qty", "reserved_qty", "projected_qty"},
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
        "Stock Entry": {
            "name",
            "purpose",
            "stock_entry_type",
            "posting_date",
            "posting_time",
            "from_warehouse",
            "to_warehouse",
            "docstatus",
            "modified",
        },
        "Stock Entry Detail": {
            "parent",
            "idx",
            "item_code",
            "item_name",
            "qty",
            "s_warehouse",
            "t_warehouse",
            "stock_uom",
            "uom",
        },
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


def _filter_sales_orders(filters):
    rows = list(SO_ROWS)
    for condition in filters or []:
        if not isinstance(condition, list) or len(condition) < 4:
            continue
        _, field, operator, value = condition[:4]
        if field == "name" and operator == "like":
            needle = str(value).replace("%", "").lower()
            rows = [row for row in rows if needle in row["name"].lower()]
        if field == "name" and operator == "=":
            rows = [row for row in rows if row["name"] == value]
        if field == "customer_name" and operator == "like":
            needle = str(value).replace("%", "").lower()
            rows = [row for row in rows if needle in row["customer_name"].lower()]
        if field == "customer" and operator == "like":
            needle = str(value).replace("%", "").lower()
            rows = [row for row in rows if needle in row["customer"].lower()]
        if field == "status" and operator == "in":
            rows = [row for row in rows if row["status"] in set(value)]
        if field == "per_delivered" and operator == "<":
            rows = [row for row in rows if float(row["per_delivered"]) < float(value)]
        if field == "docstatus" and operator == "=":
            rows = [row for row in rows if int(value) == 1]
    return rows


def _filter_stock_entries(filters):
    rows = list(STOCK_ENTRY_ROWS)
    for condition in filters or []:
        if not isinstance(condition, list) or len(condition) < 4:
            continue
        _, field, operator, value = condition[:4]
        if field == "name" and operator == "like":
            needle = str(value).replace("%", "").lower()
            rows = [row for row in rows if needle in row["name"].lower()]
        if field == "name" and operator == "=":
            rows = [row for row in rows if row["name"] == value]
        if field == "docstatus" and operator == "=":
            rows = [row for row in rows if int(row["docstatus"]) == int(value)]
        if field == "posting_date" and operator == ">=":
            rows = [row for row in rows if row["posting_date"] >= str(value)]
    return rows


def _get_list(doctype, fields=None, filters=None, order_by=None, limit_page_length=None, **kwargs):
    LIST_CALLS.append({"doctype": doctype, "fields": fields, "filters": filters, "limit": limit_page_length})
    if doctype == "Purchase Order":
        rows = _filter_purchase_orders(filters)
        return [_selected(row, fields or ["name"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Sales Order":
        rows = _filter_sales_orders(filters)
        return [_selected(row, fields or ["name"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Stock Entry":
        rows = _filter_stock_entries(filters)
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
    if doctype == "Sales Order Item":
        parent_filter = (filters or {}).get("parent") if isinstance(filters, dict) else None
        if isinstance(parent_filter, list) and parent_filter[0] == "in":
            parents = set(parent_filter[1])
        elif parent_filter:
            parents = {parent_filter}
        else:
            parents = set()
        rows = [row for row in SO_ITEM_ROWS if not parents or row["parent"] in parents]
        return [_selected(row, fields or ["parent"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Bin":
        item_filter = (filters or {}).get("item_code") if isinstance(filters, dict) else None
        warehouse_filter = (filters or {}).get("warehouse") if isinstance(filters, dict) else None
        items = set(item_filter[1]) if isinstance(item_filter, list) and item_filter[0] == "in" else set()
        warehouses = set(warehouse_filter[1]) if isinstance(warehouse_filter, list) and warehouse_filter[0] == "in" else set()
        rows = [
            row for row in BIN_ROWS
            if (not items or row["item_code"] in items) and (not warehouses or row["warehouse"] in warehouses)
        ]
        return [_selected(row, fields or ["item_code"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Stock Entry Detail":
        parent_filter = (filters or {}).get("parent") if isinstance(filters, dict) else None
        if isinstance(parent_filter, list) and parent_filter[0] == "in":
            parents = set(parent_filter[1])
        elif parent_filter:
            parents = {parent_filter}
        else:
            parents = set()
        rows = [row for row in STOCK_ENTRY_DETAIL_ROWS if not parents or row["parent"] in parents]
        return [_selected(row, fields or ["parent"]) for row in rows[: limit_page_length or len(rows)]]
    return []


def _get_doc(doctype, name, *args, **kwargs):
    GET_DOC_CALLS.append({"doctype": doctype, "name": name})
    if doctype not in {"Purchase Order", "Sales Order", "Stock Entry"}:
        raise Exception("Unsupported DocType")
    if not _has_permission(doctype, "read"):
        raise _FakePermissionError("No read permission")
    rows = PO_ROWS if doctype == "Purchase Order" else SO_ROWS if doctype == "Sales Order" else STOCK_ENTRY_ROWS
    child_rows = PO_ITEM_ROWS if doctype == "Purchase Order" else SO_ITEM_ROWS if doctype == "Sales Order" else STOCK_ENTRY_DETAIL_ROWS
    record = next((row for row in rows if row["name"] == name), None)
    if not record:
        raise Exception(f"Missing {doctype}")

    class _FakeOrderDoc:
        def get(self, fieldname, default=None):
            if fieldname == "items":
                return [dict(row) for row in child_rows if row["parent"] == name]
            return record.get(fieldname, default)

        def check_permission(self, ptype=None):
            if not _has_permission(doctype, ptype):
                raise _FakePermissionError("No read permission")
            return True

    return _FakeOrderDoc()


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


class TestWarehouseConsoleW5BContracts(unittest.TestCase):
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
            "Sales Order",
            "Sales Order Item",
            "Stock Entry",
            "Stock Entry Detail",
        })
        COUNT_CALLS.clear()
        LIST_CALLS.clear()
        GET_ALL_CALLS.clear()
        GET_DOC_CALLS.clear()

    def test_warehouse_workspace_registry_definition_has_w8a_movement_visibility_route(self):
        workspace = get_warehouse_workspace_definition()

        self.assertEqual(workspace["workspace_id"], "warehouse")
        self.assertEqual(workspace["status"], "w8a_movement_visibility")
        self.assertEqual(
            workspace["routes"],
            {
                "home": "warehouse-console",
                "home_path": "/desk/warehouse-console",
                "worklist": "warehouse-console-worklist",
                "worklist_path": "/desk/warehouse-console-worklist",
                "receiving": "warehouse-console-receiving",
                "receiving_path": "/desk/warehouse-console-receiving",
                "picking": "warehouse-console-picking",
                "picking_path": "/desk/warehouse-console-picking",
                "stock_exception": "warehouse-console-stock-exception",
                "stock_exception_path": "/desk/warehouse-console-stock-exception",
                "stock_posture": "warehouse-console-stock-posture",
                "stock_posture_path": "/desk/warehouse-console-stock-posture",
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
            workspace["methods"]["outbound_queue"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_outbound_picking_queue",
        )
        self.assertEqual(
            workspace["methods"]["receiving_detail"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_receiving_review",
        )
        self.assertEqual(
            workspace["methods"]["picking_detail"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_picking_review",
        )
        self.assertEqual(
            workspace["methods"]["stock_exceptions"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_exceptions",
        )
        self.assertEqual(
            workspace["methods"]["stock_exception_review"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_exception_review",
        )
        self.assertEqual(
            workspace["methods"]["stock_posture_review"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_posture_review",
        )
        self.assertEqual(
            workspace["methods"]["movement_visibility"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_movement_visibility_queue",
        )
        self.assertFalse(workspace["search"]["enabled"])
        self.assertEqual([item["key"] for item in workspace["fallback_items"]], [
            "warehouse_console_home",
            "inbound_receiving",
            "outbound_picking",
            "stock_exceptions",
            "movement_visibility",
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
        self.assertIn("outbound", payload)
        self.assertEqual(payload["outbound"]["queue_key"], "outbound_picking")
        self.assertEqual(payload["outbound"]["counts"]["overdue"], 1)
        self.assertEqual(payload["outbound"]["counts"]["due_today"], 1)
        self.assertEqual(payload["outbound"]["counts"]["ready_to_pick"], 1)
        self.assertEqual(payload["outbound"]["counts"]["partially_picked"], 1)
        self.assertEqual(payload["outbound"]["counts"]["needs_stock_review"], 1)
        self.assertLessEqual(len(payload["outbound"]["preview_rows"]), 6)
        self.assertIn("Outbound Work", {section["title"] for section in payload["sections"]})
        self.assertIn("stock_exceptions", payload)
        self.assertEqual(payload["stock_exceptions"]["queue_key"], "stock_exceptions")
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


    def test_outbound_queue_payload_is_grouped_read_only_and_allowlisted(self):
        payload = service.get_warehouse_outbound_picking_queue("outbound-picking")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"], {"title": "Outbound Picking", "key": "outbound_picking"})
        self.assertEqual(payload["action_targets"], {})
        self.assertEqual(payload["valuation"], {"visible": False, "fields": []})
        self.assertEqual(len(payload["rows"]), 5)
        groups = {group["key"]: group for group in payload["groups"]}
        self.assertEqual(len(groups["overdue"]["rows"]), 1)
        self.assertEqual(len(groups["due_today"]["rows"]), 1)
        self.assertEqual(len(groups["ready_to_pick"]["rows"]), 1)
        self.assertEqual(len(groups["partially_picked"]["rows"]), 1)
        self.assertEqual(len(groups["needs_stock_review"]["rows"]), 1)

        allowed_row_keys = {
            "key",
            "name",
            "sales_order",
            "primary_id",
            "customer",
            "partner",
            "required_date",
            "target_warehouse",
            "line_count",
            "item_count",
            "delivered_percent",
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
        payload_text = str(payload).lower()
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("base_net_rate", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertTrue(any(call["doctype"] == "Sales Order" for call in LIST_CALLS))
        self.assertTrue(any(call["doctype"] == "Sales Order Item" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Bin" for call in GET_ALL_CALLS))

    def test_outbound_queue_filters_stay_within_product_route_scope(self):
        payload = service.get_warehouse_outbound_picking_queue(
            "outbound-picking",
            {"state": "needs_stock_review", "customer": "Review"},
        )

        self.assertEqual([row["sales_order"] for row in payload["rows"]], ["SO-REVIEW"])
        self.assertEqual(payload["controls"]["fields"][1]["value"], "Review")
        self.assertEqual(payload["controls"]["fields"][3]["value"], "needs_stock_review")
        self.assertEqual(payload["workspace"]["routes"]["worklist"], "warehouse-console-worklist")
        self.assertNotIn("native", str(payload).lower())


    def test_stock_exceptions_payload_is_grouped_read_only_and_allowlisted(self):
        payload = service.get_warehouse_stock_exceptions("stock-exceptions")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"], {"title": "Stock Exceptions", "key": "stock_exceptions"})
        self.assertNotIn("valuation", payload)
        self.assertEqual(payload["action_targets"]["picking"]["route"], "warehouse-console-picking")
        self.assertEqual(payload["action_targets"]["receiving"]["route"], "warehouse-console-receiving")
        self.assertGreaterEqual(len(payload["rows"]), 1)
        groups = {group["key"]: group for group in payload["groups"]}
        self.assertIn("inbound_cover_expected", groups)
        self.assertGreaterEqual(len(groups["inbound_cover_expected"]["rows"]), 1)

        allowed_row_keys = {
            "key",
            "context_token",
            "sales_order",
            "customer",
            "item_code",
            "item_name",
            "required_date",
            "pending_qty",
            "delivered_qty",
            "uom",
            "source_warehouse",
            "available_qty",
            "projected_qty",
            "short_qty",
            "expected_inbound_qty",
            "expected_inbound_date",
            "expected_inbound_order",
            "exception_key",
            "exception_label",
            "urgency_label",
            "explanation",
            "route_targets",
        }
        for row in payload["rows"]:
            self.assertLessEqual(set(row), allowed_row_keys)
            self.assertTrue(row["context_token"])
            self.assertEqual(row["route_targets"]["exception_review"]["route"], "warehouse-console-stock-exception")
            self.assertEqual(row["route_targets"]["picking"]["route"], "warehouse-console-picking")
            if row.get("expected_inbound_order"):
                self.assertEqual(row["route_targets"]["receiving"]["route"], "warehouse-console-receiving")
        payload_text = str(payload).lower()
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("base_net_rate", payload_text)
        self.assertNotIn("amount", payload_text)
        self.assertNotIn("gl", payload_text)
        self.assertNotIn("item price", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertTrue(any(call["doctype"] == "Sales Order" for call in LIST_CALLS))
        self.assertTrue(any(call["doctype"] == "Sales Order Item" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Bin" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Purchase Order" for call in LIST_CALLS))
        self.assertTrue(any(call["doctype"] == "Purchase Order Item" for call in GET_ALL_CALLS))

    def test_stock_exceptions_filters_stay_inside_warehouse_routes(self):
        payload = service.get_warehouse_stock_exceptions(
            "stock-exceptions",
            {"state": "inbound_cover_expected", "text": "Power", "warehouse": "Short"},
        )

        self.assertEqual([row["sales_order"] for row in payload["rows"]], ["SO-REVIEW"])
        self.assertEqual(payload["controls"]["fields"][0]["value"], "inbound_cover_expected")
        self.assertEqual(payload["controls"]["fields"][1]["value"], "Short")
        self.assertEqual(payload["controls"]["fields"][2]["value"], "Power")
        self.assertEqual(payload["workspace"]["routes"]["worklist"], "warehouse-console-worklist")
        self.assertNotIn("native", str(payload).lower())


    def test_movement_visibility_payload_is_grouped_read_only_and_allowlisted(self):
        payload = service.get_warehouse_movement_visibility_queue("movement-visibility")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"], {"title": "Movement Visibility", "key": "movement_visibility"})
        self.assertEqual(payload["action_targets"]["stock_posture"]["route"], "warehouse-console-stock-posture")
        self.assertGreaterEqual(len(payload["rows"]), 4)
        groups = {group["key"]: group for group in payload["groups"]}
        self.assertEqual(len(groups["internal_transfers"]["rows"]), 1)
        self.assertEqual(len(groups["receipts"]["rows"]), 1)
        self.assertEqual(len(groups["issues"]["rows"]), 1)
        self.assertEqual(len(groups["adjustments_repack"]["rows"]), 1)

        allowed_row_keys = {
            "key",
            "movement_id",
            "movement_type",
            "purpose",
            "posting_date",
            "posting_time",
            "source_warehouse",
            "target_warehouse",
            "direction_label",
            "item_count",
            "quantity_summary",
            "sample_items",
            "group_key",
            "group_label",
            "route_targets",
        }
        allowed_item_keys = {
            "item_code",
            "item_name",
            "qty",
            "uom",
            "source_warehouse",
            "target_warehouse",
            "route_target",
        }
        for row in payload["rows"]:
            self.assertLessEqual(set(row), allowed_row_keys)
            self.assertEqual(row["route_targets"]["stock_posture"]["route"], "warehouse-console-stock-posture")
            for item in row["sample_items"]:
                self.assertLessEqual(set(item), allowed_item_keys)
        payload_text = str(payload).lower()
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("incoming_rate", payload_text)
        self.assertNotIn("outgoing_rate", payload_text)
        self.assertNotIn("base_amount", payload_text)
        self.assertNotIn("transfer_price", payload_text)
        self.assertNotIn("stock_queue", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertTrue(any(call["doctype"] == "Stock Entry" for call in LIST_CALLS))
        self.assertTrue(any(call["doctype"] == "Stock Entry Detail" for call in GET_ALL_CALLS))

    def test_movement_visibility_filters_and_fallback_stay_inside_custom_routes(self):
        READABLE_DOCTYPES.discard("Stock Entry Detail")

        payload = service.get_warehouse_movement_visibility_queue(
            "movement-visibility",
            {"state": "receipts", "warehouse": "Receiving", "movement": "0002"},
        )

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual([row["movement_id"] for row in payload["rows"]], ["MAT-MOV-0002"])
        self.assertEqual(payload["controls"]["fields"][0]["value"], "receipts")
        self.assertEqual(payload["controls"]["fields"][1]["value"], "Receiving")
        self.assertEqual(payload["controls"]["fields"][2]["value"], "0002")
        self.assertEqual(payload["workspace"]["routes"]["worklist"], "warehouse-console-worklist")
        self.assertFalse(any(call["doctype"] == "Stock Entry Detail" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Stock Entry" for call in GET_DOC_CALLS))
        self.assertNotIn("native", str(payload).lower())


    def test_stock_exception_review_payload_is_read_only_and_custom_routed(self):
        token = service._stock_exception_context_token("SO-REVIEW", "ITEM-105", "Short - M")

        payload = service.get_warehouse_stock_exception_review(token)

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"]["key"], "stock_exception_review")
        self.assertEqual(payload["page"]["context_token"], token)
        self.assertEqual(payload["header"]["sales_order"], "SO-REVIEW")
        self.assertEqual(payload["header"]["item_code"], "ITEM-105")
        self.assertEqual(payload["header"]["source_warehouse"], "Short - M")
        self.assertEqual({card["key"] for card in payload["summary_cards"]}, {"state", "pending_qty", "available_qty", "inbound_cover"})
        self.assertEqual(set(payload["panels"]), {"demand", "stock", "inbound", "next_reviews"})
        self.assertEqual(payload["action_targets"]["stock_exceptions"]["route"], "warehouse-console-worklist")
        self.assertEqual(payload["action_targets"]["picking"]["route"], "warehouse-console-picking")
        self.assertEqual(payload["action_targets"]["stock_posture"]["route"], "warehouse-console-stock-posture")
        self.assertEqual(payload["action_targets"]["receiving"]["route"], "warehouse-console-receiving")
        self.assertEqual(payload["panels"]["stock"]["route_target"]["route"], "warehouse-console-stock-posture")
        self.assertTrue(any(row["route_target"]["route"] == "warehouse-console-picking" for row in payload["related_rows"]))
        self.assertTrue(any(row["route_target"]["route"] == "warehouse-console-receiving" for row in payload["related_rows"]))

        payload_text = str(payload).lower()
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("base_net_rate", payload_text)
        self.assertNotIn("amount", payload_text)
        self.assertNotIn("gl", payload_text)
        self.assertNotIn("item price", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertTrue(any(call["doctype"] == "Sales Order" for call in LIST_CALLS))
        self.assertTrue(any(call["doctype"] == "Sales Order Item" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Bin" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Purchase Order" for call in LIST_CALLS))

    def test_stock_exception_review_uses_parent_sales_order_when_child_table_read_is_unavailable(self):
        READABLE_DOCTYPES.discard("Sales Order Item")
        token = service._stock_exception_context_token("SO-REVIEW", "ITEM-105", "Short - M")

        payload = service.get_warehouse_stock_exception_review(token)

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["header"]["item_code"], "ITEM-105")
        self.assertFalse(any(call["doctype"] == "Sales Order Item" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Sales Order" for call in GET_DOC_CALLS))
        self.assertNotIn("valuation_rate", str(payload).lower())

    def test_stock_exception_review_invalid_context_returns_controlled_state(self):
        payload = service.get_warehouse_stock_exception_review("not-a-review")

        self.assertEqual(payload["state"]["kind"], "unavailable")
        self.assertEqual(payload["related_rows"], [])


    def test_stock_posture_review_payload_is_read_only_and_custom_routed(self):
        stock_exception_token = service._stock_exception_context_token("SO-REVIEW", "ITEM-105", "Short - M")
        token = service._stock_posture_context_token(
            "ITEM-105",
            "Short - M",
            sales_order="SO-REVIEW",
            purchase_order="PO-SOON",
            stock_exception_token=stock_exception_token,
        )

        payload = service.get_warehouse_stock_posture_review(token)

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"]["key"], "stock_posture_review")
        self.assertEqual(payload["page"]["context_token"], token)
        self.assertEqual(payload["header"]["item_code"], "ITEM-105")
        self.assertEqual(payload["header"]["warehouse"], "Short - M")
        self.assertEqual(payload["quantity_posture"]["actual_qty"], "2")
        self.assertEqual(payload["quantity_posture"]["available_qty"], "2")
        self.assertEqual(set(payload["panels"]), {"stock", "inbound", "outbound", "related"})
        self.assertEqual({card["key"] for card in payload["summary_cards"]}, {"posture", "available", "projected", "open_demand", "inbound_cover"})
        self.assertEqual(payload["action_targets"]["picking"]["route"], "warehouse-console-picking")
        self.assertEqual(payload["action_targets"]["receiving"]["route"], "warehouse-console-receiving")
        self.assertEqual(payload["action_targets"]["stock_exception"]["route"], "warehouse-console-stock-exception")
        self.assertTrue(any(row["route_target"]["route"] == "warehouse-console-picking" for row in payload["related_rows"]))
        self.assertTrue(any(row["route_target"]["route"] == "warehouse-console-receiving" for row in payload["related_rows"]))
        self.assertTrue(any(row["route_target"]["route"] == "warehouse-console-stock-exception" for row in payload["related_rows"]))
        self.assertGreaterEqual(len(payload["outbound_rows"]), 1)
        self.assertGreaterEqual(len(payload["inbound_rows"]), 1)

        payload_text = str(payload).lower()
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("base_net_rate", payload_text)
        self.assertNotIn("amount", payload_text)
        self.assertNotIn("gl", payload_text)
        self.assertNotIn("item price", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertTrue(any(call["doctype"] == "Bin" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Sales Order" for call in LIST_CALLS))
        self.assertTrue(any(call["doctype"] == "Purchase Order" for call in LIST_CALLS))

    def test_stock_posture_review_uses_parent_documents_when_child_table_reads_are_unavailable(self):
        READABLE_DOCTYPES.discard("Sales Order Item")
        READABLE_DOCTYPES.discard("Purchase Order Item")
        token = service._stock_posture_context_token("ITEM-105", "Short - M", sales_order="SO-REVIEW", purchase_order="PO-SOON")

        payload = service.get_warehouse_stock_posture_review(token)

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["header"]["item_code"], "ITEM-105")
        self.assertFalse(any(call["doctype"] == "Sales Order Item" for call in GET_ALL_CALLS))
        self.assertFalse(any(call["doctype"] == "Purchase Order Item" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Sales Order" for call in GET_DOC_CALLS))
        self.assertTrue(any(call["doctype"] == "Purchase Order" for call in GET_DOC_CALLS))
        self.assertNotIn("valuation_rate", str(payload).lower())

    def test_stock_posture_review_invalid_context_returns_controlled_state(self):
        payload = service.get_warehouse_stock_posture_review("not-a-posture")

        self.assertEqual(payload["state"]["kind"], "unavailable")
        self.assertEqual(payload["related_rows"], [])


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

    def test_picking_review_payload_is_read_only_allowlisted_and_readiness_visible(self):
        payload = service.get_warehouse_picking_review("SO-REVIEW")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"]["sales_order"], "SO-REVIEW")
        self.assertNotIn("valuation", payload)
        self.assertEqual(payload["action_targets"]["outbound_queue"]["route"], "warehouse-console-worklist")
        self.assertEqual(payload["header"]["customer"], "Review Customer")
        self.assertEqual(payload["header"]["delivered_percent"], "0%")
        self.assertGreaterEqual(len(payload["lines"]), 1)
        self.assertLessEqual(len(payload["lines"]), service.PICKING_DETAIL_LINE_LIMIT)
        self.assertGreaterEqual(payload["header"]["review_line_count"], 1)

        allowed_line_keys = {
            "item_code",
            "item_name",
            "ordered_qty",
            "delivered_qty",
            "pending_qty",
            "uom",
            "source_warehouse",
            "required_date",
            "readiness",
            "availability",
        }
        for line in payload["lines"]:
            self.assertLessEqual(set(line), allowed_line_keys)
        payload_text = str(payload).lower()
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("base_net_rate", payload_text)
        self.assertNotIn("amount", payload_text)
        self.assertNotIn("gl", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertTrue(any(call["doctype"] == "Sales Order" for call in LIST_CALLS))
        self.assertTrue(any(call["doctype"] == "Sales Order Item" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Bin" for call in GET_ALL_CALLS))

    def test_picking_review_uses_parent_sales_order_when_child_table_read_is_unavailable(self):
        READABLE_DOCTYPES.discard("Sales Order Item")

        payload = service.get_warehouse_picking_review("SO-READY")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertGreaterEqual(len(payload["lines"]), 1)
        self.assertEqual(payload["lines"][0]["item_code"], "ITEM-103")
        self.assertFalse(any(call["doctype"] == "Sales Order Item" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Sales Order" for call in GET_DOC_CALLS))
        self.assertNotIn("valuation_rate", str(payload).lower())

        CURRENT_ROLES[:] = ["Purchase Manager"]

        overview = service.get_warehouse_console_overview()
        queue = service.get_warehouse_inbound_receiving_queue("inbound_receiving")
        outbound = service.get_warehouse_outbound_picking_queue("outbound_picking")
        detail = service.get_warehouse_receiving_review("PO-OVERDUE")
        picking_detail = service.get_warehouse_picking_review("SO-OVERDUE")
        stock_exceptions = service.get_warehouse_stock_exceptions("stock_exceptions")
        stock_exception_detail = service.get_warehouse_stock_exception_review(
            service._stock_exception_context_token("SO-REVIEW", "ITEM-105", "Short - M")
        )
        stock_posture_detail = service.get_warehouse_stock_posture_review(
            service._stock_posture_context_token("ITEM-105", "Short - M")
        )
        movement = service.get_warehouse_movement_visibility_queue("movement_visibility")

        self.assertEqual(overview["state"]["kind"], "restricted")
        self.assertFalse(overview["context"]["has_warehouse_access"])
        self.assertEqual(overview["sidebar"]["sections"], [])
        self.assertEqual(overview["allowed_actions"], [])
        self.assertEqual(queue["state"]["kind"], "restricted")
        self.assertEqual(queue["rows"], [])
        self.assertEqual(outbound["state"]["kind"], "restricted")
        self.assertEqual(outbound["rows"], [])
        self.assertEqual(detail["state"]["kind"], "restricted")
        self.assertEqual(detail["lines"], [])
        self.assertEqual(picking_detail["state"]["kind"], "restricted")
        self.assertEqual(picking_detail["lines"], [])
        self.assertEqual(stock_exceptions["state"]["kind"], "restricted")
        self.assertEqual(stock_exceptions["rows"], [])
        self.assertEqual(stock_exception_detail["state"]["kind"], "restricted")
        self.assertEqual(stock_exception_detail["related_rows"], [])
        self.assertEqual(stock_posture_detail["state"]["kind"], "restricted")
        self.assertEqual(stock_posture_detail["related_rows"], [])
        self.assertEqual(movement["state"]["kind"], "restricted")
        self.assertEqual(movement["rows"], [])

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

    def test_permission_limited_sources_return_controlled_empty_outbound_state(self):
        READABLE_DOCTYPES.discard("Sales Order")

        overview = service.get_warehouse_console_overview()
        queue = service.get_warehouse_outbound_picking_queue("outbound_picking")
        metrics = {metric["key"]: metric for metric in overview["kpis"]}

        self.assertEqual(metrics["outbound_due"]["state"], "unavailable")
        self.assertIsNone(metrics["outbound_due"]["value"])
        self.assertEqual(queue["state"]["kind"], "restricted")
        self.assertEqual(queue["rows"], [])
        self.assertFalse(any(call["doctype"] == "Sales Order" for call in LIST_CALLS))

    def test_permission_limited_sources_return_controlled_empty_movement_state(self):
        READABLE_DOCTYPES.discard("Stock Entry")

        movement = service.get_warehouse_movement_visibility_queue("movement_visibility")

        self.assertEqual(movement["state"]["kind"], "restricted")
        self.assertEqual(movement["rows"], [])
        self.assertFalse(any(call["doctype"] == "Stock Entry" for call in LIST_CALLS))


if __name__ == "__main__":
    unittest.main()
