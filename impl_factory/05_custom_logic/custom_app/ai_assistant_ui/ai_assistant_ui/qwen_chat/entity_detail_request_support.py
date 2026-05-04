from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.entity_detail_clarification import (
	customer_operational_document_choices,
	customer_tenure_basis_choices,
)
from ai_assistant_ui.qwen_chat.customer_lifecycle_basis import (
	customer_lifecycle_dimension_basis_map,
	customer_lifecycle_tenure_metric_basis_map,
)
from ai_assistant_ui.qwen_chat.document_event_basis import (
	document_event_question_shape_and_value_mode,
	resolve_document_event_question_type,
)


def _ordered_unique_values(values: List[str] | None) -> List[str]:
	ordered: List[str] = []
	for value in values or []:
		clean = str(value or "").strip()
		if clean and clean not in ordered:
			ordered.append(clean)
	return ordered


def entity_detail_capability_id(entity_type: str) -> str:
	entity_key = str(entity_type or "").strip().lower()
	capability_by_entity_type = {
		"customer": "accounts_receivable_read",
		"supplier": "accounts_payable_read",
		"item": "stock_read",
		"product": "stock_read",
		"purchase_order": "purchase_order_read",
		"sales_order": "sales_order_read",
		"sales_invoice": "sales_read",
	}
	return str(capability_by_entity_type.get(entity_key) or "").strip()


def _artifact_has_stock_position_sections(artifact_payload: Dict[str, Any]) -> bool:
	artifact = artifact_payload if isinstance(artifact_payload, dict) else {}
	sections = artifact.get("sections") if isinstance(artifact.get("sections"), dict) else {}
	return bool(
		isinstance(sections.get("stock_rows"), list)
		or isinstance(sections.get("warehouse_totals"), list)
		or isinstance(sections.get("item_totals"), list)
	)


def _normalize_stock_position_requested_metrics(requested_metrics: List[str]) -> List[str]:
	metric_aliases = {
		"quantity": "balance_qty",
		"qty": "balance_qty",
		"stock_qty": "balance_qty",
		"stock_quantity": "balance_qty",
		"balance_qty": "balance_qty",
		"value": "balance_value",
		"stock_value": "balance_value",
		"inventory_value": "balance_value",
		"balance_value": "balance_value",
	}
	return _ordered_unique_values(
		[
			str(metric_aliases.get(str(value or "").strip(), str(value or "").strip()) or "").strip()
			for value in (requested_metrics or [])
		]
	)


def _customer_basis_from_entity_detail_request(
	requested_metrics: List[str],
	requested_dimensions: List[str],
) -> tuple[str, str]:
	tenure_metric_basis = customer_lifecycle_tenure_metric_basis_map()
	lifecycle_dimension_basis = customer_lifecycle_dimension_basis_map()
	for metric_key in requested_metrics:
		if metric_key in tenure_metric_basis:
			return "customer_tenure", tenure_metric_basis[metric_key]
	for dimension_key in requested_dimensions:
		if dimension_key in lifecycle_dimension_basis and "tenure" in requested_metrics:
			return "customer_tenure", lifecycle_dimension_basis[dimension_key]
	if "tenure" in requested_metrics:
		return "customer_tenure", ""
	for dimension_key in requested_dimensions:
		if dimension_key in lifecycle_dimension_basis:
			return "customer_lifecycle_date", lifecycle_dimension_basis[dimension_key]
	if "dominant_aging_bucket" in requested_dimensions:
		return "customer_aging_bucket", ""
	return "", ""


def _non_customer_entity_detail_question_type(
	*,
	entity_type: str,
	requested_metrics: List[str],
	requested_dimensions: List[str],
	requested_concepts: List[str],
) -> str:
	return resolve_document_event_question_type(
		entity_type=entity_type,
		requested_metrics=requested_metrics,
		requested_dimensions=requested_dimensions,
		requested_concepts=requested_concepts,
	)


def _item_entity_detail_question_type(
	*,
	requested_metrics: List[str],
	requested_dimensions: List[str],
	requested_concepts: List[str],
	artifact_payload: Dict[str, Any],
) -> tuple[str, List[str]]:
	if not _artifact_has_stock_position_sections(artifact_payload):
		return "", _ordered_unique_values(requested_metrics)
	normalized_metrics = _normalize_stock_position_requested_metrics(requested_metrics)
	requested_metric_set = {
		str(value or "").strip()
		for value in normalized_metrics
		if str(value or "").strip()
	}
	requested_dimension_set = {
		str(value or "").strip()
		for value in requested_dimensions
		if str(value or "").strip()
	}
	requested_concept_set = {
		str(value or "").strip()
		for value in requested_concepts
		if str(value or "").strip()
	}
	stock_position_requested = bool(
		requested_metric_set.intersection({"balance_qty", "balance_value"})
		or "warehouse" in requested_dimension_set
		or "inventory" in requested_concept_set
	)
	if not stock_position_requested:
		return "", normalized_metrics
	return "item_stock_position", normalized_metrics


