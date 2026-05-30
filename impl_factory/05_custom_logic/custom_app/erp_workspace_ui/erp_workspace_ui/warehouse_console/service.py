from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, flt, getdate, now_datetime, nowdate

from erp_workspace_ui.workspace_registry import get_warehouse_workspace_definition


WAREHOUSE_ROLES = frozenset({"Warehouse Manager", "Warehouse User", "Stock Manager", "Stock User"})
WAREHOUSE_SUPPORT_ROLES = frozenset({"System Manager"})
WAREHOUSE_ACCESS_ROLES = WAREHOUSE_ROLES | WAREHOUSE_SUPPORT_ROLES

INBOUND_QUEUE_KEY = "inbound_receiving"
INBOUND_QUEUE_LIMIT = 50
INBOUND_OVERVIEW_LIMIT = 6
INBOUND_SCAN_LIMIT = 180
INBOUND_HORIZON_DAYS = 14
INBOUND_OPEN_STATUSES = ("To Receive", "To Receive and Bill")
INBOUND_GROUP_ORDER = ("overdue", "due_today", "partially_received", "expected_soon")

OUTBOUND_QUEUE_KEY = "outbound_picking"
OUTBOUND_QUEUE_LIMIT = 50
OUTBOUND_OVERVIEW_LIMIT = 6
OUTBOUND_SCAN_LIMIT = 180
OUTBOUND_HORIZON_DAYS = 14
OUTBOUND_OPEN_STATUSES = ("To Deliver", "To Deliver and Bill")
OUTBOUND_GROUP_ORDER = ("overdue", "due_today", "ready_to_pick", "partially_picked", "needs_stock_review", "expected_soon")

STOCK_EXCEPTIONS_KEY = "stock_exceptions"
STOCK_EXCEPTIONS_LIMIT = 50
STOCK_EXCEPTIONS_SCAN_LIMIT = 220
STOCK_EXCEPTIONS_HORIZON_DAYS = 14
STOCK_EXCEPTIONS_GROUP_ORDER = ("needs_stock_review", "inbound_cover_expected", "urgent_aging", "warehouse_posture_missing")
STOCK_EXCEPTION_REVIEW_DETAIL_KEY = "stock_exception_review"
STOCK_POSTURE_REVIEW_DETAIL_KEY = "stock_posture_review"
STOCK_POSTURE_OUTBOUND_LIMIT = 8
STOCK_POSTURE_INBOUND_LIMIT = 8

MOVEMENT_VISIBILITY_KEY = "movement_visibility"
MOVEMENT_REVIEW_DETAIL_KEY = "movement_review"
MOVEMENT_VISIBILITY_LIMIT = 50
MOVEMENT_VISIBILITY_SCAN_LIMIT = 80
MOVEMENT_VISIBILITY_HORIZON_DAYS = 14
MOVEMENT_VISIBILITY_GROUP_ORDER = ("internal_transfers", "receipts", "issues", "adjustments_repack", "needs_review")
MOVEMENT_REVIEW_LINE_LIMIT = 120
MOVEMENT_CONTEXT_MAX_LENGTH = 512

TRANSFER_VISIBILITY_KEY = "transfer_visibility"
TRANSFER_VISIBILITY_LIMIT = 50
TRANSFER_VISIBILITY_SCAN_LIMIT = 80
TRANSFER_VISIBILITY_HORIZON_DAYS = 14
TRANSFER_VISIBILITY_GROUP_ORDER = ("direct_transfers", "transit_related", "needs_review", "recently_posted")
TRANSFER_VISIBILITY_DATE_WINDOWS = {"today": 0, "last_7_days": 7, "last_14_days": 14}

PURCHASE_ORDER_INBOUND_FIELDS = [
	"name",
	"supplier",
	"supplier_name",
	"transaction_date",
	"schedule_date",
	"status",
	"per_received",
	"set_warehouse",
	"modified",
]

PURCHASE_ORDER_ITEM_INBOUND_FIELDS = [
	"parent",
	"item_code",
	"item_name",
	"schedule_date",
	"expected_delivery_date",
	"qty",
	"received_qty",
	"warehouse",
	"stock_uom",
	"uom",
]

PURCHASE_ORDER_ITEM_DETAIL_FIELDS = [
	"name",
	"parent",
	"idx",
	"item_code",
	"item_name",
	"schedule_date",
	"expected_delivery_date",
	"qty",
	"received_qty",
	"warehouse",
	"stock_uom",
	"uom",
]

PURCHASE_RECEIPT_HISTORY_FIELDS = [
	"name",
	"posting_date",
	"status",
	"docstatus",
	"modified",
]

PURCHASE_RECEIPT_ITEM_HISTORY_FIELDS = [
	"parent",
	"item_code",
	"item_name",
	"qty",
	"warehouse",
	"purchase_order",
	"purchase_order_item",
	"stock_uom",
	"uom",
]

SALES_ORDER_OUTBOUND_FIELDS = [
	"name",
	"customer",
	"customer_name",
	"transaction_date",
	"delivery_date",
	"status",
	"per_delivered",
	"set_warehouse",
	"modified",
]

SALES_ORDER_ITEM_OUTBOUND_FIELDS = [
	"parent",
	"item_code",
	"item_name",
	"delivery_date",
	"qty",
	"delivered_qty",
	"warehouse",
	"stock_uom",
	"uom",
]

SALES_ORDER_ITEM_DETAIL_FIELDS = [
	"name",
	"parent",
	"idx",
	"item_code",
	"item_name",
	"delivery_date",
	"qty",
	"delivered_qty",
	"warehouse",
	"stock_uom",
	"uom",
]

BIN_OUTBOUND_FIELDS = [
	"item_code",
	"warehouse",
	"actual_qty",
	"reserved_qty",
	"projected_qty",
]

STOCK_ENTRY_MOVEMENT_FIELDS = [
	"name",
	"purpose",
	"stock_entry_type",
	"posting_date",
	"posting_time",
	"from_warehouse",
	"to_warehouse",
	"docstatus",
	"modified",
]

STOCK_ENTRY_DETAIL_MOVEMENT_FIELDS = [
	"parent",
	"idx",
	"item_code",
	"item_name",
	"qty",
	"s_warehouse",
	"t_warehouse",
	"stock_uom",
	"uom",
]

STANDARD_SAFE_FIELDS = frozenset({"name", "parent", "idx", "docstatus", "modified", "owner", "creation"})
RECEIVING_DETAIL_LINE_LIMIT = 80
RECEIVING_DETAIL_HISTORY_ITEM_LIMIT = 120
RECEIVING_DETAIL_HISTORY_LIMIT = 8
PICKING_DETAIL_LINE_LIMIT = 80


def ensure_authenticated() -> None:
	if getattr(frappe.session, "user", None) == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)


def _clear_transient_frappe_messages() -> None:
	try:
		if hasattr(frappe.local, "message_log"):
			frappe.local.message_log = []
		response = getattr(frappe.local, "response", None)
		if isinstance(response, dict):
			response.pop("_server_messages", None)
			response.pop("exc", None)
	except Exception:
		pass


def current_user_roles(user: str | None = None) -> set[str]:
	try:
		return set(frappe.get_roles(user or getattr(frappe.session, "user", None)))
	except Exception:
		_clear_transient_frappe_messages()
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
	inbound = _build_inbound_visibility({}, preview_limit=INBOUND_OVERVIEW_LIMIT, row_limit=INBOUND_QUEUE_LIMIT)
	outbound = _build_outbound_visibility({}, preview_limit=OUTBOUND_OVERVIEW_LIMIT, row_limit=OUTBOUND_QUEUE_LIMIT)
	stock_exceptions = _build_stock_exceptions_visibility({}, row_limit=STOCK_EXCEPTIONS_LIMIT)
	kpis = _build_overview_kpis(inbound, outbound)
	payload["kpis"] = kpis
	payload["inbound"] = inbound
	payload["outbound"] = outbound
	payload["stock_exceptions"] = stock_exceptions
	payload["sections"] = _build_overview_sections(kpis, inbound, outbound)
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


def _build_overview_kpis(inbound: dict[str, object] | None = None, outbound: dict[str, object] | None = None) -> list[dict[str, object]]:
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
		_inbound_metric(
			"receiving_due",
			"Receiving Due",
			inbound,
			"due_today",
			"Submitted purchase orders due for review.",
		),
		_outbound_metric(
			"outbound_due",
			"Picking Due",
			outbound,
			"due_today",
			"Submitted sales orders due for warehouse picking review.",
		),
		_metric_from_count(
			"transfer_requests",
			"Transfer Requests",
			"Material Request",
			_transfer_request_filters(),
			"Internal warehouse requests waiting for review.",
		),
	]


def _build_overview_sections(kpis: list[dict[str, object]], inbound: dict[str, object] | None = None, outbound: dict[str, object] | None = None) -> list[dict[str, object]]:
	metrics = {cstr(metric.get("key")): metric for metric in kpis}
	low_stock = metrics.get("low_stock") or {}
	receiving = metrics.get("receiving_due") or {}
	outbound_metric = metrics.get("outbound_due") or {}
	transfers = metrics.get("transfer_requests") or {}
	inbound_cards = _inbound_section_cards(inbound)
	outbound_cards = _outbound_section_cards(outbound)
	overdue_card = next((card for card in inbound_cards if card.get("key") == "overdue"), None)
	outbound_attention_card = next((card for card in outbound_cards if card.get("key") in {"overdue", "due_today"}), None)

	attention_cards = [
		_section_card("low_stock", "Low Stock", low_stock, "No stock issues needing attention."),
		overdue_card or _section_card("receiving_due", "Receiving Due", receiving, "No receiving due today."),
		outbound_attention_card or _section_card("outbound_due", "Picking Due", outbound_metric, "No outbound picking due today."),
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
			"summary": "Expected supplier stock due into warehouse.",
			"empty_message": "No inbound receiving needs attention.",
			"cards": inbound_cards or [_section_card("receiving_due", "Receiving Due", receiving, "No receiving due today.")],
		},
		{
			"key": "outbound_work",
			"title": "Outbound Work",
			"summary": "Picking posture visible to Warehouse roles.",
			"empty_message": "No outbound picking needs attention.",
			"cards": outbound_cards or [_section_card("outbound_due", "Picking Due", outbound_metric, "No outbound picking due today.")],
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


def _inbound_metric(key: str, label: str, inbound: dict[str, object] | None, count_key: str, note: str) -> dict[str, object]:
	payload_state = inbound.get("state") if isinstance(inbound, dict) else {}
	if isinstance(payload_state, dict) and payload_state.get("kind") == "restricted":
		return _metric(key, label, None, "Not available for your role.", "unavailable")
	counts = inbound.get("counts") if isinstance(inbound, dict) else {}
	try:
		value = int((counts or {}).get(count_key) or 0)
	except Exception:
		value = 0
	return _metric(key, label, value, note, "live")


def _outbound_metric(key: str, label: str, outbound: dict[str, object] | None, count_key: str, note: str) -> dict[str, object]:
	payload_state = outbound.get("state") if isinstance(outbound, dict) else {}
	if isinstance(payload_state, dict) and payload_state.get("kind") == "restricted":
		return _metric(key, label, None, "Not available for your role.", "unavailable")
	counts = outbound.get("counts") if isinstance(outbound, dict) else {}
	try:
		value = int((counts or {}).get(count_key) or 0)
	except Exception:
		value = 0
	return _metric(key, label, value, note, "live")


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
		_clear_transient_frappe_messages()
		try:
			return len(frappe.get_all(doctype, filters=filters or {}, fields=["name"], limit_page_length=1_000))
		except Exception:
			_clear_transient_frappe_messages()
			return 0


def _can_read(doctype: str) -> bool:
	try:
		return bool(frappe.has_permission(doctype, ptype="read"))
	except Exception:
		_clear_transient_frappe_messages()
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



@frappe.whitelist()
def get_warehouse_inbound_receiving_queue(
	queue_key: str | None = None,
	filters: str | dict[str, object] | None = None,
) -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	applied_filters = _normalize_filters(filters)
	if not has_warehouse_access(context):
		return _inbound_queue_state_payload(context, restricted_state(), applied_filters)
	if _normalize_queue_key(queue_key) not in {"", INBOUND_QUEUE_KEY}:
		return _inbound_queue_state_payload(
			context,
			state("unavailable", "Inbound receiving unavailable", "This inbound receiving queue is not available."),
			applied_filters,
		)
	inbound = _build_inbound_visibility(applied_filters, preview_limit=INBOUND_QUEUE_LIMIT, row_limit=INBOUND_QUEUE_LIMIT)
	return _inbound_queue_payload(context, inbound, applied_filters)


@frappe.whitelist()
def get_warehouse_outbound_picking_queue(
	queue_key: str | None = None,
	filters: str | dict[str, object] | None = None,
) -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	applied_filters = _normalize_filters(filters)
	if not has_warehouse_access(context):
		return _outbound_queue_state_payload(context, restricted_state(), applied_filters)
	if _normalize_queue_key(queue_key) not in {"", OUTBOUND_QUEUE_KEY}:
		return _outbound_queue_state_payload(
			context,
			state("unavailable", "Outbound picking unavailable", "This outbound picking queue is not available."),
			applied_filters,
		)
	outbound = _build_outbound_visibility(applied_filters, preview_limit=OUTBOUND_QUEUE_LIMIT, row_limit=OUTBOUND_QUEUE_LIMIT)
	return _outbound_queue_payload(context, outbound, applied_filters)


@frappe.whitelist()
def get_warehouse_stock_exceptions(
	queue_key: str | None = None,
	filters: str | dict[str, object] | None = None,
) -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	applied_filters = _normalize_filters(filters)
	if not has_warehouse_access(context):
		return _stock_exceptions_state_payload(context, restricted_state(), applied_filters)
	if _normalize_queue_key(queue_key) not in {"", STOCK_EXCEPTIONS_KEY}:
		return _stock_exceptions_state_payload(
			context,
			state("unavailable", "Stock exceptions unavailable", "This stock exception view is not available."),
			applied_filters,
		)
	exceptions = _build_stock_exceptions_visibility(applied_filters, row_limit=STOCK_EXCEPTIONS_LIMIT)
	return _stock_exceptions_payload(context, exceptions, applied_filters)


@frappe.whitelist()
def get_warehouse_movement_visibility_queue(
	queue_key: str | None = None,
	filters: str | dict[str, object] | None = None,
) -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	applied_filters = _normalize_filters(filters)
	if not has_warehouse_access(context):
		return _movement_visibility_state_payload(context, restricted_state(), applied_filters)
	if _normalize_queue_key(queue_key) not in {"", MOVEMENT_VISIBILITY_KEY}:
		return _movement_visibility_state_payload(
			context,
			state("unavailable", "Movement visibility unavailable", "This movement visibility view is not available."),
			applied_filters,
		)
	movement = _build_movement_visibility(applied_filters, row_limit=MOVEMENT_VISIBILITY_LIMIT)
	return _movement_visibility_payload(context, movement, applied_filters)


@frappe.whitelist()
def get_warehouse_transfer_visibility_queue(
	queue_key: str | None = None,
	filters: str | dict[str, object] | None = None,
) -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	applied_filters = _normalize_filters(filters)
	if not has_warehouse_access(context):
		return _transfer_visibility_state_payload(context, restricted_state(), applied_filters)
	if _normalize_queue_key(queue_key) not in {"", TRANSFER_VISIBILITY_KEY}:
		return _transfer_visibility_state_payload(
			context,
			state("unavailable", "Transfer visibility unavailable", "This transfer visibility view is not available."),
			applied_filters,
		)
	transfer = _build_transfer_visibility(applied_filters, row_limit=TRANSFER_VISIBILITY_LIMIT)
	return _transfer_visibility_payload(context, transfer, applied_filters)


@frappe.whitelist()
def get_warehouse_movement_review(context: str | None = None) -> dict[str, object]:
	ensure_authenticated()
	request_context = build_context()
	context_token = cstr(context).strip()
	if not has_warehouse_access(request_context):
		return _movement_review_state_payload(request_context, restricted_state(), context_token)
	if not context_token:
		return _movement_review_state_payload(
			request_context,
			state("unavailable", "Movement review unavailable", "Choose a movement from Movement Visibility."),
			context_token,
		)
	if not _can_read("Stock Entry"):
		return _movement_review_state_payload(
			request_context,
			state("restricted", "You do not have access to movement review", "You do not have access to movement review."),
			context_token,
		)

	decoded = _decode_movement_review_context(context_token)
	if not decoded.get("movement_id"):
		return _movement_review_state_payload(
			request_context,
			state("unavailable", "Movement review unavailable", "This movement reference is not available."),
			context_token,
		)

	review = _build_movement_review(decoded, context_token)
	if not review:
		return _movement_review_state_payload(
			request_context,
			state("unavailable", "Movement review unavailable", "This posted movement is not visible for warehouse review."),
			context_token,
		)
	payload = _movement_review_state_payload(request_context, ready_state(), context_token)
	payload.update(review)
	payload["state"] = ready_state()
	return payload


@frappe.whitelist()
def get_warehouse_stock_exception_review(context_token: str | None = None) -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	token = cstr(context_token).strip()
	if not has_warehouse_access(context):
		return _stock_exception_review_state_payload(context, restricted_state(), token)
	if not token:
		return _stock_exception_review_state_payload(
			context,
			state("unavailable", "Stock exception review unavailable", "Choose a stock exception from the Stock Exceptions view."),
			token,
		)
	if not _can_read("Sales Order"):
		return _stock_exception_review_state_payload(
			context,
			state("restricted", "You do not have access to stock exceptions", "You do not have access to stock exceptions."),
			token,
		)

	decoded = _decode_stock_exception_context(token)
	if not decoded.get("sales_order") or not decoded.get("item_code"):
		return _stock_exception_review_state_payload(
			context,
			state("unavailable", "Stock exception review unavailable", "This stock exception reference is not available."),
			token,
		)

	review = _build_stock_exception_review(decoded, token)
	if not review:
		return _stock_exception_review_state_payload(
			context,
			state("unavailable", "Stock exception review unavailable", "This stock exception is not open for warehouse review."),
			token,
		)
	payload = _stock_exception_review_state_payload(context, ready_state(), token)
	payload.update(review)
	payload["state"] = ready_state()
	return payload


@frappe.whitelist()
def get_warehouse_stock_posture_review(context_token: str | None = None) -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	token = cstr(context_token).strip()
	if not has_warehouse_access(context):
		return _stock_posture_review_state_payload(context, restricted_state(), token)
	if not token:
		return _stock_posture_review_state_payload(
			context,
			state("unavailable", "Stock posture review unavailable", "Choose an item and warehouse posture from a Warehouse review."),
			token,
		)
	if not _can_read("Bin"):
		return _stock_posture_review_state_payload(
			context,
			state("restricted", "You do not have access to stock posture", "You do not have access to stock posture."),
			token,
		)

	decoded = _decode_stock_posture_context(token)
	if not decoded.get("item_code") or not decoded.get("warehouse"):
		return _stock_posture_review_state_payload(
			context,
			state("unavailable", "Stock posture review unavailable", "This item and warehouse reference is not available."),
			token,
		)

	review = _build_stock_posture_review(decoded, token)
	if not review:
		return _stock_posture_review_state_payload(
			context,
			state("unavailable", "Stock posture review unavailable", "This stock posture is not visible for warehouse review."),
			token,
		)
	payload = _stock_posture_review_state_payload(context, ready_state(), token)
	payload.update(review)
	payload["state"] = ready_state()
	return payload


@frappe.whitelist()
def get_warehouse_receiving_review(purchase_order: str | None = None) -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	po_name = cstr(purchase_order).strip()
	if not has_warehouse_access(context):
		return _receiving_review_state_payload(context, restricted_state(), po_name)
	if not po_name:
		return _receiving_review_state_payload(
			context,
			state("unavailable", "Receiving review unavailable", "Choose an inbound order from the receiving queue."),
			po_name,
		)
	if not _can_read("Purchase Order"):
		return _receiving_review_state_payload(
			context,
			state("restricted", "You do not have access to inbound receiving", "You do not have access to inbound receiving."),
			po_name,
		)

	records = _safe_get_list(
		"Purchase Order",
		fields=_available_fields("Purchase Order", PURCHASE_ORDER_INBOUND_FIELDS),
		filters=_purchase_order_receiving_review_filters(po_name),
		order_by="modified desc",
		limit=1,
	)
	if not records:
		return _receiving_review_state_payload(
			context,
			state("unavailable", "Receiving review unavailable", "This inbound order is not open for warehouse review."),
			po_name,
		)

	record = records[0]
	lines = _receiving_review_lines(po_name)
	header = _receiving_review_header(record, lines)
	payload = _receiving_review_state_payload(context, ready_state(), po_name)
	payload.update(
		{
			"state": ready_state(),
			"page": {"title": "Receiving Review", "key": "receiving_review", "purchase_order": po_name},
			"header": header,
			"summary_cards": _receiving_summary_cards(header),
			"tabs": [
				{"key": "item_lines", "label": "Item Lines", "count": len(lines)},
				{"key": "receipt_history", "label": "Receipt History", "count": len(_receiving_receipt_history(po_name))},
			],
			"lines": lines,
			"receipt_history": _receiving_receipt_history(po_name),
		}
	)
	return payload


def _purchase_order_receiving_review_filters(po_name: str) -> list[list[object]]:
	conditions: list[list[object]] = [["Purchase Order", "name", "=", po_name], ["Purchase Order", "docstatus", "=", 1]]
	if _has_field("Purchase Order", "per_received"):
		conditions.append(["Purchase Order", "per_received", "<", 100])
	if _has_field("Purchase Order", "status"):
		conditions.append(["Purchase Order", "status", "in", list(INBOUND_OPEN_STATUSES)])
	return conditions


def _receiving_review_state_payload(
	context: dict[str, object],
	payload_state: dict[str, str],
	po_name: str,
) -> dict[str, object]:
	can_access = has_warehouse_access(context)
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": payload_state,
		"page": {"title": "Receiving Review", "key": "receiving_review", "purchase_order": po_name},
		"header": {
			"purchase_order": po_name,
			"supplier": "",
			"target_warehouse": "",
			"required_date": "",
			"state_key": payload_state.get("kind") or "unavailable",
			"state_label": payload_state.get("title") or "Unavailable",
			"age_label": "",
			"received_percent": "0%",
			"remaining_summary": "",
			"line_count": 0,
			"item_count": 0,
			"status": "",
		},
		"summary_cards": [],
		"tabs": [
			{"key": "item_lines", "label": "Item Lines", "count": 0},
			{"key": "receipt_history", "label": "Receipt History", "count": 0},
		],
		"lines": [],
		"receipt_history": [],
		"allowed_actions": [
			{"key": "refresh", "label": "Refresh", "kind": "read_only"},
			{"key": "back_to_inbound", "label": "Back to inbound receiving", "kind": "navigation"},
		] if can_access else [],
		"action_targets": {
			"inbound_queue": {"route": "warehouse-console-worklist", "queue_key": INBOUND_QUEUE_KEY}
		} if can_access else {},
		"valuation": {"visible": False, "fields": []},
		"fetched_at": str(now_datetime()),
	}


