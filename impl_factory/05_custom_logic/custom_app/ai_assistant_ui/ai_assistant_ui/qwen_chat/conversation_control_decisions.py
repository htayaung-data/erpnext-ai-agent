from __future__ import annotations

from typing import Any, Dict

from ai_assistant_ui.qwen_chat.conversation_control_language import (
	control_action_id,
	control_action_id_from_message_or_evidence,
	control_action_is_strong_owner,
)
from ai_assistant_ui.qwen_chat.conversation_control_support import (
	clarification_response_decision_spec,
	decision_action,
	resolved_clarification_runtime_message,
	select_compound_cancellation_sequence_source,
	select_compound_completion_reentry_action,
	select_compound_completion_reentry_eligibility,
	select_compound_continuation_eligibility,
	select_prior_branch_restore_decision_spec,
)
from ai_assistant_ui.qwen_chat.recent_focus_support import (
	build_recent_focus_continuation_decision_spec,
)


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _build_conversation_control_decision_contract(**kwargs):
	from ai_assistant_ui.qwen_chat.contracts import build_conversation_control_decision_contract

	return build_conversation_control_decision_contract(**kwargs)


def conversation_control_sequence_target(payload: Dict[str, Any]) -> Dict[str, Any]:
	if not isinstance(payload, dict) or not payload:
		return {}
	internal_details = payload.get("internal_details") if isinstance(payload.get("internal_details"), dict) else {}
	return {
		"request_id": _clean_text(payload.get("request_id")),
		"status": _clean_text(payload.get("status")),
		"segments": [
			_clean_text(value)
			for value in (payload.get("segments") or [])
			if _clean_text(value)
		],
		"primary_segment_message": _clean_text(internal_details.get("primary_segment_message")),
		"remaining_segment_messages": [
			_clean_text(value)
			for value in (internal_details.get("remaining_segment_messages") or [])
			if _clean_text(value)
		],
		"execution_strategy": _clean_text(internal_details.get("execution_strategy")),
	}


def conversation_control_decision_from_clarification_response(
	*,
	raw_message: str,
	pending_clarification_signal: Dict[str, Any],
	clarification_response_contract,
):
	if clarification_response_contract is None:
		return None
	decision = _clean_text(getattr(clarification_response_contract, "decision", ""))
	if not decision:
		return None
	resolved_runtime_message = resolved_clarification_runtime_message(
		raw_message=raw_message,
		pending_clarification_signal=pending_clarification_signal,
		clarification_decision=decision,
		resolved_option=_clean_text(getattr(clarification_response_contract, "resolved_option", "")),
	)
	clarification_internal_details = (
		getattr(clarification_response_contract, "internal_details", {})
		if isinstance(getattr(clarification_response_contract, "internal_details", {}), dict)
		else {}
	)
	spec = clarification_response_decision_spec(
		decision=decision,
		raw_message=raw_message,
		resolved_runtime_message=_clean_text(resolved_runtime_message),
		override_business_message=_clean_text(clarification_internal_details.get("override_business_message")),
	)
	if not isinstance(spec, dict) or not spec:
		return None
	common = {
		"request_id": _clean_text(getattr(clarification_response_contract, "request_id", "")),
		"target_state_class": "pending_clarification",
		"confidence": float(getattr(clarification_response_contract, "confidence", 0.0) or 0.0),
		"reason": _clean_text(getattr(clarification_response_contract, "reason", "")),
		"internal_details": {
			"source_contract_type": "qwen_clarification_resolution_contract",
			"pending_reason_type": _clean_text(getattr(clarification_response_contract, "pending_reason_type", "")),
			"matched_by": _clean_text(getattr(clarification_response_contract, "matched_by", "")),
			"resolved_option": _clean_text(getattr(clarification_response_contract, "resolved_option", "")),
			"clarified_runtime_message": _clean_text(resolved_runtime_message),
			**dict(spec.get("internal_details_patch") or {}),
		},
	}
	return _build_conversation_control_decision_contract(
		decision_class=_clean_text(spec.get("decision_class")),
		decision_action=_clean_text(spec.get("decision_action")),
		resolved_business_message=_clean_text(spec.get("resolved_business_message")),
		clear_pending_clarification=bool(spec.get("clear_pending_clarification")),
		**common,
	)


