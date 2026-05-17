from __future__ import annotations

from typing import Any, Dict

from ai_assistant_ui.qwen_chat.governed_scope_registry import listing_view_display_label
from ai_assistant_ui.qwen_chat.master_data_family_support import is_master_data_listing_family
from ai_assistant_ui.qwen_chat.metadata import entity_grain_display_label


_CURRENT_PENDING_CLARIFICATION_OVERRIDE_ACTIONS = {
	"resume_active_sequence",
	"cancel_active_sequence",
	"restore_recent_focus",
	"replay_as_fresh_governed_query",
	"accept_prior_recovery_action",
}

_ACTIVE_SEQUENCE_SHARED_OVERRIDE_ACTIONS = {
	"restore_recent_focus",
	"replay_as_fresh_governed_query",
	"accept_prior_recovery_action",
}

_ACTIVE_SEQUENCE_NON_OVERRIDING_FRONTDOOR_INTENT_CLASSES = {
	"",
	"low_signal_non_business",
	"greeting",
	"thanks",
	"acknowledgement",
	"closure_signoff",
	"capability_question",
	"session_flow",
}


def decision_action(decision_contract) -> str:
	if decision_contract is None:
		return ""
	return str(getattr(decision_contract, "decision_action", "") or "").strip()


def select_prior_branch_restore_decision_state(*, prior_branch_restore_action: str) -> Dict[str, str]:
	action = str(prior_branch_restore_action or "").strip()
	if not action:
		return {"owner": "", "basis": "", "action": "", "kind": ""}
	if action == "reopen_pending_clarification":
		return {
			"owner": "",
			"basis": "",
			"action": action,
			"kind": "reopen_pending_clarification",
		}
	if action == "resume_active_sequence":
		return {
			"owner": "prior_branch_restore_decision",
			"basis": "prior_branch_resume_active_sequence",
			"action": action,
			"kind": "resume_active_sequence",
		}
	return {
		"owner": "prior_branch_restore_decision",
		"basis": "prior_branch_restore_override",
		"action": action,
		"kind": "non_clarification_override",
	}


def select_initial_control_override_owner(
	*,
	prior_branch_state: Dict[str, str],
	control_action: str,
) -> Dict[str, str]:
	if str((prior_branch_state or {}).get("kind") or "").strip() == "non_clarification_override":
		return {
			"owner": str((prior_branch_state or {}).get("owner") or "").strip(),
			"basis": str((prior_branch_state or {}).get("basis") or "").strip(),
		}
	if str(control_action or "").strip() == "resume_active_sequence":
		return {"owner": "control_action", "basis": "resume_active_sequence_override"}
	return {"owner": "", "basis": ""}


def select_pending_clarification_override_owner(
	*,
	current_decision_action: str,
	prior_branch_state: Dict[str, str],
) -> Dict[str, str]:
	action = str(current_decision_action or "").strip()
	if action in _CURRENT_PENDING_CLARIFICATION_OVERRIDE_ACTIONS:
		return {
			"owner": "conversation_control_decision",
			"basis": f"current_control_{action}",
		}
	if str((prior_branch_state or {}).get("kind") or "").strip() == "non_clarification_override":
		return {
			"owner": str((prior_branch_state or {}).get("owner") or "").strip(),
			"basis": str((prior_branch_state or {}).get("basis") or "").strip(),
		}
	return {"owner": "", "basis": ""}


def clarification_decision_allows_immediate_control_override(*, clarification_decision: str) -> bool:
	decision = str(clarification_decision or "").strip()
	return decision not in {
		"resolved_option",
		"show_options",
		"abandon_current_branch",
		"meta_question",
		"empty_ack",
		"reask_pending_clarification",
	}


def pending_clarification_response_should_preempt_runtime(*, clarification_decision: str) -> bool:
	decision = str(clarification_decision or "").strip()
	if not decision:
		return False
	return not clarification_decision_allows_immediate_control_override(
		clarification_decision=decision,
	)


def clarification_response_should_yield_initial_control_decision(
	*,
	clarification_decision: str,
	prior_branch_state: Dict[str, str],
	control_action: str,
) -> bool:
	selection = select_initial_control_override_owner(
		prior_branch_state=prior_branch_state,
		control_action=control_action,
	)
	if not str(selection.get("owner") or "").strip():
		return False
	decision = str(clarification_decision or "").strip()
	if not decision:
		return True
	if decision == "reask_pending_clarification":
		return str(selection.get("basis") or "").strip() != "current_control_replay_as_fresh_governed_query"
	return clarification_decision_allows_immediate_control_override(
		clarification_decision=decision,
	)


def pending_clarification_should_yield_to_current_control_decision(
	*,
	clarification_decision: str,
	current_decision_action: str,
	prior_branch_state: Dict[str, str],
) -> bool:
	selection = select_pending_clarification_override_owner(
		current_decision_action=current_decision_action,
		prior_branch_state=prior_branch_state,
	)
	if not str(selection.get("owner") or "").strip():
		return False
	decision = str(clarification_decision or "").strip()
	if not decision:
		return True
	if decision == "reask_pending_clarification":
		return str(selection.get("basis") or "").strip() != "current_control_replay_as_fresh_governed_query"
	return clarification_decision_allows_immediate_control_override(
		clarification_decision=decision,
	)


