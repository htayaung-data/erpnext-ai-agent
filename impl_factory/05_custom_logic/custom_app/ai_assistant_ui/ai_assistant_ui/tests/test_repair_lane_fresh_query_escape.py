import sys
import types
import unittest

fake_frappe = types.ModuleType("frappe")
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.lanes.repair_lane import handle_repair_turn


class RepairLaneFreshQueryEscapeTests(unittest.TestCase):
	def test_self_contained_governed_query_bypasses_recovery_repair_lane(self):
		def fail_callback(*args, **kwargs):
			raise AssertionError("Repair lane should not execute callbacks for a fresh governed query.")

		handled, payload = handle_repair_turn(
			session_doc=types.SimpleNamespace(title=""),
			request_id="req-fresh-query-escape",
			session_id="session-1",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="Top 7 Products by Revenue Last Year",
			raw_message="Top 7 Products by Revenue Last Year",
			recent_messages=[],
			latest_recovery_contract={
				"source_report": "Profit and Loss Statement",
				"recommended_recovery_action": "clarify_target_output",
			},
			latest_grounded_turn={
				"grounded": True,
				"source_name": "Profit and Loss Statement",
				"artifact_family_id": "financial_statement",
			},
			latest_assistant_payload={},
			interaction_contract=None,
			frontdoor_semantic_result=None,
			frontdoor_contract=None,
			clarification_response_contract=None,
			response_policy_contract=None,
			append_message=fail_callback,
			append_tool_payload=fail_callback,
			build_recovery_guidance_answer=fail_callback,
			handle_recovery_guidance_response=fail_callback,
			build_recovery_governed_query_message=fail_callback,
			handle_compiled_first_turn_result=fail_callback,
		)
		self.assertFalse(handled)
		self.assertIsNone(payload)


if __name__ == "__main__":
	unittest.main()
