from __future__ import annotations

import datetime as dt
import json
import re
import time
import uuid
from typing import Any, Dict, List, Tuple

import frappe

from ai_assistant_ui.qwen_chat.capability_adapters import render_local_followup
from ai_assistant_ui.qwen_chat.contracts import (
	build_audit_envelope,
	build_execution_path,
	build_followup_resolution,
	build_grounded_turn_context,
	build_interaction_contract,
	is_self_contained_business_request,
)
from ai_assistant_ui.qwen_chat.metadata import resolve_followup_report_switch
from ai_assistant_ui.qwen_chat.runtime_client import QwenRuntimeClientError, call_qwen_runtime_chat

QWEN_SESSION_DOCTYPE = "Qwen Chat Session"
VISIBLE_ROLES = {"user", "assistant"}


def _append_message(session_doc, role: str, content: str) -> None:
	session_doc.append("messages", {"role": str(role or "").strip(), "content": str(content or "")})


def _append_tool_payload(session_doc, payload: Dict[str, Any]) -> None:
	_append_message(session_doc, "tool", _safe_json_dumps(payload))


def _safe_json_dumps(obj: Any) -> str:
	try:
		return json.dumps(obj, ensure_ascii=False, default=str)
	except Exception:
		try:
			return json.dumps({"type": "text", "text": str(obj or "")}, ensure_ascii=False)
		except Exception:
			return "{\"type\":\"text\",\"text\":\"Internal serialization error.\"}"


def _extract_markdown_title(text: str) -> str:
	for raw_line in str(text or "").splitlines():
		line = raw_line.strip()
		if not line:
			continue
		if line.startswith("### "):
			return line[4:].strip()
		if line.startswith("## "):
			return line[3:].strip()
		if line.startswith("# "):
			return line[2:].strip()
		if line.startswith("**") and line.endswith("**") and len(line) > 4:
			return line[2:-2].strip()
	return ""


