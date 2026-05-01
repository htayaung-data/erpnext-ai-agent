import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_validation import (
	evaluate_nbu_candidate_against_context,
)


class NaturalBusinessUnderstandingValidationTests(unittest.TestCase):
	def test_safe_current_artifact_candidate_receives_high_system_confidence(self):
		validation, confidence = evaluate_nbu_candidate_against_context(
			candidate_payload={
				"candidate_id": "candidate-1",
				"business_domain": "customer_risk",
				"target_reference": "rank_n",
				"candidate_composite_family_ids": ["customer_risk_as_of"],
				"evidence_need": "current_artifact_ok",
				"authority_class": "safe_explanation",
				"model_confidence": 0.86,
			},
			interpretation_context={
				"current_artifact": {"family_id": "customer_risk_as_of", "row_count": 10},
				"metadata_context": {
					"composite_family_ids": ["customer_risk_as_of"],
					"business_domains": ["customer_risk"],
				},
			},
		)

		self.assertEqual(validation.status, "accepted")
		self.assertGreaterEqual(validation.registry_match_strength, 0.9)
		self.assertGreaterEqual(validation.context_reference_clarity, 0.9)
		self.assertGreaterEqual(confidence.final_confidence, 0.8)
		self.assertEqual(validation.authority_policy_state, "safe_read_authority")

	def test_policy_gated_candidate_is_blocked_even_when_model_is_confident(self):
		validation, confidence = evaluate_nbu_candidate_against_context(
			candidate_payload={
				"candidate_id": "candidate-2",
				"business_domain": "customer_risk",
				"target_reference": "rank_n",
				"candidate_composite_family_ids": ["customer_risk_as_of"],
				"evidence_need": "needs_governed_requery",
				"authority_class": "prediction",
				"model_confidence": 0.94,
			},
			interpretation_context={
				"current_artifact": {"family_id": "customer_risk_as_of"},
				"metadata_context": {
					"composite_family_ids": ["customer_risk_as_of"],
					"business_domains": ["customer_risk"],
				},
			},
		)

		self.assertEqual(validation.status, "blocked_by_authority_policy")
		self.assertEqual(validation.authority_policy_state, "blocked_policy_required")
		self.assertEqual(confidence.authority_confidence, 0.0)
		self.assertEqual(confidence.final_confidence, 0.0)

	def test_future_business_domain_is_warned_not_rejected(self):
		validation, confidence = evaluate_nbu_candidate_against_context(
			candidate_payload={
				"candidate_id": "candidate-hr",
				"business_domain": "hr_attendance",
				"candidate_capability_ids": ["attendance_read"],
				"evidence_need": "needs_governed_requery",
				"authority_class": "safe_read",
				"model_confidence": 0.72,
			},
			interpretation_context={
				"metadata_context": {
					"capability_ids": ["attendance_read"],
					"business_domains": ["customer_risk"],
				},
			},
		)

		self.assertIn("future_or_unknown_business_domain:hr_attendance", validation.validation_warnings)
		self.assertGreater(validation.registry_match_strength, 0.5)
		self.assertGreater(confidence.final_confidence, 0.0)

	def test_missing_context_for_rank_reference_lowers_confidence(self):
		validation, confidence = evaluate_nbu_candidate_against_context(
			candidate_payload={
				"candidate_id": "candidate-3",
				"business_domain": "customer_risk",
				"target_reference": "rank_n",
				"candidate_composite_family_ids": ["customer_risk_as_of"],
				"evidence_need": "current_artifact_ok",
				"authority_class": "safe_explanation",
				"model_confidence": 0.91,
			},
			interpretation_context={
				"metadata_context": {
					"composite_family_ids": ["customer_risk_as_of"],
					"business_domains": ["customer_risk"],
				},
			},
		)

		self.assertLess(confidence.final_confidence, 0.35)
		self.assertIn("rank_n_without_artifact_context", validation.validation_warnings)
		self.assertIn("current_artifact_requested_but_missing", validation.validation_warnings)

	def test_report_metric_dimension_mismatch_lowers_registry_confidence(self):
		validation, confidence = evaluate_nbu_candidate_against_context(
			candidate_payload={
				"candidate_id": "candidate-report",
				"business_domain": "sales",
				"candidate_report_names": ["Sales Invoice List"],
				"requested_metrics": ["unknown_margin"],
				"requested_dimensions": ["Customer"],
				"evidence_need": "needs_governed_requery",
				"authority_class": "safe_read",
				"model_confidence": 0.88,
			},
			interpretation_context={
				"metadata_context": {
					"report_names": ["Sales Invoice List"],
					"business_domains": ["sales"],
					"reports": [
						{
							"report_name": "Sales Invoice List",
							"supported_metrics": ["Grand Total", "Quantity", "Outstanding Amount"],
							"supported_dimensions": ["Invoice", "Customer", "Posting Date"],
						}
					],
				},
			},
		)

		self.assertLess(confidence.final_confidence, 0.65)
		self.assertIn("report_missing_metric:unknown_margin", validation.validation_warnings)

	def test_composite_family_inactive_state_blocks_registry_confidence(self):
		validation, confidence = evaluate_nbu_candidate_against_context(
			candidate_payload={
				"candidate_id": "candidate-composite",
				"business_domain": "customer_risk",
				"candidate_composite_family_ids": ["customer_risk_as_of"],
				"requested_metrics": ["overdue_amount"],
				"requested_dimensions": ["customer"],
				"evidence_need": "needs_governed_requery",
				"authority_class": "safe_read",
				"model_confidence": 0.9,
			},
			interpretation_context={
				"metadata_context": {
					"composite_family_ids": ["customer_risk_as_of"],
					"business_domains": ["customer_risk"],
					"composite_families": [
						{
							"family_id": "customer_risk_as_of",
							"entity_grain": "customer",
							"allowed_primary_metrics": ["overdue_amount"],
							"allowed_secondary_metrics": ["credit_utilization"],
							"activation_state": "blocked_missing_policy",
						}
					],
				},
			},
		)

		self.assertEqual(confidence.registry_confidence, 0.0)
		self.assertIn("inactive_composite_family:customer_risk_as_of", validation.validation_warnings)

	def test_current_artifact_missing_requested_field_lowers_artifact_confidence(self):
		validation, confidence = evaluate_nbu_candidate_against_context(
			candidate_payload={
				"candidate_id": "candidate-artifact",
				"business_domain": "customer_risk",
				"target_reference": "rank_n",
				"candidate_composite_family_ids": ["customer_risk_as_of"],
				"requested_metrics": ["credit_limit"],
				"evidence_need": "current_artifact_ok",
				"authority_class": "safe_explanation",
				"model_confidence": 0.9,
			},
			interpretation_context={
				"current_artifact": {
					"family_id": "customer_risk_as_of",
					"columns": ["customer", "overdue_amount", "outstanding_amount"],
					"row_count": 10,
				},
				"metadata_context": {
					"composite_family_ids": ["customer_risk_as_of"],
					"business_domains": ["customer_risk"],
					"composite_families": [
						{
							"family_id": "customer_risk_as_of",
							"entity_grain": "customer",
							"allowed_primary_metrics": ["overdue_amount"],
							"allowed_secondary_metrics": ["credit_utilization"],
							"activation_state": "active",
						}
					],
				},
			},
		)

		self.assertEqual(validation.artifact_compatibility, 0.0)
		self.assertIn("current_artifact_missing_requested_field:credit_limit", validation.validation_warnings)
		self.assertEqual(confidence.final_confidence, 0.0)

	def test_context_family_conflict_blocks_current_artifact_followup(self):
		validation, confidence = evaluate_nbu_candidate_against_context(
			candidate_payload={
				"candidate_id": "candidate-conflict",
				"business_domain": "customer_risk",
				"target_reference": "rank_n",
				"candidate_composite_family_ids": ["customer_risk_as_of"],
				"requested_metrics": ["overdue_amount"],
				"evidence_need": "current_artifact_ok",
				"authority_class": "safe_explanation",
				"model_confidence": 0.91,
			},
			interpretation_context={
				"current_artifact": {
					"family_id": "balance_sheet",
					"title": "Balance Sheet",
					"columns": ["account", "amount"],
					"row_count": 10,
				},
				"metadata_context": {
					"composite_family_ids": ["customer_risk_as_of"],
					"business_domains": ["customer_risk"],
					"composite_families": [
						{
							"family_id": "customer_risk_as_of",
							"entity_grain": "customer",
							"allowed_primary_metrics": ["overdue_amount"],
							"activation_state": "active",
						}
					],
				},
			},
		)

		self.assertLess(validation.context_reference_clarity, 0.1)
		self.assertGreater(confidence.context_conflict_score, 0.9)
		self.assertEqual(confidence.final_confidence, 0.0)
		self.assertTrue(
			any(
				warning.startswith("context_artifact_family_conflict:")
				for warning in validation.validation_warnings
			)
		)

	def test_governed_kpi_metric_mapping_supports_registered_metric(self):
		validation, confidence = evaluate_nbu_candidate_against_context(
			candidate_payload={
				"candidate_id": "candidate-kpi",
				"business_domain": "collections",
				"candidate_capability_ids": ["sales_read", "collections_read"],
				"candidate_report_names": ["Sales Invoice List", "Payment Entry List"],
				"requested_metrics": ["collection_ratio"],
				"requested_dimensions": ["company"],
				"evidence_need": "needs_governed_requery",
				"authority_class": "safe_read",
				"model_confidence": 0.82,
			},
			interpretation_context={
				"metadata_context": {
					"capability_ids": ["sales_read", "collections_read"],
					"report_names": ["Sales Invoice List", "Payment Entry List"],
					"business_domains": ["collections"],
					"governed_kpi_executions": [
						{
							"execution_id": "collection_ratio_execution",
							"source_capabilities": ["sales_read", "collections_read"],
							"source_reports": ["Sales Invoice List", "Payment Entry List"],
							"required_dimensions": ["company"],
							"value_metric_mapping": {"value_metric": "collection_ratio"},
							"activation_state": "active",
						}
					],
				},
			},
		)

		self.assertEqual(validation.status, "accepted")
		self.assertGreaterEqual(validation.registry_match_strength, 0.8)
		self.assertGreaterEqual(confidence.final_confidence, 0.75)


if __name__ == "__main__":
	unittest.main()
