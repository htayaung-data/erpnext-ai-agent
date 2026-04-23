from __future__ import annotations

from typing import Any, Callable, Dict, Tuple

from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_followup_resolution_contract,
	build_governed_scope_decision_contract,
	build_scope_decision_input,
)
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import execute_compiled_fresh_query_message
from ai_assistant_ui.qwen_chat.semantic_repair_intent import (
	build_repair_intent_contract_from_semantic_result,
	interpret_repair_intent_semantically,
)


def handle_repair_turn(
	*,
	session_doc,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	raw_message: str,
	recent_messages,
	latest_recovery_contract: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	latest_assistant_payload: Dict[str, Any],
	interaction_contract,
	frontdoor_semantic_result,
	frontdoor_contract,
	clarification_response_contract,
	response_policy_contract,
	append_message: Callable[..., None],
	append_tool_payload: Callable[..., None],
	build_recovery_guidance_answer: Callable[[Dict[str, Any]], str],
	handle_recovery_guidance_response: Callable[..., Tuple[bool, Dict[str, Any]]],
	build_recovery_governed_query_message: Callable[[Dict[str, Any]], str],
	handle_compiled_first_turn_result: Callable[..., Tuple[bool, Dict[str, Any]]],
) -> Tuple[bool, Dict[str, Any] | None]:
	semantic_repair_result = interpret_repair_intent_semantically(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		recent_messages=recent_messages,
		latest_recovery_contract=latest_recovery_contract,
		latest_grounded_turn=latest_grounded_turn,
		latest_assistant_payload=latest_assistant_payload,
	)
	semantic_repair_payload = semantic_repair_result.to_payload()
	repair_contract_payload = build_repair_intent_contract_from_semantic_result(
		request_id=request_id,
		session_id=session_id,
		semantic_result=semantic_repair_result,
	)
	repair_intent = semantic_repair_result.intent
	if (
		semantic_repair_result.status == "accepted"
		and repair_intent is not None
		and str(repair_intent.repair_intent_type or "").strip() == "guidance_request"
	):
		answer_text = build_recovery_guidance_answer(latest_recovery_contract)
		_, payload = handle_recovery_guidance_response(
			session_doc=session_doc,
			request_id=request_id,
			raw_message=raw_message,
			interaction_contract=interaction_contract,
			frontdoor_semantic_result=frontdoor_semantic_result,
			frontdoor_contract=frontdoor_contract,
			clarification_response_contract=clarification_response_contract,
			response_policy_contract=response_policy_contract,
			semantic_repair_payload=semantic_repair_payload,
			repair_contract_payload=repair_contract_payload,
			latest_grounded_turn=latest_grounded_turn,
			answer_text=answer_text,
		)
		return True, payload
	if (
		semantic_repair_result.status == "accepted"
		and repair_intent is not None
		and str(repair_intent.repair_intent_type or "").strip() == "accept_recovery_action"
	):
		accepted_action = str(repair_intent.accepted_recovery_action or "").strip()
		if accepted_action == "run_alternative_governed_query":
			synthesized_message = build_recovery_governed_query_message(latest_recovery_contract)
			preservable_scope = (
				latest_recovery_contract.get("preservable_scope")
				if isinstance(latest_recovery_contract.get("preservable_scope"), dict)
				else {}
			)
			governed_target_limit = int(max(0, preservable_scope.get("requested_top_n") or 0))
			followup_resolution = build_followup_resolution_contract(
				request_id=request_id,
				mode="new_query",
				depends_on_grounded_turn=False,
				self_contained=True,
				latest_grounded_turn_available=bool(latest_grounded_turn),
				reason="The user accepted a governed recovery alternative, so the assistant must run a fresh governed query.",
			)
			execution_path = ExecutionPath(
				request_id=request_id,
				path="recovery_fresh_query",
				reason="The user accepted a governed recovery alternative and it was converted into a fresh governed query.",
				requires_runtime=True,
				grounded_required=False,
			)
			scope_decision_contract = build_governed_scope_decision_contract(
				request_id=request_id,
				stage="recovery_orchestration",
				followup_resolution=followup_resolution,
				context_isolation=build_scope_decision_input(force_new_query=True, reason="Accepted governed recovery action."),
				latest_grounded_turn_available=False,
				entity_drilldown=None,
				continuation_contract=None,
				clarification_required=False,
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
			append_tool_payload(session_doc, scope_decision_contract.to_payload())
			append_tool_payload(session_doc, execution_path.to_payload())
			compiled_result = execute_compiled_fresh_query_message(
				session_id=session_id,
				user_id=user_id,
				site_name=site_name,
				message=synthesized_message,
				recent_messages=[],
				clarification_resolution=clarification_response_contract.to_payload() if clarification_response_contract is not None else None,
				front_door_contract=frontdoor_contract.to_payload() if frontdoor_contract is not None else None,
				governed_target_limit=governed_target_limit,
			)
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
			return True, payload
		if accepted_action == "clarify_target_output":
			answer_text = build_recovery_guidance_answer(latest_recovery_contract)
			_, payload = handle_recovery_guidance_response(
				session_doc=session_doc,
				request_id=request_id,
				raw_message=raw_message,
				interaction_contract=interaction_contract,
				frontdoor_semantic_result=frontdoor_semantic_result,
				frontdoor_contract=frontdoor_contract,
				clarification_response_contract=clarification_response_contract,
				response_policy_contract=response_policy_contract,
				semantic_repair_payload=semantic_repair_payload,
				repair_contract_payload=repair_contract_payload,
				latest_grounded_turn=latest_grounded_turn,
				answer_text=answer_text,
			)
			return True, payload
	return False, None
