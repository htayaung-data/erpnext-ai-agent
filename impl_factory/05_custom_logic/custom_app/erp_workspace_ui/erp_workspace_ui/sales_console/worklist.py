from __future__ import annotations

import json
import re
from datetime import timedelta
from typing import Callable

import frappe
from frappe import _
from frappe.utils import cint, cstr, flt, fmt_money, formatdate, getdate, nowdate

from . import service


ROW_LIMIT = 50


QUOTATION_DIRECTORY_VIEW_OPTIONS = [
	{"label": "All visible quotations", "value": "all_visible"},
	{"label": "Waiting action", "value": "waiting_action"},
	{"label": "Awaiting approval", "value": "awaiting_approval"},
	{"label": "Expiring soon", "value": "expiring_soon"},
	{"label": "Expired", "value": "expired"},
]

SALES_ORDER_DIRECTORY_VIEW_OPTIONS = [
	{"label": "All visible orders", "value": "all_visible"},
	{"label": "Open orders", "value": "open_orders"},
	{"label": "Pending fulfillment", "value": "pending_fulfillment"},
	{"label": "Awaiting approval", "value": "awaiting_approval"},
	{"label": "Due soon", "value": "due_soon"},
	{"label": "Partially delivered", "value": "partially_delivered"},
]

QUOTATION_STATUS_OPTIONS = [
	"",
	"Draft",
	"Open",
	"Ordered",
	"Lost",
	"Cancelled",
]

SALES_ORDER_STATUS_OPTIONS = [
	"",
	"Draft",
	"To Deliver",
	"To Bill",
	"To Deliver and Bill",
	"Partly Delivered",
	"Partly Billed",
	"Partly Delivered and Billed",
	"Completed",
	"Closed",
	"On Hold",
	"Cancelled",
]

CUSTOMER_ACTIVITY_DOCUMENT_TYPE_OPTIONS = [
	{"label": "All activity", "value": ""},
	{"label": "Quotations", "value": "Quotation"},
	{"label": "Sales Orders", "value": "Sales Order"},
	{"label": "Invoices", "value": "Sales Invoice"},
]


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
		return _apply_worklist_operating_contract(_route_unavailable_payload(normalized_key, scope))
	return _apply_worklist_operating_contract(builder())


@frappe.whitelist()
def save_sales_console_customer_profile(payload: str | dict[str, object] | None = None) -> dict[str, object]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	values = _normalize_customer_profile_payload(payload)
	context = service._build_context()
	scope = service._build_scope(context)
	mode = cstr(values.get("mode") or "").strip().lower()
	customer_name = cstr(values.get("customer") or "").strip()
	if not mode:
		mode = "edit" if customer_name else "new"

	if mode not in {"new", "edit"}:
		frappe.throw(_("Unsupported customer profile mode."), frappe.ValidationError)

	permission_type = "create" if mode == "new" else "write"
	if not _can_manage_customer_profile(context, permission_type):
		frappe.throw(_("Only Sales Managers with Customer {0} permission can perform this action.").format(permission_type), frappe.PermissionError)

	customer_payload, contact_payload = _validated_customer_profile_values(values, mode=mode)
	if mode == "new":
		duplicates = _possible_customer_duplicates({**customer_payload, **contact_payload})
		if duplicates:
			return {
				"state": "duplicate_warning",
				"message": _("Possible duplicate customer found. Review the existing account before creating a new one."),
				"duplicates": duplicates,
			}
		doc = frappe.new_doc("Customer")
	else:
		if not customer_name:
			frappe.throw(_("Customer context is required for update."), frappe.ValidationError)
		base_filters = service._customer_scope_filters(context, scope)
		if not _fetch_customer_detail_record(base_filters=base_filters, customer_name=customer_name):
			frappe.throw(_("This customer is outside the current Sales Console scope."), frappe.PermissionError)
		doc = frappe.get_doc("Customer", customer_name)

	customer_fields = service._fieldnames("Customer")
	for fieldname, value in customer_payload.items():
		if fieldname in customer_fields:
			doc.set(fieldname, value)

	if mode == "new":
		doc.insert(ignore_permissions=False)
		message = _("Customer created.")
	else:
		doc.save(ignore_permissions=False)
		message = _("Customer updated.")

	_save_customer_contact_details(doc, contact_payload)
	doc.reload()
	return _customer_profile_saved_response(doc, message=message)


