import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_archive import (
	MANUAL_UAT_ARCHIVE_INDEX_CONTRACT_TYPE,
	MANUAL_UAT_ARCHIVE_RECORD_CONTRACT_TYPE,
	MANUAL_UAT_ARCHIVE_SUITE_ID,
	build_manual_uat_archive_index,
	build_manual_uat_archive_record,
	render_manual_uat_archive_markdown,
	write_manual_uat_archive_files,
)
from ai_assistant_ui.qwen_chat.manual_uat_evidence import (
	MANUAL_UAT_STATUS_BLOCKED,
	MANUAL_UAT_STATUS_FAIL,
	MANUAL_UAT_STATUS_NOT_RUN,
	MANUAL_UAT_STATUS_PASS,
)
from ai_assistant_ui.qwen_chat.regression_scenario_packs import (
	S7_REGRESSION_SCENARIO_REGISTRY,
	build_regression_scenario_contract,
)
from ai_assistant_ui.qwen_chat.regression_suite_governance import (
	BLOCKING_RELEASE,
	GATE_RELEASE_BLOCKING_CONTRACT,
	RELEASE_BLOCKING_SUITE_IDS,
	RUNTIME_NONE,
	build_regression_suite_boundary_contract,
)


def _scenario_by_id(scenario_id: str):
	for scenario in S7_REGRESSION_SCENARIO_REGISTRY:
		if scenario.get("scenario_id") == scenario_id:
			return build_regression_scenario_contract(scenario)
	raise AssertionError(f"Scenario not found: {scenario_id}")


def _matching_trace_fields(scenario):
	return {
		"route": scenario["expected_route"],
		"artifact_family": scenario["expected_artifact_family"],
		"entity_type": scenario["expected_entity_type"],
		"row_reference": scenario["expected_row_reference"],
		"authority_source": scenario["expected_authority_source"],
		"policy_boundary": scenario["expected_policy_boundary"],
		"answer_mode": scenario["expected_answer_mode"],
	}


def _matching_model_role_fields(scenario):
	model_role_lane = scenario["expected_model_role_lane"]
	lane, _, model_role = model_role_lane.partition(":")
	return {
		"model_role_lane": model_role_lane,
		"lane": lane or model_role_lane,
		"model_role": model_role or model_role_lane,
		"expected_model_role": model_role or model_role_lane,
		"role_compliance": "compliant",
	}


def _passing_import(scenario_id: str):
	scenario = _scenario_by_id(scenario_id)
	return {
		"scenario_id": scenario_id,
		"observed_answer_summary": "Observed answer matched the scenario contract.",
		"observed_trace_fields": _matching_trace_fields(scenario),
		"observed_model_role_fields": _matching_model_role_fields(scenario),
		"uat_status": MANUAL_UAT_STATUS_PASS,
		"reviewed_at": "2026-05-13T11:00:00+06:30",
		"reviewer": "uat@example.com",
	}


