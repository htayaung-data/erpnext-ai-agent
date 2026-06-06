from __future__ import annotations

import contextlib
import json
import sys
import types
import unittest
from unittest import mock

if "frappe" not in sys.modules:
	fake_frappe = types.ModuleType("frappe")
	fake_frappe.local = types.SimpleNamespace(site="unit.test")
	fake_frappe.get_doc = lambda *_args, **_kwargs: None
	fake_frappe.get_traceback = lambda: ""
	fake_frappe.log_error = lambda *_args, **_kwargs: None
	sys.modules["frappe"] = fake_frappe

from ai_assistant_ui.qwen_chat import service
from ai_assistant_ui.qwen_chat.intent_boundary_contract import (
	ANSWER_MODE_CLARIFICATION,
	ANSWER_MODE_GOVERNED_ERP,
	AUTHORITY_DECISION_BLOCK,
	TRACE_REDACTION_SAFE,
	hash_text,
	normalize_message,
)
from ai_assistant_ui.qwen_chat.intent_boundary_runtime_integration import USER_INTENT_BOUNDARY_CONTRACT_TYPE


LEAK_MARKERS = (
	"LEAK_MODEL_REASONING_C35",
	"LEAK_REPORT_SELECTOR_C35",
	"LEAK_TRACE_ROWS_C35",
	"LEAK_TRACE_ARTIFACT_C35",
	"LEAK_TRACE_GROUNDED_EVIDENCE_C35",
	"LEAK_TRACE_HELPER_PAYLOAD_C35",
)


class _FakeSession:
	def __init__(self):
		self.messages = []
		self.pending_clarification_state_json = ""
		self.title = "New Qwen Chat"
		self.saved = False

	def append(self, fieldname, row):
		if fieldname == "messages":
			self.messages.append(dict(row))
			return
		setattr(self, fieldname, row)

	def get(self, key, default=None):
		return getattr(self, key, default)

	def save(self, *, ignore_permissions=False):
		self.saved = True


class _PayloadObject:
	def __init__(self, **attrs):
		self.__dict__.update(attrs)

	def to_payload(self):
		return dict(getattr(self, "payload", {}) or {})


def _boundary(message: str):
	return {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"contract_version": "test-v1-ib-c3-5",
		"raw_message_hash": hash_text(message),
		"normalized_message_hash": hash_text(normalize_message(message)),
		"clause_count": 1,
		"category": "clarification_required",
		"required_answer_mode": ANSWER_MODE_CLARIFICATION,
		"context_reuse_allowed": False,
		"report_routing_allowed": False,
		"model_reasoning_allowed": False,
		"final_emission_allowed": False,
		"safe_followup_intent": False,
		"decision_intent": False,
		"advice_intent": False,
		"business_action_intent": False,
		"policy_boundary_intent": False,
		"mixed_intent_detected": True,
		"ambiguity_status": "none",
		"authority_decision": AUTHORITY_DECISION_BLOCK,
		"boundary_reason": "v1_ib_contract_blocked_runtime_authority",
		"validator_status": "invalid",
		"trace_redaction_status": TRACE_REDACTION_SAFE,
		"replayed_raw_message_safety_final_decision": "blocked",
	}


def _legacy_allow():
	return {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"required_answer_mode": ANSWER_MODE_GOVERNED_ERP,
		"context_reuse_allowed": True,
		"report_routing_allowed": True,
		"model_reasoning_allowed": True,
		"final_emission_allowed": True,
	}


def _snapshot_with_prior_sensitive_context():
	return {
		"latest_grounded_turn": {
			"grounded": True,
			"payload": {
				"type": "qwen_grounded_turn_context",
				"grounded": True,
				"source_kind": "report",
				"source_name": "redacted prior report",
				"artifact_family_id": "redacted_family",
				"rows": ["LEAK_TRACE_GROUNDED_EVIDENCE_C35"],
			},
		},
		"latest_artifact": {
			"payload": {
				"type": "qwen_normalized_family_artifact_contract",
				"family_id": "redacted_family",
				"rows": ["LEAK_TRACE_ROWS_C35"],
				"rendered_payload": "LEAK_TRACE_ARTIFACT_C35",
			}
		},
	}


