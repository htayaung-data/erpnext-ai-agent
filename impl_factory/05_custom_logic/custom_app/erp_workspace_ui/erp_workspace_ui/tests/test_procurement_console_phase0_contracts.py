import sys
import types
import unittest
from datetime import date


fake_frappe = types.ModuleType("frappe")
CURRENT_ROLES = []
READABLE_DOCTYPES = {
    "Supplier",
    "Item",
    "Item Price",
    "Warehouse",
    "Company",
    "Material Request",
    "Purchase Order",
    "Purchase Receipt",
    "Purchase Invoice",
    "Request for Quotation",
    "Supplier Quotation",
    "Procurement Supplier Readiness Profile",
    "Procurement Supplier Readiness Log",
    "Procurement Item Buying Profile",
    "Procurement Item Buying Log",
}
WRITEABLE_DOCTYPES = set()
CREATEABLE_DOCTYPES = set()
CAPTURED_GET_LIST_CALLS = []
CAPTURED_GET_ALL_CALLS = []
CAPTURED_REPORT_CALLS = []
EMAIL_ACCOUNTS = []
EMAIL_ACCOUNT_GET_ALL_RAISES = False
HAS_QUOTE_STATUS = True
HIDDEN_PURCHASE_ORDER_LIST_NAMES = set()
HIDDEN_MATERIAL_REQUEST_LIST_NAMES = set()
HIDDEN_RFQ_LIST_NAMES = set()
HIDDEN_SUPPLIER_QUOTATION_LIST_NAMES = set()
MISSING_NATIVE_REPORTS = set()
MISSING_FIELDS = set()
SAVED_MATERIAL_REQUESTS = {}
SAVED_RFQS = {}
SAVED_SUPPLIER_QUOTATIONS = {}
SAVED_PURCHASE_ORDERS = {}
SUPPLIER_READINESS_PROFILES = {}
SUPPLIER_READINESS_LOGS = []
ITEM_BUYING_PROFILES = {}
ITEM_BUYING_LOGS = []


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
    if ptype == "read":
        return doctype in READABLE_DOCTYPES
    if ptype == "write":
        return doctype in WRITEABLE_DOCTYPES
    if ptype == "create":
        return doctype in CREATEABLE_DOCTYPES
    return False


def _count(doctype, filters=None):
    return 3 if doctype in READABLE_DOCTYPES else 0


def _filter_rows(doctype, rows, filters):
    if not filters:
        return rows
    if isinstance(filters, dict):
        filtered = list(rows)
        for fieldname, value in filters.items():
            if isinstance(value, (list, tuple)) and len(value) == 2 and value[0] == "in":
                filtered = [row for row in filtered if row.get(fieldname) in set(value[1] or [])]
            else:
                filtered = [row for row in filtered if row.get(fieldname) == value]
        return filtered
    filtered = list(rows)
    for condition in filters:
        if not isinstance(condition, (list, tuple)) or len(condition) < 4:
            continue
        condition_doctype, fieldname, operator, value = condition[:4]
        if condition_doctype != doctype:
            continue
        if operator == "=":
            filtered = [row for row in filtered if row.get(fieldname) == value]
        elif operator == ">":
            filtered = [row for row in filtered if float(row.get(fieldname) or 0) > float(value or 0)]
        elif operator == "<":
            filtered = [row for row in filtered if float(row.get(fieldname) or 0) < float(value or 0)]
        elif operator == ">=":
            filtered = [row for row in filtered if str(row.get(fieldname) or "") >= str(value)]
        elif operator == "<=":
            filtered = [row for row in filtered if str(row.get(fieldname) or "") <= str(value)]
        elif operator == "not in":
            filtered = [row for row in filtered if row.get(fieldname) not in set(value or [])]
        elif operator == "in":
            filtered = [row for row in filtered if row.get(fieldname) in set(value or [])]
        elif operator == "like":
            needle = str(value or "").strip("%").lower()
            filtered = [row for row in filtered if needle in str(row.get(fieldname) or "").lower()]
    return filtered


def _purchase_order_rows():
    return [
        {
            "name": "PUR-DUE-001",
            "supplier": "SUP-001",
            "supplier_name": "Alpha Supplier",
            "company": "Demo Company",
            "transaction_date": "2026-05-02",
            "schedule_date": "2026-06-01",
            "status": "To Receive and Bill",
            "workflow_state": "Pending Purchase Approval",
            "docstatus": 1,
            "per_received": 0,
            "per_billed": 0,
            "grand_total": 1000,
            "currency": "MMK",
            "modified": "2026-05-03",
        },
        {
            "name": "PUR-OVERDUE-001",
            "supplier": "SUP-001",
            "supplier_name": "Alpha Supplier",
            "company": "Demo Company",
            "transaction_date": "2026-04-20",
            "schedule_date": "2026-04-30",
            "status": "To Receive and Bill",
            "workflow_state": "Approved",
            "docstatus": 1,
            "per_received": 0,
            "per_billed": 0,
            "grand_total": 2200,
            "currency": "MMK",
            "modified": "2026-05-03",
        },
        {
            "name": "PUR-PARTIAL-001",
            "supplier": "SUP-002",
            "supplier_name": "Beta Supplier",
            "company": "Demo Company",
            "transaction_date": "2026-05-01",
            "schedule_date": "2026-05-20",
            "status": "To Receive and Bill",
            "workflow_state": "Approved",
            "docstatus": 1,
            "per_received": 50,
            "per_billed": 20,
            "grand_total": 3000,
            "currency": "MMK",
            "modified": "2026-05-03",
        },
        {
            "name": "PUR-BILLING-001",
            "supplier": "SUP-003",
            "supplier_name": "Gamma Supplier",
            "company": "Demo Company",
            "transaction_date": "2026-05-01",
            "schedule_date": "2026-05-12",
            "status": "To Bill",
            "workflow_state": "Approved",
            "docstatus": 1,
            "per_received": 100,
            "per_billed": 40,
            "grand_total": 4000,
            "currency": "MMK",
            "modified": "2026-05-03",
        },
    ]


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
    if doctype == "Email Account":
        return _filter_rows(doctype, list(EMAIL_ACCOUNTS), filters)
    if doctype == "Supplier":
        return _filter_rows(doctype, [
            {
                "name": "SUP-001",
                "supplier_name": "Alpha Supplier",
                "supplier_group": "All Supplier Groups",
                "disabled": 0,
                "modified": "2026-05-03",
            }
        ], filters)
    if doctype == "Item":
        return _filter_rows(doctype, [
            {
                "name": "ITEM-001",
                "item_name": "Widget",
                "item_group": "Products",
                "stock_uom": "Nos",
                "disabled": 0,
                "is_purchase_item": 1,
                "has_variants": 0,
                "modified": "2026-05-03",
            },
			{
				"name": "ITEM-SOLD",
				"item_name": "Sold Widget",
				"item_group": "Sales Evidence",
				"stock_uom": "Nos",
				"disabled": 0,
				"is_purchase_item": 1,
				"has_variants": 0,
				"modified": "2026-05-03",
			},
			{
				"name": "ITEM-RECEIVED",
				"item_name": "Received Widget",
				"item_group": "Buying Evidence",
				"stock_uom": "Nos",
				"disabled": 0,
				"is_purchase_item": 1,
				"has_variants": 0,
				"modified": "2026-05-03",
			}
		], filters)
    if doctype == "Warehouse":
        return _filter_rows(doctype, [
            {"name": "Stores - DC", "warehouse_name": "Stores", "company": "Demo Company", "modified": "2026-05-03"}
        ], filters)
    if doctype == "Company":
        return [{"name": "Demo Company"}]
    if doctype == "Item Price":
        return _filter_rows(doctype, [
            {
                "name": "PRICE-001",
                "item_code": "ITEM-001",
                "price_list": "Standard Buying",
                "price_list_rate": 1000,
                "currency": "MMK",
                "valid_from": "2026-05-01",
                "valid_upto": "2026-05-31",
                "uom": "Nos",
                "supplier": "SUP-001",
                "buying": 1,
                "modified": "2026-05-03",
            },
            {
                "name": "PRICE-CATALOG-001",
                "item_code": "ITEM-CATALOG",
                "price_list": "Standard Buying",
                "price_list_rate": 500,
                "currency": "MMK",
                "uom": "Nos",
                "supplier": "SUP-001",
                "buying": 1,
                "modified": "2026-05-03",
            }
        ], filters)
    if doctype == "Material Request":
        rows = _filter_rows(doctype, [
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
        ], filters)
        return [row for row in rows if row["name"] not in HIDDEN_MATERIAL_REQUEST_LIST_NAMES]
    if doctype == "Purchase Order":
        rows = _filter_rows(doctype, _purchase_order_rows(), filters)
        return [row for row in rows if row["name"] not in HIDDEN_PURCHASE_ORDER_LIST_NAMES]
    if doctype == "Request for Quotation":
        rows = _filter_rows(doctype, [
            {
                "name": "RFQ-001",
                "company": "Demo Company",
                "transaction_date": "2026-05-02",
                "schedule_date": "2026-05-10",
                "status": "Submitted",
                "docstatus": 1,
                "modified": "2026-05-03",
            }
        ], filters)
        return [row for row in rows if row["name"] not in HIDDEN_RFQ_LIST_NAMES]
    if doctype == "Supplier Quotation":
        rows = _filter_rows(doctype, [
            {
                "name": "SUP-QTN-001",
                "supplier": "SUP-001",
                "supplier_name": "Alpha Supplier",
                "company": "Demo Company",
                "status": "Submitted",
                "transaction_date": "2026-05-02",
                "valid_till": "2026-05-08",
                "currency": "MMK",
                "grand_total": 1000,
                "docstatus": 1,
                "modified": "2026-05-03",
            }
        ], filters)
        return [row for row in rows if row["name"] not in HIDDEN_SUPPLIER_QUOTATION_LIST_NAMES]
    if doctype == "Contact":
        return _filter_rows(doctype, [
            {
                "name": "CONT-001",
                "first_name": "Buyer",
                "last_name": "Contact",
                "email_id": "buyer.contact@example.com",
                "phone": "012345",
                "mobile_no": "",
                "modified": "2026-05-03",
            }
        ], filters)
    return []


def _get_all(doctype, filters=None, fields=None, order_by=None, limit_page_length=None, **kwargs):
    CAPTURED_GET_ALL_CALLS.append(
        {
            "doctype": doctype,
            "filters": filters,
            "fields": fields,
            "order_by": order_by,
            "limit_page_length": limit_page_length,
        }
    )
    if doctype == "Email Account":
        if EMAIL_ACCOUNT_GET_ALL_RAISES:
            raise _FakePermissionError("Insufficient Permissions for Email Account")
        return _filter_rows(doctype, list(EMAIL_ACCOUNTS), filters)
    if doctype == "Procurement Supplier Readiness Profile":
        return _filter_rows(doctype, list(SUPPLIER_READINESS_PROFILES.values()), filters)
    if doctype == "Procurement Supplier Readiness Log":
        return _filter_rows(doctype, list(SUPPLIER_READINESS_LOGS), filters)
    if doctype == "Procurement Item Buying Profile":
        return _filter_rows(doctype, list(ITEM_BUYING_PROFILES.values()), filters)
    if doctype == "Procurement Item Buying Log":
        return _filter_rows(doctype, list(ITEM_BUYING_LOGS), filters)
    if doctype == "Request for Quotation Supplier":
        return _filter_rows(doctype, [
            {"parent": "RFQ-001", "supplier": "SUP-001", "supplier_name": "Alpha Supplier", "quote_status": "Pending"},
            {"parent": "RFQ-001", "supplier": "SUP-002", "supplier_name": "Beta Supplier", "quote_status": "Received"},
            {"parent": "RFQ-002", "supplier": "SUP-003", "supplier_name": "Gamma Supplier", "quote_status": "Pending"},
        ], filters)
    if doctype == "Dynamic Link":
        if isinstance(filters, dict) and filters.get("link_doctype") == "Supplier" and filters.get("link_name") == "SUP-001":
            return [{"parent": "CONT-001"}]
        return []
    if doctype == "Item Supplier":
        rows = [
            {
                "name": "ITEM-SUP-001",
                "parent": "ITEM-001",
                "supplier": "SUP-001",
                "supplier_part_no": "SUP-WIDGET-001",
                "lead_time_days": 5,
                "modified": "2026-05-03",
            },
            {
                "name": "ITEM-SUP-CATALOG-001",
                "parent": "ITEM-CATALOG",
                "supplier": "SUP-001",
                "supplier_part_no": "SUP-CATALOG-001",
                "lead_time_days": 7,
                "modified": "2026-05-03",
            },
        ]
        return _filter_rows(doctype, rows, filters)
    if doctype == "Material Request Item":
        return _filter_rows(doctype, [
            {
                "name": "MRI-001",
                "parent": "MAT-MR-001",
                "item_code": "ITEM-001",
                "item_name": "Widget",
                "qty": 5,
                "ordered_qty": 1,
                "received_qty": 0,
                "uom": "Nos",
                "schedule_date": "2026-05-10",
                "warehouse": "Stores - DC",
            }
        ], filters)
    if doctype == "Request for Quotation Item":
        return _filter_rows(doctype, [
            {
                "name": "RFQI-001",
                "parent": "RFQ-001",
                "item_code": "ITEM-001",
                "item_name": "Widget",
                "qty": 5,
                "uom": "Nos",
                "schedule_date": "2026-05-10",
                "warehouse": "Stores - DC",
                "material_request": "MAT-MR-001",
            }
        ], filters)
    if doctype == "Supplier Quotation Item":
        return _filter_rows(doctype, [
            {
                "name": "SQI-001",
                "parent": "SUP-QTN-001",
                "item_code": "ITEM-001",
                "item_name": "Widget",
                "qty": 5,
                "uom": "Nos",
                "rate": 200,
                "amount": 1000,
                "request_for_quotation": "RFQ-001",
                "material_request": "MAT-MR-001",
            }
        ], filters)
    if doctype == "Purchase Order Item":
        rows = [
            {
                "name": "POI-DUE-001",
                "parent": "PUR-DUE-001",
                "item_code": "ITEM-001",
                "item_name": "Widget",
                "schedule_date": "2026-05-08",
                "expected_delivery_date": "2026-05-06",
                "qty": 10,
                "uom": "Nos",
                "rate": 100,
                "amount": 1000,
                "base_rate": 100,
                "base_amount": 1000,
                "item_group": "Products",
                "received_qty": 0,
                "warehouse": "Stores - DC",
                "material_request": "MAT-MR-001",
                "material_request_item": "MRI-001",
                "supplier_quotation": "SUP-QTN-001",
            },
            {
                "name": "POI-OVERDUE-001",
                "parent": "PUR-OVERDUE-001",
                "item_code": "ITEM-002",
                "item_name": "Overdue Widget",
                "schedule_date": "2026-04-30",
                "expected_delivery_date": "",
                "qty": 5,
                "uom": "Nos",
                "rate": 440,
                "amount": 2200,
                "base_rate": 440,
                "base_amount": 2200,
                "item_group": "Products",
                "received_qty": 0,
                "warehouse": "Stores - DC",
                "material_request": "MAT-MR-002",
                "material_request_item": "MRI-002",
                "supplier_quotation": "SUP-QTN-002",
            },
            {
                "name": "POI-PARTIAL-001",
                "parent": "PUR-PARTIAL-001",
                "item_code": "ITEM-003",
                "item_name": "Partial Widget",
                "schedule_date": "2026-05-20",
                "expected_delivery_date": "",
                "qty": 8,
                "uom": "Nos",
                "rate": 375,
                "amount": 3000,
                "base_rate": 375,
                "base_amount": 3000,
                "item_group": "Products",
                "received_qty": 4,
                "warehouse": "Stores - DC",
                "material_request": "MAT-MR-003",
                "material_request_item": "MRI-003",
                "supplier_quotation": "SUP-QTN-003",
            },
            {
                "name": "POI-BILLING-001",
                "parent": "PUR-BILLING-001",
                "item_code": "ITEM-004",
                "item_name": "Billing Widget",
                "schedule_date": "2026-05-12",
                "expected_delivery_date": "",
                "qty": 6,
                "uom": "Nos",
                "rate": 666.67,
                "amount": 4000,
                "base_rate": 666.67,
                "base_amount": 4000,
                "item_group": "Products",
                "received_qty": 6,
                "warehouse": "Stores - DC",
                "material_request": "MAT-MR-004",
                "material_request_item": "MRI-004",
                "supplier_quotation": "SUP-QTN-004",
            },
        ]
        return _filter_rows(doctype, rows, filters)
    if doctype == "Purchase Receipt Item":
        return _filter_rows(doctype, [
            {
                "parent": "MAT-PRE-001",
                "item_code": "ITEM-003",
                "qty": 4,
                "received_qty": 4,
                "rejected_qty": 0,
                "warehouse": "Stores - DC",
                "billed_amt": 500,
            },
            {
                "parent": "MAT-PRE-002",
                "item_code": "ITEM-RECEIVED",
                "qty": 2,
                "received_qty": 2,
                "rejected_qty": 0,
                "warehouse": "Stores - DC",
                "billed_amt": 250,
            }
        ], filters)
    if doctype == "Purchase Invoice Item":
        return _filter_rows(doctype, [
            {
                "parent": "ACC-PINV-001",
                "item_code": "ITEM-003",
                "qty": 2,
                "amount": 500,
                "purchase_receipt": "MAT-PRE-001",
            },
            {
                "parent": "ACC-PINV-002",
                "item_code": "ITEM-RECEIVED",
                "qty": 2,
                "amount": 250,
                "purchase_receipt": "MAT-PRE-002",
            }
        ], filters)
    if doctype == "Sales Order Item":
        return _filter_rows(doctype, [
            {
                "parent": "SAL-ORD-001",
                "item_code": "ITEM-SOLD",
                "item_name": "Sold Widget",
                "qty": 1,
                "docstatus": 1,
            }
        ], filters)
    if doctype == "Delivery Note Item":
        return _filter_rows(doctype, [
            {
                "parent": "MAT-DN-001",
                "item_code": "ITEM-SOLD",
                "item_name": "Sold Widget",
                "qty": 1,
                "docstatus": 1,
            }
        ], filters)
    if doctype == "Sales Invoice Item":
        return _filter_rows(doctype, [
            {
                "parent": "ACC-SINV-001",
                "item_code": "ITEM-SOLD",
                "item_name": "Sold Widget",
                "qty": 1,
                "docstatus": 1,
            }
        ], filters)
    return []


def _db_get_value(doctype, name=None, fieldname=None, as_dict=False, **kwargs):
    if doctype == "Contact" and name == "CONT-001":
        row = {"name": "CONT-001", "first_name": "Buyer", "last_name": "Contact", "email_id": "buyer.contact@example.com"}
        if as_dict:
            if isinstance(fieldname, (list, tuple)):
                return {field: row.get(field) for field in fieldname}
            return dict(row)
        if isinstance(fieldname, (list, tuple)):
            return tuple(row.get(field) for field in fieldname)
        return row.get(fieldname)
    if doctype == "Supplier" and name == "SUP-EMAIL":
        row = {"name": "SUP-EMAIL", "email_id": "direct.supplier@example.com"}
        if as_dict:
            if isinstance(fieldname, (list, tuple)):
                return {field: row.get(field) for field in fieldname}
            return dict(row)
        if isinstance(fieldname, (list, tuple)):
            return tuple(row.get(field) for field in fieldname)
        return row.get(fieldname)
    if doctype == "Company" and name == "Demo Company":
        if as_dict:
            return {"name": "Demo Company", "default_currency": "MMK"}
        if isinstance(fieldname, (list, tuple)):
            return tuple("MMK" if field == "default_currency" else "Demo Company" if field == "name" else None for field in fieldname)
        if fieldname == "default_currency":
            return "MMK"
        if fieldname == "name":
            return "Demo Company"
    if doctype == "Purchase Order" and name:
        rows = _filter_rows("Purchase Order", _purchase_order_rows(), [["Purchase Order", "name", "=", name]])
        if not rows:
            return None
        row = rows[0]
        if as_dict:
            if isinstance(fieldname, (list, tuple)):
                return {field: row.get(field) for field in fieldname}
            return dict(row)
        if isinstance(fieldname, (list, tuple)):
            return tuple(row.get(field) for field in fieldname)
        return row.get(fieldname)
    return None


class _FakeMeta:
    def __init__(self, doctype):
        self.doctype = doctype

    def has_field(self, fieldname):
        if (self.doctype, fieldname) in MISSING_FIELDS:
            return False
        if self.doctype == "Request for Quotation Supplier" and fieldname == "quote_status":
            return HAS_QUOTE_STATUS
        return True




class _FakeChildDoc:
    def __init__(self, values=None):
        for key, value in dict(values or {}).items():
            setattr(self, key, value)


class _FakeMaterialRequestDoc:
    def __init__(self, name=None, values=None):
        values = dict(values or {})
        self.doctype = "Material Request"
        self.name = name or values.get("name") or ""
        self.material_request_type = values.get("material_request_type") or "Purchase"
        self.transaction_date = values.get("transaction_date") or "2026-05-03"
        self.schedule_date = values.get("schedule_date") or ""
        self.company = values.get("company") or "Demo Company"
        self.docstatus = values.get("docstatus", 0)
        self.items = [child if isinstance(child, _FakeChildDoc) else _FakeChildDoc(child) for child in values.get("items", [])]

    def set(self, fieldname, value):
        setattr(self, fieldname, value)

    def update_supplier_part_no(self, supplier):
        self.vendor = supplier
        for item in self.items:
            item.supplier_part_no = f"{supplier}-{getattr(item, 'item_code', '')}".strip("-")

    def append(self, fieldname, value):
        if not hasattr(self, fieldname):
            setattr(self, fieldname, [])
        getattr(self, fieldname).append(_FakeChildDoc(value))

    def check_permission(self, ptype):
        if not _has_permission("Material Request", ptype):
            raise _FakePermissionError("No permission")

    def insert(self):
        self.check_permission("create")
        if not self.name:
            self.name = "MAT-MR-DRAFT-001"
        self.docstatus = 0
        SAVED_MATERIAL_REQUESTS[self.name] = self
        return self

    def save(self):
        self.check_permission("write")
        SAVED_MATERIAL_REQUESTS[self.name] = self
        return self

class _FakeRFQDoc:
    def __init__(self, name=None, values=None):
        values = dict(values or {})
        self.doctype = "Request for Quotation"
        self.name = name or values.get("name") or ""
        self.transaction_date = values.get("transaction_date") or "2026-05-03"
        self.schedule_date = values.get("schedule_date") or ""
        self.company = values.get("company") or "Demo Company"
        self.subject = values.get("subject") or "Request for Quotation"
        self.message_for_supplier = values.get("message_for_supplier") or "Please supply the specified items at the best possible rates"
        self.docstatus = values.get("docstatus", 0)
        self.suppliers = [child if isinstance(child, _FakeChildDoc) else _FakeChildDoc(child) for child in values.get("suppliers", [])]
        self.items = [child if isinstance(child, _FakeChildDoc) else _FakeChildDoc(child) for child in values.get("items", [])]

    def set(self, fieldname, value):
        setattr(self, fieldname, value)

    def append(self, fieldname, value):
        if not hasattr(self, fieldname):
            setattr(self, fieldname, [])
        getattr(self, fieldname).append(_FakeChildDoc(value))

    def check_permission(self, ptype):
        if not _has_permission("Request for Quotation", ptype):
            raise _FakePermissionError("No permission")

    def insert(self):
        self.check_permission("create")
        if not self.name:
            self.name = "PUR-RFQ-DRAFT-001"
        self.docstatus = 0
        SAVED_RFQS[self.name] = self
        return self

    def save(self):
        self.check_permission("write")
        SAVED_RFQS[self.name] = self
        return self


class _FakeSupplierQuotationDoc:
    def __init__(self, name=None, values=None):
        values = dict(values or {})
        self.doctype = "Supplier Quotation"
        self.name = name or values.get("name") or ""
        self.supplier = values.get("supplier") or ""
        self.transaction_date = values.get("transaction_date") or "2026-05-03"
        self.valid_till = values.get("valid_till") or ""
        self.company = values.get("company") or "Demo Company"
        self.currency = values.get("currency") or "MMK"
        self.conversion_rate = values.get("conversion_rate", 1)
        self.docstatus = values.get("docstatus", 0)
        self.items = [child if isinstance(child, _FakeChildDoc) else _FakeChildDoc(child) for child in values.get("items", [])]

    def set(self, fieldname, value):
        setattr(self, fieldname, value)

    def append(self, fieldname, value):
        if not hasattr(self, fieldname):
            setattr(self, fieldname, [])
        getattr(self, fieldname).append(_FakeChildDoc(value))

    def check_permission(self, ptype):
        if not _has_permission("Supplier Quotation", ptype):
            raise _FakePermissionError("No permission")

    def insert(self):
        self.check_permission("create")
        if not self.name:
            self.name = "SUP-QTN-DRAFT-001"
        self.docstatus = 0
        SAVED_SUPPLIER_QUOTATIONS[self.name] = self
        return self

    def save(self):
        self.check_permission("write")
        SAVED_SUPPLIER_QUOTATIONS[self.name] = self
        return self



