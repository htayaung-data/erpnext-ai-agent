from __future__ import annotations

import json
import sys
import types
import unittest

if "frappe" not in sys.modules:
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
	sys.modules["frappe"] = fake_frappe

from ai_assistant_ui.qwen_chat.authorized_emission import (
	ANSWER_TYPE_CONTROL,
	ANSWER_TYPE_GOVERNED_REPORT,
	AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE,
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
from ai_assistant_ui.qwen_chat.intent_boundary_runtime_integration import USER_INTENT_BOUNDARY_CONTRACT_TYPE


class _Session:
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
		request_id="v1-ib-c2",
		session_id="session-v1-ib-c2",
		user_id="Administrator",
		site_name="unit.test",
		raw_message=message,
	)


def _followup():
	return build_followup_resolution_contract(
		request_id="v1-ib-c2",
		mode="compiled_first_turn",
		requested_modes=["compiled_first_turn"],
		depends_on_grounded_turn=True,
		self_contained=False,
		latest_grounded_turn_available=True,
		reason="runtime integration test",
	)


def _execution_path():
	return ExecutionPath(
		request_id="v1-ib-c2",
		path="compiled_first_turn",
		reason="runtime integration test",
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
		"trace_request_id": "v1-ib-c2",
	}


def _normalized_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"request_id": "v1-ib-c2-artifact",
		"family_id": "item_sales",
	}


def _boundary(message: str, *, allow: bool):
	normalized = normalize_message(message)
	if allow:
		return {
			"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
			"contract_version": "test-v1-ib",
			"raw_message_hash": hash_text(message),
			"normalized_message_hash": hash_text(normalized),
			"clause_count": 1,
			"category": "factual_erp_query",
			"required_answer_mode": ANSWER_MODE_GOVERNED_ERP,
			"context_reuse_allowed": False,
			"report_routing_allowed": True,
			"model_reasoning_allowed": True,
			"final_emission_allowed": True,
			"authority_decision": AUTHORITY_DECISION_ALLOW_REPORT,
			"boundary_reason": "validated_safe_factual_intent",
			"validator_status": "valid",
			"trace_redaction_status": TRACE_REDACTION_SAFE,
			"replayed_raw_message_safety_final_decision": "safe",
			"v1_ib_runtime_contract_hash": hash_text("allow"),
		}
	return {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"contract_version": "test-v1-ib",
		"raw_message_hash": hash_text(message),
		"normalized_message_hash": hash_text(normalized),
		"clause_count": 1,
		"category": "clarification_required",
		"required_answer_mode": ANSWER_MODE_CLARIFICATION,
		"context_reuse_allowed": False,
		"report_routing_allowed": False,
		"model_reasoning_allowed": False,
		"final_emission_allowed": False,
		"authority_decision": AUTHORITY_DECISION_BLOCK,
		"boundary_reason": "v1_ib_contract_blocked_runtime_authority",
		"validator_status": "invalid",
		"trace_redaction_status": TRACE_REDACTION_SAFE,
		"replayed_raw_message_safety_final_decision": "blocked",
		"v1_ib_runtime_contract_hash": hash_text("block"),
	}


def _emit_governed_report_with_boundary_carrier(
	*,
	message: str,
	boundary_carrier,
	answer_text: str = "STALE_CONTRACT_SELECTED_ANSWER_LEAK",
):
	session_doc = _Session()
	runtime_trace_payload = {"agent_meta": {"engine": "qwen"}, "tool_trace": []}
	authority_context = {"normalized_family_artifact": _normalized_artifact()}
	pre_assistant_tool_payloads = []
	if boundary_carrier == "pre_assistant_tool_payloads":
		pre_assistant_tool_payloads.append(_boundary("Show EC7H-ITEM-A item sales", allow=True))
	elif boundary_carrier == "authority_context":
		authority_context["user_intent_boundary"] = _boundary("Show EC7H-ITEM-A item sales", allow=True)
	elif boundary_carrier == "runtime_trace_payload":
		runtime_trace_payload["user_intent_boundary"] = _boundary("Show EC7H-ITEM-A item sales", allow=True)
	elif isinstance(boundary_carrier, dict):
		pre_assistant_tool_payloads.append(boundary_carrier)
	result = emit_authorized_assistant_answer(
		session_doc=session_doc,
		answer_text=answer_text,
		answer_type=ANSWER_TYPE_GOVERNED_REPORT,
		append_message=_append_message,
		append_tool_payload=_append_tool_payload,
		assistant_text_payload=_assistant_text_payload,
		interaction_contract=_interaction(message),
		followup_resolution=_followup(),
		execution_path=_execution_path(),
		runtime_trace_payload=runtime_trace_payload,
		grounded_turn_context=_grounded_turn(),
		authority_context=authority_context,
		pre_assistant_tool_payloads=pre_assistant_tool_payloads,
	)
	return session_doc, result


