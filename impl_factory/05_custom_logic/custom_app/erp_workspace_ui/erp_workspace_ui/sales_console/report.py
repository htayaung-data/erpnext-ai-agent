from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import frappe
from frappe import _
from frappe.desk.query_report import run as run_query_report
from frappe.utils import add_months, flt, fmt_money, formatdate, getdate, nowdate
from frappe.utils.data import get_timespan_date_range

from . import service


ROW_LIMIT = 50


@frappe.whitelist()
def get_sales_console_report_context(
	report_key: str | None = None,
	filter_overrides: dict[str, object] | str | None = None,
) -> dict[str, object]:
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)

	normalized_key = _normalize_report_key(report_key)
	context = service._build_context()
	scope = service._build_scope(context)
	overrides = _coerce_filter_overrides(filter_overrides)
	if normalized_key == "sales_analytics":
		return _apply_report_operating_contract(_build_sales_analytics_report(context, scope, overrides))
	if normalized_key == "sales_order_analysis":
		return _apply_report_operating_contract(_build_sales_order_analysis_report(context, scope, overrides))
	if normalized_key == "quotation_trends":
		return _apply_report_operating_contract(_build_quotation_trends_report(context, scope, overrides))
	if normalized_key == "collections_status":
		return _apply_report_operating_contract(_build_collections_status_report(context, scope, overrides))
	if normalized_key == "payment_terms_status_sales_order":
		return _apply_report_operating_contract(_build_collections_status_report(context, scope, overrides))
	if normalized_key == "item_wise_sales_history":
		return _apply_report_operating_contract(_build_item_wise_sales_history_report(context, scope, overrides))
	if normalized_key == "lost_quotations":
		return _apply_report_operating_contract(_build_lost_quotations_report(context, scope, overrides))
	builder = _report_registry().get(normalized_key)
	if not builder:
		return _apply_report_operating_contract(_route_unavailable_payload(normalized_key, scope))
	return _apply_report_operating_contract(builder(context, scope))

def _report_registry() -> dict[str, Callable[[dict[str, object], dict[str, object]], dict[str, object]]]:
	return {
		"sales_analytics": _build_sales_analytics_report,
		"sales_order_analysis": _build_sales_order_analysis_report,
		"quotation_trends": _build_quotation_trends_report,
		"collections_status": _build_collections_status_report,
		"payment_terms_status_sales_order": _build_collections_status_report,
		"item_wise_sales_history": _build_item_wise_sales_history_report,
		"lost_quotations": _build_lost_quotations_report,
	}


def _normalize_report_key(report_key: str | None) -> str:
	return (report_key or "").strip().lower().replace("-", "_")


def _coerce_filter_overrides(filter_overrides: dict[str, object] | str | None) -> dict[str, object]:
	if not filter_overrides:
		return {}
	if isinstance(filter_overrides, dict):
		return filter_overrides
	if isinstance(filter_overrides, str):
		try:
			parsed = json.loads(filter_overrides)
		except Exception:
			return {}
		return parsed if isinstance(parsed, dict) else {}
	return {}