def _queue_registry(today, context: dict[str, object], scope: dict[str, object], applied_filters: dict[str, str]) -> dict[str, Callable[[], dict[str, object]]]:
	return {
		"quotation_directory": lambda: _build_quotation_directory_worklist(today, context, scope, applied_filters),
		"sales_order_directory": lambda: _build_sales_order_directory_worklist(today, context, scope, applied_filters),
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
		"customer_detail": lambda: _build_customer_detail_worklist(context, scope, applied_filters),
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
		"customer_follow_up_tasks": lambda: _build_follow_up_worklist(scope, applied_filters),
		"invoices_outstanding": lambda: _build_invoice_worklist(scope),
		"sales_returns_in_progress": lambda: _build_sales_return_worklist(today, scope),
		"customer_editor": lambda: _build_customer_editor_worklist(context, scope, applied_filters),
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


def _base_worklist_actions(*, include_filter_actions: bool) -> list[dict[str, object]]:
	actions: list[dict[str, object]] = [
		{"key": "refresh", "label": "Refresh"},
	]
	if include_filter_actions:
		actions.extend(
			[
				{"key": "reset_filters", "label": "Reset"},
				{"key": "apply_filters", "label": "Apply", "kind": "primary"},
			]
		)
	return actions


def _merge_operating_actions(
	base_actions: list[dict[str, object]], extra_actions: list[dict[str, object]] | None = None
) -> list[dict[str, object]]:
	merged: list[dict[str, object]] = []
	seen_keys: set[str] = set()
	for action in [*(base_actions or []), *((extra_actions or []))]:
		if not isinstance(action, dict):
			continue
		key = cstr(action.get("key")).strip()
		if not key or key in seen_keys:
			continue
		seen_keys.add(key)
		merged.append(dict(action))
	return merged


def _apply_worklist_operating_contract(payload: dict[str, object]) -> dict[str, object]:
	normalized = dict(payload or {})
	controls = dict(normalized.get("controls") or {})
	existing_actions = [
		dict(action)
		for action in (controls.get("actions") or [])
		if isinstance(action, dict)
	]
	include_filter_actions = not controls.get("suppressFilterActions") and (
		bool(controls.get("fields")) or any(
			cstr(action.get("key")).strip() in {"reset_filters", "apply_filters"}
			for action in existing_actions
		)
	)
	base_actions = [] if controls.get("suppressBaseActions") else _base_worklist_actions(include_filter_actions=include_filter_actions)
	controls["actions"] = _merge_operating_actions(
		base_actions,
		existing_actions,
	)
	normalized["controls"] = controls
	return normalized


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


def _build_quotation_directory_worklist(today, context: dict[str, object], scope: dict[str, object], applied_filters: dict[str, str]) -> dict[str, object]:
	if not service._can_read("Quotation"):
		return _restricted_payload(
			"Quotations",
			"All visible quotations in the current console scope, with operational views available above the table.",
			scope_note="Quotation is outside current permission scope.",
			scope=scope,
			native_target=service._quotation_native_target(scope),
		)

	view = applied_filters.get("view") or "all_visible"
	status = applied_filters.get("status") or ""
	date_start = applied_filters.get("date_start") or ""
	date_end = applied_filters.get("date_end") or ""
	keyword = applied_filters.get("keyword") or ""

	rows, scope_note = _fetch_quotation_directory_rows(
		today=today,
		context=context,
		scope=scope,
		view=view,
		status=status,
		date_start=date_start,
		date_end=date_end,
		keyword=keyword,
	)
	results_rows = []
	action_targets: dict[str, object] = {}
	for record in rows:
		row_key = str(record.get("name") or frappe.generate_hash(length=10))
		results_rows.append(
			{
				"key": row_key,
				"cells": _quotation_directory_row(record, today)["cells"],
				"actions": [{"key": "open_record", "label": "Open"}],
			}
		)
		action_targets[f"row:{row_key}:open_record"] = {
			"kind": "form",
			"doctype": "Quotation",
			"name": record.get("name"),
		}

	waiting_action_count = sum(1 for row in rows if _quotation_waiting_action_match(row))
	approval_count = sum(1 for row in rows if _pending_workflow_match("Quotation", row.get("workflow_state")))
	expiring_count = sum(1 for row in rows if _quotation_expiring_match(row, today))

	results_state = None
	if not results_rows:
		results_state = {
			"kind": "empty",
			"title": "No quotations visible",
			"detail": "No quotation records match the current directory filters inside this console scope.",
		}

	return {
		"page": {"title": "Quotations"},
		"summary": {
			"kicker": "Sales Console worklist",
			"title": "Quotations",
			"subtitle": "All visible quotations in the current console scope, with operational slices available through the filter bar.",
			"facts": _summary_facts(len(results_rows), scope, scope_note),
		},
		"controls": {
			"scopeChips": _scope_chips(scope),
			"fields": [
				{
					"key": "view",
					"label": "View",
					"type": "select",
					"value": view,
					"options": QUOTATION_DIRECTORY_VIEW_OPTIONS,
				},
				{
					"key": "status",
					"label": "Status",
					"type": "select",
					"value": status,
					"options": [{"label": "All statuses", "value": ""}] + [
						{"label": item, "value": item} for item in QUOTATION_STATUS_OPTIONS if item
					],
				},
				{
					"key": "date_start",
					"label": "Date Start",
					"type": "date",
					"value": date_start,
				},
				{
					"key": "date_end",
					"label": "Date End",
					"type": "date",
					"value": date_end,
				},
				{
					"key": "keyword",
					"label": "Keyword",
					"type": "text",
					"value": keyword,
					"placeholder": "Search quotation, customer, or party name",
				},
			],
			"actions": [
				{"key": "reset_filters", "label": "Reset"},
				{"key": "apply_filters", "label": "Apply", "kind": "primary"},
			],
		},
		"metrics": [
			{"label": "Visible Quotations", "value": str(len(results_rows)), "meta": f"Latest {ROW_LIMIT} visible quotations", "tone": "neutral"},
			{"label": "Waiting Action", "value": str(waiting_action_count), "meta": "Draft/open quotations still requiring commercial movement", "tone": "attention"},
			{"label": "Awaiting Approval", "value": str(approval_count), "meta": "Visible quotations currently parked in workflow review", "tone": "warning"},
			{"label": "Expiring Soon", "value": str(expiring_count), "meta": "Visible quotations nearing their current validity date", "tone": "positive"},
		],
		"results": {
			"title": "",
			"state": results_state,
			"meta": f"{len(results_rows)} visible - latest {ROW_LIMIT}",
			"columns": [
				{"key": "quotation", "label": "Quotation", "width": "34%"},
				{"key": "valid_till", "label": "Valid Till", "width": "18%"},
				{"key": "commercial_state", "label": "Commercial State", "width": "24%"},
				{"key": "total", "label": "Quoted Value", "width": "24%", "align": "right"},
			],
			"rows": results_rows,
			"rowActions": True,
		},
		"action_targets": action_targets,
	}


def _build_sales_order_directory_worklist(today, context: dict[str, object], scope: dict[str, object], applied_filters: dict[str, str]) -> dict[str, object]:
	if not service._can_read("Sales Order"):
		return _restricted_payload(
			"Sales Orders",
			"All visible sales orders in the current console scope, with operational views available above the table.",
			scope_note="Sales Order is outside current permission scope.",
			scope=scope,
			native_target=service._sales_order_native_target(scope),
		)

	view = applied_filters.get("view") or "all_visible"
	status = applied_filters.get("status") or ""
	date_start = applied_filters.get("date_start") or ""
	date_end = applied_filters.get("date_end") or ""
	keyword = applied_filters.get("keyword") or ""

	rows, scope_note = _fetch_sales_order_directory_rows(
		today=today,
		context=context,
		scope=scope,
		view=view,
		status=status,
		date_start=date_start,
		date_end=date_end,
		keyword=keyword,
	)
	results_rows = []
	action_targets: dict[str, object] = {}
	for record in rows:
		row_key = str(record.get("name") or frappe.generate_hash(length=10))
		results_rows.append(
			{
				"key": row_key,
				"cells": _sales_order_directory_row(record, today)["cells"],
				"actions": [{"key": "open_record", "label": "Open"}],
			}
		)
		action_targets[f"row:{row_key}:open_record"] = {
			"kind": "form",
			"doctype": "Sales Order",
			"name": record.get("name"),
		}

	open_orders_count = sum(1 for row in rows if _sales_order_active_match(row))
	pending_fulfillment_count = sum(1 for row in rows if _sales_order_pending_fulfillment_match(row))
	approval_count = sum(1 for row in rows if _pending_workflow_match("Sales Order", row.get("workflow_state")))
	due_soon_count = sum(1 for row in rows if _sales_order_due_soon_match(row, today))

	results_state = None
	if not results_rows:
		results_state = {
			"kind": "empty",
			"title": "No sales orders visible",
			"detail": "No sales orders match the current directory filters inside this console scope.",
		}

	return {
		"page": {"title": "Sales Orders"},
		"summary": {
			"kicker": "Sales Console worklist",
			"title": "Sales Orders",
			"subtitle": "All visible sales orders in the current console scope, with operational slices available through the filter bar.",
			"facts": _summary_facts(len(results_rows), scope, scope_note),
		},
		"controls": {
			"scopeChips": _scope_chips(scope),
			"fields": [
				{
					"key": "view",
					"label": "View",
					"type": "select",
					"value": view,
					"options": SALES_ORDER_DIRECTORY_VIEW_OPTIONS,
				},
				{
					"key": "status",
					"label": "Status",
					"type": "select",
					"value": status,
					"options": [{"label": "All statuses", "value": ""}] + [
						{"label": item, "value": item} for item in SALES_ORDER_STATUS_OPTIONS if item
					],
				},
				{
					"key": "date_start",
					"label": "Date Start",
					"type": "date",
					"value": date_start,
				},
				{
					"key": "date_end",
					"label": "Date End",
					"type": "date",
					"value": date_end,
				},
				{
					"key": "keyword",
					"label": "Keyword",
					"type": "text",
					"value": keyword,
					"placeholder": "Search order ID or customer",
				},
			],
			"actions": [
				{"key": "reset_filters", "label": "Reset"},
				{"key": "apply_filters", "label": "Apply", "kind": "primary"},
			],
		},
		"metrics": [
			{"label": "Visible Orders", "value": str(len(results_rows)), "meta": f"Latest {ROW_LIMIT} visible orders", "tone": "neutral"},
			{"label": "Open Orders", "value": str(open_orders_count), "meta": "Visible active orders in the current scope", "tone": "attention"},
			{"label": "Pending Fulfillment", "value": str(pending_fulfillment_count), "meta": "Active orders ready for operational movement", "tone": "positive"},
			{"label": "Awaiting Approval", "value": str(approval_count), "meta": "Visible orders currently held in workflow review", "tone": "warning"},
			{"label": "Due Soon", "value": str(due_soon_count), "meta": "Visible delivery commitments landing within three days", "tone": "attention"},
		],
		"results": {
			"title": "",
			"state": results_state,
			"meta": f"{len(results_rows)} visible - latest {ROW_LIMIT}",
			"columns": [
				{"key": "sales_order", "label": "Sales Order", "width": "32%"},
				{"key": "delivery", "label": "Delivery Date", "width": "18%"},
				{"key": "commercial_state", "label": "Commercial State", "width": "26%"},
				{"key": "total", "label": "Grand Total", "width": "24%", "align": "right"},
			],
			"rows": results_rows,
			"rowActions": True,
		},
		"action_targets": action_targets,
	}


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
			"kind": "worklist",
			"queue_key": "customer_detail",
			"filters": {"customer": record.get("name")},
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

	territory_options, group_options = _customer_profile_select_options(base_filters)

	actions = [
		{"key": "reset_filters", "label": "Reset"},
		{"key": "apply_filters", "label": "Apply", "kind": "primary"},
	]
	if _can_manage_customer_profile(context, "create"):
		actions.append({"key": "create_customer", "label": "Create Customer"})
		action_targets["create_customer"] = {
			"kind": "worklist",
			"queue_key": "customer_editor",
			"filters": {"mode": "new"},
		}

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
			"actions": actions,
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


def _build_customer_detail_worklist(context: dict[str, object], scope: dict[str, object], applied_filters: dict[str, str]) -> dict[str, object]:
	customer_name = cstr(applied_filters.get("customer") or applied_filters.get("keyword") or "").strip()
	document_type = cstr(applied_filters.get("document_type") or "").strip()
	if not customer_name:
		return _customer_detail_state_payload(
			title="Customer detail unavailable",
			detail="Open a customer from the Sales Console Customers page so the customer context is passed through.",
			scope=scope,
		)

	base_filters = service._customer_scope_filters(context, scope)
	customer = _fetch_customer_detail_record(base_filters=base_filters, customer_name=customer_name)
	if not customer:
		return _customer_detail_state_payload(
			title="Customer not visible",
			detail="This customer is outside the current Sales Console permission or account scope.",
			scope=scope,
		)

	rows, action_targets = _customer_detail_recent_rows(customer.get("name"), document_type=document_type)
	actions = [{"key": "back_to_customers", "label": "Back to Customers", "category": "navigation"}]
	if _can_manage_customer_profile(context, "write"):
		actions.append({"key": "edit_customer", "label": "Edit Customer", "category": "navigation"})
	customer_label = customer.get("customer_name") or customer.get("name") or customer_name
	header_meta = _customer_detail_header_meta(customer)
	open_orders = sum(1 for row in rows if row.get("document_type") == "Sales Order" and row.get("open_state"))
	open_invoices = sum(1 for row in rows if row.get("document_type") == "Sales Invoice" and row.get("open_state"))

	return {
		"page": {"title": customer_label},
		"summary": {
			"kicker": "Customer Detail",
			"title": customer_label,
			"subtitle": header_meta,
			"facts": [
				{"label": "Customer ID", "value": customer.get("name") or "--", "meta": "Sales Console-owned customer context"},
				{"label": "Territory", "value": customer.get("territory") or "--", "meta": customer.get("customer_group") or "Customer group not set"},
				{"label": "Scope", "value": cstr(scope.get("branch") or scope.get("team") or "Current permission"), "meta": "Visible account context"},
			],
		},
		"controls": {
			"scopeChips": _scope_chips(scope),
			"actions": actions,
			"fields": [
				{
					"key": "document_type",
					"label": "Activity Type",
					"type": "select",
					"value": document_type,
					"options": CUSTOMER_ACTIVITY_DOCUMENT_TYPE_OPTIONS,
				},
				{
					"key": "customer",
					"label": "Customer",
					"type": "hidden",
					"value": customer.get("name"),
				},
			],
		},
		"metrics": [
			{
				"label": "Outstanding",
				"value": _money(customer.get("outstanding_amount"), "MMK"),
				"meta": "Receivable exposure",
				"tone": "attention" if flt(customer.get("outstanding_amount") or 0) > 0 else "neutral",
			},
			{
				"label": "Credit Posture",
				"value": customer.get("credit_posture_label") or "--",
				"meta": customer.get("credit_posture_meta") or "",
				"tone": customer.get("credit_posture_tone") or "neutral",
			},
			{"label": "Open Orders", "value": str(open_orders), "meta": "Recent submitted orders not completed", "tone": "attention" if open_orders else "neutral"},
			{"label": "Open Invoices", "value": str(open_invoices), "meta": "Recent invoices still outstanding", "tone": "attention" if open_invoices else "neutral"},
		],
		"results": {
			"title": "Recent Customer Activity",
			"state": None if rows else {
				"kind": "empty",
				"title": "No recent customer activity",
				"detail": "No records match this customer activity filter.",
			},
			"meta": f"{len(rows)} visible recent records",
			"columns": [
				{"key": "document", "label": "Document", "width": "32%"},
				{"key": "date", "label": "Date", "width": "18%"},
				{"key": "status", "label": "Status", "width": "24%"},
				{"key": "value", "label": "Value", "width": "26%", "align": "right"},
			],
			"rows": rows,
			"rowActions": True,
		},
		"action_targets": {
			"back_to_customers": {"kind": "worklist", "queue_key": "customer_directory"},
			"edit_customer": {
				"kind": "worklist",
				"queue_key": "customer_editor",
				"filters": {"mode": "edit", "customer": customer.get("name")},
			},
			**action_targets,
		},
	}


def _customer_detail_header_meta(customer: dict[str, object]) -> str:
	parts = [
		cstr(customer.get("customer_group") or "").strip(),
		cstr(customer.get("territory") or "").strip(),
		cstr(customer.get("mobile_no") or "").strip(),
	]
	return " · ".join([part for part in parts if part]) or "No customer group, territory, or primary phone recorded"


def _build_customer_editor_worklist(context: dict[str, object], scope: dict[str, object], applied_filters: dict[str, str]) -> dict[str, object]:
	customer_name = cstr(applied_filters.get("customer") or "").strip()
	mode = cstr(applied_filters.get("mode") or "").strip().lower() or ("edit" if customer_name else "new")
	if mode not in {"new", "edit"}:
		mode = "new"

	permission_type = "create" if mode == "new" else "write"
	if not _can_manage_customer_profile(context, permission_type):
		return _customer_detail_state_payload(
			title="Customer management restricted",
			detail="Customer creation and profile edits are reserved for Sales Managers with matching Customer permissions.",
			scope=scope,
		)

	base_filters = service._customer_scope_filters(context, scope)
	customer: dict[str, object] = {}
	if mode == "edit":
		customer = _fetch_customer_detail_record(base_filters=base_filters, customer_name=customer_name) or {}
		if not customer:
			return _customer_detail_state_payload(
				title="Customer not visible",
				detail="This customer is outside the current Sales Console permission or account scope.",
				scope=scope,
			)

	territory_options, group_options = _customer_profile_select_options(base_filters)
	current_group = cstr(customer.get("customer_group") or "").strip()
	current_territory = cstr(customer.get("territory") or "").strip()
	if current_group and current_group not in group_options:
		group_options.insert(0, current_group)
	if current_territory and current_territory not in territory_options:
		territory_options.insert(0, current_territory)

	title = "Create Customer" if mode == "new" else "Edit Customer"
	subtitle = (
		"Add a customer your team can use for quotations, orders, and follow-up."
		if mode == "new"
		else ""
	)
	back_target = {
		"kind": "worklist",
		"queue_key": "customer_detail" if mode == "edit" and customer.get("name") else "customer_directory",
		"filters": {"customer": customer.get("name")} if mode == "edit" and customer.get("name") else {},
	}
	form_note = (
		"Create the customer with name, group, territory, phone, and email. Credit limit, payment terms, tax settings, and account controls can be completed later by Admin or Finance."
		if mode == "new"
		else "You can update customer name, group, territory, phone, and email here. Credit limit, payment terms, tax settings, and account controls are managed by Admin or Finance."
	)

	return {
		"page": {"title": title},
		"summary": {
			"kicker": "Customer Profile",
			"title": title,
			"subtitle": subtitle,
			"facts": _summary_facts(1, scope, "Customer information for the current sales scope."),
		},
		"controls": {
			"scopeChips": _scope_chips(scope),
			"layout": "form_panel",
			"note": form_note,
			"suppressFilterActions": True,
			"suppressBaseActions": True,
			"actions": [
				{"key": "save_customer_profile", "label": "Save Customer", "kind": "primary"},
				{"key": "cancel_customer_editor", "label": "Back to Customer" if mode == "edit" else "Back to Customers", "category": "navigation"},
			],
			"fields": [
				{"key": "mode", "label": "Mode", "type": "hidden", "value": mode},
				{"key": "customer", "label": "Customer", "type": "hidden", "value": customer.get("name") or ""},
				{
					"key": "customer_name",
					"label": "Customer Name",
					"type": "text",
					"value": customer.get("customer_name") or "",
					"placeholder": "Legal or trading name",
				},
				{
					"key": "customer_group",
					"label": "Customer Group",
					"type": "select",
					"value": current_group,
					"options": [{"label": "Select group", "value": ""}] + [{"label": item, "value": item} for item in group_options],
				},
				{
					"key": "territory",
					"label": "Territory",
					"type": "select",
					"value": current_territory,
					"options": [{"label": "Select territory", "value": ""}] + [{"label": item, "value": item} for item in territory_options],
				},
				{
					"key": "mobile_no",
					"label": "Phone",
					"type": "text",
					"value": customer.get("mobile_no") or "",
					"placeholder": "Primary phone",
				},
				{
					"key": "email_id",
					"label": "Email",
					"type": "text",
					"value": customer.get("email_id") or "",
					"placeholder": "Primary email",
				},
			],
		},
		"metrics": [],
		"results": None,
		"action_targets": {
			"save_customer_profile": {
				"kind": "api_method",
				"method": "erp_workspace_ui.sales_console.worklist.save_sales_console_customer_profile",
				"collect_fields": True,
				"stay_on_success": True,
			},
			"cancel_customer_editor": back_target,
		},
	}


def _can_manage_customer_profile(context: dict[str, object], permission_type: str) -> bool:
	if cstr((context or {}).get("role_variant")) != "sales_manager":
		return False
	return service._doctype_exists("Customer") and bool(
		frappe.has_permission("Customer", permission_type, user=frappe.session.user)
	)


def _customer_profile_select_options(base_filters: dict[str, object]) -> tuple[list[str], list[str]]:
	territory_options, group_options = _customer_filter_options(base_filters)
	if service._doctype_exists("Territory") and service._can_read("Territory"):
		territory_fields = service._fieldnames("Territory")
		territory_filters = {"is_group": 0} if "is_group" in territory_fields else {}
		territory_rows = frappe.get_all(
			"Territory",
			filters=territory_filters,
			fields=["name"],
			order_by="name asc",
			limit_page_length=500,
		)
		territory_options = [row.get("name") for row in territory_rows if row.get("name")] or territory_options
	if service._doctype_exists("Customer Group") and service._can_read("Customer Group"):
		group_fields = service._fieldnames("Customer Group")
		group_filters = {"is_group": 0} if "is_group" in group_fields else {}
		group_rows = frappe.get_all(
			"Customer Group",
			filters=group_filters,
			fields=["name"],
			order_by="name asc",
			limit_page_length=500,
		)
		group_options = [row.get("name") for row in group_rows if row.get("name")] or group_options
	return territory_options, group_options


def _customer_profile_saved_response(doc, *, message: str) -> dict[str, object]:
	customer_fields = service._fieldnames("Customer")
	contact_values = _customer_primary_contact_values({"name": doc.name, "customer_primary_contact": doc.get("customer_primary_contact")})
	saved_values = {
		"mode": "edit",
		"customer": doc.name,
		"customer_name": doc.get("customer_name") if "customer_name" in customer_fields else doc.name,
		"customer_group": doc.get("customer_group") if "customer_group" in customer_fields else "",
		"territory": doc.get("territory") if "territory" in customer_fields else "",
		"mobile_no": contact_values.get("mobile_no") or (doc.get("mobile_no") if "mobile_no" in customer_fields else ""),
		"email_id": contact_values.get("email_id") or (doc.get("email_id") if "email_id" in customer_fields else ""),
	}
	return {
		"state": "saved",
		"customer": doc.name,
		"message": message,
		"values": saved_values,
		"filters": {"mode": "edit", "customer": doc.name},
	}


def _save_customer_contact_details(customer_doc, contact_values: dict[str, str]) -> None:
	if not service._doctype_exists("Contact"):
		return
	mobile_no = cstr(contact_values.get("mobile_no") or "").strip()
	email_id = cstr(contact_values.get("email_id") or "").strip()
	if not (mobile_no or email_id or customer_doc.get("customer_primary_contact")):
		return

	contact = _get_or_create_customer_primary_contact(customer_doc, create_if_missing=bool(mobile_no or email_id))
	if not contact:
		return

	_set_primary_contact_email(contact, email_id)
	_set_primary_contact_mobile(contact, mobile_no)
	contact.save(ignore_permissions=True)

	customer_fields = service._fieldnames("Customer")
	if "customer_primary_contact" in customer_fields and customer_doc.get("customer_primary_contact") != contact.name:
		customer_doc.set("customer_primary_contact", contact.name)
		customer_doc.save(ignore_permissions=False)


def _get_or_create_customer_primary_contact(customer_doc, *, create_if_missing: bool):
	contact_name = cstr(customer_doc.get("customer_primary_contact") or "").strip()
	if contact_name and frappe.db.exists("Contact", contact_name):
		return frappe.get_doc("Contact", contact_name)

	linked_contact = _linked_customer_contact_name(customer_doc.name)
	if linked_contact:
		return frappe.get_doc("Contact", linked_contact)

	if not create_if_missing:
		return None

	contact = frappe.new_doc("Contact")
	contact.first_name = cstr(customer_doc.get("customer_name") or customer_doc.name).strip()[:140] or customer_doc.name
	if "is_primary_contact" in service._fieldnames("Contact"):
		contact.is_primary_contact = 1
	contact.append(
		"links",
		{
			"link_doctype": "Customer",
			"link_name": customer_doc.name,
			"link_title": customer_doc.get("customer_name") or customer_doc.name,
		},
	)
	contact.insert(ignore_permissions=True)
	return contact


def _linked_customer_contact_name(customer_name: str) -> str:
	if not customer_name or not service._doctype_exists("Dynamic Link"):
		return ""
	rows = frappe.get_all(
		"Dynamic Link",
		filters={
			"link_doctype": "Customer",
			"link_name": customer_name,
			"parenttype": "Contact",
		},
		fields=["parent"],
		order_by="idx asc",
		limit_page_length=1,
	)
	return cstr(rows[0].get("parent") if rows else "").strip()


def _customer_primary_contact_values(customer: dict[str, object]) -> dict[str, str]:
	values = {"mobile_no": "", "email_id": ""}
	if not customer or not service._doctype_exists("Contact"):
		return values

	contact_name = cstr(customer.get("customer_primary_contact") or "").strip()
	if not contact_name:
		contact_name = _linked_customer_contact_name(cstr(customer.get("name") or "").strip())
	if not contact_name:
		return values

	rows = frappe.get_all(
		"Contact",
		filters={"name": contact_name},
		fields=_available_fields("Contact", "name", "mobile_no", "email_id"),
		limit_page_length=1,
	)
	if not rows:
		return values
	row = rows[0]
	values["mobile_no"] = cstr(row.get("mobile_no") or "").strip()
	values["email_id"] = cstr(row.get("email_id") or "").strip()
	return values


def _set_primary_contact_email(contact, email_id: str) -> None:
	email_id = cstr(email_id or "").strip()
	found = False
	for row in list(contact.get("email_ids") or []):
		if email_id and not found and (
			cint(row.get("is_primary")) or cstr(row.get("email_id") or "").strip().lower() == email_id.lower()
		):
			row.email_id = email_id
			row.is_primary = 1
			found = True
			continue
		if cint(row.get("is_primary")):
			if email_id:
				row.is_primary = 0
			else:
				contact.remove(row)
	if email_id and not found:
		contact.append("email_ids", {"email_id": email_id, "is_primary": 1})


def _set_primary_contact_mobile(contact, mobile_no: str) -> None:
	mobile_no = cstr(mobile_no or "").strip()
	found = False
	for row in list(contact.get("phone_nos") or []):
		if mobile_no and not found and (
			cint(row.get("is_primary_mobile_no")) or cstr(row.get("phone") or "").strip() == mobile_no
		):
			row.phone = mobile_no
			row.is_primary_mobile_no = 1
			found = True
			continue
		if cint(row.get("is_primary_mobile_no")):
			if mobile_no:
				row.is_primary_mobile_no = 0
			else:
				contact.remove(row)
		else:
			row.is_primary_mobile_no = 0
	if mobile_no and not found:
		contact.append("phone_nos", {"phone": mobile_no, "is_primary_mobile_no": 1})


def _normalize_customer_profile_payload(value) -> dict[str, str]:
	if isinstance(value, str):
		try:
			value = json.loads(value)
		except Exception:
			value = {}
	if not isinstance(value, dict):
		value = {}

	allowed_keys = {
		"mode",
		"customer",
		"customer_name",
		"customer_group",
		"territory",
		"mobile_no",
		"email_id",
	}
	return {key: cstr(value.get(key) or "").strip() for key in allowed_keys}


def _validated_customer_profile_values(values: dict[str, str], *, mode: str) -> tuple[dict[str, str], dict[str, str]]:
	customer_name = cstr(values.get("customer_name") or "").strip()
	customer_group = cstr(values.get("customer_group") or "").strip()
	territory = cstr(values.get("territory") or "").strip()
	mobile_no = cstr(values.get("mobile_no") or "").strip()
	email_id = cstr(values.get("email_id") or "").strip()

	if not customer_name:
		frappe.throw(_("Customer name is required."), frappe.ValidationError)
	if not customer_group:
		frappe.throw(_("Customer group is required."), frappe.ValidationError)
	if not territory:
		frappe.throw(_("Territory is required."), frappe.ValidationError)
	if email_id and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email_id):
		frappe.throw(_("Enter a valid customer email address."), frappe.ValidationError)

	payload = {
		"customer_name": customer_name,
		"customer_group": customer_group,
		"territory": territory,
	}
	if mode == "new":
		payload["customer_type"] = "Company"
	return payload, {"mobile_no": mobile_no, "email_id": email_id}


