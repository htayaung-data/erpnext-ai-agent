from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.final_answer_emission_closure_checkpoint import (
	EC4O_COUNTERPART_DECISION,
	EC4P_RECOMMENDATION_QA_RISK_REVIEW,
	FINAL_ANSWER_EMISSION_CLOSURE_CHECKPOINT_CONTRACT_TYPE,
	build_final_answer_emission_closure_checkpoint_report,
	render_final_answer_emission_closure_checkpoint_markdown,
	write_final_answer_emission_closure_checkpoint_files,
)


PROJECT_ROOT = Path(__file__).resolve().parents[6]


class FinalAnswerEmissionClosureCheckpointContractTests(unittest.TestCase):
	def test_closure_checkpoint_consumes_fresh_ec4n_ready_report(self):
		report = build_final_answer_emission_closure_checkpoint_report(root_path=PROJECT_ROOT)
		ec4n = report["fresh_ec4n_summary"]
		ec4q = report["fresh_ec4q_summary"]

		self.assertEqual(report["type"], FINAL_ANSWER_EMISSION_CLOSURE_CHECKPOINT_CONTRACT_TYPE)
		self.assertEqual(report["slice_id"], "ec_4u_duplicate_wrapper_visible_context_closure")
		self.assertEqual(report["ec4o_counterpart_decision"], EC4O_COUNTERPART_DECISION)
		self.assertFalse(report["runtime_behavior_changed"])
		self.assertEqual(ec4n["final_recommendation"], "enterprise_cleanup_ec_4n_ready_for_counterpart_review")
		self.assertEqual(ec4n["potential_leak_count"], 0)
		self.assertEqual(ec4n["potential_leak_path_ids"], [])
		self.assertEqual(ec4q["final_recommendation"], "enterprise_cleanup_ec_4q_a_ready_for_counterpart_review")
		self.assertEqual(ec4q["inventory_item_count"], 1)
		self.assertEqual(ec4q["active_direct_assistant_append_count"], 0)
		self.assertEqual(report["final_recommendation"], EC4P_RECOMMENDATION_QA_RISK_REVIEW)

	def test_direct_no_leak_summary_covers_ec4o_migrated_lanes(self):
		report = build_final_answer_emission_closure_checkpoint_report(root_path=PROJECT_ROOT)
		rows = {row["lane_id"]: row for row in report["direct_no_leak_test_summary_by_lane"]}

		self.assertEqual(
			set(rows),
			{
				"frontdoor_governed_report_and_kpi_definition",
				"compiled_support_result_answer",
				"reasoning_business_answer",
				"nbu_governed_requery_entity_detail",
				"legacy_runtime_business_or_boundary_answer",
				"entity_followup_success_and_failure",
			},
		)
		for row in rows.values():
			self.assertEqual(row["status"], "verified_pass")
			self.assertIn("blocked_authority_writes_no_assistant_message", row["guarantees"])
			self.assertIn("blocked_authority_writes_no_tool_trace_answer_text", row["guarantees"])
			self.assertIn(
				"blocked_authority_writes_no_business_artifact_rendered_narrative_grounded_payload",
				row["guarantees"],
			)

	def test_remaining_high_risk_paths_are_classified_not_migrated(self):
		report = build_final_answer_emission_closure_checkpoint_report(root_path=PROJECT_ROOT)
		rows = {row["path_id"]: row for row in report["remaining_high_risk_classification"]}

		self.assertEqual(set(rows), {"service_append_message_wrapper"})
		self.assertEqual(rows["service_append_message_wrapper"]["decision"], "monitor_only_do_not_hard_gate_raw_wrapper")
		self.assertEqual(report["frontdoor_duplicate_decision"]["status"], "closed_by_compatibility_facade")
		self.assertEqual(report["visible_context_outer_call_site_proof"]["status"], "runtime_blocked_authority_probe_passed")
		self.assertIn("no_service_append_wrapper_migration", report["non_goals"])
		self.assertIn("no_active_package_frontdoor_behavior_change", report["non_goals"])

	def test_audit_hardening_note_is_explicit(self):
		report = build_final_answer_emission_closure_checkpoint_report(root_path=PROJECT_ROOT)
		note = report["audit_limitation_note"]
		backlog = set(report["audit_hardening_backlog"])

		self.assertIn("not a complete taint-analysis engine", note)
		self.assertIn("unknown append_tool_payload", note)
		self.assertIn("classify_unknown_append_tool_payload_sources_more_strictly", backlog)
		self.assertIn("add_source_allowlist_or_provenance_for_additional_tool_payloads", backlog)

	def test_markdown_and_file_generation_are_reviewer_friendly(self):
		report = build_final_answer_emission_closure_checkpoint_report(root_path=PROJECT_ROOT)
		markdown = render_final_answer_emission_closure_checkpoint_markdown(report)

		self.assertIn("EC-4U Final-Answer Emission Closure Packet", markdown)
		self.assertIn("Fresh EC-4N Summary", markdown)
		self.assertIn("Fresh EC-4Q-A Summary", markdown)
		self.assertIn("Duplicate / Wrapper / Visible-Context Decisions", markdown)
		self.assertIn("Direct No-Leak Tests By Lane", markdown)
		self.assertIn("Audit Hardening Backlog", markdown)
		self.assertIn(EC4P_RECOMMENDATION_QA_RISK_REVIEW, markdown)
		with tempfile.TemporaryDirectory() as temp_dir:
			result = write_final_answer_emission_closure_checkpoint_files(
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
			self.assertEqual(loaded["final_recommendation"], EC4P_RECOMMENDATION_QA_RISK_REVIEW)


if __name__ == "__main__":
	unittest.main()
