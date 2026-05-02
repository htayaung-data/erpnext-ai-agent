from __future__ import annotations

import time
import json
import re
from typing import Any, Callable, Dict, List, Tuple

from .governed_scope_registry import entity_detail_runtime_policy
from .natural_business_understanding_arbitration import nbu_activation_level_supports_action
from .natural_business_understanding_context_graph import resolve_nbu_context_graph_reference
from .natural_business_understanding_context_resolution import nbu_artifact_rows
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .natural_business_understanding_request_classification import (
	visible_context_reference_requested,
	visible_context_target_reference,
)
from .natural_business_understanding_visible_artifacts import session_visible_rendered_artifacts
from .semantic_aliases import detect_canonical_keys


AppendMessage = Callable[[Any, str, str], None]
AppendToolPayload = Callable[[Any, Dict[str, Any]], None]
AssistantTextPayload = Callable[[str], str]
SaveSession = Callable[..., None]
ClearPendingClarification = Callable[[Any], None]


SUPPORTED_REQUERY_ACTIONS = {"execute_governed_requery"}
SUPPORTED_PLANNER_MODES = {"entity_detail_requery"}
DETAIL_REQUEST_TERMS = {
	"detail",
	"details",
	"profile",
	"information",
	"info",
	"about",
	"more",
	"full",
}
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
IDENTITY_DIMENSIONS = {
	"customer",
	"customer_name",
	"supplier",
	"supplier_name",
	"item",
	"item_name",
	"item_code",
	"warehouse",
	"warehouse_name",
	"party",
	"party_name",
	"account",
	"account_name",
}
ARTIFACT_PAYLOAD_TYPES = {
	"qwen_normalized_family_artifact_contract",
	"qwen_composite_family_artifact",
	"qwen_entity_detail_artifact",
	"qwen_visible_rendered_artifact",
}
LOW_PRIORITY_ROW_SOURCES = {"sections.parties", "sections.party_rows"}


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _normalize_key(value: Any) -> str:
	text = _clean_text(value).lower().replace("-", "_").replace(" ", "_")
	text = re.sub(r"[^a-z0-9_]+", "_", text)
	return re.sub(r"_+", "_", text).strip("_")


def _tokens(value: Any) -> set[str]:
	text = re.sub(r"[^a-z0-9]+", " ", _clean_text(value).lower())
	return {token for token in text.split() if token}


def _markdown_table(columns: List[str], rows: List[List[str]]) -> str:
	if not columns or not rows:
		return ""
	lines = [
		"| " + " | ".join(columns) + " |",
		"| " + " | ".join("---" for _ in columns) + " |",
	]
	for row in rows:
		lines.append("| " + " | ".join(_clean_text(cell) for cell in row) + " |")
	return "\n".join(lines).strip()


def _render_response_payload_markdown(rendered_payload: Dict[str, Any]) -> str:
	payload = _clean_dict(rendered_payload)
	blocks = payload.get("blocks") if isinstance(payload.get("blocks"), list) else []
	if not blocks:
		return ""
	lines: List[str] = []
	title = _clean_text(payload.get("title"))
	if title:
		lines.append(title)
	for block in blocks:
		if not isinstance(block, dict):
			continue
		block_title = _clean_text(block.get("title"))
		block_type = _clean_text(block.get("block_type"))
		if block_title:
			lines.append(block_title)
		if block_type in {"summary_table", "data_table"}:
			columns = [_clean_text(col) for col in (block.get("columns") or []) if _clean_text(col)]
			rows = [
				[_clean_text(cell) for cell in row]
				for row in (block.get("rows") or [])
				if isinstance(row, list)
			]
			table = _markdown_table(columns, rows)
			if table:
				lines.append(table)
		elif block_type == "bullet_list":
			for item in (block.get("items") or []):
				value = _clean_text(item)
				if value:
					lines.append(f"- {value}")
	return "\n\n".join(part for part in lines if part).strip()


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
	return _clean_text(getattr(message, "role", "") or (message.get("role") if isinstance(message, dict) else "")).lower()


