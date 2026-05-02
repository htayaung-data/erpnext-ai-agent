from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from ai_assistant_ui.qwen_chat.contracts import (
	NormalizedFamilyArtifactContract,
	build_normalized_family_artifact_contract,
)
from ai_assistant_ui.qwen_chat.analytical_scope_policy import (
	apply_analytical_scope_runtime_policy,
)
from ai_assistant_ui.qwen_chat.governed_scope_registry import scope_id_for_entity_grain
from ai_assistant_ui.qwen_chat.master_data_directory_support import (
	master_directory_context,
	master_directory_requested_column_alias_map,
	requested_master_directory_columns,
)
from ai_assistant_ui.qwen_chat.master_data_family_support import is_master_data_listing_family
from ai_assistant_ui.qwen_chat.metadata import (
	capability_fresh_query_defaults,
	entity_grain_display_label,
	get_report_spec,
	report_business_family_ids,
	report_family_entity_dimension_label,
)

from ai_assistant_ui.qwen_chat.semantic_aliases import get_canonical_key


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


def _clean_rows(values: Any) -> List[Dict[str, Any]]:
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(value or "").strip() for value in values if str(value or "").strip()]


def _raw_report_data(result: Dict[str, Any]) -> List[Any]:
	values = result.get("data")
	if not isinstance(values, list):
		return []
	return list(values)


def _normalize_key(value: Any) -> str:
	text = str(value or "").strip().lower()
	text = re.sub(r"[^a-z0-9]+", "_", text)
	return text.strip("_")


def _strip_quotes(value: Any) -> str:
	text = str(value or "").strip()
	return text.strip("'\"")


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


def _is_total_like_row(row: Dict[str, Any]) -> bool:
	if not isinstance(row, dict):
		return False
	for value in row.values():
		text = _strip_quotes(value).strip().lower()
		if text == "total":
			return True
	return False


def _analytical_dimensions(
	*,
	family_id: str,
	report_name: str,
	dimensions: Dict[str, Any],
) -> Dict[str, Any]:
	return apply_analytical_scope_runtime_policy(
		family_id=family_id,
		report_name=report_name,
		dimensions=dimensions,
	)


def _metric_label(metric_key: str, fallback: str = "Value") -> str:
	key = str(metric_key or "").strip().lower()
	clean_fallback = str(fallback or "").strip()
	fallback_key = {
		"sales amount": "sales_amount",
		"gross profit": "gross_profit",
		"gross profit %": "gross_profit_percent",
		"gross profit percent": "gross_profit_percent",
		"buying amount": "buying_amount",
		"quantity": "quantity",
		"outstanding amount": "outstanding_total",
		"total amount due": "total_due",
		"balance value": "balance_value",
		"balance qty": "balance_qty",
		"contribution %": "contribution_percent",
		"grand total": "grand_total",
		"received amount": "received_amount",
		"total allocated amount": "total_allocated_amount",
		"paid amount": "paid_amount",
	}.get(clean_fallback.lower().replace("_", " "))
	if fallback_key and fallback_key != key:
		clean_fallback = ""
	if clean_fallback and clean_fallback.lower() not in {"value", "primary metric"}:
		if clean_fallback == clean_fallback.lower():
			return clean_fallback.replace("_", " ").title()
		return clean_fallback
	return {
		"sales_amount": "Sales Amount",
		"gross_profit": "Gross Profit",
		"gross_profit_percent": "Gross Profit %",
		"buying_amount": "Buying Amount",
		"quantity": "Quantity",
		"outstanding_total": "Outstanding Amount",
		"total_due": "Total Amount Due",
		"balance_value": "Balance Value",
		"balance_qty": "Balance Qty",
		"contribution_percent": "Contribution %",
		"grand_total": "Grand Total",
		"received_amount": "Received Amount",
		"total_allocated_amount": "Total Allocated Amount",
		"paid_amount": "Paid Amount",
	}.get(key, fallback or "Value")


def _summary_total_metric_label(metric_label: str) -> str:
	label = str(metric_label or "").strip()
	if not label:
		return "Total Amount"
	if label.lower().startswith("total "):
		return label
	return f"Total {label}"


