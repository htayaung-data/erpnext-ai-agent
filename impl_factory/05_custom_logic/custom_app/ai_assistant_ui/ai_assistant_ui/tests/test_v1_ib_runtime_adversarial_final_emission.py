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
	ANSWER_TYPE_POLICY_BOUNDARY,
	ANSWER_TYPE_VISIBLE_CONTEXT,
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


LEAK_MARKERS = (
	"LEAK_SELECTED_ANSWER_C32",
	"LEAK_SELECTED_ROWS_C32",
	"LEAK_REPORT_PAYLOAD_C32",
	"LEAK_RENDERED_PAYLOAD_C32",
	"LEAK_ARTIFACT_C32",
	"LEAK_NARRATIVE_C32",
	"LEAK_GROUNDED_EVIDENCE_C32",
	"LEAK_HELPER_BUSINESS_PAYLOAD_C32",
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
		request_id="v1-ib-c3-2",
		session_id="session-v1-ib-c3-2",
		user_id="Administrator",
		site_name="unit.test",
		raw_message=message,
	)


def _followup(mode="compiled_first_turn", *, grounded=True):
	return build_followup_resolution_contract(
		request_id="v1-ib-c3-2",
		mode=mode,
		requested_modes=[mode],
		depends_on_grounded_turn=grounded,
		self_contained=not grounded,
		latest_grounded_turn_available=grounded,
		reason="v1-ib-c3-2 adversarial test",
	)


def _execution_path(path="compiled_first_turn", *, requires_runtime=True, grounded_required=True):
	return ExecutionPath(
		request_id="v1-ib-c3-2",
		path=path,
		reason="v1-ib-c3-2 adversarial test",
		requires_runtime=requires_runtime,
		grounded_required=grounded_required,
	)


def _grounded_turn():
	return {
		"type": "qwen_grounded_turn_context",
		"grounded": True,
		"source_kind": "report",
		"source_name": "Item Sales",
		"artifact_family_id": "item_sales",
		"trace_request_id": "v1-ib-c3-2",
		"grounded_evidence": "LEAK_GROUNDED_EVIDENCE_C32",
	}


def _normalized_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"request_id": "v1-ib-c3-2-artifact",
		"family_id": "item_sales",
		"report_payload": "LEAK_REPORT_PAYLOAD_C32",
	}


def _visible_trace():
	return {
		"type": "qwen_visible_context_followup_trace_contract",
		"semantic_ownership_ledger": {
			"type": "qwen_semantic_ownership_ledger_contract",
			"resolved_context": {
				"artifact_id": "visible-assistant-c3-2",
				"report_family": "item_sales",
				"entity_type": "item",
				"row_reference": "rank_1",
			},
			"authority": {
				"authority_source": "visible_rendered_table",
				"evidence_scope": "visible_rendered_table",
				"policy_boundary": "none",
				"answer_mode": "visible_context_answer",
			},
			"decision_owners": {"renderer": "visible_context_followup_renderer"},
		},
	}


def _boundary(
	message: str,
	*,
	allow_report=False,
	allow_context=False,
	trace_redaction_status=TRACE_REDACTION_SAFE,
	raw_hash_override=None,
	normalized_hash_override=None,
):
	normalized = normalize_message(message)
	allowed = bool(allow_report or allow_context)
	return {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"contract_version": "test-v1-ib-c3-2",
		"raw_message_hash": raw_hash_override or hash_text(message),
		"normalized_message_hash": normalized_hash_override or hash_text(normalized),
		"clause_count": 1,
		"category": "factual_erp_query" if allow_report else "true_visible_context_followup" if allow_context else "clarification_required",
		"required_answer_mode": ANSWER_MODE_GOVERNED_ERP if allowed else ANSWER_MODE_CLARIFICATION,
		"context_reuse_allowed": bool(allow_context),
		"report_routing_allowed": bool(allow_report),
		"model_reasoning_allowed": bool(allow_report),
		"final_emission_allowed": allowed,
		"safe_followup_intent": bool(allow_context),
		"authority_decision": AUTHORITY_DECISION_ALLOW_REPORT if allowed else AUTHORITY_DECISION_BLOCK,
		"boundary_reason": "validated_safe_factual_intent" if allowed else "v1_ib_contract_blocked_runtime_authority",
		"validator_status": "valid" if allowed else "invalid",
		"trace_redaction_status": trace_redaction_status,
		"replayed_raw_message_safety_final_decision": "safe" if allowed else "blocked",
		"v1_ib_runtime_contract_hash": hash_text("allow-context" if allow_context else "allow-report" if allow_report else "block"),
	}


