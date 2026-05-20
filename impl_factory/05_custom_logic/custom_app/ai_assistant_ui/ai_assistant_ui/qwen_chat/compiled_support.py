from __future__ import annotations

import datetime as dt
import json
import time
from typing import Any, Callable, Dict, List, Tuple

from ai_assistant_ui.qwen_chat.authorized_emission import (
	ANSWER_TYPE_CONTROL,
	ANSWER_TYPE_ERROR,
	ANSWER_TYPE_GOVERNED_REPORT,
	ANSWER_TYPE_POLICY_BOUNDARY,
	emit_authorized_assistant_answer,
)
from ai_assistant_ui.qwen_chat.clarification_translation import render_clarification_signal_user_text
from ai_assistant_ui.qwen_chat.compound_request_support import (
	build_post_result_multi_step_assessment_payload,
	build_multi_step_step_result_integration_payload,
)
from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_clarification_reason_contract_from_sources,
)
from ai_assistant_ui.qwen_chat.master_data_family_support import is_master_data_listing_family
from ai_assistant_ui.qwen_chat.runtime_metadata_contract import (
	LANE_CLASS_CONTROL_META,
	LANE_CLASS_DETERMINISTIC_REPORT,
	LANE_CLASS_ERROR_FALLBACK,
	LANE_CLASS_POLICY_BOUNDARY,
	ROLE_CONTROL_META,
	ROLE_DETERMINISTIC,
	ROLE_NOT_APPLICABLE,
	ROLE_POLICY_BOUNDARY,
	build_runtime_metadata_envelope,
)


def compiled_clarification_reason_contract(*, request_id: str, result: Dict[str, Any]):
	pipeline = result.get("pipeline") if isinstance(result.get("pipeline"), dict) else {}
	compiler = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
	family_validation = result.get("family_validation") if isinstance(result.get("family_validation"), dict) else {}
	semantic = result.get("semantic_intent_validation") if isinstance(result.get("semantic_intent_validation"), dict) else {}
	return build_clarification_reason_contract_from_sources(
		request_id=request_id,
		compiler_reason=str(compiler.get("compiler_reason") or "").strip(),
		compiler_reason_type=str(compiler.get("clarification_reason_type") or "").strip(),
		compiler_details=compiler.get("clarification_details") if isinstance(compiler.get("clarification_details"), dict) else {},
		family_validation=family_validation,
		semantic_validation=semantic,
	)


def _compiled_payload_dict(value: Any) -> Dict[str, Any]:
	if isinstance(value, dict):
		return dict(value)
	if isinstance(value, str):
		try:
			loaded = json.loads(value)
		except Exception:
			return {}
		return dict(loaded) if isinstance(loaded, dict) else {}
	return {}


def _compiled_attempt_artifact_payloads(result: Dict[str, Any]) -> List[Dict[str, Any]]:
	pipeline = result.get("pipeline") if isinstance(result.get("pipeline"), dict) else {}
	normalized_family_artifact = result.get("normalized_family_artifact") if isinstance(result.get("normalized_family_artifact"), dict) else {}
	rendered_response = result.get("rendered_response") if isinstance(result.get("rendered_response"), dict) else {}
	narrative_response = result.get("narrative_response") if isinstance(result.get("narrative_response"), dict) else {}
	composite_family_artifacts = result.get("composite_family_artifacts") if isinstance(result.get("composite_family_artifacts"), list) else []
	composite_step_validations = result.get("composite_step_validations") if isinstance(result.get("composite_step_validations"), list) else []
	composite_validation = result.get("composite_validation") if isinstance(result.get("composite_validation"), dict) else {}
	family_validation = result.get("family_validation") if isinstance(result.get("family_validation"), dict) else {}
	semantic_payload = result.get("semantic_intent_validation") if isinstance(result.get("semantic_intent_validation"), dict) else {}
	compiled_audit = result.get("compiled_execution_audit") if isinstance(result.get("compiled_execution_audit"), dict) else {}
	composite_execution_audit = result.get("composite_execution_audit") if isinstance(result.get("composite_execution_audit"), dict) else {}
	payloads: List[Dict[str, Any]] = []
	for key in ("fresh_query_interpretation", "fresh_query_compiler", "compiled_query_request", "composite_read_plan"):
		payload = pipeline.get(key)
		if isinstance(payload, dict) and payload:
			payloads.append(payload)
	if normalized_family_artifact:
		payloads.append(normalized_family_artifact)
	if rendered_response:
		payloads.append(rendered_response)
	if narrative_response:
		payloads.append(narrative_response)
	for payload in composite_family_artifacts:
		if isinstance(payload, dict) and payload:
			payloads.append(payload)
	for payload in composite_step_validations:
		if isinstance(payload, dict) and payload:
			payloads.append(payload)
	if composite_validation:
		payloads.append(composite_validation)
	if family_validation and str(family_validation.get("type") or "").strip():
		payloads.append(family_validation)
	if semantic_payload:
		payloads.append(semantic_payload)
	if compiled_audit:
		payloads.append(compiled_audit)
	if composite_execution_audit:
		payloads.append(composite_execution_audit)
	return payloads


