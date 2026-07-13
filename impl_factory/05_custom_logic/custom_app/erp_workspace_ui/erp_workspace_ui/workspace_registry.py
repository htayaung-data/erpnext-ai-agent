from __future__ import annotations

from copy import deepcopy
from typing import Any


WORKSPACE_SIDEBAR_SCHEMA_VERSION = "workspace-sidebar.v1"

_SALES_WORKSPACE: dict[str, Any] = {
	"workspace_id": "sales",
	"status": "frozen",
	"title": "Sales Console",
	"mode_label": "Sales Workspace",
	"role_family": "Sales",
	"freeze_tag": "sales-console-freeze-v1",
	"routes": {
		"launcher": "sales-console-home",
		"launcher_path": "/desk/sales-console-home",
		"home": "sales-console",
		"home_path": "/desk/sales-console",
		"worklist": "sales-console-worklist",
		"report": "sales-console-report",
	},
	"methods": {
		"bootstrap": "erp_workspace_ui.sales_console.service.get_sales_console_bootstrap",
		"sidebar_context": "erp_workspace_ui.sales_console.service.get_sales_console_sidebar_context",
		"workspace_search": "erp_workspace_ui.sales_console.service.search_sales_console_workspace",
		"worklist_context": "erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context",
		"report_context": "erp_workspace_ui.sales_console.report.get_sales_console_report_context",
	},
	"managed_doctypes": {
		"Quotation": "quotation_directory",
		"Sales Order": "sales_order_directory",
		"Customer": "customer_directory",
		"Item": "item_directory",
		"Delivery Note": "sales_order_directory",
		"Sales Invoice": "sales_order_directory",
	},
	"directory_queues_by_doctype": {
		"Quotation": "quotation_directory",
		"Sales Order": "sales_order_directory",
		"Customer": "customer_directory",
		"Item": "item_directory",
	},
	"sidebar": {
		"home_key": "sales_console_home",
		"home_label": "Overview",
		"section_key": "browse",
		"section_label": "Browse",
	},
	"fallback_items": [
		{"key": "sales_console_home", "label": "Overview", "icon": "home", "target": {"kind": "page", "route": "sales-console"}},
		{"key": "quotation_directory", "label": "Quotations", "icon": "quotation", "target": {"kind": "worklist", "queue_key": "quotation_directory"}},
		{"key": "sales_order_directory", "label": "Sales Orders", "icon": "order", "target": {"kind": "worklist", "queue_key": "sales_order_directory"}},
		{"key": "customer_directory", "label": "Customers", "icon": "customer", "target": {"kind": "worklist", "queue_key": "customer_directory"}},
		{"key": "item_directory", "label": "Items", "icon": "item", "target": {"kind": "worklist", "queue_key": "item_directory"}},
	],
}


