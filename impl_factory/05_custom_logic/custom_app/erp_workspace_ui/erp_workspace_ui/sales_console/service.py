from __future__ import annotations

import json
import re
import uuid
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import get_fullname, getdate, now_datetime, nowdate

try:
	from ai_assistant_ui.qwen_chat.artifact_narrative import (
		build_artifact_narrative_context,
		narrate_governed_artifact,
	)
except Exception:  # pragma: no cover - workspace remains usable without AI app/runtime
	build_artifact_narrative_context = None
	narrate_governed_artifact = None


TERMINAL_SALES_ORDER_STATUSES = ("Completed", "Closed", "Cancelled")
ACTIVE_SALES_ORDER_STATUSES = (
	"To Deliver",
	"To Bill",
	"To Deliver and Bill",
	"Partly Delivered",
	"Partly Billed",
	"Partly Delivered and Billed",
	"On Hold",
)
OUTSTANDING_SALES_INVOICE_STATUSES = (
	"Unpaid",
	"Partly Paid",
	"Overdue",
	"Unpaid and Discounted",
	"Partly Paid and Discounted",
	"Overdue and Discounted",
)
EXPLICIT_PENDING_WORKFLOW_STATES = {
	"Quotation": (
		"Pending Sales Approval",
		"Pending Executive Approval",
		"Pending Supervisor Approval",
		"Pending Manager Review",
		"Pending Approval",
		"Awaiting Approval",
		"Pending GM Review",
		"Pending General Manager Approval",
		"Escalated",
	),
	"Sales Order": (
		"Pending Sales Approval",
		"Pending Executive Approval",
		"Pending Supervisor Approval",
		"Pending Finance Review",
		"Pending Credit Review",
		"Held",
		"On Hold",
		"Pending GM Review",
		"Escalated",
	),
}
INQUIRY_DOCUMENT_ORDER = ("Quotation", "Sales Order", "Sales Invoice", "Delivery Note", "Customer")
INQUIRY_DOCUMENT_HINTS = {
	"Quotation": {"date_field": "transaction_date"},
	"Sales Order": {"date_field": "transaction_date"},
	"Sales Invoice": {"date_field": "posting_date"},
	"Delivery Note": {"date_field": "posting_date"},
	"Customer": {"date_field": "modified"},
}


@frappe.whitelist()
def get_sales_console_bootstrap() -> dict[str, object]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	today = getdate(nowdate())
	context = _build_context()
	scope = _build_scope(context)

	return {
		"context": context,
		"scope": scope,
		"ui_profile": _build_ui_profile(context["role_variant"]),
		"work": _build_work(today, scope),
		"lifecycle": _build_lifecycle(today, scope),
		"blockers": _build_blockers(scope),
		"queues": _build_queues(today, scope),
		"insights": _build_insights(scope),
		"reports_catalog": _build_reports_catalog(context["role_variant"]),
		"navigation": _build_navigation(today, context, scope),
		"fetched_at": str(now_datetime()),
	}


@frappe.whitelist()
def resolve_customer_inquiry(
	query: str,
	doctype: str | None = None,
	name: str | None = None,
) -> dict[str, object]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	needle = (query or "").strip()
	if doctype and name:
		result = _build_customer_inquiry_result(str(doctype).strip(), str(name).strip(), needle or str(name).strip())
		if result.get("state") == "resolved":
			result["match_mode"] = "selected_suggestion"
		return result

	if not needle:
		return {
			"state": "empty",
			"query": "",
			"message": "Enter a customer, quotation, order, invoice, or delivery reference.",
		}

	match = _find_customer_inquiry_match(needle)
	if match.get("state") != "resolved":
		return match

	anchor = match["anchor"]
	result = _build_customer_inquiry_result(anchor["doctype"], anchor["name"], needle)
	if match.get("match_mode"):
		result["match_mode"] = match["match_mode"]
	return result


@frappe.whitelist()
def suggest_customer_inquiry(query: str) -> dict[str, object]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	needle = (query or "").strip()
	if len(needle) < 2:
		return {
			"state": "idle",
			"query": needle,
			"message": "Type at least 2 characters to see matching customers and document IDs.",
			"suggestions": [],
		}

	suggestions = _build_customer_inquiry_suggestions(needle)
	if not suggestions:
		return {
			"state": "empty",
			"query": needle,
			"message": "No visible customers or commercial documents match this entry yet.",
			"suggestions": [],
		}

	return {
		"state": "ready",
		"query": needle,
		"message": f"{len(suggestions)} visible suggestion{'s' if len(suggestions) != 1 else ''} found.",
		"suggestions": suggestions,
	}


@frappe.whitelist()
def generate_customer_inquiry_assist(
	query: str,
	doctype: str | None = None,
	name: str | None = None,
) -> dict[str, object]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	resolved = _resolve_customer_inquiry_payload(query=query, doctype=doctype, name=name)
	if resolved.get("state") != "resolved":
		return {
			"state": resolved.get("state") or "unavailable",
			"query": query,
			"message": resolved.get("message") or "Customer inquiry must resolve to a single visible chain first.",
		}

	fallback = _build_customer_inquiry_assist_fallback(resolved)
	ai_result = _generate_customer_inquiry_assist_via_runtime(resolved, fallback)
	return ai_result or fallback


def _build_context() -> dict[str, object]:
	employee_record = _employee_record()
	branch_name = _resolve_branch(employee_record)
	role_variant = _role_variant()
	return {
		"user_display_name": get_fullname(frappe.session.user) or frappe.session.user,
		"primary_role": _primary_sales_role(role_variant),
		"role_variant": role_variant,
		"employee_name": employee_record.get("name") if employee_record else None,
		"branch_label": branch_name,
		"branch_note": None if branch_name else "not mapped yet for this user",
	}


def _resolve_customer_inquiry_payload(
	*,
	query: str,
	doctype: str | None = None,
	name: str | None = None,
) -> dict[str, object]:
	needle = (query or "").strip()
	if doctype and name:
		return _build_customer_inquiry_result(str(doctype).strip(), str(name).strip(), needle)
	return resolve_customer_inquiry(needle)


def _build_scope(context: dict[str, object]) -> dict[str, object]:
	branch_name = context.get("branch_label")
	role_variant = context.get("role_variant")
	employee_name = context.get("employee_name")

	if role_variant == "sales_manager":
		team_users = _direct_report_users(employee_name)
		scoped_users = sorted({frappe.session.user, *team_users})
		return {
			"branch_name": branch_name,
			"scope_mode": "team_review_scope",
			"scope_label": (
				f"Team review scope across direct reports; branch context: {branch_name}."
				if team_users and branch_name
				else "Team review scope fallback to current user because direct reports are not mapped."
			),
			"apply_branch_filter": False,
			"owner_user_ids": scoped_users,
			"todo_user_ids": scoped_users,
		}

	if role_variant == "key_account_sales":
		return {
			"branch_name": branch_name,
			"scope_mode": "assigned_account_scope",
			"scope_label": "Assigned account and territory execution scope with broader saleable stock visibility where permitted.",
			"apply_branch_filter": False,
			"owner_user_ids": [frappe.session.user],
			"todo_user_ids": [frappe.session.user],
		}

	if role_variant == "showroom_sales":
		return {
			"branch_name": branch_name,
			"scope_mode": "showroom_scope",
			"scope_label": (
				f"Showroom execution scope with branch filter: {branch_name}."
				if branch_name
				else "Showroom execution scope using current user ownership only."
			),
			"apply_branch_filter": bool(branch_name),
			"owner_user_ids": [frappe.session.user],
			"todo_user_ids": [frappe.session.user],
		}

	if role_variant == "executive_review":
		return {
			"branch_name": branch_name,
			"scope_mode": "executive_review_scope",
			"scope_label": "Executive review scope across company-wide sales approvals and exception context.",
			"apply_branch_filter": False,
			"owner_user_ids": [],
			"todo_user_ids": [frappe.session.user],
		}

	if branch_name:
		return {
			"branch_name": branch_name,
			"scope_mode": "branch_and_owner_filtered",
			"scope_label": f"Branch and current-user scope applied where supported: {branch_name}.",
			"apply_branch_filter": True,
			"owner_user_ids": [frappe.session.user],
			"todo_user_ids": [frappe.session.user],
		}

	return {
		"branch_name": None,
		"scope_mode": "permission_scope",
		"scope_label": "Permission scope fallback; no mapped branch detected.",
		"apply_branch_filter": False,
		"owner_user_ids": [frappe.session.user],
		"todo_user_ids": [frappe.session.user],
	}


def _build_ui_profile(role_variant: str) -> dict[str, object]:
	profiles = {
		"sales_manager": {
			"mode_label": "Manager Mode",
			"summary_note": "Prioritize approvals, commercial blockers, and team follow-through.",
			"brief_points": [
				"Start with approval queues and blocked commercial exceptions.",
				"Review customer-facing downstream issues before commitments slip.",
				"Use reports as management review surfaces after active exceptions are under control.",
			],
			"action_order": [
				"new_quotation",
				"new_sales_order",
				"open_customer",
				"new_opportunity",
				"open_item",
			],
			"queue_order": [
				"quotations_waiting_action",
				"sales_orders_pending_fulfillment",
				"expiring_quotations",
				"customer_follow_up_tasks",
			],
			"hidden_actions": [],
			"hidden_insights": [],
			"show_reports": True,
			"section_order": ["approvals", "inquiry", "work", "lifecycle", "reports"],
			"section_notes": {
				"inquiry": "Single-point customer and document lookup for team review",
				"work": "Team work requiring commercial movement and follow-through",
				"lifecycle": "Downstream customer status requiring sales awareness",
				"approvals": "Manager review queue for approvals and exceptions",
				"reports": "Management review and exception follow-up",
			},
		},
		"sales_executive": {
			"mode_label": "Execution Mode",
			"summary_note": "Prioritize daily sales action, customer answers, and truthful order visibility.",
			"brief_points": [
				"Start with active quotations, promised follow-up, and pending fulfillment.",
				"Use lifecycle cards to answer customer delivery or invoice status without menu hunting.",
				"Treat approvals as escalation signals, not the main work surface.",
			],
			"action_order": [
				"new_quotation",
				"new_sales_order",
				"open_customer",
				"new_opportunity",
				"open_item",
			],
			"queue_order": [
				"quotations_waiting_action",
				"customer_follow_up_tasks",
				"expiring_quotations",
				"sales_orders_pending_fulfillment",
			],
			"hidden_actions": [],
			"hidden_insights": [],
			"show_reports": True,
			"section_order": ["inquiry", "work", "lifecycle", "approvals", "reports"],
			"section_notes": {
				"inquiry": "Search once to answer customer questions across the full sales chain",
				"work": "Execution-first commercial queue",
				"lifecycle": "Delivery, invoice, and return visibility for customer response",
				"approvals": "Escalation and approval visibility without dominating the page",
				"reports": "Deep review after daily action queues",
			},
		},
		"key_account_sales": {
			"mode_label": "Account Mode",
			"summary_note": "Prioritize customer continuity, order follow-through, and account-facing visibility.",
			"brief_points": [
				"Open customer context first when preparing for account work.",
				"Track downstream delivery, invoice, and return signals for strategic accounts.",
				"Use reports to support account review, not generic module browsing.",
			],
			"action_order": [
				"open_customer",
				"new_quotation",
				"new_sales_order",
				"open_item",
				"new_opportunity",
			],
			"queue_order": [
				"customer_follow_up_tasks",
				"sales_orders_pending_fulfillment",
				"quotations_waiting_action",
				"expiring_quotations",
			],
			"hidden_actions": [],
			"hidden_insights": [],
			"show_reports": True,
			"section_order": ["inquiry", "work", "lifecycle", "approvals", "reports"],
			"section_notes": {
				"inquiry": "Account-facing inquiry and cross-document customer visibility",
				"work": "Account continuity and follow-through",
				"lifecycle": "Customer-facing execution visibility across the account chain",
				"approvals": "Approval and blocker visibility for strategic commercial exceptions",
				"reports": "Customer and account review surfaces",
			},
		},
		"showroom_sales": {
			"mode_label": "Showroom Mode",
			"summary_note": "Prioritize fast counter execution with simpler navigation and narrower scope.",
			"brief_points": [
				"Use the shortest path to quotation and sales order creation.",
				"Keep item lookup and customer opening close to the top.",
				"Management reports stay de-emphasized in showroom mode.",
			],
			"action_order": [
				"new_quotation",
				"new_sales_order",
				"open_item",
				"open_customer",
			],
			"queue_order": [
				"quotations_waiting_action",
				"sales_orders_pending_fulfillment",
				"customer_follow_up_tasks",
				"expiring_quotations",
			],
			"hidden_actions": ["new_opportunity"],
			"hidden_insights": [],
			"show_reports": False,
			"section_order": ["inquiry", "work", "lifecycle", "approvals", "reports"],
			"section_notes": {
				"inquiry": "Fast lookup for customer, order, and invoice questions at the counter",
				"work": "Fast counter execution and follow-up",
				"lifecycle": "Only the most useful downstream visibility for customer response",
				"approvals": "Keep approval signals visible without slowing counter work",
			},
		},
		"executive_review": {
			"mode_label": "Executive Review Mode",
			"summary_note": "Review escalations, approvals, and commercial exceptions without transaction-heavy execution paths.",
			"brief_points": [
				"Use this console only for sales-related review and escalation visibility.",
				"Prioritize approvals, blocked orders, and exception context over transaction creation.",
				"Use the Executive Console as the primary oversight surface when available.",
			],
			"action_order": [
				"open_customer",
				"open_item",
				"new_quotation",
				"new_sales_order",
				"new_opportunity",
			],
			"queue_order": [
				"sales_orders_pending_fulfillment",
				"quotations_waiting_action",
				"expiring_quotations",
				"customer_follow_up_tasks",
			],
			"hidden_actions": ["new_quotation", "new_sales_order", "new_opportunity"],
			"hidden_insights": [],
			"show_reports": True,
			"section_order": ["approvals", "inquiry", "reports", "work", "lifecycle"],
			"section_notes": {
				"inquiry": "Trace the commercial chain before deciding on escalations or approvals",
				"work": "Review sales-side operational context after escalations are understood",
				"lifecycle": "Downstream context available when needed for approval decisions",
				"approvals": "Executive escalation and commercial exception review",
				"reports": "Management review surfaces",
			},
		},
	}

	return profiles.get(role_variant, profiles["sales_executive"])


