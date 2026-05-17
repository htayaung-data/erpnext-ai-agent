from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .natural_business_understanding_contracts import (
	NBUEvidencePlanContract,
	NBUAuthorityPlanContract,
	NBUConversationActionDecisionContract,
)
from .natural_business_understanding_validation import POLICY_GATED_AUTHORITY_CLASSES


MIN_CONFIDENCE_FOR_CURRENT_ARTIFACT_ANSWER = 0.65
MIN_CONFIDENCE_FOR_GOVERNED_REQUERY = 0.55


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _confidence_value(system_confidence_payload: Dict[str, Any]) -> float:
	try:
		return max(0.0, min(1.0, float(_clean_dict(system_confidence_payload).get("final_confidence") or 0.0)))
	except Exception:
		return 0.0


def _has_registry_anchor(candidate_payload: Dict[str, Any]) -> bool:
	return bool(
		_clean_list(candidate_payload.get("candidate_capability_ids"))
		or _clean_list(candidate_payload.get("candidate_report_names"))
		or _clean_list(candidate_payload.get("candidate_composite_family_ids"))
	)


def _required_artifacts(candidate_payload: Dict[str, Any]) -> List[str]:
	values: List[str] = []
	values.extend(_clean_list(candidate_payload.get("candidate_composite_family_ids")))
	values.extend(_clean_list(candidate_payload.get("candidate_report_names")))
	values.extend(_clean_list(candidate_payload.get("candidate_capability_ids")))
	return list(dict.fromkeys(values))


def _missing_fields(validation_payload: Dict[str, Any]) -> List[str]:
	missing: List[str] = []
	for warning in _clean_list(_clean_dict(validation_payload).get("validation_warnings")):
		if ":" not in warning:
			continue
		key, value = warning.split(":", 1)
		if key in {
			"current_artifact_missing_requested_field",
			"report_missing_metric",
			"report_missing_dimension",
			"composite_family_missing_metric",
			"composite_family_missing_dimension",
			"governed_kpi_missing_metric",
			"governed_kpi_missing_dimension",
		}:
			missing.append(value)
	return list(dict.fromkeys(missing))


def _has_context_conflict(validation_payload: Dict[str, Any]) -> bool:
	return any(
		warning.startswith("context_artifact_family_conflict:")
		for warning in _clean_list(_clean_dict(validation_payload).get("validation_warnings"))
	)


def _build_evidence_plan(
	*,
	candidate_payload: Dict[str, Any],
	validation_payload: Dict[str, Any],
	final_confidence: float,
) -> NBUEvidencePlanContract:
	evidence_need = _clean_text(candidate_payload.get("evidence_need")) or "unknown"
	return NBUEvidencePlanContract(
		evidence_need=evidence_need,
		current_artifact_supported=(
			evidence_need == "current_artifact_ok"
			and final_confidence >= MIN_CONFIDENCE_FOR_CURRENT_ARTIFACT_ANSWER
			and not _has_context_conflict(validation_payload)
		),
		governed_requery_available=(
			evidence_need == "needs_governed_requery"
			and _has_registry_anchor(candidate_payload)
			and final_confidence >= MIN_CONFIDENCE_FOR_GOVERNED_REQUERY
		),
		required_artifacts=_required_artifacts(candidate_payload),
		missing_fields=_missing_fields(validation_payload),
		reason="Evidence plan derived from NBU validation and candidate registry anchors.",
	)


def _build_authority_plan(candidate_payload: Dict[str, Any], validation_payload: Dict[str, Any]) -> NBUAuthorityPlanContract:
	authority_class = _clean_text(candidate_payload.get("authority_class")) or "unknown"
	policy_required = authority_class in POLICY_GATED_AUTHORITY_CLASSES
	return NBUAuthorityPlanContract(
		authority_class=authority_class,
		authority_allowed=not policy_required and _clean_text(validation_payload.get("authority_policy_state")) == "safe_read_authority",
		policy_artifact_required=(
			"approved_policy_artifact_required"
			if policy_required
			else ""
		),
		approval_state=_clean_text(validation_payload.get("authority_policy_state")) or "unknown",
		boundary_reason=(
			f"{authority_class} requires an approved governed policy artifact before execution."
			if policy_required
			else ""
		),
	)


