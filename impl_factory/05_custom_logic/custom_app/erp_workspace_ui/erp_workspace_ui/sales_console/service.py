from __future__ import annotations

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import get_fullname, getdate, now_datetime, nowdate


TERMINAL_SALES_ORDER_STATUSES = ("Completed", "Closed", "Cancelled")
WORKFLOW_PENDING_TOKENS = ("pending", "await", "wait", "review", "approval", "approve")
WORKFLOW_NEGATIVE_TOKENS = ("approved", "rejected", "cancel", "closed", "complete")


@frappe.whitelist()
def get_sales_console_bootstrap() -> dict[str, object]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	today = getdate(nowdate())
	context = _build_context()
	scope = _build_scope(context["branch_label"])

	return {
		"context": context,
		"scope": scope,
		"ui_profile": _build_ui_profile(context["role_variant"]),
		"queues": _build_queues(today, scope),
		"insights": _build_insights(scope),
		"fetched_at": str(now_datetime()),
	}


def _build_context() -> dict[str, object]:
	branch_name = _resolve_branch()
	role_variant = _role_variant()
	return {
		"user_display_name": get_fullname(frappe.session.user) or frappe.session.user,
		"primary_role": _primary_sales_role(),
		"role_variant": role_variant,
		"branch_label": branch_name,
		"branch_note": None if branch_name else "not mapped yet for this user",
	}


def _build_scope(branch_name: str | None) -> dict[str, object]:
	if branch_name:
		return {
			"branch_name": branch_name,
			"scope_mode": "branch_filtered",
			"scope_label": f"Branch-filtered where supported: {branch_name}",
		}

	return {
		"branch_name": None,
		"scope_mode": "permission_scope",
		"scope_label": "Permission scope only; no mapped branch detected",
	}


def _build_ui_profile(role_variant: str) -> dict[str, object]:
	profiles = {
		"sales_supervisor": {
			"mode_label": "Supervisor Mode",
			"summary_note": "Prioritize blocker resolution, order risk, and approval visibility.",
			"brief_points": [
				"Start with blocked commercial documents and approval queues.",
				"Review open order risk before customer commitments slip.",
				"Use reports as a management review surface, not as the first stop.",
			],
			"action_order": [
				"new_quotation",
				"new_sales_order",
				"open_customer",
				"new_opportunity",
				"open_item",
			],
			"queue_order": [
				"orders_blocked_by_approval",
				"sales_orders_pending_fulfillment",
				"quotations_waiting_action",
				"expiring_quotations",
				"customer_follow_up_tasks",
			],
			"hidden_actions": [],
			"hidden_insights": [],
			"show_reports": True,
			"section_notes": {
				"work": "Blocker-first review and queue control",
				"reports": "Management review and exception follow-up",
				"insights": "Operational control signals",
			},
		},
		"sales_executive": {
			"mode_label": "Execution Mode",
			"summary_note": "Prioritize active quotations, promised follow-up, and fast customer response.",
			"brief_points": [
				"Start with active quotations and follow-up promises due today.",
				"Move quickly from customer context into quotation or order action.",
				"Use blockers as escalation signals, not as the main work surface.",
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
				"orders_blocked_by_approval",
			],
			"hidden_actions": [],
			"hidden_insights": [],
			"show_reports": True,
			"section_notes": {
				"work": "Execution-first commercial queue",
				"reports": "Deep review after action queues",
				"insights": "Lightweight signals for daily selling work",
			},
		},
		"key_account_sales": {
			"mode_label": "Account Mode",
			"summary_note": "Prioritize customer continuity, open order follow-through, and account-level context.",
			"brief_points": [
				"Open customer context first when preparing for account work.",
				"Track delivery continuity and expiring quotes for strategic accounts.",
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
				"orders_blocked_by_approval",
			],
			"hidden_actions": [],
			"hidden_insights": [],
			"show_reports": True,
			"section_notes": {
				"work": "Account continuity and follow-through",
				"reports": "Customer and account review surfaces",
				"insights": "Account-facing commercial signals",
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
			"hidden_insights": ["credit_risk_flags", "quotations_awaiting_approval"],
			"show_reports": False,
			"section_notes": {
				"work": "Fast counter execution and follow-up",
				"insights": "Simple operational signals for showroom flow",
			},
		},
	}

	return profiles.get(role_variant, profiles["sales_executive"])


def _build_queues(today, scope: dict[str, object]) -> dict[str, dict[str, object]]:
	return {
		"quotations_waiting_action": _quotations_waiting_action_metric(scope),
		"expiring_quotations": _expiring_quotation_metric(today, scope),
		"sales_orders_pending_fulfillment": _open_sales_order_metric(scope),
		"orders_blocked_by_approval": _workflow_pending_metric("Sales Order", scope),
		"customer_follow_up_tasks": _customer_follow_up_metric(scope),
	}


def _build_insights(scope: dict[str, object]) -> dict[str, dict[str, object]]:
	return {
		"quotations_awaiting_approval": _workflow_pending_metric("Quotation", scope),
		"open_orders": _open_sales_order_metric(
			scope,
			note="Live open order count within current user and branch scope where supported.",
		),
		"credit_risk_flags": _unavailable_metric(
			"Reserved for finance-approved credit exposure contract."
		),
		"customers_needing_follow_up": _customer_follow_up_metric(
			scope,
			note="Live follow-up task count where current task assignment fields are available."
		),
	}


def _quotations_waiting_action_metric(scope: dict[str, object]) -> dict[str, object]:
	if not _can_read("Quotation"):
		return _access_metric("Quotation")

	if "status" not in _fieldnames("Quotation"):
		return _unavailable_metric("Quotation status field is not available in this site.")

	filters, scope_note = _apply_scope_filters(
		"Quotation",
		[
			["docstatus", "!=", 2],
			["status", "in", ["Draft", "Open"]],
		],
		scope,
	)
	value = _count_records("Quotation", filters)
	return _live_metric(value, f"Live quotation count for draft and open sales work. {scope_note}")


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
	if not _can_read("Sales Order"):
		return _access_metric("Sales Order")

	fields = _fieldnames("Sales Order")
	filters = [["docstatus", "!=", 2]]
	if "status" in fields:
		filters.append(["status", "not in", list(TERMINAL_SALES_ORDER_STATUSES)])

	filters, scope_note = _apply_scope_filters("Sales Order", filters, scope)
	value = _count_records("Sales Order", filters)
	base_note = note or "Live sales order count excluding terminal states."
	return _live_metric(value, f"{base_note} {scope_note}")


def _workflow_pending_metric(doctype: str, scope: dict[str, object]) -> dict[str, object]:
	if not _can_read(doctype):
		return _access_metric(doctype)

	if "workflow_state" not in _fieldnames(doctype):
		return _unavailable_metric(f"{doctype} does not expose workflow_state on this site.")

	states = _workflow_states(doctype)
	matching_states = [state for state in states if _looks_like_pending_workflow(state)]
	if not matching_states:
		return _unavailable_metric(
			f"No pending approval workflow states detected for {doctype}."
		)

	filters, scope_note = _apply_scope_filters(
		doctype,
		[["workflow_state", "in", matching_states]],
		scope,
	)
	value = _count_records(doctype, filters)
	return _live_metric(
		value,
		f"Live workflow count using detected states: {', '.join(sorted(matching_states))}. {scope_note}",
	)


def _customer_follow_up_metric(scope: dict[str, object], note: str | None = None) -> dict[str, object]:
	if not _can_read("ToDo"):
		return _access_metric("ToDo")

	fields = _fieldnames("ToDo")
	assignee_field = None
	for candidate in ("allocated_to", "assigned_to"):
		if candidate in fields:
			assignee_field = candidate
			break

	if not assignee_field:
		return _unavailable_metric("Current ToDo assignment field is not available for follow-up counting.")

	filters = [
		[assignee_field, "=", frappe.session.user],
		["status", "!=", "Closed"],
	]
	if "reference_type" in fields:
		filters.append(["reference_type", "in", ["Customer", "Quotation", "Sales Order"]])

	filters, scope_note = _apply_scope_filters("ToDo", filters, scope)
	value = _count_records("ToDo", filters)
	return _live_metric(
		value,
		f"{note or 'Live follow-up task count assigned to the current user.'} {scope_note}",
	)


def _resolve_branch() -> str | None:
	user_fields = _fieldnames("User")
	for fieldname in ("branch", "default_branch"):
		if fieldname in user_fields:
			branch_name = frappe.db.get_value("User", frappe.session.user, fieldname)
			if branch_name:
				return branch_name

	if _doctype_exists("Employee") and {"user_id", "branch"}.issubset(_fieldnames("Employee")):
		return frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "branch")

	return None


