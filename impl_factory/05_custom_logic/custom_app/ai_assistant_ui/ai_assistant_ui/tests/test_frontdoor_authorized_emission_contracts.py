from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from ai_assistant_ui.qwen_chat.contracts import build_interaction_contract
from ai_assistant_ui.qwen_chat.lanes.frontdoor_lane import handle_frontdoor_turn


PROJECT_ROOT = Path(__file__).resolve().parents[6]
ROOT_FRONTDOOR = (
	PROJECT_ROOT
	/ "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py"
)


class PayloadObject(SimpleNamespace):
	def to_payload(self):
		return dict(self.payload)


def _tool_message(payload):
	return {"role": "tool", "content": json.dumps(payload)}


def _frontdoor_contract(
	*,
	intent_class: str,
	text: str,
	response_payload: dict | None = None,
	response_mode: str = "direct_answer",
):
	payload = {
		"type": "qwen_front_door_intent_gate_contract",
		"request_id": "req-frontdoor-auth",
		"intent_class": intent_class,
		"confidence": 1.0,
		"handle_in_front_door": True,
		"response_mode": response_mode,
		"response_payload": {"text": text, **dict(response_payload or {})},
		"route_target": "front_door",
		"reason": "contract test frontdoor answer",
	}
	return PayloadObject(
		payload=payload,
		request_id=payload["request_id"],
		intent_class=intent_class,
		confidence=1.0,
		handle_in_front_door=True,
		response_mode=response_mode,
		response_payload=payload["response_payload"],
		route_target="front_door",
		reason=payload["reason"],
	)


def _semantic_result():
	return PayloadObject(payload={"type": "qwen_semantic_frontdoor_result", "status": "accepted"})


def _render_result(answer_text: str):
	return PayloadObject(
		payload={"type": "qwen_frontdoor_render_result", "ok": True, "answer_text": answer_text},
		ok=True,
		answer_text=answer_text,
	)


def _allowed_boundary():
	return {
		"type": "qwen_knowledge_boundary_contract",
		"final_lane": "front_door",
		"knowledge_coverage_state": "covered",
		"user_response_mode": "normal_answer",
		"safe_next_action": "allow_current_lane",
		"allowed_to_answer": True,
	}


def _blocking_boundary():
	return {
		"type": "qwen_knowledge_boundary_contract",
		"final_lane": "front_door",
		"knowledge_coverage_state": "valid_erp_domain_uncovered",
		"user_response_mode": "safe_refusal",
		"safe_next_action": "respond_unsupported",
		"allowed_to_answer": False,
	}