def append_compiled_attempt_artifacts(
	session_doc,
	result: Dict[str, Any],
	*,
	append_tool_payload: Callable[..., None],
) -> None:
	for payload in _compiled_attempt_artifact_payloads(result):
		append_tool_payload(session_doc, payload)


def compiled_rollout_fallback_reason(result: Dict[str, Any]) -> str:
	pipeline = result.get("pipeline") if isinstance(result.get("pipeline"), dict) else {}
	interpretation = (
		pipeline.get("fresh_query_interpretation")
		if isinstance(pipeline.get("fresh_query_interpretation"), dict)
		else {}
	)
	status = str(interpretation.get("status") or "").strip()
	if status == "runtime_error":
		return "proposal_runtime_error"
	if status == "invalid_response":
		return "proposal_invalid_response"
	if status == "low_confidence":
		return "proposal_low_confidence"
	if status == "validation_error":
		return "proposal_validation_error"
	if status == "rejected":
		return "proposal_rejected"
	return ""


def compiled_rollout_fallback_payload(*, request_id: str, result: Dict[str, Any], reason: str) -> Dict[str, Any]:
	pipeline = result.get("pipeline") if isinstance(result.get("pipeline"), dict) else {}
	compiler = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
	interpretation_payload = (
		pipeline.get("fresh_query_interpretation")
		if isinstance(pipeline.get("fresh_query_interpretation"), dict)
		else {}
	)
	interpretation_contract = (
		interpretation_payload.get("interpretation")
		if isinstance(interpretation_payload.get("interpretation"), dict)
		else {}
	)
	compiled_audit = result.get("compiled_execution_audit") if isinstance(result.get("compiled_execution_audit"), dict) else {}
	return {
		"type": "qwen_compiled_rollout_fallback",
		"request_id": str(request_id or "").strip(),
		"reason": str(reason or "").strip(),
		"interpretation_intent_class": str(interpretation_contract.get("intent_class") or "").strip(),
		"compiler_decision": str(compiler.get("decision") or "").strip(),
		"compiler_reason": str(compiler.get("compiler_reason") or "").strip(),
		"semantic_validation_status": str(
			(
				result.get("semantic_intent_validation")
				if isinstance(result.get("semantic_intent_validation"), dict)
				else {}
			).get("status")
			or ""
		).strip(),
		"compiled_audit_request_id": str(compiled_audit.get("request_id") or "").strip(),
		"created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
	}


def compiled_rollout_fallback_eligible(result: Dict[str, Any]) -> bool:
	reason = compiled_rollout_fallback_reason(result)
	if not reason:
		return False
	pipeline = result.get("pipeline") if isinstance(result.get("pipeline"), dict) else {}
	compiler = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
	decision = str(compiler.get("decision") or "").strip()
	semantic_payload = result.get("semantic_intent_validation") if isinstance(result.get("semantic_intent_validation"), dict) else {}
	semantic_status = str(semantic_payload.get("status") or "").strip()
	if semantic_status == "pass":
		return False
	return decision not in {"clarify", "reject"} and semantic_status not in {"clarify", "reject_semantically_inconsistent"}


def _prefer_rendered_family_answer(family_id: str) -> bool:
	clean_family_id = str(family_id or "").strip()
	return clean_family_id == "transaction_listing" or is_master_data_listing_family(clean_family_id)


