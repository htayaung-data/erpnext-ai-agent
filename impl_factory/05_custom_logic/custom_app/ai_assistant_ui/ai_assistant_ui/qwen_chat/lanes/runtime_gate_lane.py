from __future__ import annotations

import time
from typing import Any, Callable, Dict, Tuple

from ai_assistant_ui.qwen_chat.contracts import build_audit_envelope, build_known_unsupported_scope_decision_input
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import execute_compiled_fresh_query_message
from ai_assistant_ui.qwen_chat.knowledge_boundary import render_knowledge_boundary_answer


def handle_runtime_gate_turn(
	*,
	session_doc,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	raw_message: str,
	latest_grounded_turn_available: bool,
	latest_grounded_turn: Dict[str, Any],
	followup_resolution,
	execution_path,
	interaction_contract,
	frontdoor_contract,
	clarification_response_contract,
	scope_decision_contract,
	compiled_rollout: Dict[str, Any],
	append_tool_payload: Callable[..., None],
	append_message: Callable[..., None],
	append_knowledge_boundary_contract: Callable[..., Dict[str, Any]],
	append_knowledge_boundary_observability: Callable[..., None],
	append_compiled_attempt_artifacts: Callable[..., None],
	compiled_rollout_fallback_eligible: Callable[[Dict[str, Any]], bool],
	compiled_rollout_fallback_reason: Callable[[Dict[str, Any]], str],
	compiled_rollout_fallback_payload: Callable[..., Dict[str, Any]],
	handle_compiled_first_turn_result: Callable[..., Tuple[bool, Dict[str, Any]]],
	out_of_scope_answer: Callable[[str, Dict[str, Any] | Any], str],
	assistant_text_payload: Callable[[str], str],
	save_session: Callable[..., None],
) -> Tuple[bool, Dict[str, Any] | None, Dict[str, Any] | None]:
	compiled_rollout_fallback: Dict[str, Any] | None = None
	if (
		bool(compiled_rollout.get("enabled"))
		and (
			(
				followup_resolution.mode == "new_query"
				and bool(followup_resolution.self_contained)
			)
			or followup_resolution.mode == "capability_requery"
		)
	):
		governed_target_limit = int(max(0, getattr(followup_resolution, "target_limit", 0) or 0))
		compiled_result = execute_compiled_fresh_query_message(
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=[],
			clarification_resolution=clarification_response_contract.to_payload() if clarification_response_contract is not None else None,
			governed_target_limit=governed_target_limit,
		)
		if compiled_rollout_fallback_eligible(compiled_result):
			reason = compiled_rollout_fallback_reason(compiled_result)
			append_compiled_attempt_artifacts(session_doc, compiled_result)
			compiled_rollout_fallback = compiled_rollout_fallback_payload(
				request_id=request_id,
				result=compiled_result,
				reason=reason,
			)
			append_tool_payload(session_doc, compiled_rollout_fallback)
		else:
			_, payload = handle_compiled_first_turn_result(
				session_doc=session_doc,
				request_id=request_id,
				interaction_contract=interaction_contract,
				followup_resolution=followup_resolution,
				execution_path=execution_path,
				governed_scope_contract=scope_decision_contract,
				front_door_contract=frontdoor_contract,
				clarification_response_contract=clarification_response_contract,
				result=compiled_result,
			)
			return True, payload, None

	known_unsupported_decision = build_known_unsupported_scope_decision_input(raw_message=raw_message)
	governed_scope_status = str(getattr(scope_decision_contract, "governed_scope_status", "") or "").strip()
	unsupported_scope_source = known_unsupported_decision
	if governed_scope_status == "out_of_scope_but_valid_erp_domain":
		unsupported_scope_source = scope_decision_contract or known_unsupported_decision
	if unsupported_scope_source and (
		governed_scope_status == "out_of_scope_but_valid_erp_domain"
		or followup_resolution.mode in {"new_query", "capability_requery"}
	):
		boundary_started_at = time.perf_counter()
		legacy_out_of_scope_answer = out_of_scope_answer(raw_message, unsupported_scope_source)
		requested_domains = list(getattr(unsupported_scope_source, "requested_domains", []) or [])
		context_domains = list(getattr(unsupported_scope_source, "context_domains", []) or [])
		primary_domain = str(getattr(unsupported_scope_source, "primary_domain", "") or "").strip()
		reason = str(getattr(unsupported_scope_source, "reason", "") or "").strip()
		unsupported_scope_status = (
			"out_of_scope_but_valid_erp_domain"
			if governed_scope_status == "out_of_scope_but_valid_erp_domain" or requested_domains
			else "unsupported_request"
		)
		unsupported_scope_payload = {
			"governed_scope_status": unsupported_scope_status,
			"out_of_scope": True,
			"reason": reason,
			"requested_domains": requested_domains,
			"context_domains": context_domains,
			"primary_domain": primary_domain,
		}
		boundary_payload = append_knowledge_boundary_contract(
			session_doc,
			request_id=request_id,
			session_id=session_id,
			proposed_lane="artifact_lane",
			front_door_contract=frontdoor_contract.to_payload(),
			governed_scope_contract=unsupported_scope_payload,
			grounded_turn=latest_grounded_turn if latest_grounded_turn_available else {},
		)
		answer_text = render_knowledge_boundary_answer(
			boundary_contract=boundary_payload,
			detail_answer=legacy_out_of_scope_answer,
		)
		append_knowledge_boundary_observability(
			session_doc,
			request_id=request_id,
			session_id=session_id,
			boundary_payload=boundary_payload,
			latency_ms=int(max(0, round((time.perf_counter() - boundary_started_at) * 1000))),
		)
		append_message(session_doc, "assistant", assistant_text_payload(answer_text))
		append_tool_payload(
			session_doc,
			build_audit_envelope(
				interaction_contract=interaction_contract,
				followup_resolution=followup_resolution,
				execution_path=execution_path,
				runtime_trace_payload={},
				grounded_turn_context={},
				answer_text=answer_text,
			).to_payload(),
		)
		save_session(session_doc, ignore_permissions=False)
		payload: Dict[str, Any] = {
			"ok": True,
			"request_id": request_id,
			"mode": "known_unsupported_erp_domain",
			"agent_meta": {"engine": "local_governed_scope_guard"},
		}
		if isinstance(compiled_rollout_fallback, dict):
			payload["compiled_rollout_fallback_reason"] = str(compiled_rollout_fallback.get("reason") or "").strip()
		return True, payload, compiled_rollout_fallback

	return False, None, compiled_rollout_fallback
