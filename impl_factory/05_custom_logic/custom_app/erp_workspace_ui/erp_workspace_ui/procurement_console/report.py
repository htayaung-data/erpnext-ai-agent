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
	if normalized_key == "demand_to_order_coverage":
		return _build_demand_to_order_coverage(overrides)
	if normalized_key == "item_purchase_history":
		return _build_item_purchase_history(overrides)
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
			"open_demand_to_order_coverage": {
				"kind": "report_page",
				"report_key": "demand_to_order_coverage",
			},
			"open_item_purchase_history": {
				"kind": "report_page",
				"report_key": "item_purchase_history",
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
					"purpose": "Compare supplier offers by price, validity, supplier, item, and RFQ.",
					"status": "ready",
					"status_label": "Ready",
					"boundary": "Read-only sourcing review.",
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
					"purpose": "Review ordered value, receiving posture, billing posture, suppliers, and items.",
					"status": "ready",
					"status_label": "Ready",
					"boundary": "Read-only buyer visibility.",
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
					"purpose": "Track purchase demand that is ordered, partial, or still open.",
					"status": "ready",
					"status_label": "Ready",
					"boundary": "Read-only demand coverage.",
					"icon": "quotation",
					"action_key": "open_demand_to_order_coverage",
					"target_route": "/desk/procurement-console-report/demand-to-order-coverage",
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
					"purpose": "Review buying history by item, supplier, and order reference.",
					"status": "ready",
					"status_label": "Ready",
					"boundary": "Read-only price review.",
					"icon": "item",
					"action_key": "open_item_purchase_history",
					"target_route": "/desk/procurement-console-report/item-purchase-history",
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


DEMAND_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
	"Material Request": ("material_request_type", "transaction_date", "schedule_date", "status"),
	"Material Request Item": ("item_code", "qty", "ordered_qty", "schedule_date"),
	"Purchase Order Item": ("material_request", "material_request_item", "item_code", "qty"),
}


def _build_demand_to_order_coverage(overrides: dict[str, object]) -> dict[str, object]:
	filters = _demand_coverage_filters(overrides)
	if not common.can_read("Material Request"):
		return _demand_coverage_payload(
			filters,
			rows=[],
			state=common.restricted_state("Demand-to-Order Coverage restricted", "Material Request"),
			metrics=[],
			action_targets={},
		)
	missing_fields = _missing_demand_coverage_fields()
	if missing_fields:
		return _demand_coverage_payload(
			filters,
			rows=[],
			state=common.unavailable_state(
				"Demand-to-Order Coverage unavailable",
				"Required purchase demand linkage fields are not available: " + ", ".join(missing_fields),
			),
			metrics=[],
			action_targets={},
		)
	try:
		material_requests = _visible_purchase_material_requests(filters)
		request_names = [cstr(row.get("name")).strip() for row in material_requests if cstr(row.get("name")).strip()]
		items = _material_request_items_for(request_names)
		linked_pos = _visible_linked_purchase_orders_by_material_request(request_names, [cstr(row.get("name")).strip() for row in items if cstr(row.get("name")).strip()])
		coverage_rows = _demand_coverage_source_rows(material_requests, items, linked_pos, filters)
		filtered_rows = _filter_demand_coverage_rows(coverage_rows, filters)
		rows, action_targets = _demand_coverage_rows(filtered_rows)
		state = common.ready_state() if rows else common.empty_state(
			"No demand coverage lines",
			"The selected filters did not return visible purchase demand coverage lines.",
		)
		return _demand_coverage_payload(filters, rows=rows, state=state, metrics=_demand_coverage_metrics(filtered_rows), action_targets=action_targets)
	except Exception as exc:  # pragma: no cover - exercised against live ERP runtime
		message = getattr(exc, "message", None) or str(exc) or "Unknown report error."
		return _demand_coverage_payload(filters, rows=[], state=common.state("error", "Demand-to-Order Coverage failed", message), metrics=[], action_targets={})


