from __future__ import annotations

from copy import deepcopy
from typing import Any


VALID_ROUTE_CLASSIFICATIONS = frozenset(
	{
		"productized_overview",
		"productized_worklist",
		"productized_report",
		"productized_detail",
		"managed_create_edit",
		"governed_native_exception",
		"not_allowed_leakage",
	}
)

VALID_ACTION_CLASSIFICATIONS = frozenset(
	{
		"productized_navigation",
		"productized_primary_action",
		"productized_secondary_action",
		"governed_native_action",
		"forbidden_mutation",
		"not_allowed_leakage",
	}
)

VALID_STATE_KINDS = frozenset({"ready", "empty", "restricted", "unavailable", "error"})

FORBIDDEN_MUTATION_LABELS = (
	"Submit",
	"Cancel",
	"Amend",
	"Close",
	"Unclose",
	"Approve",
	"Reject",
	"Receive",
	"Bill",
	"Pay",
	"Set Default Supplier",
	"Update Item Price",
	"Delete",
)

NATIVE_EXCEPTION_POLICIES: dict[str, dict[str, str]] = {
	"sales-managed-document-forms-v1": {
		"workspace_id": "sales",
		"title": "Sales managed ERP document forms",
		"policy_doc": "_docs/erp-ui-customization/native-exception-policy-v1.md",
		"status": "approved_sales_freeze",
	},
	"procurement-native-create-forms-phase3-v1": {
		"workspace_id": "procurement",
		"title": "Procurement Phase 3 native create forms",
		"policy_doc": "_docs/erp-ui-customization/native-exception-policy-v1.md",
		"status": "approved_phase_3_exception",
	},
	"procurement-secondary-native-open-v1": {
		"workspace_id": "procurement",
		"title": "Procurement secondary native open actions",
		"policy_doc": "_docs/erp-ui-customization/native-exception-policy-v1.md",
		"status": "secondary_permission_gated_exception",
	},
}


def _route(
	workspace_id: str,
	route_key: str,
	page_kind: str,
	classification: str,
	route_pattern: str,
	expected_shell: str,
	*,
	owning_adapter: str | None = None,
	native_exception_ref: str | None = None,
	required_smoke_category: str = "contract",
	notes: str = "",
	repair_owner: str | None = None,
	repair_status: str | None = None,
) -> dict[str, Any]:
	return {
		"workspace_id": workspace_id,
		"route_key": route_key,
		"page_kind": page_kind,
		"classification": classification,
		"route_pattern": route_pattern,
		"owning_adapter": owning_adapter or workspace_id,
		"expected_shell": expected_shell,
		"native_exception_ref": native_exception_ref,
		"required_smoke_category": required_smoke_category,
		"notes": notes,
		"repair_owner": repair_owner,
		"repair_status": repair_status,
	}


def _action(
	manifest_key: str,
	workspace_id: str,
	source_route: str,
	action_key: str,
	classification: str,
	target_kind: str,
	*,
	label: str | None = None,
	label_pattern: str | None = None,
	target_route_pattern: str | None = None,
	native_exception_ref: str | None = None,
	forbidden_mutation_guard: str | None = None,
	notes: str = "",
	repair_owner: str | None = None,
	repair_status: str | None = None,
) -> dict[str, Any]:
	return {
		"manifest_key": manifest_key,
		"workspace_id": workspace_id,
		"source_route": source_route,
		"action_key": action_key,
		"label": label,
		"label_pattern": label_pattern,
		"classification": classification,
		"target_kind": target_kind,
		"target_route_pattern": target_route_pattern,
		"native_exception_ref": native_exception_ref,
		"forbidden_mutation_guard": forbidden_mutation_guard,
		"notes": notes,
		"repair_owner": repair_owner,
		"repair_status": repair_status,
	}


