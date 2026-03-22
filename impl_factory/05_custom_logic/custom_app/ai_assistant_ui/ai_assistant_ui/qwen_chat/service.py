from __future__ import annotations

import datetime as dt
import hashlib
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
	build_response_policy_contract,
	is_self_contained_business_request,
)
from ai_assistant_ui.qwen_chat.followup_interpreter import is_safe_local_compatibility_intent
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import execute_compiled_fresh_query_message
from ai_assistant_ui.qwen_chat.metadata import resolve_followup_report_switch
from ai_assistant_ui.qwen_chat.runtime_client import QwenRuntimeClientError, call_qwen_runtime_chat
from ai_assistant_ui.qwen_chat.semantic_interpreter import interpret_followup_semantically

QWEN_SESSION_DOCTYPE = "Qwen Chat Session"
VISIBLE_ROLES = {"user", "assistant"}


def _compiled_first_turn_rollout_enabled() -> bool:
	try:
		return bool((getattr(frappe, "conf", None) or {}).get("qwen_enable_compiled_first_turn", False))
	except Exception:
		return False


def _conf_get(key: str, default: Any = None) -> Any:
	try:
		return (getattr(frappe, "conf", None) or {}).get(key, default)
	except Exception:
		return default


def _conf_string_list(key: str) -> List[str]:
	raw = _conf_get(key, [])
	if isinstance(raw, (list, tuple, set)):
		return [str(item or "").strip() for item in raw if str(item or "").strip()]
	if isinstance(raw, str):
		return [
			part
			for part in [str(item or "").strip() for item in re.split(r"[,\n;]+", raw)]
			if part
		]
	return []


def _compiled_first_turn_rollout_percentage() -> float:
	raw = _conf_get("qwen_compiled_first_turn_rollout_percentage", None)
	if raw is None:
		return 100.0
	if isinstance(raw, str) and not str(raw).strip():
		return 100.0
	try:
		return max(0.0, min(100.0, float(raw)))
	except Exception:
		return 100.0


def _compiled_first_turn_rollout_allow_users() -> List[str]:
	return list(dict.fromkeys(_conf_string_list("qwen_compiled_first_turn_rollout_users")))


def _compiled_first_turn_rollout_bucket(*, session_name: str, user: str, site_name: str) -> float:
	seed = f"{str(site_name or '').strip()}::{str(user or '').strip()}::{str(session_name or '').strip()}"
	digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
	bucket_basis_points = int(digest[:8], 16) % 10_000
	return round(bucket_basis_points / 100.0, 2)


def _compiled_first_turn_rollout_decision(
	*,
	session_name: str,
	user: str,
	site_name: str,
) -> Dict[str, Any]:
	master_enabled = _compiled_first_turn_rollout_enabled()
	rollout_percentage = _compiled_first_turn_rollout_percentage()
	allow_users = _compiled_first_turn_rollout_allow_users()
	canonical_user = str(user or "").strip()
	bucket = _compiled_first_turn_rollout_bucket(
		session_name=session_name,
		user=user,
		site_name=site_name,
	)
	if not master_enabled:
		return {
			"enabled": False,
			"reason": "master_disabled",
			"rollout_percentage": rollout_percentage,
			"rollout_bucket": bucket,
			"allow_users": allow_users,
		}
	if canonical_user and canonical_user in allow_users:
		return {
			"enabled": True,
			"reason": "allow_user",
			"rollout_percentage": rollout_percentage,
			"rollout_bucket": bucket,
			"allow_users": allow_users,
		}
	if rollout_percentage <= 0.0:
		return {
			"enabled": False,
			"reason": "percentage_zero",
			"rollout_percentage": rollout_percentage,
			"rollout_bucket": bucket,
			"allow_users": allow_users,
		}
	if rollout_percentage >= 100.0:
		return {
			"enabled": True,
			"reason": "percentage_full",
			"rollout_percentage": rollout_percentage,
			"rollout_bucket": bucket,
			"allow_users": allow_users,
		}
	return {
		"enabled": bucket < rollout_percentage,
		"reason": "percentage_canary",
		"rollout_percentage": rollout_percentage,
		"rollout_bucket": bucket,
		"allow_users": allow_users,
	}


def get_compiled_first_turn_rollout_status(
	session_name: str = "phase4-rollout-sample",
	user: str = "Administrator",
	site_name: str = "",
) -> Dict[str, Any]:
	decision = _compiled_first_turn_rollout_decision(
		session_name=str(session_name or "").strip(),
		user=str(user or "").strip(),
		site_name=str(site_name or "").strip(),
	)
	return {
		"master_enabled": _compiled_first_turn_rollout_enabled(),
		"rollout_percentage": _compiled_first_turn_rollout_percentage(),
		"allow_users": _compiled_first_turn_rollout_allow_users(),
		"sample_decision": decision,
	}


