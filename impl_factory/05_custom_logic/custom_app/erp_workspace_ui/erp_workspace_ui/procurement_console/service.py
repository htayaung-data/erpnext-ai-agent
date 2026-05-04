from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

from erp_workspace_ui.workspace_registry import get_procurement_workspace_definition


PROCUREMENT_ROLES = frozenset({"Purchase User", "Purchase Manager", "Purchase Master Manager"})


def ensure_authenticated() -> None:
	if getattr(frappe.session, "user", None) == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)


def current_user_roles(user: str | None = None) -> set[str]:
	try:
		return set(frappe.get_roles(user or getattr(frappe.session, "user", None)))
	except Exception:
		return set()


def has_procurement_access(context: dict[str, object] | None = None) -> bool:
	if context and "roles" in context:
		roles = set(context.get("roles") or [])
	else:
		roles = current_user_roles()
	return bool(roles.intersection(PROCUREMENT_ROLES))


def build_context() -> dict[str, object]:
	roles = sorted(current_user_roles())
	return {
		"user": getattr(frappe.session, "user", None),
		"roles": roles,
		"role_family": "Procurement",
		"role_variant": _role_variant(roles),
		"has_procurement_access": bool(set(roles).intersection(PROCUREMENT_ROLES)),
	}


def _role_variant(roles: list[str]) -> str:
	role_set = set(roles)
	if "Purchase Master Manager" in role_set:
		return "purchase_master_manager"
	if "Purchase Manager" in role_set:
		return "purchase_manager"
	if "Purchase User" in role_set:
		return "purchase_user"
	return "restricted"


def procurement_workspace_public_context() -> dict[str, object]:
	workspace = get_procurement_workspace_definition()
	return {
		"workspace_id": workspace.get("workspace_id"),
		"status": workspace.get("status"),
		"title": workspace.get("title"),
		"mode_label": workspace.get("mode_label"),
		"role_family": workspace.get("role_family"),
		"routes": workspace.get("routes"),
		"methods": workspace.get("methods"),
		"sidebar": workspace.get("sidebar"),
	}


def state(kind: str, title: str, detail: str) -> dict[str, str]:
	return {
		"kind": kind,
		"title": title,
		"detail": detail,
	}


def restricted_state() -> dict[str, str]:
	return state(
		"restricted",
		"Procurement Console is restricted",
		"This workspace is available only to procurement roles.",
	)


def unavailable_state() -> dict[str, str]:
	return state(
		"unavailable",
		"Procurement Console is not available yet",
		"This Procurement Console surface is not available in the current phase.",
	)


def build_sidebar(context: dict[str, object] | None = None) -> dict[str, object]:
	workspace = get_procurement_workspace_definition()
	sidebar = workspace.get("sidebar") or {}
	items = list(workspace.get("fallback_items") or [])
	sidebar_state = state(
		"ready",
		"Procurement Console ready",
		"Buyer workbench queues are available for procurement roles.",
	) if not context or has_procurement_access(context) else restricted_state()
	return {
		"workspace_id": workspace.get("workspace_id"),
		"title": workspace.get("title"),
		"mode_label": workspace.get("mode_label"),
		"scope_label": "Buyer workbench" if not context or has_procurement_access(context) else "Restricted",
		"active_key": sidebar.get("home_key") or "procurement_console_home",
		"home_key": sidebar.get("home_key") or "procurement_console_home",
		"items": items,
		"sections": [
			{
				"key": sidebar.get("section_key") or "workspace",
				"label": sidebar.get("section_label") or "Workspace",
				"items": items,
			}
		],
		"state": sidebar_state,
	}


def _base_payload(context: dict[str, object], payload_state: dict[str, str]) -> dict[str, object]:
	return {
		"workspace": procurement_workspace_public_context(),
		"context": context,
		"scope": {
			"scope_mode": "procurement_role_scope" if has_procurement_access(context) else "restricted",
			"default_routing_enabled": has_procurement_access(context),
		},
		"state": payload_state,
		"navigation": {
			"items": list(get_procurement_workspace_definition().get("fallback_items") or []),
		},
		"sidebar": build_sidebar(context),
		"work": {},
		"directories": {},
		"queues": {},
		"insights": {},
		"reports_catalog": [],
		"create_actions": [],
		"action_targets": {},
		"fetched_at": str(now_datetime()),
	}