def _build_work(today, scope: dict[str, object]) -> dict[str, dict[str, object]]:
	return {
		"quotations_waiting_action": _quotations_waiting_action_metric(scope),
		"expiring_quotations": _expiring_quotation_metric(today, scope),
		"sales_orders_pending_fulfillment": _open_sales_order_metric_with_options(
			scope,
			exclude_pending_workflow=True,
		),
		"customer_follow_up_tasks": _customer_follow_up_metric(scope),
	}


def _build_lifecycle(today, scope: dict[str, object]) -> dict[str, dict[str, object]]:
	return {
		"orders_due_soon": _orders_due_soon_metric(today, scope),
		"partially_delivered_orders": _partially_delivered_orders_metric(scope),
		"invoices_outstanding": _invoices_outstanding_metric(scope),
		"sales_returns_in_progress": _sales_returns_in_progress_metric(today, scope),
	}


def _build_blockers(scope: dict[str, object]) -> dict[str, dict[str, object]]:
	return {
		"orders_blocked_by_approval": _workflow_pending_metric("Sales Order", scope),
		"quotations_awaiting_approval": _workflow_pending_metric("Quotation", scope),
	}


def _build_queues(today, scope: dict[str, object]) -> dict[str, dict[str, object]]:
	return {
		**_build_work(today, scope),
		**_build_blockers(scope),
	}


def _build_insights(scope: dict[str, object]) -> dict[str, dict[str, object]]:
	return {
		"awaiting_approval": _combined_approval_metric(scope),
		"open_orders": _open_sales_order_metric(
			scope,
			note="Live open order count within current user and branch scope where supported.",
		),
	}


def _build_navigation(today, context: dict[str, object], scope: dict[str, object]) -> dict[str, dict[str, object]]:
	report_targets = {}
	for report_card in _build_reports_catalog(context.get("role_variant")):
		key = report_card.get("key")
		report_name = report_card.get("report_name")
		if key and report_name:
			report_targets[key] = _report_target(report_name)

	return {
		"actions": {
			"new_opportunity": {"kind": "new_doc", "doctype": "Opportunity"},
			"new_quotation": {"kind": "new_doc", "doctype": "Quotation"},
			"new_sales_order": {"kind": "new_doc", "doctype": "Sales Order"},
			"open_customer": _customer_list_target(context, scope),
			"open_item": _item_list_target(),
		},
		"insights": {
			"awaiting_approval": _approval_review_target(scope),
			"open_orders": _open_sales_order_target(scope),
		},
		"work": {
			"sales_orders_pending_fulfillment": _pending_fulfillment_target(scope),
			"quotations_waiting_action": _actionable_quotation_target(scope),
			"expiring_quotations": _expiring_quotation_target(today, scope),
			"customer_follow_up_tasks": _follow_up_target(scope),
		},
		"lifecycle": {
			"orders_due_soon": _orders_due_soon_target(today, scope),
			"partially_delivered_orders": _partially_delivered_orders_target(scope),
			"invoices_outstanding": _invoices_outstanding_target(scope),
			"sales_returns_in_progress": _sales_returns_target(today, scope),
		},
		"blockers": {
			"orders_blocked_by_approval": _blocked_sales_order_target(scope),
			"quotations_awaiting_approval": _quotation_approval_target(scope),
		},
		"queues": {
			"orders_blocked_by_approval": _blocked_sales_order_target(scope),
			"sales_orders_pending_fulfillment": _pending_fulfillment_target(scope),
			"quotations_waiting_action": _actionable_quotation_target(scope),
			"expiring_quotations": _expiring_quotation_target(today, scope),
			"customer_follow_up_tasks": _follow_up_target(scope),
		},
		"reports": report_targets,
	}


def _quotations_waiting_action_metric(scope: dict[str, object]) -> dict[str, object]:
	if not _can_read("Quotation"):
		return _access_metric("Quotation")

	fields = _fieldnames("Quotation")
	if "status" not in fields:
		return _unavailable_metric("Quotation status field is not available in this site.")

	filters, scope_note = _quotation_action_filters(scope)
	value = _count_records("Quotation", filters)
	return _live_metric(
		value,
		f"Live quotation count for actionable draft/open sales work. {scope_note}",
	)


def _expiring_quotation_metric(today, scope: dict[str, object]) -> dict[str, object]:
	if not _can_read("Quotation"):
		return _access_metric("Quotation")

	fields = _fieldnames("Quotation")
	if "status" not in fields or "valid_till" not in fields:
		return _unavailable_metric("Expiry tracking requires Quotation status and valid_till fields.")

	filters, scope_note = _apply_scope_filters(
		"Quotation",
		[
			["docstatus", "!=", 2],
			["status", "=", "Open"],
			["valid_till", ">=", today],
			["valid_till", "<=", today + timedelta(days=7)],
		],
		scope,
	)
	value = _count_records("Quotation", filters)
	return _live_metric(value, f"Live count of open quotations expiring within seven days. {scope_note}")


def _open_sales_order_metric(scope: dict[str, object], note: str | None = None) -> dict[str, object]:
	return _open_sales_order_metric_with_options(scope, note=note, exclude_pending_workflow=False)


def _open_sales_order_metric_with_options(
	scope: dict[str, object],
	note: str | None = None,
	exclude_pending_workflow: bool = False,
) -> dict[str, object]:
	if not _can_read("Sales Order"):
		return _access_metric("Sales Order")

	filters, scope_note = _sales_order_active_filters(
		scope,
		exclude_pending_workflow=exclude_pending_workflow,
	)
	value = _count_records("Sales Order", filters)
	base_note = note or (
		"Live sales order count for approved active operational statuses."
		if exclude_pending_workflow
		else "Live sales order count for active operational statuses."
	)
	return _live_metric(value, f"{base_note} {scope_note}")


def _workflow_pending_metric(doctype: str, scope: dict[str, object]) -> dict[str, object]:
	if not _can_read(doctype):
		return _access_metric(doctype)

	if "workflow_state" not in _fieldnames(doctype):
		return _unavailable_metric(f"{doctype} does not expose workflow_state on this site.")

	matching_states = _configured_pending_states(doctype)
	if not matching_states:
		return _unavailable_metric(
			f"No configured approval workflow states are currently visible for {doctype}."
		)

	filters, scope_note = _apply_scope_filters(
		doctype,
		[["workflow_state", "in", matching_states]],
		scope,
	)
	try:
		value = _count_records(doctype, filters)
	except (frappe.PermissionError, frappe.DataError):
		return _unavailable_metric(f"{doctype} workflow approval fields are not readable in the current scope.")
	return _live_metric(
		value,
		f"Live workflow count using configured approval states: {', '.join(sorted(matching_states))}. {scope_note}",
	)


def _combined_approval_metric(scope: dict[str, object]) -> dict[str, object]:
	quotation_metric = _workflow_pending_metric("Quotation", scope)
	sales_order_metric = _workflow_pending_metric("Sales Order", scope)

	live_metrics = [
		("Quotation", quotation_metric),
		("Sales Order", sales_order_metric),
	]
	live_total = sum(
		int(metric.get("value") or 0)
		for _doctype, metric in live_metrics
		if metric.get("state") == "live"
	)
	live_sources = [doctype for doctype, metric in live_metrics if metric.get("state") == "live"]
	limited_sources = [
		f"{doctype}: {metric.get('note')}"
		for doctype, metric in live_metrics
		if metric.get("state") != "live" and metric.get("note")
	]

	if live_sources:
		note = f"Live approval visibility across {', '.join(live_sources)}."
		if limited_sources:
			note = f"{note} {' '.join(limited_sources)}"
		return _live_metric(live_total, note)

	if any(metric.get("state") == "restricted" for _doctype, metric in live_metrics):
		return {
			"state": "restricted",
			"value": None,
			"note": "Approval visibility is outside current review scope for one or more commercial documents.",
		}

	return _unavailable_metric(
		"Approval workflow states are not available for Quotation or Sales Order on this site."
	)


def _customer_follow_up_metric(scope: dict[str, object], note: str | None = None) -> dict[str, object]:
	if not _can_read("ToDo"):
		return _access_metric("ToDo")

	filters, scope_note, assignee_field = _follow_up_filters(scope)
	if not assignee_field:
		return _unavailable_metric("Current ToDo assignment field is not available for follow-up counting.")

	value = _count_records("ToDo", filters)
	return _live_metric(
		value,
		f"{note or 'Live follow-up task count for the current role scope.'} {scope_note}",
	)


def _partially_delivered_orders_metric(scope: dict[str, object]) -> dict[str, object]:
	if not _can_read("Sales Order"):
		return _access_metric("Sales Order")

	fields = _fieldnames("Sales Order")
	if "per_delivered" not in fields:
		return _unavailable_metric("Sales Order delivery progress fields are not available on this site.")

	filters, scope_note = _partially_delivered_sales_order_filters(scope)
	value = _count_records("Sales Order", filters)
	return _live_metric(
		value,
		f"Live count of submitted sales orders that are partially delivered and still operationally active. {scope_note}",
	)


def _orders_due_soon_metric(today, scope: dict[str, object]) -> dict[str, object]:
	if not _can_read("Sales Order"):
		return _access_metric("Sales Order")

	fields = _fieldnames("Sales Order")
	if "delivery_date" not in fields:
		return _unavailable_metric("Sales Order delivery_date is not available on this site.")

	filters, scope_note = _orders_due_soon_filters(today, scope)
	value = _count_records("Sales Order", filters)
	return _live_metric(
		value,
		f"Live count of active sales orders with delivery commitments due within the next three days. {scope_note}",
	)


def _invoices_outstanding_metric(scope: dict[str, object]) -> dict[str, object]:
	if not _can_read("Sales Invoice"):
		return _access_metric("Sales Invoice")

	fields = _fieldnames("Sales Invoice")
	if "status" not in fields:
		return _unavailable_metric("Sales Invoice status is not available on this site.")

	filters, scope_note = _invoice_outstanding_filters(scope)
	value = _count_records("Sales Invoice", filters)
	return _live_metric(
		value,
		f"Live count of submitted customer invoices that still require payment or settlement follow-up. {scope_note}",
	)