def _compiled_decision_message(result: Dict[str, Any]) -> str:
	pipeline = result.get("pipeline") if isinstance(result.get("pipeline"), dict) else {}
	compiler = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
	decision = str(compiler.get("decision") or "").strip()
	reason = str(compiler.get("compiler_reason") or "").strip()
	family_validation = result.get("family_validation") if isinstance(result.get("family_validation"), dict) else {}
	family_status = str(family_validation.get("status") or "").strip()
	family_errors = family_validation.get("errors") if isinstance(family_validation.get("errors"), list) else []
	family_warnings = family_validation.get("warnings") if isinstance(family_validation.get("warnings"), list) else []
	semantic = result.get("semantic_intent_validation") if isinstance(result.get("semantic_intent_validation"), dict) else {}
	semantic_status = str(semantic.get("status") or "").strip()
	semantic_errors = semantic.get("errors") if isinstance(semantic.get("errors"), list) else []
	semantic_warnings = semantic.get("warnings") if isinstance(semantic.get("warnings"), list) else []
	runtime_payload = result.get("runtime_payload") if isinstance(result.get("runtime_payload"), dict) else {}
	runtime_error = str(runtime_payload.get("error") or "").strip()
	runtime_answer = str(runtime_payload.get("answer_text") or "").strip()

	if decision == "clarify":
		if reason:
			return f"I need one more detail before I can run a governed ERP query.\n\n{reason}"
		return "I need one more detail before I can run a governed ERP query."
	if decision == "reject":
		if reason:
			return f"I can't execute this request within the approved ERP read path.\n\n{reason}"
		return "I can't execute this request within the approved ERP read path."
	if family_status == "clarify":
		detail = str((family_warnings or family_errors or ["The normalized business artifact needs clarification before display."])[0] or "").strip()
		return f"I need clarification before I can present a governed business artifact confidently.\n\n{detail}".strip()
	if family_status.startswith("reject"):
		detail = str((family_errors or ["The normalized business artifact did not pass governed validation."])[0] or "").strip()
		return f"I could not complete a governed business artifact confidently.\n\n{detail}".strip()
	if semantic_status == "clarify":
		detail = str((semantic_warnings or semantic_errors or ["The grounded result needs clarification before display."])[0] or "").strip()
		return f"I need clarification before I can present a governed result confidently.\n\n{detail}".strip()
	if semantic_status == "reject_semantically_inconsistent":
		detail = str((semantic_errors or ["The grounded result did not match the requested business intent."])[0] or "").strip()
		return f"I could not complete a semantically consistent grounded ERP answer.\n\n{detail}".strip()
	if runtime_answer:
		return runtime_answer
	if runtime_error:
		return _safe_runtime_failure_message(RuntimeError(runtime_error))
	return "I could not complete a governed ERP lookup."


def _handle_compiled_first_turn_result(
	*,
	session_doc,
	request_id: str,
	interaction_contract,
	followup_resolution,
	execution_path,
	result: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any]]:
	runtime_payload = result.get("runtime_payload") if isinstance(result.get("runtime_payload"), dict) else {}
	family_payload = result.get("family_validation") if isinstance(result.get("family_validation"), dict) else {}
	semantic_payload = result.get("semantic_intent_validation") if isinstance(result.get("semantic_intent_validation"), dict) else {}
	latency = result.get("phase4_latency_breakdown") if isinstance(result.get("phase4_latency_breakdown"), dict) else {}
	runtime_latency_ms = int(max(0, latency.get("runtime_execution_latency_ms") or 0))

	_append_compiled_attempt_artifacts(session_doc, result)

	answer_text = _compiled_decision_message(result)
	_append_message(session_doc, "assistant", _assistant_text_payload(answer_text))

	tool_trace = runtime_payload.get("tool_trace") if isinstance(runtime_payload.get("tool_trace"), list) else []
	agent_meta = runtime_payload.get("agent_meta") if isinstance(runtime_payload.get("agent_meta"), dict) else {}
	error = str(runtime_payload.get("error") or "").strip()
	if tool_trace or runtime_payload:
		_append_message(
			session_doc,
			"tool",
			_tool_trace_message(
				request_id=request_id,
				ok=bool(runtime_payload.get("ok")),
				tool_trace=tool_trace,
				agent_meta=agent_meta,
				error=error,
				runtime_latency_ms=runtime_latency_ms,
			),
		)

	grounded_turn_payload: Dict[str, Any] = {}
	if str(semantic_payload.get("status") or "").strip() == "pass" and bool(runtime_payload.get("ok")):
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
		if grounded_turn_context and grounded_turn_context.grounded:
			grounded_turn_payload = grounded_turn_context.to_payload()
			_append_tool_payload(session_doc, grounded_turn_payload)

	_append_tool_payload(
		session_doc,
		build_audit_envelope(
			interaction_contract=interaction_contract,
			followup_resolution=followup_resolution,
			execution_path=execution_path,
			runtime_trace_payload=_latest_qwen_trace_payload(session_doc),
			grounded_turn_context=grounded_turn_payload,
			answer_text=answer_text,
		).to_payload(),
	)
	session_doc.save(ignore_permissions=False)
	return True, {
		"ok": (
			bool(runtime_payload.get("ok"))
			and str(semantic_payload.get("status") or "").strip() == "pass"
			and str(family_payload.get("status") or "pass").strip() in {"", "pass", "not_run"}
		),
		"request_id": request_id,
		"mode": "compiled_first_turn",
		"agent_meta": agent_meta,
		"family_validation_status": str(family_payload.get("status") or "not_run").strip(),
		"semantic_validation_status": str(semantic_payload.get("status") or "not_run").strip(),
	}