def _possible_customer_duplicates(values: dict[str, str]) -> list[dict[str, object]]:
	fields = service._fieldnames("Customer")
	or_filters: list[list[object]] = []
	customer_name = cstr(values.get("customer_name") or "").strip()
	mobile_no = cstr(values.get("mobile_no") or "").strip()
	email_id = cstr(values.get("email_id") or "").strip()
	if customer_name:
		or_filters.append(["name", "=", customer_name])
		if "customer_name" in fields:
			or_filters.append(["customer_name", "=", customer_name])
	if mobile_no and "mobile_no" in fields:
		or_filters.append(["mobile_no", "=", mobile_no])
	if email_id and "email_id" in fields:
		or_filters.append(["email_id", "=", email_id])
	if not or_filters:
		return []

	rows = frappe.get_list(
		"Customer",
		filters={"disabled": ["!=", 1]} if "disabled" in fields else {},
		or_filters=or_filters,
		fields=_available_fields("Customer", "name", "customer_name", "customer_group", "territory", "mobile_no", "email_id"),
		limit_page_length=5,
	)
	duplicates: list[dict[str, object]] = []
	for row in rows:
		label = row.get("customer_name") or row.get("name")
		meta = " · ".join(
			[
				cstr(row.get("customer_group") or "").strip(),
				cstr(row.get("territory") or "").strip(),
				cstr(row.get("mobile_no") or row.get("email_id") or "").strip(),
			]
		)
		duplicates.append({"name": row.get("name"), "label": label, "meta": meta})
	return duplicates


