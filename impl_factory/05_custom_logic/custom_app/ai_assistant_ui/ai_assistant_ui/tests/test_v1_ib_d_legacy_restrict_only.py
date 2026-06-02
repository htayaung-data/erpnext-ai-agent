from __future__ import annotations

import contextlib
import json
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

if "frappe" not in sys.modules:
	fake_frappe = types.ModuleType("frappe")
	fake_frappe.local = types.SimpleNamespace(site="unit.test")
	fake_frappe.get_doc = lambda *_args, **_kwargs: None
	fake_frappe.get_traceback = lambda: ""
	fake_frappe.log_error = lambda *_args, **_kwargs: None
	fake_frappe.get_all = lambda *_args, **_kwargs: []
	fake_frappe.conf = {}
	fake_frappe.db = types.SimpleNamespace(
		exists=lambda *_args, **_kwargs: False,
		get_value=lambda *_args, **_kwargs: None,
		sql=lambda *_args, **_kwargs: [],
	)
	fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
	fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
	sys.modules["frappe"] = fake_frappe

from ai_assistant_ui.qwen_chat import authorized_emission, intent_boundary_runtime_integration, service, user_intent_boundary
from ai_assistant_ui.qwen_chat.authorized_emission import (
	ANSWER_TYPE_CONTROL,
	ANSWER_TYPE_GOVERNED_REPORT,
	USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE,
	emit_authorized_assistant_answer,
)
from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_followup_resolution_contract,
	build_interaction_contract,
)
from ai_assistant_ui.qwen_chat.intent_boundary_contract import (
	ANSWER_MODE_CLARIFICATION,
	ANSWER_MODE_GOVERNED_ERP,
	AUTHORITY_DECISION_ALLOW_REPORT,
	AUTHORITY_DECISION_BLOCK,
	TRACE_REDACTION_SAFE,
	hash_text,
	normalize_message,
)
from ai_assistant_ui.qwen_chat.intent_boundary_runtime_integration import (
	USER_INTENT_BOUNDARY_CONTRACT_TYPE,
	merge_v1_ib_with_legacy_boundary,
)


LEAK_MARKERS = (
	"LEAK_D4A_SELECTED_ANSWER",
	"LEAK_D4A_ROWS",
	"LEAK_D4A_ARTIFACT",
	"LEAK_D4A_VISIBLE",
	"LEAK_D4A_REASONING",
	"LEAK_D4A_COMPILED",
	"LEAK_D4A_REQUERY",
	"LEAK_D4A_LEGACY_ALLOW",
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


class _EmissionSession:
	def __init__(self):
		self.messages = []


def _append_message(session_doc, role, content):
	session_doc.messages.append({"role": role, "content": content})


def _append_tool_payload(session_doc, payload):
	session_doc.messages.append({"role": "tool", "content": payload})


def _assistant_text_payload(text):
	return {"text": str(text or "")}


def _interaction(message):
	return build_interaction_contract(
		request_id="v1-ib-d4a",
		session_id="session-v1-ib-d4a",
		user_id="Administrator",
		site_name="unit.test",
		raw_message=message,
	)


def _followup():
	return build_followup_resolution_contract(
		request_id="v1-ib-d4a",
		mode="compiled_first_turn",
		requested_modes=["compiled_first_turn"],
		depends_on_grounded_turn=True,
		self_contained=False,
		latest_grounded_turn_available=True,
		reason="legacy restrict-only assertion test",
	)


def _execution_path():
	return ExecutionPath(
		request_id="v1-ib-d4a",
		path="compiled_first_turn",
		reason="legacy restrict-only assertion test",
		requires_runtime=True,
		grounded_required=True,
	)


def _grounded_turn():
	return {
		"type": "qwen_grounded_turn_context",
		"grounded": True,
		"source_kind": "report",
		"source_name": "Item Sales",
		"artifact_family_id": "item_sales",
		"trace_request_id": "v1-ib-d4a",
	}


def _normalized_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"request_id": "v1-ib-d4a-artifact",
		"family_id": "item_sales",
	}


