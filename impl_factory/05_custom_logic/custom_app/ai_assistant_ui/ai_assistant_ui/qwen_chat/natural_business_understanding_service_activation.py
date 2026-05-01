from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Dict, List, Tuple

from .metadata import (
	load_capability_registry,
	load_composite_family_registry,
	load_governed_kpi_execution_registry,
	load_report_registry,
)
from .natural_business_understanding_activation import build_nbu_activation_assessment
from .natural_business_understanding_arbitration import nbu_activation_level_supports_action
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .natural_business_understanding_context_graph import resolve_nbu_context_graph_reference
from .natural_business_understanding_context_resolution import nbu_ordinal_reference_index
from .natural_business_understanding_response_renderer import render_nbu_professional_response
from .natural_business_understanding_runtime import interpret_natural_business_understanding_shadow
from .natural_business_understanding_schema_hardening import validate_nbu_trace_schema_hardening
from .natural_business_understanding_visible_artifacts import session_visible_rendered_artifacts


AppendMessage = Callable[[Any, str, str], None]
AppendToolPayload = Callable[[Any, Dict[str, Any]], None]
AssistantTextPayload = Callable[[str], str]
SaveSession = Callable[..., None]

LIVE_PRESENTATION_ACTIONS = {
	"ask_clarification",
	"show_supported_options",
	"reject_with_boundary",
	"out_of_scope_response",
	"answer_capability_question",
}

NBU_ALWAYS_ON_SHADOW_AUDIT_VERSION = "1.0"

MONEY_FIELD_HINTS = (
	"amount",
	"total",
	"balance",
	"outstanding",
	"overdue",
	"credit",
	"value",
	"payable",
	"receivable",
)

VISIBLE_CONTEXT_TERMS = {
	"above",
	"current",
	"latest",
	"last",
	"rank",
	"row",
	"position",
	"table",
	"that",
	"this",
	"it",
	"same",
	"selected",
}

ARTIFACT_PAYLOAD_TYPES = {
	"qwen_normalized_family_artifact_contract",
	"qwen_composite_family_artifact",
	"qwen_entity_detail_artifact",
}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_dict_list(values: Any) -> List[Dict[str, Any]]:
	if not isinstance(values, list):
		return []
	return [dict(value) for value in values if isinstance(value, dict)]


def _normalize_token_text(value: Any) -> str:
	return "".join(ch.lower() if ch.isalnum() else " " for ch in _clean_text(value)).strip()


def _message_tokens(value: Any) -> set[str]:
	return {token for token in _normalize_token_text(value).split() if token}


def _message_has_visible_context_reference(message: str) -> bool:
	if nbu_ordinal_reference_index(message) >= 0:
		return True
	return bool(_message_tokens(message).intersection(VISIBLE_CONTEXT_TERMS))


def _message_target_reference(message: str) -> str:
	if nbu_ordinal_reference_index(message) >= 0:
		return "rank_n"
	if _message_tokens(message).intersection({"this", "that", "it", "same", "selected"}):
		return "selected_entity"
	if _message_tokens(message).intersection({"above", "current", "latest", "last", "table", "row"}):
		return "current_artifact"
	return "unclear"


def _safe_json_loads(value: Any) -> Dict[str, Any]:
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
	return list(values or []) if isinstance(values, list) else []


def _payload_identity(payload: Dict[str, Any]) -> str:
	payload = _clean_dict(payload)
	for key in ("artifact_id", "request_id", "trace_id", "source_artifact_id", "source_request_id"):
		value = _clean_text(payload.get(key))
		if value:
			return value
	return _clean_text(payload.get("title") or payload.get("report_name") or payload.get("family_id"))


def _session_previous_artifacts(
	session_doc: Any,
	*,
	current_artifact: Dict[str, Any],
	limit: int = 8,
) -> List[Dict[str, Any]]:
	current_identity = _payload_identity(current_artifact)
	seen = {current_identity} if current_identity else set()
	artifacts: List[Dict[str, Any]] = []
	for message in reversed(_session_messages(session_doc)):
		if _clean_text(getattr(message, "role", "") or (message.get("role") if isinstance(message, dict) else "")).lower() != "tool":
			continue
		content = getattr(message, "content", None)
		if content is None and isinstance(message, dict):
			content = message.get("content")
		payload = _safe_json_loads(content)
		if _clean_text(payload.get("type")).lower() not in ARTIFACT_PAYLOAD_TYPES:
			continue
		identity = _payload_identity(payload)
		if identity and identity in seen:
			continue
		if identity:
			seen.add(identity)
		artifacts.append(payload)
		if len(artifacts) >= limit:
			break
	for payload in session_visible_rendered_artifacts(session_doc, limit=limit):
		identity = _payload_identity(payload)
		if identity and identity in seen:
			continue
		if identity:
			seen.add(identity)
		artifacts.append(payload)
		if len(artifacts) >= limit:
			break
	return artifacts


