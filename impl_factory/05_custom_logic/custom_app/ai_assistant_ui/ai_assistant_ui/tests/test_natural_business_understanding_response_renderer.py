import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_response_renderer import (
	render_nbu_professional_response,
)


class NaturalBusinessUnderstandingResponseRendererTests(unittest.TestCase):
	def assertUserShowableTextIsProfessional(self, response):
		self.assertTrue(response["safe_to_show"])
		self.assertEqual(response["quality_warnings"], [])
		combined = " ".join([response["title"], response["answer_text"]] + response["next_steps"]).lower()
		for term in ("qwen", "contract", "planner", "shadow", "runtime", "live activation", "blocked_missing_policy", "governed"):
			self.assertNotIn(term, combined)

	def test_clarification_renderer_uses_business_natural_options(self):
		response = render_nbu_professional_response(
			{
				"shadow_mode": True,
				"conversation_action_decision": {
					"action": "ask_clarification",
					"response_mode": "clarification",
				},
				"context_resolution": {
					"status": "ambiguous",
					"target_reference": "candidate_list",
					"ambiguity_options": ["Type-C Cable 2m Fast Charge", "Type-C Cable 1m Fast Charge"],
				},
				"governed_requery_plan": {"status": "needs_clarification"},
			}
		)

		self.assertEqual(response["title"], "Clarification Needed")
		self.assertUserShowableTextIsProfessional(response)
		self.assertIn("which option", response["answer_text"])
		self.assertEqual(response["next_steps"], ["Type-C Cable 2m Fast Charge", "Type-C Cable 1m Fast Charge"])
		self.assertNotIn("contract", response["answer_text"].lower())

	def test_clarification_renderer_translates_internal_capability_ids_to_business_labels(self):
		response = render_nbu_professional_response(
			{
				"shadow_mode": True,
				"conversation_action_decision": {
					"action": "ask_clarification",
					"response_mode": "clarification",
				},
				"context_resolution": {
					"status": "ambiguous",
					"target_reference": "candidate_list",
					"ambiguity_options": ["Cash Flow", "financial_statement_read"],
				},
				"governed_requery_plan": {"status": "needs_clarification"},
			}
		)

		self.assertEqual(response["title"], "Clarification Needed")
		self.assertUserShowableTextIsProfessional(response)
		self.assertEqual(response["next_steps"], ["Cash Flow", "financial statements"])
		self.assertNotIn("financial_statement_read", " ".join(response["next_steps"]))

	def test_policy_boundary_renderer_hides_internal_gate_language(self):
		response = render_nbu_professional_response(
			{
				"shadow_mode": True,
				"conversation_action_decision": {
					"action": "reject_with_boundary",
					"response_mode": "boundary",
				},
				"authority_plan": {
					"authority_class": "prediction",
					"policy_artifact_required": "approved_policy_artifact_required",
					"approval_state": "blocked_missing_policy",
				},
				"governed_requery_plan": {"status": "blocked_by_authority_policy"},
			}
		)

		self.assertEqual(response["title"], "Decision Not Available Yet")
		self.assertUserShowableTextIsProfessional(response)
		self.assertEqual(response["boundary_class"], "prediction")
		self.assertIn("ERP facts", response["answer_text"])
		self.assertIn("company rule", response["answer_text"])
		self.assertNotIn("blocked_missing_policy", response["answer_text"])
		self.assertNotIn("approved_policy_artifact_required", response["answer_text"])

	def test_unsupported_renderer_surfaces_nearest_governed_options(self):
		response = render_nbu_professional_response(
			{
				"shadow_mode": True,
				"conversation_action_decision": {
					"action": "ask_clarification",
					"response_mode": "clarification",
				},
				"evidence_plan": {
					"missing_fields": ["payment_behavior_score"],
				},
				"governed_requery_plan": {
					"status": "unsupported",
					"suggested_alternatives": [
						{
							"target_type": "report",
							"report_name": "Accounts Receivable Aging",
							"supported_metrics": ["outstanding_amount", "overdue_amount"],
							"supported_dimensions": ["customer"],
						}
					],
				},
			}
		)

		self.assertEqual(response["title"], "Nearest ERP Options")
		self.assertUserShowableTextIsProfessional(response)
		self.assertIn("payment behavior score", response["answer_text"])
		self.assertIn("Accounts Receivable Aging", response["next_steps"][0])
		self.assertIn("overdue_amount", response["next_steps"][0])
		self.assertNotIn("qwen", response["answer_text"].lower())

	def test_missing_evidence_renderer_names_missing_fields_without_internal_language(self):
		response = render_nbu_professional_response(
			{
				"shadow_mode": True,
				"conversation_action_decision": {
					"action": "ask_clarification",
					"response_mode": "clarification",
				},
				"candidate_interpretations": [
					{
						"candidate_id": "candidate-1",
						"requested_metrics": ["credit_limit"],
						"requested_dimensions": ["customer"],
					}
				],
				"selected_candidate_id": "candidate-1",
				"evidence_plan": {
					"missing_fields": ["credit_limit"],
				},
				"governed_requery_plan": {
					"status": "unsupported",
					"missing_fields": ["credit_limit"],
					"suggested_alternatives": [],
				},
			}
		)

		self.assertEqual(response["title"], "Missing Data For This Answer")
		self.assertUserShowableTextIsProfessional(response)
		self.assertEqual(response["boundary_class"], "unsupported_evidence")
		self.assertIn("credit limit", response["answer_text"])
		self.assertIn("ERP report or source", response["next_steps"][0])
		self.assertNotIn("qwen", response["answer_text"].lower())
		self.assertNotIn("contract", response["answer_text"].lower())

	def test_governed_requery_renderer_describes_target_without_execution_claim(self):
		response = render_nbu_professional_response(
			{
				"shadow_mode": True,
				"conversation_action_decision": {
					"action": "execute_governed_requery",
					"response_mode": "governed_query",
				},
				"context_resolution": {
					"status": "resolved",
					"resolved_entity": {"entity_label": "Ko Nay Lin Mobile Center"},
				},
				"governed_requery_plan": {
					"status": "ready_shadow",
					"planner_mode": "entity_detail_requery",
					"target_report_names": ["Customer Credit Detail"],
				},
			}
		)

		self.assertEqual(response["title"], "ERP Source Available")
		self.assertUserShowableTextIsProfessional(response)
		self.assertIn("Ko Nay Lin Mobile Center", response["answer_text"])
		self.assertIn("Customer Credit Detail", response["answer_text"])
		self.assertFalse(response["technical_details"]["live_execution_enabled"])
		self.assertNotIn("activation", response["next_steps"][0].lower())

	def test_capability_guidance_uses_candidate_targets_without_mapping_dictionary(self):
		response = render_nbu_professional_response(
			{
				"shadow_mode": True,
				"conversation_action_decision": {
					"action": "answer_capability_question",
					"response_mode": "capability_guidance",
				},
				"candidate_interpretations": [
					{
						"candidate_id": "candidate-capability",
						"business_domain": "customer_risk",
						"candidate_report_names": ["Accounts Receivable Aging"],
						"candidate_composite_family_ids": ["customer_risk_as_of"],
					}
				],
				"selected_candidate_id": "candidate-capability",
				"governed_requery_plan": {"status": "not_required"},
			}
		)

		self.assertEqual(response["title"], "What I Can Help With")
		self.assertUserShowableTextIsProfessional(response)
		self.assertIn("customer risk", response["answer_text"])
		self.assertEqual(response["next_steps"][:2], ["Accounts Receivable Aging", "customer risk as of"])

	def test_out_of_scope_guides_user_back_to_erp_context(self):
		response = render_nbu_professional_response(
			{
				"shadow_mode": True,
				"conversation_action_decision": {
					"action": "out_of_scope_response",
					"response_mode": "out_of_scope",
				},
				"candidate_interpretations": [
					{
						"candidate_id": "candidate-oos",
						"business_domain": "inventory",
					}
				],
				"selected_candidate_id": "candidate-oos",
				"governed_requery_plan": {"status": "not_required"},
			}
		)

		self.assertEqual(response["title"], "Outside ERP Scope")
		self.assertUserShowableTextIsProfessional(response)
		self.assertIn("inventory", response["answer_text"])
		self.assertIn("ERP report", response["next_steps"][1])

	def test_shadow_trace_default_is_not_user_showable(self):
		response = render_nbu_professional_response(
			{
				"shadow_mode": True,
				"conversation_action_decision": {
					"action": "observe_only",
					"response_mode": "shadow_trace_only",
				},
				"governed_requery_plan": {"status": "not_evaluated"},
			}
		)

		self.assertFalse(response["safe_to_show"])
		self.assertEqual(response["technical_details"]["response_mode"], "shadow_trace_only")


if __name__ == "__main__":
	unittest.main()
