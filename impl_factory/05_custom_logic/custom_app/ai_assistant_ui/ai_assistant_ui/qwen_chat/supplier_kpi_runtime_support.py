from __future__ import annotations

from typing import Any, Dict

from ai_assistant_ui.qwen_chat.customer_kpi_runtime_support import (
	current_date_iso,
	_numeric,
	_report_result,
	_report_rows,
	_report_tool,
	resolve_company_name,
)
from ai_assistant_ui.qwen_chat.governed_report_executor import execute_governed_report


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _normalize_text(value: Any) -> str:
	return " ".join(_clean_text(value).lower().split())


def _match_supplier_row(row: Dict[str, Any], supplier_name: str, supplier_label: str) -> bool:
	targets = {_normalize_text(supplier_name), _normalize_text(supplier_label)}
	for field in ("party", "supplier", "party_name", "supplier_name"):
		value = _normalize_text(row.get(field))
		if value and value in targets:
			return True
	return False


def get_supplier_payable_snapshot(
	supplier_name: str,
	*,
	supplier_label: str = "",
	company: str = "",
	as_of_date: str = "",
) -> Dict[str, Any]:
	supplier_key = _clean_text(supplier_name)
	entity_label = _clean_text(supplier_label) or supplier_key
	company_name = resolve_company_name(company)
	report_date = _clean_text(as_of_date) or current_date_iso()
	if not supplier_key or not company_name or not report_date:
		return {}
	runtime_payload = execute_governed_report(
		report_name="Accounts Payable Summary",
		filters={"company": company_name, "report_date": report_date},
		user="Administrator",
		mode="entity_detail",
		target_limit=0,
	)
	report_tool = _report_tool(runtime_payload if isinstance(runtime_payload, dict) else {})
	result = _report_result(report_tool)
	rows = _report_rows(result)
	target_row = next(
		(row for row in rows if isinstance(row, dict) and _match_supplier_row(row, supplier_key, entity_label)),
		{},
	)
	if not target_row:
		return {}
	outstanding = _numeric(target_row.get("outstanding"))
	total_due = _numeric(target_row.get("total_due"))
	future_amount = _numeric(target_row.get("future_amount"))
	range1 = _numeric(target_row.get("range1"))
	range2 = _numeric(target_row.get("range2"))
	range3 = _numeric(target_row.get("range3"))
	range4 = _numeric(target_row.get("range4"))
	range5 = _numeric(target_row.get("range5"))
	overdue_total = range2 + range3 + range4 + range5
	overdue_ratio = (overdue_total / outstanding) if outstanding > 0 else 0.0
	return {
		"report_date": report_date,
		"company": company_name,
		"currency": _clean_text(target_row.get("currency")),
		"summary": [
			("Outstanding (MMK)", f"{outstanding:,.2f}".rstrip("0").rstrip(".")),
			("Total Due (MMK)", f"{total_due:,.2f}".rstrip("0").rstrip(".")),
			("Overdue Total (MMK)", f"{overdue_total:,.2f}".rstrip("0").rstrip(".")),
			("Overdue Ratio", f"{overdue_ratio * 100:.1f}%"),
		],
		"bucket_rows": [
			("<0", future_amount),
			("0-30", range1),
			("31-60", range2),
			("61-90", range3),
			("91-120", range4),
			("121-Above", range5),
		],
		"metrics": {
			"outstanding_total": outstanding,
			"total_due": total_due,
			"future_bucket_total": future_amount,
			"current_bucket_total": range1,
			"bucket_31_60_total": range2,
			"bucket_61_90_total": range3,
			"bucket_91_120_total": range4,
			"bucket_121_above_total": range5,
			"overdue_total": overdue_total,
			"overdue_ratio": overdue_ratio,
		},
	}