def _message_content(message: Any) -> Any:
	content = getattr(message, "content", None)
	if content is None and isinstance(message, dict):
		content = message.get("content")
	return content


def _latest_selected_entity(session_doc: Any) -> Dict[str, Any]:
	for message in reversed(_session_messages(session_doc)):
		if _message_role(message) != "tool":
			continue
		payload = _safe_json_loads(_message_content(message))
		if _clean_text(payload.get("type")).lower() not in {
			"qwen_nbu_current_artifact_answer_activation_contract",
			"qwen_visible_context_followup_activation_contract",
		}:
			continue
		entity = _clean_dict(payload.get("resolved_entity"))
		label = _clean_text(entity.get("entity_label") or entity.get("entity_key"))
		if label:
			return entity
	return {}


def _message_has_visible_context_reference(message: str) -> bool:
	return visible_context_reference_requested(message)


def _message_target_reference(message: str) -> str:
	return visible_context_target_reference(message)


def _artifact_identity(payload: Dict[str, Any]) -> str:
	for key in ("artifact_id", "request_id", "trace_id", "source_artifact_id", "source_request_id"):
		value = _clean_text(_clean_dict(payload).get(key))
		if value:
			return value
	return _clean_text(_clean_dict(payload).get("title") or _clean_dict(payload).get("report_name") or _clean_dict(payload).get("family_id"))


def _has_rows(payload: Dict[str, Any]) -> bool:
	rows, _source = nbu_artifact_rows(_clean_dict(payload))
	return bool(rows)


def _row_source(payload: Dict[str, Any]) -> str:
	_rows, source = nbu_artifact_rows(_clean_dict(payload))
	return _clean_text(source)


def _session_tool_artifact_groups(session_doc: Any, *, limit: int = 8) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
	primary_typed_artifacts: List[Dict[str, Any]] = []
	secondary_typed_artifacts: List[Dict[str, Any]] = []
	fallback_artifacts: List[Dict[str, Any]] = []
	scanned = 0
	for message in reversed(_session_messages(session_doc)):
		if _message_role(message) != "tool":
			continue
		scanned += 1
		payload = _safe_json_loads(_message_content(message))
		payload_type = _clean_text(payload.get("type")).lower()
		if not _has_rows(payload):
			continue
		if payload_type in ARTIFACT_PAYLOAD_TYPES:
			if _row_source(payload) in LOW_PRIORITY_ROW_SOURCES:
				secondary_typed_artifacts.append(payload)
			else:
				primary_typed_artifacts.append(payload)
		else:
			fallback_artifacts.append(payload)
		if len(primary_typed_artifacts) >= limit:
			break
		if scanned >= limit * 4 and (primary_typed_artifacts or secondary_typed_artifacts):
			break
	return (
		primary_typed_artifacts[:limit],
		secondary_typed_artifacts[:limit],
		fallback_artifacts[:limit],
	)


def _context_artifacts(session_doc: Any, current_artifact: Dict[str, Any]) -> List[Dict[str, Any]]:
	artifacts: List[Dict[str, Any]] = []
	seen: set[str] = set()

	def append(payload: Dict[str, Any]) -> None:
		clean_payload = _clean_dict(payload)
		if not clean_payload:
			return
		identity = _artifact_identity(clean_payload)
		if identity and identity in seen:
			return
		if identity:
			seen.add(identity)
		artifacts.append(clean_payload)

	primary_tool_artifacts, secondary_tool_artifacts, fallback_tool_artifacts = _session_tool_artifact_groups(session_doc, limit=8)
	for payload in primary_tool_artifacts:
		append(payload)
	for payload in session_visible_rendered_artifacts(session_doc, limit=6):
		append(payload)
	for payload in secondary_tool_artifacts:
		append(payload)
	for payload in fallback_tool_artifacts:
		append(payload)
	append(current_artifact)
	return artifacts


