import io
import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_capture_template import build_manual_uat_capture_template
from ai_assistant_ui.qwen_chat.manual_uat_evidence import MANUAL_UAT_STATUS_PASS
from ai_assistant_ui.qwen_chat.manual_uat_operator_evidence_cli import (
	MANUAL_UAT_OPERATOR_EVIDENCE_CLI_CONTRACT_TYPE,
	MANUAL_UAT_OPERATOR_EVIDENCE_CLI_SUITE_ID,
	build_operator_evidence_cli_report,
	load_operator_capture_records,
	main,
	write_operator_evidence_cli_report,
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


def _model_role_parts(scenario):
	model_role_lane = scenario["expected_model_role_lane"]
	lane, _, model_role = model_role_lane.partition(":")
	return model_role_lane, lane or model_role_lane, model_role or model_role_lane


def _raw_trace_for(scenario_id: str) -> str:
	scenario = _scenario_by_id(scenario_id)
	model_role_lane, lane, model_role = _model_role_parts(scenario)
	policy_boundary = scenario["expected_policy_boundary"]
	preflight_status = "bounded" if policy_boundary != "none" else "passed"
	return "\n".join(
		[
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
			f"| lane | {lane} |",
			f"| model_role | {model_role} |",
			f"| expected_model_role | {model_role} |",
			"| role_compliance | compliant |",
			"",
		]
	)


def _operator_capture(
	scenario_id: str,
	*,
	operator_attestation: str = "I confirm this evidence was captured from browser UAT and is ready for promotion review.",
):
	scenario = _scenario_by_id(scenario_id)
	template = build_manual_uat_capture_template(scenario)
	record = dict(template["import_ready_json_skeleton"])
	record["reviewer"] = "uat@example.com"
	record["captured_at"] = "2026-05-13T23:30:00+06:30"
	record["uat_status"] = MANUAL_UAT_STATUS_PASS
	record["failure_reason"] = ""
	record["raw_answer_text"] = f"Captured answer for {scenario_id}."
	record["raw_trace_text"] = _raw_trace_for(scenario_id)
	record["observed_answer_summary"] = f"Captured answer for {scenario_id}."
	record["operator_attestation"] = operator_attestation
	return record


def _write_json(path: Path, payload):
	path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class ManualUATOperatorEvidenceCLIContractTests(unittest.TestCase):
	def test_valid_multi_record_operator_file_exits_zero_and_writes_artifacts(self):
		scenario_ids = ["visible_ar_after_ap_typed_rank_2", "visible_ap_current_rank_2"]
		with tempfile.TemporaryDirectory() as tmp:
			out_dir = Path(tmp) / "out"
			capture_path = Path(tmp) / "captures.json"
			_write_json(capture_path, [_operator_capture(scenario_id) for scenario_id in scenario_ids])
			stdout = io.StringIO()

			exit_code = main(
				[
					"--captures",
					str(capture_path),
					"--expected-scenarios",
					",".join(scenario_ids),
					"--reviewer",
					"uat@example.com",
					"--generated-at",
					"2026-05-13T23:30:00+06:30",
					"--out-dir",
					str(out_dir),
					"--strict",
					"--overwrite",
				],
				stdout=stdout,
			)

			self.assertEqual(exit_code, 0)
			self.assertIn("Release ready: True", stdout.getvalue())
			report = json.loads((out_dir / "qwen_s7_operator_evidence_import_cli_report.json").read_text(encoding="utf-8"))
			self.assertEqual(report["type"], MANUAL_UAT_OPERATOR_EVIDENCE_CLI_CONTRACT_TYPE)
			self.assertTrue(report["release_ready"])
			self.assertTrue((out_dir / "qwen_s7_manual_uat_real_evidence_intake.json").exists())
			self.assertTrue((out_dir / "qwen_s7_manual_uat_real_evidence_promotion_report.md").exists())

	def test_missing_capture_file_exits_nonzero_with_file_boundary(self):
		with tempfile.TemporaryDirectory() as tmp:
			report = write_operator_evidence_cli_report(
				[Path(tmp) / "missing.json"],
				out_dir=str(Path(tmp) / "out"),
				overwrite=True,
				generated_at="2026-05-13T23:30:00+06:30",
			)

			self.assertFalse(report["release_ready"])
			self.assertEqual(report["exit_code"], 1)
			self.assertIn("capture_file_missing", report["release_blocking_reasons"])

	def test_malformed_json_exits_nonzero(self):
		with tempfile.TemporaryDirectory() as tmp:
			capture_path = Path(tmp) / "bad.json"
			capture_path.write_text("{not json", encoding="utf-8")

			report = write_operator_evidence_cli_report(
				[str(capture_path)],
				out_dir=str(Path(tmp) / "out"),
				overwrite=True,
			)

			self.assertFalse(report["release_ready"])
			self.assertIn("capture_file_malformed_json", report["release_blocking_reasons"])

	def test_non_list_non_dict_json_payload_is_blocked(self):
		with tempfile.TemporaryDirectory() as tmp:
			capture_path = Path(tmp) / "bad.json"
			_write_json(capture_path, "not a record")

			result = load_operator_capture_records([str(capture_path)])

			self.assertEqual(result["capture_records"], [])
			self.assertIn("capture_file_payload_not_supported", result["file_blocking_reasons"])
			self.assertIn("capture_file_no_records", result["file_blocking_reasons"])

	def test_missing_operator_attestation_is_blocked_by_s7_6o(self):
		scenario_id = "visible_ap_current_rank_2"
		with tempfile.TemporaryDirectory() as tmp:
			capture_path = Path(tmp) / "captures.json"
			_write_json(capture_path, [_operator_capture(scenario_id, operator_attestation="")])

			report = write_operator_evidence_cli_report(
				[str(capture_path)],
				expected_scenario_ids=[scenario_id],
				out_dir=str(Path(tmp) / "out"),
				overwrite=True,
			)

			self.assertFalse(report["release_ready"])
			self.assertIn("operator_attestation_missing", report["release_blocking_reasons"])
			self.assertIn("intake_record_not_accepted", report["release_blocking_reasons"])

	def test_sample_fixture_file_is_loaded_but_not_promoted(self):
		with tempfile.TemporaryDirectory() as tmp:
			fixture = build_manual_uat_sample_fixture(generated_at="2026-05-13T23:30:00+06:30")
			capture_path = Path(tmp) / "sample_fixture.json"
			_write_json(capture_path, fixture)

			report = write_operator_evidence_cli_report(
				[str(capture_path)],
				expected_scenario_ids=fixture["sample_scenario_ids"],
				out_dir=str(Path(tmp) / "out"),
				overwrite=True,
			)

			self.assertFalse(report["release_ready"])
			self.assertTrue(report["intake_contract"]["sample_record_ids"])
			self.assertIn("sample_evidence_not_allowed", report["release_blocking_reasons"])

	def test_unknown_scenario_is_quarantined(self):
		capture = _operator_capture("visible_ap_current_rank_2")
		capture["scenario_id"] = "future_tax_scenario"
		with tempfile.TemporaryDirectory() as tmp:
			capture_path = Path(tmp) / "captures.json"
			_write_json(capture_path, [capture])

			report = write_operator_evidence_cli_report(
				[str(capture_path)],
				expected_scenario_ids=["future_tax_scenario"],
				out_dir=str(Path(tmp) / "out"),
				overwrite=True,
			)

			self.assertFalse(report["release_ready"])
			self.assertIn("quarantined_import_records", report["release_blocking_reasons"])

	def test_strict_expected_scenario_mismatch_blocks_even_when_intake_has_records(self):
		with tempfile.TemporaryDirectory() as tmp:
			capture_path = Path(tmp) / "captures.json"
			_write_json(capture_path, [_operator_capture("visible_ap_current_rank_2")])

			report = write_operator_evidence_cli_report(
				[str(capture_path)],
				expected_scenario_ids=["visible_ar_after_ap_typed_rank_2"],
				out_dir=str(Path(tmp) / "out"),
				strict=True,
				overwrite=True,
			)

			self.assertFalse(report["release_ready"])
			self.assertIn("strict_expected_scenarios_mismatch", report["release_blocking_reasons"])

	def test_existing_output_requires_overwrite_flag(self):
		scenario_id = "visible_ap_current_rank_2"
		with tempfile.TemporaryDirectory() as tmp:
			out_dir = Path(tmp) / "out"
			capture_path = Path(tmp) / "captures.json"
			_write_json(capture_path, [_operator_capture(scenario_id)])
			first = write_operator_evidence_cli_report(
				[str(capture_path)],
				expected_scenario_ids=[scenario_id],
				out_dir=str(out_dir),
				overwrite=True,
			)
			second = write_operator_evidence_cli_report(
				[str(capture_path)],
				expected_scenario_ids=[scenario_id],
				out_dir=str(out_dir),
				overwrite=False,
			)

			self.assertTrue(first["release_ready"])
			self.assertFalse(second["release_ready"])
			self.assertFalse(second["artifacts_written"])
			self.assertIn("output_file_exists_without_overwrite", second["release_blocking_reasons"])

	def test_expected_scenarios_file_is_supported(self):
		scenario_id = "visible_ap_current_rank_2"
		with tempfile.TemporaryDirectory() as tmp:
			capture_path = Path(tmp) / "captures.json"
			expected_path = Path(tmp) / "expected.json"
			_write_json(capture_path, [_operator_capture(scenario_id)])
			_write_json(expected_path, [scenario_id])

			report = write_operator_evidence_cli_report(
				[str(capture_path)],
				expected_scenarios_file=str(expected_path),
				out_dir=str(Path(tmp) / "out"),
				strict=True,
				overwrite=True,
			)

			self.assertTrue(report["release_ready"])
			self.assertEqual(report["expected_scenario_ids"], [scenario_id])

	def test_s7_6p_operator_evidence_cli_suite_is_release_blocking(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_OPERATOR_EVIDENCE_CLI_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_OPERATOR_EVIDENCE_CLI_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_OPERATOR_EVIDENCE_CLI_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
