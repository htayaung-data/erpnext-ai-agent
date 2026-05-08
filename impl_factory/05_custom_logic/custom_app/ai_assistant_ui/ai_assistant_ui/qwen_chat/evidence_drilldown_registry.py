from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.entity_detail_request_support import entity_detail_capability_id
from ai_assistant_ui.qwen_chat.governed_scope_registry import list_active_entity_detail_scope_activations
from ai_assistant_ui.qwen_chat.metadata import load_source_detail_drilldown_registry


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


def _source_signature(context: Dict[str, Any]) -> Dict[str, Any]:
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
		"source_reports": [
			_clean_text(value)
			for value in (source.get("source_reports") or [])
			if _clean_text(value)
		],
	}


def _source_detail_rules() -> List[Dict[str, Any]]:
	try:
		registry = load_source_detail_drilldown_registry()
	except Exception:
		return []
	rules = registry.get("source_detail_rules")
	if not isinstance(rules, list):
		return []
	return [dict(item) for item in rules if isinstance(item, dict)]


def _normalized_match(value: Any, candidates: List[Any]) -> bool:
	normalized_value = _normalize_key(value)
	if not normalized_value:
		return False
	for candidate in candidates:
		normalized_candidate = _normalize_key(candidate)
		if not normalized_candidate:
			continue
		if normalized_candidate in normalized_value or normalized_value in normalized_candidate:
			return True
	return False


def _source_values_match(value: Any, allowed_values: List[Any]) -> bool:
	if not allowed_values:
		return True
	return _normalized_match(value, allowed_values)


def _context_statement_type(context: Dict[str, Any]) -> str:
	metrics = _clean_dict(context.get("artifact_metrics"))
	return _clean_text(metrics.get("statement_type"))


def _row_identity_matches_rule(row: Dict[str, Any], rule: Dict[str, Any]) -> bool:
	match_spec = _clean_dict(rule.get("row_identity_match"))
	conditions = match_spec.get("any")
	if not isinstance(conditions, list) or not conditions:
		return False
	row_values = _row_identity_values(row)
	for condition in conditions:
		if not isinstance(condition, dict):
			continue
		fields = [_normalize_key(value) for value in (condition.get("fields") or []) if _normalize_key(value)]
		values = [value for value in (condition.get("normalized_values") or []) if _clean_text(value)]
		if not fields or not values:
			continue
		for field in fields:
			row_value = row_values.get(field)
			if row_value and _normalized_match(row_value, values):
				return True
	return False


def _template_value(template: Any, *, context: Dict[str, Any], row: Dict[str, Any]) -> Any:
	text = _clean_text(template)
	if not text:
		return ""
	parts = [_normalize_key(part) for part in text.split(".") if _normalize_key(part)]
	if not parts:
		return text
	root = parts[0]
	if root == "row" and len(parts) >= 2:
		return _row_identity_values(row).get(parts[1], "")
	if root in {"artifact_filters", "artifact_period", "artifact_metrics"}:
		obj: Any = _clean_dict(context.get(root))
		for part in parts[1:]:
			if not isinstance(obj, dict):
				return ""
			obj = obj.get(part)
		return obj
	if root == "grounded_source":
		obj = _clean_dict(context.get("grounded_source"))
		for part in parts[1:]:
			if not isinstance(obj, dict):
				return ""
			obj = obj.get(part)
		return obj
	return text


def _target_filters_for_rule(*, rule: Dict[str, Any], context: Dict[str, Any], row: Dict[str, Any]) -> Dict[str, Any]:
	target_report = _clean_dict(rule.get("target_report"))
	templates = _clean_dict(target_report.get("filter_templates"))
	filters: Dict[str, Any] = {}
	for key, template in templates.items():
		clean_key = _clean_text(key)
		if not clean_key:
			continue
		value = _template_value(template, context=context, row=row)
		if _clean_text(value):
			filters[clean_key] = value
	return filters


def _registered_source_detail_plan(context: Dict[str, Any], row: Dict[str, Any]) -> Dict[str, Any]:
	signature = _source_signature(context)
	source_names = [
		signature.get("source_name"),
		*(signature.get("source_reports") if isinstance(signature.get("source_reports"), list) else []),
	]
	statement_type = _context_statement_type(context)
	for rule in _source_detail_rules():
		if not _source_values_match(signature.get("source_family_id"), rule.get("source_family_ids") or []):
			continue
		if not _source_values_match(signature.get("source_capability_id"), rule.get("source_capability_ids") or []):
			continue
		if (rule.get("source_names") or []) and not any(
			_source_values_match(source_name, rule.get("source_names") or [])
			for source_name in source_names
		):
			continue
		if not _source_values_match(statement_type, rule.get("source_statement_types") or []):
			continue
		if not _row_identity_matches_rule(row, rule):
			continue
		target_report = _clean_dict(rule.get("target_report"))
		report_name = _clean_text(target_report.get("report_name"))
		target_filters = _target_filters_for_rule(rule=rule, context=context, row=row)
		if not report_name or not target_filters.get("company") or not target_filters.get("account"):
			return {
				"status": "source_detail_required",
				"can_execute": False,
				"execution_mode": "none",
				"drilldown_mode": "source_detail_required",
				"required_evidence_grain": "supporting_source_detail",
				"source_detail_rule_id": _clean_text(rule.get("rule_id")),
				"reason": "A governed source-detail rule matched, but required execution filters were not proven.",
			}
		return {
			"status": "source_detail_available",
			"can_execute": True,
			"execution_mode": "source_detail_report",
			"drilldown_mode": "source_detail",
			"required_evidence_grain": "supporting_source_detail",
			"source_detail_rule_id": _clean_text(rule.get("rule_id")),
			"target_report": {
				"report_name": report_name,
				"capability_id": _clean_text(target_report.get("capability_id")),
				"family_id": _clean_text(target_report.get("family_id")),
				"filters": target_filters,
				"target_limit": int(target_report.get("target_limit") or 100),
			},
			"rendering": _clean_dict(rule.get("rendering")),
			"reason": "The focused row maps to a registered executable governed source-detail report.",
		}
	return {}


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
	source_detail_plan = _registered_source_detail_plan(context, row)
	if source_detail_plan:
		return {
			**plan,
			**source_detail_plan,
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
	if status == "source_detail_available":
		target = _clean_dict(clean_plan.get("target_report"))
		report_name = _clean_text(target.get("report_name"))
		if report_name:
			return f"A deeper approved ERP source-detail report is available: {report_name}."
		return "A deeper approved ERP source-detail report is available for this row."
	if status == "source_detail_required":
		return (
			"The current result supports impact analysis and business interpretation for this row, "
			"but a true source breakdown needs an approved ERP detail view tied to it."
		)
	if status == "not_enough_evidence":
		return "The current result does not contain enough structured detail to expand this row safely."
	return ""
