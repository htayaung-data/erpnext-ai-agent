from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from ai_assistant_ui.qwen_chat.metadata import report_local_followup_adapter, report_supplemental_fields


def _safe_json_loads(value: Any) -> Any:
	if isinstance(value, (dict, list)):
		return value
	text = str(value or "").strip()
	if not text:
		return None
	try:
		return json.loads(text)
	except Exception:
		return None


def _normalize_header(value: Any) -> str:
	return str(value or "").strip()


def _numeric_value(value: Any) -> float:
	if isinstance(value, (int, float)):
		return float(value)
	text = str(value or "").strip().replace(",", "")
	if not text:
		return 0.0
	try:
		return float(text)
	except Exception:
		return 0.0


def _format_million_value(value: float) -> str:
	text = f"{(value / 1_000_000.0):,.2f}".rstrip("0").rstrip(".")
	return text or "0"


def _format_amount(value: float, show_million: bool) -> str:
	if show_million:
		return _format_million_value(value)
	return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}".rstrip("0").rstrip(".")


def _build_markdown_table(headers: List[str], rows: List[Dict[str, Any]]) -> str:
	clean_headers = [_normalize_header(header) for header in headers if _normalize_header(header)]
	if not clean_headers:
		return ""
	lines = [
		"| " + " | ".join(clean_headers) + " |",
		"| " + " | ".join("---" for _ in clean_headers) + " |",
	]
	for row in rows:
		if not isinstance(row, dict):
			continue
		cells = [str(row.get(header) or "").strip() for header in clean_headers]
		lines.append("| " + " | ".join(cells) + " |")
	return "\n".join(lines).strip()


def _report_output_payload(report_tool: Dict[str, Any]) -> Dict[str, Any]:
	output_obj = report_tool.get("output_obj")
	if not isinstance(output_obj, dict):
		output_obj = _safe_json_loads(report_tool.get("output_preview"))
	if not isinstance(output_obj, dict):
		return {}
	result = output_obj.get("result")
	return result if isinstance(result, dict) else {}


def _assistant_table(assistant_payload: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]]]:
	tables = assistant_payload.get("tables")
	first_table = tables[0] if isinstance(tables, list) and tables and isinstance(tables[0], dict) else {}
	headers = first_table.get("headers") if isinstance(first_table.get("headers"), list) else []
	rows = first_table.get("rows") if isinstance(first_table.get("rows"), list) else []
	return (
		[_normalize_header(x) for x in headers if _normalize_header(x)],
		[row for row in rows if isinstance(row, dict)],
	)


def _current_table(assistant_payload: Dict[str, Any], grounded_turn: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]]]:
	assistant_headers, assistant_rows = _assistant_table(assistant_payload or {})
	if assistant_headers and assistant_rows:
		return assistant_headers, assistant_rows
	headers = grounded_turn.get("returned_schema")
	rows = grounded_turn.get("table_rows")
	if isinstance(headers, list) and isinstance(rows, list):
		return (
			[_normalize_header(x) for x in headers if _normalize_header(x)],
			[row for row in rows if isinstance(row, dict)],
		)
	return [], []


def _grounded_table(grounded_turn: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]]]:
	headers = grounded_turn.get("returned_schema")
	rows = grounded_turn.get("table_rows")
	if isinstance(headers, list) and isinstance(rows, list):
		return (
			[_normalize_header(x) for x in headers if _normalize_header(x)],
			[row for row in rows if isinstance(row, dict)],
		)
	return [], []


def _preferred_metric_headers(headers: List[str]) -> List[str]:
	def score(header: str) -> tuple[int, str]:
		value = _normalize_header(header).lower()
		if any(token in value for token in ("outstanding", "amount", "revenue", "sales", "value", "qty", "quantity")):
			return (0, value)
		return (1, value)

	return sorted([_normalize_header(x) for x in headers if _normalize_header(x)], key=score)


def _header_matches_candidate(header: str, candidate: str) -> bool:
	head = _normalize_header(header).lower()
	target = _normalize_header(candidate).lower()
	if not head or not target:
		return False
	return head == target or head.startswith(f"{target} (")


def _find_matching_header(headers: List[str], candidates: List[str]) -> str:
	for candidate in candidates:
		for header in headers:
			if _header_matches_candidate(header, candidate):
				return _normalize_header(header)
	return ""


