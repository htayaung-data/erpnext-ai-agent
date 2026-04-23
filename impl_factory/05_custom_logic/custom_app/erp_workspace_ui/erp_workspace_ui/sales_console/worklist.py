from __future__ import annotations

import json
import re
from typing import Callable

import frappe
from frappe import _
from frappe.utils import cint, cstr, flt, fmt_money, formatdate, getdate, nowdate

from . import service


ROW_LIMIT = 50


@frappe.whitelist()
def get_sales_console_worklist_context(queue_key: str | None = None, filters: str | dict[str, object] | None = None) -> dict[str, object]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	normalized_key = _normalize_queue_key(queue_key)
	applied_filters = _normalize_filters(filters)
	context = service._build_context()
	scope = service._build_scope(context)
	today = getdate(nowdate())
	builder = _queue_registry(today, context, scope, applied_filters).get(normalized_key)
	if not builder:
		return _route_unavailable_payload(normalized_key, scope)
	return builder()


def _queue_registry(today, context: dict[str, object], scope: dict[str, object], applied_filters: dict[str, str]) -> dict[str, Callable[[], dict[str, object]]]:
	return {
		"open_orders": lambda: _build_sales_order_worklist(
			queue_key="open_orders",
			page_title="Open Sales Orders",
			summary_subtitle="All active operational sales orders in the current console scope.",
			filters_label="Active operational orders",
			filters_builder=lambda: service._sales_order_active_filters(scope),
			native_target=service._open_sales_order_target(scope),
			scope=scope,
		),
		"sales_orders_pending_fulfillment": lambda: _build_sales_order_worklist(
			queue_key="sales_orders_pending_fulfillment",
			page_title="Orders Pending Fulfillment",
			summary_subtitle="Approved sales orders that still require operational movement.",
			filters_label="Operational orders excluding pending approvals",
			filters_builder=lambda: service._sales_order_active_filters(scope, exclude_pending_workflow=True),
			native_target=service._pending_fulfillment_target(scope),
			scope=scope,
		),
		"partially_delivered_orders": lambda: _build_sales_order_worklist(
			queue_key="partially_delivered_orders",
			page_title="Partially Delivered Orders",
			summary_subtitle="Orders already moving, but still incomplete against customer commitment.",
			filters_label="Delivered between 1% and 99%",
			filters_builder=lambda: service._partially_delivered_sales_order_filters(scope),
			native_target=service._partially_delivered_orders_target(scope),
			scope=scope,
		),
		"orders_due_soon": lambda: _build_sales_order_worklist(
			queue_key="orders_due_soon",
			page_title="Orders Due Soon",
			summary_subtitle="Delivery commitments landing within the next three days.",
			filters_label="Delivery due within 3 days",
			filters_builder=lambda: service._orders_due_soon_filters(today, scope),
			native_target=service._orders_due_soon_target(today, scope),
			scope=scope,
		),
		"quotations_waiting_action": lambda: _build_quotation_worklist(
			queue_key="quotations_waiting_action",
			page_title="Quotations Waiting for Action",
			summary_subtitle="Draft and open quotations still requiring commercial movement.",
			filters_label="Draft and open quotations",
			filters_builder=lambda: service._quotation_action_filters(scope),
			native_target=service._actionable_quotation_target(scope),
			scope=scope,
		),
		"customer_directory": lambda: _build_customer_worklist(context, scope, applied_filters),
		"item_directory": lambda: _build_item_worklist(scope, applied_filters),
		"expiring_quotations": lambda: _build_quotation_worklist(
			queue_key="expiring_quotations",
			page_title="Quotations Nearing Expiry",
			summary_subtitle="Active quotations expiring within the next seven days.",
			filters_label="Valid till within 7 days",
			filters_builder=lambda: service._quotation_expiring_filters(today, scope),
			native_target=service._expiring_quotation_target(today, scope),
			scope=scope,
		),
		"orders_blocked_by_approval": lambda: _build_sales_order_approval_worklist(scope),
		"quotations_awaiting_approval": lambda: _build_quotation_approval_worklist(scope),
		"customer_follow_up_tasks": lambda: _build_follow_up_worklist(scope),
		"invoices_outstanding": lambda: _build_invoice_worklist(scope),
		"sales_returns_in_progress": lambda: _build_sales_return_worklist(today, scope),
	}


def _route_unavailable_payload(queue_key: str, scope: dict[str, object]) -> dict[str, object]:
	return {
		"page": {"title": "Sales Console Worklist"},
		"summary": {
			"kicker": "Sales Console worklist",
			"title": "Operational queue unavailable",
			"subtitle": f"The queue route '{queue_key or 'unknown'}' is not configured for this productized list surface.",
			"facts": _summary_facts(0, scope, "Unsupported queue route."),
		},
		"controls": {
			"scopeChips": _scope_chips(scope),
		},
		"results": {
			"title": "Queue state",
			"state": {
				"kind": "error",
				"title": "Queue route unavailable",
				"detail": "Open the Sales Console first, then launch the operational queue from the console card itself.",
			},
		},
		"action_targets": {},
	}


def _build_sales_order_worklist(
	*,
	queue_key: str,
	page_title: str,
	summary_subtitle: str,
	filters_label: str,
	filters_builder: Callable[[], tuple[list[list[object]], str]],
	native_target: dict[str, object],
	scope: dict[str, object],
) -> dict[str, object]:
	return _build_doctype_worklist(
		queue_key=queue_key,
		page_title=page_title,
		summary_subtitle=summary_subtitle,
		doctype="Sales Order",
		scope=scope,
		filters_builder=filters_builder,
		order_by=_preferred_order_by("Sales Order", ["delivery_date asc", "modified desc"]),
		fields=_available_fields("Sales Order", "customer", "delivery_date", "status", "per_delivered", "per_billed", "grand_total", "currency"),
		columns=[
			{"key": "sales_order", "label": "Sales Order"},
			{"key": "delivery", "label": "Delivery"},
			{"key": "execution", "label": "Execution"},
			{"key": "total", "label": "Grand Total", "align": "right"},
		],
		filter_items=[{"label": "View", "value": filters_label}],
		native_target=native_target,
		row_builder=_sales_order_row,
	)


