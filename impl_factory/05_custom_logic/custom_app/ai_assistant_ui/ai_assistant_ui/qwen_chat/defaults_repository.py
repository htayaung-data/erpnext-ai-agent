from __future__ import annotations

import datetime as dt
from typing import Dict, List, Tuple

from ai_assistant_ui.qwen_chat.framework.frappe_defaults_repository import (
	load_company_names,
	load_fiscal_year_rows,
	load_period_closing_voucher_rows,
)


def _today_date() -> dt.date:
	return dt.datetime.now(dt.timezone.utc).date()


def single_company_name() -> str:
	companies = load_company_names(limit=2)
	if len(companies) == 1:
		return str(companies[0] or "").strip()
	return ""


def fiscal_year_rows() -> List[Dict[str, str]]:
	return load_fiscal_year_rows(limit=20)


def _parse_iso_date(value: str) -> dt.date | None:
	text = str(value or "").strip()
	if not text:
		return None
	try:
		return dt.date.fromisoformat(text)
	except Exception:
		return None


def current_fiscal_year_row(*, today: dt.date | None = None) -> Dict[str, str]:
	current_day = today or _today_date()
	rows = fiscal_year_rows()
	fallback: Dict[str, str] = {}
	for row in rows:
		start = dt.date.fromisoformat(str(row.get("year_start_date") or ""))
		end = dt.date.fromisoformat(str(row.get("year_end_date") or ""))
		if not fallback:
			fallback = dict(row)
		if start <= current_day <= end:
			return dict(row)
	return fallback


def previous_fiscal_year_row(*, today: dt.date | None = None) -> Dict[str, str]:
	rows = fiscal_year_rows()
	if not rows:
		return {}
	current_name = str(current_fiscal_year_row(today=today).get("name") or "").strip()
	for index, row in enumerate(rows):
		if str(row.get("name") or "").strip() != current_name:
			continue
		if index > 0:
			return dict(rows[index - 1])
		break
	return {}


def matching_fiscal_year_row_for_range(from_date: str, to_date: str) -> Dict[str, str]:
	start = str(from_date or "").strip()
	end = str(to_date or "").strip()
	if not start or not end:
		return {}
	for row in fiscal_year_rows():
		if row.get("year_start_date") == start and row.get("year_end_date") == end:
			return dict(row)
	return {}


def fiscal_year_row_for_date(target_date: dt.date | str) -> Dict[str, str]:
	if isinstance(target_date, dt.date):
		day = target_date
	else:
		day = _parse_iso_date(str(target_date or ""))
	if day is None:
		return {}
	for row in fiscal_year_rows():
		start = _parse_iso_date(str(row.get("year_start_date") or ""))
		end = _parse_iso_date(str(row.get("year_end_date") or ""))
		if start is None or end is None:
			continue
		if start <= day <= end:
			return dict(row)
	return {}


def current_fiscal_year_bounds(*, today: dt.date | None = None) -> Tuple[str, str]:
	row = current_fiscal_year_row(today=today)
	return str(row.get("year_start_date") or "").strip(), str(row.get("year_end_date") or "").strip()


def previous_fiscal_year_bounds(*, today: dt.date | None = None) -> Tuple[str, str]:
	row = previous_fiscal_year_row(today=today)
	return str(row.get("year_start_date") or "").strip(), str(row.get("year_end_date") or "").strip()


def current_fiscal_year_name(*, today: dt.date | None = None) -> str:
	return str(current_fiscal_year_row(today=today).get("name") or "").strip()


def previous_fiscal_year_name(*, today: dt.date | None = None) -> str:
	return str(previous_fiscal_year_row(today=today).get("name") or "").strip()


def latest_closed_period_row(*, company: str = "") -> Dict[str, str]:
	resolved_company = str(company or "").strip() or single_company_name()
	rows = load_period_closing_voucher_rows(company=resolved_company, limit=20)
	for row in rows:
		status = str(row.get("gle_processing_status") or "").strip().lower()
		if status and status not in {"completed", "success", "processed"}:
			continue
		period_end = _parse_iso_date(str(row.get("period_end_date") or ""))
		if period_end is None:
			continue
		return dict(row)
	return {}


def open_fiscal_year_bounds(*, today: dt.date | None = None, company: str = "") -> Tuple[str, str]:
	current_day = today or _today_date()
	closed_period = latest_closed_period_row(company=company)
	closed_period_end = _parse_iso_date(str(closed_period.get("period_end_date") or ""))
	if closed_period_end is not None and closed_period_end < current_day:
		return (closed_period_end + dt.timedelta(days=1)).isoformat(), current_day.isoformat()
	start, _ = current_fiscal_year_bounds(today=current_day)
	return start, current_day.isoformat()
