import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.authorized_emission import (
	ANSWER_TYPE_CONTROL,
	ANSWER_TYPE_TRACE,
	AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE,
)
from ai_assistant_ui.qwen_chat.clarification_state import build_pending_clarification_state
from ai_assistant_ui.qwen_chat.lanes import clarification_lane
from ai_assistant_ui.qwen_chat.natural_business_understanding_service_activation import (
	try_activate_nbu_presentation_response,
)
from ai_assistant_ui.qwen_chat.recovery_guidance_support import handle_recovery_guidance_response
from ai_assistant_ui.qwen_chat.visible_context_trace_inspection import (
	INSPECTION_PAYLOAD_TYPE,
	try_activate_visible_context_trace_inspection_response,
)


class _Session:
	def __init__(self) -> None:
		self.name = "TEST-SESSION"
		self.title = "New Qwen Chat"
		self.messages = []
		self.pending_clarification_state_json = ""


class _PayloadObject:
	def __init__(self, payload=None, **attrs):
		self._payload = dict(payload or {})
		for key, value in attrs.items():
			setattr(self, key, value)

	def to_payload(self):
		return dict(self._payload)


def _append_message(session, role, content):
	session.messages.append({"role": role, "content": content})


def _append_tool_payload(session, payload):
	session.messages.append({"role": "tool", "content": dict(payload or {})})


def _assistant_text_payload(text):
	return str(text or "")


def _save_session(*args, **kwargs):
	return None


def _tool_payloads(session):
	return [message["content"] for message in session.messages if message.get("role") == "tool"]


def _assistant_messages(session):
	return [message["content"] for message in session.messages if message.get("role") == "assistant"]


def _first_tool_index(session, payload_type):
	for index, message in enumerate(session.messages):
		if message.get("role") == "tool" and message.get("content", {}).get("type") == payload_type:
			return index
	return -1


def _first_assistant_index(session):
	for index, message in enumerate(session.messages):
		if message.get("role") == "assistant":
			return index
	return -1