def _demand_coverage_payload(
	filters: dict[str, object],
	rows: list[dict[str, object]],
	state: dict[str, object],
	metrics: list[dict[str, object]],
	action_targets: dict[str, object],
) -> dict[str, object]:
	return {
		"page": {"title": "Demand-to-Order Coverage", "key": "demand_to_order_coverage"},
		"summary": {
			"kicker": "Demand coverage",
			"title": "Demand-to-Order Coverage",
			"subtitle": "Track purchase demand that is ordered, partial, or still open for buyer action.",
		},
		"controls": _demand_coverage_controls(filters),
		"metrics": {"appearance": "analytics_compact", "layout": "five_up", "items": metrics},
		"results": {
			"title": "Demand coverage lines",
			"subtitle": "Purchase request lines compared with linked purchase order coverage.",
			"meta": f"{len(rows)} shown",
			"columns": _demand_coverage_display_columns(),
			"rows": rows[:ROW_LIMIT],
			"state": state,
			"tableMinWidth": 1480,
		},
		"action_targets": action_targets,
	}


def _missing_demand_coverage_fields() -> list[str]:
	missing: list[str] = []
	for doctype, fields in DEMAND_REQUIRED_FIELDS.items():
		for field in fields:
			if not common.has_field(doctype, field):
				missing.append(f"{doctype}.{field}")
	return missing


def _demand_coverage_filters(overrides: dict[str, object]) -> dict[str, object]:
	return {
		"from_date": cstr(overrides.get("from_date")).strip() or common.date_days_ago(90),
		"to_date": cstr(overrides.get("to_date")).strip() or common.today_string(),
		"material_request": cstr(overrides.get("material_request") or overrides.get("purchase_request")).strip(),
		"item_code": cstr(overrides.get("item_code") or overrides.get("item")).strip(),
		"coverage_status": cstr(overrides.get("coverage_status")).strip(),
		"warehouse": cstr(overrides.get("warehouse")).strip(),
	}


def _demand_coverage_controls(filters: dict[str, object]) -> dict[str, object]:
	status_options = [
		("", "All"),
		("open_demand", "Open Demand"),
		("partially_ordered", "Partially Ordered"),
		("fully_ordered", "Fully Ordered"),
		("stopped_closed", "Stopped / Closed"),
		("cancelled", "Cancelled"),
	]
	return {
		"appearance": "analytics_compact",
		"submitLabel": "Apply",
		"resetLabel": "Reset",
		"meta": [
			{"label": "Mode", "value": "Read-only"},
			{"label": "Scope", "value": "Buyer demand review"},
		],
		"fields": [
			{"key": "from_date", "label": "From", "type": "date", "value": filters.get("from_date"), "row": 1},
			{"key": "to_date", "label": "To", "type": "date", "value": filters.get("to_date"), "row": 1},
			{"key": "material_request", "label": "Purchase Request", "type": "link", "linkDoctype": "Material Request", "value": filters.get("material_request"), "placeholder": "Select purchase request", "row": 1},
			{"key": "coverage_status", "label": "Coverage Status", "type": "select", "value": filters.get("coverage_status"), "row": 1, "options": [{"label": label, "value": value} for value, label in status_options]},
			{"key": "item_code", "label": "Item", "type": "link", "linkDoctype": "Item", "value": filters.get("item_code"), "placeholder": "Select item", "row": 2},
			{"key": "warehouse", "label": "Warehouse", "type": "link", "linkDoctype": "Warehouse", "value": filters.get("warehouse"), "placeholder": "Select warehouse", "row": 2},
		],
		"actions": [
			{"key": "refresh", "label": "Refresh"},
		],
	}


