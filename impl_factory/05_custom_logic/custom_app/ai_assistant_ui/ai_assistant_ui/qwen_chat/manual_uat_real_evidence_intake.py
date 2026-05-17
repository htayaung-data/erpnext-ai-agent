from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .manual_uat_bundle import (
	build_manual_uat_evidence_bundle,
	render_manual_uat_evidence_bundle_markdown,
)
from .manual_uat_capture_template import (
	EVIDENCE_MODE_OPERATOR_CAPTURED,
	OPERATOR_CAPTURE_SOURCE,
	OPERATOR_PROMOTION_INTENT,
	OPERATOR_RELEASE_BOUNDARY,
)
from .manual_uat_promotion import (
	EVIDENCE_CLASS_OPERATOR_CAPTURED,
	EVIDENCE_CLASS_SAMPLE_FIXTURE,
	EVIDENCE_CLASS_UNKNOWN_OR_UNSAFE,
	build_manual_uat_evidence_promotion_report,
	classify_manual_uat_evidence_record,
	render_manual_uat_evidence_promotion_markdown,
)
from .manual_uat_sample_fixture import (
	EVIDENCE_MODE_SAMPLE_FIXTURE,
	PRODUCTION_RELEASE_BOUNDARY,
	SAMPLE_CAPTURE_SOURCE,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .regression_scenario_packs import (
	S7_REGRESSION_SCENARIO_REGISTRY,
	build_regression_scenario_contract,
)


MANUAL_UAT_REAL_EVIDENCE_INTAKE_CONTRACT_TYPE = "qwen_manual_uat_real_evidence_intake_contract"
MANUAL_UAT_REAL_EVIDENCE_INTAKE_SUITE_ID = "s7_manual_uat_real_evidence_intake_contracts"

DEFAULT_MANUAL_UAT_REAL_EVIDENCE_INTAKE_JSON_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_real_evidence_intake.json"
)
DEFAULT_MANUAL_UAT_PROMOTION_READY_BUNDLE_JSON_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_promotion_ready_bundle.json"
)
DEFAULT_MANUAL_UAT_PROMOTION_READY_BUNDLE_MARKDOWN_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_promotion_ready_bundle.md"
)
DEFAULT_MANUAL_UAT_REAL_EVIDENCE_PROMOTION_JSON_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_real_evidence_promotion_report.json"
)
DEFAULT_MANUAL_UAT_REAL_EVIDENCE_PROMOTION_MARKDOWN_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_real_evidence_promotion_report.md"
)


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


def _scenario_ids_from_registry(registry: Iterable[Dict[str, Any]] | None = None) -> List[str]:
	scenario_ids: List[str] = []
	for entry in registry or S7_REGRESSION_SCENARIO_REGISTRY:
		if not isinstance(entry, dict):
			continue
		scenario = build_regression_scenario_contract(entry)
		scenario_id = _clean_text(scenario.get("scenario_id"))
		if scenario_id:
			scenario_ids.append(scenario_id)
	return scenario_ids


def _scenario_ids_from_records(records: Iterable[Dict[str, Any]]) -> List[str]:
	scenario_ids: List[str] = []
	for record in records:
		scenario_id = _clean_text(record.get("scenario_id"))
		if scenario_id:
			scenario_ids.append(scenario_id)
	return scenario_ids


def _duplicate_values(values: List[str]) -> List[str]:
	return sorted({value for value in values if value and values.count(value) > 1})


def _sample_marker_present(record: Dict[str, Any]) -> bool:
	source = _clean_dict(record)
	return bool(
		_clean_text(source.get("evidence_mode")) == EVIDENCE_MODE_SAMPLE_FIXTURE
		or _clean_text(source.get("capture_source")) == SAMPLE_CAPTURE_SOURCE
		or _clean_text(source.get("release_boundary")) == PRODUCTION_RELEASE_BOUNDARY
		or bool(source.get("dry_run_only"))
		or _clean_text(source.get("sample_fixture_id"))
	)