def _receiving_review_lines(po_name: str) -> list[dict[str, object]]:
	if not po_name:
		return []
	rows = []
	if _can_read("Purchase Order Item"):
		rows = _safe_get_all(
			"Purchase Order Item",
			fields=_available_fields("Purchase Order Item", PURCHASE_ORDER_ITEM_DETAIL_FIELDS),
			filters={"parent": po_name},
			order_by="schedule_date asc, expected_delivery_date asc, idx asc",
			limit=RECEIVING_DETAIL_LINE_LIMIT,
		)
	if not rows:
		rows = _receiving_review_lines_from_parent(po_name)
	return [_receiving_line(row) for row in rows]


def _receiving_review_lines_from_parent(po_name: str) -> list[dict[str, object]]:
	try:
		doc = frappe.get_doc("Purchase Order", po_name)
		doc.check_permission("read")
	except Exception:
		return []
	rows = []
	for child in list(doc.get("items") or [])[:RECEIVING_DETAIL_LINE_LIMIT]:
		row = {}
		for field in PURCHASE_ORDER_ITEM_DETAIL_FIELDS:
			if hasattr(child, "get"):
				row[field] = child.get(field)
			else:
				row[field] = getattr(child, field, None)
		rows.append(row)
	return sorted(rows, key=lambda row: (_date_key(row.get("schedule_date") or row.get("expected_delivery_date")), int(flt(row.get("idx")) or 0)))


def _receiving_line(row: dict[str, object]) -> dict[str, object]:
	ordered_qty = flt(row.get("qty"))
	received_qty = flt(row.get("received_qty"))
	remaining_qty = max(ordered_qty - received_qty, 0)
	required_date = cstr(row.get("expected_delivery_date") or row.get("schedule_date")).strip()
	return {
		"item_code": cstr(row.get("item_code")).strip(),
		"item_name": cstr(row.get("item_name")).strip(),
		"ordered_qty": _number_text(ordered_qty),
		"received_qty": _number_text(received_qty),
		"remaining_qty": _number_text(remaining_qty),
		"uom": cstr(row.get("stock_uom") or row.get("uom") or "").strip(),
		"target_warehouse": cstr(row.get("warehouse") or "Warehouse not set").strip(),
		"required_date": required_date,
		"status": _receiving_line_status(remaining_qty, received_qty, required_date),
	}


def _receiving_line_status(remaining_qty: float, received_qty: float, required_date: str) -> str:
	if remaining_qty <= 0:
		return "Arrived"
	if received_qty > 0:
		return "Partially arrived"
	due = _date_key(required_date)
	today = getdate(nowdate())
	if due < today:
		return "Overdue"
	if due == today:
		return "Due Today"
	return "Expected"


def _receiving_review_header(record: dict[str, object], lines: list[dict[str, object]]) -> dict[str, object]:
	warehouses = sorted({cstr(line.get("target_warehouse")).strip() for line in lines if cstr(line.get("target_warehouse")).strip()})
	item_codes = {cstr(line.get("item_code")).strip() for line in lines if cstr(line.get("item_code")).strip()}
	dates = [cstr(line.get("required_date")).strip() for line in lines if cstr(line.get("required_date")).strip()]
	required_date = min(dates, key=_date_key) if dates else cstr(record.get("schedule_date")).strip()
	remaining_by_uom: dict[str, float] = defaultdict(float)
	open_lines = 0
	for line in lines:
		remaining = flt(line.get("remaining_qty"))
		if remaining <= 0:
			continue
		open_lines += 1
		uom = cstr(line.get("uom")).strip()
		if uom:
			remaining_by_uom[uom] += remaining
	summary = {
		"open_lines": open_lines,
		"remaining_by_uom": dict(remaining_by_uom),
	}
	state_key = _inbound_state_key(record, required_date)
	return {
		"purchase_order": cstr(record.get("name")).strip(),
		"supplier": cstr(record.get("supplier_name") or record.get("supplier") or "-").strip(),
		"required_date": required_date,
		"target_warehouse": _warehouse_summary(warehouses or [cstr(record.get("set_warehouse")).strip()]),
		"state_key": state_key or "expected_soon",
		"state_label": _inbound_state_label(state_key or "expected_soon"),
		"age_label": _age_label(required_date, state_key or "expected_soon"),
		"received_percent": _percent_text(record.get("per_received")),
		"remaining_summary": _remaining_summary(summary),
		"line_count": len(lines),
		"item_count": len(item_codes),
		"status": cstr(record.get("status") or "-").strip(),
	}


def _receiving_summary_cards(header: dict[str, object]) -> list[dict[str, object]]:
	return [
		{"key": "state", "label": "Receiving State", "value": header.get("state_label") or "-", "note": header.get("age_label") or ""},
		{"key": "received", "label": "Received", "value": header.get("received_percent") or "0%", "note": "Quantity already arrived."},
		{"key": "open_lines", "label": "Open Lines", "value": header.get("line_count") or 0, "note": header.get("remaining_summary") or ""},
		{"key": "items", "label": "Items", "value": header.get("item_count") or 0, "note": header.get("target_warehouse") or ""},
	]


def _receiving_receipt_history(po_name: str) -> list[dict[str, object]]:
	if not po_name or not (_can_read("Purchase Receipt") and _can_read("Purchase Receipt Item")):
		return []
	items = _safe_get_all(
		"Purchase Receipt Item",
		fields=_available_fields("Purchase Receipt Item", PURCHASE_RECEIPT_ITEM_HISTORY_FIELDS),
		filters={"purchase_order": po_name},
		order_by="parent desc",
		limit=RECEIVING_DETAIL_HISTORY_ITEM_LIMIT,
	)
	parents = [cstr(row.get("parent")).strip() for row in items if cstr(row.get("parent")).strip()]
	if not parents:
		return []
	unique_parents = list(dict.fromkeys(parents))
	receipts = _safe_get_all(
		"Purchase Receipt",
		fields=_available_fields("Purchase Receipt", PURCHASE_RECEIPT_HISTORY_FIELDS),
		filters={"name": ["in", unique_parents]},
		order_by="posting_date desc, modified desc",
		limit=RECEIVING_DETAIL_HISTORY_LIMIT,
	)
	receipt_map = {cstr(row.get("name")).strip(): row for row in receipts}
	item_summary: dict[str, dict[str, object]] = defaultdict(lambda: {"items": set(), "qty_by_uom": defaultdict(float)})
	for item in items:
		parent = cstr(item.get("parent")).strip()
		if not parent:
			continue
		item_code = cstr(item.get("item_code")).strip()
		if item_code:
			item_summary[parent]["items"].add(item_code)
		uom = cstr(item.get("stock_uom") or item.get("uom") or "").strip()
		if uom:
			item_summary[parent]["qty_by_uom"][uom] += flt(item.get("qty"))

	history: list[dict[str, object]] = []
	for parent in unique_parents[:RECEIVING_DETAIL_HISTORY_LIMIT]:
		receipt = receipt_map.get(parent) or {"name": parent}
		summary = item_summary.get(parent) or {"items": set(), "qty_by_uom": {}}
		history.append(
			{
				"receipt_id": parent,
				"posting_date": cstr(receipt.get("posting_date") or "").strip(),
				"status": cstr(receipt.get("status") or "").strip() or "Recorded",
				"item_count": len(summary.get("items") or []),
				"quantity_summary": _quantity_summary(summary.get("qty_by_uom") or {}),
			}
		)
	return history


def _quantity_summary(qty_by_uom: dict[str, float]) -> str:
	if not qty_by_uom:
		return "Recorded quantity"
	if len(qty_by_uom) == 1:
		uom, qty = next(iter(qty_by_uom.items()))
		return f"{_number_text(qty)} {uom}"
	return f"{len(qty_by_uom)} quantities"


@frappe.whitelist()
def get_warehouse_picking_review(sales_order: str | None = None) -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	order_name = cstr(sales_order).strip()
	if not has_warehouse_access(context):
		return _picking_review_state_payload(context, restricted_state(), order_name)
	if not order_name:
		return _picking_review_state_payload(
			context,
			state("unavailable", "Picking review unavailable", "Choose an outbound order from the picking queue."),
			order_name,
		)
	if not _can_read("Sales Order"):
		return _picking_review_state_payload(
			context,
			state("restricted", "You do not have access to outbound picking", "You do not have access to outbound picking."),
			order_name,
		)

	records = _safe_get_list(
		"Sales Order",
		fields=_available_fields("Sales Order", SALES_ORDER_OUTBOUND_FIELDS),
		filters=_sales_order_picking_review_filters(order_name),
		order_by="modified desc",
		limit=1,
	)
	if not records:
		return _picking_review_state_payload(
			context,
			state("unavailable", "Picking review unavailable", "This outbound order is not open for warehouse review."),
			order_name,
		)

	record = records[0]
	lines = _picking_review_lines(order_name)
	header = _picking_review_header(record, lines)
	payload = _picking_review_state_payload(context, ready_state(), order_name)
	payload.update(
		{
			"state": ready_state(),
			"page": {"title": "Picking Review", "key": "picking_review", "sales_order": order_name},
			"header": header,
			"summary_cards": _picking_summary_cards(header),
			"tabs": [
				{"key": "item_lines", "label": "Item Lines", "count": len(lines)},
				{"key": "stock_readiness", "label": "Stock Readiness", "count": len(lines)},
			],
			"lines": lines,
		}
	)
	return payload


def _sales_order_picking_review_filters(order_name: str) -> list[list[object]]:
	conditions: list[list[object]] = [["Sales Order", "name", "=", order_name], ["Sales Order", "docstatus", "=", 1]]
	if _has_field("Sales Order", "per_delivered"):
		conditions.append(["Sales Order", "per_delivered", "<", 100])
	if _has_field("Sales Order", "status"):
		conditions.append(["Sales Order", "status", "in", list(OUTBOUND_OPEN_STATUSES)])
	return conditions


def _picking_review_state_payload(
	context: dict[str, object],
	payload_state: dict[str, str],
	order_name: str,
) -> dict[str, object]:
	can_access = has_warehouse_access(context)
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": payload_state,
		"page": {"title": "Picking Review", "key": "picking_review", "sales_order": order_name},
		"header": {
			"sales_order": order_name,
			"customer": "",
			"target_warehouse": "",
			"required_date": "",
			"state_key": payload_state.get("kind") or "unavailable",
			"state_label": payload_state.get("title") or "Unavailable",
			"age_label": "",
			"delivered_percent": "0%",
			"remaining_summary": "",
			"line_count": 0,
			"item_count": 0,
			"ready_line_count": 0,
			"review_line_count": 0,
			"status": "",
		},
		"summary_cards": [],
		"tabs": [
			{"key": "item_lines", "label": "Item Lines", "count": 0},
			{"key": "stock_readiness", "label": "Stock Readiness", "count": 0},
		],
		"lines": [],
		"allowed_actions": [
			{"key": "refresh", "label": "Refresh", "kind": "read_only"},
			{"key": "back_to_outbound", "label": "Back to outbound picking", "kind": "navigation"},
		] if can_access else [],
		"action_targets": {
			"outbound_queue": {"route": "warehouse-console-worklist", "queue_key": OUTBOUND_QUEUE_KEY}
		} if can_access else {},
		"fetched_at": str(now_datetime()),
	}


def _picking_review_lines(order_name: str) -> list[dict[str, object]]:
	if not order_name:
		return []
	rows = []
	if _can_read("Sales Order Item"):
		rows = _safe_get_all(
			"Sales Order Item",
			fields=_available_fields("Sales Order Item", SALES_ORDER_ITEM_DETAIL_FIELDS),
			filters={"parent": order_name},
			order_by="delivery_date asc, idx asc",
			limit=PICKING_DETAIL_LINE_LIMIT,
		)
	if not rows:
		rows = _picking_review_lines_from_parent(order_name)
	stock = _outbound_stock_map([_picking_requirements(rows)])
	return [_picking_line(row, stock) for row in rows]


def _picking_review_lines_from_parent(order_name: str) -> list[dict[str, object]]:
	try:
		doc = frappe.get_doc("Sales Order", order_name)
		doc.check_permission("read")
	except Exception:
		return []
	rows = []
	for child in list(doc.get("items") or [])[:PICKING_DETAIL_LINE_LIMIT]:
		row = {}
		for field in SALES_ORDER_ITEM_DETAIL_FIELDS:
			if hasattr(child, "get"):
				row[field] = child.get(field)
			else:
				row[field] = getattr(child, field, None)
		rows.append(row)
	return sorted(rows, key=lambda row: (_date_key(row.get("delivery_date")), int(flt(row.get("idx")) or 0)))


def _picking_requirements(rows: list[dict[str, object]]) -> dict[tuple[str, str], float]:
	requirements: dict[tuple[str, str], float] = defaultdict(float)
	for row in rows:
		item_code = cstr(row.get("item_code")).strip()
		warehouse = cstr(row.get("warehouse")).strip()
		remaining = max(flt(row.get("qty")) - flt(row.get("delivered_qty")), 0)
		if item_code and warehouse and remaining > 0:
			requirements[(item_code, warehouse)] += remaining
	return dict(requirements)


def _picking_line(row: dict[str, object], stock: dict[tuple[str, str], float]) -> dict[str, object]:
	ordered_qty = flt(row.get("qty"))
	delivered_qty = flt(row.get("delivered_qty"))
	pending_qty = max(ordered_qty - delivered_qty, 0)
	item_code = cstr(row.get("item_code")).strip()
	warehouse = cstr(row.get("warehouse") or "Warehouse not set").strip()
	stock_pair = (item_code, warehouse)
	available_qty = stock.get(stock_pair)
	readiness = _picking_line_readiness(pending_qty, available_qty)
	return {
		"item_code": item_code,
		"item_name": cstr(row.get("item_name")).strip(),
		"ordered_qty": _number_text(ordered_qty),
		"delivered_qty": _number_text(delivered_qty),
		"pending_qty": _number_text(pending_qty),
		"uom": cstr(row.get("stock_uom") or row.get("uom") or "").strip(),
		"source_warehouse": warehouse,
		"required_date": cstr(row.get("delivery_date")).strip(),
		"readiness": readiness,
		"availability": _picking_availability_text(available_qty),
	}


def _picking_line_readiness(pending_qty: float, available_qty: float | None) -> str:
	if pending_qty <= 0:
		return "Completed"
	if available_qty is None:
		return "Needs Stock Review"
	if flt(available_qty) >= pending_qty:
		return "Ready"
	return "Needs Stock Review"


def _picking_availability_text(available_qty: float | None) -> str:
	if available_qty is None:
		return "Availability not visible"
	return f"{_number_text(available_qty)} available"


def _picking_review_header(record: dict[str, object], lines: list[dict[str, object]]) -> dict[str, object]:
	warehouses = sorted({cstr(line.get("source_warehouse")).strip() for line in lines if cstr(line.get("source_warehouse")).strip()})
	item_codes = {cstr(line.get("item_code")).strip() for line in lines if cstr(line.get("item_code")).strip()}
	dates = [cstr(line.get("required_date")).strip() for line in lines if cstr(line.get("required_date")).strip()]
	required_date = min(dates, key=_date_key) if dates else cstr(record.get("delivery_date")).strip()
	remaining_by_uom: dict[str, float] = defaultdict(float)
	open_lines = 0
	ready_lines = 0
	review_lines = 0
	for line in lines:
		pending = flt(line.get("pending_qty"))
		if pending <= 0:
			continue
		open_lines += 1
		if cstr(line.get("readiness")) == "Ready":
			ready_lines += 1
		else:
			review_lines += 1
		uom = cstr(line.get("uom")).strip()
		if uom:
			remaining_by_uom[uom] += pending
	summary = {
		"open_lines": open_lines,
		"remaining_by_uom": dict(remaining_by_uom),
	}
	state_key = _outbound_state_key(record, required_date, {"stock_state": "ready_to_pick" if review_lines == 0 and open_lines else "needs_stock_review"})
	return {
		"sales_order": cstr(record.get("name")).strip(),
		"customer": cstr(record.get("customer_name") or record.get("customer") or "-").strip(),
		"required_date": required_date,
		"target_warehouse": _warehouse_summary(warehouses or [cstr(record.get("set_warehouse")).strip()]),
		"state_key": state_key or "expected_soon",
		"state_label": _outbound_state_label(state_key or "expected_soon"),
		"age_label": _age_label(required_date, state_key or "expected_soon"),
		"delivered_percent": _percent_text(record.get("per_delivered")),
		"remaining_summary": _remaining_summary(summary),
		"line_count": len(lines),
		"item_count": len(item_codes),
		"ready_line_count": ready_lines,
		"review_line_count": review_lines,
		"status": cstr(record.get("status") or "-").strip(),
	}


def _picking_summary_cards(header: dict[str, object]) -> list[dict[str, object]]:
	return [
		{"key": "state", "label": "Picking State", "value": header.get("state_label") or "-", "note": header.get("age_label") or ""},
		{"key": "delivered", "label": "Delivered", "value": header.get("delivered_percent") or "0%", "note": "Quantity already delivered."},
		{"key": "open_lines", "label": "Open Lines", "value": header.get("line_count") or 0, "note": header.get("remaining_summary") or ""},
		{"key": "readiness", "label": "Readiness", "value": header.get("ready_line_count") or 0, "note": f"{header.get('review_line_count') or 0} lines need review"},
	]


def _normalize_queue_key(value: str | None) -> str:
	return cstr(value).strip().lower().replace("-", "_")


def _normalize_filters(filters: str | dict[str, object] | None) -> dict[str, str]:
	if isinstance(filters, dict):
		source = filters
	elif isinstance(filters, str) and filters.strip():
		try:
			parsed = json.loads(filters)
		except Exception:
			source = {}
		else:
			source = parsed if isinstance(parsed, dict) else {}
	else:
		source = {}
	return {
		cstr(key).strip(): cstr(value).strip()
		for key, value in source.items()
		if cstr(key).strip() and value is not None and cstr(value).strip()
	}