_PROCUREMENT_WORKSPACE: dict[str, Any] = {
	"workspace_id": "procurement",
	"status": "phase_3",
	"title": "Procurement Console",
	"mode_label": "Procurement Workspace",
	"role_family": "Procurement",
	"routes": {
		"launcher": "procurement-console-home",
		"launcher_path": "/desk/procurement-console-home",
		"home": "procurement-console",
		"home_path": "/desk/procurement-console",
		"worklist": "procurement-console-worklist",
		"report": "procurement-console-report",
		"po_follow_up": "procurement-console-po-follow-up",
		"supplier_detail": "procurement-console-supplier",
		"item_detail": "procurement-console-item",
		"purchase_request_review": "procurement-console-purchase-request-review",
		"purchase_request_form": "procurement-console-purchase-request-form",
		"rfq_review": "procurement-console-rfq-review",
		"rfq_form": "procurement-console-rfq-form",
		"supplier_quotation_form": "procurement-console-supplier-quotation-form",
		"supplier_quotation_review": "procurement-console-supplier-quotation-review",
		"purchase_order_form": "procurement-console-purchase-order-form",
	},
	"methods": {
		"bootstrap": "erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap",
		"sidebar_context": "erp_workspace_ui.procurement_console.service.get_procurement_console_sidebar_context",
		"workspace_search": "erp_workspace_ui.procurement_console.service.search_procurement_console_workspace",
		"quick_find": "erp_workspace_ui.procurement_console.service.get_procurement_quick_find_suggestions",
		"worklist_context": "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context",
		"report_context": "erp_workspace_ui.procurement_console.report.get_procurement_console_report_context",
		"po_follow_up_detail_context": "erp_workspace_ui.procurement_console.purchase_order_detail.get_purchase_order_follow_up_detail_context",
		"supplier_detail_context": "erp_workspace_ui.procurement_console.supplier_detail.get_supplier_detail_context",
		"item_detail_context": "erp_workspace_ui.procurement_console.items.get_item_detail_context",
		"purchase_request_review_context": "erp_workspace_ui.procurement_console.document_reviews.get_purchase_request_review_context",
		"managed_purchase_request_context": "erp_workspace_ui.procurement_console.managed_purchase_request.get_managed_purchase_request_context",
		"managed_purchase_request_save": "erp_workspace_ui.procurement_console.managed_purchase_request.save_managed_purchase_request_draft",
		"managed_purchase_request_item_defaults": "erp_workspace_ui.procurement_console.managed_purchase_request.get_managed_purchase_request_item_defaults",
		"managed_rfq_context": "erp_workspace_ui.procurement_console.managed_rfq.get_managed_rfq_context",
		"managed_rfq_save": "erp_workspace_ui.procurement_console.managed_rfq.save_managed_rfq_draft",
		"managed_rfq_item_defaults": "erp_workspace_ui.procurement_console.managed_rfq.get_managed_rfq_item_defaults",
		"managed_supplier_quotation_context": "erp_workspace_ui.procurement_console.managed_supplier_quotation.get_managed_supplier_quotation_context",
		"managed_supplier_quotation_save": "erp_workspace_ui.procurement_console.managed_supplier_quotation.save_managed_supplier_quotation_draft",
		"managed_supplier_quotation_item_defaults": "erp_workspace_ui.procurement_console.managed_supplier_quotation.get_managed_supplier_quotation_item_defaults",
		"managed_purchase_order_context": "erp_workspace_ui.procurement_console.managed_purchase_order.get_managed_purchase_order_context",
		"managed_purchase_order_save": "erp_workspace_ui.procurement_console.managed_purchase_order.save_managed_purchase_order",
		"managed_purchase_order_item_defaults": "erp_workspace_ui.procurement_console.managed_purchase_order.get_managed_purchase_order_item_defaults",
		"rfq_review_context": "erp_workspace_ui.procurement_console.document_reviews.get_rfq_review_context",
		"supplier_quotation_review_context": "erp_workspace_ui.procurement_console.document_reviews.get_supplier_quotation_review_context",
	},
	"managed_doctypes": {
		"Supplier": "supplier_directory",
		"Supplier Group": "supplier_directory",
		"Item": "buying_item_directory",
		"Item Price": "buying_item_directory",
		"Item Supplier": "buying_item_directory",
		"Material Request": "purchase_request_directory",
		"Request for Quotation": "rfq_directory",
		"Supplier Quotation": "supplier_quotation_directory",
		"Purchase Order": "purchase_order_directory",
		"Purchase Receipt": "pending_receipt_visibility",
		"Purchase Invoice": "billing_status_visibility",
	},
	"directory_queues_by_doctype": {
		"Supplier": "supplier_directory",
		"Item": "buying_item_directory",
		"Material Request": "purchase_request_directory",
		"Request for Quotation": "rfq_directory",
		"Supplier Quotation": "supplier_quotation_directory",
		"Purchase Order": "purchase_order_directory",
	},
	"downstream_visibility_doctypes": {
		"Purchase Receipt": "pending_receipt_visibility",
		"Purchase Invoice": "billing_status_visibility",
	},
	"sidebar": {
		"home_key": "procurement_console_home",
		"home_label": "Overview",
		"section_key": "workspace",
		"section_label": "Workspace",
	},
	"fallback_items": [
		{
			"key": "procurement_console_home",
			"label": "Overview",
			"icon": "home",
			"target": {"kind": "page", "route": "procurement-console"},
		},
		{
			"key": "supplier_directory",
			"label": "Suppliers",
			"icon": "customer",
			"target": {"kind": "worklist", "queue_key": "supplier_directory"},
		},
		{
			"key": "purchase_request_directory",
			"label": "Purchase Requests",
			"icon": "quotation",
			"target": {"kind": "worklist", "queue_key": "purchase_request_directory"},
		},
		{
			"key": "purchase_order_directory",
			"label": "Purchase Orders",
			"icon": "order",
			"target": {"kind": "worklist", "queue_key": "purchase_order_directory"},
		},
		{
			"key": "rfq_directory",
			"label": "RFQs",
			"icon": "quotation",
			"target": {"kind": "worklist", "queue_key": "rfq_directory"},
		},
		{
			"key": "supplier_quotation_directory",
			"label": "Supplier Quotations",
			"icon": "quotation",
			"target": {"kind": "worklist", "queue_key": "supplier_quotation_directory"},
		},
		{
			"key": "buying_item_directory",
			"label": "Buying Items",
			"icon": "item",
			"target": {"kind": "worklist", "queue_key": "buying_item_directory"},
		},
		{
			"key": "procurement_reports",
			"label": "Reports",
			"icon": "report",
			"target": {"kind": "page", "route": "procurement-console-report"},
		},
	],
}


