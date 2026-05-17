from __future__ import annotations

from typing import Any, Dict, List

from .natural_business_understanding_evaluation_harness import (
	DEFAULT_LATENCY_BUDGET_MS,
	evaluate_nbu_trace_against_front_controller_case,
)
from .natural_business_understanding_schema_hardening import (
	nbu_confidence_threshold_for_action,
)


NBU_ROUTER_SCORECARD_VERSION = "1.0"

NBU_ROUTER_SCORECARD_OUTCOMES: List[Dict[str, str]] = [
	{
		"outcome": "both_correct",
		"meaning": "NBU and the current router both match the labelled business expectation.",
	},
	{
		"outcome": "nbu_correct_current_wrong",
		"meaning": "NBU matches the labelled expectation and the current router does not.",
	},
	{
		"outcome": "current_correct_nbu_wrong",
		"meaning": "The current router matches the labelled expectation and NBU does not.",
	},
	{
		"outcome": "both_wrong",
		"meaning": "Neither NBU nor the current router matches the labelled expectation.",
	},
	{
		"outcome": "nbu_unsafe",
		"meaning": "NBU output fails a user-facing, validation, or schema safety gate.",
	},
	{
		"outcome": "nbu_low_confidence",
		"meaning": "NBU points in the right shape but confidence is below the action threshold.",
	},
]


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
		return float(value or 0.0)
	except Exception:
		return 0.0


def _dedupe(values: List[str]) -> List[str]:
	return list(dict.fromkeys([_clean_text(value) for value in values if _clean_text(value)]))


def _outcome_ids() -> List[str]:
	return [_clean_text(row.get("outcome")) for row in NBU_ROUTER_SCORECARD_OUTCOMES]


def list_nbu_router_scorecard_outcomes() -> List[Dict[str, str]]:
	return [dict(row) for row in NBU_ROUTER_SCORECARD_OUTCOMES]


def validate_nbu_router_scorecard_contract() -> Dict[str, Any]:
	required = {
		"both_correct",
		"nbu_correct_current_wrong",
		"current_correct_nbu_wrong",
		"both_wrong",
		"nbu_unsafe",
		"nbu_low_confidence",
	}
	errors: List[str] = []
	outcomes = _outcome_ids()
	for outcome in sorted(required.difference(outcomes)):
		errors.append(f"missing_scorecard_outcome:{outcome}")
	for outcome in outcomes:
		if outcomes.count(outcome) > 1:
			errors.append(f"duplicate_scorecard_outcome:{outcome}")
	for row in NBU_ROUTER_SCORECARD_OUTCOMES:
		if not _clean_text(row.get("meaning")):
			errors.append(f"{_clean_text(row.get('outcome'))}:missing_meaning")
	return {
		"ok": not errors,
		"schema_version": NBU_ROUTER_SCORECARD_VERSION,
		"outcome_count": len(NBU_ROUTER_SCORECARD_OUTCOMES),
		"errors": _dedupe(errors),
	}


def _default_response_mode_for_action(action: str) -> str:
	action = _clean_text(action)
	if action in {"execute_fresh_governed_query", "execute_governed_requery"}:
		return "governed_query"
	if action == "answer_from_current_artifact":
		return "direct_answer"
	if action == "ask_clarification":
		return "clarification"
	if action == "show_supported_options":
		return "supported_options"
	if action == "reject_with_boundary":
		return "boundary"
	if action == "answer_capability_question":
		return "capability_guidance"
	if action == "out_of_scope_response":
		return "out_of_scope"
	return "shadow_trace_only"


def _default_evidence_need_for_action(action: str) -> str:
	action = _clean_text(action)
	if action == "answer_from_current_artifact":
		return "current_artifact_ok"
	if action in {"execute_fresh_governed_query", "execute_governed_requery"}:
		return "needs_governed_requery"
	if action in {"ask_clarification", "show_supported_options"}:
		return "needs_clarification"
	if action == "reject_with_boundary":
		return "unsupported_policy"
	if action == "out_of_scope_response":
		return "out_of_scope"
	return "unknown"


