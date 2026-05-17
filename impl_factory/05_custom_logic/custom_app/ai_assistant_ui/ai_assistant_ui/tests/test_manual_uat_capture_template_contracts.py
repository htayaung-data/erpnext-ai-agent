import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_capture_template import (
	IMPORT_READY_JSON_FIELDS,
	MANUAL_UAT_CAPTURE_TEMPLATE_CONTRACT_TYPE,
	MANUAL_UAT_CAPTURE_TEMPLATE_PACK_CONTRACT_TYPE,
	MANUAL_UAT_CAPTURE_TEMPLATE_SUITE_ID,
	build_manual_uat_capture_template,
	build_manual_uat_capture_template_pack,
	render_manual_uat_capture_template_markdown,
	write_manual_uat_capture_template_files,
)
from ai_assistant_ui.qwen_chat.manual_uat_evidence import (
	REQUIRED_OBSERVED_MODEL_ROLE_KEYS,
	REQUIRED_OBSERVED_TRACE_KEYS,
)
from ai_assistant_ui.qwen_chat.manual_uat_export import (
	build_manual_uat_export_contract,
	render_manual_uat_export_markdown,
)
from ai_assistant_ui.qwen_chat.manual_uat_import import (
	FINAL_ANSWER_AUTHORITY_FIELDS,
	IMPORT_PARSE_ACCEPTED,
	REQUIRED_IMPORT_ENVELOPE_FIELDS,
	REQUIRED_FINAL_ANSWER_AUTHORITY_KEYS,
	build_manual_uat_import_record,
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


def _filled_skeleton(scenario_id: str):
	scenario = _scenario_by_id(scenario_id)
	template = build_manual_uat_capture_template(scenario)
	skeleton = dict(template["import_ready_json_skeleton"])
	skeleton["reviewer"] = "uat@example.com"
	skeleton["captured_at"] = "2026-05-13T14:30:00+06:30"
	skeleton["capture_source"] = "manual_browser_uat"
	skeleton["operator_attestation"] = "I confirm this evidence was captured from real browser UAT."
	skeleton["uat_status"] = "pass"
	skeleton["raw_answer_text"] = f"Captured answer for {scenario_id}."
	skeleton["raw_trace_text"] = _matching_raw_trace(scenario)
	skeleton["observed_answer_summary"] = f"Captured answer for {scenario_id}."
	return skeleton


class ManualUATCaptureTemplateContractTests(unittest.TestCase):
	def test_every_scenario_has_complete_capture_template(self):
		pack = build_manual_uat_capture_template_pack(generated_at="2026-05-13T14:30:00+06:30")

		self.assertEqual(pack["type"], MANUAL_UAT_CAPTURE_TEMPLATE_PACK_CONTRACT_TYPE)
		self.assertTrue(pack["template_pack_complete"])
		self.assertEqual(pack["scenario_count"], len(S7_REGRESSION_SCENARIO_REGISTRY))
		self.assertEqual(pack["incomplete_templates"], [])
		self.assertEqual(len(pack["templates"]), len(S7_REGRESSION_SCENARIO_REGISTRY))
		for template in pack["templates"]:
			with self.subTest(template=template["scenario_id"]):
				self.assertEqual(template["type"], MANUAL_UAT_CAPTURE_TEMPLATE_CONTRACT_TYPE)
				self.assertTrue(template["template_complete"])
				self.assertTrue(template["manual_uat_prompt"])
				self.assertTrue(template["pass_criteria"])
				self.assertEqual(template["missing_fields"], [])

	def test_template_includes_all_import_trace_and_model_role_fields(self):
		template = build_manual_uat_capture_template(_scenario_by_id("visible_ar_after_ap_typed_rank_2"))

		for field in REQUIRED_IMPORT_ENVELOPE_FIELDS:
			self.assertIn(field, template["required_import_fields"])
			self.assertIn(field, template["import_ready_json_fields"])
			self.assertIn(field, template["import_ready_json_skeleton"])
		for field in REQUIRED_OBSERVED_TRACE_KEYS:
			self.assertIn(field, template["required_trace_fields"])
			self.assertIn(f"observed_trace_fields.{field}", template["import_ready_json_fields"])
			self.assertIn(field, template["import_ready_json_skeleton"]["observed_trace_fields"])
		for field in REQUIRED_OBSERVED_MODEL_ROLE_KEYS:
			self.assertIn(field, template["required_model_role_fields"])
			self.assertIn(f"observed_model_role_fields.{field}", template["import_ready_json_fields"])
			self.assertIn(field, template["import_ready_json_skeleton"]["observed_model_role_fields"])
		for field in REQUIRED_FINAL_ANSWER_AUTHORITY_KEYS:
			self.assertIn(field, template["required_final_answer_authority_fields"])
		for field in FINAL_ANSWER_AUTHORITY_FIELDS:
			self.assertIn(f"final_answer_authority.{field}", template["import_ready_json_fields"])
			self.assertIn(field, template["import_ready_json_skeleton"]["final_answer_authority"])
		self.assertEqual(set(template["import_ready_json_fields"]), set(IMPORT_READY_JSON_FIELDS))

	def test_manual_only_scenario_remains_manual_only_in_template(self):
		template = build_manual_uat_capture_template(_scenario_by_id("browser_manual_end_to_end_uat"))

		self.assertTrue(template["manual_only"])
		self.assertEqual(template["blocking_level"], "manual_acceptance_required")
		self.assertEqual(template["execution_mode"], "manual_browser_uat")

	def test_markdown_render_contains_scenario_expected_fields_and_capture_tables(self):
		pack = build_manual_uat_capture_template_pack(generated_at="2026-05-13T14:30:00+06:30")
		markdown = render_manual_uat_capture_template_markdown(pack)

		self.assertIn("# S7 Manual UAT Operator Capture Template", markdown)
		self.assertIn("visible_ar_after_ap_typed_rank_2", markdown)
		self.assertIn("product_projection_qty_preserves_revenue", markdown)
		self.assertIn("pl_cogs_source_document_rank_2", markdown)
		self.assertIn("ar_rank_2_default_prediction_boundary", markdown)
		self.assertIn("Observed Trace Fields", markdown)
		self.assertIn("Observed Model Role Fields", markdown)
		self.assertIn("Final Answer Authority", markdown)
		self.assertIn("Import-Ready JSON Skeleton", markdown)
		for field in REQUIRED_OBSERVED_TRACE_KEYS:
			self.assertIn(f"observed_trace_fields.{field}", markdown)
			self.assertIn(f"| {field} |", markdown)
		for field in REQUIRED_OBSERVED_MODEL_ROLE_KEYS:
			self.assertIn(f"observed_model_role_fields.{field}", markdown)
			self.assertIn(f"| {field} |", markdown)
		for field in FINAL_ANSWER_AUTHORITY_FIELDS:
			self.assertIn(f"final_answer_authority.{field}", markdown)
			self.assertIn(f"| {field} |", markdown)

	def test_json_skeletons_are_deterministic_and_import_ready(self):
		first = build_manual_uat_capture_template_pack(generated_at="2026-05-13T14:30:00+06:30")
		second = build_manual_uat_capture_template_pack(generated_at="2026-05-13T14:30:00+06:30")
		first_json = json.dumps(first["import_ready_json_skeletons"], indent=2, sort_keys=True)
		second_json = json.dumps(second["import_ready_json_skeletons"], indent=2, sort_keys=True)

		self.assertEqual(first_json, second_json)
		self.assertIn('"scenario_id": "visible_ar_after_ap_typed_rank_2"', first_json)
		self.assertIn('"observed_trace_fields"', first_json)
		self.assertIn('"observed_model_role_fields"', first_json)
		self.assertIn('"final_answer_authority"', first_json)

	def test_template_skeleton_can_feed_s7_6i_import_when_filled(self):
		record = build_manual_uat_import_record(_filled_skeleton("visible_ap_current_rank_2"))

		self.assertEqual(record["parse_status"], IMPORT_PARSE_ACCEPTED)
		self.assertFalse(record["release_blocking"])
		self.assertEqual(record["archive_record_contract"]["archive_complete"], True)

	def test_standalone_template_file_writer_is_deterministic(self):
		with tempfile.TemporaryDirectory() as tmp:
			markdown_path = Path(tmp) / "operator_template.md"
			json_path = Path(tmp) / "operator_template.json"

			first = write_manual_uat_capture_template_files(
				markdown_path=str(markdown_path),
				json_path=str(json_path),
				generated_at="2026-05-13T14:30:00+06:30",
			)
			first_markdown = markdown_path.read_text(encoding="utf-8")
			first_json = json_path.read_text(encoding="utf-8")
			second = write_manual_uat_capture_template_files(
				markdown_path=str(markdown_path),
				json_path=str(json_path),
				generated_at="2026-05-13T14:30:00+06:30",
			)

			self.assertTrue(first["markdown_artifact_written"])
			self.assertTrue(first["json_artifact_written"])
			self.assertTrue(second["markdown_artifact_written"])
			self.assertEqual(first_markdown, markdown_path.read_text(encoding="utf-8"))
			self.assertEqual(first_json, json_path.read_text(encoding="utf-8"))
			self.assertIn("# S7 Manual UAT Operator Capture Template", first_markdown)
			self.assertIn("visible_ar_after_ap_typed_rank_2", first_json)

	def test_manual_uat_export_embeds_operator_capture_templates(self):
		contract = build_manual_uat_export_contract(
			artifact_path="tmp/manual_uat.md",
			generated_at="2026-05-13T14:30:00+06:30",
		)
		markdown = render_manual_uat_export_markdown(contract)

		self.assertEqual(contract["source_capture_template_pack_contract"], MANUAL_UAT_CAPTURE_TEMPLATE_PACK_CONTRACT_TYPE)
		self.assertIn("capture_template_pack_contract", contract)
		self.assertIn("## Operator Capture Templates", markdown)
		self.assertIn("Capture Template: visible_ar_after_ap_typed_rank_2", markdown)
		self.assertIn("Import-Ready JSON Skeleton", markdown)

	def test_s7_6j_capture_template_suite_is_release_blocking_in_regression_boundary(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_CAPTURE_TEMPLATE_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_CAPTURE_TEMPLATE_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_CAPTURE_TEMPLATE_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
