from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.final_answer_remaining_append_mapping import (
	DECISION_EXEMPT_WITH_CONTRACT,
	DECISION_MIGRATE,
	DECISION_MONITOR_ONLY,
	FINAL_ANSWER_REMAINING_APPEND_MAPPING_CONTRACT_TYPE,
	RECOMMENDATION_READY,
	build_final_answer_remaining_append_mapping_report,
	render_final_answer_remaining_append_mapping_markdown,
	write_final_answer_remaining_append_mapping_files,
)


PROJECT_ROOT = Path(__file__).resolve().parents[6]


class FinalAnswerRemainingAppendMappingContractTests(unittest.TestCase):
	def test_count_correction_separates_inventory_items_from_direct_answer_lanes(self):
		report = build_final_answer_remaining_append_mapping_report(root_path=PROJECT_ROOT)

		self.assertEqual(report["type"], FINAL_ANSWER_REMAINING_APPEND_MAPPING_CONTRACT_TYPE)
		self.assertEqual(report["slice_id"], "ec_4q_a_remaining_append_mapping")
		self.assertEqual(report["inventory_item_count"], 1)
		self.assertEqual(report["active_direct_assistant_append_count"], 0)
		self.assertEqual(report["low_level_wrapper_count"], 1)
		self.assertEqual(report["authorized_helper_sink_count"], 2)
		self.assertEqual(report["excluded_non_runtime_count"], 1)
		self.assertIn("excludes the low-level wrapper", report["count_correction_note"])
		self.assertFalse(report["runtime_behavior_changed"])

	def test_every_remaining_path_has_required_mapping_fields_and_decision(self):
		report = build_final_answer_remaining_append_mapping_report(root_path=PROJECT_ROOT)

		for row in report["remaining_append_inventory"]:
			for field in [
				"path_id",
				"relative_file_path",
				"function_name",
				"line_reference",
				"active_import_status",
				"direct_append_count",
				"answer_class",
				"current_authority_behavior",
				"pre_helper_payload_behavior",
				"post_helper_payload_behavior",
				"leak_risk",
				"decision",
				"required_test_before_closure",
			]:
				if field == "direct_append_count":
					self.assertIsInstance(row.get(field), int, (row.get("path_id"), field))
				else:
					self.assertTrue(str(row.get(field) or "").strip(), (row.get("path_id"), field))

	def test_decision_categories_match_counterpart_sequence(self):
		report = build_final_answer_remaining_append_mapping_report(root_path=PROJECT_ROOT)
		rows = {row["path_id"]: row for row in report["remaining_append_inventory"]}

		for path_id in [
			"frontdoor_lane_root_duplicate",
			"runtime_gate_out_of_scope_boundary",
			"service_out_of_scope_domain_boundary",
			"service_known_unsupported_erp_domain_boundary",
			"artifact_boundary_evidence_answer",
			"artifact_boundary_grounded_evidence_refusal",
			"artifact_boundary_enrichment_refusal",
			"local_followup_transform",
			"visible_context_trace_inspection",
			"nbu_presentation_safe_response",
			"clarification_show_options",
			"clarification_pending_reask_or_stop",
			"recovery_guidance_answer",
			"service_prior_branch_clarification_restore",
			"service_compound_continue_completed",
			"service_compound_stop",
		]:
			self.assertNotIn(path_id, rows)
		self.assertEqual(rows["service_append_message_wrapper"]["decision"], DECISION_MONITOR_ONLY)
		duplicate = report["frontdoor_duplicate_closure"]
		self.assertEqual(duplicate["status"], "closed_by_compatibility_facade")
		self.assertEqual(duplicate["direct_append_count"], 0)

	def test_visible_context_call_site_sources_have_runtime_blocked_authority_probe(self):
		report = build_final_answer_remaining_append_mapping_report(root_path=PROJECT_ROOT)
		proof = report["visible_context_call_site_proof"]
		sources = {row["source_name"]: row for row in proof["allowed_additional_payload_sources"]}

		self.assertFalse(proof["release_blocking"])
		self.assertEqual(proof["proof_type"], "blocked_authority_runtime_probe")
		self.assertIn("no_business_evidence_tool_payload_leak", proof["runtime_probe_guarantees"])
		self.assertIn("Runtime probe", proof["limitation"])
		self.assertEqual(set(sources), {"nbu_shadow_tool_payloads", "sequence_cleanup_tool_payloads", "empty_payload_list"})
		for source in sources.values():
			self.assertFalse(source["business_answer_text_allowed"])
			self.assertIn(source["source_classification"], {"control_shadow_payload", "compound_control_payload", "no_payload"})

	def test_source_scan_has_no_unclassified_assistant_append_sites(self):
		report = build_final_answer_remaining_append_mapping_report(root_path=PROJECT_ROOT)
		scan = report["source_append_scan"]

		self.assertGreaterEqual(scan["observed_source_append_site_count"], 4)
		self.assertEqual(len(scan["explicit_ec4q_excluded_source_append_sites"]), 3)
		self.assertEqual(scan["unclassified_source_append_site_count"], 0)
		self.assertEqual(scan["unclassified_source_append_sites"], [])
		self.assertEqual(report["blocking_reasons"], [])
		self.assertEqual(report["final_recommendation"], RECOMMENDATION_READY)

	def test_markdown_and_file_generation_are_reviewer_friendly(self):
		report = build_final_answer_remaining_append_mapping_report(root_path=PROJECT_ROOT)
		markdown = render_final_answer_remaining_append_mapping_markdown(report)

		self.assertIn("EC-4Q-A Remaining Append Mapping", markdown)
		self.assertIn("Inventory item count", markdown)
		self.assertIn("Visible Context Call-Site Proof", markdown)
		self.assertIn(RECOMMENDATION_READY, markdown)
		with tempfile.TemporaryDirectory() as temp_dir:
			result = write_final_answer_remaining_append_mapping_files(
				root_path=PROJECT_ROOT,
				out_dir=temp_dir,
				reviewer="unit_test",
			)
			json_path = Path(result["report_json_artifact_path"])
			markdown_path = Path(result["report_markdown_artifact_path"])
			self.assertTrue(json_path.exists())
			self.assertTrue(markdown_path.exists())
			loaded = json.loads(json_path.read_text(encoding="utf-8"))
			self.assertEqual(loaded["reviewer"], "unit_test")
			self.assertEqual(loaded["final_recommendation"], RECOMMENDATION_READY)


if __name__ == "__main__":
	unittest.main()