def _build_inbound_visibility(
	filters: dict[str, str] | None = None,
	*,
	preview_limit: int = INBOUND_OVERVIEW_LIMIT,
	row_limit: int = INBOUND_QUEUE_LIMIT,
) -> dict[str, object]:
	applied_filters = filters or {}
	if not _can_read("Purchase Order"):
		return {
			"state": restricted_state(),
			"counts": _empty_inbound_counts(),
			"cards": _inbound_cards(_empty_inbound_counts()),
			"preview_rows": [],
			"groups": _empty_inbound_groups(),
			"total_count": 0,
			"queue_key": INBOUND_QUEUE_KEY,
			"queue_route": "warehouse-console-worklist",
		}

	rows = _inbound_rows(applied_filters, row_limit=row_limit)
	counts = _empty_inbound_counts()
	groups = _empty_inbound_groups()
	for row in rows:
		group_key = cstr(row.get("state_key")).strip() or "expected_soon"
		if group_key not in counts:
			group_key = "expected_soon"
		counts[group_key] += 1
		groups[group_key]["rows"].append(row)

	total_count = len(rows)
	payload_state = ready_state() if total_count else state(
		"empty",
		"No inbound receiving needs attention",
		"No inbound receiving needs attention.",
	)
	return {
		"state": payload_state,
		"counts": counts,
		"cards": _inbound_cards(counts),
		"preview_rows": rows[:preview_limit],
		"groups": [groups[key] for key in INBOUND_GROUP_ORDER],
		"total_count": total_count,
		"queue_key": INBOUND_QUEUE_KEY,
		"queue_route": "warehouse-console-worklist",
		"row_limit": row_limit,
		"horizon_days": INBOUND_HORIZON_DAYS,
	}


def _empty_inbound_counts() -> dict[str, int]:
	return {key: 0 for key in INBOUND_GROUP_ORDER}


def _empty_inbound_groups() -> dict[str, dict[str, object]]:
	labels = {
		"overdue": ("Overdue", "Past required date."),
		"due_today": ("Due Today", "Expected today."),
		"partially_received": ("Partially Received", "Some quantity has arrived."),
		"expected_soon": ("Expected Soon", f"Due in the next {INBOUND_HORIZON_DAYS} days."),
	}
	return {
		key: {"key": key, "title": labels[key][0], "summary": labels[key][1], "rows": []}
		for key in INBOUND_GROUP_ORDER
	}


def _inbound_cards(counts: dict[str, int]) -> list[dict[str, object]]:
	card_specs = [
		("due_today", "Receiving Due Today", "Expected today."),
		("overdue", "Overdue Receiving", "Past required date."),
		("partially_received", "Partially Received", "Some quantity has arrived."),
		("expected_soon", "Expected Soon", f"Due in the next {INBOUND_HORIZON_DAYS} days."),
	]
	return [
		{
			"key": key,
			"label": label,
			"title": label,
			"value": int(counts.get(key) or 0),
			"state": "live",
			"note": note,
			"empty_message": "No inbound receiving needs attention.",
		}
		for key, label, note in card_specs
	]


def _inbound_section_cards(inbound: dict[str, object] | None) -> list[dict[str, object]]:
	cards = inbound.get("cards") if isinstance(inbound, dict) else []
	result: list[dict[str, object]] = []
	for card in cards if isinstance(cards, list) else []:
		if not isinstance(card, dict):
			continue
		result.append(
			{
				"key": card.get("key"),
				"title": card.get("title") or card.get("label"),
				"value": card.get("value"),
				"state": card.get("state") or "live",
				"note": card.get("note") or "",
				"empty_message": card.get("empty_message") or "No inbound receiving needs attention.",
			}
		)
	return result


def _inbound_queue_state_payload(
	context: dict[str, object],
	payload_state: dict[str, str],
	filters: dict[str, str],
) -> dict[str, object]:
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": payload_state,
		"page": {"title": "Inbound Receiving", "key": INBOUND_QUEUE_KEY},
		"summary": {
			"title": "Inbound Receiving",
			"subtitle": payload_state.get("detail") or "Receiving work could not be loaded.",
			"chips": [{"label": payload_state.get("kind") or "state"}],
		},
		"controls": _inbound_controls(filters),
		"cards": _inbound_cards(_empty_inbound_counts()),
		"groups": [group for group in _empty_inbound_groups().values()],
		"rows": [],
		"action_targets": {},
		"valuation": {"visible": False, "fields": []},
		"fetched_at": str(now_datetime()),
	}


def _inbound_queue_payload(
	context: dict[str, object],
	inbound: dict[str, object],
	filters: dict[str, str],
) -> dict[str, object]:
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": inbound.get("state") or ready_state(),
		"page": {"title": "Inbound Receiving", "key": INBOUND_QUEUE_KEY},
		"summary": {
			"title": "Inbound Receiving",
			"subtitle": "Expected supplier stock due into warehouse.",
			"chips": [{"label": "Read-only"}, {"label": f"{inbound.get('total_count') or 0} shown"}],
		},
		"controls": _inbound_controls(filters),
		"cards": inbound.get("cards") or [],
		"groups": inbound.get("groups") or [],
		"rows": inbound.get("preview_rows") or [],
		"action_targets": {},
		"valuation": {"visible": False, "fields": []},
		"fetched_at": str(now_datetime()),
	}


def _inbound_controls(filters: dict[str, str]) -> dict[str, object]:
	return {
		"fields": [
			{"key": "purchase_order", "label": "Purchase Order", "type": "text", "value": filters.get("purchase_order", ""), "placeholder": "Search order"},
			{"key": "supplier", "label": "Supplier", "type": "text", "value": filters.get("supplier", ""), "placeholder": "Search supplier"},
			{"key": "warehouse", "label": "Warehouse", "type": "text", "value": filters.get("warehouse", ""), "placeholder": "Search warehouse"},
			{
				"key": "state",
				"label": "Receiving State",
				"type": "select",
				"value": filters.get("state", ""),
				"options": [
					{"label": "All", "value": ""},
					{"label": "Overdue", "value": "overdue"},
					{"label": "Due Today", "value": "due_today"},
					{"label": "Partially Received", "value": "partially_received"},
					{"label": "Expected Soon", "value": "expected_soon"},
				],
			},
		],
		"actions": [
			{"key": "refresh", "label": "Refresh"},
			{"key": "reset_filters", "label": "Reset"},
			{"key": "apply_filters", "label": "Apply", "kind": "primary"},
		],
		"scopeChips": ["Purchase Orders", "Read-only inbound"],
	}


def _inbound_rows(filters: dict[str, str], *, row_limit: int) -> list[dict[str, object]]:
	records = _safe_get_list(
		"Purchase Order",
		fields=_available_fields("Purchase Order", PURCHASE_ORDER_INBOUND_FIELDS),
		filters=_purchase_order_inbound_filters(filters),
		order_by="schedule_date asc, modified desc",
		limit=INBOUND_SCAN_LIMIT,
	)
	if not records:
		return []

	names = [cstr(record.get("name")).strip() for record in records if cstr(record.get("name")).strip()]
	line_map = _inbound_line_summary(names)
	rows: list[dict[str, object]] = []
	for record in records:
		name = cstr(record.get("name")).strip()
		if not name:
			continue
		summary = line_map.get(name) or _inbound_fallback_summary(record)
		if cstr(filters.get("warehouse")).strip() and cstr(filters.get("warehouse")).strip().lower() not in {
			cstr(warehouse).strip().lower() for warehouse in summary.get("warehouses") or []
		}:
			continue
		row = _inbound_row(record, summary)
		if not row:
			continue
		filter_state = cstr(filters.get("state")).strip()
		if filter_state and row.get("state_key") != filter_state:
			continue
		rows.append(row)
		if len(rows) >= row_limit:
			break
	return rows


def _purchase_order_inbound_filters(filters: dict[str, str]) -> list[list[object]]:
	conditions: list[list[object]] = [["Purchase Order", "docstatus", "=", 1]]
	if _has_field("Purchase Order", "per_received"):
		conditions.append(["Purchase Order", "per_received", "<", 100])
	if _has_field("Purchase Order", "status"):
		status = cstr(filters.get("status")).strip()
		if status and status in INBOUND_OPEN_STATUSES:
			conditions.append(["Purchase Order", "status", "=", status])
		else:
			conditions.append(["Purchase Order", "status", "in", list(INBOUND_OPEN_STATUSES)])
	purchase_order = cstr(filters.get("purchase_order")).strip()
	if purchase_order:
		conditions.append(["Purchase Order", "name", "like", f"%{purchase_order}%"])
	supplier = cstr(filters.get("supplier")).strip()
	if supplier:
		if _has_field("Purchase Order", "supplier_name"):
			conditions.append(["Purchase Order", "supplier_name", "like", f"%{supplier}%"])
		else:
			conditions.append(["Purchase Order", "supplier", "like", f"%{supplier}%"])
	return conditions


def _inbound_line_summary(po_names: list[str]) -> dict[str, dict[str, object]]:
	if not po_names:
		return {}
	rows = _safe_get_all(
		"Purchase Order Item",
		fields=_available_fields("Purchase Order Item", PURCHASE_ORDER_ITEM_INBOUND_FIELDS),
		filters={"parent": ["in", po_names]},
		order_by="schedule_date asc, expected_delivery_date asc, idx asc",
		limit=min(max(len(po_names) * 8, 80), 900),
	)
	summary: dict[str, dict[str, object]] = defaultdict(lambda: {
		"open_lines": 0,
		"item_codes": set(),
		"warehouses": set(),
		"earliest_date": "",
		"remaining_by_uom": defaultdict(float),
		"lines": [],
	})
	for row in rows:
		parent = cstr(row.get("parent")).strip()
		if not parent:
			continue
		remaining = max(flt(row.get("qty")) - flt(row.get("received_qty")), 0)
		if remaining <= 0:
			continue
		due_date = cstr(row.get("expected_delivery_date") or row.get("schedule_date")).strip()
		warehouse = cstr(row.get("warehouse")).strip()
		item_code = cstr(row.get("item_code")).strip()
		uom = cstr(row.get("stock_uom") or row.get("uom") or "").strip()
		summary[parent]["open_lines"] = int(summary[parent].get("open_lines") or 0) + 1
		if item_code:
			summary[parent]["item_codes"].add(item_code)
		if warehouse:
			summary[parent]["warehouses"].add(warehouse)
		if uom:
			summary[parent]["remaining_by_uom"][uom] += remaining
		if due_date and (not summary[parent].get("earliest_date") or _date_key(due_date) < _date_key(summary[parent].get("earliest_date"))):
			summary[parent]["earliest_date"] = due_date
		if len(summary[parent]["lines"]) < 4:
			summary[parent]["lines"].append(
				{
					"item_code": item_code,
					"item_name": cstr(row.get("item_name")).strip(),
					"remaining_qty": _number_text(remaining),
					"uom": uom,
					"target_warehouse": warehouse or "Warehouse not set",
					"required_date": due_date,
				}
			)
	return {
		key: {
			"open_lines": value["open_lines"],
			"item_count": len(value["item_codes"]),
			"warehouses": sorted(value["warehouses"]),
			"earliest_date": value["earliest_date"],
			"remaining_by_uom": dict(value["remaining_by_uom"]),
			"lines": value["lines"],
		}
		for key, value in summary.items()
	}


def _inbound_fallback_summary(record: dict[str, object]) -> dict[str, object]:
	warehouse = cstr(record.get("set_warehouse")).strip()
	return {
		"open_lines": 0,
		"item_count": 0,
		"warehouses": [warehouse] if warehouse else [],
		"earliest_date": cstr(record.get("schedule_date")).strip(),
		"remaining_by_uom": {},
		"lines": [],
	}


def _inbound_row(record: dict[str, object], summary: dict[str, object]) -> dict[str, object] | None:
	due_date = cstr(summary.get("earliest_date") or record.get("schedule_date")).strip()
	state_key = _inbound_state_key(record, due_date)
	if not state_key:
		return None
	warehouses = [cstr(value).strip() for value in summary.get("warehouses") or [] if cstr(value).strip()]
	name = cstr(record.get("name")).strip()
	return {
		"key": name,
		"name": name,
		"purchase_order": name,
		"supplier": cstr(record.get("supplier_name") or record.get("supplier") or "-").strip(),
		"required_date": due_date,
		"target_warehouse": _warehouse_summary(warehouses),
		"line_count": int(summary.get("open_lines") or 0),
		"item_count": int(summary.get("item_count") or 0),
		"received_percent": _percent_text(record.get("per_received")),
		"remaining_summary": _remaining_summary(summary),
		"status": cstr(record.get("status") or "-").strip(),
		"state_key": state_key,
		"state_label": _inbound_state_label(state_key),
		"age_label": _age_label(due_date, state_key),
		"lines": summary.get("lines") or [],
	}


def _inbound_state_key(record: dict[str, object], due_date: str) -> str:
	today = getdate(nowdate())
	horizon = today + timedelta(days=INBOUND_HORIZON_DAYS)
	due = _date_key(due_date)
	if due < today:
		return "overdue"
	if due == today:
		return "due_today"
	received = flt(record.get("per_received"))
	if 0 < received < 100:
		return "partially_received"
	if due <= horizon:
		return "expected_soon"
	return ""


def _inbound_state_label(state_key: str) -> str:
	return {
		"overdue": "Overdue",
		"due_today": "Due Today",
		"partially_received": "Partially Received",
		"expected_soon": "Expected Soon",
	}.get(state_key, "Expected Soon")


def _age_label(due_date: str, state_key: str) -> str:
	if not due_date:
		return "Date not set"
	today = getdate(nowdate())
	due = _date_key(due_date)
	if state_key == "overdue":
		days = max((today - due).days, 1)
		return f"Overdue {days}d"
	if state_key == "due_today":
		return "Due today"
	return f"Due {due_date}"


def _warehouse_summary(warehouses: list[str]) -> str:
	if not warehouses:
		return "Warehouse not set"
	if len(warehouses) == 1:
		return warehouses[0]
	return "Multiple warehouses"


def _remaining_summary(summary: dict[str, object]) -> str:
	remaining = summary.get("remaining_by_uom") or {}
	if isinstance(remaining, dict) and len(remaining) == 1:
		uom, qty = next(iter(remaining.items()))
		return f"{_number_text(qty)} {uom} remaining"
	open_lines = int(summary.get("open_lines") or 0)
	return f"{open_lines} open lines" if open_lines else "Open quantity pending"


def _build_movement_visibility(
	filters: dict[str, str] | None = None,
	*,
	row_limit: int = MOVEMENT_VISIBILITY_LIMIT,
) -> dict[str, object]:
	applied_filters = filters or {}
	if not _can_read("Stock Entry"):
		return {
			"state": restricted_state(),
			"counts": _empty_movement_counts(),
			"cards": _movement_cards(_empty_movement_counts(), 0),
			"groups": _empty_movement_groups(),
			"rows": [],
			"total_count": 0,
			"queue_key": MOVEMENT_VISIBILITY_KEY,
			"queue_route": "warehouse-console-worklist",
		}

	rows = _movement_visibility_rows(applied_filters, row_limit=row_limit)
	counts = _empty_movement_counts()
	groups = {group["key"]: group for group in _empty_movement_groups()}
	for row in rows:
		group_key = cstr(row.get("group_key")).strip() or "needs_review"
		if group_key not in counts:
			group_key = "needs_review"
		counts[group_key] += 1
		groups[group_key]["rows"].append(row)

	total_count = len(rows)
	payload_state = ready_state() if total_count else state(
		"empty",
		"No movement records found",
		"No posted movements found for the selected window.",
	)
	return {
		"state": payload_state,
		"counts": counts,
		"cards": _movement_cards(counts, total_count),
		"groups": [groups[key] for key in MOVEMENT_VISIBILITY_GROUP_ORDER],
		"rows": rows,
		"total_count": total_count,
		"queue_key": MOVEMENT_VISIBILITY_KEY,
		"queue_route": "warehouse-console-worklist",
		"row_limit": row_limit,
		"horizon_days": MOVEMENT_VISIBILITY_HORIZON_DAYS,
	}


def _empty_movement_counts() -> dict[str, int]:
	return {key: 0 for key in MOVEMENT_VISIBILITY_GROUP_ORDER}


def _empty_movement_groups() -> list[dict[str, object]]:
	labels = {
		"internal_transfers": ("Internal Transfers", "Warehouse-to-warehouse movements recorded recently."),
		"receipts": ("Receipts", "Stock arriving into a warehouse."),
		"issues": ("Issues", "Stock leaving a warehouse for operational use."),
		"adjustments_repack": ("Adjustments and Repack", "Recorded adjustment or repack movements."),
		"needs_review": ("Needs Review", "Movements with incomplete warehouse posture."),
	}
	return [
		{"key": key, "title": labels[key][0], "summary": labels[key][1], "rows": []}
		for key in MOVEMENT_VISIBILITY_GROUP_ORDER
	]


def _movement_cards(counts: dict[str, int], total_count: int) -> list[dict[str, object]]:
	return [
		{"key": "total_movements", "label": "Total Movements", "title": "Total Movements", "value": int(total_count or 0), "state": "live", "note": f"Latest {MOVEMENT_VISIBILITY_HORIZON_DAYS} day window."},
		{"key": "internal_transfers", "label": "Internal Transfers", "title": "Internal Transfers", "value": int(counts.get("internal_transfers") or 0), "state": "live", "note": "Warehouse-to-warehouse posture."},
		{"key": "receipts", "label": "Receipts", "title": "Receipts", "value": int(counts.get("receipts") or 0), "state": "live", "note": "Stock arriving into warehouse."},
		{"key": "needs_review", "label": "Needs Review", "title": "Needs Review", "value": int(counts.get("needs_review") or 0), "state": "live", "note": "Warehouse posture needs checking."},
	]


def _movement_visibility_state_payload(
	context: dict[str, object],
	payload_state: dict[str, str],
	filters: dict[str, str],
) -> dict[str, object]:
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": payload_state,
		"page": {"title": "Movement Visibility", "key": MOVEMENT_VISIBILITY_KEY},
		"summary": {
			"title": "Movement Visibility",
			"subtitle": payload_state.get("detail") or "Movement visibility could not be loaded.",
			"chips": [{"label": payload_state.get("kind") or "state"}],
		},
		"controls": _movement_controls(filters),
		"cards": _movement_cards(_empty_movement_counts(), 0),
		"groups": _empty_movement_groups(),
		"rows": [],
		"action_targets": {},
		"fetched_at": str(now_datetime()),
	}


def _movement_visibility_payload(
	context: dict[str, object],
	movement: dict[str, object],
	filters: dict[str, str],
) -> dict[str, object]:
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": movement.get("state") or ready_state(),
		"page": {"title": "Movement Visibility", "key": MOVEMENT_VISIBILITY_KEY},
		"summary": {
			"title": "Movement Visibility",
			"subtitle": "Recorded stock movement posture across warehouses.",
			"chips": [{"label": "Read-only"}, {"label": f"{movement.get('total_count') or 0} shown"}],
		},
		"controls": _movement_controls(filters),
		"cards": movement.get("cards") or [],
		"groups": movement.get("groups") or [],
		"rows": movement.get("rows") or [],
		"action_targets": {
			"stock_posture": {"route": "warehouse-console-stock-posture"},
		},
		"fetched_at": str(now_datetime()),
	}


def _build_transfer_visibility(
	filters: dict[str, str] | None = None,
	*,
	row_limit: int = TRANSFER_VISIBILITY_LIMIT,
) -> dict[str, object]:
	applied_filters = filters or {}
	if not _can_read("Stock Entry"):
		return {
			"state": restricted_state(),
			"counts": _empty_transfer_counts(),
			"cards": _transfer_cards(_empty_transfer_counts(), 0, "No transfer quantity visible"),
			"groups": _empty_transfer_groups(),
			"rows": [],
			"total_count": 0,
			"queue_key": TRANSFER_VISIBILITY_KEY,
			"queue_route": "warehouse-console-worklist",
		}

	rows = _transfer_visibility_rows(applied_filters, row_limit=row_limit)
	counts = _empty_transfer_counts()
	groups = {group["key"]: group for group in _empty_transfer_groups()}
	qty_by_uom: dict[str, float] = defaultdict(float)
	public_rows: list[dict[str, object]] = []
	for row in rows:
		group_key = cstr(row.get("group_key")).strip() or "needs_review"
		if group_key not in counts:
			group_key = "needs_review"
		counts[group_key] += 1
		for uom, qty in (row.get("_qty_by_uom") or {}).items():
			if cstr(uom).strip():
				qty_by_uom[cstr(uom).strip()] += flt(qty)
		public_row = _public_transfer_row(row)
		groups[group_key]["rows"].append(public_row)
		public_rows.append(public_row)

	total_count = len(public_rows)
	payload_state = ready_state() if total_count else state(
		"empty",
		"No transfer records found",
		"No posted transfers found for the selected window.",
	)
	return {
		"state": payload_state,
		"counts": counts,
		"cards": _transfer_cards(counts, total_count, _quantity_summary(qty_by_uom)),
		"groups": [groups[key] for key in TRANSFER_VISIBILITY_GROUP_ORDER],
		"rows": public_rows,
		"total_count": total_count,
		"queue_key": TRANSFER_VISIBILITY_KEY,
		"queue_route": "warehouse-console-worklist",
		"row_limit": row_limit,
		"horizon_days": TRANSFER_VISIBILITY_HORIZON_DAYS,
	}


def _empty_transfer_counts() -> dict[str, int]:
	return {key: 0 for key in TRANSFER_VISIBILITY_GROUP_ORDER}


