from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.authorized_emission import AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE


if "frappe" not in sys.modules:
	sys.modules["frappe"] = types.SimpleNamespace(
		local=types.SimpleNamespace(site="unit.test"),
		get_doc=lambda *_args, **_kwargs: None,
		get_traceback=lambda: "",
		log_error=lambda *_args, **_kwargs: None,
	)

from ai_assistant_ui.qwen_chat import service


PROJECT_ROOT = Path(__file__).resolve().parents[6]


class _Session:
	def __init__(self) -> None:
		self.messages: List[Dict[str, Any]] = []


def _tool_payloads(session_doc: _Session) -> List[Dict[str, Any]]:
	payloads: List[Dict[str, Any]] = []
	for row in session_doc.messages:
		if row.get("role") != "tool":
			continue
		content = row.get("content")
		payloads.append(content if isinstance(content, dict) else json.loads(str(content or "{}")))
	return payloads


def _assistant_messages(session_doc: _Session) -> List[Dict[str, Any]]:
	return [row for row in session_doc.messages if row.get("role") == "assistant"]


def _payload_types_before_first_assistant(session_doc: _Session) -> List[str]:
	types: List[str] = []
	for row in session_doc.messages:
		if row.get("role") == "assistant":
			break
		if row.get("role") == "tool":
			payload = row.get("content") if isinstance(row.get("content"), dict) else json.loads(str(row.get("content") or "{}"))
			types.append(str(payload.get("type") or ""))
	return types


class ServiceControlAuthorizedEmissionContractTests(unittest.TestCase):
	def _emit(self, *, answer_mode: str, answer_text: str = "Service control answer.", control_meta_authority=None):
		session_doc = _Session()

		def append_message(_session_doc, role, content):
			_session_doc.messages.append({"role": str(role or "").strip(), "content": content})

		def append_tool_payload(_session_doc, payload):
			_session_doc.messages.append({"role": "tool", "content": dict(payload or {})})

		with patch.object(service, "_append_message", side_effect=append_message), patch.object(
			service,
			"_append_tool_payload",
			side_effect=append_tool_payload,
		), patch.object(service, "_assistant_text_payload", side_effect=lambda text: str(text or "")):
			result = service._emit_service_control_answer(
				session_doc=session_doc,
				answer_text=answer_text,
				answer_mode=answer_mode,
				reason="service control test",
				pre_assistant_payload_values=[
					{"type": "qwen_service_control_payload", "mode": answer_mode},
					{"type": "qwen_audit_envelope", "answer_text": answer_text},
				],
				control_meta_authority=control_meta_authority,
			)
		return session_doc, result

	def test_service_control_modes_emit_after_authority_payloads(self):
		for answer_mode in [
			"service_prior_branch_clarification_restore",
			"service_compound_continue_completed",
			"service_compound_stop",
		]:
			with self.subTest(answer_mode=answer_mode):
				session_doc, result = self._emit(answer_mode=answer_mode)
				emission = next(
					payload
					for payload in _tool_payloads(session_doc)
					if payload.get("type") == AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE
				)

				self.assertTrue(result.emitted)
				self.assertFalse(result.blocked)
				self.assertEqual(result.answer_type, "control_meta_answer")
				self.assertEqual(result.control_meta_authority["answer_mode"], answer_mode)
				self.assertEqual(_assistant_messages(session_doc)[0]["content"], "Service control answer.")
				self.assertEqual(emission["answer_type"], "control_meta_answer")
				self.assertEqual(
					_payload_types_before_first_assistant(session_doc),
					["qwen_service_control_payload", "qwen_audit_envelope", AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE],
				)

	def test_missing_service_control_authority_blocks_without_payload_leak(self):
		session_doc, result = self._emit(
			answer_mode="service_compound_stop",
			answer_text="Unauthorized service control answer.",
			control_meta_authority={},
		)

		self.assertFalse(result.emitted)
		self.assertTrue(result.blocked)
		self.assertEqual(result.block_reason, "missing_control_authority_fields:authority_source,answer_mode,reason")
		self.assertEqual(_assistant_messages(session_doc), [])
		tool_payloads = _tool_payloads(session_doc)
		self.assertEqual(len(tool_payloads), 1)
		self.assertEqual(tool_payloads[0]["type"], AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)
		self.assertTrue(tool_payloads[0]["blocked"])
		serialized = json.dumps(tool_payloads)
		self.assertNotIn("Unauthorized service control answer", serialized)
		self.assertNotIn("qwen_service_control_payload", serialized)
		self.assertNotIn("qwen_audit_envelope", serialized)

	def test_ec4t2_service_branches_use_control_helper_not_direct_assistant_append(self):
		source = (
			PROJECT_ROOT
			/ "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py"
		).read_text(encoding="utf-8")
		prior_restore_window = source.split(
			"def _handle_prior_branch_restore_reopen_pending_clarification(",
			1,
		)[1].split("def _handle_prior_branch_restore_direct_route(", 1)[0]
		compound_continue_window = source.split(
			"compound_completion_answer = _compound_request_completion_answer_from_snapshot(",
			1,
		)[1].split("reasoning_rollout = _erp_business_reasoning_rollout_decision(", 1)[0]
		compound_stop_window = source.split(
			"compound_cancellation_decision_contract = _conversation_control_decision_from_compound_cancellation(",
			1,
		)[1].split("if compound_runtime_message:", 1)[0]

		for window in [prior_restore_window, compound_continue_window, compound_stop_window]:
			self.assertIn("_emit_service_control_answer(", window)
			self.assertNotIn('_append_message(session_doc, "assistant"', window)
			self.assertNotIn("_append_tool_payload_values(", window)


if __name__ == "__main__":
	unittest.main()
