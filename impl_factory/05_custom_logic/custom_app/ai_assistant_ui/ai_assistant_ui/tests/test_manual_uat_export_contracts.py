import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_evidence import MANUAL_UAT_STATUS_FAIL, MANUAL_UAT_STATUS_PASS
from ai_assistant_ui.qwen_chat.manual_uat_export import (
	MANUAL_UAT_EXPORT_CONTRACT_TYPE,
	MANUAL_UAT_EXPORT_SUITE_ID,
	build_manual_uat_export_contract,
	render_manual_uat_export_markdown,
	write_manual_uat_export_file,
)
from ai_assistant_ui.qwen_chat.manual_uat_workflow import (
	REQUIRED_MODEL_ROLE_CAPTURE_FIELDS,
	REQUIRED_TRACE_CAPTURE_FIELDS,
	build_manual_uat_evidence_from_workflow,
	build_manual_uat_execution_workflow,
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


def _matching_trace_fields(workflow):
	return {
		"route": workflow["expected_route"],
		"artifact_family": workflow["expected_artifact_family"],
		"entity_type": workflow["expected_entity_type"],
		"row_reference": workflow["expected_row_reference"],
		"authority_source": workflow["expected_authority_source"],
		"policy_boundary": workflow["expected_policy_boundary"],
		"answer_mode": workflow["expected_answer_mode"],
	}


def _matching_model_role_fields(workflow):
	model_role_lane = workflow["expected_model_role_lane"]
	lane, _, model_role = model_role_lane.partition(":")
	return {
		"model_role_lane": model_role_lane,
		"lane": lane or model_role_lane,
		"model_role": model_role or model_role_lane,
		"expected_model_role": model_role or model_role_lane,
		"role_compliance": "compliant",
	}


def _passing_evidence(scenario_id: str):
	workflow = build_manual_uat_execution_workflow(_scenario_by_id(scenario_id))
	return build_manual_uat_evidence_from_workflow(
		workflow,
		observed_answer_summary="Observed answer matched the workflow contract.",
		observed_trace_fields=_matching_trace_fields(workflow),
		observed_model_role_fields=_matching_model_role_fields(workflow),
		uat_status=MANUAL_UAT_STATUS_PASS,
		reviewer="uat@example.com",
		reviewed_at="2026-05-13T10:00:00+06:30",
	)


class ManualUATExportContractTests(unittest.TestCase):
	def test_export_contract_is_generated_from_governed_contracts_with_counts(self):
		contract = build_manual_uat_export_contract(
			artifact_path="tmp/manual_uat.md",
			generated_at="2026-05-13T00:00:00+00:00",
		)

		self.assertEqual(contract["type"], MANUAL_UAT_EXPORT_CONTRACT_TYPE)
		self.assertTrue(contract["artifact_complete"])
		self.assertEqual(contract["scenario_count"], len(S7_REGRESSION_SCENARIO_REGISTRY))
		self.assertGreaterEqual(contract["manual_only_count"], 1)
		self.assertGreaterEqual(contract["deterministic_reference_count"], 10)
		self.assertFalse(contract["release_ready"])
		self.assertEqual(contract["source_checklist_contract"], "qwen_manual_uat_checklist_contract")
		self.assertEqual(contract["source_workflow_pack_contract"], "qwen_manual_uat_execution_workflow_pack_contract")
		self.assertEqual(contract["source_release_summary_contract"], "qwen_manual_uat_release_summary_contract")
		self.assertIn("browser_manual_end_to_end_uat", contract["manual_only_scenario_ids"])
		self.assertIn("visible_ar_after_ap_typed_rank_2", contract["blocking_failure_scenario_ids"])

	def test_export_markdown_contains_cross_family_scenarios_capture_fields_and_release_status(self):
		contract = build_manual_uat_export_contract(
			artifact_path="tmp/manual_uat.md",
			generated_at="2026-05-13T00:00:00+00:00",
		)

		markdown = render_manual_uat_export_markdown(contract)

		self.assertIn("# S7 Manual Browser UAT Pack", markdown)
		self.assertIn("visible_ar_after_ap_typed_rank_2", markdown)
		self.assertIn("product_projection_qty_preserves_revenue", markdown)
		self.assertIn("pl_cogs_source_document_rank_2", markdown)
		self.assertIn("ar_rank_2_default_prediction_boundary", markdown)
		self.assertIn("ar_collection_recommendation_boundary", markdown)
		self.assertIn("ar_first_customer_cause_boundary", markdown)
		self.assertIn("trace_inspection_model_role_coverage", markdown)
		self.assertIn("browser_manual_end_to_end_uat", markdown)
		for field in REQUIRED_TRACE_CAPTURE_FIELDS:
			self.assertIn(f"observed_trace_fields.{field}", markdown)
		for field in REQUIRED_MODEL_ROLE_CAPTURE_FIELDS:
			self.assertIn(f"observed_model_role_fields.{field}", markdown)
		self.assertIn("| Release ready | False |", markdown)
		self.assertIn("Blocking Failures", markdown)
		self.assertIn("Manual-Only Scenarios", markdown)

	def test_export_with_complete_subset_evidence_can_be_release_ready_for_expected_subset(self):
		scenario_ids = ["visible_ar_after_ap_typed_rank_2", "pl_cogs_source_document_rank_2"]
		records = [_passing_evidence(scenario_id) for scenario_id in scenario_ids]

		contract = build_manual_uat_export_contract(
			artifact_path="tmp/manual_uat_subset.md",
			evidence_records=records,
			expected_scenario_ids=scenario_ids,
			generated_at="2026-05-13T00:00:00+00:00",
		)
		markdown = render_manual_uat_export_markdown(contract)

		self.assertTrue(contract["release_ready"])
		self.assertEqual(contract["blocking_failure_scenario_ids"], [])
		self.assertIn("| Release ready | True |", markdown)
		self.assertIn("Observed answer matched the workflow contract.", markdown)

	def test_failed_or_blocked_evidence_remains_visible_and_not_release_ready(self):
		passing = _passing_evidence("visible_ar_after_ap_typed_rank_2")
		failed_workflow = build_manual_uat_execution_workflow(_scenario_by_id("product_top7_rank_8_out_of_range"))
		failed = build_manual_uat_evidence_from_workflow(
			failed_workflow,
			observed_answer_summary="Rank 8 was invented.",
			observed_trace_fields=_matching_trace_fields(failed_workflow),
			observed_model_role_fields=_matching_model_role_fields(failed_workflow),
			uat_status=MANUAL_UAT_STATUS_FAIL,
			failure_reason="Unsupported rank hallucination.",
			reviewer="uat@example.com",
			reviewed_at="2026-05-13T10:00:00+06:30",
		)
		scenario_ids = [passing["scenario_id"], failed["scenario_id"]]

		contract = build_manual_uat_export_contract(
			artifact_path="tmp/manual_uat_failed.md",
			evidence_records=[passing, failed],
			expected_scenario_ids=scenario_ids,
			generated_at="2026-05-13T00:00:00+00:00",
		)
		markdown = render_manual_uat_export_markdown(contract)

		self.assertFalse(contract["release_ready"])
		self.assertIn("product_top7_rank_8_out_of_range", contract["blocking_failure_scenario_ids"])
		self.assertIn("| Release ready | False |", markdown)
		self.assertIn("| UAT status | fail |", markdown)
		self.assertIn("Unsupported rank hallucination.", markdown)

	def test_file_writer_creates_deterministic_artifact_at_expected_path(self):
		scenario_ids = ["visible_ar_after_ap_typed_rank_2"]
		records = [_passing_evidence(scenario_id) for scenario_id in scenario_ids]
		with tempfile.TemporaryDirectory() as tmpdir:
			path = Path(tmpdir) / "uat" / "manual_uat.md"

			first = write_manual_uat_export_file(
				artifact_path=str(path),
				evidence_records=records,
				expected_scenario_ids=scenario_ids,
				generated_at="2026-05-13T00:00:00+00:00",
			)
			first_text = path.read_text(encoding="utf-8")
			second = write_manual_uat_export_file(
				artifact_path=str(path),
				evidence_records=records,
				expected_scenario_ids=scenario_ids,
				generated_at="2026-05-13T00:00:00+00:00",
			)
			second_text = path.read_text(encoding="utf-8")

		self.assertTrue(first["artifact_written"])
		self.assertTrue(first["artifact_complete"])
		self.assertTrue(second["artifact_written"])
		self.assertEqual(first_text, second_text)
		self.assertIn("# S7 Manual Browser UAT Pack", first_text)
		self.assertIn("visible_ar_after_ap_typed_rank_2", first_text)
		self.assertIn("| Release ready | True |", first_text)

	def test_export_suite_is_release_blocking_in_regression_boundary(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_EXPORT_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_EXPORT_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_EXPORT_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