def _primary_sales_role() -> str:
	roles = set(frappe.get_roles(frappe.session.user))
	for role in (
		"Sales Supervisor",
		"Sales Executive",
		"Key Account Sales",
		"Sales User",
		"Sales Manager",
	):
		if role in roles:
			return role
	return "Sales"


def _role_variant() -> str:
	roles = {role.lower() for role in frappe.get_roles(frappe.session.user)}
	if any("showroom" in role for role in roles):
		return "showroom_sales"
	if "key account sales" in roles:
		return "key_account_sales"
	if "sales supervisor" in roles or "sales manager" in roles:
		return "sales_supervisor"
	if "sales executive" in roles or "sales user" in roles:
		return "sales_executive"
	return "sales_executive"


def _workflow_states(doctype: str) -> list[str]:
	rows = frappe.get_list(
		doctype,
		fields=["workflow_state"],
		filters=[["workflow_state", "is", "set"]],
		order_by="modified desc",
		page_length=100,
	)
	seen = []
	for row in rows:
		state = row.get("workflow_state")
		if state and state not in seen:
			seen.append(state)
	return seen


def _looks_like_pending_workflow(value: str) -> bool:
	lowered = value.lower()
	if any(token in lowered for token in WORKFLOW_NEGATIVE_TOKENS):
		return False
	return any(token in lowered for token in WORKFLOW_PENDING_TOKENS)


def _apply_scope_filters(
	doctype: str,
	filters: list[list[object]],
	scope: dict[str, object],
) -> tuple[list[list[object]], str]:
	scoped_filters = list(filters)
	branch_name = scope.get("branch_name")
	if not branch_name:
		return scoped_filters, "Using permission scope because no mapped branch is available."

	fields = _fieldnames(doctype)
	if "branch" in fields:
		scoped_filters.append(["branch", "=", branch_name])
		return scoped_filters, f"Branch scope applied: {branch_name}."

	return scoped_filters, f"Branch context detected ({branch_name}), but {doctype} is not branch-filterable here."


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