def _build_quotation_worklist(
	*,
	queue_key: str,
	page_title: str,
	summary_subtitle: str,
	filters_label: str,
	filters_builder: Callable[[], tuple[list[list[object]], str]],
	native_target: dict[str, object],
	scope: dict[str, object],
) -> dict[str, object]:
	return _build_doctype_worklist(
		queue_key=queue_key,
		page_title=page_title,
		summary_subtitle=summary_subtitle,
		doctype="Quotation",
		scope=scope,
		filters_builder=filters_builder,
		order_by=_preferred_order_by("Quotation", ["valid_till asc", "modified desc"]),
		fields=_available_fields("Quotation", "party_name", "customer_name", "quotation_to", "valid_till", "status", "grand_total", "currency"),
		columns=[
			{"key": "quotation", "label": "Quotation"},
			{"key": "valid_till", "label": "Valid Till"},
			{"key": "status", "label": "Status"},
			{"key": "total", "label": "Quoted Value", "align": "right"},
		],
		filter_items=[{"label": "View", "value": filters_label}],
		native_target=native_target,
		row_builder=_quotation_row,
	)


def _build_customer_worklist(context: dict[str, object], scope: dict[str, object], applied_filters: dict[str, str]) -> dict[str, object]:
	base_filters = service._customer_scope_filters(context, scope)
	scope_note = "Active customer records visible in the current ERP permission scope."
	if base_filters.get("owner"):
		scope_note = "Active customer records reduced to the current owned sales scope."

	territory = applied_filters.get("territory") or ""
	customer_group = applied_filters.get("customer_group") or ""
	keyword = applied_filters.get("keyword") or ""

	rows = _fetch_customer_worklist_rows(
		base_filters=base_filters,
		territory=territory,
		customer_group=customer_group,
		account_status="",
		keyword=keyword,
	)

	action_targets: dict[str, object] = {}
	results_rows = []
	for record in rows:
		row_key = str(record.get("name") or frappe.generate_hash(length=10))
		results_rows.append(
			{
				"key": row_key,
				"cells": _customer_row(record)["cells"],
				"actions": [{"key": "open_record", "label": "Open"}],
			}
		)
		action_targets[f"row:{row_key}:open_record"] = {
			"kind": "form",
			"doctype": "Customer",
			"name": record.get("name"),
		}

	outstanding_customers = sum(1 for row in rows if flt(row.get("outstanding_amount") or 0) > 0)
	recent_active_customers = sum(1 for row in rows if row.get("recent_activity_date"))

	results_state = None
	if not results_rows:
		results_state = {
			"kind": "empty",
			"title": "No customers visible",
			"detail": "No active customer records match the current sales account view.",
		}

	territory_options, group_options = _customer_filter_options(base_filters)

	return {
		"page": {"title": "Customers"},
		"summary": {
			"kicker": "Sales Console worklist",
			"title": "Customers",
			"subtitle": "Sales-facing customer accounts with exposure and recent activity in the current scope.",
			"facts": _summary_facts(len(results_rows), scope, scope_note),
		},
		"controls": {
			"scopeChips": _scope_chips(scope),
			"actions": [
				{"key": "reset_filters", "label": "Reset"},
				{"key": "apply_filters", "label": "Apply", "kind": "primary"},
			],
			"fields": [
				{
					"key": "territory",
					"label": "Territory",
					"type": "select",
					"value": territory,
					"options": [{"label": "All territories", "value": ""}] + [{"label": item, "value": item} for item in territory_options],
				},
				{
					"key": "customer_group",
					"label": "Customer Group",
					"type": "select",
					"value": customer_group,
					"options": [{"label": "All groups", "value": ""}] + [{"label": item, "value": item} for item in group_options],
				},
				{
					"key": "keyword",
					"label": "Keyword",
					"type": "text",
					"value": keyword,
					"placeholder": "Search customer name or ID",
				},
			],
		},
		"metrics": [
			{"label": "Visible Customers", "value": str(len(results_rows)), "meta": f"Latest {ROW_LIMIT} visible accounts", "tone": "neutral"},
			{"label": "With Outstanding", "value": str(outstanding_customers), "meta": "Accounts still carrying receivable exposure", "tone": "attention"},
			{"label": "Recent Activity", "value": str(recent_active_customers), "meta": "Accounts with order or invoice activity in the latest 30 days", "tone": "positive"},
		],
		"results": {
			"title": "",
			"state": results_state,
			"meta": f"{len(results_rows)} visible - latest {ROW_LIMIT}",
			"columns": [
				{"key": "customer", "label": "Customer", "width": "34%"},
				{"key": "territory", "label": "Territory", "width": "14%"},
				{"key": "group", "label": "Customer Group", "width": "16%"},
				{"key": "outstanding", "label": "Outstanding", "width": "16%", "align": "right"},
				{"key": "credit", "label": "Credit Posture", "width": "20%"},
			],
			"rows": results_rows,
			"rowActions": True,
		},
		"action_targets": action_targets,
	}


