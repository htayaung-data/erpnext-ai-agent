from __future__ import annotations

from typing import Any, Dict

from ai_assistant_ui.qwen_chat.conversation_control_language import (
	prior_branch_phrase_type_from_control_action,
	prior_branch_restore_phrase_type,
	targeted_restore_hint_from_control_evidence,
	targeted_restore_hint_from_message,
)
from ai_assistant_ui.qwen_chat.conversation_control_support import (
	select_authoritative_pending_clarification_restore_spec as _select_authoritative_pending_clarification_restore_spec_helper,
	select_direct_restore_fallback_spec as _select_direct_restore_fallback_spec_helper,
	select_latest_non_clarification_restore_state as _select_latest_non_clarification_restore_state_helper,
	select_non_clarification_restore_owner as _select_non_clarification_restore_owner_helper,
	select_prior_branch_restore_request_interpretation as _select_prior_branch_restore_request_interpretation_helper,
	select_prior_branch_restore_route as _select_prior_branch_restore_route_helper,
	select_targeted_restore_owner as _select_targeted_restore_owner_helper,
	select_targeted_recent_focus_restore_spec as _select_targeted_recent_focus_restore_spec_helper,
	select_targeted_resumable_prior_request_restore_spec as _select_targeted_resumable_prior_request_restore_spec_helper,
)


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _build_prior_branch_restore_contract(**kwargs):
	from ai_assistant_ui.qwen_chat.contracts import build_prior_branch_restore_contract

	return build_prior_branch_restore_contract(**kwargs)


def _build_prior_branch_restore_fresh_query_contracts(*, request_id: str):
	from ai_assistant_ui.qwen_chat.contracts import (
		ExecutionPath,
		build_followup_resolution_contract,
		build_governed_scope_decision_contract,
		build_scope_decision_input,
	)

	followup_resolution = build_followup_resolution_contract(
		request_id=request_id,
		mode="new_query",
		depends_on_grounded_turn=False,
		self_contained=True,
		latest_grounded_turn_available=False,
		reason="The user chose to restore a prior branch by replaying it as a fresh governed query.",
	)
	execution_path = ExecutionPath(
		request_id=request_id,
		path="prior_branch_restore_requery",
		reason="The user asked to restore a prior branch by rerunning it through current governed routes.",
		requires_runtime=True,
		grounded_required=False,
	)
	scope_decision_contract = build_governed_scope_decision_contract(
		request_id=request_id,
		stage="prior_branch_restore",
		followup_resolution=followup_resolution,
		context_isolation=build_scope_decision_input(force_new_query=True, reason="Prior branch restore replay."),
		latest_grounded_turn_available=False,
		entity_drilldown=None,
		continuation_contract=None,
		clarification_required=False,
	)
	return followup_resolution, execution_path, scope_decision_contract


def build_prior_branch_restore_fresh_query_plan(
	*,
	request_id: str,
	prior_branch_restore_contract,
) -> Dict[str, Any]:
	if prior_branch_restore_contract is None:
		return {"handled": False}
	if _clean_text(getattr(prior_branch_restore_contract, "restore_mode", "")) != "replay_as_fresh_governed_query":
		return {"handled": False}
	prior_recovery_payload = dict(
		(getattr(prior_branch_restore_contract, "internal_details", {}) or {}).get("prior_recovery_payload") or {}
	)
	if not prior_recovery_payload:
		return {"handled": False}
	from ai_assistant_ui.qwen_chat.recovery_support import build_recovery_governed_query_message

	synthesized_message = build_recovery_governed_query_message(prior_recovery_payload)
	if not synthesized_message:
		return {"handled": False}
	governed_target_limit = int(
		max(
			0,
			(
				(getattr(prior_branch_restore_contract, "target_scope", {}) or {}).get("requested_top_n")
				or 0
			),
		)
	)
	followup_resolution, execution_path, scope_decision_contract = _build_prior_branch_restore_fresh_query_contracts(
		request_id=request_id,
	)
	return {
		"handled": True,
		"prior_recovery_payload": prior_recovery_payload,
		"synthesized_message": synthesized_message,
		"governed_target_limit": governed_target_limit,
		"followup_resolution": followup_resolution,
		"execution_path": execution_path,
		"scope_decision_contract": scope_decision_contract,
	}


_TARGETED_RESTORE_FOCUS_KIND_COMPATIBILITY = {
	"entity": {"entity"},
	"listing": {"listing"},
	"document": {"document"},
	"statement": {"statement", "report"},
	"report": {"report", "statement"},
}


def targeted_restore_focus_kind_matches(*, candidate_focus_kind: str, target_focus_kind: str) -> bool:
	target_kind = _clean_text(target_focus_kind).lower()
	if not target_kind:
		return True
	candidate_kind = _clean_text(candidate_focus_kind).lower()
	allowed_kinds = _TARGETED_RESTORE_FOCUS_KIND_COMPATIBILITY.get(target_kind, {target_kind})
	return candidate_kind in allowed_kinds