@frappe.whitelist()
def get_procurement_console_bootstrap() -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	if not has_procurement_access(context):
		return _base_payload(context, restricted_state())
	payload = _base_payload(context, state(
		"ready",
		"Procurement Console ready",
		"Buyer workbench queues are available for procurement roles.",
	))
	payload.update(_build_phase1_overview())
	payload.update(_build_create_action_payload(context))
	return payload


@frappe.whitelist()
def get_procurement_console_sidebar_context() -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	payload_state = state(
		"ready",
		"Procurement Console ready",
		"Buyer workbench queues are available for procurement roles.",
	) if has_procurement_access(context) else restricted_state()
	return {
		"workspace": procurement_workspace_public_context(),
		"context": context,
		"scope": {
			"scope_mode": "procurement_role_scope" if has_procurement_access(context) else "restricted",
			"default_routing_enabled": has_procurement_access(context),
		},
		"state": payload_state,
		"sidebar": build_sidebar(context),
		"fetched_at": str(now_datetime()),
	}


@frappe.whitelist()
def search_procurement_console_workspace(query: str, limit: int = 12) -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	needle = (query or "").strip()
	if not has_procurement_access(context):
		return {
			"state": "restricted",
			"query": needle,
			"message": "Procurement Console search is restricted to procurement roles.",
			"results": [],
		}
	if len(needle) < 2:
		return {
			"state": "idle",
			"query": needle,
			"message": "Type at least 2 characters to search suppliers, purchase requests, RFQs, quotations, and purchase orders.",
			"results": [],
		}

	results = _build_procurement_workspace_search_results(needle, limit)
	if not results:
		return {
			"state": "empty",
			"query": needle,
			"message": "No visible Procurement Console records match this search yet.",
			"results": [],
		}
	return {
		"state": "ready",
		"query": needle,
		"message": f"{len(results)} Procurement Console result{'s' if len(results) != 1 else ''} found.",
		"results": results,
	}


def _build_procurement_workspace_search_results(query: str, limit: int) -> list[dict[str, object]]:
	from . import common

	per_doctype_limit = max(2, min(8, int(limit or 12)))
	search_plan = [
		{
			"doctype": "Supplier",
			"fields": ["name", "supplier_name", "supplier_group", "modified"],
			"search_fields": ["name", "supplier_name"],
			"queue_key": "supplier_directory",
			"keyword_field": "supplier_name",
			"label_field": "supplier_name",
			"meta_fields": ["supplier_group"],
		},
		{
			"doctype": "Item",
			"fields": ["name", "item_name", "item_group", "modified"],
			"search_fields": ["name", "item_name"],
			"queue_key": "buying_item_directory",
			"keyword_field": "item_name",
			"label_field": "item_name",
			"meta_fields": ["item_group"],
			"filters": [["Item", "is_purchase_item", "=", 1]],
		},
		{
			"doctype": "Material Request",
			"fields": ["name", "title", "material_request_type", "status", "modified"],
			"search_fields": ["name", "title"],
			"queue_key": "purchase_request_directory",
			"keyword_field": "name",
			"label_field": "name",
			"meta_fields": ["title", "status"],
			"filters": [["Material Request", "material_request_type", "=", "Purchase"]],
		},
		{
			"doctype": "Request for Quotation",
			"fields": ["name", "company", "status", "modified"],
			"search_fields": ["name"],
			"queue_key": "rfq_directory",
			"keyword_field": "name",
			"label_field": "name",
			"meta_fields": ["status", "company"],
		},
		{
			"doctype": "Supplier Quotation",
			"fields": ["name", "supplier", "supplier_name", "status", "modified"],
			"search_fields": ["name", "supplier", "supplier_name"],
			"queue_key": "supplier_quotation_directory",
			"keyword_field": "name",
			"label_field": "name",
			"meta_fields": ["supplier_name", "status"],
		},
		{
			"doctype": "Purchase Order",
			"fields": ["name", "supplier", "supplier_name", "status", "modified"],
			"search_fields": ["name", "supplier", "supplier_name"],
			"queue_key": "purchase_order_directory",
			"keyword_field": "name",
			"label_field": "name",
			"meta_fields": ["supplier_name", "status"],
		},
	]
	results: list[dict[str, object]] = []
	seen: set[tuple[str, str]] = set()
	for plan in search_plan:
		if not common.can_read(plan["doctype"]):
			continue
		for row in _search_procurement_rows(plan, query, per_doctype_limit):
			key = (cstr(plan["doctype"]), cstr(row.get("name")))
			if not key[1] or key in seen:
				continue
			seen.add(key)
			results.append(_search_result_from_row(plan, row))
			if len(results) >= int(limit or 12):
				return results
	return results[: int(limit or 12)]


