from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List

from .manual_uat_operator_evidence_cli import (
	DEFAULT_OPERATOR_EVIDENCE_CLI_OUT_DIR,
	DEFAULT_OPERATOR_EVIDENCE_CLI_REPORT_JSON,
	DEFAULT_OPERATOR_EVIDENCE_CLI_REPORT_MARKDOWN,
	PROMOTION_READY_BUNDLE_JSON,
	PROMOTION_READY_BUNDLE_MARKDOWN,
	REAL_EVIDENCE_INTAKE_JSON,
	REAL_EVIDENCE_PROMOTION_JSON,
	REAL_EVIDENCE_PROMOTION_MARKDOWN,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION


MANUAL_UAT_OPERATOR_RUNBOOK_CONTRACT_TYPE = "qwen_manual_uat_operator_runbook_contract"
MANUAL_UAT_OPERATOR_RUNBOOK_SUITE_ID = "s7_operator_evidence_bundle_uat_runbook_contracts"

DEFAULT_OPERATOR_RUNBOOK_JSON_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_operator_evidence_bundle_uat_runbook.json"
)
DEFAULT_OPERATOR_RUNBOOK_MARKDOWN_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_operator_evidence_bundle_uat_runbook.md"
)

REQUIRED_RUNBOOK_SECTIONS = [
	"purpose_and_scope",
	"authority_stack",
	"operator_prerequisites",
	"scenario_pack_preparation",
	"browser_capture_steps",
	"json_capture_completion",
	"promotion_field_preflight",
	"cli_execution",
	"report_interpretation",
	"blocker_resolution",
	"retry_and_overwrite",
	"archive_and_signoff",
	"forbidden_actions",
	"sample_vs_real_boundary",
	"manual_escalation",
]

REQUIRED_CONTRACT_REFERENCES = [
	"qwen_regression_scenario_pack_contract",
	"qwen_manual_browser_uat_pack",
	"qwen_manual_uat_capture_template_pack_contract",
	"qwen_manual_uat_real_evidence_intake_contract",
	"qwen_manual_uat_operator_evidence_cli_contract",
	"qwen_manual_uat_evidence_promotion_contract",
	"qwen_regression_suite_boundary_contract",
]

REQUIRED_BLOCKER_KEYS = [
	"capture_file_missing",
	"capture_file_malformed_json",
	"capture_file_payload_not_supported",
	"output_file_exists_without_overwrite",
	"strict_expected_scenarios_mismatch",
	"operator_attestation_missing",
	"sample_evidence_not_allowed",
	"quarantined_import_records",
	"blocked_import_records",
	"archive_blocking_failures",
	"missing_archive_evidence",
	"promotion_not_release_ready",
]


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _generated_path(filename: str) -> str:
	return str(Path(DEFAULT_OPERATOR_EVIDENCE_CLI_OUT_DIR) / filename)


def _artifact_paths() -> Dict[str, str]:
	return {
		"operator_capture_template_markdown": "impl_factory/00_governance/current_docs/generated/qwen_s7_manual_uat_operator_capture_template.md",
		"operator_capture_skeleton_json": "impl_factory/00_governance/current_docs/generated/qwen_s7_manual_uat_operator_capture_skeleton.json",
		"manual_browser_uat_pack_markdown": "impl_factory/00_governance/current_docs/generated/qwen_s7_manual_browser_uat_pack.md",
		"operator_cli_report_json": _generated_path(DEFAULT_OPERATOR_EVIDENCE_CLI_REPORT_JSON),
		"operator_cli_report_markdown": _generated_path(DEFAULT_OPERATOR_EVIDENCE_CLI_REPORT_MARKDOWN),
		"real_evidence_intake_json": _generated_path(REAL_EVIDENCE_INTAKE_JSON),
		"promotion_ready_bundle_json": _generated_path(PROMOTION_READY_BUNDLE_JSON),
		"promotion_ready_bundle_markdown": _generated_path(PROMOTION_READY_BUNDLE_MARKDOWN),
		"real_evidence_promotion_json": _generated_path(REAL_EVIDENCE_PROMOTION_JSON),
		"real_evidence_promotion_markdown": _generated_path(REAL_EVIDENCE_PROMOTION_MARKDOWN),
	}


