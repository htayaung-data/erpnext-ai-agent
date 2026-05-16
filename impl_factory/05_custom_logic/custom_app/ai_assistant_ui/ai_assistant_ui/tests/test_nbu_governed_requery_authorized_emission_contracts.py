from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat import natural_business_understanding_governed_requery_activation as activation
from ai_assistant_ui.qwen_chat.contracts import build_interaction_contract


REQUEST_ID = "req-ec4k-nbu-requery"
SESSION_ID = "session-ec4k"


class _ResponsePolicyContract:
	def to_runtime_payload(self):
		return {"presentation": "concise"}


def _trace_payload(*, requested_action: str = "lookup") -> dict:
	return {
		"type": "qwen_natural_business_understanding_trace_contract",
		"request_id": REQUEST_ID,
		"session_id": SESSION_ID,
		"raw_message": "what is the credit limit of that customer?",
		"selected_candidate_id": "candidate-1",
		"candidate_interpretations": [
			{
				"candidate_id": "candidate-1",
				"intent_scope": "visible_context_followup",
				"business_domain": "customer_credit",
				"requested_action": requested_action,
				"target_reference": "selected_entity",
				"candidate_route": "entity_detail",
				"requested_metrics": [] if requested_action == "detail" else ["credit_limit_amount"],
				"requested_dimensions": ["customer"],
				"evidence_need": "needs_governed_requery",
				"authority_class": "safe_read",
			}
		],
		"conversation_action_decision": {
			"action": "execute_governed_requery",
			"response_mode": "governed_query",
			"selected_candidate_id": "candidate-1",
			"requires_routing_change": True,
			"safe_to_execute": True,
		},
		"governed_requery_plan": {
			"status": "ready_shadow",
			"planner_mode": "entity_detail_requery",
			"target_route": "entity_detail",
			"target_entity": {
				"entity_type": "customer",
				"entity_key": "35th Street Mobile Wholesale",
				"entity_label": "35th Street Mobile Wholesale",
			},
			"requested_metrics": [] if requested_action == "detail" else ["credit_limit_amount"],
			"requested_dimensions": ["customer"],
			"missing_fields": [] if requested_action == "detail" else ["credit_limit"],
			"required_context": [],
			"shadow_execution_ready": True,
		},
	}


def _artifact_payload() -> dict:
	return {
		"type": "qwen_entity_detail_artifact",
		"artifact_id": "entity-detail-customer-1",
		"family_id": "entity_detail",
		"dimensions": {
			"entity_type": "customer",
			"entity_key": "35th Street Mobile Wholesale",
			"entity_label": "35th Street Mobile Wholesale",
		},
		"metrics": {"credit_limit": 75000000},
	}


def _grounded_turn_payload() -> dict:
	return {
		"type": "qwen_grounded_turn_context",
		"request_id": REQUEST_ID,
		"trace_request_id": REQUEST_ID,
		"grounded": True,
		"source_kind": "tool",
		"source_name": "entity_detail_requery",
		"artifact_family_id": "entity_detail",
		"artifact_type": "qwen_entity_detail_artifact",
	}


def _interaction_contract():
	return build_interaction_contract(
		request_id=REQUEST_ID,
		session_id=SESSION_ID,
		user_id="Administrator",
		site_name="erpai_prj1",
		raw_message="what is the credit limit of that customer?",
	)


def _append_message(session, role, content):
	session["messages"].append({"role": role, "content": content})


def _append_tool_payload(session, payload):
	session["messages"].append({"role": "tool", "content": json.dumps(payload)})


def _tool_payloads(session):
	return [
		json.loads(message["content"])
		for message in session["messages"]
		if message["role"] == "tool"
	]


def _first_message_index(session, predicate):
	for index, message in enumerate(session["messages"]):
		if predicate(message):
			return index
	return -1


