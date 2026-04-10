from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

from ai_assistant_ui.qwen_chat.compiler import compile_fresh_query
from ai_assistant_ui.qwen_chat.clarification_state import (
	build_pending_clarification_state,
	ClarificationState,
	get_clarification_state,
	store_clarification_state,
)
from ai_assistant_ui.qwen_chat.contracts import build_clarification_resolution_contract
from ai_assistant_ui.qwen_chat.customer_kpi_runtime_support import resolve_customer_scope_from_message
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import interpret_fresh_query_semantically
from ai_assistant_ui.qwen_chat.governed_kpi_runtime_execution import (
	maybe_build_governed_kpi_value_frontdoor_response,
)
from ai_assistant_ui.qwen_chat.governed_kpi_support import maybe_build_governed_kpi_frontdoor_response
from ai_assistant_ui.qwen_chat.metadata import ontology_detect_concepts


def _normalize_text(value: Any) -> str:
	return " ".join(str(value or "").strip().lower().split())


def _visible_message_text(role: str, content: str) -> str:
	text = str(content or "").strip()
	if not text:
		return ""
	if str(role or "").strip().lower() != "assistant":
		return text
	try:
		payload = json.loads(text)
	except Exception:
		return text
	if isinstance(payload, dict):
		payload_type = str(payload.get("type") or "").strip().lower()
		payload_text = str(payload.get("text") or "").strip()
		if payload_type in {"text", "error"} and payload_text:
			return payload_text
	return text


def _parse_payload(content: str) -> Dict[str, Any]:
	try:
		obj = json.loads(str(content or ""))
	except Exception:
		return {}
	return obj if isinstance(obj, dict) else {}


def latest_pending_clarification_signal_from_messages(session_doc) -> Dict[str, Any]:
	messages = list(session_doc.get("messages") or [])
	latest_assistant_index = -1
	latest_assistant_text = ""
	for idx in range(len(messages) - 1, -1, -1):
		row = messages[idx]
		if str(row.role or "").strip().lower() != "assistant":
			continue
		latest_assistant_index = idx
		latest_assistant_text = _visible_message_text("assistant", str(row.content or "")).strip()
		break
	if latest_assistant_index < 0 or not latest_assistant_text:
		return {}

	signal_payload: Dict[str, Any] = {}
	signal_index = -1
	for offset, row in enumerate(messages[latest_assistant_index + 1 :], start=latest_assistant_index + 1):
		if str(row.role or "").strip().lower() != "tool":
			continue
		payload = _parse_payload(str(row.content or ""))
		if str(payload.get("type") or "").strip() == "qwen_clarification_signal_contract":
			signal_payload = payload
			signal_index = offset
	if not signal_payload:
		return {}
	if str(signal_payload.get("user_question") or "").strip() != latest_assistant_text:
		return {}
	for row in messages[signal_index + 1 :]:
		role = str(row.role or "").strip().lower()
		if role in {"user", "assistant"} and _visible_message_text(role, str(row.content or "")).strip():
			return {}
	return signal_payload


def latest_pending_clarification_signal(session_doc) -> Dict[str, Any]:
	stored_state = get_clarification_state(session_doc)
	if stored_state.has_pending:
		return dict(stored_state.pending_signal)
	return latest_pending_clarification_signal_from_messages(session_doc)


def latest_assistant_turn_was_clarification_fallback_stop(session_doc) -> bool:
	messages = list(session_doc.get("messages") or [])
	latest_assistant_index = -1
	for idx in range(len(messages) - 1, -1, -1):
		row = messages[idx]
		if str(row.role or "").strip().lower() != "assistant":
			continue
		if not _visible_message_text("assistant", str(row.content or "")).strip():
			continue
		latest_assistant_index = idx
		break
	if latest_assistant_index < 0:
		return False
	for idx in range(latest_assistant_index - 1, -1, -1):
		row = messages[idx]
		role = str(row.role or "").strip().lower()
		if role in {"user", "assistant"}:
			break
		if role != "tool":
			continue
		payload = _parse_payload(str(row.content or ""))
		if str(payload.get("type") or "").strip() != "qwen_phase55_observability_event":
			continue
		if str(payload.get("event_family") or "").strip() != "clarification":
			continue
		return str(payload.get("event_name") or "").strip() == "fallback_stop"
	return False


