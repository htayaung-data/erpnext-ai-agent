from __future__ import annotations

import re
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.contracts import (
	build_compound_request_assessment_contract,
	build_multi_step_execution_plan_contract,
	build_multi_step_execution_state_contract,
	build_multi_step_step_result_integration_contract,
)
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import (
	_deterministic_family_surface_interpretation,
	interpret_fresh_query_semantically,
)


_SEQUENTIAL_SPLIT_PATTERN = re.compile(
	r"(?:\s*;\s*|\s*\n+\s*|\s+(?:and then|then|after that|afterward|afterwards)\s+)",
	re.IGNORECASE,
)
_GENERIC_REQUEST_PREFIXES = (
	"show me ",
	"give me ",
	"list ",
	"show ",
	"give ",
)


def _clean_text(value: Any) -> str:
	return " ".join(str(value or "").strip().split())


def _clean_segment(segment: str) -> str:
	text = _clean_text(segment).strip(" ,.;:")
	return text


def _split_candidate_segments(message: str) -> List[str]:
	text = _clean_text(message)
	if not text:
		return []
	parts = [_clean_segment(part) for part in _SEQUENTIAL_SPLIT_PATTERN.split(text)]
	return [part for part in parts if part and len(part.split()) >= 2]


def _segment_option_label(segment: str) -> str:
	text = _clean_segment(segment)
	lower = text.lower()
	for prefix in _GENERIC_REQUEST_PREFIXES:
		if lower.startswith(prefix):
			text = text[len(prefix):].strip()
			break
	if text.lower().startswith("some "):
		text = text[5:].strip()
	if not text:
		text = _clean_segment(segment)
	return text[:1].upper() + text[1:]


def _segment_option_aliases(segment: str, label: str) -> List[str]:
	aliases = [segment, label]
	cleaned = _clean_segment(segment)
	for prefix in _GENERIC_REQUEST_PREFIXES:
		if cleaned.lower().startswith(prefix):
			aliases.append(cleaned[len(prefix):].strip())
			break
	if cleaned.lower().startswith("give me some "):
		aliases.append(cleaned[13:].strip())
	return list(dict.fromkeys([_clean_text(value) for value in aliases if _clean_text(value)]))


def _clean_text_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_dict_list(values: Any) -> List[Dict[str, Any]]:
	if not isinstance(values, list):
		return []
	return [dict(value) for value in values if isinstance(value, dict) and value]


def _segment_execution_payload(
	*,
	segment: str,
	label: str,
	source: str,
	interpretation: Any,
) -> Dict[str, Any]:
	return {
		"segment_message": _clean_text(segment),
		"segment_label": _clean_text(label),
		"interpretation_source": _clean_text(source),
		"intent_class": _clean_text(getattr(interpretation, "intent_class", "")),
		"route_target": _clean_text(getattr(interpretation, "route_target", "")),
		"response_mode": _clean_text(getattr(interpretation, "response_mode", "")),
		"candidate_capability_ids": _clean_text_list(getattr(interpretation, "candidate_capability_ids", [])),
		"candidate_reports": _clean_text_list(getattr(interpretation, "candidate_reports", [])),
		"requested_dimensions": _clean_text_list(getattr(interpretation, "requested_dimensions", [])),
	}


def _multi_step_bridge_step_payloads(
	*,
	segments: List[str],
	suggested_options: List[str],
	internal_details: Dict[str, Any],
) -> List[Dict[str, Any]]:
	segment_execution_payloads = _clean_dict_list(internal_details.get("segment_execution_payloads"))
	step_count = max(len(segments), len(suggested_options), len(segment_execution_payloads))
	steps: List[Dict[str, Any]] = []
	for index in range(step_count):
		payload = segment_execution_payloads[index] if index < len(segment_execution_payloads) else {}
		segment_message = _clean_text(payload.get("segment_message") or (segments[index] if index < len(segments) else ""))
		segment_label = _clean_text(payload.get("segment_label") or (suggested_options[index] if index < len(suggested_options) else ""))
		steps.append(
			{
				"step_id": f"step_{index + 1}",
				"step_index": index + 1,
				"step_message": segment_message,
				"step_label": segment_label,
				"interpretation_source": _clean_text(payload.get("interpretation_source")),
				"intent_class": _clean_text(payload.get("intent_class")),
				"route_target": _clean_text(payload.get("route_target")),
				"response_mode": _clean_text(payload.get("response_mode")),
				"candidate_capability_ids": _clean_text_list(payload.get("candidate_capability_ids")),
				"candidate_reports": _clean_text_list(payload.get("candidate_reports")),
				"requested_dimensions": _clean_text_list(payload.get("requested_dimensions")),
				"dependency_step_ids": [],
				"carryover_classes": [],
			}
		)
	return steps