class NBUGovernedRequeryAuthorizedEmissionContractTests(unittest.TestCase):
	def _activate(self, *, outcome: dict, trace_payload: dict | None = None, direct_response=None):
		session = {"name": SESSION_ID, "messages": []}

		def execute_entity_drilldown(**kwargs):
			self.assertEqual(kwargs["entity_reference"]["entity_key"], "35th Street Mobile Wholesale")
			return dict(outcome)

		with patch.object(activation, "entity_detail_runtime_policy", return_value={"can_execute": True}):
			handled, payload = activation.try_activate_nbu_governed_requery_response(
				session_doc=session,
				request_id=REQUEST_ID,
				session_id=SESSION_ID,
				user_id="Administrator",
				site_name="erpai_prj1",
				raw_message="what is the credit limit of that customer?",
				nbu_trace_payload=trace_payload or _trace_payload(),
				current_artifact={},
				latest_grounded_turn={"grounded": True, "family_id": "accounts_receivable_aging"},
				interaction_contract=_interaction_contract(),
				response_policy_contract=_ResponsePolicyContract(),
				append_message=_append_message,
				append_tool_payload=_append_tool_payload,
				assistant_text_payload=lambda text: text,
				save_session=lambda doc, **kwargs: doc.update({"saved": True}),
				execute_entity_drilldown=execute_entity_drilldown,
				direct_evidence_response=direct_response,
			)
		return session, handled, payload

	def test_direct_evidence_first_answer_emits_through_authorized_helper(self):
		outcome = {
			"ok": True,
			"answer_text": "Full customer profile fallback",
			"artifact_payload": _artifact_payload(),
			"grounded_turn_payload": _grounded_turn_payload(),
		}
		session, handled, payload = self._activate(
			outcome=outcome,
			direct_response=lambda **kwargs: {
				"answer_text": "The configured credit limit is 75,000,000 MMK.",
			},
		)

		self.assertTrue(handled)
		self.assertTrue(payload["ok"])
		self.assertNotIn("answer_text", payload)
		assistant_texts = [message["content"] for message in session["messages"] if message["role"] == "assistant"]
		self.assertEqual(assistant_texts, ["The configured credit limit is 75,000,000 MMK."])
		tool_payloads = _tool_payloads(session)
		audit = [item for item in tool_payloads if item.get("type") == "qwen_audit_envelope"]
		emissions = [item for item in tool_payloads if item.get("type") == "qwen_authorized_assistant_emission_contract"]
		self.assertEqual(len(audit), 1)
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "governed_report_answer")
		self.assertEqual(emissions[0]["preflight_status"], "passed")
		self.assertTrue(emissions[0]["emitted"])
		self.assertEqual(audit[0]["final_answer_authority"]["authority_source"], "deterministic_tool")
		self.assertEqual(audit[0]["final_answer_authority"]["selected_report_family"], "entity_detail")

	def test_rich_entity_detail_answer_preserves_rendered_text(self):
		outcome = {
			"ok": True,
			"answer_text": "Narrow fallback should not be used.",
			"artifact_payload": _artifact_payload(),
			"grounded_turn_payload": _grounded_turn_payload(),
			"rendered_response_payload": {
				"type": "qwen_rendered_response",
				"title": "35th Street Mobile Wholesale Details",
				"blocks": [
					{
						"block_type": "summary_table",
						"title": "Credit Profile",
						"columns": ["Field", "Value"],
						"rows": [["Credit Limit", "75,000,000 MMK"]],
					}
				],
			},
		}
		session, handled, payload = self._activate(
			outcome=outcome,
			trace_payload=_trace_payload(requested_action="detail"),
			direct_response=lambda **kwargs: {"answer_text": "Narrow row should not be used."},
		)

		self.assertTrue(handled)
		self.assertTrue(payload["ok"])
		assistant_texts = [message["content"] for message in session["messages"] if message["role"] == "assistant"]
		self.assertEqual(len(assistant_texts), 1)
		self.assertIn("35th Street Mobile Wholesale Details", assistant_texts[0])
		self.assertIn("Credit Profile", assistant_texts[0])
		self.assertNotIn("Narrow fallback should not be used", assistant_texts[0])
		self.assertNotIn("Narrow row should not be used", assistant_texts[0])

	def test_missing_authority_blocks_without_assistant_or_payload_answer_text(self):
		outcome = {
			"ok": True,
			"answer_text": "This should not leak.",
			"artifact_payload": {},
			"grounded_turn_payload": {},
		}
		session, handled, payload = self._activate(outcome=outcome)

		self.assertTrue(handled)
		self.assertFalse(payload["ok"])
		self.assertNotIn("answer_text", payload)
		self.assertEqual([message for message in session["messages"] if message["role"] == "assistant"], [])
		emissions = [
			item
			for item in _tool_payloads(session)
			if item.get("type") == "qwen_authorized_assistant_emission_contract"
		]
		self.assertEqual(len(emissions), 1)
		self.assertTrue(emissions[0]["blocked"])
		self.assertEqual(emissions[0]["preflight_status"], "missing_authority")
		self.assertEqual(emissions[0]["block_reason"], "final_answer_authority_incomplete")
		serialized_payloads = json.dumps(_tool_payloads(session))
		self.assertNotIn("This should not leak.", serialized_payloads)
		self.assertNotIn("qwen_rendered_response", serialized_payloads)

	def test_invalid_grounded_authority_blocks_without_business_payload_leak(self):
		outcome = {
			"ok": True,
			"answer_text": "Artifact answer should not leak.",
			"artifact_payload": {},
			"grounded_turn_payload": {},
			"rendered_response_payload": {
				"type": "qwen_rendered_response",
				"title": "Leaky rendered detail",
			},
			"narrative_contract_payload": {
				"type": "qwen_narrative_contract",
				"answer_text": "Artifact answer should not leak.",
			},
		}
		session, handled, payload = self._activate(outcome=outcome)
		tool_payloads = _tool_payloads(session)
		emissions = [
			item
			for item in tool_payloads
			if item.get("type") == "qwen_authorized_assistant_emission_contract"
		]

		self.assertTrue(handled)
		self.assertFalse(payload["ok"])
		self.assertNotIn("answer_text", payload)
		self.assertEqual([message for message in session["messages"] if message["role"] == "assistant"], [])
		self.assertEqual(len(emissions), 1)
		self.assertTrue(emissions[0]["blocked"])
		self.assertEqual(emissions[0]["preflight_status"], "missing_authority")
		serialized_payloads = json.dumps(tool_payloads)
		self.assertNotIn("Artifact answer should not leak.", serialized_payloads)
		self.assertNotIn("Leaky rendered detail", serialized_payloads)

	def test_audit_and_emission_contract_precede_assistant_without_duplicate_audit(self):
		outcome = {
			"ok": True,
			"answer_text": "Full customer profile fallback",
			"artifact_payload": _artifact_payload(),
			"grounded_turn_payload": _grounded_turn_payload(),
		}
		session, handled, payload = self._activate(outcome=outcome)

		self.assertTrue(handled)
		self.assertTrue(payload["ok"])
		assistant_index = _first_message_index(session, lambda message: message["role"] == "assistant")
		audit_index = _first_message_index(
			session,
			lambda message: message["role"] == "tool"
			and json.loads(message["content"]).get("type") == "qwen_audit_envelope",
		)
		emission_index = _first_message_index(
			session,
			lambda message: message["role"] == "tool"
			and json.loads(message["content"]).get("type") == "qwen_authorized_assistant_emission_contract",
		)
		self.assertGreaterEqual(audit_index, 0)
		self.assertGreaterEqual(emission_index, 0)
		self.assertGreater(assistant_index, audit_index)
		self.assertGreater(assistant_index, emission_index)
		self.assertEqual(
			len([item for item in _tool_payloads(session) if item.get("type") == "qwen_audit_envelope"]),
			1,
		)


if __name__ == "__main__":
	unittest.main()