def clarification_response_decision_spec(
	*,
	decision: str,
	raw_message: str,
	resolved_runtime_message: str,
	override_business_message: str,
) -> Dict[str, Any]:
	decision_value = str(decision or "").strip()
	runtime_message = str(resolved_runtime_message or "").strip()
	override_message = str(override_business_message or "").strip()
	raw_message_value = str(raw_message or "").strip()
	if not decision_value:
		return {}
	if decision_value == "resolved_option":
		return {
			"decision_class": "clarification_resolution",
			"decision_action": "resolve_pending_clarification",
			"resolved_business_message": runtime_message,
			"clear_pending_clarification": True,
			"internal_details_patch": {},
		}
	if decision_value == "show_options":
		return {
			"decision_class": "option_list_request",
			"decision_action": "show_pending_options",
			"resolved_business_message": "",
			"clear_pending_clarification": False,
			"internal_details_patch": {},
		}
	if decision_value == "new_request":
		return {
			"decision_class": "fresh_request_override",
			"decision_action": "override_with_new_request",
			"resolved_business_message": override_message or raw_message_value,
			"clear_pending_clarification": True,
			"internal_details_patch": {
				"override_business_message": override_message,
			},
		}
	if decision_value == "abandon_current_branch":
		return {
			"decision_class": "branch_discard",
			"decision_action": "abandon_current_branch",
			"resolved_business_message": "Okay, I'll leave that aside. Ask me a new ERP question whenever you're ready.",
			"clear_pending_clarification": True,
			"internal_details_patch": {},
		}
	if decision_value == "meta_question":
		return {
			"decision_class": "meta_question",
			"decision_action": "answer_pending_clarification_meta_question",
			"resolved_business_message": "",
			"clear_pending_clarification": False,
			"internal_details_patch": {},
		}
	if decision_value == "empty_ack":
		return {
			"decision_class": "clarification_acknowledgement",
			"decision_action": "repeat_pending_clarification",
			"resolved_business_message": "",
			"clear_pending_clarification": False,
			"internal_details_patch": {},
		}
	if decision_value == "reask_pending_clarification":
		return {
			"decision_class": "clarification_reask",
			"decision_action": "reask_pending_clarification",
			"resolved_business_message": "",
			"clear_pending_clarification": False,
			"internal_details_patch": {},
		}
	return {
		"decision_class": "clarification_other",
		"decision_action": decision_value,
		"resolved_business_message": "",
		"clear_pending_clarification": False,
		"internal_details_patch": {},
	}


def clarification_response_resolved_slot_payload(clarification_response_contract) -> Dict[str, Any]:
	if clarification_response_contract is None:
		return {}
	resolved_slot = getattr(clarification_response_contract, "resolved_slot", None)
	return dict(resolved_slot) if isinstance(resolved_slot, dict) else {}


def resolved_clarification_runtime_message(
	*,
	raw_message: str,
	pending_clarification_signal: Dict[str, Any],
	clarification_decision: str,
	resolved_option: str,
) -> str:
	decision = str(clarification_decision or "").strip()
	if decision == "new_request":
		return str(raw_message or "").strip()
	if decision != "resolved_option":
		return ""
	from ai_assistant_ui.qwen_chat.clarification_resolution import (
		clarification_resolved_continuation_message,
	)
	return clarification_resolved_continuation_message(
		signal_payload=pending_clarification_signal,
		resolved_option=str(resolved_option or "").strip(),
	)


def frontdoor_clarification_reentry_message(
	*,
	raw_message: str,
	clarification_lane: str,
	clarification_decision: str,
	clarified_runtime_message: str,
	resolved_slot_payload: Dict[str, Any] | None,
) -> str:
	clean_runtime_message = str(clarified_runtime_message or "").strip()
	if clean_runtime_message:
		return clean_runtime_message
	if str(clarification_lane or "").strip() != "front_door":
		return ""
	if str(clarification_decision or "").strip() != "resolved_option":
		return ""
	if not isinstance(resolved_slot_payload, dict) or not resolved_slot_payload:
		return ""
	return str(raw_message or "").strip()


def artifact_boundary_clarification_requires_runtime_reset(
	*,
	clarification_lane: str,
	clarification_decision: str,
	clarified_runtime_message: str,
) -> bool:
	if str(clarification_lane or "").strip() != "artifact_boundary":
		return False
	if str(clarification_decision or "").strip() != "resolved_option":
		return False
	return bool(str(clarified_runtime_message or "").strip())


def frontdoor_clarification_requires_fresh_query_reset(
	*,
	clarification_lane: str,
	clarification_decision: str,
	clarified_runtime_message: str,
	resolved_slot_payload: Dict[str, Any] | None,
) -> bool:
	if str(clarification_lane or "").strip() != "front_door":
		return False
	if str(clarification_decision or "").strip() != "resolved_option":
		return False
	return bool(
		str(clarified_runtime_message or "").strip()
		or (isinstance(resolved_slot_payload, dict) and bool(resolved_slot_payload))
	)


def select_active_sequence_completion_owner(
	*,
	current_decision_action: str,
	prior_branch_state: Dict[str, str],
) -> Dict[str, str]:
	if str(current_decision_action or "").strip() == "resume_active_sequence":
		return {
			"owner": "conversation_control_decision",
			"basis": "current_control_resume_active_sequence",
		}
	if str((prior_branch_state or {}).get("kind") or "").strip() == "resume_active_sequence":
		return {
			"owner": str((prior_branch_state or {}).get("owner") or "").strip(),
			"basis": str((prior_branch_state or {}).get("basis") or "").strip(),
		}
	return {"owner": "", "basis": ""}


