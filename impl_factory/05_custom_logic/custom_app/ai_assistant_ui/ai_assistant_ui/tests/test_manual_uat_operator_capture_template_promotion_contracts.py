import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_bundle import build_manual_uat_evidence_bundle
from ai_assistant_ui.qwen_chat.manual_uat_capture_template import (
	EVIDENCE_MODE_OPERATOR_CAPTURED,
	MANUAL_UAT_OPERATOR_CAPTURE_PROMOTION_SUITE_ID,
	OPERATOR_CAPTURE_SOURCE,
	OPERATOR_PROMOTION_INTENT,
	OPERATOR_RELEASE_BOUNDARY,
	REQUIRED_PROMOTION_FIELDS,
	build_manual_uat_capture_template,
	build_manual_uat_capture_template_pack,
	render_manual_uat_capture_template_markdown,
	write_manual_uat_capture_template_files,
)
from ai_assistant_ui.qwen_chat.manual_uat_promotion import (
	PRODUCTION_RELEASE_BOUNDARY,
	build_manual_uat_evidence_promotion_report,
)
from ai_assistant_ui.qwen_chat.manual_uat_sample_fixture import build_manual_uat_sample_fixture
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


def _matching_raw_trace(scenario):
	model_role_lane = scenario["expected_model_role_lane"]
	lane, _, model_role = model_role_lane.partition(":")
	policy_boundary = scenario["expected_policy_boundary"]
	preflight_status = "bounded" if policy_boundary != "none" else "passed"
	return "\n".join(
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
			"Observed Model Role Fields",
			"",
			"| Field | Value |",
			"|---|---|",
			f"| model_role_lane | {model_role_lane} |",
			f"| lane | {lane or model_role_lane} |",
			f"| model_role | {model_role or model_role_lane} |",
			f"| expected_model_role | {model_role or model_role_lane} |",
			"| role_compliance | compliant |",
		]
	)


def _promotion_filled_skeleton(scenario_id: str, *, operator_attestation: str = "I confirm this evidence was captured from real browser UAT."):
	scenario = _scenario_by_id(scenario_id)
	template = build_manual_uat_capture_template(scenario)
	skeleton = dict(template["import_ready_json_skeleton"])
	skeleton["reviewer"] = "uat@example.com"
	skeleton["captured_at"] = "2026-05-13T18:00:00+06:30"
	skeleton["uat_status"] = "pass"
	skeleton["raw_answer_text"] = f"Captured answer for {scenario_id}."
	skeleton["raw_trace_text"] = _matching_raw_trace(scenario)
	skeleton["observed_answer_summary"] = f"Captured answer for {scenario_id}."
	skeleton["operator_attestation"] = operator_attestation
	return skeleton


