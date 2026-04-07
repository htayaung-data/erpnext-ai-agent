from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

from ai_assistant_ui.qwen_chat.contracts import ExecutionPath, build_audit_envelope


def handle_entity_drilldown_turn(
	*,
	session_doc,
	request_id: str,
	session_id: str,
	message: str,
	entity_reference: Dict[str, Any],
	followup_resolution,
	interaction_contract,
	response_policy_contract,
	frontdoor_contract,
	scope_decision_contract,
	latest_grounded_turn: Dict[str, Any],
	try_entity_detail_followup: Callable[..., Tuple[bool, Dict[str, Any]] | None],
	append_tool_payload: Callable[..., None],
	append_knowledge_boundary_contract: Callable[..., Dict[str, Any]],
	build_latest_grounded_turn_contract: Callable[..., Dict[str, Any]],
	build_latest_qwen_trace_payload: Callable[..., Dict[str, Any]],
	build_latest_assistant_payload: Callable[..., Dict[str, Any]],
	save_session: Callable[..., None],
) -> Tuple[bool, Dict[str, Any] | None]:
	explicit_entity_reference = str((entity_reference or {}).get("source") or "").strip() == "explicit_identifier"
	grounded_required = bool(latest_grounded_turn) and not explicit_entity_reference
	execution_path = ExecutionPath(
		request_id=request_id,
		path="entity_drilldown",
		reason=(
			"The request was resolved through a governed entity drilldown over an explicitly referenced entity."
			if explicit_entity_reference
			else "The request was resolved through a governed entity drilldown over the latest artifact."
		),
		requires_runtime=True,
		grounded_required=grounded_required,
	)
	append_tool_payload(session_doc, execution_path.to_payload())
	entity_result = try_entity_detail_followup(
		session_doc,
		request_id=request_id,
		raw_message=message,
		entity_reference=entity_reference,
		interaction_contract=interaction_contract,
		response_policy_contract=response_policy_contract,
		latest_grounded_turn=latest_grounded_turn,
	)
	if not entity_result:
		return False, None

	latest_grounded_turn_payload = build_latest_grounded_turn_contract(session_doc)
	append_knowledge_boundary_contract(
		session_doc,
		request_id=request_id,
		session_id=session_id,
		proposed_lane="artifact_lane",
		front_door_contract=frontdoor_contract.to_payload(),
		governed_scope_contract=scope_decision_contract.to_payload(),
		grounded_turn=latest_grounded_turn_payload,
	)
	append_tool_payload(
		session_doc,
		build_audit_envelope(
			interaction_contract=interaction_contract,
			followup_resolution=followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload=build_latest_qwen_trace_payload(session_doc),
			grounded_turn_context=latest_grounded_turn_payload,
			answer_text=str(build_latest_assistant_payload(session_doc).get("text") or ""),
		).to_payload(),
	)
	save_session(session_doc, ignore_permissions=False)
	return entity_result