def _build_item_worklist(scope: dict[str, object], applied_filters: dict[str, str]) -> dict[str, object]:
	if not service._can_read("Item"):
		return _restricted_payload(
			"Items",
			"Sales items available for quotation and order entry in the current console scope.",
			scope_note="Item is outside current permission scope.",
			scope=scope,
			native_target=service._item_native_target(),
		)

	item_group = applied_filters.get("item_group") or ""
	keyword = applied_filters.get("keyword") or ""
	availability = applied_filters.get("availability") or ""

	rows = _fetch_item_worklist_rows(scope=scope, item_group=item_group, keyword=keyword, availability=availability)
	in_stock_count = sum(1 for row in rows if flt(row.get("available_qty") or 0) > 0)
	out_of_stock_count = sum(1 for row in rows if flt(row.get("available_qty") or 0) <= 0)

	results_rows = []
	action_targets: dict[str, object] = {}
	for record in rows:
		row_key = str(record.get("name") or record.get("item_code") or frappe.generate_hash(length=10))
		results_rows.append(
			{
				"key": row_key,
				"cells": _item_row(record)["cells"],
				"actions": [{"key": "open_record", "label": "Open"}],
			}
		)
		action_targets[f"row:{row_key}:open_record"] = {
			"kind": "form",
			"doctype": "Item",
			"name": record.get("name"),
		}

	results_state = None
	if not results_rows:
		results_state = {
			"kind": "empty",
			"title": "No items visible",
			"detail": "No active sales items match the current stock-aware view.",
		}

	return {
		"page": {"title": "Items"},
		"summary": {
			"kicker": "Sales Console worklist",
			"title": "Items",
			"subtitle": "Sales items with stock posture visible for quotation and order entry in the current console scope.",
			"facts": _summary_facts(len(results_rows), scope, "Stock signal is reduced from current item warehouses."),
		},
		"controls": {
			"scopeChips": _scope_chips(scope),
			"fields": [
				{
					"key": "item_group",
					"label": "Item Group",
					"type": "select",
					"value": item_group,
					"options": [{"label": "All groups", "value": ""}, *[
						{"label": group, "value": group} for group in _item_group_options()
					]],
				},
				{
					"key": "availability",
					"label": "Availability",
					"type": "select",
					"value": availability,
					"options": [
						{"label": "All items", "value": ""},
						{"label": "In stock", "value": "in_stock"},
						{"label": "Out of stock", "value": "out_of_stock"},
					],
				},
				{
					"key": "keyword",
					"label": "Keyword",
					"type": "text",
					"value": keyword,
					"placeholder": "Search item code or item name",
				},
			],
			"actions": [
				{"key": "reset_filters", "label": "Reset"},
				{"key": "apply_filters", "label": "Apply", "kind": "primary"},
			],
		},
		"metrics": [
			{"label": "Visible Items", "value": str(len(results_rows)), "meta": f"Latest {ROW_LIMIT} visible items", "tone": "neutral"},
			{"label": "In Stock", "value": str(in_stock_count), "meta": "Items currently carrying positive stock", "tone": "positive"},
			{"label": "Out of Stock", "value": str(out_of_stock_count), "meta": "Items currently without positive stock", "tone": "warning"},
		],
		"results": {
			"title": "",
			"state": results_state,
			"meta": f"{len(results_rows)} visible - latest {ROW_LIMIT}",
			"columns": [
				{"key": "item_code", "label": "Item Code", "width": "22%"},
				{"key": "item_name", "label": "Item", "width": "24%"},
				{"key": "item_group", "label": "Item Group", "width": "18%"},
				{"key": "stock", "label": "Stock", "width": "36%"},
			],
			"rows": results_rows,
			"rowActions": True,
		},
		"action_targets": action_targets,
	}


def _build_sales_order_approval_worklist(scope: dict[str, object]) -> dict[str, object]:
	return _build_doctype_worklist(
		queue_key="orders_blocked_by_approval",
		page_title="Orders Blocked by Approval",
		summary_subtitle="Sales orders currently waiting for commercial or control approval before execution can continue.",
		doctype="Sales Order",
		scope=scope,
		filters_builder=lambda: service._sales_order_approval_filters(scope),
		order_by=_preferred_order_by("Sales Order", ["modified desc"]),
		fields=_available_fields("Sales Order", "customer", "delivery_date", "workflow_state", "status", "grand_total", "currency"),
		columns=[
			{"key": "sales_order", "label": "Sales Order"},
			{"key": "delivery", "label": "Delivery"},
			{"key": "review", "label": "Approval"},
			{"key": "total", "label": "Grand Total", "align": "right"},
		],
		filter_items=[{"label": "View", "value": "Pending sales-order approvals"}],
		native_target=service._blocked_sales_order_target(scope),
		row_builder=_sales_order_approval_row,
		empty_title="No blocked sales orders",
		empty_detail="No sales orders are currently waiting for approval inside this permission scope.",
	)


def _build_quotation_approval_worklist(scope: dict[str, object]) -> dict[str, object]:
	return _build_doctype_worklist(
		queue_key="quotations_awaiting_approval",
		page_title="Quotations Awaiting Approval",
		summary_subtitle="Quotations currently held in workflow review before they can move commercially.",
		doctype="Quotation",
		scope=scope,
		filters_builder=lambda: service._quotation_approval_filters(scope),
		order_by=_preferred_order_by("Quotation", ["valid_till asc", "modified desc"]),
		fields=_available_fields("Quotation", "party_name", "customer_name", "quotation_to", "valid_till", "workflow_state", "status", "grand_total", "currency"),
		columns=[
			{"key": "quotation", "label": "Quotation"},
			{"key": "valid_till", "label": "Valid Till"},
			{"key": "review", "label": "Approval"},
			{"key": "total", "label": "Quoted Value", "align": "right"},
		],
		filter_items=[{"label": "View", "value": "Pending quotation approvals"}],
		native_target=service._quotation_approval_target(scope),
		row_builder=_quotation_approval_row,
		empty_title="No quotations awaiting approval",
		empty_detail="No quotations are currently waiting for approval inside this permission scope.",
	)


