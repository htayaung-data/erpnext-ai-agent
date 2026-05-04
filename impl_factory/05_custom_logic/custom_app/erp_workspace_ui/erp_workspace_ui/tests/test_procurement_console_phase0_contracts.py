import sys
import types
import unittest
from datetime import date


fake_frappe = types.ModuleType("frappe")
CURRENT_ROLES = []
READABLE_DOCTYPES = {
    "Supplier",
    "Material Request",
    "Purchase Order",
    "Purchase Receipt",
    "Purchase Invoice",
    "Request for Quotation",
    "Supplier Quotation",
}
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
    return ptype == "read" and doctype in READABLE_DOCTYPES


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

from erp_workspace_ui.procurement_console import purchase_order_detail, report, service, worklist


def _set_user(user, roles):
    fake_frappe.session.user = user
    CURRENT_ROLES[:] = list(roles)


def _set_readable_doctypes(*doctypes):
    READABLE_DOCTYPES.clear()
    READABLE_DOCTYPES.update(doctypes)


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
            "Material Request",
            "Purchase Order",
            "Purchase Receipt",
            "Purchase Invoice",
            "Request for Quotation",
            "Supplier Quotation",
        )
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
            ["Overview", "Suppliers", "Purchase Requests", "Purchase Orders", "RFQs", "Supplier Quotations", "Quote Comparison"],
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

    def test_shared_console_styles_are_global_asset_contract(self):
        css_path = Path(__file__).resolve().parents[1] / "public" / "css" / "erp_workspace_ui.css"
        source = css_path.read_text()

        self.assertIn("Shared console workbench styles", source)
        self.assertIn(".sales-console-card", source)
        self.assertIn(".sales-console-kpi-card", source)
        self.assertIn(".sales-console-queue-grid", source)
        self.assertIn('data-section-grid="buying-pipeline"', source)
        self.assertIn("counter-reset: erpw-pipeline-step", source)
        self.assertIn("appearance: none", source)
        self.assertIn("grid-template-columns", source)

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
        self.assertIn('frappe.set_route(config.reportRoute, String(reportKey || "").replace(/_/g, "-"))', source)
        self.assertGreaterEqual(source.count('event.stopImmediatePropagation'), 3)

    def test_supplier_directory_uses_ready_read_only_list_contract(self):
        payload = worklist.get_procurement_console_worklist_context("supplier_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        self.assertEqual([action["key"] for action in payload["controls"]["actions"]], ["refresh", "reset_filters", "apply_filters"])
        self.assertIn("No create or edit action", payload["controls"]["scopeChips"])
        self.assertEqual(_field_by_key(payload, "supplier_group")["type"], "link")
        self.assertEqual(_field_by_key(payload, "supplier_group")["linkDoctype"], "Supplier Group")
        self.assertEqual(payload["results"]["rows"][0]["actions"], [{"key": "open_record", "label": "Open"}])
        self.assertNotIn("create_supplier", str(payload))
        self.assertEqual(payload["action_targets"]["row:SUP-001:open_record"]["kind"], "form")

    def test_material_request_directory_is_purchase_only(self):
        payload = worklist.get_procurement_console_worklist_context("purchase_request_directory")

        self.assertEqual(payload["results"]["state"]["kind"], "ready")
        filters = CAPTURED_GET_LIST_CALLS[-1]["filters"]
        self.assertTrue(_filter_contains(filters, ["Material Request", "material_request_type", "=", "Purchase"]))

    def test_procurement_filters_use_link_metadata_where_business_fields_reference_doctypes(self):
        request_payload = worklist.get_procurement_console_worklist_context("purchase_request_directory")
        order_payload = worklist.get_procurement_console_worklist_context("purchase_order_directory")
        follow_up_payload = worklist.get_procurement_console_worklist_context("purchase_orders_overdue")
        rfq_payload = worklist.get_procurement_console_worklist_context("rfq_directory")
        quotation_payload = worklist.get_procurement_console_worklist_context("supplier_quotation_directory")
        comparison_payload = report.get_procurement_console_report_context("supplier_quotation_comparison", {"company": "Demo Company"})

        self.assertEqual(_field_by_key(request_payload, "company")["linkDoctype"], "Company")
        self.assertEqual(_field_by_key(order_payload, "supplier")["linkDoctype"], "Supplier")
        self.assertEqual(_field_by_key(order_payload, "company")["linkDoctype"], "Company")
        self.assertEqual(_field_by_key(order_payload, "date_start")["label"], "PO Date From")
        self.assertEqual(_field_by_key(follow_up_payload, "supplier")["linkDoctype"], "Supplier")
        self.assertEqual(_field_by_key(follow_up_payload, "date_end")["label"], "PO Date To")
        self.assertEqual(_field_by_key(rfq_payload, "company")["linkDoctype"], "Company")
        self.assertEqual(_field_by_key(quotation_payload, "supplier")["linkDoctype"], "Supplier")
        self.assertEqual(_field_by_key(comparison_payload, "supplier_quotation")["linkDoctype"], "Supplier Quotation")
        self.assertEqual(_field_by_key(comparison_payload, "request_for_quotation")["linkDoctype"], "Request for Quotation")

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
        self.assertEqual(payload["summary"]["title"], "PUR-PARTIAL-001")
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
        self.assertEqual(payload["results"]["rows"][0]["actions"], [{"key": "open_record", "label": "Open"}])
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