def select_active_sequence_superseding_owner(
	*,
	has_latest_active_sequence: bool,
	has_current_active_sequence: bool,
	control_action: str,
	current_decision_action: str,
	prior_branch_state: Dict[str, str],
	has_raw_message: bool,
	frontdoor_intent_class: str,
) -> Dict[str, str]:
	if not has_latest_active_sequence or has_current_active_sequence:
		return {"owner": "", "basis": ""}
	control_action = str(control_action or "").strip()
	if control_action in {"resume_active_sequence", "stop_active_sequence"}:
		return {"owner": "", "basis": ""}
	current_decision_action = str(current_decision_action or "").strip()
	if current_decision_action in {"resume_active_sequence", "cancel_active_sequence"}:
		return {"owner": "", "basis": ""}
	if str((prior_branch_state or {}).get("kind") or "").strip() == "resume_active_sequence":
		return {"owner": "", "basis": ""}
	if control_action == "override_with_new_request":
		return {"owner": "control_action", "basis": "explicit_new_request_override"}
	if current_decision_action in _ACTIVE_SEQUENCE_SHARED_OVERRIDE_ACTIONS:
		return {"owner": "conversation_control_decision", "basis": "shared_owner_override"}
	if str((prior_branch_state or {}).get("kind") or "").strip() == "non_clarification_override":
		return {"owner": "prior_branch_restore_decision", "basis": "prior_branch_override"}
	if not has_raw_message:
		return {"owner": "", "basis": ""}
	if str(frontdoor_intent_class or "").strip() in _ACTIVE_SEQUENCE_NON_OVERRIDING_FRONTDOOR_INTENT_CLASSES:
		return {"owner": "", "basis": ""}
	return {"owner": "frontdoor_intent", "basis": "substantive_new_request"}


def select_compound_completion_reentry_action(*, sequence_status: str) -> Dict[str, str]:
	status = str(sequence_status or "").strip()
	if status == "ordered_execution_complete":
		return {
			"status": status,
			"action": "acknowledge_completed_sequence",
			"basis": "ordered_execution_complete",
		}
	if status == "ordered_execution_cancelled":
		return {
			"status": status,
			"action": "acknowledge_cancelled_sequence",
			"basis": "ordered_execution_cancelled",
		}
	return {"status": status, "action": "", "basis": ""}


def select_compound_completion_reentry_eligibility(
	*,
	has_completion_answer: bool,
	is_continuation_control: bool,
	has_decision_action: bool,
) -> Dict[str, str]:
	if not has_completion_answer:
		return {"action": "block", "basis": "missing_completion_answer"}
	if not is_continuation_control:
		return {"action": "block", "basis": "not_continuation_control"}
	if not has_decision_action:
		return {"action": "block", "basis": "unsupported_completion_status"}
	return {"action": "allow", "basis": "compound_completion_reentry"}


def select_compound_continuation_eligibility(
	*,
	has_runtime_message: bool,
	is_continuation_control: bool,
	has_active_sequence: bool,
) -> Dict[str, str]:
	if not has_runtime_message:
		return {"action": "block", "basis": "missing_runtime_message"}
	if not is_continuation_control:
		return {"action": "block", "basis": "not_continuation_control"}
	if not has_active_sequence:
		return {"action": "block", "basis": "active_sequence_unavailable"}
	return {"action": "allow", "basis": "active_sequence_continuation"}


def select_compound_cancellation_sequence_source(
	*,
	has_cancelled_sequence_payload: bool,
	has_active_sequence_payload: bool,
) -> Dict[str, str]:
	if has_cancelled_sequence_payload:
		return {"owner": "cancelled_sequence_payload", "basis": "cancelled_sequence_payload_available"}
	if has_active_sequence_payload:
		return {"owner": "active_sequence_payload", "basis": "active_sequence_payload_fallback"}
	return {"owner": "", "basis": ""}


def _source_tool_index(state: Dict[str, Any] | None) -> int:
	if not isinstance(state, dict):
		return -1
	value = state.get("source_tool_index")
	try:
		return int(value)
	except (TypeError, ValueError):
		return -1


def _state_is_newer(candidate_state: Dict[str, Any] | None, baseline_state: Dict[str, Any] | None) -> bool:
	candidate_index = _source_tool_index(candidate_state)
	baseline_index = _source_tool_index(baseline_state)
	if candidate_index < 0 or baseline_index < 0:
		return False
	return candidate_index > baseline_index


def _pending_clarification_is_non_authoritative_fallback(pending_clarification: Dict[str, Any] | None) -> bool:
	if not isinstance(pending_clarification, dict):
		return False
	if not bool(pending_clarification.get("available")):
		return False
	if _source_tool_index(pending_clarification) >= 0:
		return False
	return str(pending_clarification.get("source_kind") or "").strip() == "message_fallback"


def select_compound_request_completion_superseding_state(
	*,
	active_sequence_state: Dict[str, Any],
	pending_clarification_state: Dict[str, Any],
	recent_focus_state: Dict[str, Any],
	resumable_prior_request_state: Dict[str, Any],
) -> Dict[str, str]:
	if not isinstance(active_sequence_state, dict) or not active_sequence_state:
		return {"owner": "", "basis": ""}
	status = str(active_sequence_state.get("status") or "").strip()
	if status not in {"ordered_execution_complete", "ordered_execution_cancelled"}:
		return {"owner": "", "basis": ""}
	if _source_tool_index(active_sequence_state) < 0:
		return {"owner": "", "basis": ""}
	pending_supersedes = bool((pending_clarification_state or {}).get("available")) and not _pending_clarification_is_non_authoritative_fallback(pending_clarification_state) and _state_is_newer(pending_clarification_state, active_sequence_state)
	if pending_supersedes:
		return {
			"owner": "pending_clarification",
			"basis": "pending_clarification_precedes_completed_sequence_by_newer_index",
		}
	for owner, competing_state in [
		("recent_focus", recent_focus_state),
		("resumable_prior_request", resumable_prior_request_state),
	]:
		if not isinstance(competing_state, dict):
			continue
		if not (bool(competing_state.get("available")) or bool(competing_state.get("active"))):
			continue
		if _state_is_newer(competing_state, active_sequence_state):
			return {
				"owner": owner,
				"basis": f"{owner}_precedes_completed_sequence_by_newer_index",
			}
	return {"owner": "", "basis": ""}