class ControlAuthorizedEmissionContractTests(unittest.TestCase):
	def test_visible_context_trace_inspection_emits_trace_debug_authority_before_assistant(self):
		session = _Session()

		handled, payload = try_activate_visible_context_trace_inspection_response(
			session_doc=session,
			request_id="REQ-1",
			session_id="SID-1",
			user_id="USR-1",
			site_name="test",
			raw_message="Show latest context authority trace",
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			save_session=_save_session,
			additional_tool_payloads=[{"type": "qwen_control_shadow_payload", "safe": True}],
		)

		tool_payloads = _tool_payloads(session)
		emission = next(item for item in tool_payloads if item.get("type") == AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)

		self.assertTrue(handled)
		self.assertTrue(payload["ok"])
		self.assertEqual(emission["answer_type"], ANSWER_TYPE_TRACE)
		self.assertEqual(emission["control_meta_authority"]["authority_source"], "trace_debug")
		self.assertLess(_first_tool_index(session, INSPECTION_PAYLOAD_TYPE), _first_assistant_index(session))
		self.assertLess(_first_tool_index(session, AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE), _first_assistant_index(session))

	def test_nbu_presentation_safe_response_emits_control_authority_before_assistant(self):
		session = _Session()
		activation = {
			"activated": True,
			"answer_text": "Safe NBU response",
			"activation_contract": {
				"type": "qwen_nbu_presentation_activation_contract",
				"activation_mode": "show_supported_options",
				"reason": "Controlled presentation response.",
			},
			"action": "show_supported_options",
			"response_mode": "safe_response",
		}

		with patch(
			"ai_assistant_ui.qwen_chat.natural_business_understanding_service_activation.build_nbu_current_artifact_answer_response",
			return_value=activation,
		):
			handled, payload = try_activate_nbu_presentation_response(
				session_doc=session,
				request_id="REQ-2",
				session_id="SID-2",
				user_id="USR-2",
				site_name="test",
				raw_message="What can you do?",
				latest_grounded_turn={},
				current_artifact={},
				interaction_contract=_PayloadObject(
					{"type": "qwen_interaction_contract", "request_id": "REQ-2", "session_id": "SID-2"},
					request_id="REQ-2",
					session_id="SID-2",
				),
				append_message=_append_message,
				append_tool_payload=_append_tool_payload,
				assistant_text_payload=_assistant_text_payload,
				save_session=_save_session,
				nbu_trace_payload={"type": "qwen_nbu_shadow_trace", "semantic_ownership_ledger": {"owner": "test"}},
			)

		tool_payloads = _tool_payloads(session)
		emission = next(item for item in tool_payloads if item.get("type") == AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)

		self.assertTrue(handled)
		self.assertTrue(payload["ok"])
		self.assertEqual(_assistant_messages(session), ["Safe NBU response"])
		self.assertEqual(emission["answer_type"], ANSWER_TYPE_CONTROL)
		self.assertEqual(emission["control_meta_authority"]["answer_mode"], "show_supported_options")
		self.assertLess(_first_tool_index(session, AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE), _first_assistant_index(session))

	def test_clarification_show_options_emits_control_authority_and_stores_pending_after_emit(self):
		session = _Session()
		signal = {
			"type": "qwen_clarification_signal_contract",
			"user_question": "Which report?",
			"suggested_options": ["Accounts Receivable", "Accounts Payable"],
			"reason_type": "ambiguous_report",
		}
		state = build_pending_clarification_state(signal, attempt_count=0, max_attempts=3)
		clarification_response = _PayloadObject(
			{"type": "qwen_clarification_response_contract", "decision": "show_options", "reason": "Need user choice."},
			decision="show_options",
			reason="Need user choice.",
			resolved_option="",
		)

		handled, _, _, payload = clarification_lane.handle_pending_clarification_turn(
			session_doc=session,
			request_id="REQ-3",
			session_id="SID-3",
			user_id="USR-3",
			site_name="test",
			raw_message="show options",
			pending_clarification_signal=signal,
			clarification_state=state,
			clarification_response_contract=clarification_response,
			interaction_contract=_PayloadObject(
				{"type": "qwen_interaction_contract", "request_id": "REQ-3", "session_id": "SID-3"},
				request_id="REQ-3",
				session_id="SID-3",
			),
			frontdoor_semantic_result=_PayloadObject({"type": "qwen_frontdoor_semantic_result"}),
			frontdoor_contract=_PayloadObject({"type": "qwen_frontdoor_contract"}),
			latest_grounded_turn_available=False,
			latest_grounded_turn={},
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			append_knowledge_boundary_contract=lambda *args, **kwargs: {},
			assistant_text_payload=_assistant_text_payload,
			save_session=_save_session,
		)

		emission = next(item for item in _tool_payloads(session) if item.get("type") == AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)

		self.assertTrue(handled)
		self.assertTrue(payload["ok"])
		self.assertEqual(emission["answer_type"], ANSWER_TYPE_CONTROL)
		self.assertEqual(emission["control_meta_authority"]["answer_mode"], "clarification_show_options")
		self.assertIn("qwen_pending_clarification_state", session.pending_clarification_state_json)
		self.assertLess(_first_tool_index(session, AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE), _first_assistant_index(session))

	def test_recovery_guidance_emits_control_authority_and_returns_approved_text(self):
		session = _Session()

		handled, payload = handle_recovery_guidance_response(
			session,
			request_id="REQ-4",
			raw_message="help me recover",
			interaction_contract=_PayloadObject(
				{"type": "qwen_interaction_contract", "request_id": "REQ-4", "session_id": "TEST-SESSION"},
				request_id="REQ-4",
				session_id="TEST-SESSION",
			),
			frontdoor_semantic_result=_PayloadObject({"type": "qwen_frontdoor_semantic_result"}),
			frontdoor_contract=_PayloadObject({"type": "qwen_frontdoor_contract"}),
			clarification_response_contract=None,
			response_policy_contract=_PayloadObject({"type": "qwen_response_policy_contract"}),
			semantic_repair_payload={"type": "qwen_semantic_repair_payload"},
			repair_contract_payload={
				"type": "qwen_repair_contract",
				"repair_intent_type": "recovery",
				"repair_state": "ready",
				"allowed_next_lane": "clarification",
			},
			latest_grounded_turn={},
			answer_text="Recovery guidance",
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			save_session=_save_session,
		)

		emission = next(item for item in _tool_payloads(session) if item.get("type") == AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)

		self.assertTrue(handled)
		self.assertTrue(payload["ok"])
		self.assertEqual(payload["answer_text"], "Recovery guidance")
		self.assertEqual(_assistant_messages(session), ["Recovery guidance"])
		self.assertEqual(emission["answer_type"], ANSWER_TYPE_CONTROL)
		self.assertLess(_first_tool_index(session, AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE), _first_assistant_index(session))


if __name__ == "__main__":
	unittest.main()
