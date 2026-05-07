from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.entity_detail_request_support import entity_detail_capability_id
from ai_assistant_ui.qwen_chat.governed_scope_registry import list_active_entity_detail_scope_activations


CONTRACT_TYPE = "qwen_governed_evidence_drilldown_plan"
CONTRACT_VERSION = "1.0"

DRILLDOWN_EVIDENCE_DEPTHS = {"drilldown_preferred", "drilldown_required"}
DRILLDOWN_ANSWER_GOALS = {"expand_detail", "diagnose", "calculate"}
LEGACY_EXPANSION_EVIDENCE_POLICIES = {"evidence_expansion_preferred", "evidence_expansion_required"}
LEGACY_EXPANSION_OBLIGATIONS = {"expand_grounded_detail"}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _normalize_key(value: Any) -> str:
	text = _clean_text(value).lower()
	return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _normalized_text_set(values: List[Any]) -> set[str]:
	return {_normalize_key(value) for value in values if _normalize_key(value)}


def _decimal_value(value: Any) -> Decimal | None:
	text = _clean_text(value).replace(",", "").rstrip("%").strip()
	if not text:
		return None
	try:
		return Decimal(text)
	except (InvalidOperation, ValueError):
		return None


def _row_has_numeric_measure(row: Dict[str, Any]) -> bool:
	return any(_decimal_value(value) is not None for value in _clean_dict(row).values())


def _row_identity_values(row: Dict[str, Any]) -> Dict[str, str]:
	out: Dict[str, str] = {}
	for key, value in _clean_dict(row).items():
		if isinstance(value, (dict, list)):
			continue
		normalized = _normalize_key(key)
		clean_value = _clean_text(value)
		if normalized and clean_value:
			out[normalized] = clean_value
	for nested_key in ("join_key", "dimensions", "identity"):
		nested = _clean_dict(row.get(nested_key))
		for key, value in nested.items():
			normalized = _normalize_key(key)
			clean_value = _clean_text(value)
			if normalized and clean_value and normalized not in out:
				out[normalized] = clean_value
	return out


def _activation_identity_tokens(activation: Dict[str, Any]) -> set[str]:
	return _normalized_text_set(
		[
			activation.get("entity_grain"),
			activation.get("entity_label"),
			activation.get("entity_plural_label"),
			activation.get("identity_field"),
			activation.get("display_field"),
		]
	)


def _active_entity_detail_activations() -> List[Dict[str, Any]]:
	try:
		return [
			dict(item)
			for item in list_active_entity_detail_scope_activations()
			if isinstance(item, dict)
		]
	except Exception:
		return []