def _customer_detail_state_payload(*, title: str, detail: str, scope: dict[str, object]) -> dict[str, object]:
	return {
		"page": {"title": "Customer Detail"},
		"summary": {
			"kicker": "Customer Detail",
			"title": title,
			"subtitle": detail,
			"facts": _summary_facts(0, scope, "Customer detail requires a visible customer account."),
		},
		"controls": {
			"scopeChips": _scope_chips(scope),
			"actions": [{"key": "back_to_customers", "label": "Back to Customers", "category": "navigation"}],
		},
		"results": {
			"title": "Customer state",
			"state": {
				"kind": "error",
				"title": title,
				"detail": detail,
			},
		},
		"action_targets": {
			"back_to_customers": {"kind": "worklist", "queue_key": "customer_directory"},
		},
	}


def _fetch_customer_detail_record(*, base_filters: dict[str, object], customer_name: str) -> dict[str, object] | None:
	customer_filters = dict(base_filters or {})
	customer_filters["name"] = customer_name
	rows = frappe.get_all(
		"Customer",
		filters=customer_filters,
		fields=_available_fields("Customer", "name", "customer_name", "territory", "customer_group", "mobile_no", "email_id", "customer_primary_contact"),
		limit_page_length=1,
	)
	if not rows:
		return None

	row = dict(rows[0])
	contact_values = _customer_primary_contact_values(row)
	if contact_values.get("mobile_no"):
		row["mobile_no"] = contact_values.get("mobile_no")
	if contact_values.get("email_id"):
		row["email_id"] = contact_values.get("email_id")
	name = row.get("name")
	outstanding = _customer_outstanding_map([name]).get(name, 0) if name else 0
	credit_data = _customer_credit_map([name]).get(name, {}) if name else {}
	credit_limit = flt(credit_data.get("credit_limit") or 0)
	bypass_credit_limit_check = cint(credit_data.get("bypass_credit_limit_check") or 0)
	posture_code, posture_label, posture_meta, posture_tone = _customer_credit_posture(
		outstanding=flt(outstanding or 0),
		credit_limit=credit_limit,
		bypass_credit_limit_check=bypass_credit_limit_check,
	)
	row.update(
		{
			"outstanding_amount": flt(outstanding or 0),
			"credit_limit": credit_limit,
			"bypass_credit_limit_check": bypass_credit_limit_check,
			"credit_posture_code": posture_code,
			"credit_posture_label": posture_label,
			"credit_posture_meta": posture_meta,
			"credit_posture_tone": posture_tone,
		}
	)
	return row


