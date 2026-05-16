from __future__ import annotations

import json
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from ai_assistant_ui.qwen_chat.authorized_emission import (
	AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE,
)
from ai_assistant_ui.qwen_chat.contracts import (
	build_followup_resolution_contract,
	build_interaction_contract,
)
from ai_assistant_ui.qwen_chat.local_followup_support import try_local_followup_transform


PROJECT_ROOT = Path(__file__).resolve().parents[6]


class FakeSessionDoc:
	def __init__(self) -> None:
		self.name = "local-followup-session"
		self.messages: List[Dict[str, Any]] = []
		self.saved = False

	def append(self, fieldname: str, value: Dict[str, Any]) -> None:
		if str(fieldname or "").strip() == "messages":
			self.messages.append(value)


@dataclass(frozen=True)
class FakeResponsePolicy:
	def to_runtime_payload(self) -> Dict[str, Any]:
		return {"type": "qwen_response_policy_contract", "policy": "test"}


def _append_message(session_doc, role, content) -> None:
	session_doc.append("messages", {"role": str(role or "").strip(), "content": content})


def _append_tool_payload(session_doc, payload) -> None:
	session_doc.append("messages", {"role": "tool", "content": json.dumps(payload)})


def _assistant_text_payload(text: str) -> str:
	return str(text or "")


def _save_session(session_doc, *, ignore_permissions: bool = False) -> None:
	session_doc.saved = True


def _tool_payloads(session_doc) -> List[Dict[str, Any]]:
	payloads: List[Dict[str, Any]] = []
	for row in session_doc.messages:
		if row.get("role") != "tool":
			continue
		content = row.get("content")
		payloads.append(content if isinstance(content, dict) else json.loads(str(content or "{}")))
	return payloads


def _assistant_messages(session_doc) -> List[Dict[str, Any]]:
	return [row for row in session_doc.messages if row.get("role") == "assistant"]


def _payload_types_before_first_assistant(session_doc) -> List[str]:
	types: List[str] = []
	for row in session_doc.messages:
		if row.get("role") == "assistant":
			break
		if row.get("role") == "tool":
			types.append(str(json.loads(str(row.get("content") or "{}")).get("type") or ""))
	return types


def _trace_message(*, request_id: str, source_request_id: str, transforms: List[str]) -> str:
	return json.dumps(
		{
			"type": "qwen_runtime_trace",
			"request_id": request_id,
			"ok": True,
			"tool_trace": [
				{
					"tool": "local_transform",
					"status": "ok",
					"detail": ",".join(transforms),
					"detail_obj": {"source_request_id": source_request_id, "transforms": transforms},
				}
			],
			"agent_meta": {
				"engine": "local_transform",
				"transforms": transforms,
				"source_request_id": source_request_id,
			},
		}
	)


def _common_kwargs(session_doc, *, grounded_turn=None, family_artifact=None, transform_text="Transformed local answer."):
	return {
		"session_doc": session_doc,
		"request_id": "req-local-followup",
		"raw_message": "Display the values in millions",
		"followup_resolution": build_followup_resolution_contract(
			request_id="req-local-followup",
			mode="local_grounded_transform",
			requested_modes=["presentation_transform"],
			depends_on_grounded_turn=True,
			self_contained=False,
			latest_grounded_turn_available=True,
			reason="local follow-up test",
		),
		"interaction_contract": build_interaction_contract(
			request_id="req-local-followup",
			session_id=session_doc.name,
			user_id="unit@example.com",
			site_name="erpai_prj1",
			raw_message="Display the values in millions",
		),
		"response_policy_contract": FakeResponsePolicy(),
		"continuation_contract": None,
		"latest_grounded_assistant_context": lambda session_doc: (
			{"text": "Original grounded answer.", "request_id": "source-request-1"},
			{"request_id": "source-request-1"},
		),
		"latest_grounded_turn_contract": lambda session_doc: (
			grounded_turn
			if grounded_turn is not None
			else {
				"type": "qwen_grounded_turn_context",
				"grounded": True,
				"source_kind": "report",
				"source_name": "Top Products by Revenue",
				"artifact_family_id": "ranking_analytics",
				"trace_request_id": "source-request-1",
			}
		),
		"latest_normalized_family_artifact": lambda session_doc: (
			family_artifact
			if family_artifact is not None
			else {
				"type": "qwen_normalized_family_artifact_contract",
				"request_id": "artifact-local-1",
				"family_id": "ranking_analytics",
			}
		),
		"latest_display_preferences": lambda session_doc, modes: {"million": True},
		"session_tool_payloads": _tool_payloads,
		"apply_local_followup_transforms": lambda **kwargs: (
			transform_text,
			["presentation_transform"],
			{
				"type": "qwen_rendered_family_response_contract",
				"answer_text": transform_text,
			},
			{
				"type": "qwen_normalized_family_artifact_contract",
				"request_id": "artifact-local-updated",
				"family_id": "ranking_analytics",
			},
		),
		"maybe_apply_local_followup_narrative": lambda **kwargs: ("", {}, False),
		"append_message": _append_message,
		"append_tool_payload": _append_tool_payload,
		"assistant_text_payload": _assistant_text_payload,
		"local_transform_trace_message": _trace_message,
		"save_session": _save_session,
		"supports_local_family_followup": lambda *args, **kwargs: True,
		"render_local_family_followup": lambda **kwargs: {},
		"render_local_followup": lambda *args, **kwargs: "",
		"ensure_table_from_grounded_context": lambda text, *args, **kwargs: text,
		"transform_markdown_to_million": lambda text: text,
		"refine_local_family_artifact": lambda **kwargs: {},
	}


