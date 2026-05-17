import sys
import types
import unittest
from unittest.mock import patch

fake_frappe = types.ModuleType("frappe")
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.contracts import InteractionContract
from ai_assistant_ui.qwen_chat.lanes import compiled_query_lane


class _PayloadStub:
	def __init__(self, payload):
		self._payload = dict(payload)

	def to_payload(self):
		return dict(self._payload)


class _SessionStub:
	title = "New Qwen Chat"


def _interaction_contract(message="show me customer credit exposure"):
	return InteractionContract(
		request_id="req-1",
		session_id="session-1",
		user_id="user-1",
		site_name="site-1",
		raw_message=message,
		detected_language="en",
	)


class TestCompiledQueryLaneScope(unittest.TestCase):
	def _run_lane(self, *, latest_grounded_turn_available):
		captured = {}
		appended_payloads = []

		def _handle_result(**kwargs):
			captured.update(kwargs)
			return True, {"ok": True}

		with patch.object(
			compiled_query_lane,
			"execute_compiled_fresh_query_message",
			return_value={"runtime_payload": {"ok": True}},
		):
			handled, payload = compiled_query_lane.handle_compiled_query_turn(
				session_doc=_SessionStub(),
				request_id="req-1",
				session_id="session-1",
				user_id="user-1",
				site_name="site-1",
				message="show me customer credit exposure",
				raw_message="show me customer credit exposure",
				interaction_contract=_interaction_contract(),
				frontdoor_semantic_result=_PayloadStub({"type": "qwen_frontdoor_semantic_result"}),
				frontdoor_contract=_PayloadStub({"type": "qwen_frontdoor_decision_contract"}),
				clarification_response_contract=None,
				append_message=lambda *args, **kwargs: None,
				append_tool_payload=lambda _session, payload: appended_payloads.append(payload),
				handle_compiled_first_turn_result=_handle_result,
				latest_grounded_turn_available=latest_grounded_turn_available,
			)

		self.assertTrue(handled)
		self.assertEqual(payload, {"ok": True})
		return captured, appended_payloads

	def test_existing_context_fresh_query_breakout_records_scope_status(self):
		captured, appended_payloads = self._run_lane(latest_grounded_turn_available=True)

		scope_contract = captured["governed_scope_contract"]
		self.assertEqual(scope_contract.governed_scope_status, "fresh_query_breakout")
		self.assertEqual(scope_contract.execution_mode, "fresh_query")
		self.assertTrue(scope_contract.latest_grounded_turn_available)
		self.assertIn(
			"fresh_query_breakout",
			[
				payload.get("governed_scope_status")
				for payload in appended_payloads
				if isinstance(payload, dict)
			],
		)

	def test_first_turn_fresh_query_remains_covered_family(self):
		captured, _appended_payloads = self._run_lane(latest_grounded_turn_available=False)

		scope_contract = captured["governed_scope_contract"]
		self.assertEqual(scope_contract.governed_scope_status, "covered_family")
		self.assertEqual(scope_contract.execution_mode, "fresh_query")
		self.assertFalse(scope_contract.latest_grounded_turn_available)


if __name__ == "__main__":
	unittest.main()