def _entity_reference_from_row(
	*,
	row: Dict[str, Any],
	entity_detail_activations: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
	row_values = _row_identity_values(row)
	if not row_values:
		return {}
	activations = (
		[dict(item) for item in entity_detail_activations if isinstance(item, dict)]
		if isinstance(entity_detail_activations, list)
		else _active_entity_detail_activations()
	)
	for activation in activations:
		entity_grain = _clean_text(activation.get("entity_grain"))
		if not entity_grain:
			continue
		capability_id = entity_detail_capability_id(entity_grain)
		if not capability_id:
			continue
		runtime_policy = _clean_dict(activation.get("runtime_policy"))
		if not bool(runtime_policy.get("can_execute")):
			continue
		for token in _activation_identity_tokens(activation):
			entity_value = row_values.get(token)
			if not entity_value:
				continue
			return {
				"entity_type": entity_grain,
				"entity_key": entity_value,
				"entity_label": entity_value,
				"capability_id": capability_id,
				"scope_id": _clean_text(activation.get("scope_id")),
			}
	return {}


def _source_signature(context: Dict[str, Any]) -> Dict[str, str]:
	source = _clean_dict(context.get("grounded_source"))
	summary = _clean_dict(context.get("grounding_summary"))
	return {
		"source_family_id": _clean_text(source.get("family_id") or context.get("family_id")),
		"source_capability_id": _clean_text(source.get("capability_id") or context.get("capability_id")),
		"source_name": _clean_text(
			summary.get("latest_assistant_title")
			or source.get("source_name")
			or context.get("source_name")
		),
	}


def _drilldown_requested(context: Dict[str, Any]) -> bool:
	answer_goal = _clean_text(context.get("answer_goal"))
	evidence_depth = _clean_text(context.get("evidence_depth"))
	if evidence_depth in DRILLDOWN_EVIDENCE_DEPTHS:
		return True
	if answer_goal in DRILLDOWN_ANSWER_GOALS:
		return True
	return bool(
		_clean_text(context.get("answer_obligation")) in LEGACY_EXPANSION_OBLIGATIONS
		and _clean_text(context.get("evidence_policy")) in LEGACY_EXPANSION_EVIDENCE_POLICIES
	)


def _base_plan(context: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"type": CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"answer_goal": _clean_text(context.get("answer_goal")),
		"evidence_depth": _clean_text(context.get("evidence_depth")),
		"business_role": _clean_text(context.get("business_role")),
		"target_reference": _clean_text(context.get("target_reference") or "unknown"),
		"risk_level": _clean_text(context.get("risk_level")),
		**_source_signature(context),
	}


def build_governed_drilldown_plan(
	*,
	grounding_context: Dict[str, Any],
	focused_row: Dict[str, Any],
	entity_detail_activations: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
	"""Classify whether deeper governed evidence is executable for a result row.

	The registry consumes typed reasoning slots and governed activation metadata.
	It intentionally does not inspect user prompt phrases.
	"""

	context = _clean_dict(grounding_context)
	row = _clean_dict(focused_row)
	plan = _base_plan(context)
	if not _drilldown_requested(context):
		return {
			**plan,
			"status": "not_applicable",
			"can_execute": False,
			"execution_mode": "none",
			"drilldown_mode": "none",
			"reason": "The typed reasoning context did not request governed drilldown evidence.",
		}
	if not row:
		return {
			**plan,
			"status": "focus_row_missing",
			"can_execute": False,
			"execution_mode": "none",
			"drilldown_mode": "none",
			"reason": "No focused result row was proven for the drilldown request.",
		}
	entity_reference = _entity_reference_from_row(
		row=row,
		entity_detail_activations=entity_detail_activations,
	)
	if entity_reference:
		return {
			**plan,
			"status": "entity_detail_available",
			"can_execute": True,
			"execution_mode": "entity_detail",
			"drilldown_mode": "entity_detail",
			"target_entity": entity_reference,
			"reason": "The focused row maps to an active executable governed entity-detail source.",
		}
	if _row_has_numeric_measure(row):
		return {
			**plan,
			"status": "source_detail_required",
			"can_execute": False,
			"execution_mode": "none",
			"drilldown_mode": "source_detail_required",
			"required_evidence_grain": "supporting_source_detail",
			"reason": "The focused row exposes summary measures, but no executable governed detail source was registered for that row.",
		}
	return {
		**plan,
		"status": "not_enough_evidence",
		"can_execute": False,
		"execution_mode": "none",
		"drilldown_mode": "none",
		"reason": "The focused row does not expose enough structured evidence for deeper governed drilldown.",
	}


def evidence_drilldown_user_guidance(plan: Dict[str, Any]) -> str:
	clean_plan = _clean_dict(plan)
	status = _clean_text(clean_plan.get("status"))
	if status == "entity_detail_available":
		target = _clean_dict(clean_plan.get("target_entity"))
		label = _clean_text(target.get("entity_label") or target.get("entity_key"))
		if label:
			return f"A deeper approved ERP detail source is available for {label}."
		return "A deeper approved ERP detail source is available for this row."
	if status == "source_detail_required":
		return (
			"The current result supports impact analysis and business interpretation for this row, "
			"but a true source breakdown needs an approved ERP detail view tied to it."
		)
	if status == "not_enough_evidence":
		return "The current result does not contain enough structured detail to expand this row safely."
	return ""