def _build_follow_up_worklist(scope: dict[str, object]) -> dict[str, object]:
	filters, scope_note, assignee_field = service._follow_up_filters(scope)
	native_target = service._follow_up_target(scope)
	fields = ["description", "status", "priority", "reference_type", "reference_name"]
	if assignee_field:
		fields.append(assignee_field)
	if "date" in service._fieldnames("ToDo"):
		fields.append("date")
	return _build_doctype_worklist(
		queue_key="customer_follow_up_tasks",
		page_title="Customer Follow-Up Tasks",
		summary_subtitle="Open sales-facing tasks linked to customer communication and document follow-through.",
		doctype="ToDo",
		scope=scope,
		filters_builder=lambda: (filters, scope_note),
		order_by=_preferred_order_by("ToDo", ["date asc", "modified desc"]),
		fields=_available_fields("ToDo", *fields),
		columns=[
			{"key": "task", "label": "Task"},
			{"key": "due", "label": "Due"},
			{"key": "reference", "label": "Linked Record"},
		],
		filter_items=[{"label": "View", "value": "Open customer-facing ToDo records"}],
		native_target=native_target,
		row_builder=_todo_row,
		empty_title="No open customer follow-up tasks",
		empty_detail="No sales-facing follow-up tasks are currently assigned inside this permission scope.",
	)


def _build_invoice_worklist(scope: dict[str, object]) -> dict[str, object]:
	return _build_doctype_worklist(
		queue_key="invoices_outstanding",
		page_title="Invoices Outstanding",
		summary_subtitle="Submitted customer invoices that still need payment or settlement follow-through.",
		doctype="Sales Invoice",
		scope=scope,
		filters_builder=lambda: service._invoice_outstanding_filters(scope),
		order_by=_preferred_order_by("Sales Invoice", ["due_date asc", "posting_date desc", "modified desc"]),
		fields=_available_fields("Sales Invoice", "customer", "posting_date", "due_date", "status", "outstanding_amount", "grand_total", "currency"),
		columns=[
			{"key": "invoice", "label": "Invoice"},
			{"key": "timeline", "label": "Due / Posted"},
			{"key": "status", "label": "Settlement"},
			{"key": "outstanding", "label": "Outstanding", "align": "right"},
		],
		filter_items=[{"label": "View", "value": "Unpaid, partly paid, or overdue invoices"}],
		native_target=service._invoices_outstanding_target(scope),
		row_builder=_invoice_row,
	)


def _build_sales_return_worklist(today, scope: dict[str, object]) -> dict[str, object]:
	if service._can_read("Sales Invoice"):
		doctype = "Sales Invoice"
		filters_builder = lambda: service._sales_return_filters("Sales Invoice", today, scope)
		fields = _available_fields("Sales Invoice", "customer", "posting_date", "return_against", "status", "grand_total", "currency")
		columns = [
			{"key": "document", "label": "Sales Return"},
			{"key": "posted", "label": "Posted"},
			{"key": "reference", "label": "Return Against"},
			{"key": "value", "label": "Return Value", "align": "right"},
		]
		row_builder = _invoice_return_row
	else:
		doctype = "Delivery Note"
		filters_builder = lambda: service._sales_return_filters("Delivery Note", today, scope)
		fields = _available_fields("Delivery Note", "customer", "posting_date", "return_against", "status", "grand_total", "currency")
		columns = [
			{"key": "document", "label": "Return Delivery"},
			{"key": "posted", "label": "Posted"},
			{"key": "reference", "label": "Return Against"},
			{"key": "value", "label": "Gross Value", "align": "right"},
		]
		row_builder = _delivery_return_row

	return _build_doctype_worklist(
		queue_key="sales_returns_in_progress",
		page_title="Sales Returns in Progress",
		summary_subtitle="Recent customer return records still affecting the current commercial chain.",
		doctype=doctype,
		scope=scope,
		filters_builder=filters_builder,
		order_by=_preferred_order_by(doctype, ["posting_date desc", "modified desc"]),
		fields=fields,
		columns=columns,
		filter_items=[{"label": "View", "value": "Recent sales returns in the last 30 days"}],
		native_target=service._sales_returns_target(today, scope),
		row_builder=row_builder,
		empty_title="No recent sales returns",
		empty_detail="No return invoices or return deliveries are currently visible in this commercial scope.",
	)


def _build_doctype_worklist(
	*,
	queue_key: str,
	page_title: str,
	summary_subtitle: str,
	doctype: str,
	scope: dict[str, object],
	filters_builder: Callable[[], tuple[list[list[object]], str]],
	order_by: str,
	fields: list[str],
	columns: list[dict[str, object]],
	filter_items: list[dict[str, object]],
	native_target: dict[str, object],
	row_builder: Callable[[dict[str, object]], dict[str, object]],
	empty_title: str | None = None,
	empty_detail: str | None = None,
) -> dict[str, object]:
	if not service._can_read(doctype):
		return _restricted_payload(page_title, summary_subtitle, scope_note=f"{doctype} is outside current permission scope.", scope=scope, native_target=native_target)

	filters, scope_note = filters_builder()
	try:
		rows = frappe.get_list(
			doctype,
			fields=["name", *[field for field in fields if field != "name"]],
			filters=filters,
			order_by=order_by,
			limit_page_length=ROW_LIMIT,
		)
	except (frappe.PermissionError, frappe.DataError):
		return _restricted_payload(page_title, summary_subtitle, scope_note=f"{doctype} rows could not be read in the current permission scope.", scope=scope, native_target=native_target)

	results_rows = []
	action_targets: dict[str, object] = {}

	for record in rows:
		row_config = row_builder(record)
		row_key = str(record.get("name") or frappe.generate_hash(length=10))
		results_rows.append(
			{
				"key": row_key,
				"cells": row_config["cells"],
				"actions": row_config.get("actions") or [{"key": "open_record", "label": "Open"}],
			}
		)
		action_targets[f"row:{row_key}:open_record"] = row_config.get("open_target") or {
			"kind": "form",
			"doctype": doctype,
			"name": record.get("name"),
		}
		for action_key, target in (row_config.get("action_targets") or {}).items():
			action_targets[f"row:{row_key}:{action_key}"] = target

	results_state = None
	if not results_rows:
		results_state = {
			"kind": "empty",
			"title": empty_title or f"No {page_title.lower()} visible",
			"detail": empty_detail or "No records are currently visible in this ERP permission scope.",
		}

	return {
		"page": {"title": page_title},
		"summary": {
			"kicker": "Sales Console worklist",
			"title": page_title,
			"subtitle": summary_subtitle,
			"facts": _summary_facts(len(results_rows), scope, scope_note),
		},
		"controls": {
			"filters": filter_items,
			"scopeChips": _scope_chips(scope),
			"actions": [],
		},
		"results": {
			"title": "",
			"state": results_state,
			"meta": f"{len(results_rows)} visible - latest {ROW_LIMIT}",
			"columns": columns,
			"rows": results_rows,
			"rowActions": True,
		},
		"action_targets": action_targets,
	}


