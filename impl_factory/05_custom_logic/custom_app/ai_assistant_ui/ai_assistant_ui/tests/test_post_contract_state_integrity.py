import json
import sys
import types
import unittest
import ai_assistant_ui.qwen_chat.governed_scope_registry as governed_scope_registry_module
import ai_assistant_ui.qwen_chat.restore_support as restore_support_module
import ai_assistant_ui.qwen_chat.snapshot_defaults as snapshot_defaults_module
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch


def _fake_get_all(doctype, *args, **kwargs):
	if doctype == "Company":
		if kwargs.get("pluck") == "name":
			return ["Enterprise Co"]
		return [{"name": "Enterprise Co"}]
	return []


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = _fake_get_all
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

import ai_assistant_ui.qwen_chat.recent_focus_support as recent_focus_support_module
from ai_assistant_ui.qwen_chat.business_language_guards import (
	looks_like_unsupported_operational_inference_claim,
)
from ai_assistant_ui.qwen_chat.metadata import (
	load_report_registry,
	report_approved_followup_modes,
	report_business_family_ids,
)

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
	conversation_control_evidence_internal_details,
	control_action_id,
	control_action_id_from_message_or_evidence,
	control_action_is_strong_owner,
	looks_like_option_list_request as shared_looks_like_option_list_request,
	prior_branch_phrase_type_from_control_action,
	targeted_restore_hint_from_control_evidence,
	targeted_restore_hint_from_message,
)
from ai_assistant_ui.qwen_chat.conversation_control_support import (
	artifact_boundary_clarification_requires_runtime_reset,
	select_compound_request_completion_superseding_state as shared_select_compound_request_completion_superseding_state,
	clarification_decision_allows_immediate_control_override,
	clarification_response_decision_spec,
	clarification_response_resolved_slot_payload,
	clarification_response_should_yield_initial_control_decision,
	frontdoor_clarification_reentry_message,
	frontdoor_clarification_requires_fresh_query_reset,
	pending_clarification_response_should_preempt_runtime,
	pending_clarification_should_yield_to_current_control_decision,
	resolved_clarification_runtime_message,
)
from ai_assistant_ui.qwen_chat.clarification_state import (
	build_pending_clarification_state,
	clarification_state_from_storage,
	get_clarification_state,
)
from ai_assistant_ui.qwen_chat.clarification_resolution import clarification_state_after_unresolved_attempt
from ai_assistant_ui.qwen_chat.contracts import (
	_grounded_turn_has_single_row_contextual_focus,
	_looks_like_base_transaction_listing_reask,
	build_artifact_enrichment_recovery_contract,
	build_compound_request_assessment_contract,
	build_conversation_control_evidence_contract,
	build_conversation_control_decision_contract,
	build_conversational_repair_intent_contract,
	build_followup_resolution,
	build_followup_resolution_contract,
	build_scope_decision_input,
	build_prior_branch_restore_contract,
)
from ai_assistant_ui.qwen_chat.service import (
	_build_recent_focus_affordance_contract_from_snapshot,
	_compile_recent_focus_runtime_message,
	_build_conversation_control_evidence_contract,
	_build_conversation_state_snapshot,
	_build_authoritative_pending_clarification_restore_contract,
	_build_direct_restore_fallback_contract,
	_build_prior_branch_restore_contract_from_snapshot,
	_select_prior_branch_restore_route,
	_select_active_sequence_superseding_owner,
	_select_latest_non_clarification_restore_state,
	_select_non_clarification_restore_owner,
	_select_targeted_restore_owner,
	_select_resumable_prior_request_candidate,
	_artifact_boundary_clarification_requires_runtime_reset,
	_artifact_local_refinement_has_grounded_evidence,
	_artifact_local_refinement_should_defer_runtime_frontdoor,
	_conversation_control_decision_from_clarification_response,
	_conversation_control_decision_from_compound_cancellation,
	_conversation_control_decision_from_compound_completion,
	_conversation_control_decision_from_compound_continuation,
	_select_compound_cancellation_sequence_source,
	_select_compound_completion_reentry_response,
	_select_compound_completion_reentry_eligibility,
	_select_compound_continuation_eligibility,
	_select_compound_completion_reentry_action,
	_build_superseded_active_sequence_transition,
	_cancel_compound_request_assessment_payload,
	_complete_compound_request_assessment_payload,
	_active_sequence_completion_source_payload,
	_select_active_sequence_completion_source_owner,
	_active_sequence_should_complete_after_current_turn,
	_compound_request_completion_answer_from_snapshot,
	_compound_request_continuation_control_with_evidence,
	_compound_request_completion_is_superseded_by_newer_state,
	_select_compound_execution_runtime_source,
	_select_compound_request_completion_superseding_state,
	_compound_request_stop_control_with_evidence,
	_conversation_control_decision_from_prior_branch_restore_contract,
	_conversation_control_decision_from_repair_contract,
	_conversation_control_decision_from_recent_focus_runtime_message,
	_select_recent_focus_continuation_eligibility,
	_clarification_response_should_yield_initial_control_decision,
	_frontdoor_clarification_reentry_message,
	_frontdoor_clarification_requires_fresh_query_reset,
	_handle_prior_branch_restore_direct_route,
	_handle_prior_branch_restore_reopen_pending_clarification,
	_handle_prior_branch_restore_fresh_query,
	_prior_branch_restore_mode,
	_recent_focus_state_from_prior_branch_restore_contract,
	_prior_branch_restore_recent_focus_affordance_contract,
	_select_prior_branch_restore_direct_handler_route,
	_select_prior_branch_restore_projection,
	_prior_branch_restore_runtime_override_message,
	_prior_branch_restore_runtime_message,
	_latest_normalized_family_artifact,
	_latest_repair_intent_contract,
	_latest_grounded_turn_contract,
	_pending_clarification_should_yield_to_current_control_decision,
	_select_initial_control_override_owner,
	_select_prior_branch_restore_decision_state,
	_select_pending_clarification_override_owner,
	_select_active_sequence_completion_owner,
	_preserve_current_artifact_direct_evidence_followup_resolution,
	_preserve_artifact_boundary_clarification_followup_resolution,
	_current_artifact_evidence_should_block_requery,
	_current_artifact_evidence_should_preserve_context,
	_frontdoor_should_yield_to_current_artifact_evidence,
	_frontdoor_should_yield_to_reasoning_activation,
	_resolve_compound_execution_runtime_message,
	_strip_leading_control_discard_preamble,
	_latest_recovery_contract,
	_resolved_clarification_runtime_message,
	_source_compatible_reasoning_contract,
	_snapshot_recent_focus_state,
	_reasoning_activation_supersedes_followup_refinement,
	_reasoning_preempted_by_followup_refinement,
)
from ai_assistant_ui.qwen_chat.lanes.clarification_lane import (
	build_pending_clarification_frontdoor_skip,
	handle_pending_clarification_turn,
)
from ai_assistant_ui.qwen_chat.lanes.artifact_boundary_lane import handle_artifact_boundary_turn
from ai_assistant_ui.qwen_chat.lanes.entity_drilldown_lane import handle_entity_drilldown_turn
from ai_assistant_ui.qwen_chat.governed_composite_runtime_execution import (
	maybe_build_governed_composite_frontdoor_response,
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


def _fake_snapshot_session_for_grounded_report(
	*,
	request_id: str,
	trace_request_id: str,
	report_name: str,
	artifact_family_id: str,
	dimensions: Dict[str, Any] | None = None,
	table_rows: List[Dict[str, Any]] | None = None,
) -> _FakeSessionDoc:
	grounded_turn_payload = {
		"type": "qwen_grounded_turn_context",
		"contract_version": "1.0",
		"request_id": request_id,
		"trace_request_id": trace_request_id,
		"grounded": True,
		"source_kind": "report",
		"source_name": report_name,
		"artifact_family_id": artifact_family_id,
		"artifact_source_reports": [report_name],
	}
	if isinstance(table_rows, list) and table_rows:
		grounded_turn_payload["table_rows"] = list(table_rows)
	artifact_payload = {
		"type": "qwen_normalized_family_artifact_contract",
		"request_id": trace_request_id,
		"family_id": artifact_family_id,
		"artifact_type": "normalized_family_artifact",
		"source_reports": [report_name],
		"dimensions": dict(dimensions or {}),
	}
	return _FakeSessionDoc(
		[
			_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
			_FakeMessage(role="tool", content=json.dumps(artifact_payload)),
		]
	)


def _single_row_snapshot_fixture_for_focus_grain(focus_grain: str) -> Dict[str, Any]:
	grain = str(focus_grain or "").strip()
	return {
		"customer": {
			"Customer": "Ko Nay Lin Mobile Center",
			"Customer Name": "Ko Nay Lin Mobile Center",
		},
		"supplier": {
			"Supplier": "Myanmar Tech Import Services",
			"Supplier Name": "Myanmar Tech Import Services",
		},
		"item": {
			"Item Code": "ACC-CBL-BAS-TC1M",
			"Item Name": "Type-C Cable 1m Fast Charge",
		},
		"product": {
			"Item Code": "ACC-CBL-BAS-TC1M",
			"Item Name": "Type-C Cable 1m Fast Charge",
		},
		"payment_entry": {
			"Payment Entry": "ACC-PAY-2026-00179",
			"Party": "Golden Dragon Trading Co. Ltd.",
		},
		"sales_invoice": {
			"Sales Invoice": "ACC-SINV-2026-00205",
			"Customer": "Capital Telecom (NPT)",
		},
		"purchase_invoice": {
			"Purchase Invoice": "ACC-PINV-2026-00335",
			"Supplier": "Myanmar Tech Import Services",
		},
		"delivery_note": {
			"Delivery Note": "MAT-DN-2026-00018",
			"Customer": "Bayint Naung Wholesale Mobile",
		},
		"sales_order": {
			"Sales Order": "SAL-ORD-2026-00029",
			"Customer": "Bayint Naung Wholesale Mobile",
		},
		"purchase_order": {
			"Purchase Order": "PUR-ORD-2026-00004",
			"Supplier": "Shwe Taung Electronics Supply",
		},
	}.get(grain, {})


def _detail_snapshot_fixture_for_scope(scope_id: str, report_name: str) -> Dict[str, Any]:
	scope_text = str(scope_id or "").strip()
	report_text = str(report_name or "").strip()
	if scope_text in {"customer_master", "supplier_master", "item_master"}:
		focus_grain = scope_text.replace("_master", "")
		row = _single_row_snapshot_fixture_for_focus_grain(focus_grain)
		if focus_grain == "item":
			label = str(row.get("Item Name") or "").strip()
			key = str(row.get("Item Code") or label).strip()
		elif focus_grain == "supplier":
			label = str(row.get("Supplier Name") or row.get("Supplier") or "").strip()
			key = str(row.get("Supplier") or label).strip()
		else:
			label = str(row.get("Customer Name") or row.get("Customer") or "").strip()
			key = str(row.get("Customer") or label).strip()
		source_name = {
			"customer_master": "Customer Detail",
			"supplier_master": "Supplier Detail",
			"item_master": "Item Detail",
		}.get(scope_text, "Entity Detail")
		return {
			"focus_kind": "entity",
			"focus_grain": focus_grain,
			"source_name": source_name,
			"entity_label": label,
			"entity_key": key,
		}
	focus_grain = scope_text
	row = _single_row_snapshot_fixture_for_focus_grain(focus_grain)
	label_column_map = {
		"sales_invoice": "Sales Invoice",
		"purchase_invoice": "Purchase Invoice",
		"delivery_note": "Delivery Note",
		"sales_order": "Sales Order",
		"purchase_order": "Purchase Order",
	}
	label = str(row.get(label_column_map.get(focus_grain, "")) or "").strip()
	source_name = report_text[:-4] + "Detail" if report_text.endswith("List") else f"{focus_grain.replace('_', ' ').title()} Detail"
	return {
		"focus_kind": "document",
		"focus_grain": focus_grain,
		"source_name": source_name,
		"entity_label": label,
		"entity_key": label,
	}


def _runtime_followup_resolution(*, mode: str = "new_query", requested_modes: List[str] | None = None):
	return build_followup_resolution_contract(
		request_id=f"recent-focus-runtime-{mode}",
		mode=mode,
		requested_modes=list(requested_modes or [mode]),
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

	def test_pending_clarification_frontdoor_skip_accepts_shared_redirect_evidence(self):
		signal = _clarification_signal(request_id="clarify-lane-1", user_question="Which item do you mean?")
		clarification_state = build_pending_clarification_state(
			signal,
			attempt_count=0,
			max_attempts=3,
		)

		clarification_contract, frontdoor_semantic_result, frontdoor_contract = build_pending_clarification_frontdoor_skip(
			request_id="clarify-lane-1-response",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="ignore that, show me suppliers",
			pending_clarification_signal=signal,
			clarification_state=clarification_state,
			latest_grounded_turn_available=False,
			latest_grounded_turn={},
			conversation_control_evidence_payload={
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
		self.assertEqual(str(getattr(frontdoor_semantic_result, "status", "") or "").strip(), "skipped_for_pending_clarification")
		self.assertTrue(bool(frontdoor_contract is not None))

	def test_weak_clarification_response_yields_initial_control_decision_to_prior_branch_restore(self):
		clarification_contract = types.SimpleNamespace(
			decision="reask_pending_clarification",
		)
		prior_branch_decision = build_conversation_control_decision_contract(
			request_id="prior-restore-yield-1",
			decision_class="prior_branch_restore",
			decision_action="restore_recent_focus",
			target_state_class="prior_branch_restore",
		)

		self.assertTrue(
			_clarification_response_should_yield_initial_control_decision(
				clarification_response_contract=clarification_contract,
				prior_branch_restore_control_decision_contract=prior_branch_decision,
				control_evidence_payload={},
			)
		)

	def test_weak_clarification_response_yields_initial_control_decision_to_sequence_resume(self):
		clarification_contract = types.SimpleNamespace(
			decision="reask_pending_clarification",
		)

		self.assertTrue(
			_clarification_response_should_yield_initial_control_decision(
				clarification_response_contract=clarification_contract,
				prior_branch_restore_control_decision_contract=None,
				control_evidence_payload={"action_id": "resume_active_sequence"},
			)
		)

	def test_initial_control_decision_yields_to_strong_prior_branch_restore_without_clarification_response(self):
		prior_branch_decision = build_conversation_control_decision_contract(
			request_id="prior-restore-yield-1b",
			decision_class="prior_branch_restore",
			decision_action="restore_recent_focus",
			target_state_class="prior_branch_restore",
		)

		self.assertTrue(
			_clarification_response_should_yield_initial_control_decision(
				clarification_response_contract=None,
				prior_branch_restore_control_decision_contract=prior_branch_decision,
				control_evidence_payload={},
			)
		)

	def test_initial_control_decision_yields_to_sequence_resume_without_clarification_response(self):
		self.assertTrue(
			_clarification_response_should_yield_initial_control_decision(
				clarification_response_contract=None,
				prior_branch_restore_control_decision_contract=None,
				control_evidence_payload={"action_id": "resume_active_sequence"},
			)
		)


	def test_initial_control_decision_yields_to_prior_branch_restore_when_clarification_detects_new_request(self):
		clarification_contract = types.SimpleNamespace(
			decision="new_request",
		)
		prior_branch_decision = build_conversation_control_decision_contract(
			request_id="prior-restore-yield-1c",
			decision_class="prior_branch_restore",
			decision_action="restore_recent_focus",
			target_state_class="prior_branch_restore",
		)

		self.assertTrue(
			_clarification_response_should_yield_initial_control_decision(
				clarification_response_contract=clarification_contract,
				prior_branch_restore_control_decision_contract=prior_branch_decision,
				control_evidence_payload={},
			)
		)

	def test_select_initial_control_override_owner_prefers_prior_branch_restore(self):
		prior_branch_decision = build_conversation_control_decision_contract(
			request_id="initial-owner-1",
			decision_class="prior_branch_restore",
			decision_action="restore_recent_focus",
			target_state_class="prior_branch_restore",
		)

		selected = _select_initial_control_override_owner(
			prior_branch_restore_control_decision_contract=prior_branch_decision,
			control_evidence_payload={"action_id": "resume_active_sequence"},
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "prior_branch_restore_decision")
		self.assertEqual(str(selected.get("basis") or "").strip(), "prior_branch_restore_override")

	def test_select_prior_branch_restore_decision_state_ignores_reopen_pending_clarification(self):
		prior_branch_decision = build_conversation_control_decision_contract(
			request_id="prior-branch-state-1",
			decision_class="prior_branch_restore",
			decision_action="reopen_pending_clarification",
			target_state_class="prior_branch_restore",
		)

		selected = _select_prior_branch_restore_decision_state(
			prior_branch_restore_control_decision_contract=prior_branch_decision,
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "")
		self.assertEqual(str(selected.get("basis") or "").strip(), "")
		self.assertEqual(str(selected.get("action") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(str(selected.get("kind") or "").strip(), "reopen_pending_clarification")

	def test_select_prior_branch_restore_decision_state_marks_resume_active_sequence(self):
		prior_branch_decision = build_conversation_control_decision_contract(
			request_id="prior-branch-state-2",
			decision_class="prior_branch_restore",
			decision_action="resume_active_sequence",
			target_state_class="prior_branch_restore",
		)

		selected = _select_prior_branch_restore_decision_state(
			prior_branch_restore_control_decision_contract=prior_branch_decision,
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "prior_branch_restore_decision")
		self.assertEqual(str(selected.get("basis") or "").strip(), "prior_branch_resume_active_sequence")
		self.assertEqual(str(selected.get("action") or "").strip(), "resume_active_sequence")
		self.assertEqual(str(selected.get("kind") or "").strip(), "resume_active_sequence")

	def test_select_initial_control_override_owner_uses_sequence_resume_when_no_prior_branch_restore_exists(self):
		selected = _select_initial_control_override_owner(
			prior_branch_restore_control_decision_contract=None,
			control_evidence_payload={"action_id": "resume_active_sequence"},
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "control_action")
		self.assertEqual(str(selected.get("basis") or "").strip(), "resume_active_sequence_override")

	def test_pending_clarification_yields_to_current_sequence_resume_decision(self):
		clarification_contract = types.SimpleNamespace(
			decision="reask_pending_clarification",
		)
		sequence_decision = build_conversation_control_decision_contract(
			request_id="sequence-yield-1",
			decision_class="sequence_continuation",
			decision_action="resume_active_sequence",
			target_state_class="active_sequence",
		)

		self.assertTrue(
			_pending_clarification_should_yield_to_current_control_decision(
				clarification_response_contract=clarification_contract,
				prior_branch_restore_control_decision_contract=None,
				conversation_control_decision_contract=sequence_decision,
			)
		)

	def test_pending_clarification_yields_to_recent_focus_restore_without_clarification_response(self):
		restore_decision = build_conversation_control_decision_contract(
			request_id="clarify-yield-1b",
			decision_class="prior_branch_restore",
			decision_action="restore_recent_focus",
			target_state_class="prior_branch_restore",
		)

		self.assertTrue(
			_pending_clarification_should_yield_to_current_control_decision(
				clarification_response_contract=None,
				prior_branch_restore_control_decision_contract=restore_decision,
				conversation_control_decision_contract=restore_decision,
			)
		)


	def test_pending_clarification_yields_to_recent_focus_restore_when_clarification_detects_new_request(self):
		clarification_contract = types.SimpleNamespace(
			decision="new_request",
		)
		restore_decision = build_conversation_control_decision_contract(
			request_id="clarify-yield-1c",
			decision_class="prior_branch_restore",
			decision_action="restore_recent_focus",
			target_state_class="prior_branch_restore",
		)

		self.assertTrue(
			_pending_clarification_should_yield_to_current_control_decision(
				clarification_response_contract=clarification_contract,
				prior_branch_restore_control_decision_contract=restore_decision,
				conversation_control_decision_contract=restore_decision,
			)
		)
	def test_pending_clarification_does_not_yield_when_reopen_is_the_owner(self):
		clarification_contract = types.SimpleNamespace(
			decision="reask_pending_clarification",
		)
		reopen_decision = build_conversation_control_decision_contract(
			request_id="clarify-yield-1",
			decision_class="prior_branch_restore",
			decision_action="reopen_pending_clarification",
			target_state_class="prior_branch_restore",
		)

		self.assertFalse(
			_pending_clarification_should_yield_to_current_control_decision(
				clarification_response_contract=clarification_contract,
				prior_branch_restore_control_decision_contract=reopen_decision,
				conversation_control_decision_contract=None,
			)
		)

	def test_select_pending_clarification_override_owner_prefers_current_control_decision(self):
		restore_decision = build_conversation_control_decision_contract(
			request_id="clarify-owner-1",
			decision_class="recent_focus_continuation",
			decision_action="restore_recent_focus",
			target_state_class="recent_focus",
		)
		prior_branch_decision = build_conversation_control_decision_contract(
			request_id="clarify-owner-2",
			decision_class="prior_branch_restore",
			decision_action="replay_as_fresh_governed_query",
			target_state_class="prior_branch_restore",
		)

		selected = _select_pending_clarification_override_owner(
			prior_branch_restore_control_decision_contract=prior_branch_decision,
			conversation_control_decision_contract=restore_decision,
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "conversation_control_decision")
		self.assertEqual(str(selected.get("basis") or "").strip(), "current_control_restore_recent_focus")

	def test_select_pending_clarification_override_owner_uses_prior_branch_when_current_owner_is_absent(self):
		prior_branch_decision = build_conversation_control_decision_contract(
			request_id="clarify-owner-3",
			decision_class="prior_branch_restore",
			decision_action="replay_as_fresh_governed_query",
			target_state_class="prior_branch_restore",
		)

		selected = _select_pending_clarification_override_owner(
			prior_branch_restore_control_decision_contract=prior_branch_decision,
			conversation_control_decision_contract=None,
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "prior_branch_restore_decision")
		self.assertEqual(str(selected.get("basis") or "").strip(), "prior_branch_restore_override")

	def test_shared_control_support_clarification_decision_override_gate(self):
		self.assertTrue(
			clarification_decision_allows_immediate_control_override(clarification_decision="new_request")
		)
		self.assertFalse(
			clarification_decision_allows_immediate_control_override(clarification_decision="resolved_option")
		)

	def test_shared_control_support_pending_clarification_preempts_runtime_for_resolution(self):
		self.assertTrue(
			pending_clarification_response_should_preempt_runtime(clarification_decision="resolved_option")
		)
		self.assertTrue(
			pending_clarification_response_should_preempt_runtime(clarification_decision="reask_pending_clarification")
		)
		self.assertFalse(
			pending_clarification_response_should_preempt_runtime(clarification_decision="new_request")
		)
		self.assertFalse(
			pending_clarification_response_should_preempt_runtime(clarification_decision="")
		)

	def test_shared_control_support_initial_clarification_yield_gate(self):
		self.assertTrue(
			clarification_response_should_yield_initial_control_decision(
				clarification_decision="new_request",
				prior_branch_state={
					"owner": "prior_branch_restore_decision",
					"basis": "prior_branch_restore_override",
					"kind": "non_clarification_override",
				},
				control_action="",
			)
		)
		self.assertFalse(
			clarification_response_should_yield_initial_control_decision(
				clarification_decision="resolved_option",
				prior_branch_state={
					"owner": "prior_branch_restore_decision",
					"basis": "prior_branch_restore_override",
					"kind": "non_clarification_override",
				},
				control_action="",
			)
		)

	def test_shared_control_support_pending_clarification_yield_gate(self):
		prior_branch_state = {
			"owner": "prior_branch_restore_decision",
			"basis": "prior_branch_restore_override",
			"kind": "non_clarification_override",
		}
		self.assertTrue(
			pending_clarification_should_yield_to_current_control_decision(
				clarification_decision="new_request",
				current_decision_action="restore_recent_focus",
				prior_branch_state=prior_branch_state,
			)
		)
		self.assertFalse(
			pending_clarification_should_yield_to_current_control_decision(
				clarification_decision="show_options",
				current_decision_action="restore_recent_focus",
				prior_branch_state=prior_branch_state,
			)
		)
		self.assertFalse(
			pending_clarification_should_yield_to_current_control_decision(
				clarification_decision="reask_pending_clarification",
				current_decision_action="replay_as_fresh_governed_query",
				prior_branch_state={},
			)
		)

	def test_shared_control_support_clarification_response_decision_spec(self):
		spec = clarification_response_decision_spec(
			decision="new_request",
			raw_message="ignore that, show me suppliers",
			resolved_runtime_message="",
			override_business_message="show me suppliers",
		)
		self.assertEqual(str(spec.get("decision_class") or "").strip(), "fresh_request_override")
		self.assertEqual(str(spec.get("decision_action") or "").strip(), "override_with_new_request")
		self.assertEqual(str(spec.get("resolved_business_message") or "").strip(), "show me suppliers")
		self.assertTrue(bool(spec.get("clear_pending_clarification")))
		self.assertEqual(
			str((spec.get("internal_details_patch") or {}).get("override_business_message") or "").strip(),
			"show me suppliers",
		)
		other_spec = clarification_response_decision_spec(
			decision="meta_question",
			raw_message="what do you mean",
			resolved_runtime_message="",
			override_business_message="",
		)
		self.assertEqual(str(other_spec.get("decision_action") or "").strip(), "answer_pending_clarification_meta_question")
		self.assertFalse(bool(other_spec.get("clear_pending_clarification")))

	def test_business_language_guard_detects_subjective_operational_inference(self):
		self.assertTrue(
			looks_like_unsupported_operational_inference_claim(
				"based on this, which invoice was probably delayed because the customer was dissatisfied?"
			)
		)
		self.assertTrue(
			looks_like_unsupported_operational_inference_claim(
				"which sales order was likely delayed due to a dispute?"
			)
		)
		self.assertFalse(
			looks_like_unsupported_operational_inference_claim("why is the first customer risky?")
		)
		self.assertFalse(
			looks_like_unsupported_operational_inference_claim("show me the aging breakdown for the first customer")
		)

	def test_shared_control_support_frontdoor_clarification_reentry_and_reset_helpers(self):
		contract = types.SimpleNamespace(
			decision="resolved_option",
			resolved_slot={"entity_grain": "supplier"},
		)
		resolved_slot_payload = clarification_response_resolved_slot_payload(contract)
		self.assertEqual(str(resolved_slot_payload.get("entity_grain") or "").strip(), "supplier")
		self.assertEqual(
			frontdoor_clarification_reentry_message(
				raw_message="suppliers",
				clarification_lane="front_door",
				clarification_decision="resolved_option",
				clarified_runtime_message="",
				resolved_slot_payload=resolved_slot_payload,
			),
			"suppliers",
		)
		self.assertTrue(
			frontdoor_clarification_requires_fresh_query_reset(
				clarification_lane="front_door",
				clarification_decision="resolved_option",
				clarified_runtime_message="",
				resolved_slot_payload=resolved_slot_payload,
			)
		)
		self.assertTrue(
			artifact_boundary_clarification_requires_runtime_reset(
				clarification_lane="artifact_boundary",
				clarification_decision="resolved_option",
				clarified_runtime_message="what is this customer tenure by first sales order date?",
			)
		)
		self.assertFalse(
			frontdoor_clarification_reentry_message(
				raw_message="suppliers",
				clarification_lane="artifact_boundary",
				clarification_decision="resolved_option",
				clarified_runtime_message="",
				resolved_slot_payload=resolved_slot_payload,
			)
		)

	def test_shared_control_support_resolved_clarification_runtime_message(self):
		signal = _clarification_signal(request_id="clarify-entity-runtime-shared", user_question="Choose one tenure basis.")
		signal["internal_details"] = {
			"continuation_lane": "artifact_boundary",
			"resolved_message_by_option": {
				"Customer Tenure by First Sales Order": "what is this customer's tenure by first sales order date?",
			},
		}
		self.assertEqual(
			resolved_clarification_runtime_message(
				raw_message="ignore that, show me suppliers",
				pending_clarification_signal=signal,
				clarification_decision="new_request",
				resolved_option="",
			),
			"ignore that, show me suppliers",
		)
		self.assertEqual(
			resolved_clarification_runtime_message(
				raw_message="by first sales order",
				pending_clarification_signal=signal,
				clarification_decision="resolved_option",
				resolved_option="Customer Tenure by First Sales Order",
			),
			"what is this customer's tenure by first sales order date?",
		)
		self.assertEqual(
			resolved_clarification_runtime_message(
				raw_message="by first sales order",
				pending_clarification_signal=signal,
				clarification_decision="show_options",
				resolved_option="Customer Tenure by First Sales Order",
			),
			"",
		)

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

	def test_select_compound_cancellation_sequence_source_prefers_cancelled_sequence_payload(self):
		active_payload = build_compound_request_assessment_contract(
			request_id="compound-cancel-source-active",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some customer list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some customer list",
				"remaining_segment_messages": [],
			},
		).to_payload()
		cancelled_payload = build_compound_request_assessment_contract(
			request_id="compound-cancel-source-cancelled",
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

		selected = _select_compound_cancellation_sequence_source(
			active_sequence_payload=active_payload,
			cancelled_sequence_payload=cancelled_payload,
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "cancelled_sequence_payload")
		self.assertEqual(str(selected.get("basis") or "").strip(), "cancelled_sequence_payload_available")

	def test_select_compound_cancellation_sequence_source_falls_back_to_active_sequence_payload(self):
		active_payload = build_compound_request_assessment_contract(
			request_id="compound-cancel-source-active-fallback",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some customer list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some customer list",
				"remaining_segment_messages": [],
			},
		).to_payload()

		selected = _select_compound_cancellation_sequence_source(
			active_sequence_payload=active_payload,
			cancelled_sequence_payload={},
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "active_sequence_payload")
		self.assertEqual(str(selected.get("basis") or "").strip(), "active_sequence_payload_fallback")

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

	def test_select_compound_continuation_eligibility_allows_active_sequence_continuation(self):
		compound_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-cont-eligibility-1",
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

		selected = _select_compound_continuation_eligibility(
			raw_message="continue",
			active_sequence_payload=compound_payload,
			runtime_message="give me some supplier list",
			control_evidence_payload=None,
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "allow")
		self.assertEqual(str(selected.get("basis") or "").strip(), "active_sequence_continuation")

	def test_select_compound_continuation_eligibility_blocks_missing_runtime_message(self):
		compound_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-cont-eligibility-2",
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

		selected = _select_compound_continuation_eligibility(
			raw_message="continue",
			active_sequence_payload=compound_payload,
			runtime_message="",
			control_evidence_payload=None,
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "block")
		self.assertEqual(str(selected.get("basis") or "").strip(), "missing_runtime_message")

	def test_select_compound_continuation_eligibility_blocks_when_sequence_is_unavailable(self):
		selected = _select_compound_continuation_eligibility(
			raw_message="continue",
			active_sequence_payload={},
			runtime_message="give me some supplier list",
			control_evidence_payload=None,
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "block")
		self.assertEqual(str(selected.get("basis") or "").strip(), "active_sequence_unavailable")

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

	def test_select_compound_completion_reentry_action_for_completed_sequence(self):
		completed_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-3-action-complete",
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

		selected = _select_compound_completion_reentry_action(
			compound_assessment_payload=completed_payload,
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "acknowledge_completed_sequence")
		self.assertEqual(str(selected.get("basis") or "").strip(), "ordered_execution_complete")

	def test_select_compound_completion_reentry_action_for_cancelled_sequence(self):
		cancelled_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-3-action-cancelled",
			status="ordered_execution_cancelled",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request cancelled.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "",
				"remaining_segment_messages": [],
				"cancelled": True,
			},
		).to_payload()

		selected = _select_compound_completion_reentry_action(
			compound_assessment_payload=cancelled_payload,
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "acknowledge_cancelled_sequence")
		self.assertEqual(str(selected.get("basis") or "").strip(), "ordered_execution_cancelled")

	def test_select_compound_completion_reentry_eligibility_allows_supported_completion_reentry(self):
		selected = _select_compound_completion_reentry_eligibility(
			raw_message="continue",
			completion_answer="That sequence is already finished. You can start a new request anytime.",
			decision_action="acknowledge_completed_sequence",
			control_evidence_payload=None,
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "allow")
		self.assertEqual(str(selected.get("basis") or "").strip(), "compound_completion_reentry")

	def test_select_compound_completion_reentry_eligibility_blocks_missing_completion_answer(self):
		selected = _select_compound_completion_reentry_eligibility(
			raw_message="continue",
			completion_answer="",
			decision_action="acknowledge_completed_sequence",
			control_evidence_payload=None,
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "block")
		self.assertEqual(str(selected.get("basis") or "").strip(), "missing_completion_answer")

	def test_select_compound_completion_reentry_eligibility_blocks_unsupported_completion_status(self):
		selected = _select_compound_completion_reentry_eligibility(
			raw_message="continue",
			completion_answer="That sequence is already finished. You can start a new request anytime.",
			decision_action="",
			control_evidence_payload=None,
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "block")
		self.assertEqual(str(selected.get("basis") or "").strip(), "unsupported_completion_status")

	def test_select_compound_completion_reentry_response_allows_completed_sequence(self):
		completed_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-3-response-complete",
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

		selected = _select_compound_completion_reentry_response(
			compound_assessment_payload=completed_payload,
			raw_message="continue",
			control_evidence_payload=None,
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "allow")
		self.assertEqual(str(selected.get("basis") or "").strip(), "compound_completion_reentry")
		self.assertEqual(str(selected.get("decision_action") or "").strip(), "acknowledge_completed_sequence")
		self.assertIn("already finished", str(selected.get("completion_answer") or "").strip().lower())

	def test_select_compound_completion_reentry_response_blocks_non_continuation_message(self):
		completed_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-3-response-blocked",
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

		selected = _select_compound_completion_reentry_response(
			compound_assessment_payload=completed_payload,
			raw_message="show me suppliers",
			control_evidence_payload=None,
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "block")
		self.assertEqual(str(selected.get("basis") or "").strip(), "not_continuation_control")
		self.assertEqual(str(selected.get("decision_action") or "").strip(), "acknowledge_completed_sequence")
		self.assertIn("already finished", str(selected.get("completion_answer") or "").strip().lower())

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

	def test_compound_request_completion_superseding_state_records_pending_clarification_owner_and_basis(self):
		active_sequence_state = {
			"available": True,
			"status": "ordered_execution_complete",
			"source_tool_index": 10,
		}
		pending_clarification_state = {
			"available": True,
			"source_tool_index": 14,
		}

		selection = _select_compound_request_completion_superseding_state(
			active_sequence_state=active_sequence_state,
			pending_clarification_state=pending_clarification_state,
			recent_focus_state={},
			resumable_prior_request_state={},
		)

		self.assertEqual(selection.get("owner"), "pending_clarification")
		self.assertEqual(
			selection.get("basis"),
			"pending_clarification_precedes_completed_sequence_by_newer_index",
		)

	def test_compound_request_completion_is_not_superseded_by_non_authoritative_pending_clarification(self):
		active_sequence_state = {
			"available": True,
			"status": "ordered_execution_complete",
			"source_tool_index": 10,
		}
		pending_clarification_state = {
			"available": True,
			"source_kind": "message_fallback",
			"source_tool_index": -1,
		}

		self.assertFalse(
			_compound_request_completion_is_superseded_by_newer_state(
				active_sequence_state=active_sequence_state,
				pending_clarification_state=pending_clarification_state,
				recent_focus_state={},
				resumable_prior_request_state={},
			)
		)

	def test_compound_request_completion_superseding_state_ignores_non_authoritative_pending_clarification(self):
		active_sequence_state = {
			"available": True,
			"status": "ordered_execution_complete",
			"source_tool_index": 10,
		}
		pending_clarification_state = {
			"available": True,
			"source_kind": "message_fallback",
			"source_tool_index": -1,
		}

		selection = _select_compound_request_completion_superseding_state(
			active_sequence_state=active_sequence_state,
			pending_clarification_state=pending_clarification_state,
			recent_focus_state={},
			resumable_prior_request_state={},
		)

		self.assertEqual(selection, {"owner": "", "basis": ""})

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

	def test_compound_request_completion_superseding_state_records_recent_focus_owner_and_basis(self):
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

		selection = _select_compound_request_completion_superseding_state(
			active_sequence_state=active_sequence_state,
			pending_clarification_state={},
			recent_focus_state=recent_focus_state,
			resumable_prior_request_state={},
		)

		self.assertEqual(selection.get("owner"), "recent_focus")
		self.assertEqual(
			selection.get("basis"),
			"recent_focus_precedes_completed_sequence_by_newer_index",
		)

	def test_shared_compound_request_completion_superseding_state_matches_service_contract(self):
		active_sequence_state = {
			"available": True,
			"status": "ordered_execution_complete",
			"source_tool_index": 10,
		}
		pending_clarification_state = {
			"available": True,
			"source_tool_index": 14,
		}

		selection = shared_select_compound_request_completion_superseding_state(
			active_sequence_state=active_sequence_state,
			pending_clarification_state=pending_clarification_state,
			recent_focus_state={},
			resumable_prior_request_state={},
		)

		self.assertEqual(
			selection,
			_select_compound_request_completion_superseding_state(
				active_sequence_state=active_sequence_state,
				pending_clarification_state=pending_clarification_state,
				recent_focus_state={},
				resumable_prior_request_state={},
			),
		)
		self.assertEqual(str(selection.get("owner") or "").strip(), "pending_clarification")

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

	def test_compound_request_completion_answer_ignores_non_authoritative_pending_clarification(self):
		completed_payload = build_compound_request_assessment_contract(
			request_id="compound-seq-3b-fallback",
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
				"source_kind": "message_fallback",
				"source_tool_index": -1,
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
		self.assertTrue(
			_compound_request_continuation_control_with_evidence(
				"go ahead with the next one",
				control_evidence_payload=None,
			)
		)
		self.assertTrue(
			_compound_request_continuation_control_with_evidence(
				"continue with that",
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
		self.assertTrue(
			_compound_request_stop_control_with_evidence(
				"stop this sequence",
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

	def test_reasoning_preempted_by_followup_refinement_accepts_grounded_detail_followup(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="reasoning-preempt-1",
			mode="grounded_follow_up",
			requested_modes=["detail_followup"],
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The request is a contextual detail follow-up on a single grounded ERP row and should stay anchored to that focus.",
		)

		self.assertTrue(_reasoning_preempted_by_followup_refinement(followup_resolution))

	def test_accepted_reasoning_supersedes_capability_requery_refinement(self):
		accepted_reasoning = types.SimpleNamespace(
			status="accepted",
			intent=types.SimpleNamespace(reasoning_type="explanation"),
		)
		followup_resolution = build_followup_resolution_contract(
			request_id="reasoning-supersede-1",
			mode="capability_requery",
			requested_modes=["dimension_breakdown"],
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The follow-up asks for an explanation that can be answered from the current grounded artifact.",
		)

		self.assertTrue(_reasoning_preempted_by_followup_refinement(followup_resolution))
		self.assertTrue(
			_reasoning_activation_supersedes_followup_refinement(
				reasoning_semantic_result=accepted_reasoning,
				followup_resolution=followup_resolution,
			)
		)

	def test_accepted_reasoning_does_not_supersede_entity_detail_followup(self):
		accepted_reasoning = types.SimpleNamespace(
			status="accepted",
			intent=types.SimpleNamespace(reasoning_type="continuation_detail"),
		)
		followup_resolution = build_followup_resolution_contract(
			request_id="reasoning-supersede-2",
			mode="grounded_follow_up",
			requested_modes=["detail_followup"],
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The follow-up asks for more detail about a selected row.",
		)

		self.assertTrue(_reasoning_preempted_by_followup_refinement(followup_resolution))
		self.assertFalse(
			_reasoning_activation_supersedes_followup_refinement(
				reasoning_semantic_result=accepted_reasoning,
				followup_resolution=followup_resolution,
			)
		)

	def test_artifact_level_reasoning_supersedes_generic_grounded_detail_followup(self):
		accepted_reasoning = types.SimpleNamespace(
			status="accepted",
			intent=types.SimpleNamespace(reasoning_type="interpretation"),
		)
		followup_resolution = build_followup_resolution_contract(
			request_id="reasoning-supersede-3",
			mode="grounded_follow_up",
			requested_modes=["detail_followup"],
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The follow-up asks what the current grounded artifact means.",
		)

		self.assertFalse(
			_reasoning_activation_supersedes_followup_refinement(
				reasoning_semantic_result=accepted_reasoning,
				followup_resolution=followup_resolution,
			)
		)
		self.assertTrue(
			_reasoning_activation_supersedes_followup_refinement(
				reasoning_semantic_result=accepted_reasoning,
				followup_resolution=followup_resolution,
				artifact_level_context_requested=True,
			)
		)

	def test_artifact_level_reasoning_supersedes_new_query_followup_classification(self):
		accepted_reasoning = types.SimpleNamespace(
			status="accepted",
			intent=types.SimpleNamespace(reasoning_type="interpretation"),
		)
		followup_resolution = build_followup_resolution_contract(
			request_id="reasoning-supersede-4",
			mode="new_query",
			requested_modes=[],
			depends_on_grounded_turn=False,
			self_contained=True,
			latest_grounded_turn_available=True,
			reason="The semantic follow-up classified this as explanation of the previous response.",
		)

		self.assertFalse(
			_reasoning_activation_supersedes_followup_refinement(
				reasoning_semantic_result=accepted_reasoning,
				followup_resolution=followup_resolution,
			)
		)
		self.assertTrue(
			_reasoning_activation_supersedes_followup_refinement(
				reasoning_semantic_result=accepted_reasoning,
				followup_resolution=followup_resolution,
				artifact_level_context_requested=True,
			)
		)

	def test_recent_focus_decision_accepts_shared_affordance_passthrough(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "listing",
			"focus_grain": "supplier",
			"focus_label": "Supplier Master List",
			"focus_key": "supplier",
			"source_request_id": "supplier-list-2",
			"source_family": "master_data_directory",
			"source_capability": "supplier_master_read",
			"source_report": "Supplier Master List",
			"deictic_allowed": True,
			"explicit_named_allowed": False,
			"confidence": 0.84,
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-listing-1",
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
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-listing-1",
			recent_focus_state=recent_focus_state,
		)

		decision_contract = _conversation_control_decision_from_recent_focus_runtime_message(
			request_id="recent-focus-listing-1",
			raw_message="show supplier name and payment terms only",
			runtime_message="show supplier name and payment terms only",
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			recent_focus_affordance_contract=affordance_contract,
			routing_basis="shared_affordance",
		)
		payload = decision_contract.to_payload()

		self.assertEqual(str(payload.get("decision_class") or "").strip(), "recent_focus_continuation")
		self.assertEqual(str(payload.get("resolved_business_message") or "").strip(), "show supplier name and payment terms only")
		self.assertEqual(
			str(((payload.get("internal_details") or {}).get("routing_basis") or "").strip()),
			"shared_affordance",
		)
		self.assertEqual(
			str((((payload.get("internal_details") or {}).get("recent_focus_affordance") or {}).get("type")) or "").strip(),
			"qwen_recent_focus_affordance_contract",
		)

	def test_select_recent_focus_continuation_eligibility_allows_shared_affordance_passthrough(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "listing",
			"focus_grain": "supplier",
			"focus_label": "Supplier Master List",
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-eligibility-1",
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

		selected = _select_recent_focus_continuation_eligibility(
			raw_message="show supplier name and payment terms only",
			runtime_message="show supplier name and payment terms only",
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			control_evidence_payload=None,
			routing_basis="shared_affordance",
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "allow")
		self.assertEqual(str(selected.get("basis") or "").strip(), "shared_affordance_passthrough")
		self.assertTrue(bool(selected.get("allow_passthrough")))

	def test_select_recent_focus_continuation_eligibility_blocks_strong_control_owner(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "entity",
			"focus_grain": "item",
			"focus_label": "Type-C Cable 1m Fast Charge",
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-eligibility-2",
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

		selected = _select_recent_focus_continuation_eligibility(
			raw_message="ignore that, show me suppliers",
			runtime_message='how many stocks do we have, and in which warehouse for item "Type-C Cable 1m Fast Charge"?',
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			control_evidence_payload={
				"evidence_class": "fresh_request_redirect",
				"action_id": "override_with_new_request",
				"embedded_business_message": "show me suppliers",
			},
			routing_basis="",
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "block")
		self.assertEqual(str(selected.get("basis") or "").strip(), "strong_control_owner")

	def test_select_recent_focus_continuation_eligibility_blocks_passthroughless_identity_transform(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "entity",
			"focus_grain": "item",
			"focus_label": "Type-C Cable 1m Fast Charge",
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-eligibility-3",
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

		selected = _select_recent_focus_continuation_eligibility(
			raw_message="how many stocks do we have, and in which warehouse?",
			runtime_message="how many stocks do we have, and in which warehouse?",
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			control_evidence_payload=None,
			routing_basis="",
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "block")
		self.assertEqual(str(selected.get("basis") or "").strip(), "runtime_matches_raw_without_passthrough")

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
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"pending_clarification_precedes_question_restore",
		)

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
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"pending_clarification_precedes_question_restore",
		)

	def test_build_authoritative_pending_clarification_restore_contract_records_question_restore_basis(self):
		contract = _build_authoritative_pending_clarification_restore_contract(
			request_id="restore-authoritative-pending-1",
			phrase_type="question_restore",
			pending_clarification={
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-authoritative-1",
					"user_question": "Which financial view would you like to see?",
				},
			},
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"pending_clarification_precedes_question_restore",
		)

	def test_build_authoritative_pending_clarification_restore_contract_records_branch_restore_basis(self):
		contract = _build_authoritative_pending_clarification_restore_contract(
			request_id="restore-authoritative-pending-2",
			phrase_type="branch_restore",
			pending_clarification={
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-authoritative-2",
					"user_question": "Which financial view would you like to see?",
				},
			},
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"pending_clarification_precedes_generic_prior_branch_restore",
		)

	def test_select_prior_branch_restore_route_prefers_targeted_recent_focus(self):
		selected = _select_prior_branch_restore_route(
			phrase_type="branch_restore",
			pending_clarification={"available": True},
			active_sequence={"active": True},
			recent_focus={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "customer",
				"focus_label": "Customer Master List",
				"source_report": "Customer Master List",
			},
			resumable_prior_request={"available": True},
			target_hint="customer",
			target_grain="customer",
			target_focus_kind="listing",
		)

		self.assertEqual(str(selected.get("route") or "").strip(), "targeted_recent_focus")
		self.assertEqual(str(selected.get("basis") or "").strip(), "targeted_recent_focus_restore")

	def test_select_prior_branch_restore_route_blocks_unmatched_targeted_branch_restore(self):
		selected = _select_prior_branch_restore_route(
			phrase_type="branch_restore",
			pending_clarification={"available": False},
			active_sequence={"active": False},
			recent_focus={"available": False},
			resumable_prior_request={"available": False},
			target_hint="supplier",
			target_grain="supplier",
			target_focus_kind="listing",
		)

		self.assertEqual(str(selected.get("route") or "").strip(), "targeted_no_match_block")
		self.assertEqual(
			str(selected.get("basis") or "").strip(),
			"targeted_restore_requested_without_matching_owner",
		)

	def test_select_prior_branch_restore_route_uses_latest_non_clarification_owner(self):
		selected = _select_prior_branch_restore_route(
			phrase_type="question_restore",
			pending_clarification={"available": False, "source_tool_index": -1},
			active_sequence={
				"available": True,
				"active": True,
				"request_id": "sequence-route-1",
				"status": "ordered_execution_in_progress",
				"primary_segment_message": "give me some supplier list",
				"source_tool_index": 10,
			},
			recent_focus={"available": False, "source_tool_index": -1},
			resumable_prior_request={"available": False, "source_tool_index": -1},
			target_hint="",
			target_grain="",
			target_focus_kind="",
		)

		self.assertEqual(str(selected.get("route") or "").strip(), "latest_non_clarification")
		self.assertEqual(str(selected.get("owner") or "").strip(), "active_sequence")
		self.assertEqual(str(selected.get("basis") or "").strip(), "question_restore_uses_active_sequence")

	def test_select_prior_branch_restore_route_uses_authoritative_pending_clarification(self):
		selected = _select_prior_branch_restore_route(
			phrase_type="question_restore",
			pending_clarification={
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-route-1",
					"user_question": "Which financial view would you like to see?",
				},
				"source_tool_index": 5,
			},
			active_sequence={"active": False},
			recent_focus={"available": False, "source_tool_index": -1},
			resumable_prior_request={"available": False, "source_tool_index": -1},
			target_hint="",
			target_grain="",
			target_focus_kind="",
		)

		self.assertEqual(str(selected.get("route") or "").strip(), "authoritative_pending_clarification")
		self.assertEqual(str(selected.get("owner") or "").strip(), "pending_clarification")
		self.assertEqual(
			str(selected.get("basis") or "").strip(),
			"pending_clarification_precedes_question_restore",
		)

	def test_select_prior_branch_restore_route_uses_direct_fallback_for_sequence_restore(self):
		selected = _select_prior_branch_restore_route(
			phrase_type="sequence_restore",
			pending_clarification={"available": False},
			active_sequence={"active": True, "request_id": "sequence-route-fallback-1"},
			recent_focus={"available": False},
			resumable_prior_request={
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
			},
			target_hint="",
			target_grain="",
			target_focus_kind="",
		)

		self.assertEqual(str(selected.get("route") or "").strip(), "direct_restore_fallback")
		self.assertEqual(str(selected.get("owner") or "").strip(), "active_sequence")
		self.assertEqual(
			str(selected.get("basis") or "").strip(),
			"sequence_restore_uses_active_sequence",
		)

	def test_question_restore_does_not_reopen_non_authoritative_pending_clarification_without_other_owner(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"source_kind": "message_fallback",
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-restore-fallback-direct-1",
					"user_question": "Which financial view would you like to see?",
				},
				"source_tool_index": -1,
			},
			"active_sequence": {"active": False},
			"recent_focus": {"available": False, "source_tool_index": -1},
			"resumable_prior_request": {"available": False, "source_tool_index": -1},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-fallback-direct-1",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)

		self.assertIsNone(contract)

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

	def test_question_restore_uses_active_sequence_when_it_is_the_latest_unresolved_owner(self):
		snapshot = {
			"pending_clarification": {"available": False, "source_tool_index": -1},
			"active_sequence": {
				"available": True,
				"active": True,
				"request_id": "sequence-question-restore-1",
				"status": "ordered_execution_in_progress",
				"primary_segment_message": "give me some supplier list",
				"source_tool_index": 10,
			},
			"recent_focus": {
				"available": True,
				"focus_kind": "list",
				"focus_grain": "payment_entry",
				"focus_label": "Payment Entries",
				"source_request_id": "grounded-payment-restore-1",
				"source_family": "transaction_listing",
				"source_report": "Payment Entry List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
				"derivation_basis": "transaction_listing_grounded_turn",
				"confidence": 0.9,
				"source_tool_index": 8,
			},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-prior-trace-seq-1",
				"target_family": "entity_detail",
				"resumable": True,
				"suggested_restore_mode": "restore_recent_focus",
				"derivation_basis": "historical_grounded_turn_with_newer_active_sequence",
				"confidence": 0.84,
				"source_tool_index": 4,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-seq-1",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "resume_active_sequence")
		self.assertEqual(str(payload.get("target_branch_kind") or "").strip(), "sequence")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "give me some supplier list")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"question_restore_uses_active_sequence",
		)

	def test_question_restore_prefers_newer_active_sequence_over_older_pending_clarification(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-seq-restore-1",
					"user_question": "Which financial view would you like to see?",
				},
				"source_tool_index": 2,
			},
			"active_sequence": {
				"available": True,
				"active": True,
				"request_id": "sequence-question-restore-2",
				"status": "ordered_execution_in_progress",
				"primary_segment_message": "give me some supplier list",
				"source_tool_index": 9,
			},
			"recent_focus": {
				"available": True,
				"focus_kind": "list",
				"focus_grain": "payment_entry",
				"focus_label": "Payment Entries",
				"source_request_id": "grounded-payment-restore-2",
				"source_family": "transaction_listing",
				"source_report": "Payment Entry List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
				"derivation_basis": "transaction_listing_grounded_turn",
				"confidence": 0.9,
				"source_tool_index": 7,
			},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-prior-trace-seq-2",
				"target_family": "entity_detail",
				"resumable": True,
				"suggested_restore_mode": "restore_recent_focus",
				"derivation_basis": "historical_grounded_turn_with_newer_active_sequence",
				"confidence": 0.84,
				"source_tool_index": 5,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-seq-2",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "resume_active_sequence")
		self.assertTrue(bool(payload.get("clear_current_pending_clarification")))
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"newer_active_sequence_precedes_older_pending_clarification",
		)

	def test_question_restore_prefers_known_active_sequence_over_non_authoritative_pending_clarification(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"source_kind": "message_fallback",
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-seq-restore-fallback-1",
					"user_question": "Which financial view would you like to see?",
				},
				"source_tool_index": -1,
			},
			"active_sequence": {
				"available": True,
				"active": True,
				"request_id": "sequence-question-restore-fallback-1",
				"status": "ordered_execution_in_progress",
				"primary_segment_message": "give me some supplier list",
				"source_tool_index": 9,
			},
			"recent_focus": {"available": False, "source_tool_index": -1},
			"resumable_prior_request": {"available": False, "source_tool_index": -1},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-seq-fallback-1",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "resume_active_sequence")
		self.assertTrue(bool(payload.get("clear_current_pending_clarification")))
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"known_active_sequence_precedes_non_authoritative_pending_clarification",
		)

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

	def test_question_restore_prefers_known_recent_focus_over_non_authoritative_pending_clarification(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"source_kind": "message_fallback",
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-restore-recent-fallback-1",
					"user_question": "Which item do you mean?",
				},
				"source_tool_index": -1,
			},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-fallback-1",
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
			request_id="restore-turn-recent-fallback-1",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertTrue(bool(payload.get("clear_current_pending_clarification")))
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"known_recent_focus_precedes_non_authoritative_pending_clarification",
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

	def test_question_restore_prefers_known_recent_focus_over_unindexed_resumable_prior_request(self):
		snapshot = {
			"pending_clarification": {"available": False, "source_tool_index": -1},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-known-1",
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
				"source_request_id": "grounded-prior-trace-known-1",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
				"source_tool_index": -1,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-known-1",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"question_restore_prefers_known_recent_focus_over_unindexed_resumable_prior_request",
		)

	def test_question_restore_defaults_to_recent_focus_when_peer_precedence_is_indeterminate(self):
		snapshot = {
			"pending_clarification": {"available": False, "source_tool_index": -1},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-default-1",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.91,
				"source_tool_index": -1,
			},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-default-1",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
				"source_tool_index": -1,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-default-1",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"question_restore_defaults_to_recent_focus_when_peer_precedence_is_indeterminate",
		)

	def test_select_non_clarification_restore_owner_prefers_recent_focus_by_known_over_unindexed(self):
		selected = _select_non_clarification_restore_owner(
			recent_focus={"available": True, "source_tool_index": 7},
			resumable_prior_request={"available": True, "source_tool_index": -1},
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "recent_focus")
		self.assertEqual(
			str(selected.get("basis") or "").strip(),
			"recent_focus_precedes_resumable_prior_request_by_known_over_unindexed",
		)

	def test_select_non_clarification_restore_owner_defaults_recent_focus_when_peer_precedence_is_indeterminate(self):
		selected = _select_non_clarification_restore_owner(
			recent_focus={"available": True, "source_tool_index": -1},
			resumable_prior_request={"available": True, "source_tool_index": -1},
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "recent_focus")
		self.assertEqual(
			str(selected.get("basis") or "").strip(),
			"recent_focus_defaults_when_peer_precedence_is_indeterminate",
		)

	def test_select_latest_non_clarification_restore_state_prefers_active_sequence(self):
		selected = _select_latest_non_clarification_restore_state(
			phrase_type="question_restore",
			pending_clarification={"available": False, "source_tool_index": -1},
			active_sequence={"available": True, "active": True, "source_tool_index": 9},
			recent_focus={"available": True, "source_tool_index": 7},
			resumable_prior_request={"available": True, "source_tool_index": 5},
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "active_sequence")
		self.assertEqual(
			str(selected.get("basis") or "").strip(),
			"question_restore_uses_active_sequence",
		)
		self.assertFalse(bool(selected.get("clear_pending_clarification")))

	def test_select_latest_non_clarification_restore_state_prefers_known_active_sequence_over_non_authoritative_pending(self):
		selected = _select_latest_non_clarification_restore_state(
			phrase_type="question_restore",
			pending_clarification={"available": True, "source_kind": "message_fallback", "source_tool_index": -1},
			active_sequence={"available": True, "active": True, "source_tool_index": 9},
			recent_focus={"available": False, "source_tool_index": -1},
			resumable_prior_request={"available": False, "source_tool_index": -1},
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "active_sequence")
		self.assertEqual(
			str(selected.get("basis") or "").strip(),
			"known_active_sequence_precedes_non_authoritative_pending_clarification",
		)
		self.assertTrue(bool(selected.get("clear_pending_clarification")))

	def test_select_latest_non_clarification_restore_state_prefers_known_recent_focus_over_unindexed_resumable(self):
		selected = _select_latest_non_clarification_restore_state(
			phrase_type="question_restore",
			pending_clarification={"available": False, "source_tool_index": -1},
			active_sequence={"active": False},
			recent_focus={"available": True, "source_tool_index": 9},
			resumable_prior_request={"available": True, "source_tool_index": -1},
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "recent_focus")
		self.assertEqual(
			str(selected.get("basis") or "").strip(),
			"question_restore_prefers_known_recent_focus_over_unindexed_resumable_prior_request",
		)

	def test_select_latest_non_clarification_restore_state_defaults_recent_focus_when_peer_precedence_is_indeterminate(self):
		selected = _select_latest_non_clarification_restore_state(
			phrase_type="question_restore",
			pending_clarification={"available": False, "source_tool_index": -1},
			active_sequence={"active": False},
			recent_focus={"available": True, "source_tool_index": -1},
			resumable_prior_request={"available": True, "source_tool_index": -1},
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "recent_focus")
		self.assertEqual(
			str(selected.get("basis") or "").strip(),
			"question_restore_defaults_to_recent_focus_when_peer_precedence_is_indeterminate",
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

	def test_generic_branch_restore_prefers_known_resumable_prior_request_over_unindexed_recent_focus(self):
		snapshot = {
			"pending_clarification": {"available": False, "source_tool_index": -1},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-known-2",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.91,
				"source_tool_index": -1,
			},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-known-2",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
				"source_tool_index": 9,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-known-2",
			raw_message="go back",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "replay_as_fresh_governed_query")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"generic_branch_restore_prefers_known_resumable_prior_request_over_unindexed_recent_focus",
		)

	def test_generic_branch_restore_defaults_to_recent_focus_when_peer_precedence_is_indeterminate(self):
		snapshot = {
			"pending_clarification": {"available": False, "source_tool_index": -1},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "grounded-customer-restore-default-2",
				"source_family": "entity_detail",
				"source_capability": "customer_sales_detail",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "entity_detail_grounded_turn",
				"confidence": 0.91,
				"source_tool_index": -1,
			},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-default-2",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
				"source_tool_index": -1,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-default-2",
			raw_message="go back",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"generic_branch_restore_defaults_to_recent_focus_when_peer_precedence_is_indeterminate",
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

	def test_generic_branch_restore_prefers_known_resumable_prior_request_over_non_authoritative_pending_clarification(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"source_kind": "message_fallback",
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-restore-prior-fallback-1",
					"user_question": "Which item do you mean?",
				},
				"source_tool_index": -1,
			},
			"active_sequence": {"active": False},
			"recent_focus": {"available": False, "source_tool_index": -1},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-fallback-1",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
				"source_tool_index": 8,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-prior-fallback-1",
			raw_message="go back",
			conversation_state_snapshot=snapshot,
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "replay_as_fresh_governed_query")
		self.assertTrue(bool(payload.get("clear_current_pending_clarification")))
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"generic_branch_restore_prefers_known_resumable_prior_request_over_non_authoritative_pending_clarification",
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
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"sequence_restore_uses_active_sequence",
		)

	def test_build_direct_restore_fallback_contract_records_sequence_restore_basis(self):
		contract = _build_direct_restore_fallback_contract(
			request_id="restore-fallback-sequence-1",
			phrase_type="sequence_restore",
			active_sequence={
				"active": True,
				"request_id": "sequence-fallback-1",
				"status": "ordered_execution_in_progress",
				"primary_segment_message": "give me some supplier list",
			},
			resumable_prior_request={},
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "resume_active_sequence")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"sequence_restore_uses_active_sequence",
		)

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

	def test_build_superseded_active_sequence_transition_cancels_prior_sequence_for_plain_business_override(self):
		latest_active_payload = build_compound_request_assessment_contract(
			request_id="compound-supersede-1",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()

		cancelled_payload, decision_contract = _build_superseded_active_sequence_transition(
			request_id="supersede-turn-1",
			raw_message='do u have customer name similar to "Nay Lin Mobile"?',
			latest_active_sequence_payload=latest_active_payload,
			current_active_sequence_payload={},
			control_evidence_payload=None,
			conversation_control_decision_contract=None,
			prior_branch_restore_control_decision_contract=None,
			frontdoor_contract=types.SimpleNamespace(intent_class="route_onward"),
		)

		self.assertEqual(str(cancelled_payload.get("status") or "").strip(), "ordered_execution_cancelled")
		self.assertIsNotNone(decision_contract)
		self.assertEqual(str(getattr(decision_contract, "decision_action", "") or "").strip(), "cancel_active_sequence")
		self.assertEqual(
			str(getattr(decision_contract, "decision_class", "") or "").strip(),
			"sequence_superseded",
		)

	def test_build_superseded_active_sequence_transition_keeps_sequence_for_low_signal_turn(self):
		latest_active_payload = build_compound_request_assessment_contract(
			request_id="compound-supersede-2",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()

		cancelled_payload, decision_contract = _build_superseded_active_sequence_transition(
			request_id="supersede-turn-2",
			raw_message="thanks",
			latest_active_sequence_payload=latest_active_payload,
			current_active_sequence_payload={},
			control_evidence_payload=None,
			conversation_control_decision_contract=None,
			prior_branch_restore_control_decision_contract=None,
			frontdoor_contract=types.SimpleNamespace(intent_class="thanks"),
		)

		self.assertEqual(cancelled_payload, {})
		self.assertIsNone(decision_contract)

	def test_select_active_sequence_superseding_owner_prefers_explicit_new_request_override(self):
		active_payload = build_compound_request_assessment_contract(
			request_id="supersede-owner-active-1",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()
		selected = _select_active_sequence_superseding_owner(
			raw_message="ignore that, show me suppliers",
			latest_active_sequence_payload=active_payload,
			current_active_sequence_payload={},
			control_evidence_payload={"action_id": "override_with_new_request"},
			conversation_control_decision_contract=None,
			prior_branch_restore_control_decision_contract=None,
			frontdoor_contract=types.SimpleNamespace(intent_class="route_onward"),
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "control_action")
		self.assertEqual(str(selected.get("basis") or "").strip(), "explicit_new_request_override")

	def test_select_active_sequence_superseding_owner_prefers_shared_owner_decision(self):
		active_payload = build_compound_request_assessment_contract(
			request_id="supersede-owner-active-2",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()
		selected = _select_active_sequence_superseding_owner(
			raw_message="show me suppliers",
			latest_active_sequence_payload=active_payload,
			current_active_sequence_payload={},
			control_evidence_payload=None,
			conversation_control_decision_contract=build_conversation_control_decision_contract(
				request_id="supersede-owner-1",
				decision_class="recent_focus_continuation",
				decision_action="restore_recent_focus",
				target_state_class="recent_focus",
			),
			prior_branch_restore_control_decision_contract=build_conversation_control_decision_contract(
				request_id="supersede-owner-2",
				decision_class="prior_branch_restore",
				decision_action="replay_as_fresh_governed_query",
				target_state_class="prior_branch_restore",
			),
			frontdoor_contract=types.SimpleNamespace(intent_class="route_onward"),
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "conversation_control_decision")
		self.assertEqual(str(selected.get("basis") or "").strip(), "shared_owner_override")

	def test_select_active_sequence_superseding_owner_uses_prior_branch_override_when_current_owner_is_absent(self):
		active_payload = build_compound_request_assessment_contract(
			request_id="supersede-owner-active-3",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()
		selected = _select_active_sequence_superseding_owner(
			raw_message="go back",
			latest_active_sequence_payload=active_payload,
			current_active_sequence_payload={},
			control_evidence_payload=None,
			conversation_control_decision_contract=None,
			prior_branch_restore_control_decision_contract=build_conversation_control_decision_contract(
				request_id="supersede-owner-3",
				decision_class="prior_branch_restore",
				decision_action="replay_as_fresh_governed_query",
				target_state_class="prior_branch_restore",
			),
			frontdoor_contract=types.SimpleNamespace(intent_class="route_onward"),
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "prior_branch_restore_decision")
		self.assertEqual(str(selected.get("basis") or "").strip(), "prior_branch_override")

	def test_select_active_sequence_superseding_owner_returns_substantive_new_request_when_no_stronger_owner_exists(self):
		active_payload = build_compound_request_assessment_contract(
			request_id="supersede-owner-active-4",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()
		selected = _select_active_sequence_superseding_owner(
			raw_message='do u have customer name similar to "Nay Lin Mobile"?',
			latest_active_sequence_payload=active_payload,
			current_active_sequence_payload={},
			control_evidence_payload=None,
			conversation_control_decision_contract=None,
			prior_branch_restore_control_decision_contract=None,
			frontdoor_contract=types.SimpleNamespace(intent_class="route_onward"),
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "frontdoor_intent")
		self.assertEqual(str(selected.get("basis") or "").strip(), "substantive_new_request")

	def test_complete_compound_request_assessment_payload_marks_sequence_inactive(self):
		payload = build_compound_request_assessment_contract(
			request_id="compound-complete-1",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"primary_segment_label": "Supplier list",
				"primary_segment_payload": {"segment_message": "give me some supplier list"},
				"remaining_segment_messages": [],
				"remaining_segment_labels": [],
				"remaining_segment_payloads": [],
			},
		).to_payload()

		completed_payload = _complete_compound_request_assessment_payload(payload)

		self.assertEqual(str(completed_payload.get("status") or "").strip(), "ordered_execution_complete")
		self.assertFalse(bool(completed_payload.get("internal_details", {}).get("primary_segment_message")))
		self.assertEqual(
			str(completed_payload.get("internal_details", {}).get("last_completed_segment_message") or "").strip(),
			"give me some supplier list",
		)
		multi_step_assessment = (completed_payload.get("internal_details", {}).get("multi_step_assessment") or {})
		self.assertEqual(multi_step_assessment.get("status"), "ordered_execution_complete")
		self.assertEqual(multi_step_assessment.get("current_step_id"), "")
		self.assertEqual(multi_step_assessment.get("completed_step_ids"), ["step_1", "step_2"])
		multi_step_execution_plan = (completed_payload.get("internal_details", {}).get("multi_step_execution_plan") or {})
		self.assertEqual(multi_step_execution_plan.get("type"), "qwen_multi_step_execution_plan_contract")
		self.assertEqual(multi_step_execution_plan.get("entry_step_id"), "step_1")
		self.assertEqual(
			(multi_step_execution_plan.get("clarification_policy") or {}).get("policy_id"),
			"step_local_clarification_blocks_later_steps",
		)
		multi_step_execution_state = (completed_payload.get("internal_details", {}).get("multi_step_execution_state") or {})
		self.assertEqual(multi_step_execution_state.get("type"), "qwen_multi_step_execution_state_contract")
		self.assertEqual(multi_step_execution_state.get("state"), "completed")
		self.assertEqual(multi_step_execution_state.get("last_completed_step_id"), "step_2")

	def test_cancel_compound_request_assessment_payload_marks_bridge_cancelled(self):
		payload = build_compound_request_assessment_contract(
			request_id="compound-cancel-1",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "show me payment entries",
				"primary_segment_label": "Payment entries",
				"primary_segment_payload": {"segment_message": "show me payment entries"},
				"remaining_segment_messages": ["give me some supplier list"],
				"remaining_segment_labels": ["Supplier list"],
				"remaining_segment_payloads": [{"segment_message": "give me some supplier list"}],
			},
		).to_payload()

		cancelled_payload = _cancel_compound_request_assessment_payload(payload)

		self.assertEqual(str(cancelled_payload.get("status") or "").strip(), "ordered_execution_cancelled")
		self.assertTrue(bool(cancelled_payload.get("internal_details", {}).get("cancelled")))
		multi_step_assessment = (cancelled_payload.get("internal_details", {}).get("multi_step_assessment") or {})
		self.assertEqual(multi_step_assessment.get("status"), "ordered_execution_cancelled")
		self.assertEqual(multi_step_assessment.get("current_step_id"), "")
		multi_step_execution_plan = (cancelled_payload.get("internal_details", {}).get("multi_step_execution_plan") or {})
		self.assertEqual(multi_step_execution_plan.get("type"), "qwen_multi_step_execution_plan_contract")
		self.assertEqual(
			(multi_step_execution_plan.get("interruption_policy") or {}).get("allow_user_cancel"),
			True,
		)
		multi_step_execution_state = (cancelled_payload.get("internal_details", {}).get("multi_step_execution_state") or {})
		self.assertEqual(multi_step_execution_state.get("type"), "qwen_multi_step_execution_state_contract")
		self.assertEqual(multi_step_execution_state.get("state"), "cancelled")
		self.assertEqual(multi_step_execution_state.get("current_step_id"), "")

	def test_active_sequence_should_complete_after_resume_restore_when_no_segments_remain(self):
		active_payload = build_compound_request_assessment_contract(
			request_id="compound-complete-2",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()
		prior_branch_restore_contract = build_conversation_control_decision_contract(
			request_id="compound-complete-2",
			decision_class="prior_branch_restore",
			decision_action="resume_active_sequence",
			target_state_class="prior_branch_restore",
		)

		should_complete = _active_sequence_should_complete_after_current_turn(
			active_sequence_payload=active_payload,
			conversation_control_decision_contract=None,
			prior_branch_restore_control_decision_contract=prior_branch_restore_contract,
		)

		self.assertTrue(should_complete)

	def test_select_active_sequence_completion_owner_prefers_current_control_resume(self):
		decision_contract = build_conversation_control_decision_contract(
			request_id="compound-complete-owner-1",
			decision_class="sequence_continuation",
			decision_action="resume_active_sequence",
			target_state_class="active_sequence",
		)
		prior_branch_restore_contract = build_conversation_control_decision_contract(
			request_id="compound-complete-owner-2",
			decision_class="prior_branch_restore",
			decision_action="resume_active_sequence",
			target_state_class="prior_branch_restore",
		)

		selected = _select_active_sequence_completion_owner(
			conversation_control_decision_contract=decision_contract,
			prior_branch_restore_control_decision_contract=prior_branch_restore_contract,
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "conversation_control_decision")
		self.assertEqual(str(selected.get("basis") or "").strip(), "current_control_resume_active_sequence")

	def test_select_active_sequence_completion_owner_uses_prior_branch_resume_when_current_resume_is_absent(self):
		prior_branch_restore_contract = build_conversation_control_decision_contract(
			request_id="compound-complete-owner-3",
			decision_class="prior_branch_restore",
			decision_action="resume_active_sequence",
			target_state_class="prior_branch_restore",
		)

		selected = _select_active_sequence_completion_owner(
			conversation_control_decision_contract=None,
			prior_branch_restore_control_decision_contract=prior_branch_restore_contract,
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "prior_branch_restore_decision")
		self.assertEqual(str(selected.get("basis") or "").strip(), "prior_branch_resume_active_sequence")

	def test_active_sequence_completion_source_falls_back_to_latest_active_sequence(self):
		latest_payload = build_compound_request_assessment_contract(
			request_id="compound-complete-source",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			suggested_options=["Payment entries", "Supplier list"],
			clarification_required=False,
			reason="Ordered compound request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()

		resolved_payload = _active_sequence_completion_source_payload(
			current_active_sequence_payload={},
			latest_active_sequence_payload=latest_payload,
		)

		self.assertEqual(
			str(resolved_payload.get("request_id") or "").strip(),
			"compound-complete-source",
		)

	def test_select_compound_execution_runtime_source_prefers_current_frontdoor_payload(self):
		current_payload = build_compound_request_assessment_contract(
			request_id="compound-runtime-source-current",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered compound request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()
		latest_payload = build_compound_request_assessment_contract(
			request_id="compound-runtime-source-latest",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some customer list"],
			clarification_required=False,
			reason="Ordered compound request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some customer list",
				"remaining_segment_messages": [],
			},
		).to_payload()

		selected = _select_compound_execution_runtime_source(
			"continue",
			current_compound_assessment_payload=current_payload,
			latest_compound_assessment_payload=latest_payload,
			control_evidence_payload=None,
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "current_compound_assessment")
		self.assertEqual(str(selected.get("basis") or "").strip(), "current_frontdoor_active_sequence")

	def test_select_compound_execution_runtime_source_uses_latest_active_sequence_for_continuation(self):
		latest_payload = build_compound_request_assessment_contract(
			request_id="compound-runtime-source-latest-only",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered compound request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()

		selected = _select_compound_execution_runtime_source(
			"continue",
			current_compound_assessment_payload={},
			latest_compound_assessment_payload=latest_payload,
			control_evidence_payload=None,
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "latest_compound_assessment")
		self.assertEqual(str(selected.get("basis") or "").strip(), "latest_active_sequence_continuation")

	def test_resolve_compound_execution_runtime_message_prefers_current_frontdoor_payload(self):
		current_payload = build_compound_request_assessment_contract(
			request_id="compound-runtime-message-current",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered compound request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()
		latest_payload = build_compound_request_assessment_contract(
			request_id="compound-runtime-message-latest",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some customer list"],
			clarification_required=False,
			reason="Ordered compound request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some customer list",
				"remaining_segment_messages": [],
			},
		).to_payload()

		runtime_message, active_sequence_payload = _resolve_compound_execution_runtime_message(
			raw_message="continue",
			frontdoor_contract=types.SimpleNamespace(
				response_payload={"compound_request_assessment": current_payload}
			),
			latest_compound_assessment_payload=latest_payload,
			control_evidence_payload=None,
		)

		self.assertEqual(str(runtime_message or "").strip(), "give me some supplier list")
		self.assertEqual(str(active_sequence_payload.get("request_id") or "").strip(), "compound-runtime-message-current")

	def test_select_active_sequence_completion_source_owner_prefers_current_active_sequence(self):
		current_payload = build_compound_request_assessment_contract(
			request_id="compound-complete-source-current",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()
		latest_payload = build_compound_request_assessment_contract(
			request_id="compound-complete-source-latest",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some customer list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some customer list",
				"remaining_segment_messages": [],
			},
		).to_payload()

		selected = _select_active_sequence_completion_source_owner(
			current_active_sequence_payload=current_payload,
			latest_active_sequence_payload=latest_payload,
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "current_active_sequence")
		self.assertEqual(str(selected.get("basis") or "").strip(), "current_active_sequence_available")

	def test_select_active_sequence_completion_source_owner_falls_back_to_latest_active_sequence(self):
		latest_payload = build_compound_request_assessment_contract(
			request_id="compound-complete-source-fallback",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Ordered multi-step request.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()

		selected = _select_active_sequence_completion_source_owner(
			current_active_sequence_payload={},
			latest_active_sequence_payload=latest_payload,
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "latest_active_sequence")
		self.assertEqual(str(selected.get("basis") or "").strip(), "latest_active_sequence_fallback")

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
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"generic_branch_restore_uses_resumable_prior_request",
		)

	def test_build_direct_restore_fallback_contract_records_branch_restore_resumable_basis(self):
		contract = _build_direct_restore_fallback_contract(
			request_id="restore-fallback-prior-1",
			phrase_type="branch_restore",
			active_sequence={"active": False},
			resumable_prior_request={
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"source_request_id": "grounded-prior-trace-fallback-1",
				"target_family": "customer_rankings",
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "accepted_repair_with_newer_grounded_turn",
				"confidence": 0.79,
			},
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "replay_as_fresh_governed_query")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"generic_branch_restore_uses_resumable_prior_request",
		)

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

	def test_generic_branch_restore_does_not_reopen_non_authoritative_pending_clarification_without_other_owner(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"source_kind": "message_fallback",
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-restore-fallback-direct-2",
					"user_question": "Which item do you mean?",
				},
				"source_tool_index": -1,
			},
			"active_sequence": {"active": False},
			"recent_focus": {"available": False, "source_tool_index": -1},
			"resumable_prior_request": {"available": False, "source_tool_index": -1},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-turn-fallback-direct-2",
			raw_message="go back",
			conversation_state_snapshot=snapshot,
		)

		self.assertIsNone(contract)

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
				"focus_label": "Ko Nay Lin Mobile Center",
				"source_capability": "customer_detail_read",
				"source_report": "Customer Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
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
		self.assertEqual(
			str(((payload.get("resolved_focus_target") or {}).get("source_capability")) or "").strip(),
			"customer_detail_read",
		)
		self.assertTrue(bool((payload.get("resolved_focus_target") or {}).get("deictic_allowed")))
		self.assertTrue(bool((payload.get("resolved_focus_target") or {}).get("explicit_named_allowed")))
		self.assertEqual(
			str((((payload.get("internal_details") or {}).get("recent_focus_affordance") or {}).get("type")) or "").strip(),
			"qwen_recent_focus_affordance_contract",
		)

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

	def test_prior_branch_restore_runtime_message_uses_document_shape(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-2b",
			target_branch_kind="focus",
			target_branch_label="PUR-ORD-2026-00004",
			target_request_id="grounded-purchase-order-restore-1",
			target_family="entity_detail",
			target_scope={
				"focus_kind": "document",
				"focus_grain": "purchase_order",
				"focus_key": "PUR-ORD-2026-00004",
				"source_report": "Purchase Order Detail",
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent purchase order focus.",
			confidence=0.9,
		)

		self.assertEqual(
			_prior_branch_restore_runtime_message(restore_contract),
			"show me details for purchase order PUR-ORD-2026-00004",
		)

	def test_prior_branch_restore_runtime_message_uses_master_data_listing_shape(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-2c",
			target_branch_kind="focus",
			target_branch_label="Supplier Master List",
			target_request_id="grounded-supplier-list-restore-1",
			target_family="master_data_directory",
			target_scope={
				"focus_kind": "listing",
				"focus_grain": "supplier",
				"focus_key": "supplier",
				"source_report": "Supplier Master List",
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent supplier listing.",
			confidence=0.88,
		)

		self.assertEqual(
			_prior_branch_restore_runtime_message(restore_contract),
			"show me suppliers",
		)

	def test_prior_branch_restore_runtime_message_uses_transaction_listing_shape(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-2d",
			target_branch_kind="focus",
			target_branch_label="Payment Entry List",
			target_request_id="grounded-payment-entry-list-restore-1",
			target_family="transaction_listing",
			target_scope={
				"focus_kind": "listing",
				"focus_grain": "payment_entry",
				"focus_key": "payment_entry",
				"source_report": "Payment Entry List",
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent payment entry listing.",
			confidence=0.88,
		)

		self.assertEqual(
			_prior_branch_restore_runtime_message(restore_contract),
			"show me payment entries",
		)

	def test_prior_branch_restore_runtime_message_uses_transaction_document_shape(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-2e",
			target_branch_kind="focus",
			target_branch_label="ACC-PAY-2026-00179",
			target_request_id="grounded-payment-entry-document-1",
			target_family="transaction_listing",
			target_scope={
				"focus_kind": "document",
				"focus_grain": "payment_entry",
				"focus_key": "ACC-PAY-2026-00179",
				"source_report": "Payment Entry List",
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent payment entry document focus.",
			confidence=0.88,
		)

		self.assertEqual(
			_prior_branch_restore_runtime_message(restore_contract),
			"show me details for payment entry ACC-PAY-2026-00179",
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

	def test_select_prior_branch_restore_projection_uses_sequence_label_override(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-3b",
			target_branch_kind="sequence",
			target_branch_label="give me some supplier list",
			target_request_id="compound-restore-1b",
			target_family="active_sequence",
			target_scope={},
			restore_mode="resume_active_sequence",
			resumable=True,
			reason="The user asked to continue the remaining sequence.",
			confidence=0.91,
		)

		selected = _select_prior_branch_restore_projection(restore_contract)

		self.assertEqual(str(selected.get("runtime_override_message") or "").strip(), "give me some supplier list")
		self.assertEqual(str(selected.get("basis") or "").strip(), "resume_active_sequence_target_label")
		self.assertEqual(dict(selected.get("resolved_focus_target") or {}), {})

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

	def test_recent_focus_state_from_prior_branch_restore_contract_restores_focus_fields(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-4a",
			target_branch_kind="focus",
			target_branch_label="Ko Nay Lin Mobile Center",
			target_request_id="grounded-customer-restore-3a",
			target_family="entity_detail",
			target_scope={
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_key": "Ko Nay Lin Mobile Center",
				"focus_label": "Ko Nay Lin Mobile Center",
				"source_report": "Customer Detail",
				"source_capability": "customer_sales_detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent customer focus.",
			confidence=0.93,
		)

		recent_focus_state = _recent_focus_state_from_prior_branch_restore_contract(restore_contract)

		self.assertEqual(str(recent_focus_state.get("focus_kind") or "").strip(), "entity")
		self.assertEqual(str(recent_focus_state.get("focus_grain") or "").strip(), "customer")
		self.assertEqual(str(recent_focus_state.get("focus_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(str(recent_focus_state.get("source_report") or "").strip(), "Customer Detail")
		self.assertTrue(bool(recent_focus_state.get("deictic_allowed")))
		self.assertTrue(bool(recent_focus_state.get("explicit_named_allowed")))

	def test_prior_branch_restore_recent_focus_affordance_contract_rebuilds_shared_affordance(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-4aa",
			target_branch_kind="focus",
			target_branch_label="Ko Nay Lin Mobile Center",
			target_request_id="grounded-customer-restore-3aa",
			target_family="entity_detail",
			target_scope={
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_key": "Ko Nay Lin Mobile Center",
				"focus_label": "Ko Nay Lin Mobile Center",
				"source_report": "Customer Detail",
				"source_capability": "customer_sales_detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent customer focus.",
			confidence=0.93,
		)

		affordance_contract = _prior_branch_restore_recent_focus_affordance_contract(
			request_id="prior-restore-runtime-4aa",
			prior_branch_restore_contract=restore_contract,
		)
		payload = affordance_contract.to_payload()

		self.assertEqual(str(payload.get("focus_kind") or "").strip(), "entity")
		self.assertEqual(str(payload.get("focus_grain") or "").strip(), "customer")
		self.assertIn("detail_followup", list(payload.get("allowed_action_classes") or []))
		self.assertIn("commercial_status_followup", list(payload.get("allowed_action_classes") or []))
		self.assertIn("lifecycle_basis_followup", list(payload.get("allowed_action_classes") or []))
		self.assertTrue(bool(payload.get("deictic_reference_allowed")))

	def test_build_prior_branch_restore_recent_focus_projection_uses_shared_recent_focus_surface(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-4ab",
			target_branch_kind="focus",
			target_branch_label="Ko Nay Lin Mobile Center",
			target_request_id="grounded-customer-restore-3ab",
			target_family="entity_detail",
			target_scope={
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_key": "Ko Nay Lin Mobile Center",
				"focus_label": "Ko Nay Lin Mobile Center",
				"source_report": "Customer Detail",
				"source_capability": "customer_sales_detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent customer focus.",
			confidence=0.93,
		)

		projection = recent_focus_support_module.build_prior_branch_restore_recent_focus_projection(
			request_id="prior-restore-runtime-4ab",
			prior_branch_restore_contract=restore_contract,
		)

		self.assertEqual(
			str((projection.get("runtime_override_message") or "").strip()),
			"tell me more about Ko Nay Lin Mobile Center",
		)
		self.assertEqual(
			str(((projection.get("resolved_focus_target") or {}).get("focus_grain")) or "").strip(),
			"customer",
		)
		self.assertTrue(bool((projection.get("resolved_focus_target") or {}).get("listing_supported")))
		self.assertTrue(bool((projection.get("resolved_focus_target") or {}).get("detail_supported")))
		self.assertEqual(
			str(((projection.get("resolved_focus_target") or {}).get("listing_detail_support_status") or "").strip()),
			"both",
		)
		self.assertEqual(
			str((((projection.get("recent_focus_affordance_payload") or {}).get("type")) or "").strip()),
			"qwen_recent_focus_affordance_contract",
		)
		self.assertEqual(
			str(((projection.get("restored_recent_focus_state") or {}).get("focus_label")) or "").strip(),
			"Ko Nay Lin Mobile Center",
		)
		self.assertTrue(bool((projection.get("restored_recent_focus_state") or {}).get("listing_supported")))
		self.assertTrue(bool((projection.get("restored_recent_focus_state") or {}).get("detail_supported")))
		self.assertEqual(
			str(((projection.get("restored_recent_focus_state") or {}).get("listing_detail_support_status") or "").strip()),
			"both",
		)

	def test_build_latest_non_clarification_restore_owner_spec_for_recent_focus(self):
		spec = restore_support_module.build_latest_non_clarification_restore_owner_spec(
			owner="recent_focus",
			phrase_type="question_restore",
			pending_available=True,
			owner_is_newer_than_pending=True,
			arbitration_basis="recent_focus_precedes_pending",
			pending_clarification_source_tool_index=10,
			recent_focus_source_tool_index=12,
			resumable_prior_request_source_tool_index=8,
			recent_focus_derivation_basis="master_data_single_row_grounded_turn",
		)

		self.assertEqual(str(spec.get("owner") or "").strip(), "recent_focus")
		self.assertEqual(
			str(spec.get("reason") or "").strip(),
			"The user asked to answer the most recent question, and the latest grounded business focus is newer than the older pending clarification.",
		)
		self.assertEqual(
			str(((spec.get("internal_details") or {}).get("arbitration_basis") or "").strip()),
			"recent_focus_precedes_pending",
		)
		self.assertEqual(
			str(((spec.get("internal_details") or {}).get("derivation_basis") or "").strip()),
			"master_data_single_row_grounded_turn",
		)

	def test_build_latest_non_clarification_restore_owner_spec_for_resumable_prior_request(self):
		spec = restore_support_module.build_latest_non_clarification_restore_owner_spec(
			owner="resumable_prior_request",
			phrase_type="branch_restore",
			pending_available=True,
			owner_is_newer_than_pending=False,
			arbitration_basis="resumable_prior_request_precedes_pending",
			pending_clarification_source_tool_index=10,
			recent_focus_source_tool_index=12,
			resumable_prior_request_source_tool_index=14,
			resumable_snapshot_restore_mode="replay_as_fresh_governed_query",
			resumable_derivation_basis="accepted_recovery_origin",
			resumable_accepted_recovery_action="run_alternative_governed_query",
			resumable_prior_recovery_payload={"report_name": "Customer Ranking"},
		)

		self.assertEqual(str(spec.get("owner") or "").strip(), "resumable_prior_request")
		self.assertEqual(
			str(spec.get("reason") or "").strip(),
			"The user asked to go back, so the assistant is restoring the latest resumable prior branch instead of reopening a non-authoritative fallback clarification.",
		)
		self.assertEqual(
			str(((spec.get("internal_details") or {}).get("snapshot_restore_mode") or "").strip()),
			"replay_as_fresh_governed_query",
		)
		self.assertEqual(
			str((((spec.get("internal_details") or {}).get("prior_recovery_payload") or {}).get("report_name")) or "").strip(),
			"Customer Ranking",
		)

	def test_build_direct_restore_fallback_owner_spec_for_active_sequence(self):
		spec = restore_support_module.build_direct_restore_fallback_owner_spec(
			owner="active_sequence",
			reason="The assistant is resuming the active sequence.",
			arbitration_basis="direct_active_sequence_fallback",
			internal_details={"ignored": True},
		)

		self.assertEqual(str(spec.get("owner") or "").strip(), "active_sequence")
		self.assertEqual(
			str(spec.get("reason") or "").strip(),
			"The assistant is resuming the active sequence.",
		)
		self.assertEqual(
			str(spec.get("arbitration_basis") or "").strip(),
			"direct_active_sequence_fallback",
		)
		self.assertFalse("internal_details" in spec)

	def test_build_direct_restore_fallback_owner_spec_for_resumable_prior_request(self):
		spec = restore_support_module.build_direct_restore_fallback_owner_spec(
			owner="resumable_prior_request",
			reason="The assistant is restoring the resumable prior branch.",
			internal_details={"snapshot_restore_mode": "replay_as_fresh_governed_query"},
		)

		self.assertEqual(str(spec.get("owner") or "").strip(), "resumable_prior_request")
		self.assertEqual(
			str(spec.get("reason") or "").strip(),
			"The assistant is restoring the resumable prior branch.",
		)
		self.assertEqual(
			str(((spec.get("internal_details") or {}).get("snapshot_restore_mode") or "").strip()),
			"replay_as_fresh_governed_query",
		)

	def test_build_prior_branch_restore_snapshot_context_normalizes_interpretation_and_state_buckets(self):
		context = restore_support_module.build_prior_branch_restore_snapshot_context(
			conversation_state_snapshot={
				"pending_clarification": {"available": True, "source_tool_index": 4},
				"active_sequence": ["not", "a", "dict"],
				"recent_focus": {"available": True, "focus_label": "Ko Nay Lin Mobile Center"},
				"resumable_prior_request": None,
			},
			interpretation={
				"phrase_type": " branch_restore ",
				"target_hint": " customer ",
				"target_grain": " customer ",
				"target_focus_kind": " detail ",
			},
		)

		self.assertEqual(str(context.get("phrase_type") or "").strip(), "branch_restore")
		self.assertEqual(str(context.get("target_hint") or "").strip(), "customer")
		self.assertEqual(str(context.get("target_grain") or "").strip(), "customer")
		self.assertEqual(str(context.get("target_focus_kind") or "").strip(), "detail")
		self.assertTrue(bool((context.get("pending_clarification") or {}).get("available")))
		self.assertEqual(context.get("active_sequence"), {})
		self.assertEqual(
			str(((context.get("recent_focus") or {}).get("focus_label") or "").strip()),
			"Ko Nay Lin Mobile Center",
		)
		self.assertEqual(context.get("resumable_prior_request"), {})

	def test_select_latest_non_clarification_restore_state_prefers_known_recent_focus_over_unindexed_resumable_shared_helper(self):
		selected = restore_support_module.select_latest_non_clarification_restore_state(
			phrase_type="branch_restore",
			pending_clarification={},
			active_sequence={},
			recent_focus={"available": True, "source_tool_index": 12},
			resumable_prior_request={"available": True, "source_tool_index": -1},
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "recent_focus")
		self.assertEqual(
			str(selected.get("basis") or "").strip(),
			"generic_branch_restore_prefers_known_recent_focus_over_unindexed_resumable_prior_request",
		)

	def test_build_prior_branch_restore_route_context_builds_selector_inputs_from_candidate_discovery(self):
		context = restore_support_module.build_prior_branch_restore_route_context(
			phrase_type="branch_restore",
			pending_clarification={"available": False},
			active_sequence={"active": False},
			recent_focus={"available": True, "source_tool_index": 12},
			resumable_prior_request={"available": True, "source_tool_index": -1},
			has_target_specifier=True,
			recent_focus_matches_targeted_restore=True,
			resumable_prior_request_matches_targeted_restore=False,
		)

		self.assertEqual(
			str((((context.get("targeted_restore_selection") or {}).get("owner")) or "").strip()),
			"recent_focus",
		)
		self.assertEqual(
			str((((context.get("latest_non_clarification_selection") or {}).get("owner")) or "").strip()),
			"recent_focus",
		)
		self.assertEqual(
			str((((context.get("route_selector_inputs") or {}).get("targeted_restore_owner")) or "").strip()),
			"recent_focus",
		)
		self.assertEqual(
			str((((context.get("route_selector_inputs") or {}).get("latest_non_clarification_owner")) or "").strip()),
			"recent_focus",
		)
		self.assertTrue(bool((context.get("route_selector_inputs") or {}).get("has_target_specifier")))

	def test_build_prior_branch_restore_route_selector_inputs_normalizes_selection_state(self):
		inputs = restore_support_module.build_prior_branch_restore_route_selector_inputs(
			phrase_type="branch_restore",
			targeted_restore_selection={"owner": "recent_focus", "basis": "targeted_recent_focus_restore"},
			latest_non_clarification_selection={"owner": "active_sequence", "basis": "question_restore_uses_active_sequence"},
			has_target_specifier=True,
			pending_clarification_is_authoritative=False,
			has_active_sequence=True,
			has_resumable_prior_request=True,
		)

		self.assertEqual(str(inputs.get("phrase_type") or "").strip(), "branch_restore")
		self.assertEqual(str(inputs.get("targeted_restore_owner") or "").strip(), "recent_focus")
		self.assertEqual(str(inputs.get("targeted_restore_basis") or "").strip(), "targeted_recent_focus_restore")
		self.assertEqual(str(inputs.get("latest_non_clarification_owner") or "").strip(), "active_sequence")
		self.assertTrue(bool(inputs.get("has_target_specifier")))
		self.assertTrue(bool(inputs.get("has_active_sequence")))
		self.assertTrue(bool(inputs.get("has_resumable_prior_request")))

	def test_build_targeted_restore_owner_spec_for_recent_focus(self):
		spec = restore_support_module.build_targeted_restore_owner_spec(
			restore_route="targeted_recent_focus",
			phrase_type="branch_restore",
			target_hint="customer",
			target_grain="customer",
			target_focus_kind="listing",
			restore_basis="targeted_recent_focus_restore",
			clear_pending_clarification=True,
			recent_focus_derivation_basis="master_data_single_row_grounded_turn",
		)

		self.assertEqual(str(spec.get("owner") or "").strip(), "recent_focus")
		self.assertEqual(
			str(spec.get("reason") or "").strip(),
			"The user asked to return to the recent business focus that matches the requested branch.",
		)
		self.assertTrue(bool(spec.get("clear_current_pending_clarification")))
		self.assertEqual(
			str(((spec.get("internal_details") or {}).get("derivation_basis") or "").strip()),
			"master_data_single_row_grounded_turn",
		)

	def test_build_targeted_restore_owner_spec_for_resumable_prior_request(self):
		spec = restore_support_module.build_targeted_restore_owner_spec(
			restore_route="targeted_resumable_prior_request",
			phrase_type="branch_restore",
			target_hint="top customer",
			target_grain="customer",
			target_focus_kind="listing",
			restore_basis="targeted_resumable_prior_branch_restore",
			clear_pending_clarification=True,
			resumable_suggested_restore_mode="replay_as_fresh_governed_query",
			resumable_derivation_basis="accepted_recovery_origin",
			resumable_accepted_recovery_action="run_alternative_governed_query",
			resumable_prior_recovery_payload={"report_name": "Top Customers by Revenue"},
		)

		self.assertEqual(str(spec.get("owner") or "").strip(), "resumable_prior_request")
		self.assertEqual(
			str(spec.get("reason") or "").strip(),
			"The user asked to return to a prior branch that matches the requested business target.",
		)
		self.assertTrue(bool(spec.get("clear_current_pending_clarification")))
		self.assertEqual(
			str(((spec.get("internal_details") or {}).get("snapshot_restore_mode") or "").strip()),
			"replay_as_fresh_governed_query",
		)
		self.assertEqual(
			str((((spec.get("internal_details") or {}).get("prior_recovery_payload") or {}).get("report_name")) or "").strip(),
			"Top Customers by Revenue",
		)

	def test_select_prior_branch_restore_projection_enriches_recent_focus_target_and_affordance(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-4b",
			target_branch_kind="focus",
			target_branch_label="Ko Nay Lin Mobile Center",
			target_request_id="grounded-customer-restore-3b",
			target_family="entity_detail",
			target_scope={
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_report": "Customer Detail",
				"source_capability": "customer_sales_detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent customer focus.",
			confidence=0.93,
		)

		selected = _select_prior_branch_restore_projection(restore_contract)

		self.assertEqual(str(selected.get("runtime_override_message") or "").strip(), "tell me more about Ko Nay Lin Mobile Center")
		self.assertEqual(str(selected.get("basis") or "").strip(), "restore_recent_focus_projection")
		self.assertEqual(
			str(((selected.get("resolved_focus_target") or {}).get("focus_grain")) or "").strip(),
			"customer",
		)
		self.assertEqual(
			str((((selected.get("internal_details") or {}).get("recent_focus_affordance") or {}).get("type")) or "").strip(),
			"qwen_recent_focus_affordance_contract",
		)
		self.assertTrue(bool((selected.get("resolved_focus_target") or {}).get("listing_supported")))
		self.assertTrue(bool((selected.get("resolved_focus_target") or {}).get("detail_supported")))
		self.assertEqual(
			str(((selected.get("resolved_focus_target") or {}).get("listing_detail_support_status") or "").strip()),
			"both",
		)

	def test_build_prior_branch_restore_recent_focus_projection_preserves_listing_only_parity(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-4bb",
			target_branch_kind="focus",
			target_branch_label="Payment Entry List",
			target_request_id="grounded-payment-entry-restore-4bb",
			target_family="transaction_listing",
			target_scope={
				"focus_kind": "listing",
				"focus_grain": "payment_entry",
				"focus_key": "payment_entry",
				"focus_label": "Payment Entry List",
				"source_report": "Payment Entry List",
				"source_capability": "payment_entry_read",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
			restore_mode="restore_recent_focus",
			resumable=True,
			reason="The user asked to return to the recent payment entry listing.",
			confidence=0.91,
		)

		projection = recent_focus_support_module.build_prior_branch_restore_recent_focus_projection(
			request_id="prior-restore-runtime-4bb",
			prior_branch_restore_contract=restore_contract,
		)

		self.assertTrue(bool((projection.get("restored_recent_focus_state") or {}).get("listing_supported")))
		self.assertFalse(bool((projection.get("restored_recent_focus_state") or {}).get("detail_supported")))
		self.assertEqual(
			str(((projection.get("restored_recent_focus_state") or {}).get("listing_detail_support_status") or "").strip()),
			"listing_only",
		)
		self.assertTrue(bool((projection.get("resolved_focus_target") or {}).get("listing_supported")))
		self.assertFalse(bool((projection.get("resolved_focus_target") or {}).get("detail_supported")))
		self.assertEqual(
			str(((projection.get("resolved_focus_target") or {}).get("listing_detail_support_status") or "").strip()),
			"listing_only",
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

	def test_select_prior_branch_restore_direct_handler_route_prefers_reopen_when_signal_exists(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-5b",
			target_branch_kind="clarification",
			target_branch_label="Which financial view would you like to see?",
			target_request_id="clarify-runtime-1b",
			target_family="clarification",
			target_scope={},
			restore_mode="reopen_pending_clarification",
			resumable=True,
			reason="The user asked to reopen the pending clarification.",
			confidence=0.95,
		)

		selected = _select_prior_branch_restore_direct_handler_route(
			restore_contract,
			pending_clarification_signal=_clarification_signal(
				request_id="clarify-runtime-route-1",
				user_question="Which financial view would you like to see?",
			),
		)

		self.assertEqual(str(selected.get("route") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(str(selected.get("basis") or "").strip(), "restore_mode_reopen_pending_clarification")

	def test_select_prior_branch_restore_direct_handler_route_blocks_reopen_without_signal(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-5c",
			target_branch_kind="clarification",
			target_branch_label="Which financial view would you like to see?",
			target_request_id="clarify-runtime-1c",
			target_family="clarification",
			target_scope={},
			restore_mode="reopen_pending_clarification",
			resumable=True,
			reason="The user asked to reopen the pending clarification.",
			confidence=0.95,
		)

		selected = _select_prior_branch_restore_direct_handler_route(
			restore_contract,
			pending_clarification_signal={},
		)

		self.assertEqual(str(selected.get("route") or "").strip(), "")
		self.assertEqual(str(selected.get("basis") or "").strip(), "missing_pending_clarification_signal")

	def test_select_prior_branch_restore_direct_handler_route_uses_replay_route(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-5d",
			target_branch_kind="accepted_recovery_origin",
			target_branch_label="Top Customers by Revenue",
			target_request_id="grounded-prior-turn-route-1",
			target_family="ranked_entity_analytics",
			target_scope={"requested_top_n": 10},
			restore_mode="replay_as_fresh_governed_query",
			resumable=True,
			reason="The user chose to replay a prior governed branch.",
			confidence=0.94,
		)

		selected = _select_prior_branch_restore_direct_handler_route(
			restore_contract,
			pending_clarification_signal={},
		)

		self.assertEqual(str(selected.get("route") or "").strip(), "replay_as_fresh_governed_query")
		self.assertEqual(str(selected.get("basis") or "").strip(), "restore_mode_replay_as_fresh_governed_query")

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
				for key, value in self._payload.items():
					setattr(self, key, value)

			def to_payload(self):
				return dict(self._payload)

		with patch("ai_assistant_ui.qwen_chat.service._append_message"), patch(
			"ai_assistant_ui.qwen_chat.service._append_tool_payload"
		) as append_tool_payload_mock, patch(
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

	def test_handle_prior_branch_restore_direct_route_dispatches_reopen_handler(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-6b",
			target_branch_kind="clarification",
			target_branch_label="Which financial view would you like to see?",
			target_request_id="clarify-runtime-2b",
			target_family="clarification",
			target_scope={},
			restore_mode="reopen_pending_clarification",
			resumable=True,
			reason="The user asked to reopen the pending clarification.",
			confidence=0.95,
		)

		with patch(
			"ai_assistant_ui.qwen_chat.service._handle_prior_branch_restore_reopen_pending_clarification",
			return_value=(True, {"mode": "clarification"}),
		) as reopen_mock, patch(
			"ai_assistant_ui.qwen_chat.service._handle_prior_branch_restore_fresh_query",
			return_value=(False, None),
		) as replay_mock:
			handled, payload = _handle_prior_branch_restore_direct_route(
				session_doc=object(),
				request_id="prior-restore-runtime-6b",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				raw_message="answer the last question",
				interaction_contract=object(),
				conversation_control_evidence_contract=None,
				frontdoor_semantic_result=None,
				frontdoor_contract=None,
				clarification_response_contract=None,
				response_policy_contract=None,
				prior_branch_restore_contract=restore_contract,
				prior_branch_restore_control_decision_contract=None,
				pending_clarification_signal=_clarification_signal(
					request_id="clarify-runtime-direct-1",
					user_question="Which financial view would you like to see?",
				),
				additional_tool_payloads=[],
			)

		self.assertTrue(handled)
		self.assertEqual(payload, {"mode": "clarification"})
		self.assertEqual(reopen_mock.call_count, 1)
		self.assertEqual(replay_mock.call_count, 0)

	def test_handle_prior_branch_restore_direct_route_dispatches_replay_handler(self):
		restore_contract = build_prior_branch_restore_contract(
			request_id="prior-restore-runtime-6c",
			target_branch_kind="accepted_recovery_origin",
			target_branch_label="Top Customers by Revenue",
			target_request_id="grounded-prior-turn-route-2",
			target_family="ranked_entity_analytics",
			target_scope={"requested_top_n": 10},
			restore_mode="replay_as_fresh_governed_query",
			resumable=True,
			reason="The user chose to replay a prior governed branch.",
			confidence=0.94,
		)

		with patch(
			"ai_assistant_ui.qwen_chat.service._handle_prior_branch_restore_reopen_pending_clarification",
			return_value=(False, None),
		) as reopen_mock, patch(
			"ai_assistant_ui.qwen_chat.service._handle_prior_branch_restore_fresh_query",
			return_value=(True, {"mode": "front_door"}),
		) as replay_mock:
			handled, payload = _handle_prior_branch_restore_direct_route(
				session_doc=object(),
				request_id="prior-restore-runtime-6c",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				raw_message="go back",
				interaction_contract=object(),
				conversation_control_evidence_contract=None,
				frontdoor_semantic_result=None,
				frontdoor_contract=None,
				clarification_response_contract=None,
				response_policy_contract=object(),
				prior_branch_restore_contract=restore_contract,
				prior_branch_restore_control_decision_contract=None,
				pending_clarification_signal={},
				additional_tool_payloads=[],
			)

		self.assertTrue(handled)
		self.assertEqual(payload, {"mode": "front_door"})
		self.assertEqual(reopen_mock.call_count, 0)
		self.assertEqual(replay_mock.call_count, 1)

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

	def test_strip_leading_control_discard_preamble_supports_soft_chained_remainder(self):
		self.assertEqual(
			_strip_leading_control_discard_preamble("ignore that show me suppliers"),
			"show me suppliers",
		)
		self.assertEqual(
			_strip_leading_control_discard_preamble("forget it answer the last question"),
			"answer the last question",
		)

	def test_shared_control_language_reclassifies_discard_prefix_into_question_restore(self):
		evidence = classify_conversation_control_evidence("forget the first question, answer the last question")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(str(evidence.get("embedded_business_message") or "").strip(), "")
		self.assertTrue(bool((evidence.get("internal_details") or {}).get("discard_prefix_applied")))

	def test_shared_control_language_supports_additional_question_restore_variants(self):
		last_one = classify_conversation_control_evidence("answer the last one")
		previous_one = classify_conversation_control_evidence("repeat the previous one")
		polite_last_question = classify_conversation_control_evidence("answer the last question please")
		repeat_last_request = classify_conversation_control_evidence("repeat the last request please")
		back_to_that_question = classify_conversation_control_evidence("go back to that question")

		self.assertEqual(str(last_one.get("action_id") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(str(previous_one.get("action_id") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(str(polite_last_question.get("action_id") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(str(repeat_last_request.get("action_id") or "").strip(), "reopen_pending_clarification")
		self.assertEqual(str(back_to_that_question.get("action_id") or "").strip(), "reopen_pending_clarification")

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
		next_one_evidence = classify_conversation_control_evidence("go ahead with the next one")
		continue_with_that = classify_conversation_control_evidence("continue with that")
		stop_sequence = classify_conversation_control_evidence("stop this sequence")

		self.assertEqual(str(continue_evidence.get("action_id") or "").strip(), "resume_active_sequence")
		self.assertEqual(str(continue_evidence.get("evidence_class") or "").strip(), "sequence_continuation")
		self.assertEqual(str(stop_evidence.get("action_id") or "").strip(), "stop_active_sequence")
		self.assertEqual(str(stop_evidence.get("evidence_class") or "").strip(), "sequence_stop")
		self.assertEqual(str(next_one_evidence.get("action_id") or "").strip(), "resume_active_sequence")
		self.assertEqual(str(continue_with_that.get("action_id") or "").strip(), "resume_active_sequence")
		self.assertEqual(str(stop_sequence.get("action_id") or "").strip(), "stop_active_sequence")

	def test_shared_control_language_classifies_redirect_with_embedded_business_request(self):
		evidence = classify_conversation_control_evidence("ignore that, show me suppliers")
		self.assertEqual(str(evidence.get("evidence_class") or "").strip(), "fresh_request_redirect")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "override_with_new_request")
		self.assertEqual(str(evidence.get("embedded_business_message") or "").strip(), "show me suppliers")

	def test_shared_control_language_supports_soft_chained_redirect_without_separator(self):
		evidence = classify_conversation_control_evidence("ignore that show me suppliers")
		self.assertEqual(str(evidence.get("evidence_class") or "").strip(), "fresh_request_redirect")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "override_with_new_request")
		self.assertEqual(str(evidence.get("embedded_business_message") or "").strip(), "show me suppliers")
		self.assertTrue(bool((evidence.get("internal_details") or {}).get("discard_prefix_applied")))

	def test_shared_control_language_exposes_control_action_helpers(self):
		evidence = classify_conversation_control_evidence("ignore that, show me suppliers")
		self.assertEqual(control_action_id(evidence), "override_with_new_request")
		self.assertEqual(
			control_action_id_from_message_or_evidence("ignore that, show me suppliers", None),
			"override_with_new_request",
		)
		self.assertEqual(
			control_action_id_from_message_or_evidence("placeholder", evidence),
			"override_with_new_request",
		)
		self.assertTrue(control_action_is_strong_owner(evidence))
		self.assertFalse(control_action_is_strong_owner({"action_id": "weak_signal_only"}))

	def test_shared_control_language_exposes_restore_interpretation_helpers(self):
		evidence = classify_conversation_control_evidence("ignore that, go back to the supplier directory")
		self.assertEqual(prior_branch_phrase_type_from_control_action(evidence), "branch_restore")
		self.assertEqual(
			targeted_restore_hint_from_control_evidence(evidence),
			("supplier directory", "supplier", "listing"),
		)
		self.assertEqual(
			targeted_restore_hint_from_message("go back to the supplier directory"),
			("supplier directory", "supplier", "listing"),
		)
		internal_details = conversation_control_evidence_internal_details(evidence)
		self.assertEqual(
			str(internal_details.get("source_contract_type") or "").strip(),
			"qwen_conversation_control_language_classifier",
		)

	def test_shared_control_language_supports_pronoun_discard_prefix_with_question_restore(self):
		evidence = classify_conversation_control_evidence("forget it, answer the last question")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "reopen_pending_clarification")
		self.assertTrue(bool((evidence.get("internal_details") or {}).get("discard_prefix_applied")))

	def test_shared_control_language_supports_pronoun_discard_prefix_with_targeted_restore(self):
		evidence = classify_conversation_control_evidence("ignore this and go back to the customer")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "replay_or_restore_prior_branch")
		self.assertEqual(
			str((evidence.get("internal_details") or {}).get("target_grain") or "").strip(),
			"customer",
		)
		self.assertTrue(bool((evidence.get("internal_details") or {}).get("discard_prefix_applied")))

	def test_shared_control_language_classifies_targeted_branch_restore(self):
		evidence = classify_conversation_control_evidence("go back to the customer")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "replay_or_restore_prior_branch")
		self.assertEqual(
			str((evidence.get("internal_details") or {}).get("target_grain") or "").strip(),
			"customer",
		)

	def test_shared_control_language_classifies_targeted_collection_alias_branch_restore(self):
		evidence = classify_conversation_control_evidence("go back to the supplier directory")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "replay_or_restore_prior_branch")
		self.assertEqual(
			str((evidence.get("internal_details") or {}).get("target_grain") or "").strip(),
			"supplier",
		)
		self.assertEqual(
			str((evidence.get("internal_details") or {}).get("target_focus_kind") or "").strip(),
			"listing",
		)

	def test_shared_control_language_classifies_plural_collection_alias_branch_restore(self):
		evidence = classify_conversation_control_evidence("go back to the supplier directories")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "replay_or_restore_prior_branch")
		self.assertEqual(
			str((evidence.get("internal_details") or {}).get("target_grain") or "").strip(),
			"supplier",
		)
		self.assertEqual(
			str((evidence.get("internal_details") or {}).get("target_focus_kind") or "").strip(),
			"listing",
		)

	def test_shared_control_language_reclassifies_discard_prefix_into_targeted_branch_restore(self):
		evidence = classify_conversation_control_evidence("forget that, go back to the customer")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "replay_or_restore_prior_branch")
		self.assertEqual(
			str((evidence.get("internal_details") or {}).get("target_grain") or "").strip(),
			"customer",
		)
		self.assertTrue(bool((evidence.get("internal_details") or {}).get("discard_prefix_applied")))

	def test_shared_control_language_classifies_targeted_document_branch_restore(self):
		evidence = classify_conversation_control_evidence("go back to the purchase order")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "replay_or_restore_prior_branch")
		self.assertEqual(
			str((evidence.get("internal_details") or {}).get("target_grain") or "").strip(),
			"purchase_order",
		)

	def test_shared_control_language_classifies_targeted_delivery_note_branch_restore(self):
		evidence = classify_conversation_control_evidence("go back to the delivery note")
		self.assertEqual(str(evidence.get("action_id") or "").strip(), "replay_or_restore_prior_branch")
		self.assertEqual(
			str((evidence.get("internal_details") or {}).get("target_grain") or "").strip(),
			"delivery_note",
		)

	def test_handle_pending_clarification_turn_accepts_shared_control_evidence_contract(self):
		signal = _clarification_signal(request_id="clarify-lane-1", user_question="Which item do you mean?")
		clarification_state = build_pending_clarification_state(signal)

		class _PayloadContract:
			def __init__(self, payload: Dict[str, Any]):
				self._payload = dict(payload)
				for key, value in self._payload.items():
					setattr(self, key, value)

			def to_payload(self):
				return dict(self._payload)

		handled, returned_contract, resolved_message, payload = handle_pending_clarification_turn(
			session_doc=_FakeSessionDoc(),
			request_id="clarify-lane-1",
			session_id="clarify-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			raw_message="show me the list",
			pending_clarification_signal=signal,
			clarification_state=clarification_state,
			clarification_response_contract=_PayloadContract(
				{
					"decision": "show_options",
					"reason": "The user asked to review the clarification options.",
					"resolved_option": "",
				}
			),
			interaction_contract=_PayloadContract({"type": "interaction"}),
			frontdoor_semantic_result=_PayloadContract({"type": "frontdoor_semantic"}),
			frontdoor_contract=_PayloadContract({"type": "frontdoor_contract"}),
			latest_grounded_turn_available=False,
			latest_grounded_turn={},
			conversation_control_evidence_contract=_PayloadContract({"type": "control_evidence"}),
			append_message=lambda *args, **kwargs: None,
			append_tool_payload=lambda *args, **kwargs: None,
			append_knowledge_boundary_contract=lambda *args, **kwargs: {},
			assistant_text_payload=lambda text: text,
			save_session=lambda *args, **kwargs: None,
		)

		self.assertTrue(handled)
		self.assertEqual(str(getattr(returned_contract, "to_payload")().get("decision") or "").strip(), "show_options")
		self.assertEqual(str(resolved_message or "").strip(), "show me the list")
		self.assertEqual(str((payload or {}).get("mode") or "").strip(), "clarification")
		self.assertEqual(str((((payload or {}).get("agent_meta") or {}).get("mode")) or "").strip(), "show_options")


	def test_entity_drilldown_lane_clears_pending_clarification_after_success(self):
		clear_calls = []

		def _try_entity_detail_followup(*args, **kwargs):
			return True, {"ok": True, "mode": "entity_drilldown"}

		with patch(
			"ai_assistant_ui.qwen_chat.lanes.entity_drilldown_lane.build_audit_envelope",
			return_value=types.SimpleNamespace(to_payload=lambda: {}),
		):
			handled, payload = handle_entity_drilldown_turn(
				session_doc=_FakeSessionDoc(),
				request_id="entity-drilldown-clear-1",
				session_id="entity-session",
				message="tell me more about Ko Nay Lin Mobile Center",
				entity_reference={"source": "explicit_identifier"},
				followup_resolution=types.SimpleNamespace(),
				interaction_contract=types.SimpleNamespace(request_id="entity-drilldown-clear-1"),
				response_policy_contract=types.SimpleNamespace(),
				frontdoor_contract=types.SimpleNamespace(to_payload=lambda: {}),
				scope_decision_contract=types.SimpleNamespace(to_payload=lambda: {}),
				latest_grounded_turn={},
				try_entity_detail_followup=_try_entity_detail_followup,
				append_tool_payload=lambda *args, **kwargs: None,
				append_knowledge_boundary_contract=lambda *args, **kwargs: {},
				build_latest_grounded_turn_contract=lambda *args, **kwargs: {},
				build_latest_qwen_trace_payload=lambda *args, **kwargs: {},
				build_latest_assistant_payload=lambda *args, **kwargs: {"text": "ok"},
				save_session=lambda *args, **kwargs: None,
				clear_pending_clarification_signal=lambda session_doc: clear_calls.append(True),
			)

		self.assertTrue(handled)
		self.assertEqual(payload, {"ok": True, "mode": "entity_drilldown"})
		self.assertEqual(clear_calls, [True])

	def test_artifact_boundary_lane_clears_pending_clarification_after_direct_evidence_answer(self):
		clear_calls = []
		session_doc = _FakeSessionDoc()
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.artifact_boundary_lane.build_audit_envelope",
			return_value=types.SimpleNamespace(to_payload=lambda: {}),
		):
			handled, payload = handle_artifact_boundary_turn(
				session_doc=session_doc,
				request_id="artifact-boundary-clear-1",
				session_id="artifact-session",
				message="how many stocks do we have for that product, and in which warehouse?",
				followup_resolution=types.SimpleNamespace(),
				interaction_contract=types.SimpleNamespace(request_id="artifact-boundary-clear-1"),
				response_policy_contract=types.SimpleNamespace(),
				frontdoor_contract=types.SimpleNamespace(to_payload=lambda: {}),
				scope_decision_contract=types.SimpleNamespace(to_payload=lambda: {}),
				latest_family_artifact={},
				latest_grounded_turn={},
				enrichment_compatibility_contract=None,
				grounded_artifact_direct_evidence_response=lambda **kwargs: {"answer_text": "We currently hold 587 units across 3 warehouses."},
				grounded_artifact_direct_evidence_answer=lambda **kwargs: "",
				grounded_artifact_evidence_boundary_answer=lambda **kwargs: "",
				artifact_enrichment_boundary_answer=lambda **kwargs: "",
				append_grounded_evidence_recovery_contract=lambda *args, **kwargs: {},
				append_enrichment_recovery_contract=lambda *args, **kwargs: {},
				session_tool_payloads=lambda *args, **kwargs: [],
				latest_tool_payload_by_type=lambda *args, **kwargs: {},
				append_artifact_boundary_observability=lambda *args, **kwargs: None,
				append_knowledge_boundary_contract=lambda *args, **kwargs: {},
				append_tool_payload=lambda *args, **kwargs: None,
				append_message=lambda *args, **kwargs: None,
				assistant_text_payload=lambda text: text,
				store_pending_clarification_signal=lambda *args, **kwargs: None,
				save_session=lambda *args, **kwargs: None,
				clear_pending_clarification_signal=lambda session_doc: clear_calls.append(True),
			)

		self.assertTrue(handled)
		self.assertEqual(str((payload or {}).get("mode") or "").strip(), "grounded_evidence_answer")
		self.assertEqual(clear_calls, [True])

	def test_artifact_boundary_lane_clears_pending_clarification_after_enrichment_boundary(self):
		clear_calls = []
		session_doc = _FakeSessionDoc()
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.artifact_boundary_lane.build_audit_envelope",
			return_value=types.SimpleNamespace(to_payload=lambda: {}),
		):
			handled, payload = handle_artifact_boundary_turn(
				session_doc=session_doc,
				request_id="artifact-boundary-clear-2",
				session_id="artifact-session",
				message="how many stocks do we have for that product, and in which warehouse?",
				followup_resolution=types.SimpleNamespace(),
				interaction_contract=types.SimpleNamespace(request_id="artifact-boundary-clear-2"),
				response_policy_contract=types.SimpleNamespace(),
				frontdoor_contract=types.SimpleNamespace(to_payload=lambda: {}),
				scope_decision_contract=types.SimpleNamespace(to_payload=lambda: {}),
				latest_family_artifact={},
				latest_grounded_turn={},
				enrichment_compatibility_contract=types.SimpleNamespace(
					compatible=False,
					reason="The current governed artifact cannot be enriched safely.",
				),
				grounded_artifact_direct_evidence_response=lambda **kwargs: {},
				grounded_artifact_direct_evidence_answer=lambda **kwargs: "",
				grounded_artifact_evidence_boundary_answer=lambda **kwargs: "",
				artifact_enrichment_boundary_answer=lambda **kwargs: "I couldn't complete that result confidently from governed ERP data.",
				append_grounded_evidence_recovery_contract=lambda *args, **kwargs: {},
				append_enrichment_recovery_contract=lambda *args, **kwargs: {},
				session_tool_payloads=lambda *args, **kwargs: [],
				latest_tool_payload_by_type=lambda *args, **kwargs: {},
				append_artifact_boundary_observability=lambda *args, **kwargs: None,
				append_knowledge_boundary_contract=lambda *args, **kwargs: {},
				append_tool_payload=lambda *args, **kwargs: None,
				append_message=lambda *args, **kwargs: None,
				assistant_text_payload=lambda text: text,
				store_pending_clarification_signal=lambda *args, **kwargs: None,
				save_session=lambda *args, **kwargs: None,
				clear_pending_clarification_signal=lambda session_doc: clear_calls.append(True),
			)

		self.assertTrue(handled)
		self.assertEqual(str((payload or {}).get("mode") or "").strip(), "artifact_enrichment_boundary")
		self.assertEqual(clear_calls, [True])
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

	def test_single_row_master_data_listing_promotes_recent_focus_to_specific_entity(self):
		recent_focus = _snapshot_recent_focus_state(
			latest_grounded_turn={
				"payload": {
					"request_id": "grounded-master-data-single-1",
					"source_kind": "report",
					"source_name": "Customer Master List",
					"artifact_family_id": "master_data_directory",
					"table_rows": [
						{
							"Customer": "Ko Nay Lin Mobile Center",
							"Customer Name": "Ko Nay Lin Mobile Center",
						}
					],
				},
				"available": True,
				"grounded": True,
				"source_tool_index": 17,
			},
			latest_artifact={
				"payload": {
					"family_id": "master_data_directory",
					"dimensions": {
						"entity_type": "customer",
					},
				},
			},
			latest_recovery_contract={},
		)

		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "entity")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "customer")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(str(recent_focus.get("focus_key") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "master_data_single_row_grounded_turn")
		self.assertTrue(bool(recent_focus.get("explicit_named_allowed")))

	def test_master_data_recent_focus_row_columns_follow_report_metadata(self):
		self.assertIn(
			"Customer Name",
			recent_focus_support_module.master_data_recent_focus_row_label_columns(
				focus_grain="customer",
				source_report="Customer Master List",
			),
		)
		self.assertIn(
			"Supplier Name",
			recent_focus_support_module.master_data_recent_focus_row_label_columns(
				focus_grain="supplier",
				source_report="Supplier Master List",
			),
		)
		item_label_columns = recent_focus_support_module.master_data_recent_focus_row_label_columns(
			focus_grain="item",
			source_report="Item Master List",
		)
		item_key_columns = recent_focus_support_module.master_data_recent_focus_row_key_columns(
			focus_grain="item",
			source_report="Item Master List",
		)
		self.assertIn("Item Name", item_label_columns)
		self.assertIn("Item", item_label_columns)
		self.assertIn("Item Code", item_key_columns)
		self.assertIn("name", item_key_columns)

	def test_grounded_recent_focus_surface_descriptor_uses_governed_report_family_for_master_data_listing(self):
		descriptor = recent_focus_support_module.grounded_recent_focus_surface_descriptor(
			source_report="Item Master List",
			source_family="",
			dimensions={},
		)

		self.assertEqual(str(descriptor.get("surface_class") or "").strip(), "master_data_listing")
		self.assertEqual(str(descriptor.get("focus_grain") or "").strip(), "item")
		self.assertEqual(str(descriptor.get("derivation_basis") or "").strip(), "master_data_listing_grounded_turn")

	def test_grounded_recent_focus_surface_descriptor_uses_governed_report_family_for_transaction_listing(self):
		descriptor = recent_focus_support_module.grounded_recent_focus_surface_descriptor(
			source_report="Purchase Invoice List",
			source_family="",
			dimensions={},
		)

		self.assertEqual(str(descriptor.get("surface_class") or "").strip(), "transaction_listing")
		self.assertEqual(str(descriptor.get("focus_grain") or "").strip(), "purchase_invoice")
		self.assertEqual(str(descriptor.get("derivation_basis") or "").strip(), "transaction_listing_grounded_turn")

	def test_grounded_recent_focus_surface_descriptor_uses_governed_report_family_for_statement(self):
		descriptor = recent_focus_support_module.grounded_recent_focus_surface_descriptor(
			source_report="Profit and Loss Statement",
			source_kind="report",
			source_family="",
			dimensions={},
		)

		self.assertEqual(str(descriptor.get("surface_class") or "").strip(), "statement")
		self.assertEqual(str(descriptor.get("focus_grain") or "").strip(), "profit_and_loss")
		self.assertEqual(str(descriptor.get("derivation_basis") or "").strip(), "statement_grounded_turn")

	def test_grounded_recent_focus_surface_descriptor_prefers_governed_analytical_policy_for_statement(self):
		descriptor = recent_focus_support_module.grounded_recent_focus_surface_descriptor(
			source_report="Profit and Loss Statement",
			source_kind="report",
			source_family="",
			dimensions={
				"governed_scope_runtime_policy": {
					"family_id": "financial_statement",
					"scope_id": "profit_and_loss",
					"scope_class": "financial_summary",
				},
			},
		)

		self.assertEqual(str(descriptor.get("surface_class") or "").strip(), "statement")
		self.assertEqual(str(descriptor.get("focus_grain") or "").strip(), "profit_and_loss")
		self.assertEqual(str(descriptor.get("source_family_default") or "").strip(), "financial_statement")
		self.assertEqual(str(descriptor.get("scope_id") or "").strip(), "profit_and_loss")
		self.assertEqual(str(descriptor.get("scope_class") or "").strip(), "financial_summary")

	def test_grounded_recent_focus_surface_descriptor_uses_shared_generic_report_descriptor(self):
		descriptor = recent_focus_support_module.grounded_recent_focus_surface_descriptor(
			source_report="Warehouse Wise Stock Balance",
			source_kind="report",
			source_family="inventory_snapshot",
			dimensions={},
		)

		self.assertEqual(str(descriptor.get("surface_class") or "").strip(), "report")
		self.assertEqual(str(descriptor.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(descriptor.get("focus_grain") or "").strip(), "inventory_snapshot")
		self.assertEqual(str(descriptor.get("derivation_basis") or "").strip(), "report_grounded_turn")

	def test_grounded_recent_focus_surface_descriptor_prefers_governed_analytical_policy_for_report(self):
		descriptor = recent_focus_support_module.grounded_recent_focus_surface_descriptor(
			source_report="Warehouse Wise Stock Balance",
			source_kind="report",
			source_family="",
			dimensions={
				"governed_scope_runtime_policy": {
					"family_id": "inventory_snapshot",
					"scope_id": "warehouse_item_snapshot",
					"scope_class": "inventory_summary",
				},
			},
		)

		self.assertEqual(str(descriptor.get("surface_class") or "").strip(), "report")
		self.assertEqual(str(descriptor.get("focus_grain") or "").strip(), "inventory_snapshot")
		self.assertEqual(str(descriptor.get("source_family_default") or "").strip(), "inventory_snapshot")
		self.assertEqual(str(descriptor.get("scope_id") or "").strip(), "warehouse_item_snapshot")
		self.assertEqual(str(descriptor.get("scope_class") or "").strip(), "inventory_summary")

	def test_build_grounded_recent_focus_state_from_surface_descriptor_shapes_master_data_listing(self):
		recent_focus = recent_focus_support_module.build_grounded_recent_focus_state_from_surface_descriptor(
			surface_descriptor={
				"surface_class": "master_data_listing",
				"focus_grain": "item",
				"source_family_default": "master_data_directory",
				"derivation_basis": "master_data_listing_grounded_turn",
			},
			source_request_id="rf-shape-1",
			source_family="",
			source_capability="item_master_read",
			source_report="Item Master List",
			source_tool_index=14,
		)

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "item")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "Item Master List")
		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "master_data_directory")
		self.assertEqual(str(recent_focus.get("source_capability") or "").strip(), "item_master_read")
		self.assertFalse(bool(recent_focus.get("explicit_named_allowed")))

	def test_build_grounded_recent_focus_state_preserves_governed_scope_fields_for_report(self):
		recent_focus = recent_focus_support_module.build_grounded_recent_focus_state_from_surface_descriptor(
			surface_descriptor={
				"surface_class": "report",
				"focus_kind": "report",
				"focus_grain": "inventory_snapshot",
				"focus_label": "Warehouse Wise Stock Balance",
				"focus_key": "Warehouse Wise Stock Balance",
				"source_family_default": "inventory_snapshot",
				"derivation_basis": "report_grounded_turn",
				"scope_id": "warehouse_item_snapshot",
				"scope_class": "inventory_summary",
			},
			source_request_id="rf-shape-analytical-1",
			source_family="",
			source_capability="",
			source_report="Warehouse Wise Stock Balance",
			source_tool_index=16,
		)

		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "inventory_snapshot")
		self.assertEqual(str(recent_focus.get("scope_id") or "").strip(), "warehouse_item_snapshot")
		self.assertEqual(str(recent_focus.get("scope_class") or "").strip(), "inventory_summary")

	def test_build_grounded_recent_focus_state_from_surface_descriptor_shapes_generic_report(self):
		recent_focus = recent_focus_support_module.build_grounded_recent_focus_state_from_surface_descriptor(
			surface_descriptor={
				"surface_class": "report",
				"focus_kind": "report",
				"focus_grain": "inventory_snapshot",
				"focus_label": "Warehouse Wise Stock Balance",
				"focus_key": "Warehouse Wise Stock Balance",
				"source_family_default": "report",
				"derivation_basis": "report_grounded_turn",
			},
			source_request_id="rf-shape-2",
			source_family="",
			source_capability="",
			source_report="Warehouse Wise Stock Balance",
			source_tool_index=15,
		)

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "inventory_snapshot")
		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "report")
		self.assertTrue(bool(recent_focus.get("explicit_named_allowed")))

	def test_build_grounded_recent_focus_state_from_surface_descriptor_shapes_entity_detail(self):
		recent_focus = recent_focus_support_module.build_grounded_recent_focus_state_from_surface_descriptor(
			surface_descriptor={
				"surface_class": "entity_detail",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
			},
			source_request_id="rf-shape-3",
			source_family="entity_detail",
			source_capability="customer_credit_profile",
			source_report="Customer Detail",
			source_tool_index=16,
		)

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "entity")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "entity_detail_grounded_turn")
		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "entity_detail")
		self.assertTrue(bool(recent_focus.get("explicit_named_allowed")))

	def test_build_grounded_recent_focus_state_from_surface_descriptor_shapes_document_detail(self):
		recent_focus = recent_focus_support_module.build_grounded_recent_focus_state_from_surface_descriptor(
			surface_descriptor={
				"surface_class": "entity_detail",
				"focus_grain": "sales_invoice",
				"focus_label": "ACC-SINV-2026-00194",
				"focus_key": "ACC-SINV-2026-00194",
			},
			source_request_id="rf-shape-4",
			source_family="entity_detail",
			source_capability="sales_invoice_read",
			source_report="Sales Invoice Detail",
			source_tool_index=17,
		)

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "document")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "document_detail_grounded_turn")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Sales Invoice Detail")

	def test_empty_recent_focus_state_uses_shared_conservative_shape(self):
		recent_focus = recent_focus_support_module.empty_recent_focus_state()

		self.assertFalse(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "none")
		self.assertEqual(int(recent_focus.get("source_tool_index")), -1)

	def test_build_single_row_document_recent_focus_state_uses_shared_shape(self):
		recent_focus = recent_focus_support_module.build_single_row_document_recent_focus_state(
			focus_grain="sales_invoice",
			focus_label="ACC-SINV-2026-00205",
			focus_key="ACC-SINV-2026-00205",
			source_request_id="grounded-single-row-document-1",
			source_family="transaction_listing",
			source_capability="sales_invoice_list_read",
			source_report="Sales Invoice List",
			source_tool_index=17,
		)

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "document")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "sales_invoice")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "ACC-SINV-2026-00205")
		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "transaction_listing")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_single_row_grounded_turn")
		self.assertEqual(float(recent_focus.get("confidence") or 0.0), 0.86)
		self.assertEqual(int(recent_focus.get("source_tool_index")), 17)

	def test_build_single_row_entity_recent_focus_state_uses_shared_shape(self):
		recent_focus = recent_focus_support_module.build_single_row_entity_recent_focus_state(
			focus_grain="customer",
			focus_label="Ko Nay Lin Mobile Center",
			focus_key="Ko Nay Lin Mobile Center",
			source_request_id="grounded-single-row-entity-1",
			source_family="master_data_directory",
			source_capability="customer_master_read",
			source_report="Customer Master List",
			source_tool_index=18,
		)

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "entity")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "customer")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "master_data_directory")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "master_data_single_row_grounded_turn")
		self.assertEqual(float(recent_focus.get("confidence") or 0.0), 0.88)
		self.assertEqual(int(recent_focus.get("source_tool_index")), 18)

	def test_recent_focus_runtime_route_selection_blocks_non_grounded_followup(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "listing",
			"focus_grain": "supplier",
			"focus_label": "Supplier Master List",
			"source_family": "master_data_directory",
			"source_capability": "supplier_master_read",
			"source_report": "Supplier Master List",
			"deictic_allowed": True,
			"explicit_named_allowed": False,
		}
		affordance_contract = recent_focus_support_module.build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-route-selection-1",
			recent_focus_state=recent_focus_state,
		)
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-route-selection-1",
			mode="new_query",
			requested_modes=["new_query"],
			depends_on_grounded_turn=False,
			latest_grounded_turn_available=False,
			reason="The request is not grounded on the latest turn.",
		)

		selection = recent_focus_support_module.recent_focus_runtime_route_selection(
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			recent_focus_affordance_contract=affordance_contract,
		)

		self.assertFalse(bool(selection.get("eligible")))
		self.assertEqual(selection.get("requested_modes"), [])
		self.assertFalse(bool(selection.get("local_transform_allowed")))
		self.assertFalse(bool(selection.get("requery_allowed")))

	def test_recent_focus_runtime_route_selection_composes_modes_and_permissions(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "listing",
			"focus_grain": "supplier",
			"focus_label": "Supplier Master List",
			"source_family": "master_data_directory",
			"source_capability": "supplier_master_read",
			"source_report": "Supplier Master List",
			"deictic_allowed": True,
			"explicit_named_allowed": False,
		}
		affordance_contract = recent_focus_support_module.build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-route-selection-2",
			recent_focus_state=recent_focus_state,
		)
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-route-selection-2",
			mode="new_query",
			requested_modes=["column_refinement", "new_query"],
			depends_on_grounded_turn=True,
			latest_grounded_turn_available=True,
			reason="The request stays on the latest supplier list.",
		)

		selection = recent_focus_support_module.recent_focus_runtime_route_selection(
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			recent_focus_affordance_contract=affordance_contract,
		)

		self.assertTrue(bool(selection.get("eligible")))
		self.assertEqual(selection.get("requested_modes"), ["column_refinement", "new_query"])
		self.assertTrue(bool(selection.get("local_transform_allowed")))
		self.assertTrue(bool(selection.get("requery_allowed")))

	def test_conversation_control_focus_target_from_recent_focus_state_uses_shared_shape(self):
		target = recent_focus_support_module.conversation_control_focus_target_from_recent_focus_state(
			{
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
			}
		)

		self.assertEqual(str(target.get("focus_kind") or "").strip(), "entity")
		self.assertEqual(str(target.get("focus_grain") or "").strip(), "item")
		self.assertEqual(str(target.get("focus_label") or "").strip(), "Type-C Cable 1m Fast Charge")
		self.assertEqual(str(target.get("focus_key") or "").strip(), "ACC-CBL-BAS-TC1M")
		self.assertEqual(str(target.get("source_family") or "").strip(), "entity_detail")
		self.assertTrue(bool(target.get("deictic_allowed")))
		self.assertTrue(bool(target.get("explicit_named_allowed")))

	def test_build_recent_focus_continuation_decision_spec_uses_shared_reason_and_payload(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "listing",
			"focus_grain": "supplier",
			"focus_label": "Supplier Master List",
			"focus_key": "supplier",
			"source_request_id": "supplier-list-2",
			"source_family": "master_data_directory",
			"source_capability": "supplier_master_read",
			"source_report": "Supplier Master List",
			"deictic_allowed": True,
			"explicit_named_allowed": False,
			"confidence": 0.84,
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-decision-spec-1",
			mode="new_query",
			requested_modes=["new_query"],
			depends_on_grounded_turn=True,
			latest_grounded_turn_available=True,
			reason="The follow-up depends on the latest grounded focus.",
		)
		spec = recent_focus_support_module.build_recent_focus_continuation_decision_spec(
			recent_focus_state=recent_focus_state,
			selection={"action": "allow", "basis": "shared_affordance_passthrough"},
			followup_resolution=followup_resolution,
			recent_focus_affordance_payload={"type": "qwen_recent_focus_affordance_contract"},
			control_action_id="show_pending_options",
			raw_message="show supplier name and payment terms only",
			routing_basis="shared_affordance",
		)

		self.assertEqual(
			str(spec.get("reason") or "").strip(),
			"The follow-up stays on the latest grounded business focus through the shared recent-focus affordance surface.",
		)
		self.assertEqual(float(spec.get("confidence") or 0.0), 0.84)
		self.assertEqual(
			str(((spec.get("resolved_focus_target") or {}).get("focus_label") or "").strip()),
			"Supplier Master List",
		)
		self.assertFalse(bool((spec.get("resolved_focus_target") or {}).get("listing_supported")))
		self.assertFalse(bool((spec.get("resolved_focus_target") or {}).get("detail_supported")))
		self.assertEqual(
			str(((spec.get("resolved_focus_target") or {}).get("listing_detail_support_status") or "").strip()),
			"",
		)
		self.assertEqual(
			str((((spec.get("internal_details") or {}).get("recent_focus_affordance") or {}).get("type")) or "").strip(),
			"qwen_recent_focus_affordance_contract",
		)
		self.assertEqual(
			str(((spec.get("internal_details") or {}).get("routing_basis") or "").strip()),
			"shared_affordance",
		)

	def test_build_recent_focus_continuation_decision_spec_enriches_resolved_focus_target_with_parity(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "listing",
			"focus_grain": "supplier",
			"focus_label": "Supplier Master List",
			"focus_key": "supplier",
			"source_request_id": "supplier-list-3",
			"source_family": "master_data_directory",
			"source_capability": "supplier_master_read",
			"source_report": "Supplier Master List",
			"deictic_allowed": True,
			"explicit_named_allowed": False,
			"confidence": 0.88,
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-decision-spec-2",
			mode="new_query",
			requested_modes=["new_query"],
			depends_on_grounded_turn=True,
			latest_grounded_turn_available=True,
			reason="The follow-up depends on the latest grounded focus.",
		)
		spec = recent_focus_support_module.build_recent_focus_continuation_decision_spec(
			recent_focus_state=recent_focus_state,
			selection={"action": "allow", "basis": "shared_affordance_passthrough"},
			followup_resolution=followup_resolution,
			recent_focus_affordance_payload={
				"type": "qwen_recent_focus_affordance_contract",
				"listing_supported": True,
				"detail_supported": True,
				"listing_detail_support_status": "both",
			},
			control_action_id="show_pending_options",
			raw_message="tell me more about that supplier",
			routing_basis="local_transform",
		)

		self.assertTrue(bool((spec.get("resolved_focus_target") or {}).get("listing_supported")))
		self.assertTrue(bool((spec.get("resolved_focus_target") or {}).get("detail_supported")))
		self.assertEqual(
			str(((spec.get("resolved_focus_target") or {}).get("listing_detail_support_status") or "").strip()),
			"both",
		)

	def test_recent_focus_continuation_eligibility_allows_shared_affordance_passthrough(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "listing",
			"focus_grain": "supplier",
			"focus_label": "Supplier Master List",
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-shared-eligibility-1",
			mode="new_query",
			requested_modes=["new_query"],
			depends_on_grounded_turn=True,
			latest_grounded_turn_available=True,
			reason="The follow-up depends on the latest grounded focus.",
		)

		selected = recent_focus_support_module.recent_focus_continuation_eligibility(
			raw_message="show supplier name and payment terms only",
			runtime_message="show supplier name and payment terms only",
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			has_strong_control_owner=False,
			routing_basis="shared_affordance",
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "allow")
		self.assertEqual(str(selected.get("basis") or "").strip(), "shared_affordance_passthrough")
		self.assertTrue(bool(selected.get("allow_passthrough")))

	def test_recent_focus_continuation_eligibility_blocks_strong_control_owner(self):
		recent_focus_state = {
			"available": True,
			"focus_kind": "entity",
			"focus_grain": "item",
			"focus_label": "Type-C Cable 1m Fast Charge",
		}
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-shared-eligibility-2",
			mode="new_query",
			requested_modes=["new_query"],
			depends_on_grounded_turn=True,
			latest_grounded_turn_available=True,
			reason="The follow-up depends on the latest grounded focus.",
		)

		selected = recent_focus_support_module.recent_focus_continuation_eligibility(
			raw_message="ignore that",
			runtime_message='how many stocks do we have, and in which warehouse for item "Type-C Cable 1m Fast Charge"?',
			recent_focus_state=recent_focus_state,
			followup_resolution=followup_resolution,
			has_strong_control_owner=True,
			routing_basis="local_transform",
		)

		self.assertEqual(str(selected.get("action") or "").strip(), "block")
		self.assertEqual(str(selected.get("basis") or "").strip(), "strong_control_owner")

	def test_recent_focus_runtime_routing_permissions_allow_entity_local_transform_fallback(self):
		permissions = recent_focus_support_module.recent_focus_runtime_routing_permissions(
			recent_focus_state={
				"available": True,
				"focus_kind": "entity",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
			requested_modes=["new_query"],
			allowed_local_followup_modes=[],
			allowed_requery_followup_modes=[],
			supports_cross_family_followup=True,
		)

		self.assertTrue(bool(permissions.get("local_transform_allowed")))
		self.assertTrue(bool(permissions.get("requery_allowed")))

	def test_recent_focus_runtime_routing_permissions_follow_affordance_mode_sets_for_listing(self):
		permissions = recent_focus_support_module.recent_focus_runtime_routing_permissions(
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
			requested_modes=["column_refinement"],
			allowed_local_followup_modes=["column_refinement"],
			allowed_requery_followup_modes=["new_query"],
			supports_cross_family_followup=True,
		)

		self.assertTrue(bool(permissions.get("local_transform_allowed")))
		self.assertFalse(bool(permissions.get("requery_allowed")))

	def test_empty_resumable_prior_request_state_uses_shared_conservative_shape(self):
		prior_request = snapshot_defaults_module.empty_resumable_prior_request_state()

		self.assertFalse(bool(prior_request.get("available")))
		self.assertEqual(str(prior_request.get("branch_kind") or "").strip(), "none")
		self.assertEqual(str(prior_request.get("derivation_basis") or "").strip(), "conservative_none")
		self.assertEqual(int(prior_request.get("source_tool_index")), -1)

	def test_build_snapshot_state_quality_uses_shared_snapshot_quality_shape(self):
		quality = snapshot_defaults_module.build_snapshot_state_quality(
			pending_clarification={"available": True, "source_kind": "stored_state"},
			latest_grounded_turn={"available": True, "grounded": True},
			latest_artifact={"available": True, "grounded_compatible": True},
			latest_recovery_contract={"available": True},
			latest_repair_intent={"available": True},
			active_sequence={"active": True},
			recent_focus={"available": True},
			recent_focus_affordance={"type": "qwen_recent_focus_affordance_contract"},
			resumable_prior_request={"available": False},
		)

		self.assertTrue(bool(quality.get("has_authoritative_pending_clarification")))
		self.assertTrue(bool(quality.get("has_grounded_turn")))
		self.assertTrue(bool(quality.get("has_grounded_compatible_artifact")))
		self.assertTrue(bool(quality.get("has_recovery_contract")))
		self.assertTrue(bool(quality.get("has_latest_repair_intent")))
		self.assertTrue(bool(quality.get("has_active_sequence")))
		self.assertTrue(bool(quality.get("has_recent_focus")))
		self.assertTrue(bool(quality.get("has_recent_focus_affordance")))
		self.assertFalse(bool(quality.get("has_resumable_prior_request")))

	def test_build_snapshot_internal_details_uses_shared_snapshot_summary_shape(self):
		internal_details = snapshot_defaults_module.build_snapshot_internal_details(
			pending_clarification={"source_kind": "message_fallback"},
			latest_artifact={"source_quality": "fallback_candidate"},
			latest_repair_intent={"repair_intent_type": "guidance_request"},
			recent_focus={"derivation_basis": "transaction_listing_grounded_turn"},
			recent_focus_affordance={"reason": "listing_followup_supported"},
			resumable_prior_request={"derivation_basis": "conservative_none"},
		)

		source_summary = internal_details.get("source_summary") or {}
		self.assertEqual(str(source_summary.get("pending_clarification_source_kind") or "").strip(), "message_fallback")
		self.assertEqual(str(source_summary.get("latest_artifact_source_quality") or "").strip(), "fallback_candidate")
		self.assertEqual(str(source_summary.get("latest_repair_intent_type") or "").strip(), "guidance_request")
		self.assertEqual(str(source_summary.get("recent_focus_derivation_basis") or "").strip(), "transaction_listing_grounded_turn")
		self.assertEqual(str(source_summary.get("recent_focus_affordance_reason") or "").strip(), "listing_followup_supported")
		self.assertEqual(str(source_summary.get("resumable_prior_request_derivation_basis") or "").strip(), "conservative_none")
		self.assertEqual(
			list(internal_details.get("fallbacks_used") or []),
			["pending_clarification_message_fallback", "artifact_fallback_candidate"],
		)

	def test_build_pending_clarification_snapshot_state_uses_shared_pending_shape(self):
		pending_state = snapshot_defaults_module.build_pending_clarification_snapshot_state(
			signal={"request_id": "clar-1", "question": "Which one?"},
			source_kind="stored_state",
			attempt_count=2,
			max_attempts=3,
			continuation_lane="clarification_resolution",
			status="pending",
			source_tool_index=11,
		)

		self.assertTrue(bool(pending_state.get("available")))
		self.assertEqual(str(pending_state.get("source_kind") or "").strip(), "stored_state")
		self.assertEqual(int(pending_state.get("attempt_count")), 2)
		self.assertEqual(int(pending_state.get("max_attempts")), 3)
		self.assertEqual(str(pending_state.get("continuation_lane") or "").strip(), "clarification_resolution")
		self.assertEqual(str(pending_state.get("status") or "").strip(), "pending")
		self.assertEqual(int(pending_state.get("source_tool_index")), 11)

	def test_build_latest_grounded_turn_snapshot_state_uses_shared_grounded_shape(self):
		grounded_state = snapshot_defaults_module.build_latest_grounded_turn_snapshot_state(
			payload={
				"request_id": "grounded-1",
				"trace_request_id": "grounded-1-trace",
				"grounded": True,
				"source_name": "Customer Detail",
				"artifact_family_id": "entity_detail",
				"artifact_source_reports": ["Customer Detail", " ", "Customer Ledger"],
			},
			source_tool_index=14,
		)

		self.assertTrue(bool(grounded_state.get("available")))
		self.assertEqual(str(grounded_state.get("request_id") or "").strip(), "grounded-1")
		self.assertEqual(str(grounded_state.get("trace_request_id") or "").strip(), "grounded-1-trace")
		self.assertTrue(bool(grounded_state.get("grounded")))
		self.assertEqual(str(grounded_state.get("source_name") or "").strip(), "Customer Detail")
		self.assertEqual(str(grounded_state.get("artifact_family_id") or "").strip(), "entity_detail")
		self.assertEqual(list(grounded_state.get("artifact_source_reports") or []), ["Customer Detail", "Customer Ledger"])
		self.assertEqual(str(grounded_state.get("source_quality") or "").strip(), "grounded")
		self.assertEqual(int(grounded_state.get("source_tool_index")), 14)

	def test_build_latest_artifact_snapshot_state_uses_shared_artifact_shape(self):
		artifact_state = snapshot_defaults_module.build_latest_artifact_snapshot_state(
			payload={
				"request_id": "artifact-1",
				"family_id": "entity_detail",
				"artifact_type": "normalized_family_artifact",
				"source_reports": ["Customer Detail", "", "Customer Ledger"],
			},
			grounded_compatible=True,
			source_tool_index=15,
		)

		self.assertTrue(bool(artifact_state.get("available")))
		self.assertEqual(str(artifact_state.get("request_id") or "").strip(), "artifact-1")
		self.assertEqual(str(artifact_state.get("family_id") or "").strip(), "entity_detail")
		self.assertEqual(str(artifact_state.get("artifact_type") or "").strip(), "normalized_family_artifact")
		self.assertEqual(list(artifact_state.get("source_reports") or []), ["Customer Detail", "Customer Ledger"])
		self.assertTrue(bool(artifact_state.get("grounded_compatible")))
		self.assertEqual(str(artifact_state.get("source_quality") or "").strip(), "grounded_compatible")
		self.assertEqual(int(artifact_state.get("source_tool_index")), 15)

	def test_build_latest_artifact_snapshot_state_falls_back_to_payload_type(self):
		artifact_state = snapshot_defaults_module.build_latest_artifact_snapshot_state(
			payload={
				"request_id": "artifact-2",
				"family_id": "transaction_listing",
				"type": "qwen_normalized_family_artifact_contract",
				"source_reports": ["Payment Entry List"],
			},
			grounded_compatible=False,
			source_tool_index=15,
		)

		self.assertEqual(
			str(artifact_state.get("artifact_type") or "").strip(),
			"qwen_normalized_family_artifact_contract",
		)
		self.assertEqual(str(artifact_state.get("source_quality") or "").strip(), "fallback_candidate")

	def test_build_active_sequence_snapshot_state_uses_shared_sequence_shape(self):
		active_sequence_state = snapshot_defaults_module.build_active_sequence_snapshot_state(
			payload={
				"request_id": "compound-1",
				"status": "ordered_execution_active",
				"segments": ["show me payment entries", "", "give me some customer list"],
				"internal_details": {
					"primary_segment_message": "show me payment entries",
					"remaining_segment_messages": ["give me some customer list", ""],
					"execution_strategy": "ordered",
				},
			},
			active=True,
			source_tool_index=16,
		)

		self.assertTrue(bool(active_sequence_state.get("available")))
		self.assertEqual(str(active_sequence_state.get("request_id") or "").strip(), "compound-1")
		self.assertEqual(str(active_sequence_state.get("status") or "").strip(), "ordered_execution_active")
		self.assertEqual(
			list(active_sequence_state.get("segments") or []),
			["show me payment entries", "give me some customer list"],
		)
		self.assertEqual(
			str(active_sequence_state.get("primary_segment_message") or "").strip(),
			"show me payment entries",
		)
		self.assertEqual(
			list(active_sequence_state.get("remaining_segment_messages") or []),
			["give me some customer list"],
		)
		self.assertEqual(str(active_sequence_state.get("execution_strategy") or "").strip(), "ordered")
		self.assertTrue(bool(active_sequence_state.get("active")))
		self.assertEqual(int(active_sequence_state.get("source_tool_index")), 16)

	def test_build_historical_recent_focus_snapshot_inputs_uses_shared_snapshot_shapes(self):
		historical_inputs = snapshot_defaults_module.build_historical_recent_focus_snapshot_inputs(
			grounded_turn_payload={
				"request_id": "grounded-historical-1",
				"trace_request_id": "grounded-historical-1-trace",
				"grounded": True,
				"source_name": "Customer Detail",
				"artifact_family_id": "entity_detail",
				"artifact_source_reports": ["Customer Detail", ""],
			},
			grounded_turn_source_tool_index=3,
			artifact_payload={
				"request_id": "grounded-historical-1-trace",
				"family_id": "entity_detail",
				"type": "qwen_normalized_family_artifact_contract",
				"source_reports": ["Customer Detail"],
			},
			artifact_source_tool_index=4,
			recovery_payload={
				"request_id": "recovery-historical-1",
				"source_request_id": "grounded-historical-1-trace",
				"source_family_id": "entity_detail",
				"source_capability_id": "customer_detail_read",
				"source_report": "Customer Detail",
				"recovery_state": "recoverable",
				"recommended_recovery_action": "run_alternative_governed_query",
				"allowed_to_recover": True,
			},
			recovery_source_tool_index=5,
		)

		grounded_state = historical_inputs.get("latest_grounded_turn") or {}
		artifact_state = historical_inputs.get("latest_artifact") or {}
		recovery_state = historical_inputs.get("latest_recovery_contract") or {}

		self.assertEqual(str(grounded_state.get("trace_request_id") or "").strip(), "grounded-historical-1-trace")
		self.assertEqual(int(grounded_state.get("source_tool_index")), 3)
		self.assertEqual(str(artifact_state.get("artifact_type") or "").strip(), "qwen_normalized_family_artifact_contract")
		self.assertTrue(bool(artifact_state.get("grounded_compatible")))
		self.assertEqual(int(artifact_state.get("source_tool_index")), 4)
		self.assertEqual(str(recovery_state.get("source_capability_id") or "").strip(), "customer_detail_read")
		self.assertEqual(int(recovery_state.get("source_tool_index")), 5)

	def test_build_latest_recovery_contract_snapshot_state_uses_shared_recovery_shape(self):
		recovery_state = snapshot_defaults_module.build_latest_recovery_contract_snapshot_state(
			payload={
				"request_id": "recovery-1",
				"source_request_id": "grounded-1",
				"source_family_id": "sales_analytics",
				"source_capability_id": "sales_read",
				"source_report": "Sales Analytics",
				"recovery_state": "recoverable",
				"recommended_recovery_action": "run_alternative_governed_query",
				"allowed_to_recover": True,
			},
			source_tool_index=12,
		)

		self.assertTrue(bool(recovery_state.get("available")))
		self.assertEqual(str(recovery_state.get("request_id") or "").strip(), "recovery-1")
		self.assertEqual(str(recovery_state.get("source_capability_id") or "").strip(), "sales_read")
		self.assertEqual(str(recovery_state.get("recovery_state") or "").strip(), "recoverable")
		self.assertTrue(bool(recovery_state.get("allowed_to_recover")))
		self.assertEqual(int(recovery_state.get("source_tool_index")), 12)

	def test_build_latest_repair_intent_snapshot_state_uses_shared_repair_shape(self):
		repair_state = snapshot_defaults_module.build_latest_repair_intent_snapshot_state(
			payload={
				"request_id": "repair-1",
				"repair_intent_type": "accept_recovery_action",
				"repair_state": "accepted",
				"targets_prior_recovery": True,
				"accepted_recovery_action": "run_alternative_governed_query",
				"allowed_next_lane": "fresh_query",
				"confidence": 1.4,
			},
			source_tool_index=13,
		)

		self.assertTrue(bool(repair_state.get("available")))
		self.assertEqual(str(repair_state.get("repair_intent_type") or "").strip(), "accept_recovery_action")
		self.assertEqual(str(repair_state.get("repair_state") or "").strip(), "accepted")
		self.assertTrue(bool(repair_state.get("targets_prior_recovery")))
		self.assertEqual(str(repair_state.get("allowed_next_lane") or "").strip(), "fresh_query")
		self.assertEqual(float(repair_state.get("confidence")), 1.0)
		self.assertEqual(int(repair_state.get("source_tool_index")), 13)

	def test_single_row_item_master_listing_uses_metadata_backed_label_and_key_columns(self):
		recent_focus = _snapshot_recent_focus_state(
			latest_grounded_turn={
				"payload": {
					"request_id": "grounded-master-data-single-item-1",
					"source_kind": "report",
					"source_name": "Item Master List",
					"artifact_family_id": "master_data_directory",
					"table_rows": [
						{
							"Item": "ACC-CBL-BAS-TC1M",
							"Item Name": "Type-C Cable 1m Fast Charge",
						}
					],
				},
				"available": True,
				"grounded": True,
				"source_tool_index": 18,
			},
			latest_artifact={
				"payload": {
					"family_id": "master_data_directory",
					"dimensions": {
						"entity_type": "item",
					},
				},
			},
			latest_recovery_contract={},
		)

		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "entity")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "item")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "Type-C Cable 1m Fast Charge")
		self.assertEqual(str(recent_focus.get("focus_key") or "").strip(), "ACC-CBL-BAS-TC1M")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "master_data_single_row_grounded_turn")
		self.assertTrue(bool(recent_focus.get("explicit_named_allowed")))

	def test_single_row_transaction_listing_keeps_listing_focus_when_scope_is_not_detail_capable(self):
		recent_focus = _snapshot_recent_focus_state(
			latest_grounded_turn={
				"payload": {
					"request_id": "grounded-transaction-single-1",
					"source_kind": "report",
					"source_name": "Payment Entry List",
					"artifact_family_id": "transaction_listing",
					"table_rows": [
						{
							"Payment Entry": "ACC-PAY-2026-00179",
							"Party": "Golden Dragon Trading Co. Ltd.",
						}
					],
				},
				"available": True,
				"grounded": True,
				"source_tool_index": 19,
			},
			latest_artifact={
				"payload": {
					"family_id": "transaction_listing",
					"dimensions": {
						"listing_view": "payment_entry",
					},
				},
			},
			latest_recovery_contract={"source_capability_id": "payment_entry_read"},
		)

		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "payment_entry")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "Payment Entry List")
		self.assertEqual(str(recent_focus.get("focus_key") or "").strip(), "payment_entry")
		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "transaction_listing")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_listing_grounded_turn")
		self.assertFalse(bool(recent_focus.get("explicit_named_allowed")))

	def test_single_row_purchase_order_listing_promotes_recent_focus_to_specific_document_before_entity_grain_fallback(self):
		recent_focus = _snapshot_recent_focus_state(
			latest_grounded_turn={
				"payload": {
					"request_id": "grounded-transaction-single-2",
					"source_kind": "report",
					"source_name": "Purchase Order List",
					"artifact_family_id": "transaction_listing",
					"table_rows": [
						{
							"Purchase Order": "PUR-ORD-2026-00004",
							"Supplier": "Shwe Taung Electronics Supply",
						}
					],
				},
				"available": True,
				"grounded": True,
				"source_tool_index": 20,
			},
			latest_artifact={
				"payload": {
					"family_id": "transaction_listing",
					"dimensions": {
						"listing_view": "purchase_order",
						"entity_type": "supplier",
					},
				},
			},
			latest_recovery_contract={"source_capability_id": "purchase_order_read"},
		)

		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "document")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "purchase_order")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "PUR-ORD-2026-00004")
		self.assertEqual(str(recent_focus.get("focus_key") or "").strip(), "PUR-ORD-2026-00004")
		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "transaction_listing")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_single_row_grounded_turn")
		self.assertTrue(bool(recent_focus.get("explicit_named_allowed")))

	def test_detail_capable_document_focus_grains_follow_governed_scope_policy(self):
		grains = set(recent_focus_support_module.detail_capable_document_focus_grains())

		self.assertEqual(
			grains,
			{
				"sales_invoice",
				"purchase_invoice",
				"delivery_note",
				"sales_order",
				"purchase_order",
			},
		)
		self.assertNotIn("payment_entry", grains)
		self.assertNotIn("purchase_receipt", grains)

	def test_single_row_sales_order_listing_promotes_recent_focus_to_specific_document(self):
		recent_focus = _snapshot_recent_focus_state(
			latest_grounded_turn={
				"payload": {
					"request_id": "grounded-transaction-single-3",
					"source_kind": "report",
					"source_name": "Sales Order List",
					"artifact_family_id": "transaction_listing",
					"table_rows": [
						{
							"Sales Order": "SAL-ORD-2026-00029",
							"Customer": "Bayint Naung Wholesale Mobile",
						}
					],
				},
				"available": True,
				"grounded": True,
				"source_tool_index": 21,
			},
			latest_artifact={
				"payload": {
					"family_id": "transaction_listing",
					"dimensions": {
						"listing_view": "sales_order",
						"entity_type": "customer",
					},
				},
			},
			latest_recovery_contract={"source_capability_id": "sales_order_read"},
		)

		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "document")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "sales_order")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "SAL-ORD-2026-00029")
		self.assertEqual(str(recent_focus.get("focus_key") or "").strip(), "SAL-ORD-2026-00029")
		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "transaction_listing")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_single_row_grounded_turn")
		self.assertTrue(bool(recent_focus.get("explicit_named_allowed")))

	def test_single_row_delivery_note_listing_promotes_recent_focus_to_specific_document(self):
		recent_focus = _snapshot_recent_focus_state(
			latest_grounded_turn={
				"payload": {
					"request_id": "grounded-transaction-single-4",
					"source_kind": "report",
					"source_name": "Delivery Note List",
					"artifact_family_id": "transaction_listing",
					"table_rows": [
						{
							"Delivery Note": "MAT-DN-2026-00018",
							"Customer": "Bayint Naung Wholesale Mobile",
						}
					],
				},
				"available": True,
				"grounded": True,
				"source_tool_index": 22,
			},
			latest_artifact={
				"payload": {
					"family_id": "transaction_listing",
					"dimensions": {
						"listing_view": "delivery_note",
						"entity_type": "customer",
					},
				},
			},
			latest_recovery_contract={"source_capability_id": "delivery_note_read"},
		)

		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "document")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "delivery_note")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "MAT-DN-2026-00018")
		self.assertEqual(str(recent_focus.get("focus_key") or "").strip(), "MAT-DN-2026-00018")
		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "transaction_listing")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_single_row_grounded_turn")
		self.assertTrue(bool(recent_focus.get("explicit_named_allowed")))

	def test_single_row_purchase_receipt_listing_keeps_listing_focus_when_detail_is_not_active(self):
		recent_focus = _snapshot_recent_focus_state(
			latest_grounded_turn={
				"payload": {
					"request_id": "grounded-transaction-single-5",
					"source_kind": "report",
					"source_name": "Purchase Receipt List",
					"artifact_family_id": "transaction_listing",
					"table_rows": [
						{
							"Purchase Receipt": "PUR-REC-2026-00011",
							"Supplier": "Sunflower Accessories Co.",
						}
					],
				},
				"available": True,
				"grounded": True,
				"source_tool_index": 23,
			},
			latest_artifact={
				"payload": {
					"family_id": "transaction_listing",
					"dimensions": {
						"listing_view": "purchase_receipt",
						"entity_type": "supplier",
					},
				},
			},
			latest_recovery_contract={"source_capability_id": "purchase_receipt_read"},
		)

		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "purchase_receipt")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "Purchase Receipt List")
		self.assertEqual(str(recent_focus.get("focus_key") or "").strip(), "purchase_receipt")
		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "transaction_listing")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_listing_grounded_turn")
		self.assertFalse(bool(recent_focus.get("explicit_named_allowed")))

	def test_single_row_purchase_invoice_listing_promotes_recent_focus_to_specific_document(self):
		recent_focus = _snapshot_recent_focus_state(
			latest_grounded_turn={
				"payload": {
					"request_id": "grounded-transaction-single-6",
					"source_kind": "report",
					"source_name": "Purchase Invoice List",
					"artifact_family_id": "transaction_listing",
					"table_rows": [
						{
							"Purchase Invoice": "ACC-PINV-2026-00335",
							"Supplier": "Myanmar Tech Import Services",
						}
					],
				},
				"available": True,
				"grounded": True,
				"source_tool_index": 24,
			},
			latest_artifact={
				"payload": {
					"family_id": "transaction_listing",
					"dimensions": {
						"listing_view": "purchase_invoice",
						"entity_type": "supplier",
					},
				},
			},
			latest_recovery_contract={"source_capability_id": "purchase_invoice_read"},
		)

		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "document")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "purchase_invoice")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "ACC-PINV-2026-00335")
		self.assertEqual(str(recent_focus.get("focus_key") or "").strip(), "ACC-PINV-2026-00335")
		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "transaction_listing")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_single_row_grounded_turn")
		self.assertTrue(bool(recent_focus.get("explicit_named_allowed")))

	def test_targeted_branch_restore_from_master_data_entity_focus_clears_pending_clarification(self):
		snapshot = {
			"pending_clarification": {
				"available": True,
				"continuation_lane": "front_door",
				"signal": {
					"request_id": "clarify-targeted-master-1",
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
				"source_request_id": "grounded-master-data-single-2",
				"source_family": "master_data_directory",
				"source_capability": "",
				"source_report": "Customer Master List",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "master_data_single_row_grounded_turn",
				"confidence": 0.88,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-master-1",
			raw_message="go back to the customer",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-master-1",
				raw_message="go back to the customer",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertTrue(bool(payload.get("clear_current_pending_clarification")))

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

	def test_select_targeted_restore_owner_prefers_recent_focus_match(self):
		selected = _select_targeted_restore_owner(
			recent_focus={
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"source_report": "Customer Detail",
			},
			resumable_prior_request={
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"target_family": "customer_rankings",
			},
			target_hint="customer",
			target_grain="customer",
			target_focus_kind="entity",
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "recent_focus")
		self.assertEqual(str(selected.get("basis") or "").strip(), "targeted_recent_focus_restore")

	def test_select_targeted_restore_owner_uses_resumable_prior_request_when_recent_focus_does_not_match(self):
		selected = _select_targeted_restore_owner(
			recent_focus={
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "supplier",
				"focus_label": "Sunflower Accessories Co.",
				"source_report": "Supplier Detail",
			},
			resumable_prior_request={
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Customers by Revenue",
				"target_family": "customer_rankings",
				"target_scope": {
					"focus_kind": "entity",
					"focus_grain": "customer",
					"focus_label": "Top Customers by Revenue",
					"source_report": "Top Customers by Revenue",
				},
			},
			target_hint="customer",
			target_grain="customer",
			target_focus_kind="entity",
		)

		self.assertEqual(str(selected.get("owner") or "").strip(), "resumable_prior_request")
		self.assertEqual(
			str(selected.get("basis") or "").strip(),
			"targeted_resumable_prior_branch_restore",
		)

	def test_select_targeted_restore_owner_returns_empty_when_no_targeted_match_exists(self):
		selected = _select_targeted_restore_owner(
			recent_focus={
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "supplier",
				"focus_label": "Sunflower Accessories Co.",
				"source_report": "Supplier Detail",
			},
			resumable_prior_request={
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"branch_label": "Top Suppliers by Spend",
				"target_family": "supplier_rankings",
			},
			target_hint="customer",
			target_grain="customer",
			target_focus_kind="entity",
		)

		self.assertEqual(selected, {"owner": "", "basis": ""})

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
		self.assertFalse(bool((payload.get("target_scope") or {}).get("deictic_allowed")))
		self.assertTrue(bool((payload.get("target_scope") or {}).get("explicit_named_allowed")))

	def test_targeted_master_data_restore_keeps_recent_focus_reference_policy_fields(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "supplier",
				"focus_label": "Supplier Master List",
				"focus_key": "supplier",
				"source_request_id": "supplier-list-restore-1",
				"source_family": "master_data_directory",
				"source_capability": "supplier_master_read",
				"source_report": "Supplier Master List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
				"derivation_basis": "master_data_listing_grounded_turn",
				"confidence": 0.82,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-focus-4c",
			raw_message="go back to the suppliers",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-7c",
				raw_message="go back to the suppliers",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_family") or "").strip(), "master_data_directory")
		self.assertEqual(str(((payload.get("target_scope") or {}).get("source_capability")) or "").strip(), "supplier_master_read")
		self.assertTrue(bool((payload.get("target_scope") or {}).get("deictic_allowed")))
		self.assertFalse(bool((payload.get("target_scope") or {}).get("explicit_named_allowed")))

	def test_targeted_purchase_order_restore_keeps_recent_focus_reference_policy_fields(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "document",
				"focus_grain": "purchase_order",
				"focus_label": "PUR-ORD-2026-00004",
				"focus_key": "PUR-ORD-2026-00004",
				"source_request_id": "purchase-order-restore-1",
				"source_family": "entity_detail",
				"source_capability": "purchase_order_read",
				"source_report": "Purchase Order Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "document_detail_grounded_turn",
				"confidence": 0.86,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-focus-document-1",
			raw_message="go back to the purchase order",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-document-1",
				raw_message="go back to the purchase order",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_family") or "").strip(), "entity_detail")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "PUR-ORD-2026-00004")
		self.assertEqual(str(((payload.get("target_scope") or {}).get("focus_kind")) or "").strip(), "document")
		self.assertEqual(str(((payload.get("target_scope") or {}).get("focus_grain")) or "").strip(), "purchase_order")
		self.assertEqual(str(((payload.get("target_scope") or {}).get("source_capability")) or "").strip(), "purchase_order_read")
		self.assertTrue(bool((payload.get("target_scope") or {}).get("deictic_allowed")))
		self.assertTrue(bool((payload.get("target_scope") or {}).get("explicit_named_allowed")))

	def test_targeted_transaction_document_restore_keeps_recent_focus_reference_policy_fields(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "document",
				"focus_grain": "payment_entry",
				"focus_label": "ACC-PAY-2026-00179",
				"focus_key": "ACC-PAY-2026-00179",
				"source_request_id": "payment-entry-restore-1",
				"source_family": "transaction_listing",
				"source_capability": "payment_entry_read",
				"source_report": "Payment Entry List",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"derivation_basis": "transaction_single_row_grounded_turn",
				"confidence": 0.86,
			},
			"resumable_prior_request": {"available": False},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-focus-document-2",
			raw_message="go back to the payment entry",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-document-2",
				raw_message="go back to the payment entry",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_family") or "").strip(), "transaction_listing")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "ACC-PAY-2026-00179")
		self.assertEqual(str(((payload.get("target_scope") or {}).get("focus_kind")) or "").strip(), "document")
		self.assertEqual(str(((payload.get("target_scope") or {}).get("focus_grain")) or "").strip(), "payment_entry")
		self.assertEqual(str(((payload.get("target_scope") or {}).get("source_capability")) or "").strip(), "payment_entry_read")
		self.assertTrue(bool((payload.get("target_scope") or {}).get("deictic_allowed")))
		self.assertTrue(bool((payload.get("target_scope") or {}).get("explicit_named_allowed")))

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
		) as append_tool_payload_mock, patch(
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
				additional_tool_payloads=[{"type": "qwen_compound_request_assessment_contract", "status": "ordered_execution_complete"}],
			)

		self.assertTrue(handled)
		self.assertEqual(payload, expected_payload)
		execute_kwargs = execute_mock.call_args.kwargs
		self.assertEqual(str(execute_kwargs.get("message") or "").strip(), "show me Top Customers by Revenue")
		self.assertEqual(int(execute_kwargs.get("governed_target_limit") or 0), 10)
		handle_kwargs = handle_result_mock.call_args.kwargs
		self.assertEqual(handle_kwargs.get("result"), compiled_result)
		self.assertEqual(
			str(getattr(handle_kwargs.get("execution_path"), "path", "") or "").strip(),
			"prior_branch_restore_requery",
		)
		appended_payloads = [
			call.args[1]
			for call in append_tool_payload_mock.call_args_list
			if len(call.args) >= 2 and isinstance(call.args[1], dict)
		]
		self.assertTrue(
			any(
				str(payload.get("type") or "").strip() == "qwen_compound_request_assessment_contract"
				and str(payload.get("status") or "").strip() == "ordered_execution_complete"
				for payload in appended_payloads
			),
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

	def test_all_h3_live_smokes_are_registered_in_live_suite(self):
		service_path = Path(__file__).resolve().parents[1] / "qwen_chat" / "service.py"
		live_suite_path = Path(__file__).resolve().parent / "test_post_contract_state_live.py"

		service_names = {
			line.split("def ", 1)[1].split("(", 1)[0].strip()
			for line in service_path.read_text().splitlines()
			if line.startswith("def run_h3_")
		}
		live_suite_text = live_suite_path.read_text()
		missing = sorted(name for name in service_names if name not in live_suite_text)

		self.assertEqual(missing, [])

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

		self.assertEqual(
			int(pending.get("source_tool_index")) if pending.get("source_tool_index") is not None else -1,
			0,
		)
		self.assertEqual(
			int(grounded.get("source_tool_index")) if grounded.get("source_tool_index") is not None else -1,
			1,
		)
		self.assertEqual(
			int(recent_focus.get("source_tool_index")) if recent_focus.get("source_tool_index") is not None else -1,
			2,
		)

	def test_conversation_state_snapshot_recent_focus_uses_latest_branch_contributor_source_tool_index(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-recency-branch-1",
			"trace_request_id": "grounded-recency-branch-1-trace",
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
			"request_id": "grounded-recency-branch-1-trace",
			"family_id": "entity_detail",
			"source_reports": ["Ko Nay Lin Mobile Center Detail"],
			"artifact_type": "normalized_family_artifact",
			"dimensions": {
				"entity_type": "customer",
				"entity_label": "Ko Nay Lin Mobile Center",
				"entity_key": "Ko Nay Lin Mobile Center",
			},
		}
		matching_recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-recency-branch-1",
			session_id="phase8a",
			source_request_id="grounded-recency-branch-1-trace",
			source_family_id="entity_detail",
			source_capability_id="customer_detail_read",
			source_report="Customer Detail",
			recovery_state="recoverable",
			available_recovery_actions=["requery_same_scope"],
			recommended_recovery_action="requery_same_scope",
			allowed_to_recover=True,
			confidence=0.91,
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(matching_artifact_payload)),
				_FakeMessage(role="tool", content=json.dumps(matching_recovery_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-recency-branch-1",
			session_doc=session_doc,
		)
		latest_artifact = snapshot.get("latest_artifact") or {}
		latest_recovery = snapshot.get("latest_recovery_contract") or {}
		recent_focus = snapshot.get("recent_focus") or {}

		self.assertEqual(
			int(latest_artifact.get("source_tool_index")) if latest_artifact.get("source_tool_index") is not None else -1,
			1,
		)
		self.assertEqual(
			int(latest_recovery.get("source_tool_index")) if latest_recovery.get("source_tool_index") is not None else -1,
			2,
		)
		self.assertEqual(
			int(recent_focus.get("source_tool_index")) if recent_focus.get("source_tool_index") is not None else -1,
			2,
		)
		self.assertEqual(str(recent_focus.get("source_capability") or "").strip(), "customer_detail_read")

	def test_question_restore_prefers_recent_focus_when_branch_contributor_is_newer_than_pending_clarification(self):
		pending_signal = _clarification_signal(
			request_id="clarify-recency-branch-2",
			user_question="Which customer do you mean?",
		)
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-recency-branch-2",
			"trace_request_id": "grounded-recency-branch-2-trace",
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
			"request_id": "grounded-recency-branch-2-trace",
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
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(pending_signal)),
				_FakeMessage(role="tool", content=json.dumps(matching_artifact_payload)),
			]
		)
		store_pending_clarification_signal(session_doc, pending_signal, attempt_count=0, max_attempts=3)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-recency-branch-2",
			session_doc=session_doc,
		)
		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-recency-branch-2",
			raw_message="answer the last question",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-recency-branch-2",
				raw_message="answer the last question",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"newer_recent_focus_precedes_older_pending_clarification",
		)

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
		self.assertEqual(
			int(active_sequence.get("source_tool_index")) if active_sequence.get("source_tool_index") is not None else -1,
			0,
		)
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
		self.assertTrue(bool(payload.get("listing_supported")))
		self.assertTrue(bool(payload.get("detail_supported")))
		self.assertEqual(str(payload.get("listing_detail_support_status") or "").strip(), "both")
		self.assertTrue(bool(payload.get("deictic_reference_allowed")))

	def test_recent_focus_affordance_builder_for_purchase_order_document_detail(self):
		contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-document-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "document",
				"focus_grain": "purchase_order",
				"focus_label": "PUR-ORD-2026-00004",
				"focus_key": "PUR-ORD-2026-00004",
				"source_request_id": "purchase-order-detail-1",
				"source_family": "entity_detail",
				"source_capability": "purchase_order_read",
				"source_report": "Purchase Order Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("focus_kind") or "").strip(), "document")
		self.assertEqual(str(payload.get("focus_grain") or "").strip(), "purchase_order")
		self.assertIn("detail_followup", list(payload.get("allowed_action_classes") or []))
		self.assertIn("linked_document_navigation", list(payload.get("allowed_action_classes") or []))
		self.assertIn("document_status_followup", list(payload.get("allowed_action_classes") or []))
		self.assertIn("document_event_followup", list(payload.get("allowed_action_classes") or []))
		self.assertTrue(bool(payload.get("listing_supported")))
		self.assertTrue(bool(payload.get("detail_supported")))
		self.assertEqual(str(payload.get("listing_detail_support_status") or "").strip(), "both")
		self.assertTrue(bool(payload.get("deictic_reference_allowed")))

	def test_recent_focus_affordance_builder_marks_listing_only_when_detail_not_supported(self):
		original_runtime_policy = recent_focus_support_module.governed_scope_runtime_policy

		def _runtime_policy(scope_id, family_id):
			if str(family_id or "").strip() == "entity_detail":
				return {}
			return original_runtime_policy(scope_id, family_id)

		with patch.object(recent_focus_support_module, "governed_scope_runtime_policy", side_effect=_runtime_policy):
			contract = recent_focus_support_module.build_recent_focus_affordance_contract_from_snapshot(
				request_id="recent-focus-affordance-listing-only-1",
				recent_focus_state={
					"available": True,
					"focus_kind": "listing",
					"focus_grain": "payment_entry",
					"focus_label": "Payment Entry List",
					"focus_key": "payment_entry",
					"source_request_id": "payment-entry-listing-1",
					"source_family": "transaction_listing",
					"source_capability": "payment_entry_list",
					"source_report": "Payment Entry List",
					"deictic_allowed": True,
					"explicit_named_allowed": False,
				},
			)
		payload = contract.to_payload()

		self.assertTrue(bool(payload.get("listing_supported")))
		self.assertFalse(bool(payload.get("detail_supported")))
		self.assertEqual(str(payload.get("listing_detail_support_status") or "").strip(), "listing_only")
		self.assertNotIn("document_selection_followup", list(payload.get("allowed_action_classes") or []))
		self.assertNotIn("entity_selection_followup", list(payload.get("allowed_action_classes") or []))

	def _assert_listing_focus_selection_contract(self, affordance_payload, expected_selection_action, msg=""):
		allowed_action_classes = list(affordance_payload.get("allowed_action_classes") or [])
		self.assertTrue(bool(affordance_payload.get("listing_supported")), msg=msg)
		detail_supported = bool(affordance_payload.get("detail_supported"))
		status = str(affordance_payload.get("listing_detail_support_status") or "").strip()
		if detail_supported:
			self.assertEqual(status, "both", msg=msg)
			self.assertIn(expected_selection_action, allowed_action_classes, msg=msg)
			return
		self.assertEqual(status, "listing_only", msg=msg)
		self.assertNotIn("document_selection_followup", allowed_action_classes, msg=msg)
		self.assertNotIn("entity_selection_followup", allowed_action_classes, msg=msg)

	def test_compile_recent_focus_runtime_message_uses_local_transform_for_entity_detail(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-entity-1",
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-entity-1",
			raw_message="how many stocks do we have, and in which warehouse?",
			followup_resolution=followup_resolution,
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
			grounded_turn={"artifact_family_id": "entity_detail"},
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "item",
					"entity_label": "Type-C Cable 1m Fast Charge",
					"entity_key": "ACC-CBL-BAS-TC1M",
				},
			},
		)

		self.assertEqual(
			runtime_message,
			'how many stocks do we have, and in which warehouse for item "Type-C Cable 1m Fast Charge"?',
		)
		self.assertEqual(routing_basis, "local_transform")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "entity")

	def test_compile_recent_focus_runtime_message_uses_local_transform_for_document_detail(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-document-1",
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-document-1",
			raw_message="when was it delivered?",
			followup_resolution=followup_resolution,
			recent_focus_state={
				"available": True,
				"focus_kind": "document",
				"focus_grain": "sales_invoice",
				"focus_label": "ACC-SINV-2026-00194",
				"focus_key": "ACC-SINV-2026-00194",
				"source_request_id": "sales-invoice-detail-1",
				"source_family": "entity_detail",
				"source_capability": "sales_invoice_read",
				"source_report": "Sales Invoice Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
			grounded_turn={"artifact_family_id": "entity_detail"},
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "sales_invoice",
					"entity_label": "ACC-SINV-2026-00194",
					"entity_key": "ACC-SINV-2026-00194",
				},
			},
		)

		self.assertEqual(
			runtime_message,
			'when was it delivered for sales invoice "ACC-SINV-2026-00194"?',
		)
		self.assertEqual(routing_basis, "local_transform")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "document")

	def test_compile_recent_focus_runtime_message_uses_local_transform_for_purchase_order_document_detail(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-document-2",
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-document-2",
			raw_message="when was it received?",
			followup_resolution=followup_resolution,
			recent_focus_state={
				"available": True,
				"focus_kind": "document",
				"focus_grain": "purchase_order",
				"focus_label": "PUR-ORD-2026-00004",
				"focus_key": "PUR-ORD-2026-00004",
				"source_request_id": "purchase-order-detail-1",
				"source_family": "entity_detail",
				"source_capability": "purchase_order_read",
				"source_report": "Purchase Order Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
			grounded_turn={"artifact_family_id": "entity_detail"},
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "purchase_order",
					"entity_label": "PUR-ORD-2026-00004",
					"entity_key": "PUR-ORD-2026-00004",
				},
			},
		)

		self.assertEqual(
			runtime_message,
			'when was it received for purchase order "PUR-ORD-2026-00004"?',
		)
		self.assertEqual(routing_basis, "local_transform")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "document")

	def test_compile_recent_focus_runtime_message_uses_local_transform_for_delivery_note_document_detail(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-document-3",
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-document-3",
			raw_message="which sales order is it from?",
			followup_resolution=followup_resolution,
			recent_focus_state={
				"available": True,
				"focus_kind": "document",
				"focus_grain": "delivery_note",
				"focus_label": "MAT-DN-2026-00016",
				"focus_key": "MAT-DN-2026-00016",
				"source_request_id": "delivery-note-detail-1",
				"source_family": "entity_detail",
				"source_capability": "delivery_note_read",
				"source_report": "Delivery Note Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
			grounded_turn={"artifact_family_id": "entity_detail"},
			artifact_payload={
				"family_id": "entity_detail",
				"dimensions": {
					"entity_type": "delivery_note",
					"entity_label": "MAT-DN-2026-00016",
					"entity_key": "MAT-DN-2026-00016",
				},
			},
		)

		self.assertEqual(
			runtime_message,
			'which sales order is it from for delivery note "MAT-DN-2026-00016"?',
		)
		self.assertEqual(routing_basis, "local_transform")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "document")

	def test_compile_recent_focus_runtime_message_uses_local_transform_for_master_data_entity_focus(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-entity-2",
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-entity-2",
			raw_message="how many stocks do we have, and in which warehouse?",
			followup_resolution=followup_resolution,
			recent_focus_state={
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "item",
				"focus_label": "Type-C Cable 1m Fast Charge",
				"focus_key": "ACC-CBL-BAS-TC1M",
				"source_request_id": "item-master-single-1",
				"source_family": "master_data_directory",
				"source_capability": "item_master_read",
				"source_report": "Item Master List",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
			grounded_turn={"artifact_family_id": "master_data_directory"},
			artifact_payload={"family_id": "master_data_directory"},
		)

		self.assertEqual(
			runtime_message,
			'how many stocks do we have, and in which warehouse for item "Type-C Cable 1m Fast Charge"?',
		)
		self.assertEqual(routing_basis, "local_transform")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "entity")

	def test_compile_recent_focus_runtime_message_uses_local_transform_for_transaction_single_document_focus(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-document-4",
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-document-4",
			raw_message="when was it delivered?",
			followup_resolution=followup_resolution,
			recent_focus_state={
				"available": True,
				"focus_kind": "document",
				"focus_grain": "sales_invoice",
				"focus_label": "ACC-SINV-2026-00201",
				"focus_key": "ACC-SINV-2026-00201",
				"source_request_id": "sales-invoice-list-single-1",
				"source_family": "transaction_listing",
				"source_capability": "sales_invoice_read",
				"source_report": "Sales Invoice List",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
			grounded_turn={"artifact_family_id": "transaction_listing"},
			artifact_payload={"family_id": "transaction_listing"},
		)

		self.assertEqual(
			runtime_message,
			'when was it delivered for sales invoice "ACC-SINV-2026-00201"?',
		)
		self.assertEqual(routing_basis, "local_transform")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "document")

	def test_compile_recent_focus_runtime_message_uses_local_transform_for_transaction_single_document_grounded_follow_up(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-document-4b",
			mode="grounded_follow_up",
			requested_modes=[],
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-document-4b",
			raw_message="tell me more about that purchase order",
			followup_resolution=followup_resolution,
			recent_focus_state={
				"available": True,
				"focus_kind": "document",
				"focus_grain": "purchase_order",
				"focus_label": "PUR-ORD-2026-00004",
				"focus_key": "PUR-ORD-2026-00004",
				"source_request_id": "purchase-order-list-single-1",
				"source_family": "transaction_listing",
				"source_capability": "purchase_order_read",
				"source_report": "Purchase Order List",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
			grounded_turn={"artifact_family_id": "transaction_listing"},
			artifact_payload={"family_id": "transaction_listing"},
		)

		self.assertEqual(
			runtime_message,
			"show me details for purchase order PUR-ORD-2026-00004",
		)
		self.assertEqual(routing_basis, "local_transform")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "document")

	def test_base_transaction_listing_reask_ignores_contextual_detail_followup(self):
		self.assertFalse(
			_looks_like_base_transaction_listing_reask(
				message="tell me more about that purchase order",
				latest_grounded_turn={
					"artifact_family_id": "transaction_listing",
					"source_name": "Purchase Order List",
				},
				requested_time_scope="",
			)
		)

	def test_grounded_turn_has_single_row_contextual_focus_for_transaction_listing(self):
		self.assertTrue(
			_grounded_turn_has_single_row_contextual_focus(
				{
					"artifact_family_id": "transaction_listing",
					"source_name": "Purchase Order List",
					"row_count": 1,
					"table_rows": [{"Purchase Order": "PUR-ORD-2026-00004"}],
				}
			)
		)

	def test_grounded_turn_has_single_row_contextual_focus_for_master_data_listing(self):
		self.assertTrue(
			_grounded_turn_has_single_row_contextual_focus(
				{
					"artifact_family_id": "master_data_directory",
					"source_name": "Supplier Master List",
					"row_count": 1,
					"table_rows": [{"Supplier Name": "Myanmar Tech Import Services"}],
				}
			)
		)

	def test_grounded_turn_has_single_row_contextual_focus_for_customer_master_listing(self):
		self.assertTrue(
			_grounded_turn_has_single_row_contextual_focus(
				{
					"artifact_family_id": "customer_master_list",
					"table_rows": [{"customer_name": "Ko Nay Lin Mobile Center"}],
				}
			)
		)

	def test_build_followup_resolution_keeps_contextual_transaction_document_detail_grounded(self):
		followup_resolution = build_followup_resolution(
			request_id="followup-resolution-transaction-document-1",
			message="tell me more about that purchase order",
			latest_grounded_turn_available=True,
			latest_grounded_turn={
				"artifact_family_id": "transaction_listing",
				"source_name": "Purchase Order List",
				"row_count": 1,
				"table_rows": [{"Purchase Order": "PUR-ORD-2026-00004"}],
				"date_range": {"from_date": "2026-01-15", "to_date": "2026-01-15"},
				"filters": {
					"company": "Mingalar Mobile Distribution Co., Ltd.",
					"purchase_order": "PUR-ORD-2026-00004",
				},
			},
			semantic_intent=types.SimpleNamespace(
				requested_modes=["column_projection"],
				target_dimension="Purchase Order",
				target_limit=1,
				sort_direction="",
				target_metric="grand total",
				requested_columns=["transaction date", "supplier", "grand total", "quantity", "status"],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
				reason="User asked for more details about the purchase order, so a column projection is appropriate.",
			),
		)

		self.assertEqual(str(followup_resolution.mode or "").strip(), "grounded_follow_up")
		self.assertEqual(list(followup_resolution.requested_modes or []), ["detail_followup"])
		self.assertTrue(bool(followup_resolution.depends_on_grounded_turn))
		self.assertFalse(bool(followup_resolution.self_contained))

	def test_build_followup_resolution_normalizes_runtime_followup_mode_aliases(self):
		followup_resolution = build_followup_resolution(
			request_id="followup-resolution-mode-normalization-1",
			message="show supplier name and payment terms only",
			latest_grounded_turn_available=False,
			latest_grounded_turn=None,
			semantic_intent=types.SimpleNamespace(
				requested_modes=["column_projection", "metric_change"],
				target_dimension="",
				target_limit=0,
				sort_direction="",
				target_metric="outstanding",
				requested_columns=["supplier name", "payment terms"],
				requested_time_scope="",
				target_capability_id="",
				self_contained=False,
				reason="The request narrows the displayed fields and metric.",
			),
		)

		self.assertEqual(
			list(followup_resolution.requested_modes or []),
			["column_refinement", "metric_refinement"],
		)

	def test_compile_recent_focus_runtime_message_uses_shared_affordance_for_master_data_listing(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-list-1",
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-list-1",
			raw_message="show supplier name and payment terms only",
			followup_resolution=followup_resolution,
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "supplier",
				"focus_label": "Supplier Master List",
				"focus_key": "supplier",
				"source_request_id": "supplier-list-1",
				"source_family": "master_data_directory",
				"source_capability": "supplier_master_read",
				"source_report": "Supplier Master List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
			grounded_turn={"artifact_family_id": "master_data_directory"},
			artifact_payload={"family_id": "master_data_directory"},
		)

		self.assertEqual(runtime_message, "show supplier name and payment terms only")
		self.assertEqual(routing_basis, "shared_affordance")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing")

	def test_compile_recent_focus_runtime_message_uses_local_transform_for_detail_capable_master_data_listing(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-listing-detail-1",
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-listing-detail-1",
			raw_message="tell me more about that supplier",
			followup_resolution=followup_resolution,
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "supplier",
				"focus_label": "Supplier Master List",
				"focus_key": "supplier",
				"source_request_id": "supplier-list-2",
				"source_family": "master_data_directory",
				"source_capability": "supplier_master_read",
				"source_report": "Supplier Master List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
			grounded_turn={
				"artifact_family_id": "master_data_directory",
				"known_entities": [
					{
						"entity_type": "supplier",
						"name": "Myanmar Tech Import Services",
						"code": "Myanmar Tech Import Services",
					}
				],
			},
			artifact_payload={"family_id": "master_data_directory"},
		)

		self.assertEqual(runtime_message, "show me details for supplier Myanmar Tech Import Services")
		self.assertEqual(routing_basis, "local_transform")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing")
		self.assertTrue(bool(getattr(affordance_contract, "detail_supported", False)))

	def test_compile_recent_focus_runtime_message_keeps_listing_only_scope_on_shared_affordance(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-listing-only-1",
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-listing-only-1",
			raw_message="tell me more about that payment entry",
			followup_resolution=followup_resolution,
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "payment_entry",
				"focus_label": "Payment Entry List",
				"focus_key": "payment_entry",
				"source_request_id": "payment-entry-list-2",
				"source_family": "transaction_listing",
				"source_capability": "payment_entry_read",
				"source_report": "Payment Entry List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
			grounded_turn={
				"artifact_family_id": "transaction_listing",
				"known_entities": [
					{
						"entity_type": "payment_entry",
						"name": "ACC-PAY-2026-00179",
						"code": "ACC-PAY-2026-00179",
					}
				],
			},
			artifact_payload={"family_id": "transaction_listing"},
		)

		self.assertEqual(runtime_message, "tell me more about that payment entry")
		self.assertEqual(routing_basis, "shared_affordance")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing")
		self.assertFalse(bool(getattr(affordance_contract, "detail_supported", False)))

	def test_recent_focus_affordance_normalizes_registry_column_projection_for_listing(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-listing-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "supplier",
				"focus_label": "Supplier Master List",
				"focus_key": "supplier",
				"source_request_id": "supplier-list-1",
				"source_family": "master_data_directory",
				"source_capability": "supplier_master_read",
				"source_report": "Supplier Master List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
		)

		self.assertIsNotNone(affordance_contract)
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertNotIn("column_projection", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_normalizes_registry_metric_change_for_report(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-report-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "ranking_analytics",
				"focus_label": "Gross Profit",
				"focus_key": "Gross Profit",
				"source_request_id": "gross-profit-1",
				"source_family": "ranking_analytics",
				"source_capability": "product_performance_read",
				"source_report": "Gross Profit",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)

		self.assertIsNotNone(affordance_contract)
		self.assertIn("metric_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertNotIn("metric_change", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("grouping_change", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_statement_recent_focus_descriptor_uses_metadata_family(self):
		with patch.object(
			recent_focus_support_module,
			"report_business_family_ids",
			return_value=["financial_statement"],
		), patch.object(
			recent_focus_support_module,
			"get_report_spec",
			return_value={"family": "owner_profit_statement"},
		):
			descriptor = recent_focus_support_module.statement_recent_focus_descriptor_for_report_name(
				"Owner Profit Statement"
			)

		self.assertEqual(descriptor.get("focus_kind"), "statement")
		self.assertEqual(descriptor.get("focus_grain"), "owner_profit")
		self.assertEqual(descriptor.get("focus_label"), "Owner Profit Statement")
		self.assertEqual(descriptor.get("focus_key"), "Owner Profit Statement")

	def test_snapshot_recent_focus_uses_metadata_statement_descriptor_helper(self):
		with patch(
			"ai_assistant_ui.qwen_chat.service._grounded_recent_focus_surface_descriptor_helper",
			return_value={
				"surface_class": "statement",
				"focus_kind": "statement",
				"focus_grain": "owner_profit",
				"focus_label": "Owner Profit Statement",
				"focus_key": "Owner Profit Statement",
				"source_family_default": "financial_statement",
				"derivation_basis": "statement_grounded_turn",
			},
		):
			recent_focus = _snapshot_recent_focus_state(
				latest_grounded_turn={
					"payload": {
						"request_id": "owner-statement-1",
						"source_kind": "report",
						"source_name": "Owner Profit Statement",
						"artifact_family_id": "owner_financials",
					},
				},
				latest_artifact={
					"payload": {
						"type": "qwen_normalized_family_artifact_contract",
						"request_id": "owner-statement-1-trace",
						"family_id": "owner_financials",
						"dimensions": {},
					},
					"grounded_compatible": True,
				},
				latest_recovery_contract={},
			)

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "statement")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "owner_profit")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "Owner Profit Statement")
		self.assertEqual(str(recent_focus.get("focus_key") or "").strip(), "Owner Profit Statement")
		self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "owner_financials")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "statement_grounded_turn")

	def test_recent_focus_affordance_uses_governed_followup_policy_for_accounts_receivable_summary(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-ar-summary-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "accounts_receivable_summary",
				"focus_label": "Accounts Receivable Summary",
				"focus_key": "Accounts Receivable Summary",
				"source_request_id": "ar-summary-1",
				"source_family": "aging",
				"source_capability": "accounts_receivable_read",
				"source_report": "Accounts Receivable Summary",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "report")
		self.assertIn("report_refinement", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("dimension_breakdown", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("aging_bucket_view", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("sibling_switch", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_accounts_receivable(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-ar-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "aging",
				"focus_label": "Accounts Receivable",
				"focus_key": "Accounts Receivable",
				"source_request_id": "ar-1",
				"source_family": "aging",
				"source_capability": "accounts_receivable_read",
				"source_report": "Accounts Receivable",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "report")
		self.assertIn("report_refinement", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("dimension_breakdown", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("aging_bucket_view", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("sibling_switch", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_accounts_payable_summary(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-ap-summary-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "accounts_payable_summary",
				"focus_label": "Accounts Payable Summary",
				"focus_key": "Accounts Payable Summary",
				"source_request_id": "ap-summary-1",
				"source_family": "aging",
				"source_capability": "accounts_payable_read",
				"source_report": "Accounts Payable Summary",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "report")
		self.assertIn("report_refinement", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("dimension_breakdown", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("aging_bucket_view", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("sibling_switch", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_accounts_payable(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-ap-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "aging",
				"focus_label": "Accounts Payable",
				"focus_key": "Accounts Payable",
				"source_request_id": "ap-1",
				"source_family": "aging",
				"source_capability": "accounts_payable_read",
				"source_report": "Accounts Payable",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "report")
		self.assertIn("report_refinement", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("dimension_breakdown", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("aging_bucket_view", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("sibling_switch", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_stock_balance(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-stock-balance-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "inventory_snapshot",
				"focus_label": "Stock Balance",
				"focus_key": "Stock Balance",
				"source_request_id": "stock-balance-1",
				"source_family": "inventory_snapshot",
				"source_capability": "stock_read",
				"source_report": "Stock Balance",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "report")
		self.assertIn("report_refinement", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("grouping_change", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_warehouse_wise_stock_balance(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-warehouse-stock-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "inventory_snapshot",
				"focus_label": "Warehouse Wise Stock Balance",
				"focus_key": "Warehouse Wise Stock Balance",
				"source_request_id": "warehouse-stock-1",
				"source_family": "inventory_snapshot",
				"source_capability": "stock_read",
				"source_report": "Warehouse Wise Stock Balance",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "report")
		self.assertIn("report_refinement", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("grouping_change", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_delivery_note_trends(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-delivery-trends-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "trend_analytics",
				"focus_label": "Delivery Note Trends",
				"focus_key": "Delivery Note Trends",
				"source_request_id": "delivery-trends-1",
				"source_family": "trend_analytics",
				"source_capability": "fulfillment_read",
				"source_report": "Delivery Note Trends",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "report")
		self.assertIn("report_refinement", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("metric_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertNotIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_sales_analytics(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-sales-analytics-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "sales_analytics",
				"focus_label": "Sales Analytics",
				"focus_key": "Sales Analytics",
				"source_request_id": "sales-analytics-1",
				"source_family": "trend_analytics",
				"source_capability": "sales_read",
				"source_report": "Sales Analytics",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "report")
		self.assertIn("report_refinement", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("grouping_change", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("metric_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_item_wise_sales_history(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-item-sales-history-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "product_performance",
				"focus_label": "Item-wise Sales History",
				"focus_key": "Item-wise Sales History",
				"source_request_id": "item-sales-history-1",
				"source_family": "product_performance",
				"source_capability": "product_performance_read",
				"source_report": "Item-wise Sales History",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "report")
		self.assertIn("report_refinement", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertNotIn("metric_refinement", list(affordance_contract.allowed_local_followup_modes or []))

	def test_recent_focus_affordance_falls_back_to_new_query_only_for_sales_order_item_list(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-sales-order-item-list-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "sales_order_item_list",
				"focus_label": "Sales Order Item List",
				"focus_key": "Sales Order Item List",
				"source_request_id": "sales-order-item-list-1",
				"source_family": "sales_order_item_list",
				"source_capability": "sales_order_read",
				"source_report": "Sales Order Item List",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "report")
		self.assertEqual(list(affordance_contract.allowed_local_followup_modes or []), [])
		self.assertEqual(list(affordance_contract.allowed_requery_followup_modes or []), ["new_query"])

	def test_recent_focus_affordance_falls_back_to_new_query_only_for_sales_invoice_item_list(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-sales-invoice-item-list-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "sales_invoice_item_list",
				"focus_label": "Sales Invoice Item List",
				"focus_key": "Sales Invoice Item List",
				"source_request_id": "sales-invoice-item-list-1",
				"source_family": "sales_invoice_item_list",
				"source_capability": "sales_read",
				"source_report": "Sales Invoice Item List",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "report")
		self.assertEqual(list(affordance_contract.allowed_local_followup_modes or []), [])
		self.assertEqual(list(affordance_contract.allowed_requery_followup_modes or []), ["new_query"])

	def test_recent_focus_affordance_matrix_covers_active_approved_report_surface(self):
		report_specs = [
			dict(item)
			for item in (load_report_registry().get("reports") or [])
			if isinstance(item, dict)
			and list(report_approved_followup_modes(str(item.get("report_name") or "").strip()))
		]
		self.assertTrue(bool(report_specs))
		for index, report_spec in enumerate(report_specs, start=1):
			report_name = str(report_spec.get("report_name") or "").strip()
			supported_families = [
				value for value in report_business_family_ids(report_name) if str(value or "").strip()
			]
			statement_descriptor = recent_focus_support_module.statement_recent_focus_descriptor_for_report_name(
				report_name
			)
			if statement_descriptor:
				recent_focus_state = {
					"available": True,
					"focus_kind": str(statement_descriptor.get("focus_kind") or "").strip(),
					"focus_grain": str(statement_descriptor.get("focus_grain") or "").strip(),
					"focus_label": str(statement_descriptor.get("focus_label") or "").strip(),
					"focus_key": str(statement_descriptor.get("focus_key") or "").strip(),
					"source_request_id": f"report-matrix-{index}",
					"source_family": str((supported_families or ["financial_statement"])[0] or "").strip(),
					"source_capability": "",
					"source_report": report_name,
					"deictic_allowed": False,
					"explicit_named_allowed": True,
				}
			else:
				recent_focus_state = {
					"available": True,
					"focus_kind": "report",
					"focus_grain": str(
						(supported_families or [report_spec.get("family") or report_name.lower().replace(" ", "_")])[0]
						or ""
					).strip(),
					"focus_label": report_name,
					"focus_key": report_name,
					"source_request_id": f"report-matrix-{index}",
					"source_family": str((supported_families or [report_spec.get("family") or "report"])[0] or "").strip(),
					"source_capability": "",
					"source_report": report_name,
					"deictic_allowed": True,
					"explicit_named_allowed": True,
				}

			affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
				request_id=f"report-matrix-{index}",
				recent_focus_state=recent_focus_state,
			)

			self.assertIsNotNone(affordance_contract, msg=report_name)
			all_modes = list(affordance_contract.allowed_local_followup_modes or []) + list(
				affordance_contract.allowed_requery_followup_modes or []
			)
			self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []), msg=report_name)
			self.assertNotIn("column_projection", all_modes, msg=report_name)
			self.assertNotIn("metric_change", all_modes, msg=report_name)
			for approved_mode in report_approved_followup_modes(report_name):
				normalized_mode = recent_focus_support_module._normalize_policy_followup_mode(
					str(approved_mode or "").strip()
				)
				if normalized_mode:
					self.assertIn(normalized_mode, all_modes, msg=f"{report_name}: {approved_mode}")

	def test_recent_focus_affordance_uses_governed_followup_policy_for_transaction_listing(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-payment-list-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "payment_entry",
				"focus_label": "Payment Entry List",
				"source_family": "transaction_listing",
				"source_capability": "payment_entry_read",
				"source_report": "Payment Entry List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing")
		self._assert_listing_focus_selection_contract(
			affordance_contract.to_payload(),
			"document_selection_followup",
		)
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("time_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_master_data_listing(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-supplier-list-2",
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "supplier",
				"focus_label": "Supplier Master List",
				"source_family": "unclassified_listing_runtime",
				"source_capability": "supplier_master_read",
				"source_report": "Supplier Master List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
		)

		self.assertIn("entity_selection_followup", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_matrix_covers_active_approved_listing_scope_surface(self):
		scopes = [
			dict(item)
			for item in (governed_scope_registry_module.load_governed_scope_registry().get("scopes") or [])
			if isinstance(item, dict)
		]
		active_listing_scopes = []
		for scope in scopes:
			authority = (
				scope.get("approved_source_authority")
				if isinstance(scope.get("approved_source_authority"), dict)
				else {}
			)
			report_name = str(authority.get("report_name") or "").strip()
			if str(scope.get("status") or "").strip() != "active":
				continue
			if str(authority.get("authority_status") or "").strip() != "approved":
				continue
			if str(authority.get("source_kind") or "").strip() != "report":
				continue
			if not report_name.endswith("List"):
				continue
			active_listing_scopes.append(scope)

		self.assertTrue(bool(active_listing_scopes))
		for index, scope in enumerate(active_listing_scopes, start=1):
			scope_id = str(scope.get("scope_id") or "").strip()
			scope_class = str(scope.get("scope_class") or "").strip()
			authority = (
				scope.get("approved_source_authority")
				if isinstance(scope.get("approved_source_authority"), dict)
				else {}
			)
			report_name = str(authority.get("report_name") or "").strip()
			canonical_grains = [
				str(value or "").strip()
				for value in (scope.get("canonical_grains") or [])
				if str(value or "").strip()
			]
			if scope_class == "master_data":
				focus_grain = str((canonical_grains or [scope_id])[0] or "").strip()
				source_family = "master_data_directory"
				expected_selection_action = "entity_selection_followup"
			else:
				focus_grain = scope_id
				source_family = "transaction_listing"
				expected_selection_action = "document_selection_followup"

			affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
				request_id=f"listing-scope-matrix-{index}",
				recent_focus_state={
					"available": True,
					"focus_kind": "listing",
					"focus_grain": focus_grain,
					"focus_label": report_name,
					"focus_key": focus_grain or report_name,
					"source_request_id": f"listing-scope-matrix-{index}",
					"source_family": source_family,
					"source_capability": str(authority.get("capability_id") or "").strip(),
					"source_report": report_name,
					"deictic_allowed": True,
					"explicit_named_allowed": False,
				},
			)

			self.assertIsNotNone(affordance_contract, msg=report_name)
			self.assertEqual(
				governed_scope_registry_module.scope_id_for_report_name(report_name),
				scope_id,
				msg=report_name,
			)
			self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing", msg=report_name)
			self._assert_listing_focus_selection_contract(
				affordance_contract.to_payload(),
				expected_selection_action,
				msg=report_name,
			)
			self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []), msg=report_name)
			self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []), msg=report_name)
			self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []), msg=report_name)
			self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []), msg=report_name)
			self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []), msg=report_name)

	def test_scope_id_for_listing_view_falls_back_to_active_governed_scope_identity(self):
		with patch.dict(governed_scope_registry_module._LISTING_VIEW_SCOPE_MAP, {}, clear=True):
			with patch.object(
				governed_scope_registry_module,
				"governed_scope_spec",
				return_value={
					"scope_id": "future_transaction_listing",
					"status": "active",
					"approved_source_authority": {
						"authority_status": "approved",
						"source_kind": "report",
						"report_name": "Future Transaction Listing",
					},
				},
			):
				self.assertEqual(
					governed_scope_registry_module.scope_id_for_listing_view("future_transaction_listing"),
					"future_transaction_listing",
				)

	def test_recent_focus_affordance_uses_governed_followup_policy_for_item_master_listing(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-item-list-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "item",
				"focus_label": "Item Master List",
				"source_family": "master_data_directory",
				"source_capability": "item_master_read",
				"source_report": "Item Master List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing")
		self.assertIn("entity_selection_followup", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_customer_master_listing(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-customer-list-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "customer",
				"focus_label": "Customer Master List",
				"source_family": "master_data_directory",
				"source_capability": "customer_master_read",
				"source_report": "Customer Master List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing")
		self.assertIn("entity_selection_followup", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_sales_order_listing(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-sales-order-list-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "sales_order",
				"focus_label": "Sales Order List",
				"source_family": "transaction_listing",
				"source_capability": "sales_order_read",
				"source_report": "Sales Order List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing")
		self.assertIn("document_selection_followup", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("time_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_sales_invoice_listing(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-sales-invoice-list-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "sales_invoice",
				"focus_label": "Sales Invoice List",
				"source_family": "transaction_listing",
				"source_capability": "sales_invoice_read",
				"source_report": "Sales Invoice List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing")
		self.assertIn("document_selection_followup", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("time_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_delivery_note_listing(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-delivery-note-list-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "delivery_note",
				"focus_label": "Delivery Note List",
				"source_family": "transaction_listing",
				"source_capability": "delivery_note_read",
				"source_report": "Delivery Note List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing")
		self.assertIn("document_selection_followup", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("time_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_purchase_order_listing(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-purchase-order-list-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "purchase_order",
				"focus_label": "Purchase Order List",
				"source_family": "transaction_listing",
				"source_capability": "purchase_order_read",
				"source_report": "Purchase Order List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing")
		self.assertIn("document_selection_followup", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("time_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_recent_focus_affordance_uses_governed_followup_policy_for_purchase_invoice_listing(self):
		affordance_contract = _build_recent_focus_affordance_contract_from_snapshot(
			request_id="recent-focus-affordance-purchase-invoice-list-1",
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "purchase_invoice",
				"focus_label": "Purchase Invoice List",
				"source_family": "transaction_listing",
				"source_capability": "purchase_invoice_read",
				"source_report": "Purchase Invoice List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
		)

		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing")
		self.assertIn("document_selection_followup", list(affordance_contract.allowed_action_classes or []))
		self.assertIn("column_refinement", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("sort_or_limit", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("presentation_transform", list(affordance_contract.allowed_local_followup_modes or []))
		self.assertIn("filter_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("time_refinement", list(affordance_contract.allowed_requery_followup_modes or []))
		self.assertIn("new_query", list(affordance_contract.allowed_requery_followup_modes or []))

	def test_compile_recent_focus_runtime_message_uses_shared_affordance_for_transaction_listing_detail_followup(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-list-2",
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-list-2",
			raw_message="tell me more about ACC-SINV-2026-00201",
			followup_resolution=followup_resolution,
			recent_focus_state={
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "sales_invoice",
				"focus_label": "Sales Invoice List",
				"focus_key": "sales_invoice",
				"source_request_id": "sales-invoice-list-1",
				"source_family": "transaction_listing",
				"source_capability": "sales_invoice_read",
				"source_report": "Sales Invoice List",
				"deictic_allowed": True,
				"explicit_named_allowed": False,
			},
			grounded_turn={"artifact_family_id": "transaction_listing"},
			artifact_payload={"family_id": "transaction_listing"},
		)

		self.assertEqual(runtime_message, "tell me more about ACC-SINV-2026-00201")
		self.assertEqual(routing_basis, "shared_affordance")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "listing")

	def test_compile_recent_focus_runtime_message_uses_shared_affordance_for_statement_switch(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-statement-1",
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-statement-1",
			raw_message="show me balance sheet",
			followup_resolution=followup_resolution,
			recent_focus_state={
				"available": True,
				"focus_kind": "statement",
				"focus_grain": "profit_and_loss",
				"focus_label": "Profit and Loss Statement",
				"focus_key": "Profit and Loss Statement",
				"source_request_id": "statement-1",
				"source_family": "financial_statement",
				"source_capability": "financial_statement_read",
				"source_report": "Profit and Loss Statement",
				"deictic_allowed": False,
				"explicit_named_allowed": True,
			},
			grounded_turn={"artifact_family_id": "financial_statement"},
			artifact_payload={"family_id": "financial_statement"},
		)

		self.assertEqual(runtime_message, "show me balance sheet")
		self.assertEqual(routing_basis, "shared_affordance")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "statement")

	def test_compile_recent_focus_runtime_message_uses_shared_affordance_for_report_detail_navigation(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="recent-focus-runtime-report-1",
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

		runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
			request_id="recent-focus-runtime-report-1",
			raw_message="tell me more about Type-C Cable 1m Fast Charge",
			followup_resolution=followup_resolution,
			recent_focus_state={
				"available": True,
				"focus_kind": "report",
				"focus_grain": "ranking_analytics",
				"focus_label": "Top Products by Revenue",
				"focus_key": "Top Products by Revenue",
				"source_request_id": "ranking-report-1",
				"source_family": "ranking_analytics",
				"source_capability": "product_performance_read",
				"source_report": "Top Products by Revenue",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
			},
			grounded_turn={"artifact_family_id": "ranking_analytics"},
			artifact_payload={"family_id": "ranking_analytics"},
		)

		self.assertEqual(runtime_message, "tell me more about Type-C Cable 1m Fast Charge")
		self.assertEqual(routing_basis, "shared_affordance")
		self.assertEqual(str(affordance_contract.focus_kind or "").strip(), "report")
		self.assertEqual(list(affordance_contract.allowed_requery_followup_modes or []), ["new_query"])
		self.assertTrue(bool(affordance_contract.supports_cross_family_followup))

	def test_conversation_state_snapshot_matrix_covers_active_approved_listing_scope_surface(self):
		scopes = [
			dict(item)
			for item in (governed_scope_registry_module.load_governed_scope_registry().get("scopes") or [])
			if isinstance(item, dict)
		]
		active_listing_scopes = []
		for scope in scopes:
			authority = (
				scope.get("approved_source_authority")
				if isinstance(scope.get("approved_source_authority"), dict)
				else {}
			)
			report_name = str(authority.get("report_name") or "").strip()
			if str(scope.get("status") or "").strip() != "active":
				continue
			if str(authority.get("authority_status") or "").strip() != "approved":
				continue
			if str(authority.get("source_kind") or "").strip() != "report":
				continue
			if not report_name.endswith("List"):
				continue
			active_listing_scopes.append(scope)

		self.assertTrue(bool(active_listing_scopes))
		for index, scope in enumerate(active_listing_scopes, start=1):
			scope_id = str(scope.get("scope_id") or "").strip()
			authority = (
				scope.get("approved_source_authority")
				if isinstance(scope.get("approved_source_authority"), dict)
				else {}
			)
			report_name = str(authority.get("report_name") or "").strip()
			canonical_grains = [
				str(value or "").strip()
				for value in (scope.get("canonical_grains") or [])
				if str(value or "").strip()
			]
			listing_view = governed_scope_registry_module.listing_view_for_report_name(report_name)
			entity_grain = governed_scope_registry_module.entity_grain_for_report_name(report_name)
			if scope_id in {"customer_master", "supplier_master", "item_master"}:
				entity_grain = entity_grain or next(
					(value for value in canonical_grains if value in {"customer", "supplier", "item", "product"}),
					"",
				)
				artifact_family_id = "master_data_directory"
				dimensions = {"entity_type": entity_grain}
				expected_focus_grain = entity_grain
				expected_basis = "master_data_listing_grounded_turn"
				expected_action_class = "entity_selection_followup"
			else:
				listing_view = listing_view or scope_id
				artifact_family_id = "transaction_listing"
				dimensions = {"listing_view": listing_view}
				expected_focus_grain = listing_view
				expected_basis = "transaction_listing_grounded_turn"
				expected_action_class = "document_selection_followup"
			session_doc = _fake_snapshot_session_for_grounded_report(
				request_id=f"snapshot-listing-matrix-{index}",
				trace_request_id=f"snapshot-listing-matrix-{index}-trace",
				report_name=report_name,
				artifact_family_id=artifact_family_id,
				dimensions=dimensions,
				table_rows=[
					{"name": f"ROW-{index:03d}-A"},
					{"name": f"ROW-{index:03d}-B"},
				],
			)

			snapshot = _build_conversation_state_snapshot(
				request_id=f"snapshot-listing-matrix-{index}",
				session_doc=session_doc,
			)
			recent_focus = snapshot.get("recent_focus") or {}
			affordance = snapshot.get("recent_focus_affordance") or {}

			self.assertTrue(bool(recent_focus.get("available")), msg=report_name)
			self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing", msg=report_name)
			self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), expected_focus_grain, msg=report_name)
			self.assertEqual(str(recent_focus.get("source_report") or "").strip(), report_name, msg=report_name)
			self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), expected_basis, msg=report_name)
			self.assertEqual(str(affordance.get("focus_kind") or "").strip(), "listing", msg=report_name)
			self._assert_listing_focus_selection_contract(
				affordance,
				expected_action_class,
				msg=report_name,
			)
			self.assertIn("new_query", list(affordance.get("allowed_requery_followup_modes") or []), msg=report_name)
			self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_recent_focus_affordance")), msg=report_name)

	def test_conversation_state_snapshot_matrix_covers_active_approved_statement_surface(self):
		report_specs = [
			dict(item)
			for item in (load_report_registry().get("reports") or [])
			if isinstance(item, dict)
			and list(report_approved_followup_modes(str(item.get("report_name") or "").strip()))
		]
		statement_report_specs = []
		for report_spec in report_specs:
			report_name = str(report_spec.get("report_name") or "").strip()
			statement_descriptor = recent_focus_support_module.statement_recent_focus_descriptor_for_report_name(
				report_name
			)
			if statement_descriptor:
				statement_report_specs.append((report_spec, statement_descriptor))

		self.assertTrue(bool(statement_report_specs))
		for index, (report_spec, statement_descriptor) in enumerate(statement_report_specs, start=1):
			report_name = str(report_spec.get("report_name") or "").strip()
			artifact_family_id = str(report_spec.get("family") or "").strip() or "financial_statement"
			session_doc = _fake_snapshot_session_for_grounded_report(
				request_id=f"snapshot-statement-matrix-{index}",
				trace_request_id=f"snapshot-statement-matrix-{index}-trace",
				report_name=report_name,
				artifact_family_id=artifact_family_id,
			)

			snapshot = _build_conversation_state_snapshot(
				request_id=f"snapshot-statement-matrix-{index}",
				session_doc=session_doc,
			)
			recent_focus = snapshot.get("recent_focus") or {}
			affordance = snapshot.get("recent_focus_affordance") or {}

			self.assertTrue(bool(recent_focus.get("available")), msg=report_name)
			self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "statement", msg=report_name)
			self.assertEqual(
				str(recent_focus.get("focus_grain") or "").strip(),
				str(statement_descriptor.get("focus_grain") or "").strip(),
				msg=report_name,
			)
			self.assertEqual(str(recent_focus.get("source_report") or "").strip(), report_name, msg=report_name)
			self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "statement_grounded_turn", msg=report_name)
			self.assertIn("statement_switch", list(affordance.get("allowed_action_classes") or []), msg=report_name)
			self.assertIn("line_item_followup", list(affordance.get("allowed_action_classes") or []), msg=report_name)
			self.assertIn("new_query", list(affordance.get("allowed_requery_followup_modes") or []), msg=report_name)
			self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_recent_focus_affordance")), msg=report_name)

	def test_conversation_state_snapshot_matrix_covers_active_approved_non_scope_report_surface(self):
		report_specs = [
			dict(item)
			for item in (load_report_registry().get("reports") or [])
			if isinstance(item, dict)
			and list(report_approved_followup_modes(str(item.get("report_name") or "").strip()))
		]
		generic_report_specs = []
		for report_spec in report_specs:
			report_name = str(report_spec.get("report_name") or "").strip()
			if not report_name:
				continue
			if recent_focus_support_module.statement_recent_focus_descriptor_for_report_name(report_name):
				continue
			if governed_scope_registry_module.scope_id_for_report_name(report_name):
				continue
			generic_report_specs.append(report_spec)

		self.assertTrue(bool(generic_report_specs))
		for index, report_spec in enumerate(generic_report_specs, start=1):
			report_name = str(report_spec.get("report_name") or "").strip()
			artifact_family_id = str(report_spec.get("family") or "").strip() or report_name.lower().replace(" ", "_")
			session_doc = _fake_snapshot_session_for_grounded_report(
				request_id=f"snapshot-report-matrix-{index}",
				trace_request_id=f"snapshot-report-matrix-{index}-trace",
				report_name=report_name,
				artifact_family_id=artifact_family_id,
			)

			snapshot = _build_conversation_state_snapshot(
				request_id=f"snapshot-report-matrix-{index}",
				session_doc=session_doc,
			)
			recent_focus = snapshot.get("recent_focus") or {}
			affordance = snapshot.get("recent_focus_affordance") or {}

			self.assertTrue(bool(recent_focus.get("available")), msg=report_name)
			self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report", msg=report_name)
			self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), artifact_family_id, msg=report_name)
			self.assertEqual(str(recent_focus.get("source_report") or "").strip(), report_name, msg=report_name)
			self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn", msg=report_name)
			self.assertEqual(str(affordance.get("focus_kind") or "").strip(), "report", msg=report_name)
			self.assertIn("new_query", list(affordance.get("allowed_requery_followup_modes") or []), msg=report_name)
			self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_recent_focus_affordance")), msg=report_name)

	def test_conversation_state_snapshot_matrix_covers_active_approved_single_row_listing_promotion_surface(self):
		scopes = [
			dict(item)
			for item in (governed_scope_registry_module.load_governed_scope_registry().get("scopes") or [])
			if isinstance(item, dict)
		]
		active_listing_scopes = []
		for scope in scopes:
			authority = (
				scope.get("approved_source_authority")
				if isinstance(scope.get("approved_source_authority"), dict)
				else {}
			)
			report_name = str(authority.get("report_name") or "").strip()
			if str(scope.get("status") or "").strip() != "active":
				continue
			if str(authority.get("authority_status") or "").strip() != "approved":
				continue
			if str(authority.get("source_kind") or "").strip() != "report":
				continue
			if not report_name.endswith("List"):
				continue
			active_listing_scopes.append(scope)

		self.assertTrue(bool(active_listing_scopes))
		for index, scope in enumerate(active_listing_scopes, start=1):
			scope_id = str(scope.get("scope_id") or "").strip()
			authority = (
				scope.get("approved_source_authority")
				if isinstance(scope.get("approved_source_authority"), dict)
				else {}
			)
			report_name = str(authority.get("report_name") or "").strip()
			listing_view = governed_scope_registry_module.listing_view_for_report_name(report_name)
			entity_grain = governed_scope_registry_module.entity_grain_for_report_name(report_name)
			if scope_id in {"customer_master", "supplier_master", "item_master"}:
				focus_grain = entity_grain or scope_id.replace("_master", "")
				row = _single_row_snapshot_fixture_for_focus_grain(focus_grain)
				self.assertTrue(bool(row), msg=report_name)
				session_doc = _fake_snapshot_session_for_grounded_report(
					request_id=f"snapshot-single-row-matrix-{index}",
					trace_request_id=f"snapshot-single-row-matrix-{index}-trace",
					report_name=report_name,
					artifact_family_id="master_data_directory",
					dimensions={"entity_type": focus_grain},
					table_rows=[row],
				)
				expected_focus_kind = "entity"
				expected_basis = "master_data_single_row_grounded_turn"
				expected_action_class = "detail_followup"
				expected_explicit_named_allowed = True
			else:
				focus_grain = listing_view or scope_id
				row = _single_row_snapshot_fixture_for_focus_grain(focus_grain)
				if not row:
					continue
				policy = governed_scope_registry_module.governed_scope_family_policy(scope_id, "entity_detail")
				allowed_modes = {
					str(value or "").strip()
					for value in ((policy or {}).get("allowed_modes") or [])
					if str(value or "").strip()
				}
				promotes_to_document_focus = bool(
					str((policy or {}).get("compatibility_level") or "").strip() == "full_consumption"
					and allowed_modes.intersection({"document_detail", "profile_section_evidence"})
				)
				session_doc = _fake_snapshot_session_for_grounded_report(
					request_id=f"snapshot-single-row-matrix-{index}",
					trace_request_id=f"snapshot-single-row-matrix-{index}-trace",
					report_name=report_name,
					artifact_family_id="transaction_listing",
					dimensions={"listing_view": focus_grain},
					table_rows=[row],
				)
				expected_focus_kind = "document" if promotes_to_document_focus else "listing"
				expected_basis = (
					"transaction_single_row_grounded_turn"
					if promotes_to_document_focus
					else "transaction_listing_grounded_turn"
				)
				expected_action_class = (
					"detail_followup"
					if promotes_to_document_focus
					else "document_selection_followup"
				)
				expected_explicit_named_allowed = promotes_to_document_focus

			snapshot = _build_conversation_state_snapshot(
				request_id=f"snapshot-single-row-matrix-{index}",
				session_doc=session_doc,
			)
			recent_focus = snapshot.get("recent_focus") or {}
			affordance = snapshot.get("recent_focus_affordance") or {}

			self.assertTrue(bool(recent_focus.get("available")), msg=report_name)
			self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), expected_focus_kind, msg=report_name)
			self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), focus_grain, msg=report_name)
			self.assertEqual(str(recent_focus.get("source_report") or "").strip(), report_name, msg=report_name)
			self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), expected_basis, msg=report_name)
			self.assertEqual(bool(recent_focus.get("explicit_named_allowed")), expected_explicit_named_allowed, msg=report_name)
			self.assertEqual(str(affordance.get("focus_kind") or "").strip(), expected_focus_kind, msg=report_name)
			if expected_focus_kind == "listing":
				self._assert_listing_focus_selection_contract(
					affordance,
					expected_action_class,
					msg=report_name,
				)
			else:
				self.assertIn(expected_action_class, list(affordance.get("allowed_action_classes") or []), msg=report_name)
			self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_recent_focus_affordance")), msg=report_name)

	def test_conversation_state_snapshot_matrix_covers_active_approved_detail_capable_scope_surface(self):
		scopes = [
			dict(item)
			for item in (governed_scope_registry_module.load_governed_scope_registry().get("scopes") or [])
			if isinstance(item, dict)
		]
		detail_capable_scopes = []
		for scope in scopes:
			scope_id = str(scope.get("scope_id") or "").strip()
			authority = (
				scope.get("approved_source_authority")
				if isinstance(scope.get("approved_source_authority"), dict)
				else {}
			)
			report_name = str(authority.get("report_name") or "").strip()
			if str(scope.get("status") or "").strip() != "active":
				continue
			if str(authority.get("authority_status") or "").strip() != "approved":
				continue
			if str(authority.get("source_kind") or "").strip() != "report":
				continue
			policy = governed_scope_registry_module.governed_scope_family_policy(scope_id, "entity_detail")
			if not isinstance(policy, dict) or not policy:
				continue
			if str(policy.get("compatibility_level") or "").strip() != "full_consumption":
				continue
			allowed_modes = {
				str(value or "").strip()
				for value in (policy.get("allowed_modes") or [])
				if str(value or "").strip()
			}
			if not allowed_modes.intersection({"profile_target", "document_detail"}):
				continue
			detail_capable_scopes.append((scope, allowed_modes))

		self.assertTrue(bool(detail_capable_scopes))
		for index, (scope, allowed_modes) in enumerate(detail_capable_scopes, start=1):
			scope_id = str(scope.get("scope_id") or "").strip()
			authority = (
				scope.get("approved_source_authority")
				if isinstance(scope.get("approved_source_authority"), dict)
				else {}
			)
			report_name = str(authority.get("report_name") or "").strip()
			fixture = _detail_snapshot_fixture_for_scope(scope_id, report_name)
			self.assertTrue(bool(fixture), msg=report_name)
			session_doc = _fake_snapshot_session_for_grounded_report(
				request_id=f"snapshot-detail-matrix-{index}",
				trace_request_id=f"snapshot-detail-matrix-{index}-trace",
				report_name=str(fixture.get("source_name") or "").strip(),
				artifact_family_id="entity_detail",
				dimensions={
					"entity_type": str(fixture.get("focus_grain") or "").strip(),
					"entity_label": str(fixture.get("entity_label") or "").strip(),
					"entity_key": str(fixture.get("entity_key") or "").strip(),
				},
			)

			snapshot = _build_conversation_state_snapshot(
				request_id=f"snapshot-detail-matrix-{index}",
				session_doc=session_doc,
			)
			recent_focus = snapshot.get("recent_focus") or {}
			affordance = snapshot.get("recent_focus_affordance") or {}
			expected_focus_kind = str(fixture.get("focus_kind") or "").strip()
			expected_focus_grain = str(fixture.get("focus_grain") or "").strip()
			expected_basis = (
				"entity_detail_grounded_turn"
				if expected_focus_kind == "entity"
				else "document_detail_grounded_turn"
			)

			self.assertTrue(bool(recent_focus.get("available")), msg=report_name)
			self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), expected_focus_kind, msg=report_name)
			self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), expected_focus_grain, msg=report_name)
			self.assertEqual(
				str(recent_focus.get("focus_label") or "").strip(),
				str(fixture.get("entity_label") or "").strip(),
				msg=report_name,
			)
			self.assertEqual(str(recent_focus.get("source_family") or "").strip(), "entity_detail", msg=report_name)
			self.assertEqual(str(recent_focus.get("source_report") or "").strip(), str(fixture.get("source_name") or "").strip(), msg=report_name)
			self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), expected_basis, msg=report_name)
			self.assertTrue(bool(recent_focus.get("explicit_named_allowed")), msg=report_name)
			self.assertEqual(str(affordance.get("focus_kind") or "").strip(), expected_focus_kind, msg=report_name)
			self.assertIn("detail_followup", list(affordance.get("allowed_action_classes") or []), msg=report_name)
			if expected_focus_kind == "entity":
				if expected_focus_grain == "item":
					self.assertIn("inventory_position_followup", list(affordance.get("allowed_action_classes") or []), msg=report_name)
				else:
					self.assertIn("commercial_status_followup", list(affordance.get("allowed_action_classes") or []), msg=report_name)
			else:
				self.assertTrue("document_detail" in allowed_modes, msg=report_name)
				self.assertIn("linked_document_navigation", list(affordance.get("allowed_action_classes") or []), msg=report_name)
				self.assertIn("document_status_followup", list(affordance.get("allowed_action_classes") or []), msg=report_name)
			self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_recent_focus_affordance")), msg=report_name)

	def test_compile_recent_focus_runtime_message_matrix_covers_active_approved_detail_capable_scope_surface(self):
		scopes = [
			dict(item)
			for item in (governed_scope_registry_module.load_governed_scope_registry().get("scopes") or [])
			if isinstance(item, dict)
		]
		detail_capable_scopes = []
		for scope in scopes:
			scope_id = str(scope.get("scope_id") or "").strip()
			authority = (
				scope.get("approved_source_authority")
				if isinstance(scope.get("approved_source_authority"), dict)
				else {}
			)
			report_name = str(authority.get("report_name") or "").strip()
			if str(scope.get("status") or "").strip() != "active":
				continue
			if str(authority.get("authority_status") or "").strip() != "approved":
				continue
			if str(authority.get("source_kind") or "").strip() != "report":
				continue
			policy = governed_scope_registry_module.governed_scope_family_policy(scope_id, "entity_detail")
			if not isinstance(policy, dict) or not policy:
				continue
			if str(policy.get("compatibility_level") or "").strip() != "full_consumption":
				continue
			allowed_modes = {
				str(value or "").strip()
				for value in (policy.get("allowed_modes") or [])
				if str(value or "").strip()
			}
			if not allowed_modes.intersection({"profile_target", "document_detail"}):
				continue
			detail_capable_scopes.append(scope)

		self.assertTrue(bool(detail_capable_scopes))
		followup_resolution = _runtime_followup_resolution()
		for index, scope in enumerate(detail_capable_scopes, start=1):
			scope_id = str(scope.get("scope_id") or "").strip()
			authority = (
				scope.get("approved_source_authority")
				if isinstance(scope.get("approved_source_authority"), dict)
				else {}
			)
			report_name = str(authority.get("report_name") or "").strip()
			fixture = _detail_snapshot_fixture_for_scope(scope_id, report_name)
			session_doc = _fake_snapshot_session_for_grounded_report(
				request_id=f"runtime-detail-matrix-{index}",
				trace_request_id=f"runtime-detail-matrix-{index}-trace",
				report_name=str(fixture.get("source_name") or "").strip(),
				artifact_family_id="entity_detail",
				dimensions={
					"entity_type": str(fixture.get("focus_grain") or "").strip(),
					"entity_label": str(fixture.get("entity_label") or "").strip(),
					"entity_key": str(fixture.get("entity_key") or "").strip(),
				},
			)
			snapshot = _build_conversation_state_snapshot(
				request_id=f"runtime-detail-matrix-{index}",
				session_doc=session_doc,
			)
			recent_focus = snapshot.get("recent_focus") or {}
			runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
				request_id=f"runtime-detail-matrix-{index}",
				raw_message="tell me more about that",
				followup_resolution=followup_resolution,
				recent_focus_state=recent_focus,
				grounded_turn={"artifact_family_id": "entity_detail"},
				artifact_payload={
					"family_id": "entity_detail",
					"dimensions": {
						"entity_type": str(fixture.get("focus_grain") or "").strip(),
						"entity_label": str(fixture.get("entity_label") or "").strip(),
						"entity_key": str(fixture.get("entity_key") or "").strip(),
					},
				},
			)

			self.assertEqual(routing_basis, "local_transform", msg=report_name)
			self.assertTrue(bool(runtime_message), msg=report_name)
			self.assertIn(str(fixture.get("entity_label") or "").strip(), runtime_message, msg=report_name)
			self.assertEqual(str(getattr(affordance_contract, "focus_kind", "") or "").strip(), str(fixture.get("focus_kind") or "").strip(), msg=report_name)

	def test_compile_recent_focus_runtime_message_matrix_covers_active_approved_listing_scope_surface(self):
		scopes = [
			dict(item)
			for item in (governed_scope_registry_module.load_governed_scope_registry().get("scopes") or [])
			if isinstance(item, dict)
		]
		active_listing_scopes = []
		for scope in scopes:
			authority = (
				scope.get("approved_source_authority")
				if isinstance(scope.get("approved_source_authority"), dict)
				else {}
			)
			report_name = str(authority.get("report_name") or "").strip()
			if str(scope.get("status") or "").strip() != "active":
				continue
			if str(authority.get("authority_status") or "").strip() != "approved":
				continue
			if str(authority.get("source_kind") or "").strip() != "report":
				continue
			if not report_name.endswith("List"):
				continue
			active_listing_scopes.append(scope)

		self.assertTrue(bool(active_listing_scopes))
		followup_resolution = _runtime_followup_resolution()
		for index, scope in enumerate(active_listing_scopes, start=1):
			scope_id = str(scope.get("scope_id") or "").strip()
			authority = (
				scope.get("approved_source_authority")
				if isinstance(scope.get("approved_source_authority"), dict)
				else {}
			)
			report_name = str(authority.get("report_name") or "").strip()
			listing_view = governed_scope_registry_module.listing_view_for_report_name(report_name)
			entity_grain = governed_scope_registry_module.entity_grain_for_report_name(report_name)
			if scope_id in {"customer_master", "supplier_master", "item_master"}:
				session_doc = _fake_snapshot_session_for_grounded_report(
					request_id=f"runtime-listing-matrix-{index}",
					trace_request_id=f"runtime-listing-matrix-{index}-trace",
					report_name=report_name,
					artifact_family_id="master_data_directory",
					dimensions={"entity_type": entity_grain or scope_id.replace("_master", "")},
					table_rows=[{"name": f"ROW-{index}-A"}, {"name": f"ROW-{index}-B"}],
				)
				grounded_turn = {"artifact_family_id": "master_data_directory"}
				artifact_payload = {"family_id": "master_data_directory"}
			else:
				session_doc = _fake_snapshot_session_for_grounded_report(
					request_id=f"runtime-listing-matrix-{index}",
					trace_request_id=f"runtime-listing-matrix-{index}-trace",
					report_name=report_name,
					artifact_family_id="transaction_listing",
					dimensions={"listing_view": listing_view or scope_id},
					table_rows=[{"name": f"ROW-{index}-A"}, {"name": f"ROW-{index}-B"}],
				)
				grounded_turn = {"artifact_family_id": "transaction_listing"}
				artifact_payload = {"family_id": "transaction_listing"}
			snapshot = _build_conversation_state_snapshot(
				request_id=f"runtime-listing-matrix-{index}",
				session_doc=session_doc,
			)
			runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
				request_id=f"runtime-listing-matrix-{index}",
				raw_message="tell me more about that",
				followup_resolution=followup_resolution,
				recent_focus_state=snapshot.get("recent_focus") or {},
				grounded_turn=grounded_turn,
				artifact_payload=artifact_payload,
			)

			self.assertEqual(routing_basis, "shared_affordance", msg=report_name)
			self.assertEqual(runtime_message, "tell me more about that", msg=report_name)
			self.assertEqual(str(getattr(affordance_contract, "focus_kind", "") or "").strip(), "listing", msg=report_name)

	def test_compile_recent_focus_runtime_message_matrix_covers_active_approved_statement_and_report_surface(self):
		report_specs = [
			dict(item)
			for item in (load_report_registry().get("reports") or [])
			if isinstance(item, dict)
			and list(report_approved_followup_modes(str(item.get("report_name") or "").strip()))
		]
		self.assertTrue(bool(report_specs))
		followup_resolution = _runtime_followup_resolution()
		for index, report_spec in enumerate(report_specs, start=1):
			report_name = str(report_spec.get("report_name") or "").strip()
			if governed_scope_registry_module.scope_id_for_report_name(report_name):
				continue
			statement_descriptor = recent_focus_support_module.statement_recent_focus_descriptor_for_report_name(report_name)
			if statement_descriptor:
				session_doc = _fake_snapshot_session_for_grounded_report(
					request_id=f"runtime-report-matrix-{index}",
					trace_request_id=f"runtime-report-matrix-{index}-trace",
					report_name=report_name,
					artifact_family_id=str(report_spec.get("family") or "").strip() or "financial_statement",
				)
				expected_focus_kind = "statement"
			else:
				session_doc = _fake_snapshot_session_for_grounded_report(
					request_id=f"runtime-report-matrix-{index}",
					trace_request_id=f"runtime-report-matrix-{index}-trace",
					report_name=report_name,
					artifact_family_id=str(report_spec.get("family") or "").strip() or report_name.lower().replace(" ", "_"),
				)
				expected_focus_kind = "report"
			snapshot = _build_conversation_state_snapshot(
				request_id=f"runtime-report-matrix-{index}",
				session_doc=session_doc,
			)
			runtime_message, routing_basis, affordance_contract = _compile_recent_focus_runtime_message(
				request_id=f"runtime-report-matrix-{index}",
				raw_message="tell me more about that",
				followup_resolution=followup_resolution,
				recent_focus_state=snapshot.get("recent_focus") or {},
				grounded_turn={"artifact_family_id": str(report_spec.get("family") or "").strip()},
				artifact_payload={"family_id": str(report_spec.get("family") or "").strip()},
			)

			self.assertEqual(routing_basis, "shared_affordance", msg=report_name)
			self.assertEqual(runtime_message, "tell me more about that", msg=report_name)
			self.assertEqual(str(getattr(affordance_contract, "focus_kind", "") or "").strip(), expected_focus_kind, msg=report_name)

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

	def test_conversation_state_snapshot_recent_focus_derives_from_item_master_listing(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "item-list-grounded-1",
			"trace_request_id": "item-list-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Item Master List",
			"artifact_family_id": "master_data_directory",
			"artifact_source_reports": ["Item Master List"],
		}
		list_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "item-list-grounded-1-trace",
			"family_id": "master_data_directory",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Item Master List"],
			"dimensions": {
				"entity_type": "item",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(list_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-item-list-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "item")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Item Master List")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "master_data_listing_grounded_turn")
		self.assertIn("entity_selection_followup", list(affordance.get("allowed_action_classes") or []))
		self.assertIn("column_refinement", list(affordance.get("allowed_local_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_customer_master_listing(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "customer-list-grounded-1",
			"trace_request_id": "customer-list-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Customer Master List",
			"artifact_family_id": "master_data_directory",
			"artifact_source_reports": ["Customer Master List"],
		}
		list_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "customer-list-grounded-1-trace",
			"family_id": "master_data_directory",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Customer Master List"],
			"dimensions": {
				"entity_type": "customer",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(list_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-customer-list-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "customer")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Customer Master List")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "master_data_listing_grounded_turn")
		self.assertIn("entity_selection_followup", list(affordance.get("allowed_action_classes") or []))
		self.assertIn("column_refinement", list(affordance.get("allowed_local_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_sales_order_listing(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "sales-order-list-grounded-1",
			"trace_request_id": "sales-order-list-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Sales Order List",
			"artifact_family_id": "transaction_listing",
			"artifact_source_reports": ["Sales Order List"],
		}
		list_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "sales-order-list-grounded-1-trace",
			"family_id": "transaction_listing",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Sales Order List"],
			"dimensions": {
				"listing_view": "sales_order",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(list_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-sales-order-list-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "sales_order")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Sales Order List")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_listing_grounded_turn")
		self.assertIn("document_selection_followup", list(affordance.get("allowed_action_classes") or []))
		self.assertIn("time_refinement", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_sales_invoice_listing(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "sales-invoice-list-grounded-1",
			"trace_request_id": "sales-invoice-list-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Sales Invoice List",
			"artifact_family_id": "transaction_listing",
			"artifact_source_reports": ["Sales Invoice List"],
		}
		list_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "sales-invoice-list-grounded-1-trace",
			"family_id": "transaction_listing",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Sales Invoice List"],
			"dimensions": {
				"listing_view": "sales_invoice",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(list_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-sales-invoice-list-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "sales_invoice")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Sales Invoice List")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_listing_grounded_turn")
		self.assertIn("document_selection_followup", list(affordance.get("allowed_action_classes") or []))
		self.assertIn("time_refinement", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_delivery_note_listing(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "delivery-note-list-grounded-1",
			"trace_request_id": "delivery-note-list-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Delivery Note List",
			"artifact_family_id": "transaction_listing",
			"artifact_source_reports": ["Delivery Note List"],
		}
		list_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "delivery-note-list-grounded-1-trace",
			"family_id": "transaction_listing",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Delivery Note List"],
			"dimensions": {
				"listing_view": "delivery_note",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(list_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-delivery-note-list-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "delivery_note")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Delivery Note List")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_listing_grounded_turn")
		self.assertIn("document_selection_followup", list(affordance.get("allowed_action_classes") or []))
		self.assertIn("time_refinement", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_purchase_order_listing(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "purchase-order-list-grounded-1",
			"trace_request_id": "purchase-order-list-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Purchase Order List",
			"artifact_family_id": "transaction_listing",
			"artifact_source_reports": ["Purchase Order List"],
		}
		list_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "purchase-order-list-grounded-1-trace",
			"family_id": "transaction_listing",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Purchase Order List"],
			"dimensions": {
				"listing_view": "purchase_order",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(list_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-purchase-order-list-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "purchase_order")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Purchase Order List")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_listing_grounded_turn")
		self.assertIn("document_selection_followup", list(affordance.get("allowed_action_classes") or []))
		self.assertIn("time_refinement", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_purchase_invoice_listing(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "purchase-invoice-list-grounded-1",
			"trace_request_id": "purchase-invoice-list-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Purchase Invoice List",
			"artifact_family_id": "transaction_listing",
			"artifact_source_reports": ["Purchase Invoice List"],
		}
		list_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "purchase-invoice-list-grounded-1-trace",
			"family_id": "transaction_listing",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Purchase Invoice List"],
			"dimensions": {
				"listing_view": "purchase_invoice",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(list_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-purchase-invoice-list-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "purchase_invoice")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Purchase Invoice List")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_listing_grounded_turn")
		self.assertIn("document_selection_followup", list(affordance.get("allowed_action_classes") or []))
		self.assertIn("time_refinement", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_document_focus_from_document_detail(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "sales-invoice-detail-grounded-1",
			"trace_request_id": "sales-invoice-detail-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Sales Invoice Detail",
			"artifact_family_id": "entity_detail",
			"artifact_source_reports": ["Sales Invoice Detail"],
		}
		document_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "sales-invoice-detail-grounded-1-trace",
			"family_id": "entity_detail",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Sales Invoice Detail"],
			"dimensions": {
				"entity_type": "sales_invoice",
				"entity_label": "ACC-SINV-2026-00194",
			},
		}
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="sales-invoice-detail-recovery-1",
			session_id="phase8a",
			source_request_id="sales-invoice-detail-grounded-1-trace",
			source_family_id="entity_detail",
			source_capability_id="sales_invoice_read",
			source_report="Sales Invoice Detail",
			recovery_state="recoverable",
			available_recovery_actions=["run_alternative_governed_query"],
			recommended_recovery_action="run_alternative_governed_query",
			allowed_to_recover=True,
			confidence=0.9,
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(document_artifact_payload)),
				_FakeMessage(role="tool", content=json.dumps(recovery_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-sales-invoice-document-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "document")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "sales_invoice")
		self.assertEqual(str(recent_focus.get("focus_label") or "").strip(), "ACC-SINV-2026-00194")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "document_detail_grounded_turn")
		self.assertEqual(str(recent_focus.get("source_capability") or "").strip(), "sales_invoice_read")
		self.assertEqual(str(affordance.get("focus_kind") or "").strip(), "document")
		self.assertIn("linked_document_navigation", list(affordance.get("allowed_action_classes") or []))
		self.assertIn("document_status_followup", list(affordance.get("allowed_action_classes") or []))
		self.assertIn("document_event_followup", list(affordance.get("allowed_action_classes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_report_view(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "ranking-grounded-1",
			"trace_request_id": "ranking-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Gross Profit",
			"artifact_family_id": "ranking_analytics",
			"artifact_source_reports": ["Gross Profit"],
		}
		ranking_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "ranking-grounded-1-trace",
			"family_id": "ranking_analytics",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Gross Profit"],
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
		self.assertIn("new_query", list(affordance.get("allowed_requery_followup_modes") or []))
		self.assertTrue(bool(affordance.get("supports_cross_family_followup")))

	def test_conversation_state_snapshot_recent_focus_derives_from_accounts_receivable_summary_report(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "ar-summary-grounded-1",
			"trace_request_id": "ar-summary-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Accounts Receivable Summary",
			"artifact_family_id": "aging",
			"artifact_source_reports": ["Accounts Receivable Summary"],
		}
		report_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "ar-summary-grounded-1-trace",
			"family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Accounts Receivable Summary"],
			"dimensions": {
				"subject": "customer",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(report_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-ar-summary-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "aging")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Accounts Receivable Summary")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn")
		self.assertIn("aging_bucket_view", list(affordance.get("allowed_local_followup_modes") or []))
		self.assertIn("sibling_switch", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_accounts_receivable_report(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "ar-grounded-1",
			"trace_request_id": "ar-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Accounts Receivable",
			"artifact_family_id": "aging",
			"artifact_source_reports": ["Accounts Receivable"],
		}
		report_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "ar-grounded-1-trace",
			"family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Accounts Receivable"],
			"dimensions": {
				"subject": "customer",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(report_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-ar-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "aging")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Accounts Receivable")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn")
		self.assertIn("aging_bucket_view", list(affordance.get("allowed_local_followup_modes") or []))
		self.assertIn("sibling_switch", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_accounts_payable_summary_report(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "ap-summary-grounded-1",
			"trace_request_id": "ap-summary-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Accounts Payable Summary",
			"artifact_family_id": "aging",
			"artifact_source_reports": ["Accounts Payable Summary"],
		}
		report_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "ap-summary-grounded-1-trace",
			"family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Accounts Payable Summary"],
			"dimensions": {
				"subject": "supplier",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(report_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-ap-summary-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "aging")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Accounts Payable Summary")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn")
		self.assertIn("aging_bucket_view", list(affordance.get("allowed_local_followup_modes") or []))
		self.assertIn("sibling_switch", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_accounts_payable_report(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "ap-grounded-1",
			"trace_request_id": "ap-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Accounts Payable",
			"artifact_family_id": "aging",
			"artifact_source_reports": ["Accounts Payable"],
		}
		report_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "ap-grounded-1-trace",
			"family_id": "aging",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Accounts Payable"],
			"dimensions": {
				"subject": "supplier",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(report_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-ap-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "aging")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Accounts Payable")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn")
		self.assertIn("aging_bucket_view", list(affordance.get("allowed_local_followup_modes") or []))
		self.assertIn("sibling_switch", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_stock_balance_report(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "stock-balance-grounded-1",
			"trace_request_id": "stock-balance-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Stock Balance",
			"artifact_family_id": "inventory_snapshot",
			"artifact_source_reports": ["Stock Balance"],
		}
		report_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "stock-balance-grounded-1-trace",
			"family_id": "inventory_snapshot",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Stock Balance"],
			"dimensions": {
				"subject": "item",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(report_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-stock-balance-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "inventory_snapshot")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Stock Balance")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn")
		self.assertIn("grouping_change", list(affordance.get("allowed_requery_followup_modes") or []))
		self.assertIn("filter_refinement", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_warehouse_wise_stock_balance_report(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "warehouse-stock-grounded-1",
			"trace_request_id": "warehouse-stock-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Warehouse Wise Stock Balance",
			"artifact_family_id": "inventory_snapshot",
			"artifact_source_reports": ["Warehouse Wise Stock Balance"],
		}
		report_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "warehouse-stock-grounded-1-trace",
			"family_id": "inventory_snapshot",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Warehouse Wise Stock Balance"],
			"dimensions": {
				"subject": "warehouse",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(report_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-warehouse-stock-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "inventory_snapshot")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Warehouse Wise Stock Balance")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn")
		self.assertIn("grouping_change", list(affordance.get("allowed_requery_followup_modes") or []))
		self.assertIn("filter_refinement", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_delivery_note_trends_report(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "delivery-trends-grounded-1",
			"trace_request_id": "delivery-trends-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Delivery Note Trends",
			"artifact_family_id": "trend_analytics",
			"artifact_source_reports": ["Delivery Note Trends"],
		}
		report_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "delivery-trends-grounded-1-trace",
			"family_id": "trend_analytics",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Delivery Note Trends"],
			"dimensions": {
				"subject": "customer",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(report_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-delivery-trends-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "trend_analytics")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Delivery Note Trends")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn")
		self.assertIn("metric_refinement", list(affordance.get("allowed_local_followup_modes") or []))
		self.assertIn("filter_refinement", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_sales_analytics_report(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "sales-analytics-grounded-1",
			"trace_request_id": "sales-analytics-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Sales Analytics",
			"artifact_family_id": "trend_analytics",
			"artifact_source_reports": ["Sales Analytics"],
		}
		report_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "sales-analytics-grounded-1-trace",
			"family_id": "trend_analytics",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Sales Analytics"],
			"dimensions": {
				"subject": "customer",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(report_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-sales-analytics-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "trend_analytics")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Sales Analytics")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn")
		self.assertIn("metric_refinement", list(affordance.get("allowed_local_followup_modes") or []))
		self.assertIn("grouping_change", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_item_wise_sales_history_report(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "item-sales-history-grounded-1",
			"trace_request_id": "item-sales-history-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Item-wise Sales History",
			"artifact_family_id": "product_performance",
			"artifact_source_reports": ["Item-wise Sales History"],
		}
		report_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "item-sales-history-grounded-1-trace",
			"family_id": "product_performance",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Item-wise Sales History"],
			"dimensions": {
				"subject": "item",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(report_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-item-sales-history-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "product_performance")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Item-wise Sales History")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn")
		self.assertIn("sort_or_limit", list(affordance.get("allowed_local_followup_modes") or []))
		self.assertIn("filter_refinement", list(affordance.get("allowed_requery_followup_modes") or []))

	def test_conversation_state_snapshot_recent_focus_derives_from_sales_order_item_list_report(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "sales-order-item-list-grounded-1",
			"trace_request_id": "sales-order-item-list-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Sales Order Item List",
			"artifact_family_id": "sales_order_item_list",
			"artifact_source_reports": ["Sales Order Item List"],
		}
		report_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "sales-order-item-list-grounded-1-trace",
			"family_id": "sales_order_item_list",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Sales Order Item List"],
			"dimensions": {
				"subject": "item",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(report_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-sales-order-item-list-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "sales_order_item_list")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Sales Order Item List")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn")
		self.assertEqual(list(affordance.get("allowed_local_followup_modes") or []), [])
		self.assertEqual(list(affordance.get("allowed_requery_followup_modes") or []), ["new_query"])

	def test_conversation_state_snapshot_recent_focus_derives_from_sales_invoice_item_list_report(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "sales-invoice-item-list-grounded-1",
			"trace_request_id": "sales-invoice-item-list-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Sales Invoice Item List",
			"artifact_family_id": "sales_invoice_item_list",
			"artifact_source_reports": ["Sales Invoice Item List"],
		}
		report_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "sales-invoice-item-list-grounded-1-trace",
			"family_id": "sales_invoice_item_list",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Sales Invoice Item List"],
			"dimensions": {
				"subject": "item",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(report_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-sales-invoice-item-list-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "report")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "sales_invoice_item_list")
		self.assertEqual(str(recent_focus.get("source_report") or "").strip(), "Sales Invoice Item List")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "report_grounded_turn")
		self.assertEqual(list(affordance.get("allowed_local_followup_modes") or []), [])
		self.assertEqual(list(affordance.get("allowed_requery_followup_modes") or []), ["new_query"])

	def test_conversation_state_snapshot_recent_focus_derives_from_statement_view(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "statement-grounded-1",
			"trace_request_id": "statement-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Profit and Loss Statement",
			"artifact_family_id": "financial_statement",
			"artifact_source_reports": ["Profit and Loss Statement"],
		}
		statement_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "statement-grounded-1-trace",
			"family_id": "financial_statement",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Profit and Loss Statement"],
			"dimensions": {
				"statement_type": "profit_and_loss",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(statement_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-statement-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "statement")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "profit_and_loss")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "statement_grounded_turn")
		self.assertIn("statement_switch", list(affordance.get("allowed_action_classes") or []))
		self.assertIn("line_item_followup", list(affordance.get("allowed_action_classes") or []))
		self.assertIn("new_query", list(affordance.get("allowed_requery_followup_modes") or []))
		self.assertTrue(bool(affordance.get("supports_cross_family_followup")))

	def test_conversation_state_snapshot_recent_focus_derives_from_transaction_listing(self):
		grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "payment-list-grounded-1",
			"trace_request_id": "payment-list-grounded-1-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Payment Entry List",
			"artifact_family_id": "transaction_listing",
			"artifact_source_reports": ["Payment Entry List"],
			"table_rows": [
				{"Payment Entry": "ACC-PAY-2026-00179", "Party": "Golden Dragon Trading Co. Ltd."},
				{"Payment Entry": "ACC-PAY-2026-00178", "Party": "Capital Telecom (NPT)"},
			],
		}
		listing_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "payment-list-grounded-1-trace",
			"family_id": "transaction_listing",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Payment Entry List"],
			"dimensions": {
				"listing_view": "payment_entry",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(listing_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-payment-entry-list-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		affordance = snapshot.get("recent_focus_affordance") or {}

		self.assertTrue(bool(recent_focus.get("available")))
		self.assertEqual(str(recent_focus.get("focus_kind") or "").strip(), "listing")
		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "payment_entry")
		self.assertEqual(str(recent_focus.get("derivation_basis") or "").strip(), "transaction_listing_grounded_turn")
		self._assert_listing_focus_selection_contract(
			affordance,
			"document_selection_followup",
		)
		self.assertIn("new_query", list(affordance.get("allowed_requery_followup_modes") or []))
		self.assertTrue(bool(affordance.get("supports_cross_family_followup")))

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
		self.assertEqual(str(prior_branch.get("derivation_basis") or "").strip(), "conservative_none")
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

	def test_targeted_branch_restore_matches_resumable_prior_request_target_scope_focus_grain(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {"active": True},
			"recent_focus": {
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "payment_entry",
				"focus_label": "Payment Entry List",
				"source_tool_index": 12,
			},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "prior_recent_focus_origin",
				"branch_label": "Ko Nay Lin Mobile Center",
				"source_request_id": "customer-detail-request-1",
				"target_family": "entity_detail",
				"target_scope": {
					"focus_kind": "entity",
					"focus_grain": "customer",
					"focus_key": "Ko Nay Lin Mobile Center",
					"focus_label": "Ko Nay Lin Mobile Center",
					"source_report": "Customer Detail",
					"deictic_allowed": True,
					"explicit_named_allowed": True,
				},
				"resumable": True,
				"suggested_restore_mode": "restore_recent_focus",
				"derivation_basis": "historical_grounded_branch_before_current_focus",
				"confidence": 0.78,
				"source_tool_index": 4,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-prior-focus-1",
			raw_message="go back to the customer",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-prior-focus-1",
				raw_message="go back to the customer",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(
			str((payload.get("target_scope") or {}).get("focus_grain") or "").strip(),
			"customer",
		)
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"targeted_resumable_prior_branch_restore",
		)

	def test_discard_prefixed_targeted_branch_restore_matches_historical_prior_branch_over_active_sequence(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {"active": True},
			"recent_focus": {
				"available": True,
				"focus_kind": "listing",
				"focus_grain": "payment_entry",
				"focus_label": "Payment Entry List",
				"source_tool_index": 12,
			},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "prior_recent_focus_origin",
				"branch_label": "Ko Nay Lin Mobile Center",
				"source_request_id": "customer-detail-request-1",
				"target_family": "entity_detail",
				"target_scope": {
					"focus_kind": "entity",
					"focus_grain": "customer",
					"focus_key": "Ko Nay Lin Mobile Center",
					"focus_label": "Ko Nay Lin Mobile Center",
					"source_report": "Customer Detail",
					"deictic_allowed": True,
					"explicit_named_allowed": True,
				},
				"resumable": True,
				"suggested_restore_mode": "restore_recent_focus",
				"derivation_basis": "historical_grounded_branch_before_current_focus",
				"confidence": 0.78,
				"source_tool_index": 4,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-prior-focus-discard-1",
			raw_message="forget that, go back to the customer",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-prior-focus-discard-1",
				raw_message="forget that, go back to the customer",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(str(payload.get("target_branch_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(
			str((payload.get("target_scope") or {}).get("focus_grain") or "").strip(),
			"customer",
		)
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"targeted_resumable_prior_branch_restore",
		)

	def test_targeted_collection_alias_restore_prefers_historical_supplier_listing_over_newer_supplier_detail(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "supplier",
				"focus_label": "Myanmar Tech Import Services",
				"focus_key": "Myanmar Tech Import Services",
				"source_request_id": "supplier-detail-current-1",
				"source_family": "entity_detail",
				"source_capability": "supplier_detail_read",
				"source_report": "Supplier Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"source_tool_index": 18,
			},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "prior_recent_focus_origin",
				"branch_label": "Supplier Master List",
				"source_request_id": "supplier-list-history-1",
				"target_family": "master_data_directory",
				"target_scope": {
					"focus_kind": "listing",
					"focus_grain": "supplier",
					"focus_key": "supplier",
					"focus_label": "Supplier Master List",
					"source_report": "Supplier Master List",
					"source_capability": "supplier_master_read",
					"deictic_allowed": True,
					"explicit_named_allowed": False,
				},
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "historical_grounded_branch_before_current_focus",
				"confidence": 0.8,
				"source_tool_index": 8,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-supplier-directory-1",
			raw_message="go back to the supplier directory",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-supplier-directory-1",
				raw_message="go back to the supplier directory",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "replay_as_fresh_governed_query")
		self.assertEqual(str(payload.get("target_family") or "").strip(), "master_data_directory")
		self.assertEqual(str(((payload.get("target_scope") or {}).get("focus_kind")) or "").strip(), "listing")
		self.assertEqual(str(((payload.get("target_scope") or {}).get("focus_grain")) or "").strip(), "supplier")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"targeted_resumable_prior_branch_restore",
		)

	def test_discard_prefixed_collection_alias_restore_prefers_historical_supplier_listing_over_newer_supplier_detail(self):
		snapshot = {
			"pending_clarification": {"available": False},
			"active_sequence": {"active": False},
			"recent_focus": {
				"available": True,
				"focus_kind": "entity",
				"focus_grain": "supplier",
				"focus_label": "Myanmar Tech Import Services",
				"focus_key": "Myanmar Tech Import Services",
				"source_request_id": "supplier-detail-current-2",
				"source_family": "entity_detail",
				"source_capability": "supplier_detail_read",
				"source_report": "Supplier Detail",
				"deictic_allowed": True,
				"explicit_named_allowed": True,
				"source_tool_index": 18,
			},
			"resumable_prior_request": {
				"available": True,
				"branch_kind": "prior_recent_focus_origin",
				"branch_label": "Supplier Master List",
				"source_request_id": "supplier-list-history-2",
				"target_family": "master_data_directory",
				"target_scope": {
					"focus_kind": "listing",
					"focus_grain": "supplier",
					"focus_key": "supplier",
					"focus_label": "Supplier Master List",
					"source_report": "Supplier Master List",
					"source_capability": "supplier_master_read",
					"deictic_allowed": True,
					"explicit_named_allowed": False,
				},
				"resumable": True,
				"suggested_restore_mode": "requery_prior_branch",
				"derivation_basis": "historical_grounded_branch_before_current_focus",
				"confidence": 0.8,
				"source_tool_index": 8,
			},
		}

		contract = _build_prior_branch_restore_contract_from_snapshot(
			request_id="restore-targeted-supplier-directory-discard-1",
			raw_message="forget that, go back to the supplier directories",
			conversation_state_snapshot=snapshot,
			control_evidence_payload=_build_conversation_control_evidence_contract(
				request_id="control-evidence-targeted-supplier-directory-discard-1",
				raw_message="forget that, go back to the supplier directories",
			).to_payload(),
		)
		payload = contract.to_payload()

		self.assertEqual(str(payload.get("restore_mode") or "").strip(), "replay_as_fresh_governed_query")
		self.assertEqual(str(payload.get("target_family") or "").strip(), "master_data_directory")
		self.assertEqual(str(((payload.get("target_scope") or {}).get("focus_kind")) or "").strip(), "listing")
		self.assertEqual(str(((payload.get("target_scope") or {}).get("focus_grain")) or "").strip(), "supplier")
		self.assertEqual(
			str((payload.get("internal_details") or {}).get("arbitration_basis") or "").strip(),
			"targeted_resumable_prior_branch_restore",
		)

	def test_conversation_state_snapshot_derives_historical_prior_recent_focus_during_active_sequence(self):
		customer_grounded_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "customer-detail-request-1",
			"trace_request_id": "customer-detail-trace-1",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Customer Detail",
			"artifact_family_id": "entity_detail",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Customer Detail"],
			"known_entities": [],
			"known_documents": [],
		}
		customer_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "customer-detail-trace-1",
			"family_id": "entity_detail",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Customer Detail"],
			"dimensions": {
				"entity_type": "customer",
				"entity_label": "Ko Nay Lin Mobile Center",
				"entity_key": "Ko Nay Lin Mobile Center",
			},
		}
		payment_grounded_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "payment-list-request-1",
			"trace_request_id": "payment-list-trace-1",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Payment Entry List",
			"artifact_family_id": "transaction_listing",
			"artifact_type": "normalized_family_artifact",
			"artifact_source_reports": ["Payment Entry List"],
			"known_entities": [],
			"known_documents": [],
		}
		payment_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "payment-list-trace-1",
			"family_id": "transaction_listing",
			"artifact_type": "normalized_family_artifact",
			"source_reports": ["Payment Entry List"],
			"dimensions": {"listing_view": "payment_entry"},
		}
		active_sequence_payload = build_compound_request_assessment_contract(
			request_id="compound-active-historical-1",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			clarification_required=False,
			reason="Two ordered steps were identified.",
			internal_details={
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "give me some supplier list",
				"remaining_segment_messages": [],
			},
		).to_payload()
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(customer_grounded_payload)),
				_FakeMessage(role="tool", content=json.dumps(customer_artifact_payload)),
				_FakeMessage(role="tool", content=json.dumps(payment_grounded_payload)),
				_FakeMessage(role="tool", content=json.dumps(payment_artifact_payload)),
				_FakeMessage(role="tool", content=json.dumps(active_sequence_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-historical-prior-focus",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		prior_branch = snapshot.get("resumable_prior_request") or {}

		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "payment_entry")
		self.assertTrue(bool(prior_branch.get("available")))
		self.assertEqual(str(prior_branch.get("branch_kind") or "").strip(), "prior_recent_focus_origin")
		self.assertEqual(str(prior_branch.get("branch_label") or "").strip(), "Ko Nay Lin Mobile Center")
		self.assertEqual(str(prior_branch.get("suggested_restore_mode") or "").strip(), "restore_recent_focus")
		self.assertEqual(
			str((prior_branch.get("target_scope") or {}).get("focus_grain") or "").strip(),
			"customer",
		)
		self.assertEqual(
			str(prior_branch.get("derivation_basis") or "").strip(),
			"historical_grounded_branch_before_current_focus",
		)
		self.assertEqual(
			str(((prior_branch.get("internal_details") or {}).get("arbitration_basis")) or "").strip(),
			"historical_prior_focus_only_available",
		)
		self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_resumable_prior_request")))

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
		self.assertEqual(
			int(prior_branch.get("source_tool_index")) if prior_branch.get("source_tool_index") is not None else -1,
			2,
		)
		self.assertEqual(
			int(((prior_branch.get("internal_details") or {}).get("accepted_repair_source_tool_index")) or -1),
			1,
		)
		self.assertEqual(
			int(((prior_branch.get("internal_details") or {}).get("newer_grounded_turn_source_tool_index")) or -1),
			2,
		)
		self.assertEqual(str(latest_repair.get("repair_intent_type") or "").strip(), "accept_recovery_action")
		self.assertEqual(
			int(latest_repair.get("source_tool_index")) if latest_repair.get("source_tool_index") is not None else -1,
			1,
		)
		self.assertEqual(
			str(((prior_branch.get("internal_details") or {}).get("arbitration_basis")) or "").strip(),
			"accepted_repair_only_available",
		)
		self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_latest_repair_intent")))
		self.assertTrue(bool((snapshot.get("state_quality") or {}).get("has_resumable_prior_request")))

	def test_conversation_state_snapshot_prefers_newer_accepted_repair_branch_over_historical_prior_focus(self):
		recovery_payload = build_artifact_enrichment_recovery_contract(
			request_id="recovery-prior-2",
			session_id="phase8a",
			source_request_id="grounded-prior-trace-2",
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
			request_id="repair-prior-2",
			session_id="phase8a",
			repair_intent_type="accept_recovery_action",
			repair_state="accepted",
			targets_prior_recovery=True,
			accepted_recovery_action="run_alternative_governed_query",
			reason="User accepted the governed alternative.",
			allowed_next_lane="artifact_lane",
			confidence=0.96,
		).to_payload()
		historical_grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-historical-request-2",
			"trace_request_id": "grounded-historical-trace-2",
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
		historical_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "grounded-historical-trace-2",
			"family_id": "entity_detail",
			"source_reports": ["Ko Nay Lin Mobile Center Detail"],
			"artifact_type": "normalized_family_artifact",
			"dimensions": {
				"entity_type": "customer",
				"entity_label": "Ko Nay Lin Mobile Center",
				"entity_key": "Ko Nay Lin Mobile Center",
			},
		}
		current_grounded_turn_payload = {
			"type": "qwen_grounded_turn_context",
			"contract_version": "1.0",
			"request_id": "grounded-new-request-2",
			"trace_request_id": "grounded-new-trace-2",
			"grounded": True,
			"source_name": "Payment Entry List",
			"artifact_family_id": "transaction_listing",
			"artifact_source_reports": ["Payment Entry List"],
		}
		current_artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "grounded-new-trace-2",
			"family_id": "transaction_listing",
			"source_reports": ["Payment Entry List"],
			"artifact_type": "normalized_family_artifact",
			"dimensions": {
				"listing_view": "payment_entry",
			},
		}
		session_doc = _FakeSessionDoc(
			[
				_FakeMessage(role="tool", content=json.dumps(recovery_payload)),
				_FakeMessage(role="tool", content=json.dumps(accepted_repair_payload)),
				_FakeMessage(role="tool", content=json.dumps(historical_grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(historical_artifact_payload)),
				_FakeMessage(role="tool", content=json.dumps(current_grounded_turn_payload)),
				_FakeMessage(role="tool", content=json.dumps(current_artifact_payload)),
			]
		)

		snapshot = _build_conversation_state_snapshot(
			request_id="snapshot-resumable-prior-2",
			session_doc=session_doc,
		)
		recent_focus = snapshot.get("recent_focus") or {}
		prior_branch = snapshot.get("resumable_prior_request") or {}

		self.assertEqual(str(recent_focus.get("focus_grain") or "").strip(), "payment_entry")
		self.assertTrue(bool(prior_branch.get("available")))
		self.assertEqual(str(prior_branch.get("branch_kind") or "").strip(), "accepted_recovery_origin")
		self.assertEqual(str(prior_branch.get("branch_label") or "").strip(), "Top Customers by Revenue")
		self.assertEqual(
			int(prior_branch.get("source_tool_index")) if prior_branch.get("source_tool_index") is not None else -1,
			4,
		)
		self.assertEqual(
			str(prior_branch.get("derivation_basis") or "").strip(),
			"accepted_repair_with_newer_grounded_turn",
		)
		self.assertEqual(
			str(((prior_branch.get("internal_details") or {}).get("arbitration_basis")) or "").strip(),
			"accepted_repair_precedes_historical_prior_focus_by_newer_index",
		)

	def test_select_resumable_prior_request_candidate_defaults_accepted_repair_when_peer_precedence_is_indeterminate(self):
		selected = _select_resumable_prior_request_candidate(
			accepted_repair_candidate={
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"source_tool_index": -1,
				"internal_details": {"accepted": True},
			},
			historical_candidate={
				"available": True,
				"branch_kind": "prior_recent_focus_origin",
				"source_tool_index": -1,
				"internal_details": {"historical": True},
			},
		)

		self.assertEqual(str(selected.get("branch_kind") or "").strip(), "accepted_recovery_origin")
		self.assertEqual(
			str(((selected.get("internal_details") or {}).get("arbitration_basis")) or "").strip(),
			"accepted_repair_defaults_when_peer_precedence_is_indeterminate",
		)

	def test_select_resumable_prior_request_candidate_prefers_historical_when_known_over_unindexed(self):
		selected = _select_resumable_prior_request_candidate(
			accepted_repair_candidate={
				"available": True,
				"branch_kind": "accepted_recovery_origin",
				"source_tool_index": -1,
			},
			historical_candidate={
				"available": True,
				"branch_kind": "prior_recent_focus_origin",
				"source_tool_index": 7,
			},
		)

		self.assertEqual(str(selected.get("branch_kind") or "").strip(), "prior_recent_focus_origin")
		self.assertEqual(
			str(((selected.get("internal_details") or {}).get("arbitration_basis")) or "").strip(),
			"historical_prior_focus_precedes_accepted_repair_by_known_over_unindexed",
		)

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
		signal = _clarification_signal(request_id="clarify-3", user_question="Which item do you mean?")
		state = build_pending_clarification_state(
			signal,
			attempt_count=2,
			max_attempts=3,
		)
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

	def test_artifact_evidence_clarification_resolution_stays_grounded(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="artifact-evidence-clarification-1",
			mode="new_query",
			requested_modes=[],
			target_dimension="",
			target_metric="",
			target_capability_id="",
			target_report="",
			depends_on_grounded_turn=False,
			self_contained=True,
			latest_grounded_turn_available=True,
			reason="The user asks a generic artifact question that needs a governed clarification.",
		)

		preserved = _preserve_current_artifact_direct_evidence_followup_resolution(
			request_id="artifact-evidence-clarification-1",
			followup_resolution=followup_resolution,
			evidence_request_contract={
				"entity_type": "customer",
				"entity_question_type": "customer_tenure",
				"clarification_required": True,
				"clarification_reason_type": "customer_tenure_basis_missing",
			},
			direct_evidence_answer="I can calculate customer tenure using one of three date bases.",
			evidence_boundary_answer="",
			latest_grounded_turn_available=True,
		)

		self.assertEqual(preserved.mode, "grounded_follow_up")
		self.assertEqual(preserved.target_capability_id, "")
		self.assertIn("entity_detail_evidence", list(preserved.requested_modes))
		self.assertTrue(preserved.depends_on_grounded_turn)
		self.assertFalse(preserved.self_contained)

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
		self.assertIn(str(contract.matched_by or "").strip(), {"exact_token_alias", "fuzzy_alias"})

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

	def test_composite_row_evidence_preempts_frontdoor_without_entity_detail_contract(self):
		artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"family_id": "customer_entity_detail",
			"source_reports": ["Customer Risk As-Of"],
			"period": {"as_of_date": "2026-04-27"},
			"filters": {"composite_family_id": "customer_risk_as_of", "as_of_date": "2026-04-27"},
			"dimensions": {
				"source_composite_family_id": "customer_risk_as_of",
				"source_composite_family_label": "Customer Risk As-Of",
				"source_composite_primary_metric_id": "overdue_amount",
				"source_composite_secondary_metric_ids": [
					"outstanding_amount",
					"overdue_ratio",
					"credit_utilization",
				],
			},
			"sections": {
				"ranked_rows": [
					{
						"rank": 1,
						"entity": "35th Street Mobile Wholesale",
						"customer": "35th Street Mobile Wholesale",
						"overdue_amount": 60212000.0,
						"outstanding_amount": 86837000.0,
						"credit_utilization": 0.6203,
						"aging_buckets": [
							{"bucket": "0-30", "amount": 24315000.0},
							{"bucket": "31-60", "amount": 60212000.0},
						],
					},
					{
						"rank": 2,
						"entity": "Ko Nay Lin Mobile Center",
						"customer": "Ko Nay Lin Mobile Center",
						"overdue_amount": 37335000.0,
						"outstanding_amount": 63125000.0,
						"credit_utilization": 0.8417,
					},
				]
			},
		}
		grounded_turn = {
			"source_name": "Customer Risk As-Of",
			"known_entities": [
				{"entity_type": "customer", "name": "35th Street Mobile Wholesale", "rank": 1},
				{"entity_type": "customer", "name": "Ko Nay Lin Mobile Center", "rank": 2},
			],
		}

		self.assertTrue(
			_artifact_local_refinement_has_grounded_evidence(
				request_id="risk-row-evidence-preempt",
				message="show me the aging breakdown for the first customer",
				latest_grounded_turn=grounded_turn,
				latest_family_artifact=artifact_payload,
			)
		)

		defer_runtime_value_frontdoor, semantic_candidate = _artifact_local_refinement_should_defer_runtime_frontdoor(
			request_id="risk-row-evidence-preempt",
			session_id="risk-session",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="why is the first customer risky?",
			recent_messages=[],
			latest_grounded_turn=grounded_turn,
			latest_family_artifact=artifact_payload,
			latest_assistant_payload={},
		)

		self.assertTrue(defer_runtime_value_frontdoor)
		self.assertIsNone(semantic_candidate)

	def test_blocked_advisory_question_preempts_composite_frontdoor_with_policy_boundary(self):
		artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"family_id": "customer_entity_detail",
			"source_reports": ["Customer Risk As-Of"],
			"period": {"as_of_date": "2026-04-27"},
			"filters": {"composite_family_id": "customer_risk_as_of", "as_of_date": "2026-04-27"},
			"dimensions": {
				"source_composite_family_id": "customer_risk_as_of",
				"source_composite_family_label": "Customer Risk As-Of",
				"source_composite_primary_metric_id": "overdue_amount",
			},
			"sections": {
				"ranked_rows": [
					{
						"rank": 1,
						"entity": "35th Street Mobile Wholesale",
						"customer": "35th Street Mobile Wholesale",
						"overdue_amount": 60212000.0,
					}
				]
			},
		}

		self.assertTrue(
			_artifact_local_refinement_has_grounded_evidence(
				request_id="risk-row-evidence-no-advisory",
				message="who should we collect from first?",
				latest_grounded_turn={"source_name": "Customer Risk As-Of"},
				latest_family_artifact=artifact_payload,
			)
		)

	def test_current_artifact_direct_evidence_blocks_requery_upgrade(self):
		self.assertTrue(
			_current_artifact_evidence_should_block_requery(
				direct_evidence_answer="Rank 1 has 60,212,000 MMK overdue.",
				evidence_boundary_answer="",
				latest_grounded_turn_available=True,
			)
		)

		self.assertTrue(
			_current_artifact_evidence_should_block_requery(
				direct_evidence_answer="",
				evidence_boundary_answer="The current artifact cannot prove the requested field.",
				latest_grounded_turn_available=True,
			)
		)

		self.assertFalse(
			_current_artifact_evidence_should_block_requery(
				direct_evidence_answer="",
				evidence_boundary_answer="",
				latest_grounded_turn_available=True,
			)
		)

		self.assertFalse(
			_current_artifact_evidence_should_block_requery(
				direct_evidence_answer="Rank 1 has 60,212,000 MMK overdue.",
				evidence_boundary_answer="",
				latest_grounded_turn_available=False,
			)
		)

	def test_current_artifact_direct_evidence_preserves_context_isolation(self):
		artifact_payload = {
			"type": "qwen_normalized_family_artifact_contract",
			"family_id": "customer_entity_detail",
			"period": {"as_of_date": "2026-04-28"},
			"filters": {"composite_family_id": "customer_risk_as_of", "as_of_date": "2026-04-28"},
			"dimensions": {
				"source_composite_family_id": "customer_risk_as_of",
				"source_composite_family_label": "Customer Risk As-Of",
				"source_composite_primary_metric_id": "overdue_amount",
				"source_composite_secondary_metric_ids": [
					"outstanding_amount",
					"overdue_ratio",
					"credit_utilization",
				],
			},
			"sections": {
				"ranked_rows": [
					{
						"rank": 1,
						"entity": "35th Street Mobile Wholesale",
						"customer": "35th Street Mobile Wholesale",
						"overdue_amount": 60212000.0,
						"outstanding_amount": 86837000.0,
						"aging_buckets": [
							{"bucket": "0-30", "amount": 24315000.0},
							{"bucket": "31-60", "amount": 14820000.0},
						],
					}
				]
			},
		}
		grounded_turn = {
			"source_name": "Customer Risk As-Of",
			"known_entities": [
				{"entity_type": "customer", "name": "35th Street Mobile Wholesale", "rank": 1},
			],
		}
		context_isolation = build_scope_decision_input(
			force_new_query=True,
			out_of_scope=False,
			reason="The request is a self-contained entity-navigation query and should not inherit the current artifact.",
			context_domains=["customer", "receivable"],
		)

		self.assertTrue(
			_current_artifact_evidence_should_preserve_context(
				request_id="risk-row-evidence-preserve-context",
				message="show me the aging breakdown for the first customer",
				context_isolation=context_isolation,
				latest_grounded_turn_available=True,
				latest_grounded_turn=grounded_turn,
				latest_family_artifact=artifact_payload,
			)
		)

	def test_frontdoor_yields_when_current_artifact_evidence_is_available(self):
		self.assertTrue(
			_frontdoor_should_yield_to_current_artifact_evidence(
				entity_drilldown=None,
				artifact_local_refinement_has_grounded_evidence=True,
			)
		)
		self.assertFalse(
			_frontdoor_should_yield_to_current_artifact_evidence(
				entity_drilldown=None,
				artifact_local_refinement_has_grounded_evidence=False,
			)
		)
		self.assertFalse(
			_frontdoor_should_yield_to_current_artifact_evidence(
				entity_drilldown={"source": "explicit_identifier"},
				artifact_local_refinement_has_grounded_evidence=True,
			)
		)

	def test_frontdoor_yields_when_grounded_reasoning_activation_is_authoritative(self):
		accepted_reasoning = types.SimpleNamespace(
			status="accepted",
			intent=types.SimpleNamespace(reasoning_type="interpretation"),
		)
		self.assertTrue(
			_frontdoor_should_yield_to_reasoning_activation(
				reasoning_semantic_result=accepted_reasoning,
				latest_grounded_turn_available=True,
				context_force_new_query=False,
				entity_drilldown=None,
			)
		)
		self.assertFalse(
			_frontdoor_should_yield_to_reasoning_activation(
				reasoning_semantic_result=accepted_reasoning,
				latest_grounded_turn_available=False,
				context_force_new_query=False,
				entity_drilldown=None,
			)
		)
		self.assertFalse(
			_frontdoor_should_yield_to_reasoning_activation(
				reasoning_semantic_result=accepted_reasoning,
				latest_grounded_turn_available=True,
				context_force_new_query=True,
				entity_drilldown=None,
			)
		)
		self.assertFalse(
			_frontdoor_should_yield_to_reasoning_activation(
				reasoning_semantic_result=accepted_reasoning,
				latest_grounded_turn_available=True,
				context_force_new_query=False,
				entity_drilldown={"source": "explicit_identifier"},
			)
		)

	def test_current_artifact_evidence_does_not_preserve_out_of_scope_isolation(self):
		context_isolation = build_scope_decision_input(
			force_new_query=True,
			out_of_scope=True,
			reason="The request is outside governed ERP scope.",
			context_domains=["customer", "receivable"],
		)

		self.assertFalse(
			_current_artifact_evidence_should_preserve_context(
				request_id="risk-row-evidence-out-of-scope",
				message="show me the aging breakdown for the first customer",
				context_isolation=context_isolation,
				latest_grounded_turn_available=True,
				latest_grounded_turn={"source_name": "Customer Risk As-Of"},
				latest_family_artifact={
					"family_id": "customer_entity_detail",
					"period": {"as_of_date": "2026-04-28"},
					"filters": {"composite_family_id": "customer_risk_as_of", "as_of_date": "2026-04-28"},
					"dimensions": {
						"source_composite_family_id": "customer_risk_as_of",
						"source_composite_family_label": "Customer Risk As-Of",
						"source_composite_primary_metric_id": "overdue_amount",
					},
					"sections": {
						"ranked_rows": [
							{
								"rank": 1,
								"entity": "35th Street Mobile Wholesale",
								"aging_buckets": [{"bucket": "31-60", "amount": 14820000.0}],
							}
						]
					},
				},
			)
		)

	def test_preserved_direct_evidence_followup_clears_requery_target(self):
		followup_resolution = build_followup_resolution_contract(
			request_id="preserve-direct-evidence",
			mode="capability_requery",
			requested_modes=["column_projection"],
			target_dimension="customer",
			target_limit=0,
			sort_direction="",
			target_metric="overdue_amount",
			requested_columns=["aging_buckets"],
			requested_time_scope="",
			target_capability_id="accounts_receivable_aging",
			target_report="Accounts Receivable Summary",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="The local artifact was missing a requested column.",
		)

		preserved = _preserve_current_artifact_direct_evidence_followup_resolution(
			request_id="preserve-direct-evidence",
			followup_resolution=followup_resolution,
			evidence_request_contract={},
			direct_evidence_answer="35th Street Mobile Wholesale aging breakdown is available.",
			evidence_boundary_answer="",
			latest_grounded_turn_available=True,
		)

		self.assertEqual(str(getattr(preserved, "mode", "") or "").strip(), "grounded_follow_up")
		self.assertIn("direct_evidence_followup", list(getattr(preserved, "requested_modes", []) or []))
		self.assertEqual(str(getattr(preserved, "target_capability_id", "") or "").strip(), "")
		self.assertEqual(str(getattr(preserved, "target_report", "") or "").strip(), "")

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

	def test_pending_item_clarification_uses_explicit_master_data_breakout_when_cross_checks_miss(self):
		signal = _clarification_signal(request_id="clarify-md-explicit-1", user_question="Which item do you mean?")
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

		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-md-explicit-1-response",
				session_id="clarify-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message='do u have customer name similar to "Nay Lin Mobile"?',
				signal_payload=signal,
				clarification_attempt_count=0,
				max_attempts=3,
			)

		self.assertEqual(str(contract.decision or "").strip(), "new_request")

	def test_pending_item_clarification_uses_explicit_master_data_listing_breakout_when_cross_checks_miss(self):
		signal = _clarification_signal(request_id="clarify-md-explicit-2", user_question="Which item do you mean?")
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

		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-md-explicit-2-response",
				session_id="clarify-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me suppliers",
				signal_payload=signal,
				clarification_attempt_count=0,
				max_attempts=3,
			)

		self.assertEqual(str(contract.decision or "").strip(), "new_request")

	def test_pending_item_clarification_uses_explicit_transaction_listing_breakout_when_cross_checks_miss(self):
		signal = _clarification_signal(request_id="clarify-md-explicit-2b", user_question="Which item do you mean?")
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

		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-md-explicit-2b-response",
				session_id="clarify-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me sales invoices",
				signal_payload=signal,
				clarification_attempt_count=0,
				max_attempts=3,
			)

		self.assertEqual(str(contract.decision or "").strip(), "new_request")

	def test_pending_item_clarification_uses_explicit_statement_breakout_when_cross_checks_miss(self):
		signal = _clarification_signal(request_id="clarify-md-explicit-2c", user_question="Which item do you mean?")
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

		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-md-explicit-2c-response",
				session_id="clarify-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me financial statement",
				signal_payload=signal,
				clarification_attempt_count=0,
				max_attempts=3,
			)

		self.assertEqual(str(contract.decision or "").strip(), "new_request")

	def test_pending_item_clarification_option_list_request_stays_on_clarification_path(self):
		signal = _clarification_signal(request_id="clarify-md-explicit-3", user_question="Which item do you mean?")
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

		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._semantic_new_request_detected",
			return_value=False,
		), patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution._frontdoor_new_request_detected",
			return_value=False,
		):
			contract = resolve_pending_clarification_response(
				request_id="clarify-md-explicit-3-response",
				session_id="clarify-session",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me the list that you found",
				signal_payload=signal,
				clarification_attempt_count=0,
				max_attempts=3,
			)

		self.assertEqual(str(contract.decision or "").strip(), "show_options")

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

	def test_governed_composite_followup_ready_family_artifact_carries_analytical_scope_policy(self):
		assembled_rows = [
			{
				"rank": 1,
				"customer": "Zegyo Mobile Supply House",
				"customer_name": "Zegyo Mobile Supply House",
				"metric_values": {
					"revenue": {"value": 9340000.0, "display_value": "9,340,000 MMK"},
					"quantity": {"value": 30.0, "display_value": "30 units"},
				},
				"primary_metric_id": "revenue",
				"row_provenance": [],
				"join_key": {"customer": "Zegyo Mobile Supply House"},
			}
		]
		with patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._execute_component_ranking_artifacts",
			return_value=({}, [{"execution_id": "customer_sales_order_revenue_period_ranking_execution"}], ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._evaluate_composite_compatibility",
			return_value=("compatible", ""),
		), patch(
			"ai_assistant_ui.qwen_chat.governed_composite_runtime_execution._assemble_entity_period_commercial_rows",
			return_value=(assembled_rows, ""),
		):
			response = maybe_build_governed_composite_frontdoor_response(
				request_id="composite-scope-policy-1",
				message="show top 5 customers by revenue for sales orders last month",
				company_name="Mingalar Mobile Distribution Co., Ltd.",
			)

		dimensions = (((response.get("normalized_family_artifact") or {}).get("dimensions")) or {})
		policy = dict(dimensions.get("governed_scope_runtime_policy") or {})
		self.assertEqual(str((response.get("normalized_family_artifact") or {}).get("family_id") or "").strip(), "ranking_analytics")
		self.assertEqual(str(dimensions.get("scope_id") or "").strip(), "sales_ranking")
		self.assertEqual(str(dimensions.get("scope_class") or "").strip(), "ranked_entities")
		self.assertEqual(str(policy.get("family_id") or "").strip(), "ranking_analytics")
		self.assertEqual(str(policy.get("scope_id") or "").strip(), "sales_ranking")
		self.assertEqual(str(policy.get("scope_class") or "").strip(), "ranked_entities")
		self.assertEqual(str(policy.get("compatibility_level") or "").strip(), "full_consumption")

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
