from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime, nowdate

from erp_workspace_ui.workspace_registry import get_warehouse_workspace_definition


WAREHOUSE_ROLES = frozenset({"Warehouse Manager", "Warehouse User", "Stock Manager", "Stock User"})
WAREHOUSE_SUPPORT_ROLES = frozenset({"System Manager"})
WAREHOUSE_ACCESS_ROLES = WAREHOUSE_ROLES | WAREHOUSE_SUPPORT_ROLES


def ensure_authenticated() -> None:
	if getattr(frappe.session, "user", None) == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)


def current_user_roles(user: str | None = None) -> set[str]:
	try:
		return set(frappe.get_roles(user or getattr(frappe.session, "user", None)))
	except Exception:
		return set()


def has_warehouse_access(context: dict[str, object] | None = None) -> bool:
	roles = set(context.get("roles") or []) if context and "roles" in context else current_user_roles()
	return bool(roles.intersection(WAREHOUSE_ACCESS_ROLES))


def build_context() -> dict[str, object]:
	roles = sorted(current_user_roles())
	return {
		"user": getattr(frappe.session, "user", None),
		"roles": roles,
		"role_family": "Warehouse",
		"role_variant": _role_variant(roles),
		"has_warehouse_access": bool(set(roles).intersection(WAREHOUSE_ACCESS_ROLES)),
		"can_view_valuation": False,
	}


def _role_variant(roles: list[str]) -> str:
	role_set = set(roles)
	if role_set.intersection({"Warehouse Manager", "Stock Manager"}):
		return "warehouse_manager"
	if role_set.intersection({"Warehouse User", "Stock User"}):
		return "warehouse_user"
	if "System Manager" in role_set:
		return "system_manager"
	return "restricted"


def warehouse_workspace_public_context() -> dict[str, object]:
	workspace = get_warehouse_workspace_definition()
	return {
		"workspace_id": workspace.get("workspace_id"),
		"status": workspace.get("status"),
		"title": workspace.get("title"),
		"mode_label": workspace.get("mode_label"),
		"role_family": workspace.get("role_family"),
		"routes": workspace.get("routes"),
		"methods": workspace.get("methods"),
		"sidebar": workspace.get("sidebar"),
		"search": workspace.get("search") or {},
	}


def state(kind: str, title: str, detail: str) -> dict[str, str]:
	return {"kind": kind, "title": title, "detail": detail}


def restricted_state() -> dict[str, str]:
	return state(
		"restricted",
		"Warehouse Console is restricted",
		"This page is available only to Warehouse roles.",
	)


def ready_state() -> dict[str, str]:
	return state(
		"ready",
		"Warehouse Console ready",
		"Stock visibility and warehouse posture are available for review.",
	)


def build_sidebar(context: dict[str, object] | None = None) -> dict[str, object]:
	workspace = get_warehouse_workspace_definition()
	sidebar = workspace.get("sidebar") or {}
	items = list(workspace.get("fallback_items") or []) if not context or has_warehouse_access(context) else []
	payload_state = ready_state() if not context or has_warehouse_access(context) else restricted_state()
	return {
		"workspace_id": workspace.get("workspace_id"),
		"title": workspace.get("title"),
		"mode_label": workspace.get("mode_label"),
		"scope_label": "Stock workbench" if not context or has_warehouse_access(context) else "Restricted",
		"active_key": sidebar.get("home_key") or "warehouse_console_home",
		"home_key": sidebar.get("home_key") or "warehouse_console_home",
		"items": items,
		"sections": [
			{
				"key": sidebar.get("section_key") or "workspace",
				"label": sidebar.get("section_label") or "Workspace",
				"items": items,
			}
		] if items else [],
		"state": payload_state,
	}


def _base_payload(context: dict[str, object], payload_state: dict[str, str]) -> dict[str, object]:
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"scope": {
			"scope_mode": "warehouse_role_scope" if has_warehouse_access(context) else "restricted",
			"default_routing_enabled": has_warehouse_access(context),
		},
		"state": payload_state,
		"navigation": {"items": list(get_warehouse_workspace_definition().get("fallback_items") or [])},
		"sidebar": build_sidebar(context),
		"kpis": [],
		"sections": [],
		"allowed_actions": [{"key": "refresh", "label": "Refresh", "kind": "read_only"}] if has_warehouse_access(context) else [],
		"action_targets": {},
		"valuation": {"visible": False, "fields": []},
		"fetched_at": str(now_datetime()),
	}