def _command_examples() -> List[Dict[str, str]]:
	return [
		{
			"name": "strict_real_evidence_import",
			"purpose": "Import one or more real operator capture files and fail if expected scenarios do not exactly match.",
			"command": (
				"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
				"python3 scripts/qwen_manual_uat_operator_evidence_import.py "
				"--captures path/to/operator_capture.json "
				"--expected-scenarios visible_ar_after_ap_typed_rank_2,visible_ap_current_rank_2 "
				"--reviewer uat@example.com --strict --overwrite"
			),
		},
		{
			"name": "expected_scenarios_file_import",
			"purpose": "Use a governed expected-scenario file instead of inline ids.",
			"command": (
				"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
				"python3 scripts/qwen_manual_uat_operator_evidence_import.py "
				"--captures path/to/operator_capture.json "
				"--expected-scenarios-file path/to/expected_scenarios.json "
				"--reviewer uat@example.com --strict --overwrite"
			),
		},
		{
			"name": "dry_summary_block_check",
			"purpose": "Run without overwrite first when preserving prior generated artifacts is required.",
			"command": (
				"PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui "
				"python3 scripts/qwen_manual_uat_operator_evidence_import.py "
				"--captures path/to/operator_capture.json --reviewer uat@example.com --strict"
			),
		},
	]


def _blocker_catalog() -> List[Dict[str, str]]:
	return [
		{"key": "capture_file_missing", "meaning": "The supplied capture path does not exist.", "operator_action": "Verify the path and rerun the CLI."},
		{"key": "capture_file_malformed_json", "meaning": "The capture file is not valid JSON.", "operator_action": "Fix JSON syntax using the operator skeleton, then rerun."},
		{"key": "capture_file_payload_not_supported", "meaning": "The JSON shape is not a record, record list, or supported bundle field.", "operator_action": "Use the S7-6N skeleton format or a list of those records."},
		{"key": "output_file_exists_without_overwrite", "meaning": "Generated artifacts already exist and overwrite was not allowed.", "operator_action": "Review existing artifacts, then rerun with --overwrite if replacement is intentional."},
		{"key": "strict_expected_scenarios_mismatch", "meaning": "Strict mode found expected scenario ids do not exactly match capture record ids.", "operator_action": "Correct the expected scenario list or capture the missing scenario evidence."},
		{"key": "operator_attestation_missing", "meaning": "At least one record lacks operator attestation.", "operator_action": "Fill operator_attestation after verifying the evidence was captured from real browser UAT."},
		{"key": "sample_evidence_not_allowed", "meaning": "A record is marked as sample or dry-run evidence.", "operator_action": "Do not promote sample records; rerun with real operator-captured records."},
		{"key": "quarantined_import_records", "meaning": "A scenario is unknown or trace evidence cannot be trusted.", "operator_action": "Use a registered scenario id and paste the complete context authority trace."},
		{"key": "blocked_import_records", "meaning": "A registered record is missing required answer, trace, or model-role fields.", "operator_action": "Repair the captured answer/trace fields and rerun."},
		{"key": "archive_blocking_failures", "meaning": "A captured scenario failed UAT or archive validation.", "operator_action": "Treat this as a real product defect or recapture only after the issue is fixed."},
		{"key": "missing_archive_evidence", "meaning": "Expected scenario evidence is missing from the archive bundle.", "operator_action": "Capture and import the missing scenario evidence."},
		{"key": "promotion_not_release_ready", "meaning": "The promotion boundary did not approve the composed evidence bundle.", "operator_action": "Resolve the listed S7-6O/S7-6M blockers before release signoff."},
	]