def _select_sort_metric(headers: List[str], rows: List[Dict[str, Any]]) -> str:
	for header in _preferred_metric_headers(headers[1:]):
		values = [
			_numeric_value(row.get(header))
			for row in rows
			if isinstance(row, dict) and str(row.get(header) or "").strip()
		]
		if values and any(abs(value) > 0 for value in values):
			return header
	return _normalize_header(headers[-1]) if headers else ""


def _extract_report_table(report_name: str, report_tool: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]]]:
	result = _report_output_payload(report_tool)
	data = result.get("data")
	columns = result.get("columns")
	headers: List[str] = []
	rows: List[Dict[str, Any]] = []
	field_order: List[Tuple[str, str]] = []

	if isinstance(columns, list):
		for item in columns:
			if not isinstance(item, dict):
				continue
			label = _normalize_header(item.get("label") or item.get("fieldname"))
			fieldname = _normalize_header(item.get("fieldname"))
			if not label or not fieldname:
				continue
			headers.append(label)
			field_order.append((label, fieldname))

		existing = {fieldname for _, fieldname in field_order}
		for item in report_supplemental_fields(report_name):
			fieldname = _normalize_header(item.get("fieldname"))
			label = _normalize_header(item.get("label"))
			if fieldname and label and fieldname not in existing:
				headers.append(label)
				field_order.append((label, fieldname))
				existing.add(fieldname)

	if isinstance(data, list):
		for entry in data[:100]:
			if not isinstance(entry, dict):
				continue
			row: Dict[str, Any] = {}
			for label, fieldname in field_order:
				row[label] = entry.get(fieldname)
			if row:
				rows.append(row)

	return headers, rows


def extract_grounded_table(report_tool: Dict[str, Any], assistant_payload: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]]]:
	tool_args = report_tool.get("detail_obj")
	if not isinstance(tool_args, dict):
		tool_args = _safe_json_loads(report_tool.get("detail"))
	report_name = _normalize_header((tool_args or {}).get("report_name"))
	assistant_headers, assistant_rows = _assistant_table(assistant_payload)
	report_headers, report_rows = _extract_report_table(report_name, report_tool) if report_name else ([], [])
	if not report_headers:
		return assistant_headers, assistant_rows
	if not assistant_headers or len(report_headers) > len(assistant_headers):
		return report_headers, report_rows
	adapter = report_local_followup_adapter(report_name, "aging_bucket_view")
	bucket_headers = {
		_normalize_header(value)
		for value in (adapter.get("bucket_labels") or [])
		if _normalize_header(value)
	}
	if bucket_headers and bucket_headers.difference(set(assistant_headers)):
		return report_headers, report_rows
	return assistant_headers, assistant_rows


def supports_local_followup_mode(grounded_turn: Dict[str, Any], mode: str, target_dimension: str = "") -> bool:
	mode_name = str(mode or "").strip()
	if mode_name == "sort_or_limit":
		headers = [
			_normalize_header(value)
			for value in (grounded_turn.get("returned_schema") or [])
			if _normalize_header(value)
		]
		rows = grounded_turn.get("table_rows")
		return bool(headers and isinstance(rows, list) and len(headers) >= 2)

	if mode_name == "dimension_breakdown":
		report_name = _normalize_header(grounded_turn.get("source_name"))
		adapter = report_local_followup_adapter(report_name, mode_name)
		if not adapter:
			return False
		headers = {
			_normalize_header(value)
			for value in (grounded_turn.get("returned_schema") or [])
			if _normalize_header(value)
		}
		source_dimension = _normalize_header(adapter.get("source_dimension_header"))
		display_dimension = _normalize_header(adapter.get("display_dimension_label"))
		if target_dimension and _normalize_header(target_dimension) not in {
			display_dimension,
			source_dimension,
		}:
			return False
		return bool(headers and source_dimension and source_dimension in headers)

	if mode_name != "aging_bucket_view":
		return False
	report_name = _normalize_header(grounded_turn.get("source_name"))
	adapter = report_local_followup_adapter(report_name, mode_name)
	if not adapter:
		return False
	headers = {
		_normalize_header(value)
		for value in (grounded_turn.get("returned_schema") or [])
		if _normalize_header(value)
	}
	configured = {
		_normalize_header(value)
		for value in (adapter.get("bucket_labels") or [])
		if _normalize_header(value)
	}
	return len(headers.intersection(configured)) >= 2 or bool(headers and "Future Amount" in configured and adapter.get("total_due_field"))


