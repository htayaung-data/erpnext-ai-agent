from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import cstr, getdate, nowdate


ROW_LIMIT = 50


def normalize_filters(filters: str | dict[str, object] | None) -> dict[str, str]:
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
		str(key): cstr(value).strip()
		for key, value in source.items()
		if value is not None and cstr(value).strip()
	}


def can_read(doctype: str) -> bool:
	try:
		return bool(frappe.has_permission(doctype, ptype="read"))
	except Exception:
		return False


def can_write(doctype: str) -> bool:
	try:
		return bool(frappe.has_permission(doctype, ptype="write"))
	except Exception:
		return False


def can_create(doctype: str) -> bool:
	try:
		return bool(frappe.has_permission(doctype, ptype="create"))
	except Exception:
		return False


def count(doctype: str, filters: list | dict | None = None) -> int:
	try:
		return int(frappe.db.count(doctype, filters=filters or {}))
	except Exception:
		try:
			return len(frappe.get_all(doctype, filters=filters or {}, fields=["name"], limit_page_length=0))
		except Exception:
			return 0


def get_list(
	doctype: str,
	fields: list[str],
	filters: list | dict | None = None,
	order_by: str | None = None,
	limit: int = ROW_LIMIT,
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
		return []


def today_string() -> str:
	return str(getdate(nowdate()))


def date_days_ago(days: int) -> str:
	return str(getdate(nowdate()) - timedelta(days=days))


def date_days_from_now(days: int) -> str:
	return str(getdate(nowdate()) + timedelta(days=days))


def has_field(doctype: str, fieldname: str) -> bool:
	try:
		return bool(frappe.get_meta(doctype).has_field(fieldname))
	except Exception:
		return False


def state(kind: str, title: str, detail: str, action: dict[str, str] | None = None) -> dict[str, object]:
	payload: dict[str, object] = {
		"kind": kind,
		"title": title,
		"detail": detail,
	}
	if action:
		payload["action"] = action
	return payload


def ready_state() -> dict[str, object]:
	return {"kind": "ready", "title": "Ready"}


def empty_state(title: str = "No visible records", detail: str = "No records match the current filters.") -> dict[str, object]:
	return state("empty", title, detail)


def restricted_state(title: str, doctype: str) -> dict[str, object]:
	return state(
		"restricted",
		title,
		f"You do not have read access to {doctype} records for this Procurement Console view.",
	)


def unavailable_state(title: str = "Queue unavailable", detail: str = "This Procurement Console queue is not available yet.") -> dict[str, object]:
	return state("unavailable", title, detail)


def metric(label: str, value: int | str, meta: str, tone: str = "neutral") -> dict[str, object]:
	return {
		"label": label,
		"value": value,
		"meta": meta,
		"tone": tone,
	}


def live_metric(value: int, note: str = "", badge_class: str = "review") -> dict[str, object]:
	return {
		"state": "live",
		"value": value,
		"note": note,
		"badgeClass": badge_class,
	}


def standard_actions() -> list[dict[str, object]]:
	return [
		{"key": "refresh", "label": "Refresh"},
		{"key": "reset_filters", "label": "Reset"},
		{"key": "apply_filters", "label": "Apply", "kind": "primary"},
	]


PROCUREMENT_NATIVE_FORM_CONTEXTS = {
	"Material Request": {
		"parentLabel": "Purchase Requests",
		"parentRoute": "/desk/procurement-console-worklist/purchase-request-directory",
		"defaultLeafLabel": "Purchase Request",
	},
	"Request for Quotation": {
		"parentLabel": "RFQs",
		"parentRoute": "/desk/procurement-console-worklist/rfq-directory",
		"defaultLeafLabel": "RFQ",
	},
	"Supplier Quotation": {
		"parentLabel": "Supplier Quotations",
		"parentRoute": "/desk/procurement-console-worklist/supplier-quotation-directory",
		"defaultLeafLabel": "Supplier Quotation",
	},
	"Purchase Order": {
		"parentLabel": "Purchase Orders",
		"parentRoute": "/desk/procurement-console-worklist/purchase-order-directory",
		"defaultLeafLabel": "Purchase Order",
	},
	"Supplier": {
		"parentLabel": "Suppliers",
		"parentRoute": "/desk/procurement-console-worklist/supplier-directory",
		"defaultLeafLabel": "ERP Supplier Form",
	},
	"Item": {
		"parentLabel": "Buying Items",
		"parentRoute": "/desk/procurement-console-worklist/buying-item-directory",
		"defaultLeafLabel": "ERP Item Form",
	},
}


def native_form_context(doctype: str, name: str | None = None, leaf_label: str | None = None) -> dict[str, object]:
	base = PROCUREMENT_NATIVE_FORM_CONTEXTS.get(doctype) or {}
	label = cstr(leaf_label).strip() or cstr(name).strip() or cstr(base.get("defaultLeafLabel")).strip() or doctype
	return {
		"workspace": "procurement",
		"doctype": doctype,
		"homeLabel": "Procurement Console",
		"homeRoute": "/desk/procurement-console",
		"parentLabel": base.get("parentLabel") or "Procurement",
		"parentRoute": base.get("parentRoute") or "/desk/procurement-console",
		"leafLabel": label,
	}


def action_targets_for_rows(
	doctype: str,
	rows: list[dict[str, Any]],
	action_key: str = "open_record",
	include_native_chrome: bool = False,
) -> dict[str, object]:
	targets: dict[str, object] = {}
	for row in rows:
		row_key = cstr(row.get("key") or row.get("name")).strip()
		name = cstr(row.get("name") or row_key).strip()
		if row_key and name:
			target: dict[str, object] = {"kind": "form", "doctype": doctype, "name": name}
			if include_native_chrome:
				target["native_chrome"] = native_form_context(doctype, name=name)
			targets[f"row:{row_key}:{action_key}"] = target
	return targets


def page_action_targets_for_rows(
	route: str,
	rows: list[dict[str, Any]],
	options_by_name: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
	targets: dict[str, object] = {}
	options_map = options_by_name or {}
	for row in rows:
		row_key = cstr(row.get("key") or row.get("name")).strip()
		name = cstr(row.get("name") or row_key).strip()
		if row_key and name:
			targets[f"row:{row_key}:open_record"] = {
				"kind": "page",
				"route": route,
				"route_parts": [name],
				"options": options_map.get(name) or {},
			}
	return targets
