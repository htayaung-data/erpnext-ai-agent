from __future__ import annotations

import time
from typing import Any, Dict, Tuple

from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_audit_envelope,
	build_followup_resolution_contract,
)
from ai_assistant_ui.qwen_chat.observability import (
	record_phase6_observability_event,
	record_phase6_performance_metric,
)


def handle_recovery_guidance_response(
	session_doc,
	*,
	request_id: str,
	raw_message: str,
	interaction_contract,
	frontdoor_semantic_result,
	frontdoor_contract,
	clarification_response_contract,
	response_policy_contract,
	semantic_repair_payload: Dict[str, Any],
	repair_contract_payload: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	answer_text: str,
	append_message,
	append_tool_payload,
	assistant_text_payload,
	save_session,
) -> Tuple[bool, Dict[str, Any]]:
	started_at = time.perf_counter()
	followup_resolution = build_followup_resolution_contract(
		request_id=request_id,
		mode="repair_guidance",
		depends_on_grounded_turn=bool(latest_grounded_turn),
		self_contained=False,
		latest_grounded_turn_available=bool(latest_grounded_turn),
		reason="The current turn asked for bounded recovery guidance rather than new data retrieval.",
	)
	execution_path = ExecutionPath(
		request_id=request_id,
		path="recovery_guidance",
		reason="The assistant rendered bounded guidance from the active recovery contract.",
		requires_runtime=False,
		grounded_required=bool(latest_grounded_turn),
	)
	if (session_doc.title or "").strip() in ("", "New Qwen Chat"):
		session_doc.title = (raw_message[:60] + "…") if len(raw_message) > 60 else raw_message
	append_message(session_doc, "user", raw_message)
	append_tool_payload(session_doc, interaction_contract.to_payload())
	append_tool_payload(session_doc, frontdoor_semantic_result.to_payload())
	append_tool_payload(session_doc, frontdoor_contract.to_payload())
	if clarification_response_contract is not None:
		append_tool_payload(session_doc, clarification_response_contract.to_payload())
	append_tool_payload(session_doc, response_policy_contract.to_payload())
	append_tool_payload(session_doc, semantic_repair_payload)
	append_tool_payload(session_doc, repair_contract_payload)
	append_tool_payload(session_doc, followup_resolution.to_payload())
	append_tool_payload(session_doc, execution_path.to_payload())
	append_message(session_doc, "assistant", assistant_text_payload(answer_text))
	recovery_guidance_latency_ms = int(max(0, round((time.perf_counter() - started_at) * 1000)))
	append_tool_payload(
		session_doc,
		record_phase6_observability_event(
			request_id=request_id,
			session_id=str(getattr(session_doc, "name", "") or "").strip(),
			event_family="recovery_guidance",
			event_name="answered",
			event_level="info",
			details={
				"repair_intent_type": str(repair_contract_payload.get("repair_intent_type") or "").strip(),
				"repair_state": str(repair_contract_payload.get("repair_state") or "").strip(),
				"allowed_next_lane": str(repair_contract_payload.get("allowed_next_lane") or "").strip(),
				"grounded_context_available": bool(latest_grounded_turn),
				"latency_ms": recovery_guidance_latency_ms,
			},
		),
	)
	append_tool_payload(
		session_doc,
		record_phase6_performance_metric(
			request_id=request_id,
			session_id=str(getattr(session_doc, "name", "") or "").strip(),
			metric_name="recovery_guidance_latency",
			metric_value=float(recovery_guidance_latency_ms),
			metric_unit="ms",
			details={
				"repair_intent_type": str(repair_contract_payload.get("repair_intent_type") or "").strip(),
				"repair_state": str(repair_contract_payload.get("repair_state") or "").strip(),
			},
		),
	)
	append_tool_payload(
		session_doc,
		build_audit_envelope(
			interaction_contract=interaction_contract,
			followup_resolution=followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload={},
			grounded_turn_context=latest_grounded_turn,
			answer_text=answer_text,
		).to_payload(),
	)
	save_session(session_doc, ignore_permissions=False)
	return True, {
		"ok": True,
		"request_id": request_id,
		"mode": "recovery_guidance",
		"answer_text": answer_text,
		"agent_meta": {"engine": "recovery_guidance"},
	}
