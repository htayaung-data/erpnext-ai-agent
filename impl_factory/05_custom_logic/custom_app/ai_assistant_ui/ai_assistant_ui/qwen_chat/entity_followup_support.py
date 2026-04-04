from __future__ import annotations

from typing import Any, Dict, Tuple


def try_entity_detail_followup(
	session_doc,
	*,
	request_id: str,
	raw_message: str,
	entity_reference: Dict[str, Any],
	interaction_contract,
	response_policy_contract,
	latest_grounded_turn: Dict[str, Any],
	execute_entity_drilldown,
	log_error,
	append_message,
	append_tool_payload,
	assistant_text_payload,
	tool_trace_message,
	save_session,
) -> Tuple[bool, Dict[str, Any]] | None:
	try:
		outcome = execute_entity_drilldown(
			request_id=request_id,
			session_id=session_doc.name,
			user_id=str(interaction_contract.user_id or "").strip(),
			site_name=str(interaction_contract.site_name or "").strip(),
			message=str(raw_message or "").strip(),
			entity_reference=entity_reference,
			response_policy=response_policy_contract.to_runtime_payload(),
			grounded_turn=latest_grounded_turn,
		)
	except Exception as exc:
		log_error("Qwen Assistant: entity drilldown failed")
		append_message(
			session_doc,
			"assistant",
			assistant_text_payload("I couldn't complete that entity detail confidently from governed ERP data."),
		)
		append_message(
			session_doc,
			"tool",
			tool_trace_message(
				request_id=request_id,
				ok=False,
				tool_trace=[
					{
						"tool": "entity_detail_lookup",
						"status": "error",
						"detail": str(exc or "").strip(),
						"detail_obj": {
							"entity_type": str(entity_reference.get("entity_type") or "").strip(),
							"entity_key": str(entity_reference.get("entity_key") or "").strip(),
						},
					}
				],
				agent_meta={"engine": "entity_detail", "mode": "entity_drilldown"},
				error=str(exc or "").strip(),
				runtime_latency_ms=0,
			),
		)
		save_session(session_doc, ignore_permissions=False)
		return True, {"ok": False, "request_id": request_id, "error": str(exc or "").strip(), "agent_meta": {"engine": "entity_detail"}}

	if not bool(outcome.get("ok")):
		return None

	answer_text = str(outcome.get("answer_text") or "").strip()
	append_message(session_doc, "assistant", assistant_text_payload(answer_text))
	artifact_payload = outcome.get("artifact_payload") if isinstance(outcome.get("artifact_payload"), dict) else {}
	rendered_payload = outcome.get("rendered_response_payload") if isinstance(outcome.get("rendered_response_payload"), dict) else {}
	narrative_contract_payload = outcome.get("narrative_contract_payload") if isinstance(outcome.get("narrative_contract_payload"), dict) else {}
	grounded_turn_payload = outcome.get("grounded_turn_payload") if isinstance(outcome.get("grounded_turn_payload"), dict) else {}
	if artifact_payload:
		append_tool_payload(session_doc, artifact_payload)
	if rendered_payload:
		append_tool_payload(session_doc, rendered_payload)
	if narrative_contract_payload:
		append_tool_payload(session_doc, narrative_contract_payload)
	if grounded_turn_payload:
		append_tool_payload(session_doc, grounded_turn_payload)
	trace_payload = tool_trace_message(
		request_id=request_id,
		ok=True,
		tool_trace=[
			{
				"tool": "entity_detail_lookup",
				"status": "ok",
				"detail": str(outcome.get("answer_text") or "").strip()[:240],
				"detail_obj": {
					"entity_type": str((outcome.get("entity_reference") or {}).get("entity_type") or "").strip(),
					"entity_key": str((outcome.get("entity_reference") or {}).get("entity_key") or "").strip(),
				},
			}
		],
		agent_meta={"engine": "entity_detail", "mode": "entity_drilldown"},
		error="",
		runtime_latency_ms=0,
	)
	append_message(session_doc, "tool", trace_payload)
	save_session(session_doc, ignore_permissions=False)
	return True, {"ok": True, "request_id": request_id, "agent_meta": {"engine": "entity_detail", "mode": "entity_drilldown"}}
