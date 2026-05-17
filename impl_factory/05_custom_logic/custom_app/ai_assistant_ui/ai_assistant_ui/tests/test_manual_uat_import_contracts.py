import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_evidence import (
	MANUAL_UAT_STATUS_BLOCKED,
	MANUAL_UAT_STATUS_FAIL,
	MANUAL_UAT_STATUS_PASS,
)
from ai_assistant_ui.qwen_chat.manual_uat_import import (
	IMPORT_PARSE_ACCEPTED,
	IMPORT_PARSE_BLOCKED,
	IMPORT_PARSE_QUARANTINED,
	MANUAL_UAT_IMPORT_BATCH_CONTRACT_TYPE,
	MANUAL_UAT_IMPORT_RECORD_CONTRACT_TYPE,
	MANUAL_UAT_IMPORT_SUITE_ID,
	build_manual_uat_import_batch,
	build_manual_uat_import_record,
	extract_final_answer_authority_fields,
	extract_observed_model_role_fields,
	extract_observed_trace_fields,
	parse_capture_tables,
	render_manual_uat_import_markdown,
	write_manual_uat_import_files,
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


def _raw_trace_for(
	scenario_id: str,
	*,
	omit_trace: bool = False,
	omit_model_role: bool = False,
	omit_final_answer_authority: bool = False,
	final_authority_complete: str = "True",
	final_preflight_status: str | None = None,
	final_missing_fields: str = "none",
) -> str:
	scenario = _scenario_by_id(scenario_id)
	model_role_lane, lane, model_role = _model_role_parts(scenario)
	policy_boundary = scenario["expected_policy_boundary"]
	preflight_status = final_preflight_status or ("bounded" if policy_boundary != "none" else "passed")
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
				f"| authority_complete | {final_authority_complete} |",
				f"| preflight_status | {preflight_status} |",
				f"| missing_fields | {final_missing_fields} |",
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
		"capture_source": "browser_chat",
		"captured_at": "2026-05-13T13:00:00+06:30",
		"reviewer": "uat@example.com",
	}