def render_local_followup(
	mode: str,
	grounded_turn: Dict[str, Any],
	display_preferences: Dict[str, Any],
	target_dimension: str = "",
	assistant_payload: Dict[str, Any] | None = None,
	target_limit: int = 0,
	sort_direction: str = "",
) -> str:
	mode_name = str(mode or "").strip()
	if mode_name == "sort_or_limit":
		report_name = _normalize_header(grounded_turn.get("source_name"))
		adapter = report_local_followup_adapter(report_name, mode_name)
		display_dimension = _normalize_header(adapter.get("display_dimension_label")) if adapter else ""
		source_dimension = _normalize_header(adapter.get("source_dimension_header")) if adapter else ""
		metric_candidates = [
			_normalize_header(value)
			for value in ((adapter.get("metric_headers") or []) if adapter else [])
			if _normalize_header(value)
		]

		grounded_headers, grounded_rows = _grounded_table(grounded_turn)
		headers, rows = grounded_headers, grounded_rows
		if len(headers) < 2 or not rows:
			headers, rows = _current_table(assistant_payload or {}, grounded_turn)
		if len(headers) < 2 or not rows:
			return ""

		dimension_header = _find_matching_header(headers, [source_dimension, display_dimension]) or _normalize_header(headers[0]) or "Dimension"
		metric_header = _find_matching_header(headers, metric_candidates) if metric_candidates else ""
		if not metric_header:
			metric_header = _select_sort_metric(headers, rows)
		if not metric_header:
			return ""
		show_million = bool((display_preferences or {}).get("million"))
		direction = str(sort_direction or "desc").strip().lower() or "desc"

		total_rows: List[Dict[str, Any]] = []
		sortable_rows: List[Dict[str, Any]] = []
		for row in rows:
			if not isinstance(row, dict):
				continue
			dimension_value = str(row.get(dimension_header) or "").strip().lower()
			if dimension_value in {"total", "grand total"}:
				total_rows.append(row)
				continue
			sortable_rows.append(row)

		sorted_rows = sorted(
			sortable_rows,
			key=lambda row: _numeric_value(row.get(metric_header)),
			reverse=(direction != "asc"),
		)
		if target_limit > 0:
			sorted_rows = sorted_rows[: target_limit]

		render_metric_header = metric_header
		if show_million and "million" not in render_metric_header.lower():
			render_metric_header = (
				render_metric_header.replace("(MMK)", "(Million MMK)")
				if "(MMK)" in render_metric_header
				else f"{render_metric_header} (Million MMK)"
			)

		table_rows: List[Dict[str, str]] = []
		rank_required = target_limit > 0
		for idx, row in enumerate(sorted_rows, start=1):
			out_row: Dict[str, str] = {}
			if rank_required:
				out_row["Rank"] = str(idx)
			out_row[display_dimension or dimension_header] = str(row.get(dimension_header) or "").strip()
			out_row[render_metric_header] = _format_amount(_numeric_value(row.get(metric_header)), show_million)
			table_rows.append(out_row)

		if total_rows and target_limit <= 0:
			for row in total_rows:
				out_row = {}
				if rank_required:
					out_row["Rank"] = ""
				out_row[display_dimension or dimension_header] = str(row.get(dimension_header) or "").strip()
				out_row[render_metric_header] = _format_amount(_numeric_value(row.get(metric_header)), show_million)
				table_rows.append(out_row)

		if not table_rows:
			return ""

		output_dimension_header = display_dimension or dimension_header
		table_headers = (["Rank"] if rank_required else []) + [output_dimension_header, render_metric_header]
		if target_limit > 0:
			title_prefix = "Top" if direction != "asc" else "Bottom"
			base_title = _normalize_header(adapter.get("title")) if adapter else ""
			title = base_title or f"{title_prefix} {target_limit} by {metric_header}"
		else:
			title = f"{output_dimension_header} sorted by {metric_header}"
		table_block = _build_markdown_table(table_headers, table_rows)
		return f"## {title}\n\n{table_block}".strip()

	if mode_name == "dimension_breakdown":
		report_name = _normalize_header(grounded_turn.get("source_name"))
		adapter = report_local_followup_adapter(report_name, mode_name)
		if not adapter:
			return ""
		headers = grounded_turn.get("returned_schema")
		rows = grounded_turn.get("table_rows")
		if not isinstance(headers, list) or not isinstance(rows, list):
			return ""
		source_dimension = _normalize_header(adapter.get("source_dimension_header"))
		display_dimension = _normalize_header(adapter.get("display_dimension_label")) or source_dimension or "Dimension"
		if target_dimension and _normalize_header(target_dimension) not in {display_dimension, source_dimension}:
			return ""
		metric_headers = [
			_normalize_header(value)
			for value in (adapter.get("metric_headers") or [])
			if _normalize_header(value)
		]
		if not source_dimension or not metric_headers:
			return ""
		header_set = {_normalize_header(value) for value in headers if _normalize_header(value)}
		if source_dimension not in header_set:
			return ""
		show_million = bool((display_preferences or {}).get("million"))
		render_headers = [display_dimension]
		metric_pairs: List[Tuple[str, str]] = []
		for metric in metric_headers:
			if metric not in header_set:
				continue
			if show_million and "million" not in metric.lower():
				render_header = metric.replace("(MMK)", "(Million MMK)") if "(MMK)" in metric else f"{metric} (Million MMK)"
			else:
				render_header = metric
			render_headers.append(render_header)
			metric_pairs.append((metric, render_header))
		table_rows: List[Dict[str, str]] = []
		for row in rows:
			if not isinstance(row, dict):
				continue
			dimension_value = str(row.get(source_dimension) or "").strip()
			if not dimension_value:
				continue
			out_row: Dict[str, str] = {display_dimension: dimension_value}
			for metric, render_header in metric_pairs:
				value = _numeric_value(row.get(metric))
				out_row[render_header] = _format_amount(value, show_million)
			table_rows.append(out_row)
		if not table_rows:
			return ""
		table_block = _build_markdown_table(render_headers, table_rows)
		title = _normalize_header(adapter.get("title")) or f"{display_dimension} Breakdown"
		return f"## {title}\n\n{table_block}".strip()

	if mode_name != "aging_bucket_view":
		return ""
	report_name = _normalize_header(grounded_turn.get("source_name"))
	adapter = report_local_followup_adapter(report_name, mode_name)
	if not adapter:
		return ""

	headers = grounded_turn.get("returned_schema")
	rows = grounded_turn.get("table_rows")
	if not isinstance(headers, list) or not isinstance(rows, list):
		return ""

	show_million = bool((display_preferences or {}).get("million"))
	total_outstanding_field = _normalize_header(adapter.get("total_outstanding_field"))
	total_due_field = _normalize_header(adapter.get("total_due_field"))
	total_outstanding = sum(_numeric_value(row.get(total_outstanding_field)) for row in rows if isinstance(row, dict))

	amount_header = "Amount (Million MMK)" if show_million else "Amount (MMK)"
	table_rows: List[Dict[str, str]] = []
	for bucket in adapter.get("bucket_labels") or []:
		label = _normalize_header(bucket)
		if not label:
			continue
		if label == "Future Amount":
			amount = sum(
				max(_numeric_value(row.get(total_outstanding_field)) - _numeric_value(row.get(total_due_field)), 0.0)
				for row in rows
				if isinstance(row, dict)
			)
		else:
			amount = sum(_numeric_value(row.get(label)) for row in rows if isinstance(row, dict))
		table_rows.append({"Due Period": label, amount_header: _format_amount(amount, show_million)})

	total_text = (
		f"{_format_million_value(total_outstanding)} Million MMK"
		if show_million
		else f"{_format_amount(total_outstanding, False)} MMK"
	)
	table_block = _build_markdown_table(["Due Period", amount_header], table_rows)
	title = _normalize_header(adapter.get("title")) or "Due Period View"
	return f"## {title}\n\nTotal Outstanding: {total_text}\n\n{table_block}".strip()