def _demand_coverage_display_columns() -> list[dict[str, object]]:
	return [
		{"key": "material_request", "label": "Purchase Request", "nowrap": True},
		{"key": "required_date", "label": "Required By", "nowrap": True},
		{"key": "item_code", "label": "Item", "nowrap": True},
		{"key": "requested_qty", "label": "Requested Qty", "align": "right"},
		{"key": "ordered_qty", "label": "Ordered Qty", "align": "right"},
		{"key": "open_qty", "label": "Open Qty", "align": "right"},
		{"key": "coverage_status", "label": "Coverage Status", "nowrap": True},
		{"key": "linked_purchase_order", "label": "Linked PO", "nowrap": True},
	]


def _visible_purchase_material_requests(filters: dict[str, object]) -> list[dict[str, object]]:
	query_filters: list[list[object]] = [["Material Request", "material_request_type", "=", "Purchase"]]
	if filters.get("from_date"):
		query_filters.append(["Material Request", "transaction_date", ">=", filters.get("from_date")])
	if filters.get("to_date"):
		query_filters.append(["Material Request", "transaction_date", "<=", filters.get("to_date")])
	if filters.get("material_request"):
		query_filters.append(["Material Request", "name", "=", filters.get("material_request")])
	fields = ["name", "title", "transaction_date", "schedule_date", "status", "docstatus", "per_ordered"]
	return common.get_list("Material Request", fields=fields, filters=query_filters, order_by="transaction_date desc, name desc", limit=ROW_LIMIT)


def _available_child_fields(doctype: str, fields: list[str]) -> list[str]:
	return [field for field in fields if field in {"name", "parent", "idx"} or common.has_field(doctype, field)]


def _material_request_items_for(request_names: list[str]) -> list[dict[str, object]]:
	if not request_names:
		return []
	try:
		return list(
			frappe.get_all(
				"Material Request Item",
				filters={"parent": ["in", request_names]},
				fields=_available_child_fields("Material Request Item", ["name", "parent", "idx", "item_code", "item_name", "qty", "ordered_qty", "uom", "schedule_date", "warehouse"]),
				order_by="parent desc, idx asc",
				limit_page_length=ROW_LIMIT,
			)
		)
	except Exception:
		return []


def _visible_linked_purchase_orders_by_material_request(request_names: list[str], item_row_names: list[str]) -> dict[str, list[dict[str, object]]]:
	if not request_names or not common.can_read("Purchase Order"):
		return {}
	try:
		po_items = list(
			frappe.get_all(
				"Purchase Order Item",
				filters={"material_request": ["in", request_names]},
				fields=_available_child_fields("Purchase Order Item", ["name", "parent", "item_code", "qty", "material_request", "material_request_item"]),
				order_by="parent desc, idx asc",
				limit_page_length=ROW_LIMIT * 4,
			)
		)
	except Exception:
		po_items = []
	if item_row_names:
		try:
			linked_by_item = list(
				frappe.get_all(
					"Purchase Order Item",
					filters={"material_request_item": ["in", item_row_names]},
					fields=_available_child_fields("Purchase Order Item", ["name", "parent", "item_code", "qty", "material_request", "material_request_item"]),
					order_by="parent desc, idx asc",
					limit_page_length=ROW_LIMIT * 4,
				)
			)
		except Exception:
			linked_by_item = []
		seen = {cstr(row.get("name")).strip() for row in po_items if cstr(row.get("name")).strip()}
		for row in linked_by_item:
			name = cstr(row.get("name")).strip()
			if name and name not in seen:
				po_items.append(row)
				seen.add(name)
	po_names = sorted({cstr(row.get("parent")).strip() for row in po_items if cstr(row.get("parent")).strip()})
	if not po_names:
		return {}
	visible_pos = common.get_list("Purchase Order", fields=["name", "status"], filters=[["Purchase Order", "name", "in", po_names]], limit=max(len(po_names), 1))
	visible_po_names = {cstr(row.get("name")).strip() for row in visible_pos if cstr(row.get("name")).strip()}
	links: dict[str, list[dict[str, object]]] = {}
	for row in po_items:
		po_name = cstr(row.get("parent")).strip()
		if not po_name or po_name not in visible_po_names:
			continue
		item_key = cstr(row.get("material_request_item")).strip()
		request_key = cstr(row.get("material_request")).strip()
		payload = {"purchase_order": po_name, "qty": flt(row.get("qty")), "item_code": cstr(row.get("item_code")).strip()}
		if item_key:
			links.setdefault(item_key, []).append(payload)
		if request_key:
			links.setdefault(request_key, []).append(payload)
	return links


