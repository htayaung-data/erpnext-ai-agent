import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_requery_planner import (
	build_nbu_governed_requery_plan,
)


class NaturalBusinessUnderstandingRequeryPlannerTests(unittest.TestCase):
	def test_not_required_when_current_artifact_can_answer(self):
		plan = build_nbu_governed_requery_plan(
			candidate_payload={
				"evidence_need": "current_artifact_ok",
				"requested_metrics": ["overdue_amount"],
			},
			validation_payload={"status": "accepted"},
			evidence_plan_payload={"current_artifact_supported": True},
			context_resolution_payload={"status": "resolved"},
			interpretation_context={},
		).to_payload()

		self.assertEqual(plan["status"], "not_required")
		self.assertEqual(plan["planner_mode"], "none")
		self.assertFalse(plan["shadow_execution_ready"])

	def test_report_registry_target_proves_capability_requery_without_phrase_mapping(self):
		plan = build_nbu_governed_requery_plan(
			candidate_payload={
				"evidence_need": "needs_governed_requery",
				"candidate_route": "fresh_query",
				"candidate_capability_ids": ["accounts_receivable_read"],
				"requested_metrics": ["credit_limit"],
				"requested_dimensions": ["customer"],
				"business_domain": "customer_credit",
			},
			validation_payload={
				"status": "accepted",
				"validation_warnings": ["current_artifact_missing_requested_field:credit_limit"],
			},
			evidence_plan_payload={
				"governed_requery_available": True,
				"missing_fields": ["credit_limit"],
			},
			context_resolution_payload={
				"status": "resolved",
				"resolved_entity": {
					"entity_type": "customer",
					"entity_label": "Ko Nay Lin Mobile Center",
					"entity_key": "Ko Nay Lin Mobile Center",
				},
			},
			interpretation_context={
				"metadata_context": {
					"reports": [
						{
							"report_name": "Customer Credit Detail",
							"capability_ids": ["accounts_receivable_read"],
							"supported_metrics": ["credit_limit", "outstanding_amount"],
							"supported_dimensions": ["customer"],
							"activation_state": "active",
						}
					]
				}
			},
		).to_payload()

		self.assertEqual(plan["status"], "ready_shadow")
		self.assertEqual(plan["planner_mode"], "entity_detail_requery")
		self.assertTrue(plan["shadow_execution_ready"])
		self.assertEqual(plan["target_capability_ids"], ["accounts_receivable_read"])
		self.assertEqual(plan["target_report_names"], ["Customer Credit Detail"])
		self.assertEqual(plan["target_entity"]["entity_label"], "Ko Nay Lin Mobile Center")
		self.assertEqual(plan["missing_fields"], ["credit_limit"])

	def test_context_ambiguity_blocks_requery_and_requires_clarification(self):
		plan = build_nbu_governed_requery_plan(
			candidate_payload={
				"evidence_need": "needs_governed_requery",
				"target_reference": "rank_n",
				"candidate_capability_ids": ["accounts_receivable_read"],
				"requested_metrics": ["credit_limit"],
			},
			validation_payload={},
			evidence_plan_payload={"governed_requery_available": True},
			context_resolution_payload={
				"status": "ambiguous",
				"ambiguity_options": ["Customer A", "Customer B"],
			},
			interpretation_context={},
		).to_payload()

		self.assertEqual(plan["status"], "needs_clarification")
		self.assertEqual(plan["planner_mode"], "context_resolution_required")
		self.assertIn("unambiguous_context_reference", plan["required_context"])
		self.assertEqual(plan["warnings"], ["Customer A", "Customer B"])

	def test_authority_boundary_blocks_requery_plan(self):
		plan = build_nbu_governed_requery_plan(
			candidate_payload={
				"evidence_need": "needs_governed_requery",
				"candidate_route": "frontdoor_composite",
				"candidate_composite_family_ids": ["customer_risk_as_of"],
				"requested_metrics": ["default_probability"],
			},
			validation_payload={"status": "blocked_by_authority_policy"},
			evidence_plan_payload={"governed_requery_available": True},
			context_resolution_payload={"status": "resolved"},
			interpretation_context={},
		).to_payload()

		self.assertEqual(plan["status"], "blocked_by_authority_policy")
		self.assertEqual(plan["planner_mode"], "authority_boundary")
		self.assertFalse(plan["shadow_execution_ready"])
		self.assertIn("approved_policy_or_authority_gate", plan["required_context"])

	def test_composite_target_uses_registered_family(self):
		plan = build_nbu_governed_requery_plan(
			candidate_payload={
				"evidence_need": "needs_governed_requery",
				"candidate_route": "frontdoor_composite",
				"candidate_composite_family_ids": ["customer_risk_as_of"],
				"requested_metrics": ["overdue_amount"],
			},
			validation_payload={},
			evidence_plan_payload={"governed_requery_available": True},
			context_resolution_payload={"status": "not_evaluated"},
			interpretation_context={
				"metadata_context": {
					"composite_families": [
						{
							"family_id": "customer_risk_as_of",
							"allowed_primary_metrics": ["overdue_amount"],
							"activation_state": "active",
						}
					]
				}
			},
		).to_payload()

		self.assertEqual(plan["status"], "ready_shadow")
		self.assertEqual(plan["planner_mode"], "composite_requery")
		self.assertEqual(plan["target_composite_family_ids"], ["customer_risk_as_of"])

	def test_no_governed_target_becomes_unsupported_boundary_plan(self):
		plan = build_nbu_governed_requery_plan(
			candidate_payload={
				"evidence_need": "needs_governed_requery",
				"requested_metrics": ["unregistered_metric"],
			},
			validation_payload={},
			evidence_plan_payload={"governed_requery_available": False},
			context_resolution_payload={"status": "not_evaluated"},
			interpretation_context={"metadata_context": {"reports": []}},
		).to_payload()

		self.assertEqual(plan["status"], "unsupported")
		self.assertEqual(plan["planner_mode"], "unsupported")
		self.assertIn("governed_report_or_capability", plan["required_context"][0])

	def test_candidate_report_name_alone_is_not_ready_when_metadata_disproves_requested_metric(self):
		plan = build_nbu_governed_requery_plan(
			candidate_payload={
				"evidence_need": "needs_governed_requery",
				"candidate_route": "fresh_query",
				"candidate_report_names": ["Accounts Receivable Aging"],
				"candidate_capability_ids": ["accounts_receivable_read"],
				"requested_metrics": ["credit_limit"],
				"requested_dimensions": ["customer"],
				"business_domain": "customer_credit",
			},
			validation_payload={
				"status": "accepted",
				"validation_warnings": ["current_artifact_missing_requested_field:credit_limit"],
			},
			evidence_plan_payload={
				"governed_requery_available": True,
				"missing_fields": ["credit_limit"],
			},
			context_resolution_payload={"status": "resolved"},
			interpretation_context={
				"metadata_context": {
					"reports": [
						{
							"report_name": "Accounts Receivable Aging",
							"capability_ids": ["accounts_receivable_read"],
							"supported_metrics": ["outstanding_amount", "overdue_amount"],
							"supported_dimensions": ["customer"],
							"semantic_tags": ["customer_credit"],
							"activation_state": "active",
						}
					]
				}
			},
		).to_payload()

		self.assertEqual(plan["status"], "unsupported")
		self.assertEqual(plan["planner_mode"], "unsupported")
		self.assertFalse(plan["shadow_execution_ready"])
		self.assertEqual(plan["target_report_names"], [])
		self.assertEqual(plan["target_capability_ids"], [])
		self.assertEqual(plan["missing_fields"], ["credit_limit"])
		self.assertEqual(plan["suggested_alternatives"][0]["report_name"], "Accounts Receivable Aging")

	def test_unsupported_exact_request_carries_nearest_governed_alternative(self):
		plan = build_nbu_governed_requery_plan(
			candidate_payload={
				"evidence_need": "needs_governed_requery",
				"candidate_route": "fresh_query",
				"candidate_capability_ids": ["accounts_receivable_read"],
				"requested_metrics": ["payment_behavior_score"],
				"requested_dimensions": ["customer"],
				"business_domain": "customer_credit",
			},
			validation_payload={"status": "accepted"},
			evidence_plan_payload={
				"governed_requery_available": True,
				"missing_fields": ["payment_behavior_score"],
			},
			context_resolution_payload={"status": "resolved"},
			interpretation_context={
				"metadata_context": {
					"reports": [
						{
							"report_name": "Accounts Receivable Aging",
							"capability_ids": ["accounts_receivable_read"],
							"supported_metrics": ["outstanding_amount", "overdue_amount"],
							"supported_dimensions": ["customer"],
							"semantic_tags": ["customer_credit"],
							"activation_state": "active",
						},
						{
							"report_name": "Sales Trend",
							"capability_ids": ["sales_read"],
							"supported_metrics": ["sales_amount"],
							"supported_dimensions": ["month"],
							"activation_state": "active",
						},
					]
				}
			},
		).to_payload()

		self.assertEqual(plan["status"], "unsupported")
		self.assertFalse(plan["shadow_execution_ready"])
		self.assertEqual(plan["suggested_alternatives"][0]["report_name"], "Accounts Receivable Aging")
		self.assertIn("overdue_amount", plan["suggested_alternatives"][0]["supported_metrics"])

	def test_entity_detail_requires_governed_target_even_when_entity_is_resolved(self):
		plan = build_nbu_governed_requery_plan(
			candidate_payload={
				"evidence_need": "needs_governed_requery",
				"candidate_route": "entity_detail",
				"requested_metrics": ["credit_limit"],
				"target_entity": {
					"entity_type": "customer",
					"entity_label": "Ko Nay Lin Mobile Center",
				},
			},
			validation_payload={"status": "accepted"},
			evidence_plan_payload={"governed_requery_available": True},
			context_resolution_payload={
				"status": "resolved",
				"resolved_entity": {
					"entity_type": "customer",
					"entity_label": "Ko Nay Lin Mobile Center",
				},
			},
			interpretation_context={"metadata_context": {"reports": []}},
		).to_payload()

		self.assertEqual(plan["status"], "unsupported")
		self.assertEqual(plan["planner_mode"], "unsupported")
		self.assertFalse(plan["shadow_execution_ready"])
		self.assertIn("governed_report_or_capability", plan["required_context"][0])

	def test_absent_metadata_allows_unverified_shadow_candidate_anchor_with_warning(self):
		plan = build_nbu_governed_requery_plan(
			candidate_payload={
				"evidence_need": "needs_governed_requery",
				"candidate_route": "fresh_query",
				"candidate_report_names": ["Future HR Attendance Summary"],
				"candidate_capability_ids": ["attendance_read"],
				"requested_metrics": ["absence_count"],
			},
			validation_payload={"status": "accepted"},
			evidence_plan_payload={"governed_requery_available": True},
			context_resolution_payload={"status": "resolved"},
			interpretation_context={},
		).to_payload()

		self.assertEqual(plan["status"], "ready_shadow")
		self.assertEqual(plan["planner_mode"], "capability_requery")
		self.assertTrue(plan["shadow_execution_ready"])
		self.assertEqual(plan["target_report_names"], ["Future HR Attendance Summary"])
		self.assertIn("metadata_context_absent_candidate_targets_unverified", plan["warnings"])


if __name__ == "__main__":
	unittest.main()