def _customer_detail_recent_rows(customer_name: str | None, *, document_type: str = "") -> tuple[list[dict[str, object]], dict[str, object]]:
	if not customer_name:
		return [], {}

	candidates: list[dict[str, object]] = []
	action_targets: dict[str, object] = {}
	document_filter = cstr(document_type or "").strip()

	def add_rows(doctype: str, date_field: str, value_field: str = "grand_total") -> None:
		if document_filter and doctype != document_filter:
			return
		if not service._can_read(doctype):
			return
		fields = service._fieldnames(doctype)
		if date_field not in fields:
			return

		filters: dict[str, object] | None = None
		if doctype == "Quotation":
			if "quotation_to" in fields and "party_name" in fields:
				filters = {"quotation_to": "Customer", "party_name": customer_name}
			elif "party_name" in fields:
				filters = {"party_name": customer_name}
			elif "customer_name" in fields:
				filters = {"customer_name": customer_name}
		elif "customer" in fields:
			filters = {"customer": customer_name}

		if not filters:
			return
		query_fields = _available_fields(
			doctype,
			"name",
			"customer",
			"party_name",
			"customer_name",
			date_field,
			"status",
			"docstatus",
			value_field,
			"currency",
			"per_delivered",
			"per_billed",
			"outstanding_amount",
		)
		rows = frappe.get_all(
			doctype,
			filters=filters,
			fields=query_fields,
			order_by=_preferred_order_by(doctype, [f"{date_field} desc", "modified desc"]),
			limit_page_length=8,
		)
		for row in rows:
			candidates.append(_customer_activity_candidate(doctype, row, date_field, value_field))

	add_rows("Quotation", "transaction_date")
	add_rows("Sales Order", "transaction_date")
	add_rows("Sales Invoice", "posting_date")

	sorted_candidates = sorted(
		[item for item in candidates if item.get("name")],
		key=lambda item: getdate(item.get("date")) if item.get("date") else getdate("1900-01-01"),
		reverse=True,
	)[:12]

	results: list[dict[str, object]] = []
	for item in sorted_candidates:
		row_key = f"{item.get('doctype')}::{item.get('name')}"
		results.append(
			{
				"key": row_key,
				"document_type": item.get("doctype"),
				"open_state": item.get("open_state"),
				"actions": [{"key": "open_record", "label": "Open"}],
				"cells": {
					"document": {"value": item.get("name"), "meta": item.get("doctype")},
					"date": {"value": _date(item.get("date"))},
					"status": {"value": item.get("status") or "--", "meta": item.get("status_meta") or "", "tone": item.get("status_tone") or ""},
					"value": {"value": _money(item.get("value"), item.get("currency"))},
				},
			}
		)
		action_targets[f"row:{row_key}:open_record"] = {
			"kind": "form",
			"doctype": item.get("doctype"),
			"name": item.get("name"),
		}

	return results, action_targets


