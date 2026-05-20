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
fake_frappe.get_traceback = lambda: ""
fake_frappe.log_error = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat import fresh_query_interpreter as fresh_query
from ai_assistant_ui.qwen_chat import frontdoor_intent_gate as frontdoor
from ai_assistant_ui.qwen_chat import semantic_interpreter as followup
from ai_assistant_ui.qwen_chat import semantic_reasoning_activation as reasoning_activation
from ai_assistant_ui.qwen_chat import semantic_repair_intent as repair_intent
from ai_assistant_ui.qwen_chat.runtime_metadata_contract import STRICT_STATUS_READY, validate_runtime_metadata_envelope


AGENT_META = {"model": "qwen-light-semantic", "telemetry": {"fallback_used": False}}
MISSING_MODEL_AGENT_META = {"telemetry": {"fallback_used": False}}


class LightSemanticRuntimeProbeTests(unittest.TestCase):
	def setUp(self):
		self._originals = []

	def tearDown(self):
		for module, attr, value in reversed(self._originals):
			setattr(module, attr, value)

	def patch_runtime(self, module, attr, replacement):
		self._originals.append((module, attr, getattr(module, attr)))
		setattr(module, attr, replacement)

	def assert_strict_ready_payload(self, payload, *, lane_id):
		metadata = payload["runtime_metadata_envelope"]
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		self.assertEqual(metadata["lane_id"], lane_id)
		self.assertEqual(metadata["lane_class"], "ai_semantic")
		self.assertEqual(metadata["model_role"], "light_semantic")
		self.assertEqual(metadata["model_name"], "qwen-light-semantic")
		self.assertFalse(metadata["fallback_used"])
		self.assertEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertTrue(metadata["strict_enforcement_ready"])

	def assert_not_strict_payload(self, payload, *, fallback_reason=None):
		metadata = payload["runtime_metadata_envelope"]
		self.assertTrue(validate_runtime_metadata_envelope(metadata)["valid"])
		self.assertNotEqual(metadata["strict_readiness_status"], STRICT_STATUS_READY)
		self.assertFalse(metadata["strict_enforcement_ready"])
		if fallback_reason is not None:
			self.assertTrue(payload["fallback_used"])
			self.assertEqual(payload["fallback_reason"], fallback_reason)
			self.assertTrue(metadata["fallback_used"])
			self.assertEqual(metadata["fallback_reason"], fallback_reason)

	def frontdoor_result(self, *, agent_meta=AGENT_META, interpretation=None, raises=False):
		def runtime_call(**_kwargs):
			if raises:
				raise frontdoor.QwenRuntimeClientError("frontdoor runtime unavailable")
			return {
				"interpretation": interpretation
				or {"intent_class": "route_onward", "confidence": 0.93, "reason": "ERP request"},
				"agent_meta": dict(agent_meta),
			}

		self.patch_runtime(frontdoor, "call_qwen_runtime_frontdoor_interpretation", runtime_call)
		return frontdoor.interpret_front_door_semantically(
			request_id="probe-frontdoor",
			session_id="session-probe",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="show sales",
			recent_messages=[],
			grounded_context_available=False,
		)

	def fresh_query_result(self, *, agent_meta=AGENT_META, interpretation=None, raises=False):
		def runtime_call(**_kwargs):
			if raises:
				raise fresh_query.QwenRuntimeClientError("fresh query runtime unavailable")
			return {
				"interpretation": interpretation
				or {
					"intent_class": "financial_summary",
					"candidate_capability_ids": ["sales_read"],
					"candidate_reports": ["Sales Analytics"],
					"requested_metrics": ["Grand Total"],
					"confidence": 0.91,
				},
				"agent_meta": dict(agent_meta),
			}

		self.patch_runtime(fresh_query, "call_qwen_runtime_fresh_query_interpretation", runtime_call)
		return fresh_query.interpret_fresh_query_semantically(
			request_id="probe-fresh",
			session_id="session-probe",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="show sales total",
			recent_messages=[],
		)

	def followup_result(self, *, agent_meta=AGENT_META, interpretation=None, raises=False):
		def runtime_call(**_kwargs):
			if raises:
				raise followup.QwenRuntimeClientError("follow-up runtime unavailable")
			return {
				"interpretation": interpretation
				or {
					"requested_modes": ["column_projection"],
					"requested_columns": ["grand_total"],
					"confidence": 0.91,
					"reason": "project grounded result columns",
				},
				"agent_meta": dict(agent_meta),
			}

		self.patch_runtime(followup, "call_qwen_runtime_followup_interpretation", runtime_call)
		return followup.interpret_followup_semantically(
			request_id="probe-followup",
			session_id="session-probe",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="show only grand total",
			recent_messages=[],
			latest_grounded_turn={
				"source_name": "Sales Analytics",
				"returned_schema": ["Customer", "Grand Total"],
				"artifact_family_id": "ranking_analytics",
				"artifact_source_reports": ["Sales Analytics"],
			},
			latest_assistant_payload={},
		)

	def reasoning_result(self, *, agent_meta=AGENT_META, interpretation=None, raises=False):
		def runtime_call(**_kwargs):
			if raises:
				raise reasoning_activation.QwenRuntimeClientError("reasoning activation runtime unavailable")
			return {
				"interpretation": interpretation
				or {
					"reasoning_type": "explain_variance",
					"detail_level": "default",
					"presentation_style": "default",
					"confidence": 0.91,
					"reason": "explain current result",
				},
				"agent_meta": dict(agent_meta),
			}

		self.patch_runtime(reasoning_activation, "call_qwen_runtime_reasoning_activation_interpretation", runtime_call)
		return reasoning_activation.interpret_reasoning_activation_semantically(
			request_id="probe-reasoning-activation",
			session_id="session-probe",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="explain the current result",
			recent_messages=[],
			latest_grounded_turn={},
			latest_family_artifact={},
			latest_assistant_payload={},
			activation_contract={
				"activation_state": "eligible",
				"allowed_reasoning_types": ["explain_variance"],
				"grounded_context_available": False,
			},
		)

	def repair_result(self, *, agent_meta=AGENT_META, interpretation=None, raises=False):
		def runtime_call(**_kwargs):
			if raises:
				raise repair_intent.QwenRuntimeClientError("repair runtime unavailable")
			return {
				"interpretation": interpretation
				or {
					"repair_intent_type": "guidance_request",
					"guidance_topic": "scope",
					"confidence": 0.91,
					"reason": "user asked for recovery guidance",
				},
				"agent_meta": dict(agent_meta),
			}

		self.patch_runtime(repair_intent, "call_qwen_runtime_repair_intent_interpretation", runtime_call)
		return repair_intent.interpret_repair_intent_semantically(
			request_id="probe-repair",
			session_id="session-probe",
			user_id="user@example.com",
			site_name="erpai_prj1",
			message="help me recover this request",
			recent_messages=[],
			latest_recovery_contract={
				"recovery_state": "available",
				"available_recovery_actions": ["retry_with_clearer_scope"],
				"recommended_recovery_action": "retry_with_clearer_scope",
			},
			latest_grounded_turn={},
			latest_assistant_payload={},
		)

	def test_success_with_complete_metadata_can_be_strict_ready_for_all_light_semantic_interpreters(self):
		cases = [
			("frontdoor_semantic_classification", self.frontdoor_result),
			("fresh_query_interpretation", self.fresh_query_result),
			("followup_interpretation", self.followup_result),
			("semantic_reasoning_activation", self.reasoning_result),
			("semantic_repair_intent", self.repair_result),
		]
		for lane_id, factory in cases:
			with self.subTest(lane_id=lane_id):
				payload = factory().to_payload()
				self.assertEqual(payload["status"], "accepted")
				self.assert_strict_ready_payload(payload, lane_id=lane_id)

	def test_missing_model_metadata_cannot_be_strict_ready_for_all_light_semantic_interpreters(self):
		cases = [self.frontdoor_result, self.fresh_query_result, self.followup_result, self.reasoning_result, self.repair_result]
		for factory in cases:
			with self.subTest(factory=factory.__name__):
				payload = factory(agent_meta=MISSING_MODEL_AGENT_META).to_payload()
				self.assertEqual(payload["status"], "accepted")
				self.assert_not_strict_payload(payload)
				self.assertIn("model_name", payload["runtime_metadata_envelope"]["missing_fields"])

	def test_degraded_invalid_low_confidence_and_not_applicable_paths_are_not_strict_ready(self):
		cases = [
			(
				self.frontdoor_result(interpretation={"intent_class": "not_registered", "confidence": 0.95, "reason": "bad"}),
				"invalid_response",
				"semantic_status_invalid_response",
			),
			(
				self.fresh_query_result(
					interpretation={
						"intent_class": "financial_summary",
						"candidate_capability_ids": ["sales_read"],
						"candidate_reports": ["Sales Analytics"],
						"requested_metrics": ["Grand Total"],
						"confidence": 0.2,
					}
				),
				"low_confidence",
				"semantic_status_low_confidence",
			),
			(
				self.followup_result(interpretation={"requested_modes": ["column_projection"], "confidence": 0.2, "requested_columns": ["grand_total"]}),
				"low_confidence",
				"semantic_status_low_confidence",
			),
			(
				self.reasoning_result(interpretation={"reasoning_type": "not_allowed", "confidence": 0.91}),
				"rejected",
				"semantic_status_rejected",
			),
			(
				self.repair_result(interpretation={"repair_intent_type": "not_applicable", "confidence": 0.91, "reason": "not repair"}),
				"not_applicable",
				"semantic_status_not_applicable",
			),
		]
		for result, status, fallback_reason in cases:
			with self.subTest(status=status):
				payload = result.to_payload()
				self.assertEqual(payload["status"], status)
				self.assert_not_strict_payload(payload, fallback_reason=fallback_reason)

	def test_runtime_errors_are_not_strict_ready_for_all_light_semantic_interpreters(self):
		cases = [self.frontdoor_result, self.fresh_query_result, self.followup_result, self.reasoning_result, self.repair_result]
		for factory in cases:
			with self.subTest(factory=factory.__name__):
				payload = factory(raises=True).to_payload()
				self.assertEqual(payload["status"], "runtime_error")
				self.assert_not_strict_payload(payload, fallback_reason="semantic_status_runtime_error")
				self.assertTrue(payload["runtime_error"])


if __name__ == "__main__":
	unittest.main()