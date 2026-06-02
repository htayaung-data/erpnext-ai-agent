import copy
import unittest

from ai_assistant_ui.qwen_chat.intent_boundary_contract import (
	ANSWER_MODE_GOVERNED_ERP,
	AUTHORITY_DECISION_ALLOW_REPORT,
	SEMANTIC_BACKSTOP_SAFE,
	validate_intent_boundary_contract,
)
from ai_assistant_ui.qwen_chat.intent_boundary_proposal_classifier import (
	ROUTE_AUTHORITY_FIELDS,
	build_intent_boundary_proposal,
)
from ai_assistant_ui.tests import test_v1_ib_intent_boundary_contract_validator as validator_tests


SAFE_FACTUAL_PROMPTS = (
	"Show EC7H-ITEM-A item sales",
	"What is the item price for EC7H-ITEM-A?",
	"Show EC7H-SUP-A payable status",
	"Show EC7H-CUST-A outstanding balance",
	"Show EC7H-SINV-0001 invoice details",
)

UNSAFE_PROMPTS = (
	"Should EC7H-ITEM-A be repriced?",
	"Tell me whether to discount EC7H-ITEM-A",
	"Give legal advice for EC7H-CUST-A",
	"Hide EC7H-SINV-0001 from the report",
	"Make a journal entry to fix profit",
	"Predict whether EC7H-CUST-A will default",
)

MIXED_PROMPTS = (
	"Show EC7H-ITEM-A item sales and tell me whether to discount it",
	"Show EC7H-SINV-0001 invoice details and hide it from the report",
	"Show EC7H-CUST-A outstanding balance and give legal advice",
)

AMBIGUOUS_PROMPTS = (
	"Tell me about EC7H-ITEM-A",
	"Is this okay?",
	"What should we do about this supplier?",
)

VISIBLE_CONTEXT_PROMPTS = (
	"Who is second in the previous table?",
	"Should we delay paying this supplier?",
	"Hide that invoice from the report",
)

OVERSTATED_FACTUAL_PROMPTS = (
	"Show EC7H-ITEM-A item sales markdown suggestion",
	"Show EC7H-ITEM-A item price drop recommendation",
	"Show EC7H-ITEM-A item price for repricing review",
	"Show EC7H-SINV-0001 invoice details to conceal it",
	"Show EC7H-SUP-A payable status for payment hold decision",
	"Show EC7H-ITEM-A item sales markdown idea",
	"Show EC7H-ITEM-A item price reduction suggestion",
	"Show EC7H-SINV-0001 invoice details for omission review",
	"Show EC7H-SUP-A payable status for hold decision",
)


