from __future__ import annotations

import time
from typing import Any, Callable, Dict, Tuple

from ai_assistant_ui.qwen_chat.authorized_emission import (
	ANSWER_TYPE_ERROR,
	ANSWER_TYPE_GOVERNED_REPORT,
	ANSWER_TYPE_POLICY_BOUNDARY,
	emit_authorized_assistant_answer,
)
from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_audit_envelope,
	build_followup_resolution_contract,
	build_grounded_turn_context,
	build_interaction_contract,
)
from ai_assistant_ui.qwen_chat.runtime_client import QwenRuntimeClientError, call_qwen_runtime_chat
from ai_assistant_ui.qwen_chat.runtime_metadata_contract import (
	LANE_CLASS_DETERMINISTIC_REPORT,
	LANE_CLASS_ERROR_FALLBACK,
	LANE_CLASS_POLICY_BOUNDARY,
	ROLE_DETERMINISTIC,
	ROLE_NOT_APPLICABLE,
	ROLE_POLICY_BOUNDARY,
	build_runtime_metadata_envelope,
)


def _legacy_runtime_family_tool_surface_allowed(
	compiled_rollout_fallback: Dict[str, Any] | None,
) -> bool:
	return False


def _legacy_runtime_error_control_authority(*, error: str, mode: str) -> Dict[str, Any]:
	return {
		"authority_source": "error_fallback",
		"answer_mode": mode,
		"reason": str(error or "Legacy runtime client failed before governed answer authority was available.").strip(),
		"preflight_status": "passed",
	}


def _legacy_runtime_metadata_envelope(
	*,
	answer_type: str,
	mode: str,
	error: str = "",
) -> Dict[str, Any]:
	if answer_type == ANSWER_TYPE_POLICY_BOUNDARY:
		return build_runtime_metadata_envelope(
			lane_id="legacy_runtime_business_or_boundary_answer",
			lane_class=LANE_CLASS_POLICY_BOUNDARY,
			model_role=ROLE_POLICY_BOUNDARY,
			model_name="none",
			fallback_used=False,
			fallback_reason="",
			role_compliance="compliant",
			authority_source="policy_boundary",
			evidence_scope="knowledge_boundary_contract",
			answer_mode=mode,
			preflight_status="bounded",
			metadata_source="legacy_runtime_authorized_emission",
		)
	if answer_type == ANSWER_TYPE_ERROR:
		return build_runtime_metadata_envelope(
			lane_id="legacy_runtime_business_or_boundary_answer",
			lane_class=LANE_CLASS_ERROR_FALLBACK,
			model_role=ROLE_NOT_APPLICABLE,
			model_name="none",
			fallback_used=False,
			fallback_reason=str(error or "").strip(),
			role_compliance="not_applicable",
			authority_source="error_fallback",
			evidence_scope="legacy_runtime_client_error",
			answer_mode=mode,
			preflight_status="passed",
			metadata_source="legacy_runtime_authorized_emission",
		)
	return build_runtime_metadata_envelope(
		lane_id="legacy_runtime_business_or_boundary_answer",
		lane_class=LANE_CLASS_DETERMINISTIC_REPORT,
		model_role=ROLE_DETERMINISTIC,
		model_name="none",
		fallback_used=False,
		fallback_reason="",
		role_compliance="compliant",
		authority_source="governed_erp_report",
		evidence_scope="legacy_runtime_grounded_turn_context",
		answer_mode=mode,
		preflight_status="passed",
		metadata_source="legacy_runtime_authorized_emission",
	)


def _legacy_runtime_boundary_payload() -> Dict[str, Any]:
	return {
		"type": "qwen_knowledge_boundary_contract",
		"final_lane": "legacy_runtime_grounded_validation_boundary",
		"proposed_lane": "legacy_runtime",
		"knowledge_coverage_state": "grounded_validation_failed",
		"user_response_mode": "safe_refusal",
		"allowed_to_answer": False,
		"safe_next_action": "show_current_facts_or_require_approved_policy",
		"boundary_status": "blocked",
	}


def _legacy_interaction_contract_for_authority(
	interaction_contract,
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
):
	if all(hasattr(interaction_contract, field) for field in ("request_id", "session_id", "user_id", "site_name")):
		return interaction_contract
	return build_interaction_contract(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		raw_message=message,
	)


def _legacy_followup_resolution_for_authority(followup_resolution, *, request_id: str):
	if all(hasattr(followup_resolution, field) for field in ("mode", "depends_on_grounded_turn")):
		return followup_resolution
	return build_followup_resolution_contract(
		request_id=request_id,
		mode="legacy_runtime",
		depends_on_grounded_turn=True,
		self_contained=False,
		latest_grounded_turn_available=False,
		reason="Legacy runtime fallback authority adapter.",
	)


