import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_bundle import build_manual_uat_evidence_bundle
from ai_assistant_ui.qwen_chat.manual_uat_evidence import MANUAL_UAT_STATUS_FAIL, MANUAL_UAT_STATUS_PASS
from ai_assistant_ui.qwen_chat.manual_uat_promotion import (
	EVIDENCE_CLASS_OPERATOR_CAPTURED,
	EVIDENCE_CLASS_SAMPLE_FIXTURE,
	EVIDENCE_CLASS_UNKNOWN_OR_UNSAFE,
	EVIDENCE_MODE_OPERATOR_CAPTURED,
	MANUAL_BROWSER_CAPTURE_SOURCE,
	MANUAL_UAT_PROMOTION_CONTRACT_TYPE,
	MANUAL_UAT_PROMOTION_SUITE_ID,
	PRODUCTION_RELEASE_BOUNDARY,
	build_manual_uat_evidence_promotion_report,
	classify_manual_uat_evidence_record,
	render_manual_uat_evidence_promotion_markdown,
	write_manual_uat_evidence_promotion_files,
)
from ai_assistant_ui.qwen_chat.manual_uat_sample_fixture import (
	EVIDENCE_MODE_SAMPLE_FIXTURE,
	SAMPLE_CAPTURE_SOURCE,
	build_manual_uat_sample_fixture,
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


def _raw_trace_for(scenario_id: str, *, omit_final_answer_authority: bool = False) -> str:
	scenario = _scenario_by_id(scenario_id)
	model_role_lane, lane, model_role = _model_role_parts(scenario)
	policy_boundary = scenario["expected_policy_boundary"]
	preflight_status = "bounded" if policy_boundary != "none" else "passed"
	parts = [
		"Context Authority Trace",
		"",
		"Observed Trace Fields",
		"",
		"| Field | Value |",
		"|---|---|",
		f"| route | {scenario['expected_route']} |",
		f"| artifact_family | {scenario['expected_artifact_family']} |",
		f"| entity_type | {scenario['expected_entity_type']} |",
		f"| row_reference | {scenario['expected_row_reference']} |",
		f"| authority_source | {scenario['expected_authority_source']} |",
		f"| policy_boundary | {policy_boundary} |",
		f"| answer_mode | {scenario['expected_answer_mode']} |",
		"",
	]
	if not omit_final_answer_authority:
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
		]
	)
	return "\n".join(parts)


def _operator_capture(
	scenario_id: str,
	*,
	status: str = MANUAL_UAT_STATUS_PASS,
	failure_reason: str = "",
	reviewer: str = "uat@example.com",
	captured_at: str = "2026-05-13T17:15:00+06:30",
	raw_trace_text: str | None = None,
	evidence_mode: str = EVIDENCE_MODE_OPERATOR_CAPTURED,
	capture_source: str = MANUAL_BROWSER_CAPTURE_SOURCE,
	operator_attestation: str = "I confirm this evidence was captured from real browser UAT.",
):
	return {
		"scenario_id": scenario_id,
		"reviewer": reviewer,
		"captured_at": captured_at,
		"capture_source": capture_source,
		"evidence_mode": evidence_mode,
		"release_boundary": "none",
		"dry_run_only": False,
		"promotion_intent": "production_manual_uat",
		"operator_attestation": operator_attestation,
		"uat_status": status,
		"failure_reason": failure_reason,
		"raw_answer_text": f"Operator captured answer for {scenario_id}.",
		"raw_trace_text": _raw_trace_for(scenario_id) if raw_trace_text is None else raw_trace_text,
		"observed_answer_summary": f"Operator captured answer for {scenario_id}.",
	}


def _operator_bundle(scenario_ids, captures=None):
	records = captures if captures is not None else [_operator_capture(scenario_id) for scenario_id in scenario_ids]
	return build_manual_uat_evidence_bundle(
		records,
		expected_scenario_ids=scenario_ids,
		bundle_id="operator_uat_bundle",
		generated_at="2026-05-13T17:15:00+06:30",
		reviewer="uat@example.com",
	)


