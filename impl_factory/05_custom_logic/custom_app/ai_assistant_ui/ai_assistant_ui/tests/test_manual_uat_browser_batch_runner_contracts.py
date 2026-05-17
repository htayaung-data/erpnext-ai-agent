import json
import tempfile
import unittest
from pathlib import Path

from ai_assistant_ui.qwen_chat.manual_uat_browser_batch_runner import (
	BROWSER_BATCH_STATUS_PARTIAL_BLOCKED,
	BROWSER_BATCH_STATUS_RELEASE_READY,
	CHECKPOINT_ANSWER_CAPTURED,
	CHECKPOINT_TRACE_CAPTURED,
	FORBIDDEN_BROWSER_BATCH_ACTIONS,
	MANUAL_UAT_BROWSER_BATCH_RUNNER_CONTRACT_TYPE,
	MANUAL_UAT_BROWSER_BATCH_RUNNER_SUITE_ID,
	REQUIRED_BROWSER_BATCH_REASON_CODES,
	REQUIRED_CHECKPOINT_STATES,
	SCENARIO_STATUS_BLOCKED,
	SCENARIO_STATUS_PASSED,
	build_browser_batch_runner_contract,
	evaluate_browser_batch_scenario,
	render_browser_batch_runner_markdown,
	strict_import_command_argv,
	write_browser_batch_runner_files,
)
from ai_assistant_ui.qwen_chat.regression_suite_governance import (
	BLOCKING_RELEASE,
	GATE_RELEASE_BLOCKING_CONTRACT,
	RELEASE_BLOCKING_SUITE_IDS,
	RUNTIME_NONE,
	build_regression_suite_boundary_contract,
)


def _complete_capture(scenario_id: str, *, trace_scenario_id: str = "", cleanup_state: str = "session_checkpointed"):
	return {
		"scenario_id": scenario_id,
		"execution_envelope_id": f"s7_6t:{scenario_id}:1",
		"browser_session_id": f"browser-session-{scenario_id}",
		"prompt_turn_count": 2,
		"checkpoint_state": CHECKPOINT_TRACE_CAPTURED,
		"raw_answer_text": f"Captured answer for {scenario_id}.",
		"raw_trace_text": f"Context Authority Trace for {trace_scenario_id or scenario_id}.",
		"trace_scenario_id": trace_scenario_id or scenario_id,
		"timeout_state": "completed",
		"retry_count": 0,
		"max_retries": 1,
		"cleanup_state": cleanup_state,
	}


def _timeout_capture(scenario_id: str):
	return {
		"scenario_id": scenario_id,
		"execution_envelope_id": f"s7_6t:{scenario_id}:1",
		"browser_session_id": f"browser-session-{scenario_id}",
		"prompt_turn_count": 2,
		"checkpoint_state": CHECKPOINT_ANSWER_CAPTURED,
		"raw_answer_text": f"Captured answer for {scenario_id}, but trace did not complete.",
		"raw_trace_text": "",
		"timeout_state": "browser_timeout",
		"retry_count": 0,
		"max_retries": 2,
		"cleanup_state": "session_checkpointed",
	}


