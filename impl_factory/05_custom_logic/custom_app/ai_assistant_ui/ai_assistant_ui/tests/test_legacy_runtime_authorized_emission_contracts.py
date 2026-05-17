from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_followup_resolution_contract,
	build_interaction_contract,
)
from ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane import (
	QwenRuntimeClientError,
	handle_legacy_runtime_turn,
)


class _Session:
	def __init__(self):
		self.messages = []


class _ResponsePolicy:
	def to_runtime_payload(self):
		return {"mode": "read_only"}


def _tool_trace() -> list[dict]:
	return [
		{
			"tool": "erp_fac-generate_report",
			"detail_obj": {
				"report_name": "Accounts Receivable Aging",
				"filters": {
					"company": "Mingalar Mobile Distribution Co., Ltd.",
					"report_date": "2026-05-15",
				},
			},
		}
	]


class LegacyRuntimeAuthorizedEmissionContractTests(unittest.TestCase):
	def _run_legacy(self, runtime_result=None, *, runtime_error=None, trace_payload=None, artifact_payload=None):
		session_doc = _Session()
		messages = []
		tool_payloads = []
		request_id = "legacy-runtime-ec4i"

		def append_message(session_doc, role, content):
			messages.append({"role": role, "content": content})
			session_doc.messages.append({"role": role, "content": content})

		def append_tool_payload(session_doc, payload):
			clean = dict(payload)
			tool_payloads.append(clean)
			session_doc.messages.append({"role": "tool", "content": clean})

		def latest_assistant_payload(_session_doc):
			raise AssertionError("legacy runtime must not build authority from post-append latest assistant payload")

		def latest_qwen_trace_payload(_session_doc):
			return dict(
				trace_payload
				if trace_payload is not None
				else {
					"ok": True,
					"tool_trace": _tool_trace(),
					"agent_meta": {
						"engine": "qwen_runtime",
						"model": "qwen-test",
						"validation": {"status": "pass", "errors": []},
					},
					"runtime_latency_ms": 12,
				}
			)

		def latest_artifact(_session_doc):
			return dict(
				artifact_payload
				if artifact_payload is not None
				else {
					"type": "qwen_normalized_family_artifact_contract",
					"request_id": request_id,
					"family_id": "aging",
					"source_name": "Accounts Receivable Aging",
				}
			)

		def tool_trace_payload(**kwargs):
			return {"type": "qwen_tool_trace", **kwargs}

		def tool_trace_message(**kwargs):
			return {"type": "qwen_tool_trace", **kwargs}

		def safe_runtime_failure_message(exc):
			return f"Runtime unavailable: {exc}"

		patch_target = "ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane.call_qwen_runtime_chat"
		with patch(patch_target, side_effect=runtime_error) if runtime_error is not None else patch(
			patch_target,
			return_value=runtime_result,
		):
			handled, payload = handle_legacy_runtime_turn(
				session_doc=session_doc,
				request_id=request_id,
				session_id="session-legacy-runtime-ec4i",
				user_id="Administrator",
				site_name="erp.test",
				message="Show AR",
				recent_messages=[],
				response_policy_contract=_ResponsePolicy(),
				interaction_contract=build_interaction_contract(
					request_id=request_id,
					session_id="session-legacy-runtime-ec4i",
					user_id="Administrator",
					site_name="erp.test",
					raw_message="Show AR",
				),
				followup_resolution=build_followup_resolution_contract(
					request_id=request_id,
					mode="legacy_runtime",
					depends_on_grounded_turn=True,
					self_contained=False,
					latest_grounded_turn_available=False,
					reason="legacy runtime test",
				),
				execution_path=ExecutionPath(
					request_id=request_id,
					path="legacy_runtime",
					reason="legacy runtime test",
					requires_runtime=True,
					grounded_required=True,
				),
				compiled_rollout_fallback=None,
				append_message=append_message,
				append_tool_payload=append_tool_payload,
				assistant_text_payload=lambda text: {"text": str(text or "")},
				save_session=lambda *_args, **_kwargs: None,
				tool_trace_payload=tool_trace_payload,
				tool_trace_message=tool_trace_message,
				safe_runtime_failure_message=safe_runtime_failure_message,
				latest_qwen_trace_payload=latest_qwen_trace_payload,
				latest_assistant_payload=latest_assistant_payload,
				latest_normalized_family_artifact=latest_artifact,
			)
		return {
			"handled": handled,
			"payload": payload,
			"session_doc": session_doc,
			"messages": messages,
			"tool_payloads": tool_payloads,
		}

	def _assistant_texts(self, result):
		return [
			message["content"]["text"]
			for message in result["messages"]
			if message.get("role") == "assistant"
		]

	def _authorized_emissions(self, result):
		return [
			payload
			for payload in result["tool_payloads"]
			if payload.get("type") == "qwen_authorized_assistant_emission_contract"
		]

	def _audit_payloads(self, result):
		return [
			payload
			for payload in result["tool_payloads"]
			if payload.get("type") == "qwen_audit_envelope"
		]

	def test_normal_grounded_legacy_output_emits_governed_report_authority(self):
		result = self._run_legacy(
			{
				"ok": True,
				"answer_text": "Legacy governed answer",
				"tool_trace": _tool_trace(),
				"agent_meta": {"engine": "qwen_runtime", "model": "qwen-test", "validation": {"status": "pass"}},
				"error": "",
			}
		)
		emissions = self._authorized_emissions(result)
		audits = self._audit_payloads(result)

		self.assertTrue(result["handled"])
		self.assertTrue(result["payload"]["ok"])
		self.assertEqual(self._assistant_texts(result), ["Legacy governed answer"])
		self.assertEqual(result["payload"].get("answer_text", ""), "")
		self.assertEqual(len(audits), 1)
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "governed_report_answer")
		self.assertEqual(emissions[0]["preflight_status"], "passed")
		self.assertEqual(emissions[0]["final_answer_authority"]["authority_source"], "governed_erp_report")
		self.assertEqual(emissions[0]["final_answer_authority"]["selected_report_family"], "aging")
		self.assertTrue(result["payload"]["agent_meta"]["authorized_emission"]["emitted"])

	def test_grounded_validation_failure_emits_policy_boundary(self):
		result = self._run_legacy(
			{
				"ok": False,
				"answer_text": "",
				"tool_trace": _tool_trace(),
				"agent_meta": {
					"engine": "qwen_runtime",
					"model": "qwen-test",
					"validation": {"status": "fail", "errors": ["unsafe prediction"]},
				},
				"error": "Grounded read validation failed.",
			},
			trace_payload={
				"ok": False,
				"tool_trace": _tool_trace(),
				"agent_meta": {
					"engine": "local_grounded_boundary",
					"model": "qwen-test",
					"validation": {"status": "fail", "errors": ["unsafe prediction"]},
				},
				"runtime_latency_ms": 12,
			},
		)
		emissions = self._authorized_emissions(result)

		self.assertTrue(result["handled"])
		self.assertTrue(result["payload"]["ok"])
		self.assertEqual(len(self._assistant_texts(result)), 1)
		self.assertEqual(result["payload"].get("answer_text", ""), "")
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "policy_boundary_refusal")
		self.assertEqual(emissions[0]["preflight_status"], "bounded")
		self.assertEqual(emissions[0]["final_answer_authority"]["authority_source"], "policy_boundary")
		self.assertTrue(result["payload"]["agent_meta"]["authorized_emission"]["emitted"])

	def test_runtime_client_error_emits_explicit_error_fallback_authority(self):
		result = self._run_legacy(runtime_error=QwenRuntimeClientError("timeout"))
		emissions = self._authorized_emissions(result)

		self.assertTrue(result["handled"])
		self.assertFalse(result["payload"]["ok"])
		self.assertEqual(self._assistant_texts(result), ["Runtime unavailable: timeout"])
		self.assertEqual(result["payload"].get("answer_text", ""), "")
		self.assertEqual(len(emissions), 1)
		self.assertEqual(emissions[0]["answer_type"], "error_fallback_answer")
		self.assertEqual(emissions[0]["preflight_status"], "passed")
		self.assertEqual(emissions[0]["control_meta_authority"]["authority_source"], "error_fallback")
		self.assertTrue(result["payload"]["agent_meta"]["authorized_emission"]["emitted"])

	def test_missing_governed_authority_blocks_without_assistant_or_payload_answer_text(self):
		result = self._run_legacy(
			{
				"ok": True,
				"answer_text": "Ungrounded legacy business answer",
				"tool_trace": [],
				"agent_meta": {"engine": "qwen_runtime", "model": "qwen-test"},
				"error": "",
			},
			trace_payload={
				"ok": True,
				"tool_trace": [],
				"agent_meta": {"engine": "qwen_runtime", "model": "qwen-test"},
				"runtime_latency_ms": 12,
			},
			artifact_payload={},
		)
		emissions = self._authorized_emissions(result)

		self.assertTrue(result["handled"])
		self.assertFalse(result["payload"]["ok"])
		self.assertEqual(self._assistant_texts(result), [])
		self.assertEqual(result["payload"].get("answer_text", ""), "")
		self.assertEqual(len(emissions), 1)
		self.assertTrue(emissions[0]["blocked"])
		self.assertEqual(emissions[0]["answer_type"], "governed_report_answer")
		self.assertEqual(emissions[0]["preflight_status"], "missing_authority")
		self.assertEqual(emissions[0]["block_reason"], "final_answer_authority_incomplete")
		self.assertFalse(result["payload"]["agent_meta"]["authorized_emission"]["emitted"])
		serialized_payloads = json.dumps(result["tool_payloads"])
		self.assertNotIn("Ungrounded legacy business answer", serialized_payloads)
		self.assertNotIn("qwen_tool_trace", serialized_payloads)
		self.assertNotIn("qwen_grounded_turn_context", serialized_payloads)


if __name__ == "__main__":
	unittest.main()
