from __future__ import annotations

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import get_fullname, getdate, now_datetime, nowdate


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
		"queues": _build_queues(today, scope),
		"insights": _build_insights(scope),
		"navigation": _build_navigation(today, context, scope),
		"fetched_at": str(now_datetime()),
	}


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


def _build_scope(context: dict[str, object]) -> dict[str, object]:
	branch_name = context.get("branch_label")
	role_variant = context.get("role_variant")
	employee_name = context.get("employee_name")

	if role_variant == "sales_supervisor":
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
			"hidden_insights": ["quotations_awaiting_approval"],
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
			"hidden_insights": ["quotations_awaiting_approval"],
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
				"orders_blocked_by_approval",
				"sales_orders_pending_fulfillment",
				"quotations_waiting_action",
				"expiring_quotations",
				"customer_follow_up_tasks",
			],
			"hidden_actions": ["new_quotation", "new_sales_order", "new_opportunity"],
			"hidden_insights": [],
			"show_reports": True,
			"section_notes": {
				"work": "Review escalations and sales-side exceptions",
				"reports": "Management review surfaces",
				"insights": "Approval and pipeline summary",
			},
		},
	}

	return profiles.get(role_variant, profiles["sales_executive"])


def _build_queues(today, scope: dict[str, object]) -> dict[str, dict[str, object]]:
	return {
		"quotations_waiting_action": _quotations_waiting_action_metric(scope),
		"expiring_quotations": _expiring_quotation_metric(today, scope),
		"sales_orders_pending_fulfillment": _open_sales_order_metric_with_options(
			scope,
			exclude_pending_workflow=True,
		),
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


def _build_navigation(today, context: dict[str, object], scope: dict[str, object]) -> dict[str, dict[str, object]]:
	return {
		"actions": {
			"new_opportunity": {"kind": "new_doc", "doctype": "Opportunity"},
			"new_quotation": {"kind": "new_doc", "doctype": "Quotation"},
			"new_sales_order": {"kind": "new_doc", "doctype": "Sales Order"},
			"open_customer": _customer_list_target(context, scope),
			"open_item": _item_list_target(),
		},
		"insights": {
			"quotations_awaiting_approval": _quotation_approval_target(scope),
			"open_orders": _open_sales_order_target(scope),
		},
		"queues": {
			"orders_blocked_by_approval": _blocked_sales_order_target(scope),
			"sales_orders_pending_fulfillment": _pending_fulfillment_target(scope),
			"quotations_waiting_action": _actionable_quotation_target(scope),
			"expiring_quotations": _expiring_quotation_target(today, scope),
			"customer_follow_up_tasks": _follow_up_target(scope),
		},
		"reports": {
			"sales_analytics": _report_target("Sales Analytics"),
			"customer_wise_sales_history": _report_target("Customer-wise Sales History"),
			"item_wise_sales_register": _report_target("Item-wise Sales Register"),
			"open_orders": _open_sales_order_target(scope),
		},
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


def _report_target(report_name: str, filters: dict[str, object] | None = None) -> dict[str, object]:
	target = {"kind": "report", "report_name": report_name}
	if filters:
		target["filters"] = filters
	return target


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
		filters.append(["reference_type", "in", ["Customer", "Lead", "Opportunity", "Quotation", "Sales Order"]])

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
		"sales_supervisor": "Sales Manager",
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
	if "sales supervisor" in roles or "sales manager" in roles:
		return "sales_supervisor"
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

	seen = []
	for workflow_row in workflows:
		workflow_name = workflow_row.get("name")
		if not workflow_name:
			continue
		try:
			workflow = frappe.get_doc("Workflow", workflow_name)
		except (frappe.DoesNotExistError, frappe.PermissionError, frappe.DataError):
			continue

		for state_row in getattr(workflow, "states", []):
			state = getattr(state_row, "state", None)
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