def compiled_decision_message(
	*,
	request_id: str,
	raw_message: str,
	result: Dict[str, Any],
	build_known_unsupported_scope_decision_input,
	translate_clarification_signal,
	out_of_scope_answer,
	is_generic_compiled_failure_answer,
	safe_runtime_failure_message,
) -> Tuple[str, Dict[str, Any]]:
	pipeline = result.get("pipeline") if isinstance(result.get("pipeline"), dict) else {}
	compiler = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
	decision = str(compiler.get("decision") or "").strip()
	reason = str(compiler.get("compiler_reason") or "").strip()
	reason_type = str(compiler.get("clarification_reason_type") or "").strip()
	reason_details = compiler.get("clarification_details") if isinstance(compiler.get("clarification_details"), dict) else {}
	rendered_response = result.get("rendered_response") if isinstance(result.get("rendered_response"), dict) else {}
	narrative_response = result.get("narrative_response") if isinstance(result.get("narrative_response"), dict) else {}
	family_validation = result.get("family_validation") if isinstance(result.get("family_validation"), dict) else {}
	family_status = str(family_validation.get("status") or "").strip()
	family_errors = family_validation.get("errors") if isinstance(family_validation.get("errors"), list) else []
	semantic = result.get("semantic_intent_validation") if isinstance(result.get("semantic_intent_validation"), dict) else {}
	semantic_status = str(semantic.get("status") or "").strip()
	semantic_errors = semantic.get("errors") if isinstance(semantic.get("errors"), list) else []
	runtime_payload = result.get("runtime_payload") if isinstance(result.get("runtime_payload"), dict) else {}
	runtime_error = str(runtime_payload.get("error") or "").strip()
	runtime_answer = str(runtime_payload.get("answer_text") or "").strip()
	unsupported_decision = build_known_unsupported_scope_decision_input(raw_message=raw_message)

	if decision == "clarify":
		signal = translate_clarification_signal(
			request_id=request_id,
			raw_message=raw_message,
			compiler_reason=reason,
			compiler_reason_type=reason_type,
			compiler_details=reason_details,
		)
		payload = signal.to_payload()
		return render_clarification_signal_user_text(payload), payload
	if decision == "reject":
		if unsupported_decision:
			return out_of_scope_answer(raw_message, unsupported_decision), {}
		if reason:
			return f"I can't complete that safely within the approved ERP read path yet.\n\n{reason}", {}
		return "I can't complete that safely within the approved ERP read path yet.", {}
	if family_status == "clarify":
		signal = translate_clarification_signal(
			request_id=request_id,
			raw_message=raw_message,
			family_validation=family_validation,
		)
		payload = signal.to_payload()
		return render_clarification_signal_user_text(payload), payload
	if family_status.startswith("reject"):
		if unsupported_decision:
			return out_of_scope_answer(raw_message, unsupported_decision), {}
		detail = str((family_errors or ["The normalized business artifact did not pass governed validation."])[0] or "").strip()
		return f"I couldn't complete that result confidently from governed ERP data.\n\n{detail}".strip(), {}
	if semantic_status == "clarify":
		signal = translate_clarification_signal(
			request_id=request_id,
			raw_message=raw_message,
			semantic_validation=semantic,
		)
		payload = signal.to_payload()
		return render_clarification_signal_user_text(payload), payload
	if semantic_status == "reject_semantically_inconsistent":
		if unsupported_decision:
			return out_of_scope_answer(raw_message, unsupported_decision), {}
		detail = str((semantic_errors or ["The grounded result did not match the requested business intent."])[0] or "").strip()
		return f"I couldn't complete a grounded answer that matched the requested business intent.\n\n{detail}".strip(), {}
	normalized_family_artifact = result.get("normalized_family_artifact") if isinstance(result.get("normalized_family_artifact"), dict) else {}
	family_id = str(
		rendered_response.get("family_id")
		or narrative_response.get("family_id")
		or normalized_family_artifact.get("family_id")
		or ""
	).strip()
	narrative_answer = str(narrative_response.get("answer_text") or "").strip()
	rendered_answer = str(rendered_response.get("answer_text") or "").strip()
	if _prefer_rendered_family_answer(family_id):
		if rendered_answer:
			return rendered_answer, {}
		if narrative_answer:
			return narrative_answer, {}
	else:
		if narrative_answer:
			return narrative_answer, {}
		if rendered_answer:
			return rendered_answer, {}
	if unsupported_decision and is_generic_compiled_failure_answer(runtime_answer):
		return out_of_scope_answer(raw_message, unsupported_decision), {}
	if runtime_answer:
		return runtime_answer, {}
	if runtime_error:
		if unsupported_decision:
			return out_of_scope_answer(raw_message, unsupported_decision), {}
		return safe_runtime_failure_message(RuntimeError(runtime_error)), {}
	if unsupported_decision:
		return out_of_scope_answer(raw_message, unsupported_decision), {}
	return "I could not complete a governed ERP lookup.", {}


