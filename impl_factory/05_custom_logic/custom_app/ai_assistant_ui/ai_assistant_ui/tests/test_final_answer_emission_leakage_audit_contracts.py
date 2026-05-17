from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.final_answer_emission_dry_run import (
	MIGRATED_AUTHORIZED_PATHS,
	build_final_answer_emission_dry_run_report,
)
from ai_assistant_ui.qwen_chat.final_answer_emission_leakage_audit import (
	BLOCKED_LEAK_CHECKS,
	FINAL_ANSWER_EMISSION_LEAKAGE_AUDIT_CONTRACT_TYPE,
	LEAK_STATUS_NOT_APPLICABLE,
	LEAK_STATUS_PASS,
	LEAK_STATUS_POTENTIAL_LEAK,
	RECOMMENDATION_READY,
	build_final_answer_emission_leakage_audit_report,
	render_final_answer_emission_leakage_audit_markdown,
	write_final_answer_emission_leakage_audit_files,
)


PROJECT_ROOT = Path(__file__).resolve().parents[6]


class FinalAnswerEmissionLeakageAuditContractTests(unittest.TestCase):
	def test_report_covers_every_migrated_authorized_path(self):
		report = build_final_answer_emission_leakage_audit_report(root_path=PROJECT_ROOT)
		migrated_ids = {item["path_id"] for item in MIGRATED_AUTHORIZED_PATHS}
		audit_ids = {item["path_id"] for item in report["migrated_lane_audit"]}

		self.assertEqual(report["type"], FINAL_ANSWER_EMISSION_LEAKAGE_AUDIT_CONTRACT_TYPE)
		self.assertEqual(report["slice_id"], "ec_4n_final_answer_emission_leakage_audit")
		self.assertFalse(report["runtime_behavior_changed"])
		self.assertFalse(report["hard_runtime_blocking_enabled"])
		self.assertEqual(audit_ids, migrated_ids)
		self.assertEqual(report["migrated_path_count"], len(MIGRATED_AUTHORIZED_PATHS))
		self.assertEqual(report["missing_evidence_path_ids"], [])

	def test_each_migrated_path_has_machine_checkable_blocked_leakage_fields(self):
		report = build_final_answer_emission_leakage_audit_report(root_path=PROJECT_ROOT)

		for row in report["migrated_lane_audit"]:
			self.assertIn(
				row["blocked_leakage_status"],
				{LEAK_STATUS_PASS, LEAK_STATUS_NOT_APPLICABLE, LEAK_STATUS_POTENTIAL_LEAK},
			)
			self.assertTrue(row["blocked_probe_reason"], row["path_id"])
			self.assertTrue(row["evidence_tests"], row["path_id"])
			self.assertEqual(set(row["blocked_leakage_checks"].keys()), set(BLOCKED_LEAK_CHECKS))
			self.assertGreaterEqual(row["helper_call_count"], 1, row["path_id"])

	def test_ec4o_clears_known_potential_pre_authority_payload_leak_paths(self):
		report = build_final_answer_emission_leakage_audit_report(root_path=PROJECT_ROOT)
		potential = set(report["potential_leak_path_ids"])

		for path_id in {
			"frontdoor_lane_package_governed_report_or_projection",
			"frontdoor_lane_package_governed_kpi_definition",
			"compiled_support_result_answer",
			"reasoning_lane_business_answer",
			"nbu_governed_requery_entity_detail",
			"legacy_runtime_business_or_boundary_answer",
			"artifact_boundary_evidence_answer",
			"local_followup_transform",
			"runtime_gate_out_of_scope_boundary",
			"service_out_of_scope_domain_boundary",
			"service_known_unsupported_erp_domain_boundary",
			"visible_context_trace_inspection",
			"nbu_presentation_safe_response",
			"clarification_show_options",
			"clarification_pending_reask_or_stop",
			"recovery_guidance_answer",
			"service_prior_branch_clarification_restore",
			"service_compound_continue_completed",
			"service_compound_stop",
		}:
			self.assertNotIn(path_id, potential)
			row = {item["path_id"]: item for item in report["migrated_lane_audit"]}[path_id]
			self.assertEqual(row["blocked_leakage_status"], LEAK_STATUS_PASS)
			self.assertEqual(row["pre_helper_business_payload_risks"], [])
			self.assertEqual(row["post_helper_payload_risks"], [])
		self.assertEqual(report["blocked_leakage_potential_leak_count"], len(potential))
		self.assertEqual(report["final_recommendation"], RECOMMENDATION_READY)

	def test_ec4m_a_entity_followup_paths_are_clean_after_preauthority_payload_fix(self):
		report = build_final_answer_emission_leakage_audit_report(root_path=PROJECT_ROOT)
		rows = {item["path_id"]: item for item in report["migrated_lane_audit"]}

		for path_id in ["entity_followup_success", "entity_followup_failure"]:
			self.assertEqual(rows[path_id]["blocked_leakage_status"], LEAK_STATUS_PASS)
			self.assertEqual(rows[path_id]["pre_helper_business_payload_risks"], [])
			self.assertNotIn(path_id, report["potential_leak_path_ids"])

	def test_reasoning_business_path_records_answer_text_tool_payload_fix(self):
		report = build_final_answer_emission_leakage_audit_report(root_path=PROJECT_ROOT)
		row = {
			item["path_id"]: item for item in report["migrated_lane_audit"]
		}["reasoning_lane_business_answer"]
		serialized_risks = json.dumps(row["pre_helper_business_payload_risks"])

		self.assertEqual(row["blocked_leakage_status"], LEAK_STATUS_PASS)
		self.assertNotIn("reasoning execution payload can contain answer_text", serialized_risks)
		self.assertEqual(row["blocked_leakage_checks"]["no_tool_trace_answer_text"], "pass")
		self.assertEqual(row["blocked_leakage_checks"]["no_post_helper_payload_after_block"], "pass")

	def test_remaining_high_risk_paths_are_classified_not_migrated(self):
		report = build_final_answer_emission_leakage_audit_report(root_path=PROJECT_ROOT)
		remaining = {item["path_id"]: item for item in report["remaining_high_risk_paths"]}

		self.assertEqual(set(remaining), {"service_append_message_wrapper"})
		self.assertEqual(
			remaining["service_append_message_wrapper"]["ec4n_decision"],
			"classify_only_do_not_migrate_in_ec4n",
		)

	def test_dry_run_counts_reflect_ec4t1_control_trace_migration(self):
		report = build_final_answer_emission_leakage_audit_report(root_path=PROJECT_ROOT)
		dry = report["dry_run_counts"]
		direct = build_final_answer_emission_dry_run_report()

		self.assertEqual(dry["active_runtime_direct_assistant_append_count"], 0)
		self.assertEqual(dry["authorized_runtime_append_sink_count"], 2)
		self.assertEqual(dry["excluded_non_runtime_append_count"], 1)
		self.assertEqual(dry["total_source_assistant_append_sites_observed"], 3)
		self.assertEqual(dry["migrated_authorized_path_count"], 27)
		self.assertEqual(dry["high_risk_paths"], direct["high_risk_paths"])

	def test_markdown_and_file_generation_are_reviewer_friendly(self):
		report = build_final_answer_emission_leakage_audit_report(root_path=PROJECT_ROOT)
		markdown = render_final_answer_emission_leakage_audit_markdown(report)

		self.assertIn("EC-4N Final-Answer Emission Leakage Audit", markdown)
		self.assertIn("Migrated Lane Audit", markdown)
		self.assertIn("Potential Leak Paths", markdown)
		self.assertIn("frontdoor_lane_package_governed_kpi_definition", markdown)
		self.assertIn(RECOMMENDATION_READY, markdown)
		with tempfile.TemporaryDirectory() as temp_dir:
			result = write_final_answer_emission_leakage_audit_files(
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