def _tool_trace_items(runtime_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	values = runtime_payload.get("tool_trace")
	if not isinstance(values, list):
		return []
	return [item for item in values if isinstance(item, dict)]


def _report_tool(runtime_payload: Dict[str, Any]) -> Dict[str, Any]:
	for item in reversed(_tool_trace_items(runtime_payload)):
		if str(item.get("tool") or "").strip() == "erp_fac-generate_report":
			return item
	return {}


def _tool_args(item: Dict[str, Any]) -> Dict[str, Any]:
	value = item.get("detail_obj")
	if isinstance(value, dict):
		return value
	parsed = _safe_json_loads(item.get("detail"))
	return parsed if isinstance(parsed, dict) else {}


def _report_result(report_tool: Dict[str, Any]) -> Dict[str, Any]:
	output_obj = report_tool.get("output_obj")
	if not isinstance(output_obj, dict):
		output_obj = _safe_json_loads(report_tool.get("output_preview"))
	if not isinstance(output_obj, dict):
		return {}
	result = output_obj.get("result")
	return dict(result) if isinstance(result, dict) else {}


def _report_rows(result: Dict[str, Any]) -> List[Dict[str, Any]]:
	rows = _clean_rows(result.get("data"))
	if rows:
		return rows
	columns = _report_columns(result)
	data = _raw_report_data(result)
	if not columns or not data:
		return []
	out: List[Dict[str, Any]] = []
	for item in data:
		if not isinstance(item, list):
			continue
		mapped: Dict[str, Any] = {}
		for index, column in enumerate(columns):
			fieldname = str(column.get("fieldname") or "").strip() or f"col_{index}"
			mapped[fieldname] = item[index] if index < len(item) else None
		out.append(mapped)
	return out


def _report_filters(report_tool: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
	applied = result.get("filters_applied")
	if isinstance(applied, dict):
		return dict(applied)
	filters = _tool_args(report_tool).get("filters")
	return dict(filters) if isinstance(filters, dict) else {}


def _report_columns(result: Dict[str, Any]) -> List[Dict[str, Any]]:
	return _clean_rows(result.get("columns"))


def _report_total_row_map(result: Dict[str, Any]) -> Dict[str, Any]:
	data = _raw_report_data(result)
	if not data:
		return {}
	last_row = data[-1]
	if not isinstance(last_row, list):
		return {}
	columns = _report_columns(result)
	if not columns or len(last_row) != len(columns):
		return {}
	out: Dict[str, Any] = {}
	for index, column in enumerate(columns):
		fieldname = str(column.get("fieldname") or "").strip() or f"col_{index}"
		out[fieldname] = last_row[index]
	return out


def _period_from_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"from_date": str(
			filters.get("period_start_date")
			or filters.get("from_date")
			or ""
		).strip(),
		"to_date": str(
			filters.get("period_end_date")
			or filters.get("to_date")
			or filters.get("report_date")
			or ""
		).strip(),
		"fiscal_year": str(filters.get("fiscal_year") or "").strip(),
		"from_fiscal_year": str(filters.get("from_fiscal_year") or filters.get("fiscal_year") or "").strip(),
		"to_fiscal_year": str(filters.get("to_fiscal_year") or filters.get("fiscal_year") or "").strip(),
		"periodicity": str(filters.get("periodicity") or filters.get("period") or filters.get("range") or "").strip(),
	}


def _statement_type_for_report(report_name: str) -> str:
	key = _normalize_key(report_name)
	if key == "profit_and_loss_statement":
		return "profit_and_loss"
	if key == "balance_sheet":
		return "balance_sheet"
	if key == "cash_flow":
		return "cash_flow"
	return ""


def _value_fieldname(columns: List[Dict[str, Any]]) -> str:
	for item in columns:
		fieldname = str(item.get("fieldname") or "").strip()
		if fieldname and fieldname not in {"account", "acc_name", "acc_number", "currency", "section"}:
			return fieldname
	return ""


def _sum_field(rows: List[Dict[str, Any]], fieldname: str) -> float:
	total = 0.0
	for row in rows:
		if not isinstance(row, dict):
			continue
		total += _numeric_value(row.get(fieldname))
	return total


def _clean_metric_key(value: Any) -> str:
	return _normalize_key(value)


def _requested_metric_keys(compiler_contract: Dict[str, Any]) -> set[str]:
	requested = {
		_clean_metric_key(value)
		for value in (compiler_contract.get("requested_metrics") or [])
		if str(value or "").strip()
	}
	governed_details = (
		compiler_contract.get("governed_resolution_details")
		if isinstance(compiler_contract.get("governed_resolution_details"), dict)
		else {}
	)
	requested.update(
		{
			_clean_metric_key(value)
			for value in (governed_details.get("requested_metric_keys") or [])
			if str(value or "").strip()
		}
	)
	return requested


def _requested_dimension_keys(compiler_contract: Dict[str, Any]) -> set[str]:
	return {
		_clean_metric_key(value)
		for value in (compiler_contract.get("requested_dimensions") or [])
		if str(value or "").strip()
	}


def _requested_time_scope(compiler_contract: Dict[str, Any]) -> str:
	return str(compiler_contract.get("requested_time_scope") or "").strip()


def _requested_top_n_from_contract(compiler_contract: Dict[str, Any]) -> int:
	try:
		return max(0, min(50, int(compiler_contract.get("target_limit") or 0)))
	except Exception:
		return 0


def _canonical_requested_values(
	compiler_contract: Dict[str, Any],
	fieldname: str,
	*,
	dimension_or_metric: str,
) -> List[str]:
	values = compiler_contract.get(fieldname)
	if not isinstance(values, list):
		return []
	capability_id = str(compiler_contract.get("capability_id") or "").strip() or None
	out: List[str] = []
	for value in values:
		raw = str(value or "").strip()
		if not raw:
			continue
		canonical = get_canonical_key(
			raw,
			capability_id=capability_id,
			dimension_or_metric=dimension_or_metric,
		)
		out.append(str(canonical or _clean_metric_key(raw)).strip())
	return list(dict.fromkeys([value for value in out if value]))


def _requested_metric_key_from_contract(
	compiler_contract: Dict[str, Any],
	available_metric_keys: List[str],
	default_metric_key: str,
) -> str:
	available_by_key = {
		_clean_metric_key(metric_key): str(metric_key or "").strip()
		for metric_key in available_metric_keys
		if str(metric_key or "").strip()
	}
	for requested_key in _canonical_requested_values(
		compiler_contract,
		"requested_metrics",
		dimension_or_metric="metric",
	):
		resolved = available_by_key.get(_clean_metric_key(requested_key))
		if resolved:
			return resolved
	return str(default_metric_key or "").strip()


def _requested_metric_label_from_contract(
	compiler_contract: Dict[str, Any],
	metric_key: str,
	fallback_label: str,
) -> str:
	values = compiler_contract.get("requested_metrics")
	if isinstance(values, list):
		capability_id = str(compiler_contract.get("capability_id") or "").strip() or None
		target_key = _clean_metric_key(metric_key)
		for raw in values:
			label = str(raw or "").strip()
			if not label:
				continue
			canonical = get_canonical_key(
				label,
				capability_id=capability_id,
				dimension_or_metric="metric",
			)
			if _clean_metric_key(canonical or label) == target_key:
				return label
	return _metric_label(metric_key, fallback_label)


def _requested_output_columns_from_contract(
	compiler_contract: Dict[str, Any],
	*,
	available_metric_keys: List[str],
	primary_metric_key: str,
	entity_code_dimension_keys: Tuple[str, ...] = ("item_code",),
) -> List[str]:
	requested_dimensions = set(
		_canonical_requested_values(
			compiler_contract,
			"requested_dimensions",
			dimension_or_metric="dimension",
		)
	)
	requested_metrics = set(
		_canonical_requested_values(
			compiler_contract,
			"requested_metrics",
			dimension_or_metric="metric",
		)
	)
	has_explicit_projection_request = bool(requested_dimensions or requested_metrics)
	columns: List[str] = []
	if requested_dimensions:
		columns.append("entity")
	if requested_dimensions.intersection(entity_code_dimension_keys):
		columns.append("entity_code")
	requested_metric_key = _requested_metric_key_from_contract(
		compiler_contract,
		available_metric_keys,
		primary_metric_key,
	)
	if requested_metric_key:
		columns.append(requested_metric_key)
	if "contribution_percent" in requested_metrics and "contribution_percent" in available_metric_keys:
		columns.append("contribution_percent")
	return list(dict.fromkeys([value for value in columns if value]))


def _requested_secondary_metric_keys_from_contract(
	compiler_contract: Dict[str, Any],
	*,
	available_metric_keys: List[str],
	primary_metric_key: str,
) -> List[str]:
	available_by_key = {
		_clean_metric_key(metric_key): str(metric_key or "").strip()
		for metric_key in available_metric_keys
		if str(metric_key or "").strip()
	}
	primary_key = _clean_metric_key(primary_metric_key)
	out: List[str] = []
	for requested_key in _canonical_requested_values(
		compiler_contract,
		"requested_metrics",
		dimension_or_metric="metric",
	):
		resolved = available_by_key.get(_clean_metric_key(requested_key))
		if not resolved or _clean_metric_key(resolved) == primary_key:
			continue
		if resolved not in out:
			out.append(resolved)
	return out


def _ranking_requested_column_alias_map(
	*,
	entity_dimension: str,
	available_metric_keys: List[str],
) -> Dict[str, str]:
	alias_map: Dict[str, str] = {"entity": "entity"}
	entity_key = _normalize_key(entity_dimension)
	if entity_key in {"customer", "customers"}:
		alias_map.update({"customer": "entity", "customers": "entity"})
	elif entity_key in {"item", "items", "product", "products"} or "item" in entity_key or "product" in entity_key:
		alias_map.update(
			{
				"item": "entity",
				"items": "entity",
				"item_name": "entity",
				"product": "entity",
				"products": "entity",
				"product_name": "entity",
			}
		)
	if "sales_amount" in available_metric_keys:
		alias_map.update(
			{
				"amount": "sales_amount",
				"revenue": "sales_amount",
				"sales": "sales_amount",
				"sales_amount": "sales_amount",
				"value": "sales_amount",
			}
		)
	if "quantity" in available_metric_keys:
		alias_map.update({"qty": "quantity", "quantity": "quantity"})
	if "average_order_value" in available_metric_keys:
		alias_map.update({"aov": "average_order_value", "average_order_value": "average_order_value"})
	if "average_invoice_value" in available_metric_keys:
		alias_map.update({"average_invoice_value": "average_invoice_value"})
	if "average_selling_price" in available_metric_keys:
		alias_map.update({"asp": "average_selling_price", "average_selling_price": "average_selling_price"})
	if "gross_profit" in available_metric_keys:
		alias_map.update({"gross_profit": "gross_profit"})
	if "gross_profit_percent" in available_metric_keys:
		alias_map.update(
			{
				"gross_profit_percent": "gross_profit_percent",
				"gross_profit_percentage": "gross_profit_percent",
				"gross_profit_pct": "gross_profit_percent",
			}
		)
	if "buying_amount" in available_metric_keys:
		alias_map.update({"buying_amount": "buying_amount", "cost": "buying_amount"})
	if "contribution_percent" in available_metric_keys:
		alias_map.update(
			{
				"contribution": "contribution_percent",
				"contribution_percent": "contribution_percent",
				"share": "contribution_percent",
			}
		)
	return alias_map


def _apply_ranking_request_hints(
	dimensions: Dict[str, Any],
	*,
	compiler_contract: Dict[str, Any],
	available_metric_keys: List[str],
	default_metric_key: str,
	entity_dimension: str,
) -> Dict[str, Any]:
	hints = _apply_request_hints(
		dimensions,
		compiler_contract=compiler_contract,
		available_metric_keys=available_metric_keys,
		default_metric_key=default_metric_key,
		entity_code_dimension_keys=(),
	)
	requested_metric_key = str(hints.get("requested_metric_key") or default_metric_key or "").strip()
	requested_columns = ["entity"]
	if requested_metric_key:
		requested_columns.append(requested_metric_key)
	secondary_metric_keys = _requested_secondary_metric_keys_from_contract(
		compiler_contract,
		available_metric_keys=available_metric_keys,
		primary_metric_key=requested_metric_key,
	)
	requested_columns.extend(secondary_metric_keys)
	hints["requested_columns"] = list(dict.fromkeys([value for value in requested_columns if value]))
	hints["requested_projection_mode"] = "explicit_selection" if secondary_metric_keys else "default"
	hints["requested_column_alias_map"] = _ranking_requested_column_alias_map(
		entity_dimension=entity_dimension,
		available_metric_keys=available_metric_keys,
	)
	hints["suppress_summary_by_default"] = True
	return hints


def _apply_request_hints(
	dimensions: Dict[str, Any],
	*,
	compiler_contract: Dict[str, Any],
	available_metric_keys: List[str],
	default_metric_key: str,
	entity_code_dimension_keys: Tuple[str, ...] = ("item_code",),
) -> Dict[str, Any]:
	hints = dict(dimensions or {})
	top_n = _requested_top_n_from_contract(compiler_contract)
	if top_n > 0:
		hints["requested_top_n"] = top_n
	requested_metric_key = _requested_metric_key_from_contract(
		compiler_contract,
		available_metric_keys,
		default_metric_key,
	)
	if requested_metric_key:
		hints["requested_metric_key"] = requested_metric_key
	requested_columns = _requested_output_columns_from_contract(
		compiler_contract,
		available_metric_keys=available_metric_keys,
		primary_metric_key=requested_metric_key or default_metric_key,
		entity_code_dimension_keys=entity_code_dimension_keys,
	)
	if requested_columns:
		hints["requested_columns"] = requested_columns
	if available_metric_keys:
		hints["available_metric_keys"] = [value for value in available_metric_keys if str(value or "").strip()]
	return hints


def _add_contribution_percent(
	rows: List[Dict[str, Any]],
	*,
	base_metric_key: str,
) -> List[Dict[str, Any]]:
	clean_rows = [dict(item) for item in rows if isinstance(item, dict)]
	total_value = sum(_numeric_value(item.get(base_metric_key)) for item in clean_rows)
	for item in clean_rows:
		value = _numeric_value(item.get(base_metric_key))
		item["contribution_percent"] = (value / total_value * 100.0) if total_value > 0 else 0.0
	return clean_rows


def _looks_like_period_column(fieldname: str, label: str) -> bool:
	field_key = _normalize_key(fieldname)
	label_key = _normalize_key(label)
	if not field_key:
		return False
	if field_key.startswith("total") or label_key.startswith("total"):
		return False
	period_prefixes = (
		"jan",
		"feb",
		"mar",
		"apr",
		"may",
		"jun",
		"jul",
		"aug",
		"sep",
		"oct",
		"nov",
		"dec",
		"q1",
		"q2",
		"q3",
		"q4",
		"h1",
		"h2",
		"year",
	)
	return any(field_key.startswith(prefix) or label_key.startswith(prefix) for prefix in period_prefixes)


def _period_field_specs(columns: List[Dict[str, Any]], metric_key: str = "") -> List[Tuple[str, str]]:
	excluded = {"entity", "entity_name", "total", "item_code", "item_name"}
	has_metric_suffixes = any(
		_looks_like_period_column(str(item.get("fieldname") or "").strip(), str(item.get("label") or "").strip())
		and _normalize_key(item.get("fieldname") or "").endswith(("qty", "amt"))
		for item in columns
		if isinstance(item, dict)
	)
	out: List[Tuple[str, str]] = []
	for item in columns:
		fieldname = str(item.get("fieldname") or "").strip()
		label = str(item.get("label") or "").strip()
		field_key = _normalize_key(fieldname)
		if not fieldname or fieldname in excluded or not _looks_like_period_column(fieldname, label):
			continue
		if has_metric_suffixes:
			if metric_key == "quantity" and not field_key.endswith("qty"):
				continue
			if metric_key != "quantity" and not field_key.endswith("amt"):
				continue
			label = re.sub(r"\s*\((qty|amt)\)\s*$", "", label, flags=re.IGNORECASE).strip()
		out.append((fieldname, label or fieldname))
	return out


def _time_grain_from_filters(filters: Dict[str, Any]) -> str:
	range_value = _normalize_key(filters.get("range") or filters.get("period") or filters.get("periodicity"))
	if range_value:
		return range_value
	return "monthly"


def _sort_ranked_rows(rows: List[Dict[str, Any]], metric_key: str) -> List[Dict[str, Any]]:
	ordered = sorted(
		[dict(item) for item in rows if isinstance(item, dict)],
		key=lambda item: _numeric_value(item.get(metric_key)),
		reverse=True,
	)
	for index, item in enumerate(ordered, start=1):
		item["rank"] = index
	return ordered


def _format_period_label(period_key: str) -> str:
	if re.fullmatch(r"\d{4}-\d{2}", period_key):
		year, month = period_key.split("-", 1)
		try:
			return dt.date(int(year), int(month), 1).strftime("%b %Y")
		except Exception:
			return period_key
	return period_key


def _first_text(row: Dict[str, Any], *fieldnames: str) -> str:
	for fieldname in fieldnames:
		value = str(row.get(fieldname) or "").strip()
		if value:
			return value
	return ""


def _stock_balance_qty(row: Dict[str, Any]) -> float:
	for fieldname in ("balance_qty", "bal_qty", "qty_after_transaction"):
		if fieldname in row:
			return _numeric_value(row.get(fieldname))
	return 0.0


def _stock_balance_value(row: Dict[str, Any]) -> float:
	for fieldname in ("balance_value", "bal_val", "stock_value"):
		if fieldname in row:
			return _numeric_value(row.get(fieldname))
	return 0.0


def _snapshot_period(filters: Dict[str, Any]) -> Dict[str, Any]:
	period = _period_from_filters(filters)
	if not str(period.get("to_date") or "").strip():
		period["to_date"] = dt.datetime.now(dt.timezone.utc).date().isoformat()
	return period


def _stock_snapshot_row_entry(row: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"item": _first_text(row, "item_name", "item_code", "item"),
		"item_code": _first_text(row, "item_code", "item"),
		"item_name": _first_text(row, "item_name", "item_code", "item"),
		"warehouse": _first_text(row, "warehouse"),
		"item_group": _first_text(row, "item_group"),
		"brand": _first_text(row, "brand"),
		"stock_uom": _first_text(row, "stock_uom"),
		"balance_qty": _stock_balance_qty(row),
		"balance_value": _stock_balance_value(row),
	}


def _sort_metric_rows(rows: List[Dict[str, Any]], metric_key: str) -> List[Dict[str, Any]]:
	return sorted(
		[dict(item) for item in rows if isinstance(item, dict)],
		key=lambda item: _numeric_value(item.get(metric_key)),
		reverse=True,
	)


def _aggregate_snapshot_dimension(
	rows: List[Dict[str, Any]],
	*,
	label_key: str,
	label_fieldnames: Tuple[str, ...],
) -> List[Dict[str, Any]]:
	aggregated: Dict[str, Dict[str, Any]] = {}
	for row in rows:
		label = ""
		for fieldname in label_fieldnames:
			label = str(row.get(fieldname) or "").strip()
			if label:
				break
		if not label:
			continue
		entry = aggregated.setdefault(
			label,
			{
				label_key: label,
				"balance_qty": 0.0,
				"balance_value": 0.0,
			},
		)
		entry["balance_qty"] = float(entry.get("balance_qty") or 0.0) + _numeric_value(row.get("balance_qty"))
		entry["balance_value"] = float(entry.get("balance_value") or 0.0) + _numeric_value(row.get("balance_value"))
	return _sort_metric_rows(list(aggregated.values()), "balance_value")


def _row_label(row: Dict[str, Any]) -> str:
	for key in ("account_name", "section_name", "section", "account", "acc_name"):
		text = _strip_quotes(row.get(key))
		if text:
			return text
	return ""


def _find_row_value(rows: List[Dict[str, Any]], *label_candidates: str) -> float | None:
	candidates = {_normalize_key(value) for value in label_candidates if str(value or "").strip()}
	for row in rows:
		label = _normalize_key(_row_label(row))
		if label and label in candidates:
			return _numeric_value(row.get("total"))
	return None


def _row_entry(row: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"label": _row_label(row),
		"account": _strip_quotes(row.get("account")),
		"parent_account": _strip_quotes(row.get("parent_account")),
		"section": _strip_quotes(row.get("section") or row.get("parent_section") or row.get("section_name")),
		"indent": int(row.get("indent") or 0),
		"opening_balance": _numeric_value(row.get("opening_balance")),
		"amount": _numeric_value(row.get("total")),
		"currency": str(row.get("currency") or "").strip(),
	}


def _root_account_label(row: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
	account_lookup: Dict[str, Dict[str, Any]] = {}
	for item in rows:
		account = _strip_quotes(item.get("account"))
		if account:
			account_lookup[account] = item
	current_account = _strip_quotes(row.get("account"))
	parent_account = _strip_quotes(row.get("parent_account"))
	seen: set[str] = set()
	target = parent_account or current_account
	last_label = _row_label(row)
	while target and target not in seen:
		seen.add(target)
		candidate = account_lookup.get(target)
		if not candidate:
			break
		last_label = _row_label(candidate) or last_label
		next_parent = _strip_quotes(candidate.get("parent_account"))
		if not next_parent:
			break
		target = next_parent
	return last_label


def _financial_statement_sections(
	statement_type: str,
	rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
	if statement_type == "profit_and_loss":
		sections: Dict[str, List[Dict[str, Any]]] = {"income": [], "expense": [], "summary": []}
		for row in rows:
			if not row:
				continue
			label = _row_label(row)
			parent = _strip_quotes(row.get("parent_account"))
			clean_entry = _row_entry(row)
			if not label:
				continue
			key = _normalize_key(label)
			parent_key = _normalize_key(parent)
			root_key = _normalize_key(_root_account_label(row, rows))
			if key in {"total_income_credit", "total_expense_debit", "profit_for_the_year", "net_profit", "loss_for_the_year"}:
				sections["summary"].append(clean_entry)
			elif "income" in key or "income" in parent_key or "income" in root_key:
				sections["income"].append(clean_entry)
			else:
				sections["expense"].append(clean_entry)
		return sections
	if statement_type == "balance_sheet":
		sections = {"assets": [], "liabilities": [], "equity": [], "summary": []}
		for row in rows:
			if not row:
				continue
			label = _row_label(row)
			parent = _strip_quotes(row.get("parent_account"))
			clean_entry = _row_entry(row)
			if not label:
				continue
			key = _normalize_key(label)
			parent_key = _normalize_key(parent)
			root_key = _normalize_key(_root_account_label(row, rows))
			if key.startswith("total_") or "provisional_profit_loss" in key:
				sections["summary"].append(clean_entry)
			elif (
				"asset" in key
				or "application_of_funds" in key
				or "asset" in parent_key
				or "application_of_funds" in root_key
				or "asset" in root_key
			):
				sections["assets"].append(clean_entry)
			elif (
				"liabilit" in key
				or "source_of_funds" in key
				or "liabilit" in parent_key
				or "source_of_funds" in root_key
				or "liabilit" in root_key
			):
				sections["liabilities"].append(clean_entry)
			else:
				sections["equity"].append(clean_entry)
		return sections
	if statement_type == "cash_flow":
		sections = {"operations": [], "investing": [], "financing": [], "summary": []}
		for row in rows:
			if not row:
				continue
			label = _row_label(row)
			section = _strip_quotes(row.get("parent_section") or row.get("section_name") or row.get("section"))
			clean_entry = _row_entry(row)
			key = _normalize_key(label or section)
			section_key = _normalize_key(section)
			if not label and not section:
				continue
			if "net_cash_from_operations" in key:
				sections["summary"].append(clean_entry)
			elif "net_cash_from_investing" in key:
				sections["summary"].append(clean_entry)
			elif "net_cash_from_financing" in key:
				sections["summary"].append(clean_entry)
			elif "net_change_in_cash" in key:
				sections["summary"].append(clean_entry)
			elif "operations" in section_key:
				sections["operations"].append(clean_entry)
			elif "investing" in section_key:
				sections["investing"].append(clean_entry)
			elif "financing" in section_key:
				sections["financing"].append(clean_entry)
		return sections
	return {}


def _financial_statement_metrics(statement_type: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
	if statement_type == "profit_and_loss":
		return {
			"statement_type": statement_type,
			"total_income": _find_row_value(rows, "Total Income (Credit)"),
			"total_expense": _find_row_value(rows, "Total Expense (Debit)"),
			"net_profit": _find_row_value(rows, "Profit for the year", "Net Profit", "Loss for the year"),
		}
	if statement_type == "balance_sheet":
		return {
			"statement_type": statement_type,
			"total_asset": _find_row_value(rows, "Total Asset (Debit)", "Total Assets"),
			"total_liability": _find_row_value(rows, "Total Liability (Credit)", "Total Liabilities"),
			"total_equity": _find_row_value(rows, "Total Equity (Credit)", "Total Equity"),
			"provisional_profit_or_loss": _find_row_value(rows, "Provisional Profit / Loss (Credit)"),
		}
	if statement_type == "cash_flow":
		return {
			"statement_type": statement_type,
			"net_cash_from_operations": _find_row_value(rows, "Net Cash from Operations"),
			"net_cash_from_investing": _find_row_value(rows, "Net Cash from Investing"),
			"net_cash_from_financing": _find_row_value(rows, "Net Cash from Financing"),
			"net_change_in_cash": _find_row_value(rows, "Net Change in Cash"),
		}
	return {"statement_type": statement_type}


def _aging_type_for_report(report_name: str) -> str:
	key = _normalize_key(report_name)
	if "accounts_payable" in key:
		return "accounts_payable"
	if "accounts_receivable" in key:
		return "accounts_receivable"
	return ""


def _aging_party_dimension_label(aging_type: str) -> str:
	if aging_type == "accounts_payable":
		return "Supplier"
	if aging_type == "accounts_receivable":
		return "Customer"
	return "Party"


def _aging_group_field(aging_type: str) -> str:
	if aging_type == "accounts_payable":
		return "supplier_group"
	if aging_type == "accounts_receivable":
		return "customer_group"
	return ""


def _aging_extra_dimension_field(aging_type: str) -> str:
	if aging_type == "accounts_receivable":
		return "territory"
	return ""


def _aging_bucket_specs() -> List[Tuple[str, str, Tuple[str, ...]]]:
	return [
		("future_bucket_total", "<0", ("future_amount", "range0")),
		("current_bucket_total", "0-30", ("range1",)),
		("bucket_31_60_total", "31-60", ("range2",)),
		("bucket_61_90_total", "61-90", ("range3",)),
		("bucket_91_120_total", "91-120", ("range4",)),
		("bucket_121_above_total", "121-Above", ("range5",)),
	]


def _aging_bucket_value(row: Dict[str, Any], field_candidates: Tuple[str, ...]) -> float:
	for fieldname in field_candidates:
		if fieldname in row:
			return _numeric_value(row.get(fieldname))
	return 0.0


def _aging_row_overdue_total(row: Dict[str, Any]) -> float:
	return (
		_aging_bucket_value(row, ("range2",))
		+ _aging_bucket_value(row, ("range3",))
		+ _aging_bucket_value(row, ("range4",))
		+ _aging_bucket_value(row, ("range5",))
	)


def _aging_filter_mode(compiler_contract: Dict[str, Any]) -> str:
	requested = _requested_metric_keys(compiler_contract)
	if "overdue_only" in requested:
		return "overdue_only"
	if "credit_balance_only" in requested:
		return "credit_balance_only"
	return ""


def _filter_aging_rows(rows: List[Dict[str, Any]], *, filter_mode: str) -> List[Dict[str, Any]]:
	if not filter_mode:
		return rows
	filtered: List[Dict[str, Any]] = []
	for row in rows:
		if not isinstance(row, dict):
			continue
		outstanding = _numeric_value(row.get("outstanding"))
		if filter_mode == "credit_balance_only":
			if outstanding < 0:
				filtered.append(row)
			continue
		if filter_mode == "overdue_only":
			if _aging_row_overdue_total(row) > 0:
				filtered.append(row)
			continue
		filtered.append(row)
	return filtered


def _aging_party_entry(row: Dict[str, Any], aging_type: str) -> Dict[str, Any]:
	group_field = _aging_group_field(aging_type)
	extra_field = _aging_extra_dimension_field(aging_type)
	entry: Dict[str, Any] = {
		"party": str(row.get("party") or "").strip(),
		"party_type": str(row.get("party_type") or _aging_party_dimension_label(aging_type)).strip(),
		"currency": str(row.get("currency") or "").strip(),
		"invoiced": _numeric_value(row.get("invoiced")),
		"paid": _numeric_value(row.get("paid")),
		"credit_note": _numeric_value(row.get("credit_note")),
		"outstanding": _numeric_value(row.get("outstanding")),
		"total_due": _numeric_value(row.get("total_due")),
		"future_amount": _aging_bucket_value(row, ("future_amount", "range0")),
		"bucket_0_30": _aging_bucket_value(row, ("range1",)),
		"bucket_31_60": _aging_bucket_value(row, ("range2",)),
		"bucket_61_90": _aging_bucket_value(row, ("range3",)),
		"bucket_91_120": _aging_bucket_value(row, ("range4",)),
		"bucket_121_above": _aging_bucket_value(row, ("range5",)),
	}
	if row.get("age") not in (None, ""):
		entry["age_days"] = int(_numeric_value(row.get("age")))
	for fieldname in (
		"posting_date",
		"due_date",
		"voucher_type",
		"voucher_no",
		"bill_no",
		"bill_date",
		"remarks",
		"party_account",
	):
		value = row.get(fieldname)
		if value not in (None, ""):
			entry[fieldname] = value
	if group_field:
		value = row.get(group_field)
		if value not in (None, ""):
			entry[group_field] = value
	if extra_field:
		value = row.get(extra_field)
		if value not in (None, ""):
			entry[extra_field] = value
	return entry


def _aging_sections(rows: List[Dict[str, Any]], aging_type: str, currency: str) -> Dict[str, Any]:
	parties = [
		_aging_party_entry(row, aging_type)
		for row in rows
		if isinstance(row, dict) and str(row.get("party") or "").strip()
	]
	parties.sort(key=lambda item: _numeric_value(item.get("outstanding")), reverse=True)
	bucket_totals: List[Dict[str, Any]] = []
	for metric_key, label, field_candidates in _aging_bucket_specs():
		amount = 0.0
		for row in rows:
			if not isinstance(row, dict):
				continue
			amount += _aging_bucket_value(row, field_candidates)
		bucket_totals.append(
			{
				"bucket_key": metric_key,
				"label": label,
				"amount": amount,
				"currency": currency,
			}
		)
	outstanding_total = _sum_field(rows, "outstanding")
	total_due_total = _sum_field(rows, "total_due")
	current_bucket_total = next(
		(item["amount"] for item in bucket_totals if item.get("bucket_key") == "current_bucket_total"),
		0.0,
	)
	overdue_total = sum(
		float(item.get("amount") or 0.0)
		for item in bucket_totals
		if item.get("bucket_key") in {"bucket_31_60_total", "bucket_61_90_total", "bucket_91_120_total", "bucket_121_above_total"}
	)
	overdue_ratio = (overdue_total / outstanding_total) if outstanding_total > 0 else 0.0
	summary = [
		{"label": "Outstanding Total", "metric_key": "outstanding_total", "amount": outstanding_total, "currency": currency},
		{"label": "Total Amount Due", "metric_key": "total_due", "amount": total_due_total, "currency": currency},
		{"label": "Current Bucket (0-30)", "metric_key": "current_bucket_total", "amount": current_bucket_total, "currency": currency},
		{"label": "Overdue Total (31+)", "metric_key": "overdue_total", "amount": overdue_total, "currency": currency},
		{"label": "Overdue Ratio", "metric_key": "overdue_ratio", "value": overdue_ratio},
	]
	return {
		"parties": parties,
		"bucket_totals": bucket_totals,
		"summary": summary,
	}


def _aging_metrics(rows: List[Dict[str, Any]], aging_type: str) -> Dict[str, Any]:
	future_bucket_total = 0.0
	current_bucket_total = 0.0
	bucket_31_60_total = 0.0
	bucket_61_90_total = 0.0
	bucket_91_120_total = 0.0
	bucket_121_above_total = 0.0
	for row in rows:
		if not isinstance(row, dict):
			continue
		future_bucket_total += _aging_bucket_value(row, ("future_amount", "range0"))
		current_bucket_total += _aging_bucket_value(row, ("range1",))
		bucket_31_60_total += _aging_bucket_value(row, ("range2",))
		bucket_61_90_total += _aging_bucket_value(row, ("range3",))
		bucket_91_120_total += _aging_bucket_value(row, ("range4",))
		bucket_121_above_total += _aging_bucket_value(row, ("range5",))
	outstanding_total = _sum_field(rows, "outstanding")
	total_due_total = _sum_field(rows, "total_due")
	overdue_total = bucket_31_60_total + bucket_61_90_total + bucket_91_120_total + bucket_121_above_total
	overdue_ratio = (overdue_total / outstanding_total) if outstanding_total > 0 else 0.0
	return {
		"aging_type": aging_type,
		"outstanding_total": outstanding_total,
		"total_due": total_due_total,
		"invoiced_total": _sum_field(rows, "invoiced"),
		"paid_total": _sum_field(rows, "paid"),
		"credit_note_total": _sum_field(rows, "credit_note"),
		"future_bucket_total": future_bucket_total,
		"current_bucket_total": current_bucket_total,
		"bucket_31_60_total": bucket_31_60_total,
		"bucket_61_90_total": bucket_61_90_total,
		"bucket_91_120_total": bucket_91_120_total,
		"bucket_121_above_total": bucket_121_above_total,
		"overdue_total": overdue_total,
		"overdue_ratio": overdue_ratio,
		"party_count": len([row for row in rows if isinstance(row, dict) and str(row.get("party") or "").strip()]),
	}


def _ranking_metric_choice(
	compiler_contract: Dict[str, Any],
	options: List[Tuple[set[str], Tuple[str, str]]],
	default_metric: Tuple[str, str],
) -> Tuple[str, str]:
	requested = _requested_metric_keys(compiler_contract)
	for aliases, metric in options:
		if requested & aliases:
			return metric
	return default_metric


def _ranking_summary(metric_key: str, metric_label: str, total_value: float, top_entity: str, top_value: float) -> List[Dict[str, Any]]:
	return [
		{"label": f"Total {metric_label}", "metric_key": metric_key, "amount": total_value},
		{"label": "Top Entity", "metric_key": "top_entity", "value": top_entity},
		{"label": f"Top {metric_label}", "metric_key": "top_value", "amount": top_value},
	]


def _build_sales_analytics_ranking(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	rows = [
		row
		for row in _report_rows(result)
		if isinstance(row, dict) and str(row.get("entity") or "").strip()
	]
	if not rows:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="ranking_analytics",
			report_name=report_name,
			errors=[f"Ranking adapter received no entity rows for `{report_name}`."],
		)
	filters = _report_filters(report_tool, result)
	period = _period_from_filters(filters)
	total_row = _report_total_row_map(result)
	metric_key = "quantity" if _normalize_key(filters.get("value_quantity")) == "quantity" else "sales_amount"
	metric_label = _requested_metric_label_from_contract(
		compiler_contract,
		metric_key,
		"Quantity" if metric_key == "quantity" else "Sales Amount",
	)
	ranked_rows = _sort_ranked_rows(
		[
			{
				"entity": str(row.get("entity") or "").strip(),
				"entity_name": str(row.get("entity_name") or "").strip(),
				metric_key: _numeric_value(row.get("total")),
			}
			for row in rows
		],
		metric_key,
	)
	ranked_rows = _add_contribution_percent(ranked_rows, base_metric_key=metric_key)
	total_value = _numeric_value(total_row.get("total")) or sum(_numeric_value(row.get(metric_key)) for row in ranked_rows)
	top_row = ranked_rows[0] if ranked_rows else {}
	available_metric_keys = [metric_key, "contribution_percent"]
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="ranking_analytics",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions=_analytical_dimensions(
			family_id="ranking_analytics",
			report_name=report_name,
			dimensions=_apply_ranking_request_hints({
				"entity_dimension": str(filters.get("tree_type") or "Entity").strip() or "Entity",
				"primary_metric_key": metric_key,
				"primary_metric_label": metric_label,
				"time_grain": _time_grain_from_filters(filters),
				"source_grain": "entity_total",
			},
				compiler_contract=compiler_contract,
				available_metric_keys=available_metric_keys,
				default_metric_key=metric_key,
				entity_dimension=str(filters.get("tree_type") or "Entity").strip() or "Entity",
			),
		),
		metrics={
			metric_key: total_value,
			"entity_count": len(ranked_rows),
			"top_value": _numeric_value(top_row.get(metric_key)),
		},
		sections={
			"ranked_rows": ranked_rows,
			"summary": _ranking_summary(
				metric_key,
				metric_label,
				total_value,
				str(top_row.get("entity_name") or top_row.get("entity") or "").strip(),
				_numeric_value(top_row.get(metric_key)),
			),
		},
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="ranking_analytics",
		report_name=report_name,
		artifact_contract=artifact,
	)


def _build_aging_ranking(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	rows = [
		row
		for row in _report_rows(result)
		if isinstance(row, dict) and str(row.get("party") or "").strip()
	]
	if not rows:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="ranking_analytics",
			report_name=report_name,
			errors=[f"Ranking adapter received no party rows for `{report_name}`."],
		)
	aging_type = _aging_type_for_report(report_name)
	filters = _report_filters(report_tool, result)
	period = _period_from_filters(filters)
	metric_key, metric_label = _ranking_metric_choice(
		compiler_contract,
		options=[
			({"total_due", "total_amount_due"}, ("total_due", "Total Amount Due")),
		],
		default_metric=("outstanding_total", "Outstanding Amount"),
	)
	source_field = "total_due" if metric_key == "total_due" else "outstanding"
	entity_dimension = _aging_party_dimension_label(aging_type)
	available_metric_keys = ["outstanding_total", "total_due", "contribution_percent"]
	metric_key = _requested_metric_key_from_contract(compiler_contract, available_metric_keys, metric_key)
	metric_label = _metric_label(metric_key, metric_label)
	ranked_rows = _sort_ranked_rows(
		[
			{
				"entity": str(row.get("party") or "").strip(),
				"outstanding_total": _numeric_value(row.get("outstanding")),
				"total_due": _numeric_value(row.get("total_due")),
			}
			for row in rows
		],
		metric_key,
	)
	ranked_rows = _add_contribution_percent(ranked_rows, base_metric_key=metric_key)
	total_value = sum(_numeric_value(row.get(metric_key)) for row in ranked_rows)
	top_row = ranked_rows[0] if ranked_rows else {}
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="ranking_analytics",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions=_analytical_dimensions(
			family_id="ranking_analytics",
			report_name=report_name,
			dimensions=_apply_ranking_request_hints({
				"entity_dimension": entity_dimension,
				"primary_metric_key": metric_key,
				"primary_metric_label": metric_label,
				"source_grain": "aging_summary",
				"aging_type": aging_type,
			},
				compiler_contract=compiler_contract,
				available_metric_keys=available_metric_keys,
				default_metric_key=metric_key,
				entity_dimension=entity_dimension,
			),
		),
		metrics={
			metric_key: total_value,
			"entity_count": len(ranked_rows),
			"top_value": _numeric_value(top_row.get(metric_key)),
		},
		sections={
			"ranked_rows": ranked_rows,
			"summary": _ranking_summary(
				metric_key,
				metric_label,
				total_value,
				str(top_row.get("entity") or "").strip(),
				_numeric_value(top_row.get(metric_key)),
			),
		},
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="ranking_analytics",
		report_name=report_name,
		artifact_contract=artifact,
	)


def _is_total_label(value: Any) -> bool:
	return _normalize_key(value) == "total"


def _build_gross_profit_ranking(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	all_rows = [row for row in _report_rows(result) if isinstance(row, dict)]
	if not all_rows:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="ranking_analytics",
			report_name=report_name,
			errors=[f"Ranking adapter received no rows for `{report_name}`."],
		)
	total_row = next(
		(
			row
			for row in all_rows
			if _is_total_label(row.get("item_code")) or _is_total_label(row.get("item_name"))
		),
		{},
	)
	rows = [
		row
		for row in all_rows
		if not (_is_total_label(row.get("item_code")) or _is_total_label(row.get("item_name")))
	]
	if not rows:
		rows = all_rows
	metric_key, metric_label = _ranking_metric_choice(
		compiler_contract,
		options=[
			({"gross_profit_percent", "gross_profit_percentage", "gross_profit_"}, ("gross_profit_percent", "Gross Profit Percent")),
			({"sales_amount", "selling_amount", "revenue", "value"}, ("sales_amount", "Sales Amount")),
			({"buying_amount", "cost"}, ("buying_amount", "Buying Amount")),
			({"quantity", "qty"}, ("quantity", "Quantity")),
		],
		default_metric=("gross_profit", "Gross Profit"),
	)
	source_field = {
		"gross_profit": "gross_profit",
		"gross_profit_percent": "gross_profit_%",
		"sales_amount": "selling_amount",
		"buying_amount": "buying_amount",
		"quantity": "qty",
	}.get(metric_key, "gross_profit")
	filters = _report_filters(report_tool, result)
	period = _period_from_filters(filters)
	available_metric_keys = [
		"gross_profit",
		"gross_profit_percent",
		"sales_amount",
		"buying_amount",
		"quantity",
		"contribution_percent",
	]
	metric_key = _requested_metric_key_from_contract(compiler_contract, available_metric_keys, metric_key)
	metric_label = _metric_label(metric_key, metric_label)
	source_field = {
		"gross_profit": "gross_profit",
		"gross_profit_percent": "gross_profit_%",
		"sales_amount": "selling_amount",
		"buying_amount": "buying_amount",
		"quantity": "qty",
	}.get(metric_key, "gross_profit")
	ranked_rows = _sort_ranked_rows(
		[
			{
				"entity": str(row.get("item_name") or row.get("item_code") or "").strip(),
				"entity_code": str(row.get("item_code") or "").strip(),
				"brand": str(row.get("brand") or "").strip(),
				"item_group": str(row.get("item_group") or "").strip(),
				"sales_amount": _numeric_value(row.get("selling_amount")),
				"buying_amount": _numeric_value(row.get("buying_amount")),
				"gross_profit": _numeric_value(row.get("gross_profit")),
				"gross_profit_percent": _numeric_value(row.get("gross_profit_%")),
				"quantity": _numeric_value(row.get("qty")),
				metric_key: _numeric_value(row.get(source_field)),
			}
			for row in rows
		],
		metric_key,
	)
	contribution_metric_key = "sales_amount" if any(_numeric_value(row.get("sales_amount")) for row in ranked_rows) else metric_key
	ranked_rows = _add_contribution_percent(ranked_rows, base_metric_key=contribution_metric_key)
	total_value = _numeric_value(total_row.get(source_field)) or sum(_numeric_value(row.get(metric_key)) for row in ranked_rows)
	top_row = ranked_rows[0] if ranked_rows else {}
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="ranking_analytics",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions=_analytical_dimensions(
			family_id="ranking_analytics",
			report_name=report_name,
			dimensions=_apply_ranking_request_hints({
				"entity_dimension": report_family_entity_dimension_label(
					"ranking_analytics",
					entity_fields=("item_name", "item_code"),
					default_label=str(filters.get("group_by") or "Item Code").strip() or "Item Code",
				),
				"primary_metric_key": metric_key,
				"primary_metric_label": metric_label,
				"source_grain": "grouped_profitability",
			},
				compiler_contract=compiler_contract,
				available_metric_keys=available_metric_keys,
				default_metric_key=metric_key,
				entity_dimension=report_family_entity_dimension_label(
					"ranking_analytics",
					entity_fields=("item_name", "item_code"),
					default_label=str(filters.get("group_by") or "Item Code").strip() or "Item Code",
				),
			),
		),
		metrics={
			metric_key: total_value,
			"entity_count": len(ranked_rows),
			"top_value": _numeric_value(top_row.get(metric_key)),
		},
		sections={
			"ranked_rows": ranked_rows,
			"summary": _ranking_summary(
				metric_key,
				metric_label,
				total_value,
				str(top_row.get("entity") or "").strip(),
				_numeric_value(top_row.get(metric_key)),
			),
		},
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="ranking_analytics",
		report_name=report_name,
		artifact_contract=artifact,
	)


def _history_entity_dimension_fields(compiler_contract: Dict[str, Any]) -> Tuple[str, Tuple[str, ...]]:
	requested = _requested_dimension_keys(compiler_contract)
	if "customer" in requested or "party" in requested:
		return "Customer", ("customer_name", "customer")
	if "territory" in requested:
		return "Territory", ("territory",)
	if "item_group" in requested:
		return "Item Group", ("item_group",)
	return "Item", ("item_name", "item_code")


def _history_metric_choice(compiler_contract: Dict[str, Any]) -> Tuple[str, str, Tuple[str, ...]]:
	requested = _requested_metric_keys(compiler_contract)
	if requested & {"quantity", "qty", "delivered_quantity"}:
		return "quantity", "Quantity", ("delivered_quantity", "quantity")
	return "sales_amount", "Sales Amount", ("billed_amount", "amount")


def _build_item_history_ranking(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	rows = [row for row in _report_rows(result) if isinstance(row, dict)]
	if not rows:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="ranking_analytics",
			report_name=report_name,
			errors=[f"Ranking adapter received no rows for `{report_name}`."],
		)
	entity_dimension, entity_fields = _history_entity_dimension_fields(compiler_contract)
	metric_key, metric_label, source_fields = _history_metric_choice(compiler_contract)
	aggregated: Dict[str, Dict[str, Any]] = {}
	for row in rows:
		entity = ""
		for fieldname in entity_fields:
			entity = str(row.get(fieldname) or "").strip()
			if entity:
				break
		if not entity:
			continue
		entry = aggregated.setdefault(entity, {"entity": entity, "sales_amount": 0.0, "quantity": 0.0})
		source_value = 0.0
		for fieldname in source_fields:
			if fieldname in row:
				source_value = _numeric_value(row.get(fieldname))
				entry[metric_key] = float(entry.get(metric_key) or 0.0) + source_value
				break
		if metric_key != "sales_amount" and ("billed_amount" in row or "amount" in row):
			entry["sales_amount"] = float(entry.get("sales_amount") or 0.0) + _numeric_value(row.get("billed_amount") or row.get("amount"))
		elif metric_key == "sales_amount":
			entry["sales_amount"] = float(entry.get("sales_amount") or 0.0) + source_value
		if metric_key != "quantity" and ("delivered_quantity" in row or "quantity" in row):
			entry["quantity"] = float(entry.get("quantity") or 0.0) + _numeric_value(row.get("delivered_quantity") or row.get("quantity"))
		elif metric_key == "quantity":
			entry["quantity"] = float(entry.get("quantity") or 0.0) + source_value
	if not aggregated:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="ranking_analytics",
			report_name=report_name,
			errors=[f"Ranking adapter could not aggregate any `{entity_dimension}` rows for `{report_name}`."],
		)
	filters = _report_filters(report_tool, result)
	period = _period_from_filters(filters)
	available_metric_keys = ["sales_amount", "quantity", "contribution_percent"]
	metric_key = _requested_metric_key_from_contract(compiler_contract, available_metric_keys, metric_key)
	metric_label = _metric_label(metric_key, metric_label)
	ranked_rows = _sort_ranked_rows(list(aggregated.values()), metric_key)
	contribution_metric_key = "sales_amount" if any(_numeric_value(row.get("sales_amount")) for row in ranked_rows) else metric_key
	ranked_rows = _add_contribution_percent(ranked_rows, base_metric_key=contribution_metric_key)
	total_value = sum(_numeric_value(row.get(metric_key)) for row in ranked_rows)
	top_row = ranked_rows[0] if ranked_rows else {}
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="ranking_analytics",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions=_analytical_dimensions(
			family_id="ranking_analytics",
			report_name=report_name,
			dimensions=_apply_ranking_request_hints({
				"entity_dimension": entity_dimension,
				"primary_metric_key": metric_key,
				"primary_metric_label": metric_label,
				"source_grain": "aggregated_sales_history",
			},
				compiler_contract=compiler_contract,
				available_metric_keys=available_metric_keys,
				default_metric_key=metric_key,
				entity_dimension=entity_dimension,
			),
		),
		metrics={
			metric_key: total_value,
			"entity_count": len(ranked_rows),
			"top_value": _numeric_value(top_row.get(metric_key)),
		},
		sections={
			"ranked_rows": ranked_rows,
			"summary": _ranking_summary(
				metric_key,
				metric_label,
				total_value,
				str(top_row.get("entity") or "").strip(),
				_numeric_value(top_row.get(metric_key)),
			),
		},
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="ranking_analytics",
		report_name=report_name,
		artifact_contract=artifact,
	)