def recent_focus_matches_targeted_restore(
	recent_focus_state: Dict[str, Any],
	*,
	target_hint: str,
	target_grain: str,
	target_focus_kind: str,
) -> bool:
	if not isinstance(recent_focus_state, dict) or not bool(recent_focus_state.get("available")):
		return False
	focus_kind = _clean_text(recent_focus_state.get("focus_kind")).lower()
	if not targeted_restore_focus_kind_matches(
		candidate_focus_kind=focus_kind,
		target_focus_kind=target_focus_kind,
	):
		return False
	focus_grain = _clean_text(recent_focus_state.get("focus_grain")).lower()
	focus_label = _clean_text(recent_focus_state.get("focus_label")).lower()
	source_report = _clean_text(recent_focus_state.get("source_report")).lower()
	normalized_target_grain = _clean_text(target_grain).lower()
	normalized_target_hint = _clean_text(target_hint).lower()
	if normalized_target_grain and normalized_target_grain == focus_grain:
		return True
	if normalized_target_hint and (normalized_target_hint in focus_label or normalized_target_hint in source_report):
		return True
	return False


def resumable_prior_request_matches_targeted_restore(
	resumable_prior_request: Dict[str, Any],
	*,
	target_hint: str,
	target_grain: str,
	target_focus_kind: str,
) -> bool:
	if not isinstance(resumable_prior_request, dict) or not bool(resumable_prior_request.get("available")):
		return False
	branch_label = _clean_text(resumable_prior_request.get("branch_label")).lower()
	target_family = _clean_text(resumable_prior_request.get("target_family")).lower()
	branch_kind = _clean_text(resumable_prior_request.get("branch_kind")).lower()
	target_scope = (
		resumable_prior_request.get("target_scope")
		if isinstance(resumable_prior_request.get("target_scope"), dict)
		else {}
	)
	scope_focus_kind = _clean_text(target_scope.get("focus_kind")).lower()
	scope_focus_grain = _clean_text(target_scope.get("focus_grain")).lower()
	scope_focus_label = _clean_text(target_scope.get("focus_label")).lower()
	scope_source_report = _clean_text(target_scope.get("source_report")).lower()
	scope_source_capability = _clean_text(target_scope.get("source_capability")).lower()
	candidate_focus_kind = scope_focus_kind
	if candidate_focus_kind and not targeted_restore_focus_kind_matches(
		candidate_focus_kind=candidate_focus_kind,
		target_focus_kind=target_focus_kind,
	):
		return False
	normalized_target_grain = _clean_text(target_grain).lower()
	normalized_target_hint = _clean_text(target_hint).lower()
	if normalized_target_grain and (
		normalized_target_grain in target_family
		or normalized_target_grain in branch_kind
		or normalized_target_grain in branch_label
		or normalized_target_grain == scope_focus_grain
		or normalized_target_grain in scope_focus_kind
		or normalized_target_grain in scope_focus_label
		or normalized_target_grain in scope_source_report
		or normalized_target_grain in scope_source_capability
	):
		return True
	if normalized_target_hint and (
		normalized_target_hint in branch_label
		or normalized_target_hint in target_family
		or normalized_target_hint in scope_focus_label
		or normalized_target_hint in scope_source_report
	):
		return True
	return False


def _source_tool_index(state_payload: Dict[str, Any]) -> int:
	if not isinstance(state_payload, dict):
		return -1
	try:
		return int(state_payload.get("source_tool_index", -1) or -1)
	except (TypeError, ValueError):
		return -1


def _state_is_newer(candidate_state: Dict[str, Any], baseline_state: Dict[str, Any]) -> bool:
	candidate_index = _source_tool_index(candidate_state)
	baseline_index = _source_tool_index(baseline_state)
	if candidate_index < 0 or baseline_index < 0:
		return False
	return candidate_index > baseline_index


def _pending_clarification_is_non_authoritative_fallback(pending_clarification: Dict[str, Any]) -> bool:
	if not bool((pending_clarification or {}).get("available")):
		return False
	if _source_tool_index(pending_clarification) >= 0:
		return False
	return _clean_text((pending_clarification or {}).get("source_kind")) == "message_fallback"


def _pending_clarification_is_restore_authoritative(pending_clarification: Dict[str, Any]) -> bool:
	if not bool((pending_clarification or {}).get("available")):
		return False
	return not _pending_clarification_is_non_authoritative_fallback(pending_clarification)


def _state_precedes_pending_clarification(
	candidate_state: Dict[str, Any],
	pending_clarification: Dict[str, Any],
) -> bool:
	if not bool((pending_clarification or {}).get("available")):
		return True
	if _state_is_newer(candidate_state, pending_clarification):
		return True
	if not _pending_clarification_is_non_authoritative_fallback(pending_clarification):
		return False
	return _source_tool_index(candidate_state) >= 0


def pending_clarification_is_non_authoritative_fallback(pending_clarification: Dict[str, Any]) -> bool:
	return _pending_clarification_is_non_authoritative_fallback(pending_clarification)


def pending_clarification_is_restore_authoritative(pending_clarification: Dict[str, Any]) -> bool:
	return _pending_clarification_is_restore_authoritative(pending_clarification)


def state_precedes_pending_clarification(
	candidate_state: Dict[str, Any],
	pending_clarification: Dict[str, Any],
) -> bool:
	return _state_precedes_pending_clarification(candidate_state, pending_clarification)


def _peer_precedence_basis(candidate_state: Dict[str, Any], baseline_state: Dict[str, Any]) -> str:
	candidate_index = _source_tool_index(candidate_state)
	baseline_index = _source_tool_index(baseline_state)
	if candidate_index >= 0 and baseline_index < 0:
		return "known_over_unindexed"
	if _state_is_newer(candidate_state, baseline_state):
		return "newer"
	return ""


