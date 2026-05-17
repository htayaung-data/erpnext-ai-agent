import json
import tempfile
import unittest
from pathlib import Path
from typing import Iterable

from ai_assistant_ui.qwen_chat.final_answer_emission_dry_run import (
	ANSWER_TYPE_BUSINESS_FACTUAL,
	ANSWER_TYPE_CONTROL,
	ANSWER_TYPE_ERROR,
	ANSWER_TYPE_GOVERNED_REPORT,
	ANSWER_TYPE_POLICY_BOUNDARY,
	ANSWER_TYPE_REASONING,
	ANSWER_TYPE_TRACE,
	ANSWER_TYPE_VISIBLE_CONTEXT,
	AUTHORIZED_APPEND_SITES,
	EXCLUDED_APPEND_SITES,
	FINAL_ANSWER_EMISSION_DRY_RUN_CONTRACT_TYPE,
	MIGRATED_AUTHORIZED_PATHS,
	RECOMMENDATION_READY,
	RISK_HIGH,
	build_final_answer_emission_dry_run_report,
	main,
	render_final_answer_emission_dry_run_markdown,
	write_final_answer_emission_dry_run_files,
)


def _short_qwen_path(relative_file_path: str) -> str:
	normalized = str(relative_file_path or "").replace("\\", "/")
	marker = "/qwen_chat/"
	return normalized.split(marker, 1)[1] if marker in normalized else normalized


def _first_line_reference(line_reference: str) -> int:
	first = str(line_reference or "").split(",", 1)[0].split("-", 1)[0].strip()
	return int(first)


def _assistant_append_source_sites() -> set[tuple[str, int]]:
	qwen_chat_dir = Path(__file__).resolve().parents[1] / "qwen_chat"
	sites: set[tuple[str, int]] = set()
	for path in qwen_chat_dir.rglob("*.py"):
		parts = set(path.parts)
		if "evaluation" in parts or "probes" in parts:
			continue
		lines = path.read_text(encoding="utf-8").splitlines()
		for index, line in enumerate(lines, start=1):
			if "append_message(" not in line and "_append_message(" not in line:
				continue
			if line.lstrip().startswith("def "):
				continue
			window = "\n".join(lines[index - 1 : index + 8])
			if '"assistant"' in window or "'assistant'" in window:
				sites.add((path.relative_to(qwen_chat_dir).as_posix(), index))
	return sites


def _sites_from_report_items(items: Iterable[dict], *, id_field: str) -> set[tuple[str, int]]:
	sites: set[tuple[str, int]] = set()
	for item in items:
		self_id = item.get(id_field)
		if not self_id:
			continue
		sites.add((_short_qwen_path(item["relative_file_path"]), _first_line_reference(item["line_reference"])))
	return sites


