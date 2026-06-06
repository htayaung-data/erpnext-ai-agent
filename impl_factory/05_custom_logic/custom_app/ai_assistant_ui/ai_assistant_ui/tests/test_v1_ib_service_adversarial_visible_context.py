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
	AUTHORITY_DECISION_ALLOW_REPORT,
	AUTHORITY_DECISION_BLOCK,
	TRACE_REDACTION_SAFE,
	hash_text,
	normalize_message,
)
from ai_assistant_ui.qwen_chat.intent_boundary_runtime_integration import USER_INTENT_BOUNDARY_CONTRACT_TYPE


LEAK_MARKERS = (
	"LEAK_SERVICE_SELECTED_ANSWER_C34",
	"LEAK_SERVICE_ERP_ROWS_C34",
	"LEAK_SERVICE_REPORT_PAYLOAD_C34",
	"LEAK_SERVICE_RENDERED_PAYLOAD_C34",
	"LEAK_SERVICE_ARTIFACT_C34",
	"LEAK_SERVICE_NARRATIVE_C34",
	"LEAK_SERVICE_GROUNDED_EVIDENCE_C34",
	"LEAK_SERVICE_HELPER_PAYLOAD_C34",
	"LEAK_STALE_VISIBLE_CONTEXT_C34A",
)


class _FakeSession:
	def __init__(self):
		self.messages = []
		self.pending_clarification_state_json = ""
		self.saved = False

	def append(self, fieldname, row):
		if fieldname != "messages":
			setattr(self, fieldname, row)
			return
		self.messages.append(dict(row))

	def get(self, key, default=None):
		return getattr(self, key, default)

	def save(self, *, ignore_permissions=False):
		self.saved = True


class _PayloadObject:
	def __init__(self, **attrs):
		self.__dict__.update(attrs)

	def to_payload(self):
		return dict(getattr(self, "payload", {}) or {})


def _boundary(
	message: str,
	*,
	allow_context=False,
	allow_report=False,
	raw_hash_override=None,
	normalized_hash_override=None,
	trace_redaction_status=TRACE_REDACTION_SAFE,
):
	allowed = bool(allow_context or allow_report)
	return {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"contract_version": "test-v1-ib-c3-4",
		"raw_message_hash": raw_hash_override or hash_text(message),
		"normalized_message_hash": normalized_hash_override or hash_text(normalize_message(message)),
		"clause_count": 1,
		"category": "true_visible_context_followup" if allow_context else "factual_erp_query" if allow_report else "clarification_required",
		"required_answer_mode": ANSWER_MODE_GOVERNED_ERP if allowed else ANSWER_MODE_CLARIFICATION,
		"context_reuse_allowed": bool(allow_context),
		"report_routing_allowed": bool(allow_report),
		"model_reasoning_allowed": bool(allow_report),
		"final_emission_allowed": allowed,
		"safe_followup_intent": bool(allow_context),
		"decision_intent": False,
		"advice_intent": False,
		"business_action_intent": False,
		"policy_boundary_intent": False,
		"mixed_intent_detected": False,
		"ambiguity_status": "none",
		"authority_decision": AUTHORITY_DECISION_ALLOW_REPORT if allowed else AUTHORITY_DECISION_BLOCK,
		"boundary_reason": "validated_visible_context_followup" if allow_context else "validated_safe_factual_intent" if allow_report else "v1_ib_contract_blocked_runtime_authority",
		"validator_status": "valid" if allowed else "invalid",
		"trace_redaction_status": trace_redaction_status,
		"replayed_raw_message_safety_final_decision": "safe" if allowed else "blocked",
	}


def _legacy_allow():
	return {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"category": "factual_erp_query",
		"required_answer_mode": ANSWER_MODE_GOVERNED_ERP,
		"context_reuse_allowed": True,
		"report_routing_allowed": True,
		"boundary_reason": "legacy_allows",
	}


def _snapshot_with_prior_context():
	return {
		"latest_grounded_turn": {
			"grounded": True,
			"payload": {
				"type": "qwen_grounded_turn_context",
				"grounded": True,
				"source_kind": "report",
				"source_name": "Supplier Payable Status",
				"artifact_family_id": "payable_status",
			},
		},
		"latest_artifact": {
			"payload": {
				"type": "qwen_normalized_family_artifact_contract",
				"family_id": "payable_status",
			}
		},
	}


def _frontdoor_result():
	return (
		_PayloadObject(status="rejected", payload={"type": "frontdoor_semantic_result", "status": "rejected"}),
		_PayloadObject(handle_in_front_door=False, response_payload={}, payload={"type": "frontdoor_contract"}),
		None,
		"",
	)