def compound_request_continuation_control_with_evidence(
	message: str,
	*,
	control_evidence_payload: Dict[str, Any] | None,
) -> bool:
	return control_action_id_from_message_or_evidence(
		message,
		control_evidence_payload,
	) == "resume_active_sequence"


def compound_request_stop_control_with_evidence(
	message: str,
	*,
	control_evidence_payload: Dict[str, Any] | None,
) -> bool:
	return control_action_id_from_message_or_evidence(
		message,
		control_evidence_payload,
	) in {"stop_active_sequence", "abandon_current_branch"}


def compound_completion_reentry_answer_for_status(status: str) -> str:
	if status == "ordered_execution_complete":
		return "That sequence is already finished. You can start a new request anytime."
	if status == "ordered_execution_cancelled":
		return "That sequence was already stopped. You can start a new request anytime."
	return ""


def select_compound_completion_reentry_response(
	*,
	compound_assessment_payload: Dict[str, Any],
	raw_message: str,
	control_evidence_payload: Dict[str, Any] | None = None,
) -> Dict[str, str]:
	action_selection = select_compound_completion_reentry_action(
		sequence_status=_clean_text((compound_assessment_payload or {}).get("status")),
	)
	status = _clean_text(action_selection.get("status"))
	decision_action_value = _clean_text(action_selection.get("action"))
	completion_answer = compound_completion_reentry_answer_for_status(status)
	eligibility = select_compound_completion_reentry_eligibility(
		has_completion_answer=bool(completion_answer),
		is_continuation_control=compound_request_continuation_control_with_evidence(
			raw_message,
			control_evidence_payload=control_evidence_payload,
		),
		has_decision_action=bool(decision_action_value),
	)
	return {
		"action": _clean_text(eligibility.get("action")),
		"basis": _clean_text(eligibility.get("basis")),
		"status": status,
		"decision_action": decision_action_value,
		"completion_answer": completion_answer,
	}


def conversation_control_decision_from_compound_completion(
	*,
	request_id: str,
	raw_message: str,
	compound_assessment_payload: Dict[str, Any],
	completion_answer: str,
	control_evidence_payload: Dict[str, Any] | None = None,
):
	selection = select_compound_completion_reentry_response(
		compound_assessment_payload=compound_assessment_payload,
		raw_message=raw_message,
		control_evidence_payload=control_evidence_payload,
	)
	if _clean_text(selection.get("action")) != "allow":
		return None
	status = _clean_text(selection.get("status"))
	decision_action_value = _clean_text(selection.get("decision_action"))
	resolved_completion_answer = _clean_text(selection.get("completion_answer")) or _clean_text(completion_answer)
	return _build_conversation_control_decision_contract(
		request_id=request_id,
		decision_class="sequence_completion_reentry",
		decision_action=decision_action_value,
		target_state_class="active_sequence",
		resolved_business_message=resolved_completion_answer,
		resolved_sequence_target=conversation_control_sequence_target(compound_assessment_payload),
		clear_active_sequence=True,
		confidence=1.0,
		reason="The user tried to continue an ordered multi-step sequence that had already finished.",
		internal_details={
			"source_contract_type": "qwen_compound_request_assessment_contract",
			"prior_sequence_status": status,
			"user_message": _clean_text(raw_message),
		},
	)


def conversation_control_decision_from_compound_continuation(
	*,
	request_id: str,
	raw_message: str,
	active_sequence_payload: Dict[str, Any],
	runtime_message: str,
	control_evidence_payload: Dict[str, Any] | None = None,
	has_active_sequence: bool,
):
	selection = select_compound_continuation_eligibility(
		has_runtime_message=bool(_clean_text(runtime_message)),
		is_continuation_control=compound_request_continuation_control_with_evidence(
			raw_message,
			control_evidence_payload=control_evidence_payload,
		),
		has_active_sequence=bool(has_active_sequence),
	)
	if _clean_text(selection.get("action")) != "allow":
		return None
	return _build_conversation_control_decision_contract(
		request_id=request_id,
		decision_class="sequence_continuation",
		decision_action="resume_active_sequence",
		target_state_class="active_sequence",
		resolved_business_message=_clean_text(runtime_message),
		resolved_sequence_target=conversation_control_sequence_target(active_sequence_payload),
		confidence=0.95,
		reason="The user chose to continue the active ordered multi-step sequence.",
		internal_details={
			"source_contract_type": "qwen_compound_request_assessment_contract",
			"prior_sequence_status": _clean_text((active_sequence_payload or {}).get("status")),
			"user_message": _clean_text(raw_message),
		},
	)


