from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.frontdoor_emission_mapping import (
	FRONTDOOR_EMISSION_MAPPING_CONTRACT_TYPE,
	PROJECT_RELATIVE_PACKAGE_FRONTDOOR,
	PROJECT_RELATIVE_ROOT_FRONTDOOR,
	PROJECT_RELATIVE_SERVICE,
	build_frontdoor_emission_mapping_report,
	render_frontdoor_emission_mapping_markdown,
	write_frontdoor_emission_mapping_files,
)


PROJECT_ROOT = Path(__file__).resolve().parents[6]


class FrontdoorEmissionMappingContractTests(unittest.TestCase):
	def test_report_classifies_package_lane_as_active_and_root_as_facade(self):
		report = build_frontdoor_emission_mapping_report(root_path=PROJECT_ROOT)
		emitters = {item["path_id"]: item for item in report["frontdoor_emitters"]}

		self.assertEqual(report["type"], FRONTDOOR_EMISSION_MAPPING_CONTRACT_TYPE)
		self.assertTrue(report["runtime_behavior_changed"])
		self.assertFalse(report["hard_runtime_blocking_enabled"])
		self.assertEqual(report["frontdoor_emitter_count"], 2)
		self.assertEqual(report["frontdoor_direct_assistant_append_count"], 0)
		self.assertEqual(report["active_runtime_emitter_count"], 1)
		self.assertEqual(report["active_runtime_migrated_to_authorized_helper_count"], 1)
		self.assertEqual(report["duplicate_drift_emitter_count"], 0)
		self.assertEqual(report["compatibility_facade_emitter_count"], 1)
		self.assertEqual(
			emitters["frontdoor_lane_package_governed_report_or_projection"]["active_classification"],
			"active_runtime_primary_migrated_to_authorized_helper",
		)
		self.assertEqual(
			emitters["frontdoor_lane_package_governed_report_or_projection"]["direct_assistant_append_count"],
			0,
		)
		self.assertGreater(
			emitters["frontdoor_lane_package_governed_report_or_projection"]["authorized_emission_helper_count"],
			0,
		)
		self.assertEqual(
			emitters["frontdoor_lane_root_duplicate"]["active_classification"],
			"compatibility_facade_not_service_runtime",
		)
		self.assertEqual(emitters["frontdoor_lane_root_duplicate"]["direct_assistant_append_count"], 0)
		self.assertTrue(emitters["frontdoor_lane_package_governed_report_or_projection"]["service_imported"])
		self.assertFalse(emitters["frontdoor_lane_root_duplicate"]["service_imported"])

	def test_service_import_and_call_evidence_points_only_to_package_lane(self):
		report = build_frontdoor_emission_mapping_report(root_path=PROJECT_ROOT)
		service = report["service_import_evidence"]

		self.assertTrue(service["package_imported_by_service"])
		self.assertFalse(service["root_imported_by_service"])
		self.assertIn(265, service["package_import_lines"])
		self.assertGreaterEqual(len(service["service_call_sites"]["evaluate_frontdoor_lane"]), 3)
		self.assertGreaterEqual(len(service["service_call_sites"]["handle_frontdoor_turn"]), 3)
		self.assertFalse(report["test_import_evidence"]["root_imports"])
		self.assertTrue(report["test_import_evidence"]["package_imports"])

	def test_frontdoor_source_append_sites_are_all_mapped(self):
		report = build_frontdoor_emission_mapping_report(root_path=PROJECT_ROOT)
		emitters = report["frontdoor_emitters"]
		source_sites = []
		for relative_path in (PROJECT_RELATIVE_PACKAGE_FRONTDOOR, PROJECT_RELATIVE_ROOT_FRONTDOOR):
			text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8", errors="ignore")
			for index, line in enumerate(text.splitlines(), start=1):
				if 'append_message(session_doc, "assistant"' in line:
					source_sites.append((relative_path, index))
		mapped_sites = [
			(item["relative_file_path"], line)
			for item in emitters
			for line in item["direct_assistant_append_lines"]
		]

		self.assertEqual(sorted(source_sites), sorted(mapped_sites))
		self.assertEqual(len(source_sites), 0)

	def test_duplicate_summary_records_root_facade(self):
		report = build_frontdoor_emission_mapping_report(root_path=PROJECT_ROOT)
		diff_summary = report["diff_summary"]

		self.assertFalse(diff_summary["files_identical"])
		self.assertGreater(diff_summary["package_line_count"], diff_summary["root_line_count"])
		self.assertTrue(diff_summary["package_has_fresh_breakout_helper"])
		self.assertFalse(diff_summary["root_has_fresh_breakout_helper"])
		self.assertTrue(diff_summary["root_is_compatibility_facade"])
		self.assertIn("compatibility facade", diff_summary["root_duplicate_drift_reason"])

	def test_proposed_ec4u_write_scope_keeps_service_forbidden_and_root_facade_allowed(self):
		report = build_frontdoor_emission_mapping_report(root_path=PROJECT_ROOT)
		write_scope = report["proposed_ec4c_write_scope"]

		self.assertIn(PROJECT_RELATIVE_PACKAGE_FRONTDOOR, write_scope["allowed_files"])
		self.assertIn(PROJECT_RELATIVE_ROOT_FRONTDOOR, write_scope["allowed_files"])
		self.assertNotIn(PROJECT_RELATIVE_ROOT_FRONTDOOR, write_scope["forbidden_files"])
		self.assertIn(PROJECT_RELATIVE_SERVICE, write_scope["forbidden_files"])
		self.assertEqual(
			write_scope["write_scope_decision"],
			"ec_4u_root_duplicate_converted_to_facade_service_unchanged",
		)

	def test_markdown_and_files_are_reviewer_friendly(self):
		report = build_frontdoor_emission_mapping_report(root_path=PROJECT_ROOT)
		markdown = render_frontdoor_emission_mapping_markdown(report)

		self.assertIn("EC-4B Frontdoor Emission Mapping", markdown)
		self.assertIn("frontdoor_lane_package_governed_report_or_projection", markdown)
		self.assertIn("frontdoor_lane_root_duplicate", markdown)
		self.assertIn("Proposed EC-4C Write Scope", markdown)
		with tempfile.TemporaryDirectory() as temp_dir:
			result = write_frontdoor_emission_mapping_files(
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
				"enterprise_cleanup_ec_4u_frontdoor_duplicate_facade_closed",
			)


if __name__ == "__main__":
	unittest.main()