@frappe.whitelist()
def get_warehouse_console_overview() -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	if not has_warehouse_access(context):
		return _base_payload(context, restricted_state())

	payload = _base_payload(context, ready_state())
	kpis = _build_overview_kpis()
	payload["kpis"] = kpis
	payload["sections"] = _build_overview_sections(kpis)
	if not any(_metric_value(metric) for metric in kpis):
		payload["state"] = state(
			"empty",
			"Warehouse Console has no stock activity yet",
			"No warehouse activity is visible for your role right now.",
		)
	return payload


@frappe.whitelist()
def get_warehouse_console_sidebar_context() -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	payload_state = ready_state() if has_warehouse_access(context) else restricted_state()
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"scope": {
			"scope_mode": "warehouse_role_scope" if has_warehouse_access(context) else "restricted",
			"default_routing_enabled": has_warehouse_access(context),
		},
		"state": payload_state,
		"sidebar": build_sidebar(context),
		"fetched_at": str(now_datetime()),
	}


def _build_overview_kpis() -> list[dict[str, object]]:
	return [
		_metric_from_count(
			"active_warehouses",
			"Active Warehouses",
			"Warehouse",
			_active_warehouse_filters(),
			"Warehouse locations available for stock review.",
		),
		_metric_from_count(
			"stocked_items",
			"Stocked Items",
			"Bin",
			[["Bin", "actual_qty", ">", 0]],
			"Item and warehouse positions with stock on hand.",
		),
		_metric_from_count(
			"low_stock",
			"Low Stock",
			"Bin",
			[["Bin", "projected_qty", "<", 0]],
			"Projected quantity below zero.",
		),
		_metric_from_count(
			"receiving_due",
			"Receiving Due",
			"Purchase Order",
			_purchase_order_due_filters(),
			"Submitted purchase orders due for receipt.",
		),
		_metric_from_count(
			"outbound_due",
			"Outbound Due",
			"Pick List",
			_pick_list_open_filters(),
			"Open picking work visible to your role.",
		),
		_metric_from_count(
			"transfer_requests",
			"Transfer Requests",
			"Material Request",
			_transfer_request_filters(),
			"Internal warehouse requests waiting for review.",
		),
	]


def _build_overview_sections(kpis: list[dict[str, object]]) -> list[dict[str, object]]:
	metrics = {cstr(metric.get("key")): metric for metric in kpis}
	low_stock = metrics.get("low_stock") or {}
	receiving = metrics.get("receiving_due") or {}
	outbound = metrics.get("outbound_due") or {}
	transfers = metrics.get("transfer_requests") or {}

	attention_cards = [
		_section_card("low_stock", "Low Stock", low_stock, "No stock issues needing attention."),
		_section_card("receiving_due", "Receiving Due", receiving, "No receiving due today."),
		_section_card("outbound_due", "Outbound Due", outbound, "No outbound work due today."),
	]
	return [
		{
			"key": "needs_attention",
			"title": "Needs Attention",
			"summary": "Warehouse work that may need review today.",
			"empty_message": "No stock issues needing attention.",
			"cards": attention_cards[:3],
		},
		{
			"key": "inbound_work",
			"title": "Inbound Work",
			"summary": "Receiving posture from visible purchase activity.",
			"empty_message": "No receiving due today.",
			"cards": [_section_card("receiving_due", "Receiving Due", receiving, "No receiving due today.")],
		},
		{
			"key": "outbound_work",
			"title": "Outbound Work",
			"summary": "Picking posture visible to Warehouse roles.",
			"empty_message": "No outbound work due today.",
			"cards": [_section_card("outbound_due", "Outbound Due", outbound, "No outbound work due today.")],
		},
		{
			"key": "stock_health",
			"title": "Stock Health",
			"summary": "Stocked items and projected shortages.",
			"empty_message": "No stock issues needing attention.",
			"cards": [
				_section_card("stocked_items", "Stocked Items", metrics.get("stocked_items") or {}, "No stocked items visible."),
				_section_card("low_stock", "Low Stock", low_stock, "No stock issues needing attention."),
			],
		},
		{
			"key": "movement_watch",
			"title": "Movement Watch",
			"summary": "Internal transfer demand visible to Warehouse roles.",
			"empty_message": "No transfer requests needing review.",
			"cards": [_section_card("transfer_requests", "Transfer Requests", transfers, "No transfer requests needing review.")],
		},
	]


