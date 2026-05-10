from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.desk.query_report import run as run_query_report
from frappe.utils import cstr, flt

from . import common, service


ROW_LIMIT = 80
REPORT_INDEX_KEY = "procurement_reports_index"
REPORT_INDEX_ALIASES = {"", "index", REPORT_INDEX_KEY}
NATIVE_COMPARISON_REPORT = "Supplier Quotation Comparison"


def _normalize_report_key(report_key: str | None) -> str:
	return str(report_key or "").strip().lower().replace("-", "_")


def _state_payload(report_key: str, state: dict[str, object]) -> dict[str, object]:
	title = state.get("title") or "Procurement report unavailable"
	return {
		"page": {"title": title, "key": report_key},
		"summary": {
			"kicker": "Procurement Console report",
			"title": title,
			"subtitle": state["detail"],
		},
		"controls": {
			"actions": [
				{"key": "refresh", "label": "Refresh"},
			],
			"fields": [],
		},
		"metrics": [],
		"results": {
			"title": "Report state",
			"columns": [],
			"rows": [],
			"state": state,
		},
		"action_targets": {},
	}


def _coerce_filter_overrides(filter_overrides: str | dict[str, object] | None) -> dict[str, object]:
	if isinstance(filter_overrides, dict):
		return dict(filter_overrides)
	if isinstance(filter_overrides, str) and filter_overrides.strip():
		try:
			parsed = json.loads(filter_overrides)
		except Exception:
			return {}
		return parsed if isinstance(parsed, dict) else {}
	return {}


@frappe.whitelist()
def get_procurement_console_report_context(
	report_key: str | None = None,
	filter_overrides: str | dict[str, object] | None = None,
) -> dict[str, object]:
	service.ensure_authenticated()
	context = service.build_context()
	normalized_key = _normalize_report_key(report_key)
	overrides = _coerce_filter_overrides(filter_overrides)
	if not service.has_procurement_access(context):
		return _state_payload(normalized_key, service.restricted_state())
	if normalized_key in REPORT_INDEX_ALIASES:
		return _build_report_index()
	if normalized_key == "supplier_quotation_comparison":
		return _build_supplier_quotation_comparison(overrides)
	return _state_payload(normalized_key, service.unavailable_state())


def _build_report_index() -> dict[str, object]:
	sections = _report_index_sections()
	cards = [card for section in sections for card in section.get("cards", [])]
	state = common.ready_state() if cards else common.empty_state(
		"No Procurement reports available",
		"No Procurement report surfaces are available for the current role.",
	)
	return {
		"page": {"title": "Procurement Reports", "key": REPORT_INDEX_KEY},
		"summary": {
			"kicker": "Buyer decision review",
			"title": "Procurement Reports",
			"subtitle": "Review sourcing, demand, orders, and item buying history from approved Procurement report surfaces.",
		},
		"controls": {
			"actions": [
				{"key": "refresh", "label": "Refresh"},
			],
			"fields": [],
		},
		"metrics": [],
		"catalog": {
			"title": "Report catalog",
			"subtitle": "Active reports open inside Procurement. Planned reports are listed for Phase 4A sequence only.",
			"sections": sections,
		},
		"results": {
			"title": "Report catalog state",
			"columns": [],
			"rows": [],
			"state": state,
		},
		"action_targets": {
			"open_supplier_quotation_comparison": {
				"kind": "report_page",
				"report_key": "supplier_quotation_comparison",
			},
		},
	}


