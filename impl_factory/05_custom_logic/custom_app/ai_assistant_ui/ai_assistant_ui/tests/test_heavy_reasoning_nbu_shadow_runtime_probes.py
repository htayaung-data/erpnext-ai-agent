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

from ai_assistant_ui.qwen_chat import reasoning_execution
from ai_assistant_ui.qwen_chat.authorized_emission import ANSWER_TYPE_BUSINESS_FACTUAL, emit_authorized_assistant_answer
from ai_assistant_ui.qwen_chat.natural_business_understanding_runtime import interpret_natural_business_understanding_shadow
from ai_assistant_ui.qwen_chat.runtime_metadata_contract import STRICT_STATUS_READY, validate_runtime_metadata_envelope


HEAVY_AGENT_META = {"model": "qwen-heavy-reasoning", "telemetry": {"fallback_used": False}}
HEAVY_MISSING_MODEL_META = {"telemetry": {"fallback_used": False}}
SHADOW_AGENT_META = {"model": "qwen-shadow-observer", "telemetry": {"fallback_used": False}}
SHADOW_MISSING_MODEL_META = {"telemetry": {"fallback_used": False}}


class FakeSessionDoc:
	def __init__(self):
		self.messages = []


def append_message(session_doc, role, content):
	session_doc.messages.append({"role": role, "content": content})


def append_tool_payload(session_doc, payload):
	session_doc.messages.append({"role": "tool", "content": payload})


def assistant_text_payload(text):
	return {"text": str(text or "")}


def reasoning_activation_contract():
	return {
		"activation_state": "eligible",
		"grounded_context_available": True,
		"grounded_source_request_id": "reasoning-source-1",
		"grounded_source_kind": "report",
		"grounded_source_name": "Sales Analytics",
		"grounded_family_id": "ranking_analytics",
		"grounded_artifact_type": "normalized_family_artifact",
		"grounded_source_reports": ["Sales Analytics"],
		"grounded_capability_id": "sales_read",
		"allowed_reasoning_types": ["interpretation"],
		"recommendation_allowed": False,
	}


def semantic_activation_result():
	return {
		"status": "accepted",
		"intent": {
			"reasoning_type": "interpretation",
			"confidence": 0.92,
			"reason": "explain the grounded result",
		},
	}


def grounded_turn():
	return {
		"grounded": True,
		"trace_request_id": "reasoning-source-1",
		"source_kind": "report",
		"source_name": "Sales Analytics",
		"artifact_family_id": "ranking_analytics",
		"artifact_type": "normalized_family_artifact",
		"artifact_source_reports": ["Sales Analytics"],
		"returned_schema": ["Customer", "Grand Total"],
		"table_rows": [{"Customer": "Customer A", "Grand Total": "1000"}],
		"row_count": 1,
	}


def heavy_runtime_payload(*, agent_meta=HEAVY_AGENT_META, answer_text="Grounded reasoning answer."):
	return {
		"payload": {
			"answer_text": answer_text,
			"supported_claims": [{"claim": "Sales total is grounded.", "support": "Sales Analytics row."}],
			"recommendations": [],
			"speculation_flags": [],
			"reason": "Grounded interpretation.",
			"confidence": 0.91,
		},
		"agent_meta": dict(agent_meta),
	}