def _search_procurement_rows(plan: dict[str, object], query: str, limit: int) -> list[dict[str, object]]:
	from . import common

	rows: list[dict[str, object]] = []
	base_filters = list(plan.get("filters") or [])
	for fieldname in plan.get("search_fields") or []:
		filters = list(base_filters)
		filters.append([cstr(plan["doctype"]), cstr(fieldname), "like", f"%{query}%"])
		rows.extend(common.get_list(cstr(plan["doctype"]), fields=list(plan.get("fields") or ["name"]), filters=filters, order_by="modified desc", limit=limit))
	return rows


def _search_result_from_row(plan: dict[str, object], row: dict[str, object]) -> dict[str, object]:
	name = cstr(row.get("name")).strip()
	label_field = cstr(plan.get("label_field")).strip()
	keyword_field = cstr(plan.get("keyword_field")).strip()
	label = cstr(row.get(label_field)).strip() or name
	keyword = cstr(row.get(keyword_field)).strip() or name
	meta_parts = [cstr(row.get(field)).strip() for field in plan.get("meta_fields") or []]
	meta = " | ".join(part for part in meta_parts if part)
	return {
		"doctype": plan.get("doctype"),
		"name": name,
		"label": label,
		"meta": meta,
		"target": {"kind": "worklist", "queue_key": plan.get("queue_key"), "filters": {"keyword": keyword}},
	}


