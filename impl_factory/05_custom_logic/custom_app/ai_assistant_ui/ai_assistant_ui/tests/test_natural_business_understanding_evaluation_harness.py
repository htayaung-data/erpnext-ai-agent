import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_evaluation_harness import (
	evaluate_nbu_trace_against_front_controller_case,
	list_nbu_evaluation_failure_taxonomy,
	summarize_nbu_front_controller_evaluations,
	validate_nbu_evaluation_failure_taxonomy,
	validate_nbu_front_controller_evaluation_harness,
)
from ai_assistant_ui.qwen_chat.natural_business_understanding_front_controller_cases import (
	list_nbu_front_controller_baseline_cases,
)


def _case(case_id):
	for case in list_nbu_front_controller_baseline_cases():
		if case["case_id"] == case_id:
			return case
	raise AssertionError(f"case not found: {case_id}")


def _base_trace(*, action, response_mode, candidate=None, context=None, response=None, schema_ok=True):
	candidate_payload = candidate or {
		"candidate_id": "candidate-1",
		"business_domain": "customer_risk",
		"target_reference": "rank_n",
		"candidate_composite_family_ids": ["customer_risk_as_of"],
		"requested_metrics": ["overdue_amount"],
		"evidence_need": "current_artifact_ok",
		"authority_class": "safe_explanation",
	}
	return {
		"selected_candidate_id": candidate_payload.get("candidate_id", "candidate-1"),
		"candidate_interpretations": [candidate_payload],
		"system_confidence": {"final_confidence": 0.91},
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
			"evidence_need": candidate_payload.get("evidence_need", "current_artifact_ok"),
			"current_artifact_supported": candidate_payload.get("evidence_need") == "current_artifact_ok",
			"governed_requery_available": candidate_payload.get("evidence_need") == "needs_governed_requery",
			"missing_fields": [],
		},
		"authority_plan": {
			"authority_class": candidate_payload.get("authority_class", "safe_explanation"),
			"boundary_reason": "",
		},
		"context_resolution": context or {
			"status": "resolved",
			"target_reference": candidate_payload.get("target_reference", "rank_n"),
			"resolved_artifact_id": "customer-risk-artifact-1",
			"resolved_rank": 2,
		},
		"governed_requery_plan": {"status": "not_required"},
		"professional_response": response or {
			"title": "Business Answer",
			"answer_text": "Here is the business answer.",
			"next_steps": [],
			"safe_to_show": response_mode != "direct_answer",
			"quality_warnings": [],
		},
		"schema_hardening_assessment": {"ok": schema_ok, "errors": [] if schema_ok else ["schema_error"], "warnings": []},
		"activation_assessment": {"blockers": []},
		"current_artifact": {"family_id": "customer_risk_as_of"},
	}


