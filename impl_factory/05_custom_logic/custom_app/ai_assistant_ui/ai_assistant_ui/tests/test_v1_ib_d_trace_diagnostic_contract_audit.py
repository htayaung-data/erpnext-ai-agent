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
	"LEAK_D3_SELECTED_ANSWER",
	"LEAK_D3_ROWS",
	"LEAK_D3_ARTIFACT",
	"LEAK_D3_RENDERED",
	"LEAK_D3_NARRATIVE",
	"LEAK_D3_GROUNDED",
	"LEAK_D3_HELPER",
	"LEAK_D3_REASONING_DRAFT",
	"LEAK_D3_COMPILED_ROWS",
	"LEAK_D3_REQUERY_ROWS",
	"LEAK_D3_VISIBLE_CONTEXT",
	"LEAK_D3_NBU_SHADOW",
	"LEAK_D3_RAW_UNSAFE_PROMPT",
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


def _blocked_boundary(message: str):
	return {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"contract_version": "test-v1-ib-d-3",
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
		"decision_intent": True,
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
		"type": "qwen_legacy_user_intent_boundary",
		"required_answer_mode": ANSWER_MODE_GOVERNED_ERP,
		"context_reuse_allowed": True,
		"report_routing_allowed": True,
		"model_reasoning_allowed": True,
		"final_emission_allowed": True,
	}


def _snapshot_with_sensitive_diagnostics():
	return {
		"latest_grounded_turn": {
			"grounded": True,
			"payload": {
				"type": "qwen_grounded_turn_context",
				"grounded": True,
				"source_kind": "report",
				"source_name": "LEAK_D3_GROUNDED",
				"artifact_family_id": "LEAK_D3_ARTIFACT",
				"rows": ["LEAK_D3_ROWS"],
			},
		},
		"latest_artifact": {
			"payload": {
				"type": "qwen_normalized_family_artifact_contract",
				"family_id": "LEAK_D3_ARTIFACT",
				"rows": ["LEAK_D3_ROWS"],
				"artifact": "LEAK_D3_ARTIFACT",
				"rendered_payload": "LEAK_D3_RENDERED",
				"narrative": "LEAK_D3_NARRATIVE",
			}
		},
		"recent_focus": {
			"payload": {
				"type": "qwen_recent_focus_context",
				"helper_payload": "LEAK_D3_HELPER",
			}
		},
	}