def _restricted_payload(
	page_title: str,
	summary_subtitle: str,
	*,
	scope_note: str,
	scope: dict[str, object] | None,
	native_target: dict[str, object] | None,
) -> dict[str, object]:
	return {
		"page": {"title": page_title},
		"summary": {
			"kicker": "Sales Console worklist",
			"title": page_title,
			"subtitle": summary_subtitle,
			"facts": _summary_facts(0, scope, scope_note),
		},
		"controls": {
			"scopeChips": _scope_chips(scope or {}),
			"actions": [],
		},
		"results": {
			"title": "Queue state",
			"state": {
				"kind": "error",
				"title": "Queue unavailable",
				"detail": scope_note,
			},
		},
		"action_targets": {},
	}


def _summary_facts(visible_rows: int, scope: dict[str, object] | None, scope_note: str) -> list[dict[str, object]]:
	return [
		{"label": "Visible Rows", "value": str(visible_rows), "meta": f"Latest {ROW_LIMIT} records"},
		{"label": "Scope", "value": _scope_label(scope or {}), "meta": scope_note},
	]


def _scope_label(scope: dict[str, object]) -> str:
	return {
		"team_review_scope": "Team scope",
		"assigned_account_scope": "Account scope",
		"showroom_scope": "Showroom scope",
		"executive_review_scope": "Executive scope",
		"branch_and_owner_filtered": "User + branch scope",
		"permission_scope": "Permission scope",
	}.get(scope.get("scope_mode"), "Permission scope")


def _scope_chips(scope: dict[str, object]) -> list[dict[str, object]]:
	chips = []
	label = _scope_label(scope)
	if label:
		chips.append({"label": label, "tone": "neutral"})
	branch_name = scope.get("branch_name")
	if branch_name:
		chips.append({"label": branch_name, "tone": "neutral"})
	return chips


def _preferred_order_by(doctype: str, candidates: list[str]) -> str:
	fields = service._fieldnames(doctype)
	for candidate in candidates:
		parts = [segment.strip().split()[0] for segment in candidate.split(",")]
		if all(field in fields or field == "modified" for field in parts):
			return candidate
	return "modified desc"


def _available_fields(doctype: str, *requested_fields: str) -> list[str]:
	fields = service._fieldnames(doctype)
	return [field for field in requested_fields if field in fields]


def _sales_order_row(record: dict[str, object]) -> dict[str, object]:
	return {
		"cells": {
			"sales_order": {"value": record.get("name"), "meta": record.get("customer") or "--"},
			"delivery": {"value": _date(record.get("delivery_date")), "meta": record.get("status") or "--"},
			"execution": {
				"value": f"{cint(flt(record.get('per_delivered') or 0))}% delivered",
				"meta": f"{cint(flt(record.get('per_billed') or 0))}% billed",
			},
			"total": {"value": _money(record.get("grand_total"), record.get("currency"))},
		},
	}


def _quotation_row(record: dict[str, object]) -> dict[str, object]:
	customer_label = record.get("customer_name") or record.get("party_name") or "--"
	return {
		"cells": {
			"quotation": {"value": record.get("name"), "meta": customer_label},
			"valid_till": {"value": _date(record.get("valid_till"))},
			"status": {"value": record.get("status") or "--"},
			"total": {"value": _money(record.get("grand_total"), record.get("currency"))},
		},
	}


def _customer_row(record: dict[str, object]) -> dict[str, object]:
	customer_name = record.get("customer_name") or record.get("name") or "--"
	customer_meta = record.get("name") if record.get("name") and record.get("name") != customer_name else None
	recent_label = "--"
	recent_type = cstr(record.get("recent_activity_type") or "").strip()
	recent_name = cstr(record.get("recent_activity_name") or "").strip()
	recent_date = record.get("recent_activity_date")
	if recent_type and recent_name and recent_date:
		recent_label = f"Last {recent_type.lower()} {_date(recent_date)}"
	elif recent_type and recent_date:
		recent_label = f"Last {recent_type.lower()} {_date(recent_date)}"
	else:
		recent_label = "No recent sales"
	return {
		"cells": {
			"customer": {"value": customer_name, "meta": customer_meta or recent_label, "metaLines": [recent_label] if customer_meta else []},
			"territory": {"value": record.get("territory") or "--"},
			"group": {"value": record.get("customer_group") or "--"},
			"outstanding": {"value": _money(record.get("outstanding_amount"), "MMK"), "tone": "attention" if flt(record.get("outstanding_amount") or 0) > 0 else ""},
			"credit": {
				"value": record.get("credit_posture_label") or "--",
				"meta": record.get("credit_posture_meta") or "",
				"tone": record.get("credit_posture_tone") or "",
			},
		},
	}


def _sales_order_approval_row(record: dict[str, object]) -> dict[str, object]:
	workflow_state = record.get("workflow_state") or "Pending approval"
	return {
		"cells": {
			"sales_order": {"value": record.get("name"), "meta": record.get("customer") or "--"},
			"delivery": {"value": _date(record.get("delivery_date")), "meta": record.get("status") or "--"},
			"review": {"value": workflow_state, "meta": record.get("status") or "--", "tone": "pending"},
			"total": {"value": _money(record.get("grand_total"), record.get("currency"))},
		},
	}


