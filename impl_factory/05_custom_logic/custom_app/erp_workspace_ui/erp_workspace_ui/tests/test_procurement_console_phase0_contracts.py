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
    "Material Request",
    "Purchase Order",
    "Purchase Receipt",
    "Purchase Invoice",
    "Request for Quotation",
    "Supplier Quotation",
}
WRITEABLE_DOCTYPES = set()
CREATEABLE_DOCTYPES = set()
CAPTURED_GET_LIST_CALLS = []
CAPTURED_GET_ALL_CALLS = []
CAPTURED_REPORT_CALLS = []
HAS_QUOTE_STATUS = True
HIDDEN_PURCHASE_ORDER_LIST_NAMES = set()


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
            }
        ], filters)
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
            }
        ], filters)
    if doctype == "Material Request":
        return _filter_rows(doctype, [
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
    if doctype == "Purchase Order":
        rows = _filter_rows(doctype, _purchase_order_rows(), filters)
        return [row for row in rows if row["name"] not in HIDDEN_PURCHASE_ORDER_LIST_NAMES]
    if doctype == "Request for Quotation":
        return _filter_rows(doctype, [
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
    if doctype == "Supplier Quotation":
        return _filter_rows(doctype, [
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
    if doctype == "Request for Quotation Supplier":
        rows = [
            {"parent": "RFQ-001", "supplier": "SUP-001", "supplier_name": "Alpha Supplier", "quote_status": "Pending"},
            {"parent": "RFQ-001", "supplier": "SUP-002", "supplier_name": "Beta Supplier", "quote_status": "Received"},
            {"parent": "RFQ-002", "supplier": "SUP-003", "supplier_name": "Gamma Supplier", "quote_status": "Pending"},
        ]
        status_filter = (filters or {}).get("quote_status") if isinstance(filters, dict) else None
        if status_filter:
            rows = [row for row in rows if row["quote_status"] == status_filter]
        parent_filter = (filters or {}).get("parent") if isinstance(filters, dict) else None
        if isinstance(parent_filter, list) and len(parent_filter) == 2 and parent_filter[0] == "in":
            rows = [row for row in rows if row["parent"] in set(parent_filter[1])]
        return rows
    if doctype == "Dynamic Link":
        if isinstance(filters, dict) and filters.get("link_doctype") == "Supplier" and filters.get("link_name") == "SUP-001":
            return [{"parent": "CONT-001"}]
        return []
    if doctype == "Item Supplier":
        if isinstance(filters, dict) and filters.get("parent") == "ITEM-001":
            return [
                {
                    "name": "ITEM-SUP-001",
                    "parent": "ITEM-001",
                    "supplier": "SUP-001",
                    "supplier_part_no": "SUP-WIDGET-001",
                    "lead_time_days": 5,
                    "modified": "2026-05-03",
                }
            ]
        return []
    if doctype == "Supplier Quotation Item":
        if isinstance(filters, dict) and filters.get("item_code") == "ITEM-001":
            return [{"parent": "SUP-QTN-001", "item_code": "ITEM-001"}]
        return []
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
                "received_qty": 0,
                "warehouse": "Stores - DC",
                "material_request": "MAT-MR-001",
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
                "received_qty": 0,
                "warehouse": "Stores - DC",
                "material_request": "MAT-MR-002",
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
                "received_qty": 4,
                "warehouse": "Stores - DC",
                "material_request": "MAT-MR-003",
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
                "received_qty": 6,
                "warehouse": "Stores - DC",
                "material_request": "MAT-MR-004",
                "supplier_quotation": "SUP-QTN-004",
            },
        ]
        parent_filter = (filters or {}).get("parent") if isinstance(filters, dict) else None
        if isinstance(parent_filter, list) and len(parent_filter) == 2 and parent_filter[0] == "in":
            rows = [row for row in rows if row["parent"] in set(parent_filter[1])]
        elif parent_filter:
            rows = [row for row in rows if row["parent"] == parent_filter]
        item_filter = (filters or {}).get("item_code") if isinstance(filters, dict) else None
        if item_filter:
            rows = [row for row in rows if row["item_code"] == item_filter]
        return rows
    if doctype == "Purchase Receipt Item":
        return [
            {
                "parent": "MAT-PRE-001",
                "item_code": "ITEM-003",
                "qty": 4,
                "received_qty": 4,
                "rejected_qty": 0,
                "warehouse": "Stores - DC",
                "billed_amt": 500,
            }
        ]
    if doctype == "Purchase Invoice Item":
        return [
            {
                "parent": "ACC-PINV-001",
                "item_code": "ITEM-003",
                "qty": 2,
                "amount": 500,
                "purchase_receipt": "MAT-PRE-001",
            }
        ]
    return []


def _db_get_value(doctype, name=None, fieldname=None, as_dict=False, **kwargs):
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
        if self.doctype == "Request for Quotation Supplier" and fieldname == "quote_status":
            return HAS_QUOTE_STATUS
        return True


def _run_query_report(report_name, filters=None, ignore_prepared_report=None, **kwargs):
    CAPTURED_REPORT_CALLS.append(
        {
            "report_name": report_name,
            "filters": filters,
            "ignore_prepared_report": ignore_prepared_report,
        }
    )
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
fake_frappe.db = types.SimpleNamespace(
    get_value=_db_get_value,
    exists=lambda *args, **kwargs: False,
    get_single_value=lambda doctype, fieldname: "Demo Company" if doctype == "Global Defaults" else None,
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
fake_frappe.get_meta = lambda doctype: _FakeMeta(doctype)
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

from erp_workspace_ui.procurement_console import items, purchase_order_detail, report, service, supplier_detail, worklist


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
        global HAS_QUOTE_STATUS
        HAS_QUOTE_STATUS = True
        _set_user("purchase@example.com", ["Purchase User"])
        _set_readable_doctypes(
            "Supplier",
            "Item",
            "Item Price",
            "Material Request",
            "Purchase Order",
            "Purchase Receipt",
            "Purchase Invoice",
            "Request for Quotation",
            "Supplier Quotation",
        )
        _set_writeable_doctypes()
        _set_createable_doctypes()
        CAPTURED_GET_LIST_CALLS.clear()
        CAPTURED_GET_ALL_CALLS.clear()
        CAPTURED_REPORT_CALLS.clear()
        HIDDEN_PURCHASE_ORDER_LIST_NAMES.clear()

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
                "supplier_quotation_comparison",
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
        _set_createable_doctypes("Material Request", "Request for Quotation", "Supplier Quotation", "Purchase Order")

        payload = service.get_procurement_console_bootstrap()

        self.assertEqual(
            [action["key"] for action in payload["create_actions"]],
            ["new_purchase_request", "new_rfq", "new_supplier_quotation", "new_purchase_order"],
        )
        self.assertEqual([action["variant"] for action in payload["create_actions"]], ["primary", "primary", "primary", "primary"])
        self.assertEqual(payload["action_targets"]["new_purchase_request"]["kind"], "new_doc")
        self.assertEqual(payload["action_targets"]["new_purchase_request"]["doctype"], "Material Request")
        self.assertEqual(payload["action_targets"]["new_purchase_request"]["defaults"], {"material_request_type": "Purchase"})
        self.assertEqual(payload["action_targets"]["new_purchase_order"]["doctype"], "Purchase Order")
        self.assertNotIn("new_supplier", payload["action_targets"])
        self.assertNotIn("new_item", payload["action_targets"])

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
        self.assertIn("new_doc", source)
        self.assertIn('frappe.set_route("Form"', source)
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
            ["Overview", "Suppliers", "Purchase Requests", "Purchase Orders", "RFQs", "Supplier Quotations", "Buying Items", "Quote Comparison"],
        )
        self.assertEqual(payload["sidebar"]["items"][-1]["target"]["kind"], "report_page")

    def test_procurement_workspace_search_is_permission_aware_and_productized(self):
        payload = service.search_procurement_console_workspace("Alpha")

        self.assertEqual(payload["state"], "ready")
        self.assertTrue(payload["results"])
        self.assertTrue(all((item["target"] or {}).get("kind") == "worklist" for item in payload["results"]))
        self.assertTrue(any(item["doctype"] == "Supplier" for item in payload["results"]))

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
        self.assertIn("main-count-4", source)
        self.assertIn('data-erpw-list-field-shell-key="date_start"', source)
        self.assertIn('data-erpw-list-field-shell-key="date_end"', source)
        self.assertIn("data-erpw-list-field-role", source)
        self.assertIn("data-erpw-list-field-group", source)
        self.assertIn("erpw-list-result-summary", source)
        self.assertIn("data-erpw-list-metric-count", source)
        self.assertIn("grid-template-columns: minmax(210px, 270px)", source)

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
        self.assertIn('frappe.set_route("procurement-console")', source)
        self.assertIn('salesWorkspaceRoute("launcher", "sales-console-home")', source)
        self.assertIn("scheduleRoleHomeRedirect", source)

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
        self.assertIn("Create action left Procurement shell visible", source)
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

    def test_supplier_detail_native_form_action_requires_manager_and_write_permission(self):
        _set_user("manager@example.com", ["Purchase Manager"])
        _set_writeable_doctypes("Supplier")

        manager_payload = supplier_detail.get_supplier_detail_context("SUP-001")

        supplier_target = manager_payload["action_targets"]["open_supplier_form"]
        self.assertEqual(supplier_target["kind"], "form")
        self.assertEqual(supplier_target["doctype"], "Supplier")
        self.assertEqual(supplier_target["name"], "SUP-001")
        self.assertEqual(supplier_target["native_chrome"]["parentLabel"], "Suppliers")
        self.assertEqual(supplier_target["native_chrome"]["leafLabel"], "ERP Supplier Form")
        self.assertEqual([action["key"] for action in manager_payload["controls"]["actions"]], ["back_to_suppliers", "refresh", "open_supplier_form"])
        self.assertEqual([action["icon"] for action in manager_payload["controls"]["actions"]], ["arrow-left", "refresh", "external-link"])

        _set_user("purchase@example.com", ["Purchase User"])
        user_payload = supplier_detail.get_supplier_detail_context("SUP-001")

        self.assertNotIn("open_supplier_form", user_payload["action_targets"])

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
        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Item", "is_purchase_item", "=", 1]))
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

    def test_buying_item_native_form_action_requires_item_write_governance(self):
        _set_user("master@example.com", ["Purchase Master Manager"])
        _set_writeable_doctypes("Item")

        payload = items.get_item_detail_context("ITEM-001")

        item_target = payload["action_targets"]["open_item_form"]
        self.assertEqual(item_target["kind"], "form")
        self.assertEqual(item_target["doctype"], "Item")
        self.assertEqual(item_target["name"], "ITEM-001")
        self.assertEqual(item_target["native_chrome"]["parentLabel"], "Buying Items")
        self.assertEqual(item_target["native_chrome"]["leafLabel"], "ERP Item Form")
        self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["back_to_items", "refresh", "open_item_form"])
        self.assertEqual([action["icon"] for action in payload["controls"]["actions"]], ["arrow-left", "refresh", "external-link"])

        _set_user("manager@example.com", ["Purchase Manager"])
        manager_payload = items.get_item_detail_context("ITEM-001")

        self.assertNotIn("open_item_form", manager_payload["action_targets"])

    def test_material_request_directory_is_purchase_only(self):
        payload = worklist.get_procurement_console_worklist_context("purchase_request_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual(payload["results"]["rows"][0]["actions"], [{"key": "open_erp_form", "label": "Open ERP Form"}])
        request_target = payload["action_targets"]["row:MAT-MR-001:open_erp_form"]
        self.assertEqual(request_target["kind"], "form")
        self.assertEqual(request_target["doctype"], "Material Request")
        self.assertEqual(request_target["native_chrome"]["parentLabel"], "Purchase Requests")
        self.assertEqual(request_target["native_chrome"]["leafLabel"], "MAT-MR-001")
        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Material Request", "material_request_type", "=", "Purchase"]))

    def test_procurement_filters_use_link_metadata_where_business_fields_reference_doctypes(self):
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
        self.assertEqual(_field_by_key(request_payload, "keyword")["label"], "Search request text")
        self.assertEqual(_field_by_key(order_payload, "purchase_order")["linkDoctype"], "Purchase Order")
        self.assertEqual(_field_by_key(order_payload, "purchase_order")["placeholder"], "Select purchase order")
        self.assertEqual(_field_by_key(order_payload, "supplier")["linkDoctype"], "Supplier")
        self.assertEqual(_field_by_key(order_payload, "supplier")["placeholder"], "Select supplier")
        self.assertEqual(_field_by_key(order_payload, "keyword")["label"], "Search order ID or supplier")
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
        self.assertIsNone(_field_by_key(comparison_payload, "company"))
        self.assertEqual(_field_by_key(comparison_payload, "item_code")["linkDoctype"], "Item")
        self.assertEqual(_field_by_key(comparison_payload, "item_code")["placeholder"], "Select item")
        self.assertEqual(_field_by_key(comparison_payload, "supplier_quotation")["linkDoctype"], "Supplier Quotation")
        self.assertEqual(_field_by_key(comparison_payload, "supplier_quotation")["placeholder"], "Select supplier quotation")
        self.assertEqual(_field_by_key(comparison_payload, "request_for_quotation")["linkDoctype"], "Request for Quotation")
        self.assertEqual(_field_by_key(comparison_payload, "request_for_quotation")["placeholder"], "Select RFQ")

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
        self.assertEqual(payload["results"]["rows"][0]["actions"], [{"key": "open_erp_form", "label": "Open ERP Form"}])
        rfq_target = payload["action_targets"]["row:RFQ-001:open_erp_form"]
        self.assertEqual(rfq_target["kind"], "form")
        self.assertEqual(rfq_target["doctype"], "Request for Quotation")
        self.assertEqual(rfq_target["native_chrome"]["parentLabel"], "RFQs")
        self.assertIn("No send/email action", payload["controls"]["scopeChips"])
        self.assertNotIn("send_email", str(payload))

    def test_rfqs_awaiting_response_uses_quote_status(self):
        payload = worklist.get_procurement_console_worklist_context("rfqs_awaiting_supplier_response")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertTrue(any(call["doctype"] == "Request for Quotation Supplier" and call["filters"].get("quote_status") == "Pending" for call in CAPTURED_GET_ALL_CALLS))
        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Request for Quotation", "docstatus", "=", 1]))

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

    def test_supplier_quotation_directory_is_read_only(self):
        payload = worklist.get_procurement_console_worklist_context("supplier_quotation_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        payload_text = str(payload).lower()
        self.assertNotIn("create", payload_text)
        self.assertNotIn("purchase_order", payload_text)
        self.assertNotIn("item_price", payload_text)
        self.assertNotIn("set_default_supplier", payload_text)
        self.assertEqual(payload["results"]["rows"][0]["actions"], [{"key": "open_erp_form", "label": "Open ERP Form"}])
        quotation_target = payload["action_targets"]["row:SUP-QTN-001:open_erp_form"]
        self.assertEqual(quotation_target["kind"], "form")
        self.assertEqual(quotation_target["doctype"], "Supplier Quotation")
        self.assertEqual(quotation_target["native_chrome"]["parentLabel"], "Supplier Quotations")

    def test_supplier_quotations_to_compare_filters_submitted_visible_records(self):
        payload = worklist.get_procurement_console_worklist_context("supplier_quotations_to_compare")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Supplier Quotation", "docstatus", "=", 1]))
        self.assertTrue(_filter_contains(filters, ["Supplier Quotation", "status", "not in", ["Cancelled", "Stopped"]]))

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

    def test_supplier_quotation_comparison_wraps_native_report_without_mutation_tools(self):
        payload = report.get_procurement_console_report_context(
            "supplier_quotation_comparison",
            {"company": "Demo Company", "supplier": "SUP-001", "include_expired": "1"},
        )

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual(CAPTURED_REPORT_CALLS[-1]["report_name"], "Supplier Quotation Comparison")
        self.assertEqual(CAPTURED_REPORT_CALLS[-1]["filters"]["supplier"], ["SUP-001"])
        self.assertEqual(CAPTURED_REPORT_CALLS[-1]["filters"]["include_expired"], 1)
        self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["refresh", "back_to_console"])
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
            ["refresh", "back_to_console"],
        )

    def test_later_phase_report_returns_unavailable_not_ready(self):
        payload = report.get_procurement_console_report_context("purchase_order_analysis")

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
