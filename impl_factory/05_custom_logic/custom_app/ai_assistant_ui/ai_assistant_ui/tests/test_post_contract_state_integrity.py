import json
import unittest
from dataclasses import dataclass
from typing import Any, Dict, List
from unittest.mock import patch

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
from ai_assistant_ui.qwen_chat.clarification_state import (
	build_pending_clarification_state,
	clarification_state_from_storage,
	get_clarification_state,
)
from ai_assistant_ui.qwen_chat.clarification_resolution import clarification_state_after_unresolved_attempt
from ai_assistant_ui.qwen_chat.contracts import (
	build_artifact_enrichment_recovery_contract,
	build_conversational_repair_intent_contract,
)
from ai_assistant_ui.qwen_chat.service import (
	_latest_normalized_family_artifact,
	_latest_grounded_turn_contract,
	_latest_recovery_contract,
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

	def test_customer_scope_clarification_can_resume_from_customer_name(self):
		signal = _clarification_signal(request_id="clarify-customer-scope", user_question="Which customer do you want?")
		signal["reason_type"] = "customer_scope_missing"
		signal["suggested_options"] = []
		signal["internal_details"] = {
			"continuation_lane": "front_door",
			"continuation_intent_class": "governed_kpi_value",
			"resolved_message_template": "show customer tenure by customer created date for {customer} as of 2026-04-10",
		}

		with patch(
			"ai_assistant_ui.qwen_chat.clarification_resolution.resolve_customer_scope_from_message",
			return_value={
				"customer": "Zegyo Mobile Supply House",
				"customer_name": "Zegyo Mobile Supply House",
				"entity_name": "Zegyo Mobile Supply House",
				"entity_label": "Zegyo Mobile Supply House",
				"has_customer_scope": True,
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
		self.assertEqual(str(contract.matched_by or "").strip(), "customer_scope")
		self.assertEqual(
			clarification_resolved_continuation_message(
				signal_payload=signal,
				resolved_option=str(contract.resolved_option or "").strip(),
			),
			"show customer tenure by customer created date for Zegyo Mobile Supply House as of 2026-04-10",
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
