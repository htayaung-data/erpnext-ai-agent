from __future__ import annotations

import json
import unittest
from dataclasses import dataclass
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.authorized_emission import (
	AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE,
)
from ai_assistant_ui.qwen_chat.contracts import (
	build_followup_resolution_contract,
	build_interaction_contract,
)
from ai_assistant_ui.qwen_chat.lanes.artifact_boundary_lane import handle_artifact_boundary_turn


class FakeSessionDoc:
	def __init__(self) -> None:
		self.messages: List[Dict[str, Any]] = []
		self.saved = False
		self.pending_signal: Dict[str, Any] = {}
		self.pending_cleared = False

	def append(self, fieldname: str, value: Dict[str, Any]) -> None:
		if str(fieldname or "").strip() == "messages":
			self.messages.append(value)


@dataclass(frozen=True)
class FakeContract:
	payload: Dict[str, Any]

	def to_payload(self) -> Dict[str, Any]:
		return dict(self.payload)


@dataclass(frozen=True)
class FakeCompatibility:
	compatible: bool
	reason: str = "Requested enrichment is not supported by the current artifact."


def _append_message(session_doc, role, content) -> None:
	session_doc.append("messages", {"role": str(role or "").strip(), "content": content})


def _append_tool_payload(session_doc, payload) -> None:
	session_doc.append("messages", {"role": "tool", "content": json.dumps(payload)})


def _assistant_text_payload(text: str) -> str:
	return str(text or "")


def _save_session(session_doc, *, ignore_permissions: bool = False) -> None:
	session_doc.saved = True


def _store_pending(session_doc, payload) -> None:
	session_doc.pending_signal = dict(payload or {})


def _clear_pending(session_doc) -> None:
	session_doc.pending_cleared = True


def _tool_payloads(session_doc) -> List[Dict[str, Any]]:
	payloads: List[Dict[str, Any]] = []
	for row in session_doc.messages:
		if row.get("role") != "tool":
			continue
		content = row.get("content")
		payload = content if isinstance(content, dict) else json.loads(str(content or "{}"))
		payloads.append(payload)
	return payloads


def _assistant_messages(session_doc) -> List[Dict[str, Any]]:
	return [row for row in session_doc.messages if row.get("role") == "assistant"]


def _payload_types_before_first_assistant(session_doc) -> List[str]:
	types: List[str] = []
	for row in session_doc.messages:
		if row.get("role") == "assistant":
			break
		if row.get("role") == "tool":
			payload = json.loads(str(row.get("content") or "{}"))
			types.append(str(payload.get("type") or ""))
	return types


def _append_knowledge_boundary_contract(session_doc, **kwargs) -> Dict[str, Any]:
	payload = {
		"type": "qwen_knowledge_boundary_contract",
		"request_id": kwargs.get("request_id"),
		"session_id": kwargs.get("session_id"),
		"proposed_lane": kwargs.get("proposed_lane") or "artifact_lane",
		"final_lane": "valid_erp_domain_uncovered",
		"knowledge_coverage_state": "valid_erp_domain_uncovered",
		"user_response_mode": "safe_refusal",
		"safe_next_action": "respond_uncovered_erp_domain",
		"allowed_to_answer": False,
	}
	_append_tool_payload(session_doc, payload)
	return payload


def _append_grounded_evidence_recovery_contract(session_doc, **kwargs) -> Dict[str, Any]:
	payload = {
		"type": "qwen_artifact_enrichment_recovery_contract",
		"request_id": kwargs.get("request_id"),
		"session_id": kwargs.get("session_id"),
		"recovery_reason": kwargs.get("reason"),
		"artifact_id": (kwargs.get("artifact_payload") or {}).get("request_id"),
	}
	_append_tool_payload(session_doc, payload)
	return payload


def _append_enrichment_recovery_contract(session_doc, **kwargs) -> Dict[str, Any]:
	payload = {
		"type": "qwen_artifact_enrichment_recovery_contract",
		"request_id": kwargs.get("request_id"),
		"session_id": kwargs.get("session_id"),
		"recovery_reason": getattr(kwargs.get("compatibility_contract"), "reason", ""),
	}
	_append_tool_payload(session_doc, payload)
	return payload