def _quotation_approval_row(record: dict[str, object]) -> dict[str, object]:
	workflow_state = record.get("workflow_state") or "Pending approval"
	customer_label = record.get("customer_name") or record.get("party_name") or "--"
	return {
		"cells": {
			"quotation": {"value": record.get("name"), "meta": customer_label},
			"valid_till": {"value": _date(record.get("valid_till"))},
			"review": {"value": workflow_state, "meta": record.get("status") or "--", "tone": "pending"},
			"total": {"value": _money(record.get("grand_total"), record.get("currency"))},
		},
	}


def _todo_row(record: dict[str, object]) -> dict[str, object]:
	reference_type = record.get("reference_type")
	reference_name = record.get("reference_name")
	status = record.get("status") or "--"
	priority = record.get("priority") or "--"
	due_value, due_meta, due_tone = _todo_due_signal(record.get("date"), status)
	status_tone = _todo_status_tone(status, priority)
	open_target = {"kind": "form", "doctype": reference_type, "name": reference_name} if reference_type and reference_name else {
		"kind": "form",
		"doctype": "ToDo",
		"name": record.get("name"),
	}
	return {
		"open_target": open_target,
		"cells": {
			"task": {"value": record.get("description") or record.get("name") or "--", "meta": priority},
			"due": {"value": due_value, "meta": due_meta, "tone": due_tone},
			"reference": {"value": reference_name or "--", "meta": reference_type or "ToDo"},
		},
	}


def _item_row(record: dict[str, object]) -> dict[str, object]:
	item_code = record.get("item_code") or record.get("name") or "--"
	item_name = record.get("item_name") or "--"
	stock_cell = _item_stock_cell(record)
	return {
		"cells": {
			"item_code": {"value": item_code},
			"item_name": {"value": item_name, "meta": record.get("name") if record.get("name") and record.get("name") != item_code else ""},
			"item_group": {"value": record.get("item_group") or "--"},
			"stock": stock_cell,
		},
	}


def _fetch_item_worklist_rows(*, scope: dict[str, object], item_group: str, keyword: str, availability: str) -> list[dict[str, object]]:
	item_fields = service._fieldnames("Item")
	conditions = ["ifnull(i.disabled, 0) = 0"]
	params: dict[str, object] = {}
	if "is_sales_item" in item_fields:
		conditions.append("ifnull(i.is_sales_item, 0) = 1")
	if item_group:
		conditions.append("i.item_group = %(item_group)s")
		params["item_group"] = item_group
	if keyword:
		params["keyword"] = f"%{keyword.strip()}%"
		conditions.append("(i.item_code like %(keyword)s or i.item_name like %(keyword)s)")
	if availability == "in_stock":
		conditions.append("ifnull(stock.available_qty, 0) > 0")
	elif availability == "out_of_stock":
		conditions.append("ifnull(stock.available_qty, 0) <= 0")

	where_clause = " and ".join(conditions) if conditions else "1=1"
	rows = frappe.db.sql(
		f"""
		select
			i.name,
			i.item_code,
			i.item_name,
			i.item_group,
			i.stock_uom,
			ifnull(stock.available_qty, 0) as available_qty
		from tabItem i
		left join (
			select
				b.item_code,
				sum(ifnull(b.actual_qty, 0)) as available_qty
			from tabBin b
			group by b.item_code
		) stock on stock.item_code = i.item_code
		where {where_clause}
		order by i.item_group asc, i.item_name asc, i.item_code asc
		limit {ROW_LIMIT}
		""",
		params,
		as_dict=True,
	)
	if not rows:
		return []

	item_codes = [row.get("item_code") for row in rows if row.get("item_code")]
	warehouse_rows = frappe.db.sql(
		"""
		select
			item_code,
			warehouse,
			actual_qty
		from tabBin
		where item_code in %(item_codes)s
		  and ifnull(actual_qty, 0) > 0
		order by item_code asc, actual_qty desc, warehouse asc
		""",
		{"item_codes": tuple(item_codes)},
		as_dict=True,
	)

	warehouse_map: dict[str, list[dict[str, object]]] = {}
	branch_name = str(scope.get("branch_name") or "").strip().lower()
	for entry in warehouse_rows:
		item_code = entry.get("item_code")
		if not item_code:
			continue
		warehouse_map.setdefault(item_code, []).append(entry)

	for row in rows:
		row_warehouses = warehouse_map.get(row.get("item_code") or "", [])
		row["stock_entries"] = sorted(
			row_warehouses,
			key=lambda entry: (
				0 if branch_name and branch_name in str(entry.get("warehouse") or "").lower() else 1,
				-flt(entry.get("actual_qty") or 0),
				str(entry.get("warehouse") or ""),
			),
		)

	return rows


def _item_group_options() -> list[str]:
	rows = frappe.db.sql(
		"""
		select distinct item_group
		from tabItem
		where ifnull(disabled, 0) = 0
		  and ifnull(is_sales_item, 0) = 1
		  and ifnull(item_group, '') != ''
		order by item_group asc
		""",
		as_dict=True,
	)
	return [row["item_group"] for row in rows if row.get("item_group")]


def _customer_filter_options(base_filters: dict[str, object]) -> tuple[list[str], list[str]]:
	rows = frappe.get_all(
		"Customer",
		filters=base_filters,
		fields=["territory", "customer_group"],
		order_by=_preferred_order_by("Customer", ["customer_name asc", "modified desc"]),
		limit_page_length=500,
	)
	territories: list[str] = []
	groups: list[str] = []
	seen_territories: set[str] = set()
	seen_groups: set[str] = set()
	for row in rows:
		territory = cstr(row.get("territory") or "").strip()
		group = cstr(row.get("customer_group") or "").strip()
		if territory and territory not in seen_territories:
			seen_territories.add(territory)
			territories.append(territory)
		if group and group not in seen_groups:
			seen_groups.add(group)
			groups.append(group)
	return territories, groups


