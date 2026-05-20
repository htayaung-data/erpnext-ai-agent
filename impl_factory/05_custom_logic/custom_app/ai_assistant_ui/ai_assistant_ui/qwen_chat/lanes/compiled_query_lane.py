from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

from ai_assistant_ui.qwen_chat.contracts import (
	build_execution_path,
	build_followup_resolution_contract,
	build_governed_scope_decision_contract,
	build_response_policy_contract,
	build_scope_decision_input,
)
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import execute_compiled_fresh_query_message


def handle_compiled_query_turn(
	*,
	session_doc,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	raw_message: str,
	interaction_contract,
	frontdoor_semantic_result,
	frontdoor_contract,
	clarification_response_contract,
	append_message: Callable[..., None],
	append_tool_payload: Callable[..., None],
	handle_compiled_first_turn_result: Callable[..., Tuple[bool, Dict[str, Any]]],
	latest_grounded_turn_available: bool = False,
	context_isolation=None,
) -> Tuple[bool, Dict[str, Any]]:
	latest_context_available = bool(latest_grounded_turn_available)
	response_policy_contract = build_response_policy_contract(
		interaction_contract=interaction_contract,
	)
	reason = (
		"The request is self-contained, so it should run as a fresh governed ERP query instead of continuing the previous result."
		if latest_context_available
		else "No grounded context exists yet, so the request should be treated as a fresh governed ERP query."
	)
	followup_resolution = build_followup_resolution_contract(
		request_id=request_id,
		mode="new_query",
		requested_modes=[],
		target_dimension="",
		target_limit=0,
		sort_direction="",
		target_metric="",
		requested_columns=[],
		requested_time_scope="",
		target_capability_id="",
		target_report="",
		depends_on_grounded_turn=False,
		self_contained=True,
		latest_grounded_turn_available=latest_context_available,
		reason=reason,
	)
	execution_path = build_execution_path(
		request_id=request_id,
		followup_resolution=followup_resolution,
		local_transform_applied=False,
	)
	scope_decision_contract = build_governed_scope_decision_contract(
		request_id=request_id,
		stage="followup_orchestration",
		followup_resolution=followup_resolution,
		context_isolation=context_isolation if context_isolation is not None else build_scope_decision_input(),
		latest_grounded_turn_available=latest_context_available,
		entity_drilldown=None,
		continuation_contract=None,
		clarification_required=False,
	)
	if (session_doc.title or "").strip() in ("", "New Qwen Chat"):
		session_doc.title = (raw_message[:60] + "...") if len(raw_message) > 60 else raw_message
	append_message(session_doc, "user", raw_message)
	append_tool_payload(session_doc, interaction_contract.to_payload())
	append_tool_payload(session_doc, frontdoor_semantic_result.to_payload())
	append_tool_payload(session_doc, frontdoor_contract.to_payload())
	if clarification_response_contract is not None:
		append_tool_payload(session_doc, clarification_response_contract.to_payload())
	append_tool_payload(session_doc, response_policy_contract.to_payload())
	append_tool_payload(session_doc, followup_resolution.to_payload())
	append_tool_payload(session_doc, scope_decision_contract.to_payload())
	append_tool_payload(session_doc, execution_path.to_payload())
	compiled_result = execute_compiled_fresh_query_message(
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		recent_messages=[],
		clarification_resolution=clarification_response_contract.to_payload() if clarification_response_contract is not None else None,
		front_door_contract=frontdoor_contract.to_payload() if frontdoor_contract is not None else None,
	)
	return handle_compiled_first_turn_result(
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
