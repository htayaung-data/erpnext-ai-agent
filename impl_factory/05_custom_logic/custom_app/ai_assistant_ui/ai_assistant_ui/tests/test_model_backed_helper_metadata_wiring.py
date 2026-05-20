import json
import sys
import types
import unittest


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.log_error = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat import artifact_narrative, clarification_system
from ai_assistant_ui.qwen_chat.authorized_emission import (
	ANSWER_TYPE_BUSINESS_FACTUAL,
	EMISSION_STATUS_BLOCKED,
	emit_authorized_assistant_answer,
)
from ai_assistant_ui.qwen_chat.contracts import (
	ExecutionPath,
	build_followup_resolution_contract,
	build_interaction_contract,
)
from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import FrontDoorRenderResult
from ai_assistant_ui.qwen_chat.runtime_metadata_contract import (
	LANE_CLASS_CONTROL_META,
	LANE_CLASS_MODEL_BACKED_HELPER,
	METADATA_STATUS_NOT_APPLICABLE,
	ROLE_MODEL_BACKED_HELPER,
	ROLE_NOT_APPLICABLE,
	STRICT_STATUS_READY,
)


class FakeSessionDoc:
	def __init__(self):
		self.messages = []


def _append_message(session_doc, role, content):
	session_doc.messages.append({"role": role, "content": content})


def _append_tool_payload(session_doc, payload):
	session_doc.messages.append({"role": "tool", "content": payload})


def _assistant_text_payload(text):
	return {"text": str(text or "")}


def _interaction():
	return build_interaction_contract(
		request_id="req-c2a",
		session_id="session-c2a",
		user_id="user@example.com",
		site_name="erpai_prj1",
		raw_message="frontdoor helper text",
	)


def _followup():
	return build_followup_resolution_contract(
		request_id="req-c2a",
		mode="frontdoor_render",
		requested_modes=["frontdoor_render"],
		depends_on_grounded_turn=False,
		self_contained=True,
		latest_grounded_turn_available=False,
		reason="contract test",
	)


def _execution_path():
	return ExecutionPath(
		request_id="req-c2a",
		path="frontdoor_render",
		reason="contract test",
		requires_runtime=False,
		grounded_required=False,
	)


