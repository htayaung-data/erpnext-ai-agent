import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_import import IMPORT_PARSE_ACCEPTED
from ai_assistant_ui.qwen_chat.manual_uat_sample_fixture import (
	DEFAULT_SAMPLE_SCENARIO_IDS,
	EVIDENCE_MODE_SAMPLE_FIXTURE,
	MANUAL_UAT_SAMPLE_FIXTURE_CONTRACT_TYPE,
	MANUAL_UAT_SAMPLE_FIXTURE_SUITE_ID,
	PRODUCTION_RELEASE_BOUNDARY,
	SAMPLE_CAPTURE_SOURCE,
	build_manual_uat_sample_fixture,
	render_manual_uat_sample_fixture_markdown,
	write_manual_uat_sample_fixture_files,
)
from ai_assistant_ui.qwen_chat.regression_suite_governance import (
	BLOCKING_RELEASE,
	GATE_RELEASE_BLOCKING_CONTRACT,
	RELEASE_BLOCKING_SUITE_IDS,
	RUNTIME_NONE,
	build_regression_suite_boundary_contract,
)


class ManualUATSampleFixtureContractTests(unittest.TestCase):
	def test_default_sample_fixture_roundtrip_is_complete_but_not_production_release_ready(self):
		fixture = build_manual_uat_sample_fixture(generated_at="2026-05-13T16:45:00+06:30")

		self.assertEqual(fixture["type"], MANUAL_UAT_SAMPLE_FIXTURE_CONTRACT_TYPE)
		self.assertEqual(fixture["evidence_mode"], EVIDENCE_MODE_SAMPLE_FIXTURE)
		self.assertEqual(fixture["release_boundary"], PRODUCTION_RELEASE_BOUNDARY)
		self.assertTrue(fixture["fixture_complete"])
		self.assertTrue(fixture["sample_roundtrip_complete"])
		self.assertTrue(fixture["sample_bundle_release_ready"])
		self.assertTrue(fixture["sample_bundle_contract"]["roundtrip_complete"])
		self.assertTrue(fixture["sample_bundle_contract"]["release_ready"])
		self.assertFalse(fixture["production_release_ready"])
		self.assertFalse(fixture["release_ready"])
		self.assertIn(PRODUCTION_RELEASE_BOUNDARY, fixture["release_blocking_reasons"])
		self.assertEqual(fixture["requested_scenario_ids"], DEFAULT_SAMPLE_SCENARIO_IDS)
		self.assertEqual(fixture["capture_record_count"], len(DEFAULT_SAMPLE_SCENARIO_IDS))

	def test_sample_capture_records_are_import_ready_and_labeled_as_sample_only(self):
		fixture = build_manual_uat_sample_fixture(generated_at="2026-05-13T16:45:00+06:30")

		for record in fixture["sample_capture_records"]:
			with self.subTest(record=record["scenario_id"]):
				self.assertEqual(record["evidence_mode"], EVIDENCE_MODE_SAMPLE_FIXTURE)
				self.assertEqual(record["release_boundary"], PRODUCTION_RELEASE_BOUNDARY)
				self.assertEqual(record["capture_source"], SAMPLE_CAPTURE_SOURCE)
				self.assertTrue(record["dry_run_only"])
				self.assertTrue(record["raw_answer_text"])
				self.assertTrue(record["raw_trace_text"])
				self.assertTrue(record["observed_trace_fields"])
				self.assertTrue(record["observed_model_role_fields"])
		for import_record in fixture["sample_bundle_contract"]["import_batch_contract"]["records"]:
			with self.subTest(import_record=import_record["scenario_id"]):
				self.assertEqual(import_record["parse_status"], IMPORT_PARSE_ACCEPTED)
				self.assertFalse(import_record["release_blocking"])

	def test_fixture_covers_required_cross_family_sample_scenarios(self):
		fixture = build_manual_uat_sample_fixture(generated_at="2026-05-13T16:45:00+06:30")

		for scenario_id in [
			"visible_ar_after_ap_typed_rank_2",
			"visible_ap_current_rank_2",
			"product_projection_qty_preserves_revenue",
			"product_top7_rank_8_out_of_range",
			"pl_cogs_source_document_rank_2",
			"ar_rank_2_default_prediction_boundary",
			"ar_first_customer_cause_boundary",
			"ar_collection_recommendation_boundary",
			"trace_inspection_model_role_coverage",
		]:
			self.assertIn(scenario_id, fixture["sample_scenario_ids"])
		self.assertIn("accounts_receivable_aging", fixture["family_coverage"])
		self.assertIn("accounts_payable_aging", fixture["family_coverage"])
		self.assertIn("product_revenue_ranking", fixture["family_coverage"])
		self.assertIn("profit_and_loss_cogs_detail", fixture["family_coverage"])
		self.assertIn("visible_context_trace_inspection", fixture["family_coverage"])

	def test_product_out_of_range_boundary_is_preserved_in_sample_fixture(self):
		fixture = build_manual_uat_sample_fixture(
			scenario_ids=["product_top7_rank_8_out_of_range"],
			generated_at="2026-05-13T16:45:00+06:30",
		)
		record = fixture["sample_bundle_contract"]["archive_index_contract"]["records"][0]

		self.assertTrue(fixture["fixture_complete"])
		self.assertEqual(record["observed_policy_boundary"], "visible_context_out_of_range")
		self.assertEqual(record["observed_row_reference"], "none")
		self.assertEqual(record["observed_entity_type"], "item")

	def test_policy_boundary_samples_preserve_prediction_causal_and_recommendation_boundaries(self):
		fixture = build_manual_uat_sample_fixture(
			scenario_ids=[
				"ar_rank_2_default_prediction_boundary",
				"ar_first_customer_cause_boundary",
				"ar_collection_recommendation_boundary",
			],
			generated_at="2026-05-13T16:45:00+06:30",
		)
		boundaries = {
			record["scenario_id"]: record["observed_policy_boundary"]
			for record in fixture["sample_bundle_contract"]["archive_index_contract"]["records"]
		}

		self.assertTrue(fixture["fixture_complete"])
		self.assertEqual(boundaries["ar_rank_2_default_prediction_boundary"], "prediction_boundary")
		self.assertEqual(boundaries["ar_first_customer_cause_boundary"], "causal_boundary")
		self.assertEqual(boundaries["ar_collection_recommendation_boundary"], "recommendation_boundary")

	def test_trace_inspection_wildcard_expectations_resolve_to_concrete_sample_values(self):
		fixture = build_manual_uat_sample_fixture(
			scenario_ids=["trace_inspection_model_role_coverage"],
			generated_at="2026-05-13T16:45:00+06:30",
		)
		record = fixture["sample_bundle_contract"]["archive_index_contract"]["records"][0]

		self.assertTrue(fixture["fixture_complete"])
		self.assertEqual(record["observed_entity_type"], "customer")
		self.assertEqual(record["observed_row_reference"], "rank_2")
		self.assertEqual(record["observed_authority_source"], "visible_rendered_table")
		self.assertEqual(record["observed_model_role_lane"], "trace_inspection:deterministic")
		self.assertEqual(record["mismatches"], [])
		self.assertEqual(record["missing_fields"], [])

	def test_unknown_sample_scenario_blocks_fixture_completeness(self):
		fixture = build_manual_uat_sample_fixture(
			scenario_ids=["visible_ap_current_rank_2", "future_tax_scenario"],
			generated_at="2026-05-13T16:45:00+06:30",
		)

		self.assertFalse(fixture["fixture_complete"])
		self.assertFalse(fixture["sample_roundtrip_complete"])
		self.assertFalse(fixture["sample_bundle_release_ready"])
		self.assertFalse(fixture["release_ready"])
		self.assertIn("future_tax_scenario", fixture["unknown_scenario_ids"])
		self.assertIn("unknown_sample_scenario_ids", fixture["release_blocking_reasons"])
		self.assertIn("sample_bundle_not_release_ready", fixture["release_blocking_reasons"])

	def test_empty_sample_scenario_set_is_not_complete(self):
		fixture = build_manual_uat_sample_fixture(
			scenario_ids=[],
			generated_at="2026-05-13T16:45:00+06:30",
		)

		self.assertFalse(fixture["fixture_complete"])
		self.assertFalse(fixture["sample_roundtrip_complete"])
		self.assertFalse(fixture["sample_bundle_release_ready"])
		self.assertEqual(fixture["sample_capture_records"], [])
		self.assertIn("sample_roundtrip_not_complete", fixture["release_blocking_reasons"])

	def test_raw_evidence_hashes_are_stable_for_fixed_sample_fixture(self):
		first = build_manual_uat_sample_fixture(generated_at="2026-05-13T16:45:00+06:30")
		second = build_manual_uat_sample_fixture(generated_at="2026-05-13T16:45:00+06:30")

		self.assertEqual(first["raw_evidence_hashes"], second["raw_evidence_hashes"])
		self.assertEqual(len(first["raw_evidence_hashes"]), len(DEFAULT_SAMPLE_SCENARIO_IDS))
		self.assertTrue(all(len(value) == 64 for value in first["raw_evidence_hashes"]))

	def test_markdown_renderer_discloses_sample_boundary_and_bundle_status(self):
		fixture = build_manual_uat_sample_fixture(generated_at="2026-05-13T16:45:00+06:30")
		markdown = render_manual_uat_sample_fixture_markdown(fixture)

		self.assertIn("# S7 Manual UAT Sample Evidence Dry-Run Bundle", markdown)
		self.assertIn(PRODUCTION_RELEASE_BOUNDARY, markdown)
		self.assertIn("Sample evidence is dry-run only", markdown)
		self.assertIn("visible_ar_after_ap_typed_rank_2", markdown)
		self.assertIn("trace_inspection_model_role_coverage", markdown)
		self.assertIn("Bundle roundtrip complete", markdown)

	def test_writer_generates_import_ready_capture_json_and_dry_run_bundle_artifacts(self):
		with tempfile.TemporaryDirectory() as tmp:
			capture_json_path = Path(tmp) / "sample_captures.json"
			bundle_json_path = Path(tmp) / "sample_bundle.json"
			bundle_markdown_path = Path(tmp) / "sample_bundle.md"

			first = write_manual_uat_sample_fixture_files(
				generated_at="2026-05-13T16:45:00+06:30",
				capture_json_path=str(capture_json_path),
				bundle_json_path=str(bundle_json_path),
				bundle_markdown_path=str(bundle_markdown_path),
			)
			first_capture_json = capture_json_path.read_text(encoding="utf-8")
			first_bundle_json = bundle_json_path.read_text(encoding="utf-8")
			first_markdown = bundle_markdown_path.read_text(encoding="utf-8")
			second = write_manual_uat_sample_fixture_files(
				generated_at="2026-05-13T16:45:00+06:30",
				capture_json_path=str(capture_json_path),
				bundle_json_path=str(bundle_json_path),
				bundle_markdown_path=str(bundle_markdown_path),
			)

			self.assertTrue(first["capture_json_artifact_written"])
			self.assertTrue(first["bundle_json_artifact_written"])
			self.assertTrue(first["bundle_markdown_artifact_written"])
			self.assertTrue(second["capture_json_artifact_written"])
			self.assertEqual(first_capture_json, capture_json_path.read_text(encoding="utf-8"))
			self.assertEqual(first_bundle_json, bundle_json_path.read_text(encoding="utf-8"))
			self.assertEqual(first_markdown, bundle_markdown_path.read_text(encoding="utf-8"))
			loaded_captures = json.loads(first_capture_json)
			loaded_bundle = json.loads(first_bundle_json)
			self.assertIsInstance(loaded_captures, list)
			self.assertEqual(len(loaded_captures), len(DEFAULT_SAMPLE_SCENARIO_IDS))
			self.assertEqual(loaded_bundle["type"], MANUAL_UAT_SAMPLE_FIXTURE_CONTRACT_TYPE)
			self.assertFalse(loaded_bundle["release_ready"])
			self.assertIn(PRODUCTION_RELEASE_BOUNDARY, first_markdown)

	def test_s7_6l_sample_fixture_suite_is_release_blocking_in_regression_boundary(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_SAMPLE_FIXTURE_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_SAMPLE_FIXTURE_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_SAMPLE_FIXTURE_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