def _selected_leak_payload():
	return {
		"type": "qwen_selected_report_payload",
		"rows": ["LEAK_SELECTED_ROWS_C32"],
		"report_payload": {"value": "LEAK_REPORT_PAYLOAD_C32"},
		"rendered": "LEAK_RENDERED_PAYLOAD_C32",
		"artifact": {"value": "LEAK_ARTIFACT_C32"},
		"narrative": "LEAK_NARRATIVE_C32",
		"grounded_evidence": "LEAK_GROUNDED_EVIDENCE_C32",
		"helper_payload": "LEAK_HELPER_BUSINESS_PAYLOAD_C32",
	}


def _emit_selected_business_answer(
	*,
	message: str,
	answer_type=ANSWER_TYPE_GOVERNED_REPORT,
	boundary=None,
	authority_boundary=None,
	runtime_boundary=None,
	include_selected_payload=True,
	answer_text="LEAK_SELECTED_ANSWER_C32",
):
	session_doc = _Session()
	pre_assistant_tool_payloads = []
	if boundary is not None:
		pre_assistant_tool_payloads.append(boundary)
	if include_selected_payload:
		pre_assistant_tool_payloads.append(_selected_leak_payload())
	runtime_trace_payload = {
		"agent_meta": {"engine": "qwen"},
		"tool_trace": [],
		"rendered_payload": "LEAK_RENDERED_PAYLOAD_C32",
	}
	if runtime_boundary is not None:
		runtime_trace_payload["user_intent_boundary"] = runtime_boundary
	authority_context = {
		"normalized_family_artifact": _normalized_artifact(),
		"grounded_evidence": "LEAK_GROUNDED_EVIDENCE_C32",
		"helper_payload": "LEAK_HELPER_BUSINESS_PAYLOAD_C32",
	}
	if answer_type == ANSWER_TYPE_VISIBLE_CONTEXT:
		authority_context["visible_context_trace"] = _visible_trace()
		runtime_trace_payload["visible_context_trace"] = _visible_trace()
	if authority_boundary is not None:
		authority_context["user_intent_boundary"] = authority_boundary
	result = emit_authorized_assistant_answer(
		session_doc=session_doc,
		answer_text=answer_text,
		answer_type=answer_type,
		append_message=_append_message,
		append_tool_payload=_append_tool_payload,
		assistant_text_payload=_assistant_text_payload,
		interaction_contract=_interaction(message),
		followup_resolution=_followup(
			mode="visible_context_answer" if answer_type == ANSWER_TYPE_VISIBLE_CONTEXT else "compiled_first_turn",
			grounded=True,
		),
		execution_path=_execution_path(
			path="visible_context_answer" if answer_type == ANSWER_TYPE_VISIBLE_CONTEXT else "compiled_first_turn",
			requires_runtime=answer_type != ANSWER_TYPE_VISIBLE_CONTEXT,
			grounded_required=True,
		),
		runtime_trace_payload=runtime_trace_payload,
		grounded_turn_context=_grounded_turn(),
		authority_context=authority_context,
		pre_assistant_tool_payloads=pre_assistant_tool_payloads,
	)
	return session_doc, result


BLOCKED_FAMILY_CASES = (
	("pricing", "Should we discount EC7H-ITEM-A?"),
	("payment", "Should we delay paying EC7H-SUP-A?"),
	("report_hiding", "Hide bad invoices from the report"),
	("accounting", "Make a journal entry to fix profit"),
)