class V1IBServiceAdversarialVisibleContextTests(unittest.TestCase):
	def run_service(self, message, boundary, *, prior_context=True, trace_result=(False, None), visible_result=(False, None)):
		session = _FakeSession()
		calls = {"trace_visible": 0, "visible_followup": 0, "compiled": 0}

		def trace_visible(**_kwargs):
			calls["trace_visible"] += 1
			return trace_result

		def visible_followup(**_kwargs):
			calls["visible_followup"] += 1
			return visible_result

		def compiled(**_kwargs):
			calls["compiled"] += 1
			raise AssertionError("report routing must not run in visible-context test")

		patches = [
			mock.patch.object(service.frappe, "get_doc", lambda *_args, **_kwargs: session),
			mock.patch.object(service, "build_v1_ib_runtime_boundary", lambda _raw: dict(boundary)),
			mock.patch.object(service, "build_user_intent_boundary_contract", lambda _raw: _legacy_allow()),
			mock.patch.object(service, "_build_conversation_state_snapshot", lambda **_kwargs: _snapshot_with_prior_context() if prior_context else {}),
			mock.patch.object(service, "_latest_normalized_family_artifact", lambda *_args, **_kwargs: {}),
			mock.patch.object(service, "_latest_grounded_assistant_context", lambda _session: ({}, {})),
			mock.patch.object(service, "_latest_assistant_payload", lambda _session: {}),
			mock.patch.object(service, "_latest_reasoning_contract", lambda _session: {}),
			mock.patch.object(service, "_source_compatible_reasoning_contract", lambda **_kwargs: {}),
			mock.patch.object(service, "get_clarification_state", lambda _session: {}),
			mock.patch.object(service, "_build_conversation_control_evidence_contract", lambda **_kwargs: _PayloadObject(payload={"type": "control_evidence"})),
			mock.patch.object(service, "_strip_leading_control_discard_preamble", lambda _raw: ""),
			mock.patch.object(service, "_build_prior_branch_restore_contract_from_snapshot", lambda **_kwargs: None),
			mock.patch.object(service, "_conversation_control_decision_from_prior_branch_restore_contract", lambda _contract: None),
			mock.patch.object(service, "_prior_branch_restore_runtime_override_message", lambda _contract: ""),
			mock.patch.object(service, "_build_nbu_always_on_shadow_trace", lambda **_kwargs: {}),
			mock.patch.object(service, "_try_activate_visible_context_trace_inspection_response", trace_visible),
			mock.patch.object(service, "_compound_request_completion_answer_from_snapshot", lambda **_kwargs: ""),
			mock.patch.object(service, "_erp_business_reasoning_rollout_decision", lambda **_kwargs: {"enabled": True}),
			mock.patch.object(service, "build_response_policy_contract", lambda **_kwargs: _PayloadObject(payload={"type": "response_policy"})),
			mock.patch.object(service, "_recent_messages_for_grounded_source", lambda *_args, **_kwargs: []),
			mock.patch.object(service, "_reasoning_contract_has_executable_offered_next_action", lambda _contract: False),
			mock.patch.object(service, "_message_should_override_stale_context_as_fresh_query", lambda **_kwargs: False),
			mock.patch.object(service, "governed_composite_frontdoor_candidate_available", lambda **_kwargs: False),
			mock.patch.object(service, "governed_kpi_value_frontdoor_candidate_available", lambda **_kwargs: False),
			mock.patch.object(service, "evaluate_frontdoor_lane", lambda **_kwargs: _frontdoor_result()),
			mock.patch.object(service, "_frontdoor_context_isolation_retry_needed", lambda **_kwargs: False),
			mock.patch.object(service, "_resolve_compound_execution_runtime_message", lambda **_kwargs: ("", {})),
			mock.patch.object(service, "_build_superseded_active_sequence_transition", lambda **_kwargs: ({}, None)),
			mock.patch.object(service, "_active_sequence_completion_source_payload", lambda **_kwargs: {}),
			mock.patch.object(service, "_active_sequence_should_complete_after_current_turn", lambda **_kwargs: False),
			mock.patch.object(service, "_compound_request_stop_control_with_evidence", lambda *_args, **_kwargs: False),
			mock.patch.object(service, "detect_entity_drilldown_request", lambda **_kwargs: None),
			mock.patch.object(service, "_try_activate_visible_context_followup_response", visible_followup),
			mock.patch.object(service, "handle_compiled_query_turn", compiled),
		]
		with contextlib.ExitStack() as stack:
			for patch in patches:
				stack.enter_context(patch)
			ok, payload = service.handle_qwen_user_message(
				session_name="session-c3-4-visible",
				message=message,
				user="Administrator",
			)
		return session, payload, calls, ok

	def serialized_messages(self, session):
		return json.dumps(session.messages, sort_keys=True, default=str)

	def assert_no_business_leaks(self, session):
		serialized = self.serialized_messages(session)
		for marker in LEAK_MARKERS:
			self.assertNotIn(marker, serialized)

	def assert_control_or_boundary_response(self, payload):
		self.assertNotEqual(payload.get("mode"), "visible_context_answer")
		self.assertNotEqual(payload.get("mode"), "compiled_first_turn")
		self.assertEqual(payload.get("mode"), "user_intent_boundary")

	def test_context_reuse_helper_requires_current_raw_message_proof(self):
		message = "Who is second in the previous table?"
		valid = _boundary(message, allow_context=True)
		stale = _boundary("Show EC7H-SUP-A payable status", allow_context=True)
		normalized_mismatch = _boundary(message, allow_context=True, normalized_hash_override=hash_text("different normalized"))
		raw_mismatch = _boundary(message, allow_context=True, raw_hash_override=hash_text("different raw"))
		non_redaction_safe = _boundary(message, allow_context=True, trace_redaction_status="unsafe")
		mixed_intent = _boundary(message, allow_context=True)
		mixed_intent["mixed_intent_detected"] = True
		decision_intent = _boundary(message, allow_context=True)
		decision_intent["decision_intent"] = True

		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(valid))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(valid, raw_message=None))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(valid, raw_message="   "))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(valid, raw_message="Show EC7H-SUP-A payable status"))
		self.assertTrue(service._user_intent_boundary_context_reuse_allowed(valid, raw_message=message))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(stale, raw_message=message))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(normalized_mismatch, raw_message=message))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(raw_mismatch, raw_message=message))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(non_redaction_safe, raw_message=message))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(mixed_intent, raw_message=message))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(decision_intent, raw_message=message))

	def test_unsafe_prompt_after_prior_report_context_does_not_activate_visible_context(self):
		message = "Can we leave it unpaid?"
		session, payload, calls, ok = self.run_service(message, _boundary(message), prior_context=True)

		self.assertTrue(ok)
		self.assertEqual(calls["trace_visible"], 0)
		self.assertEqual(calls["visible_followup"], 0)
		self.assertEqual(calls["compiled"], 0)
		self.assert_control_or_boundary_response(payload)
		self.assert_no_business_leaks(session)

	def test_pronoun_and_context_references_cannot_activate_context_without_v1_ib_allow(self):
		for message in (
			"Should we adjust it?",
			"Can we leave that row out?",
			"Show above and tell me what to do",
		):
			with self.subTest(message=message):
				session, payload, calls, ok = self.run_service(message, _boundary(message), prior_context=True)

				self.assertTrue(ok)
				self.assertEqual(calls["trace_visible"], 0)
				self.assertEqual(calls["visible_followup"], 0)
				self.assert_control_or_boundary_response(payload)
				self.assert_no_business_leaks(session)

	def test_stale_or_mismatched_v1_ib_context_contract_blocks_visible_context(self):
		message = "Who is second in the previous table?"
		stale = _boundary("Show EC7H-SUP-A payable status", allow_context=True)
		mismatched = _boundary(message, allow_context=True, normalized_hash_override=hash_text("different normalized"))
		raw_mismatch = _boundary(message, allow_context=True, raw_hash_override=hash_text("different raw"))
		non_redaction_safe = _boundary(message, allow_context=True, trace_redaction_status="unsafe")
		mixed_intent = _boundary(message, allow_context=True)
		mixed_intent["mixed_intent_detected"] = True
		decision_intent = _boundary(message, allow_context=True)
		decision_intent["decision_intent"] = True
		handled_visible_context_payload = {
			"ok": True,
			"mode": "visible_context_answer",
			"answer": "LEAK_STALE_VISIBLE_CONTEXT_C34A",
		}
		for name, boundary in (
			("stale", stale),
			("mismatched", mismatched),
			("raw_mismatch", raw_mismatch),
			("non_redaction_safe", non_redaction_safe),
			("mixed_intent", mixed_intent),
			("decision_intent", decision_intent),
		):
			with self.subTest(case=name):
				session, payload, calls, ok = self.run_service(
					message,
					boundary,
					prior_context=True,
					trace_result=(True, handled_visible_context_payload),
				)

				self.assertTrue(ok)
				self.assertEqual(calls["trace_visible"], 0)
				self.assertEqual(calls["visible_followup"], 0)
				self.assertEqual(calls["compiled"], 0)
				self.assertNotEqual(payload.get("mode"), "visible_context_answer")
				self.assert_control_or_boundary_response(payload)
				self.assert_no_business_leaks(session)
				serialized = self.serialized_messages(session) + json.dumps(payload, sort_keys=True, default=str)
				self.assertNotIn("LEAK_STALE_VISIBLE_CONTEXT_C34A", serialized)

	def test_safe_explicit_read_only_followup_can_activate_context_only_with_v1_ib_and_visible_authority(self):
		message = "Who is second in the previous table?"
		context_allow = _boundary(message, allow_context=True)
		visible_payload = {"ok": True, "mode": "visible_context_answer", "answer": "Rank 2 safe visible answer."}

		session, payload, calls, ok = self.run_service(
			message,
			context_allow,
			prior_context=True,
			trace_result=(True, visible_payload),
		)
		self.assertTrue(ok)
		self.assertEqual(calls["trace_visible"], 1)
		self.assertEqual(payload["mode"], "visible_context_answer")
		self.assert_no_business_leaks(session)

		session, payload, calls, ok = self.run_service(
			message,
			context_allow,
			prior_context=True,
			trace_result=(False, None),
			visible_result=(False, None),
		)
		self.assertTrue(ok)
		self.assertNotEqual(payload.get("mode"), "visible_context_answer")
		self.assertEqual(calls["trace_visible"], 1)
		self.assertEqual(calls["visible_followup"], 0)
		self.assert_control_or_boundary_response(payload)


if __name__ == "__main__":
	unittest.main()