class ManualUATArchiveContractTests(unittest.TestCase):
	def test_passing_product_quantity_record_archives_expected_and_observed_contract_fields(self):
		record = build_manual_uat_archive_record(_passing_import("product_projection_qty_preserves_revenue"))

		self.assertEqual(record["type"], MANUAL_UAT_ARCHIVE_RECORD_CONTRACT_TYPE)
		self.assertEqual(record["scenario_id"], "product_projection_qty_preserves_revenue")
		self.assertEqual(record["scenario_pack"], "projection_and_cardinality")
		self.assertTrue(record["scenario_registered"])
		self.assertTrue(record["archive_complete"])
		self.assertFalse(record["release_blocking"])
		self.assertTrue(record["answer_evidence_present"])
		self.assertTrue(record["trace_evidence_present"])
		self.assertTrue(record["model_role_evidence_present"])
		self.assertTrue(record["policy_evidence_present"])
		self.assertTrue(record["authority_evidence_present"])
		self.assertEqual(record["observed_answer_mode"], "projection_preservation_answer")
		self.assertEqual(record["expected_row_reference"], "all_visible_rows")
		self.assertEqual(record["mismatches"], [])
		self.assertEqual(record["missing_fields"], [])

	def test_passing_top5_top7_cardinality_archive_can_be_release_ready_for_expected_subset(self):
		import_record = _passing_import("requested_top5_top7_cardinality")

		index = build_manual_uat_archive_index(
			[import_record],
			expected_scenario_ids=["requested_top5_top7_cardinality"],
			generated_at="2026-05-13T11:15:00+06:30",
		)

		self.assertEqual(index["type"], MANUAL_UAT_ARCHIVE_INDEX_CONTRACT_TYPE)
		self.assertTrue(index["archive_complete"])
		self.assertTrue(index["release_ready"])
		self.assertEqual(index["expected_scenario_count"], 1)
		self.assertEqual(index["archived_record_count"], 1)
		self.assertEqual(index["passed_scenario_count"], 1)
		self.assertEqual(index["missing_evidence_scenario_ids"], [])
		self.assertEqual(index["blocking_failure_scenario_ids"], [])

	def test_missing_trace_evidence_blocks_even_when_status_claims_pass(self):
		source = _passing_import("visible_ar_after_ap_typed_rank_2")
		source["observed_trace_fields"] = {}

		record = build_manual_uat_archive_record(source)

		self.assertFalse(record["archive_complete"])
		self.assertTrue(record["release_blocking"])
		self.assertFalse(record["trace_evidence_present"])
		self.assertIn("observed_trace_fields", record["missing_fields"])

	def test_policy_boundary_mismatch_blocks_release_archive(self):
		source = _passing_import("ar_rank_2_default_prediction_boundary")
		source["observed_trace_fields"]["policy_boundary"] = "none"

		record = build_manual_uat_archive_record(source)

		self.assertFalse(record["archive_complete"])
		self.assertTrue(record["release_blocking"])
		self.assertEqual(record["mismatches"][0]["field"], "expected_policy_boundary")
		self.assertEqual(record["mismatches"][0]["expected"], "prediction_boundary")
		self.assertEqual(record["mismatches"][0]["observed"], "none")

	def test_missing_model_role_evidence_blocks_archive(self):
		source = _passing_import("pl_cogs_source_document_rank_2")
		source["observed_model_role_fields"] = {}

		record = build_manual_uat_archive_record(source)

		self.assertFalse(record["archive_complete"])
		self.assertTrue(record["release_blocking"])
		self.assertFalse(record["model_role_evidence_present"])
		self.assertIn("observed_model_role_fields", record["missing_fields"])

	def test_archive_index_counts_statuses_missing_evidence_and_blocking_failures(self):
		passed = _passing_import("visible_ap_current_rank_2")
		failed = _passing_import("product_top7_rank_8_out_of_range")
		failed["uat_status"] = MANUAL_UAT_STATUS_FAIL
		failed["failure_reason"] = "Assistant invented a rank outside the visible rows."
		blocked = _passing_import("ar_first_customer_cause_boundary")
		blocked["uat_status"] = MANUAL_UAT_STATUS_BLOCKED
		blocked["failure_reason"] = "Trace capture unavailable."
		not_run = {
			"scenario_id": "ar_collection_recommendation_boundary",
			"uat_status": MANUAL_UAT_STATUS_NOT_RUN,
		}

		index = build_manual_uat_archive_index(
			[passed, failed, blocked, not_run],
			expected_scenario_ids=[
				"visible_ap_current_rank_2",
				"product_top7_rank_8_out_of_range",
				"ar_first_customer_cause_boundary",
				"ar_collection_recommendation_boundary",
				"trace_inspection_model_role_coverage",
			],
		)

		self.assertFalse(index["release_ready"])
		self.assertTrue(index["archive_complete"])
		self.assertEqual(index["passed_scenario_count"], 1)
		self.assertEqual(index["failed_scenario_count"], 1)
		self.assertEqual(index["blocked_scenario_count"], 1)
		self.assertEqual(index["not_run_scenario_count"], 1)
		self.assertIn("trace_inspection_model_role_coverage", index["missing_evidence_scenario_ids"])
		self.assertIn("product_top7_rank_8_out_of_range", index["blocking_failure_scenario_ids"])
		self.assertIn("trace_inspection_model_role_coverage", index["blocking_failure_scenario_ids"])

	def test_manual_only_scenario_remains_explicit_manual_acceptance_archive(self):
		record = build_manual_uat_archive_record(_passing_import("browser_manual_end_to_end_uat"))

		self.assertTrue(record["manual_only"])
		self.assertFalse(record["deterministic_reference"])
		self.assertEqual(record["blocking_level"], "manual_acceptance_required")
		self.assertTrue(record["archive_complete"])
		self.assertFalse(record["release_blocking"])

	def test_unknown_scenario_cannot_be_archived_as_pass(self):
		record = build_manual_uat_archive_record(
			{
				"scenario_id": "tax_family_future_unknown_scenario",
				"observed_answer_summary": "Looks good.",
				"uat_status": MANUAL_UAT_STATUS_PASS,
				"reviewed_at": "2026-05-13T11:30:00+06:30",
			}
		)

		self.assertFalse(record["scenario_registered"])
		self.assertTrue(record["unknown_scenario"])
		self.assertFalse(record["archive_complete"])
		self.assertTrue(record["release_blocking"])
		self.assertIn("registered_scenario", record["missing_fields"])
		self.assertEqual(record["mismatches"][0]["field"], "scenario_id")

	def test_markdown_and_json_archive_writers_are_deterministic_and_auditable(self):
		import_records = [
			_passing_import("visible_ar_after_ap_typed_rank_2"),
			_passing_import("visible_ap_current_rank_2"),
		]
		with tempfile.TemporaryDirectory() as tmp:
			json_path = Path(tmp) / "uat_archive.json"
			markdown_path = Path(tmp) / "uat_archive.md"

			first = write_manual_uat_archive_files(
				import_records,
				json_path=str(json_path),
				markdown_path=str(markdown_path),
				expected_scenario_ids=[
					"visible_ar_after_ap_typed_rank_2",
					"visible_ap_current_rank_2",
				],
				generated_at="2026-05-13T11:45:00+06:30",
				reviewer="uat@example.com",
			)
			first_json = json_path.read_text(encoding="utf-8")
			first_markdown = markdown_path.read_text(encoding="utf-8")
			second = write_manual_uat_archive_files(
				import_records,
				json_path=str(json_path),
				markdown_path=str(markdown_path),
				expected_scenario_ids=[
					"visible_ar_after_ap_typed_rank_2",
					"visible_ap_current_rank_2",
				],
				generated_at="2026-05-13T11:45:00+06:30",
				reviewer="uat@example.com",
			)

			self.assertTrue(first["json_artifact_written"])
			self.assertTrue(first["markdown_artifact_written"])
			self.assertTrue(second["json_artifact_written"])
			self.assertEqual(first_json, json_path.read_text(encoding="utf-8"))
			self.assertEqual(first_markdown, markdown_path.read_text(encoding="utf-8"))
			loaded = json.loads(first_json)
			self.assertTrue(loaded["release_ready"])
			self.assertIn("# S7 Manual UAT Evidence Archive", first_markdown)
			self.assertIn("visible_ar_after_ap_typed_rank_2", first_markdown)

	def test_empty_archive_artifact_is_structurally_complete_but_not_release_ready(self):
		index = build_manual_uat_archive_index(
			[],
			expected_scenario_ids=["visible_ar_after_ap_typed_rank_2"],
			generated_at="2026-05-13T12:00:00+06:30",
		)
		markdown = render_manual_uat_archive_markdown(index)

		self.assertTrue(index["archive_complete"])
		self.assertFalse(index["release_ready"])
		self.assertEqual(index["missing_evidence_scenario_ids"], ["visible_ar_after_ap_typed_rank_2"])
		self.assertIn("Missing evidence", markdown)
		self.assertIn("visible_ar_after_ap_typed_rank_2", markdown)

	def test_s7_6h_archive_suite_is_release_blocking_in_regression_boundary(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_ARCHIVE_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_ARCHIVE_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_ARCHIVE_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