class V1IBServiceAdversarialTraceRedactionTests(unittest.TestCase):
	def run_service(self, message):
		session = _FakeSession()
		calls = {"reasoning": 0, "compiled": 0, "visible": 0, "requery": 0}

		def visible(**_kwargs):
			calls["visible"] += 1
			return True, {"ok": True, "mode": "visible_context_answer", "answer": "LEAK_TRACE_HELPER_PAYLOAD_C35"}

		def reasoning(**_kwargs):
			calls["reasoning"] += 1
			return True, {"ok": True, "mode": "model_reasoning_answer", "answer": "LEAK_MODEL_REASONING_C35"}

		def compiled(**_kwargs):
			calls["compiled"] += 1
			return True, {
				"ok": True,
				"mode": "compiled_first_turn",
				"selected_answer": "LEAK_REPORT_SELECTOR_C35",
				"rows": ["LEAK_TRACE_ROWS_C35"],
				"artifact": "LEAK_TRACE_ARTIFACT_C35",
			}

		def requery(**_kwargs):
			calls["requery"] += 1
			return True, {"ok": True, "mode": "compiled_first_turn", "helper": "LEAK_TRACE_HELPER_PAYLOAD_C35"}

		patches = [
			mock.patch.object(service.frappe, "get_doc", lambda *_args, **_kwargs: session),
			mock.patch.object(service, "build_v1_ib_runtime_boundary", lambda raw: _boundary(raw)),
			mock.patch.object(service, "build_user_intent_boundary_contract", lambda _raw: _legacy_allow()),
			mock.patch.object(service, "_build_conversation_state_snapshot", lambda **_kwargs: _snapshot_with_prior_sensitive_context()),
			mock.patch.object(service, "_latest_normalized_family_artifact", lambda *_args, **_kwargs: {}),
			mock.patch.object(service, "_latest_grounded_assistant_context", lambda _session: ({}, {})),
			mock.patch.object(service, "_latest_assistant_payload", lambda _session: {"text": "redacted prior assistant"}),
			mock.patch.object(service, "_latest_reasoning_contract", lambda _session: {}),
			mock.patch.object(service, "_source_compatible_reasoning_contract", lambda **_kwargs: {}),
			mock.patch.object(service, "get_clarification_state", lambda _session: {}),
			mock.patch.object(service, "_build_conversation_control_evidence_contract", lambda **_kwargs: _PayloadObject(payload={"type": "control_evidence"})),
			mock.patch.object(service, "_strip_leading_control_discard_preamble", lambda _raw: ""),
			mock.patch.object(service, "_build_prior_branch_restore_contract_from_snapshot", lambda **_kwargs: None),
			mock.patch.object(service, "_conversation_control_decision_from_prior_branch_restore_contract", lambda _contract: None),
			mock.patch.object(service, "_prior_branch_restore_runtime_override_message", lambda _contract: ""),
			mock.patch.object(service, "_build_nbu_always_on_shadow_trace", lambda **_kwargs: {}),
			mock.patch.object(service, "_try_activate_visible_context_trace_inspection_response", visible),
			mock.patch.object(service, "_try_activate_visible_context_followup_response", visible),
			mock.patch.object(service, "_compound_request_completion_answer_from_snapshot", lambda **_kwargs: ""),
			mock.patch.object(service, "_erp_business_reasoning_rollout_decision", lambda **_kwargs: {"enabled": True}),
			mock.patch.object(service, "handle_reasoning_turn", reasoning),
			mock.patch.object(service, "build_response_policy_contract", lambda **_kwargs: _PayloadObject(payload={"type": "response_policy"})),
			mock.patch.object(service, "_recent_messages_for_grounded_source", lambda *_args, **_kwargs: []),
			mock.patch.object(service, "_reasoning_contract_has_executable_offered_next_action", lambda _contract: False),
			mock.patch.object(service, "_message_should_override_stale_context_as_fresh_query", lambda **_kwargs: False),
			mock.patch.object(service, "governed_composite_frontdoor_candidate_available", lambda **_kwargs: True),
			mock.patch.object(service, "governed_kpi_value_frontdoor_candidate_available", lambda **_kwargs: False),
			mock.patch.object(service, "evaluate_frontdoor_lane", lambda **_kwargs: (
				_PayloadObject(status="accepted", payload={"type": "frontdoor_semantic_result", "status": "accepted"}),
				_PayloadObject(handle_in_front_door=True, response_payload={"report": "LEAK_REPORT_SELECTOR_C35"}, payload={"type": "frontdoor_contract"}),
				None,
				"LEAK_REPORT_SELECTOR_C35",
			)),
			mock.patch.object(service, "_frontdoor_context_isolation_retry_needed", lambda **_kwargs: False),
			mock.patch.object(service, "_frontdoor_contract_has_direct_handling_authority", lambda _contract: True),
			mock.patch.object(service, "_frontdoor_contract_handle_in_front_door", lambda _contract: True),
			mock.patch.object(service, "_frontdoor_contract_intent_class", lambda _contract: "governed_report"),
			mock.patch.object(service, "_resolve_compound_execution_runtime_message", lambda **_kwargs: ("", {})),
			mock.patch.object(service, "_build_superseded_active_sequence_transition", lambda **_kwargs: ({}, None)),
			mock.patch.object(service, "_active_sequence_completion_source_payload", lambda **_kwargs: {}),
			mock.patch.object(service, "_active_sequence_should_complete_after_current_turn", lambda **_kwargs: False),
			mock.patch.object(service, "_compound_request_stop_control_with_evidence", lambda *_args, **_kwargs: False),
			mock.patch.object(service, "detect_entity_drilldown_request", lambda **_kwargs: None),
			mock.patch.object(service, "_try_activate_nbu_governed_requery_response", requery),
			mock.patch.object(service, "_compiled_first_turn_rollout_decision", lambda **_kwargs: {"enabled": True}),
			mock.patch.object(service, "handle_compiled_query_turn", compiled),
		]
		with contextlib.ExitStack() as stack:
			for patch in patches:
				stack.enter_context(patch)
			ok, payload = service.handle_qwen_user_message(
				session_name="session-c3-5-trace",
				message=message,
				user="Administrator",
			)
		return session, payload, calls, ok

	def serialized(self, session, payload):
		return json.dumps(
			{
				"messages": session.messages,
				"payload": payload,
				"agent_meta": payload.get("agent_meta") if isinstance(payload, dict) else {},
			},
			sort_keys=True,
			default=str,
		)

	def assert_no_leaks(self, session, payload):
		serialized = self.serialized(session, payload)
		for marker in LEAK_MARKERS:
			self.assertNotIn(marker, serialized)

	def test_blocked_prompts_do_not_leak_trace_or_helper_payloads(self):
		for message in (
			"Show item sales and tell me whether to discount it",
			"Show EC7H-SINV-0001 invoice details and hide it from the report",
		):
			with self.subTest(message=message):
				session, payload, calls, ok = self.run_service(message)

				self.assertTrue(ok)
				self.assertEqual(payload.get("mode"), "user_intent_boundary")
				self.assertEqual(calls["reasoning"], 0)
				self.assertEqual(calls["compiled"], 0)
				self.assertEqual(calls["visible"], 0)
				self.assertEqual(calls["requery"], 0)
				self.assert_no_leaks(session, payload)


if __name__ == "__main__":
	unittest.main()