class LocalFollowupAuthorizedEmissionContractTests(unittest.TestCase):
	def test_local_transform_emits_after_authority_payloads(self):
		session_doc = FakeSessionDoc()
		handled = try_local_followup_transform(**_common_kwargs(session_doc))

		self.assertIsNotNone(handled)
		ok, payload = handled
		self.assertTrue(ok)
		self.assertTrue(payload["ok"])
		self.assertEqual(_assistant_messages(session_doc)[0]["content"], "Transformed local answer.")
		self.assertEqual(
			_payload_types_before_first_assistant(session_doc),
			[
				"qwen_normalized_family_artifact_contract",
				"qwen_rendered_family_response_contract",
				"qwen_runtime_trace",
				"qwen_execution_path",
				"qwen_audit_envelope",
				AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE,
			],
		)
		emission = payload["agent_meta"]["authorized_emission"]
		self.assertTrue(emission["emitted"])
		self.assertEqual(emission["answer_type"], "visible_context_answer")
		self.assertEqual(emission["preflight_status"], "passed")

	def test_missing_local_transform_authority_blocks_without_answer_or_payload_leak(self):
		session_doc = FakeSessionDoc()
		handled = try_local_followup_transform(
			**_common_kwargs(
				session_doc,
				grounded_turn={},
				family_artifact={},
				transform_text="Unauthorized transformed local answer.",
			)
		)
		self.assertIsNotNone(handled)
		ok, payload = handled
		serialized_messages = json.dumps(session_doc.messages)

		self.assertTrue(ok)
		self.assertFalse(payload["ok"])
		self.assertEqual(_assistant_messages(session_doc), [])
		self.assertEqual(len(_tool_payloads(session_doc)), 1)
		self.assertEqual(_tool_payloads(session_doc)[0]["type"], AUTHORIZED_ASSISTANT_EMISSION_CONTRACT_TYPE)
		self.assertTrue(_tool_payloads(session_doc)[0]["blocked"])
		self.assertNotIn("Unauthorized transformed local answer.", serialized_messages)
		self.assertNotIn("answer_text", payload)

	def test_service_local_transform_guard_skips_legacy_post_helper_audit_when_authorized_emission_exists(self):
		service_text = (
			PROJECT_ROOT
			/ "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py"
		).read_text(encoding="utf-8")
		local_transform_block_start = service_text.index("if local_transform:")
		guard_index = service_text.index("local_authorized_emission", local_transform_block_start)
		return_index = service_text.index("return local_transform", guard_index)
		legacy_audit_index = service_text.index("build_audit_envelope(", local_transform_block_start)

		self.assertLess(guard_index, legacy_audit_index)
		self.assertLess(return_index, legacy_audit_index)
		self.assertIn("agent_meta", service_text[guard_index:legacy_audit_index])
		self.assertIn("authorized_emission", service_text[guard_index:legacy_audit_index])


if __name__ == "__main__":
	unittest.main()
