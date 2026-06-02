from __future__ import annotations

import json
import sys
import types
import unittest

if "frappe" not in sys.modules:
	sys.modules["frappe"] = types.SimpleNamespace(
		local=types.SimpleNamespace(site="unit.test"),
		get_doc=lambda *_args, **_kwargs: None,
		get_traceback=lambda: "",
		log_error=lambda *_args, **_kwargs: None,
	)

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
from ai_assistant_ui.qwen_chat.intent_boundary_runtime_integration import (
	USER_INTENT_BOUNDARY_CONTRACT_TYPE,
	build_v1_ib_runtime_boundary,
	merge_v1_ib_with_legacy_boundary,
	v1_ib_runtime_contract_metadata,
)
from ai_assistant_ui.qwen_chat.intent_boundary_proposal_classifier import build_intent_boundary_proposal
from ai_assistant_ui.tests import test_v1_ib_intent_boundary_contract_validator as validator_tests


class _Contract:
	def __init__(self, payload):
		self.payload = dict(payload)

	def to_payload(self):
		return dict(self.payload)


def _base_contract_payload(message: str, **overrides):
	normalized = normalize_message(message)
	payload = {
		"contract_version": "test-v1-ib",
		"raw_message_hash": hash_text(message),
		"normalized_message_hash": hash_text(normalized),
		"clause_count": 1,
		"factual_lookup_intent": True,
		"safe_followup_intent": False,
		"decision_intent": False,
		"advice_intent": False,
		"business_action_intent": False,
		"policy_boundary_intent": False,
		"mixed_intent_detected": False,
		"business_action_domain": "none",
		"policy_domain": "none",
		"ambiguity_status": "none",
		"report_routing_allowed": True,
		"context_reuse_allowed": False,
		"model_reasoning_allowed": True,
		"final_emission_allowed": True,
		"required_answer_mode": ANSWER_MODE_GOVERNED_ERP,
		"boundary_reason": "validator_test_contract",
		"validator_status": "valid",
		"trace_redaction_status": TRACE_REDACTION_SAFE,
		"authority_decision": AUTHORITY_DECISION_ALLOW_REPORT,
		"authority_source": "deterministic_validator",
		"authority_blocking_reason": "",
		"deterministic_validator_errors": [],
		"residual_text_status": "clear",
		"connector_coverage_status": "complete",
		"pronoun_reference_status": "complete",
		"replayed_raw_message_safety_final_decision": "safe",
		"replayed_raw_message_safety_status": "passed",
		"replayed_raw_message_safety_evidence_match_status": "matched",
	}
	payload.update(overrides)
	return payload


def _allowing_legacy():
	return {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"category": "factual_erp_query",
		"required_answer_mode": ANSWER_MODE_GOVERNED_ERP,
		"context_reuse_allowed": True,
		"report_routing_allowed": True,
		"boundary_reason": "legacy_allows",
	}


def _blocking_legacy():
	return {
		"type": USER_INTENT_BOUNDARY_CONTRACT_TYPE,
		"category": "clarification_required",
		"required_answer_mode": ANSWER_MODE_CLARIFICATION,
		"context_reuse_allowed": False,
		"report_routing_allowed": False,
		"boundary_reason": "legacy_blocks",
	}