def _default_authority_class_for_action(action: str) -> str:
	action = _clean_text(action)
	if action == "reject_with_boundary":
		return "recommendation"
	if action == "answer_from_current_artifact":
		return "safe_explanation"
	if action in {"execute_fresh_governed_query", "execute_governed_requery"}:
		return "safe_read"
	return "unknown"


def build_current_router_trace_from_outcome(current_router_outcome: Dict[str, Any]) -> Dict[str, Any]:
	outcome = _clean_dict(current_router_outcome)
	action = _clean_text(outcome.get("action")) or "observe_only"
	response_mode = _clean_text(outcome.get("response_mode")) or _default_response_mode_for_action(action)
	evidence_need = _clean_text(outcome.get("evidence_need")) or _default_evidence_need_for_action(action)
	authority_class = _clean_text(outcome.get("authority_class")) or _default_authority_class_for_action(action)
	candidate_id = _clean_text(outcome.get("candidate_id")) or "current-router-candidate"
	rank = int(outcome.get("rank") or 0)
	family_ids = (
		_clean_list(outcome.get("candidate_composite_family_ids"))
		+ _clean_list(outcome.get("family_ids"))
	)
	if _clean_text(outcome.get("preferred_family_id")):
		family_ids.append(_clean_text(outcome.get("preferred_family_id")))
	if _clean_text(outcome.get("fallback_family_id")):
		family_ids.append(_clean_text(outcome.get("fallback_family_id")))

	final_confidence = _clean_float(outcome.get("final_confidence"))
	if final_confidence <= 0.0:
		final_confidence = 0.90

	requery_status = _clean_text(outcome.get("governed_requery_status"))
	requires_execution = action in {"execute_fresh_governed_query", "execute_governed_requery"}
	if requires_execution and not requery_status:
		requery_status = "ready_shadow"

	candidate = {
		"candidate_id": candidate_id,
		"business_domain": _clean_text(outcome.get("business_domain")),
		"target_reference": _clean_text(outcome.get("target_reference")) or "none",
		"target_entity": {"rank": rank} if rank else {},
		"candidate_capability_ids": _clean_list(outcome.get("candidate_capability_ids")),
		"candidate_report_names": _clean_list(outcome.get("candidate_report_names")),
		"candidate_composite_family_ids": _dedupe(family_ids),
		"requested_metrics": _clean_list(outcome.get("requested_metrics")),
		"requested_dimensions": _clean_list(outcome.get("requested_dimensions")),
		"evidence_need": evidence_need,
		"authority_class": authority_class,
		"model_confidence": final_confidence,
	}
	current_artifact_family = (
		_clean_text(outcome.get("current_artifact_family_id"))
		or _clean_text(outcome.get("artifact_family"))
		or (family_ids[0] if family_ids else "")
	)

	return {
		"type": "qwen_current_router_outcome_as_nbu_trace",
		"schema_version": NBU_ROUTER_SCORECARD_VERSION,
		"selected_candidate_id": candidate_id,
		"candidate_interpretations": [candidate],
		"system_confidence": {"final_confidence": final_confidence},
		"validation_result": {
			"status": _clean_text(outcome.get("validation_status")) or "validated",
			"validation_errors": _clean_list(outcome.get("validation_errors")),
			"validation_warnings": _clean_list(outcome.get("validation_warnings")),
		},
		"conversation_action_decision": {
			"action": action,
			"response_mode": response_mode,
			"requires_routing_change": requires_execution,
			"safe_to_execute": bool(outcome.get("safe_to_execute", action in {
				"answer_from_current_artifact",
				"execute_fresh_governed_query",
				"execute_governed_requery",
			})),
		},
		"evidence_plan": {
			"evidence_need": evidence_need,
			"current_artifact_supported": bool(outcome.get("current_artifact_supported", evidence_need == "current_artifact_ok")),
			"governed_requery_available": bool(outcome.get("governed_requery_available", evidence_need == "needs_governed_requery")),
			"missing_fields": _clean_list(outcome.get("missing_fields")),
		},
		"authority_plan": {
			"authority_class": authority_class,
			"boundary_reason": _clean_text(outcome.get("boundary_reason")),
		},
		"context_resolution": {
			"status": _clean_text(outcome.get("context_status")) or ("resolved" if rank or current_artifact_family else "not_required"),
			"target_reference": _clean_text(outcome.get("target_reference")) or "none",
			"resolved_artifact_id": _clean_text(outcome.get("resolved_artifact_id")) or current_artifact_family,
			"resolved_rank": rank,
		},
		"governed_requery_plan": {
			"status": requery_status or _clean_text(outcome.get("governed_requery_status")) or "not_required",
			"shadow_execution_ready": bool(outcome.get("shadow_execution_ready", requires_execution)),
			"target_capability_ids": _clean_list(outcome.get("target_capability_ids")),
			"target_report_names": _clean_list(outcome.get("target_report_names")),
			"target_composite_family_ids": _clean_list(outcome.get("target_composite_family_ids")),
			"requested_metrics": _clean_list(outcome.get("requested_metrics")),
			"requested_dimensions": _clean_list(outcome.get("requested_dimensions")),
		},
		"professional_response": {
			"title": _clean_text(outcome.get("response_title")) or "Current Router Outcome",
			"answer_text": _clean_text(outcome.get("response_text")) or "Current router outcome.",
			"next_steps": _clean_list(outcome.get("next_steps")),
			"safe_to_show": bool(outcome.get("response_safe_to_show", response_mode != "direct_answer")),
			"quality_warnings": _clean_list(outcome.get("quality_warnings")),
		},
		"schema_hardening_assessment": {
			"ok": bool(outcome.get("schema_ok", True)),
			"errors": _clean_list(outcome.get("schema_errors")),
			"warnings": _clean_list(outcome.get("schema_warnings")),
		},
		"activation_assessment": {"blockers": _clean_list(outcome.get("activation_blockers"))},
		"current_artifact": {"family_id": current_artifact_family},
	}