def _fetch_customer_worklist_rows(
	*,
	base_filters: dict[str, object],
	territory: str,
	customer_group: str,
	account_status: str,
	keyword: str,
) -> list[dict[str, object]]:
	customer_filters = dict(base_filters or {})
	if territory:
		customer_filters["territory"] = territory
	if customer_group:
		customer_filters["customer_group"] = customer_group

	customer_rows = frappe.get_all(
		"Customer",
		filters=customer_filters,
		fields=_available_fields("Customer", "name", "customer_name", "territory", "customer_group", "mobile_no", "email_id"),
		or_filters=(
			[
				["name", "like", f"%{keyword.strip()}%"],
				["customer_name", "like", f"%{keyword.strip()}%"],
			]
			if keyword.strip()
			else None
		),
		order_by=_preferred_order_by("Customer", ["customer_name asc", "modified desc"]),
		limit_page_length=ROW_LIMIT,
	)
	if not customer_rows:
		return []

	customer_names = [row.get("name") for row in customer_rows if row.get("name")]
	outstanding_map = _customer_outstanding_map(customer_names)
	credit_map = _customer_credit_map(customer_names)
	recent_map = _customer_recent_activity_map(customer_names)

	results = []
	for row in customer_rows:
		name = row.get("name")
		outstanding = flt(outstanding_map.get(name) or 0)
		credit_data = credit_map.get(name) or {}
		credit_limit = flt(credit_data.get("credit_limit") or 0)
		bypass_credit_limit_check = cint(credit_data.get("bypass_credit_limit_check") or 0)
		recent_activity = recent_map.get(name) or {}
		posture_code, posture_label, posture_meta, posture_tone = _customer_credit_posture(
			outstanding=outstanding,
			credit_limit=credit_limit,
			bypass_credit_limit_check=bypass_credit_limit_check,
		)
		enriched = dict(row)
		enriched.update(
			{
				"outstanding_amount": outstanding,
				"credit_limit": credit_limit,
				"bypass_credit_limit_check": bypass_credit_limit_check,
				"credit_posture_code": posture_code,
				"credit_posture_label": posture_label,
				"credit_posture_meta": posture_meta,
				"credit_posture_tone": posture_tone,
				"recent_activity_type": recent_activity.get("activity_type"),
				"recent_activity_name": recent_activity.get("activity_name"),
				"recent_activity_date": recent_activity.get("activity_date"),
			}
		)
		results.append(enriched)

	if account_status:
		results = [row for row in results if row.get("credit_posture_code") == account_status]

	return results


def _customer_outstanding_map(customer_names: list[str]) -> dict[str, float]:
	if not customer_names or not service._doctype_exists("Sales Invoice"):
		return {}
	fields = service._fieldnames("Sales Invoice")
	if "customer" not in fields or "outstanding_amount" not in fields:
		return {}
	rows = frappe.db.sql(
		"""
		select customer, sum(outstanding_amount) as outstanding_amount
		from `tabSales Invoice`
		where docstatus = 1
		  and customer in %(customers)s
		  and ifnull(outstanding_amount, 0) > 0
		group by customer
		""",
		{"customers": tuple(customer_names)},
		as_dict=True,
	)
	return {row.get("customer"): flt(row.get("outstanding_amount") or 0) for row in rows if row.get("customer")}


def _customer_credit_map(customer_names: list[str]) -> dict[str, dict[str, object]]:
	if not customer_names or not service._doctype_exists("Customer Credit Limit"):
		return {}
	rows = frappe.db.sql(
		"""
		select parent, max(credit_limit) as credit_limit, max(bypass_credit_limit_check) as bypass_credit_limit_check
		from `tabCustomer Credit Limit`
		where parent in %(customers)s
		group by parent
		""",
		{"customers": tuple(customer_names)},
		as_dict=True,
	)
	return {
		row.get("parent"): {
			"credit_limit": flt(row.get("credit_limit") or 0),
			"bypass_credit_limit_check": cint(row.get("bypass_credit_limit_check") or 0),
		}
		for row in rows
		if row.get("parent")
	}


def _customer_recent_activity_map(customer_names: list[str]) -> dict[str, dict[str, object]]:
	activity_by_customer: dict[str, dict[str, object]] = {}
	candidates: list[dict[str, object]] = []

	if customer_names and service._doctype_exists("Sales Order"):
		fields = service._fieldnames("Sales Order")
		if "customer" in fields and "transaction_date" in fields:
			rows = frappe.get_all(
				"Sales Order",
				filters={"customer": ["in", customer_names], "docstatus": 1},
				fields=_available_fields("Sales Order", "customer", "name", "transaction_date"),
				order_by=_preferred_order_by("Sales Order", ["transaction_date desc", "modified desc"]),
				limit_page_length=500,
			)
			for row in rows:
				candidates.append(
					{
						"customer": row.get("customer"),
						"activity_type": "Order",
						"activity_name": row.get("name"),
						"activity_date": row.get("transaction_date"),
					}
				)

	if customer_names and service._doctype_exists("Sales Invoice"):
		fields = service._fieldnames("Sales Invoice")
		if "customer" in fields and "posting_date" in fields:
			rows = frappe.get_all(
				"Sales Invoice",
				filters={"customer": ["in", customer_names], "docstatus": 1},
				fields=_available_fields("Sales Invoice", "customer", "name", "posting_date"),
				order_by=_preferred_order_by("Sales Invoice", ["posting_date desc", "modified desc"]),
				limit_page_length=500,
			)
			for row in rows:
				candidates.append(
					{
						"customer": row.get("customer"),
						"activity_type": "Invoice",
						"activity_name": row.get("name"),
						"activity_date": row.get("posting_date"),
					}
				)

	for candidate in sorted(
		candidates,
		key=lambda item: getdate(item.get("activity_date")) if item.get("activity_date") else getdate("1900-01-01"),
		reverse=True,
	):
		customer = candidate.get("customer")
		if customer and customer not in activity_by_customer:
			activity_by_customer[customer] = candidate

	return activity_by_customer


