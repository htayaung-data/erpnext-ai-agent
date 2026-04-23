import sys
import types
import unittest
from unittest.mock import patch


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.compound_request_support import (
	assess_compound_request,
	build_post_result_multi_step_assessment_payload,
	build_multi_step_step_result_integration_payload,
)


class TestCompoundRequestSupport(unittest.TestCase):
	def test_assess_compound_request_detects_two_supported_segments(self):
		with patch(
			"ai_assistant_ui.qwen_chat.compound_request_support._supported_segment_interpretation",
			side_effect=[
				{
					"status": "accepted",
					"source": "deterministic_surface",
					"interpretation": object(),
				},
				{
					"status": "accepted",
					"source": "deterministic_surface",
					"interpretation": object(),
				},
			],
		):
			result = assess_compound_request(
				request_id="compound-1",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="show me payment entries then give me some supplier list",
			)
		self.assertTrue(result)
		assessment = result.get("assessment_contract")
		signal = result.get("clarification_signal")
		self.assertEqual(assessment.status, "ordered_execution_ready")
		self.assertFalse(assessment.clarification_required)
		self.assertEqual(assessment.segments, ["show me payment entries", "give me some supplier list"])
		self.assertIsNone(signal)
		self.assertEqual(
			assessment.internal_details.get("resolved_message_by_option", {}).get("Supplier list"),
			"give me some supplier list",
		)
		self.assertEqual(
			assessment.internal_details.get("primary_segment_payload", {}).get("segment_message"),
			"show me payment entries",
		)
		self.assertEqual(
			assessment.internal_details.get("remaining_segment_payloads", [{}])[0].get("segment_label"),
			"Supplier list",
		)
		multi_step_assessment = assessment.internal_details.get("multi_step_assessment", {})
		self.assertEqual(multi_step_assessment.get("assessment_kind"), "multi_step")
		self.assertEqual(multi_step_assessment.get("relationship_type"), "independent_ordered")
		self.assertEqual(multi_step_assessment.get("step_count"), 2)
		self.assertEqual(multi_step_assessment.get("current_step_id"), "step_1")
		self.assertEqual(multi_step_assessment.get("remaining_step_ids"), ["step_2"])
		self.assertEqual(
			((multi_step_assessment.get("steps") or [{}])[1]).get("step_label"),
			"Supplier list",
		)
		multi_step_execution_plan = assessment.internal_details.get("multi_step_execution_plan", {})
		self.assertEqual(multi_step_execution_plan.get("type"), "qwen_multi_step_execution_plan_contract")
		self.assertEqual(multi_step_execution_plan.get("relationship_type"), "independent_ordered")
		self.assertEqual(multi_step_execution_plan.get("entry_step_id"), "step_1")
		self.assertEqual(
			((multi_step_execution_plan.get("steps") or [{}])[0]).get("dependency_step_ids"),
			[],
		)
		self.assertEqual(
			(multi_step_execution_plan.get("interruption_policy") or {}).get("policy_id"),
			"single_active_plan_latest_request_wins",
		)
		multi_step_execution_state = assessment.internal_details.get("multi_step_execution_state", {})
		self.assertEqual(multi_step_execution_state.get("type"), "qwen_multi_step_execution_state_contract")
		self.assertEqual(multi_step_execution_state.get("state"), "ready")
		self.assertEqual(multi_step_execution_state.get("current_step_id"), "step_1")
		self.assertEqual(multi_step_execution_state.get("remaining_step_ids"), ["step_2"])

	def test_assess_compound_request_fails_closed_when_one_segment_is_not_supported(self):
		with patch(
			"ai_assistant_ui.qwen_chat.compound_request_support._supported_segment_interpretation",
			side_effect=[
				{
					"status": "accepted",
					"source": "deterministic_surface",
					"interpretation": object(),
				},
				{},
			],
		):
			result = assess_compound_request(
				request_id="compound-2",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="show me payment entries then supplier details",
			)
		self.assertEqual(result, {})

	def test_build_multi_step_step_result_integration_payload_promotes_grounded_result(self):
		with patch(
			"ai_assistant_ui.qwen_chat.compound_request_support._supported_segment_interpretation",
			side_effect=[
				{
					"status": "accepted",
					"source": "deterministic_surface",
					"interpretation": object(),
				},
				{
					"status": "accepted",
					"source": "deterministic_surface",
					"interpretation": object(),
				},
			],
		):
			result = assess_compound_request(
				request_id="compound-3",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="show me payment entries then give me some supplier list",
			)
		assessment = result.get("assessment_contract")
		integration_payload = build_multi_step_step_result_integration_payload(
			request_id="compound-3",
			compound_assessment_payload=assessment.to_payload(),
			grounded_turn_payload={
				"type": "qwen_grounded_turn_context",
				"request_id": "compound-3",
				"trace_request_id": "compound-3-trace",
				"grounded": True,
				"artifact_family_id": "transaction_listing",
				"source_name": "Payment Entry List",
			},
			normalized_family_artifact={
				"type": "qwen_normalized_family_artifact_contract",
				"artifact_type": "normalized_family_artifact",
				"family_id": "transaction_listing",
			},
			family_validation_payload={"status": "pass"},
			semantic_validation_payload={"status": "pass"},
		)
		self.assertEqual(
			integration_payload.get("type"),
			"qwen_multi_step_step_result_integration_contract",
		)
		self.assertEqual(integration_payload.get("source_step_id"), "step_1")
		self.assertTrue(bool(integration_payload.get("update_recent_focus")))
		self.assertEqual(
			(integration_payload.get("result_handle") or {}).get("artifact_family_id"),
			"transaction_listing",
		)

	def test_build_post_result_multi_step_assessment_payload_advances_after_grounded_result(self):
		with patch(
			"ai_assistant_ui.qwen_chat.compound_request_support._supported_segment_interpretation",
			side_effect=[
				{
					"status": "accepted",
					"source": "deterministic_surface",
					"interpretation": object(),
				},
				{
					"status": "accepted",
					"source": "deterministic_surface",
					"interpretation": object(),
				},
			],
		):
			result = assess_compound_request(
				request_id="compound-4",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="show me payment entries then give me some supplier list",
			)
		assessment = result.get("assessment_contract")
		integration_payload = build_multi_step_step_result_integration_payload(
			request_id="compound-4",
			compound_assessment_payload=assessment.to_payload(),
			grounded_turn_payload={
				"type": "qwen_grounded_turn_context",
				"request_id": "compound-4",
				"trace_request_id": "compound-4-trace",
				"grounded": True,
				"artifact_family_id": "transaction_listing",
				"source_name": "Payment Entry List",
			},
			normalized_family_artifact={
				"type": "qwen_normalized_family_artifact_contract",
				"artifact_type": "normalized_family_artifact",
				"family_id": "transaction_listing",
			},
			family_validation_payload={"status": "pass"},
			semantic_validation_payload={"status": "pass"},
		)
		updated_payload = build_post_result_multi_step_assessment_payload(
			compound_assessment_payload=assessment.to_payload(),
			step_result_integration_payload=integration_payload,
		)
		self.assertEqual(updated_payload.get("status"), "ordered_execution_ready")
		self.assertFalse(bool(updated_payload.get("clarification_required")))
		multi_step_assessment = (updated_payload.get("internal_details") or {}).get("multi_step_assessment") or {}
		self.assertEqual(multi_step_assessment.get("current_step_id"), "step_2")
		self.assertEqual(multi_step_assessment.get("completed_step_ids"), ["step_1"])
		multi_step_execution_state = (updated_payload.get("internal_details") or {}).get("multi_step_execution_state") or {}
		self.assertEqual(multi_step_execution_state.get("state"), "ready")
		self.assertEqual(multi_step_execution_state.get("current_step_id"), "step_2")
		self.assertEqual(multi_step_execution_state.get("last_completed_step_id"), "step_1")

	def test_build_post_result_multi_step_assessment_payload_holds_current_step_on_clarification(self):
		with patch(
			"ai_assistant_ui.qwen_chat.compound_request_support._supported_segment_interpretation",
			side_effect=[
				{
					"status": "accepted",
					"source": "deterministic_surface",
					"interpretation": object(),
				},
				{
					"status": "accepted",
					"source": "deterministic_surface",
					"interpretation": object(),
				},
			],
		):
			result = assess_compound_request(
				request_id="compound-5",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="show me payment entries then give me some supplier list",
			)
		assessment = result.get("assessment_contract")
		integration_payload = build_multi_step_step_result_integration_payload(
			request_id="compound-5",
			compound_assessment_payload=assessment.to_payload(),
			clarification_signal_payload={
				"type": "qwen_clarification_signal_contract",
				"request_id": "compound-5",
			},
		)
		updated_payload = build_post_result_multi_step_assessment_payload(
			compound_assessment_payload=assessment.to_payload(),
			step_result_integration_payload=integration_payload,
		)
		self.assertEqual(updated_payload.get("status"), "ordered_execution_waiting_for_clarification")
		self.assertTrue(bool(updated_payload.get("clarification_required")))
		multi_step_assessment = (updated_payload.get("internal_details") or {}).get("multi_step_assessment") or {}
		self.assertEqual(multi_step_assessment.get("current_step_id"), "step_1")
		self.assertEqual(multi_step_assessment.get("remaining_step_ids"), ["step_2"])
		self.assertEqual(multi_step_assessment.get("completed_step_ids"), [])
		multi_step_execution_state = (updated_payload.get("internal_details") or {}).get("multi_step_execution_state") or {}
		self.assertEqual(multi_step_execution_state.get("state"), "waiting_for_clarification")
		self.assertEqual(multi_step_execution_state.get("current_step_id"), "step_1")
		self.assertEqual(multi_step_execution_state.get("waiting_step_id"), "step_1")


if __name__ == "__main__":
	unittest.main()
