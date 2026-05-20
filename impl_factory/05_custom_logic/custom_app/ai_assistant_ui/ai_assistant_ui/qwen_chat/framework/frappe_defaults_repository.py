from __future__ import annotations

import datetime as dt
from typing import Dict, List

try:
	import frappe  # type: ignore
except Exception:  # pragma: no cover
	frappe = None


def load_company_names(*, limit: int = 2) -> List[str]:
	if frappe is None:
		return []
	try:
		rows = frappe.get_all("Company", pluck="name", limit=max(1, int(limit or 1)))
	except Exception:
		return []
	return [str(value or "").strip() for value in (rows or []) if str(value or "").strip()]


def load_fiscal_year_rows(*, limit: int = 20) -> List[Dict[str, str]]:
	if frappe is None:
		return []
	try:
		rows = frappe.get_all(
			"Fiscal Year",
			fields=["name", "year_start_date", "year_end_date"],
			order_by="year_start_date asc",
			limit=max(1, int(limit or 1)),
		)
	except Exception:
		return []
	out: List[Dict[str, str]] = []
	for row in rows or []:
		if not isinstance(row, dict):
			continue
		name = str(row.get("name") or "").strip()
		start_value = row.get("year_start_date")
		end_value = row.get("year_end_date")
		try:
			start = dt.date.fromisoformat(str(start_value)) if start_value else None
			end = dt.date.fromisoformat(str(end_value)) if end_value else None
		except Exception:
			start = None
			end = None
		if not name or not start or not end:
			continue
		out.append(
			{
				"name": name,
				"year_start_date": start.isoformat(),
				"year_end_date": end.isoformat(),
			}
		)
	return out


def load_period_closing_voucher_rows(*, company: str = "", limit: int = 20) -> List[Dict[str, str]]:
	if frappe is None:
		return []
	filters: Dict[str, object] = {"docstatus": 1}
	clean_company = str(company or "").strip()
	if clean_company:
		filters["company"] = clean_company
	try:
		rows = frappe.get_all(
			"Period Closing Voucher",
			filters=filters,
			fields=[
				"name",
				"company",
				"fiscal_year",
				"period_start_date",
				"period_end_date",
				"transaction_date",
				"gle_processing_status",
			],
			order_by="period_end_date desc",
			limit=max(1, int(limit or 1)),
		)
	except Exception:
		return []
	out: List[Dict[str, str]] = []
	for row in rows or []:
		if not isinstance(row, dict):
			continue
		name = str(row.get("name") or "").strip()
		period_start_value = row.get("period_start_date")
		period_end_value = row.get("period_end_date")
		transaction_date_value = row.get("transaction_date")
		try:
			period_start = dt.date.fromisoformat(str(period_start_value)) if period_start_value else None
			period_end = dt.date.fromisoformat(str(period_end_value)) if period_end_value else None
			transaction_date = (
				dt.date.fromisoformat(str(transaction_date_value))
				if transaction_date_value
				else None
			)
		except Exception:
			period_start = None
			period_end = None
			transaction_date = None
		if not name or not period_end:
			continue
		record: Dict[str, str] = {
			"name": name,
			"company": str(row.get("company") or "").strip(),
			"fiscal_year": str(row.get("fiscal_year") or "").strip(),
			"period_start_date": period_start.isoformat() if period_start else "",
			"period_end_date": period_end.isoformat(),
			"transaction_date": transaction_date.isoformat() if transaction_date else "",
			"gle_processing_status": str(row.get("gle_processing_status") or "").strip(),
		}
		out.append(record)
	return out
