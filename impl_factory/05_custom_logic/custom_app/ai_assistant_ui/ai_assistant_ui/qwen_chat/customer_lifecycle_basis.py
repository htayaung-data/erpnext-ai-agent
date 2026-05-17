from __future__ import annotations

from typing import Any, Dict, List


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


_CUSTOMER_LIFECYCLE_BASIS_SPECS: List[Dict[str, Any]] = [
	{
		"basis": "customer_created_date",
		"tenure_choice_label": "Customer Tenure by Customer Created Date",
		"date_choice_label": "Customer Created Date",
		"summary_label": "customer created date",
		"date_dimension": "customer_created_date",
		"tenure_metric": "customer_created_tenure_days",
		"resolved_tenure_message": "what is this customer's tenure by customer created date?",
		"source_report": "Customer Master List",
		"source_capability": "customer_master_read",
		"aliases": [
			"customer created date",
			"created date",
			"customer creation date",
			"by customer created date",
		],
	},
	{
		"basis": "first_sales_order_date",
		"tenure_choice_label": "Customer Tenure by First Sales Order",
		"date_choice_label": "First Sales Order Date",
		"summary_label": "first submitted sales order date",
		"date_dimension": "first_sales_order_date",
		"tenure_metric": "first_sales_order_tenure_days",
		"resolved_tenure_message": "what is this customer's tenure by first sales order date?",
		"source_report": "Sales Order List",
		"source_capability": "sales_order_read",
		"aliases": [
			"first sales order",
			"first sales order date",
			"sales order",
			"order date",
			"by first sales order",
		],
	},
	{
		"basis": "first_sales_invoice_date",
		"tenure_choice_label": "Customer Tenure by First Sales Invoice",
		"date_choice_label": "First Sales Invoice Date",
		"summary_label": "first submitted sales invoice date",
		"date_dimension": "first_sales_invoice_date",
		"tenure_metric": "first_sales_invoice_tenure_days",
		"resolved_tenure_message": "what is this customer's tenure by first sales invoice date?",
		"source_report": "Sales Invoice List",
		"source_capability": "sales_read",
		"aliases": [
			"first sales invoice",
			"first sales invoice date",
			"sales invoice",
			"invoice date",
			"by first sales invoice",
		],
	},
]


def customer_lifecycle_basis_specs() -> List[Dict[str, Any]]:
	return [dict(item) for item in _CUSTOMER_LIFECYCLE_BASIS_SPECS]


def customer_lifecycle_basis_ids() -> List[str]:
	return [
		_clean_text(item.get("basis"))
		for item in _CUSTOMER_LIFECYCLE_BASIS_SPECS
		if _clean_text(item.get("basis"))
	]


def customer_lifecycle_supported_focus_grains() -> List[str]:
	return ["customer"]


def customer_lifecycle_tenure_basis_choices() -> List[Dict[str, str]]:
	return [
		{
			"label": _clean_text(item.get("tenure_choice_label")),
			"basis": _clean_text(item.get("basis")),
			"resolved_message": _clean_text(item.get("resolved_tenure_message")),
		}
		for item in _CUSTOMER_LIFECYCLE_BASIS_SPECS
		if _clean_text(item.get("tenure_choice_label"))
	]


def customer_lifecycle_tenure_aliases_by_option() -> Dict[str, List[str]]:
	out: Dict[str, List[str]] = {}
	for item in _CUSTOMER_LIFECYCLE_BASIS_SPECS:
		label = _clean_text(item.get("tenure_choice_label"))
		if label:
			out[label] = [
				_clean_text(alias)
				for alias in (item.get("aliases") or [])
				if _clean_text(alias)
			]
	return out


def customer_lifecycle_tenure_metric_basis_map() -> Dict[str, str]:
	return {
		_clean_text(item.get("tenure_metric")): _clean_text(item.get("basis"))
		for item in _CUSTOMER_LIFECYCLE_BASIS_SPECS
		if _clean_text(item.get("tenure_metric")) and _clean_text(item.get("basis"))
	}


def customer_lifecycle_dimension_basis_map() -> Dict[str, str]:
	return {
		_clean_text(item.get("date_dimension")): _clean_text(item.get("basis"))
		for item in _CUSTOMER_LIFECYCLE_BASIS_SPECS
		if _clean_text(item.get("date_dimension")) and _clean_text(item.get("basis"))
	}


def customer_lifecycle_source_report_by_basis() -> Dict[str, str]:
	return {
		_clean_text(item.get("basis")): _clean_text(item.get("source_report"))
		for item in _CUSTOMER_LIFECYCLE_BASIS_SPECS
		if _clean_text(item.get("basis")) and _clean_text(item.get("source_report"))
	}


def customer_lifecycle_source_capability_by_basis() -> Dict[str, str]:
	return {
		_clean_text(item.get("basis")): _clean_text(item.get("source_capability"))
		for item in _CUSTOMER_LIFECYCLE_BASIS_SPECS
		if _clean_text(item.get("basis")) and _clean_text(item.get("source_capability"))
	}


def customer_lifecycle_basis_summary_phrase() -> str:
	labels = [
		_clean_text(item.get("summary_label") or item.get("date_choice_label")).lower()
		for item in _CUSTOMER_LIFECYCLE_BASIS_SPECS
		if _clean_text(item.get("summary_label") or item.get("date_choice_label"))
	]
	if not labels:
		return ""
	if len(labels) == 1:
		return labels[0]
	return ", ".join(labels[:-1]) + f", or {labels[-1]}"
