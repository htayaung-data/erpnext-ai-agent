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
NATIVE_PO_ANALYSIS_REPORT = "Purchase Order Analysis"


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
	if normalized_key == "purchase_order_analysis":
		return _build_purchase_order_analysis(overrides)
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
			"open_purchase_order_analysis": {
				"kind": "report_page",
				"report_key": "purchase_order_analysis",
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
					"status": "ready",
					"status_label": "Ready",
					"boundary": "Buyer visibility only. Receiving and billing execution remain outside Procurement.",
					"icon": "order",
					"action_key": "open_purchase_order_analysis",
					"target_route": "/desk/procurement-console-report/purchase-order-analysis",
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


def _build_purchase_order_analysis(overrides: dict[str, object]) -> dict[str, object]:
	filters = _po_analysis_filters(overrides)
	if not common.can_read("Purchase Order"):
		return _po_analysis_payload(
			filters,
			rows=[],
			state=common.restricted_state("Purchase Order Analysis restricted", "Purchase Order"),
			metrics=[],
			action_targets={},
		)
	if not _native_report_available(NATIVE_PO_ANALYSIS_REPORT):
		return _po_analysis_payload(
			filters,
			rows=[],
			state=common.unavailable_state(
				"Purchase Order Analysis unavailable",
				"The installed ERPNext Purchase Order Analysis report is not available on this site.",
			),
			metrics=[],
			action_targets={},
		)
	try:
		payload = run_query_report(NATIVE_PO_ANALYSIS_REPORT, filters=_native_po_analysis_filters(filters), ignore_prepared_report=True)
		columns = _comparison_columns(payload.get("columns") or [])
		raw_rows = _normalize_rows(payload.get("result") or payload.get("data") or [], columns)
		filtered_rows = _filter_po_analysis_rows(raw_rows, filters)
		visible_rows, po_details = _permission_visible_po_analysis_rows(filtered_rows)
		rows, action_targets = _po_analysis_rows(visible_rows, po_details)
		state = common.ready_state() if rows else common.empty_state(
			"No purchase orders in view",
			"The selected filters did not return visible purchase orders for analysis.",
		)
		return _po_analysis_payload(filters, rows=rows, state=state, metrics=_po_analysis_metrics(visible_rows), action_targets=action_targets)
	except Exception as exc:  # pragma: no cover - exercised against live ERP runtime
		message = getattr(exc, "message", None) or str(exc) or "Unknown report error."
		if "not found" in message.lower() or "does not exist" in message.lower():
			state = common.unavailable_state("Purchase Order Analysis unavailable", message)
		else:
			state = common.state("error", "Purchase Order Analysis failed", message)
		return _po_analysis_payload(filters, rows=[], state=state, metrics=[], action_targets={})


def _po_analysis_payload(
	filters: dict[str, object],
	rows: list[dict[str, object]],
	state: dict[str, object],
	metrics: list[dict[str, object]],
	action_targets: dict[str, object],
) -> dict[str, object]:
	return {
		"page": {"title": "Purchase Order Analysis", "key": "purchase_order_analysis"},
		"summary": {
			"kicker": "Order review",
			"title": "Purchase Order Analysis",
			"subtitle": "Review ordered value, receipt posture, billing posture, suppliers, items, and status for buyer follow-up.",
		},
		"controls": _po_analysis_controls(filters),
		"metrics": {"appearance": "analytics_compact", "layout": "five_up", "items": metrics},
		"results": {
			"title": "Purchase order lines",
			"subtitle": "Read-only purchase order analysis with productized drilldowns for buyer review.",
			"meta": f"{len(rows)} shown",
			"columns": _po_analysis_display_columns(),
			"rows": rows[:ROW_LIMIT],
			"state": state,
			"tableMinWidth": 1720,
		},
		"action_targets": action_targets,
	}


def _po_analysis_filters(overrides: dict[str, object]) -> dict[str, object]:
	company = cstr(overrides.get("company")).strip() or _default_company()
	return {
		"company": company,
		"from_date": cstr(overrides.get("from_date")).strip() or common.date_days_ago(30),
		"to_date": cstr(overrides.get("to_date")).strip() or common.today_string(),
		"purchase_order": cstr(overrides.get("purchase_order") or overrides.get("name")).strip(),
		"supplier": cstr(overrides.get("supplier")).strip(),
		"item_code": cstr(overrides.get("item_code") or overrides.get("item")).strip(),
		"status": cstr(overrides.get("status")).strip(),
	}


def _native_po_analysis_filters(filters: dict[str, object]) -> dict[str, object]:
	payload: dict[str, object] = {
		"company": filters.get("company"),
		"from_date": filters.get("from_date"),
		"to_date": filters.get("to_date"),
		"group_by_po": 0,
	}
	if filters.get("purchase_order"):
		payload["name"] = [filters.get("purchase_order")]
	if filters.get("status"):
		payload["status"] = [filters.get("status")]
	return payload


def _po_analysis_controls(filters: dict[str, object]) -> dict[str, object]:
	status_options = ["", "To Pay", "To Bill", "To Receive", "To Receive and Bill", "Completed", "Closed"]
	return {
		"appearance": "analytics_compact",
		"submitLabel": "Apply",
		"resetLabel": "Reset",
		"meta": [
			{"label": "Mode", "value": "Read-only"},
			{"label": "Scope", "value": "Buyer order review"},
		],
		"fields": [
			{"key": "from_date", "label": "From", "type": "date", "value": filters.get("from_date"), "row": 1},
			{"key": "to_date", "label": "To", "type": "date", "value": filters.get("to_date"), "row": 1},
			{"key": "purchase_order", "label": "Purchase Order", "type": "link", "linkDoctype": "Purchase Order", "value": filters.get("purchase_order"), "placeholder": "Select purchase order", "row": 1},
			{
				"key": "status",
				"label": "Status",
				"type": "select",
				"value": filters.get("status"),
				"row": 1,
				"options": [{"label": option or "All", "value": option} for option in status_options],
			},
			{"key": "supplier", "label": "Supplier", "type": "link", "linkDoctype": "Supplier", "value": filters.get("supplier"), "placeholder": "Select supplier", "row": 2},
			{"key": "item_code", "label": "Item", "type": "link", "linkDoctype": "Item", "value": filters.get("item_code"), "placeholder": "Select item", "row": 2},
		],
		"actions": [
			{"key": "refresh", "label": "Refresh"},
		],
	}


def _po_analysis_display_columns() -> list[dict[str, object]]:
	return [
		{"key": "purchase_order", "label": "Purchase Order", "nowrap": True},
		{"key": "supplier", "label": "Supplier", "nowrap": True},
		{"key": "item_code", "label": "Item", "nowrap": True},
		{"key": "required_date", "label": "Required By", "nowrap": True},
		{"key": "status", "label": "Status / Workflow", "nowrap": True},
		{"key": "received_percent", "label": "Received %", "align": "right"},
		{"key": "billed_percent", "label": "Billed %", "align": "right"},
		{"key": "ordered_value", "label": "Ordered Value", "align": "right"},
		{"key": "open_receiving", "label": "Open Receiving", "align": "right"},
		{"key": "open_billing", "label": "Open Billing", "align": "right"},
	]


def _filter_po_analysis_rows(rows: list[dict[str, object]], filters: dict[str, object]) -> list[dict[str, object]]:
	filtered = list(rows)
	if filters.get("supplier"):
		filtered = [row for row in filtered if cstr(row.get("supplier")).strip() == filters.get("supplier")]
	if filters.get("item_code"):
		filtered = [row for row in filtered if cstr(row.get("item_code")).strip() == filters.get("item_code")]
	return filtered


def _po_visibility_fields() -> list[str]:
	fields = ["name", "status", "supplier", "supplier_name", "per_received", "per_billed", "grand_total", "currency"]
	if common.has_field("Purchase Order", "workflow_state"):
		fields.append("workflow_state")
	return list(dict.fromkeys(fields))


def _permission_visible_po_analysis_rows(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
	po_names = sorted({cstr(row.get("purchase_order")).strip() for row in rows if cstr(row.get("purchase_order")).strip()})
	if not po_names:
		return [], {}
	fields = _po_visibility_fields()
	visible = common.get_list(
		"Purchase Order",
		fields=fields,
		filters=[["Purchase Order", "name", "in", po_names]],
		limit=max(len(po_names), 1),
	)
	visible_map = {cstr(row.get("name")).strip(): row for row in visible if cstr(row.get("name")).strip()}
	return [row for row in rows if cstr(row.get("purchase_order")).strip() in visible_map], visible_map


def _po_analysis_rows(rows: list[dict[str, object]], po_details: dict[str, dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object]]:
	formatted_rows: list[dict[str, object]] = []
	action_targets: dict[str, object] = {}
	currency = _company_currency(cstr(rows[0].get("company")).strip() if rows else "")
	for index, row in enumerate(rows[:ROW_LIMIT]):
		po_name = cstr(row.get("purchase_order")).strip()
		details = po_details.get(po_name) or {}
		supplier = cstr(row.get("supplier") or details.get("supplier")).strip()
		item_code = cstr(row.get("item_code")).strip()
		qty = flt(row.get("qty"))
		received_qty = flt(row.get("received_qty"))
		billed_qty = flt(row.get("billed_qty"))
		pending_qty = flt(row.get("pending_qty"))
		qty_to_bill = flt(row.get("qty_to_bill"))
		status = cstr(row.get("status") or details.get("status")).strip()
		workflow_state = cstr(details.get("workflow_state")).strip()
		status_value = status if not workflow_state or workflow_state == status else f"{status} / {workflow_state}"
		po_action = f"po_analysis:po:{po_name}"
		supplier_action = f"po_analysis:supplier:{supplier}"
		item_action = f"po_analysis:item:{item_code}"
		if po_name:
			action_targets[po_action] = {"kind": "page", "route": "procurement-console-po-follow-up", "route_parts": [po_name]}
		if supplier:
			action_targets[supplier_action] = {"kind": "page", "route": "procurement-console-supplier", "route_parts": [supplier]}
		if item_code:
			action_targets[item_action] = {"kind": "page", "route": "procurement-console-item", "route_parts": [item_code]}
		formatted_rows.append(
			{
				"key": cstr(row.get("name") or f"{po_name}-{index}"),
				"cells": {
					"purchase_order": {"value": po_name, "actionKey": po_action} if po_name else {"value": "-"},
					"supplier": {"value": supplier or "-", "actionKey": supplier_action} if supplier else {"value": "-"},
					"item_code": {"value": item_code or "-", "actionKey": item_action} if item_code else {"value": "-"},
					"required_date": {"value": cstr(row.get("required_date") or row.get("date") or "-")},
					"status": {"value": status_value or "-"},
					"received_percent": {"value": _percent(received_qty, qty)},
					"billed_percent": {"value": _percent(billed_qty, qty)},
					"ordered_value": {"value": _money(row.get("amount"), currency)},
					"open_receiving": {"value": _quantity(pending_qty)},
					"open_billing": {"value": _quantity(qty_to_bill)},
				},
			}
		)
	return formatted_rows, action_targets


def _po_analysis_metrics(rows: list[dict[str, object]]) -> list[dict[str, object]]:
	po_names = {cstr(row.get("purchase_order")).strip() for row in rows if cstr(row.get("purchase_order")).strip()}
	currency = _company_currency(cstr(rows[0].get("company")).strip() if rows else "")
	ordered_value = sum(flt(row.get("amount")) for row in rows)
	open_receiving = sum(max(flt(row.get("pending_qty")), 0) for row in rows)
	open_billing = sum(max(flt(row.get("qty_to_bill")), 0) for row in rows)
	today = common.today_string()
	overdue_pos = {
		cstr(row.get("purchase_order")).strip()
		for row in rows
		if cstr(row.get("purchase_order")).strip()
		and flt(row.get("pending_qty")) > 0
		and cstr(row.get("required_date")).strip()
		and cstr(row.get("required_date")).strip() < today
	}
	return [
		common.metric("Visible orders", len(po_names), "Purchase orders matching the current report filters.", "slate"),
		common.metric("Ordered value", _money(ordered_value, currency), "Base ordered value in view.", "teal"),
		common.metric("Open receiving", _quantity(open_receiving), "Quantity still not received. Warehouse owns receipt execution.", "amber"),
		common.metric("Open billing", _quantity(open_billing), "Quantity not fully billed. Finance owns invoice and payment work.", "indigo"),
		common.metric("Overdue open", len(overdue_pos), "Open purchase orders past required date.", "red"),
	]


def _native_report_available(report_name: str) -> bool:
	try:
		return bool(frappe.db.exists("Report", report_name))
	except Exception:
		return True


def _company_currency(company: str) -> str:
	try:
		return cstr(frappe.db.get_value("Company", company, "default_currency")).strip()
	except Exception:
		return ""


def _percent(part: object, total: object) -> str:
	total_value = flt(total)
	if total_value <= 0:
		return "0%"
	value = max(0, min(100, (flt(part) / total_value) * 100))
	if float(value).is_integer():
		return f"{int(value)}%"
	return f"{value:.1f}%"


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
			"tableMinWidth": 1820,
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
		{"key": "valid_till", "label": "Valid Till", "nowrap": True},
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
