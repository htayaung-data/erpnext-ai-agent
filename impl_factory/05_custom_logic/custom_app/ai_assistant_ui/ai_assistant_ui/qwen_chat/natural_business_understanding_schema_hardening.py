from __future__ import annotations

from typing import Any, Dict, List

from .natural_business_understanding_contracts import (
	ALLOWED_ACTION_DECISIONS,
	ALLOWED_AUTHORITY_CLASSES,
	ALLOWED_EVIDENCE_NEEDS,
	ALLOWED_RESPONSE_MODES,
)
from .natural_business_understanding_decision import (
	MIN_CONFIDENCE_FOR_CURRENT_ARTIFACT_ANSWER,
	MIN_CONFIDENCE_FOR_GOVERNED_REQUERY,
)
from .natural_business_understanding_front_controller_cases import (
	list_nbu_front_controller_baseline_cases,
)
from .natural_business_understanding_quality_standard import (
	nbu_action_quality_expectations,
	validate_nbu_user_facing_response_text,
)
from .natural_business_understanding_validation import (
	POLICY_GATED_AUTHORITY_CLASSES,
	SAFE_AUTHORITY_CLASSES,
)


NBU_SCHEMA_HARDENING_VERSION = "1.0"

READY_REQUERY_STATUSES = {"ready_shadow", "ready", "planned"}
RESOLVED_CONTEXT_STATUSES = {"resolved"}
CONTEXT_TARGET_REFERENCES_REQUIRING_RESOLUTION = {
	"current_artifact",
	"previous_artifact",
	"rank_n",
	"named_entity",
	"selected_entity",
}