def _empty_transfer_groups() -> list[dict[str, object]]:
	labels = {
		"direct_transfers": ("Direct Transfers", "Posted warehouse-to-warehouse transfers with clear direction."),
		"transit_related": ("Transit Related", "Transfers involving a transit warehouse posture."),
		"needs_review": ("Needs Review", "Transfers with incomplete or mixed warehouse posture."),
		"recently_posted": ("Recently Posted", "Submitted transfer records visible in the current window."),
	}
	return [
		{"key": key, "title": labels[key][0], "summary": labels[key][1], "rows": []}
		for key in TRANSFER_VISIBILITY_GROUP_ORDER
	]


def _transfer_cards(counts: dict[str, int], _total_count: int, quantity_summary: str) -> list[dict[str, object]]:
	return [
		{"key": "needs_review", "label": "Needs Review", "title": "Needs Review", "value": int(counts.get("needs_review") or 0), "state": "live", "note": "Missing or mixed warehouse posture."},
		{"key": "direct_transfers", "label": "Direct Transfers", "title": "Direct Transfers", "value": int(counts.get("direct_transfers") or 0), "state": "live", "note": "Clear source and target warehouse posture."},
		{"key": "transit_related", "label": "Transit Related", "title": "Transit Related", "value": int(counts.get("transit_related") or 0), "state": "live", "note": "Transit warehouse posture visible."},
		{"key": "transfer_quantity", "label": "Transfer Quantity", "title": "Transfer Quantity", "value": quantity_summary or "Recorded quantity", "state": "live", "note": "Operational quantity summary."},
	]


def _transfer_visibility_state_payload(
	context: dict[str, object],
	payload_state: dict[str, str],
	filters: dict[str, str],
) -> dict[str, object]:
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": payload_state,
		"page": {"title": "Transfer Visibility", "key": TRANSFER_VISIBILITY_KEY},
		"summary": {
			"title": "Transfer Visibility",
			"subtitle": payload_state.get("detail") or "Transfer visibility could not be loaded.",
			"chips": [{"label": payload_state.get("kind") or "state"}],
		},
		"controls": _transfer_controls(filters),
		"cards": _transfer_cards(_empty_transfer_counts(), 0, "No transfer quantity visible"),
		"groups": _empty_transfer_groups(),
		"rows": [],
		"action_targets": {},
		"fetched_at": str(now_datetime()),
	}


def _transfer_visibility_payload(
	context: dict[str, object],
	transfer: dict[str, object],
	filters: dict[str, str],
) -> dict[str, object]:
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": transfer.get("state") or ready_state(),
		"page": {"title": "Transfer Visibility", "key": TRANSFER_VISIBILITY_KEY},
		"summary": {
			"title": "Transfer Visibility",
			"subtitle": "Read-only warehouse-to-warehouse transfer posture.",
			"chips": [{"label": "Read-only"}, {"label": "Submitted movement records"}, {"label": f"{transfer.get('total_count') or 0} shown"}],
		},
		"controls": _transfer_controls(filters),
		"cards": transfer.get("cards") or [],
		"groups": transfer.get("groups") or [],
		"rows": transfer.get("rows") or [],
		"action_targets": {
			"movement_review": {"route": "warehouse-console-movement"},
			"stock_posture": {"route": "warehouse-console-stock-posture"},
		},
		"fetched_at": str(now_datetime()),
	}


def _transfer_controls(filters: dict[str, str]) -> dict[str, object]:
	return {
		"fields": [
			{
				"key": "transfer_state",
				"label": "Transfer Posture",
				"type": "select",
				"value": filters.get("transfer_state", filters.get("state", "")),
				"options": [
					{"label": "All", "value": ""},
					{"label": "Direct Transfers", "value": "direct_transfers"},
					{"label": "Transit Related", "value": "transit_related"},
					{"label": "Needs Review", "value": "needs_review"},
					{"label": "Recently Posted", "value": "recently_posted"},
				],
			},
			{
				"key": "date_window",
				"label": "Date Window",
				"type": "select",
				"value": filters.get("date_window", "last_14_days"),
				"options": [
					{"label": "Today", "value": "today"},
					{"label": "Last 7 Days", "value": "last_7_days"},
					{"label": "Last 14 Days", "value": "last_14_days"},
				],
			},
			{"key": "source_warehouse", "label": "Source Warehouse", "type": "text", "value": filters.get("source_warehouse", ""), "placeholder": "Filter source warehouse"},
			{"key": "target_warehouse", "label": "Target Warehouse", "type": "text", "value": filters.get("target_warehouse", ""), "placeholder": "Filter target warehouse"},
			{"key": "item", "label": "Item", "type": "text", "value": filters.get("item", ""), "placeholder": "Filter item"},
		],
		"actions": [
			{"key": "refresh", "label": "Refresh"},
			{"key": "reset_filters", "label": "Reset"},
			{"key": "apply_filters", "label": "Apply", "kind": "primary"},
		],
		"scopeChips": ["Submitted movement records", "Read-only transfer board"],
	}


def _transfer_visibility_rows(filters: dict[str, str], *, row_limit: int) -> list[dict[str, object]]:
	records = _safe_get_list(
		"Stock Entry",
		fields=_available_fields("Stock Entry", STOCK_ENTRY_MOVEMENT_FIELDS),
		filters=_stock_entry_transfer_filters(filters),
		order_by="posting_date desc, posting_time desc, modified desc",
		limit=TRANSFER_VISIBILITY_SCAN_LIMIT,
	)
	if not records:
		return []

	transfer_records = [record for record in records if _is_material_transfer_record(record)]
	names = [cstr(record.get("name")).strip() for record in transfer_records if cstr(record.get("name")).strip()]
	line_map = _movement_line_map(names)
	rows: list[dict[str, object]] = []
	for record in transfer_records:
		name = cstr(record.get("name")).strip()
		if not name:
			continue
		row = _transfer_row(record, line_map.get(name) or [])
		if not row:
			continue
		if not _transfer_row_matches(row, filters):
			continue
		rows.append(row)
		if len(rows) >= row_limit:
			break
	return rows


def _stock_entry_transfer_filters(filters: dict[str, str]) -> list[list[object]]:
	conditions: list[list[object]] = [["Stock Entry", "docstatus", "=", 1]]
	if _has_field("Stock Entry", "posting_date"):
		conditions.append(["Stock Entry", "posting_date", ">=", str(_transfer_window_start(filters))])
	if _has_field("Stock Entry", "purpose"):
		conditions.append(["Stock Entry", "purpose", "=", "Material Transfer"])
	elif _has_field("Stock Entry", "stock_entry_type"):
		conditions.append(["Stock Entry", "stock_entry_type", "=", "Material Transfer"])
	movement_id = cstr(filters.get("transfer_id") or filters.get("movement") or "").strip()
	if movement_id:
		conditions.append(["Stock Entry", "name", "like", f"%{movement_id}%"])
	return conditions


def _transfer_window_start(filters: dict[str, str]):
	window_key = cstr(filters.get("date_window") or "last_14_days").strip() or "last_14_days"
	days = TRANSFER_VISIBILITY_DATE_WINDOWS.get(window_key, TRANSFER_VISIBILITY_HORIZON_DAYS)
	return getdate(nowdate()) - timedelta(days=int(days or 0))


def _is_material_transfer_record(record: dict[str, object]) -> bool:
	label = f"{record.get('purpose') or ''} {record.get('stock_entry_type') or ''}".lower()
	return "material transfer" in label


def _transfer_row(record: dict[str, object], lines: list[dict[str, object]]) -> dict[str, object]:
	source_warehouse = cstr(record.get("from_warehouse")).strip() or _warehouse_summary(_unique_text(line.get("s_warehouse") for line in lines))
	target_warehouse = cstr(record.get("to_warehouse")).strip() or _warehouse_summary(_unique_text(line.get("t_warehouse") for line in lines))
	if source_warehouse == "Warehouse not set":
		source_warehouse = ""
	if target_warehouse == "Warehouse not set":
		target_warehouse = ""
	group_key = _transfer_group_key(source_warehouse, target_warehouse, lines)
	item_codes = _unique_text(line.get("item_code") for line in lines)
	qty_by_uom: dict[str, float] = defaultdict(float)
	sample_items: list[dict[str, object]] = []
	for line in lines:
		uom = cstr(line.get("stock_uom") or line.get("uom")).strip()
		if uom:
			qty_by_uom[uom] += flt(line.get("qty"))
		if len(sample_items) < 3:
			line_item = cstr(line.get("item_code")).strip()
			line_warehouse = cstr(line.get("t_warehouse") or line.get("s_warehouse") or target_warehouse or source_warehouse).strip()
			target = {}
			if line_item and line_warehouse:
				target = {
					"route": "warehouse-console-stock-posture",
					"context_token": _stock_posture_context_token(line_item, line_warehouse),
				}
			sample_items.append(
				{
					"item_code": line_item,
					"item_name": cstr(line.get("item_name")).strip(),
					"qty": _number_text(line.get("qty")),
					"uom": uom,
					"source_warehouse": cstr(line.get("s_warehouse")).strip(),
					"target_warehouse": cstr(line.get("t_warehouse")).strip(),
					"route_target": target,
				}
			)
	transfer_id = cstr(record.get("name")).strip()
	route_targets: dict[str, dict[str, object]] = {}
	if transfer_id:
		route_targets["movement_review"] = {
			"route": "warehouse-console-movement",
			"context_token": _movement_review_context_token(
				transfer_id,
				{"route": "warehouse-console-worklist", "queue_key": TRANSFER_VISIBILITY_KEY},
			),
		}
	for sample in sample_items:
		target = sample.get("route_target") if isinstance(sample, dict) else {}
		if isinstance(target, dict) and cstr(target.get("context_token")).strip():
			route_targets["stock_posture"] = target
			break
	return {
		"key": transfer_id,
		"transfer_id": transfer_id,
		"movement_id": transfer_id,
		"movement_type": _movement_type_label(record),
		"purpose": _movement_type_label(record),
		"posting_date": cstr(record.get("posting_date")).strip(),
		"posting_time": cstr(record.get("posting_time")).split(".")[0].strip(),
		"source_warehouse": source_warehouse,
		"target_warehouse": target_warehouse,
		"direction_label": _movement_direction_label(source_warehouse, target_warehouse, "internal_transfers"),
		"posture_key": group_key,
		"posture": _transfer_group_label(group_key),
		"item_count": len(item_codes),
		"quantity_summary": _quantity_summary(qty_by_uom),
		"sample_items": sample_items,
		"group_key": group_key,
		"group_label": _transfer_group_label(group_key),
		"route_targets": route_targets,
		"_qty_by_uom": dict(qty_by_uom),
	}


def _public_transfer_row(row: dict[str, object]) -> dict[str, object]:
	return {key: value for key, value in row.items() if not str(key).startswith("_")}


def _transfer_group_key(source_warehouse: str, target_warehouse: str, lines: list[dict[str, object]]) -> str:
	warehouses = [source_warehouse, target_warehouse]
	for line in lines:
		warehouses.extend([cstr(line.get("s_warehouse")).strip(), cstr(line.get("t_warehouse")).strip()])
	if any(_is_transit_warehouse(warehouse) for warehouse in warehouses):
		return "transit_related"
	if not source_warehouse or not target_warehouse or not lines:
		return "needs_review"
	if source_warehouse and target_warehouse:
		return "direct_transfers"
	return "recently_posted"


def _is_transit_warehouse(warehouse: object) -> bool:
	return "transit" in cstr(warehouse).strip().lower()


def _transfer_group_label(group_key: str) -> str:
	return {
		"direct_transfers": "Direct Transfer",
		"transit_related": "Transit Related",
		"needs_review": "Needs Review",
		"recently_posted": "Recently Posted",
	}.get(group_key, "Needs Review")


def _transfer_row_matches(row: dict[str, object], filters: dict[str, str]) -> bool:
	state_filter = cstr(filters.get("transfer_state") or filters.get("state")).strip()
	if state_filter and row.get("group_key") != state_filter:
		return False
	for field in ("source_warehouse", "target_warehouse"):
		needle = cstr(filters.get(field)).strip().lower()
		if needle and needle not in cstr(row.get(field)).strip().lower():
			return False
	item_filter = cstr(filters.get("item")).strip().lower()
	if item_filter:
		item_text = " ".join(
			f"{sample.get('item_code') or ''} {sample.get('item_name') or ''}".lower()
			for sample in row.get("sample_items") or []
			if isinstance(sample, dict)
		)
		if item_filter not in item_text:
			return False
	return True


def _movement_controls(filters: dict[str, str]) -> dict[str, object]:
	return {
		"fields": [
			{
				"key": "state",
				"label": "Movement State",
				"type": "select",
				"value": filters.get("state", ""),
				"options": [
					{"label": "All", "value": ""},
					{"label": "Internal Transfers", "value": "internal_transfers"},
					{"label": "Receipts", "value": "receipts"},
					{"label": "Issues", "value": "issues"},
					{"label": "Adjustments and Repack", "value": "adjustments_repack"},
					{"label": "Needs Review", "value": "needs_review"},
				],
			},
			{"key": "warehouse", "label": "Warehouse", "type": "text", "value": filters.get("warehouse", ""), "placeholder": "Filter warehouse"},
			{"key": "movement", "label": "Movement ID", "type": "text", "value": filters.get("movement", ""), "placeholder": "Filter movement"},
		],
		"actions": [
			{"key": "refresh", "label": "Refresh"},
			{"key": "reset_filters", "label": "Reset"},
			{"key": "apply_filters", "label": "Apply", "kind": "primary"},
		],
		"scopeChips": ["Recorded movements", "Read-only movement board"],
	}


def _movement_visibility_rows(filters: dict[str, str], *, row_limit: int) -> list[dict[str, object]]:
	records = _safe_get_list(
		"Stock Entry",
		fields=_available_fields("Stock Entry", STOCK_ENTRY_MOVEMENT_FIELDS),
		filters=_stock_entry_movement_filters(filters),
		order_by="posting_date desc, posting_time desc, modified desc",
		limit=MOVEMENT_VISIBILITY_SCAN_LIMIT,
	)
	if not records:
		return []

	names = [cstr(record.get("name")).strip() for record in records if cstr(record.get("name")).strip()]
	line_map = _movement_line_map(names)
	rows: list[dict[str, object]] = []
	for record in records:
		name = cstr(record.get("name")).strip()
		if not name:
			continue
		row = _movement_row(record, line_map.get(name) or [])
		if not row:
			continue
		if not _movement_row_matches(row, filters):
			continue
		rows.append(row)
		if len(rows) >= row_limit:
			break
	return rows


def _stock_entry_movement_filters(filters: dict[str, str]) -> list[list[object]]:
	conditions: list[list[object]] = [["Stock Entry", "docstatus", "=", 1]]
	if _has_field("Stock Entry", "posting_date"):
		window_start = getdate(nowdate()) - timedelta(days=MOVEMENT_VISIBILITY_HORIZON_DAYS)
		conditions.append(["Stock Entry", "posting_date", ">=", str(window_start)])
	movement = cstr(filters.get("movement")).strip()
	if movement:
		conditions.append(["Stock Entry", "name", "like", f"%{movement}%"])
	return conditions


def _movement_line_map(names: list[str]) -> dict[str, list[dict[str, object]]]:
	if not names:
		return {}
	if _can_read("Stock Entry Detail"):
		rows = _safe_get_all(
			"Stock Entry Detail",
			fields=_available_fields("Stock Entry Detail", STOCK_ENTRY_DETAIL_MOVEMENT_FIELDS),
			filters={"parent": ["in", names]},
			order_by="idx asc",
			limit=min(max(len(names) * 12, 120), 1000),
		)
		if rows:
			grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
			for row in rows:
				parent = cstr(row.get("parent")).strip()
				if parent:
					grouped[parent].append(row)
			return grouped
	return _movement_lines_from_entries(names)


def _movement_lines_from_entries(names: list[str]) -> dict[str, list[dict[str, object]]]:
	grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
	for name in names[:MOVEMENT_VISIBILITY_SCAN_LIMIT]:
		try:
			doc = frappe.get_doc("Stock Entry", name)
			doc.check_permission("read")
		except Exception:
			_clear_transient_frappe_messages()
			continue
		for row in list(doc.get("items") or [])[:80]:
			grouped[name].append(
				{
					"parent": name,
					"idx": row.get("idx"),
					"item_code": row.get("item_code"),
					"item_name": row.get("item_name"),
					"qty": row.get("qty"),
					"s_warehouse": row.get("s_warehouse"),
					"t_warehouse": row.get("t_warehouse"),
					"stock_uom": row.get("stock_uom"),
					"uom": row.get("uom"),
				}
			)
	return grouped


def _movement_row(record: dict[str, object], lines: list[dict[str, object]]) -> dict[str, object]:
	source_warehouse = cstr(record.get("from_warehouse")).strip() or _warehouse_summary(_unique_text(line.get("s_warehouse") for line in lines))
	target_warehouse = cstr(record.get("to_warehouse")).strip() or _warehouse_summary(_unique_text(line.get("t_warehouse") for line in lines))
	if source_warehouse == "Warehouse not set":
		source_warehouse = ""
	if target_warehouse == "Warehouse not set":
		target_warehouse = ""
	group_key = _movement_group_key(record, source_warehouse, target_warehouse)
	item_codes = _unique_text(line.get("item_code") for line in lines)
	qty_by_uom: dict[str, float] = defaultdict(float)
	sample_items: list[dict[str, object]] = []
	for line in lines:
		uom = cstr(line.get("stock_uom") or line.get("uom")).strip()
		if uom:
			qty_by_uom[uom] += flt(line.get("qty"))
		if len(sample_items) < 3:
			line_item = cstr(line.get("item_code")).strip()
			line_warehouse = cstr(line.get("t_warehouse") or line.get("s_warehouse") or target_warehouse or source_warehouse).strip()
			target = {}
			if line_item and line_warehouse:
				target = {
					"route": "warehouse-console-stock-posture",
					"context_token": _stock_posture_context_token(line_item, line_warehouse),
				}
			sample_items.append(
				{
					"item_code": line_item,
					"item_name": cstr(line.get("item_name")).strip(),
					"qty": _number_text(line.get("qty")),
					"uom": uom,
					"source_warehouse": cstr(line.get("s_warehouse")).strip(),
					"target_warehouse": cstr(line.get("t_warehouse")).strip(),
					"route_target": target,
				}
			)
	movement_id = cstr(record.get("name")).strip()
	route_targets: dict[str, dict[str, object]] = {}
	if movement_id:
		route_targets["movement_review"] = {
			"route": "warehouse-console-movement",
			"context_token": _movement_review_context_token(movement_id),
		}
	for sample in sample_items:
		target = sample.get("route_target") if isinstance(sample, dict) else {}
		if isinstance(target, dict) and cstr(target.get("context_token")).strip():
			route_targets["stock_posture"] = target
			break
	return {
		"key": movement_id,
		"movement_id": movement_id,
		"movement_type": _movement_type_label(record),
		"purpose": _movement_type_label(record),
		"posting_date": cstr(record.get("posting_date")).strip(),
		"posting_time": cstr(record.get("posting_time")).split(".")[0].strip(),
		"source_warehouse": source_warehouse,
		"target_warehouse": target_warehouse,
		"direction_label": _movement_direction_label(source_warehouse, target_warehouse, group_key),
		"item_count": len(item_codes),
		"quantity_summary": _quantity_summary(qty_by_uom),
		"sample_items": sample_items,
		"group_key": group_key,
		"group_label": _movement_group_label(group_key),
		"route_targets": route_targets,
	}


def _unique_text(values) -> list[str]:
	unique: list[str] = []
	seen: set[str] = set()
	for value in values:
		text = cstr(value).strip()
		if not text or text in seen:
			continue
		seen.add(text)
		unique.append(text)
	return unique


def _movement_type_label(record: dict[str, object]) -> str:
	return cstr(record.get("purpose") or record.get("stock_entry_type") or "Recorded Movement").strip()


def _movement_group_key(record: dict[str, object], source_warehouse: str, target_warehouse: str) -> str:
	purpose = _movement_type_label(record).lower()
	if not source_warehouse and not target_warehouse:
		return "needs_review"
	if "repack" in purpose or "manufacture" in purpose:
		return "adjustments_repack"
	if "transfer" in purpose or (source_warehouse and target_warehouse):
		return "internal_transfers"
	if "receipt" in purpose or (target_warehouse and not source_warehouse):
		return "receipts"
	if "issue" in purpose or (source_warehouse and not target_warehouse):
		return "issues"
	if "material" in purpose:
		return "adjustments_repack"
	return "needs_review"


def _movement_group_label(group_key: str) -> str:
	return {
		"internal_transfers": "Internal Transfers",
		"receipts": "Receipts",
		"issues": "Issues",
		"adjustments_repack": "Adjustments and Repack",
		"needs_review": "Needs Review",
	}.get(group_key, "Needs Review")


