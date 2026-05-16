import unittest

from ai_assistant_ui.qwen_chat.manual_uat_evidence import (
	EXECUTION_DETERMINISTIC_CONTRACT,
	EXECUTION_MANUAL_BROWSER_UAT,
	MANUAL_UAT_CHECKLIST_CONTRACT_TYPE,
	MANUAL_UAT_EVIDENCE_CONTRACT_TYPE,
	MANUAL_UAT_EVIDENCE_SUITE_ID,
	MANUAL_UAT_RELEASE_SUMMARY_CONTRACT_TYPE,
	MANUAL_UAT_STATUS_BLOCKED,
	MANUAL_UAT_STATUS_FAIL,
	MANUAL_UAT_STATUS_NOT_RUN,
	MANUAL_UAT_STATUS_PASS,
	REQUIRED_EVIDENCE_FIELDS,
	build_manual_uat_checklist_contract,
	build_manual_uat_evidence_record,
	build_manual_uat_release_summary,
)
from ai_assistant_ui.qwen_chat.regression_scenario_packs import (
	S7_REGRESSION_SCENARIO_REGISTRY,
	build_regression_scenario_contract,
	manual_uat_regression_scenarios,
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


class ManualUATEvidenceContractTests(unittest.TestCase):
	def test_checklist_export_is_generated_from_scenario_pack_contracts(self):
		checklist = build_manual_uat_checklist_contract()

		self.assertEqual(checklist["type"], MANUAL_UAT_CHECKLIST_CONTRACT_TYPE)
		self.assertTrue(checklist["contract_complete"])
		self.assertEqual(checklist["row_count"], len(S7_REGRESSION_SCENARIO_REGISTRY))
		self.assertGreaterEqual(checklist["deterministic_reference_row_count"], 10)
		self.assertGreaterEqual(checklist["manual_only_row_count"], 1)
		self.assertEqual(checklist["incomplete_rows"], [])
		self.assertEqual(
			set(checklist["manual_only_scenario_ids"]),
			{scenario["scenario_id"] for scenario in manual_uat_regression_scenarios()},
		)
		for row in checklist["rows"]:
			with self.subTest(row=row.get("scenario_id")):
				self.assertTrue(row["row_complete"])
				self.assertTrue(row["manual_uat_prompt"])
				self.assertTrue(row["pass_criteria"])
				self.assertIn(row["execution_mode"], {EXECUTION_DETERMINISTIC_CONTRACT, EXECUTION_MANUAL_BROWSER_UAT})

	def test_evidence_record_requires_trace_model_role_answer_and_review_metadata_for_pass(self):
		scenario = _scenario_by_id("visible_ar_after_ap_typed_rank_2")

		record = build_manual_uat_evidence_record(scenario, uat_status=MANUAL_UAT_STATUS_PASS)

		self.assertEqual(record["type"], MANUAL_UAT_EVIDENCE_CONTRACT_TYPE)
		self.assertFalse(record["evidence_complete"])
		self.assertTrue(record["release_blocking_failure"])
		self.assertIn("observed_answer_summary", record["missing_fields"])
		self.assertIn("reviewed_at", record["missing_fields"])
		self.assertIn("observed_trace_fields", record["missing_fields"])
		self.assertIn("observed_model_role_fields", record["missing_fields"])
		for field in REQUIRED_EVIDENCE_FIELDS:
			self.assertIn(field, record)

	def test_matching_evidence_passes_and_trace_mismatch_blocks_release(self):
		scenario = _scenario_by_id("visible_ap_current_rank_2")

		passing = _passing_evidence(scenario)

		self.assertTrue(passing["evidence_complete"])
		self.assertFalse(passing["release_blocking_failure"])
		self.assertEqual(passing["missing_fields"], [])
		self.assertEqual(passing["field_mismatches"], [])

		mismatched_trace = _matching_trace_fields(scenario)
		mismatched_trace["entity_type"] = "customer"
		mismatched = build_manual_uat_evidence_record(
			scenario,
			observed_answer_summary="Observed answer used a wrong family.",
			observed_trace_fields=mismatched_trace,
			observed_model_role_fields=_matching_model_role_fields(scenario),
			uat_status=MANUAL_UAT_STATUS_PASS,
			reviewed_at="2026-05-13T10:00:00+06:30",
		)

		self.assertFalse(mismatched["evidence_complete"])
		self.assertTrue(mismatched["release_blocking_failure"])
		self.assertEqual(mismatched["field_mismatches"][0]["field"], "expected_entity_type")

	def test_failed_blocked_and_not_run_statuses_are_explicit_release_blockers(self):
		scenario = _scenario_by_id("ar_rank_2_default_prediction_boundary")

		failed = build_manual_uat_evidence_record(
			scenario,
			observed_answer_summary="The assistant predicted default probability.",
			uat_status=MANUAL_UAT_STATUS_FAIL,
			failure_reason="Unsupported prediction escaped policy boundary.",
			reviewed_at="2026-05-13T10:00:00+06:30",
		)
		blocked = build_manual_uat_evidence_record(
			scenario,
			uat_status=MANUAL_UAT_STATUS_BLOCKED,
			failure_reason="Trace could not be inspected in browser.",
			reviewed_at="2026-05-13T10:00:00+06:30",
		)
		not_run = build_manual_uat_evidence_record(scenario, uat_status=MANUAL_UAT_STATUS_NOT_RUN)

		self.assertTrue(failed["release_blocking_failure"])
		self.assertTrue(blocked["release_blocking_failure"])
		self.assertTrue(not_run["release_blocking_failure"])
		self.assertFalse(failed["evidence_complete"])
		self.assertFalse(blocked["evidence_complete"])
		self.assertFalse(not_run["evidence_complete"])

	def test_release_summary_blocks_missing_failed_mismatched_or_duplicate_evidence(self):
		scenario = _scenario_by_id("pl_cogs_source_document_rank_2")
		other = _scenario_by_id("product_top7_rank_8_out_of_range")
		passing = _passing_evidence(scenario)
		failed = build_manual_uat_evidence_record(
			other,
			observed_answer_summary="Out-of-range answer invented rank 8.",
			uat_status=MANUAL_UAT_STATUS_FAIL,
			failure_reason="Unsupported rank hallucination.",
			reviewed_at="2026-05-13T10:00:00+06:30",
		)

		missing_summary = build_manual_uat_release_summary(
			evidence_records=[passing],
			expected_scenario_ids=[scenario["scenario_id"], other["scenario_id"]],
		)
		failed_summary = build_manual_uat_release_summary(
			evidence_records=[passing, failed],
			expected_scenario_ids=[scenario["scenario_id"], other["scenario_id"]],
		)
		duplicate_summary = build_manual_uat_release_summary(
			evidence_records=[passing, passing],
			expected_scenario_ids=[scenario["scenario_id"]],
		)

		self.assertEqual(missing_summary["type"], MANUAL_UAT_RELEASE_SUMMARY_CONTRACT_TYPE)
		self.assertFalse(missing_summary["release_ready"])
		self.assertIn(other["scenario_id"], missing_summary["missing_evidence_scenario_ids"])
		self.assertFalse(failed_summary["release_ready"])
		self.assertIn(other["scenario_id"], failed_summary["blocking_failure_scenario_ids"])
		self.assertFalse(duplicate_summary["release_ready"])
		self.assertIn(scenario["scenario_id"], duplicate_summary["duplicate_evidence_scenario_ids"])

	def test_release_summary_can_pass_for_complete_matching_expected_evidence_set(self):
		scenarios = [
			_scenario_by_id("visible_ar_after_ap_typed_rank_2"),
			_scenario_by_id("ar_collection_recommendation_boundary"),
			_scenario_by_id("trace_inspection_model_role_coverage"),
		]
		records = [_passing_evidence(scenario) for scenario in scenarios]

		summary = build_manual_uat_release_summary(
			evidence_records=records,
			expected_scenario_ids=[scenario["scenario_id"] for scenario in scenarios],
		)

		self.assertTrue(summary["release_ready"])
		self.assertEqual(summary["missing_evidence_scenario_ids"], [])
		self.assertEqual(summary["blocking_failure_scenario_ids"], [])
		self.assertEqual(summary["status_counts"][MANUAL_UAT_STATUS_PASS], 3)

	def test_s7_6c_evidence_suite_is_release_blocking_in_regression_boundary(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_EVIDENCE_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_EVIDENCE_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_EVIDENCE_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
