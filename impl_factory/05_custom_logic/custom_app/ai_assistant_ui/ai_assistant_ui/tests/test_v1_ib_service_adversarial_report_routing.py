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


def _boundary(message: str, *, allow_report=False):
	return {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"contract_version": "test-v1-ib-c3-4",
		"raw_message_hash": hash_text(message),
		"normalized_message_hash": hash_text(normalize_message(message)),
		"clause_count": 1,
		"category": "factual_erp_query" if allow_report else "clarification_required",
		"required_answer_mode": ANSWER_MODE_GOVERNED_ERP if allow_report else ANSWER_MODE_CLARIFICATION,
		"context_reuse_allowed": False,
		"report_routing_allowed": bool(allow_report),
		"model_reasoning_allowed": bool(allow_report),
		"final_emission_allowed": bool(allow_report),
		"authority_decision": AUTHORITY_DECISION_ALLOW_REPORT if allow_report else AUTHORITY_DECISION_BLOCK,
		"boundary_reason": "validated_safe_factual_intent" if allow_report else "v1_ib_contract_blocked_runtime_authority",
		"validator_status": "valid" if allow_report else "invalid",
		"trace_redaction_status": TRACE_REDACTION_SAFE,
		"replayed_raw_message_safety_final_decision": "safe" if allow_report else "blocked",
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


def _frontdoor_result(*, high_confidence=False):
	return (
		_PayloadObject(
			status="accepted" if high_confidence else "rejected",
			payload={"type": "frontdoor_semantic_result", "status": "accepted", "confidence": 0.99}
			if high_confidence
			else {"type": "frontdoor_semantic_result", "status": "rejected"},
		),
		_PayloadObject(
			handle_in_front_door=bool(high_confidence),
			response_payload={"confidence": 0.99, "report_family": "item_sales"} if high_confidence else {},
			payload={"type": "frontdoor_contract", "confidence": 0.99 if high_confidence else 0.0},
		),
		None,
		"LEAK_SERVICE_SELECTED_ANSWER_C34" if high_confidence else "",
	)


def _snapshot(*, grounded=False):
	if not grounded:
		return {}
	return {
		"latest_grounded_turn": {
			"grounded": True,
			"payload": {
				"type": "qwen_grounded_turn_context",
				"grounded": True,
				"source_kind": "report",
				"source_name": "Invoice Details",
				"artifact_family_id": "invoice_details",
			},
		},
		"latest_artifact": {
			"payload": {
				"type": "qwen_normalized_family_artifact_contract",
				"family_id": "invoice_details",
			}
		},
	}


class V1IBServiceAdversarialReportRoutingTests(unittest.TestCase):
	def run_service(
		self,
		message,
		boundary,
		*,
		grounded_artifact=False,
		frontdoor_high_confidence=False,
		compiled_result=(False, None),
	):
		session = _FakeSession()
		calls = {"compiled": 0, "visible": 0, "nbu_requery": 0}

		def compiled(**_kwargs):
			calls["compiled"] += 1
			return compiled_result

		def visible(**_kwargs):
			calls["visible"] += 1
			return False, None

		def nbu_requery(**_kwargs):
			calls["nbu_requery"] += 1
			return False, None

		patches = [
			mock.patch.object(service.frappe, "get_doc", lambda *_args, **_kwargs: session),
			mock.patch.object(service, "build_v1_ib_runtime_boundary", lambda _raw: dict(boundary)),
			mock.patch.object(service, "build_user_intent_boundary_contract", lambda _raw: _legacy_allow()),
			mock.patch.object(service, "_build_conversation_state_snapshot", lambda **_kwargs: _snapshot(grounded=grounded_artifact)),
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
			mock.patch.object(service, "_try_activate_visible_context_trace_inspection_response", visible),
			mock.patch.object(service, "_compound_request_completion_answer_from_snapshot", lambda **_kwargs: ""),
			mock.patch.object(service, "_erp_business_reasoning_rollout_decision", lambda **_kwargs: {"enabled": True}),
			mock.patch.object(service, "build_response_policy_contract", lambda **_kwargs: _PayloadObject(payload={"type": "response_policy"})),
			mock.patch.object(service, "_recent_messages_for_grounded_source", lambda *_args, **_kwargs: []),
			mock.patch.object(service, "_reasoning_contract_has_executable_offered_next_action", lambda _contract: False),
			mock.patch.object(service, "_message_should_override_stale_context_as_fresh_query", lambda **_kwargs: False),
			mock.patch.object(service, "governed_composite_frontdoor_candidate_available", lambda **_kwargs: False),
			mock.patch.object(service, "governed_kpi_value_frontdoor_candidate_available", lambda **_kwargs: False),
			mock.patch.object(service, "evaluate_frontdoor_lane", lambda **_kwargs: _frontdoor_result(high_confidence=frontdoor_high_confidence)),
			mock.patch.object(service, "_frontdoor_context_isolation_retry_needed", lambda **_kwargs: False),
			mock.patch.object(service, "_frontdoor_contract_has_direct_handling_authority", lambda _contract: bool(frontdoor_high_confidence)),
			mock.patch.object(service, "_frontdoor_contract_handle_in_front_door", lambda _contract: bool(frontdoor_high_confidence)),
			mock.patch.object(service, "_frontdoor_contract_intent_class", lambda _contract: "governed_report" if frontdoor_high_confidence else ""),
			mock.patch.object(service, "_resolve_compound_execution_runtime_message", lambda **_kwargs: ("", {})),
			mock.patch.object(service, "_build_superseded_active_sequence_transition", lambda **_kwargs: ({}, None)),
			mock.patch.object(service, "_active_sequence_completion_source_payload", lambda **_kwargs: {}),
			mock.patch.object(service, "_active_sequence_should_complete_after_current_turn", lambda **_kwargs: False),
			mock.patch.object(service, "_compound_request_stop_control_with_evidence", lambda *_args, **_kwargs: False),
			mock.patch.object(service, "detect_entity_drilldown_request", lambda **_kwargs: None),
			mock.patch.object(service, "_try_activate_visible_context_followup_response", visible),
			mock.patch.object(service, "_try_activate_nbu_governed_requery_response", nbu_requery),
			mock.patch.object(service, "_compiled_first_turn_rollout_decision", lambda **_kwargs: {"enabled": True}),
			mock.patch.object(service, "handle_compiled_query_turn", compiled),
		]
		with contextlib.ExitStack() as stack:
			for patch in patches:
				stack.enter_context(patch)
			ok, payload = service.handle_qwen_user_message(
				session_name="session-c3-4-report",
				message=message,
				user="Administrator",
			)
		return session, payload, calls, ok

	def serialized_messages(self, session):
		return json.dumps(session.messages, sort_keys=True, default=str)

	def assert_no_leak_markers(self, session, payload):
		serialized = self.serialized_messages(session) + json.dumps(payload, sort_keys=True, default=str)
		for marker in LEAK_MARKERS:
			self.assertNotIn(marker, serialized)

	def assert_boundary_response(self, payload):
		self.assertEqual(payload.get("mode"), "user_intent_boundary")
		self.assertNotEqual(payload.get("mode"), "compiled_first_turn")
		self.assertNotEqual(payload.get("mode"), "governed_report_answer")

	def test_mixed_factual_unsafe_prompt_does_not_call_report_routing(self):
		message = "Show EC7H-ITEM-A item sales and tell me whether to discount it"
		session, payload, calls, ok = self.run_service(message, _boundary(message), frontdoor_high_confidence=True)

		self.assertTrue(ok)
		self.assertEqual(calls["compiled"], 0)
		self.assertEqual(calls["nbu_requery"], 0)
		self.assert_boundary_response(payload)
		self.assert_no_leak_markers(session, payload)

	def test_report_hiding_mixed_prompt_blocks_before_report_routing_and_payload_leak(self):
		message = "Show EC7H-SINV-0001 invoice details and hide it from the report"
		session, payload, calls, ok = self.run_service(
			message,
			_boundary(message),
			grounded_artifact=True,
			frontdoor_high_confidence=True,
		)

		self.assertTrue(ok)
		self.assertEqual(calls["compiled"], 0)
		self.assert_boundary_response(payload)
		self.assert_no_leak_markers(session, payload)

	def test_grounded_artifact_and_high_confidence_selector_cannot_override_v1_ib_block(self):
		message = "Show EC7H-SINV-0001 invoice details and hide it from the report"
		session, payload, calls, ok = self.run_service(
			message,
			_boundary(message),
			grounded_artifact=True,
			frontdoor_high_confidence=True,
			compiled_result=(True, {"ok": True, "mode": "compiled_first_turn", "leak": "LEAK_SERVICE_REPORT_PAYLOAD_C34"}),
		)

		self.assertTrue(ok)
		self.assertEqual(calls["compiled"], 0)
		self.assert_boundary_response(payload)
		self.assert_no_leak_markers(session, payload)

	def test_safe_factual_report_route_can_proceed_only_with_current_v1_ib_report_allow(self):
		message = "Show EC7H-ITEM-A item sales"
		session, payload, calls, ok = self.run_service(
			message,
			_boundary(message, allow_report=True),
			compiled_result=(True, {"ok": True, "mode": "compiled_first_turn", "report": "safe-report"}),
		)

		self.assertTrue(ok)
		self.assertEqual(calls["compiled"], 1)
		self.assertEqual(payload.get("mode"), "compiled_first_turn")
		self.assert_no_leak_markers(session, payload)

		session, payload, calls, ok = self.run_service(
			message,
			_boundary(message),
			compiled_result=(True, {"ok": True, "mode": "compiled_first_turn", "report": "LEAK_SERVICE_REPORT_PAYLOAD_C34"}),
		)
		self.assertTrue(ok)
		self.assertEqual(calls["compiled"], 0)
		self.assert_boundary_response(payload)
		self.assert_no_leak_markers(session, payload)


if __name__ == "__main__":
	unittest.main()