def _append_artifact_boundary_observability(session_doc, **kwargs) -> None:
	_append_tool_payload(
		session_doc,
		{
			"type": "qwen_artifact_boundary_observability",
			"request_id": kwargs.get("request_id"),
			"boundary_name": kwargs.get("boundary_name"),
			"recovery_payload": kwargs.get("recovery_payload") or {},
		},
	)


def _latest_tool_payload_by_type(payloads, payload_type):
	for payload in reversed(list(payloads or [])):
		if payload.get("type") == payload_type:
			return payload
	return {}


def _common_kwargs(session_doc, *, evidence_response=None, evidence_boundary_answer="", compatibility=None):
	return {
		"session_doc": session_doc,
		"request_id": "req-artifact-boundary",
		"session_id": "session-artifact-boundary",
		"message": "Tell me more about this artifact",
		"interaction_contract": build_interaction_contract(
			request_id="req-artifact-boundary",
			session_id="session-artifact-boundary",
			user_id="unit@example.com",
			site_name="erpai_prj1",
			raw_message="Tell me more about this artifact",
		),
		"followup_resolution": build_followup_resolution_contract(
			request_id="req-artifact-boundary",
			mode="grounded_evidence_answer",
			requested_modes=["grounded_evidence_answer"],
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="artifact boundary contract test",
		),
		"response_policy_contract": FakeContract({"type": "response_policy"}),
		"frontdoor_contract": FakeContract({"type": "frontdoor_contract"}),
		"scope_decision_contract": FakeContract({"type": "scope_decision_contract"}),
		"latest_family_artifact": {
			"type": "qwen_normalized_family_artifact_contract",
			"request_id": "artifact-1",
			"family_id": "aging",
		},
		"latest_grounded_turn": {
			"type": "qwen_grounded_turn_context",
			"grounded": True,
			"source_kind": "report",
			"source_name": "Accounts Receivable Aging",
			"artifact_family_id": "aging",
			"trace_request_id": "trace-1",
		},
		"enrichment_compatibility_contract": compatibility,
		"precomputed_evidence_response": evidence_response or {},
		"precomputed_evidence_answer": "",
		"grounded_artifact_direct_evidence_response": lambda **kwargs: {},
		"grounded_artifact_direct_evidence_answer": lambda **kwargs: "",
		"precomputed_evidence_boundary_answer": evidence_boundary_answer,
		"grounded_artifact_evidence_boundary_answer": lambda **kwargs: "",
		"artifact_enrichment_boundary_answer": lambda **kwargs: "Enrichment boundary answer",
		"append_grounded_evidence_recovery_contract": _append_grounded_evidence_recovery_contract,
		"append_enrichment_recovery_contract": _append_enrichment_recovery_contract,
		"session_tool_payloads": _tool_payloads,
		"latest_tool_payload_by_type": _latest_tool_payload_by_type,
		"append_artifact_boundary_observability": _append_artifact_boundary_observability,
		"append_knowledge_boundary_contract": _append_knowledge_boundary_contract,
		"append_tool_payload": _append_tool_payload,
		"append_message": _append_message,
		"assistant_text_payload": _assistant_text_payload,
		"store_pending_clarification_signal": _store_pending,
		"save_session": _save_session,
		"clear_pending_clarification_signal": _clear_pending,
	}


