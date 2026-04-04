from __future__ import annotations

import json
from typing import Any, Dict, List, Set


def parse_payload(content: str) -> Dict[str, Any]:
	try:
		obj = json.loads(str(content or ""))
	except Exception:
		return {}
	return obj if isinstance(obj, dict) else {}


def visible_message_text(role: str, content: str) -> str:
	text = str(content or "").strip()
	if not text:
		return ""
	if role != "assistant":
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


def positions_to_skip_for_runtime_context(session_doc: Any, *, visible_roles: Set[str]) -> set[int]:
	messages = list(session_doc.get("messages") or [])
	skip: set[int] = set()
	for pos, message in enumerate(messages):
		if str(message.role or "").strip().lower() != "tool":
			continue
		payload = parse_payload(str(message.content or ""))
		if str(payload.get("type") or "").strip().lower() != "qwen_runtime_trace":
			continue
		agent_meta = payload.get("agent_meta") if isinstance(payload.get("agent_meta"), dict) else {}
		if str(agent_meta.get("engine") or "").strip().lower() != "local_transform":
			continue
		scan = pos - 1
		visible_found = 0
		while scan >= 0 and visible_found < 2:
			role = str(messages[scan].role or "").strip().lower()
			if role == "tool":
				break
			if role in visible_roles:
				skip.add(scan)
				visible_found += 1
			scan -= 1
	return skip


def recent_messages(session_doc: Any, *, visible_roles: Set[str], limit: int = 10) -> List[Dict[str, str]]:
	out: List[Dict[str, str]] = []
	skip_positions = positions_to_skip_for_runtime_context(session_doc, visible_roles=visible_roles)
	for pos, message in reversed(list(enumerate(session_doc.get("messages") or []))):
		if pos in skip_positions:
			continue
		role = str(message.role or "").strip().lower()
		if role not in visible_roles:
			continue
		content = visible_message_text(role, str(message.content or ""))
		if not content:
			continue
		out.append({"role": role, "content": content[:2000]})
		if len(out) >= max(1, int(limit)):
			break
	return list(reversed(out))


def latest_assistant_payload(session_doc: Any) -> Dict[str, Any]:
	for message in reversed(session_doc.get("messages") or []):
		if str(message.role or "").strip().lower() != "assistant":
			continue
		payload = parse_payload(str(message.content or ""))
		if payload:
			return payload
		text = str(message.content or "").strip()
		if text:
			return {"type": "text", "text": text}
	return {}


def tool_payloads(session_doc: Any) -> List[Dict[str, Any]]:
	out: List[Dict[str, Any]] = []
	for row in session_doc.get("messages") or []:
		if str(row.role or "").strip().lower() != "tool":
			continue
		payload = parse_payload(str(row.content or ""))
		if payload:
			out.append(payload)
	return out


def latest_display_preferences(
	session_doc: Any,
	*,
	requested_modes: List[str] | None = None,
) -> Dict[str, bool]:
	requested = {
		str(mode or "").strip()
		for mode in (requested_modes or [])
		if str(mode or "").strip()
	}
	payload = latest_assistant_payload(session_doc)
	text = str(payload.get("text") or "").strip().lower()
	has_tables = bool(payload.get("tables"))
	return {
		"million": "presentation_transform" in requested or "mmk million" in text or "million mmk" in text,
		"table": "table_presentation" in requested or has_tables,
		"bullet": "bullet_presentation" in requested or "•" in text or "\n- " in text,
	}


def recent_messages_for_grounded_source(
	session_doc: Any,
	*,
	grounded_turn: Dict[str, Any],
	visible_roles: Set[str],
	limit: int = 10,
) -> List[Dict[str, str]]:
	grounded = dict(grounded_turn or {})
	source_request_id = str(grounded.get("trace_request_id") or grounded.get("request_id") or "").strip()
	if not source_request_id:
		return recent_messages(session_doc, visible_roles=visible_roles, limit=limit)
	messages = list(session_doc.get("messages") or [])
	skip_positions = positions_to_skip_for_runtime_context(session_doc, visible_roles=visible_roles)
	start_pos = -1
	for pos, message in enumerate(messages):
		if str(message.role or "").strip().lower() != "tool":
			continue
		payload = parse_payload(str(message.content or ""))
		if str(payload.get("type") or "").strip().lower() != "qwen_grounded_turn_context":
			continue
		payload_request_id = str(payload.get("trace_request_id") or payload.get("request_id") or "").strip()
		if payload_request_id == source_request_id:
			start_pos = pos
	out: List[Dict[str, str]] = []
	for pos in range(len(messages) - 1, start_pos, -1):
		if pos in skip_positions:
			continue
		message = messages[pos]
		role = str(message.role or "").strip().lower()
		if role not in visible_roles:
			continue
		content = visible_message_text(role, str(message.content or ""))
		if not content:
			continue
		out.append({"role": role, "content": content[:2000]})
		if len(out) >= max(1, int(limit)):
			break
	return list(reversed(out))
