from __future__ import annotations

from typing import Callable

import frappe
from frappe import _
from frappe.utils import cint, flt, fmt_money, formatdate, getdate, nowdate

from . import service


ROW_LIMIT = 50


@frappe.whitelist()
def get_sales_console_worklist_context(queue_key: str | None = None) -> dict[str, object]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	normalized_key = _normalize_queue_key(queue_key)
	context = service._build_context()
	scope = service._build_scope(context)
	today = getdate(nowdate())
	builder = _queue_registry(today, scope).get(normalized_key)
	if not builder:
		return _route_unavailable_payload(normalized_key, scope)
	return builder()


def _queue_registry(today, scope: dict[str, object]) -> dict[str, Callable[[], dict[str, object]]]:
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
			"meta": f"{len(results_rows)} visible · latest {ROW_LIMIT}",
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


def _date(value) -> str:
	if not value:
		return "--"
	return formatdate(value)


def _money(amount, currency) -> str:
	if amount in (None, ""):
		return "--"
	return fmt_money(amount, currency=currency)
