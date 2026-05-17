from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, TextIO

from .natural_business_understanding_contracts import CONTRACT_VERSION
from .regression_suite_governance import (
	GATE_LEGACY_STABILIZATION_BACKLOG,
	GATE_STALE_EXPECTATION_CLEANUP,
	REGRESSION_SUITE_BOUNDARY_CONTRACT_TYPE,
	STATUS_VERIFIED_PASS,
	build_regression_suite_boundary_contract,
)


ENTERPRISE_CLEANUP_GATE_REPORT_CONTRACT_TYPE = "qwen_enterprise_cleanup_gate_report_contract"
ENTERPRISE_CLEANUP_GATE_REPORT_SUITE_ID = "ec_2_enterprise_cleanup_gate_report_contracts"

GATE_DECISION_PASS = "pass"
GATE_DECISION_FAIL = "fail"
GATE_DECISION_DEFERRED = "deferred"

ARTIFACT_STATUS_PASS = "pass"
ARTIFACT_STATUS_FAIL = "fail"

DEFAULT_EC2_OUT_DIR = "impl_factory/00_governance/current_docs/generated/ec_2_enterprise_cleanup_gate"
DEFAULT_EC2_REPORT_JSON = "qwen_ec2_enterprise_cleanup_gate_report.json"
DEFAULT_EC2_REPORT_MARKDOWN = "qwen_ec2_enterprise_cleanup_gate_report.md"
MARKDOWN_TABLE_SEPARATOR = "-" * 3
PROJECTION_HEADER_TOKENS = ["Rank", "Product", "Revenue", "Quantity"]

EC0_MANIFEST_PATH = "impl_factory/00_governance/current_docs/qwen_erp_ec_0_baseline_write_scope_manifest_2026-05-14.md"
EC1_CLOSURE_NOTE_PATH = "impl_factory/00_governance/current_docs/qwen_erp_ec_1_product_projection_browser_evidence_2026-05-14.md"

EC1_EVIDENCE_DIR = "impl_factory/00_governance/current_docs/generated/ec_1_product_projection_browser_evidence"
EC1_CAPTURE_PATH = f"{EC1_EVIDENCE_DIR}/qwen_ec1_operator_capture_product_projection_qty_preserves_revenue.json"
EC1_OPERATOR_CLI_REPORT_PATH = f"{EC1_EVIDENCE_DIR}/qwen_s7_operator_evidence_import_cli_report.json"
EC1_INTAKE_PATH = f"{EC1_EVIDENCE_DIR}/qwen_s7_manual_uat_real_evidence_intake.json"
EC1_BUNDLE_PATH = f"{EC1_EVIDENCE_DIR}/qwen_s7_manual_uat_promotion_ready_bundle.json"
EC1_PROMOTION_PATH = f"{EC1_EVIDENCE_DIR}/qwen_s7_manual_uat_real_evidence_promotion_report.json"
EC1_BROWSER_CLI_PATH = f"{EC1_EVIDENCE_DIR}/qwen_s7_browser_batch_cli_report.json"
EC1_BROWSER_RUNNER_PATH = f"{EC1_EVIDENCE_DIR}/qwen_s7_browser_batch_resilience_runner_contract.json"

S7_6S_BUNDLE_PATH = (
	"impl_factory/00_governance/current_docs/generated/s7_6s_multi_scenario_browser_uat_batch/"
	"qwen_s7_manual_uat_promotion_ready_bundle.json"
)

EXPECTED_EC1_SCENARIO_ID = "product_projection_qty_preserves_revenue"


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _project_path(root_path: str | Path, relative_path: str) -> Path:
	root = Path(root_path or ".")
	path = Path(relative_path)
	return path if path.is_absolute() else root / path


def _read_json(path: Path) -> Dict[str, Any]:
	if not path.exists():
		return {}
	try:
		payload = json.loads(path.read_text(encoding="utf-8"))
	except json.JSONDecodeError:
		return {}
	return payload if isinstance(payload, dict) else {}