def _is_markdown_table_separator(line: str) -> bool:
	return bool(re.match(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$", str(line or "")))


def _split_markdown_table_cells(line: str) -> List[str]:
	value = str(line or "").strip()
	if value.startswith("|"):
		value = value[1:]
	if value.endswith("|"):
		value = value[:-1]
	return [cell.strip() for cell in value.split("|")]


def _unwrap_markdown_emphasis(value: str) -> Tuple[str, str, str]:
	text = str(value or "").strip()
	match = re.fullmatch(r"(\*{0,2})(.*?)(\*{0,2})", text)
	if not match:
		return "", text, ""
	return match.group(1), match.group(2).strip(), match.group(3)


def _detect_amount_unit(value: str) -> str:
	_, inner, _ = _unwrap_markdown_emphasis(value)
	lower = inner.lower().strip()
	if not lower:
		return ""
	if re.fullmatch(r"mmk\s*-?\d[\d,]*(?:\.\d+)?\s*million mmk", lower):
		return "million_mmk"
	if re.fullmatch(r"-?\d[\d,]*(?:\.\d+)?\s*million mmk", lower):
		return "million_mmk"
	if re.fullmatch(r"mmk\s*-?\d[\d,]*(?:\.\d+)?", lower):
		return "mmk"
	if re.fullmatch(r"-?\d[\d,]*(?:\.\d+)?\s*mmk", lower):
		return "mmk"
	return ""


def _header_unit_mode(header: str) -> str:
	value = str(header or "").strip().lower()
	if "million mmk" in value:
		return "million_mmk"
	if "mmk" in value:
		return "mmk"
	return ""


def _normalize_amount_cell(value: str, unit_mode: str) -> str:
	if unit_mode not in {"mmk", "million_mmk"}:
		return str(value or "").strip()

	lead, inner, trail = _unwrap_markdown_emphasis(value)
	text = inner
	text = re.sub(r"^\s*mmk\s+", "", text, flags=re.IGNORECASE)
	text = re.sub(r"\s+million mmk\s*$", "", text, flags=re.IGNORECASE)
	text = re.sub(r"\s+mmk\s*$", "", text, flags=re.IGNORECASE)
	text = text.strip()
	if not text:
		return str(value or "").strip()
	return f"{lead}{text}{trail}"


def _normalize_table_headers_and_rows(headers: List[str], body_lines: List[str]) -> Tuple[List[str], List[str]]:
	if not headers or not body_lines:
		return headers, body_lines

	row_cells: List[List[str]] = [_split_markdown_table_cells(line) for line in body_lines]
	normalized_headers = list(headers)
	normalized_rows = [list(cells) for cells in row_cells]

	for idx, header in enumerate(headers):
		header_mode = _header_unit_mode(header)
		column_values = [cells[idx] for cells in row_cells if idx < len(cells) and str(cells[idx] or "").strip()]
		detected_modes = [mode for mode in (_detect_amount_unit(cell) for cell in column_values) if mode]
		target_mode = header_mode
		if not target_mode and detected_modes:
			target_mode = "million_mmk" if "million_mmk" in detected_modes else "mmk"
		if target_mode not in {"mmk", "million_mmk"}:
			continue

		header_text = str(header or "").strip()
		if not header_mode:
			suffix = "(Million MMK)" if target_mode == "million_mmk" else "(MMK)"
			normalized_headers[idx] = f"{header_text} {suffix}".strip()

		for row_idx, cells in enumerate(normalized_rows):
			if idx >= len(cells):
				continue
			cells[idx] = _normalize_amount_cell(cells[idx], target_mode)

	return normalized_headers, ["| " + " | ".join(cells) + " |" for cells in normalized_rows]


def _normalize_inline_amount_units(line: str) -> str:
	def repl(match: re.Match[str]) -> str:
		lead = match.group(1) or ""
		number = match.group(2) or ""
		million = bool(match.group(3))
		trail = match.group(4) or ""
		if million:
			return f"{lead}{number} Million MMK{trail}"
		return f"{lead}{number} MMK{trail}"

	normalized = re.sub(
		r"(\*{0,2})MMK\s+(-?\d[\d,]*(?:\.\d+)?)(?:\s+(Million MMK))?(\*{0,2})",
		repl,
		str(line or ""),
		flags=re.IGNORECASE,
	)
	return re.sub(r"\bMillion MMK\s+MMK\b", "Million MMK", normalized, flags=re.IGNORECASE)


def _normalize_markdown_units(text: str) -> str:
	lines = str(text or "").replace("\r\n", "\n").split("\n")
	out: List[str] = []
	i = 0
	while i < len(lines):
		line = str(lines[i] or "")
		next_line = str(lines[i + 1] or "") if i + 1 < len(lines) else ""
		if "|" in line and _is_markdown_table_separator(next_line):
			headers = _split_markdown_table_cells(line)
			body_lines: List[str] = []
			i += 2
			while i < len(lines):
				body = str(lines[i] or "")
				if not body.strip() or "|" not in body:
					break
				body_lines.append(body)
				i += 1
			normalized_headers, normalized_body_lines = _normalize_table_headers_and_rows(headers, body_lines)
			out.append("| " + " | ".join(normalized_headers) + " |")
			out.append(next_line)
			out.extend(normalized_body_lines)
			continue
		out.append(_normalize_inline_amount_units(line))
		i += 1
	return "\n".join(out).strip()


def _extract_markdown_tables(text: str) -> List[Dict[str, Any]]:
	lines = str(text or "").replace("\r\n", "\n").split("\n")
	tables: List[Dict[str, Any]] = []
	i = 0
	while i < len(lines):
		line = str(lines[i] or "")
		next_line = str(lines[i + 1] or "") if i + 1 < len(lines) else ""
		if "|" in line and _is_markdown_table_separator(next_line):
			headers = _split_markdown_table_cells(line)
			rows: List[Dict[str, str]] = []
			i += 2
			while i < len(lines):
				body = str(lines[i] or "")
				if not body.strip() or "|" not in body:
					break
				cells = _split_markdown_table_cells(body)
				row = {
					headers[idx] if idx < len(headers) else f"col_{idx + 1}": cells[idx] if idx < len(cells) else ""
					for idx in range(len(headers))
				}
				rows.append(row)
				i += 1
			tables.append({"headers": headers, "rows": rows})
			continue
		i += 1
	return tables


def _assistant_text_payload(text: str) -> str:
	clean = _normalize_markdown_units(str(text or "").strip())
	payload: Dict[str, Any] = {
		"type": "text",
		"text": clean,
		"format": "markdown",
	}
	title = _extract_markdown_title(clean)
	if title:
		payload["title"] = title
	tables = _extract_markdown_tables(clean)
	if tables:
		payload["tables"] = tables
	return _safe_json_dumps(payload)


def _build_markdown_table(headers: List[str], rows: List[Dict[str, Any]]) -> str:
	clean_headers = [str(header or "").strip() for header in headers if str(header or "").strip()]
	if not clean_headers:
		return ""
	separator = "| " + " | ".join("---" for _ in clean_headers) + " |"
	lines = ["| " + " | ".join(clean_headers) + " |", separator]
	for row in rows:
		if not isinstance(row, dict):
			continue
		cells = [str(row.get(header) or "").strip() for header in clean_headers]
		lines.append("| " + " | ".join(cells) + " |")
	return "\n".join(lines).strip()


def _ensure_table_from_grounded_context(
	text: str,
	assistant_payload: Dict[str, Any],
	grounded_turn: Dict[str, Any],
) -> str:
	current = str(text or "").strip()
	if current and _extract_markdown_tables(current):
		return current
	headers = grounded_turn.get("returned_schema")
	rows = grounded_turn.get("table_rows")
	if not isinstance(headers, list) or not isinstance(rows, list):
		return current
	table_block = _build_markdown_table(headers, rows)
	if not table_block:
		return current
	if not current:
		title = str(assistant_payload.get("title") or grounded_turn.get("source_name") or "").strip()
		if title:
			return f"## {title}\n\n{table_block}".strip()
		return table_block
	return f"{current}\n\n{table_block}".strip()


def _visible_message_text(role: str, content: str) -> str:
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


def _parse_payload(content: str) -> Dict[str, Any]:
	try:
		obj = json.loads(str(content or ""))
	except Exception:
		return {}
	return obj if isinstance(obj, dict) else {}


def _positions_to_skip_for_runtime_context(session_doc) -> set[int]:
	messages = list(session_doc.get("messages") or [])
	skip: set[int] = set()
	for pos, message in enumerate(messages):
		if str(message.role or "").strip().lower() != "tool":
			continue
		payload = _parse_payload(str(message.content or ""))
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
			if role in VISIBLE_ROLES:
				skip.add(scan)
				visible_found += 1
			scan -= 1
	return skip


def _recent_messages(session_doc, limit: int = 10) -> List[Dict[str, str]]:
	out: List[Dict[str, str]] = []
	skip_positions = _positions_to_skip_for_runtime_context(session_doc)
	for pos, m in reversed(list(enumerate(session_doc.get("messages") or []))):
		if pos in skip_positions:
			continue
		role = str(m.role or "").strip().lower()
		if role not in VISIBLE_ROLES:
			continue
		content = _visible_message_text(role, str(m.content or ""))
		if not content:
			continue
		out.append({"role": role, "content": content[:2000]})
		if len(out) >= max(1, int(limit)):
			break
	return list(reversed(out))


def _latest_assistant_payload(session_doc) -> Dict[str, Any]:
	for m in reversed(session_doc.get("messages") or []):
		if str(m.role or "").strip().lower() != "assistant":
			continue
		payload = _parse_payload(str(m.content or ""))
		if payload:
			return payload
		text = str(m.content or "").strip()
		if text:
			return {"type": "text", "text": text}
	return {}


def _latest_display_preferences(session_doc, requested_modes: List[str] | None = None) -> Dict[str, bool]:
	requested = {
		str(mode or "").strip()
		for mode in (requested_modes or [])
		if str(mode or "").strip()
	}
	payload = _latest_assistant_payload(session_doc)
	text = str(payload.get("text") or "").strip().lower()
	has_tables = bool(payload.get("tables"))
	return {
		"million": "presentation_transform" in requested or "million mmk" in text,
		"table": "table_presentation" in requested or has_tables,
	}


def _compile_capability_requery_message(
	session_doc,
	*,
	raw_message: str,
	followup_resolution,
	grounded_turn: Dict[str, Any],
) -> str:
	switch = resolve_followup_report_switch(
		getattr(followup_resolution, "requested_modes", []) or [],
		str(grounded_turn.get("source_name") or "").strip(),
	)
	target_report = str(getattr(followup_resolution, "target_report", "") or switch.get("target_report") or "").strip()
	if not target_report:
		return str(raw_message or "").strip()

	filters = grounded_turn.get("filters") if isinstance(grounded_turn.get("filters"), dict) else {}
	date_range = grounded_turn.get("date_range") if isinstance(grounded_turn.get("date_range"), dict) else {}
	company = str(filters.get("company") or grounded_turn.get("company") or "").strip()
	report_date = str(date_range.get("report_date") or filters.get("report_date") or "").strip()
	from_date = str(date_range.get("from_date") or filters.get("from_date") or "").strip()
	to_date = str(date_range.get("to_date") or filters.get("to_date") or "").strip()
	prefs = _latest_display_preferences(session_doc, getattr(followup_resolution, "requested_modes", []) or [])
	hint = str(switch.get("requery_prompt_hint") or "").strip()

	parts = [f"Use the report `{target_report}`."]
	if company:
		parts.append(f'Use company "{company}".')
	if report_date:
		parts.append(f"Use report_date {report_date}.")
	elif from_date and to_date:
		parts.append(f"Use the date range from {from_date} to {to_date}.")
	if hint:
		parts.append(hint)
	if prefs.get("million"):
		parts.append("Present all amounts in Million MMK.")
	if prefs.get("table"):
		parts.append("Return the result as a table.")
	parts.append(f"User request: {str(raw_message or '').strip()}")
	return " ".join(part for part in parts if part).strip()


def _latest_qwen_trace_payload(session_doc) -> Dict[str, Any]:
	for m in reversed(session_doc.get("messages") or []):
		if str(m.role or "").strip().lower() != "tool":
			continue
		payload = _parse_payload(str(m.content or ""))
		if str(payload.get("type") or "").strip().lower() == "qwen_runtime_trace":
			return payload
	return {}


def _latest_grounded_assistant_context(session_doc) -> Tuple[Dict[str, Any], Dict[str, Any]]:
	messages = list(session_doc.get("messages") or [])
	for idx in range(len(messages) - 1, -1, -1):
		message = messages[idx]
		if str(message.role or "").strip().lower() != "tool":
			continue
		trace = _parse_payload(str(message.content or ""))
		if str(trace.get("type") or "").strip().lower() != "qwen_runtime_trace":
			continue
		if not bool(trace.get("ok")):
			continue
		for prev_idx in range(idx - 1, -1, -1):
			prev = messages[prev_idx]
			role = str(prev.role or "").strip().lower()
			if role == "assistant":
				payload = _parse_payload(str(prev.content or ""))
				if payload:
					return payload, trace
				text = str(prev.content or "").strip()
				if text:
					return {"type": "text", "text": text}, trace
				break
			if role == "user":
				break
	return {}, {}


def _latest_grounded_turn_contract(session_doc) -> Dict[str, Any]:
	for m in reversed(session_doc.get("messages") or []):
		if str(m.role or "").strip().lower() != "tool":
			continue
		payload = _parse_payload(str(m.content or ""))
		if str(payload.get("type") or "").strip().lower() == "qwen_grounded_turn_context":
			return payload
	return {}


def _format_million_value(raw: str) -> str:
	negative = raw.startswith("-")
	numeric = raw[1:] if negative else raw
	value = float(numeric.replace(",", ""))
	scaled = value / 1_000_000.0
	text = f"{scaled:,.2f}".rstrip("0").rstrip(".")
	return f"-{text}" if negative else text


def _currency_like_header(header: str) -> bool:
	value = str(header or "").strip().lower()
	return any(token in value for token in ("sales", "revenue", "amount", "outstanding", "value", "mmk"))


def _convert_summary_line_to_million(line: str) -> str:
	text = str(line or "")
	lower = text.lower()
	if "million" in lower:
		return text
	if not any(token in lower for token in ("sales", "revenue", "amount", "outstanding", "value", "mmk")):
		return text
	match = re.search(
		r"(\*{0,2})(?:MMK\s+)?(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?)(?:\s+MMK)?(\*{0,2})",
		text,
		flags=re.IGNORECASE,
	)
	if not match:
		return text
	scaled = _format_million_value(match.group(2))
	replacement = f"{match.group(1)}{scaled} Million MMK{match.group(3)}"
	return text[: match.start()] + replacement + text[match.end() :]


def _transform_markdown_to_million(text: str) -> str:
	lines = str(text or "").replace("\r\n", "\n").split("\n")
	out: List[str] = []
	i = 0
	while i < len(lines):
		line = str(lines[i] or "")
		next_line = str(lines[i + 1] or "") if i + 1 < len(lines) else ""
		if "|" in line and _is_markdown_table_separator(next_line):
			headers = _split_markdown_table_cells(line)
			scaled_headers = []
			scale_cols = set()
			for idx, header in enumerate(headers):
				if _currency_like_header(header):
					scale_cols.add(idx)
					if "million" not in header.lower():
						header = header.replace("(MMK)", "(Million MMK)")
						if header == headers[idx]:
							header = f"{header} (Million MMK)"
				scaled_headers.append(header)
			out.append("| " + " | ".join(scaled_headers) + " |")
			out.append(next_line)
			i += 2
			while i < len(lines):
				body = str(lines[i] or "")
				if not body.strip() or "|" not in body:
					break
				cells = _split_markdown_table_cells(body)
				for idx in scale_cols:
					if idx >= len(cells):
						continue
					cell = cells[idx]
					match = re.fullmatch(r"(\*{0,2})(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?)(\*{0,2})", cell.strip())
					if not match:
						continue
					cells[idx] = f"{match.group(1)}{_format_million_value(match.group(2))}{match.group(3)}"
				out.append("| " + " | ".join(cells) + " |")
				i += 1
			continue
		out.append(_convert_summary_line_to_million(line))
		i += 1
	return "\n".join(out).strip()


def _local_transform_trace_message(request_id: str, source_request_id: str, transforms: List[str]) -> str:
	return _tool_trace_message(
		request_id=request_id,
		ok=True,
		tool_trace=[
			{
				"tool": "local_transform",
				"status": "ok",
				"detail": ",".join(str(x or "").strip() for x in transforms if str(x or "").strip()),
				"detail_obj": {"transforms": transforms, "source_request_id": source_request_id},
			}
		],
		agent_meta={"engine": "local_transform", "transforms": transforms, "source_request_id": source_request_id},
		error="",
		runtime_latency_ms=0,
	)


def _try_local_followup_transform(
	session_doc,
	*,
	request_id: str,
	followup_resolution,
) -> Tuple[bool, Dict[str, Any]] | None:
	requested_modes = {
		str(mode or "").strip()
		for mode in getattr(followup_resolution, "requested_modes", []) or []
		if str(mode or "").strip()
	}
	target_dimension = str(getattr(followup_resolution, "target_dimension", "") or "").strip()
	if not requested_modes.intersection({"presentation_transform", "table_presentation", "aging_bucket_view", "dimension_breakdown"}):
		return None
	assistant_payload, trace = _latest_grounded_assistant_context(session_doc)
	grounded_turn = _latest_grounded_turn_contract(session_doc)
	if not assistant_payload or not trace:
		return None
	text = str(assistant_payload.get("text") or "").strip()
	if not text and not grounded_turn:
		return None
	transformed = text
	applied_transforms: List[str] = []
	display_preferences = _latest_display_preferences(
		session_doc,
		getattr(followup_resolution, "requested_modes", []) or [],
	)

	if "aging_bucket_view" in requested_modes:
		aging_view = render_local_followup("aging_bucket_view", grounded_turn, display_preferences)
		if aging_view:
			transformed = aging_view
			applied_transforms.append("aging_bucket_view")

	if "dimension_breakdown" in requested_modes:
		breakdown_view = render_local_followup(
			"dimension_breakdown",
			grounded_turn,
			display_preferences,
			target_dimension=target_dimension,
		)
		if breakdown_view:
			transformed = breakdown_view
			applied_transforms.append("dimension_breakdown")

	if "table_presentation" in requested_modes:
		with_table = _ensure_table_from_grounded_context(transformed, assistant_payload, grounded_turn)
		if with_table and with_table != transformed:
			transformed = with_table
			applied_transforms.append("table_presentation")

	if "presentation_transform" in requested_modes:
		scaled = _transform_markdown_to_million(transformed)
		if scaled and scaled != transformed:
			transformed = scaled
			applied_transforms.append("presentation_transform")

	if not transformed or not applied_transforms:
		return None

	_append_message(session_doc, "assistant", _assistant_text_payload(transformed))
	_append_message(
		session_doc,
		"tool",
		_local_transform_trace_message(
			request_id=request_id,
			source_request_id=str(trace.get("request_id") or "").strip(),
			transforms=applied_transforms,
		),
	)
	session_doc.save(ignore_permissions=False)
	return True, {"ok": True, "request_id": request_id, "agent_meta": {"engine": "local_transform", "transforms": applied_transforms}}


def _tool_trace_message(
	*,
	request_id: str,
	ok: bool,
	tool_trace: List[Dict[str, Any]],
	agent_meta: Dict[str, Any],
	error: str,
	runtime_latency_ms: int,
) -> str:
	return _safe_json_dumps(
		_tool_trace_payload(
			request_id=request_id,
			ok=ok,
			tool_trace=tool_trace,
			agent_meta=agent_meta,
			error=error,
			runtime_latency_ms=runtime_latency_ms,
		)
	)


def _tool_trace_payload(
	*,
	request_id: str,
	ok: bool,
	tool_trace: List[Dict[str, Any]],
	agent_meta: Dict[str, Any],
	error: str,
	runtime_latency_ms: int,
) -> Dict[str, Any]:
	return {
		"type": "qwen_runtime_trace",
		"request_id": str(request_id or "").strip(),
		"ok": bool(ok),
		"tool_trace": list(tool_trace or []),
		"agent_meta": agent_meta if isinstance(agent_meta, dict) else {},
		"error": str(error or "").strip(),
		"runtime_latency_ms": int(max(0, runtime_latency_ms)),
		"created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
	}


def _safe_runtime_failure_message(exc: Exception) -> str:
	raw = str(exc or "").strip()
	if raw:
		return f"Qwen runtime is unavailable right now. {raw}"
	return "Qwen runtime is unavailable right now. Please try again."


def handle_qwen_user_message(*, session_name: str, message: str, user: str) -> Tuple[bool, Dict[str, Any]]:
	session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, session_name)
	site_name = str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()
	request_id = uuid.uuid4().hex
	msg = str(message or "").strip()
	latest_grounded_turn = _latest_grounded_turn_contract(session_doc)
	latest_grounded_turn_available = bool(latest_grounded_turn.get("grounded")) or bool(
		_latest_grounded_assistant_context(session_doc)[0]
	)
	interaction_contract = build_interaction_contract(
		request_id=request_id,
		session_id=session_name,
		user_id=user,
		site_name=site_name,
		raw_message=msg,
	)
	followup_resolution = build_followup_resolution(
		request_id=request_id,
		message=msg,
		latest_grounded_turn_available=latest_grounded_turn_available,
		latest_grounded_turn=latest_grounded_turn,
	)
	recent_messages = (
		[]
		if followup_resolution.mode == "new_query" and bool(followup_resolution.self_contained)
		else _recent_messages(session_doc, limit=10)
	)
	runtime_message = msg
	if followup_resolution.mode == "capability_requery":
		runtime_message = _compile_capability_requery_message(
			session_doc,
			raw_message=msg,
			followup_resolution=followup_resolution,
			grounded_turn=latest_grounded_turn,
		)
		recent_messages = []

	if (session_doc.title or "").strip() in ("", "New Qwen Chat"):
		session_doc.title = (msg[:60] + "…") if len(msg) > 60 else msg

	_append_message(session_doc, "user", msg)
	_append_tool_payload(session_doc, interaction_contract.to_payload())
	_append_tool_payload(session_doc, followup_resolution.to_payload())

	local_transform = None
	if followup_resolution.mode == "local_grounded_transform":
		local_transform = _try_local_followup_transform(
			session_doc,
			request_id=request_id,
			followup_resolution=followup_resolution,
		)
	if local_transform:
		execution_path = build_execution_path(
			request_id=request_id,
			followup_resolution=followup_resolution,
			local_transform_applied=True,
		)
		_append_tool_payload(
			session_doc,
			execution_path.to_payload(),
		)
		_append_tool_payload(
			session_doc,
			build_audit_envelope(
				interaction_contract=interaction_contract,
				followup_resolution=followup_resolution,
				execution_path=execution_path,
				runtime_trace_payload=_latest_qwen_trace_payload(session_doc),
				grounded_turn_context=latest_grounded_turn,
				answer_text=str(_latest_assistant_payload(session_doc).get("text") or ""),
			).to_payload(),
		)
		session_doc.save(ignore_permissions=False)
		return local_transform

	execution_path = build_execution_path(
		request_id=request_id,
		followup_resolution=followup_resolution,
		local_transform_applied=False,
	)
	_append_tool_payload(
		session_doc,
		execution_path.to_payload(),
	)
	start = time.perf_counter()
	try:
		runtime_payload = call_qwen_runtime_chat(
			session_id=session_name,
			user_id=user,
			site_name=site_name,
			message=runtime_message,
			recent_messages=recent_messages,
			mode="read_only",
			request_id=request_id,
		)
		runtime_latency_ms = int((time.perf_counter() - start) * 1000)
	except QwenRuntimeClientError as exc:
		runtime_latency_ms = int((time.perf_counter() - start) * 1000)
		error_text = _safe_runtime_failure_message(exc)
		trace_payload = _tool_trace_payload(
			request_id=request_id,
			ok=False,
			tool_trace=[],
			agent_meta={"engine": "unavailable", "mode": "read_only"},
			error=str(exc),
			runtime_latency_ms=runtime_latency_ms,
		)
		_append_message(session_doc, "assistant", _assistant_text_payload(error_text))
		_append_tool_payload(session_doc, trace_payload)
		_append_tool_payload(
			session_doc,
			build_audit_envelope(
				interaction_contract=interaction_contract,
				followup_resolution=followup_resolution,
				execution_path=execution_path,
				runtime_trace_payload=trace_payload,
				grounded_turn_context={},
				answer_text=error_text,
			).to_payload(),
		)
		session_doc.save(ignore_permissions=False)
		return True, {"ok": False, "request_id": request_id, "error": str(exc)}

	ok = bool(runtime_payload.get("ok"))
	answer_text = str(runtime_payload.get("answer_text") or "").strip()
	tool_trace = runtime_payload.get("tool_trace") if isinstance(runtime_payload.get("tool_trace"), list) else []
	agent_meta = runtime_payload.get("agent_meta") if isinstance(runtime_payload.get("agent_meta"), dict) else {}
	error = str(runtime_payload.get("error") or "").strip()

	if not answer_text:
		if error:
			answer_text = f"Qwen runtime could not complete the request. {error}"
		else:
			answer_text = "Qwen runtime returned no answer."

	_append_message(session_doc, "assistant", _assistant_text_payload(answer_text))
	_append_message(
		session_doc,
		"tool",
		_tool_trace_message(
			request_id=request_id,
			ok=ok,
			tool_trace=tool_trace,
			agent_meta=agent_meta,
			error=error,
			runtime_latency_ms=runtime_latency_ms,
		),
	)
	runtime_trace_payload = _latest_qwen_trace_payload(session_doc)
	assistant_payload = _latest_assistant_payload(session_doc)
	grounded_turn_context = build_grounded_turn_context(
		request_id=request_id,
		interaction_contract=interaction_contract,
		assistant_payload=assistant_payload,
		runtime_payload={
			**runtime_trace_payload,
			"request_id": request_id,
		},
	)
	grounded_turn_payload: Dict[str, Any] = {}
	if grounded_turn_context and grounded_turn_context.grounded:
		grounded_turn_payload = grounded_turn_context.to_payload()
		_append_tool_payload(session_doc, grounded_turn_payload)
	_append_tool_payload(
		session_doc,
		build_audit_envelope(
			interaction_contract=interaction_contract,
			followup_resolution=followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload=runtime_trace_payload,
			grounded_turn_context=grounded_turn_payload,
			answer_text=answer_text,
		).to_payload(),
	)
	session_doc.save(ignore_permissions=False)
	return True, {"ok": ok, "request_id": request_id, "error": error, "agent_meta": agent_meta}
