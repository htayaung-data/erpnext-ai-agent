from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.authorized_emission import AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE
from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_followup_resolution_contract,
	build_interaction_contract,
)


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


def _valid_boundary_payload() -> Dict[str, Any]:
	return {
		"type": "qwen_knowledge_boundary_contract",
		"request_id": "service-boundary-ec4s2",
		"session_id": "session-service-boundary-ec4s2",
		"final_lane": "valid_erp_domain_uncovered",
		"knowledge_coverage_state": "valid_erp_domain_uncovered",
		"user_response_mode": "coverage_gap_explanation",
		"safe_next_action": "respond_uncovered_erp_domain",
		"grounding_required": True,
		"grounding_available": False,
	}


def _contracts():
	request_id = "service-boundary-ec4s2"
	session_id = "session-service-boundary-ec4s2"
	return {
		"interaction_contract": build_interaction_contract(
			request_id=request_id,
			session_id=session_id,
			user_id="Administrator",
			site_name="erpai_prj1",
			raw_message="show hr headcount",
		),
		"followup_resolution": build_followup_resolution_contract(
			request_id=request_id,
			mode="grounded_follow_up",
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="service policy boundary test",
		),
		"execution_path": ExecutionPath(
			request_id=request_id,
			path="known_unsupported_erp_domain",
			reason="service policy boundary test",
			requires_runtime=False,
			grounded_required=True,
		),
	}


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


class ServicePolicyBoundaryAuthorizedEmissionContractTests(unittest.TestCase):
	def _emit(self, *, boundary_payload=None, answer_text="Service boundary answer."):
		session_doc = _Session()
		contracts = _contracts()

		def append_message(_session_doc, role, content):
			_session_doc.messages.append({"role": str(role or "").strip(), "content": content})

		def append_tool_payload(_session_doc, payload):
			_session_doc.messages.append({"role": "tool", "content": dict(payload or {})})

		with patch.object(service, "_append_message", side_effect=append_message), patch.object(
			service,
			"_append_tool_payload",
			side_effect=append_tool_payload,
		), patch.object(service, "_assistant_text_payload", side_effect=lambda text: str(text or "")):
			result = service._emit_service_policy_boundary_answer(
				session_doc=session_doc,
				request_id="service-boundary-ec4s2",
				session_id="session-service-boundary-ec4s2",
				mode="known_unsupported_erp_domain",
				engine="local_governed_scope_guard",
				answer_text=answer_text,
				boundary_payload=boundary_payload if boundary_payload is not None else _valid_boundary_payload(),
				latency_ms=7,
				**contracts,
			)
		return session_doc, result

	def test_service_policy_boundary_emits_after_authority_payloads(self):
		session_doc, result = self._emit()

		self.assertTrue(result.emitted)
		self.assertEqual(result.answer_type, "policy_boundary_refusal")
		self.assertEqual(result.preflight_status, "bounded")
		self.assertEqual(result.final_answer_authority["authority_source"], "policy_boundary")
		self.assertEqual(_assistant_messages(session_doc)[0]["content"], "Service boundary answer.")
		types = _payload_types_before_first_assistant(session_doc)
		self.assertEqual(types[0], "qwen_knowledge_boundary_contract")
		self.assertIn("qwen_execution_path", types)
		self.assertIn("qwen_audit_envelope", types)
		self.assertEqual(types[-1], AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)

	def test_missing_service_policy_boundary_authority_blocks_without_payload_leak(self):
		session_doc, result = self._emit(
			boundary_payload={},
			answer_text="Unauthorized service boundary answer.",
		)

		self.assertFalse(result.emitted)
		self.assertTrue(result.blocked)
		self.assertEqual(result.block_reason, "final_answer_authority_incomplete")
		self.assertEqual(_assistant_messages(session_doc), [])
		tool_payloads = _tool_payloads(session_doc)
		self.assertEqual(len(tool_payloads), 1)
		self.assertEqual(tool_payloads[0]["type"], AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)
		self.assertTrue(tool_payloads[0]["blocked"])
		serialized = json.dumps(tool_payloads)
		self.assertNotIn("Unauthorized service boundary answer", serialized)
		self.assertNotIn("qwen_knowledge_boundary_contract", serialized)

	def test_service_boundary_branches_use_authorized_helper_not_direct_assistant_append(self):
		source = (
			PROJECT_ROOT
			/ "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py"
		).read_text(encoding="utf-8")
		out_of_scope_window = source.split(
			"if governed_scope_decision_is_out_of_scope(scope_decision_contract) and entity_drilldown is None:",
			1,
		)[1].split("skip_artifact_boundary =", 1)[0]
		local_boundary_window = source.split("if not local_transform and local_boundary_payload:", 1)[1].split(
			"if local_transform:",
			1,
		)[0]

		for window in [out_of_scope_window, local_boundary_window]:
			self.assertIn("_emit_service_policy_boundary_answer(", window)
			self.assertNotIn('_append_message(session_doc, "assistant"', window)
			self.assertNotIn("build_audit_envelope(", window)


if __name__ == "__main__":
	unittest.main()