def _entity_detail_question_shape_and_value_mode(
	*,
	entity_type: str,
	entity_question_type: str,
	requested_metrics: List[str],
	requested_dimensions: List[str],
) -> tuple[str, str]:
	if entity_question_type == "customer_tenure":
		return "scalar_duration", "current_value"
	if entity_question_type == "customer_lifecycle_date":
		return "date_lookup", "first_value"
	if entity_question_type == "customer_aging_bucket":
		return "dimension_lookup", "dominant_value"
	document_event_shape, document_event_value_mode = document_event_question_shape_and_value_mode(entity_question_type)
	if document_event_shape and document_event_value_mode:
		return document_event_shape, document_event_value_mode
	if entity_question_type == "item_stock_position":
		return "dimension_lookup", "current_value"
	if "dominant_aging_bucket" in requested_dimensions:
		return "dimension_lookup", "dominant_value"
	if "overdue_only" in requested_metrics or "credit_balance_only" in requested_metrics:
		return "boolean_status", "current_value"
	if any(metric in requested_metrics for metric in ("overdue_total", "outstanding_total", "total_due", "credit_limit_available")):
		return "scalar_amount", "current_value"
	if any(metric in requested_metrics for metric in ("overdue_ratio", "credit_limit_utilization_ratio")):
		return "scalar_ratio", "current_value"
	if requested_dimensions or requested_metrics:
		return "dimension_lookup", "current_value"
	if str(entity_type or "").strip():
		return "profile_request", "current_value"
	return "", ""


def resolve_entity_detail_request_interpretation(
	*,
	entity_type: str,
	requested_metrics: List[str],
	requested_dimensions: List[str],
	requested_concepts: List[str],
	artifact_payload: Dict[str, Any],
) -> Dict[str, Any]:
	normalized_metrics = _ordered_unique_values(requested_metrics)
	entity_question_type = ""
	basis = ""
	clarification_required = False
	clarification_reason_type = ""
	clarification_options: List[str] = []

	if entity_type == "customer":
		entity_question_type, basis = _customer_basis_from_entity_detail_request(
			requested_metrics=normalized_metrics,
			requested_dimensions=requested_dimensions,
		)
		if entity_question_type == "customer_tenure" and basis:
			normalized_metrics = [value for value in normalized_metrics if value != "tenure"]
		if entity_question_type == "customer_tenure" and not basis:
			clarification_required = True
			clarification_reason_type = "customer_tenure_basis_missing"
			clarification_options = [
				str(item.get("label") or "").strip()
				for item in customer_tenure_basis_choices()
				if str(item.get("label") or "").strip()
			]
		elif "posting_date" in requested_dimensions and not entity_question_type:
			clarification_required = True
			clarification_reason_type = "customer_operational_document_missing"
			clarification_options = [
				str(item.get("label") or "").strip()
				for item in customer_operational_document_choices()
				if str(item.get("label") or "").strip()
			]
	elif entity_type == "item":
		entity_question_type, normalized_metrics = _item_entity_detail_question_type(
			requested_metrics=normalized_metrics,
			requested_dimensions=requested_dimensions,
			requested_concepts=requested_concepts,
			artifact_payload=artifact_payload,
		)
	else:
		entity_question_type = _non_customer_entity_detail_question_type(
			entity_type=entity_type,
			requested_metrics=normalized_metrics,
			requested_dimensions=requested_dimensions,
			requested_concepts=requested_concepts,
		)

	question_shape, value_mode = _entity_detail_question_shape_and_value_mode(
		entity_type=entity_type,
		entity_question_type=entity_question_type,
		requested_metrics=normalized_metrics,
		requested_dimensions=requested_dimensions,
	)
	return {
		"requested_metrics": normalized_metrics,
		"entity_question_type": entity_question_type,
		"basis": basis,
		"clarification_required": clarification_required,
		"clarification_reason_type": clarification_reason_type,
		"clarification_options": clarification_options,
		"question_shape": question_shape,
		"value_mode": value_mode,
	}