def _sales_returns_in_progress_metric(today, scope: dict[str, object]) -> dict[str, object]:
	if _can_read("Sales Invoice"):
		filters, scope_note = _sales_return_filters("Sales Invoice", today, scope)
		value = _count_records("Sales Invoice", filters)
		return _live_metric(
			value,
			f"Live count of recent customer return or credit-note records visible through Sales Invoice. {scope_note}",
		)

	if _can_read("Delivery Note"):
		filters, scope_note = _sales_return_filters("Delivery Note", today, scope)
		value = _count_records("Delivery Note", filters)
		return _live_metric(
			value,
			f"Live count of recent sales-return delivery records visible through Delivery Note. {scope_note}",
		)

	if _doctype_exists("Sales Invoice"):
		return _access_metric("Sales Invoice")

	return _access_metric("Delivery Note")


def _customer_list_target(context: dict[str, object], scope: dict[str, object]) -> dict[str, object]:
	filters = {"disabled": ["!=", 1]}
	role_variant = context.get("role_variant")
	fields = _fieldnames("Customer")
	owner_user_ids = list(scope.get("owner_user_ids") or [])
	if role_variant in {"sales_executive", "key_account_sales", "showroom_sales"} and owner_user_ids and "owner" in fields:
		filters["owner"] = ["in", owner_user_ids]

	return {
		"kind": "list",
		"doctype": "Customer",
		"filters": filters,
	}


def _item_list_target() -> dict[str, object]:
	filters = {}
	fields = _fieldnames("Item")
	if "disabled" in fields:
		filters["disabled"] = ["!=", 1]
	if "is_sales_item" in fields:
		filters["is_sales_item"] = 1
	return {"kind": "list", "doctype": "Item", "filters": filters}


def _quotation_approval_target(scope: dict[str, object]) -> dict[str, object]:
	if "workflow_state" not in _fieldnames("Quotation"):
		return {
			"kind": "list",
			"doctype": "Quotation",
			"filters": _route_filter_options(_quotation_action_filters(scope)[0]),
			"notice": "Quotation approval states are not exposed on this site. Opening actionable quotations instead.",
		}

	matching_states = _configured_pending_states("Quotation")
	if not matching_states:
		return {
			"kind": "list",
			"doctype": "Quotation",
			"filters": _route_filter_options(_quotation_action_filters(scope)[0]),
			"notice": "No configured quotation approval states are visible on this site. Opening actionable quotations instead.",
		}

	filters, _scope_note = _apply_scope_filters(
		"Quotation",
		[["workflow_state", "in", matching_states]],
		scope,
	)
	return {"kind": "list", "doctype": "Quotation", "filters": _route_filter_options(filters)}


def _approval_review_target(scope: dict[str, object]) -> dict[str, object]:
	sales_order_metric = _workflow_pending_metric("Sales Order", scope)
	if sales_order_metric.get("state") == "live" and int(sales_order_metric.get("value") or 0) > 0:
		return _blocked_sales_order_target(scope)

	quotation_metric = _workflow_pending_metric("Quotation", scope)
	if quotation_metric.get("state") == "live" and int(quotation_metric.get("value") or 0) > 0:
		return _quotation_approval_target(scope)

	if sales_order_metric.get("state") == "live":
		return _blocked_sales_order_target(scope)

	return _quotation_approval_target(scope)


def _open_sales_order_target(scope: dict[str, object]) -> dict[str, object]:
	filters, _scope_note = _sales_order_active_filters(scope)
	return {"kind": "list", "doctype": "Sales Order", "filters": _route_filter_options(filters)}


def _blocked_sales_order_target(scope: dict[str, object]) -> dict[str, object]:
	if "workflow_state" not in _fieldnames("Sales Order"):
		filters, _scope_note = _sales_order_active_filters(scope)
		return {
			"kind": "list",
			"doctype": "Sales Order",
			"filters": _route_filter_options(filters),
			"notice": "Sales Order workflow_state is not exposed on this site. Opening active sales orders instead.",
		}

	matching_states = _configured_pending_states("Sales Order")
	if not matching_states:
		filters, _scope_note = _sales_order_active_filters(scope)
		return {
			"kind": "list",
			"doctype": "Sales Order",
			"filters": _route_filter_options(filters),
			"notice": "No configured blocked-order workflow states are visible on this site. Opening active sales orders instead.",
		}

	filters, _scope_note = _apply_scope_filters(
		"Sales Order",
		[["workflow_state", "in", matching_states]],
		scope,
	)
	return {"kind": "list", "doctype": "Sales Order", "filters": _route_filter_options(filters)}


def _pending_fulfillment_target(scope: dict[str, object]) -> dict[str, object]:
	filters, _scope_note = _sales_order_active_filters(scope, exclude_pending_workflow=True)
	return {"kind": "list", "doctype": "Sales Order", "filters": _route_filter_options(filters)}


def _actionable_quotation_target(scope: dict[str, object]) -> dict[str, object]:
	filters, _scope_note = _quotation_action_filters(scope)
	return {"kind": "list", "doctype": "Quotation", "filters": _route_filter_options(filters)}


def _expiring_quotation_target(today, scope: dict[str, object]) -> dict[str, object]:
	filters, _scope_note = _quotation_expiring_filters(today, scope)
	return {"kind": "list", "doctype": "Quotation", "filters": _route_filter_options(filters)}


def _follow_up_target(scope: dict[str, object]) -> dict[str, object]:
	filters, _scope_note, assignee_field = _follow_up_filters(scope)
	target = {
		"kind": "list",
		"doctype": "ToDo",
		"filters": _route_filter_options(filters),
	}
	if not assignee_field:
		target["notice"] = "Task assignment fields are not available on this site. Opening the general ToDo list instead."
		target["filters"] = {}
	return target


def _partially_delivered_orders_target(scope: dict[str, object]) -> dict[str, object]:
	filters, _scope_note = _partially_delivered_sales_order_filters(scope)
	return {"kind": "list", "doctype": "Sales Order", "filters": _route_filter_options(filters)}


def _orders_due_soon_target(today, scope: dict[str, object]) -> dict[str, object]:
	filters, _scope_note = _orders_due_soon_filters(today, scope)
	return {"kind": "list", "doctype": "Sales Order", "filters": _route_filter_options(filters)}


def _invoices_outstanding_target(scope: dict[str, object]) -> dict[str, object]:
	filters, _scope_note = _invoice_outstanding_filters(scope)
	return {"kind": "list", "doctype": "Sales Invoice", "filters": _route_filter_options(filters)}


def _sales_returns_target(today, scope: dict[str, object]) -> dict[str, object]:
	if _can_read("Sales Invoice"):
		filters, _scope_note = _sales_return_filters("Sales Invoice", today, scope)
		return {"kind": "list", "doctype": "Sales Invoice", "filters": _route_filter_options(filters)}

	if _can_read("Delivery Note"):
		filters, _scope_note = _sales_return_filters("Delivery Note", today, scope)
		return {"kind": "list", "doctype": "Delivery Note", "filters": _route_filter_options(filters)}

	return {"kind": "list", "doctype": "Delivery Note", "filters": {}}


def _report_target(report_name: str, filters: dict[str, object] | None = None) -> dict[str, object]:
	target = {"kind": "report", "report_name": report_name}
	if filters:
		target["filters"] = filters
	return target


def _build_reports_catalog(role_variant: str | None) -> list[dict[str, object]]:
	role_map = {
		"sales_executive": [
			("quotation_trends", "Quotation Trends", "Quotation Trends", "Review quotation movement and expiring commercial momentum", "quotation"),
			("sales_order_analysis", "Sales Order Analysis", "Sales Order Analysis", "Review order execution quality and operational follow-through", "order"),
			("payment_terms_status_sales_order", "Payment Terms Status for Sales Order", "Payment Terms Status", "Check payment schedule exposure without leaving sales context", "chart"),
			("item_wise_sales_history", "Item-wise Sales History", "Item-wise Sales History", "Check product-level sales history when speaking with customers", "item"),
		],
		"key_account_sales": [
			("sales_order_analysis", "Sales Order Analysis", "Sales Order Analysis", "Review account order execution and commercial follow-through", "order"),
			("quotation_trends", "Quotation Trends", "Quotation Trends", "Review quotation behavior and account conversion direction", "quotation"),
			("item_wise_sales_history", "Item-wise Sales History", "Item-wise Sales History", "Check customer-facing item history for account follow-up", "item"),
			("payment_terms_status_sales_order", "Payment Terms Status for Sales Order", "Payment Terms Status", "Review sales-order payment schedule exposure", "chart"),
		],
		"showroom_sales": [
			("sales_order_analysis", "Sales Order Analysis", "Sales Order Analysis", "Keep order review simple and operationally clear", "order"),
			("quotation_trends", "Quotation Trends", "Quotation Trends", "Review quotation movement without a heavy management surface", "quotation"),
			("item_wise_sales_history", "Item-wise Sales History", "Item-wise Sales History", "Check sales history during item and customer discussion", "item"),
		],
		"sales_manager": [
			("sales_analytics", "Sales Analytics", "Sales Analytics", "Management and team performance review", "chart"),
			("sales_order_analysis", "Sales Order Analysis", "Sales Order Analysis", "Review operational order execution and exception patterns", "order"),
			("quotation_trends", "Quotation Trends", "Quotation Trends", "Review quotation flow, conversion direction, and aging", "quotation"),
			("lost_quotations", "Lost Quotations", "Lost Quotations", "Review commercial loss patterns and follow-up quality", "quotation"),
			("payment_terms_status_sales_order", "Payment Terms Status for Sales Order", "Payment Terms Status", "Check sales-order payment schedule exposure", "chart"),
			("item_wise_sales_history", "Item-wise Sales History", "Item-wise Sales History", "Item-level commercial history for deeper review", "item"),
		],
		"executive_review": [
			("sales_analytics", "Sales Analytics", "Sales Analytics", "High-level performance review across sales execution", "chart"),
			("sales_order_trends", "Sales Order Trends", "Sales Order Trends", "Review directional order movement over time", "order"),
			("lost_quotations", "Lost Quotations", "Lost Quotations", "Review lost business patterns before approving major exceptions", "quotation"),
			("payment_terms_status_sales_order", "Payment Terms Status for Sales Order", "Payment Terms Status", "Review downstream payment exposure attached to sales orders", "chart"),
		],
	}

	selected = role_map.get(role_variant or "", role_map["sales_executive"])
	catalog = []
	for key, report_name, title, meta, icon in selected:
		if not _report_exists(report_name):
			continue
		catalog.append({
			"key": key,
			"report_name": report_name,
			"title": title,
			"meta": meta,
			"icon": icon,
		})
	return catalog


def _report_exists(report_name: str) -> bool:
	if not _doctype_exists("Report"):
		return False
	return bool(frappe.db.exists("Report", report_name))


def _quotation_action_filters(scope: dict[str, object]) -> tuple[list[list[object]], str]:
	fields = _fieldnames("Quotation")
	filters = [
		["docstatus", "!=", 2],
		["status", "in", ["Draft", "Open"]],
	]
	pending_states = _configured_pending_states("Quotation")
	if "workflow_state" in fields and pending_states:
		filters.append(["workflow_state", "not in", pending_states])
	return _apply_scope_filters("Quotation", filters, scope)


def _quotation_expiring_filters(today, scope: dict[str, object]) -> tuple[list[list[object]], str]:
	return _apply_scope_filters(
		"Quotation",
		[
			["docstatus", "!=", 2],
			["status", "=", "Open"],
			["valid_till", ">=", today],
			["valid_till", "<=", today + timedelta(days=7)],
		],
		scope,
	)


def _sales_order_active_filters(
	scope: dict[str, object],
	exclude_pending_workflow: bool = False,
) -> tuple[list[list[object]], str]:
	fields = _fieldnames("Sales Order")
	filters = [["docstatus", "!=", 2]]
	if "status" in fields:
		filters.append(["status", "in", list(ACTIVE_SALES_ORDER_STATUSES)])

	pending_states = _configured_pending_states("Sales Order")
	if exclude_pending_workflow and "workflow_state" in fields and pending_states:
		filters.append(["workflow_state", "not in", pending_states])

	return _apply_scope_filters("Sales Order", filters, scope)


