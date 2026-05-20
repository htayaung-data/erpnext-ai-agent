from __future__ import annotations

from datetime import datetime

from frappe.utils import cstr

from . import common, supplier_readiness


SUPPLIER_FIELDS = ["name", "supplier_name", "supplier_group", "disabled", "modified"]
SUPPLIER_DETAIL_ROUTE = "procurement-console-supplier"


def supplier_filters(filters: dict[str, str] | None = None) -> list[list[object]]:
	applied = filters or {}
	conditions: list[list[object]] = []
	supplier = cstr(applied.get("supplier")).strip()
	if supplier:
		conditions.append(["Supplier", "name", "=", supplier])
	keyword = cstr(applied.get("keyword")).strip()
	if keyword:
		common.apply_keyword_name_filter(
			conditions,
			"Supplier",
			keyword,
			common.matching_parent_names_for_keyword("Supplier", keyword, ["name", "supplier_name", "supplier_group"]),
		)
	group = cstr(applied.get("supplier_group")).strip()
	if group:
		conditions.append(["Supplier", "supplier_group", "=", group])
	disabled = cstr(applied.get("disabled")).strip()
	if disabled:
		conditions.append(["Supplier", "disabled", "=", 1 if disabled == "1" else 0])
	return conditions


def count_visible_suppliers() -> int:
	if not common.can_read("Supplier"):
		return 0
	return common.count("Supplier", filters=[])


def build_supplier_directory(filters: dict[str, str] | None = None) -> dict[str, object]:
	applied = filters or {}
	if not common.can_read("Supplier"):
		return _supplier_payload(
			applied,
			rows=[],
			state=common.restricted_state("Supplier Directory restricted", "Supplier"),
			total=0,
		)

	rows = _supplier_rows(applied)
	state = common.ready_state() if rows else common.empty_state(
		"No suppliers found",
		"No visible suppliers match the current filters.",
	)
	return _supplier_payload(applied, rows=rows, state=state, total=len(rows))


def _supplier_rows(filters: dict[str, str]) -> list[dict[str, object]]:
	records = common.get_list(
		"Supplier",
		fields=SUPPLIER_FIELDS,
		filters=supplier_filters(filters),
		order_by="modified desc",
	)
	readiness_by_supplier = supplier_readiness.supplier_readiness_chips_for_suppliers([cstr(record.get("name")).strip() for record in records])
	rows: list[dict[str, object]] = []
	for record in records:
		name = cstr(record.get("name")).strip()
		if not name:
			continue
		disabled = bool(record.get("disabled"))
		readiness = readiness_by_supplier.get(name) or supplier_readiness.supplier_readiness_chip(name)
		rows.append(
			{
				"key": name,
				"name": name,
				"cells": {
					"supplier": {
						"value": record.get("supplier_name") or name,
						"meta": name,
					},
					"group": record.get("supplier_group") or "-",
					"status": {
						"value": "Disabled" if disabled else "Active",
						"tone": "danger" if disabled else "positive",
					},
					"readiness": {
						"value": readiness.get("value") or "New supplier - review needed",
						"tone": readiness.get("tone") or "neutral",
					},
					"modified": _format_supplier_modified(record.get("modified")),
				},
				"actions": [{"key": "open_record", "label": "Open"}],
			}
		)
	return rows


def _format_supplier_modified(value: object) -> str:
	if not value:
		return "-"
	if hasattr(value, "strftime"):
		return value.strftime("%d %b %Y")
	fallback = cstr(value).strip()
	for pattern in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
		try:
			return datetime.strptime(fallback, pattern).strftime("%d %b %Y")
		except Exception:
			continue
	return fallback.split(".", 1)[0] if fallback else "-"


def _supplier_payload(
	filters: dict[str, str],
	rows: list[dict[str, object]],
	state: dict[str, object],
	total: int,
) -> dict[str, object]:
	return {
		"page": {"title": "Suppliers", "key": "supplier_directory"},
		"summary": {
			"title": "Suppliers",
			"subtitle": "Supplier directory for buying coordination. Records open in a read-only Procurement view.",
			"chips": [{"label": "Supplier visibility"}],
		},
		"controls": {
			"fields": [
				{"key": "supplier", "label": "Supplier", "type": "link", "linkDoctype": "Supplier", "value": filters.get("supplier", ""), "placeholder": "Supplier"},
				{"key": "keyword", "label": "Search supplier or group", "type": "text", "value": filters.get("keyword", ""), "placeholder": "Search supplier or group"},
				{"key": "supplier_group", "label": "Group", "type": "link", "linkDoctype": "Supplier Group", "value": filters.get("supplier_group", ""), "placeholder": "Supplier group"},
				{
					"key": "disabled",
					"label": "Status",
					"type": "select",
					"value": filters.get("disabled", ""),
					"options": [
						{"label": "All", "value": ""},
						{"label": "Active", "value": "0"},
						{"label": "Disabled", "value": "1"},
					],
				},
			],
			"actions": common.standard_actions(),
			"scopeChips": ["Supplier read access", "Read-only supplier detail"],
		},
		"metrics": [common.metric("Suppliers in view", total, "Matching suppliers.")],
		"results": {
			"title": "Supplier records",
			"meta": f"{total} shown",
			"columns": [
				{"key": "supplier", "label": "Supplier"},
				{"key": "group", "label": "Group"},
				{"key": "status", "label": "Status"},
				{"key": "readiness", "label": "Readiness"},
				{"key": "modified", "label": "Modified"},
			],
			"rows": rows,
			"rowActions": True,
			"state": state,
		},
		"action_targets": common.page_action_targets_for_rows(SUPPLIER_DETAIL_ROUTE, rows),
	}