def _boundary(
	message: str,
	*,
	allow_report: bool = False,
	raw_source: str | None = None,
	normalized_source: str | None = None,
	validator_status: str | None = None,
	trace_redaction_status: str = TRACE_REDACTION_SAFE,
	mixed: bool | None = None,
	decision: bool = False,
	ambiguity_status: str = "none",
):
	raw_source = raw_source if raw_source is not None else message
	normalized_source = normalized_source if normalized_source is not None else raw_source
	is_allowed = bool(allow_report)
	return {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"contract_version": "test-v1-ib-d4a",
		"raw_message_hash": hash_text(raw_source),
		"normalized_message_hash": hash_text(normalize_message(normalized_source)),
		"clause_count": 1,
		"category": "factual_erp_query" if is_allowed else "clarification_required",
		"required_answer_mode": ANSWER_MODE_GOVERNED_ERP if is_allowed else ANSWER_MODE_CLARIFICATION,
		"context_reuse_allowed": False,
		"report_routing_allowed": is_allowed,
		"model_reasoning_allowed": is_allowed,
		"final_emission_allowed": is_allowed,
		"safe_followup_intent": False,
		"decision_intent": bool(decision),
		"advice_intent": False,
		"business_action_intent": False,
		"policy_boundary_intent": False,
		"mixed_intent_detected": (not is_allowed) if mixed is None else bool(mixed),
		"ambiguity_status": ambiguity_status,
		"authority_decision": AUTHORITY_DECISION_ALLOW_REPORT if is_allowed else AUTHORITY_DECISION_BLOCK,
		"boundary_reason": "validated_safe_factual_intent" if is_allowed else "v1_ib_contract_blocked_runtime_authority",
		"validator_status": validator_status if validator_status is not None else ("valid" if is_allowed else "invalid"),
		"trace_redaction_status": trace_redaction_status,
		"replayed_raw_message_safety_final_decision": "safe" if is_allowed else "blocked",
		"v1_ib_runtime_contract_hash": hash_text("allow" if is_allowed else "block"),
	}


def _legacy_allow(*, include_leak: bool = False):
	payload = {
		"type": "qwen_legacy_user_intent_boundary",
		"contract_version": "legacy-test-d4a",
		"category": "factual_erp_query",
		"required_answer_mode": ANSWER_MODE_GOVERNED_ERP,
		"context_reuse_allowed": True,
		"report_routing_allowed": True,
		"model_reasoning_allowed": True,
		"final_emission_allowed": True,
		"authority_decision": AUTHORITY_DECISION_ALLOW_REPORT,
		"boundary_reason": "legacy_allow_should_not_authorize",
	}
	if include_leak:
		payload["legacy_selected_answer"] = "LEAK_D4A_LEGACY_ALLOW"
		payload["legacy_rows"] = ["LEAK_D4A_ROWS"]
	return payload


def _legacy_block():
	return {
		"type": "qwen_legacy_user_intent_boundary",
		"contract_version": "legacy-test-d4a",
		"category": "clarification_required",
		"required_answer_mode": ANSWER_MODE_CLARIFICATION,
		"context_reuse_allowed": False,
		"report_routing_allowed": False,
		"boundary_reason": "legacy_block_restricts_only",
	}


def _frontdoor_result():
	return (
		_PayloadObject(status="accepted", payload={"type": "frontdoor_semantic_result", "status": "accepted"}),
		_PayloadObject(
			handle_in_front_door=True,
			response_payload={"confidence": 0.99, "answer": "LEAK_D4A_SELECTED_ANSWER"},
			payload={"type": "frontdoor_contract", "confidence": 0.99},
		),
		None,
		"LEAK_D4A_SELECTED_ANSWER",
	)


def _frontdoor_rejected():
	return (
		_PayloadObject(status="rejected", payload={"type": "frontdoor_semantic_result", "status": "rejected"}),
		_PayloadObject(
			handle_in_front_door=False,
			response_payload={},
			payload={"type": "frontdoor_contract", "confidence": 0.0},
		),
		None,
		"",
	)