def _partially_delivered_sales_order_filters(scope: dict[str, object]) -> tuple[list[list[object]], str]:
	filters, scope_note = _sales_order_active_filters(scope, exclude_pending_workflow=True)
	filters.extend(
		[
			["docstatus", "=", 1],
			["per_delivered", ">", 0],
			["per_delivered", "<", 100],
		]
	)
	return filters, scope_note


def _orders_due_soon_filters(today, scope: dict[str, object]) -> tuple[list[list[object]], str]:
	filters, scope_note = _sales_order_active_filters(scope, exclude_pending_workflow=True)
	filters.extend(
		[
			["docstatus", "=", 1],
			["delivery_date", ">=", today],
			["delivery_date", "<=", today + timedelta(days=3)],
		]
	)
	return filters, scope_note


def _invoice_outstanding_filters(scope: dict[str, object]) -> tuple[list[list[object]], str]:
	fields = _fieldnames("Sales Invoice")
	filters = [["docstatus", "=", 1], ["status", "in", list(OUTSTANDING_SALES_INVOICE_STATUSES)]]
	if "is_return" in fields:
		filters.append(["is_return", "=", 0])
	if "outstanding_amount" in fields:
		filters.append(["outstanding_amount", ">", 0])
	return _apply_scope_filters("Sales Invoice", filters, scope)


def _sales_return_filters(
	doctype: str,
	today,
	scope: dict[str, object],
) -> tuple[list[list[object]], str]:
	fields = _fieldnames(doctype)
	filters = [["docstatus", "=", 1]]
	if "is_return" in fields:
		filters.append(["is_return", "=", 1])
	if "posting_date" in fields:
		filters.append(["posting_date", ">=", today - timedelta(days=30)])
	return _apply_scope_filters(doctype, filters, scope)


def _follow_up_filters(scope: dict[str, object]) -> tuple[list[list[object]], str, str | None]:
	fields = _fieldnames("ToDo")
	assignee_field = None
	for candidate in ("allocated_to", "assigned_to"):
		if candidate in fields:
			assignee_field = candidate
			break

	if not assignee_field:
		return [], "Using general ToDo scope because assignment fields are unavailable.", None

	filters = [
		[assignee_field, "in", scope.get("todo_user_ids") or [frappe.session.user]],
		["status", "!=", "Closed"],
	]
	if "reference_type" in fields:
		filters.append(
			[
				"reference_type",
				"in",
				[
					"Customer",
					"Lead",
					"Opportunity",
					"Quotation",
					"Sales Order",
					"Sales Invoice",
					"Delivery Note",
				],
			]
		)

	scoped_filters, scope_note = _apply_scope_filters("ToDo", filters, scope)
	return scoped_filters, scope_note, assignee_field


def _route_filter_options(filters: list[list[object]]) -> dict[str, object]:
	route_filters: dict[str, object] = {}
	for filter_row in filters:
		if len(filter_row) != 3:
			continue

		fieldname, operator, value = filter_row
		condition = [operator, value]
		existing = route_filters.get(fieldname)
		if existing is None:
			route_filters[fieldname] = condition
			continue

		if isinstance(existing, list) and existing and isinstance(existing[0], list):
			existing.append(condition)
			continue

		route_filters[fieldname] = [existing, condition]
	return route_filters


def _resolve_branch(employee_record: dict[str, object] | None = None) -> str | None:
	if employee_record and employee_record.get("branch"):
		return employee_record["branch"]

	user_fields = _fieldnames("User")
	for fieldname in ("branch", "default_branch"):
		if fieldname in user_fields:
			branch_name = frappe.db.get_value("User", frappe.session.user, fieldname)
			if branch_name:
				return branch_name

	return None


def _primary_sales_role(role_variant: str | None = None) -> str:
	labels = {
		"sales_manager": "Sales Manager",
		"sales_executive": "Sales Staff",
		"key_account_sales": "Key Account Sales",
		"showroom_sales": "Showroom Sales",
		"executive_review": "Executive Approver",
	}
	return labels.get(role_variant or _role_variant(), "Sales Staff")


def _role_variant() -> str:
	roles = {role.lower() for role in frappe.get_roles(frappe.session.user)}
	if "general manager" in roles or "executive approver" in roles:
		return "executive_review"
	if any("showroom" in role for role in roles):
		return "showroom_sales"
	if "key account sales" in roles:
		return "key_account_sales"
	if "sales manager" in roles or "sales supervisor" in roles:
		return "sales_manager"
	if "sales executive" in roles or "sales user" in roles:
		return "sales_executive"
	return "sales_executive"


def _workflow_states(doctype: str) -> list[str]:
	if "workflow_state" not in _fieldnames(doctype):
		return []

	try:
		rows = frappe.get_list(
			doctype,
			fields=["workflow_state"],
			filters=[["workflow_state", "is", "set"]],
			order_by="modified desc",
			page_length=100,
		)
	except (frappe.PermissionError, frappe.DataError):
		return []
	seen = []
	for row in rows:
		state = row.get("workflow_state")
		if state and state not in seen:
			seen.append(state)
	return seen


def _active_workflow_states(doctype: str) -> list[str]:
	if not _doctype_exists("Workflow"):
		return []

	try:
		workflows = frappe.get_all(
			"Workflow",
			fields=["name"],
			filters={
				"document_type": doctype,
				"is_active": 1,
			},
			order_by="modified desc",
			page_length=5,
		)
	except (frappe.PermissionError, frappe.DataError):
		return []

	workflow_names = [row.get("name") for row in workflows if row.get("name")]
	if not workflow_names or not _doctype_exists("Workflow Document State"):
		return []

	state_rows = frappe.get_all(
		"Workflow Document State",
		fields=["state", "parent"],
		filters={"parent": ["in", workflow_names]},
		order_by="idx asc",
	)

	seen = []
	for state_row in state_rows:
		state = state_row.get("state")
		if state and state not in seen:
			seen.append(state)
	return seen


def _configured_pending_states(doctype: str) -> list[str]:
	configured = EXPLICIT_PENDING_WORKFLOW_STATES.get(doctype, ())
	if not configured:
		return []

	visible_states = [*_active_workflow_states(doctype), *_workflow_states(doctype)]
	visible_lookup = {state.casefold(): state for state in visible_states}
	matching_states = []
	for state in configured:
		matched = visible_lookup.get(state.casefold())
		if matched and matched not in matching_states:
			matching_states.append(matched)
	return matching_states


def _apply_scope_filters(
	doctype: str,
	filters: list[list[object]],
	scope: dict[str, object],
) -> tuple[list[list[object]], str]:
	scoped_filters = list(filters)
	branch_name = scope.get("branch_name")
	owner_user_ids = list(scope.get("owner_user_ids") or [])

	fields = _fieldnames(doctype)
	if owner_user_ids and "owner" in fields and doctype in {"Quotation", "Sales Order", "Opportunity", "Lead"}:
		scoped_filters.append(["owner", "in", owner_user_ids])

	if branch_name and scope.get("apply_branch_filter") and "branch" in fields:
		scoped_filters.append(["branch", "=", branch_name])
		if owner_user_ids:
			return scoped_filters, f"Owner and branch scope applied: {branch_name}."
		return scoped_filters, f"Branch scope applied: {branch_name}."

	if owner_user_ids and doctype in {"Quotation", "Sales Order", "Opportunity", "Lead"}:
		return scoped_filters, "Current role scope applied through document ownership."

	if branch_name:
		return scoped_filters, f"Branch context detected ({branch_name}), but {doctype} is not branch-filterable here."

	return scoped_filters, "Using permission scope because no mapped branch is available."


def _count_records(doctype: str, filters: list[list[object]]) -> int:
	rows = frappe.get_list(
		doctype,
		fields=[{"COUNT": "name", "as": "count"}],
		filters=filters,
		page_length=1,
	)
	if not rows:
		return 0
	count_value = rows[0].get("count", 0)
	try:
		return int(count_value or 0)
	except (TypeError, ValueError):
		return 0


def _fieldnames(doctype: str) -> set[str]:
	if not _doctype_exists(doctype):
		return set()

	meta = frappe.get_meta(doctype)
	fieldnames = {field.fieldname for field in meta.fields if field.fieldname}
	fieldnames.update({"name", "owner", "creation", "modified", "modified_by", "docstatus"})
	return fieldnames


def _employee_record() -> dict[str, object] | None:
	if not _doctype_exists("Employee") or "user_id" not in _fieldnames("Employee"):
		return None

	record = frappe.db.get_value(
		"Employee",
		{"user_id": frappe.session.user},
		["name", "branch", "designation", "department"],
		as_dict=True,
	)
	return record or None


def _direct_report_users(employee_name: str | None) -> list[str]:
	if not employee_name or not _doctype_exists("Employee"):
		return []

	fields = _fieldnames("Employee")
	if "reports_to" not in fields or "user_id" not in fields:
		return []

	rows = frappe.get_all(
		"Employee",
		fields=["user_id"],
		filters={
			"reports_to": employee_name,
			"user_id": ["is", "set"],
		},
	)
	return [row.get("user_id") for row in rows if row.get("user_id")]


def _doctype_exists(doctype: str) -> bool:
	return bool(frappe.db.exists("DocType", doctype))


def _can_read(doctype: str) -> bool:
	return _doctype_exists(doctype) and bool(
		frappe.has_permission(doctype, "read", user=frappe.session.user)
	)


def _live_metric(value: int, note: str) -> dict[str, object]:
	return {"state": "live", "value": value, "note": note}


def _unavailable_metric(note: str) -> dict[str, object]:
	return {"state": "unavailable", "value": None, "note": note}


def _access_metric(doctype: str) -> dict[str, object]:
	if not _doctype_exists(doctype):
		return _unavailable_metric(f"{doctype} is not available on this site.")
	return {"state": "restricted", "value": None, "note": f"{doctype} is outside current read scope."}


def _find_customer_inquiry_match(query: str) -> dict[str, object]:
	for doctype in INQUIRY_DOCUMENT_ORDER:
		if not _can_read(doctype):
			continue
		if frappe.db.exists(doctype, query):
			return {
				"state": "resolved",
				"match_mode": "exact_document",
				"anchor": {"doctype": doctype, "name": query},
			}

	customer_matches = _find_exact_customer_matches(query)
	if len(customer_matches) == 1:
		return {
			"state": "resolved",
			"match_mode": "exact_customer_name",
			"anchor": {"doctype": "Customer", "name": customer_matches[0]["name"]},
		}

	if len(customer_matches) > 1:
		return {
			"state": "multiple_matches",
			"query": query,
			"message": "Multiple customers share this exact name. Choose the correct customer chain.",
			"choices": [_build_customer_choice(row) for row in customer_matches],
		}

	suggestions = _build_customer_inquiry_suggestions(query)
	if suggestions:
		return {
			"state": "multiple_matches",
			"query": query,
			"message": "No exact match was found. Choose the closest visible customer or document.",
			"choices": suggestions,
		}

	return {
		"state": "not_found",
		"query": query,
		"message": "No customer or document match was found for this inquiry.",
	}


def _find_exact_customer_matches(query: str) -> list[dict[str, object]]:
	if not _can_read("Customer"):
		return []

	fields = _fieldnames("Customer")
	filters: list[list[object]] = []
	if "customer_name" in fields:
		filters.append(["customer_name", "=", query])
	filters.append(["name", "=", query])
	if not filters:
		return []

	rows = frappe.get_list(
		"Customer",
		fields=["name", "customer_name", "territory", "modified"],
		filters=filters,
		or_filters=filters,
		order_by="modified desc",
		page_length=6,
	)
	return _dedupe_inquiry_rows(rows)


