from __future__ import annotations

import sys
import types
import unittest

fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.db = types.SimpleNamespace(exists=lambda *args, **kwargs: False)
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.lanes.runtime_gate_lane import handle_runtime_gate_turn


class SemanticFinancialRuntimeGateAuthorityTests(unittest.TestCase):
	def test_runtime_gate_honors_governed_uncovered_scope_without_new_query_mode(self):
		appended_messages = []
		appended_tools = []

		def _append_message(_session_doc, role, content):
			appended_messages.append((role, content))

		def _append_tool_payload(_session_doc, payload):
			appended_tools.append(payload)

		ok, payload, compiled_fallback = handle_runtime_gate_turn(
			session_doc=object(),
			request_id="runtime-gate-1",
			session_id="session-1",
			user_id="Administrator",
			site_name="erpai_prj1",
			message="show employee headcount by department",
			raw_message="show employee headcount by department",
			latest_grounded_turn_available=True,
			latest_grounded_turn={"grounded": True, "source_name": "Sales Analytics"},
			followup_resolution=types.SimpleNamespace(mode="grounded_follow_up", target_limit=0),
			execution_path=types.SimpleNamespace(path="artifact_lane"),
			interaction_contract=types.SimpleNamespace(
				request_id="runtime-gate-1",
				session_id="session-1",
			),
			frontdoor_contract=types.SimpleNamespace(to_payload=lambda: {}),
			clarification_response_contract=None,
			scope_decision_contract=types.SimpleNamespace(
				governed_scope_status="out_of_scope_but_valid_erp_domain",
				requested_domains=["employee"],
				context_domains=["sales"],
				primary_domain="hr",
				reason="HR is a valid ERP domain but not covered.",
				out_of_scope=True,
			),
			compiled_rollout={"enabled": False},
			append_tool_payload=_append_tool_payload,
			append_message=_append_message,
			append_knowledge_boundary_contract=lambda *_args, **_kwargs: self.fail(
				"runtime gate should stage boundary payloads through the authorized helper"
			),
			append_knowledge_boundary_observability=lambda *_args, **_kwargs: None,
			append_compiled_attempt_artifacts=lambda *_args, **_kwargs: None,
			compiled_rollout_fallback_eligible=lambda *_args, **_kwargs: False,
			compiled_rollout_fallback_reason=lambda *_args, **_kwargs: "",
			compiled_rollout_fallback_payload=lambda **_kwargs: {},
			handle_compiled_first_turn_result=lambda **_kwargs: (True, {}),
			out_of_scope_answer=lambda _message, _decision: "I don't have governed HR or headcount coverage yet.",
			assistant_text_payload=lambda text: text,
			save_session=lambda *_args, **_kwargs: None,
		)

		self.assertTrue(ok)
		self.assertEqual(payload["mode"], "known_unsupported_erp_domain")
		self.assertIsNone(compiled_fallback)
		boundary_payload = next(payload for payload in appended_tools if payload.get("type") == "qwen_knowledge_boundary_contract")
		self.assertEqual(boundary_payload["knowledge_coverage_state"], "valid_erp_domain_uncovered")
		self.assertEqual(boundary_payload["final_lane"], "valid_erp_domain_uncovered")
		self.assertEqual(payload["agent_meta"]["authorized_emission"]["preflight_status"], "bounded")
		self.assertIn("headcount coverage", appended_messages[-1][1])


if __name__ == "__main__":
	unittest.main()
