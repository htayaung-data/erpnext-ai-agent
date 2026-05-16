from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Dict, List, Tuple

from .natural_business_understanding_contracts import CONTRACT_VERSION
from .authorized_emission import (
	ANSWER_TYPE_TRACE,
	emit_authorized_assistant_answer,
)
from .model_role_observability import (
	ROLE_DETERMINISTIC,
	build_model_role_observability_contract,
)
from .model_role_coverage import (
	build_deterministic_model_role_contract_bundle,
	build_model_role_coverage_contract,
)
from .model_role_strict_readiness import build_model_role_strict_readiness_contract
from .policy_boundary_uniformity import build_policy_boundary_uniformity_contract
from .visible_context_frame_stack import (
	build_visible_context_frame_stack,
	resolve_visible_context_frame_arbitration,
)


AppendMessage = Callable[[Any, str, str], None]
AppendToolPayload = Callable[[Any, Dict[str, Any]], None]
AssistantTextPayload = Callable[[str], str]
SaveSession = Callable[..., None]

TRACE_PAYLOAD_TYPE = "qwen_visible_context_followup_trace_contract"
INSPECTION_PAYLOAD_TYPE = "qwen_visible_context_authority_trace_inspection_contract"
AUDIT_PAYLOAD_TYPE = "qwen_audit_envelope"
FINAL_AUTHORITY_PAYLOAD_TYPE = "qwen_final_answer_authority_contract"


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
	messages = _session_messages(session_doc)
	assistant_index = _latest_assistant_message_index(messages)
	if assistant_index >= 0:
		user_index = _previous_user_message_index(messages, assistant_index)
		for index in range(len(messages) - 1, user_index, -1):
			payload = _trace_payload_from_message(messages[index])
			if payload:
				return payload
		synthetic_trace = _synthesize_turn_level_trace_from_assistant_message(
			messages[assistant_index],
			raw_message=_message_text(messages[user_index]) if user_index >= 0 else "",
		)
		if synthetic_trace:
			return synthetic_trace
	for message in reversed(messages):
		payload = _trace_payload_from_message(message)
		if payload:
			return payload
	return {}


def _trace_payload_from_message(message: Any) -> Dict[str, Any]:
	if _message_role(message) != "tool":
		return {}
	payload = _safe_json_loads(_message_content(message))
	if _clean_text(payload.get("type")) == TRACE_PAYLOAD_TYPE:
		return payload
	return {}


def _latest_assistant_message_index(messages: List[Any]) -> int:
	for index in range(len(messages) - 1, -1, -1):
		if _message_role(messages[index]) == "assistant":
			return index
	return -1


def _previous_user_message_index(messages: List[Any], before_index: int) -> int:
	for index in range(before_index - 1, -1, -1):
		if _message_role(messages[index]) == "user":
			return index
	return -1


def _message_text(message: Any) -> str:
	content = _message_content(message)
	if isinstance(content, dict):
		return _clean_text(content.get("text") or content.get("message") or content.get("content") or content.get("answer_text"))
	return _clean_text(content)


def _assistant_text_from_content(content: Any) -> str:
	if isinstance(content, dict):
		return _clean_text(
			content.get("text")
			or content.get("message")
			or content.get("content")
			or content.get("answer_text")
			or content.get("markdown")
		)
	text = _clean_text(content)
	if not text:
		return ""
	payload = _safe_json_loads(text)
	if payload:
		return _clean_text(payload.get("text") or payload.get("message") or payload.get("content"))
	return text


def _artifact_identity_from_frame(frame: Dict[str, Any]) -> str:
	return _clean_text(frame.get("artifact_id") or frame.get("frame_id"))


def _report_family_from_frame(frame: Dict[str, Any]) -> str:
	return _clean_text(frame.get("family_id") or frame.get("artifact_title") or frame.get("artifact_id") or frame.get("frame_id"))


def _projection_fields_from_frame(frame: Dict[str, Any]) -> List[str]:
	fields: List[str] = []
	for column in _clean_list(frame.get("columns")):
		clean_column = _clean_dict(column)
		value = _clean_text(clean_column.get("key") or clean_column.get("label"))
		if value and value not in fields:
			fields.append(value)
	return fields


