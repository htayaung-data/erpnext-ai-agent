from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

from ai_assistant_ui.qwen_chat.clarification_resolution import (
	clarification_state_after_unresolved_attempt,
	clear_pending_clarification_signal,
	governed_fallback_option,
	pending_clarification_empty_ack_answer,
	pending_clarification_fallback_stop_answer,
	pending_clarification_meta_answer,
	pending_clarification_options_answer,
	pending_clarification_repeat_answer,
	resolve_pending_clarification_response,
	store_pending_clarification_signal,
)
from ai_assistant_ui.qwen_chat.contracts import ExecutionPath
from ai_assistant_ui.qwen_chat.authorized_emission import (
	ANSWER_TYPE_CONTROL,
	emit_authorized_assistant_answer,
)
from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import (
	SemanticFrontDoorIntent,
	SemanticFrontDoorResult,
	build_front_door_intent_gate_contract_from_semantic_result,
)
from ai_assistant_ui.qwen_chat.knowledge_boundary import evaluate_knowledge_boundary
from ai_assistant_ui.qwen_chat.observability import record_phase55_observability_event
from ai_assistant_ui.qwen_chat.runtime_metadata_contract import (
	LANE_CLASS_CONTROL_META,
	ROLE_CONTROL_META,
	build_runtime_metadata_envelope,
)


def build_pending_clarification_frontdoor_skip(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	pending_clarification_signal: Dict[str, Any],
	clarification_state,
	latest_grounded_turn_available: bool,
	latest_grounded_turn: Dict[str, Any],
	conversation_control_evidence_payload: Dict[str, Any] | None = None,
) -> Tuple[Any, SemanticFrontDoorResult, Any]:
	clarification_response_contract = resolve_pending_clarification_response(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		signal_payload=pending_clarification_signal,
		clarification_attempt_count=int(max(0, clarification_state.attempt_count)),
		max_attempts=int(max(1, clarification_state.max_attempts)),
		grounded_turn=latest_grounded_turn,
		control_evidence_payload=conversation_control_evidence_payload,
	)
	frontdoor_semantic_result = SemanticFrontDoorResult(
		status="skipped_for_pending_clarification",
		intent=SemanticFrontDoorIntent(
			intent_class="route_onward",
			confidence=1.0,
			reason="A pending clarification is resolved before front-door classification runs.",
		),
		confidence_threshold=1.0,
	)
	frontdoor_contract = build_front_door_intent_gate_contract_from_semantic_result(
		request_id=request_id,
		semantic_result=frontdoor_semantic_result,
		grounded_context_available=latest_grounded_turn_available,
	)
	return clarification_response_contract, frontdoor_semantic_result, frontdoor_contract


def _clarification_control_authority(*, answer_mode: str, reason: str) -> Dict[str, Any]:
	return {
		"authority_source": "control_meta",
		"answer_mode": answer_mode,
		"reason": reason,
		"preflight_status": "passed",
	}


def _clarification_runtime_metadata_envelope(*, answer_mode: str) -> Dict[str, Any]:
	return build_runtime_metadata_envelope(
		lane_id="clarification_control",
		lane_class=LANE_CLASS_CONTROL_META,
		model_role=ROLE_CONTROL_META,
		model_name="none",
		fallback_used=False,
		fallback_reason="",
		role_compliance="compliant",
		authority_source="control_meta",
		evidence_scope="clarification_control_contract",
		answer_mode=answer_mode,
		preflight_status="passed",
		metadata_source="clarification_control_authority",
	)


def _clarification_boundary_payload(
	*,
	request_id: str,
	session_id: str,
	clarification_response_contract,
	frontdoor_contract,
	latest_grounded_turn_available: bool,
	latest_grounded_turn: Dict[str, Any],
) -> Dict[str, Any]:
	return evaluate_knowledge_boundary(
		request_id=request_id,
		session_id=session_id,
		proposed_lane="clarification",
		clarification_resolution=clarification_response_contract.to_payload(),
		front_door_contract=frontdoor_contract.to_payload(),
		grounded_turn=latest_grounded_turn if latest_grounded_turn_available else {},
	)