def _legacy_execution_path_for_authority(execution_path, *, request_id: str):
	if all(hasattr(execution_path, field) for field in ("path", "requires_runtime", "grounded_required")):
		return execution_path
	return ExecutionPath(
		request_id=request_id,
		path="legacy_runtime",
		reason="Legacy runtime fallback authority adapter.",
		requires_runtime=True,
		grounded_required=True,
	)


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
	assistant_text_payload: Callable[[str], Any],
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
	authority_interaction_contract = _legacy_interaction_contract_for_authority(
		interaction_contract,
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
	)
	authority_followup_resolution = _legacy_followup_resolution_for_authority(
		followup_resolution,
		request_id=request_id,
	)
	authority_execution_path = _legacy_execution_path_for_authority(
		execution_path,
		request_id=request_id,
	)
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
		runtime_metadata_envelope = _legacy_runtime_metadata_envelope(
			answer_type=ANSWER_TYPE_ERROR,
			mode="legacy_runtime_error",
			error=str(exc),
		)
		trace_payload = tool_trace_payload(
			request_id=request_id,
			ok=False,
			tool_trace=[],
			agent_meta={
				"engine": "unavailable",
				"mode": "read_only",
				"runtime_metadata_envelope": runtime_metadata_envelope,
			},
			error=str(exc),
			runtime_latency_ms=runtime_latency_ms,
		)
		trace_payload["runtime_metadata_envelope"] = runtime_metadata_envelope
		append_tool_payload(session_doc, trace_payload)
		authorized_emission = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text=error_text,
			answer_type=ANSWER_TYPE_ERROR,
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			assistant_text_payload=assistant_text_payload,
			control_meta_authority=_legacy_runtime_error_control_authority(
				error=str(exc),
				mode="legacy_runtime_error",
			),
			runtime_trace_payload=trace_payload,
			pre_assistant_tool_payloads=[runtime_metadata_envelope],
		)
		save_session(session_doc, ignore_permissions=False)
		payload: Dict[str, Any] = {
			"ok": False,
			"request_id": request_id,
			"error": str(exc),
			"agent_meta": {
				"runtime_metadata_envelope": runtime_metadata_envelope,
				"authorized_emission": authorized_emission.to_payload(),
			},
		}
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
			"I can't answer that safely from the current ERP evidence. "
			"The available data supports facts and bounded explanation, but not this prediction or conclusion yet. "
			"Please ask for the current facts, aging details, or an approved prediction policy first."
		)
		agent_meta = {
			**agent_meta,
			"engine": "local_grounded_boundary",
			"status": "grounded_validation_failed",
		}
	elif not answer_text:
		answer_text = "Qwen runtime could not complete the request right now. Please try again."

	runtime_trace_payload = tool_trace_payload(
		request_id=request_id,
		ok=ok,
		tool_trace=tool_trace,
		agent_meta=agent_meta,
		error=error,
		runtime_latency_ms=runtime_latency_ms,
	)
	pre_assistant_tool_payloads = [runtime_trace_payload]
	assistant_payload = assistant_text_payload(answer_text)
	if not isinstance(assistant_payload, dict):
		assistant_payload = {"text": str(answer_text or "")}
	artifact_payload = latest_normalized_family_artifact(session_doc)
	grounded_turn_context = build_grounded_turn_context(
		request_id=request_id,
		interaction_contract=authority_interaction_contract,
		assistant_payload=assistant_payload,
		runtime_payload={
			**runtime_trace_payload,
			"request_id": request_id,
		},
		artifact_payload=artifact_payload,
	)
	grounded_turn_payload: Dict[str, Any] = {}
	if grounded_turn_context and grounded_turn_context.grounded:
		grounded_turn_payload = grounded_turn_context.to_payload()
		pre_assistant_tool_payloads.append(grounded_turn_payload)
	answer_type = ANSWER_TYPE_POLICY_BOUNDARY if grounded_validation_failed else ANSWER_TYPE_GOVERNED_REPORT
	boundary_payload = _legacy_runtime_boundary_payload() if grounded_validation_failed else {}
	answer_mode = "grounded_evidence_boundary" if grounded_validation_failed else "legacy_runtime"
	runtime_metadata_envelope = _legacy_runtime_metadata_envelope(
		answer_type=answer_type,
		mode=answer_mode,
		error=error,
	)
	runtime_trace_payload["runtime_metadata_envelope"] = runtime_metadata_envelope
	runtime_trace_agent_meta = (
		runtime_trace_payload.get("agent_meta") if isinstance(runtime_trace_payload.get("agent_meta"), dict) else {}
	)
	runtime_trace_payload["agent_meta"] = {
		**runtime_trace_agent_meta,
		"runtime_metadata_envelope": runtime_metadata_envelope,
	}
	pre_assistant_tool_payloads.append(runtime_metadata_envelope)
	authorized_emission = emit_authorized_assistant_answer(
		session_doc=session_doc,
		answer_text=answer_text,
		answer_type=answer_type,
		append_message=append_message,
		append_tool_payload=append_tool_payload,
		assistant_text_payload=assistant_text_payload,
		interaction_contract=authority_interaction_contract,
		followup_resolution=authority_followup_resolution,
		execution_path=authority_execution_path,
		runtime_trace_payload=runtime_trace_payload,
		grounded_turn_context={} if grounded_validation_failed else grounded_turn_payload,
		authority_context=(
			{"knowledge_boundary": boundary_payload}
			if grounded_validation_failed
			else {"normalized_family_artifact": artifact_payload}
		),
		pre_assistant_tool_payloads=pre_assistant_tool_payloads,
	)
	save_session(session_doc, ignore_permissions=False)
	payload = {
		"ok": bool(authorized_emission.emitted) and (True if grounded_validation_failed else ok),
		"request_id": request_id,
		"error": error,
		"agent_meta": {
			**agent_meta,
			"runtime_metadata_envelope": runtime_metadata_envelope,
			"authorized_emission": authorized_emission.to_payload(),
		},
	}
	if isinstance(compiled_rollout_fallback, dict):
		payload["mode"] = "legacy_runtime_rollout_fallback"
		payload["compiled_rollout_fallback_reason"] = str(compiled_rollout_fallback.get("reason") or "").strip()
	elif grounded_validation_failed:
		payload["mode"] = "grounded_evidence_boundary"
	else:
		payload["mode"] = "legacy_runtime"
	return True, payload