def _synthesize_turn_level_trace_from_assistant_message(message: Any, *, raw_message: str) -> Dict[str, Any]:
	assistant_text = _assistant_text_from_content(_message_content(message))
	if not assistant_text:
		return {}
	if "Context Authority Trace" in assistant_text and "Authority Summary" in assistant_text:
		return {}
	synthetic_session = {"messages": [{"role": "assistant", "content": assistant_text}]}
	frame_stack = build_visible_context_frame_stack(synthetic_session, limit=1)
	frames = _frame_stack_frames({"context_frame_stack": frame_stack})
	if not frames:
		return {}
	frame_arbitration = resolve_visible_context_frame_arbitration(
		raw_message=raw_message or "current table",
		frame_stack=frame_stack,
	)
	if _clean_text(frame_arbitration.get("status")) not in {"resolved", "fresh_query", "projection"}:
		return {}
	selected_frame = _frame_by_id({"context_frame_stack": frame_stack}, _clean_text(frame_arbitration.get("selected_frame_id")))
	if not selected_frame:
		selected_frame = frames[0]
	projection_fields = _projection_fields_from_frame(selected_frame)
	artifact_id = _artifact_identity_from_frame(selected_frame)
	report_family = _report_family_from_frame(selected_frame)
	entity_type = _clean_text(frame_arbitration.get("selected_business_object_type") or selected_frame.get("business_object_type"))
	answer_mode = "turn_level_rendered_artifact"
	authority = _synthetic_final_answer_authority(
		raw_message=raw_message,
		artifact_id=artifact_id,
		report_family=report_family,
		entity_type=entity_type,
		answer_mode=answer_mode,
	)
	model_role_observability = build_model_role_observability_contract(
		lane="erp_report_execution",
		role_owner="turn_level_trace_recency_contract",
		model_role=ROLE_DETERMINISTIC,
		model_name="none",
		fallback_used=False,
		strict_mode_enforced=False,
		runtime_source="deterministic_turn_level_trace_publication",
	)
	model_role_strict_readiness = build_model_role_strict_readiness_contract(
		model_role_observability=model_role_observability,
		lane="erp_report_execution",
		strict_enforcement_enabled=False,
	)
	policy_model_role_bundle = build_deterministic_model_role_contract_bundle(
		lane="policy_boundary_rendering",
		role_owner="policy_boundary_uniformity_contract",
		runtime_source="deterministic_policy_boundary_renderer",
		strict_enforcement_enabled=False,
	)
	model_role_coverage = build_model_role_coverage_contract(
		observed_contracts=[
			model_role_observability,
			policy_model_role_bundle["model_role_observability"],
		],
		strict_enforcement_enabled=False,
	)
	policy_boundary_uniformity = build_policy_boundary_uniformity_contract(
		raw_message=raw_message,
		route=answer_mode,
		visible_authority_intent="safe_visible_fact",
		selected_report_family=report_family,
		entity_type=entity_type,
		evidence_scope=_clean_text(frame_arbitration.get("selected_evidence_scope") or selected_frame.get("evidence_scope")),
		visible_metric_lines=[],
	)
	return {
		"type": TRACE_PAYLOAD_TYPE,
		"contract_version": CONTRACT_VERSION,
		"request_id": f"turn-level:{artifact_id or 'rendered-artifact'}",
		"raw_message": _clean_text(raw_message),
		"answer_mode": answer_mode,
		"trace_publish_status": "published_from_latest_assistant_artifact",
		"trace_publish_reason": "The latest user-visible answer rendered a visible artifact without a dedicated follow-up trace, so trace inspection published authority from the rendered artifact contract.",
		"projection_fields": projection_fields,
		"resolution": {
			"status": "resolved",
			"reason": "Resolved from the latest user-visible rendered artifact.",
			"resolved_artifact_id": artifact_id,
			"resolved_entity": {},
		},
		"context_frame_stack": frame_stack,
		"frame_arbitration": {
			**frame_arbitration,
			"selected_report_family": report_family,
			"status": "fresh_query",
		},
		"authority_observability": {
			"relation": _clean_text(frame_arbitration.get("relation")),
			"requested_object_label": _clean_text(frame_arbitration.get("requested_object_label")),
			"selected_frame_id": _clean_text(frame_arbitration.get("selected_frame_id")),
			"selected_artifact_id": artifact_id,
			"selected_business_object_type": entity_type,
			"selected_evidence_scope": _clean_text(frame_arbitration.get("selected_evidence_scope") or selected_frame.get("evidence_scope")),
			"selected_recovery_source": _clean_text(frame_arbitration.get("selected_recovery_source")),
			"selection_strategy": _clean_text(frame_arbitration.get("selection_strategy")),
			"candidate_frame_count": _clean_text(frame_arbitration.get("candidate_frame_count")),
			"rejected_frame_count": len(_clean_list(frame_arbitration.get("rejected_frames"))),
		},
		"semantic_ownership_ledger": _synthetic_semantic_ownership_ledger(
			artifact_id=artifact_id,
			report_family=report_family,
			entity_type=entity_type,
			answer_mode=answer_mode,
		),
		"policy_boundary_uniformity": policy_boundary_uniformity,
		"model_role_observability": model_role_observability,
		"model_role_strict_readiness": model_role_strict_readiness,
		"policy_model_role_observability": policy_model_role_bundle["model_role_observability"],
		"policy_model_role_strict_readiness": policy_model_role_bundle["model_role_strict_readiness"],
		"model_role_coverage": model_role_coverage,
		"final_answer_authority": authority,
		"created_at_unix": time.time(),
	}