def _find_customer_name_matches(query: str, limit: int = 6) -> list[dict[str, object]]:
	if not _can_read("Customer"):
		return []

	fields = _fieldnames("Customer")
	filters: list[list[object]] = []
	if "customer_name" in fields:
		filters.append(["customer_name", "like", f"%{query}%"])
	filters.append(["name", "like", f"%{query}%"])
	if not filters:
		return []

	rows = frappe.get_list(
		"Customer",
		fields=["name", "customer_name", "territory", "modified"],
		filters=filters,
		or_filters=filters,
		order_by="modified desc",
		page_length=limit,
	)
	return _dedupe_inquiry_rows(rows)


def _build_customer_inquiry_suggestions(query: str, limit: int = 8) -> list[dict[str, object]]:
	query = (query or "").strip()
	if not query:
		return []

	doctype_order = _inquiry_doctype_priority(query)
	doctype_priority = {doctype: index for index, doctype in enumerate(doctype_order)}
	query_prefers_document_order = bool(re.search(r"[\d-]", query))
	candidates: list[dict[str, object]] = []
	seen: set[tuple[str, str]] = set()

	for doctype in doctype_order:
		for suggestion in _search_inquiry_candidates(doctype, query):
			key = (suggestion["doctype"], suggestion["name"])
			if key in seen:
				continue
			seen.add(key)
			candidates.append(suggestion)

	candidates.sort(key=lambda item: item.get("_sort_modified") or "", reverse=True)
	if query_prefers_document_order:
		candidates.sort(key=lambda item: item.get("_sort_name") or "", reverse=True)
	candidates.sort(key=lambda item: doctype_priority.get(item.get("doctype"), len(doctype_order)))
	candidates.sort(key=lambda item: item.get("_sort_score", 0), reverse=True)
	return [
		{
			"doctype": item["doctype"],
			"name": item["name"],
			"label": item["label"],
			"meta": item["meta"],
		}
		for item in candidates[:limit]
	]


def _search_inquiry_candidates(doctype: str, query: str) -> list[dict[str, object]]:
	if doctype == "Customer":
		return _search_customer_inquiry_candidates(query)
	if not _can_read(doctype):
		return []

	rows = frappe.get_list(
		doctype,
		fields=_inquiry_doc_fields(doctype),
		filters=[["name", "like", f"%{query}%"]],
		order_by="modified desc",
		page_length=6,
	)
	candidates = []
	for row in rows:
		score = _score_inquiry_value(query, row.get("name"))
		if score <= 0:
			continue
		candidates.append(
			{
				"doctype": doctype,
				"name": row.get("name"),
				"label": row.get("name"),
				"meta": _build_inquiry_doc_meta(doctype, row),
				"_sort_name": row.get("name") or "",
				"_sort_score": score,
				"_sort_modified": row.get("modified") or "",
			}
		)
	return candidates


def _search_customer_inquiry_candidates(query: str) -> list[dict[str, object]]:
	rows = _find_customer_name_matches(query, limit=6)
	candidates = []
	for row in rows:
		score = max(
			_score_inquiry_value(query, row.get("customer_name"), exact_bonus=40),
			_score_inquiry_value(query, row.get("name"), exact_bonus=20),
		)
		if score <= 0:
			continue
		candidates.append(
			{
				"doctype": "Customer",
				"name": row.get("name"),
				"label": row.get("customer_name") or row.get("name"),
				"meta": _build_customer_choice_meta(row),
				"_sort_name": row.get("name") or row.get("customer_name") or "",
				"_sort_score": score,
				"_sort_modified": row.get("modified") or "",
			}
		)
	return candidates


def _inquiry_doc_fields(doctype: str) -> list[str]:
	fields = _fieldnames(doctype)
	field_list = ["name", "modified"]
	for fieldname in ("customer", "status", "transaction_date", "posting_date", "delivery_date"):
		if fieldname in fields and fieldname not in field_list:
			field_list.append(fieldname)
	return field_list


def _score_inquiry_value(query: str, value: object, exact_bonus: int = 0) -> int:
	if value in (None, ""):
		return 0

	needle = str(query).strip().casefold()
	candidate = str(value).strip().casefold()
	if not needle or not candidate:
		return 0
	if candidate == needle:
		return 1000 + exact_bonus
	if candidate.startswith(needle):
		return 820 + exact_bonus
	if needle in candidate:
		return 540 + exact_bonus
	return 0


def _build_inquiry_doc_meta(doctype: str, row: dict[str, object]) -> str:
	date_field = (INQUIRY_DOCUMENT_HINTS.get(doctype) or {}).get("date_field")
	date_value = row.get(date_field) if date_field else None
	parts = [row.get("customer"), row.get("status"), date_value]
	if not any(part not in (None, "") for part in parts):
		parts = [doctype]
	return " · ".join(str(part).strip() for part in parts if part not in (None, ""))


def _build_customer_choice(row: dict[str, object]) -> dict[str, object]:
	return {
		"doctype": "Customer",
		"name": row.get("name"),
		"label": row.get("customer_name") or row.get("name"),
		"meta": _build_customer_choice_meta(row),
	}


def _build_customer_choice_meta(row: dict[str, object]) -> str:
	parts = []
	if row.get("name") and row.get("customer_name") and row.get("name") != row.get("customer_name"):
		parts.append(row.get("name"))
	if row.get("territory"):
		parts.append(row.get("territory"))
	if not parts:
		parts.append("Customer record")
	return " · ".join(str(part).strip() for part in parts if part not in (None, ""))


def _inquiry_doctype_priority(query: str) -> list[str]:
	if re.search(r"[\d-]", query or ""):
		return list(INQUIRY_DOCUMENT_ORDER)
	return ["Customer", "Quotation", "Sales Order", "Sales Invoice", "Delivery Note"]


def _dedupe_inquiry_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
	seen: set[str] = set()
	unique_rows: list[dict[str, object]] = []
	for row in rows:
		name = row.get("name")
		if not name or name in seen:
			continue
		seen.add(name)
		unique_rows.append(row)
	return unique_rows


def _build_customer_inquiry_result(doctype: str, name: str, query: str) -> dict[str, object]:
	if not _can_read(doctype):
		return {
			"state": "restricted",
			"query": query,
			"message": f"{doctype} is outside current read scope.",
		}

	anchor = _load_anchor_document(doctype, name)
	if not anchor:
		return {
			"state": "not_found",
			"query": query,
			"message": f"{doctype} {name} was not found.",
		}

	customer_name = anchor.get("customer")
	customer = _load_customer_summary(customer_name) if customer_name else None
	quotation_docs, sales_order_docs, delivery_docs, sales_invoice_docs = _resolve_commercial_chain(anchor)
	payment_entries = _resolve_payment_entries(sales_invoice_docs, sales_order_docs)
	return_docs = _resolve_return_documents(anchor, sales_invoice_docs, delivery_docs, customer_name)

	return {
		"state": "resolved",
		"query": query,
		"anchor": {"doctype": doctype, "name": name},
		"primary_match": _build_primary_match(anchor, customer),
		"customer_summary": _build_customer_summary(customer, quotation_docs, sales_order_docs, sales_invoice_docs),
		"document_flow": _build_document_flow(
			anchor,
			quotation_docs,
			sales_order_docs,
			delivery_docs,
			sales_invoice_docs,
			payment_entries,
			return_docs,
		),
		"current_status": _build_current_status(
			anchor,
			quotation_docs,
			sales_order_docs,
			delivery_docs,
			sales_invoice_docs,
			payment_entries,
			return_docs,
		),
		"exceptions": _build_inquiry_exceptions(
			quotation_docs,
			sales_order_docs,
			sales_invoice_docs,
			return_docs,
		),
		"related_documents": _build_related_documents(
			anchor,
			quotation_docs,
			sales_order_docs,
			delivery_docs,
			sales_invoice_docs,
			payment_entries,
			return_docs,
		),
	}


def _load_anchor_document(doctype: str, name: str) -> dict[str, object] | None:
	fields = _fieldnames(doctype)
	field_list = [field for field in [
		"name",
		"customer",
		"customer_name",
		"status",
		"workflow_state",
		"docstatus",
		"territory",
		"posting_date",
		"transaction_date",
		"delivery_date",
		"valid_till",
		"grand_total",
		"outstanding_amount",
		"per_delivered",
		"per_billed",
		"billing_status",
		"advance_payment_status",
		"is_return",
		"return_against",
		"mobile_no",
		"phone",
	] if field in fields]
	document = frappe.db.get_value(doctype, name, field_list, as_dict=True)
	if not document:
		return None
	document["doctype"] = doctype
	if doctype == "Customer":
		document.setdefault("customer", document.get("name"))
		document.setdefault("customer_name", document.get("customer_name") or document.get("name"))
	return document


def _load_customer_summary(customer_name: str) -> dict[str, object] | None:
	if not customer_name or not _can_read("Customer"):
		return None
	fields = _fieldnames("Customer")
	field_list = [field for field in [
		"name",
		"customer_name",
		"territory",
		"mobile_no",
		"phone",
		"customer_group",
	] if field in fields]
	return frappe.db.get_value("Customer", customer_name, field_list, as_dict=True) or None


