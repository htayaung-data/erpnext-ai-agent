from __future__ import annotations

from typing import Any, Dict, List

from .natural_business_understanding_activation import (
	DELEGATED_ACTIONS,
	EXECUTION_REQUIRED_ACTIONS,
	PRESENTATION_ONLY_ACTIONS,
)


NBU_ARBITRATION_VERSION = "1.0"

NBU_ARBITRATION_DECISIONS: List[Dict[str, str]] = [
	{
		"decision": "trust_current_router",
		"meaning": "Keep the existing governed route because it is correct, safer, or sufficient.",
	},
	{
		"decision": "trust_nbu",
		"meaning": "Allow NBU to own the next route only when the matching activation level is enabled.",
	},
	{
		"decision": "ask_clarification",
		"meaning": "Ask one useful business clarification instead of guessing.",
	},
	{
		"decision": "safe_boundary",
		"meaning": "Stop unsupported prediction, recommendation, approval, or unsafe behavior with a business-safe boundary.",
	},
	{
		"decision": "shadow_only",
		"meaning": "Record the NBU finding but do not change live behavior yet.",
	},
]

NBU_ARBITRATION_ACTIVATION_LEVELS: List[Dict[str, Any]] = [
	{
		"activation_level": "shadow_only",
		"allowed_action_lanes": [],
		"meaning": "Audit only; no NBU route ownership.",
	},
	{
		"activation_level": "presentation_only",
		"allowed_action_lanes": ["presentation"],
		"meaning": "NBU may own safe clarification, option, boundary, capability, or out-of-scope responses.",
	},
	{
		"activation_level": "current_artifact_answer",
		"allowed_action_lanes": ["presentation", "current_artifact"],
		"meaning": "NBU may also own validated answers from visible current artifacts.",
	},
	{
		"activation_level": "governed_requery",
		"allowed_action_lanes": ["presentation", "current_artifact", "governed_requery"],
		"meaning": "NBU may also plan approved follow-up requery routes.",
	},
	{
		"activation_level": "fresh_query",
		"allowed_action_lanes": ["presentation", "current_artifact", "governed_requery", "fresh_query"],
		"meaning": "NBU may also route fresh self-contained governed queries.",
	},
	{
		"activation_level": "full_front_controller",
		"allowed_action_lanes": ["presentation", "current_artifact", "governed_requery", "fresh_query", "context_control"],
		"meaning": "NBU may own all approved front-controller lanes after release gating.",
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


def _dedupe(values: List[str]) -> List[str]:
	return list(dict.fromkeys([_clean_text(value) for value in values if _clean_text(value)]))


def _decision_ids() -> List[str]:
	return [_clean_text(row.get("decision")) for row in NBU_ARBITRATION_DECISIONS]


def _activation_levels() -> List[str]:
	return [_clean_text(row.get("activation_level")) for row in NBU_ARBITRATION_ACTIVATION_LEVELS]


def list_nbu_arbitration_decisions() -> List[Dict[str, str]]:
	return [dict(row) for row in NBU_ARBITRATION_DECISIONS]


def list_nbu_arbitration_activation_levels() -> List[Dict[str, Any]]:
	return [
		{
			"activation_level": _clean_text(row.get("activation_level")),
			"allowed_action_lanes": _clean_list(row.get("allowed_action_lanes")),
			"meaning": _clean_text(row.get("meaning")),
		}
		for row in NBU_ARBITRATION_ACTIVATION_LEVELS
	]


def validate_nbu_arbitration_contract() -> Dict[str, Any]:
	required_decisions = {
		"trust_current_router",
		"trust_nbu",
		"ask_clarification",
		"safe_boundary",
		"shadow_only",
	}
	required_levels = {
		"shadow_only",
		"presentation_only",
		"current_artifact_answer",
		"governed_requery",
		"fresh_query",
		"full_front_controller",
	}
	errors: List[str] = []
	decisions = _decision_ids()
	levels = _activation_levels()
	for decision in sorted(required_decisions.difference(decisions)):
		errors.append(f"missing_arbitration_decision:{decision}")
	for decision in decisions:
		if decisions.count(decision) > 1:
			errors.append(f"duplicate_arbitration_decision:{decision}")
	for level in sorted(required_levels.difference(levels)):
		errors.append(f"missing_activation_level:{level}")
	for level in levels:
		if levels.count(level) > 1:
			errors.append(f"duplicate_activation_level:{level}")
	for row in NBU_ARBITRATION_DECISIONS:
		if not _clean_text(row.get("meaning")):
			errors.append(f"{_clean_text(row.get('decision'))}:missing_meaning")
	for row in NBU_ARBITRATION_ACTIVATION_LEVELS:
		if not _clean_text(row.get("meaning")):
			errors.append(f"{_clean_text(row.get('activation_level'))}:missing_meaning")
	return {
		"ok": not errors,
		"schema_version": NBU_ARBITRATION_VERSION,
		"decision_count": len(NBU_ARBITRATION_DECISIONS),
		"activation_level_count": len(NBU_ARBITRATION_ACTIVATION_LEVELS),
		"errors": _dedupe(errors),
	}


def _action_lane(action: str) -> str:
	action = _clean_text(action)
	if action in PRESENTATION_ONLY_ACTIONS:
		return "presentation"
	if action in DELEGATED_ACTIONS:
		return "current_artifact"
	if action == "execute_governed_requery":
		return "governed_requery"
	if action == "execute_fresh_governed_query":
		return "fresh_query"
	if action in EXECUTION_REQUIRED_ACTIONS:
		return "context_control"
	return "unknown"


def nbu_action_lane_for_action(action: str) -> str:
	return _action_lane(action)


def _allowed_lanes_for_activation_level(activation_level: str) -> List[str]:
	level = _clean_text(activation_level) or "shadow_only"
	for row in NBU_ARBITRATION_ACTIVATION_LEVELS:
		if _clean_text(row.get("activation_level")) == level:
			return _clean_list(row.get("allowed_action_lanes"))
	return []


def nbu_activation_level_supports_action(*, action: str, activation_level: str) -> Dict[str, Any]:
	lane = _action_lane(action)
	allowed_lanes = _allowed_lanes_for_activation_level(activation_level)
	return {
		"action": _clean_text(action),
		"required_action_lane": lane,
		"activation_level": _clean_text(activation_level) or "shadow_only",
		"allowed_action_lanes": allowed_lanes,
		"supported": bool(lane and lane != "unknown" and lane in allowed_lanes),
	}


def _scorecard_outcome(scorecard_payload: Dict[str, Any]) -> str:
	return _clean_text(_clean_dict(scorecard_payload).get("scorecard_outcome"))


def _nbu_action(scorecard_payload: Dict[str, Any]) -> str:
	return _clean_text(_clean_dict(scorecard_payload).get("nbu_actual_action"))


def _current_passed(scorecard_payload: Dict[str, Any]) -> bool:
	return bool(_clean_dict(scorecard_payload).get("current_router_passed"))


def _nbu_passed(scorecard_payload: Dict[str, Any]) -> bool:
	return bool(_clean_dict(scorecard_payload).get("nbu_passed"))


def _policy_or_evidence_gap(scorecard_payload: Dict[str, Any]) -> bool:
	scorecard = _clean_dict(scorecard_payload)
	buckets = (
		_clean_list(scorecard.get("nbu_failure_buckets"))
		+ _clean_list(scorecard.get("current_router_failure_buckets"))
		+ _clean_list(scorecard.get("nbu_diagnostic_buckets"))
		+ _clean_list(scorecard.get("current_router_diagnostic_buckets"))
	)
	return "policy_evidence_gap" in buckets


def _nbu_activation_supported(scorecard_payload: Dict[str, Any], activation_level: str) -> Dict[str, Any]:
	action = _nbu_action(scorecard_payload)
	support = nbu_activation_level_supports_action(action=action, activation_level=activation_level)
	support["nbu_action"] = action
	return support


def build_nbu_arbitration_decision(
	*,
	scorecard_payload: Dict[str, Any],
	activation_level: str = "shadow_only",
) -> Dict[str, Any]:
	scorecard = _clean_dict(scorecard_payload)
	outcome = _scorecard_outcome(scorecard)
	support = _nbu_activation_supported(scorecard, activation_level)
	blockers: List[str] = []
	warnings: List[str] = []
	reason = ""
	decision = "shadow_only"
	selected_route_owner = "none"
	live_behavior_change_authorized = False

	if outcome == "both_correct":
		decision = "trust_current_router"
		selected_route_owner = "current_router"
		reason = "NBU and the current router agree, so keeping the current governed route is sufficient."
	elif outcome == "current_correct_nbu_wrong":
		decision = "trust_current_router"
		selected_route_owner = "current_router"
		blockers.append("nbu_did_not_match_oracle")
		reason = "The current router matches the labelled expectation and NBU does not."
	elif outcome == "nbu_unsafe":
		blockers.append("nbu_failed_safety_gate")
		if _current_passed(scorecard):
			decision = "trust_current_router"
			selected_route_owner = "current_router"
			reason = "NBU failed a safety gate, so the current safe route remains in control."
		else:
			decision = "safe_boundary"
			selected_route_owner = "safe_boundary"
			reason = "NBU is unsafe and the current route is not proven correct, so fail safely."
	elif outcome == "nbu_low_confidence":
		blockers.append("nbu_below_confidence_threshold")
		if _current_passed(scorecard):
			decision = "trust_current_router"
			selected_route_owner = "current_router"
			reason = "NBU confidence is too low and the current route is correct."
		else:
			decision = "ask_clarification"
			selected_route_owner = "clarification"
			reason = "NBU confidence is too low and no correct route is proven."
	elif outcome == "both_wrong":
		decision = "safe_boundary" if _policy_or_evidence_gap(scorecard) else "ask_clarification"
		selected_route_owner = "safe_boundary" if decision == "safe_boundary" else "clarification"
		blockers.append("no_proven_correct_route")
		reason = "Neither NBU nor the current router matches the labelled expectation."
	elif outcome == "nbu_correct_current_wrong":
		if support["supported"]:
			decision = "trust_nbu"
			selected_route_owner = "nbu"
			live_behavior_change_authorized = True
			reason = "NBU matches the labelled expectation and the current router does not; the activation level allows this NBU lane."
		else:
			decision = "shadow_only"
			selected_route_owner = "current_router"
			blockers.append("nbu_lane_not_enabled_for_activation_level")
			warnings.append("nbu_would_win_if_lane_enabled")
			reason = "NBU matches the labelled expectation, but this action lane is not enabled yet."
	else:
		decision = "ask_clarification"
		selected_route_owner = "clarification"
		blockers.append("unknown_scorecard_outcome")
		reason = "The scorecard outcome is unknown, so do not guess."

	return {
		"type": "qwen_nbu_arbitration_decision",
		"schema_version": NBU_ARBITRATION_VERSION,
		"case_id": _clean_text(scorecard.get("case_id")),
		"scorecard_outcome": outcome,
		"decision": decision,
		"selected_route_owner": selected_route_owner,
		"activation_level": support["activation_level"],
		"required_action_lane": support["required_action_lane"],
		"allowed_action_lanes": support["allowed_action_lanes"],
		"live_behavior_change_authorized": live_behavior_change_authorized,
		"live_behavior_changed_by_fc2": False,
		"nbu_passed": _nbu_passed(scorecard),
		"current_router_passed": _current_passed(scorecard),
		"blockers": _dedupe(blockers),
		"warnings": _dedupe(warnings),
		"reason": reason,
	}


def summarize_nbu_arbitration_decisions(arbitration_decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
	decisions = [_clean_dict(decision) for decision in arbitration_decisions if isinstance(decision, dict)]
	decision_counts = {decision_id: 0 for decision_id in _decision_ids()}
	owner_counts: Dict[str, int] = {}
	for decision in decisions:
		decision_id = _clean_text(decision.get("decision"))
		if decision_id in decision_counts:
			decision_counts[decision_id] += 1
		owner = _clean_text(decision.get("selected_route_owner")) or "none"
		owner_counts[owner] = owner_counts.get(owner, 0) + 1
	return {
		"type": "qwen_nbu_arbitration_summary",
		"schema_version": NBU_ARBITRATION_VERSION,
		"case_count": len(decisions),
		"decision_counts": decision_counts,
		"selected_route_owner_counts": owner_counts,
		"authorized_behavior_change_count": sum(
			1 for decision in decisions if bool(decision.get("live_behavior_change_authorized"))
		),
		"actual_behavior_change_count": sum(
			1 for decision in decisions if bool(decision.get("live_behavior_changed_by_fc2"))
		),
	}
