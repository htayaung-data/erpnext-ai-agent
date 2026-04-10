from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

from ai_assistant_ui.qwen_chat.contracts import ExecutionPath, build_audit_envelope, build_followup_resolution_contract
from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import (
	SemanticFrontDoorIntent,
	SemanticFrontDoorResult,
	build_front_door_intent_gate_contract_from_semantic_result,
	interpret_front_door_semantically,
	render_front_door_answer,
)
from ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution import (
	maybe_build_governed_kpi_value_frontdoor_response,
)
from ai_assistant_ui.qwen_chat.governed_kpi_support import maybe_build_governed_kpi_frontdoor_response
from ai_assistant_ui.qwen_chat.observability import record_phase55_observability_event


def _front_door_answer_text(frontdoor_contract: Any) -> str:
	if frontdoor_contract is None:
		return ""
	response_payload = getattr(frontdoor_contract, "response_payload", {})
	if not isinstance(response_payload, dict):
		return ""
	return str(response_payload.get("text") or "").strip()


def _front_door_clarification_signal(frontdoor_contract: Any) -> Dict[str, Any]:
	if frontdoor_contract is None:
		return {}
	response_payload = getattr(frontdoor_contract, "response_payload", {})
	if not isinstance(response_payload, dict):
		return {}
	payload = response_payload.get("clarification_signal_payload")
	return dict(payload) if isinstance(payload, dict) else {}


def _frontdoor_response_engine(frontdoor_render_result: Any) -> str:
	return "frontdoor_response_renderer" if bool(getattr(frontdoor_render_result, "ok", False)) else "semantic_frontdoor"


_FRONTDOOR_INTENTS_THAT_OVERRIDE_REASONING = {
	"low_signal_non_business",
	"greeting",
	"thanks",
	"acknowledgement",
	"closure_signoff",
	"capability_question",
	"governed_kpi_definition",
	"governed_kpi_value",
}


def _frontdoor_semantic_preserves_frontdoor_ownership(frontdoor_semantic_result: Any) -> bool:
	intent = getattr(frontdoor_semantic_result, "intent", None)
	intent_class = str(getattr(intent, "intent_class", "") or "").strip()
	status = str(getattr(frontdoor_semantic_result, "status", "") or "").strip()
	return bool(
		intent_class in _FRONTDOOR_INTENTS_THAT_OVERRIDE_REASONING
		and status in {"accepted", "guardrailed_to_route_onward"}
	)


def evaluate_frontdoor_lane(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages,
	grounded_context_available: bool,
	latest_grounded_turn: Dict[str, Any] | None = None,
	latest_recovery_contract_available: bool,
	pre_frontdoor_reasoning_semantic_result,
	post_clarification_stop_acknowledgement: bool = False,
) -> Tuple[Any, Any, Any, str]:
	frontdoor_render_result = None
	frontdoor_answer = ""
	if post_clarification_stop_acknowledgement:
		frontdoor_semantic_result = SemanticFrontDoorResult(
			status="accepted",
			intent=SemanticFrontDoorIntent(
				intent_class="acknowledgement",
				confidence=1.0,
				reason=(
					"The immediately preceding clarification turn ended with fallback_stop, "
					"so a short acknowledgement should remain in the front-door lane until "
					"the user starts a new substantive ERP request."
				),
			),
			confidence_threshold=1.0,
		)
	elif governed_kpi_frontdoor := maybe_build_governed_kpi_frontdoor_response(
		request_id=request_id,
		message=message,
	):
		frontdoor_semantic_result = governed_kpi_frontdoor.get("semantic_result")
		frontdoor_contract = governed_kpi_frontdoor.get("frontdoor_contract")
		frontdoor_answer = str(governed_kpi_frontdoor.get("frontdoor_answer") or "").strip()
		return frontdoor_semantic_result, frontdoor_contract, frontdoor_render_result, frontdoor_answer
	elif governed_kpi_value_frontdoor := maybe_build_governed_kpi_value_frontdoor_response(
		request_id=request_id,
		message=message,
		grounded_turn=latest_grounded_turn,
	):
		frontdoor_semantic_result = governed_kpi_value_frontdoor.get("semantic_result")
		frontdoor_contract = governed_kpi_value_frontdoor.get("frontdoor_contract")
		frontdoor_answer = str(governed_kpi_value_frontdoor.get("frontdoor_answer") or "").strip()
		return frontdoor_semantic_result, frontdoor_contract, frontdoor_render_result, frontdoor_answer
	elif (
		pre_frontdoor_reasoning_semantic_result is not None
		and str(pre_frontdoor_reasoning_semantic_result.status or "").strip() == "accepted"
		and getattr(pre_frontdoor_reasoning_semantic_result, "intent", None) is not None
	):
		frontdoor_semantic_candidate = interpret_front_door_semantically(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=recent_messages,
			grounded_context_available=grounded_context_available,
		)
		if _frontdoor_semantic_preserves_frontdoor_ownership(frontdoor_semantic_candidate):
			frontdoor_semantic_result = frontdoor_semantic_candidate
		else:
			reasoning_intent = pre_frontdoor_reasoning_semantic_result.intent
			frontdoor_semantic_result = SemanticFrontDoorResult(
				status="guardrailed_to_route_onward",
				intent=SemanticFrontDoorIntent(
					intent_class="route_onward",
					confidence=max(0.95, float(getattr(reasoning_intent, "confidence", 0.0) or 0.0)),
					reason=(
						f"Grounded ERP business reasoning activation accepted the turn as "
						f"`{str(getattr(reasoning_intent, 'reasoning_type', '') or '').strip()}`, so front door must route onward."
					),
				),
				confidence_threshold=1.0,
			)
	else:
		frontdoor_semantic_result = interpret_front_door_semantically(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=recent_messages,
			grounded_context_available=grounded_context_available,
		)
	frontdoor_contract = build_front_door_intent_gate_contract_from_semantic_result(
		request_id=request_id,
		semantic_result=frontdoor_semantic_result,
		grounded_context_available=grounded_context_available,
	)
	if post_clarification_stop_acknowledgement:
		frontdoor_answer = _front_door_answer_text(frontdoor_contract)
	elif bool(getattr(frontdoor_contract, "handle_in_front_door", False)):
		intent_class = str(getattr(frontdoor_contract, "intent_class", "") or "").strip()
		if intent_class == "session_flow" and not latest_recovery_contract_available:
			frontdoor_answer = _front_door_answer_text(frontdoor_contract)
		else:
			frontdoor_render_result = render_front_door_answer(
				request_id=request_id,
				session_id=session_id,
				user_id=user_id,
				site_name=site_name,
				message=message,
				recent_messages=recent_messages,
				grounded_context_available=grounded_context_available,
				frontdoor_contract=frontdoor_contract,
			)
			frontdoor_answer = str(frontdoor_render_result.answer_text or "").strip() or _front_door_answer_text(frontdoor_contract)
	return frontdoor_semantic_result, frontdoor_contract, frontdoor_render_result, frontdoor_answer


