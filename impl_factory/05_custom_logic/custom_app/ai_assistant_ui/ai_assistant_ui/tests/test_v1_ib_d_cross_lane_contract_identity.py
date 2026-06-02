from __future__ import annotations

import sys
import types
import unittest

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


def _boundary(
	message: str,
	*,
	allow_report: bool = False,
	allow_context: bool = False,
	raw_source: str | None = None,
	normalized_source: str | None = None,
	trace_redaction_status: str = TRACE_REDACTION_SAFE,
	malformed: bool = False,
):
	raw_source = raw_source if raw_source is not None else message
	normalized_source = normalized_source if normalized_source is not None else raw_source
	payload = {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"contract_version": "test-v1-ib-d-2",
		"raw_message_hash": hash_text(raw_source),
		"normalized_message_hash": hash_text(normalize_message(normalized_source)),
		"clause_count": 1,
		"category": "factual_erp_query" if allow_report or allow_context else "clarification_required",
		"required_answer_mode": ANSWER_MODE_GOVERNED_ERP if allow_report else ANSWER_MODE_CLARIFICATION,
		"context_reuse_allowed": bool(allow_context),
		"report_routing_allowed": bool(allow_report),
		"model_reasoning_allowed": bool(allow_report),
		"final_emission_allowed": bool(allow_report),
		"safe_followup_intent": bool(allow_context),
		"decision_intent": False,
		"advice_intent": False,
		"business_action_intent": False,
		"policy_boundary_intent": False,
		"mixed_intent_detected": False if allow_report or allow_context else True,
		"ambiguity_status": "none",
		"authority_decision": AUTHORITY_DECISION_ALLOW_REPORT if allow_report else AUTHORITY_DECISION_BLOCK,
		"boundary_reason": "validated_safe_factual_intent" if allow_report or allow_context else "blocked",
		"validator_status": "valid" if allow_report or allow_context else "invalid",
		"trace_redaction_status": trace_redaction_status,
		"replayed_raw_message_safety_final_decision": "safe" if allow_report or allow_context else "blocked",
	}
	if malformed:
		payload.pop("type", None)
		payload.pop("raw_message_hash", None)
	return payload


class V1IBDCrossLaneContractIdentityTests(unittest.TestCase):
	def test_visible_context_identity_requires_current_trace_safe_contract(self):
		current = "Who is second in the previous table?"
		stale = "Show EC7H-SUP-A payable status"
		current_boundary = _boundary(current, allow_context=True)
		stale_boundary = _boundary(current, allow_context=True, raw_source=stale)
		normalized_mismatch = _boundary(current, allow_context=True, normalized_source=stale)
		non_redaction_safe = _boundary(current, allow_context=True, trace_redaction_status="unsafe")
		malformed = _boundary(current, allow_context=True, malformed=True)

		self.assertTrue(service._user_intent_boundary_context_reuse_allowed(current_boundary, raw_message=current))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(current_boundary))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(current_boundary, raw_message=None))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(current_boundary, raw_message="   "))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(stale_boundary, raw_message=current))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(normalized_mismatch, raw_message=current))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(non_redaction_safe, raw_message=current))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(malformed, raw_message=current))

	def test_report_routing_helper_requires_current_contract_identity(self):
		current = "Show EC7H-ITEM-A item sales"
		stale = "Show EC7H-SUP-A payable status"
		current_boundary = _boundary(current, allow_report=True)
		stale_boundary = _boundary(current, allow_report=True, raw_source=stale)
		normalized_mismatch = _boundary(current, allow_report=True, normalized_source=stale)
		non_redaction_safe = _boundary(current, allow_report=True, trace_redaction_status="unsafe")
		malformed = _boundary(current, allow_report=True, malformed=True)
		invalid_validator = {**current_boundary, "validator_status": "invalid"}
		non_governed = {**current_boundary, "required_answer_mode": ANSWER_MODE_CLARIFICATION}
		non_allow = {**current_boundary, "authority_decision": AUTHORITY_DECISION_BLOCK}
		unsafe_replay = {**current_boundary, "replayed_raw_message_safety_final_decision": "blocked"}
		decision_intent = {**current_boundary, "decision_intent": True}
		mixed_intent = {**current_boundary, "mixed_intent_detected": True}
		ambiguous_intent = {**current_boundary, "ambiguity_status": "ambiguous"}

		self.assertFalse(service._user_intent_boundary_report_routing_allowed(current_boundary))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(current_boundary, raw_message=None))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(current_boundary, raw_message="   "))
		self.assertTrue(service._user_intent_boundary_report_routing_allowed(current_boundary, raw_message=current))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(stale_boundary, raw_message=current))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(normalized_mismatch, raw_message=current))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(non_redaction_safe, raw_message=current))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(malformed, raw_message=current))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(invalid_validator, raw_message=current))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(non_governed, raw_message=current))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(non_allow, raw_message=current))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(unsafe_replay, raw_message=current))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(decision_intent, raw_message=current))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(mixed_intent, raw_message=current))
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(ambiguous_intent, raw_message=current))

	def test_pre_routing_gate_must_not_skip_boundary_response_for_stale_allow_contract(self):
		current = "Show EC7H-ITEM-A item sales"
		stale = "Show EC7H-SUP-A payable status"
		stale_boundary = _boundary(current, allow_report=True, raw_source=stale)
		current_boundary = _boundary(current, allow_report=True)

		self.assertTrue(service._user_intent_boundary_pre_routing_response_required(stale_boundary, raw_message=current))
		self.assertFalse(service._user_intent_boundary_pre_routing_response_required(current_boundary, raw_message=current))


if __name__ == "__main__":
	unittest.main()