def _report_index_sections() -> list[dict[str, object]]:
	return [
		{
			"key": "sourcing_review",
			"title": "Sourcing review",
			"subtitle": "Compare supplier offers and quotation posture before buying decisions.",
			"cards": [
				{
					"key": "supplier_quotation_comparison",
					"title": "Quote Comparison",
					"purpose": "Compare supplier offers by price, validity, item, supplier, and RFQ reference.",
					"status": "ready",
					"status_label": "Ready",
					"boundary": "Read-only sourcing comparison. Supplier selection and item price updates are not exposed here.",
					"icon": "report",
					"action_key": "open_supplier_quotation_comparison",
					"target_route": "/desk/procurement-console-report/supplier-quotation-comparison",
				},
			],
		},
		{
			"key": "order_review",
			"title": "Order review",
			"subtitle": "Understand ordered value and follow-up posture without changing Purchase Orders.",
			"cards": [
				{
					"key": "purchase_order_analysis",
					"title": "Purchase Order Analysis",
					"purpose": "Review ordered value, open receiving posture, billing posture, suppliers, items, and status.",
					"status": "planned",
					"status_label": "Planned",
					"boundary": "Buyer visibility only. Receiving and billing execution remain outside Procurement.",
					"icon": "order",
				},
			],
		},
		{
			"key": "demand_coverage",
			"title": "Demand coverage",
			"subtitle": "Review purchase demand coverage before building new order reports.",
			"cards": [
				{
					"key": "demand_to_order_coverage",
					"title": "Demand-to-Order Coverage",
					"purpose": "Show which purchase request lines are ordered, partially ordered, or still need sourcing action.",
					"status": "planned",
					"status_label": "Planned",
					"boundary": "Demand review only. It will not create Purchase Orders or receive stock.",
					"icon": "quotation",
				},
			],
		},
		{
			"key": "item_price_review",
			"title": "Item and price review",
			"subtitle": "Prepare read-only item buying history before any price governance work.",
			"cards": [
				{
					"key": "item_purchase_history",
					"title": "Item Purchase History",
					"purpose": "Review bought items, suppliers, historical buying rates, and order references.",
					"status": "planned",
					"status_label": "Planned",
					"boundary": "Read-only history. Item Price and default supplier changes stay disabled.",
					"icon": "item",
				},
			],
		},
	]


def _build_supplier_quotation_comparison(overrides: dict[str, object]) -> dict[str, object]:
	filters = _comparison_filters(overrides)
	if not common.can_read("Supplier Quotation"):
		return _comparison_payload(
			filters,
			rows=[],
			state=common.restricted_state("Supplier Quotation Comparison restricted", "Supplier Quotation"),
			metrics=[],
		)
	if not filters.get("company"):
		return _comparison_payload(
			filters,
			rows=[],
			state=common.unavailable_state(
				"Company is required",
				"Supplier quotation comparison needs the buying company context before it can run.",
			),
			metrics=[],
		)
	try:
		payload = run_query_report(NATIVE_COMPARISON_REPORT, filters=_native_comparison_filters(filters), ignore_prepared_report=True)
		columns = _comparison_columns(payload.get("columns") or [])
		raw_rows = _normalize_rows(payload.get("result") or payload.get("data") or [], columns)
		rows = _comparison_rows(raw_rows, columns)
		state = common.ready_state() if rows else common.empty_state(
			"No comparable quotations",
			"The selected filters did not return supplier quotations for comparison.",
		)
		return _comparison_payload(filters, rows=rows, state=state, metrics=_comparison_metrics(raw_rows))
	except Exception as exc:  # pragma: no cover - exercised against live ERP runtime
		message = getattr(exc, "message", None) or str(exc) or "Unknown report error."
		return _comparison_payload(
			filters,
			rows=[],
			state=common.state("error", "Supplier quotation comparison failed", message),
			metrics=[],
		)


def _comparison_payload(
	filters: dict[str, object],
	rows: list[dict[str, object]],
	state: dict[str, object],
	metrics: list[dict[str, object]],
) -> dict[str, object]:
	return {
		"page": {"title": "Supplier Quotation Comparison", "key": "supplier_quotation_comparison"},
		"summary": {
			"kicker": "Sourcing review",
			"title": "Quote Comparison",
			"subtitle": "Compare supplier offers by price, validity, item, supplier, and RFQ reference. Read-only view for buyer review.",
		},
		"controls": _comparison_controls(filters),
		"metrics": metrics,
		"results": {
			"title": "Supplier offers",
			"subtitle": "Quoted prices, validity, lead time, supplier, item, and RFQ reference for buyer comparison.",
			"meta": f"{len(rows)} shown",
			"columns": _comparison_display_columns(),
			"rows": rows[:ROW_LIMIT],
			"state": state,
			"tableMinWidth": 1040,
		},
		"action_targets": {},
	}