def _synthetic_semantic_ownership_ledger(
	*,
	artifact_id: str,
	report_family: str,
	entity_type: str,
	answer_mode: str,
) -> Dict[str, Any]:
	return {
		"type": "qwen_semantic_ownership_ledger_contract",
		"contract_version": CONTRACT_VERSION,
		"decision_owners": {
			"route": "turn_level_trace_recency_contract",
			"context": "latest_rendered_artifact_resolver",
			"row_entity_metric": "latest_rendered_artifact_resolver",
			"policy": "policy_boundary_uniformity_contract",
			"renderer": "source_answer_renderer",
		},
		"resolved_context": {
			"artifact_id": _clean_text(artifact_id),
			"report_family": _clean_text(report_family),
			"entity_type": _clean_text(entity_type),
			"row_reference": "none",
		},
		"authority": {
			"authority_source": "visible_rendered_table",
			"evidence_scope": "visible_rendered_table",
			"policy_boundary": "none",
			"answer_mode": _clean_text(answer_mode),
		},
		"override_policy": {"non_owner_override_allowed": False},
	}


def _synthetic_final_answer_authority(
	*,
	raw_message: str,
	artifact_id: str,
	report_family: str,
	entity_type: str,
	answer_mode: str,
) -> Dict[str, Any]:
	return {
		"type": FINAL_AUTHORITY_PAYLOAD_TYPE,
		"contract_version": CONTRACT_VERSION,
		"request_id": f"turn-level:{_clean_text(artifact_id) or 'rendered-artifact'}",
		"raw_message": _clean_text(raw_message),
		"authority_source": "visible_rendered_table",
		"evidence_scope": "visible_rendered_table",
		"selected_artifact_id": _clean_text(artifact_id),
		"selected_report_family": _clean_text(report_family),
		"selected_entity_type": _clean_text(entity_type),
		"selected_row_reference": "none",
		"policy_boundary": "none",
		"answer_mode": _clean_text(answer_mode),
		"renderer_owner": "source_answer_renderer",
		"authority_complete": True,
		"preflight_status": "passed",
		"missing_fields": [],
		"authority_reason": "Final answer authority was published from the latest rendered artifact for trace recency.",
	}


