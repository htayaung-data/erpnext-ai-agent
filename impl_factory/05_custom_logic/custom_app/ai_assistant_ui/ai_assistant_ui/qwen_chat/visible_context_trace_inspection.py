from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Dict, List, Tuple

from .natural_business_understanding_contracts import CONTRACT_VERSION


AppendMessage = Callable[[Any, str, str], None]
AppendToolPayload = Callable[[Any, Dict[str, Any]], None]
AssistantTextPayload = Callable[[str], str]
SaveSession = Callable[..., None]

TRACE_PAYLOAD_TYPE = "qwen_visible_context_followup_trace_contract"
INSPECTION_PAYLOAD_TYPE = "qwen_visible_context_authority_trace_inspection_contract"


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(value: Any) -> List[Any]:
	return list(value) if isinstance(value, list) else []


def _normalize(value: Any) -> str:
	text = _clean_text(value).lower().replace("_", " ")
	text = re.sub(r"[^a-z0-9]+", " ", text)
	return re.sub(r"\s+", " ", text).strip()


def _safe_json_loads(value: Any) -> Dict[str, Any]:
	if isinstance(value, dict):
		return dict(value)
	try:
		payload = json.loads(_clean_text(value))
	except Exception:
		return {}
	return dict(payload) if isinstance(payload, dict) else {}


def _session_messages(session_doc: Any) -> List[Any]:
	if isinstance(session_doc, dict):
		values = session_doc.get("messages", [])
	else:
		values = getattr(session_doc, "messages", [])
	try:
		return list(values or [])
	except Exception:
		return []


def _message_role(message: Any) -> str:
	if isinstance(message, dict):
		return _clean_text(message.get("role")).lower()
	return _clean_text(getattr(message, "role", "")).lower()


def _message_content(message: Any) -> Any:
	if isinstance(message, dict):
		return message.get("content")
	return getattr(message, "content", None)


def visible_context_trace_inspection_requested(message: str) -> bool:
	"""Detect explicit operator/debug requests without stealing business follow-ups."""

	text = _normalize(message)
	if not text:
		return False
	explicit_trace_terms = {"trace", "debug", "inspection", "inspect", "observability"}
	context_terms = {"context", "authority", "arbitration", "frame", "visible", "table"}
	terms = set(text.split())
	if terms.intersection(explicit_trace_terms) and terms.intersection(context_terms):
		return True
	if re.search(r"\bwhy\b.*\b(choose|chose|select|selected)\b.*\b(table|context|frame)\b", text):
		return True
	if re.search(r"\bshow\b.*\b(frame arbitration|authority trace|context trace)\b", text):
		return True
	return False


def latest_visible_context_authority_trace(session_doc: Any) -> Dict[str, Any]:
	for message in reversed(_session_messages(session_doc)):
		if _message_role(message) != "tool":
			continue
		payload = _safe_json_loads(_message_content(message))
		if _clean_text(payload.get("type")) == TRACE_PAYLOAD_TYPE:
			return payload
	return {}