def _comparison_filters(overrides: dict[str, object]) -> dict[str, object]:
	company = cstr(overrides.get("company")).strip() or _default_company()
	from_date = cstr(overrides.get("from_date")).strip() or common.date_days_ago(30)
	to_date = cstr(overrides.get("to_date")).strip() or common.today_string()
	return {
		"company": company,
		"from_date": from_date,
		"to_date": to_date,
		"item_code": cstr(overrides.get("item_code")).strip(),
		"supplier": cstr(overrides.get("supplier")).strip(),
		"supplier_quotation": cstr(overrides.get("supplier_quotation")).strip(),
		"request_for_quotation": cstr(overrides.get("request_for_quotation")).strip(),
		"categorize_by": cstr(overrides.get("categorize_by")).strip() or "Categorize by Supplier",
		"include_expired": _truthy(overrides.get("include_expired")),
	}


def _native_comparison_filters(filters: dict[str, object]) -> dict[str, object]:
	payload: dict[str, object] = {
		"company": filters.get("company"),
		"from_date": filters.get("from_date"),
		"to_date": filters.get("to_date"),
		"categorize_by": filters.get("categorize_by") or "Categorize by Supplier",
		"include_expired": 1 if filters.get("include_expired") else 0,
	}
	for key in ["item_code", "request_for_quotation"]:
		if filters.get(key):
			payload[key] = filters.get(key)
	if filters.get("supplier"):
		payload["supplier"] = [filters.get("supplier")]
	if filters.get("supplier_quotation"):
		payload["supplier_quotation"] = [filters.get("supplier_quotation")]
	return payload


def _comparison_controls(filters: dict[str, object]) -> dict[str, object]:
	return {
		"appearance": "analytics_compact",
		"actionLayout": "separate_row",
		"submitLabel": "Apply",
		"resetLabel": "Reset",
		"meta": [
			{"label": "Mode", "value": "Read-only"},
			{"label": "Scope", "value": "Buyer comparison"},
		],
		"fields": [
			{"key": "from_date", "label": "From", "type": "date", "value": filters.get("from_date"), "row": 1},
			{"key": "to_date", "label": "To", "type": "date", "value": filters.get("to_date"), "row": 1},
			{
				"key": "categorize_by",
				"label": "Categorize",
				"type": "select",
				"value": filters.get("categorize_by"),
				"row": 1,
				"options": [
					{"label": "By Supplier", "value": "Categorize by Supplier"},
					{"label": "By Item", "value": "Categorize by Item"},
				],
			},
			{
				"key": "include_expired",
				"label": "Expired",
				"type": "select",
				"value": "1" if filters.get("include_expired") else "0",
				"row": 1,
				"options": [
					{"label": "Exclude expired", "value": "0"},
					{"label": "Include expired", "value": "1"},
				],
			},
			{"key": "item_code", "label": "Item", "type": "link", "linkDoctype": "Item", "value": filters.get("item_code"), "placeholder": "Select item", "row": 2},
			{"key": "supplier", "label": "Supplier", "type": "link", "linkDoctype": "Supplier", "value": filters.get("supplier"), "placeholder": "Select supplier", "row": 2},
			{"key": "supplier_quotation", "label": "Quotation", "type": "link", "linkDoctype": "Supplier Quotation", "value": filters.get("supplier_quotation"), "placeholder": "Select supplier quotation", "row": 2},
			{"key": "request_for_quotation", "label": "RFQ", "type": "link", "linkDoctype": "Request for Quotation", "value": filters.get("request_for_quotation"), "placeholder": "Select RFQ", "row": 2},
		],
		"actions": [
			{"key": "refresh", "label": "Refresh"},
		],
	}


