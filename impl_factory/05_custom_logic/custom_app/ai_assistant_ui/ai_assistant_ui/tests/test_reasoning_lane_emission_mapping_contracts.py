from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.final_answer_emission_dry_run import (
	build_final_answer_emission_dry_run_report,
)
from ai_assistant_ui.qwen_chat.reasoning_lane_emission_mapping import (
	PROJECT_RELATIVE_REASONING_LANE,
	PROJECT_RELATIVE_SERVICE,
	REASONING_LANE_EMISSION_MAPPING_CONTRACT_TYPE,
	build_reasoning_lane_emission_mapping_report,
	render_reasoning_lane_emission_mapping_markdown,
	write_reasoning_lane_emission_mapping_files,
)


PROJECT_ROOT = Path(__file__).resolve().parents[6]


def _line_numbers_containing(text: str, needle: str):
	return [index for index, line in enumerate(text.splitlines(), start=1) if needle in line]


class ReasoningLaneEmissionMappingContractTests(unittest.TestCase):
	def test_report_classifies_reasoning_lane_as_authorized_helper_migrated(self):
		report = build_reasoning_lane_emission_mapping_report(root_path=PROJECT_ROOT)
		emitters = {item["path_id"]: item for item in report["reasoning_lane_emitters"]}

		self.assertEqual(report["type"], REASONING_LANE_EMISSION_MAPPING_CONTRACT_TYPE)
		self.assertEqual(report["slice_id"], "ec_4g_reasoning_lane_authorized_emission_migration")
		self.assertTrue(report["runtime_behavior_changed"])
		self.assertTrue(report["authorized_emission_runtime_migration_done"])
		self.assertFalse(report["hard_runtime_blocking_enabled"])
		self.assertEqual(report["reasoning_lane_emitter_count"], 2)
		self.assertEqual(report["reasoning_lane_direct_assistant_append_count"], 0)
		self.assertEqual(report["reasoning_lane_authorized_emission_helper_count"], 2)
		self.assertEqual(report["active_runtime_emitter_count"], 2)
		self.assertEqual(report["clarification_control_emitter_count"], 0)
		self.assertIn("no_reasoning_lane_assistant_control", report["clarification_control_assessment"])
		self.assertEqual(
			emitters["reasoning_lane_business_answer"]["active_classification"],
			"active_runtime_primary_migrated_to_authorized_helper",
		)
		self.assertEqual(
			emitters["reasoning_lane_guardrail_boundary"]["active_classification"],
			"active_runtime_primary_migrated_to_authorized_helper",
		)
		delta = report["reasoning_model_role_runtime_delta"]
		self.assertTrue(delta["runtime_delta_detected"])
		self.assertEqual(delta["classification"], "pre_existing_s7_reasoning_model_role_observability_prep")
		self.assertIn("S7-X1 baseline", delta["baseline_evidence"])
		self.assertIn("model-role", " ".join(delta["runtime_delta_summary"]))

	def test_business_reasoning_answer_records_authorized_emission_migration(self):
		report = build_reasoning_lane_emission_mapping_report(root_path=PROJECT_ROOT)
		emitter = {
			item["path_id"]: item for item in report["reasoning_lane_emitters"]
		}["reasoning_lane_business_answer"]

		self.assertEqual(emitter["answer_type"], "reasoning_business_consultant_answer")
		self.assertEqual(emitter["risk_level"], "high")
		self.assertEqual(emitter["append_mechanism"], "authorized_assistant_emission_helper")
		self.assertEqual(emitter["direct_assistant_append_lines"], [])
		self.assertEqual(len(emitter["authorized_emission_helper_lines"]), 1)
		self.assertEqual(emitter["build_audit_envelope_lines"], [])
		self.assertEqual(len(emitter["knowledge_boundary_lines"]), 1)
		self.assertEqual(emitter["audit_timing"], "audit_envelope_and_authorized_emission_contract_before_assistant_append")
		self.assertEqual(emitter["authority_availability_status"], "authority_validated_before_assistant_append")
		self.assertIn("latest_grounded_turn", emitter["authority_inputs_before_append"])
		self.assertEqual(emitter["authority_inputs_after_append"], [])
		self.assertEqual(emitter["missing_before_append"], [])

	def test_guardrail_boundary_records_authorized_policy_boundary_mapping(self):
		report = build_reasoning_lane_emission_mapping_report(root_path=PROJECT_ROOT)
		emitter = {
			item["path_id"]: item for item in report["reasoning_lane_emitters"]
		}["reasoning_lane_guardrail_boundary"]

		self.assertEqual(emitter["answer_type"], "policy_boundary_refusal")
		self.assertEqual(emitter["risk_level"], "medium")
		self.assertEqual(emitter["direct_assistant_append_lines"], [])
		self.assertEqual(len(emitter["authorized_emission_helper_lines"]), 1)
		self.assertEqual(emitter["build_audit_envelope_lines"], [])
		self.assertEqual(len(emitter["knowledge_boundary_lines"]), 1)
		self.assertEqual(emitter["authority_availability_status"], "authority_validated_before_assistant_append")
		self.assertIn("knowledge_boundary_contract", emitter["authority_inputs_before_append"])
		self.assertEqual(emitter["authority_inputs_after_append"], [])

	def test_service_import_evidence_points_to_reasoning_lane(self):
		report = build_reasoning_lane_emission_mapping_report(root_path=PROJECT_ROOT)
		service = report["service_import_evidence"]
		service_text = (PROJECT_ROOT / PROJECT_RELATIVE_SERVICE).read_text(encoding="utf-8", errors="ignore")
		expected_import_lines = _line_numbers_containing(
			service_text,
			"from ai_assistant_ui.qwen_chat.lanes.reasoning_lane import",
		)
		expected_call_lines = _line_numbers_containing(service_text, "handle_reasoning_turn(")

		self.assertTrue(service["reasoning_lane_imported_by_service"])
		self.assertEqual(service["reasoning_lane_import_lines"], expected_import_lines)
		self.assertEqual(service["service_call_sites"]["handle_reasoning_turn"], expected_call_lines)
		self.assertGreaterEqual(len(expected_import_lines), 1)
		self.assertGreaterEqual(len(service["service_call_sites"]["handle_reasoning_turn"]), 1)
		self.assertGreaterEqual(len(service["service_call_sites"]["reasoning_handled_payload"]), 1)

	def test_reasoning_source_append_sites_are_all_mapped(self):
		report = build_reasoning_lane_emission_mapping_report(root_path=PROJECT_ROOT)
		text = (PROJECT_ROOT / PROJECT_RELATIVE_REASONING_LANE).read_text(encoding="utf-8", errors="ignore")
		source_lines = [
			index
			for index, line in enumerate(text.splitlines(), start=1)
			if 'append_message(session_doc, "assistant"' in line
		]
		helper_lines = [
			index
			for index, line in enumerate(text.splitlines(), start=1)
			if "emit_authorized_assistant_answer(" in line
		]
		mapped_lines = [
			line
			for item in report["reasoning_lane_emitters"]
			for line in item["direct_assistant_append_lines"]
		]
		mapped_helper_lines = [
			line
			for item in report["reasoning_lane_emitters"]
			for line in item["authorized_emission_helper_lines"]
		]

		self.assertEqual(source_lines, [])
		self.assertEqual(sorted(source_lines), sorted(mapped_lines))
		self.assertEqual(len(helper_lines), 2)
		self.assertEqual(sorted(helper_lines), sorted(mapped_helper_lines))
		self.assertTrue(report["source_scan"]["all_assistant_appends_mapped"])

	def test_ec3_dry_run_records_reasoning_paths_as_migrated(self):
		report = build_final_answer_emission_dry_run_report()
		migrated = {item["path_id"] for item in report["migrated_authorized_paths"]}

		self.assertNotIn("reasoning_lane_business_answer", report["high_risk_paths"])
		self.assertIn("reasoning_lane_business_answer", migrated)
		self.assertIn("reasoning_lane_guardrail_boundary", migrated)

	def test_completed_ec4g_scope_forbids_service_and_unrelated_lanes(self):
		report = build_reasoning_lane_emission_mapping_report(root_path=PROJECT_ROOT)
		write_scope = report["completed_ec4g_write_scope"]

		self.assertIn(PROJECT_RELATIVE_REASONING_LANE, write_scope["allowed_files"])
		self.assertIn(PROJECT_RELATIVE_SERVICE, write_scope["forbidden_files"])
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py",
			write_scope["forbidden_files"],
		)
		self.assertEqual(
			write_scope["write_scope_decision"],
			"ec_4g_reasoning_lane_migration_complete_no_next_lane_until_counterpart_acceptance",
		)

	def test_markdown_and_files_are_reviewer_friendly(self):
		report = build_reasoning_lane_emission_mapping_report(root_path=PROJECT_ROOT)
		markdown = render_reasoning_lane_emission_mapping_markdown(report)

		self.assertIn("EC-4G Reasoning Lane Authorized Emission Migration", markdown)
		self.assertIn("reasoning_lane_business_answer", markdown)
		self.assertIn("reasoning_lane_guardrail_boundary", markdown)
		self.assertIn("Runtime Delta Classification", markdown)
		self.assertIn("Completed EC-4G Write Scope", markdown)
		with tempfile.TemporaryDirectory() as temp_dir:
			result = write_reasoning_lane_emission_mapping_files(
				root_path=PROJECT_ROOT,
				out_dir=temp_dir,
				reviewer="unit_test",
			)
			json_path = Path(result["json_path"])
			markdown_path = Path(result["markdown_path"])
			self.assertTrue(json_path.exists())
			self.assertTrue(markdown_path.exists())
			loaded = json.loads(json_path.read_text(encoding="utf-8"))
			self.assertEqual(loaded["reviewer"], "unit_test")
			self.assertEqual(loaded["final_recommendation"], "enterprise_cleanup_ec_4g_ready_for_counterpart_review")


if __name__ == "__main__":
	unittest.main()
