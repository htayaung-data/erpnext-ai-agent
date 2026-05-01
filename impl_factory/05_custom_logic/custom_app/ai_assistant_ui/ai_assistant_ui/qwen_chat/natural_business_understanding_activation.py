from __future__ import annotations

from typing import Any, Dict, List

from .natural_business_understanding_contracts import CONTRACT_VERSION


PRESENTATION_ONLY_ACTIONS = {
	"ask_clarification",
	"show_supported_options",
	"reject_with_boundary",
	"out_of_scope_response",
	"answer_capability_question",
}

DELEGATED_ACTIONS = {
	"answer_from_current_artifact",
}

EXECUTION_REQUIRED_ACTIONS = {
	"execute_governed_requery",
	"execute_fresh_governed_query",
	"restore_previous_context",
	"clear_pending_context",
}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _confidence(value: Any) -> float:
	try:
		return max(0.0, min(1.0, float(value or 0.0)))
	except Exception:
		return 0.0


def _dedupe(values: List[str]) -> List[str]:
	return list(dict.fromkeys([value for value in values if value]))


def build_nbu_activation_assessment(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	"""Assess whether an NBU trace is eligible for controlled activation.

	This does not activate live behavior. It records whether the already-rendered
	NBU response is safe enough for a future activation slice to consume.
	"""

	trace = _clean_dict(trace_payload)
	decision = _clean_dict(trace.get("conversation_action_decision"))
	response = _clean_dict(trace.get("professional_response"))
	confidence_payload = _clean_dict(trace.get("system_confidence"))
	validation = _clean_dict(trace.get("validation_result"))
	requery = _clean_dict(trace.get("governed_requery_plan"))
	action = _clean_text(decision.get("action")) or _clean_text(response.get("action")) or "observe_only"
	response_mode = _clean_text(decision.get("response_mode")) or _clean_text(response.get("response_mode")) or "shadow_trace_only"
	final_confidence = _confidence(confidence_payload.get("final_confidence"))
	quality_warnings = _clean_list(response.get("quality_warnings"))
	blockers: List[str] = []
	warnings: List[str] = []
	activation_mode = "none"

	if action in DELEGATED_ACTIONS or response_mode == "direct_answer":
		blockers.append("delegated_to_existing_artifact_renderer")
	elif action in EXECUTION_REQUIRED_ACTIONS or response_mode == "governed_query":
		blockers.append("requires_execution_lane_activation")
	elif action in PRESENTATION_ONLY_ACTIONS:
		activation_mode = "presentation_only"
	else:
		blockers.append("action_not_in_controlled_activation_allowlist")

	if not bool(response.get("safe_to_show")):
		blockers.append("professional_response_not_safe_to_show")
	if quality_warnings:
		blockers.append("professional_response_quality_warnings")
		warnings.extend(quality_warnings)
	if _clean_text(validation.get("status")) in {"runtime_unavailable", "shadow_no_candidates"}:
		blockers.append("runtime_interpretation_not_ready")
	if not trace.get("candidate_interpretations"):
		blockers.append("missing_candidate_interpretation")
	if response_mode not in {"clarification", "boundary", "supported_options", "out_of_scope", "capability_guidance"} and action in PRESENTATION_ONLY_ACTIONS:
		blockers.append("response_mode_not_presentation_safe")
	if _clean_text(requery.get("status")) == "ready_shadow" and action in PRESENTATION_ONLY_ACTIONS:
		warnings.append("governed_requery_plan_available_but_not_executed")

	blockers = _dedupe(blockers)
	warnings = _dedupe(warnings)
	eligible = activation_mode == "presentation_only" and not blockers
	return {
		"type": "qwen_nbu_activation_assessment_contract",
		"contract_version": CONTRACT_VERSION,
		"activation_state": "eligible_shadow" if eligible else "blocked_shadow",
		"activation_mode": activation_mode,
		"eligible_for_controlled_activation": eligible,
		"live_execution_enabled": False,
		"action": action,
		"response_mode": response_mode,
		"final_confidence": final_confidence,
		"blockers": blockers,
		"warnings": warnings,
		"reason": (
			"NBU response is eligible for future presentation-only activation."
			if eligible
			else "NBU response remains shadow-only until blockers are resolved or a later activation lane owns execution."
		),
	}