def _forbidden_actions() -> List[str]:
	return [
		"Do not edit generated CLI, intake, bundle, or promotion artifacts by hand.",
		"Do not use sample_fixture or dry_run_only records for production promotion.",
		"Do not remove blocker keys from JSON to force release readiness.",
		"Do not approve screenshots without raw answer text and context authority trace evidence.",
		"Do not bypass S7-6P by importing evidence directly into generated folders.",
		"Do not set operator_attestation before personally verifying the browser evidence.",
	]


def _runbook_sections() -> List[Dict[str, Any]]:
	return [
		{
			"id": "purpose_and_scope",
			"title": "Purpose And Scope",
			"steps": [
				"Use this runbook only for S7 manual browser UAT evidence capture and promotion readiness.",
				"The runbook governs the operator workflow; S7-6O and S7-6P remain the execution authority.",
			],
		},
		{
			"id": "authority_stack",
			"title": "Authority Stack",
			"steps": [
				"Read the scenario pack and manual browser UAT pack before running browser tests.",
				"Use S7-6N skeletons for capture records.",
				"Use S7-6P CLI for import; it composes S7-6O, S7-6K, and S7-6M.",
			],
		},
		{
			"id": "operator_prerequisites",
			"title": "Operator Prerequisites",
			"steps": [
				"Confirm the local or browser UAT environment is the intended test target.",
				"Confirm the reviewer identity that will appear in every record.",
				"Confirm generated artifacts may be overwritten before using --overwrite.",
			],
		},
		{
			"id": "scenario_pack_preparation",
			"title": "Scenario Pack Preparation",
			"steps": [
				"Select scenario ids from the governed S7-6B scenario pack.",
				"Create an expected scenario id list for strict CLI mode.",
				"Do not add new scenario ids ad hoc during evidence import.",
			],
		},
		{
			"id": "browser_capture_steps",
			"title": "Browser Capture Steps",
			"steps": [
				"Run each scenario prompt sequence exactly as written.",
				"Capture the user-visible answer text.",
				"Run Show latest context authority trace after the scenario requires trace evidence.",
				"Capture the full trace sections including final answer authority and model-role sections.",
			],
		},
		{
			"id": "json_capture_completion",
			"title": "JSON Capture Completion",
			"steps": [
				"Start from qwen_s7_manual_uat_operator_capture_skeleton.json.",
				"Fill raw_answer_text, raw_trace_text, observed_answer_summary, reviewer, captured_at, and uat_status.",
				"Keep scenario_id aligned to the governed scenario pack.",
			],
		},
		{
			"id": "promotion_field_preflight",
			"title": "Promotion Field Preflight",
			"steps": [
				"evidence_mode must be operator_captured.",
				"capture_source must be manual_browser_uat.",
				"release_boundary must be none.",
				"dry_run_only must be False.",
				"promotion_intent must be production_manual_uat.",
				"operator_attestation must be filled only after real browser evidence is verified.",
			],
		},
		{
			"id": "cli_execution",
			"title": "CLI Execution",
			"steps": [
				"Run scripts/qwen_manual_uat_operator_evidence_import.py with --captures and --reviewer.",
				"Use --strict with expected scenarios for release promotion review.",
				"Use --overwrite only after reviewing prior generated artifacts.",
			],
		},
		{
			"id": "report_interpretation",
			"title": "Report Interpretation",
			"steps": [
				"CLI exit code 0 means the CLI layer and S7-6O promotion path are release-ready.",
				"CLI exit code 1 means at least one file, strict-mode, intake, bundle, archive, or promotion blocker remains.",
				"Inspect qwen_s7_operator_evidence_import_cli_report.md first, then intake, bundle, and promotion reports.",
			],
		},
		{
			"id": "blocker_resolution",
			"title": "Blocker Resolution",
			"steps": [
				"Resolve blocker keys from the blocker catalog; do not delete them manually.",
				"Recapture browser evidence when trace or answer evidence is incomplete.",
				"Escalate real product failures instead of converting them into pass records.",
			],
		},
		{
			"id": "retry_and_overwrite",
			"title": "Retry And Overwrite",
			"steps": [
				"Keep failed CLI reports for audit when diagnosing defects.",
				"Use --overwrite only for an intentional replacement after evidence has been corrected.",
				"Do not mix old generated artifacts with newly captured JSON files.",
			],
		},
		{
			"id": "archive_and_signoff",
			"title": "Archive And Signoff",
			"steps": [
				"Store the final capture JSON alongside CLI, intake, bundle, and promotion artifacts.",
				"Release signoff requires release_ready=True and exit_code=0 in the CLI report.",
				"Reviewer signoff must include the operator attestation trail.",
			],
		},
		{
			"id": "forbidden_actions",
			"title": "Forbidden Actions",
			"steps": _forbidden_actions(),
		},
		{
			"id": "sample_vs_real_boundary",
			"title": "Sample Vs Real Boundary",
			"steps": [
				"Sample fixture artifacts are useful for dry-run mechanics only.",
				"Any sample_fixture, sample_fixture_dry_run, dry_run_only=True, or not_production_uat_evidence marker blocks production promotion.",
				"Real evidence requires operator_captured, manual_browser_uat, release_boundary=none, and operator attestation.",
			],
		},
		{
			"id": "manual_escalation",
			"title": "Manual Escalation",
			"steps": [
				"Escalate unsupported blocker meanings to the S7 owner before signoff.",
				"Escalate scenario coverage gaps instead of editing generated evidence.",
				"Escalate business behavior defects with the exact scenario id and raw evidence hash.",
			],
		},
	]