def _resolve_commercial_chain(
	anchor: dict[str, object]
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
	doctype = anchor.get("doctype")
	customer_name = anchor.get("customer")

	quotation_names: set[str] = set()
	sales_order_names: set[str] = set()
	delivery_names: set[str] = set()
	sales_invoice_names: set[str] = set()

	if doctype == "Quotation":
		quotation_names.add(anchor["name"])
	elif doctype == "Sales Order":
		sales_order_names.add(anchor["name"])
	elif doctype == "Delivery Note":
		delivery_names.add(anchor["name"])
	elif doctype == "Sales Invoice":
		sales_invoice_names.add(anchor["name"])

	if doctype == "Customer":
		quotation_names.update(_recent_doc_names("Quotation", customer_name, limit=5))
		sales_order_names.update(_recent_doc_names("Sales Order", customer_name, limit=5))
		delivery_names.update(_recent_doc_names("Delivery Note", customer_name, limit=5))
		sales_invoice_names.update(_recent_doc_names("Sales Invoice", customer_name, limit=5))

	if quotation_names:
		sales_order_names.update(_sales_orders_from_quotation_names(list(quotation_names)))

	if sales_order_names:
		quotation_names.update(_quotations_from_sales_order_names(list(sales_order_names)))
		delivery_names.update(_delivery_notes_from_sales_order_names(list(sales_order_names)))
		sales_invoice_names.update(_sales_invoices_from_sales_order_names(list(sales_order_names)))

	if delivery_names:
		sales_order_names.update(_sales_orders_from_delivery_names(list(delivery_names)))
		sales_invoice_names.update(_sales_invoices_from_delivery_names(list(delivery_names)))

	if sales_invoice_names:
		sales_order_names.update(_sales_orders_from_sales_invoice_names(list(sales_invoice_names)))
		delivery_names.update(_delivery_notes_from_sales_invoice_names(list(sales_invoice_names)))

	if sales_order_names and not quotation_names:
		quotation_names.update(_quotations_from_sales_order_names(list(sales_order_names)))

	quotation_docs = _load_documents("Quotation", list(quotation_names), order_date_field="transaction_date")
	sales_order_docs = _load_documents("Sales Order", list(sales_order_names), order_date_field="transaction_date")
	delivery_docs = _load_documents("Delivery Note", list(delivery_names), order_date_field="posting_date")
	sales_invoice_docs = _load_documents("Sales Invoice", list(sales_invoice_names), order_date_field="posting_date")
	return quotation_docs, sales_order_docs, delivery_docs, sales_invoice_docs


def _recent_doc_names(doctype: str, customer_name: str | None, limit: int = 5) -> list[str]:
	if not customer_name or not _can_read(doctype) or "customer" not in _fieldnames(doctype):
		return []
	rows = frappe.get_list(
		doctype,
		fields=["name"],
		filters={"customer": customer_name},
		order_by="modified desc",
		page_length=limit,
	)
	return [row.get("name") for row in rows if row.get("name")]


def _sales_orders_from_quotation_names(quotation_names: list[str]) -> list[str]:
	if not quotation_names or not _doctype_exists("Sales Order Item"):
		return []
	rows = frappe.get_all(
		"Sales Order Item",
		fields=["parent"],
		filters={"prevdoc_docname": ["in", quotation_names]},
		distinct=True,
	)
	return [row.get("parent") for row in rows if row.get("parent")]


def _quotations_from_sales_order_names(sales_order_names: list[str]) -> list[str]:
	if not sales_order_names or not _doctype_exists("Sales Order Item"):
		return []
	rows = frappe.get_all(
		"Sales Order Item",
		fields=["prevdoc_docname"],
		filters={
			"parent": ["in", sales_order_names],
			"prevdoc_docname": ["is", "set"],
		},
		distinct=True,
	)
	return [row.get("prevdoc_docname") for row in rows if row.get("prevdoc_docname")]


def _delivery_notes_from_sales_order_names(sales_order_names: list[str]) -> list[str]:
	if not sales_order_names or not _doctype_exists("Delivery Note Item"):
		return []
	rows = frappe.get_all(
		"Delivery Note Item",
		fields=["parent"],
		filters={"against_sales_order": ["in", sales_order_names]},
		distinct=True,
	)
	return [row.get("parent") for row in rows if row.get("parent")]


def _sales_invoices_from_sales_order_names(sales_order_names: list[str]) -> list[str]:
	if not sales_order_names or not _doctype_exists("Sales Invoice Item"):
		return []
	rows = frappe.get_all(
		"Sales Invoice Item",
		fields=["parent"],
		filters={"sales_order": ["in", sales_order_names]},
		distinct=True,
	)
	return [row.get("parent") for row in rows if row.get("parent")]


def _sales_orders_from_delivery_names(delivery_names: list[str]) -> list[str]:
	if not delivery_names or not _doctype_exists("Delivery Note Item"):
		return []
	rows = frappe.get_all(
		"Delivery Note Item",
		fields=["against_sales_order"],
		filters={
			"parent": ["in", delivery_names],
			"against_sales_order": ["is", "set"],
		},
		distinct=True,
	)
	return [row.get("against_sales_order") for row in rows if row.get("against_sales_order")]


def _sales_invoices_from_delivery_names(delivery_names: list[str]) -> list[str]:
	if not delivery_names or not _doctype_exists("Sales Invoice Item"):
		return []
	rows = frappe.get_all(
		"Sales Invoice Item",
		fields=["parent"],
		filters={"delivery_note": ["in", delivery_names]},
		distinct=True,
	)
	return [row.get("parent") for row in rows if row.get("parent")]


def _sales_orders_from_sales_invoice_names(sales_invoice_names: list[str]) -> list[str]:
	if not sales_invoice_names or not _doctype_exists("Sales Invoice Item"):
		return []
	rows = frappe.get_all(
		"Sales Invoice Item",
		fields=["sales_order"],
		filters={
			"parent": ["in", sales_invoice_names],
			"sales_order": ["is", "set"],
		},
		distinct=True,
	)
	return [row.get("sales_order") for row in rows if row.get("sales_order")]


def _delivery_notes_from_sales_invoice_names(sales_invoice_names: list[str]) -> list[str]:
	if not sales_invoice_names or not _doctype_exists("Sales Invoice Item"):
		return []
	rows = frappe.get_all(
		"Sales Invoice Item",
		fields=["delivery_note"],
		filters={
			"parent": ["in", sales_invoice_names],
			"delivery_note": ["is", "set"],
		},
		distinct=True,
	)
	return [row.get("delivery_note") for row in rows if row.get("delivery_note")]


def _load_documents(doctype: str, names: list[str], order_date_field: str | None = None) -> list[dict[str, object]]:
	if not names or not _can_read(doctype):
		return []

	fields = _fieldnames(doctype)
	field_list = [field for field in [
		"name",
		"customer",
		"customer_name",
		"status",
		"workflow_state",
		"docstatus",
		"posting_date",
		"transaction_date",
		"delivery_date",
		"valid_till",
		"grand_total",
		"outstanding_amount",
		"per_delivered",
		"per_billed",
		"billing_status",
		"advance_payment_status",
		"is_return",
		"return_against",
	] if field in fields]
	rows = frappe.get_list(
		doctype,
		fields=field_list,
		filters={"name": ["in", names]},
		order_by="modified desc",
		page_length=max(len(names), 20),
	)
	for row in rows:
		row["doctype"] = doctype
	if order_date_field and order_date_field in fields:
		rows.sort(key=lambda row: (row.get(order_date_field) or "", row.get("name") or ""), reverse=True)
	return rows


def _resolve_payment_entries(
	sales_invoice_docs: list[dict[str, object]],
	sales_order_docs: list[dict[str, object]],
) -> list[dict[str, object]]:
	if not _can_read("Payment Entry") or not _doctype_exists("Payment Entry Reference"):
		return []

	invoice_names = [doc.get("name") for doc in sales_invoice_docs if doc.get("name")]
	order_names = [doc.get("name") for doc in sales_order_docs if doc.get("name")]
	if invoice_names:
		rows = frappe.get_all(
			"Payment Entry Reference",
			fields=["parent", "reference_doctype", "reference_name", "allocated_amount", "outstanding_amount"],
			filters={"reference_doctype": "Sales Invoice", "reference_name": ["in", invoice_names]},
		)
	elif order_names:
		rows = frappe.get_all(
			"Payment Entry Reference",
			fields=["parent", "reference_doctype", "reference_name", "allocated_amount", "outstanding_amount"],
			filters={"reference_doctype": "Sales Order", "reference_name": ["in", order_names]},
		)
	else:
		return []

	parent_names = sorted({row.get("parent") for row in rows if row.get("parent")})
	payments = _load_documents("Payment Entry", parent_names, order_date_field="posting_date")
	payments = [payment for payment in payments if payment.get("docstatus") == 1][:8]
	allocation_map: dict[str, list[dict[str, object]]] = {}
	for row in rows:
		parent = row.get("parent")
		if not parent:
			continue
		allocation_map.setdefault(parent, []).append(row)
	for payment in payments:
		payment["allocations"] = allocation_map.get(payment.get("name"), [])
	return payments


def _resolve_return_documents(
	anchor: dict[str, object],
	sales_invoice_docs: list[dict[str, object]],
	delivery_docs: list[dict[str, object]],
	customer_name: str | None,
) -> list[dict[str, object]]:
	returns: list[dict[str, object]] = []
	invoice_names = [doc.get("name") for doc in sales_invoice_docs if doc.get("name")]
	delivery_names = [doc.get("name") for doc in delivery_docs if doc.get("name")]

	if _can_read("Sales Invoice") and "is_return" in _fieldnames("Sales Invoice"):
		filters = {"is_return": 1}
		if invoice_names and "return_against" in _fieldnames("Sales Invoice"):
			filters["return_against"] = ["in", invoice_names]
		elif customer_name and "customer" in _fieldnames("Sales Invoice"):
			filters["customer"] = customer_name
		rows = frappe.get_list(
			"Sales Invoice",
			fields=[field for field in ["name", "customer", "status", "posting_date", "return_against"] if field in _fieldnames("Sales Invoice")],
			filters=filters,
			order_by="posting_date desc, modified desc",
			page_length=10,
		)
		for row in rows:
			row["doctype"] = "Sales Invoice"
		returns.extend(rows)

	if _can_read("Delivery Note") and "is_return" in _fieldnames("Delivery Note"):
		filters = {"is_return": 1}
		if delivery_names and "return_against" in _fieldnames("Delivery Note"):
			filters["return_against"] = ["in", delivery_names]
		elif customer_name and "customer" in _fieldnames("Delivery Note"):
			filters["customer"] = customer_name
		rows = frappe.get_list(
			"Delivery Note",
			fields=[field for field in ["name", "customer", "status", "posting_date", "return_against"] if field in _fieldnames("Delivery Note")],
			filters=filters,
			order_by="posting_date desc, modified desc",
			page_length=10,
		)
		for row in rows:
			row["doctype"] = "Delivery Note"
		returns.extend(rows)

	if anchor.get("doctype") in {"Sales Invoice", "Delivery Note"} and (
		anchor.get("is_return") in (1, "1", True)
		or bool(anchor.get("return_against"))
		or str(anchor.get("status") or "").lower() == "return"
	):
		returns.append({
			"doctype": anchor.get("doctype"),
			"name": anchor.get("name"),
			"customer": anchor.get("customer"),
			"status": anchor.get("status"),
			"posting_date": anchor.get("posting_date"),
			"return_against": anchor.get("return_against"),
		})

	seen: set[tuple[str, str]] = set()
	unique_returns: list[dict[str, object]] = []
	for row in sorted(
		returns,
		key=lambda item: (item.get("posting_date") or "", item.get("name") or ""),
		reverse=True,
	):
		key = (str(row.get("doctype") or ""), str(row.get("name") or ""))
		if not key[0] or not key[1] or key in seen:
			continue
		seen.add(key)
		unique_returns.append(row)
	return unique_returns


def _build_primary_match(anchor: dict[str, object], customer: dict[str, object] | None) -> dict[str, object]:
	customer_label = None
	if customer:
		customer_label = customer.get("customer_name") or customer.get("name")
	elif anchor.get("customer_name"):
		customer_label = anchor.get("customer_name")
	elif anchor.get("customer"):
		customer_label = anchor.get("customer")
	return {
		"doctype": anchor.get("doctype"),
		"name": anchor.get("name"),
		"customer": customer_label,
		"status": _document_status_label(anchor),
	}


def _build_customer_summary(
	customer: dict[str, object] | None,
	quotation_docs: list[dict[str, object]],
	sales_order_docs: list[dict[str, object]],
	sales_invoice_docs: list[dict[str, object]],
) -> dict[str, object]:
	return {
		"name": (customer or {}).get("customer_name") or (customer or {}).get("name"),
		"customer_id": (customer or {}).get("name"),
		"territory": (customer or {}).get("territory"),
		"contact": (customer or {}).get("mobile_no") or (customer or {}).get("phone"),
		"latest_documents": [
			_latest_doc_reference("Quotation", quotation_docs),
			_latest_doc_reference("Sales Order", sales_order_docs),
			_latest_doc_reference("Sales Invoice", sales_invoice_docs),
		],
	}


def _latest_doc_reference(doctype: str, docs: list[dict[str, object]]) -> dict[str, object]:
	if not docs:
		return {"doctype": doctype, "state": "not_available", "name": None, "status": None}
	doc = docs[0]
	return {
		"doctype": doctype,
		"state": "present",
		"name": doc.get("name"),
		"status": _document_status_label(doc),
	}


def _build_document_flow(
	anchor: dict[str, object],
	quotation_docs: list[dict[str, object]],
	sales_order_docs: list[dict[str, object]],
	delivery_docs: list[dict[str, object]],
	sales_invoice_docs: list[dict[str, object]],
	payment_entries: list[dict[str, object]],
	return_docs: list[dict[str, object]],
) -> list[dict[str, object]]:
	return [
		_flow_stage("Quotation", quotation_docs, _infer_flow_state("Quotation", anchor, quotation_docs, sales_order_docs, delivery_docs, sales_invoice_docs, payment_entries, return_docs)),
		_flow_stage("Sales Order", sales_order_docs, _infer_flow_state("Sales Order", anchor, quotation_docs, sales_order_docs, delivery_docs, sales_invoice_docs, payment_entries, return_docs)),
		_flow_stage("Delivery", delivery_docs, _infer_flow_state("Delivery", anchor, quotation_docs, sales_order_docs, delivery_docs, sales_invoice_docs, payment_entries, return_docs)),
		_flow_stage("Sales Invoice", sales_invoice_docs, _infer_flow_state("Sales Invoice", anchor, quotation_docs, sales_order_docs, delivery_docs, sales_invoice_docs, payment_entries, return_docs)),
		_build_payment_flow_stage(sales_invoice_docs, payment_entries),
		_flow_stage("Return", return_docs, _infer_flow_state("Return", anchor, quotation_docs, sales_order_docs, delivery_docs, sales_invoice_docs, payment_entries, return_docs)),
	]


def _flow_stage(label: str, docs: list[dict[str, object]], state: str) -> dict[str, object]:
	return {
		"label": label,
		"state": state,
		"items": [
			{
				"doctype": doc.get("doctype") or label,
				"name": doc.get("name"),
				"status": _document_status_label(doc),
			}
			for doc in docs[:5]
		],
	}


def _build_payment_flow_stage(
	sales_invoice_docs: list[dict[str, object]],
	payment_entries: list[dict[str, object]],
) -> dict[str, object]:
	state, item_name, item_status = _payment_flow_descriptor(sales_invoice_docs, payment_entries)
	stage = _flow_stage("Payment", payment_entries, state)
	if stage["items"]:
		return stage
	stage["items"] = [{
		"doctype": "Payment",
		"name": item_name,
		"status": item_status,
	}]
	return stage


def _infer_flow_state(
	stage: str,
	anchor: dict[str, object],
	quotation_docs: list[dict[str, object]],
	sales_order_docs: list[dict[str, object]],
	delivery_docs: list[dict[str, object]],
	sales_invoice_docs: list[dict[str, object]],
	payment_entries: list[dict[str, object]],
	return_docs: list[dict[str, object]],
) -> str:
	stage_docs = {
		"Quotation": quotation_docs,
		"Sales Order": sales_order_docs,
		"Delivery": delivery_docs,
		"Sales Invoice": sales_invoice_docs,
		"Payment": payment_entries,
		"Return": return_docs,
	}.get(stage, [])
	if stage_docs:
		return "present"

	if stage == "Quotation":
		if sales_order_docs or delivery_docs or sales_invoice_docs:
			return "not_used"
		if anchor.get("doctype") == "Customer":
			return "unknown"
		return "not_yet_created"

	if stage == "Sales Order":
		if sales_invoice_docs or delivery_docs:
			return "not_used"
		if quotation_docs:
			return "not_yet_created"
		return "unknown"

	if stage == "Delivery":
		if sales_invoice_docs and not sales_order_docs:
			return "not_used"
		if sales_order_docs:
			return "not_yet_created"
		return "unknown"

	if stage == "Sales Invoice":
		if sales_order_docs or delivery_docs:
			return "not_yet_created"
		if quotation_docs:
			return "unknown"
		return "unknown"

	if stage == "Payment":
		if sales_invoice_docs:
			return "not_yet_created"
		return "not_applicable"

	if stage == "Return":
		if delivery_docs or sales_invoice_docs:
			return "not_applicable"
		return "not_used"

	return "unknown"


def _build_current_status(
	anchor: dict[str, object],
	quotation_docs: list[dict[str, object]],
	sales_order_docs: list[dict[str, object]],
	delivery_docs: list[dict[str, object]],
	sales_invoice_docs: list[dict[str, object]],
	payment_entries: list[dict[str, object]],
	return_docs: list[dict[str, object]],
) -> list[dict[str, object]]:
	return [
		{
			"label": "Quotation",
			"value": _status_summary(quotation_docs, "No quotation in this chain yet"),
		},
		{
			"label": "Sales Order",
			"value": _status_summary(sales_order_docs, "No sales order in this chain yet"),
		},
		{
			"label": "Delivery",
			"value": _delivery_summary(sales_order_docs, delivery_docs),
		},
		{
			"label": "Invoice",
			"value": _invoice_summary(sales_invoice_docs),
		},
		{
			"label": "Payment",
			"value": _payment_summary(sales_invoice_docs, payment_entries),
		},
		{
			"label": "Return",
			"value": _return_summary(return_docs),
		},
		{
			"label": "Approval / Blocker",
			"value": _approval_summary(quotation_docs, sales_order_docs, anchor),
		},
	]


def _status_summary(docs: list[dict[str, object]], empty_text: str) -> str:
	if not docs:
		return empty_text
	primary = docs[0]
	return f"{primary.get('name')}: {_document_status_label(primary)}"


def _delivery_summary(sales_order_docs: list[dict[str, object]], delivery_docs: list[dict[str, object]]) -> str:
	if delivery_docs:
		return f"{len(delivery_docs)} delivery record(s); latest status: {_document_status_label(delivery_docs[0])}"
	if sales_order_docs:
		partial = [doc for doc in sales_order_docs if (doc.get("per_delivered") or 0) not in (None, "", 0, 100)]
		if partial:
			return f"{len(partial)} order(s) partially delivered"
		return "Sales order exists; delivery not yet created or not linked"
	return "No delivery in the current chain"


def _invoice_summary(sales_invoice_docs: list[dict[str, object]]) -> str:
	if not sales_invoice_docs:
		return "No invoice in the current chain"
	latest = sales_invoice_docs[0]
	return f"{len(sales_invoice_docs)} invoice record(s); latest status: {_document_status_label(latest)}"


def _payment_summary(sales_invoice_docs: list[dict[str, object]], payment_entries: list[dict[str, object]]) -> str:
	if payment_entries:
		return f"{len(payment_entries)} payment entry record(s) linked"
	if not sales_invoice_docs:
		return "Payment not yet applicable without invoice"
	cancelled = [
		doc for doc in sales_invoice_docs
		if str(_document_status_label(doc) or "").lower() == "cancelled"
	]
	if cancelled and len(cancelled) == len(sales_invoice_docs):
		return "Cancelled invoices do not require payment follow-up"
	returned = [
		doc for doc in sales_invoice_docs
		if (doc.get("is_return") in (1, "1", True)) or str(doc.get("status") or "").lower() == "return"
	]
	if returned and len(returned) == len(sales_invoice_docs):
		return "Return invoices require credit or refund settlement review"
	paid = [
		doc for doc in sales_invoice_docs
		if (doc.get("outstanding_amount") in (0, 0.0, None, "")) or str(doc.get("status") or "").lower() == "paid"
	]
	if paid and len(paid) == len(sales_invoice_docs):
		return "Invoices appear fully settled"
	if paid:
		return "Invoices are partly settled"
	return "Invoices still need payment or settlement follow-up"


def _payment_flow_descriptor(
	sales_invoice_docs: list[dict[str, object]],
	payment_entries: list[dict[str, object]],
) -> tuple[str, str, str]:
	if payment_entries:
		return ("present", "Visible payment entry in this chain", "")
	if not sales_invoice_docs:
		return ("not_applicable", "None visible in this chain", "")
	cancelled = [
		doc for doc in sales_invoice_docs
		if str(_document_status_label(doc) or "").lower() == "cancelled"
	]
	if cancelled and len(cancelled) == len(sales_invoice_docs):
		return ("not_applicable", "Cancelled invoices do not require payment follow-up", "")
	returned = [
		doc for doc in sales_invoice_docs
		if (doc.get("is_return") in (1, "1", True)) or str(doc.get("status") or "").lower() == "return"
	]
	if returned and len(returned) == len(sales_invoice_docs):
		return ("not_applicable", "Return invoices require credit or refund settlement review", "")
	paid = [
		doc for doc in sales_invoice_docs
		if (doc.get("outstanding_amount") in (0, 0.0, None, "")) or str(doc.get("status") or "").lower() == "paid"
	]
	payment_scope_available = _can_read("Payment Entry") and _doctype_exists("Payment Entry Reference")
	if paid and len(paid) == len(sales_invoice_docs):
		if payment_scope_available:
			return ("settled", "Settlement reflected on invoice status", "")
		return ("settled", "Detailed payment records are outside current read scope", "")
	if paid:
		if payment_scope_available:
			return ("partly_settled", "Settlement is partially reflected on invoice status", "")
		return ("partly_settled", "Detailed payment records are outside current read scope", "")
	if payment_scope_available:
		return ("follow_up", "No linked payment record is visible in this chain", "")
	return ("follow_up", "Detailed payment records are outside current read scope", "")


def _return_summary(return_docs: list[dict[str, object]]) -> str:
	if not return_docs:
		return "No active return is linked in this chain"
	latest = return_docs[0]
	return f"{len(return_docs)} return record(s); latest: {latest.get('doctype')} {latest.get('name')}"


def _approval_summary(
	quotation_docs: list[dict[str, object]],
	sales_order_docs: list[dict[str, object]],
	anchor: dict[str, object],
) -> str:
	for doc in quotation_docs + sales_order_docs + [anchor]:
		if not doc:
			continue
		workflow_state = doc.get("workflow_state")
		doctype = doc.get("doctype")
		if workflow_state and workflow_state in _configured_pending_states(doctype):
			return f"{doctype} {doc.get('name')} is waiting on {workflow_state}"
	return "No active approval blocker found in the linked chain"


def _build_inquiry_exceptions(
	quotation_docs: list[dict[str, object]],
	sales_order_docs: list[dict[str, object]],
	sales_invoice_docs: list[dict[str, object]],
	return_docs: list[dict[str, object]],
) -> list[dict[str, object]]:
	exceptions: list[dict[str, object]] = []
	for doc in quotation_docs + sales_order_docs:
		workflow_state = doc.get("workflow_state")
		doctype = doc.get("doctype")
		if workflow_state and workflow_state in _configured_pending_states(doctype):
			exceptions.append({
				"severity": "blocker",
				"label": f"{doctype} approval waiting",
				"detail": f"{doc.get('name')} is in {workflow_state}.",
			})

	for doc in sales_invoice_docs:
		status = str(doc.get("status") or "")
		if "Overdue" in status:
			exceptions.append({
				"severity": "attention",
				"label": "Overdue invoice",
				"detail": f"{doc.get('name')} is currently {status}.",
			})

	if return_docs:
		exceptions.append({
			"severity": "review",
			"label": "Return activity",
			"detail": f"{len(return_docs)} return-related record(s) are linked to this chain.",
		})

	return exceptions[:6]


def _build_related_documents(
	anchor: dict[str, object],
	quotation_docs: list[dict[str, object]],
	sales_order_docs: list[dict[str, object]],
	delivery_docs: list[dict[str, object]],
	sales_invoice_docs: list[dict[str, object]],
	payment_entries: list[dict[str, object]],
	return_docs: list[dict[str, object]],
) -> list[dict[str, object]]:
	seen: set[tuple[str, str]] = set()
	related = []
	for doc in [anchor, *quotation_docs, *sales_order_docs, *delivery_docs, *sales_invoice_docs, *payment_entries, *return_docs]:
		doctype = doc.get("doctype")
		name = doc.get("name")
		if not doctype or not name or (doctype, name) in seen:
			continue
		seen.add((doctype, name))
		related.append({
			"doctype": doctype,
			"name": name,
			"label": f"{doctype} {name}",
			"status": _document_status_label(doc),
			"target": {"kind": "form", "doctype": doctype, "name": name},
		})
	return related[:12]


def _document_status_label(doc: dict[str, object]) -> str:
	if doc.get("doctype") == "Customer":
		return "Customer Record"
	workflow_state = doc.get("workflow_state")
	status = doc.get("status")
	if workflow_state:
		return str(workflow_state)
	if status:
		return str(status)
	if doc.get("docstatus") == 1:
		return "Submitted"
	if doc.get("docstatus") == 2:
		return "Cancelled"
	return "Draft"


def _build_customer_inquiry_assist_fallback(result: dict[str, object]) -> dict[str, object]:
	primary = result.get("primary_match") if isinstance(result.get("primary_match"), dict) else {}
	customer = result.get("customer_summary") if isinstance(result.get("customer_summary"), dict) else {}
	status_rows = list(result.get("current_status") or [])
	exceptions = list(result.get("exceptions") or [])
	status_map = {
		str(item.get("label") or "").strip(): str(item.get("value") or "").strip()
		for item in status_rows
		if isinstance(item, dict) and str(item.get("label") or "").strip()
	}

	customer_label = (
		str(customer.get("name") or "").strip()
		or str(primary.get("customer") or "").strip()
		or "This customer"
	)
	anchor_label = f"{primary.get('doctype') or 'record'} {primary.get('name') or ''}".strip()

	summary = _fallback_summary_text(customer_label, anchor_label, status_map)
	blocker = _fallback_blocker_text(exceptions, status_map)
	next_action = _fallback_next_action_text(exceptions, status_map)
	customer_reply = _fallback_customer_reply_text(customer_label, status_map, exceptions, next_action)

	return {
		"state": "ready",
		"query": result.get("query"),
		"anchor": result.get("anchor"),
		"source": "fallback",
		"engine": "structured_inquiry_brief",
		"assist": {
			"summary": summary,
			"blocker_explanation": blocker,
			"next_action": next_action,
			"customer_reply": customer_reply,
			"confidence_note": "Built from linked ERP documents visible in the current permission scope.",
		},
	}


def _fallback_summary_text(
	customer_label: str,
	anchor_label: str,
	status_map: dict[str, str],
) -> str:
	parts = [f"{customer_label} is currently anchored on {anchor_label}."]
	for label in ("Sales Order", "Delivery", "Invoice", "Payment", "Return"):
		value = str(status_map.get(label) or "").strip()
		if value:
			parts.append(f"{label}: {value}.")
	return " ".join(parts[:4])


def _fallback_blocker_text(
	exceptions: list[dict[str, object]],
	status_map: dict[str, str],
) -> str:
	if exceptions:
		primary = next(
			(item for item in exceptions if str(item.get("severity") or "").strip() == "blocker"),
			exceptions[0],
		)
		label = str(primary.get("label") or "Exception").strip()
		detail = str(primary.get("detail") or "").strip()
		return f"{label}: {detail}".strip(": ")

	approval = str(status_map.get("Approval / Blocker") or "").strip()
	if approval:
		return approval
	return "No active commercial blocker is visible in the linked chain right now."


def _fallback_next_action_text(
	exceptions: list[dict[str, object]],
	status_map: dict[str, str],
) -> str:
	for item in exceptions:
		severity = str(item.get("severity") or "").strip()
		label = str(item.get("label") or "").strip().lower()
		if severity == "blocker":
			return "Review the pending approval or exception state before confirming any new commitment to the customer."
		if "overdue invoice" in label:
			return "Coordinate with accounts on settlement status and update the customer with a clear payment follow-up message."
		if "return" in label:
			return "Review the linked return records with operations or finance before giving the customer the next commitment."

	delivery = str(status_map.get("Delivery") or "").strip().lower()
	invoice = str(status_map.get("Invoice") or "").strip().lower()
	payment = str(status_map.get("Payment") or "").strip().lower()
	if "not yet created" in delivery or "not linked" in delivery:
		return "Check delivery scheduling or fulfillment handoff with operations before replying to the customer."
	if "need payment" in payment or "settlement" in payment or "outstanding" in invoice:
		return "Confirm current invoice and payment status with accounts before giving a collection-related answer."
	return "Use the linked chain to confirm the latest status and continue the normal customer follow-up."


def _fallback_customer_reply_text(
	customer_label: str,
	status_map: dict[str, str],
	exceptions: list[dict[str, object]],
	next_action: str,
) -> str:
	delivery = str(status_map.get("Delivery") or "").strip()
	invoice = str(status_map.get("Invoice") or "").strip()
	payment = str(status_map.get("Payment") or "").strip()
	blocker_line = _fallback_blocker_text(exceptions, status_map)

	reply_parts = [f"I checked the latest records for {customer_label}."]
	if delivery:
		reply_parts.append(f"Delivery status: {delivery}.")
	if invoice:
		reply_parts.append(f"Invoice status: {invoice}.")
	if payment:
		reply_parts.append(f"Payment status: {payment}.")
	if blocker_line and not blocker_line.lower().startswith("no active"):
		reply_parts.append(f"Current issue to note: {blocker_line}.")
	reply_parts.append(f"Next step on our side: {next_action}")
	return " ".join(reply_parts[:5])


def _generate_customer_inquiry_assist_via_runtime(
	result: dict[str, object],
	fallback: dict[str, object],
) -> dict[str, object] | None:
	if build_artifact_narrative_context is None or narrate_governed_artifact is None:
		return None

	query = str(result.get("query") or "").strip()
	request_id = str(uuid.uuid4())
	context_payload = _build_customer_inquiry_ai_context(result)
	artifact_context = build_artifact_narrative_context(
		request_id=request_id,
		artifact_payload=_customer_inquiry_artifact_payload(result),
		rendered_response_payload=_customer_inquiry_rendered_payload(result),
		response_policy={
			"answer_style": "concise_operational",
			"preferred_formats": ["json_only"],
			"max_paragraph_sentences": 2,
		},
		validation_payload={},
	)
	user_prompt = (
		f"Customer inquiry query: {query or 'n/a'}\n\n"
		"You are writing a concise sales-console assist brief from a governed inquiry artifact.\n"
		"Use only the governed artifact content. Do not invent missing commercial steps.\n"
		"If a linked payment, quotation, order, or delivery record is not visible in the governed chain, describe it as not visible in the chain, not as missing or omitted from the system.\n"
		"Do not imply process failure unless the governed artifact explicitly shows a blocker, exception, overdue state, or cancellation.\n"
		"Produce a JSON object only with this structure:\n"
		"{\n"
		'  "summary": "2-4 sentence operational summary",\n'
		'  "blocker_explanation": "clear explanation of the most important blocker or say none visible",\n'
		'  "next_action": "single recommended next action for staff",\n'
		'  "customer_reply": "short customer-facing reply draft in plain business language",\n'
		'  "confidence_note": "one sentence about scope or visibility limitations"\n'
		"}\n\n"
		f"Governed inquiry context JSON:\n{json.dumps(context_payload, default=str, ensure_ascii=True, indent=2)}"
	)

	try:
		runtime_payload = narrate_governed_artifact(
			session_id=f"sales-console-inquiry-{frappe.session.user}",
			user_id=frappe.session.user,
			site_name=str(getattr(frappe.local, "site", "") or ""),
			message=user_prompt,
			request_id=request_id,
			artifact_context=artifact_context,
			response_policy={
				"answer_style": "concise_operational",
				"preferred_formats": ["json_only"],
				"max_paragraph_sentences": 2,
			},
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Sales Console AI Assist Error")
		return None

	if not isinstance(runtime_payload, dict) or not bool(runtime_payload.get("ok")):
		return None

	answer_text = str(runtime_payload.get("answer_text") or "").strip()
	parsed = _extract_json_object(answer_text)
	if not isinstance(parsed, dict):
		return None

	assist = {}
	for key in ("summary", "blocker_explanation", "next_action", "customer_reply", "confidence_note"):
		value = str(parsed.get(key) or "").strip()
		if value:
			assist[key] = value

	if not all(assist.get(key) for key in ("summary", "blocker_explanation", "next_action", "customer_reply")):
		return None

	assist = _normalize_customer_inquiry_ai_assist(assist, result)

	return {
		"state": "ready",
		"query": result.get("query"),
		"anchor": result.get("anchor"),
		"source": "ai",
		"engine": str(((runtime_payload.get("agent_meta") or {}).get("engine")) or "qwen_runtime"),
		"assist": {
			"summary": assist["summary"],
			"blocker_explanation": assist["blocker_explanation"],
			"next_action": assist["next_action"],
			"customer_reply": assist["customer_reply"],
			"confidence_note": assist.get("confidence_note")
				or "Generated from the visible ERP inquiry chain for the current user scope.",
		},
	}


def _build_customer_inquiry_ai_context(result: dict[str, object]) -> dict[str, object]:
	return {
		"primary_match": result.get("primary_match") if isinstance(result.get("primary_match"), dict) else {},
		"customer_summary": result.get("customer_summary") if isinstance(result.get("customer_summary"), dict) else {},
		"document_flow": list(result.get("document_flow") or []),
		"current_status": list(result.get("current_status") or []),
		"exceptions": list(result.get("exceptions") or []),
		"related_documents": [
			{
				"doctype": item.get("doctype"),
				"name": item.get("name"),
				"status": item.get("status"),
			}
			for item in list(result.get("related_documents") or [])[:8]
			if isinstance(item, dict)
		],
	}


def _customer_inquiry_artifact_payload(result: dict[str, object]) -> dict[str, object]:
	anchor = result.get("anchor") if isinstance(result.get("anchor"), dict) else {}
	return {
		"family_id": "sales_console_customer_inquiry",
		"source_reports": ["Sales Console Customer Inquiry"],
		"warnings": [],
		"anchor_doctype": anchor.get("doctype"),
		"anchor_name": anchor.get("name"),
		"query": result.get("query"),
	}


def _customer_inquiry_rendered_payload(result: dict[str, object]) -> dict[str, object]:
	status_rows = list(result.get("current_status") or [])
	exceptions = list(result.get("exceptions") or [])
	related = list(result.get("related_documents") or [])
	primary = result.get("primary_match") if isinstance(result.get("primary_match"), dict) else {}
	customer = result.get("customer_summary") if isinstance(result.get("customer_summary"), dict) else {}

	return {
		"title": "Sales Console Customer Inquiry",
		"family_id": "sales_console_customer_inquiry",
		"source_reports": ["Sales Console Customer Inquiry"],
		"blocks": [
			{
				"block_type": "summary_table",
				"title": "Primary Match",
				"columns": ["Field", "Value"],
				"rows": [
					["Document", f"{primary.get('doctype') or ''} {primary.get('name') or ''}".strip()],
					["Status", str(primary.get("status") or "").strip()],
					["Customer", str(customer.get("name") or primary.get("customer") or "").strip()],
				],
			},
			{
				"block_type": "summary_table",
				"title": "Current Status",
				"columns": ["Area", "Value"],
				"rows": [
					[str(item.get("label") or "").strip(), str(item.get("value") or "").strip()]
					for item in status_rows
					if isinstance(item, dict)
				],
			},
			{
				"block_type": "bullet_list",
				"title": "Exceptions",
				"items": [
					f"{str(item.get('label') or '').strip()}: {str(item.get('detail') or '').strip()}".strip(": ")
					for item in exceptions
					if isinstance(item, dict)
				] or ["No active commercial exception is visible in the linked chain."],
			},
			{
				"block_type": "bullet_list",
				"title": "Related Documents",
				"items": [
					f"{str(item.get('doctype') or '').strip()} {str(item.get('name') or '').strip()} ({str(item.get('status') or '').strip()})".strip()
					for item in related[:8]
					if isinstance(item, dict)
				],
			},
		],
	}


def _extract_json_object(text: str) -> dict[str, object] | None:
	raw = str(text or "").strip()
	if not raw:
		return None
	candidates = [raw]
	match = re.search(r"\{[\s\S]*\}", raw)
	if match:
		candidates.append(match.group(0))
	for candidate in candidates:
		try:
			data = json.loads(candidate)
		except Exception:
			continue
		if isinstance(data, dict):
			return data
	return None


def _normalize_customer_inquiry_ai_assist(
	assist: dict[str, str],
	result: dict[str, object],
) -> dict[str, str]:
	normalized = dict(assist)
	status_map = {
		str(item.get("label") or "").strip(): str(item.get("value") or "").strip()
		for item in list(result.get("current_status") or [])
		if isinstance(item, dict)
	}
	payment_status = str(status_map.get("Payment") or "").strip().lower()
	invoice_status = str(status_map.get("Invoice") or "").strip().lower()
	anchor = result.get("primary_match") if isinstance(result.get("primary_match"), dict) else {}
	anchor_name = str(anchor.get("name") or "").strip()
	is_partly_paid = "partly paid" in invoice_status or "partly settled" in payment_status
	is_fully_paid = (
		not is_partly_paid
		and ("fully settled" in payment_status or "latest status: paid" in invoice_status)
	)

	if is_partly_paid:
		normalized["next_action"] = (
			"If the customer needs the latest balance position, verify the related finance record and confirm the remaining amount before replying."
		)
		if anchor_name:
			normalized["customer_reply"] = (
				f"Hi there - invoice {anchor_name} is partly paid in our system and a balance is still pending. "
				"If you need the latest balance or payment confirmation, we can verify the related finance record and share the confirmed position with you."
			)
		else:
			normalized["customer_reply"] = (
				"The invoice is partly paid in our system and a balance is still pending. If you need the latest balance or payment confirmation, we can verify the related finance record and share the confirmed position with you."
			)
	elif is_fully_paid:
		normalized["next_action"] = (
			"If the customer needs a copy of the invoice or settlement proof, verify the related finance record and share the confirmed document."
		)
		if anchor_name:
			normalized["customer_reply"] = (
				f"Hi there - invoice {anchor_name} is recorded as paid in our system. "
				"If you need a copy of the invoice or payment confirmation, we can verify the related finance record and share it with you."
			)
		else:
			normalized["customer_reply"] = (
				"The invoice is recorded as paid in our system. If you need a copy of the invoice or payment confirmation, we can verify the related finance record and share it with you."
			)

	return normalized