def store_pending_clarification_signal(
	session_doc,
	signal_payload: Dict[str, Any],
	*,
	attempt_count: int = 0,
	max_attempts: int = 3,
) -> None:
	state = build_pending_clarification_state(
		signal_payload,
		attempt_count=attempt_count,
		max_attempts=max_attempts,
	)
	store_clarification_state(session_doc, state)


def clear_pending_clarification_signal(session_doc) -> None:
	store_clarification_state(session_doc, build_pending_clarification_state({}))


def _human_join(values: List[str]) -> str:
	items = [str(value or "").strip() for value in (values or []) if str(value or "").strip()]
	if not items:
		return ""
	if len(items) == 1:
		return items[0]
	if len(items) == 2:
		return f"{items[0]} or {items[1]}"
	return f"{', '.join(items[:-1])}, or {items[-1]}"


def _word_tokens(value: str) -> List[str]:
	return re.findall(r"[A-Za-z0-9]+", str(value or "").lower())


def _looks_like_meta_question(message: str) -> bool:
	text = str(message or "").strip()
	if not text:
		return False
	return "?" in text


def _looks_like_empty_ack(message: str) -> bool:
	text = str(message or "").strip()
	if not text:
		return False
	if "?" in text:
		return False
	return len(_word_tokens(text)) <= 2


def looks_like_short_acknowledgement(message: str) -> bool:
	return _looks_like_empty_ack(message)


def _match_pending_clarification_option(
	message: str,
	options: List[str],
	option_aliases_by_option: Dict[str, List[str]] | None = None,
) -> Tuple[str, str, float]:
	normalized_message = _normalize_text(message)
	if not normalized_message:
		return "", "", 0.0
	unique_options = [str(option or "").strip() for option in (options or []) if str(option or "").strip()]
	if not unique_options:
		return "", "", 0.0
	normalized_options = {_normalize_text(option): option for option in unique_options}
	if normalized_message in normalized_options:
		return normalized_options[normalized_message], "exact", 1.0
	option_aliases_by_option = dict(option_aliases_by_option or {})
	for option in unique_options:
		for alias in (option_aliases_by_option.get(option) or []):
			if normalized_message == _normalize_text(alias):
				return option, "exact_alias", 0.97
	if len(unique_options) == 1:
		return unique_options[0], "single_option", 0.95

	message_concepts = set(ontology_detect_concepts(normalized_message))
	best_option = ""
	best_score = 0.0
	second_score = 0.0
	best_mode = ""
	for option in unique_options:
		normalized_option = _normalize_text(option)
		score = 0.0
		mode = ""
		candidate_phrases = [normalized_option] + [
			_normalize_text(alias)
			for alias in (option_aliases_by_option.get(option) or [])
			if _normalize_text(alias)
		]
		for candidate in candidate_phrases:
			if normalized_message and (normalized_message in candidate or candidate in normalized_message):
				if 0.86 > score:
					score = 0.86
					mode = "substring"
		if message_concepts:
			for phrase in [option] + list(option_aliases_by_option.get(option) or []):
				option_concepts = set(ontology_detect_concepts(phrase))
				if option_concepts:
					overlap = len(message_concepts & option_concepts) / float(len(option_concepts))
					if overlap > score:
						score = overlap
						mode = "concept_overlap"
		if score > best_score:
			second_score = best_score
			best_score = score
			best_option = option
			best_mode = mode
		elif score > second_score:
			second_score = score
	if best_option and best_score >= 0.6 and (best_score - second_score) >= 0.2:
		return best_option, best_mode or "semantic", float(best_score)
	return "", "", 0.0