class NaturalBusinessUnderstandingEvaluationHarnessTests(unittest.TestCase):
	def test_failure_taxonomy_is_complete_and_business_named(self):
		validation = validate_nbu_evaluation_failure_taxonomy()

		self.assertTrue(validation["ok"], validation["errors"])
		self.assertEqual(validation["bucket_count"], 8)
		bucket_ids = {bucket["bucket_id"] for bucket in list_nbu_evaluation_failure_taxonomy()}
		self.assertIn("model_misunderstanding", bucket_ids)
		self.assertIn("renderer_quality_failure", bucket_ids)

	def test_evaluation_harness_validates_against_baseline_registry(self):
		validation = validate_nbu_front_controller_evaluation_harness()

		self.assertTrue(validation["ok"], validation["errors"])
		self.assertGreaterEqual(validation["baseline_case_count"], 10)

	def test_rank_2_current_artifact_trace_passes_expected_case(self):
		report = evaluate_nbu_trace_against_front_controller_case(
			case_payload=_case("nbu_fc0_rank_2_current_artifact_answer"),
			trace_payload=_base_trace(action="answer_from_current_artifact", response_mode="direct_answer"),
		)

		self.assertTrue(report["passed"], report)
		self.assertEqual(report["failure_buckets"], [])
		self.assertTrue(report["action_match"])
		self.assertTrue(report["target_match"])

	def test_action_mismatch_is_model_misunderstanding(self):
		report = evaluate_nbu_trace_against_front_controller_case(
			case_payload=_case("nbu_fc0_rank_2_current_artifact_answer"),
			trace_payload=_base_trace(action="answer_capability_question", response_mode="capability_guidance"),
		)

		self.assertFalse(report["passed"])
		self.assertIn("model_misunderstanding", report["failure_buckets"])
		self.assertFalse(report["action_match"])

	def test_previous_artifact_target_mismatch_is_context_graph_failure(self):
		trace = _base_trace(
			action="answer_from_current_artifact",
			response_mode="direct_answer",
			candidate={
				"candidate_id": "candidate-previous",
				"business_domain": "customer_risk",
				"target_reference": "current_artifact",
				"candidate_composite_family_ids": ["supplier_master"],
				"requested_metrics": ["supplier_name"],
				"evidence_need": "current_artifact_ok",
				"authority_class": "safe_explanation",
			},
			context={
				"status": "resolved",
				"target_reference": "current_artifact",
				"resolved_artifact_id": "supplier-list-1",
				"resolved_rank": 2,
			},
		)

		report = evaluate_nbu_trace_against_front_controller_case(
			case_payload=_case("nbu_fc0_above_ar_table_previous_context"),
			trace_payload=trace,
		)

		self.assertFalse(report["passed"])
		self.assertIn("context_graph_failure", report["failure_buckets"])

	def test_expected_policy_boundary_passes_with_policy_evidence_diagnostic(self):
		trace = _base_trace(
			action="reject_with_boundary",
			response_mode="boundary",
			candidate={
				"candidate_id": "candidate-policy",
				"business_domain": "customer_risk",
				"target_reference": "rank_n",
				"candidate_composite_family_ids": ["customer_risk_as_of"],
				"evidence_need": "needs_governed_requery",
				"authority_class": "prediction",
			},
			response={
				"title": "Decision Not Available Yet",
				"answer_text": "I can show the ERP facts, but I cannot safely predict this without an approved company rule.",
				"next_steps": ["ask for aging or payment history"],
				"safe_to_show": True,
				"quality_warnings": [],
			},
		)
		trace["authority_plan"]["authority_class"] = "prediction"
		trace["authority_plan"]["boundary_reason"] = "Prediction requires an approved company rule."
		trace["governed_requery_plan"] = {"status": "blocked_by_authority_policy"}

		report = evaluate_nbu_trace_against_front_controller_case(
			case_payload=_case("nbu_fc0_default_prediction_boundary"),
			trace_payload=trace,
		)

		self.assertTrue(report["passed"], report)
		self.assertEqual(report["failure_buckets"], [])
		self.assertIn("policy_evidence_gap", report["diagnostic_buckets"])

	def test_renderer_quality_warning_becomes_failure_bucket(self):
		trace = _base_trace(
			action="reject_with_boundary",
			response_mode="boundary",
			candidate={
				"candidate_id": "candidate-policy",
				"business_domain": "customer_risk",
				"target_reference": "rank_n",
				"candidate_composite_family_ids": ["customer_risk_as_of"],
				"evidence_need": "needs_governed_requery",
				"authority_class": "prediction",
			},
			response={
				"title": "Governed Boundary",
				"answer_text": "The runtime contract is blocked.",
				"next_steps": [],
				"safe_to_show": True,
				"quality_warnings": ["user_text_internal_term:runtime"],
			},
		)
		trace["authority_plan"]["authority_class"] = "prediction"
		trace["authority_plan"]["boundary_reason"] = "Prediction requires an approved company rule."

		report = evaluate_nbu_trace_against_front_controller_case(
			case_payload=_case("nbu_fc0_default_prediction_boundary"),
			trace_payload=trace,
		)

		self.assertFalse(report["passed"])
		self.assertIn("renderer_quality_failure", report["failure_buckets"])

	def test_runtime_unavailable_is_latency_runtime_bucket(self):
		trace = {
			"candidate_interpretations": [],
			"validation_result": {"status": "runtime_unavailable", "validation_errors": ["offline"]},
			"conversation_action_decision": {"action": "observe_only", "response_mode": "shadow_trace_only"},
			"professional_response": {"safe_to_show": False, "quality_warnings": []},
			"schema_hardening_assessment": {"ok": True, "errors": [], "warnings": []},
		}

		report = evaluate_nbu_trace_against_front_controller_case(
			case_payload=_case("nbu_fc0_customer_risk_broad_ask"),
			trace_payload=trace,
			latency_ms=4100,
			latency_budget_ms=2500,
		)

		self.assertFalse(report["passed"])
		self.assertIn("latency_runtime_unavailable", report["failure_buckets"])

	def test_summary_counts_passes_and_failure_buckets(self):
		pass_report = evaluate_nbu_trace_against_front_controller_case(
			case_payload=_case("nbu_fc0_rank_2_current_artifact_answer"),
			trace_payload=_base_trace(action="answer_from_current_artifact", response_mode="direct_answer"),
		)
		fail_report = evaluate_nbu_trace_against_front_controller_case(
			case_payload=_case("nbu_fc0_rank_2_current_artifact_answer"),
			trace_payload=_base_trace(action="answer_capability_question", response_mode="capability_guidance"),
		)

		summary = summarize_nbu_front_controller_evaluations([pass_report, fail_report])

		self.assertEqual(summary["case_count"], 2)
		self.assertEqual(summary["pass_count"], 1)
		self.assertEqual(summary["fail_count"], 1)
		self.assertEqual(summary["failure_bucket_counts"]["model_misunderstanding"], 1)


if __name__ == "__main__":
	unittest.main()
