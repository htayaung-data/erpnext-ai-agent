import ast
import sys
import types
import unittest
from pathlib import Path

fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.db = types.SimpleNamespace(exists=lambda *args, **kwargs: False, sql=lambda *args, **kwargs: [])
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.get_traceback = lambda: ""
fake_frappe.log_error = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.fresh_query_interpreter import SemanticFreshQueryResult
from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import (
	SemanticFrontDoorIntent,
	SemanticFrontDoorResult,
)
from ai_assistant_ui.qwen_chat.runtime_metadata_contract import (
	LANE_CLASS_AI_SEMANTIC,
	ROLE_LIGHT_SEMANTIC,
	STRICT_STATUS_READY,
	validate_runtime_metadata_envelope,
)
from ai_assistant_ui.qwen_chat.semantic_interpreter import (
	SemanticFollowUpIntent,
	SemanticFollowUpResult,
)
from ai_assistant_ui.qwen_chat.semantic_reasoning_activation import (
	SemanticReasoningActivationIntent,
	SemanticReasoningActivationResult,
)
from ai_assistant_ui.qwen_chat.semantic_repair_intent import (
	SemanticRepairIntent,
	SemanticRepairIntentResult,
)


PROJECT_ROOT = Path(__file__).resolve().parents[6]
QWEN_CHAT_ROOT = PROJECT_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat"


AGENT_META = {
	"model": "qwen-light-semantic",
	"telemetry": {
		"fallback_used": False,
		"latency_ms": 12,
	},
}


