import unittest

from ai_assistant_ui.qwen_chat.natural_business_understanding_runtime import (
	interpret_natural_business_understanding_shadow,
)
from ai_assistant_ui.qwen_chat.reasoning_execution import ERPBusinessReasoningExecutionResult
from ai_assistant_ui.qwen_chat.runtime_metadata_contract import (
	LANE_CLASS_AI_REASONING,
	LANE_CLASS_SHADOW_OBSERVER,
	ROLE_HEAVY_REASONING,
	ROLE_SHADOW_OBSERVER,
	STRICT_STATUS_READY,
	validate_runtime_metadata_envelope,
)


HEAVY_AGENT_META = {
	"model": "qwen-heavy-reasoning",
	"telemetry": {"fallback_used": False, "latency_ms": 42},
}
SHADOW_AGENT_META = {
	"model": "qwen-shadow-observer",
	"telemetry": {"fallback_used": False, "latency_ms": 18},
}


class HeavyShadowRuntimeMetadataContractsTest(unittest.TestCase):
	def test_reasoning_execution_answer_payload_includes_valid_heavy_metadata(self):
		payload = ERPBusinessReasoningExecutionResult(
			status="answered",
			answer_text="Grounded reasoning answer",
			reasoning_contract={"allowed_to_answer": True},
			agent_meta=HEAVY_AGENT_META,
		).to_payload()

		metadata = payload["runtime_metadata_envelope"]
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		self.assertEqual(metadata["lane_id"], "business_reasoning_answer")
		self.assertEqual(metadata["lane_class"], LANE_CLASS_AI_REASONING)
		self.assertEqual(metadata["model_role"], ROLE_HEAVY_REASONING)
		self.assertEqual(metadata["model_name"], "qwen-heavy-reasoning")
		self.assertFalse(metadata["fallback_used"])
		self.assertEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertEqual(payload["agent_meta"]["runtime_metadata_envelope"], metadata)

	def test_reasoning_execution_fallback_metadata_is_not_strict_ready(self):
		payload = ERPBusinessReasoningExecutionResult(
			status="answered",
			answer_text="Grounded reasoning answer",
			reasoning_contract={"allowed_to_answer": True},
			agent_meta={
				"model": "qwen-heavy-reasoning",
				"telemetry": {"fallback_used": True, "fallback_reason": "runtime_degraded"},
			},
		).to_payload()

		metadata = payload["runtime_metadata_envelope"]
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		self.assertTrue(metadata["fallback_used"])
		self.assertEqual(metadata["fallback_reason"], "runtime_degraded")
		self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(metadata["strict_enforcement_ready"])

	def test_nbu_shadow_observation_includes_valid_shadow_metadata(self):
		def fake_runtime_call(**kwargs):
			return {
				"ok": True,
				"agent_meta": SHADOW_AGENT_META,
				"interpretation": {"candidate_interpretations": []},
			}

		trace = interpret_natural_business_understanding_shadow(
			request_id="req-shadow",
			session_id="session-shadow",
			message="unclear business question",
			runtime_call=fake_runtime_call,
		)

		metadata = trace["runtime_metadata_envelope"]
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		self.assertEqual(metadata["lane_id"], "nbu_shadow_observation")
		self.assertEqual(metadata["lane_class"], LANE_CLASS_SHADOW_OBSERVER)
		self.assertEqual(metadata["model_role"], ROLE_SHADOW_OBSERVER)
		self.assertEqual(metadata["model_name"], "qwen-shadow-observer")
		self.assertFalse(metadata["fallback_used"])
		self.assertEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertEqual(trace["agent_meta"]["runtime_metadata_envelope"], metadata)

	def test_nbu_shadow_fallback_metadata_is_not_strict_ready(self):
		def fake_runtime_call(**kwargs):
			return {
				"ok": True,
				"agent_meta": {
					"model": "qwen-shadow-observer",
					"telemetry": {"fallback_used": True, "fallback_reason": "shadow_runtime_degraded"},
				},
				"interpretation": {"candidate_interpretations": []},
			}

		trace = interpret_natural_business_understanding_shadow(
			request_id="req-shadow-fallback",
			session_id="session-shadow-fallback",
			message="unclear business question",
			runtime_call=fake_runtime_call,
		)

		metadata = trace["runtime_metadata_envelope"]
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		self.assertTrue(metadata["fallback_used"])
		self.assertEqual(metadata["fallback_reason"], "shadow_runtime_degraded")
		self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(metadata["strict_enforcement_ready"])

	def test_nbu_shadow_runtime_failure_missing_metadata_is_not_strict_ready(self):
		def fake_runtime_call(**kwargs):
			raise RuntimeError("shadow runtime offline")

		trace = interpret_natural_business_understanding_shadow(
			request_id="req-shadow-offline",
			session_id="session-shadow-offline",
			message="unclear business question",
			runtime_call=fake_runtime_call,
		)

		metadata = trace["runtime_metadata_envelope"]
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		self.assertEqual(metadata["model_name"], "unknown")
		self.assertTrue(metadata["fallback_used"])
		self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(metadata["strict_enforcement_ready"])


if __name__ == "__main__":
	unittest.main()
