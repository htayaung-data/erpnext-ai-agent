from __future__ import annotations

from frappe.utils import cstr

from . import common


SUPPLIER_FIELDS = ["name", "supplier_name", "supplier_group", "disabled", "modified"]


def supplier_filters(filters: dict[str, str] | None = None) -> list[list[object]]:
	applied = filters or {}
	conditions: list[list[object]] = []
	keyword = cstr(applied.get("keyword")).strip()
	if keyword:
		conditions.append(["Supplier", "supplier_name", "like", f"%{keyword}%"])
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
	rows: list[dict[str, object]] = []
	for record in records:
		name = cstr(record.get("name")).strip()
		if not name:
			continue
		disabled = bool(record.get("disabled"))
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
					"modified": cstr(record.get("modified") or ""),
				},
				"actions": [{"key": "open_record", "label": "Open"}],
			}
		)
	return rows


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
			"subtitle": "Supplier directory for buying coordination. Records open in ERPNext according to user permissions.",
			"chips": [{"label": "Supplier visibility"}],
		},
		"controls": {
			"fields": [
				{"key": "keyword", "label": "Search", "type": "text", "value": filters.get("keyword", ""), "placeholder": "Supplier name"},
				{"key": "supplier_group", "label": "Supplier Group", "type": "link", "linkDoctype": "Supplier Group", "value": filters.get("supplier_group", "")},
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
			"scopeChips": ["Supplier read access", "No create or edit action"],
		},
		"metrics": [common.metric("Visible suppliers", total, "Current filtered supplier records.")],
		"results": {
			"title": "Supplier records",
			"meta": f"{total} shown",
			"columns": [
				{"key": "supplier", "label": "Supplier"},
				{"key": "group", "label": "Group"},
				{"key": "status", "label": "Status"},
				{"key": "modified", "label": "Modified"},
			],
			"rows": rows,
			"rowActions": True,
			"state": state,
		},
		"action_targets": common.action_targets_for_rows("Supplier", rows),
	}
