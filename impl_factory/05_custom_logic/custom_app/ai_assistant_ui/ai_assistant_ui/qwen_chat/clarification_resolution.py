from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

from ai_assistant_ui.qwen_chat.contracts import build_clarification_resolution_contract
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import interpret_fresh_query_semantically
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


def _stored_pending_clarification_signal(session_doc) -> Dict[str, Any]:
	raw_value = str(getattr(session_doc, "pending_clarification_state_json", "") or "").strip()
	if not raw_value:
		return {}
	payload = _parse_payload(raw_value)
	if str(payload.get("type") or "").strip() != "qwen_clarification_signal_contract":
		return {}
	return payload


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
	for row in messages[latest_assistant_index + 1 :]:
		if str(row.role or "").strip().lower() != "tool":
			continue
		payload = _parse_payload(str(row.content or ""))
		if str(payload.get("type") or "").strip() == "qwen_clarification_signal_contract":
			signal_payload = payload
	if not signal_payload:
		return {}
	if str(signal_payload.get("user_question") or "").strip() != latest_assistant_text:
		return {}
	return signal_payload


def latest_pending_clarification_signal(session_doc) -> Dict[str, Any]:
	stored = _stored_pending_clarification_signal(session_doc)
	if stored:
		return stored
	return latest_pending_clarification_signal_from_messages(session_doc)


def store_pending_clarification_signal(session_doc, signal_payload: Dict[str, Any]) -> None:
	payload = dict(signal_payload or {})
	if str(payload.get("type") or "").strip() != "qwen_clarification_signal_contract":
		return
	session_doc.pending_clarification_state_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)


def clear_pending_clarification_signal(session_doc) -> None:
	session_doc.pending_clarification_state_json = ""


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


def _match_pending_clarification_option(message: str, options: List[str]) -> Tuple[str, str, float]:
	normalized_message = _normalize_text(message)
	if not normalized_message:
		return "", "", 0.0
	unique_options = [str(option or "").strip() for option in (options or []) if str(option or "").strip()]
	if not unique_options:
		return "", "", 0.0
	normalized_options = {_normalize_text(option): option for option in unique_options}
	if normalized_message in normalized_options:
		return normalized_options[normalized_message], "exact", 1.0
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
		if normalized_message and (normalized_message in normalized_option or normalized_option in normalized_message):
			score = 0.86
			mode = "substring"
		if message_concepts:
			option_concepts = set(ontology_detect_concepts(option))
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


def _resolved_slot(reason_type: str, matched_option: str) -> Dict[str, Any]:
	if not matched_option:
		return {}
	if reason_type == "report_ambiguity":
		return {"selected_report": matched_option}
	if reason_type == "capability_ambiguity":
		return {"selected_business_area": matched_option}
	if reason_type in {"time_scope_missing", "time_scope_clarification"}:
		return {"selected_time_scope": matched_option}
	return {"selected_option": matched_option}


def _semantic_new_request_detected(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
) -> bool:
	result = interpret_fresh_query_semantically(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
		recent_messages=[],
	)
	if str(getattr(result, "status", "") or "").strip() != "accepted":
		return False
	interpretation = getattr(result, "interpretation", None)
	if interpretation is None:
		return False
	return bool(list(getattr(interpretation, "candidate_capability_ids", []) or []) or list(
		getattr(interpretation, "candidate_reports", []) or []
	))


def resolve_pending_clarification_response(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
	signal_payload: Dict[str, Any],
) -> Any:
	stage = str(signal_payload.get("stage") or "").strip()
	reason_type = str(signal_payload.get("reason_type") or "").strip()
	user_question = str(signal_payload.get("user_question") or "").strip()
	options = [
		str(value or "").strip()
		for value in (signal_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	matched_option, matched_by, confidence = _match_pending_clarification_option(message, options)
	if matched_option:
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
			clarification_attempt_count=1,
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
			clarification_attempt_count=1,
		)
	if _semantic_new_request_detected(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=message,
	):
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
	)