def _frame_stack_frames(trace_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
	frame_stack = _clean_dict(trace_payload.get("context_frame_stack"))
	return [_clean_dict(frame) for frame in _clean_list(frame_stack.get("frames"))]


def _frame_by_id(trace_payload: Dict[str, Any], frame_id: str) -> Dict[str, Any]:
	for frame in _frame_stack_frames(trace_payload):
		if _clean_text(frame.get("frame_id")) == frame_id:
			return frame
	return {}


def _selected_row_summary(resolution: Dict[str, Any]) -> Tuple[str, List[str]]:
	entity = _clean_dict(resolution.get("resolved_entity"))
	row = _clean_dict(entity.get("row"))
	rank = _clean_text(entity.get("rank") or resolution.get("resolved_rank"))
	label = _clean_text(entity.get("entity_label") or entity.get("label") or entity.get("entity_key"))
	if not label:
		for key in ("customer", "supplier", "party", "product", "item", "invoice", "document", "account", "source_document"):
			if _clean_text(row.get(key)):
				label = _clean_text(row.get(key))
				break
	if not label:
		return "", []
	title = f"Rank {rank}: {label}" if rank else label
	facts: List[str] = []
	for key, value in row.items():
		if key in {"rank", "customer", "supplier", "party", "product", "item", "invoice", "document", "account", "source_document"}:
			continue
		clean_value = _clean_text(value)
		if clean_value:
			facts.append(f"{str(key).replace('_', ' ').title()}: {clean_value}")
		if len(facts) >= 4:
			break
	return title, facts


def _frame_title(frame: Dict[str, Any]) -> str:
	return _clean_text(frame.get("artifact_title") or frame.get("family_id") or frame.get("frame_id")) or "unnamed frame"


def _md_value(value: Any) -> str:
	text = _clean_text(value)
	if not text:
		return "none"
	return text.replace("|", "\\|").replace("\n", " ")


def _frame_decision(frame: Dict[str, Any]) -> str:
	decision = "selected" if frame.get("selected") else "not selected"
	rejection_reason = _clean_text(frame.get("rejection_reason"))
	if rejection_reason:
		decision = f"{decision}; rejection={rejection_reason}"
	recovery_source = _clean_text(frame.get("recovery_source"))
	if recovery_source:
		decision = f"{decision}; recovery={recovery_source}"
	return decision


def _format_match_reasons(frame: Dict[str, Any]) -> str:
	reasons = [_clean_text(reason) for reason in _clean_list(frame.get("match_reasons")) if _clean_text(reason)]
	if not reasons:
		return "none"
	return ", ".join(reasons[:6])


def _append_kv_table(lines: List[str], rows: List[Tuple[str, Any]]) -> None:
	lines.extend(["| Field | Value |", "|---|---|"])
	for key, value in rows:
		lines.append(f"| {_md_value(key)} | {_md_value(value)} |")


def _append_frame_table(lines: List[str], frames: List[Dict[str, Any]]) -> None:
	lines.extend(["| # | Table | Type | Rows | Role | Decision | Match reasons |", "|---|---|---|---:|---|---|---|"])
	if not frames:
		lines.append("| - | none | none | 0 | none | none | none |")
		return
	for index, frame in enumerate(frames[:6], start=1):
		lines.append(
			"| "
			+ " | ".join(
				[
					_md_value(index),
					_md_value(_frame_title(frame)),
					_md_value(_clean_text(frame.get("business_object_type")) or "unknown"),
					_md_value(_clean_text(frame.get("visible_row_count")) or "0"),
					_md_value(_clean_text(frame.get("role")) or "unknown"),
					_md_value(_frame_decision(frame)),
					_md_value(_format_match_reasons(frame)),
				]
			)
			+ " |"
		)


def render_visible_context_authority_trace(trace_payload: Dict[str, Any]) -> str:
	trace = _clean_dict(trace_payload)
	if not trace:
		return (
			"Context Authority Trace\n\n"
			"No visible-context authority trace is available yet. Run a visible table follow-up first, "
			"then ask for the latest context authority trace."
		)
	arbitration = _clean_dict(trace.get("frame_arbitration"))
	resolution = _clean_dict(trace.get("resolution"))
	observability = _clean_dict(trace.get("authority_observability"))
	status = _clean_text(arbitration.get("status") or resolution.get("status") or "unknown")
	selected_frame_id = _clean_text(arbitration.get("selected_frame_id") or observability.get("selected_frame_id"))
	selected_frame = _frame_by_id(trace, selected_frame_id)
	selected_title = _frame_title(selected_frame) if selected_frame else ""
	requested_object = _clean_text(arbitration.get("requested_object_label") or observability.get("requested_object_label")) or "none"
	recovery_source = _clean_text(
		arbitration.get("selected_recovery_source")
		or observability.get("selected_recovery_source")
		or selected_frame.get("recovery_source")
	) or "none"
	lines = ["**Context Authority Trace**", "", "**Authority Summary**"]
	_append_kv_table(
		lines,
		[
			("Status", status),
			("Raw request", _clean_text(trace.get("raw_message")) or "unknown"),
			("Relation", _clean_text(arbitration.get("relation") or observability.get("relation")) or "unknown"),
			("Requested object", requested_object),
			("Selected frame", selected_frame_id or "none"),
			("Selected table", selected_title or "none"),
			(
				"Selected object type",
				_clean_text(arbitration.get("selected_business_object_type") or observability.get("selected_business_object_type")) or "none",
			),
			(
				"Evidence scope",
				_clean_text(arbitration.get("selected_evidence_scope") or observability.get("selected_evidence_scope")) or "none",
			),
			(
				"Visible row count",
				_clean_text(arbitration.get("selected_visible_row_count") or observability.get("selected_visible_row_count")) or "0",
			),
			(
				"Selection strategy",
				_clean_text(arbitration.get("selection_strategy") or observability.get("selection_strategy")) or "none",
			),
			("Recovery source", recovery_source),
		],
	)
	selected_row, row_facts = _selected_row_summary(resolution)
	if selected_row:
		lines.extend(["", "**Resolved Row**"])
		rows: List[Tuple[str, Any]] = [("Row", selected_row)]
		for fact in row_facts:
			if ":" in fact:
				key, value = fact.split(":", 1)
				rows.append((key, value.strip()))
			else:
				rows.append(("Fact", fact))
		_append_kv_table(lines, rows)
	candidate_frames = [_clean_dict(frame) for frame in _clean_list(arbitration.get("candidate_frames"))]
	rejected_frames = [_clean_dict(frame) for frame in _clean_list(arbitration.get("rejected_frames"))]
	lines.extend(["", f"**Candidate Frames ({len(candidate_frames)})**"])
	_append_frame_table(lines, candidate_frames)
	lines.extend(["", f"**Rejected Frames ({len(rejected_frames)})**"])
	_append_frame_table(lines, rejected_frames)
	reason = _clean_text(arbitration.get("reason") or resolution.get("reason"))
	if reason:
		lines.extend(["", "**Authority Reason**", "", reason])
	return "\n".join(lines).strip()


def _inspection_contract(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	raw_message: str,
	trace_payload: Dict[str, Any],
	answer_text: str,
) -> Dict[str, Any]:
	arbitration = _clean_dict(trace_payload.get("frame_arbitration"))
	observability = _clean_dict(trace_payload.get("authority_observability"))
	return {
		"type": INSPECTION_PAYLOAD_TYPE,
		"contract_version": CONTRACT_VERSION,
		"request_id": _clean_text(request_id),
		"session_id": _clean_text(session_id),
		"user_id": _clean_text(user_id),
		"site_name": _clean_text(site_name),
		"raw_message": _clean_text(raw_message),
		"inspected_trace_request_id": _clean_text(trace_payload.get("request_id")),
		"trace_available": bool(trace_payload),
		"trace_status": _clean_text(arbitration.get("status")),
		"relation": _clean_text(arbitration.get("relation") or observability.get("relation")),
		"requested_object_label": _clean_text(arbitration.get("requested_object_label") or observability.get("requested_object_label")),
		"selected_frame_id": _clean_text(arbitration.get("selected_frame_id") or observability.get("selected_frame_id")),
		"selected_business_object_type": _clean_text(
			arbitration.get("selected_business_object_type") or observability.get("selected_business_object_type")
		),
		"selected_recovery_source": _clean_text(arbitration.get("selected_recovery_source") or observability.get("selected_recovery_source")),
		"candidate_frame_count": len(_clean_list(arbitration.get("candidate_frames"))),
		"rejected_frame_count": len(_clean_list(arbitration.get("rejected_frames"))),
		"answer_preview": answer_text[:500],
		"created_at_unix": time.time(),
	}


def try_activate_visible_context_trace_inspection_response(
	*,
	session_doc: Any,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str = "",
	raw_message: str,
	user_message_already_appended: bool = False,
	append_message: AppendMessage,
	append_tool_payload: AppendToolPayload,
	assistant_text_payload: AssistantTextPayload,
	save_session: SaveSession,
	additional_tool_payloads: List[Dict[str, Any]] | None = None,
) -> Tuple[bool, Dict[str, Any] | None]:
	if not visible_context_trace_inspection_requested(raw_message):
		return False, None
	trace_payload = latest_visible_context_authority_trace(session_doc)
	answer_text = render_visible_context_authority_trace(trace_payload)
	if not user_message_already_appended:
		append_message(session_doc, "user", raw_message)
	for payload in additional_tool_payloads or []:
		if isinstance(payload, dict) and payload:
			append_tool_payload(session_doc, payload)
	inspection_payload = _inspection_contract(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		raw_message=raw_message,
		trace_payload=trace_payload,
		answer_text=answer_text,
	)
	append_tool_payload(session_doc, inspection_payload)
	execution_path_payload = {
		"type": "qwen_execution_path",
		"contract_version": CONTRACT_VERSION,
		"request_id": _clean_text(request_id),
		"path": "visible_context_trace_inspection",
		"reason": "The user explicitly requested inspection of the latest visible-context authority trace.",
		"requires_runtime": False,
		"grounded_required": False,
	}
	append_tool_payload(session_doc, execution_path_payload)
	append_message(session_doc, "assistant", assistant_text_payload(answer_text))
	save_session(session_doc, ignore_permissions=False)
	return True, {
		"ok": True,
		"request_id": request_id,
		"mode": "visible_context_trace_inspection",
		"agent_meta": {
			"engine": "visible_context_trace_inspection",
			"trace_available": bool(trace_payload),
			"status": _clean_text(_clean_dict(trace_payload.get("frame_arbitration")).get("status")),
		},
	}
