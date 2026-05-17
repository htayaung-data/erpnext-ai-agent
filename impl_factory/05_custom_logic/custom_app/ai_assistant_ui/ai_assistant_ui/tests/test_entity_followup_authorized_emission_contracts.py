from __future__ import annotations

import json
import unittest

from ai_assistant_ui.qwen_chat.entity_followup_support import try_entity_detail_followup
from ai_assistant_ui.qwen_chat.contracts import build_interaction_contract


REQUEST_ID = "req-ec4m-entity-followup"
SESSION_ID = "session-ec4m"


class _Session:
	name = SESSION_ID

	def __init__(self):
		self.messages = []
		self.saved = False


class _ResponsePolicyContract:
	def to_runtime_payload(self):
		return {"presentation": "concise"}


def _interaction_contract():
	return build_interaction_contract(
		request_id=REQUEST_ID,
		session_id=SESSION_ID,
		user_id="Administrator",
		site_name="erpai_prj1",
		raw_message="tell me more about this customer",
	)


def _append_message(session, role, content):
	session.messages.append({"role": role, "content": content})


def _append_tool_payload(session, payload):
	session.messages.append({"role": "tool", "content": json.dumps(payload)})


def _assistant_text_payload(text):
	return str(text or "")


def _tool_trace_message(**kwargs):
	return json.dumps({"type": "qwen_tool_trace", **kwargs})


def _save_session(session, **kwargs):
	session.saved = True


def _tool_payloads(session):
	return [
		json.loads(message["content"])
		for message in session.messages
		if message["role"] == "tool"
	]


def _first_message_index(session, predicate):
	for index, message in enumerate(session.messages):
		if predicate(message):
			return index
	return -1


def _artifact_payload():
	return {
		"type": "qwen_entity_detail_artifact",
		"artifact_id": "entity-followup-customer-1",
		"family_id": "entity_detail",
		"dimensions": {
			"entity_type": "customer",
			"entity_key": "35th Street Mobile Wholesale",
			"entity_label": "35th Street Mobile Wholesale",
		},
		"metrics": {"credit_limit": 75000000},
	}


def _grounded_turn_payload():
	return {
		"type": "qwen_grounded_turn_context",
		"request_id": REQUEST_ID,
		"trace_request_id": REQUEST_ID,
		"grounded": True,
		"source_kind": "tool",
		"source_name": "entity_detail_lookup",
		"artifact_family_id": "entity_detail",
		"artifact_type": "qwen_entity_detail_artifact",
	}