NBU_ACTION_SCHEMA_HARDENING_RULES: Dict[str, Dict[str, Any]] = {
	"answer_from_current_artifact": {
		"allowed_response_modes": ["direct_answer"],
		"min_final_confidence": MIN_CONFIDENCE_FOR_CURRENT_ARTIFACT_ANSWER,
		"required_evidence_needs": ["current_artifact_ok"],
		"allowed_authority_classes": ["safe_read", "safe_explanation"],
		"requires_selected_candidate": True,
		"requires_current_artifact_support": True,
		"requires_context_resolution_for_reference": True,
		"requires_safe_to_execute": True,
	},
	"execute_fresh_governed_query": {
		"allowed_response_modes": ["governed_query"],
		"min_final_confidence": MIN_CONFIDENCE_FOR_GOVERNED_REQUERY,
		"required_evidence_needs": ["needs_governed_requery"],
		"allowed_authority_classes": sorted(SAFE_AUTHORITY_CLASSES),
		"requires_selected_candidate": True,
		"requires_governed_requery_support": True,
		"requires_routing_change": True,
		"requires_safe_to_execute": True,
	},
	"execute_governed_requery": {
		"allowed_response_modes": ["governed_query"],
		"min_final_confidence": MIN_CONFIDENCE_FOR_GOVERNED_REQUERY,
		"required_evidence_needs": ["needs_governed_requery"],
		"allowed_authority_classes": sorted(SAFE_AUTHORITY_CLASSES),
		"requires_selected_candidate": True,
		"requires_governed_requery_support": True,
		"requires_context_resolution_for_reference": True,
		"requires_routing_change": True,
		"requires_safe_to_execute": True,
	},
	"ask_clarification": {
		"allowed_response_modes": ["clarification"],
		"min_final_confidence": 0.0,
		"required_evidence_needs": ["current_artifact_ok", "needs_governed_requery", "needs_clarification", "unknown"],
		"allowed_authority_classes": sorted(ALLOWED_AUTHORITY_CLASSES),
		"requires_selected_candidate": False,
		"requires_business_safe_response": True,
	},
	"show_supported_options": {
		"allowed_response_modes": ["supported_options"],
		"min_final_confidence": 0.0,
		"required_evidence_needs": ["needs_clarification", "needs_governed_requery", "unknown"],
		"allowed_authority_classes": sorted(ALLOWED_AUTHORITY_CLASSES),
		"requires_selected_candidate": False,
		"requires_business_safe_response": True,
	},
	"restore_previous_context": {
		"allowed_response_modes": ["clarification", "supported_options", "shadow_trace_only"],
		"min_final_confidence": 0.50,
		"required_evidence_needs": ["current_artifact_ok", "needs_clarification", "unknown"],
		"allowed_authority_classes": sorted(ALLOWED_AUTHORITY_CLASSES),
		"requires_context_resolution_for_reference": True,
	},
	"clear_pending_context": {
		"allowed_response_modes": ["clarification", "supported_options", "shadow_trace_only"],
		"min_final_confidence": 0.50,
		"required_evidence_needs": ["unknown", "needs_clarification"],
		"allowed_authority_classes": sorted(ALLOWED_AUTHORITY_CLASSES),
	},
	"reject_with_boundary": {
		"allowed_response_modes": ["boundary"],
		"min_final_confidence": 0.0,
		"required_evidence_needs": ["current_artifact_ok", "needs_governed_requery", "unsupported_policy", "unknown"],
		"allowed_authority_classes": sorted(POLICY_GATED_AUTHORITY_CLASSES),
		"requires_authority_boundary": True,
		"requires_business_safe_response": True,
	},
	"answer_capability_question": {
		"allowed_response_modes": ["capability_guidance"],
		"min_final_confidence": 0.0,
		"required_evidence_needs": ["unknown", "needs_clarification"],
		"allowed_authority_classes": sorted(ALLOWED_AUTHORITY_CLASSES),
		"requires_business_safe_response": True,
	},
	"out_of_scope_response": {
		"allowed_response_modes": ["out_of_scope"],
		"min_final_confidence": 0.0,
		"required_evidence_needs": ["out_of_scope", "unknown"],
		"allowed_authority_classes": sorted(ALLOWED_AUTHORITY_CLASSES),
		"requires_business_safe_response": True,
	},
	"observe_only": {
		"allowed_response_modes": ["shadow_trace_only"],
		"min_final_confidence": 0.0,
		"required_evidence_needs": ["unknown", "current_artifact_ok", "needs_governed_requery", "needs_clarification", "out_of_scope"],
		"allowed_authority_classes": sorted(ALLOWED_AUTHORITY_CLASSES),
	},
}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_float(value: Any) -> float:
	try:
		return max(0.0, min(1.0, float(value or 0.0)))
	except Exception:
		return 0.0


