from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import time
import uuid
from typing import Any, Dict, List, Tuple

import frappe

from ai_assistant_ui.qwen_chat.artifact_narrative import (
	build_artifact_narrative_context,
	build_artifact_narrative_contract,
	narrate_governed_artifact,
)
from ai_assistant_ui.qwen_chat.capability_adapters import render_local_followup
from ai_assistant_ui.qwen_chat.clarification_translation import translate_clarification_signal
from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	FollowUpResolution,
	build_audit_envelope,
	build_execution_path,
	build_followup_resolution,
	build_grounded_turn_context,
	build_interaction_contract,
	build_response_policy_contract,
	is_self_contained_business_request,
)
from ai_assistant_ui.qwen_chat.entity_detail import (
	detect_entity_drilldown_request,
	execute_entity_drilldown,
)
from ai_assistant_ui.qwen_chat.family_followup import (
	render_local_family_followup,
	supports_local_family_followup,
)
from ai_assistant_ui.qwen_chat.family_tool_surface import build_family_tool_surface_for_message
from ai_assistant_ui.qwen_chat.followup_interpreter import is_safe_local_compatibility_intent
from ai_assistant_ui.qwen_chat.followup_interpreter import detect_followup_intent
from ai_assistant_ui.qwen_chat.followup_interpreter import assess_context_isolation
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import execute_compiled_fresh_query_message
from ai_assistant_ui.qwen_chat.metadata import (
	get_family_evaluation_case_set,
	get_family_latency_budget_spec,
	list_family_evaluation_case_sets,
	resolve_followup_report_switch,
)
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


def _compiled_decision_message(*, request_id: str, raw_message: str, result: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
	pipeline = result.get("pipeline") if isinstance(result.get("pipeline"), dict) else {}
	compiler = pipeline.get("fresh_query_compiler") if isinstance(pipeline.get("fresh_query_compiler"), dict) else {}
	decision = str(compiler.get("decision") or "").strip()
	reason = str(compiler.get("compiler_reason") or "").strip()
	rendered_response = result.get("rendered_response") if isinstance(result.get("rendered_response"), dict) else {}
	narrative_response = result.get("narrative_response") if isinstance(result.get("narrative_response"), dict) else {}
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
		signal = translate_clarification_signal(
			request_id=request_id,
			raw_message=raw_message,
			compiler_reason=reason,
		)
		return str(signal.user_question or "").strip(), signal.to_payload()
	if decision == "reject":
		if reason:
			return f"I can't complete that safely within the approved ERP read path yet.\n\n{reason}", {}
		return "I can't complete that safely within the approved ERP read path yet.", {}
	if family_status == "clarify":
		detail = str((family_warnings or family_errors or ["The normalized business artifact needs clarification before display."])[0] or "").strip()
		signal = translate_clarification_signal(
			request_id=request_id,
			raw_message=raw_message,
			family_detail=detail,
		)
		return str(signal.user_question or "").strip(), signal.to_payload()
	if family_status.startswith("reject"):
		detail = str((family_errors or ["The normalized business artifact did not pass governed validation."])[0] or "").strip()
		return f"I couldn't complete that result confidently from governed ERP data.\n\n{detail}".strip(), {}
	if semantic_status == "clarify":
		detail = str((semantic_warnings or semantic_errors or ["The grounded result needs clarification before display."])[0] or "").strip()
		signal = translate_clarification_signal(
			request_id=request_id,
			raw_message=raw_message,
			semantic_detail=detail,
		)
		return str(signal.user_question or "").strip(), signal.to_payload()
	if semantic_status == "reject_semantically_inconsistent":
		detail = str((semantic_errors or ["The grounded result did not match the requested business intent."])[0] or "").strip()
		return f"I couldn't complete a grounded answer that matched the requested business intent.\n\n{detail}".strip(), {}
	narrative_answer = str(narrative_response.get("answer_text") or "").strip()
	if narrative_answer:
		return narrative_answer, {}
	rendered_answer = str(rendered_response.get("answer_text") or "").strip()
	if rendered_answer:
		return rendered_answer, {}
	if runtime_answer:
		return runtime_answer, {}
	if runtime_error:
		return _safe_runtime_failure_message(RuntimeError(runtime_error)), {}
	return "I could not complete a governed ERP lookup.", {}


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

	answer_text, clarification_signal_payload = _compiled_decision_message(
		request_id=request_id,
		raw_message=str(interaction_contract.raw_message or "").strip(),
		result=result,
	)
	_append_message(session_doc, "assistant", _assistant_text_payload(answer_text))
	if clarification_signal_payload:
		_append_tool_payload(session_doc, clarification_signal_payload)

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
			artifact_payload=result.get("normalized_family_artifact") if isinstance(result.get("normalized_family_artifact"), dict) else {},
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
	rendered_response = result.get("rendered_response") if isinstance(result.get("rendered_response"), dict) else {}
	narrative_response = result.get("narrative_response") if isinstance(result.get("narrative_response"), dict) else {}
	composite_family_artifacts = result.get("composite_family_artifacts") if isinstance(result.get("composite_family_artifacts"), list) else []
	composite_step_validations = result.get("composite_step_validations") if isinstance(result.get("composite_step_validations"), list) else []
	composite_validation = result.get("composite_validation") if isinstance(result.get("composite_validation"), dict) else {}
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
	if rendered_response:
		_append_tool_payload(session_doc, rendered_response)
	if narrative_response:
		_append_tool_payload(session_doc, narrative_response)
	for payload in composite_family_artifacts:
		if isinstance(payload, dict) and payload:
			_append_tool_payload(session_doc, payload)
	for payload in composite_step_validations:
		if isinstance(payload, dict) and payload:
			_append_tool_payload(session_doc, payload)
	if composite_validation:
		_append_tool_payload(session_doc, composite_validation)
	if family_validation and str(family_validation.get("type") or "").strip():
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
	if semantic_status == "pass":
		return False
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
		"bullet": "bullet_presentation" in requested or "•" in text or "\n- " in text,
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
	requested_time_scope = str(getattr(followup_resolution, "requested_time_scope", "") or "").strip()
	target_metric = str(getattr(followup_resolution, "target_metric", "") or "").strip()
	requested_columns = [
		str(value or "").strip()
		for value in (getattr(followup_resolution, "requested_columns", []) or [])
		if str(value or "").strip()
	]
	prefs = _latest_display_preferences(session_doc, getattr(followup_resolution, "requested_modes", []) or [])
	hint = str(switch.get("requery_prompt_hint") or "").strip()

	parts = [f"Use the report `{target_report}`."]
	if company:
		parts.append(f'Use company "{company}".')
	if requested_time_scope == "last_month":
		parts.append("Use the last month date range.")
	elif requested_time_scope == "current_period":
		parts.append("Use the current month to date.")
	elif requested_time_scope == "all_period":
		parts.append("Use the full available time range.")
	elif report_date:
		parts.append(f"Use report_date {report_date}.")
	elif from_date and to_date:
		parts.append(f"Use the date range from {from_date} to {to_date}.")
	if target_metric:
		parts.append(f"Prioritize the metric `{target_metric}`.")
	if requested_columns:
		parts.append("Return these columns if available: " + ", ".join(requested_columns) + ".")
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


def _latest_normalized_family_artifact(session_doc) -> Dict[str, Any]:
	for m in reversed(session_doc.get("messages") or []):
		if str(m.role or "").strip().lower() != "tool":
			continue
		payload = _parse_payload(str(m.content or ""))
		payload_type = str(payload.get("type") or "").strip().lower()
		if payload_type in {"qwen_normalized_family_artifact_contract", "qwen_composite_family_artifact", "qwen_entity_detail_artifact"}:
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
	pattern = re.compile(
		r"(\*{0,2})(?:MMK\s+)?(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?)(?:\s+MMK)?(\*{0,2})",
		flags=re.IGNORECASE,
	)

	def _replace(match: re.Match[str]) -> str:
		scaled = _format_million_value(match.group(2))
		return f"{match.group(1)}{scaled} Million MMK{match.group(3)}"

	return pattern.sub(_replace, text)


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
	raw_message: str,
	followup_resolution,
	interaction_contract,
	response_policy_contract,
) -> Tuple[bool, Dict[str, Any]] | None:
	requested_modes = {
		str(mode or "").strip()
		for mode in getattr(followup_resolution, "requested_modes", []) or []
		if str(mode or "").strip()
	}
	target_dimension = str(getattr(followup_resolution, "target_dimension", "") or "").strip()
	target_limit = int(max(0, getattr(followup_resolution, "target_limit", 0) or 0))
	sort_direction = str(getattr(followup_resolution, "sort_direction", "") or "").strip()
	target_metric = str(getattr(followup_resolution, "target_metric", "") or "").strip()
	requested_columns = [
		str(value or "").strip()
		for value in (getattr(followup_resolution, "requested_columns", []) or [])
		if str(value or "").strip()
	]
	requested_time_scope = str(getattr(followup_resolution, "requested_time_scope", "") or "").strip()
	if not requested_modes.intersection({
		"presentation_transform",
		"table_presentation",
		"bullet_presentation",
		"aging_bucket_view",
		"dimension_breakdown",
		"sort_or_limit",
		"metric_refinement",
		"column_refinement",
	}):
		return None
	assistant_payload, trace = _latest_grounded_assistant_context(session_doc)
	grounded_turn = _latest_grounded_turn_contract(session_doc)
	family_artifact_payload = _latest_normalized_family_artifact(session_doc)
	heuristic_intent = detect_followup_intent(
		str(raw_message or "").strip(),
		grounded_turn=grounded_turn,
	)
	if not target_metric:
		target_metric = str(getattr(heuristic_intent, "target_metric", "") or "").strip()
	if not requested_columns:
		requested_columns = [
			str(value or "").strip()
			for value in (getattr(heuristic_intent, "requested_columns", []) or [])
			if str(value or "").strip()
		]
	for mode in getattr(heuristic_intent, "requested_modes", []) or []:
		clean_mode = str(mode or "").strip()
		if clean_mode and clean_mode not in requested_modes:
			requested_modes.add(clean_mode)
	if not assistant_payload or not trace:
		return None
	text = str(assistant_payload.get("text") or "").strip()
	if not text and not grounded_turn:
		return None
	transformed = text
	applied_transforms: List[str] = []
	family_followup_payload: Dict[str, Any] = {}
	display_preferences = _latest_display_preferences(
		session_doc,
		getattr(followup_resolution, "requested_modes", []) or [],
	)

	if supports_local_family_followup(
		family_artifact_payload,
		target_limit=target_limit,
		target_metric=target_metric,
		requested_columns=requested_columns,
		requested_time_scope=requested_time_scope,
		requested_modes=list(requested_modes),
	):
		family_render = render_local_family_followup(
			request_id=request_id,
			artifact_payload=family_artifact_payload,
			target_limit=target_limit,
			target_metric=target_metric,
			requested_columns=requested_columns,
			requested_modes=list(requested_modes),
		)
		family_text = str(family_render.get("answer_text") or "").strip()
		if family_text:
			transformed = family_text
			family_followup_payload = family_render
			applied_transforms.append("family_followup_render")

	if "aging_bucket_view" in requested_modes and "family_followup_render" not in applied_transforms:
		aging_view = render_local_followup("aging_bucket_view", grounded_turn, display_preferences)
		if aging_view:
			transformed = aging_view
			applied_transforms.append("aging_bucket_view")

	if "dimension_breakdown" in requested_modes and "family_followup_render" not in applied_transforms:
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

	if "sort_or_limit" in requested_modes and "family_followup_render" not in applied_transforms:
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

	def _session_tool_payloads() -> List[Dict[str, Any]]:
		out: List[Dict[str, Any]] = []
		for row in session_doc.get("messages") or []:
			if str(row.role or "").strip().lower() != "tool":
				continue
			payload = _parse_payload(str(row.content or ""))
			if payload:
				out.append(payload)
		return out

	narrative_payload: Dict[str, Any] = {}
	narrative_contract_payload: Dict[str, Any] = {}
	rendered_payload = family_followup_payload
	if not rendered_payload:
		rendered_payload = _latest_tool_payload_by_type(
			_session_tool_payloads(),
			"qwen_rendered_family_response_contract",
		)
	if not rendered_payload:
		rendered_payload = _latest_tool_payload_by_type(
			_session_tool_payloads(),
			"qwen_entity_detail_rendered_response",
		)
	if family_artifact_payload and (
		family_followup_payload
		or requested_modes.intersection({"table_presentation", "bullet_presentation", "metric_refinement", "column_refinement", "sort_or_limit"})
	):
		artifact_context = build_artifact_narrative_context(
			request_id=request_id,
			artifact_payload=family_artifact_payload,
			rendered_response_payload=rendered_payload,
			response_policy=response_policy_contract.to_runtime_payload(),
			validation_payload={},
		)
		narrative_payload = narrate_governed_artifact(
			session_id=session_doc.name,
			user_id=str(interaction_contract.user_id or "").strip(),
			site_name=str(interaction_contract.site_name or "").strip(),
			message=str(raw_message or "").strip(),
			request_id=request_id,
			artifact_context=artifact_context,
			response_policy=response_policy_contract.to_runtime_payload(),
		)
		narrative_contract = build_artifact_narrative_contract(
			request_id=request_id,
			artifact_context=artifact_context,
			runtime_payload=narrative_payload,
		)
		if narrative_contract is not None:
			narrative_contract_payload = narrative_contract.to_payload()
			narrative_text = str(narrative_contract_payload.get("answer_text") or "").strip()
			if narrative_text:
				transformed = narrative_text
				applied_transforms.append("artifact_narrative_followup")

	_append_message(session_doc, "assistant", _assistant_text_payload(transformed))
	if family_followup_payload:
		_append_tool_payload(session_doc, family_followup_payload)
	if narrative_contract_payload:
		_append_tool_payload(session_doc, narrative_contract_payload)
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


