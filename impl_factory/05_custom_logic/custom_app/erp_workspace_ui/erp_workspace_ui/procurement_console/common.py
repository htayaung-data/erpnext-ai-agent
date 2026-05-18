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


def _get_all_unchecked(
	doctype: str,
	fields: list[str],
	filters: list | dict | None = None,
	order_by: str | None = None,
	limit: int = ROW_LIMIT,
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


def _append_unique(target: list[str], seen: set[str], value: object) -> None:
	name = cstr(value).strip()
	if name and name not in seen:
		seen.add(name)
		target.append(name)


def matching_parent_names_for_keyword(
	parent_doctype: str,
	keyword: str,
	parent_fields: list[str],
	child_specs: list[dict[str, object]] | None = None,
	limit: int | None = None,
) -> list[str]:
	term = cstr(keyword).strip()
	if not term:
		return []
	row_limit = limit or ROW_LIMIT * 4
	like_value = f"%{term}%"
	names: list[str] = []
	seen: set[str] = set()
	for fieldname in parent_fields:
		field = cstr(fieldname).strip()
		if not field or (field != "name" and not has_field(parent_doctype, field)):
			continue
		rows = get_list(parent_doctype, fields=["name"], filters=[[parent_doctype, field, "like", like_value]], limit=row_limit)
		for row in rows:
			_append_unique(names, seen, row.get("name"))
	for spec in child_specs or []:
		child_doctype = cstr(spec.get("doctype")).strip()
		parent_field = cstr(spec.get("parent_field") or "parent").strip()
		child_fields = [cstr(field).strip() for field in spec.get("fields") or [] if cstr(field).strip()]
		if not child_doctype or not parent_field:
			continue
		for field in child_fields:
			if field != "name" and not has_field(child_doctype, field):
				continue
			rows = _get_all_unchecked(child_doctype, fields=[parent_field], filters=[[child_doctype, field, "like", like_value]], limit=row_limit)
			for row in rows:
				_append_unique(names, seen, row.get(parent_field))
	return names


def apply_keyword_name_filter(conditions: list[list[object]], doctype: str, keyword: str, names: list[str]) -> None:
	if not cstr(keyword).strip():
		return
	if names:
		conditions.append([doctype, "name", "in", names])
	else:
		conditions.append([doctype, "name", "=", "__erpw_no_keyword_match__"])


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
