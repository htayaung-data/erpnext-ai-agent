import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_contracts import (
	NBUEvidencePlanContract,
	NBUGovernedRequeryPlanContract,
	NBUSystemConfidenceContract,
	NBUConversationActionDecisionContract,
	NBUContextResolutionContract,
	NBUValidationResultContract,
	build_nbu_candidate_interpretation_contract,
	build_nbu_trace_contract,
)


class NaturalBusinessUnderstandingContractTests(unittest.TestCase):
	def test_candidate_contract_serializes_ranked_business_interpretation(self):
		candidate = build_nbu_candidate_interpretation_contract(
			candidate_id="candidate-1",
			intent_scope="fresh_query",
			business_domain="customer_risk",
			requested_action="show",
			target_reference="none",
			candidate_route="frontdoor_composite",
			candidate_composite_family_ids=["customer_risk_as_of"],
			requested_metrics=["overdue_amount", "credit_utilization"],
			evidence_need="current_artifact_ok",
			authority_class="safe_read",
			model_confidence=1.7,
			model_reason="The message asks for customer risk ranking.",
		)

		payload = candidate.to_payload()

		self.assertEqual(payload["type"], "qwen_nbu_candidate_interpretation_contract")
		self.assertEqual(payload["contract_version"], "1.0")
		self.assertEqual(payload["business_domain"], "customer_risk")
		self.assertEqual(payload["candidate_composite_family_ids"], ["customer_risk_as_of"])
		self.assertEqual(payload["model_confidence"], 1.0)

	def test_candidate_contract_keeps_future_family_domain_extensible(self):
		candidate = build_nbu_candidate_interpretation_contract(
			candidate_id="candidate-hr",
			intent_scope="fresh_query",
			business_domain="hr_attendance",
			requested_action="show",
			candidate_route="fresh_query",
			candidate_capability_ids=["attendance_read"],
			candidate_report_names=["Attendance Summary"],
			authority_class="safe_read",
			model_confidence=0.81,
		)

		payload = candidate.to_payload()

		self.assertEqual(payload["business_domain"], "hr_attendance")
		self.assertEqual(payload["candidate_capability_ids"], ["attendance_read"])
		self.assertEqual(payload["candidate_report_names"], ["Attendance Summary"])

	def test_candidate_contract_unknowns_invalid_enum_values_without_rejecting_trace(self):
		candidate = build_nbu_candidate_interpretation_contract(
			candidate_id="candidate-invalid",
			intent_scope="magic",
			requested_action="teleport",
			target_reference="moon",
			candidate_route="unknown_lane",
			evidence_need="unsupported_magic",
			authority_class="wizardry",
		)

		payload = candidate.to_payload()

		self.assertEqual(payload["intent_scope"], "unknown")
		self.assertEqual(payload["requested_action"], "unknown")
		self.assertEqual(payload["target_reference"], "unknown")
		self.assertEqual(payload["candidate_route"], "unknown")
		self.assertEqual(payload["evidence_need"], "unknown")
		self.assertEqual(payload["authority_class"], "unknown")

	def test_trace_contract_serializes_shadow_mode_decision_trace(self):
		candidate = build_nbu_candidate_interpretation_contract(
			candidate_id="candidate-1",
			intent_scope="context_reference",
			business_domain="customer_risk",
			requested_action="explain",
			target_reference="rank_n",
			candidate_route="local_followup",
			evidence_need="current_artifact_ok",
			authority_class="safe_explanation",
			model_confidence=0.88,
		)
		trace = build_nbu_trace_contract(
			request_id="nbu-test-1",
			session_id="session-1",
			raw_message="why is the first customer risky?",
			candidate_interpretations=[candidate],
			selected_candidate_id="candidate-1",
			validation_result=NBUValidationResultContract(
				status="accepted",
				registry_match_strength=0.9,
				context_reference_clarity=1.0,
				artifact_compatibility=1.0,
				evidence_availability=1.0,
				authority_policy_state="safe",
			),
			system_confidence=NBUSystemConfidenceContract(
				model_confidence=0.88,
				registry_confidence=0.9,
				context_confidence=1.0,
				evidence_confidence=1.0,
				authority_confidence=1.0,
				context_conflict_score=0.0,
				final_confidence=0.94,
				confidence_basis=["model", "registry", "context", "evidence", "authority"],
			),
			conversation_action_decision=NBUConversationActionDecisionContract(
				action="answer_from_current_artifact",
				response_mode="direct_answer",
				selected_candidate_id="candidate-1",
				requires_routing_change=False,
				safe_to_execute=True,
				reason="Current customer-risk artifact has rank 1 evidence.",
			),
			evidence_plan=NBUEvidencePlanContract(
				evidence_need="current_artifact_ok",
				current_artifact_supported=True,
				governed_requery_available=False,
			),
			context_resolution=NBUContextResolutionContract(
				status="resolved",
				target_reference="rank_n",
				resolved_row_index=0,
				resolved_rank=1,
				resolved_entity={"entity_type": "customer", "entity_name": "35th Street Mobile Wholesale"},
			),
			governed_requery_plan=NBUGovernedRequeryPlanContract(
				status="not_required",
				planner_mode="none",
				reason="Current artifact can answer.",
			),
			trace_summary="NBU resolved rank 1 against current customer-risk artifact.",
			shadow_mode=True,
		)

		payload = trace.to_payload()

		self.assertEqual(payload["type"], "qwen_natural_business_understanding_trace_contract")
		self.assertEqual(payload["selected_candidate_id"], "candidate-1")
		self.assertTrue(payload["shadow_mode"])
		self.assertEqual(payload["conversation_action_decision"]["action"], "answer_from_current_artifact")
		self.assertEqual(payload["context_resolution"]["resolved_rank"], 1)
		self.assertEqual(payload["governed_requery_plan"]["status"], "not_required")
		self.assertEqual(len(payload["candidate_interpretations"]), 1)

	def test_trace_contract_defaults_to_observe_only_without_behavior_change(self):
		trace = build_nbu_trace_contract(
			request_id="nbu-test-2",
			session_id="session-2",
			raw_message="show customer risk",
		)

		payload = trace.to_payload()

		self.assertTrue(payload["shadow_mode"])
		self.assertEqual(payload["conversation_action_decision"]["action"], "observe_only")
		self.assertEqual(payload["conversation_action_decision"]["response_mode"], "shadow_trace_only")
		self.assertFalse(payload["conversation_action_decision"]["requires_routing_change"])
		self.assertFalse(payload["conversation_action_decision"]["safe_to_execute"])
		self.assertEqual(payload["governed_requery_plan"]["status"], "not_evaluated")

	def test_governed_requery_plan_serializes_suggested_alternatives(self):
		plan = NBUGovernedRequeryPlanContract(
			status="unsupported",
			planner_mode="unsupported",
			suggested_alternatives=[
				{
					"target_type": "report",
					"report_name": "Customer Credit Detail",
					"supported_metrics": ["credit_limit"],
					"ignored_non_dict": ["kept because value is part of dict"],
				},
				"not a dict",
			],
		)

		payload = plan.to_payload()

		self.assertEqual(
			payload["suggested_alternatives"],
			[
				{
					"target_type": "report",
					"report_name": "Customer Credit Detail",
					"supported_metrics": ["credit_limit"],
					"ignored_non_dict": ["kept because value is part of dict"],
				}
			],
		)


if __name__ == "__main__":
	unittest.main()