def _section_card(key: str, title: str, metric: dict[str, object], empty_message: str) -> dict[str, object]:
	value = _metric_value(metric)
	state_value = cstr(metric.get("state") or "unavailable")
	note = cstr(metric.get("note") or metric.get("meta") or "")
	return {
		"key": key,
		"title": title,
		"value": value,
		"state": state_value,
		"note": note if state_value == "live" else note or "Not available for your role.",
		"empty_message": empty_message,
	}


def _metric_from_count(
	key: str,
	label: str,
	doctype: str,
	filters: list | dict | None,
	meta: str,
) -> dict[str, object]:
	if not _can_read(doctype):
		return _metric(key, label, None, "Not available for your role.", "unavailable")
	count = _safe_count(doctype, filters)
	return _metric(key, label, count, meta, "live")


def _metric(key: str, label: str, value: int | None, note: str, state_value: str) -> dict[str, object]:
	return {
		"key": key,
		"label": label,
		"value": value,
		"note": note,
		"meta": note,
		"state": state_value,
		"badgeClass": "attention" if state_value == "live" and value else "review",
	}


def _metric_value(metric: dict[str, object]) -> int:
	try:
		return int(metric.get("value") or 0)
	except Exception:
		return 0


def _safe_count(doctype: str, filters: list | dict | None = None) -> int:
	try:
		return int(frappe.db.count(doctype, filters=filters or {}))
	except Exception:
		try:
			return len(frappe.get_all(doctype, filters=filters or {}, fields=["name"], limit_page_length=1_000))
		except Exception:
			return 0


def _can_read(doctype: str) -> bool:
	try:
		return bool(frappe.has_permission(doctype, ptype="read"))
	except Exception:
		return False


def _has_field(doctype: str, fieldname: str) -> bool:
	try:
		return bool(frappe.get_meta(doctype).has_field(fieldname))
	except Exception:
		return False


def _active_warehouse_filters() -> list[list[object]]:
	filters: list[list[object]] = []
	if _has_field("Warehouse", "disabled"):
		filters.append(["Warehouse", "disabled", "=", 0])
	if _has_field("Warehouse", "is_group"):
		filters.append(["Warehouse", "is_group", "=", 0])
	return filters


def _purchase_order_due_filters() -> list[list[object]]:
	today = nowdate()
	filters: list[list[object]] = [["Purchase Order", "docstatus", "=", 1]]
	if _has_field("Purchase Order", "status"):
		filters.append(["Purchase Order", "status", "not in", ["Completed", "Closed", "Cancelled"]])
	if _has_field("Purchase Order", "per_received"):
		filters.append(["Purchase Order", "per_received", "<", 100])
	if _has_field("Purchase Order", "schedule_date"):
		filters.append(["Purchase Order", "schedule_date", "<=", today])
	return filters


def _pick_list_open_filters() -> list[list[object]]:
	filters: list[list[object]] = []
	if _has_field("Pick List", "docstatus"):
		filters.append(["Pick List", "docstatus", "<", 2])
	if _has_field("Pick List", "status"):
		filters.append(["Pick List", "status", "not in", ["Completed", "Cancelled"]])
	return filters


def _transfer_request_filters() -> list[list[object]]:
	filters: list[list[object]] = [["Material Request", "docstatus", "=", 1]]
	if _has_field("Material Request", "material_request_type"):
		filters.append(["Material Request", "material_request_type", "in", ["Material Transfer", "Material Issue", "Material Receipt"]])
	if _has_field("Material Request", "status"):
		filters.append(["Material Request", "status", "not in", ["Completed", "Cancelled", "Stopped"]])
	return filters
