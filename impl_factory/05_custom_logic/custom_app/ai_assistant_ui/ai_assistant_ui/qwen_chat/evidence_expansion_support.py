from __future__ import annotations

from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.evidence_drilldown_registry import (
	DRILLDOWN_ANSWER_GOALS,
	DRILLDOWN_EVIDENCE_DEPTHS,
	LEGACY_EXPANSION_EVIDENCE_POLICIES,
	LEGACY_EXPANSION_OBLIGATIONS,
	build_governed_drilldown_plan,
	evidence_drilldown_user_guidance,
)
from ai_assistant_ui.qwen_chat.governed_scope_registry import list_active_entity_detail_scope_activations


CONTRACT_TYPE = "qwen_evidence_expansion_plan"
CONTRACT_VERSION = "1.0"
EXPANSION_EVIDENCE_POLICIES = set(LEGACY_EXPANSION_EVIDENCE_POLICIES)
EXPANSION_OBLIGATIONS = set(LEGACY_EXPANSION_OBLIGATIONS)


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _entity_detail_activations() -> List[Dict[str, Any]]:
	try:
		return [
			dict(item)
			for item in list_active_entity_detail_scope_activations()
			if isinstance(item, dict)
		]
	except Exception:
		return []


def _drilldown_requested(context: Dict[str, Any]) -> bool:
	return bool(
		_clean_text(context.get("evidence_depth")) in DRILLDOWN_EVIDENCE_DEPTHS
		or _clean_text(context.get("answer_goal")) in DRILLDOWN_ANSWER_GOALS
		or (
			_clean_text(context.get("answer_obligation")) in EXPANSION_OBLIGATIONS
			and _clean_text(context.get("evidence_policy")) in EXPANSION_EVIDENCE_POLICIES
		)
	)


def _adapt_governed_drilldown_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
	clean_plan = _clean_dict(plan)
	status = _clean_text(clean_plan.get("status"))
	legacy_status = "summary_row_only" if status == "source_detail_required" else status
	can_execute = bool(clean_plan.get("can_execute"))
	adapted: Dict[str, Any] = {
		"type": CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"status": legacy_status,
		"can_execute_expansion": can_execute,
		"expansion_mode": _clean_text(clean_plan.get("drilldown_mode") or "none") if can_execute else "none",
		"reason": _clean_text(clean_plan.get("reason")),
		"governed_drilldown_plan": clean_plan,
	}
	if status == "entity_detail_available" and isinstance(clean_plan.get("target_entity"), dict):
		adapted["target_entity"] = dict(clean_plan.get("target_entity") or {})
	return adapted


def build_evidence_expansion_plan(
	*,
	grounding_context: Dict[str, Any],
	focused_row: Dict[str, Any],
) -> Dict[str, Any]:
	"""Compatibility adapter over the governed drilldown registry.

	The public shape is kept for existing runtime callers, but the decision is
	now owned by a typed registry contract instead of this renderer-adjacent seam.
	"""

	context = _clean_dict(grounding_context)
	row = _clean_dict(focused_row)
	activations = _entity_detail_activations() if _drilldown_requested(context) and row else None
	drilldown_plan = build_governed_drilldown_plan(
		grounding_context=context,
		focused_row=row,
		entity_detail_activations=activations,
	)
	return _adapt_governed_drilldown_plan(drilldown_plan)


def evidence_expansion_user_guidance(plan: Dict[str, Any]) -> str:
	clean_plan = _clean_dict(plan)
	drilldown_plan = clean_plan.get("governed_drilldown_plan")
	if isinstance(drilldown_plan, dict):
		guidance = evidence_drilldown_user_guidance(drilldown_plan)
		if guidance:
			return guidance
	status = _clean_text(clean_plan.get("status"))
	if status == "entity_detail_available":
		target = _clean_dict(clean_plan.get("target_entity"))
		label = _clean_text(target.get("entity_label") or target.get("entity_key"))
		if label:
			return f"A deeper approved ERP detail source is available for {label}."
		return "A deeper approved ERP detail source is available for this row."
	if status == "summary_row_only":
		return (
			"The current result supports impact analysis and business interpretation for this row, "
			"but a true source breakdown needs an approved ERP detail view tied to it."
		)
	if status == "not_enough_evidence":
		return "The current result does not contain enough structured detail to expand this row safely."
	return ""