def _comparison_display_columns() -> list[dict[str, object]]:
	return [
		{"key": "supplier_name", "label": "Supplier", "nowrap": True},
		{"key": "item_code", "label": "Item", "nowrap": True},
		{"key": "qty", "label": "Qty", "align": "right"},
		{"key": "uom", "label": "UOM"},
		{"key": "price", "label": "Price", "align": "right"},
		{"key": "price_per_unit", "label": "Unit Price", "align": "right"},
		{"key": "quotation", "label": "Quotation", "nowrap": True},
		{"key": "valid_till", "label": "Valid Till"},
		{"key": "lead_time_days", "label": "Lead Time", "align": "right"},
		{"key": "request_for_quotation", "label": "RFQ", "nowrap": True},
	]


def _comparison_columns(raw_columns: list[object]) -> list[dict[str, object]]:
	columns: list[dict[str, object]] = []
	for index, column in enumerate(raw_columns):
		if isinstance(column, dict):
			fieldname = column.get("fieldname") or column.get("key") or f"column_{index}"
			label = column.get("label") or fieldname
		else:
			parts = cstr(column).split(":")
			label = parts[0] if parts else f"Column {index + 1}"
			fieldname = label.strip().lower().replace(" ", "_")
		columns.append({"key": cstr(fieldname), "label": cstr(label)})
	return columns


def _normalize_rows(raw_rows: list[object], columns: list[dict[str, object]]) -> list[dict[str, object]]:
	rows: list[dict[str, object]] = []
	for raw in raw_rows:
		if isinstance(raw, dict):
			rows.append(dict(raw))
		elif isinstance(raw, (list, tuple)):
			rows.append({columns[index]["key"]: raw[index] for index in range(min(len(columns), len(raw)))})
	return rows


def _comparison_rows(raw_rows: list[dict[str, object]], columns: list[dict[str, object]]) -> list[dict[str, object]]:
	allowed = {column["key"] for column in _comparison_display_columns()}
	rows: list[dict[str, object]] = []
	for index, raw in enumerate(raw_rows):
		cells: dict[str, object] = {}
		for key in allowed:
			value = raw.get(key)
			if key in {"price", "price_per_unit"}:
				value = _money(value, raw.get("currency"))
			elif key == "qty":
				value = _quantity(value)
			elif key == "lead_time_days" and value not in (None, ""):
				value = cstr(value)
			else:
				value = cstr(value) if value not in (None, "") else "-"
			cells[key] = {"value": value}
		rows.append({"key": cstr(raw.get("quotation") or index), "cells": cells})
	return rows


def _comparison_metrics(raw_rows: list[dict[str, object]]) -> list[dict[str, object]]:
	quotations = {cstr(row.get("quotation")).strip() for row in raw_rows if cstr(row.get("quotation")).strip()}
	suppliers = {cstr(row.get("supplier_name")).strip() for row in raw_rows if cstr(row.get("supplier_name")).strip()}
	items = {cstr(row.get("item_code")).strip() for row in raw_rows if cstr(row.get("item_code")).strip()}
	expiring = len([row for row in raw_rows if cstr(row.get("valid_till")).strip()])
	return [
		common.metric("Quotations", len(quotations), "Unique submitted quotations in this comparison.", "teal"),
		common.metric("Suppliers", len(suppliers), "Suppliers represented in visible rows.", "slate"),
		common.metric("Items", len(items), "Items represented in visible rows.", "amber"),
		common.metric("Validity rows", expiring, "Rows with quoted validity dates.", "indigo"),
	]


def _default_company() -> str:
	try:
		return cstr(frappe.defaults.get_user_default("Company")).strip()
	except Exception:
		pass
	try:
		return cstr(frappe.defaults.get_default("company")).strip()
	except Exception:
		pass
	try:
		return cstr(frappe.db.get_single_value("Global Defaults", "default_company")).strip()
	except Exception:
		return ""


def _truthy(value: object) -> bool:
	return cstr(value).strip().lower() in {"1", "true", "yes", "on"}


def _quantity(value: object) -> str:
	number = flt(value)
	if number.is_integer():
		return str(int(number))
	return f"{number:,.2f}"


def _money(value: object, currency: object) -> str:
	amount = flt(value)
	code = cstr(currency).strip()
	if code:
		return f"{code} {amount:,.2f}"
	return f"{amount:,.2f}"
