import sys
import types
import unittest
from pathlib import Path

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

from ai_assistant_ui.qwen_chat.fresh_query_interpreter import _attach_fresh_compiled_read_runtime_metadata
from ai_assistant_ui.qwen_chat.runtime_metadata_contract import STRICT_STATUS_READY, validate_runtime_metadata_envelope
from ai_assistant_ui.qwen_chat.semantic_interpreter import SemanticFollowUpResult
from ai_assistant_ui.qwen_chat.semantic_validator import validate_compiled_semantic_result


PROJECT_ROOT = Path(__file__).resolve().parents[6]
SERVICE_PATH = PROJECT_ROOT / (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py"
)


class ServiceValidatorProvenanceProbeTests(unittest.TestCase):
	def test_service_pre_frontdoor_followup_passes_explicit_fallback_provenance(self):
		text = SERVICE_PATH.read_text(encoding="utf-8")
		self.assertIn("semantic_payload = semantic_result.to_payload(", text)
		self.assertIn("fallback_used=False", text)
		self.assertIn(
			"No heuristic fallback permitted; degraded follow-up handling remains explicit and auditable.",
			text,
		)

	def test_degraded_followup_with_complete_model_metadata_is_not_strict_ready(self):
		payload = SemanticFollowUpResult(
			status="rejected",
			agent_meta={"model": "qwen-light-semantic", "telemetry": {"fallback_used": False}},
		).to_payload()
		metadata = payload["runtime_metadata_envelope"]

		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		self.assertTrue(payload["fallback_used"])
		self.assertEqual(payload["fallback_reason"], "semantic_status_rejected")
		self.assertTrue(metadata["fallback_used"])
		self.assertEqual(metadata["fallback_reason"], "semantic_status_rejected")
		self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(metadata["strict_enforcement_ready"])

	def test_failed_compiled_read_runtime_provenance_remains_visible_and_non_strict(self):
		payload = _attach_fresh_compiled_read_runtime_metadata(
			{
				"ok": False,
				"answer_text": "",
				"tool_trace": [],
				"agent_meta": {"engine": "unavailable"},
				"error": "runtime unavailable",
			},
			fallback_used=True,
			fallback_reason="runtime unavailable",
		)
		metadata = payload["runtime_metadata_envelope"]

		self.assertEqual(payload["error"], "runtime unavailable")
		self.assertTrue(metadata["fallback_used"])
		self.assertEqual(metadata["fallback_reason"], "runtime unavailable")
		self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(metadata["strict_enforcement_ready"])
		self.assertEqual(payload["agent_meta"]["runtime_metadata_envelope"], metadata)

	def test_semantic_validator_does_not_forge_model_strict_readiness(self):
		runtime_payload = _attach_fresh_compiled_read_runtime_metadata(
			{"ok": False, "answer_text": "", "tool_trace": [], "agent_meta": {"engine": "unavailable"}},
			fallback_used=True,
			fallback_reason="runtime unavailable",
		)
		validation_payload = validate_compiled_semantic_result(
			interaction_contract={"request_id": "probe"},
			interpretation_contract={"intent_class": "financial_summary"},
			compiler_contract={
				"request_id": "probe",
				"capability_id": "accounts_payable_read",
				"selected_report": "Accounts Payable Summary",
			},
			runtime_payload=runtime_payload,
		).to_payload()

		self.assertEqual(validation_payload["status"], "reject_semantically_inconsistent")
		self.assertNotIn("runtime_metadata_envelope", validation_payload)
		self.assertNotIn("model_role_strict_readiness", validation_payload)
		self.assertNotIn(STRICT_STATUS_READY, str(validation_payload))


if __name__ == "__main__":
	unittest.main()