def _selected_candidate(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	trace = _clean_dict(trace_payload)
	selected_id = _clean_text(trace.get("selected_candidate_id"))
	candidates = trace.get("candidate_interpretations")
	if not isinstance(candidates, list):
		return {}
	for candidate in candidates:
		candidate_payload = _clean_dict(candidate)
		if selected_id and _clean_text(candidate_payload.get("candidate_id")) == selected_id:
			return candidate_payload
	if candidates:
		return _clean_dict(candidates[0])
	return {}


def _trace_action_payload(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("conversation_action_decision"))


def _trace_evidence_payload(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("evidence_plan"))


def _trace_authority_payload(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("authority_plan"))


def _trace_context_payload(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("context_resolution"))


def _trace_requery_payload(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	return _clean_dict(_clean_dict(trace_payload).get("governed_requery_plan"))


def _trace_final_confidence(trace_payload: Dict[str, Any]) -> float:
	system_confidence = _clean_dict(_clean_dict(trace_payload).get("system_confidence"))
	return _clean_float(system_confidence.get("final_confidence"))


def _target_reference_requires_resolution(candidate_payload: Dict[str, Any]) -> bool:
	target_reference = _clean_text(candidate_payload.get("target_reference")).lower()
	return target_reference in CONTEXT_TARGET_REFERENCES_REQUIRING_RESOLUTION


def _governed_requery_supports_execution(trace_payload: Dict[str, Any]) -> bool:
	evidence = _trace_evidence_payload(trace_payload)
	requery = _trace_requery_payload(trace_payload)
	if bool(evidence.get("governed_requery_available")):
		return True
	if bool(requery.get("shadow_execution_ready")):
		return True
	return _clean_text(requery.get("status")).lower() in READY_REQUERY_STATUSES


def list_nbu_action_schema_hardening_rules() -> List[Dict[str, Any]]:
	return [
		{"action": action, **dict(rule)}
		for action, rule in sorted(NBU_ACTION_SCHEMA_HARDENING_RULES.items())
	]


def nbu_confidence_threshold_for_action(action: str) -> float:
	rule = NBU_ACTION_SCHEMA_HARDENING_RULES.get(_clean_text(action), {})
	return _clean_float(rule.get("min_final_confidence"))


def validate_nbu_action_schema_hardening_rules() -> Dict[str, Any]:
	errors: List[str] = []
	rule_actions = set(NBU_ACTION_SCHEMA_HARDENING_RULES)
	for action in sorted(ALLOWED_ACTION_DECISIONS):
		if action not in rule_actions:
			errors.append(f"missing_action_schema_rule:{action}")
	for action in sorted(rule_actions.difference(ALLOWED_ACTION_DECISIONS)):
		errors.append(f"unknown_action_schema_rule:{action}")

	for action, rule in sorted(NBU_ACTION_SCHEMA_HARDENING_RULES.items()):
		modes = _clean_list(rule.get("allowed_response_modes"))
		if not modes:
			errors.append(f"{action}:missing_allowed_response_modes")
		for mode in modes:
			if mode not in ALLOWED_RESPONSE_MODES:
				errors.append(f"{action}:unknown_response_mode:{mode}")
		for evidence_need in _clean_list(rule.get("required_evidence_needs")):
			if evidence_need not in ALLOWED_EVIDENCE_NEEDS:
				errors.append(f"{action}:unknown_evidence_need:{evidence_need}")
		for authority_class in _clean_list(rule.get("allowed_authority_classes")):
			if authority_class not in ALLOWED_AUTHORITY_CLASSES:
				errors.append(f"{action}:unknown_authority_class:{authority_class}")
		if not (0.0 <= _clean_float(rule.get("min_final_confidence")) <= 1.0):
			errors.append(f"{action}:invalid_min_final_confidence")
		if not nbu_action_quality_expectations(action):
			errors.append(f"{action}:missing_quality_expectations")

	return {
		"ok": not errors,
		"schema_version": NBU_SCHEMA_HARDENING_VERSION,
		"rule_count": len(NBU_ACTION_SCHEMA_HARDENING_RULES),
		"errors": errors,
	}


def validate_nbu_trace_schema_hardening(
	trace_payload: Dict[str, Any],
	*,
	response_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	trace = _clean_dict(trace_payload)
	decision = _trace_action_payload(trace)
	candidate = _selected_candidate(trace)
	evidence = _trace_evidence_payload(trace)
	authority = _trace_authority_payload(trace)
	context = _trace_context_payload(trace)

	action = _clean_text(decision.get("action")) or "observe_only"
	response_mode = _clean_text(decision.get("response_mode")) or "shadow_trace_only"
	rule = NBU_ACTION_SCHEMA_HARDENING_RULES.get(action)
	errors: List[str] = []
	warnings: List[str] = []

	if action not in ALLOWED_ACTION_DECISIONS:
		errors.append(f"unknown_action:{action}")
	if response_mode not in ALLOWED_RESPONSE_MODES:
		errors.append(f"unknown_response_mode:{response_mode}")
	if not rule:
		errors.append(f"missing_action_rule:{action}")
		return {
			"ok": False,
			"schema_version": NBU_SCHEMA_HARDENING_VERSION,
			"action": action,
			"response_mode": response_mode,
			"errors": errors,
			"warnings": warnings,
		}

	if response_mode not in _clean_list(rule.get("allowed_response_modes")):
		errors.append(f"{action}:response_mode_not_allowed:{response_mode}")

	if bool(rule.get("requires_selected_candidate")) and not candidate:
		errors.append(f"{action}:missing_selected_candidate")

	evidence_need = _clean_text(candidate.get("evidence_need") or evidence.get("evidence_need") or "unknown").lower()
	required_evidence_needs = set(_clean_list(rule.get("required_evidence_needs")))
	if required_evidence_needs and evidence_need not in required_evidence_needs:
		errors.append(f"{action}:evidence_need_not_allowed:{evidence_need}")

	authority_class = _clean_text(candidate.get("authority_class") or authority.get("authority_class") or "unknown").lower()
	allowed_authority_classes = set(_clean_list(rule.get("allowed_authority_classes")))
	if allowed_authority_classes and authority_class not in allowed_authority_classes:
		errors.append(f"{action}:authority_class_not_allowed:{authority_class}")

	final_confidence = _trace_final_confidence(trace)
	min_confidence = _clean_float(rule.get("min_final_confidence"))
	if final_confidence < min_confidence:
		errors.append(f"{action}:confidence_below_threshold:{final_confidence:.2f}<{min_confidence:.2f}")

	if bool(rule.get("requires_current_artifact_support")) and not bool(evidence.get("current_artifact_supported")):
		errors.append(f"{action}:current_artifact_not_supported")

	if bool(rule.get("requires_governed_requery_support")) and not _governed_requery_supports_execution(trace):
		errors.append(f"{action}:governed_requery_not_ready")

	if bool(rule.get("requires_authority_boundary")):
		if authority_class not in POLICY_GATED_AUTHORITY_CLASSES:
			errors.append(f"{action}:missing_policy_gated_authority_class")
		if not _clean_text(authority.get("boundary_reason")) and not _clean_text(trace.get("boundary_reason")):
			warnings.append(f"{action}:missing_boundary_reason")

	if bool(rule.get("requires_context_resolution_for_reference")) and _target_reference_requires_resolution(candidate):
		context_status = _clean_text(context.get("status")).lower()
		if context_status not in RESOLVED_CONTEXT_STATUSES:
			errors.append(f"{action}:context_reference_not_resolved:{context_status or 'unknown'}")

	if bool(rule.get("requires_safe_to_execute")) and not bool(decision.get("safe_to_execute")):
		errors.append(f"{action}:safe_to_execute_false")

	if bool(rule.get("requires_routing_change")) and not bool(decision.get("requires_routing_change")):
		errors.append(f"{action}:requires_routing_change_false")

	if bool(rule.get("requires_business_safe_response")) and response_payload is not None:
		quality = validate_nbu_user_facing_response_text(response_payload)
		if not bool(quality.get("ok")):
			errors.extend([f"{action}:user_text_violation:{term}" for term in _clean_list(quality.get("violations"))])

	return {
		"ok": not errors,
		"schema_version": NBU_SCHEMA_HARDENING_VERSION,
		"action": action,
		"response_mode": response_mode,
		"min_final_confidence": min_confidence,
		"final_confidence": final_confidence,
		"errors": errors,
		"warnings": warnings,
	}


def validate_nbu_front_controller_schema_hardening() -> Dict[str, Any]:
	errors: List[str] = []
	rule_validation = validate_nbu_action_schema_hardening_rules()
	errors.extend(_clean_list(rule_validation.get("errors")))

	for case in list_nbu_front_controller_baseline_cases():
		action = _clean_text(case.get("expected_action"))
		if action not in NBU_ACTION_SCHEMA_HARDENING_RULES:
			errors.append(f"{_clean_text(case.get('case_id'))}:expected_action_missing_hardening_rule:{action}")

	return {
		"ok": not errors,
		"schema_version": NBU_SCHEMA_HARDENING_VERSION,
		"rule_count": len(NBU_ACTION_SCHEMA_HARDENING_RULES),
		"baseline_case_count": len(list_nbu_front_controller_baseline_cases()),
		"errors": errors,
	}
