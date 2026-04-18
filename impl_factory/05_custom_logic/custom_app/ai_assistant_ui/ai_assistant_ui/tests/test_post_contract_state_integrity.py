import json
import sys
import types
import unittest
from dataclasses import dataclass
from typing import Any, Dict, List
from unittest.mock import patch

fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.clarification_resolution import (
	clarification_continuation_lane,
	clarification_resolved_continuation_message,
	clear_pending_clarification_signal,
	latest_assistant_turn_was_clarification_fallback_stop,
	latest_pending_clarification_signal,
	latest_pending_clarification_signal_from_messages,
	looks_like_short_acknowledgement,
	resolve_pending_clarification_response,
	store_pending_clarification_signal,
)
from ai_assistant_ui.qwen_chat.conversation_control_language import (
	classify_conversation_control_evidence,
	looks_like_option_list_request as shared_looks_like_option_list_request,
)
from ai_assistant_ui.qwen_chat.clarification_state import (
	build_pending_clarification_state,
	clarification_state_from_storage,
	get_clarification_state,
)
from ai_assistant_ui.qwen_chat.clarification_resolution import clarification_state_after_unresolved_attempt
from ai_assistant_ui.qwen_chat.contracts import (
	build_artifact_enrichment_recovery_contract,
	build_compound_request_assessment_contract,
	build_conversation_control_evidence_contract,
	build_conversation_control_decision_contract,
	build_conversational_repair_intent_contract,
	build_followup_resolution_contract,
	build_prior_branch_restore_contract,
)
from ai_assistant_ui.qwen_chat.service import (
	_build_recent_focus_affordance_contract_from_snapshot,
	_build_conversation_control_evidence_contract,
	_build_conversation_state_snapshot,
	_build_prior_branch_restore_contract_from_snapshot,
	_artifact_boundary_clarification_requires_runtime_reset,
	_artifact_local_refinement_should_defer_runtime_frontdoor,
	_conversation_control_decision_from_clarification_response,
	_conversation_control_decision_from_compound_cancellation,
	_conversation_control_decision_from_compound_completion,
	_conversation_control_decision_from_compound_continuation,
	_compound_request_completion_answer_from_snapshot,
	_compound_request_continuation_control_with_evidence,
	_compound_request_completion_is_superseded_by_newer_state,
	_compound_request_stop_control_with_evidence,
	_conversation_control_decision_from_prior_branch_restore_contract,
	_conversation_control_decision_from_repair_contract,
	_conversation_control_decision_from_recent_focus_runtime_message,
	_frontdoor_clarification_reentry_message,
	_frontdoor_clarification_requires_fresh_query_reset,
	_handle_prior_branch_restore_reopen_pending_clarification,
	_handle_prior_branch_restore_fresh_query,
	_prior_branch_restore_mode,
	_prior_branch_restore_runtime_override_message,
	_prior_branch_restore_runtime_message,
	_latest_normalized_family_artifact,
	_latest_repair_intent_contract,
	_latest_grounded_turn_contract,
	_preserve_current_artifact_direct_evidence_followup_resolution,
	_preserve_artifact_boundary_clarification_followup_resolution,
	_resolve_compound_execution_runtime_message,
	_strip_leading_control_discard_preamble,
	_latest_recovery_contract,
	_resolved_clarification_runtime_message,
	_source_compatible_reasoning_contract,
)


def _clarification_signal(*, request_id: str, user_question: str) -> Dict[str, Any]:
	return {
		"type": "qwen_clarification_signal_contract",
		"contract_version": "1.0",
		"request_id": request_id,
		"stage": "fresh_query_compiler",
		"reason_type": "report_ambiguity",
		"user_question": user_question,
		"suggested_options": ["Option A", "Option B"],
	}


@dataclass
class _FakeMessage:
	role: str
	content: str


class _FakeSessionDoc:
	def __init__(self, messages: List[_FakeMessage] | None = None):
		self._messages = list(messages or [])
		self.pending_clarification_state_json = ""

	def get(self, key, default=None):
		if key == "messages":
			return list(self._messages)
		return default


