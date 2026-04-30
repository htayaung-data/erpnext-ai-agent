from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_audit_envelope,
	build_followup_resolution_contract,
	build_front_door_intent_gate_contract,
)
from ai_assistant_ui.qwen_chat.compound_request_support import assess_compound_request
from ai_assistant_ui.qwen_chat.clarification_translation import render_clarification_signal_user_text
from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import (
	SemanticFrontDoorIntent,
	SemanticFrontDoorResult,
	build_front_door_intent_gate_contract_from_semantic_result,
	interpret_front_door_semantically,
	render_front_door_answer,
)
from ai_assistant_ui.qwen_chat.governed_composite_runtime_execution import (
	maybe_build_governed_composite_frontdoor_response,
)
from ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution import (
	maybe_build_governed_kpi_value_frontdoor_response,
)
from ai_assistant_ui.qwen_chat.governed_kpi_support import maybe_build_governed_kpi_frontdoor_response
from ai_assistant_ui.qwen_chat.master_data_frontdoor_support import (
	assess_master_data_frontdoor_request,
	maybe_build_master_data_entity_reference_clarification,
)
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


def _front_door_response_payload_item(frontdoor_contract: Any, key: str) -> Dict[str, Any]:
	if frontdoor_contract is None:
		return {}
	response_payload = getattr(frontdoor_contract, "response_payload", {})
	if not isinstance(response_payload, dict):
		return {}
	payload = response_payload.get(key)
	return dict(payload) if isinstance(payload, dict) else {}


def _frontdoor_response_engine(frontdoor_render_result: Any) -> str:
	return "frontdoor_response_renderer" if bool(getattr(frontdoor_render_result, "ok", False)) else "semantic_frontdoor"


def _looks_like_creative_non_business_request(message: str) -> bool:
	text = f" {str(message or '').strip().lower()} "
	if not text.strip():
		return False
	creative_actions = (
		"write",
		"compose",
		"create",
		"generate",
		"make",
		"draft",
	)
	creative_outputs = (
		"poem",
		"poetry",
		"joke",
		"story",
		"song",
		"rap",
		"haiku",
		"fiction",
		"fairy tale",
	)
	return any(f" {action} " in text for action in creative_actions) and any(
		f" {output} " in text for output in creative_outputs
	)


_FRONTDOOR_INTENTS_THAT_OVERRIDE_REASONING = {
	"low_signal_non_business",
	"greeting",
	"thanks",
	"acknowledgement",
	"closure_signoff",
	"capability_question",
	"governed_kpi_definition",
	"governed_composite_value",
	"governed_kpi_value",
	"compound_request_clarification",
	"master_data_grain_clarification",
}


_DATA_VALUE_FRONTDOOR_INTENTS = {"governed_composite_value", "governed_kpi_value"}


def _frontdoor_data_value_payload_missing(frontdoor_contract: Any) -> bool:
	intent_class = str(getattr(frontdoor_contract, "intent_class", "") or "").strip()
	if intent_class not in _DATA_VALUE_FRONTDOOR_INTENTS:
		return False
	response_payload = getattr(frontdoor_contract, "response_payload", {})
	if not isinstance(response_payload, dict):
		return True
	for key in (
		"composite_artifact",
		"normalized_family_artifact",
		"rendered_family_response",
		"grounded_turn_context",
		"runtime_trace_payload",
		"kpi_value_artifact",
		"kpi_ranking_artifact",
		"clarification_signal_payload",
	):
		payload = response_payload.get(key)
		if isinstance(payload, dict) and payload:
			return False
	return True


def _frontdoor_semantic_preserves_frontdoor_ownership(frontdoor_semantic_result: Any) -> bool:
	intent = getattr(frontdoor_semantic_result, "intent", None)
	intent_class = str(getattr(intent, "intent_class", "") or "").strip()
	status = str(getattr(frontdoor_semantic_result, "status", "") or "").strip()
	return bool(
		intent_class in _FRONTDOOR_INTENTS_THAT_OVERRIDE_REASONING
		and status in {"accepted", "guardrailed_to_route_onward"}
	)


def _frontdoor_payload_only_response(
	frontdoor_contract: Any,
	*,
	latest_recovery_contract_available: bool,
) -> bool:
	intent_class = str(getattr(frontdoor_contract, "intent_class", "") or "").strip()
	response_mode = str(getattr(frontdoor_contract, "response_mode", "") or "").strip()
	if response_mode == "clarification_signal":
		return True
	return intent_class == "session_flow" and not latest_recovery_contract_available


