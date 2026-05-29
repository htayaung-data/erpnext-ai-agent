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

STANDARD_SAFE_FIELDS = frozenset({"name", "parent", "idx", "docstatus", "modified", "owner", "creation"})
RECEIVING_DETAIL_LINE_LIMIT = 80
RECEIVING_DETAIL_HISTORY_ITEM_LIMIT = 120
RECEIVING_DETAIL_HISTORY_LIMIT = 8
PICKING_DETAIL_LINE_LIMIT = 80


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
	inbound = _build_inbound_visibility({}, preview_limit=INBOUND_OVERVIEW_LIMIT, row_limit=INBOUND_QUEUE_LIMIT)
	outbound = _build_outbound_visibility({}, preview_limit=OUTBOUND_OVERVIEW_LIMIT, row_limit=OUTBOUND_QUEUE_LIMIT)
	kpis = _build_overview_kpis(inbound, outbound)
	payload["kpis"] = kpis
	payload["inbound"] = inbound
	payload["outbound"] = outbound
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