class TestPostContractStateIntegrity(unittest.TestCase):
	def test_conversation_control_decision_maps_clarification_resolution(self):
		signal = _clarification_signal(request_id="clarify-map-1", user_question="Choose one KPI basis.")
		signal["reason_type"] = "governed_kpi_definition_ambiguity"
		signal["internal_details"] = {
			"continuation_lane": "front_door",
			"resolved_message_by_option": {
				"Average Order Value by Sales Order": "what is Average Order Value by Sales Order",
			},
		}
		clarification_contract = resolve_pending_clarification_response(
			request_id="clarify-map-1-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="Average Order Value by Sales Order",
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
		)

		decision_contract = _conversation_control_decision_from_clarification_response(
			raw_message="Average Order Value by Sales Order",
			pending_clarification_signal=signal,
			clarification_response_contract=clarification_contract,
		)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_class") or "").strip(), "clarification_resolution")
		self.assertEqual(str(payload.get("decision_action") or "").strip(), "resolve_pending_clarification")
		self.assertTrue(bool(payload.get("clear_pending_clarification")))
		self.assertEqual(
			str(payload.get("resolved_business_message") or "").strip(),
			"what is Average Order Value by Sales Order",
		)

	def test_conversation_control_decision_maps_clarification_new_request_override(self):
		signal = _clarification_signal(request_id="clarify-map-2", user_question="Choose one report.")
		clarification_contract = resolve_pending_clarification_response(
			request_id="clarify-map-2-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="show me suppliers",
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
		)

		decision_contract = _conversation_control_decision_from_clarification_response(
			raw_message="show me suppliers",
			pending_clarification_signal=signal,
			clarification_response_contract=clarification_contract,
		)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_class") or "").strip(), "fresh_request_override")
		self.assertEqual(str(payload.get("decision_action") or "").strip(), "override_with_new_request")
		self.assertTrue(bool(payload.get("clear_pending_clarification")))
		self.assertEqual(str(payload.get("resolved_business_message") or "").strip(), "show me suppliers")

	def test_conversation_control_decision_prefers_embedded_override_business_message(self):
		signal = _clarification_signal(request_id="clarify-map-2b", user_question="Choose one report.")
		clarification_contract = resolve_pending_clarification_response(
			request_id="clarify-map-2b-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="ignore that, show me suppliers",
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
			control_evidence_payload={
				"evidence_class": "fresh_request_redirect",
				"action_id": "override_with_new_request",
				"embedded_business_message": "show me suppliers",
			},
		)

		decision_contract = _conversation_control_decision_from_clarification_response(
			raw_message="ignore that, show me suppliers",
			pending_clarification_signal=signal,
			clarification_response_contract=clarification_contract,
		)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_action") or "").strip(), "override_with_new_request")
		self.assertEqual(str(payload.get("resolved_business_message") or "").strip(), "show me suppliers")

	def test_clarification_resolution_uses_shared_option_list_evidence(self):
		signal = _clarification_signal(request_id="clarify-shared-1", user_question="Which item do you mean?")
		clarification_contract = resolve_pending_clarification_response(
			request_id="clarify-shared-1-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="show me the list",
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
			control_evidence_payload={
				"evidence_class": "option_list_request",
				"action_id": "show_pending_options",
				"embedded_business_message": "",
			},
		)

		self.assertEqual(str(getattr(clarification_contract, "decision", "") or "").strip(), "show_options")
		self.assertEqual(str(getattr(clarification_contract, "matched_by", "") or "").strip(), "shared_control_evidence")

	def test_clarification_resolution_uses_shared_redirect_evidence(self):
		signal = _clarification_signal(request_id="clarify-shared-2", user_question="Which item do you mean?")
		clarification_contract = resolve_pending_clarification_response(
			request_id="clarify-shared-2-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="ignore that, show me suppliers",
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
			control_evidence_payload={
				"evidence_class": "fresh_request_redirect",
				"action_id": "override_with_new_request",
				"embedded_business_message": "show me suppliers",
			},
		)

		self.assertEqual(str(getattr(clarification_contract, "decision", "") or "").strip(), "new_request")
		self.assertEqual(
			str((getattr(clarification_contract, "internal_details", {}) or {}).get("override_business_message") or "").strip(),
			"show me suppliers",
		)

	def test_clarification_resolution_uses_shared_discard_evidence(self):
		signal = _clarification_signal(request_id="clarify-shared-2b", user_question="Which item do you mean?")
		clarification_contract = resolve_pending_clarification_response(
			request_id="clarify-shared-2b-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="ignore that",
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
			control_evidence_payload={
				"evidence_class": "override_discard",
				"action_id": "abandon_current_branch",
				"embedded_business_message": "",
			},
		)

		self.assertEqual(str(getattr(clarification_contract, "decision", "") or "").strip(), "abandon_current_branch")
		self.assertEqual(str(getattr(clarification_contract, "matched_by", "") or "").strip(), "shared_control_evidence")

	def test_conversation_control_decision_maps_clarification_branch_discard(self):
		signal = _clarification_signal(request_id="clarify-map-2c", user_question="Choose one report.")
		clarification_contract = resolve_pending_clarification_response(
			request_id="clarify-map-2c-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="ignore that",
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
			control_evidence_payload={
				"evidence_class": "override_discard",
				"action_id": "abandon_current_branch",
				"embedded_business_message": "",
			},
		)

		decision_contract = _conversation_control_decision_from_clarification_response(
			raw_message="ignore that",
			pending_clarification_signal=signal,
			clarification_response_contract=clarification_contract,
		)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_class") or "").strip(), "branch_discard")
		self.assertEqual(str(payload.get("decision_action") or "").strip(), "abandon_current_branch")
		self.assertTrue(bool(payload.get("clear_pending_clarification")))

	def test_conversation_control_decision_maps_sequence_cancellation_from_shared_discard_evidence(self):
		active_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-2b",
			status="ordered_execution_in_progress",
			segments=["show me payment entries", "give me some customer list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some customer list",
				"remaining_segment_messages": ["give me some customer list"],
			},
		).to_payload()
		cancelled_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-2b",
			status="ordered_execution_cancelled",
			segments=["show me payment entries", "give me some customer list"],
			clarification_required=False,
			reason="Ordered multi-step request cancelled.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "",
				"remaining_segment_messages": [],
				"cancelled": True,
			},
		).to_payload()

		decision_contract = _conversation_control_decision_from_compound_cancellation(
			request_id="compound-seq-2b-turn-2",
			raw_message="ignore that",
			active_sequence_payload=active_payload,
			cancelled_sequence_payload=cancelled_payload,
			control_evidence_payload={
				"evidence_class": "override_discard",
				"action_id": "abandon_current_branch",
				"embedded_business_message": "",
			},
		)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_action") or "").strip(), "cancel_active_sequence")
		self.assertTrue(bool(payload.get("clear_active_sequence")))

	def test_conversation_control_decision_maps_sequence_continuation(self):
		compound_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-1",
			status="ordered_execution_in_progress",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": ["give me some supplier list"],
			},
		).to_payload()

		decision_contract = _conversation_control_decision_from_compound_continuation(
			request_id="compound-seq-1-turn-2",
			raw_message="continue",
			active_sequence_payload=compound_payload,
			runtime_message="give me some supplier list",
		)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_class") or "").strip(), "sequence_continuation")
		self.assertEqual(str(payload.get("decision_action") or "").strip(), "resume_active_sequence")
		self.assertEqual(str(payload.get("target_state_class") or "").strip(), "active_sequence")
		self.assertEqual(str(payload.get("resolved_business_message") or "").strip(), "give me some supplier list")
		self.assertFalse(bool(payload.get("clear_active_sequence")))
		self.assertEqual(
			str(((payload.get("resolved_sequence_target") or {}).get("primary_segment_message")) or "").strip(),
			"give me some supplier list",
		)

	def test_conversation_control_decision_maps_sequence_cancellation(self):
		active_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-2",
			status="ordered_execution_in_progress",
			segments=["show me payment entries", "give me some customer list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some customer list",
				"remaining_segment_messages": ["give me some customer list"],
			},
		).to_payload()
		cancelled_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-2",
			status="ordered_execution_cancelled",
			segments=["show me payment entries", "give me some customer list"],
			clarification_required=False,
			reason="Ordered multi-step request cancelled.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "",
				"remaining_segment_messages": [],
				"cancelled": True,
			},
		).to_payload()

		decision_contract = _conversation_control_decision_from_compound_cancellation(
			request_id="compound-seq-2-turn-2",
			raw_message="stop",
			active_sequence_payload=active_payload,
			cancelled_sequence_payload=cancelled_payload,
		)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_class") or "").strip(), "sequence_cancellation")
		self.assertEqual(str(payload.get("decision_action") or "").strip(), "cancel_active_sequence")
		self.assertTrue(bool(payload.get("clear_active_sequence")))
		self.assertEqual(str(payload.get("resolved_business_message") or "").strip(), "Okay, I'll stop here.")
		self.assertEqual(
			str(((payload.get("resolved_sequence_target") or {}).get("status")) or "").strip(),
			"ordered_execution_cancelled",
		)

	def test_conversation_control_decision_maps_sequence_completion_reentry(self):
		completed_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-3",
			status="ordered_execution_complete",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request complete.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "",
				"remaining_segment_messages": [],
			},
		).to_payload()

		decision_contract = _conversation_control_decision_from_compound_completion(
			request_id="compound-seq-3-turn-3",
			raw_message="continue",
			compound_assessment_payload=completed_payload,
			completion_answer="That sequence is already finished. You can start a new request anytime.",
		)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_class") or "").strip(), "sequence_completion_reentry")
		self.assertEqual(str(payload.get("decision_action") or "").strip(), "acknowledge_completed_sequence")
		self.assertTrue(bool(payload.get("clear_active_sequence")))
		self.assertIn("already finished", str(payload.get("resolved_business_message") or "").strip().lower())

	def test_compound_request_completion_superseded_by_newer_pending_clarification(self):
		active_sequence_state = {
			"available": True,
			"status": "ordered_execution_complete",
			"source_tool_index": 10,
		}
		pending_clarification_state = {
			"available": True,
			"source_tool_index": 14,
		}

		self.assertTrue(
			_compound_request_completion_is_superseded_by_newer_state(
				active_sequence_state=active_sequence_state,
				pending_clarification_state=pending_clarification_state,
				recent_focus_state={},
				resumable_prior_request_state={},
			)
		)

	def test_compound_request_completion_superseded_by_newer_recent_focus(self):
		active_sequence_state = {
			"available": True,
			"status": "ordered_execution_cancelled",
			"source_tool_index": 20,
		}
		recent_focus_state = {
			"available": True,
			"focus_label": "Ko Nay Lin Mobile Center",
			"source_tool_index": 25,
		}

		self.assertTrue(
			_compound_request_completion_is_superseded_by_newer_state(
				active_sequence_state=active_sequence_state,
				pending_clarification_state={},
				recent_focus_state=recent_focus_state,
				resumable_prior_request_state={},
			)
		)

	def test_compound_request_completion_answer_from_snapshot_is_suppressed_by_newer_state(self):
		completed_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-3b",
			status="ordered_execution_complete",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request complete.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "",
				"remaining_segment_messages": [],
			},
		).to_payload()
		snapshot = {
			"active_sequence": {
				"available": True,
				"payload": completed_payload,
				"status": "ordered_execution_complete",
				"source_tool_index": 10,
			},
			"pending_clarification": {
				"available": True,
				"source_tool_index": 12,
			},
			"recent_focus": {"available": False},
			"resumable_prior_request": {"available": False},
		}

		answer = _compound_request_completion_answer_from_snapshot(
			conversation_state_snapshot=snapshot,
			message="continue",
			control_evidence_payload=None,
		)

		self.assertEqual(answer, "")

	def test_compound_request_completion_answer_from_snapshot_preserves_latest_completed_sequence(self):
		completed_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-3c",
			status="ordered_execution_complete",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request complete.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "",
				"remaining_segment_messages": [],
			},
		).to_payload()
		snapshot = {
			"active_sequence": {
				"available": True,
				"payload": completed_payload,
				"status": "ordered_execution_complete",
				"source_tool_index": 18,
			},
			"pending_clarification": {
				"available": True,
				"source_tool_index": 12,
			},
			"recent_focus": {"available": False},
			"resumable_prior_request": {"available": False},
		}

		answer = _compound_request_completion_answer_from_snapshot(
			conversation_state_snapshot=snapshot,
			message="continue",
			control_evidence_payload=None,
		)

		self.assertIn("already finished", answer.lower())

	def test_compound_request_continuation_control_uses_shared_classifier_without_explicit_evidence(self):
		self.assertTrue(
			_compound_request_continuation_control_with_evidence(
				"go ahead",
				control_evidence_payload=None,
			)
		)
		self.assertFalse(
			_compound_request_continuation_control_with_evidence(
				"show me suppliers",
				control_evidence_payload=None,
			)
		)

	def test_compound_request_stop_control_uses_shared_classifier_without_explicit_evidence(self):
		self.assertTrue(
			_compound_request_stop_control_with_evidence(
				"not now",
				control_evidence_payload=None,
			)
		)
		self.assertFalse(
			_compound_request_stop_control_with_evidence(
				"show me suppliers",
				control_evidence_payload=None,
			)
		)

	def test_conversation_control_decision_maps_recent_focus_runtime_message(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "entity",
			"focus_grain": "item",
			"focus_label": "Type-C Cable 1m Fast Charge",
			"focus_key": "ACC-CBL-BAS-TC1M",
			"source_request_id": "item-detail-1",
			"source_family": "entity_detail",
			"source_capability": "item_sales_detail",
			"source_report": "Item Detail",
			"deictic_allowed": True,
			"explicit_named_allowed": True,
			"confidence": 0.9,
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-1",
			mode="new_query",
			requested_modes=["new_query"],
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
			latest_grounded_turn_available=True,
			reason="The follow-up depends on the latest grounded focus.",
		)

		decision_contract = _conversation_control_decision_from_recent_focus_runtime_message(
			request_id="recent-focus-1",
			raw_message="how many stocks do we have, and in which warehouse?",
			runtime_message='how many stocks do we have, and in which warehouse for item "Type-C Cable 1m Fast Charge"?',
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
		)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_class") or "").strip(), "recent_focus_continuation")
		self.assertEqual(str(payload.get("decision_action") or "").strip(), "resolve_recent_focus_followup")
		self.assertEqual(str(payload.get("target_state_class") or "").strip(), "recent_focus")
		self.assertTrue(bool(payload.get("update_recent_focus")))
		self.assertEqual(
			str(((payload.get("resolved_focus_target") or {}).get("focus_label")) or "").strip(),
			"Type-C Cable 1m Fast Charge",
		)
		self.assertEqual(
			str((((payload.get("internal_details") or {}).get("recent_focus_affordance") or {}).get("type")) or "").strip(),
			"qwen_recent_focus_affordance_contract",
		)
		self.assertIn(
			"inventory_position_followup",
			list((((payload.get("internal_details") or {}).get("recent_focus_affordance") or {}).get("allowed_action_classes")) or []),
		)

	def test_recent_focus_decision_is_suppressed_by_shared_control_evidence(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "entity",
			"focus_grain": "item",
			"focus_label": "Type-C Cable 1m Fast Charge",
			"focus_key": "ACC-CBL-BAS-TC1M",
			"source_request_id": "item-detail-2",
			"source_family": "entity_detail",
			"source_capability": "item_sales_detail",
			"source_report": "Item Detail",
			"deictic_allowed": True,
			"explicit_named_allowed": True,
			"confidence": 0.9,
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-2",
			mode="new_query",
			requested_modes=["new_query"],
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
			latest_grounded_turn_available=True,
			reason="The follow-up depends on the latest grounded focus.",
		)

		decision_contract = _conversation_control_decision_from_recent_focus_runtime_message(
			request_id="recent-focus-2",
			raw_message="ignore that",
			runtime_message='how many stocks do we have, and in which warehouse for item "Type-C Cable 1m Fast Charge"?',
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			control_evidence_payload={
				"evidence_class": "override_discard",
				"action_id": "abandon_current_branch",
				"embedded_business_message": "",
			},
		)

		self.assertIsNone(decision_contract)

	def test_recent_focus_decision_is_suppressed_by_option_list_control_evidence(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "entity",
			"focus_grain": "item",
			"focus_label": "Type-C Cable 1m Fast Charge",
			"focus_key": "ACC-CBL-BAS-TC1M",
			"source_request_id": "item-detail-3",
			"source_family": "entity_detail",
			"source_capability": "item_sales_detail",
			"source_report": "Item Detail",
			"deictic_allowed": True,
			"explicit_named_allowed": True,
			"confidence": 0.9,
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-3",
			mode="new_query",
			requested_modes=["new_query"],
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
			latest_grounded_turn_available=True,
			reason="The follow-up depends on the latest grounded focus.",
		)

		decision_contract = _conversation_control_decision_from_recent_focus_runtime_message(
			request_id="recent-focus-3",
			raw_message="show me the list",
			runtime_message='how many stocks do we have, and in which warehouse for item "Type-C Cable 1m Fast Charge"?',
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			control_evidence_payload={
				"evidence_class": "option_list_request",
				"action_id": "show_pending_options",
				"embedded_business_message": "",
			},
		)

		self.assertIsNone(decision_contract)

	def test_recent_focus_decision_is_suppressed_by_fresh_request_override_control_evidence(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "entity",
			"focus_grain": "item",
			"focus_label": "Type-C Cable 1m Fast Charge",
			"focus_key": "ACC-CBL-BAS-TC1M",
			"source_request_id": "item-detail-4",
			"source_family": "entity_detail",
			"source_capability": "item_sales_detail",
			"source_report": "Item Detail",
			"deictic_allowed": True,
			"explicit_named_allowed": True,
			"confidence": 0.9,
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-4",
			mode="new_query",
			requested_modes=["new_query"],
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
			latest_grounded_turn_available=True,
			reason="The follow-up depends on the latest grounded focus.",
		)

		decision_contract = _conversation_control_decision_from_recent_focus_runtime_message(
			request_id="recent-focus-4",
			raw_message="ignore that, show me suppliers",
			runtime_message='how many stocks do we have, and in which warehouse for item "Type-C Cable 1m Fast Charge"?',
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			control_evidence_payload={
				"evidence_class": "fresh_request_redirect",
				"action_id": "override_with_new_request",
				"embedded_business_message": "show me suppliers",
			},
		)

		self.assertIsNone(decision_contract)

	def test_recent_focus_decision_is_suppressed_by_sequence_resume_control_evidence(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "entity",
			"focus_grain": "item",
			"focus_label": "Type-C Cable 1m Fast Charge",
			"focus_key": "ACC-CBL-BAS-TC1M",
			"source_request_id": "item-detail-5",
			"source_family": "entity_detail",
			"source_capability": "item_sales_detail",
			"source_report": "Item Detail",
			"deictic_allowed": True,
			"explicit_named_allowed": True,
			"confidence": 0.9,
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-5",
			mode="new_query",
			requested_modes=["new_query"],
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
			latest_grounded_turn_available=True,
			reason="The follow-up depends on the latest grounded focus.",
		)

		decision_contract = _conversation_control_decision_from_recent_focus_runtime_message(
			request_id="recent-focus-5",
			raw_message="continue",
			runtime_message='how many stocks do we have, and in which warehouse for item "Type-C Cable 1m Fast Charge"?',
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			control_evidence_payload={
				"evidence_class": "sequence_continuation",
				"action_id": "resume_active_sequence",
				"embedded_business_message": "",
			},
		)

		self.assertIsNone(decision_contract)

	def test_conversation_control_decision_maps_repair_guidance(self):
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-guidance-1",
			session_id="phase8a",
			source_request_id="grounded-guidance-1",
			source_family_id="product_rankings",
			source_capability_id="top_products_by_revenue",
			source_report="Top Products by Revenue",
			recovery_state="recoverable",
			available_recovery_actions=["run_alternative_governed_query"],
			recommended_recovery_action="run_alternative_governed_query",
			allowed_to_recover=True,
			confidence=0.93,
		).to_payload()
		repair_payload = build_conversational_repair_intent_contract(
			request_id="repair-guidance-1",
			session_id="phase8a",
			repair_intent_type="guidance_request",
			repair_state="accepted",
			targets_prior_recovery=False,
			reason="User asked what can be done next.",
			allowed_next_lane="front_door",
			confidence=0.88,
		).to_payload()

		decision_contract = _conversation_control_decision_from_repair_contract(
			request_id="repair-guidance-1",
			repair_contract_payload=repair_payload,
			latest_recovery_contract=recovery_payload,
		)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_class") or "").strip(), "repair_guidance")
		self.assertEqual(str(payload.get("decision_action") or "").strip(), "answer_recovery_guidance")
		self.assertEqual(str(payload.get("target_state_class") or "").strip(), "repair_guidance")
		self.assertEqual(
			str(((payload.get("resolved_focus_target") or {}).get("focus_label")) or "").strip(),
			"Top Products by Revenue",
		)

	def test_conversation_control_decision_maps_repair_acceptance(self):
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-accept-1",
			session_id="phase8a",
			source_request_id="grounded-accept-1",
			source_family_id="customer_rankings",
			source_capability_id="top_customers_by_revenue",
			source_report="Top Customers by Revenue",
			recovery_state="recoverable",
			available_recovery_actions=["run_alternative_governed_query"],
			recommended_recovery_action="run_alternative_governed_query",
			allowed_to_recover=True,
			confidence=0.93,
		).to_payload()
		repair_payload = build_conversational_repair_intent_contract(
			request_id="repair-accept-1",
			session_id="phase8a",
			repair_intent_type="accept_recovery_action",
			repair_state="accepted",
			targets_prior_recovery=True,
			accepted_recovery_action="run_alternative_governed_query",
			reason="User accepted the governed alternative.",
			allowed_next_lane="artifact_lane",
			confidence=0.96,
		).to_payload()

		decision_contract = _conversation_control_decision_from_repair_contract(
			request_id="repair-accept-1",
			repair_contract_payload=repair_payload,
			latest_recovery_contract=recovery_payload,
		)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_class") or "").strip(), "repair_acceptance")
		self.assertEqual(str(payload.get("decision_action") or "").strip(), "run_alternative_governed_query")
		self.assertTrue(bool(payload.get("preserve_prior_branch")))
		self.assertTrue(bool(payload.get("update_recent_focus")))

	def test_prior_branch_restore_contract_payload_is_normalized(self):
		contract = build_prior_branch_restore_contract(
			request_id="prior-restore-1",
			target_branch_kind="focus",
			target_branch_label="Ko Nay Lin Mobile Center",
			target_request_id="grounded-customer-1",
			target_family="entity_detail",
			target_scope={"company": "Mingalar Mobile Distribution Co., Ltd."},
			restore_mode="restore_recent_focus",
			resumable=True,
			clear_current_pending_clarification=False,
			clear_current_active_sequence=False,
			preserve_time_context=True,
			preserve_scope=True,
			preserve_entity_dimension=True,
			reason="The user asked to return to the prior customer branch.",
			confidence=1.4,
			internal_details={"phrase_type": "branch_restore"},
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("type") or "").strip(), "qwen_prior_branch_restore_contract")
		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertTrue(bool(payload.get("resumable")))
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(float(payload.get("confidence") or 0.0), 1.0)

	def test_prior_branch_restore_contract_builds_from_pending_clarification_question_restore(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-restore-1",
					"user_question": "Which financial view would you like to see?",
				},
			},
			"active_sequence": {"active": False},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("target_branch_kind") or "").strip(), "clarification")
		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "reopen_pending_clarification")
		self.assertTrue(bool(payload.get("resumable")))

	def test_prior_branch_restore_contract_builds_after_leading_discard_preamble(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-restore-2",
					"user_question": "Which financial view would you like to see?",
				},
			},
			"active_sequence": {"active": False},
			"resumable_prior_request": {"available": False},
		}

		stripped_message = _strip_leading_control_discard_preamble(
			"forget the first question, answer the last question"
		)
		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1b",
			raw_message=stripped_message,
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("target_branch_kind") or "").strip(), "clarification")
		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "reopen_pending_clarification")
		self.assertTrue(bool(payload.get("resumable")))

	def test_question_restore_prefers_newer_recent_focus_over_older_pending_clarification(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-restore-3",
					"user_question": "Which item do you mean?",
				},
				"source_tool_index": 2,
			},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-3",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.91,
				"source_tool_index": 7,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1c",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-restore-1c",
				raw_message="forget the first question, answer the last question",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertTrue(bool(payload.get("clear_current_pending_clarification")))
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"newer_recent_focus_precedes_older_pending_clarification",
		)

	def test_question_restore_keeps_pending_clarification_when_it_is_newer_than_recent_focus(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-restore-3b",
					"user_question": "Which item do you mean?",
				},
				"source_tool_index": 8,
			},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-3b",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.91,
				"source_tool_index": 4,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1d",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(str(payload.get("target_branch_kind") or "").strip(), "clarification")
		self.assertFalse(bool(payload.get("clear_current_pending_clarification")))

	def test_question_restore_uses_recent_focus_when_no_pending_clarification_exists(self):
		snapshot = {
			"pending_clarification": {"available": False, "source_tool_index": -1},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-3c",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.91,
				"source_tool_index": 7,
			},
			"resumable_prior_request": {"available": False, "source_tool_index": -1},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1d2",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"question_restore_uses_recent_focus",
		)

	def test_question_restore_uses_resumable_prior_request_when_no_pending_clarification_exists(self):
		snapshot = {
			"pending_clarification": {"available": False, "source_tool_index": -1},
			"active_sequence": {"active": False},
			"recent_focus": {"available": False, "source_tool_index": -1},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-3c",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
				"source_tool_index": 8,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1d3",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "replay_as_fresh_governed_query")
		self.assertEqual(str(payload.get("target_family") or "").strip(), "customer_rankings")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"question_restore_uses_resumable_prior_request",
		)

	def test_question_restore_prefers_newer_resumable_prior_request_over_older_pending_clarification(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-restore-3c",
					"user_question": "Which item do you mean?",
				},
				"source_tool_index": 2,
			},
			"active_sequence": {"active": False},
			"recent_focus": {"available": False, "source_tool_index": -1},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-3d",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
				"source_tool_index": 8,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1d4",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "replay_as_fresh_governed_query")
		self.assertEqual(str(payload.get("target_family") or "").strip(), "customer_rankings")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"newer_resumable_prior_request_precedes_older_pending_clarification",
		)

	def test_question_restore_prefers_newer_recent_focus_over_resumable_prior_request(self):
		snapshot = {
			"pending_clarification": {"available": False, "source_tool_index": -1},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-3e",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.91,
				"source_tool_index": 9,
			},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-3e",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
				"source_tool_index": 5,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1d5",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"question_restore_prefers_newer_recent_focus_over_resumable_prior_request",
		)

	def test_generic_branch_restore_prefers_newer_resumable_prior_request_over_older_recent_focus(self):
		snapshot = {
			"pending_clarification": {"available": False, "source_tool_index": -1},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-5b",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.91,
				"source_tool_index": 4,
			},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-4c",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
				"source_tool_index": 9,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1g2",
			raw_message="go back",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "replay_as_fresh_governed_query")
		self.assertEqual(str(payload.get("target_family") or "").strip(), "customer_rankings")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"generic_branch_restore_prefers_newer_resumable_prior_request_over_recent_focus",
		)

	def test_generic_branch_restore_prefers_newer_recent_focus_over_older_resumable_prior_request(self):
		snapshot = {
			"pending_clarification": {"available": False, "source_tool_index": -1},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-5c",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.91,
				"source_tool_index": 10,
			},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-4d",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
				"source_tool_index": 4,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1g3",
			raw_message="go back",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"generic_branch_restore_prefers_newer_recent_focus_over_resumable_prior_request",
		)

	def test_generic_branch_restore_uses_recent_focus_when_no_pending_branch_exists(self):
		snapshot = {
			"pending_clarification": {"available": False, "source_tool_index": -1},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-4",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.91,
				"source_tool_index": 6,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1e",
			raw_message="go back",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"generic_branch_restore_uses_recent_focus",
		)

	def test_generic_branch_restore_prefers_newer_recent_focus_over_older_pending_clarification(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-restore-4",
					"user_question": "Which item do you mean?",
				},
				"source_tool_index": 1,
			},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-5",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.91,
				"source_tool_index": 9,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1f",
			raw_message="go back",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertTrue(bool(payload.get("clear_current_pending_clarification")))
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"generic_branch_restore_prefers_newer_recent_focus",
		)

	def test_generic_branch_restore_prefers_newer_resumable_prior_request_over_older_pending_clarification(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-restore-4b",
					"user_question": "Which item do you mean?",
				},
				"source_tool_index": 2,
			},
			"active_sequence": {"active": False},
			"recent_focus": {"available": False, "source_tool_index": -1},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-4b",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
				"source_tool_index": 8,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-1g",
			raw_message="go back",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "replay_as_fresh_governed_query")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Top Customers by Revenue")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"generic_branch_restore_prefers_newer_resumable_prior_request",
		)

	def test_prior_branch_restore_contract_is_suppressed_for_discarded_new_business_request(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {"active": False},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-2",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-override-1",
			raw_message="show me suppliers",
			conversation_state_snapshot=snapshot,
			control_evidence_payload={
				"evidence_class": "fresh_request_redirect",
				"action_id": "override_with_new_request",
				"embedded_business_message": "show me suppliers",
			},
		)

		self.assertIsNone(contract)

	def test_prior_branch_restore_contract_builds_from_active_sequence_restore(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {
				"active": True,
				"request_id": "sequence-restore-1",
				"status": "ordered_execution_in_progress",
				"primary_segment_message": "give me some supplier list",
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-2",
			raw_message="continue the previous sequence",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("target_branch_kind") or "").strip(), "sequence")
		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "resume_active_sequence")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "give me some supplier list")

	def test_compound_runtime_message_does_not_resume_active_sequence_for_new_business_override(self):
		active_payload = build_compound_request_assessment_contract(
			request_id="compound-runtime-override-1",
			status="ordered_execution_in_progress",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": ["give me some supplier list"],
			},
		).to_payload()

		runtime_message, active_sequence_payload = _resolve_compound_execution_runtime_message(
			raw_message="ignore that, show me suppliers",
			frontdoor_contract=types.SimpleNamespace(response_payload={}),
			latest_compound_assessment_payload=active_payload,
			control_evidence_payload={
				"evidence_class": "fresh_request_redirect",
				"action_id": "override_with_new_request",
				"embedded_business_message": "show me suppliers",
			},
		)

		self.assertEqual(runtime_message, "")
		self.assertEqual(active_sequence_payload, {})

	def test_prior_branch_restore_contract_builds_from_control_evidence_sequence_restore(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {
				"active": True,
				"request_id": "sequence-restore-2",
				"status": "ordered_execution_in_progress",
				"primary_segment_message": "give me some customer list",
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-2b",
			raw_message="please do it",
			conversation_state_snapshot=snapshot,
			control_evidence_payload={
				"action_id": "resume_active_sequence",
			},
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("target_branch_kind") or "").strip(), "sequence")
		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "resume_active_sequence")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "give me some customer list")

	def test_prior_branch_restore_contract_builds_from_resumable_prior_branch(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {"active": False},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-1",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-3",
			raw_message="go back",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("target_branch_kind") or "").strip(), "accepted_recovery_origin")
		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "replay_as_fresh_governed_query")
		self.assertEqual(str(payload.get("target_family") or "").strip(), "customer_rankings")

	def test_generic_branch_restore_prefers_pending_clarification_over_resumable_prior_branch(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-restore-priority-1",
					"user_question": "Which financial view would you like to see?",
				},
			},
			"active_sequence": {"active": False},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-3",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-priority-1",
			raw_message="go back",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("target_branch_kind") or "").strip(), "clarification")
		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(str(payload.get("target_request_id") or "").strip(), "clarify-restore-priority-1")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"pending_clarification_precedes_generic_prior_branch_restore",
		)

	def test_conversation_control_decision_maps_prior_branch_restore(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-decision-1",
			target_branch_kind="clarification",
			target_branch_label="Which financial view would you like to see?",
			target_request_id="clarify-restore-1",
			target_family="clarification",
			restore_mode="reopen_pending_clarification",
			resumable=True,
			reason="The user asked to return to the last pending clarification question.",
			confidence=0.95,
		)

		decision_contract = _conversation_control_decision_from_prior_branch_restore_contract(restore_contract)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_class") or "").strip(), "prior_branch_restore")
		self.assertEqual(str(payload.get("decision_action") or "").strip(), "reopen_pending_clarification")
		self.assertTrue(bool(payload.get("preserve_prior_branch")))

	def test_conversation_control_decision_maps_recent_focus_restore_with_normalized_focus_fields(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-decision-2",
			target_branch_kind="focus",
			target_branch_label="Ko Nay Lin Mobile Center",
			target_request_id="grounded-customer-restore-1",
			target_family="entity_detail",
			target_scope={
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_report": "Customer Detail",
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent customer focus.",
			confidence=0.93,
		)

		decision_contract = _conversation_control_decision_from_prior_branch_restore_contract(restore_contract)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_action") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(((payload.get("resolved_focus_target") or {}).get("focus_grain")) or "").strip(), "customer")
		self.assertEqual(str(((payload.get("resolved_focus_target") or {}).get("focus_label")) or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(str(((payload.get("resolved_focus_target") or {}).get("source_report")) or "").strip(), "Customer Detail")

	def test_prior_branch_restore_runtime_message_uses_entity_detail_shape(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-1",
			target_branch_kind="focus",
			target_branch_label="Ko Nay Lin Mobile Center",
			target_request_id="grounded-customer-restore-2",
			target_family="entity_detail",
			target_scope={
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_report": "Customer Detail",
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent customer focus.",
			confidence=0.93,
		)

		self.assertEqual(
			_prior_branch_restore_runtime_message(restore_contract),
			"tell me more about Ko Nay Lin Mobile Center",
		)

	def test_prior_branch_restore_runtime_message_uses_statement_shape(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-2",
			target_branch_kind="focus",
			target_branch_label="Balance Sheet",
			target_request_id="grounded-statement-restore-1",
			target_family="financial_statement",
			target_scope={
				"focus_kind": "statement",
				"focus_grain": "balance_sheet",
				"focus_key": "Balance Sheet",
				"source_report": "Balance Sheet",
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent statement focus.",
			confidence=0.89,
		)

		self.assertEqual(
			_prior_branch_restore_runtime_message(restore_contract),
			"show me Balance Sheet",
		)

	def test_prior_branch_restore_runtime_override_message_uses_sequence_label(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-3",
			target_branch_kind="sequence",
			target_branch_label="give me some supplier list",
			target_request_id="compound-restore-1",
			target_family="active_sequence",
			target_scope={},
			restore_mode="resume_active_sequence",
			resumable=True,
			reason="The user asked to continue the remaining sequence.",
			confidence=0.91,
		)

		self.assertEqual(
			_prior_branch_restore_runtime_override_message(restore_contract),
			"give me some supplier list",
		)

	def test_prior_branch_restore_runtime_override_message_uses_recent_focus_message(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-4",
			target_branch_kind="focus",
			target_branch_label="Ko Nay Lin Mobile Center",
			target_request_id="grounded-customer-restore-3",
			target_family="entity_detail",
			target_scope={
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_report": "Customer Detail",
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent customer focus.",
			confidence=0.93,
		)

		self.assertEqual(
			_prior_branch_restore_runtime_override_message(restore_contract),
			"tell me more about Ko Nay Lin Mobile Center",
		)

	def test_prior_branch_restore_runtime_override_message_is_empty_for_reopen_pending(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-5",
			target_branch_kind="clarification",
			target_branch_label="Which financial view would you like to see?",
			target_request_id="clarify-runtime-1",
			target_family="clarification",
			target_scope={},
			restore_mode="reopen_pending_clarification",
			resumable=True,
			reason="The user asked to reopen the pending clarification.",
			confidence=0.95,
		)

		self.assertEqual(_prior_branch_restore_mode(restore_contract), "reopen_pending_clarification")
		self.assertEqual(_prior_branch_restore_runtime_override_message(restore_contract), "")

	def test_handle_prior_branch_restore_reopen_pending_clarification_returns_direct_payload(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-6",
			target_branch_kind="clarification",
			target_branch_label="Which financial view would you like to see?",
			target_request_id="clarify-runtime-2",
			target_family="clarification",
			target_scope={},
			restore_mode="reopen_pending_clarification",
			resumable=True,
			reason="The user asked to reopen the pending clarification.",
			confidence=0.95,
		)

		class _PayloadContract:
			def __init__(self, payload: Dict[str, Any]):
				self._payload = dict(payload)

			def to_payload(self):
				return dict(self._payload)

		with patch("ai_assistant_ui.qwen_chat.service._append_message"), patch(
			"ai_assistant_ui.qwen_chat.service._append_tool_payload"
		), patch(
			"ai_assistant_ui.qwen_chat.service._save_session"
		):
			handled, payload = _handle_prior_branch_restore_reopen_pending_clarification(
				session_doc=object(),
				request_id="prior-restore-runtime-6",
				raw_message="answer the last question",
				interaction_contract=_PayloadContract({"type": "interaction"}),
				conversation_control_evidence_contract=_PayloadContract({"type": "control_evidence"}),
				prior_branch_restore_contract=restore_contract,
				prior_branch_restore_control_decision_contract=_PayloadContract({"type": "restore_decision"}),
				pending_clarification_signal=_clarification_signal(
					request_id="clarify-runtime-2",
					user_question="Which financial view would you like to see?",
				),
			)

		self.assertTrue(handled)
		self.assertEqual(str((payload or {}).get("mode") or "").strip(), "clarification")
		self.assertEqual(
			str((((payload or {}).get("agent_meta") or {}).get("intent_class")) or "").strip(),
			"reopen_pending_clarification",
		)

	def test_conversation_control_evidence_contract_payload_is_normalized(self):
		contract = build_conversation_control_evidence_contract(
			request_id="control-evidence-1",
			evidence_class="fresh_request_redirect",
			action_id="override_with_new_request",
			evidence_strength="strong",
			raw_message="ignore that, show me suppliers",
			normalized_message="ignore that show me suppliers",
			matched_surface_form="ignore that, show me suppliers",
			embedded_business_message="show me suppliers",
			reason="Shared conversation-control evidence was derived from the user message.",
			internal_details={"source_contract_type": "qwen_conversation_control_language_classifier"},
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("type") or "").strip(), "qwen_conversation_control_evidence_contract")
		self.assertEqual(str(payload.get("evidence_class") or "").strip(), "fresh_request_redirect")
		self.assertEqual(str(payload.get("action_id") or "").strip(), "override_with_new_request")
		self.assertEqual(str(payload.get("embedded_business_message") or "").strip(), "show me suppliers")

	def test_build_conversation_control_evidence_contract_uses_shared_classifier(self):
		contract = _build_conversation_control_evidence_contract(
			request_id="control-evidence-2",
			raw_message="ignore that, show me suppliers",
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("evidence_class") or "").strip(), "fresh_request_redirect")
		self.assertEqual(str(payload.get("action_id") or "").strip(), "override_with_new_request")
		self.assertEqual(str(payload.get("embedded_business_message") or "").strip(), "show me suppliers")

	def test_strip_leading_control_discard_preamble_returns_business_remainder(self):
		self.assertEqual(
			_strip_leading_control_discard_preamble("forget the first question, answer the last question"),
			"answer the last question",
		)
		self.assertEqual(
			_strip_leading_control_discard_preamble("ignore that and show me suppliers"),
			"show me suppliers",
		)
		self.assertEqual(
			_strip_leading_control_discard_preamble("show me suppliers"),
			"",
		)

	def test_shared_control_language_reclassifies_discard_prefix_into_question_restore(self):
		evidence = classify_conversation_control_evidence("forget the first question, answer the last question")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(str(evidence.get("embedded_business_message") or "").strip(), "")
		self.assertTrue(bool((evidence.get("internal_details") or {}).get("discard_prefix_applied")))

	def test_shared_control_language_supports_additional_question_restore_variants(self):
		last_one = classify_conversation_control_evidence("answer the last one")
		previous_one = classify_conversation_control_evidence("repeat the previous one")

		self.assertEqual(str(last_one.get("action_id") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(str(previous_one.get("action_id") or "").strip(), "reopen_pending_clarification")

	def test_shared_control_language_reclassifies_discard_prefix_into_new_question_restore_variant(self):
		evidence = classify_conversation_control_evidence("forget that, answer the last one")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "reopen_pending_clarification")
		self.assertTrue(bool((evidence.get("internal_details") or {}).get("discard_prefix_applied")))

	def test_shared_control_language_reclassifies_discard_prefix_into_option_list_request(self):
		evidence = classify_conversation_control_evidence("ignore that, show me the list")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "show_pending_options")
		self.assertEqual(str(evidence.get("embedded_business_message") or "").strip(), "")
		self.assertTrue(bool((evidence.get("internal_details") or {}).get("discard_prefix_applied")))

	def test_shared_control_language_classifies_option_list_request(self):
		evidence = classify_conversation_control_evidence("show me the list that you found")
		self.assertEqual(str(evidence.get("evidence_class") or "").strip(), "option_list_request")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "show_pending_options")
		self.assertTrue(shared_looks_like_option_list_request("show me the list that you found"))

	def test_shared_control_language_supports_additional_option_list_variants(self):
		list_you_found = classify_conversation_control_evidence("show me the list you found")
		options_you_found = classify_conversation_control_evidence("show the options you found")
		what_are_options = classify_conversation_control_evidence("what are the options")

		self.assertEqual(str(list_you_found.get("action_id") or "").strip(), "show_pending_options")
		self.assertEqual(str(options_you_found.get("action_id") or "").strip(), "show_pending_options")
		self.assertEqual(str(what_are_options.get("action_id") or "").strip(), "show_pending_options")
		self.assertTrue(shared_looks_like_option_list_request("show me the list you found"))

	def test_shared_control_language_reclassifies_discard_prefix_into_new_option_list_variant(self):
		evidence = classify_conversation_control_evidence("forget that, show the options you found")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "show_pending_options")
		self.assertTrue(bool((evidence.get("internal_details") or {}).get("discard_prefix_applied")))

	def test_shared_control_language_classifies_sequence_continuation_and_stop(self):
		continue_evidence = classify_conversation_control_evidence("go ahead")
		stop_evidence = classify_conversation_control_evidence("not now")

		self.assertEqual(str(continue_evidence.get("action_id") or "").strip(), "resume_active_sequence")
		self.assertEqual(str(continue_evidence.get("evidence_class") or "").strip(), "sequence_continuation")
		self.assertEqual(str(stop_evidence.get("action_id") or "").strip(), "stop_active_sequence")
		self.assertEqual(str(stop_evidence.get("evidence_class") or "").strip(), "sequence_stop")

	def test_shared_control_language_classifies_redirect_with_embedded_business_request(self):
		evidence = classify_conversation_control_evidence("ignore that, show me suppliers")
		self.assertEqual(str(evidence.get("evidence_class") or "").strip(), "fresh_request_redirect")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "override_with_new_request")
		self.assertEqual(str(evidence.get("embedded_business_message") or "").strip(), "show me suppliers")

	def test_shared_control_language_classifies_targeted_branch_restore(self):
		evidence = classify_conversation_control_evidence("go back to the customer")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "replay_or_restore_prior_branch")
		self.assertEqual(
			str((evidence.get("internal_details") or {}).get("target_grain") or "").strip(),
			"customer",
		)

	def test_shared_control_language_reclassifies_discard_prefix_into_targeted_branch_restore(self):
		evidence = classify_conversation_control_evidence("forget that, go back to the customer")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "replay_or_restore_prior_branch")
		self.assertEqual(
			str((evidence.get("internal_details") or {}).get("target_grain") or "").strip(),
			"customer",
		)
		self.assertTrue(bool((evidence.get("internal_details") or {}).get("discard_prefix_applied")))

	def test_build_conversation_control_evidence_contract_keeps_targeted_restore_metadata(self):
		contract = _build_conversation_control_evidence_contract(
			request_id="control-evidence-targeted-1",
			raw_message="go back to the customer",
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("action_id") or "").strip(), "replay_or_restore_prior_branch")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("target_grain") or "").strip(),
			"customer",
		)

	def test_targeted_branch_restore_prefers_matching_recent_focus_over_pending_clarification(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-targeted-1",
					"user_question": "Which item do you mean?",
				},
			},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-target-1",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.92,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-focus-1",
			raw_message="go back to the customer",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-2",
				raw_message="go back to the customer",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"targeted_recent_focus_restore",
		)

	def test_targeted_branch_restore_prefers_matching_recent_focus_without_explicit_control_payload(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-targeted-1b",
					"user_question": "Which item do you mean?",
				},
			},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-target-1b",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.92,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-focus-1b",
			raw_message="go back to the customer",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")

	def test_targeted_branch_restore_fails_closed_when_no_matching_target_exists(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-targeted-2",
					"user_question": "Which item do you mean?",
				},
			},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "item",
				"focus_label": "Type-C Cable 1m Fast Charge",
				"focus_key": "ACC-CBL-BAS-TC1M",
				"source_request_id": "grounded-item-target-1",
				"source_family": "entity_detail",
				"source_capability": "item_sales_detail",
				"source_report": "Item Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.91,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-focus-2",
			raw_message="go back to the customer",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-3",
				raw_message="go back to the customer",
			).to_payload(),
		)

		self.assertIsNone(contract)

	def test_targeted_branch_restore_builds_from_matching_resumable_prior_request(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {"active": False},
			"recent_focus": {"available": False},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Customer Ranking Branch",
				"source_request_id": "grounded-customer-ranking-1",
				"target_family": "customer_rankings",
				"target_scope": {"requested_top_n": 10},
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.84,
				"internal_details": {
					"prior_recovery_payload": {
						"source_report": "Top Customers by Revenue",
						"source_family_id": "customer_rankings",
						"preservable_scope": {"requested_top_n": 10},
					},
				},
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-prior-1",
			raw_message="go back to the customer",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-4",
				raw_message="go back to the customer",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "replay_as_fresh_governed_query")
		self.assertEqual(str(payload.get("target_family") or "").strip(), "customer_rankings")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"targeted_resumable_prior_branch_restore",
		)

	def test_discard_prefixed_targeted_branch_restore_keeps_target_metadata(self):
		evidence_contract = _build_conversation_control_evidence_contract(
			request_id="control-evidence-targeted-5",
			raw_message="ignore that, go back to the customer",
		)
		payload = evidence_contract.to_payload()

		self.assertEqual(str(payload.get("action_id") or "").strip(), "replay_or_restore_prior_branch")
		self.assertTrue(bool((payload.get("internal_details") or {}).get("discard_prefix_applied")))
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("target_grain") or "").strip(),
			"customer",
		)

	def test_discard_prefixed_targeted_branch_restore_builds_recent_focus_restore(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-targeted-3",
					"user_question": "Which item do you mean?",
				},
			},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-target-2",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.92,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-focus-3",
			raw_message="ignore that, go back to the customer",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-6",
				raw_message="ignore that, go back to the customer",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")

	def test_targeted_statement_restore_builds_recent_focus_restore(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "statement",
				"focus_grain": "balance_sheet",
				"focus_label": "Balance Sheet",
				"focus_key": "Balance Sheet",
				"source_request_id": "grounded-statement-target-1",
				"source_family": "financial_statement",
				"source_capability": "",
				"source_report": "Balance Sheet",
				"deictic_allowed": False,
				"explicit_named_allowed": True,
				"derivation_basis": "statement_grounded_turn",
				"confidence": 0.85,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-focus-4",
			raw_message="go back to the balance sheet",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-7",
				raw_message="go back to the balance sheet",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_family") or "").strip(), "financial_statement")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Balance Sheet")

	def test_targeted_statement_restore_builds_without_explicit_control_payload(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "statement",
				"focus_grain": "balance_sheet",
				"focus_label": "Balance Sheet",
				"focus_key": "Balance Sheet",
				"source_request_id": "grounded-statement-target-1b",
				"source_family": "financial_statement",
				"source_capability": "",
				"source_report": "Balance Sheet",
				"deictic_allowed": False,
				"explicit_named_allowed": True,
				"derivation_basis": "statement_grounded_turn",
				"confidence": 0.85,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-focus-4b",
			raw_message="go back to the balance sheet",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Balance Sheet")

	def test_recent_focus_decision_is_suppressed_by_targeted_branch_restore_control_evidence(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "entity",
			"focus_grain": "customer",
			"focus_label": "Ko Nay Lin Mobile Center",
			"focus_key": "Ko Nay Lin Mobile Center",
			"source_request_id": "customer-detail-restore-suppress-1",
			"source_family": "entity_detail",
			"source_capability": "customer_sales_detail",
			"source_report": "Customer Detail",
			"deictic_allowed": True,
			"explicit_named_allowed": True,
			"confidence": 0.92,
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-restore-suppress-1",
			mode="new_query",
			requested_modes=["new_query"],
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
			latest_grounded_turn_available=True,
			reason="The follow-up depends on the latest grounded focus.",
		)

		decision_contract = _conversation_control_decision_from_recent_focus_runtime_message(
			request_id="recent-focus-restore-suppress-1",
			raw_message="go back to the customer",
			runtime_message="tell me more about Ko Nay Lin Mobile Center",
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-suppress-1",
				raw_message="go back to the customer",
			).to_payload(),
		)

		self.assertIsNone(decision_contract)

	def test_prior_branch_restore_fresh_query_routes_through_compiled_execution(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-live-1",
			target_branch_kind="accepted_recovery_origin",
			target_branch_label="Top Customers by Revenue",
			target_request_id="grounded-prior-turn",
			target_family="ranked_entity_analytics",
			target_scope={"requested_top_n": 10},
			restore_mode="replay_as_fresh_governed_query",
			resumable=True,
			reason="The user chose to rerun a prior governed branch.",
			confidence=0.94,
			internal_details={
				"prior_recovery_payload": {
					"source_report": "Top Customers by Revenue",
					"source_family_id": "ranked_entity_analytics",
					"preservable_scope": {"requested_top_n": 10},
				},
			},
		)
		restore_decision = _conversation_control_decision_from_prior_branch_restore_contract(restore_contract)

		class _PayloadContract:
			def __init__(self, payload: Dict[str, Any]):
				self._payload = dict(payload)

			def to_payload(self):
				return dict(self._payload)

		compiled_result = {"ok": True, "rows": []}
		expected_payload = {"ok": True, "mode": "fresh_query"}

		with patch("ai_assistant_ui.qwen_chat.service._append_message"), patch(
			"ai_assistant_ui.qwen_chat.service._append_tool_payload"
		), patch(
			"ai_assistant_ui.qwen_chat.service.execute_compiled_fresh_query_message",
			return_value=compiled_result,
		) as execute_mock, patch(
			"ai_assistant_ui.qwen_chat.service._handle_compiled_first_turn_result",
			return_value=(True, expected_payload),
		) as handle_result_mock:
			handled, payload = _handle_prior_branch_restore_fresh_query(
				session_doc=object(),
				request_id="prior-restore-live-1",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				raw_message="go back",
				interaction_contract=_PayloadContract({"type": "interaction"}),
				conversation_control_evidence_contract=_PayloadContract({"type": "control_evidence"}),
				frontdoor_semantic_result=_PayloadContract({"type": "frontdoor_semantic"}),
				frontdoor_contract=_PayloadContract({"type": "frontdoor_contract"}),
				clarification_response_contract=None,
				response_policy_contract=_PayloadContract({"type": "response_policy"}),
				prior_branch_restore_contract=restore_contract,
				prior_branch_restore_control_decision_contract=restore_decision,
			)

		self.assertTrue(handled)
		self.assertEqual(payload, expected_payload)
		execute_kwargs = execute_mock.call_args.kwargs
		self.assertEqual(str(execute_kwargs.get("message") or "").strip(), "show me top 10 customers by revenue")
		self.assertEqual(int(execute_kwargs.get("governed_target_limit") or 0), 10)
		handle_kwargs = handle_result_mock.call_args.kwargs
		self.assertEqual(handle_kwargs.get("result"), compiled_result)
		self.assertEqual(
			str(getattr(handle_kwargs.get("execution_path"), "path", "") or "").strip(),
			"prior_branch_restore_requery",
		)

	def test_conversation_control_decision_contract_payload_is_normalized(self):
		contract = build_conversation_control_decision_contract(
			request_id="control-decision-1",
			decision_class="fresh_request_override",
			decision_action="override_with_new_request",
			target_state_class="pending_clarification",
			resolved_business_message="show me suppliers",
			resolved_focus_target={"focus_grain": "supplier", "focus_label": "Myanmar Tech Import Services"},
			resolved_sequence_target={"sequence_id": "seq-1"},
			clear_pending_clarification=True,
			clear_active_sequence=False,
			update_recent_focus=False,
			preserve_prior_branch=True,
			confidence=1.7,
			reason="The user explicitly started a fresh business request.",
			internal_details={"evidence_class": "fresh_business_request"},
		)

		payload = contract.to_payload()

		self.assertEqual(str(payload.get("type") or "").strip(), "qwen_conversation_control_decision_contract")
		self.assertEqual(str(payload.get("decision_class") or "").strip(), "fresh_request_override")
		self.assertEqual(str(payload.get("decision_action") or "").strip(), "override_with_new_request")
		self.assertEqual(str(payload.get("target_state_class") or "").strip(), "pending_clarification")
		self.assertEqual(str(payload.get("resolved_business_message") or "").strip(), "show me suppliers")
		self.assertTrue(bool(payload.get("clear_pending_clarification")))
		self.assertFalse(bool(payload.get("clear_active_sequence")))
		self.assertTrue(bool(payload.get("preserve_prior_branch")))
		self.assertEqual(float(payload.get("confidence") or 0.0), 1.0)
		self.assertEqual(
			str(((payload.get("resolved_focus_target") or {}).get("focus_label")) or "").strip(),
			"Myanmar Tech Import Services",
		)
		self.assertEqual(
			str(((payload.get("resolved_sequence_target") or {}).get("sequence_id")) or "").strip(),
			"seq-1",
		)

	def test_conversation_state_snapshot_empty_fails_closed(self):
		session_doc = _FakeSessionDoc()

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-empty",
			session_doc=session_doc,
		)

		self.assertEqual(snapshot.get("type"), "qwen_conversation_state_snapshot")
		self.assertEqual(snapshot.get("snapshot_version"), "1.0")
		self.assertFalse(bool((snapshot.get("pending_clarification") or {}).get("available")))
		self.assertFalse(bool((snapshot.get("latest_grounded_turn") or {}).get("available")))
		self.assertFalse(bool((snapshot.get("latest_artifact") or {}).get("available")))
		self.assertFalse(bool((snapshot.get("latest_recovery_contract") or {}).get("available")))
		self.assertFalse(bool((snapshot.get("active_sequence") or {}).get("available")))
		self.assertFalse(bool((snapshot.get("recent_focus") or {}).get("available")))
		self.assertFalse(bool((snapshot.get("resumable_prior_request") or {}).get("available")))
		self.assertFalse(bool((snapshot.get("state_quality") or {}).get("has_grounded_turn")))

	def test_conversation_state_snapshot_prefers_stored_pending_clarification(self):
		session_doc = _FakeSessionDoc()
		stored_signal = _clarification_signal(
			request_id="clarify-stored",
			user_question="Which report do you want?",
		)
		message_fallback_signal = _clarification_signal(
			request_id="clarify-message-fallback",
			user_question="Which time scope do you want?",
		)
		session_doc._messages = [
			_FakeMessage(role="assistant", content=message_fallback_signal["user_question"]),
			_FakeMessage(role="tool", content=json.dumps(message_fallback_signal)),
		]
		store_pending_clarification_signal(session_doc, stored_signal, attempt_count=1, max_attempts=3)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-pending",
			session_doc=session_doc,
		)
		pending = snapshot.get("pending_clarification") or {}

		self.assertTrue(bool(pending.get("available")))
		self.assertEqual(str(pending.get("source_kind") or "").strip(), "stored_state")
		self.assertEqual(str((pending.get("signal") or {}).get("request_id") or "").strip(), "clarify-stored")
		self.assertEqual(int(pending.get("attempt_count") or 0), 1)
		self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_authoritative_pending_clarification")))

	def test_conversation_state_snapshot_captures_source_tool_indexes_for_recency_arbitration(self):
		pending_signal = _clarification_signal(
			request_id="clarify-recency-1",
			user_question="Which item do you mean?",
		)
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-recency-1",
			"trace_request_id": "grounded-recency-1-trace",
			"grounded": True,
			"source_name": "Ko Nay Lin Mobile Center Detail",
			"artifact_family_id": "entity_detail",
			"known_entities": [
				{
					"entity_type": "customer",
					"entity_label": "Ko Nay Lin Mobile Center",
					"entity_key": "Ko Nay Lin Mobile Center",
				}
			],
		}
		matching_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "grounded-recency-1-trace",
			"family_id": "entity_detail",
			"source_reports": ["Ko Nay Lin Mobile Center Detail"],
			"artifact_type": "normalized_family_artifact",
			"dimensions": {
				"entity_type": "customer",
				"entity_label": "Ko Nay Lin Mobile Center",
				"entity_key": "Ko Nay Lin Mobile Center",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(pending_signal)),
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(matching_artifact_payload)),
			]
		)
		store_pending_clarification_signal(session_doc, pending_signal, attempt_count=0, max_attempts=3)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-recency-1",
			session_doc=session_doc,
		)
		pending = snapshot.get("pending_clarification") or {}
		grounded = snapshot.get("latest_grounded_turn") or {}
		recent_focus = snapshot.get("recent_focus") or {}

		self.assertEqual(int(pending.get("source_tool_index") or -1), 0)
		self.assertEqual(int(grounded.get("source_tool_index") or -1), 1)
		self.assertEqual(int(recent_focus.get("source_tool_index") or -1), 1)

	def test_conversation_state_snapshot_marks_grounded_compatible_artifact(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-snapshot-1",
			"trace_request_id": "grounded-snapshot-1-trace",
			"grounded": True,
			"source_name": "Accounts Receivable Summary",
			"artifact_family_id": "receivable_summary",
			"artifact_source_reports": ["Accounts Receivable Summary"],
		}
		matching_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "grounded-snapshot-1-trace",
			"family_id": "receivable_summary",
			"source_reports": ["Accounts Receivable Summary"],
			"artifact_type": "normalized_family_artifact",
		}
		incompatible_later_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "other-trace",
			"family_id": "payable_summary",
			"source_reports": ["Accounts Payable Summary"],
			"artifact_type": "normalized_family_artifact",
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(matching_artifact_payload)),
				_FakeMessage(role="tool", content=json.dumps(incompatible_later_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-grounded-artifact",
			session_doc=session_doc,
		)
		grounded = snapshot.get("latest_grounded_turn") or {}
		artifact = snapshot.get("latest_artifact") or {}

		self.assertTrue(bool(grounded.get("available")))
		self.assertTrue(bool(grounded.get("grounded")))
		self.assertTrue(bool(artifact.get("available")))
		self.assertTrue(bool(artifact.get("grounded_compatible")))
		self.assertEqual(str(artifact.get("source_quality") or "").strip(), "grounded_compatible")
		self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_grounded_compatible_artifact")))

	def test_conversation_state_snapshot_normalizes_active_sequence(self):
		active_sequence_payload = build_compound_request_assessment_contract(
			request_id="compound-active-1",
			status="ordered_execution_active",
			segments=["show me payment entries", "give me some customer list"],
			clarification_required=False,
			reason="Two ordered steps were identified.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "show me payment entries",
				"remaining_segment_messages": ["give me some customer list"],
			},
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(active_sequence_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-sequence-active",
			session_doc=session_doc,
		)
		active_sequence = snapshot.get("active_sequence") or {}

		self.assertTrue(bool(active_sequence.get("available")))
		self.assertTrue(bool(active_sequence.get("active")))
		self.assertEqual(str(active_sequence.get("primary_segment_message") or "").strip(), "show me payment entries")
		self.assertEqual(
			list(active_sequence.get("remaining_segment_messages") or []),
			["give me some customer list"],
		)
		self.assertEqual(int(active_sequence.get("source_tool_index") or -1), 0)
		self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_active_sequence")))

	def test_conversation_state_snapshot_recent_focus_derives_from_entity_detail(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "entity-grounded-1",
			"trace_request_id": "entity-grounded-1-trace",
			"grounded": True,
			"source_kind": "entity_detail",
			"source_name": "Ko Nay Lin Mobile Center Detail",
			"artifact_family_id": "entity_detail",
			"artifact_source_reports": ["Ko Nay Lin Mobile Center Detail"],
		}
		entity_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "entity-grounded-1-trace",
			"family_id": "entity_detail",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Ko Nay Lin Mobile Center Detail"],
			"dimensions": {
				"entity_type": "customer",
				"entity_label": "Ko Nay Lin Mobile Center",
				"entity_key": "Ko Nay Lin Mobile Center",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(entity_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-recent-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "entity")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "customer")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "entity_detail_grounded_turn")
		self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_recent_focus")))

	def test_recent_focus_affordance_builder_for_item_entity_detail(self):
		contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-item-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "item",
				"focus_label": "Type-C Cable 1m Fast Charge",
				"focus_key": "ACC-CBL-BAS-TC1M",
				"source_request_id": "item-detail-1",
				"source_family": "entity_detail",
				"source_capability": "item_sales_detail",
				"source_report": "Item Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("focus_kind") or "").strip(), "entity")
		self.assertEqual(str(payload.get("focus_grain") or "").strip(), "item")
		self.assertIn("detail_followup", list(payload.get("allowed_action_classes") or []))
		self.assertIn("inventory_position_followup", list(payload.get("allowed_action_classes") or []))
		self.assertTrue(bool(payload.get("deictic_reference_allowed")))

	def test_conversation_state_snapshot_recent_focus_derives_from_master_data_listing(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "supplier-list-grounded-1",
			"trace_request_id": "supplier-list-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Supplier Master List",
			"artifact_family_id": "master_data_directory",
			"artifact_source_reports": ["Supplier Master List"],
		}
		list_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "supplier-list-grounded-1-trace",
			"family_id": "master_data_directory",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Supplier Master List"],
			"dimensions": {
				"entity_type": "supplier",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(list_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-supplier-list-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "supplier")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "master_data_listing_grounded_turn")
		self.assertEqual(str(affordance.get("type") or "").strip(), "qwen_recent_focus_affordance_contract")
		self.assertIn("entity_selection_followup", list(affordance.get("allowed_action_classes") or []))
		self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_recent_focus_affordance")))

	def test_conversation_state_snapshot_recent_focus_derives_from_report_view(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "ranking-grounded-1",
			"trace_request_id": "ranking-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Top Products by Revenue",
			"artifact_family_id": "ranking_analytics",
			"artifact_source_reports": ["Top Products by Revenue"],
		}
		ranking_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "ranking-grounded-1-trace",
			"family_id": "ranking_analytics",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Top Products by Revenue"],
			"dimensions": {
				"subject": "item",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(ranking_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-report-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "ranking_analytics")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn")
		self.assertIn("report_refinement", list(affordance.get("allowed_action_classes") or []))
		self.assertIn("detail_navigation", list(affordance.get("allowed_action_classes") or []))

	def test_conversation_state_snapshot_keeps_resumable_prior_request_conservative(self):
		active_sequence_payload = build_compound_request_assessment_contract(
			request_id="compound-active-2",
			status="ordered_execution_active",
			segments=["show me payment entries", "give me some customer list"],
			clarification_required=False,
			reason="Two ordered steps were identified.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "show me payment entries",
				"remaining_segment_messages": ["give me some customer list"],
			},
		).to_payload()
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-snapshot-1",
			session_id="phase8a",
			source_request_id="grounded-snapshot-1",
			source_family_id="ranking_analytics",
			source_capability_id="sales_read",
			source_report="Sales Analytics",
			recovery_state="recoverable",
			available_recovery_actions=["run_alternative_governed_query"],
			recommended_recovery_action="run_alternative_governed_query",
			allowed_to_recover=True,
			confidence=0.93,
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(active_sequence_payload)),
				_FakeMessage(role="tool", content=json.dumps(recovery_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-prior-branch",
			session_doc=session_doc,
		)
		prior_branch = snapshot.get("resumable_prior_request") or {}

		self.assertFalse(bool(prior_branch.get("available")))
		self.assertEqual(str(prior_branch.get("branch_kind") or "").strip(), "none")
		self.assertEqual(str(prior_branch.get("derivation_basis") or "").strip(), "blocked_by_higher_priority_state")
		self.assertFalse(bool((snapshot.get("state_quality") or {}).get("has_resumable_prior_request")))

	def test_latest_repair_intent_contract_returns_latest_payload(self):
		first_repair_payload = build_conversational_repair_intent_contract(
			request_id="repair-latest-1",
			session_id="phase8a",
			repair_intent_type="guidance_request",
			repair_state="accepted",
			targets_prior_recovery=False,
			reason="Older repair.",
			allowed_next_lane="front_door",
			confidence=0.7,
		).to_payload()
		second_repair_payload = build_conversational_repair_intent_contract(
			request_id="repair-latest-2",
			session_id="phase8a",
			repair_intent_type="accept_recovery_action",
			repair_state="accepted",
			targets_prior_recovery=True,
			accepted_recovery_action="run_alternative_governed_query",
			reason="Latest repair.",
			allowed_next_lane="artifact_lane",
			confidence=0.9,
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(first_repair_payload)),
				_FakeMessage(role="tool", content=json.dumps(second_repair_payload)),
			]
		)

		latest = _latest_repair_intent_contract(session_doc)
		self.assertEqual(str(latest.get("request_id") or "").strip(), "repair-latest-2")
		self.assertEqual(str(latest.get("repair_intent_type") or "").strip(), "accept_recovery_action")

	def test_conversation_state_snapshot_derives_resumable_prior_request_from_accepted_repair(self):
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-prior-1",
			session_id="phase8a",
			source_request_id="grounded-prior-trace-1",
			source_family_id="customer_rankings",
			source_capability_id="top_customers_by_revenue",
			source_report="Top Customers by Revenue",
			recovery_state="recoverable",
			available_recovery_actions=["run_alternative_governed_query"],
			recommended_recovery_action="run_alternative_governed_query",
			allowed_to_recover=True,
			confidence=0.93,
		).to_payload()
		accepted_repair_payload = build_conversational_repair_intent_contract(
			request_id="repair-prior-1",
			session_id="phase8a",
			repair_intent_type="accept_recovery_action",
			repair_state="accepted",
			targets_prior_recovery=True,
			accepted_recovery_action="run_alternative_governed_query",
			reason="User accepted the governed alternative.",
			allowed_next_lane="artifact_lane",
			confidence=0.96,
		).to_payload()
		new_grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-new-request-1",
			"trace_request_id": "grounded-new-trace-1",
			"grounded": True,
			"source_name": "Top Customers by Quantity",
			"artifact_family_id": "customer_rankings",
			"artifact_source_reports": ["Top Customers by Quantity"],
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(recovery_payload)),
				_FakeMessage(role="tool", content=json.dumps(accepted_repair_payload)),
				_FakeMessage(role="tool", content=json.dumps(new_grounded_turn_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-resumable-prior",
			session_doc=session_doc,
		)
		prior_branch = snapshot.get("resumable_prior_request") or {}
		latest_repair = snapshot.get("latest_repair_intent") or {}

		self.assertTrue(bool(prior_branch.get("available")))
		self.assertEqual(str(prior_branch.get("branch_kind") or "").strip(), "accepted_recovery_origin")
		self.assertEqual(str(prior_branch.get("branch_label") or "").strip(), "Top Customers by Revenue")
		self.assertEqual(str(prior_branch.get("source_request_id") or "").strip(), "grounded-prior-trace-1")
		self.assertEqual(
			str(prior_branch.get("derivation_basis") or "").strip(),
			"accepted_repair_with_newer_grounded_turn",
		)
		self.assertEqual(int(prior_branch.get("source_tool_index") or -1), 1)
		self.assertEqual(str(latest_repair.get("repair_intent_type") or "").strip(), "accept_recovery_action")
		self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_latest_repair_intent")))
		self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_resumable_prior_request")))

	def test_short_acknowledgement_detection_is_bounded(self):
		self.assertTrue(looks_like_short_acknowledgement("yes"))
		self.assertTrue(looks_like_short_acknowledgement("okay"))
		self.assertFalse(looks_like_short_acknowledgement("what do you mean?"))
		self.assertFalse(looks_like_short_acknowledgement("yes show me AR"))

	def test_pending_clarification_store_roundtrip_preserves_latest_signal(self):
		session_doc = _FakeSessionDoc()
		first_signal = _clarification_signal(request_id="clarify-1", user_question="Which report do you want?")
		second_signal = _clarification_signal(request_id="clarify-2", user_question="Which time scope do you want?")

		store_pending_clarification_signal(session_doc, first_signal, attempt_count=1, max_attempts=3)
		store_pending_clarification_signal(session_doc, second_signal, attempt_count=0, max_attempts=3)

		stored = get_clarification_state(session_doc)
		self.assertTrue(stored.has_pending)
		self.assertEqual(stored.pending_signal.get("request_id"), "clarify-2")
		self.assertEqual(stored.attempt_count, 0)
		self.assertEqual(latest_pending_clarification_signal(session_doc).get("request_id"), "clarify-2")

	def test_pending_clarification_repeated_unresolved_attempts_increment_only_counter(self):
		signal = _clarification_signal(request_id="clarify-3", user_question="Which warehouse do you want?")
		state = build_pending_clarification_state(signal, attempt_count=0, max_attempts=3)

		state = clarification_state_after_unresolved_attempt(state, signal)
		self.assertEqual(state.attempt_count, 1)
		self.assertEqual(state.pending_signal.get("request_id"), "clarify-3")

		state = clarification_state_after_unresolved_attempt(state, signal)
		self.assertEqual(state.attempt_count, 2)
		self.assertEqual(state.pending_signal.get("request_id"), "clarify-3")
		self.assertFalse(state.max_attempts_reached)

	def test_direct_evidence_followup_resolution_stays_grounded(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="direct-evidence-1",
			mode="capability_requery",
			requested_modes=["dimension_breakdown", "metric_refinement"],
			target_dimension="Warehouse",
			target_metric="quantity",
			target_capability_id="stock_read",
			target_report="Warehouse Wise Stock Balance",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The request appears to need a stock requery.",
		)

		preserved = _preserve_current_artifact_direct_evidence_followup_resolution(
			request_id="direct-evidence-1",
			followup_resolution=followup_resolution,
			evidence_request_contract={
				"entity_type": "item",
				"question_type": "item_stock_position",
				"clarification_required": False,
			},
			direct_evidence_answer="We currently hold 587 units across 3 warehouses.",
			evidence_boundary_answer="",
			latest_grounded_turn_available=True,
		)

		self.assertEqual(preserved.mode, "grounded_follow_up")
		self.assertEqual(preserved.target_capability_id, "")
		self.assertIn("direct_evidence_followup", list(preserved.requested_modes))
		self.assertTrue(preserved.depends_on_grounded_turn)
		self.assertFalse(preserved.self_contained)

		state = clarification_state_after_unresolved_attempt(state, signal)
		self.assertEqual(state.attempt_count, 3)
		self.assertTrue(state.max_attempts_reached)
		self.assertEqual(state.pending_signal.get("request_id"), "clarify-3")

	def test_clear_pending_clarification_signal_removes_stored_state(self):
		session_doc = _FakeSessionDoc()
		signal = _clarification_signal(request_id="clarify-4", user_question="Which business area do you want?")
		store_pending_clarification_signal(session_doc, signal, attempt_count=2, max_attempts=3)

		clear_pending_clarification_signal(session_doc)

		self.assertEqual(session_doc.pending_clarification_state_json, "")
		self.assertFalse(get_clarification_state(session_doc).has_pending)
		self.assertEqual(latest_pending_clarification_signal(session_doc), {})

	def test_pending_clarification_can_carry_frontdoor_continuation_message(self):
		signal = _clarification_signal(request_id="clarify-4c", user_question="Choose one KPI basis.")
		signal["reason_type"] = "governed_kpi_definition_ambiguity"
		signal["internal_details"] = {
			"continuation_lane": "front_door",
			"resolved_message_by_option": {
				"Average Order Value by Sales Order": "what is Average Order Value by Sales Order",
			},
		}

		self.assertEqual(clarification_continuation_lane(signal), "front_door")
		self.assertEqual(
			clarification_resolved_continuation_message(
				signal_payload=signal,
				resolved_option="Average Order Value by Sales Order",
			),
			"what is Average Order Value by Sales Order",
		)

	def test_pending_clarification_resolves_alias_option_for_governed_kpi_basis(self):
		signal = _clarification_signal(request_id="clarify-4c-alias", user_question="Choose one KPI basis.")
		signal["reason_type"] = "governed_kpi_definition_ambiguity"
		signal["suggested_options"] = [
			"Average Order Value by Sales Order",
			"Average Order Value by Sales Invoice",
		]
		signal["internal_details"] = {
			"continuation_lane": "front_door",
			"resolved_message_by_option": {
				"Average Order Value by Sales Order": "show average order value sales order last month",
				"Average Order Value by Sales Invoice": "show average order value sales invoice last month",
			},
			"option_aliases_by_option": {
				"Average Order Value by Sales Order": ["Sales Order", "Sales Orders"],
				"Average Order Value by Sales Invoice": ["Sales Invoice", "Sales Invoices"],
			},
		}

		contract = resolve_pending_clarification_response(
			request_id="clarify-4c-alias-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="Sales Order",
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
		)

		self.assertEqual(str(contract.decision or "").strip(), "resolved_option")
		self.assertEqual(str(contract.resolved_option or "").strip(), "Average Order Value by Sales Order")
		self.assertEqual(str(contract.matched_by or "").strip(), "exact_alias")

	def test_pending_clarification_resolves_typo_for_entity_detail_basis(self):
		signal = _clarification_signal(request_id="clarify-entity-basis", user_question="Choose one tenure basis.")
		signal["stage"] = "artifact_boundary"
		signal["reason_type"] = "customer_tenure_basis_missing"
		signal["suggested_options"] = [
			"Customer Tenure by Customer Created Date",
			"Customer Tenure by First Sales Order",
			"Customer Tenure by First Sales Invoice",
		]
		signal["internal_details"] = {
			"continuation_lane": "artifact_boundary",
			"resolved_message_by_option": {
				"Customer Tenure by Customer Created Date": "what is this customer's tenure by customer created date?",
				"Customer Tenure by First Sales Order": "what is this customer's tenure by first sales order date?",
				"Customer Tenure by First Sales Invoice": "what is this customer's tenure by first sales invoice date?",
			},
			"option_aliases_by_option": {
				"Customer Tenure by Customer Created Date": ["customer created date", "created date"],
				"Customer Tenure by First Sales Order": ["first sales order", "sales order", "by first sales order"],
				"Customer Tenure by First Sales Invoice": ["first sales invoice", "sales invoice", "by first sales invoice"],
			},
		}

		contract = resolve_pending_clarification_response(
			request_id="clarify-entity-basis-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="by Frist Sales order",
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
		)

		self.assertEqual(str(contract.decision or "").strip(), "resolved_option")
		self.assertEqual(str(contract.resolved_option or "").strip(), "Customer Tenure by First Sales Order")
		self.assertEqual(str(contract.matched_by or "").strip(), "fuzzy_alias")

	def test_resolved_clarification_runtime_message_preserves_entity_detail_continuation(self):
		signal = _clarification_signal(request_id="clarify-entity-runtime", user_question="Choose one tenure basis.")
		signal["stage"] = "artifact_boundary"
		signal["reason_type"] = "customer_tenure_basis_missing"
		signal["suggested_options"] = [
			"Customer Tenure by First Sales Order",
		]
		signal["internal_details"] = {
			"continuation_lane": "artifact_boundary",
			"resolved_message_by_option": {
				"Customer Tenure by First Sales Order": "what is this customer's tenure by first sales order date?",
			},
		}

		contract = resolve_pending_clarification_response(
			request_id="clarify-entity-runtime-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="Customer Tenure by First Sales Order",
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
		)

		self.assertEqual(
			_resolved_clarification_runtime_message(
				raw_message="by first sales order",
				pending_clarification_signal=signal,
				clarification_response_contract=contract,
			),
			"what is this customer's tenure by first sales order date?",
		)
		self.assertTrue(
			_artifact_boundary_clarification_requires_runtime_reset(
				clarification_lane="artifact_boundary",
				clarification_response_contract=contract,
				clarified_runtime_message="what is this customer's tenure by first sales order date?",
			)
		)

	def test_artifact_boundary_clarification_blocks_capability_requery_breakout(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="clarify-entity-followup",
			mode="capability_requery",
			requested_modes=["filter_refinement"],
			target_dimension="customer",
			target_metric="tenure",
			target_capability_id="sales_order_ranking",
			target_report="Sales Order Analysis",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The clarified request looked like a governed report switch.",
		)

		preserved = _preserve_artifact_boundary_clarification_followup_resolution(
			request_id="clarify-entity-followup",
			followup_resolution=followup_resolution,
			clarification_continuation_active=True,
			latest_grounded_turn_available=True,
		)

		self.assertEqual(str(getattr(preserved, "mode", "") or "").strip(), "grounded_follow_up")
		self.assertIn("entity_detail_evidence", list(getattr(preserved, "requested_modes", []) or []))
		self.assertEqual(str(getattr(preserved, "target_capability_id", "") or "").strip(), "")
		self.assertEqual(str(getattr(preserved, "target_report", "") or "").strip(), "")

	def test_entity_detail_evidence_preempts_frontdoor_kpi_clarification(self):
		defer_runtime_value_frontdoor, semantic_candidate = _artifact_local_refinement_should_defer_runtime_frontdoor(
			request_id="clarify-entity-preempt",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="what is this customer's tenure?",
			recent_messages=[],
			latest_grounded_turn={"source_name": "Zegyo Mobile Supply House Detail"},
			latest_family_artifact={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "customer",
					"entity_label": "Zegyo Mobile Supply House",
				},
				"metrics": {
					"customer_created_tenure_days": 13,
					"first_sales_order_tenure_days": 13,
					"first_sales_invoice_tenure_days": 13,
				},
				"sections": {
					"lifecycle": [
						{"label": "Customer Created Date", "value": "2026-03-30"},
						{"label": "First Sales Order Date", "value": "2026-03-30"},
						{"label": "First Sales Invoice Date", "value": "2026-03-30"},
					]
				},
			},
			latest_assistant_payload={},
		)

		self.assertTrue(defer_runtime_value_frontdoor)
		self.assertIsNone(semantic_candidate)

	def test_pending_clarification_allows_new_frontdoor_kpi_request_to_break_out(self):
		signal = _clarification_signal(request_id="clarify-4d", user_question="Choose one period.")
		signal["reason_type"] = "time_scope_missing"
		signal["suggested_options"] = ["Last Month", "Current Fiscal Year to Date", "Last Year"]
		signal["internal_details"] = {
			"continuation_lane": "front_door",
			"continuation_intent_class": "governed_kpi_value",
			"resolved_message_by_option": {
				"Last Month": "show average order value sales order last month",
				"Current Fiscal Year to Date": "show average order value sales order current fiscal year to date",
				"Last Year": "show average order value sales order last year",
			},
		}

		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=True,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-4d-response",
				session_id="clarify-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show collection ratio last month",
				signal_payload=signal,
				clarification_attempt_count=0,
				max_attempts=3,
			)

		self.assertEqual(str(contract.decision or "").strip(), "new_request")

	def test_pending_item_clarification_allows_cross_grain_master_data_breakout(self):
		signal = _clarification_signal(request_id="clarify-md-1", user_question="Which item do you mean?")
		signal["reason_type"] = "entity_scope_missing"
		signal["suggested_options"] = ["Type-C Cable 2m Fast Charge", "Type-C Cable 1m Fast Charge"]
		signal["internal_details"] = {
			"continuation_lane": "front_door",
			"entity_grain": "item",
			"lookup_mode": "candidate_resolution",
			"carryover_slot_values": {
				"entity_grain": "item",
				"lookup_mode": "candidate_resolution",
				"lookup_search_text": "Type-C Fast Charge",
			},
		}

		contract = resolve_pending_clarification_response(
			request_id="clarify-md-1-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message='do u have customer name similar to "Nay Lin Mobile"?',
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
		)

		self.assertEqual(str(contract.decision or "").strip(), "new_request")

	def test_pending_item_clarification_allows_same_grain_different_lookup_mode_breakout(self):
		signal = _clarification_signal(request_id="clarify-md-2", user_question="Which item do you mean?")
		signal["reason_type"] = "entity_scope_missing"
		signal["suggested_options"] = ["Type-C Cable 2m Fast Charge", "Type-C Cable 1m Fast Charge"]
		signal["internal_details"] = {
			"continuation_lane": "front_door",
			"entity_grain": "item",
			"lookup_mode": "candidate_resolution",
			"carryover_slot_values": {
				"entity_grain": "item",
				"lookup_mode": "candidate_resolution",
				"lookup_search_text": "Type-C Fast Charge",
			},
		}

		contract = resolve_pending_clarification_response(
			request_id="clarify-md-2-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="give me some item list",
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
		)

		self.assertEqual(str(contract.decision or "").strip(), "new_request")

	def test_pending_item_clarification_allows_same_grain_same_mode_different_search_text_breakout(self):
		signal = _clarification_signal(request_id="clarify-md-3", user_question="Which item do you mean?")
		signal["reason_type"] = "entity_scope_missing"
		signal["suggested_options"] = ["Type-C Cable 2m Fast Charge", "Type-C Cable 1m Fast Charge"]
		signal["internal_details"] = {
			"continuation_lane": "front_door",
			"entity_grain": "item",
			"lookup_mode": "candidate_resolution",
			"lookup_search_text": "Type-C Fast Charge",
			"carryover_slot_values": {
				"entity_grain": "item",
				"lookup_mode": "candidate_resolution",
				"lookup_search_text": "Type-C Fast Charge",
			},
		}

		contract = resolve_pending_clarification_response(
			request_id="clarify-md-3-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message='do u have product name similar to "Demo Item"?',
			signal_payload=signal,
			clarification_attempt_count=0,
			max_attempts=3,
		)

		self.assertEqual(str(contract.decision or "").strip(), "new_request")

	def test_customer_scope_clarification_can_resume_from_customer_name(self):
		signal = _clarification_signal(request_id="clarify-customer-scope", user_question="Which customer do you want?")
		signal["reason_type"] = "customer_scope_missing"
		signal["suggested_options"] = []
		signal["internal_details"] = {
			"continuation_lane": "front_door",
			"continuation_intent_class": "governed_kpi_value",
			"entity_grain": "customer",
			"resolved_message_placeholder": "customer",
			"resolved_message_template": "show customer tenure by customer created date for {customer} as of 2026-04-10",
		}

		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution.resolve_entity_reference_from_message",
			return_value={
				"resolution_status": "resolved",
				"resolved_entity": {
					"entity_type": "customer",
					"entity_key": "Zegyo Mobile Supply House",
					"entity_label": "Zegyo Mobile Supply House",
					"resolution_source": "exact_display",
				},
			},
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-customer-scope-response",
				session_id="clarify-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="Zegyo Mobile Supply House",
				signal_payload=signal,
				clarification_attempt_count=0,
				max_attempts=3,
			)

		self.assertEqual(str(contract.decision or "").strip(), "resolved_option")
		self.assertEqual(str(contract.resolved_option or "").strip(), "Zegyo Mobile Supply House")
		self.assertEqual(str(contract.matched_by or "").strip(), "entity_reference_exact")
		self.assertEqual(
			clarification_resolved_continuation_message(
				signal_payload=signal,
				resolved_option=str(contract.resolved_option or "").strip(),
			),
			"show customer tenure by customer created date for Zegyo Mobile Supply House as of 2026-04-10",
		)

	def test_frontdoor_structured_resolution_can_reenter_without_prebuilt_continuation_message(self):
		contract = types.SimpleNamespace(
			decision="resolved_option",
			resolved_option="Suppliers",
			resolved_slot={"entity_grain": "supplier"},
		)
		self.assertTrue(
			_frontdoor_clarification_requires_fresh_query_reset(
				clarification_lane="front_door",
				clarification_response_contract=contract,
				clarified_runtime_message="",
			)
		)
		self.assertEqual(
			_frontdoor_clarification_reentry_message(
				raw_message="suppliers",
				clarification_lane="front_door",
				clarification_response_contract=contract,
				clarified_runtime_message="",
			),
			"suppliers",
		)

	def test_message_history_pending_clarification_ignores_superseded_signal_after_later_visible_turn(self):
		signal = _clarification_signal(
			request_id="clarify-4b",
			user_question="Which report do you want?",
		)
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="assistant", content=json.dumps({"type": "text", "text": "Which report do you want?"})),
				_FakeMessage(role="tool", content=json.dumps(signal)),
				_FakeMessage(role="user", content="show accounts receivable summary as of today"),
				_FakeMessage(role="assistant", content=json.dumps({"type": "text", "text": "Accounts Receivable Summary as of today"})),
			]
		)

		self.assertEqual(latest_pending_clarification_signal_from_messages(session_doc), {})

	def test_latest_assistant_turn_detects_clarification_fallback_stop(self):
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="user", content="yes"),
				_FakeMessage(
					role="tool",
					content=json.dumps(
						{
							"type": "qwen_phase55_observability_event",
							"event_family": "clarification",
							"event_name": "fallback_stop",
						}
					),
				),
				_FakeMessage(
					role="assistant",
					content=json.dumps({"type": "text", "text": "I'll pause here rather than guess."}),
				),
			]
		)

		self.assertTrue(latest_assistant_turn_was_clarification_fallback_stop(session_doc))

	def test_latest_assistant_turn_ignores_older_clarification_fallback_stop(self):
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="user", content="yes"),
				_FakeMessage(
					role="tool",
					content=json.dumps(
						{
							"type": "qwen_phase55_observability_event",
							"event_family": "clarification",
							"event_name": "fallback_stop",
						}
					),
				),
				_FakeMessage(
					role="assistant",
					content=json.dumps({"type": "text", "text": "I'll pause here rather than guess."}),
				),
				_FakeMessage(role="user", content="show accounts receivable summary"),
				_FakeMessage(
					role="tool",
					content=json.dumps(
						{
							"type": "qwen_phase55_observability_event",
							"event_family": "front_door",
							"event_name": "handled",
						}
					),
				),
				_FakeMessage(
					role="assistant",
					content=json.dumps({"type": "text", "text": "Accounts Receivable Summary"}),
				),
			]
		)

		self.assertFalse(latest_assistant_turn_was_clarification_fallback_stop(session_doc))

	def test_malformed_clarification_storage_fails_closed_to_empty_state(self):
		session_doc = _FakeSessionDoc()
		session_doc.pending_clarification_state_json = json.dumps(
			{
				"type": "qwen_pending_clarification_state",
				"attempt_count": 99,
				"max_attempts": 3,
				"pending_signal": "not-a-dict",
			}
		)

		state = clarification_state_from_storage(session_doc.pending_clarification_state_json)
		self.assertFalse(state.has_pending)
		self.assertEqual(state.attempt_count, 0)

	def test_duplicate_accepted_repairs_keep_recovery_consumed(self):
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-state-1",
			session_id="phase8a",
			source_request_id="grounded-state-1",
			source_family_id="ranking_analytics",
			source_capability_id="sales_read",
			source_report="Sales Analytics",
			recovery_state="recoverable",
			available_recovery_actions=["run_alternative_governed_query"],
			recommended_recovery_action="run_alternative_governed_query",
			allowed_to_recover=True,
			confidence=0.93,
		).to_payload()
		accepted_repair_payload = build_conversational_repair_intent_contract(
			request_id="repair-state-accepted-1",
			session_id="phase8a",
			repair_intent_type="accept_recovery_action",
			repair_state="accepted",
			targets_prior_recovery=True,
			accepted_recovery_action="run_alternative_governed_query",
			reason="User accepted the recovery.",
			allowed_next_lane="artifact_lane",
			confidence=0.96,
		).to_payload()
		duplicate_accepted_repair_payload = build_conversational_repair_intent_contract(
			request_id="repair-state-accepted-2",
			session_id="phase8a",
			repair_intent_type="accept_recovery_action",
			repair_state="accepted",
			targets_prior_recovery=True,
			accepted_recovery_action="run_alternative_governed_query",
			reason="User repeated the same acceptance.",
			allowed_next_lane="artifact_lane",
			confidence=0.97,
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(recovery_payload)),
				_FakeMessage(role="tool", content=json.dumps(accepted_repair_payload)),
				_FakeMessage(role="tool", content=json.dumps(duplicate_accepted_repair_payload)),
			]
		)

		self.assertEqual(_latest_recovery_contract(session_doc), {})

	def test_accepted_non_recovery_repair_does_not_consume_latest_recovery(self):
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-state-2",
			session_id="phase8a",
			source_request_id="grounded-state-2",
			source_family_id="ranking_analytics",
			source_capability_id="sales_read",
			source_report="Sales Analytics",
			recovery_state="recoverable",
			available_recovery_actions=["run_alternative_governed_query"],
			recommended_recovery_action="run_alternative_governed_query",
			allowed_to_recover=True,
			confidence=0.93,
		).to_payload()
		accepted_non_recovery_payload = build_conversational_repair_intent_contract(
			request_id="repair-state-non-recovery-accepted-1",
			session_id="phase8a",
			repair_intent_type="guidance_request",
			repair_state="accepted",
			targets_prior_recovery=False,
			accepted_recovery_action="",
			reason="User asked for explanation, not recovery execution.",
			allowed_next_lane="front_door",
			confidence=0.88,
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(recovery_payload)),
				_FakeMessage(role="tool", content=json.dumps(accepted_non_recovery_payload)),
			]
		)

		latest = _latest_recovery_contract(session_doc)
		self.assertEqual(latest.get("request_id"), "recovery-state-2")
		self.assertEqual(latest.get("recommended_recovery_action"), "run_alternative_governed_query")

	def test_unresolved_repair_does_not_consume_latest_recovery(self):
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-state-3",
			session_id="phase8a",
			source_request_id="grounded-state-3",
			source_family_id="ranking_analytics",
			source_capability_id="sales_read",
			source_report="Sales Analytics",
			recovery_state="recoverable",
			available_recovery_actions=["run_alternative_governed_query"],
			recommended_recovery_action="run_alternative_governed_query",
			allowed_to_recover=True,
			confidence=0.93,
		).to_payload()
		unresolved_repair_payload = build_conversational_repair_intent_contract(
			request_id="repair-state-unresolved-1",
			session_id="phase8a",
			repair_intent_type="accept_recovery_action",
			repair_state="unresolved",
			targets_prior_recovery=True,
			accepted_recovery_action="run_alternative_governed_query",
			reason="Interpretation was unresolved and should not consume recovery.",
			allowed_next_lane="front_door",
			confidence=0.42,
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(recovery_payload)),
				_FakeMessage(role="tool", content=json.dumps(unresolved_repair_payload)),
			]
		)

		latest = _latest_recovery_contract(session_doc)
		self.assertEqual(latest.get("request_id"), "recovery-state-3")
		self.assertEqual(latest.get("recommended_recovery_action"), "run_alternative_governed_query")

	def test_latest_grounded_turn_ignores_later_non_grounded_tool_payloads(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-state-4",
			"trace_request_id": "grounded-state-4-trace",
			"grounded": True,
			"source_name": "Accounts Receivable Summary",
			"artifact_family_id": "receivable_summary",
			"artifact_source_reports": ["Accounts Receivable Summary"],
		}
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-state-4",
			session_id="phase8a",
			source_request_id="grounded-state-4-trace",
			source_family_id="receivable_summary",
			source_capability_id="receivables_read",
			source_report="Accounts Receivable Summary",
			recovery_state="recoverable",
			available_recovery_actions=["clarify_target_output"],
			recommended_recovery_action="clarify_target_output",
			allowed_to_recover=True,
			confidence=0.74,
		).to_payload()
		repair_payload = build_conversational_repair_intent_contract(
			request_id="repair-state-4",
			session_id="phase8a",
			repair_intent_type="guidance_request",
			repair_state="accepted",
			targets_prior_recovery=False,
			accepted_recovery_action="",
			reason="User asked for explanation.",
			allowed_next_lane="front_door",
			confidence=0.86,
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(recovery_payload)),
				_FakeMessage(role="tool", content=json.dumps(repair_payload)),
			]
		)

		latest_grounded = _latest_grounded_turn_contract(session_doc)
		self.assertEqual(latest_grounded.get("request_id"), "grounded-state-4")
		self.assertEqual(latest_grounded.get("trace_request_id"), "grounded-state-4-trace")
		self.assertEqual(latest_grounded.get("source_name"), "Accounts Receivable Summary")

	def test_latest_grounded_turn_ignores_later_malformed_grounded_payload_without_authority(self):
		valid_grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-state-4b",
			"trace_request_id": "grounded-state-4b-trace",
			"grounded": True,
			"source_name": "Accounts Receivable Summary",
			"artifact_family_id": "receivable_summary",
			"artifact_source_reports": ["Accounts Receivable Summary"],
		}
		malformed_later_grounded_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "",
			"trace_request_id": "",
			"grounded": False,
			"source_name": "Broken Payload",
			"artifact_family_id": "broken_family",
			"artifact_source_reports": ["Broken Report"],
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(valid_grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(malformed_later_grounded_payload)),
			]
		)

		latest_grounded = _latest_grounded_turn_contract(session_doc)
		self.assertEqual(latest_grounded.get("request_id"), "grounded-state-4b")
		self.assertEqual(latest_grounded.get("trace_request_id"), "grounded-state-4b-trace")
		self.assertEqual(latest_grounded.get("artifact_family_id"), "receivable_summary")

	def test_latest_recovery_contract_ignores_later_non_authoritative_grounded_payload(self):
		valid_grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-state-4c",
			"trace_request_id": "grounded-state-4c-trace",
			"grounded": True,
			"source_name": "Accounts Receivable Summary",
			"artifact_family_id": "receivable_summary",
			"artifact_source_reports": ["Accounts Receivable Summary"],
		}
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-state-4c",
			session_id="phase8a",
			source_request_id="grounded-state-4c-trace",
			source_family_id="receivable_summary",
			source_capability_id="receivables_read",
			source_report="Accounts Receivable Summary",
			recovery_state="recoverable",
			available_recovery_actions=["clarify_target_output"],
			recommended_recovery_action="clarify_target_output",
			allowed_to_recover=True,
			confidence=0.78,
		).to_payload()
		malformed_later_grounded_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "broken-grounded-state-4c",
			"trace_request_id": "",
			"grounded": False,
			"source_name": "Broken Payload",
			"artifact_family_id": "broken_family",
			"artifact_source_reports": ["Broken Report"],
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(valid_grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(recovery_payload)),
				_FakeMessage(role="tool", content=json.dumps(malformed_later_grounded_payload)),
			]
		)

		latest_recovery = _latest_recovery_contract(session_doc)
		self.assertEqual(latest_recovery.get("request_id"), "recovery-state-4c")
		self.assertEqual(latest_recovery.get("source_request_id"), "grounded-state-4c-trace")

	def test_source_compatible_reasoning_contract_prefers_matching_grounded_request(self):
		grounded_turn = {
			"request_id": "grounded-state-5",
			"trace_request_id": "grounded-state-5-trace",
			"artifact_family_id": "receivable_summary",
			"artifact_source_reports": ["Accounts Receivable Summary"],
		}
		matching_reasoning_contract = {
			"type": "qwen_erp_business_reasoning_contract",
			"grounding_source_request_id": "grounded-state-5-trace",
			"grounding_family_id": "receivable_summary",
			"grounding_source_reports": ["Accounts Receivable Summary"],
		}
		mismatched_reasoning_contract = {
			"type": "qwen_erp_business_reasoning_contract",
			"grounding_source_request_id": "other-grounded-trace",
			"grounding_family_id": "receivable_summary",
			"grounding_source_reports": ["Accounts Receivable Summary"],
		}

		self.assertEqual(
			_source_compatible_reasoning_contract(
				grounded_turn=grounded_turn,
				reasoning_contract=mismatched_reasoning_contract,
			),
			{},
		)
		self.assertEqual(
			_source_compatible_reasoning_contract(
				grounded_turn=grounded_turn,
				reasoning_contract=matching_reasoning_contract,
			),
			matching_reasoning_contract,
		)

	def test_source_compatible_reasoning_contract_rejects_mismatched_grounded_reports(self):
		grounded_turn = {
			"request_id": "grounded-state-5b",
			"trace_request_id": "",
			"artifact_family_id": "receivable_summary",
			"artifact_source_reports": ["Accounts Receivable Summary"],
		}
		mismatched_reasoning_contract = {
			"type": "qwen_erp_business_reasoning_contract",
			"grounding_source_request_id": "",
			"grounding_family_id": "receivable_summary",
			"grounding_source_reports": ["Accounts Payable Summary"],
		}

		self.assertEqual(
			_source_compatible_reasoning_contract(
				grounded_turn=grounded_turn,
				reasoning_contract=mismatched_reasoning_contract,
			),
			{},
		)

	def test_source_compatible_reasoning_contract_rejects_mismatched_grounded_family(self):
		grounded_turn = {
			"request_id": "grounded-state-5c",
			"trace_request_id": "",
			"artifact_family_id": "receivable_summary",
			"artifact_source_reports": [],
		}
		mismatched_reasoning_contract = {
			"type": "qwen_erp_business_reasoning_contract",
			"grounding_source_request_id": "",
			"grounding_family_id": "payable_summary",
			"grounding_source_reports": [],
		}

		self.assertEqual(
			_source_compatible_reasoning_contract(
				grounded_turn=grounded_turn,
				reasoning_contract=mismatched_reasoning_contract,
			),
			{},
		)

	def test_latest_normalized_family_artifact_prefers_grounded_compatible_artifact(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-state-6",
			"trace_request_id": "grounded-state-6-trace",
			"grounded": True,
			"artifact_type": "normalized_family_artifact",
			"artifact_family_id": "receivable_summary",
			"artifact_source_reports": ["Accounts Receivable Summary"],
		}
		matching_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "grounded-state-6-trace",
			"family_id": "receivable_summary",
			"source_reports": ["Accounts Receivable Summary"],
			"artifact_type": "normalized_family_artifact",
		}
		incompatible_later_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "other-grounded-trace",
			"family_id": "payable_summary",
			"source_reports": ["Accounts Payable Summary"],
			"artifact_type": "normalized_family_artifact",
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(matching_artifact_payload)),
				_FakeMessage(role="tool", content=json.dumps(incompatible_later_artifact_payload)),
			]
		)

		latest = _latest_normalized_family_artifact(
			session_doc,
			grounded_turn=_latest_grounded_turn_contract(session_doc),
		)
		self.assertEqual(latest.get("request_id"), "grounded-state-6-trace")
		self.assertEqual(latest.get("family_id"), "receivable_summary")

	def test_latest_normalized_family_artifact_falls_back_to_latest_candidate_without_grounded_turn(self):
		older_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "artifact-old",
			"family_id": "receivable_summary",
			"source_reports": ["Accounts Receivable Summary"],
			"artifact_type": "normalized_family_artifact",
		}
		newer_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "artifact-new",
			"family_id": "payable_summary",
			"source_reports": ["Accounts Payable Summary"],
			"artifact_type": "normalized_family_artifact",
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(older_artifact_payload)),
				_FakeMessage(role="tool", content=json.dumps(newer_artifact_payload)),
			]
		)

		latest = _latest_normalized_family_artifact(session_doc, grounded_turn={})
		self.assertEqual(latest.get("request_id"), "artifact-new")
		self.assertEqual(latest.get("family_id"), "payable_summary")

	def test_latest_normalized_family_artifact_prefers_matching_composite_artifact(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-state-7",
			"trace_request_id": "grounded-state-7-trace",
			"grounded": True,
			"artifact_type": "normalized_composite_family_artifact",
			"artifact_family_id": "customer_health_composite",
			"artifact_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
		}
		matching_composite_artifact_payload = {
			"type": "qwen_composite_family_artifact",
			"request_id": "grounded-state-7-trace",
			"family_id": "customer_health_composite",
			"source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
			"artifact_type": "normalized_composite_family_artifact",
		}
		incompatible_later_normalized_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "grounded-state-7-trace",
			"family_id": "customer_health_composite",
			"source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
			"artifact_type": "normalized_family_artifact",
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(matching_composite_artifact_payload)),
				_FakeMessage(role="tool", content=json.dumps(incompatible_later_normalized_artifact_payload)),
			]
		)

		latest = _latest_normalized_family_artifact(
			session_doc,
			grounded_turn=_latest_grounded_turn_contract(session_doc),
		)
		self.assertEqual(latest.get("type"), "qwen_composite_family_artifact")
		self.assertEqual(latest.get("request_id"), "grounded-state-7-trace")
		self.assertEqual(latest.get("family_id"), "customer_health_composite")

	def test_latest_normalized_family_artifact_prefers_matching_entity_detail_artifact(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-state-8",
			"trace_request_id": "grounded-state-8-trace",
			"grounded": True,
			"artifact_type": "entity_detail_artifact",
			"artifact_family_id": "customer_detail",
			"artifact_source_reports": ["Customer Ledger Summary"],
		}
		matching_entity_detail_payload = {
			"type": "qwen_entity_detail_artifact",
			"request_id": "grounded-state-8-trace",
			"family_id": "customer_detail",
			"source_reports": ["Customer Ledger Summary"],
			"artifact_type": "entity_detail_artifact",
		}
		incompatible_later_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "other-grounded-trace",
			"family_id": "customer_summary",
			"source_reports": ["Customer Summary"],
			"artifact_type": "normalized_family_artifact",
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(matching_entity_detail_payload)),
				_FakeMessage(role="tool", content=json.dumps(incompatible_later_artifact_payload)),
			]
		)

		latest = _latest_normalized_family_artifact(
			session_doc,
			grounded_turn=_latest_grounded_turn_contract(session_doc),
		)
		self.assertEqual(latest.get("type"), "qwen_entity_detail_artifact")
		self.assertEqual(latest.get("request_id"), "grounded-state-8-trace")
		self.assertEqual(latest.get("family_id"), "customer_detail")