def _customer_activity_candidate(doctype: str, row: dict[str, object], date_field: str, value_field: str) -> dict[str, object]:
	status = cstr(row.get("status") or "").strip() or ("Submitted" if cint(row.get("docstatus") or 0) == 1 else "Draft")
	status_meta = ""
	status_tone = ""
	open_state = False
	if doctype == "Sales Order":
		per_delivered = flt(row.get("per_delivered") or 0)
		per_billed = flt(row.get("per_billed") or 0)
		status_meta = f"{cint(per_delivered)}% delivered • {cint(per_billed)}% billed"
		open_state = status not in {"Completed", "Closed", "Cancelled"} or per_delivered < 100 or per_billed < 100
		status_tone = "attention" if open_state else ""
	elif doctype == "Sales Invoice":
		outstanding = flt(row.get("outstanding_amount") or 0)
		status_meta = _money(outstanding, row.get("currency")) if outstanding else "Settled or no outstanding"
		open_state = outstanding > 0
		status_tone = "attention" if outstanding > 0 else ""
	elif doctype == "Quotation":
		open_state = status in {"Draft", "Open"}
		status_tone = "attention" if open_state else ""
	return {
		"doctype": doctype,
		"name": row.get("name"),
		"date": row.get(date_field),
		"status": status,
		"status_meta": status_meta,
		"status_tone": status_tone,
		"value": row.get(value_field),
		"currency": row.get("currency"),
		"open_state": open_state,
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


def _build_follow_up_worklist(scope: dict[str, object], applied_filters: dict[str, object] | None = None) -> dict[str, object]:
	filters, scope_note, assignee_field = service._follow_up_filters(scope)
	native_target = service._follow_up_target(scope)
	filters = _apply_follow_up_route_filters(filters, applied_filters or {})
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


def _as_filter_list(value) -> list[str]:
	if value in (None, ""):
		return []
	if isinstance(value, (list, tuple, set)):
		if len(value) == 2 and cstr(list(value)[0]).strip().lower() in {"in", "=", "!="}:
			operator, entries = list(value)
			if cstr(operator).strip().lower() == "in":
				return [cstr(entry).strip() for entry in (entries or []) if cstr(entry).strip()]
			return [cstr(entries).strip()] if cstr(entries).strip() else []
		return [cstr(entry).strip() for entry in value if cstr(entry).strip()]
	return [entry.strip() for entry in cstr(value).split(",") if entry.strip()]


def _apply_follow_up_route_filters(filters: list[list[object]], applied_filters: dict[str, object]) -> list[list[object]]:
	next_filters = [list(row) for row in filters]
	fields = service._fieldnames("ToDo")
	todo_names = _as_filter_list(applied_filters.get("todo_name") or applied_filters.get("name"))
	reference_names = _as_filter_list(applied_filters.get("reference_name"))
	reference_types = _as_filter_list(applied_filters.get("reference_type"))

	if todo_names:
		next_filters.append(["name", "in", todo_names])
	if reference_names and "reference_name" in fields:
		next_filters.append(["reference_name", "in", reference_names])
	if reference_types and "reference_type" in fields:
		next_filters.append(["reference_type", "in", reference_types])

	return next_filters


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
	action_targets = {}
	state_action = None
	if native_target:
		action_targets["open_native_list"] = native_target
		state_action = {"key": "open_native_list", "label": "Open Native List"}

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
				"action": state_action,
			},
		},
		"action_targets": action_targets,
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