class V1IBRuntimeFinalEmissionContractVetoTests(unittest.TestCase):
	def test_blocked_contract_vetoes_selected_report_and_redacts_payloads(self):
		message = "Show EC7H-ITEM-A item sales and tell me whether to discount it"
		session_doc = _Session()
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="LEAK_SELECTED_ANSWER_TEXT EC7H-ITEM-A",
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
				_boundary(message, allow=False),
				{
					"type": "qwen_selected_report_payload",
					"rows": ["SELECTED_ROWS_SHOULD_NOT_LEAK"],
					"rendered": "RENDERED_PAYLOAD_SHOULD_NOT_LEAK",
					"narrative": "NARRATIVE_SHOULD_NOT_LEAK",
					"grounded_evidence": "GROUNDED_EVIDENCE_SHOULD_NOT_LEAK",
				},
			],
		)

		self.assertTrue(result.emitted)
		self.assertFalse(result.blocked)
		self.assertEqual(result.answer_type, ANSWER_TYPE_CONTROL)
		serialized = json.dumps(session_doc.messages, sort_keys=True)
		for forbidden in (
			"LEAK_SELECTED_ANSWER_TEXT",
			"SELECTED_ROWS_SHOULD_NOT_LEAK",
			"RENDERED_PAYLOAD_SHOULD_NOT_LEAK",
			"NARRATIVE_SHOULD_NOT_LEAK",
			"GROUNDED_EVIDENCE_SHOULD_NOT_LEAK",
		):
			self.assertNotIn(forbidden, serialized)
		self.assertIn(USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE, serialized)

	def test_raw_message_fallback_uses_v1_ib_fail_closed_not_legacy_allow(self):
		message = "Show EC7H-ITEM-A item sales and tell me whether to discount it"
		session_doc = _Session()
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="Unsafe selected governed answer",
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
		)

		self.assertTrue(result.emitted)
		self.assertEqual(result.answer_type, ANSWER_TYPE_CONTROL)
		serialized = json.dumps(session_doc.messages, sort_keys=True)
		self.assertNotIn("Unsafe selected governed answer", serialized)
		self.assertIn(USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE, serialized)

	def test_stale_safe_contract_in_pre_assistant_payload_vetoes_current_unsafe_message(self):
		session_doc, result = _emit_governed_report_with_boundary_carrier(
			message="Show EC7H-ITEM-A item sales and tell me whether to discount it",
			boundary_carrier="pre_assistant_tool_payloads",
		)

		self.assertTrue(result.emitted)
		self.assertEqual(result.answer_type, ANSWER_TYPE_CONTROL)
		serialized = json.dumps(session_doc.messages, sort_keys=True)
		self.assertNotIn("STALE_CONTRACT_SELECTED_ANSWER_LEAK", serialized)
		self.assertIn(USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE, serialized)

	def test_stale_safe_contract_in_authority_context_vetoes_current_unsafe_message(self):
		session_doc, result = _emit_governed_report_with_boundary_carrier(
			message="Show EC7H-ITEM-A item sales and tell me whether to discount it",
			boundary_carrier="authority_context",
		)

		self.assertTrue(result.emitted)
		self.assertEqual(result.answer_type, ANSWER_TYPE_CONTROL)
		serialized = json.dumps(session_doc.messages, sort_keys=True)
		self.assertNotIn("STALE_CONTRACT_SELECTED_ANSWER_LEAK", serialized)
		self.assertIn(USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE, serialized)

	def test_stale_safe_contract_in_runtime_trace_vetoes_current_unsafe_message(self):
		session_doc, result = _emit_governed_report_with_boundary_carrier(
			message="Show EC7H-ITEM-A item sales and tell me whether to discount it",
			boundary_carrier="runtime_trace_payload",
		)

		self.assertTrue(result.emitted)
		self.assertEqual(result.answer_type, ANSWER_TYPE_CONTROL)
		serialized = json.dumps(session_doc.messages, sort_keys=True)
		self.assertNotIn("STALE_CONTRACT_SELECTED_ANSWER_LEAK", serialized)
		self.assertIn(USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE, serialized)

	def test_mismatched_normalized_hash_vetoes_even_when_raw_hash_matches(self):
		message = "Show EC7H-ITEM-A item sales"
		boundary = _boundary(message, allow=True)
		boundary["normalized_message_hash"] = hash_text("different normalized text")
		session_doc, result = _emit_governed_report_with_boundary_carrier(
			message=message,
			boundary_carrier=boundary,
			answer_text="NORMALIZED_HASH_MISMATCH_LEAK",
		)

		self.assertTrue(result.emitted)
		self.assertEqual(result.answer_type, ANSWER_TYPE_CONTROL)
		serialized = json.dumps(session_doc.messages, sort_keys=True)
		self.assertNotIn("NORMALIZED_HASH_MISMATCH_LEAK", serialized)
		self.assertIn(USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE, serialized)

	def test_allowed_contract_still_requires_existing_final_answer_authority(self):
		message = "Show EC7H-ITEM-A item sales"
		session_doc = _Session()
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="Item sales governed ERP answer.",
			answer_type=ANSWER_TYPE_GOVERNED_REPORT,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=_interaction(message),
			followup_resolution=_followup(),
			execution_path=_execution_path(),
			runtime_trace_payload={"agent_meta": {"engine": "qwen"}, "tool_trace": []},
			grounded_turn_context=_grounded_turn(),
			authority_context={
				"normalized_family_artifact": _normalized_artifact(),
				"user_intent_boundary": _boundary(message, allow=True),
			},
			pre_assistant_tool_payloads=[_boundary(message, allow=True)],
		)

		self.assertTrue(result.emitted)
		self.assertFalse(result.blocked)
		self.assertEqual(result.answer_type, ANSWER_TYPE_GOVERNED_REPORT)
		self.assertEqual([row["role"] for row in session_doc.messages][-1], "assistant")
		self.assertEqual(session_doc.messages[-2]["content"]["type"], AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)


if __name__ == "__main__":
	unittest.main()
