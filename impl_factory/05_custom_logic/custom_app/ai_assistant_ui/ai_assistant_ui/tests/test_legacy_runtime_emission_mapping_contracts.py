from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.final_answer_emission_dry_run import (
	build_final_answer_emission_dry_run_report,
)
from ai_assistant_ui.qwen_chat.legacy_runtime_emission_mapping import (
	LEGACY_RUNTIME_EMISSION_MAPPING_CONTRACT_TYPE,
	PROJECT_RELATIVE_LEGACY_RUNTIME,
	PROJECT_RELATIVE_SERVICE,
	build_legacy_runtime_emission_mapping_report,
	render_legacy_runtime_emission_mapping_markdown,
	write_legacy_runtime_emission_mapping_files,
)


PROJECT_ROOT = Path(__file__).resolve().parents[6]


def _line_numbers_containing(text: str, needle: str):
	return [index for index, line in enumerate(text.splitlines(), start=1) if needle in line]


class LegacyRuntimeEmissionMappingContractTests(unittest.TestCase):
	def test_report_classifies_legacy_runtime_as_authorized_helper_migrated(self):
		report = build_legacy_runtime_emission_mapping_report(root_path=PROJECT_ROOT)
		emitters = {item["path_id"]: item for item in report["legacy_runtime_emitters"]}

		self.assertEqual(report["type"], LEGACY_RUNTIME_EMISSION_MAPPING_CONTRACT_TYPE)
		self.assertEqual(report["slice_id"], "ec_4h_legacy_runtime_emission_mapping")
		self.assertTrue(report["runtime_behavior_changed"])
		self.assertFalse(report["hard_runtime_blocking_enabled"])
		self.assertEqual(report["legacy_runtime_emitter_count"], 2)
		self.assertEqual(report["legacy_runtime_direct_assistant_append_count"], 0)
		self.assertEqual(report["legacy_runtime_authorized_emission_helper_count"], 2)
		self.assertEqual(report["active_runtime_emitter_count"], 2)
		self.assertEqual(report["excluded_non_runtime_emitter_count"], 0)
		self.assertEqual(
			emitters["legacy_runtime_client_error"]["active_classification"],
			"active_runtime_error_fallback_migrated_to_authorized_helper",
		)
		self.assertEqual(
			emitters["legacy_runtime_business_or_boundary_answer"]["active_classification"],
			"active_runtime_primary_migrated_to_authorized_helper",
		)
		self.assertEqual(emitters["legacy_runtime_client_error"]["answer_type"], "error_fallback_answer")
		self.assertEqual(
			emitters["legacy_runtime_business_or_boundary_answer"]["answer_type"],
			"governed_report_answer_or_policy_boundary_refusal",
		)

	def test_service_import_evidence_points_to_active_legacy_runtime_lane(self):
		report = build_legacy_runtime_emission_mapping_report(root_path=PROJECT_ROOT)
		service = report["service_import_evidence"]
		service_text = (PROJECT_ROOT / PROJECT_RELATIVE_SERVICE).read_text(encoding="utf-8", errors="ignore")
		expected_import_lines = _line_numbers_containing(
			service_text,
			"from ai_assistant_ui.qwen_chat.lanes.legacy_runtime_lane import handle_legacy_runtime_turn",
		)
		expected_call_lines = [
			index
			for index, line in enumerate(service_text.splitlines(), start=1)
			if "handle_legacy_runtime_turn(" in line and not line.strip().startswith("from ")
		]

		self.assertTrue(service["legacy_runtime_imported_by_service"])
		self.assertEqual(service["legacy_runtime_import_lines"], expected_import_lines)
		self.assertEqual(service["service_call_sites"]["handle_legacy_runtime_turn"], expected_call_lines)
		self.assertGreaterEqual(len(expected_import_lines), 1)
		self.assertGreaterEqual(len(expected_call_lines), 1)
		self.assertGreaterEqual(len(service["service_call_sites"]["legacy_runtime_mode_checks"]), 1)

	def test_source_append_sites_are_all_mapped(self):
		report = build_legacy_runtime_emission_mapping_report(root_path=PROJECT_ROOT)
		text = (PROJECT_ROOT / PROJECT_RELATIVE_LEGACY_RUNTIME).read_text(encoding="utf-8", errors="ignore")
		source_lines = [
			index
			for index, line in enumerate(text.splitlines(), start=1)
			if 'append_message(session_doc, "assistant"' in line
		]
		mapped_lines = [
			line
			for item in report["legacy_runtime_emitters"]
			for line in item["direct_assistant_append_lines"]
		]
		helper_lines = [
			index
			for index, line in enumerate(text.splitlines(), start=1)
			if "emit_authorized_assistant_answer(" in line
		]
		mapped_helper_lines = [
			line
			for item in report["legacy_runtime_emitters"]
			for line in item["authorized_emission_helper_lines"]
		]

		self.assertEqual(source_lines, [])
		self.assertEqual(sorted(source_lines), sorted(mapped_lines))
		self.assertEqual(report["source_scan"]["assistant_append_lines"], source_lines)
		self.assertEqual(len(helper_lines), 2)
		self.assertEqual(sorted(helper_lines), sorted(mapped_helper_lines))
		self.assertEqual(report["source_scan"]["authorized_emission_helper_lines"], helper_lines)
		self.assertTrue(report["source_scan"]["all_assistant_appends_mapped"])

	def test_authority_timing_records_pre_append_authorized_emission(self):
		report = build_legacy_runtime_emission_mapping_report(root_path=PROJECT_ROOT)
		emitters = {item["path_id"]: item for item in report["legacy_runtime_emitters"]}
		error_emitter = emitters["legacy_runtime_client_error"]
		business_emitter = emitters["legacy_runtime_business_or_boundary_answer"]

		self.assertEqual(error_emitter["append_mechanism"], "authorized_assistant_emission_helper")
		self.assertEqual(error_emitter["audit_timing"], "authorized_emission_contract_before_error_assistant_append")
		self.assertEqual(error_emitter["authority_availability_status"], "explicit_error_authority_validated_before_append")
		self.assertEqual(error_emitter["missing_before_append"], [])
		self.assertEqual(error_emitter["authority_inputs_after_append"], [])
		self.assertFalse(error_emitter["returned_payload_answer_text_surface"])

		self.assertEqual(business_emitter["append_mechanism"], "authorized_assistant_emission_helper")
		self.assertEqual(
			business_emitter["audit_timing"],
			"grounded_turn_audit_and_authorized_emission_contract_before_assistant_append",
		)
		self.assertEqual(business_emitter["authority_availability_status"], "authority_validated_before_assistant_append")
		self.assertEqual(business_emitter["authority_inputs_after_append"], [])
		self.assertEqual(business_emitter["missing_before_append"], [])
		self.assertFalse(business_emitter["returned_payload_answer_text_surface"])

	def test_ec3_dry_run_records_legacy_runtime_paths_as_migrated(self):
		report = build_final_answer_emission_dry_run_report()
		migrated = {item["path_id"] for item in report["migrated_authorized_paths"]}

		self.assertNotIn("legacy_runtime_client_error", {item["path_id"] for item in report["emission_path_inventory"]})
		self.assertNotIn("legacy_runtime_business_or_boundary_answer", report["high_risk_paths"])
		self.assertIn("legacy_runtime_client_error", migrated)
		self.assertIn("legacy_runtime_business_or_boundary_answer", migrated)

	def test_completed_ec4i_scope_forbids_service_and_unrelated_lanes(self):
		report = build_legacy_runtime_emission_mapping_report(root_path=PROJECT_ROOT)
		write_scope = report["completed_ec4i_write_scope"]

		self.assertIn(PROJECT_RELATIVE_LEGACY_RUNTIME, write_scope["allowed_files"])
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/legacy_runtime_emission_mapping.py",
			write_scope["allowed_files"],
		)
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_legacy_runtime_emission_mapping_contracts.py",
			write_scope["allowed_files"],
		)
		self.assertIn(PROJECT_RELATIVE_SERVICE, write_scope["forbidden_files"])
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/reasoning_lane.py",
			write_scope["forbidden_files"],
		)
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py",
			write_scope["forbidden_files"],
		)
		self.assertEqual(
			write_scope["write_scope_decision"],
			"ec_4i_legacy_runtime_migration_complete_no_next_lane_until_counterpart_acceptance",
		)

	def test_markdown_and_files_are_reviewer_friendly(self):
		report = build_legacy_runtime_emission_mapping_report(root_path=PROJECT_ROOT)
		markdown = render_legacy_runtime_emission_mapping_markdown(report)

		self.assertIn("EC-4H/EC-4I Legacy Runtime Emission Mapping", markdown)
		self.assertIn("legacy_runtime_client_error", markdown)
		self.assertIn("legacy_runtime_business_or_boundary_answer", markdown)
		self.assertIn("Completed EC-4I Write Scope", markdown)
		with tempfile.TemporaryDirectory() as temp_dir:
			result = write_legacy_runtime_emission_mapping_files(
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
			self.assertEqual(
				loaded["final_recommendation"],
				"enterprise_cleanup_ec_4i_ready_for_counterpart_review",
			)


if __name__ == "__main__":
	unittest.main()