_WAREHOUSE_WORKSPACE: dict[str, Any] = {
	"workspace_id": "warehouse",
	"status": "w8c_transfer_visibility",
	"title": "Warehouse Console",
	"mode_label": "Warehouse Workspace",
	"role_family": "Warehouse",
	"routes": {
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
	"methods": {
		"overview": "erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview",
		"inbound_queue": "erp_workspace_ui.warehouse_console.service.get_warehouse_inbound_receiving_queue",
		"outbound_queue": "erp_workspace_ui.warehouse_console.service.get_warehouse_outbound_picking_queue",
		"receiving_detail": "erp_workspace_ui.warehouse_console.service.get_warehouse_receiving_review",
		"picking_detail": "erp_workspace_ui.warehouse_console.service.get_warehouse_picking_review",
		"returns_work_hub": "erp_workspace_ui.warehouse_console.service.get_warehouse_returns_work_hub",
		"internal_transfer_workflow": "erp_workspace_ui.warehouse_console.service.get_warehouse_internal_transfer_workflow",
		"cycle_count_workflow": "erp_workspace_ui.warehouse_console.service.get_warehouse_cycle_count_workflow",
		"customer_return_intake_draft": "erp_workspace_ui.warehouse_console.service.save_warehouse_customer_return_intake_draft",
		"customer_return_manager_decision": "erp_workspace_ui.warehouse_console.service.save_warehouse_customer_return_manager_decision",
		"supplier_return_candidate_draft": "erp_workspace_ui.warehouse_console.service.save_warehouse_supplier_return_candidate_draft",
		"supplier_return_manager_decision": "erp_workspace_ui.warehouse_console.service.save_warehouse_supplier_return_manager_decision",
		"internal_transfer_candidate_draft": "erp_workspace_ui.warehouse_console.service.save_warehouse_internal_transfer_candidate_draft",
		"internal_transfer_manager_decision": "erp_workspace_ui.warehouse_console.service.save_warehouse_internal_transfer_manager_decision",
		"cycle_count_task_draft": "erp_workspace_ui.warehouse_console.service.save_warehouse_cycle_count_task_draft",
		"cycle_count_manager_decision": "erp_workspace_ui.warehouse_console.service.save_warehouse_cycle_count_manager_decision",
		"stock_exceptions": "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_exceptions",
		"stock_exception_review": "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_exception_review",
		"stock_posture_review": "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_posture_review",
		"movement_visibility": "erp_workspace_ui.warehouse_console.service.get_warehouse_movement_visibility_queue",
		"movement_review": "erp_workspace_ui.warehouse_console.service.get_warehouse_movement_review",
		"transfer_visibility": "erp_workspace_ui.warehouse_console.service.get_warehouse_transfer_visibility_queue",
		"quick_find": "erp_workspace_ui.warehouse_console.service.get_warehouse_quick_find_suggestions",
		"workspace_search": "erp_workspace_ui.warehouse_console.service.search_warehouse_console_workspace",
		"sidebar_context": "erp_workspace_ui.warehouse_console.service.get_warehouse_console_sidebar_context",
	},
	"managed_doctypes": {
		"Warehouse": "warehouse_console_home",
		"Item": "warehouse_console_home",
		"Bin": "warehouse_console_home",
		"Purchase Order": "inbound_receiving",
		"Sales Order": "outbound_picking",
		"Purchase Order Item": "stock_exceptions",
		"Sales Order Item": "stock_exceptions",
		"Stock Entry": "movement_visibility",
		"Stock Entry Detail": "movement_visibility",
	},
	"sidebar": {
		"home_key": "warehouse_console_home",
		"home_label": "Overview",
		"section_key": "workspace",
		"section_label": "Workspace",
	},
	"search": {
		"enabled": True,
		"mode": "warehouse_sidebar_search",
		"placement": "sidebar_utility",
		"placeholder": "Find purchase orders, sales orders, items, warehouses, or movements",
	},
	"fallback_items": [
		{
			"key": "warehouse_console_home",
			"label": "Overview",
			"icon": "item",
			"target": {"kind": "page", "route": "warehouse-console"},
		},
		{
			"key": "inbound_receiving",
			"label": "Inbound Receiving",
			"icon": "quotation",
			"target": {"kind": "worklist", "queue_key": "inbound_receiving"},
		},
		{
			"key": "outbound_picking",
			"label": "Outbound Picking",
			"icon": "order",
			"target": {"kind": "worklist", "queue_key": "outbound_picking"},
		},
		{
			"key": "stock_exceptions",
			"label": "Stock Exceptions",
			"icon": "report",
			"target": {"kind": "worklist", "queue_key": "stock_exceptions"},
		},
		{
			"key": "returns_work_hub",
			"label": "Returns",
			"icon": "return",
			"target": {"kind": "worklist", "queue_key": "returns_work_hub"},
		},
		{
			"key": "internal_transfer_workflow",
			"label": "Internal Transfer",
			"icon": "stock",
			"target": {"kind": "worklist", "queue_key": "internal_transfer_workflow"},
		},
		{
			"key": "cycle_count_workflow",
			"label": "Cycle Count",
			"icon": "report",
			"target": {"kind": "worklist", "queue_key": "cycle_count_workflow"},
		},
		{
			"key": "movement_visibility",
			"label": "Movement Visibility",
			"icon": "stock",
			"target": {"kind": "worklist", "queue_key": "movement_visibility"},
		},
		{
			"key": "transfer_visibility",
			"label": "Transfer Visibility",
			"icon": "stock",
			"target": {"kind": "worklist", "queue_key": "transfer_visibility"},
		},
	],
}


_FINANCE_WORKSPACE: dict[str, Any] = {
	"workspace_id": "finance",
	"status": "cycle_1_f6_quality_gate_pending",
	"title": "Finance Control Desk",
	"workspace_family": "Finance & Accounting",
	"mode_label": "Read-only aggregate posture",
	"role_family": "Finance & Accounting",
	"routes": {
		"home": "finance-control-desk",
		"home_path": "/desk/finance-control-desk",
	},
	"methods": {
		"shell_context": "erp_workspace_ui.finance_accounting.service.get_finance_control_desk_shell_context",
		"overview_context": "erp_workspace_ui.finance_accounting.service.get_finance_control_desk_overview_context",
		"sidebar_context": "erp_workspace_ui.finance_accounting.service.get_finance_control_desk_sidebar_context",
		"workspace_search": "erp_workspace_ui.finance_accounting.service.search_finance_control_desk_workspace",
	},
	"managed_doctypes": {},
	"directory_queues_by_doctype": {},
	"sidebar": {
		"home_key": "finance_control_desk_home",
		"home_label": "Overview",
		"section_key": "workspace",
		"section_label": "Workspace",
	},
	"search": {
		"enabled": False,
		"mode": "finance_cycle_1_aggregate_posture_no_rows",
		"placement": "none",
		"placeholder": "Finance search is not available in Cycle 1",
	},
	"fallback_items": [
		{
			"key": "finance_control_desk_home",
			"label": "Overview",
			"icon": "home",
			"target": {"kind": "page", "route": "finance-control-desk"},
		},
	],
}


_WORKSPACE_ROADMAP: tuple[dict[str, Any], ...] = (
	{
		"workspace_id": "sales",
		"matrix_name": "Sales Console",
		"recommended_name": "Sales Console",
		"wave": "first",
		"priority": 1,
		"status": "frozen",
	},
	{
		"workspace_id": "procurement",
		"matrix_name": "Procurement Console",
		"recommended_name": "Procurement Console",
		"wave": "first",
		"priority": 2,
		"status": "phase_3",
	},
	{
		"workspace_id": "warehouse",
		"matrix_name": "Warehouse Console",
		"recommended_name": "Warehouse Console",
		"wave": "first",
		"priority": 3,
		"status": "w8c_transfer_visibility",
	},
	{
		"workspace_id": "finance",
		"matrix_name": "Finance Console",
		"recommended_name": "Finance Control Desk",
		"wave": "first",
		"priority": 4,
		"status": "cycle_1_f6_quality_gate_pending",
	},
	{
		"workspace_id": "executive",
		"matrix_name": "Executive Console",
		"recommended_name": "Management Daily Brief",
		"wave": "second",
		"priority": 5,
		"status": "name_review",
	},
	{
		"workspace_id": "customer_service",
		"matrix_name": "Customer Service Console",
		"recommended_name": "Customer Service Console",
		"wave": "second",
		"priority": 6,
		"status": "planned",
	},
	{
		"workspace_id": "hr_admin",
		"matrix_name": "HR and Admin Console",
		"recommended_name": "HR and Admin Console",
		"wave": "second",
		"priority": 7,
		"status": "planned",
	},
	{
		"workspace_id": "erp_admin",
		"matrix_name": "ERP Admin Console",
		"recommended_name": "ERP Admin Console",
		"wave": "second",
		"priority": 8,
		"status": "planned",
	},
)


_ACTIVE_WORKSPACES: dict[str, dict[str, Any]] = {
	"sales": _SALES_WORKSPACE,
	"procurement": _PROCUREMENT_WORKSPACE,
	"warehouse": _WAREHOUSE_WORKSPACE,
	"finance": _FINANCE_WORKSPACE,
}


def get_workspace_definition(workspace_id: str = "sales") -> dict[str, Any]:
	workspace = _ACTIVE_WORKSPACES.get(str(workspace_id or "").strip())
	if not workspace:
		raise KeyError(f"Unknown active workspace: {workspace_id}")
	return deepcopy(workspace)


def get_active_workspace_definitions() -> list[dict[str, Any]]:
	return [deepcopy(workspace) for workspace in _ACTIVE_WORKSPACES.values()]


def get_workspace_by_route(route_key: str) -> dict[str, Any] | None:
	normalized = str(route_key or "").strip()
	if not normalized:
		return None

	for workspace in _ACTIVE_WORKSPACES.values():
		routes = workspace.get("routes") or {}
		route_values = {str(value) for key, value in routes.items() if not str(key).endswith("_path")}
		if normalized in route_values:
			return deepcopy(workspace)
	return None


def get_workspace_roadmap() -> list[dict[str, Any]]:
	return [deepcopy(item) for item in _WORKSPACE_ROADMAP]


def get_sales_workspace_definition() -> dict[str, Any]:
	return get_workspace_definition("sales")


def get_procurement_workspace_definition() -> dict[str, Any]:
	return get_workspace_definition("procurement")



def get_warehouse_workspace_definition() -> dict[str, Any]:
	return get_workspace_definition("warehouse")


def get_finance_workspace_definition() -> dict[str, Any]:
	return get_workspace_definition("finance")