class ManualUATOperatorCaptureTemplatePromotionContractTests(unittest.TestCase):
	def test_every_operator_skeleton_includes_promotion_fields(self):
		pack = build_manual_uat_capture_template_pack(generated_at="2026-05-13T18:00:00+06:30")

		for skeleton in pack["import_ready_json_skeletons"]:
			with self.subTest(scenario=skeleton["scenario_id"]):
				for field in REQUIRED_PROMOTION_FIELDS:
					self.assertIn(field, skeleton)
				self.assertEqual(skeleton["evidence_mode"], EVIDENCE_MODE_OPERATOR_CAPTURED)
				self.assertEqual(skeleton["capture_source"], OPERATOR_CAPTURE_SOURCE)
				self.assertEqual(skeleton["release_boundary"], OPERATOR_RELEASE_BOUNDARY)
				self.assertEqual(skeleton["dry_run_only"], False)
				self.assertEqual(skeleton["promotion_intent"], OPERATOR_PROMOTION_INTENT)
				self.assertEqual(skeleton["operator_attestation"], "")

	def test_template_pack_declares_required_promotion_fields(self):
		pack = build_manual_uat_capture_template_pack(generated_at="2026-05-13T18:00:00+06:30")

		self.assertTrue(pack["template_pack_complete"])
		self.assertEqual(pack["required_promotion_fields"], REQUIRED_PROMOTION_FIELDS)
		for template in pack["templates"]:
			with self.subTest(template=template["scenario_id"]):
				self.assertEqual(template["required_promotion_fields"], REQUIRED_PROMOTION_FIELDS)
				self.assertTrue(template["operator_attestation_required"])
				self.assertTrue(template["promotion_ready_by_default"])
				self.assertEqual(template["promotion_defaults"]["evidence_mode"], EVIDENCE_MODE_OPERATOR_CAPTURED)

	def test_markdown_template_explains_promotion_fields_and_attestation(self):
		pack = build_manual_uat_capture_template_pack(generated_at="2026-05-13T18:00:00+06:30")
		markdown = render_manual_uat_capture_template_markdown(pack)

		self.assertIn("Required Promotion Fields", markdown)
		self.assertIn("Promotion Boundary Fields", markdown)
		self.assertIn("evidence_mode must remain `operator_captured`", markdown)
		self.assertIn("operator_attestation must be filled", markdown)
		self.assertIn("promotion_intent", markdown)

	def test_missing_attestation_blocks_s7_6m_promotion(self):
		scenario_id = "visible_ap_current_rank_2"
		bundle = build_manual_uat_evidence_bundle(
			[_promotion_filled_skeleton(scenario_id, operator_attestation="")],
			expected_scenario_ids=[scenario_id],
			generated_at="2026-05-13T18:00:00+06:30",
			reviewer="uat@example.com",
		)

		report = build_manual_uat_evidence_promotion_report(bundle)

		self.assertFalse(report["promotion_eligible"])
		self.assertIn("operator_attestation_missing", report["promotion_blocking_reasons"])

	def test_filled_attestation_plus_valid_skeleton_passes_s7_6m_promotion(self):
		scenario_id = "visible_ap_current_rank_2"
		bundle = build_manual_uat_evidence_bundle(
			[_promotion_filled_skeleton(scenario_id)],
			expected_scenario_ids=[scenario_id],
			generated_at="2026-05-13T18:00:00+06:30",
			reviewer="uat@example.com",
		)

		report = build_manual_uat_evidence_promotion_report(bundle)

		self.assertTrue(report["promotion_eligible"])
		self.assertTrue(report["release_ready"])
		self.assertEqual(report["promotion_blocking_reasons"], [])
		self.assertEqual(report["operator_record_ids"], [scenario_id])

	def test_cross_family_filled_skeletons_can_pass_promotion(self):
		scenario_ids = [
			"visible_ar_after_ap_typed_rank_2",
			"visible_ap_current_rank_2",
			"product_projection_qty_preserves_revenue",
			"pl_cogs_source_document_rank_2",
			"ar_rank_2_default_prediction_boundary",
			"ar_first_customer_cause_boundary",
			"ar_collection_recommendation_boundary",
		]
		bundle = build_manual_uat_evidence_bundle(
			[_promotion_filled_skeleton(scenario_id) for scenario_id in scenario_ids],
			expected_scenario_ids=scenario_ids,
			generated_at="2026-05-13T18:00:00+06:30",
			reviewer="uat@example.com",
		)

		report = build_manual_uat_evidence_promotion_report(bundle)

		self.assertTrue(report["promotion_eligible"])
		self.assertEqual(set(report["operator_record_ids"]), set(scenario_ids))

	def test_sample_fixture_remains_sample_only_and_blocked(self):
		fixture = build_manual_uat_sample_fixture(generated_at="2026-05-13T18:00:00+06:30")

		report = build_manual_uat_evidence_promotion_report(fixture)

		self.assertFalse(report["promotion_eligible"])
		self.assertIn(PRODUCTION_RELEASE_BOUNDARY, report["promotion_blocking_reasons"])
		self.assertEqual(report["operator_record_ids"], [])

	def test_generated_operator_capture_json_is_deterministic_with_promotion_fields(self):
		with tempfile.TemporaryDirectory() as tmp:
			markdown_path = Path(tmp) / "operator_template.md"
			json_path = Path(tmp) / "operator_template.json"

			first = write_manual_uat_capture_template_files(
				markdown_path=str(markdown_path),
				json_path=str(json_path),
				generated_at="2026-05-13T18:00:00+06:30",
			)
			first_json = json_path.read_text(encoding="utf-8")
			first_markdown = markdown_path.read_text(encoding="utf-8")
			second = write_manual_uat_capture_template_files(
				markdown_path=str(markdown_path),
				json_path=str(json_path),
				generated_at="2026-05-13T18:00:00+06:30",
			)

			self.assertTrue(first["json_artifact_written"])
			self.assertTrue(first["markdown_artifact_written"])
			self.assertTrue(second["json_artifact_written"])
			self.assertEqual(first_json, json_path.read_text(encoding="utf-8"))
			self.assertEqual(first_markdown, markdown_path.read_text(encoding="utf-8"))
			loaded = json.loads(first_json)
			self.assertEqual(loaded[0]["evidence_mode"], EVIDENCE_MODE_OPERATOR_CAPTURED)
			self.assertIn('"operator_attestation": ""', first_json)
			self.assertIn("Required Promotion Fields", first_markdown)

	def test_s7_6n_operator_capture_template_suite_is_release_blocking(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_OPERATOR_CAPTURE_PROMOTION_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_OPERATOR_CAPTURE_PROMOTION_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_OPERATOR_CAPTURE_PROMOTION_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