def _stock_dimension_fields(compiler_contract: Dict[str, Any], report_name: str) -> Tuple[str, Tuple[str, ...]]:
	requested = _requested_dimension_keys(compiler_contract)
	if "warehouse" in requested or "warehouse_wise" in _normalize_key(report_name):
		return "Warehouse", ("warehouse",)
	return "Item", ("item_name", "item_code", "item")


def _stock_metric_choice(compiler_contract: Dict[str, Any]) -> Tuple[str, str, Tuple[str, ...]]:
	requested = _requested_metric_keys(compiler_contract)
	if requested & {"balance_value", "balance_value_mmk", "value"}:
		return "balance_value", "Balance Value", ("balance_value", "bal_val", "stock_value")
	return "balance_qty", "Balance Qty", ("balance_qty", "bal_qty", "qty_after_transaction")


def _build_stock_ranking(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	rows = [row for row in _report_rows(result) if isinstance(row, dict)]
	if not rows:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="ranking_analytics",
			report_name=report_name,
			errors=[f"Ranking adapter received no rows for `{report_name}`."],
		)
	entity_dimension, entity_fields = _stock_dimension_fields(compiler_contract, report_name)
	metric_key, metric_label, source_fields = _stock_metric_choice(compiler_contract)
	aggregated: Dict[str, Dict[str, Any]] = {}
	for row in rows:
		entity = ""
		for fieldname in entity_fields:
			entity = str(row.get(fieldname) or "").strip()
			if entity:
				break
		if not entity:
			continue
		entry = aggregated.setdefault(entity, {"entity": entity, metric_key: 0.0})
		for fieldname in source_fields:
			if fieldname in row:
				entry[metric_key] = float(entry.get(metric_key) or 0.0) + _numeric_value(row.get(fieldname))
				break
	if not aggregated:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="ranking_analytics",
			report_name=report_name,
			errors=[f"Ranking adapter could not aggregate any stock rows for `{report_name}`."],
		)
	filters = _report_filters(report_tool, result)
	period = _period_from_filters(filters)
	available_metric_keys = ["balance_qty", "balance_value", "contribution_percent"]
	metric_key = _requested_metric_key_from_contract(compiler_contract, available_metric_keys, metric_key)
	metric_label = _metric_label(metric_key, metric_label)
	ranked_rows = _sort_ranked_rows(list(aggregated.values()), metric_key)
	ranked_rows = _add_contribution_percent(ranked_rows, base_metric_key=metric_key)
	total_value = sum(_numeric_value(row.get(metric_key)) for row in ranked_rows)
	top_row = ranked_rows[0] if ranked_rows else {}
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="ranking_analytics",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions=_analytical_dimensions(
			family_id="ranking_analytics",
			report_name=report_name,
			dimensions=_apply_ranking_request_hints({
				"entity_dimension": entity_dimension,
				"primary_metric_key": metric_key,
				"primary_metric_label": metric_label,
				"source_grain": "inventory_snapshot",
			},
				compiler_contract=compiler_contract,
				available_metric_keys=available_metric_keys,
				default_metric_key=metric_key,
				entity_dimension=entity_dimension,
			),
		),
		metrics={
			metric_key: total_value,
			"entity_count": len(ranked_rows),
			"top_value": _numeric_value(top_row.get(metric_key)),
		},
		sections={
			"ranked_rows": ranked_rows,
			"summary": _ranking_summary(
				metric_key,
				metric_label,
				total_value,
				str(top_row.get("entity") or "").strip(),
				_numeric_value(top_row.get(metric_key)),
			),
		},
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="ranking_analytics",
		report_name=report_name,
		artifact_contract=artifact,
	)


