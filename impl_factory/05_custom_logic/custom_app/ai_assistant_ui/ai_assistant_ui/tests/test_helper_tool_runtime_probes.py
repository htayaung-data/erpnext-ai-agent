import json
import sys
import types
import unittest
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
frappe_module = sys.modules.setdefault("frappe", fake_frappe)
for _name, _value in {
	"get_all": fake_frappe.get_all,
	"conf": fake_frappe.conf,
	"local": fake_frappe.local,
	"db": fake_frappe.db,
	"get_doc": fake_frappe.get_doc,
	"log_error": fake_frappe.log_error,
	"DoesNotExistError": fake_frappe.DoesNotExistError,
	"ValidationError": fake_frappe.ValidationError,
}.items():
	if not hasattr(frappe_module, _name):
		setattr(frappe_module, _name, _value)

from ai_assistant_ui.qwen_chat import (
	artifact_narrative,
	clarification_system,
	composite_reads,
	fresh_query_interpreter,
	frontdoor_intent_gate,
)
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
	LANE_CLASS_MODEL_BACKED_HELPER,
	ROLE_GOVERNED_TOOL_RUNTIME,
	ROLE_MODEL_BACKED_HELPER,
	STRICT_STATUS_READY,
	validate_runtime_metadata_envelope,
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
		request_id="req-7fd",
		session_id="session-7fd",
		user_id="user@example.com",
		site_name="erpai_prj1",
		raw_message="helper provenance probe",
	)


def _followup():
	return build_followup_resolution_contract(
		request_id="req-7fd",
		mode="helper_runtime_probe",
		requested_modes=["helper_runtime_probe"],
		depends_on_grounded_turn=False,
		self_contained=True,
		latest_grounded_turn_available=False,
		reason="EC-7F-D probe",
	)


def _execution_path():
	return ExecutionPath(
		request_id="req-7fd",
		path="helper_runtime_probe",
		reason="EC-7F-D probe",
		requires_runtime=False,
		grounded_required=False,
	)


def _compiled_request():
	return CompiledQueryRequestContract(
		request_id="compiled-7fd",
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
		request_id="compiled-7fd",
		session_id="session-7fd",
		capability_id="sales_read",
		selected_report="Sales Analytics",
		selected_report_family="ranking_analytics",
		completed_filters={},
		requested_dimensions=["Customer"],
		requested_metrics=["Revenue"],
		requested_time_scope="current_fiscal_year_to_date",
		decision="execute",
		clarification_required=False,
		compiler_reason="EC-7F-D probe",
		governed_resolution_details={},
		clarification_reason_type="",
		clarification_details={},
		extracted_slots={},
	)


def _frontdoor_contract():
	return SimpleNamespace(
		response_payload={"text": "Template fallback frontdoor answer."},
		intent_class="capability_question",
		response_mode="direct_answer",
		reason="EC-7F-D probe",
	)


def _assert_valid(testcase, envelope):
	validation = validate_runtime_metadata_envelope(envelope)
	testcase.assertTrue(validation["valid"], validation)


def _assert_strict_ready(testcase, envelope, *, lane_class, model_role):
	_assert_valid(testcase, envelope)
	testcase.assertEqual(envelope["lane_class"], lane_class)
	testcase.assertEqual(envelope["model_role"], model_role)
	testcase.assertEqual(envelope["strict_readiness_status"], STRICT_STATUS_READY)
	testcase.assertTrue(envelope["strict_enforcement_ready"])


def _assert_not_strict_ready(testcase, envelope):
	_assert_valid(testcase, envelope)
	testcase.assertNotEqual(envelope["strict_readiness_status"], STRICT_STATUS_READY)
	testcase.assertFalse(envelope["strict_enforcement_ready"])