def select_recent_focus_continuation_eligibility(
	*,
	has_runtime_message: bool,
	runtime_matches_raw_without_passthrough: bool,
	has_strong_control_owner: bool,
	has_recent_focus: bool,
	has_followup_resolution: bool,
	followup_mode: str,
	depends_on_grounded_turn: bool,
	allow_passthrough: bool,
) -> Dict[str, object]:
	if not has_runtime_message:
		return {"action": "block", "basis": "missing_runtime_message", "allow_passthrough": False}
	if runtime_matches_raw_without_passthrough:
		return {"action": "block", "basis": "runtime_matches_raw_without_passthrough", "allow_passthrough": False}
	if has_strong_control_owner:
		return {"action": "block", "basis": "strong_control_owner", "allow_passthrough": allow_passthrough}
	if not has_recent_focus:
		return {"action": "block", "basis": "recent_focus_unavailable", "allow_passthrough": allow_passthrough}
	if not has_followup_resolution:
		return {"action": "block", "basis": "missing_followup_resolution", "allow_passthrough": allow_passthrough}
	if str(followup_mode or "").strip() != "new_query":
		return {"action": "block", "basis": "followup_mode_not_new_query", "allow_passthrough": allow_passthrough}
	if not depends_on_grounded_turn:
		return {"action": "block", "basis": "followup_not_grounded", "allow_passthrough": allow_passthrough}
	return {
		"action": "allow",
		"basis": "shared_affordance_passthrough" if allow_passthrough else "local_transform_grounded_followup",
		"allow_passthrough": allow_passthrough,
	}


def select_active_sequence_completion_source_owner(
	*,
	has_current_active_sequence: bool,
	has_latest_active_sequence: bool,
) -> Dict[str, str]:
	if has_current_active_sequence:
		return {"owner": "current_active_sequence", "basis": "current_active_sequence_available"}
	if has_latest_active_sequence:
		return {"owner": "latest_active_sequence", "basis": "latest_active_sequence_fallback"}
	return {"owner": "", "basis": ""}


def select_compound_execution_runtime_source(
	*,
	has_current_compound_assessment: bool,
	is_continuation_control: bool,
	has_latest_compound_assessment: bool,
) -> Dict[str, str]:
	if has_current_compound_assessment:
		return {"owner": "current_compound_assessment", "basis": "current_frontdoor_active_sequence"}
	if is_continuation_control and has_latest_compound_assessment:
		return {"owner": "latest_compound_assessment", "basis": "latest_active_sequence_continuation"}
	return {"owner": "", "basis": ""}


def select_targeted_restore_owner(
	*,
	has_target_specifier: bool,
	recent_focus_matches: bool,
	resumable_prior_request_matches: bool,
) -> Dict[str, str]:
	if not has_target_specifier:
		return {"owner": "", "basis": ""}
	if recent_focus_matches:
		return {"owner": "recent_focus", "basis": "targeted_recent_focus_restore"}
	if resumable_prior_request_matches:
		return {"owner": "resumable_prior_request", "basis": "targeted_resumable_prior_branch_restore"}
	return {"owner": "", "basis": ""}


def select_non_clarification_restore_owner(
	*,
	has_recent_focus: bool,
	has_resumable_prior_request: bool,
	recent_focus_precedence_basis: str,
	resumable_prior_precedence_basis: str,
) -> Dict[str, str]:
	if has_recent_focus and not has_resumable_prior_request:
		return {"owner": "recent_focus", "basis": "recent_focus_only_available"}
	if has_resumable_prior_request and not has_recent_focus:
		return {"owner": "resumable_prior_request", "basis": "resumable_prior_request_only_available"}
	if not has_recent_focus and not has_resumable_prior_request:
		return {"owner": "", "basis": ""}
	if str(recent_focus_precedence_basis or "").strip() == "newer":
		return {"owner": "recent_focus", "basis": "recent_focus_precedes_resumable_prior_request_by_newer_index"}
	if str(recent_focus_precedence_basis or "").strip() == "known_over_unindexed":
		return {"owner": "recent_focus", "basis": "recent_focus_precedes_resumable_prior_request_by_known_over_unindexed"}
	if str(resumable_prior_precedence_basis or "").strip() == "newer":
		return {"owner": "resumable_prior_request", "basis": "resumable_prior_request_precedes_recent_focus_by_newer_index"}
	if str(resumable_prior_precedence_basis or "").strip() == "known_over_unindexed":
		return {"owner": "resumable_prior_request", "basis": "resumable_prior_request_precedes_recent_focus_by_known_over_unindexed"}
	return {"owner": "recent_focus", "basis": "recent_focus_defaults_when_peer_precedence_is_indeterminate"}


def select_prior_branch_restore_direct_handler_route(
	*,
	restore_mode: str,
	has_pending_clarification_signal: bool,
) -> Dict[str, str]:
	mode = str(restore_mode or "").strip()
	if mode == "reopen_pending_clarification":
		if has_pending_clarification_signal:
			return {
				"route": "reopen_pending_clarification",
				"basis": "restore_mode_reopen_pending_clarification",
			}
		return {
			"route": "",
			"basis": "missing_pending_clarification_signal",
		}
	if mode == "replay_as_fresh_governed_query":
		return {
			"route": "replay_as_fresh_governed_query",
			"basis": "restore_mode_replay_as_fresh_governed_query",
		}
	return {"route": "", "basis": "unsupported_direct_handler_route"}