def _movement_direction_label(source_warehouse: str, target_warehouse: str, group_key: str) -> str:
	if source_warehouse and target_warehouse:
		return f"{source_warehouse} to {target_warehouse}"
	if target_warehouse:
		return f"Into {target_warehouse}"
	if source_warehouse:
		return f"From {source_warehouse}"
	return _movement_group_label(group_key)


def _movement_row_matches(row: dict[str, object], filters: dict[str, str]) -> bool:
	state_filter = cstr(filters.get("state")).strip()
	if state_filter and row.get("group_key") != state_filter:
		return False
	warehouse_filter = cstr(filters.get("warehouse")).strip().lower()
	if warehouse_filter:
		warehouses = {
			cstr(row.get("source_warehouse")).strip().lower(),
			cstr(row.get("target_warehouse")).strip().lower(),
		}
		for item in row.get("sample_items") or []:
			if isinstance(item, dict):
				warehouses.add(cstr(item.get("source_warehouse")).strip().lower())
				warehouses.add(cstr(item.get("target_warehouse")).strip().lower())
		if not any(warehouse_filter in warehouse for warehouse in warehouses if warehouse):
			return False
	return True


def _movement_review_context_token(movement_id: object, return_route: dict[str, object] | None = None) -> str:
	payload = {
		"movement_id": cstr(movement_id).strip(),
		"return_route": return_route or {"route": "warehouse-console-worklist", "queue_key": MOVEMENT_VISIBILITY_KEY},
	}
	return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8").hex()


def _decode_movement_review_context(context_token: str) -> dict[str, object]:
	token = cstr(context_token).strip()
	if not token or len(token) > MOVEMENT_CONTEXT_MAX_LENGTH:
		return {}
	try:
		payload = json.loads(bytes.fromhex(token).decode("utf-8"))
	except Exception:
		_clear_transient_frappe_messages()
		return {}
	if not isinstance(payload, dict):
		return {}
	movement_id = cstr(payload.get("movement_id")).strip()
	if not movement_id or len(movement_id) > 140 or any(character in movement_id for character in ("/", "\\", "#", "?")):
		return {}
	return {
		"movement_id": movement_id,
		"return_route": _safe_movement_return_route(payload.get("return_route")),
	}


def _safe_movement_return_route(value: object) -> dict[str, str]:
	if not isinstance(value, dict):
		return {"route": "warehouse-console-worklist", "queue_key": MOVEMENT_VISIBILITY_KEY}
	route = cstr(value.get("route")).strip()
	queue_key = _normalize_queue_key(cstr(value.get("queue_key")).strip())
	if route == "warehouse-console-worklist" and queue_key in {MOVEMENT_VISIBILITY_KEY, TRANSFER_VISIBILITY_KEY}:
		return {"route": "warehouse-console-worklist", "queue_key": queue_key}
	return {"route": "warehouse-console-worklist", "queue_key": MOVEMENT_VISIBILITY_KEY}


def _movement_review_state_payload(
	context: dict[str, object],
	payload_state: dict[str, str],
	context_token: str,
) -> dict[str, object]:
	can_access = has_warehouse_access(context)
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": payload_state,
		"page": {
			"title": "Movement Review",
			"key": MOVEMENT_REVIEW_DETAIL_KEY,
			"context_token": context_token,
		},
		"header": {
			"title": payload_state.get("title") or "Movement Review",
			"subtitle": payload_state.get("detail") or "",
			"context_token": context_token,
			"movement_id": "",
			"purpose": "",
			"movement_type": "",
			"posting_date": "",
			"posting_time": "",
			"source_warehouse": "",
			"target_warehouse": "",
			"direction_label": "",
			"docstatus_label": "",
			"freshness": str(now_datetime()),
		},
		"movement": {},
		"summary_cards": [],
		"panels": {
			"direction": {"title": "Movement Direction", "items": []},
			"related": {"title": "Related Reviews", "items": []},
		},
		"line_groups": [],
		"related_routes": [],
		"allowed_actions": [
			{"key": "back_to_movement_visibility", "label": "Back to movement visibility", "kind": "navigation"},
			{"key": "refresh", "label": "Refresh", "kind": "read_only"},
		] if can_access else [],
		"action_targets": {
			"back": {"route": "warehouse-console-worklist", "queue_key": MOVEMENT_VISIBILITY_KEY},
		} if can_access else {},
		"fetched_at": str(now_datetime()),
	}


def _build_movement_review(decoded: dict[str, object], context_token: str) -> dict[str, object] | None:
	movement_id = cstr(decoded.get("movement_id")).strip()
	records = _safe_get_list(
		"Stock Entry",
		fields=_available_fields("Stock Entry", STOCK_ENTRY_MOVEMENT_FIELDS),
		filters=_stock_entry_movement_review_filters(movement_id),
		order_by="modified desc",
		limit=1,
	)
	if not records:
		return None
	record = records[0]
	lines = (_movement_line_map([movement_id]).get(movement_id) or [])[:MOVEMENT_REVIEW_LINE_LIMIT]
	summary = _movement_row(record, lines)
	header = _movement_review_header(summary, context_token)
	review_lines = [_movement_review_line(line, summary) for line in lines[:MOVEMENT_REVIEW_LINE_LIMIT]]
	line_groups = _movement_review_line_groups(review_lines)
	related_routes = _movement_review_related_routes(review_lines)
	action_targets = {
		"back": decoded.get("return_route") or {"route": "warehouse-console-worklist", "queue_key": MOVEMENT_VISIBILITY_KEY},
	}
	return {
		"page": {
			"title": "Movement Review",
			"key": MOVEMENT_REVIEW_DETAIL_KEY,
			"context_token": context_token,
			"movement_id": movement_id,
		},
		"header": header,
		"movement": _movement_review_parent(summary),
		"summary_cards": _movement_review_cards(summary, review_lines, related_routes),
		"panels": {
			"direction": _movement_review_direction_panel(summary),
			"related": _movement_review_related_panel(related_routes),
		},
		"line_groups": line_groups,
		"related_routes": related_routes,
		"allowed_actions": [
			{"key": "back_to_movement_visibility", "label": "Back to movement visibility", "kind": "navigation"},
			{"key": "refresh", "label": "Refresh", "kind": "read_only"},
		],
		"action_targets": action_targets,
		"fetched_at": str(now_datetime()),
	}


def _stock_entry_movement_review_filters(movement_id: str) -> list[list[object]]:
	return [
		["Stock Entry", "name", "=", movement_id],
		["Stock Entry", "docstatus", "=", 1],
	]


def _movement_review_header(summary: dict[str, object], context_token: str) -> dict[str, object]:
	return {
		"title": "Movement Review",
		"subtitle": "Posted movement direction, item lines, and related Warehouse stock posture.",
		"context_token": context_token,
		"movement_id": summary.get("movement_id") or "",
		"purpose": summary.get("purpose") or "",
		"movement_type": summary.get("movement_type") or "",
		"posting_date": summary.get("posting_date") or "",
		"posting_time": summary.get("posting_time") or "",
		"source_warehouse": summary.get("source_warehouse") or "",
		"target_warehouse": summary.get("target_warehouse") or "",
		"direction_label": summary.get("direction_label") or "",
		"docstatus_label": "Posted",
		"freshness": str(now_datetime()),
	}


def _movement_review_parent(summary: dict[str, object]) -> dict[str, object]:
	return {
		"movement_id": summary.get("movement_id") or "",
		"purpose": summary.get("purpose") or "",
		"movement_type": summary.get("movement_type") or "",
		"posting_date": summary.get("posting_date") or "",
		"posting_time": summary.get("posting_time") or "",
		"source_warehouse": summary.get("source_warehouse") or "",
		"target_warehouse": summary.get("target_warehouse") or "",
		"direction_label": summary.get("direction_label") or "",
		"docstatus_label": "Posted",
		"item_count": summary.get("item_count") or 0,
		"quantity_summary": summary.get("quantity_summary") or "",
		"freshness": str(now_datetime()),
	}


def _movement_review_line(line: dict[str, object], summary: dict[str, object]) -> dict[str, object]:
	item_code = cstr(line.get("item_code")).strip()
	source_warehouse = cstr(line.get("s_warehouse") or summary.get("source_warehouse")).strip()
	target_warehouse = cstr(line.get("t_warehouse") or summary.get("target_warehouse")).strip()
	warehouse = target_warehouse or source_warehouse
	stock_posture_route = {}
	if item_code and warehouse:
		stock_posture_route = {
			"route": "warehouse-console-stock-posture",
			"context_token": _stock_posture_context_token(item_code, warehouse),
		}
	return {
		"item_code": item_code,
		"item_name": cstr(line.get("item_name")).strip(),
		"stock_uom": cstr(line.get("stock_uom") or line.get("uom")).strip(),
		"quantity": _number_text(line.get("qty")),
		"source_warehouse": source_warehouse,
		"target_warehouse": target_warehouse,
		"direction_label": _movement_direction_label(source_warehouse, target_warehouse, "needs_review"),
		"line_note": _movement_line_note(source_warehouse, target_warehouse),
		"stock_posture_route": stock_posture_route,
	}


def _movement_line_note(source_warehouse: str, target_warehouse: str) -> str:
	if source_warehouse and target_warehouse:
		return "Moves between warehouses."
	if target_warehouse:
		return "Adds stock into the target warehouse."
	if source_warehouse:
		return "Removes stock from the source warehouse."
	return "Warehouse direction is not fully visible."


def _movement_review_line_groups(lines: list[dict[str, object]]) -> list[dict[str, object]]:
	groups: dict[str, dict[str, object]] = {}
	for line in lines:
		key = _movement_line_group_key(line)
		if key not in groups:
			groups[key] = {
				"key": key,
				"title": line.get("direction_label") or "Warehouse Direction",
				"summary": "Read-only item movement lines.",
				"rows": [],
			}
		groups[key]["rows"].append(line)
	return list(groups.values()) or [
		{
			"key": "empty",
			"title": "Movement Lines",
			"summary": "No movement lines are visible for this movement.",
			"rows": [],
		}
	]


def _movement_line_group_key(line: dict[str, object]) -> str:
	source = cstr(line.get("source_warehouse")).strip() or "no-source"
	target = cstr(line.get("target_warehouse")).strip() or "no-target"
	return f"{source}->{target}".lower().replace(" ", "_")


def _movement_review_related_routes(lines: list[dict[str, object]]) -> list[dict[str, object]]:
	routes: list[dict[str, object]] = []
	seen: set[str] = set()
	for line in lines:
		target = line.get("stock_posture_route") if isinstance(line, dict) else {}
		token = cstr((target or {}).get("context_token")).strip() if isinstance(target, dict) else ""
		if not token or token in seen:
			continue
		seen.add(token)
		routes.append(
			{
				"key": f"stock_posture_{len(routes) + 1}",
				"label": "Stock Posture",
				"title": cstr(line.get("item_code")).strip(),
				"detail": cstr(line.get("target_warehouse") or line.get("source_warehouse")).strip(),
				"route_target": {"route": "warehouse-console-stock-posture", "context_token": token},
			}
		)
		if len(routes) >= 6:
			break
	return routes


def _movement_review_cards(summary: dict[str, object], lines: list[dict[str, object]], related_routes: list[dict[str, object]]) -> list[dict[str, object]]:
	warehouses = _unique_text(
		warehouse
		for line in lines
		for warehouse in (line.get("source_warehouse"), line.get("target_warehouse"))
	)
	return [
		{"key": "items", "label": "Item Lines", "value": len(lines), "note": f"{summary.get('item_count') or len(lines)} unique items"},
		{"key": "quantity", "label": "Quantity", "value": summary.get("quantity_summary") or "-", "note": "Operational quantity summary."},
		{"key": "warehouses", "label": "Warehouses", "value": len(warehouses), "note": _warehouse_summary(warehouses)},
		{"key": "posture_routes", "label": "Posture Reviews", "value": len(related_routes), "note": "Custom Warehouse review paths."},
	]


def _movement_review_direction_panel(summary: dict[str, object]) -> dict[str, object]:
	return {
		"title": "Movement Direction",
		"summary": summary.get("direction_label") or "Warehouse movement direction.",
		"items": _panel_items(
			("Source Warehouse", summary.get("source_warehouse")),
			("Target Warehouse", summary.get("target_warehouse")),
			("Movement Type", summary.get("movement_type")),
			("Posted", f"{summary.get('posting_date') or ''} {summary.get('posting_time') or ''}".strip()),
			("Status", "Posted"),
		),
	}


def _movement_review_related_panel(related_routes: list[dict[str, object]]) -> dict[str, object]:
	return {
		"title": "Related Reviews",
		"summary": "Custom Warehouse review paths for item and warehouse posture.",
		"items": [
			{
				"label": row.get("label") or "",
				"value": f"{row.get('title') or ''} {row.get('detail') or ''}".strip(),
				"target": row.get("route_target") or {},
			}
			for row in related_routes
		],
	}



def _build_stock_exceptions_visibility(
	filters: dict[str, str] | None = None,
	*,
	row_limit: int = STOCK_EXCEPTIONS_LIMIT,
) -> dict[str, object]:
	applied_filters = filters or {}
	if not _can_read("Sales Order"):
		return {
			"state": restricted_state(),
			"counts": _empty_stock_exception_counts(),
			"cards": _stock_exception_cards(_empty_stock_exception_counts(), 0),
			"groups": _empty_stock_exception_groups(),
			"rows": [],
			"total_count": 0,
			"queue_key": STOCK_EXCEPTIONS_KEY,
			"queue_route": "warehouse-console-worklist",
		}

	rows = _stock_exception_rows(applied_filters, row_limit=row_limit)
	counts = _empty_stock_exception_counts()
	groups = {group["key"]: group for group in _empty_stock_exception_groups()}
	for row in rows:
		group_key = cstr(row.get("exception_key")).strip() or "needs_stock_review"
		if group_key not in counts:
			group_key = "needs_stock_review"
		counts[group_key] += 1
		groups[group_key]["rows"].append(row)

	total_count = len(rows)
	payload_state = ready_state() if total_count else state(
		"empty",
		"No stock exceptions need attention",
		"No stock exceptions need attention.",
	)
	return {
		"state": payload_state,
		"counts": counts,
		"cards": _stock_exception_cards(counts, total_count),
		"groups": [groups[key] for key in STOCK_EXCEPTIONS_GROUP_ORDER],
		"rows": rows,
		"total_count": total_count,
		"queue_key": STOCK_EXCEPTIONS_KEY,
		"queue_route": "warehouse-console-worklist",
		"row_limit": row_limit,
		"horizon_days": STOCK_EXCEPTIONS_HORIZON_DAYS,
	}


def _empty_stock_exception_counts() -> dict[str, int]:
	return {key: 0 for key in STOCK_EXCEPTIONS_GROUP_ORDER}


def _empty_stock_exception_groups() -> list[dict[str, object]]:
	labels = {
		"needs_stock_review": ("Needs Stock Review", "Short stock without a near inbound cover."),
		"inbound_cover_expected": ("Inbound Cover Expected", "Short demand with supplier stock expected soon."),
		"urgent_aging": ("Urgent / Aging Demand", "Short demand that is due now or past due."),
		"warehouse_posture_missing": ("Warehouse Posture Missing", "Lines missing warehouse or stock posture."),
	}
	return [
		{"key": key, "title": labels[key][0], "summary": labels[key][1], "rows": []}
		for key in STOCK_EXCEPTIONS_GROUP_ORDER
	]


def _stock_exception_cards(counts: dict[str, int], total_count: int) -> list[dict[str, object]]:
	return [
		{"key": "total_exceptions", "label": "Total Exceptions", "title": "Total Exceptions", "value": int(total_count or 0), "state": "live", "note": "Rows needing warehouse review."},
		{"key": "shortage_risk", "label": "Shortage Risk", "title": "Shortage Risk", "value": int(counts.get("needs_stock_review") or 0) + int(counts.get("urgent_aging") or 0), "state": "live", "note": "Demand short of visible stock posture."},
		{"key": "inbound_cover_soon", "label": "Inbound Cover Soon", "title": "Inbound Cover Soon", "value": int(counts.get("inbound_cover_expected") or 0), "state": "live", "note": f"Supplier stock expected within {STOCK_EXCEPTIONS_HORIZON_DAYS} days."},
		{"key": "missing_posture", "label": "Missing Warehouse Posture", "title": "Missing Warehouse Posture", "value": int(counts.get("warehouse_posture_missing") or 0), "state": "live", "note": "Warehouse or stock posture is incomplete."},
	]


def _stock_exceptions_state_payload(
	context: dict[str, object],
	payload_state: dict[str, str],
	filters: dict[str, str],
) -> dict[str, object]:
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": payload_state,
		"page": {"title": "Stock Exceptions", "key": STOCK_EXCEPTIONS_KEY},
		"summary": {
			"title": "Stock Exceptions",
			"subtitle": payload_state.get("detail") or "Stock exceptions could not be loaded.",
			"chips": [{"label": payload_state.get("kind") or "state"}],
		},
		"controls": _stock_exception_controls(filters),
		"cards": _stock_exception_cards(_empty_stock_exception_counts(), 0),
		"groups": _empty_stock_exception_groups(),
		"rows": [],
		"action_targets": {},
		"fetched_at": str(now_datetime()),
	}


def _stock_exceptions_payload(
	context: dict[str, object],
	exceptions: dict[str, object],
	filters: dict[str, str],
) -> dict[str, object]:
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": exceptions.get("state") or ready_state(),
		"page": {"title": "Stock Exceptions", "key": STOCK_EXCEPTIONS_KEY},
		"summary": {
			"title": "Stock Exceptions",
			"subtitle": "Outbound blockers, inbound cover, and warehouse posture gaps.",
			"chips": [{"label": "Read-only"}, {"label": f"{exceptions.get('total_count') or 0} shown"}],
		},
		"controls": _stock_exception_controls(filters),
		"cards": exceptions.get("cards") or [],
		"groups": exceptions.get("groups") or [],
		"rows": exceptions.get("rows") or [],
		"action_targets": {
			"picking": {"route": "warehouse-console-picking"},
			"receiving": {"route": "warehouse-console-receiving"},
		},
		"fetched_at": str(now_datetime()),
	}


def _stock_exception_review_state_payload(
	context: dict[str, object],
	payload_state: dict[str, str],
	context_token: str,
) -> dict[str, object]:
	can_access = has_warehouse_access(context)
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": payload_state,
		"page": {
			"title": "Stock Exception Review",
			"key": STOCK_EXCEPTION_REVIEW_DETAIL_KEY,
			"context_token": context_token,
		},
		"header": {
			"title": payload_state.get("title") or "Stock Exception Review",
			"subtitle": payload_state.get("detail") or "",
			"exception_label": payload_state.get("kind") or "unavailable",
			"context_token": context_token,
			"sales_order": "",
			"customer": "",
			"item_code": "",
			"item_name": "",
			"source_warehouse": "",
			"required_date": "",
			"urgency_label": "",
			"explanation": payload_state.get("detail") or "",
		},
		"summary_cards": [],
		"panels": {
			"demand": {"title": "Demand at Risk", "items": []},
			"stock": {"title": "Stock Posture", "items": []},
			"inbound": {"title": "Inbound Cover", "items": []},
			"next_reviews": {"title": "Recommended Review", "items": []},
		},
		"related_rows": [],
		"allowed_actions": [
			{"key": "refresh", "label": "Refresh", "kind": "read_only"},
			{"key": "back_to_stock_exceptions", "label": "Back to stock exceptions", "kind": "navigation"},
		] if can_access else [],
		"action_targets": {
			"stock_exceptions": {"route": "warehouse-console-worklist", "queue_key": STOCK_EXCEPTIONS_KEY},
		} if can_access else {},
		"fetched_at": str(now_datetime()),
	}


def _build_stock_exception_review(decoded: dict[str, str], context_token: str) -> dict[str, object] | None:
	sales_order = cstr(decoded.get("sales_order")).strip()
	item_code = cstr(decoded.get("item_code")).strip()
	warehouse = cstr(decoded.get("warehouse")).strip()
	records = _safe_get_list(
		"Sales Order",
		fields=_available_fields("Sales Order", SALES_ORDER_OUTBOUND_FIELDS),
		filters=_sales_order_picking_review_filters(sales_order),
		order_by="modified desc",
		limit=1,
	)
	if not records:
		return None

	order = records[0]
	line = _stock_exception_review_line(order, item_code, warehouse)
	if not line:
		return None
	resolved_warehouse = cstr(line.get("warehouse") or order.get("set_warehouse")).strip()
	pair = {(item_code, resolved_warehouse)} if item_code and resolved_warehouse else set()
	stock = _stock_exception_stock_map(pair)
	inbound = _stock_exception_inbound_map(pair)
	row = _stock_exception_row(line, order, stock, inbound)
	if not row:
		return None
	header = _stock_exception_review_header(row, context_token)
	inbound_info = {
		"purchase_order": row.get("expected_inbound_order"),
		"expected_inbound_qty": row.get("expected_inbound_qty"),
		"expected_inbound_date": row.get("expected_inbound_date"),
	}
	return {
		"page": {
			"title": "Stock Exception Review",
			"key": STOCK_EXCEPTION_REVIEW_DETAIL_KEY,
			"context_token": context_token,
			"sales_order": row.get("sales_order"),
			"item_code": row.get("item_code"),
			"source_warehouse": row.get("source_warehouse"),
		},
		"header": header,
		"summary_cards": _stock_exception_review_cards(row),
		"panels": {
			"demand": _stock_exception_demand_panel(row, order),
			"stock": _stock_exception_stock_panel(row),
			"inbound": _stock_exception_inbound_panel(row),
			"next_reviews": _stock_exception_next_review_panel(row),
		},
		"related_rows": _stock_exception_related_rows(row, inbound_info),
		"action_targets": _stock_exception_review_action_targets(row),
	}