class HelperToolRuntimeProbeTests(unittest.TestCase):
	def setUp(self):
		self._orig_frontdoor_render = frontdoor_intent_gate.call_qwen_runtime_frontdoor_render
		self._orig_clarification_chat = clarification_system.call_qwen_runtime_chat
		self._orig_artifact_chat = artifact_narrative.call_qwen_runtime_chat
		self._orig_composite_report = composite_reads.execute_governed_report
		self._orig_composite_chat = composite_reads.call_qwen_runtime_chat
		self._orig_build_artifact = composite_reads.build_normalized_family_artifact
		self._orig_validate_artifact = composite_reads.validate_normalized_family_artifact
		self._orig_fresh_compile = fresh_query_interpreter.compile_from_fresh_query_message
		self._orig_fresh_report = fresh_query_interpreter.execute_governed_report
		self._orig_fresh_chat = fresh_query_interpreter.call_qwen_runtime_chat
		self._orig_fresh_build_artifact = fresh_query_interpreter.build_normalized_family_artifact
		self._orig_fresh_validate_artifact = fresh_query_interpreter.validate_normalized_family_artifact
		self._orig_fresh_render = fresh_query_interpreter.render_normalized_family_response
		self._orig_fresh_semantic_validation = fresh_query_interpreter.validate_compiled_semantic_result
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
		frontdoor_intent_gate.call_qwen_runtime_frontdoor_render = self._orig_frontdoor_render
		clarification_system.call_qwen_runtime_chat = self._orig_clarification_chat
		artifact_narrative.call_qwen_runtime_chat = self._orig_artifact_chat
		composite_reads.execute_governed_report = self._orig_composite_report
		composite_reads.call_qwen_runtime_chat = self._orig_composite_chat
		composite_reads.build_normalized_family_artifact = self._orig_build_artifact
		composite_reads.validate_normalized_family_artifact = self._orig_validate_artifact
		fresh_query_interpreter.compile_from_fresh_query_message = self._orig_fresh_compile
		fresh_query_interpreter.execute_governed_report = self._orig_fresh_report
		fresh_query_interpreter.call_qwen_runtime_chat = self._orig_fresh_chat
		fresh_query_interpreter.build_normalized_family_artifact = self._orig_fresh_build_artifact
		fresh_query_interpreter.validate_normalized_family_artifact = self._orig_fresh_validate_artifact
		fresh_query_interpreter.render_normalized_family_response = self._orig_fresh_render
		fresh_query_interpreter.validate_compiled_semantic_result = self._orig_fresh_semantic_validation

	def _execute_composite_step(self):
		return composite_reads._execute_composite_step(
			session_id="session-7fd",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="top customers by revenue",
			compiled_request=_compiled_request(),
			compiler_contract=_compiler_contract(),
			step_family_id="ranking_analytics",
			recent_messages=[],
		)

	def _fresh_query_pipeline(self):
		return {
			"request_id": "req-7fd-fresh-path",
			"phase4_latency_breakdown": {},
			"response_policy_contract": {},
			"compiled_query_request": _compiled_request().to_payload(),
			"fresh_query_compiler": _compiler_contract().to_payload(),
		}

	def test_frontdoor_render_success_and_missing_model_metadata_probes(self):
		def successful_runtime(**_kwargs):
			return {
				"ok": True,
				"answer_text": "Exact frontdoor render text.",
				"agent_meta": {"model": "qwen-helper-render"},
			}

		frontdoor_intent_gate.call_qwen_runtime_frontdoor_render = successful_runtime
		payload = frontdoor_intent_gate.render_front_door_answer(
			request_id="req-7fd-frontdoor",
			session_id="session-7fd",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="what can you do",
			recent_messages=[],
			grounded_context_available=False,
			frontdoor_contract=_frontdoor_contract(),
		).to_payload()
		self.assertEqual(payload["answer_text"], "Exact frontdoor render text.")
		_assert_strict_ready(
			self,
			payload["runtime_metadata_envelope"],
			lane_class=LANE_CLASS_MODEL_BACKED_HELPER,
			model_role=ROLE_MODEL_BACKED_HELPER,
		)

		frontdoor_intent_gate.call_qwen_runtime_frontdoor_render = lambda **_kwargs: {
			"ok": True,
			"answer_text": "Missing model render text.",
			"agent_meta": {},
		}
		payload = frontdoor_intent_gate.render_front_door_answer(
			request_id="req-7fd-frontdoor-missing",
			session_id="session-7fd",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="what can you do",
			recent_messages=[],
			grounded_context_available=False,
			frontdoor_contract=_frontdoor_contract(),
		).to_payload()
		self.assertEqual(payload["answer_text"], "Missing model render text.")
		_assert_not_strict_ready(self, payload["runtime_metadata_envelope"])
		self.assertIn("model_name", payload["runtime_metadata_envelope"]["missing_fields"])

	def test_frontdoor_render_runtime_failure_is_visible_and_non_strict(self):
		def failing_runtime(**_kwargs):
			raise frontdoor_intent_gate.QwenRuntimeClientError("renderer unavailable")

		frontdoor_intent_gate.call_qwen_runtime_frontdoor_render = failing_runtime
		payload = frontdoor_intent_gate.render_front_door_answer(
			request_id="req-7fd-frontdoor-failure",
			session_id="session-7fd",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="what can you do",
			recent_messages=[],
			grounded_context_available=False,
			frontdoor_contract=_frontdoor_contract(),
		).to_payload()
		self.assertEqual(payload["answer_text"], "Template fallback frontdoor answer.")
		self.assertTrue(payload["runtime_metadata_envelope"]["fallback_used"])
		self.assertEqual(payload["runtime_metadata_envelope"]["fallback_reason"], "renderer unavailable")
		_assert_not_strict_ready(self, payload["runtime_metadata_envelope"])

	def test_clarification_system_success_and_template_fallback_probes(self):
		clarification_system.call_qwen_runtime_chat = lambda **_kwargs: {
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
		question = clarification_system.generate_ai_clarification(
			request_id="req-7fd-clarify",
			session_id="session-7fd",
			user_id="user@example.com",
			site_name="erpai_prj1",
			raw_message="that one",
			context={"family_id": "aging"},
		)
		self.assertIsNotNone(question)
		payload = clarification_system.build_clarification_response(question)
		self.assertEqual(payload["answer_text"], "Do you want the current report or a new period?")
		_assert_strict_ready(
			self,
			payload["runtime_metadata_envelope"],
			lane_class=LANE_CLASS_MODEL_BACKED_HELPER,
			model_role=ROLE_MODEL_BACKED_HELPER,
		)

		clarification_system.call_qwen_runtime_chat = lambda **_kwargs: {
			"ok": True,
			"answer_text": json.dumps(
				{
					"question": "Which report should I use?",
					"options": ["Sales", "Receivables"],
					"context_type": "scope",
				}
			),
			"agent_meta": {},
		}
		question = clarification_system.generate_ai_clarification(
			request_id="req-7fd-clarify-missing-model",
			session_id="session-7fd",
			user_id="user@example.com",
			site_name="erpai_prj1",
			raw_message="that report",
			context={"family_id": "sales"},
		)
		self.assertIsNotNone(question)
		payload = clarification_system.build_clarification_response(question)
		self.assertEqual(payload["answer_text"], "Which report should I use?")
		_assert_not_strict_ready(self, payload["runtime_metadata_envelope"])
		self.assertIn("model_name", payload["runtime_metadata_envelope"]["missing_fields"])

		def failing_runtime(**_kwargs):
			raise RuntimeError("clarification runtime unavailable")

		clarification_system.call_qwen_runtime_chat = failing_runtime
		question = clarification_system.generate_clarification(
			request_id="req-7fd-clarify-failure",
			session_id="session-7fd",
			user_id="user@example.com",
			site_name="erpai_prj1",
			raw_message="that one",
			context={},
			use_ai_first=True,
		)
		payload = clarification_system.build_clarification_response(question)
		self.assertTrue(payload["answer_text"])
		_assert_not_strict_ready(self, payload["runtime_metadata_envelope"])

		template = clarification_system.ClarificationQuestion(
			question="Which period should I use?",
			options=["This month", "This year"],
			context_type="scope",
			generation_method="template",
		)
		payload = clarification_system.build_clarification_response(template)
		self.assertEqual(payload["answer_text"], "Which period should I use?")
		_assert_not_strict_ready(self, payload["runtime_metadata_envelope"])

	def test_artifact_narrative_success_missing_model_and_runtime_failure_probes(self):
		artifact_narrative.call_qwen_runtime_chat = lambda **_kwargs: {
			"ok": True,
			"answer_text": "Exact artifact narrative.",
			"agent_meta": {"model": "qwen-helper-narrative"},
		}
		payload = artifact_narrative.narrate_governed_artifact(
			session_id="session-7fd",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="summarize this artifact",
			request_id="req-7fd-artifact",
			artifact_context={"family_id": "ranking", "source_reports": ["Sales Order"]},
			response_policy={},
		)
		self.assertEqual(payload["answer_text"], "Exact artifact narrative.")
		_assert_strict_ready(
			self,
			payload["runtime_metadata_envelope"],
			lane_class=LANE_CLASS_MODEL_BACKED_HELPER,
			model_role=ROLE_MODEL_BACKED_HELPER,
		)

		artifact_narrative.call_qwen_runtime_chat = lambda **_kwargs: {
			"ok": True,
			"answer_text": "Missing model artifact narrative.",
			"agent_meta": {},
		}
		payload = artifact_narrative.narrate_governed_artifact(
			session_id="session-7fd",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="summarize this artifact",
			request_id="req-7fd-artifact-missing",
			artifact_context={"family_id": "ranking"},
			response_policy={},
		)
		_assert_not_strict_ready(self, payload["runtime_metadata_envelope"])
		self.assertIn("model_name", payload["runtime_metadata_envelope"]["missing_fields"])

		def failing_runtime(**_kwargs):
			raise artifact_narrative.QwenRuntimeClientError("narrative unavailable")

		artifact_narrative.call_qwen_runtime_chat = failing_runtime
		payload = artifact_narrative.narrate_governed_artifact(
			session_id="session-7fd",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="summarize this artifact",
			request_id="req-7fd-artifact-failure",
			artifact_context={"family_id": "ranking"},
			response_policy={},
		)
		self.assertFalse(payload["ok"])
		self.assertEqual(payload["answer_text"], "")
		self.assertTrue(payload["runtime_metadata_envelope"]["fallback_used"])
		_assert_not_strict_ready(self, payload["runtime_metadata_envelope"])

	def test_composite_deterministic_path_remains_deterministic(self):
		called = {"runtime": False}
		composite_reads.execute_governed_report = lambda **_kwargs: {
			"ok": True,
			"tool_trace": [{"tool": "execute_report", "args": {"report_name": "Sales Analytics"}}],
			"agent_meta": {"engine": "governed_report_executor", "model": "none"},
		}

		def runtime_call(**_kwargs):
			called["runtime"] = True
			raise AssertionError("model fallback should not run for deterministic governed report path")

		composite_reads.call_qwen_runtime_chat = runtime_call
		result = self._execute_composite_step()
		self.assertFalse(called["runtime"])
		self.assertNotIn("runtime_metadata_envelope", result.runtime_payload)
		self.assertNotIn("runtime_metadata_envelope", result.runtime_payload.get("agent_meta") or {})

	def test_composite_fallback_and_runtime_failure_governed_tool_metadata_is_non_strict(self):
		composite_reads.execute_governed_report = lambda **_kwargs: {"ok": False, "tool_trace": [], "agent_meta": {}}
		composite_reads.call_qwen_runtime_chat = lambda **_kwargs: {
			"ok": True,
			"answer_text": "Composite fallback answer.",
			"tool_trace": [{"tool": "compiled_read_query"}],
			"agent_meta": {"model": "qwen-tool-runtime"},
		}
		result = self._execute_composite_step()
		metadata = result.runtime_payload["runtime_metadata_envelope"]
		self.assertEqual(result.runtime_payload["answer_text"], "Composite fallback answer.")
		self.assertEqual(metadata["lane_class"], LANE_CLASS_GOVERNED_TOOL_RUNTIME)
		self.assertEqual(metadata["model_role"], ROLE_GOVERNED_TOOL_RUNTIME)
		self.assertTrue(metadata["fallback_used"])
		_assert_not_strict_ready(self, metadata)

		def failing_runtime(**_kwargs):
			raise composite_reads.QwenRuntimeClientError("compiled read unavailable")

		composite_reads.call_qwen_runtime_chat = failing_runtime
		result = self._execute_composite_step()
		metadata = result.runtime_payload["runtime_metadata_envelope"]
		self.assertFalse(result.runtime_payload["ok"])
		self.assertEqual(result.runtime_payload["error"], "compiled read unavailable")
		self.assertTrue(metadata["fallback_used"])
		self.assertEqual(metadata["fallback_reason"], "compiled read unavailable")
		_assert_not_strict_ready(self, metadata)

	def test_fresh_query_compiled_read_runtime_success_missing_model_and_failure_probes(self):
		success = fresh_query_interpreter._attach_fresh_compiled_read_runtime_metadata(
			{
				"ok": True,
				"answer_text": "Fresh compiled read answer.",
				"tool_trace": [{"tool": "compiled_read_query"}],
				"agent_meta": {"model": "qwen-tool-runtime"},
			},
			fallback_used=False,
		)
		self.assertEqual(success["answer_text"], "Fresh compiled read answer.")
		_assert_strict_ready(
			self,
			success["runtime_metadata_envelope"],
			lane_class=LANE_CLASS_GOVERNED_TOOL_RUNTIME,
			model_role=ROLE_GOVERNED_TOOL_RUNTIME,
		)

		missing_model = fresh_query_interpreter._attach_fresh_compiled_read_runtime_metadata(
			{"ok": True, "answer_text": "Fresh answer", "tool_trace": [], "agent_meta": {}},
			fallback_used=False,
		)
		_assert_not_strict_ready(self, missing_model["runtime_metadata_envelope"])
		self.assertIn("model_name", missing_model["runtime_metadata_envelope"]["missing_fields"])

		failure = fresh_query_interpreter._attach_fresh_compiled_read_runtime_metadata(
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
		self.assertFalse(failure["ok"])
		self.assertEqual(failure["error"], "runtime unavailable")
		self.assertTrue(failure["runtime_metadata_envelope"]["fallback_used"])
		_assert_not_strict_ready(self, failure["runtime_metadata_envelope"])

	def test_fresh_query_compiled_read_real_call_path_fallback_has_non_strict_metadata(self):
		calls = {"governed_report": 0, "runtime_fallback": 0}
		fresh_query_interpreter.compile_from_fresh_query_message = lambda **_kwargs: self._fresh_query_pipeline()

		def governed_report_failure(**_kwargs):
			calls["governed_report"] += 1
			return {"ok": False, "tool_trace": [], "agent_meta": {}}

		def runtime_fallback(**_kwargs):
			calls["runtime_fallback"] += 1
			return {
				"ok": True,
				"answer_text": "Fresh query runtime fallback answer.",
				"tool_trace": [{"tool": "compiled_read_query"}],
				"agent_meta": {"model": "qwen-tool-runtime"},
			}

		fresh_query_interpreter.execute_governed_report = governed_report_failure
		fresh_query_interpreter.call_qwen_runtime_chat = runtime_fallback
		fresh_query_interpreter.build_normalized_family_artifact = lambda **_kwargs: SimpleNamespace(
			artifact_contract=PayloadObject(payload={"type": "artifact", "family_id": "ranking_analytics"}),
			family_id="ranking_analytics",
			errors=[],
			warnings=[],
			status="pass",
		)
		fresh_query_interpreter.validate_normalized_family_artifact = lambda **_kwargs: PayloadObject(
			payload={"type": "validation", "status": "pass"}
		)
		fresh_query_interpreter.render_normalized_family_response = lambda **_kwargs: SimpleNamespace(contract=None)
		fresh_query_interpreter.validate_compiled_semantic_result = lambda **_kwargs: PayloadObject(
			payload={"type": "semantic_validation", "status": "pass", "errors": [], "warnings": []}
		)

		result = fresh_query_interpreter.execute_compiled_fresh_query_message(
			session_id="session-7fd",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="top customers by revenue",
			recent_messages=[],
		)
		runtime_payload = result["runtime_payload"]
		metadata = runtime_payload["runtime_metadata_envelope"]

		self.assertEqual(calls, {"governed_report": 1, "runtime_fallback": 1})
		self.assertEqual(runtime_payload["answer_text"], "Fresh query runtime fallback answer.")
		self.assertEqual(metadata["lane_id"], "fresh_query_compiled_read_runtime")
		self.assertEqual(metadata["lane_class"], LANE_CLASS_GOVERNED_TOOL_RUNTIME)
		self.assertEqual(metadata["model_role"], ROLE_GOVERNED_TOOL_RUNTIME)
		self.assertTrue(metadata["fallback_used"])
		self.assertEqual(metadata["fallback_reason"], "governed_report_runtime_unavailable")
		_assert_not_strict_ready(self, metadata)

		probe_envelope = dict(metadata)
		probe_envelope["authority_source"] = "governed_erp_report"
		session_doc = FakeSessionDoc()
		emission = emit_authorized_assistant_answer(
			session_doc=session_doc,
			answer_text="Fresh query runtime fallback answer.",
			answer_type=ANSWER_TYPE_BUSINESS_FACTUAL,
			append_message=_append_message,
			append_tool_payload=_append_tool_payload,
			assistant_text_payload=_assistant_text_payload,
			interaction_contract=_interaction(),
			followup_resolution=_followup(),
			execution_path=_execution_path(),
			runtime_trace_payload={"agent_meta": {"runtime_metadata_envelope": probe_envelope}},
			authority_context={"runtime_metadata_envelope": probe_envelope},
		)
		self.assertFalse(emission.emitted)
		self.assertTrue(emission.blocked)
		self.assertEqual([message["role"] for message in session_doc.messages], ["tool"])
		self.assertNotEqual(emission.final_answer_authority.get("authority_source"), "governed_erp_report")

	def test_helper_and_governed_tool_metadata_cannot_create_business_authority(self):
		for envelope in (
			frontdoor_intent_gate.FrontDoorRenderResult(
				ok=True,
				answer_text="Helper-rendered business text.",
				agent_meta={"model": "qwen-helper-render"},
			).to_payload()["runtime_metadata_envelope"],
			attach_governed_tool_runtime_metadata_to_payload(
				{
					"ok": True,
					"answer_text": "Tool helper answer.",
					"tool_trace": [],
					"agent_meta": {"model": "qwen-tool-runtime"},
				},
				lane_id="fresh_query_compiled_read_runtime",
				role_owner="fresh_query_interpreter",
				runtime_source="ec_7f_d_probe",
				authority_source="governed_erp_report",
				fallback_used=False,
			)["runtime_metadata_envelope"],
		):
			probe_envelope = dict(envelope)
			probe_envelope["authority_source"] = "governed_erp_report"
			session_doc = FakeSessionDoc()
			result = emit_authorized_assistant_answer(
				session_doc=session_doc,
				answer_text="Probe business answer.",
				answer_type=ANSWER_TYPE_BUSINESS_FACTUAL,
				append_message=_append_message,
				append_tool_payload=_append_tool_payload,
				assistant_text_payload=_assistant_text_payload,
				interaction_contract=_interaction(),
				followup_resolution=_followup(),
				execution_path=_execution_path(),
				runtime_trace_payload={"agent_meta": {"runtime_metadata_envelope": probe_envelope}},
				authority_context={"runtime_metadata_envelope": probe_envelope},
			)
			self.assertFalse(result.emitted)
			self.assertTrue(result.blocked)
			self.assertEqual([message["role"] for message in session_doc.messages], ["tool"])
			self.assertEqual(session_doc.messages[0]["content"]["emission_status"], EMISSION_STATUS_BLOCKED)
			self.assertNotEqual(result.final_answer_authority.get("authority_source"), "governed_erp_report")


if __name__ == "__main__":
	unittest.main()