SALES_WORKLIST_ROUTES = (
	("quotation_directory", "Quotation Directory", "productized_worklist", "list_page_shell"),
	("quotations_waiting_action", "Quotations Waiting Action", "productized_worklist", "list_page_shell"),
	("quotations_awaiting_approval", "Quotations Awaiting Approval", "productized_worklist", "list_page_shell"),
	("expiring_quotations", "Expiring Quotations", "productized_worklist", "list_page_shell"),
	("sales_order_directory", "Sales Order Directory", "productized_worklist", "list_page_shell"),
	("open_orders", "Open Orders", "productized_worklist", "list_page_shell"),
	("sales_orders_pending_fulfillment", "Orders Pending Fulfillment", "productized_worklist", "list_page_shell"),
	("partially_delivered_orders", "Partially Delivered Orders", "productized_worklist", "list_page_shell"),
	("orders_due_soon", "Orders Due Soon", "productized_worklist", "list_page_shell"),
	("orders_blocked_by_approval", "Orders Blocked By Approval", "productized_worklist", "list_page_shell"),
	("customer_follow_up_tasks", "Customer Follow Up Tasks", "productized_worklist", "list_page_shell"),
	("invoices_outstanding", "Invoices Outstanding", "productized_worklist", "list_page_shell"),
	("sales_returns_in_progress", "Sales Returns In Progress", "productized_worklist", "list_page_shell"),
	("customer_directory", "Customer Directory", "productized_worklist", "list_page_shell"),
	("customer_detail/<customer>", "Customer Detail", "productized_detail", "list_detail_pattern"),
	("customer_editor", "Customer Create", "managed_create_edit", "form_panel_pattern"),
	("customer_editor/<customer>", "Customer Edit", "managed_create_edit", "form_panel_pattern"),
	("item_directory", "Item Directory", "productized_worklist", "list_page_shell"),
	("item_detail/<item>", "Item Detail", "productized_detail", "list_detail_pattern"),
)

SALES_REPORT_ROUTES = (
	("sales_analytics", "Sales Analytics"),
	("sales_order_analysis", "Sales Order Analysis"),
	("trend_analysis", "Trend Analysis"),
	("quotation_trends", "Quotation Trends compatibility alias"),
	("lost_quotations", "Lost Quotations"),
	("collections_status", "Collections Status"),
	("payment_terms_status_sales_order", "Payment Terms Status compatibility alias"),
	("item_wise_sales_history", "Item-wise Sales History"),
)

PROCUREMENT_WORKLIST_ROUTES = (
	("supplier_directory", "Supplier Directory"),
	("buying_item_directory", "Buying Item Directory"),
	("purchase_request_directory", "Purchase Request Directory"),
	("requests_to_source", "Requests To Source"),
	("purchase_order_directory", "Purchase Order Directory"),
	("purchase_orders_pending_approval", "Purchase Orders Pending Approval"),
	("purchase_orders_open", "Open Purchase Orders"),
	("purchase_orders_late_or_unreceived", "Late Or Unreceived Purchase Orders"),
	("purchase_orders_due_soon", "Purchase Orders Due Soon"),
	("purchase_orders_overdue", "Overdue Purchase Orders"),
	("purchase_orders_partially_received", "Partially Received Purchase Orders"),
	("purchase_orders_not_billed_visibility", "Purchase Orders Not Billed Visibility"),
	("purchase_orders_supplier_follow_up", "Purchase Orders Supplier Follow Up"),
	("rfq_directory", "RFQ Directory"),
	("rfqs_awaiting_supplier_response", "RFQs Awaiting Supplier Response"),
	("rfqs_partially_quoted", "RFQs Partially Quoted"),
	("supplier_quotation_directory", "Supplier Quotation Directory"),
	("supplier_quotations_to_compare", "Supplier Quotations To Compare"),
	("supplier_quotations_expiring", "Supplier Quotations Expiring"),
)