def _truthy(value: Any) -> bool:
	return _clean_text(value).lower() in {"true", "1", "yes"}


def _none_like(value: Any) -> bool:
	text = _clean_text(value).lower()
	return not text or text in {"none", "[]", "null", "-"}


def _data_row_count(raw_answer_text: str) -> int:
	count = 0
	for line in _clean_text(raw_answer_text).splitlines():
		text = line.strip()
		if not text.startswith("|"):
			continue
		if MARKDOWN_TABLE_SEPARATOR in text or all(token in text for token in PROJECTION_HEADER_TOKENS):
			continue
		count += 1
	return count


def _artifact_result(
	check_id: str,
	path: Path,
	*,
	pass_conditions: Iterable[bool],
	blocking_reasons: Iterable[str] | None = None,
	details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
	reasons = _clean_list(list(blocking_reasons or []))
	if not path.exists():
		reasons.append("artifact_missing")
	if all(bool(condition) for condition in pass_conditions) and not reasons:
		status = ARTIFACT_STATUS_PASS
	else:
		status = ARTIFACT_STATUS_FAIL
	return {
		"check_id": check_id,
		"artifact_path": str(path),
		"artifact_exists": path.exists(),
		"check_status": status,
		"release_blocking": status != ARTIFACT_STATUS_PASS,
		"blocking_reasons": sorted(set(reasons)),
		"details": dict(details or {}),
	}


def _release_ready_json_check(root_path: str | Path, check_id: str, relative_path: str) -> Dict[str, Any]:
	path = _project_path(root_path, relative_path)
	payload = _read_json(path)
	blockers = _clean_list(payload.get("release_blocking_reasons")) or _clean_list(payload.get("promotion_blocking_reasons"))
	return _artifact_result(
		check_id,
		path,
		pass_conditions=[bool(payload), bool(payload.get("release_ready")), not blockers],
		blocking_reasons=[] if path.exists() and payload else ["artifact_json_missing_or_malformed"],
		details={
			"release_ready": bool(payload.get("release_ready")),
			"blocking_reasons": blockers,
		},
	)


def _ec1_capture_check(root_path: str | Path) -> Dict[str, Any]:
	path = _project_path(root_path, EC1_CAPTURE_PATH)
	payload = _read_json(path)
	records = payload.get("source_capture_records") if isinstance(payload.get("source_capture_records"), list) else []
	record = dict(records[0]) if records and isinstance(records[0], dict) else {}
	raw_answer = _clean_text(record.get("raw_answer_text"))
	raw_trace = _clean_text(record.get("raw_trace_text"))
	row_count = _data_row_count(raw_answer)
	reasons: List[str] = []
	if record.get("scenario_id") != EXPECTED_EC1_SCENARIO_ID:
		reasons.append("scenario_id_mismatch")
	if _clean_text(record.get("evidence_mode")) != "operator_captured":
		reasons.append("evidence_mode_not_operator_captured")
	if record.get("dry_run_only") is not False:
		reasons.append("dry_run_only_not_false")
	if "Revenue" not in raw_answer:
		reasons.append("revenue_missing_from_answer")
	if "Quantity" not in raw_answer:
		reasons.append("quantity_missing_from_answer")
	if row_count != 7:
		reasons.append("visible_row_count_not_7")
	if "Projection fields | rank, item, revenue, quantity" not in raw_trace:
		reasons.append("projection_fields_missing_from_trace")
	if not _clean_text(record.get("operator_attestation")):
		reasons.append("operator_attestation_missing")
	return _artifact_result(
		"ec1_operator_capture_product_projection",
		path,
		pass_conditions=[bool(record), not reasons],
		blocking_reasons=reasons if path.exists() and payload else reasons + ["artifact_json_missing_or_malformed"],
		details={
			"scenario_id": _clean_text(record.get("scenario_id")),
			"evidence_mode": _clean_text(record.get("evidence_mode")),
			"dry_run_only": record.get("dry_run_only"),
			"answer_has_revenue": "Revenue" in raw_answer,
			"answer_has_quantity": "Quantity" in raw_answer,
			"answer_row_count": row_count,
			"trace_has_projection_fields": "Projection fields | rank, item, revenue, quantity" in raw_trace,
		},
	)


def _final_answer_authority_complete(fields: Dict[str, Any]) -> bool:
	return bool(
		_clean_text(fields.get("authority_source"))
		and _clean_text(fields.get("evidence_scope"))
		and _clean_text(fields.get("answer_mode"))
		and _truthy(fields.get("authority_complete"))
		and _clean_text(fields.get("preflight_status")) in {"passed", "bounded"}
		and _none_like(fields.get("missing_fields"))
	)


def _ec1_final_answer_authority_check(root_path: str | Path) -> Dict[str, Any]:
	path = _project_path(root_path, EC1_BUNDLE_PATH)
	payload = _read_json(path)
	records = _clean_list([])
	import_batch = _clean_dict(payload.get("import_batch_contract"))
	raw_records = import_batch.get("records") if isinstance(import_batch.get("records"), list) else []
	record = dict(raw_records[0]) if raw_records and isinstance(raw_records[0], dict) else {}
	final_fields = _clean_dict(record.get("final_answer_authority_fields"))
	reasons: List[str] = []
	if _clean_text(record.get("parse_status")) != "accepted":
		reasons.append("import_parse_not_accepted")
	if _clean_list(record.get("missing_capture_sections")):
		reasons.append("missing_capture_sections_present")
	if isinstance(record.get("field_mismatches"), list) and record.get("field_mismatches"):
		reasons.append("field_mismatches_present")
	if not _final_answer_authority_complete(final_fields):
		reasons.append("final_answer_authority_incomplete")
	if record.get("scenario_id") != EXPECTED_EC1_SCENARIO_ID:
		reasons.append("scenario_id_mismatch")
	records = [record.get("scenario_id")] if record.get("scenario_id") else []
	return _artifact_result(
		"ec1_final_answer_authority_normalized",
		path,
		pass_conditions=[bool(record), not reasons],
		blocking_reasons=reasons if path.exists() and payload else reasons + ["artifact_json_missing_or_malformed"],
		details={
			"scenario_ids": records,
			"parse_status": _clean_text(record.get("parse_status")),
			"missing_capture_sections": _clean_list(record.get("missing_capture_sections")),
			"field_mismatches": record.get("field_mismatches") if isinstance(record.get("field_mismatches"), list) else [],
			"final_answer_authority_fields": final_fields,
		},
	)


def _s7_6s_final_answer_authority_check(root_path: str | Path) -> Dict[str, Any]:
	path = _project_path(root_path, S7_6S_BUNDLE_PATH)
	payload = _read_json(path)
	import_batch = _clean_dict(payload.get("import_batch_contract"))
	raw_records = import_batch.get("records") if isinstance(import_batch.get("records"), list) else []
	scenario_ids: List[str] = []
	incomplete_ids: List[str] = []
	for raw_record in raw_records:
		if not isinstance(raw_record, dict):
			continue
		scenario_id = _clean_text(raw_record.get("scenario_id"))
		if scenario_id:
			scenario_ids.append(scenario_id)
		if not _final_answer_authority_complete(_clean_dict(raw_record.get("final_answer_authority_fields"))):
			incomplete_ids.append(scenario_id or "unknown")
	reasons: List[str] = []
	if not bool(payload.get("release_ready")):
		reasons.append("s7_6s_bundle_not_release_ready")
	if len(scenario_ids) < 4:
		reasons.append("s7_6s_promoted_record_count_below_4")
	if incomplete_ids:
		reasons.append("s7_6s_final_answer_authority_incomplete")
	return _artifact_result(
		"s7_6s_promoted_browser_evidence_authority_refresh",
		path,
		pass_conditions=[bool(payload), bool(scenario_ids), not reasons],
		blocking_reasons=reasons if path.exists() and payload else reasons + ["artifact_json_missing_or_malformed"],
		details={
			"release_ready": bool(payload.get("release_ready")),
			"promoted_scenario_ids": scenario_ids,
			"incomplete_authority_scenario_ids": incomplete_ids,
		},
	)


def build_artifact_freshness_checks(root_path: str | Path = ".") -> List[Dict[str, Any]]:
	return [
		_artifact_result(
			"ec0_manifest_present",
			_project_path(root_path, EC0_MANIFEST_PATH),
			pass_conditions=[_project_path(root_path, EC0_MANIFEST_PATH).exists()],
		),
		_artifact_result(
			"ec1_closure_note_present",
			_project_path(root_path, EC1_CLOSURE_NOTE_PATH),
			pass_conditions=[_project_path(root_path, EC1_CLOSURE_NOTE_PATH).exists()],
		),
		_ec1_capture_check(root_path),
		_release_ready_json_check(root_path, "ec1_operator_import_cli_release_ready", EC1_OPERATOR_CLI_REPORT_PATH),
		_release_ready_json_check(root_path, "ec1_real_evidence_intake_release_ready", EC1_INTAKE_PATH),
		_release_ready_json_check(root_path, "ec1_promotion_ready_bundle_release_ready", EC1_BUNDLE_PATH),
		_release_ready_json_check(root_path, "ec1_promotion_report_release_ready", EC1_PROMOTION_PATH),
		_release_ready_json_check(root_path, "ec1_browser_batch_cli_release_ready", EC1_BROWSER_CLI_PATH),
		_release_ready_json_check(root_path, "ec1_browser_batch_runner_release_ready", EC1_BROWSER_RUNNER_PATH),
		_ec1_final_answer_authority_check(root_path),
		_s7_6s_final_answer_authority_check(root_path),
	]


def _suite_status(entries: List[Dict[str, Any]], suite_ids: Iterable[str]) -> Dict[str, Any]:
	selected = [entry for entry in entries if _clean_text(entry.get("suite_id")) in set(suite_ids)]
	not_verified = [
		_clean_text(entry.get("suite_id"))
		for entry in selected
		if _clean_text(entry.get("last_verified_status")) != STATUS_VERIFIED_PASS
	]
	return {
		"suite_count": len(selected),
		"not_verified_pass_suites": not_verified,
		"status": GATE_DECISION_PASS if not not_verified else GATE_DECISION_FAIL,
	}


def _manual_browser_evidence_status(artifact_checks: List[Dict[str, Any]]) -> Dict[str, Any]:
	checks_by_id = {check.get("check_id"): check for check in artifact_checks}
	required_ids = [
		"ec1_operator_capture_product_projection",
		"ec1_operator_import_cli_release_ready",
		"ec1_real_evidence_intake_release_ready",
		"ec1_promotion_ready_bundle_release_ready",
		"ec1_promotion_report_release_ready",
		"ec1_browser_batch_cli_release_ready",
		"ec1_final_answer_authority_normalized",
		"s7_6s_promoted_browser_evidence_authority_refresh",
	]
	failed = [
		check_id
		for check_id in required_ids
		if _clean_dict(checks_by_id.get(check_id)).get("check_status") != ARTIFACT_STATUS_PASS
	]
	promoted_scenarios = [EXPECTED_EC1_SCENARIO_ID]
	s7_details = _clean_dict(_clean_dict(checks_by_id.get("s7_6s_promoted_browser_evidence_authority_refresh")).get("details"))
	promoted_scenarios.extend(_clean_list(s7_details.get("promoted_scenario_ids")))
	return {
		"status": GATE_DECISION_PASS if not failed else GATE_DECISION_FAIL,
		"failed_checks": failed,
		"promoted_real_browser_scenario_ids": sorted(set(promoted_scenarios)),
	}


def _final_decision(
	*,
	release_blocking_status: Dict[str, Any],
	artifact_checks: List[Dict[str, Any]],
	runtime_required_suites: List[str],
	manual_uat_suites: List[str],
) -> Dict[str, Any]:
	failed_artifacts = [
		_clean_text(check.get("check_id"))
		for check in artifact_checks
		if _clean_text(check.get("check_status")) != ARTIFACT_STATUS_PASS
	]
	if release_blocking_status.get("status") != GATE_DECISION_PASS or failed_artifacts:
		return {
			"final_decision": GATE_DECISION_FAIL,
			"decision_reason": "Release-blocking suite metadata or required evidence artifacts are incomplete.",
			"failed_artifact_checks": failed_artifacts,
		}
	if runtime_required_suites or manual_uat_suites:
		return {
			"final_decision": GATE_DECISION_DEFERRED,
			"decision_reason": "Release-blocking contracts and required evidence artifacts pass, but runtime/manual suites remain explicitly classified for later execution.",
			"failed_artifact_checks": [],
		}
	return {
		"final_decision": GATE_DECISION_PASS,
		"decision_reason": "Release-blocking contracts, evidence artifacts, and runtime/manual suite classifications are all complete.",
		"failed_artifact_checks": [],
	}


def build_enterprise_cleanup_gate_report(
	*,
	root_path: str | Path = ".",
	generated_at: str = "",
	reviewer: str = "",
	contract_owner: str = "enterprise_cleanup_gate_report",
) -> Dict[str, Any]:
	generated_at_text = _clean_text(generated_at) or _utc_now()
	boundary = build_regression_suite_boundary_contract(contract_owner="enterprise_cleanup_gate_report:regression_boundary")
	entries = [dict(entry) for entry in boundary.get("entries") or [] if isinstance(entry, dict)]
	release_status = _suite_status(entries, boundary.get("release_blocking_suites") or [])
	runtime_required_suites = _clean_list(boundary.get("runtime_required_suites"))
	manual_uat_suites = _clean_list(boundary.get("manual_uat_suites"))
	artifact_checks = build_artifact_freshness_checks(root_path)
	manual_evidence_status = _manual_browser_evidence_status(artifact_checks)
	known_red_suites = _clean_list(boundary.get("known_red_classified_suites"))
	legacy_backlog_suites = [
		_clean_text(entry.get("suite_id"))
		for entry in entries
		if _clean_text(entry.get("gate_class")) == GATE_LEGACY_STABILIZATION_BACKLOG
	]
	stale_cleanup_suites = [
		_clean_text(entry.get("suite_id"))
		for entry in entries
		if _clean_text(entry.get("gate_class")) == GATE_STALE_EXPECTATION_CLEANUP
	]
	artifact_status = GATE_DECISION_PASS if all(
		_clean_text(check.get("check_status")) == ARTIFACT_STATUS_PASS for check in artifact_checks
	) else GATE_DECISION_FAIL
	decision = _final_decision(
		release_blocking_status=release_status,
		artifact_checks=artifact_checks,
		runtime_required_suites=runtime_required_suites,
		manual_uat_suites=manual_uat_suites,
	)
	return {
		"type": ENTERPRISE_CLEANUP_GATE_REPORT_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"generated_at": generated_at_text,
		"reviewer": _clean_text(reviewer),
		"source_boundary_contract_type": REGRESSION_SUITE_BOUNDARY_CONTRACT_TYPE,
		"regression_boundary_contract": boundary,
		"suite_count": int(boundary.get("suite_count") or 0),
		"release_blocking_suite_count": int(boundary.get("release_blocking_suite_count") or 0),
		"runtime_required_suite_count": int(boundary.get("runtime_required_suite_count") or 0),
		"manual_uat_suite_count": int(boundary.get("manual_uat_suite_count") or 0),
		"release_blocking_suites": _clean_list(boundary.get("release_blocking_suites")),
		"runtime_required_suites": runtime_required_suites,
		"manual_uat_suites": manual_uat_suites,
		"known_red_classified_suites": known_red_suites,
		"legacy_backlog_suites": legacy_backlog_suites,
		"stale_cleanup_suites": stale_cleanup_suites,
		"release_blocking_status": release_status,
		"artifact_freshness_status": artifact_status,
		"artifact_freshness_checks": artifact_checks,
		"manual_browser_evidence_status": manual_evidence_status,
		"runtime_required_status": GATE_DECISION_DEFERRED if runtime_required_suites else GATE_DECISION_PASS,
		"known_red_status": "classified" if known_red_suites else "none",
		"final_decision": decision["final_decision"],
		"decision_reason": decision["decision_reason"],
		"failed_artifact_checks": decision["failed_artifact_checks"],
		"report_complete": bool(boundary.get("contract_complete") and artifact_checks),
		"scope_exclusions": [
			"no_final_answer_hard_gate",
			"no_model_role_strict_enforcement",
			"no_service_py_refactor",
			"no_duplicate_lane_cleanup",
			"no_release_packaging",
		],
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


def render_enterprise_cleanup_gate_report_markdown(report: Dict[str, Any]) -> str:
	contract = dict(report or {})
	lines: List[str] = ["# EC-2 Enterprise Cleanup Gate Report", ""]
	lines.extend(["## Decision", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"generated_at",
		"reviewer",
		"final_decision",
		"decision_reason",
		"report_complete",
		"suite_count",
		"release_blocking_suite_count",
		"runtime_required_suite_count",
		"manual_uat_suite_count",
		"artifact_freshness_status",
		"runtime_required_status",
		"known_red_status",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(contract.get(field))} |")
	lines.extend(["", "## Suite Boundary", ""])
	lines.append("| Category | Suites |")
	lines.append("|---|---|")
	lines.append(f"| Release blocking | {_md_cell(_join(contract.get('release_blocking_suites')))} |")
	lines.append(f"| Runtime required | {_md_cell(_join(contract.get('runtime_required_suites')))} |")
	lines.append(f"| Manual/browser UAT | {_md_cell(_join(contract.get('manual_uat_suites')))} |")
	lines.append(f"| Known red classified | {_md_cell(_join(contract.get('known_red_classified_suites')))} |")
	lines.append(f"| Legacy backlog | {_md_cell(_join(contract.get('legacy_backlog_suites')))} |")
	lines.append(f"| Stale cleanup | {_md_cell(_join(contract.get('stale_cleanup_suites')))} |")
	lines.extend(["", "## Artifact Freshness Checks", ""])
	lines.append("| Check | Status | Blocking | Reasons |")
	lines.append("|---|---|---|---|")
	for check in contract.get("artifact_freshness_checks") or []:
		if not isinstance(check, dict):
			continue
		lines.append(
			"| "
			+ " | ".join(
				[
					_md_cell(check.get("check_id")),
					_md_cell(check.get("check_status")),
					_md_cell(check.get("release_blocking")),
					_md_cell(_join(check.get("blocking_reasons"))),
				]
			)
			+ " |"
		)
	lines.extend(["", "## Manual Browser Evidence", ""])
	manual_status = _clean_dict(contract.get("manual_browser_evidence_status"))
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Status | {_md_cell(manual_status.get('status'))} |")
	lines.append(f"| Failed checks | {_md_cell(_join(manual_status.get('failed_checks')))} |")
	lines.append(f"| Promoted real browser scenarios | {_md_cell(_join(manual_status.get('promoted_real_browser_scenario_ids')))} |")
	lines.extend(["", "## Scope Exclusions", ""])
	for exclusion in _clean_list(contract.get("scope_exclusions")):
		lines.append(f"- {exclusion}")
	return "\n".join(lines).strip() + "\n"


def enterprise_cleanup_gate_report_output_paths(out_dir: str = DEFAULT_EC2_OUT_DIR) -> Dict[str, str]:
	target_dir = Path(_clean_text(out_dir) or DEFAULT_EC2_OUT_DIR)
	return {
		"report_json": str(target_dir / DEFAULT_EC2_REPORT_JSON),
		"report_markdown": str(target_dir / DEFAULT_EC2_REPORT_MARKDOWN),
	}


def write_enterprise_cleanup_gate_report_files(
	*,
	root_path: str | Path = ".",
	generated_at: str = "",
	reviewer: str = "",
	out_dir: str = DEFAULT_EC2_OUT_DIR,
) -> Dict[str, Any]:
	report = build_enterprise_cleanup_gate_report(
		root_path=root_path,
		generated_at=generated_at,
		reviewer=reviewer,
	)
	output_paths = enterprise_cleanup_gate_report_output_paths(out_dir)
	json_target = Path(output_paths["report_json"])
	markdown_target = Path(output_paths["report_markdown"])
	if not json_target.is_absolute():
		json_target = Path(root_path) / json_target
	if not markdown_target.is_absolute():
		markdown_target = Path(root_path) / markdown_target
	json_target.parent.mkdir(parents=True, exist_ok=True)
	json_target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_target.write_text(render_enterprise_cleanup_gate_report_markdown(report), encoding="utf-8")
	written = dict(report)
	written["output_paths"] = output_paths
	written["report_json_artifact_path"] = str(json_target)
	written["report_markdown_artifact_path"] = str(markdown_target)
	written["report_json_artifact_written"] = json_target.exists()
	written["report_markdown_artifact_written"] = markdown_target.exists()
	return written


def _summary_lines(report: Dict[str, Any]) -> List[str]:
	return [
		"EC-2 Enterprise Cleanup Gate Report",
		f"Final decision: {_clean_text(report.get('final_decision'))}",
		f"Artifact freshness: {_clean_text(report.get('artifact_freshness_status'))}",
		f"Release-blocking suites: {int(report.get('release_blocking_suite_count') or 0)}",
		f"Runtime-required suites: {int(report.get('runtime_required_suite_count') or 0)}",
		f"Manual UAT suites: {int(report.get('manual_uat_suite_count') or 0)}",
		f"Failed artifact checks: {_join(report.get('failed_artifact_checks'))}",
		f"Report JSON: {_clean_text(report.get('report_json_artifact_path'))}",
	]


def build_arg_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Build the EC-2 Enterprise Cleanup gate report without changing runtime behavior.")
	parser.add_argument("--root", default=".", help="Repository root for reading evidence artifacts and writing generated reports.")
	parser.add_argument("--out-dir", default=DEFAULT_EC2_OUT_DIR, help="Output directory for EC-2 JSON/Markdown reports.")
	parser.add_argument("--reviewer", default="", help="Reviewer identity for the generated report.")
	parser.add_argument("--generated-at", default="", help="Deterministic timestamp override.")
	return parser


def main(argv: Sequence[str] | None = None, *, stdout: TextIO | None = None) -> int:
	parser = build_arg_parser()
	args = parser.parse_args(list(argv) if argv is not None else None)
	report = write_enterprise_cleanup_gate_report_files(
		root_path=args.root,
		out_dir=args.out_dir,
		reviewer=args.reviewer,
		generated_at=args.generated_at,
	)
	stream = stdout or __import__("sys").stdout
	stream.write("\n".join(_summary_lines(report)) + "\n")
	return 0 if report.get("final_decision") in {GATE_DECISION_PASS, GATE_DECISION_DEFERRED} else 1


if __name__ == "__main__":
	raise SystemExit(main())
