from __future__ import annotations

import json
import sys
import types
import unittest
from types import SimpleNamespace


def _fake_get_all(doctype, *args, **kwargs):
	if doctype == "Company":
		if kwargs.get("pluck") == "name":
			return ["Enterprise Co"]
		return [{"name": "Enterprise Co"}]
	if doctype == "Fiscal Year":
		return [
			{"name": "FY-2025", "year_start_date": "2024-04-01", "year_end_date": "2025-03-31"},
			{"name": "FY-2026", "year_start_date": "2025-04-01", "year_end_date": "2026-03-31"},
			{"name": "FY-2027", "year_start_date": "2026-04-01", "year_end_date": "2027-03-31"},
		]
	if doctype == "Period Closing Voucher":
		return [
			{
				"name": "PCV-2025-0001",
				"company": "Enterprise Co",
				"fiscal_year": "FY-2025",
				"period_start_date": "2024-04-01",
				"period_end_date": "2025-03-31",
				"transaction_date": "2025-03-31",
				"gle_processing_status": "Completed",
			}
		]
	return []


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = _fake_get_all
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


from ai_assistant_ui.qwen_chat.compiled_support import handle_compiled_first_turn_result
from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_followup_resolution_contract,
	build_interaction_contract,
)


class _DummyContract:
	def __init__(self, payload):
		self._payload = dict(payload)

	def to_payload(self):
		return dict(self._payload)


class _GroundedTurnContext:
	grounded = True

	def to_payload(self):
		return {
			"type": "qwen_grounded_turn_context",
			"request_id": "compiled-auth",
			"trace_request_id": "compiled-auth-trace",
			"grounded": True,
			"source_kind": "report",
			"source_name": "ranking_analytics",
			"artifact_family_id": "ranking_analytics",
			"artifact_type": "normalized_family_artifact",
		}


def _tool_message(payload):
	return {"role": "tool", "content": json.dumps(payload)}


def _base_result(*, ok=True, semantic_status="pass", family_status="pass", include_artifact=True):
	result = {
		"runtime_payload": {
			"ok": ok,
			"answer_text": "Compiled governed answer",
			"tool_trace": [
				{
					"tool": "erp_fac-generate_report",
					"detail_obj": {"report_name": "ranking_analytics", "filters": {"company": "Mingalar"}},
				}
			],
			"agent_meta": {"engine": "compiled_runtime"},
		},
		"family_validation": {"status": family_status},
		"semantic_intent_validation": {"status": semantic_status},
		"phase4_latency_breakdown": {},
		"compiled_execution_audit": {"type": "qwen_compiled_execution_audit", "request_id": "compiled-auth"},
		"pipeline": {},
	}
	if include_artifact:
		result["normalized_family_artifact"] = {
			"type": "qwen_normalized_family_artifact_contract",
			"artifact_id": "compiled-artifact-1",
			"family_id": "ranking_analytics",
			"artifact_type": "normalized_family_artifact",
		}
	return result


def _allowed_boundary():
	return {
		"type": "qwen_knowledge_boundary_contract",
		"final_lane": "artifact_lane",
		"knowledge_coverage_state": "covered",
		"user_response_mode": "normal_answer",
		"safe_next_action": "allow_current_lane",
		"allowed_to_answer": True,
	}


def _blocking_boundary():
	return {
		"type": "qwen_knowledge_boundary_contract",
		"final_lane": "artifact_lane",
		"knowledge_coverage_state": "valid_erp_domain_uncovered",
		"user_response_mode": "safe_refusal",
		"safe_next_action": "respond_unsupported",
		"allowed_to_answer": False,
	}