def select_latest_non_clarification_restore_state(
	*,
	phrase_type: str,
	has_pending_clarification: bool,
	has_active_sequence: bool,
	has_recent_focus: bool,
	has_resumable_prior_request: bool,
	active_sequence_beats_pending: bool,
	recent_focus_beats_pending: bool,
	resumable_beats_pending: bool,
	active_sequence_is_newer_than_pending: bool,
	recent_focus_is_newer_than_pending: bool,
	resumable_is_newer_than_pending: bool,
	owner_selection_owner: str,
	owner_selection_basis: str,
) -> Dict[str, object]:
	phrase_type = str(phrase_type or "").strip()
	if not has_active_sequence and not has_recent_focus and not has_resumable_prior_request:
		return {"owner": "", "basis": "", "clear_pending_clarification": False}
	active_sequence_eligible = has_active_sequence and (
		not has_pending_clarification or active_sequence_beats_pending
	)
	if active_sequence_eligible:
		return {
			"owner": "active_sequence",
			"basis": (
				"question_restore_uses_active_sequence"
				if not has_pending_clarification
				else (
					"newer_active_sequence_precedes_older_pending_clarification"
					if active_sequence_is_newer_than_pending
					else "known_active_sequence_precedes_non_authoritative_pending_clarification"
				)
			),
			"clear_pending_clarification": has_pending_clarification,
		}
	recent_focus_eligible = has_recent_focus and (
		not has_pending_clarification or recent_focus_beats_pending
	)
	resumable_eligible = has_resumable_prior_request and (
		not has_pending_clarification or resumable_beats_pending
	)
	if not recent_focus_eligible and not resumable_eligible:
		return {"owner": "", "basis": "", "clear_pending_clarification": False}
	owner = str(owner_selection_owner or "").strip()
	owner_basis = str(owner_selection_basis or "").strip()
	if owner == "recent_focus":
		basis = {
			("question_restore", False): "question_restore_uses_recent_focus",
			("question_restore", True): "newer_recent_focus_precedes_older_pending_clarification",
			("branch_restore", False): "generic_branch_restore_uses_recent_focus",
			("branch_restore", True): "generic_branch_restore_prefers_newer_recent_focus",
		}.get((phrase_type, has_pending_clarification), "")
		if has_pending_clarification and not recent_focus_is_newer_than_pending:
			basis = {
				"question_restore": "known_recent_focus_precedes_non_authoritative_pending_clarification",
				"branch_restore": "generic_branch_restore_prefers_known_recent_focus_over_non_authoritative_pending_clarification",
			}.get(phrase_type, basis)
		if recent_focus_eligible and resumable_eligible:
			if owner_basis == "recent_focus_precedes_resumable_prior_request_by_newer_index":
				basis = (
					"question_restore_prefers_newer_recent_focus_over_resumable_prior_request"
					if phrase_type == "question_restore"
					else "generic_branch_restore_prefers_newer_recent_focus_over_resumable_prior_request"
				)
			elif owner_basis == "recent_focus_precedes_resumable_prior_request_by_known_over_unindexed":
				basis = (
					"question_restore_prefers_known_recent_focus_over_unindexed_resumable_prior_request"
					if phrase_type == "question_restore"
					else "generic_branch_restore_prefers_known_recent_focus_over_unindexed_resumable_prior_request"
				)
			else:
				basis = (
					"question_restore_defaults_to_recent_focus_when_peer_precedence_is_indeterminate"
					if phrase_type == "question_restore"
					else "generic_branch_restore_defaults_to_recent_focus_when_peer_precedence_is_indeterminate"
				)
		return {
			"owner": "recent_focus",
			"basis": basis,
			"clear_pending_clarification": has_pending_clarification,
		}
	if owner == "resumable_prior_request":
		basis = {
			("question_restore", False): "question_restore_uses_resumable_prior_request",
			("question_restore", True): "newer_resumable_prior_request_precedes_older_pending_clarification",
			("branch_restore", False): "generic_branch_restore_uses_resumable_prior_request",
			("branch_restore", True): "generic_branch_restore_prefers_newer_resumable_prior_request",
		}.get((phrase_type, has_pending_clarification), "")
		if has_pending_clarification and not resumable_is_newer_than_pending:
			basis = {
				"question_restore": "known_resumable_prior_request_precedes_non_authoritative_pending_clarification",
				"branch_restore": "generic_branch_restore_prefers_known_resumable_prior_request_over_non_authoritative_pending_clarification",
			}.get(phrase_type, basis)
		if recent_focus_eligible and resumable_eligible:
			if owner_basis == "resumable_prior_request_precedes_recent_focus_by_newer_index":
				basis = (
					"question_restore_prefers_newer_resumable_prior_request_over_recent_focus"
					if phrase_type == "question_restore"
					else "generic_branch_restore_prefers_newer_resumable_prior_request_over_recent_focus"
				)
			else:
				basis = (
					"question_restore_prefers_known_resumable_prior_request_over_unindexed_recent_focus"
					if phrase_type == "question_restore"
					else "generic_branch_restore_prefers_known_resumable_prior_request_over_unindexed_recent_focus"
				)
		return {
			"owner": "resumable_prior_request",
			"basis": basis,
			"clear_pending_clarification": has_pending_clarification,
		}
	return {"owner": "", "basis": "", "clear_pending_clarification": False}


