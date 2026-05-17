import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_front_controller_cases import (
	list_nbu_front_controller_baseline_cases,
)
from ai_assistant_ui.qwen_chat.natural_business_understanding_scorecard import (
	build_current_router_trace_from_outcome,
	build_nbu_vs_current_router_scorecard,
	evaluate_current_router_outcome_against_front_controller_case,
	list_nbu_router_scorecard_outcomes,
	summarize_nbu_router_scorecards,
	validate_nbu_router_scorecard_contract,
)


def _case(case_id):
	for case in list_nbu_front_controller_baseline_cases():
		if case["case_id"] == case_id:
			return case
	raise AssertionError(f"case not found: {case_id}")


def _trace(
	*,
	action,
	response_mode,
	business_domain="customer_risk",
	family_id="customer_risk_as_of",
	target_reference="rank_n",
	rank=2,
	authority_class="safe_explanation",
	evidence_need="current_artifact_ok",
	final_confidence=0.91,
	schema_ok=True,
	schema_errors=None,
	response_text="Here is the business answer.",
	quality_warnings=None,
):
	candidate = {
		"candidate_id": "nbu-candidate-1",
		"business_domain": business_domain,
		"target_reference": target_reference,
		"target_entity": {"rank": rank} if rank else {},
		"candidate_composite_family_ids": [family_id] if family_id else [],
		"requested_metrics": ["overdue_amount"],
		"evidence_need": evidence_need,
		"authority_class": authority_class,
		"model_confidence": final_confidence,
	}
	return {
		"selected_candidate_id": "nbu-candidate-1",
		"candidate_interpretations": [candidate],
		"system_confidence": {"final_confidence": final_confidence},
		"validation_result": {
			"status": "validated",
			"validation_errors": [],
			"validation_warnings": [],
		},
		"conversation_action_decision": {
			"action": action,
			"response_mode": response_mode,
			"requires_routing_change": action.startswith("execute_"),
			"safe_to_execute": action in {
				"answer_from_current_artifact",
				"execute_fresh_governed_query",
				"execute_governed_requery",
			},
		},
		"evidence_plan": {
			"evidence_need": evidence_need,
			"current_artifact_supported": evidence_need == "current_artifact_ok",
			"governed_requery_available": evidence_need == "needs_governed_requery",
			"missing_fields": [],
		},
		"authority_plan": {"authority_class": authority_class, "boundary_reason": ""},
		"context_resolution": {
			"status": "resolved",
			"target_reference": target_reference,
			"resolved_artifact_id": family_id,
			"resolved_rank": rank,
		},
		"governed_requery_plan": {
			"status": "ready_shadow" if action.startswith("execute_") else "not_required",
			"shadow_execution_ready": action.startswith("execute_"),
		},
		"professional_response": {
			"title": "Business Answer",
			"answer_text": response_text,
			"next_steps": [],
			"safe_to_show": response_mode != "direct_answer",
			"quality_warnings": quality_warnings or [],
		},
		"schema_hardening_assessment": {
			"ok": schema_ok,
			"errors": schema_errors or [],
			"warnings": [],
		},
		"activation_assessment": {"blockers": []},
		"current_artifact": {"family_id": family_id},
	}


def _rank_2_router_outcome():
	return {
		"action": "answer_from_current_artifact",
		"response_mode": "direct_answer",
		"business_domain": "customer_risk",
		"target_reference": "rank_n",
		"rank": 2,
		"candidate_composite_family_ids": ["customer_risk_as_of"],
		"current_artifact_family_id": "customer_risk_as_of",
		"requested_metrics": ["overdue_amount"],
	}


