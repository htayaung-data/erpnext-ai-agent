import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_runtime import (
	build_nbu_shadow_interpretation_context,
	interpret_natural_business_understanding_shadow,
)


class NaturalBusinessUnderstandingRuntimeTests(unittest.TestCase):
	def test_shadow_context_carries_allowed_values_and_metadata(self):
		context = build_nbu_shadow_interpretation_context(
			raw_message="forget the first question, answer the last question",
			current_artifact={
				"artifact_id": "artifact-1",
				"family_id": "customer_risk_as_of",
				"title": "Customer Risk As-Of",
				"rows": [{"customer": "Hidden noise"}],
			},
			metadata_context={
				"capability_ids": ["accounts_receivable_aging_read"],
				"report_names": ["Accounts Receivable Summary"],
				"composite_family_ids": ["customer_risk_as_of"],
				"business_domains": ["customer_risk"],
				"reports": [
					{
						"report_name": "Accounts Receivable Summary",
						"supported_metrics": ["Outstanding Amount"],
						"supported_dimensions": ["Customer"],
						"internal_notes": "must not leak",
					}
				],
				"composite_families": [
					{
						"family_id": "customer_risk_as_of",
						"entity_grain": "customer",
						"allowed_primary_metrics": ["overdue_amount"],
						"activation_state": "active",
					}
				],
			},
		)

		self.assertTrue(context["shadow_mode"])
		self.assertIn("fresh_query", context["allowed_values"]["intent_scopes"])
		self.assertEqual(context["current_artifact"]["family_id"], "customer_risk_as_of")
		self.assertNotIn("rows", context["current_artifact"])
		self.assertEqual(context["metadata_context"]["composite_family_ids"], ["customer_risk_as_of"])
		self.assertEqual(context["metadata_context"]["reports"][0]["report_name"], "Accounts Receivable Summary")
		self.assertNotIn("internal_notes", context["metadata_context"]["reports"][0])
		self.assertEqual(context["metadata_context"]["composite_families"][0]["family_id"], "customer_risk_as_of")
		self.assertEqual(context["conversation_control_evidence"]["action_id"], "reopen_pending_clarification")
		self.assertTrue(
			context["conversation_control_evidence"]["internal_details"]["discard_prefix_applied"]
		)

	def test_shadow_runtime_normalizes_model_candidates_without_execution(self):
		captured = {}

		def fake_runtime_call(**kwargs):
			captured.update(kwargs)
			return {
				"ok": True,
				"interpretation": {
					"detected_language": "en",
					"candidate_interpretations": [
						{
							"candidate_id": "candidate-1",
							"intent_scope": "context_reference",
							"business_domain": "customer_risk",
							"requested_action": "explain",
							"target_reference": "rank_n",
							"candidate_route": "local_followup",
							"candidate_composite_family_ids": ["customer_risk_as_of"],
							"requested_metrics": ["overdue_amount"],
							"evidence_need": "current_artifact_ok",
							"authority_class": "safe_explanation",
							"model_confidence": 1.4,
							"model_reason": "The user asks why rank 1 is risky.",
						}
					],
				},
			}

		trace = interpret_natural_business_understanding_shadow(
			request_id="req-1",
			session_id="session-1",
			user_id="user-1",
			site_name="site-1",
			message="why is the first customer risky?",
			current_artifact={
				"artifact_id": "risk-artifact-1",
				"family_id": "customer_risk_as_of",
				"columns": ["customer", "overdue_amount"],
				"sections": {
					"ranked_rows": [
						{
							"rank": 1,
							"customer": "35th Street Mobile Wholesale",
							"overdue_amount": 60212000,
						}
					]
				},
			},
			metadata_context={
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
			runtime_call=fake_runtime_call,
		)

		self.assertEqual(captured["interpretation_context"]["contract_version"], "1.0")
		self.assertEqual(trace["conversation_action_decision"]["action"], "answer_from_current_artifact")
		self.assertTrue(trace["conversation_action_decision"]["safe_to_execute"])
		self.assertTrue(trace["conversation_action_decision"]["technical_details"]["shadow_mode"])
		self.assertFalse(trace["conversation_action_decision"]["technical_details"]["runtime_execution_enabled"])
		self.assertTrue(trace["conversation_action_decision"]["technical_details"]["execution_not_performed"])
		self.assertEqual(trace["selected_candidate_id"], "candidate-1")
		self.assertEqual(trace["candidate_interpretations"][0]["model_confidence"], 1.0)
		self.assertEqual(trace["candidate_interpretations"][0]["target_reference"], "rank_n")
		self.assertEqual(trace["authority_plan"]["authority_class"], "safe_explanation")
		self.assertEqual(trace["context_resolution"]["status"], "resolved")
		self.assertEqual(trace["context_resolution"]["resolved_entity"]["entity_label"], "35th Street Mobile Wholesale")
		self.assertEqual(trace["context_resolution"]["resolved_rank"], 1)
		self.assertEqual(trace["governed_requery_plan"]["status"], "not_required")
		self.assertIn("professional_response", trace)
		self.assertFalse(trace["professional_response"]["safe_to_show"])
		self.assertIn("schema_hardening_assessment", trace)
		self.assertTrue(trace["schema_hardening_assessment"]["ok"])
		self.assertIn("activation_assessment", trace)
		self.assertFalse(trace["activation_assessment"]["eligible_for_controlled_activation"])
		self.assertIn("delegated_to_existing_artifact_renderer", trace["activation_assessment"]["blockers"])

	def test_shadow_runtime_policy_boundary_decision_is_recorded_not_executed(self):
		def fake_runtime_call(**kwargs):
			return {
				"ok": True,
				"interpretation": {
					"candidate_interpretations": [
						{
							"candidate_id": "candidate-policy",
							"intent_scope": "followup",
							"business_domain": "customer_risk",
							"requested_action": "predict",
							"target_reference": "rank_n",
							"candidate_composite_family_ids": ["customer_risk_as_of"],
							"evidence_need": "needs_governed_requery",
							"authority_class": "prediction",
							"model_confidence": 0.95,
						}
					],
				},
			}

		trace = interpret_natural_business_understanding_shadow(
			request_id="req-policy",
			session_id="session-policy",
			message="will the first customer default next month?",
			current_artifact={"family_id": "customer_risk_as_of"},
			metadata_context={
				"composite_family_ids": ["customer_risk_as_of"],
				"business_domains": ["customer_risk"],
			},
			runtime_call=fake_runtime_call,
		)

		self.assertEqual(trace["conversation_action_decision"]["action"], "reject_with_boundary")
		self.assertEqual(trace["conversation_action_decision"]["response_mode"], "boundary")
		self.assertEqual(trace["authority_plan"]["policy_artifact_required"], "approved_policy_artifact_required")
		self.assertTrue(trace["conversation_action_decision"]["technical_details"]["shadow_mode"])
		self.assertFalse(trace["conversation_action_decision"]["technical_details"]["runtime_execution_enabled"])
		self.assertEqual(trace["governed_requery_plan"]["status"], "blocked_by_authority_policy")
		self.assertEqual(trace["professional_response"]["title"], "Decision Not Available Yet")
		self.assertIn("ERP facts", trace["professional_response"]["answer_text"])
		self.assertIn("schema_hardening_assessment", trace)
		self.assertTrue(trace["schema_hardening_assessment"]["ok"])
		self.assertTrue(trace["activation_assessment"]["eligible_for_controlled_activation"])
		self.assertEqual(trace["activation_assessment"]["activation_mode"], "presentation_only")

	def test_shadow_runtime_records_existing_conversation_control_evidence(self):
		def fake_runtime_call(**kwargs):
			return {
				"ok": True,
				"interpretation": {
					"candidate_interpretations": [
						{
							"candidate_id": "candidate-restore",
							"intent_scope": "context_reference",
							"business_domain": "customer",
							"requested_action": "restore",
							"target_reference": "previous_artifact",
							"candidate_route": "recovery",
							"evidence_need": "needs_clarification",
							"authority_class": "safe_read",
							"model_confidence": 0.8,
						}
					],
				},
			}

		trace = interpret_natural_business_understanding_shadow(
			request_id="req-control",
			session_id="session-control",
			message="go back to the customer",
			recent_focus={
				"focus_kind": "entity",
				"focus_grain": "customer",
				"focus_label": "Ko Nay Lin Mobile Center",
				"focus_key": "Ko Nay Lin Mobile Center",
				"source_request_id": "customer-detail-1",
			},
			runtime_call=fake_runtime_call,
		)

		control = trace["conversation_action_decision"]["technical_details"]["conversation_control_evidence"]
		self.assertEqual(control["action_id"], "replay_or_restore_prior_branch")
		self.assertEqual(control["internal_details"]["target_grain"], "customer")
		self.assertEqual(control["internal_details"]["target_focus_kind"], "entity")
		self.assertEqual(trace["context_resolution"]["status"], "resolved")
		self.assertEqual(trace["context_resolution"]["resolved_artifact_id"], "customer-detail-1")
		self.assertEqual(trace["context_resolution"]["resolved_entity"]["entity_label"], "Ko Nay Lin Mobile Center")
		self.assertTrue(trace["conversation_action_decision"]["technical_details"]["execution_not_performed"])

	def test_shadow_runtime_records_governed_requery_plan_without_execution(self):
		def fake_runtime_call(**kwargs):
			return {
				"ok": True,
				"interpretation": {
					"candidate_interpretations": [
						{
							"candidate_id": "candidate-requery",
							"intent_scope": "followup",
							"business_domain": "customer_credit",
							"requested_action": "detail",
							"target_reference": "named_entity",
							"target_entity": {
								"entity_type": "customer",
								"entity_key": "Ko Nay Lin Mobile Center",
								"entity_label": "Ko Nay Lin Mobile Center",
							},
							"candidate_route": "entity_detail",
							"candidate_capability_ids": ["accounts_receivable_read"],
							"candidate_report_names": ["Customer Credit Detail"],
							"requested_metrics": ["credit_limit"],
							"requested_dimensions": ["customer"],
							"evidence_need": "needs_governed_requery",
							"authority_class": "governed_requery",
							"model_confidence": 0.92,
						}
					],
				},
			}

		trace = interpret_natural_business_understanding_shadow(
			request_id="req-requery",
			session_id="session-requery",
			message="do you know the credit limit of that customer?",
			metadata_context={
				"capability_ids": ["accounts_receivable_read"],
				"report_names": ["Customer Credit Detail"],
				"business_domains": ["customer_credit"],
				"reports": [
					{
						"report_name": "Customer Credit Detail",
						"capability_ids": ["accounts_receivable_read"],
						"supported_metrics": ["credit_limit", "outstanding_amount"],
						"supported_dimensions": ["customer"],
						"activation_state": "active",
					}
				],
			},
			runtime_call=fake_runtime_call,
		)

		self.assertEqual(trace["conversation_action_decision"]["action"], "execute_governed_requery")
		self.assertTrue(trace["conversation_action_decision"]["technical_details"]["execution_not_performed"])
		self.assertEqual(trace["context_resolution"]["status"], "resolved")
		self.assertEqual(trace["governed_requery_plan"]["status"], "ready_shadow")
		self.assertEqual(trace["governed_requery_plan"]["planner_mode"], "entity_detail_requery")
		self.assertEqual(trace["governed_requery_plan"]["target_report_names"], ["Customer Credit Detail"])
		self.assertFalse(trace["conversation_action_decision"]["technical_details"]["runtime_execution_enabled"])
		self.assertEqual(trace["professional_response"]["title"], "ERP Source Available")
		self.assertIn("Customer Credit Detail", trace["professional_response"]["answer_text"])
		self.assertFalse(trace["activation_assessment"]["eligible_for_controlled_activation"])
		self.assertIn("requires_execution_lane_activation", trace["activation_assessment"]["blockers"])

	def test_shadow_runtime_preserves_future_business_domain_but_unknowns_invalid_enums(self):
		def fake_runtime_call(**kwargs):
			return {
				"ok": True,
				"candidate_interpretations": [
					{
						"candidate_id": "candidate-hr",
						"intent_scope": "fresh_query",
						"business_domain": "hr_attendance",
						"requested_action": "show",
						"target_reference": "mystery_pointer",
						"candidate_route": "unknown_future_route",
						"candidate_capability_ids": ["attendance_read"],
						"evidence_need": "needs_governed_requery",
						"authority_class": "safe_read",
						"model_confidence": 0.72,
					}
				],
			}

		trace = interpret_natural_business_understanding_shadow(
			request_id="req-2",
			session_id="session-2",
			message="show attendance risk",
			runtime_call=fake_runtime_call,
		)

		candidate = trace["candidate_interpretations"][0]
		self.assertEqual(candidate["business_domain"], "hr_attendance")
		self.assertEqual(candidate["candidate_capability_ids"], ["attendance_read"])
		self.assertEqual(candidate["target_reference"], "unknown")
		self.assertEqual(candidate["candidate_route"], "unknown")

	def test_shadow_runtime_failure_is_safe_observe_only_trace(self):
		def fake_runtime_call(**kwargs):
			raise RuntimeError("runtime offline")

		trace = interpret_natural_business_understanding_shadow(
			request_id="req-3",
			session_id="session-3",
			message="anything natural",
			runtime_call=fake_runtime_call,
		)

		self.assertTrue(trace["shadow_mode"])
		self.assertEqual(trace["validation_result"]["status"], "runtime_unavailable")
		self.assertEqual(trace["conversation_action_decision"]["action"], "observe_only")
		self.assertFalse(trace["conversation_action_decision"]["requires_routing_change"])
		self.assertIn("runtime offline", trace["validation_result"]["validation_errors"][0])

	def test_shadow_runtime_empty_candidates_warns_without_behavior_change(self):
		def fake_runtime_call(**kwargs):
			return {"ok": True, "interpretation": {"candidate_interpretations": []}}

		trace = interpret_natural_business_understanding_shadow(
			request_id="req-4",
			session_id="session-4",
			message="unclear business question",
			runtime_call=fake_runtime_call,
		)

		self.assertEqual(trace["validation_result"]["status"], "shadow_no_candidates")
		self.assertIn("no_candidate_interpretations", trace["validation_result"]["validation_warnings"])
		self.assertEqual(trace["conversation_action_decision"]["response_mode"], "shadow_trace_only")
		self.assertFalse(trace["conversation_action_decision"]["safe_to_execute"])
		self.assertIn("professional_response", trace)
		self.assertFalse(trace["professional_response"]["safe_to_show"])
		self.assertIn("schema_hardening_assessment", trace)
		self.assertTrue(trace["schema_hardening_assessment"]["ok"])
		self.assertIn("activation_assessment", trace)
		self.assertIn("runtime_interpretation_not_ready", trace["activation_assessment"]["blockers"])


if __name__ == "__main__":
	unittest.main()
