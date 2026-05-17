from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.final_answer_emission_dry_run import (
	build_final_answer_emission_dry_run_report,
)
from ai_assistant_ui.qwen_chat.nbu_governed_requery_emission_mapping import (
	NBU_GOVERNED_REQUERY_EMISSION_MAPPING_CONTRACT_TYPE,
	PROJECT_RELATIVE_NBU_GOVERNED_REQUERY,
	PROJECT_RELATIVE_SERVICE,
	build_nbu_governed_requery_emission_mapping_report,
	render_nbu_governed_requery_emission_mapping_markdown,
	write_nbu_governed_requery_emission_mapping_files,
)


PROJECT_ROOT = Path(__file__).resolve().parents[6]


class NBUGovernedRequeryEmissionMappingContractTests(unittest.TestCase):
	def test_report_classifies_nbu_governed_requery_as_authorized_helper_migrated(self):
		report = build_nbu_governed_requery_emission_mapping_report(root_path=PROJECT_ROOT)
		emitters = {item["path_id"]: item for item in report["nbu_governed_requery_emitters"]}

		self.assertEqual(report["type"], NBU_GOVERNED_REQUERY_EMISSION_MAPPING_CONTRACT_TYPE)
		self.assertEqual(report["slice_id"], "ec_4j_nbu_governed_requery_emission_mapping")
		self.assertTrue(report["runtime_behavior_changed"])
		self.assertTrue(report["authorized_emission_runtime_migration_done"])
		self.assertFalse(report["hard_runtime_blocking_enabled"])
		self.assertEqual(report["nbu_governed_requery_emitter_count"], 1)
		self.assertEqual(report["nbu_governed_requery_direct_assistant_append_count"], 0)
		self.assertEqual(report["nbu_governed_requery_authorized_emission_helper_count"], 1)
		self.assertEqual(report["active_runtime_emitter_count"], 1)
		self.assertEqual(report["excluded_non_runtime_emitter_count"], 0)
		self.assertEqual(
			emitters["nbu_governed_requery_entity_detail"]["active_classification"],
			"active_runtime_primary_migrated_to_authorized_helper",
		)
		self.assertEqual(
			emitters["nbu_governed_requery_entity_detail"]["answer_type"],
			"business_facing_factual_answer_or_governed_report_answer",
		)

	def test_service_import_evidence_points_to_active_nbu_governed_requery(self):
		report = build_nbu_governed_requery_emission_mapping_report(root_path=PROJECT_ROOT)
		service = report["service_import_evidence"]

		self.assertTrue(service["nbu_governed_requery_imported_by_service"])
		self.assertGreaterEqual(len(service["nbu_governed_requery_import_lines"]), 1)
		self.assertGreaterEqual(len(service["nbu_governed_requery_alias_lines"]), 1)
		self.assertGreaterEqual(len(service["service_call_sites"]["_try_activate_nbu_governed_requery_response"]), 1)
		self.assertGreaterEqual(len(service["service_call_sites"]["activation_level_governed_requery"]), 1)

	def test_source_append_sites_are_all_mapped(self):
		report = build_nbu_governed_requery_emission_mapping_report(root_path=PROJECT_ROOT)
		text = (PROJECT_ROOT / PROJECT_RELATIVE_NBU_GOVERNED_REQUERY).read_text(encoding="utf-8", errors="ignore")
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
			for item in report["nbu_governed_requery_emitters"]
			for line in item["direct_assistant_append_lines"]
		]
		mapped_helper_lines = [
			line
			for item in report["nbu_governed_requery_emitters"]
			for line in item["authorized_emission_helper_lines"]
		]

		self.assertEqual(source_lines, [])
		self.assertEqual(sorted(source_lines), sorted(mapped_lines))
		self.assertEqual(len(helper_lines), 1)
		self.assertEqual(sorted(helper_lines), sorted(mapped_helper_lines))
		self.assertEqual(report["source_scan"]["assistant_append_lines"], source_lines)
		self.assertTrue(report["source_scan"]["all_assistant_appends_mapped"])

	def test_authority_timing_records_pre_append_authorized_emission(self):
		report = build_nbu_governed_requery_emission_mapping_report(root_path=PROJECT_ROOT)
		emitter = {
			item["path_id"]: item for item in report["nbu_governed_requery_emitters"]
		}["nbu_governed_requery_entity_detail"]

		self.assertEqual(emitter["risk_level"], "high")
		self.assertEqual(emitter["append_mechanism"], "authorized_assistant_emission_helper")
		self.assertEqual(
			emitter["audit_timing"],
			"audit_envelope_and_authorized_emission_contract_before_assistant_append",
		)
		self.assertEqual(
			emitter["authority_availability_status"],
			"authority_validated_before_assistant_append",
		)
		self.assertFalse(emitter["conditional_audit_gap"])
		self.assertFalse(emitter["api_payload_answer_text_surface"])
		self.assertIn("outcome.artifact_payload", emitter["authority_inputs_before_append"])
		self.assertIn("outcome.grounded_turn_payload", emitter["authority_inputs_before_append"])
		self.assertEqual(emitter["authority_inputs_after_append"], [])
		self.assertEqual(emitter["missing_before_append"], [])
		self.assertEqual(emitter["build_audit_envelope_lines"], [])

	def test_ec3_dry_run_records_nbu_governed_requery_as_migrated(self):
		report = build_final_answer_emission_dry_run_report()
		inventory_paths = {item["path_id"] for item in report["emission_path_inventory"]}
		migrated = {item["path_id"] for item in report["migrated_authorized_paths"]}

		self.assertNotIn("nbu_governed_requery_entity_detail", inventory_paths)
		self.assertNotIn("nbu_governed_requery_entity_detail", report["high_risk_paths"])
		self.assertIn("nbu_governed_requery_entity_detail", migrated)

	def test_completed_ec4k_scope_forbids_service_and_unrelated_lanes(self):
		report = build_nbu_governed_requery_emission_mapping_report(root_path=PROJECT_ROOT)
		write_scope = report["completed_ec4k_write_scope"]

		self.assertIn(PROJECT_RELATIVE_NBU_GOVERNED_REQUERY, write_scope["allowed_files"])
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/nbu_governed_requery_emission_mapping.py",
			write_scope["allowed_files"],
		)
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_nbu_governed_requery_emission_mapping_contracts.py",
			write_scope["allowed_files"],
		)
		self.assertIn(PROJECT_RELATIVE_SERVICE, write_scope["forbidden_files"])
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/entity_followup_support.py",
			write_scope["forbidden_files"],
		)
		self.assertIn(
			"impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/frontdoor_lane.py",
			write_scope["forbidden_files"],
		)
		self.assertEqual(
			write_scope["write_scope_decision"],
			"ec_4k_nbu_governed_requery_migration_complete_no_next_lane_until_counterpart_acceptance",
		)

	def test_markdown_and_files_are_reviewer_friendly(self):
		report = build_nbu_governed_requery_emission_mapping_report(root_path=PROJECT_ROOT)
		markdown = render_nbu_governed_requery_emission_mapping_markdown(report)

		self.assertIn("EC-4J/EC-4K NBU Governed-Requery Emission Mapping", markdown)
		self.assertIn("nbu_governed_requery_entity_detail", markdown)
		self.assertIn("Completed EC-4K Write Scope", markdown)
		self.assertIn("ec4j_was_mapping_only_ec4k_performed_bounded_nbu_governed_requery_migration", markdown)
		with tempfile.TemporaryDirectory() as temp_dir:
			result = write_nbu_governed_requery_emission_mapping_files(
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
				"enterprise_cleanup_ec_4k_ready_for_counterpart_review",
			)


if __name__ == "__main__":
	unittest.main()