def evaluate_current_router_outcome_against_front_controller_case(
	*,
	case_payload: Dict[str, Any],
	current_router_outcome: Dict[str, Any],
	latency_ms: int | float | None = None,
	latency_budget_ms: int = DEFAULT_LATENCY_BUDGET_MS,
) -> Dict[str, Any]:
	return evaluate_nbu_trace_against_front_controller_case(
		case_payload=case_payload,
		trace_payload=build_current_router_trace_from_outcome(current_router_outcome),
		latency_ms=latency_ms,
		latency_budget_ms=latency_budget_ms,
	)


def _schema_errors(trace_payload: Dict[str, Any]) -> List[str]:
	schema = _clean_dict(_clean_dict(trace_payload).get("schema_hardening_assessment"))
	return _clean_list(schema.get("errors"))


def _trace_action(trace_payload: Dict[str, Any], evaluation_report: Dict[str, Any]) -> str:
	return _clean_text(
		_clean_dict(_clean_dict(trace_payload).get("conversation_action_decision")).get("action")
	) or _clean_text(evaluation_report.get("actual_action"))


def _trace_final_confidence(trace_payload: Dict[str, Any]) -> float:
	return _clean_float(_clean_dict(_clean_dict(trace_payload).get("system_confidence")).get("final_confidence"))


def _nbu_low_confidence(trace_payload: Dict[str, Any], evaluation_report: Dict[str, Any]) -> bool:
	action = _trace_action(trace_payload, evaluation_report)
	threshold = nbu_confidence_threshold_for_action(action)
	final_confidence = _trace_final_confidence(trace_payload)
	schema_errors = _schema_errors(trace_payload)
	if any("confidence_below_threshold" in error or "insufficient_confidence" in error for error in schema_errors):
		return True
	return threshold > 0.0 and final_confidence < threshold


def _nbu_unsafe(trace_payload: Dict[str, Any], evaluation_report: Dict[str, Any]) -> bool:
	if _nbu_low_confidence(trace_payload, evaluation_report):
		return False
	failure_buckets = set(_clean_list(evaluation_report.get("failure_buckets")))
	if "renderer_quality_failure" in failure_buckets or "validation_gate_failure" in failure_buckets:
		return True
	schema = _clean_dict(_clean_dict(trace_payload).get("schema_hardening_assessment"))
	return bool(schema) and not bool(schema.get("ok", True))


