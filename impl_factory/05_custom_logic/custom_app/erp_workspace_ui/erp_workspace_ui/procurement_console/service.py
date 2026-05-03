from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

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
			"default_routing_enabled": False,
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
			"default_routing_enabled": False,
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
	return {
		"state": "unavailable",
		"query": needle,
		"message": "Procurement Console search is not available yet.",
		"results": [],
		"limit": limit,
	}


def _build_phase1_overview() -> dict[str, object]:
	from . import purchase_orders, requests, sourcing, suppliers

	requests_to_source = requests.count_purchase_requests_to_source()
	requests_total = requests.count_purchase_request_directory()
	orders_open = purchase_orders.count_purchase_orders_open()
	orders_total = purchase_orders.count_purchase_order_directory()
	orders_pending_approval = purchase_orders.count_purchase_orders_pending_approval()
	orders_late = purchase_orders.count_purchase_orders_late_or_unreceived()
	suppliers_total = suppliers.count_visible_suppliers()
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
				"note": "Open Purchase Orders past required date and not fully received.",
				"badgeClass": "attention" if orders_late else "review",
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
				"note": "Read-only supplier records visible to this user.",
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
		},
		"queues": {
			"requests_to_source": requests_to_source,
			"purchase_orders_pending_approval": orders_pending_approval,
			"purchase_orders_late_or_unreceived": orders_late,
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
				"description": "Read-only comparison of quoted supplier prices and validity.",
			}
		],
	}