def handle_pending_clarification_turn(
	*,
	session_doc,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	raw_message: str,
	pending_clarification_signal: Dict[str, Any],
	clarification_state,
	clarification_response_contract,
	interaction_contract,
	frontdoor_semantic_result,
	frontdoor_contract,
	latest_grounded_turn_available: bool,
	latest_grounded_turn: Dict[str, Any],
	conversation_control_evidence_contract=None,
	append_message: Callable[..., None],
	append_tool_payload: Callable[..., None],
	append_knowledge_boundary_contract: Callable[..., Dict[str, Any]],
	assistant_text_payload: Callable[[str], str],
	save_session: Callable[..., None],
) -> Tuple[bool, Any, str, Dict[str, Any] | None]:
	clarification_decision = str(clarification_response_contract.decision or "").strip()
	if clarification_decision == "show_options":
		answer_text = pending_clarification_options_answer(pending_clarification_signal)
		execution_path = ExecutionPath(
			request_id=request_id,
			path="clarification",
			reason=str(clarification_response_contract.reason or "").strip()
			or "The user asked to review the clarification options before continuing.",
			requires_runtime=False,
			grounded_required=False,
		)
		append_message(session_doc, "user", raw_message)
		observability_payload = record_phase55_observability_event(
			request_id=request_id,
			session_id=session_id,
			event_family="clarification",
			event_name="show_options",
			details={
				"pending_reason_type": str(pending_clarification_signal.get("reason_type") or "").strip(),
				"attempt_count": int(max(0, clarification_state.attempt_count)),
				"max_attempts": int(max(1, clarification_state.max_attempts)),
			},
		)
		boundary_payload = _clarification_boundary_payload(
			request_id=request_id,
			session_id=session_id,
			clarification_response_contract=clarification_response_contract,
			frontdoor_contract=frontdoor_contract,
			latest_grounded_turn_available=latest_grounded_turn_available,
			latest_grounded_turn=latest_grounded_turn,
		)
		answer_mode = "clarification_show_options"
		runtime_metadata_envelope = _clarification_runtime_metadata_envelope(answer_mode=answer_mode)
		authorized_emission = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text=answer_text,
			answer_type=ANSWER_TYPE_CONTROL,
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			assistant_text_payload=assistant_text_payload,
			control_meta_authority=_clarification_control_authority(
				answer_mode=answer_mode,
				reason=str(clarification_response_contract.reason or "").strip()
				or "The user asked to review the clarification options before continuing.",
			),
			runtime_trace_payload={
				"runtime_metadata_envelope": runtime_metadata_envelope,
				"agent_meta": {
					"engine": "pending_clarification_resolver",
					"mode": "show_options",
					"runtime_metadata_envelope": runtime_metadata_envelope,
				},
			},
			pre_assistant_tool_payloads=[
				interaction_contract.to_payload(),
				frontdoor_semantic_result.to_payload(),
				frontdoor_contract.to_payload(),
				clarification_response_contract.to_payload(),
				observability_payload,
				boundary_payload,
				runtime_metadata_envelope,
				execution_path.to_payload(),
				pending_clarification_signal,
			],
		)
		if authorized_emission.emitted:
			store_pending_clarification_signal(
				session_doc,
				pending_clarification_signal,
				attempt_count=int(max(0, clarification_state.attempt_count)),
				max_attempts=int(max(1, clarification_state.max_attempts)),
			)
		save_session(session_doc, ignore_permissions=False)
		return True, clarification_response_contract, raw_message, {
			"ok": bool(authorized_emission.emitted),
			"request_id": request_id,
			"mode": "clarification",
			"agent_meta": {
				"engine": "pending_clarification_resolver",
				"mode": "show_options",
				"runtime_metadata_envelope": runtime_metadata_envelope,
				"authorized_emission": authorized_emission.to_payload(),
			},
		}
	if clarification_decision in {"reask_pending_clarification", "meta_question", "empty_ack"}:
		clarification_state = clarification_state_after_unresolved_attempt(
			clarification_state,
			pending_clarification_signal,
		)
		fallback_option = governed_fallback_option(pending_clarification_signal) if clarification_state.max_attempts_reached else ""
		if fallback_option:
			clarification_response_contract = resolve_pending_clarification_response(
				request_id=request_id,
				session_id=session_id,
				user_id=user_id,
				site_name=site_name,
				message=fallback_option,
				signal_payload=pending_clarification_signal,
				clarification_attempt_count=int(max(0, clarification_state.attempt_count)),
				max_attempts=int(max(1, clarification_state.max_attempts)),
				grounded_turn=latest_grounded_turn,
				control_evidence_payload=(
					conversation_control_evidence_contract.to_payload()
					if conversation_control_evidence_contract is not None and hasattr(conversation_control_evidence_contract, "to_payload")
					else {}
				),
			)
			clarification_decision = str(clarification_response_contract.decision or "").strip()
		else:
			answer_text = ""
			if clarification_state.max_attempts_reached:
				answer_text = pending_clarification_fallback_stop_answer(pending_clarification_signal)
			elif clarification_decision == "meta_question":
				answer_text = pending_clarification_meta_answer(pending_clarification_signal)
			elif clarification_decision == "empty_ack":
				answer_text = pending_clarification_empty_ack_answer(pending_clarification_signal)
			else:
				answer_text = pending_clarification_repeat_answer(pending_clarification_signal)
			execution_path = ExecutionPath(
				request_id=request_id,
				path="clarification",
				reason=str(clarification_response_contract.reason or "").strip()
				or "A governed clarification is still pending before the ERP lane can continue.",
				requires_runtime=False,
				grounded_required=False,
			)
			append_message(session_doc, "user", raw_message)
			response_mode = (
				"fallback_stop"
				if clarification_state.max_attempts_reached
				else clarification_decision or "reask_pending_clarification"
			)
			observability_payload = record_phase55_observability_event(
				request_id=request_id,
				session_id=session_id,
				event_family="clarification",
				event_name=response_mode,
				details={
					"pending_reason_type": str(pending_clarification_signal.get("reason_type") or "").strip(),
					"attempt_count": int(max(0, clarification_state.attempt_count)),
					"max_attempts": int(max(1, clarification_state.max_attempts)),
				},
			)
			boundary_payload = _clarification_boundary_payload(
				request_id=request_id,
				session_id=session_id,
				clarification_response_contract=clarification_response_contract,
				frontdoor_contract=frontdoor_contract,
				latest_grounded_turn_available=latest_grounded_turn_available,
				latest_grounded_turn=latest_grounded_turn,
			)
			answer_mode = f"clarification_{response_mode}"
			runtime_metadata_envelope = _clarification_runtime_metadata_envelope(answer_mode=answer_mode)
			pre_assistant_payloads = [
				interaction_contract.to_payload(),
				frontdoor_semantic_result.to_payload(),
				frontdoor_contract.to_payload(),
				clarification_response_contract.to_payload(),
				observability_payload,
				boundary_payload,
				runtime_metadata_envelope,
				execution_path.to_payload(),
			]
			if not clarification_state.max_attempts_reached:
				pre_assistant_payloads.append(pending_clarification_signal)
			authorized_emission = emit_authorized_assistant_answer(
				session_doc=session_doc,
				answer_text=answer_text,
				answer_type=ANSWER_TYPE_CONTROL,
				append_message=append_message,
				append_tool_payload=append_tool_payload,
				assistant_text_payload=assistant_text_payload,
				control_meta_authority=_clarification_control_authority(
					answer_mode=answer_mode,
					reason=str(clarification_response_contract.reason or "").strip()
					or "A governed clarification is still pending before the ERP lane can continue.",
				),
				runtime_trace_payload={
					"runtime_metadata_envelope": runtime_metadata_envelope,
					"agent_meta": {
						"engine": "pending_clarification_resolver",
						"mode": response_mode,
						"runtime_metadata_envelope": runtime_metadata_envelope,
					},
				},
				pre_assistant_tool_payloads=pre_assistant_payloads,
			)
			if authorized_emission.emitted and clarification_state.max_attempts_reached:
				clear_pending_clarification_signal(session_doc)
			elif authorized_emission.emitted:
				store_pending_clarification_signal(
					session_doc,
					pending_clarification_signal,
					attempt_count=int(max(0, clarification_state.attempt_count)),
					max_attempts=int(max(1, clarification_state.max_attempts)),
				)
			save_session(session_doc, ignore_permissions=False)
			return True, clarification_response_contract, raw_message, {
				"ok": bool(authorized_emission.emitted),
				"request_id": request_id,
				"mode": "clarification",
				"agent_meta": {
					"engine": "pending_clarification_resolver",
					"mode": response_mode,
					"runtime_metadata_envelope": runtime_metadata_envelope,
					"authorized_emission": authorized_emission.to_payload(),
				},
			}
	clear_pending_clarification_signal(session_doc)
	append_tool_payload(
		session_doc,
		record_phase55_observability_event(
			request_id=request_id,
			session_id=session_id,
			event_family="clarification",
			event_name=str(clarification_response_contract.decision or "").strip() or "resolved",
			details={
				"pending_reason_type": str(pending_clarification_signal.get("reason_type") or "").strip(),
				"attempt_count": int(max(0, clarification_state.attempt_count)),
				"max_attempts": int(max(1, clarification_state.max_attempts)),
				"resolved_option": str(clarification_response_contract.resolved_option or "").strip(),
			},
		),
	)
	resolved_message = raw_message
	if str(clarification_response_contract.decision or "").strip() == "resolved_option":
		resolved_message = str(clarification_response_contract.resolved_option or "").strip() or resolved_message
	return False, clarification_response_contract, resolved_message, None