class ModelBackedHelperMetadataWiringTests(unittest.TestCase):
	def test_frontdoor_render_success_includes_strict_ready_helper_metadata_without_text_change(self):
		payload = FrontDoorRenderResult(
			ok=True,
			answer_text="Exact frontdoor answer.",
			agent_meta={"model": "qwen-helper-render"},
		).to_payload()
		envelope = payload["runtime_metadata_envelope"]

		self.assertEqual(payload["answer_text"], "Exact frontdoor answer.")
		self.assertEqual(envelope["lane_class"], LANE_CLASS_MODEL_BACKED_HELPER)
		self.assertEqual(envelope["model_role"], ROLE_MODEL_BACKED_HELPER)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertEqual(payload["agent_meta"]["runtime_metadata_envelope"], envelope)

	def test_frontdoor_render_error_metadata_is_not_strict_ready_without_text_change(self):
		payload = FrontDoorRenderResult(
			ok=False,
			answer_text="Fallback frontdoor answer.",
			runtime_error="runtime unavailable",
		).to_payload()
		envelope = payload["runtime_metadata_envelope"]

		self.assertEqual(payload["answer_text"], "Fallback frontdoor answer.")
		self.assertNotEqual(envelope["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(envelope["strict_enforcement_ready"])
		self.assertTrue(envelope["fallback_used"])

	def test_ai_clarification_success_includes_strict_ready_helper_metadata_without_text_change(self):
		original = clarification_system.call_qwen_runtime_chat

		def fake_call(**_kwargs):
			return {
				"ok": True,
				"answer_text": json.dumps(
					{
						"question": "Do you want the current report or a new period?",
						"options": ["Current report", "New period"],
						"context_type": "followup",
					}
				),
				"agent_meta": {"model": "qwen-helper-clarification"},
			}

		try:
			clarification_system.call_qwen_runtime_chat = fake_call
			question = clarification_system.generate_ai_clarification(
				request_id="req-c2a-clarify",
				session_id="session-c2a",
				user_id="user@example.com",
				site_name="erpai_prj1",
				raw_message="that one",
				context={"family_id": "aging"},
			)
		finally:
			clarification_system.call_qwen_runtime_chat = original

		self.assertIsNotNone(question)
		payload = clarification_system.build_clarification_response(question)
		envelope = payload["runtime_metadata_envelope"]
		self.assertEqual(payload["answer_text"], "Do you want the current report or a new period?")
		self.assertEqual(envelope["lane_class"], LANE_CLASS_MODEL_BACKED_HELPER)
		self.assertEqual(envelope["model_role"], ROLE_MODEL_BACKED_HELPER)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_READY)

	def test_clarification_template_fallback_is_not_applicable_and_non_strict(self):
		question = clarification_system.ClarificationQuestion(
			question="Which period should I use?",
			options=["This month", "This year"],
			context_type="scope",
			generation_method="template",
		)
		payload = clarification_system.build_clarification_response(question)
		envelope = payload["runtime_metadata_envelope"]

		self.assertEqual(payload["answer_text"], "Which period should I use?")
		self.assertEqual(envelope["lane_class"], LANE_CLASS_CONTROL_META)
		self.assertEqual(envelope["model_role"], ROLE_NOT_APPLICABLE)
		self.assertEqual(envelope["metadata_status"], METADATA_STATUS_NOT_APPLICABLE)
		self.assertNotEqual(envelope["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(envelope["strict_enforcement_ready"])

	def test_artifact_narrative_success_includes_strict_ready_helper_metadata_without_text_change(self):
		original = artifact_narrative.call_qwen_runtime_chat

		def fake_call(**_kwargs):
			return {
				"ok": True,
				"answer_text": "Exact artifact narrative.",
				"agent_meta": {"model": "qwen-helper-narrative"},
			}

		try:
			artifact_narrative.call_qwen_runtime_chat = fake_call
			payload = artifact_narrative.narrate_governed_artifact(
				session_id="session-c2a",
				user_id="user@example.com",
				site_name="erpai_prj1",
				message="summarize this artifact",
				request_id="req-c2a-artifact",
				artifact_context={"family_id": "ranking", "source_reports": ["Sales Order"]},
				response_policy={},
			)
		finally:
			artifact_narrative.call_qwen_runtime_chat = original

		envelope = payload["runtime_metadata_envelope"]
		self.assertEqual(payload["answer_text"], "Exact artifact narrative.")
		self.assertEqual(envelope["lane_class"], LANE_CLASS_MODEL_BACKED_HELPER)
		self.assertEqual(envelope["model_role"], ROLE_MODEL_BACKED_HELPER)
		self.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_READY)

	def test_artifact_narrative_invalid_and_runtime_failure_paths_are_not_strict_ready(self):
		original = artifact_narrative.call_qwen_runtime_chat

		def invalid_call(**_kwargs):
			return "invalid"

		def failing_call(**_kwargs):
			raise artifact_narrative.QwenRuntimeClientError("runtime unavailable")

		try:
			for fake_call in (invalid_call, failing_call):
				artifact_narrative.call_qwen_runtime_chat = fake_call
				payload = artifact_narrative.narrate_governed_artifact(
					session_id="session-c2a",
					user_id="user@example.com",
					site_name="erpai_prj1",
					message="summarize this artifact",
					request_id="req-c2a-artifact",
					artifact_context={"family_id": "ranking"},
					response_policy={},
				)
				envelope = payload["runtime_metadata_envelope"]
				self.assertEqual(payload["answer_text"], "")
				self.assertNotEqual(envelope["strict_readiness_status"], STRICT_STATUS_READY)
				self.assertFalse(envelope["strict_enforcement_ready"])
		finally:
			artifact_narrative.call_qwen_runtime_chat = original

	def test_helper_metadata_cannot_create_final_answer_business_authority(self):
		helper_payload = FrontDoorRenderResult(
			ok=True,
			answer_text="Helper-rendered business text.",
			agent_meta={"model": "qwen-helper-render"},
		).to_payload()
		envelope = dict(helper_payload["runtime_metadata_envelope"])
		envelope["authority_source"] = "governed_erp_report"
		session_doc = FakeSessionDoc()
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="Helper-rendered business text.",
			answer_type=ANSWER_TYPE_BUSINESS_FACTUAL,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=_interaction(),
			followup_resolution=_followup(),
			execution_path=_execution_path(),
			runtime_trace_payload={"agent_meta": {"runtime_metadata_envelope": envelope}},
			authority_context={"runtime_metadata_envelope": envelope},
		)

		self.assertFalse(result.emitted)
		self.assertTrue(result.blocked)
		self.assertEqual([message["role"] for message in session_doc.messages], ["tool"])
		self.assertEqual(session_doc.messages[0]["content"]["emission_status"], EMISSION_STATUS_BLOCKED)
		self.assertNotEqual(result.final_answer_authority.get("authority_source"), "governed_erp_report")
		self.assertNotIn("assistant", [message["role"] for message in session_doc.messages])


if __name__ == "__main__":
	unittest.main()
