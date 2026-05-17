from __future__ import annotations

from typing import Any, Dict, List, Set

from ai_assistant_ui.qwen_chat.customer_lifecycle_basis import customer_lifecycle_basis_summary_phrase
from ai_assistant_ui.qwen_chat.entity_detail_clarification import entity_detail_boundary_clarification_answer


def _numeric(value: Any) -> float:
	try:
		return float(value or 0.0)
	except Exception:
		return 0.0


def _money(value: Any) -> str:
	return f"{_numeric(value):,.2f}".rstrip("0").rstrip(".")


def _days_text(value: Any) -> str:
	days = int(max(_numeric(value), 0))
	return f"{days} day" if days == 1 else f"{days} days"


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


def customer_boundary_direct_evidence_answer(
	*,
	typed_request: Dict[str, Any],
	artifact: Dict[str, Any],
	dimensions: Dict[str, Any],
	clarification_required: bool,
	clarification_reason_type: str,
) -> str:
	requested_metrics = _requested_values(typed_request.get("requested_metrics"))
	requested_dimensions = _requested_values(typed_request.get("requested_dimensions"))
	basis = str(typed_request.get("basis") or "").strip()
	entity_question_type = str(typed_request.get("entity_question_type") or "").strip()
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	metrics = artifact.get("metrics") if isinstance(artifact.get("metrics"), dict) else {}
	credit_buckets = sections.get("credit_buckets") if isinstance(sections.get("credit_buckets"), list) else []
	credit_policy = sections.get("credit_policy") if isinstance(sections.get("credit_policy"), list) else []
	lifecycle_rows = sections.get("lifecycle") if isinstance(sections.get("lifecycle"), list) else []
	outstanding_total = _numeric(metrics.get("outstanding_total"))
	total_due = _numeric(metrics.get("total_due"))
	overdue_total = _numeric(metrics.get("overdue_total"))
	overdue_ratio = _numeric(metrics.get("overdue_ratio"))
	credit_limit = _numeric(metrics.get("credit_limit"))
	credit_limit_available = _numeric(metrics.get("credit_limit_available"))
	credit_limit_excess = _numeric(metrics.get("credit_limit_excess"))
	credit_limit_utilization = _numeric(metrics.get("credit_limit_utilization_ratio"))
	credit_limit_configured = bool(metrics.get("credit_limit_configured")) or credit_limit > 0
	credit_limit_exceeded = bool(metrics.get("credit_limit_exceeded")) or credit_limit_excess > 0
	credit_limit_bypass = bool(metrics.get("credit_limit_bypass_sales_order"))
	entity_label = str(dimensions.get("entity_label") or dimensions.get("entity_key") or "this customer").strip()
	policy_values = _section_label_values(credit_policy)
	lifecycle_values = _section_label_values(lifecycle_rows)
	policy_company = policy_values.get("company", "")
	company_phrase = f" for {policy_company}" if policy_company else ""
	payment_terms = policy_values.get("payment terms", "")
	default_price_list = policy_values.get("default price list", "")
	customer_created_date = lifecycle_values.get("customer created date", "")
	first_sales_order_date = lifecycle_values.get("first sales order date", "")
	first_sales_invoice_date = lifecycle_values.get("first sales invoice date", "")
	customer_created_tenure_days = int(_numeric(metrics.get("customer_created_tenure_days")))
	first_sales_order_tenure_days = int(_numeric(metrics.get("first_sales_order_tenure_days")))
	first_sales_invoice_tenure_days = int(_numeric(metrics.get("first_sales_invoice_tenure_days")))

	if clarification_required:
		clarification_answer = entity_detail_boundary_clarification_answer(
			reason_type=clarification_reason_type,
			entity_label=entity_label,
			company_phrase=company_phrase,
		)
		if clarification_answer:
			return clarification_answer

	if entity_question_type == "customer_tenure":
		if basis == "customer_created_date":
			if customer_created_date:
				return (
					f"{entity_label} has a governed tenure of {_days_text(customer_created_tenure_days)}"
					f"{company_phrase}, measured from customer created date {customer_created_date}."
				)
			return f"I couldn't find a governed customer created date for {entity_label}{company_phrase}."
		if basis == "first_sales_order_date":
			if first_sales_order_date:
				return (
					f"{entity_label} has a governed tenure of {_days_text(first_sales_order_tenure_days)}"
					f"{company_phrase}, measured from first submitted sales order date {first_sales_order_date}."
				)
			return f"I couldn't find a governed first submitted sales order date for {entity_label}{company_phrase}."
		if basis == "first_sales_invoice_date":
			if first_sales_invoice_date:
				return (
					f"{entity_label} has a governed tenure of {_days_text(first_sales_invoice_tenure_days)}"
					f"{company_phrase}, measured from first submitted sales invoice date {first_sales_invoice_date}."
				)
			return f"I couldn't find a governed first submitted sales invoice date for {entity_label}{company_phrase}."
		basis_phrase = customer_lifecycle_basis_summary_phrase()
		if not basis_phrase:
			basis_phrase = "customer created date, first submitted sales order date, or first submitted sales invoice date"
		return (
			f"I can calculate tenure for {entity_label}{company_phrase} using one of three date bases: "
			f"{basis_phrase}."
		)

	if entity_question_type == "customer_lifecycle_date":
		if basis == "customer_created_date":
			if customer_created_date:
				return f"{entity_label} was created on {customer_created_date}{company_phrase}."
			return f"I couldn't find a governed customer created date for {entity_label}{company_phrase}."
		if basis == "first_sales_order_date":
			if first_sales_order_date:
				return f"The first observed submitted sales order for {entity_label}{company_phrase} was on {first_sales_order_date}."
			return f"I couldn't find a governed first submitted sales order date for {entity_label}{company_phrase}."
		if basis == "first_sales_invoice_date":
			if first_sales_invoice_date:
				return f"The first observed submitted sales invoice for {entity_label}{company_phrase} was on {first_sales_invoice_date}."
			return f"I couldn't find a governed first submitted sales invoice date for {entity_label}{company_phrase}."

	if "credit_limit_status" in requested_metrics:
		if not credit_limit_configured:
			return (
				f"{entity_label} does not have a configured credit limit{company_phrase}, "
				"so I can't determine limit status from governed policy data."
			)
		if credit_limit_exceeded:
			answer = (
				f"Yes. {entity_label} has exceeded the configured credit limit{company_phrase}.\n\n"
				f"Current outstanding is {_money(outstanding_total)} MMK against a credit limit of {_money(credit_limit)} MMK, "
				f"so it is over by {_money(credit_limit_excess)} MMK."
			)
		else:
			answer = (
				f"No. {entity_label} is still within the configured credit limit{company_phrase}.\n\n"
				f"Current outstanding is {_money(outstanding_total)} MMK against a credit limit of {_money(credit_limit)} MMK, "
				f"leaving {_money(credit_limit_available)} MMK available."
			)
		if credit_limit_bypass:
			answer += "\n\nSales-order credit-limit check is currently bypassed in master data."
		return answer

	if "credit_limit_available" in requested_metrics:
		if not credit_limit_configured:
			return (
				f"{entity_label} does not have a configured credit limit{company_phrase}, "
				"so available credit cannot be calculated from governed policy data."
			)
		if credit_limit_exceeded:
			return (
				f"{entity_label} has no remaining configured credit{company_phrase}.\n\n"
				f"Current outstanding exceeds the limit by {_money(credit_limit_excess)} MMK."
			)
		return (
			f"The remaining available credit for {entity_label}{company_phrase} is {_money(credit_limit_available)} MMK.\n\n"
			f"Configured credit limit is {_money(credit_limit)} MMK and current outstanding is {_money(outstanding_total)} MMK."
		)

	if "credit_limit_utilization" in requested_metrics:
		if not credit_limit_configured:
			return (
				f"{entity_label} does not have a configured credit limit{company_phrase}, "
				"so utilization cannot be calculated from governed policy data."
			)
		return (
			f"{entity_label} is currently using {credit_limit_utilization * 100:.1f}% of the configured credit limit{company_phrase}.\n\n"
			f"This is based on outstanding amount {_money(outstanding_total)} MMK against credit limit {_money(credit_limit)} MMK."
		)

	if "payment_terms_template" in requested_dimensions:
		if payment_terms:
			return f"The configured payment terms for {entity_label}{company_phrase} are {payment_terms}."
		return f"{entity_label} does not have configured payment terms{company_phrase}."

	if "default_price_list" in requested_dimensions:
		if default_price_list:
			return f"The default price list for {entity_label}{company_phrase} is {default_price_list}."
		return f"{entity_label} does not have a configured default price list{company_phrase}."

	if "credit_limit_amount" in requested_metrics:
		if credit_limit_configured:
			return f"The configured credit limit for {entity_label}{company_phrase} is {_money(credit_limit)} MMK."
		return f"{entity_label} does not have a configured credit limit{company_phrase}."

	if "credit_balance_amount" in requested_metrics:
		if outstanding_total < 0:
			return f"The credit balance for {entity_label} is {_money(abs(outstanding_total))} MMK."
		return f"{entity_label} does not have a credit balance."

	if "credit_balance_only" in requested_metrics:
		if outstanding_total < 0:
			return f"Yes. {entity_label} has a credit balance of {_money(abs(outstanding_total))} MMK."
		return f"No. {entity_label} does not have a credit balance."

	if "overdue_ratio" in requested_metrics:
		if outstanding_total <= 0:
			return (
				f"As of the current receivable snapshot, {entity_label} has an overdue ratio of 0.0%{company_phrase}.\n\n"
				"There is no positive outstanding balance in this snapshot."
			)
		return (
			f"As of the current receivable snapshot, {entity_label} has an overdue ratio of {overdue_ratio * 100:.1f}%{company_phrase}.\n\n"
			f"This is based on overdue amount {_money(overdue_total)} MMK against outstanding amount {_money(outstanding_total)} MMK."
		)

	if "overdue_total" in requested_metrics:
		return f"The overdue amount for {entity_label} is {_money(overdue_total)} MMK."

	if "overdue_only" in requested_metrics:
		if overdue_total > 0:
			return f"Yes. {entity_label} is overdue with {_money(overdue_total)} MMK past due."
		return f"No. {entity_label} is not overdue."

	if "outstanding_total" in requested_metrics:
		return f"The outstanding balance for {entity_label} is {_money(outstanding_total)} MMK."

	if "dominant_aging_bucket" in requested_dimensions or entity_question_type == "customer_aging_bucket":
		if credit_buckets:
			top_bucket = max(credit_buckets, key=lambda row: _numeric(row.get("amount")))
			bucket_label = str(top_bucket.get("bucket") or "").strip()
			amount = _numeric(top_bucket.get("amount"))
			if bucket_label:
				return f"The highest aging bucket for {entity_label} is {bucket_label} with {_money(amount)} MMK."

	if "total_due" in requested_metrics:
		return f"The total due amount for {entity_label} is {_money(total_due)} MMK."

	return ""
