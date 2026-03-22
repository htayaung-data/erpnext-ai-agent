from __future__ import annotations

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


def build_normalized_family_artifact(
	*,
	request_id: str,
	compiler_contract: Dict[str, Any],
	runtime_payload: Dict[str, Any],
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
	if "financial_statement" in family_ids:
		return _build_financial_statement_artifact(
			request_id=request_id,
			report_name=report_name,
			report_tool=report_tool,
		)
	return FamilyArtifactOutcome(
		status="not_applicable",
		family_id="",
		report_name=report_name,
	)