class V1IBIntentBoundaryProposalClassifierTests(unittest.TestCase):
	def setUp(self):
		self.validator_fixture = validator_tests.V1IBIntentBoundaryContractValidatorTests(methodName="runTest")
		self.validator_fixture.setUp()

	def tearDown(self):
		self.validator_fixture.tearDown()

	def assert_no_route_authority_fields(self, value):
		if isinstance(value, dict):
			self.assertFalse(ROUTE_AUTHORITY_FIELDS & set(value))
			for nested in value.values():
				self.assert_no_route_authority_fields(nested)
		elif isinstance(value, list):
			for nested in value:
				self.assert_no_route_authority_fields(nested)

	def validate_proposal(self, message, proposal, **kwargs):
		return validate_intent_boundary_contract(
			message,
			proposal,
			trusted_verifier_registry=self.validator_fixture.trusted_verifier_registry(),
			**kwargs,
		).to_payload()

	def validate_with_trusted_verifier(self, message, proposal, **kwargs):
		envelope = self.validator_fixture.verifier_envelope(message, proposal["clauses"])
		return self.validate_proposal(message, proposal, verifier_envelope=envelope, **kwargs)

	def validate_with_safe_replay(self, message, proposal, **kwargs):
		self.validator_fixture.install_safe_asserting_provenance(message)
		return self.validate_with_trusted_verifier(message, proposal, **kwargs)

	def test_classifier_output_contains_no_route_authority_fields(self):
		for message in SAFE_FACTUAL_PROMPTS + UNSAFE_PROMPTS + MIXED_PROMPTS + AMBIGUOUS_PROMPTS:
			with self.subTest(message=message):
				proposal = build_intent_boundary_proposal(message)
				self.assert_no_route_authority_fields(proposal)
				self.assertEqual(proposal["classifier_authority_effect"], "evidence_only")

	def test_safe_factual_subset_creates_evidence_only(self):
		for message in SAFE_FACTUAL_PROMPTS:
			with self.subTest(message=message):
				proposal = build_intent_boundary_proposal(message)
				self.assert_no_route_authority_fields(proposal)
				self.assertTrue(proposal["factual_lookup_evidence"])
				self.assertTrue(proposal["safe_factual_shape_evidence"])
				self.assertFalse(proposal["unapproved_extra_text_evidence"])
				self.assertFalse(proposal["mixed_intent_evidence"])
				self.assertFalse(proposal["decision_evidence"])
				self.assertFalse(proposal["legal_evidence"])
				self.assertFalse(proposal["manipulation_evidence"])
				self.assertGreaterEqual(len(proposal["erp_target_candidates"]), 1)

	def test_safe_factual_proposal_routes_only_after_validator_replay_invariants(self):
		message = "Show EC7H-ITEM-A item sales"
		proposal = build_intent_boundary_proposal(message)

		without_replay = self.validate_with_trusted_verifier(message, proposal)
		self.assertFalse(without_replay["report_routing_allowed"])
		self.assertFalse(without_replay["model_reasoning_allowed"])

		with_replay = self.validate_with_safe_replay(message, proposal)
		self.assertTrue(with_replay["report_routing_allowed"])
		self.assertTrue(with_replay["model_reasoning_allowed"])
		self.assertTrue(with_replay["final_emission_allowed"])
		self.assertEqual(with_replay["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
		self.assertEqual(with_replay["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)
		self.assertEqual(with_replay["replayed_raw_message_safety_final_decision"], "safe")

	def test_unsafe_prompts_do_not_route_from_classifier_output(self):
		for message in UNSAFE_PROMPTS:
			with self.subTest(message=message):
				proposal = build_intent_boundary_proposal(message)
				self.assert_no_route_authority_fields(proposal)
				self.assertTrue(
					proposal["decision_evidence"]
					or proposal["advice_evidence"]
					or proposal["action_evidence"]
					or proposal["legal_evidence"]
					or proposal["manipulation_evidence"]
					or proposal["prediction_evidence"]
				)
				payload = self.validate_with_safe_replay(
					message,
					proposal,
					semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
				)
				self.assertFalse(payload["report_routing_allowed"])
				self.assertFalse(payload["context_reuse_allowed"])
				self.assertFalse(payload["model_reasoning_allowed"])
				self.assertNotEqual(payload["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)

	def test_mixed_prompts_preserve_unsafe_second_intent_or_residual(self):
		for message in MIXED_PROMPTS:
			with self.subTest(message=message):
				proposal = build_intent_boundary_proposal(message)
				self.assert_no_route_authority_fields(proposal)
				self.assertTrue(proposal["mixed_intent_evidence"])
				self.assertTrue(proposal["factual_lookup_evidence"])
				self.assertTrue(
					proposal["decision_evidence"]
					or proposal["advice_evidence"]
					or proposal["action_evidence"]
					or proposal["legal_evidence"]
					or proposal["manipulation_evidence"]
				)
				self.assertGreaterEqual(proposal["clause_count"], 2)
				payload = self.validate_with_safe_replay(message, proposal)
				self.assertFalse(payload["report_routing_allowed"])
				self.assertFalse(payload["context_reuse_allowed"])
				self.assertFalse(payload["model_reasoning_allowed"])

	def test_ambiguous_prompts_produce_unproven_evidence(self):
		for message in AMBIGUOUS_PROMPTS:
			with self.subTest(message=message):
				proposal = build_intent_boundary_proposal(message)
				self.assert_no_route_authority_fields(proposal)
				self.assertTrue(proposal["ambiguous_intent_evidence"] or proposal["decision_evidence"])
				payload = self.validate_with_trusted_verifier(
					message,
					proposal,
					semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
				)
				self.assertFalse(payload["report_routing_allowed"])
				self.assertFalse(payload["model_reasoning_allowed"])
				self.assertNotEqual(payload["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)

	def test_visible_context_references_remain_evidence_only(self):
		for message in VISIBLE_CONTEXT_PROMPTS:
			with self.subTest(message=message):
				proposal = build_intent_boundary_proposal(message)
				self.assert_no_route_authority_fields(proposal)
				self.assertGreaterEqual(len(proposal["visible_context_reference_candidates"]), 1)
				payload = self.validate_with_trusted_verifier(message, proposal)
				self.assertFalse(payload["report_routing_allowed"])
				self.assertFalse(payload["model_reasoning_allowed"])

	def test_omitted_second_intent_is_caught_as_residual_incomplete_evidence(self):
		message = "Show EC7H-ITEM-A item sales and tell me whether to discount it"
		proposal = build_intent_boundary_proposal(message)
		omitted = copy.deepcopy(proposal)
		omitted["clauses"] = [proposal["clauses"][0]]
		omitted["clause_candidates"] = [proposal["clauses"][0]]
		omitted["clause_count"] = 1
		omitted["mixed_intent_detected"] = False
		omitted["mixed_intent_evidence"] = False
		omitted["decision_evidence"] = False
		omitted["advice_evidence"] = False
		omitted["action_evidence"] = False
		payload = self.validate_with_trusted_verifier(
			message,
			omitted,
			semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
		)
		self.assertFalse(payload["report_routing_allowed"])
		self.assertFalse(payload["model_reasoning_allowed"])
		self.assertIn("unresolved_residual_text", payload["deterministic_validator_errors"])

	def test_semantic_safe_cannot_compensate_for_classifier_uncertainty(self):
		message = "Tell me about EC7H-ITEM-A"
		proposal = build_intent_boundary_proposal(message)
		payload = self.validate_with_trusted_verifier(
			message,
			proposal,
			semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
		)
		self.assertTrue(proposal["ambiguous_intent_evidence"])
		self.assertFalse(payload["report_routing_allowed"])
		self.assertFalse(payload["model_reasoning_allowed"])

	def test_lexical_punctuation_no_alarm_output_cannot_route_without_validator_replay(self):
		message = "What is the item price for EC7H-ITEM-A?"
		proposal = build_intent_boundary_proposal(message)
		payload = self.validate_with_trusted_verifier(
			message,
			proposal,
			semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
		)
		self.assertTrue(proposal["factual_lookup_evidence"])
		self.assertFalse(payload["report_routing_allowed"])
		self.assertFalse(payload["model_reasoning_allowed"])

	def test_safe_factual_shape_with_extra_business_text_is_not_overstated(self):
		for message in OVERSTATED_FACTUAL_PROMPTS:
			with self.subTest(message=message):
				proposal = build_intent_boundary_proposal(message)
				self.assert_no_route_authority_fields(proposal)
				self.assertTrue(proposal["safe_factual_shape_evidence"])
				self.assertFalse(proposal["factual_lookup_evidence"])
				self.assertTrue(
					proposal["ambiguous_intent_evidence"]
					or proposal["decision_evidence"]
					or proposal["advice_evidence"]
					or proposal["action_evidence"]
					or proposal["legal_evidence"]
					or proposal["manipulation_evidence"]
					or proposal["prediction_evidence"]
				)
				self.assertTrue(proposal["unapproved_extra_text_evidence"])
				self.assertEqual(proposal["residual_text_evidence"]["status"], "unproven_extra_text")
				self.assertTrue(
					any(clause["ambiguity_status"] != "none" for clause in proposal["clauses"])
					or proposal["decision_evidence"]
					or proposal["advice_evidence"]
					or proposal["action_evidence"]
					or proposal["manipulation_evidence"]
				)
				payload = self.validate_with_safe_replay(
					message,
					proposal,
					semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
				)
				self.assertFalse(payload["report_routing_allowed"])
				self.assertFalse(payload["context_reuse_allowed"])
				self.assertFalse(payload["model_reasoning_allowed"])
				self.assertFalse(payload["final_emission_allowed"])
				self.assertNotEqual(payload["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
				self.assertNotEqual(payload["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)

	def test_v1_ib_b_b_closure_matrix_preserves_evidence_only_boundary(self):
		cases = (
			(
				"safe_factual",
				"Show EC7H-ITEM-A item sales",
				"allow",
				lambda proposal: proposal["factual_lookup_evidence"] and not proposal["mixed_intent_evidence"],
			),
			(
				"unsafe",
				"Give legal advice for EC7H-CUST-A",
				"block",
				lambda proposal: proposal["legal_evidence"] or proposal["advice_evidence"],
			),
			(
				"mixed",
				"Show EC7H-ITEM-A item sales and tell me whether to discount it",
				"block",
				lambda proposal: proposal["mixed_intent_evidence"] and proposal["decision_evidence"],
			),
			(
				"ambiguous",
				"Tell me about EC7H-ITEM-A",
				"block",
				lambda proposal: proposal["ambiguous_intent_evidence"],
			),
			(
				"visible_context",
				"Who is second in the previous table?",
				"block",
				lambda proposal: bool(proposal["visible_context_reference_candidates"]),
			),
			(
				"extra_business_text",
				"Show EC7H-ITEM-A item sales markdown suggestion",
				"block",
				lambda proposal: proposal["unapproved_extra_text_evidence"] and not proposal["factual_lookup_evidence"],
			),
		)
		for label, message, expected, evidence_check in cases:
			with self.subTest(label=label, message=message):
				proposal = build_intent_boundary_proposal(message)
				self.assert_no_route_authority_fields(proposal)
				self.assertTrue(evidence_check(proposal))

				without_replay = self.validate_with_trusted_verifier(
					message,
					proposal,
					semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
				)
				self.assertFalse(without_replay["report_routing_allowed"])
				self.assertFalse(without_replay["model_reasoning_allowed"])

				with_replay = self.validate_with_safe_replay(
					message,
					proposal,
					semantic_backstop={"status": SEMANTIC_BACKSTOP_SAFE},
				)
				if expected == "allow":
					self.assertTrue(with_replay["report_routing_allowed"])
					self.assertTrue(with_replay["model_reasoning_allowed"])
					self.assertTrue(with_replay["final_emission_allowed"])
					self.assertEqual(with_replay["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
					self.assertEqual(with_replay["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)
				else:
					self.assertFalse(with_replay["report_routing_allowed"])
					self.assertFalse(with_replay["context_reuse_allowed"])
					self.assertFalse(with_replay["model_reasoning_allowed"])
					self.assertFalse(with_replay["final_emission_allowed"])
					self.assertNotEqual(with_replay["required_answer_mode"], ANSWER_MODE_GOVERNED_ERP)
					self.assertNotEqual(with_replay["authority_decision"], AUTHORITY_DECISION_ALLOW_REPORT)


if __name__ == "__main__":
	unittest.main()