ROUTE_MANIFEST: tuple[dict[str, Any], ...] = (
	_route("sales", "sales-console-home", "launcher", "productized_overview", "/desk/sales-console-home", "launcher_handoff", required_smoke_category="sales_role_smoke", notes="Frozen Sales launcher route."),
	_route("sales", "sales-console", "overview", "productized_overview", "/desk/sales-console", "console_runtime", required_smoke_category="sales_role_smoke", notes="Frozen Sales overview."),
	_route("sales", "sales-console-worklist", "worklist_guard", "productized_worklist", "/desk/sales-console-worklist", "list_page_shell", required_smoke_category="sales_worklist_contract", notes="Bare route renders guarded state."),
	*(
		_route(
			"sales",
			f"sales-console-worklist/{queue_key}",
			"detail" if classification == "productized_detail" else "create_edit" if classification == "managed_create_edit" else "worklist",
			classification,
			f"/desk/sales-console-worklist/{queue_key.replace('_', '-')}",
			expected_shell,
			required_smoke_category="sales_worklist_contract",
			notes=label,
		)
		for queue_key, label, classification, expected_shell in SALES_WORKLIST_ROUTES
	),
	_route("sales", "sales-console-report", "report_guard", "productized_report", "/desk/sales-console-report", "report_page_shell", required_smoke_category="sales_report_contract", notes="Bare route renders guarded state."),
	*(
		_route(
			"sales",
			f"sales-console-report/{report_key}",
			"report",
			"productized_report",
			f"/desk/sales-console-report/{report_key.replace('_', '-')}",
			"report_page_shell",
			required_smoke_category="sales_report_contract",
			notes=label,
		)
		for report_key, label in SALES_REPORT_ROUTES
	),
	_route("sales", "Form/Quotation", "managed_document_form", "managed_create_edit", "Form/Quotation/<name-or-new>", "child_page_managed_form", native_exception_ref="sales-managed-document-forms-v1", required_smoke_category="sales_child_page_runtime", notes="Approved managed Sales document form."),
	_route("sales", "Form/Sales Order", "managed_document_form", "managed_create_edit", "Form/Sales Order/<name-or-new>", "child_page_managed_form", native_exception_ref="sales-managed-document-forms-v1", required_smoke_category="sales_child_page_runtime", notes="Approved managed Sales document form."),
	_route("sales", "Form/Delivery Note", "managed_document_form", "managed_create_edit", "Form/Delivery Note/<name-or-new>", "child_page_managed_form", native_exception_ref="sales-managed-document-forms-v1", required_smoke_category="sales_child_page_runtime", notes="Approved managed Sales document form."),
	_route("sales", "Form/Sales Invoice", "managed_document_form", "managed_create_edit", "Form/Sales Invoice/<name-or-new>", "child_page_managed_form", native_exception_ref="sales-managed-document-forms-v1", required_smoke_category="sales_child_page_runtime", notes="Approved managed Sales document form."),
	_route("procurement", "procurement-console-home", "launcher", "productized_overview", "/desk/procurement-console-home", "launcher_handoff", required_smoke_category="procurement_phase3_smoke", notes="Owner-approved Purchase role home route."),
	_route("procurement", "procurement-console", "overview", "productized_overview", "/desk/procurement-console", "console_runtime", required_smoke_category="procurement_phase3_smoke", notes="Phase 3 buyer workbench."),
	_route("procurement", "procurement-console-worklist", "worklist_guard", "productized_worklist", "/desk/procurement-console-worklist", "list_page_shell", required_smoke_category="procurement_worklist_contract", notes="Bare route renders guarded state."),
	*(
		_route(
			"procurement",
			f"procurement-console-worklist/{queue_key}",
			"worklist",
			"productized_worklist",
			f"/desk/procurement-console-worklist/{queue_key.replace('_', '-')}",
			"list_page_shell",
			required_smoke_category="procurement_phase3_smoke",
			notes=label,
		)
		for queue_key, label in PROCUREMENT_WORKLIST_ROUTES
	),
	_route("procurement", "procurement-console-report", "report_guard", "productized_report", "/desk/procurement-console-report", "report_page_shell", required_smoke_category="procurement_report_contract", notes="Bare route renders guarded state."),
	_route("procurement", "procurement-console-report/supplier_quotation_comparison", "report", "productized_report", "/desk/procurement-console-report/supplier-quotation-comparison", "report_page_shell", required_smoke_category="procurement_phase3_smoke", notes="Read-only wrapper around ERPNext Supplier Quotation Comparison."),
	_route("procurement", "procurement-console-po-follow-up", "detail", "productized_detail", "/desk/procurement-console-po-follow-up/<purchase-order>", "compact_child_detail_shell", required_smoke_category="procurement_phase3_smoke", notes="Read-only PO follow-up detail."),
	_route("procurement", "procurement-console-supplier", "detail", "productized_detail", "/desk/procurement-console-supplier/<supplier>", "compact_child_detail_shell", required_smoke_category="procurement_phase3_smoke", notes="Read-only supplier profile."),
	_route("procurement", "procurement-console-item", "detail", "productized_detail", "/desk/procurement-console-item/<item>", "compact_child_detail_shell", required_smoke_category="procurement_phase3_smoke", notes="Read-only buying item profile."),
	_route("procurement", "procurement-console-purchase-request-review", "review", "productized_detail", "/desk/procurement-console-purchase-request-review/<material-request>", "compact_review_shell", required_smoke_category="procurement_phase3_smoke", notes="Read-only Purchase Request review."),
	_route("procurement", "procurement-console-rfq-review", "review", "productized_detail", "/desk/procurement-console-rfq-review/<rfq>", "compact_review_shell", required_smoke_category="procurement_phase3_smoke", notes="Read-only RFQ review."),
	_route("procurement", "procurement-console-supplier-quotation-review", "review", "productized_detail", "/desk/procurement-console-supplier-quotation-review/<supplier-quotation>", "compact_review_shell", required_smoke_category="procurement_phase3_smoke", notes="Read-only Supplier Quotation review."),
	_route("procurement", "Form/Material Request/new-purchase", "native_create_form", "governed_native_exception", "Form/Material Request/new-*", "native_form_with_procurement_chrome", native_exception_ref="procurement-native-create-forms-phase3-v1", required_smoke_category="procurement_native_exception_smoke", notes="New Purchase Request Start Buying Work exception."),
	_route("procurement", "Form/Request for Quotation/new", "native_create_form", "governed_native_exception", "Form/Request for Quotation/new-*", "native_form_with_procurement_chrome", native_exception_ref="procurement-native-create-forms-phase3-v1", required_smoke_category="procurement_native_exception_smoke", notes="New RFQ Start Buying Work exception."),
	_route("procurement", "Form/Supplier Quotation/new", "native_create_form", "governed_native_exception", "Form/Supplier Quotation/new-*", "native_form_with_procurement_chrome", native_exception_ref="procurement-native-create-forms-phase3-v1", required_smoke_category="procurement_native_exception_smoke", notes="New Supplier Quotation Start Buying Work exception."),
	_route("procurement", "Form/Purchase Order/new", "native_create_form", "governed_native_exception", "Form/Purchase Order/new-*", "native_form_with_procurement_chrome", native_exception_ref="procurement-native-create-forms-phase3-v1", required_smoke_category="procurement_native_exception_smoke", notes="New Purchase Order Start Buying Work exception."),
	_route("procurement", "Form/Procurement secondary native open", "native_secondary_form", "governed_native_exception", "Form/<doctype>/<name>", "native_form_with_procurement_chrome", native_exception_ref="procurement-secondary-native-open-v1", required_smoke_category="procurement_native_exception_smoke", notes="Secondary permission-gated native open action from productized detail/review pages."),
)