class FinalAnswerEmissionDryRunContractTests(unittest.TestCase):
	def test_report_exposes_dry_run_scope_without_runtime_enforcement(self):
		report = build_final_answer_emission_dry_run_report(reviewer="contract_test", status_count=259)

		self.assertEqual(report["type"], FINAL_ANSWER_EMISSION_DRY_RUN_CONTRACT_TYPE)
		self.assertEqual(report["slice_id"], "ec_3_final_answer_hard_gate_dry_run")
		self.assertFalse(report["hard_runtime_blocking_enabled"])
		self.assertFalse(report["runtime_behavior_changed"])
		self.assertEqual(report["current_dirty_status_count"], 259)
		self.assertEqual(report["final_recommendation"], RECOMMENDATION_READY)
		self.assertEqual(report["active_runtime_direct_assistant_append_count"], 0)
		self.assertEqual(report["authorized_runtime_append_sink_count"], 2)
		self.assertEqual(report["excluded_non_runtime_append_count"], 1)
		self.assertEqual(report["total_source_assistant_append_sites_observed"], 3)

	def test_inventory_covers_required_active_answer_classes(self):
		report = build_final_answer_emission_dry_run_report()
		answer_type_counts = report["answer_type_counts"]

		for answer_type in [
			ANSWER_TYPE_BUSINESS_FACTUAL,
			ANSWER_TYPE_VISIBLE_CONTEXT,
			ANSWER_TYPE_GOVERNED_REPORT,
			ANSWER_TYPE_POLICY_BOUNDARY,
			ANSWER_TYPE_REASONING,
			ANSWER_TYPE_TRACE,
			ANSWER_TYPE_ERROR,
			ANSWER_TYPE_CONTROL,
		]:
			self.assertGreater(answer_type_counts.get(answer_type, 0), 0, answer_type)
		self.assertEqual(report["missing_answer_types"], [])

	def test_high_risk_paths_include_business_and_fallback_emitters(self):
		report = build_final_answer_emission_dry_run_report()
		high_risk_paths = set(report["high_risk_paths"])

		self.assertNotIn("entity_followup_success", high_risk_paths)
		self.assertNotIn("nbu_governed_requery_entity_detail", high_risk_paths)
		self.assertNotIn("legacy_runtime_business_or_boundary_answer", high_risk_paths)
		self.assertEqual(report["high_risk_paths"], ["service_append_message_wrapper"])
		self.assertGreaterEqual(report["risk_counts"][RISK_HIGH], 1)

	def test_each_inventory_entry_has_file_reference_authority_status_and_ec4_action(self):
		report = build_final_answer_emission_dry_run_report()

		self.assertEqual(report["missing_required_fields"], {})
		for item in report["emission_path_inventory"]:
			self.assertTrue(item["relative_file_path"].endswith(".py"))
			self.assertTrue(item["line_reference"])
			self.assertTrue(item["authority_availability_status"])
			self.assertTrue(item["audit_timing"])
			self.assertTrue(item["ec4_action"])

	def test_excluded_append_sites_classify_phase8_smoke_seed_helper(self):
		report = build_final_answer_emission_dry_run_report()
		excluded = report["excluded_append_sites"]

		self.assertEqual(excluded, EXCLUDED_APPEND_SITES)
		self.assertEqual(excluded[0]["relative_file_path"], "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/phase8_hardening_support.py")
		self.assertEqual(excluded[0]["line_reference"], "68")
		self.assertIn("Smoke/recovery seed helper", excluded[0]["exclusion_reason"])

	def test_authorized_append_sites_classify_ec4_helper_sinks(self):
		report = build_final_answer_emission_dry_run_report()
		authorized = report["authorized_append_sites"]

		self.assertEqual(authorized, AUTHORIZED_APPEND_SITES)
		self.assertEqual(len(authorized), 2)
		self.assertTrue(all(item["relative_file_path"].endswith("qwen_chat/authorized_emission.py") for item in authorized))
		self.assertIn("final-answer authority preflight", authorized[1]["authorization_reason"])

	def test_ec4a_through_ec4t1_paths_are_recorded_as_migrated_to_authorized_helper(self):
		report = build_final_answer_emission_dry_run_report()
		migrated = report["migrated_authorized_paths"]
		path_ids = {item["path_id"] for item in migrated}

		self.assertEqual(migrated, MIGRATED_AUTHORIZED_PATHS)
		self.assertIn("visible_context_followup_filter_boundary", path_ids)
		self.assertIn("visible_context_followup_answer", path_ids)
		self.assertIn("frontdoor_lane_package_governed_report_or_projection", path_ids)
		self.assertIn("frontdoor_lane_package_governed_kpi_definition", path_ids)
		self.assertIn("compiled_support_result_answer", path_ids)
		self.assertIn("reasoning_lane_business_answer", path_ids)
		self.assertIn("reasoning_lane_guardrail_boundary", path_ids)
		self.assertIn("nbu_governed_requery_entity_detail", path_ids)
		self.assertIn("entity_followup_failure", path_ids)
		self.assertIn("entity_followup_success", path_ids)
		self.assertIn("legacy_runtime_client_error", path_ids)
		self.assertIn("legacy_runtime_business_or_boundary_answer", path_ids)
		self.assertIn("artifact_boundary_evidence_answer", path_ids)
		self.assertIn("artifact_boundary_grounded_evidence_refusal", path_ids)
		self.assertIn("artifact_boundary_enrichment_refusal", path_ids)
		self.assertIn("local_followup_transform", path_ids)
		self.assertIn("runtime_gate_out_of_scope_boundary", path_ids)
		self.assertIn("service_out_of_scope_domain_boundary", path_ids)
		self.assertIn("service_known_unsupported_erp_domain_boundary", path_ids)
		self.assertIn("visible_context_trace_inspection", path_ids)
		self.assertIn("nbu_presentation_safe_response", path_ids)
		self.assertIn("clarification_show_options", path_ids)
		self.assertIn("clarification_pending_reask_or_stop", path_ids)
		self.assertIn("recovery_guidance_answer", path_ids)
		self.assertIn("service_prior_branch_clarification_restore", path_ids)
		self.assertIn("service_compound_continue_completed", path_ids)
		self.assertIn("service_compound_stop", path_ids)
		self.assertEqual(len(migrated), 27)
		self.assertEqual(
			{item["migration_slice"] for item in migrated},
			{"EC-4A", "EC-4C", "EC-4E", "EC-4G", "EC-4I", "EC-4K", "EC-4M", "EC-4R1", "EC-4R2", "EC-4S1", "EC-4S2", "EC-4T1", "EC-4T2"},
		)
		self.assertTrue(all(item["authorization_helper"] == "emit_authorized_assistant_answer" for item in migrated))

	def test_source_scan_append_sites_are_inventory_or_explicit_exclusions(self):
		report = build_final_answer_emission_dry_run_report()
		observed_sites = _assistant_append_source_sites()
		active_sites = _sites_from_report_items(
			[item for item in report["emission_path_inventory"] if item.get("direct_assistant_append")],
			id_field="path_id",
		)
		authorized_sites = _sites_from_report_items(report["authorized_append_sites"], id_field="site_id")
		excluded_sites = _sites_from_report_items(report["excluded_append_sites"], id_field="site_id")

		self.assertEqual(observed_sites - active_sites - authorized_sites - excluded_sites, set())
		self.assertEqual(active_sites - observed_sites, set())
		self.assertEqual(authorized_sites - observed_sites, set())
		self.assertEqual(excluded_sites - observed_sites, set())

	def test_ec4_design_recommends_authorized_helper_not_lowest_append_only(self):
		report = build_final_answer_emission_dry_run_report()
		design = report["proposed_ec4_design"]

		self.assertEqual(design["central_helper"], "emit_authorized_assistant_answer")
		self.assertIn("low-level append", design["why_not_lowest_append_only"])
		self.assertIn("passed", report["ec4_allowed_preflight_statuses"])
		self.assertIn("bounded", report["ec4_allowed_preflight_statuses"])
		self.assertIn("missing_authority", report["ec4_blocked_preflight_statuses"])

	def test_markdown_renders_reviewer_sections(self):
		report = build_final_answer_emission_dry_run_report(status_count=259)
		markdown = render_final_answer_emission_dry_run_markdown(report)

		self.assertIn("EC-3 Final-Answer Hard Gate Design / Dry Run", markdown)
		self.assertIn("Emission Path Inventory", markdown)
		self.assertIn("Authorized Append Sinks", markdown)
		self.assertIn("Migrated Authorized Paths", markdown)
		self.assertIn("Excluded Append Sites", markdown)
		self.assertIn("Proposed EC-4 Design", markdown)
		self.assertIn("EC-4 Tests Required", markdown)
		self.assertIn(RECOMMENDATION_READY, markdown)

	def test_write_report_files_outputs_json_and_markdown(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			report = write_final_answer_emission_dry_run_files(
				root_path=root,
				out_dir="generated/ec3",
				reviewer="contract_test",
				status_count=259,
			)

			json_path = Path(report["report_json_artifact_path"])
			markdown_path = Path(report["report_markdown_artifact_path"])
			self.assertTrue(json_path.exists())
			self.assertTrue(markdown_path.exists())
			self.assertEqual(json.loads(json_path.read_text(encoding="utf-8"))["final_recommendation"], RECOMMENDATION_READY)

	def test_main_accepts_status_count_argument(self):
		with tempfile.TemporaryDirectory() as tmp:
			exit_code = main(
				[
					"--root-path",
					tmp,
					"--out-dir",
					"generated/ec3",
					"--reviewer",
					"contract_test",
					"--status-count",
					"262",
				]
			)
			report_path = Path(tmp) / "generated/ec3/qwen_ec3_final_answer_emission_dry_run_report.json"

			self.assertEqual(exit_code, 0)
			self.assertEqual(json.loads(report_path.read_text(encoding="utf-8"))["current_dirty_status_count"], 262)


if __name__ == "__main__":
	unittest.main()
