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


LEAK_MARKERS = (
	"LEAK_D2_SELECTED_ANSWER",
	"LEAK_D2_ROWS",
	"LEAK_D2_ARTIFACT",
	"LEAK_D2_RENDERED",
	"LEAK_D2_NARRATIVE",
	"LEAK_D2_GROUNDED",
	"LEAK_D2_HELPER",
)


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
		request_id="v1-ib-d-2",
		session_id="session-v1-ib-d-2",
		user_id="Administrator",
		site_name="unit.test",
		raw_message=message,
	)


def _followup():
	return build_followup_resolution_contract(
		request_id="v1-ib-d-2",
		mode="compiled_first_turn",
		requested_modes=["compiled_first_turn"],
		depends_on_grounded_turn=True,
		self_contained=False,
		latest_grounded_turn_available=True,
		reason="authority consistency test",
	)


def _execution_path():
	return ExecutionPath(
		request_id="v1-ib-d-2",
		path="compiled_first_turn",
		reason="authority consistency test",
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
		"trace_request_id": "v1-ib-d-2",
	}


def _artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"request_id": "v1-ib-d-2-artifact",
		"family_id": "item_sales",
	}


def _boundary(
	message: str,
	*,
	allow: bool,
	raw_source: str | None = None,
	normalized_source: str | None = None,
	trace_redaction_status: str = TRACE_REDACTION_SAFE,
):
	raw_source = raw_source if raw_source is not None else message
	normalized_source = normalized_source if normalized_source is not None else raw_source
	return {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"contract_version": "test-v1-ib-d-2",
		"raw_message_hash": hash_text(raw_source),
		"normalized_message_hash": hash_text(normalize_message(normalized_source)),
		"clause_count": 1,
		"category": "factual_erp_query" if allow else "clarification_required",
		"required_answer_mode": ANSWER_MODE_GOVERNED_ERP if allow else ANSWER_MODE_CLARIFICATION,
		"context_reuse_allowed": False,
		"report_routing_allowed": bool(allow),
		"model_reasoning_allowed": bool(allow),
		"final_emission_allowed": bool(allow),
		"authority_decision": AUTHORITY_DECISION_ALLOW_REPORT if allow else AUTHORITY_DECISION_BLOCK,
		"boundary_reason": "validated_safe_factual_intent" if allow else "v1_ib_contract_blocked_runtime_authority",
		"validator_status": "valid" if allow else "invalid",
		"trace_redaction_status": trace_redaction_status,
		"replayed_raw_message_safety_final_decision": "safe" if allow else "blocked",
	}


def _emit(message, boundary):
	session_doc = _Session()
	result = emit_authorized_assistant_answer(
		session_doc=session_doc,
		answer_text="LEAK_D2_SELECTED_ANSWER EC7H-ITEM-A",
		answer_type=ANSWER_TYPE_GOVERNED_REPORT,
		append_message=_append_message,
		append_tool_payload=_append_tool_payload,
		assistant_text_payload=_assistant_text_payload,
		interaction_contract=_interaction(message),
		followup_resolution=_followup(),
		execution_path=_execution_path(),
		runtime_trace_payload={"agent_meta": {"engine": "qwen"}, "tool_trace": []},
		grounded_turn_context=_grounded_turn(),
		authority_context={"normalized_family_artifact": _artifact()},
		pre_assistant_tool_payloads=[
			boundary,
			{
				"type": "qwen_selected_report_payload",
				"rows": ["LEAK_D2_ROWS"],
				"artifact": "LEAK_D2_ARTIFACT",
				"rendered_payload": "LEAK_D2_RENDERED",
				"narrative": "LEAK_D2_NARRATIVE",
				"grounded_evidence": "LEAK_D2_GROUNDED",
				"helper_payload": "LEAK_D2_HELPER",
			},
		],
	)
	return session_doc, result


class V1IBDTraceDiagnosticAuthorityConsistencyTests(unittest.TestCase):
	def assert_no_leaks(self, session_doc):
		serialized = json.dumps(session_doc.messages, sort_keys=True, default=str)
		for marker in LEAK_MARKERS:
			self.assertNotIn(marker, serialized)

	def test_final_emission_veto_rejects_stale_mismatched_and_non_redaction_safe_contracts(self):
		current = "Show EC7H-ITEM-A item sales and tell me whether to discount it"
		stale = "Show EC7H-SUP-A payable status"
		for boundary in (
			_boundary(current, allow=True, raw_source=stale),
			_boundary(current, allow=True, normalized_source=stale),
			_boundary(current, allow=True, trace_redaction_status="unsafe"),
			_boundary(current, allow=False),
		):
			with self.subTest(boundary=boundary):
				session_doc, result = _emit(current, boundary)

				self.assertTrue(result.emitted)
				self.assertEqual(result.answer_type, ANSWER_TYPE_CONTROL)
				serialized = json.dumps(session_doc.messages, sort_keys=True, default=str)
				self.assertIn(USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE, serialized)
				self.assert_no_leaks(session_doc)

	def test_final_emission_positive_control_requires_current_trace_safe_contract(self):
		current = "Show EC7H-ITEM-A item sales"
		session_doc, result = _emit(current, _boundary(current, allow=True))

		self.assertTrue(result.emitted)
		self.assertEqual(result.answer_type, ANSWER_TYPE_GOVERNED_REPORT)
		serialized = json.dumps(session_doc.messages, sort_keys=True, default=str)
		self.assertIn("LEAK_D2_SELECTED_ANSWER", serialized)
		self.assertNotIn(USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE, serialized)


if __name__ == "__main__":
	unittest.main()