def pending_clarification_repeat_answer(signal_payload: Dict[str, Any]) -> str:
	question = str(signal_payload.get("user_question") or "").strip()
	options = [
		str(value or "").strip()
		for value in (signal_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	reason_type = str(signal_payload.get("reason_type") or "").strip()
	if reason_type == "report_ambiguity" and options:
		return f"I still need you to choose the report before I continue: {_human_join(options[:3])}."
	if reason_type == "capability_ambiguity" and options:
		return f"I still need you to choose the business area before I continue: {_human_join(options[:5])}."
	if reason_type in {"time_scope_missing", "time_scope_clarification"} and options:
		return f"I still need the time period before I continue: {_human_join(options[:3])}."
	return question or "I still need one more detail before I can continue."


def pending_clarification_meta_answer(signal_payload: Dict[str, Any]) -> str:
	options = [
		str(value or "").strip()
		for value in (signal_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	reason_type = str(signal_payload.get("reason_type") or "").strip()
	if reason_type == "report_ambiguity" and options:
		return f"I’m waiting for you to choose the governed report view before I continue: {_human_join(options[:3])}."
	if reason_type == "capability_ambiguity" and options:
		return f"I’m waiting for you to choose the business area before I continue: {_human_join(options[:5])}."
	if reason_type in {"time_scope_missing", "time_scope_clarification"} and options:
		return f"I’m waiting for the time period before I continue: {_human_join(options[:3])}."
	return pending_clarification_repeat_answer(signal_payload)


def pending_clarification_empty_ack_answer(signal_payload: Dict[str, Any]) -> str:
	options = [
		str(value or "").strip()
		for value in (signal_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	if options:
		return f"I still need one of these choices before I continue: {_human_join(options[:5])}."
	return pending_clarification_repeat_answer(signal_payload)


def pending_clarification_fallback_stop_answer(signal_payload: Dict[str, Any]) -> str:
	options = [
		str(value or "").strip()
		for value in (signal_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	reason_type = str(signal_payload.get("reason_type") or "").strip()
	if reason_type == "report_ambiguity" and options:
		return f"I’ll pause here rather than guess the report. When you come back, please choose one of these directly: {_human_join(options[:3])}."
	if reason_type == "capability_ambiguity" and options:
		return f"I’ll pause here rather than guess the business area. When you come back, please choose one of these directly: {_human_join(options[:5])}."
	if reason_type in {"time_scope_missing", "time_scope_clarification"} and options:
		return f"I’ll pause here rather than guess the period. When you come back, please choose one of these directly: {_human_join(options[:3])}."
	return "I’ll pause here rather than guess the missing detail. When you come back, please restate the request with the specific report, area, or period you want."


def _resolved_slot(reason_type: str, matched_option: str) -> Dict[str, Any]:
	if not matched_option:
		return {}
	if reason_type == "report_ambiguity":
		return {"selected_report": matched_option}
	if reason_type == "capability_ambiguity":
		return {"selected_business_area": matched_option}
	if reason_type in {"time_scope_missing", "time_scope_clarification"}:
		return {"selected_time_scope": matched_option}
	if reason_type == "customer_scope_missing":
		return {"selected_customer": matched_option}
	return {"selected_option": matched_option}


def governed_fallback_option(signal_payload: Dict[str, Any]) -> str:
	payload = dict(signal_payload or {})
	for key in ("governed_default_option", "default_option"):
		value = str(payload.get(key) or "").strip()
		if value:
			return value
	internal_details = payload.get("internal_details")
	if isinstance(internal_details, dict):
		for key in ("governed_default_option", "default_option"):
			value = str(internal_details.get(key) or "").strip()
			if value:
				return value
	return ""


def clarification_state_after_unresolved_attempt(state: ClarificationState, signal_payload: Dict[str, Any]) -> ClarificationState:
	if state.has_pending:
		return state.next_attempt()
	return build_pending_clarification_state(signal_payload, attempt_count=1)


def _normalized_values(values: List[str]) -> List[str]:
	out: List[str] = []
	for value in values:
		clean = re.sub(r"\s+", " ", str(value or "").strip().lower())
		if clean and clean not in out:
			out.append(clean)
	return out


def clarification_continuation_lane(signal_payload: Dict[str, Any]) -> str:
	internal_details = signal_payload.get("internal_details")
	if not isinstance(internal_details, dict):
		return ""
	return str(internal_details.get("continuation_lane") or "").strip()


def clarification_resolved_continuation_message(
	*,
	signal_payload: Dict[str, Any],
	resolved_option: str,
) -> str:
	option = str(resolved_option or "").strip()
	if not option:
		return ""
	internal_details = signal_payload.get("internal_details")
	if not isinstance(internal_details, dict):
		return ""
	resolved_message_by_option = (
		internal_details.get("resolved_message_by_option")
		if isinstance(internal_details.get("resolved_message_by_option"), dict)
		else {}
	)
	if resolved_message_by_option:
		exact_message = str(resolved_message_by_option.get(option) or "").strip()
		if exact_message:
			return exact_message
		normalized_target = _normalize_text(option)
		for key, value in resolved_message_by_option.items():
			if _normalize_text(key) == normalized_target:
				return str(value or "").strip()
	resolved_message_template = str(internal_details.get("resolved_message_template") or "").strip()
	if resolved_message_template and "{customer}" in resolved_message_template:
		return resolved_message_template.replace("{customer}", option)
	return ""


def _same_pending_clarification(
	*,
	compiler_contract: Any,
	signal_payload: Dict[str, Any],
) -> bool:
	pending_reason_type = str(signal_payload.get("reason_type") or "").strip()
	compiler_reason_type = str(getattr(compiler_contract, "clarification_reason_type", "") or "").strip()
	if not pending_reason_type or compiler_reason_type != pending_reason_type:
		return False
	compiler_details = getattr(compiler_contract, "clarification_details", None)
	if not isinstance(compiler_details, dict):
		return False
	pending_options = _normalized_values(
		[
			str(value or "").strip()
			for value in (signal_payload.get("suggested_options") or [])
			if str(value or "").strip()
		]
	)
	if not pending_options:
		return False
	candidate_values: List[str] = []
	for key in ("report_candidates", "capability_candidates", "suggested_options"):
		values = compiler_details.get(key)
		if isinstance(values, list):
			candidate_values = [str(value or "").strip() for value in values if str(value or "").strip()]
			if candidate_values:
				break
	if not candidate_values:
		return False
	return _normalized_values(candidate_values) == pending_options


def _semantic_new_request_detected(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	signal_payload: Dict[str, Any],
) -> bool:
	result = interpret_fresh_query_semantically(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		recent_messages=[],
	)
	interpretation = getattr(result, "interpretation", None)
	if interpretation is None:
		return False
	if not bool(list(getattr(interpretation, "candidate_capability_ids", []) or []) or list(
		getattr(interpretation, "candidate_reports", []) or []
	)):
		return False
	compiler_outcome = compile_fresh_query(
		request_id=request_id,
		session_id=session_id,
		interpretation=interpretation,
		response_policy={"analysis_level": "none"},
	)
	compiler_contract = getattr(compiler_outcome, "compiler_contract", None)
	if compiler_contract is None:
		return False
	decision = str(getattr(compiler_contract, "decision", "") or "").strip()
	if decision not in {"execute", "clarify"}:
		return False
	if decision == "clarify" and _same_pending_clarification(
		compiler_contract=compiler_contract,
		signal_payload=signal_payload,
	):
		return False
	return True


def _frontdoor_new_request_detected(
	*,
	request_id: str,
	message: str,
	grounded_turn: Dict[str, Any] | None = None,
) -> bool:
	return bool(
		maybe_build_governed_kpi_frontdoor_response(
			request_id=request_id,
			message=message,
		)
		or maybe_build_governed_kpi_value_frontdoor_response(
			request_id=request_id,
			message=message,
			grounded_turn=grounded_turn,
		)
	)


def resolve_pending_clarification_response(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	signal_payload: Dict[str, Any],
	clarification_attempt_count: int = 0,
	max_attempts: int = 3,
	grounded_turn: Dict[str, Any] | None = None,
) -> Any:
	stage = str(signal_payload.get("stage") or "").strip()
	reason_type = str(signal_payload.get("reason_type") or "").strip()
	user_question = str(signal_payload.get("user_question") or "").strip()
	options = [
		str(value or "").strip()
		for value in (signal_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	internal_details = signal_payload.get("internal_details")
	option_aliases_by_option = (
		internal_details.get("option_aliases_by_option")
		if isinstance(internal_details, dict) and isinstance(internal_details.get("option_aliases_by_option"), dict)
		else {}
	)
	matched_option, matched_by, confidence = _match_pending_clarification_option(
		message,
		options,
		option_aliases_by_option=option_aliases_by_option,
	)
	if reason_type == "customer_scope_missing":
		customer_scope = resolve_customer_scope_from_message(message)
		resolved_customer = str(
			customer_scope.get("customer_name")
			or customer_scope.get("entity_label")
			or customer_scope.get("customer")
			or ""
		).strip()
		if resolved_customer:
			return build_clarification_resolution_contract(
				request_id=request_id,
				session_id=session_id,
				pending_stage=stage,
				pending_reason_type=reason_type,
				pending_user_question=user_question,
				pending_suggested_options=options,
				decision="resolved_option",
				resolved_option=resolved_customer,
				matched_by="customer_scope",
				confidence=0.95,
				reason="The user supplied a governed customer scope for the pending customer KPI request.",
				resolved_slot=_resolved_slot(reason_type, resolved_customer),
				clarification_attempt_count=int(max(0, clarification_attempt_count)),
				is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
			)
	new_request_detected = _semantic_new_request_detected(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		signal_payload=signal_payload,
	) or _frontdoor_new_request_detected(
		request_id=request_id,
		message=message,
		grounded_turn=grounded_turn,
	)
	if matched_option and (matched_by in {"exact", "exact_alias", "single_option"} or not new_request_detected):
		return build_clarification_resolution_contract(
			request_id=request_id,
			session_id=session_id,
			pending_stage=stage,
			pending_reason_type=reason_type,
			pending_user_question=user_question,
			pending_suggested_options=options,
			decision="resolved_option",
			resolved_option=matched_option,
			matched_by=matched_by,
			confidence=confidence,
			reason="The user selected one of the pending clarification options.",
			resolved_slot=_resolved_slot(reason_type, matched_option),
			clarification_attempt_count=int(max(0, clarification_attempt_count)),
			is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
		)
	if _looks_like_meta_question(message):
		return build_clarification_resolution_contract(
			request_id=request_id,
			session_id=session_id,
			pending_stage=stage,
			pending_reason_type=reason_type,
			pending_user_question=user_question,
			pending_suggested_options=options,
			decision="meta_question",
			matched_by="question_shape",
			confidence=0.7,
			reason="The user asked about the pending clarification itself rather than selecting an option.",
			clarification_attempt_count=int(max(0, clarification_attempt_count)),
			is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
		)
	if _looks_like_empty_ack(message):
		return build_clarification_resolution_contract(
			request_id=request_id,
			session_id=session_id,
			pending_stage=stage,
			pending_reason_type=reason_type,
			pending_user_question=user_question,
			pending_suggested_options=options,
			decision="empty_ack",
			matched_by="short_non_business_turn",
			confidence=0.65,
			reason="The user acknowledged the clarification but did not provide a resolvable option yet.",
			clarification_attempt_count=int(max(0, clarification_attempt_count)),
			is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
		)
	if new_request_detected:
		return build_clarification_resolution_contract(
			request_id=request_id,
			session_id=session_id,
			pending_stage=stage,
			pending_reason_type=reason_type,
			pending_user_question=user_question,
			pending_suggested_options=options,
			decision="new_request",
			confidence=0.8,
			reason="A semantic fresh-query cross-check indicates the user started a new ERP request and should continue through the main lanes.",
			clarification_attempt_count=int(max(0, clarification_attempt_count)),
			is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
		)
	return build_clarification_resolution_contract(
		request_id=request_id,
		session_id=session_id,
		pending_stage=stage,
		pending_reason_type=reason_type,
		pending_user_question=user_question,
		pending_suggested_options=options,
		decision="reask_pending_clarification",
		confidence=0.0,
		reason="The user did not answer the pending clarification with a resolvable option or new substantive ERP request.",
		clarification_attempt_count=int(max(0, clarification_attempt_count)),
		is_final_attempt=bool(int(max(0, clarification_attempt_count)) >= max(0, int(max_attempts) - 1)),
	)