def conversation_control_decision_from_compound_cancellation(
	*,
	request_id: str,
	raw_message: str,
	active_sequence_payload: Dict[str, Any],
	cancelled_sequence_payload: Dict[str, Any],
	control_evidence_payload: Dict[str, Any] | None = None,
	has_active_sequence: bool,
):
	if not compound_request_stop_control_with_evidence(
		raw_message,
		control_evidence_payload=control_evidence_payload,
	):
		return None
	if not has_active_sequence:
		return None
	selection = select_compound_cancellation_sequence_source(
		has_cancelled_sequence_payload=bool(isinstance(cancelled_sequence_payload, dict) and cancelled_sequence_payload),
		has_active_sequence_payload=bool(isinstance(active_sequence_payload, dict) and active_sequence_payload),
	)
	sequence_payload = (
		cancelled_sequence_payload
		if _clean_text(selection.get("owner")) == "cancelled_sequence_payload"
		else active_sequence_payload
	)
	return _build_conversation_control_decision_contract(
		request_id=request_id,
		decision_class="sequence_cancellation",
		decision_action="cancel_active_sequence",
		target_state_class="active_sequence",
		resolved_business_message="Okay, I'll stop here.",
		resolved_sequence_target=conversation_control_sequence_target(sequence_payload),
		clear_active_sequence=True,
		confidence=1.0,
		reason="The user explicitly stopped the remaining ordered multi-step sequence.",
		internal_details={
			"source_contract_type": "qwen_compound_request_assessment_contract",
			"prior_sequence_status": _clean_text((active_sequence_payload or {}).get("status")),
			"user_message": _clean_text(raw_message),
		},
	)


def conversation_control_decision_from_recent_focus_runtime_message(
	*,
	request_id: str,
	runtime_message: str,
	recent_focus_state: Dict[str, Any],
	followup_resolution,
	recent_focus_affordance_payload: Dict[str, Any],
	control_evidence_payload: Dict[str, Any] | None = None,
	selection: Dict[str, Any],
	raw_message: str,
	routing_basis: str = "",
):
	if _clean_text((selection or {}).get("action")) != "allow":
		return None
	decision_spec = build_recent_focus_continuation_decision_spec(
		recent_focus_state=recent_focus_state,
		selection=selection,
		followup_resolution=followup_resolution,
		recent_focus_affordance_payload=recent_focus_affordance_payload,
		control_action_id=control_action_id(control_evidence_payload),
		raw_message=raw_message,
		routing_basis=routing_basis,
	)
	return _build_conversation_control_decision_contract(
		request_id=request_id,
		decision_class="recent_focus_continuation",
		decision_action="resolve_recent_focus_followup",
		target_state_class="recent_focus",
		resolved_business_message=_clean_text(runtime_message),
		resolved_focus_target=decision_spec.get("resolved_focus_target"),
		update_recent_focus=True,
		confidence=float(decision_spec.get("confidence") or 0.0),
		reason=_clean_text(decision_spec.get("reason")),
		internal_details=dict(decision_spec.get("internal_details") or {}),
	)