def _frontdoor_contract_can_handle_fresh_breakout(frontdoor_contract: Any) -> bool:
	"""
	Context isolation means "do not reuse the previous artifact"; it should not
	block a self-contained governed answer that the front-door already resolved.
	"""
	intent_class = str(getattr(frontdoor_contract, "intent_class", "") or "").strip()
	return intent_class in {"governed_composite_value", "governed_kpi_value", "governed_kpi_definition"}


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
	defer_runtime_value_frontdoor: bool = False,
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
	elif _looks_like_creative_non_business_request(message):
		frontdoor_semantic_result = SemanticFrontDoorResult(
			status="accepted",
			intent=SemanticFrontDoorIntent(
				intent_class="low_signal_non_business",
				confidence=1.0,
				reason="The request asks for creative content generation rather than a governed ERP/business answer.",
			),
			confidence_threshold=1.0,
		)
		frontdoor_contract = build_front_door_intent_gate_contract(
			request_id=request_id,
			intent_class="low_signal_non_business",
			confidence=1.0,
			grounded_context_available=grounded_context_available,
			reason="The request asks for creative content generation rather than a governed ERP/business answer.",
		)
		frontdoor_answer = _front_door_answer_text(frontdoor_contract)
		return frontdoor_semantic_result, frontdoor_contract, frontdoor_render_result, frontdoor_answer
	elif compound_request := assess_compound_request(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
	):
		assessment_contract = compound_request.get("assessment_contract")
		clarification_signal = compound_request.get("clarification_signal")
		compound_status = str(getattr(assessment_contract, "status", "") or "").strip()
		if compound_status == "ordered_execution_ready":
			frontdoor_semantic_result = SemanticFrontDoorResult(
				status="accepted",
				intent=SemanticFrontDoorIntent(
					intent_class="route_onward",
					confidence=1.0,
					reason=str(compound_request.get("reason") or "").strip(),
				),
				confidence_threshold=1.0,
			)
			frontdoor_contract = build_front_door_intent_gate_contract(
				request_id=request_id,
				intent_class="route_onward",
				confidence=1.0,
				grounded_context_available=grounded_context_available,
				reason=str(compound_request.get("reason") or "").strip(),
				response_payload_override={
					"compound_request_assessment": (
						assessment_contract.to_payload() if assessment_contract is not None else {}
					),
				},
			)
			frontdoor_answer = ""
			return frontdoor_semantic_result, frontdoor_contract, frontdoor_render_result, frontdoor_answer
		frontdoor_semantic_result = SemanticFrontDoorResult(
			status="accepted",
			intent=SemanticFrontDoorIntent(
				intent_class="compound_request_clarification",
				confidence=1.0,
				reason=str(compound_request.get("reason") or "").strip(),
			),
			confidence_threshold=1.0,
		)
		frontdoor_contract = build_front_door_intent_gate_contract(
			request_id=request_id,
			intent_class="compound_request_clarification",
			confidence=1.0,
			grounded_context_available=grounded_context_available,
			reason=str(compound_request.get("reason") or "").strip(),
			response_payload_override={
				"text": str(compound_request.get("user_question") or "").strip(),
				"suggested_prompts": list(getattr(clarification_signal, "suggested_options", []) or []),
				"clarification_signal_payload": (
					clarification_signal.to_payload() if clarification_signal is not None else {}
				),
				"compound_request_assessment": (
					assessment_contract.to_payload() if assessment_contract is not None else {}
				),
			},
		)
		frontdoor_answer = _front_door_answer_text(frontdoor_contract)
		return frontdoor_semantic_result, frontdoor_contract, frontdoor_render_result, frontdoor_answer
	elif not defer_runtime_value_frontdoor and (
		governed_kpi_frontdoor := maybe_build_governed_kpi_frontdoor_response(
		request_id=request_id,
		message=message,
	)
	):
		frontdoor_semantic_result = governed_kpi_frontdoor.get("semantic_result")
		frontdoor_contract = governed_kpi_frontdoor.get("frontdoor_contract")
		frontdoor_answer = str(governed_kpi_frontdoor.get("frontdoor_answer") or "").strip()
		return frontdoor_semantic_result, frontdoor_contract, frontdoor_render_result, frontdoor_answer
	elif not defer_runtime_value_frontdoor and (
		governed_composite_frontdoor := maybe_build_governed_composite_frontdoor_response(
			request_id=request_id,
			message=message,
		)
	):
		frontdoor_semantic_result = governed_composite_frontdoor.get("semantic_result")
		frontdoor_contract = governed_composite_frontdoor.get("frontdoor_contract")
		frontdoor_answer = str(governed_composite_frontdoor.get("frontdoor_answer") or "").strip()
		return frontdoor_semantic_result, frontdoor_contract, frontdoor_render_result, frontdoor_answer
	elif not defer_runtime_value_frontdoor and (
		governed_kpi_value_frontdoor := maybe_build_governed_kpi_value_frontdoor_response(
			request_id=request_id,
			message=message,
			grounded_turn=latest_grounded_turn,
		)
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
	master_data_frontdoor = None
	if (
		not defer_runtime_value_frontdoor
		and not _frontdoor_semantic_preserves_frontdoor_ownership(frontdoor_semantic_result)
	):
		frontdoor_intent = getattr(frontdoor_semantic_result, "intent", None)
		master_data_frontdoor = assess_master_data_frontdoor_request(
			request_id=request_id,
			message=message,
			frontdoor_extracted_slots=(
				dict(getattr(frontdoor_intent, "extracted_slots", {}) or {})
				if frontdoor_intent is not None
				else {}
			),
		)
		assessment_contract = (
			master_data_frontdoor.get("assessment_contract")
			if isinstance(master_data_frontdoor, dict)
			else None
		)
		clarification_signal = (
			master_data_frontdoor.get("clarification_signal")
			if isinstance(master_data_frontdoor, dict)
			else None
		)
		if (
			assessment_contract is not None
			and str(getattr(assessment_contract, "status", "") or "").strip() == "clarification_required"
			and clarification_signal is not None
		):
			frontdoor_semantic_result = SemanticFrontDoorResult(
				status="accepted",
				intent=SemanticFrontDoorIntent(
					intent_class="master_data_grain_clarification",
					confidence=1.0,
					reason="The request is a master-data lookup, but the entity grain still needs clarification.",
				),
				confidence_threshold=1.0,
			)
			frontdoor_contract = build_front_door_intent_gate_contract(
				request_id=request_id,
				intent_class="master_data_grain_clarification",
				confidence=1.0,
				grounded_context_available=grounded_context_available,
				reason="The request is a master-data lookup, but the entity grain still needs clarification.",
				response_payload_override={
					"text": render_clarification_signal_user_text(clarification_signal.to_payload()),
					"suggested_prompts": list(getattr(clarification_signal, "suggested_options", []) or []),
					"clarification_signal_payload": clarification_signal.to_payload(),
					"master_data_frontdoor_assessment": assessment_contract.to_payload(),
				},
			)
			frontdoor_answer = _front_door_answer_text(frontdoor_contract)
			return frontdoor_semantic_result, frontdoor_contract, frontdoor_render_result, frontdoor_answer
	response_payload_override = None
	if isinstance(master_data_frontdoor, dict):
		assessment_contract = master_data_frontdoor.get("assessment_contract")
		if (
			assessment_contract is not None
			and str(getattr(assessment_contract, "status", "") or "").strip() == "resolved"
		):
			entity_reference_followup = maybe_build_master_data_entity_reference_clarification(
				request_id=request_id,
				message=message,
				assessment_contract=assessment_contract,
			)
			entity_reference_clarification = (
				entity_reference_followup.get("clarification_signal")
				if isinstance(entity_reference_followup, dict)
				else None
			)
			entity_reference_resolution = (
				entity_reference_followup.get("entity_reference_resolution")
				if isinstance(entity_reference_followup, dict)
				else {}
			)
			if entity_reference_clarification is not None:
				frontdoor_semantic_result = SemanticFrontDoorResult(
					status="accepted",
					intent=SemanticFrontDoorIntent(
						intent_class="master_data_grain_clarification",
						confidence=1.0,
						reason="The request matched more than one governed entity and needs one exact selection.",
					),
					confidence_threshold=1.0,
				)
				frontdoor_contract = build_front_door_intent_gate_contract(
					request_id=request_id,
					intent_class="master_data_grain_clarification",
					confidence=1.0,
					grounded_context_available=grounded_context_available,
					reason="The request matched more than one governed entity and needs one exact selection.",
					response_payload_override={
						"text": render_clarification_signal_user_text(entity_reference_clarification.to_payload()),
						"suggested_prompts": list(getattr(entity_reference_clarification, "suggested_options", []) or []),
						"clarification_signal_payload": entity_reference_clarification.to_payload(),
						"master_data_frontdoor_assessment": assessment_contract.to_payload(),
						"entity_reference_resolution": (
							dict(entity_reference_resolution) if isinstance(entity_reference_resolution, dict) else {}
						),
					},
				)
				frontdoor_answer = _front_door_answer_text(frontdoor_contract)
				return frontdoor_semantic_result, frontdoor_contract, frontdoor_render_result, frontdoor_answer
			response_payload_override = {
				"master_data_frontdoor_assessment": assessment_contract.to_payload(),
			}
			if isinstance(entity_reference_resolution, dict) and entity_reference_resolution:
				response_payload_override["entity_reference_resolution"] = dict(entity_reference_resolution)
	frontdoor_contract = build_front_door_intent_gate_contract_from_semantic_result(
		request_id=request_id,
		semantic_result=frontdoor_semantic_result,
		grounded_context_available=grounded_context_available,
		response_payload_override=response_payload_override,
	)
	if _frontdoor_data_value_payload_missing(frontdoor_contract):
		intent_class = str(getattr(frontdoor_contract, "intent_class", "") or "").strip()
		frontdoor_semantic_result = SemanticFrontDoorResult(
			status="guardrailed_to_route_onward",
			intent=SemanticFrontDoorIntent(
				intent_class="route_onward",
				confidence=max(0.9, float(getattr(getattr(frontdoor_semantic_result, "intent", None), "confidence", 0.0) or 0.0)),
				reason=(
					f"The semantic front door recognized {intent_class or 'a governed value request'}, "
					"but no governed front-door artifact or clarification payload was produced, so the turn must route onward."
				),
			),
			confidence_threshold=1.0,
		)
		frontdoor_contract = build_front_door_intent_gate_contract(
			request_id=request_id,
			intent_class="route_onward",
			confidence=1.0,
			grounded_context_available=grounded_context_available,
			reason=str(getattr(frontdoor_semantic_result.intent, "reason", "") or "").strip(),
		)
	if post_clarification_stop_acknowledgement or _frontdoor_payload_only_response(
		frontdoor_contract,
		latest_recovery_contract_available=latest_recovery_contract_available,
	):
		frontdoor_answer = _front_door_answer_text(frontdoor_contract)
	elif bool(getattr(frontdoor_contract, "handle_in_front_door", False)):
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
	additional_tool_payloads: list[Dict[str, Any]] | None = None,
) -> Tuple[bool, Dict[str, Any] | None]:
	if not (
		bool(getattr(frontdoor_contract, "handle_in_front_door", False))
		and frontdoor_answer
		and (not bool(context_force_new_query) or _frontdoor_contract_can_handle_fresh_breakout(frontdoor_contract))
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
	composite_artifact_payload = _front_door_response_payload_item(frontdoor_contract, "composite_artifact")
	normalized_family_artifact_payload = _front_door_response_payload_item(frontdoor_contract, "normalized_family_artifact")
	rendered_family_response_payload = _front_door_response_payload_item(frontdoor_contract, "rendered_family_response")
	grounded_turn_context_payload = _front_door_response_payload_item(frontdoor_contract, "grounded_turn_context")
	runtime_trace_payload = _front_door_response_payload_item(frontdoor_contract, "runtime_trace_payload")
	compound_request_assessment_payload = _front_door_response_payload_item(frontdoor_contract, "compound_request_assessment")
	append_message(session_doc, "user", raw_message or message)
	append_tool_payload(session_doc, interaction_contract.to_payload())
	if clarification_response_contract is not None:
		append_tool_payload(session_doc, clarification_response_contract.to_payload())
	for payload in (additional_tool_payloads or []):
		if isinstance(payload, dict) and payload:
			append_tool_payload(session_doc, payload)
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
	if runtime_trace_payload:
		append_tool_payload(session_doc, runtime_trace_payload)
	for payload in (
		composite_artifact_payload,
		normalized_family_artifact_payload,
		rendered_family_response_payload,
		grounded_turn_context_payload,
		compound_request_assessment_payload,
	):
		if payload:
			append_tool_payload(session_doc, payload)
	if clarification_signal_payload:
		append_tool_payload(session_doc, clarification_signal_payload)
		store_pending_clarification_signal(session_doc, clarification_signal_payload)
	append_tool_payload(
		session_doc,
		build_audit_envelope(
			interaction_contract=interaction_contract,
			followup_resolution=frontdoor_followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload=runtime_trace_payload if runtime_trace_payload else {},
			grounded_turn_context=grounded_turn_context_payload if grounded_turn_context_payload else (latest_grounded_turn if latest_grounded_turn_available else {}),
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
