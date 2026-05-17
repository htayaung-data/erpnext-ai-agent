from __future__ import annotations

import json
import unittest
from typing import Any, Dict, List
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.authorized_emission import AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE
from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_followup_resolution_contract,
	build_interaction_contract,
)
from ai_assistant_ui.qwen_chat.lanes.runtime_gate_lane import handle_runtime_gate_turn


class _Session:
	def __init__(self) -> None:
		self.messages: List[Dict[str, Any]] = []
		self.saved = False


class _Payload:
	def __init__(self, payload: Dict[str, Any]) -> None:
		self.payload = dict(payload)

	def __getattr__(self, name: str) -> Any:
		try:
			return self.payload[name]
		except KeyError as exc:
			raise AttributeError(name) from exc

	def to_payload(self) -> Dict[str, Any]:
		return dict(self.payload)


def _append_message(session_doc, role, content) -> None:
	session_doc.messages.append({"role": str(role or "").strip(), "content": content})


def _append_tool_payload(session_doc, payload) -> None:
	session_doc.messages.append({"role": "tool", "content": dict(payload or {})})


def _tool_payloads(session_doc) -> List[Dict[str, Any]]:
	payloads: List[Dict[str, Any]] = []
	for row in session_doc.messages:
		if row.get("role") != "tool":
			continue
		content = row.get("content")
		if isinstance(content, dict):
			payloads.append(dict(content))
		else:
			payloads.append(json.loads(str(content or "{}")))
	return payloads


def _assistant_messages(session_doc) -> List[Dict[str, Any]]:
	return [row for row in session_doc.messages if row.get("role") == "assistant"]


def _tool_payload_types_before_first_assistant(session_doc) -> List[str]:
	types: List[str] = []
	for row in session_doc.messages:
		if row.get("role") == "assistant":
			break
		if row.get("role") == "tool":
			content = row.get("content")
			payload = content if isinstance(content, dict) else json.loads(str(content or "{}"))
			types.append(str(payload.get("type") or ""))
	return types


def _fail_if_called(*_args, **_kwargs):
	raise AssertionError("runtime gate must stage boundary payloads through the authorized helper")


def _common_kwargs(session_doc):
	request_id = "runtime-gate-ec4s1"
	session_id = "session-runtime-gate-ec4s1"
	return {
		"session_doc": session_doc,
		"request_id": request_id,
		"session_id": session_id,
		"user_id": "Administrator",
		"site_name": "erpai_prj1",
		"message": "show employee headcount by department",
		"raw_message": "show employee headcount by department",
		"latest_grounded_turn_available": True,
		"latest_grounded_turn": {
			"grounded": True,
			"source_kind": "report",
			"source_name": "Sales Analytics",
		},
		"followup_resolution": build_followup_resolution_contract(
			request_id=request_id,
			mode="grounded_follow_up",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="runtime gate boundary test",
		),
		"execution_path": ExecutionPath(
			request_id=request_id,
			path="artifact_lane",
			reason="runtime gate boundary test",
			requires_runtime=False,
			grounded_required=True,
		),
		"interaction_contract": build_interaction_contract(
			request_id=request_id,
			session_id=session_id,
			user_id="Administrator",
			site_name="erpai_prj1",
			raw_message="show employee headcount by department",
		),
		"frontdoor_contract": _Payload({"type": "frontdoor_contract"}),
		"clarification_response_contract": None,
		"scope_decision_contract": _Payload(
			{
				"type": "governed_scope_decision",
				"governed_scope_status": "out_of_scope_but_valid_erp_domain",
				"requested_domains": ["employee"],
				"context_domains": ["sales"],
				"primary_domain": "hr",
				"reason": "HR is a valid ERP domain but not covered.",
				"out_of_scope": True,
			}
		),
		"compiled_rollout": {"enabled": False},
		"append_tool_payload": _append_tool_payload,
		"append_message": _append_message,
		"append_knowledge_boundary_contract": _fail_if_called,
		"append_knowledge_boundary_observability": _fail_if_called,
		"append_compiled_attempt_artifacts": _fail_if_called,
		"compiled_rollout_fallback_eligible": lambda *_args, **_kwargs: False,
		"compiled_rollout_fallback_reason": lambda *_args, **_kwargs: "",
		"compiled_rollout_fallback_payload": lambda **_kwargs: {},
		"handle_compiled_first_turn_result": lambda **_kwargs: (True, {}),
		"out_of_scope_answer": lambda _message, _decision: "I don't have governed HR or headcount coverage yet.",
		"assistant_text_payload": lambda text: str(text or ""),
		"save_session": lambda session, **_kwargs: setattr(session, "saved", True),
	}


class RuntimeGateAuthorizedEmissionContractTests(unittest.TestCase):
	def test_policy_boundary_emits_through_authorized_helper_before_assistant(self):
		session_doc = _Session()
		handled, payload, compiled_fallback = handle_runtime_gate_turn(**_common_kwargs(session_doc))

		self.assertTrue(handled)
		self.assertIsNone(compiled_fallback)
		self.assertTrue(payload["ok"])
		self.assertTrue(session_doc.saved)
		self.assertEqual(len(_assistant_messages(session_doc)), 1)
		self.assertIn("headcount coverage", _assistant_messages(session_doc)[0]["content"])
		types = _tool_payload_types_before_first_assistant(session_doc)
		self.assertEqual(types[0], "qwen_knowledge_boundary_contract")
		self.assertIn("qwen_audit_envelope", types)
		self.assertEqual(types[-1], AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)
		emission = _tool_payloads(session_doc)[-1]
		self.assertTrue(emission["emitted"])
		self.assertEqual(emission["answer_type"], "policy_boundary_refusal")
		self.assertEqual(emission["preflight_status"], "bounded")
		self.assertEqual(emission["final_answer_authority"]["authority_source"], "policy_boundary")
		self.assertEqual(payload["agent_meta"]["authorized_emission"]["emitted"], True)

	def test_missing_boundary_authority_blocks_without_answer_or_payload_leak(self):
		session_doc = _Session()
		with patch(
			"ai_assistant_ui.qwen_chat.lanes.runtime_gate_lane.evaluate_knowledge_boundary",
			return_value={},
		):
			handled, payload, compiled_fallback = handle_runtime_gate_turn(**_common_kwargs(session_doc))

		self.assertTrue(handled)
		self.assertIsNone(compiled_fallback)
		self.assertFalse(payload["ok"])
		self.assertEqual(payload["agent_meta"]["authorized_emission"]["emitted"], False)
		self.assertEqual(_assistant_messages(session_doc), [])
		tool_payloads = _tool_payloads(session_doc)
		self.assertEqual(len(tool_payloads), 1)
		self.assertEqual(tool_payloads[0]["type"], AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)
		self.assertTrue(tool_payloads[0]["blocked"])
		self.assertEqual(tool_payloads[0]["block_reason"], "final_answer_authority_incomplete")
		serialized = json.dumps(tool_payloads)
		self.assertNotIn("headcount coverage", serialized)
		self.assertNotIn("qwen_knowledge_boundary_contract", serialized)


if __name__ == "__main__":
	unittest.main()
