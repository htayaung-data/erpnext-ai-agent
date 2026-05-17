from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.entity_followup_emission_mapping import (
	ENTITY_FOLLOWUP_EMISSION_MAPPING_CONTRACT_TYPE,
	PROJECT_RELATIVE_ENTITY_FOLLOWUP,
	PROJECT_RELATIVE_SERVICE,
	build_entity_followup_emission_mapping_report,
	render_entity_followup_emission_mapping_markdown,
	write_entity_followup_emission_mapping_files,
)
from ai_assistant_ui.qwen_chat.final_answer_emission_dry_run import (
	build_final_answer_emission_dry_run_report,
)


PROJECT_ROOT = Path(__file__).resolve().parents[6]


class EntityFollowupEmissionMappingContractTests(unittest.TestCase):
	def test_report_classifies_entity_followup_as_authorized_helper_migrated(self):
		report = build_entity_followup_emission_mapping_report(root_path=PROJECT_ROOT)
		emitters = {item["path_id"]: item for item in report["entity_followup_emitters"]}

		self.assertEqual(report["type"], ENTITY_FOLLOWUP_EMISSION_MAPPING_CONTRACT_TYPE)
		self.assertEqual(report["slice_id"], "ec_4l_entity_followup_emission_mapping")
		self.assertTrue(report["runtime_behavior_changed"])
		self.assertTrue(report["authorized_emission_runtime_migration_done"])
		self.assertFalse(report["hard_runtime_blocking_enabled"])
		self.assertEqual(report["entity_followup_emitter_count"], 2)
		self.assertEqual(report["entity_followup_direct_assistant_append_count"], 0)
		self.assertEqual(report["entity_followup_authorized_emission_helper_count"], 2)
		self.assertEqual(report["active_runtime_emitter_count"], 2)
		self.assertEqual(report["excluded_non_runtime_emitter_count"], 0)
		self.assertEqual(
			emitters["entity_followup_success"]["active_classification"],
			"active_runtime_primary_migrated_to_authorized_helper",
		)
		self.assertEqual(
			emitters["entity_followup_failure"]["active_classification"],
			"active_runtime_error_fallback_migrated_to_authorized_helper",
		)

	def test_service_import_evidence_points_to_active_entity_followup(self):
		report = build_entity_followup_emission_mapping_report(root_path=PROJECT_ROOT)
		service = report["service_import_evidence"]

		self.assertTrue(service["entity_followup_imported_by_service"])
		self.assertGreaterEqual(len(service["entity_followup_import_lines"]), 1)
		self.assertGreaterEqual(len(service["entity_followup_alias_lines"]), 1)
		self.assertGreaterEqual(len(service["service_call_sites"]["_try_entity_detail_followup"]), 1)
		self.assertGreaterEqual(len(service["service_call_sites"]["_try_entity_detail_followup_helper"]), 1)

	def test_source_append_sites_are_all_mapped(self):
		report = build_entity_followup_emission_mapping_report(root_path=PROJECT_ROOT)
		source_lines = list(report["source_scan"]["assistant_append_lines"])
		text = (PROJECT_ROOT / PROJECT_RELATIVE_ENTITY_FOLLOWUP).read_text(encoding="utf-8", errors="ignore")
		helper_lines = [
			index
			for index, line in enumerate(text.splitlines(), start=1)
			if "emit_authorized_assistant_answer(" in line
		]
		mapped_lines = [
			line
			for item in report["entity_followup_emitters"]
			for line in item["direct_assistant_append_lines"]
		]
		mapped_helper_lines = [
			line
			for item in report["entity_followup_emitters"]
			for line in item["authorized_emission_helper_lines"]
		]

		self.assertEqual(source_lines, [])
		self.assertEqual(sorted(source_lines), sorted(mapped_lines))
		self.assertEqual(len(helper_lines), 2)
		self.assertEqual(sorted(helper_lines), sorted(mapped_helper_lines))
		self.assertEqual(report["source_scan"]["assistant_append_lines"], source_lines)
		self.assertTrue(report["source_scan"]["all_assistant_appends_mapped"])

	def test_success_path_records_missing_final_authority_and_post_append_payloads(self):
		report = build_entity_followup_emission_mapping_report(root_path=PROJECT_ROOT)
		emitter = {item["path_id"]: item for item in report["entity_followup_emitters"]}["entity_followup_success"]

		self.assertEqual(emitter["risk_level"], "high")
		self.assertEqual(emitter["append_mechanism"], "authorized_assistant_emission_helper")
		self.assertEqual(emitter["audit_timing"], "audit_envelope_and_authorized_emission_contract_before_assistant_append")
		self.assertEqual(emitter["authority_availability_status"], "authority_validated_before_assistant_append")
		self.assertFalse(emitter["api_payload_answer_text_surface"])
		self.assertIn("outcome.artifact_payload", emitter["authority_inputs_before_append"])
		self.assertEqual(emitter["authority_inputs_after_append"], [])
		self.assertEqual(emitter["missing_before_append"], [])

	def test_failure_path_records_missing_error_authority(self):
		report = build_entity_followup_emission_mapping_report(root_path=PROJECT_ROOT)
		emitter = {item["path_id"]: item for item in report["entity_followup_emitters"]}["entity_followup_failure"]

		self.assertEqual(emitter["risk_level"], "medium")
		self.assertEqual(emitter["answer_type"], "error_fallback_answer")
		self.assertEqual(emitter["append_mechanism"], "authorized_assistant_emission_helper")
		self.assertEqual(emitter["authority_availability_status"], "explicit_error_authority_validated_before_append")
		self.assertEqual(emitter["missing_before_append"], [])
		self.assertFalse(emitter["api_payload_answer_text_surface"])

	def test_ec3_dry_run_records_entity_followup_as_migrated(self):
		report = build_final_answer_emission_dry_run_report()
		inventory_paths = {item["path_id"] for item in report["emission_path_inventory"]}
		migrated = {item["path_id"] for item in report["migrated_authorized_paths"]}

		self.assertNotIn("entity_followup_success", inventory_paths)
		self.assertNotIn("entity_followup_failure", inventory_paths)
		self.assertNotIn("entity_followup_success", report["high_risk_paths"])
		self.assertIn("entity_followup_success", migrated)
		self.assertIn("entity_followup_failure", migrated)

	def test_completed_ec4m_scope_forbids_service_and_unrelated_lanes(self):
		report = build_entity_followup_emission_mapping_report(root_path=PROJECT_ROOT)
		write_scope = report["completed_ec4m_write_scope"]

		self.assertIn(PROJECT_RELATIVE_ENTITY_FOLLOWUP, write_scope["allowed_files"])
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_emission_mapping.py",
			write_scope["allowed_files"],
		)
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_followup_emission_mapping_contracts.py",
			write_scope["allowed_files"],
		)
		self.assertIn(PROJECT_RELATIVE_SERVICE, write_scope["forbidden_files"])
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py",
			write_scope["forbidden_files"],
		)
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/natural_business_understanding_governed_requery_activation.py",
			write_scope["forbidden_files"],
		)
		self.assertEqual(
			write_scope["write_scope_decision"],
			"ec_4m_entity_followup_migration_complete_no_next_lane_until_counterpart_acceptance",
		)

	def test_markdown_and_files_are_reviewer_friendly(self):
		report = build_entity_followup_emission_mapping_report(root_path=PROJECT_ROOT)
		markdown = render_entity_followup_emission_mapping_markdown(report)

		self.assertIn("EC-4L/EC-4M Entity Follow-Up Emission Mapping", markdown)
		self.assertIn("entity_followup_success", markdown)
		self.assertIn("entity_followup_failure", markdown)
		self.assertIn("Completed EC-4M Write Scope", markdown)
		self.assertIn("ec4l_was_mapping_only_ec4m_performed_bounded_entity_followup_migration", markdown)
		with tempfile.TemporaryDirectory() as temp_dir:
			result = write_entity_followup_emission_mapping_files(
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
				"enterprise_cleanup_ec_4m_ready_for_counterpart_review",
			)


if __name__ == "__main__":
	unittest.main()
