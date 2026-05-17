import copy
import unittest

from ai_assistant_ui.qwen_chat.manual_uat_evidence import (
	MANUAL_UAT_STATUS_BLOCKED,
	MANUAL_UAT_STATUS_FAIL,
	MANUAL_UAT_STATUS_PASS,
	build_manual_uat_checklist_contract,
	build_manual_uat_evidence_record,
	build_manual_uat_release_summary,
)
from ai_assistant_ui.qwen_chat.manual_uat_renderer import (
	MANUAL_UAT_RENDERER_SUITE_ID,
	render_manual_uat_checklist_markdown,
	render_manual_uat_evidence_record_markdown,
	render_manual_uat_pack_markdown,
	render_manual_uat_release_summary_markdown,
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


def _passing_evidence(scenario):
	return build_manual_uat_evidence_record(
		scenario,
		observed_answer_summary="Observed answer matched the scenario contract.",
		observed_trace_fields=_matching_trace_fields(scenario),
		observed_model_role_fields=_matching_model_role_fields(scenario),
		uat_status=MANUAL_UAT_STATUS_PASS,
		reviewed_at="2026-05-13T10:00:00+06:30",
		reviewer="uat@example.com",
	)


class ManualUATRendererContractTests(unittest.TestCase):
	def test_checklist_renderer_exports_cross_family_prompts_expected_fields_and_capture_template(self):
		checklist = build_manual_uat_checklist_contract()

		rendered = render_manual_uat_checklist_markdown(checklist)

		self.assertIn("**Manual UAT Checklist**", rendered)
		self.assertIn("visible_ar_after_ap_typed_rank_2", rendered)
		self.assertIn("product_projection_qty_preserves_revenue", rendered)
		self.assertIn("pl_cogs_source_document_rank_2", rendered)
		self.assertIn("ar_rank_2_default_prediction_boundary", rendered)
		self.assertIn("ar_collection_recommendation_boundary", rendered)
		self.assertIn("ar_first_customer_cause_boundary", rendered)
		self.assertIn("trace_inspection_model_role_coverage", rendered)
		self.assertIn("Expected policy boundary", rendered)
		self.assertIn("Expected model-role lane", rendered)
		self.assertIn("Observed trace fields", rendered)
		self.assertIn("Observed model-role fields", rendered)
		self.assertIn("Manual-only", rendered)

	def test_evidence_renderer_shows_passing_evidence_without_mutating_record(self):
		scenario = _scenario_by_id("visible_ap_current_rank_2")
		record = _passing_evidence(scenario)
		before = copy.deepcopy(record)

		rendered = render_manual_uat_evidence_record_markdown(record)

		self.assertEqual(record, before)
		self.assertIn("**Manual UAT Evidence Record**", rendered)
		self.assertIn("visible_ap_current_rank_2", rendered)
		self.assertIn("| UAT status | pass |", rendered)
		self.assertIn("| Evidence complete | True |", rendered)
		self.assertIn("| Release blocking failure | False |", rendered)
		self.assertIn("accounts_payable_aging", rendered)
		self.assertIn("visible_context_followup:deterministic", rendered)
		self.assertIn("Observed Trace Fields", rendered)
		self.assertIn("Observed Model-Role Fields", rendered)

	def test_evidence_renderer_keeps_failed_blocked_and_missing_evidence_visible(self):
		prediction = _scenario_by_id("ar_rank_2_default_prediction_boundary")
		failed = build_manual_uat_evidence_record(
			prediction,
			observed_answer_summary="The assistant predicted a default probability.",
			uat_status=MANUAL_UAT_STATUS_FAIL,
			failure_reason="Unsupported prediction escaped policy boundary.",
			reviewed_at="2026-05-13T10:00:00+06:30",
		)
		blocked = build_manual_uat_evidence_record(
			prediction,
			uat_status=MANUAL_UAT_STATUS_BLOCKED,
			failure_reason="Trace was not available in the browser.",
			reviewed_at="2026-05-13T10:00:00+06:30",
		)

		failed_rendered = render_manual_uat_evidence_record_markdown(failed)
		blocked_rendered = render_manual_uat_evidence_record_markdown(blocked)

		self.assertIn("| UAT status | fail |", failed_rendered)
		self.assertIn("| Release blocking failure | True |", failed_rendered)
		self.assertIn("Unsupported prediction escaped policy boundary.", failed_rendered)
		self.assertIn("prediction_boundary", failed_rendered)
		self.assertIn("| UAT status | blocked |", blocked_rendered)
		self.assertIn("Trace was not available in the browser.", blocked_rendered)
		self.assertIn("Release blocking failure", blocked_rendered)

	def test_release_summary_renderer_shows_counts_missing_evidence_and_blocking_failures(self):
		passing_scenario = _scenario_by_id("pl_cogs_source_document_rank_2")
		missing_scenario = _scenario_by_id("product_top7_rank_8_out_of_range")
		passing = _passing_evidence(passing_scenario)
		summary = build_manual_uat_release_summary(
			evidence_records=[passing],
			expected_scenario_ids=[passing_scenario["scenario_id"], missing_scenario["scenario_id"]],
		)

		rendered = render_manual_uat_release_summary_markdown(summary)

		self.assertIn("**Manual UAT Release Summary**", rendered)
		self.assertIn("| Release ready | False |", rendered)
		self.assertIn("Status Counts", rendered)
		self.assertIn("Blocking Failures", rendered)
		self.assertIn("Missing Evidence", rendered)
		self.assertIn("product_top7_rank_8_out_of_range", rendered)
		self.assertIn("pass", rendered)

	def test_combined_pack_renderer_is_read_only_and_includes_all_sections(self):
		checklist = build_manual_uat_checklist_contract()
		scenarios = [
			_scenario_by_id("visible_ar_after_ap_typed_rank_2"),
			_scenario_by_id("ar_collection_recommendation_boundary"),
		]
		records = [_passing_evidence(scenario) for scenario in scenarios]
		summary = build_manual_uat_release_summary(
			evidence_records=records,
			expected_scenario_ids=[scenario["scenario_id"] for scenario in scenarios],
		)
		before_checklist = copy.deepcopy(checklist)
		before_records = copy.deepcopy(records)
		before_summary = copy.deepcopy(summary)

		rendered = render_manual_uat_pack_markdown(checklist, evidence_records=records, summary_contract=summary)

		self.assertEqual(checklist, before_checklist)
		self.assertEqual(records, before_records)
		self.assertEqual(summary, before_summary)
		self.assertIn("**Manual UAT Checklist**", rendered)
		self.assertIn("**Manual UAT Evidence Record**", rendered)
		self.assertIn("**Manual UAT Release Summary**", rendered)
		self.assertIn("---", rendered)
		self.assertIn("| Release ready | True |", rendered)

	def test_renderer_suite_is_release_blocking_in_regression_boundary(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_RENDERER_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_RENDERER_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_RENDERER_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