class V1IBDTraceDiagnosticContractAuditTests(unittest.TestCase):
	def run_blocked_service(self, message: str):
		session = _FakeSession()
		calls = {"visible": 0, "reasoning": 0, "compiled": 0, "requery": 0}

		def visible(**_kwargs):
			calls["visible"] += 1
			return True, {"ok": True, "mode": "visible_context_answer", "answer": "LEAK_D3_VISIBLE_CONTEXT"}

		def reasoning(**_kwargs):
			calls["reasoning"] += 1
			return True, {"ok": True, "mode": "model_reasoning_answer", "answer": "LEAK_D3_REASONING_DRAFT"}

		def compiled(**_kwargs):
			calls["compiled"] += 1
			return True, {"ok": True, "mode": "compiled_first_turn", "rows": ["LEAK_D3_COMPILED_ROWS"]}

		def requery(**_kwargs):
			calls["requery"] += 1
			return True, {"ok": True, "mode": "compiled_first_turn", "rows": ["LEAK_D3_REQUERY_ROWS"]}

		patches = [
			mock.patch.object(service.frappe, "get_doc", lambda *_args, **_kwargs: session),
			mock.patch.object(service, "build_v1_ib_runtime_boundary", lambda raw: _blocked_boundary(raw)),
			mock.patch.object(service, "build_user_intent_boundary_contract", lambda _raw: _legacy_allow()),
			mock.patch.object(service, "_build_conversation_state_snapshot", lambda **_kwargs: _snapshot_with_sensitive_diagnostics()),
			mock.patch.object(service, "_latest_normalized_family_artifact", lambda *_args, **_kwargs: {}),
			mock.patch.object(service, "_latest_grounded_assistant_context", lambda _session: ({}, {})),
			mock.patch.object(service, "_latest_assistant_payload", lambda _session: {"text": "LEAK_D3_SELECTED_ANSWER"}),
			mock.patch.object(service, "_latest_reasoning_contract", lambda _session: {}),
			mock.patch.object(service, "_source_compatible_reasoning_contract", lambda **_kwargs: {}),
			mock.patch.object(service, "get_clarification_state", lambda _session: {}),
			mock.patch.object(service, "_build_conversation_control_evidence_contract", lambda **_kwargs: _PayloadObject(payload={"type": "control_evidence"})),
			mock.patch.object(service, "_strip_leading_control_discard_preamble", lambda _raw: ""),
			mock.patch.object(service, "_build_prior_branch_restore_contract_from_snapshot", lambda **_kwargs: None),
			mock.patch.object(service, "_conversation_control_decision_from_prior_branch_restore_contract", lambda _contract: None),
			mock.patch.object(service, "_prior_branch_restore_runtime_override_message", lambda _contract: ""),
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
				_PayloadObject(handle_in_front_door=True, response_payload={"report": "LEAK_D3_SELECTED_ANSWER"}, payload={"type": "frontdoor_contract"}),
				None,
				"LEAK_D3_SELECTED_ANSWER",
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
				session_name="session-v1-ib-d-3",
				message=message,
				user="Administrator",
			)
		return session, payload, calls, ok

	def tool_payload_text(self, session):
		return json.dumps(
			[row.get("content") for row in session.messages if row.get("role") == "tool"],
			sort_keys=True,
			default=str,
		)

	def parsed_tool_payloads(self, session):
		payloads = []
		for row in session.messages:
			if row.get("role") != "tool":
				continue
			content = row.get("content")
			if isinstance(content, dict):
				payloads.append(content)
				continue
			try:
				parsed = json.loads(content)
			except Exception:
				continue
			if isinstance(parsed, dict):
				payloads.append(parsed)
		return payloads

	def assert_no_diagnostic_leaks(self, session):
		tool_payload_text = self.tool_payload_text(session)
		leaked_markers = [marker for marker in LEAK_MARKERS if marker in tool_payload_text]
		self.assertEqual([], leaked_markers)

	def assert_blocked_raw_messages_redacted(self, session):
		payloads = self.parsed_tool_payloads(session)
		by_type = {payload.get("type"): payload for payload in payloads if isinstance(payload, dict)}
		for payload_type in (
			"qwen_interaction_contract",
			"qwen_natural_business_understanding_trace_contract",
		):
			with self.subTest(payload_type=payload_type):
				payload = by_type.get(payload_type) or {}
				self.assertEqual(payload.get("raw_message"), "[redacted_by_v1_ib]")
				self.assertTrue(payload.get("raw_message_hash"))
				self.assertTrue(payload.get("normalized_message_hash"))
				self.assertEqual(payload.get("trace_redaction_status"), "safe")
				self.assertEqual(payload.get("redaction_reason"), "v1_ib_blocked_turn_diagnostic_redaction")

	def test_blocked_pre_routing_trace_and_tool_payloads_do_not_leak_business_markers(self):
		message = "LEAK_D3_RAW_UNSAFE_PROMPT Show item sales and tell me whether to discount it"
		session, payload, calls, ok = self.run_blocked_service(message)

		self.assertTrue(ok)
		self.assertEqual(payload.get("mode"), "user_intent_boundary")
		self.assertEqual(calls, {"visible": 0, "reasoning": 0, "compiled": 0, "requery": 0})
		self.assert_no_diagnostic_leaks(session)
		self.assert_blocked_raw_messages_redacted(session)
		boundary = (payload.get("agent_meta") or {}).get("user_intent_boundary") or {}
		self.assertFalse(boundary.get("report_routing_allowed"))
		self.assertFalse(boundary.get("context_reuse_allowed"))
		self.assertFalse(boundary.get("model_reasoning_allowed"))
		self.assertFalse(boundary.get("final_emission_allowed"))


if __name__ == "__main__":
	unittest.main()