class FrontdoorAuthorizedEmissionContractTests(unittest.TestCase):
	def _run_frontdoor(self, *, frontdoor_contract, boundary_payload=None):
		session_doc = {"messages": []}
		payloads = []
		pending_signals = []
		answer_text = str(frontdoor_contract.response_payload.get("text") or "").strip()

		def append_message(session_doc, role, text):
			session_doc.setdefault("messages", []).append({"role": role, "content": text})

		def append_tool_payload(session_doc, payload):
			payloads.append(payload)
			session_doc.setdefault("messages", []).append(_tool_message(payload))

		def append_knowledge_boundary_contract(session_doc, **kwargs):
			payload = dict(boundary_payload or _allowed_boundary())
			append_tool_payload(session_doc, payload)
			return payload

		def store_pending_clarification_signal(session_doc, payload):
			pending_signals.append(payload)

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		handled, result_payload = handle_frontdoor_turn(
			session_doc=session_doc,
			request_id="req-frontdoor-auth",
			session_id="session-frontdoor-auth",
			message="frontdoor request",
			raw_message="frontdoor request",
			interaction_contract=build_interaction_contract(
				request_id="req-frontdoor-auth",
				session_id="session-frontdoor-auth",
				user_id="user@example.com",
				site_name="erpai_prj1",
				raw_message="frontdoor request",
			),
			frontdoor_semantic_result=_semantic_result(),
			frontdoor_contract=frontdoor_contract,
			frontdoor_render_result=_render_result(answer_text),
			frontdoor_answer=answer_text,
			context_force_new_query=False,
			latest_grounded_turn_available=False,
			latest_grounded_turn={},
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			append_knowledge_boundary_contract=append_knowledge_boundary_contract,
			assistant_text_payload=lambda text: text,
			store_pending_clarification_signal=store_pending_clarification_signal,
			save_session=save_session,
		)
		return handled, result_payload, session_doc, payloads, pending_signals

	def _payloads_around_assistant(self, session_doc):
		messages = session_doc.get("messages") or []
		assistant_indices = [index for index, message in enumerate(messages) if message.get("role") == "assistant"]
		self.assertTrue(assistant_indices)
		assistant_index = assistant_indices[-1]

		def decode(items):
			decoded = []
			for message in items:
				if message.get("role") != "tool":
					continue
				decoded.append(json.loads(message.get("content") or "{}"))
			return decoded

		return decode(messages[:assistant_index]), decode(messages[assistant_index + 1 :])

	def _assert_no_audit_or_emission_after_answer(self, session_doc):
		_before, after = self._payloads_around_assistant(session_doc)
		self.assertFalse([payload for payload in after if payload.get("type") == "qwen_audit_envelope"])
		self.assertFalse([
			payload for payload in after if payload.get("type") == "qwen_authorized_assistant_emission_contract"
		])

	def test_governed_frontdoor_answer_emits_authorized_audit_before_assistant(self):
		contract = _frontdoor_contract(
			intent_class="governed_composite_value",
			text="Top customers by revenue are available.",
			response_payload={
				"normalized_family_artifact": {
					"type": "qwen_normalized_family_artifact_contract",
					"artifact_id": "frontdoor-artifact-1",
					"family_id": "ranking_analytics",
				},
				"rendered_family_response": {"type": "qwen_rendered_family_response"},
				"grounded_turn_context": {
					"type": "qwen_grounded_turn_context",
					"grounded": True,
					"source_kind": "report",
					"source_name": "ranking_analytics",
					"artifact_family_id": "ranking_analytics",
					"trace_request_id": "trace-frontdoor-1",
				},
				"runtime_trace_payload": {"agent_meta": {"engine": "frontdoor_runtime"}},
			},
		)
		handled, result_payload, session_doc, _payloads, _pending = self._run_frontdoor(frontdoor_contract=contract)
		before, _after = self._payloads_around_assistant(session_doc)
		audits = [payload for payload in before if payload.get("type") == "qwen_audit_envelope"]
		emissions = [payload for payload in before if payload.get("type") == "qwen_authorized_assistant_emission_contract"]

		self.assertTrue(handled)
		self.assertTrue(result_payload["agent_meta"]["authorized_emission"]["emitted"])
		self.assertEqual(len(audits), 1)
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "governed_report_answer")
		self.assertEqual(emissions[0]["preflight_status"], "passed")
		self.assertEqual(audits[0]["runtime_engine"], "frontdoor_runtime")
		self._assert_no_audit_or_emission_after_answer(session_doc)

	def test_governed_kpi_definition_with_registry_evidence_emits_business_factual_authority(self):
		contract = _frontdoor_contract(
			intent_class="governed_kpi_definition",
			text="Gross margin means sales less cost of goods sold.",
			response_payload={
				"definition_state": {
					"resolution_state": "active",
					"definition": "Gross margin means sales less cost of goods sold.",
				},
				"formula_state": {
					"resolution_state": "active",
					"formula": "Sales - Cost of Goods Sold",
				},
				"lookup_value": "gross margin",
				"company_name": "Mingalar Mobile Distribution Co., Ltd.",
				"query_kind": "definition",
			},
		)
		handled, result_payload, session_doc, _payloads, _pending = self._run_frontdoor(frontdoor_contract=contract)
		before, _after = self._payloads_around_assistant(session_doc)
		audits = [payload for payload in before if payload.get("type") == "qwen_audit_envelope"]
		emissions = [payload for payload in before if payload.get("type") == "qwen_authorized_assistant_emission_contract"]
		final_authority = emissions[0]["final_answer_authority"]

		self.assertTrue(handled)
		self.assertTrue(result_payload["agent_meta"]["authorized_emission"]["emitted"])
		self.assertEqual(len(audits), 1)
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "business_facing_factual_answer")
		self.assertEqual(emissions[0]["preflight_status"], "passed")
		self.assertEqual(final_authority["authority_source"], "deterministic_tool")
		self.assertEqual(final_authority["selected_report_family"], "governed_kpi_definition")
		self.assertEqual(final_authority["evidence_scope"], "grounded_turn_context")
		self._assert_no_audit_or_emission_after_answer(session_doc)

	def test_governed_kpi_definition_without_registry_evidence_blocks(self):
		contract = _frontdoor_contract(
			intent_class="governed_kpi_definition",
			text="This would be an ungrounded KPI definition.",
			response_payload={
				"lookup_value": "gross margin",
				"company_name": "Mingalar Mobile Distribution Co., Ltd.",
				"query_kind": "definition",
			},
		)
		handled, result_payload, session_doc, payloads, _pending = self._run_frontdoor(frontdoor_contract=contract)
		emissions = [payload for payload in payloads if payload.get("type") == "qwen_authorized_assistant_emission_contract"]

		self.assertTrue(handled)
		self.assertEqual(len(emissions), 1)
		self.assertTrue(emissions[0]["blocked"])
		self.assertEqual(emissions[0]["answer_type"], "business_facing_factual_answer")
		self.assertEqual(emissions[0]["preflight_status"], "missing_authority")
		self.assertEqual(emissions[0]["block_reason"], "final_answer_authority_incomplete")
		self.assertNotEqual(
			emissions[0]["final_answer_authority"].get("authority_source"),
			"policy_boundary",
		)
		self.assertNotEqual(
			emissions[0]["final_answer_authority"].get("policy_boundary"),
			"covered",
		)
		self.assertFalse(result_payload["agent_meta"]["authorized_emission"]["emitted"])
		self.assertNotIn("assistant", [message.get("role") for message in session_doc.get("messages", [])])
		serialized_payloads = json.dumps(payloads)
		self.assertNotIn("This would be an ungrounded KPI definition.", serialized_payloads)
		self.assertNotIn("qwen_frontdoor_render_result", serialized_payloads)

	def test_capability_question_still_uses_control_meta_authority(self):
		contract = _frontdoor_contract(
			intent_class="capability_question",
			text="I can help with governed ERP questions.",
		)
		handled, result_payload, session_doc, _payloads, _pending = self._run_frontdoor(frontdoor_contract=contract)
		before, _after = self._payloads_around_assistant(session_doc)
		emissions = [payload for payload in before if payload.get("type") == "qwen_authorized_assistant_emission_contract"]

		self.assertTrue(handled)
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "control_meta_answer")
		self.assertEqual(emissions[0]["control_meta_authority"]["authority_source"], "control_meta")
		self.assertTrue(result_payload["agent_meta"]["authorized_emission"]["emitted"])
		self._assert_no_audit_or_emission_after_answer(session_doc)

	def test_clarification_frontdoor_answer_uses_control_authority(self):
		contract = _frontdoor_contract(
			intent_class="compound_request_clarification",
			text="Which request should I run first?",
			response_mode="clarification_signal",
			response_payload={
				"clarification_signal_payload": {
					"type": "qwen_clarification_signal",
					"question": "Which request should I run first?",
				}
			},
		)
		handled, result_payload, session_doc, _payloads, pending = self._run_frontdoor(frontdoor_contract=contract)
		before, _after = self._payloads_around_assistant(session_doc)
		emissions = [payload for payload in before if payload.get("type") == "qwen_authorized_assistant_emission_contract"]

		self.assertTrue(handled)
		self.assertTrue(pending)
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "control_meta_answer")
		self.assertEqual(emissions[0]["control_meta_authority"]["authority_source"], "control_meta")
		self.assertTrue(result_payload["agent_meta"]["authorized_emission"]["emitted"])
		self._assert_no_audit_or_emission_after_answer(session_doc)

	def test_bounded_frontdoor_refusal_uses_policy_boundary_answer_type(self):
		contract = _frontdoor_contract(
			intent_class="capability_question",
			text="I cannot answer that without approved coverage.",
		)
		handled, result_payload, session_doc, _payloads, _pending = self._run_frontdoor(
			frontdoor_contract=contract,
			boundary_payload=_blocking_boundary(),
		)
		before, _after = self._payloads_around_assistant(session_doc)
		emissions = [payload for payload in before if payload.get("type") == "qwen_authorized_assistant_emission_contract"]

		self.assertTrue(handled)
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "policy_boundary_refusal")
		self.assertEqual(emissions[0]["preflight_status"], "bounded")
		self.assertTrue(result_payload["agent_meta"]["authorized_emission"]["emitted"])
		self._assert_no_audit_or_emission_after_answer(session_doc)

	def test_missing_business_authority_blocks_without_assistant_answer(self):
		contract = _frontdoor_contract(
			intent_class="governed_composite_value",
			text="This would be an ungrounded business answer.",
		)
		handled, result_payload, session_doc, payloads, _pending = self._run_frontdoor(frontdoor_contract=contract)
		emissions = [payload for payload in payloads if payload.get("type") == "qwen_authorized_assistant_emission_contract"]

		self.assertTrue(handled)
		self.assertEqual(len(emissions), 1)
		self.assertTrue(emissions[0]["blocked"])
		self.assertEqual(emissions[0]["preflight_status"], "missing_authority")
		self.assertEqual(emissions[0]["block_reason"], "final_answer_authority_incomplete")
		self.assertNotEqual(
			emissions[0]["final_answer_authority"].get("authority_source"),
			"policy_boundary",
		)
		self.assertNotEqual(
			emissions[0]["final_answer_authority"].get("policy_boundary"),
			"covered",
		)
		self.assertFalse(result_payload["agent_meta"]["authorized_emission"]["emitted"])
		self.assertNotIn("assistant", [message.get("role") for message in session_doc.get("messages", [])])
		serialized_payloads = json.dumps(payloads)
		self.assertNotIn("This would be an ungrounded business answer.", serialized_payloads)
		self.assertNotIn("qwen_frontdoor_render_result", serialized_payloads)

	def test_root_duplicate_frontdoor_is_compatibility_facade(self):
		root_text = ROOT_FRONTDOOR.read_text(encoding="utf-8", errors="ignore")

		self.assertIn("Compatibility facade", root_text)
		self.assertIn("ai_assistant_ui.qwen_chat.lanes.frontdoor_lane", root_text)
		self.assertIn("evaluate_frontdoor_lane", root_text)
		self.assertIn("handle_frontdoor_turn", root_text)
		self.assertNotIn('append_message(session_doc, "assistant"', root_text)
		self.assertNotIn("emit_authorized_assistant_answer", root_text)


if __name__ == "__main__":
	unittest.main()