def _record_intake_blocking_reasons(record: Dict[str, Any]) -> List[str]:
	source = _clean_dict(record)
	reasons: List[str] = []
	if not _clean_text(source.get("scenario_id")):
		reasons.append("scenario_id_missing")
	if _clean_text(source.get("evidence_mode")) != EVIDENCE_MODE_OPERATOR_CAPTURED:
		reasons.append("evidence_mode_not_operator_captured")
	if _clean_text(source.get("capture_source")) != OPERATOR_CAPTURE_SOURCE:
		reasons.append("capture_source_not_manual_browser_uat")
	release_boundary = _clean_text(source.get("release_boundary"))
	if not release_boundary:
		reasons.append("release_boundary_missing")
	elif release_boundary != OPERATOR_RELEASE_BOUNDARY:
		reasons.append("release_boundary_not_none")
	if source.get("dry_run_only") is not False:
		reasons.append("dry_run_only_not_false")
	if _clean_text(source.get("promotion_intent")) != OPERATOR_PROMOTION_INTENT:
		reasons.append("promotion_intent_not_production_manual_uat")
	if not _clean_text(source.get("operator_attestation")):
		reasons.append("operator_attestation_missing")
	if not _clean_text(source.get("reviewer")):
		reasons.append("reviewer_missing")
	if not _clean_text(source.get("captured_at")):
		reasons.append("captured_at_missing")
	if _sample_marker_present(source):
		reasons.append("sample_evidence_not_allowed")
	return sorted(set(reasons))