ACTION_MANIFEST: tuple[dict[str, Any], ...] = (
	_action("sales-overview-new-quotation", "sales", "sales-console", "new_quotation", "governed_native_action", "new_doc", label="New Quotation", native_exception_ref="sales-managed-document-forms-v1", notes="Overview quick action opens the approved managed ERP Quotation create flow."),
	_action("sales-overview-new-sales-order", "sales", "sales-console", "new_sales_order", "governed_native_action", "new_doc", label="New Sales Order", native_exception_ref="sales-managed-document-forms-v1", notes="Overview quick action opens the approved managed ERP Sales Order create flow."),
	_action("sales-overview-open-customer", "sales", "sales-console", "open_customer", "productized_navigation", "worklist", label="Customers", target_route_pattern="/desk/sales-console-worklist/customer-directory"),
	_action("sales-overview-open-item", "sales", "sales-console", "open_item", "productized_navigation", "worklist", label="Items", target_route_pattern="/desk/sales-console-worklist/item-directory"),
	_action("sales-overview-queue-card-navigation", "sales", "sales-console", "queue_card_navigation", "productized_navigation", "worklist", label_pattern="queue card", target_route_pattern="/desk/sales-console-worklist/<queue>"),
	_action("sales-overview-report-shortcut-navigation", "sales", "sales-console", "report_shortcut_navigation", "productized_navigation", "report_page", label_pattern="report shortcut", target_route_pattern="/desk/sales-console-report/<report>"),
	_action("sales-worklist-refresh", "sales", "sales-console-worklist/*", "refresh", "productized_secondary_action", "current_shell", label="Refresh", notes="Shared worklist command."),
	_action("sales-worklist-reset", "sales", "sales-console-worklist/*", "reset_filters", "productized_secondary_action", "current_shell", label="Reset", notes="Shared worklist command."),
	_action("sales-worklist-apply", "sales", "sales-console-worklist/*", "apply_filters", "productized_primary_action", "current_shell", label="Apply", notes="Shared worklist command."),
	_action("sales-report-apply", "sales", "sales-console-report/*", "apply_filters", "productized_primary_action", "current_shell", label="Apply", notes="Shared report command."),
	_action("sales-report-reset", "sales", "sales-console-report/*", "reset_filters", "productized_secondary_action", "current_shell", label="Reset", notes="Shared report command."),
	_action("sales-report-refresh", "sales", "sales-console-report/*", "refresh", "productized_secondary_action", "current_shell", label="Refresh", notes="Shared report command."),
	_action("sales-report-back", "sales", "sales-console-report/*", "back_to_console", "productized_navigation", "page", label="Back to Sales Console", target_route_pattern="/desk/sales-console"),
	_action("sales-report-row-drilldown", "sales", "sales-console-report/*", "report_cell_drilldown", "productized_navigation", "declared_target", label_pattern="report cell link", notes="Report targets must follow productized route first."),
	_action("sales-document-row-open", "sales", "sales-console-worklist/quotation_directory|sales_order_directory", "row:*:open_record", "productized_navigation", "managed_form", label="Open", native_exception_ref="sales-managed-document-forms-v1", notes="Approved managed Sales document form target."),
	_action("sales-profile-row-open", "sales", "sales-console-worklist/customer_directory|item_directory", "row:*:open_record", "productized_navigation", "page", label="Open", target_route_pattern="/desk/sales-console-worklist/<detail-route>/<name>"),
	_action("sales-customer-detail-managed-document-open", "sales", "sales-console-worklist/customer_detail/<customer>", "row:*:open_record", "productized_navigation", "managed_form", label="Open", native_exception_ref="sales-managed-document-forms-v1", notes="Customer Detail recent activity rows open approved managed Sales document forms for Quotation, Sales Order, or Sales Invoice."),
	_action("sales-new-quotation", "sales", "sales-console-worklist/quotation_directory", "new_quotation", "governed_native_action", "new_doc", label="New Quotation", native_exception_ref="sales-managed-document-forms-v1", notes="ERPNext create workflow remains transaction truth."),
	_action("sales-new-sales-order", "sales", "sales-console-worklist/sales_order_directory", "new_sales_order", "governed_native_action", "new_doc", label="New Sales Order", native_exception_ref="sales-managed-document-forms-v1", notes="ERPNext create workflow remains transaction truth."),
	_action("sales-create-customer", "sales", "sales-console-worklist/customer_directory", "create_customer", "productized_primary_action", "page", label="Create Customer", target_route_pattern="/desk/sales-console-worklist/customer-editor"),
	_action("sales-edit-customer", "sales", "sales-console-worklist/customer_detail/<customer>", "edit_customer", "productized_secondary_action", "page", label="Edit Customer", target_route_pattern="/desk/sales-console-worklist/customer-editor/<customer>"),
	_action("sales-back-customers", "sales", "sales-console-worklist/customer_detail|customer_editor", "back_to_customers", "productized_navigation", "worklist", label="Back to Customers", target_route_pattern="/desk/sales-console-worklist/customer-directory"),
	_action("sales-back-items", "sales", "sales-console-worklist/item_detail/<item>", "back_to_items", "productized_navigation", "worklist", label="Back to Items", target_route_pattern="/desk/sales-console-worklist/item-directory"),
	_action("sales-managed-form-native-lifecycle", "sales", "Form/Quotation|Sales Order|Delivery Note|Sales Invoice", "native_document_lifecycle", "governed_native_action", "native_form_lifecycle", label_pattern="Save|Submit|Print|Email|Assign|Share", native_exception_ref="sales-managed-document-forms-v1"),
	_action("procurement-worklist-refresh", "procurement", "procurement-console-worklist/*", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("procurement-worklist-reset", "procurement", "procurement-console-worklist/*", "reset_filters", "productized_secondary_action", "current_shell", label="Reset"),
	_action("procurement-worklist-apply", "procurement", "procurement-console-worklist/*", "apply_filters", "productized_primary_action", "current_shell", label="Apply"),
	_action("procurement-report-refresh", "procurement", "procurement-console-report/*", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("procurement-report-reset", "procurement", "procurement-console-report/*", "reset_filters", "productized_secondary_action", "current_shell", label="Reset"),
	_action("procurement-report-apply", "procurement", "procurement-console-report/*", "apply_filters", "productized_primary_action", "current_shell", label="Apply"),
	_action("procurement-overview-navigation", "procurement", "procurement-console", "overview_card_navigation", "productized_navigation", "page_or_worklist_or_report", label_pattern="overview card", target_route_pattern="/desk/procurement-console*"),
	_action("procurement-sidebar-navigation", "procurement", "procurement-sidebar", "sidebar_navigation", "productized_navigation", "page_or_worklist_or_report", label_pattern="sidebar item", target_route_pattern="/desk/procurement-console*"),
	_action("procurement-worklist-row-open", "procurement", "procurement-console-worklist/*", "row:*:open_record", "productized_navigation", "page", label_pattern="Open|Review Request|Review RFQ|Review Quote", target_route_pattern="/desk/procurement-console-*", notes="Productized worklists must not use native form as primary row action."),
	_action("procurement-back-worklist", "procurement", "procurement-console-*-review/<name>", "back_to_worklist", "productized_navigation", "worklist", label_pattern="Back to *"),
	_action("procurement-back-queue", "procurement", "procurement-console-po-follow-up/<purchase-order>", "back_to_queue", "productized_navigation", "worklist", label="Back to queue"),
	_action("procurement-back-suppliers", "procurement", "procurement-console-supplier/<supplier>", "back_to_suppliers", "productized_navigation", "worklist", label="Back to suppliers"),
	_action("procurement-back-items", "procurement", "procurement-console-item/<item>", "back_to_items", "productized_navigation", "worklist", label="Back to items"),
	_action("procurement-detail-refresh", "procurement", "procurement-console-po-follow-up|supplier|item|*-review", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("procurement-open-quote-comparison", "procurement", "procurement-console-supplier-quotation-review/<supplier-quotation>", "open_quote_comparison", "productized_navigation", "report_page", label="Compare offers", target_route_pattern="/desk/procurement-console-report/supplier-quotation-comparison"),
	_action("procurement-new-purchase-request", "procurement", "procurement-console", "new_purchase_request", "governed_native_action", "new_doc", label="New Purchase Request", native_exception_ref="procurement-native-create-forms-phase3-v1"),
	_action("procurement-new-rfq", "procurement", "procurement-console", "new_rfq", "governed_native_action", "new_doc", label="New RFQ", native_exception_ref="procurement-native-create-forms-phase3-v1"),
	_action("procurement-new-supplier-quotation", "procurement", "procurement-console", "new_supplier_quotation", "governed_native_action", "new_doc", label="New Supplier Quotation", native_exception_ref="procurement-native-create-forms-phase3-v1"),
	_action("procurement-new-purchase-order", "procurement", "procurement-console", "new_purchase_order", "governed_native_action", "new_doc", label="New Purchase Order", native_exception_ref="procurement-native-create-forms-phase3-v1"),
	_action("procurement-open-erp-form", "procurement", "procurement-console-purchase-request-review|rfq-review|supplier-quotation-review", "open_erp_form", "governed_native_action", "form", label="Open ERP Form", native_exception_ref="procurement-secondary-native-open-v1", notes="Secondary action only."),
	_action("procurement-open-supplier-form", "procurement", "procurement-console-supplier/<supplier>", "open_supplier_form", "governed_native_action", "form", label="ERP Supplier Form", native_exception_ref="procurement-secondary-native-open-v1", notes="Secondary manager/write-permission action only."),
	_action("procurement-open-item-form", "procurement", "procurement-console-item/<item>", "open_item_form", "governed_native_action", "form", label="ERP Item Form", native_exception_ref="procurement-secondary-native-open-v1", notes="Secondary governance action only."),
	_action("procurement-native-form-lifecycle", "procurement", "Form/Material Request|Request for Quotation|Supplier Quotation|Purchase Order", "native_form_lifecycle", "governed_native_action", "native_form_lifecycle", label_pattern="Get Items From|Tools|Save|Add row|Add multiple|workflow controls", native_exception_ref="procurement-native-create-forms-phase3-v1"),
)

FORBIDDEN_MUTATION_GUARDS: tuple[dict[str, Any], ...] = (
	{
		"workspace_id": "sales",
		"scope": "productized_overview_worklist_report_detail_pages",
		"labels": FORBIDDEN_MUTATION_LABELS,
		"allowed_only_when": "declared managed native form or future managed mutation page",
		"policy_doc": "_docs/erp-ui-customization/native-exception-policy-v1.md",
	},
	{
		"workspace_id": "procurement",
		"scope": "productized_overview_worklist_report_detail_review_pages",
		"labels": FORBIDDEN_MUTATION_LABELS,
		"allowed_only_when": "declared governed native exception or future managed mutation page",
		"policy_doc": "_docs/erp-ui-customization/native-exception-policy-v1.md",
	},
)


def get_route_manifest() -> list[dict[str, Any]]:
	return [deepcopy(item) for item in ROUTE_MANIFEST]


def get_action_manifest() -> list[dict[str, Any]]:
	return [deepcopy(item) for item in ACTION_MANIFEST]


def route_keys_by_workspace(workspace_id: str) -> set[str]:
	return {str(item.get("route_key")) for item in ROUTE_MANIFEST if item.get("workspace_id") == workspace_id}


def action_keys_by_workspace(workspace_id: str) -> set[str]:
	return {str(item.get("manifest_key")) for item in ACTION_MANIFEST if item.get("workspace_id") == workspace_id}


def validate_manifest() -> list[str]:
	errors: list[str] = []
	seen_routes: set[tuple[str, str]] = set()
	seen_actions: set[str] = set()
	for route in ROUTE_MANIFEST:
		workspace_id = str(route.get("workspace_id") or "")
		route_key = str(route.get("route_key") or "")
		identity = (workspace_id, route_key)
		if not workspace_id or not route_key:
			errors.append(f"Route missing workspace or key: {route!r}")
		if identity in seen_routes:
			errors.append(f"Duplicate route manifest entry: {workspace_id}:{route_key}")
		seen_routes.add(identity)
		classification = route.get("classification")
		if classification not in VALID_ROUTE_CLASSIFICATIONS:
			errors.append(f"Invalid route classification for {workspace_id}:{route_key}: {classification}")
		if not route.get("route_pattern"):
			errors.append(f"Route missing route pattern: {workspace_id}:{route_key}")
		if not route.get("owning_adapter"):
			errors.append(f"Route missing owning adapter: {workspace_id}:{route_key}")
		if not route.get("expected_shell"):
			errors.append(f"Route missing expected shell: {workspace_id}:{route_key}")
		if classification == "governed_native_exception" and route.get("native_exception_ref") not in NATIVE_EXCEPTION_POLICIES:
			errors.append(f"Governed native route missing valid policy reference: {workspace_id}:{route_key}")
		if classification == "not_allowed_leakage" and not (route.get("repair_owner") and route.get("repair_status")):
			errors.append(f"Leakage route missing repair owner/status: {workspace_id}:{route_key}")

	for action in ACTION_MANIFEST:
		manifest_key = str(action.get("manifest_key") or "")
		workspace_id = str(action.get("workspace_id") or "")
		if not manifest_key or not workspace_id:
			errors.append(f"Action missing manifest key or workspace: {action!r}")
		if manifest_key in seen_actions:
			errors.append(f"Duplicate action manifest entry: {manifest_key}")
		seen_actions.add(manifest_key)
		classification = action.get("classification")
		if classification not in VALID_ACTION_CLASSIFICATIONS:
			errors.append(f"Invalid action classification for {manifest_key}: {classification}")
		if not action.get("source_route"):
			errors.append(f"Action missing source route: {manifest_key}")
		if not action.get("action_key"):
			errors.append(f"Action missing action key: {manifest_key}")
		if not action.get("target_kind"):
			errors.append(f"Action missing target kind: {manifest_key}")
		if not (action.get("label") or action.get("label_pattern")):
			errors.append(f"Action missing label or label pattern: {manifest_key}")
		if classification == "governed_native_action" and action.get("native_exception_ref") not in NATIVE_EXCEPTION_POLICIES:
			errors.append(f"Governed native action missing valid policy reference: {manifest_key}")
		if classification == "not_allowed_leakage" and not (action.get("repair_owner") and action.get("repair_status")):
			errors.append(f"Leakage action missing repair owner/status: {manifest_key}")
		if classification == "forbidden_mutation" and not action.get("forbidden_mutation_guard"):
			errors.append(f"Forbidden mutation action missing guard: {manifest_key}")

	for guard in FORBIDDEN_MUTATION_GUARDS:
		labels = tuple(guard.get("labels") or ())
		if not labels:
			errors.append(f"Forbidden mutation guard missing labels: {guard!r}")
		missing = sorted(set(FORBIDDEN_MUTATION_LABELS) - set(labels))
		if missing:
			errors.append(f"Forbidden mutation guard missing labels {missing}: {guard.get('workspace_id')}")
	return errors