def _missing_sections(sections: List[Dict[str, Any]]) -> List[str]:
	section_ids = {_clean_text(section.get("id")) for section in sections}
	return [section_id for section_id in REQUIRED_RUNBOOK_SECTIONS if section_id not in section_ids]


def build_operator_evidence_runbook_contract(
	*,
	generated_at: str = "",
	json_artifact_path: str = DEFAULT_OPERATOR_RUNBOOK_JSON_PATH,
	markdown_artifact_path: str = DEFAULT_OPERATOR_RUNBOOK_MARKDOWN_PATH,
	contract_owner: str = "s7_operator_evidence_bundle_uat_runbook",
) -> Dict[str, Any]:
	sections = _runbook_sections()
	blocker_catalog = _blocker_catalog()
	artifact_paths = _artifact_paths()
	command_examples = _command_examples()
	missing_sections = _missing_sections(sections)
	missing_blockers = [
		key
		for key in REQUIRED_BLOCKER_KEYS
		if key not in {_clean_text(entry.get("key")) for entry in blocker_catalog}
	]
	return {
		"type": MANUAL_UAT_OPERATOR_RUNBOOK_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"generated_at": _clean_text(generated_at) or _utc_now(),
		"json_artifact_path": _clean_text(json_artifact_path),
		"markdown_artifact_path": _clean_text(markdown_artifact_path),
		"json_artifact_written": False,
		"markdown_artifact_written": False,
		"required_sections": list(REQUIRED_RUNBOOK_SECTIONS),
		"sections": sections,
		"missing_sections": missing_sections,
		"contract_references": list(REQUIRED_CONTRACT_REFERENCES),
		"artifact_paths": artifact_paths,
		"command_examples": command_examples,
		"blocker_catalog": blocker_catalog,
		"required_blocker_keys": list(REQUIRED_BLOCKER_KEYS),
		"missing_blocker_keys": missing_blockers,
		"forbidden_actions": _forbidden_actions(),
		"pass_criteria": [
			"Every selected scenario has real operator-captured evidence.",
			"S7-6P CLI report has release_ready=True.",
			"S7-6P CLI report has exit_code=0.",
			"S7-6O intake, bundle, and promotion artifacts are release-ready.",
			"No sample, unsafe, quarantined, blocked, missing, duplicate, or archive-failed evidence remains.",
		],
		"runbook_complete": bool(not missing_sections and not missing_blockers and command_examples and artifact_paths),
	}