class V1IBRuntimeIntegrationTests(unittest.TestCase):
	def test_safe_report_routes_only_from_validated_replay_safe_contract(self):
		message = "Show EC7H-ITEM-A item sales"
		boundary = build_v1_ib_runtime_boundary(
			message,
			proposal_builder=lambda raw: {"classifier_route_field_should_not_matter": True},
			contract_validator=lambda raw, proposal, **kwargs: _Contract(_base_contract_payload(raw)),
		)

		self.assertTrue(boundary["report_routing_allowed"])
		self.assertTrue(boundary["model_reasoning_allowed"])
		self.assertTrue(boundary["final_emission_allowed"])
		self.assertEqual(boundary["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
		self.assertEqual(boundary["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)

	def test_safe_report_routes_through_accepted_validator_replay_fixture(self):
		message = "Show EC7H-ITEM-A item sales"
		fixture = validator_tests.V1IBIntentBoundaryContractValidatorTests(methodName="runTest")
		fixture.setUp()
		try:
			proposal = build_intent_boundary_proposal(message)
			fixture.install_safe_asserting_provenance(message)
			boundary = build_v1_ib_runtime_boundary(
				message,
				verifier_envelope=fixture.verifier_envelope(message, proposal["clauses"]),
				trusted_verifier_registry=fixture.trusted_verifier_registry(),
			)
		finally:
			fixture.tearDown()

		self.assertTrue(boundary["report_routing_allowed"])
		self.assertTrue(boundary["model_reasoning_allowed"])
		self.assertTrue(boundary["final_emission_allowed"])
		self.assertEqual(boundary["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
		self.assertEqual(boundary["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)

	def test_classifier_output_alone_cannot_route(self):
		message = "Show EC7H-ITEM-A item sales"
		boundary = build_v1_ib_runtime_boundary(
			message,
			proposal_builder=lambda raw: {
				"report_routing_allowed": True,
				"model_reasoning_allowed": True,
				"authority_decision": AUTHORITY_DECISION_ALLOW_REPORT,
			},
			contract_validator=None,
		)

		self.assertFalse(boundary["report_routing_allowed"])
		self.assertFalse(boundary["context_reuse_allowed"])
		self.assertFalse(boundary["model_reasoning_allowed"])
		self.assertFalse(boundary["final_emission_allowed"])
		self.assertEqual(boundary["authority_decision"], AUTHORITY_DECISION_BLOCK)

	def test_replay_missing_blocks_even_when_contract_claims_report_allowed(self):
		message = "Show EC7H-ITEM-A item sales"
		boundary = build_v1_ib_runtime_boundary(
			message,
			proposal_builder=lambda raw: {},
			contract_validator=lambda raw, proposal, **kwargs: _Contract(
				_base_contract_payload(raw, replayed_raw_message_safety_final_decision="blocked")
			),
		)

		self.assertFalse(boundary["report_routing_allowed"])
		self.assertFalse(boundary["model_reasoning_allowed"])
		self.assertFalse(boundary["final_emission_allowed"])
		self.assertNotEqual(boundary["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)

	def test_missing_or_exceptional_classifier_and_validator_fail_closed(self):
		def raises(_raw):
			raise RuntimeError("boom")

		cases = (
			{"proposal_builder": None, "contract_validator": lambda raw, proposal, **kwargs: _Contract({})},
			{"proposal_builder": raises, "contract_validator": lambda raw, proposal, **kwargs: _Contract({})},
			{"proposal_builder": lambda raw: {}, "contract_validator": None},
			{"proposal_builder": lambda raw: {}, "contract_validator": lambda raw, proposal, **kwargs: (_ for _ in ()).throw(RuntimeError("boom"))},
		)
		for kwargs in cases:
			with self.subTest(kwargs=sorted(kwargs)):
				boundary = build_v1_ib_runtime_boundary("Show EC7H-ITEM-A item sales", **kwargs)
				self.assertFalse(boundary["report_routing_allowed"])
				self.assertFalse(boundary["context_reuse_allowed"])
				self.assertFalse(boundary["model_reasoning_allowed"])
				self.assertFalse(boundary["final_emission_allowed"])
				self.assertEqual(boundary["authority_decision"], AUTHORITY_DECISION_BLOCK)

	def test_v1_block_overrides_legacy_allow(self):
		blocked = build_v1_ib_runtime_boundary(
			"Show EC7H-ITEM-A item sales and tell me whether to discount it",
			proposal_builder=lambda raw: {},
			contract_validator=lambda raw, proposal, **kwargs: _Contract(
				_base_contract_payload(
					raw,
					report_routing_allowed=False,
					model_reasoning_allowed=False,
					final_emission_allowed=False,
					required_answer_mode=ANSWER_MODE_CLARIFICATION,
					authority_decision=AUTHORITY_DECISION_BLOCK,
					replayed_raw_message_safety_final_decision="blocked",
				)
			),
		)
		merged = merge_v1_ib_with_legacy_boundary(blocked, _allowing_legacy())

		self.assertFalse(merged["report_routing_allowed"])
		self.assertFalse(merged["context_reuse_allowed"])
		self.assertEqual(merged["authority_decision"], AUTHORITY_DECISION_BLOCK)

	def test_legacy_block_conservatively_restricts_v1_allow(self):
		allowed = build_v1_ib_runtime_boundary(
			"Show EC7H-ITEM-A item sales",
			proposal_builder=lambda raw: {},
			contract_validator=lambda raw, proposal, **kwargs: _Contract(_base_contract_payload(raw)),
		)
		merged = merge_v1_ib_with_legacy_boundary(allowed, _blocking_legacy())

		self.assertFalse(merged["report_routing_allowed"])
		self.assertFalse(merged["model_reasoning_allowed"])
		self.assertFalse(merged["final_emission_allowed"])
		self.assertEqual(merged["authority_decision"], AUTHORITY_DECISION_BLOCK)

	def test_service_gates_fail_closed_on_missing_contract(self):
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(None))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(None))
		self.assertTrue(service._user_intent_boundary_pre_routing_response_required(None))

	def test_visible_context_requires_contract_context_allow(self):
		message = "Who is second in the previous table?"
		boundary_without_context = build_v1_ib_runtime_boundary(
			message,
			proposal_builder=lambda raw: {},
			contract_validator=lambda raw, proposal, **kwargs: _Contract(
				_base_contract_payload(
					raw,
					factual_lookup_intent=False,
					safe_followup_intent=True,
					report_routing_allowed=False,
					context_reuse_allowed=False,
					model_reasoning_allowed=False,
				)
			),
		)
		context_boundary = build_v1_ib_runtime_boundary(
			message,
			proposal_builder=lambda raw: {},
			contract_validator=lambda raw, proposal, **kwargs: _Contract(
				_base_contract_payload(
					raw,
					factual_lookup_intent=False,
					safe_followup_intent=True,
					report_routing_allowed=False,
					context_reuse_allowed=True,
					model_reasoning_allowed=False,
				)
			),
		)

		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(None))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(boundary_without_context, raw_message=message))
		self.assertFalse(service._user_intent_boundary_context_reuse_allowed(context_boundary))
		self.assertTrue(service._user_intent_boundary_context_reuse_allowed(context_boundary, raw_message=message))
		self.assertFalse(
			service._user_intent_boundary_context_reuse_allowed(
				context_boundary,
				raw_message="Show EC7H-SUP-A payable status",
			)
		)
		self.assertFalse(service._user_intent_boundary_report_routing_allowed(context_boundary))

	def test_real_classifier_and_validator_default_fail_closed_for_mixed_prompt(self):
		boundary = build_v1_ib_runtime_boundary("Show EC7H-ITEM-A item sales and tell me whether to discount it")

		self.assertFalse(boundary["report_routing_allowed"])
		self.assertFalse(boundary["context_reuse_allowed"])
		self.assertFalse(boundary["model_reasoning_allowed"])
		self.assertFalse(boundary["final_emission_allowed"])
		self.assertNotEqual(boundary["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)

	def test_runtime_metadata_is_redaction_safe(self):
		boundary = build_v1_ib_runtime_boundary(
			"Show EC7H-ITEM-A item sales",
			proposal_builder=lambda raw: {},
			contract_validator=lambda raw, proposal, **kwargs: _Contract(_base_contract_payload(raw)),
		)
		metadata = v1_ib_runtime_contract_metadata(boundary)
		serialized = json.dumps(metadata, sort_keys=True)

		self.assertEqual(metadata["type"], "qwen_v1_ib_runtime_contract_metadata")
		self.assertNotIn("EC7H-ITEM-A", serialized)
		self.assertNotIn("item sales", serialized)
		self.assertNotIn("Show ", serialized)


if __name__ == "__main__":
	unittest.main()
