from __future__ import annotations

import time
from typing import Any, Callable, Dict, Tuple

from ai_assistant_ui.qwen_chat.contracts import ExecutionPath, build_audit_envelope, build_followup_resolution_contract
from ai_assistant_ui.qwen_chat.knowledge_boundary import render_knowledge_boundary_answer
from ai_assistant_ui.qwen_chat.observability import record_phase6_observability_event, record_phase6_performance_metric
from ai_assistant_ui.qwen_chat.reasoning_execution import build_reasoning_boundary_answer, execute_erp_business_reasoning


def handle_reasoning_turn(
	*,
	session_doc,
	request_id: str,
	session_id: str,
	user_id: str,
	message: str,
	raw_message: str,
	reasoning_recent_messages,
	reasoning_display_preferences: Dict[str, Any],
	interaction_contract,
	frontdoor_semantic_result,
	frontdoor_contract,
	clarification_response_contract,
	provisional_response_policy_contract,
	reasoning_activation_contract,
	reasoning_semantic_result,
	latest_grounded_turn: Dict[str, Any],
	latest_family_artifact: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
	latest_reasoning_contract: Dict[str, Any],
	append_message: Callable[..., None],
	append_tool_payload: Callable[..., None],
	append_knowledge_boundary_contract: Callable[..., Dict[str, Any]],
	assistant_text_payload: Callable[[str], str],
	save_session: Callable[..., None],
	phase6_execution_event_level: Callable[[str], str],
) -> Tuple[bool, Dict[str, Any] | None]:
	if not (
		str(getattr(reasoning_semantic_result, "status", "") or "").strip() == "accepted"
		and getattr(reasoning_semantic_result, "intent", None) is not None
	):
		return False, None

	reasoning_execution_started_at = time.perf_counter()
	reasoning_execution = execute_erp_business_reasoning(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		message=message,
		recent_messages=reasoning_recent_messages,
		activation_contract=reasoning_activation_contract.to_payload(),
		semantic_activation_result=reasoning_semantic_result.to_payload(),
		latest_grounded_turn=latest_grounded_turn,
		latest_family_artifact=latest_family_artifact,
		latest_assistant_payload=latest_assistant_payload,
		presentation_preferences={
			"million": bool(reasoning_display_preferences.get("million")),
			"bullet": str(getattr(reasoning_semantic_result.intent, "presentation_style", "") or "").strip() == "bullet",
			"table": str(getattr(reasoning_semantic_result.intent, "presentation_style", "") or "").strip() == "table",
		},
		prior_reasoning_contract=latest_reasoning_contract,
		prior_answer_text=str(latest_assistant_payload.get("text") or "").strip(),
	)
	reasoning_execution_latency_ms = int(max(0, round((time.perf_counter() - reasoning_execution_started_at) * 1000)))
	append_tool_payload(
		session_doc,
		record_phase6_observability_event(
			request_id=request_id,
			session_id=session_id,
			event_family="reasoning_execution",
			event_name=str(reasoning_execution.status or "").strip() or "unknown",
			event_level=phase6_execution_event_level(reasoning_execution.status),
			details={
				"reasoning_type": str(getattr(reasoning_semantic_result.intent, "reasoning_type", "") or "").strip(),
				"grounded_source_name": str(reasoning_activation_contract.grounded_source_name or "").strip(),
				"grounded_family_id": str(reasoning_activation_contract.grounded_family_id or "").strip(),
				"latency_ms": reasoning_execution_latency_ms,
				"validation_error": str(reasoning_execution.validation_error or "").strip(),
				"runtime_error": str(reasoning_execution.runtime_error or "").strip(),
				"allowed_to_answer": bool((reasoning_execution.reasoning_contract or {}).get("allowed_to_answer")),
				"grounding_sufficient": bool((reasoning_execution.reasoning_contract or {}).get("grounding_sufficient")),
				"grounding_gaps": list((reasoning_execution.reasoning_contract or {}).get("grounding_gaps") or []),
			},
		),
	)
	append_tool_payload(
		session_doc,
		record_phase6_performance_metric(
			request_id=request_id,
			session_id=session_id,
			metric_name="reasoning_execution_latency",
			metric_value=float(reasoning_execution_latency_ms),
			metric_unit="ms",
			details={
				"status": str(reasoning_execution.status or "").strip(),
				"reasoning_type": str(getattr(reasoning_semantic_result.intent, "reasoning_type", "") or "").strip(),
			},
		),
	)

	if reasoning_execution.status == "answered":
		reasoning_followup_resolution = build_followup_resolution_contract(
			request_id=request_id,
			mode="reasoning_lane",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The current turn was handled by the grounded ERP business reasoning lane.",
		)
		execution_path = ExecutionPath(
			request_id=request_id,
			path="reasoning_lane",
			reason="The current turn requested grounded ERP interpretation, explanation, recommendation, or continuation detail.",
			requires_runtime=True,
			grounded_required=True,
		)
		if (session_doc.title or "").strip() in ("", "New Qwen Chat"):
			session_doc.title = (raw_message[:60] + "…") if len(raw_message) > 60 else raw_message
		append_message(session_doc, "user", raw_message)
		append_tool_payload(session_doc, interaction_contract.to_payload())
		append_tool_payload(session_doc, frontdoor_semantic_result.to_payload())
		append_tool_payload(session_doc, frontdoor_contract.to_payload())
		if clarification_response_contract is not None:
			append_tool_payload(session_doc, clarification_response_contract.to_payload())
		append_tool_payload(session_doc, provisional_response_policy_contract.to_payload())
		append_tool_payload(session_doc, reasoning_activation_contract.to_payload())
		append_tool_payload(session_doc, reasoning_semantic_result.to_payload())
		append_tool_payload(session_doc, reasoning_execution.to_payload())
		if reasoning_execution.reasoning_contract:
			append_tool_payload(session_doc, reasoning_execution.reasoning_contract)
		append_knowledge_boundary_contract(
			session_doc,
			request_id=request_id,
			session_id=session_id,
			proposed_lane="reasoning_lane",
			front_door_contract=frontdoor_contract.to_payload(),
			reasoning_activation_contract=reasoning_activation_contract.to_payload(),
			reasoning_contract=reasoning_execution.reasoning_contract,
			grounded_turn=latest_grounded_turn,
		)
		append_tool_payload(session_doc, reasoning_followup_resolution.to_payload())
		append_tool_payload(session_doc, execution_path.to_payload())
		answer_text = str(reasoning_execution.answer_text or "").strip()
		append_message(session_doc, "assistant", assistant_text_payload(answer_text))
		append_tool_payload(
			session_doc,
			build_audit_envelope(
				interaction_contract=interaction_contract,
				followup_resolution=reasoning_followup_resolution,
				execution_path=execution_path,
				runtime_trace_payload={
					"agent_meta": dict(reasoning_execution.agent_meta or {}),
					"runtime_latency_ms": int(
						max(
							0,
							(
								(reasoning_execution.agent_meta.get("telemetry") or {})
								if isinstance(reasoning_execution.agent_meta, dict)
								else {}
							).get("latency_ms")
							or 0,
						)
					),
				},
				grounded_turn_context=latest_grounded_turn,
				answer_text=answer_text,
			).to_payload(),
		)
		save_session(session_doc, ignore_permissions=False)
		return True, {
			"ok": True,
			"request_id": request_id,
			"mode": "erp_business_reasoning",
			"answer_text": answer_text,
			"agent_meta": reasoning_execution.agent_meta if isinstance(reasoning_execution.agent_meta, dict) else {},
		}

	reasoning_boundary_answer = build_reasoning_boundary_answer(
		execution_result=reasoning_execution,
		activation_contract=reasoning_activation_contract.to_payload(),
		semantic_activation_result=reasoning_semantic_result.to_payload(),
	)
	reasoning_followup_resolution = build_followup_resolution_contract(
		request_id=request_id,
		mode="reasoning_lane",
		depends_on_grounded_turn=True,
		self_contained=False,
		latest_grounded_turn_available=True,
		reason="The current turn entered the grounded ERP reasoning lane but was stopped by a deterministic reasoning boundary.",
	)
	execution_path = ExecutionPath(
		request_id=request_id,
		path="reasoning_lane_guardrail",
		reason="The current turn requested grounded ERP reasoning, but deterministic execution boundaries prevented an unsafe answer.",
		requires_runtime=True,
		grounded_required=True,
	)
	if (session_doc.title or "").strip() in ("", "New Qwen Chat"):
		session_doc.title = (raw_message[:60] + "…") if len(raw_message) > 60 else raw_message
	append_message(session_doc, "user", raw_message)
	append_tool_payload(session_doc, interaction_contract.to_payload())
	append_tool_payload(session_doc, frontdoor_semantic_result.to_payload())
	append_tool_payload(session_doc, frontdoor_contract.to_payload())
	if clarification_response_contract is not None:
		append_tool_payload(session_doc, clarification_response_contract.to_payload())
	append_tool_payload(session_doc, provisional_response_policy_contract.to_payload())
	append_tool_payload(session_doc, reasoning_activation_contract.to_payload())
	append_tool_payload(session_doc, reasoning_semantic_result.to_payload())
	append_tool_payload(session_doc, reasoning_execution.to_payload())
	if reasoning_execution.reasoning_contract:
		append_tool_payload(session_doc, reasoning_execution.reasoning_contract)
	boundary_payload = append_knowledge_boundary_contract(
		session_doc,
		request_id=request_id,
		session_id=session_id,
		proposed_lane="reasoning_lane",
		front_door_contract=frontdoor_contract.to_payload(),
		reasoning_activation_contract=reasoning_activation_contract.to_payload(),
		reasoning_contract=reasoning_execution.reasoning_contract,
		grounded_turn=latest_grounded_turn,
	)
	append_tool_payload(session_doc, reasoning_followup_resolution.to_payload())
	append_tool_payload(session_doc, execution_path.to_payload())
	answer_text = render_knowledge_boundary_answer(
		boundary_contract=boundary_payload,
		detail_answer=reasoning_boundary_answer,
	)
	append_message(session_doc, "assistant", assistant_text_payload(answer_text))
	append_tool_payload(
		session_doc,
		build_audit_envelope(
			interaction_contract=interaction_contract,
			followup_resolution=reasoning_followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload={
				"agent_meta": dict(reasoning_execution.agent_meta or {}),
				"runtime_latency_ms": int(
					max(
						0,
						(
							(reasoning_execution.agent_meta.get("telemetry") or {})
							if isinstance(reasoning_execution.agent_meta, dict)
							else {}
						).get("latency_ms")
						or 0,
					)
				),
			},
			grounded_turn_context=latest_grounded_turn,
			answer_text=answer_text,
		).to_payload(),
	)
	save_session(session_doc, ignore_permissions=False)
	return True, {
		"ok": True,
		"request_id": request_id,
		"mode": "erp_business_reasoning",
		"answer_text": reasoning_boundary_answer,
		"agent_meta": {
			"engine": "erp_business_reasoning_guardrail",
			"status": str(reasoning_execution.status or "").strip(),
		},
	}
