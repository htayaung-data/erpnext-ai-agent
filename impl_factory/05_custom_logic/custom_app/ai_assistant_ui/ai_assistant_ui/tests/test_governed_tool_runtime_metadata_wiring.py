import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace


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

from ai_assistant_ui.qwen_chat import composite_reads, fresh_query_interpreter
from ai_assistant_ui.qwen_chat.authorized_emission import (
	ANSWER_TYPE_BUSINESS_FACTUAL,
	EMISSION_STATUS_BLOCKED,
	emit_authorized_assistant_answer,
)
from ai_assistant_ui.qwen_chat.contracts import (
	CompiledQueryRequestContract,
	ExecutionPath,
	FreshQueryCompilerContract,
	build_followup_resolution_contract,
	build_interaction_contract,
)
from ai_assistant_ui.qwen_chat.model_backed_helper_metadata import (
	attach_governed_tool_runtime_metadata_to_payload,
)
from ai_assistant_ui.qwen_chat.runtime_metadata_contract import (
	LANE_CLASS_GOVERNED_TOOL_RUNTIME,
	ROLE_GOVERNED_TOOL_RUNTIME,
	STRICT_STATUS_READY,
	validate_runtime_metadata_envelope,
)


PROJECT_ROOT = Path(__file__).resolve().parents[6]
FRESH_QUERY_INTERPRETER = PROJECT_ROOT / (
	"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/"
	"qwen_chat/fresh_query_interpreter.py"
)


class PayloadObject(SimpleNamespace):
	def to_payload(self):
		return dict(self.payload)


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
		request_id="req-c2b",
		session_id="session-c2b",
		user_id="user@example.com",
		site_name="erpai_prj1",
		raw_message="compiled read helper text",
	)


def _followup():
	return build_followup_resolution_contract(
		request_id="req-c2b",
		mode="compiled_read_query",
		requested_modes=["compiled_read_query"],
		depends_on_grounded_turn=False,
		self_contained=True,
		latest_grounded_turn_available=False,
		reason="contract test",
	)


def _execution_path():
	return ExecutionPath(
		request_id="req-c2b",
		path="compiled_read_query",
		reason="contract test",
		requires_runtime=False,
		grounded_required=False,
	)


def _compiled_request():
	return CompiledQueryRequestContract(
		request_id="compiled-c2b",
		capability_id="sales_read",
		selected_report="Sales Analytics",
		filters={},
		requested_dimensions=["Customer"],
		requested_metrics=["Revenue"],
		response_policy={},
		extracted_slots={},
	)


def _compiler_contract():
	return FreshQueryCompilerContract(
		request_id="compiled-c2b",
		session_id="session-c2b",
		capability_id="sales_read",
		selected_report="Sales Analytics",
		selected_report_family="ranking_analytics",
		completed_filters={},
		requested_dimensions=["Customer"],
		requested_metrics=["Revenue"],
		requested_time_scope="current_fiscal_year_to_date",
		decision="execute",
		clarification_required=False,
		compiler_reason="contract test",
		governed_resolution_details={},
		clarification_reason_type="",
		clarification_details={},
		extracted_slots={},
	)