def _demand_coverage_source_rows(
	material_requests: list[dict[str, object]],
	items: list[dict[str, object]],
	linked_pos: dict[str, list[dict[str, object]]],
	filters: dict[str, object],
) -> list[dict[str, object]]:
	request_by_name = {cstr(row.get("name")).strip(): row for row in material_requests if cstr(row.get("name")).strip()}
	rows: list[dict[str, object]] = []
	for item in items:
		request_name = cstr(item.get("parent")).strip()
		request = request_by_name.get(request_name)
		if not request:
			continue
		item_code = cstr(item.get("item_code")).strip()
		if filters.get("item_code") and item_code != filters.get("item_code"):
			continue
		warehouse = cstr(item.get("warehouse")).strip()
		if filters.get("warehouse") and warehouse != filters.get("warehouse"):
			continue
		requested_qty = flt(item.get("qty"))
		ordered_qty = max(flt(item.get("ordered_qty")), 0)
		open_qty = max(requested_qty - ordered_qty, 0)
		status_key, status_label = _demand_coverage_status(request, requested_qty, ordered_qty)
		item_row_name = cstr(item.get("name")).strip()
		po_links = linked_pos.get(item_row_name) or linked_pos.get(request_name) or []
		unique_pos = []
		seen_pos = set()
		for link in po_links:
			po_name = cstr(link.get("purchase_order")).strip()
			if po_name and po_name not in seen_pos:
				unique_pos.append(link)
				seen_pos.add(po_name)
		rows.append(
			{
				"key": item_row_name or f"{request_name}:{item_code}",
				"material_request": request_name,
				"request_date": cstr(request.get("transaction_date")).strip(),
				"required_date": cstr(item.get("schedule_date") or request.get("schedule_date")).strip(),
				"item_code": item_code,
				"item_name": cstr(item.get("item_name")).strip(),
				"requested_qty": requested_qty,
				"ordered_qty": ordered_qty,
				"open_qty": open_qty,
				"coverage_status_key": status_key,
				"coverage_status": status_label,
				"warehouse": warehouse,
				"linked_purchase_orders": unique_pos,
			}
		)
	return rows


def _demand_coverage_status(request: dict[str, object], requested_qty: float, ordered_qty: float) -> tuple[str, str]:
	status = cstr(request.get("status")).strip().lower()
	docstatus = cstr(request.get("docstatus")).strip()
	if status == "cancelled" or docstatus == "2":
		return "cancelled", "Cancelled"
	if status in {"stopped", "closed"}:
		return "stopped_closed", "Stopped / Closed"
	if requested_qty > 0 and ordered_qty >= requested_qty:
		return "fully_ordered", "Fully Ordered"
	if ordered_qty > 0:
		return "partially_ordered", "Partially Ordered"
	return "open_demand", "Open Demand"


def _filter_demand_coverage_rows(rows: list[dict[str, object]], filters: dict[str, object]) -> list[dict[str, object]]:
	coverage_status = cstr(filters.get("coverage_status")).strip()
	if coverage_status:
		rows = [row for row in rows if row.get("coverage_status_key") == coverage_status]
	return rows