class ManualUATEvidencePromotionContractTests(unittest.TestCase):
	def test_sample_fixture_bundle_is_blocked_from_promotion(self):
		fixture = build_manual_uat_sample_fixture(generated_at="2026-05-13T17:15:00+06:30")

		report = build_manual_uat_evidence_promotion_report(fixture, generated_at="2026-05-13T17:15:00+06:30")

		self.assertEqual(report["type"], MANUAL_UAT_PROMOTION_CONTRACT_TYPE)
		self.assertFalse(report["promotion_eligible"])
		self.assertFalse(report["release_ready"])
		self.assertIn(PRODUCTION_RELEASE_BOUNDARY, report["promotion_blocking_reasons"])
		self.assertEqual(report["evidence_class_counts"][EVIDENCE_CLASS_SAMPLE_FIXTURE], fixture["capture_record_count"])
		self.assertEqual(report["source_contract_type"], "qwen_manual_uat_sample_fixture_contract")

	def test_operator_ar_ap_evidence_can_be_promotion_eligible_when_complete(self):
		scenario_ids = ["visible_ar_after_ap_typed_rank_2", "visible_ap_current_rank_2"]

		report = build_manual_uat_evidence_promotion_report(_operator_bundle(scenario_ids))

		self.assertTrue(report["promotion_eligible"])
		self.assertTrue(report["release_ready"])
		self.assertEqual(report["release_boundary"], "none")
		self.assertEqual(set(report["operator_record_ids"]), set(scenario_ids))
		self.assertEqual(report["promotion_blocking_reasons"], [])

	def test_operator_product_projection_evidence_can_be_promotion_eligible(self):
		scenario_ids = ["product_projection_qty_preserves_revenue"]

		report = build_manual_uat_evidence_promotion_report(_operator_bundle(scenario_ids))

		self.assertTrue(report["promotion_eligible"])
		self.assertEqual(report["record_evaluations"][0]["evidence_class"], EVIDENCE_CLASS_OPERATOR_CAPTURED)
		self.assertEqual(report["record_evaluations"][0]["scenario_id"], "product_projection_qty_preserves_revenue")

	def test_operator_pl_cogs_evidence_can_be_promotion_eligible(self):
		scenario_ids = ["pl_cogs_source_document_rank_2"]

		report = build_manual_uat_evidence_promotion_report(_operator_bundle(scenario_ids))

		self.assertTrue(report["promotion_eligible"])
		self.assertEqual(report["record_evaluations"][0]["scenario_id"], "pl_cogs_source_document_rank_2")

	def test_operator_policy_boundary_evidence_can_be_promotion_eligible_when_bounded_correctly(self):
		scenario_ids = [
			"ar_rank_2_default_prediction_boundary",
			"ar_first_customer_cause_boundary",
			"ar_collection_recommendation_boundary",
		]

		report = build_manual_uat_evidence_promotion_report(_operator_bundle(scenario_ids))

		self.assertTrue(report["promotion_eligible"])
		self.assertEqual(set(report["operator_record_ids"]), set(scenario_ids))

	def test_missing_reviewer_blocks_promotion(self):
		scenario_id = "visible_ap_current_rank_2"
		bundle = _operator_bundle([scenario_id], captures=[_operator_capture(scenario_id, reviewer="")])

		report = build_manual_uat_evidence_promotion_report(bundle)

		self.assertFalse(report["promotion_eligible"])
		self.assertIn("reviewer_missing", report["promotion_blocking_reasons"])
		self.assertIn("reviewer_missing", report["record_evaluations"][0]["blocking_reasons"])

	def test_missing_timestamp_blocks_promotion(self):
		scenario_id = "visible_ap_current_rank_2"
		bundle = _operator_bundle([scenario_id], captures=[_operator_capture(scenario_id, captured_at="")])

		report = build_manual_uat_evidence_promotion_report(bundle)

		self.assertFalse(report["promotion_eligible"])
		self.assertIn("captured_at_missing", report["promotion_blocking_reasons"])

	def test_missing_operator_attestation_blocks_promotion(self):
		scenario_id = "visible_ap_current_rank_2"
		bundle = _operator_bundle([scenario_id], captures=[_operator_capture(scenario_id, operator_attestation="")])

		report = build_manual_uat_evidence_promotion_report(bundle)

		self.assertFalse(report["promotion_eligible"])
		self.assertIn("operator_attestation_missing", report["promotion_blocking_reasons"])
		self.assertFalse(report["record_evaluations"][0]["operator_attestation_present"])

	def test_unknown_evidence_mode_blocks_promotion_even_when_bundle_is_clean(self):
		scenario_id = "visible_ap_current_rank_2"
		bundle = _operator_bundle([scenario_id], captures=[_operator_capture(scenario_id, evidence_mode="")])

		report = build_manual_uat_evidence_promotion_report(bundle)

		self.assertFalse(report["promotion_eligible"])
		self.assertIn("unknown_or_unsafe_evidence_mode", report["promotion_blocking_reasons"])
		self.assertEqual(report["unsafe_record_ids"], [scenario_id])

	def test_sample_marker_inside_otherwise_valid_bundle_blocks_promotion(self):
		scenario_id = "visible_ap_current_rank_2"
		capture = _operator_capture(scenario_id)
		capture["release_boundary"] = PRODUCTION_RELEASE_BOUNDARY
		bundle = _operator_bundle([scenario_id], captures=[capture])

		report = build_manual_uat_evidence_promotion_report(bundle)

		self.assertFalse(report["promotion_eligible"])
		self.assertIn("sample_marker_present", report["promotion_blocking_reasons"])
		self.assertIn(PRODUCTION_RELEASE_BOUNDARY, report["promotion_blocking_reasons"])
		self.assertEqual(report["sample_record_ids"], [scenario_id])

	def test_blocked_import_blocks_promotion(self):
		scenario_id = "visible_ap_current_rank_2"
		capture = _operator_capture(scenario_id, raw_trace_text="")
		bundle = _operator_bundle([scenario_id], captures=[capture])

		report = build_manual_uat_evidence_promotion_report(bundle)

		self.assertFalse(report["promotion_eligible"])
		self.assertIn("blocked_import_records", report["promotion_blocking_reasons"])
		self.assertIn("import_not_accepted", report["record_evaluations"][0]["blocking_reasons"])

	def test_missing_final_answer_authority_blocks_promotion(self):
		scenario_id = "visible_ap_current_rank_2"
		capture = _operator_capture(
			scenario_id,
			raw_trace_text=_raw_trace_for(scenario_id, omit_final_answer_authority=True),
		)
		bundle = _operator_bundle([scenario_id], captures=[capture])

		report = build_manual_uat_evidence_promotion_report(bundle)

		self.assertFalse(report["promotion_eligible"])
		self.assertFalse(report["release_ready"])
		self.assertIn("blocked_import_records", report["promotion_blocking_reasons"])
		self.assertIn("import_not_accepted", report["record_evaluations"][0]["blocking_reasons"])

	def test_quarantined_import_blocks_promotion(self):
		capture = _operator_capture("visible_ap_current_rank_2")
		capture["scenario_id"] = "future_tax_scenario"
		bundle = build_manual_uat_evidence_bundle(
			[capture],
			expected_scenario_ids=["visible_ap_current_rank_2"],
			generated_at="2026-05-13T17:15:00+06:30",
			reviewer="uat@example.com",
		)

		report = build_manual_uat_evidence_promotion_report(bundle)

		self.assertFalse(report["promotion_eligible"])
		self.assertIn("quarantined_import_records", report["promotion_blocking_reasons"])
		self.assertIn("import_not_accepted", report["record_evaluations"][0]["blocking_reasons"])

	def test_archive_blocking_failure_blocks_promotion(self):
		scenario_id = "product_top7_rank_8_out_of_range"
		bundle = _operator_bundle(
			[scenario_id],
			captures=[
				_operator_capture(
					scenario_id,
					status=MANUAL_UAT_STATUS_FAIL,
					failure_reason="Assistant invented an out-of-range row.",
				)
			],
		)

		report = build_manual_uat_evidence_promotion_report(bundle)

		self.assertFalse(report["promotion_eligible"])
		self.assertIn("archive_blocking_failures", report["promotion_blocking_reasons"])
		self.assertIn("archive_release_blocking", report["record_evaluations"][0]["blocking_reasons"])

	def test_classification_is_structural_not_filename_or_markdown_based(self):
		self.assertEqual(
			classify_manual_uat_evidence_record(
				{
					"evidence_mode": EVIDENCE_MODE_OPERATOR_CAPTURED,
					"capture_source": MANUAL_BROWSER_CAPTURE_SOURCE,
				}
			),
			EVIDENCE_CLASS_OPERATOR_CAPTURED,
		)
		self.assertEqual(
			classify_manual_uat_evidence_record(
				{
					"evidence_mode": EVIDENCE_MODE_SAMPLE_FIXTURE,
					"capture_source": SAMPLE_CAPTURE_SOURCE,
				}
			),
			EVIDENCE_CLASS_SAMPLE_FIXTURE,
		)
		self.assertEqual(classify_manual_uat_evidence_record({"capture_source": MANUAL_BROWSER_CAPTURE_SOURCE}), EVIDENCE_CLASS_UNKNOWN_OR_UNSAFE)

	def test_promotion_report_markdown_lists_blocking_reasons_structurally(self):
		fixture = build_manual_uat_sample_fixture(generated_at="2026-05-13T17:15:00+06:30")
		report = build_manual_uat_evidence_promotion_report(fixture, generated_at="2026-05-13T17:15:00+06:30")

		markdown = render_manual_uat_evidence_promotion_markdown(report)

		self.assertIn("# S7 Manual UAT Evidence Promotion Report", markdown)
		self.assertIn("Promotion Boundary", markdown)
		self.assertIn(PRODUCTION_RELEASE_BOUNDARY, markdown)
		self.assertIn("sample_fixture", markdown)
		self.assertIn("Record Evaluation", markdown)

	def test_writer_generates_deterministic_json_and_markdown(self):
		scenario_ids = ["visible_ar_after_ap_typed_rank_2", "visible_ap_current_rank_2"]
		bundle = _operator_bundle(scenario_ids)
		with tempfile.TemporaryDirectory() as tmp:
			json_path = Path(tmp) / "promotion.json"
			markdown_path = Path(tmp) / "promotion.md"

			first = write_manual_uat_evidence_promotion_files(
				bundle,
				json_path=str(json_path),
				markdown_path=str(markdown_path),
				generated_at="2026-05-13T17:15:00+06:30",
				reviewer="uat@example.com",
			)
			first_json = json_path.read_text(encoding="utf-8")
			first_markdown = markdown_path.read_text(encoding="utf-8")
			second = write_manual_uat_evidence_promotion_files(
				bundle,
				json_path=str(json_path),
				markdown_path=str(markdown_path),
				generated_at="2026-05-13T17:15:00+06:30",
				reviewer="uat@example.com",
			)

			self.assertTrue(first["json_artifact_written"])
			self.assertTrue(first["markdown_artifact_written"])
			self.assertTrue(second["json_artifact_written"])
			self.assertEqual(first_json, json_path.read_text(encoding="utf-8"))
			self.assertEqual(first_markdown, markdown_path.read_text(encoding="utf-8"))
			loaded = json.loads(first_json)
			self.assertEqual(loaded["type"], MANUAL_UAT_PROMOTION_CONTRACT_TYPE)
			self.assertTrue(loaded["promotion_eligible"])
			self.assertIn("# S7 Manual UAT Evidence Promotion Report", first_markdown)

	def test_s7_6m_promotion_suite_is_release_blocking_in_regression_boundary(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_PROMOTION_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_PROMOTION_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_PROMOTION_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
