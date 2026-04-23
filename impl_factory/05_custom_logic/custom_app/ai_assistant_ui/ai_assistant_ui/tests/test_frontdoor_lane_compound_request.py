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

from ai_assistant_ui.qwen_chat.contracts import (
	build_compound_request_assessment_contract,
)
from ai_assistant_ui.qwen_chat.compound_request_support import (
	compound_request_internal_details_with_multi_step_bridge,
)
from ai_assistant_ui.qwen_chat.lanes.frontdoor_lane import evaluate_frontdoor_lane


class TestFrontdoorLaneCompoundRequest(unittest.TestCase):
	def test_evaluate_frontdoor_lane_builds_ordered_execution_plan_for_compound_request(self):
		assessment = build_compound_request_assessment_contract(
			request_id="compound-frontdoor",
			status="ordered_execution_ready",
			segments=["show me payment entries", "give me some supplier list"],
			suggested_options=["Payment entries", "Supplier list"],
			clarification_required=False,
			reason="Two self-contained ERP requests were detected in a stated sequence.",
			internal_details=compound_request_internal_details_with_multi_step_bridge(
				request_id="compound-frontdoor",
				status="ordered_execution_ready",
				segments=["show me payment entries", "give me some supplier list"],
				suggested_options=["Payment entries", "Supplier list"],
				internal_details={
				"continuation_lane": "front_door",
				"execution_strategy": "ordered_multi_step",
				"primary_segment_message": "show me payment entries",
				"primary_segment_label": "Payment entries",
				"primary_segment_payload": {
					"segment_message": "show me payment entries",
					"segment_label": "Payment entries",
					"interpretation_source": "deterministic_surface",
				},
				"remaining_segment_messages": ["give me some supplier list"],
				"remaining_segment_labels": ["Supplier list"],
				"remaining_segment_payloads": [
					{
						"segment_message": "give me some supplier list",
						"segment_label": "Supplier list",
						"interpretation_source": "deterministic_surface",
					}
				],
				"segment_execution_payloads": [
					{
						"segment_message": "show me payment entries",
						"segment_label": "Payment entries",
						"interpretation_source": "deterministic_surface",
					},
					{
						"segment_message": "give me some supplier list",
						"segment_label": "Supplier list",
						"interpretation_source": "deterministic_surface",
					},
				],
				"resolved_message_by_option": {
					"Payment entries": "show me payment entries",
					"Supplier list": "give me some supplier list",
				},
			},
			),
		)
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.frontdoor_lane.assess_compound_request",
			return_value={
				"assessment_contract": assessment,
				"clarification_signal": None,
				"user_question": "",
				"reason": assessment.reason,
			},
		), patch(
			"ai_assistant_ui.qwen_chat.lanes.frontdoor_lane.render_front_door_answer",
		) as render_mock:
			semantic_result, frontdoor_contract, frontdoor_render_result, frontdoor_answer = evaluate_frontdoor_lane(
				request_id="compound-frontdoor",
				session_id="session-a",
				user_id="Administrator",
				site_name="erp.test",
				message="show me payment entries then give me some supplier list",
				recent_messages=[],
				grounded_context_available=False,
				latest_grounded_turn=None,
				latest_recovery_contract_available=False,
				pre_frontdoor_reasoning_semantic_result=None,
			)
		self.assertEqual(semantic_result.intent.intent_class, "route_onward")
		self.assertEqual(frontdoor_contract.intent_class, "route_onward")
		self.assertEqual(frontdoor_contract.response_mode, "route_onward")
		self.assertEqual(frontdoor_answer, "")
		self.assertIsNone(frontdoor_render_result)
		payload = frontdoor_contract.response_payload.get("compound_request_assessment", {})
		self.assertEqual(payload.get("status"), "ordered_execution_ready")
		self.assertEqual(
			(payload.get("internal_details") or {}).get("primary_segment_message"),
			"show me payment entries",
		)
		self.assertEqual(
			(payload.get("internal_details") or {}).get("remaining_segment_messages"),
			["give me some supplier list"],
		)
		self.assertEqual(
			((payload.get("internal_details") or {}).get("primary_segment_payload") or {}).get("segment_label"),
			"Payment entries",
		)
		self.assertEqual(
			((((payload.get("internal_details") or {}).get("remaining_segment_payloads") or [{}])[0]).get("segment_message")),
			"give me some supplier list",
		)
		self.assertEqual(
			(((payload.get("internal_details") or {}).get("multi_step_assessment") or {}).get("current_step_id")),
			"step_1",
		)
		multi_step_execution_plan = ((payload.get("internal_details") or {}).get("multi_step_execution_plan") or {})
		self.assertEqual(multi_step_execution_plan.get("type"), "qwen_multi_step_execution_plan_contract")
		self.assertEqual(multi_step_execution_plan.get("entry_step_id"), "step_1")
		multi_step_execution_state = ((payload.get("internal_details") or {}).get("multi_step_execution_state") or {})
		self.assertEqual(multi_step_execution_state.get("type"), "qwen_multi_step_execution_state_contract")
		self.assertEqual(multi_step_execution_state.get("state"), "ready")
		self.assertEqual(multi_step_execution_state.get("current_step_index"), 1)
		render_mock.assert_not_called()


if __name__ == "__main__":
	unittest.main()