def _frontdoor_compound_request_assessment_payload(front_door_contract: Any) -> Dict[str, Any]:
	if front_door_contract is None:
		return {}
	response_payload = getattr(front_door_contract, "response_payload", {})
	if not isinstance(response_payload, dict):
		return {}
	payload = response_payload.get("compound_request_assessment")
	return dict(payload) if isinstance(payload, dict) else {}


def _compound_request_internal_details(payload: Dict[str, Any]) -> Dict[str, Any]:
	internal_details = payload.get("internal_details")
	return dict(internal_details) if isinstance(internal_details, dict) else {}


def _compound_request_payload_has_ordered_execution(payload: Dict[str, Any]) -> bool:
	if str(payload.get("type") or "").strip() != "qwen_compound_request_assessment_contract":
		return False
	internal_details = _compound_request_internal_details(payload)
	if str(internal_details.get("execution_strategy") or "").strip() != "ordered_multi_step":
		return False
	return bool(str(internal_details.get("primary_segment_message") or "").strip())


def _compound_request_next_step_note(payload: Dict[str, Any]) -> str:
	if not _compound_request_payload_has_ordered_execution(payload):
		return ""
	internal_details = _compound_request_internal_details(payload)
	remaining_labels = [
		str(value or "").strip()
		for value in (internal_details.get("remaining_segment_labels") or [])
		if str(value or "").strip()
	]
	if not remaining_labels:
		return ""
	return f'If you\'d like, I can show {remaining_labels[0]} next. Just say "continue".'


def _compiled_clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _compiled_text(value: Any) -> str:
	return str(value or "").strip()


def _compiled_assistant_payload(answer_text: str, assistant_text_payload: Callable[[str], Any]) -> Dict[str, Any]:
	try:
		payload_value = assistant_text_payload(answer_text)
	except Exception:
		payload_value = ""
	if isinstance(payload_value, dict):
		return dict(payload_value)
	try:
		parsed = json.loads(str(payload_value or ""))
	except Exception:
		parsed = {}
	if isinstance(parsed, dict) and parsed:
		return parsed
	return {"type": "text", "text": _compiled_text(answer_text)}


def _compiled_boundary_blocks_answer(boundary_payload: Dict[str, Any]) -> bool:
	boundary = _compiled_clean_dict(boundary_payload)
	if not boundary:
		return False
	if bool(boundary.get("allowed_to_answer")):
		return False
	return _compiled_text(boundary.get("safe_next_action")) != "allow_current_lane"


def _compiled_family_validation_passed(family_payload: Dict[str, Any]) -> bool:
	return _compiled_text(family_payload.get("status") or "pass") in {"", "pass", "not_run"}


def _compiled_answer_type(
	*,
	answer_text: str,
	clarification_signal_payload: Dict[str, Any],
	boundary_payload: Dict[str, Any],
	runtime_payload: Dict[str, Any],
	family_payload: Dict[str, Any],
	semantic_payload: Dict[str, Any],
) -> str:
	if clarification_signal_payload:
		return ANSWER_TYPE_CONTROL
	if _compiled_boundary_blocks_answer(boundary_payload):
		return ANSWER_TYPE_POLICY_BOUNDARY
	if _compiled_text(runtime_payload.get("error")) and not bool(runtime_payload.get("ok")):
		return ANSWER_TYPE_ERROR
	if (
		_compiled_text(answer_text)
		and bool(runtime_payload.get("ok"))
		and _compiled_text(semantic_payload.get("status")) == "pass"
		and _compiled_family_validation_passed(family_payload)
	):
		return ANSWER_TYPE_GOVERNED_REPORT
	return ANSWER_TYPE_ERROR


