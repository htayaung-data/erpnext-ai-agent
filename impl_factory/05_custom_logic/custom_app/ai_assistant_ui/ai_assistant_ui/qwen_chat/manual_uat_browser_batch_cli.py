from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, TextIO

from .manual_uat_browser_batch_runner import (
	DEFAULT_BROWSER_BATCH_RUNNER_JSON_PATH,
	DEFAULT_BROWSER_BATCH_RUNNER_MARKDOWN_PATH,
	build_browser_batch_runner_contract,
	render_browser_batch_runner_markdown,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION


MANUAL_UAT_BROWSER_BATCH_CLI_CONTRACT_TYPE = "qwen_manual_uat_browser_batch_cli_contract"
MANUAL_UAT_BROWSER_BATCH_CLI_SUITE_ID = "s7_browser_batch_cli_adapter_contracts"

DEFAULT_BROWSER_BATCH_CLI_OUT_DIR = "impl_factory/00_governance/current_docs/generated"
DEFAULT_BROWSER_BATCH_CLI_REPORT_JSON = "qwen_s7_browser_batch_cli_report.json"
DEFAULT_BROWSER_BATCH_CLI_REPORT_MARKDOWN = "qwen_s7_browser_batch_cli_report.md"
DEFAULT_BROWSER_BATCH_RUNNER_JSON = "qwen_s7_browser_batch_resilience_runner_contract.json"
DEFAULT_BROWSER_BATCH_RUNNER_MARKDOWN = "qwen_s7_browser_batch_resilience_runner_contract.md"

ADAPTER_MODE_CAPTURE_RESULT_IMPORT = "capture_result_import"
ADAPTER_MODE_PLAN_ONLY = "plan_only"

CLI_STATUS_RELEASE_READY = "release_ready"
CLI_STATUS_PLAN_READY = "plan_ready"
CLI_STATUS_BLOCKED = "blocked"


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_records(values: Iterable[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
	return [dict(value) for value in values or [] if isinstance(value, dict)]


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _dedupe(values: Iterable[str]) -> List[str]:
	seen = set()
	out: List[str] = []
	for value in values:
		text = _clean_text(value)
		if text and text not in seen:
			seen.add(text)
			out.append(text)
	return out


def _split_tokens(values: Iterable[str] | None) -> List[str]:
	tokens: List[str] = []
	for value in values or []:
		for part in _clean_text(value).replace("\n", ",").replace(" ", ",").split(","):
			text = _clean_text(part)
			if text:
				tokens.append(text)
	return _dedupe(tokens)


def _read_scenario_file(path: str) -> Dict[str, Any]:
	path_text = _clean_text(path)
	if not path_text:
		return {"scenario_ids": [], "blocking_reasons": []}
	target = Path(path_text)
	if not target.exists():
		return {"scenario_ids": [], "blocking_reasons": ["scenario_file_missing"], "path": path_text}
	text = target.read_text(encoding="utf-8")
	try:
		payload = json.loads(text)
	except json.JSONDecodeError:
		return {"scenario_ids": _split_tokens(text.splitlines()), "blocking_reasons": [], "path": path_text, "payload_shape": "text"}
	if isinstance(payload, list):
		return {"scenario_ids": _split_tokens([str(value) for value in payload]), "blocking_reasons": [], "path": path_text, "payload_shape": "json_list"}
	if isinstance(payload, dict):
		for field in ["scenario_ids", "expected_scenario_ids", "selected_scenario_ids"]:
			if isinstance(payload.get(field), list):
				return {
					"scenario_ids": _split_tokens([str(value) for value in payload.get(field) or []]),
					"blocking_reasons": [],
					"path": path_text,
					"payload_shape": f"json_dict:{field}",
				}
	return {"scenario_ids": [], "blocking_reasons": ["scenario_file_payload_not_supported"], "path": path_text, "payload_shape": type(payload).__name__}


def parse_browser_batch_scenario_ids(values: Iterable[str] | None = None, *, scenario_file: str = "") -> Dict[str, Any]:
	file_result = _read_scenario_file(scenario_file)
	return {
		"scenario_ids": _dedupe(_split_tokens(values) + _clean_list(file_result.get("scenario_ids"))),
		"scenario_file": _clean_text(scenario_file),
		"scenario_file_payload_shape": _clean_text(file_result.get("payload_shape")),
		"blocking_reasons": _clean_list(file_result.get("blocking_reasons")),
	}


def _records_from_payload(payload: Any) -> Dict[str, Any]:
	if isinstance(payload, list):
		records = [dict(value) for value in payload if isinstance(value, dict)]
		return {
			"records": records,
			"payload_shape": "list",
			"blocking_reasons": [] if len(records) == len(payload) else ["capture_result_file_contains_non_object_records"],
		}
	if isinstance(payload, dict):
		for field in ["capture_results", "scenario_results", "browser_capture_results", "records", "source_capture_records"]:
			if isinstance(payload.get(field), list):
				records = [dict(value) for value in payload.get(field) or [] if isinstance(value, dict)]
				return {
					"records": records,
					"payload_shape": f"dict:{field}",
					"blocking_reasons": [] if len(records) == len(payload.get(field) or []) else ["capture_result_file_contains_non_object_records"],
				}
		return {"records": [dict(payload)], "payload_shape": "dict:single_record", "blocking_reasons": []}
	return {"records": [], "payload_shape": type(payload).__name__, "blocking_reasons": ["capture_result_payload_not_supported"]}


def load_browser_capture_results(capture_result_paths: Iterable[str] | None) -> Dict[str, Any]:
	records: List[Dict[str, Any]] = []
	file_evaluations: List[Dict[str, Any]] = []
	clean_paths = [_clean_text(path) for path in capture_result_paths or [] if _clean_text(path)]
	for path_text in clean_paths:
		target = Path(path_text)
		evaluation = {
			"path": path_text,
			"exists": target.exists(),
			"json_loaded": False,
			"payload_shape": "missing",
			"record_count": 0,
			"blocking_reasons": [],
		}
		if not target.exists():
			evaluation["blocking_reasons"] = ["capture_result_file_missing"]
			file_evaluations.append(evaluation)
			continue
		try:
			payload = json.loads(target.read_text(encoding="utf-8"))
		except json.JSONDecodeError:
			evaluation["payload_shape"] = "malformed_json"
			evaluation["blocking_reasons"] = ["capture_result_file_malformed_json"]
			file_evaluations.append(evaluation)
			continue
		payload_result = _records_from_payload(payload)
		loaded_records = _clean_records(payload_result.get("records"))
		records.extend(loaded_records)
		evaluation["json_loaded"] = True
		evaluation["payload_shape"] = _clean_text(payload_result.get("payload_shape"))
		evaluation["record_count"] = len(loaded_records)
		evaluation["blocking_reasons"] = _clean_list(payload_result.get("blocking_reasons"))
		if not loaded_records:
			evaluation["blocking_reasons"] = sorted(set(evaluation["blocking_reasons"] + ["capture_result_file_no_records"]))
		file_evaluations.append(evaluation)
	return {
		"capture_results": records,
		"capture_result_paths": clean_paths,
		"file_evaluations": file_evaluations,
		"file_blocking_reasons": sorted(
			{
				reason
				for evaluation in file_evaluations
				for reason in _clean_list(evaluation.get("blocking_reasons"))
			}
		),
	}


def browser_batch_cli_output_paths(out_dir: str = DEFAULT_BROWSER_BATCH_CLI_OUT_DIR) -> Dict[str, str]:
	target_dir = Path(_clean_text(out_dir) or DEFAULT_BROWSER_BATCH_CLI_OUT_DIR)
	return {
		"cli_report_json": str(target_dir / DEFAULT_BROWSER_BATCH_CLI_REPORT_JSON),
		"cli_report_markdown": str(target_dir / DEFAULT_BROWSER_BATCH_CLI_REPORT_MARKDOWN),
		"runner_json": str(target_dir / DEFAULT_BROWSER_BATCH_RUNNER_JSON),
		"runner_markdown": str(target_dir / DEFAULT_BROWSER_BATCH_RUNNER_MARKDOWN),
	}


def _existing_output_blockers(paths: Dict[str, str], *, overwrite: bool) -> Dict[str, Any]:
	existing_paths = [
		path
		for path in paths.values()
		if _clean_text(path) and Path(path).exists()
	]
	return {
		"existing_output_paths": existing_paths,
		"blocking_reasons": [] if overwrite or not existing_paths else ["output_file_exists_without_overwrite"],
	}


def build_browser_batch_cli_report(
	scenario_ids: Iterable[str] | None = None,
	*,
	scenario_file: str = "",
	capture_result_paths: Iterable[str] | None = None,
	reviewer: str = "",
	generated_at: str = "",
	out_dir: str = DEFAULT_BROWSER_BATCH_CLI_OUT_DIR,
	batch_id: str = "s7_browser_batch_cli_adapter",
	operator_capture_bundle_path: str = "path/to/operator_capture.json",
	max_retries: int = 1,
	plan_only: bool = False,
	overwrite: bool = False,
	command_id: str = "s7_browser_batch_cli_adapter",
) -> Dict[str, Any]:
	generated_at_text = _clean_text(generated_at) or _utc_now()
	output_paths = browser_batch_cli_output_paths(out_dir)
	scenario_result = parse_browser_batch_scenario_ids(scenario_ids, scenario_file=scenario_file)
	selected_ids = _clean_list(scenario_result.get("scenario_ids"))
	load_result = load_browser_capture_results([] if plan_only else capture_result_paths)
	output_result = (
		{"existing_output_paths": [], "blocking_reasons": []}
		if plan_only
		else _existing_output_blockers(output_paths, overwrite=overwrite)
	)
	runner = build_browser_batch_runner_contract(
		selected_ids,
		capture_results=[] if plan_only else _clean_records(load_result.get("capture_results")),
		batch_id=batch_id,
		generated_at=generated_at_text,
		reviewer=reviewer,
		capture_bundle_path=operator_capture_bundle_path,
		out_dir=out_dir,
		max_retries=max_retries,
		contract_owner="s7_browser_batch_cli_adapter_runner",
	)
	release_blocking_reasons = sorted(
		set(_clean_list(scenario_result.get("blocking_reasons")))
		| set(_clean_list(load_result.get("file_blocking_reasons")))
		| set(_clean_list(output_result.get("blocking_reasons")))
	)
	if not selected_ids:
		release_blocking_reasons.append("scenario_ids_missing")
	if not plan_only and not _clean_list(load_result.get("capture_result_paths")):
		release_blocking_reasons.append("capture_result_files_missing")
	if not plan_only and not bool(runner.get("release_ready")):
		release_blocking_reasons.append("runner_not_release_ready")
	release_blocking_reasons = sorted(set(release_blocking_reasons))
	release_ready = bool(not plan_only and bool(runner.get("release_ready")) and not release_blocking_reasons)
	plan_ready = bool(plan_only and selected_ids and not release_blocking_reasons)
	cli_status = CLI_STATUS_RELEASE_READY if release_ready else CLI_STATUS_PLAN_READY if plan_ready else CLI_STATUS_BLOCKED
	return {
		"type": MANUAL_UAT_BROWSER_BATCH_CLI_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": "s7_browser_batch_cli_adapter",
		"command_id": _clean_text(command_id),
		"adapter_mode": ADAPTER_MODE_PLAN_ONLY if plan_only else ADAPTER_MODE_CAPTURE_RESULT_IMPORT,
		"generated_at": generated_at_text,
		"reviewer": _clean_text(reviewer),
		"out_dir": _clean_text(out_dir),
		"batch_id": _clean_text(batch_id),
		"operator_capture_bundle_path": _clean_text(operator_capture_bundle_path),
		"max_retries": int(max_retries),
		"plan_only": bool(plan_only),
		"overwrite": bool(overwrite),
		"scenario_ids": selected_ids,
		"scenario_count": len(selected_ids),
		"scenario_file": _clean_text(scenario_file),
		"capture_result_paths": _clean_list(load_result.get("capture_result_paths")),
		"capture_result_file_count": len(_clean_list(load_result.get("capture_result_paths"))),
		"capture_result_count": len(_clean_records(load_result.get("capture_results"))),
		"file_evaluations": _clean_records(load_result.get("file_evaluations")),
		"output_paths": output_paths,
		"existing_output_paths": _clean_list(output_result.get("existing_output_paths")),
		"runner_contract": runner,
		"promotion_eligible_scenario_ids": _clean_list(runner.get("promotion_eligible_scenario_ids")),
		"blocked_scenario_ids": _clean_list(runner.get("blocked_scenario_ids")),
		"retryable_scenario_ids": _clean_list(runner.get("retryable_scenario_ids")),
		"strict_import_command": _clean_text(runner.get("strict_import_command")),
		"strict_import_command_argv": _clean_list(runner.get("strict_import_command_argv")),
		"strict_import_execution_mode": "exported_argv_not_invoked",
		"release_ready": release_ready,
		"plan_ready": plan_ready,
		"cli_status": cli_status,
		"exit_code": 0 if (release_ready or plan_ready) else 1,
		"release_blocking_reasons": release_blocking_reasons,
		"artifacts_written": False,
	}


def _md_cell(value: Any) -> str:
	if value is None:
		text = ""
	elif isinstance(value, bool):
		text = "True" if value else "False"
	else:
		text = str(value).strip()
	return text.replace("|", "\\|").replace("\n", "<br>")


def _join(values: Any) -> str:
	items = _clean_list(values)
	return ", ".join(items) if items else "none"


def render_browser_batch_cli_report_markdown(report: Dict[str, Any]) -> str:
	contract = _clean_dict(report)
	lines: List[str] = ["# S7 Browser Batch CLI Report", ""]
	lines.extend(["## Command Summary", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"command_id",
		"adapter_mode",
		"generated_at",
		"reviewer",
		"operator_capture_bundle_path",
		"plan_only",
		"overwrite",
		"scenario_count",
		"capture_result_file_count",
		"capture_result_count",
		"cli_status",
		"release_ready",
		"plan_ready",
		"exit_code",
		"artifacts_written",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(contract.get(field))} |")
	lines.extend(["", "## Release Boundary", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Blocking reasons | {_md_cell(_join(contract.get('release_blocking_reasons')))} |")
	lines.append(f"| Promotion eligible scenarios | {_md_cell(_join(contract.get('promotion_eligible_scenario_ids')))} |")
	lines.append(f"| Blocked scenarios | {_md_cell(_join(contract.get('blocked_scenario_ids')))} |")
	lines.append(f"| Retryable scenarios | {_md_cell(_join(contract.get('retryable_scenario_ids')))} |")
	lines.extend(["", "## File Evaluation", ""])
	lines.append("| Path | Exists | Loaded | Shape | Records | Blocking reasons |")
	lines.append("|---|---|---|---|---|---|")
	for entry in contract.get("file_evaluations") or []:
		if not isinstance(entry, dict):
			continue
		lines.append(
			"| "
			+ " | ".join(
				[
					_md_cell(entry.get("path")),
					_md_cell(entry.get("exists")),
					_md_cell(entry.get("json_loaded")),
					_md_cell(entry.get("payload_shape")),
					_md_cell(entry.get("record_count")),
					_md_cell(_join(entry.get("blocking_reasons"))),
				]
			)
			+ " |"
		)
	lines.extend(["", "## Strict Import", ""])
	lines.append(f"- Mode: `{_md_cell(contract.get('strict_import_execution_mode'))}`")
	lines.append(f"- Command: `{_md_cell(contract.get('strict_import_command'))}`")
	lines.append(f"- Argv: `{_md_cell(json.dumps(contract.get('strict_import_command_argv') or []))}`")
	lines.extend(["", "## Artifacts", ""])
	for key, value in _clean_dict(contract.get("output_paths")).items():
		lines.append(f"- {key}: `{value}`")
	return "\n".join(lines).strip() + "\n"


def _write_text(path: str, text: str) -> None:
	target = Path(path)
	if not target.is_absolute():
		target = Path.cwd() / target
	target.parent.mkdir(parents=True, exist_ok=True)
	target.write_text(text, encoding="utf-8")


def _write_json(path: str, payload: Dict[str, Any]) -> None:
	_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_browser_batch_cli_report(
	scenario_ids: Iterable[str] | None = None,
	*,
	scenario_file: str = "",
	capture_result_paths: Iterable[str] | None = None,
	reviewer: str = "",
	generated_at: str = "",
	out_dir: str = DEFAULT_BROWSER_BATCH_CLI_OUT_DIR,
	batch_id: str = "s7_browser_batch_cli_adapter",
	operator_capture_bundle_path: str = "path/to/operator_capture.json",
	max_retries: int = 1,
	plan_only: bool = False,
	overwrite: bool = False,
	command_id: str = "s7_browser_batch_cli_adapter",
) -> Dict[str, Any]:
	report = build_browser_batch_cli_report(
		scenario_ids,
		scenario_file=scenario_file,
		capture_result_paths=capture_result_paths,
		reviewer=reviewer,
		generated_at=generated_at,
		out_dir=out_dir,
		batch_id=batch_id,
		operator_capture_bundle_path=operator_capture_bundle_path,
		max_retries=max_retries,
		plan_only=plan_only,
		overwrite=overwrite,
		command_id=command_id,
	)
	output_paths = _clean_dict(report.get("output_paths"))
	if "output_file_exists_without_overwrite" in _clean_list(report.get("release_blocking_reasons")):
		return report
	_write_json(output_paths["runner_json"], _clean_dict(report.get("runner_contract")))
	_write_text(output_paths["runner_markdown"], render_browser_batch_runner_markdown(_clean_dict(report.get("runner_contract"))))
	report["artifacts_written"] = True
	_write_json(output_paths["cli_report_json"], report)
	_write_text(output_paths["cli_report_markdown"], render_browser_batch_cli_report_markdown(report))
	return report


def _summary_lines(report: Dict[str, Any]) -> List[str]:
	reasons = _clean_list(report.get("release_blocking_reasons"))
	exit_code = int(report["exit_code"]) if report.get("exit_code") is not None else 1
	return [
		"S7-6U Browser Batch CLI Adapter",
		f"Status: {_clean_text(report.get('cli_status'))}",
		f"Release ready: {bool(report.get('release_ready'))}",
		f"Plan ready: {bool(report.get('plan_ready'))}",
		f"Exit code: {exit_code}",
		f"Scenario count: {int(report.get('scenario_count') or 0)}",
		f"Capture result files: {int(report.get('capture_result_file_count') or 0)}",
		f"Capture results: {int(report.get('capture_result_count') or 0)}",
		f"Promotion eligible: {_join(report.get('promotion_eligible_scenario_ids'))}",
		f"Blocked: {_join(report.get('blocked_scenario_ids'))}",
		f"Blocking reasons: {', '.join(reasons[:12]) if reasons else 'none'}",
		f"Report JSON: {_clean_dict(report.get('output_paths')).get('cli_report_json', '')}",
	]


def build_arg_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Build S7-6T browser batch runner artifacts from selected scenarios and browser capture-result JSON files.")
	parser.add_argument("--scenarios", nargs="*", default=None, help="Scenario ids as repeated values, space-separated values, or comma-separated values.")
	parser.add_argument("--scenarios-file", default="", help="Optional JSON/text file containing selected scenario ids.")
	parser.add_argument("--capture-results", nargs="*", default=None, help="One or more JSON files containing browser capture result records.")
	parser.add_argument("--reviewer", default="", help="Reviewer/operator identity for generated artifacts.")
	parser.add_argument("--generated-at", default="", help="Deterministic timestamp override.")
	parser.add_argument("--out-dir", default=DEFAULT_BROWSER_BATCH_CLI_OUT_DIR, help="Output directory for CLI and runner artifacts.")
	parser.add_argument("--batch-id", default="s7_browser_batch_cli_adapter", help="Stable batch id.")
	parser.add_argument("--operator-capture-bundle", default="path/to/operator_capture.json", help="Path to the operator capture bundle that S7-6P should receive for strict import.")
	parser.add_argument("--max-retries", type=int, default=1, help="Maximum browser retry count used by the S7-6T runner contract.")
	parser.add_argument("--plan-only", action="store_true", help="Generate a selected-scenario plan without requiring capture results.")
	parser.add_argument("--overwrite", action="store_true", help="Allow overwriting existing generated artifacts.")
	return parser


def main(argv: Sequence[str] | None = None, *, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
	parser = build_arg_parser()
	args = parser.parse_args(argv)
	out = stdout or sys.stdout
	report = write_browser_batch_cli_report(
		args.scenarios,
		scenario_file=args.scenarios_file,
		capture_result_paths=args.capture_results,
		reviewer=args.reviewer,
		generated_at=args.generated_at,
		out_dir=args.out_dir,
		batch_id=args.batch_id,
		operator_capture_bundle_path=args.operator_capture_bundle,
		max_retries=args.max_retries,
		plan_only=args.plan_only,
		overwrite=args.overwrite,
	)
	out.write("\n".join(_summary_lines(report)) + "\n")
	return int(report["exit_code"]) if report.get("exit_code") is not None else 1
