from __future__ import annotations

import datetime as dt
from typing import Any, Dict

import frappe


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _coerce_date(value: Any) -> dt.date | None:
	if isinstance(value, dt.datetime):
		return value.date()
	if isinstance(value, dt.date):
		return value
	text = _clean_text(value)
	if not text:
		return None
	text = text[:10]
	try:
		return dt.date.fromisoformat(text)
	except Exception:
		return None


def _iso_date(value: Any) -> str:
	date_value = _coerce_date(value)
	return date_value.isoformat() if date_value else ""


def _days_between(start_date: dt.date | None, end_date: dt.date | None) -> int:
	if not start_date or not end_date:
		return 0
	return max((end_date - start_date).days, 0)


def _first_document_date(
	doctype: str,
	*,
	party_field: str,
	party_value: str,
	date_field: str,
	company: str = "",
) -> str:
	conditions = [f"{party_field}=%s", "docstatus=1"]
	values: list[Any] = [party_value]
	if company:
		conditions.append("company=%s")
		values.append(company)
	rows = frappe.db.sql(
		f"""
		select min({date_field}) as first_date
		from `tab{doctype}`
		where {' and '.join(conditions)}
		""",
		tuple(values),
		as_dict=True,
	)
	row = dict(rows[0] or {}) if rows else {}
	return _iso_date(row.get("first_date"))


def get_customer_lifecycle_snapshot(
	customer_name: str,
	*,
	company: str = "",
	as_of_date: str = "",
) -> Dict[str, Any]:
	customer_key = _clean_text(customer_name)
	if not customer_key:
		return {}
	as_of = _coerce_date(as_of_date) or dt.datetime.now(dt.timezone.utc).date()
	created_on = frappe.db.get_value("Customer", customer_key, "creation")
	customer_created_date = _iso_date(created_on)
	first_sales_order_date = _first_document_date(
		"Sales Order",
		party_field="customer",
		party_value=customer_key,
		date_field="transaction_date",
		company=company,
	)
	first_sales_invoice_date = _first_document_date(
		"Sales Invoice",
		party_field="customer",
		party_value=customer_key,
		date_field="posting_date",
		company=company,
	)
	return {
		"customer_created_date": customer_created_date,
		"first_sales_order_date": first_sales_order_date,
		"first_sales_invoice_date": first_sales_invoice_date,
		"as_of_date": as_of.isoformat(),
		"customer_created_tenure_days": _days_between(_coerce_date(customer_created_date), as_of),
		"first_sales_order_tenure_days": _days_between(_coerce_date(first_sales_order_date), as_of),
		"first_sales_invoice_tenure_days": _days_between(_coerce_date(first_sales_invoice_date), as_of),
	}
