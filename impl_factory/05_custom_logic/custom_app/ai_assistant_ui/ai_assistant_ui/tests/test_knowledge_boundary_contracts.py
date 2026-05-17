import sys
import types
import unittest


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.knowledge_boundary import (
	evaluate_knowledge_boundary,
	render_knowledge_boundary_answer,
)


class TestKnowledgeBoundaryContracts(unittest.TestCase):
	def test_frontdoor_reclassifies_to_artifact_lane_when_governed_artifact_is_confirmed(self):
		payload = evaluate_knowledge_boundary(
			request_id="boundary-frontdoor-artifact",
			session_id="phase7b",
			proposed_lane="front_door",
			front_door_contract={
				"handle_in_front_door": True,
				"route_target": "front_door",
				"confidence": 0.93,
			},
			governed_scope_contract={
				"governed_scope_status": "covered_family",
			},
			compiled_execution_audit={
				"runtime_ok": True,
				"family_validation_status": "pass",
				"semantic_validation_status": "pass",
			},
		)

		self.assertEqual(payload.get("final_lane"), "artifact_lane")
		self.assertEqual(payload.get("boundary_status"), "reclassified")
		self.assertEqual(payload.get("knowledge_coverage_state"), "covered_but_wrong_lane")
		self.assertEqual(payload.get("safe_next_action"), "route_to_artifact_lane")
		self.assertTrue(bool(payload.get("allowed_to_answer")))

	def test_clarification_preempts_artifact_lane_even_when_governed_artifact_is_available(self):
		payload = evaluate_knowledge_boundary(
			request_id="boundary-clarification-preempts-artifact",
			session_id="phase7b",
			proposed_lane="artifact_lane",
			clarification_resolution={
				"decision": "reask_pending_clarification",
			},
			governed_scope_contract={
				"governed_scope_status": "covered_family",
			},
			compiled_execution_audit={
				"runtime_ok": True,
				"family_validation_status": "pass",
				"semantic_validation_status": "pass",
			},
		)

		self.assertEqual(payload.get("final_lane"), "clarification")
		self.assertEqual(payload.get("boundary_status"), "reclassified")
		self.assertEqual(payload.get("safe_next_action"), "route_to_clarification")
		self.assertFalse(bool(payload.get("allowed_to_answer")))
		self.assertEqual(payload.get("knowledge_coverage_state"), "covered")

	def test_reasoning_lane_reclassifies_to_valid_erp_domain_uncovered_when_grounding_is_insufficient(self):
		payload = evaluate_knowledge_boundary(
			request_id="boundary-reasoning-uncovered",
			session_id="phase7b",
			proposed_lane="reasoning_lane",
			governed_scope_contract={
				"governed_scope_status": "out_of_scope_but_valid_erp_domain",
			},
			reasoning_activation_contract={
				"grounded_context_available": False,
			},
			reasoning_contract={
				"allowed_to_answer": False,
				"grounding_sufficient": False,
				"grounding_gaps": ["missing_governed_source"],
			},
		)

		self.assertEqual(payload.get("final_lane"), "valid_erp_domain_uncovered")
		self.assertEqual(payload.get("boundary_status"), "reclassified")
		self.assertEqual(payload.get("knowledge_coverage_state"), "valid_erp_domain_uncovered")
		self.assertEqual(payload.get("safe_next_action"), "respond_uncovered_erp_domain")
		self.assertFalse(bool(payload.get("allowed_to_answer")))
		self.assertIn("missing_governed_source", payload.get("boundary_flags") or [])

	def test_unsupported_non_erp_request_is_blocked_with_safe_refusal(self):
		payload = evaluate_knowledge_boundary(
			request_id="boundary-unsupported-non-erp",
			session_id="phase7b",
			proposed_lane="artifact_lane",
			governed_scope_contract={
				"governed_scope_status": "unsupported_request",
			},
		)

		self.assertEqual(payload.get("final_lane"), "unsupported_request")
		self.assertEqual(payload.get("boundary_status"), "blocked")
		self.assertEqual(payload.get("knowledge_coverage_state"), "unsupported_non_erp")
		self.assertEqual(payload.get("safe_next_action"), "respond_unsupported")
		self.assertFalse(bool(payload.get("allowed_to_answer")))

	def test_boundary_renderer_uses_lane_specific_message_for_artifact_reclassification(self):
		answer = render_knowledge_boundary_answer(
			boundary_contract={
				"user_response_mode": "boundary_explanation",
				"safe_next_action": "route_to_artifact_lane",
				"final_lane": "artifact_lane",
				"reclassification_reason": "Artifact lane owns the governed result.",
			}
		)

		self.assertTrue(
			answer.startswith("This turn belongs in the governed ERP artifact lane, not in the current lane."),
		)
		self.assertIn("Artifact lane owns the governed result.", answer)


if __name__ == "__main__":
	unittest.main()