def select_prior_branch_restore_route(
	*,
	phrase_type: str,
	targeted_restore_owner: str,
	targeted_restore_basis: str,
	has_target_specifier: bool,
	latest_non_clarification_owner: str,
	latest_non_clarification_basis: str,
	pending_clarification_is_authoritative: bool,
	has_active_sequence: bool,
	has_resumable_prior_request: bool,
) -> Dict[str, str]:
	phrase_type = str(phrase_type or "").strip()
	targeted_restore_owner = str(targeted_restore_owner or "").strip()
	targeted_restore_basis = str(targeted_restore_basis or "").strip()
	if targeted_restore_owner == "recent_focus":
		return {
			"route": "targeted_recent_focus",
			"owner": targeted_restore_owner,
			"basis": targeted_restore_basis,
		}
	if targeted_restore_owner == "resumable_prior_request":
		return {
			"route": "targeted_resumable_prior_request",
			"owner": targeted_restore_owner,
			"basis": targeted_restore_basis,
		}
	if phrase_type == "branch_restore" and has_target_specifier:
		return {
			"route": "targeted_no_match_block",
			"owner": "",
			"basis": "targeted_restore_requested_without_matching_owner",
		}
	latest_owner = str(latest_non_clarification_owner or "").strip()
	if phrase_type in {"question_restore", "branch_restore"} and latest_owner:
		return {
			"route": "latest_non_clarification",
			"owner": latest_owner,
			"basis": str(latest_non_clarification_basis or "").strip(),
		}
	if phrase_type in {"question_restore", "branch_restore"} and pending_clarification_is_authoritative:
		return {
			"route": "authoritative_pending_clarification",
			"owner": "pending_clarification",
			"basis": {
				"question_restore": "pending_clarification_precedes_question_restore",
				"branch_restore": "pending_clarification_precedes_generic_prior_branch_restore",
			}.get(phrase_type, ""),
		}
	if phrase_type == "sequence_restore" and has_active_sequence:
		return {
			"route": "direct_restore_fallback",
			"owner": "active_sequence",
			"basis": "sequence_restore_uses_active_sequence",
		}
	if phrase_type in {"question_restore", "branch_restore"} and has_resumable_prior_request:
		return {
			"route": "direct_restore_fallback",
			"owner": "resumable_prior_request",
			"basis": {
				"question_restore": "question_restore_uses_resumable_prior_request",
				"branch_restore": "generic_branch_restore_uses_resumable_prior_request",
			}.get(phrase_type, ""),
		}
	return {"route": "", "owner": "", "basis": ""}


def recent_focus_reference_defaults_for_kind(focus_kind: str) -> tuple[bool, bool]:
	normalized_focus_kind = str(focus_kind or "").strip()
	if normalized_focus_kind == "entity":
		return True, True
	if normalized_focus_kind == "document":
		return True, True
	if normalized_focus_kind == "statement":
		return False, True
	if normalized_focus_kind == "listing":
		return True, False
	if normalized_focus_kind == "report":
		return True, True
	return False, False


def prior_branch_restore_mode(prior_branch_restore_contract) -> str:
	if prior_branch_restore_contract is None:
		return ""
	return str(getattr(prior_branch_restore_contract, "restore_mode", "") or "").strip()


def recent_focus_state_from_prior_branch_restore_contract(
	prior_branch_restore_contract,
) -> Dict[str, object]:
	if prior_branch_restore_mode(prior_branch_restore_contract) != "restore_recent_focus":
		return {}
	target_scope = (
		getattr(prior_branch_restore_contract, "target_scope", {})
		if isinstance(getattr(prior_branch_restore_contract, "target_scope", {}), dict)
		else {}
	)
	focus_kind = str(target_scope.get("focus_kind") or "").strip()
	deictic_allowed_default, explicit_named_allowed_default = recent_focus_reference_defaults_for_kind(
		focus_kind
	)
	focus_label = str(target_scope.get("focus_label") or "").strip() or str(
		getattr(prior_branch_restore_contract, "target_branch_label", "") or ""
	).strip()
	return {
		"available": bool(focus_label),
		"focus_kind": focus_kind,
		"focus_grain": str(target_scope.get("focus_grain") or "").strip(),
		"focus_label": focus_label,
		"focus_key": str(target_scope.get("focus_key") or "").strip() or focus_label,
		"source_request_id": str(getattr(prior_branch_restore_contract, "target_request_id", "") or "").strip(),
		"source_family": str(getattr(prior_branch_restore_contract, "target_family", "") or "").strip(),
		"source_capability": str(target_scope.get("source_capability") or "").strip(),
		"source_report": str(target_scope.get("source_report") or "").strip(),
		"deictic_allowed": (
			bool(target_scope.get("deictic_allowed"))
			if "deictic_allowed" in target_scope
			else deictic_allowed_default
		),
		"explicit_named_allowed": (
			bool(target_scope.get("explicit_named_allowed"))
			if "explicit_named_allowed" in target_scope
			else explicit_named_allowed_default
		),
		"derivation_basis": "prior_branch_restore_contract",
		"confidence": float(getattr(prior_branch_restore_contract, "confidence", 0.0) or 0.0),
	}