def _session_recent_selection_focus(session_doc: Any) -> Dict[str, Any]:
	for message in reversed(_session_messages(session_doc)):
		if _clean_text(getattr(message, "role", "") or (message.get("role") if isinstance(message, dict) else "")).lower() != "tool":
			continue
		content = getattr(message, "content", None)
		if content is None and isinstance(message, dict):
			content = message.get("content")
		payload = _safe_json_loads(content)
		if _clean_text(payload.get("type")).lower() != "qwen_nbu_current_artifact_answer_activation_contract":
			continue
		entity = _clean_dict(payload.get("resolved_entity"))
		if not entity:
			continue
		label = _clean_text(entity.get("entity_label") or entity.get("entity_key"))
		if not label:
			continue
		return {
			"focus_kind": "entity",
			"focus_grain": _clean_text(entity.get("entity_type")) or "entity",
			"focus_label": label,
			"focus_key": _clean_text(entity.get("entity_key")) or label,
			"source_request_id": _clean_text(payload.get("request_id")),
		}
	return {}


def _safe_load_registry(loader: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
	try:
		value = loader()
	except Exception:
		return {}
	return dict(value) if isinstance(value, dict) else {}


def _project_specs(values: Any, allowed_keys: set[str], *, limit: int = 80) -> List[Dict[str, Any]]:
	out: List[Dict[str, Any]] = []
	for item in _clean_dict_list(values)[:limit]:
		out.append({key: item.get(key) for key in allowed_keys if item.get(key) is not None})
	return out


def build_nbu_service_metadata_context() -> Dict[str, Any]:
	"""Build the compact registry context used by service-level NBU activation."""

	capability_registry = _safe_load_registry(load_capability_registry)
	report_registry = _safe_load_registry(load_report_registry)
	composite_family_registry = _safe_load_registry(load_composite_family_registry)
	kpi_execution_registry = _safe_load_registry(load_governed_kpi_execution_registry)

	capabilities = _clean_dict_list(capability_registry.get("capabilities"))
	reports = _clean_dict_list(report_registry.get("reports"))
	composite_families = _clean_dict_list(composite_family_registry.get("families"))
	kpi_executions = _clean_dict_list(kpi_execution_registry.get("executions"))

	return {
		"capability_ids": _clean_list([item.get("capability_id") for item in capabilities]),
		"report_names": _clean_list([item.get("report_name") for item in reports]),
		"composite_family_ids": _clean_list([item.get("family_id") for item in composite_families]),
		"governed_kpi_ids": _clean_list([item.get("execution_id") for item in kpi_executions]),
		"business_domains": _clean_list(
			[
				*(tag for item in reports for tag in _clean_list(item.get("semantic_tags"))),
				*(item.get("family_id") for item in composite_families),
			]
		),
		"reports": _project_specs(
			reports,
			{
				"report_name",
				"family",
				"capability_ids",
				"supported_intent_classes",
				"supported_dimensions",
				"supported_metrics",
				"semantic_tags",
				"grounding_mode",
				"activation_state",
			},
		),
		"composite_families": _project_specs(
			composite_families,
			{
				"family_id",
				"label",
				"entity_grain",
				"subject_alias_value",
				"allowed_primary_metrics",
				"allowed_secondary_metrics",
				"metric_semantic_key_map",
				"supported_variation_values",
				"activation_state",
				"blocked_reason",
			},
		),
		"governed_kpi_executions": _project_specs(
			kpi_executions,
			{
				"execution_id",
				"definition_id",
				"label",
				"source_capabilities",
				"source_reports",
				"required_dimensions",
				"value_metric_mapping",
				"activation_state",
				"blocked_reason",
			},
		),
	}


def build_nbu_always_on_shadow_trace(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str = "",
	raw_message: str,
	effective_message: str = "",
	recent_messages: List[Dict[str, str]] | None = None,
	latest_grounded_turn: Dict[str, Any] | None = None,
	latest_assistant_payload: Dict[str, Any] | None = None,
	current_artifact: Dict[str, Any] | None = None,
	recent_focus: Dict[str, Any] | None = None,
	conversation_state: Dict[str, Any] | None = None,
	metadata_context: Dict[str, Any] | None = None,
	runtime_call: Callable[..., Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
	"""Build an always-on NBU shadow trace without changing live behavior.

	FC1 uses this as the shared observation seam. The trace is intentionally
	non-executing: downstream lanes may audit it, but existing governed routing
	continues to own the user-facing answer until later activation slices.
	"""

	message = _clean_text(effective_message) or _clean_text(raw_message)
	started_at = time.perf_counter()
	try:
		trace = interpret_natural_business_understanding_shadow(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=message,
			recent_messages=recent_messages or [],
			latest_grounded_turn=_clean_dict(latest_grounded_turn),
			latest_assistant_payload=_clean_dict(latest_assistant_payload),
			current_artifact=_clean_dict(current_artifact),
			recent_focus=_clean_dict(recent_focus),
			metadata_context=metadata_context if isinstance(metadata_context, dict) else build_nbu_service_metadata_context(),
			conversation_state=_clean_dict(conversation_state),
			runtime_call=runtime_call,
		)
	except Exception as exc:
		trace = {
			"type": "qwen_natural_business_understanding_trace_contract",
			"contract_version": CONTRACT_VERSION,
			"request_id": _clean_text(request_id),
			"session_id": _clean_text(session_id),
			"raw_message": message,
			"candidate_interpretations": [],
			"validation_result": {
				"status": "runtime_unavailable",
				"validation_errors": [f"NBU shadow failed safely: {exc}"],
				"validation_warnings": [],
			},
			"conversation_action_decision": {
				"action": "observe_only",
				"response_mode": "shadow_trace_only",
				"requires_routing_change": False,
				"safe_to_execute": False,
				"reason": "NBU shadow failed safely without changing runtime behavior.",
			},
			"professional_response": {
				"safe_to_show": False,
				"quality_warnings": [],
			},
			"activation_assessment": {
				"activation_state": "blocked_shadow",
				"activation_mode": "none",
				"eligible_for_controlled_activation": False,
				"blockers": ["runtime_interpretation_not_ready"],
			},
			"schema_hardening_assessment": {
				"ok": False,
				"errors": ["runtime_interpretation_not_ready"],
				"warnings": [],
			},
			"shadow_mode": True,
		}
	latency_ms = int(max(0, round((time.perf_counter() - started_at) * 1000)))
	decision = _clean_dict(trace.get("conversation_action_decision"))
	response = _clean_dict(trace.get("professional_response"))
	activation = _clean_dict(trace.get("activation_assessment"))
	schema = _clean_dict(trace.get("schema_hardening_assessment"))
	trace["always_on_shadow_audit"] = {
		"type": "qwen_nbu_always_on_shadow_audit_contract",
		"contract_version": CONTRACT_VERSION,
		"schema_version": NBU_ALWAYS_ON_SHADOW_AUDIT_VERSION,
		"request_id": _clean_text(request_id),
		"shadow_state": "observed",
		"live_behavior_changed": False,
		"runtime_execution_enabled": False,
		"latency_ms": latency_ms,
		"action": _clean_text(decision.get("action")) or "observe_only",
		"response_mode": _clean_text(decision.get("response_mode")) or "shadow_trace_only",
		"professional_response_safe_to_show": bool(response.get("safe_to_show")),
		"schema_hardening_ok": bool(schema.get("ok", False)),
		"activation_state": _clean_text(activation.get("activation_state")),
		"activation_mode": _clean_text(activation.get("activation_mode")),
		"reason": "NBU observed this turn in shadow mode only; existing governed routing remains authoritative.",
	}
	return trace


def _format_professional_response(response_payload: Dict[str, Any]) -> str:
	response = _clean_dict(response_payload)
	title = _clean_text(response.get("title"))
	answer = _clean_text(response.get("answer_text"))
	next_steps = _clean_list(response.get("next_steps"))
	lines: List[str] = []
	if title:
		lines.append(title)
	if answer:
		if lines:
			lines.append("")
		lines.append(answer)
	if next_steps:
		if lines:
			lines.append("")
		lines.append("You can ask me to:")
		lines.extend([f"- {step}" for step in next_steps])
	return "\n".join(lines).strip()


def _selected_candidate(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	trace = _clean_dict(trace_payload)
	selected_id = _clean_text(trace.get("selected_candidate_id"))
	for candidate in _clean_dict_list(trace.get("candidate_interpretations")):
		if selected_id and _clean_text(candidate.get("candidate_id")) == selected_id:
			return candidate
	candidates = _clean_dict_list(trace.get("candidate_interpretations"))
	return candidates[0] if candidates else {}


def _trace_activation_action(trace_payload: Dict[str, Any]) -> str:
	trace = _clean_dict(trace_payload)
	decision = _clean_dict(trace.get("conversation_action_decision"))
	assessment = _clean_dict(trace.get("activation_assessment"))
	response = _clean_dict(trace.get("professional_response"))
	return (
		_clean_text(decision.get("action"))
		or _clean_text(assessment.get("action"))
		or _clean_text(response.get("action"))
	)


def _build_visible_context_activation_trace(
	*,
	base_trace: Dict[str, Any],
	raw_message: str,
	current_artifact: Dict[str, Any],
	previous_artifacts: List[Dict[str, Any]],
	recent_focus: Dict[str, Any],
) -> Dict[str, Any]:
	if not _message_has_visible_context_reference(raw_message):
		return {}
	target_reference = _message_target_reference(raw_message)
	candidate = {
		"candidate_id": "visible-context-reference",
		"intent_scope": "visible_context_followup",
		"business_domain": "erp_reporting",
		"requested_action": "explain",
		"evidence_need": "current_artifact_ok",
		"authority_class": "safe_read",
		"target_reference": target_reference,
		"model_confidence": 0.82,
	}
	resolution = resolve_nbu_context_graph_reference(
		raw_message=raw_message,
		candidate_payload=candidate,
		current_artifact=current_artifact,
		previous_artifacts=previous_artifacts,
		recent_focus=recent_focus,
	).to_payload()
	status = _clean_text(resolution.get("status")).lower()
	if status not in {"resolved", "ambiguous", "out_of_range"}:
		return {}
	if status == "resolved":
		action = "answer_from_current_artifact"
		response_mode = "direct_answer"
		safe_to_execute = True
		evidence_need = "current_artifact_ok"
	else:
		action = "ask_clarification"
		response_mode = "clarification"
		safe_to_execute = False
		evidence_need = "needs_clarification"
		candidate["evidence_need"] = evidence_need
	trace = dict(base_trace or {})
	trace.update(
		{
			"type": _clean_text(trace.get("type")) or "qwen_natural_business_understanding_trace_contract",
			"request_id": _clean_text(trace.get("request_id")),
			"selected_candidate_id": candidate["candidate_id"],
			"candidate_interpretations": [candidate],
			"validation_result": {
				"status": "valid",
				"validation_errors": [],
				"validation_warnings": [],
			},
			"conversation_action_decision": {
				"action": action,
				"response_mode": response_mode,
				"selected_candidate_id": candidate["candidate_id"],
				"requires_routing_change": True,
				"safe_to_execute": safe_to_execute,
				"reason": "Resolved a visible ERP result reference through the shared NBU context graph.",
				"suggested_options": _clean_list(resolution.get("ambiguity_options")),
				"technical_details": {"source": "visible_context_graph_fallback"},
			},
			"evidence_plan": {
				"evidence_need": evidence_need,
				"current_artifact_supported": status == "resolved",
				"visible_artifact_supported": status == "resolved",
				"governed_requery_available": False,
				"required_artifacts": [],
				"missing_fields": [],
				"reason": "The requested row/focus was resolved from visible ERP result context.",
			},
			"authority_plan": {
				"authority_class": "safe_read",
				"authority_allowed": True,
				"policy_artifact_required": "",
				"approval_state": "safe_read_authority",
				"boundary_reason": "",
			},
			"context_resolution": resolution,
			"system_confidence": {
				"final_confidence": 0.82 if status == "resolved" else 0.68,
				"confidence_basis": ["visible_context_graph_resolution"],
			},
			"shadow_mode": True,
		}
	)
	professional_response = render_nbu_professional_response(trace)
	trace["professional_response"] = professional_response
	trace["activation_assessment"] = build_nbu_activation_assessment(trace)
	trace["schema_hardening_assessment"] = validate_nbu_trace_schema_hardening(
		trace,
		response_payload=professional_response,
	)
	return trace


def _prepare_trace_for_visible_context_activation(
	*,
	trace_payload: Dict[str, Any],
	session_doc: Any,
	raw_message: str,
	current_artifact: Dict[str, Any],
	recent_focus: Dict[str, Any],
) -> Dict[str, Any]:
	trace = _clean_dict(trace_payload)
	action = _trace_activation_action(trace)
	has_visible_context_reference = _message_has_visible_context_reference(raw_message)
	if action in LIVE_PRESENTATION_ACTIONS and not has_visible_context_reference:
		return trace
	if action == "answer_from_current_artifact":
		context = _clean_dict(trace.get("context_resolution"))
		evidence = _clean_dict(trace.get("evidence_plan"))
		schema = _clean_dict(trace.get("schema_hardening_assessment"))
		if (
			_clean_text(context.get("status")).lower() == "resolved"
			and bool(evidence.get("current_artifact_supported"))
			and bool(schema.get("ok", True))
		):
			return trace
		if not has_visible_context_reference:
			return trace
	selection_focus = _session_recent_selection_focus(session_doc)
	focus = selection_focus or _clean_dict(recent_focus)
	previous_artifacts = _session_previous_artifacts(
		session_doc,
		current_artifact=_clean_dict(current_artifact),
	)
	fallback_trace = _build_visible_context_activation_trace(
		base_trace=trace,
		raw_message=raw_message,
		current_artifact=_clean_dict(current_artifact),
		previous_artifacts=previous_artifacts,
		recent_focus=focus,
	)
	return fallback_trace or trace


def _humanize(value: Any) -> str:
	text = _clean_text(value).replace("_", " ").replace("-", " ")
	return " ".join(part for part in text.split() if part)


def _format_value(key: str, value: Any) -> str:
	if value in ("", None):
		return ""
	if isinstance(value, float):
		text = f"{value:,.2f}".rstrip("0").rstrip(".")
	elif isinstance(value, int):
		text = f"{value:,}"
	else:
		text = _clean_text(value)
	key_lower = _clean_text(key).lower()
	if isinstance(value, (int, float)) and any(hint in key_lower for hint in MONEY_FIELD_HINTS):
		return f"{text} MMK"
	if (
		not isinstance(value, (int, float))
		and any(hint in key_lower for hint in MONEY_FIELD_HINTS)
		and "mmk" not in text.lower()
		and "%" not in text
		and re.fullmatch(r"-?\d[\d,]*(?:\.\d+)?", text)
	):
		return f"{text} MMK"
	return text


def _row_metric_lines(row: Dict[str, Any], requested_metrics: List[str], *, limit: int = 8) -> List[str]:
	identity_keys = {
		"rank",
		"row_rank",
		"position",
		"idx",
		"index",
		"customer",
		"customer_name",
		"supplier",
		"supplier_name",
		"item",
		"item_name",
		"item_code",
		"entity",
		"entity_name",
		"label",
		"name",
	}
	preferred = [_clean_text(value) for value in requested_metrics if _clean_text(value)]
	keys: List[str] = []
	for key in preferred:
		if key in row:
			keys.append(key)
	for key in row.keys():
		clean_key = _clean_text(key)
		if clean_key and clean_key.lower() not in identity_keys:
			keys.append(clean_key)
	out: List[str] = []
	for key in list(dict.fromkeys(keys))[:limit]:
		value = _format_value(key, row.get(key))
		if value:
			out.append(f"- {_humanize(key).title()}: {value}")
	return out


def build_nbu_current_artifact_answer_response(
	trace_payload: Dict[str, Any],
	*,
	activation_level: str = "current_artifact_answer",
) -> Dict[str, Any]:
	trace = _clean_dict(trace_payload)
	decision = _clean_dict(trace.get("conversation_action_decision"))
	evidence = _clean_dict(trace.get("evidence_plan"))
	authority = _clean_dict(trace.get("authority_plan"))
	context = _clean_dict(trace.get("context_resolution"))
	schema = _clean_dict(trace.get("schema_hardening_assessment"))
	candidate = _selected_candidate(trace)
	action = _clean_text(decision.get("action"))
	response_mode = _clean_text(decision.get("response_mode"))
	action_support = nbu_activation_level_supports_action(action=action, activation_level=activation_level)
	if not bool(action_support.get("supported")):
		return {
			"activated": False,
			"reason": "NBU current-artifact activation is not enabled for this action lane.",
			"blockers": ["nbu_action_lane_not_enabled"],
			"activation_level": _clean_text(action_support.get("activation_level")),
			"required_action_lane": _clean_text(action_support.get("required_action_lane")),
			"allowed_action_lanes": _clean_list(action_support.get("allowed_action_lanes")),
		}
	if action != "answer_from_current_artifact":
		return {"activated": False, "reason": "NBU action is not a current-artifact answer."}
	if response_mode != "direct_answer":
		return {"activated": False, "reason": "NBU current-artifact answer requires direct-answer response mode."}
	if schema and not bool(schema.get("ok", True)):
		return {
			"activated": False,
			"reason": "NBU schema hardening did not pass for current-artifact activation.",
			"blockers": _clean_list(schema.get("errors")) or ["schema_hardening_failed"],
		}
	if not bool(evidence.get("current_artifact_supported")):
		return {"activated": False, "reason": "Current artifact was not proven sufficient."}
	if _clean_text(authority.get("approval_state")) not in {"safe_read_authority", ""}:
		return {"activated": False, "reason": "Authority state does not allow direct fact explanation."}
	if _clean_text(context.get("status")) != "resolved":
		return {"activated": False, "reason": "Current context target was not resolved."}
	entity = _clean_dict(context.get("resolved_entity"))
	row = _clean_dict(entity.get("row"))
	label = _clean_text(entity.get("entity_label")) or _clean_text(entity.get("entity_key"))
	rank = int(context.get("resolved_rank") or 0)
	if not row or not label:
		return {"activated": False, "reason": "Resolved row did not include enough displayable evidence."}

	rank_text = f"Rank {rank}" if rank > 0 else "The selected row"
	lines = [f"{rank_text} is {label} in the current ERP result."]
	metric_lines = _row_metric_lines(row, _clean_list(candidate.get("requested_metrics")))
	if metric_lines:
		lines.append("")
		lines.append("Current row facts:")
		lines.extend(metric_lines)
	lines.append("")
	lines.append("This answer uses only the current ERP result already shown in this conversation.")
	answer_text = "\n".join(lines).strip()
	activation_contract = {
		"type": "qwen_nbu_current_artifact_answer_activation_contract",
		"contract_version": CONTRACT_VERSION,
		"request_id": _clean_text(trace.get("request_id")),
		"activation_state": "activated",
		"activation_mode": "current_artifact_answer",
		"activation_level": _clean_text(action_support.get("activation_level")),
		"required_action_lane": _clean_text(action_support.get("required_action_lane")),
		"allowed_action_lanes": _clean_list(action_support.get("allowed_action_lanes")),
		"live_execution_enabled": True,
		"live_behavior_changed_by_fc5": True,
		"runtime_execution_enabled": False,
		"execution_not_performed": True,
		"action": "answer_from_current_artifact",
		"response_mode": "direct_answer",
		"resolved_rank": rank,
		"resolved_entity": entity,
		"reason": "NBU current-artifact answer was activated after context, evidence, and authority gates passed.",
	}
	return {
		"activated": True,
		"answer_text": answer_text,
		"activation_contract": activation_contract,
		"action": "answer_from_current_artifact",
		"response_mode": "direct_answer",
	}


def build_nbu_presentation_activation_response(
	trace_payload: Dict[str, Any],
	*,
	activation_level: str = "presentation_only",
) -> Dict[str, Any]:
	"""Convert an eligible NBU trace into a live presentation-only response.

	This function does not execute governed queries and does not answer from local
	artifacts. It only activates NBU responses that were already proven safe by
	the shared activation assessment.
	"""

	trace = _clean_dict(trace_payload)
	assessment = _clean_dict(trace.get("activation_assessment"))
	response = _clean_dict(trace.get("professional_response"))
	action = _clean_text(assessment.get("action")) or _clean_text(response.get("action"))
	response_mode = _clean_text(assessment.get("response_mode")) or _clean_text(response.get("response_mode"))
	blockers = _clean_list(assessment.get("blockers"))
	action_support = nbu_activation_level_supports_action(action=action, activation_level=activation_level)
	if not bool(action_support.get("supported")):
		return {
			"activated": False,
			"reason": "NBU presentation activation is not enabled for this action lane.",
			"blockers": blockers or ["nbu_action_lane_not_enabled"],
			"activation_level": _clean_text(action_support.get("activation_level")),
			"required_action_lane": _clean_text(action_support.get("required_action_lane")),
			"allowed_action_lanes": _clean_list(action_support.get("allowed_action_lanes")),
		}
	if action not in LIVE_PRESENTATION_ACTIONS:
		return {
			"activated": False,
			"reason": "NBU presentation activation for this action is deferred to a later live slice.",
			"blockers": blockers or [f"live_activation_deferred:{action or 'unknown'}"],
		}
	if not bool(assessment.get("eligible_for_controlled_activation")):
		return {
			"activated": False,
			"reason": "NBU assessment is not eligible for controlled presentation activation.",
			"blockers": blockers,
		}
	if _clean_text(assessment.get("activation_mode")) != "presentation_only":
		return {
			"activated": False,
			"reason": "NBU assessment is not presentation-only.",
			"blockers": blockers or ["activation_mode_not_presentation_only"],
		}
	if not bool(response.get("safe_to_show")):
		return {
			"activated": False,
			"reason": "NBU professional response is not safe to show.",
			"blockers": blockers or ["professional_response_not_safe_to_show"],
		}
	if _clean_list(response.get("quality_warnings")):
		return {
			"activated": False,
			"reason": "NBU professional response has quality warnings.",
			"blockers": blockers or ["professional_response_quality_warnings"],
		}
	answer_text = _format_professional_response(response)
	if not answer_text:
		return {
			"activated": False,
			"reason": "NBU professional response did not produce user-facing text.",
			"blockers": blockers or ["empty_professional_response"],
		}
	activation_contract = {
		"type": "qwen_nbu_presentation_activation_contract",
		"contract_version": CONTRACT_VERSION,
		"request_id": _clean_text(trace.get("request_id")),
		"activation_state": "activated",
		"activation_mode": "presentation_only",
		"activation_level": _clean_text(action_support.get("activation_level")),
		"required_action_lane": _clean_text(action_support.get("required_action_lane")),
		"allowed_action_lanes": _clean_list(action_support.get("allowed_action_lanes")),
		"live_execution_enabled": True,
		"live_behavior_changed_by_fc4": True,
		"runtime_execution_enabled": False,
		"execution_not_performed": True,
		"action": action,
		"response_mode": response_mode,
		"reason": "NBU presentation-only response was activated after shared assessment gates passed.",
	}
	return {
		"activated": True,
		"answer_text": answer_text,
		"activation_contract": activation_contract,
		"action": action,
		"response_mode": response_mode,
	}


def try_activate_nbu_presentation_response(
	*,
	session_doc: Any,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str = "",
	raw_message: str,
	effective_message: str = "",
	recent_messages: List[Dict[str, str]] | None = None,
	latest_grounded_turn: Dict[str, Any] | None = None,
	latest_assistant_payload: Dict[str, Any] | None = None,
	current_artifact: Dict[str, Any] | None = None,
	recent_focus: Dict[str, Any] | None = None,
	conversation_state: Dict[str, Any] | None = None,
	metadata_context: Dict[str, Any] | None = None,
	interaction_contract: Any | None = None,
	followup_resolution: Any | None = None,
	user_message_already_appended: bool = False,
	append_message: AppendMessage | None = None,
	append_tool_payload: AppendToolPayload | None = None,
	assistant_text_payload: AssistantTextPayload | None = None,
	save_session: SaveSession | None = None,
	runtime_call: Callable[..., Dict[str, Any]] | None = None,
	nbu_trace_payload: Dict[str, Any] | None = None,
	nbu_trace_already_appended: bool = False,
	activation_level: str = "current_artifact_answer",
	require_visible_context_reference: bool = False,
) -> Tuple[bool, Dict[str, Any] | None]:
	"""Try the controlled NBU safe-response lane.

	The lane is intentionally fail-open to the existing assistant flow: runtime
	errors, unsupported actions, and governed query plans all return ``False`` so
	mature lanes remain authoritative. FC4 owns presentation-only responses; FC5
	adds direct answers from already-visible current-artifact facts.
	"""

	if append_message is None or append_tool_payload is None or assistant_text_payload is None or save_session is None:
		return False, None
	trace = _clean_dict(nbu_trace_payload)
	if not trace:
		trace = build_nbu_always_on_shadow_trace(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			raw_message=raw_message,
			effective_message=effective_message,
			recent_messages=recent_messages or [],
			latest_grounded_turn=_clean_dict(latest_grounded_turn),
			latest_assistant_payload=_clean_dict(latest_assistant_payload),
			current_artifact=_clean_dict(current_artifact),
			recent_focus=_clean_dict(recent_focus),
			metadata_context=metadata_context if isinstance(metadata_context, dict) else build_nbu_service_metadata_context(),
			conversation_state=_clean_dict(conversation_state),
			runtime_call=runtime_call,
		)
	visible_context_message = _clean_text(raw_message) or _clean_text(effective_message)
	trace = _prepare_trace_for_visible_context_activation(
		trace_payload=trace,
		session_doc=session_doc,
		raw_message=visible_context_message,
		current_artifact=_clean_dict(current_artifact),
		recent_focus=_clean_dict(recent_focus),
	)
	if require_visible_context_reference and not _message_has_visible_context_reference(
		visible_context_message
	):
		return False, None
	if require_visible_context_reference and _clean_text(_selected_candidate(trace).get("candidate_id")) != "visible-context-reference":
		return False, None
	activation = build_nbu_current_artifact_answer_response(trace, activation_level=activation_level)
	if not bool(activation.get("activated")):
		activation = build_nbu_presentation_activation_response(trace, activation_level=activation_level)
	if not bool(activation.get("activated")):
		return False, None

	answer_text = _clean_text(activation.get("answer_text"))
	activation_contract = _clean_dict(activation.get("activation_contract"))
	if not answer_text or not activation_contract:
		return False, None

	if not user_message_already_appended:
		append_message(session_doc, "user", raw_message)
	if not nbu_trace_already_appended:
		append_tool_payload(session_doc, trace)
	append_tool_payload(session_doc, activation_contract)
	execution_path_payload = {
		"type": "qwen_execution_path",
		"contract_version": CONTRACT_VERSION,
		"request_id": request_id,
		"path": _clean_text(activation_contract.get("activation_mode")) or "nbu_safe_response_activation",
		"reason": _clean_text(activation_contract.get("reason")),
		"requires_runtime": False,
		"grounded_required": False,
	}
	append_tool_payload(session_doc, execution_path_payload)
	append_message(session_doc, "assistant", assistant_text_payload(answer_text))
	if interaction_contract is not None:
		from .contracts import (
			ExecutionPath,
			build_audit_envelope,
			build_followup_resolution_contract,
		)

		activation_mode = _clean_text(activation_contract.get("activation_mode")) or "nbu_safe_response_activation"
		execution_path = ExecutionPath(
			request_id=request_id,
			path=activation_mode,
			reason=_clean_text(activation_contract.get("reason")),
			requires_runtime=False,
			grounded_required=False,
		)
		resolution = followup_resolution or build_followup_resolution_contract(
			request_id=request_id,
			mode="front_door",
			requested_modes=[activation_mode],
			depends_on_grounded_turn=False,
			self_contained=True,
			latest_grounded_turn_available=bool(_clean_dict(latest_grounded_turn).get("grounded")),
			reason="NBU safe-response activation handled the request without executing a governed query.",
		)
		append_tool_payload(
			session_doc,
			build_audit_envelope(
				interaction_contract=interaction_contract,
				followup_resolution=resolution,
				execution_path=execution_path,
				runtime_trace_payload={
					"agent_meta": {
						"engine": "natural_business_understanding",
						"action": _clean_text(activation.get("action")),
						"response_mode": _clean_text(activation.get("response_mode")),
					}
				},
				grounded_turn_context=_clean_dict(latest_grounded_turn),
				answer_text=answer_text,
			).to_payload(),
		)
	save_session(session_doc, ignore_permissions=False)
	return True, {
		"ok": True,
		"request_id": request_id,
		"mode": _clean_text(activation_contract.get("activation_mode")) or "nbu_safe_response_activation",
		"agent_meta": {
			"engine": "natural_business_understanding",
			"action": _clean_text(activation.get("action")),
			"response_mode": _clean_text(activation.get("response_mode")),
		},
	}