class GovernedToolRuntimeMetadataWiringTests(unittest.TestCase):
	def setUp(self):
		self._orig_execute_governed_report = composite_reads.execute_governed_report
		self._orig_call_qwen_runtime_chat = composite_reads.call_qwen_runtime_chat
		self._orig_build_artifact = composite_reads.build_normalized_family_artifact
		self._orig_validate_artifact = composite_reads.validate_normalized_family_artifact

		composite_reads.build_normalized_family_artifact = lambda **_kwargs: SimpleNamespace(
			artifact_contract=PayloadObject(payload={"type": "artifact", "family_id": "ranking_analytics"}),
			family_id="ranking_analytics",
			errors=[],
			warnings=[],
			status="pass",
		)
		composite_reads.validate_normalized_family_artifact = lambda **_kwargs: PayloadObject(
			payload={"type": "validation", "status": "pass"}
		)

	def tearDown(self):
		composite_reads.execute_governed_report = self._orig_execute_governed_report
		composite_reads.call_qwen_runtime_chat = self._orig_call_qwen_runtime_chat
		composite_reads.build_normalized_family_artifact = self._orig_build_artifact
		composite_reads.validate_normalized_family_artifact = self._orig_validate_artifact

	def _execute_step(self):
		return composite_reads._execute_composite_step(
			session_id="session-c2b",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="top customers by revenue",
			compiled_request=_compiled_request(),
			compiler_contract=_compiler_contract(),
			step_family_id="ranking_analytics",
			recent_messages=[],
		)

	def test_composite_deterministic_governed_report_path_remains_deterministic(self):
		called = {"runtime": False}

		def governed_report(**_kwargs):
			return {
				"ok": True,
				"tool_trace": [{"tool": "execute_report", "args": {"report_name": "Sales Analytics"}}],
				"agent_meta": {"engine": "governed_report_executor", "model": "none"},
			}

		def runtime_call(**_kwargs):
			called["runtime"] = True
			raise AssertionError("model fallback should not run for deterministic governed report path")

		composite_reads.execute_governed_report = governed_report
		composite_reads.call_qwen_runtime_chat = runtime_call
		result = self._execute_step()

		self.assertFalse(called["runtime"])
		self.assertNotIn("runtime_metadata_envelope", result.runtime_payload)
		self.assertNotIn("runtime_metadata_envelope", result.runtime_payload.get("agent_meta") or {})

	def test_composite_fallback_model_path_gets_governed_tool_runtime_envelope(self):
		composite_reads.execute_governed_report = lambda **_kwargs: {"ok": False, "tool_trace": [], "agent_meta": {}}
		composite_reads.call_qwen_runtime_chat = lambda **_kwargs: {
			"ok": True,
			"answer_text": "Composite fallback answer.",
			"tool_trace": [{"tool": "compiled_read_query"}],
			"agent_meta": {"model": "qwen-tool-runtime"},
		}
		result = self._execute_step()
		metadata = result.runtime_payload["runtime_metadata_envelope"]

		self.assertEqual(metadata["lane_class"], LANE_CLASS_GOVERNED_TOOL_RUNTIME)
		self.assertEqual(metadata["model_role"], ROLE_GOVERNED_TOOL_RUNTIME)
		self.assertTrue(metadata["fallback_used"])
		self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertEqual(result.runtime_payload["agent_meta"]["runtime_metadata_envelope"], metadata)
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])

	def test_fresh_query_compiled_read_helper_call_sites_are_all_annotated(self):
		text = FRESH_QUERY_INTERPRETER.read_text(encoding="utf-8")
		self.assertEqual(text.count("runtime_payload = call_qwen_runtime_chat("), 5)
		self.assertEqual(text.count("_attach_fresh_compiled_read_runtime_metadata("), 6)
		self.assertEqual(text.count("fallback_used=False"), 4)
		self.assertIn("fallback_used=True", text)

	def test_fresh_query_compiled_read_helper_metadata_success_and_fallback_state(self):
		success = fresh_query_interpreter._attach_fresh_compiled_read_runtime_metadata(
			{
				"ok": True,
				"answer_text": "Fresh compiled read answer.",
				"tool_trace": [{"tool": "compiled_read_query"}],
				"agent_meta": {"model": "qwen-tool-runtime"},
			},
			fallback_used=False,
		)
		success_metadata = success["runtime_metadata_envelope"]
		self.assertEqual(success["answer_text"], "Fresh compiled read answer.")
		self.assertEqual(success_metadata["lane_class"], LANE_CLASS_GOVERNED_TOOL_RUNTIME)
		self.assertEqual(success_metadata["model_role"], ROLE_GOVERNED_TOOL_RUNTIME)
		self.assertEqual(success_metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertTrue(validate_runtime_metadata_envelope(success_metadata)["valid"])

		fallback = fresh_query_interpreter._attach_fresh_compiled_read_runtime_metadata(
			{
				"ok": False,
				"answer_text": "",
				"tool_trace": [],
				"agent_meta": {"engine": "unavailable", "mode": "compiled_read_query"},
				"error": "runtime unavailable",
			},
			fallback_used=True,
			fallback_reason="runtime unavailable",
		)
		fallback_metadata = fallback["runtime_metadata_envelope"]
		self.assertTrue(fallback_metadata["fallback_used"])
		self.assertNotEqual(fallback_metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(fallback_metadata["strict_enforcement_ready"])
		self.assertTrue(validate_runtime_metadata_envelope(fallback_metadata)["valid"])

	def test_missing_model_metadata_is_not_strict_ready(self):
		payload = attach_governed_tool_runtime_metadata_to_payload(
			{"ok": True, "answer_text": "Answer", "tool_trace": [], "agent_meta": {}},
			lane_id="fresh_query_compiled_read_runtime",
			role_owner="fresh_query_interpreter",
			runtime_source="test_missing_model",
			fallback_used=False,
		)
		metadata = payload["runtime_metadata_envelope"]
		self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(metadata["strict_enforcement_ready"])
		self.assertIn("model_name", metadata["missing_fields"])

	def test_governed_tool_runtime_metadata_cannot_create_final_answer_business_authority(self):
		payload = attach_governed_tool_runtime_metadata_to_payload(
			{"ok": True, "answer_text": "Tool helper answer", "tool_trace": [], "agent_meta": {"model": "qwen-tool-runtime"}},
			lane_id="fresh_query_compiled_read_runtime",
			role_owner="fresh_query_interpreter",
			runtime_source="test_tool_runtime",
			authority_source="governed_erp_report",
			fallback_used=False,
		)
		envelope = payload["runtime_metadata_envelope"]
		session_doc = FakeSessionDoc()
		result = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="Tool helper answer",
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