class _FakePurchaseOrderDoc:
    def __init__(self, name=None, values=None):
        values = dict(values or {})
        self.doctype = "Purchase Order"
        self.name = name or values.get("name") or ""
        self.supplier = values.get("supplier") or ""
        self.transaction_date = values.get("transaction_date") or "2026-05-03"
        self.schedule_date = values.get("schedule_date") or ""
        self.set_warehouse = values.get("set_warehouse") or ""
        self.buying_price_list = values.get("buying_price_list") or ""
        self.company = values.get("company") or "Demo Company"
        self.currency = values.get("currency") or "MMK"
        self.conversion_rate = values.get("conversion_rate", 1)
        self.docstatus = values.get("docstatus", 0)
        self.items = [child if isinstance(child, _FakeChildDoc) else _FakeChildDoc(child) for child in values.get("items", [])]

    def set(self, fieldname, value):
        setattr(self, fieldname, value)

    def append(self, fieldname, value):
        if not hasattr(self, fieldname):
            setattr(self, fieldname, [])
        getattr(self, fieldname).append(_FakeChildDoc(value))

    def check_permission(self, ptype):
        if not _has_permission("Purchase Order", ptype):
            raise _FakePermissionError("No permission")

    def insert(self):
        self.check_permission("create")
        if not self.name:
            self.name = "PUR-ORD-DRAFT-001"
        self.docstatus = 0
        SAVED_PURCHASE_ORDERS[self.name] = self
        return self

    def save(self):
        self.check_permission("write")
        SAVED_PURCHASE_ORDERS[self.name] = self
        return self


class _FakeReadinessProfileDoc:
    def __init__(self, name=None, values=None):
        values = dict(values or {})
        self.doctype = "Procurement Supplier Readiness Profile"
        self.name = name or values.get("name") or values.get("supplier") or ""
        self.supplier = values.get("supplier") or self.name
        self.buying_readiness_status = values.get("buying_readiness_status") or "Ready"
        self.preferred_rfq_contact = values.get("preferred_rfq_contact") or ""
        self.rfq_recipient_email_override = values.get("rfq_recipient_email_override") or ""
        self.buying_note = values.get("buying_note") or ""
        self.readiness_note = values.get("readiness_note") or ""
        self.modified = values.get("modified") or "2026-05-03 00:00:00"
        self.modified_by = values.get("modified_by") or fake_frappe.session.user
        self.owner = values.get("owner") or fake_frappe.session.user

    def _row(self):
        return {
            "name": self.name,
            "supplier": self.supplier,
            "buying_readiness_status": self.buying_readiness_status,
            "preferred_rfq_contact": self.preferred_rfq_contact,
            "rfq_recipient_email_override": self.rfq_recipient_email_override,
            "buying_note": self.buying_note,
            "readiness_note": self.readiness_note,
            "modified": self.modified,
            "modified_by": self.modified_by,
            "owner": self.owner,
        }

    def insert(self, ignore_permissions=False):
        if not self.name:
            self.name = self.supplier
        SUPPLIER_READINESS_PROFILES[self.supplier] = self._row()
        return self

    def save(self, ignore_permissions=False):
        if not self.name:
            self.name = self.supplier
        SUPPLIER_READINESS_PROFILES[self.supplier] = self._row()
        return self


class _FakeReadinessLogDoc:
    def __init__(self, values=None):
        values = dict(values or {})
        self.doctype = "Procurement Supplier Readiness Log"
        self.name = values.get("name") or f"LOG-{len(SUPPLIER_READINESS_LOGS) + 1:03d}"
        for key, value in values.items():
            setattr(self, key, value)

    def insert(self, ignore_permissions=False):
        SUPPLIER_READINESS_LOGS.append(dict(self.__dict__))
        return self


class _FakeItemBuyingProfileDoc:
    def __init__(self, name=None, values=None):
        values = dict(values or {})
        self.doctype = "Procurement Item Buying Profile"
        self.name = name or values.get("name") or values.get("item_code") or ""
        self.item_code = values.get("item_code") or self.name
        self.buying_readiness_status = values.get("buying_readiness_status") or "Not reviewed"
        self.preferred_existing_supplier = values.get("preferred_existing_supplier") or ""
        self.supplier_part_no_context = values.get("supplier_part_no_context") or ""
        self.procurement_lead_time_days = values.get("procurement_lead_time_days") if values.get("procurement_lead_time_days") not in (None, "") else ""
        self.minimum_order_qty_context = values.get("minimum_order_qty_context") if values.get("minimum_order_qty_context") not in (None, "") else ""
        self.buying_note = values.get("buying_note") or ""
        self.readiness_note = values.get("readiness_note") or ""
        self.last_context_update_by = values.get("last_context_update_by") or fake_frappe.session.user
        self.last_context_update_at = values.get("last_context_update_at") or "2026-05-03 00:00:00"
        self.modified = values.get("modified") or "2026-05-03 00:00:00"
        self.modified_by = values.get("modified_by") or fake_frappe.session.user
        self.owner = values.get("owner") or fake_frappe.session.user

    def _row(self):
        return {
            "name": self.name,
            "item_code": self.item_code,
            "buying_readiness_status": self.buying_readiness_status,
            "preferred_existing_supplier": self.preferred_existing_supplier,
            "supplier_part_no_context": self.supplier_part_no_context,
            "procurement_lead_time_days": self.procurement_lead_time_days,
            "minimum_order_qty_context": self.minimum_order_qty_context,
            "buying_note": self.buying_note,
            "readiness_note": self.readiness_note,
            "last_context_update_by": self.last_context_update_by,
            "last_context_update_at": self.last_context_update_at,
            "modified": self.modified,
            "modified_by": self.modified_by,
            "owner": self.owner,
        }

    def insert(self, ignore_permissions=False):
        if not self.name:
            self.name = self.item_code
        ITEM_BUYING_PROFILES[self.item_code] = self._row()
        return self

    def save(self, ignore_permissions=False):
        if not self.name:
            self.name = self.item_code
        ITEM_BUYING_PROFILES[self.item_code] = self._row()
        return self


class _FakeItemBuyingLogDoc:
    def __init__(self, values=None):
        values = dict(values or {})
        self.doctype = "Procurement Item Buying Log"
        self.name = values.get("name") or f"ITEM-LOG-{len(ITEM_BUYING_LOGS) + 1:03d}"
        for key, value in values.items():
            setattr(self, key, value)

    def insert(self, ignore_permissions=False):
        ITEM_BUYING_LOGS.append(dict(self.__dict__))
        return self


def _get_doc(*args, **kwargs):
    if args and isinstance(args[0], dict):
        doctype = args[0].get("doctype")
        if doctype == "Procurement Supplier Readiness Profile":
            return _FakeReadinessProfileDoc(values=args[0])
        if doctype == "Procurement Supplier Readiness Log":
            return _FakeReadinessLogDoc(values=args[0])
        if doctype == "Procurement Item Buying Profile":
            return _FakeItemBuyingProfileDoc(values=args[0])
        if doctype == "Procurement Item Buying Log":
            return _FakeItemBuyingLogDoc(values=args[0])
        if doctype == "Request for Quotation":
            return _FakeRFQDoc(values=args[0])
        if doctype == "Supplier Quotation":
            return _FakeSupplierQuotationDoc(values=args[0])
        if doctype == "Purchase Order":
            return _FakePurchaseOrderDoc(values=args[0])
        return _FakeMaterialRequestDoc(values=args[0])
    if len(args) >= 2 and args[0] == "Procurement Supplier Readiness Profile":
        name = args[1]
        row = next((row for row in SUPPLIER_READINESS_PROFILES.values() if row.get("name") == name or row.get("supplier") == name), None)
        if row:
            return _FakeReadinessProfileDoc(name=row.get("name"), values=row)
        raise Exception("Document not found")
    if len(args) >= 2 and args[0] == "Procurement Item Buying Profile":
        name = args[1]
        row = next((row for row in ITEM_BUYING_PROFILES.values() if row.get("name") == name or row.get("item_code") == name), None)
        if row:
            return _FakeItemBuyingProfileDoc(name=row.get("name"), values=row)
        raise Exception("Document not found")
    if len(args) >= 2 and args[0] == "Purchase Order":
        name = args[1]
        if name in SAVED_PURCHASE_ORDERS:
            return SAVED_PURCHASE_ORDERS[name]
        if name == "PUR-ORD-SUBMITTED":
            return _FakePurchaseOrderDoc(name=name, values={"docstatus": 1})
        if name == "PUR-DUE-001":
            return _FakePurchaseOrderDoc(name=name, values={
                "supplier": "SUP-001",
                "transaction_date": "2026-05-02",
                "schedule_date": "2026-05-20",
                "company": "Demo Company",
                "currency": "MMK",
                "items": [{"item_code": "ITEM-001", "qty": 5, "rate": 100, "amount": 500, "schedule_date": "2026-05-20", "warehouse": "Stores - DC", "uom": "Nos"}],
            })
    if len(args) >= 2 and args[0] == "Supplier Quotation":
        name = args[1]
        if name in SAVED_SUPPLIER_QUOTATIONS:
            return SAVED_SUPPLIER_QUOTATIONS[name]
        if name == "SUP-QTN-SUBMITTED":
            return _FakeSupplierQuotationDoc(name=name, values={"docstatus": 1})
        if name == "SUP-QTN-001":
            return _FakeSupplierQuotationDoc(name=name, values={
                "supplier": "SUP-001",
                "transaction_date": "2026-05-02",
                "valid_till": "2026-05-30",
                "company": "Demo Company",
                "currency": "MMK",
                "items": [{"item_code": "ITEM-001", "qty": 5, "rate": 100, "amount": 500, "uom": "Nos"}],
            })
    if len(args) >= 2 and args[0] == "Request for Quotation":
        name = args[1]
        if name in SAVED_RFQS:
            return SAVED_RFQS[name]
        if name == "PUR-RFQ-SUBMITTED":
            return _FakeRFQDoc(name=name, values={"docstatus": 1})
        if name == "PUR-RFQ-001":
            return _FakeRFQDoc(name=name, values={
                "transaction_date": "2026-05-02",
                "schedule_date": "2026-05-10",
                "company": "Demo Company",
                "suppliers": [{"supplier": "SUP-001"}],
                "items": [{"item_code": "ITEM-001", "qty": 5, "schedule_date": "2026-05-10", "warehouse": "Stores - DC", "uom": "Nos"}],
            })
        if name == "RFQ-001":
            return _FakeRFQDoc(name=name, values={
                "transaction_date": "2026-05-02",
                "schedule_date": "2026-05-10",
                "company": "Demo Company",
                "suppliers": [{"supplier": "SUP-001", "supplier_name": "Alpha Supplier"}, {"supplier": "SUP-002", "supplier_name": "Beta Supplier"}],
                "items": [{"item_code": "ITEM-001", "qty": 5, "schedule_date": "2026-05-10", "warehouse": "Stores - DC", "uom": "Nos"}],
            })
        if name == "PUR-RFQ-MULTI":
            return _FakeRFQDoc(name=name, values={
                "transaction_date": "2026-05-02",
                "schedule_date": "2026-05-10",
                "company": "Demo Company",
                "suppliers": [{"supplier": "SUP-001", "supplier_name": "Alpha Supplier"}, {"supplier": "SUP-002", "supplier_name": "Beta Supplier"}],
                "items": [{"item_code": "ITEM-001", "qty": 5, "schedule_date": "2026-05-10", "warehouse": "Stores - DC", "uom": "Nos"}],
            })
    if len(args) >= 2 and args[0] == "Material Request":
        name = args[1]
        if name in SAVED_MATERIAL_REQUESTS:
            return SAVED_MATERIAL_REQUESTS[name]
        if name == "MAT-MR-SUBMITTED":
            return _FakeMaterialRequestDoc(name=name, values={"docstatus": 1})
        if name == "MAT-MR-NONPUR":
            return _FakeMaterialRequestDoc(name=name, values={"material_request_type": "Material Transfer"})
        if name == "MAT-MR-001":
            return _FakeMaterialRequestDoc(name=name, values={
                "material_request_type": "Purchase",
                "transaction_date": "2026-05-02",
                "schedule_date": "2026-05-10",
                "company": "Demo Company",
                "items": [{"item_code": "ITEM-001", "qty": 5, "schedule_date": "2026-05-10", "warehouse": "Stores - DC", "uom": "Nos"}],
            })
    raise Exception("Document not found")

def _run_query_report(report_name, filters=None, ignore_prepared_report=None, **kwargs):
    CAPTURED_REPORT_CALLS.append(
        {
            "report_name": report_name,
            "filters": filters,
            "ignore_prepared_report": ignore_prepared_report,
        }
    )
    if report_name == "Purchase Order Analysis":
        return {
            "columns": [
                {"fieldname": "date", "label": "Date"},
                {"fieldname": "required_date", "label": "Required By"},
                {"fieldname": "purchase_order", "label": "Purchase Order"},
                {"fieldname": "status", "label": "Status"},
                {"fieldname": "supplier", "label": "Supplier"},
                {"fieldname": "project", "label": "Project"},
                {"fieldname": "item_code", "label": "Item Code"},
                {"fieldname": "qty", "label": "Qty"},
                {"fieldname": "received_qty", "label": "Received Qty"},
                {"fieldname": "pending_qty", "label": "Pending Qty"},
                {"fieldname": "billed_qty", "label": "Billed Qty"},
                {"fieldname": "qty_to_bill", "label": "Qty to Bill"},
                {"fieldname": "amount", "label": "Amount"},
                {"fieldname": "billed_amount", "label": "Billed Amount"},
                {"fieldname": "pending_amount", "label": "Pending Amount"},
                {"fieldname": "received_qty_amount", "label": "Received Qty Amount"},
                {"fieldname": "warehouse", "label": "Warehouse"},
                {"fieldname": "company", "label": "Company"},
                {"fieldname": "name", "label": "PO Item"},
            ],
            "result": [
                {
                    "date": "2026-04-20",
                    "required_date": "2026-04-30",
                    "purchase_order": "PUR-OVERDUE-001",
                    "status": "To Receive and Bill",
                    "supplier": "SUP-001",
                    "project": None,
                    "item_code": "ITEM-002",
                    "qty": 5,
                    "received_qty": 0,
                    "pending_qty": 5,
                    "billed_qty": 0,
                    "qty_to_bill": 5,
                    "amount": 2200,
                    "billed_amount": 0,
                    "pending_amount": 2200,
                    "received_qty_amount": 0,
                    "warehouse": "Stores - DC",
                    "company": "Demo Company",
                    "name": "POI-OVERDUE-001",
                },
                {
                    "date": "2026-05-01",
                    "required_date": "2026-05-20",
                    "purchase_order": "PUR-PARTIAL-001",
                    "status": "To Receive and Bill",
                    "supplier": "SUP-002",
                    "project": None,
                    "item_code": "ITEM-003",
                    "qty": 8,
                    "received_qty": 4,
                    "pending_qty": 4,
                    "billed_qty": 2,
                    "qty_to_bill": 6,
                    "amount": 3000,
                    "billed_amount": 750,
                    "pending_amount": 2250,
                    "received_qty_amount": 1500,
                    "warehouse": "Stores - DC",
                    "company": "Demo Company",
                    "name": "POI-PARTIAL-001",
                },
            ],
        }
    return {
        "columns": [
            {"fieldname": "supplier_name", "label": "Supplier"},
            {"fieldname": "item_code", "label": "Item"},
            {"fieldname": "qty", "label": "Qty"},
            {"fieldname": "uom", "label": "UOM"},
            {"fieldname": "price", "label": "Price"},
            {"fieldname": "price_per_unit", "label": "Unit Price"},
            {"fieldname": "currency", "label": "Currency"},
            {"fieldname": "quotation", "label": "Supplier Quotation"},
            {"fieldname": "valid_till", "label": "Valid Till"},
            {"fieldname": "lead_time_days", "label": "Lead Time"},
            {"fieldname": "request_for_quotation", "label": "RFQ"},
        ],
        "result": [
            {
                "supplier_name": "Alpha Supplier",
                "item_code": "ITEM-001",
                "qty": 5,
                "uom": "Nos",
                "price": 1000,
                "price_per_unit": 200,
                "currency": "MMK",
                "quotation": "SUP-QTN-001",
                "valid_till": "2026-05-08",
                "lead_time_days": 4,
                "request_for_quotation": "RFQ-001",
            }
        ],
    }


fake_frappe.whitelist = _identity_whitelist
fake_frappe.PermissionError = _FakePermissionError
fake_frappe.ValidationError = Exception
fake_frappe.throw = _throw
fake_frappe.session = types.SimpleNamespace(user="purchase@example.com")
def _db_exists(doctype, name=None, **kwargs):
    if doctype == "Report":
        return name in {"Supplier Quotation Comparison", "Purchase Order Analysis"} and name not in MISSING_NATIVE_REPORTS
    return False


fake_frappe.db = types.SimpleNamespace(
    get_value=_db_get_value,
    exists=_db_exists,
    get_single_value=lambda doctype, fieldname: "Demo Company" if doctype == "Global Defaults" and fieldname == "default_company" else "MMK" if doctype == "Global Defaults" and fieldname == "default_currency" else None,
    count=_count,
)
fake_frappe.defaults = types.SimpleNamespace(
    get_user_default=lambda key=None, *args, **kwargs: "Demo Company" if key == "Company" else None,
    get_default=lambda key=None, *args, **kwargs: "Demo Company" if key == "company" else None,
)
fake_frappe.get_roles = lambda *args, **kwargs: list(CURRENT_ROLES)
fake_frappe.has_permission = _has_permission
fake_frappe.get_list = _get_list
fake_frappe.get_all = _get_all
fake_frappe.get_doc = _get_doc
def _new_doc(doctype):
    if doctype == "Procurement Supplier Readiness Profile":
        return _FakeReadinessProfileDoc(values={"doctype": doctype})
    if doctype == "Procurement Supplier Readiness Log":
        return _FakeReadinessLogDoc({"doctype": doctype})
    if doctype == "Procurement Item Buying Profile":
        return _FakeItemBuyingProfileDoc(values={"doctype": doctype})
    if doctype == "Procurement Item Buying Log":
        return _FakeItemBuyingLogDoc({"doctype": doctype})
    return _FakeReadinessLogDoc({"doctype": doctype})

fake_frappe.new_doc = _new_doc
fake_frappe.get_meta = lambda doctype: _FakeMeta(doctype)
fake_frappe.get_print = lambda doctype, name, print_format=None, doc=None, as_pdf=False, letterhead=None, **kwargs: (
    f"<div class='print-format'><h1>{doctype} {name}</h1><span class='supplier'>{getattr(doc, 'vendor', getattr(doc, 'supplier', ''))}</span></div>".encode("utf-8")
    if as_pdf
    else f"<div class='print-format'><h1>{doctype} {name}</h1><span class='supplier'>{getattr(doc, 'vendor', getattr(doc, 'supplier', ''))}</span></div>"
)
fake_frappe.generate_hash = lambda length=10: "x" * length
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="", response={})
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

def _fake_getdate(value=None):
    if isinstance(value, date):
        return value
    if not value:
        return date(2026, 5, 3)
    year, month, day = str(value).split(" ")[0].split("-")
    return date(int(year), int(month), int(day))


fake_utils.getdate = _fake_getdate
fake_utils.now_datetime = lambda: "2026-05-03 00:00:00"
fake_utils.nowdate = lambda: "2026-05-03"

fake_utils_data = types.ModuleType("frappe.utils.data")
fake_utils_data.get_timespan_date_range = lambda timespan: (None, None)

fake_query_report = types.ModuleType("frappe.desk.query_report")
fake_query_report.run = _run_query_report

fake_desk = types.ModuleType("frappe.desk")
fake_desk.query_report = fake_query_report
fake_frappe.desk = fake_desk
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
from pathlib import Path

from erp_workspace_ui.procurement_console import document_output, document_reviews, item_buying_profile, items, managed_purchase_order, managed_purchase_request, managed_rfq, managed_supplier_quotation, purchase_order_detail, readiness, readiness_evidence, report, service, supplier_detail, supplier_readiness, worklist


def _set_user(user, roles):
    fake_frappe.session.user = user
    CURRENT_ROLES[:] = list(roles)


def _set_readable_doctypes(*doctypes):
    READABLE_DOCTYPES.clear()
    READABLE_DOCTYPES.update(doctypes)


def _set_writeable_doctypes(*doctypes):
    WRITEABLE_DOCTYPES.clear()
    WRITEABLE_DOCTYPES.update(doctypes)


def _set_createable_doctypes(*doctypes):
    CREATEABLE_DOCTYPES.clear()
    CREATEABLE_DOCTYPES.update(doctypes)


def _filter_contains(filters, condition):
    return list(condition) in [list(item) for item in filters]




def _field_by_key(payload, key):
    for field in ((payload.get("controls") or {}).get("fields") or []):
        if field.get("key") == key:
            return field
    return None


def _row_names(payload):
    return [row.get("name") for row in ((payload.get("results") or {}).get("rows") or [])]

def _payload_actions(payload):
    actions = []
    controls = payload.get("controls") or {}
    actions.extend(controls.get("actions") or [])
    for row in ((payload.get("results") or {}).get("rows") or []):
        actions.extend(row.get("actions") or [])
    actions.extend((payload.get("action_targets") or {}).values())
    return actions


def _assert_no_forbidden_mutation_actions(testcase, payload):
    fragments = []
    for action in _payload_actions(payload):
        if isinstance(action, dict):
            fragments.append(" ".join(str(action.get(key) or "") for key in ["key", "label", "title", "kind", "doctype", "route"]))
        else:
            fragments.append(str(action))
    text = " ".join(fragments).lower()
    for forbidden in [
        "approve",
        "reject",
        "submit",
        "cancel",
        "amend",
        "close",
        "receive",
        "bill",
        "pay",
        "item_price",
        "default_supplier",
        "acknowledg",
    ]:
        testcase.assertNotIn(forbidden, text)