def _customer_credit_posture(*, outstanding: float, credit_limit: float, bypass_credit_limit_check: int) -> tuple[str, str, str, str]:
	if bypass_credit_limit_check:
		return "commercially_clear", "Limit bypassed", "Manual credit bypass enabled", "neutral"
	if credit_limit > 0 and outstanding > credit_limit:
		return "credit_review", "Over limit", f"Limit {_money(credit_limit, 'MMK')}", "warning"
	if outstanding > 0 and credit_limit <= 0:
		return "credit_review", "No limit set", "Outstanding without configured limit", "attention"
	if outstanding > 0:
		return "outstanding", "Within limit", f"Limit {_money(credit_limit, 'MMK')}", "positive"
	if credit_limit > 0:
		return "commercially_clear", "Clear", f"Limit {_money(credit_limit, 'MMK')}", "neutral"
	return "commercially_clear", "Clear", "No limit in use", "neutral"


def _item_stock_cell(record: dict[str, object]) -> dict[str, object]:
	available_qty = flt(record.get("available_qty") or 0)
	stock_entries = list(record.get("stock_entries") or [])
	if available_qty <= 0 or not stock_entries:
		return {
			"value": "Out of stock",
			"meta": "No positive stock",
			"tone": "warning",
		}

	visible_entries = stock_entries[:2]
	lines = [_format_stock_location_line(entry) for entry in visible_entries]
	remaining = max(len(stock_entries) - len(visible_entries), 0)
	if remaining:
		lines.append(f"+{remaining} more locations")

	return {
		"value": lines[0],
		"metaLines": lines[1:],
		"tone": "positive",
	}


def _format_stock_location_line(entry: dict[str, object]) -> str:
	warehouse = cstr(entry.get("warehouse") or "--").strip()
	warehouse = re.sub(r"\s*-\s*[A-Z0-9]+$", "", warehouse).strip()
	qty = _qty(entry.get("actual_qty"))
	return f"{warehouse}: {qty}"


def _invoice_row(record: dict[str, object]) -> dict[str, object]:
	return {
		"cells": {
			"invoice": {"value": record.get("name"), "meta": record.get("customer") or "--"},
			"timeline": {"value": _date(record.get("due_date")), "meta": f"Posted {_date(record.get('posting_date'))}"},
			"status": {"value": record.get("status") or "--", "meta": _money(record.get("grand_total"), record.get("currency"))},
			"outstanding": {"value": _money(record.get("outstanding_amount"), record.get("currency"))},
		},
	}


def _invoice_return_row(record: dict[str, object]) -> dict[str, object]:
	reference_name = record.get("return_against") or "--"
	return {
		"action_targets": {
			"open_reference": {
				"kind": "form",
				"doctype": "Sales Invoice",
				"name": record.get("return_against"),
			}
		} if record.get("return_against") else {},
		"cells": {
			"document": {"value": record.get("name"), "meta": record.get("customer") or "--"},
			"posted": {"value": _date(record.get("posting_date")), "meta": "Credit note"},
			"reference": {"value": reference_name, "actionKey": "open_reference"} if record.get("return_against") else {"value": reference_name},
			"value": {"value": _money(record.get("grand_total"), record.get("currency")), "tone": "attention"},
		},
	}


def _delivery_return_row(record: dict[str, object]) -> dict[str, object]:
	reference_name = record.get("return_against") or "--"
	return {
		"action_targets": {
			"open_reference": {
				"kind": "form",
				"doctype": "Delivery Note",
				"name": record.get("return_against"),
			}
		} if record.get("return_against") else {},
		"cells": {
			"document": {"value": record.get("name"), "meta": record.get("customer") or "--"},
			"posted": {"value": _date(record.get("posting_date")), "meta": "Return delivery"},
			"reference": {"value": reference_name, "actionKey": "open_reference"} if record.get("return_against") else {"value": reference_name},
			"value": {"value": _money(record.get("grand_total"), record.get("currency")), "tone": "attention"},
		},
	}


def _todo_due_signal(value, status: str) -> tuple[str, str, str]:
	due_date = getdate(value) if value else None
	if not due_date:
		return "--", status or "--", ""

	today = getdate(nowdate())
	if due_date < today:
		return _date(due_date), "Overdue", "blocker"
	if due_date == today:
		return _date(due_date), "Due today", "attention"
	return _date(due_date), status or "--", ""


def _todo_status_tone(status: str, priority: str) -> str:
	status_value = (status or "").strip().lower()
	priority_value = (priority or "").strip().lower()
	if status_value in {"cancelled", "closed", "overdue"}:
		return "blocker"
	if priority_value in {"high", "urgent"}:
		return "attention"
	if status_value in {"open", "pending"}:
		return "pending"
	return ""


def _normalize_queue_key(value: str | None) -> str:
	return str(value or "").strip().lower().replace("-", "_")


def _normalize_filters(value) -> dict[str, str]:
	if not value:
		return {}
	if isinstance(value, str):
		try:
			value = json.loads(value)
		except Exception:
			return {}
	if not isinstance(value, dict):
		return {}
	return {
		str(key): str(item).strip()
		for key, item in value.items()
		if item not in (None, "")
	}


def _date(value) -> str:
	if not value:
		return "--"
	return formatdate(value)


def _money(amount, currency) -> str:
	if amount in (None, ""):
		return "--"
	return fmt_money(amount, currency=currency)


def _qty(value) -> str:
	number = flt(value or 0)
	if abs(number - int(number)) < 0.000001:
		return str(int(number))
	return f"{number:,.2f}".rstrip("0").rstrip(".")
