from __future__ import annotations

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

from ai_assistant_ui.qwen_chat import (
	compiled_support,
	entity_followup_support,
	local_followup_support,
	natural_business_understanding_governed_requery_activation as nbu_governed_requery,
	natural_business_understanding_service_activation as nbu_service_activation,
	service,
	visible_context_followup_activation,
	visible_context_trace_inspection,
)
from ai_assistant_ui.qwen_chat.authorized_emission import (
	ANSWER_TYPE_CONTROL,
	ANSWER_TYPE_ERROR,
	ANSWER_TYPE_GOVERNED_REPORT,
	ANSWER_TYPE_POLICY_BOUNDARY,
)
from ai_assistant_ui.qwen_chat.final_answer_emission_closure_checkpoint import (
	build_final_answer_emission_closure_checkpoint_report,
)
from ai_assistant_ui.qwen_chat.final_answer_remaining_append_mapping import (
	build_final_answer_remaining_append_mapping_report,
)
from ai_assistant_ui.qwen_chat.lanes import (
	artifact_boundary_lane,
	clarification_lane,
	legacy_runtime_lane,
	runtime_gate_lane,
)
from ai_assistant_ui.qwen_chat.runtime_metadata_contract import (
	LANE_CLASS_CONTROL_META,
	LANE_CLASS_DETERMINISTIC_REPORT,
	LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT,
	LANE_CLASS_ERROR_FALLBACK,
	LANE_CLASS_POLICY_BOUNDARY,
	ROLE_CONTROL_META,
	ROLE_DETERMINISTIC,
	ROLE_NOT_APPLICABLE,
	ROLE_POLICY_BOUNDARY,
	STRICT_STATUS_NOT_APPLICABLE,
	validate_runtime_metadata_envelope,
)


PROJECT_ROOT = Path(__file__).resolve().parents[6]


def _assert_valid(testcase: unittest.TestCase, envelope: dict) -> None:
	validation = validate_runtime_metadata_envelope(envelope)
	testcase.assertTrue(validation["valid"], validation)
	testcase.assertIn("authority_source", envelope)
	testcase.assertTrue(str(envelope.get("authority_source") or "").strip())
	testcase.assertEqual(envelope.get("strict_readiness_status"), STRICT_STATUS_NOT_APPLICABLE)
	testcase.assertFalse(envelope.get("strict_enforcement_ready"))


def _deterministic_envelopes() -> list[dict]:
	return [
		compiled_support._compiled_runtime_metadata_envelope(answer_type=ANSWER_TYPE_GOVERNED_REPORT),
		legacy_runtime_lane._legacy_runtime_metadata_envelope(
			answer_type=ANSWER_TYPE_GOVERNED_REPORT,
			mode="legacy_runtime",
		),
		artifact_boundary_lane._artifact_boundary_metadata_envelope(
			answer_type=ANSWER_TYPE_GOVERNED_REPORT,
			answer_mode="grounded_evidence_answer",
		),
		local_followup_support._local_followup_metadata_envelope(answer_mode="local_grounded_transform"),
		entity_followup_support._entity_followup_metadata_envelope(
			answer_type=ANSWER_TYPE_GOVERNED_REPORT,
			answer_mode="entity_followup_detail",
			authority_source="deterministic_tool",
		),
		nbu_governed_requery._nbu_governed_requery_metadata_envelope(
			answer_selection_mode="direct_evidence_first",
		),
		visible_context_followup_activation._visible_context_runtime_metadata_envelope(
			answer_type="visible_context_answer",
			answer_mode="visible_context_answer",
		),
	]


def _policy_boundary_envelopes() -> list[dict]:
	return [
		runtime_gate_lane._runtime_gate_metadata_envelope(answer_mode="runtime_gate_boundary"),
		compiled_support._compiled_runtime_metadata_envelope(answer_type=ANSWER_TYPE_POLICY_BOUNDARY),
		legacy_runtime_lane._legacy_runtime_metadata_envelope(
			answer_type=ANSWER_TYPE_POLICY_BOUNDARY,
			mode="legacy_runtime_boundary",
		),
		artifact_boundary_lane._artifact_boundary_metadata_envelope(
			answer_type=ANSWER_TYPE_POLICY_BOUNDARY,
			answer_mode="artifact_boundary_refusal",
		),
		visible_context_followup_activation._visible_context_runtime_metadata_envelope(
			answer_type=ANSWER_TYPE_POLICY_BOUNDARY,
			answer_mode="visible_context_boundary",
		),
		service._service_policy_boundary_metadata_envelope(answer_mode="service_out_of_scope_domain_boundary"),
	]


def _control_envelopes() -> list[dict]:
	return [
		compiled_support._compiled_runtime_metadata_envelope(
			answer_type=ANSWER_TYPE_CONTROL,
			control_meta_authority={"authority_source": "control_meta"},
		),
		clarification_lane._clarification_runtime_metadata_envelope(answer_mode="clarification_show_options"),
		nbu_service_activation._nbu_safe_response_metadata_envelope(
			activation_mode="show_supported_options",
		),
		visible_context_followup_activation._visible_context_runtime_metadata_envelope(
			answer_type=ANSWER_TYPE_CONTROL,
			answer_mode="visible_context_clarification",
		),
		visible_context_trace_inspection._trace_inspection_runtime_metadata_envelope(),
		service._service_control_metadata_envelope(
			answer_mode="service_compound_stop",
			authority={"authority_source": "control_meta"},
		),
	]