def _requested_entity_detail_fields(raw_message: str) -> Tuple[List[str], List[str]]:
	try:
		metrics = detect_canonical_keys(raw_message, dimension_or_metric="metric")
	except Exception:
		metrics = []
	try:
		dimensions = detect_canonical_keys(raw_message, dimension_or_metric="dimension")
	except Exception:
		dimensions = []
	return _clean_list(metrics), _clean_list(dimensions)


def _row_has_all_requested_fields(row: Dict[str, Any], metrics: List[str], dimensions: List[str]) -> bool:
	requested = [_normalize_key(value) for value in [*metrics, *dimensions] if _normalize_key(value)]
	if not requested:
		return False
	row_keys = {_normalize_key(key) for key in _clean_dict(row).keys()}
	return bool(row_keys) and all(value in row_keys for value in requested)


def _message_requests_entity_detail(raw_message: str) -> bool:
	tokens = _tokens(raw_message)
	if "more" in tokens and (
		tokens.intersection({"tell", "information", "info", "details", "detail"})
		or tokens.intersection({"rank", "row", "that", "this", "supplier", "customer", "item", "product", "invoice"})
	):
		return True
	if tokens.intersection({"details", "detail", "profile"}) and tokens.intersection({"about", "for"}):
		return True
	return bool(tokens.intersection({"profile", "details", "detail"}) and tokens.intersection({"rank", "row", "that", "this", "supplier", "customer", "item", "product", "invoice"}))


def _assessment_requests_specific_fields(assessment: Dict[str, Any]) -> bool:
	metrics = _clean_list(_clean_dict(assessment).get("requested_metrics"))
	dimensions = [
		value
		for value in _clean_list(_clean_dict(assessment).get("requested_dimensions"))
		if _normalize_key(value) not in IDENTITY_DIMENSIONS
	]
	missing_fields = [
		value
		for value in _clean_list(_clean_dict(assessment).get("missing_fields"))
		if _normalize_key(value) not in IDENTITY_DIMENSIONS
	]
	return bool(metrics or dimensions or missing_fields)


def _prefer_rich_entity_detail_answer(*, raw_message: str, assessment: Dict[str, Any]) -> bool:
	"""Use full governed detail for broad "more/details/profile" requests.

	Direct evidence helpers are intentionally concise. They are excellent for
	field asks like credit limit or outstanding amount, but too narrow for broad
	"tell me more" requests across customers, suppliers, items, and documents.
	"""

	return _message_requests_entity_detail(raw_message) and not _assessment_requests_specific_fields(assessment)


def _rich_entity_detail_answer_text(outcome: Dict[str, Any]) -> str:
	return _render_response_payload_markdown(_clean_dict(outcome).get("rendered_response_payload")) or _clean_text(_clean_dict(outcome).get("answer_text"))


def _requested_fields_need_entity_detail(
	*,
	raw_message: str,
	entity: Dict[str, Any],
) -> Tuple[bool, List[str], List[str]]:
	metrics, dimensions = _requested_entity_detail_fields(raw_message)
	if _message_requests_entity_detail(raw_message):
		return True, metrics, dimensions
	meaningful_dimensions = [
		value
		for value in dimensions
		if _normalize_key(value) not in IDENTITY_DIMENSIONS
	]
	if not metrics and not meaningful_dimensions:
		return False, metrics, dimensions
	row = _clean_dict(entity.get("row"))
	if _row_has_all_requested_fields(row, metrics, dimensions):
		return False, metrics, dimensions
	return True, metrics, dimensions


def _resolve_visible_entity_for_registry_requery(
	*,
	session_doc: Any,
	raw_message: str,
	current_artifact: Dict[str, Any],
) -> Dict[str, Any]:
	if not _message_has_visible_context_reference(raw_message):
		return {}
	target_reference = _message_target_reference(raw_message)
	selected = _latest_selected_entity(session_doc)
	if target_reference == "selected_entity" and selected:
		return selected
	artifacts = _context_artifacts(session_doc, current_artifact)
	if not artifacts:
		return {}
	resolution = resolve_nbu_context_graph_reference(
		raw_message=raw_message,
		candidate_payload={
			"candidate_id": "registry-visible-entity-requery",
			"target_reference": target_reference,
			"intent_scope": "visible_context_followup",
			"authority_class": "safe_read",
		},
		current_artifact=artifacts[0],
		previous_artifacts=artifacts[1:],
		recent_focus=(
			{
				"focus_kind": "entity",
				"focus_grain": _clean_text(selected.get("entity_type")),
				"focus_label": _clean_text(selected.get("entity_label") or selected.get("entity_key")),
				"focus_key": _clean_text(selected.get("entity_key") or selected.get("entity_label")),
			}
			if selected
			else {}
		),
	).to_payload()
	if _clean_text(resolution.get("status")).lower() != "resolved":
		return {}
	return _clean_dict(resolution.get("resolved_entity"))