def _demand_coverage_rows(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object]]:
	formatted_rows: list[dict[str, object]] = []
	action_targets: dict[str, object] = {}
	for row in rows[:ROW_LIMIT]:
		request_name = cstr(row.get("material_request")).strip()
		item_code = cstr(row.get("item_code")).strip()
		po_links = row.get("linked_purchase_orders") if isinstance(row.get("linked_purchase_orders"), list) else []
		first_po = cstr(po_links[0].get("purchase_order")).strip() if po_links else ""
		request_action = f"demand_coverage:request:{request_name}"
		item_action = f"demand_coverage:item:{item_code}"
		po_action = f"demand_coverage:po:{first_po}"
		if request_name:
			action_targets[request_action] = {"kind": "page", "route": "procurement-console-purchase-request-review", "route_parts": [request_name]}
		if item_code:
			action_targets[item_action] = {"kind": "page", "route": "procurement-console-item", "route_parts": [item_code]}
		if first_po:
			action_targets[po_action] = {"kind": "page", "route": "procurement-console-po-follow-up", "route_parts": [first_po]}
		linked_po_value = "-"
		linked_po_cell: dict[str, object] = {"value": linked_po_value}
		if first_po:
			linked_po_value = first_po if len(po_links) == 1 else f"{first_po} + {len(po_links) - 1} more"
			linked_po_cell = {"value": linked_po_value, "actionKey": po_action}
		formatted_rows.append(
			{
				"key": cstr(row.get("key") or f"{request_name}:{item_code}"),
				"cells": {
					"material_request": {"value": request_name or "-", "actionKey": request_action} if request_name else {"value": "-"},
					"required_date": {"value": cstr(row.get("required_date") or "-")},
					"item_code": {"value": item_code or "-", "detail": cstr(row.get("item_name")).strip(), "actionKey": item_action} if item_code else {"value": "-"},
					"requested_qty": {"value": _quantity(row.get("requested_qty"))},
					"ordered_qty": {"value": _quantity(row.get("ordered_qty"))},
					"open_qty": {"value": _quantity(row.get("open_qty"))},
					"coverage_status": {"value": cstr(row.get("coverage_status") or "-")},
					"linked_purchase_order": linked_po_cell,
				},
			}
		)
	return formatted_rows, action_targets


def _demand_coverage_metrics(rows: list[dict[str, object]]) -> list[dict[str, object]]:
	open_rows = [row for row in rows if row.get("coverage_status_key") in {"open_demand", "partially_ordered"}]
	partial_rows = [row for row in rows if row.get("coverage_status_key") == "partially_ordered"]
	fully_rows = [row for row in rows if row.get("coverage_status_key") == "fully_ordered"]
	today = common.today_string()
	overdue_open = [row for row in open_rows if cstr(row.get("required_date")).strip() and cstr(row.get("required_date")).strip() < today and flt(row.get("open_qty")) > 0]
	return [
		common.metric("Demand lines", len(rows), "Visible purchase request lines in this report.", "slate"),
		common.metric("Open demand", _quantity(sum(max(flt(row.get("open_qty")), 0) for row in open_rows)), "Quantity not yet covered by purchase orders.", "amber"),
		common.metric("Partially ordered", len(partial_rows), "Demand lines with ordering progress and remaining open quantity.", "indigo"),
		common.metric("Fully ordered", len(fully_rows), "Demand lines fully covered by purchase orders.", "teal"),
		common.metric("Overdue open", len(overdue_open), "Open demand lines past required date.", "red"),
	]


ITEM_HISTORY_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
	"Purchase Order": ("transaction_date", "supplier", "supplier_name", "currency", "status"),
	"Purchase Order Item": ("item_code", "item_name", "qty", "uom", "rate", "amount", "base_rate", "base_amount"),
}