def build_prior_branch_restore_snapshot_context(
	*,
	conversation_state_snapshot: Any,
	interpretation: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	snapshot = (
		dict(conversation_state_snapshot)
		if isinstance(conversation_state_snapshot, dict)
		else {}
	)

	def _state_bucket(name: str) -> Dict[str, Any]:
		value = snapshot.get(name)
		return dict(value) if isinstance(value, dict) else {}

	interpretation = dict(interpretation or {})
	return {
		"phrase_type": _clean_text(interpretation.get("phrase_type")),
		"target_hint": _clean_text(interpretation.get("target_hint")),
		"target_grain": _clean_text(interpretation.get("target_grain")),
		"target_focus_kind": _clean_text(interpretation.get("target_focus_kind")),
		"pending_clarification": _state_bucket("pending_clarification"),
		"active_sequence": _state_bucket("active_sequence"),
		"recent_focus": _state_bucket("recent_focus"),
		"resumable_prior_request": _state_bucket("resumable_prior_request"),
	}


def select_non_clarification_restore_owner(
	*,
	recent_focus: Dict[str, Any],
	resumable_prior_request: Dict[str, Any],
) -> Dict[str, str]:
	return _select_non_clarification_restore_owner_helper(
		has_recent_focus=bool((recent_focus or {}).get("available")),
		has_resumable_prior_request=bool((resumable_prior_request or {}).get("available")),
		recent_focus_precedence_basis=_peer_precedence_basis(recent_focus, resumable_prior_request),
		resumable_prior_precedence_basis=_peer_precedence_basis(resumable_prior_request, recent_focus),
	)


def select_latest_non_clarification_restore_state(
	*,
	phrase_type: str,
	pending_clarification: Dict[str, Any],
	active_sequence: Dict[str, Any],
	recent_focus: Dict[str, Any],
	resumable_prior_request: Dict[str, Any],
) -> Dict[str, Any]:
	pending_available = bool((pending_clarification or {}).get("available"))
	active_sequence_available = phrase_type == "question_restore" and bool((active_sequence or {}).get("active"))
	recent_focus_available = bool((recent_focus or {}).get("available"))
	resumable_available = bool((resumable_prior_request or {}).get("available"))
	active_sequence_beats_pending = active_sequence_available and _state_precedes_pending_clarification(
		active_sequence,
		pending_clarification,
	)
	recent_focus_beats_pending = recent_focus_available and _state_precedes_pending_clarification(
		recent_focus,
		pending_clarification,
	)
	resumable_beats_pending = resumable_available and _state_precedes_pending_clarification(
		resumable_prior_request,
		pending_clarification,
	)
	owner_selection = select_non_clarification_restore_owner(
		recent_focus=recent_focus if (recent_focus_available and (not pending_available or recent_focus_beats_pending)) else {},
		resumable_prior_request=(
			resumable_prior_request
			if (resumable_available and (not pending_available or resumable_beats_pending))
			else {}
		),
	)
	return _select_latest_non_clarification_restore_state_helper(
		phrase_type=_clean_text(phrase_type),
		has_pending_clarification=pending_available,
		has_active_sequence=active_sequence_available,
		has_recent_focus=recent_focus_available,
		has_resumable_prior_request=resumable_available,
		active_sequence_beats_pending=active_sequence_beats_pending,
		recent_focus_beats_pending=recent_focus_beats_pending,
		resumable_beats_pending=resumable_beats_pending,
		active_sequence_is_newer_than_pending=_state_is_newer(active_sequence, pending_clarification),
		recent_focus_is_newer_than_pending=_state_is_newer(recent_focus, pending_clarification),
		resumable_is_newer_than_pending=_state_is_newer(resumable_prior_request, pending_clarification),
		owner_selection_owner=_clean_text((owner_selection or {}).get("owner")),
		owner_selection_basis=_clean_text((owner_selection or {}).get("basis")),
	)


def build_prior_branch_restore_route_context(
	*,
	phrase_type: str,
	pending_clarification: Dict[str, Any],
	active_sequence: Dict[str, Any],
	recent_focus: Dict[str, Any],
	resumable_prior_request: Dict[str, Any],
	has_target_specifier: bool,
	recent_focus_matches_targeted_restore: bool,
	resumable_prior_request_matches_targeted_restore: bool,
) -> Dict[str, Any]:
	targeted_restore_selection = (
		_select_targeted_restore_owner_helper(
			has_target_specifier=bool(has_target_specifier),
			recent_focus_matches=bool(recent_focus_matches_targeted_restore),
			resumable_prior_request_matches=bool(resumable_prior_request_matches_targeted_restore),
		)
		if _clean_text(phrase_type) == "branch_restore"
		else {"owner": "", "basis": ""}
	)
	latest_non_clarification_selection = {"owner": "", "basis": ""}
	if _clean_text(phrase_type) in {"question_restore", "branch_restore"}:
		latest_non_clarification_selection = select_latest_non_clarification_restore_state(
			phrase_type=_clean_text(phrase_type),
			pending_clarification=pending_clarification,
			active_sequence=active_sequence,
			recent_focus=recent_focus,
			resumable_prior_request=resumable_prior_request,
		)
	return {
		"targeted_restore_selection": dict(targeted_restore_selection or {}),
		"latest_non_clarification_selection": dict(latest_non_clarification_selection or {}),
		"route_selector_inputs": build_prior_branch_restore_route_selector_inputs(
			phrase_type=_clean_text(phrase_type),
			targeted_restore_selection=targeted_restore_selection,
			latest_non_clarification_selection=latest_non_clarification_selection,
			has_target_specifier=bool(has_target_specifier),
			pending_clarification_is_authoritative=_pending_clarification_is_restore_authoritative(
				pending_clarification
			),
			has_active_sequence=bool((active_sequence or {}).get("active")),
			has_resumable_prior_request=bool((resumable_prior_request or {}).get("available")),
		),
	}


def build_latest_non_clarification_restore_owner_spec(
	*,
	owner: str,
	phrase_type: str,
	pending_available: bool,
	owner_is_newer_than_pending: bool,
	arbitration_basis: str,
	pending_clarification_source_tool_index: Any = None,
	active_sequence_source_tool_index: Any = None,
	recent_focus_source_tool_index: Any = None,
	resumable_prior_request_source_tool_index: Any = None,
	recent_focus_derivation_basis: str = "",
	resumable_snapshot_restore_mode: str = "",
	resumable_derivation_basis: str = "",
	resumable_accepted_recovery_action: str = "",
	resumable_prior_recovery_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	owner = _clean_text(owner)
	phrase_type = _clean_text(phrase_type)
	arbitration_basis = _clean_text(arbitration_basis)
	pending_available = bool(pending_available)
	owner_is_newer_than_pending = bool(owner_is_newer_than_pending)
	resumable_prior_recovery_payload = dict(resumable_prior_recovery_payload or {})
	if not owner:
		return {}
	if owner == "active_sequence":
		reason = (
			"The user asked to answer the most recent question, so the assistant is resuming "
			"the latest unresolved step in the active ordered multi-step sequence."
		)
		if pending_available:
			reason = (
				"The user asked to answer the most recent question, and the active ordered "
				"multi-step sequence is newer than the older pending clarification."
				if owner_is_newer_than_pending
				else "The user asked to answer the most recent question, and the active ordered "
				"multi-step sequence is taking ownership ahead of a non-authoritative fallback clarification."
			)
		return {
			"owner": owner,
			"reason": reason,
			"extra_internal_details": {
				"pending_clarification_source_tool_index": pending_clarification_source_tool_index,
				"active_sequence_source_tool_index": active_sequence_source_tool_index,
				"recent_focus_source_tool_index": recent_focus_source_tool_index,
				"resumable_prior_request_source_tool_index": resumable_prior_request_source_tool_index,
			},
		}
	if owner == "recent_focus":
		reason = (
			"The user asked to answer the most recent question, so the assistant is restoring "
			"the latest grounded business focus."
			if phrase_type == "question_restore"
			else "The user asked to go back, so the assistant is restoring the latest grounded business focus."
		)
		if pending_available:
			reason = (
				"The user asked to answer the most recent question, and the latest grounded "
				"business focus is newer than the older pending clarification."
				if phrase_type == "question_restore"
				else "The user asked to go back, so the assistant is restoring the latest grounded "
				"business focus instead of reopening an older pending branch."
			)
			if not owner_is_newer_than_pending:
				reason = (
					"The user asked to answer the most recent question, and the latest grounded "
					"business focus is taking ownership ahead of a non-authoritative fallback clarification."
					if phrase_type == "question_restore"
					else "The user asked to go back, so the assistant is restoring the latest grounded "
					"business focus instead of reopening a non-authoritative fallback clarification."
				)
		return {
			"owner": owner,
			"reason": reason,
			"internal_details": {
				"phrase_type": phrase_type,
				"arbitration_basis": arbitration_basis,
				"pending_clarification_source_tool_index": pending_clarification_source_tool_index,
				"recent_focus_source_tool_index": recent_focus_source_tool_index,
				"resumable_prior_request_source_tool_index": resumable_prior_request_source_tool_index,
				"derivation_basis": _clean_text(recent_focus_derivation_basis),
			},
		}
	if owner == "resumable_prior_request":
		reason = (
			"The user asked to answer the most recent question, so the assistant is restoring "
			"the latest resumable prior branch."
			if phrase_type == "question_restore"
			else "The user asked to go back, so the assistant is restoring the latest resumable prior branch."
		)
		if pending_available:
			reason = (
				"The user asked to answer the most recent question, so the assistant is restoring "
				"the latest resumable prior branch instead of reopening an older pending clarification."
				if phrase_type == "question_restore"
				else "The user asked to go back, so the assistant is restoring the latest resumable "
				"prior branch instead of reopening an older pending clarification."
			)
			if not owner_is_newer_than_pending:
				reason = (
					"The user asked to answer the most recent question, so the assistant is restoring "
					"the latest resumable prior branch instead of reopening a non-authoritative fallback clarification."
					if phrase_type == "question_restore"
					else "The user asked to go back, so the assistant is restoring the latest resumable "
					"prior branch instead of reopening a non-authoritative fallback clarification."
				)
		return {
			"owner": owner,
			"reason": reason,
			"internal_details": {
				"phrase_type": phrase_type,
				"snapshot_restore_mode": _clean_text(resumable_snapshot_restore_mode),
				"arbitration_basis": arbitration_basis,
				"derivation_basis": _clean_text(resumable_derivation_basis),
				"accepted_recovery_action": _clean_text(resumable_accepted_recovery_action),
				"pending_clarification_source_tool_index": pending_clarification_source_tool_index,
				"recent_focus_source_tool_index": recent_focus_source_tool_index,
				"resumable_prior_request_source_tool_index": resumable_prior_request_source_tool_index,
				"prior_recovery_payload": resumable_prior_recovery_payload,
			},
		}
	return {}


def build_direct_restore_fallback_owner_spec(
	*,
	owner: str,
	reason: str,
	arbitration_basis: str = "",
	internal_details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	owner = _clean_text(owner)
	if not owner:
		return {}
	spec = {
		"owner": owner,
		"reason": _clean_text(reason),
	}
	if owner == "active_sequence":
		spec["arbitration_basis"] = _clean_text(arbitration_basis)
		return spec
	if owner == "resumable_prior_request":
		spec["internal_details"] = dict(internal_details or {})
		return spec
	return {}


def build_recent_focus_restore_contract(
	*,
	request_id: str,
	recent_focus: Dict[str, Any],
	reason: str,
	confidence: float | None = None,
	internal_details: Dict[str, Any] | None = None,
	clear_current_pending_clarification: bool = False,
):
	if not isinstance(recent_focus, dict) or not bool(recent_focus.get("available")):
		return None
	resolved_confidence = float(
		max(
			0.0,
			min(
				1.0,
				confidence
				if confidence is not None
				else float((recent_focus or {}).get("confidence") or 0.0),
			),
		)
	)
	return _build_prior_branch_restore_contract(
		request_id=request_id,
		target_branch_kind="focus",
		target_branch_label=_clean_text((recent_focus or {}).get("focus_label")),
		target_request_id=_clean_text((recent_focus or {}).get("source_request_id")),
		target_family=_clean_text((recent_focus or {}).get("source_family")),
		target_scope={
			"focus_kind": _clean_text((recent_focus or {}).get("focus_kind")),
			"focus_grain": _clean_text((recent_focus or {}).get("focus_grain")),
			"focus_key": _clean_text((recent_focus or {}).get("focus_key")),
			"focus_label": _clean_text((recent_focus or {}).get("focus_label")),
			"source_capability": _clean_text((recent_focus or {}).get("source_capability")),
			"source_report": _clean_text((recent_focus or {}).get("source_report")),
			"deictic_allowed": bool((recent_focus or {}).get("deictic_allowed")),
			"explicit_named_allowed": bool((recent_focus or {}).get("explicit_named_allowed")),
		},
		restore_mode="restore_recent_focus",
		resumable=True,
		clear_current_pending_clarification=bool(clear_current_pending_clarification),
		preserve_time_context=True,
		preserve_scope=True,
		preserve_entity_dimension=True,
		reason=_clean_text(reason),
		confidence=resolved_confidence,
		internal_details=dict(internal_details or {}),
	)


def build_resumable_prior_request_restore_contract(
	*,
	request_id: str,
	resumable_prior_request: Dict[str, Any],
	reason: str,
	internal_details: Dict[str, Any] | None = None,
	clear_current_pending_clarification: bool = False,
):
	if not isinstance(resumable_prior_request, dict) or not bool(resumable_prior_request.get("available")):
		return None
	suggested_restore_mode = _clean_text((resumable_prior_request or {}).get("suggested_restore_mode"))
	restore_mode = {
		"requery_prior_branch": "replay_as_fresh_governed_query",
		"restore_recent_focus": "restore_recent_focus",
		"resume_active_sequence": "resume_active_sequence",
		"accept_prior_recovery_action": "accept_prior_recovery_action",
	}.get(suggested_restore_mode, "not_resumable")
	return _build_prior_branch_restore_contract(
		request_id=request_id,
		target_branch_kind=_clean_text((resumable_prior_request or {}).get("branch_kind")),
		target_branch_label=_clean_text((resumable_prior_request or {}).get("branch_label")),
		target_request_id=_clean_text((resumable_prior_request or {}).get("source_request_id")),
		target_family=_clean_text((resumable_prior_request or {}).get("target_family")),
		target_scope=dict((resumable_prior_request or {}).get("target_scope") or {}),
		restore_mode=restore_mode,
		resumable=bool((resumable_prior_request or {}).get("resumable")) and restore_mode != "not_resumable",
		clear_current_pending_clarification=bool(clear_current_pending_clarification),
		preserve_time_context=True,
		preserve_scope=True,
		preserve_entity_dimension=True,
		reason=_clean_text(reason),
		confidence=float((resumable_prior_request or {}).get("confidence") or 0.0),
		internal_details=dict(internal_details or {}),
	)


def build_active_sequence_restore_contract(
	*,
	request_id: str,
	active_sequence: Dict[str, Any],
	phrase_type: str,
	reason: str,
	clear_current_pending_clarification: bool = False,
	arbitration_basis: str = "",
	extra_internal_details: Dict[str, Any] | None = None,
):
	if not bool((active_sequence or {}).get("active")):
		return None
	internal_details = {
		"phrase_type": _clean_text(phrase_type),
		"sequence_status": _clean_text((active_sequence or {}).get("status")),
	}
	if arbitration_basis:
		internal_details["arbitration_basis"] = _clean_text(arbitration_basis)
	if isinstance(extra_internal_details, dict) and extra_internal_details:
		internal_details.update(extra_internal_details)
	return _build_prior_branch_restore_contract(
		request_id=request_id,
		target_branch_kind="sequence",
		target_branch_label=_clean_text((active_sequence or {}).get("primary_segment_message")),
		target_request_id=_clean_text((active_sequence or {}).get("request_id")),
		target_family="active_sequence",
		restore_mode="resume_active_sequence",
		resumable=True,
		clear_current_pending_clarification=bool(clear_current_pending_clarification),
		clear_current_active_sequence=False,
		preserve_time_context=True,
		preserve_scope=True,
		preserve_entity_dimension=True,
		reason=_clean_text(reason),
		confidence=0.93,
		internal_details=internal_details,
	)


def build_latest_non_clarification_restore_contract(
	*,
	request_id: str,
	phrase_type: str,
	pending_clarification: Dict[str, Any],
	active_sequence: Dict[str, Any],
	recent_focus: Dict[str, Any],
	resumable_prior_request: Dict[str, Any],
):
	restore_selection = select_latest_non_clarification_restore_state(
		phrase_type=phrase_type,
		pending_clarification=pending_clarification,
		active_sequence=active_sequence,
		recent_focus=recent_focus,
		resumable_prior_request=resumable_prior_request,
	)
	owner = _clean_text((restore_selection or {}).get("owner"))
	arbitration_basis = _clean_text((restore_selection or {}).get("basis"))
	pending_available = bool((pending_clarification or {}).get("available"))
	clear_pending_clarification = bool((restore_selection or {}).get("clear_pending_clarification"))
	if not owner:
		return None
	owner_spec = build_latest_non_clarification_restore_owner_spec(
		owner=owner,
		phrase_type=phrase_type,
		pending_available=pending_available,
		owner_is_newer_than_pending=(
			_state_is_newer(active_sequence, pending_clarification)
			if owner == "active_sequence"
			else _state_is_newer(recent_focus, pending_clarification)
			if owner == "recent_focus"
			else _state_is_newer(resumable_prior_request, pending_clarification)
			if owner == "resumable_prior_request"
			else False
		),
		arbitration_basis=arbitration_basis,
		pending_clarification_source_tool_index=_source_tool_index(pending_clarification),
		active_sequence_source_tool_index=_source_tool_index(active_sequence),
		recent_focus_source_tool_index=_source_tool_index(recent_focus),
		resumable_prior_request_source_tool_index=_source_tool_index(resumable_prior_request),
		recent_focus_derivation_basis=_clean_text((recent_focus or {}).get("derivation_basis")),
		resumable_snapshot_restore_mode=_clean_text((resumable_prior_request or {}).get("suggested_restore_mode")),
		resumable_derivation_basis=_clean_text((resumable_prior_request or {}).get("derivation_basis")),
		resumable_accepted_recovery_action=_clean_text((resumable_prior_request or {}).get("accepted_recovery_action")),
		resumable_prior_recovery_payload=dict(
			((resumable_prior_request or {}).get("internal_details") or {}).get("prior_recovery_payload") or {}
		),
	)
	if owner == "active_sequence":
		return build_active_sequence_restore_contract(
			request_id=request_id,
			active_sequence=active_sequence,
			phrase_type=phrase_type,
			reason=_clean_text((owner_spec or {}).get("reason")),
			clear_current_pending_clarification=clear_pending_clarification,
			arbitration_basis=arbitration_basis,
			extra_internal_details=dict((owner_spec or {}).get("extra_internal_details") or {}),
		)
	if owner == "recent_focus":
		return build_recent_focus_restore_contract(
			request_id=request_id,
			recent_focus=recent_focus,
			reason=_clean_text((owner_spec or {}).get("reason")),
			clear_current_pending_clarification=clear_pending_clarification,
			internal_details=dict((owner_spec or {}).get("internal_details") or {}),
		)
	if owner == "resumable_prior_request":
		return build_resumable_prior_request_restore_contract(
			request_id=request_id,
			resumable_prior_request=resumable_prior_request,
			reason=_clean_text((owner_spec or {}).get("reason")),
			clear_current_pending_clarification=clear_pending_clarification,
			internal_details=dict((owner_spec or {}).get("internal_details") or {}),
		)
	return None


def build_authoritative_pending_clarification_restore_contract(
	*,
	request_id: str,
	phrase_type: str,
	pending_clarification: Dict[str, Any],
):
	signal = dict((pending_clarification or {}).get("signal") or {})
	spec = _select_authoritative_pending_clarification_restore_spec_helper(
		phrase_type=phrase_type,
		has_authoritative_pending_clarification=pending_clarification_is_restore_authoritative(pending_clarification),
		user_question=_clean_text(signal.get("user_question")),
		request_id=_clean_text(signal.get("request_id")),
		continuation_lane=_clean_text((pending_clarification or {}).get("continuation_lane")),
	)
	if not spec:
		return None
	return _build_prior_branch_restore_contract(request_id=request_id, **spec)


def build_direct_restore_fallback_contract(
	*,
	request_id: str,
	phrase_type: str,
	active_sequence: Dict[str, Any],
	resumable_prior_request: Dict[str, Any],
):
	spec = _select_direct_restore_fallback_spec_helper(
		phrase_type=phrase_type,
		has_active_sequence=bool((active_sequence or {}).get("active")),
		has_resumable_prior_request=bool((resumable_prior_request or {}).get("available")),
		resumable_suggested_restore_mode=_clean_text((resumable_prior_request or {}).get("suggested_restore_mode")),
		resumable_derivation_basis=_clean_text((resumable_prior_request or {}).get("derivation_basis")),
		resumable_accepted_recovery_action=_clean_text((resumable_prior_request or {}).get("accepted_recovery_action")),
		resumable_prior_recovery_payload=dict(
			((resumable_prior_request or {}).get("internal_details") or {}).get("prior_recovery_payload") or {}
		),
	)
	if not spec:
		return None
	owner = _clean_text(spec.get("owner"))
	owner_spec = build_direct_restore_fallback_owner_spec(
		owner=owner,
		reason=_clean_text(spec.get("reason")),
		arbitration_basis=_clean_text(spec.get("arbitration_basis")),
		internal_details=dict(spec.get("internal_details") or {}),
	)
	if owner == "active_sequence":
		return build_active_sequence_restore_contract(
			request_id=request_id,
			active_sequence=active_sequence,
			phrase_type=phrase_type,
			reason=_clean_text((owner_spec or {}).get("reason")),
			arbitration_basis=_clean_text((owner_spec or {}).get("arbitration_basis")),
		)
	if owner == "resumable_prior_request":
		return build_resumable_prior_request_restore_contract(
			request_id=request_id,
			resumable_prior_request=resumable_prior_request,
			reason=_clean_text((owner_spec or {}).get("reason")),
			internal_details=dict((owner_spec or {}).get("internal_details") or {}),
		)
	return None


def select_prior_branch_restore_route(
	*,
	phrase_type: str,
	pending_clarification: Dict[str, Any],
	active_sequence: Dict[str, Any],
	recent_focus: Dict[str, Any],
	resumable_prior_request: Dict[str, Any],
	target_hint: str,
	target_grain: str,
	target_focus_kind: str,
) -> Dict[str, Any]:
	route_context = build_prior_branch_restore_route_context(
		phrase_type=phrase_type,
		pending_clarification=pending_clarification,
		active_sequence=active_sequence,
		recent_focus=recent_focus,
		resumable_prior_request=resumable_prior_request,
		has_target_specifier=bool(target_hint or target_grain or target_focus_kind),
		recent_focus_matches_targeted_restore=recent_focus_matches_targeted_restore(
			recent_focus,
			target_hint=target_hint,
			target_grain=target_grain,
			target_focus_kind=target_focus_kind,
		),
		resumable_prior_request_matches_targeted_restore=resumable_prior_request_matches_targeted_restore(
			resumable_prior_request,
			target_hint=target_hint,
			target_grain=target_grain,
			target_focus_kind=target_focus_kind,
		),
	)
	route_selector_inputs = dict((route_context or {}).get("route_selector_inputs") or {})
	return _select_prior_branch_restore_route_helper(**route_selector_inputs)


def build_prior_branch_restore_contract_from_snapshot(
	*,
	request_id: str,
	raw_message: str,
	conversation_state_snapshot: Dict[str, Any],
	control_evidence_payload: Dict[str, Any] | None = None,
):
	control_phrase_type = prior_branch_phrase_type_from_control_action(control_evidence_payload)
	message_phrase_type = prior_branch_restore_phrase_type(raw_message)
	control_target_hint, control_target_grain, control_target_focus_kind = targeted_restore_hint_from_control_evidence(control_evidence_payload)
	message_target_hint, message_target_grain, message_target_focus_kind = targeted_restore_hint_from_message(raw_message)
	interpretation = _select_prior_branch_restore_request_interpretation_helper(
		control_phrase_type=control_phrase_type,
		message_phrase_type=message_phrase_type,
		control_target_hint=control_target_hint,
		control_target_grain=control_target_grain,
		control_target_focus_kind=control_target_focus_kind,
		message_target_hint=message_target_hint,
		message_target_grain=message_target_grain,
		message_target_focus_kind=message_target_focus_kind,
	)
	restore_snapshot_context = build_prior_branch_restore_snapshot_context(
		conversation_state_snapshot=conversation_state_snapshot,
		interpretation=interpretation,
	)
	phrase_type = _clean_text((restore_snapshot_context or {}).get("phrase_type"))
	if not phrase_type:
		return None
	pending_clarification = dict((restore_snapshot_context or {}).get("pending_clarification") or {})
	active_sequence = dict((restore_snapshot_context or {}).get("active_sequence") or {})
	recent_focus = dict((restore_snapshot_context or {}).get("recent_focus") or {})
	resumable_prior_request = dict((restore_snapshot_context or {}).get("resumable_prior_request") or {})
	target_hint = _clean_text((restore_snapshot_context or {}).get("target_hint"))
	target_grain = _clean_text((restore_snapshot_context or {}).get("target_grain"))
	target_focus_kind = _clean_text((restore_snapshot_context or {}).get("target_focus_kind"))
	restore_route_selection = select_prior_branch_restore_route(
		phrase_type=phrase_type,
		pending_clarification=pending_clarification,
		active_sequence=active_sequence,
		recent_focus=recent_focus,
		resumable_prior_request=resumable_prior_request,
		target_hint=target_hint,
		target_grain=target_grain,
		target_focus_kind=target_focus_kind,
	)
	restore_route = _clean_text((restore_route_selection or {}).get("route"))
	restore_basis = _clean_text((restore_route_selection or {}).get("basis"))
	targeted_restore_owner_spec = build_targeted_restore_owner_spec(
		restore_route=restore_route,
		phrase_type=phrase_type,
		target_hint=target_hint,
		target_grain=target_grain,
		target_focus_kind=target_focus_kind,
		restore_basis=restore_basis,
		clear_pending_clarification=bool((pending_clarification or {}).get("available")),
		recent_focus_derivation_basis=_clean_text((recent_focus or {}).get("derivation_basis")),
		resumable_suggested_restore_mode=_clean_text((resumable_prior_request or {}).get("suggested_restore_mode")),
		resumable_derivation_basis=_clean_text((resumable_prior_request or {}).get("derivation_basis")),
		resumable_accepted_recovery_action=_clean_text((resumable_prior_request or {}).get("accepted_recovery_action")),
		resumable_prior_recovery_payload=dict(
			((resumable_prior_request or {}).get("internal_details") or {}).get("prior_recovery_payload") or {}
		),
	)
	if restore_route == "targeted_recent_focus":
		return build_recent_focus_restore_contract(
			request_id=request_id,
			recent_focus=recent_focus,
			reason=_clean_text((targeted_restore_owner_spec or {}).get("reason")),
			clear_current_pending_clarification=bool(
				(targeted_restore_owner_spec or {}).get("clear_current_pending_clarification")
			),
			internal_details=dict((targeted_restore_owner_spec or {}).get("internal_details") or {}),
		)
	if restore_route == "targeted_resumable_prior_request":
		return build_resumable_prior_request_restore_contract(
			request_id=request_id,
			resumable_prior_request=resumable_prior_request,
			reason=_clean_text((targeted_restore_owner_spec or {}).get("reason")),
			clear_current_pending_clarification=bool(
				(targeted_restore_owner_spec or {}).get("clear_current_pending_clarification")
			),
			internal_details=dict((targeted_restore_owner_spec or {}).get("internal_details") or {}),
		)
	if restore_route == "targeted_no_match_block":
		return None
	if restore_route == "latest_non_clarification":
		return build_latest_non_clarification_restore_contract(
			request_id=request_id,
			phrase_type=phrase_type,
			pending_clarification=pending_clarification,
			active_sequence=active_sequence,
			recent_focus=recent_focus,
			resumable_prior_request=resumable_prior_request,
		)
	if restore_route == "authoritative_pending_clarification":
		return build_authoritative_pending_clarification_restore_contract(
			request_id=request_id,
			phrase_type=phrase_type,
			pending_clarification=pending_clarification,
		)
	if restore_route == "direct_restore_fallback":
		return build_direct_restore_fallback_contract(
			request_id=request_id,
			phrase_type=phrase_type,
			active_sequence=active_sequence,
			resumable_prior_request=resumable_prior_request,
		)
	return None


def build_prior_branch_restore_route_selector_inputs(
	*,
	phrase_type: str,
	targeted_restore_selection: Dict[str, Any] | None = None,
	latest_non_clarification_selection: Dict[str, Any] | None = None,
	has_target_specifier: bool,
	pending_clarification_is_authoritative: bool,
	has_active_sequence: bool,
	has_resumable_prior_request: bool,
) -> Dict[str, Any]:
	targeted_restore_selection = dict(targeted_restore_selection or {})
	latest_non_clarification_selection = dict(latest_non_clarification_selection or {})
	return {
		"phrase_type": _clean_text(phrase_type),
		"targeted_restore_owner": _clean_text(targeted_restore_selection.get("owner")),
		"targeted_restore_basis": _clean_text(targeted_restore_selection.get("basis")),
		"has_target_specifier": bool(has_target_specifier),
		"latest_non_clarification_owner": _clean_text(latest_non_clarification_selection.get("owner")),
		"latest_non_clarification_basis": _clean_text(latest_non_clarification_selection.get("basis")),
		"pending_clarification_is_authoritative": bool(pending_clarification_is_authoritative),
		"has_active_sequence": bool(has_active_sequence),
		"has_resumable_prior_request": bool(has_resumable_prior_request),
	}


def build_targeted_restore_owner_spec(
	*,
	restore_route: str,
	phrase_type: str,
	target_hint: str,
	target_grain: str,
	target_focus_kind: str,
	restore_basis: str,
	clear_pending_clarification: bool,
	recent_focus_derivation_basis: str = "",
	resumable_suggested_restore_mode: str = "",
	resumable_derivation_basis: str = "",
	resumable_accepted_recovery_action: str = "",
	resumable_prior_recovery_payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	restore_route = _clean_text(restore_route)
	if restore_route == "targeted_recent_focus":
		spec = _select_targeted_recent_focus_restore_spec_helper(
			phrase_type=_clean_text(phrase_type),
			target_hint=_clean_text(target_hint),
			target_grain=_clean_text(target_grain),
			target_focus_kind=_clean_text(target_focus_kind),
			restore_basis=_clean_text(restore_basis),
			clear_pending_clarification=bool(clear_pending_clarification),
			recent_focus_derivation_basis=_clean_text(recent_focus_derivation_basis),
		)
		return {
			"owner": "recent_focus",
			"reason": _clean_text((spec or {}).get("reason")),
			"clear_current_pending_clarification": bool((spec or {}).get("clear_current_pending_clarification")),
			"internal_details": dict((spec or {}).get("internal_details") or {}),
		}
	if restore_route == "targeted_resumable_prior_request":
		spec = _select_targeted_resumable_prior_request_restore_spec_helper(
			phrase_type=_clean_text(phrase_type),
			target_hint=_clean_text(target_hint),
			target_grain=_clean_text(target_grain),
			target_focus_kind=_clean_text(target_focus_kind),
			restore_basis=_clean_text(restore_basis),
			clear_pending_clarification=bool(clear_pending_clarification),
			resumable_suggested_restore_mode=_clean_text(resumable_suggested_restore_mode),
			resumable_derivation_basis=_clean_text(resumable_derivation_basis),
			resumable_accepted_recovery_action=_clean_text(resumable_accepted_recovery_action),
			resumable_prior_recovery_payload=dict(resumable_prior_recovery_payload or {}),
		)
		return {
			"owner": "resumable_prior_request",
			"reason": _clean_text((spec or {}).get("reason")),
			"clear_current_pending_clarification": bool((spec or {}).get("clear_current_pending_clarification")),
			"internal_details": dict((spec or {}).get("internal_details") or {}),
		}
	return {}
