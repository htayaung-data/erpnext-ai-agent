from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, TextIO

from .manual_uat_real_evidence_intake import (
	build_manual_uat_real_evidence_intake,
	write_manual_uat_real_evidence_intake_files,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION


MANUAL_UAT_OPERATOR_EVIDENCE_CLI_CONTRACT_TYPE = "qwen_manual_uat_operator_evidence_cli_contract"
MANUAL_UAT_OPERATOR_EVIDENCE_CLI_SUITE_ID = "s7_operator_evidence_import_cli_contracts"

DEFAULT_OPERATOR_EVIDENCE_CLI_OUT_DIR = "impl_factory/00_governance/current_docs/generated"
DEFAULT_OPERATOR_EVIDENCE_CLI_REPORT_JSON = "qwen_s7_operator_evidence_import_cli_report.json"
DEFAULT_OPERATOR_EVIDENCE_CLI_REPORT_MARKDOWN = "qwen_s7_operator_evidence_import_cli_report.md"

REAL_EVIDENCE_INTAKE_JSON = "qwen_s7_manual_uat_real_evidence_intake.json"
PROMOTION_READY_BUNDLE_JSON = "qwen_s7_manual_uat_promotion_ready_bundle.json"
PROMOTION_READY_BUNDLE_MARKDOWN = "qwen_s7_manual_uat_promotion_ready_bundle.md"
REAL_EVIDENCE_PROMOTION_JSON = "qwen_s7_manual_uat_real_evidence_promotion_report.json"
REAL_EVIDENCE_PROMOTION_MARKDOWN = "qwen_s7_manual_uat_real_evidence_promotion_report.md"


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _clean_records(values: Iterable[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
	return [dict(value) for value in values or [] if isinstance(value, dict)]


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _dedupe_preserve_order(values: Iterable[str]) -> List[str]:
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
	return _dedupe_preserve_order(tokens)


def _read_expected_scenario_file(path: str) -> Dict[str, Any]:
	path_text = _clean_text(path)
	if not path_text:
		return {"scenario_ids": [], "blocking_reasons": []}
	target = Path(path_text)
	if not target.exists():
		return {
			"scenario_ids": [],
			"blocking_reasons": ["expected_scenarios_file_missing"],
			"path": str(target),
		}
	text = target.read_text(encoding="utf-8")
	try:
		payload = json.loads(text)
	except json.JSONDecodeError:
		return {
			"scenario_ids": _split_tokens(text.splitlines()),
			"blocking_reasons": [],
			"path": str(target),
			"payload_shape": "text",
		}
	if isinstance(payload, list):
		return {
			"scenario_ids": _split_tokens([str(value) for value in payload]),
			"blocking_reasons": [],
			"path": str(target),
			"payload_shape": "json_list",
		}
	if isinstance(payload, dict):
		for field in ["expected_scenario_ids", "scenario_ids", "sample_scenario_ids"]:
			if isinstance(payload.get(field), list):
				return {
					"scenario_ids": _split_tokens([str(value) for value in payload.get(field) or []]),
					"blocking_reasons": [],
					"path": str(target),
					"payload_shape": f"json_dict:{field}",
				}
	return {
		"scenario_ids": [],
		"blocking_reasons": ["expected_scenarios_file_payload_not_supported"],
		"path": str(target),
		"payload_shape": type(payload).__name__,
	}


def parse_expected_scenario_ids(
	values: Iterable[str] | None = None,
	*,
	expected_scenarios_file: str = "",
) -> Dict[str, Any]:
	inline_ids = _split_tokens(values)
	file_result = _read_expected_scenario_file(expected_scenarios_file)
	return {
		"expected_scenario_ids": _dedupe_preserve_order(inline_ids + _clean_list(file_result.get("scenario_ids"))),
		"blocking_reasons": _clean_list(file_result.get("blocking_reasons")),
		"expected_scenarios_file": _clean_text(expected_scenarios_file),
		"expected_scenarios_file_payload_shape": _clean_text(file_result.get("payload_shape")),
	}


def _records_from_payload(payload: Any) -> Dict[str, Any]:
	if isinstance(payload, list):
		records = [dict(value) for value in payload if isinstance(value, dict)]
		return {
			"records": records,
			"payload_shape": "list",
			"blocking_reasons": [] if len(records) == len(payload) else ["capture_file_contains_non_object_records"],
		}
	if isinstance(payload, dict):
		for field in [
			"source_capture_records",
			"sample_capture_records",
			"capture_records",
			"records",
			"import_ready_json_skeletons",
		]:
			if isinstance(payload.get(field), list):
				records = [dict(value) for value in payload.get(field) or [] if isinstance(value, dict)]
				reasons = [] if len(records) == len(payload.get(field) or []) else ["capture_file_contains_non_object_records"]
				return {
					"records": records,
					"payload_shape": f"dict:{field}",
					"blocking_reasons": reasons,
				}
		return {
			"records": [dict(payload)],
			"payload_shape": "dict:single_record",
			"blocking_reasons": [],
		}
	return {
		"records": [],
		"payload_shape": type(payload).__name__,
		"blocking_reasons": ["capture_file_payload_not_supported"],
	}


def load_operator_capture_records(capture_paths: Iterable[str] | None) -> Dict[str, Any]:
	records: List[Dict[str, Any]] = []
	file_evaluations: List[Dict[str, Any]] = []
	for raw_path in capture_paths or []:
		path_text = _clean_text(raw_path)
		target = Path(path_text)
		evaluation = {
			"path": path_text,
			"exists": target.exists(),
			"json_loaded": False,
			"payload_shape": "missing",
			"record_count": 0,
			"blocking_reasons": [],
		}
		if not path_text:
			evaluation["blocking_reasons"] = ["capture_file_path_missing"]
			file_evaluations.append(evaluation)
			continue
		if not target.exists():
			evaluation["blocking_reasons"] = ["capture_file_missing"]
			file_evaluations.append(evaluation)
			continue
		try:
			payload = json.loads(target.read_text(encoding="utf-8"))
		except json.JSONDecodeError:
			evaluation["payload_shape"] = "malformed_json"
			evaluation["blocking_reasons"] = ["capture_file_malformed_json"]
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
			evaluation["blocking_reasons"] = sorted(set(evaluation["blocking_reasons"] + ["capture_file_no_records"]))
		file_evaluations.append(evaluation)
	if not list(capture_paths or []):
		file_evaluations.append(
			{
				"path": "",
				"exists": False,
				"json_loaded": False,
				"payload_shape": "none",
				"record_count": 0,
				"blocking_reasons": ["capture_files_missing"],
			}
		)
	return {
		"capture_records": records,
		"file_evaluations": file_evaluations,
		"file_blocking_reasons": sorted(
			{
				reason
				for evaluation in file_evaluations
				for reason in _clean_list(evaluation.get("blocking_reasons"))
			}
		),
	}


def _scenario_ids_from_records(records: Iterable[Dict[str, Any]]) -> List[str]:
	return _dedupe_preserve_order([_clean_text(record.get("scenario_id")) for record in records if _clean_text(record.get("scenario_id"))])


def _strict_blocking_reasons(
	*,
	strict: bool,
	expected_scenario_ids: List[str],
	capture_records: List[Dict[str, Any]],
) -> List[str]:
	if not strict:
		return []
	reasons: List[str] = []
	record_ids = _scenario_ids_from_records(capture_records)
	if not expected_scenario_ids:
		reasons.append("strict_expected_scenarios_missing")
	if sorted(record_ids) != sorted(expected_scenario_ids):
		reasons.append("strict_expected_scenarios_mismatch")
	return sorted(set(reasons))


def operator_evidence_output_paths(out_dir: str = DEFAULT_OPERATOR_EVIDENCE_CLI_OUT_DIR) -> Dict[str, str]:
	target_dir = Path(_clean_text(out_dir) or DEFAULT_OPERATOR_EVIDENCE_CLI_OUT_DIR)
	return {
		"cli_report_json": str(target_dir / DEFAULT_OPERATOR_EVIDENCE_CLI_REPORT_JSON),
		"cli_report_markdown": str(target_dir / DEFAULT_OPERATOR_EVIDENCE_CLI_REPORT_MARKDOWN),
		"intake_json": str(target_dir / REAL_EVIDENCE_INTAKE_JSON),
		"bundle_json": str(target_dir / PROMOTION_READY_BUNDLE_JSON),
		"bundle_markdown": str(target_dir / PROMOTION_READY_BUNDLE_MARKDOWN),
		"promotion_json": str(target_dir / REAL_EVIDENCE_PROMOTION_JSON),
		"promotion_markdown": str(target_dir / REAL_EVIDENCE_PROMOTION_MARKDOWN),
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


def build_operator_evidence_cli_report(
	capture_paths: Iterable[str] | None = None,
	*,
	expected_scenario_ids: Iterable[str] | None = None,
	expected_scenarios_file: str = "",
	reviewer: str = "",
	generated_at: str = "",
	out_dir: str = DEFAULT_OPERATOR_EVIDENCE_CLI_OUT_DIR,
	intake_id: str = "s7_operator_evidence_import_cli",
	strict: bool = False,
	overwrite: bool = False,
	command_id: str = "s7_operator_evidence_import_cli",
) -> Dict[str, Any]:
	generated_at_text = _clean_text(generated_at) or _utc_now()
	clean_capture_paths = [_clean_text(path) for path in capture_paths or [] if _clean_text(path)]
	expected_result = parse_expected_scenario_ids(
		expected_scenario_ids,
		expected_scenarios_file=expected_scenarios_file,
	)
	expected_ids = _clean_list(expected_result.get("expected_scenario_ids"))
	load_result = load_operator_capture_records(clean_capture_paths)
	records = _clean_records(load_result.get("capture_records"))
	output_paths = operator_evidence_output_paths(out_dir)
	output_result = _existing_output_blockers(output_paths, overwrite=overwrite)
	strict_reasons = _strict_blocking_reasons(
		strict=strict,
		expected_scenario_ids=expected_ids,
		capture_records=records,
	)
	intake = build_manual_uat_real_evidence_intake(
		records,
		expected_scenario_ids=expected_ids if expected_ids else None,
		intake_id=intake_id,
		generated_at=generated_at_text,
		reviewer=reviewer,
		intake_json_artifact_path=output_paths["intake_json"],
		bundle_json_artifact_path=output_paths["bundle_json"],
		bundle_markdown_artifact_path=output_paths["bundle_markdown"],
		promotion_json_artifact_path=output_paths["promotion_json"],
		promotion_markdown_artifact_path=output_paths["promotion_markdown"],
		contract_owner="s7_operator_evidence_import_cli_intake",
	)
	release_blocking_reasons = sorted(
		set(_clean_list(expected_result.get("blocking_reasons")))
		| set(_clean_list(load_result.get("file_blocking_reasons")))
		| set(_clean_list(output_result.get("blocking_reasons")))
		| set(strict_reasons)
		| set(_clean_list(intake.get("release_blocking_reasons")))
	)
	release_ready = bool(intake.get("release_ready") and not release_blocking_reasons)
	return {
		"type": MANUAL_UAT_OPERATOR_EVIDENCE_CLI_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": "s7_operator_evidence_import_cli",
		"command_id": _clean_text(command_id),
		"generated_at": generated_at_text,
		"reviewer": _clean_text(reviewer),
		"strict": bool(strict),
		"overwrite": bool(overwrite),
		"capture_file_paths": clean_capture_paths,
		"capture_file_count": len(clean_capture_paths),
		"file_evaluations": _clean_records(load_result.get("file_evaluations")),
		"expected_scenario_ids": expected_ids,
		"expected_scenario_count": len(expected_ids),
		"expected_scenarios_file": _clean_text(expected_scenarios_file),
		"capture_record_count": len(records),
		"output_paths": output_paths,
		"existing_output_paths": _clean_list(output_result.get("existing_output_paths")),
		"intake_contract": intake,
		"intake_release_ready": bool(intake.get("release_ready")),
		"release_ready": release_ready,
		"exit_code": 0 if release_ready else 1,
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


def render_operator_evidence_cli_report_markdown(report: Dict[str, Any]) -> str:
	contract = dict(report or {})
	intake = _clean_dict(contract.get("intake_contract"))
	lines: List[str] = ["# S7 Operator Evidence Import CLI Report", ""]
	lines.append("## Command Summary")
	lines.append("")
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"command_id",
		"generated_at",
		"reviewer",
		"strict",
		"overwrite",
		"capture_file_count",
		"capture_record_count",
		"expected_scenario_count",
		"intake_release_ready",
		"release_ready",
		"exit_code",
		"artifacts_written",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(contract.get(field))} |")
	lines.extend(["", "## Release Boundary", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Blocking reasons | {_md_cell(_join(contract.get('release_blocking_reasons')))} |")
	lines.append(f"| Existing output paths | {_md_cell(_join(contract.get('existing_output_paths')))} |")
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
	lines.extend(["", "## Composed Intake", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Intake complete | {_md_cell(intake.get('intake_complete'))} |")
	lines.append(f"| Promotion ready | {_md_cell(intake.get('promotion_ready'))} |")
	lines.append(f"| Release ready | {_md_cell(intake.get('release_ready'))} |")
	lines.append(f"| Blocking reasons | {_md_cell(_join(intake.get('release_blocking_reasons')))} |")
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


def write_operator_evidence_cli_report(
	capture_paths: Iterable[str] | None = None,
	*,
	expected_scenario_ids: Iterable[str] | None = None,
	expected_scenarios_file: str = "",
	reviewer: str = "",
	generated_at: str = "",
	out_dir: str = DEFAULT_OPERATOR_EVIDENCE_CLI_OUT_DIR,
	intake_id: str = "s7_operator_evidence_import_cli",
	strict: bool = False,
	overwrite: bool = False,
	command_id: str = "s7_operator_evidence_import_cli",
) -> Dict[str, Any]:
	report = build_operator_evidence_cli_report(
		capture_paths,
		expected_scenario_ids=expected_scenario_ids,
		expected_scenarios_file=expected_scenarios_file,
		reviewer=reviewer,
		generated_at=generated_at,
		out_dir=out_dir,
		intake_id=intake_id,
		strict=strict,
		overwrite=overwrite,
		command_id=command_id,
	)
	output_paths = _clean_dict(report.get("output_paths"))
	if "output_file_exists_without_overwrite" in _clean_list(report.get("release_blocking_reasons")):
		return report
	written_intake = write_manual_uat_real_evidence_intake_files(
		_clean_records(report.get("intake_contract", {}).get("source_capture_records")),
		intake_json_path=output_paths.get("intake_json") or "",
		bundle_json_path=output_paths.get("bundle_json") or "",
		bundle_markdown_path=output_paths.get("bundle_markdown") or "",
		promotion_json_path=output_paths.get("promotion_json") or "",
		promotion_markdown_path=output_paths.get("promotion_markdown") or "",
		expected_scenario_ids=_clean_list(report.get("expected_scenario_ids")) or None,
		intake_id=intake_id,
		generated_at=report.get("generated_at") or "",
		reviewer=reviewer,
	)
	report["intake_contract"] = written_intake
	report["artifacts_written"] = True
	_write_json(output_paths["cli_report_json"], report)
	_write_text(output_paths["cli_report_markdown"], render_operator_evidence_cli_report_markdown(report))
	return report


def _summary_lines(report: Dict[str, Any]) -> List[str]:
	reasons = _clean_list(report.get("release_blocking_reasons"))
	exit_code = int(report["exit_code"]) if report.get("exit_code") is not None else 1
	return [
		"S7-6P Operator Evidence Import CLI",
		f"Release ready: {bool(report.get('release_ready'))}",
		f"Exit code: {exit_code}",
		f"Capture files: {int(report.get('capture_file_count') or 0)}",
		f"Capture records: {int(report.get('capture_record_count') or 0)}",
		f"Blocking reasons: {', '.join(reasons[:12]) if reasons else 'none'}",
		f"Report JSON: {_clean_dict(report.get('output_paths')).get('cli_report_json', '')}",
	]


def build_arg_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Import operator-captured S7 manual UAT evidence through the governed S7-6O intake contract.")
	parser.add_argument("--captures", nargs="+", required=True, help="One or more JSON files containing operator capture records.")
	parser.add_argument("--expected-scenarios", nargs="*", default=None, help="Expected scenario ids as repeated values, space-separated values, or comma-separated values.")
	parser.add_argument("--expected-scenarios-file", default="", help="Optional JSON/text file containing expected scenario ids.")
	parser.add_argument("--reviewer", default="", help="Reviewer/operator identity for the intake report.")
	parser.add_argument("--generated-at", default="", help="Deterministic timestamp override for generated artifacts.")
	parser.add_argument("--out-dir", default=DEFAULT_OPERATOR_EVIDENCE_CLI_OUT_DIR, help="Output directory for CLI, intake, bundle, and promotion artifacts.")
	parser.add_argument("--intake-id", default="s7_operator_evidence_import_cli", help="Stable intake id for generated contracts.")
	parser.add_argument("--strict", action="store_true", help="Require expected scenarios to exactly match capture record scenario ids.")
	parser.add_argument("--overwrite", action="store_true", help="Allow overwriting existing generated artifacts.")
	return parser


def main(argv: Sequence[str] | None = None, *, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
	parser = build_arg_parser()
	args = parser.parse_args(list(argv) if argv is not None else None)
	report = write_operator_evidence_cli_report(
		args.captures,
		expected_scenario_ids=args.expected_scenarios,
		expected_scenarios_file=args.expected_scenarios_file,
		reviewer=args.reviewer,
		generated_at=args.generated_at,
		out_dir=args.out_dir,
		intake_id=args.intake_id,
		strict=args.strict,
		overwrite=args.overwrite,
	)
	stream = stdout or sys.stdout
	stream.write("\n".join(_summary_lines(report)) + "\n")
	return int(report["exit_code"]) if report.get("exit_code") is not None else 1


if __name__ == "__main__":
	raise SystemExit(main())