def handle_frontdoor_turn(
	*,
	session_doc,
	request_id: str,
	session_id: str,
	message: str,
	interaction_contract,
	frontdoor_semantic_result,
	frontdoor_contract,
	frontdoor_render_result,
	frontdoor_answer: str,
	context_force_new_query: bool,
	latest_grounded_turn_available: bool,
	latest_grounded_turn: Dict[str, Any],
	append_message: Callable[..., None],
	append_tool_payload: Callable[..., None],
	append_knowledge_boundary_contract: Callable[..., Dict[str, Any]],
	assistant_text_payload: Callable[[str], str],
	store_pending_clarification_signal: Callable[..., None],
	save_session: Callable[..., None],
	raw_message: str = "",
	clarification_response_contract=None,
) -> Tuple[bool, Dict[str, Any] | None]:
	if not (
		bool(getattr(frontdoor_contract, "handle_in_front_door", False))
		and frontdoor_answer
		and not bool(context_force_new_query)
	):
		return False, None
	frontdoor_followup_resolution = build_followup_resolution_contract(
		request_id=request_id,
		mode="front_door",
		requested_modes=[],
		target_dimension="",
		target_limit=0,
		sort_direction="",
		target_metric="",
		requested_columns=[],
		requested_time_scope="",
		target_capability_id="",
		target_report="",
		depends_on_grounded_turn=latest_grounded_turn_available,
		self_contained=not latest_grounded_turn_available,
		latest_grounded_turn_available=latest_grounded_turn_available,
		reason=str(getattr(frontdoor_contract, "reason", "") or "").strip()
		or "The turn was handled in the front-door lane.",
	)
	execution_path = ExecutionPath(
		request_id=request_id,
		path="front_door",
		reason=str(getattr(frontdoor_contract, "reason", "") or "").strip()
		or "The turn was handled safely in the front-door lane.",
		requires_runtime=False,
		grounded_required=False,
	)
	response_engine = _frontdoor_response_engine(frontdoor_render_result)
	clarification_signal_payload = _front_door_clarification_signal(frontdoor_contract)
	append_message(session_doc, "user", raw_message or message)
	append_tool_payload(session_doc, interaction_contract.to_payload())
	if clarification_response_contract is not None:
		append_tool_payload(session_doc, clarification_response_contract.to_payload())
	append_tool_payload(session_doc, frontdoor_semantic_result.to_payload())
	append_tool_payload(session_doc, frontdoor_contract.to_payload())
	if frontdoor_render_result is not None:
		append_tool_payload(session_doc, frontdoor_render_result.to_payload())
	append_tool_payload(
		session_doc,
		record_phase55_observability_event(
			request_id=request_id,
			session_id=session_id,
			event_family="front_door",
			event_name="handled",
			details={
				"intent_class": str(getattr(frontdoor_contract, "intent_class", "") or "").strip(),
				"response_engine": response_engine,
				"pending_clarification": bool(clarification_signal_payload),
			},
		),
	)
	append_knowledge_boundary_contract(
		session_doc,
		request_id=request_id,
		session_id=session_id,
		proposed_lane="front_door",
		clarification_resolution=clarification_response_contract.to_payload() if clarification_response_contract is not None else {},
		front_door_contract=frontdoor_contract.to_payload(),
		grounded_turn=latest_grounded_turn if latest_grounded_turn_available else {},
	)
	append_tool_payload(session_doc, execution_path.to_payload())
	append_message(session_doc, "assistant", assistant_text_payload(frontdoor_answer))
	if clarification_signal_payload:
		append_tool_payload(session_doc, clarification_signal_payload)
		store_pending_clarification_signal(session_doc, clarification_signal_payload)
	append_tool_payload(
		session_doc,
		build_audit_envelope(
			interaction_contract=interaction_contract,
			followup_resolution=frontdoor_followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload={},
			grounded_turn_context=latest_grounded_turn if latest_grounded_turn_available else {},
			answer_text=frontdoor_answer,
		).to_payload(),
	)
	save_session(session_doc, ignore_permissions=False)
	return True, {
		"ok": True,
		"request_id": request_id,
		"mode": "front_door",
		"agent_meta": {
			"engine": response_engine,
			"intent_class": str(getattr(frontdoor_contract, "intent_class", "") or "").strip(),
		},
	}