class ArtifactBoundaryAuthorizedEmissionContractTests(unittest.TestCase):
	def test_governed_artifact_evidence_emits_after_authority_payloads(self):
		session_doc = FakeSessionDoc()
		handled, payload = handle_artifact_boundary_turn(
			**_common_kwargs(
				session_doc,
				evidence_response={
					"answer_text": "Approved artifact evidence answer.",
					"narrative_contract_payload": {
						"type": "qwen_artifact_narrative_contract",
						"narrative_engine": "local_grounded_evidence",
					},
					"evidence_request_contract_payload": {"type": "qwen_evidence_request_contract"},
					"selected_entity_activation_payload": {"type": "qwen_selected_entity_activation_contract"},
				},
			)
		)

		self.assertTrue(handled)
		self.assertTrue(payload["ok"])
		self.assertEqual(_assistant_messages(session_doc)[0]["content"], "Approved artifact evidence answer.")
		self.assertEqual(
			_payload_types_before_first_assistant(session_doc),
			[
				"qwen_execution_path",
				"qwen_evidence_request_contract",
				"qwen_artifact_narrative_contract",
				"qwen_selected_entity_activation_contract",
				"qwen_audit_envelope",
				AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE,
			],
		)
		emission = payload["agent_meta"]["authorized_emission"]
		self.assertTrue(emission["emitted"])
		self.assertEqual(emission["answer_type"], "governed_report_answer")
		self.assertEqual(emission["preflight_status"], "passed")

	def test_missing_artifact_evidence_authority_blocks_without_answer_or_payload_leak(self):
		session_doc = FakeSessionDoc()
		kwargs = _common_kwargs(
			session_doc,
			evidence_response={
				"answer_text": "Unauthorized artifact evidence answer.",
				"narrative_contract_payload": {
					"type": "qwen_artifact_narrative_contract",
					"summary": "Unauthorized artifact evidence answer.",
				},
				"evidence_request_contract_payload": {
					"type": "qwen_evidence_request_contract",
					"detail": "Unauthorized artifact evidence answer.",
				},
			},
		)
		kwargs["latest_family_artifact"] = {}
		kwargs["latest_grounded_turn"] = {}

		handled, payload = handle_artifact_boundary_turn(**kwargs)
		serialized_messages = json.dumps(session_doc.messages)

		self.assertFalse(handled)
		self.assertFalse(payload["ok"])
		self.assertEqual(_assistant_messages(session_doc), [])
		self.assertEqual(len(_tool_payloads(session_doc)), 1)
		self.assertEqual(_tool_payloads(session_doc)[0]["type"], AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)
		self.assertTrue(_tool_payloads(session_doc)[0]["blocked"])
		self.assertNotIn("Unauthorized artifact evidence answer.", serialized_messages)
		self.assertNotIn("answer_text", payload)

	def test_grounded_evidence_boundary_emits_as_bounded_policy_refusal(self):
		session_doc = FakeSessionDoc()
		handled, payload = handle_artifact_boundary_turn(
			**_common_kwargs(
				session_doc,
				evidence_boundary_answer="Grounded evidence is not available in this artifact.",
			)
		)

		self.assertTrue(handled)
		self.assertTrue(payload["ok"])
		self.assertIn("Grounded evidence is not available", _assistant_messages(session_doc)[0]["content"])
		self.assertEqual(
			_payload_types_before_first_assistant(session_doc),
			[
				"qwen_knowledge_boundary_contract",
				"qwen_artifact_enrichment_recovery_contract",
				"qwen_artifact_boundary_observability",
				"qwen_execution_path",
				"qwen_audit_envelope",
				AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE,
			],
		)
		emission = payload["agent_meta"]["authorized_emission"]
		self.assertTrue(emission["emitted"])
		self.assertEqual(emission["answer_type"], "policy_boundary_refusal")
		self.assertEqual(emission["preflight_status"], "bounded")

	def test_enrichment_boundary_emits_as_bounded_policy_refusal(self):
		session_doc = FakeSessionDoc()
		handled, payload = handle_artifact_boundary_turn(
			**_common_kwargs(
				session_doc,
				compatibility=FakeCompatibility(compatible=False),
			)
		)

		self.assertTrue(handled)
		self.assertTrue(payload["ok"])
		self.assertIn("Enrichment boundary answer", _assistant_messages(session_doc)[0]["content"])
		self.assertIn("qwen_artifact_boundary_observability", _payload_types_before_first_assistant(session_doc))
		emission = payload["agent_meta"]["authorized_emission"]
		self.assertTrue(emission["emitted"])
		self.assertEqual(emission["answer_type"], "policy_boundary_refusal")
		self.assertEqual(emission["preflight_status"], "bounded")


if __name__ == "__main__":
	unittest.main()
