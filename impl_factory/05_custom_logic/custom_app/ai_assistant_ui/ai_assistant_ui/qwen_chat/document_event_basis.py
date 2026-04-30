from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_set(values: List[str] | Set[str] | None) -> Set[str]:
	return {
		_clean_text(value)
		for value in (values or [])
		if _clean_text(value)
	}


_DOCUMENT_EVENT_BASIS_SPECS: List[Dict[str, Any]] = [
	{
		"entity_type": "sales_order",
		"entity_question_type": "sales_order_actual_delivery_event_date",
		"required_dimensions_any": ["posting_date"],
		"question_shape": "date_lookup",
		"value_mode": "actual_value",
		"event_basis": "actual_delivery_event_date",
	},
	{
		"entity_type": "sales_order",
		"entity_question_type": "sales_order_planned_delivery_date",
		"required_dimensions_any": ["planned_delivery_date"],
		"question_shape": "date_lookup",
		"value_mode": "planned_value",
		"event_basis": "planned_delivery_date",
	},
	{
		"entity_type": "sales_order",
		"entity_question_type": "sales_order_billing_progress",
		"required_metrics_any": ["billing_progress_percent"],
		"question_shape": "scalar_ratio",
		"value_mode": "current_value",
		"event_basis": "billing_progress",
	},
	{
		"entity_type": "sales_order",
		"entity_question_type": "sales_order_delivery_progress",
		"required_metrics_any": ["delivery_progress_percent"],
		"question_shape": "boolean_status",
		"value_mode": "current_value",
		"event_basis": "delivery_progress",
	},
	{
		"entity_type": "sales_order",
		"entity_question_type": "sales_order_document_status",
		"required_dimensions_any": ["document_status"],
		"question_shape": "dimension_lookup",
		"value_mode": "current_value",
		"event_basis": "document_status",
	},
	{
		"entity_type": "purchase_order",
		"entity_question_type": "purchase_order_actual_receipt_event_date",
		"required_dimensions_any": ["posting_date"],
		"question_shape": "date_lookup",
		"value_mode": "actual_value",
		"event_basis": "actual_receipt_event_date",
	},
	{
		"entity_type": "purchase_order",
		"entity_question_type": "purchase_order_planned_receipt_date",
		"required_dimensions_any": ["planned_receipt_date"],
		"question_shape": "date_lookup",
		"value_mode": "planned_value",
		"event_basis": "planned_receipt_date",
	},
	{
		"entity_type": "purchase_order",
		"entity_question_type": "purchase_order_billing_progress",
		"required_metrics_any": ["billing_progress_percent"],
		"question_shape": "scalar_ratio",
		"value_mode": "current_value",
		"event_basis": "billing_progress",
	},
	{
		"entity_type": "purchase_order",
		"entity_question_type": "purchase_order_receipt_progress",
		"required_metrics_any": ["receipt_progress_percent"],
		"question_shape": "boolean_status",
		"value_mode": "current_value",
		"event_basis": "receipt_progress",
	},
	{
		"entity_type": "purchase_order",
		"entity_question_type": "purchase_order_document_status",
		"required_dimensions_any": ["document_status"],
		"question_shape": "dimension_lookup",
		"value_mode": "current_value",
		"event_basis": "document_status",
	},
	{
		"entity_type": "sales_invoice",
		"entity_question_type": "sales_invoice_delivery_event_date",
		"required_concepts_all": ["fulfillment"],
		"required_dimensions_any": ["posting_date"],
		"question_shape": "date_lookup",
		"value_mode": "actual_value",
		"event_basis": "delivery_event_date",
	},
	{
		"entity_type": "sales_invoice",
		"entity_question_type": "sales_invoice_delivery_evidence",
		"required_concepts_all": ["fulfillment"],
		"question_shape": "boolean_status",
		"value_mode": "current_value",
		"event_basis": "delivery_evidence",
	},
]


def document_event_basis_specs() -> List[Dict[str, Any]]:
	return [dict(item) for item in _DOCUMENT_EVENT_BASIS_SPECS]


def document_event_supported_focus_grains() -> List[str]:
	return list(
		dict.fromkeys(
			_clean_text(item.get("entity_type"))
			for item in _DOCUMENT_EVENT_BASIS_SPECS
			if _clean_text(item.get("entity_type"))
		)
	)


def document_event_question_type_shape_map() -> Dict[str, Tuple[str, str]]:
	return {
		_clean_text(item.get("entity_question_type")): (
			_clean_text(item.get("question_shape")),
			_clean_text(item.get("value_mode")),
		)
		for item in _DOCUMENT_EVENT_BASIS_SPECS
		if _clean_text(item.get("entity_question_type"))
	}


def resolve_document_event_question_type(
	*,
	entity_type: str,
	requested_metrics: List[str],
	requested_dimensions: List[str],
	requested_concepts: List[str],
) -> str:
	clean_entity_type = _clean_text(entity_type)
	metric_set = _clean_set(requested_metrics)
	dimension_set = _clean_set(requested_dimensions)
	concept_set = _clean_set(requested_concepts)
	for item in _DOCUMENT_EVENT_BASIS_SPECS:
		if _clean_text(item.get("entity_type")) != clean_entity_type:
			continue
		required_concepts_all = _clean_set(item.get("required_concepts_all"))
		if required_concepts_all and not required_concepts_all.issubset(concept_set):
			continue
		required_dimensions_any = _clean_set(item.get("required_dimensions_any"))
		if required_dimensions_any and not required_dimensions_any.intersection(dimension_set):
			continue
		required_metrics_any = _clean_set(item.get("required_metrics_any"))
		if required_metrics_any and not required_metrics_any.intersection(metric_set):
			continue
		return _clean_text(item.get("entity_question_type"))
	return ""


def document_event_question_shape_and_value_mode(entity_question_type: str) -> Tuple[str, str]:
	return document_event_question_type_shape_map().get(_clean_text(entity_question_type), ("", ""))