def _fetch_quotation_directory_rows(
	*,
	today,
	context: dict[str, object],
	scope: dict[str, object],
	view: str,
	status: str,
	date_start: str,
	date_end: str,
	keyword: str,
) -> tuple[list[dict[str, object]], str]:
	filters, scope_note = _quotation_directory_filters(
		today=today,
		context=context,
		scope=scope,
		view=view,
		status=status,
		date_start=date_start,
		date_end=date_end,
	)
	order_by = _preferred_order_by(
		"Quotation",
		["valid_till asc, modified desc"] if view in {"expiring_soon", "expired"} else ["modified desc", "valid_till asc"],
	)
	or_filters = _quotation_keyword_filters(keyword)
	rows = frappe.get_list(
		"Quotation",
		fields=["name", *[
			field for field in _available_fields(
				"Quotation",
				"party_name",
				"customer_name",
				"quotation_to",
				"valid_till",
				"status",
				"workflow_state",
				"grand_total",
				"currency",
			)
			if field != "name"
		]],
		filters=filters,
		or_filters=or_filters or None,
		order_by=order_by,
		limit_page_length=ROW_LIMIT,
	)
	return rows, scope_note


def _fetch_sales_order_directory_rows(
	*,
	today,
	context: dict[str, object],
	scope: dict[str, object],
	view: str,
	status: str,
	date_start: str,
	date_end: str,
	keyword: str,
) -> tuple[list[dict[str, object]], str]:
	filters, scope_note = _sales_order_directory_filters(
		today=today,
		context=context,
		scope=scope,
		view=view,
		status=status,
		date_start=date_start,
		date_end=date_end,
	)
	order_by = _preferred_order_by(
		"Sales Order",
		["delivery_date asc, modified desc"] if view in {"due_soon", "partially_delivered"} else ["modified desc", "delivery_date asc"],
	)
	or_filters = _sales_order_keyword_filters(keyword)
	rows = frappe.get_list(
		"Sales Order",
		fields=["name", *[
			field for field in _available_fields(
				"Sales Order",
				"customer",
				"delivery_date",
				"status",
				"workflow_state",
				"per_delivered",
				"per_billed",
				"grand_total",
				"currency",
			)
			if field != "name"
		]],
		filters=filters,
		or_filters=or_filters or None,
		order_by=order_by,
		limit_page_length=ROW_LIMIT,
	)
	return rows, scope_note


def _quotation_directory_filters(
	*,
	today,
	context: dict[str, object],
	scope: dict[str, object],
	view: str,
	status: str,
	date_start: str,
	date_end: str,
) -> tuple[list[list[object]], str]:
	normalized_view = cstr(view).strip() or "all_visible"
	if normalized_view == "waiting_action":
		filters, scope_note = service._quotation_action_filters(scope)
	elif normalized_view == "awaiting_approval":
		filters, scope_note = service._quotation_approval_filters(scope)
	elif normalized_view == "expiring_soon":
		filters, scope_note = service._quotation_expiring_filters(today, scope)
	elif normalized_view == "expired":
		filters, scope_note = service._apply_scope_filters(
			"Quotation",
			[
				["docstatus", "!=", 2],
				["valid_till", "<", today],
			],
			scope,
		)
		scope_note = f"{scope_note} Expired quotations only."
	else:
		filters, scope_note = _directory_browse_scope_filters("Quotation", context, scope)

	if status and "status" in service._fieldnames("Quotation"):
		filters.append(["status", "=", status])
	_append_directory_period_filters(
		filters,
		doctype="Quotation",
		candidates=("transaction_date", "valid_till"),
		date_start=date_start,
		date_end=date_end,
	)
	return filters, scope_note


def _sales_order_directory_filters(
	*,
	today,
	context: dict[str, object],
	scope: dict[str, object],
	view: str,
	status: str,
	date_start: str,
	date_end: str,
) -> tuple[list[list[object]], str]:
	normalized_view = cstr(view).strip() or "all_visible"
	if normalized_view == "open_orders":
		filters, scope_note = service._sales_order_active_filters(scope)
	elif normalized_view == "pending_fulfillment":
		filters, scope_note = service._sales_order_active_filters(scope, exclude_pending_workflow=True)
	elif normalized_view == "awaiting_approval":
		filters, scope_note = service._sales_order_approval_filters(scope)
	elif normalized_view == "due_soon":
		filters, scope_note = service._orders_due_soon_filters(today, scope)
	elif normalized_view == "partially_delivered":
		filters, scope_note = service._partially_delivered_sales_order_filters(scope)
	else:
		filters, scope_note = _directory_browse_scope_filters("Sales Order", context, scope)

	if status and "status" in service._fieldnames("Sales Order"):
		filters.append(["status", "=", status])
	_append_directory_period_filters(
		filters,
		doctype="Sales Order",
		candidates=("transaction_date", "delivery_date"),
		date_start=date_start,
		date_end=date_end,
	)
	return filters, scope_note


def _append_directory_period_filters(
	filters: list[list[object]],
	*,
	doctype: str,
	candidates: tuple[str, ...],
	date_start: str,
	date_end: str,
) -> None:
	date_field = _directory_period_field(doctype, *candidates)
	start_value = _parse_filter_date(date_start)
	end_value = _parse_filter_date(date_end)
	if date_field and start_value:
		filters.append([date_field, ">=", start_value])
	if date_field and end_value:
		filters.append([date_field, "<=", end_value])


def _directory_period_field(doctype: str, *candidates: str) -> str | None:
	fields = service._fieldnames(doctype)
	for fieldname in candidates:
		if fieldname in fields:
			return fieldname
	return None


def _parse_filter_date(value: str) -> object | None:
	needle = cstr(value).strip()
	if not needle:
		return None
	try:
		return getdate(needle)
	except Exception:
		return None