def _build_phase1_overview() -> dict[str, object]:
	from . import items, purchase_order_follow_up, purchase_orders, requests, sourcing, suppliers

	requests_to_source = requests.count_purchase_requests_to_source()
	requests_total = requests.count_purchase_request_directory()
	orders_open = purchase_orders.count_purchase_orders_open()
	orders_total = purchase_orders.count_purchase_order_directory()
	orders_pending_approval = purchase_orders.count_purchase_orders_pending_approval()
	orders_follow_up = purchase_order_follow_up.build_purchase_order_follow_up_summary()
	orders_late = orders_follow_up["overdue"]
	orders_due_soon = orders_follow_up["due_soon"]
	orders_partially_received = orders_follow_up["partially_received"]
	orders_not_billed_visibility = orders_follow_up["billing_visibility"]
	orders_supplier_follow_up = orders_follow_up["supplier_follow_up"]
	suppliers_total = suppliers.count_visible_suppliers()
	buying_items_total = items.count_buying_items()
	rfqs_total = sourcing.count_rfq_directory()
	rfqs_awaiting_response = sourcing.count_rfqs_awaiting_supplier_response()
	supplier_quotations_total = sourcing.count_supplier_quotation_directory()
	supplier_quotations_to_compare = sourcing.count_supplier_quotations_to_compare()
	supplier_quotations_expiring = sourcing.count_supplier_quotations_expiring()

	return {
		"work": {
			"requests_to_source": {
				"state": "live",
				"value": requests_to_source,
				"note": "Submitted purchase requests not fully ordered.",
				"badgeClass": "attention" if requests_to_source else "review",
			},
			"purchase_orders_pending_approval": {
				"state": "live",
				"value": orders_pending_approval,
				"note": "Purchase Orders waiting on purchase approval.",
				"badgeClass": "blocker" if orders_pending_approval else "review",
			},
			"purchase_orders_late_or_unreceived": {
				"state": "live",
				"value": orders_late,
				"note": "Submitted Purchase Orders with overdue open item lines.",
				"badgeClass": "attention" if orders_late else "review",
			},
			"purchase_orders_due_soon": {
				"state": "live",
				"value": orders_due_soon,
				"note": "Open item lines due within seven days.",
				"badgeClass": "attention" if orders_due_soon else "review",
			},
			"purchase_orders_overdue": {
				"state": "live",
				"value": orders_late,
				"note": "Open item lines past required date.",
				"badgeClass": "blocker" if orders_late else "review",
			},
			"purchase_orders_partially_received": {
				"state": "live",
				"value": orders_partially_received,
				"note": "Orders with some receipt but incomplete fulfillment.",
				"badgeClass": "attention" if orders_partially_received else "review",
			},
			"purchase_orders_not_billed_visibility": {
				"state": "live",
				"value": orders_not_billed_visibility,
				"note": "Received orders not fully billed; visibility only.",
				"badgeClass": "review",
			},
			"purchase_orders_supplier_follow_up": {
				"state": "live",
				"value": orders_supplier_follow_up,
				"note": "Orders needing buyer follow-up.",
				"badgeClass": "blocker" if orders_supplier_follow_up else "review",
			},
			"purchase_orders_open": {
				"state": "live",
				"value": orders_open,
				"note": "Submitted Purchase Orders still active.",
				"badgeClass": "review",
			},
			"rfqs_awaiting_supplier_response": {
				"state": "live",
				"value": rfqs_awaiting_response,
				"note": "Submitted RFQs with pending supplier responses.",
				"badgeClass": "attention" if rfqs_awaiting_response else "review",
			},
			"supplier_quotations_to_compare": {
				"state": "live",
				"value": supplier_quotations_to_compare,
				"note": "Submitted Supplier Quotations available for comparison.",
				"badgeClass": "attention" if supplier_quotations_to_compare else "review",
			},
			"supplier_quotations_expiring": {
				"state": "live",
				"value": supplier_quotations_expiring,
				"note": "Supplier Quotations expiring within seven days.",
				"badgeClass": "blocker" if supplier_quotations_expiring else "review",
			},
		},
		"directories": {
			"supplier_directory": {
				"state": "live",
				"value": suppliers_total,
				"note": "Supplier records visible to this user.",
				"badgeClass": "review",
			},
			"purchase_request_directory": {
				"state": "live",
				"value": requests_total,
				"note": "Purchase Material Requests visible to this user.",
				"badgeClass": "review",
			},
			"purchase_order_directory": {
				"state": "live",
				"value": orders_total,
				"note": "Purchase Orders visible to this user.",
				"badgeClass": "review",
			},
			"rfq_directory": {
				"state": "live",
				"value": rfqs_total,
				"note": "RFQ records visible to this user.",
				"badgeClass": "review",
			},
			"supplier_quotation_directory": {
				"state": "live",
				"value": supplier_quotations_total,
				"note": "Supplier Quotation records visible to this user.",
				"badgeClass": "review",
			},
			"buying_item_directory": {
				"state": "live",
				"value": buying_items_total,
				"note": "Purchase-enabled items visible to this user.",
				"badgeClass": "review",
			},
		},
		"queues": {
			"requests_to_source": requests_to_source,
			"purchase_orders_pending_approval": orders_pending_approval,
			"purchase_orders_late_or_unreceived": orders_late,
			"purchase_orders_due_soon": orders_due_soon,
			"purchase_orders_overdue": orders_late,
			"purchase_orders_partially_received": orders_partially_received,
			"purchase_orders_not_billed_visibility": orders_not_billed_visibility,
			"purchase_orders_supplier_follow_up": orders_supplier_follow_up,
			"purchase_orders_open": orders_open,
			"rfqs_awaiting_supplier_response": rfqs_awaiting_response,
			"supplier_quotations_to_compare": supplier_quotations_to_compare,
			"supplier_quotations_expiring": supplier_quotations_expiring,
		},
		"insights": {
			"requests_to_source": {
				"state": "live",
				"value": requests_to_source,
				"note": "Need sourcing action.",
			},
			"purchase_orders_pending_approval": {
				"state": "live",
				"value": orders_pending_approval,
				"note": "Need purchase approval review.",
			},
			"purchase_orders_late_or_unreceived": {
				"state": "live",
				"value": orders_late,
				"note": "Need supplier follow-up.",
			},
			"purchase_orders_due_soon": {
				"state": "live",
				"value": orders_due_soon,
				"note": "Need pre-due follow-up.",
			},
			"purchase_orders_overdue": {
				"state": "live",
				"value": orders_late,
				"note": "Need urgent follow-up.",
			},
			"purchase_orders_supplier_follow_up": {
				"state": "live",
				"value": orders_supplier_follow_up,
				"note": "Need buyer follow-up.",
			},
			"supplier_quotations_expiring": {
				"state": "live",
				"value": supplier_quotations_expiring,
				"note": "Need quote validity review.",
			},
		},
		"reports_catalog": [
			{
				"key": "supplier_quotation_comparison",
				"label": "Supplier Quotation Comparison",
				"description": "Governed comparison of quoted supplier prices and validity.",
			}
		],
	}