def _append_compiled_attempt_artifacts(session_doc, result: Dict[str, Any]) -> None:
	pipeline = result.get("pipeline") if isinstance(result.get("pipeline"), dict) else {}
	normalized_family_artifact = result.get("normalized_family_artifact") if isinstance(result.get("normalized_family_artifact"), dict) else {}
	composite_family_artifacts = result.get("composite_family_artifacts") if isinstance(result.get("composite_family_artifacts"), list) else []
	composite_step_validations = result.get("composite_step_validations") if isinstance(result.get("composite_step_validations"), list) else []
	family_validation = result.get("family_validation") if isinstance(result.get("family_validation"), dict) else {}
	semantic_payload = result.get("semantic_intent_validation") if isinstance(result.get("semantic_intent_validation"), dict) else {}
	compiled_audit = result.get("compiled_execution_audit") if isinstance(result.get("compiled_execution_audit"), dict) else {}
	composite_execution_audit = result.get("composite_execution_audit") if isinstance(result.get("composite_execution_audit"), dict) else {}
	for key in ("fresh_query_interpretation", "fresh_query_compiler", "compiled_query_request", "composite_read_plan"):
		payload = pipeline.get(key)
		if isinstance(payload, dict) and payload:
			_append_tool_payload(session_doc, payload)
	if normalized_family_artifact:
		_append_tool_payload(session_doc, normalized_family_artifact)
	for payload in composite_family_artifacts:
		if isinstance(payload, dict) and payload:
			_append_tool_payload(session_doc, payload)
	for payload in composite_step_validations:
		if isinstance(payload, dict) and payload:
			_append_tool_payload(session_doc, payload)
	if family_validation:
		_append_tool_payload(session_doc, family_validation)
	if semantic_payload:
		_append_tool_payload(session_doc, semantic_payload)
	if compiled_audit:
		_append_tool_payload(session_doc, compiled_audit)
	if composite_execution_audit:
		_append_tool_payload(session_doc, composite_execution_audit)


def _compiled_rollout_fallback_reason(result: Dict[str, Any]) -> str:
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


