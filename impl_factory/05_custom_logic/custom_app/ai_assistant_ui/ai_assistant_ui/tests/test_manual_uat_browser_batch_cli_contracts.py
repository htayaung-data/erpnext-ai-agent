import io
import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_browser_batch_cli import (
	ADAPTER_MODE_CAPTURE_RESULT_IMPORT,
	ADAPTER_MODE_PLAN_ONLY,
	CLI_STATUS_BLOCKED,
	CLI_STATUS_PLAN_READY,
	CLI_STATUS_RELEASE_READY,
	MANUAL_UAT_BROWSER_BATCH_CLI_CONTRACT_TYPE,
	MANUAL_UAT_BROWSER_BATCH_CLI_SUITE_ID,
	build_browser_batch_cli_report,
	load_browser_capture_results,
	main,
	parse_browser_batch_scenario_ids,
	write_browser_batch_cli_report,
)
from ai_assistant_ui.qwen_chat.regression_suite_governance import (
	BLOCKING_RELEASE,
	GATE_RELEASE_BLOCKING_CONTRACT,
	RELEASE_BLOCKING_SUITE_IDS,
	RUNTIME_NONE,
	build_regression_suite_boundary_contract,
)


def _complete_capture(scenario_id: str):
	return {
		"scenario_id": scenario_id,
		"execution_envelope_id": f"s7_6u:{scenario_id}:1",
		"browser_session_id": f"browser-session-{scenario_id}",
		"prompt_turn_count": 2,
		"checkpoint_state": "trace_captured",
		"raw_answer_text": f"Captured answer for {scenario_id}.",
		"raw_trace_text": f"Context Authority Trace for {scenario_id}.",
		"trace_scenario_id": scenario_id,
		"timeout_state": "completed",
		"retry_count": 0,
		"max_retries": 1,
		"cleanup_state": "session_checkpointed",
	}


def _timeout_capture(scenario_id: str):
	return {
		"scenario_id": scenario_id,
		"execution_envelope_id": f"s7_6u:{scenario_id}:1",
		"browser_session_id": f"browser-session-{scenario_id}",
		"prompt_turn_count": 2,
		"checkpoint_state": "answer_captured",
		"raw_answer_text": f"Captured answer for {scenario_id}, but trace did not complete.",
		"raw_trace_text": "",
		"trace_scenario_id": scenario_id,
		"timeout_state": "browser_timeout",
		"retry_count": 0,
		"max_retries": 2,
		"cleanup_state": "session_checkpointed",
	}