def _build_create_action_payload(context: dict[str, object]) -> dict[str, object]:
	from . import common

	roles = set(context.get("roles") or [])
	plan = [
		{
			"key": "new_purchase_request",
			"title": "New Purchase Request",
			"doctype": "Material Request",
			"defaults": {"material_request_type": "Purchase"},
			"note": "Starts a Purchase Material Request in ERPNext.",
		},
		{
			"key": "new_rfq",
			"title": "New RFQ",
			"doctype": "Request for Quotation",
			"defaults": {},
			"note": "Starts an ERPNext Request for Quotation.",
		},
		{
			"key": "new_supplier_quotation",
			"title": "New Supplier Quotation",
			"doctype": "Supplier Quotation",
			"defaults": {},
			"note": "Starts an ERPNext Supplier Quotation.",
		},
		{
			"key": "new_purchase_order",
			"title": "New Purchase Order",
			"doctype": "Purchase Order",
			"defaults": {},
			"note": "Starts an ERPNext Purchase Order.",
		},
	]
	if roles.intersection({"Purchase Manager", "Purchase Master Manager"}):
		plan.append(
			{
				"key": "new_supplier",
				"title": "New Supplier",
				"doctype": "Supplier",
				"defaults": {},
				"note": "Uses ERPNext supplier master permissions.",
			}
		)
	if roles.intersection({"Purchase Master Manager", "Item Manager", "Stock Manager", "System Manager"}):
		plan.append(
			{
				"key": "new_item",
				"title": "New Item",
				"doctype": "Item",
				"defaults": {},
				"note": "Uses ERPNext item master permissions.",
			}
		)

	actions: list[dict[str, object]] = []
	targets: dict[str, object] = {}
	for item in plan:
		doctype = cstr(item.get("doctype")).strip()
		if not doctype or not common.can_create(doctype):
			continue
		key = cstr(item.get("key")).strip()
		actions.append(
			{
				"key": key,
				"title": item.get("title"),
				"label": item.get("title"),
				"variant": "primary" if key in {"new_purchase_request", "new_purchase_order"} else "secondary",
				"category": "create",
				"note": item.get("note"),
			}
		)
		targets[key] = {
			"kind": "new_doc",
			"doctype": doctype,
			"defaults": dict(item.get("defaults") or {}),
		}
	return {"create_actions": actions, "action_targets": targets}