def _directory_browse_scope_filters(
	doctype: str,
	context: dict[str, object],
	scope: dict[str, object],
) -> tuple[list[list[object]], str]:
	role_variant = cstr(context.get("role_variant")).strip()
	fields = service._fieldnames(doctype)
	branch_name = scope.get("branch_name")
	owner_user_ids = list(scope.get("owner_user_ids") or [])
	scoped_filters: list[list[object]] = []

	if role_variant in {"sales_manager", "executive_review"}:
		return scoped_filters, "Browse view uses broader visible document scope for manager-style review."

	if owner_user_ids and "owner" in fields and doctype in {"Quotation", "Sales Order", "Opportunity", "Lead"}:
		scoped_filters.append(["owner", "in", owner_user_ids])

	if branch_name and scope.get("apply_branch_filter") and "branch" in fields:
		scoped_filters.append(["branch", "=", branch_name])
		if owner_user_ids:
			return scoped_filters, f"Browse view uses current-user and branch scope: {branch_name}."
		return scoped_filters, f"Browse view uses branch scope: {branch_name}."

	if owner_user_ids and doctype in {"Quotation", "Sales Order", "Opportunity", "Lead"}:
		return scoped_filters, "Browse view uses current-user document ownership scope."

	return scoped_filters, "Browse view uses current permission scope."


def _quotation_keyword_filters(keyword: str) -> list[list[object]]:
	needle = cstr(keyword).strip()
	if not needle:
		return []
	like_value = f"%{needle}%"
	fields = service._fieldnames("Quotation")
	filters = [["name", "like", like_value]]
	for fieldname in ("customer_name", "party_name"):
		if fieldname in fields:
			filters.append([fieldname, "like", like_value])
	return filters


def _sales_order_keyword_filters(keyword: str) -> list[list[object]]:
	needle = cstr(keyword).strip()
	if not needle:
		return []
	like_value = f"%{needle}%"
	fields = service._fieldnames("Sales Order")
	filters = [["name", "like", like_value]]
	if "customer" in fields:
		filters.append(["customer", "like", like_value])
	return filters


def _pending_workflow_match(doctype: str, workflow_state: object) -> bool:
	state = cstr(workflow_state).strip()
	if not state:
		return False
	matching_states = {cstr(item).casefold() for item in service._configured_pending_states(doctype)}
	return state.casefold() in matching_states


def _quotation_waiting_action_match(record: dict[str, object]) -> bool:
	status = cstr(record.get("status")).strip()
	return status in {"Draft", "Open"} and not _pending_workflow_match("Quotation", record.get("workflow_state"))


def _quotation_expiring_match(record: dict[str, object], today) -> bool:
	status = cstr(record.get("status")).strip()
	valid_till = record.get("valid_till")
	if status not in {"Draft", "Open"} or not valid_till:
		return False
	try:
		valid_date = getdate(valid_till)
	except Exception:
		return False
	return today <= valid_date <= today + timedelta(days=7)


def _sales_order_active_match(record: dict[str, object]) -> bool:
	status = cstr(record.get("status")).strip()
	return status in set(service.ACTIVE_SALES_ORDER_STATUSES) if hasattr(service, "ACTIVE_SALES_ORDER_STATUSES") else status != ""


def _sales_order_pending_fulfillment_match(record: dict[str, object]) -> bool:
	return _sales_order_active_match(record) and not _pending_workflow_match("Sales Order", record.get("workflow_state"))


def _sales_order_due_soon_match(record: dict[str, object], today) -> bool:
	if not _sales_order_pending_fulfillment_match(record):
		return False
	delivery_date = record.get("delivery_date")
	if not delivery_date:
		return False
	try:
		delivery_value = getdate(delivery_date)
	except Exception:
		return False
	return today <= delivery_value <= today + timedelta(days=3) and flt(record.get("per_delivered") or 0) < 100


def _quotation_validity_meta(record: dict[str, object], today) -> tuple[str, str]:
	valid_till = record.get("valid_till")
	if not valid_till:
		return "", ""
	try:
		valid_date = getdate(valid_till)
	except Exception:
		return "", ""
	if valid_date < today:
		return "Expired", "blocker"
	if valid_date == today:
		return "Due today", "attention"
	if valid_date <= today + timedelta(days=7):
		days_left = (valid_date - today).days
		return f"{days_left} day{'s' if days_left != 1 else ''} left", "attention"
	return "", ""


def _sales_order_delivery_meta(record: dict[str, object], today) -> tuple[str, str]:
	delivery_date = record.get("delivery_date")
	if not delivery_date:
		return "", ""
	try:
		delivery_value = getdate(delivery_date)
	except Exception:
		return "", ""
	if delivery_value < today and flt(record.get("per_delivered") or 0) < 100:
		return "Past due", "blocker"
	if delivery_value == today and flt(record.get("per_delivered") or 0) < 100:
		return "Due today", "attention"
	if delivery_value <= today + timedelta(days=3) and flt(record.get("per_delivered") or 0) < 100:
		return "Due soon", "attention"
	return "", ""


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


def _quotation_directory_row(record: dict[str, object], today) -> dict[str, object]:
	customer_label = record.get("customer_name") or record.get("party_name") or "--"
	workflow_state = cstr(record.get("workflow_state")).strip()
	status = cstr(record.get("status")).strip() or "--"
	validity_meta, validity_tone = _quotation_validity_meta(record, today)
	commercial_value = workflow_state if _pending_workflow_match("Quotation", workflow_state) else status
	commercial_meta = status if workflow_state and workflow_state != status else ""
	return {
		"cells": {
			"quotation": {"value": record.get("name"), "meta": customer_label},
			"valid_till": {"value": _date(record.get("valid_till")), "meta": validity_meta, "tone": validity_tone},
			"commercial_state": {"value": commercial_value, "meta": commercial_meta, "tone": "pending" if workflow_state and workflow_state == commercial_value else ""},
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


def _sales_order_directory_row(record: dict[str, object], today) -> dict[str, object]:
	workflow_state = cstr(record.get("workflow_state")).strip()
	status = cstr(record.get("status")).strip() or "--"
	delivery_meta, delivery_tone = _sales_order_delivery_meta(record, today)
	commercial_value = workflow_state if _pending_workflow_match("Sales Order", workflow_state) else status
	commercial_meta = f"{cint(flt(record.get('per_delivered') or 0))}% delivered • {cint(flt(record.get('per_billed') or 0))}% billed"
	return {
		"cells": {
			"sales_order": {"value": record.get("name"), "meta": record.get("customer") or "--"},
			"delivery": {"value": _date(record.get("delivery_date")), "meta": delivery_meta, "tone": delivery_tone},
			"commercial_state": {"value": commercial_value, "meta": commercial_meta, "tone": "pending" if workflow_state and workflow_state == commercial_value else ""},
			"total": {"value": _money(record.get("grand_total"), record.get("currency"))},
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


def _normalize_filters(value) -> dict[str, object]:
	if not value:
		return {}
	if isinstance(value, str):
		try:
			value = json.loads(value)
		except Exception:
			return {}
	if not isinstance(value, dict):
		return {}
	normalized: dict[str, object] = {}
	for key, item in value.items():
		if item in (None, ""):
			continue
		if isinstance(item, (list, tuple, set)):
			normalized[str(key)] = list(item)
			continue
		if isinstance(item, dict):
			normalized[str(key)] = dict(item)
			continue
		text = str(item).strip()
		if text:
			normalized[str(key)] = text
	return normalized


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