def _build_ranking_artifact(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	report_key = _normalize_key(report_name)
	if report_key == "sales_analytics":
		return _build_sales_analytics_ranking(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	if report_key in {"accounts_payable_summary", "accounts_receivable_summary"}:
		return _build_aging_ranking(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	if report_key == "gross_profit":
		return _build_gross_profit_ranking(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	if report_key == "item_wise_sales_history":
		return _build_item_history_ranking(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	if report_key in {"stock_balance", "warehouse_wise_stock_balance"}:
		return _build_stock_ranking(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	return FamilyArtifactOutcome(
		status="unsupported_family_report",
		family_id="ranking_analytics",
		report_name=report_name,
		errors=[f"Unsupported ranking analytics report: `{report_name}`."],
	)


def _build_sales_analytics_trend(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	columns = _report_columns(result)
	rows = [row for row in _report_rows(result) if isinstance(row, dict) and not _is_total_like_row(row)]
	total_row = _report_total_row_map(result)
	filters = _report_filters(report_tool, result)
	requested_metrics = _requested_metric_keys(compiler_contract)
	if _normalize_key(filters.get("value_quantity")) == "quantity" or requested_metrics & {"quantity", "qty", "delivered_quantity"}:
		metric_key = "quantity"
		metric_label = _requested_metric_label_from_contract(
			compiler_contract,
			metric_key,
			"Quantity",
		)
		total_fields = ("total(qty)", "total_qty", "total")
	else:
		metric_key = "sales_amount"
		metric_label = _requested_metric_label_from_contract(
			compiler_contract,
			metric_key,
			"Sales Amount",
		)
		total_fields = ("total(amt)", "total_amt", "total")
	period_fields = _period_field_specs(columns, metric_key=metric_key)
	if not period_fields:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="trend_analytics",
			report_name=report_name,
			errors=[f"Trend adapter could not detect any governed period columns for `{report_name}`."],
		)
	period_series: List[Dict[str, Any]] = []
	for fieldname, label in period_fields:
		value = _numeric_value(total_row.get(fieldname))
		if value == 0.0:
			value = sum(_numeric_value(row.get(fieldname)) for row in rows)
		period_series.append(
			{
				"period_key": fieldname,
				"label": label,
				"value": value,
			}
		)
	total_value = 0.0
	for fieldname in total_fields:
		total_value = _numeric_value(total_row.get(fieldname))
		if total_value:
			break
	if total_value == 0.0:
		total_value = sum(_numeric_value(item.get("value")) for item in period_series)
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="trend_analytics",
		source_reports=[report_name],
		period=_period_from_filters(filters),
		filters=filters,
		dimensions=_analytical_dimensions(
			family_id="trend_analytics",
			report_name=report_name,
			dimensions={
				"time_grain": _time_grain_from_filters(filters),
				"primary_metric_key": metric_key,
				"primary_metric_label": metric_label,
				"series_dimension": str(filters.get("tree_type") or "").strip(),
				"source_grain": "period_total",
			},
		),
		metrics={
			metric_key: total_value,
			"period_count": len(period_series),
		},
		sections={
			"period_series": period_series,
			"summary": [
				{"label": f"Total {metric_label}", "metric_key": metric_key, "amount": total_value},
				{"label": "Period Count", "metric_key": "period_count", "value": len(period_series)},
			],
		},
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="trend_analytics",
		report_name=report_name,
		artifact_contract=artifact,
	)


def _build_item_history_trend(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	rows = [row for row in _report_rows(result) if isinstance(row, dict)]
	if not rows:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="trend_analytics",
			report_name=report_name,
			errors=[f"Trend adapter received no rows for `{report_name}`."],
		)
	metric_key, metric_label, source_fields = _history_metric_choice(compiler_contract)
	aggregated: Dict[str, float] = {}
	for row in rows:
		date_text = str(row.get("transaction_date") or "").strip()
		if not date_text:
			continue
		try:
			date_value = dt.date.fromisoformat(date_text)
		except Exception:
			continue
		period_key = f"{date_value.year:04d}-{date_value.month:02d}"
		amount = 0.0
		for fieldname in source_fields:
			if fieldname in row:
				amount = _numeric_value(row.get(fieldname))
				break
		aggregated[period_key] = float(aggregated.get(period_key) or 0.0) + amount
	if not aggregated:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="trend_analytics",
			report_name=report_name,
			errors=[f"Trend adapter could not aggregate any period values for `{report_name}`."],
		)
	period_series = [
		{
			"period_key": period_key,
			"label": _format_period_label(period_key),
			"value": value,
		}
		for period_key, value in sorted(aggregated.items())
	]
	total_value = sum(item["value"] for item in period_series)
	filters = _report_filters(report_tool, result)
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="trend_analytics",
		source_reports=[report_name],
		period=_period_from_filters(filters),
		filters=filters,
		dimensions=_analytical_dimensions(
			family_id="trend_analytics",
			report_name=report_name,
			dimensions={
				"time_grain": "monthly",
				"primary_metric_key": metric_key,
				"primary_metric_label": metric_label,
				"source_grain": "aggregated_history",
			},
		),
		metrics={
			metric_key: total_value,
			"period_count": len(period_series),
		},
		sections={
			"period_series": period_series,
			"summary": [
				{"label": f"Total {metric_label}", "metric_key": metric_key, "amount": total_value},
				{"label": "Period Count", "metric_key": "period_count", "value": len(period_series)},
			],
		},
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="trend_analytics",
		report_name=report_name,
		artifact_contract=artifact,
	)


def _build_trend_artifact(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	report_key = _normalize_key(report_name)
	if report_key in {"sales_analytics", "delivery_note_trends"}:
		return _build_sales_analytics_trend(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	if report_key == "item_wise_sales_history":
		return _build_item_history_trend(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	return FamilyArtifactOutcome(
		status="unsupported_family_report",
		family_id="trend_analytics",
		report_name=report_name,
		errors=[f"Unsupported trend analytics report: `{report_name}`."],
	)


def _build_inventory_snapshot_artifact(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	all_rows = [row for row in _report_rows(result) if isinstance(row, dict)]
	if not all_rows:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="inventory_snapshot",
			report_name=report_name,
			errors=[f"Inventory snapshot adapter received no rows for `{report_name}`."],
		)
	report_key = _normalize_key(report_name)
	rows = [
		row
		for row in all_rows
		if not (
			_is_total_label(row.get("item_code"))
			or _is_total_label(row.get("item_name"))
			or _is_total_label(row.get("warehouse"))
		)
	]
	if not rows:
		rows = all_rows
	filters = _report_filters(report_tool, result)
	period = _snapshot_period(filters)
	requested_dimensions = _requested_dimension_keys(compiler_contract)
	if report_key == "warehouse_wise_stock_balance" and any("stock_balance" in row for row in all_rows):
		snapshot_rows = [
			{
				"warehouse": _first_text(row, "warehouse", "name"),
				"parent_warehouse": _first_text(row, "parent_warehouse"),
				"balance_qty": _stock_balance_qty(row),
				"balance_value": _numeric_value(row.get("stock_balance")),
				"is_group": bool(row.get("is_group")),
				"indent": int(_numeric_value(row.get("indent"))),
			}
			for row in all_rows
			if _first_text(row, "warehouse", "name")
		]
		if not snapshot_rows:
			return FamilyArtifactOutcome(
				status="adapter_error",
				family_id="inventory_snapshot",
				report_name=report_name,
				errors=[f"Inventory snapshot adapter could not normalize any warehouse rows for `{report_name}`."],
			)
		total_row = next(
			(
				row for row in snapshot_rows
				if bool(row.get("is_group")) and int(row.get("indent") or 0) == 0
			),
			{},
		)
		warehouse_totals = [
			row for row in snapshot_rows
			if str(row.get("warehouse") or "").strip()
		]
		total_balance_value = _numeric_value(total_row.get("balance_value"))
		if total_balance_value == 0.0:
			total_balance_value = sum(
				_numeric_value(row.get("balance_value"))
				for row in warehouse_totals
				if not bool(row.get("is_group"))
			)
		total_balance_qty = sum(
			_numeric_value(row.get("balance_qty"))
			for row in warehouse_totals
			if not bool(row.get("is_group"))
		)
		artifact = build_normalized_family_artifact_contract(
			request_id=request_id,
			family_id="inventory_snapshot",
			source_reports=[report_name],
			period=period,
			filters=filters,
			dimensions=_analytical_dimensions(
				family_id="inventory_snapshot",
				report_name=report_name,
				dimensions={
					"snapshot_dimension": "Warehouse",
					"source_grain": "warehouse_tree_snapshot",
				},
			),
			metrics={
				"balance_qty": total_balance_qty,
				"balance_value": total_balance_value,
				"item_count": 0,
				"warehouse_count": len([row for row in warehouse_totals if not bool(row.get("is_group"))]),
				"row_count": len(snapshot_rows),
			},
			sections={
				"snapshot_rows": snapshot_rows,
				"item_totals": [],
				"warehouse_totals": warehouse_totals,
				"summary": [
					{"label": "Total Balance Qty", "metric_key": "balance_qty", "amount": total_balance_qty},
					{"label": "Total Balance Value", "metric_key": "balance_value", "amount": total_balance_value},
					{"label": "Warehouse Count", "metric_key": "warehouse_count", "value": len([row for row in warehouse_totals if not bool(row.get("is_group"))])},
				],
			},
		)
		return FamilyArtifactOutcome(
			status="adapted",
			family_id="inventory_snapshot",
			report_name=report_name,
			artifact_contract=artifact,
		)
	snapshot_dimension = "Warehouse" if ("warehouse" in requested_dimensions or "warehouse_wise" in _normalize_key(report_name)) else "Item"
	snapshot_rows = [_stock_snapshot_row_entry(row) for row in rows]
	snapshot_rows = [
		row
		for row in snapshot_rows
		if str(row.get("item_code") or row.get("item") or row.get("warehouse") or "").strip()
	]
	if not snapshot_rows:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="inventory_snapshot",
			report_name=report_name,
			errors=[f"Inventory snapshot adapter could not normalize any stock rows for `{report_name}`."],
		)
	total_balance_qty = sum(_numeric_value(row.get("balance_qty")) for row in snapshot_rows)
	total_balance_value = sum(_numeric_value(row.get("balance_value")) for row in snapshot_rows)
	item_totals = _aggregate_snapshot_dimension(
		snapshot_rows,
		label_key="item",
		label_fieldnames=("item_code", "item_name", "item"),
	)
	warehouse_totals = _aggregate_snapshot_dimension(
		snapshot_rows,
		label_key="warehouse",
		label_fieldnames=("warehouse",),
	)
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="inventory_snapshot",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions=_analytical_dimensions(
			family_id="inventory_snapshot",
			report_name=report_name,
			dimensions={
				"snapshot_dimension": snapshot_dimension,
				"source_grain": "warehouse_item_snapshot" if _normalize_key(report_name) == "warehouse_wise_stock_balance" else "item_snapshot",
			},
		),
		metrics={
			"balance_qty": total_balance_qty,
			"balance_value": total_balance_value,
			"item_count": len([row for row in item_totals if str(row.get("item") or "").strip()]),
			"warehouse_count": len([row for row in warehouse_totals if str(row.get("warehouse") or "").strip()]),
			"row_count": len(snapshot_rows),
		},
		sections={
			"snapshot_rows": snapshot_rows,
			"item_totals": item_totals,
			"warehouse_totals": warehouse_totals,
			"summary": [
				{"label": "Total Balance Qty", "metric_key": "balance_qty", "amount": total_balance_qty},
				{"label": "Total Balance Value", "metric_key": "balance_value", "amount": total_balance_value},
				{"label": "Item Count", "metric_key": "item_count", "value": len(item_totals)},
				{"label": "Warehouse Count", "metric_key": "warehouse_count", "value": len(warehouse_totals)},
			],
		},
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="inventory_snapshot",
		report_name=report_name,
		artifact_contract=artifact,
	)


def _product_primary_metric_key(
	compiler_contract: Dict[str, Any],
	available_metrics: List[str],
) -> Tuple[str, str]:
	options = [
		({"gross_profit_percent", "gross_profit_percentage"}, ("gross_profit_percent", "Gross Profit Percent")),
		({"gross_profit"}, ("gross_profit", "Gross Profit")),
		({"sales_amount", "selling_amount", "billed_amount", "revenue", "value"}, ("sales_amount", "Sales Amount")),
		({"quantity", "qty", "delivered_quantity"}, ("quantity", "Quantity")),
	]
	requested = _requested_metric_keys(compiler_contract)
	for aliases, metric in options:
		if metric[0] in available_metrics and requested & aliases:
			return metric
	if "gross_profit" in available_metrics:
		return "gross_profit", "Gross Profit"
	if "sales_amount" in available_metrics:
		return "sales_amount", "Sales Amount"
	return "quantity", "Quantity"


def _gross_profit_product_rows(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
	total_row = next(
		(
			row
			for row in rows
			if _is_total_label(row.get("item_code")) or _is_total_label(row.get("item_name"))
		),
		{},
	)
	product_rows = [
		{
			"item": _first_text(row, "item_name", "item_code"),
			"item_code": _first_text(row, "item_code"),
			"item_name": _first_text(row, "item_name", "item_code"),
			"item_group": _first_text(row, "item_group"),
			"brand": _first_text(row, "brand"),
			"warehouse": _first_text(row, "warehouse"),
			"sales_amount": _numeric_value(row.get("selling_amount")),
			"buying_amount": _numeric_value(row.get("buying_amount")),
			"gross_profit": _numeric_value(row.get("gross_profit")),
			"gross_profit_percent": _numeric_value(row.get("gross_profit_%")),
			"quantity": _numeric_value(row.get("qty")),
		}
		for row in rows
		if not (_is_total_label(row.get("item_code")) or _is_total_label(row.get("item_name")))
	]
	return product_rows, total_row if isinstance(total_row, dict) else {}


def _item_history_product_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	aggregated: Dict[str, Dict[str, Any]] = {}
	for row in rows:
		item_code = _first_text(row, "item_code", "item")
		item_name = _first_text(row, "item_name", "item_code", "item")
		item_key = item_code or item_name
		if not item_key:
			continue
		entry = aggregated.setdefault(
			item_key,
			{
				"item": item_name or item_code,
				"item_code": item_code,
				"item_name": item_name or item_code,
				"item_group": _first_text(row, "item_group"),
				"sales_amount": 0.0,
				"quantity": 0.0,
			},
		)
		entry["sales_amount"] = float(entry.get("sales_amount") or 0.0) + _numeric_value(row.get("billed_amount") or row.get("amount"))
		entry["quantity"] = float(entry.get("quantity") or 0.0) + _numeric_value(row.get("delivered_quantity") or row.get("quantity"))
	return list(aggregated.values())


def _build_product_profitability_artifact(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	rows = [row for row in _report_rows(result) if isinstance(row, dict)]
	if not rows:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="product_profitability",
			report_name=report_name,
			errors=[f"Product profitability adapter received no rows for `{report_name}`."],
		)
	report_key = _normalize_key(report_name)
	filters = _report_filters(report_tool, result)
	period = _period_from_filters(filters)
	product_rows: List[Dict[str, Any]] = []
	metrics: Dict[str, Any] = {}
	dimensions: Dict[str, Any] = {}
	if report_key == "gross_profit":
		product_rows, total_row = _gross_profit_product_rows(rows)
		if not product_rows:
			product_rows = _gross_profit_product_rows(rows + [total_row])[0]
		total_sales_amount = _numeric_value(total_row.get("selling_amount")) or sum(_numeric_value(row.get("sales_amount")) for row in product_rows)
		total_buying_amount = _numeric_value(total_row.get("buying_amount")) or sum(_numeric_value(row.get("buying_amount")) for row in product_rows)
		total_gross_profit = _numeric_value(total_row.get("gross_profit")) or sum(_numeric_value(row.get("gross_profit")) for row in product_rows)
		total_quantity = _numeric_value(total_row.get("qty")) or sum(_numeric_value(row.get("quantity")) for row in product_rows)
		total_gross_profit_percent = (
			(total_gross_profit / total_sales_amount) * 100.0
			if total_sales_amount > 0
			else _numeric_value(total_row.get("gross_profit_%"))
		)
		metrics = {
			"sales_amount": total_sales_amount,
			"buying_amount": total_buying_amount,
			"gross_profit": total_gross_profit,
			"gross_profit_percent": total_gross_profit_percent,
			"quantity": total_quantity,
			"product_count": len(product_rows),
		}
		dimensions = {
			"product_dimension": str(filters.get("group_by") or "Item Code").strip() or "Item Code",
			"source_grain": "grouped_profitability",
		}
	elif report_key == "item_wise_sales_history":
		product_rows = _item_history_product_rows(rows)
		total_sales_amount = sum(_numeric_value(row.get("sales_amount")) for row in product_rows)
		total_quantity = sum(_numeric_value(row.get("quantity")) for row in product_rows)
		metrics = {
			"sales_amount": total_sales_amount,
			"quantity": total_quantity,
			"product_count": len(product_rows),
		}
		dimensions = {
			"product_dimension": "Item",
			"source_grain": "aggregated_sales_history",
		}
	else:
		return FamilyArtifactOutcome(
			status="unsupported_family_report",
			family_id="product_profitability",
			report_name=report_name,
			errors=[f"Unsupported product profitability report: `{report_name}`."],
		)
	product_rows = [row for row in product_rows if str(row.get("item_code") or row.get("item_name") or row.get("item") or "").strip()]
	if not product_rows:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="product_profitability",
			report_name=report_name,
			errors=[f"Product profitability adapter could not normalize any product rows for `{report_name}`."],
		)
	available_metrics = [str(key or "").strip() for key in metrics.keys() if str(key or "").strip()]
	primary_metric_key, primary_metric_label = _product_primary_metric_key(compiler_contract, available_metrics)
	primary_metric_key = _requested_metric_key_from_contract(compiler_contract, available_metrics, primary_metric_key)
	primary_metric_label = _metric_label(primary_metric_key, primary_metric_label)
	product_rows = _sort_metric_rows(product_rows, primary_metric_key)
	contribution_metric_key = "sales_amount" if any(_numeric_value(row.get("sales_amount")) for row in product_rows) else primary_metric_key
	product_rows = _add_contribution_percent(product_rows, base_metric_key=contribution_metric_key)
	top_row = product_rows[0] if product_rows else {}
	dimensions["primary_metric_key"] = primary_metric_key
	dimensions["primary_metric_label"] = primary_metric_label
	dimensions = _apply_ranking_request_hints(
		dimensions,
		compiler_contract=compiler_contract,
		available_metric_keys=available_metrics + ["contribution_percent"],
		default_metric_key=primary_metric_key,
		entity_dimension="Product",
	)
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="product_profitability",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions=_analytical_dimensions(
			family_id="product_profitability",
			report_name=report_name,
			dimensions=dimensions,
		),
		metrics=metrics,
		sections={
			"product_rows": product_rows,
			"summary": [
				{"label": f"Total {primary_metric_label}", "metric_key": primary_metric_key, "amount": _numeric_value(metrics.get(primary_metric_key))},
				{"label": "Product Count", "metric_key": "product_count", "value": len(product_rows)},
				{"label": "Top Product", "metric_key": "top_product", "value": str(top_row.get("item_name") or top_row.get("item") or "").strip()},
				{"label": f"Top {primary_metric_label}", "metric_key": "top_value", "amount": _numeric_value(top_row.get(primary_metric_key))},
			],
		},
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="product_profitability",
		report_name=report_name,
		artifact_contract=artifact,
	)


def _family_preference_order(intent_class: str) -> List[str]:
	return {
		"financial_statement": ["financial_statement"],
		"aging_analysis": ["aging"],
		"ranked_entities": ["ranking_analytics", "aging", "inventory_snapshot", "product_profitability"],
		"trend_analysis": ["trend_analytics", "product_profitability"],
		"inventory_summary": ["inventory_snapshot"],
		"product_performance": ["product_profitability", "ranking_analytics", "trend_analytics"],
		"transaction_listing": ["transaction_listing"],
		"financial_summary": ["financial_statement", "aging", "inventory_snapshot", "product_profitability"],
	}.get(str(intent_class or "").strip(), [])


def _resolve_target_family_id(
	report_name: str,
	family_ids: List[str],
	intent_class: str,
	preferred_family_id: str,
) -> str:
	candidates = [str(value or "").strip() for value in family_ids if str(value or "").strip()]
	if not candidates:
		return ""
	if preferred_family_id and preferred_family_id in candidates:
		return preferred_family_id
	if len(candidates) == 1:
		return candidates[0]
	for family_id in _family_preference_order(intent_class):
		if family_id in candidates:
			return family_id
	return candidates[0]


@dataclass(frozen=True)
class FamilyArtifactOutcome:
	status: str
	family_id: str
	report_name: str
	artifact_contract: NormalizedFamilyArtifactContract | None = None
	errors: List[str] = field(default_factory=list)
	warnings: List[str] = field(default_factory=list)

	def to_payload(self) -> Dict[str, Any]:
		return {
			"type": "qwen_family_artifact_outcome",
			"contract_version": "1.0",
			"status": self.status,
			"family_id": self.family_id,
			"report_name": self.report_name,
			"errors": list(self.errors),
			"warnings": list(self.warnings),
			"artifact": self.artifact_contract.to_payload() if self.artifact_contract else {},
		}


def _build_financial_statement_artifact(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	rows = _report_rows(result)
	if not rows:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="financial_statement",
			report_name=report_name,
			errors=[f"Financial statement adapter received no report rows for `{report_name}`."],
		)
	statement_type = _statement_type_for_report(report_name)
	if not statement_type:
		return FamilyArtifactOutcome(
			status="unsupported_family_report",
			family_id="financial_statement",
			report_name=report_name,
			errors=[f"Unsupported financial statement report: `{report_name}`."],
		)
	filters = _report_filters(report_tool, result)
	period = _period_from_filters(filters)
	columns = _report_columns(result)
	currency = ""
	for row in rows:
		currency = str(row.get("currency") or "").strip()
		if currency:
			break
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="financial_statement",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions=_analytical_dimensions(
			family_id="financial_statement",
			report_name=report_name,
			dimensions={
				"statement_type": statement_type,
				"currency": currency,
				"periodicity": str(filters.get("periodicity") or "").strip(),
				"value_column": _value_fieldname(columns),
			},
		),
		metrics=_financial_statement_metrics(statement_type, rows),
		sections=_financial_statement_sections(statement_type, rows),
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="financial_statement",
		report_name=report_name,
		artifact_contract=artifact,
	)


def _build_aging_artifact(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	rows = _report_rows(result)
	if not rows:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="aging",
			report_name=report_name,
			errors=[f"Aging adapter received no report rows for `{report_name}`."],
		)
	aging_type = _aging_type_for_report(report_name)
	if not aging_type:
		return FamilyArtifactOutcome(
			status="unsupported_family_report",
			family_id="aging",
			report_name=report_name,
			errors=[f"Unsupported aging report: `{report_name}`."],
		)
	filters = _report_filters(report_tool, result)
	period = _period_from_filters(filters)
	filter_mode = _aging_filter_mode(compiler_contract)
	if filter_mode:
		rows = _filter_aging_rows(rows, filter_mode=filter_mode)
	currency = ""
	for row in rows:
		currency = str(row.get("currency") or "").strip()
		if currency:
			break
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="aging",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions=_analytical_dimensions(
			family_id="aging",
			report_name=report_name,
			dimensions={
				"aging_type": aging_type,
				"currency": currency,
				"party_dimension_label": _aging_party_dimension_label(aging_type),
				"source_grain": "summary" if "summary" in _normalize_key(report_name) else "detail",
				"bucket_labels": [label for _, label, _ in _aging_bucket_specs()],
				"filter_mode": filter_mode,
			},
		),
		metrics=_aging_metrics(rows, aging_type),
		sections=_aging_sections(rows, aging_type, currency),
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="aging",
		report_name=report_name,
		artifact_contract=artifact,
	)


def _requested_transaction_columns(
	compiler_contract: Dict[str, Any],
	*,
	available_metric_keys: List[str] | None = None,
	primary_metric_key: str = "",
) -> List[str]:
	requested_dimensions = set(
		_canonical_requested_values(
			compiler_contract,
			"requested_dimensions",
			dimension_or_metric="dimension",
		)
	)
	requested_metrics = set(
		_canonical_requested_values(
			compiler_contract,
			"requested_metrics",
			dimension_or_metric="metric",
		)
	)
	columns: List[str] = []
	available = {
		str(value or "").strip()
		for value in (available_metric_keys or [])
		if str(value or "").strip()
	}
	if "document_name" in requested_dimensions:
		columns.append("document_name")
	if requested_dimensions.intersection({"posting_date", "transaction_date"}):
		columns.append("posting_date")
	if "delivery_date" in requested_dimensions:
		columns.append("delivery_date")
	if "schedule_date" in requested_dimensions:
		columns.append("schedule_date")
	if "customer" in requested_dimensions:
		columns.append("customer")
	elif requested_dimensions.intersection({"supplier", "party"}):
		columns.append("party_name")
	metric_column_map = {
		"grand_total": "grand_total",
		"sales_amount": "grand_total",
		"received_amount": "received_amount",
		"total_allocated_amount": "total_allocated_amount",
		"paid_amount": "paid_amount",
	}
	for metric_key, column_name in metric_column_map.items():
		if metric_key in requested_metrics and (not available or column_name in available):
			columns.append(column_name)
	if requested_metrics.intersection({"quantity"}):
		columns.append("quantity")
	if requested_metrics.intersection({"outstanding_amount", "outstanding_total"}):
		columns.append("outstanding_amount")
	if requested_dimensions.intersection({"document_status", "status"}):
		columns.append("status")
	if not columns and primary_metric_key and (not available or primary_metric_key in available):
		columns.append(primary_metric_key)
	return list(dict.fromkeys([value for value in columns if value]))


def _transaction_listing_default_metric_keys(
	report_name: str,
	compiler_contract: Dict[str, Any],
) -> List[str]:
	capability_id = str(compiler_contract.get("capability_id") or "").strip()
	report_spec = get_report_spec(report_name)
	if not capability_id:
		capability_ids = report_spec.get("capability_ids") if isinstance(report_spec.get("capability_ids"), list) else []
		for value in capability_ids:
			capability_id = str(value or "").strip()
			if capability_id:
				break
	if not capability_id:
		return []
	defaults = capability_fresh_query_defaults(capability_id, intent_class="transaction_listing")
	default_metrics = defaults.get("default_metrics") if isinstance(defaults.get("default_metrics"), list) else []
	out: List[str] = []
	for value in default_metrics:
		raw = str(value or "").strip()
		if not raw:
			continue
		canonical = get_canonical_key(
			raw,
			capability_id=capability_id,
			dimension_or_metric="metric",
		)
		metric_key = str(canonical or _clean_metric_key(raw)).strip()
		if metric_key:
			out.append(metric_key)
	return list(dict.fromkeys(out))


def _transaction_listing_amount_metric_context(
	report_name: str,
	rows: List[Dict[str, Any]],
	compiler_contract: Dict[str, Any],
) -> Tuple[str, str]:
	report_spec = get_report_spec(report_name)
	direct_query = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
	direct_fields = {
		str(value or "").strip()
		for value in (direct_query.get("fields") or [])
		if str(value or "").strip()
	}
	available_metric_keys: List[str] = []
	for candidate in ["grand_total", "received_amount", "total_allocated_amount", "paid_amount"]:
		if candidate in direct_fields or any(isinstance(row, dict) and candidate in row for row in rows):
			available_metric_keys.append(candidate)
	if not available_metric_keys:
		return "grand_total", "Grand Total"
	default_metric_key = ""
	for candidate in _transaction_listing_default_metric_keys(report_name, compiler_contract):
		if candidate in available_metric_keys:
			default_metric_key = candidate
			break
	if not default_metric_key:
		for candidate in ["grand_total", "received_amount", "total_allocated_amount", "paid_amount"]:
			if candidate in available_metric_keys:
				default_metric_key = candidate
				break
	primary_metric_key = _requested_metric_key_from_contract(
		compiler_contract,
		available_metric_keys,
		default_metric_key,
	)
	if not primary_metric_key:
		primary_metric_key = default_metric_key
	primary_metric_label = _requested_metric_label_from_contract(
		compiler_contract,
		primary_metric_key,
		_metric_label(primary_metric_key, "Value"),
	)
	return primary_metric_key, primary_metric_label


def _requested_master_directory_columns(
	compiler_contract: Dict[str, Any],
	*,
	entity_type: str,
) -> List[str]:
	extracted_slots = (
		dict(compiler_contract.get("extracted_slots"))
		if isinstance(compiler_contract.get("extracted_slots"), dict)
		else {}
	)
	lookup_projection = str(extracted_slots.get("lookup_projection") or "").strip()
	requested_dimensions = set(
		_canonical_requested_values(
			compiler_contract,
			"requested_dimensions",
			dimension_or_metric="dimension",
		)
	)
	return requested_master_directory_columns(
		requested_dimensions=requested_dimensions,
		lookup_projection=lookup_projection,
		entity_type=entity_type,
	)


def _master_directory_requested_column_alias_map(entity_type: str) -> Dict[str, str]:
	return master_directory_requested_column_alias_map(entity_type)


def _master_directory_context(report_name: str) -> Dict[str, str]:
	return master_directory_context(report_name)


def _transaction_listing_context(report_name: str, rows: List[Dict[str, Any]]) -> Dict[str, str]:
	report_spec = get_report_spec(report_name)
	direct_query = report_spec.get("direct_query") if isinstance(report_spec.get("direct_query"), dict) else {}
	doctype = str(direct_query.get("doctype") or "").strip()
	date_field = str(direct_query.get("date_field") or "").strip()
	document_label = doctype or str(report_name or "").replace(" List", "").strip()
	transaction_type = _normalize_key(doctype) or _normalize_key(document_label)
	party_field = ""
	party_label = "Party"
	for candidate, label in (("customer", "Customer"), ("supplier", "Supplier"), ("party", "Party")):
		if any(str(row.get(candidate) or "").strip() for row in rows):
			party_field = candidate
			party_label = label
			break
	return {
		"document_label": document_label or "Document",
		"transaction_type": transaction_type or "document",
		"party_field": party_field,
		"party_label": party_label,
		"date_label": "Transaction Date" if date_field == "transaction_date" else "Posting Date",
	}


def _transaction_listing_requested_column_alias_map(context: Dict[str, str]) -> Dict[str, str]:
	transaction_type = _normalize_key(context.get("transaction_type") or "")
	document_label = _normalize_key(context.get("document_label") or "")
	aliases: Dict[str, str] = {
		"document": "document_name",
		"document_name": "document_name",
		"name": "document_name",
		"id": "document_name",
		"posting_date": "posting_date",
		"transaction_date": "posting_date",
		"date": "posting_date",
		"delivery_date": "delivery_date",
		"schedule_date": "schedule_date",
		"customer": "party_name",
		"supplier": "party_name",
		"party": "party_name",
		"party_name": "party_name",
		"amount": "grand_total",
		"grand_total": "grand_total",
		"total": "grand_total",
		"total_amount": "grand_total",
		"outstanding": "outstanding_amount",
		"outstanding_amount": "outstanding_amount",
		"received_amount": "received_amount",
		"total_allocated_amount": "total_allocated_amount",
		"paid_amount": "paid_amount",
		"quantity": "quantity",
		"qty": "quantity",
		"status": "status",
		"document_status": "status",
	}
	if transaction_type:
		aliases[transaction_type] = "document_name"
	if document_label:
		aliases[document_label] = "document_name"
	return aliases


def _build_transaction_listing_artifact(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	rows = [row for row in _report_rows(result) if isinstance(row, dict)]
	context = _transaction_listing_context(report_name, rows)
	if not context.get("document_label"):
		return FamilyArtifactOutcome(
			status="unsupported_family_report",
			family_id="transaction_listing",
			report_name=report_name,
			errors=[f"Unsupported transaction listing report: `{report_name}`."],
		)
	filters = _report_filters(report_tool, result)
	period = _period_from_filters(filters)
	party_field = str(context.get("party_field") or "").strip()
	primary_metric_key, primary_metric_label = _transaction_listing_amount_metric_context(
		report_name,
		rows,
		compiler_contract,
	)
	source_has_outstanding = any(isinstance(row, dict) and "outstanding_amount" in row for row in rows)
	document_rows = []
	aux_metric_keys = [
		candidate
		for candidate in ["grand_total", "received_amount", "total_allocated_amount", "paid_amount"]
		if candidate and candidate != primary_metric_key
	]
	for row in rows:
		if not isinstance(row, dict):
			continue
		document_name = str(row.get("name") or "").strip()
		if not document_name:
			continue
		document_row = {
			"document_name": str(row.get("name") or "").strip(),
			"posting_date": str(row.get("posting_date") or row.get("transaction_date") or "").strip(),
			"delivery_date": str(row.get("delivery_date") or "").strip(),
			"schedule_date": str(row.get("schedule_date") or "").strip(),
			"customer": str(row.get("customer") or "").strip(),
			"party_name": str(row.get(party_field) or "").strip() if party_field else "",
			"quantity": _numeric_value(row.get("total_qty") if row.get("total_qty") not in (None, "") else row.get("qty")),
			"status": str(row.get("status") or "").strip(),
			"docstatus": _numeric_value(row.get("docstatus")),
		}
		if primary_metric_key:
			document_row[primary_metric_key] = _numeric_value(row.get(primary_metric_key))
		metric_values = {
			candidate: _numeric_value(row.get(candidate))
			for candidate in aux_metric_keys
			if candidate in row
		}
		if metric_values:
			document_row["metric_values"] = metric_values
		if source_has_outstanding:
			document_row["outstanding_amount"] = _numeric_value(row.get("outstanding_amount"))
		document_rows.append(document_row)
	requested_top_n = _requested_top_n_from_contract(compiler_contract)
	if requested_top_n > 0:
		document_rows = document_rows[:requested_top_n]
	total_amount = sum(_numeric_value(row.get(primary_metric_key)) for row in document_rows)
	total_outstanding = sum(_numeric_value(row.get("outstanding_amount")) for row in document_rows)
	total_quantity = sum(_numeric_value(row.get("quantity")) for row in document_rows)
	has_explicit_projection_request = bool(
		_canonical_requested_values(
			compiler_contract,
			"requested_dimensions",
			dimension_or_metric="dimension",
		)
		or _canonical_requested_values(
			compiler_contract,
			"requested_metrics",
			dimension_or_metric="metric",
		)
	)
	requested_columns = _requested_transaction_columns(
		compiler_contract,
		available_metric_keys=[primary_metric_key] if primary_metric_key else [],
		primary_metric_key=primary_metric_key,
	)
	metrics = {
		"document_count": len(document_rows),
		"total_amount": total_amount,
	}
	if any(_numeric_value(row.get("outstanding_amount")) for row in document_rows):
		metrics["outstanding_amount"] = total_outstanding
	if any(_numeric_value(row.get("quantity")) for row in document_rows):
		metrics["quantity"] = total_quantity
	summary = [
		{"label": "Document Count", "metric_key": "document_count", "value": len(document_rows)},
		{
			"label": "Total Amount" if primary_metric_key == "grand_total" else _summary_total_metric_label(primary_metric_label),
			"metric_key": "total_amount",
			"amount": total_amount,
		},
	]
	if "quantity" in metrics:
		summary.insert(
			1,
			{"label": "Total Quantity", "metric_key": "quantity", "value": total_quantity},
		)
	if "outstanding_amount" in metrics:
		summary.append(
			{"label": "Outstanding Amount", "metric_key": "outstanding_amount", "amount": total_outstanding}
		)
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="transaction_listing",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions={
			"scope_id": context.get("transaction_type"),
			"transaction_type": context.get("transaction_type"),
			"document_entity_type": context.get("transaction_type"),
			"document_label": context.get("document_label"),
			"party_field": party_field,
			"party_label": context.get("party_label"),
			"date_label": context.get("date_label") or "Posting Date",
			"primary_metric_key": primary_metric_key or "grand_total",
			"primary_metric_label": primary_metric_label or "Grand Total",
			"metric_label_map": {
				"grand_total": "Grand Total",
				"received_amount": "Received Amount",
				"total_allocated_amount": "Total Allocated Amount",
				"paid_amount": "Paid Amount",
				"outstanding_amount": "Outstanding Amount",
				"quantity": "Quantity",
			},
			"requested_top_n": requested_top_n or len(document_rows),
			"requested_columns": requested_columns,
			"requested_column_alias_map": _transaction_listing_requested_column_alias_map(context),
			"has_explicit_projection_request": has_explicit_projection_request,
			"source_grain": "document_list",
		},
		metrics=metrics,
		sections={
			"transaction_rows": document_rows,
			"summary": summary,
		},
		warnings=(
			["No documents matched these filters."]
			if not document_rows
			else []
		),
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="transaction_listing",
		report_name=report_name,
		artifact_contract=artifact,
	)


def _build_master_data_directory_artifact(
	*,
	request_id: str,
	report_name: str,
	report_tool: Dict[str, Any],
	compiler_contract: Dict[str, Any],
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	rows = [row for row in _report_rows(result) if isinstance(row, dict)]
	filters = _report_filters(report_tool, result)
	period = _period_from_filters(filters)
	requested_top_n = _requested_top_n_from_contract(compiler_contract)
	context = _master_directory_context(report_name)
	directory_rows: List[Dict[str, Any]] = []
	for row in rows:
		entity_key = str(row.get("name") or "").strip()
		entity_label = str(row.get(context.get("name_field")) or "").strip() or entity_key
		if not entity_key and not entity_label:
			continue
		disabled = _numeric_value(row.get("disabled"))
		is_frozen = _numeric_value(row.get("is_frozen"))
		status = "Disabled" if disabled else ("Frozen" if is_frozen else "Active")
		directory_rows.append(
			{
				"entity": entity_label or entity_key,
				"entity_name": entity_label or entity_key,
				"entity_code": entity_key,
				"region": str(row.get(context.get("region_field")) or "").strip(),
				"group": str(row.get(context.get("group_field")) or "").strip(),
				"creation": str(row.get("creation") or "").strip()[:10],
				"status": status,
				"default_price_list": str(row.get("default_price_list") or "").strip(),
				"payment_terms": str(row.get("payment_terms") or "").strip(),
				"disabled": disabled,
				"is_frozen": is_frozen,
			}
		)
	if requested_top_n > 0:
		directory_rows = directory_rows[:requested_top_n]
	requested_columns = _requested_master_directory_columns(
		compiler_contract,
		entity_type=str(context.get("entity_type") or "").strip(),
	)
	extracted_slots = (
		dict(compiler_contract.get("extracted_slots"))
		if isinstance(compiler_contract.get("extracted_slots"), dict)
		else {}
	)
	entity_reference_resolution = (
		dict(extracted_slots.get("entity_reference_resolution"))
		if isinstance(extracted_slots.get("entity_reference_resolution"), dict)
		else {}
	)
	summary = [
		{"label": f"{context.get('entity_label')} Count", "metric_key": "row_count", "value": len(directory_rows)},
	]
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="master_data_directory",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions={
			"scope_id": str(extracted_slots.get("scope_id") or "").strip() or scope_id_for_entity_grain(str(context.get("entity_type") or "").strip()),
			"entity_type": context.get("entity_type"),
			"entity_label": context.get("entity_label"),
			"entity_plural_label": context.get("entity_plural_label"),
			"region_label": context.get("region_label"),
			"group_label": context.get("group_label"),
			"requested_top_n": requested_top_n or len(directory_rows),
			"requested_columns": requested_columns,
			"requested_column_alias_map": _master_directory_requested_column_alias_map(
				str(context.get("entity_type") or "").strip()
			),
			"suppress_summary_by_default": True,
			"source_grain": context.get("source_grain"),
			"lookup_mode": str(extracted_slots.get("lookup_mode") or "").strip(),
			"lookup_projection": str(extracted_slots.get("lookup_projection") or "").strip(),
			"lookup_search_text": str(extracted_slots.get("lookup_search_text") or "").strip(),
		},
		metrics={
			"row_count": len(directory_rows),
		},
		sections={
			"directory_rows": directory_rows,
			"summary": summary,
			"entity_reference_resolution": entity_reference_resolution,
		},
		warnings=(
			[f"No governed {str(context.get('entity_type') or 'entity')} master rows matched the current filters."]
			if not directory_rows
			else []
		),
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="master_data_directory",
		report_name=report_name,
		artifact_contract=artifact,
	)


def build_normalized_family_artifact(
	*,
	request_id: str,
	compiler_contract: Dict[str, Any],
	runtime_payload: Dict[str, Any],
	intent_class: str = "",
	preferred_family_id: str = "",
) -> FamilyArtifactOutcome:
	report_name = str(compiler_contract.get("selected_report") or "").strip()
	report_tool = _report_tool(runtime_payload)
	tool_report_name = str(_tool_args(report_tool).get("report_name") or "").strip()
	if tool_report_name:
		report_name = tool_report_name
	if not report_name:
		return FamilyArtifactOutcome(
			status="not_applicable",
			family_id="",
			report_name="",
			errors=["No governed report name was available for family adaptation."],
		)
	family_ids = report_business_family_ids(report_name)
	target_family_id = _resolve_target_family_id(
		report_name,
		family_ids,
		intent_class,
		str(preferred_family_id or "").strip(),
	)
	if target_family_id == "financial_statement":
		return _build_financial_statement_artifact(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
		)
	if target_family_id == "aging":
		return _build_aging_artifact(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	if target_family_id == "ranking_analytics":
		return _build_ranking_artifact(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	if target_family_id == "trend_analytics":
		return _build_trend_artifact(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	if target_family_id == "inventory_snapshot":
		return _build_inventory_snapshot_artifact(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	if target_family_id == "product_profitability":
		return _build_product_profitability_artifact(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	if target_family_id == "transaction_listing":
		return _build_transaction_listing_artifact(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	if is_master_data_listing_family(target_family_id):
		return _build_master_data_directory_artifact(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
			compiler_contract=compiler_contract,
		)
	return FamilyArtifactOutcome(
		status="not_applicable",
		family_id=target_family_id,
		report_name=report_name,
	)