def _compiled_runtime_metadata_envelope(
	*,
	answer_type: str,
	control_meta_authority: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	answer_mode = "compiled_first_turn"
	if answer_type == ANSWER_TYPE_GOVERNED_REPORT:
		return build_runtime_metadata_envelope(
			lane_id="compiled_support_result_answer",
			lane_class=LANE_CLASS_DETERMINISTIC_REPORT,
			model_role=ROLE_DETERMINISTIC,
			model_name="none",
			fallback_used=False,
			fallback_reason="",
			role_compliance="compliant",
			authority_source="governed_erp_report",
			evidence_scope="compiled_grounded_turn_context",
			answer_mode=answer_mode,
			preflight_status="passed",
			metadata_source="compiled_support_authorized_emission",
		)
	if answer_type == ANSWER_TYPE_POLICY_BOUNDARY:
		return build_runtime_metadata_envelope(
			lane_id="compiled_support_result_answer",
			lane_class=LANE_CLASS_POLICY_BOUNDARY,
			model_role=ROLE_POLICY_BOUNDARY,
			model_name="none",
			fallback_used=False,
			fallback_reason="",
			role_compliance="compliant",
			authority_source="policy_boundary",
			evidence_scope="knowledge_boundary_contract",
			answer_mode=answer_mode,
			preflight_status="bounded",
			metadata_source="compiled_support_authorized_emission",
		)
	if answer_type == ANSWER_TYPE_ERROR:
		authority_source = _compiled_text((control_meta_authority or {}).get("authority_source")) or "error_fallback"
		return build_runtime_metadata_envelope(
			lane_id="compiled_support_result_answer",
			lane_class=LANE_CLASS_ERROR_FALLBACK,
			model_role=ROLE_NOT_APPLICABLE,
			model_name="none",
			fallback_used=False,
			fallback_reason=_compiled_text((control_meta_authority or {}).get("reason")),
			role_compliance="not_applicable",
			authority_source=authority_source,
			evidence_scope="compiled_runtime_error_fallback",
			answer_mode=answer_mode,
			preflight_status="passed",
			metadata_source="compiled_support_authorized_emission",
		)
	authority_source = _compiled_text((control_meta_authority or {}).get("authority_source")) or "control_meta"
	return build_runtime_metadata_envelope(
		lane_id="compiled_support_result_answer",
		lane_class=LANE_CLASS_CONTROL_META,
		model_role=ROLE_CONTROL_META,
		model_name="none",
		fallback_used=False,
		fallback_reason="",
		role_compliance="compliant",
		authority_source=authority_source,
		evidence_scope="compiled_control_contract",
		answer_mode=answer_mode,
		preflight_status="passed",
		metadata_source="compiled_support_authorized_emission",
	)


def _compiled_control_meta_authority(
	*,
	answer_type: str,
	clarification_signal_payload: Dict[str, Any],
	runtime_payload: Dict[str, Any],
) -> Dict[str, Any]:
	if answer_type == ANSWER_TYPE_ERROR:
		return {
			"authority_source": "error_fallback",
			"answer_mode": "compiled_first_turn",
			"reason": _compiled_text(runtime_payload.get("error")) or "Compiled runtime fallback answer.",
			"preflight_status": "passed",
		}
	return {
		"authority_source": "control_meta",
		"answer_mode": "compiled_first_turn",
		"reason": (
			"Compiled clarification response."
			if clarification_signal_payload
			else "Compiled non-business control response."
		),
		"preflight_status": "passed",
	}


def _compiled_execution_path_for_authority(
	*,
	execution_path: ExecutionPath,
	answer_type: str,
) -> ExecutionPath:
	if answer_type == ANSWER_TYPE_GOVERNED_REPORT:
		return ExecutionPath(
			request_id=execution_path.request_id,
			path=execution_path.path,
			reason=execution_path.reason,
			requires_runtime=execution_path.requires_runtime,
			grounded_required=True,
		)
	return execution_path


def _compiled_authority_context(
	*,
	answer_type: str,
	boundary_payload: Dict[str, Any],
	result: Dict[str, Any],
	family_payload: Dict[str, Any],
	semantic_payload: Dict[str, Any],
	compiled_audit_payload: Dict[str, Any],
) -> Dict[str, Any]:
	context: Dict[str, Any] = {
		"normalized_family_artifact": result.get("normalized_family_artifact")
		if isinstance(result.get("normalized_family_artifact"), dict)
		else {},
		"family_validation": family_payload,
		"semantic_validation": semantic_payload,
		"compiled_execution_audit": compiled_audit_payload,
	}
	if answer_type == ANSWER_TYPE_POLICY_BOUNDARY and boundary_payload:
		context["knowledge_boundary"] = boundary_payload
	return context


def _compiled_grounded_turn_payload_for_authority(
	*,
	grounded_turn_payload: Dict[str, Any],
	result: Dict[str, Any],
	request_id: str,
) -> Dict[str, Any]:
	payload = _compiled_clean_dict(grounded_turn_payload)
	if not payload or not bool(payload.get("grounded")):
		return payload
	artifact = (
		result.get("normalized_family_artifact")
		if isinstance(result.get("normalized_family_artifact"), dict)
		else {}
	)
	if not _compiled_text(payload.get("source_kind")):
		payload["source_kind"] = "report"
	if not _compiled_text(payload.get("source_name")):
		payload["source_name"] = _compiled_text(
			artifact.get("report_family")
			or artifact.get("family_id")
			or artifact.get("artifact_type")
			or "compiled_family_artifact"
		)
	if not _compiled_text(payload.get("artifact_family_id")):
		payload["artifact_family_id"] = _compiled_text(
			artifact.get("family_id")
			or artifact.get("report_family")
			or payload.get("source_name")
		)
	if not _compiled_text(payload.get("trace_request_id")):
		payload["trace_request_id"] = _compiled_text(
			artifact.get("artifact_id")
			or artifact.get("request_id")
			or request_id
		)
	return payload


def handle_compiled_first_turn_result(
	*,
	session_doc,
	request_id: str,
	interaction_contract,
	followup_resolution,
	execution_path,
	result: Dict[str, Any],
	governed_scope_contract=None,
	front_door_contract=None,
	clarification_response_contract=None,
	pre_result_tool_payloads: List[Dict[str, Any]] | None = None,
	append_compiled_attempt_artifacts,
	compiled_decision_message,
	compiled_clarification_reason_contract,
	append_message,
	append_tool_payload,
	assistant_text_payload,
	tool_trace_message,
	latest_qwen_trace_payload,
	latest_assistant_payload,
	append_knowledge_boundary_contract,
	knowledge_boundary_event_level,
	append_knowledge_boundary_observability,
	build_grounded_turn_context,
	build_audit_envelope,
	save_session,
	store_pending_clarification_signal,
	clear_pending_clarification_signal,
) -> Tuple[bool, Dict[str, Any]]:
	runtime_payload = result.get("runtime_payload") if isinstance(result.get("runtime_payload"), dict) else {}
	family_payload = result.get("family_validation") if isinstance(result.get("family_validation"), dict) else {}
	semantic_payload = result.get("semantic_intent_validation") if isinstance(result.get("semantic_intent_validation"), dict) else {}
	latency = result.get("phase4_latency_breakdown") if isinstance(result.get("phase4_latency_breakdown"), dict) else {}
	runtime_latency_ms = int(max(0, latency.get("runtime_execution_latency_ms") or 0))
	boundary_started_at = time.perf_counter()

	pre_assistant_tool_payloads: List[Dict[str, Any]] = _compiled_attempt_artifact_payloads(result)

	answer_text, clarification_signal_payload = compiled_decision_message(
		request_id=request_id,
		raw_message=str(interaction_contract.raw_message or "").strip(),
		result=result,
	)
	compound_request_assessment_payload = _frontdoor_compound_request_assessment_payload(front_door_contract)
	if answer_text and not clarification_signal_payload:
		next_step_note = _compound_request_next_step_note(compound_request_assessment_payload)
		if next_step_note:
			answer_text = f"{answer_text}\n\n{next_step_note}"
	assistant_payload_for_grounding = _compiled_assistant_payload(answer_text, assistant_text_payload)
	for payload in (pre_result_tool_payloads or []):
		if isinstance(payload, dict) and payload:
			pre_assistant_tool_payloads.append(payload)
	clarification_reason_payload: Dict[str, Any] = {}
	if clarification_signal_payload:
		clarification_reason_contract = compiled_clarification_reason_contract(
			request_id=request_id,
			result=result,
		)
		if clarification_reason_contract is not None:
			clarification_reason_payload = clarification_reason_contract.to_payload()
			pre_assistant_tool_payloads.append(clarification_reason_payload)
		pre_assistant_tool_payloads.append(clarification_signal_payload)
	else:
		clear_pending_clarification_signal(session_doc)

	tool_trace = runtime_payload.get("tool_trace") if isinstance(runtime_payload.get("tool_trace"), list) else []
	agent_meta = runtime_payload.get("agent_meta") if isinstance(runtime_payload.get("agent_meta"), dict) else {}
	error = str(runtime_payload.get("error") or "").strip()
	if tool_trace or runtime_payload:
		pre_assistant_tool_payloads.append(
			_compiled_payload_dict(
				tool_trace_message(
					request_id=request_id,
					ok=bool(runtime_payload.get("ok")),
					tool_trace=tool_trace,
					agent_meta=agent_meta,
					error=error,
					runtime_latency_ms=runtime_latency_ms,
				)
			)
		)
	runtime_trace_payload = (
		pre_assistant_tool_payloads[-1]
		if pre_assistant_tool_payloads and pre_assistant_tool_payloads[-1].get("type")
		else {
			"request_id": request_id,
			"ok": bool(runtime_payload.get("ok")),
			"tool_trace": tool_trace,
			"agent_meta": agent_meta,
			"error": error,
			"runtime_latency_ms": runtime_latency_ms,
		}
	)

	grounded_turn_payload: Dict[str, Any] = {}
	if str(semantic_payload.get("status") or "").strip() == "pass" and bool(runtime_payload.get("ok")):
		grounded_turn_context = build_grounded_turn_context(
			request_id=request_id,
			interaction_contract=interaction_contract,
			assistant_payload=assistant_payload_for_grounding,
			runtime_payload={
				**runtime_trace_payload,
				"request_id": request_id,
			},
			artifact_payload=result.get("normalized_family_artifact") if isinstance(result.get("normalized_family_artifact"), dict) else {},
		)
		if grounded_turn_context and grounded_turn_context.grounded:
			grounded_turn_payload = _compiled_grounded_turn_payload_for_authority(
				grounded_turn_payload=grounded_turn_context.to_payload(),
				result=result,
				request_id=request_id,
			)
			pre_assistant_tool_payloads.append(grounded_turn_payload)
	step_result_integration_payload = build_multi_step_step_result_integration_payload(
		request_id=request_id,
		compound_assessment_payload=compound_request_assessment_payload,
		grounded_turn_payload=grounded_turn_payload,
		clarification_signal_payload=clarification_signal_payload,
		normalized_family_artifact=result.get("normalized_family_artifact")
		if isinstance(result.get("normalized_family_artifact"), dict)
		else {},
		family_validation_payload=family_payload,
		semantic_validation_payload=semantic_payload,
	)
	if step_result_integration_payload:
		pre_assistant_tool_payloads.append(step_result_integration_payload)
	updated_compound_assessment_payload = build_post_result_multi_step_assessment_payload(
		compound_assessment_payload=compound_request_assessment_payload,
		step_result_integration_payload=step_result_integration_payload,
	)
	if updated_compound_assessment_payload:
		pre_assistant_tool_payloads.append(updated_compound_assessment_payload)
	compiled_audit_payload = result.get("compiled_execution_audit") if isinstance(result.get("compiled_execution_audit"), dict) else {}
	boundary_payload = append_knowledge_boundary_contract(
		session_doc,
		request_id=request_id,
		session_id=str(getattr(interaction_contract, "session_id", "") or "").strip(),
		proposed_lane="clarification" if clarification_signal_payload else "artifact_lane",
		clarification_resolution=clarification_response_contract.to_payload() if clarification_response_contract is not None else {},
		clarification_reason=clarification_reason_payload,
		front_door_contract=front_door_contract.to_payload() if front_door_contract is not None else {},
		governed_scope_contract=governed_scope_contract.to_payload() if governed_scope_contract is not None else {},
		compiled_execution_audit=compiled_audit_payload,
		family_validation=family_payload,
		semantic_validation=semantic_payload,
		grounded_turn=grounded_turn_payload,
	)
	should_append_boundary_observability = knowledge_boundary_event_level(boundary_payload) == "warning"

	answer_type = _compiled_answer_type(
		answer_text=answer_text,
		clarification_signal_payload=clarification_signal_payload,
		boundary_payload=boundary_payload,
		runtime_payload=runtime_payload,
		family_payload=family_payload,
		semantic_payload=semantic_payload,
	)
	control_meta_authority = (
		_compiled_control_meta_authority(
			answer_type=answer_type,
			clarification_signal_payload=clarification_signal_payload,
			runtime_payload=runtime_payload,
		)
		if answer_type in {ANSWER_TYPE_CONTROL, ANSWER_TYPE_ERROR}
		else None
	)
	runtime_metadata_envelope = _compiled_runtime_metadata_envelope(
		answer_type=answer_type,
		control_meta_authority=control_meta_authority,
	)
	if isinstance(runtime_trace_payload, dict):
		runtime_trace_payload["runtime_metadata_envelope"] = runtime_metadata_envelope
		trace_agent_meta = runtime_trace_payload.get("agent_meta") if isinstance(runtime_trace_payload.get("agent_meta"), dict) else {}
		runtime_trace_payload["agent_meta"] = {
			**trace_agent_meta,
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
		interaction_contract=interaction_contract,
		followup_resolution=followup_resolution,
		execution_path=_compiled_execution_path_for_authority(
			execution_path=execution_path,
			answer_type=answer_type,
		),
		runtime_trace_payload=runtime_trace_payload,
		grounded_turn_context=grounded_turn_payload,
		authority_context=_compiled_authority_context(
			answer_type=answer_type,
			boundary_payload=boundary_payload,
			result=result,
			family_payload=family_payload,
			semantic_payload=semantic_payload,
			compiled_audit_payload=compiled_audit_payload,
		),
		control_meta_authority=control_meta_authority,
		pre_assistant_tool_payloads=pre_assistant_tool_payloads,
	)
	if authorized_emission.emitted and clarification_signal_payload:
		store_pending_clarification_signal(session_doc, clarification_signal_payload)
	if authorized_emission.emitted and should_append_boundary_observability:
		append_knowledge_boundary_observability(
			session_doc,
			request_id=request_id,
			session_id=str(getattr(interaction_contract, "session_id", "") or "").strip(),
			boundary_payload=boundary_payload,
			latency_ms=int(max(0, round((time.perf_counter() - boundary_started_at) * 1000))),
		)
	clarification_turn_ok = bool(answer_text and clarification_signal_payload)
	grounded_runtime_turn_ok = (
		bool(runtime_payload.get("ok"))
		and str(semantic_payload.get("status") or "").strip() == "pass"
		and str(family_payload.get("status") or "pass").strip() in {"", "pass", "not_run"}
	)
	save_session(session_doc, ignore_permissions=False)
	agent_meta_payload = dict(agent_meta)
	agent_meta_payload["runtime_metadata_envelope"] = runtime_metadata_envelope
	agent_meta_payload["authorized_emission"] = authorized_emission.to_payload()
	return True, {
		"ok": bool(
			authorized_emission.emitted
			and (
				clarification_turn_ok
				or grounded_runtime_turn_ok
				or answer_type in {ANSWER_TYPE_POLICY_BOUNDARY, ANSWER_TYPE_CONTROL, ANSWER_TYPE_ERROR}
			)
		),
		"request_id": request_id,
		"mode": "compiled_first_turn",
		"agent_meta": agent_meta_payload,
		"family_validation_status": str(family_payload.get("status") or "not_run").strip(),
		"semantic_validation_status": str(semantic_payload.get("status") or "not_run").strip(),
	}