class ManualUATImportContractTests(unittest.TestCase):
	def test_contract_tables_parse_trace_and_model_role_fields_deterministically(self):
		raw_trace = _raw_trace_for("visible_ar_after_ap_typed_rank_2")

		sections = parse_capture_tables(raw_trace)
		trace_fields = extract_observed_trace_fields(raw_trace)
		model_role_fields = extract_observed_model_role_fields(raw_trace)
		final_authority_fields = extract_final_answer_authority_fields(raw_trace)

		self.assertEqual(sections["observed_trace_fields"]["row_reference"], "rank_2")
		self.assertEqual(sections["final_answer_authority"]["authority_source"], "visible_rendered_table")
		self.assertEqual(trace_fields["route"], "visible_context_followup")
		self.assertEqual(trace_fields["entity_type"], "customer")
		self.assertEqual(model_role_fields["model_role_lane"], "visible_context_followup:deterministic")
		self.assertEqual(model_role_fields["role_compliance"], "compliant")
		self.assertEqual(final_authority_fields["authority_complete"], "True")
		self.assertEqual(final_authority_fields["preflight_status"], "passed")

	def test_ar_ap_visible_context_capture_imports_to_archive_ready_record(self):
		record = build_manual_uat_import_record(_capture("visible_ar_after_ap_typed_rank_2"))

		self.assertEqual(record["type"], MANUAL_UAT_IMPORT_RECORD_CONTRACT_TYPE)
		self.assertEqual(record["parse_status"], IMPORT_PARSE_ACCEPTED)
		self.assertTrue(record["scenario_registered"])
		self.assertFalse(record["release_blocking"])
		self.assertEqual(record["archive_import_record"]["observed_trace_fields"]["row_reference"], "rank_2")
		self.assertEqual(record["archive_record_contract"]["archive_complete"], True)
		self.assertEqual(record["missing_capture_sections"], [])
		self.assertEqual(record["field_mismatches"], [])

	def test_product_projection_capture_preserves_projection_family_fields(self):
		record = build_manual_uat_import_record(_capture("product_projection_qty_preserves_revenue"))

		self.assertEqual(record["parse_status"], IMPORT_PARSE_ACCEPTED)
		self.assertEqual(record["family"], "product_revenue_ranking")
		self.assertEqual(record["archive_import_record"]["observed_trace_fields"]["row_reference"], "all_visible_rows")
		self.assertEqual(record["archive_import_record"]["observed_trace_fields"]["answer_mode"], "projection_preservation_answer")
		self.assertFalse(record["release_blocking"])

	def test_pl_cogs_drilldown_capture_imports_rank_2_document(self):
		record = build_manual_uat_import_record(_capture("pl_cogs_source_document_rank_2"))

		self.assertEqual(record["parse_status"], IMPORT_PARSE_ACCEPTED)
		self.assertEqual(record["archive_import_record"]["observed_trace_fields"]["entity_type"], "document")
		self.assertEqual(record["archive_import_record"]["observed_trace_fields"]["row_reference"], "rank_2")
		self.assertFalse(record["release_blocking"])

	def test_prediction_and_causal_boundaries_are_preserved(self):
		prediction = build_manual_uat_import_record(_capture("ar_rank_2_default_prediction_boundary"))
		causal = build_manual_uat_import_record(_capture("ar_first_customer_cause_boundary"))

		self.assertEqual(prediction["parse_status"], IMPORT_PARSE_ACCEPTED)
		self.assertEqual(prediction["archive_import_record"]["observed_trace_fields"]["policy_boundary"], "prediction_boundary")
		self.assertEqual(causal["parse_status"], IMPORT_PARSE_ACCEPTED)
		self.assertEqual(causal["archive_import_record"]["observed_trace_fields"]["policy_boundary"], "causal_boundary")

	def test_failed_business_outcome_can_be_imported_but_still_blocks_archive_release(self):
		record = build_manual_uat_import_record(
			_capture(
				"product_top7_rank_8_out_of_range",
				status=MANUAL_UAT_STATUS_FAIL,
				failure_reason="Assistant invented a rank outside the visible rows.",
			)
		)

		self.assertEqual(record["parse_status"], IMPORT_PARSE_ACCEPTED)
		self.assertEqual(record["uat_status"], MANUAL_UAT_STATUS_FAIL)
		self.assertTrue(record["release_blocking"])
		self.assertFalse(record["archive_record_contract"]["archive_complete"])

	def test_missing_trace_section_blocks_registered_capture(self):
		capture = _capture("visible_ap_current_rank_2")
		capture["raw_trace_text"] = _raw_trace_for("visible_ap_current_rank_2", omit_trace=True)

		record = build_manual_uat_import_record(capture)

		self.assertEqual(record["parse_status"], IMPORT_PARSE_BLOCKED)
		self.assertTrue(record["release_blocking"])
		self.assertIn("observed_trace_fields.route", record["missing_capture_sections"])
		self.assertIn("observed_trace_fields.entity_type", record["missing_capture_sections"])

	def test_missing_model_role_section_blocks_registered_capture(self):
		capture = _capture("pl_cogs_source_document_rank_2")
		capture["raw_trace_text"] = _raw_trace_for("pl_cogs_source_document_rank_2", omit_model_role=True)

		record = build_manual_uat_import_record(capture)

		self.assertEqual(record["parse_status"], IMPORT_PARSE_BLOCKED)
		self.assertTrue(record["release_blocking"])
		self.assertIn("observed_model_role_fields.model_role_lane", record["missing_capture_sections"])

	def test_missing_final_answer_authority_blocks_registered_capture(self):
		capture = _capture("visible_ap_current_rank_2")
		capture["raw_trace_text"] = _raw_trace_for("visible_ap_current_rank_2", omit_final_answer_authority=True)

		record = build_manual_uat_import_record(capture)

		self.assertEqual(record["parse_status"], IMPORT_PARSE_BLOCKED)
		self.assertTrue(record["release_blocking"])
		self.assertIn("final_answer_authority.authority_source", record["missing_capture_sections"])
		self.assertIn("final_answer_authority.preflight_status", record["missing_capture_sections"])

	def test_incomplete_final_answer_authority_blocks_registered_capture(self):
		capture = _capture("visible_ap_current_rank_2")
		capture["raw_trace_text"] = _raw_trace_for(
			"visible_ap_current_rank_2",
			final_authority_complete="False",
			final_preflight_status="missing_authority",
			final_missing_fields="authority_source",
		)

		record = build_manual_uat_import_record(capture)

		self.assertEqual(record["parse_status"], IMPORT_PARSE_BLOCKED)
		self.assertTrue(record["release_blocking"])
		self.assertIn("final_answer_authority.authority_complete_true", record["missing_capture_sections"])
		self.assertIn("final_answer_authority.preflight_status_allowed", record["missing_capture_sections"])
		self.assertIn("final_answer_authority.missing_fields_none", record["missing_capture_sections"])

	def test_unstructured_trace_is_quarantined_instead_of_interpreted(self):
		capture = _capture("visible_ap_current_rank_2")
		capture["raw_trace_text"] = "The answer looked okay to me."

		record = build_manual_uat_import_record(capture)

		self.assertEqual(record["parse_status"], IMPORT_PARSE_QUARANTINED)
		self.assertEqual(record["quarantine_reason"], "trace_not_structured")
		self.assertTrue(record["release_blocking"])

	def test_unknown_scenario_is_quarantined_and_cannot_feed_fake_green_status(self):
		capture = _capture("visible_ap_current_rank_2")
		capture["scenario_id"] = "future_tax_uat_scenario"

		record = build_manual_uat_import_record(capture)

		self.assertEqual(record["parse_status"], IMPORT_PARSE_QUARANTINED)
		self.assertEqual(record["quarantine_reason"], "unknown_scenario")
		self.assertFalse(record["scenario_registered"])
		self.assertTrue(record["release_blocking"])

	def test_raw_evidence_hash_is_stable_and_changes_when_raw_evidence_changes(self):
		first = build_manual_uat_import_record(_capture("visible_ap_current_rank_2"))
		second = build_manual_uat_import_record(_capture("visible_ap_current_rank_2"))
		changed_capture = _capture("visible_ap_current_rank_2")
		changed_capture["raw_answer_text"] = "Different captured answer text."
		changed = build_manual_uat_import_record(changed_capture)

		self.assertEqual(first["raw_evidence_hash"], second["raw_evidence_hash"])
		self.assertNotEqual(first["raw_evidence_hash"], changed["raw_evidence_hash"])

	def test_import_batch_feeds_archive_and_release_ready_only_for_complete_expected_set(self):
		complete = build_manual_uat_import_batch(
			[
				_capture("visible_ar_after_ap_typed_rank_2"),
				_capture("visible_ap_current_rank_2"),
			],
			expected_scenario_ids=[
				"visible_ar_after_ap_typed_rank_2",
				"visible_ap_current_rank_2",
			],
			generated_at="2026-05-13T13:15:00+06:30",
		)
		incomplete = build_manual_uat_import_batch(
			[_capture("visible_ar_after_ap_typed_rank_2")],
			expected_scenario_ids=[
				"visible_ar_after_ap_typed_rank_2",
				"visible_ap_current_rank_2",
			],
			generated_at="2026-05-13T13:15:00+06:30",
		)

		self.assertEqual(complete["type"], MANUAL_UAT_IMPORT_BATCH_CONTRACT_TYPE)
		self.assertTrue(complete["import_complete"])
		self.assertTrue(complete["archive_release_ready"])
		self.assertTrue(complete["release_ready"])
		self.assertEqual(complete["accepted_record_count"], 2)
		self.assertEqual(complete["archive_import_record_count"], 2)
		self.assertFalse(incomplete["release_ready"])
		self.assertIn("visible_ap_current_rank_2", incomplete["archive_index_contract"]["missing_evidence_scenario_ids"])

	def test_markdown_and_json_import_writers_are_deterministic(self):
		captures = [
			_capture("visible_ar_after_ap_typed_rank_2"),
			_capture("visible_ap_current_rank_2"),
		]
		with tempfile.TemporaryDirectory() as tmp:
			json_path = Path(tmp) / "uat_import.json"
			markdown_path = Path(tmp) / "uat_import.md"

			first = write_manual_uat_import_files(
				captures,
				json_path=str(json_path),
				markdown_path=str(markdown_path),
				expected_scenario_ids=[
					"visible_ar_after_ap_typed_rank_2",
					"visible_ap_current_rank_2",
				],
				generated_at="2026-05-13T13:30:00+06:30",
				reviewer="uat@example.com",
			)
			first_json = json_path.read_text(encoding="utf-8")
			first_markdown = markdown_path.read_text(encoding="utf-8")
			second = write_manual_uat_import_files(
				captures,
				json_path=str(json_path),
				markdown_path=str(markdown_path),
				expected_scenario_ids=[
					"visible_ar_after_ap_typed_rank_2",
					"visible_ap_current_rank_2",
				],
				generated_at="2026-05-13T13:30:00+06:30",
				reviewer="uat@example.com",
			)

			self.assertTrue(first["json_artifact_written"])
			self.assertTrue(first["markdown_artifact_written"])
			self.assertTrue(second["markdown_artifact_written"])
			self.assertEqual(first_json, json_path.read_text(encoding="utf-8"))
			self.assertEqual(first_markdown, markdown_path.read_text(encoding="utf-8"))
			loaded = json.loads(first_json)
			self.assertTrue(loaded["release_ready"])
			self.assertIn("# S7 Manual UAT Evidence Import Batch", first_markdown)
			self.assertIn("visible_ar_after_ap_typed_rank_2", first_markdown)

	def test_empty_import_artifact_is_structurally_complete_but_not_release_ready(self):
		batch = build_manual_uat_import_batch(
			[],
			expected_scenario_ids=["visible_ar_after_ap_typed_rank_2"],
			generated_at="2026-05-13T13:45:00+06:30",
		)
		markdown = render_manual_uat_import_markdown(batch)

		self.assertTrue(batch["import_complete"])
		self.assertFalse(batch["release_ready"])
		self.assertEqual(batch["capture_record_count"], 0)
		self.assertIn("visible_ar_after_ap_typed_rank_2", markdown)

	def test_s7_6i_import_suite_is_release_blocking_in_regression_boundary(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_IMPORT_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_IMPORT_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_IMPORT_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