def recent_focus_restore_runtime_message(*, recent_focus_state: Dict[str, object]) -> str:
	if not recent_focus_state:
		return ""
	target_label = str((recent_focus_state or {}).get("focus_label") or "").strip()
	focus_kind = str((recent_focus_state or {}).get("focus_kind") or "").strip()
	focus_grain = str((recent_focus_state or {}).get("focus_grain") or "").strip()
	source_family = str((recent_focus_state or {}).get("source_family") or "").strip()
	source_report = str((recent_focus_state or {}).get("source_report") or "").strip()
	if focus_kind == "entity":
		return f"tell me more about {target_label}".strip()
	if focus_kind == "document":
		document_label = focus_grain.replace("_", " ").strip() if focus_grain else ""
		if document_label and target_label:
			return f"show me details for {document_label} {target_label}".strip()
		if target_label:
			return f"show me details for {target_label}".strip()
		return ""
	if focus_kind == "statement":
		return f"show me {target_label}".strip()
	if focus_kind == "listing":
		if is_master_data_listing_family(source_family) or focus_grain in {
			"customer",
			"supplier",
			"item",
			"product",
		}:
			entity_plural = str(entity_grain_display_label(focus_grain, plural=True) or "").strip().lower()
			if entity_plural:
				return f"show me {entity_plural}".strip()
		listing_label = str(listing_view_display_label(focus_grain, plural=True, lowercase=True) or "").strip()
		if listing_label:
			return f"show me {listing_label}".strip()
		if target_label:
			return f"show me {target_label}".strip()
		if source_report:
			return f"show me {source_report}".strip()
		return ""
	if focus_kind == "report":
		if target_label:
			return f"show me {target_label}".strip()
		if source_report:
			return f"show me {source_report}".strip()
		return ""
	return target_label


def prior_branch_restore_runtime_message(prior_branch_restore_contract) -> str:
	recent_focus_state = recent_focus_state_from_prior_branch_restore_contract(prior_branch_restore_contract)
	return recent_focus_restore_runtime_message(recent_focus_state=recent_focus_state)


def select_authoritative_pending_clarification_restore_spec(
	*,
	phrase_type: str,
	has_authoritative_pending_clarification: bool,
	user_question: str,
	request_id: str,
	continuation_lane: str,
) -> Dict[str, object]:
	phrase_type = str(phrase_type or "").strip()
	if phrase_type not in {"question_restore", "branch_restore"}:
		return {}
	if not has_authoritative_pending_clarification:
		return {}
	reason = (
		"The user asked to return to the still-pending clarification question."
		if phrase_type == "question_restore"
		else "A generic branch-restore request was resolved to the still-pending clarification because it is the highest-priority active branch."
	)
	arbitration_basis = {
		"question_restore": "pending_clarification_precedes_question_restore",
		"branch_restore": "pending_clarification_precedes_generic_prior_branch_restore",
	}.get(phrase_type, "")
	return {
		"target_branch_kind": "clarification",
		"target_branch_label": str(user_question or "").strip(),
		"target_request_id": str(request_id or "").strip(),
		"target_family": "clarification",
		"restore_mode": "reopen_pending_clarification",
		"resumable": True,
		"preserve_time_context": True,
		"preserve_scope": True,
		"preserve_entity_dimension": True,
		"reason": reason,
		"confidence": 0.96 if phrase_type == "question_restore" else 0.9,
		"internal_details": {
			"phrase_type": phrase_type,
			"continuation_lane": str(continuation_lane or "").strip(),
			"arbitration_basis": arbitration_basis,
		},
	}


def select_direct_restore_fallback_spec(
	*,
	phrase_type: str,
	has_active_sequence: bool,
	has_resumable_prior_request: bool,
	resumable_suggested_restore_mode: str,
	resumable_derivation_basis: str,
	resumable_accepted_recovery_action: str,
	resumable_prior_recovery_payload: Dict[str, object],
) -> Dict[str, object]:
	phrase_type = str(phrase_type or "").strip()
	if phrase_type == "sequence_restore":
		if not has_active_sequence:
			return {}
		return {
			"owner": "active_sequence",
			"reason": "The user asked to resume the still-active ordered multi-step sequence.",
			"arbitration_basis": "sequence_restore_uses_active_sequence",
		}
	if phrase_type not in {"question_restore", "branch_restore"}:
		return {}
	if not has_resumable_prior_request:
		return {}
	arbitration_basis = {
		"question_restore": "question_restore_uses_resumable_prior_request",
		"branch_restore": "generic_branch_restore_uses_resumable_prior_request",
	}.get(phrase_type, "")
	return {
		"owner": "resumable_prior_request",
		"reason": "The user asked to return to a prior resumable branch.",
		"internal_details": {
			"phrase_type": phrase_type,
			"snapshot_restore_mode": str(resumable_suggested_restore_mode or "").strip(),
			"arbitration_basis": arbitration_basis,
			"derivation_basis": str(resumable_derivation_basis or "").strip(),
			"accepted_recovery_action": str(resumable_accepted_recovery_action or "").strip(),
			"prior_recovery_payload": dict(resumable_prior_recovery_payload or {}),
		},
	}


