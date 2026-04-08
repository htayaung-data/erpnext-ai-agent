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