def _compiled_rollout_fallback_payload(*, request_id: str, result: Dict[str, Any], reason: str) -> Dict[str, Any]:
	pipeline = result.get("pipeline") if isinstance(result.get("pipeline"), dict) else {}
	compiler = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
	compiled_audit = result.get("compiled_execution_audit") if isinstance(result.get("compiled_execution_audit"), dict) else {}
	return {
		"type": "qwen_compiled_rollout_fallback",
		"request_id": str(request_id or "").strip(),
		"reason": str(reason or "").strip(),
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


def _compiled_rollout_fallback_eligible(result: Dict[str, Any]) -> bool:
	reason = _compiled_rollout_fallback_reason(result)
	if not reason:
		return False
	pipeline = result.get("pipeline") if isinstance(result.get("pipeline"), dict) else {}
	compiler = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
	decision = str(compiler.get("decision") or "").strip()
	semantic_payload = result.get("semantic_intent_validation") if isinstance(result.get("semantic_intent_validation"), dict) else {}
	semantic_status = str(semantic_payload.get("status") or "").strip()
	return decision not in {"clarify", "reject"} and semantic_status not in {"clarify", "reject_semantically_inconsistent"}


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
	target_limit = int(max(0, getattr(followup_resolution, "target_limit", 0) or 0))
	sort_direction = str(getattr(followup_resolution, "sort_direction", "") or "").strip()
	if not requested_modes.intersection({"presentation_transform", "table_presentation", "aging_bucket_view", "dimension_breakdown", "sort_or_limit"}):
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
			assistant_payload=assistant_payload,
		)
		if breakdown_view:
			transformed = breakdown_view
			applied_transforms.append("dimension_breakdown")

	if "sort_or_limit" in requested_modes:
		sorted_view = render_local_followup(
			"sort_or_limit",
			grounded_turn,
			display_preferences,
			target_dimension=target_dimension,
			assistant_payload=assistant_payload,
			target_limit=target_limit,
			sort_direction=sort_direction,
		)
		if sorted_view:
			transformed = sorted_view
			applied_transforms.append("sort_or_limit")

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
	latest_assistant_payload = _latest_assistant_payload(session_doc)
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
	response_policy_contract = build_response_policy_contract(
		interaction_contract=interaction_contract,
	)
	semantic_intent = None
	allow_heuristic_fallback = True
	degraded_reason = ""
	semantic_payload = None
	if latest_grounded_turn_available and latest_grounded_turn:
		semantic_result = interpret_followup_semantically(
			request_id=request_id,
			session_id=session_name,
			user_id=user,
			site_name=site_name,
			message=msg,
			recent_messages=_recent_messages(session_doc, limit=6),
			latest_grounded_turn=latest_grounded_turn,
			latest_assistant_payload=latest_assistant_payload,
		)
		if semantic_result.status == "accepted" and semantic_result.intent is not None:
			semantic_intent = semantic_result.intent
			allow_heuristic_fallback = False
		else:
			allow_heuristic_fallback = is_safe_local_compatibility_intent(
				msg,
				grounded_turn=latest_grounded_turn,
			)
			degraded_reason = "Semantic follow-up interpretation did not meet governed confidence or runtime reliability requirements."
		semantic_payload = semantic_result.to_payload(
			fallback_used=bool(allow_heuristic_fallback and semantic_result.status != "accepted"),
			fallback_reason=(
				"Explicit compatibility fallback is allowed only for safe local presentation and ordering transforms."
				if allow_heuristic_fallback and semantic_result.status != "accepted"
				else "No heuristic fallback permitted; degraded follow-up handling remains explicit and auditable."
			),
		)
	followup_resolution = build_followup_resolution(
		request_id=request_id,
		message=msg,
		latest_grounded_turn_available=latest_grounded_turn_available,
		latest_grounded_turn=latest_grounded_turn,
		semantic_intent=semantic_intent,
		allow_heuristic_fallback=allow_heuristic_fallback,
		degraded_reason=degraded_reason,
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
	_append_tool_payload(session_doc, response_policy_contract.to_payload())
	if isinstance(semantic_payload, dict):
		_append_tool_payload(session_doc, semantic_payload)
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
	compiled_rollout = _compiled_first_turn_rollout_decision(
		session_name=session_name,
		user=user,
		site_name=site_name,
	)
	compiled_rollout_fallback: Dict[str, Any] | None = None
	if (
		bool(compiled_rollout.get("enabled"))
		and followup_resolution.mode == "new_query"
		and bool(followup_resolution.self_contained)
	):
		compiled_result = execute_compiled_fresh_query_message(
			session_id=session_name,
			user_id=user,
			site_name=site_name,
			message=msg,
			recent_messages=[],
		)
		if _compiled_rollout_fallback_eligible(compiled_result):
			reason = _compiled_rollout_fallback_reason(compiled_result)
			_append_compiled_attempt_artifacts(session_doc, compiled_result)
			compiled_rollout_fallback = _compiled_rollout_fallback_payload(
				request_id=request_id,
				result=compiled_result,
				reason=reason,
			)
			_append_tool_payload(session_doc, compiled_rollout_fallback)
		else:
			return _handle_compiled_first_turn_result(
				session_doc=session_doc,
				request_id=request_id,
				interaction_contract=interaction_contract,
				followup_resolution=followup_resolution,
				execution_path=execution_path,
				result=compiled_result,
			)
	start = time.perf_counter()
	try:
		runtime_payload = call_qwen_runtime_chat(
			session_id=session_name,
			user_id=user,
			site_name=site_name,
			message=runtime_message,
			recent_messages=recent_messages,
			response_policy=response_policy_contract.to_runtime_payload(),
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
		payload: Dict[str, Any] = {"ok": False, "request_id": request_id, "error": str(exc)}
		if isinstance(compiled_rollout_fallback, dict):
			payload["mode"] = "legacy_runtime_rollout_fallback"
			payload["compiled_rollout_fallback_reason"] = str(compiled_rollout_fallback.get("reason") or "").strip()
		return True, payload

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
	payload = {"ok": ok, "request_id": request_id, "error": error, "agent_meta": agent_meta}
	if isinstance(compiled_rollout_fallback, dict):
		payload["mode"] = "legacy_runtime_rollout_fallback"
		payload["compiled_rollout_fallback_reason"] = str(compiled_rollout_fallback.get("reason") or "").strip()
	return True, payload


def run_phase4_compiled_rollout_smoke() -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	original_flag = None
	original_percent = None
	original_users = None
	had_original = False
	had_percent = False
	had_users = False
	try:
		try:
			original_flag = (getattr(frappe, "conf", None) or {}).get(flag_key)
			original_percent = (getattr(frappe, "conf", None) or {}).get(percent_key)
			original_users = (getattr(frappe, "conf", None) or {}).get(users_key)
			had_original = flag_key in (getattr(frappe, "conf", None) or {})
			had_percent = percent_key in (getattr(frappe, "conf", None) or {})
			had_users = users_key in (getattr(frappe, "conf", None) or {})
		except Exception:
			original_flag = None
			original_percent = None
			original_users = None
			had_original = False
			had_percent = False
			had_users = False
		(getattr(frappe, "conf", None) or {})[flag_key] = True
		(getattr(frappe, "conf", None) or {})[percent_key] = 100
		(getattr(frappe, "conf", None) or {})[users_key] = []

		doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		doc.title = "Phase4 Compiled Rollout Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="How much payable amount do we have as of now",
				user="Administrator",
			)
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			tool_payloads = []
			for row in session_doc.get("messages") or []:
				if str(row.role or "").strip().lower() != "tool":
					continue
				payload_obj = _parse_payload(str(row.content or ""))
				if payload_obj:
					tool_payloads.append(payload_obj)
			type_names = [str(item.get("type") or "").strip() for item in tool_payloads if isinstance(item, dict)]
			has_compiled_audit = "qwen_compiled_execution_audit_contract" in type_names
			has_semantic_validation = "qwen_semantic_validation_outcome" in type_names
			has_grounded_turn = "qwen_grounded_turn_context" in type_names
			has_rollout_fallback = "qwen_compiled_rollout_fallback" in type_names
			if not ok or not isinstance(payload, dict):
				raise RuntimeError("Compiled rollout smoke failed: live service did not return an ok payload.")
			mode = str(payload.get("mode") or "").strip()
			if mode == "compiled_first_turn":
				if str(payload.get("semantic_validation_status") or "").strip() != "pass":
					raise RuntimeError("Compiled rollout smoke failed: semantic validation did not pass.")
				if not has_compiled_audit or not has_semantic_validation or not has_grounded_turn:
					raise RuntimeError("Compiled rollout smoke failed: required compiled-path audit artifacts were not persisted.")
			elif mode == "legacy_runtime_rollout_fallback":
				if not has_compiled_audit or not has_rollout_fallback:
					raise RuntimeError("Compiled rollout smoke failed: rollout fallback was not persisted auditably.")
			else:
				raise RuntimeError("Compiled rollout smoke failed: live service did not use compiled mode or audited fallback mode.")
			return {
				"ok": ok,
				"payload": payload,
				"session_name": doc.name,
				"persisted_tool_payload_types": type_names,
			}
		finally:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	finally:
		conf = getattr(frappe, "conf", None) or {}
		if had_original:
			conf[flag_key] = original_flag
		else:
			try:
				conf.pop(flag_key, None)
			except Exception:
				pass
		if had_percent:
			conf[percent_key] = original_percent
		else:
			try:
				conf.pop(percent_key, None)
			except Exception:
				pass
		if had_users:
			conf[users_key] = original_users
		else:
			try:
				conf.pop(users_key, None)
			except Exception:
				pass


def run_phase4_compiled_rollout_governance_selftests() -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	conf = getattr(frappe, "conf", None) or {}
	originals = {
		flag_key: conf.get(flag_key),
		percent_key: conf.get(percent_key),
		users_key: conf.get(users_key),
	}
	presence = {
		flag_key: flag_key in conf,
		percent_key: percent_key in conf,
		users_key: users_key in conf,
	}
	try:
		conf[flag_key] = False
		conf[percent_key] = 100
		conf[users_key] = []
		disabled = _compiled_first_turn_rollout_decision(
			session_name="phase4-rollout-disabled",
			user="Administrator",
			site_name="erpai_prj1",
		)
		if bool(disabled.get("enabled")):
			raise RuntimeError("Compiled rollout governance selftest failed: master-disabled rollout still enabled.")

		conf[flag_key] = True
		conf[percent_key] = 0
		conf[users_key] = []
		zero_percent = _compiled_first_turn_rollout_decision(
			session_name="phase4-rollout-zero",
			user="User A",
			site_name="erpai_prj1",
		)
		if bool(zero_percent.get("enabled")):
			raise RuntimeError("Compiled rollout governance selftest failed: zero-percent rollout still enabled.")

		conf[flag_key] = True
		conf[percent_key] = 0
		conf[users_key] = ["Administrator"]
		allow_user = _compiled_first_turn_rollout_decision(
			session_name="phase4-rollout-allow",
			user="Administrator",
			site_name="erpai_prj1",
		)
		if not bool(allow_user.get("enabled")) or str(allow_user.get("reason") or "") != "allow_user":
			raise RuntimeError("Compiled rollout governance selftest failed: allowlisted user was not enabled.")

		conf[flag_key] = True
		conf[percent_key] = 50
		conf[users_key] = []
		first = _compiled_first_turn_rollout_decision(
			session_name="phase4-rollout-stable",
			user="User B",
			site_name="erpai_prj1",
		)
		second = _compiled_first_turn_rollout_decision(
			session_name="phase4-rollout-stable",
			user="User B",
			site_name="erpai_prj1",
		)
		if float(first.get("rollout_bucket") or -1.0) != float(second.get("rollout_bucket") or -2.0):
			raise RuntimeError("Compiled rollout governance selftest failed: rollout bucket was not deterministic.")
		return {
			"ok": True,
			"disabled": disabled,
			"zero_percent": zero_percent,
			"allow_user": allow_user,
			"stable_bucket": first,
		}
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def _audit_latency_summary(values: List[int]) -> Dict[str, int]:
	clean = sorted(int(max(0, value or 0)) for value in values if int(max(0, value or 0)) > 0)
	if not clean:
		return {"count": 0, "avg_ms": 0, "p95_ms": 0, "max_ms": 0}
	index = max(0, min(len(clean) - 1, int((len(clean) - 1) * 0.95)))
	return {
		"count": len(clean),
		"avg_ms": int(round(sum(clean) / float(len(clean)))),
		"p95_ms": int(clean[index]),
		"max_ms": int(clean[-1]),
	}


def summarize_compiled_first_turn_audits(
	limit_sessions: int = 50,
	limit_audits: int = 200,
	session_names: List[str] | None = None,
) -> Dict[str, Any]:
	requested_session_names = [
		str(name or "").strip()
		for name in (session_names or [])
		if str(name or "").strip()
	]
	if requested_session_names:
		session_rows = [{"name": name, "modified": ""} for name in requested_session_names]
	else:
		session_rows = frappe.get_all(
			QWEN_SESSION_DOCTYPE,
			fields=["name", "modified"],
			order_by="modified desc",
			limit_page_length=max(1, int(limit_sessions or 50)),
		)
	records: List[Dict[str, Any]] = []
	rollout_fallbacks: List[Dict[str, Any]] = []
	for row in session_rows:
		session_name = str((row or {}).get("name") or "").strip()
		if not session_name:
			continue
		try:
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, session_name)
		except Exception:
			continue
		for message in reversed(list(session_doc.get("messages") or [])):
			if str(message.role or "").strip().lower() != "tool":
				continue
			payload = _parse_payload(str(message.content or ""))
			payload_type = str(payload.get("type") or "").strip()
			if payload_type == "qwen_compiled_rollout_fallback":
				rollout_fallbacks.append(
					{
						"session_name": session_name,
						"request_id": str(payload.get("request_id") or "").strip(),
						"reason": str(payload.get("reason") or "").strip(),
					}
				)
				continue
			if payload_type != "qwen_compiled_execution_audit_contract":
				continue
			records.append(
				{
					"session_name": session_name,
					"session_modified": str((row or {}).get("modified") or ""),
					"request_id": str(payload.get("request_id") or "").strip(),
						"compiler_decision": str(payload.get("compiler_decision") or "").strip(),
						"selected_report": str(payload.get("selected_report") or "").strip(),
						"capability_id": str(payload.get("capability_id") or "").strip(),
						"proposal_cache_hit": bool(payload.get("proposal_cache_hit")),
						"proposal_shared_inflight_hit": bool(payload.get("proposal_shared_inflight_hit")),
						"runtime_ok": bool(payload.get("runtime_ok")),
					"grounded_validation_status": str(payload.get("grounded_validation_status") or "").strip(),
					"semantic_validation_status": str(payload.get("semantic_validation_status") or "").strip(),
					"proposal_generation_latency_ms": int(max(0, payload.get("proposal_generation_latency_ms") or 0)),
					"compilation_latency_ms": int(max(0, payload.get("compilation_latency_ms") or 0)),
					"runtime_execution_latency_ms": int(max(0, payload.get("runtime_execution_latency_ms") or 0)),
					"semantic_validation_latency_ms": int(max(0, payload.get("semantic_validation_latency_ms") or 0)),
					"total_pipeline_latency_ms": int(max(0, payload.get("total_pipeline_latency_ms") or 0)),
					"tool_count": int(max(0, payload.get("tool_count") or 0)),
				}
			)
			if len(records) >= max(1, int(limit_audits or 200)):
				break
		if len(records) >= max(1, int(limit_audits or 200)):
			break

	def count_values(key: str) -> Dict[str, int]:
		out: Dict[str, int] = {}
		for record in records:
			value = str(record.get(key) or "").strip() or "unknown"
			out[value] = int(out.get(value, 0)) + 1
		return out

	total = len(records)
	runtime_ok_count = sum(1 for record in records if bool(record.get("runtime_ok")))
	proposal_cache_hit_count = sum(1 for record in records if bool(record.get("proposal_cache_hit")))
	proposal_shared_inflight_hit_count = sum(
		1 for record in records if bool(record.get("proposal_shared_inflight_hit"))
	)
	rollout_fallback_count = len(rollout_fallbacks)
	return {
		"sessions_scanned": len(session_rows),
		"audits_found": total,
		"rollout_status": get_compiled_first_turn_rollout_status(),
		"runtime_ok_rate": 0.0 if total == 0 else round(runtime_ok_count / float(total), 4),
		"proposal_cache_hit_rate": 0.0 if total == 0 else round(proposal_cache_hit_count / float(total), 4),
		"proposal_shared_inflight_hit_rate": 0.0
		if total == 0
		else round(proposal_shared_inflight_hit_count / float(total), 4),
		"rollout_fallback_count": rollout_fallback_count,
		"rollout_fallback_rate": 0.0 if total == 0 else round(rollout_fallback_count / float(total), 4),
		"compiler_decision_counts": count_values("compiler_decision"),
		"semantic_validation_status_counts": count_values("semantic_validation_status"),
		"grounded_validation_status_counts": count_values("grounded_validation_status"),
		"proposal_generation_latency": _audit_latency_summary(
			[int(record.get("proposal_generation_latency_ms") or 0) for record in records]
		),
		"compilation_latency": _audit_latency_summary(
			[int(record.get("compilation_latency_ms") or 0) for record in records]
		),
		"runtime_execution_latency": _audit_latency_summary(
			[int(record.get("runtime_execution_latency_ms") or 0) for record in records]
		),
		"semantic_validation_latency": _audit_latency_summary(
			[int(record.get("semantic_validation_latency_ms") or 0) for record in records]
		),
		"total_pipeline_latency": _audit_latency_summary(
			[int(record.get("total_pipeline_latency_ms") or 0) for record in records]
		),
		"average_tool_count": 0.0
		if total == 0
		else round(sum(int(record.get("tool_count") or 0) for record in records) / float(total), 2),
		"recent_audits": records[:10],
		"recent_rollout_fallbacks": rollout_fallbacks[:10],
	}


