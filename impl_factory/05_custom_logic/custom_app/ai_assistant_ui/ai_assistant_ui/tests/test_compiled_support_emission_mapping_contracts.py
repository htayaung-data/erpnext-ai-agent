from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.compiled_support_emission_mapping import (
	COMPILED_SUPPORT_EMISSION_MAPPING_CONTRACT_TYPE,
	PROJECT_RELATIVE_COMPILED_SUPPORT,
	PROJECT_RELATIVE_SERVICE,
	build_compiled_support_emission_mapping_report,
	render_compiled_support_emission_mapping_markdown,
	write_compiled_support_emission_mapping_files,
)
from ai_assistant_ui.qwen_chat.final_answer_emission_dry_run import (
	build_final_answer_emission_dry_run_report,
)


PROJECT_ROOT = Path(__file__).resolve().parents[6]


def _line_numbers_containing(text: str, needle: str):
	return [index for index, line in enumerate(text.splitlines(), start=1) if needle in line]


class CompiledSupportEmissionMappingContractTests(unittest.TestCase):
	def test_report_classifies_compiled_support_as_authorized_helper_migrated(self):
		report = build_compiled_support_emission_mapping_report(root_path=PROJECT_ROOT)
		emitter = report["compiled_support_emitters"][0]

		self.assertEqual(report["type"], COMPILED_SUPPORT_EMISSION_MAPPING_CONTRACT_TYPE)
		self.assertEqual(report["slice_id"], "ec_4d_compiled_support_emission_mapping")
		self.assertTrue(report["runtime_behavior_changed"])
		self.assertFalse(report["hard_runtime_blocking_enabled"])
		self.assertEqual(report["compiled_support_emitter_count"], 1)
		self.assertEqual(report["compiled_support_direct_assistant_append_count"], 0)
		self.assertEqual(report["compiled_support_authorized_emission_helper_count"], 1)
		self.assertEqual(report["active_runtime_emitter_count"], 1)
		self.assertEqual(report["excluded_non_runtime_emitter_count"], 0)
		self.assertEqual(emitter["path_id"], "compiled_support_result_answer")
		self.assertEqual(emitter["active_classification"], "active_runtime_primary_migrated_to_authorized_helper")
		self.assertEqual(emitter["append_mechanism"], "authorized_assistant_emission_helper")
		self.assertEqual(emitter["authorized_emission_helper_count"], 1)
		self.assertGreaterEqual((emitter["authorized_emission_helper_lines"] or [0])[0], 600)
		self.assertEqual(emitter["audit_timing"], "audit_envelope_and_authorized_emission_contract_before_assistant_append")
		self.assertEqual(
			emitter["authority_availability_status"],
			"authority_validated_before_assistant_append",
		)

	def test_service_import_evidence_points_to_compiled_support_helper(self):
		report = build_compiled_support_emission_mapping_report(root_path=PROJECT_ROOT)
		service = report["service_import_evidence"]
		service_text = (PROJECT_ROOT / PROJECT_RELATIVE_SERVICE).read_text(encoding="utf-8", errors="ignore")
		expected_import_lines = _line_numbers_containing(
			service_text,
			"from ai_assistant_ui.qwen_chat.compiled_support import",
		)
		expected_alias_lines = _line_numbers_containing(
			service_text,
			"handle_compiled_first_turn_result as _handle_compiled_first_turn_result_helper",
		)

		self.assertTrue(service["compiled_support_imported_by_service"])
		self.assertEqual(service["compiled_support_import_lines"], expected_import_lines)
		self.assertEqual(service["handle_helper_alias_lines"], expected_alias_lines)
		self.assertGreaterEqual(len(expected_import_lines), 1)
		self.assertGreaterEqual(len(expected_alias_lines), 1)
		self.assertGreaterEqual(len(service["service_call_sites"]["_handle_compiled_first_turn_result"]), 1)
		self.assertGreaterEqual(len(service["service_call_sites"]["handle_compiled_first_turn_result_keyword"]), 1)

	def test_compiled_support_source_append_sites_are_all_mapped(self):
		report = build_compiled_support_emission_mapping_report(root_path=PROJECT_ROOT)
		source_lines = report["source_scan"]["assistant_append_lines"]
		helper_lines = report["source_scan"]["authorized_emission_helper_lines"]
		mapped_lines = [
			line
			for item in report["compiled_support_emitters"]
			for line in item["direct_assistant_append_lines"]
		]
		mapped_helper_lines = [
			line
			for item in report["compiled_support_emitters"]
			for line in item["authorized_emission_helper_lines"]
		]
		text = (PROJECT_ROOT / PROJECT_RELATIVE_COMPILED_SUPPORT).read_text(encoding="utf-8", errors="ignore")
		manual_source_lines = [
			index
			for index, line in enumerate(text.splitlines(), start=1)
			if 'append_message(session_doc, "assistant"' in line
		]
		manual_helper_lines = [
			index
			for index, line in enumerate(text.splitlines(), start=1)
			if "emit_authorized_assistant_answer(" in line
		]

		self.assertEqual(source_lines, mapped_lines)
		self.assertEqual(source_lines, manual_source_lines)
		self.assertEqual(source_lines, [])
		self.assertEqual(helper_lines, mapped_helper_lines)
		self.assertEqual(helper_lines, manual_helper_lines)
		self.assertEqual(len(helper_lines), 1)
		self.assertTrue(report["source_scan"]["all_assistant_appends_mapped"])

	def test_authority_timing_records_inputs_before_assistant_append(self):
		report = build_compiled_support_emission_mapping_report(root_path=PROJECT_ROOT)
		emitter = report["compiled_support_emitters"][0]

		self.assertIn("compiled_decision_message.answer_text", emitter["authority_inputs_before_append"])
		self.assertIn("result.normalized_family_artifact via append_compiled_attempt_artifacts", emitter["authority_inputs_before_append"])
		self.assertIn("grounded_turn_payload", emitter["authority_inputs_before_append"])
		self.assertIn("knowledge_boundary", emitter["authority_inputs_before_append"])
		self.assertIn("audit_envelope.final_answer_authority", emitter["authority_inputs_before_append"])
		self.assertIn("authorized_emission_contract", emitter["authority_inputs_before_append"])
		self.assertEqual(emitter["authority_inputs_after_append"], [])
		self.assertEqual(emitter["missing_before_append"], [])

	def test_completed_ec4e_scope_forbids_service_and_unrelated_lanes(self):
		report = build_compiled_support_emission_mapping_report(root_path=PROJECT_ROOT)
		write_scope = report["completed_ec4e_write_scope"]

		self.assertIn(PROJECT_RELATIVE_COMPILED_SUPPORT, write_scope["allowed_files"])
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
			"ec_4e_compiled_support_migration_complete_no_next_lane_until_counterpart_acceptance",
		)

	def test_ec3_dry_run_records_compiled_support_as_migrated_not_high_risk(self):
		report = build_final_answer_emission_dry_run_report()

		self.assertNotIn("compiled_support_result_answer", report["high_risk_paths"])
		self.assertIn(
			"compiled_support_result_answer",
			{item["path_id"] for item in report["migrated_authorized_paths"]},
		)

	def test_markdown_and_files_are_reviewer_friendly(self):
		report = build_compiled_support_emission_mapping_report(root_path=PROJECT_ROOT)
		markdown = render_compiled_support_emission_mapping_markdown(report)

		self.assertIn("EC-4D Compiled Support Emission Mapping", markdown)
		self.assertIn("compiled_support_result_answer", markdown)
		self.assertIn("Completed EC-4E Write Scope", markdown)
		with tempfile.TemporaryDirectory() as temp_dir:
			result = write_compiled_support_emission_mapping_files(
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
				"enterprise_cleanup_ec_4e_mapping_governance_ready_for_counterpart_review",
			)


if __name__ == "__main__":
	unittest.main()