class NaturalBusinessUnderstandingScorecardTests(unittest.TestCase):
	def test_scorecard_contract_lists_enterprise_outcomes(self):
		validation = validate_nbu_router_scorecard_contract()

		self.assertTrue(validation["ok"], validation["errors"])
		self.assertEqual(validation["outcome_count"], 6)
		outcomes = {row["outcome"] for row in list_nbu_router_scorecard_outcomes()}
		self.assertIn("nbu_correct_current_wrong", outcomes)
		self.assertIn("current_correct_nbu_wrong", outcomes)

	def test_current_router_outcome_reuses_front_controller_evaluator(self):
		report = evaluate_current_router_outcome_against_front_controller_case(
			case_payload=_case("nbu_fc0_supplier_fresh_query_context_switch"),
			current_router_outcome={
				"action": "execute_fresh_governed_query",
				"business_domain": "supplier_master",
				"candidate_capability_ids": ["supplier_master_read"],
				"target_capability_ids": ["supplier_master_read"],
			},
		)

		self.assertTrue(report["passed"], report)

	def test_current_router_trace_has_execution_ready_defaults(self):
		trace = build_current_router_trace_from_outcome(
			{
				"action": "execute_fresh_governed_query",
				"business_domain": "customer_risk",
				"candidate_composite_family_ids": ["customer_risk_as_of"],
			}
		)

		self.assertEqual(trace["conversation_action_decision"]["response_mode"], "governed_query")
		self.assertEqual(trace["governed_requery_plan"]["status"], "ready_shadow")
		self.assertTrue(trace["governed_requery_plan"]["shadow_execution_ready"])

	def test_scorecard_classifies_both_correct(self):
		scorecard = build_nbu_vs_current_router_scorecard(
			case_payload=_case("nbu_fc0_rank_2_current_artifact_answer"),
			nbu_trace_payload=_trace(action="answer_from_current_artifact", response_mode="direct_answer"),
			current_router_outcome=_rank_2_router_outcome(),
		)

		self.assertEqual(scorecard["scorecard_outcome"], "both_correct")
		self.assertTrue(scorecard["nbu_passed"])
		self.assertTrue(scorecard["current_router_passed"])

	def test_scorecard_classifies_nbu_correct_current_wrong(self):
		scorecard = build_nbu_vs_current_router_scorecard(
			case_payload=_case("nbu_fc0_customer_risk_broad_ask"),
			nbu_trace_payload=_trace(
				action="execute_fresh_governed_query",
				response_mode="governed_query",
				family_id="customer_risk_as_of",
				target_reference="none",
				rank=0,
				authority_class="safe_read",
				evidence_need="needs_governed_requery",
			),
			current_router_outcome={
				"action": "execute_fresh_governed_query",
				"business_domain": "customer_master",
				"candidate_capability_ids": ["customer_master_read"],
			},
		)

		self.assertEqual(scorecard["scorecard_outcome"], "nbu_correct_current_wrong")
		self.assertTrue(scorecard["nbu_passed"], scorecard["nbu_evaluation"])
		self.assertFalse(scorecard["current_router_passed"])

	def test_scorecard_classifies_current_correct_nbu_wrong(self):
		scorecard = build_nbu_vs_current_router_scorecard(
			case_payload=_case("nbu_fc0_rank_2_current_artifact_answer"),
			nbu_trace_payload=_trace(
				action="answer_capability_question",
				response_mode="capability_guidance",
				target_reference="none",
				rank=0,
			),
			current_router_outcome=_rank_2_router_outcome(),
		)

		self.assertEqual(scorecard["scorecard_outcome"], "current_correct_nbu_wrong")
		self.assertFalse(scorecard["nbu_passed"])
		self.assertTrue(scorecard["current_router_passed"])

	def test_scorecard_classifies_both_wrong(self):
		scorecard = build_nbu_vs_current_router_scorecard(
			case_payload=_case("nbu_fc0_rank_2_current_artifact_answer"),
			nbu_trace_payload=_trace(
				action="answer_capability_question",
				response_mode="capability_guidance",
				target_reference="none",
				rank=0,
			),
			current_router_outcome={
				"action": "execute_fresh_governed_query",
				"business_domain": "supplier_master",
				"candidate_capability_ids": ["supplier_master_read"],
			},
		)

		self.assertEqual(scorecard["scorecard_outcome"], "both_wrong")

	def test_scorecard_classifies_unsafe_nbu_before_correctness(self):
		trace = _trace(
			action="reject_with_boundary",
			response_mode="boundary",
			authority_class="prediction",
			evidence_need="needs_governed_requery",
			response_text="The runtime contract is blocked.",
			quality_warnings=["user_text_internal_term:runtime"],
		)
		trace["authority_plan"]["authority_class"] = "prediction"
		trace["authority_plan"]["boundary_reason"] = "Prediction requires an approved company rule."

		scorecard = build_nbu_vs_current_router_scorecard(
			case_payload=_case("nbu_fc0_default_prediction_boundary"),
			nbu_trace_payload=trace,
			current_router_outcome={"action": "observe_only"},
		)

		self.assertEqual(scorecard["scorecard_outcome"], "nbu_unsafe")
		self.assertIn("renderer_quality_failure", scorecard["nbu_failure_buckets"])

	def test_scorecard_classifies_low_confidence_separately(self):
		scorecard = build_nbu_vs_current_router_scorecard(
			case_payload=_case("nbu_fc0_rank_2_current_artifact_answer"),
			nbu_trace_payload=_trace(
				action="answer_from_current_artifact",
				response_mode="direct_answer",
				final_confidence=0.20,
				schema_ok=False,
				schema_errors=["confidence_below_threshold:answer_from_current_artifact"],
			),
			current_router_outcome=_rank_2_router_outcome(),
		)

		self.assertEqual(scorecard["scorecard_outcome"], "nbu_low_confidence")

	def test_scorecard_summary_counts_router_and_nbu_rates(self):
		scorecards = [
			build_nbu_vs_current_router_scorecard(
				case_payload=_case("nbu_fc0_rank_2_current_artifact_answer"),
				nbu_trace_payload=_trace(action="answer_from_current_artifact", response_mode="direct_answer"),
				current_router_outcome=_rank_2_router_outcome(),
			),
			build_nbu_vs_current_router_scorecard(
				case_payload=_case("nbu_fc0_rank_2_current_artifact_answer"),
				nbu_trace_payload=_trace(
					action="answer_capability_question",
					response_mode="capability_guidance",
					target_reference="none",
					rank=0,
				),
				current_router_outcome=_rank_2_router_outcome(),
			),
		]

		summary = summarize_nbu_router_scorecards(scorecards)

		self.assertEqual(summary["case_count"], 2)
		self.assertEqual(summary["nbu_pass_count"], 1)
		self.assertEqual(summary["current_router_pass_count"], 2)
		self.assertEqual(summary["scorecard_outcome_counts"]["both_correct"], 1)
		self.assertEqual(summary["scorecard_outcome_counts"]["current_correct_nbu_wrong"], 1)


if __name__ == "__main__":
	unittest.main()
