from __future__ import annotations

from typing import Any, Dict


def empty_resumable_prior_request_state() -> Dict[str, Any]:
	return {
		"available": False,
		"branch_kind": "none",
		"branch_label": "",
		"source_request_id": "",
		"target_family": "",
		"target_scope": {},
		"accepted_recovery_action": "",
		"resumable": False,
		"suggested_restore_mode": "",
		"derivation_basis": "conservative_none",
		"confidence": 0.0,
		"source_tool_index": -1,
	}


def build_snapshot_state_quality(
	*,
	pending_clarification: Dict[str, Any],
	latest_grounded_turn: Dict[str, Any],
	latest_artifact: Dict[str, Any],
	latest_recovery_contract: Dict[str, Any],
	latest_repair_intent: Dict[str, Any],
	active_sequence: Dict[str, Any],
	recent_focus: Dict[str, Any],
	recent_focus_affordance: Dict[str, Any],
	resumable_prior_request: Dict[str, Any],
) -> Dict[str, Any]:
	return {
		"has_authoritative_pending_clarification": bool(
			pending_clarification.get("available") and pending_clarification.get("source_kind") == "stored_state"
		),
		"has_grounded_turn": bool(latest_grounded_turn.get("available") and latest_grounded_turn.get("grounded")),
		"has_grounded_compatible_artifact": bool(
			latest_artifact.get("available") and latest_artifact.get("grounded_compatible")
		),
		"has_recovery_contract": bool(latest_recovery_contract.get("available")),
		"has_latest_repair_intent": bool(latest_repair_intent.get("available")),
		"has_active_sequence": bool(active_sequence.get("active")),
		"has_recent_focus": bool(recent_focus.get("available")),
		"has_recent_focus_affordance": bool(recent_focus_affordance),
		"has_resumable_prior_request": bool(resumable_prior_request.get("available")),
	}


def build_snapshot_internal_details(
	*,
	pending_clarification: Dict[str, Any],
	latest_artifact: Dict[str, Any],
	latest_repair_intent: Dict[str, Any],
	recent_focus: Dict[str, Any],
	recent_focus_affordance: Dict[str, Any],
	resumable_prior_request: Dict[str, Any],
) -> Dict[str, Any]:
	return {
		"source_summary": {
			"pending_clarification_source_kind": str(pending_clarification.get("source_kind") or "").strip(),
			"latest_artifact_source_quality": str(latest_artifact.get("source_quality") or "").strip(),
			"latest_repair_intent_type": str(latest_repair_intent.get("repair_intent_type") or "").strip(),
			"recent_focus_derivation_basis": str(recent_focus.get("derivation_basis") or "").strip(),
			"recent_focus_affordance_reason": str(recent_focus_affordance.get("reason") or "").strip(),
			"resumable_prior_request_derivation_basis": str(
				resumable_prior_request.get("derivation_basis") or ""
			).strip(),
		},
		"fallbacks_used": [
			value
			for value in [
				"pending_clarification_message_fallback"
				if pending_clarification.get("source_kind") == "message_fallback"
				else "",
				"artifact_fallback_candidate" if latest_artifact.get("source_quality") == "fallback_candidate" else "",
			]
			if value
		],
	}


def build_pending_clarification_snapshot_state(
	*,
	signal: Dict[str, Any],
	source_kind: str,
	attempt_count: int,
	max_attempts: int,
	continuation_lane: str,
	status: str,
	source_tool_index: int,
) -> Dict[str, Any]:
	return {
		"available": bool(signal),
		"source_kind": str(source_kind or "").strip(),
		"signal": dict(signal or {}),
		"attempt_count": int(max(0, attempt_count or 0)),
		"max_attempts": int(max(0, max_attempts or 0)),
		"continuation_lane": str(continuation_lane or "").strip(),
		"status": str(status or "").strip(),
		"source_tool_index": int(source_tool_index if isinstance(source_tool_index, int) else -1),
	}


def build_latest_grounded_turn_snapshot_state(
	*,
	payload: Dict[str, Any],
	source_tool_index: int,
) -> Dict[str, Any]:
	artifact_source_reports = []
	for value in ((payload or {}).get("artifact_source_reports") or []):
		report_name = str(value or "").strip()
		if report_name:
			artifact_source_reports.append(report_name)
	return {
		"available": bool(payload),
		"payload": dict(payload or {}),
		"request_id": str((payload or {}).get("request_id") or "").strip(),
		"trace_request_id": str((payload or {}).get("trace_request_id") or "").strip(),
		"grounded": bool((payload or {}).get("grounded")),
		"source_name": str((payload or {}).get("source_name") or "").strip(),
		"artifact_family_id": str((payload or {}).get("artifact_family_id") or "").strip(),
		"artifact_source_reports": artifact_source_reports,
		"source_quality": "grounded" if bool((payload or {}).get("grounded")) else "absent",
		"source_tool_index": int(source_tool_index if isinstance(source_tool_index, int) else -1),
	}


