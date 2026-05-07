import unittest

from ai_assistant_ui.qwen_chat.semantic_reasoning_activation import (
	SemanticReasoningActivationResult,
	_build_activation_context,
	_validate_semantic_payload,
)


class TestSemanticReasoningActivationContract(unittest.TestCase):
	def _context(self, *, recommendation_allowed=False):
		return {
			"allowed_reasoning_types": [
				"interpretation",
				"explanation",
				"recommendation",
				"continuation_detail",
			],
			"recommendation_allowed": recommendation_allowed,
		}

	def test_legacy_interpretation_payload_gets_consultant_defaults(self):
		intent = _validate_semantic_payload(
			payload={
				"reasoning_type": "interpretation",
				"detail_level": "default",
				"presentation_style": "default",
				"confidence": 0.91,
			},
			context=self._context(),
		)
		self.assertIsNotNone(intent)
		self.assertEqual(intent.response_mode, "consultant_interpretation")
		self.assertEqual(intent.evidence_policy, "current_result_only")
		self.assertEqual(intent.answer_obligation, "explain_grounded_meaning")
		self.assertEqual(intent.answer_goal, "explain")
		self.assertEqual(intent.evidence_depth, "current_result_only")
		self.assertEqual(intent.business_role, "business_consultant")
		self.assertEqual(intent.target_reference, "current_result")
		self.assertEqual(intent.risk_level, "bounded_consultation")

	def test_continuation_detail_prefers_evidence_expansion(self):
		intent = _validate_semantic_payload(
			payload={
				"reasoning_type": "continuation_detail",
				"detail_level": "comprehensive",
				"presentation_style": "default",
				"confidence": 0.94,
			},
			context=self._context(),
		)
		self.assertIsNotNone(intent)
		self.assertEqual(intent.presentation_style, "bullet")
		self.assertEqual(intent.response_mode, "consultant_detail")
		self.assertEqual(intent.evidence_policy, "evidence_expansion_required")
		self.assertEqual(intent.answer_obligation, "expand_grounded_detail")
		self.assertEqual(intent.answer_goal, "expand_detail")
		self.assertEqual(intent.evidence_depth, "drilldown_required")
		self.assertEqual(intent.target_reference, "current_result")
		self.assertEqual(intent.risk_level, "bounded_consultation")

	def test_invalid_consultant_fields_are_normalized_to_safe_contract(self):
		intent = _validate_semantic_payload(
			payload={
				"reasoning_type": "explanation",
				"detail_level": "expanded",
				"presentation_style": "bullet",
				"response_mode": "free_form_answer",
				"evidence_policy": "guess_if_needed",
				"answer_obligation": "make_it_sound_good",
				"confidence": 0.89,
			},
			context=self._context(),
		)
		self.assertIsNotNone(intent)
		self.assertEqual(intent.response_mode, "consultant_interpretation")
		self.assertEqual(intent.evidence_policy, "current_result_only")
		self.assertEqual(intent.answer_obligation, "explain_grounded_basis")
		self.assertEqual(intent.answer_goal, "explain")
		self.assertEqual(intent.evidence_depth, "current_result_only")
		self.assertEqual(intent.business_role, "business_consultant")
		self.assertEqual(intent.target_reference, "current_result")
		self.assertEqual(intent.risk_level, "bounded_consultation")

	def test_recommendation_without_policy_becomes_boundary_guidance(self):
		intent = _validate_semantic_payload(
			payload={
				"reasoning_type": "recommendation",
				"detail_level": "default",
				"presentation_style": "default",
				"confidence": 0.88,
			},
			context=self._context(recommendation_allowed=False),
		)
		self.assertIsNotNone(intent)
		self.assertEqual(intent.response_mode, "boundary_guidance")
		self.assertEqual(intent.evidence_policy, "policy_required")
		self.assertEqual(intent.answer_obligation, "state_boundary_and_next_step")
		self.assertEqual(intent.answer_goal, "clarify_boundary")
		self.assertEqual(intent.evidence_depth, "policy_required")
		self.assertEqual(intent.risk_level, "policy_required")

	def test_payload_exposes_consultant_contract_fields(self):
		intent = _validate_semantic_payload(
			payload={
				"reasoning_type": "recommendation",
				"detail_level": "expanded",
				"presentation_style": "bullet",
				"response_mode": "consultant_recommendation",
				"evidence_policy": "evidence_expansion_preferred",
				"answer_obligation": "advise_with_approved_policy",
				"answer_goal": "recommend",
				"evidence_depth": "drilldown_preferred",
				"business_role": "controller",
				"target_reference": "current_metric",
				"risk_level": "bounded_consultation",
				"confidence": 0.95,
			},
			context=self._context(recommendation_allowed=True),
		)
		result = SemanticReasoningActivationResult(status="accepted", intent=intent)
		payload = result.to_payload()
		self.assertEqual(payload["intent"]["response_mode"], "consultant_recommendation")
		self.assertEqual(payload["intent"]["evidence_policy"], "evidence_expansion_preferred")
		self.assertEqual(payload["intent"]["answer_obligation"], "advise_with_approved_policy")
		self.assertEqual(payload["intent"]["answer_goal"], "recommend")
		self.assertEqual(payload["intent"]["evidence_depth"], "drilldown_preferred")
		self.assertEqual(payload["intent"]["business_role"], "controller")
		self.assertEqual(payload["intent"]["target_reference"], "current_metric")
		self.assertEqual(payload["intent"]["risk_level"], "bounded_consultation")

	def test_semantic_detail_intent_defaults_use_governed_context_not_user_keywords(self):
		intent = _validate_semantic_payload(
			payload={
				"reasoning_type": "continuation_detail",
				"detail_level": "expanded",
				"presentation_style": "default",
				"confidence": 0.93,
			},
			context={
				**self._context(),
				"grounded_family_id": "accounts_receivable",
				"grounded_capability_id": "accounts_receivable_read",
				"prior_offered_next_action_count": 1,
			},
		)
		self.assertIsNotNone(intent)
		self.assertEqual(intent.answer_goal, "expand_detail")
		self.assertEqual(intent.evidence_depth, "drilldown_preferred")
		self.assertEqual(intent.business_role, "collector")
		self.assertEqual(intent.target_reference, "offered_next_action")
		self.assertEqual(intent.risk_level, "bounded_consultation")

	def test_invalid_semantic_detail_intent_slots_normalize_to_safe_defaults(self):
		intent = _validate_semantic_payload(
			payload={
				"reasoning_type": "interpretation",
				"detail_level": "default",
				"presentation_style": "default",
				"answer_goal": "say_whatever",
				"evidence_depth": "browse_everywhere",
				"business_role": "fortune_teller",
				"target_reference": "secret_table",
				"risk_level": "guaranteed_prediction",
				"confidence": 0.93,
			},
			context={
				**self._context(),
				"grounded_family_id": "financial_statement",
				"grounded_capability_id": "financial_statement_read",
			},
		)
		self.assertIsNotNone(intent)
		self.assertEqual(intent.answer_goal, "explain")
		self.assertEqual(intent.evidence_depth, "current_result_only")
		self.assertEqual(intent.business_role, "controller")
		self.assertEqual(intent.target_reference, "current_result")
		self.assertEqual(intent.risk_level, "bounded_consultation")

	def test_activation_context_carries_prior_offered_next_actions(self):
		context = _build_activation_context(
			activation_contract={
				"activation_state": "eligible",
				"grounded_context_available": True,
				"allowed_reasoning_types": ["continuation_detail"],
			},
			prior_reasoning_contract={
				"reasoning_type": "interpretation",
				"offered_next_actions": [
					{
						"action_id": "compare_listed_parties_by_overdue_amount_and_intensity",
						"execution_mode": "current_governed_artifact",
						"capability_id": "accounts_receivable_read",
					}
				],
			},
		)
		self.assertTrue(context["prior_reasoning_available"])
		self.assertEqual(context["prior_offered_next_action_count"], 1)
		self.assertEqual(
			context["prior_offered_next_actions"][0]["execution_mode"],
			"current_governed_artifact",
		)


if __name__ == "__main__":
	unittest.main()