def select_prior_branch_restore_decision_spec(
	*,
	request_id: str,
	restore_mode: str,
	target_branch_kind: str,
	target_branch_label: str,
	target_request_id: str,
	target_family: str,
	projection_resolved_focus_target: Dict[str, object],
	projection_internal_details: Dict[str, object],
	clear_pending_clarification: bool,
	clear_active_sequence: bool,
	resumable: bool,
	confidence: float,
	reason: str,
) -> Dict[str, object]:
	mode = str(restore_mode or "").strip()
	if not mode:
		return {}
	resolved_focus_target = {
		"target_branch_kind": str(target_branch_kind or "").strip(),
		"target_branch_label": str(target_branch_label or "").strip(),
		"target_request_id": str(target_request_id or "").strip(),
		"target_family": str(target_family or "").strip(),
	}
	if isinstance(projection_resolved_focus_target, dict) and projection_resolved_focus_target:
		resolved_focus_target.update(dict(projection_resolved_focus_target))
	internal_details = {
		"source_contract_type": "qwen_prior_branch_restore_contract",
		"restore_mode": mode,
		"resumable": bool(resumable),
	}
	if isinstance(projection_internal_details, dict) and projection_internal_details:
		internal_details.update(dict(projection_internal_details))
	return {
		"request_id": str(request_id or "").strip(),
		"decision_class": "prior_branch_restore",
		"decision_action": mode,
		"target_state_class": "prior_branch_restore",
		"resolved_business_message": "",
		"resolved_focus_target": resolved_focus_target,
		"clear_pending_clarification": bool(clear_pending_clarification),
		"clear_active_sequence": bool(clear_active_sequence),
		"preserve_prior_branch": True,
		"confidence": float(confidence or 0.0),
		"reason": str(reason or "").strip(),
		"internal_details": internal_details,
	}


def select_targeted_recent_focus_restore_spec(
	*,
	phrase_type: str,
	target_hint: str,
	target_grain: str,
	target_focus_kind: str,
	restore_basis: str,
	clear_pending_clarification: bool,
	recent_focus_derivation_basis: str,
) -> Dict[str, object]:
	return {
		"reason": "The user asked to return to the recent business focus that matches the requested branch.",
		"clear_current_pending_clarification": bool(clear_pending_clarification),
		"internal_details": {
			"phrase_type": str(phrase_type or "").strip(),
			"target_hint": str(target_hint or "").strip(),
			"target_grain": str(target_grain or "").strip(),
			"target_focus_kind": str(target_focus_kind or "").strip(),
			"arbitration_basis": str(restore_basis or "").strip(),
			"derivation_basis": str(recent_focus_derivation_basis or "").strip(),
		},
	}


def select_targeted_resumable_prior_request_restore_spec(
	*,
	phrase_type: str,
	target_hint: str,
	target_grain: str,
	target_focus_kind: str,
	restore_basis: str,
	clear_pending_clarification: bool,
	resumable_suggested_restore_mode: str,
	resumable_derivation_basis: str,
	resumable_accepted_recovery_action: str,
	resumable_prior_recovery_payload: Dict[str, object],
) -> Dict[str, object]:
	return {
		"reason": "The user asked to return to a prior branch that matches the requested business target.",
		"clear_current_pending_clarification": bool(clear_pending_clarification),
		"internal_details": {
			"phrase_type": str(phrase_type or "").strip(),
			"target_hint": str(target_hint or "").strip(),
			"target_grain": str(target_grain or "").strip(),
			"target_focus_kind": str(target_focus_kind or "").strip(),
			"snapshot_restore_mode": str(resumable_suggested_restore_mode or "").strip(),
			"arbitration_basis": str(restore_basis or "").strip(),
			"derivation_basis": str(resumable_derivation_basis or "").strip(),
			"accepted_recovery_action": str(resumable_accepted_recovery_action or "").strip(),
			"prior_recovery_payload": dict(resumable_prior_recovery_payload or {}),
		},
	}


def select_prior_branch_restore_request_interpretation(
	*,
	control_phrase_type: str,
	message_phrase_type: str,
	control_target_hint: str,
	control_target_grain: str,
	control_target_focus_kind: str,
	message_target_hint: str,
	message_target_grain: str,
	message_target_focus_kind: str,
) -> Dict[str, str]:
	phrase_type = str(control_phrase_type or "").strip() or str(message_phrase_type or "").strip()
	target_hint = str(control_target_hint or "").strip()
	target_grain = str(control_target_grain or "").strip()
	target_focus_kind = str(control_target_focus_kind or "").strip()
	if not target_hint and not target_grain and not target_focus_kind:
		target_hint = str(message_target_hint or "").strip()
		target_grain = str(message_target_grain or "").strip()
		target_focus_kind = str(message_target_focus_kind or "").strip()
	return {
		"phrase_type": phrase_type,
		"target_hint": target_hint,
		"target_grain": target_grain,
		"target_focus_kind": target_focus_kind,
	}


def select_prior_branch_restore_projection(
	*,
	restore_mode: str,
	target_branch_label: str,
	runtime_override_message: str,
	resolved_focus_target: Dict[str, object],
	recent_focus_affordance_payload: Dict[str, object],
) -> Dict[str, object]:
	mode = str(restore_mode or "").strip()
	if not mode:
		return {
			"restore_mode": "",
			"runtime_override_message": "",
			"resolved_focus_target": {},
			"internal_details": {},
			"basis": "",
		}
	if mode == "resume_active_sequence":
		return {
			"restore_mode": mode,
			"runtime_override_message": str(target_branch_label or "").strip(),
			"resolved_focus_target": {},
			"internal_details": {},
			"basis": "resume_active_sequence_target_label",
		}
	if mode == "restore_recent_focus":
		internal_details = {}
		if isinstance(recent_focus_affordance_payload, dict) and recent_focus_affordance_payload:
			internal_details["recent_focus_affordance"] = dict(recent_focus_affordance_payload)
		return {
			"restore_mode": mode,
			"runtime_override_message": str(runtime_override_message or "").strip(),
			"resolved_focus_target": dict(resolved_focus_target or {}),
			"internal_details": internal_details,
			"basis": "restore_recent_focus_projection",
		}
	return {
		"restore_mode": mode,
		"runtime_override_message": "",
		"resolved_focus_target": {},
		"internal_details": {},
		"basis": "no_projection",
	}