def build_nbu_conversation_action_decision(
	*,
	candidate_payload: Dict[str, Any],
	validation_payload: Dict[str, Any],
	system_confidence_payload: Dict[str, Any],
) -> Tuple[NBUConversationActionDecisionContract, NBUEvidencePlanContract, NBUAuthorityPlanContract]:
	candidate = _clean_dict(candidate_payload)
	validation = _clean_dict(validation_payload)
	final_confidence = _confidence_value(system_confidence_payload)
	evidence_need = _clean_text(candidate.get("evidence_need")).lower()
	intent_scope = _clean_text(candidate.get("intent_scope")).lower()
	requested_action = _clean_text(candidate.get("requested_action")).lower()
	authority_class = _clean_text(candidate.get("authority_class")).lower()
	validation_status = _clean_text(validation.get("status")).lower()
	selected_candidate_id = _clean_text(candidate.get("candidate_id"))

	evidence_plan = _build_evidence_plan(
		candidate_payload=candidate,
		validation_payload=validation,
		final_confidence=final_confidence,
	)
	authority_plan = _build_authority_plan(candidate, validation)

	if intent_scope == "out_of_scope" or evidence_need == "out_of_scope":
		return (
			NBUConversationActionDecisionContract(
				action="out_of_scope_response",
				response_mode="out_of_scope",
				selected_candidate_id=selected_candidate_id,
				reason="The interpreted request is outside governed ERP scope.",
			),
			evidence_plan,
			authority_plan,
		)

	if validation_status == "blocked_by_authority_policy" or authority_class in POLICY_GATED_AUTHORITY_CLASSES:
		return (
			NBUConversationActionDecisionContract(
				action="reject_with_boundary",
				response_mode="boundary",
				selected_candidate_id=selected_candidate_id,
				reason="The request needs recommendation, prediction, approval, or policy authority that is not approved for execution.",
				technical_details={"authority_class": authority_class, "validation_status": validation_status},
			),
			evidence_plan,
			authority_plan,
		)

	if _has_context_conflict(validation) or evidence_need == "needs_clarification" or validation_status == "insufficient_confidence":
		return (
			NBUConversationActionDecisionContract(
				action="ask_clarification",
				response_mode="clarification",
				selected_candidate_id=selected_candidate_id,
				reason="The request is governable, but the current context or evidence is not clear enough to answer safely.",
				suggested_options=_required_artifacts(candidate)[:5],
				technical_details={"validation_status": validation_status, "final_confidence": final_confidence},
			),
			evidence_plan,
			authority_plan,
		)

	if evidence_plan.current_artifact_supported:
		return (
			NBUConversationActionDecisionContract(
				action="answer_from_current_artifact",
				response_mode="direct_answer",
				selected_candidate_id=selected_candidate_id,
				requires_routing_change=False,
				safe_to_execute=True,
				reason="The current governed artifact contains enough compatible evidence for the requested follow-up.",
			),
			evidence_plan,
			authority_plan,
		)

	if evidence_plan.governed_requery_available:
		action = "execute_fresh_governed_query" if intent_scope == "fresh_query" else "execute_governed_requery"
		return (
			NBUConversationActionDecisionContract(
				action=action,
				response_mode="governed_query",
				selected_candidate_id=selected_candidate_id,
				requires_routing_change=True,
				safe_to_execute=True,
				reason="The current artifact is insufficient, but a compatible governed query/requery path is available.",
			),
			evidence_plan,
			authority_plan,
		)

	if intent_scope == "capability_question":
		return (
			NBUConversationActionDecisionContract(
				action="answer_capability_question",
				response_mode="capability_guidance",
				selected_candidate_id=selected_candidate_id,
				safe_to_execute=True,
				reason="The user is asking what the assistant can do.",
			),
			evidence_plan,
			authority_plan,
		)

	if requested_action == "clarify" or candidate.get("target_reference") == "candidate_list":
		return (
			NBUConversationActionDecisionContract(
				action="show_supported_options",
				response_mode="supported_options",
				selected_candidate_id=selected_candidate_id,
				suggested_options=_required_artifacts(candidate)[:5],
				reason="The safest response is to show supported options before proceeding.",
			),
			evidence_plan,
			authority_plan,
		)

	return (
		NBUConversationActionDecisionContract(
			action="ask_clarification",
			response_mode="clarification",
			selected_candidate_id=selected_candidate_id,
			reason="The request is governable, but no safe answer, requery, or boundary action was proven.",
			suggested_options=_required_artifacts(candidate)[:5],
			technical_details={"validation_status": validation_status, "final_confidence": final_confidence},
		),
		evidence_plan,
		authority_plan,
	)