class HeavyReasoningAndNBUShadowRuntimeProbeTests(unittest.TestCase):
	def setUp(self):
		self._original_reasoning_render = reasoning_execution.call_qwen_runtime_reasoning_render

	def tearDown(self):
		reasoning_execution.call_qwen_runtime_reasoning_render = self._original_reasoning_render

	def execute_reasoning(self, runtime_response=None, raises=False):
		def fake_runtime(**_kwargs):
			if raises:
				raise reasoning_execution.QwenRuntimeClientError("heavy reasoning runtime unavailable")
			return runtime_response if runtime_response is not None else heavy_runtime_payload()

		reasoning_execution.call_qwen_runtime_reasoning_render = fake_runtime
		return reasoning_execution.execute_erp_business_reasoning(
			request_id="req-heavy",
			session_id="session-heavy",
			user_id="user@example.com",
			message="explain this result",
			recent_messages=[],
			activation_contract=reasoning_activation_contract(),
			semantic_activation_result=semantic_activation_result(),
			latest_grounded_turn=grounded_turn(),
			latest_family_artifact={"family_id": "ranking_analytics"},
			latest_assistant_payload={"title": "Sales Analytics"},
		)

	def assert_metadata_valid(self, payload):
		metadata = payload["runtime_metadata_envelope"]
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		return metadata

	def test_heavy_reasoning_success_with_complete_metadata_can_be_strict_ready(self):
		payload = self.execute_reasoning().to_payload()
		metadata = self.assert_metadata_valid(payload)

		self.assertEqual(payload["status"], "answered")
		self.assertEqual(metadata["lane_id"], "business_reasoning_answer")
		self.assertEqual(metadata["lane_class"], "ai_reasoning")
		self.assertEqual(metadata["model_role"], "heavy_reasoning")
		self.assertEqual(metadata["model_name"], "qwen-heavy-reasoning")
		self.assertFalse(metadata["fallback_used"])
		self.assertEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertTrue(metadata["strict_enforcement_ready"])

	def test_heavy_reasoning_missing_model_metadata_cannot_be_strict_ready(self):
		payload = self.execute_reasoning(runtime_response=heavy_runtime_payload(agent_meta=HEAVY_MISSING_MODEL_META)).to_payload()
		metadata = self.assert_metadata_valid(payload)

		self.assertEqual(payload["status"], "answered")
		self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(metadata["strict_enforcement_ready"])
		self.assertIn("model_name", metadata["missing_fields"])

	def test_heavy_reasoning_fallback_and_runtime_error_cannot_be_strict_ready(self):
		fallback_payload = self.execute_reasoning(
			runtime_response=heavy_runtime_payload(
				agent_meta={"model": "qwen-heavy-reasoning", "telemetry": {"fallback_used": True, "fallback_reason": "heavy_runtime_degraded"}}
			)
		).to_payload()
		fallback_metadata = self.assert_metadata_valid(fallback_payload)
		self.assertTrue(fallback_metadata["fallback_used"])
		self.assertEqual(fallback_metadata["fallback_reason"], "heavy_runtime_degraded")
		self.assertNotEqual(fallback_metadata["strict_readiness_status"], STRICT_STATUS_READY)

		error_payload = self.execute_reasoning(raises=True).to_payload()
		error_metadata = self.assert_metadata_valid(error_payload)
		self.assertEqual(error_payload["status"], "runtime_error")
		self.assertNotEqual(error_metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(error_metadata["strict_enforcement_ready"])

	def test_heavy_reasoning_metadata_does_not_bypass_final_answer_authority(self):
		reasoning_payload = self.execute_reasoning().to_payload()
		session_doc = FakeSessionDoc()
		emission = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="Business answer from helper metadata only.",
			answer_type=ANSWER_TYPE_BUSINESS_FACTUAL,
			append_message=append_message,
			append_tool_payload=append_tool_payload,
			assistant_text_payload=assistant_text_payload,
			runtime_trace_payload={"runtime_metadata_envelope": reasoning_payload["runtime_metadata_envelope"], "agent_meta": reasoning_payload["agent_meta"]},
			authority_context={"runtime_metadata_envelope": reasoning_payload["runtime_metadata_envelope"]},
		)

		self.assertFalse(emission.emitted)
		self.assertTrue(emission.blocked)
		self.assertEqual([msg for msg in session_doc.messages if msg["role"] == "assistant"], [])
		self.assertNotEqual(emission.to_payload()["final_answer_authority"].get("authority_source"), "business_reasoning_runtime_agent_meta")

	def test_nbu_shadow_success_missing_metadata_and_fallback_provenance(self):
		def success_runtime(**_kwargs):
			return {"ok": True, "agent_meta": SHADOW_AGENT_META, "interpretation": {"candidate_interpretations": []}}

		def missing_runtime(**_kwargs):
			return {"ok": True, "agent_meta": SHADOW_MISSING_MODEL_META, "interpretation": {"candidate_interpretations": []}}

		def fallback_runtime(**_kwargs):
			return {
				"ok": True,
				"agent_meta": {"model": "qwen-shadow-observer", "telemetry": {"fallback_used": True, "fallback_reason": "shadow_runtime_degraded"}},
				"interpretation": {"candidate_interpretations": []},
			}

		for runtime_call, strict_expected in [(success_runtime, True), (missing_runtime, False), (fallback_runtime, False)]:
			with self.subTest(runtime_call=runtime_call.__name__):
				trace = interpret_natural_business_understanding_shadow(
					request_id="req-shadow",
					session_id="session-shadow",
					message="unclear business question",
					runtime_call=runtime_call,
				)
				metadata = self.assert_metadata_valid(trace)
				self.assertEqual(metadata["lane_id"], "nbu_shadow_observation")
				self.assertEqual(metadata["lane_class"], "shadow_observer")
				self.assertEqual(metadata["model_role"], "shadow_observer")
				self.assertEqual(trace["conversation_action_decision"]["action"], "observe_only")
				self.assertFalse(trace["conversation_action_decision"]["requires_routing_change"])
				self.assertFalse(trace["conversation_action_decision"]["safe_to_execute"])
				if strict_expected:
					self.assertEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
				else:
					self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
					self.assertFalse(metadata["strict_enforcement_ready"])

	def test_nbu_shadow_runtime_error_is_observe_only_and_not_strict_ready(self):
		def failing_runtime(**_kwargs):
			raise RuntimeError("shadow runtime offline")

		trace = interpret_natural_business_understanding_shadow(
			request_id="req-shadow-error",
			session_id="session-shadow-error",
			message="unclear business question",
			runtime_call=failing_runtime,
		)
		metadata = self.assert_metadata_valid(trace)

		self.assertTrue(metadata["fallback_used"])
		self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(metadata["strict_enforcement_ready"])
		self.assertEqual(trace["conversation_action_decision"]["action"], "observe_only")
		self.assertFalse(trace["conversation_action_decision"]["requires_routing_change"])
		self.assertFalse(trace["conversation_action_decision"]["safe_to_execute"])


if __name__ == "__main__":
	unittest.main()