import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_capture_template import build_manual_uat_capture_template
from ai_assistant_ui.qwen_chat.manual_uat_evidence import (
	MANUAL_UAT_STATUS_FAIL,
	MANUAL_UAT_STATUS_PASS,
)
from ai_assistant_ui.qwen_chat.manual_uat_real_evidence_intake import (
	MANUAL_UAT_REAL_EVIDENCE_INTAKE_CONTRACT_TYPE,
	MANUAL_UAT_REAL_EVIDENCE_INTAKE_SUITE_ID,
	build_manual_uat_real_evidence_intake,
	render_manual_uat_real_evidence_intake_markdown,
	write_manual_uat_real_evidence_intake_files,
)
from ai_assistant_ui.qwen_chat.manual_uat_sample_fixture import (
	PRODUCTION_RELEASE_BOUNDARY,
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


def _operator_capture(
	scenario_id: str,
	*,
	status: str = MANUAL_UAT_STATUS_PASS,
	failure_reason: str = "",
	operator_attestation: str = "I confirm this evidence was captured from browser UAT and is ready for promotion review.",
	reviewer: str = "uat@example.com",
	captured_at: str = "2026-05-13T22:45:00+06:30",
	raw_trace_text: str | None = None,
):
	scenario = _scenario_by_id(scenario_id)
	template = build_manual_uat_capture_template(scenario)
	record = dict(template["import_ready_json_skeleton"])
	record["reviewer"] = reviewer
	record["captured_at"] = captured_at
	record["uat_status"] = status
	record["failure_reason"] = failure_reason
	record["raw_answer_text"] = f"Captured answer for {scenario_id}."
	record["raw_trace_text"] = _raw_trace_for(scenario_id) if raw_trace_text is None else raw_trace_text
	record["observed_answer_summary"] = f"Captured answer for {scenario_id}."
	record["operator_attestation"] = operator_attestation
	return record


class ManualUATRealEvidenceIntakeContractTests(unittest.TestCase):
	def test_cross_family_operator_evidence_produces_promotion_ready_intake(self):
		scenario_ids = [
			"visible_ar_after_ap_typed_rank_2",
			"visible_ap_current_rank_2",
			"product_projection_qty_preserves_revenue",
			"pl_cogs_source_document_rank_2",
			"ar_rank_2_default_prediction_boundary",
			"ar_first_customer_cause_boundary",
			"ar_collection_recommendation_boundary",
		]

		intake = build_manual_uat_real_evidence_intake(
			[_operator_capture(scenario_id) for scenario_id in scenario_ids],
			expected_scenario_ids=scenario_ids,
			generated_at="2026-05-13T22:45:00+06:30",
			reviewer="uat@example.com",
		)

		self.assertEqual(intake["type"], MANUAL_UAT_REAL_EVIDENCE_INTAKE_CONTRACT_TYPE)
		self.assertTrue(intake["intake_complete"])
		self.assertTrue(intake["promotion_ready"])
		self.assertTrue(intake["release_ready"])
		self.assertEqual(intake["release_blocking_reasons"], [])
		self.assertEqual(set(intake["operator_record_ids"]), set(scenario_ids))
		self.assertTrue(intake["promotion_ready_bundle_contract"]["release_ready"])
		self.assertTrue(intake["promotion_report_contract"]["release_ready"])

	def test_empty_real_evidence_intake_is_not_release_ready(self):
		intake = build_manual_uat_real_evidence_intake(
			[],
			expected_scenario_ids=["visible_ap_current_rank_2"],
			generated_at="2026-05-13T22:45:00+06:30",
		)

		self.assertFalse(intake["intake_complete"])
		self.assertFalse(intake["release_ready"])
		self.assertIn("source_capture_records_missing", intake["release_blocking_reasons"])
		self.assertIn("bundle_roundtrip_not_complete", intake["release_blocking_reasons"])

	def test_missing_attestation_reviewer_and_timestamp_block_intake(self):
		scenario_id = "visible_ap_current_rank_2"
		capture = _operator_capture(
			scenario_id,
			operator_attestation="",
			reviewer="",
			captured_at="",
		)

		intake = build_manual_uat_real_evidence_intake(
			[capture],
			expected_scenario_ids=[scenario_id],
		)

		self.assertFalse(intake["release_ready"])
		self.assertEqual(intake["blocked_intake_record_count"], 1)
		self.assertIn("operator_attestation_missing", intake["release_blocking_reasons"])
		self.assertIn("reviewer_missing", intake["release_blocking_reasons"])
		self.assertIn("captured_at_missing", intake["release_blocking_reasons"])
		self.assertIn("intake_record_not_accepted", intake["release_blocking_reasons"])

	def test_sample_fixture_capture_records_are_rejected_from_real_intake(self):
		fixture = build_manual_uat_sample_fixture(generated_at="2026-05-13T22:45:00+06:30")

		intake = build_manual_uat_real_evidence_intake(
			fixture["sample_capture_records"],
			expected_scenario_ids=fixture["sample_scenario_ids"],
			generated_at="2026-05-13T22:45:00+06:30",
		)

		self.assertFalse(intake["release_ready"])
		self.assertEqual(intake["operator_record_ids"], [])
		self.assertTrue(intake["sample_record_ids"])
		self.assertIn("sample_evidence_not_allowed", intake["release_blocking_reasons"])
		self.assertIn(PRODUCTION_RELEASE_BOUNDARY, intake["release_blocking_reasons"])

	def test_unknown_scenario_is_quarantined_not_promoted(self):
		capture = _operator_capture("visible_ap_current_rank_2")
		capture["scenario_id"] = "future_tax_scenario"

		intake = build_manual_uat_real_evidence_intake(
			[capture],
			expected_scenario_ids=["future_tax_scenario"],
		)

		self.assertFalse(intake["release_ready"])
		self.assertIn("future_tax_scenario", intake["promotion_ready_bundle_contract"]["quarantined_scenario_ids"])
		self.assertIn("quarantined_import_records", intake["release_blocking_reasons"])
		self.assertIn("promotion_not_release_ready", intake["release_blocking_reasons"])

	def test_blocked_import_does_not_roundtrip_to_promotion(self):
		scenario_id = "visible_ap_current_rank_2"
		capture = _operator_capture(
			scenario_id,
			raw_trace_text=_raw_trace_for(scenario_id, omit_trace=True),
		)

		intake = build_manual_uat_real_evidence_intake(
			[capture],
			expected_scenario_ids=[scenario_id],
		)

		self.assertFalse(intake["release_ready"])
		self.assertIn(scenario_id, intake["promotion_ready_bundle_contract"]["blocked_scenario_ids"])
		self.assertIn("blocked_import_records", intake["release_blocking_reasons"])

	def test_archive_failure_remains_blocking_after_intake(self):
		scenario_id = "product_top7_rank_8_out_of_range"
		capture = _operator_capture(
			scenario_id,
			status=MANUAL_UAT_STATUS_FAIL,
			failure_reason="Assistant invented a rank outside visible rows.",
		)

		intake = build_manual_uat_real_evidence_intake(
			[capture],
			expected_scenario_ids=[scenario_id],
		)

		self.assertFalse(intake["release_ready"])
		self.assertIn(scenario_id, intake["promotion_ready_bundle_contract"]["archive_blocking_failure_scenario_ids"])
		self.assertIn("archive_blocking_failures", intake["release_blocking_reasons"])

	def test_missing_expected_scenario_blocks_promotion_ready_bundle(self):
		intake = build_manual_uat_real_evidence_intake(
			[_operator_capture("visible_ar_after_ap_typed_rank_2")],
			expected_scenario_ids=["visible_ar_after_ap_typed_rank_2", "visible_ap_current_rank_2"],
		)

		self.assertFalse(intake["release_ready"])
		self.assertIn("visible_ap_current_rank_2", intake["promotion_ready_bundle_contract"]["missing_evidence_scenario_ids"])
		self.assertIn("missing_archive_evidence", intake["release_blocking_reasons"])

	def test_dry_run_operator_record_is_not_real_evidence(self):
		scenario_id = "visible_ap_current_rank_2"
		capture = _operator_capture(scenario_id)
		capture["dry_run_only"] = True

		intake = build_manual_uat_real_evidence_intake(
			[capture],
			expected_scenario_ids=[scenario_id],
		)

		self.assertFalse(intake["release_ready"])
		self.assertIn("dry_run_only_not_false", intake["release_blocking_reasons"])
		self.assertIn("sample_evidence_not_allowed", intake["release_blocking_reasons"])

	def test_markdown_renderer_shows_release_boundary_and_composed_status(self):
		scenario_id = "visible_ap_current_rank_2"
		intake = build_manual_uat_real_evidence_intake(
			[_operator_capture(scenario_id)],
			expected_scenario_ids=[scenario_id],
		)

		markdown = render_manual_uat_real_evidence_intake_markdown(intake)

		self.assertIn("# S7 Manual UAT Real Evidence Intake", markdown)
		self.assertIn("Promotion-ready bundle", markdown)
		self.assertIn(scenario_id, markdown)
		self.assertIn("Release Boundary", markdown)

	def test_generated_intake_bundle_and_promotion_artifacts_are_deterministic(self):
		scenario_ids = ["visible_ar_after_ap_typed_rank_2", "visible_ap_current_rank_2"]
		captures = [_operator_capture(scenario_id) for scenario_id in scenario_ids]
		with tempfile.TemporaryDirectory() as tmp:
			intake_json = Path(tmp) / "intake.json"
			bundle_json = Path(tmp) / "bundle.json"
			bundle_markdown = Path(tmp) / "bundle.md"
			promotion_json = Path(tmp) / "promotion.json"
			promotion_markdown = Path(tmp) / "promotion.md"

			first = write_manual_uat_real_evidence_intake_files(
				captures,
				intake_json_path=str(intake_json),
				bundle_json_path=str(bundle_json),
				bundle_markdown_path=str(bundle_markdown),
				promotion_json_path=str(promotion_json),
				promotion_markdown_path=str(promotion_markdown),
				expected_scenario_ids=scenario_ids,
				generated_at="2026-05-13T22:45:00+06:30",
				reviewer="uat@example.com",
			)
			snapshots = {
				"path": intake_json.read_text(encoding="utf-8"),
				"bundle_json": bundle_json.read_text(encoding="utf-8"),
				"bundle_markdown": bundle_markdown.read_text(encoding="utf-8"),
				"promotion_json": promotion_json.read_text(encoding="utf-8"),
				"promotion_markdown": promotion_markdown.read_text(encoding="utf-8"),
			}
			second = write_manual_uat_real_evidence_intake_files(
				captures,
				intake_json_path=str(intake_json),
				bundle_json_path=str(bundle_json),
				bundle_markdown_path=str(bundle_markdown),
				promotion_json_path=str(promotion_json),
				promotion_markdown_path=str(promotion_markdown),
				expected_scenario_ids=scenario_ids,
				generated_at="2026-05-13T22:45:00+06:30",
				reviewer="uat@example.com",
			)

			self.assertTrue(first["intake_json_artifact_written"])
			self.assertTrue(second["promotion_markdown_artifact_written"])
			self.assertEqual(snapshots["path"], intake_json.read_text(encoding="utf-8"))
			self.assertEqual(snapshots["bundle_json"], bundle_json.read_text(encoding="utf-8"))
			self.assertEqual(snapshots["bundle_markdown"], bundle_markdown.read_text(encoding="utf-8"))
			self.assertEqual(snapshots["promotion_json"], promotion_json.read_text(encoding="utf-8"))
			self.assertEqual(snapshots["promotion_markdown"], promotion_markdown.read_text(encoding="utf-8"))
			loaded = json.loads(snapshots["path"])
			self.assertTrue(loaded["release_ready"])

	def test_s7_6o_real_evidence_intake_suite_is_release_blocking(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_REAL_EVIDENCE_INTAKE_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_REAL_EVIDENCE_INTAKE_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_REAL_EVIDENCE_INTAKE_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