def _selected_candidate(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	trace = _clean_dict(trace_payload)
	selected_id = _clean_text(trace.get("selected_candidate_id"))
	candidates = [
		dict(candidate)
		for candidate in trace.get("candidate_interpretations", [])
		if isinstance(candidate, dict)
	]
	for candidate in candidates:
		if selected_id and _clean_text(candidate.get("candidate_id")) == selected_id:
			return candidate
	return candidates[0] if candidates else {}


def _target_entity_from_plan(trace_payload: Dict[str, Any]) -> Dict[str, Any]:
	trace = _clean_dict(trace_payload)
	plan = _clean_dict(trace.get("governed_requery_plan"))
	context = _clean_dict(trace.get("context_resolution"))
	candidate = _selected_candidate(trace)
	for source in (
		plan.get("target_entity"),
		context.get("resolved_entity"),
		candidate.get("target_entity"),
	):
		entity = _clean_dict(source)
		label = _clean_text(entity.get("entity_label") or entity.get("entity_key"))
		if label:
			return entity
	return {}


def _entity_detail_can_execute(entity: Dict[str, Any]) -> bool:
	entity_type = _clean_text(entity.get("entity_type")).lower()
	if not entity_type:
		return False
	try:
		policy = entity_detail_runtime_policy(entity_type)
	except Exception:
		return False
	return bool(_clean_dict(policy).get("can_execute"))


def _entity_reference(entity: Dict[str, Any]) -> Dict[str, Any]:
	entity_type = _clean_text(entity.get("entity_type")).lower()
	entity_label = _clean_text(entity.get("entity_label") or entity.get("entity_key"))
	entity_key = _clean_text(entity.get("entity_key")) or entity_label
	return {
		key: value
		for key, value in {
			"entity_type": entity_type,
			"entity_key": entity_key,
			"entity_label": entity_label or entity_key,
		}.items()
		if value
	}


def build_nbu_governed_requery_activation(
	trace_payload: Dict[str, Any],
	*,
	activation_level: str = "governed_requery",
) -> Dict[str, Any]:
	"""Validate whether an NBU shadow requery plan may become live.

	FC6 only activates proven entity-detail requery plans. Other governed requery
	planner modes remain shadow-only until their execution seams are separately
	approved.
	"""

	trace = _clean_dict(trace_payload)
	decision = _clean_dict(trace.get("conversation_action_decision"))
	plan = _clean_dict(trace.get("governed_requery_plan"))
	candidate = _selected_candidate(trace)
	action = _clean_text(decision.get("action"))
	action_support = nbu_activation_level_supports_action(
		action=action,
		activation_level=activation_level,
	)
	blockers: List[str] = []
	if action not in SUPPORTED_REQUERY_ACTIONS:
		blockers.append("action_not_governed_requery")
	if not bool(action_support.get("supported")):
		blockers.append("activation_level_does_not_allow_requery")
	if not bool(decision.get("safe_to_execute")):
		blockers.append("conversation_decision_not_safe_to_execute")
	if _clean_text(plan.get("status")) != "ready_shadow":
		blockers.append("governed_requery_plan_not_ready")
	if _clean_text(plan.get("planner_mode")) not in SUPPORTED_PLANNER_MODES:
		blockers.append("planner_mode_not_live_enabled")
	if _clean_list(plan.get("required_context")):
		blockers.append("required_context_missing")
	entity = _target_entity_from_plan(trace)
	entity_reference = _entity_reference(entity)
	if not entity_reference:
		blockers.append("target_entity_not_resolved")
	elif not _entity_detail_can_execute(entity_reference):
		blockers.append("entity_detail_execution_not_enabled")

	return {
		"type": "qwen_nbu_governed_requery_activation_assessment",
		"contract_version": CONTRACT_VERSION,
		"activation_state": "ready" if not blockers else "blocked",
		"activation_mode": "governed_requery_entity_detail" if not blockers else "none",
		"activation_level": _clean_text(action_support.get("activation_level")) or activation_level,
		"required_action_lane": _clean_text(action_support.get("required_action_lane")),
		"allowed_action_lanes": _clean_list(action_support.get("allowed_action_lanes")),
		"action": action,
		"planner_mode": _clean_text(plan.get("planner_mode")),
		"target_entity": entity_reference,
		"requested_metrics": _clean_list(plan.get("requested_metrics") or candidate.get("requested_metrics")),
		"requested_dimensions": _clean_list(plan.get("requested_dimensions") or candidate.get("requested_dimensions")),
		"missing_fields": _clean_list(plan.get("missing_fields")),
		"blockers": list(dict.fromkeys(blockers)),
		"reason": (
			"NBU governed requery activation is ready for entity-detail execution."
			if not blockers
			else "NBU governed requery activation is not safe to execute live."
		),
	}


def build_nbu_registry_visible_entity_requery_activation(
	*,
	session_doc: Any,
	raw_message: str,
	current_artifact: Dict[str, Any],
	activation_level: str = "governed_requery",
) -> Dict[str, Any]:
	entity = _resolve_visible_entity_for_registry_requery(
		session_doc=session_doc,
		raw_message=raw_message,
		current_artifact=current_artifact,
	)
	needs_entity_detail, metrics, dimensions = _requested_fields_need_entity_detail(
		raw_message=raw_message,
		entity=entity,
	)
	action_support = nbu_activation_level_supports_action(
		action="execute_governed_requery",
		activation_level=activation_level,
	)
	blockers: List[str] = []
	if not bool(action_support.get("supported")):
		blockers.append("activation_level_does_not_allow_requery")
	if not entity:
		blockers.append("target_entity_not_resolved")
	if entity and not _entity_detail_can_execute(_entity_reference(entity)):
		blockers.append("entity_detail_execution_not_enabled")
	if not needs_entity_detail:
		blockers.append("requested_field_not_proven_entity_detail_requery")
	entity_reference = _entity_reference(entity)
	return {
		"type": "qwen_nbu_governed_requery_activation_assessment",
		"contract_version": CONTRACT_VERSION,
		"activation_state": "ready" if not blockers else "blocked",
		"activation_mode": "governed_requery_entity_detail" if not blockers else "none",
		"activation_level": _clean_text(action_support.get("activation_level")) or activation_level,
		"required_action_lane": _clean_text(action_support.get("required_action_lane")),
		"allowed_action_lanes": _clean_list(action_support.get("allowed_action_lanes")),
		"action": "execute_governed_requery",
		"planner_mode": "entity_detail_requery",
		"target_entity": entity_reference,
		"requested_metrics": metrics,
		"requested_dimensions": dimensions,
		"missing_fields": [*metrics, *dimensions],
		"blockers": list(dict.fromkeys(blockers)),
		"reason": (
			"Registry-backed NBU requery activation is ready for entity-detail execution."
			if not blockers
			else "Registry-backed NBU requery activation is not safe to execute live."
		),
		"activation_source": "registry_visible_entity_requery",
	}


def _activation_contract(
	*,
	request_id: str,
	assessment: Dict[str, Any],
) -> Dict[str, Any]:
	return {
		"type": "qwen_nbu_governed_requery_activation_contract",
		"contract_version": CONTRACT_VERSION,
		"request_id": _clean_text(request_id),
		"activation_state": "activated",
		"activation_mode": "governed_requery_entity_detail",
		"activation_level": _clean_text(assessment.get("activation_level")) or "governed_requery",
		"required_action_lane": _clean_text(assessment.get("required_action_lane")),
		"allowed_action_lanes": _clean_list(assessment.get("allowed_action_lanes")),
		"live_execution_enabled": True,
		"live_behavior_changed_by_fc6": True,
		"runtime_execution_enabled": False,
		"execution_not_performed": False,
		"action": "execute_governed_requery",
		"planner_mode": _clean_text(assessment.get("planner_mode")),
		"target_entity": _clean_dict(assessment.get("target_entity")),
		"requested_metrics": _clean_list(assessment.get("requested_metrics")),
		"requested_dimensions": _clean_list(assessment.get("requested_dimensions")),
		"missing_fields": _clean_list(assessment.get("missing_fields")),
		"reason": "NBU requery activation executed an approved entity-detail lookup because the visible artifact lacked the requested evidence.",
	}


def _append_outcome_payloads(
	*,
	append_tool_payload: AppendToolPayload,
	session_doc: Any,
	outcome: Dict[str, Any],
	direct_response: Dict[str, Any],
) -> None:
	for key in (
		"artifact_payload",
		"rendered_response_payload",
		"narrative_contract_payload",
		"grounded_turn_payload",
	):
		payload = outcome.get(key)
		if isinstance(payload, dict) and payload:
			append_tool_payload(session_doc, payload)
	for key in (
		"rendered_response_payload",
		"narrative_payload",
		"narrative_contract_payload",
		"clarification_signal_payload",
		"evidence_request_contract_payload",
	):
		payload = direct_response.get(key)
		if isinstance(payload, dict) and payload:
			append_tool_payload(session_doc, payload)


def try_activate_nbu_governed_requery_response(
	*,
	session_doc: Any,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str = "",
	raw_message: str,
	nbu_trace_payload: Dict[str, Any],
	current_artifact: Dict[str, Any] | None = None,
	latest_grounded_turn: Dict[str, Any] | None = None,
	interaction_contract: Any = None,
	response_policy_contract: Any = None,
	user_message_already_appended: bool = False,
	append_message: AppendMessage,
	append_tool_payload: AppendToolPayload,
	assistant_text_payload: AssistantTextPayload,
	save_session: SaveSession,
	execute_entity_drilldown: Callable[..., Dict[str, Any]],
	direct_evidence_response: Callable[..., Dict[str, Any]] | None = None,
	clear_pending_clarification_signal: ClearPendingClarification | None = None,
	additional_tool_payloads: List[Dict[str, Any]] | None = None,
	activation_level: str = "governed_requery",
) -> Tuple[bool, Dict[str, Any] | None]:
	assessment = build_nbu_governed_requery_activation(
		nbu_trace_payload,
		activation_level=activation_level,
	)
	if _clean_text(assessment.get("activation_state")) != "ready":
		assessment = build_nbu_registry_visible_entity_requery_activation(
			session_doc=session_doc,
			raw_message=raw_message,
			current_artifact=_clean_dict(current_artifact),
			activation_level=activation_level,
		)
	if _clean_text(assessment.get("activation_state")) != "ready":
		return False, None

	entity_reference = _clean_dict(assessment.get("target_entity"))
	if not entity_reference:
		return False, None

	started_at = time.perf_counter()
	try:
		outcome = execute_entity_drilldown(
			request_id=request_id,
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			message=raw_message,
			entity_reference=entity_reference,
			response_policy=(
				response_policy_contract.to_runtime_payload()
				if response_policy_contract is not None
				else {}
			),
			grounded_turn=_clean_dict(latest_grounded_turn),
		)
	except Exception:
		return False, None

	if not bool(_clean_dict(outcome).get("ok")):
		return False, None

	artifact_payload = _clean_dict(outcome.get("artifact_payload"))
	grounded_turn = _clean_dict(outcome.get("grounded_turn_payload")) or _clean_dict(latest_grounded_turn)
	direct_response: Dict[str, Any] = {}
	prefer_rich_detail_answer = _prefer_rich_entity_detail_answer(
		raw_message=raw_message,
		assessment=assessment,
	)
	if (
		not prefer_rich_detail_answer
		and direct_evidence_response is not None
		and artifact_payload
		and interaction_contract is not None
		and response_policy_contract is not None
	):
		try:
			direct_response = direct_evidence_response(
				request_id=request_id,
				session_id=session_id,
				interaction_contract=interaction_contract,
				response_policy_contract=response_policy_contract,
				raw_message=raw_message,
				artifact_payload=artifact_payload,
				grounded_turn=grounded_turn,
				fallback_answer_text="",
			)
		except Exception:
			direct_response = {}
	answer_text = (
		_rich_entity_detail_answer_text(outcome)
		if prefer_rich_detail_answer
		else _clean_text(direct_response.get("answer_text")) or _clean_text(outcome.get("answer_text"))
	)
	if not answer_text:
		return False, None

	if not user_message_already_appended:
		append_message(session_doc, "user", raw_message)
	for payload in additional_tool_payloads or []:
		if isinstance(payload, dict) and payload:
			append_tool_payload(session_doc, payload)
	append_tool_payload(session_doc, assessment)
	activation_contract = _activation_contract(request_id=request_id, assessment=assessment)
	append_tool_payload(session_doc, activation_contract)
	_append_outcome_payloads(
		append_tool_payload=append_tool_payload,
		session_doc=session_doc,
		outcome=outcome,
		direct_response=direct_response,
	)
	execution_path = None
	execution_path_payload = {
		"type": "qwen_execution_path",
		"contract_version": CONTRACT_VERSION,
		"request_id": _clean_text(request_id),
		"path": "nbu_governed_requery_entity_detail",
		"reason": _clean_text(activation_contract.get("reason")),
		"requires_runtime": False,
		"grounded_required": True,
		"answer_selection_mode": "rich_entity_detail" if prefer_rich_detail_answer else "direct_evidence_first",
	}
	try:
		from .contracts import ExecutionPath, build_audit_envelope, build_followup_resolution_contract

		execution_path = ExecutionPath(
			request_id=request_id,
			path="nbu_governed_requery_entity_detail",
			reason=_clean_text(activation_contract.get("reason")),
			requires_runtime=False,
			grounded_required=True,
		)
		execution_path_payload = execution_path.to_payload()
	except Exception:
		build_audit_envelope = None
		build_followup_resolution_contract = None
	append_tool_payload(session_doc, execution_path_payload)
	append_message(session_doc, "assistant", assistant_text_payload(answer_text))
	if clear_pending_clarification_signal is not None:
		clear_pending_clarification_signal(session_doc)
	if interaction_contract is not None and execution_path is not None and build_audit_envelope is not None and build_followup_resolution_contract is not None:
		followup_resolution = build_followup_resolution_contract(
			request_id=request_id,
			mode="nbu_governed_requery_entity_detail",
			requested_modes=["nbu_governed_requery_entity_detail"],
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=bool(_clean_dict(latest_grounded_turn).get("grounded")),
			reason="NBU activated a governed requery from visible context to entity detail.",
		)
		append_tool_payload(
			session_doc,
			build_audit_envelope(
				interaction_contract=interaction_contract,
				followup_resolution=followup_resolution,
				execution_path=execution_path,
				runtime_trace_payload={
					"agent_meta": {
						"engine": "nbu_governed_requery",
						"mode": "entity_detail",
						"latency_ms": int(max(0, round((time.perf_counter() - started_at) * 1000))),
					}
				},
				grounded_turn_context=grounded_turn,
				answer_text=answer_text,
			).to_payload(),
		)
	save_session(session_doc, ignore_permissions=False)
	return True, {
		"ok": True,
		"request_id": request_id,
		"mode": "nbu_governed_requery_entity_detail",
		"agent_meta": {
			"engine": "nbu_governed_requery",
			"planner_mode": _clean_text(assessment.get("planner_mode")),
			"target_entity_type": _clean_text(entity_reference.get("entity_type")),
		},
	}