def _build_item_purchase_history(overrides: dict[str, object]) -> dict[str, object]:
	filters = _item_history_filters(overrides)
	if not common.can_read("Purchase Order"):
		return _item_history_payload(
			filters,
			rows=[],
			state=common.restricted_state("Item Purchase History restricted", "Purchase Order"),
			metrics=[],
			action_targets={},
		)
	missing_fields = _missing_item_history_fields()
	if missing_fields:
		return _item_history_payload(
			filters,
			rows=[],
			state=common.unavailable_state(
				"Item Purchase History unavailable",
				"Required item buying history fields are not available: " + ", ".join(missing_fields),
			),
			metrics=[],
			action_targets={},
		)
	try:
		purchase_orders = _visible_item_history_purchase_orders(filters)
		po_names = [cstr(row.get("name")).strip() for row in purchase_orders if cstr(row.get("name")).strip()]
		items = _purchase_order_items_for_history(po_names, filters)
		source_rows = _item_history_source_rows(purchase_orders, items)
		rows, action_targets = _item_history_rows(source_rows)
		state = common.ready_state() if rows else common.empty_state(
			"No item purchase history",
			"The selected filters did not return visible item buying history lines.",
		)
		return _item_history_payload(filters, rows=rows, state=state, metrics=_item_history_metrics(source_rows), action_targets=action_targets)
	except Exception as exc:  # pragma: no cover - exercised against live ERP runtime
		message = getattr(exc, "message", None) or str(exc) or "Unknown report error."
		return _item_history_payload(filters, rows=[], state=common.state("error", "Item Purchase History failed", message), metrics=[], action_targets={})


def _item_history_payload(
	filters: dict[str, object],
	rows: list[dict[str, object]],
	state: dict[str, object],
	metrics: list[dict[str, object]],
	action_targets: dict[str, object],
) -> dict[str, object]:
	return {
		"page": {"title": "Item Purchase History", "key": "item_purchase_history"},
		"summary": {
			"kicker": "Item and price review",
			"title": "Item Purchase History",
			"subtitle": "Review item buying history, suppliers, rates, and purchase order references.",
		},
		"controls": _item_history_controls(filters),
		"metrics": {"appearance": "analytics_compact", "layout": "five_up", "items": metrics},
		"results": {
			"title": "Item buying history",
			"subtitle": "Purchase order lines summarized for buyer price review.",
			"meta": f"{len(rows)} shown",
			"columns": _item_history_display_columns(),
			"rows": rows[:ROW_LIMIT],
			"state": state,
			"tableMinWidth": 1580,
		},
		"action_targets": action_targets,
	}


def _missing_item_history_fields() -> list[str]:
	missing: list[str] = []
	for doctype, fields in ITEM_HISTORY_REQUIRED_FIELDS.items():
		for field in fields:
			if not common.has_field(doctype, field):
				missing.append(f"{doctype}.{field}")
	return missing


def _item_history_filters(overrides: dict[str, object]) -> dict[str, object]:
	return {
		"from_date": cstr(overrides.get("from_date")).strip() or common.date_days_ago(90),
		"to_date": cstr(overrides.get("to_date")).strip() or common.today_string(),
		"item_code": cstr(overrides.get("item_code") or overrides.get("item")).strip(),
		"supplier": cstr(overrides.get("supplier")).strip(),
		"item_group": cstr(overrides.get("item_group")).strip(),
	}


def _item_history_controls(filters: dict[str, object]) -> dict[str, object]:
	return {
		"appearance": "analytics_compact",
		"submitLabel": "Apply",
		"resetLabel": "Reset",
		"meta": [
			{"label": "Mode", "value": "Read-only"},
			{"label": "Scope", "value": "Buyer price review"},
		],
		"fields": [
			{"key": "from_date", "label": "From", "type": "date", "value": filters.get("from_date"), "row": 1},
			{"key": "to_date", "label": "To", "type": "date", "value": filters.get("to_date"), "row": 1},
			{"key": "item_code", "label": "Item", "type": "link", "linkDoctype": "Item", "value": filters.get("item_code"), "placeholder": "Select item", "row": 1},
			{"key": "supplier", "label": "Supplier", "type": "link", "linkDoctype": "Supplier", "value": filters.get("supplier"), "placeholder": "Select supplier", "row": 1},
			{"key": "item_group", "label": "Item Group", "type": "link", "linkDoctype": "Item Group", "value": filters.get("item_group"), "placeholder": "Select item group", "row": 2},
		],
		"actions": [
			{"key": "refresh", "label": "Refresh"},
		],
	}