def build_nbu_vs_current_router_scorecard(
	*,
	case_payload: Dict[str, Any],
	nbu_trace_payload: Dict[str, Any],
	current_router_outcome: Dict[str, Any],
	nbu_latency_ms: int | float | None = None,
	current_router_latency_ms: int | float | None = None,
	latency_budget_ms: int = DEFAULT_LATENCY_BUDGET_MS,
) -> Dict[str, Any]:
	case = _clean_dict(case_payload)
	nbu_trace = _clean_dict(nbu_trace_payload)
	nbu_evaluation = evaluate_nbu_trace_against_front_controller_case(
		case_payload=case,
		trace_payload=nbu_trace,
		latency_ms=nbu_latency_ms,
		latency_budget_ms=latency_budget_ms,
	)
	current_evaluation = evaluate_current_router_outcome_against_front_controller_case(
		case_payload=case,
		current_router_outcome=current_router_outcome,
		latency_ms=current_router_latency_ms,
		latency_budget_ms=latency_budget_ms,
	)
	nbu_passed = bool(nbu_evaluation.get("passed"))
	current_passed = bool(current_evaluation.get("passed"))

	if _nbu_unsafe(nbu_trace, nbu_evaluation):
		outcome = "nbu_unsafe"
	elif _nbu_low_confidence(nbu_trace, nbu_evaluation):
		outcome = "nbu_low_confidence"
	elif nbu_passed and current_passed:
		outcome = "both_correct"
	elif nbu_passed and not current_passed:
		outcome = "nbu_correct_current_wrong"
	elif current_passed and not nbu_passed:
		outcome = "current_correct_nbu_wrong"
	else:
		outcome = "both_wrong"

	return {
		"type": "qwen_nbu_vs_current_router_scorecard",
		"schema_version": NBU_ROUTER_SCORECARD_VERSION,
		"case_id": _clean_text(case.get("case_id")),
		"expected_action": _clean_text(case.get("expected_action")),
		"scorecard_outcome": outcome,
		"nbu_passed": nbu_passed,
		"current_router_passed": current_passed,
		"nbu_actual_action": _clean_text(nbu_evaluation.get("actual_action")),
		"current_router_actual_action": _clean_text(current_evaluation.get("actual_action")),
		"nbu_failure_buckets": _clean_list(nbu_evaluation.get("failure_buckets")),
		"current_router_failure_buckets": _clean_list(current_evaluation.get("failure_buckets")),
		"nbu_diagnostic_buckets": _clean_list(nbu_evaluation.get("diagnostic_buckets")),
		"current_router_diagnostic_buckets": _clean_list(current_evaluation.get("diagnostic_buckets")),
		"nbu_evaluation": nbu_evaluation,
		"current_router_evaluation": current_evaluation,
		"oracle_source": "front_controller_baseline_case",
	}


def summarize_nbu_router_scorecards(scorecards: List[Dict[str, Any]]) -> Dict[str, Any]:
	cards = [_clean_dict(card) for card in scorecards if isinstance(card, dict)]
	counts = {outcome: 0 for outcome in _outcome_ids()}
	for card in cards:
		outcome = _clean_text(card.get("scorecard_outcome"))
		if outcome in counts:
			counts[outcome] += 1
	nbu_pass_count = sum(1 for card in cards if bool(card.get("nbu_passed")))
	current_pass_count = sum(1 for card in cards if bool(card.get("current_router_passed")))
	return {
		"type": "qwen_nbu_vs_current_router_scorecard_summary",
		"schema_version": NBU_ROUTER_SCORECARD_VERSION,
		"case_count": len(cards),
		"nbu_pass_count": nbu_pass_count,
		"current_router_pass_count": current_pass_count,
		"nbu_pass_rate": round(nbu_pass_count / max(1, len(cards)), 4),
		"current_router_pass_rate": round(current_pass_count / max(1, len(cards)), 4),
		"scorecard_outcome_counts": counts,
	}