class TestProcurementConsolePhase3Contracts(unittest.TestCase):
    def setUp(self):
        global EMAIL_ACCOUNT_GET_ALL_RAISES, HAS_QUOTE_STATUS
        EMAIL_ACCOUNT_GET_ALL_RAISES = False
        HAS_QUOTE_STATUS = True
        _set_user("purchase@example.com", ["Purchase User"])
        _set_readable_doctypes(
            "Supplier",
            "Item",
            "Item Price",
            "Warehouse",
            "Company",
            "Material Request",
            "Purchase Order",
            "Purchase Receipt",
            "Purchase Invoice",
            "Request for Quotation",
            "Supplier Quotation",
            "Procurement Supplier Readiness Profile",
            "Procurement Supplier Readiness Log",
            "Procurement Item Buying Profile",
            "Procurement Item Buying Log",
        )
        _set_writeable_doctypes()
        _set_createable_doctypes()
        CAPTURED_GET_LIST_CALLS.clear()
        CAPTURED_GET_ALL_CALLS.clear()
        CAPTURED_REPORT_CALLS.clear()
        EMAIL_ACCOUNTS.clear()
        HIDDEN_PURCHASE_ORDER_LIST_NAMES.clear()
        HIDDEN_MATERIAL_REQUEST_LIST_NAMES.clear()
        HIDDEN_RFQ_LIST_NAMES.clear()
        HIDDEN_SUPPLIER_QUOTATION_LIST_NAMES.clear()
        MISSING_NATIVE_REPORTS.clear()
        MISSING_FIELDS.clear()
        SAVED_MATERIAL_REQUESTS.clear()
        SAVED_RFQS.clear()
        SAVED_SUPPLIER_QUOTATIONS.clear()
        SAVED_PURCHASE_ORDERS.clear()
        SUPPLIER_READINESS_PROFILES.clear()
        SUPPLIER_READINESS_LOGS.clear()
        ITEM_BUYING_PROFILES.clear()
        ITEM_BUYING_LOGS.clear()
        fake_frappe.local.response = {}

    def test_guest_bootstrap_raises_permission_error(self):
        _set_user("Guest", [])

        with self.assertRaises(_FakePermissionError):
            service.get_procurement_console_bootstrap()

    def test_procurement_bootstrap_returns_ready_buyer_sourcing_and_po_follow_up_workbench(self):
        payload = service.get_procurement_console_bootstrap()

        self.assertEqual(payload["workspace"]["workspace_id"], "procurement")
        self.assertEqual(payload["workspace"]["status"], "phase_3")
        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["scope"]["default_routing_enabled"], True)
        self.assertEqual(payload["reports_catalog"][0]["key"], "supplier_quotation_comparison")
        self.assertEqual(
            [item["key"] for item in payload["sidebar"]["items"]],
            [
                "procurement_console_home",
                "supplier_directory",
                "purchase_request_directory",
                "purchase_order_directory",
                "rfq_directory",
                "supplier_quotation_directory",
                "buying_item_directory",
                "procurement_reports",
            ],
        )
        self.assertIn("rfqs_awaiting_supplier_response", payload["work"])
        self.assertIn("supplier_quotations_to_compare", payload["work"])
        self.assertIn("supplier_quotations_expiring", payload["work"])
        self.assertIn("purchase_orders_due_soon", payload["work"])
        self.assertIn("purchase_orders_overdue", payload["work"])
        self.assertIn("purchase_orders_partially_received", payload["work"])
        self.assertIn("purchase_orders_not_billed_visibility", payload["work"])
        self.assertIn("purchase_orders_supplier_follow_up", payload["work"])
        self.assertIn("rfq_directory", payload["directories"])
        self.assertIn("supplier_quotation_directory", payload["directories"])
        self.assertIn("buying_item_directory", payload["directories"])

    def test_procurement_create_actions_follow_erpnext_create_permissions(self):
        _set_writeable_doctypes("Material Request", "Request for Quotation", "Supplier Quotation", "Purchase Order")
        _set_createable_doctypes("Material Request", "Request for Quotation", "Supplier Quotation", "Purchase Order")

        payload = service.get_procurement_console_bootstrap()

        self.assertEqual(
            [action["key"] for action in payload["create_actions"]],
            ["new_purchase_request", "new_rfq", "new_supplier_quotation", "new_purchase_order"],
        )
        self.assertEqual([action["variant"] for action in payload["create_actions"]], ["primary", "primary", "primary", "primary"])
        self.assertEqual(payload["action_targets"]["new_purchase_request"], {"kind": "page", "route": "procurement-console-purchase-request-form", "route_parts": ["new"]})
        self.assertEqual(payload["action_targets"]["new_rfq"], {"kind": "page", "route": "procurement-console-rfq-form", "route_parts": ["new"]})
        self.assertEqual(payload["action_targets"]["new_supplier_quotation"], {"kind": "page", "route": "procurement-console-supplier-quotation-form", "route_parts": ["new"]})
        self.assertEqual(payload["action_targets"]["new_purchase_order"], {"kind": "page", "route": "procurement-console-purchase-order-form", "route_parts": ["new"]})
        self.assertNotIn("new_supplier", payload["action_targets"])
        self.assertNotIn("new_item", payload["action_targets"])

    def test_managed_purchase_request_context_is_ready_for_purchase_roles(self):
        _set_writeable_doctypes("Material Request")
        _set_createable_doctypes("Material Request")

        payload = managed_purchase_request.get_managed_purchase_request_context("new")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["form"]["header"]["material_request_type"], "Purchase")
        self.assertEqual(payload["action_targets"]["back_to_purchase_requests"], {"kind": "worklist", "queue_key": "purchase_request_directory"})
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_managed_purchase_request_context_restricts_sales_roles(self):
        _set_user("sales@example.com", ["Sales User"])
        _set_writeable_doctypes("Material Request")
        _set_createable_doctypes("Material Request")

        payload = managed_purchase_request.get_managed_purchase_request_context("new")

        self.assertEqual(payload["state"]["kind"], "restricted")

    def test_managed_purchase_request_save_creates_purchase_draft(self):
        _set_writeable_doctypes("Material Request")
        _set_createable_doctypes("Material Request")

        payload = managed_purchase_request.save_managed_purchase_request_draft({
            "header": {"transaction_date": "2026-05-03", "schedule_date": "2026-05-20", "company": "Demo Company", "material_request_type": "Purchase"},
            "items": [{"item_code": "ITEM-001", "qty": 2, "schedule_date": "2026-05-20", "warehouse": "Stores - DC", "uom": "Wrong"}],
        })

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertIn("MAT-MR-DRAFT-001", SAVED_MATERIAL_REQUESTS)
        doc = SAVED_MATERIAL_REQUESTS["MAT-MR-DRAFT-001"]
        self.assertEqual(doc.material_request_type, "Purchase")
        self.assertEqual(doc.docstatus, 0)
        self.assertEqual(doc.items[0].uom, "Nos")
        self.assertEqual(doc.items[0].stock_uom, "Nos")
        self.assertEqual(doc.items[0].conversion_factor, 1)
        self.assertEqual(payload["review_route"], "/desk/procurement-console-purchase-request-review/MAT-MR-DRAFT-001")
        saved_action_keys = [action["key"] for action in payload["controls"]["actions"]]
        self.assertNotIn("open_erp_form", saved_action_keys)
        self.assertIn("review_request", saved_action_keys)
        self.assertEqual(payload["action_targets"]["review_request"]["kind"], "page")
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_managed_purchase_request_rejects_non_purchase_type_and_forbidden_fields(self):
        _set_writeable_doctypes("Material Request")
        _set_createable_doctypes("Material Request")

        non_purchase = managed_purchase_request.save_managed_purchase_request_draft({
            "header": {"material_request_type": "Material Transfer", "transaction_date": "2026-05-03", "company": "Demo Company"},
            "items": [{"item_code": "ITEM-001", "qty": 1, "schedule_date": "2026-05-20"}],
        })
        forbidden = managed_purchase_request.save_managed_purchase_request_draft({
            "header": {"transaction_date": "2026-05-03", "company": "Demo Company"},
            "items": [{"item_code": "ITEM-001", "qty": 1, "schedule_date": "2026-05-20", "item_price": 100}],
        })

        self.assertEqual(non_purchase["state"]["kind"], "error")
        self.assertEqual(forbidden["state"]["kind"], "error")
        self.assertEqual({}, SAVED_MATERIAL_REQUESTS)

    def test_managed_purchase_request_cannot_edit_submitted_document(self):
        _set_writeable_doctypes("Material Request")
        _set_createable_doctypes("Material Request")

        payload = managed_purchase_request.save_managed_purchase_request_draft({
            "name": "MAT-MR-SUBMITTED",
            "header": {"transaction_date": "2026-05-03", "company": "Demo Company"},
            "items": [{"item_code": "ITEM-001", "qty": 1, "schedule_date": "2026-05-20"}],
        })

        self.assertEqual(payload["state"]["kind"], "error")

    def test_managed_rfq_context_is_ready_for_purchase_roles(self):
        _set_writeable_doctypes("Request for Quotation")
        _set_createable_doctypes("Request for Quotation")

        payload = managed_rfq.get_managed_rfq_context("new")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["summary"]["chips"][0]["label"], "New RFQ")
        self.assertEqual(payload["form"]["header"]["subject"], "Request for Quotation")
        self.assertEqual(payload["action_targets"]["back_to_rfqs"], {"kind": "worklist", "queue_key": "rfq_directory"})
        self.assertEqual(payload["conversion"]["purchase_request_to_rfq"], "deferred")
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_managed_rfq_context_restricts_sales_roles(self):
        _set_user("sales@example.com", ["Sales User"])
        _set_writeable_doctypes("Request for Quotation")
        _set_createable_doctypes("Request for Quotation")

        payload = managed_rfq.get_managed_rfq_context("new")

        self.assertEqual(payload["state"]["kind"], "restricted")

    def test_managed_rfq_save_creates_draft(self):
        _set_writeable_doctypes("Request for Quotation")
        _set_createable_doctypes("Request for Quotation")

        payload = managed_rfq.save_managed_rfq_draft({
            "header": {"transaction_date": "2026-05-03", "schedule_date": "2026-05-20", "company": "Demo Company"},
            "suppliers": [{"supplier": "SUP-001"}],
            "items": [{"item_code": "ITEM-001", "qty": 2, "schedule_date": "2026-05-20", "warehouse": "Stores - DC", "uom": "Wrong"}],
        })

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertIn("PUR-RFQ-DRAFT-001", SAVED_RFQS)
        doc = SAVED_RFQS["PUR-RFQ-DRAFT-001"]
        self.assertEqual(doc.docstatus, 0)
        self.assertEqual(doc.suppliers[0].supplier, "SUP-001")
        self.assertEqual(doc.items[0].uom, "Nos")
        self.assertEqual(doc.items[0].stock_uom, "Nos")
        self.assertEqual(doc.items[0].conversion_factor, 1)
        self.assertEqual(payload["review_route"], "/desk/procurement-console-rfq-review/PUR-RFQ-DRAFT-001")
        self.assertNotIn("open_erp_form", [action["key"] for action in managed_rfq.get_managed_rfq_context("new")["controls"]["actions"]])
        saved_action_keys = [action["key"] for action in payload["controls"]["actions"]]
        self.assertNotIn("open_erp_form", saved_action_keys)
        self.assertIn("review_rfq", saved_action_keys)
        self.assertEqual(payload["action_targets"]["review_rfq"]["kind"], "page")
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_managed_rfq_requires_supplier_and_item(self):
        _set_writeable_doctypes("Request for Quotation")
        _set_createable_doctypes("Request for Quotation")

        missing_supplier = managed_rfq.save_managed_rfq_draft({
            "header": {"transaction_date": "2026-05-03", "company": "Demo Company"},
            "suppliers": [],
            "items": [{"item_code": "ITEM-001", "qty": 1, "schedule_date": "2026-05-20"}],
        })
        missing_item = managed_rfq.save_managed_rfq_draft({
            "header": {"transaction_date": "2026-05-03", "company": "Demo Company"},
            "suppliers": [{"supplier": "SUP-001"}],
            "items": [],
        })

        self.assertEqual(missing_supplier["state"]["kind"], "error")
        self.assertEqual(missing_item["state"]["kind"], "error")
        self.assertEqual({}, SAVED_RFQS)

    def test_managed_rfq_rejects_forbidden_fields(self):
        _set_writeable_doctypes("Request for Quotation")
        _set_createable_doctypes("Request for Quotation")

        payload = managed_rfq.save_managed_rfq_draft({
            "header": {"transaction_date": "2026-05-03", "company": "Demo Company", "submit": 1},
            "suppliers": [{"supplier": "SUP-001", "email_id": "supplier@example.com"}],
            "items": [{"item_code": "ITEM-001", "qty": 1, "schedule_date": "2026-05-20", "supplier_quotation": "SQ-001"}],
        })

        self.assertEqual(payload["state"]["kind"], "error")
        self.assertEqual({}, SAVED_RFQS)

    def test_managed_rfq_cannot_edit_submitted_document(self):
        _set_writeable_doctypes("Request for Quotation")
        _set_createable_doctypes("Request for Quotation")

        payload = managed_rfq.save_managed_rfq_draft({
            "name": "PUR-RFQ-SUBMITTED",
            "header": {"transaction_date": "2026-05-03", "company": "Demo Company"},
            "suppliers": [{"supplier": "SUP-001"}],
            "items": [{"item_code": "ITEM-001", "qty": 1, "schedule_date": "2026-05-20"}],
        })

        self.assertEqual(payload["state"]["kind"], "error")

    def test_managed_supplier_quotation_context_is_ready_for_purchase_roles(self):
        _set_writeable_doctypes("Supplier Quotation")
        _set_createable_doctypes("Supplier Quotation")

        payload = managed_supplier_quotation.get_managed_supplier_quotation_context("new")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["summary"]["chips"][0]["label"], "New Quotation")
        self.assertEqual(payload["form"]["doctype"], "Supplier Quotation")
        self.assertEqual(payload["form"]["header"]["currency"], "MMK")
        self.assertEqual(payload["action_targets"]["back_to_supplier_quotations"], {"kind": "worklist", "queue_key": "supplier_quotation_directory"})
        self.assertEqual(payload["conversion"]["rfq_to_supplier_quotation"], "deferred")
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_managed_supplier_quotation_currency_never_uses_company_name(self):
        original_get_value = fake_frappe.db.get_value
        original_get_single_value = fake_frappe.db.get_single_value
        fake_frappe.db.get_value = lambda doctype, name=None, fieldname=None, as_dict=False, **kwargs: None
        fake_frappe.db.get_single_value = lambda doctype, fieldname: "Demo Company" if doctype == "Global Defaults" else None
        try:
            _set_writeable_doctypes("Supplier Quotation")
            _set_createable_doctypes("Supplier Quotation")

            payload = managed_supplier_quotation.get_managed_supplier_quotation_context("new")

            self.assertEqual(payload["form"]["header"]["company"], "Demo Company")
            self.assertEqual(payload["form"]["header"]["currency"], "MMK")
        finally:
            fake_frappe.db.get_value = original_get_value
            fake_frappe.db.get_single_value = original_get_single_value

    def test_managed_supplier_quotation_context_restricts_sales_roles(self):
        _set_user("sales@example.com", ["Sales User"])
        _set_writeable_doctypes("Supplier Quotation")
        _set_createable_doctypes("Supplier Quotation")

        payload = managed_supplier_quotation.get_managed_supplier_quotation_context("new")

        self.assertEqual(payload["state"]["kind"], "restricted")

    def test_managed_supplier_quotation_save_creates_draft(self):
        _set_writeable_doctypes("Supplier Quotation")
        _set_createable_doctypes("Supplier Quotation")

        payload = managed_supplier_quotation.save_managed_supplier_quotation_draft({
            "header": {"supplier": "SUP-001", "transaction_date": "2026-05-03", "valid_till": "2026-05-30", "company": "Demo Company", "currency": "MMK"},
            "items": [{"item_code": "ITEM-001", "qty": 2, "rate": 100, "uom": "Wrong"}],
        })

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertIn("SUP-QTN-DRAFT-001", SAVED_SUPPLIER_QUOTATIONS)
        doc = SAVED_SUPPLIER_QUOTATIONS["SUP-QTN-DRAFT-001"]
        self.assertEqual(doc.docstatus, 0)
        self.assertEqual(doc.supplier, "SUP-001")
        self.assertEqual(doc.items[0].uom, "Nos")
        self.assertEqual(doc.items[0].stock_uom, "Nos")
        self.assertEqual(doc.items[0].conversion_factor, 1)
        self.assertEqual(doc.items[0].rate, 100.0)
        self.assertEqual(doc.items[0].amount, 200.0)
        self.assertEqual(payload["review_route"], "/desk/procurement-console-supplier-quotation-review/SUP-QTN-DRAFT-001")
        self.assertNotIn("open_erp_form", [action["key"] for action in managed_supplier_quotation.get_managed_supplier_quotation_context("new")["controls"]["actions"]])
        saved_action_keys = [action["key"] for action in payload["controls"]["actions"]]
        self.assertNotIn("open_erp_form", saved_action_keys)
        self.assertIn("review_quotation", saved_action_keys)
        self.assertEqual(payload["action_targets"]["review_quotation"]["kind"], "page")
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_managed_supplier_quotation_requires_supplier_item_and_rate(self):
        _set_writeable_doctypes("Supplier Quotation")
        _set_createable_doctypes("Supplier Quotation")

        missing_supplier = managed_supplier_quotation.save_managed_supplier_quotation_draft({
            "header": {"transaction_date": "2026-05-03", "company": "Demo Company"},
            "items": [{"item_code": "ITEM-001", "qty": 1, "rate": 100}],
        })
        missing_item = managed_supplier_quotation.save_managed_supplier_quotation_draft({
            "header": {"supplier": "SUP-001", "transaction_date": "2026-05-03", "company": "Demo Company"},
            "items": [],
        })
        missing_rate = managed_supplier_quotation.save_managed_supplier_quotation_draft({
            "header": {"supplier": "SUP-001", "transaction_date": "2026-05-03", "company": "Demo Company"},
            "items": [{"item_code": "ITEM-001", "qty": 1, "rate": 0}],
        })

        self.assertEqual(missing_supplier["state"]["kind"], "error")
        self.assertEqual(missing_item["state"]["kind"], "error")
        self.assertEqual(missing_rate["state"]["kind"], "error")
        self.assertEqual({}, SAVED_SUPPLIER_QUOTATIONS)

    def test_managed_supplier_quotation_rejects_forbidden_fields(self):
        _set_writeable_doctypes("Supplier Quotation")
        _set_createable_doctypes("Supplier Quotation")

        payload = managed_supplier_quotation.save_managed_supplier_quotation_draft({
            "header": {"supplier": "SUP-001", "transaction_date": "2026-05-03", "submit": 1},
            "items": [{"item_code": "ITEM-001", "qty": 1, "rate": 100, "purchase_order": "PO-001", "item_price": 100}],
        })

        self.assertEqual(payload["state"]["kind"], "error")
        self.assertEqual({}, SAVED_SUPPLIER_QUOTATIONS)

    def test_managed_supplier_quotation_cannot_edit_submitted_document(self):
        _set_writeable_doctypes("Supplier Quotation")
        _set_createable_doctypes("Supplier Quotation")

        payload = managed_supplier_quotation.save_managed_supplier_quotation_draft({
            "name": "SUP-QTN-SUBMITTED",
            "header": {"supplier": "SUP-001", "transaction_date": "2026-05-03", "company": "Demo Company"},
            "items": [{"item_code": "ITEM-001", "qty": 1, "rate": 100}],
        })

        self.assertEqual(payload["state"]["kind"], "error")


    def test_managed_purchase_order_context_is_ready_for_purchase_roles(self):
        _set_writeable_doctypes("Purchase Order")
        _set_createable_doctypes("Purchase Order")

        payload = managed_purchase_order.get_managed_purchase_order_context("new")

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(payload["summary"]["chips"][0]["label"], "New Purchase Order")
        self.assertEqual(payload["form"]["doctype"], "Purchase Order")
        self.assertEqual(payload["form"]["header"]["currency"], "MMK")
        self.assertEqual(len(payload["form"]["items"]), 1)
        self.assertEqual(payload["action_targets"]["back_to_purchase_orders"], {"kind": "worklist", "queue_key": "purchase_order_directory"})
        self.assertEqual(payload["conversion"]["supplier_quotation_to_purchase_order"], "deferred")
        self.assertNotIn("open_erp_form", [action["key"] for action in payload["controls"]["actions"]])
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_managed_purchase_order_context_restricts_sales_roles(self):
        _set_user("sales@example.com", ["Sales User"])
        _set_writeable_doctypes("Purchase Order")
        _set_createable_doctypes("Purchase Order")

        payload = managed_purchase_order.get_managed_purchase_order_context("new")

        self.assertEqual(payload["state"]["kind"], "restricted")

    def test_managed_purchase_order_save_creates_draft(self):
        _set_writeable_doctypes("Purchase Order")
        _set_createable_doctypes("Purchase Order")

        payload = managed_purchase_order.save_managed_purchase_order({
            "header": {"supplier": "SUP-001", "transaction_date": "2026-05-03", "schedule_date": "2026-05-30", "company": "Demo Company", "currency": "MMK", "set_warehouse": "Stores - DC"},
            "items": [{"item_code": "ITEM-001", "qty": 2, "rate": 100, "schedule_date": "2026-05-30", "warehouse": "Stores - DC", "uom": "Wrong"}],
        })

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertIn("PUR-ORD-DRAFT-001", SAVED_PURCHASE_ORDERS)
        doc = SAVED_PURCHASE_ORDERS["PUR-ORD-DRAFT-001"]
        self.assertEqual(doc.docstatus, 0)
        self.assertEqual(doc.supplier, "SUP-001")
        self.assertEqual(doc.items[0].uom, "Nos")
        self.assertEqual(doc.items[0].stock_uom, "Nos")
        self.assertEqual(doc.items[0].conversion_factor, 1)
        self.assertEqual(doc.items[0].rate, 100.0)
        self.assertEqual(doc.items[0].amount, 200.0)
        self.assertEqual(doc.items[0].schedule_date, "2026-05-30")
        self.assertEqual(payload["route"], "/desk/procurement-console-purchase-order-form/PUR-ORD-DRAFT-001")
        self.assertEqual(payload["review_route"], "/desk/procurement-console-po-follow-up/PUR-ORD-DRAFT-001")
        saved_action_keys = [action["key"] for action in payload["controls"]["actions"]]
        self.assertNotIn("open_erp_form", saved_action_keys)
        self.assertIn("review_purchase_order", saved_action_keys)
        self.assertEqual(payload["action_targets"]["review_purchase_order"]["kind"], "page")
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_managed_purchase_order_requires_supplier_item_qty_and_rate(self):
        _set_writeable_doctypes("Purchase Order")
        _set_createable_doctypes("Purchase Order")

        missing_supplier = managed_purchase_order.save_managed_purchase_order({
            "header": {"transaction_date": "2026-05-03", "company": "Demo Company"},
            "items": [{"item_code": "ITEM-001", "qty": 1, "rate": 100, "schedule_date": "2026-05-20"}],
        })
        missing_item = managed_purchase_order.save_managed_purchase_order({
            "header": {"supplier": "SUP-001", "transaction_date": "2026-05-03", "company": "Demo Company"},
            "items": [],
        })
        invalid_qty = managed_purchase_order.save_managed_purchase_order({
            "header": {"supplier": "SUP-001", "transaction_date": "2026-05-03", "company": "Demo Company"},
            "items": [{"item_code": "ITEM-001", "qty": 0, "rate": 100, "schedule_date": "2026-05-20"}],
        })
        missing_rate = managed_purchase_order.save_managed_purchase_order({
            "header": {"supplier": "SUP-001", "transaction_date": "2026-05-03", "company": "Demo Company"},
            "items": [{"item_code": "ITEM-001", "qty": 1, "schedule_date": "2026-05-20"}],
        })

        self.assertEqual(missing_supplier["state"]["kind"], "error")
        self.assertEqual(missing_item["state"]["kind"], "error")
        self.assertEqual(invalid_qty["state"]["kind"], "error")
        self.assertEqual(missing_rate["state"]["kind"], "error")
        self.assertEqual({}, SAVED_PURCHASE_ORDERS)

    def test_managed_purchase_order_rejects_forbidden_fields(self):
        _set_writeable_doctypes("Purchase Order")
        _set_createable_doctypes("Purchase Order")

        payload = managed_purchase_order.save_managed_purchase_order({
            "header": {"supplier": "SUP-001", "transaction_date": "2026-05-03", "submit": 1},
            "items": [{"item_code": "ITEM-001", "qty": 1, "rate": 100, "schedule_date": "2026-05-20", "purchase_receipt": "PR-001", "item_price": 100}],
        })

        self.assertEqual(payload["state"]["kind"], "error")
        self.assertEqual({}, SAVED_PURCHASE_ORDERS)

    def test_managed_purchase_order_cannot_edit_submitted_document(self):
        _set_writeable_doctypes("Purchase Order")
        _set_createable_doctypes("Purchase Order")

        payload = managed_purchase_order.save_managed_purchase_order({
            "name": "PUR-ORD-SUBMITTED",
            "header": {"supplier": "SUP-001", "transaction_date": "2026-05-03", "company": "Demo Company"},
            "items": [{"item_code": "ITEM-001", "qty": 1, "rate": 100, "schedule_date": "2026-05-20"}],
        })

        self.assertEqual(payload["state"]["kind"], "error")

    def test_document_output_context_for_rfq_and_purchase_order_is_preview_only(self):
        _set_user("purchase@example.com", ["Purchase User"])

        rfq_context = document_output.get_document_output_context("Request for Quotation", "PUR-RFQ-MULTI")
        po_context = document_output.get_document_output_context("Purchase Order", "PUR-DUE-001")

        self.assertEqual(rfq_context["state"]["kind"], "ready")
        self.assertEqual(rfq_context["warning"], "Draft / Not sent")
        self.assertFalse(rfq_context["can_send"])
        self.assertIn("Email sending is not active yet", rfq_context["send_block_reason"])
        self.assertTrue(rfq_context["requires_supplier_selection"])
        self.assertEqual([row["supplier"] for row in rfq_context["suppliers"]], ["SUP-001", "SUP-002"])
        self.assertIn("send_readiness", rfq_context)
        self.assertFalse(rfq_context["send_readiness"]["can_send"])
        self.assertEqual(po_context["state"]["kind"], "ready")
        self.assertEqual(po_context["warning"], "Draft / Not for supplier")
        self.assertFalse(po_context["can_send"])
        self.assertIn("Supplier sending is not active yet", po_context["send_block_reason"])
        _assert_no_forbidden_mutation_actions(self, rfq_context)
        _assert_no_forbidden_mutation_actions(self, po_context)

    def test_rfq_send_readiness_context_reports_recipients_and_blocked_send(self):
        _set_user("purchase.manager@example.com", ["Purchase Manager"])

        context = document_output.get_rfq_send_readiness_context("PUR-RFQ-MULTI")

        self.assertEqual(context["state"]["kind"], "ready")
        self.assertFalse(context["can_send"])
        self.assertIn("Email sending is not active yet", context["send_block_reason"])
        self.assertFalse(context["outgoing_email"]["available"])
        self.assertIn("Outgoing email", context["outgoing_email"]["reason"])
        statuses = {row["supplier"]: row for row in context["suppliers"]}
        self.assertEqual(statuses["SUP-001"]["email"], "buyer.contact@example.com")
        self.assertEqual(statuses["SUP-001"]["readiness_status"], "email_unavailable")
        self.assertEqual(statuses["SUP-002"]["readiness_status"], "missing_email")
        self.assertEqual(context["summary"]["total"], 2)
        self.assertEqual(context["summary"]["missing_email"], 1)
        self.assertEqual(context["summary"]["email_unavailable"], 1)

    def test_rfq_send_readiness_reports_ready_recipient_when_outgoing_email_available(self):
        _set_user("purchase.manager@example.com", ["Purchase Manager"])
        EMAIL_ACCOUNTS.append({"name": "Buying", "email_id": "buying@example.com", "enable_outgoing": 1, "default_outgoing": 1, "awaiting_password": 0})

        context = document_output.get_rfq_send_readiness_context("PUR-RFQ-MULTI")

        statuses = {row["supplier"]: row for row in context["suppliers"]}
        self.assertTrue(context["outgoing_email"]["available"])
        self.assertEqual(context["outgoing_email"]["account"], "")
        self.assertEqual(context["outgoing_email"]["email_id"], "")
        self.assertEqual(statuses["SUP-001"]["readiness_status"], "ready")
        self.assertEqual(statuses["SUP-002"]["readiness_status"], "missing_email")
        self.assertFalse(context["can_send"])

    def test_rfq_send_readiness_handles_email_account_permission_failure_as_unavailable(self):
        global EMAIL_ACCOUNT_GET_ALL_RAISES
        _set_user("purchase.manager@example.com", ["Purchase Manager"])
        EMAIL_ACCOUNT_GET_ALL_RAISES = True

        context = document_output.get_rfq_send_readiness_context("PUR-RFQ-MULTI")

        self.assertEqual(context["state"]["kind"], "ready")
        self.assertFalse(context["outgoing_email"]["available"])
        self.assertEqual(context["outgoing_email"]["status"], "unavailable")
        self.assertIn("Outgoing email", context["outgoing_email"]["reason"])
        self.assertNotIn("Email Account", context["outgoing_email"]["reason"])
        self.assertFalse(context["can_send"])
        self.assertFalse(any(call["doctype"] == "Email Account" for call in CAPTURED_GET_LIST_CALLS))

    def test_rfq_send_readiness_restricts_sales_and_guest(self):
        _set_user("sales@example.com", ["Sales User"])
        restricted = document_output.get_rfq_send_readiness_context("PUR-RFQ-MULTI")
        self.assertEqual(restricted["state"]["kind"], "restricted")

        _set_user("Guest", [])
        guest = document_output.get_rfq_send_readiness_context("PUR-RFQ-MULTI")
        self.assertEqual(guest["state"]["kind"], "restricted")

    def test_document_output_restricts_sales_and_invalid_doctype(self):
        _set_user("sales@example.com", ["Sales User"])

        restricted = document_output.get_document_output_context("Request for Quotation", "PUR-RFQ-001")
        invalid = document_output.get_document_output_context("Sales Order", "SO-001")

        self.assertEqual(restricted["state"]["kind"], "restricted")
        self.assertEqual(invalid["state"]["kind"], "error")

    def test_rfq_preview_requires_and_isolates_selected_supplier(self):
        missing = document_output.get_document_print_preview_context("Request for Quotation", "PUR-RFQ-MULTI")
        selected = document_output.get_document_print_preview_context("Request for Quotation", "PUR-RFQ-MULTI", supplier="SUP-002")

        self.assertEqual(missing["state"]["kind"], "error")
        self.assertIn("Select one supplier", missing["state"]["detail"])
        self.assertEqual(selected["state"]["kind"], "ready")
        self.assertEqual(selected["selected_supplier"]["supplier"], "SUP-002")
        self.assertIn("Supplier: SUP-002", selected["html"])
        self.assertIn("SUP-002", selected["html"])
        self.assertNotIn("Supplier: SUP-001", selected["html"])
        self.assertNotIn("Get PDF", selected["html"])
        self.assertNotIn("<button", selected["html"])
        self.assertIn("erpw-output-preview-table", selected["html"])
        self.assertEqual(selected["filename"], "PUR-RFQ-MULTI-SUP-002-DRAFT-NOT-SENT.pdf")

    def test_rfq_pdf_requires_supplier_and_sets_supplier_specific_filename(self):
        missing = None
        try:
            document_output.download_document_pdf("Request for Quotation", "PUR-RFQ-MULTI")
        except Exception as exc:
            missing = str(exc)
        self.assertIn("Select one supplier", missing or "")

        document_output.download_document_pdf("Request for Quotation", "PUR-RFQ-MULTI", supplier="SUP-001")

        response = fake_frappe.local.response
        self.assertEqual(response["type"], "pdf")
        self.assertEqual(response["filename"], "PUR-RFQ-MULTI-SUP-001-DRAFT-NOT-SENT.pdf")
        self.assertIn(b"Draft / Not sent", response["filecontent"])
        self.assertIn(b"Supplier: SUP-001", response["filecontent"])

    def test_po_preview_and_pdf_are_draft_internal_only(self):
        preview = document_output.get_document_print_preview_context("Purchase Order", "PUR-DUE-001")
        document_output.download_document_pdf("Purchase Order", "PUR-DUE-001")

        self.assertEqual(preview["state"]["kind"], "ready")
        self.assertEqual(preview["warning"], "Draft / Not for supplier")
        self.assertIn("Draft / Not for supplier", preview["html"])
        self.assertIn("erpw-output-preview-table", preview["html"])
        self.assertNotIn("Get PDF", preview["html"])
        self.assertNotIn("Finished Good Qty", preview["html"])
        self.assertNotIn("Stock UOM", preview["html"])
        self.assertNotIn("Subcontracted Quantity", preview["html"])
        self.assertNotIn("Discount Amount", preview["html"])
        self.assertNotIn("Distributed Discount Amount", preview["html"])
        self.assertNotIn("Rate Of Stock UOM", preview["html"])
        self.assertEqual(preview["filename"], "PUR-DUE-001-DRAFT-NOT-FOR-SUPPLIER.pdf")
        response = fake_frappe.local.response
        self.assertEqual(response["type"], "pdf")
        self.assertEqual(response["filename"], "PUR-DUE-001-DRAFT-NOT-FOR-SUPPLIER.pdf")
        self.assertIn(b"Draft / Not for supplier", response["filecontent"])
        self.assertNotIn(b"Finished Good Qty", response["filecontent"])

    def test_document_output_has_no_send_or_communication_side_effects(self):
        rfq_context = document_output.get_document_output_context("Request for Quotation", "PUR-RFQ-001")
        po_context = document_output.get_document_output_context("Purchase Order", "PUR-DUE-001")

        for payload in (rfq_context, po_context):
            self.assertFalse(payload["can_send"])
            self.assertNotIn("Communication", str(payload))
            for action in payload["actions"]:
                if action["key"] == "send":
                    self.assertTrue(action["disabled"])
                    self.assertEqual(action["kind"], "blocked")
        _assert_no_forbidden_mutation_actions(self, rfq_context)
        _assert_no_forbidden_mutation_actions(self, po_context)

    def test_procurement_supplier_and_item_create_actions_are_deferred(self):
        _set_user("manager@example.com", ["Purchase Manager"])
        _set_createable_doctypes("Supplier", "Item")

        manager_payload = service.get_procurement_console_bootstrap()

        self.assertEqual(manager_payload["create_actions"], [])
        self.assertNotIn("new_supplier", manager_payload["action_targets"])
        self.assertNotIn("new_item", manager_payload["action_targets"])

        _set_user("master@example.com", ["Purchase Master Manager", "Item Manager", "Stock Manager"])
        master_payload = service.get_procurement_console_bootstrap()

        self.assertEqual(master_payload["create_actions"], [])
        self.assertNotIn("new_supplier", master_payload["action_targets"])
        self.assertNotIn("new_item", master_payload["action_targets"])

    def test_procurement_overview_renders_create_actions_from_backend_payload(self):
        overview_public_path = Path(__file__).resolve().parents[1] / "public" / "js" / "procurement_console" / "procurement_console_page.js"
        source = overview_public_path.read_text()
        boot_source = (Path(__file__).resolve().parents[1] / "public" / "js" / "erp_workspace_ui_boot.js").read_text()

        self.assertIn("create_actions", source)
        self.assertNotIn("new_doc", source)
        self.assertIn('if (target.kind === "page"', source)
        self.assertNotIn('frappe.set_route("Form"', source)
        self.assertIn("cleanupProcurementRouteShells", source)
        self.assertIn("workspace_console_runtime.js", source)
        self.assertIn("ensureConsoleRuntime", source)
        self.assertIn("renderLoadingState(page)", source)
        self.assertIn('data-erpw-console-bootstrap="loading"', source)
        self.assertIn("fetchBootstrapWithRetry", source)
        self.assertIn("BOOTSTRAP_RETRY_DELAYS", source)
        self.assertIn('data-erpw-console-bootstrap", "retrying"', source)
        self.assertIn('$(\'.sales-console-shell[data-erpw-workspace="procurement"]\').first()', source)
        self.assertIn("isFirstPaintShell", source)
        self.assertIn("isLoadingShell", source)
        self.assertIn('data-erpw-direct-first-paint") === "procurement-console"', source)
        self.assertIn("scheduleActiveOverviewRender", source)
        self.assertIn("shouldSelfRenderOverview", source)
        self.assertIn("renderActiveOverviewRoute", source)
        self.assertIn('document.querySelector(".sales-console-kpi-card")', source)
        self.assertIn('data-erpw-page-key="procurement-console"', source)
        self.assertIn('if (wrapper && wrapper.id === "body") return makeFallbackPage(wrapper);', source)
        self.assertIn("function render(wrapper) {\n    if (!isActiveProcurementRoute()) return;", source)
        self.assertIn("hasReadyOverviewShell", source)
        self.assertIn('if (hasReadyOverviewShell()) return;', source)
        self.assertIn("bindActiveOverviewGuard", source)
        self.assertIn("activeOverviewGuardBound", source)
        self.assertIn("}, 160);", source)
        self.assertIn('.first().get(0)', source)
        self.assertIn("function pageBodyElement(page)", source)
        self.assertIn('return document.querySelector(".erpw-direct-console-body");', source)
        self.assertIn("function replacePageBody(page, $content)", source)
        self.assertIn("body.appendChild(node);", source)
        self.assertIn("if (!keepNode || !keepNode.isConnected) return;", source)
        self.assertNotIn('$host.empty().append(\'<main class="layout-main-section erpw-direct-console-body"></main>\');', source)
        self.assertNotIn("frappe.new_doc", source)
        self.assertIn('data-section-key="create-actions"', source)
        self.assertIn("Start Buying Work", source)
        self.assertIn("renderProcurementOverviewFirstPaint", boot_source)
        self.assertIn('data-erpw-direct-first-paint", "procurement-console"', boot_source)
        self.assertIn("activeShellIsLoading", boot_source)
        self.assertIn('getAttribute("data-erpw-console-runtime") === "loading"', boot_source)
        self.assertIn("if (activeShell && procurementRouteShellCount(pageKey) === 1 && !activeShellIsLoading)", boot_source)
        self.assertLess(boot_source.index('const deskBody = document.getElementById("body");'), boot_source.index("if (page && page.wrapper) return page.wrapper;"))
        self.assertNotIn("if (page) return page;", boot_source)
        self.assertIn("Start Buying Work", boot_source)
        self.assertIn("Buying Pipeline", boot_source)
        self.assertLess(boot_source.index("renderProcurementOverviewFirstPaint(pageKey)"), boot_source.index("if (!window.frappe || !frappe.pages) return false;"))

    def test_shared_action_rebalance_preserves_click_handlers(self):
        runtime_path = Path(__file__).resolve().parents[1] / "public" / "js" / "runtime" / "console" / "workspace_console_runtime.js"
        source = runtime_path.read_text()
        rebalance_index = source.index("function rebalanceActionStrips")
        detach_index = source.index("$actions.detach();", rebalance_index)
        empty_index = source.index("$primary.empty();", rebalance_index)

        self.assertLess(detach_index, empty_index)
        self.assertIn("$(elements).detach();", source)
        self.assertIn('if (typeof config.onClick === "function") config.onClick(event);', source)

    def test_purchase_roles_receive_procurement_home_without_sales_default_app(self):
        _set_user("purchase@example.com", ["Purchase User"])
        bootinfo = {}

        self.assertIsNone(boot.resolve_default_app("purchase@example.com"))
        self.assertEqual(boot.resolve_default_home_page("purchase@example.com"), "procurement-console-home")
        boot.apply_role_based_boot_home(bootinfo)
        self.assertEqual(bootinfo["home_page"], "procurement-console-home")

    def test_sales_roles_keep_sales_home_and_default_app(self):
        _set_user("sales@example.com", ["Sales User"])
        bootinfo = {}

        self.assertEqual(boot.resolve_default_app("sales@example.com"), "erp_workspace_ui")
        self.assertEqual(boot.resolve_default_home_page("sales@example.com"), "sales-console-home")
        boot.apply_role_based_boot_home(bootinfo)
        self.assertEqual(bootinfo["home_page"], "sales-console-home")

    def test_warehouse_operational_roles_receive_warehouse_home_without_default_app(self):
        _set_user("warehouse@example.com", ["Warehouse Manager"])
        bootinfo = {}

        self.assertIsNone(boot.resolve_default_app("warehouse@example.com"))
        self.assertTrue(boot.should_use_warehouse_console_home("warehouse@example.com"))
        self.assertEqual(boot.resolve_default_home_page("warehouse@example.com"), "warehouse-console")
        boot.apply_role_based_boot_home(bootinfo)
        self.assertEqual(bootinfo["home_page"], "warehouse-console")

    def test_finance_roles_receive_finance_control_desk_without_default_app(self):
        cases = (
            ("finance-manager@example.com", ["Accounts Manager"]),
            ("finance-user@example.com", ["Accounts User"]),
        )
        for user, roles in cases:
            with self.subTest(user=user):
                _set_user(user, roles)
                bootinfo = {}

                self.assertIsNone(boot.resolve_default_app(user))
                self.assertEqual(boot.resolve_default_home_page(user), "finance-control-desk")
                boot.apply_role_based_boot_home(bootinfo)
                self.assertEqual(bootinfo["home_page"], "finance-control-desk")

    def test_finance_boot_home_is_not_persisted_by_default_home_sync(self):
        _set_user("finance-manager@example.com", ["Accounts Manager"])
        db_set_calls = []
        default_set_calls = []
        default_clear_calls = []
        original_db_set_value = getattr(fake_frappe.db, "set_value", None)
        original_set_user_default = getattr(fake_frappe.defaults, "set_user_default", None)
        original_clear_user_default = getattr(fake_frappe.defaults, "clear_user_default", None)
        fake_frappe.db.set_value = lambda *args, **kwargs: db_set_calls.append((args, kwargs))
        fake_frappe.defaults.set_user_default = lambda *args, **kwargs: default_set_calls.append((args, kwargs))
        fake_frappe.defaults.clear_user_default = lambda *args, **kwargs: default_clear_calls.append((args, kwargs))
        try:
            self.assertEqual(boot.resolve_default_home_page("finance-manager@example.com"), "finance-control-desk")
            self.assertIsNone(boot.resolve_default_home_page("finance-manager@example.com", include_finance=False))
            bootinfo = {}
            boot.apply_role_based_boot_home(bootinfo)
            self.assertEqual(bootinfo["home_page"], "finance-control-desk")

            boot.sync_current_user_default_app()

            self.assertEqual(db_set_calls, [])
            self.assertEqual(default_set_calls, [])
            self.assertEqual(default_clear_calls, [])
        finally:
            if original_db_set_value is None:
                delattr(fake_frappe.db, "set_value")
            else:
                fake_frappe.db.set_value = original_db_set_value
            if original_set_user_default is None:
                delattr(fake_frappe.defaults, "set_user_default")
            else:
                fake_frappe.defaults.set_user_default = original_set_user_default
            if original_clear_user_default is None:
                delattr(fake_frappe.defaults, "clear_user_default")
            else:
                fake_frappe.defaults.clear_user_default = original_clear_user_default

    def test_boot_default_home_sync_does_not_use_broad_user_get_all(self):
        source = Path(boot.__file__).read_text(encoding="utf-8")

        self.assertNotIn("frappe.get_all", source)
        self.assertIn('getattr(frappe, "get_list", None)', source)
        self.assertIn("PERSISTENT_DEFAULT_HOME_PAGE_RULES", source)
        self.assertIn("BOOT_HOME_PAGE_RULES", source)

    def test_managed_system_user_inventory_is_bounded_deterministic_and_fail_closed(self):
        original_get_list = fake_frappe.get_list
        calls = []

        def bounded_get_list(doctype, **kwargs):
            calls.append((doctype, kwargs))
            return ["accounts@example.com", "sales@example.com"]

        try:
            fake_frappe.get_list = bounded_get_list
            self.assertEqual(
                boot._managed_system_users(),
                ["accounts@example.com", "sales@example.com"],
            )
            self.assertEqual(calls[0][0], "User")
            self.assertEqual(calls[0][1]["order_by"], "name asc")
            self.assertEqual(calls[0][1]["limit_start"], 0)
            self.assertEqual(
                calls[0][1]["limit_page_length"],
                boot.MANAGED_SYSTEM_USER_MAX_ROWS + 1,
            )

            fake_frappe.get_list = lambda *args, **kwargs: [
                f"user-{index}@example.test"
                for index in range(boot.MANAGED_SYSTEM_USER_MAX_ROWS + 1)
            ]
            self.assertEqual(boot._managed_system_users(), [])
            fake_frappe.get_list = lambda *args, **kwargs: ["duplicate@example.test", "duplicate@example.test"]
            self.assertEqual(boot._managed_system_users(), [])
            fake_frappe.get_list = lambda *args, **kwargs: [""]
            self.assertEqual(boot._managed_system_users(), [])

            def denied_get_list(*args, **kwargs):
                raise fake_frappe.PermissionError("denied")

            fake_frappe.get_list = denied_get_list
            self.assertEqual(boot._managed_system_users(), [])
        finally:
            fake_frappe.get_list = original_get_list

    def test_non_finance_roles_do_not_receive_finance_control_desk_home(self):
        cases = (
            ("system@example.com", ["System Manager"]),
            ("executive@example.com", ["Executive Approver"]),
            ("sales-only@example.com", ["Sales User"]),
            ("purchase-only@example.com", ["Purchase User"]),
            ("warehouse-only@example.com", ["Warehouse Manager"]),
        )
        for user, roles in cases:
            with self.subTest(user=user):
                _set_user(user, roles)
                self.assertNotEqual(boot.resolve_default_home_page(user), "finance-control-desk")

    def test_workspace_home_priority_remains_sales_procurement_finance_then_warehouse(self):
        cases = (
            ("sales-finance@example.com", ["Sales User", "Accounts Manager"], "sales-console-home"),
            ("purchase-finance@example.com", ["Purchase User", "Accounts Manager"], "procurement-console-home"),
            ("warehouse-finance@example.com", ["Warehouse Manager", "Accounts User"], "finance-control-desk"),
            ("warehouse-only-priority@example.com", ["Warehouse Manager"], "warehouse-console"),
        )
        for user, roles, expected_home in cases:
            with self.subTest(user=user):
                _set_user(user, roles)
                self.assertEqual(boot.resolve_default_home_page(user), expected_home)

    def test_warehouse_home_is_blocked_for_admin_and_cross_workspace_roles(self):
        cases = (
            ("warehouse-admin@example.com", ["Warehouse Manager", "System Manager"], None),
            ("warehouse-accounts@example.com", ["Warehouse User", "Accounts User"], "finance-control-desk"),
            ("warehouse-sales@example.com", ["Warehouse Manager", "Sales User"], "sales-console-home"),
            ("warehouse-purchase@example.com", ["Stock User", "Purchase User"], "procurement-console-home"),
        )
        for user, roles, expected_home in cases:
            with self.subTest(user=user):
                _set_user(user, roles)
                self.assertFalse(boot.should_use_warehouse_console_home(user))
                if expected_home:
                    self.assertEqual(boot.resolve_default_home_page(user), expected_home)

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

    def test_procurement_sidebar_context_uses_procurement_title_and_order(self):
        payload = service.get_procurement_console_sidebar_context()

        self.assertEqual(payload["sidebar"]["title"], "Procurement Console")
        self.assertEqual(payload["sidebar"]["mode_label"], "Procurement Workspace")
        self.assertEqual(
            [item["label"] for item in payload["sidebar"]["items"]],
            ["Overview", "Suppliers", "Purchase Requests", "Purchase Orders", "RFQs", "Supplier Quotations", "Buying Items", "Reports"],
        )
        self.assertEqual(payload["sidebar"]["items"][-1]["target"], {"kind": "page", "route": "procurement-console-report"})
        self.assertNotIn("Quote Comparison", [item["label"] for item in payload["sidebar"]["items"]])

    def test_procurement_workspace_search_is_permission_aware_and_productized(self):
        payload = service.search_procurement_console_workspace("Alpha")

        self.assertEqual(payload["state"], "ready")
        self.assertTrue(payload["results"])
        self.assertTrue(all((item["target"] or {}).get("kind") == "worklist" for item in payload["results"]))
        self.assertTrue(any(item["doctype"] == "Supplier" for item in payload["results"]))


    def test_procurement_quick_find_returns_grouped_productized_previews(self):
        supplier_payload = service.get_procurement_quick_find_suggestions("Alpha")

        self.assertEqual(supplier_payload["state"], "ready")
        self.assertTrue(any(group["key"] == "suppliers" for group in supplier_payload["groups"]))
        supplier_result = next(item for item in supplier_payload["results"] if item["result_type"] == "supplier")
        self.assertEqual(supplier_result["target"], {"kind": "page", "route": "procurement-console-supplier", "route_parts": ["SUP-001"], "options": {}})
        self.assertEqual(supplier_result["preview"]["primary_action_label"], "Open supplier")
        self.assertIn("Supplier ID", [fact["label"] for fact in supplier_result["preview"]["facts"]])

        item_payload = service.get_procurement_quick_find_suggestions("Widget")
        self.assertEqual(item_payload["state"], "ready")
        self.assertTrue(any(item["result_type"] == "buying_item" for item in item_payload["results"]))
        self.assertTrue(any(item["result_type"] == "purchase_request" for item in item_payload["results"]))
        self.assertTrue(any(item["result_type"] == "purchase_order" for item in item_payload["results"]))

        report_payload = service.get_procurement_quick_find_suggestions("report")
        self.assertEqual(report_payload["state"], "ready")
        report_result = next(item for item in report_payload["results"] if item["result_type"] == "report")
        self.assertEqual(report_result["target"]["kind"], "report_page")
        self.assertTrue(str(report_result["target"]["report_key"]).startswith("procurement"))

        text = str([supplier_payload, item_payload, report_payload])
        self.assertNotIn("/desk/Form", text)
        self.assertNotIn("/app/", text)
        self.assertNotIn("Contact", text)
        self.assertNotIn("Email Queue", text)
        self.assertNotIn("Item Price", text)
        self.assertNotIn("Default Supplier", text)

    def test_procurement_quick_find_is_restricted_for_non_procurement_user(self):
        _set_user("sales@example.com", ["Sales User"])

        payload = service.get_procurement_quick_find_suggestions("Alpha")

        self.assertEqual(payload["state"], "restricted")
        self.assertEqual(payload["results"], [])

    def test_procurement_quick_find_does_not_change_bootstrap_or_directory_search_contract(self):
        bootstrap = service.get_procurement_console_bootstrap()
        self.assertNotIn("quick_find", bootstrap)
        self.assertNotIn("manager_readiness", bootstrap)

        directory_payload = service.search_procurement_console_workspace("Alpha")
        self.assertTrue(directory_payload["results"])
        self.assertTrue(all((item["target"] or {}).get("kind") == "worklist" for item in directory_payload["results"]))

    def test_procurement_quick_find_client_invalidates_stale_input_and_governs_targets(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "public"
            / "js"
            / "procurement_console"
            / "procurement_console_page.js"
        ).read_text()

        self.assertIn("function beginQuickFindRequest(query)", source)
        self.assertIn("function invalidateQuickFindRequests()", source)
        self.assertIn("function quickFindRequestCurrent(authority, query)", source)
        self.assertIn("function procurementTargetAllowed(target)", source)
        self.assertIn("const authority = beginQuickFindRequest($input.val());", source)
        self.assertIn("state.authority = authority;", source)
        self.assertIn("invalidateQuickFindRequests();", source)
        self.assertIn("function quickFindOpenCurrent(state, result, authority, query, connected, coordinator)", source)
        self.assertIn("renderQuickFindPreview($section, state, result, authority);", source)
        self.assertIn(
            "if (!quickFindOpenCurrent(state, result, authority, currentQuery, Boolean(sectionNode && sectionNode.isConnected))) return;",
            source,
        )
        self.assertIn("if (!quickFindRequestCurrent(authority, $input.val())) return;", source)
        self.assertIn("if (!procurementTargetAllowed(target)) return;", source)
        self.assertNotIn("requestSerial", source)
        for forbidden in (
            'target.kind === "new_doc"',
            'target.kind === "form"',
            'target.kind === "list"',
            'target.kind === "report"',
            'target.kind === "export"',
            'target.kind === "print"',
        ):
            self.assertNotIn(forbidden, source)

    def test_procurement_workspace_search_restricted_for_non_procurement_user(self):
        _set_user("sales@example.com", ["Sales User"])

        payload = service.search_procurement_console_workspace("Alpha")

        self.assertEqual(payload["state"], "restricted")
        self.assertEqual(payload["results"], [])

    def test_list_shell_supports_link_autocomplete_contract(self):
        shell_path = Path(__file__).resolve().parents[1] / "public" / "js" / "runtime" / "list_page" / "list_page_shell.js"
        source = shell_path.read_text()

        self.assertIn("data-erpw-list-link-doctype", source)
        self.assertIn("frappe.desk.search.search_link", source)
        self.assertIn("data-erpw-list-link-option", source)
        self.assertIn("ArrowDown", source)
        self.assertIn("ArrowUp", source)
        self.assertIn("erpw-list-filter-deck", source)
        self.assertIn("erpw-list-filter-main-row", source)
        self.assertIn("erpw-list-date-window-group", source)
        self.assertIn("erpw-list-command-action-cell", source)
        self.assertIn("grid-template-areas:", source)
        self.assertIn('"main actions"', source)
        self.assertIn('"secondary actions"', source)
        self.assertIn("main-count-4", source)
        self.assertIn('data-erpw-list-field-shell-key="date_start"', source)
        self.assertIn('data-erpw-list-field-shell-key="date_end"', source)
        self.assertIn("data-erpw-list-field-role", source)
        self.assertIn("data-erpw-list-field-group", source)
        self.assertIn("erpw-list-result-summary", source)
        self.assertIn("data-erpw-list-metric-count", source)
        self.assertIn("erpw-list-summary-side", source)
        self.assertIn("erpw-list-summary-facts", source)
        self.assertIn("is-procurement-worklist", source)
        self.assertIn("table-layout: auto", source)
        self.assertIn(".erpw-list-table tbody td:first-child .erpw-list-inline-open-label", source)
        self.assertIn("overflow-wrap: normal", source)
        self.assertIn(".erpw-list-cell-value", source)
        self.assertIn("display: block", source)
        self.assertIn("@media (max-width: 1366px)", source)
        self.assertIn("grid-template-columns: minmax(0, 1fr) max-content", source)
        self.assertIn('"main main"', source)
        self.assertIn('"main actions"', source)
        self.assertIn("has-actions:not(.has-date-window)", source)
        self.assertIn("justify-content: flex-end", source)
        self.assertIn("align-items: flex-end", source)
        self.assertIn("min-height: 0", source)
        self.assertIn("renderSummary(page.summary, page.controls, page.metrics, page)", source)
        self.assertIn("renderMetrics(page.metrics, { integrated: Boolean(page.summary && page.summary.title) })", source)

        css_source = (Path(__file__).resolve().parents[1] / "public" / "css" / "erp_workspace_ui.css").read_text()
        self.assertIn(".erpw-list-table tbody td:first-child .erpw-list-cell-value", css_source)
        self.assertIn("hyphens: manual", css_source)

        page_source = (Path(__file__).resolve().parents[1] / "erp_workspace_ui" / "page" / "procurement_console_worklist" / "procurement_console_worklist.js").read_text()
        self.assertIn('workspace: "procurement"', page_source)

        report_shell_source = (Path(__file__).resolve().parents[1] / "public" / "js" / "runtime" / "report_page" / "report_page_shell.js").read_text()
        self.assertIn("is-procurement-report", report_shell_source)
        self.assertIn("applyWorkspaceMode", report_shell_source)
        self.assertIn("erpw-report-command-actions", report_shell_source)

        report_page_source = (Path(__file__).resolve().parents[1] / "erp_workspace_ui" / "page" / "procurement_console_report" / "procurement_console_report.js").read_text()
        self.assertIn('workspace: "procurement"', report_page_source)

    def test_po_follow_up_detail_loads_shared_runtime_contract(self):
        public_path = Path(__file__).resolve().parents[1] / "public" / "js" / "procurement_console" / "procurement_console_po_follow_up_page.js"
        supplier_public_path = Path(__file__).resolve().parents[1] / "public" / "js" / "procurement_console" / "procurement_console_supplier_page.js"
        item_public_path = Path(__file__).resolve().parents[1] / "public" / "js" / "procurement_console" / "procurement_console_item_page.js"
        overview_public_path = Path(__file__).resolve().parents[1] / "public" / "js" / "procurement_console" / "procurement_console_page.js"
        page_path = Path(__file__).resolve().parents[1] / "erp_workspace_ui" / "page" / "procurement_console_po_follow_up" / "procurement_console_po_follow_up.js"
        report_page_path = Path(__file__).resolve().parents[1] / "erp_workspace_ui" / "page" / "procurement_console_report" / "procurement_console_report.js"
        boot_path = Path(__file__).resolve().parents[1] / "public" / "js" / "erp_workspace_ui_boot.js"
        source = public_path.read_text()
        supplier_source = supplier_public_path.read_text()
        item_source = item_public_path.read_text()
        overview_source = overview_public_path.read_text()
        page_source = page_path.read_text()
        report_page_source = report_page_path.read_text()
        boot_source = boot_path.read_text()

        self.assertIn("makeConsolePage", overview_source)
        self.assertIn("erpw-direct-console-body", overview_source)
        self.assertIn("__erpwProcurementConsole", overview_source)
        self.assertIn("procurement-console-supplier", supplier_source)
        self.assertIn("get_supplier_detail_context", supplier_source)
        self.assertIn("Buying contacts", supplier_source)
        self.assertIn("supplier_directory", supplier_source)
        self.assertIn("procurement-console-item", item_source)
        self.assertIn("get_item_detail_context", item_source)
        self.assertIn("Supplier price review", item_source)
        self.assertIn("buying_item_directory", item_source)
        self.assertIn("&rarr;", item_source)
        self.assertNotIn("erpw-procurement-table-link", item_source)
        self.assertNotIn('aria-hidden="true">?</span>', item_source)
        self.assertIn("cleanupManagedPageChrome", item_source)
        self.assertIn("routeToPurchaseOrderFollowUp", supplier_source)
        self.assertIn("&rarr;", supplier_source)
        self.assertNotIn("erpw-procurement-table-link", supplier_source)
        self.assertIn("cleanupManagedPageChrome", supplier_source)
        self.assertIn("cleanupManagedPageChrome", source)
        self.assertIn("CHILD_PAGE_RUNTIME_URLS", source)
        self.assertIn("child_page_shell_content.js", source)
        self.assertIn("ensureDetailRuntime", source)
        self.assertIn("defaultActionIconMarkup", (Path(__file__).resolve().parents[1] / "public" / "js" / "runtime" / "child_page" / "child_page_shell_content.js").read_text())
        self.assertIn("erpw-child-toolbar-action", (Path(__file__).resolve().parents[1] / "public" / "js" / "runtime" / "child_page" / "child_page_shell_content.js").read_text())
        self.assertIn("makeFallbackPage", source)
        self.assertIn("erpw-direct-child-body", source)
        self.assertIn("frappe.require", source)
        self.assertNotIn("Detail runtime unavailable", source)
        self.assertIn("procurement_console_po_follow_up_page.js", page_source)
        self.assertIn("cleanupDuplicateReportChrome", report_page_source)
        self.assertIn("Procurement Console Report", report_page_source)
        self.assertIn("PROCUREMENT_DIRECT_PAGE_ASSETS", boot_source)
        self.assertIn("procurement_console_page.js", boot_source)
        self.assertIn("ensureProcurementDirectPage", boot_source)
        self.assertIn("procurementDirectPageWrapper(pageKey, pageDef)", boot_source)
        self.assertIn("pageDef.page_name === pageKey", boot_source)
        self.assertIn("document.getElementById(\"body\")", boot_source)
        self.assertIn("__erpwProcurementConsole", boot_source)
        self.assertIn("__erpwProcurementSupplierDetail", boot_source)
        self.assertIn("__erpwProcurementItemDetail", boot_source)
        self.assertIn("existing.routeSignature === routeSignature", boot_source)
        self.assertIn("procurementRouteShellCount(pageKey) === 1", boot_source)
        self.assertIn("cleanupProcurementRouteShells(pageKey, { removeActive: true })", boot_source)
        self.assertIn("loadProcurementDirectPageAsset", boot_source)
        self.assertIn("document.createElement(\"script\")", boot_source)
        self.assertIn("bindProcurementDirectRouteWatch", boot_source)
        self.assertIn("missingShell = procurementRouteShellCount(pageKey) === 0", boot_source)
        self.assertIn("if (pathRouteParts.length && pathPageKey) return pathRouteParts;", boot_source)
        self.assertNotIn("?v=procurement", boot_source)
        self.assertNotIn("frappe.require(asset", boot_source)
        self.assertIn("procurement-console-po-follow-up", boot_source)
        self.assertIn("procurement-console-supplier", boot_source)
        self.assertIn("procurement-console-item", boot_source)

    def test_procurement_boot_runtime_has_role_home_fallback(self):
        boot_path = Path(__file__).resolve().parents[1] / "public" / "js" / "erp_workspace_ui_boot.js"
        source = boot_path.read_text()

        self.assertIn("function routeToRoleHome", source)
        self.assertIn("Purchase Manager", source)
        self.assertIn('frappe.set_route("procurement-console-home")', source)
        self.assertIn('salesWorkspaceRoute("launcher", "sales-console-home")', source)
        self.assertIn('frappe.set_route("finance-control-desk")', source)
        self.assertIn("hasWarehouseOperationalHomeRole", source)
        self.assertIn("hasWarehouseDeskBypassRole", source)
        self.assertIn('frappe.set_route("warehouse-console")', source)
        self.assertIn("scheduleRoleHomeRedirect", source)
        self.assertLess(
            source.index('salesWorkspaceRoute("launcher", "sales-console-home")'),
            source.index('frappe.set_route("procurement-console-home")'),
        )
        self.assertLess(
            source.index('frappe.set_route("procurement-console-home")'),
            source.index('frappe.set_route("finance-control-desk")'),
        )
        self.assertLess(
            source.index('frappe.set_route("finance-control-desk")'),
            source.index('frappe.set_route("warehouse-console")'),
        )

    def test_phase3_smoke_covers_direct_po_follow_up_route(self):
        smoke_path = Path(__file__).resolve().parents[2] / "ui_smoke" / "procurement_phase3_smoke.js"
        source = smoke_path.read_text()

        self.assertIn("ERPW_PROCUREMENT_DIRECT_PO_NAME", source)
        self.assertIn("PUR-ORD-2026-00010", source)
        self.assertIn('worklistPayload(page, "purchase_order_directory")', source)
        self.assertIn('process.env.ERPW_PROCUREMENT_DIRECT_PO_NAME || firstPoName || "PUR-ORD-2026-00010"', source)
        self.assertIn("data-erpw-report-link-option", source)
        self.assertIn("checkProcurementOverviewNavigationLifecycle", source)
        self.assertIn("assertSingleProcurementShell", source)
        self.assertIn("waitForFunction((shellKey)", source)
        self.assertIn("old Procurement Overview remains visible", source)
        self.assertIn("multiple Procurement shells are visible", source)
        self.assertIn("sales-console-action[data-erpw-procurement-create-action]", source)
        self.assertIn("still use child-page action styling", source)
        self.assertIn("checkProcurementBackForwardLifecycle", source)
        self.assertIn("New Purchase Request must use the managed Phase 5A page route", source)
        self.assertIn("Overview and Purchase Requests directory must route to the same managed PR form", source)
        self.assertIn("New RFQ must use the managed Phase 5B page route", source)
        self.assertIn("Overview and RFQ Directory must route to the same managed RFQ form", source)
        self.assertIn("Open ERP Form must not appear before a managed Purchase Request draft is saved", source)
        self.assertIn("New RFQ must use the managed Phase 5B page route", source)
        self.assertIn("Overview and RFQ Directory must route to the same managed RFQ form", source)
        self.assertIn("New Supplier Quotation must use the managed Phase 5C page route", source)
        self.assertIn("Overview and Supplier Quotations Directory must route to the same managed Supplier Quotation form", source)
        self.assertIn("must remain a governed native exception", source)
        self.assertIn("new_purchase_request", source)
        self.assertIn("Repeated navigation", source)
        self.assertIn("PO Follow-up Detail direct route", source)
        self.assertIn("Supplier Detail direct route", source)
        self.assertIn("Buying Item Detail direct route", source)
        self.assertIn("Pipeline Billing Visibility", source)
        self.assertIn("Detail runtime unavailable", source)
        self.assertIn("Receipt posture", source)
        self.assertIn("Billing posture", source)

    def test_procurement_create_actions_use_shared_action_cards(self):
        source = (Path(__file__).resolve().parents[1] / "public" / "js" / "procurement_console" / "procurement_console_page.js").read_text()
        css_source = (Path(__file__).resolve().parents[1] / "public" / "css" / "erp_workspace_ui.css").read_text()

        self.assertIn("makeAction({", source)
        self.assertIn("sales-console-action-strip primary", source)
        self.assertIn("data-erpw-procurement-create-action", source)
        self.assertIn("data-erpw-procurement-create-variant", source)
        self.assertIn("maxPrimaryActions: 4", source)
        self.assertIn("primaryColumns: primaryCount === 4 ? 2 : 0", source)
        self.assertNotIn("erpw-child-action secondary erpw-procurement-create-action", source)
        self.assertIn("Shared workspace action cards", css_source)
        self.assertIn(".sales-console-action", css_source)
        self.assertIn(".sales-console-action-strip.primary", css_source)

    def test_procurement_pages_call_route_cleanup_contract(self):
        paths = [
            Path(__file__).resolve().parents[1] / "public" / "js" / "procurement_console" / "procurement_console_page.js",
            Path(__file__).resolve().parents[1] / "erp_workspace_ui" / "page" / "procurement_console_worklist" / "procurement_console_worklist.js",
            Path(__file__).resolve().parents[1] / "erp_workspace_ui" / "page" / "procurement_console_report" / "procurement_console_report.js",
            Path(__file__).resolve().parents[1] / "public" / "js" / "procurement_console" / "procurement_console_po_follow_up_page.js",
            Path(__file__).resolve().parents[1] / "public" / "js" / "procurement_console" / "procurement_console_supplier_page.js",
            Path(__file__).resolve().parents[1] / "public" / "js" / "procurement_console" / "procurement_console_item_page.js",
        ]
        for path in paths:
            source = path.read_text()
            self.assertIn("cleanupProcurementRouteShells(PAGE_KEY, { removeActive: true })", source, str(path))
            self.assertIn("pruneProcurementRouteShells", source, str(path))

    def test_procurement_overview_uses_dynamic_shared_console_runtime(self):
        source = (Path(__file__).resolve().parents[1] / "public" / "js" / "procurement_console" / "procurement_console_page.js").read_text()

        self.assertIn('data-erpw-workspace="procurement"', source)
        self.assertIn("function consoleRuntime()", source)
        self.assertIn("window.erpWorkspaceConsoleRuntime || {}", source)
        self.assertIn("const method = consoleRuntime()[name]", source)
        self.assertNotIn("const consoleRuntime = window.erpWorkspaceConsoleRuntime || {}", source)

    def test_procurement_detail_asset_loaders_use_frappe_require_contract(self):
        public_js = Path(__file__).resolve().parents[1] / "public" / "js" / "procurement_console"
        for filename in [
            "procurement_console_po_follow_up_page.js",
            "procurement_console_supplier_page.js",
            "procurement_console_item_page.js",
        ]:
            source = (public_js / filename).read_text()
            self.assertIn("frappe.require(url, () =>", source, filename)
            self.assertNotIn("Could not load shared detail runtime", source, filename)
            self.assertNotIn("frappe.require(url, () => resolve(), (error)", source, filename)
            self.assertNotIn("?v=procurement", source, filename)

    def test_procurement_routes_do_not_null_native_route_options(self):
        paths = [
            Path(__file__).resolve().parents[1] / "public" / "js" / "runtime" / "console" / "workspace_console_sidebar.js",
            Path(__file__).resolve().parents[1] / "erp_workspace_ui" / "page" / "procurement_console" / "procurement_console.js",
            Path(__file__).resolve().parents[1] / "erp_workspace_ui" / "page" / "procurement_console_worklist" / "procurement_console_worklist.js",
            Path(__file__).resolve().parents[1] / "erp_workspace_ui" / "page" / "procurement_console_report" / "procurement_console_report.js",
            Path(__file__).resolve().parents[1] / "erp_workspace_ui" / "page" / "procurement_console_po_follow_up" / "procurement_console_po_follow_up.js",
        ]
        for path in paths:
            self.assertNotIn("frappe.route_options = null", path.read_text(), str(path))

    def test_shared_console_styles_are_global_asset_contract(self):
        css_path = Path(__file__).resolve().parents[1] / "public" / "css" / "erp_workspace_ui.css"
        source = css_path.read_text()

        self.assertIn("Shared console workbench styles", source)
        self.assertIn(".sales-console-card", source)
        self.assertIn(".sales-console-kpi-card", source)
        self.assertIn(".sales-console-queue-grid", source)
        self.assertIn(".sales-console-action", source)
        self.assertIn(".sales-console-action-strip", source)
        self.assertIn('data-section-grid="buying-pipeline"', source)
        self.assertIn("counter-reset: erpw-pipeline-step", source)
        self.assertIn("appearance: none", source)
        self.assertIn("grid-template-columns", source)

    def test_procurement_direct_page_asset_load_retries_when_shell_missing(self):
        boot_path = Path(__file__).resolve().parents[1] / "public" / "js" / "erp_workspace_ui_boot.js"
        source = boot_path.read_text()
        self.assertNotIn('if (procurementDirectPageLoads[pageKey]) return true;', source)
        self.assertIn('if (procurementDirectPageLoads[pageKey]) {', source)
        self.assertIn('procurementRouteShellCount(pageKey) === 0', source)
        self.assertIn('renderProcurementDirectPage(pageKey);', source)

    def test_procurement_sidebar_target_resolution_bypasses_sales_child_helper(self):
        sidebar_path = Path(__file__).resolve().parents[1] / "public" / "js" / "runtime" / "console" / "workspace_console_sidebar.js"
        source = sidebar_path.read_text()
        execute_target = source[source.index("  function executeTarget(target)"):source.index("  function resetSearchTimer()")]

        self.assertIn('const config = workspaceConfig(getRoute());', execute_target)
        self.assertIn('config.workspaceId === "sales"', execute_target)
        self.assertIn('routeToSalesConsoleTarget(target)', execute_target)
        self.assertLess(execute_target.index('config.workspaceId === "sales"'), execute_target.index('routeToSalesConsoleTarget(target)'))
        self.assertIn('function workspaceFromRouteKey(routeKey)', source)
        self.assertIn('pageKey.indexOf("procurement-console") === 0', source)
        self.assertIn('if (inferredId) return workspaceFromRegistry(inferredId) || { workspaceId: inferredId };', source)
        self.assertNotIn('const workspaceRegistry = root.erpWorkspaceUiWorkspaceRegistry || {};', source)
        self.assertIn('frappe.set_route(config.worklistRoute, normalizedQueueKey)', source)
        self.assertIn('const slug = String(reportKey || "").replace(/_/g, "-");', source)
        self.assertIn('frappe.set_route(config.reportRoute, slug)', source)
        self.assertIn('fallbackToProcurementManagedRoute(config, config.reportRoute, slug, ".erpw-report-shell")', source)
        self.assertGreaterEqual(source.count('event.stopImmediatePropagation'), 3)
        self.assertNotIn('target.kind === "new_doc"', execute_target)
        self.assertNotIn('target.kind === "form"', execute_target)
        self.assertNotIn('target.kind === "list"', execute_target)
        self.assertNotIn('target.kind === "report"', execute_target)
        browser_exports = source[source.index("root.erpWorkspaceConsoleSidebar = Object.assign"):]
        self.assertNotIn("\n    executeTarget,", browser_exports)
        self.assertIn("\n    executeSidebarTarget,", browser_exports)
        child_actions = (
            Path(__file__).resolve().parents[1]
            / "public"
            / "js"
            / "runtime"
            / "child_page"
            / "child_page_operating_actions.js"
        ).read_text()
        self.assertIn("sidebar.executeSidebarTarget", child_actions)
        self.assertNotIn("sidebar.executeTarget", child_actions)

    def test_supplier_directory_uses_ready_read_only_list_contract(self):
        payload = worklist.get_procurement_console_worklist_context("supplier_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["refresh", "reset_filters", "apply_filters"])
        self.assertIn("Read-only supplier detail", payload["controls"]["scopeChips"])
        self.assertEqual(_field_by_key(payload, "supplier")["type"], "link")
        self.assertEqual(_field_by_key(payload, "supplier")["linkDoctype"], "Supplier")
        self.assertEqual(_field_by_key(payload, "supplier_group")["type"], "link")
        self.assertEqual(_field_by_key(payload, "supplier_group")["linkDoctype"], "Supplier Group")
        self.assertEqual(payload["results"]["rows"][0]["actions"], [{"key": "open_record", "label": "Open"}])
        self.assertNotIn("create_supplier", str(payload))
        self.assertEqual(payload["action_targets"]["row:SUP-001:open_record"]["kind"], "page")
        self.assertEqual(payload["action_targets"]["row:SUP-001:open_record"]["route"], "procurement-console-supplier")
        self.assertEqual(payload["action_targets"]["row:SUP-001:open_record"]["route_parts"], ["SUP-001"])

    def test_supplier_detail_is_productized_and_permission_aware(self):
        payload = supplier_detail.get_supplier_detail_context("SUP-001")

        self.assertEqual(payload["detail"]["state"]["kind"], "ready")
        self.assertEqual(payload["summary"]["title"], "Alpha Supplier")
        self.assertEqual(payload["detail"]["supplier"]["supplier_group"], "All Supplier Groups")
        self.assertEqual(payload["detail"]["recent_purchase_orders"]["rows"][0]["key"], "PUR-DUE-001")
        recent_po_cell = payload["detail"]["recent_purchase_orders"]["rows"][0]["cells"]["purchase_order"]
        self.assertEqual(recent_po_cell["route"], "procurement-console-po-follow-up")
        self.assertEqual(recent_po_cell["route_parts"], ["PUR-DUE-001"])
        open_po_cell = payload["detail"]["open_purchase_orders"]["rows"][0]["cells"]["purchase_order"]
        self.assertEqual(open_po_cell["route"], "procurement-console-po-follow-up")
        self.assertEqual(open_po_cell["route_parts"], ["PUR-DUE-001"])
        self.assertEqual(payload["detail"]["rfqs"]["rows"][0]["key"], "RFQ-001")
        self.assertEqual(payload["detail"]["supplier_quotations"]["rows"][0]["key"], "SUP-QTN-001")
        self.assertEqual(payload["action_targets"]["back_to_suppliers"]["kind"], "worklist")
        self.assertNotIn("open_supplier_form", payload["action_targets"])
        self.assertTrue(
            any(
                call["doctype"] == "Supplier"
                and _filter_contains(call["filters"], ["Supplier", "name", "=", "SUP-001"])
                for call in CAPTURED_GET_LIST_CALLS
            )
        )
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_supplier_detail_does_not_load_children_when_parent_not_visible(self):
        CAPTURED_GET_LIST_CALLS.clear()
        CAPTURED_GET_ALL_CALLS.clear()

        payload = supplier_detail.get_supplier_detail_context("SUP-HIDDEN")

        self.assertEqual(payload["detail"]["state"]["kind"], "unavailable")
        self.assertEqual(payload["detail"]["state"]["title"], "Supplier not found")
        self.assertTrue(
            any(
                call["doctype"] == "Supplier"
                and _filter_contains(call["filters"], ["Supplier", "name", "=", "SUP-HIDDEN"])
                for call in CAPTURED_GET_LIST_CALLS
            )
        )
        self.assertFalse(
            any(
                call["doctype"] in {"Purchase Order", "Request for Quotation", "Supplier Quotation", "Contact"}
                for call in CAPTURED_GET_LIST_CALLS
            )
        )
        self.assertFalse(any(call["doctype"] in {"Request for Quotation Supplier", "Dynamic Link"} for call in CAPTURED_GET_ALL_CALLS))

    def test_supplier_detail_does_not_expose_native_form_escape_for_procurement_roles(self):
        for user, roles in (
            ("manager@example.com", ["Purchase Manager"]),
            ("purchase@example.com", ["Purchase User"]),
            ("master@example.com", ["Purchase Master Manager"]),
        ):
            with self.subTest(user=user):
                _set_user(user, roles)
                _set_writeable_doctypes("Supplier")

                payload = supplier_detail.get_supplier_detail_context("SUP-001")

                self.assertNotIn("open_supplier_form", payload["action_targets"])
                self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["back_to_suppliers", "refresh"])
                self.assertNotIn("Open ERP Supplier Form", str(payload))

    def test_supplier_readiness_profile_is_manager_editable_and_audited(self):
        _set_user("manager@example.com", ["Purchase Manager"])

        payload = supplier_readiness.save_supplier_readiness_profile(
            "SUP-001",
            {
                "buying_readiness_status": "Ready",
                "preferred_rfq_contact": "CONT-001",
                "rfq_recipient_email_override": "sourcing@example.com",
                "buying_note": "Use negotiated packaging.",
                "readiness_note": "",
            },
        )

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(SUPPLIER_READINESS_PROFILES["SUP-001"]["rfq_recipient_email_override"], "sourcing@example.com")
        self.assertEqual(SUPPLIER_READINESS_PROFILES["SUP-001"]["preferred_rfq_contact"], "CONT-001")
        self.assertEqual(len(SUPPLIER_READINESS_LOGS), 1)
        self.assertIn("rfq_recipient_email_override", SUPPLIER_READINESS_LOGS[0]["changed_fields"])
        detail = supplier_detail.get_supplier_detail_context("SUP-001")
        self.assertTrue(detail["detail"]["buying_profile"]["can_edit"])
        self.assertEqual(detail["detail"]["buying_profile"]["recipient"]["email"], "sourcing@example.com")
        self.assertNotIn("Open ERP Supplier Form", str(detail))

    def test_supplier_readiness_profile_is_read_only_for_purchase_user(self):
        _set_user("purchase@example.com", ["Purchase User"])

        payload = supplier_readiness.save_supplier_readiness_profile("SUP-001", {"buying_readiness_status": "Ready"})

        self.assertEqual(payload["state"]["kind"], "restricted")
        self.assertEqual({}, SUPPLIER_READINESS_PROFILES)
        detail = supplier_detail.get_supplier_detail_context("SUP-001")
        self.assertFalse(detail["detail"]["buying_profile"]["can_edit"])
        self.assertIn("Purchase Manager", detail["detail"]["buying_profile"]["read_only_reason"])

    def test_supplier_readiness_rejects_unknown_forbidden_invalid_and_unlinked_payload(self):
        _set_user("manager@example.com", ["Purchase Manager"])

        cases = [
            {"supplier_group": "Services"},
            {"unexpected_field": "x"},
            {"rfq_recipient_email_override": "not-an-email"},
            {"preferred_rfq_contact": "CONT-999"},
            {"buying_readiness_status": "Needs email", "readiness_note": ""},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                response = supplier_readiness.save_supplier_readiness_profile("SUP-001", payload)
                self.assertEqual(response["state"]["kind"], "error")
        self.assertEqual({}, SUPPLIER_READINESS_PROFILES)
        self.assertEqual([], SUPPLIER_READINESS_LOGS)

    def test_supplier_readiness_hold_blocks_rfq_readiness_without_send_side_effects(self):
        _set_user("manager@example.com", ["Purchase Manager"])
        supplier_readiness.save_supplier_readiness_profile(
            "SUP-001",
            {
                "buying_readiness_status": "Hold for sourcing",
                "preferred_rfq_contact": "CONT-001",
                "rfq_recipient_email_override": "",
                "buying_note": "",
                "readiness_note": "Supplier paused by buyer.",
            },
        )

        context = document_output.get_rfq_send_readiness_context("PUR-RFQ-MULTI")

        statuses = {row["supplier"]: row for row in context["suppliers"]}
        self.assertEqual(statuses["SUP-001"]["readiness_status"], "blocked")
        self.assertEqual(statuses["SUP-001"]["readiness_label"], "Hold for sourcing")
        self.assertIn("Supplier paused", statuses["SUP-001"]["reason"])
        self.assertFalse(context["can_send"])
        self.assertEqual(context["summary"]["blocked"], 1)
        self.assertEqual([], [row for row in SUPPLIER_READINESS_LOGS if row.get("doctype") in {"Communication", "Email Queue"}])
        self.assertEqual({}, SAVED_SUPPLIER_QUOTATIONS)
        self.assertEqual({}, SAVED_PURCHASE_ORDERS)

    def test_supplier_readiness_override_feeds_rfq_recipient_context(self):
        _set_user("manager@example.com", ["Purchase Manager"])
        EMAIL_ACCOUNTS.append({"name": "Buying", "email_id": "buying@example.com", "enable_outgoing": 1, "default_outgoing": 1, "awaiting_password": 0})
        supplier_readiness.save_supplier_readiness_profile(
            "SUP-001",
            {
                "buying_readiness_status": "Ready",
                "preferred_rfq_contact": "",
                "rfq_recipient_email_override": "rfq.override@example.com",
                "buying_note": "",
                "readiness_note": "",
            },
        )

        context = document_output.get_rfq_send_readiness_context("PUR-RFQ-MULTI")

        statuses = {row["supplier"]: row for row in context["suppliers"]}
        self.assertEqual(statuses["SUP-001"]["email"], "rfq.override@example.com")
        self.assertEqual(statuses["SUP-001"]["email_source"], "readiness_override")
        self.assertEqual(statuses["SUP-001"]["readiness_status"], "ready")
        self.assertFalse(context["can_send"])


    def test_supplier_readiness_infers_known_trading_record_without_profile(self):
        context = readiness.get_supplier_readiness_context("SUP-001")
        chip = supplier_readiness.supplier_readiness_chip("SUP-001")

        self.assertEqual(context["issues"][0]["severity"], "ready")
        self.assertEqual(context["issues"][0]["title"], readiness_evidence.SUPPLIER_KNOWN_TRADING_LABEL)
        self.assertEqual(chip["value"], readiness_evidence.SUPPLIER_KNOWN_TRADING_LABEL)
        self.assertTrue(readiness_evidence.supplier_evidence("SUP-001")["has_linked_contact_email"])

    def test_supplier_readiness_warns_for_new_supplier_without_history(self):
        context = readiness.get_supplier_readiness_context("SUP-NEW")

        self.assertEqual(context["issues"][0]["severity"], "warning")
        self.assertEqual(context["issues"][0]["title"], readiness_evidence.SUPPLIER_NEW_REVIEW_LABEL)

    def test_supplier_readiness_manual_hold_overrides_history(self):
        _set_user("manager@example.com", ["Purchase Manager"])
        supplier_readiness.save_supplier_readiness_profile(
            "SUP-001",
            {
                "buying_readiness_status": "Hold for sourcing",
                "preferred_rfq_contact": "CONT-001",
                "rfq_recipient_email_override": "",
                "buying_note": "",
                "readiness_note": "Paused for sourcing review.",
            },
        )

        context = readiness.get_supplier_readiness_context("SUP-001")

        self.assertEqual(context["issues"][0]["severity"], "critical")
        self.assertIn("hold", context["issues"][0]["title"].lower())

    def test_manager_readiness_excludes_historical_no_profile_supplier_item(self):
        _set_user("manager@example.com", ["Purchase Manager"])

        queue = readiness.get_procurement_manager_readiness()
        titles = [issue["title"] for issue in queue["issues"]]

        self.assertNotIn("Supplier profile not reviewed", titles)
        self.assertNotIn("Item buying context not reviewed", titles)
        self.assertNotIn(readiness_evidence.SUPPLIER_KNOWN_TRADING_LABEL, titles)
        self.assertNotIn(readiness_evidence.ITEM_EXISTING_BUYING_LABEL, titles)

    def test_supplier_detail_restricted_for_finance_executive_only(self):
        _set_user("approver@example.com", ["Finance Lead Approver", "Executive Approver"])

        payload = supplier_detail.get_supplier_detail_context("SUP-001")

        self.assertEqual(payload["detail"]["state"]["kind"], "restricted")

    def test_buying_item_directory_is_read_only_and_productized(self):
        payload = worklist.get_procurement_console_worklist_context("buying_item_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual(_field_by_key(payload, "item")["linkDoctype"], "Item")
        self.assertEqual(_field_by_key(payload, "item_group")["linkDoctype"], "Item Group")
        self.assertEqual(payload["results"]["rows"][0]["actions"], [{"key": "open_record", "label": "Open"}])
        self.assertEqual(payload["action_targets"]["row:ITEM-001:open_record"]["kind"], "page")
        self.assertEqual(payload["action_targets"]["row:ITEM-001:open_record"]["route"], "procurement-console-item")
        self.assertTrue(any(call["doctype"] == "Item" and _filter_contains(call["filters"], ["Item", "is_purchase_item", "=", 1]) for call in CAPTURED_GET_LIST_CALLS))
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_buying_item_detail_is_read_only_productized_context(self):
        payload = items.get_item_detail_context("ITEM-001")

        self.assertEqual(payload["detail"]["state"]["kind"], "ready")
        self.assertEqual(payload["summary"]["title"], "Widget")
        self.assertEqual(payload["detail"]["item_suppliers"]["rows"][0]["cells"]["supplier"], "SUP-001")
        self.assertEqual(payload["detail"]["item_prices"]["rows"][0]["cells"]["rate"], "1,000 MMK")
        self.assertEqual(payload["detail"]["supplier_quotations"]["rows"][0]["key"], "SUP-QTN-001")
        self.assertEqual(payload["detail"]["purchase_orders"]["rows"][0]["key"], "PUR-DUE-001")
        po_cell = payload["detail"]["purchase_orders"]["rows"][0]["cells"]["purchase_order"]
        self.assertEqual(po_cell["route"], "procurement-console-po-follow-up")
        self.assertEqual(po_cell["route_parts"], ["PUR-DUE-001"])
        self.assertEqual(payload["action_targets"]["back_to_items"], {"kind": "worklist", "queue_key": "buying_item_directory"})
        self.assertNotIn("open_item_form", payload["action_targets"])
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_buying_item_detail_parent_visibility_is_enforced_before_children(self):
        CAPTURED_GET_LIST_CALLS.clear()
        CAPTURED_GET_ALL_CALLS.clear()

        payload = items.get_item_detail_context("ITEM-HIDDEN")

        self.assertEqual(payload["detail"]["state"]["kind"], "unavailable")
        self.assertEqual(payload["detail"]["state"]["title"], "Item not found")
        self.assertTrue(
            any(
                call["doctype"] == "Item"
                and _filter_contains(call["filters"], ["Item", "name", "=", "ITEM-HIDDEN"])
                for call in CAPTURED_GET_LIST_CALLS
            )
        )
        self.assertFalse(any(call["doctype"] in {"Item Supplier", "Supplier Quotation Item", "Purchase Order Item"} for call in CAPTURED_GET_ALL_CALLS))

    def test_buying_item_detail_does_not_expose_native_form_escape_for_procurement_roles(self):
        for user, roles in (
            ("master@example.com", ["Purchase Master Manager"]),
            ("manager@example.com", ["Purchase Manager"]),
            ("purchase@example.com", ["Purchase User"]),
        ):
            with self.subTest(user=user):
                _set_user(user, roles)
                _set_writeable_doctypes("Item")

                payload = items.get_item_detail_context("ITEM-001")

                self.assertNotIn("open_item_form", payload["action_targets"])
                self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["back_to_items", "refresh"])
                self.assertNotIn("Open ERP Item Form", str(payload))

    def test_item_buying_profile_is_manager_editable_and_audited(self):
        _set_user("manager@example.com", ["Purchase Manager"])

        payload = item_buying_profile.save_item_buying_profile(
            "ITEM-001",
            {
                "buying_readiness_status": "Ready for buying",
                "preferred_existing_supplier": "SUP-001",
                "supplier_part_no_context": "SUP-WIDGET-CTX",
                "procurement_lead_time_days": 12,
                "minimum_order_qty_context": 24,
                "buying_note": "Use controlled packaging.",
                "readiness_note": "Ready after sourcing review.",
            },
        )

        self.assertEqual(payload["state"]["kind"], "ready")
        self.assertEqual(ITEM_BUYING_PROFILES["ITEM-001"]["buying_readiness_status"], "Ready for buying")
        self.assertEqual(ITEM_BUYING_PROFILES["ITEM-001"]["preferred_existing_supplier"], "SUP-001")
        self.assertEqual(ITEM_BUYING_PROFILES["ITEM-001"]["supplier_part_no_context"], "SUP-WIDGET-CTX")
        self.assertEqual(len(ITEM_BUYING_LOGS), 1)
        self.assertIn("preferred_existing_supplier", ITEM_BUYING_LOGS[0]["change_summary"])
        detail = items.get_item_detail_context("ITEM-001")
        self.assertTrue(detail["detail"]["buying_profile"]["can_edit"])
        self.assertEqual(detail["detail"]["buying_profile"]["readiness_label"], "Reviewed for buying")
        directory = items.build_buying_item_directory({})
        self.assertEqual(directory["results"]["columns"][3]["key"], "readiness")
        self.assertEqual(directory["results"]["rows"][0]["cells"]["readiness"]["value"], "Reviewed for buying")
        self.assertNotIn("Open ERP Item Form", str(detail))
        self.assertEqual({}, SAVED_PURCHASE_ORDERS)
        self.assertEqual({}, SAVED_SUPPLIER_QUOTATIONS)
        self.assertEqual([], [row for row in ITEM_BUYING_LOGS if row.get("doctype") in {"Communication", "Email Queue"}])


    def test_item_readiness_infers_existing_buying_activity_without_profile(self):
        context = readiness.get_item_buying_readiness_context("ITEM-001")
        chip = item_buying_profile.item_readiness_chip("ITEM-001")

        self.assertEqual(context["issues"][0]["severity"], "ready")
        self.assertEqual(context["issues"][0]["title"], readiness_evidence.ITEM_EXISTING_BUYING_LABEL)
        self.assertEqual(chip["value"], readiness_evidence.ITEM_EXISTING_BUYING_LABEL)

    def test_item_readiness_infers_existing_receipt_or_invoice_activity_without_profile(self):
        context = readiness.get_item_buying_readiness_context("ITEM-RECEIVED")
        chip = item_buying_profile.item_readiness_chip("ITEM-RECEIVED")
        evidence = readiness_evidence.item_evidence("ITEM-RECEIVED")

        self.assertEqual(context["issues"][0]["severity"], "ready")
        self.assertEqual(context["issues"][0]["title"], readiness_evidence.ITEM_EXISTING_BUYING_LABEL)
        self.assertEqual(chip["value"], readiness_evidence.ITEM_EXISTING_BUYING_LABEL)
        self.assertTrue(evidence["has_buying_transaction_history"])
        self.assertTrue(evidence["has_purchase_receipt_history"])
        self.assertTrue(evidence["has_purchase_invoice_history"])

    def test_item_readiness_infers_existing_sales_activity_without_profile(self):
        context = readiness.get_item_buying_readiness_context("ITEM-SOLD")
        chip = item_buying_profile.item_readiness_chip("ITEM-SOLD")
        evidence = readiness_evidence.item_evidence("ITEM-SOLD")

        self.assertEqual(context["issues"][0]["severity"], "ready")
        self.assertEqual(context["issues"][0]["title"], readiness_evidence.ITEM_EXISTING_SALES_LABEL)
        self.assertEqual(chip["value"], readiness_evidence.ITEM_EXISTING_SALES_LABEL)
        self.assertTrue(evidence["has_sales_history"])
        self.assertTrue(evidence["has_sales_order_history"])
        self.assertTrue(evidence["has_delivery_note_history"])
        self.assertTrue(evidence["has_sales_invoice_history"])

    def test_item_readiness_infers_catalog_evidence_without_transaction_history(self):
        context = readiness.get_item_buying_readiness_context("ITEM-CATALOG")
        chip = item_buying_profile.item_readiness_chip("ITEM-CATALOG")

        self.assertEqual(context["issues"][0]["severity"], "ready")
        self.assertEqual(context["issues"][0]["title"], readiness_evidence.ITEM_CATALOG_EVIDENCE_LABEL)
        self.assertEqual(chip["value"], readiness_evidence.ITEM_CATALOG_EVIDENCE_LABEL)

    def test_item_readiness_warns_for_new_purchase_item_without_evidence(self):
        context = readiness.get_item_buying_readiness_context("ITEM-NEW")

        self.assertEqual(context["issues"][0]["severity"], "warning")
        self.assertEqual(context["issues"][0]["title"], readiness_evidence.ITEM_NEW_REVIEW_LABEL)

    def test_item_readiness_manual_hold_overrides_history(self):
        _set_user("manager@example.com", ["Purchase Manager"])
        item_buying_profile.save_item_buying_profile(
            "ITEM-001",
            {
                "buying_readiness_status": "Hold for sourcing",
                "preferred_existing_supplier": "SUP-001",
                "supplier_part_no_context": "",
                "procurement_lead_time_days": "",
                "minimum_order_qty_context": "",
                "buying_note": "",
                "readiness_note": "Paused for source review.",
            },
        )

        context = readiness.get_item_buying_readiness_context("ITEM-001")

        self.assertEqual(context["issues"][0]["severity"], "critical")
        self.assertIn("hold", context["issues"][0]["title"].lower())

    def test_item_buying_profile_is_read_only_for_purchase_user(self):
        _set_user("purchase@example.com", ["Purchase User"])

        payload = item_buying_profile.save_item_buying_profile("ITEM-001", {"buying_readiness_status": "Ready for buying"})

        self.assertEqual(payload["state"]["kind"], "restricted")
        self.assertEqual({}, ITEM_BUYING_PROFILES)
        detail = items.get_item_detail_context("ITEM-001")
        self.assertFalse(detail["detail"]["buying_profile"]["can_edit"])
        self.assertIn("Purchase Manager", detail["detail"]["buying_profile"]["read_only_reason"])

    def test_item_buying_profile_rejects_unknown_forbidden_and_invalid_payloads(self):
        _set_user("manager@example.com", ["Purchase Manager"])

        cases = [
            {"item_group": "Products"},
            {"default_supplier": "SUP-001"},
            {"price_list_rate": 100},
            {"unexpected_field": "x"},
            {"buying_readiness_status": "Ready"},
            {"preferred_existing_supplier": "SUP-MISSING"},
            {"procurement_lead_time_days": -1},
            {"procurement_lead_time_days": 366},
            {"minimum_order_qty_context": 0},
            {"minimum_order_qty_context": 1000001},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                response = item_buying_profile.save_item_buying_profile("ITEM-001", payload)
                self.assertEqual(response["state"]["kind"], "error")
        self.assertEqual({}, ITEM_BUYING_PROFILES)
        self.assertEqual([], ITEM_BUYING_LOGS)

    def test_item_buying_profile_does_not_mutate_erpnext_master_or_send_side_effects(self):
        _set_user("manager@example.com", ["Purchase Manager"])
        before_supplier_rows = _get_all("Item Supplier", filters={"parent": "ITEM-001"}, fields=["supplier", "supplier_part_no"])
        before_prices = _get_list("Item Price", filters=[["Item Price", "item_code", "=", "ITEM-001"]])

        item_buying_profile.save_item_buying_profile(
            "ITEM-001",
            {
                "buying_readiness_status": "Hold for sourcing",
                "preferred_existing_supplier": "SUP-001",
                "supplier_part_no_context": "CONTEXT-ONLY",
                "procurement_lead_time_days": 30,
                "minimum_order_qty_context": 5,
                "buying_note": "Hold until specs are confirmed.",
                "readiness_note": "Spec review pending.",
            },
        )

        after_supplier_rows = _get_all("Item Supplier", filters={"parent": "ITEM-001"}, fields=["supplier", "supplier_part_no"])
        after_prices = _get_list("Item Price", filters=[["Item Price", "item_code", "=", "ITEM-001"]])
        self.assertEqual(before_supplier_rows, after_supplier_rows)
        self.assertEqual(before_prices, after_prices)
        self.assertEqual(ITEM_BUYING_PROFILES["ITEM-001"]["supplier_part_no_context"], "CONTEXT-ONLY")
        self.assertNotEqual(ITEM_BUYING_PROFILES["ITEM-001"]["supplier_part_no_context"], after_supplier_rows[0]["supplier_part_no"])
        self.assertEqual({}, SAVED_RFQS)
        self.assertEqual({}, SAVED_SUPPLIER_QUOTATIONS)
        self.assertEqual({}, SAVED_PURCHASE_ORDERS)
        self.assertEqual([], [row for row in ITEM_BUYING_LOGS if row.get("doctype") in {"Communication", "Email Queue", "Contact", "User"}])

    def test_material_request_directory_is_purchase_only(self):
        payload = worklist.get_procurement_console_worklist_context("purchase_request_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual(payload["results"]["rows"][0]["actions"], [{"key": "open_record", "label": "Review Request"}])
        request_target = payload["action_targets"]["row:MAT-MR-001:open_record"]
        self.assertEqual(request_target["kind"], "page")
        self.assertEqual(request_target["route"], "procurement-console-purchase-request-review")
        self.assertEqual(request_target["options"], {"return_queue": "purchase_request_directory"})
        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Material Request", "material_request_type", "=", "Purchase"]))

    def test_purchase_request_directory_exposes_managed_create_action_when_permitted(self):
        _set_writeable_doctypes("Material Request")
        _set_createable_doctypes("Material Request")

        payload = worklist.get_procurement_console_worklist_context("purchase_request_directory")

        actions = payload["controls"]["actions"]
        self.assertEqual(actions[0]["key"], "new_purchase_request")
        self.assertEqual(actions[0]["category"], "create-action")
        self.assertEqual(actions[0]["kind"], "create")
        self.assertEqual(
            payload["action_targets"]["new_purchase_request"],
            {"kind": "page", "route": "procurement-console-purchase-request-form", "route_parts": ["new"]},
        )

        _set_writeable_doctypes()
        _set_createable_doctypes()
        restricted_payload = worklist.get_procurement_console_worklist_context("purchase_request_directory")
        self.assertNotIn("new_purchase_request", [action["key"] for action in restricted_payload["controls"]["actions"]])

    def test_procurement_filters_use_link_metadata_where_business_fields_reference_doctypes(self):
        supplier_payload = worklist.get_procurement_console_worklist_context("supplier_directory")
        request_payload = worklist.get_procurement_console_worklist_context("purchase_request_directory")
        order_payload = worklist.get_procurement_console_worklist_context("purchase_order_directory")
        follow_up_payload = worklist.get_procurement_console_worklist_context("purchase_orders_overdue")
        rfq_payload = worklist.get_procurement_console_worklist_context("rfq_directory")
        quotation_payload = worklist.get_procurement_console_worklist_context("supplier_quotation_directory")
        item_payload = worklist.get_procurement_console_worklist_context("buying_item_directory")
        comparison_payload = report.get_procurement_console_report_context("supplier_quotation_comparison", {"company": "Demo Company"})

        self.assertEqual(_field_by_key(request_payload, "material_request")["linkDoctype"], "Material Request")
        self.assertIsNone(_field_by_key(request_payload, "company"))
        self.assertEqual(_field_by_key(request_payload, "material_request")["placeholder"], "Select purchase request")
        self.assertEqual(_field_by_key(request_payload, "keyword")["label"], "Search request, item, or warehouse")
        self.assertEqual(_field_by_key(order_payload, "purchase_order")["linkDoctype"], "Purchase Order")
        self.assertEqual(_field_by_key(order_payload, "purchase_order")["placeholder"], "Select purchase order")
        self.assertEqual(_field_by_key(order_payload, "supplier")["linkDoctype"], "Supplier")
        self.assertEqual(_field_by_key(order_payload, "supplier")["placeholder"], "Select supplier")
        self.assertEqual(_field_by_key(order_payload, "keyword")["label"], "Search order, supplier, or item")
        self.assertIsNone(_field_by_key(order_payload, "company"))
        self.assertEqual(_field_by_key(order_payload, "date_start")["label"], "PO Date From")
        self.assertEqual(order_payload["metrics"][0]["label"], "Orders in view")
        self.assertEqual(_field_by_key(follow_up_payload, "purchase_order")["linkDoctype"], "Purchase Order")
        self.assertEqual(_field_by_key(follow_up_payload, "purchase_order")["placeholder"], "Select purchase order")
        self.assertEqual(_field_by_key(follow_up_payload, "supplier")["linkDoctype"], "Supplier")
        self.assertEqual(_field_by_key(follow_up_payload, "supplier")["placeholder"], "Select supplier")
        self.assertIsNone(_field_by_key(follow_up_payload, "company"))
        self.assertEqual(_field_by_key(follow_up_payload, "date_end")["label"], "PO Date To")
        self.assertEqual(_field_by_key(rfq_payload, "request_for_quotation")["linkDoctype"], "Request for Quotation")
        self.assertEqual(_field_by_key(rfq_payload, "request_for_quotation")["placeholder"], "Select RFQ")
        self.assertEqual(_field_by_key(rfq_payload, "date_start")["label"], "RFQ Date From")
        self.assertEqual(rfq_payload["metrics"][0]["label"], "RFQs in view")
        self.assertIsNone(_field_by_key(rfq_payload, "company"))
        self.assertEqual(_field_by_key(quotation_payload, "supplier_quotation")["linkDoctype"], "Supplier Quotation")
        self.assertEqual(_field_by_key(quotation_payload, "date_start")["label"], "Quotation Date From")
        self.assertEqual(quotation_payload["metrics"][0]["label"], "Quotations in view")
        self.assertEqual(_field_by_key(quotation_payload, "supplier_quotation")["placeholder"], "Select supplier quotation")
        self.assertEqual(_field_by_key(quotation_payload, "supplier")["linkDoctype"], "Supplier")
        self.assertEqual(_field_by_key(quotation_payload, "supplier")["placeholder"], "Select supplier")
        self.assertIsNone(_field_by_key(quotation_payload, "company"))
        self.assertEqual(_field_by_key(item_payload, "item")["linkDoctype"], "Item")
        self.assertEqual(_field_by_key(item_payload, "item")["placeholder"], "Select item")
        self.assertEqual(_field_by_key(item_payload, "item_group")["linkDoctype"], "Item Group")
        self.assertEqual(_field_by_key(item_payload, "item_group")["placeholder"], "Select item group")
        self.assertEqual(_field_by_key(supplier_payload, "keyword")["label"], "Search supplier or group")
        self.assertEqual(_field_by_key(supplier_payload, "keyword")["placeholder"], "Search supplier or group")
        self.assertEqual(_field_by_key(follow_up_payload, "keyword")["label"], "Search order, supplier, or item")
        self.assertEqual(_field_by_key(rfq_payload, "keyword")["label"], "Search RFQ, supplier, or item")
        self.assertEqual(_field_by_key(quotation_payload, "keyword")["label"], "Search quotation, supplier, or item")
        self.assertEqual(_field_by_key(item_payload, "keyword")["label"], "Search item, name, or group")
        self.assertIsNone(_field_by_key(comparison_payload, "company"))
        self.assertEqual(_field_by_key(comparison_payload, "item_code")["linkDoctype"], "Item")
        self.assertEqual(_field_by_key(comparison_payload, "item_code")["placeholder"], "Select item")
        self.assertEqual(_field_by_key(comparison_payload, "supplier_quotation")["linkDoctype"], "Supplier Quotation")
        self.assertEqual(_field_by_key(comparison_payload, "supplier_quotation")["placeholder"], "Select supplier quotation")
        self.assertEqual(_field_by_key(comparison_payload, "request_for_quotation")["linkDoctype"], "Request for Quotation")
        self.assertEqual(_field_by_key(comparison_payload, "request_for_quotation")["placeholder"], "Select RFQ")
        self.assertNotIn("actionLayout", comparison_payload["controls"])
        self.assertEqual(_field_by_key(comparison_payload, "include_expired")["row"], 1)
        self.assertEqual(_field_by_key(comparison_payload, "item_code")["row"], 2)
        self.assertEqual(_field_by_key(comparison_payload, "supplier")["row"], 2)

    def test_procurement_keyword_searches_match_buyer_facing_business_fields(self):
        cases = [
            ("supplier_directory", "SUP-001", ["SUP-001"]),
            ("supplier_directory", "All Supplier Groups", ["SUP-001"]),
            ("buying_item_directory", "ITEM-001", ["ITEM-001"]),
            ("buying_item_directory", "Products", ["ITEM-001"]),
            ("purchase_request_directory", "MAT-MR-001", ["MAT-MR-001"]),
            ("purchase_request_directory", "Widget", ["MAT-MR-001"]),
            ("purchase_request_directory", "Stores - DC", ["MAT-MR-001"]),
            ("purchase_order_directory", "PUR-PARTIAL", ["PUR-PARTIAL-001"]),
            ("purchase_order_directory", "Beta Supplier", ["PUR-PARTIAL-001"]),
            ("purchase_order_directory", "Partial Widget", ["PUR-PARTIAL-001"]),
            ("purchase_orders_supplier_follow_up", "Overdue Widget", ["PUR-OVERDUE-001"]),
            ("rfq_directory", "RFQ-001", ["RFQ-001"]),
            ("rfq_directory", "Alpha Supplier", ["RFQ-001"]),
            ("rfq_directory", "Widget", ["RFQ-001"]),
            ("supplier_quotation_directory", "SUP-QTN-001", ["SUP-QTN-001"]),
            ("supplier_quotation_directory", "Alpha Supplier", ["SUP-QTN-001"]),
            ("supplier_quotation_directory", "Widget", ["SUP-QTN-001"]),
        ]

        for queue_key, keyword, expected in cases:
            with self.subTest(queue_key=queue_key, keyword=keyword):
                payload = worklist.get_procurement_console_worklist_context(queue_key, {"keyword": keyword})
                self.assertEqual(_row_names(payload), expected)

    def test_keyword_search_remains_parent_permission_aware_after_child_match(self):
        HIDDEN_RFQ_LIST_NAMES.add("RFQ-001")

        payload = worklist.get_procurement_console_worklist_context("rfq_directory", {"keyword": "Alpha Supplier"})

        self.assertEqual(_row_names(payload), [])
        self.assertEqual(payload["results"]["state"]["kind"], "empty")

    def test_requests_to_source_enforces_purchase_and_not_fully_ordered(self):
        worklist.get_procurement_console_worklist_context("requests_to_source")

        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Material Request", "material_request_type", "=", "Purchase"]))
        self.assertTrue(_filter_contains(filters, ["Material Request", "docstatus", "=", 1]))
        self.assertTrue(_filter_contains(filters, ["Material Request", "per_ordered", "<", 100]))

    def test_purchase_request_review_is_read_only_productized_context(self):
        payload = document_reviews.get_purchase_request_review_context("MAT-MR-001")

        self.assertEqual(payload["detail"]["state"]["kind"], "ready")
        self.assertEqual(payload["summary"]["title"], "MAT-MR-001")
        self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["back_to_worklist", "refresh"])
        self.assertEqual(payload["detail"]["sections"][0]["table"]["rows"][0]["cells"]["item"]["value"], "ITEM-001")
        self.assertEqual(payload["action_targets"]["back_to_worklist"], {"kind": "worklist", "queue_key": "purchase_request_directory"})
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_purchase_request_review_requires_parent_visible_before_children(self):
        HIDDEN_MATERIAL_REQUEST_LIST_NAMES.add("MAT-MR-001")
        CAPTURED_GET_LIST_CALLS.clear()
        CAPTURED_GET_ALL_CALLS.clear()

        payload = document_reviews.get_purchase_request_review_context("MAT-MR-001")

        self.assertEqual(payload["detail"]["state"]["kind"], "unavailable")
        self.assertEqual(payload["detail"]["state"]["title"], "Purchase Request not found")
        self.assertTrue(any(call["doctype"] == "Material Request" and _filter_contains(call["filters"], ["Material Request", "name", "=", "MAT-MR-001"]) for call in CAPTURED_GET_LIST_CALLS))
        self.assertFalse(any(call["doctype"] == "Material Request Item" for call in CAPTURED_GET_ALL_CALLS))

    def test_purchase_order_pending_approval_is_visibility_only(self):
        payload = worklist.get_procurement_console_worklist_context("purchase_orders_pending_approval")

        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertTrue(_filter_contains(filters, ["Purchase Order", "workflow_state", "=", "Pending Purchase Approval"]))
        self.assertNotIn("approve", str(payload).lower())
        self.assertNotIn("reject", str(payload).lower())
        self.assertEqual(payload["action_targets"]["row:PUR-DUE-001:open_record"]["kind"], "page")

    def test_purchase_orders_due_soon_uses_line_level_expected_date(self):
        payload = worklist.get_procurement_console_worklist_context("purchase_orders_due_soon")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual([row["name"] for row in payload["results"]["rows"]], ["PUR-DUE-001"])
        self.assertEqual(payload["results"]["rows"][0]["cells"]["required_by"], "2026-05-06")
        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Purchase Order", "docstatus", "=", 1]))
        self.assertTrue(_filter_contains(filters, ["Purchase Order", "status", "not in", ["Completed", "Closed", "Cancelled"]]))
        self.assertTrue(any(call["doctype"] == "Purchase Order Item" and "expected_delivery_date" in call["fields"] for call in CAPTURED_GET_ALL_CALLS))
        self.assertEqual(payload["action_targets"]["row:PUR-DUE-001:open_record"]["kind"], "page")
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_purchase_orders_overdue_uses_line_level_schedule_date(self):
        payload = worklist.get_procurement_console_worklist_context("purchase_orders_overdue")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual([row["name"] for row in payload["results"]["rows"]], ["PUR-OVERDUE-001"])
        self.assertEqual(payload["results"]["rows"][0]["cells"]["required_by"], "2026-04-30")
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_late_or_unreceived_queue_is_backward_compatible_overdue_alias(self):
        payload = worklist.get_procurement_console_worklist_context("purchase_orders_late_or_unreceived")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual(payload["results"]["rows"][0]["name"], "PUR-OVERDUE-001")
        self.assertIn("Compatibility alias", payload["controls"]["scopeChips"])

    def test_purchase_orders_partially_received_filters_buyer_follow_up(self):
        payload = worklist.get_procurement_console_worklist_context("purchase_orders_partially_received")

        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertTrue(_filter_contains(filters, ["Purchase Order", "per_received", ">", 0]))
        self.assertTrue(_filter_contains(filters, ["Purchase Order", "per_received", "<", 100]))
        self.assertEqual([row["name"] for row in payload["results"]["rows"]], ["PUR-PARTIAL-001"])
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_purchase_orders_billing_visibility_is_received_not_fully_billed_only(self):
        payload = worklist.get_procurement_console_worklist_context("purchase_orders_not_billed_visibility")

        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertTrue(_filter_contains(filters, ["Purchase Order", "per_received", ">", 0]))
        self.assertTrue(_filter_contains(filters, ["Purchase Order", "per_billed", "<", 100]))
        self.assertEqual([row["name"] for row in payload["results"]["rows"]], ["PUR-PARTIAL-001", "PUR-BILLING-001"])
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_purchase_orders_supplier_follow_up_combines_buyer_reasons(self):
        payload = worklist.get_procurement_console_worklist_context("purchase_orders_supplier_follow_up")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual(
            [row["name"] for row in payload["results"]["rows"]],
            ["PUR-OVERDUE-001", "PUR-DUE-001", "PUR-PARTIAL-001"],
        )
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_finance_and_executive_direct_po_follow_up_queue_restricted(self):
        _set_user("approver@example.com", ["Finance Lead Approver", "Executive Approver"])

        payload = worklist.get_procurement_console_worklist_context("purchase_orders_overdue")

        self.assertEqual(payload["results"]["state"]["kind"], "restricted")

    def test_po_follow_up_detail_is_read_only_productized_page(self):
        payload = purchase_order_detail.get_purchase_order_follow_up_detail_context("PUR-PARTIAL-001", return_queue="purchase_orders_partially_received")

        self.assertEqual(payload["detail"]["state"]["kind"], "ready")
        self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["back_to_queue", "refresh"])
        self.assertEqual([action["icon"] for action in payload["controls"]["actions"]], ["arrow-left", "refresh"])
        self.assertEqual(payload["summary"]["title"], "PUR-PARTIAL-001")
        item_cell = payload["detail"]["items"]["rows"][0]["cells"]["item"]
        self.assertEqual(item_cell["value"], "ITEM-003")
        self.assertEqual(item_cell["meta"], "Partial Widget")
        self.assertEqual(payload["detail"]["items"]["rows"][0]["cells"]["remaining_qty"], "4")
        self.assertEqual(payload["action_targets"]["back_to_queue"]["kind"], "worklist")
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_po_follow_up_detail_requires_parent_visible_in_permission_aware_list(self):
        HIDDEN_PURCHASE_ORDER_LIST_NAMES.add("PUR-PARTIAL-001")
        CAPTURED_GET_LIST_CALLS.clear()
        CAPTURED_GET_ALL_CALLS.clear()

        payload = purchase_order_detail.get_purchase_order_follow_up_detail_context("PUR-PARTIAL-001")

        self.assertEqual(payload["detail"]["state"]["kind"], "unavailable")
        self.assertEqual(payload["detail"]["state"]["title"], "Purchase Order not found")
        self.assertTrue(
            any(
                call["doctype"] == "Purchase Order"
                and _filter_contains(call["filters"], ["Purchase Order", "name", "=", "PUR-PARTIAL-001"])
                for call in CAPTURED_GET_LIST_CALLS
            )
        )
        self.assertFalse(any(call["doctype"] in {"Purchase Order Item", "Purchase Receipt Item", "Purchase Invoice Item"} for call in CAPTURED_GET_ALL_CALLS))

    def test_po_follow_up_detail_restricted_for_finance_executive_only(self):
        _set_user("approver@example.com", ["Finance Lead Approver", "Executive Approver"])

        payload = purchase_order_detail.get_purchase_order_follow_up_detail_context("PUR-PARTIAL-001")

        self.assertEqual(payload["detail"]["state"]["kind"], "restricted")

    def test_rfq_directory_is_read_only(self):
        payload = worklist.get_procurement_console_worklist_context("rfq_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual(payload["results"]["rows"][0]["actions"], [{"key": "open_record", "label": "Review RFQ"}])
        rfq_target = payload["action_targets"]["row:RFQ-001:open_record"]
        self.assertEqual(rfq_target["kind"], "page")
        self.assertEqual(rfq_target["route"], "procurement-console-rfq-review")
        self.assertEqual(rfq_target["options"], {"return_queue": "rfq_directory"})
        self.assertIn("Supplier response visibility", payload["controls"]["scopeChips"])
        self.assertNotIn("send", str(payload.get("controls", {})).lower())
        self.assertNotIn("email", str(payload.get("controls", {})).lower())
        self.assertNotIn("send_email", str(payload))

    def test_rfq_directory_exposes_managed_create_action_when_permitted(self):
        _set_writeable_doctypes("Request for Quotation")
        _set_createable_doctypes("Request for Quotation")

        payload = worklist.get_procurement_console_worklist_context("rfq_directory")

        actions = payload["controls"]["actions"]
        self.assertEqual(actions[0]["key"], "new_rfq")
        self.assertEqual(actions[0]["category"], "create-action")
        self.assertEqual(actions[0]["kind"], "create")
        self.assertEqual(
            payload["action_targets"]["new_rfq"],
            {"kind": "page", "route": "procurement-console-rfq-form", "route_parts": ["new"]},
        )

        _set_writeable_doctypes()
        _set_createable_doctypes()
        restricted_payload = worklist.get_procurement_console_worklist_context("rfq_directory")
        self.assertNotIn("new_rfq", [action["key"] for action in restricted_payload["controls"]["actions"]])

    def test_rfqs_awaiting_response_uses_quote_status(self):
        payload = worklist.get_procurement_console_worklist_context("rfqs_awaiting_supplier_response")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertTrue(any(call["doctype"] == "Request for Quotation Supplier" and call["filters"].get("quote_status") == "Pending" for call in CAPTURED_GET_ALL_CALLS))
        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Request for Quotation", "docstatus", "=", 1]))

    def test_rfq_review_is_read_only_productized_context(self):
        payload = document_reviews.get_rfq_review_context("RFQ-001")

        self.assertEqual(payload["detail"]["state"]["kind"], "ready")
        self.assertEqual(payload["summary"]["title"], "RFQ-001")
        self.assertEqual(payload["detail"]["sections"][0]["table"]["rows"][0]["cells"]["supplier"]["value"], "Alpha Supplier")
        self.assertEqual(payload["detail"]["sections"][1]["table"]["rows"][0]["cells"]["source"], "MAT-MR-001")
        self.assertEqual(payload["action_targets"]["back_to_worklist"], {"kind": "worklist", "queue_key": "rfq_directory"})
        output_context = payload["output_context"]
        self.assertEqual(output_context["state"]["kind"], "ready")
        self.assertEqual(output_context["warning"], "Draft / Not sent")
        self.assertTrue(output_context["requires_supplier_selection"])
        self.assertEqual([row["supplier"] for row in output_context["suppliers"]], ["SUP-001", "SUP-002"])
        self.assertFalse(output_context["can_send"])
        self.assertIn("send_readiness", output_context)
        self.assertFalse(output_context["send_readiness"]["can_send"])
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_rfq_review_requires_parent_visible_before_children(self):
        HIDDEN_RFQ_LIST_NAMES.add("RFQ-001")
        CAPTURED_GET_LIST_CALLS.clear()
        CAPTURED_GET_ALL_CALLS.clear()

        payload = document_reviews.get_rfq_review_context("RFQ-001")

        self.assertEqual(payload["detail"]["state"]["kind"], "unavailable")
        self.assertEqual(payload["detail"]["state"]["title"], "RFQ not found")
        self.assertFalse(any(call["doctype"] in {"Request for Quotation Item", "Request for Quotation Supplier"} for call in CAPTURED_GET_ALL_CALLS))

    def test_rfqs_awaiting_response_unavailable_without_quote_status_field(self):
        global HAS_QUOTE_STATUS
        HAS_QUOTE_STATUS = False

        payload = worklist.get_procurement_console_worklist_context("rfqs_awaiting_supplier_response")

        self.assertEqual(payload["results"]["state"]["kind"], "unavailable")
        self.assertNotEqual(payload["results"]["state"]["kind"], "error")

    def test_partially_quoted_rfqs_require_pending_and_received_status(self):
        payload = worklist.get_procurement_console_worklist_context("rfqs_partially_quoted")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual(payload["results"]["rows"][0]["name"], "RFQ-001")


    def test_manager_overview_readiness_is_manager_only_and_productized(self):
        _set_user("manager@example.com", ["Purchase Manager"])

        payload = service.get_procurement_console_bootstrap()

        self.assertNotIn("manager_readiness", payload)
        manager_queue = readiness.get_procurement_manager_readiness()
        self.assertTrue(manager_queue["visible"])
        self.assertGreater(manager_queue["summary"]["total"], 0)
        self.assertTrue(manager_queue["groups"])
        text = str(manager_queue)
        self.assertNotIn("/desk/Form", text)
        self.assertNotIn("/app/", text)
        self.assertNotIn("Open ERP", text)
        for issue in manager_queue["issues"]:
            self.assertTrue(issue["productized_only"])
            route = issue.get("fix_route") or {}
            if route:
                self.assertEqual(route.get("kind"), "page")
                self.assertTrue(str(route.get("route") or "").startswith("procurement-console-"))

        _set_user("purchase@example.com", ["Purchase User"])
        user_payload = service.get_procurement_console_bootstrap()
        self.assertNotIn("manager_readiness", user_payload)
        user_queue = readiness.get_procurement_manager_readiness()
        self.assertFalse(user_queue["visible"])
        self.assertEqual([], user_queue["issues"])

    def test_manager_overview_readiness_does_not_build_full_profile_contexts(self):
        _set_user("manager@example.com", ["Purchase Manager"])
        original_item_context = item_buying_profile.get_item_profile_context
        original_supplier_context = supplier_readiness.get_supplier_profile_for_readiness

        def _blocked_context(*args, **kwargs):
            raise AssertionError("Overview readiness must use batched lightweight context")

        try:
            item_buying_profile.get_item_profile_context = _blocked_context
            supplier_readiness.get_supplier_profile_for_readiness = _blocked_context
            payload = readiness.get_procurement_manager_readiness()
        finally:
            item_buying_profile.get_item_profile_context = original_item_context
            supplier_readiness.get_supplier_profile_for_readiness = original_supplier_context

        self.assertTrue(payload["visible"])
        self.assertEqual(payload["summary"]["total"], len(payload["issues"]))
        self.assertIn("groups", payload)
        for issue in payload["issues"]:
            self.assertTrue(issue["productized_only"])
            self.assertNotIn("/desk/Form", str(issue))

    def test_page_level_readiness_contexts_are_read_only_and_productized(self):
        _set_user("manager@example.com", ["Purchase Manager"])
        supplier_readiness.save_supplier_readiness_profile(
            "SUP-001",
            {
                "buying_readiness_status": "Hold for sourcing",
                "preferred_rfq_contact": "CONT-001",
                "rfq_recipient_email_override": "",
                "buying_note": "",
                "readiness_note": "Supplier paused.",
            },
        )
        item_buying_profile.save_item_buying_profile(
            "ITEM-001",
            {
                "buying_readiness_status": "Hold for sourcing",
                "preferred_existing_supplier": "SUP-001",
                "supplier_part_no_context": "",
                "procurement_lead_time_days": "",
                "minimum_order_qty_context": "",
                "buying_note": "",
                "readiness_note": "Item paused.",
            },
        )
        before_logs = (len(SUPPLIER_READINESS_LOGS), len(ITEM_BUYING_LOGS))

        supplier_payload = supplier_detail.get_supplier_detail_context("SUP-001")
        item_payload = items.get_item_detail_context("ITEM-001")
        rfq_payload = document_reviews.get_rfq_review_context("RFQ-001")
        sq_payload = document_reviews.get_supplier_quotation_review_context("SUP-QTN-001")
        po_payload = purchase_order_detail.get_purchase_order_follow_up_detail_context("PUR-DUE-001")
        pr_payload = document_reviews.get_purchase_request_review_context("MAT-MR-001")

        contexts = [
            supplier_payload["detail"]["readiness_context"],
            item_payload["detail"]["readiness_context"],
            rfq_payload["detail"]["readiness_context"],
            sq_payload["detail"]["readiness_context"],
            po_payload["detail"]["readiness_context"],
            pr_payload["detail"]["readiness_context"],
        ]
        for context in contexts:
            with self.subTest(source=context.get("source_name")):
                self.assertEqual(context["state"]["kind"], "ready")
                self.assertTrue(context["productized_only"])
                self.assertTrue(context["issues"])
                for issue in context["issues"]:
                    self.assertTrue(issue["productized_only"])
                    route = issue.get("fix_route") or {}
                    if route:
                        self.assertEqual(route.get("kind"), "page")
                        self.assertTrue(str(route.get("route") or "").startswith("procurement-console-"))
                self.assertNotIn("/desk/Form", str(context))
                self.assertNotIn("/app/", str(context))
                self.assertNotIn("Open ERP", str(context))
        self.assertTrue(any(issue["severity"] == "critical" for issue in rfq_payload["detail"]["readiness_context"]["issues"]))
        self.assertIn("Sending not active", str(rfq_payload["detail"]["readiness_context"]))
        self.assertEqual(before_logs, (len(SUPPLIER_READINESS_LOGS), len(ITEM_BUYING_LOGS)))
        self.assertEqual({}, SAVED_PURCHASE_ORDERS)
        self.assertEqual({}, SAVED_SUPPLIER_QUOTATIONS)
        _assert_no_forbidden_mutation_actions(self, rfq_payload)
        _assert_no_forbidden_mutation_actions(self, sq_payload)
        _assert_no_forbidden_mutation_actions(self, po_payload)

    def test_managed_saved_forms_include_readiness_without_lifecycle_actions(self):
        _set_user("manager@example.com", ["Purchase Manager"])
        _set_writeable_doctypes("Material Request", "Request for Quotation", "Supplier Quotation", "Purchase Order")
        SAVED_MATERIAL_REQUESTS["MAT-MR-DRAFT-001"] = _FakeMaterialRequestDoc(name="MAT-MR-DRAFT-001", values={"items": [{"item_code": "ITEM-001", "qty": 1, "schedule_date": "2026-05-10", "warehouse": "Stores - DC", "uom": "Nos"}]})
        SAVED_RFQS["PUR-RFQ-DRAFT-001"] = _FakeRFQDoc(name="PUR-RFQ-DRAFT-001", values={"suppliers": [{"supplier": "SUP-001"}], "items": [{"item_code": "ITEM-001", "qty": 1, "schedule_date": "2026-05-10", "warehouse": "Stores - DC", "uom": "Nos"}]})
        SAVED_SUPPLIER_QUOTATIONS["SUP-QTN-DRAFT-001"] = _FakeSupplierQuotationDoc(name="SUP-QTN-DRAFT-001", values={"supplier": "SUP-001", "items": [{"item_code": "ITEM-001", "qty": 1, "rate": 100, "uom": "Nos"}]})
        SAVED_PURCHASE_ORDERS["PUR-ORD-DRAFT-001"] = _FakePurchaseOrderDoc(name="PUR-ORD-DRAFT-001", values={"supplier": "SUP-001", "items": [{"item_code": "ITEM-001", "qty": 1, "rate": 100, "schedule_date": "2026-05-10", "warehouse": "Stores - DC", "uom": "Nos"}]})

        payloads = [
            managed_purchase_request.get_managed_purchase_request_context("MAT-MR-DRAFT-001"),
            managed_rfq.get_managed_rfq_context("PUR-RFQ-DRAFT-001"),
            managed_supplier_quotation.get_managed_supplier_quotation_context("SUP-QTN-DRAFT-001"),
            managed_purchase_order.get_managed_purchase_order_context("PUR-ORD-DRAFT-001"),
        ]

        for payload in payloads:
            with self.subTest(title=payload["summary"]["title"]):
                self.assertIn("readiness_context", payload)
                self.assertEqual(payload["readiness_context"]["state"]["kind"], "ready")
                self.assertTrue(payload["readiness_context"]["productized_only"])
                self.assertNotIn("Open ERP Form", str(payload))
                _assert_no_forbidden_mutation_actions(self, payload)

    def test_supplier_quotation_directory_is_read_only(self):
        payload = worklist.get_procurement_console_worklist_context("supplier_quotation_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        payload_text = str(payload).lower()
        self.assertNotIn("create", payload_text)
        self.assertNotIn("purchase_order", payload_text)
        self.assertNotIn("item_price", payload_text)
        self.assertNotIn("set_default_supplier", payload_text)
        self.assertEqual(payload["results"]["rows"][0]["actions"], [{"key": "open_record", "label": "Review Quote"}])
        quotation_target = payload["action_targets"]["row:SUP-QTN-001:open_record"]
        self.assertEqual(quotation_target["kind"], "page")
        self.assertEqual(quotation_target["route"], "procurement-console-supplier-quotation-review")
        self.assertEqual(quotation_target["options"], {"return_queue": "supplier_quotation_directory"})

    def test_supplier_quotations_to_compare_filters_submitted_visible_records(self):
        payload = worklist.get_procurement_console_worklist_context("supplier_quotations_to_compare")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Supplier Quotation", "docstatus", "=", 1]))
        self.assertTrue(_filter_contains(filters, ["Supplier Quotation", "status", "not in", ["Cancelled", "Stopped"]]))

    def test_supplier_quotation_review_is_read_only_productized_context(self):
        payload = document_reviews.get_supplier_quotation_review_context("SUP-QTN-001")

        self.assertEqual(payload["detail"]["state"]["kind"], "ready")
        self.assertEqual(payload["summary"]["title"], "SUP-QTN-001")
        self.assertEqual(payload["detail"]["sections"][0]["table"]["rows"][0]["cells"]["item"]["value"], "ITEM-001")
        self.assertEqual(payload["detail"]["sections"][0]["table"]["rows"][0]["cells"]["references"], "RFQ-001, MAT-MR-001")
        self.assertEqual(payload["action_targets"]["open_quote_comparison"], {"kind": "report_page", "report_key": "supplier_quotation_comparison", "filters": {"supplier_quotation": "SUP-QTN-001"}})
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_review_contexts_do_not_expose_native_form_escape_for_procurement_roles(self):
        _set_writeable_doctypes("Material Request", "Request for Quotation", "Supplier Quotation")

        contexts = (
            document_reviews.get_purchase_request_review_context("MAT-MR-001"),
            document_reviews.get_rfq_review_context("PUR-RFQ-001"),
            document_reviews.get_supplier_quotation_review_context("SUP-QTN-001"),
        )

        for payload in contexts:
            with self.subTest(title=payload["summary"]["title"]):
                action_keys = [action["key"] for action in payload["controls"]["actions"]]
                self.assertNotIn("open_erp_form", action_keys)
                self.assertNotIn("open_erp_form", payload["action_targets"])
                self.assertNotIn("Open ERP Form", str(payload))
        quotation_payload = contexts[2]
        self.assertIn("open_quote_comparison", [action["key"] for action in quotation_payload["controls"]["actions"]])
        self.assertEqual(quotation_payload["action_targets"]["open_quote_comparison"]["kind"], "report_page")

    def test_supplier_quotation_review_requires_parent_visible_before_children(self):
        HIDDEN_SUPPLIER_QUOTATION_LIST_NAMES.add("SUP-QTN-001")
        CAPTURED_GET_LIST_CALLS.clear()
        CAPTURED_GET_ALL_CALLS.clear()

        payload = document_reviews.get_supplier_quotation_review_context("SUP-QTN-001")

        self.assertEqual(payload["detail"]["state"]["kind"], "unavailable")
        self.assertEqual(payload["detail"]["state"]["title"], "Supplier Quotation not found")
        self.assertFalse(any(call["doctype"] == "Supplier Quotation Item" for call in CAPTURED_GET_ALL_CALLS))

    def test_supplier_quotations_expiring_filters_validity_window(self):
        payload = worklist.get_procurement_console_worklist_context("supplier_quotations_expiring")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Supplier Quotation", "valid_till", ">=", "2026-05-03"]))
        self.assertTrue(_filter_contains(filters, ["Supplier Quotation", "valid_till", "<=", "2026-05-10"]))

    def test_worklist_restricted_for_non_procurement_user(self):
        _set_user("sales@example.com", ["Sales User"])

        payload = worklist.get_procurement_console_worklist_context("supplier_quotation_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "restricted")

    def test_guest_worklist_raises_permission_error(self):
        _set_user("Guest", [])

        with self.assertRaises(_FakePermissionError):
            worklist.get_procurement_console_worklist_context("supplier_directory")

    def test_unknown_worklist_returns_unavailable_not_error(self):
        payload = worklist.get_procurement_console_worklist_context("unknown_queue")

        self.assertEqual(payload["results"]["state"]["kind"], "unavailable")
        self.assertNotEqual(payload["results"]["state"]["kind"], "error")
        self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["refresh"])

    def test_report_index_returns_ready_catalog_for_procurement_user(self):
        payload = report.get_procurement_console_report_context()

        self.assertEqual(payload["page"], {"title": "Procurement Reports", "key": "procurement_reports_index"})
        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        sections = payload["catalog"]["sections"]
        self.assertEqual(
            [section["key"] for section in sections],
            ["sourcing_review", "order_review", "demand_coverage", "item_price_review"],
        )
        cards = [card for section in sections for card in section["cards"]]
        card_by_key = {card["key"]: card for card in cards}
        self.assertEqual(card_by_key["supplier_quotation_comparison"]["status"], "ready")
        self.assertEqual(card_by_key["supplier_quotation_comparison"]["target_route"], "/desk/procurement-console-report/supplier-quotation-comparison")
        self.assertEqual(card_by_key["purchase_order_analysis"]["status"], "ready")
        self.assertEqual(card_by_key["purchase_order_analysis"]["target_route"], "/desk/procurement-console-report/purchase-order-analysis")
        self.assertEqual(
            [card["status"] for card in cards],
            ["ready", "ready", "ready", "ready"],
        )
        self.assertEqual(card_by_key["demand_to_order_coverage"]["status"], "ready")
        self.assertEqual(card_by_key["demand_to_order_coverage"]["target_route"], "/desk/procurement-console-report/demand-to-order-coverage")
        self.assertEqual(card_by_key["item_purchase_history"]["status"], "ready")
        self.assertEqual(card_by_key["item_purchase_history"]["target_route"], "/desk/procurement-console-report/item-purchase-history")
        self.assertEqual(
            payload["action_targets"]["open_supplier_quotation_comparison"],
            {"kind": "report_page", "report_key": "supplier_quotation_comparison"},
        )
        self.assertEqual(
            payload["action_targets"]["open_purchase_order_analysis"],
            {"kind": "report_page", "report_key": "purchase_order_analysis"},
        )
        self.assertEqual(
            payload["action_targets"]["open_demand_to_order_coverage"],
            {"kind": "report_page", "report_key": "demand_to_order_coverage"},
        )
        self.assertEqual(
            payload["action_targets"]["open_item_purchase_history"],
            {"kind": "report_page", "report_key": "item_purchase_history"},
        )
        payload_text = str(payload).lower()
        self.assertNotIn("query-report", payload_text)
        self.assertNotIn("set_default_supplier", payload_text)
        self.assertNotIn("default supplier mutation", payload_text)
        _assert_no_forbidden_mutation_actions(self, payload)

    def test_report_index_restricted_for_non_procurement_user(self):
        _set_user("sales@example.com", ["Sales User"])

        payload = report.get_procurement_console_report_context()

        self.assertEqual(payload["results"]["state"]["kind"], "restricted")


    def test_supplier_quotation_comparison_wraps_native_report_without_mutation_tools(self):
        payload = report.get_procurement_console_report_context(
            "supplier_quotation_comparison",
            {"company": "Demo Company", "supplier": "SUP-001", "include_expired": "1"},
        )

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual(CAPTURED_REPORT_CALLS[-1]["report_name"], "Supplier Quotation Comparison")
        self.assertEqual(CAPTURED_REPORT_CALLS[-1]["filters"]["supplier"], ["SUP-001"])
        self.assertEqual(CAPTURED_REPORT_CALLS[-1]["filters"]["include_expired"], 1)
        self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["refresh"])
        column_by_key = {column["key"]: column for column in payload["results"]["columns"]}
        self.assertTrue(column_by_key["valid_till"].get("nowrap"))
        self.assertGreaterEqual(payload["results"].get("tableMinWidth", 0), 1800)
        payload_text = str(payload).lower()
        self.assertNotIn("set_default_supplier", payload_text)
        self.assertNotIn("default_supplier", payload_text)
        self.assertNotIn("item price", payload_text)
        self.assertNotIn("purchase order", payload_text)

    def test_supplier_quotation_comparison_defaults_company_without_noisy_filter(self):
        CAPTURED_REPORT_CALLS.clear()

        payload = report.get_procurement_console_report_context("supplier_quotation_comparison", {})

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertIsNone(_field_by_key(payload, "company"))
        self.assertEqual(CAPTURED_REPORT_CALLS[-1]["filters"]["company"], "Demo Company")
        self.assertNotIn("Company", " ".join(field.get("label", "") for field in payload["controls"]["fields"]))
        payload_text = str(payload)
        self.assertIn("Compare supplier offers by price, validity, item, supplier, and RFQ reference", payload_text)
        self.assertNotIn("ERPNext native report", payload_text)
        self.assertNotIn("Mutation tools are not exposed", payload_text)

    def test_supplier_quotation_comparison_restricted_without_supplier_quotation_read(self):
        _set_readable_doctypes("Supplier", "Material Request", "Purchase Order", "Request for Quotation")

        payload = report.get_procurement_console_report_context("supplier_quotation_comparison")

        self.assertEqual(payload["results"]["state"]["kind"], "restricted")

    def test_unknown_report_returns_unavailable_not_error(self):
        payload = report.get_procurement_console_report_context("unknown_report")

        self.assertEqual(payload["results"]["state"]["kind"], "unavailable")
        self.assertNotEqual(payload["results"]["state"]["kind"], "error")
        self.assertEqual(
            [action["key"] for action in payload["controls"]["actions"]],
            ["refresh"],
        )

    def test_purchase_order_analysis_wraps_native_report_with_productized_drilldowns(self):
        payload = report.get_procurement_console_report_context(
            "purchase_order_analysis",
            {"company": "Demo Company", "purchase_order": "PUR-OVERDUE-001", "supplier": "SUP-001", "item_code": "ITEM-002", "status": "To Receive and Bill"},
        )

        self.assertEqual(payload["page"], {"title": "Purchase Order Analysis", "key": "purchase_order_analysis"})
        self.assertEqual(payload["metrics"].get("layout"), "five_up")
        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual(CAPTURED_REPORT_CALLS[-1]["report_name"], "Purchase Order Analysis")
        self.assertEqual(CAPTURED_REPORT_CALLS[-1]["filters"]["name"], ["PUR-OVERDUE-001"])
        self.assertEqual(CAPTURED_REPORT_CALLS[-1]["filters"]["status"], ["To Receive and Bill"])
        po_get_list = [call for call in CAPTURED_GET_LIST_CALLS if call["doctype"] == "Purchase Order"][-1]
        self.assertEqual(po_get_list["fields"].count("workflow_state"), 1)
        self.assertEqual(len(po_get_list["fields"]), len(set(po_get_list["fields"])))
        self.assertIsNone(_field_by_key(payload, "company"))
        self.assertEqual(_field_by_key(payload, "purchase_order")["linkDoctype"], "Purchase Order")
        self.assertEqual(_field_by_key(payload, "supplier")["linkDoctype"], "Supplier")
        self.assertEqual(_field_by_key(payload, "item_code")["linkDoctype"], "Item")
        self.assertGreaterEqual(payload["results"].get("tableMinWidth", 0), 1700)
        column_by_key = {column["key"]: column for column in payload["results"]["columns"]}
        self.assertTrue(column_by_key["purchase_order"].get("nowrap"))
        self.assertTrue(column_by_key["required_date"].get("nowrap"))
        self.assertEqual(len(payload["results"]["rows"]), 1)
        row = payload["results"]["rows"][0]
        self.assertEqual(row["cells"]["purchase_order"]["value"], "PUR-OVERDUE-001")
        self.assertEqual(row["cells"]["purchase_order"]["actionKey"], "po_analysis:po:PUR-OVERDUE-001")
        self.assertEqual(row["cells"]["supplier"]["actionKey"], "po_analysis:supplier:SUP-001")
        self.assertEqual(row["cells"]["item_code"]["actionKey"], "po_analysis:item:ITEM-002")
        self.assertEqual(payload["action_targets"]["po_analysis:po:PUR-OVERDUE-001"], {"kind": "page", "route": "procurement-console-po-follow-up", "route_parts": ["PUR-OVERDUE-001"]})
        self.assertEqual(payload["action_targets"]["po_analysis:supplier:SUP-001"], {"kind": "page", "route": "procurement-console-supplier", "route_parts": ["SUP-001"]})
        self.assertEqual(payload["action_targets"]["po_analysis:item:ITEM-002"], {"kind": "page", "route": "procurement-console-item", "route_parts": ["ITEM-002"]})
        _assert_no_forbidden_mutation_actions(self, payload)
        payload_text = str(payload).lower()
        self.assertNotIn("query-report", payload_text)
        self.assertNotIn("form", payload_text)

    def test_purchase_order_analysis_empty_after_supplier_or_item_filter(self):
        payload = report.get_procurement_console_report_context("purchase_order_analysis", {"supplier": "SUP-NOPE"})

        self.assertEqual(payload["results"]["state"]["kind"], "empty")
        self.assertEqual(payload["results"]["rows"], [])

    def test_purchase_order_analysis_restricted_without_purchase_order_read(self):
        _set_readable_doctypes("Supplier", "Item", "Material Request", "Supplier Quotation")

        payload = report.get_procurement_console_report_context("purchase_order_analysis")

        self.assertEqual(payload["results"]["state"]["kind"], "restricted")

    def test_purchase_order_analysis_unavailable_when_native_report_missing(self):
        MISSING_NATIVE_REPORTS.add("Purchase Order Analysis")

        payload = report.get_procurement_console_report_context("purchase_order_analysis")

        self.assertEqual(payload["results"]["state"]["kind"], "unavailable")
        self.assertEqual(payload["results"]["rows"], [])

    def test_demand_to_order_coverage_returns_ready_productized_report(self):
        payload = report.get_procurement_console_report_context("demand_to_order_coverage", {"material_request": "MAT-MR-001", "item_code": "ITEM-001", "coverage_status": "partially_ordered"})

        self.assertEqual(payload["page"], {"title": "Demand-to-Order Coverage", "key": "demand_to_order_coverage"})
        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual(payload["metrics"].get("layout"), "five_up")
        self.assertIsNone(_field_by_key(payload, "company"))
        self.assertEqual(_field_by_key(payload, "material_request")["linkDoctype"], "Material Request")
        self.assertEqual(_field_by_key(payload, "item_code")["linkDoctype"], "Item")
        self.assertEqual(_field_by_key(payload, "warehouse")["linkDoctype"], "Warehouse")
        column_by_key = {column["key"]: column for column in payload["results"]["columns"]}
        self.assertTrue(column_by_key["material_request"].get("nowrap"))
        self.assertTrue(column_by_key["required_date"].get("nowrap"))
        self.assertEqual(len(payload["results"]["rows"]), 1)
        row = payload["results"]["rows"][0]
        self.assertEqual(row["cells"]["material_request"]["value"], "MAT-MR-001")
        self.assertEqual(row["cells"]["coverage_status"]["value"], "Partially Ordered")
        self.assertEqual(row["cells"]["open_qty"]["value"], "4")
        self.assertEqual(row["cells"]["linked_purchase_order"]["actionKey"], "demand_coverage:po:PUR-DUE-001")
        self.assertEqual(payload["action_targets"]["demand_coverage:request:MAT-MR-001"], {"kind": "page", "route": "procurement-console-purchase-request-review", "route_parts": ["MAT-MR-001"]})
        self.assertEqual(payload["action_targets"]["demand_coverage:item:ITEM-001"], {"kind": "page", "route": "procurement-console-item", "route_parts": ["ITEM-001"]})
        self.assertEqual(payload["action_targets"]["demand_coverage:po:PUR-DUE-001"], {"kind": "page", "route": "procurement-console-po-follow-up", "route_parts": ["PUR-DUE-001"]})
        _assert_no_forbidden_mutation_actions(self, payload)
        payload_text = str(payload).lower()
        self.assertNotIn("query-report", payload_text)
        self.assertNotIn("create purchase order", payload_text)
        self.assertNotIn("form", payload_text)

    def test_demand_to_order_coverage_empty_after_filter(self):
        payload = report.get_procurement_console_report_context("demand_to_order_coverage", {"coverage_status": "fully_ordered"})

        self.assertEqual(payload["results"]["state"]["kind"], "empty")
        self.assertEqual(payload["results"]["rows"], [])

    def test_demand_to_order_coverage_restricted_without_material_request_read(self):
        _set_readable_doctypes("Supplier", "Item", "Purchase Order")

        payload = report.get_procurement_console_report_context("demand_to_order_coverage")

        self.assertEqual(payload["results"]["state"]["kind"], "restricted")

    def test_demand_to_order_coverage_hides_po_drilldown_without_po_read(self):
        _set_readable_doctypes("Supplier", "Item", "Material Request")

        payload = report.get_procurement_console_report_context("demand_to_order_coverage")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        row = payload["results"]["rows"][0]
        self.assertEqual(row["cells"]["linked_purchase_order"]["value"], "-")
        self.assertFalse(any(key.startswith("demand_coverage:po:") for key in payload["action_targets"]))

    def test_demand_to_order_coverage_unavailable_when_required_link_field_missing(self):
        MISSING_FIELDS.add(("Purchase Order Item", "material_request_item"))

        payload = report.get_procurement_console_report_context("demand_to_order_coverage")

        self.assertEqual(payload["results"]["state"]["kind"], "unavailable")
        self.assertEqual(payload["results"]["rows"], [])


    def test_item_purchase_history_returns_ready_productized_report(self):
        payload = report.get_procurement_console_report_context("item_purchase_history", {"item_code": "ITEM-002", "supplier": "SUP-001", "item_group": "Products"})

        self.assertEqual(payload["page"], {"title": "Item Purchase History", "key": "item_purchase_history"})
        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual(payload["metrics"].get("layout"), "five_up")
        self.assertIsNone(_field_by_key(payload, "company"))
        self.assertEqual(_field_by_key(payload, "item_code")["linkDoctype"], "Item")
        self.assertEqual(_field_by_key(payload, "supplier")["linkDoctype"], "Supplier")
        self.assertEqual(_field_by_key(payload, "item_group")["linkDoctype"], "Item Group")
        column_by_key = {column["key"]: column for column in payload["results"]["columns"]}
        self.assertTrue(column_by_key["item_code"].get("nowrap"))
        self.assertTrue(column_by_key["purchase_order"].get("nowrap"))
        self.assertTrue(column_by_key["order_date"].get("nowrap"))
        self.assertEqual(len(payload["results"]["rows"]), 1)
        row = payload["results"]["rows"][0]
        self.assertEqual(row["cells"]["item_code"]["value"], "ITEM-002")
        self.assertEqual(row["cells"]["purchase_order"]["value"], "PUR-OVERDUE-001")
        self.assertEqual(row["cells"]["purchase_order"]["actionKey"], "item_history:po:PUR-OVERDUE-001")
        self.assertEqual(row["cells"]["supplier"]["actionKey"], "item_history:supplier:SUP-001")
        self.assertEqual(row["cells"]["item_code"]["actionKey"], "item_history:item:ITEM-002")
        self.assertEqual(payload["action_targets"]["item_history:po:PUR-OVERDUE-001"], {"kind": "page", "route": "procurement-console-po-follow-up", "route_parts": ["PUR-OVERDUE-001"]})
        self.assertEqual(payload["action_targets"]["item_history:supplier:SUP-001"], {"kind": "page", "route": "procurement-console-supplier", "route_parts": ["SUP-001"]})
        self.assertEqual(payload["action_targets"]["item_history:item:ITEM-002"], {"kind": "page", "route": "procurement-console-item", "route_parts": ["ITEM-002"]})
        _assert_no_forbidden_mutation_actions(self, payload)
        payload_text = str(payload).lower()
        self.assertNotIn("query-report", payload_text)
        self.assertNotIn("update item price", payload_text)
        self.assertNotIn("set default supplier", payload_text)
        self.assertNotIn("create purchase order", payload_text)
        self.assertNotIn("form", payload_text)

    def test_item_purchase_history_empty_after_filter(self):
        payload = report.get_procurement_console_report_context("item_purchase_history", {"item_code": "ITEM-NOPE"})

        self.assertEqual(payload["results"]["state"]["kind"], "empty")
        self.assertEqual(payload["results"]["rows"], [])

    def test_item_purchase_history_restricted_without_purchase_order_read(self):
        _set_readable_doctypes("Supplier", "Item", "Item Price")

        payload = report.get_procurement_console_report_context("item_purchase_history")

        self.assertEqual(payload["results"]["state"]["kind"], "restricted")

    def test_item_purchase_history_hides_supplier_and_item_drilldowns_without_read(self):
        _set_readable_doctypes("Purchase Order")

        payload = report.get_procurement_console_report_context("item_purchase_history", {"item_code": "ITEM-002"})

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        row = payload["results"]["rows"][0]
        self.assertNotIn("actionKey", row["cells"]["supplier"])
        self.assertNotIn("actionKey", row["cells"]["item_code"])
        self.assertTrue(any(key.startswith("item_history:po:") for key in payload["action_targets"]))

    def test_item_purchase_history_unavailable_when_required_rate_field_missing(self):
        MISSING_FIELDS.add(("Purchase Order Item", "base_rate"))

        payload = report.get_procurement_console_report_context("item_purchase_history")

        self.assertEqual(payload["results"]["state"]["kind"], "unavailable")
        self.assertEqual(payload["results"]["rows"], [])

    def test_report_restricted_for_non_procurement_user(self):
        _set_user("sales@example.com", ["Sales User"])

        payload = report.get_procurement_console_report_context("supplier_quotation_comparison")

        self.assertEqual(payload["results"]["state"]["kind"], "restricted")

    def test_guest_report_raises_permission_error(self):
        _set_user("Guest", [])

        with self.assertRaises(_FakePermissionError):
            report.get_procurement_console_report_context("supplier_quotation_comparison")


if __name__ == "__main__":
    unittest.main()