def _item_history_display_columns() -> list[dict[str, object]]:
	return [
		{"key": "item_code", "label": "Item", "nowrap": True},
		{"key": "supplier", "label": "Supplier", "nowrap": True},
		{"key": "purchase_order", "label": "Purchase Order", "nowrap": True},
		{"key": "order_date", "label": "Order Date", "nowrap": True},
		{"key": "qty", "label": "Qty", "align": "right"},
		{"key": "uom", "label": "UOM", "nowrap": True},
		{"key": "rate", "label": "Rate", "align": "right"},
		{"key": "amount", "label": "Amount", "align": "right"},
		{"key": "currency", "label": "Currency", "nowrap": True},
		{"key": "price_signal", "label": "Price Signal", "nowrap": True},
	]


def _visible_item_history_purchase_orders(filters: dict[str, object]) -> list[dict[str, object]]:
	query_filters: list[list[object]] = [["Purchase Order", "docstatus", "<", 2]]
	if filters.get("from_date"):
		query_filters.append(["Purchase Order", "transaction_date", ">=", filters.get("from_date")])
	if filters.get("to_date"):
		query_filters.append(["Purchase Order", "transaction_date", "<=", filters.get("to_date")])
	if filters.get("supplier"):
		query_filters.append(["Purchase Order", "supplier", "=", filters.get("supplier")])
	fields = ["name", "transaction_date", "supplier", "supplier_name", "currency", "status", "docstatus"]
	return common.get_list("Purchase Order", fields=fields, filters=query_filters, order_by="transaction_date desc, name desc", limit=ROW_LIMIT)


def _purchase_order_items_for_history(po_names: list[str], filters: dict[str, object]) -> list[dict[str, object]]:
	if not po_names:
		return []
	child_filters: dict[str, object] = {"parent": ["in", po_names]}
	if filters.get("item_code"):
		child_filters["item_code"] = filters.get("item_code")
	if filters.get("item_group"):
		child_filters["item_group"] = filters.get("item_group")
	try:
		return list(
			frappe.get_all(
				"Purchase Order Item",
				filters=child_filters,
				fields=_available_child_fields("Purchase Order Item", ["name", "parent", "idx", "item_code", "item_name", "item_group", "qty", "uom", "rate", "amount", "base_rate", "base_amount"]),
				order_by="parent desc, idx asc",
				limit_page_length=ROW_LIMIT,
			)
		)
	except Exception:
		return []


def _item_history_source_rows(purchase_orders: list[dict[str, object]], items: list[dict[str, object]]) -> list[dict[str, object]]:
	po_by_name = {cstr(row.get("name")).strip(): row for row in purchase_orders if cstr(row.get("name")).strip()}
	rows: list[dict[str, object]] = []
	for item in items:
		po_name = cstr(item.get("parent")).strip()
		po = po_by_name.get(po_name)
		if not po:
			continue
		rows.append(
			{
				"key": cstr(item.get("name") or f"{po_name}:{item.get('item_code')}"),
				"purchase_order": po_name,
				"order_date": cstr(po.get("transaction_date")).strip(),
				"supplier": cstr(po.get("supplier")).strip(),
				"supplier_name": cstr(po.get("supplier_name") or po.get("supplier")).strip(),
				"currency": cstr(po.get("currency")).strip(),
				"status": cstr(po.get("status")).strip(),
				"item_code": cstr(item.get("item_code")).strip(),
				"item_name": cstr(item.get("item_name")).strip(),
				"item_group": cstr(item.get("item_group")).strip(),
				"qty": flt(item.get("qty")),
				"uom": cstr(item.get("uom")).strip(),
				"rate": flt(item.get("rate")),
				"amount": flt(item.get("amount")),
				"base_rate": flt(item.get("base_rate")),
				"base_amount": flt(item.get("base_amount")),
			}
		)
	return rows


