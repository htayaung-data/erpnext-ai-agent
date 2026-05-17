from __future__ import annotations

from typing import Any, Dict

import frappe


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _numeric(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def compute_collection_ratio_by_sales_invoice_period(
	*,
	company: str,
	from_date: str,
	to_date: str,
) -> Dict[str, Any]:
	company_name = _clean_text(company)
	start_date = _clean_text(from_date)
	end_date = _clean_text(to_date)
	if not company_name or not start_date or not end_date:
		return {}
	sales_rows = frappe.db.sql(
		"""
		select
			count(si.name) as invoice_count,
			coalesce(sum(si.grand_total), 0) as sales_invoice_grand_total
		from `tabSales Invoice` si
		where si.docstatus = 1
		  and coalesce(si.is_return, 0) = 0
		  and si.company = %s
		  and si.posting_date between %s and %s
		""",
		(company_name, start_date, end_date),
		as_dict=True,
	)
	collection_rows = frappe.db.sql(
		"""
		select
			coalesce(sum(per.allocated_amount), 0) as allocated_customer_receipt_amount
		from `tabPayment Entry Reference` per
		inner join `tabSales Invoice` si
			on si.name = per.reference_name
		inner join `tabPayment Entry` pe
			on pe.name = per.parent
		where per.reference_doctype = 'Sales Invoice'
		  and si.docstatus = 1
		  and coalesce(si.is_return, 0) = 0
		  and pe.docstatus = 1
		  and pe.payment_type = 'Receive'
		  and pe.party_type = 'Customer'
		  and si.company = %s
		  and pe.company = %s
		  and si.posting_date between %s and %s
		""",
		(company_name, company_name, start_date, end_date),
		as_dict=True,
	)
	sales_row = dict(sales_rows[0] or {}) if sales_rows else {}
	collection_row = dict(collection_rows[0] or {}) if collection_rows else {}
	invoiced_total = _numeric(sales_row.get("sales_invoice_grand_total"))
	collected_total = _numeric(collection_row.get("allocated_customer_receipt_amount"))
	return {
		"company": company_name,
		"from_date": start_date,
		"to_date": end_date,
		"invoice_count": int(_numeric(sales_row.get("invoice_count"))),
		"sales_invoice_grand_total": invoiced_total,
		"allocated_customer_receipt_amount": collected_total,
		"collection_ratio": (collected_total / invoiced_total) if invoiced_total > 0 else 0.0,
	}
