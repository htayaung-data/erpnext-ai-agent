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
RECEIVING_TASK_DOCS = {}
PICKING_TASK_DOCS = {}
DISPATCH_HANDOFF_REQUEST_DOCS = {}
CUSTOMER_RETURN_INTAKE_DOCS = {}

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
        "Warehouse Receiving Task": {
            "purchase_order",
            "supplier",
            "target_warehouse",
            "status",
            "assigned_user",
            "manager",
            "started_at",
            "submitted_at",
            "reviewed_at",
            "decision",
            "notes",
            "evidence_reference",
            "source_route",
            "policy_version",
            "last_request_id",
            "line_count",
            "total_expected_qty",
            "lines",
            "events",
        },
        "Warehouse Receiving Task Line": {
            "purchase_order_item",
            "item_code",
            "item_name",
            "uom",
            "expected_qty",
            "counted_qty",
            "accepted_qty",
            "damaged_qty",
            "short_qty",
            "over_qty",
            "quarantine_qty",
            "discrepancy_reason",
            "note",
            "evidence_reference",
            "target_warehouse",
            "line_status",
        },
        "Warehouse Receiving Task Event": {
            "event_type",
            "actor",
            "event_at",
            "previous_status",
            "next_status",
            "note",
            "server_request_id",
        },
        "Warehouse Picking Task": {
            "sales_order",
            "customer",
            "source_warehouse",
            "task_status",
            "workflow_state",
            "source_payload_hash",
            "request_id",
            "created_by_user",
            "last_action_by",
            "last_action_at",
            "notes",
            "source_route",
            "policy_version",
            "line_count",
            "total_open_qty",
            "lines",
            "events",
        },
        "Warehouse Picking Task Line": {
            "sales_order_item",
            "item_code",
            "item_name",
            "warehouse",
            "ordered_qty",
            "delivered_qty",
            "open_qty",
            "picked_qty",
            "packed_qty",
            "short_qty",
            "damaged_qty",
            "not_found_qty",
            "exception_type",
            "exception_note",
            "evidence_reference",
            "line_status",
            "uom",
        },
        "Warehouse Picking Task Event": {
            "event_type",
            "event_label",
            "event_by",
            "event_at",
            "request_id",
            "details_json",
        },
        "Warehouse Dispatch Handoff Request": {
            "picking_task",
            "sales_order",
            "customer",
            "warehouse",
            "request_status",
            "dispatch_handoff_reference",
            "pack_reference",
            "package_count",
            "handoff_note",
            "sales_approval_reference",
            "source_payload_hash",
            "policy_version",
            "line_count",
            "total_dispatch_qty",
            "request_id",
            "requested_by",
            "requested_at",
            "lines",
            "events",
        },
        "Warehouse Dispatch Handoff Request Line": {
            "picking_task_line",
            "sales_order_item",
            "item_code",
            "item_name",
            "warehouse",
            "open_qty",
            "picked_qty",
            "packed_qty",
            "accepted_for_dispatch_qty",
            "short_qty",
            "damaged_qty",
            "not_found_qty",
            "line_status",
            "exception_note",
            "evidence_reference",
            "uom",
        },
        "Warehouse Dispatch Handoff Request Event": {
            "event_type",
            "event_label",
            "event_by",
            "event_at",
            "request_id",
            "details_json",
        },
        "Warehouse Customer Return Intake": {
            "customer",
            "warehouse",
            "intake_status",
            "return_authorization_reference",
            "sales_order_reference_text",
            "delivery_note_reference_text",
            "sales_invoice_reference_text",
            "source_reference_note",
            "received_by",
            "received_at",
            "inspection_status",
            "manager_review_status",
            "sales_escalation_reference",
            "notes",
            "source_payload_hash",
            "policy_version",
            "line_count",
            "total_returned_qty",
            "request_id",
            "lines",
            "events",
        },
        "Warehouse Customer Return Intake Line": {
            "item_code",
            "item_name",
            "warehouse",
            "returned_qty",
            "accepted_qty",
            "damaged_qty",
            "quarantine_qty",
            "repair_qty",
            "scrap_candidate_qty",
            "rejected_qty",
            "condition_grade",
            "disposition",
            "evidence_reference",
            "condition_note",
            "uom",
        },
        "Warehouse Customer Return Intake Event": {
            "event_type",
            "event_label",
            "event_by",
            "event_at",
            "request_id",
            "details_json",
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
    if doctype == "Warehouse":
        warehouses = {
            row.get("set_warehouse") for row in PO_ROWS + SO_ROWS if row.get("set_warehouse")
        } | {
            row.get("warehouse") for row in PO_ITEM_ROWS + SO_ITEM_ROWS + BIN_ROWS if row.get("warehouse")
        } | {
            row.get("from_warehouse") for row in STOCK_ENTRY_ROWS if row.get("from_warehouse")
        } | {
            row.get("to_warehouse") for row in STOCK_ENTRY_ROWS if row.get("to_warehouse")
        }
        rows = [{"name": name} for name in sorted(warehouses) if name]
        if isinstance(filters, dict) and filters.get("name"):
            rows = [row for row in rows if row["name"] == filters.get("name")]
        return [_selected(row, fields or ["name"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Warehouse Receiving Task":
        rows = list(RECEIVING_TASK_DOCS.values())
        if isinstance(filters, dict):
            for key, value in filters.items():
                if isinstance(value, list) and value[0] == "in":
                    allowed = set(value[1])
                    rows = [row for row in rows if getattr(row, key, None) in allowed]
                else:
                    rows = [row for row in rows if getattr(row, key, None) == value]
        return [_selected(row.__dict__, fields or ["name"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Warehouse Picking Task":
        rows = list(PICKING_TASK_DOCS.values())
        if isinstance(filters, dict):
            for key, value in filters.items():
                if isinstance(value, list) and value[0] == "in":
                    allowed = set(value[1])
                    rows = [row for row in rows if getattr(row, key, None) in allowed]
                else:
                    rows = [row for row in rows if getattr(row, key, None) == value]
        return [_selected(row.__dict__, fields or ["name"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Warehouse Picking Task Event":
        rows = []
        for task in PICKING_TASK_DOCS.values():
            for event in list(getattr(task, "events", []) or []):
                row = dict(event)
                row["parent"] = task.name
                rows.append(row)
        if isinstance(filters, dict):
            for key, value in filters.items():
                rows = [row for row in rows if row.get(key) == value]
        return [_selected(row, fields or ["parent"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Warehouse Dispatch Handoff Request":
        rows = list(DISPATCH_HANDOFF_REQUEST_DOCS.values())
        if isinstance(filters, dict):
            for key, value in filters.items():
                if isinstance(value, list) and value[0] == "in":
                    allowed = set(value[1])
                    rows = [row for row in rows if getattr(row, key, None) in allowed]
                else:
                    rows = [row for row in rows if getattr(row, key, None) == value]
        return [_selected(row.__dict__, fields or ["name"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Warehouse Dispatch Handoff Request Event":
        rows = []
        for request in DISPATCH_HANDOFF_REQUEST_DOCS.values():
            for event in list(getattr(request, "events", []) or []):
                row = dict(event)
                row["parent"] = request.name
                rows.append(row)
        if isinstance(filters, dict):
            for key, value in filters.items():
                rows = [row for row in rows if row.get(key) == value]
        return [_selected(row, fields or ["parent"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Warehouse Customer Return Intake":
        rows = list(CUSTOMER_RETURN_INTAKE_DOCS.values())
        if isinstance(filters, dict):
            for key, value in filters.items():
                if isinstance(value, list) and value[0] == "in":
                    allowed = set(value[1])
                    rows = [row for row in rows if getattr(row, key, None) in allowed]
                else:
                    rows = [row for row in rows if getattr(row, key, None) == value]
        return [_selected(row.__dict__, fields or ["name"]) for row in rows[: limit_page_length or len(rows)]]
    if doctype == "Warehouse Customer Return Intake Event":
        rows = []
        for intake in CUSTOMER_RETURN_INTAKE_DOCS.values():
            for event in list(getattr(intake, "events", []) or []):
                row = dict(event)
                row["parent"] = intake.name
                rows.append(row)
        if isinstance(filters, dict):
            for key, value in filters.items():
                rows = [row for row in rows if row.get(key) == value]
        return [_selected(row, fields or ["parent"]) for row in rows[: limit_page_length or len(rows)]]
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


class _FakeWorkflowDoc:
    def __init__(self, values=None):
        values = dict(values or {})
        self.doctype = values.pop("doctype", "Warehouse Receiving Task")
        self.name = values.pop("name", "")
        self.lines = list(values.pop("lines", []) or [])
        self.events = list(values.pop("events", []) or [])
        for key, value in values.items():
            setattr(self, key, value)

    def get(self, fieldname, default=None):
        return getattr(self, fieldname, default)

    def set(self, fieldname, value):
        setattr(self, fieldname, value)

    def append(self, fieldname, value):
        rows = list(getattr(self, fieldname, []) or [])
        rows.append(dict(value))
        setattr(self, fieldname, rows)
        return rows[-1]

    def insert(self):
        if self.doctype == "Warehouse Customer Return Intake":
            if not self.name:
                self.name = f"WCRI-{len(CUSTOMER_RETURN_INTAKE_DOCS) + 1:05d}"
            CUSTOMER_RETURN_INTAKE_DOCS[self.name] = self
            return self
        if self.doctype == "Warehouse Dispatch Handoff Request":
            if not self.name:
                self.name = f"WDHR-{len(DISPATCH_HANDOFF_REQUEST_DOCS) + 1:05d}"
            DISPATCH_HANDOFF_REQUEST_DOCS[self.name] = self
            return self
        if self.doctype == "Warehouse Picking Task":
            if not self.name:
                self.name = f"WPT-{len(PICKING_TASK_DOCS) + 1:05d}"
            PICKING_TASK_DOCS[self.name] = self
            return self
        if not self.name:
            self.name = f"WRT-{len(RECEIVING_TASK_DOCS) + 1:05d}"
        RECEIVING_TASK_DOCS[self.name] = self
        return self

    def save(self):
        if self.doctype == "Warehouse Customer Return Intake":
            if not self.name:
                self.name = f"WCRI-{len(CUSTOMER_RETURN_INTAKE_DOCS) + 1:05d}"
            CUSTOMER_RETURN_INTAKE_DOCS[self.name] = self
            return self
        if self.doctype == "Warehouse Dispatch Handoff Request":
            if not self.name:
                self.name = f"WDHR-{len(DISPATCH_HANDOFF_REQUEST_DOCS) + 1:05d}"
            DISPATCH_HANDOFF_REQUEST_DOCS[self.name] = self
            return self
        if self.doctype == "Warehouse Picking Task":
            if not self.name:
                self.name = f"WPT-{len(PICKING_TASK_DOCS) + 1:05d}"
            PICKING_TASK_DOCS[self.name] = self
            return self
        if not self.name:
            self.name = f"WRT-{len(RECEIVING_TASK_DOCS) + 1:05d}"
        RECEIVING_TASK_DOCS[self.name] = self
        return self

    def check_permission(self, ptype=None):
        return True


def _get_doc(doctype, name=None, *args, **kwargs):
    if isinstance(doctype, dict):
        if doctype.get("doctype") in {"Warehouse Receiving Task", "Warehouse Picking Task", "Warehouse Dispatch Handoff Request", "Warehouse Customer Return Intake"}:
            return _FakeWorkflowDoc(doctype)
        raise Exception("Unsupported DocType")
    GET_DOC_CALLS.append({"doctype": doctype, "name": name})
    if doctype == "Warehouse Receiving Task":
        if name not in RECEIVING_TASK_DOCS:
            raise Exception("Missing Warehouse Receiving Task")
        return RECEIVING_TASK_DOCS[name]
    if doctype == "Warehouse Picking Task":
        if name not in PICKING_TASK_DOCS:
            raise Exception("Missing Warehouse Picking Task")
        return PICKING_TASK_DOCS[name]
    if doctype == "Warehouse Dispatch Handoff Request":
        if name not in DISPATCH_HANDOFF_REQUEST_DOCS:
            raise Exception("Missing Warehouse Dispatch Handoff Request")
        return DISPATCH_HANDOFF_REQUEST_DOCS[name]
    if doctype == "Warehouse Customer Return Intake":
        if name not in CUSTOMER_RETURN_INTAKE_DOCS:
            raise Exception("Missing Warehouse Customer Return Intake")
        return CUSTOMER_RETURN_INTAKE_DOCS[name]
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
        RECEIVING_TASK_DOCS.clear()
        PICKING_TASK_DOCS.clear()
        DISPATCH_HANDOFF_REQUEST_DOCS.clear()
        CUSTOMER_RETURN_INTAKE_DOCS.clear()

    def test_warehouse_workspace_registry_definition_has_w8c_transfer_visibility_route(self):
        workspace = get_warehouse_workspace_definition()

        self.assertEqual(workspace["workspace_id"], "warehouse")
        self.assertEqual(workspace["status"], "w8c_transfer_visibility")
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
                "movement": "warehouse-console-movement",
                "movement_path": "/desk/warehouse-console-movement",
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
        self.assertEqual(
            workspace["methods"]["movement_review"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_movement_review",
        )
        self.assertEqual(
            workspace["methods"]["transfer_visibility"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_transfer_visibility_queue",
        )
        self.assertEqual(
            workspace["methods"]["quick_find"],
            "erp_workspace_ui.warehouse_console.service.get_warehouse_quick_find_suggestions",
        )
        self.assertTrue(workspace["search"]["enabled"])
        self.assertEqual(workspace["search"]["mode"], "warehouse_sidebar_search")
        self.assertEqual(workspace["search"]["placement"], "sidebar_utility")
        self.assertEqual(workspace["methods"]["workspace_search"], "erp_workspace_ui.warehouse_console.service.search_warehouse_console_workspace")
        self.assertEqual([item["key"] for item in workspace["fallback_items"]], [
            "warehouse_console_home",
            "inbound_receiving",
            "outbound_picking",
            "stock_exceptions",
            "movement_visibility",
            "transfer_visibility",
        ])

    def test_overview_payload_adds_inbound_preview_and_hides_valuation(self):
        payload = service.get_warehouse_console_overview()

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertTrue(payload["context"]["has_warehouse_access"])
        self.assertEqual(payload["valuation"], {"visible": False, "fields": []})
        self.assertEqual(payload["action_targets"], {})
        self.assertEqual(payload["allowed_actions"], [{"key": "refresh", "label": "Refresh", "kind": "read_only"}])
        self.assertNotIn("manager_center", payload)
        self.assertIn("action_center", payload)
        self.assertEqual(payload["action_center"]["mode"], "shell_only")
        self.assertEqual(payload["action_center"]["state"], "planning")
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

    def test_w15b_action_center_is_shell_only_and_custom_route_only(self):
        CURRENT_ROLES[:] = ["Warehouse Manager"]

        payload = service.get_warehouse_console_overview()

        self.assertNotIn("manager_center", payload)
        action_center = payload["action_center"]
        self.assertEqual(action_center["key"], "w15b_action_center")
        self.assertEqual(action_center["mode"], "shell_only")
        self.assertEqual(action_center["role_mode"], "manager")
        self.assertGreaterEqual(len(action_center["sections"]), 2)
        allowed_route_parts = {
            "inbound-receiving",
            "outbound-picking",
            "stock-exceptions",
            "movement-visibility",
            "transfer-visibility",
        }
        routed_cards = []
        planned_cards = []
        expected_button_labels = {
            "arrival_checks": "Open inbound",
            "picking_work": "Open picking",
            "arrival_review": "Review arrivals",
            "picking_blockers": "Review blockers",
            "exception_resolution": "Review exceptions",
            "movement_visibility": "Review transfers",
        }
        for section in action_center["sections"]:
            self.assertIn("cards", section)
            for card in section["cards"]:
                if card.get("route"):
                    routed_cards.append(card)
                    self.assertEqual(card["route"], "warehouse-console-worklist")
                    self.assertIn(card["route_part"], allowed_route_parts)
                    self.assertEqual(card["button_label"], expected_button_labels[card["key"]])
                else:
                    planned_cards.append(card)
                    self.assertEqual(card["state"], "planned")
                    self.assertNotIn("button_label", card)
        self.assertGreaterEqual(len(routed_cards), 4)
        self.assertGreaterEqual(len(planned_cards), 3)
        payload_text = str(action_center).lower()
        self.assertNotIn("manager readiness", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertNotIn("/desk/form", payload_text)
        self.assertNotIn("submit", payload_text)
        self.assertNotIn("cancel", payload_text)
        self.assertNotIn("valuation", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("quick find", payload_text)

    def test_phase0_removes_manager_readiness_from_overview_payload(self):
        CURRENT_ROLES[:] = ["Warehouse Manager"]

        payload = service.get_warehouse_console_overview()

        self.assertNotIn("manager_center", payload)
        payload_text = str(payload).lower()
        self.assertNotIn("manager readiness", payload_text)
        self.assertNotIn("manager readiness", payload_text)
        self.assertNotIn("warehouse_page', 'route': 'warehouse-console-receiving", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertNotIn("/desk/form", payload_text)

    def test_w14b_quick_find_is_role_scoped_preview_and_custom_route_only(self):
        payload = service.get_warehouse_quick_find_suggestions("PO", limit=8)

        self.assertEqual(payload["state"], "ready")
        self.assertIn("receiving", [group["key"] for group in payload["groups"]])
        self.assertGreaterEqual(len(payload["results"]), 1)
        for result in payload["results"]:
            target = result["target"]
            self.assertEqual(target["kind"], "warehouse_page")
            self.assertIn(target["route"], {
                "warehouse-console-receiving",
                "warehouse-console-picking",
                "warehouse-console-stock-exception",
                "warehouse-console-stock-posture",
                "warehouse-console-movement",
            })
            self.assertIn("preview", result)
            self.assertIn("primary_action_label", result["preview"])
            self.assertNotIn("/app/", str(result))
            self.assertNotIn("/desk/Form", str(result))
            self.assertNotIn("valuation_rate", str(result).lower())
            self.assertNotIn("stock_value", str(result).lower())

    def test_w14b_quick_find_restricted_without_warehouse_role(self):
        CURRENT_ROLES[:] = []

        payload = service.get_warehouse_quick_find_suggestions("PO", limit=8)

        self.assertEqual(payload["state"], "restricted")
        self.assertEqual(payload["results"], [])
        self.assertEqual(payload["groups"], [])

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
            self.assertEqual(row["route_targets"]["movement_review"]["route"], "warehouse-console-movement")
            self.assertTrue(row["route_targets"]["movement_review"]["context_token"])
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


    def test_transfer_visibility_payload_is_grouped_read_only_and_allowlisted(self):
        payload = service.get_warehouse_transfer_visibility_queue("transfer-visibility")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"], {"title": "Transfer Visibility", "key": "transfer_visibility"})
        self.assertEqual(payload["action_targets"]["movement_review"]["route"], "warehouse-console-movement")
        self.assertEqual(payload["action_targets"]["stock_posture"]["route"], "warehouse-console-stock-posture")
        groups = {group["key"]: group for group in payload["groups"]}
        self.assertEqual(len(groups["direct_transfers"]["rows"]), 1)
        self.assertEqual([row["transfer_id"] for row in payload["rows"]], ["MAT-MOV-0001"])

        allowed_row_keys = {
            "key",
            "transfer_id",
            "movement_id",
            "movement_type",
            "purpose",
            "posting_date",
            "posting_time",
            "source_warehouse",
            "target_warehouse",
            "direction_label",
            "posture_key",
            "posture",
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
            self.assertEqual(row["route_targets"]["movement_review"]["route"], "warehouse-console-movement")
            self.assertTrue(row["route_targets"]["movement_review"]["context_token"])
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

    def test_transfer_visibility_filters_and_movement_review_return_route_are_custom(self):
        READABLE_DOCTYPES.discard("Stock Entry Detail")

        payload = service.get_warehouse_transfer_visibility_queue(
            "transfer_visibility",
            {"transfer_state": "direct_transfers", "source_warehouse": "Stores", "target_warehouse": "Main", "item": "Speaker"},
        )

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual([row["transfer_id"] for row in payload["rows"]], ["MAT-MOV-0001"])
        self.assertEqual(payload["controls"]["fields"][0]["value"], "direct_transfers")
        self.assertEqual(payload["controls"]["fields"][2]["value"], "Stores")
        self.assertEqual(payload["controls"]["fields"][3]["value"], "Main")
        self.assertEqual(payload["controls"]["fields"][4]["value"], "Speaker")
        self.assertFalse(any(call["doctype"] == "Stock Entry Detail" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Stock Entry" for call in GET_DOC_CALLS))
        token = payload["rows"][0]["route_targets"]["movement_review"]["context_token"]
        review = service.get_warehouse_movement_review(token)
        self.assertEqual(review["state"]["kind"], "ready")
        self.assertEqual(review["action_targets"]["back"], {"route": "warehouse-console-worklist", "queue_key": "transfer_visibility"})
        self.assertNotIn("native", str(payload).lower())


    def test_movement_review_payload_is_read_only_and_custom_routed(self):
        token = service._movement_review_context_token("MAT-MOV-0001")

        payload = service.get_warehouse_movement_review(token)

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"]["key"], "movement_review")
        self.assertEqual(payload["page"]["context_token"], token)
        self.assertEqual(payload["header"]["movement_id"], "MAT-MOV-0001")
        self.assertEqual(payload["header"]["docstatus_label"], "Posted")
        self.assertEqual(payload["action_targets"]["back"], {"route": "warehouse-console-worklist", "queue_key": "movement_visibility"})
        self.assertGreaterEqual(len(payload["line_groups"]), 1)
        self.assertGreaterEqual(len(payload["related_routes"]), 1)
        self.assertEqual({card["key"] for card in payload["summary_cards"]}, {"items", "quantity", "warehouses", "posture_routes"})

        allowed_parent_keys = {
            "movement_id",
            "purpose",
            "movement_type",
            "posting_date",
            "posting_time",
            "source_warehouse",
            "target_warehouse",
            "direction_label",
            "docstatus_label",
            "item_count",
            "quantity_summary",
            "freshness",
        }
        self.assertLessEqual(set(payload["movement"]), allowed_parent_keys)
        allowed_line_keys = {
            "item_code",
            "item_name",
            "stock_uom",
            "quantity",
            "source_warehouse",
            "target_warehouse",
            "direction_label",
            "line_note",
            "stock_posture_route",
        }
        for group in payload["line_groups"]:
            for row in group["rows"]:
                self.assertLessEqual(set(row), allowed_line_keys)
                self.assertEqual(row["stock_posture_route"]["route"], "warehouse-console-stock-posture")
        payload_text = str(payload).lower()
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("stock_value_difference", payload_text)
        self.assertNotIn("incoming_rate", payload_text)
        self.assertNotIn("outgoing_rate", payload_text)
        self.assertNotIn("basic_rate", payload_text)
        self.assertNotIn("base_amount", payload_text)
        self.assertNotIn("expense_account", payload_text)
        self.assertNotIn("difference_account", payload_text)
        self.assertNotIn("stock_queue", payload_text)
        self.assertNotIn("stock ledger", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertTrue(any(call["doctype"] == "Stock Entry" for call in LIST_CALLS))
        self.assertTrue(any(call["doctype"] == "Stock Entry Detail" for call in GET_ALL_CALLS))

    def test_movement_review_uses_parent_stock_entry_when_child_table_read_is_unavailable(self):
        READABLE_DOCTYPES.discard("Stock Entry Detail")
        token = service._movement_review_context_token("MAT-MOV-0002")

        payload = service.get_warehouse_movement_review(token)

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["header"]["movement_id"], "MAT-MOV-0002")
        self.assertFalse(any(call["doctype"] == "Stock Entry Detail" for call in GET_ALL_CALLS))
        self.assertTrue(any(call["doctype"] == "Stock Entry" for call in GET_DOC_CALLS))
        self.assertNotIn("valuation_rate", str(payload).lower())

    def test_movement_review_invalid_context_returns_controlled_state(self):
        payload = service.get_warehouse_movement_review("not-a-movement")

        self.assertEqual(payload["state"]["kind"], "unavailable")
        self.assertEqual(payload["line_groups"], [])
        self.assertEqual(payload["related_routes"], [])


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

    def _create_receiving_task(self, *, line=None, request_id="draft-for-manager"):
        CURRENT_ROLES[:] = ["Warehouse Manager"]
        payload = service.save_warehouse_receiving_task_draft(
            purchase_order="PO-PARTIAL",
            target_warehouse="Main - M",
            lines=[
                line or {
                    "item_code": "ITEM-003",
                    "target_warehouse": "Main - M",
                    "counted_qty": 13,
                    "accepted_qty": 13,
                }
            ],
            note="Counted at receiving dock.",
            request_id=request_id,
        )
        return RECEIVING_TASK_DOCS[payload["task"]["task_id"]]

    def test_w15c3_save_receiving_task_draft_creates_internal_task_without_stock_document(self):
        payload = service.save_warehouse_receiving_task_draft(
            purchase_order="PO-PARTIAL",
            target_warehouse="Main - M",
            lines=[
                {
                    "item_code": "ITEM-003",
                    "target_warehouse": "Main - M",
                    "counted_qty": 5,
                    "accepted_qty": 5,
                }
            ],
            note="Counted at receiving dock.",
            request_id="req-001",
        )

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"]["key"], "receiving_task_draft")
        self.assertEqual(payload["task"]["purchase_order"], "PO-PARTIAL")
        self.assertEqual(payload["task"]["target_warehouse"], "Main - M")
        self.assertEqual(payload["task"]["status"], "In Progress")
        self.assertEqual(payload["task"]["line_count"], 1)
        self.assertFalse(payload["stock_effect"]["stock_posted"])
        self.assertFalse(payload["stock_effect"]["purchase_receipt_created"])
        self.assertFalse(payload["stock_effect"]["purchase_receipt_submitted"])
        self.assertEqual(len(RECEIVING_TASK_DOCS), 1)
        task = next(iter(RECEIVING_TASK_DOCS.values()))
        self.assertEqual(task.policy_version, service.RECEIVING_TASK_POLICY_VERSION)
        self.assertEqual(task.last_request_id, "req-001")
        self.assertEqual(len(task.lines), 1)
        self.assertEqual(task.lines[0]["item_code"], "ITEM-003")
        self.assertEqual(task.lines[0]["accepted_qty"], 5.0)
        self.assertEqual(len(task.events), 1)
        self.assertEqual(task.events[0]["event_type"], "saved_count_draft")
        payload_text = str(payload).lower()
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertFalse(any(call["doctype"] == "Purchase Receipt" for call in GET_DOC_CALLS))

    def test_w15c3_save_receiving_task_draft_is_idempotent_by_request_id(self):
        first = service.save_warehouse_receiving_task_draft(
            purchase_order="PO-PARTIAL",
            target_warehouse="Main - M",
            lines=[{"item_code": "ITEM-003", "target_warehouse": "Main - M", "counted_qty": 3, "accepted_qty": 3}],
            request_id="same-req",
        )
        second = service.save_warehouse_receiving_task_draft(
            purchase_order="PO-PARTIAL",
            target_warehouse="Main - M",
            lines=[{"item_code": "ITEM-003", "target_warehouse": "Main - M", "counted_qty": 3, "accepted_qty": 3}],
            request_id="same-req",
        )

        self.assertEqual(first["task"]["task_id"], second["task"]["task_id"])
        self.assertFalse(first["task"]["idempotent"])
        self.assertTrue(second["task"]["idempotent"])
        task = next(iter(RECEIVING_TASK_DOCS.values()))
        self.assertEqual(len(task.events), 1)

    def test_w15c3_receiving_task_requires_evidence_for_damage_overage_and_quarantine(self):
        with self.assertRaises(Exception):
            service.save_warehouse_receiving_task_draft(
                purchase_order="PO-PARTIAL",
                target_warehouse="Main - M",
                lines=[
                    {
                        "item_code": "ITEM-003",
                        "target_warehouse": "Main - M",
                        "counted_qty": 7,
                        "accepted_qty": 5,
                        "damaged_qty": 2,
                        "discrepancy_reason": "damaged",
                    }
                ],
                request_id="needs-evidence",
            )
        self.assertEqual(RECEIVING_TASK_DOCS, {})

        payload = service.save_warehouse_receiving_task_draft(
            purchase_order="PO-PARTIAL",
            target_warehouse="Main - M",
            lines=[
                {
                    "item_code": "ITEM-003",
                    "target_warehouse": "Main - M",
                    "counted_qty": 7,
                    "accepted_qty": 5,
                    "damaged_qty": 2,
                    "discrepancy_reason": "damaged",
                    "evidence_reference": "Dock photo DR-1",
                }
            ],
            request_id="has-evidence",
        )

        self.assertEqual(payload["state"]["kind"], "ready")
        task = next(iter(RECEIVING_TASK_DOCS.values()))
        self.assertEqual(task.lines[0]["evidence_reference"], "Dock photo DR-1")
        self.assertEqual(task.lines[0]["line_status"], "Needs Review")

    def test_w15c3_receiving_task_rejects_lines_outside_purchase_order_warehouse(self):
        with self.assertRaises(Exception):
            service.save_warehouse_receiving_task_draft(
                purchase_order="PO-PARTIAL",
                target_warehouse="Receiving - M",
                lines=[{"item_code": "ITEM-003", "target_warehouse": "Receiving - M", "counted_qty": 1}],
                request_id="wrong-warehouse",
            )
        self.assertEqual(RECEIVING_TASK_DOCS, {})

    def test_w15c4_manager_can_request_recount_and_event_is_appended(self):
        task = self._create_receiving_task(request_id="draft-recount")

        payload = service.save_warehouse_receiving_manager_decision(
            task_id=task.name,
            decision="request_recount",
            note="Recount dock two before review.",
            request_id="mgr-recount-1",
        )

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["status"], "Recount Requested")
        self.assertEqual(payload["decision"], "request_recount")
        self.assertEqual(payload["last_event"]["event_type"], "requested_recount")
        self.assertEqual(payload["last_event"]["previous_status"], "In Progress")
        self.assertEqual(payload["last_event"]["next_status"], "Recount Requested")
        self.assertEqual(len(task.events), 2)
        self.assertFalse(payload["stock_effect"]["stock_posted"])
        self.assertFalse(payload["stock_effect"]["purchase_receipt_created"])
        self.assertFalse(payload["stock_effect"]["purchase_receipt_submitted"])
        self.assertFalse(any(call["doctype"] == "Purchase Receipt" for call in GET_DOC_CALLS))

    def test_w15c4_manager_can_approve_clean_task_only_for_clean_lines(self):
        task = self._create_receiving_task(request_id="draft-clean")

        payload = service.save_warehouse_receiving_manager_decision(
            task_id=task.name,
            decision="approve_clean",
            note="Clean count.",
            request_id="mgr-clean-1",
        )

        self.assertEqual(payload["status"], "Approved Clean")
        self.assertEqual(payload["last_event"]["event_type"], "approved_clean")
        self.assertEqual(task.status, "Approved Clean")
        self.assertEqual(task.decision, "approve_clean")
        self.assertEqual(task.manager, "warehouse@example.com")
        self.assertEqual(len(task.events), 2)

    def test_w15c4_manager_cannot_approve_clean_task_with_discrepancy_line(self):
        task = self._create_receiving_task(
            request_id="draft-damaged",
            line={
                "item_code": "ITEM-003",
                "target_warehouse": "Main - M",
                "counted_qty": 13,
                "accepted_qty": 11,
                "damaged_qty": 2,
                "discrepancy_reason": "damaged",
                "evidence_reference": "Dock photo D-1",
            },
        )

        with self.assertRaises(Exception):
            service.save_warehouse_receiving_manager_decision(
                task_id=task.name,
                decision="approve_clean",
                note="Clean despite damage.",
                request_id="mgr-clean-damaged",
            )
        self.assertEqual(task.status, "In Progress")
        self.assertEqual(len(task.events), 1)

    def test_w15c4_manager_can_approve_discrepancy_only_when_discrepancy_exists(self):
        clean_task = self._create_receiving_task(request_id="draft-clean-discrepancy-check")
        with self.assertRaises(Exception):
            service.save_warehouse_receiving_manager_decision(
                task_id=clean_task.name,
                decision="approve_discrepancy",
                request_id="mgr-discrepancy-clean",
            )
        RECEIVING_TASK_DOCS.clear()
        task = self._create_receiving_task(
            request_id="draft-short",
            line={
                "item_code": "ITEM-003",
                "target_warehouse": "Main - M",
                "counted_qty": 10,
                "accepted_qty": 10,
            },
        )

        payload = service.save_warehouse_receiving_manager_decision(
            task_id=task.name,
            decision="approve_discrepancy",
            note="Shortage is inside review tolerance.",
            request_id="mgr-discrepancy-1",
        )

        self.assertEqual(payload["status"], "Approved With Discrepancy")
        self.assertEqual(payload["last_event"]["event_type"], "approved_with_discrepancy")
        self.assertEqual(len(task.events), 2)

    def test_w15c4_manager_can_mark_quarantine_only_with_quarantine_or_damage_evidence(self):
        clean_task = self._create_receiving_task(request_id="draft-clean-quarantine-check")
        with self.assertRaises(Exception):
            service.save_warehouse_receiving_manager_decision(
                task_id=clean_task.name,
                decision="mark_quarantine_review",
                request_id="mgr-quarantine-clean",
            )
        RECEIVING_TASK_DOCS.clear()
        task = self._create_receiving_task(
            request_id="draft-quarantine",
            line={
                "item_code": "ITEM-003",
                "target_warehouse": "Main - M",
                "counted_qty": 13,
                "accepted_qty": 10,
                "quarantine_qty": 3,
                "discrepancy_reason": "quarantine",
                "evidence_reference": "Quarantine tag Q-7",
            },
        )

        payload = service.save_warehouse_receiving_manager_decision(
            task_id=task.name,
            decision="mark_quarantine_review",
            note="Hold goods for quarantine review.",
            request_id="mgr-quarantine-1",
        )

        self.assertEqual(payload["status"], "Quarantine Review")
        self.assertEqual(payload["last_event"]["event_type"], "marked_quarantine_review")

    def test_w15c4_manager_can_escalate_to_procurement_without_purchase_receipt_effect(self):
        task = self._create_receiving_task(
            request_id="draft-over",
            line={
                "item_code": "ITEM-003",
                "target_warehouse": "Main - M",
                "counted_qty": 15,
                "accepted_qty": 13,
                "over_qty": 2,
                "discrepancy_reason": "over",
                "evidence_reference": "Supplier paperwork O-4",
            },
        )

        payload = service.save_warehouse_receiving_manager_decision(
            task_id=task.name,
            decision="escalate_to_procurement",
            note="Overage needs Procurement decision.",
            request_id="mgr-procurement-1",
        )

        self.assertEqual(payload["status"], "Escalated To Procurement")
        self.assertEqual(payload["last_event"]["event_type"], "escalated_to_procurement")
        self.assertFalse(payload["stock_effect"]["stock_posted"])
        self.assertFalse(payload["stock_effect"]["purchase_receipt_created"])
        self.assertFalse(payload["stock_effect"]["purchase_receipt_submitted"])
        self.assertFalse(any(call["doctype"] == "Purchase Receipt" for call in GET_DOC_CALLS))

    def test_w15c4_warehouse_user_cannot_make_manager_decision(self):
        task = self._create_receiving_task(request_id="draft-user-denied")
        CURRENT_ROLES[:] = ["Warehouse User"]

        with self.assertRaises(Exception):
            service.save_warehouse_receiving_manager_decision(
                task_id=task.name,
                decision="request_recount",
                request_id="mgr-user-denied",
            )
        self.assertEqual(task.status, "In Progress")
        self.assertEqual(len(task.events), 1)

    def test_w15c4_manager_decision_rejects_unknown_decision(self):
        task = self._create_receiving_task(request_id="draft-unknown-decision")

        with self.assertRaises(Exception):
            service.save_warehouse_receiving_manager_decision(
                task_id=task.name,
                decision="prepare_purchase_receipt",
                request_id="mgr-unknown-decision",
            )
        self.assertEqual(task.status, "In Progress")
        self.assertEqual(len(task.events), 1)

    def test_w15c4_manager_decision_rejects_final_status(self):
        task = self._create_receiving_task(request_id="draft-final-status")
        task.status = "Approved Clean"

        with self.assertRaises(Exception):
            service.save_warehouse_receiving_manager_decision(
                task_id=task.name,
                decision="request_recount",
                request_id="mgr-final-status",
            )
        self.assertEqual(task.status, "Approved Clean")
        self.assertEqual(len(task.events), 1)

    def test_w15c4_manager_decision_request_id_is_idempotent(self):
        task = self._create_receiving_task(request_id="draft-idempotent")
        first = service.save_warehouse_receiving_manager_decision(
            task_id=task.name,
            decision="request_recount",
            note="Same request.",
            request_id="mgr-same-req",
        )
        second = service.save_warehouse_receiving_manager_decision(
            task_id=task.name,
            decision="request_recount",
            note="Same request.",
            request_id="mgr-same-req",
        )

        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        self.assertEqual(first["task_id"], second["task_id"])
        self.assertEqual(len(task.events), 2)
        with self.assertRaises(Exception):
            service.save_warehouse_receiving_manager_decision(
                task_id=task.name,
                decision="approve_clean",
                request_id="mgr-same-req",
            )

    def test_w15c4_manager_decision_request_id_cannot_cross_tasks(self):
        task = self._create_receiving_task(request_id="draft-cross-task-one")
        service.save_warehouse_receiving_manager_decision(
            task_id=task.name,
            decision="request_recount",
            request_id="mgr-cross-task",
        )

        with self.assertRaises(Exception):
            service.save_warehouse_receiving_manager_decision(
                task_id="WRT-OTHER-TASK",
                decision="request_recount",
                request_id="mgr-cross-task",
            )
        self.assertEqual(task.status, "Recount Requested")
        self.assertEqual(len(task.events), 2)

    def test_w15c4_manager_decision_response_has_no_native_or_commercial_leakage(self):
        task = self._create_receiving_task(request_id="draft-safe-response")

        payload = service.save_warehouse_receiving_manager_decision(
            task_id=task.name,
            decision="approve_clean",
            request_id="mgr-safe-response",
        )

        payload_text = str(payload).lower()
        self.assertEqual(payload["valuation"], {"visible": False, "fields": []})
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("rate", payload_text)
        self.assertNotIn("amount", payload_text)
        self.assertNotIn("tax", payload_text)
        self.assertNotIn("account", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertNotIn("/desk/form", payload_text)
        self.assertFalse(payload["stock_effect"]["stock_posted"])
        self.assertFalse(payload["stock_effect"]["purchase_receipt_created"])
        self.assertFalse(payload["stock_effect"]["purchase_receipt_submitted"])

    def _save_pick_task(self, **overrides):
        payload = {
            "sales_order": "SO-REVIEW",
            "source_warehouse": "Short - M",
            "lines": [
                {
                    "item_code": "ITEM-105",
                    "warehouse": "Short - M",
                    "picked_qty": 2,
                    "packed_qty": 2,
                }
            ],
            "note": "Picked at outbound bench.",
            "request_id": "pick-req-001",
        }
        payload.update(overrides)
        return service.save_warehouse_picking_task_draft(**payload)

    def test_w15d3_warehouse_user_can_save_custom_pick_task_draft(self):
        payload = self._save_pick_task()

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"]["key"], "picking_task_draft")
        self.assertEqual(payload["task"]["sales_order"], "SO-REVIEW")
        self.assertEqual(payload["task"]["source_warehouse"], "Short - M")
        self.assertEqual(payload["task"]["status"], "In Progress")
        self.assertEqual(payload["task"]["workflow_state"], "Pick draft saved")
        self.assertEqual(payload["task"]["line_count"], 1)
        self.assertFalse(payload["stock_effect"])
        self.assertFalse(payload["delivery_note_created"])
        self.assertFalse(payload["delivery_note_submitted"])
        self.assertFalse(payload["pick_list_created"])
        self.assertFalse(payload["stock_reserved"])
        self.assertFalse(payload["stock_posted"])
        self.assertEqual(payload["valuation"], {"visible": False, "fields": []})
        self.assertEqual(len(PICKING_TASK_DOCS), 1)
        task = next(iter(PICKING_TASK_DOCS.values()))
        self.assertEqual(task.policy_version, service.PICKING_TASK_POLICY_VERSION)
        self.assertEqual(task.request_id, "pick-req-001")
        self.assertEqual(len(task.lines), 1)
        self.assertEqual(task.lines[0]["item_code"], "ITEM-105")
        self.assertEqual(task.lines[0]["picked_qty"], 2.0)
        self.assertEqual(len(task.events), 1)
        self.assertEqual(task.events[0]["event_type"], "saved_pick_draft")

    def test_w15d3_non_warehouse_user_is_denied(self):
        CURRENT_ROLES[:] = ["Sales User"]
        with self.assertRaises(Exception):
            self._save_pick_task(request_id="pick-denied")
        self.assertEqual(PICKING_TASK_DOCS, {})

    def test_w15d3_unknown_or_invisible_sales_order_is_denied(self):
        with self.assertRaises(Exception):
            self._save_pick_task(sales_order="SO-MISSING", request_id="pick-missing")
        self.assertEqual(PICKING_TASK_DOCS, {})

    def test_w15d3_wrong_warehouse_and_line_mismatch_are_rejected(self):
        with self.assertRaises(Exception):
            self._save_pick_task(source_warehouse="Main - M", request_id="pick-wrong-warehouse")
        with self.assertRaises(Exception):
            self._save_pick_task(
                lines=[{"item_code": "ITEM-103", "warehouse": "Short - M", "picked_qty": 1}],
                request_id="pick-line-mismatch",
            )
        self.assertEqual(PICKING_TASK_DOCS, {})

    def test_w15d3_duplicate_line_is_rejected(self):
        with self.assertRaises(Exception):
            self._save_pick_task(
                lines=[
                    {"item_code": "ITEM-105", "warehouse": "Short - M", "picked_qty": 1},
                    {"item_code": "ITEM-105", "warehouse": "Short - M", "picked_qty": 1},
                ],
                request_id="pick-duplicate-line",
            )
        self.assertEqual(PICKING_TASK_DOCS, {})

    def test_w15d3_negative_and_over_open_quantities_are_rejected(self):
        with self.assertRaises(Exception):
            self._save_pick_task(
                lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "picked_qty": -1}],
                request_id="pick-negative",
            )
        with self.assertRaises(Exception):
            self._save_pick_task(
                lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "picked_qty": 9}],
                request_id="pick-over-open",
            )
        with self.assertRaises(Exception):
            self._save_pick_task(
                lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "picked_qty": 2, "packed_qty": 3}],
                request_id="pick-packed-over-picked",
            )
        self.assertEqual(PICKING_TASK_DOCS, {})

    def test_w15d3_short_damage_and_not_found_require_evidence_or_note(self):
        with self.assertRaises(Exception):
            self._save_pick_task(
                lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "picked_qty": 1, "short_qty": 1}],
                request_id="pick-short-no-evidence",
                note="",
            )
        payload = self._save_pick_task(
            lines=[
                {
                    "item_code": "ITEM-105",
                    "warehouse": "Short - M",
                    "picked_qty": 1,
                    "damaged_qty": 1,
                    "exception_type": "damaged",
                    "evidence_reference": "Corner damage photo DR-2",
                }
            ],
            request_id="pick-damaged-evidence",
        )
        task = PICKING_TASK_DOCS[payload["task"]["task_id"]]
        self.assertEqual(task.lines[0]["line_status"], "Needs Review")
        self.assertEqual(task.lines[0]["exception_type"], "damaged")
        self.assertEqual(task.lines[0]["evidence_reference"], "Corner damage photo DR-2")
        self.assertEqual(payload["task"]["lines"][0]["evidence_reference"], "Corner damage photo DR-2")

    def test_w15d3_request_idempotency_returns_same_result(self):
        first = self._save_pick_task(request_id="pick-same-req")
        second = self._save_pick_task(request_id="pick-same-req")

        self.assertEqual(first["task"]["task_id"], second["task"]["task_id"])
        self.assertFalse(first["task"]["idempotent"])
        self.assertTrue(second["task"]["idempotent"])
        task = next(iter(PICKING_TASK_DOCS.values()))
        self.assertEqual(len(task.events), 1)

    def test_w15d3_request_id_reuse_across_sales_order_is_rejected(self):
        self._save_pick_task(request_id="pick-cross-task")
        with self.assertRaises(Exception):
            self._save_pick_task(
                sales_order="SO-READY",
                source_warehouse="Main - M",
                lines=[{"item_code": "ITEM-103", "warehouse": "Main - M", "picked_qty": 1}],
                request_id="pick-cross-task",
            )
        self.assertEqual(len(PICKING_TASK_DOCS), 1)

    def test_w15d3_payload_has_no_native_or_commercial_leakage_and_no_stock_docs(self):
        payload = self._save_pick_task(request_id="pick-safe-response")

        payload_text = str(payload).lower()
        self.assertNotIn("/app/", payload_text)
        self.assertNotIn("/desk/form", payload_text)
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("amount", payload_text)
        self.assertNotIn("tax", payload_text)
        self.assertNotIn("account", payload_text)
        self.assertEqual(payload["valuation"], {"visible": False, "fields": []})
        self.assertFalse(payload["delivery_note_created"])
        self.assertFalse(payload["delivery_note_submitted"])
        self.assertFalse(payload["pick_list_created"])
        self.assertFalse(payload["stock_reserved"])
        self.assertFalse(payload["stock_posted"])
        forbidden_docs = {"Delivery Note", "Pick List", "Stock Reservation Entry", "Stock Entry", "Stock Ledger Entry"}
        self.assertFalse(any(call["doctype"] in forbidden_docs for call in GET_DOC_CALLS))
        self.assertFalse(any(call["doctype"] in forbidden_docs for call in GET_ALL_CALLS))

    def _save_pick_manager_decision(self, task, decision, request_id, note=""):
        CURRENT_ROLES[:] = ["Warehouse Manager"]
        return service.save_warehouse_picking_manager_decision(
            task_id=task.name,
            decision=decision,
            note=note,
            request_id=request_id,
        )

    def test_w15d4_warehouse_user_cannot_make_picking_manager_decision(self):
        payload = self._save_pick_task(request_id="pick-user-denied-draft")
        task = PICKING_TASK_DOCS[payload["task"]["task_id"]]
        CURRENT_ROLES[:] = ["Warehouse User"]

        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=task.name,
                decision="request_repick",
                note="User cannot make manager decision.",
                request_id="pick-mgr-user-denied",
            )
        CURRENT_ROLES[:] = ["Stock User"]
        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=task.name,
                decision="request_repick",
                note="Stock user cannot make manager decision.",
                request_id="pick-mgr-stock-user-denied",
            )
        self.assertEqual(task.task_status, "In Progress")
        self.assertEqual(len(task.events), 1)

    def test_w15d4_manager_can_request_repick_and_event_is_appended(self):
        payload = self._save_pick_task(request_id="pick-repick-draft")
        task = PICKING_TASK_DOCS[payload["task"]["task_id"]]

        result = self._save_pick_manager_decision(
            task,
            "request_repick",
            "pick-mgr-repick",
            note="Check outbound bin count again.",
        )

        self.assertEqual(result["state"]["kind"], "ready")
        self.assertEqual(result["status"], "Repick Requested")
        self.assertEqual(result["decision"], "request_repick")
        self.assertEqual(result["event_summary"]["event_type"], "requested_repick")
        self.assertEqual(task.task_status, "Repick Requested")
        self.assertEqual(task.workflow_state, "Repick requested")
        self.assertEqual(len(task.events), 2)
        self.assertFalse(result["stock_effect"])
        self.assertFalse(result["delivery_note_created"])
        self.assertFalse(result["pick_list_created"])
        self.assertFalse(result["stock_reserved"])
        self.assertFalse(result["sales_order_updated"])
        self.assertFalse(result["customer_notified"])

    def test_w15d4_manager_decision_rejects_unknown_and_final_status(self):
        payload = self._save_pick_task(request_id="pick-manager-invalid-draft")
        task = PICKING_TASK_DOCS[payload["task"]["task_id"]]
        CURRENT_ROLES[:] = ["Warehouse Manager"]

        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=task.name,
                decision="create_delivery_note",
                request_id="pick-mgr-unknown",
            )
        task.task_status = "Closed"
        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=task.name,
                decision="request_repick",
                note="Closed tasks cannot move.",
                request_id="pick-mgr-final",
            )
        self.assertEqual(len(task.events), 1)

    def test_w15d4_clean_pick_approval_requires_clean_lines(self):
        clean_payload = self._save_pick_task(request_id="pick-clean-approval-draft")
        clean_task = PICKING_TASK_DOCS[clean_payload["task"]["task_id"]]

        result = self._save_pick_manager_decision(clean_task, "approve_clean_pick", "pick-mgr-clean")

        self.assertEqual(result["status"], "Clean Pick Approved")
        self.assertEqual(result["event_summary"]["event_type"], "approved_clean_pick")
        self.assertEqual(clean_task.task_status, "Clean Pick Approved")

        PICKING_TASK_DOCS.clear()
        damaged_payload = self._save_pick_task(
            request_id="pick-damaged-approval-draft",
            lines=[
                {
                    "item_code": "ITEM-105",
                    "warehouse": "Short - M",
                    "picked_qty": 1,
                    "damaged_qty": 1,
                    "exception_type": "damaged",
                    "evidence_reference": "Damaged carton D-15",
                }
            ],
        )
        damaged_task = PICKING_TASK_DOCS[damaged_payload["task"]["task_id"]]
        CURRENT_ROLES[:] = ["Warehouse Manager"]
        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=damaged_task.name,
                decision="approve_clean_pick",
                request_id="pick-mgr-clean-damaged",
            )
        self.assertEqual(damaged_task.task_status, "In Progress")
        self.assertEqual(len(damaged_task.events), 1)

    def test_w15d4_partial_pick_and_shortage_review_require_shortage_evidence(self):
        clean_payload = self._save_pick_task(request_id="pick-partial-clean-draft")
        clean_task = PICKING_TASK_DOCS[clean_payload["task"]["task_id"]]
        CURRENT_ROLES[:] = ["Warehouse Manager"]
        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=clean_task.name,
                decision="approve_partial_pick",
                request_id="pick-mgr-partial-clean",
            )
        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=clean_task.name,
                decision="mark_shortage_review",
                request_id="pick-mgr-shortage-clean",
            )

        PICKING_TASK_DOCS.clear()
        short_payload = self._save_pick_task(
            request_id="pick-short-approval-draft",
            lines=[
                {
                    "item_code": "ITEM-105",
                    "warehouse": "Short - M",
                    "picked_qty": 1,
                    "short_qty": 2,
                    "exception_type": "short",
                    "evidence_reference": "Shelf shortage S-2",
                }
            ],
        )
        short_task = PICKING_TASK_DOCS[short_payload["task"]["task_id"]]
        partial = self._save_pick_manager_decision(short_task, "approve_partial_pick", "pick-mgr-partial")
        self.assertEqual(partial["status"], "Partial Pick Approved")
        self.assertEqual(partial["event_summary"]["event_type"], "approved_partial_pick")

        PICKING_TASK_DOCS.clear()
        short_payload = self._save_pick_task(
            request_id="pick-short-review-draft",
            lines=[
                {
                    "item_code": "ITEM-105",
                    "warehouse": "Short - M",
                    "picked_qty": 1,
                    "not_found_qty": 1,
                    "exception_type": "not_found",
                    "evidence_reference": "Bin check NF-1",
                }
            ],
        )
        short_task = PICKING_TASK_DOCS[short_payload["task"]["task_id"]]
        shortage = self._save_pick_manager_decision(short_task, "mark_shortage_review", "pick-mgr-shortage")
        self.assertEqual(shortage["status"], "Shortage Review")
        self.assertEqual(shortage["event_summary"]["event_type"], "marked_shortage_review")

    def test_w15d4_sales_escalation_requires_sales_issue_or_reason(self):
        clean_payload = self._save_pick_task(request_id="pick-sales-clean-draft")
        clean_task = PICKING_TASK_DOCS[clean_payload["task"]["task_id"]]
        CURRENT_ROLES[:] = ["Warehouse Manager"]
        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=clean_task.name,
                decision="escalate_to_sales",
                request_id="pick-mgr-sales-clean",
            )

        result = service.save_warehouse_picking_manager_decision(
            task_id=clean_task.name,
            decision="escalate_to_sales",
            note="Customer-facing delivery quantity needs Sales review.",
            request_id="pick-mgr-sales-reason",
        )
        self.assertEqual(result["status"], "Sales Escalation")
        self.assertFalse(result["sales_order_updated"])
        self.assertFalse(result["customer_notified"])

    def test_w15d4_pack_ready_requires_picked_packed_and_no_unresolved_damage(self):
        no_pack_payload = self._save_pick_task(
            request_id="pick-no-pack-draft",
            lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "picked_qty": 2, "packed_qty": 0}],
        )
        no_pack_task = PICKING_TASK_DOCS[no_pack_payload["task"]["task_id"]]
        CURRENT_ROLES[:] = ["Warehouse Manager"]
        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=no_pack_task.name,
                decision="mark_pack_ready",
                request_id="pick-mgr-pack-no-pack",
            )

        PICKING_TASK_DOCS.clear()
        damaged_payload = self._save_pick_task(
            request_id="pick-pack-damaged-draft",
            lines=[
                {
                    "item_code": "ITEM-105",
                    "warehouse": "Short - M",
                    "picked_qty": 1,
                    "packed_qty": 1,
                    "damaged_qty": 1,
                    "exception_type": "damaged",
                    "evidence_reference": "Damage D-20",
                }
            ],
        )
        damaged_task = PICKING_TASK_DOCS[damaged_payload["task"]["task_id"]]
        CURRENT_ROLES[:] = ["Warehouse Manager"]
        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=damaged_task.name,
                decision="mark_pack_ready",
                request_id="pick-mgr-pack-damaged",
            )

        PICKING_TASK_DOCS.clear()
        clean_payload = self._save_pick_task(request_id="pick-pack-ready-draft")
        clean_task = PICKING_TASK_DOCS[clean_payload["task"]["task_id"]]
        ready = self._save_pick_manager_decision(clean_task, "mark_pack_ready", "pick-mgr-pack-ready")
        self.assertEqual(ready["status"], "Pack Ready")
        self.assertEqual(ready["event_summary"]["event_type"], "marked_pack_ready")

    def test_w15d4_dispatch_handoff_requires_pack_ready_and_no_delivery_note_effect(self):
        payload = self._save_pick_task(request_id="pick-dispatch-draft")
        task = PICKING_TASK_DOCS[payload["task"]["task_id"]]
        CURRENT_ROLES[:] = ["Warehouse Manager"]
        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=task.name,
                decision="mark_dispatch_handoff",
                request_id="pick-mgr-dispatch-too-soon",
            )
        task.task_status = "Pack Ready"

        result = service.save_warehouse_picking_manager_decision(
            task_id=task.name,
            decision="mark_dispatch_handoff",
            request_id="pick-mgr-dispatch",
        )

        self.assertEqual(result["status"], "Dispatch Handoff Ready")
        self.assertEqual(result["event_summary"]["event_type"], "marked_dispatch_handoff")
        self.assertFalse(result["delivery_note_created"])
        self.assertFalse(result["delivery_note_submitted"])
        self.assertFalse(result["stock_posted"])
        self.assertFalse(any(call["doctype"] == "Delivery Note" for call in GET_DOC_CALLS))

    def test_w15d4_manager_decision_request_id_is_idempotent(self):
        payload = self._save_pick_task(request_id="pick-idempotent-draft")
        task = PICKING_TASK_DOCS[payload["task"]["task_id"]]
        first = self._save_pick_manager_decision(
            task,
            "request_repick",
            "pick-mgr-same-req",
            note="Same manager request.",
        )
        second = self._save_pick_manager_decision(
            task,
            "request_repick",
            "pick-mgr-same-req",
            note="Same manager request.",
        )

        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        self.assertEqual(first["task_id"], second["task_id"])
        self.assertEqual(len(task.events), 2)
        CURRENT_ROLES[:] = ["Warehouse Manager"]
        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=task.name,
                decision="approve_clean_pick",
                request_id="pick-mgr-same-req",
            )

    def test_w15d4_manager_request_id_cannot_cross_picking_tasks(self):
        first_payload = self._save_pick_task(request_id="pick-cross-manager-one")
        first_task = PICKING_TASK_DOCS[first_payload["task"]["task_id"]]
        self._save_pick_manager_decision(
            first_task,
            "request_repick",
            "pick-mgr-cross-task",
            note="First task manager request.",
        )

        second_payload = self._save_pick_task(
            sales_order="SO-READY",
            source_warehouse="Main - M",
            lines=[{"item_code": "ITEM-103", "warehouse": "Main - M", "picked_qty": 2, "packed_qty": 2}],
            request_id="pick-cross-manager-two",
        )
        second_task = PICKING_TASK_DOCS[second_payload["task"]["task_id"]]
        CURRENT_ROLES[:] = ["Warehouse Manager"]
        with self.assertRaises(Exception):
            service.save_warehouse_picking_manager_decision(
                task_id=second_task.name,
                decision="request_repick",
                note="Reuse is not allowed.",
                request_id="pick-mgr-cross-task",
            )
        self.assertEqual(first_task.task_status, "Repick Requested")
        self.assertEqual(second_task.task_status, "In Progress")

    def test_w15d4_manager_decision_response_has_no_native_commercial_or_stock_doc_effect(self):
        payload = self._save_pick_task(request_id="pick-safe-manager-draft")
        task = PICKING_TASK_DOCS[payload["task"]["task_id"]]

        result = self._save_pick_manager_decision(task, "approve_clean_pick", "pick-mgr-safe-response")

        payload_text = str(result).lower()
        self.assertEqual(result["valuation"], {"visible": False, "fields": []})
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("amount", payload_text)
        self.assertNotIn("tax", payload_text)
        self.assertNotIn("account", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertNotIn("/desk/form", payload_text)
        self.assertFalse(result["stock_effect"])
        self.assertFalse(result["delivery_note_created"])
        self.assertFalse(result["delivery_note_submitted"])
        self.assertFalse(result["pick_list_created"])
        self.assertFalse(result["stock_reserved"])
        self.assertFalse(result["stock_posted"])
        self.assertFalse(result["sales_order_updated"])
        self.assertFalse(result["customer_notified"])
        forbidden_docs = {"Delivery Note", "Pick List", "Stock Reservation Entry", "Stock Entry", "Stock Ledger Entry", "Sales Order"}
        self.assertFalse(any(call["doctype"] in forbidden_docs for call in GET_DOC_CALLS))
        self.assertFalse(any(call["doctype"] in forbidden_docs for call in GET_ALL_CALLS))

    def _dispatch_ready_pick_task(
        self,
        request_id="pick-dispatch-ready-draft",
        line=None,
        status="Dispatch Handoff Ready",
        sales_order="SO-REVIEW",
        source_warehouse="Short - M",
    ):
        line_payload = line or {
            "item_code": "ITEM-105",
            "warehouse": source_warehouse,
            "picked_qty": 8,
            "packed_qty": 8,
        }
        payload = self._save_pick_task(
            request_id=request_id,
            sales_order=sales_order,
            source_warehouse=source_warehouse,
            lines=[line_payload],
        )
        task = PICKING_TASK_DOCS[payload["task"]["task_id"]]
        task.task_status = status
        task.workflow_state = "Dispatch handoff marked" if status == "Dispatch Handoff Ready" else status
        return task

    def _request_dispatch_handoff(self, task, as_manager=True, **overrides):
        if as_manager:
            CURRENT_ROLES[:] = ["Warehouse Manager"]
        line = list(getattr(task, "lines", []) or [])[0]
        payload = {
            "picking_task": task.name,
            "lines": [
                {
                    "sales_order_item": line["sales_order_item"],
                    "item_code": line["item_code"],
                    "warehouse": line["warehouse"],
                    "accepted_for_dispatch_qty": 8,
                }
            ],
            "pack_reference": "PACK-001",
            "dispatch_handoff_reference": "HANDOFF-001",
            "package_count": 1,
            "handoff_note": "Packed and staged for Sales/Admin handoff.",
            "request_id": "dispatch-req-001",
        }
        payload.update(overrides)
        return service.request_warehouse_dispatch_handoff(**payload)

    def test_w15d6_warehouse_and_stock_users_are_denied_dispatch_request(self):
        task = self._dispatch_ready_pick_task(request_id="dispatch-user-denied-draft")
        CURRENT_ROLES[:] = ["Warehouse User"]
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(task, as_manager=False, request_id="dispatch-user-denied")
        CURRENT_ROLES[:] = ["Stock User"]
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(task, as_manager=False, request_id="dispatch-stock-user-denied")
        self.assertEqual(DISPATCH_HANDOFF_REQUEST_DOCS, {})

    def test_w15d6_manager_can_create_dispatch_handoff_request_for_ready_clean_task(self):
        task = self._dispatch_ready_pick_task(request_id="dispatch-clean-draft")

        payload = self._request_dispatch_handoff(task, request_id="dispatch-clean-request")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"]["key"], "dispatch_handoff_request")
        self.assertEqual(payload["request"]["picking_task"], task.name)
        self.assertEqual(payload["request"]["sales_order"], "SO-REVIEW")
        self.assertEqual(payload["request"]["warehouse"], "Short - M")
        self.assertEqual(payload["request"]["request_status"], "Requested")
        self.assertEqual(payload["request"]["line_count"], 1)
        self.assertEqual(payload["event_summary"]["event_type"], "requested_dispatch_handoff")
        self.assertFalse(payload["stock_effect"])
        self.assertFalse(payload["delivery_note_created"])
        self.assertFalse(payload["delivery_note_submitted"])
        self.assertFalse(payload["pick_list_created"])
        self.assertFalse(payload["stock_reserved"])
        self.assertFalse(payload["stock_posted"])
        self.assertFalse(payload["sales_order_updated"])
        self.assertFalse(payload["customer_notified"])
        self.assertEqual(len(DISPATCH_HANDOFF_REQUEST_DOCS), 1)
        request = next(iter(DISPATCH_HANDOFF_REQUEST_DOCS.values()))
        self.assertEqual(request.policy_version, service.DISPATCH_HANDOFF_POLICY_VERSION)
        self.assertEqual(request.total_dispatch_qty, 8.0)
        self.assertEqual(len(request.lines), 1)
        self.assertEqual(len(request.events), 1)

    def test_w15d6_unknown_invisible_and_not_ready_tasks_are_rejected(self):
        CURRENT_ROLES[:] = ["Warehouse Manager"]
        with self.assertRaises(Exception):
            service.request_warehouse_dispatch_handoff(
                picking_task="WPT-MISSING",
                lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "accepted_for_dispatch_qty": 1}],
                pack_reference="PACK-X",
                request_id="dispatch-missing-task",
            )
        task = self._dispatch_ready_pick_task(request_id="dispatch-invisible-draft")
        task.sales_order = "SO-MISSING"
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(task, request_id="dispatch-invisible-task")
        self.assertEqual(DISPATCH_HANDOFF_REQUEST_DOCS, {})

        PICKING_TASK_DOCS.clear()
        task = self._dispatch_ready_pick_task(request_id="dispatch-not-ready-draft", status="In Progress")
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(task, request_id="dispatch-not-ready")
        task.task_status = "Closed"
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(task, request_id="dispatch-closed")
        self.assertEqual(DISPATCH_HANDOFF_REQUEST_DOCS, {})

    def test_w15d6_wrong_line_and_quantity_validation(self):
        task = self._dispatch_ready_pick_task(request_id="dispatch-line-validation-draft")
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(
                task,
                lines=[{"item_code": "ITEM-103", "warehouse": "Short - M", "accepted_for_dispatch_qty": 1}],
                request_id="dispatch-wrong-line",
            )
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(
                task,
                lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "accepted_for_dispatch_qty": -1}],
                request_id="dispatch-negative",
            )
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(
                task,
                lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "accepted_for_dispatch_qty": 9}],
                request_id="dispatch-over-picked",
            )

        PICKING_TASK_DOCS.clear()
        task = self._dispatch_ready_pick_task(
            request_id="dispatch-over-packed-draft",
            line={"item_code": "ITEM-105", "warehouse": "Short - M", "picked_qty": 8, "packed_qty": 6},
        )
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(
                task,
                lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "accepted_for_dispatch_qty": 7}],
                request_id="dispatch-over-packed",
            )
        self.assertEqual(DISPATCH_HANDOFF_REQUEST_DOCS, {})

    def test_w15d6_damaged_not_found_and_partial_without_sales_approval_are_rejected(self):
        damaged_task = self._dispatch_ready_pick_task(
            request_id="dispatch-damaged-draft",
            line={
                "item_code": "ITEM-105",
                "warehouse": "Short - M",
                "picked_qty": 7,
                "packed_qty": 7,
                "damaged_qty": 1,
                "exception_type": "damaged",
                "evidence_reference": "Damage D-90",
            },
        )
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(
                damaged_task,
                lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "accepted_for_dispatch_qty": 7}],
                request_id="dispatch-damaged",
            )

        PICKING_TASK_DOCS.clear()
        not_found_task = self._dispatch_ready_pick_task(
            request_id="dispatch-not-found-draft",
            line={
                "item_code": "ITEM-105",
                "warehouse": "Short - M",
                "picked_qty": 7,
                "packed_qty": 7,
                "not_found_qty": 1,
                "exception_type": "not_found",
                "evidence_reference": "Bin NF-7",
            },
        )
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(
                not_found_task,
                lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "accepted_for_dispatch_qty": 7}],
                request_id="dispatch-not-found",
            )

        PICKING_TASK_DOCS.clear()
        partial_task = self._dispatch_ready_pick_task(
            request_id="dispatch-partial-draft",
            line={
                "item_code": "ITEM-105",
                "warehouse": "Short - M",
                "picked_qty": 6,
                "packed_qty": 6,
                "short_qty": 2,
                "exception_type": "short",
                "evidence_reference": "Short S-8",
            },
        )
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(
                partial_task,
                lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "accepted_for_dispatch_qty": 6}],
                request_id="dispatch-partial-no-sales",
            )
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(
                partial_task,
                lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "accepted_for_dispatch_qty": 6}],
                sales_approval_reference="SALES-APP-1",
                handoff_note="",
                request_id="dispatch-partial-no-note",
            )
        payload = self._request_dispatch_handoff(
            partial_task,
            lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "accepted_for_dispatch_qty": 6}],
            sales_approval_reference="SALES-APP-1",
            handoff_note="Sales approved partial dispatch after shortage review.",
            request_id="dispatch-partial-approved",
        )
        self.assertEqual(payload["request"]["request_status"], "Requested")
        self.assertEqual(len(DISPATCH_HANDOFF_REQUEST_DOCS), 1)

    def test_w15d6_missing_pack_or_handoff_evidence_is_rejected(self):
        task = self._dispatch_ready_pick_task(request_id="dispatch-missing-evidence-draft")
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(
                task,
                pack_reference="",
                dispatch_handoff_reference="",
                request_id="dispatch-missing-evidence",
            )
        self.assertEqual(DISPATCH_HANDOFF_REQUEST_DOCS, {})

    def test_w15d6_request_idempotency_and_changed_payload_rejection(self):
        task = self._dispatch_ready_pick_task(request_id="dispatch-idempotent-draft")
        first = self._request_dispatch_handoff(task, request_id="dispatch-same-request")
        second = self._request_dispatch_handoff(task, request_id="dispatch-same-request")

        self.assertFalse(first["request"]["idempotent"])
        self.assertTrue(second["request"]["idempotent"])
        self.assertEqual(first["request"]["request_id"], second["request"]["request_id"])
        self.assertEqual(len(DISPATCH_HANDOFF_REQUEST_DOCS), 1)
        request = next(iter(DISPATCH_HANDOFF_REQUEST_DOCS.values()))
        self.assertEqual(len(request.events), 1)

        with self.assertRaises(Exception):
            self._request_dispatch_handoff(task, package_count=2, request_id="dispatch-same-request")

    def test_w15d6_request_id_cannot_cross_picking_tasks(self):
        first_task = self._dispatch_ready_pick_task(request_id="dispatch-cross-one-draft")
        self._request_dispatch_handoff(first_task, request_id="dispatch-cross-request")

        second_task = self._dispatch_ready_pick_task(
            request_id="dispatch-cross-two-draft",
            sales_order="SO-READY",
            source_warehouse="Main - M",
            line={"item_code": "ITEM-103", "warehouse": "Main - M", "picked_qty": 5, "packed_qty": 5},
        )
        with self.assertRaises(Exception):
            self._request_dispatch_handoff(
                second_task,
                lines=[{"item_code": "ITEM-103", "warehouse": "Main - M", "accepted_for_dispatch_qty": 5}],
                request_id="dispatch-cross-request",
            )
        self.assertEqual(len(DISPATCH_HANDOFF_REQUEST_DOCS), 1)

    def test_w15d6_response_has_no_native_commercial_or_stock_doc_effect(self):
        task = self._dispatch_ready_pick_task(request_id="dispatch-safe-draft")
        payload = self._request_dispatch_handoff(task, request_id="dispatch-safe-response")

        payload_text = str(payload).lower()
        self.assertEqual(payload["valuation"], {"visible": False, "fields": []})
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("amount", payload_text)
        self.assertNotIn("tax", payload_text)
        self.assertNotIn("account", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertNotIn("/desk/form", payload_text)
        self.assertFalse(payload["stock_effect"])
        self.assertFalse(payload["delivery_note_created"])
        self.assertFalse(payload["delivery_note_submitted"])
        self.assertFalse(payload["pick_list_created"])
        self.assertFalse(payload["stock_reserved"])
        self.assertFalse(payload["stock_posted"])
        self.assertFalse(payload["sales_order_updated"])
        self.assertFalse(payload["customer_notified"])
        forbidden_docs = {"Delivery Note", "Pick List", "Stock Reservation Entry", "Stock Entry", "Stock Ledger Entry"}
        self.assertFalse(any(call["doctype"] in forbidden_docs for call in GET_DOC_CALLS))
        self.assertFalse(any(call["doctype"] in forbidden_docs for call in GET_ALL_CALLS))

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
        transfer = service.get_warehouse_transfer_visibility_queue("transfer_visibility")
        movement_detail = service.get_warehouse_movement_review(
            service._movement_review_context_token("MAT-MOV-0001")
        )

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
        self.assertEqual(transfer["state"]["kind"], "restricted")
        self.assertEqual(transfer["rows"], [])
        self.assertEqual(movement_detail["state"]["kind"], "restricted")
        self.assertEqual(movement_detail["line_groups"], [])

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
        transfer = service.get_warehouse_transfer_visibility_queue("transfer_visibility")
        movement_detail = service.get_warehouse_movement_review(
            service._movement_review_context_token("MAT-MOV-0001")
        )

        self.assertEqual(movement["state"]["kind"], "restricted")
        self.assertEqual(transfer["state"]["kind"], "restricted")
        self.assertEqual(movement["rows"], [])
        self.assertEqual(movement_detail["state"]["kind"], "restricted")
        self.assertEqual(movement_detail["line_groups"], [])
        self.assertFalse(any(call["doctype"] == "Stock Entry" for call in LIST_CALLS))


    def _save_customer_return_intake(self, **overrides):
        payload = {
            "customer": "CUST-RET-001",
            "warehouse": "Main - M",
            "return_authorization_reference": "RMA-001",
            "sales_order_reference_text": "SO-TODAY",
            "delivery_note_reference_text": "DN-TEXT-001",
            "source_reference_note": "Sales approved return intake.",
            "lines": [
                {
                    "item_code": "ITEM-102",
                    "item_name": "Screen Guard",
                    "warehouse": "Main - M",
                    "returned_qty": 2,
                    "accepted_qty": 2,
                    "condition_grade": "Good",
                    "disposition": "Restock candidate",
                    "uom": "Nos",
                }
            ],
            "notes": "Received at returns bench.",
            "request_id": "return-intake-001",
        }
        payload.update(overrides)
        return service.save_warehouse_customer_return_intake_draft(**payload)

    def test_w15e3_warehouse_and_stock_users_can_save_customer_return_intake_draft(self):
        payload = self._save_customer_return_intake()

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["page"]["key"], "customer_return_intake_draft")
        self.assertEqual(payload["intake"]["customer"], "CUST-RET-001")
        self.assertEqual(payload["intake"]["warehouse"], "Main - M")
        self.assertEqual(payload["intake"]["line_count"], 1)
        self.assertFalse(payload["stock_effect"])
        self.assertFalse(payload["stock_increased"])
        self.assertFalse(payload["sales_return_created"])
        self.assertFalse(payload["credit_note_created"])
        self.assertFalse(payload["delivery_note_created"])
        self.assertFalse(payload["stock_entry_created"])
        self.assertFalse(payload["stock_posted"])
        self.assertFalse(payload["sales_order_updated"])
        self.assertFalse(payload["customer_notified"])
        self.assertEqual(payload["valuation"], {"visible": False, "fields": []})
        self.assertEqual(len(CUSTOMER_RETURN_INTAKE_DOCS), 1)
        intake = next(iter(CUSTOMER_RETURN_INTAKE_DOCS.values()))
        self.assertEqual(intake.policy_version, service.CUSTOMER_RETURN_INTAKE_POLICY_VERSION)
        self.assertEqual(intake.request_id, "return-intake-001")
        self.assertEqual(intake.total_returned_qty, 2.0)
        self.assertEqual(len(intake.lines), 1)
        self.assertEqual(intake.lines[0]["item_code"], "ITEM-102")
        self.assertEqual(len(intake.events), 1)
        self.assertEqual(intake.events[0]["event_type"], "saved_customer_return_intake_draft")

        CUSTOMER_RETURN_INTAKE_DOCS.clear()
        CURRENT_ROLES[:] = ["Stock User"]
        stock_payload = self._save_customer_return_intake(request_id="return-stock-user")
        self.assertEqual(stock_payload["state"]["kind"], "ready")
        self.assertEqual(len(CUSTOMER_RETURN_INTAKE_DOCS), 1)

    def test_w15e3_non_warehouse_user_denied_customer_return_intake(self):
        CURRENT_ROLES[:] = ["Sales User"]
        with self.assertRaises(Exception):
            self._save_customer_return_intake(request_id="return-denied")
        self.assertEqual(CUSTOMER_RETURN_INTAKE_DOCS, {})

    def test_w15e3_missing_customer_authorization_or_visible_warehouse_rejected(self):
        with self.assertRaises(Exception):
            self._save_customer_return_intake(customer="", request_id="return-missing-customer")
        with self.assertRaises(Exception):
            self._save_customer_return_intake(return_authorization_reference="", request_id="return-missing-rma")
        with self.assertRaises(Exception):
            self._save_customer_return_intake(warehouse="Unknown - M", request_id="return-unknown-warehouse")
        self.assertEqual(CUSTOMER_RETURN_INTAKE_DOCS, {})

    def test_w15e3_customer_return_line_validation(self):
        with self.assertRaises(Exception):
            self._save_customer_return_intake(lines=[], request_id="return-missing-lines")
        with self.assertRaises(Exception):
            self._save_customer_return_intake(lines=[{"warehouse": "Main - M", "returned_qty": 1, "condition_grade": "Good"}], request_id="return-missing-item")
        with self.assertRaises(Exception):
            self._save_customer_return_intake(lines=[{"item_code": "ITEM-102", "warehouse": "Main - M", "returned_qty": 0, "condition_grade": "Good"}], request_id="return-zero-qty")
        with self.assertRaises(Exception):
            self._save_customer_return_intake(lines=[{"item_code": "ITEM-102", "warehouse": "Main - M", "returned_qty": 1, "accepted_qty": -1, "condition_grade": "Good"}], request_id="return-negative-qty")
        with self.assertRaises(Exception):
            self._save_customer_return_intake(lines=[{"item_code": "ITEM-102", "warehouse": "Main - M", "returned_qty": 2, "accepted_qty": 2, "damaged_qty": 1, "condition_grade": "Good"}], request_id="return-over-sum")
        with self.assertRaises(Exception):
            self._save_customer_return_intake(lines=[{"item_code": "ITEM-102", "warehouse": "Main - M", "returned_qty": 1}], request_id="return-missing-condition")
        self.assertEqual(CUSTOMER_RETURN_INTAKE_DOCS, {})

    def test_w15e3_exception_quantities_require_evidence_or_condition_note(self):
        with self.assertRaises(Exception):
            self._save_customer_return_intake(
                lines=[{"item_code": "ITEM-102", "warehouse": "Main - M", "returned_qty": 2, "accepted_qty": 1, "damaged_qty": 1, "condition_grade": "Damaged"}],
                request_id="return-damaged-no-evidence",
            )
        payload = self._save_customer_return_intake(
            lines=[{"item_code": "ITEM-102", "warehouse": "Main - M", "returned_qty": 2, "accepted_qty": 1, "damaged_qty": 1, "condition_grade": "Damaged", "evidence_reference": "RET-PHOTO-1"}],
            request_id="return-damaged-evidence",
        )
        self.assertEqual(payload["state"]["kind"], "ready")
        intake = next(iter(CUSTOMER_RETURN_INTAKE_DOCS.values()))
        self.assertEqual(intake.lines[0]["evidence_reference"], "RET-PHOTO-1")

    def test_w15e3_request_idempotency_and_changed_payload_rejection(self):
        first = self._save_customer_return_intake(request_id="return-same-request")
        second = self._save_customer_return_intake(request_id="return-same-request")

        self.assertFalse(first["intake"]["idempotent"])
        self.assertTrue(second["intake"]["idempotent"])
        self.assertEqual(first["intake"]["intake_id"], second["intake"]["intake_id"])
        self.assertEqual(len(CUSTOMER_RETURN_INTAKE_DOCS), 1)
        intake = next(iter(CUSTOMER_RETURN_INTAKE_DOCS.values()))
        self.assertEqual(len(intake.events), 1)

        with self.assertRaises(Exception):
            self._save_customer_return_intake(notes="Changed note.", request_id="return-same-request")

    def test_w15e3_request_id_cannot_cross_customer_or_warehouse(self):
        self._save_customer_return_intake(request_id="return-cross-request")
        with self.assertRaises(Exception):
            self._save_customer_return_intake(customer="CUST-RET-002", request_id="return-cross-request")
        with self.assertRaises(Exception):
            self._save_customer_return_intake(warehouse="Short - M", lines=[{"item_code": "ITEM-105", "warehouse": "Short - M", "returned_qty": 1, "accepted_qty": 1, "condition_grade": "Good"}], request_id="return-cross-request")
        self.assertEqual(len(CUSTOMER_RETURN_INTAKE_DOCS), 1)

    def test_w15e3_forbidden_fields_and_safe_payload_boundaries(self):
        with self.assertRaises(Exception):
            self._save_customer_return_intake(sales_return="SR-0001", request_id="return-forbidden-sales-return")
        self.assertEqual(CUSTOMER_RETURN_INTAKE_DOCS, {})

        payload = self._save_customer_return_intake(request_id="return-safe-response")
        payload_text = str(payload).lower()
        self.assertEqual(payload["valuation"], {"visible": False, "fields": []})
        self.assertNotIn("valuation_rate", payload_text)
        self.assertNotIn("stock_value", payload_text)
        self.assertNotIn("amount", payload_text)
        self.assertNotIn("tax", payload_text)
        self.assertNotIn("account", payload_text)
        self.assertNotIn("/app/", payload_text)
        self.assertNotIn("/desk/form", payload_text)
        self.assertFalse(payload["stock_effect"])
        self.assertFalse(payload["stock_increased"])
        self.assertFalse(payload["sales_return_created"])
        self.assertFalse(payload["credit_note_created"])
        self.assertFalse(payload["delivery_note_created"])
        self.assertFalse(payload["stock_entry_created"])
        self.assertFalse(payload["stock_posted"])
        self.assertFalse(payload["sales_order_updated"])
        self.assertFalse(payload["customer_notified"])
        forbidden_docs = {"Sales Return", "Credit Note", "Delivery Note", "Stock Entry", "Stock Ledger Entry", "Stock Reconciliation", "Sales Order"}
        self.assertFalse(any(call["doctype"] in forbidden_docs for call in GET_DOC_CALLS))
        self.assertFalse(any(call["doctype"] in forbidden_docs for call in GET_ALL_CALLS))


if __name__ == "__main__":
    unittest.main()