def _stock_exception_review_line(order: dict[str, object], item_code: str, warehouse: str) -> dict[str, object] | None:
	sales_order = cstr(order.get("name")).strip()
	rows = []
	if _can_read("Sales Order Item"):
		rows = _safe_get_all(
			"Sales Order Item",
			fields=_available_fields("Sales Order Item", SALES_ORDER_ITEM_DETAIL_FIELDS),
			filters={"parent": sales_order},
			order_by="delivery_date asc, idx asc",
			limit=PICKING_DETAIL_LINE_LIMIT,
		)
	if not rows:
		rows = _stock_exception_lines_from_orders({sales_order: order})
	for row in rows:
		row_item = cstr(row.get("item_code")).strip()
		row_warehouse = cstr(row.get("warehouse") or order.get("set_warehouse")).strip()
		if row_item != item_code:
			continue
		if warehouse and row_warehouse != warehouse:
			continue
		if max(flt(row.get("qty")) - flt(row.get("delivered_qty")), 0) <= 0:
			continue
		return row
	return None


def _stock_exception_review_header(row: dict[str, object], context_token: str) -> dict[str, object]:
	return {
		"title": row.get("exception_label") or "Stock Exception Review",
		"subtitle": "Demand, stock posture, and inbound cover for this warehouse line.",
		"exception_label": row.get("exception_label") or "",
		"context_token": context_token,
		"sales_order": row.get("sales_order") or "",
		"customer": row.get("customer") or "",
		"item_code": row.get("item_code") or "",
		"item_name": row.get("item_name") or "",
		"source_warehouse": row.get("source_warehouse") or "",
		"required_date": row.get("required_date") or "",
		"urgency_label": row.get("urgency_label") or "",
		"explanation": row.get("explanation") or "",
	}


def _stock_exception_review_cards(row: dict[str, object]) -> list[dict[str, object]]:
	return [
		{"key": "state", "label": "Exception State", "value": row.get("exception_label") or "-", "note": row.get("urgency_label") or ""},
		{"key": "pending_qty", "label": "Pending Demand", "value": f"{row.get('pending_qty') or '0'} {row.get('uom') or ''}".strip(), "note": row.get("sales_order") or ""},
		{"key": "available_qty", "label": "Available", "value": row.get("available_qty") or "N/A", "note": row.get("source_warehouse") or ""},
		{"key": "inbound_cover", "label": "Inbound Cover", "value": row.get("expected_inbound_qty") or "0", "note": row.get("expected_inbound_date") or "No near cover visible"},
	]


def _panel_items(*items: tuple[str, object]) -> list[dict[str, str]]:
	return [{"label": label, "value": cstr(value).strip()} for label, value in items if cstr(value).strip()]


def _stock_exception_demand_panel(row: dict[str, object], order: dict[str, object]) -> dict[str, object]:
	return {
		"title": "Demand at Risk",
		"summary": row.get("explanation") or "",
		"items": _panel_items(
			("Sales Order", row.get("sales_order")),
			("Customer", row.get("customer")),
			("Required Date", row.get("required_date")),
			("Pending Qty", f"{row.get('pending_qty') or '0'} {row.get('uom') or ''}".strip()),
			("Delivered Qty", f"{row.get('delivered_qty') or '0'} {row.get('uom') or ''}".strip()),
			("Order Status", order.get("status")),
		),
	}


def _stock_exception_stock_panel(row: dict[str, object]) -> dict[str, object]:
	stock_posture_token = _stock_posture_context_token(
		row.get("item_code") or "",
		row.get("source_warehouse") or "",
		sales_order=row.get("sales_order") or "",
		purchase_order=row.get("expected_inbound_order") or "",
		stock_exception_token=row.get("context_token") or "",
	)
	return {
		"title": "Stock Posture",
		"summary": "Current visible stock compared with pending demand.",
		"items": _panel_items(
			("Item", f"{row.get('item_code') or ''} {row.get('item_name') or ''}".strip()),
			("Warehouse", row.get("source_warehouse")),
			("Available", row.get("available_qty")),
			("Projected", row.get("projected_qty")),
			("Short Qty", f"{row.get('short_qty') or '0'} {row.get('uom') or ''}".strip()),
		),
		"route_target": {"route": "warehouse-console-stock-posture", "context_token": stock_posture_token},
	}


def _stock_exception_inbound_panel(row: dict[str, object]) -> dict[str, object]:
	purchase_order = cstr(row.get("expected_inbound_order")).strip()
	return {
		"title": "Inbound Cover",
		"summary": "Supplier stock expected soon." if purchase_order else "No near inbound cover is visible for this line.",
		"items": _panel_items(
			("Expected Qty", f"{row.get('expected_inbound_qty') or '0'} {row.get('uom') or ''}".strip()),
			("Expected Date", row.get("expected_inbound_date")),
			("Inbound Order", purchase_order),
		),
	}


def _stock_exception_next_review_panel(row: dict[str, object]) -> dict[str, object]:
	items = [
		{
			"label": "Picking Posture",
			"value": "Review outbound line readiness inside Warehouse.",
			"target": {"route": "warehouse-console-picking", "sales_order": row.get("sales_order") or ""},
		}
	]
	if cstr(row.get("expected_inbound_order")).strip():
		items.append(
			{
				"label": "Inbound Cover",
				"value": "Review expected supplier stock inside Warehouse.",
				"target": {"route": "warehouse-console-receiving", "purchase_order": row.get("expected_inbound_order") or ""},
			}
		)
	items.append(
		{
			"label": "Stock Exceptions",
			"value": "Return to the exception queue.",
			"target": {"route": "warehouse-console-worklist", "queue_key": STOCK_EXCEPTIONS_KEY},
		}
	)
	if cstr(row.get("item_code")).strip() and cstr(row.get("source_warehouse")).strip():
		items.insert(
			1,
			{
				"label": "Stock Posture",
				"value": "Review item and warehouse posture inside Warehouse.",
				"target": {
					"route": "warehouse-console-stock-posture",
					"context_token": _stock_posture_context_token(
						row.get("item_code") or "",
						row.get("source_warehouse") or "",
						sales_order=row.get("sales_order") or "",
						purchase_order=row.get("expected_inbound_order") or "",
						stock_exception_token=row.get("context_token") or "",
					),
				},
			},
		)
	return {"title": "Recommended Review", "summary": "Read-only review paths available for this exception.", "items": items}


def _stock_exception_related_rows(row: dict[str, object], inbound_info: dict[str, object]) -> list[dict[str, object]]:
	rows = [
		{
			"key": "demand",
			"title": row.get("sales_order") or "",
			"label": "Outbound Demand",
			"detail": f"{row.get('pending_qty') or '0'} {row.get('uom') or ''} pending".strip(),
			"route_target": {"route": "warehouse-console-picking", "sales_order": row.get("sales_order") or ""},
		}
	]
	if cstr(inbound_info.get("purchase_order")).strip():
		rows.append(
			{
				"key": "inbound",
				"title": inbound_info.get("purchase_order") or "",
				"label": "Inbound Cover",
				"detail": f"{inbound_info.get('expected_inbound_qty') or '0'} expected {inbound_info.get('expected_inbound_date') or ''}".strip(),
				"route_target": {"route": "warehouse-console-receiving", "purchase_order": inbound_info.get("purchase_order") or ""},
			}
		)
	return rows


def _stock_exception_review_action_targets(row: dict[str, object]) -> dict[str, dict[str, str]]:
	targets: dict[str, dict[str, str]] = {
		"stock_exceptions": {"route": "warehouse-console-worklist", "queue_key": STOCK_EXCEPTIONS_KEY},
		"picking": {"route": "warehouse-console-picking", "sales_order": cstr(row.get("sales_order")).strip()},
	}
	if cstr(row.get("item_code")).strip() and cstr(row.get("source_warehouse")).strip():
		targets["stock_posture"] = {
			"route": "warehouse-console-stock-posture",
			"context_token": _stock_posture_context_token(
				row.get("item_code") or "",
				row.get("source_warehouse") or "",
				sales_order=row.get("sales_order") or "",
				purchase_order=row.get("expected_inbound_order") or "",
				stock_exception_token=row.get("context_token") or "",
			),
		}
	purchase_order = cstr(row.get("expected_inbound_order")).strip()
	if purchase_order:
		targets["receiving"] = {"route": "warehouse-console-receiving", "purchase_order": purchase_order}
	return targets


def _stock_posture_review_state_payload(
	context: dict[str, object],
	payload_state: dict[str, str],
	context_token: str,
) -> dict[str, object]:
	can_access = has_warehouse_access(context)
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": payload_state,
		"page": {
			"title": "Stock Posture Review",
			"key": STOCK_POSTURE_REVIEW_DETAIL_KEY,
			"context_token": context_token,
		},
		"header": {
			"title": payload_state.get("title") or "Stock Posture Review",
			"subtitle": payload_state.get("detail") or "",
			"context_token": context_token,
			"item_code": "",
			"item_name": "",
			"warehouse": "",
			"posture_label": payload_state.get("kind") or "unavailable",
			"explanation": payload_state.get("detail") or "",
			"fetched_at": str(now_datetime()),
		},
		"summary_cards": [],
		"panels": {
			"stock": {"title": "Stock Posture", "items": []},
			"inbound": {"title": "Inbound Cover", "items": []},
			"outbound": {"title": "Open Demand", "items": []},
			"related": {"title": "Related Reviews", "items": []},
		},
		"outbound_rows": [],
		"inbound_rows": [],
		"related_rows": [],
		"allowed_actions": [
			{"key": "back", "label": "Back", "kind": "navigation"},
			{"key": "refresh", "label": "Refresh", "kind": "read_only"},
		] if can_access else [],
		"action_targets": {
			"back": {"route": "warehouse-console-worklist", "queue_key": STOCK_EXCEPTIONS_KEY},
		} if can_access else {},
		"fetched_at": str(now_datetime()),
	}


def _build_stock_posture_review(decoded: dict[str, str], context_token: str) -> dict[str, object] | None:
	item_code = cstr(decoded.get("item_code")).strip()
	warehouse = cstr(decoded.get("warehouse")).strip()
	if not item_code or not warehouse:
		return None
	pair = {(item_code, warehouse)}
	stock_info = _stock_exception_stock_map(pair).get((item_code, warehouse)) or {}
	inbound_rows = _stock_posture_inbound_rows(item_code, warehouse)
	outbound_rows = _stock_posture_outbound_rows(item_code, warehouse)
	inbound_summary = _stock_posture_inbound_summary(inbound_rows)
	outbound_summary = _stock_posture_outbound_summary(outbound_rows)
	item_name = _stock_posture_item_name(item_code, outbound_rows, inbound_rows)
	actual_qty = stock_info.get("actual_qty")
	reserved_qty = stock_info.get("reserved_qty")
	available_qty = stock_info.get("available_qty")
	projected_qty = stock_info.get("projected_qty")
	posture = _stock_posture_label(available_qty, outbound_summary.get("pending_qty"), inbound_summary.get("expected_qty"))
	header = {
		"title": "Stock Posture Review",
		"subtitle": "Item and warehouse posture for read-only operational review.",
		"context_token": context_token,
		"item_code": item_code,
		"item_name": item_name,
		"warehouse": warehouse,
		"posture_label": posture["label"],
		"explanation": posture["explanation"],
		"fetched_at": str(now_datetime()),
	}
	return {
		"page": {
			"title": "Stock Posture Review",
			"key": STOCK_POSTURE_REVIEW_DETAIL_KEY,
			"context_token": context_token,
			"item_code": item_code,
			"warehouse": warehouse,
		},
		"header": header,
		"summary_cards": _stock_posture_review_cards(stock_info, inbound_summary, outbound_summary, posture),
		"panels": {
			"stock": _stock_posture_stock_panel(item_code, item_name, warehouse, stock_info, posture),
			"inbound": _stock_posture_inbound_panel(inbound_rows, inbound_summary),
			"outbound": _stock_posture_outbound_panel(outbound_rows, outbound_summary),
			"related": _stock_posture_related_panel(decoded, inbound_rows, outbound_rows),
		},
		"outbound_rows": outbound_rows[:STOCK_POSTURE_OUTBOUND_LIMIT],
		"inbound_rows": inbound_rows[:STOCK_POSTURE_INBOUND_LIMIT],
		"related_rows": _stock_posture_related_rows(decoded, inbound_rows, outbound_rows),
		"action_targets": _stock_posture_action_targets(decoded, inbound_rows, outbound_rows),
		"quantity_posture": {
			"actual_qty": _number_text(actual_qty) if actual_qty is not None else "N/A",
			"available_qty": _number_text(available_qty) if available_qty is not None else "N/A",
			"reserved_qty": _number_text(reserved_qty) if reserved_qty is not None else "N/A",
			"projected_qty": _number_text(projected_qty) if projected_qty is not None else "N/A",
		},
	}


def _stock_posture_review_cards(
	stock_info: dict[str, float],
	inbound_summary: dict[str, object],
	outbound_summary: dict[str, object],
	posture: dict[str, str],
) -> list[dict[str, object]]:
	available_qty = stock_info.get("available_qty")
	projected_qty = stock_info.get("projected_qty")
	return [
		{"key": "posture", "label": "Posture", "value": posture.get("label") or "-", "note": posture.get("explanation") or ""},
		{"key": "available", "label": "Available", "value": _number_text(available_qty) if available_qty is not None else "N/A", "note": "Current operational availability."},
		{"key": "projected", "label": "Projected", "value": _number_text(projected_qty) if projected_qty is not None else "N/A", "note": "Projected warehouse quantity."},
		{"key": "open_demand", "label": "Open Demand", "value": _number_text(outbound_summary.get("pending_qty")), "note": f"{outbound_summary.get('line_count') or 0} open lines"},
		{"key": "inbound_cover", "label": "Inbound Cover", "value": _number_text(inbound_summary.get("expected_qty")), "note": inbound_summary.get("next_date") or "No near inbound cover visible"},
	]


def _stock_posture_stock_panel(
	item_code: str,
	item_name: str,
	warehouse: str,
	stock_info: dict[str, float],
	posture: dict[str, str],
) -> dict[str, object]:
	return {
		"title": "Stock Posture",
		"summary": posture.get("explanation") or "Current item and warehouse posture.",
		"items": _panel_items(
			("Item", f"{item_code} {item_name}".strip()),
			("Warehouse", warehouse),
			("Actual Qty", _number_text(stock_info.get("actual_qty")) if stock_info.get("actual_qty") is not None else "N/A"),
			("Available Qty", _number_text(stock_info.get("available_qty")) if stock_info.get("available_qty") is not None else "N/A"),
			("Reserved Qty", _number_text(stock_info.get("reserved_qty")) if stock_info.get("reserved_qty") is not None else "N/A"),
			("Projected Qty", _number_text(stock_info.get("projected_qty")) if stock_info.get("projected_qty") is not None else "N/A"),
		),
	}


def _stock_posture_inbound_panel(rows: list[dict[str, object]], summary: dict[str, object]) -> dict[str, object]:
	return {
		"title": "Inbound Cover",
		"summary": "Submitted purchase orders expected for this item and warehouse." if rows else "No near inbound cover is visible for this item and warehouse.",
		"items": _panel_items(
			("Expected Qty", _number_text(summary.get("expected_qty"))),
			("Next Expected Date", summary.get("next_date")),
			("Inbound Orders", summary.get("order_count")),
		),
	}


def _stock_posture_outbound_panel(rows: list[dict[str, object]], summary: dict[str, object]) -> dict[str, object]:
	return {
		"title": "Open Demand",
		"summary": "Submitted sales orders with pending demand for this item and warehouse." if rows else "No open outbound demand is visible for this item and warehouse.",
		"items": _panel_items(
			("Pending Qty", _number_text(summary.get("pending_qty"))),
			("Open Lines", summary.get("line_count")),
			("Next Required Date", summary.get("next_date")),
		),
	}


def _stock_posture_related_panel(
	decoded: dict[str, str],
	inbound_rows: list[dict[str, object]],
	outbound_rows: list[dict[str, object]],
) -> dict[str, object]:
	related = _stock_posture_related_rows(decoded, inbound_rows, outbound_rows)
	return {
		"title": "Related Reviews",
		"summary": "Custom Warehouse review paths connected to this item and warehouse.",
		"items": [{"label": row.get("label") or "", "value": row.get("detail") or ""} for row in related],
	}


def _stock_posture_inbound_rows(item_code: str, warehouse: str) -> list[dict[str, object]]:
	if not _can_read("Purchase Order"):
		return []
	po_records = _safe_get_list(
		"Purchase Order",
		fields=_available_fields("Purchase Order", PURCHASE_ORDER_INBOUND_FIELDS),
		filters=_purchase_order_inbound_filters({}),
		order_by="schedule_date asc, modified desc",
		limit=INBOUND_SCAN_LIMIT,
	)
	po_map = {cstr(record.get("name")).strip(): record for record in po_records if cstr(record.get("name")).strip()}
	if not po_map:
		return []
	rows = []
	if _can_read("Purchase Order Item"):
		rows = _safe_get_all(
			"Purchase Order Item",
			fields=_available_fields("Purchase Order Item", PURCHASE_ORDER_ITEM_INBOUND_FIELDS),
			filters={"parent": ["in", sorted(po_map)]},
			order_by="schedule_date asc, expected_delivery_date asc, idx asc",
			limit=min(max(len(po_map) * 10, 120), 1200),
		)
	if not rows:
		rows = _stock_exception_purchase_lines_from_orders(po_map)
	result: list[dict[str, object]] = []
	horizon = getdate(nowdate()) + timedelta(days=STOCK_EXCEPTIONS_HORIZON_DAYS)
	for row in rows:
		parent = cstr(row.get("parent")).strip()
		po_record = po_map.get(parent) or {}
		row_item = cstr(row.get("item_code")).strip()
		row_warehouse = cstr(row.get("warehouse") or po_record.get("set_warehouse")).strip()
		if row_item != item_code or row_warehouse != warehouse:
			continue
		remaining = max(flt(row.get("qty")) - flt(row.get("received_qty")), 0)
		if remaining <= 0:
			continue
		expected_date = cstr(row.get("expected_delivery_date") or row.get("schedule_date") or po_record.get("schedule_date")).strip()
		if expected_date and _date_key(expected_date) > horizon:
			continue
		result.append(
			{
				"key": f"{parent}:{item_code}:{row_warehouse}",
				"purchase_order": parent,
				"supplier": cstr(po_record.get("supplier_name") or po_record.get("supplier") or "-").strip(),
				"item_code": item_code,
				"item_name": cstr(row.get("item_name") or "").strip(),
				"expected_date": expected_date,
				"expected_qty": _number_text(remaining),
				"uom": cstr(row.get("stock_uom") or row.get("uom") or "").strip(),
				"warehouse": row_warehouse,
				"status": cstr(po_record.get("status") or "").strip(),
				"route_target": {"route": "warehouse-console-receiving", "purchase_order": parent},
			}
		)
		if len(result) >= STOCK_POSTURE_INBOUND_LIMIT:
			break
	return sorted(result, key=lambda row: (_date_key(row.get("expected_date")), cstr(row.get("purchase_order"))))


