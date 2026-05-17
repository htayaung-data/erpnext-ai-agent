from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List


CONTRACT_VERSION = "1.0"
LEDGER_TYPE = "qwen_semantic_ownership_ledger_contract"


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_list(value: Any) -> List[Any]:
	return list(value) if isinstance(value, list) else []


def _clean_dict_list(value: Any) -> List[Dict[str, Any]]:
	return [dict(item) for item in _clean_list(value) if isinstance(item, dict)]


def _first_text(*values: Any) -> str:
	for value in values:
		text = _clean_text(value)
		if text:
			return text
	return ""


def _frame_by_id(frame_stack: Dict[str, Any], frame_id: str) -> Dict[str, Any]:
	target = _clean_text(frame_id)
	if not target:
		return {}
	for frame in _clean_dict_list(_clean_dict(frame_stack).get("frames")):
		if _clean_text(frame.get("frame_id")) == target:
			return frame
	return {}


def _resolved_rank(resolution: Dict[str, Any]) -> int:
	entity = _clean_dict(resolution.get("resolved_entity"))
	for value in (resolution.get("resolved_rank"), entity.get("rank"), _clean_dict(entity.get("row")).get("rank")):
		try:
			rank = int(value or 0)
		except (TypeError, ValueError):
			continue
		if rank > 0:
			return rank
	return 0


def _row_reference(resolution: Dict[str, Any]) -> str:
	rank = _resolved_rank(resolution)
	if rank > 0:
		return f"rank_{rank}"
	try:
		row_index = int(resolution.get("resolved_row_index"))
	except (TypeError, ValueError):
		row_index = -1
	if row_index >= 0:
		return f"row_index_{row_index}"
	return "none"


def _entity_label(resolution: Dict[str, Any]) -> str:
	entity = _clean_dict(resolution.get("resolved_entity"))
	row = _clean_dict(entity.get("row"))
	label = _first_text(entity.get("entity_label"), entity.get("label"), entity.get("entity_key"))
	if label:
		return label
	for key in ("customer", "supplier", "party", "product", "item", "invoice", "document", "account", "source_document"):
		label = _clean_text(row.get(key))
		if label:
			return label
	return ""


def _policy_boundary(answer_mode: str, authority_intent: str = "", authority_state: str = "") -> str:
	mode = _clean_text(answer_mode)
	intent = _clean_text(authority_intent)
	state = _clean_text(authority_state)
	if intent and intent != "safe_visible_fact":
		return intent
	if state and state not in {"safe_read_authority", "safe_read", "allowed"}:
		return state
	if mode in {"visible_context_answer", "current_artifact_answer", "direct_answer", "presentation_only"}:
		return "none"
	return mode or "none"