def _write_json(path: Path, payload):
	path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class ManualUATBrowserBatchCLIContractTests(unittest.TestCase):
	def test_plan_only_selected_scenarios_is_exit_zero_without_capture_results(self):
		report = build_browser_batch_cli_report(
			["visible_ap_current_rank_2", "visible_ar_after_ap_typed_rank_2"],
			plan_only=True,
			generated_at="2026-05-14T02:00:00+06:30",
			reviewer="codex_s7_6u",
		)

		self.assertEqual(report["type"], MANUAL_UAT_BROWSER_BATCH_CLI_CONTRACT_TYPE)
		self.assertEqual(report["adapter_mode"], ADAPTER_MODE_PLAN_ONLY)
		self.assertEqual(report["cli_status"], CLI_STATUS_PLAN_READY)
		self.assertTrue(report["plan_ready"])
		self.assertFalse(report["release_ready"])
		self.assertEqual(report["exit_code"], 0)
		self.assertEqual(report["capture_result_count"], 0)

	def test_release_ready_capture_results_write_runner_and_cli_artifacts(self):
		scenario_ids = ["visible_ap_current_rank_2", "visible_ar_after_ap_typed_rank_2"]
		with tempfile.TemporaryDirectory() as tmp:
			tmp_path = Path(tmp)
			capture_path = tmp_path / "captures.json"
			out_dir = tmp_path / "out"
			operator_bundle = tmp_path / "operator_capture.json"
			_write_json(capture_path, {"capture_results": [_complete_capture(scenario_id) for scenario_id in scenario_ids]})

			report = write_browser_batch_cli_report(
				scenario_ids,
				capture_result_paths=[str(capture_path)],
				reviewer="codex_s7_6u",
				generated_at="2026-05-14T02:00:00+06:30",
				out_dir=str(out_dir),
				operator_capture_bundle_path=str(operator_bundle),
				overwrite=True,
			)

			self.assertEqual(report["adapter_mode"], ADAPTER_MODE_CAPTURE_RESULT_IMPORT)
			self.assertEqual(report["cli_status"], CLI_STATUS_RELEASE_READY)
			self.assertTrue(report["release_ready"])
			self.assertTrue(report["artifacts_written"])
			self.assertEqual(report["promotion_eligible_scenario_ids"], scenario_ids)
			self.assertIn(str(operator_bundle), report["strict_import_command"])
			self.assertEqual(report["strict_import_command_argv"][0], "python3")
			self.assertIn("--strict", report["strict_import_command_argv"])
			self.assertTrue((out_dir / "qwen_s7_browser_batch_cli_report.json").exists())
			self.assertTrue((out_dir / "qwen_s7_browser_batch_resilience_runner_contract.json").exists())
			loaded = json.loads((out_dir / "qwen_s7_browser_batch_cli_report.json").read_text(encoding="utf-8"))
			self.assertTrue(loaded["release_ready"])

	def test_partial_capture_is_blocked_but_exports_only_promotion_eligible_strict_import_argv(self):
		with tempfile.TemporaryDirectory() as tmp:
			capture_path = Path(tmp) / "captures.json"
			_write_json(
				capture_path,
				[
					_complete_capture("visible_ap_current_rank_2"),
					_timeout_capture("product_rank_2_after_million_projection"),
				],
			)

			report = build_browser_batch_cli_report(
				["visible_ap_current_rank_2", "product_rank_2_after_million_projection"],
				capture_result_paths=[str(capture_path)],
				generated_at="2026-05-14T02:00:00+06:30",
				overwrite=True,
			)

			self.assertEqual(report["cli_status"], CLI_STATUS_BLOCKED)
			self.assertFalse(report["release_ready"])
			self.assertIn("runner_not_release_ready", report["release_blocking_reasons"])
			self.assertEqual(report["promotion_eligible_scenario_ids"], ["visible_ap_current_rank_2"])
			self.assertIn("product_rank_2_after_million_projection", report["blocked_scenario_ids"])
			self.assertIn("product_rank_2_after_million_projection", report["retryable_scenario_ids"])
			self.assertIn("visible_ap_current_rank_2", report["strict_import_command_argv"])
			self.assertNotIn("product_rank_2_after_million_projection", report["strict_import_command_argv"])

	def test_duplicate_capture_result_blocks_cli_via_runner_contract(self):
		with tempfile.TemporaryDirectory() as tmp:
			capture_path = Path(tmp) / "captures.json"
			_write_json(
				capture_path,
				[
					_complete_capture("visible_ap_current_rank_2"),
					_complete_capture("visible_ap_current_rank_2"),
				],
			)

			report = build_browser_batch_cli_report(
				["visible_ap_current_rank_2"],
				capture_result_paths=[str(capture_path)],
				generated_at="2026-05-14T02:00:00+06:30",
				overwrite=True,
			)

			self.assertFalse(report["release_ready"])
			self.assertIn("runner_not_release_ready", report["release_blocking_reasons"])
			self.assertIn("duplicate_capture_result", report["runner_contract"]["failure_reason_codes"])

	def test_missing_capture_file_is_blocked_before_runner_promotion(self):
		with tempfile.TemporaryDirectory() as tmp:
			report = build_browser_batch_cli_report(
				["visible_ap_current_rank_2"],
				capture_result_paths=[str(Path(tmp) / "missing.json")],
				generated_at="2026-05-14T02:00:00+06:30",
				overwrite=True,
			)

			self.assertFalse(report["release_ready"])
			self.assertEqual(report["exit_code"], 1)
			self.assertIn("capture_result_file_missing", report["release_blocking_reasons"])

	def test_malformed_capture_file_is_blocked(self):
		with tempfile.TemporaryDirectory() as tmp:
			capture_path = Path(tmp) / "bad.json"
			capture_path.write_text("{not json", encoding="utf-8")

			result = load_browser_capture_results([str(capture_path)])

			self.assertEqual(result["capture_results"], [])
			self.assertIn("capture_result_file_malformed_json", result["file_blocking_reasons"])

	def test_existing_output_requires_overwrite_flag(self):
		with tempfile.TemporaryDirectory() as tmp:
			capture_path = Path(tmp) / "captures.json"
			out_dir = Path(tmp) / "out"
			_write_json(capture_path, [_complete_capture("visible_ap_current_rank_2")])
			first = write_browser_batch_cli_report(
				["visible_ap_current_rank_2"],
				capture_result_paths=[str(capture_path)],
				out_dir=str(out_dir),
				overwrite=True,
			)
			second = write_browser_batch_cli_report(
				["visible_ap_current_rank_2"],
				capture_result_paths=[str(capture_path)],
				out_dir=str(out_dir),
				overwrite=False,
			)

			self.assertTrue(first["release_ready"])
			self.assertFalse(second["release_ready"])
			self.assertFalse(second["artifacts_written"])
			self.assertIn("output_file_exists_without_overwrite", second["release_blocking_reasons"])

	def test_scenario_file_is_supported(self):
		with tempfile.TemporaryDirectory() as tmp:
			scenario_file = Path(tmp) / "scenarios.json"
			_write_json(scenario_file, {"scenario_ids": ["visible_ap_current_rank_2"]})

			result = parse_browser_batch_scenario_ids(scenario_file=str(scenario_file))

			self.assertEqual(result["scenario_ids"], ["visible_ap_current_rank_2"])
			self.assertEqual(result["blocking_reasons"], [])

	def test_cli_main_plan_only_outputs_summary_and_exit_zero(self):
		stdout = io.StringIO()
		exit_code = main(
			[
				"--scenarios",
				"visible_ap_current_rank_2",
				"--plan-only",
				"--generated-at",
				"2026-05-14T02:00:00+06:30",
				"--reviewer",
				"codex_s7_6u",
				"--overwrite",
			],
			stdout=stdout,
		)

		self.assertEqual(exit_code, 0)
		self.assertIn("S7-6U Browser Batch CLI Adapter", stdout.getvalue())
		self.assertIn("Status: plan_ready", stdout.getvalue())

	def test_s7_6u_browser_batch_cli_suite_is_release_blocking(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_BROWSER_BATCH_CLI_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_BROWSER_BATCH_CLI_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_BROWSER_BATCH_CLI_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