def _stock_posture_outbound_rows(item_code: str, warehouse: str) -> list[dict[str, object]]:
	if not _can_read("Sales Order"):
		return []
	so_records = _safe_get_list(
		"Sales Order",
		fields=_available_fields("Sales Order", SALES_ORDER_OUTBOUND_FIELDS),
		filters=_sales_order_outbound_filters({}),
		order_by="delivery_date asc, modified desc",
		limit=STOCK_EXCEPTIONS_SCAN_LIMIT,
	)
	so_map = {cstr(record.get("name")).strip(): record for record in so_records if cstr(record.get("name")).strip()}
	if not so_map:
		return []
	rows = []
	if _can_read("Sales Order Item"):
		rows = _safe_get_all(
			"Sales Order Item",
			fields=_available_fields("Sales Order Item", SALES_ORDER_ITEM_DETAIL_FIELDS),
			filters={"parent": ["in", sorted(so_map)]},
			order_by="delivery_date asc, idx asc",
			limit=min(max(len(so_map) * 12, 120), 1200),
		)
	if not rows:
		rows = _stock_exception_lines_from_orders(so_map)
	result: list[dict[str, object]] = []
	for row in rows:
		parent = cstr(row.get("parent")).strip()
		so_record = so_map.get(parent) or {}
		row_item = cstr(row.get("item_code")).strip()
		row_warehouse = cstr(row.get("warehouse") or so_record.get("set_warehouse")).strip()
		pending_qty = max(flt(row.get("qty")) - flt(row.get("delivered_qty")), 0)
		if row_item != item_code or row_warehouse != warehouse or pending_qty <= 0:
			continue
		required_date = cstr(row.get("delivery_date") or so_record.get("delivery_date") or "").strip()
		result.append(
			{
				"key": f"{parent}:{item_code}:{row_warehouse}",
				"sales_order": parent,
				"customer": cstr(so_record.get("customer_name") or so_record.get("customer") or "-").strip(),
				"item_code": item_code,
				"item_name": cstr(row.get("item_name") or "").strip(),
				"required_date": required_date,
				"ordered_qty": _number_text(row.get("qty")),
				"delivered_qty": _number_text(row.get("delivered_qty")),
				"pending_qty": _number_text(pending_qty),
				"uom": cstr(row.get("stock_uom") or row.get("uom") or "").strip(),
				"warehouse": row_warehouse,
				"status": cstr(so_record.get("status") or "").strip(),
				"route_target": {"route": "warehouse-console-picking", "sales_order": parent},
			}
		)
		if len(result) >= STOCK_POSTURE_OUTBOUND_LIMIT:
			break
	return sorted(result, key=lambda row: (_date_key(row.get("required_date")), cstr(row.get("sales_order"))))


def _stock_posture_inbound_summary(rows: list[dict[str, object]]) -> dict[str, object]:
	total = sum(flt(row.get("expected_qty")) for row in rows)
	dates = [row.get("expected_date") for row in rows if cstr(row.get("expected_date")).strip()]
	return {
		"expected_qty": total,
		"next_date": min(dates, key=_date_key) if dates else "",
		"order_count": len({cstr(row.get("purchase_order")).strip() for row in rows if cstr(row.get("purchase_order")).strip()}),
	}


def _stock_posture_outbound_summary(rows: list[dict[str, object]]) -> dict[str, object]:
	total = sum(flt(row.get("pending_qty")) for row in rows)
	dates = [row.get("required_date") for row in rows if cstr(row.get("required_date")).strip()]
	return {
		"pending_qty": total,
		"next_date": min(dates, key=_date_key) if dates else "",
		"line_count": len(rows),
	}


def _stock_posture_item_name(item_code: str, outbound_rows: list[dict[str, object]], inbound_rows: list[dict[str, object]]) -> str:
	for row in [*outbound_rows, *inbound_rows]:
		if cstr(row.get("item_code")).strip() == item_code and cstr(row.get("item_name")).strip():
			return cstr(row.get("item_name")).strip()
	return ""


def _stock_posture_label(
	available_qty: object,
	pending_qty: object,
	expected_qty: object,
) -> dict[str, str]:
	if available_qty is None:
		return {"label": "Warehouse Posture Missing", "explanation": "Current stock posture is not visible for this item and warehouse."}
	pending = flt(pending_qty)
	available = flt(available_qty)
	if pending <= 0:
		return {"label": "No Open Demand", "explanation": "No open outbound demand is visible for this item and warehouse."}
	if available >= pending:
		return {"label": "Covered", "explanation": "Visible stock covers current open outbound demand."}
	if flt(expected_qty) > 0:
		return {"label": "Inbound Cover Expected", "explanation": "Visible stock is short, with inbound cover expected soon."}
	return {"label": "Needs Stock Review", "explanation": "Visible stock is short for open outbound demand."}


def _stock_posture_related_rows(
	decoded: dict[str, str],
	inbound_rows: list[dict[str, object]],
	outbound_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
	rows: list[dict[str, object]] = []
	sales_order = cstr(decoded.get("sales_order")).strip() or cstr((outbound_rows[0] if outbound_rows else {}).get("sales_order")).strip()
	purchase_order = cstr(decoded.get("purchase_order")).strip() or cstr((inbound_rows[0] if inbound_rows else {}).get("purchase_order")).strip()
	stock_exception_token = cstr(decoded.get("stock_exception_token")).strip()
	if sales_order:
		rows.append(
			{
				"key": "picking",
				"title": sales_order,
				"label": "Picking Posture",
				"detail": "Review outbound readiness inside Warehouse.",
				"route_target": {"route": "warehouse-console-picking", "sales_order": sales_order},
			}
		)
	if purchase_order:
		rows.append(
			{
				"key": "receiving",
				"title": purchase_order,
				"label": "Inbound Cover",
				"detail": "Review expected inbound cover inside Warehouse.",
				"route_target": {"route": "warehouse-console-receiving", "purchase_order": purchase_order},
			}
		)
	if stock_exception_token:
		rows.append(
			{
				"key": "stock_exception",
				"title": "Stock Exception",
				"label": "Exception Review",
				"detail": "Return to the stock exception context.",
				"route_target": {"route": "warehouse-console-stock-exception", "context_token": stock_exception_token},
			}
		)
	return rows


def _stock_posture_action_targets(
	decoded: dict[str, str],
	inbound_rows: list[dict[str, object]],
	outbound_rows: list[dict[str, object]],
) -> dict[str, dict[str, str]]:
	targets: dict[str, dict[str, str]] = {
		"back": {"route": "warehouse-console-worklist", "queue_key": STOCK_EXCEPTIONS_KEY},
	}
	related = _stock_posture_related_rows(decoded, inbound_rows, outbound_rows)
	for row in related:
		target = row.get("route_target") if isinstance(row, dict) else {}
		route = cstr((target or {}).get("route")).strip()
		if route == "warehouse-console-picking":
			targets["picking"] = {"route": route, "sales_order": cstr((target or {}).get("sales_order")).strip()}
		elif route == "warehouse-console-receiving":
			targets["receiving"] = {"route": route, "purchase_order": cstr((target or {}).get("purchase_order")).strip()}
		elif route == "warehouse-console-stock-exception":
			targets["stock_exception"] = {"route": route, "context_token": cstr((target or {}).get("context_token")).strip()}
	if "stock_exception" in targets:
		targets["back"] = dict(targets["stock_exception"])
	elif "picking" in targets:
		targets["back"] = dict(targets["picking"])
	elif "receiving" in targets:
		targets["back"] = dict(targets["receiving"])
	return targets


def _stock_posture_context_token(
	item_code: object,
	warehouse: object,
	*,
	sales_order: object = "",
	purchase_order: object = "",
	stock_exception_token: object = "",
) -> str:
	payload = {
		"item_code": cstr(item_code).strip(),
		"purchase_order": cstr(purchase_order).strip(),
		"sales_order": cstr(sales_order).strip(),
		"stock_exception_token": cstr(stock_exception_token).strip(),
		"warehouse": cstr(warehouse).strip(),
	}
	return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8").hex()


def _decode_stock_posture_context(context_token: str) -> dict[str, str]:
	token = cstr(context_token).strip()
	if not token:
		return {}
	try:
		payload = json.loads(bytes.fromhex(token).decode("utf-8"))
	except Exception:
		_clear_transient_frappe_messages()
		return {}
	if not isinstance(payload, dict):
		return {}
	return {
		"item_code": cstr(payload.get("item_code")).strip(),
		"warehouse": cstr(payload.get("warehouse")).strip(),
		"sales_order": cstr(payload.get("sales_order")).strip(),
		"purchase_order": cstr(payload.get("purchase_order")).strip(),
		"stock_exception_token": cstr(payload.get("stock_exception_token")).strip(),
	}


def _stock_exception_context_token(sales_order: str, item_code: str, warehouse: str) -> str:
	payload = {
		"sales_order": cstr(sales_order).strip(),
		"item_code": cstr(item_code).strip(),
		"warehouse": cstr(warehouse).strip(),
	}
	return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8").hex()


def _decode_stock_exception_context(context_token: str) -> dict[str, str]:
	token = cstr(context_token).strip()
	if not token:
		return {}
	try:
		payload = json.loads(bytes.fromhex(token).decode("utf-8"))
	except Exception:
		_clear_transient_frappe_messages()
		return {}
	if not isinstance(payload, dict):
		return {}
	return {
		"sales_order": cstr(payload.get("sales_order")).strip(),
		"item_code": cstr(payload.get("item_code")).strip(),
		"warehouse": cstr(payload.get("warehouse")).strip(),
	}


def _stock_exception_controls(filters: dict[str, str]) -> dict[str, object]:
	return {
		"fields": [
			{
				"key": "state",
				"label": "Exception State",
				"type": "select",
				"value": filters.get("state", ""),
				"options": [
					{"label": "All", "value": ""},
					{"label": "Needs Stock Review", "value": "needs_stock_review"},
					{"label": "Inbound Cover Expected", "value": "inbound_cover_expected"},
					{"label": "Urgent / Aging Demand", "value": "urgent_aging"},
					{"label": "Warehouse Posture Missing", "value": "warehouse_posture_missing"},
				],
			},
			{"key": "warehouse", "label": "Warehouse", "type": "text", "value": filters.get("warehouse", ""), "placeholder": "Filter warehouse"},
			{"key": "text", "label": "Order, Item, Customer", "type": "text", "value": filters.get("text", ""), "placeholder": "Filter order, item, or customer"},
		],
		"actions": [
			{"key": "refresh", "label": "Refresh"},
			{"key": "reset_filters", "label": "Reset"},
			{"key": "apply_filters", "label": "Apply", "kind": "primary"},
		],
		"scopeChips": ["Sales Orders", "Inbound cover", "Read-only exceptions"],
	}


def _stock_exception_rows(filters: dict[str, str], *, row_limit: int) -> list[dict[str, object]]:
	records = _safe_get_list(
		"Sales Order",
		fields=_available_fields("Sales Order", SALES_ORDER_OUTBOUND_FIELDS),
		filters=_sales_order_outbound_filters({}),
		order_by="delivery_date asc, modified desc",
		limit=STOCK_EXCEPTIONS_SCAN_LIMIT,
	)
	if not records:
		return []

	orders = {cstr(record.get("name")).strip(): record for record in records if cstr(record.get("name")).strip()}
	line_rows = []
	if _can_read("Sales Order Item"):
		line_rows = _safe_get_all(
			"Sales Order Item",
			fields=_available_fields("Sales Order Item", SALES_ORDER_ITEM_DETAIL_FIELDS),
			filters={"parent": ["in", sorted(orders)]},
			order_by="delivery_date asc, idx asc",
			limit=min(max(len(orders) * 12, 120), 1200),
		)
	if not line_rows:
		line_rows = _stock_exception_lines_from_orders(orders)
	pairs = _stock_exception_pairs(line_rows)
	stock = _stock_exception_stock_map(pairs)
	inbound = _stock_exception_inbound_map(pairs)
	rows: list[dict[str, object]] = []
	for line in line_rows:
		row = _stock_exception_row(line, orders.get(cstr(line.get("parent")).strip()) or {}, stock, inbound)
		if not row:
			continue
		if not _stock_exception_row_matches(row, filters):
			continue
		rows.append(row)
		if len(rows) >= row_limit:
			break
	return sorted(rows, key=lambda row: (STOCK_EXCEPTIONS_GROUP_ORDER.index(row.get("exception_key")) if row.get("exception_key") in STOCK_EXCEPTIONS_GROUP_ORDER else 99, _date_key(row.get("required_date")), cstr(row.get("sales_order"))))


def _stock_exception_lines_from_orders(orders: dict[str, dict[str, object]]) -> list[dict[str, object]]:
	rows: list[dict[str, object]] = []
	limit = min(max(len(orders) * 12, 120), 1200)
	for order_name in sorted(orders):
		try:
			doc = frappe.get_doc("Sales Order", order_name)
			doc.check_permission("read")
		except Exception:
			_clear_transient_frappe_messages()
			continue
		for child in list(doc.get("items") or [])[:12]:
			row: dict[str, object] = {"parent": order_name}
			for field in SALES_ORDER_ITEM_DETAIL_FIELDS:
				if hasattr(child, "get"):
					row[field] = child.get(field)
				else:
					row[field] = getattr(child, field, None)
			row["parent"] = row.get("parent") or order_name
			rows.append(row)
			if len(rows) >= limit:
				return sorted(rows, key=lambda row: (_date_key(row.get("delivery_date")), int(flt(row.get("idx")) or 0)))
	return sorted(rows, key=lambda row: (_date_key(row.get("delivery_date")), int(flt(row.get("idx")) or 0)))


def _stock_exception_pairs(line_rows: list[dict[str, object]]) -> set[tuple[str, str]]:
	pairs: set[tuple[str, str]] = set()
	for line in line_rows:
		item_code = cstr(line.get("item_code")).strip()
		warehouse = cstr(line.get("warehouse")).strip()
		if item_code and warehouse and max(flt(line.get("qty")) - flt(line.get("delivered_qty")), 0) > 0:
			pairs.add((item_code, warehouse))
	return pairs


def _stock_exception_stock_map(pairs: set[tuple[str, str]]) -> dict[tuple[str, str], dict[str, float]]:
	if not pairs or not _can_read("Bin"):
		return {}
	items = sorted({item for item, _warehouse in pairs})
	warehouses = sorted({warehouse for _item, warehouse in pairs})
	rows = _safe_get_all(
		"Bin",
		fields=_available_fields("Bin", BIN_OUTBOUND_FIELDS),
		filters={"item_code": ["in", items], "warehouse": ["in", warehouses]},
		limit=min(max(len(pairs) * 2, 80), 1200),
	)
	result: dict[tuple[str, str], dict[str, float]] = {}
	for row in rows:
		item_code = cstr(row.get("item_code")).strip()
		warehouse = cstr(row.get("warehouse")).strip()
		if not item_code or not warehouse:
			continue
		actual_qty = flt(row.get("actual_qty"))
		reserved_qty = max(flt(row.get("reserved_qty")), 0)
		result[(item_code, warehouse)] = {
			"actual_qty": actual_qty,
			"reserved_qty": reserved_qty,
			"available_qty": actual_qty - reserved_qty,
			"projected_qty": flt(row.get("projected_qty")),
		}
	return result


def _stock_exception_inbound_map(pairs: set[tuple[str, str]]) -> dict[tuple[str, str], dict[str, object]]:
	if not pairs or not _can_read("Purchase Order"):
		return {}
	po_records = _safe_get_list(
		"Purchase Order",
		fields=_available_fields("Purchase Order", PURCHASE_ORDER_INBOUND_FIELDS),
		filters=_purchase_order_inbound_filters({}),
		order_by="schedule_date asc, modified desc",
		limit=INBOUND_SCAN_LIMIT,
	)
	po_map = {cstr(record.get("name")).strip(): record for record in po_records if cstr(record.get("name")).strip()}
	if not po_map:
		return {}
	rows = []
	if _can_read("Purchase Order Item"):
		rows = _safe_get_all(
			"Purchase Order Item",
			fields=_available_fields("Purchase Order Item", PURCHASE_ORDER_ITEM_INBOUND_FIELDS),
			filters={"parent": ["in", sorted(po_map)]},
			order_by="schedule_date asc, expected_delivery_date asc, idx asc",
			limit=min(max(len(po_map) * 10, 120), 1200),
		)
	if not rows:
		rows = _stock_exception_purchase_lines_from_orders(po_map)
	horizon = getdate(nowdate()) + timedelta(days=STOCK_EXCEPTIONS_HORIZON_DAYS)
	result: dict[tuple[str, str], dict[str, object]] = {}
	for row in rows:
		parent = cstr(row.get("parent")).strip()
		po_record = po_map.get(parent) or {}
		item_code = cstr(row.get("item_code")).strip()
		warehouse = cstr(row.get("warehouse") or po_record.get("set_warehouse")).strip()
		pair = (item_code, warehouse)
		if pair not in pairs:
			continue
		remaining = max(flt(row.get("qty")) - flt(row.get("received_qty")), 0)
		if remaining <= 0:
			continue
		expected_date = cstr(row.get("expected_delivery_date") or row.get("schedule_date") or po_record.get("schedule_date")).strip()
		if expected_date and _date_key(expected_date) > horizon:
			continue
		entry = result.setdefault(pair, {"expected_inbound_qty": 0.0, "expected_inbound_date": expected_date, "purchase_order": parent})
		entry["expected_inbound_qty"] = flt(entry.get("expected_inbound_qty")) + remaining
		if expected_date and (not entry.get("expected_inbound_date") or _date_key(expected_date) < _date_key(entry.get("expected_inbound_date"))):
			entry["expected_inbound_date"] = expected_date
			entry["purchase_order"] = parent
	return result


def _stock_exception_purchase_lines_from_orders(po_map: dict[str, dict[str, object]]) -> list[dict[str, object]]:
	rows: list[dict[str, object]] = []
	limit = min(max(len(po_map) * 10, 120), 1200)
	for purchase_order in sorted(po_map):
		try:
			doc = frappe.get_doc("Purchase Order", purchase_order)
			doc.check_permission("read")
		except Exception:
			_clear_transient_frappe_messages()
			continue
		for child in list(doc.get("items") or [])[:10]:
			row: dict[str, object] = {"parent": purchase_order}
			for field in PURCHASE_ORDER_ITEM_INBOUND_FIELDS:
				if hasattr(child, "get"):
					row[field] = child.get(field)
				else:
					row[field] = getattr(child, field, None)
			row["parent"] = row.get("parent") or purchase_order
			rows.append(row)
			if len(rows) >= limit:
				return sorted(rows, key=lambda row: (_date_key(row.get("schedule_date") or row.get("expected_delivery_date")), int(flt(row.get("idx")) or 0)))
	return sorted(rows, key=lambda row: (_date_key(row.get("schedule_date") or row.get("expected_delivery_date")), int(flt(row.get("idx")) or 0)))


def _stock_exception_row(
	line: dict[str, object],
	order: dict[str, object],
	stock: dict[tuple[str, str], dict[str, float]],
	inbound: dict[tuple[str, str], dict[str, object]],
) -> dict[str, object] | None:
	sales_order = cstr(line.get("parent")).strip()
	item_code = cstr(line.get("item_code")).strip()
	warehouse = cstr(line.get("warehouse") or order.get("set_warehouse")).strip()
	pending_qty = max(flt(line.get("qty")) - flt(line.get("delivered_qty")), 0)
	if not sales_order or pending_qty <= 0:
		return None
	pair = (item_code, warehouse)
	stock_info = stock.get(pair)
	available_qty = flt(stock_info.get("available_qty")) if stock_info else None
	projected_qty = flt(stock_info.get("projected_qty")) if stock_info else None
	inbound_info = inbound.get(pair) or {}
	exception_key = _stock_exception_key(line, order, available_qty, inbound_info)
	if not exception_key:
		return None
	short_qty = pending_qty if available_qty is None else max(pending_qty - flt(available_qty), 0)
	context_token = _stock_exception_context_token(sales_order, item_code, warehouse)
	return {
		"key": f"{sales_order}:{item_code}:{warehouse or 'warehouse-missing'}",
		"context_token": context_token,
		"sales_order": sales_order,
		"customer": cstr(order.get("customer_name") or order.get("customer") or "-").strip(),
		"item_code": item_code,
		"item_name": cstr(line.get("item_name") or "").strip(),
		"required_date": cstr(line.get("delivery_date") or order.get("delivery_date") or "").strip(),
		"pending_qty": _number_text(pending_qty),
		"delivered_qty": _number_text(line.get("delivered_qty")),
		"uom": cstr(line.get("stock_uom") or line.get("uom") or "").strip(),
		"source_warehouse": warehouse or "Warehouse not set",
		"available_qty": _number_text(available_qty) if available_qty is not None else "N/A",
		"projected_qty": _number_text(projected_qty) if projected_qty is not None else "N/A",
		"short_qty": _number_text(short_qty),
		"expected_inbound_qty": _number_text(inbound_info.get("expected_inbound_qty")) if inbound_info else "0",
		"expected_inbound_date": cstr(inbound_info.get("expected_inbound_date") or "").strip(),
		"expected_inbound_order": cstr(inbound_info.get("purchase_order") or "").strip(),
		"exception_key": exception_key,
		"exception_label": _stock_exception_label(exception_key),
		"urgency_label": _age_label(cstr(line.get("delivery_date") or order.get("delivery_date") or "").strip(), "overdue" if _date_key(line.get("delivery_date") or order.get("delivery_date")) < getdate(nowdate()) else "due_today" if _date_key(line.get("delivery_date") or order.get("delivery_date")) == getdate(nowdate()) else "expected_soon"),
		"explanation": _stock_exception_explanation(exception_key, inbound_info),
		"route_targets": _stock_exception_route_targets(sales_order, item_code, warehouse, context_token, inbound_info),
	}


def _stock_exception_key(line: dict[str, object], order: dict[str, object], available_qty: float | None, inbound_info: dict[str, object]) -> str:
	item_code = cstr(line.get("item_code")).strip()
	warehouse = cstr(line.get("warehouse") or order.get("set_warehouse")).strip()
	pending_qty = max(flt(line.get("qty")) - flt(line.get("delivered_qty")), 0)
	if not item_code or not warehouse or available_qty is None:
		return "warehouse_posture_missing"
	if flt(available_qty) >= pending_qty:
		return ""
	if inbound_info and flt(inbound_info.get("expected_inbound_qty")) > 0:
		return "inbound_cover_expected"
	due = _date_key(line.get("delivery_date") or order.get("delivery_date"))
	if due <= getdate(nowdate()):
		return "urgent_aging"
	return "needs_stock_review"


def _stock_exception_label(exception_key: str) -> str:
	return {
		"needs_stock_review": "Needs Stock Review",
		"inbound_cover_expected": "Inbound Cover Expected",
		"urgent_aging": "Urgent / Aging Demand",
		"warehouse_posture_missing": "Warehouse Posture Missing",
	}.get(exception_key, "Needs Stock Review")


def _stock_exception_explanation(exception_key: str, inbound_info: dict[str, object]) -> str:
	if exception_key == "inbound_cover_expected":
		return "Visible stock is short, with inbound cover expected soon."
	if exception_key == "urgent_aging":
		return "Demand is due now or past due and visible stock is short."
	if exception_key == "warehouse_posture_missing":
		return "Warehouse or stock posture is missing for this line."
	return "Visible stock is short for this outbound line."


def _stock_exception_route_targets(
	sales_order: str,
	item_code: str,
	warehouse: str,
	context_token: str,
	inbound_info: dict[str, object],
) -> dict[str, dict[str, str]]:
	targets = {
		"exception_review": {
			"route": "warehouse-console-stock-exception",
			"context_token": context_token,
			"sales_order": sales_order,
			"item_code": item_code,
			"warehouse": warehouse,
		},
		"picking": {"route": "warehouse-console-picking", "sales_order": sales_order},
	}
	purchase_order = cstr(inbound_info.get("purchase_order") if inbound_info else "").strip()
	if purchase_order:
		targets["receiving"] = {"route": "warehouse-console-receiving", "purchase_order": purchase_order}
	return targets


def _stock_exception_row_matches(row: dict[str, object], filters: dict[str, str]) -> bool:
	state_filter = cstr(filters.get("state")).strip()
	if state_filter and row.get("exception_key") != state_filter:
		return False
	warehouse_filter = cstr(filters.get("warehouse")).strip().lower()
	if warehouse_filter and warehouse_filter not in cstr(row.get("source_warehouse")).strip().lower():
		return False
	text_filter = cstr(filters.get("text")).strip().lower()
	if text_filter:
		haystack = " ".join(cstr(row.get(key)).lower() for key in ("sales_order", "customer", "item_code", "item_name"))
		if text_filter not in haystack:
			return False
	return True


def _build_outbound_visibility(
	filters: dict[str, str] | None = None,
	*,
	preview_limit: int = OUTBOUND_OVERVIEW_LIMIT,
	row_limit: int = OUTBOUND_QUEUE_LIMIT,
) -> dict[str, object]:
	applied_filters = filters or {}
	if not _can_read("Sales Order"):
		return {
			"state": restricted_state(),
			"counts": _empty_outbound_counts(),
			"cards": _outbound_cards(_empty_outbound_counts()),
			"preview_rows": [],
			"groups": [group for group in _empty_outbound_groups().values()],
			"total_count": 0,
			"queue_key": OUTBOUND_QUEUE_KEY,
			"queue_route": "warehouse-console-worklist",
		}

	rows = _outbound_rows(applied_filters, row_limit=row_limit)
	counts = _empty_outbound_counts()
	groups = _empty_outbound_groups()
	for row in rows:
		group_key = cstr(row.get("state_key")).strip() or "expected_soon"
		if group_key not in counts:
			group_key = "expected_soon"
		counts[group_key] += 1
		groups[group_key]["rows"].append(row)

	total_count = len(rows)
	payload_state = ready_state() if total_count else state(
		"empty",
		"No outbound picking needs attention",
		"No outbound picking needs attention.",
	)
	return {
		"state": payload_state,
		"counts": counts,
		"cards": _outbound_cards(counts),
		"preview_rows": rows[:preview_limit],
		"groups": [groups[key] for key in OUTBOUND_GROUP_ORDER],
		"total_count": total_count,
		"queue_key": OUTBOUND_QUEUE_KEY,
		"queue_route": "warehouse-console-worklist",
		"row_limit": row_limit,
		"horizon_days": OUTBOUND_HORIZON_DAYS,
	}


def _empty_outbound_counts() -> dict[str, int]:
	return {key: 0 for key in OUTBOUND_GROUP_ORDER}


def _empty_outbound_groups() -> dict[str, dict[str, object]]:
	labels = {
		"overdue": ("Overdue", "Past delivery date."),
		"due_today": ("Due Today", "Required today."),
		"ready_to_pick": ("Ready to Pick", "Visible stock posture looks ready."),
		"partially_picked": ("Partially Picked", "Some quantity has already moved."),
		"needs_stock_review": ("Needs Stock Review", "Stock posture needs warehouse review."),
		"expected_soon": ("Expected Soon", f"Due in the next {OUTBOUND_HORIZON_DAYS} days."),
	}
	return {
		key: {"key": key, "title": labels[key][0], "summary": labels[key][1], "rows": []}
		for key in OUTBOUND_GROUP_ORDER
	}


def _outbound_cards(counts: dict[str, int]) -> list[dict[str, object]]:
	card_specs = [
		("due_today", "Picking Due Today", "Required today."),
		("overdue", "Overdue Picking", "Past delivery date."),
		("ready_to_pick", "Ready to Pick", "Visible stock posture looks ready."),
		("needs_stock_review", "Needs Stock Review", "Stock posture needs warehouse review."),
	]
	return [
		{
			"key": key,
			"label": label,
			"title": label,
			"value": int(counts.get(key) or 0),
			"state": "live",
			"note": note,
			"empty_message": "No outbound picking needs attention.",
		}
		for key, label, note in card_specs
	]


def _outbound_section_cards(outbound: dict[str, object] | None) -> list[dict[str, object]]:
	cards = outbound.get("cards") if isinstance(outbound, dict) else []
	result: list[dict[str, object]] = []
	for card in cards if isinstance(cards, list) else []:
		if not isinstance(card, dict):
			continue
		result.append(
			{
				"key": card.get("key"),
				"title": card.get("title") or card.get("label"),
				"value": card.get("value"),
				"state": card.get("state") or "live",
				"note": card.get("note") or "",
				"empty_message": card.get("empty_message") or "No outbound picking needs attention.",
			}
		)
	return result


def _outbound_queue_state_payload(
	context: dict[str, object],
	payload_state: dict[str, str],
	filters: dict[str, str],
) -> dict[str, object]:
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": payload_state,
		"page": {"title": "Outbound Picking", "key": OUTBOUND_QUEUE_KEY},
		"summary": {
			"title": "Outbound Picking",
			"subtitle": payload_state.get("detail") or "Outbound picking work could not be loaded.",
			"chips": [{"label": payload_state.get("kind") or "state"}],
		},
		"controls": _outbound_controls(filters),
		"cards": _outbound_cards(_empty_outbound_counts()),
		"groups": [group for group in _empty_outbound_groups().values()],
		"rows": [],
		"action_targets": {},
		"valuation": {"visible": False, "fields": []},
		"fetched_at": str(now_datetime()),
	}