def _find_current_step_index(steps: List[Dict[str, Any]], internal_details: Dict[str, Any]) -> int:
	primary_payload = _clean_dict(internal_details.get("primary_segment_payload"))
	primary_message = _clean_text(primary_payload.get("segment_message") or internal_details.get("primary_segment_message"))
	primary_label = _clean_text(primary_payload.get("segment_label") or internal_details.get("primary_segment_label"))
	if not primary_message and not primary_label:
		return 0
	for step in steps:
		step_message = _clean_text(step.get("step_message"))
		step_label = _clean_text(step.get("step_label"))
		if primary_message and primary_label:
			if step_message == primary_message and step_label == primary_label:
				return int(step.get("step_index") or 0)
		elif primary_message and step_message == primary_message:
			return int(step.get("step_index") or 0)
		elif primary_label and step_label == primary_label:
			return int(step.get("step_index") or 0)
	return 0


def build_multi_step_assessment_bridge(
	*,
	status: str,
	segments: List[str],
	suggested_options: List[str],
	internal_details: Dict[str, Any],
) -> Dict[str, Any]:
	steps = _multi_step_bridge_step_payloads(
		segments=segments,
		suggested_options=suggested_options,
		internal_details=internal_details,
	)
	current_step_index = _find_current_step_index(steps, internal_details)
	current_step_id = ""
	remaining_step_ids: List[str] = []
	completed_step_ids: List[str] = []
	clean_status = _clean_text(status)
	if clean_status == "ordered_execution_ready" and current_step_index > 0:
		current_step_id = f"step_{current_step_index}"
		remaining_step_ids = [
			str(step.get("step_id") or "").strip()
			for step in steps
			if int(step.get("step_index") or 0) > current_step_index
		]
		completed_step_ids = [
			str(step.get("step_id") or "").strip()
			for step in steps
			if 0 < int(step.get("step_index") or 0) < current_step_index
		]
	elif "clarification" in clean_status and current_step_index > 0:
		current_step_id = f"step_{current_step_index}"
		remaining_step_ids = [
			str(step.get("step_id") or "").strip()
			for step in steps
			if int(step.get("step_index") or 0) > current_step_index
		]
		completed_step_ids = [
			str(step.get("step_id") or "").strip()
			for step in steps
			if 0 < int(step.get("step_index") or 0) < current_step_index
		]
	elif clean_status == "ordered_execution_complete":
		completed_step_ids = [str(step.get("step_id") or "").strip() for step in steps]
	return {
		"assessment_kind": "multi_step",
		"compatibility_mode": "compound_request_assessment_bridge",
		"bridge_version": "1.0",
		"relationship_type": "independent_ordered",
		"status": clean_status,
		"step_count": len(steps),
		"current_step_id": current_step_id,
		"current_step_index": current_step_index,
		"remaining_step_ids": remaining_step_ids,
		"completed_step_ids": completed_step_ids,
		"steps": steps,
	}


def build_multi_step_execution_plan_payload(
	*,
	request_id: str,
	segments: List[str],
	suggested_options: List[str],
	internal_details: Dict[str, Any],
) -> Dict[str, Any]:
	steps = _multi_step_bridge_step_payloads(
		segments=segments,
		suggested_options=suggested_options,
		internal_details=internal_details,
	)
	entry_step_id = str((steps[0].get("step_id") if steps else "") or "").strip()
	return build_multi_step_execution_plan_contract(
		request_id=request_id,
		plan_id=f"{_clean_text(request_id)}:multi_step_execution_plan",
		relationship_type="independent_ordered",
		entry_step_id=entry_step_id,
		steps=steps,
		interruption_policy={
			"policy_id": "single_active_plan_latest_request_wins",
			"allow_user_resume": True,
			"allow_user_cancel": True,
			"preserve_recent_focus_on_interrupt": True,
			"preserve_prior_branch_on_interrupt": True,
		},
		clarification_policy={
			"policy_id": "step_local_clarification_blocks_later_steps",
			"step_requires_clarification_blocks_plan": True,
			"resume_mode": "resume_current_step",
			"preserve_completed_steps_on_clarification": True,
		},
		internal_details={
			"compatibility_mode": "compound_request_plan_bridge",
			"plan_source": "compound_request_support",
		},
	).to_payload()