class V1IBDLegacyRestrictOnlyTests(unittest.TestCase):
	def run_service(
		self,
		message,
		boundary,
		*,
		frontdoor_candidate=True,
		frontdoor_high_confidence=True,
		visible_result=(True, {"ok": True, "mode": "visible_context_answer", "answer": "LEAK_D4A_VISIBLE"}),
		requery_result=(True, {"ok": True, "mode": "governed_requery", "rows": ["LEAK_D4A_REQUERY"]}),
		compiled_result=(True, {"ok": True, "mode": "compiled_first_turn", "rows": ["LEAK_D4A_COMPILED"]}),
	):
		session = _FakeSession()
		calls = {"trace_visible": 0, "visible_followup": 0, "reasoning": 0, "compiled": 0, "requery": 0}

		def trace_visible(**_kwargs):
			calls["trace_visible"] += 1
			return visible_result

		def visible_followup(**_kwargs):
			calls["visible_followup"] += 1
			return visible_result

		def reasoning(**_kwargs):
			calls["reasoning"] += 1
			return True, {"ok": True, "mode": "model_reasoning_answer", "answer": "LEAK_D4A_REASONING"}

		def compiled(**_kwargs):
			calls["compiled"] += 1
			return compiled_result

		def requery(**_kwargs):
			calls["requery"] += 1
			return requery_result

		def v1_ib_builder(_raw):
			return dict(boundary or {})

		patches = [
			mock.patch.object(service.frappe, "get_doc", lambda *_args, **_kwargs: session),
			mock.patch.object(service, "build_v1_ib_runtime_boundary", v1_ib_builder),
			mock.patch.object(service, "build_user_intent_boundary_contract", lambda _raw: _legacy_allow(include_leak=True)),
			mock.patch.object(service, "_build_conversation_state_snapshot", lambda **_kwargs: {}),
			mock.patch.object(service, "_latest_normalized_family_artifact", lambda *_args, **_kwargs: {}),
			mock.patch.object(service, "_latest_grounded_assistant_context", lambda _session: ({}, {})),
			mock.patch.object(service, "_latest_assistant_payload", lambda _session: {"text": "LEAK_D4A_SELECTED_ANSWER"}),
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
			mock.patch.object(service, "_try_activate_visible_context_followup_response", visible_followup),
			mock.patch.object(service, "_compound_request_completion_answer_from_snapshot", lambda **_kwargs: ""),
			mock.patch.object(service, "_erp_business_reasoning_rollout_decision", lambda **_kwargs: {"enabled": True}),
			mock.patch.object(service, "build_reasoning_activation_contract", lambda **_kwargs: _PayloadObject(payload={"type": "reasoning_activation"})),
			mock.patch.object(service, "interpret_reasoning_activation_semantically", lambda **_kwargs: _PayloadObject(payload={"semantic_safe": True})),
			mock.patch.object(service, "handle_reasoning_turn", reasoning),
			mock.patch.object(service, "build_response_policy_contract", lambda **_kwargs: _PayloadObject(payload={"type": "response_policy"})),
			mock.patch.object(service, "_recent_messages_for_grounded_source", lambda *_args, **_kwargs: []),
			mock.patch.object(service, "_reasoning_contract_has_executable_offered_next_action", lambda _contract: False),
			mock.patch.object(service, "_message_should_override_stale_context_as_fresh_query", lambda **_kwargs: False),
			mock.patch.object(service, "governed_composite_frontdoor_candidate_available", lambda **_kwargs: bool(frontdoor_candidate)),
			mock.patch.object(service, "governed_kpi_value_frontdoor_candidate_available", lambda **_kwargs: False),
			mock.patch.object(
				service,
				"evaluate_frontdoor_lane",
				lambda **_kwargs: _frontdoor_result() if frontdoor_high_confidence else _frontdoor_rejected(),
			),
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
			mock.patch.object(service, "_try_activate_nbu_governed_requery_response", requery),
			mock.patch.object(service, "_compiled_first_turn_rollout_decision", lambda **_kwargs: {"enabled": True}),
			mock.patch.object(service, "handle_compiled_query_turn", compiled),
		]
		with contextlib.ExitStack() as stack:
			for patch in patches:
				stack.enter_context(patch)
			ok, payload = service.handle_qwen_user_message(
				session_name="session-v1-ib-d4a",
				message=message,
				user="Administrator",
			)
		return session, payload, calls, ok

	def serialized(self, session, payload):
		return json.dumps({"messages": session.messages, "payload": payload}, sort_keys=True, default=str)

	def assert_no_leaks(self, session, payload):
		serialized = self.serialized(session, payload)
		for marker in LEAK_MARKERS:
			self.assertNotIn(marker, serialized)

	def assert_blocked(self, payload):
		self.assertEqual(payload.get("mode"), "user_intent_boundary")
		boundary = (payload.get("agent_meta") or {}).get("user_intent_boundary") or {}
		self.assertFalse(boundary.get("report_routing_allowed"))
		self.assertFalse(boundary.get("context_reuse_allowed"))
		self.assertFalse(boundary.get("model_reasoning_allowed"))
		self.assertFalse(boundary.get("final_emission_allowed"))
		self.assertNotEqual(boundary.get("required_answer_mode"), ANSWER_MODE_GOVERNED_ERP)
		self.assertNotEqual(boundary.get("authority_decision"), AUTHORITY_DECISION_ALLOW_REPORT)
		self.assertEqual(boundary.get("runtime_authority_source"), "v1_ib_contract_validator")

	def test_runtime_merge_keeps_legacy_allow_restrict_only(self):
		message = "Show item sales and tell me whether to discount it"
		cases = [
			_boundary(message),
			_boundary(message, validator_status="invalid"),
			_boundary(message, mixed=True),
			_boundary(message, decision=True),
			_boundary(message, ambiguity_status="ambiguous"),
		]
		for v1_ib_block in cases:
			with self.subTest(reason=v1_ib_block.get("boundary_reason"), ambiguity=v1_ib_block.get("ambiguity_status")):
				merged = merge_v1_ib_with_legacy_boundary(v1_ib_block, _legacy_allow(include_leak=True))
				self.assertFalse(merged.get("report_routing_allowed"))
				self.assertFalse(merged.get("context_reuse_allowed"))
				self.assertFalse(merged.get("model_reasoning_allowed"))
				self.assertFalse(merged.get("final_emission_allowed"))
				self.assertNotEqual(merged.get("required_answer_mode"), ANSWER_MODE_GOVERNED_ERP)
				self.assertNotEqual(merged.get("authority_decision"), AUTHORITY_DECISION_ALLOW_REPORT)
				self.assertEqual(merged.get("runtime_authority_source"), "v1_ib_contract_validator")
				serialized = json.dumps(merged, sort_keys=True, default=str)
				self.assertNotIn("LEAK_D4A_LEGACY_ALLOW", serialized)
				self.assertNotIn("LEAK_D4A_ROWS", serialized)

	def test_runtime_merge_legacy_block_can_only_reduce_v1_ib_allow(self):
		message = "Show EC7H-ITEM-A item sales"
		allowed_by_v1 = _boundary(message, allow_report=True)

		legacy_restricted = merge_v1_ib_with_legacy_boundary(allowed_by_v1, _legacy_block())
		self.assertFalse(legacy_restricted.get("report_routing_allowed"))
		self.assertFalse(legacy_restricted.get("context_reuse_allowed"))
		self.assertFalse(legacy_restricted.get("model_reasoning_allowed"))
		self.assertFalse(legacy_restricted.get("final_emission_allowed"))
		self.assertEqual(legacy_restricted.get("authority_decision"), AUTHORITY_DECISION_BLOCK)
		self.assertEqual(legacy_restricted.get("runtime_authority_source"), "v1_ib_contract_validator")

		legacy_allow_with_v1_allow = merge_v1_ib_with_legacy_boundary(allowed_by_v1, _legacy_allow())
		self.assertTrue(legacy_allow_with_v1_allow.get("report_routing_allowed"))
		self.assertEqual(legacy_allow_with_v1_allow.get("authority_decision"), AUTHORITY_DECISION_ALLOW_REPORT)
		self.assertEqual(legacy_allow_with_v1_allow.get("runtime_authority_source"), "v1_ib_contract_validator")
		self.assertNotEqual(legacy_allow_with_v1_allow.get("runtime_authority_source"), "legacy_user_intent_boundary")

	def test_service_blocking_v1_ib_dominates_legacy_allow_and_optimistic_lanes(self):
		message = "Show supplier aging and tell me if we should delay payment"
		session, payload, calls, ok = self.run_service(
			message,
			_boundary(message),
			compiled_result=(True, {"ok": True, "mode": "compiled_first_turn", "rows": ["LEAK_D4A_COMPILED"]}),
		)

		self.assertTrue(ok)
		self.assert_blocked(payload)
		self.assertEqual(calls["trace_visible"], 0)
		self.assertEqual(calls["visible_followup"], 0)
		self.assertEqual(calls["reasoning"], 0)
		self.assertEqual(calls["compiled"], 0)
		self.assertEqual(calls["requery"], 0)
		self.assert_no_leaks(session, payload)

	def test_service_missing_stale_malformed_or_invalid_v1_ib_fails_closed_despite_legacy_allow(self):
		message = "Show EC7H-ITEM-A item sales"
		stale_source = "Show EC7H-SUP-A payable status"
		cases = {
			"missing": {},
			"malformed": {"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE, "report_routing_allowed": True},
			"stale": _boundary(message, allow_report=True, raw_source=stale_source),
			"invalid": _boundary(message, allow_report=True, validator_status="invalid"),
		}

		for label, boundary in cases.items():
			with self.subTest(label=label):
				session, payload, calls, ok = self.run_service(
					message,
					boundary,
					frontdoor_candidate=False,
					frontdoor_high_confidence=False,
					visible_result=(False, None),
					requery_result=(True, {"ok": True, "mode": "governed_requery", "rows": ["LEAK_D4A_REQUERY"]}),
					compiled_result=(True, {"ok": True, "mode": "compiled_first_turn", "rows": ["LEAK_D4A_COMPILED"]}),
				)
				self.assertTrue(ok)
				self.assert_blocked(payload)
				self.assertEqual(calls["trace_visible"], 0)
				self.assertEqual(calls["visible_followup"], 0)
				self.assertEqual(calls["reasoning"], 0)
				self.assertEqual(calls["compiled"], 0)
				self.assertEqual(calls["requery"], 0)
				self.assert_no_leaks(session, payload)

	def test_final_emission_fallback_does_not_use_legacy_allow_to_emit_governed_answer(self):
		message = "Show EC7H-ITEM-A item sales and tell me whether to discount it"
		session_doc = _EmissionSession()

		with contextlib.ExitStack() as stack:
			stack.enter_context(mock.patch.object(intent_boundary_runtime_integration, "build_v1_ib_runtime_boundary", lambda _raw: _boundary(message)))
			stack.enter_context(mock.patch.object(user_intent_boundary, "build_user_intent_boundary_contract", lambda _raw: _legacy_allow(include_leak=True)))
			result = emit_authorized_assistant_answer(
				session_doc=session_doc,
				answer_text="LEAK_D4A_SELECTED_ANSWER governed answer",
				answer_type=ANSWER_TYPE_GOVERNED_REPORT,
				append_message=_append_message,
				append_tool_payload=_append_tool_payload,
				assistant_text_payload=_assistant_text_payload,
				interaction_contract=_interaction(message),
				followup_resolution=_followup(),
				execution_path=_execution_path(),
				runtime_trace_payload={"agent_meta": {"engine": "qwen"}, "tool_trace": []},
				grounded_turn_context=_grounded_turn(),
				authority_context={"normalized_family_artifact": _normalized_artifact()},
				pre_assistant_tool_payloads=[
					{
						"type": "qwen_selected_report_payload",
						"rows": ["LEAK_D4A_ROWS"],
						"artifact": "LEAK_D4A_ARTIFACT",
					},
					_legacy_allow(include_leak=True),
				],
			)

		self.assertTrue(result.emitted)
		self.assertEqual(result.answer_type, ANSWER_TYPE_CONTROL)
		serialized = json.dumps(session_doc.messages, sort_keys=True, default=str)
		for marker in LEAK_MARKERS:
			self.assertNotIn(marker, serialized)
		self.assertIn(USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE, serialized)

	def test_trace_metadata_keeps_legacy_allow_redacted_and_non_authoritative(self):
		message = "Show item sales and tell me whether to discount it"
		merged = merge_v1_ib_with_legacy_boundary(_boundary(message), _legacy_allow(include_leak=True))
		metadata = intent_boundary_runtime_integration.v1_ib_runtime_contract_metadata(merged)

		self.assertEqual(metadata.get("runtime_authority_source"), "v1_ib_contract_validator")
		self.assertFalse(metadata.get("report_routing_allowed"))
		self.assertFalse(metadata.get("context_reuse_allowed"))
		self.assertFalse(metadata.get("model_reasoning_allowed"))
		self.assertFalse(metadata.get("final_emission_allowed"))
		serialized = json.dumps(metadata, sort_keys=True, default=str)
		self.assertNotIn("LEAK_D4A_LEGACY_ALLOW", serialized)
		self.assertNotIn("LEAK_D4A_ROWS", serialized)
		self.assertNotIn("legacy_selected_answer", serialized)
		self.assertNotIn("legacy_rows", serialized)

	def test_rejected_structural_classifier_is_not_runtime_authority_import(self):
		qwen_chat_dir = Path(service.__file__).resolve().parent
		tests_dir = qwen_chat_dir.parent / "tests"
		runtime_files = [
			path
			for path in qwen_chat_dir.glob("*.py")
			if path.name not in {"intent_boundary_structural_classifier.py"}
		]
		importing_files = []
		for path in runtime_files:
			text = path.read_text()
			if "intent_boundary_structural_classifier" in text:
				importing_files.append(path.name)

		self.assertEqual(importing_files, [])
		self.assertFalse((qwen_chat_dir / "intent_boundary_structural_classifier.py").exists())
		self.assertFalse((tests_dir / "test_v1_ib_structural_classifier.py").exists())
		self.assertTrue((qwen_chat_dir / "intent_boundary_proposal_classifier.py").exists())
		self.assertFalse(list(tests_dir.glob("test_user_intent_boundary_*.py")))

		legacy_boundary = _legacy_allow()
		blocked_boundary = _boundary(
			"Show item sales and tell me whether to discount it",
			decision=True,
			mixed=True,
		)
		merged = merge_v1_ib_with_legacy_boundary(blocked_boundary, legacy_boundary)
		self.assertFalse(merged.get("report_routing_allowed"))
		self.assertFalse(merged.get("context_reuse_allowed"))
		self.assertFalse(merged.get("model_reasoning_allowed"))
		self.assertFalse(merged.get("final_emission_allowed"))
		self.assertEqual(merged.get("authority_decision"), AUTHORITY_DECISION_BLOCK)

	def test_safe_positive_control_is_v1_ib_authorized_not_legacy_authorized(self):
		message = "Show EC7H-ITEM-A item sales"
		merged = merge_v1_ib_with_legacy_boundary(_boundary(message, allow_report=True), _legacy_allow())
		self.assertTrue(merged.get("report_routing_allowed"))
		self.assertEqual(merged.get("authority_decision"), AUTHORITY_DECISION_ALLOW_REPORT)
		self.assertEqual(merged.get("runtime_authority_source"), "v1_ib_contract_validator")

		session, payload, calls, ok = self.run_service(
			message,
			_boundary(message, allow_report=True),
			frontdoor_candidate=False,
			frontdoor_high_confidence=False,
			visible_result=(False, None),
			requery_result=(False, None),
			compiled_result=(True, {"ok": True, "mode": "compiled_first_turn", "report": "safe report"}),
		)

		self.assertTrue(ok)
		self.assertEqual(payload.get("mode"), "compiled_first_turn")
		self.assertEqual(calls["compiled"], 1)
		self.assert_no_leaks(session, payload)

		session, payload, calls, ok = self.run_service(
			message,
			_boundary(message),
			frontdoor_candidate=False,
			frontdoor_high_confidence=False,
			visible_result=(False, None),
			requery_result=(False, None),
			compiled_result=(True, {"ok": True, "mode": "compiled_first_turn", "rows": ["LEAK_D4A_COMPILED"]}),
		)

		self.assertTrue(ok)
		self.assert_blocked(payload)
		self.assertEqual(calls["compiled"], 0)
		self.assert_no_leaks(session, payload)


if __name__ == "__main__":
	unittest.main()
