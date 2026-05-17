import unittest

from ai_assistant_ui.qwen_chat.manual_uat_evidence import (
	MANUAL_UAT_STATUS_BLOCKED,
	MANUAL_UAT_STATUS_PASS,
)
from ai_assistant_ui.qwen_chat.manual_uat_renderer import (
	render_manual_uat_evidence_record_markdown,
	render_manual_uat_release_summary_markdown,
)
from ai_assistant_ui.qwen_chat.manual_uat_workflow import (
	MANUAL_UAT_WORKFLOW_CONTRACT_TYPE,
	MANUAL_UAT_WORKFLOW_SUITE_ID,
	REQUIRED_MODEL_ROLE_CAPTURE_FIELDS,
	REQUIRED_TRACE_CAPTURE_FIELDS,
	STAGE_BLOCK_OR_ACCEPT,
	STAGE_CAPTURE_ANSWER,
	STAGE_CAPTURE_MODEL_ROLE,
	STAGE_CAPTURE_TRACE,
	STAGE_EXECUTE_PROMPT_SEQUENCE,
	STAGE_PREPARE_CHECKLIST,
	STAGE_SUMMARIZE_RELEASE,
	STAGE_VALIDATE_EVIDENCE,
	WORKFLOW_STAGE_SEQUENCE,
	build_manual_uat_evidence_from_workflow,
	build_manual_uat_execution_workflow,
	build_manual_uat_release_summary_from_workflow_evidence,
	build_manual_uat_workflow_pack_contract,
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


def _passing_workflow_evidence(workflow):
	return build_manual_uat_evidence_from_workflow(
		workflow,
		observed_answer_summary="Observed answer matched the workflow contract.",
		observed_trace_fields=_matching_trace_fields(workflow),
		observed_model_role_fields=_matching_model_role_fields(workflow),
		uat_status=MANUAL_UAT_STATUS_PASS,
		reviewer="uat@example.com",
		reviewed_at="2026-05-13T10:00:00+06:30",
	)


class ManualUATWorkflowContractTests(unittest.TestCase):
	def test_workflow_pack_generates_cross_family_execution_workflows(self):
		contract = build_manual_uat_workflow_pack_contract()

		self.assertTrue(contract["contract_complete"])
		self.assertGreaterEqual(contract["workflow_count"], 10)
		self.assertEqual(contract["incomplete_workflows"], [])
		for scenario_id in [
			"visible_ar_after_ap_typed_rank_2",
			"product_projection_qty_preserves_revenue",
			"pl_cogs_source_document_rank_2",
			"ar_rank_2_default_prediction_boundary",
			"ar_first_customer_cause_boundary",
			"ar_collection_recommendation_boundary",
			"trace_inspection_model_role_coverage",
		]:
			self.assertIn(scenario_id, contract["scenario_ids"])

	def test_execution_workflow_declares_all_required_stages_and_capture_fields(self):
		workflow = build_manual_uat_execution_workflow(_scenario_by_id("visible_ar_after_ap_typed_rank_2"))

		self.assertEqual(workflow["type"], MANUAL_UAT_WORKFLOW_CONTRACT_TYPE)
		self.assertTrue(workflow["workflow_complete"])
		self.assertEqual(workflow["stage_sequence"], WORKFLOW_STAGE_SEQUENCE)
		self.assertEqual(
			[stage["stage_id"] for stage in workflow["execution_stages"]],
			[
				STAGE_PREPARE_CHECKLIST,
				STAGE_EXECUTE_PROMPT_SEQUENCE,
				STAGE_CAPTURE_ANSWER,
				STAGE_CAPTURE_TRACE,
				STAGE_CAPTURE_MODEL_ROLE,
				STAGE_VALIDATE_EVIDENCE,
				STAGE_SUMMARIZE_RELEASE,
				STAGE_BLOCK_OR_ACCEPT,
			],
		)
		for trace_field in REQUIRED_TRACE_CAPTURE_FIELDS:
			self.assertIn(f"observed_trace_fields.{trace_field}", workflow["required_capture_fields"])
		for model_field in REQUIRED_MODEL_ROLE_CAPTURE_FIELDS:
			self.assertIn(f"observed_model_role_fields.{model_field}", workflow["required_capture_fields"])
		self.assertIn("observed_answer_summary", workflow["required_capture_fields"])
		self.assertIn("reviewer", workflow["required_capture_fields"])
		self.assertIn("reviewed_at", workflow["required_capture_fields"])

	def test_missing_trace_or_model_role_capture_forces_blocked_evidence_not_pass(self):
		workflow = build_manual_uat_execution_workflow(_scenario_by_id("product_rank_2_after_million_projection"))

		missing_trace = build_manual_uat_evidence_from_workflow(
			workflow,
			observed_answer_summary="Observed rank 2 product response.",
			observed_model_role_fields=_matching_model_role_fields(workflow),
			uat_status=MANUAL_UAT_STATUS_PASS,
			reviewer="uat@example.com",
			reviewed_at="2026-05-13T10:00:00+06:30",
		)
		missing_model_role = build_manual_uat_evidence_from_workflow(
			workflow,
			observed_answer_summary="Observed rank 2 product response.",
			observed_trace_fields=_matching_trace_fields(workflow),
			uat_status=MANUAL_UAT_STATUS_PASS,
			reviewer="uat@example.com",
			reviewed_at="2026-05-13T10:00:00+06:30",
		)

		self.assertEqual(missing_trace["uat_status"], MANUAL_UAT_STATUS_BLOCKED)
		self.assertTrue(missing_trace["workflow_forced_blocked"])
		self.assertTrue(missing_trace["release_blocking_failure"])
		self.assertIn("observed_trace_fields.route", missing_trace["workflow_missing_capture_fields"])
		self.assertEqual(missing_model_role["uat_status"], MANUAL_UAT_STATUS_BLOCKED)
		self.assertTrue(missing_model_role["workflow_forced_blocked"])
		self.assertIn("observed_model_role_fields.model_role_lane", missing_model_role["workflow_missing_capture_fields"])

	def test_matching_workflow_evidence_passes_and_mismatched_observation_blocks_release(self):
		workflow = build_manual_uat_execution_workflow(_scenario_by_id("pl_cogs_source_document_rank_2"))

		passing = _passing_workflow_evidence(workflow)
		mismatched_trace = _matching_trace_fields(workflow)
		mismatched_trace["entity_type"] = "customer"
		mismatched = build_manual_uat_evidence_from_workflow(
			workflow,
			observed_answer_summary="Observed answer used the wrong entity type.",
			observed_trace_fields=mismatched_trace,
			observed_model_role_fields=_matching_model_role_fields(workflow),
			uat_status=MANUAL_UAT_STATUS_PASS,
			reviewer="uat@example.com",
			reviewed_at="2026-05-13T10:00:00+06:30",
		)

		self.assertTrue(passing["evidence_complete"])
		self.assertFalse(passing["release_blocking_failure"])
		self.assertEqual(passing["workflow_final_status"], MANUAL_UAT_STATUS_PASS)
		self.assertFalse(passing["workflow_forced_blocked"])
		self.assertFalse(mismatched["evidence_complete"])
		self.assertTrue(mismatched["release_blocking_failure"])
		self.assertEqual(mismatched["field_mismatches"][0]["field"], "expected_entity_type")

	def test_release_summary_is_generated_from_workflow_evidence_only(self):
		workflows = [
			build_manual_uat_execution_workflow(_scenario_by_id("visible_ar_after_ap_typed_rank_2")),
			build_manual_uat_execution_workflow(_scenario_by_id("ar_collection_recommendation_boundary")),
		]
		records = [_passing_workflow_evidence(workflow) for workflow in workflows]
		summary = build_manual_uat_release_summary_from_workflow_evidence(
			evidence_records=records,
			expected_scenario_ids=[workflow["scenario_id"] for workflow in workflows],
		)
		missing_summary = build_manual_uat_release_summary_from_workflow_evidence(
			evidence_records=records[:1],
			expected_scenario_ids=[workflow["scenario_id"] for workflow in workflows],
		)

		self.assertTrue(summary["release_ready"])
		self.assertEqual(summary["evidence_record_count"], 2)
		self.assertEqual(summary["status_counts"][MANUAL_UAT_STATUS_PASS], 2)
		self.assertFalse(missing_summary["release_ready"])
		self.assertIn(workflows[1]["scenario_id"], missing_summary["missing_evidence_scenario_ids"])

	def test_renderer_can_render_workflow_evidence_without_changing_status(self):
		workflow = build_manual_uat_execution_workflow(_scenario_by_id("ar_rank_2_default_prediction_boundary"))
		evidence = build_manual_uat_evidence_from_workflow(
			workflow,
			observed_answer_summary="Trace could not be inspected.",
			observed_trace_fields={},
			observed_model_role_fields=_matching_model_role_fields(workflow),
			uat_status=MANUAL_UAT_STATUS_PASS,
			reviewer="uat@example.com",
			reviewed_at="2026-05-13T10:00:00+06:30",
		)
		summary = build_manual_uat_release_summary_from_workflow_evidence(
			evidence_records=[evidence],
			expected_scenario_ids=[workflow["scenario_id"]],
		)

		evidence_markdown = render_manual_uat_evidence_record_markdown(evidence)
		summary_markdown = render_manual_uat_release_summary_markdown(summary)

		self.assertEqual(evidence["uat_status"], MANUAL_UAT_STATUS_BLOCKED)
		self.assertIn("| UAT status | blocked |", evidence_markdown)
		self.assertIn("| Release blocking failure | True |", evidence_markdown)
		self.assertIn("Required UAT capture fields are missing", evidence_markdown)
		self.assertIn("| Release ready | False |", summary_markdown)

	def test_workflow_suite_is_release_blocking_in_regression_boundary(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_WORKFLOW_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_WORKFLOW_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_WORKFLOW_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
