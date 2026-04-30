from __future__ import annotations

import time
from typing import Any, Callable, Dict, Tuple

from ai_assistant_ui.qwen_chat.contracts import build_audit_envelope, build_grounded_turn_context
from ai_assistant_ui.qwen_chat.runtime_client import QwenRuntimeClientError, call_qwen_runtime_chat


def _legacy_runtime_family_tool_surface_allowed(
	compiled_rollout_fallback: Dict[str, Any] | None,
) -> bool:
	return False


def handle_legacy_runtime_turn(
	*,
	session_doc,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	recent_messages,
	response_policy_contract,
	interaction_contract,
	followup_resolution,
	execution_path,
	compiled_rollout_fallback: Dict[str, Any] | None,
	append_message: Callable[..., None],
	append_tool_payload: Callable[..., None],
	assistant_text_payload: Callable[[str], str],
	save_session: Callable[..., None],
	tool_trace_payload: Callable[..., Dict[str, Any]],
	tool_trace_message: Callable[..., str],
	safe_runtime_failure_message: Callable[[Exception], str],
	latest_qwen_trace_payload: Callable[..., Dict[str, Any]],
	latest_assistant_payload: Callable[..., Dict[str, Any]],
	latest_normalized_family_artifact: Callable[..., Dict[str, Any]],
) -> Tuple[bool, Dict[str, Any]]:
	start = time.perf_counter()
	family_tool_context_payload = {}
	try:
		runtime_payload = call_qwen_runtime_chat(
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=recent_messages,
			response_policy=response_policy_contract.to_runtime_payload(),
			family_tool_context=family_tool_context_payload,
			mode="read_only",
			request_id=request_id,
		)
		runtime_latency_ms = int((time.perf_counter() - start) * 1000)
	except QwenRuntimeClientError as exc:
		runtime_latency_ms = int((time.perf_counter() - start) * 1000)
		error_text = safe_runtime_failure_message(exc)
		trace_payload = tool_trace_payload(
			request_id=request_id,
			ok=False,
			tool_trace=[],
			agent_meta={"engine": "unavailable", "mode": "read_only"},
			error=str(exc),
			runtime_latency_ms=runtime_latency_ms,
		)
		append_message(session_doc, "assistant", assistant_text_payload(error_text))
		append_tool_payload(session_doc, trace_payload)
		append_tool_payload(
			session_doc,
			build_audit_envelope(
				interaction_contract=interaction_contract,
				followup_resolution=followup_resolution,
				execution_path=execution_path,
				runtime_trace_payload=trace_payload,
				grounded_turn_context={},
				answer_text=error_text,
			).to_payload(),
		)
		save_session(session_doc, ignore_permissions=False)
		payload: Dict[str, Any] = {"ok": False, "request_id": request_id, "error": str(exc)}
		if isinstance(compiled_rollout_fallback, dict):
			payload["mode"] = "legacy_runtime_rollout_fallback"
			payload["compiled_rollout_fallback_reason"] = str(compiled_rollout_fallback.get("reason") or "").strip()
		else:
			payload["mode"] = "legacy_runtime"
		return True, payload

	ok = bool(runtime_payload.get("ok"))
	answer_text = str(runtime_payload.get("answer_text") or "").strip()
	tool_trace = runtime_payload.get("tool_trace") if isinstance(runtime_payload.get("tool_trace"), list) else []
	agent_meta = runtime_payload.get("agent_meta") if isinstance(runtime_payload.get("agent_meta"), dict) else {}
	error = str(runtime_payload.get("error") or "").strip()
	grounded_validation_failed = (
		not ok
		and error == "Grounded read validation failed."
		and str(((agent_meta.get("validation") or {}).get("status") if isinstance(agent_meta.get("validation"), dict) else "") or "").strip() == "fail"
	)

	if grounded_validation_failed:
		answer_text = (
			"I can't answer that safely from the current governed ERP evidence. "
			"The runtime did not produce a grounded tool-backed answer, so I stopped rather than guess."
		)
		agent_meta = {
			**agent_meta,
			"engine": "local_grounded_boundary",
			"status": "grounded_validation_failed",
		}
	elif not answer_text:
		answer_text = "Qwen runtime could not complete the request right now. Please try again."

	append_message(session_doc, "assistant", assistant_text_payload(answer_text))
	append_message(
		session_doc,
		"tool",
		tool_trace_message(
			request_id=request_id,
			ok=ok,
			tool_trace=tool_trace,
			agent_meta=agent_meta,
			error=error,
			runtime_latency_ms=runtime_latency_ms,
		),
	)
	runtime_trace_payload = latest_qwen_trace_payload(session_doc)
	assistant_payload = latest_assistant_payload(session_doc)
	grounded_turn_context = build_grounded_turn_context(
		request_id=request_id,
		interaction_contract=interaction_contract,
		assistant_payload=assistant_payload,
		runtime_payload={
			**runtime_trace_payload,
			"request_id": request_id,
		},
		artifact_payload=latest_normalized_family_artifact(session_doc),
	)
	grounded_turn_payload: Dict[str, Any] = {}
	if grounded_turn_context and grounded_turn_context.grounded:
		grounded_turn_payload = grounded_turn_context.to_payload()
		append_tool_payload(session_doc, grounded_turn_payload)
	append_tool_payload(
		session_doc,
		build_audit_envelope(
			interaction_contract=interaction_contract,
			followup_resolution=followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload=runtime_trace_payload,
			grounded_turn_context=grounded_turn_payload,
			answer_text=answer_text,
		).to_payload(),
	)
	save_session(session_doc, ignore_permissions=False)
	payload = {
		"ok": True if grounded_validation_failed else ok,
		"request_id": request_id,
		"error": error,
		"agent_meta": agent_meta,
	}
	if isinstance(compiled_rollout_fallback, dict):
		payload["mode"] = "legacy_runtime_rollout_fallback"
		payload["compiled_rollout_fallback_reason"] = str(compiled_rollout_fallback.get("reason") or "").strip()
	elif grounded_validation_failed:
		payload["mode"] = "grounded_evidence_boundary"
	else:
		payload["mode"] = "legacy_runtime"
	return True, payload