class CompiledSupportAuthorizedEmissionContractTests(unittest.TestCase):
	def _run_compiled(
		self,
		*,
		result=None,
		decision_message=None,
		grounded_turn_context=None,
		boundary_payload=None,
	):
		session_doc = {"messages": []}
		payloads = []
		pending_signals = []
		cleared_pending = []
		grounding_observations = []

		def append_message(session_doc, role, content):
			session_doc.setdefault("messages", []).append({"role": role, "content": content})

		def append_tool_payload(session_doc, payload):
			payloads.append(dict(payload))
			session_doc.setdefault("messages", []).append(_tool_message(payload))

		def append_boundary(session_doc, **kwargs):
			payload = dict(boundary_payload or _allowed_boundary())
			append_tool_payload(session_doc, payload)
			return payload

		def build_grounded_turn_context(**kwargs):
			assistant_count = len([
				message for message in session_doc.get("messages", []) if message.get("role") == "assistant"
			])
			grounding_observations.append(
				{
					"assistant_count_at_grounding": assistant_count,
					"assistant_payload": dict(kwargs.get("assistant_payload") or {}),
				}
			)
			return grounded_turn_context

		ok, output = handle_compiled_first_turn_result(
			session_doc=session_doc,
			request_id="compiled-auth",
			interaction_contract=build_interaction_contract(
				request_id="compiled-auth",
				session_id="session-compiled-auth",
				user_id="Administrator",
				site_name="erp.test",
				raw_message="compiled request",
			),
			followup_resolution=build_followup_resolution_contract(
				request_id="compiled-auth",
				mode="new_query",
				requested_modes=[],
				target_dimension="",
				target_limit=0,
				sort_direction="",
				target_metric="",
				requested_columns=[],
				requested_time_scope="",
				target_capability_id="",
				target_report="",
				depends_on_grounded_turn=False,
				self_contained=True,
				latest_grounded_turn_available=False,
				reason="fresh query",
			),
			execution_path=ExecutionPath(
				request_id="compiled-auth",
				path="runtime",
				reason="compiled runtime",
				requires_runtime=True,
				grounded_required=False,
			),
			result=result if result is not None else _base_result(),
			governed_scope_contract=None,
			front_door_contract=None,
			clarification_response_contract=None,
			pre_result_tool_payloads=[],
			append_compiled_attempt_artifacts=lambda *_args, **_kwargs: None,
			compiled_decision_message=decision_message
			or (lambda **_kwargs: ("Compiled governed answer", {})),
			compiled_clarification_reason_contract=lambda **_kwargs: _DummyContract(
				{"type": "qwen_clarification_reason_contract"}
			),
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			assistant_text_payload=lambda text: json.dumps({"type": "text", "text": str(text or "")}),
			tool_trace_message=lambda **kwargs: json.dumps(
				{
					"type": "qwen_runtime_trace",
					"request_id": kwargs.get("request_id"),
					"ok": kwargs.get("ok"),
					"tool_trace": kwargs.get("tool_trace") or [],
					"agent_meta": kwargs.get("agent_meta") or {},
					"error": kwargs.get("error") or "",
				}
			),
			latest_qwen_trace_payload=lambda _doc: {
				"type": "qwen_runtime_trace",
				"tool_trace": (result or _base_result()).get("runtime_payload", {}).get("tool_trace", []),
				"agent_meta": (result or _base_result()).get("runtime_payload", {}).get("agent_meta", {}),
			},
			latest_assistant_payload=lambda _doc: {"type": "text", "text": "SHOULD_NOT_BE_USED"},
			append_knowledge_boundary_contract=append_boundary,
			knowledge_boundary_event_level=lambda _payload: "info",
			append_knowledge_boundary_observability=lambda *_args, **_kwargs: None,
			build_grounded_turn_context=build_grounded_turn_context,
			build_audit_envelope=lambda **_kwargs: _DummyContract({"type": "qwen_legacy_audit_should_not_emit"}),
			save_session=lambda *_args, **_kwargs: None,
			store_pending_clarification_signal=lambda _doc, payload: pending_signals.append(dict(payload)),
			clear_pending_clarification_signal=lambda *_args, **_kwargs: cleared_pending.append(True),
		)
		return {
			"ok": ok,
			"output": output,
			"session_doc": session_doc,
			"payloads": payloads,
			"pending_signals": pending_signals,
			"cleared_pending": cleared_pending,
			"grounding_observations": grounding_observations,
		}

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

	def test_governed_compiled_result_emits_authorized_audit_before_assistant(self):
		result = self._run_compiled(grounded_turn_context=_GroundedTurnContext())
		before, _after = self._payloads_around_assistant(result["session_doc"])
		audits = [payload for payload in before if payload.get("type") == "qwen_audit_envelope"]
		emissions = [payload for payload in before if payload.get("type") == "qwen_authorized_assistant_emission_contract"]

		self.assertTrue(result["ok"])
		self.assertTrue(result["output"]["ok"])
		self.assertEqual(len(audits), 1)
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "governed_report_answer")
		self.assertEqual(emissions[0]["preflight_status"], "passed")
		self.assertEqual(emissions[0]["final_answer_authority"]["selected_report_family"], "ranking_analytics")
		self.assertEqual(result["grounding_observations"][0]["assistant_count_at_grounding"], 0)
		self.assertNotEqual(result["grounding_observations"][0]["assistant_payload"].get("text"), "SHOULD_NOT_BE_USED")
		self._assert_no_audit_or_emission_after_answer(result["session_doc"])

	def test_compiled_clarification_emits_control_and_stores_pending_signal(self):
		result = self._run_compiled(
			result=_base_result(ok=False, semantic_status="not_run", family_status="not_run", include_artifact=False),
			decision_message=lambda **_kwargs: (
				"Which report should I run?",
				{
					"type": "qwen_clarification_signal_contract",
					"request_id": "compiled-auth",
					"user_question": "Which report should I run?",
				},
			),
			grounded_turn_context=None,
		)
		before, _after = self._payloads_around_assistant(result["session_doc"])
		emissions = [payload for payload in before if payload.get("type") == "qwen_authorized_assistant_emission_contract"]

		self.assertTrue(result["ok"])
		self.assertTrue(result["output"]["ok"])
		self.assertEqual(len(result["pending_signals"]), 1)
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "control_meta_answer")
		self.assertEqual(emissions[0]["preflight_status"], "passed")
		self.assertEqual(emissions[0]["control_meta_authority"]["authority_source"], "control_meta")
		self._assert_no_audit_or_emission_after_answer(result["session_doc"])

	def test_missing_governed_business_authority_blocks_without_assistant_answer(self):
		result = self._run_compiled(
			result=_base_result(ok=True, semantic_status="pass", family_status="pass", include_artifact=False),
			grounded_turn_context=None,
		)
		emissions = [
			payload
			for payload in result["payloads"]
			if payload.get("type") == "qwen_authorized_assistant_emission_contract"
		]

		self.assertTrue(result["ok"])
		self.assertFalse(result["output"]["ok"])
		self.assertEqual(len(emissions), 1)
		self.assertTrue(emissions[0]["blocked"])
		self.assertEqual(emissions[0]["answer_type"], "governed_report_answer")
		self.assertEqual(emissions[0]["preflight_status"], "missing_authority")
		self.assertEqual(emissions[0]["block_reason"], "final_answer_authority_incomplete")
		self.assertFalse([message for message in result["session_doc"].get("messages", []) if message.get("role") == "assistant"])
		serialized_payloads = json.dumps(result["payloads"])
		self.assertNotIn("Compiled governed answer", serialized_payloads)
		self.assertNotIn("qwen_runtime_trace", serialized_payloads)
		self.assertNotIn("qwen_grounded_turn_context", serialized_payloads)

	def test_policy_boundary_refusal_emits_bounded_answer(self):
		result = self._run_compiled(
			result=_base_result(ok=False, semantic_status="not_run", family_status="not_run", include_artifact=False),
			decision_message=lambda **_kwargs: ("I cannot answer that with approved ERP evidence.", {}),
			grounded_turn_context=None,
			boundary_payload=_blocking_boundary(),
		)
		before, _after = self._payloads_around_assistant(result["session_doc"])
		emissions = [payload for payload in before if payload.get("type") == "qwen_authorized_assistant_emission_contract"]

		self.assertTrue(result["ok"])
		self.assertTrue(result["output"]["ok"])
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "policy_boundary_refusal")
		self.assertEqual(emissions[0]["preflight_status"], "bounded")
		self.assertTrue(emissions[0]["emitted"])
		self._assert_no_audit_or_emission_after_answer(result["session_doc"])


if __name__ == "__main__":
	unittest.main()