def _multi_step_execution_state_kind(status: str) -> str:
	clean_status = _clean_text(status)
	if clean_status == "ordered_execution_complete":
		return "completed"
	if clean_status == "ordered_execution_cancelled":
		return "cancelled"
	if "clarification" in clean_status:
		return "waiting_for_clarification"
	if clean_status == "ordered_execution_ready":
		return "ready"
	if "interrupted" in clean_status:
		return "interrupted"
	return "ready"


def build_multi_step_execution_state_payload(
	*,
	request_id: str,
	status: str,
	segments: List[str],
	suggested_options: List[str],
	internal_details: Dict[str, Any],
	multi_step_assessment: Dict[str, Any] | None = None,
	multi_step_execution_plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	assessment_payload = (
		dict(multi_step_assessment)
		if isinstance(multi_step_assessment, dict) and multi_step_assessment
		else build_multi_step_assessment_bridge(
			status=status,
			segments=segments,
			suggested_options=suggested_options,
			internal_details=internal_details,
		)
	)
	plan_payload = (
		dict(multi_step_execution_plan)
		if isinstance(multi_step_execution_plan, dict) and multi_step_execution_plan
		else build_multi_step_execution_plan_payload(
			request_id=request_id,
			segments=segments,
			suggested_options=suggested_options,
			internal_details=internal_details,
		)
	)
	completed_step_ids = [
		str(value or "").strip()
		for value in (assessment_payload.get("completed_step_ids") or [])
		if str(value or "").strip()
	]
	remaining_step_ids = [
		str(value or "").strip()
		for value in (assessment_payload.get("remaining_step_ids") or [])
		if str(value or "").strip()
	]
	current_step_id = str(assessment_payload.get("current_step_id") or "").strip()
	state = _multi_step_execution_state_kind(status)
	current_step_status = ""
	waiting_step_id = ""
	if state == "ready" and current_step_id:
		current_step_status = "ready"
	elif state == "waiting_for_clarification":
		current_step_status = "waiting_for_clarification"
		waiting_step_id = current_step_id
	last_completed_step_id = completed_step_ids[-1] if completed_step_ids else ""
	return build_multi_step_execution_state_contract(
		request_id=request_id,
		execution_id=f"{_clean_text(request_id)}:multi_step_execution_state",
		plan_id=str(plan_payload.get("plan_id") or "").strip(),
		state=state,
		current_step_id=current_step_id,
		current_step_index=int(max(0, assessment_payload.get("current_step_index") or 0)),
		current_step_status=current_step_status,
		completed_step_ids=completed_step_ids,
		remaining_step_ids=remaining_step_ids,
		last_completed_step_id=last_completed_step_id,
		waiting_step_id=waiting_step_id,
		interruption_reason="",
		internal_details={
			"compatibility_mode": "compound_request_execution_state_bridge",
			"state_source": "compound_request_support",
			"step_count": int(max(0, assessment_payload.get("step_count") or 0)),
		},
	).to_payload()


def _ordered_multi_step_internal_details(payload: Dict[str, Any]) -> Dict[str, Any]:
	if not isinstance(payload, dict):
		return {}
	internal_details = payload.get("internal_details")
	if not isinstance(internal_details, dict):
		return {}
	if _clean_text(internal_details.get("execution_strategy")) != "ordered_multi_step":
		return {}
	return dict(internal_details)


def _ordered_multi_step_payload_has_active_step(payload: Dict[str, Any]) -> bool:
	if str((payload or {}).get("type") or "").strip() != "qwen_compound_request_assessment_contract":
		return False
	internal_details = _ordered_multi_step_internal_details(payload)
	if not internal_details:
		return False
	return bool(_clean_text(internal_details.get("primary_segment_message")))


def _ordered_multi_step_payload_list(internal_details: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
	values = internal_details.get(key)
	if not isinstance(values, list):
		return []
	return [dict(item) for item in values if isinstance(item, dict)]


def _ordered_multi_step_payload_item(internal_details: Dict[str, Any], key: str) -> Dict[str, Any]:
	value = internal_details.get(key)
	return dict(value) if isinstance(value, dict) else {}


def advance_compound_request_assessment_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
	if not _ordered_multi_step_payload_has_active_step(payload):
		return {}
	internal_details = _ordered_multi_step_internal_details(payload)
	segments = [str(value or "").strip() for value in (payload.get("segments") or []) if str(value or "").strip()]
	segment_labels = [str(value or "").strip() for value in (payload.get("suggested_options") or []) if str(value or "").strip()]
	remaining_messages = [
		str(value or "").strip()
		for value in (internal_details.get("remaining_segment_messages") or [])
		if str(value or "").strip()
	]
	remaining_labels = [
		str(value or "").strip()
		for value in (internal_details.get("remaining_segment_labels") or [])
		if str(value or "").strip()
	]
	primary_payload = _ordered_multi_step_payload_item(internal_details, "primary_segment_payload")
	remaining_payloads = _ordered_multi_step_payload_list(internal_details, "remaining_segment_payloads")
	all_payloads = _ordered_multi_step_payload_list(internal_details, "segment_execution_payloads")
	if not remaining_messages:
		updated_internal_details = compound_request_internal_details_with_multi_step_bridge(
			request_id=str(payload.get("request_id") or "").strip(),
			status="ordered_execution_complete",
			segments=segments,
			suggested_options=segment_labels,
			internal_details={
				**internal_details,
				"primary_segment_message": "",
				"primary_segment_label": "",
				"primary_segment_payload": {},
				"remaining_segment_messages": [],
				"remaining_segment_labels": [],
				"remaining_segment_payloads": [],
				"segment_execution_payloads": all_payloads,
				"last_completed_segment_message": str(internal_details.get("primary_segment_message") or "").strip(),
				"last_completed_segment_label": str(internal_details.get("primary_segment_label") or "").strip(),
				"last_completed_segment_payload": primary_payload,
			},
		)
		return build_compound_request_assessment_contract(
			request_id=str(payload.get("request_id") or "").strip(),
			status="ordered_execution_complete",
			segments=segments,
			suggested_options=segment_labels,
			clarification_required=False,
			reason=str(payload.get("reason") or "").strip(),
			internal_details=updated_internal_details,
		).to_payload()
	updated_internal_details = compound_request_internal_details_with_multi_step_bridge(
		request_id=str(payload.get("request_id") or "").strip(),
		status="ordered_execution_ready",
		segments=segments,
		suggested_options=segment_labels,
		internal_details={
			**internal_details,
			"primary_segment_message": remaining_messages[0],
			"primary_segment_label": remaining_labels[0] if remaining_labels else "",
			"primary_segment_payload": remaining_payloads[0] if remaining_payloads else {},
			"remaining_segment_messages": remaining_messages[1:],
			"remaining_segment_labels": remaining_labels[1:],
			"remaining_segment_payloads": remaining_payloads[1:],
			"segment_execution_payloads": all_payloads,
			"last_completed_segment_message": str(internal_details.get("primary_segment_message") or "").strip(),
			"last_completed_segment_label": str(internal_details.get("primary_segment_label") or "").strip(),
			"last_completed_segment_payload": primary_payload,
		},
	)
	return build_compound_request_assessment_contract(
		request_id=str(payload.get("request_id") or "").strip(),
		status="ordered_execution_ready",
		segments=segments,
		suggested_options=segment_labels,
		clarification_required=False,
		reason=str(payload.get("reason") or "").strip(),
		internal_details=updated_internal_details,
	).to_payload()


def build_multi_step_step_result_integration_payload(
	*,
	request_id: str,
	compound_assessment_payload: Dict[str, Any],
	grounded_turn_payload: Dict[str, Any] | None = None,
	clarification_signal_payload: Dict[str, Any] | None = None,
	normalized_family_artifact: Dict[str, Any] | None = None,
	family_validation_payload: Dict[str, Any] | None = None,
	semantic_validation_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	if str((compound_assessment_payload or {}).get("type") or "").strip() != "qwen_compound_request_assessment_contract":
		return {}
	internal_details = (
		dict((compound_assessment_payload or {}).get("internal_details") or {})
		if isinstance((compound_assessment_payload or {}).get("internal_details"), dict)
		else {}
	)
	execution_state = (
		dict(internal_details.get("multi_step_execution_state") or {})
		if isinstance(internal_details.get("multi_step_execution_state"), dict)
		else {}
	)
	execution_plan = (
		dict(internal_details.get("multi_step_execution_plan") or {})
		if isinstance(internal_details.get("multi_step_execution_plan"), dict)
		else {}
	)
	if not execution_state or not execution_plan:
		return {}
	source_step_id = _clean_text(execution_state.get("current_step_id"))
	source_step_index = int(max(0, execution_state.get("current_step_index") or 0))
	if not source_step_id or source_step_index <= 0:
		return {}
	plan_steps = execution_plan.get("steps") if isinstance(execution_plan.get("steps"), list) else []
	source_step = {}
	for item in plan_steps:
		if not isinstance(item, dict):
			continue
		if _clean_text(item.get("step_id")) == source_step_id:
			source_step = dict(item)
			break
	grounded_turn = dict(grounded_turn_payload or {}) if isinstance(grounded_turn_payload, dict) else {}
	clarification_signal = (
		dict(clarification_signal_payload or {})
		if isinstance(clarification_signal_payload, dict)
		else {}
	)
	normalized_artifact = (
		dict(normalized_family_artifact or {})
		if isinstance(normalized_family_artifact, dict)
		else {}
	)
	family_validation = (
		dict(family_validation_payload or {})
		if isinstance(family_validation_payload, dict)
		else {}
	)
	semantic_validation = (
		dict(semantic_validation_payload or {})
		if isinstance(semantic_validation_payload, dict)
		else {}
	)
	if grounded_turn and bool(grounded_turn.get("grounded")):
		result_kind = "governed_artifact"
		result_request_id = _clean_text(
			grounded_turn.get("trace_request_id") or grounded_turn.get("request_id") or request_id
		)
		update_recent_focus = True
		recent_focus_source_request_id = result_request_id
		result_handle = {
			"handle_kind": "grounded_turn",
			"grounded_request_id": result_request_id,
			"artifact_family_id": _clean_text(
				normalized_artifact.get("family_id") or grounded_turn.get("artifact_family_id")
			),
			"artifact_type": _clean_text(normalized_artifact.get("artifact_type")),
			"source_report": _clean_text(
				grounded_turn.get("source_name")
				or ((grounded_turn.get("artifact_source_reports") or [""])[0] if isinstance(grounded_turn.get("artifact_source_reports"), list) else "")
			),
		}
		interruption_policy = {
			"owner_resolution_mode": "grounded_result_remains_current_step_authority_until_superseded",
			"preserve_prior_branch": True,
		}
		internal_details_payload = {
			"integration_action": "promote_grounded_result_to_recent_focus",
			"source_step_label": _clean_text(source_step.get("step_label")),
			"family_validation_status": _clean_text(family_validation.get("status")),
			"semantic_validation_status": _clean_text(semantic_validation.get("status")),
		}
	elif clarification_signal:
		result_kind = "clarification_signal"
		result_request_id = _clean_text(clarification_signal.get("request_id") or request_id)
		update_recent_focus = False
		recent_focus_source_request_id = ""
		result_handle = {
			"handle_kind": "clarification_signal",
			"clarification_type": _clean_text(clarification_signal.get("type")),
		}
		interruption_policy = {
			"owner_resolution_mode": "await_current_step_clarification_before_later_steps",
			"preserve_prior_branch": True,
		}
		internal_details_payload = {
			"integration_action": "pause_plan_for_current_step_clarification",
			"source_step_label": _clean_text(source_step.get("step_label")),
			"clarification_required": True,
		}
	else:
		return {}
	return build_multi_step_step_result_integration_contract(
		request_id=request_id,
		execution_id=_clean_text(execution_state.get("execution_id")),
		plan_id=_clean_text(execution_plan.get("plan_id")),
		source_step_id=source_step_id,
		source_step_index=source_step_index,
		result_kind=result_kind,
		result_request_id=result_request_id,
		update_recent_focus=update_recent_focus,
		recent_focus_source_request_id=recent_focus_source_request_id,
		carryover_classes=[
			_clean_text(value)
			for value in (source_step.get("carryover_classes") or [])
			if _clean_text(value)
		],
		result_handle=result_handle,
		interruption_policy=interruption_policy,
		internal_details=internal_details_payload,
	).to_payload()


def build_post_result_multi_step_assessment_payload(
	*,
	compound_assessment_payload: Dict[str, Any],
	step_result_integration_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	if not _ordered_multi_step_payload_has_active_step(compound_assessment_payload):
		return {}
	step_result_integration = (
		dict(step_result_integration_payload or {})
		if isinstance(step_result_integration_payload, dict)
		else {}
	)
	if _clean_text(step_result_integration.get("type")) != "qwen_multi_step_step_result_integration_contract":
		return {}
	result_kind = _clean_text(step_result_integration.get("result_kind"))
	if result_kind == "governed_artifact":
		return advance_compound_request_assessment_payload(compound_assessment_payload)
	if result_kind != "clarification_signal":
		return {}
	internal_details = _ordered_multi_step_internal_details(compound_assessment_payload)
	segments = [
		str(value or "").strip()
		for value in (compound_assessment_payload.get("segments") or [])
		if str(value or "").strip()
	]
	segment_labels = [
		str(value or "").strip()
		for value in (compound_assessment_payload.get("suggested_options") or [])
		if str(value or "").strip()
	]
	updated_internal_details = compound_request_internal_details_with_multi_step_bridge(
		request_id=str(compound_assessment_payload.get("request_id") or "").strip(),
		status="ordered_execution_waiting_for_clarification",
		segments=segments,
		suggested_options=segment_labels,
		internal_details={
			**internal_details,
			"current_step_clarification_required": True,
			"latest_step_result_integration": step_result_integration,
			"waiting_for_current_clarification": True,
		},
	)
	return build_compound_request_assessment_contract(
		request_id=str(compound_assessment_payload.get("request_id") or "").strip(),
		status="ordered_execution_waiting_for_clarification",
		segments=segments,
		suggested_options=segment_labels,
		clarification_required=True,
		reason=str(compound_assessment_payload.get("reason") or "").strip(),
		internal_details=updated_internal_details,
	).to_payload()


def compound_request_internal_details_with_multi_step_bridge(
	*,
	request_id: str,
	status: str,
	segments: List[str],
	suggested_options: List[str],
	internal_details: Dict[str, Any],
) -> Dict[str, Any]:
	normalized_internal_details = dict(internal_details or {})
	normalized_segments = [_clean_text(value) for value in segments if _clean_text(value)]
	normalized_options = [_clean_text(value) for value in suggested_options if _clean_text(value)]
	multi_step_assessment = build_multi_step_assessment_bridge(
		status=status,
		segments=normalized_segments,
		suggested_options=normalized_options,
		internal_details=normalized_internal_details,
	)
	normalized_internal_details["multi_step_assessment"] = multi_step_assessment
	multi_step_execution_plan = build_multi_step_execution_plan_payload(
		request_id=request_id,
		segments=normalized_segments,
		suggested_options=normalized_options,
		internal_details=normalized_internal_details,
	)
	normalized_internal_details["multi_step_execution_plan"] = multi_step_execution_plan
	normalized_internal_details["multi_step_execution_state"] = build_multi_step_execution_state_payload(
		request_id=request_id,
		status=status,
		segments=normalized_segments,
		suggested_options=normalized_options,
		internal_details=normalized_internal_details,
		multi_step_assessment=multi_step_assessment,
		multi_step_execution_plan=multi_step_execution_plan,
	)
	return normalized_internal_details


def _supported_segment_interpretation(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	segment: str,
) -> Dict[str, Any]:
	deterministic = _deterministic_family_surface_interpretation(
		request_id=request_id,
		session_id=session_id,
		message=segment,
		confidence_threshold=0.72,
	)
	if deterministic is not None and (
		list(getattr(deterministic, "candidate_capability_ids", []) or [])
		or list(getattr(deterministic, "candidate_reports", []) or [])
	):
		return {
			"status": "accepted",
			"source": "deterministic_surface",
			"interpretation": deterministic,
		}
	semantic = interpret_fresh_query_semantically(
		request_id=request_id,
		session_id=session_id,
		user_id=user_id,
		site_name=site_name,
		message=segment,
		recent_messages=[],
	)
	interpretation = getattr(semantic, "interpretation", None)
	if (
		str(getattr(semantic, "status", "") or "").strip() == "accepted"
		and interpretation is not None
		and (
			list(getattr(interpretation, "candidate_capability_ids", []) or [])
			or list(getattr(interpretation, "candidate_reports", []) or [])
		)
	):
		return {
			"status": "accepted",
			"source": "semantic_interpreter",
			"interpretation": interpretation,
		}
	return {}


def assess_compound_request(
	*,
	request_id: str,
	session_id: str,
	user_id: str,
	site_name: str,
	message: str,
) -> Dict[str, Any]:
	segments = _split_candidate_segments(message)
	if len(segments) < 2:
		return {}
	supported_segments: List[Dict[str, Any]] = []
	for index, segment in enumerate(segments, start=1):
		supported = _supported_segment_interpretation(
			request_id=f"{request_id}-segment-{index}",
			session_id=session_id,
			user_id=user_id,
			site_name=site_name,
			segment=segment,
		)
		if not supported:
			return {}
		supported_segments.append(
			{
				"message": segment,
				"source": str(supported.get("source") or "").strip(),
				"interpretation": supported.get("interpretation"),
			}
		)
	option_aliases_by_option: Dict[str, List[str]] = {}
	resolved_message_by_option: Dict[str, str] = {}
	suggested_options: List[str] = []
	segment_execution_payloads: List[Dict[str, Any]] = []
	for item in supported_segments:
		segment = str(item.get("message") or "").strip()
		option = _segment_option_label(segment)
		base_option = option
		suffix = 2
		while option in resolved_message_by_option:
			option = f"{base_option} ({suffix})"
			suffix += 1
		suggested_options.append(option)
		resolved_message_by_option[option] = segment
		option_aliases_by_option[option] = _segment_option_aliases(segment, base_option)
		segment_execution_payloads.append(
			_segment_execution_payload(
				segment=segment,
				label=option,
				source=str(item.get("source") or "").strip(),
				interpretation=item.get("interpretation"),
			)
		)
	primary_segment_message = str(segments[0] or "").strip()
	primary_segment_label = str(suggested_options[0] or "").strip()
	primary_segment_payload = dict(segment_execution_payloads[0] or {}) if segment_execution_payloads else {}
	remaining_segment_messages = [str(value or "").strip() for value in segments[1:] if str(value or "").strip()]
	remaining_segment_labels = [str(value or "").strip() for value in suggested_options[1:] if str(value or "").strip()]
	remaining_segment_payloads = [
		dict(value or {})
		for value in segment_execution_payloads[1:]
		if isinstance(value, dict) and value
	]
	reason = (
		"The message contains multiple self-contained ERP requests in a stated sequence, "
		"so the front door should preserve ordered execution instead of forcing a branch-choice clarification."
	)
	internal_details = compound_request_internal_details_with_multi_step_bridge(
		request_id=request_id,
		status="ordered_execution_ready",
		segments=segments,
		suggested_options=suggested_options,
		internal_details={
			"continuation_lane": "front_door",
			"execution_strategy": "ordered_multi_step",
			"resolved_message_by_option": resolved_message_by_option,
			"option_aliases_by_option": option_aliases_by_option,
			"segment_messages": segments,
			"segment_labels": suggested_options,
			"segment_count": len(segments),
			"primary_segment_message": primary_segment_message,
			"primary_segment_label": primary_segment_label,
			"primary_segment_payload": primary_segment_payload,
			"remaining_segment_messages": remaining_segment_messages,
			"remaining_segment_labels": remaining_segment_labels,
			"remaining_segment_payloads": remaining_segment_payloads,
			"segment_execution_payloads": [
				dict(value or {})
				for value in segment_execution_payloads
				if isinstance(value, dict) and value
			],
		},
	)
	assessment = build_compound_request_assessment_contract(
		request_id=request_id,
		status="ordered_execution_ready",
		segments=segments,
		suggested_options=suggested_options,
		clarification_required=False,
		reason=reason,
		internal_details=internal_details,
	)
	return {
		"assessment_contract": assessment,
		"clarification_signal": None,
		"user_question": "",
		"reason": reason,
	}