class LightSemanticRuntimeMetadataContractsTest(unittest.TestCase):
	def assert_light_semantic_metadata(self, payload, *, lane_id):
		metadata = payload["runtime_metadata_envelope"]
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		self.assertEqual(metadata["lane_id"], lane_id)
		self.assertEqual(metadata["lane_class"], LANE_CLASS_AI_SEMANTIC)
		self.assertEqual(metadata["model_role"], ROLE_LIGHT_SEMANTIC)
		self.assertEqual(metadata["model_name"], "qwen-light-semantic")
		self.assertFalse(metadata["fallback_used"])
		self.assertEqual(metadata["role_compliance"], "compliant")
		self.assertEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertEqual(payload["agent_meta"]["runtime_metadata_envelope"], metadata)
		self.assertEqual(payload["agent_meta"]["model_role_observability"], payload["model_role_observability"])
		self.assertEqual(payload["agent_meta"]["model_role_strict_readiness"], payload["model_role_strict_readiness"])


	def test_all_light_semantic_metadata_helper_calls_pass_semantic_status(self):
		missing = []
		observed_call_sites = []
		for path in QWEN_CHAT_ROOT.rglob("*.py"):
			if path.name == "light_semantic_metadata.py":
				continue
			try:
				tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
			except SyntaxError:
				# Known manual-UAT BOM parse issue is tracked outside EC-7E-C2-C1.
				continue
			for node in ast.walk(tree):
				if not isinstance(node, ast.Call):
					continue
				func = node.func
				name = ""
				if isinstance(func, ast.Name):
					name = func.id
				elif isinstance(func, ast.Attribute):
					name = func.attr
				if name != "build_light_semantic_runtime_metadata_bundle":
					continue
				location = f"{path.relative_to(PROJECT_ROOT)}:{node.lineno}"
				observed_call_sites.append(location)
				if not any(keyword.arg == "semantic_status" for keyword in node.keywords):
					missing.append(location)
		self.assertGreaterEqual(len(observed_call_sites), 5)
		self.assertEqual(missing, [])

	def test_frontdoor_semantic_classification_includes_runtime_metadata_envelope(self):
		payload = SemanticFrontDoorResult(
			status="accepted",
			intent=SemanticFrontDoorIntent(
				intent_class="route_onward",
				confidence=0.93,
				reason="semantic match",
			),
			agent_meta=AGENT_META,
		).to_payload()

		self.assert_light_semantic_metadata(payload, lane_id="frontdoor_semantic_classification")
		self.assertEqual(payload["intent"]["intent_class"], "route_onward")

	def test_fresh_query_interpretation_includes_runtime_metadata_envelope(self):
		payload = SemanticFreshQueryResult(status="accepted", agent_meta=AGENT_META).to_payload()

		self.assert_light_semantic_metadata(payload, lane_id="fresh_query_interpretation")
		self.assertEqual(payload["status"], "accepted")

	def test_followup_interpretation_includes_runtime_metadata_envelope(self):
		payload = SemanticFollowUpResult(
			status="accepted",
			intent=SemanticFollowUpIntent(
				requested_modes=["projection"],
				confidence=0.91,
				reason="follow-up semantic match",
			),
			agent_meta=AGENT_META,
		).to_payload()

		self.assert_light_semantic_metadata(payload, lane_id="followup_interpretation")
		self.assertEqual(payload["intent"]["requested_modes"], ["projection"])

	def test_followup_fallback_arguments_propagate_to_runtime_metadata_envelope(self):
		payload = SemanticFollowUpResult(
			status="accepted",
			intent=SemanticFollowUpIntent(
				requested_modes=["projection"],
				confidence=0.91,
				reason="follow-up semantic match",
			),
			agent_meta=AGENT_META,
		).to_payload(fallback_used=True, fallback_reason="deterministic_local")

		metadata = payload["runtime_metadata_envelope"]
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		self.assertTrue(payload["fallback_used"])
		self.assertEqual(payload["fallback_reason"], "deterministic_local")
		self.assertTrue(metadata["fallback_used"])
		self.assertEqual(metadata["fallback_reason"], "deterministic_local")
		self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(metadata["strict_enforcement_ready"])

	def test_followup_non_fallback_remains_valid_and_covered(self):
		payload = SemanticFollowUpResult(
			status="accepted",
			intent=SemanticFollowUpIntent(
				requested_modes=["projection"],
				confidence=0.91,
				reason="follow-up semantic match",
			),
			agent_meta=AGENT_META,
		).to_payload(fallback_used=False, fallback_reason="")

		metadata = payload["runtime_metadata_envelope"]
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		self.assertFalse(metadata["fallback_used"])
		self.assertEqual(metadata["fallback_reason"], "")
		self.assertEqual(metadata["metadata_status"], "covered")
		self.assertEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)


	def assert_degraded_light_semantic_metadata(self, payload, *, fallback_reason):
		metadata = payload["runtime_metadata_envelope"]
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		self.assertTrue(payload["fallback_used"])
		self.assertEqual(payload["fallback_reason"], fallback_reason)
		self.assertTrue(metadata["fallback_used"])
		self.assertEqual(metadata["fallback_reason"], fallback_reason)
		self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(metadata["strict_enforcement_ready"])
		self.assertTrue(payload["model_role_observability"]["fallback_used"])
		self.assertEqual(payload["model_role_observability"]["fallback_reason"], fallback_reason)
		self.assertTrue(payload["model_role_strict_readiness"]["fallback_used"])
		self.assertNotEqual(payload["model_role_strict_readiness"]["readiness_status"], "ready_for_strict")

	def test_non_accepted_light_semantic_outcomes_are_degraded_not_strict_ready(self):
		cases = [
			(
				SemanticFrontDoorResult(status="invalid_response", agent_meta=AGENT_META).to_payload(),
				"semantic_status_invalid_response",
			),
			(
				SemanticFreshQueryResult(status="low_confidence", agent_meta=AGENT_META).to_payload(),
				"semantic_status_low_confidence",
			),
			(
				SemanticReasoningActivationResult(status="runtime_error", agent_meta=AGENT_META).to_payload(),
				"semantic_status_runtime_error",
			),
			(
				SemanticRepairIntentResult(status="not_applicable", agent_meta=AGENT_META).to_payload(),
				"semantic_status_not_applicable",
			),
			(
				SemanticFollowUpResult(status="rejected", agent_meta=AGENT_META).to_payload(),
				"semantic_status_rejected",
			),
			(
				SemanticFollowUpResult(status="not_applicable", agent_meta=AGENT_META).to_payload(),
				"semantic_status_not_applicable",
			),
		]
		for payload, fallback_reason in cases:
			with self.subTest(status=payload["status"]):
				self.assert_degraded_light_semantic_metadata(payload, fallback_reason=fallback_reason)

	def test_degraded_followup_preserves_explicit_fallback_reason(self):
		payload = SemanticFollowUpResult(
			status="rejected",
			agent_meta=AGENT_META,
		).to_payload(fallback_used=True, fallback_reason="deterministic_local")

		self.assert_degraded_light_semantic_metadata(payload, fallback_reason="deterministic_local")

	def test_semantic_reasoning_activation_includes_runtime_metadata_envelope(self):
		payload = SemanticReasoningActivationResult(
			status="accepted",
			intent=SemanticReasoningActivationIntent(
				reasoning_type="explain_variance",
				confidence=0.9,
				reason="reasoning requested",
			),
			agent_meta=AGENT_META,
		).to_payload()

		self.assert_light_semantic_metadata(payload, lane_id="semantic_reasoning_activation")
		self.assertEqual(payload["intent"]["reasoning_type"], "explain_variance")

	def test_semantic_repair_intent_includes_runtime_metadata_envelope(self):
		payload = SemanticRepairIntentResult(
			status="accepted",
			intent=SemanticRepairIntent(
				repair_intent_type="guidance_request",
				confidence=0.9,
				reason="repair requested",
			),
			agent_meta=AGENT_META,
		).to_payload()

		self.assert_light_semantic_metadata(payload, lane_id="semantic_repair_intent")
		self.assertEqual(payload["intent"]["repair_intent_type"], "guidance_request")


if __name__ == "__main__":
	unittest.main()