class ManualUATBrowserBatchRunnerContractTests(unittest.TestCase):
	def test_complete_scenario_is_promotion_eligible(self):
		scenario = evaluate_browser_batch_scenario(
			"visible_ap_current_rank_2",
			_complete_capture("visible_ap_current_rank_2"),
			generated_at="2026-05-14T01:10:00+06:30",
		)

		self.assertEqual(scenario["scenario_status"], SCENARIO_STATUS_PASSED)
		self.assertTrue(scenario["promotion_eligible"])
		self.assertEqual(scenario["blocking_reasons"], [])
		self.assertEqual(scenario["answer_capture_state"], "captured")
		self.assertEqual(scenario["trace_capture_state"], "captured")
		self.assertEqual(scenario["expected_entity_type"], "supplier")

	def test_batch_release_ready_when_all_expected_scenarios_complete(self):
		contract = build_browser_batch_runner_contract(
			["visible_ap_current_rank_2", "visible_ar_after_ap_typed_rank_2"],
			capture_results=[
				_complete_capture("visible_ap_current_rank_2"),
				_complete_capture("visible_ar_after_ap_typed_rank_2"),
			],
			generated_at="2026-05-14T01:10:00+06:30",
			reviewer="codex_s7_6t",
			capture_bundle_path="generated/s7_6t/captures.json",
			out_dir="generated/s7_6t",
		)

		self.assertEqual(contract["type"], MANUAL_UAT_BROWSER_BATCH_RUNNER_CONTRACT_TYPE)
		self.assertEqual(contract["batch_status"], BROWSER_BATCH_STATUS_RELEASE_READY)
		self.assertTrue(contract["release_ready"])
		self.assertEqual(
			contract["strict_import_expected_scenario_ids"],
			["visible_ap_current_rank_2", "visible_ar_after_ap_typed_rank_2"],
		)
		self.assertIn("--strict --overwrite", contract["strict_import_command"])
		self.assertEqual(
			contract["strict_import_command_argv"],
			[
				"python3",
				"scripts/qwen_manual_uat_operator_evidence_import.py",
				"--captures",
				"generated/s7_6t/captures.json",
				"--expected-scenarios",
				"visible_ap_current_rank_2,visible_ar_after_ap_typed_rank_2",
				"--reviewer",
				"codex_s7_6t",
				"--out-dir",
				"generated/s7_6t",
				"--strict",
				"--overwrite",
			],
		)
		self.assertEqual(contract["blocked_scenario_ids"], [])

	def test_structured_strict_import_argv_handles_empty_scenario_list(self):
		argv = strict_import_command_argv(
			capture_bundle_path="generated/s7_6t/captures.json",
			scenario_ids=[],
			reviewer="codex_s7_6t",
			out_dir="generated/s7_6t",
		)

		self.assertEqual(argv, [])

	def test_timeout_missing_trace_is_blocked_retryable_and_excluded_from_strict_import(self):
		contract = build_browser_batch_runner_contract(
			["visible_ap_current_rank_2", "product_rank_2_after_million_projection"],
			capture_results=[
				_complete_capture("visible_ap_current_rank_2"),
				_timeout_capture("product_rank_2_after_million_projection"),
			],
			generated_at="2026-05-14T01:10:00+06:30",
			max_retries=2,
		)
		scenarios = {entry["scenario_id"]: entry for entry in contract["scenario_contracts"]}
		blocked = scenarios["product_rank_2_after_million_projection"]

		self.assertEqual(contract["batch_status"], BROWSER_BATCH_STATUS_PARTIAL_BLOCKED)
		self.assertFalse(contract["release_ready"])
		self.assertTrue(contract["partial_capture_safe"])
		self.assertEqual(contract["strict_import_expected_scenario_ids"], ["visible_ap_current_rank_2"])
		self.assertIn("product_rank_2_after_million_projection", contract["excluded_from_promotion_scenario_ids"])
		self.assertIn("product_rank_2_after_million_projection", contract["retryable_scenario_ids"])
		self.assertEqual(blocked["scenario_status"], SCENARIO_STATUS_BLOCKED)
		self.assertFalse(blocked["promotion_eligible"])
		self.assertIn("browser_timeout", blocked["blocking_reasons"])
		self.assertIn("missing_trace_text", blocked["blocking_reasons"])
		self.assertEqual(blocked["resume_from_checkpoint"], CHECKPOINT_ANSWER_CAPTURED)

	def test_stale_trace_reuse_is_blocked_even_with_answer_and_trace_text(self):
		contract = build_browser_batch_runner_contract(
			["visible_ap_current_rank_2"],
			capture_results=[
				_complete_capture(
					"visible_ap_current_rank_2",
					trace_scenario_id="visible_ar_after_ap_typed_rank_2",
				)
			],
			generated_at="2026-05-14T01:10:00+06:30",
		)
		scenario = contract["scenario_contracts"][0]

		self.assertFalse(contract["release_ready"])
		self.assertFalse(scenario["promotion_eligible"])
		self.assertIn("stale_trace_reused", scenario["blocking_reasons"])
		self.assertEqual(contract["strict_import_expected_scenario_ids"], [])

	def test_unexpected_unknown_capture_is_quarantined_from_promotion(self):
		contract = build_browser_batch_runner_contract(
			["visible_ap_current_rank_2"],
			capture_results=[
				_complete_capture("visible_ap_current_rank_2"),
				_complete_capture("future_tax_scenario"),
			],
			generated_at="2026-05-14T01:10:00+06:30",
		)
		scenarios = {entry["scenario_id"]: entry for entry in contract["scenario_contracts"]}
		unknown = scenarios["future_tax_scenario"]

		self.assertFalse(contract["release_ready"])
		self.assertIn("future_tax_scenario", contract["blocked_scenario_ids"])
		self.assertIn("unexpected_scenario_capture", unknown["blocking_reasons"])
		self.assertIn("scenario_not_registered", unknown["blocking_reasons"])
		self.assertEqual(contract["strict_import_expected_scenario_ids"], ["visible_ap_current_rank_2"])

	def test_duplicate_capture_result_blocks_batch_and_excludes_duplicate_from_promotion(self):
		contract = build_browser_batch_runner_contract(
			["visible_ap_current_rank_2"],
			capture_results=[
				_complete_capture("visible_ap_current_rank_2"),
				_complete_capture("visible_ap_current_rank_2"),
			],
			generated_at="2026-05-14T01:10:00+06:30",
		)
		duplicate_rows = [
			entry
			for entry in contract["scenario_contracts"]
			if "duplicate_capture_result" in entry["blocking_reasons"]
		]

		self.assertFalse(contract["release_ready"])
		self.assertEqual(contract["strict_import_expected_scenario_ids"], ["visible_ap_current_rank_2"])
		self.assertEqual(len(duplicate_rows), 1)
		self.assertIn("visible_ap_current_rank_2", contract["blocked_scenario_ids"])
		self.assertIn("duplicate_capture_result", contract["failure_reason_codes"])

	def test_malformed_retry_values_are_blocked_without_throwing(self):
		capture = _complete_capture("visible_ap_current_rank_2")
		capture["retry_count"] = "not-a-number"
		capture["max_retries"] = "also-bad"

		contract = build_browser_batch_runner_contract(
			["visible_ap_current_rank_2"],
			capture_results=[capture],
			generated_at="2026-05-14T01:10:00+06:30",
		)
		scenario = contract["scenario_contracts"][0]

		self.assertFalse(contract["release_ready"])
		self.assertIn("retry_value_invalid", scenario["blocking_reasons"])
		self.assertEqual(scenario["retry_count"], 0)
		self.assertEqual(scenario["max_retries"], 1)

	def test_cleanup_not_confirmed_blocks_promotion(self):
		contract = build_browser_batch_runner_contract(
			["visible_ap_current_rank_2"],
			capture_results=[_complete_capture("visible_ap_current_rank_2", cleanup_state="pending")],
			generated_at="2026-05-14T01:10:00+06:30",
		)
		scenario = contract["scenario_contracts"][0]

		self.assertFalse(contract["release_ready"])
		self.assertIn("cleanup_not_confirmed", scenario["blocking_reasons"])
		self.assertEqual(scenario["resume_from_checkpoint"], CHECKPOINT_TRACE_CAPTURED)

	def test_missing_capture_result_gets_checkpointed_not_promoted(self):
		contract = build_browser_batch_runner_contract(
			["visible_ap_current_rank_2"],
			capture_results=[],
			generated_at="2026-05-14T01:10:00+06:30",
		)
		scenario = contract["scenario_contracts"][0]

		self.assertFalse(contract["release_ready"])
		self.assertIn("capture_result_missing", scenario["blocking_reasons"])
		self.assertIn("missing_answer_text", scenario["blocking_reasons"])
		self.assertIn("missing_trace_text", scenario["blocking_reasons"])
		self.assertEqual(scenario["resume_from_checkpoint"], "queued")
		self.assertEqual(contract["strict_import_command"], "not_available_no_promotion_eligible_scenarios")

	def test_contract_exposes_required_reason_codes_checkpoints_and_forbidden_actions(self):
		contract = build_browser_batch_runner_contract(
			["visible_ap_current_rank_2"],
			capture_results=[_complete_capture("visible_ap_current_rank_2")],
			generated_at="2026-05-14T01:10:00+06:30",
		)

		self.assertEqual(contract["required_reason_codes"], REQUIRED_BROWSER_BATCH_REASON_CODES)
		self.assertEqual(contract["supported_reason_codes"], REQUIRED_BROWSER_BATCH_REASON_CODES)
		self.assertEqual(contract["missing_reason_codes"], [])
		self.assertEqual(contract["required_checkpoint_states"], REQUIRED_CHECKPOINT_STATES)
		self.assertEqual(contract["forbidden_actions"], FORBIDDEN_BROWSER_BATCH_ACTIONS)
		self.assertIn("browser_timeout", contract["required_reason_codes"])
		self.assertIn("stale_trace_reused", contract["required_reason_codes"])
		self.assertIn("Do not reuse a trace", "\n".join(contract["forbidden_actions"]))

	def test_markdown_renders_runner_status_scenarios_reason_codes_and_cli_command(self):
		contract = build_browser_batch_runner_contract(
			["visible_ap_current_rank_2", "product_rank_2_after_million_projection"],
			capture_results=[
				_complete_capture("visible_ap_current_rank_2"),
				_timeout_capture("product_rank_2_after_million_projection"),
			],
			generated_at="2026-05-14T01:10:00+06:30",
			capture_bundle_path="generated/s7_6t/captures.json",
			out_dir="generated/s7_6t",
		)
		markdown = render_browser_batch_runner_markdown(contract)

		self.assertIn("# S7 Browser Batch Resilience Runner Contract", markdown)
		self.assertIn("product_rank_2_after_million_projection", markdown)
		self.assertIn("browser_timeout", markdown)
		self.assertIn("Excluded from promotion", markdown)
		self.assertIn("scripts/qwen_manual_uat_operator_evidence_import.py", markdown)
		self.assertIn("visible_ap_current_rank_2", markdown)

	def test_writer_is_deterministic(self):
		with tempfile.TemporaryDirectory() as tmp:
			json_path = Path(tmp) / "runner.json"
			markdown_path = Path(tmp) / "runner.md"

			first = write_browser_batch_runner_files(
				["visible_ap_current_rank_2"],
				capture_results=[_complete_capture("visible_ap_current_rank_2")],
				json_path=str(json_path),
				markdown_path=str(markdown_path),
				generated_at="2026-05-14T01:10:00+06:30",
			)
			first_json = json_path.read_text(encoding="utf-8")
			first_markdown = markdown_path.read_text(encoding="utf-8")
			second = write_browser_batch_runner_files(
				["visible_ap_current_rank_2"],
				capture_results=[_complete_capture("visible_ap_current_rank_2")],
				json_path=str(json_path),
				markdown_path=str(markdown_path),
				generated_at="2026-05-14T01:10:00+06:30",
			)

			self.assertTrue(first["json_artifact_written"])
			self.assertTrue(first["markdown_artifact_written"])
			self.assertTrue(second["json_artifact_written"])
			self.assertEqual(first_json, json_path.read_text(encoding="utf-8"))
			self.assertEqual(first_markdown, markdown_path.read_text(encoding="utf-8"))
			loaded = json.loads(first_json)
			self.assertTrue(loaded["release_ready"])
			self.assertIn("Browser Batch Resilience", first_markdown)

	def test_s7_6t_browser_batch_runner_suite_is_release_blocking(self):
		boundary = build_regression_suite_boundary_contract()
		entries = {entry["suite_id"]: entry for entry in boundary["entries"]}

		self.assertIn(MANUAL_UAT_BROWSER_BATCH_RUNNER_SUITE_ID, RELEASE_BLOCKING_SUITE_IDS)
		self.assertIn(MANUAL_UAT_BROWSER_BATCH_RUNNER_SUITE_ID, entries)
		entry = entries[MANUAL_UAT_BROWSER_BATCH_RUNNER_SUITE_ID]
		self.assertEqual(entry["gate_class"], GATE_RELEASE_BLOCKING_CONTRACT)
		self.assertEqual(entry["runtime_dependency"], RUNTIME_NONE)
		self.assertEqual(entry["blocking_level"], BLOCKING_RELEASE)
		self.assertTrue(entry["release_blocking"])


if __name__ == "__main__":
	unittest.main()
