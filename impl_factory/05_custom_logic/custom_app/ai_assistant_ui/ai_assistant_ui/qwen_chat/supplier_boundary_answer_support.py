from __future__ import annotations

from typing import Any, Dict, Set


def _numeric(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def _money(value: Any) -> str:
	return f"{_numeric(value):,.2f}".rstrip("0").rstrip(".")


def _requested_values(values: Any) -> Set[str]:
	if not isinstance(values, list):
		return set()
	return {
		str(value or "").strip()
		for value in values
		if str(value or "").strip()
	}


def _section_label_values(rows: Any) -> Dict[str, str]:
	if not isinstance(rows, list):
		return {}
	return {
		str(item.get("label") or "").strip().lower(): str(item.get("value") or "").strip()
		for item in rows
		if isinstance(item, dict) and str(item.get("label") or "").strip()
	}


def supplier_boundary_direct_evidence_answer(
	*,
	typed_request: Dict[str, Any],
	artifact: Dict[str, Any],
	dimensions: Dict[str, Any],
) -> str:
	requested_metrics = _requested_values(typed_request.get("requested_metrics"))
	requested_dimensions = _requested_values(typed_request.get("requested_dimensions"))
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	metrics = artifact.get("metrics") if isinstance(artifact.get("metrics"), dict) else {}
	policy_rows = sections.get("credit_policy") if isinstance(sections.get("credit_policy"), list) else []
	policy_values = _section_label_values(policy_rows)
	entity_label = str(dimensions.get("entity_label") or dimensions.get("entity_key") or "this supplier").strip()
	company_name = policy_values.get("company", "")
	company_phrase = f" for {company_name}" if company_name else ""
	payment_terms = policy_values.get("payment terms", "")
	invoice_count = int(_numeric(metrics.get("invoice_count")))
	outstanding_total = _numeric(metrics.get("outstanding_total"))
	if not outstanding_total:
		outstanding_total = _numeric(metrics.get("outstanding_amount"))
	latest_invoice_date = str(metrics.get("latest_invoice_date") or "").strip()
	overdue_total = _numeric(metrics.get("overdue_total"))
	overdue_ratio = _numeric(metrics.get("overdue_ratio"))
	total_due = _numeric(metrics.get("total_due"))
	aging_buckets = sections.get("aging_buckets") if isinstance(sections.get("aging_buckets"), list) else []

	if "payment_terms_template" in requested_dimensions:
		if payment_terms:
			return f"The configured payment terms for {entity_label}{company_phrase} are {payment_terms}."
		return f"{entity_label} does not have configured payment terms{company_phrase}."

	if "outstanding_total" in requested_metrics:
		return f"The current outstanding payable balance for {entity_label} is {_money(outstanding_total)} MMK."

	if "invoice_count" in requested_metrics:
		return f"{entity_label} has {invoice_count} posted purchase invoices in the governed history{company_phrase}."

	if "overdue_ratio" in requested_metrics:
		if outstanding_total <= 0:
			return (
				f"As of the current governed payable snapshot, {entity_label} has an overdue ratio of 0.0%{company_phrase}.\n\n"
				"There is no positive outstanding payable balance in the current governed artifact."
			)
		return (
			f"As of the current governed payable snapshot, {entity_label} has an overdue ratio of {overdue_ratio * 100:.1f}%{company_phrase}.\n\n"
			f"This is based on overdue amount {_money(overdue_total)} MMK against outstanding amount {_money(outstanding_total)} MMK."
		)

	if "overdue_total" in requested_metrics:
		return f"The overdue payable amount for {entity_label} is {_money(overdue_total)} MMK."

	if "overdue_only" in requested_metrics:
		if overdue_total > 0:
			return f"Yes. {entity_label} has {_money(overdue_total)} MMK in overdue payables."
		return f"No. {entity_label} does not have overdue payables."

	if "total_due" in requested_metrics:
		return f"The total due amount for {entity_label} is {_money(total_due)} MMK."

	if "dominant_aging_bucket" in requested_dimensions:
		if aging_buckets:
			top_bucket = max(aging_buckets, key=lambda row: _numeric(row.get("amount")))
			bucket_label = str(top_bucket.get("bucket") or "").strip()
			amount = _numeric(top_bucket.get("amount"))
			if bucket_label:
				return f"The highest payable aging bucket for {entity_label} is {bucket_label} with {_money(amount)} MMK."

	if "posting_date" in requested_dimensions:
		if latest_invoice_date:
			return f"The latest governed purchase invoice date for {entity_label}{company_phrase} is {latest_invoice_date}."
		return f"I couldn't find a governed latest purchase invoice date for {entity_label}{company_phrase}."

	return ""