def _intake_record_evaluations(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	evaluations: List[Dict[str, Any]] = []
	for record in records:
		scenario_id = _clean_text(record.get("scenario_id")) or "unknown"
		blocking_reasons = _record_intake_blocking_reasons(record)
		evidence_class = classify_manual_uat_evidence_record(record)
		evaluations.append(
			{
				"scenario_id": scenario_id,
				"evidence_class": evidence_class,
				"evidence_mode": _clean_text(record.get("evidence_mode")) or "none",
				"capture_source": _clean_text(record.get("capture_source")) or "none",
				"reviewer_present": bool(_clean_text(record.get("reviewer"))),
				"captured_at_present": bool(_clean_text(record.get("captured_at"))),
				"operator_attestation_present": bool(_clean_text(record.get("operator_attestation"))),
				"promotion_intent": _clean_text(record.get("promotion_intent")) or "none",
				"release_boundary": _clean_text(record.get("release_boundary")) or "none",
				"dry_run_only": bool(record.get("dry_run_only")),
				"sample_marker_present": _sample_marker_present(record),
				"intake_accepted": not blocking_reasons,
				"blocking_reasons": blocking_reasons,
			}
		)
	return evaluations


def _release_blocking_reasons(
	*,
	expected_ids: List[str],
	records: List[Dict[str, Any]],
	record_evaluations: List[Dict[str, Any]],
	bundle: Dict[str, Any],
	promotion_report: Dict[str, Any],
) -> List[str]:
	reasons = set()
	if not records:
		reasons.add("source_capture_records_missing")
	if not expected_ids:
		reasons.add("expected_scenarios_missing")
	record_ids = _scenario_ids_from_records(records)
	if _duplicate_values(record_ids):
		reasons.add("duplicate_capture_records")
	for record in record_evaluations:
		if not bool(record.get("intake_accepted")):
			reasons.add("intake_record_not_accepted")
		for reason in _clean_list(record.get("blocking_reasons")):
			reasons.add(reason)
	for reason in _clean_list(bundle.get("release_blocking_reasons")):
		reasons.add(reason)
	if not bool(bundle.get("roundtrip_complete")):
		reasons.add("bundle_roundtrip_not_complete")
	if not bool(bundle.get("release_ready")):
		reasons.add("bundle_not_release_ready")
	for reason in _clean_list(promotion_report.get("promotion_blocking_reasons")):
		reasons.add(reason)
	if not bool(promotion_report.get("release_ready")):
		reasons.add("promotion_not_release_ready")
	if _clean_list(bundle.get("blocked_scenario_ids")):
		reasons.add("blocked_import_records")
	if _clean_list(bundle.get("quarantined_scenario_ids")):
		reasons.add("quarantined_import_records")
	if _clean_list(bundle.get("missing_evidence_scenario_ids")):
		reasons.add("missing_archive_evidence")
	if _clean_list(bundle.get("archive_blocking_failure_scenario_ids")):
		reasons.add("archive_blocking_failures")
	return sorted(reasons)


def build_manual_uat_real_evidence_intake(
	capture_records: Iterable[Dict[str, Any]] | None = None,
	*,
	registry: Iterable[Dict[str, Any]] | None = None,
	expected_scenario_ids: Iterable[str] | None = None,
	intake_id: str = "s7_manual_uat_real_evidence_intake",
	generated_at: str = "",
	reviewer: str = "",
	intake_json_artifact_path: str = DEFAULT_MANUAL_UAT_REAL_EVIDENCE_INTAKE_JSON_PATH,
	bundle_json_artifact_path: str = DEFAULT_MANUAL_UAT_PROMOTION_READY_BUNDLE_JSON_PATH,
	bundle_markdown_artifact_path: str = DEFAULT_MANUAL_UAT_PROMOTION_READY_BUNDLE_MARKDOWN_PATH,
	promotion_json_artifact_path: str = DEFAULT_MANUAL_UAT_REAL_EVIDENCE_PROMOTION_JSON_PATH,
	promotion_markdown_artifact_path: str = DEFAULT_MANUAL_UAT_REAL_EVIDENCE_PROMOTION_MARKDOWN_PATH,
	contract_owner: str = "s7_manual_uat_real_evidence_intake",
) -> Dict[str, Any]:
	generated_at_text = _clean_text(generated_at) or _utc_now()
	records = _clean_records(capture_records)
	expected_ids = (
		[_clean_text(value) for value in expected_scenario_ids if _clean_text(value)]
		if expected_scenario_ids is not None
		else (_scenario_ids_from_records(records) or _scenario_ids_from_registry(registry))
	)
	record_evaluations = _intake_record_evaluations(records)
	bundle = build_manual_uat_evidence_bundle(
		records,
		registry=registry,
		expected_scenario_ids=expected_ids,
		bundle_id=f"{_clean_text(intake_id)}:promotion_ready_bundle",
		generated_at=generated_at_text,
		reviewer=reviewer,
		json_artifact_path=bundle_json_artifact_path,
		markdown_artifact_path=bundle_markdown_artifact_path,
		contract_owner="s7_manual_uat_real_evidence_intake_bundle",
	)
	promotion_report = build_manual_uat_evidence_promotion_report(
		bundle,
		promotion_id=f"{_clean_text(intake_id)}:promotion",
		generated_at=generated_at_text,
		reviewer=reviewer,
		json_artifact_path=promotion_json_artifact_path,
		markdown_artifact_path=promotion_markdown_artifact_path,
		contract_owner="s7_manual_uat_real_evidence_intake_promotion",
	)
	release_blocking_reasons = _release_blocking_reasons(
		expected_ids=expected_ids,
		records=records,
		record_evaluations=record_evaluations,
		bundle=bundle,
		promotion_report=promotion_report,
	)
	intake_complete = bool(records and not release_blocking_reasons)
	promotion_ready = bool(
		intake_complete
		and bool(bundle.get("roundtrip_complete"))
		and bool(bundle.get("release_ready"))
		and bool(promotion_report.get("promotion_eligible"))
		and bool(promotion_report.get("release_ready"))
	)
	return {
		"type": MANUAL_UAT_REAL_EVIDENCE_INTAKE_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"intake_id": _clean_text(intake_id),
		"generated_at": generated_at_text,
		"reviewer": _clean_text(reviewer),
		"intake_json_artifact_path": _clean_text(intake_json_artifact_path),
		"intake_json_artifact_written": False,
		"bundle_json_artifact_path": _clean_text(bundle_json_artifact_path),
		"bundle_markdown_artifact_path": _clean_text(bundle_markdown_artifact_path),
		"promotion_json_artifact_path": _clean_text(promotion_json_artifact_path),
		"promotion_markdown_artifact_path": _clean_text(promotion_markdown_artifact_path),
		"expected_scenario_ids": expected_ids,
		"expected_scenario_count": len(expected_ids),
		"source_capture_record_count": len(records),
		"accepted_intake_record_count": len([record for record in record_evaluations if bool(record.get("intake_accepted"))]),
		"blocked_intake_record_count": len([record for record in record_evaluations if not bool(record.get("intake_accepted"))]),
		"record_evaluations": record_evaluations,
		"source_capture_records": records,
		"promotion_ready_bundle_contract": bundle,
		"promotion_report_contract": promotion_report,
		"operator_record_ids": _clean_list(promotion_report.get("operator_record_ids")),
		"sample_record_ids": _clean_list(promotion_report.get("sample_record_ids")),
		"unsafe_record_ids": _clean_list(promotion_report.get("unsafe_record_ids")),
		"intake_complete": intake_complete,
		"promotion_ready": promotion_ready,
		"release_ready": promotion_ready,
		"release_boundary": "none" if promotion_ready else "real_evidence_intake_boundary",
		"release_blocking_reasons": release_blocking_reasons,
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


def render_manual_uat_real_evidence_intake_markdown(intake_contract: Dict[str, Any]) -> str:
	contract = dict(intake_contract or {})
	bundle = _clean_dict(contract.get("promotion_ready_bundle_contract"))
	promotion = _clean_dict(contract.get("promotion_report_contract"))
	lines: List[str] = ["# S7 Manual UAT Real Evidence Intake", ""]
	lines.append("## Intake Metadata")
	lines.append("")
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"intake_id",
		"generated_at",
		"reviewer",
		"expected_scenario_count",
		"source_capture_record_count",
		"accepted_intake_record_count",
		"blocked_intake_record_count",
		"intake_complete",
		"promotion_ready",
		"release_ready",
		"release_boundary",
		"intake_json_artifact_path",
		"bundle_json_artifact_path",
		"bundle_markdown_artifact_path",
		"promotion_json_artifact_path",
		"promotion_markdown_artifact_path",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(contract.get(field))} |")
	lines.extend(["", "## Release Boundary", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Blocking reasons | {_md_cell(_join(contract.get('release_blocking_reasons')))} |")
	lines.append(f"| Operator records | {_md_cell(_join(contract.get('operator_record_ids')))} |")
	lines.append(f"| Sample records | {_md_cell(_join(contract.get('sample_record_ids')))} |")
	lines.append(f"| Unsafe records | {_md_cell(_join(contract.get('unsafe_record_ids')))} |")
	lines.extend(["", "## Composed Contract Status", ""])
	lines.append("| Contract | Complete | Release ready |")
	lines.append("|---|---|---|")
	lines.append(f"| Promotion-ready bundle | {_md_cell(bundle.get('roundtrip_complete'))} | {_md_cell(bundle.get('release_ready'))} |")
	lines.append(f"| Promotion report | {_md_cell(promotion.get('promotion_eligible'))} | {_md_cell(promotion.get('release_ready'))} |")
	lines.extend(["", "## Intake Record Evaluation", ""])
	lines.append("| Scenario | Class | Mode | Source | Attested | Accepted | Blocking reasons |")
	lines.append("|---|---|---|---|---|---|---|")
	for record in contract.get("record_evaluations") or []:
		if not isinstance(record, dict):
			continue
		lines.append(
			"| "
			+ " | ".join(
				[
					_md_cell(record.get("scenario_id")),
					_md_cell(record.get("evidence_class")),
					_md_cell(record.get("evidence_mode")),
					_md_cell(record.get("capture_source")),
					_md_cell(record.get("operator_attestation_present")),
					_md_cell(record.get("intake_accepted")),
					_md_cell(_join(record.get("blocking_reasons"))),
				]
			)
			+ " |"
		)
	if not contract.get("record_evaluations"):
		lines.append("| none | none | none | none | False | False | source_capture_records_missing |")
	return "\n".join(lines).strip() + "\n"


def write_manual_uat_real_evidence_intake_files(
	capture_records: Iterable[Dict[str, Any]] | None = None,
	*,
	intake_json_path: str = DEFAULT_MANUAL_UAT_REAL_EVIDENCE_INTAKE_JSON_PATH,
	bundle_json_path: str = DEFAULT_MANUAL_UAT_PROMOTION_READY_BUNDLE_JSON_PATH,
	bundle_markdown_path: str = DEFAULT_MANUAL_UAT_PROMOTION_READY_BUNDLE_MARKDOWN_PATH,
	promotion_json_path: str = DEFAULT_MANUAL_UAT_REAL_EVIDENCE_PROMOTION_JSON_PATH,
	promotion_markdown_path: str = DEFAULT_MANUAL_UAT_REAL_EVIDENCE_PROMOTION_MARKDOWN_PATH,
	registry: Iterable[Dict[str, Any]] | None = None,
	expected_scenario_ids: Iterable[str] | None = None,
	intake_id: str = "s7_manual_uat_real_evidence_intake",
	generated_at: str = "",
	reviewer: str = "",
) -> Dict[str, Any]:
	contract = build_manual_uat_real_evidence_intake(
		capture_records,
		registry=registry,
		expected_scenario_ids=expected_scenario_ids,
		intake_id=intake_id,
		generated_at=generated_at,
		reviewer=reviewer,
		intake_json_artifact_path=intake_json_path,
		bundle_json_artifact_path=bundle_json_path,
		bundle_markdown_artifact_path=bundle_markdown_path,
		promotion_json_artifact_path=promotion_json_path,
		promotion_markdown_artifact_path=promotion_markdown_path,
	)
	intake_target = Path(contract["intake_json_artifact_path"])
	bundle_json_target = Path(contract["bundle_json_artifact_path"])
	bundle_markdown_target = Path(contract["bundle_markdown_artifact_path"])
	promotion_json_target = Path(contract["promotion_json_artifact_path"])
	promotion_markdown_target = Path(contract["promotion_markdown_artifact_path"])
	targets = [
		intake_target,
		bundle_json_target,
		bundle_markdown_target,
		promotion_json_target,
		promotion_markdown_target,
	]
	resolved_targets = []
	for target in targets:
		resolved = target if target.is_absolute() else Path.cwd() / target
		resolved.parent.mkdir(parents=True, exist_ok=True)
		resolved_targets.append(resolved)
	intake_target, bundle_json_target, bundle_markdown_target, promotion_json_target, promotion_markdown_target = resolved_targets
	bundle = _clean_dict(contract.get("promotion_ready_bundle_contract"))
	promotion = _clean_dict(contract.get("promotion_report_contract"))
	intake_target.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	bundle_json_target.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	bundle_markdown_target.write_text(render_manual_uat_evidence_bundle_markdown(bundle), encoding="utf-8")
	promotion_json_target.write_text(json.dumps(promotion, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	promotion_markdown_target.write_text(render_manual_uat_evidence_promotion_markdown(promotion), encoding="utf-8")
	written = dict(contract)
	written["intake_json_artifact_path"] = str(intake_target)
	written["bundle_json_artifact_path"] = str(bundle_json_target)
	written["bundle_markdown_artifact_path"] = str(bundle_markdown_target)
	written["promotion_json_artifact_path"] = str(promotion_json_target)
	written["promotion_markdown_artifact_path"] = str(promotion_markdown_target)
	written["intake_json_artifact_written"] = intake_target.exists()
	written["bundle_json_artifact_written"] = bundle_json_target.exists()
	written["bundle_markdown_artifact_written"] = bundle_markdown_target.exists()
	written["promotion_json_artifact_written"] = promotion_json_target.exists()
	written["promotion_markdown_artifact_written"] = promotion_markdown_target.exists()
	written["intake_json_artifact_size_bytes"] = intake_target.stat().st_size if intake_target.exists() else 0
	written["bundle_json_artifact_size_bytes"] = bundle_json_target.stat().st_size if bundle_json_target.exists() else 0
	written["bundle_markdown_artifact_size_bytes"] = bundle_markdown_target.stat().st_size if bundle_markdown_target.exists() else 0
	written["promotion_json_artifact_size_bytes"] = promotion_json_target.stat().st_size if promotion_json_target.exists() else 0
	written["promotion_markdown_artifact_size_bytes"] = promotion_markdown_target.stat().st_size if promotion_markdown_target.exists() else 0
	return written