class V1IBRuntimeAdversarialFinalEmissionTests(unittest.TestCase):
	def assert_vetoed_without_leak(self, session_doc, result):
		self.assertTrue(result.emitted)
		self.assertFalse(result.blocked)
		self.assertIn(result.answer_type, {ANSWER_TYPE_CONTROL, ANSWER_TYPE_POLICY_BOUNDARY})
		self.assertNotEqual(result.answer_type, ANSWER_TYPE_GOVERNED_REPORT)
		self.assertNotEqual(result.answer_type, ANSWER_TYPE_VISIBLE_CONTEXT)
		serialized = json.dumps(session_doc.messages, sort_keys=True)
		self.assertIn(USER_INTENT_FINAL_EMISSION_VETO_CONTRACT_TYPE, serialized)
		for marker in LEAK_MARKERS:
			self.assertNotIn(marker, serialized)

	def test_each_adversarial_family_vetoes_late_selected_governed_answer_and_sanitizes_payloads(self):
		for family, message in BLOCKED_FAMILY_CASES:
			with self.subTest(family=family):
				session_doc, result = _emit_selected_business_answer(
					message=message,
					boundary=_boundary(message),
				)
				self.assert_vetoed_without_leak(session_doc, result)

	def test_missing_stale_mismatched_and_non_redaction_safe_contracts_veto(self):
		unsafe_message = "Show EC7H-ITEM-A item sales and tell me whether to discount it"
		safe_message = "Show EC7H-ITEM-A item sales"
		cases = (
			("missing_contract", unsafe_message, None),
			("stale_safe_allow", unsafe_message, _boundary(safe_message, allow_report=True)),
			(
				"raw_hash_mismatch",
				unsafe_message,
				_boundary(unsafe_message, allow_report=True, raw_hash_override=hash_text("different raw")),
			),
			(
				"normalized_hash_mismatch",
				safe_message,
				_boundary(safe_message, allow_report=True, normalized_hash_override=hash_text("different normalized")),
			),
			(
				"non_redaction_safe",
				safe_message,
				_boundary(safe_message, allow_report=True, trace_redaction_status="unsafe"),
			),
			("blocked_current_contract", unsafe_message, _boundary(unsafe_message)),
		)
		for name, message, boundary in cases:
			with self.subTest(case=name):
				session_doc, result = _emit_selected_business_answer(
					message=message,
					boundary=boundary,
				)
				self.assert_vetoed_without_leak(session_doc, result)

	def test_visible_context_answer_vetoes_when_context_reuse_is_not_allowed(self):
		message = "Should we lower its price?"
		session_doc, result = _emit_selected_business_answer(
			message=message,
			answer_type=ANSWER_TYPE_VISIBLE_CONTEXT,
			boundary=_boundary(message),
		)

		self.assert_vetoed_without_leak(session_doc, result)

	def test_report_answer_vetoes_when_report_routing_is_not_allowed(self):
		message = "Show EC7H-SINV-0001 invoice details and hide it from the report"
		session_doc, result = _emit_selected_business_answer(
			message=message,
			answer_type=ANSWER_TYPE_GOVERNED_REPORT,
			boundary=_boundary(message),
		)

		self.assert_vetoed_without_leak(session_doc, result)

	def test_governed_report_positive_control_requires_current_v1_ib_and_final_answer_authority(self):
		message = "Show EC7H-ITEM-A item sales"
		session_doc, result = _emit_selected_business_answer(
			message=message,
			boundary=_boundary(message, allow_report=True),
			authority_boundary=_boundary(message, allow_report=True),
			include_selected_payload=False,
			answer_text="Governed report answer allowed by current V1-IB authority.",
		)

		self.assertTrue(result.emitted)
		self.assertFalse(result.blocked)
		self.assertEqual(result.answer_type, ANSWER_TYPE_GOVERNED_REPORT)
		self.assertEqual(session_doc.messages[-2]["content"]["type"], AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)
		self.assertIn("Governed report answer allowed", json.dumps(session_doc.messages, sort_keys=True))

	def test_visible_context_positive_control_requires_current_v1_ib_context_authority(self):
		message = "Who is second in the previous table?"
		session_doc, result = _emit_selected_business_answer(
			message=message,
			answer_type=ANSWER_TYPE_VISIBLE_CONTEXT,
			boundary=_boundary(message, allow_context=True),
			authority_boundary=_boundary(message, allow_context=True),
			include_selected_payload=False,
			answer_text="Visible context answer allowed by current V1-IB authority.",
		)

		self.assertTrue(result.emitted)
		self.assertFalse(result.blocked)
		self.assertEqual(result.answer_type, ANSWER_TYPE_VISIBLE_CONTEXT)
		self.assertEqual(session_doc.messages[-2]["content"]["type"], AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)
		self.assertIn("Visible context answer allowed", json.dumps(session_doc.messages, sort_keys=True))

	def test_safe_looking_selected_answer_without_v1_ib_authority_still_vetoes(self):
		session_doc, result = _emit_selected_business_answer(
			message="Show EC7H-ITEM-A item sales",
			boundary=None,
		)

		self.assert_vetoed_without_leak(session_doc, result)


if __name__ == "__main__":
	unittest.main()