def _md_cell(value: Any) -> str:
	if value is None:
		text = ""
	elif isinstance(value, bool):
		text = "True" if value else "False"
	else:
		text = str(value).strip()
	return text.replace("|", "\\|").replace("\n", "<br>")


def render_operator_evidence_runbook_markdown(contract: Dict[str, Any]) -> str:
	runbook = dict(contract or {})
	lines: List[str] = ["# S7 Operator Evidence Bundle UAT Execution Runbook", ""]
	lines.append("## Runbook Metadata")
	lines.append("")
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"generated_at",
		"runbook_complete",
		"json_artifact_path",
		"markdown_artifact_path",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(runbook.get(field))} |")
	lines.append("")
	lines.append("## Contract Authority")
	lines.append("")
	for reference in _clean_list(runbook.get("contract_references")):
		lines.append(f"- {reference}")
	lines.append("")
	lines.append("## Artifact Paths")
	lines.append("")
	for key, value in dict(runbook.get("artifact_paths") or {}).items():
		lines.append(f"- {key}: `{value}`")
	lines.append("")
	lines.append("## Command Examples")
	lines.append("")
	for example in runbook.get("command_examples") or []:
		if not isinstance(example, dict):
			continue
		lines.append(f"### {_clean_text(example.get('name'))}")
		lines.append("")
		lines.append(_clean_text(example.get("purpose")))
		lines.append("")
		lines.append("```bash")
		lines.append(_clean_text(example.get("command")))
		lines.append("```")
		lines.append("")
	for section in runbook.get("sections") or []:
		if not isinstance(section, dict):
			continue
		lines.append(f"## {_clean_text(section.get('title'))}")
		lines.append("")
		for step in _clean_list(section.get("steps")):
			lines.append(f"- {step}")
		lines.append("")
	lines.append("## Blocker Catalog")
	lines.append("")
	lines.append("| Blocker | Meaning | Operator action |")
	lines.append("|---|---|---|")
	for entry in runbook.get("blocker_catalog") or []:
		if not isinstance(entry, dict):
			continue
		lines.append(
			f"| {_md_cell(entry.get('key'))} | {_md_cell(entry.get('meaning'))} | {_md_cell(entry.get('operator_action'))} |"
		)
	lines.append("")
	lines.append("## Pass Criteria")
	lines.append("")
	for criterion in _clean_list(runbook.get("pass_criteria")):
		lines.append(f"- {criterion}")
	return "\n".join(lines).strip() + "\n"


def write_operator_evidence_runbook_files(
	*,
	json_path: str = DEFAULT_OPERATOR_RUNBOOK_JSON_PATH,
	markdown_path: str = DEFAULT_OPERATOR_RUNBOOK_MARKDOWN_PATH,
	generated_at: str = "",
) -> Dict[str, Any]:
	contract = build_operator_evidence_runbook_contract(
		generated_at=generated_at,
		json_artifact_path=json_path,
		markdown_artifact_path=markdown_path,
	)
	json_target = Path(contract["json_artifact_path"])
	markdown_target = Path(contract["markdown_artifact_path"])
	if not json_target.is_absolute():
		json_target = Path.cwd() / json_target
	if not markdown_target.is_absolute():
		markdown_target = Path.cwd() / markdown_target
	json_target.parent.mkdir(parents=True, exist_ok=True)
	markdown_target.parent.mkdir(parents=True, exist_ok=True)
	json_target.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_target.write_text(render_operator_evidence_runbook_markdown(contract), encoding="utf-8")
	written = dict(contract)
	written["json_artifact_path"] = str(json_target)
	written["markdown_artifact_path"] = str(markdown_target)
	written["json_artifact_written"] = json_target.exists()
	written["markdown_artifact_written"] = markdown_target.exists()
	written["json_artifact_size_bytes"] = json_target.stat().st_size if json_target.exists() else 0
	written["markdown_artifact_size_bytes"] = markdown_target.stat().st_size if markdown_target.exists() else 0
	return written
