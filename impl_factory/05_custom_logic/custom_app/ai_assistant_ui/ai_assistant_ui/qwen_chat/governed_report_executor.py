from __future__ import annotations

import datetime as dt
import json
import time
from typing import Any, Dict

from ai_assistant_ui.qwen_chat.metadata import get_report_spec

try:
	from ai_assistant_ui.qwen_chat.fac_client import fac_generate_report
except Exception:  # pragma: no cover
	fac_generate_report = None

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None


def _normalize_output_obj(raw_result: Any) -> Dict[str, Any]:
	if isinstance(raw_result, dict):
		if isinstance(raw_result.get("result"), dict):
			return json.loads(json.dumps(raw_result))
		if any(key in raw_result for key in ("report_name", "data", "columns", "message", "filters_applied")):
			return {
				"success": True,
				"result": json.loads(json.dumps(raw_result)),
			}
	return {
		"success": False,
		"result": {
			"success": False,
			"message": "Governed direct report execution returned an invalid payload.",
		},
	}


def _result_row_count(output_obj: Dict[str, Any]) -> int:
	result_obj = output_obj.get("result") if isinstance(output_obj.get("result"), dict) else {}
	data = result_obj.get("data")
	if isinstance(data, list):
		return len(data)
	return -1


def _default_limit(default_limit: int) -> int:
	return max(1, min(100, int(default_limit or 10)))


def _direct_query_columns(fields: list[str], *, doctype: str = "") -> list[dict[str, Any]]:
	document_label = str(doctype or "").strip() or "Document"
	label_map = {
		"name": document_label,
		"posting_date": "Posting Date",
		"transaction_date": "Transaction Date",
		"delivery_date": "Delivery Date",
		"customer": "Customer",
		"grand_total": "Grand Total",
		"outstanding_amount": "Outstanding Amount",
		"total_qty": "Quantity",
		"per_delivered": "Delivered %",
		"per_billed": "Billed %",
		"status": "Status",
		"docstatus": "Docstatus",
	}
	out = []
	for fieldname in fields:
		name = str(fieldname or "").strip()
		if not name:
			continue
		out.append(
			{
				"fieldname": name,
				"label": label_map.get(name, name.replace("_", " ").title()),
			}
		)
	return out


def _json_safe_value(value: Any) -> Any:
	if isinstance(value, (dt.date, dt.datetime, dt.time)):
		return value.isoformat()
	return value


def _json_safe_row(row: Dict[str, Any]) -> Dict[str, Any]:
	return {
		str(key or "").strip(): _json_safe_value(value)
		for key, value in row.items()
		if str(key or "").strip()
	}


def _direct_query_filterable_fields(report_spec: Dict[str, Any]) -> set[str]:
	query_spec = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
	fields = {
		str(value or "").strip()
		for value in (query_spec.get("fields") or [])
		if str(value or "").strip()
	}
	defaultable_filters = {
		str(item.get("fieldname") or "").strip()
		for item in (report_spec.get("defaultable_filters") or [])
		if isinstance(item, dict) and str(item.get("fieldname") or "").strip()
	}
	required_filters = {
		str(value or "").strip()
		for value in (report_spec.get("required_filters") or [])
		if str(value or "").strip()
	}
	return fields | defaultable_filters | required_filters


def _normalize_direct_query_filter_value(value: Any) -> Any:
	if value is None:
		return None
	if isinstance(value, str):
		clean = value.strip()
		return clean or None
	if isinstance(value, (bool, int, float)):
		return value
	if isinstance(value, (dt.date, dt.datetime, dt.time)):
		return value.isoformat()
	return None


def _execute_direct_query(
	*,
	report_name: str,
	report_spec: Dict[str, Any],
	filters: Dict[str, Any],
	target_limit: int = 0,
) -> Dict[str, Any]:
	query_spec = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
	doctype = str(query_spec.get("doctype") or "").strip()
	fields = [
		str(value or "").strip()
		for value in (query_spec.get("fields") or [])
		if str(value or "").strip()
	]
	if not doctype or not fields:
		return {
			"success": False,
			"result": {
				"success": False,
				"message": f"Direct query configuration is incomplete for `{report_name}`.",
			},
		}
	date_field = str(query_spec.get("date_field") or "").strip()
	order_by = str(query_spec.get("order_by") or "").strip() or "modified desc"
	default_limit = int(query_spec.get("default_limit") or 10)
	limit = _default_limit(target_limit or default_limit)
	applied_filters: Dict[str, Any] = {}
	fixed_filters = query_spec.get("fixed_filters") if isinstance(query_spec.get("fixed_filters"), dict) else {}
	applied_filters.update({str(k): v for k, v in fixed_filters.items() if str(k or "").strip()})
	allowed_filter_fields = _direct_query_filterable_fields(report_spec)
	if "company" in allowed_filter_fields and str(filters.get("company") or "").strip():
		applied_filters["company"] = str(filters.get("company") or "").strip()
	from_date = str(filters.get("from_date") or "").strip()
	to_date = str(filters.get("to_date") or filters.get("report_date") or "").strip()
	if date_field and from_date and to_date:
		applied_filters[date_field] = ["between", [from_date, to_date]]
	elif date_field and to_date:
		applied_filters[date_field] = ["<=", to_date]
	reserved_filter_keys = {
		"from_date",
		"to_date",
		"report_date",
		"period_start_date",
		"period_end_date",
		"limit",
	}
	fixed_filter_keys = {str(key or "").strip() for key in fixed_filters}
	for raw_key, raw_value in (filters or {}).items():
		key = str(raw_key or "").strip()
		if (
			not key
			or key in reserved_filter_keys
			or key == date_field
			or key in fixed_filter_keys
			or key not in allowed_filter_fields
			or key in applied_filters
		):
			continue
		value = _normalize_direct_query_filter_value(raw_value)
		if value is None:
			continue
		applied_filters[key] = value

	started = time.perf_counter()
	try:
		rows = frappe.get_all(
			doctype,
			fields=fields,
			filters=applied_filters,
			order_by=order_by,
			limit_page_length=limit,
		)
		duration_ms = int((time.perf_counter() - started) * 1000)
		return {
			"success": True,
			"result": {
				"success": True,
				"report_name": report_name,
				"columns": _direct_query_columns(fields, doctype=doctype),
				"data": [_json_safe_row(row) for row in rows if isinstance(row, dict)],
				"message": "",
				"filters_applied": {
					**dict(filters or {}),
					"limit": limit,
				},
				"metadata": {
					"grounding_mode": "direct_query",
					"doctype": doctype,
					"duration_ms": duration_ms,
				},
			},
		}
	except Exception as exc:
		return {
			"success": False,
			"result": {
				"success": False,
				"message": str(exc).strip() or f"Direct query execution failed for `{report_name}`.",
			},
		}