def run_phase4_compiled_rollout_monitoring_smoke() -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	original_flag = None
	original_percent = None
	original_users = None
	had_original = False
	had_percent = False
	had_users = False
	try:
		try:
			original_flag = (getattr(frappe, "conf", None) or {}).get(flag_key)
			original_percent = (getattr(frappe, "conf", None) or {}).get(percent_key)
			original_users = (getattr(frappe, "conf", None) or {}).get(users_key)
			had_original = flag_key in (getattr(frappe, "conf", None) or {})
			had_percent = percent_key in (getattr(frappe, "conf", None) or {})
			had_users = users_key in (getattr(frappe, "conf", None) or {})
		except Exception:
			original_flag = None
			original_percent = None
			original_users = None
			had_original = False
			had_percent = False
			had_users = False
		(getattr(frappe, "conf", None) or {})[flag_key] = True
		(getattr(frappe, "conf", None) or {})[percent_key] = 100
		(getattr(frappe, "conf", None) or {})[users_key] = []

		doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		doc.title = "Phase4 Compiled Rollout Monitoring Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="How much payable amount do we have as of now",
				user="Administrator",
			)
			summary = summarize_compiled_first_turn_audits(
				limit_sessions=10,
				limit_audits=50,
				session_names=[doc.name],
			)
			if not ok or not isinstance(payload, dict):
				raise RuntimeError("Compiled rollout monitoring smoke failed: live service did not return an ok payload.")
			if int(summary.get("audits_found") or 0) < 1:
				raise RuntimeError("Compiled rollout monitoring smoke failed: no compiled audits were found.")
			decision_counts = summary.get("compiler_decision_counts") if isinstance(summary.get("compiler_decision_counts"), dict) else {}
			semantic_counts = (
				summary.get("semantic_validation_status_counts")
				if isinstance(summary.get("semantic_validation_status_counts"), dict)
				else {}
			)
			mode = str(payload.get("mode") or "").strip()
			if mode == "compiled_first_turn":
				if int(decision_counts.get("execute") or 0) < 1:
					raise RuntimeError("Compiled rollout monitoring smoke failed: execute decisions were not observed.")
				if int(semantic_counts.get("pass") or 0) < 1:
					raise RuntimeError("Compiled rollout monitoring smoke failed: semantic pass outcomes were not observed.")
			elif mode == "legacy_runtime_rollout_fallback":
				if int(summary.get("rollout_fallback_count") or 0) < 1:
					raise RuntimeError("Compiled rollout monitoring smoke failed: rollout fallback was not observed in summary.")
			else:
				raise RuntimeError("Compiled rollout monitoring smoke failed: unexpected live mode was returned.")
			return {
				"ok": ok,
				"payload": payload,
				"summary": summary,
				"session_name": doc.name,
			}
		finally:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	finally:
		conf = getattr(frappe, "conf", None) or {}
		if had_original:
			conf[flag_key] = original_flag
		else:
			try:
				conf.pop(flag_key, None)
			except Exception:
				pass
		if had_percent:
			conf[percent_key] = original_percent
		else:
			try:
				conf.pop(percent_key, None)
			except Exception:
				pass
		if had_users:
			conf[users_key] = original_users
		else:
			try:
				conf.pop(users_key, None)
			except Exception:
				pass


