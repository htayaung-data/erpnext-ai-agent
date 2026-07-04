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
	"Ship",
	"Dispatch",
	"Post",
	"Reconcile",
	"Reserve",
	"Unreserve",
	"Bill",
	"Pay",
	"Set Default Supplier",
	"Update Item Price",
	"Stock Entry",
	"Purchase Receipt",
	"Delivery Note",
	"Stock Reconciliation",
	"Assign Serial",
	"Assign Batch",
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
	_route("procurement", "procurement-console-report", "report_index", "productized_report", "/desk/procurement-console-report", "report_page_shell", required_smoke_category="procurement_phase4_smoke", notes="Procurement Reports Index catalog."),
	_route("procurement", "procurement-console-report/supplier_quotation_comparison", "report", "productized_report", "/desk/procurement-console-report/supplier-quotation-comparison", "report_page_shell", required_smoke_category="procurement_phase3_smoke", notes="Read-only wrapper around ERPNext Supplier Quotation Comparison."),
	_route("procurement", "procurement-console-report/purchase_order_analysis", "report", "productized_report", "/desk/procurement-console-report/purchase-order-analysis", "report_page_shell", required_smoke_category="procurement_phase4_smoke", notes="Read-only wrapper around ERPNext Purchase Order Analysis with productized drilldowns."),
	_route("procurement", "procurement-console-report/demand_to_order_coverage", "report", "productized_report", "/desk/procurement-console-report/demand-to-order-coverage", "report_page_shell", required_smoke_category="procurement_phase4_smoke", notes="Read-only demand-to-order coverage report with productized drilldowns."),
	_route("procurement", "procurement-console-report/item_purchase_history", "report", "productized_report", "/desk/procurement-console-report/item-purchase-history", "report_page_shell", required_smoke_category="procurement_phase4_smoke", notes="Read-only item purchase history and price review report with productized drilldowns."),
	_route("procurement", "procurement-console-po-follow-up", "detail", "productized_detail", "/desk/procurement-console-po-follow-up/<purchase-order>", "compact_child_detail_shell", required_smoke_category="procurement_phase3_smoke", notes="Read-only PO follow-up detail."),
	_route("procurement", "procurement-console-supplier", "detail", "productized_detail", "/desk/procurement-console-supplier/<supplier>", "compact_child_detail_shell", required_smoke_category="procurement_phase3_smoke", notes="Productized Supplier Detail with Phase 7E1A manager-only readiness profile. No native Supplier form escape."),
	_route("procurement", "procurement-console-item", "detail", "productized_detail", "/desk/procurement-console-item/<item>", "compact_child_detail_shell", required_smoke_category="procurement_phase3_smoke", notes="Productized Buying Item Detail with Phase 7E2A manager-only buying context profile. No native Item form escape."),
	_route("procurement", "procurement-console-purchase-request-review", "review", "productized_detail", "/desk/procurement-console-purchase-request-review/<material-request>", "compact_review_shell", required_smoke_category="procurement_phase3_smoke", notes="Read-only Purchase Request review."),
	_route("procurement", "procurement-console-purchase-request-form", "managed_purchase_request_form", "managed_create_edit", "/desk/procurement-console-purchase-request-form/<name-or-new>", "managed_draft_form_shell", required_smoke_category="procurement_phase5a_smoke", notes="Managed Purchase Request draft form. Save Draft only; Purchase Material Request only."),
	_route("procurement", "procurement-console-rfq-form", "managed_rfq_form", "managed_create_edit", "/desk/procurement-console-rfq-form/<name-or-new>", "managed_draft_form_shell", required_smoke_category="procurement_phase5b_smoke", notes="Managed RFQ draft form with Phase 6C1 supplier-specific preview/PDF output; no email send."),
	_route("procurement", "procurement-console-rfq-review", "review", "productized_detail", "/desk/procurement-console-rfq-review/<rfq>", "compact_review_shell", required_smoke_category="procurement_phase3_smoke", notes="Read-only RFQ review."),
	_route("procurement", "procurement-console-supplier-quotation-form", "managed_supplier_quotation_form", "managed_create_edit", "/desk/procurement-console-supplier-quotation-form/<name-or-new>", "managed_draft_form_shell", required_smoke_category="procurement_phase5c_smoke", notes="Managed Supplier Quotation draft form. Save Quotation only; no submit or Purchase Order creation."),
	_route("procurement", "procurement-console-purchase-order-form", "managed_purchase_order_form", "managed_create_edit", "/desk/procurement-console-purchase-order-form/<name-or-new>", "managed_draft_form_shell", required_smoke_category="procurement_phase5d_smoke", notes="Managed Purchase Order draft form. Save Purchase Order only; no submit, receipt, invoice, or payment actions."),
	_route("procurement", "procurement-console-supplier-quotation-review", "review", "productized_detail", "/desk/procurement-console-supplier-quotation-review/<supplier-quotation>", "compact_review_shell", required_smoke_category="procurement_phase3_smoke", notes="Read-only Supplier Quotation review."),
	_route("warehouse", "warehouse-console", "overview", "productized_overview", "/desk/warehouse-console", "console_runtime", required_smoke_category="warehouse_phase_w5a_smoke", notes="W5A read-only Warehouse Overview with inbound and outbound visibility."),
	_route("warehouse", "warehouse-console-worklist", "worklist_guard", "productized_worklist", "/desk/warehouse-console-worklist", "warehouse_worklist_shell", required_smoke_category="warehouse_phase_w5a_smoke", notes="Warehouse worklist route for read-only inbound and outbound visibility."),
	_route("warehouse", "warehouse-console-worklist/inbound_receiving", "worklist", "productized_worklist", "/desk/warehouse-console-worklist/inbound-receiving", "warehouse_inbound_shell", required_smoke_category="warehouse_phase_w4a_smoke", notes="Read-only inbound supplier receiving queue."),
	_route("warehouse", "warehouse-console-worklist/outbound_picking", "worklist", "productized_worklist", "/desk/warehouse-console-worklist/outbound-picking", "warehouse_outbound_shell", required_smoke_category="warehouse_phase_w5a_smoke", notes="Read-only outbound picking visibility queue."),
	_route("warehouse", "warehouse-console-worklist/stock_exceptions", "worklist", "productized_worklist", "/desk/warehouse-console-worklist/stock-exceptions", "warehouse_stock_exception_shell", required_smoke_category="warehouse_phase_w6a_smoke", notes="Read-only stock exception visibility for outbound blockers and inbound cover."),
	_route("warehouse", "warehouse-console-worklist/returns_work_hub", "worklist", "productized_worklist", "/desk/warehouse-console-worklist/returns-work-hub", "warehouse_custom_workflow_shell", required_smoke_category="warehouse_phase_w9a_smoke", notes="Custom Returns workflow hub for request-only customer and supplier return posture records."),
	_route("warehouse", "warehouse-console-worklist/internal_transfer_workflow", "worklist", "productized_worklist", "/desk/warehouse-console-worklist/internal-transfer-workflow", "warehouse_custom_workflow_shell", required_smoke_category="warehouse_phase_w9a_smoke", notes="Custom Internal Transfer workflow for transfer intent and manager posture records; no stock movement."),
	_route("warehouse", "warehouse-console-worklist/cycle_count_workflow", "worklist", "productized_worklist", "/desk/warehouse-console-worklist/cycle-count-workflow", "warehouse_custom_workflow_shell", required_smoke_category="warehouse_phase_w9a_smoke", notes="Custom Cycle Count workflow for count evidence and variance posture records; no stock reconciliation."),
	_route("warehouse", "warehouse-console-worklist/movement_visibility", "worklist", "productized_worklist", "/desk/warehouse-console-worklist/movement-visibility", "warehouse_movement_shell", required_smoke_category="warehouse_phase_w8a_smoke", notes="Read-only movement visibility for recent recorded stock movements."),
	_route("warehouse", "warehouse-console-worklist/transfer_visibility", "worklist", "productized_worklist", "/desk/warehouse-console-worklist/transfer-visibility", "warehouse_transfer_shell", required_smoke_category="warehouse_phase_w8c_smoke", notes="Read-only transfer visibility for posted warehouse-to-warehouse movement posture."),
	_route("warehouse", "warehouse-console-receiving", "detail", "productized_detail", "/desk/warehouse-console-receiving/<purchase-order>", "warehouse_receiving_shell", required_smoke_category="warehouse_phase_w4b_smoke", notes="Read-only receiving review for inbound purchase orders."),
	_route("warehouse", "warehouse-console-picking", "detail", "productized_detail", "/desk/warehouse-console-picking/<sales-order>", "warehouse_picking_shell", required_smoke_category="warehouse_phase_w5b_smoke", notes="Read-only picking review for outbound sales orders."),
	_route("warehouse", "warehouse-console-stock-exception", "detail", "productized_detail", "/desk/warehouse-console-stock-exception/<encoded-context>", "warehouse_stock_exception_review_shell", required_smoke_category="warehouse_phase_w6b_smoke", notes="Read-only stock exception review with custom Warehouse drilldowns only."),
	_route("warehouse", "warehouse-console-stock-posture", "detail", "productized_detail", "/desk/warehouse-console-stock-posture/<encoded-context>", "warehouse_stock_posture_shell", required_smoke_category="warehouse_phase_w7a_smoke", notes="Read-only item and warehouse stock posture review with custom Warehouse drilldowns only."),
	_route("warehouse", "warehouse-console-movement", "detail", "productized_detail", "/desk/warehouse-console-movement/<encoded-context>", "warehouse_movement_review_shell", required_smoke_category="warehouse_phase_w8b_smoke", notes="Read-only movement review with custom Warehouse drilldowns only."),
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
	_action("procurement-report-index-card-navigation", "procurement", "procurement-console-report", "report_card_navigation", "productized_navigation", "report_page", label_pattern="report card", target_route_pattern="/desk/procurement-console-report/<report>"),
	_action("procurement-report-planned-card", "procurement", "procurement-console-report", "planned_report_card", "productized_secondary_action", "disabled", label_pattern="Planned", notes="Planned Phase 4A report cards are disabled until their report payloads are implemented."),
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
	_action("procurement-supplier-readiness-view", "procurement", "procurement-console-supplier/<supplier>", "view_supplier_readiness", "productized_secondary_action", "current_shell", label="Supplier Buying Profile", notes="Phase 7E1A companion readiness profile. Read-only for Purchase User; manager-only edits."),
	_action("procurement-supplier-readiness-save", "procurement", "procurement-console-supplier/<supplier>", "save_supplier_readiness", "productized_secondary_action", "current_shell", label="Save Readiness", notes="Phase 7E1A allowlisted readiness profile save. Writes only Procurement Supplier Readiness Profile and immutable readiness log; no Supplier, Contact, User, email, or native ERP mutation."),
	_action("procurement-item-buying-profile-view", "procurement", "procurement-console-item/<item>", "view_item_buying_profile", "productized_secondary_action", "current_shell", label="Buying Procurement Context", notes="Phase 7E2A companion item buying profile. Read-only for Purchase User; manager-only edits. No native Item form escape."),
	_action("procurement-item-buying-profile-save", "procurement", "procurement-console-item/<item>", "save_item_buying_profile", "productized_secondary_action", "current_shell", label="Save Context", notes="Phase 7E2A allowlisted item buying profile save. Writes only Procurement Item Buying Profile and immutable item buying log; no Item, Item Supplier, Item Price, Default Supplier, Supplier, Contact, User, email, or lifecycle mutation."),
	_action("procurement-manager-readiness-view", "procurement", "procurement-console", "view_manager_readiness", "productized_secondary_action", "current_shell", label="Manager Readiness", notes="Phase 7E3A read-only manager readiness queue. Purchase Manager only; no lifecycle, email, native route, or master-data mutation."),
	_action("procurement-page-readiness-view", "procurement", "procurement-console-supplier|item|po-follow-up|*-review|*-form", "view_page_readiness", "productized_secondary_action", "current_shell", label="Readiness Review", notes="Phase 7E3A read-only page-level readiness card with productized navigation only."),
	_action("procurement-readiness-productized-fix-link", "procurement", "procurement-console-*", "readiness_fix_link", "productized_navigation", "page", label_pattern="Review supplier|Review item context|Open RFQ|Open quotation|Open purchase order", target_route_pattern="/desk/procurement-console-*", notes="Phase 7E3A readiness fix links must stay inside productized Procurement Console routes."),
	_action("procurement-report-index-open-quote-comparison", "procurement", "procurement-console-report", "open_supplier_quotation_comparison", "productized_navigation", "report_page", label="Quote Comparison", target_route_pattern="/desk/procurement-console-report/supplier-quotation-comparison", notes="Ready Reports Index card opens the productized Quote Comparison wrapper."),
	_action("procurement-report-index-open-purchase-order-analysis", "procurement", "procurement-console-report", "open_purchase_order_analysis", "productized_navigation", "report_page", label="Purchase Order Analysis", target_route_pattern="/desk/procurement-console-report/purchase-order-analysis", notes="Ready Reports Index card opens the productized Purchase Order Analysis wrapper."),
	_action("procurement-report-index-open-demand-coverage", "procurement", "procurement-console-report", "open_demand_to_order_coverage", "productized_navigation", "report_page", label="Demand-to-Order Coverage", target_route_pattern="/desk/procurement-console-report/demand-to-order-coverage", notes="Ready Reports Index card opens the productized Demand-to-Order Coverage report."),
	_action("procurement-report-index-open-item-purchase-history", "procurement", "procurement-console-report", "open_item_purchase_history", "productized_navigation", "report_page", label="Item Purchase History", target_route_pattern="/desk/procurement-console-report/item-purchase-history", notes="Ready Reports Index card opens the productized Item Purchase History report."),
	_action("procurement-report-purchase-order-analysis-drilldown", "procurement", "procurement-console-report/purchase_order_analysis", "po_analysis:*", "productized_navigation", "page", label_pattern="report cell link", target_route_pattern="/desk/procurement-console-*", notes="Purchase Order Analysis cells drill down to productized Procurement PO, Supplier, and Item pages."),
	_action("procurement-report-demand-coverage-drilldown", "procurement", "procurement-console-report/demand_to_order_coverage", "demand_coverage:*", "productized_navigation", "page", label_pattern="report cell link", target_route_pattern="/desk/procurement-console-*", notes="Demand-to-Order Coverage cells drill down to productized Purchase Request, PO, and Item pages."),
	_action("procurement-report-item-purchase-history-drilldown", "procurement", "procurement-console-report/item_purchase_history", "item_history:*", "productized_navigation", "page", label_pattern="report cell link", target_route_pattern="/desk/procurement-console-*", notes="Item Purchase History cells drill down to productized Procurement Item, Supplier, and PO pages."),
	_action("procurement-open-quote-comparison", "procurement", "procurement-console-supplier-quotation-review/<supplier-quotation>", "open_quote_comparison", "productized_navigation", "report_page", label="Compare offers", target_route_pattern="/desk/procurement-console-report/supplier-quotation-comparison"),
	_action("procurement-new-purchase-request", "procurement", "procurement-console", "new_purchase_request", "productized_navigation", "page", label="New Purchase Request", target_route_pattern="/desk/procurement-console-purchase-request-form/new", notes="Phase 5A managed Purchase Request draft form replaces native create as the primary Overview action."),
	_action("procurement-worklist-new-purchase-request", "procurement", "procurement-console-worklist/purchase_request_directory", "new_purchase_request", "productized_navigation", "page", label="New Purchase Request", target_route_pattern="/desk/procurement-console-purchase-request-form/new", notes="Contextual Purchase Requests directory create action uses the same managed form route as Overview."),
	_action("procurement-managed-pr-save-draft", "procurement", "procurement-console-purchase-request-form/<material-request-or-new>", "save_draft", "productized_primary_action", "current_shell", label="Save Draft", notes="Draft-only managed Purchase Request save using ERPNext Material Request validation."),
	_action("procurement-managed-pr-reset", "procurement", "procurement-console-purchase-request-form/<material-request-or-new>", "reset_unsaved", "productized_secondary_action", "current_shell", label="Reset unsaved changes"),
	_action("procurement-managed-pr-back", "procurement", "procurement-console-purchase-request-form/<material-request-or-new>", "back_to_purchase_requests", "productized_navigation", "worklist", label="Back to Purchase Requests", target_route_pattern="/desk/procurement-console-worklist/purchase-request-directory"),
	_action("procurement-managed-pr-review", "procurement", "procurement-console-purchase-request-form/<material-request>", "review_request", "productized_navigation", "page", label="Review Request", target_route_pattern="/desk/procurement-console-purchase-request-review/<material-request>"),
	_action("procurement-new-rfq", "procurement", "procurement-console", "new_rfq", "productized_navigation", "page", label="New RFQ", target_route_pattern="/desk/procurement-console-rfq-form/new", notes="Phase 5B managed RFQ draft form replaces native create as the primary Overview action."),
	_action("procurement-worklist-new-rfq", "procurement", "procurement-console-worklist/rfq_directory", "new_rfq", "productized_navigation", "page", label="New RFQ", target_route_pattern="/desk/procurement-console-rfq-form/new", notes="Contextual RFQ directory create action uses the same managed form route as Overview."),
	_action("procurement-managed-rfq-save-draft", "procurement", "procurement-console-rfq-form/<rfq-or-new>", "save_rfq", "productized_primary_action", "current_shell", label="Save RFQ", notes="Draft-only managed RFQ save using ERPNext validation."),
	_action("procurement-managed-rfq-reset", "procurement", "procurement-console-rfq-form/<rfq-or-new>", "reset_unsaved", "productized_secondary_action", "current_shell", label="Reset unsaved changes"),
	_action("procurement-managed-rfq-back", "procurement", "procurement-console-rfq-form/<rfq-or-new>", "back_to_rfqs", "productized_navigation", "worklist", label="Back to RFQs", target_route_pattern="/desk/procurement-console-worklist/rfq-directory"),
	_action("procurement-managed-rfq-review", "procurement", "procurement-console-rfq-form/<rfq>", "review_rfq", "productized_navigation", "page", label="Review RFQ", target_route_pattern="/desk/procurement-console-rfq-review/<rfq>"),
	_action("procurement-managed-rfq-preview-output", "procurement", "procurement-console-rfq-form/<rfq>", "preview_rfq_output", "productized_secondary_action", "current_shell", label="Preview RFQ", notes="Phase 6C1 productized supplier-specific RFQ preview. No native print UI."),
	_action("procurement-managed-rfq-download-pdf", "procurement", "procurement-console-rfq-form/<rfq>", "download_rfq_pdf", "productized_secondary_action", "controlled_pdf_endpoint", label="Download RFQ PDF", notes="Phase 6C1 supplier-specific RFQ PDF wrapper. Filename must include supplier and DRAFT-NOT-SENT."),
	_action("procurement-managed-rfq-recipient-readiness", "procurement", "procurement-console-rfq-form/<rfq>", "view_recipient_readiness", "productized_secondary_action", "current_shell", label="Recipient readiness", notes="Phase 6C2A productized RFQ supplier recipient and outgoing-email readiness panel. Read-only; no email send."),
	_action("procurement-managed-rfq-email-blocked", "procurement", "procurement-console-rfq-form/<rfq>", "send_rfq", "productized_secondary_action", "disabled", label="Send RFQ", notes="Phase 6C2A blocked action; governed RFQ send remains deferred and non-actionable."),
	_action("procurement-rfq-review-preview-output", "procurement", "procurement-console-rfq-review/<rfq>", "preview_rfq_output", "productized_secondary_action", "current_shell", label="Preview RFQ", notes="Phase 6C2A exposes the same productized supplier-specific RFQ preview on the read-only RFQ Review route. No native print UI."),
	_action("procurement-rfq-review-download-pdf", "procurement", "procurement-console-rfq-review/<rfq>", "download_rfq_pdf", "productized_secondary_action", "controlled_pdf_endpoint", label="Download RFQ PDF", notes="Phase 6C2A exposes the controlled supplier-specific RFQ PDF endpoint from RFQ Review."),
	_action("procurement-rfq-review-recipient-readiness", "procurement", "procurement-console-rfq-review/<rfq>", "view_recipient_readiness", "productized_secondary_action", "current_shell", label="Recipient readiness", notes="Phase 6C2A read-only supplier recipient and outgoing-email readiness on RFQ Review. Read-only; no email send."),
	_action("procurement-rfq-review-email-blocked", "procurement", "procurement-console-rfq-review/<rfq>", "send_rfq", "productized_secondary_action", "disabled", label="Send RFQ", notes="Phase 6C2A blocked action on RFQ Review; governed RFQ send remains deferred and non-actionable."),
	_action("procurement-new-supplier-quotation", "procurement", "procurement-console", "new_supplier_quotation", "productized_navigation", "page", label="New Supplier Quotation", target_route_pattern="/desk/procurement-console-supplier-quotation-form/new", notes="Phase 5C managed Supplier Quotation draft form replaces native create as the primary Overview action."),
	_action("procurement-worklist-new-supplier-quotation", "procurement", "procurement-console-worklist/supplier_quotation_directory", "new_supplier_quotation", "productized_navigation", "page", label="New Supplier Quotation", target_route_pattern="/desk/procurement-console-supplier-quotation-form/new", notes="Contextual Supplier Quotations directory create action uses the same managed form route as Overview."),
	_action("procurement-managed-sq-save-draft", "procurement", "procurement-console-supplier-quotation-form/<supplier-quotation-or-new>", "save_supplier_quotation", "productized_primary_action", "current_shell", label="Save Quotation", notes="Draft-only managed Supplier Quotation save using ERPNext validation."),
	_action("procurement-managed-sq-reset", "procurement", "procurement-console-supplier-quotation-form/<supplier-quotation-or-new>", "reset_unsaved", "productized_secondary_action", "current_shell", label="Reset unsaved changes"),
	_action("procurement-managed-sq-back", "procurement", "procurement-console-supplier-quotation-form/<supplier-quotation-or-new>", "back_to_supplier_quotations", "productized_navigation", "worklist", label="Back to Supplier Quotations", target_route_pattern="/desk/procurement-console-worklist/supplier-quotation-directory"),
	_action("procurement-managed-sq-review", "procurement", "procurement-console-supplier-quotation-form/<supplier-quotation>", "review_quotation", "productized_navigation", "page", label="Review Quotation", target_route_pattern="/desk/procurement-console-supplier-quotation-review/<supplier-quotation>"),
	_action("procurement-new-purchase-order", "procurement", "procurement-console", "new_purchase_order", "productized_navigation", "page", label="New Purchase Order", target_route_pattern="/desk/procurement-console-purchase-order-form/new", notes="Phase 5D managed Purchase Order draft form replaces native create as the primary Overview action."),
	_action("procurement-worklist-new-purchase-order", "procurement", "procurement-console-worklist/purchase_order_directory", "new_purchase_order", "productized_navigation", "page", label="New Purchase Order", target_route_pattern="/desk/procurement-console-purchase-order-form/new", notes="Contextual Purchase Orders directory create action uses the same managed form route as Overview."),
	_action("procurement-managed-po-save-draft", "procurement", "procurement-console-purchase-order-form/<purchase-order-or-new>", "save_purchase_order", "productized_primary_action", "current_shell", label="Save Purchase Order", notes="Draft-only managed Purchase Order save using ERPNext validation."),
	_action("procurement-managed-po-reset", "procurement", "procurement-console-purchase-order-form/<purchase-order-or-new>", "reset_unsaved", "productized_secondary_action", "current_shell", label="Reset unsaved changes"),
	_action("procurement-managed-po-back", "procurement", "procurement-console-purchase-order-form/<purchase-order-or-new>", "back_to_purchase_orders", "productized_navigation", "worklist", label="Back to Purchase Orders", target_route_pattern="/desk/procurement-console-worklist/purchase-order-directory"),
	_action("procurement-managed-po-review", "procurement", "procurement-console-purchase-order-form/<purchase-order>", "review_purchase_order", "productized_navigation", "page", label="Review Purchase Order", target_route_pattern="/desk/procurement-console-po-follow-up/<purchase-order>"),
	_action("procurement-managed-po-preview-output", "procurement", "procurement-console-purchase-order-form/<purchase-order>", "preview_purchase_order_output", "productized_secondary_action", "current_shell", label="Preview Purchase Order", notes="Phase 6C1 productized draft PO preview. No native print UI."),
	_action("procurement-managed-po-download-pdf", "procurement", "procurement-console-purchase-order-form/<purchase-order>", "download_purchase_order_pdf", "productized_secondary_action", "controlled_pdf_endpoint", label="Download PO PDF", notes="Phase 6C1 internal draft PO PDF wrapper. Filename must include DRAFT-NOT-FOR-SUPPLIER."),
	_action("procurement-managed-po-email-blocked", "procurement", "procurement-console-purchase-order-form/<purchase-order>", "email_supplier", "productized_secondary_action", "disabled", label="Email supplier", notes="Phase 6C1 blocked action; PO supplier send requires approval/submit governance."),
	_action("warehouse-overview-refresh", "warehouse", "warehouse-console", "refresh", "productized_secondary_action", "current_shell", label="Refresh", notes="Read-only Overview reload."),
	_action("warehouse-overview-open-inbound", "warehouse", "warehouse-console", "open_inbound_receiving", "productized_navigation", "worklist", label="Open inbound receiving", target_route_pattern="/desk/warehouse-console-worklist/inbound-receiving", notes="Overview navigation into the read-only inbound queue."),
	_action("warehouse-overview-open-outbound", "warehouse", "warehouse-console", "open_outbound_picking", "productized_navigation", "worklist", label="Open outbound picking", target_route_pattern="/desk/warehouse-console-worklist/outbound-picking", notes="Overview navigation into the read-only outbound queue."),
	_action("warehouse-overview-open-transfer", "warehouse", "warehouse-console", "open_transfer_visibility", "productized_navigation", "worklist", label="Open transfer visibility", target_route_pattern="/desk/warehouse-console-worklist/transfer-visibility", notes="Cockpit navigation into the read-only transfer visibility board."),
	_action("warehouse-inbound-refresh", "warehouse", "warehouse-console-worklist/inbound_receiving", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("warehouse-inbound-reset", "warehouse", "warehouse-console-worklist/inbound_receiving", "reset_filters", "productized_secondary_action", "current_shell", label="Reset"),
	_action("warehouse-inbound-apply", "warehouse", "warehouse-console-worklist/inbound_receiving", "apply_filters", "productized_primary_action", "current_shell", label="Apply"),
	_action("warehouse-inbound-view-lines", "warehouse", "warehouse-console-worklist/inbound_receiving", "view_lines", "productized_secondary_action", "current_shell", label="View lines"),
	_action("warehouse-inbound-open-receiving-review", "warehouse", "warehouse-console-worklist/inbound_receiving", "open_receiving_review", "productized_navigation", "page", label="View details", target_route_pattern="/desk/warehouse-console-receiving/<purchase-order>", notes="Read-only Warehouse receiving review drilldown."),
	_action("warehouse-outbound-refresh", "warehouse", "warehouse-console-worklist/outbound_picking", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("warehouse-outbound-reset", "warehouse", "warehouse-console-worklist/outbound_picking", "reset_filters", "productized_secondary_action", "current_shell", label="Reset"),
	_action("warehouse-outbound-apply", "warehouse", "warehouse-console-worklist/outbound_picking", "apply_filters", "productized_primary_action", "current_shell", label="Apply"),
	_action("warehouse-outbound-view-lines", "warehouse", "warehouse-console-worklist/outbound_picking", "view_lines", "productized_secondary_action", "current_shell", label="View lines"),
	_action("warehouse-outbound-open-picking-review", "warehouse", "warehouse-console-worklist/outbound_picking", "open_picking_review", "productized_navigation", "page", label="View details", target_route_pattern="/desk/warehouse-console-picking/<sales-order>", notes="Read-only Warehouse picking review drilldown."),
	_action("warehouse-stock-exceptions-refresh", "warehouse", "warehouse-console-worklist/stock_exceptions", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("warehouse-stock-exceptions-reset", "warehouse", "warehouse-console-worklist/stock_exceptions", "reset_filters", "productized_secondary_action", "current_shell", label="Reset"),
	_action("warehouse-stock-exceptions-apply", "warehouse", "warehouse-console-worklist/stock_exceptions", "apply_filters", "productized_primary_action", "current_shell", label="Apply"),
	_action("warehouse-stock-exceptions-open-exception-review", "warehouse", "warehouse-console-worklist/stock_exceptions", "open_stock_exception_review", "productized_navigation", "page", label="Review exception", target_route_pattern="/desk/warehouse-console-stock-exception/<encoded-context>", notes="Read-only custom Warehouse stock exception review drilldown."),
	_action("warehouse-stock-exceptions-open-picking-review", "warehouse", "warehouse-console-worklist/stock_exceptions", "open_picking_review", "productized_navigation", "page", label="View picking review", target_route_pattern="/desk/warehouse-console-picking/<sales-order>", notes="Read-only custom Warehouse picking review drilldown."),
	_action("warehouse-stock-exceptions-open-receiving-review", "warehouse", "warehouse-console-worklist/stock_exceptions", "open_receiving_review", "productized_navigation", "page", label="View inbound review", target_route_pattern="/desk/warehouse-console-receiving/<purchase-order>", notes="Read-only custom Warehouse receiving review drilldown."),
	_action("warehouse-movement-refresh", "warehouse", "warehouse-console-worklist/movement_visibility", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("warehouse-movement-reset", "warehouse", "warehouse-console-worklist/movement_visibility", "reset_filters", "productized_secondary_action", "current_shell", label="Reset"),
	_action("warehouse-movement-apply", "warehouse", "warehouse-console-worklist/movement_visibility", "apply_filters", "productized_primary_action", "current_shell", label="Apply"),
	_action("warehouse-movement-view-lines", "warehouse", "warehouse-console-worklist/movement_visibility", "view_lines", "productized_secondary_action", "current_shell", label="View lines"),
	_action("warehouse-movement-open-movement-review", "warehouse", "warehouse-console-worklist/movement_visibility", "open_movement_review", "productized_navigation", "page", label="Review movement", target_route_pattern="/desk/warehouse-console-movement/<encoded-context>", notes="Read-only custom Warehouse movement review drilldown."),
	_action("warehouse-movement-open-stock-posture", "warehouse", "warehouse-console-worklist/movement_visibility", "open_stock_posture", "productized_navigation", "page", label="Review stock posture", target_route_pattern="/desk/warehouse-console-stock-posture/<encoded-context>", notes="Read-only custom Warehouse item and warehouse posture drilldown."),
	_action("warehouse-transfer-refresh", "warehouse", "warehouse-console-worklist/transfer_visibility", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("warehouse-transfer-reset", "warehouse", "warehouse-console-worklist/transfer_visibility", "reset_filters", "productized_secondary_action", "current_shell", label="Reset"),
	_action("warehouse-transfer-apply", "warehouse", "warehouse-console-worklist/transfer_visibility", "apply_filters", "productized_primary_action", "current_shell", label="Apply"),
	_action("warehouse-transfer-view-lines", "warehouse", "warehouse-console-worklist/transfer_visibility", "view_lines", "productized_secondary_action", "current_shell", label="View lines"),
	_action("warehouse-transfer-open-movement-review", "warehouse", "warehouse-console-worklist/transfer_visibility", "open_movement_review", "productized_navigation", "page", label="Review movement", target_route_pattern="/desk/warehouse-console-movement/<encoded-context>", notes="Read-only custom Warehouse movement review drilldown."),
	_action("warehouse-transfer-open-stock-posture", "warehouse", "warehouse-console-worklist/transfer_visibility", "open_stock_posture", "productized_navigation", "page", label="Review stock posture", target_route_pattern="/desk/warehouse-console-stock-posture/<encoded-context>", notes="Read-only custom Warehouse item and warehouse posture drilldown."),
	_action("warehouse-picking-refresh", "warehouse", "warehouse-console-picking/<sales-order>", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("warehouse-picking-back-to-queue", "warehouse", "warehouse-console-picking/<sales-order>", "back_to_outbound_picking", "productized_navigation", "worklist", label="Back to outbound picking", target_route_pattern="/desk/warehouse-console-worklist/outbound-picking"),
	_action("warehouse-picking-tab-switch", "warehouse", "warehouse-console-picking/<sales-order>", "switch_tab", "productized_secondary_action", "current_shell", label_pattern="Item Lines|Stock Readiness"),
	_action("warehouse-receiving-refresh", "warehouse", "warehouse-console-receiving/<purchase-order>", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("warehouse-receiving-back-to-queue", "warehouse", "warehouse-console-receiving/<purchase-order>", "back_to_inbound_receiving", "productized_navigation", "worklist", label="Back to inbound receiving", target_route_pattern="/desk/warehouse-console-worklist/inbound-receiving"),
	_action("warehouse-receiving-tab-switch", "warehouse", "warehouse-console-receiving/<purchase-order>", "switch_tab", "productized_secondary_action", "current_shell", label_pattern="Item Lines|Receipt History"),
	_action("warehouse-stock-exception-refresh", "warehouse", "warehouse-console-stock-exception/<encoded-context>", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("warehouse-stock-exception-back-to-list", "warehouse", "warehouse-console-stock-exception/<encoded-context>", "back_to_stock_exceptions", "productized_navigation", "worklist", label="Back to stock exceptions", target_route_pattern="/desk/warehouse-console-worklist/stock-exceptions"),
	_action("warehouse-stock-exception-open-picking-review", "warehouse", "warehouse-console-stock-exception/<encoded-context>", "open_picking_review", "productized_navigation", "page", label="Review picking posture", target_route_pattern="/desk/warehouse-console-picking/<sales-order>"),
	_action("warehouse-stock-exception-open-receiving-review", "warehouse", "warehouse-console-stock-exception/<encoded-context>", "open_receiving_review", "productized_navigation", "page", label="Review inbound cover", target_route_pattern="/desk/warehouse-console-receiving/<purchase-order>"),
	_action("warehouse-stock-exception-open-stock-posture", "warehouse", "warehouse-console-stock-exception/<encoded-context>", "open_stock_posture", "productized_navigation", "page", label="Review stock posture", target_route_pattern="/desk/warehouse-console-stock-posture/<encoded-context>"),
	_action("warehouse-stock-posture-refresh", "warehouse", "warehouse-console-stock-posture/<encoded-context>", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("warehouse-stock-posture-back", "warehouse", "warehouse-console-stock-posture/<encoded-context>", "back", "productized_navigation", "page", label="Back", target_route_pattern="/desk/warehouse-console-*"),
	_action("warehouse-stock-posture-open-picking-review", "warehouse", "warehouse-console-stock-posture/<encoded-context>", "open_picking_review", "productized_navigation", "page", label="Review picking posture", target_route_pattern="/desk/warehouse-console-picking/<sales-order>"),
	_action("warehouse-stock-posture-open-receiving-review", "warehouse", "warehouse-console-stock-posture/<encoded-context>", "open_receiving_review", "productized_navigation", "page", label="Review inbound cover", target_route_pattern="/desk/warehouse-console-receiving/<purchase-order>"),
	_action("warehouse-stock-posture-open-stock-exception", "warehouse", "warehouse-console-stock-posture/<encoded-context>", "open_stock_exception_review", "productized_navigation", "page", label="Review stock exception", target_route_pattern="/desk/warehouse-console-stock-exception/<encoded-context>"),
	_action("warehouse-movement-review-refresh", "warehouse", "warehouse-console-movement/<encoded-context>", "refresh", "productized_secondary_action", "current_shell", label="Refresh"),
	_action("warehouse-movement-review-back", "warehouse", "warehouse-console-movement/<encoded-context>", "back_to_movement_visibility", "productized_navigation", "worklist", label="Back to movement visibility", target_route_pattern="/desk/warehouse-console-worklist/movement-visibility"),
	_action("warehouse-movement-review-open-stock-posture", "warehouse", "warehouse-console-movement/<encoded-context>", "open_stock_posture", "productized_navigation", "page", label="Review stock posture", target_route_pattern="/desk/warehouse-console-stock-posture/<encoded-context>"),
	_action("warehouse-sidebar-overview-navigation", "warehouse", "warehouse-sidebar", "sidebar_overview_navigation", "productized_navigation", "page", label="Overview", target_route_pattern="/desk/warehouse-console", notes="Sidebar entry opens the Warehouse Overview."),
	_action("warehouse-sidebar-inbound-navigation", "warehouse", "warehouse-sidebar", "sidebar_inbound_navigation", "productized_navigation", "worklist", label="Inbound Receiving", target_route_pattern="/desk/warehouse-console-worklist/inbound-receiving", notes="Sidebar entry opens the read-only inbound queue."),
	_action("warehouse-sidebar-outbound-navigation", "warehouse", "warehouse-sidebar", "sidebar_outbound_navigation", "productized_navigation", "worklist", label="Outbound Picking", target_route_pattern="/desk/warehouse-console-worklist/outbound-picking", notes="Sidebar entry opens the read-only outbound queue."),
	_action("warehouse-sidebar-stock-exceptions-navigation", "warehouse", "warehouse-sidebar", "sidebar_stock_exceptions_navigation", "productized_navigation", "worklist", label="Stock Exceptions", target_route_pattern="/desk/warehouse-console-worklist/stock-exceptions", notes="Sidebar entry opens the read-only stock exceptions view."),
	_action("warehouse-sidebar-movement-navigation", "warehouse", "warehouse-sidebar", "sidebar_movement_navigation", "productized_navigation", "worklist", label="Movement Visibility", target_route_pattern="/desk/warehouse-console-worklist/movement-visibility", notes="Sidebar entry opens the read-only movement visibility view."),
	_action("warehouse-sidebar-transfer-navigation", "warehouse", "warehouse-sidebar", "sidebar_transfer_navigation", "productized_navigation", "worklist", label="Transfer Visibility", target_route_pattern="/desk/warehouse-console-worklist/transfer-visibility", notes="Sidebar entry opens the read-only transfer visibility view."),
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
	{
		"workspace_id": "warehouse",
		"scope": "w8c_productized_overview_inbound_outbound_stock_exception_stock_posture_movement_and_transfer_read_only_pages",
		"labels": FORBIDDEN_MUTATION_LABELS,
		"allowed_only_when": "future controlled Warehouse execution design and manifest update",
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