def _item_history_rows(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object]]:
	formatted_rows: list[dict[str, object]] = []
	action_targets: dict[str, object] = {}
	last_by_item = _last_item_history_rate_by_item(rows)
	can_read_supplier = common.can_read("Supplier")
	can_read_item = common.can_read("Item")
	for row in rows[:ROW_LIMIT]:
		po_name = cstr(row.get("purchase_order")).strip()
		supplier = cstr(row.get("supplier")).strip()
		item_code = cstr(row.get("item_code")).strip()
		currency = cstr(row.get("currency")).strip()
		po_action = f"item_history:po:{po_name}"
		supplier_action = f"item_history:supplier:{supplier}"
		item_action = f"item_history:item:{item_code}"
		if po_name:
			action_targets[po_action] = {"kind": "page", "route": "procurement-console-po-follow-up", "route_parts": [po_name]}
		if supplier and can_read_supplier:
			action_targets[supplier_action] = {"kind": "page", "route": "procurement-console-supplier", "route_parts": [supplier]}
		if item_code and can_read_item:
			action_targets[item_action] = {"kind": "page", "route": "procurement-console-item", "route_parts": [item_code]}
		is_last = row.get("key") == last_by_item.get(item_code, {}).get("key")
		formatted_rows.append(
			{
				"key": cstr(row.get("key") or f"{po_name}:{item_code}"),
				"cells": {
					"item_code": {"value": item_code or "-", "detail": cstr(row.get("item_name")).strip(), "actionKey": item_action} if item_code and can_read_item else {"value": item_code or "-", "detail": cstr(row.get("item_name")).strip()},
					"supplier": {"value": supplier or "-", "detail": cstr(row.get("supplier_name")).strip(), "actionKey": supplier_action} if supplier and can_read_supplier else {"value": supplier or "-", "detail": cstr(row.get("supplier_name")).strip()},
					"purchase_order": {"value": po_name or "-", "actionKey": po_action} if po_name else {"value": "-"},
					"order_date": {"value": cstr(row.get("order_date") or "-")},
					"qty": {"value": _quantity(row.get("qty"))},
					"uom": {"value": cstr(row.get("uom") or "-")},
					"rate": {"value": _money(row.get("rate"), currency)},
					"amount": {"value": _money(row.get("amount"), currency)},
					"currency": {"value": currency or "-"},
					"price_signal": {"value": "Last purchase" if is_last else "History"},
				},
			}
		)
	return formatted_rows, action_targets


def _last_item_history_rate_by_item(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
	latest: dict[str, dict[str, object]] = {}
	for row in rows:
		item_code = cstr(row.get("item_code")).strip()
		if not item_code:
			continue
		current = latest.get(item_code)
		if not current or cstr(row.get("order_date")).strip() > cstr(current.get("order_date")).strip():
			latest[item_code] = row
	return latest


def _item_history_metrics(rows: list[dict[str, object]]) -> list[dict[str, object]]:
	items = {cstr(row.get("item_code")).strip() for row in rows if cstr(row.get("item_code")).strip()}
	suppliers = {cstr(row.get("supplier")).strip() for row in rows if cstr(row.get("supplier")).strip()}
	currency = cstr(rows[0].get("currency")).strip() if rows else ""
	latest = max(rows, key=lambda row: cstr(row.get("order_date")).strip(), default={})
	qty_total = sum(max(flt(row.get("qty")), 0) for row in rows)
	amount_total = sum(flt(row.get("amount")) for row in rows)
	weighted_rate = amount_total / qty_total if qty_total else 0
	return [
		common.metric("Purchase lines", len(rows), "Visible purchase order lines in this report.", "slate"),
		common.metric("Items", len(items), "Distinct items represented in visible purchase lines.", "teal"),
		common.metric("Suppliers", len(suppliers), "Distinct suppliers represented in visible purchase lines.", "indigo"),
		common.metric("Last rate", _money(latest.get("rate"), cstr(latest.get("currency") or currency)), "Most recent visible purchase rate.", "amber"),
		common.metric("Weighted average", _money(weighted_rate, currency), "Amount divided by quantity across visible purchase lines.", "red"),
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