def _latest_audit_envelope(session_doc: Any, *, request_id: str = "") -> Dict[str, Any]:
	fallback: Dict[str, Any] = {}
	target_request_id = _clean_text(request_id)
	for message in reversed(_session_messages(session_doc)):
		if _message_role(message) != "tool":
			continue
		payload = _safe_json_loads(_message_content(message))
		if _clean_text(payload.get("type")) != AUDIT_PAYLOAD_TYPE:
			continue
		authority = _clean_dict(payload.get("final_answer_authority"))
		if not authority:
			continue
		if not fallback:
			fallback = payload
		if target_request_id and _clean_text(payload.get("request_id")) == target_request_id:
			return payload
	return fallback


def latest_final_answer_authority_contract(
	session_doc: Any,
	*,
	trace_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	trace = _clean_dict(trace_payload)
	audit = _latest_audit_envelope(session_doc, request_id=_clean_text(trace.get("request_id")))
	authority = _clean_dict(audit.get("final_answer_authority"))
	if _clean_text(authority.get("type")) == FINAL_AUTHORITY_PAYLOAD_TYPE:
		return authority
	authority = _clean_dict(trace.get("final_answer_authority"))
	if _clean_text(authority.get("type")) == FINAL_AUTHORITY_PAYLOAD_TYPE:
		return authority
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
	if isinstance(value, bool):
		return "True" if value else "False"
	text = _clean_text(value)
	if not text:
		return "none"
	return text.replace("|", "\\|").replace("\n", " ")


def _md_bool(value: Any) -> str:
	if isinstance(value, bool):
		return "True" if value else "False"
	if value is None:
		return "unknown"
	return _md_value(value)


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


def _normalized_trace_status(
	*,
	arbitration: Dict[str, Any],
	resolution: Dict[str, Any],
	authority_payload: Dict[str, Any],
) -> str:
	answer_mode = _clean_text(authority_payload.get("answer_mode"))
	policy_boundary = _clean_text(authority_payload.get("policy_boundary"))
	preflight_status = _clean_text(authority_payload.get("preflight_status"))
	resolution_status = _clean_text(resolution.get("status"))
	arbitration_status = _clean_text(arbitration.get("status"))
	for value in (answer_mode, policy_boundary, resolution_status, arbitration_status):
		if value in {"out_of_range", "visible_context_out_of_range"}:
			return "out_of_range"
		if value == "missing_requested_object":
			return "missing_requested_object"
		if value == "ambiguous":
			return "ambiguous"
	if preflight_status == "bounded" or (policy_boundary and policy_boundary != "none"):
		return "boundary"
	return arbitration_status or resolution_status or "unknown"


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


def _append_final_answer_authority(lines: List[str], authority_payload: Dict[str, Any]) -> None:
	authority = _clean_dict(authority_payload)
	if not authority:
		return
	missing_fields = [
		_clean_text(value)
		for value in _clean_list(authority.get("missing_fields"))
		if _clean_text(value)
	]
	lines.extend(["", "**Final Answer Authority**"])
	_append_kv_table(
		lines,
		[
			("Authority source", authority.get("authority_source") or "none"),
			("Evidence scope", authority.get("evidence_scope") or "none"),
			("Selected artifact", authority.get("selected_artifact_id") or "none"),
			("Selected report family", authority.get("selected_report_family") or "none"),
			("Selected row reference", authority.get("selected_row_reference") or "none"),
			("Policy boundary", authority.get("policy_boundary") or "none"),
			("Answer mode", authority.get("answer_mode") or "none"),
			("Renderer owner", authority.get("renderer_owner") or "none"),
			("Authority complete", authority.get("authority_complete")),
			("Preflight status", authority.get("preflight_status") or "none"),
			("Missing fields", ", ".join(missing_fields) if missing_fields else "none"),
			("Authority reason", authority.get("authority_reason") or "none"),
		],
	)


def _append_policy_boundary_uniformity(lines: List[str], contract_payload: Dict[str, Any]) -> None:
	contract = _clean_dict(contract_payload)
	if not contract:
		return
	blocked_claim_types = [
		_clean_text(value)
		for value in _clean_list(contract.get("blocked_claim_types"))
		if _clean_text(value)
	]
	safe_alternatives = [
		_clean_text(value)
		for value in _clean_list(contract.get("safe_alternative_actions"))
		if _clean_text(value)
	]
	lines.extend(["", "**Policy Boundary Uniformity**"])
	_append_kv_table(
		lines,
		[
			("Policy owner", contract.get("policy_owner") or "none"),
			("Source", contract.get("source") or "none"),
			("Policy intent class", contract.get("policy_intent_class") or "none"),
			("Policy boundary", contract.get("policy_boundary") or "none"),
			("Boundary applies", contract.get("boundary_applies")),
			("Allowed answer mode", contract.get("allowed_answer_mode") or "none"),
			("Selected report family", contract.get("selected_report_family") or "none"),
			("Entity type", contract.get("entity_type") or "none"),
			("Approved model required", contract.get("approved_model_required")),
			("Approved policy required", contract.get("approved_policy_required")),
			("Approved trend required", contract.get("approved_trend_required")),
			("Blocked claim types", ", ".join(blocked_claim_types) if blocked_claim_types else "none"),
			("Safe alternatives", " / ".join(safe_alternatives[:3]) if safe_alternatives else "none"),
			("Renderer instruction", contract.get("renderer_instruction") or "none"),
		],
	)


def _append_model_role_observability(lines: List[str], contract_payload: Dict[str, Any]) -> None:
	contract = _clean_dict(contract_payload)
	if not contract:
		return
	lines.extend(["", "**Model Role Observability**"])
	_append_kv_table(
		lines,
		[
			("Lane", contract.get("lane") or "none"),
			("Role owner", contract.get("role_owner") or "none"),
			("Model role", contract.get("model_role") or "none"),
			("Expected model role", contract.get("expected_model_role") or "none"),
			("Role compliance", contract.get("role_compliance") or "none"),
			("Model name", contract.get("model_name") or "unknown"),
			("Fallback used", contract.get("fallback_used")),
			("Fallback reason", contract.get("fallback_reason") or "none"),
			("Strict mode enforced", contract.get("strict_mode_enforced")),
			("Runtime source", contract.get("runtime_source") or "none"),
		],
	)


def _append_model_role_strict_readiness(lines: List[str], contract_payload: Dict[str, Any]) -> None:
	contract = _clean_dict(contract_payload)
	if not contract:
		return
	missing_fields = [
		_clean_text(value)
		for value in _clean_list(contract.get("missing_fields"))
		if _clean_text(value)
	]
	lines.extend(["", "**Model Role Strict Readiness**"])
	_append_kv_table(
		lines,
		[
			("Readiness owner", contract.get("readiness_owner") or "none"),
			("Lane", contract.get("lane") or "none"),
			("Readiness status", contract.get("readiness_status") or "none"),
			("Strict enforcement ready", contract.get("strict_enforcement_ready")),
			("Runtime safe without model enforcement", contract.get("runtime_safe_without_model_enforcement")),
			("Strict enforcement enabled", contract.get("strict_enforcement_enabled")),
			("Blocking", contract.get("blocking")),
			("Requires AI runtime", contract.get("requires_ai_runtime")),
			("Deterministic lane", contract.get("deterministic_lane")),
			("Missing fields", ", ".join(missing_fields) if missing_fields else "none"),
			("Readiness reason", contract.get("readiness_reason") or "none"),
		],
	)


def _append_model_role_coverage(lines: List[str], contract_payload: Dict[str, Any]) -> None:
	contract = _clean_dict(contract_payload)
	if not contract:
		return
	uncovered_lanes = [
		_clean_text(value)
		for value in _clean_list(contract.get("uncovered_lanes"))
		if _clean_text(value)
	]
	blocking_lanes = [
		_clean_text(value)
		for value in _clean_list(contract.get("blocking_lanes"))
		if _clean_text(value)
	]
	lines.extend(["", "**Model Role Coverage**"])
	_append_kv_table(
		lines,
		[
			("Coverage owner", contract.get("coverage_owner") or "none"),
			("Coverage status", contract.get("coverage_status") or "none"),
			("Coverage complete", contract.get("coverage_complete")),
			("Global strict enforcement safe", contract.get("global_strict_enforcement_safe")),
			("Strict enforcement enabled", contract.get("strict_enforcement_enabled")),
			("Required lane count", contract.get("required_lane_count") or 0),
			("Observed lane count", contract.get("observed_lane_count") or 0),
			("Uncovered lane count", contract.get("uncovered_lane_count") or 0),
			("Blocking lane count", contract.get("blocking_lane_count") or 0),
			("Uncovered lanes", ", ".join(uncovered_lanes) if uncovered_lanes else "none"),
			("Blocking lanes", ", ".join(blocking_lanes) if blocking_lanes else "none"),
		],
	)


def render_visible_context_authority_trace(
	trace_payload: Dict[str, Any],
	*,
	final_answer_authority: Dict[str, Any] | None = None,
) -> str:
	trace = _clean_dict(trace_payload)
	authority_payload = _clean_dict(final_answer_authority)
	if not trace:
		lines = [
			"Context Authority Trace\n\n"
			"No visible-context authority trace is available yet. Run a visible table follow-up first, "
			"then ask for the latest context authority trace."
		]
		_append_final_answer_authority(lines, authority_payload)
		return "\n".join(lines).strip()
	arbitration = _clean_dict(trace.get("frame_arbitration"))
	resolution = _clean_dict(trace.get("resolution"))
	observability = _clean_dict(trace.get("authority_observability"))
	status = _normalized_trace_status(
		arbitration=arbitration,
		resolution=resolution,
		authority_payload=authority_payload,
	)
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
			("Answer mode", _clean_text(trace.get("answer_mode")) or "none"),
			("Trace publish status", _clean_text(trace.get("trace_publish_status")) or "explicit_trace"),
			("Trace publish reason", _clean_text(trace.get("trace_publish_reason")) or "none"),
			("Relation", _clean_text(arbitration.get("relation") or observability.get("relation")) or "unknown"),
			("Requested object", requested_object),
			("Selected frame", selected_frame_id or "none"),
			("Selected table", selected_title or "none"),
			("Selected report family", _clean_text(arbitration.get("selected_report_family") or selected_frame.get("family_id")) or "none"),
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
				"Requested row limit",
				_clean_text(arbitration.get("selected_requested_limit") or observability.get("selected_requested_limit")) or "none",
			),
			(
				"Selection strategy",
				_clean_text(arbitration.get("selection_strategy") or observability.get("selection_strategy")) or "none",
			),
			("Recovery source", recovery_source),
			("Projection fields", ", ".join(_clean_list(trace.get("projection_fields"))) or "none"),
		],
	)
	ledger = _clean_dict(trace.get("semantic_ownership_ledger"))
	if ledger:
		owners = _clean_dict(ledger.get("decision_owners"))
		resolved_context = _clean_dict(ledger.get("resolved_context"))
		authority = _clean_dict(ledger.get("authority"))
		lines.extend(["", "**Semantic Ownership Ledger**"])
		_append_kv_table(
			lines,
			[
				("Route owner", owners.get("route") or "none"),
				("Context owner", owners.get("context") or "none"),
				("Row/entity/metric owner", owners.get("row_entity_metric") or "none"),
				("Policy owner", owners.get("policy") or "none"),
				("Renderer owner", owners.get("renderer") or "none"),
				("Ledger artifact", resolved_context.get("artifact_id") or "none"),
				("Ledger report family", resolved_context.get("report_family") or "none"),
				("Ledger entity type", resolved_context.get("entity_type") or "none"),
				("Ledger row reference", resolved_context.get("row_reference") or "none"),
				("Authority source", authority.get("authority_source") or "none"),
				("Policy boundary", authority.get("policy_boundary") or "none"),
				(
					"Non-owner override allowed",
					_md_bool(_clean_dict(ledger.get("override_policy")).get("non_owner_override_allowed")),
				),
			],
		)
	_append_model_role_observability(lines, _clean_dict(trace.get("model_role_observability")))
	_append_model_role_strict_readiness(lines, _clean_dict(trace.get("model_role_strict_readiness")))
	_append_model_role_coverage(lines, _clean_dict(trace.get("model_role_coverage")))
	_append_policy_boundary_uniformity(lines, _clean_dict(trace.get("policy_boundary_uniformity")))
	_append_final_answer_authority(lines, authority_payload)
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
	final_answer_authority: Dict[str, Any] | None = None,
	answer_text: str,
) -> Dict[str, Any]:
	arbitration = _clean_dict(trace_payload.get("frame_arbitration"))
	resolution = _clean_dict(trace_payload.get("resolution"))
	observability = _clean_dict(trace_payload.get("authority_observability"))
	authority = _clean_dict(final_answer_authority)
	policy_uniformity = _clean_dict(trace_payload.get("policy_boundary_uniformity"))
	model_role_observability = _clean_dict(trace_payload.get("model_role_observability"))
	model_role_strict_readiness = _clean_dict(trace_payload.get("model_role_strict_readiness"))
	model_role_coverage = _clean_dict(trace_payload.get("model_role_coverage"))
	trace_status = _normalized_trace_status(
		arbitration=arbitration,
		resolution=resolution,
		authority_payload=authority,
	)
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
		"trace_status": trace_status,
		"relation": _clean_text(arbitration.get("relation") or observability.get("relation")),
		"requested_object_label": _clean_text(arbitration.get("requested_object_label") or observability.get("requested_object_label")),
		"selected_frame_id": _clean_text(arbitration.get("selected_frame_id") or observability.get("selected_frame_id")),
		"selected_business_object_type": _clean_text(
			arbitration.get("selected_business_object_type") or observability.get("selected_business_object_type")
		),
		"selected_recovery_source": _clean_text(arbitration.get("selected_recovery_source") or observability.get("selected_recovery_source")),
		"candidate_frame_count": len(_clean_list(arbitration.get("candidate_frames"))),
		"rejected_frame_count": len(_clean_list(arbitration.get("rejected_frames"))),
		"final_answer_authority_available": bool(authority),
		"final_answer_authority_source": _clean_text(authority.get("authority_source")),
		"final_answer_evidence_scope": _clean_text(authority.get("evidence_scope")),
		"final_answer_policy_boundary": _clean_text(authority.get("policy_boundary")),
		"final_answer_preflight_status": _clean_text(authority.get("preflight_status")),
		"final_answer_authority_complete": bool(authority.get("authority_complete")) if authority else False,
		"policy_boundary_uniformity_available": bool(policy_uniformity),
		"policy_boundary_uniformity_source": _clean_text(policy_uniformity.get("source")),
		"policy_boundary_uniformity_intent_class": _clean_text(policy_uniformity.get("policy_intent_class")),
		"policy_boundary_uniformity_boundary": _clean_text(policy_uniformity.get("policy_boundary")),
		"policy_boundary_uniformity_applies": bool(policy_uniformity.get("boundary_applies")) if policy_uniformity else False,
		"model_role_observability_available": bool(model_role_observability),
		"model_role_lane": _clean_text(model_role_observability.get("lane")),
		"model_role_owner": _clean_text(model_role_observability.get("role_owner")),
		"model_role": _clean_text(model_role_observability.get("model_role")),
		"model_role_expected": _clean_text(model_role_observability.get("expected_model_role")),
		"model_role_compliance": _clean_text(model_role_observability.get("role_compliance")),
		"model_role_fallback_used": bool(model_role_observability.get("fallback_used")) if model_role_observability else False,
		"model_role_strict_readiness_available": bool(model_role_strict_readiness),
		"model_role_strict_readiness_status": _clean_text(model_role_strict_readiness.get("readiness_status")),
		"model_role_strict_enforcement_ready": bool(model_role_strict_readiness.get("strict_enforcement_ready"))
		if model_role_strict_readiness
		else False,
		"model_role_runtime_safe_without_model_enforcement": bool(
			model_role_strict_readiness.get("runtime_safe_without_model_enforcement")
		)
		if model_role_strict_readiness
		else False,
		"model_role_strict_enforcement_enabled": bool(model_role_strict_readiness.get("strict_enforcement_enabled"))
		if model_role_strict_readiness
		else False,
		"model_role_strict_readiness_blocking": bool(model_role_strict_readiness.get("blocking"))
		if model_role_strict_readiness
		else False,
		"model_role_coverage_available": bool(model_role_coverage),
		"model_role_coverage_status": _clean_text(model_role_coverage.get("coverage_status")),
		"model_role_coverage_complete": bool(model_role_coverage.get("coverage_complete")) if model_role_coverage else False,
		"model_role_global_strict_enforcement_safe": bool(model_role_coverage.get("global_strict_enforcement_safe"))
		if model_role_coverage
		else False,
		"model_role_uncovered_lanes": _clean_list(model_role_coverage.get("uncovered_lanes")),
		"model_role_blocking_lanes": _clean_list(model_role_coverage.get("blocking_lanes")),
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
	final_answer_authority = latest_final_answer_authority_contract(session_doc, trace_payload=trace_payload)
	answer_text = render_visible_context_authority_trace(
		trace_payload,
		final_answer_authority=final_answer_authority,
	)
	if not user_message_already_appended:
		append_message(session_doc, "user", raw_message)
	inspection_payload = _inspection_contract(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		raw_message=raw_message,
		trace_payload=trace_payload,
		final_answer_authority=final_answer_authority,
		answer_text=answer_text,
	)
	model_role_observability = build_model_role_observability_contract(
		lane="visible_context_trace_inspection",
		role_owner="visible_context_trace_inspection",
		model_role=ROLE_DETERMINISTIC,
		model_name="none",
		fallback_used=False,
		strict_mode_enforced=False,
		runtime_source="deterministic_trace_inspection_renderer",
	)
	model_role_strict_readiness = build_model_role_strict_readiness_contract(
		model_role_observability=model_role_observability,
		lane="visible_context_trace_inspection",
		strict_enforcement_enabled=False,
	)
	inspection_payload["model_role_observability"] = model_role_observability
	inspection_payload["model_role_strict_readiness"] = model_role_strict_readiness
	execution_path_payload = {
		"type": "qwen_execution_path",
		"contract_version": CONTRACT_VERSION,
		"request_id": _clean_text(request_id),
		"path": "visible_context_trace_inspection",
		"reason": "The user explicitly requested inspection of the latest visible-context authority trace.",
		"requires_runtime": False,
		"grounded_required": False,
		"model_role_observability": model_role_observability,
		"model_role_strict_readiness": model_role_strict_readiness,
	}
	pre_assistant_payloads = [
		payload
		for payload in (additional_tool_payloads or [])
		if isinstance(payload, dict) and payload
	]
	pre_assistant_payloads.extend([inspection_payload, execution_path_payload])
	authorized_emission = emit_authorized_assistant_answer(
		session_doc=session_doc,
		answer_text=answer_text,
		answer_type=ANSWER_TYPE_TRACE,
		append_message=append_message,
		append_tool_payload=append_tool_payload,
		assistant_text_payload=assistant_text_payload,
		control_meta_authority={
			"authority_source": "trace_debug",
			"answer_mode": "visible_context_trace_inspection",
			"reason": "The user explicitly requested inspection of the latest visible-context authority trace.",
			"preflight_status": "passed",
		},
		pre_assistant_tool_payloads=pre_assistant_payloads,
	)
	save_session(session_doc, ignore_permissions=False)
	return True, {
		"ok": bool(authorized_emission.emitted),
		"request_id": request_id,
		"mode": "visible_context_trace_inspection",
		"agent_meta": {
			"engine": "visible_context_trace_inspection",
			"trace_available": bool(trace_payload),
			"model_role_observability": model_role_observability,
			"model_role_strict_readiness": model_role_strict_readiness,
			"status": _normalized_trace_status(
				arbitration=_clean_dict(trace_payload.get("frame_arbitration")),
				resolution=_clean_dict(trace_payload.get("resolution")),
				authority_payload=final_answer_authority,
			),
			"authorized_emission": authorized_emission.to_payload(),
		},
	}