def _execute_once(
	*,
	report_name: str,
	filters: Dict[str, Any],
	user: str,
	target_limit: int = 0,
) -> Dict[str, Any]:
	started = time.perf_counter()
	try:
		report_spec = get_report_spec(report_name)
		grounding_mode = str(report_spec.get("grounding_mode") or "report").strip() or "report"
		if grounding_mode == "direct_query":
			raw_result = _execute_direct_query(
				report_name=report_name,
				report_spec=report_spec,
				filters=filters,
				target_limit=target_limit,
			)
		else:
			if fac_generate_report is None:
				raise RuntimeError("FAC report client is unavailable in this runtime.")
			raw_result = fac_generate_report(
				report_name,
				filters=filters,
				fmt="json",
				user=str(user or "").strip() or None,
			)
		output_obj = _normalize_output_obj(raw_result)
		success = bool(output_obj.get("success") is not False)
		result_obj = output_obj.get("result") if isinstance(output_obj.get("result"), dict) else {}
		error = ""
		if not success:
			error = str(result_obj.get("message") or "Governed direct report execution failed.").strip()
	except Exception as exc:
		output_obj = {
			"success": False,
			"result": {
				"success": False,
				"message": str(exc).strip() or type(exc).__name__,
			},
		}
		success = False
		error = str(exc).strip() or type(exc).__name__
	duration_ms = int((time.perf_counter() - started) * 1000)
	return {
		"output_obj": output_obj,
		"success": success,
		"error": error,
		"duration_ms": duration_ms,
		"row_count": _result_row_count(output_obj),
	}


def execute_governed_report(
	*,
	report_name: str,
	filters: Dict[str, Any] | None,
	user: str,
	mode: str = "compiled_read_query",
	target_limit: int = 0,
	request_message: str | None = None,
) -> Dict[str, Any]:
	report = str(report_name or "").strip()
	clean_filters = dict(filters or {})
	report_spec = get_report_spec(report)
	grounding_mode = str(report_spec.get("grounding_mode") or "report").strip() or "report"
	detail_obj = {
		"report_name": report,
		"filters": clean_filters,
		"format": "json",
		"grounding_mode": grounding_mode,
	}
	# Compatibility metadata only. The runtime executor must not treat raw message
	# text as report-routing authority or expose it through tool traces.
	_ = request_message
	max_attempts = 2
	attempts = []
	final_attempt: Dict[str, Any] = {}
	for attempt_index in range(1, max_attempts + 1):
		attempt = _execute_once(
			report_name=report,
			filters=clean_filters,
			user=user,
			target_limit=target_limit,
		)
		attempts.append(
			{
				"attempt": attempt_index,
				"success": bool(attempt.get("success")),
				"duration_ms": int(attempt.get("duration_ms") or 0),
				"row_count": int(attempt.get("row_count") or 0),
				"error": str(attempt.get("error") or "").strip(),
			}
		)
		final_attempt = attempt
		row_count = int(attempt.get("row_count") or 0)
		should_retry = (
			attempt_index < max_attempts
			and (
				not bool(attempt.get("success"))
				or row_count == 0
			)
		)
		if not should_retry:
			break
	output_obj = final_attempt.get("output_obj") if isinstance(final_attempt.get("output_obj"), dict) else {}
	success = bool(final_attempt.get("success"))
	error = str(final_attempt.get("error") or "").strip()
	duration_ms = sum(int(item.get("duration_ms") or 0) for item in attempts)
	row_count = int(final_attempt.get("row_count") or 0)
	preview = json.dumps(output_obj, ensure_ascii=False)[:500]
	tool_trace = [
		{
			"tool": "erp_fac-generate_report",
			"status": "ok" if success else "error",
			"detail": json.dumps(detail_obj, ensure_ascii=False),
			"detail_obj": detail_obj,
			"output_preview": preview,
			"output_obj": output_obj,
			"duration_ms": duration_ms,
			"attempt_count": len(attempts),
			"attempts": attempts,
			"row_count": row_count,
		}
	]
	return {
		"ok": success,
		"answer_text": "",
		"tool_trace": tool_trace,
		"agent_meta": {
			"engine": "deterministic_governed_report_executor",
			"mode": str(mode or "compiled_read_query").strip() or "compiled_read_query",
			"model": "",
			"validation": {"status": "pass" if success else "fail"},
			"attempt_count": len(attempts),
			"row_count": row_count,
		},
		"error": error,
	}