def build_latest_artifact_snapshot_state(
	*,
	payload: Dict[str, Any],
	grounded_compatible: bool,
	source_tool_index: int,
) -> Dict[str, Any]:
	source_reports = []
	for value in ((payload or {}).get("source_reports") or []):
		report_name = str(value or "").strip()
		if report_name:
			source_reports.append(report_name)
	source_quality = "absent"
	if payload:
		source_quality = "grounded_compatible" if bool(grounded_compatible) else "fallback_candidate"
	return {
		"available": bool(payload),
		"payload": dict(payload or {}),
		"request_id": str((payload or {}).get("request_id") or "").strip(),
		"family_id": str((payload or {}).get("family_id") or "").strip(),
		"artifact_type": str((payload or {}).get("artifact_type") or (payload or {}).get("type") or "").strip(),
		"source_reports": source_reports,
		"grounded_compatible": bool(grounded_compatible),
		"source_quality": source_quality,
		"source_tool_index": int(source_tool_index if isinstance(source_tool_index, int) else -1),
	}


def build_active_sequence_snapshot_state(
	*,
	payload: Dict[str, Any],
	active: bool,
	source_tool_index: int,
) -> Dict[str, Any]:
	internal_details = (payload or {}).get("internal_details")
	if not isinstance(internal_details, dict):
		internal_details = {}
	segments = []
	for value in ((payload or {}).get("segments") or []):
		segment = str(value or "").strip()
		if segment:
			segments.append(segment)
	remaining_segment_messages = []
	for value in (internal_details.get("remaining_segment_messages") or []):
		segment = str(value or "").strip()
		if segment:
			remaining_segment_messages.append(segment)
	return {
		"available": bool(payload),
		"payload": dict(payload or {}),
		"request_id": str((payload or {}).get("request_id") or "").strip(),
		"status": str((payload or {}).get("status") or "").strip(),
		"segments": segments,
		"primary_segment_message": str(internal_details.get("primary_segment_message") or "").strip(),
		"remaining_segment_messages": remaining_segment_messages,
		"execution_strategy": str(internal_details.get("execution_strategy") or "").strip(),
		"active": bool(active),
		"source_tool_index": int(source_tool_index if isinstance(source_tool_index, int) else -1),
	}


def build_historical_recent_focus_snapshot_inputs(
	*,
	grounded_turn_payload: Dict[str, Any],
	grounded_turn_source_tool_index: int,
	artifact_payload: Dict[str, Any],
	artifact_source_tool_index: int,
	recovery_payload: Dict[str, Any],
	recovery_source_tool_index: int,
) -> Dict[str, Dict[str, Any]]:
	return {
		"latest_grounded_turn": build_latest_grounded_turn_snapshot_state(
			payload=dict(grounded_turn_payload or {}),
			source_tool_index=grounded_turn_source_tool_index,
		),
		"latest_artifact": build_latest_artifact_snapshot_state(
			payload=dict(artifact_payload or {}),
			grounded_compatible=bool(artifact_payload),
			source_tool_index=artifact_source_tool_index,
		),
		"latest_recovery_contract": build_latest_recovery_contract_snapshot_state(
			payload=dict(recovery_payload or {}),
			source_tool_index=recovery_source_tool_index,
		),
	}


def build_latest_recovery_contract_snapshot_state(
	*,
	payload: Dict[str, Any],
	source_tool_index: int,
) -> Dict[str, Any]:
	return {
		"available": bool(payload),
		"payload": dict(payload or {}),
		"request_id": str((payload or {}).get("request_id") or "").strip(),
		"source_request_id": str((payload or {}).get("source_request_id") or "").strip(),
		"source_family_id": str((payload or {}).get("source_family_id") or "").strip(),
		"source_capability_id": str((payload or {}).get("source_capability_id") or "").strip(),
		"source_report": str((payload or {}).get("source_report") or "").strip(),
		"recovery_state": str((payload or {}).get("recovery_state") or "").strip(),
		"recommended_recovery_action": str((payload or {}).get("recommended_recovery_action") or "").strip(),
		"allowed_to_recover": bool((payload or {}).get("allowed_to_recover")),
		"source_tool_index": int(source_tool_index if isinstance(source_tool_index, int) else -1),
	}


def build_latest_repair_intent_snapshot_state(
	*,
	payload: Dict[str, Any],
	source_tool_index: int,
) -> Dict[str, Any]:
	confidence = (payload or {}).get("confidence")
	try:
		confidence_value = float(confidence or 0.0)
	except (TypeError, ValueError):
		confidence_value = 0.0
	confidence_value = max(0.0, min(1.0, confidence_value))
	return {
		"available": bool(payload),
		"payload": dict(payload or {}),
		"request_id": str((payload or {}).get("request_id") or "").strip(),
		"repair_intent_type": str((payload or {}).get("repair_intent_type") or "").strip(),
		"repair_state": str((payload or {}).get("repair_state") or "").strip(),
		"targets_prior_recovery": bool((payload or {}).get("targets_prior_recovery")),
		"accepted_recovery_action": str((payload or {}).get("accepted_recovery_action") or "").strip(),
		"allowed_next_lane": str((payload or {}).get("allowed_next_lane") or "").strip(),
		"confidence": confidence_value,
		"source_tool_index": int(source_tool_index if isinstance(source_tool_index, int) else -1),
	}