def _outbound_queue_payload(
	context: dict[str, object],
	outbound: dict[str, object],
	filters: dict[str, str],
) -> dict[str, object]:
	return {
		"workspace": warehouse_workspace_public_context(),
		"context": context,
		"state": outbound.get("state") or ready_state(),
		"page": {"title": "Outbound Picking", "key": OUTBOUND_QUEUE_KEY},
		"summary": {
			"title": "Outbound Picking",
			"subtitle": "Pending customer demand waiting for warehouse review.",
			"chips": [{"label": "Read-only"}, {"label": f"{outbound.get('total_count') or 0} shown"}],
		},
		"controls": _outbound_controls(filters),
		"cards": outbound.get("cards") or [],
		"groups": outbound.get("groups") or [],
		"rows": outbound.get("preview_rows") or [],
		"action_targets": {},
		"valuation": {"visible": False, "fields": []},
		"fetched_at": str(now_datetime()),
	}


def _outbound_controls(filters: dict[str, str]) -> dict[str, object]:
	return {
		"fields": [
			{"key": "sales_order", "label": "Sales Order", "type": "text", "value": filters.get("sales_order", ""), "placeholder": "Search order"},
			{"key": "customer", "label": "Customer", "type": "text", "value": filters.get("customer", ""), "placeholder": "Search customer"},
			{"key": "warehouse", "label": "Warehouse", "type": "text", "value": filters.get("warehouse", ""), "placeholder": "Search warehouse"},
			{
				"key": "state",
				"label": "Picking State",
				"type": "select",
				"value": filters.get("state", ""),
				"options": [
					{"label": "All", "value": ""},
					{"label": "Overdue", "value": "overdue"},
					{"label": "Due Today", "value": "due_today"},
					{"label": "Ready to Pick", "value": "ready_to_pick"},
					{"label": "Partially Picked", "value": "partially_picked"},
					{"label": "Needs Stock Review", "value": "needs_stock_review"},
					{"label": "Expected Soon", "value": "expected_soon"},
				],
			},
		],
		"actions": [
			{"key": "refresh", "label": "Refresh"},
			{"key": "reset_filters", "label": "Reset"},
			{"key": "apply_filters", "label": "Apply", "kind": "primary"},
		],
		"scopeChips": ["Sales Orders", "Read-only outbound"],
	}


def _outbound_rows(filters: dict[str, str], *, row_limit: int) -> list[dict[str, object]]:
	records = _safe_get_list(
		"Sales Order",
		fields=_available_fields("Sales Order", SALES_ORDER_OUTBOUND_FIELDS),
		filters=_sales_order_outbound_filters(filters),
		order_by="delivery_date asc, modified desc",
		limit=OUTBOUND_SCAN_LIMIT,
	)
	if not records:
		return []

	names = [cstr(record.get("name")).strip() for record in records if cstr(record.get("name")).strip()]
	line_map = _outbound_line_summary(names)
	rows: list[dict[str, object]] = []
	for record in records:
		name = cstr(record.get("name")).strip()
		if not name:
			continue
		summary = line_map.get(name) or _outbound_fallback_summary(record)
		warehouse_filter = cstr(filters.get("warehouse")).strip().lower()
		if warehouse_filter and warehouse_filter not in {cstr(warehouse).strip().lower() for warehouse in summary.get("warehouses") or []}:
			continue
		row = _outbound_row(record, summary)
		if not row:
			continue
		filter_state = cstr(filters.get("state")).strip()
		if filter_state and row.get("state_key") != filter_state:
			continue
		rows.append(row)
		if len(rows) >= row_limit:
			break
	return rows


def _sales_order_outbound_filters(filters: dict[str, str]) -> list[list[object]]:
	conditions: list[list[object]] = [["Sales Order", "docstatus", "=", 1]]
	if _has_field("Sales Order", "per_delivered"):
		conditions.append(["Sales Order", "per_delivered", "<", 100])
	if _has_field("Sales Order", "status"):
		status = cstr(filters.get("status")).strip()
		if status and status in OUTBOUND_OPEN_STATUSES:
			conditions.append(["Sales Order", "status", "=", status])
		else:
			conditions.append(["Sales Order", "status", "in", list(OUTBOUND_OPEN_STATUSES)])
	sales_order = cstr(filters.get("sales_order")).strip()
	if sales_order:
		conditions.append(["Sales Order", "name", "like", f"%{sales_order}%"])
	customer = cstr(filters.get("customer")).strip()
	if customer:
		if _has_field("Sales Order", "customer_name"):
			conditions.append(["Sales Order", "customer_name", "like", f"%{customer}%"])
		else:
			conditions.append(["Sales Order", "customer", "like", f"%{customer}%"])
	return conditions


def _outbound_line_summary(order_names: list[str]) -> dict[str, dict[str, object]]:
	if not order_names:
		return {}
	rows = _safe_get_all(
		"Sales Order Item",
		fields=_available_fields("Sales Order Item", SALES_ORDER_ITEM_OUTBOUND_FIELDS),
		filters={"parent": ["in", order_names]},
		order_by="delivery_date asc, idx asc",
		limit=min(max(len(order_names) * 8, 80), 900),
	)
	summary: dict[str, dict[str, object]] = defaultdict(lambda: {
		"open_lines": 0,
		"item_codes": set(),
		"warehouses": set(),
		"earliest_date": "",
		"remaining_by_uom": defaultdict(float),
		"requirements": defaultdict(float),
		"lines": [],
	})
	for row in rows:
		parent = cstr(row.get("parent")).strip()
		if not parent:
			continue
		remaining = max(flt(row.get("qty")) - flt(row.get("delivered_qty")), 0)
		if remaining <= 0:
			continue
		due_date = cstr(row.get("delivery_date")).strip()
		warehouse = cstr(row.get("warehouse")).strip()
		item_code = cstr(row.get("item_code")).strip()
		uom = cstr(row.get("stock_uom") or row.get("uom") or "").strip()
		summary[parent]["open_lines"] = int(summary[parent].get("open_lines") or 0) + 1
		if item_code:
			summary[parent]["item_codes"].add(item_code)
		if warehouse:
			summary[parent]["warehouses"].add(warehouse)
		if item_code and warehouse:
			summary[parent]["requirements"][(item_code, warehouse)] += remaining
		if uom:
			summary[parent]["remaining_by_uom"][uom] += remaining
		if due_date and (not summary[parent].get("earliest_date") or _date_key(due_date) < _date_key(summary[parent].get("earliest_date"))):
			summary[parent]["earliest_date"] = due_date
		if len(summary[parent]["lines"]) < 4:
			summary[parent]["lines"].append(
				{
					"item_code": item_code,
					"item_name": cstr(row.get("item_name")).strip(),
					"remaining_qty": _number_text(remaining),
					"uom": uom,
					"target_warehouse": warehouse or "Warehouse not set",
					"required_date": due_date,
				}
			)
	stock_map = _outbound_stock_map([value["requirements"] for value in summary.values()])
	return {
		key: {
			"open_lines": value["open_lines"],
			"item_count": len(value["item_codes"]),
			"warehouses": sorted(value["warehouses"]),
			"earliest_date": value["earliest_date"],
			"remaining_by_uom": dict(value["remaining_by_uom"]),
			"requirements": dict(value["requirements"]),
			"stock_state": _outbound_stock_state(value["requirements"], stock_map),
			"lines": value["lines"],
		}
		for key, value in summary.items()
	}


def _outbound_stock_map(requirement_groups: list[dict[tuple[str, str], float]]) -> dict[tuple[str, str], float]:
	if not _can_read("Bin"):
		return {}
	pairs: set[tuple[str, str]] = set()
	for requirements in requirement_groups:
		pairs.update((item, warehouse) for item, warehouse in requirements if item and warehouse)
	if not pairs:
		return {}
	items = sorted({item for item, _warehouse in pairs})
	warehouses = sorted({warehouse for _item, warehouse in pairs})
	rows = _safe_get_all(
		"Bin",
		fields=_available_fields("Bin", BIN_OUTBOUND_FIELDS),
		filters={"item_code": ["in", items], "warehouse": ["in", warehouses]},
		limit=min(max(len(pairs) * 2, 80), 900),
	)
	stock: dict[tuple[str, str], float] = {}
	for row in rows:
		item_code = cstr(row.get("item_code")).strip()
		warehouse = cstr(row.get("warehouse")).strip()
		if not item_code or not warehouse:
			continue
		stock[(item_code, warehouse)] = max(flt(row.get("actual_qty")) - max(flt(row.get("reserved_qty")), 0), flt(row.get("projected_qty")))
	return stock


def _outbound_stock_state(requirements: dict[tuple[str, str], float], stock: dict[tuple[str, str], float]) -> str:
	if not requirements:
		return "needs_stock_review"
	for pair, required_qty in requirements.items():
		if pair not in stock or flt(stock.get(pair)) < flt(required_qty):
			return "needs_stock_review"
	return "ready_to_pick"


def _outbound_fallback_summary(record: dict[str, object]) -> dict[str, object]:
	warehouse = cstr(record.get("set_warehouse")).strip()
	return {
		"open_lines": 0,
		"item_count": 0,
		"warehouses": [warehouse] if warehouse else [],
		"earliest_date": cstr(record.get("delivery_date")).strip(),
		"remaining_by_uom": {},
		"stock_state": "needs_stock_review",
		"lines": [],
	}


def _outbound_row(record: dict[str, object], summary: dict[str, object]) -> dict[str, object] | None:
	due_date = cstr(summary.get("earliest_date") or record.get("delivery_date")).strip()
	state_key = _outbound_state_key(record, due_date, summary)
	if not state_key:
		return None
	warehouses = [cstr(value).strip() for value in summary.get("warehouses") or [] if cstr(value).strip()]
	name = cstr(record.get("name")).strip()
	return {
		"key": name,
		"name": name,
		"sales_order": name,
		"primary_id": name,
		"customer": cstr(record.get("customer_name") or record.get("customer") or "-").strip(),
		"partner": cstr(record.get("customer_name") or record.get("customer") or "-").strip(),
		"required_date": due_date,
		"target_warehouse": _warehouse_summary(warehouses),
		"line_count": int(summary.get("open_lines") or 0),
		"item_count": int(summary.get("item_count") or 0),
		"delivered_percent": _percent_text(record.get("per_delivered")),
		"remaining_summary": _remaining_summary(summary),
		"status": cstr(record.get("status") or "-").strip(),
		"state_key": state_key,
		"state_label": _outbound_state_label(state_key),
		"age_label": _age_label(due_date, state_key),
		"lines": summary.get("lines") or [],
	}


def _outbound_state_key(record: dict[str, object], due_date: str, summary: dict[str, object]) -> str:
	today = getdate(nowdate())
	horizon = today + timedelta(days=OUTBOUND_HORIZON_DAYS)
	due = _date_key(due_date)
	if due < today:
		return "overdue"
	if due == today:
		return "due_today"
	delivered = flt(record.get("per_delivered"))
	if 0 < delivered < 100:
		return "partially_picked"
	if due > horizon:
		return ""
	stock_state = cstr(summary.get("stock_state")).strip()
	if stock_state == "ready_to_pick":
		return "ready_to_pick"
	if stock_state == "needs_stock_review":
		return "needs_stock_review"
	return "expected_soon"


def _outbound_state_label(state_key: str) -> str:
	return {
		"overdue": "Overdue",
		"due_today": "Due Today",
		"ready_to_pick": "Ready to Pick",
		"partially_picked": "Partially Picked",
		"needs_stock_review": "Needs Stock Review",
		"expected_soon": "Expected Soon",
	}.get(state_key, "Expected Soon")


def _safe_get_list(
	doctype: str,
	*,
	fields: list[str],
	filters: list | dict | None = None,
	order_by: str | None = None,
	limit: int = INBOUND_QUEUE_LIMIT,
) -> list[dict[str, Any]]:
	try:
		return list(
			frappe.get_list(
				doctype,
				fields=fields,
				filters=filters or [],
				order_by=order_by,
				limit_page_length=limit,
			)
		)
	except Exception:
		_clear_transient_frappe_messages()
		try:
			return list(
				frappe.get_all(
					doctype,
					fields=fields,
					filters=filters or [],
					order_by=order_by,
					limit_page_length=limit,
				)
			)
		except Exception:
			_clear_transient_frappe_messages()
			return []


def _safe_get_all(
	doctype: str,
	*,
	fields: list[str],
	filters: list | dict | None = None,
	order_by: str | None = None,
	limit: int = INBOUND_QUEUE_LIMIT,
) -> list[dict[str, Any]]:
	try:
		return list(
			frappe.get_all(
				doctype,
				fields=fields,
				filters=filters or [],
				order_by=order_by,
				limit_page_length=limit,
			)
		)
	except Exception:
		_clear_transient_frappe_messages()
		return []


def _available_fields(doctype: str, fields: list[str]) -> list[str]:
	available: list[str] = []
	for field in fields:
		if field in STANDARD_SAFE_FIELDS or _has_field(doctype, field):
			available.append(field)
	return available or ["name"]


def _date_key(value: object):
	try:
		return getdate(value)
	except Exception:
		return getdate("2999-12-31")


def _percent_text(value: object) -> str:
	number = flt(value)
	if number.is_integer():
		return f"{int(number)}%"
	return f"{number:.1f}%"


def _number_text(value: object) -> str:
	number = flt(value)
	if number.is_integer():
		return str(int(number))
	return f"{number:.2f}".rstrip("0").rstrip(".")