def _build_sales_analytics_report(
	context: dict[str, object],
	scope: dict[str, object],
	filter_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
	filters = _sales_analytics_filters(filter_overrides)
	company_currency = _company_currency(filters.get("company"))
	entity_labels = _sales_analytics_entity_labels(filters.get("tree_type"))
	try:
		payload = run_query_report("Sales Analytics", filters=filters, ignore_prepared_report=True)
		raw_columns = _normalize_columns(payload.get("columns") or [])
		raw_rows = _normalize_rows(payload.get("result") or payload.get("data") or [], raw_columns)
		report_rows = _prepare_sales_analytics_rows(raw_rows, filters)
		columns = _sales_analytics_columns(raw_columns, filters)
		rows, action_targets = _build_rows(report_rows, columns, company_currency)
		return {
			"page": {"title": "Sales Analytics", "key": "sales_analytics"},
			"summary": {
				"title": "Sales Analytics",
				"subtitle": f"Billed sales value by {entity_labels['plural'].lower()} across the selected reporting window.",
			},
			"controls": _sales_analytics_controls(filters, scope),
			"metrics": _sales_analytics_metrics(report_rows, payload, filters, company_currency),
			"secondary": _sales_analytics_secondary(payload.get("chart"), filters, company_currency),
			"results": {
				"title": f"{entity_labels['singular']} performance detail",
				"subtitle": f"Visible {entity_labels['plural'].lower()} and period billed value in the current analytics window.",
				"meta": _results_meta(len(report_rows)),
				"columns": [{"key": col["key"], "label": col["label"], "align": col["align"]} for col in columns],
				"rows": rows[:ROW_LIMIT],
				"state": _ready_state() if report_rows else {
					"kind": "empty",
					"title": "No visible records",
					"detail": f"The current billed-sales window does not return any visible {entity_labels['plural'].lower()} inside this ERP scope.",
				},
			},
			"action_targets": action_targets,
		}
	except Exception as exc:  # pragma: no cover - exercised against live ERP runtime
		message = getattr(exc, "message", None) or str(exc) or "Unknown report error."
		return {
			"page": {"title": "Sales Analytics", "key": "sales_analytics"},
			"summary": {
				"title": "Sales Analytics",
				"subtitle": f"Billed sales value by {entity_labels['plural'].lower()} across the selected reporting window.",
			},
			"controls": _sales_analytics_controls(filters, scope),
			"results": {
				"title": "Report state",
				"state": {
					"kind": "error",
					"title": "Report unavailable",
					"detail": message,
					"action": {"key": "open_native_report", "label": "Open Native Report"},
				},
			},
			"action_targets": {
				"open_native_report": {"kind": "report", "report_name": "Sales Analytics", "filters": filters},
			},
		}

def _build_sales_order_analysis_report(
	context: dict[str, object],
	scope: dict[str, object],
	filter_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
	filters = _sales_order_analysis_filters(filter_overrides)
	company_currency = _company_currency(filters.get("company"))
	query_filters = {
		"company": filters.get("company"),
		"from_date": filters.get("from_date"),
		"to_date": filters.get("to_date"),
		"group_by_so": 1,
	}
	try:
		payload = run_query_report("Sales Order Analysis", filters=query_filters, ignore_prepared_report=True)
		raw_columns = _normalize_columns(payload.get("columns") or [])
		raw_rows = _normalize_rows(payload.get("result") or payload.get("data") or [], raw_columns)
		report_rows = _prepare_sales_order_analysis_rows(raw_rows, filters)
		columns = _sales_order_analysis_columns()
		rows, action_targets = _build_rows(report_rows, columns, company_currency)
		return {
			"page": {"title": "Sales Order Analysis", "key": "sales_order_analysis"},
			"summary": {
				"title": "Sales Order Analysis",
				"subtitle": "Submitted sales orders shaped for delivery and billing review across the selected operating window.",
			},
			"controls": _sales_order_analysis_controls(filters, scope),
			"metrics": _sales_order_analysis_metrics(report_rows, payload, filters, company_currency),
			"secondary": _sales_order_analysis_secondary(report_rows, filters, company_currency),
			"results": {
				"title": "Order execution detail",
				"subtitle": "Visible sales orders reduced to delivery, billing, and value posture inside the selected window.",
				"meta": _results_meta(len(report_rows)),
				"columns": [{"key": col["key"], "label": col["label"], "align": col["align"]} for col in columns],
				"rows": rows[:ROW_LIMIT],
				"state": _ready_state() if report_rows else {
					"kind": "empty",
					"title": "No visible records",
					"detail": _sales_order_analysis_empty_detail(filters),
				},
			},
			"action_targets": action_targets,
		}
	except Exception as exc:  # pragma: no cover - exercised against live ERP runtime
		message = getattr(exc, "message", None) or str(exc) or "Unknown report error."
		return {
			"page": {"title": "Sales Order Analysis", "key": "sales_order_analysis"},
			"summary": {
				"title": "Sales Order Analysis",
				"subtitle": "Submitted sales orders shaped for delivery and billing review across the selected operating window.",
			},
			"controls": _sales_order_analysis_controls(filters, scope),
			"results": {
				"title": "Report state",
				"state": {
					"kind": "error",
					"title": "Live report unavailable",
					"detail": message,
				},
			},
			"action_targets": {},
		}



def _build_quotation_trends_report(
	context: dict[str, object],
	scope: dict[str, object],
	filter_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
	filters = _quotation_trends_filters(filter_overrides)
	company_currency = _company_currency(filters.get("company"))
	entity_labels = _sales_analytics_entity_labels(filters.get("based_on"))
	try:
		payload = run_query_report("Quotation Trends", filters=filters, ignore_prepared_report=True)
		raw_columns = _normalize_columns(payload.get("columns") or [])
		raw_rows = _normalize_rows(payload.get("result") or payload.get("data") or [], raw_columns)
		report_rows = _prepare_quotation_trends_rows(raw_rows)
		columns = _quotation_trends_columns(raw_columns, report_rows, filters)
		rows, action_targets = _build_rows(report_rows, columns, company_currency)
		return {
			"page": {"title": "Quotation Trends", "key": "quotation_trends"},
			"summary": {
				"title": "Quotation Trends",
				"subtitle": f"Quoted value movement by {entity_labels['plural'].lower()} across the selected fiscal window.",
			},
			"controls": _quotation_trends_controls(filters, scope),
			"metrics": _quotation_trends_metrics(report_rows, payload, filters, company_currency),
			"secondary": _quotation_trends_secondary(payload.get("chart"), filters, company_currency),
			"results": {
				"title": f"{entity_labels['singular']} quotation detail",
				"subtitle": f"Visible {entity_labels['plural'].lower()} ranked by quoted value across the active fiscal window.",
				"meta": _results_meta(len(report_rows)),
				"columns": [{"key": col["key"], "label": col["label"], "align": col["align"]} for col in columns],
				"rows": rows[:ROW_LIMIT],
				"state": _ready_state() if report_rows else {
					"kind": "empty",
					"title": "No visible records",
					"detail": f"The selected fiscal window does not return any visible quotation movement for these {entity_labels['plural'].lower()} inside this ERP scope.",
				},
			},
			"action_targets": action_targets,
		}
	except Exception as exc:  # pragma: no cover - exercised against live ERP runtime
		message = getattr(exc, "message", None) or str(exc) or "Unknown report error."
		return {
			"page": {"title": "Quotation Trends", "key": "quotation_trends"},
			"summary": {
				"title": "Quotation Trends",
				"subtitle": f"Quoted value movement by {entity_labels['plural'].lower()} across the selected fiscal window.",
			},
			"controls": _quotation_trends_controls(filters, scope),
			"results": {
				"title": "Report state",
				"state": {
					"kind": "error",
					"title": "Live report unavailable",
					"detail": message,
				},
			},
			"action_targets": {},
		}


def _build_collections_status_report(
	context: dict[str, object],
	scope: dict[str, object],
	filter_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
	filters = _collections_status_filters(filter_overrides)
	company_currency = _company_currency(filters.get("company"))
	try:
		report_rows = _fetch_collections_status_rows(filters, scope)
		columns = _collections_status_columns()
		rows, action_targets = _build_rows(report_rows, columns, company_currency)
		return {
			"page": {"title": "Collections Status", "key": "collections_status"},
			"summary": {
				"title": "Collections Status",
				"subtitle": "Actual invoice settlement and receivable exposure across the selected operating window.",
			},
			"controls": _collections_status_controls(filters, scope),
			"metrics": _collections_status_metrics(report_rows, filters, company_currency),
			"secondary": _collections_status_secondary(report_rows, filters, company_currency),
			"results": {
				"title": "Invoice settlement detail",
				"subtitle": "Visible customer invoices reduced to due date, settlement posture, collected value, and outstanding exposure.",
				"meta": _results_meta(len(report_rows)),
				"columns": [{"key": col["key"], "label": col["label"], "align": col["align"]} for col in columns],
				"rows": rows[:ROW_LIMIT],
				"state": _ready_state() if report_rows else {
					"kind": "empty",
					"title": "No visible invoices",
					"detail": _collections_status_empty_detail(filters),
				},
			},
			"action_targets": action_targets,
		}
	except Exception as exc:  # pragma: no cover - exercised against live ERP runtime
		message = getattr(exc, "message", None) or str(exc) or "Unknown report error."
		return {
			"page": {"title": "Collections Status", "key": "collections_status"},
			"summary": {
				"title": "Collections Status",
				"subtitle": "Actual invoice settlement and receivable exposure across the selected operating window.",
			},
			"controls": _collections_status_controls(filters, scope),
			"results": {
				"title": "Report state",
				"state": {
					"kind": "error",
					"title": "Live report unavailable",
					"detail": message,
				},
			},
			"action_targets": {},
		}


def _build_item_wise_sales_history_report(
	context: dict[str, object],
	scope: dict[str, object],
	filter_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
	filters = _item_wise_sales_history_filters(filter_overrides)
	company_currency = _company_currency(filters.get("company"))
	try:
		payload = run_query_report("Item-wise Sales History", filters=filters, ignore_prepared_report=True)
		raw_columns = _normalize_columns(payload.get("columns") or [])
		raw_rows = _normalize_rows(payload.get("result") or payload.get("data") or [], raw_columns)
		report_rows = _prepare_item_wise_sales_history_rows(raw_rows)
		columns = _item_wise_sales_history_columns()
		if company_currency:
			for column in columns:
				if column.get("fieldname") == "amount":
					column["label"] = f"Sales ({company_currency})"
				elif column.get("fieldname") == "billed_amount":
					column["label"] = f"Billed ({company_currency})"
		rows, action_targets = _build_rows(report_rows, columns, company_currency)
		return {
			"page": {"title": "Item-wise Sales History", "key": "item_wise_sales_history"},
			"summary": {
				"title": "Item-wise Sales History",
				"subtitle": "Submitted sales-order lines reduced to monthly item, customer, and billing history across the selected operating window.",
			},
			"controls": _item_wise_sales_history_controls(filters, scope),
			"metrics": _item_wise_sales_history_metrics(report_rows, payload, filters, company_currency),
			"secondary": _item_wise_sales_history_secondary(report_rows, payload.get("chart"), filters, company_currency),
			"results": {
				"title": "Item sales detail",
				"subtitle": "Visible monthly item summaries shaped for customer, order count, sales value, and downstream billing review inside the selected window.",
				"meta": _results_meta(len(report_rows)),
				"tableMinWidth": 980,
				"columns": [{"key": col["key"], "label": col["label"], "align": col["align"], "nowrap": bool(col.get("nowrap"))} for col in columns],
				"rows": rows[:ROW_LIMIT],
				"state": _ready_state() if report_rows else {
					"kind": "empty",
					"title": "No visible records",
					"detail": _item_wise_sales_history_empty_detail(filters),
				},
			},
			"action_targets": action_targets,
		}
	except Exception as exc:  # pragma: no cover - exercised against live ERP runtime
		message = getattr(exc, "message", None) or str(exc) or "Unknown report error."
		return {
			"page": {"title": "Item-wise Sales History", "key": "item_wise_sales_history"},
			"summary": {
				"title": "Item-wise Sales History",
				"subtitle": "Submitted sales-order lines reduced to monthly item, customer, and billing history across the selected operating window.",
			},
			"controls": _item_wise_sales_history_controls(filters, scope),
			"results": {
				"title": "Report state",
				"state": {
					"kind": "error",
					"title": "Live report unavailable",
					"detail": message,
				},
			},
			"action_targets": {},
		}


def _build_lost_quotations_report(
	context: dict[str, object],
	scope: dict[str, object],
	filter_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
	filters = _lost_quotations_filters(filter_overrides)
	company_currency = _company_currency(filters.get("company"))
	try:
		payload = run_query_report("Lost Quotations", filters=filters, ignore_prepared_report=True)
		raw_columns = _normalize_columns(payload.get("columns") or [])
		raw_rows = _normalize_rows(payload.get("result") or payload.get("data") or [], raw_columns)
		report_rows = _prepare_lost_quotations_rows(raw_rows)
		columns = _lost_quotations_columns(raw_columns, filters)
		rows, action_targets = _build_rows(report_rows, columns, company_currency)
		_attach_lost_quotation_bucket_actions(rows, action_targets, report_rows, columns, filters)
		return {
			"page": {"title": "Lost Quotations", "key": "lost_quotations"},
			"summary": {
				"title": "Lost Quotations",
				"subtitle": f"Commercial loss concentration grouped by {str(filters.get('group_by') or 'loss pattern').lower()} across the selected review window.",
			},
			"controls": _lost_quotations_controls(filters, scope),
			"metrics": _lost_quotations_metrics(report_rows, payload, filters, company_currency),
			"results": {
				"title": "Loss pattern detail",
				"subtitle": "Visible loss buckets ranked by lost value inside the current review window.",
				"meta": _results_meta(len(report_rows)),
				"columns": [{"key": col["key"], "label": col["label"], "align": col["align"]} for col in columns],
				"rows": rows[:ROW_LIMIT],
				"state": _ready_state() if report_rows else {
					"kind": "empty",
					"title": "No visible records",
					"detail": "The selected review window does not return any visible lost quotations inside this ERP scope.",
				},
			},
			"action_targets": action_targets,
		}
	except Exception as exc:  # pragma: no cover - exercised against live ERP runtime
		message = getattr(exc, "message", None) or str(exc) or "Unknown report error."
		return {
			"page": {"title": "Lost Quotations", "key": "lost_quotations"},
			"summary": {
				"title": "Lost Quotations",
				"subtitle": f"Commercial loss concentration grouped by {str(filters.get('group_by') or 'loss pattern').lower()} across the selected review window.",
			},
			"controls": _lost_quotations_controls(filters, scope),
			"results": {
				"title": "Report state",
				"state": {
					"kind": "error",
					"title": "Live report unavailable",
					"detail": message,
				},
			},
			"action_targets": {},
		}


def _build_sales_order_trends_report(
	context: dict[str, object],
	scope: dict[str, object],
	filter_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
	filters = _sales_order_trends_filters(filter_overrides)
	company_currency = _company_currency(filters.get("company"))
	entity_labels = _sales_analytics_entity_labels(filters.get("based_on"))
	try:
		payload = run_query_report("Sales Order Trends", filters=filters, ignore_prepared_report=True)
		raw_columns = _normalize_columns(payload.get("columns") or [])
		raw_rows = _normalize_rows(payload.get("result") or payload.get("data") or [], raw_columns)
		report_rows = _prepare_sales_order_trends_rows(raw_rows)
		columns = _sales_order_trends_columns(raw_columns, report_rows, filters)
		rows, action_targets = _build_rows(report_rows, columns, company_currency)
		return {
			"page": {"title": "Sales Order Trends", "key": "sales_order_trends"},
			"summary": {
				"title": "Sales Order Trends",
				"subtitle": f"Submitted order value movement by {entity_labels['plural'].lower()} across the selected fiscal window.",
			},
			"controls": _sales_order_trends_controls(filters, scope),
			"metrics": _sales_order_trends_metrics(report_rows, payload, filters, company_currency),
			"secondary": _sales_order_trends_secondary(payload.get("chart"), filters, company_currency),
			"results": {
				"title": f"{entity_labels['singular']} order trend detail",
				"subtitle": f"Visible {entity_labels['plural'].lower()} ranked by order value across the active fiscal window.",
				"meta": _results_meta(len(report_rows)),
				"columns": [{"key": col["key"], "label": col["label"], "align": col["align"]} for col in columns],
				"rows": rows[:ROW_LIMIT],
				"state": _ready_state() if report_rows else {
					"kind": "empty",
					"title": "No visible records",
					"detail": _sales_order_trends_empty_detail(filters, entity_labels),
				},
			},
			"action_targets": action_targets,
		}
	except Exception as exc:  # pragma: no cover - exercised against live ERP runtime
		message = getattr(exc, "message", None) or str(exc) or "Unknown report error."
		return {
			"page": {"title": "Sales Order Trends", "key": "sales_order_trends"},
			"summary": {
				"title": "Sales Order Trends",
				"subtitle": f"Submitted order value movement by {entity_labels['plural'].lower()} across the selected fiscal window.",
			},
			"controls": _sales_order_trends_controls(filters, scope),
			"results": {
				"title": "Report state",
				"state": {
					"kind": "error",
					"title": "Live report unavailable",
					"detail": message,
				},
			},
			"action_targets": {},
		}


def _build_report_payload(
	*,
	report_key: str,
	report_name: str,
	page_title: str,
	summary_subtitle: str,
	results_title: str,
	results_subtitle: str,
	filters: dict[str, object],
	scope: dict[str, object],
	filter_chip_builder: Callable[[dict[str, object], dict[str, object]], list[dict[str, object]]],
	metric_builder: Callable[[list[dict[str, object]], dict[str, object], dict[str, object], str | None], list[dict[str, object]]],
	secondary_builder: Callable[[dict[str, object] | None, dict[str, object], str | None], dict[str, object] | None] | None = None,
) -> dict[str, object]:
	company_currency = _company_currency(filters.get("company"))
	try:
		payload = run_query_report(report_name, filters=filters, ignore_prepared_report=True)
		columns = _normalize_columns(payload.get("columns") or [])
		raw_rows = _normalize_rows(payload.get("result") or payload.get("data") or [], columns)
		rows, action_targets = _build_rows(raw_rows, columns, company_currency)
		visible_rows = rows[:ROW_LIMIT]
		metrics = metric_builder(raw_rows, payload, filters, company_currency)
		secondary = secondary_builder(payload.get("chart"), filters, company_currency) if secondary_builder else None
		return {
			"page": {"title": page_title},
			"summary": {
				"title": page_title,
				"subtitle": summary_subtitle,
			},
			"controls": {
				"filterChips": filter_chip_builder(filters, scope),
			},
			"metrics": metrics,
			"secondary": secondary,
			"results": {
				"title": results_title,
				"subtitle": results_subtitle,
				"meta": _results_meta(len(raw_rows)),
				"columns": [{"key": col["key"], "label": col["label"], "align": col["align"]} for col in columns],
				"rows": visible_rows,
				"state": _ready_state() if raw_rows else {
					"kind": "empty",
					"title": "No visible records",
					"detail": "The current report window does not return any records inside this ERP permission scope.",
				},
			},
			"action_targets": action_targets,
		}
	except Exception as exc:  # pragma: no cover - exercised against live ERP runtime
		return _report_error_payload(
			report_name=report_name,
			page_title=page_title,
			summary_subtitle=summary_subtitle,
			scope=scope,
			filters=filters,
			filter_chip_builder=filter_chip_builder,
			exc=exc,
		)


def _route_unavailable_payload(report_key: str, scope: dict[str, object]) -> dict[str, object]:
	return {
		"page": {"title": "Sales Console Report"},
		"summary": {
			"title": "Report route unavailable",
			"subtitle": f"The report route '{report_key or 'unknown'}' is not configured for this productized report surface.",
		},
		"controls": {
			"filterChips": _scope_filter_chip(scope),
		},
		"results": {
			"title": "Report state",
			"state": {
				"kind": "error",
				"title": "Unsupported report route",
				"detail": "Open the report from a Sales Console report card so the correct route key is passed through.",
			},
		},
			"action_targets": {},
	}


def _base_report_actions() -> list[dict[str, object]]:
	return [
		{"key": "back_to_console", "label": "Back to Sales Console"},
		{"key": "refresh", "label": "Refresh"},
	]


def _merge_report_actions(
	base_actions: list[dict[str, object]], extra_actions: list[dict[str, object]] | None = None
) -> list[dict[str, object]]:
	merged: list[dict[str, object]] = []
	seen_keys: set[str] = set()
	for action in [*(base_actions or []), *((extra_actions or []))]:
		if not isinstance(action, dict):
			continue
		key = str(action.get("key") or "").strip()
		if not key or key in seen_keys:
			continue
		seen_keys.add(key)
		merged.append(dict(action))
	return merged


def _apply_report_operating_contract(payload: dict[str, object]) -> dict[str, object]:
	normalized = dict(payload or {})
	controls = dict(normalized.get("controls") or {})
	existing_actions = [
		dict(action)
		for action in (controls.get("actions") or [])
		if isinstance(action, dict)
	]
	controls["actions"] = _merge_report_actions(_base_report_actions(), existing_actions)
	normalized["controls"] = controls
	return normalized


def _report_error_payload(
	*,
	report_name: str,
	page_title: str,
	summary_subtitle: str,
	scope: dict[str, object],
	filters: dict[str, object],
	filter_chip_builder: Callable[[dict[str, object], dict[str, object]], list[dict[str, object]]],
	exc: Exception,
) -> dict[str, object]:
	message = getattr(exc, "message", None) or str(exc) or "Unknown report error."
	return {
		"page": {"title": page_title},
		"summary": {
			"title": page_title,
			"subtitle": summary_subtitle,
		},
		"controls": {
			"filterChips": filter_chip_builder(filters, scope),
		},
		"results": {
			"title": "Report state",
			"state": {
				"kind": "error",
				"title": "Report unavailable",
				"detail": message,
				"action": {"key": "open_native_report", "label": "Open Native Report"},
			},
		},
		"action_targets": {
			"open_native_report": {"kind": "report", "report_name": report_name, "filters": filters},
		},
	}


def _default_company() -> str | None:
	return (
		frappe.defaults.get_user_default("Company")
		or frappe.defaults.get_default("company")
		or frappe.db.get_value("Company", {}, "name")
	)


def _company_currency(company: object) -> str | None:
	if not company:
		return None
	return frappe.db.get_value("Company", company, "default_currency")


def _current_fiscal_year_window() -> dict[str, object]:
	today = getdate(nowdate())
	fiscal_year = frappe.db.get_value(
		"Fiscal Year",
		{
			"disabled": 0,
			"year_start_date": ["<=", today],
			"year_end_date": [">=", today],
		},
		["name", "year_start_date", "year_end_date"],
		as_dict=True,
	)
	if fiscal_year:
		return fiscal_year

	fiscal_year = frappe.db.get_value(
		"Fiscal Year",
		{"disabled": 0},
		["name", "year_start_date", "year_end_date"],
		as_dict=True,
		order_by="year_start_date desc",
	)
	if fiscal_year:
		return fiscal_year

	return {
		"name": "Current Fiscal Year",
		"year_start_date": today,
		"year_end_date": today,
	}


def _sales_analytics_filters(filter_overrides: dict[str, object] | None = None) -> dict[str, object]:
	fiscal_window = _current_fiscal_year_window()
	filters = {
		"tree_type": "Customer",
		"doc_type": "Sales Invoice",
		"value_quantity": "Value",
		"from_date": str(fiscal_window["year_start_date"]),
		"to_date": str(fiscal_window["year_end_date"]),
		"company": _default_company(),
		"range": "Monthly",
		"curves": "total",
	}
	overrides = filter_overrides or {}
	allowed_tree_types = {option["value"] for option in _sales_analytics_tree_type_options()}
	allowed_ranges = {option["value"] for option in _sales_analytics_range_options()}
	tree_type = str(overrides.get("tree_type") or filters["tree_type"])
	range_value = str(overrides.get("range") or filters["range"])
	if tree_type in allowed_tree_types:
		filters["tree_type"] = tree_type
	if range_value in allowed_ranges:
		filters["range"] = range_value
	for key in ("from_date", "to_date"):
		value = overrides.get(key)
		if not value:
			continue
		try:
			filters[key] = str(getdate(value))
		except Exception:
			pass
	try:
		if getdate(filters["from_date"]) > getdate(filters["to_date"]):
			filters["from_date"], filters["to_date"] = filters["to_date"], filters["from_date"]
	except Exception:
		pass
	return filters


def _sales_analytics_tree_type_options() -> list[dict[str, str]]:
	return [
		{"label": "Customer", "value": "Customer"},
		{"label": "Customer Group", "value": "Customer Group"},
		{"label": "Item Group", "value": "Item Group"},
	]


def _sales_analytics_range_options() -> list[dict[str, str]]:
	return [
		{"label": "Monthly", "value": "Monthly"},
		{"label": "Quarterly", "value": "Quarterly"},
		{"label": "Yearly", "value": "Yearly"},
	]


def _sales_analytics_entity_labels(tree_type: str | None) -> dict[str, str]:
	label_map = {
		"Customer": {"singular": "Customer", "plural": "Customers"},
		"Territory": {"singular": "Territory", "plural": "Territories"},
		"Customer Group": {"singular": "Customer group", "plural": "Customer groups"},
		"Item": {"singular": "Item", "plural": "Items"},
		"Item Group": {"singular": "Item group", "plural": "Item groups"},
		"Project": {"singular": "Project", "plural": "Projects"},
	}
	return label_map.get(tree_type or "Customer", label_map["Customer"])


def _scope_control_value(scope: dict[str, object]) -> str:
	branch_name = scope.get("branch_name")
	scope_mode = scope.get("scope_mode")
	scope_label_map = {
		"team_review_scope": "Team scope",
		"assigned_account_scope": "Assigned scope",
		"showroom_scope": "Showroom scope",
		"executive_review_scope": "Executive scope",
		"branch_and_owner_filtered": "Branch scope",
	}
	scope_label = scope_label_map.get(scope_mode, "Permission scope")
	return f"{scope_label}: {branch_name}" if branch_name else scope_label


def _sales_analytics_controls(filters: dict[str, object], scope: dict[str, object]) -> dict[str, object]:
	scope_value = _scope_control_value(scope)
	return {
		"appearance": "analytics_compact",
		"meta": [{"label": "Scope", "value": scope_value}],
		"fields": [
			{
				"key": "tree_type",
				"label": "View by",
				"type": "select",
				"value": filters.get("tree_type") or "Customer",
				"options": _sales_analytics_tree_type_options(),
			},
			{
				"key": "range",
				"label": "Periodicity",
				"type": "select",
				"value": filters.get("range") or "Monthly",
				"options": _sales_analytics_range_options(),
			},
			{
				"key": "from_date",
				"label": "Window start",
				"type": "date",
				"value": filters.get("from_date"),
				"span": 2,
			},
			{
				"key": "to_date",
				"label": "Window end",
				"type": "date",
				"value": filters.get("to_date"),
				"span": 2,
			},
		],
		"submitLabel": "Apply",
		"resetLabel": "Reset",
	}



def _prepare_sales_analytics_rows(rows: list[dict[str, object]], filters: dict[str, object]) -> list[dict[str, object]]:
	tree_type = filters.get("tree_type") or "Customer"
	prepared: list[dict[str, object]] = []
	for row in rows:
		row_copy = dict(row)
		entity = str(row_copy.get("entity") or row_copy.get("entity_name") or "--").strip()
		entity_lower = entity.lower()
		if tree_type == "Customer" and len(rows) > 1 and entity_lower == "total":
			continue
		if tree_type != "Customer" and len(rows) > 1 and entity_lower.startswith("all "):
			continue
		if tree_type == "Customer":
			row_copy["entity"] = row_copy.get("entity_name") or row_copy.get("entity") or "--"
		else:
			row_copy["entity"] = row_copy.get("entity") or row_copy.get("entity_name") or "--"
		row_copy["_row_total"] = _sales_analytics_row_total(row_copy)
		if flt(row_copy.get("_row_total")) <= 0 and len(rows) > 1:
			continue
		prepared.append(row_copy)
	prepared.sort(key=lambda item: flt(item.get("_row_total")), reverse=True)
	return prepared


def _sales_analytics_columns(columns: list[dict[str, object]], filters: dict[str, object]) -> list[dict[str, object]]:
	entity_labels = _sales_analytics_entity_labels(filters.get("tree_type"))
	prepared: list[dict[str, object]] = []
	for column in columns:
		if column.get("key") == "entity_name":
			continue
		updated = dict(column)
		if updated.get("key") == "entity":
			updated["label"] = entity_labels["singular"]
		elif updated.get("key") == "total":
			updated["label"] = "Total Value"
		prepared.append(updated)
	return prepared


def _sales_analytics_row_total(row: dict[str, object]) -> float:
	for key in ("total", "total(amt)", "total_amount", "amount"):
		if row.get(key) not in (None, ""):
			return flt(row.get(key))
	total = 0.0
	for key, value in row.items():
		if key in {"entity", "entity_name", "currency", "_row_total"}:
			continue
		if value in (None, "", "--"):
			continue
		total += flt(value)
	return total


def _sales_analytics_top_entity(rows: list[dict[str, object]]) -> tuple[str | None, float]:
	if not rows:
		return None, 0.0
	row = rows[0]
	return str(row.get("entity") or "").strip() or None, flt(row.get("_row_total"))

def _sales_order_analysis_filters(filter_overrides: dict[str, object] | None = None) -> dict[str, object]:
	today = getdate(nowdate())
	filters = {
		"company": _default_company(),
		"from_date": str(today.replace(day=1)),
		"to_date": str(today),
		"group_by_so": 1,
		"execution_view": "all_orders",
	}
	overrides = filter_overrides or {}
	allowed_views = {option["value"] for option in _sales_order_analysis_view_options()}
	execution_view = str(overrides.get("execution_view") or filters["execution_view"])
	if execution_view in allowed_views:
		filters["execution_view"] = execution_view
	for key in ("from_date", "to_date"):
		value = overrides.get(key)
		if not value:
			continue
		try:
			filters[key] = str(getdate(value))
		except Exception:
			pass
	try:
		if getdate(filters["from_date"]) > getdate(filters["to_date"]):
			filters["from_date"], filters["to_date"] = filters["to_date"], filters["from_date"]
	except Exception:
		pass
	return filters


def _sales_order_analysis_view_options() -> list[dict[str, str]]:
	return [
		{"label": "All submitted", "value": "all_orders"},
		{"label": "Open execution", "value": "open_execution"},
		{"label": "Completed / closed", "value": "completed_orders"},
	]


def _sales_order_analysis_controls(filters: dict[str, object], scope: dict[str, object]) -> dict[str, object]:
	return {
		"appearance": "analytics_compact",
		"meta": [{"label": "Scope", "value": _scope_control_value(scope)}],
		"fields": [
			{
				"key": "execution_view",
				"label": "View",
				"type": "select",
				"value": filters.get("execution_view") or "all_orders",
				"options": _sales_order_analysis_view_options(),
			},
			{
				"key": "from_date",
				"label": "Window start",
				"type": "date",
				"value": filters.get("from_date"),
				"span": 2,
			},
			{
				"key": "to_date",
				"label": "Window end",
				"type": "date",
				"value": filters.get("to_date"),
				"span": 2,
			},
		],
		"submitLabel": "Apply",
		"resetLabel": "Reset",
	}


def _prepare_sales_order_analysis_rows(rows: list[dict[str, object]], filters: dict[str, object]) -> list[dict[str, object]]:
	execution_view = filters.get("execution_view") or "all_orders"
	prepared: list[dict[str, object]] = []
	for row in rows:
		row_copy = dict(row)
		row_copy["delivery_date"] = row_copy.get("delivery_date") or row_copy.get("required_date") or row_copy.get("date")
		row_copy["qty_to_deliver"] = flt(row_copy.get("pending_qty"))
		row_copy["pending_value"] = flt(row_copy.get("pending_amount"))
		row_copy["order_value"] = flt(row_copy.get("amount"))
		row_copy["billed_value"] = flt(row_copy.get("billed_amount"))
		if not str(row_copy.get("sales_order") or "").strip():
			continue
		row_copy["_open_execution"] = _sales_order_analysis_is_open_execution(row_copy)
		row_copy["_overdue_delivery"] = _sales_order_analysis_is_overdue(row_copy)
		if execution_view == "open_execution" and not row_copy["_open_execution"]:
			continue
		if execution_view == "completed_orders" and row_copy["_open_execution"]:
			continue
		prepared.append(row_copy)
	prepared.sort(key=_sales_order_analysis_sort_key)
	return prepared


def _fetch_collections_status_rows(
	filters: dict[str, object],
	scope: dict[str, object],
) -> list[dict[str, object]]:
	invoice_fields = set(service._fieldnames("Sales Invoice"))
	query_filters: list[list[object]] = [["docstatus", "=", 1]]
	if "is_return" in invoice_fields:
		query_filters.append(["is_return", "=", 0])
	if "posting_date" in invoice_fields:
		query_filters.append(["posting_date", ">=", filters.get("from_date")])
		query_filters.append(["posting_date", "<=", filters.get("to_date")])
	query_filters, _scope_note = service._apply_scope_filters("Sales Invoice", query_filters, scope)

	fields = ["name", "customer", "posting_date", "due_date", "status"]
	for optional_field in ("outstanding_amount", "base_grand_total", "base_rounded_total", "grand_total", "rounded_total", "currency"):
		if optional_field in invoice_fields:
			fields.append(optional_field)

	rows = frappe.get_all(
		"Sales Invoice",
		filters=query_filters,
		fields=fields,
		order_by="posting_date desc, name desc",
		limit_page_length=5000,
	)
	return _prepare_collections_status_rows(rows, filters)


def _coerce_report_date(value: object):
	if not value:
		return None
	try:
		return getdate(value)
	except Exception:
		return None


def _prepare_collections_status_rows(
	rows: list[dict[str, object]],
	filters: dict[str, object],
) -> list[dict[str, object]]:
	collection_view = filters.get("collection_view") or "open_invoices"
	today = getdate(nowdate())
	prepared: list[dict[str, object]] = []
	for row in rows:
		row_copy = dict(row)
		invoice_name = str(row_copy.get("name") or "").strip()
		if not invoice_name:
			continue
		row_copy["sales_invoice"] = invoice_name
		row_copy["invoice_value"] = _collections_invoice_value(row_copy)
		row_copy["outstanding_value"] = max(flt(row_copy.get("outstanding_amount")), 0.0)
		row_copy["paid_value"] = max(row_copy["invoice_value"] - row_copy["outstanding_value"], 0.0)
		row_copy["_is_settled"] = row_copy["outstanding_value"] <= 0.009
		due_date = _coerce_report_date(row_copy.get("due_date"))
		row_copy["_is_overdue"] = bool(due_date and due_date < today and not row_copy["_is_settled"])
		row_copy["_is_open"] = not row_copy["_is_settled"]
		row_copy["settlement_status"] = _collections_settlement_status(row_copy)
		if collection_view == "open_invoices" and not row_copy["_is_open"]:
			continue
		if collection_view == "overdue_only" and not row_copy["_is_overdue"]:
			continue
		if collection_view == "settled_invoices" and not row_copy["_is_settled"]:
			continue
		prepared.append(row_copy)
	prepared.sort(key=_collections_status_sort_key)
	return prepared


def _collections_invoice_value(row: dict[str, object]) -> float:
	for key in ("base_rounded_total", "base_grand_total", "rounded_total", "grand_total"):
		if row.get(key) not in (None, ""):
			return flt(row.get(key))
	return 0.0


def _collections_settlement_status(row: dict[str, object]) -> str:
	status = str(row.get("status") or "").strip()
	if row.get("_is_settled"):
		return "Paid"
	if row.get("_is_overdue"):
		return "Overdue"
	if "partly paid" in status.lower():
		return "Partly paid"
	return "Unpaid"


def _collections_status_sort_key(row: dict[str, object]) -> tuple[object, object, object]:
	if row.get("_is_overdue"):
		bucket = 0
	elif row.get("_is_open"):
		bucket = 1
	else:
		bucket = 2
	due_date = str(row.get("due_date") or "9999-12-31")
	return (bucket, due_date, -flt(row.get("outstanding_value")))


def _collections_status_columns() -> list[dict[str, object]]:
	return [
		{"key": "sales_invoice", "fieldname": "sales_invoice", "label": "Sales invoice", "fieldtype": "Link", "options": "Sales Invoice", "align": ""},
		{"key": "customer", "fieldname": "customer", "label": "Customer", "fieldtype": "Link", "options": "Customer", "align": ""},
		{"key": "posting_date", "fieldname": "posting_date", "label": "Posted", "fieldtype": "Date", "options": None, "align": ""},
		{"key": "due_date", "fieldname": "due_date", "label": "Due date", "fieldtype": "Date", "options": None, "align": ""},
		{"key": "settlement_status", "fieldname": "settlement_status", "label": "Settlement", "fieldtype": "Data", "options": None, "align": ""},
		{"key": "paid_value", "fieldname": "paid_value", "label": "Collected", "fieldtype": "Currency", "options": None, "align": "right"},
		{"key": "outstanding_value", "fieldname": "outstanding_value", "label": "Outstanding", "fieldtype": "Currency", "options": None, "align": "right"},
		{"key": "invoice_value", "fieldname": "invoice_value", "label": "Invoice value", "fieldtype": "Currency", "options": None, "align": "right"},
	]


def _collections_status_empty_detail(filters: dict[str, object]) -> str:
	view = filters.get("collection_view") or "open_invoices"
	if view == "overdue_only":
		return "The selected window does not return any overdue customer invoices inside this ERP scope."
	if view == "settled_invoices":
		return "The selected window does not return any fully settled customer invoices inside this ERP scope."
	if view == "open_invoices":
		return "The selected window does not return any open customer invoices inside this ERP scope."
	return "The selected window does not return any visible customer invoices inside this ERP scope."


def _sales_order_analysis_is_open_execution(row: dict[str, object]) -> bool:
	return flt(row.get("pending_qty")) > 0 or flt(row.get("pending_amount")) > 0


def _sales_order_analysis_is_overdue(row: dict[str, object]) -> bool:
	return flt(row.get("pending_qty")) > 0 and flt(row.get("delay")) > 0


def _sales_order_analysis_sort_key(row: dict[str, object]) -> tuple[object, object, object]:
	if row.get("_overdue_delivery"):
		bucket = 0
	elif row.get("_open_execution"):
		bucket = 1
	else:
		bucket = 2
	delivery_date = str(row.get("delivery_date") or "9999-12-31")
	return (bucket, delivery_date, -flt(row.get("order_value")))


def _sales_order_analysis_columns() -> list[dict[str, object]]:
	return [
		{"key": "sales_order", "fieldname": "sales_order", "label": "Sales order", "fieldtype": "Link", "options": "Sales Order", "align": ""},
		{"key": "customer", "fieldname": "customer", "label": "Customer", "fieldtype": "Link", "options": "Customer", "align": ""},
		{"key": "delivery_date", "fieldname": "delivery_date", "label": "Delivery date", "fieldtype": "Date", "options": None, "align": ""},
		{"key": "status", "fieldname": "status", "label": "Execution", "fieldtype": "Data", "options": None, "align": ""},
		{"key": "qty_to_deliver", "fieldname": "qty_to_deliver", "label": "Qty to deliver", "fieldtype": "Float", "options": None, "align": "right"},
		{"key": "pending_value", "fieldname": "pending_value", "label": "Pending bill", "fieldtype": "Currency", "options": None, "align": "right"},
		{"key": "order_value", "fieldname": "order_value", "label": "Order value", "fieldtype": "Currency", "options": None, "align": "right"},
	]


def _sales_order_analysis_empty_detail(filters: dict[str, object]) -> str:
	view = filters.get("execution_view") or "all_orders"
	if view == "open_execution":
		return "The current window does not return any visible open sales orders inside this ERP scope."
	if view == "completed_orders":
		return "The current window does not return any visible completed or closed sales orders inside this ERP scope."
	return "The current report window does not return any visible sales orders inside this ERP permission scope."


def _prepare_quotation_trends_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
	prepared: list[dict[str, object]] = []
	for row in rows:
		row_copy = dict(row)
		row_copy["_entity"] = _quotation_trends_row_entity(row_copy)
		row_copy["_total_amount"] = _quotation_trends_total_amount(row_copy)
		if _quotation_trends_is_total_row(row_copy):
			continue
		if flt(row_copy.get("_total_amount")) <= 0 and len(rows) > 1:
			continue
		prepared.append(row_copy)
	prepared.sort(key=lambda item: (-flt(item.get("_total_amount")), str(item.get("_entity") or "")))
	return prepared


def _quotation_trends_columns(
	columns: list[dict[str, object]],
	rows: list[dict[str, object]],
	filters: dict[str, object],
) -> list[dict[str, object]]:
	prepared: list[dict[str, object]] = []
	for column in columns:
		fieldname = str(column.get("fieldname") or column.get("key") or "")
		if _quotation_trends_is_quantity_field(fieldname):
			continue
		if fieldname == "currency":
			continue
		if fieldname == "party_name" and _quotation_trends_field_values_match(rows, "party", "party_name"):
			continue
		updated = dict(column)
		if fieldname in {"party", "item_code", "item_group", "customer_group", "project"}:
			updated["label"] = _sales_analytics_entity_labels(filters.get("based_on"))["singular"]
		elif fieldname == "territory":
			updated["label"] = "Territory"
			updated["fieldtype"] = "Data"
			updated["options"] = None
		elif fieldname == "total(amt)":
			updated["label"] = "Quoted value"
		elif _quotation_trends_is_period_amount_field(fieldname):
			updated["label"] = _quotation_trends_period_label(updated.get("label") or fieldname)
		prepared.append(updated)
	return prepared


def _prepare_lost_quotations_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
	prepared: list[dict[str, object]] = []
	for row in rows:
		row_copy = dict(row)
		if flt(row_copy.get("lost_value")) <= 0 and flt(row_copy.get("lost_quotations")) <= 0:
			continue
		prepared.append(row_copy)
	prepared.sort(key=lambda item: (-flt(item.get("lost_value")), -flt(item.get("lost_quotations"))))
	return prepared


def _lost_quotations_columns(columns: list[dict[str, object]], filters: dict[str, object]) -> list[dict[str, object]]:
	prepared: list[dict[str, object]] = []
	for column in columns:
		updated = dict(column)
		fieldname = str(updated.get("fieldname") or updated.get("key") or "")
		if fieldname == "lost_quotations_%":
			updated["label"] = "Quotation share"
		elif fieldname == "lost_value_%":
			updated["label"] = "Value share"
		prepared.append(updated)
	return prepared


def _attach_lost_quotation_bucket_actions(
	rows: list[dict[str, object]],
	action_targets: dict[str, dict[str, object]],
	report_rows: list[dict[str, object]],
	columns: list[dict[str, object]],
	filters: dict[str, object],
) -> None:
	if not rows or not report_rows or not columns:
		return
	bucket_column = columns[0]
	bucket_key = str(bucket_column.get("key") or "")
	bucket_fieldname = str(bucket_column.get("fieldname") or bucket_key)
	for row_index, row in enumerate(report_rows[: len(rows)]):
		bucket_value = str(row.get(bucket_fieldname) or "").strip()
		if not bucket_value or bucket_value == "--":
			continue
		target = _lost_quotation_bucket_target(filters, bucket_value)
		if not target:
			continue
		action_key = f"cell:{row_index}:{bucket_fieldname}"
		rows[row_index].setdefault("cells", {}).setdefault(bucket_key, {})["actionKey"] = action_key
		action_targets[action_key] = target


def _quotation_trends_filters(filter_overrides: dict[str, object] | None = None) -> dict[str, object]:
	fiscal_window = _current_fiscal_year_window()
	filters = {
		"period": "Monthly",
		"based_on": "Customer",
		"group_by": "",
		"fiscal_year": fiscal_window["name"],
		"company": _default_company(),
	}
	overrides = filter_overrides or {}
	allowed_periods = {option["value"] for option in _quotation_trends_period_options()}
	allowed_based_on = {option["value"] for option in _quotation_trends_based_on_options()}
	allowed_fiscal_years = {option["value"] for option in _fiscal_year_options()}
	period = str(overrides.get("period") or filters["period"])
	based_on = str(overrides.get("based_on") or filters["based_on"])
	fiscal_year = str(overrides.get("fiscal_year") or filters["fiscal_year"])
	if period in allowed_periods:
		filters["period"] = period
	if based_on in allowed_based_on:
		filters["based_on"] = based_on
	if fiscal_year in allowed_fiscal_years:
		filters["fiscal_year"] = fiscal_year
	filters["group_by"] = ""
	return filters


def _quotation_trends_controls(filters: dict[str, object], scope: dict[str, object]) -> dict[str, object]:
	return {
		"appearance": "analytics_compact",
		"meta": [{"label": "Scope", "value": _scope_control_value(scope)}],
		"fields": [
			{
				"key": "based_on",
				"label": "View by",
				"type": "select",
				"value": filters.get("based_on") or "Customer",
				"options": _quotation_trends_based_on_options(),
			},
			{
				"key": "period",
				"label": "Periodicity",
				"type": "select",
				"value": filters.get("period") or "Monthly",
				"options": _quotation_trends_period_options(),
			},
			{
				"key": "fiscal_year",
				"label": "Fiscal year",
				"type": "select",
				"value": filters.get("fiscal_year"),
				"options": _fiscal_year_options(),
			},
		],
		"submitLabel": "Apply",
		"resetLabel": "Reset",
	}


def _quotation_trends_period_options() -> list[dict[str, str]]:
	return [
		{"label": "Monthly", "value": "Monthly"},
		{"label": "Quarterly", "value": "Quarterly"},
		{"label": "Half-Yearly", "value": "Half-Yearly"},
		{"label": "Yearly", "value": "Yearly"},
	]


def _quotation_trends_based_on_options() -> list[dict[str, str]]:
	return [
		{"label": "Customer", "value": "Customer"},
		{"label": "Customer Group", "value": "Customer Group"},
		{"label": "Item", "value": "Item"},
		{"label": "Item Group", "value": "Item Group"},
		{"label": "Territory", "value": "Territory"},
		{"label": "Project", "value": "Project"},
	]


def _sales_analytics_filter_chips(filters: dict[str, object], scope: dict[str, object]) -> list[dict[str, object]]:
	return _scope_filter_chip(scope) + [
		{"label": "Company", "value": filters.get("company")},
		{"label": "Window", "value": _date_range_label(filters.get("from_date"), filters.get("to_date"))},
		{"label": "Based on", "value": filters.get("doc_type")},
		{"label": "Range", "value": filters.get("range")},
	]


def _sales_order_analysis_filter_chips(filters: dict[str, object], scope: dict[str, object]) -> list[dict[str, object]]:
	return _scope_filter_chip(scope) + [
		{"label": "Company", "value": filters.get("company")},
		{"label": "Window", "value": _date_range_label(filters.get("from_date"), filters.get("to_date"))},
		{"label": "Grouping", "value": "Grouped by sales order" if filters.get("group_by_so") else "Detailed rows"},
	]


def _collections_status_filters(filter_overrides: dict[str, object] | None = None) -> dict[str, object]:
	today = getdate(nowdate())
	filters = {
		"company": _default_company(),
		"from_date": str(add_months(today, -1)),
		"to_date": str(today),
		"collection_view": "open_invoices",
	}
	overrides = filter_overrides or {}
	allowed_views = {option["value"] for option in _collections_status_view_options()}
	collection_view = str(overrides.get("collection_view") or filters["collection_view"])
	if collection_view in allowed_views:
		filters["collection_view"] = collection_view
	for key in ("from_date", "to_date"):
		value = overrides.get(key)
		if not value:
			continue
		try:
			filters[key] = str(getdate(value))
		except Exception:
			pass
	try:
		if getdate(filters["from_date"]) > getdate(filters["to_date"]):
			filters["from_date"], filters["to_date"] = (
				filters["to_date"],
				filters["from_date"],
			)
	except Exception:
		pass
	return filters


def _collections_status_controls(filters: dict[str, object], scope: dict[str, object]) -> dict[str, object]:
	return {
		"appearance": "analytics_compact",
		"meta": [{"label": "Scope", "value": _scope_control_value(scope)}],
		"fields": [
			{
				"key": "collection_view",
				"label": "View",
				"type": "select",
				"value": filters.get("collection_view") or "open_invoices",
				"options": _collections_status_view_options(),
			},
			{
				"key": "from_date",
				"label": "Window start",
				"type": "date",
				"value": filters.get("from_date"),
				"span": 2,
			},
			{
				"key": "to_date",
				"label": "Window end",
				"type": "date",
				"value": filters.get("to_date"),
				"span": 2,
			},
		],
		"submitLabel": "Apply",
		"resetLabel": "Reset",
	}


def _collections_status_view_options() -> list[dict[str, str]]:
	return [
		{"label": "Open invoices", "value": "open_invoices"},
		{"label": "Overdue only", "value": "overdue_only"},
		{"label": "Settled invoices", "value": "settled_invoices"},
		{"label": "All invoices", "value": "all_invoices"},
	]


def _item_wise_sales_history_filters(filter_overrides: dict[str, object] | None = None) -> dict[str, object]:
	today = getdate(nowdate())
	filters = {
		"company": _default_company(),
		"from_date": str(add_months(today, -1)),
		"to_date": str(today),
		"item_group": "",
		"item_code": "",
		"customer": "",
	}
	overrides = filter_overrides or {}
	for key in ("from_date", "to_date"):
		value = overrides.get(key)
		if not value:
			continue
		try:
			filters[key] = str(getdate(value))
		except Exception:
			pass
	for key in ("item_group", "item_code", "customer"):
		value = str(overrides.get(key) or "").strip()
		filters[key] = value
	try:
		if getdate(filters["from_date"]) > getdate(filters["to_date"]):
			filters["from_date"], filters["to_date"] = filters["to_date"], filters["from_date"]
	except Exception:
		pass
	return filters


def _item_wise_sales_history_controls(filters: dict[str, object], scope: dict[str, object]) -> dict[str, object]:
	return {
		"appearance": "analytics_compact",
		"meta": [{"label": "Scope", "value": _scope_control_value(scope)}],
		"fields": [
			{
				"key": "item_group",
				"label": "Item group",
				"type": "select",
				"value": filters.get("item_group") or "",
				"options": _item_group_options(),
				"row": 1,
			},
			{
				"key": "item_code",
				"label": "Item code",
				"type": "text",
				"value": filters.get("item_code") or "",
				"row": 1,
			},
			{
				"key": "customer",
				"label": "Customer",
				"type": "text",
				"value": filters.get("customer") or "",
				"row": 1,
			},
			{
				"key": "from_date",
				"label": "Window start",
				"type": "date",
				"value": filters.get("from_date"),
				"row": 2,
			},
			{
				"key": "to_date",
				"label": "Window end",
				"type": "date",
				"value": filters.get("to_date"),
				"row": 2,
			},
		],
		"submitLabel": "Apply",
		"resetLabel": "Reset",
	}


def _item_group_options() -> list[dict[str, str]]:
	options = [{"label": "All groups", "value": ""}]
	try:
		rows = frappe.get_all(
			"Item",
			filters={"disabled": 0},
			fields=["item_group"],
			distinct=True,
			order_by="item_group asc",
			limit_page_length=500,
		)
	except Exception:
		rows = []
	for row in rows:
		name = str(row.get("item_group") or "").strip()
		if name:
			options.append({"label": name, "value": name})
	return options


def _lost_quotations_filters(filter_overrides: dict[str, object] | None = None) -> dict[str, object]:
	filters = {
		"company": _default_company(),
		"timespan": "This Year",
		"group_by": "Lost Reason",
	}
	overrides = filter_overrides or {}
	allowed_timespans = {option["value"] for option in _lost_quotations_timespan_options()}
	allowed_group_by = {option["value"] for option in _lost_quotations_group_by_options()}
	timespan = str(overrides.get("timespan") or filters["timespan"])
	group_by = str(overrides.get("group_by") or filters["group_by"])
	if timespan in allowed_timespans:
		filters["timespan"] = timespan
	if group_by in allowed_group_by:
		filters["group_by"] = group_by
	return filters


def _lost_quotations_controls(filters: dict[str, object], scope: dict[str, object]) -> dict[str, object]:
	return {
		"appearance": "analytics_compact",
		"meta": [{"label": "Scope", "value": _scope_control_value(scope)}],
		"fields": [
			{
				"key": "timespan",
				"label": "Review window",
				"type": "select",
				"value": filters.get("timespan") or "This Year",
				"options": _lost_quotations_timespan_options(),
			},
			{
				"key": "group_by",
				"label": "Group by",
				"type": "select",
				"value": filters.get("group_by") or "Lost Reason",
				"options": _lost_quotations_group_by_options(),
			},
		],
		"submitLabel": "Apply",
		"resetLabel": "Reset",
	}


def _lost_quotations_timespan_options() -> list[dict[str, str]]:
	return [
		{"label": "Last Week", "value": "Last Week"},
		{"label": "Last Month", "value": "Last Month"},
		{"label": "Last Quarter", "value": "Last Quarter"},
		{"label": "Last 6 months", "value": "Last 6 months"},
		{"label": "Last Year", "value": "Last Year"},
		{"label": "This Week", "value": "This Week"},
		{"label": "This Month", "value": "This Month"},
		{"label": "This Quarter", "value": "This Quarter"},
		{"label": "This Year", "value": "This Year"},
	]


def _lost_quotations_group_by_options() -> list[dict[str, str]]:
	return [
		{"label": "Lost Reason", "value": "Lost Reason"},
		{"label": "Competitor", "value": "Competitor"},
	]


def _sales_order_trends_filters() -> dict[str, object]:
	fiscal_window = _current_fiscal_year_window()
	return {
		"period": "Monthly",
		"based_on": "Customer",
		"group_by": "",
		"fiscal_year": fiscal_window["name"],
		"company": _default_company(),
		"include_closed_orders": 0,
	}


def _collections_status_filter_chips(filters: dict[str, object], scope: dict[str, object]) -> list[dict[str, object]]:
	return _scope_filter_chip(scope) + [
		{"label": "Company", "value": filters.get("company")},
		{"label": "Window", "value": _date_range_label(filters.get("from_date"), filters.get("to_date"))},
	]


def _item_wise_sales_history_filter_chips(filters: dict[str, object], scope: dict[str, object]) -> list[dict[str, object]]:
	return _scope_filter_chip(scope) + [
		{"label": "Company", "value": filters.get("company")},
		{"label": "Window", "value": _date_range_label(filters.get("from_date"), filters.get("to_date"))},
	]


def _prepare_item_wise_sales_history_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
	grouped: dict[tuple[str, str, str], dict[str, object]] = {}
	for row in rows:
		row_copy = dict(row)
		item_code = str(row_copy.get("item_code") or "").strip()
		customer = str(row_copy.get("customer") or "").strip()
		transaction_date = _coerce_report_date(row_copy.get("transaction_date"))
		if not item_code or not customer or not transaction_date:
			continue
		month_key = transaction_date.strftime("%Y-%m")
		group_key = (item_code, customer, month_key)
		group = grouped.get(group_key)
		if not group:
			group = dict(row_copy)
			group["transaction_month"] = transaction_date.strftime("%b-%y")
			group["_month_sort"] = transaction_date.strftime("%Y-%m")
			group["orders_count"] = 0
			group["_sales_orders"] = set()
			group["quantity"] = 0.0
			group["amount"] = 0.0
			group["billed_amount"] = 0.0
			grouped[group_key] = group
		sales_order = str(row_copy.get("sales_order") or "").strip()
		if sales_order and sales_order not in group["_sales_orders"]:
			group["_sales_orders"].add(sales_order)
			group["orders_count"] = int(group.get("orders_count") or 0) + 1
		group["quantity"] = flt(group.get("quantity")) + flt(row_copy.get("quantity"))
		group["amount"] = flt(group.get("amount")) + flt(row_copy.get("amount"))
		group["billed_amount"] = flt(group.get("billed_amount")) + flt(row_copy.get("billed_amount"))
	prepared = list(grouped.values())
	for row in prepared:
		row.pop("_sales_orders", None)
	prepared.sort(
		key=lambda row: (
			str(row.get("_month_sort") or ""),
			flt(row.get("amount")),
			str(row.get("item_code") or ""),
			str(row.get("customer") or ""),
		),
		reverse=True,
	)
	return prepared


def _item_wise_sales_history_columns() -> list[dict[str, object]]:
	return [
		{"key": "item_code", "fieldname": "item_code", "label": "Item code", "fieldtype": "Link", "options": "Item", "align": "", "nowrap": 1},
		{"key": "item_name", "fieldname": "item_name", "label": "Item", "fieldtype": "Data", "options": None, "align": ""},
		{"key": "customer", "fieldname": "customer", "label": "Customer", "fieldtype": "Link", "options": "Customer", "align": ""},
		{"key": "transaction_month", "fieldname": "transaction_month", "label": "Month", "fieldtype": "Data", "options": None, "align": "", "nowrap": 1},
		{"key": "orders_count", "fieldname": "orders_count", "label": "Orders", "fieldtype": "Int", "options": None, "align": "right", "nowrap": 1},
		{"key": "quantity", "fieldname": "quantity", "label": "Qty", "fieldtype": "Float", "options": None, "align": "right"},
		{"key": "amount", "fieldname": "amount", "label": "Sales", "fieldtype": "Currency", "options": "currency", "align": "right", "compact_currency": 1},
		{"key": "billed_amount", "fieldname": "billed_amount", "label": "Billed", "fieldtype": "Currency", "options": "currency", "align": "right", "compact_currency": 1},
	]


def _item_wise_sales_history_empty_detail(filters: dict[str, object]) -> str:
	if filters.get("item_code"):
		return f"No visible sales history is returned for item '{filters.get('item_code')}' inside the selected window."
	if filters.get("customer"):
		return f"No visible sales history is returned for customer '{filters.get('customer')}' inside the selected window."
	if filters.get("item_group"):
		return f"No visible sales history is returned for item group '{filters.get('item_group')}' inside the selected window."
	return "The selected operating window does not return any visible item sales rows inside this ERP scope."


def _sales_order_trends_filter_chips(filters: dict[str, object], scope: dict[str, object]) -> list[dict[str, object]]:
	return _scope_filter_chip(scope) + [
		{"label": "Company", "value": filters.get("company")},
		{"label": "Fiscal year", "value": filters.get("fiscal_year")},
		{"label": "Based on", "value": filters.get("based_on")},
		{"label": "Period", "value": filters.get("period")},
	]


def _fiscal_year_options() -> list[dict[str, str]]:
	fiscal_years = frappe.get_all(
		"Fiscal Year",
		filters={"disabled": 0},
		fields=["name"],
		order_by="year_start_date desc",
	)
	options = [{"label": str(entry["name"]), "value": str(entry["name"])} for entry in fiscal_years if entry.get("name")]
	if not options:
		current = _current_fiscal_year_window()["name"]
		options = [{"label": str(current), "value": str(current)}]
	return options


def _scope_filter_chip(scope: dict[str, object]) -> list[dict[str, object]]:
	branch_name = scope.get("branch_name")
	scope_mode = scope.get("scope_mode")
	label_map = {
		"team_review_scope": "Team scope",
		"assigned_account_scope": "Assigned scope",
		"showroom_scope": "Showroom scope",
		"executive_review_scope": "Executive scope",
		"branch_and_owner_filtered": "Branch scope",
	}
	label = label_map.get(scope_mode, "Permission scope")
	value = branch_name or label
	if branch_name and label != branch_name:
		value = f"{label} · {branch_name}"
	return [{"label": "Scope", "value": value}]


def _normalize_columns(columns: list[object]) -> list[dict[str, object]]:
	normalized: list[dict[str, object]] = []
	for index, column in enumerate(columns):
		if isinstance(column, str):
			fieldname = frappe.scrub(column)
			label = column
			fieldtype = "Data"
			options = None
		else:
			fieldname = column.get("fieldname") or frappe.scrub(column.get("label") or f"column_{index}")
			label = column.get("label") or fieldname.replace("_", " ").title()
			fieldtype = column.get("fieldtype") or "Data"
			options = column.get("options")
		normalized.append(
			{
				"key": fieldname,
				"fieldname": fieldname,
				"label": label,
				"fieldtype": fieldtype,
				"options": options,
				"align": "right" if fieldtype in {"Currency", "Float", "Int", "Percent"} else "",
			}
		)
	return normalized


def _normalize_rows(rows: list[object], columns: list[dict[str, object]]) -> list[dict[str, object]]:
	field_order = [column["fieldname"] for column in columns]
	normalized: list[dict[str, object]] = []
	for row in rows:
		if isinstance(row, dict):
			normalized.append(row)
			continue
		if isinstance(row, (list, tuple)):
			normalized.append({field_order[index]: value for index, value in enumerate(row) if index < len(field_order)})
	return normalized


def _build_rows(
	rows: list[dict[str, object]],
	columns: list[dict[str, object]],
	company_currency: str | None,
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
	normalized_rows: list[dict[str, object]] = []
	action_targets: dict[str, dict[str, object]] = {}
	for row_index, row in enumerate(rows):
		cells: dict[str, dict[str, object]] = {}
		for column in columns:
			fieldname = column["fieldname"]
			raw_value = row.get(fieldname)
			cell: dict[str, object] = {
				"value": _format_value(raw_value, column, row, company_currency),
			}
			action = _cell_action(column, raw_value)
			if action:
				action_key = f"cell:{row_index}:{fieldname}"
				cell["actionKey"] = action_key
				action_targets[action_key] = action
			cells[column["key"]] = cell
		normalized_rows.append({"key": str(row_index), "cells": cells})
	return normalized_rows, action_targets


def _cell_action(column: dict[str, object], raw_value: object) -> dict[str, object] | None:
	if raw_value in (None, "", "--"):
		return None
	if column.get("fieldtype") != "Link":
		return None
	doctype = column.get("options")
	if not doctype or not service._doctype_exists(str(doctype)):
		return None
	if not _link_target_exists(str(doctype), str(raw_value)):
		return None
	return {"kind": "form", "doctype": str(doctype), "name": str(raw_value)}


def _link_target_exists(doctype: str, name: str) -> bool:
	try:
		return bool(frappe.db.exists(str(doctype), str(name)))
	except Exception:
		return False


def _format_value(
	raw_value: object,
	column: dict[str, object],
	row: dict[str, object],
	company_currency: str | None,
) -> str:
	if raw_value in (None, ""):
		return "--"

	fieldtype = column.get("fieldtype") or "Data"
	options = column.get("options")

	if fieldtype == "Date":
		return formatdate(raw_value)

	if fieldtype == "Currency":
		currency = row.get(options) if isinstance(options, str) and options in row else company_currency
		if column.get("compact_currency"):
			return _money_number(raw_value, 0)
		return fmt_money(flt(raw_value), currency=currency)

	try:
		return frappe.format_value(raw_value, {"fieldtype": fieldtype, "options": options}, row)
	except Exception:
		return str(raw_value)


def _results_meta(total_rows: int) -> str:
	if total_rows <= ROW_LIMIT:
		return f"{total_rows} visible"
	return f"Showing first {ROW_LIMIT} of {total_rows} visible rows"


def _ready_state() -> dict[str, object]:
	return {"kind": "ready", "title": "Ready"}


def _date_range_label(from_date: object, to_date: object) -> str:
	if not from_date or not to_date:
		return "--"
	return f"{formatdate(from_date)} to {formatdate(to_date)}"


def _sales_analytics_metrics(
	rows: list[dict[str, object]],
	payload: dict[str, object],
	filters: dict[str, object],
	company_currency: str | None,
) -> dict[str, object]:
	entity_labels = _sales_analytics_entity_labels(filters.get("tree_type"))
	total_value = sum(flt(row.get("_row_total")) for row in rows)
	labels, values = _chart_series(payload.get("chart"))
	peak_label, peak_value = _peak_point(labels, values)
	top_label, top_value = _sales_analytics_top_entity(rows)
	top_share = ((top_value / total_value) * 100.0) if total_value else 0.0
	return {
		"appearance": "analytics_compact",
		"items": [
			{
				"label": "Total billed value",
				"value": _money(total_value, company_currency),
				"meta": _date_range_label(filters.get("from_date"), filters.get("to_date")),
				"tone": "teal",
			},
			{
				"label": f"Top {entity_labels['singular'].lower()}",
				"value": top_label or "--",
				"meta": (f"{_money(top_value, company_currency)} / {top_share:.0f}% of visible value" if top_label else "No visible concentration yet"),
				"tone": "indigo",
			},
			{
				"label": "Peak period",
				"value": peak_label or "--",
				"meta": _money(peak_value, company_currency) if peak_label else "No active period yet",
				"tone": "amber",
			},
		],
	}

def _sales_order_analysis_metrics(
	rows: list[dict[str, object]],
	payload: dict[str, object],
	filters: dict[str, object],
	company_currency: str | None,
) -> dict[str, object]:
	total_order_value = sum(flt(row.get("order_value")) for row in rows)
	pending_bill_value = sum(flt(row.get("pending_value")) for row in rows)
	return {
		"appearance": "analytics_compact",
		"items": [
			{
				"label": "Visible orders",
				"value": str(len(rows)),
				"meta": _date_range_label(filters.get("from_date"), filters.get("to_date")),
				"tone": "teal",
			},
			{
				"label": "Order value",
				"value": _money(total_order_value, company_currency),
				"meta": "Visible submitted order value",
				"tone": "indigo",
			},
			{
				"label": "Pending bill",
				"value": _money(pending_bill_value, company_currency),
				"meta": "Visible order value still waiting to bill",
				"tone": "amber",
			},
		],
	}


def _sales_order_analysis_secondary(
	rows: list[dict[str, object]],
	filters: dict[str, object],
	company_currency: str | None,
) -> dict[str, object] | None:
	if not rows:
		return None
	open_count = sum(1 for row in rows if row.get("_open_execution"))
	overdue_count = sum(1 for row in rows if row.get("_overdue_delivery"))
	qty_to_deliver = sum(flt(row.get("qty_to_deliver")) for row in rows)
	return {
		"title": "Execution posture",
		"subtitle": "Open execution, overdue delivery, and remaining delivery load inside the selected window.",
		"items": [
			{
				"label": "Open execution",
				"value": str(open_count),
				"meta": "Orders still carrying delivery or billing work",
			},
			{
				"label": "Overdue delivery",
				"value": str(overdue_count),
				"meta": "Open orders already past planned delivery",
			},
			{
				"label": "Qty to deliver",
				"value": _number(qty_to_deliver),
				"meta": "Remaining delivery quantity across visible orders",
			},
		],
	}



def _quotation_trends_metrics(
	rows: list[dict[str, object]],
	payload: dict[str, object],
	filters: dict[str, object],
	company_currency: str | None,
) -> dict[str, object]:
	entity_labels = _sales_analytics_entity_labels(filters.get("based_on"))
	total_amt = sum(flt(row.get("_total_amount")) for row in rows)
	top_entity = "--"
	top_entity_meta = "No visible quoted movement"
	if rows:
		top_row = rows[0]
		top_entity = str(top_row.get("_entity") or "--")
		top_entity_value = flt(top_row.get("_total_amount"))
		share = (top_entity_value / total_amt * 100.0) if total_amt else 0.0
		top_entity_meta = f"{_money(top_entity_value, company_currency)} / {round(share)}% of visible quoted value"
	labels, values = _chart_series(payload.get("chart"))
	peak_label, peak_value = _peak_point(labels, values)
	return {
		"appearance": "analytics_compact",
		"items": [
			{
				"label": "Quoted value",
				"value": _money(total_amt, company_currency),
				"meta": f"{filters.get('fiscal_year')} visible quotation value",
				"tone": "teal",
			},
			{
				"label": f"Top {entity_labels['singular'].lower()}",
				"value": top_entity,
				"meta": top_entity_meta,
				"tone": "indigo",
			},
			{
				"label": "Peak period",
				"value": peak_label or "--",
				"meta": _money(peak_value, company_currency) if peak_label else "No active period yet",
				"tone": "amber",
			},
		],
	}


def _collections_status_metrics(
	rows: list[dict[str, object]],
	filters: dict[str, object],
	company_currency: str | None,
) -> dict[str, object]:
	outstanding_value = sum(flt(row.get("outstanding_value")) for row in rows)
	overdue_value = sum(flt(row.get("outstanding_value")) for row in rows if row.get("_is_overdue"))
	return {
		"appearance": "analytics_compact",
		"items": [
			{
				"label": "Visible invoices",
				"value": str(len(rows)),
				"meta": _date_range_label(filters.get("from_date"), filters.get("to_date")),
				"tone": "teal",
			},
			{
				"label": "Outstanding value",
				"value": _money(outstanding_value, company_currency),
				"meta": "Visible receivable value still waiting to settle",
				"tone": "indigo",
			},
			{
				"label": "Overdue value",
				"value": _money(overdue_value, company_currency),
				"meta": "Visible receivable value already past due date",
				"tone": "amber",
			},
		],
	}


def _collections_status_secondary(
	rows: list[dict[str, object]],
	filters: dict[str, object],
	company_currency: str | None,
) -> dict[str, object] | None:
	if not rows:
		return None
	open_invoices = sum(1 for row in rows if row.get("_is_open"))
	overdue_invoices = sum(1 for row in rows if row.get("_is_overdue"))
	collected_value = sum(flt(row.get("paid_value")) for row in rows)
	return {
		"title": "Settlement posture",
		"subtitle": "Open invoices, overdue exposure, and realized collections inside the selected review window.",
		"items": [
			{
				"label": "Open invoices",
				"value": str(open_invoices),
				"meta": "Invoices still waiting for full settlement",
			},
			{
				"label": "Overdue invoices",
				"value": str(overdue_invoices),
				"meta": "Invoices already beyond due date",
			},
			{
				"label": "Collected value",
				"value": _money(collected_value, company_currency),
				"meta": "Already realized across visible invoice settlement",
			},
		],
	}


def _item_wise_sales_history_metrics(
	rows: list[dict[str, object]],
	payload: dict[str, object],
	filters: dict[str, object],
	company_currency: str | None,
) -> dict[str, object]:
	top_item_label, top_item_value = _item_wise_sales_history_top_item(rows)
	total_item_value = _sum_field(rows, "amount")
	top_item_meta = "No visible item concentration yet"
	if top_item_label:
		share = (top_item_value / total_item_value * 100.0) if total_item_value else 0.0
		top_item_meta = f"{_money(top_item_value, company_currency)} / {round(share)}% of visible sales value"
	return {
		"appearance": "analytics_compact",
		"items": [
			{
				"label": "Visible summaries",
				"value": str(len(rows)),
				"meta": _date_range_label(filters.get("from_date"), filters.get("to_date")),
				"tone": "teal",
			},
			{
				"label": "Sales value",
				"value": _money(total_item_value, company_currency),
				"meta": "Visible item sales value",
				"tone": "indigo",
			},
			{
				"label": "Top item",
				"value": top_item_label or "--",
				"meta": top_item_meta,
				"tone": "amber",
			},
		],
	}


def _item_wise_sales_history_secondary(
	rows: list[dict[str, object]],
	chart: dict[str, object] | None,
	filters: dict[str, object],
	company_currency: str | None,
) -> dict[str, object] | None:
	labels, values = _chart_series(chart)
	if not rows and not labels:
		return None
	visible_items = len({str(row.get("item_code") or "").strip() for row in rows if str(row.get("item_code") or "").strip()})
	total_billed = _sum_field(rows, "billed_amount")
	top_customer_label, top_customer_value = _item_wise_sales_history_top_customer(rows)
	total_value = _sum_field(rows, "amount")
	top_customer_meta = "No visible customer concentration yet"
	if top_customer_label:
		share = (top_customer_value / total_value * 100.0) if total_value else 0.0
		top_customer_meta = f"{_money(top_customer_value, company_currency)} / {round(share)}% of visible sales value"
	return {
		"appearance": "analytics_trend_compact",
		"title": "Item concentration",
		"subtitle": "Top item sales value across the selected operating window.",
		"chart": _item_wise_sales_history_chart(chart, company_currency),
		"items": [
			{
				"label": "Visible items",
				"value": str(visible_items),
				"meta": "Distinct items represented in visible rows",
			},
			{
				"label": "Billed value",
				"value": _money(total_billed, company_currency),
				"meta": "Already billed against visible sales lines",
			},
			{
				"label": "Top customer",
				"value": top_customer_label or "--",
				"meta": top_customer_meta,
			},
		],
	}


def _item_wise_sales_history_chart(chart: dict[str, object] | None, company_currency: str | None) -> dict[str, object] | None:
	labels, values = _chart_series(chart)
	if not labels:
		return None
	peak_label, _ = _peak_point(labels, values)
	peak_index = labels.index(peak_label) if peak_label in labels else -1
	max_value = max([flt(value) for value in values], default=0.0)
	points = []
	for index, label in enumerate(labels):
		value = flt(values[index]) if index < len(values) else 0.0
		points.append({
			"label": _compact_chart_label(label),
			"value": value,
			"formatted": _money(value, company_currency),
			"ratio": (value / max_value) if max_value else 0.0,
			"highlighted": index == peak_index,
		})
	return {
		"kind": "period_bar_strip",
		"points": points[:15],
	}


def _compact_chart_label(label: object, limit: int = 14) -> str:
	text = str(label or "").strip()
	if not text:
		return "--"
	if len(text) <= limit:
		return text
	return text[: max(limit - 1, 1)].rstrip(" -_/") + "…"


def _item_wise_sales_history_top_item(rows: list[dict[str, object]]) -> tuple[str | None, float]:
	item_totals: dict[str, float] = {}
	for row in rows:
		label = str(row.get("item_name") or row.get("item_code") or "").strip()
		if not label:
			continue
		item_totals[label] = flt(item_totals.get(label)) + flt(row.get("amount"))
	if not item_totals:
		return None, 0.0
	top_label = max(item_totals, key=lambda key: flt(item_totals[key]))
	return top_label, flt(item_totals[top_label])


def _item_wise_sales_history_top_customer(rows: list[dict[str, object]]) -> tuple[str | None, float]:
	customer_totals: dict[str, float] = {}
	for row in rows:
		label = str(row.get("customer") or row.get("customer_name") or "").strip()
		if not label:
			continue
		customer_totals[label] = flt(customer_totals.get(label)) + flt(row.get("amount"))
	if not customer_totals:
		return None, 0.0
	top_label = max(customer_totals, key=lambda key: flt(customer_totals[key]))
	return top_label, flt(customer_totals[top_label])


def _lost_quotations_metrics(
	rows: list[dict[str, object]],
	payload: dict[str, object],
	filters: dict[str, object],
	company_currency: str | None,
) -> dict[str, object]:
	top_group_label = str(filters.get("group_by") or "Top group")
	top_group_value = "--"
	top_group_meta = "No visible loss pattern"
	total_lost_value = _sum_field(rows, "lost_value")
	if rows:
		first_row = rows[0]
		top_group_value = _lost_group_value(first_row) or "--"
		top_value = flt(first_row.get("lost_value"))
		share = (top_value / total_lost_value * 100.0) if total_lost_value else 0.0
		top_group_meta = f"{_money(top_value, company_currency)} / {round(share)}% of visible lost value"
	return {
		"appearance": "analytics_compact",
		"items": [
			{
				"label": "Lost quotations",
				"value": _number(_sum_field(rows, "lost_quotations")),
				"meta": "Visible lost quotation count",
				"tone": "teal",
			},
			{
				"label": "Lost value",
				"value": _money(total_lost_value, company_currency),
				"meta": "Visible commercial value lost",
				"tone": "indigo",
			},
			{
				"label": f"Top {top_group_label.lower()}",
				"value": top_group_value,
				"meta": top_group_meta,
				"tone": "amber",
			},
		],
	}


def _sales_order_trends_metrics(
	rows: list[dict[str, object]],
	payload: dict[str, object],
	filters: dict[str, object],
	company_currency: str | None,
) -> list[dict[str, object]]:
	total_qty = _sum_field(rows, "total(qty)")
	total_amt = _sum_field(rows, "total(amt)")
	labels, values = _chart_series(payload.get("chart"))
	peak_label, peak_value = _peak_point(labels, values)
	return [
		{"label": "Visible parties", "value": str(len(rows)), "meta": "Customers in the current fiscal trend view"},
		{"label": "Ordered qty", "value": _number(total_qty), "meta": "Total visible ordered quantity"},
		{"label": "Ordered value", "value": _money(total_amt, company_currency), "meta": "Total visible order amount"},
		{"label": "Peak period", "value": peak_label or "--", "meta": _money(peak_value, company_currency) if peak_label else "No active period yet"},
	]


def _sales_analytics_secondary(
	chart: dict[str, object] | None,
	filters: dict[str, object],
	company_currency: str | None,
) -> dict[str, object] | None:
	return _period_bar_secondary(
		chart,
		company_currency,
		f"{filters.get('range') or 'Monthly'} visible billed sales value across the selected window.",
	)

def _quotation_trends_secondary(
	chart: dict[str, object] | None,
	filters: dict[str, object],
	company_currency: str | None,
) -> dict[str, object] | None:
	return _period_bar_secondary(
		chart,
		company_currency,
		f"{filters.get('period') or 'Monthly'} visible quoted amount across the selected fiscal year.",
	)


def _sales_order_trends_secondary(
	chart: dict[str, object] | None,
	filters: dict[str, object],
	company_currency: str | None,
) -> dict[str, object] | None:
	return _line_chart_secondary(chart, company_currency, "Order value across the selected fiscal year")


def _period_bar_secondary(
	chart: dict[str, object] | None,
	company_currency: str | None,
	subtitle: str,
) -> dict[str, object] | None:
	labels, values = _chart_series(chart)
	if not labels:
		return None
	peak_label, _ = _peak_point(labels, values)
	peak_index = labels.index(peak_label) if peak_label in labels else -1
	max_value = max([flt(value) for value in values], default=0.0)
	points = []
	for index, label in enumerate(labels):
		value = flt(values[index]) if index < len(values) else 0.0
		points.append({
			"label": str(label).replace("(Amt)", "").strip(),
			"value": value,
			"formatted": _money(value, company_currency),
			"ratio": (value / max_value) if max_value else 0.0,
			"highlighted": index == peak_index,
		})
	return {
		"appearance": "analytics_trend_compact",
		"title": "Period trend",
		"subtitle": subtitle,
		"chart": {
			"kind": "period_bar_strip",
			"points": points,
			"summary": "",
		},
	}


def _line_chart_secondary(
	chart: dict[str, object] | None,
	company_currency: str | None,
	subtitle: str,
) -> dict[str, object] | None:
	labels, values = _chart_series(chart)
	if not labels:
		return None
	peak_label, peak_value = _peak_point(labels, values)
	latest_label, latest_value = _latest_active_point(labels, values)
	active_periods = len([value for value in values if flt(value) > 0])
	return {
		"title": "Trend window",
		"subtitle": subtitle,
		"items": [
			{"label": "Peak period", "value": peak_label or "--", "meta": _money(peak_value, company_currency) if peak_label else "No active period"},
			{"label": "Latest active", "value": latest_label or "--", "meta": _money(latest_value, company_currency) if latest_label else "No active period"},
			{"label": "Active periods", "value": str(active_periods), "meta": "Periods carrying visible value"},
		],
	}


def _chart_series(chart: dict[str, object] | None) -> tuple[list[str], list[float]]:
	data = (chart or {}).get("data") or {}
	labels = list(data.get("labels") or [])
	datasets = list(data.get("datasets") or [])
	if not labels or not datasets:
		return [], []
	values = [flt(value) for value in (datasets[0].get("values") or [])]
	return labels, values


def _peak_point(labels: list[str], values: list[float]) -> tuple[str | None, float]:
	if not labels or not values:
		return None, 0.0
	peak_index = max(range(len(values)), key=lambda index: flt(values[index]))
	if flt(values[peak_index]) <= 0:
		return None, 0.0
	return labels[peak_index], values[peak_index]


def _latest_active_point(labels: list[str], values: list[float]) -> tuple[str | None, float]:
	for index in range(len(values) - 1, -1, -1):
		if flt(values[index]) > 0:
			return labels[index], values[index]
	return None, 0.0


def _sum_field(rows: list[dict[str, object]], fieldname: str) -> float:
	return sum(flt(row.get(fieldname)) for row in rows if row.get(fieldname) not in (None, ""))


def _quotation_trends_row_entity(row: dict[str, object]) -> str:
	for fieldname, value in row.items():
		key = str(fieldname).lower()
		if key in {"currency", "party_name", "_entity", "_total_amount"}:
			continue
		if _quotation_trends_is_quantity_field(key) or _quotation_trends_is_amount_field(key):
			continue
		if value not in (None, "", "--"):
			return str(value)
	return "--"


def _quotation_trends_is_total_row(row: dict[str, object]) -> bool:
	entity = str(row.get("_entity") or _quotation_trends_row_entity(row) or "").strip().strip("'").lower()
	return entity == "total"


def _quotation_trends_total_amount(row: dict[str, object]) -> float:
	if row.get("total(amt)") not in (None, ""):
		return flt(row.get("total(amt)"))
	total = 0.0
	for fieldname, value in row.items():
		if _quotation_trends_is_period_amount_field(str(fieldname).lower()) and value not in (None, ""):
			total += flt(value)
	return total


def _quotation_trends_field_values_match(rows: list[dict[str, object]], left: str, right: str) -> bool:
	if not rows:
		return False
	for row in rows:
		if row.get(left) in (None, "", "--") and row.get(right) in (None, "", "--"):
			continue
		if str(row.get(left) or "").strip() != str(row.get(right) or "").strip():
			return False
	return True


def _quotation_trends_is_quantity_field(fieldname: str) -> bool:
	key = str(fieldname).lower()
	return "(qty)" in key or key == "total(qty)"


def _quotation_trends_is_amount_field(fieldname: str) -> bool:
	key = str(fieldname).lower()
	return "(amt)" in key or key == "total(amt)"


def _quotation_trends_period_label(label: object) -> str:
	text = str(label or "").strip()
	if not text:
		return "--"
	return text.replace(" (Amt)", "").replace("(Amt)", "").strip()


def _quotation_trends_is_period_amount_field(fieldname: str) -> bool:
	key = str(fieldname).lower()
	return "(amt)" in key and key != "total(amt)"


def _lost_group_value(row: dict[str, object]) -> str | None:
	for fieldname in ("lost_reason", "competitor"):
		value = row.get(fieldname)
		if value not in (None, "", "--"):
			return str(value)
	for fieldname, value in row.items():
		if fieldname in {"lost_quotations", "lost_quotations_%", "lost_value", "lost_value_%"}:
			continue
		if value not in (None, "", "--"):
			return str(value)
	return None


def _lost_quotation_bucket_target(filters: dict[str, object], bucket_value: str) -> dict[str, object] | None:
	names = _lost_quotation_names_for_bucket(filters, bucket_value)
	if not names:
		return None
	return {
		"kind": "list",
		"doctype": "Quotation",
		"filters": {
			"name": ["in", names],
			"status": "Lost",
			"company": filters.get("company"),
		},
	}


def _lost_quotation_names_for_bucket(filters: dict[str, object], bucket_value: str) -> list[str]:
	group_by = str(filters.get("group_by") or "Lost Reason")
	if group_by == "Lost Reason":
		fieldname = "lost_reason"
		dimension = frappe.qb.DocType("Quotation Lost Reason Detail")
	elif group_by == "Competitor":
		fieldname = "competitor"
		dimension = frappe.qb.DocType("Competitor Detail")
	else:
		return []
	from_date, to_date = get_timespan_date_range(str(filters.get("timespan") or "This Year").lower())
	q = frappe.qb.DocType("Quotation")
	query = (
		frappe.qb.from_(q)
		.left_join(dimension)
		.on(dimension.parent == q.name)
		.select(q.name)
		.where(
			(q.status == "Lost")
			& (q.docstatus == 1)
			& (q.transaction_date >= from_date)
			& (q.transaction_date <= to_date)
			& (q.company == filters.get("company"))
		)
		.distinct()
	)
	if bucket_value == "Not Specified":
		query = query.where((dimension[fieldname].isnull()) | (dimension[fieldname] == ""))
	else:
		query = query.where(dimension[fieldname] == bucket_value)
	return [str(row[0]) for row in query.run() if row and row[0]]


def _money(value: object, currency: str | None) -> str:
	return fmt_money(flt(value), currency=currency)


def _money_number(value: object, precision: int = 0) -> str:
	amount = flt(value)
	if precision <= 0:
		return f"{amount:,.0f}"
	return f"{amount:,.{precision}f}"


def _number(value: object) -> str:
	try:
		return frappe.format_value(value, {"fieldtype": "Float"})
	except Exception:
		return str(value)