class EntityFollowupAuthorizedEmissionContractTests(unittest.TestCase):
	def _run_followup(self, *, outcome=None, raise_exc=None):
		session = _Session()

		def execute_entity_drilldown(**kwargs):
			if raise_exc is not None:
				raise raise_exc
			return dict(outcome or {})

		result = try_entity_detail_followup(
			session,
			request_id=REQUEST_ID,
			raw_message="tell me more about this customer",
			entity_reference={"entity_type": "customer", "entity_key": "35th Street Mobile Wholesale"},
			interaction_contract=_interaction_contract(),
			response_policy_contract=_ResponsePolicyContract(),
			latest_grounded_turn={"grounded": True, "family_id": "accounts_receivable_aging"},
			execute_entity_drilldown=execute_entity_drilldown,
			log_error=lambda message: None,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			tool_trace_message=_tool_trace_message,
			save_session=_save_session,
		)
		self.assertIsNotNone(result)
		handled, payload = result
		self.assertTrue(handled)
		return session, payload

	def test_success_emits_governed_report_authority(self):
		session, payload = self._run_followup(
			outcome={
				"ok": True,
				"answer_text": "Customer detail answer",
				"artifact_payload": _artifact_payload(),
				"rendered_response_payload": {"type": "qwen_rendered_response", "title": "Customer Detail"},
				"narrative_contract_payload": {"type": "qwen_narrative_contract"},
				"grounded_turn_payload": _grounded_turn_payload(),
				"entity_reference": {"entity_type": "customer", "entity_key": "35th Street Mobile Wholesale"},
			}
		)

		self.assertTrue(payload["ok"])
		self.assertNotIn("answer_text", payload)
		assistant_messages = [message for message in session.messages if message["role"] == "assistant"]
		self.assertEqual([message["content"] for message in assistant_messages], ["Customer detail answer"])
		tool_payloads = _tool_payloads(session)
		audits = [item for item in tool_payloads if item.get("type") == "qwen_audit_envelope"]
		emissions = [item for item in tool_payloads if item.get("type") == "qwen_authorized_assistant_emission_contract"]
		self.assertEqual(len(audits), 1)
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "governed_report_answer")
		self.assertEqual(emissions[0]["preflight_status"], "passed")
		self.assertTrue(emissions[0]["emitted"])
		self.assertEqual(audits[0]["final_answer_authority"]["authority_source"], "deterministic_tool")
		self.assertEqual(audits[0]["final_answer_authority"]["selected_report_family"], "entity_detail")
		traces = [item for item in tool_payloads if item.get("type") == "qwen_tool_trace"]
		self.assertEqual(len(traces), 1)
		self.assertNotIn("Customer detail answer", json.dumps(traces[0]))

	def test_failure_emits_error_fallback_authority(self):
		session, payload = self._run_followup(raise_exc=RuntimeError("lookup failed"))

		self.assertFalse(payload["ok"])
		self.assertNotIn("answer_text", payload)
		assistant_messages = [message for message in session.messages if message["role"] == "assistant"]
		self.assertEqual(len(assistant_messages), 1)
		self.assertIn("couldn't complete", assistant_messages[0]["content"])
		emissions = [
			item
			for item in _tool_payloads(session)
			if item.get("type") == "qwen_authorized_assistant_emission_contract"
		]
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "error_fallback_answer")
		self.assertEqual(emissions[0]["control_meta_authority"]["authority_source"], "error_fallback")
		self.assertEqual(emissions[0]["preflight_status"], "passed")

	def test_missing_authority_blocks_without_assistant_or_payload_answer_text(self):
		session, payload = self._run_followup(
			outcome={
				"ok": True,
				"answer_text": "This answer must not leak",
				"artifact_payload": {},
				"grounded_turn_payload": {},
				"entity_reference": {"entity_type": "customer", "entity_key": "35th Street Mobile Wholesale"},
			}
		)

		self.assertFalse(payload["ok"])
		self.assertNotIn("answer_text", payload)
		self.assertEqual([message for message in session.messages if message["role"] == "assistant"], [])
		emissions = [
			item
			for item in _tool_payloads(session)
			if item.get("type") == "qwen_authorized_assistant_emission_contract"
		]
		self.assertEqual(len(emissions), 1)
		self.assertTrue(emissions[0]["blocked"])
		self.assertEqual(emissions[0]["preflight_status"], "missing_authority")
		self.assertEqual(emissions[0]["block_reason"], "final_answer_authority_incomplete")
		self.assertEqual(len(_tool_payloads(session)), 1)
		self.assertNotIn("This answer must not leak", json.dumps(_tool_payloads(session)))
		self.assertNotIn("qwen_tool_trace", json.dumps(_tool_payloads(session)))

	def test_artifact_present_but_invalid_grounding_blocks_without_business_payloads(self):
		session, payload = self._run_followup(
			outcome={
				"ok": True,
				"answer_text": "Unauthorized entity detail answer",
				"artifact_payload": _artifact_payload(),
				"rendered_response_payload": {
					"type": "qwen_rendered_response",
					"title": "Unauthorized Customer Detail",
				},
				"narrative_contract_payload": {"type": "qwen_narrative_contract"},
				"grounded_turn_payload": {
					"type": "qwen_grounded_turn_context",
					"request_id": REQUEST_ID,
					"grounded": False,
				},
				"entity_reference": {"entity_type": "customer", "entity_key": "35th Street Mobile Wholesale"},
			}
		)

		self.assertFalse(payload["ok"])
		self.assertNotIn("answer_text", payload)
		self.assertEqual([message for message in session.messages if message["role"] == "assistant"], [])
		tool_payloads = _tool_payloads(session)
		self.assertEqual(len(tool_payloads), 1)
		self.assertEqual(tool_payloads[0]["type"], "qwen_authorized_assistant_emission_contract")
		self.assertTrue(tool_payloads[0]["blocked"])
		self.assertEqual(tool_payloads[0]["block_reason"], "final_answer_authority_incomplete")
		serialized = json.dumps(tool_payloads)
		self.assertNotIn("Unauthorized entity detail answer", serialized)
		self.assertNotIn("qwen_entity_detail_artifact", serialized)
		self.assertNotIn("qwen_rendered_response", serialized)
		self.assertNotIn("qwen_narrative_contract", serialized)
		self.assertNotIn("qwen_grounded_turn_context", serialized)
		self.assertNotIn("qwen_tool_trace", serialized)

	def test_success_payloads_and_authority_precede_assistant_without_duplicate_audit(self):
		session, payload = self._run_followup(
			outcome={
				"ok": True,
				"answer_text": "Customer detail answer",
				"artifact_payload": _artifact_payload(),
				"rendered_response_payload": {"type": "qwen_rendered_response", "title": "Customer Detail"},
				"narrative_contract_payload": {"type": "qwen_narrative_contract"},
				"grounded_turn_payload": _grounded_turn_payload(),
				"entity_reference": {"entity_type": "customer", "entity_key": "35th Street Mobile Wholesale"},
			}
		)

		self.assertTrue(payload["ok"])
		assistant_index = _first_message_index(session, lambda message: message["role"] == "assistant")
		for payload_type in [
			"qwen_entity_detail_artifact",
			"qwen_rendered_response",
			"qwen_narrative_contract",
			"qwen_grounded_turn_context",
			"qwen_tool_trace",
			"qwen_audit_envelope",
			"qwen_authorized_assistant_emission_contract",
		]:
			index = _first_message_index(
				session,
				lambda message, payload_type=payload_type: message["role"] == "tool"
				and json.loads(message["content"]).get("type") == payload_type,
			)
			self.assertGreaterEqual(index, 0, payload_type)
			self.assertLess(index, assistant_index, payload_type)
		self.assertEqual(
			len([item for item in _tool_payloads(session) if item.get("type") == "qwen_audit_envelope"]),
			1,
		)


if __name__ == "__main__":
	unittest.main()