def _error_fallback_envelopes() -> list[dict]:
	return [
		compiled_support._compiled_runtime_metadata_envelope(
			answer_type=ANSWER_TYPE_ERROR,
			control_meta_authority={"authority_source": "error_fallback", "reason": "compiled runtime failed"},
		),
		legacy_runtime_lane._legacy_runtime_metadata_envelope(
			answer_type=ANSWER_TYPE_ERROR,
			mode="legacy_runtime_error",
			error="runtime unavailable",
		),
		entity_followup_support._entity_followup_metadata_envelope(
			answer_type=ANSWER_TYPE_ERROR,
			answer_mode="entity_followup_error",
			authority_source="error_fallback",
		),
	]


class DeterministicControlRuntimeMetadataProbeTests(unittest.TestCase):
	def test_deterministic_report_and_visible_context_metadata_is_covered_not_ai_strict_ready(self):
		expected = {
			"compiled_support_result_answer": LANE_CLASS_DETERMINISTIC_REPORT,
			"legacy_runtime_business_or_boundary_answer": LANE_CLASS_DETERMINISTIC_REPORT,
			"artifact_boundary": LANE_CLASS_DETERMINISTIC_REPORT,
			"local_followup_transform": LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT,
			"entity_followup": LANE_CLASS_DETERMINISTIC_REPORT,
			"nbu_governed_requery_entity_detail": LANE_CLASS_DETERMINISTIC_REPORT,
			"visible_context_followup": LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT,
		}
		seen = set()
		for envelope in _deterministic_envelopes():
			_assert_valid(self, envelope)
			self.assertEqual(envelope["metadata_status"], "covered")
			self.assertEqual(envelope["model_role"], ROLE_DETERMINISTIC)
			self.assertEqual(envelope["preflight_status"], "passed")
			self.assertEqual(envelope["lane_class"], expected[envelope["lane_id"]])
			seen.add(envelope["lane_id"])
		self.assertEqual(seen, set(expected))

	def test_policy_boundary_metadata_is_bounded_and_not_ai_strict_ready(self):
		seen = set()
		for envelope in _policy_boundary_envelopes():
			_assert_valid(self, envelope)
			self.assertEqual(envelope["lane_class"], LANE_CLASS_POLICY_BOUNDARY)
			self.assertEqual(envelope["model_role"], ROLE_POLICY_BOUNDARY)
			self.assertEqual(envelope["authority_source"], "policy_boundary")
			self.assertEqual(envelope["preflight_status"], "bounded")
			self.assertEqual(envelope["metadata_status"], "covered")
			seen.add(envelope["lane_id"])
		self.assertEqual(
			seen,
			{
				"runtime_gate",
				"compiled_support_result_answer",
				"legacy_runtime_business_or_boundary_answer",
				"artifact_boundary",
				"visible_context_followup",
				"service_policy_control_responses",
			},
		)

	def test_control_and_error_fallback_metadata_has_explicit_non_business_authority(self):
		for envelope in _control_envelopes():
			_assert_valid(self, envelope)
			self.assertEqual(envelope["lane_class"], LANE_CLASS_CONTROL_META)
			self.assertEqual(envelope["model_role"], ROLE_CONTROL_META)
			self.assertIn(envelope["authority_source"], {"control_meta", "trace_debug"})
			self.assertEqual(envelope["preflight_status"], "passed")
		for envelope in _error_fallback_envelopes():
			_assert_valid(self, envelope)
			self.assertEqual(envelope["lane_class"], LANE_CLASS_ERROR_FALLBACK)
			self.assertEqual(envelope["model_role"], ROLE_NOT_APPLICABLE)
			self.assertEqual(envelope["authority_source"], "error_fallback")
			self.assertEqual(envelope["preflight_status"], "passed")

	def test_no_deterministic_or_control_probe_silently_omits_authority_source(self):
		all_envelopes = (
			_deterministic_envelopes()
			+ _policy_boundary_envelopes()
			+ _control_envelopes()
			+ _error_fallback_envelopes()
		)
		self.assertGreaterEqual(len(all_envelopes), 20)
		for envelope in all_envelopes:
			_assert_valid(self, envelope)
			self.assertTrue(str(envelope.get("authority_source") or "").strip(), envelope)

	def test_blocked_missing_authority_and_visible_context_proofs_remain_green(self):
		closure = build_final_answer_emission_closure_checkpoint_report(root_path=PROJECT_ROOT)
		rows = {row["lane_id"]: row for row in closure["direct_no_leak_test_summary_by_lane"]}
		self.assertEqual(closure["visible_context_outer_call_site_proof"]["status"], "runtime_blocked_authority_probe_passed")
		for row in rows.values():
			self.assertEqual(row["status"], "verified_pass")
			self.assertIn("blocked_authority_writes_no_assistant_message", row["guarantees"])
			self.assertIn("blocked_authority_writes_no_tool_trace_answer_text", row["guarantees"])
			self.assertIn(
				"blocked_authority_writes_no_business_artifact_rendered_narrative_grounded_payload",
				row["guarantees"],
			)

		mapping = build_final_answer_remaining_append_mapping_report(root_path=PROJECT_ROOT)
		proof = mapping["visible_context_call_site_proof"]
		self.assertFalse(proof["release_blocking"])
		self.assertEqual(proof["proof_type"], "blocked_authority_runtime_probe")
		self.assertIn("no_business_evidence_tool_payload_leak", proof["runtime_probe_guarantees"])


if __name__ == "__main__":
	unittest.main()