def conversation_control_decision_from_prior_branch_restore_contract(
	*,
	prior_branch_restore_contract,
	projection: Dict[str, Any],
):
	if prior_branch_restore_contract is None:
		return None
	restore_mode = _clean_text(getattr(prior_branch_restore_contract, "restore_mode", ""))
	if not restore_mode:
		return None
	spec = select_prior_branch_restore_decision_spec(
		request_id=_clean_text(getattr(prior_branch_restore_contract, "request_id", "")),
		restore_mode=restore_mode,
		target_branch_kind=_clean_text(getattr(prior_branch_restore_contract, "target_branch_kind", "")),
		target_branch_label=_clean_text(getattr(prior_branch_restore_contract, "target_branch_label", "")),
		target_request_id=_clean_text(getattr(prior_branch_restore_contract, "target_request_id", "")),
		target_family=_clean_text(getattr(prior_branch_restore_contract, "target_family", "")),
		projection_resolved_focus_target=(
			dict(projection.get("resolved_focus_target") or {})
			if isinstance(projection.get("resolved_focus_target"), dict)
			else {}
		),
		projection_internal_details=(
			dict(projection.get("internal_details") or {})
			if isinstance(projection.get("internal_details"), dict)
			else {}
		),
		clear_pending_clarification=bool(
			getattr(prior_branch_restore_contract, "clear_current_pending_clarification", False)
		),
		clear_active_sequence=bool(
			getattr(prior_branch_restore_contract, "clear_current_active_sequence", False)
		),
		resumable=bool(getattr(prior_branch_restore_contract, "resumable", False)),
		confidence=float(getattr(prior_branch_restore_contract, "confidence", 0.0) or 0.0),
		reason=_clean_text(getattr(prior_branch_restore_contract, "reason", "")),
	)
	if not spec:
		return None
	return _build_conversation_control_decision_contract(**spec)


def conversation_control_focus_target_from_recovery_contract(recovery_contract: Dict[str, Any]) -> Dict[str, Any]:
	if not isinstance(recovery_contract, dict) or not recovery_contract:
		return {}
	return {
		"focus_kind": "recovery_origin",
		"focus_grain": _clean_text(recovery_contract.get("source_family_id")),
		"focus_label": _clean_text(recovery_contract.get("source_report")),
		"focus_key": _clean_text(recovery_contract.get("source_request_id")),
		"source_request_id": _clean_text(recovery_contract.get("source_request_id")),
		"source_family": _clean_text(recovery_contract.get("source_family_id")),
		"source_capability": _clean_text(recovery_contract.get("source_capability_id")),
		"source_report": _clean_text(recovery_contract.get("source_report")),
		"deictic_allowed": False,
		"explicit_named_allowed": True,
	}


def conversation_control_decision_from_repair_contract(
	*,
	request_id: str,
	repair_contract_payload: Dict[str, Any],
	latest_recovery_contract: Dict[str, Any],
):
	if not isinstance(repair_contract_payload, dict) or not repair_contract_payload:
		return None
	if _clean_text(repair_contract_payload.get("repair_state")) != "accepted":
		return None
	repair_intent_type = _clean_text(repair_contract_payload.get("repair_intent_type"))
	accepted_recovery_action = _clean_text(repair_contract_payload.get("accepted_recovery_action"))
	common = {
		"request_id": request_id,
		"target_state_class": "repair_guidance",
		"resolved_focus_target": conversation_control_focus_target_from_recovery_contract(latest_recovery_contract),
		"preserve_prior_branch": bool(repair_contract_payload.get("targets_prior_recovery")),
		"confidence": float(repair_contract_payload.get("confidence") or 0.0),
		"reason": _clean_text(repair_contract_payload.get("reason")),
		"internal_details": {
			"source_contract_type": "qwen_conversational_repair_intent_contract",
			"repair_intent_type": repair_intent_type,
			"repair_state": _clean_text(repair_contract_payload.get("repair_state")),
			"accepted_recovery_action": accepted_recovery_action,
			"allowed_next_lane": _clean_text(repair_contract_payload.get("allowed_next_lane")),
			"targets_prior_recovery": bool(repair_contract_payload.get("targets_prior_recovery")),
		},
	}
	if repair_intent_type == "guidance_request":
		return _build_conversation_control_decision_contract(
			decision_class="repair_guidance",
			decision_action="answer_recovery_guidance",
			**common,
		)
	if repair_intent_type == "accept_recovery_action":
		return _build_conversation_control_decision_contract(
			decision_class="repair_acceptance",
			decision_action=accepted_recovery_action or "accept_recovery_action",
			update_recent_focus=bool(accepted_recovery_action == "run_alternative_governed_query"),
			**common,
		)
	return None
