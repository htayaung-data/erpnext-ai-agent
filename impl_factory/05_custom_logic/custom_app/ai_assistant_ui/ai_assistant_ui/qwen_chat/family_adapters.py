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
from ai_assistant_ui.qwen_chat.metadata import report_business_family_ids


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
	return _clean_rows(result.get("data"))


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
		"from_fiscal_year": str(filters.get("from_fiscal_year") or "").strip(),
		"to_fiscal_year": str(filters.get("to_fiscal_year") or "").strip(),
		"periodicity": str(filters.get("periodicity") or "").strip(),
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
	return {
		_clean_metric_key(value)
		for value in (compiler_contract.get("requested_metrics") or [])
		if str(value or "").strip()
	}


def _requested_dimension_keys(compiler_contract: Dict[str, Any]) -> set[str]:
	return {
		_clean_metric_key(value)
		for value in (compiler_contract.get("requested_dimensions") or [])
		if str(value or "").strip()
	}


def _requested_time_scope(compiler_contract: Dict[str, Any]) -> str:
	return str(compiler_contract.get("requested_time_scope") or "").strip()


def _period_field_specs(columns: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
	excluded = {"entity", "entity_name", "total", "item_code", "item_name"}
	out: List[Tuple[str, str]] = []
	for item in columns:
		fieldname = str(item.get("fieldname") or "").strip()
		label = str(item.get("label") or "").strip()
		if not fieldname or fieldname in excluded:
			continue
		out.append((fieldname, label or fieldname))
	return out


def _time_grain_from_filters(filters: Dict[str, Any]) -> str:
	range_value = _normalize_key(filters.get("range"))
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
	metric_label = "Quantity" if metric_key == "quantity" else "Sales Amount"
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
	total_value = _numeric_value(total_row.get("total")) or sum(_numeric_value(row.get(metric_key)) for row in ranked_rows)
	top_row = ranked_rows[0] if ranked_rows else {}
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="ranking_analytics",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions={
			"entity_dimension": str(filters.get("tree_type") or "Entity").strip() or "Entity",
			"primary_metric_key": metric_key,
			"primary_metric_label": metric_label,
			"time_grain": _time_grain_from_filters(filters),
			"source_grain": "entity_total",
		},
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
	ranked_rows = _sort_ranked_rows(
		[
			{
				"entity": str(row.get("party") or "").strip(),
				metric_key: _numeric_value(row.get(source_field)),
			}
			for row in rows
		],
		metric_key,
	)
	total_value = sum(_numeric_value(row.get(metric_key)) for row in ranked_rows)
	top_row = ranked_rows[0] if ranked_rows else {}
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="ranking_analytics",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions={
			"entity_dimension": entity_dimension,
			"primary_metric_key": metric_key,
			"primary_metric_label": metric_label,
			"source_grain": "aging_summary",
			"aging_type": aging_type,
		},
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
	ranked_rows = _sort_ranked_rows(
		[
			{
				"entity": str(row.get("item_name") or row.get("item_code") or "").strip(),
				"entity_code": str(row.get("item_code") or "").strip(),
				"brand": str(row.get("brand") or "").strip(),
				"item_group": str(row.get("item_group") or "").strip(),
				metric_key: _numeric_value(row.get(source_field)),
			}
			for row in rows
		],
		metric_key,
	)
	total_value = _numeric_value(total_row.get(source_field)) or sum(_numeric_value(row.get(metric_key)) for row in ranked_rows)
	top_row = ranked_rows[0] if ranked_rows else {}
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="ranking_analytics",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions={
			"entity_dimension": str(filters.get("group_by") or "Item Code").strip() or "Item Code",
			"primary_metric_key": metric_key,
			"primary_metric_label": metric_label,
			"source_grain": "grouped_profitability",
		},
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
			errors=[f"Ranking adapter could not aggregate any `{entity_dimension}` rows for `{report_name}`."],
		)
	filters = _report_filters(report_tool, result)
	period = _period_from_filters(filters)
	ranked_rows = _sort_ranked_rows(list(aggregated.values()), metric_key)
	total_value = sum(_numeric_value(row.get(metric_key)) for row in ranked_rows)
	top_row = ranked_rows[0] if ranked_rows else {}
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="ranking_analytics",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions={
			"entity_dimension": entity_dimension,
			"primary_metric_key": metric_key,
			"primary_metric_label": metric_label,
			"source_grain": "aggregated_history",
		},
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
	ranked_rows = _sort_ranked_rows(list(aggregated.values()), metric_key)
	total_value = sum(_numeric_value(row.get(metric_key)) for row in ranked_rows)
	top_row = ranked_rows[0] if ranked_rows else {}
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="ranking_analytics",
		source_reports=[report_name],
		period=period,
		filters=filters,
		dimensions={
			"entity_dimension": entity_dimension,
			"primary_metric_key": metric_key,
			"primary_metric_label": metric_label,
			"source_grain": "inventory_snapshot",
		},
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
) -> FamilyArtifactOutcome:
	result = _report_result(report_tool)
	columns = _report_columns(result)
	period_fields = _period_field_specs(columns)
	if not period_fields:
		return FamilyArtifactOutcome(
			status="adapter_error",
			family_id="trend_analytics",
			report_name=report_name,
			errors=[f"Trend adapter could not detect any governed period columns for `{report_name}`."],
		)
	rows = [row for row in _report_rows(result) if isinstance(row, dict)]
	total_row = _report_total_row_map(result)
	filters = _report_filters(report_tool, result)
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
	metric_key = "quantity" if _normalize_key(filters.get("value_quantity")) == "quantity" else "sales_amount"
	metric_label = "Quantity" if metric_key == "quantity" else "Sales Amount"
	total_value = _numeric_value(total_row.get("total")) or sum(_numeric_value(item.get("value")) for item in period_series)
	artifact = build_normalized_family_artifact_contract(
		request_id=request_id,
		family_id="trend_analytics",
		source_reports=[report_name],
		period=_period_from_filters(filters),
		filters=filters,
		dimensions={
			"time_grain": _time_grain_from_filters(filters),
			"primary_metric_key": metric_key,
			"primary_metric_label": metric_label,
			"series_dimension": str(filters.get("tree_type") or "").strip(),
			"source_grain": "period_total",
		},
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
		dimensions={
			"time_grain": "monthly",
			"primary_metric_key": metric_key,
			"primary_metric_label": metric_label,
			"source_grain": "aggregated_history",
		},
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
	if report_key == "sales_analytics":
		return _build_sales_analytics_trend(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
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


def _family_preference_order(intent_class: str) -> List[str]:
	return {
		"financial_statement": ["financial_statement"],
		"aging_analysis": ["aging"],
		"ranked_entities": ["ranking_analytics", "aging", "inventory_snapshot", "product_profitability"],
		"trend_analysis": ["trend_analytics", "product_profitability"],
		"inventory_summary": ["inventory_snapshot"],
		"product_performance": ["product_profitability", "ranking_analytics", "trend_analytics"],
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
		dimensions={
			"statement_type": statement_type,
			"currency": currency,
			"periodicity": str(filters.get("periodicity") or "").strip(),
			"value_column": _value_fieldname(columns),
		},
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
		dimensions={
			"aging_type": aging_type,
			"currency": currency,
			"party_dimension_label": _aging_party_dimension_label(aging_type),
			"source_grain": "summary" if "summary" in _normalize_key(report_name) else "detail",
			"bucket_labels": [label for _, label, _ in _aging_bucket_specs()],
		},
		metrics=_aging_metrics(rows, aging_type),
		sections=_aging_sections(rows, aging_type, currency),
	)
	return FamilyArtifactOutcome(
		status="adapted",
		family_id="aging",
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
	return FamilyArtifactOutcome(
		status="not_applicable",
		family_id=target_family_id,
		report_name=report_name,
	)
