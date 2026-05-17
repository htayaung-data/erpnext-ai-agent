import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_bundle import (
	MANUAL_UAT_BUNDLE_CONTRACT_TYPE,
	MANUAL_UAT_BUNDLE_SUITE_ID,
	build_manual_uat_evidence_bundle,
	render_manual_uat_evidence_bundle_markdown,
	write_manual_uat_evidence_bundle_files,
)
from ai_assistant_ui.qwen_chat.manual_uat_evidence import (
	MANUAL_UAT_STATUS_FAIL,
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


def _model_role_parts(scenario):
	model_role_lane = scenario["expected_model_role_lane"]
	lane, _, model_role = model_role_lane.partition(":")
	return model_role_lane, lane or model_role_lane, model_role or model_role_lane


def _raw_trace_for(scenario_id: str, *, omit_trace: bool = False, omit_model_role: bool = False) -> str:
	scenario = _scenario_by_id(scenario_id)
	model_role_lane, lane, model_role = _model_role_parts(scenario)
	policy_boundary = scenario["expected_policy_boundary"]
	preflight_status = "bounded" if policy_boundary != "none" else "passed"
	parts = ["Context Authority Trace", ""]
	if not omit_trace:
		parts.extend(
			[
				"Observed Trace Fields",
				"",
				"| Field | Value |",
				"|---|---|",
				f"| route | {scenario['expected_route']} |",
				f"| artifact_family | {scenario['expected_artifact_family']} |",
				f"| entity_type | {scenario['expected_entity_type']} |",
				f"| row_reference | {scenario['expected_row_reference']} |",
				f"| authority_source | {scenario['expected_authority_source']} |",
				f"| policy_boundary | {scenario['expected_policy_boundary']} |",
				f"| answer_mode | {scenario['expected_answer_mode']} |",
				"",
			]
		)
		parts.extend(
			[
				"Final Answer Authority",
				"",
				"| Field | Value |",
				"|---|---|",
				f"| authority_source | {scenario['expected_authority_source']} |",
				"| evidence_scope | visible_rendered_table |",
				"| selected_artifact_id | visible-assistant-test |",
				f"| selected_report_family | {scenario['expected_artifact_family']} |",
				f"| selected_row_reference | {scenario['expected_row_reference']} |",
				f"| policy_boundary | {policy_boundary} |",
				f"| answer_mode | {scenario['expected_answer_mode']} |",
				"| authority_complete | True |",
				f"| preflight_status | {preflight_status} |",
				"| missing_fields | none |",
				"",
			]
		)
	if not omit_model_role:
		parts.extend(
			[
				"Observed Model Role Fields",
				"",
				"| Field | Value |",
				"|---|---|",
				f"| model_role_lane | {model_role_lane} |",
				f"| lane | {lane} |",
				f"| model_role | {model_role} |",
				f"| expected_model_role | {model_role} |",
				"| role_compliance | compliant |",
				"",
			]
		)
	return "\n".join(parts)


def _capture(scenario_id: str, *, status: str = MANUAL_UAT_STATUS_PASS, failure_reason: str = ""):
	return {
		"scenario_id": scenario_id,
		"raw_answer_text": f"Captured answer for {scenario_id}.",
		"raw_trace_text": _raw_trace_for(scenario_id),
		"uat_status": status,
		"failure_reason": failure_reason,
		"capture_source": "manual_browser_uat",
		"captured_at": "2026-05-13T15:30:00+06:30",
		"reviewer": "uat@example.com",
	}


class ManualUATEvidenceBundleContractTests(unittest.TestCase):
	def test_complete_ar_ap_capture_subset_produces_release_ready_bundle(self):
		scenario_ids = ["visible_ar_after_ap_typed_rank_2", "visible_ap_current_rank_2"]

		bundle = build_manual_uat_evidence_bundle(
			[_capture(scenario_id) for scenario_id in scenario_ids],
			expected_scenario_ids=scenario_ids,
			generated_at="2026-05-13T15:30:00+06:30",
		)

		self.assertEqual(bundle["type"], MANUAL_UAT_BUNDLE_CONTRACT_TYPE)
		self.assertTrue(bundle["roundtrip_complete"])
		self.assertTrue(bundle["release_ready"])
		self.assertEqual(bundle["expected_scenario_count"], 2)
		self.assertEqual(bundle["capture_record_count"], 2)
		self.assertEqual(set(bundle["accepted_scenario_ids"]), set(scenario_ids))
		self.assertEqual(bundle["release_blocking_reasons"], [])
		self.assertEqual(bundle["import_batch_contract"]["release_ready"], True)
		self.assertEqual(bundle["archive_index_contract"]["release_ready"], True)

	def test_product_projection_capture_roundtrips_through_import_and_archive(self):
		scenario_id = "product_projection_qty_preserves_revenue"

		bundle = build_manual_uat_evidence_bundle(
			[_capture(scenario_id)],
			expected_scenario_ids=[scenario_id],
		)

		self.assertTrue(bundle["release_ready"])
		self.assertEqual(bundle["archive_index_contract"]["records"][0]["expected_row_reference"], "all_visible_rows")
		self.assertEqual(bundle["import_batch_contract"]["records"][0]["family"], "product_revenue_ranking")

	def test_pl_cogs_capture_roundtrips_with_rank_2_document(self):
		scenario_id = "pl_cogs_source_document_rank_2"

		bundle = build_manual_uat_evidence_bundle(
			[_capture(scenario_id)],
			expected_scenario_ids=[scenario_id],
		)

		self.assertTrue(bundle["release_ready"])
		self.assertEqual(bundle["archive_index_contract"]["records"][0]["observed_entity_type"], "document")
		self.assertEqual(bundle["archive_index_contract"]["records"][0]["observed_row_reference"], "rank_2")

	def test_prediction_boundary_capture_preserves_boundary_through_bundle(self):
		scenario_id = "ar_rank_2_default_prediction_boundary"

		bundle = build_manual_uat_evidence_bundle(
			[_capture(scenario_id)],
			expected_scenario_ids=[scenario_id],
		)

		self.assertTrue(bundle["release_ready"])
		self.assertEqual(bundle["import_batch_contract"]["records"][0]["observed_trace_fields"]["policy_boundary"], "prediction_boundary")
		self.assertEqual(bundle["archive_index_contract"]["records"][0]["observed_policy_boundary"], "prediction_boundary")

	def test_missing_capture_record_keeps_release_ready_false(self):
		bundle = build_manual_uat_evidence_bundle(
			[_capture("visible_ar_after_ap_typed_rank_2")],
			expected_scenario_ids=["visible_ar_after_ap_typed_rank_2", "visible_ap_current_rank_2"],
		)

		self.assertFalse(bundle["roundtrip_complete"])
		self.assertFalse(bundle["release_ready"])
		self.assertIn("visible_ap_current_rank_2", bundle["missing_evidence_scenario_ids"])
		self.assertIn("missing_archive_evidence", bundle["release_blocking_reasons"])

	def test_blocked_import_keeps_release_ready_false(self):
		capture = _capture("visible_ap_current_rank_2")
		capture["raw_trace_text"] = _raw_trace_for("visible_ap_current_rank_2", omit_trace=True)

		bundle = build_manual_uat_evidence_bundle(
			[capture],
			expected_scenario_ids=["visible_ap_current_rank_2"],
		)

		self.assertFalse(bundle["roundtrip_complete"])
		self.assertFalse(bundle["release_ready"])
		self.assertIn("visible_ap_current_rank_2", bundle["blocked_scenario_ids"])
		self.assertIn("blocked_import_records", bundle["release_blocking_reasons"])

	def test_quarantined_unknown_scenario_keeps_release_ready_false(self):
		capture = _capture("visible_ap_current_rank_2")
		capture["scenario_id"] = "future_tax_scenario"

		bundle = build_manual_uat_evidence_bundle(
			[capture],
			expected_scenario_ids=["visible_ap_current_rank_2"],
		)

		self.assertFalse(bundle["roundtrip_complete"])
		self.assertFalse(bundle["release_ready"])
		self.assertIn("future_tax_scenario", bundle["quarantined_scenario_ids"])
		self.assertIn("quarantined_import_records", bundle["release_blocking_reasons"])

	def test_failed_uat_status_remains_visible_and_blocks_release(self):
		scenario_id = "product_top7_rank_8_out_of_range"

		bundle = build_manual_uat_evidence_bundle(
			[
				_capture(
					scenario_id,
					status=MANUAL_UAT_STATUS_FAIL,
					failure_reason="Assistant invented a rank outside the visible rows.",
				)
			],
			expected_scenario_ids=[scenario_id],
		)

		self.assertFalse(bundle["release_ready"])
		self.assertIn(scenario_id, bundle["accepted_scenario_ids"])
		self.assertIn(scenario_id, bundle["archive_blocking_failure_scenario_ids"])
		self.assertIn("archive_blocking_failures", bundle["release_blocking_reasons"])

	def test_raw_evidence_hashes_are_preserved_in_bundle(self):
		scenario_ids = ["visible_ar_after_ap_typed_rank_2", "visible_ap_current_rank_2"]

		bundle = build_manual_uat_evidence_bundle(
			[_capture(scenario_id) for scenario_id in scenario_ids],
			expected_scenario_ids=scenario_ids,
		)

		import_hashes = [
			record["raw_evidence_hash"]
			for record in bundle["import_batch_contract"]["records"]
		]
		self.assertEqual(bundle["raw_evidence_hashes"], import_hashes)
		self.assertEqual(bundle["raw_evidence_hash_count"], 2)
		self.assertTrue(all(len(value) == 64 for value in bundle["raw_evidence_hashes"]))

	def test_markdown_and_json_bundle_exports_are_deterministic(self):
		scenario_ids = ["visible_ar_after_ap_typed_rank_2", "visible_ap_current_rank_2"]
		captures = [_capture(scenario_id) for scenario_id in scenario_ids]
		with tempfile.TemporaryDirectory() as tmp:
			json_path = Path(tmp) / "bundle.json"
			markdown_path = Path(tmp) / "bundle.md"

			first = write_manual_uat_evidence_bundle_files(
				captures,
				json_path=str(json_path),
				markdown_path=str(markdown_path),
				expected_scenario_ids=scenario_ids,
				generated_at="2026-05-13T15:45:00+06:30",
				reviewer="uat@example.com",
			)
			first_json = json_path.read_text(encoding="utf-8")
			first_markdown = markdown_path.read_text(encoding="utf-8")
			second = write_manual_uat_evidence_bundle_files(
				captures,
				json_path=str(json_path),
				markdown_path=str(markdown_path),
				expected_scenario_ids=scenario_ids,
				generated_at="2026-05-13T15:45:00+06:30",
				reviewer="uat@example.com",
			)

			self.assertTrue(first["json_artifact_written"])
			self.assertTrue(first["markdown_artifact_written"])
			self.assertTrue(second["json_artifact_written"])
			self.assertEqual(first_json, json_path.read_text(encoding="utf-8"))
			self.assertEqual(first_markdown, markdown_path.read_text(encoding="utf-8"))
			loaded = json.loads(first_json)
			self.assertTrue(loaded["release_ready"])
			self.assertIn("# S7 Manual UAT Evidence Bundle", first_markdown)
			self.assertIn("visible_ar_after_ap_typed_rank_2", first_markdown)

	def test_empty_bundle_artifact_is_structurally_visible_but_not_release_ready(self):
		bundle = build_manual_uat_evidence_bundle(
			[],
			expected_scenario_ids=["visible_ar_after_ap_typed_rank_2"],
			generated_at="2026-05-13T16:00:00+06:30",
		)
		markdown = render_manual_uat_evidence_bundle_markdown(bundle)

		self.assertFalse(bundle["roundtrip_complete"])
		self.assertFalse(bundle["release_ready"])
		self.assertEqual(bundle["capture_record_count"], 0)
		self.assertIn("visible_ar_after_ap_typed_rank_2", bundle["missing_evidence_scenario_ids"])
		self.assertIn("missing_archive_evidence", bundle["release_blocking_reasons"])
		self.assertIn("S7 Manual UAT Evidence Bundle", markdown)

	def test_s7_6k_bundle_suite_is_release_blocking_in_regression_boundary(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_BUNDLE_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_BUNDLE_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_BUNDLE_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