def _context_isolation_payload(*, request_id: str, decision: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"type": "qwen_context_isolation_decision",
		"request_id": str(request_id or "").strip(),
		"force_new_query": bool(decision.get("force_new_query")),
		"out_of_scope": bool(decision.get("out_of_scope")),
		"reason": str(decision.get("reason") or "").strip(),
		"requested_domains": list(decision.get("requested_domains") or []),
		"context_domains": list(decision.get("context_domains") or []),
		"primary_domain": str(decision.get("primary_domain") or "").strip(),
		"created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
	}


def _out_of_scope_answer(message: str, decision: Dict[str, Any]) -> str:
	primary_domain = str(decision.get("primary_domain") or "").strip()
	if primary_domain == "hr":
		return (
			"I can help with finance, sales, inventory, product performance, invoices, and governed ERP drilldowns.\n\n"
			"I don't have governed HR or headcount coverage yet, so I can't answer staff-count questions confidently from ERP data in this assistant."
		)
	return (
		"I can help with finance, sales, inventory, product performance, invoices, and governed ERP drilldowns.\n\n"
		"This question falls outside the current governed Qwen ERP coverage, so I can't answer it confidently from ERP data yet."
	)


def _try_entity_detail_followup(
	session_doc,
	*,
	request_id: str,
	raw_message: str,
	entity_reference: Dict[str, Any],
	interaction_contract,
	response_policy_contract,
	latest_grounded_turn: Dict[str, Any],
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
		frappe.log_error(frappe.get_traceback(), "Qwen Assistant: entity drilldown failed")
		_append_message(session_doc, "assistant", _assistant_text_payload(f"I couldn't complete a grounded entity drilldown confidently.\n\n{str(exc or '').strip()}"))
		_append_message(
			session_doc,
			"tool",
			_tool_trace_message(
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
		session_doc.save(ignore_permissions=False)
		return True, {"ok": False, "request_id": request_id, "error": str(exc or "").strip(), "agent_meta": {"engine": "entity_detail"}}

	if not bool(outcome.get("ok")):
		return None

	answer_text = str(outcome.get("answer_text") or "").strip()
	_append_message(session_doc, "assistant", _assistant_text_payload(answer_text))
	artifact_payload = outcome.get("artifact_payload") if isinstance(outcome.get("artifact_payload"), dict) else {}
	rendered_payload = outcome.get("rendered_response_payload") if isinstance(outcome.get("rendered_response_payload"), dict) else {}
	narrative_contract_payload = outcome.get("narrative_contract_payload") if isinstance(outcome.get("narrative_contract_payload"), dict) else {}
	grounded_turn_payload = outcome.get("grounded_turn_payload") if isinstance(outcome.get("grounded_turn_payload"), dict) else {}
	if artifact_payload:
		_append_tool_payload(session_doc, artifact_payload)
	if rendered_payload:
		_append_tool_payload(session_doc, rendered_payload)
	if narrative_contract_payload:
		_append_tool_payload(session_doc, narrative_contract_payload)
	if grounded_turn_payload:
		_append_tool_payload(session_doc, grounded_turn_payload)
	trace_payload = _tool_trace_message(
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
	_append_message(session_doc, "tool", trace_payload)
	session_doc.save(ignore_permissions=False)
	return True, {"ok": True, "request_id": request_id, "agent_meta": {"engine": "entity_detail", "mode": "entity_drilldown"}}


def handle_qwen_user_message(*, session_name: str, message: str, user: str) -> Tuple[bool, Dict[str, Any]]:
	session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, session_name)
	site_name = str(getattr(getattr(frappe, "local", None), "site", "") or "").strip()
	request_id = uuid.uuid4().hex
	msg = str(message or "").strip()
	latest_grounded_turn = _latest_grounded_turn_contract(session_doc)
	latest_family_artifact = _latest_normalized_family_artifact(session_doc)
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
	entity_drilldown = None
	context_isolation = {
		"force_new_query": False,
		"out_of_scope": False,
		"reason": "",
		"requested_domains": [],
		"context_domains": [],
	}
	if latest_grounded_turn_available:
		entity_drilldown = detect_entity_drilldown_request(
			message=msg,
			artifact_payload=latest_family_artifact,
			grounded_turn=latest_grounded_turn,
		)
		if entity_drilldown is None:
			context_isolation = assess_context_isolation(
				msg,
				language=interaction_contract.detected_language,
				grounded_turn=latest_grounded_turn,
			)

	semantic_intent = None
	allow_heuristic_fallback = True
	degraded_reason = ""
	semantic_payload = None
	followup_context_available = bool(latest_grounded_turn_available and not context_isolation.get("force_new_query") and entity_drilldown is None)
	if followup_context_available and latest_grounded_turn:
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
	if entity_drilldown is not None:
		followup_resolution = FollowUpResolution(
			request_id=request_id,
			mode="entity_drilldown",
			requested_modes=["entity_drilldown"],
			target_dimension="",
			target_limit=0,
			sort_direction="",
			target_metric="",
			requested_columns=[],
			requested_time_scope="",
			target_capability_id="",
			target_report="",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=latest_grounded_turn_available,
			reason="The request drills into a governed entity from the latest grounded artifact.",
		)
	else:
		followup_resolution = build_followup_resolution(
			request_id=request_id,
			message=msg,
			latest_grounded_turn_available=followup_context_available,
			latest_grounded_turn=latest_grounded_turn if followup_context_available else {},
			semantic_intent=semantic_intent,
			allow_heuristic_fallback=allow_heuristic_fallback if followup_context_available else True,
			degraded_reason=str(context_isolation.get("reason") or degraded_reason or "").strip(),
		)
	response_policy_contract = build_response_policy_contract(
		interaction_contract=interaction_contract,
		followup_resolution=followup_resolution,
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
	if bool(context_isolation.get("force_new_query")):
		_append_tool_payload(session_doc, _context_isolation_payload(request_id=request_id, decision=context_isolation))
	_append_tool_payload(session_doc, followup_resolution.to_payload())

	if bool(context_isolation.get("out_of_scope")) and entity_drilldown is None:
		answer_text = _out_of_scope_answer(msg, context_isolation)
		execution_path = ExecutionPath(
			request_id=request_id,
			path="unsupported_domain",
			reason=str(context_isolation.get("reason") or "").strip() or "The request is outside the current governed ERP scope.",
			requires_runtime=False,
			grounded_required=False,
		)
		_append_tool_payload(session_doc, execution_path.to_payload())
		_append_message(session_doc, "assistant", _assistant_text_payload(answer_text))
		_append_tool_payload(
			session_doc,
			build_audit_envelope(
				interaction_contract=interaction_contract,
				followup_resolution=followup_resolution,
				execution_path=execution_path,
				runtime_trace_payload={},
				grounded_turn_context={},
				answer_text=answer_text,
			).to_payload(),
		)
		session_doc.save(ignore_permissions=False)
		return True, {"ok": True, "request_id": request_id, "mode": "out_of_scope_domain", "agent_meta": {"engine": "local_governed_scope_guard"}}

	local_transform = None
	if followup_resolution.mode == "local_grounded_transform":
		local_transform = _try_local_followup_transform(
			session_doc,
			request_id=request_id,
			raw_message=msg,
			followup_resolution=followup_resolution,
			interaction_contract=interaction_contract,
			response_policy_contract=response_policy_contract,
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

	if followup_resolution.mode == "entity_drilldown" and entity_drilldown is not None:
		execution_path = ExecutionPath(
			request_id=request_id,
			path="entity_drilldown",
			reason="The request was resolved through a governed entity drilldown over the latest artifact.",
			requires_runtime=True,
			grounded_required=True,
		)
		_append_tool_payload(session_doc, execution_path.to_payload())
		entity_result = _try_entity_detail_followup(
			session_doc,
			request_id=request_id,
			raw_message=msg,
			entity_reference=entity_drilldown,
			interaction_contract=interaction_contract,
			response_policy_contract=response_policy_contract,
			latest_grounded_turn=latest_grounded_turn,
		)
		if entity_result:
			_append_tool_payload(
				session_doc,
				build_audit_envelope(
					interaction_contract=interaction_contract,
					followup_resolution=followup_resolution,
					execution_path=execution_path,
					runtime_trace_payload=_latest_qwen_trace_payload(session_doc),
					grounded_turn_context=_latest_grounded_turn_contract(session_doc),
					answer_text=str(_latest_assistant_payload(session_doc).get("text") or ""),
				).to_payload(),
			)
			session_doc.save(ignore_permissions=False)
			return entity_result

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
	family_tool_surface = build_family_tool_surface_for_message(
		request_id=request_id,
		session_id=session_name,
		message=msg,
	)
	family_tool_context_payload = {}
	if family_tool_surface is not None:
		family_tool_context_payload = family_tool_surface.to_runtime_payload()
		_append_tool_payload(session_doc, family_tool_surface.to_payload())
	try:
		runtime_payload = call_qwen_runtime_chat(
			session_id=session_name,
			user_id=user,
			site_name=site_name,
			message=runtime_message,
			recent_messages=recent_messages,
			response_policy=response_policy_contract.to_runtime_payload(),
			family_tool_context=family_tool_context_payload,
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
		artifact_payload=_latest_normalized_family_artifact(session_doc),
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


def _family_latency_budget_payload(family_id: str) -> Dict[str, Any]:
	spec = get_family_latency_budget_spec(family_id)
	if not spec:
		return {}
	return {
		"family_id": str(spec.get("family_id") or "").strip(),
		"proposal_generation_development_budget_ms": int(
			max(0, spec.get("proposal_generation_development_budget_ms") or 0)
		),
		"runtime_execution_development_budget_ms": int(
			max(0, spec.get("runtime_execution_development_budget_ms") or 0)
		),
		"total_pipeline_development_budget_ms": int(
			max(0, spec.get("total_pipeline_development_budget_ms") or 0)
		),
		"total_pipeline_enterprise_target_ms": int(
			max(0, spec.get("total_pipeline_enterprise_target_ms") or 0)
		),
		"notes": str(spec.get("notes") or "").strip(),
	}


def _case_latency_budget_assessment(
	*,
	family_id: str,
	proposal_generation_latency_ms: int,
	runtime_execution_latency_ms: int,
	total_pipeline_latency_ms: int,
) -> Dict[str, Any]:
	budget = _family_latency_budget_payload(family_id)
	if not budget:
		return {}

	proposal_budget_ms = int(budget.get("proposal_generation_development_budget_ms") or 0)
	runtime_budget_ms = int(budget.get("runtime_execution_development_budget_ms") or 0)
	total_development_budget_ms = int(budget.get("total_pipeline_development_budget_ms") or 0)
	total_enterprise_target_ms = int(budget.get("total_pipeline_enterprise_target_ms") or 0)
	within_proposal_budget = proposal_budget_ms <= 0 or proposal_generation_latency_ms <= proposal_budget_ms
	within_runtime_budget = runtime_budget_ms <= 0 or runtime_execution_latency_ms <= runtime_budget_ms
	within_development_budget = total_development_budget_ms <= 0 or total_pipeline_latency_ms <= total_development_budget_ms
	within_enterprise_target = total_enterprise_target_ms > 0 and total_pipeline_latency_ms <= total_enterprise_target_ms

	status = "not_configured"
	if budget:
		if within_enterprise_target:
			status = "enterprise_green"
		elif within_development_budget and within_proposal_budget and within_runtime_budget:
			status = "development_green_enterprise_open"
		elif within_development_budget:
			status = "development_green_with_stage_overage"
		else:
			status = "over_development_budget"

	return {
		"budget": budget,
		"observed": {
			"proposal_generation_latency_ms": int(max(0, proposal_generation_latency_ms)),
			"runtime_execution_latency_ms": int(max(0, runtime_execution_latency_ms)),
			"total_pipeline_latency_ms": int(max(0, total_pipeline_latency_ms)),
		},
		"within_proposal_budget": bool(within_proposal_budget),
		"within_runtime_budget": bool(within_runtime_budget),
		"within_development_budget": bool(within_development_budget),
		"within_enterprise_target": bool(within_enterprise_target),
		"development_budget_overage_ms": int(
			max(0, total_pipeline_latency_ms - total_development_budget_ms)
		)
		if total_development_budget_ms > 0
		else 0,
		"enterprise_target_overage_ms": int(
			max(0, total_pipeline_latency_ms - total_enterprise_target_ms)
		)
		if total_enterprise_target_ms > 0
		else 0,
		"status": status,
	}


def _family_latency_budget_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
	grouped: Dict[str, List[Dict[str, Any]]] = {}
	for item in results:
		if not isinstance(item, dict):
			continue
		if not bool(item.get("case_ok")):
			continue
		family_id = str(item.get("observed_family_id") or item.get("expected_family_id") or "").strip()
		if not family_id:
			continue
		grouped.setdefault(family_id, []).append(item)

	families: Dict[str, Any] = {}
	development_green_count = 0
	enterprise_green_count = 0
	for family_id, items in grouped.items():
		budget = _family_latency_budget_payload(family_id)
		proposal_summary = _audit_latency_summary(
			[int(item.get("proposal_generation_latency_ms") or 0) for item in items]
		)
		runtime_summary = _audit_latency_summary(
			[int(item.get("runtime_execution_latency_ms") or 0) for item in items]
		)
		total_summary = _audit_latency_summary(
			[int(item.get("total_pipeline_latency_ms") or 0) for item in items]
		)
		proposal_budget_ms = int(budget.get("proposal_generation_development_budget_ms") or 0)
		runtime_budget_ms = int(budget.get("runtime_execution_development_budget_ms") or 0)
		total_development_budget_ms = int(budget.get("total_pipeline_development_budget_ms") or 0)
		total_enterprise_target_ms = int(budget.get("total_pipeline_enterprise_target_ms") or 0)
		proposal_p95_ms = int(proposal_summary.get("p95_ms") or 0)
		runtime_p95_ms = int(runtime_summary.get("p95_ms") or 0)
		total_p95_ms = int(total_summary.get("p95_ms") or 0)
		within_proposal_budget = proposal_budget_ms <= 0 or proposal_p95_ms <= proposal_budget_ms
		within_runtime_budget = runtime_budget_ms <= 0 or runtime_p95_ms <= runtime_budget_ms
		within_development_budget = total_development_budget_ms <= 0 or total_p95_ms <= total_development_budget_ms
		within_enterprise_target = total_enterprise_target_ms > 0 and total_p95_ms <= total_enterprise_target_ms
		status = "not_configured"
		if budget:
			if within_enterprise_target:
				status = "enterprise_green"
			elif within_development_budget and within_proposal_budget and within_runtime_budget:
				status = "development_green_enterprise_open"
			elif within_development_budget:
				status = "development_green_with_stage_overage"
			else:
				status = "over_development_budget"
		if status in {"enterprise_green"}:
			enterprise_green_count += 1
		if status in {"enterprise_green", "development_green_enterprise_open", "development_green_with_stage_overage"}:
			development_green_count += 1
		families[family_id] = {
			"case_count": len(items),
			"budget": budget,
			"proposal_generation_latency": proposal_summary,
			"runtime_execution_latency": runtime_summary,
			"total_pipeline_latency": total_summary,
			"within_proposal_budget": bool(within_proposal_budget),
			"within_runtime_budget": bool(within_runtime_budget),
			"within_development_budget": bool(within_development_budget),
			"within_enterprise_target": bool(within_enterprise_target),
			"development_budget_overage_ms": int(max(0, total_p95_ms - total_development_budget_ms))
			if total_development_budget_ms > 0
			else 0,
			"enterprise_target_overage_ms": int(max(0, total_p95_ms - total_enterprise_target_ms))
			if total_enterprise_target_ms > 0
			else 0,
			"status": status,
			"case_ids": [str(item.get("case_id") or "").strip() for item in items if str(item.get("case_id") or "").strip()],
		}

	family_count = len(families)
	return {
		"family_count": family_count,
		"development_green_family_count": development_green_count,
		"enterprise_green_family_count": enterprise_green_count,
		"development_green_rate": 0.0 if family_count == 0 else round(development_green_count / float(family_count), 4),
		"enterprise_green_rate": 0.0 if family_count == 0 else round(enterprise_green_count / float(family_count), 4),
		"families": families,
	}


def _family_metrics_summary(records: List[Dict[str, Any]], rollout_fallbacks: List[Dict[str, Any]]) -> Dict[str, Any]:
	fallback_keys = {
		(
			str(item.get("session_name") or "").strip(),
			str(item.get("request_id") or "").strip(),
		)
		for item in rollout_fallbacks
		if str(item.get("session_name") or "").strip() and str(item.get("request_id") or "").strip()
	}
	grouped: Dict[str, List[Dict[str, Any]]] = {}
	for record in records:
		family_id = str(record.get("governed_family_id") or "").strip() or "unknown"
		grouped.setdefault(family_id, []).append(record)

	out: Dict[str, Any] = {}
	for family_id, items in grouped.items():
		total = len(items)
		runtime_ok_count = sum(1 for item in items if bool(item.get("runtime_ok")))
		fallback_count = sum(
			1
			for item in items
			if (
				str(item.get("session_name") or "").strip(),
				str(item.get("request_id") or "").strip(),
			)
			in fallback_keys
		)
		out[family_id] = {
			"audit_count": total,
			"compiler_decision_counts": {
				value: sum(1 for item in items if str(item.get("compiler_decision") or "").strip() == value)
				for value in sorted(
					{
						str(item.get("compiler_decision") or "").strip() or "unknown"
						for item in items
					}
				)
			},
			"semantic_validation_status_counts": {
				value: sum(1 for item in items if str(item.get("semantic_validation_status") or "").strip() == value)
				for value in sorted(
					{
						str(item.get("semantic_validation_status") or "").strip() or "unknown"
						for item in items
					}
				)
			},
			"family_validation_status_counts": {
				value: sum(1 for item in items if str(item.get("family_validation_status") or "").strip() == value)
				for value in sorted(
					{
						str(item.get("family_validation_status") or "").strip() or "unknown"
						for item in items
					}
				)
			},
			"runtime_ok_rate": 0.0 if total == 0 else round(runtime_ok_count / float(total), 4),
			"rollout_fallback_count": fallback_count,
			"rollout_fallback_rate": 0.0 if total == 0 else round(fallback_count / float(total), 4),
			"proposal_generation_latency": _audit_latency_summary(
				[int(item.get("proposal_generation_latency_ms") or 0) for item in items]
			),
			"runtime_execution_latency": _audit_latency_summary(
				[int(item.get("runtime_execution_latency_ms") or 0) for item in items]
			),
			"total_pipeline_latency": _audit_latency_summary(
				[int(item.get("total_pipeline_latency_ms") or 0) for item in items]
			),
		}
	return out


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
						"governed_family_id": str(payload.get("governed_family_id") or "").strip(),
						"composite_plan_id": str(payload.get("composite_plan_id") or "").strip(),
						"capability_id": str(payload.get("capability_id") or "").strip(),
						"proposal_cache_hit": bool(payload.get("proposal_cache_hit")),
						"proposal_shared_inflight_hit": bool(payload.get("proposal_shared_inflight_hit")),
						"runtime_ok": bool(payload.get("runtime_ok")),
					"grounded_validation_status": str(payload.get("grounded_validation_status") or "").strip(),
					"family_validation_status": str(payload.get("family_validation_status") or "").strip(),
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
		"family_metrics": _family_metrics_summary(records, rollout_fallbacks),
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


def run_same_session_fresh_query_regression_smoke(messages: List[str] | None = None) -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	default_messages = [
		"How much payable amount do we have as of now",
		"Top 5 customers by revenue",
		"Show monthly sales trend",
		"Show me P & L statement",
		"Which products are performing well last month",
		"Analyze AR / AP amount and evaluate the company health",
		"Show current inventory value by warehouse",
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
		doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		doc.title = "Same Session Fresh Query Regression"
		doc.insert(ignore_permissions=False)
		results: List[Dict[str, Any]] = []
		try:
			for message in test_messages:
				start = time.perf_counter()
				ok, payload = handle_qwen_user_message(
					session_name=doc.name,
					message=message,
					user="Administrator",
				)
				elapsed_ms = int((time.perf_counter() - start) * 1000)
				payload = payload if isinstance(payload, dict) else {}
				mode = str(payload.get("mode") or "").strip()
				semantic_status = str(payload.get("semantic_validation_status") or "").strip()
				results.append(
					{
						"message": message,
						"ok": bool(ok),
						"mode": mode,
						"semantic_validation_status": semantic_status,
						"elapsed_ms": elapsed_ms,
					}
				)
				if not bool(ok):
					raise RuntimeError(
						f"Same-session fresh-query smoke failed: service returned not-ok for `{message}`."
					)
				if mode != "compiled_first_turn":
					raise RuntimeError(
						f"Same-session fresh-query smoke failed: `{message}` did not use compiled first-turn mode."
					)
				if semantic_status and semantic_status != "pass":
					raise RuntimeError(
						f"Same-session fresh-query smoke failed: `{message}` semantic status was `{semantic_status}`."
					)
			return {
				"ok": True,
				"session_name": doc.name,
				"results": results,
				"rollout_status": get_compiled_first_turn_rollout_status(),
			}
		finally:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_phase4b_followup_fidelity_smoke() -> Dict[str, Any]:
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

	def _session_tool_payloads(session_doc) -> List[Dict[str, Any]]:
		out: List[Dict[str, Any]] = []
		for row in session_doc.get("messages") or []:
			if str(row.role or "").strip().lower() != "tool":
				continue
			payload = _parse_payload(str(row.content or ""))
			if payload:
				out.append(payload)
		return out

	try:
		conf[flag_key] = True
		conf[percent_key] = 100
		conf[users_key] = []

		results: Dict[str, Any] = {}

		doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		doc.title = "Phase4B Followup Fidelity Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="Top 10 customers by revenue",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Follow-up fidelity smoke failed on initial top-10 ranking request.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			initial_tool_payloads = _session_tool_payloads(session_doc)
			initial_artifact = _latest_tool_payload_by_type(initial_tool_payloads, "qwen_normalized_family_artifact_contract")
			results["top_n_followup_initial"] = {
				"mode": str((payload or {}).get("mode") or "").strip(),
				"family_id": str(initial_artifact.get("family_id") or "").strip(),
				"has_artifact": bool(initial_artifact),
			}
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="I mean top 5",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Follow-up fidelity smoke failed on top-5 correction.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			rendered = _latest_tool_payload_by_type(_session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
			rows = data_table.get("rows") if isinstance(data_table.get("rows"), list) else []
			results["top_n_followup"] = {
				"mode": str((payload or {}).get("mode") or "").strip(),
				"title": str(rendered.get("title") or "").strip(),
				"row_count": len(rows),
				"columns": data_table.get("columns") if isinstance(data_table.get("columns"), list) else [],
			}
			if len(rows) != 5:
				raise RuntimeError(
					f"Follow-up fidelity smoke failed: expected 5 ranking rows after correction, observed {len(rows)}. "
					f"mode={str((payload or {}).get('mode') or '').strip()!r} "
					f"initial={results.get('top_n_followup_initial')!r} "
					f"title={str(rendered.get('title') or '').strip()!r}"
				)
		finally:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)

		doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		doc.title = "Phase4B Metric Fidelity Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="Which products are performing best last month",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Metric fidelity smoke failed on initial product-performance request.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			initial_tool_payloads = _session_tool_payloads(session_doc)
			initial_artifact = _latest_tool_payload_by_type(initial_tool_payloads, "qwen_normalized_family_artifact_contract")
			results["amount_followup_initial"] = {
				"mode": str((payload or {}).get("mode") or "").strip(),
				"family_id": str(initial_artifact.get("family_id") or "").strip(),
				"has_artifact": bool(initial_artifact),
			}
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show me with their amount",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Metric fidelity smoke failed on amount refinement.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			rendered = _latest_tool_payload_by_type(_session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
			columns = data_table.get("columns") if isinstance(data_table.get("columns"), list) else []
			results["amount_followup"] = {
				"mode": str((payload or {}).get("mode") or "").strip(),
				"title": str(rendered.get("title") or "").strip(),
				"columns": columns,
			}
			if not any("Amount" in str(col or "") for col in columns):
				raise RuntimeError(
					f"Metric fidelity smoke failed: amount refinement did not render an amount column. "
					f"mode={str((payload or {}).get('mode') or '').strip()!r} "
					f"initial={results.get('amount_followup_initial')!r} "
					f"title={str(rendered.get('title') or '').strip()!r} columns={columns!r}"
				)
		finally:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)

		doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		doc.title = "Phase4B Column Fidelity Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show me top 10 products last month by revenue with item name, revenue, and contribution percent",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Column fidelity smoke failed on explicit revenue/contribution request.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			rendered = _latest_tool_payload_by_type(_session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
			rows = data_table.get("rows") if isinstance(data_table.get("rows"), list) else []
			columns = data_table.get("columns") if isinstance(data_table.get("columns"), list) else []
			results["explicit_columns"] = {
				"mode": str((payload or {}).get("mode") or "").strip(),
				"title": str(rendered.get("title") or "").strip(),
				"row_count": len(rows),
				"columns": columns,
			}
			if len(rows) != 10:
				raise RuntimeError(f"Column fidelity smoke failed: expected 10 rows, observed {len(rows)}.")
			if not any("Sales Amount" in str(col or "") for col in columns):
				raise RuntimeError(f"Column fidelity smoke failed: explicit revenue request did not render Sales Amount. Observed columns={columns!r}")
			if not any("Contribution" in str(col or "") for col in columns):
				raise RuntimeError(f"Column fidelity smoke failed: explicit contribution request did not render Contribution %. Observed columns={columns!r}")
		finally:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)

		return {"ok": True, "results": results}
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_phase4b_transaction_listing_smoke() -> Dict[str, Any]:
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

	def _session_tool_payloads(session_doc) -> List[Dict[str, Any]]:
		out: List[Dict[str, Any]] = []
		for row in session_doc.get("messages") or []:
			if str(row.role or "").strip().lower() != "tool":
				continue
			payload = _parse_payload(str(row.content or ""))
			if payload:
				out.append(payload)
		return out

	try:
		conf[flag_key] = True
		conf[percent_key] = 100
		conf[users_key] = []

		doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		doc.title = "Phase4B Transaction Listing Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message="show me the last 7 sale invoices",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Transaction listing smoke failed on invoice-list request.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			rendered = _latest_tool_payload_by_type(_session_tool_payloads(session_doc), "qwen_rendered_family_response_contract")
			blocks = rendered.get("blocks") if isinstance(rendered.get("blocks"), list) else []
			data_table = next((item for item in blocks if isinstance(item, dict) and str(item.get("block_type") or "").strip() == "data_table"), {})
			rows = data_table.get("rows") if isinstance(data_table.get("rows"), list) else []
			columns = data_table.get("columns") if isinstance(data_table.get("columns"), list) else []
			if len(rows) != 7:
				raise RuntimeError(
					f"Transaction listing smoke failed: expected 7 invoice rows, observed {len(rows)}. "
					f"mode={str((payload or {}).get('mode') or '').strip()!r} title={str(rendered.get('title') or '').strip()!r} columns={columns!r}"
				)
			if not any("Invoice" in str(col or "") for col in columns):
				raise RuntimeError(f"Transaction listing smoke failed: invoice column missing. Observed columns={columns!r}")
			if not any("Customer" in str(col or "") for col in columns):
				raise RuntimeError(f"Transaction listing smoke failed: customer column missing. Observed columns={columns!r}")
			return {
				"ok": True,
				"mode": str((payload or {}).get("mode") or "").strip(),
				"title": str(rendered.get("title") or "").strip(),
				"row_count": len(rows),
				"columns": columns,
			}
		finally:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def _latest_tool_payload_by_type(tool_payloads: List[Dict[str, Any]], payload_type: str) -> Dict[str, Any]:
	for item in reversed(tool_payloads):
		if str(item.get("type") or "").strip() == str(payload_type or "").strip():
			return item
	return {}


def _run_family_evaluation_case(*, case: Dict[str, Any], user: str = "Administrator") -> Dict[str, Any]:
	message = str(case.get("message") or "").strip()
	case_id = str(case.get("case_id") or "").strip()
	expected_mode = str(case.get("expected_mode") or "").strip()
	expected_compiler_decision = str(case.get("expected_compiler_decision") or "").strip()
	expected_family_validation_status = str(case.get("expected_family_validation_status") or "").strip()
	expected_semantic_status = str(case.get("expected_semantic_status") or "").strip()
	expected_family_id = str(case.get("family_id") or "").strip()
	expected_composite_plan_id = str(case.get("composite_plan_id") or "").strip()

	doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
	doc.title = f"Phase4B Family Evaluation {case_id or 'case'}"
	doc.insert(ignore_permissions=False)
	start = time.perf_counter()
	try:
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=message,
			user=user,
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
		compiled_audit = _latest_tool_payload_by_type(tool_payloads, "qwen_compiled_execution_audit_contract")
		family_validation = _latest_tool_payload_by_type(tool_payloads, "qwen_family_validation_outcome")
		composite_validation = _latest_tool_payload_by_type(tool_payloads, "qwen_composite_read_validation_contract")
		semantic_validation = _latest_tool_payload_by_type(tool_payloads, "qwen_semantic_validation_outcome")
		composite_semantic = _latest_tool_payload_by_type(tool_payloads, "qwen_composite_semantic_validation")
		fallback_payload = _latest_tool_payload_by_type(tool_payloads, "qwen_compiled_rollout_fallback")
		observed_mode = str((payload or {}).get("mode") or "").strip()
		observed_compiler_decision = str((compiled_audit or {}).get("compiler_decision") or "").strip()
		observed_family_id = str((compiled_audit or {}).get("governed_family_id") or "").strip()
		observed_composite_plan_id = str((compiled_audit or {}).get("composite_plan_id") or "").strip()
		observed_family_validation_status = str((compiled_audit or {}).get("family_validation_status") or "").strip()
		if not observed_family_validation_status:
			observed_family_validation_status = str(
				(family_validation or composite_validation or {}).get("status") or ""
			).strip()
		observed_semantic_status = str((compiled_audit or {}).get("semantic_validation_status") or "").strip()
		if not observed_semantic_status:
			observed_semantic_status = str((semantic_validation or composite_semantic or {}).get("status") or "").strip()

		mismatches: List[str] = []
		if expected_mode and observed_mode != expected_mode:
			mismatches.append(f"mode expected `{expected_mode}` but observed `{observed_mode or 'missing'}`")
		if expected_compiler_decision and observed_compiler_decision != expected_compiler_decision:
			mismatches.append(
				f"compiler decision expected `{expected_compiler_decision}` but observed `{observed_compiler_decision or 'missing'}`"
			)
		if expected_family_id and observed_family_id != expected_family_id:
			mismatches.append(f"family expected `{expected_family_id}` but observed `{observed_family_id or 'missing'}`")
		if expected_composite_plan_id and observed_composite_plan_id != expected_composite_plan_id:
			mismatches.append(
				f"composite plan expected `{expected_composite_plan_id}` but observed `{observed_composite_plan_id or 'missing'}`"
			)
		if expected_family_validation_status and observed_family_validation_status != expected_family_validation_status:
			mismatches.append(
				f"family validation expected `{expected_family_validation_status}` but observed `{observed_family_validation_status or 'missing'}`"
			)
		if expected_semantic_status and observed_semantic_status != expected_semantic_status:
			mismatches.append(
				f"semantic status expected `{expected_semantic_status}` but observed `{observed_semantic_status or 'missing'}`"
			)
		resolved_family_id = observed_family_id or expected_family_id
		latency_assessment = _case_latency_budget_assessment(
			family_id=resolved_family_id,
			proposal_generation_latency_ms=int(max(0, (compiled_audit or {}).get("proposal_generation_latency_ms") or 0)),
			runtime_execution_latency_ms=int(max(0, (compiled_audit or {}).get("runtime_execution_latency_ms") or 0)),
			total_pipeline_latency_ms=int(max(0, (compiled_audit or {}).get("total_pipeline_latency_ms") or 0)),
		)

		return {
			"case_id": case_id,
			"session_name": doc.name,
			"message": message,
			"ok": bool(ok),
			"elapsed_ms": elapsed_ms,
			"answer_text": answer_text,
			"expected_mode": expected_mode,
			"observed_mode": observed_mode,
			"expected_compiler_decision": expected_compiler_decision,
			"observed_compiler_decision": observed_compiler_decision,
			"expected_family_id": expected_family_id,
			"observed_family_id": observed_family_id,
			"expected_composite_plan_id": expected_composite_plan_id,
			"observed_composite_plan_id": observed_composite_plan_id,
			"expected_family_validation_status": expected_family_validation_status,
			"observed_family_validation_status": observed_family_validation_status,
			"expected_semantic_status": expected_semantic_status,
			"observed_semantic_status": observed_semantic_status,
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
			"latency_assessment": latency_assessment,
			"persisted_tool_payload_types": type_names,
			"fallback_payload": fallback_payload,
			"case_ok": bool(ok) and not mismatches,
			"mismatches": mismatches,
		}
	except Exception:
		frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
		raise


def run_phase4b_family_evaluation_suite(set_id: str = "core_governed_families") -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	available_case_sets = [
		str(item.get("set_id") or "").strip()
		for item in list_family_evaluation_case_sets()
		if isinstance(item, dict) and str(item.get("set_id") or "").strip()
	]
	case_set = get_family_evaluation_case_set(set_id)
	if not case_set:
		raise RuntimeError(
			f"Unknown family evaluation case set `{set_id}`. Available sets: {', '.join(available_case_sets) or 'none'}."
		)
	cases = [item for item in list(case_set.get("cases") or []) if isinstance(item, dict)]
	if not cases:
		raise RuntimeError(f"Family evaluation case set `{set_id}` does not contain any cases.")

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
	session_names: List[str] = []
	try:
		conf[flag_key] = True
		conf[percent_key] = 100
		conf[users_key] = []
		results: List[Dict[str, Any]] = []
		for case in cases:
			case_id = str(case.get("case_id") or "").strip()
			try:
				result = _run_family_evaluation_case(case=case, user="Administrator")
			except Exception as exc:
				result = {
					"case_id": case_id,
					"session_name": "",
					"message": str(case.get("message") or "").strip(),
					"ok": False,
					"elapsed_ms": 0,
					"answer_text": "",
					"expected_mode": str(case.get("expected_mode") or "").strip(),
					"observed_mode": "",
					"expected_compiler_decision": str(case.get("expected_compiler_decision") or "").strip(),
					"observed_compiler_decision": "",
					"expected_family_id": str(case.get("family_id") or "").strip(),
					"observed_family_id": "",
					"expected_composite_plan_id": str(case.get("composite_plan_id") or "").strip(),
					"observed_composite_plan_id": "",
					"expected_family_validation_status": str(
						case.get("expected_family_validation_status") or ""
					).strip(),
					"observed_family_validation_status": "",
					"expected_semantic_status": str(case.get("expected_semantic_status") or "").strip(),
					"observed_semantic_status": "",
					"selected_report": "",
					"proposal_generation_latency_ms": 0,
					"runtime_execution_latency_ms": 0,
					"total_pipeline_latency_ms": 0,
					"latency_assessment": {},
					"persisted_tool_payload_types": [],
					"fallback_payload": {},
					"case_ok": False,
					"mismatches": [f"case execution raised `{str(exc).strip() or type(exc).__name__}`"],
				}
			session_name = str(result.get("session_name") or "").strip()
			if session_name:
				session_names.append(session_name)
			results.append(result)
		summary = summarize_compiled_first_turn_audits(
			limit_sessions=max(10, len(session_names)),
			limit_audits=max(50, len(session_names) * 4),
			session_names=session_names,
		)
		failed_cases = [item for item in results if not bool(item.get("case_ok"))]
		return {
			"ok": len(failed_cases) == 0,
			"set_id": str(case_set.get("set_id") or "").strip(),
			"set_label": str(case_set.get("set_label") or "").strip(),
			"description": str(case_set.get("description") or "").strip(),
			"available_case_sets": available_case_sets,
			"case_count": len(results),
			"passed_case_count": len(results) - len(failed_cases),
			"failed_case_count": len(failed_cases),
			"failed_cases": failed_cases,
			"results": results,
			"latency_budget_summary": _family_latency_budget_summary(results),
			"family_metrics": summary.get("family_metrics") if isinstance(summary.get("family_metrics"), dict) else {},
			"audit_summary": summary,
			"rollout_status": get_compiled_first_turn_rollout_status(),
		}
	finally:
		for session_name in session_names:
			try:
				frappe.delete_doc(QWEN_SESSION_DOCTYPE, session_name, ignore_permissions=False)
			except Exception:
				pass
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_phase4b_family_evaluation_smoke(set_id: str = "core_governed_families") -> Dict[str, Any]:
	result = run_phase4b_family_evaluation_suite(set_id=set_id)
	family_metrics = result.get("family_metrics") if isinstance(result.get("family_metrics"), dict) else {}
	if not family_metrics:
		raise RuntimeError(f"Phase 4B family evaluation smoke failed for set `{set_id}`: no family metrics were produced.")
	if int(result.get("case_count") or 0) <= 0:
		raise RuntimeError(f"Phase 4B family evaluation smoke failed for set `{set_id}`: no evaluation cases were executed.")
	return {
		**result,
		"smoke_ok": True,
		"baseline_ok": bool(result.get("ok")),
	}


def run_phase4b_full_family_evaluation_suite() -> Dict[str, Any]:
	set_ids = [
		str(item.get("set_id") or "").strip()
		for item in list_family_evaluation_case_sets()
		if isinstance(item, dict) and str(item.get("set_id") or "").strip()
	]
	if not set_ids:
		raise RuntimeError("No Phase 4B family evaluation case sets are configured.")

	suite_results: List[Dict[str, Any]] = []
	all_results: List[Dict[str, Any]] = []
	failed_cases: List[Dict[str, Any]] = []
	for set_id in set_ids:
		result = run_phase4b_family_evaluation_suite(set_id=set_id)
		suite_results.append(result)
		for item in list(result.get("results") or []):
			if isinstance(item, dict):
				enriched = dict(item)
				enriched["set_id"] = set_id
				all_results.append(enriched)
		for item in list(result.get("failed_cases") or []):
			if isinstance(item, dict):
				enriched = dict(item)
				enriched["set_id"] = set_id
				failed_cases.append(enriched)

	return {
		"ok": len(failed_cases) == 0,
		"set_ids": set_ids,
		"suite_count": len(suite_results),
		"case_count": len(all_results),
		"passed_case_count": len(all_results) - len(failed_cases),
		"failed_case_count": len(failed_cases),
		"failed_cases": failed_cases,
		"latency_budget_summary": _family_latency_budget_summary(all_results),
		"suite_results": suite_results,
	}


def run_phase4b_full_family_evaluation_smoke() -> Dict[str, Any]:
	result = run_phase4b_full_family_evaluation_suite()
	if int(result.get("case_count") or 0) <= 0:
		raise RuntimeError("Phase 4B full family evaluation smoke failed: no evaluation cases were executed.")
	return {
		**result,
		"smoke_ok": True,
		"baseline_ok": bool(result.get("ok")),
	}


def run_phase4b_family_latency_budget_report(set_id: str = "") -> Dict[str, Any]:
	if str(set_id or "").strip():
		result = run_phase4b_family_evaluation_suite(set_id=str(set_id or "").strip())
	else:
		result = run_phase4b_full_family_evaluation_suite()
	latency_budget_summary = (
		result.get("latency_budget_summary")
		if isinstance(result.get("latency_budget_summary"), dict)
		else {}
	)
	families = latency_budget_summary.get("families") if isinstance(latency_budget_summary.get("families"), dict) else {}
	return {
		**result,
		"latency_budget_summary": latency_budget_summary,
		"development_budget_ok": bool(
			families
		)
		and all(
			bool(item.get("within_development_budget"))
			for item in families.values()
			if isinstance(item, dict)
		),
		"enterprise_target_ok": bool(
			families
		)
		and all(
			bool(item.get("within_enterprise_target"))
			for item in families.values()
			if isinstance(item, dict)
		),
	}


def run_phase4b_family_latency_budget_smoke() -> Dict[str, Any]:
	result = run_phase4b_family_latency_budget_report()
	latency_budget_summary = (
		result.get("latency_budget_summary")
		if isinstance(result.get("latency_budget_summary"), dict)
		else {}
	)
	families = latency_budget_summary.get("families") if isinstance(latency_budget_summary.get("families"), dict) else {}
	if not families:
		raise RuntimeError("Phase 4B family latency budget smoke failed: no family latency budget summary was produced.")
	if not bool(result.get("development_budget_ok")):
		raise RuntimeError("Phase 4B family latency budget smoke failed: one or more families exceeded the current development latency budget.")
	return {
		**result,
		"smoke_ok": True,
	}


def run_phase4b_family_tool_surface_smoke(messages: List[str] | None = None) -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	default_messages = [
		"Top 5 customers by revenue",
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
		conf[flag_key] = False
		conf[percent_key] = 0
		conf[users_key] = []
		results: List[Dict[str, Any]] = []
		for message in test_messages:
			expected_surface = build_family_tool_surface_for_message(
				request_id=f"phase4b-family-tool-{uuid.uuid4().hex[:8]}",
				session_id="phase4b-family-tool-surface",
				message=message,
			)
			if expected_surface is None:
				raise RuntimeError(
					f"Phase 4B family tool surface smoke failed: no governed family tool surface was built for `{message}`."
				)
			doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
			doc.title = "Phase 4B Family Tool Surface Smoke"
			doc.insert(ignore_permissions=False)
			try:
				ok, payload = handle_qwen_user_message(
					session_name=doc.name,
					message=message,
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
				family_tool_payload = next(
					(
						item
						for item in reversed(tool_payloads)
						if str(item.get("type") or "").strip() == "qwen_family_tool_surface_contract"
					),
					{},
				)
				if not family_tool_payload:
					raise RuntimeError(
						f"Phase 4B family tool surface smoke failed: family tool contract was not persisted for `{message}`."
					)
				runtime_trace = next(
					(
						item
						for item in reversed(tool_payloads)
						if str(item.get("type") or "").strip() == "qwen_runtime_trace"
					),
					{},
				)
				tool_trace = runtime_trace.get("tool_trace") if isinstance(runtime_trace.get("tool_trace"), list) else []
				tool_names = [str(item.get("tool") or "").strip() for item in tool_trace if isinstance(item, dict)]
				if "erp_fac-report_list" in tool_names:
					raise RuntimeError(
						f"Phase 4B family tool surface smoke failed: runtime used report discovery for `{message}`."
					)
				agent_meta = runtime_trace.get("agent_meta") if isinstance(runtime_trace.get("agent_meta"), dict) else {}
				if not bool(agent_meta.get("family_tool_surface_active")):
					raise RuntimeError(
						f"Phase 4B family tool surface smoke failed: runtime agent meta did not mark family tool routing active for `{message}`."
					)
				if not bool(ok):
					raise RuntimeError(
						f"Phase 4B family tool surface smoke failed: live service did not return ok for `{message}`."
					)
				results.append(
					{
						"message": message,
						"ok": bool(ok),
						"mode": str((payload or {}).get("mode") or "").strip(),
						"candidate_family_ids": list(family_tool_payload.get("candidate_family_ids") or []),
						"preferred_tool_ids": list(family_tool_payload.get("preferred_tool_ids") or []),
						"report_discovery_allowed": bool(family_tool_payload.get("report_discovery_allowed", True)),
						"tool_names": tool_names,
						"agent_meta": agent_meta,
					}
				)
			finally:
				frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
		return {"ok": True, "results": results}
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_phase4b_family_tool_surface_probe() -> Dict[str, Any]:
	checks = [
		("financial_statement", "Show me P & L statement"),
		("aging", "How much payable amount do we have as of now"),
		("ranking_analytics", "Top 5 customers by revenue"),
		("trend_analytics", "Show monthly sales trend"),
		("product_profitability", "which products are performing well last month"),
	]
	results: List[Dict[str, Any]] = []
	for expected_family_id, message in checks:
		contract = build_family_tool_surface_for_message(
			request_id=f"phase4b-family-probe-{uuid.uuid4().hex[:8]}",
			session_id="phase4b-family-tool-probe",
			message=message,
		)
		if contract is None:
			raise RuntimeError(
				f"Phase 4B family tool surface probe failed: no family tool contract was produced for `{message}`."
			)
		candidate_family_ids = list(contract.candidate_family_ids or [])
		if expected_family_id not in candidate_family_ids:
			raise RuntimeError(
				f"Phase 4B family tool surface probe failed: expected family `{expected_family_id}` was not present for `{message}`."
			)
		if contract.report_discovery_allowed:
			raise RuntimeError(
				f"Phase 4B family tool surface probe failed: report discovery remained enabled for `{message}`."
			)
		results.append(
			{
				"message": message,
				"candidate_family_ids": candidate_family_ids,
				"preferred_tool_ids": list(contract.preferred_tool_ids or []),
				"allowed_report_names": list(contract.allowed_report_names or []),
			}
		)
	return {"ok": True, "results": results}


def run_phase4b_clarification_translation_probe() -> Dict[str, Any]:
	cases = [
		{
			"message": "Analyze company health and suggest area to improve",
			"compiler_reason": "Ambiguous capability candidates: financial_statement_read, sales_read, accounts_receivable_read, accounts_payable_read, stock_read, product_performance_read",
			"reason_type": "capability_ambiguity",
		},
		{
			"message": "Show me top 10 products last month by revenue",
			"compiler_reason": "Missing or unresolved required filters: from_date",
			"reason_type": "time_scope_missing",
		},
	]
	results: List[Dict[str, Any]] = []
	for index, case in enumerate(cases, start=1):
		signal = translate_clarification_signal(
			request_id=f"phase4b-clarify-{index}",
			raw_message=str(case.get("message") or "").strip(),
			compiler_reason=str(case.get("compiler_reason") or "").strip(),
		)
		question = str(signal.user_question or "").strip()
		if not question:
			raise RuntimeError("Phase 4B clarification probe failed: translated question was empty.")
		if "Ambiguous capability candidates" in question:
			raise RuntimeError("Phase 4B clarification probe failed: compiler ambiguity leaked into user question.")
		if str(signal.reason_type or "").strip() != str(case.get("reason_type") or "").strip():
			raise RuntimeError("Phase 4B clarification probe failed: clarification reason type did not match expected mapping.")
		results.append(
			{
				"message": str(case.get("message") or "").strip(),
				"reason_type": str(signal.reason_type or "").strip(),
				"user_question": question,
				"suggested_options": list(signal.suggested_options or []),
			}
		)
	return {"ok": True, "results": results}


def run_phase4b_response_policy_probe() -> Dict[str, Any]:
	class _DummyFollowupResolution:
		def __init__(self, mode: str, self_contained: bool) -> None:
			self.mode = mode
			self.self_contained = self_contained

	cases = [
		{
			"message": "How much payable do we have as of now",
			"expected_style": "simple_factual",
		},
		{
			"message": "Analyze AR / AP and evaluate company health",
			"expected_style": "analysis_question",
		},
		{
			"message": "Show me P & L statement",
			"expected_style": "statement_question",
		},
		{
			"message": "show me the latest 7 sale invoices",
			"expected_style": "operational_list",
		},
		{
			"message": "how about all the time",
			"expected_style": "followup_refinement",
			"followup_resolution": _DummyFollowupResolution("local_grounded_transform", False),
		},
	]
	results: List[Dict[str, Any]] = []
	for index, case in enumerate(cases, start=1):
		interaction_contract = build_interaction_contract(
			request_id=f"phase4b-policy-{index}",
			session_id="phase4b-policy-probe",
			user_id="Administrator",
			site_name="erpai_prj1",
			raw_message=str(case.get("message") or "").strip(),
		)
		policy = build_response_policy_contract(
			interaction_contract=interaction_contract,
			followup_resolution=case.get("followup_resolution"),
		)
		if str(policy.answer_style or "").strip() != str(case.get("expected_style") or "").strip():
			raise RuntimeError(
				f"Phase 4B response policy probe failed: `{case.get('message')}` mapped to `{policy.answer_style}` instead of `{case.get('expected_style')}`."
			)
		results.append(policy.to_payload())
	return {"ok": True, "results": results}


def run_phase4b_clarification_policy_smoke() -> Dict[str, Any]:
	clarification = run_phase4b_clarification_translation_probe()
	policy = run_phase4b_response_policy_probe()
	return {
		"ok": True,
		"clarification": clarification,
		"response_policy": policy,
	}


def run_phase4b_natural_narrative_smoke(messages: List[str] | None = None) -> Dict[str, Any]:
	flag_key = "qwen_enable_compiled_first_turn"
	percent_key = "qwen_compiled_first_turn_rollout_percentage"
	users_key = "qwen_compiled_first_turn_rollout_users"
	default_messages = [
		"How much payable amount do we have as of now",
		"Analyze AR / AP and evaluate company health",
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
		conf[percent_key] = 0
		conf[users_key] = ["Administrator"]
		results: List[Dict[str, Any]] = []
		for message in test_messages:
			doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
			doc.title = "Phase 4B Natural Narrative Smoke"
			doc.insert(ignore_permissions=False)
			try:
				ok, payload = handle_qwen_user_message(
					session_name=doc.name,
					message=message,
					user="Administrator",
				)
				if not ok:
					raise RuntimeError(
						f"Phase 4B natural narrative smoke failed: service returned not-ok for `{message}`."
					)
				session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
				tool_payloads = []
				for row in session_doc.get("messages") or []:
					if str(row.role or "").strip().lower() != "tool":
						continue
					payload_obj = _parse_payload(str(row.content or ""))
					if payload_obj:
						tool_payloads.append(payload_obj)
				narrative_payload = _latest_tool_payload_by_type(
					tool_payloads,
					"qwen_artifact_narrative_response_contract",
				)
				if not narrative_payload:
					raise RuntimeError(
						f"Phase 4B natural narrative smoke failed: no narrative response contract was persisted for `{message}`."
					)
				assistant_payload = _latest_assistant_payload(session_doc)
				answer_text = str(assistant_payload.get("text") or "").strip()
				narrative_text = str(narrative_payload.get("answer_text") or "").strip()
				expected_text = _normalize_markdown_units(narrative_text)
				if not narrative_text or answer_text != expected_text:
					raise RuntimeError(
						f"Phase 4B natural narrative smoke failed: assistant answer did not come from the narrative contract for `{message}`."
					)
				results.append(
					{
						"message": message,
						"mode": str((payload or {}).get("mode") or "").strip(),
						"answer_text": answer_text,
						"narrative_engine": str(narrative_payload.get("narrative_engine") or "").strip(),
						"answer_style": str(narrative_payload.get("answer_style") or "").strip(),
					}
				)
			finally:
				frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
		return {"ok": True, "results": results}
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_phase4b_structured_presentation_smoke() -> Dict[str, Any]:
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
		conf[flag_key] = True
		conf[percent_key] = 0
		conf[users_key] = ["Administrator"]
		doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		doc.title = "Phase 4B Structured Presentation Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, _ = handle_qwen_user_message(
				session_name=doc.name,
				message="Analyze AR / AP, and evaluate company health",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Structured presentation smoke failed on initial analysis request.")
			ok, _ = handle_qwen_user_message(
				session_name=doc.name,
				message="Show me the numbers with table, and your facts as bullet points, so that we can see clearly",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Structured presentation smoke failed on presentation follow-up.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			assistant_payload = _latest_assistant_payload(session_doc)
			answer_text = str(assistant_payload.get("text") or "").strip()
			tables = assistant_payload.get("tables") if isinstance(assistant_payload.get("tables"), list) else []
			has_bullets = bool(re.search(r"(^|\n)([-*] |\d+\.\s)", answer_text))
			if not tables:
				raise RuntimeError("Structured presentation smoke failed: expected a markdown table in the final assistant answer.")
			if not has_bullets:
				raise RuntimeError("Structured presentation smoke failed: expected bullet or numbered facts in the final assistant answer.")
			return {
				"ok": True,
				"answer_text": answer_text,
				"table_count": len(tables),
				"has_bullets": has_bullets,
			}
		finally:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_phase4b_context_isolation_smoke() -> Dict[str, Any]:
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
		conf[flag_key] = True
		conf[percent_key] = 0
		conf[users_key] = ["Administrator"]
		doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		doc.title = "Phase 4B Context Isolation Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, _ = handle_qwen_user_message(
				session_name=doc.name,
				message="Show me P & L Statement",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Context isolation smoke failed on initial statement request.")
			ok, trend_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="please perform Monthly Sale Trend by Revenue",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Context isolation smoke failed on same-session monthly trend request.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			trend_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
			if str((trend_payload or {}).get("mode") or "").strip() != "compiled_first_turn":
				raise RuntimeError("Context isolation smoke failed: monthly trend was not treated as a fresh compiled query.")
			if "could not complete a grounded erp lookup" in trend_text.lower():
				raise RuntimeError("Context isolation smoke failed: monthly trend degraded inside the same chat session.")
			ok, staff_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="total number of staff in our company",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Context isolation smoke failed on staff-count request.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			staff_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
			if "profit and loss statement artifact" in staff_text.lower():
				raise RuntimeError("Context isolation smoke failed: unsupported staff query leaked prior P&L artifact context.")
			if "governed hr" not in staff_text.lower() and "headcount" not in staff_text.lower():
				raise RuntimeError("Context isolation smoke failed: unsupported staff query did not return the governed out-of-scope guidance.")
			return {
				"ok": True,
				"trend_mode": str((trend_payload or {}).get("mode") or "").strip(),
				"trend_text": trend_text,
				"staff_mode": str((staff_payload or {}).get("mode") or "").strip(),
				"staff_text": staff_text,
			}
		finally:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_phase4b_entity_drilldown_smoke() -> Dict[str, Any]:
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
		conf[flag_key] = True
		conf[percent_key] = 0
		conf[users_key] = ["Administrator"]
		doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		doc.title = "Phase 4B Entity Drilldown Smoke"
		doc.insert(ignore_permissions=False)
		try:
			ok, _ = handle_qwen_user_message(
				session_name=doc.name,
				message="show me 7 latest sale invoice",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Entity drilldown smoke failed on invoice listing request.")
			ok, invoice_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="give me details of ACC-SINV-2026-00121",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Entity drilldown smoke failed on invoice detail request.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			invoice_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
			if "acc-sinv-2026-00121" not in invoice_text.lower():
				raise RuntimeError("Entity drilldown smoke failed: invoice detail answer did not switch to the requested invoice.")
			if str((invoice_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError("Entity drilldown smoke failed: invoice detail did not use the governed entity-detail engine.")

			ok, _ = handle_qwen_user_message(
				session_name=doc.name,
				message="Top 7 customers by revenue last month",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Entity drilldown smoke failed on ranking request.")
			ok, customer_payload = handle_qwen_user_message(
				session_name=doc.name,
				message="Tell me more about the 35th Street Mobile Wholesale",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Entity drilldown smoke failed on customer detail request.")
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			customer_text = str(_latest_assistant_payload(session_doc).get("text") or "").strip()
			if "35th street mobile wholesale" not in customer_text.lower():
				raise RuntimeError("Entity drilldown smoke failed: customer detail answer did not switch to the requested customer.")
			if str((customer_payload or {}).get("agent_meta", {}).get("engine") or "").strip() != "entity_detail":
				raise RuntimeError("Entity drilldown smoke failed: customer detail did not use the governed entity-detail engine.")
			return {
				"ok": True,
				"invoice_mode": str((invoice_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"invoice_text": invoice_text,
				"customer_mode": str((customer_payload or {}).get("agent_meta", {}).get("engine") or "").strip(),
				"customer_text": customer_text,
			}
		finally:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass


def run_phase4b_entity_drilldown_probe() -> Dict[str, Any]:
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
		conf[flag_key] = True
		conf[percent_key] = 0
		conf[users_key] = ["Administrator"]
		doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		doc.title = "Phase 4B Entity Drilldown Probe"
		doc.insert(ignore_permissions=False)
		try:
			first = handle_qwen_user_message(
				session_name=doc.name,
				message="show me 7 latest sale invoice",
				user="Administrator",
			)
			second = handle_qwen_user_message(
				session_name=doc.name,
				message="give me details of ACC-SINV-2026-00121",
				user="Administrator",
			)
			third = handle_qwen_user_message(
				session_name=doc.name,
				message="Top 7 customers by revenue last month",
				user="Administrator",
			)
			fourth = handle_qwen_user_message(
				session_name=doc.name,
				message="Tell me more about the 35th Street Mobile Wholesale",
				user="Administrator",
			)
			session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
			assistant_payload = _latest_assistant_payload(session_doc)
			tool_payloads = []
			for row in session_doc.get("messages") or []:
				if str(row.role or "").strip().lower() != "tool":
					continue
				payload_obj = _parse_payload(str(row.content or ""))
				if payload_obj:
					tool_payloads.append(payload_obj)
			return {
				"ok": True,
				"first": first,
				"second": second,
				"third": third,
				"fourth": fourth,
				"assistant_text": str(assistant_payload.get("text") or "").strip(),
				"assistant_payload": assistant_payload,
				"recent_tool_types": [str(item.get("type") or "").strip() for item in tool_payloads[-12:]],
				"recent_trace": _latest_qwen_trace_payload(session_doc),
				"latest_grounded_turn": _latest_grounded_turn_contract(session_doc),
				"latest_artifact": _latest_normalized_family_artifact(session_doc),
			}
		finally:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	finally:
		for key, was_present in presence.items():
			if was_present:
				conf[key] = originals.get(key)
			else:
				try:
					conf.pop(key, None)
				except Exception:
					pass
