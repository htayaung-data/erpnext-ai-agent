from __future__ import annotations

from copy import deepcopy
from typing import Any


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
	"status": "phase_0",
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
	},
	"methods": {
		"bootstrap": "erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap",
		"sidebar_context": "erp_workspace_ui.procurement_console.service.get_procurement_console_sidebar_context",
		"workspace_search": "erp_workspace_ui.procurement_console.service.search_procurement_console_workspace",
		"worklist_context": "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context",
		"report_context": "erp_workspace_ui.procurement_console.report.get_procurement_console_report_context",
	},
	"managed_doctypes": {
		"Supplier": "supplier_directory",
		"Supplier Group": "supplier_directory",
		"Item": "supplier_price_review",
		"Item Price": "supplier_price_review",
		"Item Supplier": "supplier_price_review",
		"Material Request": "purchase_request_directory",
		"Request for Quotation": "rfq_directory",
		"Supplier Quotation": "supplier_quotation_directory",
		"Purchase Order": "purchase_order_directory",
		"Purchase Receipt": "pending_receipt_visibility",
		"Purchase Invoice": "billing_status_visibility",
	},
	"directory_queues_by_doctype": {
		"Supplier": "supplier_directory",
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
		"status": "phase_0",
	},
	{
		"workspace_id": "warehouse",
		"matrix_name": "Warehouse Console",
		"recommended_name": "Warehouse Console",
		"wave": "first",
		"priority": 3,
		"status": "planned",
	},
	{
		"workspace_id": "finance",
		"matrix_name": "Finance Console",
		"recommended_name": "Finance Control Desk",
		"wave": "first",
		"priority": 4,
		"status": "name_review",
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
		if normalized in {routes.get("launcher"), routes.get("home"), routes.get("worklist"), routes.get("report")}:
			return deepcopy(workspace)
	return None


def get_workspace_roadmap() -> list[dict[str, Any]]:
	return [deepcopy(item) for item in _WORKSPACE_ROADMAP]


def get_sales_workspace_definition() -> dict[str, Any]:
	return get_workspace_definition("sales")


def get_procurement_workspace_definition() -> dict[str, Any]:
	return get_workspace_definition("procurement")