def _base_ledger(
	*,
	request_id: str,
	raw_message: str,
	route: str,
	decision_owners: Dict[str, Any],
	resolved_context: Dict[str, Any],
	authority: Dict[str, Any],
	owner_decisions: List[Dict[str, Any]] | None = None,
	advisory_inputs: List[Dict[str, Any]] | None = None,
	blocked_overrides: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
	return {
		"type": LEDGER_TYPE,
		"contract_version": CONTRACT_VERSION,
		"request_id": _clean_text(request_id),
		"raw_message": _clean_text(raw_message),
		"route": _clean_text(route),
		"decision_owners": _clean_dict(decision_owners),
		"resolved_context": _clean_dict(resolved_context),
		"authority": _clean_dict(authority),
		"owner_decisions": _clean_dict_list(owner_decisions or []),
		"advisory_inputs": _clean_dict_list(advisory_inputs or []),
		"override_policy": {
			"non_owner_override_allowed": False,
			"blocked_overrides": _clean_dict_list(blocked_overrides or []),
		},
		"created_at": _utc_now(),
	}


def build_visible_context_semantic_ownership_ledger(
	*,
	request_id: str,
	raw_message: str,
	answer_mode: str,
	resolution: Dict[str, Any],
	frame_stack: Dict[str, Any],
	frame_arbitration: Dict[str, Any],
	authority_intent: str = "",
) -> Dict[str, Any]:
	resolution_payload = _clean_dict(resolution)
	arbitration = _clean_dict(frame_arbitration)
	selected_frame = _frame_by_id(_clean_dict(frame_stack), _clean_text(arbitration.get("selected_frame_id")))
	selected_artifact_id = _first_text(
		arbitration.get("selected_artifact_id"),
		resolution_payload.get("resolved_artifact_id"),
		selected_frame.get("artifact_id"),
	)
	evidence_scope = _first_text(arbitration.get("selected_evidence_scope"), selected_frame.get("evidence_scope"))
	entity_type = _first_text(arbitration.get("selected_business_object_type"), selected_frame.get("business_object_type"))
	report_family = _first_text(selected_frame.get("family_id"), resolution_payload.get("selected_report_family"))
	selection_strategy = _first_text(arbitration.get("selection_strategy"), resolution_payload.get("selection_strategy"))
	row_reference = _row_reference(resolution_payload)
	policy_boundary = _policy_boundary(answer_mode, authority_intent=authority_intent)
	return _base_ledger(
		request_id=request_id,
		raw_message=raw_message,
		route="visible_context_followup",
		decision_owners={
			"route": "visible_context_followup_activation",
			"context": "visible_context_frame_stack_resolver",
			"row_entity_metric": "visible_context_frame_stack_resolver",
			"policy": "visible_context_followup_policy_gate",
			"answer_authority": "visible_context_followup_activation",
			"renderer": "visible_context_followup_renderer",
		},
		resolved_context={
			"artifact_id": selected_artifact_id,
			"report_family": report_family,
			"entity_type": entity_type,
			"entity_label": _entity_label(resolution_payload),
			"row_reference": row_reference,
			"relation": _clean_text(arbitration.get("relation")),
			"selection_strategy": selection_strategy,
			"status": _clean_text(arbitration.get("status") or resolution_payload.get("status")),
		},
		authority={
			"authority_source": evidence_scope or "visible_context_resolution",
			"evidence_scope": evidence_scope or "visible_context_resolution",
			"policy_boundary": policy_boundary,
			"answer_mode": _clean_text(answer_mode),
		},
		owner_decisions=[
			{
				"decision_type": "route",
				"owner": "visible_context_followup_activation",
				"decision": "visible_context_followup",
				"source": "visible_context_reference_contract",
			},
			{
				"decision_type": "context",
				"owner": "visible_context_frame_stack_resolver",
				"decision": selected_artifact_id,
				"source": selection_strategy,
			},
			{
				"decision_type": "authority",
				"owner": "visible_context_followup_policy_gate",
				"decision": policy_boundary,
				"source": _clean_text(authority_intent) or "safe_visible_fact",
			},
		],
		advisory_inputs=[
			{"source": "nbu_shadow", "role": "advisory_only"},
			{"source": "reasoning_semantic", "role": "advisory_only"},
		],
	)


def build_nbu_semantic_ownership_ledger(
	trace_payload: Dict[str, Any],
	*,
	activation_mode: str = "",
) -> Dict[str, Any]:
	trace = _clean_dict(trace_payload)
	decision = _clean_dict(trace.get("conversation_action_decision"))
	evidence = _clean_dict(trace.get("evidence_plan"))
	authority = _clean_dict(trace.get("authority_plan"))
	context = _clean_dict(trace.get("context_resolution"))
	candidate_id = _clean_text(trace.get("selected_candidate_id") or decision.get("selected_candidate_id"))
	action = _clean_text(decision.get("action")) or _clean_text(activation_mode) or "observe_only"
	response_mode = _clean_text(decision.get("response_mode")) or _clean_text(activation_mode)
	if bool(evidence.get("current_artifact_supported") or evidence.get("visible_artifact_supported")):
		authority_source = "visible_rendered_table"
		evidence_scope = "visible_artifact_rows"
	else:
		authority_source = _clean_text(evidence.get("evidence_need")) or "nbu_trace_contract"
		evidence_scope = authority_source
	policy_boundary = _policy_boundary(response_mode, authority_state=_clean_text(authority.get("approval_state")))
	return _base_ledger(
		request_id=_clean_text(trace.get("request_id")),
		raw_message=_clean_text(trace.get("raw_message")),
		route=action,
		decision_owners={
			"route": "natural_business_understanding_activation",
			"context": "natural_business_understanding_context_graph",
			"row_entity_metric": "natural_business_understanding_context_graph",
			"policy": "natural_business_understanding_authority_plan",
			"answer_authority": "natural_business_understanding_activation",
			"renderer": "natural_business_understanding_response_renderer",
			"shadow": "natural_business_understanding_shadow_observer",
		},
		resolved_context={
			"artifact_id": _clean_text(context.get("resolved_artifact_id")),
			"report_family": _clean_text(context.get("selected_report_family")),
			"entity_type": _clean_text(context.get("selected_entity_type")),
			"entity_label": _entity_label(context),
			"row_reference": _row_reference(context),
			"relation": _clean_text(context.get("target_reference")),
			"selection_strategy": _clean_text(context.get("selection_strategy")),
			"status": _clean_text(context.get("status")),
		},
		authority={
			"authority_source": authority_source,
			"evidence_scope": evidence_scope,
			"policy_boundary": policy_boundary,
			"answer_mode": _clean_text(activation_mode) or response_mode,
		},
		owner_decisions=[
			{
				"decision_type": "route",
				"owner": "natural_business_understanding_activation",
				"decision": action,
				"source": candidate_id,
			},
			{
				"decision_type": "context",
				"owner": "natural_business_understanding_context_graph",
				"decision": _clean_text(context.get("resolved_artifact_id")),
				"source": _clean_text(context.get("selection_strategy")),
			},
			{
				"decision_type": "authority",
				"owner": "natural_business_understanding_authority_plan",
				"decision": _clean_text(authority.get("approval_state")) or policy_boundary,
				"source": _clean_text(authority.get("authority_class")),
			},
		],
		advisory_inputs=[{"source": "shadow_trace", "role": "observer_unless_promoted"}],
	)