def run_first_turn_regression_suite(messages: List[str] | None = None) -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	default_messages = [
		"How much payable amount do we have as of now",
		"Top 5 customers by revenue",
		"Show monthly sales trend",
		"Analyze AR / AP amount and evaluate the company health",
		"Show me P & L statement, and analyze it",
		"which products are performing well last month",
	]
	test_messages = [
		str(item or "").strip()
		for item in (messages or default_messages)
		if str(item or "").strip()
	]
	conf = getattr(frappe, "conf", None) or {}
	originals = {
		flag_key: conf.get(flag_key),
		percent_key: conf.get(percent_key),
		users_key: conf.get(users_key),
	}
	presence = {
		flag_key: flag_key in conf,
		percent_key: percent_key in conf,
		users_key: users_key in conf,
	}
	try:
		conf[flag_key] = True
		conf[percent_key] = 100
		conf[users_key] = []
		results: List[Dict[str, Any]] = []
		for message in test_messages:
			doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
			doc.title = "First Turn Regression Suite"
			doc.insert(ignore_permissions=False)
			try:
				start = time.perf_counter()
				ok, payload = handle_qwen_user_message(
					session_name=doc.name,
					message=message,
					user="Administrator",
				)
				elapsed_ms = int((time.perf_counter() - start) * 1000)
				session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
				assistant_payload = _latest_assistant_payload(session_doc)
				answer_text = str(assistant_payload.get("text") or "").strip()
				tool_payloads = []
				for row in session_doc.get("messages") or []:
					if str(row.role or "").strip().lower() != "tool":
						continue
					payload_obj = _parse_payload(str(row.content or ""))
					if payload_obj:
						tool_payloads.append(payload_obj)
				type_names = [str(item.get("type") or "").strip() for item in tool_payloads if isinstance(item, dict)]
				compiled_audit = next(
					(
						item
						for item in reversed(tool_payloads)
						if str(item.get("type") or "").strip() == "qwen_compiled_execution_audit_contract"
					),
					{},
				)
				semantic_validation = next(
					(
						item
						for item in reversed(tool_payloads)
						if str(item.get("type") or "").strip() == "qwen_semantic_validation_outcome"
					),
					{},
				)
				fallback_payload = next(
					(
						item
						for item in reversed(tool_payloads)
						if str(item.get("type") or "").strip() == "qwen_compiled_rollout_fallback"
					),
					{},
				)
				results.append(
					{
						"message": message,
						"ok": bool(ok),
						"mode": str((payload or {}).get("mode") or "").strip(),
						"compiled_rollout_fallback_reason": str(
							(payload or {}).get("compiled_rollout_fallback_reason") or ""
						).strip(),
						"answer_text": answer_text,
						"elapsed_ms": elapsed_ms,
						"semantic_validation_status": str(
							(semantic_validation or {}).get("status") or ""
						).strip(),
						"compiler_decision": str((compiled_audit or {}).get("compiler_decision") or "").strip(),
						"selected_report": str((compiled_audit or {}).get("selected_report") or "").strip(),
						"proposal_generation_latency_ms": int(
							max(0, (compiled_audit or {}).get("proposal_generation_latency_ms") or 0)
						),
						"runtime_execution_latency_ms": int(
							max(0, (compiled_audit or {}).get("runtime_execution_latency_ms") or 0)
						),
						"total_pipeline_latency_ms": int(
							max(0, (compiled_audit or {}).get("total_pipeline_latency_ms") or 0)
						),
						"persisted_tool_payload_types": type_names,
						"fallback_payload": fallback_payload,
					}
				)
			finally:
				frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
		return {
			"ok": True,
			"results": results,
			"rollout_status": get_compiled_first_turn_rollout_status(),
		}
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass
