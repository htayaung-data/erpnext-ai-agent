from __future__ import annotations

from typing import Any, Dict


_SCOPE_CLASS_BY_FAMILY = {
	"financial_statement": "financial_summary",
	"aging": "aging_analysis",
	"ranking_analytics": "ranked_entities",
	"inventory_snapshot": "inventory_summary",
	"product_profitability": "product_performance",
	"trend_analytics": "trend_analysis",
}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _normalized_scope_id(*, family_id: str, dimensions: Dict[str, Any]) -> str:
	family = _clean_text(family_id)
	source_grain = _clean_text((dimensions or {}).get("source_grain"))
	if family == "financial_statement":
		return _clean_text((dimensions or {}).get("statement_type")) or "financial_statement"
	if family == "aging":
		return _clean_text((dimensions or {}).get("aging_type")) or "aging"
	if family == "ranking_analytics":
		return {
			"aging_summary": "aging_ranking",
			"inventory_snapshot": "inventory_ranking",
			"grouped_profitability": "profitability_ranking",
			"aggregated_sales_history": "item_history_ranking",
			"entity_total": "sales_ranking",
		}.get(source_grain, "ranking_analytics")
	if family == "inventory_snapshot":
		return source_grain or "inventory_snapshot"
	if family == "product_profitability":
		return source_grain or "product_profitability"
	if family == "trend_analytics":
		return source_grain or "trend_analytics"
	return family


def build_analytical_scope_runtime_policy(
	*,
	family_id: str,
	report_name: str,
	dimensions: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	family = _clean_text(family_id)
	if family not in _SCOPE_CLASS_BY_FAMILY:
		return {}
	dimension_payload = dict(dimensions or {})
	scope_id = _normalized_scope_id(family_id=family, dimensions=dimension_payload)
	return {
		"type": "qwen_analytical_scope_runtime_policy",
		"family_id": family,
		"scope_id": scope_id,
		"scope_class": _SCOPE_CLASS_BY_FAMILY.get(family, ""),
		"compatibility_level": "full_consumption",
		"source_report": _clean_text(report_name),
		"source_grain": _clean_text(dimension_payload.get("source_grain")),
	}


def apply_analytical_scope_runtime_policy(
	*,
	family_id: str,
	report_name: str,
	dimensions: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	dimension_payload = dict(dimensions or {})
	policy = build_analytical_scope_runtime_policy(
		family_id=family_id,
		report_name=report_name,
		dimensions=dimension_payload,
	)
	if not policy:
		return dimension_payload
	dimension_payload.setdefault("scope_id", _clean_text(policy.get("scope_id")))
	dimension_payload.setdefault("scope_class", _clean_text(policy.get("scope_class")))
	dimension_payload["governed_scope_runtime_policy"] = policy
	return dimension_payload
