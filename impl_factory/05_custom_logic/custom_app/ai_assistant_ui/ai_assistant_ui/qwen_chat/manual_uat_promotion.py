from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .manual_uat_bundle import MANUAL_UAT_BUNDLE_CONTRACT_TYPE
from .manual_uat_import import IMPORT_PARSE_ACCEPTED
from .manual_uat_sample_fixture import (
	EVIDENCE_MODE_SAMPLE_FIXTURE,
	PRODUCTION_RELEASE_BOUNDARY,
	SAMPLE_CAPTURE_SOURCE,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION


MANUAL_UAT_PROMOTION_CONTRACT_TYPE = "qwen_manual_uat_evidence_promotion_contract"
MANUAL_UAT_PROMOTION_SUITE_ID = "s7_manual_uat_evidence_promotion_contracts"

EVIDENCE_MODE_OPERATOR_CAPTURED = "operator_captured"
EVIDENCE_CLASS_SAMPLE_FIXTURE = "sample_fixture"
EVIDENCE_CLASS_OPERATOR_CAPTURED = "operator_captured"
EVIDENCE_CLASS_UNKNOWN_OR_UNSAFE = "unknown_or_unsafe"
MANUAL_BROWSER_CAPTURE_SOURCE = "manual_browser_uat"
OPERATOR_PROMOTION_INTENT = "production_manual_uat"
OPERATOR_RELEASE_BOUNDARY = "none"

PROMOTION_RELEASE_BOUNDARY = "manual_uat_promotion_boundary"

DEFAULT_MANUAL_UAT_PROMOTION_JSON_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_evidence_promotion_report.json"
)
DEFAULT_MANUAL_UAT_PROMOTION_MARKDOWN_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_evidence_promotion_report.md"
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


def _count_values(values: Iterable[str]) -> Dict[str, int]:
	counts: Dict[str, int] = {}
	for value in values:
		key = _clean_text(value) or "none"
		counts[key] = counts.get(key, 0) + 1
	return dict(sorted(counts.items()))


def _source_bundle(source_contract: Dict[str, Any]) -> Dict[str, Any]:
	source = _clean_dict(source_contract)
	if isinstance(source.get("sample_bundle_contract"), dict):
		return dict(source.get("sample_bundle_contract") or {})
	if _clean_text(source.get("type")) == MANUAL_UAT_BUNDLE_CONTRACT_TYPE:
		return source
	return source


def _source_contract_type(source_contract: Dict[str, Any]) -> str:
	return _clean_text(_clean_dict(source_contract).get("type")) or "unknown"


def _records_by_scenario(records: Iterable[Dict[str, Any]] | None) -> Dict[str, Dict[str, Any]]:
	out: Dict[str, Dict[str, Any]] = {}
	for record in _clean_records(records):
		scenario_id = _clean_text(record.get("scenario_id"))
		if scenario_id and scenario_id not in out:
			out[scenario_id] = record
	return out


def _sample_marker_present(record: Dict[str, Any]) -> bool:
	source = _clean_dict(record)
	return bool(
		_clean_text(source.get("evidence_mode")) == EVIDENCE_MODE_SAMPLE_FIXTURE
		or _clean_text(source.get("capture_source")) == SAMPLE_CAPTURE_SOURCE
		or _clean_text(source.get("release_boundary")) == PRODUCTION_RELEASE_BOUNDARY
		or bool(source.get("dry_run_only"))
		or _clean_text(source.get("sample_fixture_id"))
	)


def classify_manual_uat_evidence_record(record: Dict[str, Any]) -> str:
	source = _clean_dict(record)
	if _sample_marker_present(source):
		return EVIDENCE_CLASS_SAMPLE_FIXTURE
	if (
		_clean_text(source.get("evidence_mode")) == EVIDENCE_MODE_OPERATOR_CAPTURED
		and _clean_text(source.get("capture_source")) == MANUAL_BROWSER_CAPTURE_SOURCE
	):
		return EVIDENCE_CLASS_OPERATOR_CAPTURED
	return EVIDENCE_CLASS_UNKNOWN_OR_UNSAFE


def _record_blocking_reasons(
	*,
	source_record: Dict[str, Any],
	import_record: Dict[str, Any],
	archive_record: Dict[str, Any],
	bundle_roundtrip_complete: bool,
	bundle_release_ready: bool,
) -> List[str]:
	reasons: List[str] = []
	evidence_class = classify_manual_uat_evidence_record(source_record)
	if evidence_class == EVIDENCE_CLASS_SAMPLE_FIXTURE:
		reasons.append(PRODUCTION_RELEASE_BOUNDARY)
	if evidence_class == EVIDENCE_CLASS_UNKNOWN_OR_UNSAFE:
		reasons.append("unknown_or_unsafe_evidence_mode")
	if _clean_text(source_record.get("evidence_mode")) != EVIDENCE_MODE_OPERATOR_CAPTURED:
		reasons.append("evidence_mode_not_operator_captured")
	if _clean_text(source_record.get("capture_source")) != MANUAL_BROWSER_CAPTURE_SOURCE:
		reasons.append("capture_source_not_manual_browser_uat")
	if not _clean_text(source_record.get("reviewer")):
		reasons.append("reviewer_missing")
	if not _clean_text(source_record.get("captured_at")):
		reasons.append("captured_at_missing")
	if not _clean_text(source_record.get("operator_attestation")):
		reasons.append("operator_attestation_missing")
	if _clean_text(source_record.get("promotion_intent")) != OPERATOR_PROMOTION_INTENT:
		reasons.append("promotion_intent_not_production_manual_uat")
	release_boundary = _clean_text(source_record.get("release_boundary"))
	if not release_boundary:
		reasons.append("release_boundary_missing")
	elif release_boundary != OPERATOR_RELEASE_BOUNDARY:
		reasons.append("release_boundary_not_none")
	if _sample_marker_present(source_record):
		reasons.append("sample_marker_present")
	if _clean_text(import_record.get("parse_status")) != IMPORT_PARSE_ACCEPTED:
		reasons.append("import_not_accepted")
	if bool(import_record.get("release_blocking")):
		reasons.append("import_release_blocking")
	if not bool(archive_record.get("archive_complete")):
		reasons.append("archive_not_complete")
	if bool(archive_record.get("release_blocking")):
		reasons.append("archive_release_blocking")
	if not bundle_roundtrip_complete:
		reasons.append("bundle_roundtrip_not_complete")
	if not bundle_release_ready:
		reasons.append("bundle_not_release_ready")
	return sorted(set(reasons))


def _promotion_blocking_reasons(
	*,
	record_evaluations: List[Dict[str, Any]],
	bundle: Dict[str, Any],
) -> List[str]:
	reasons = set(_clean_list(bundle.get("release_blocking_reasons")))
	if not record_evaluations:
		reasons.add("source_capture_records_missing")
	if not bool(bundle.get("roundtrip_complete")):
		reasons.add("bundle_roundtrip_not_complete")
	if not bool(bundle.get("release_ready")):
		reasons.add("bundle_not_release_ready")
	if _clean_list(bundle.get("blocked_scenario_ids")):
		reasons.add("blocked_import_records")
	if _clean_list(bundle.get("quarantined_scenario_ids")):
		reasons.add("quarantined_import_records")
	if _clean_list(bundle.get("missing_evidence_scenario_ids")):
		reasons.add("missing_archive_evidence")
	if _clean_list(bundle.get("archive_blocking_failure_scenario_ids")):
		reasons.add("archive_blocking_failures")
	if _clean_list(bundle.get("duplicate_evidence_ids")):
		reasons.add("duplicate_evidence_records")
	classes = sorted({_clean_text(record.get("evidence_class")) for record in record_evaluations})
	if EVIDENCE_CLASS_SAMPLE_FIXTURE in classes:
		reasons.add(PRODUCTION_RELEASE_BOUNDARY)
	if EVIDENCE_CLASS_UNKNOWN_OR_UNSAFE in classes:
		reasons.add("unknown_or_unsafe_evidence_mode")
	if len([value for value in classes if value]) > 1:
		reasons.add("mixed_evidence_classes")
	for record in record_evaluations:
		if not bool(record.get("promotion_eligible")):
			reasons.add("record_not_promotion_eligible")
		for reason in _clean_list(record.get("blocking_reasons")):
			reasons.add(reason)
	return sorted(reasons)


def build_manual_uat_evidence_promotion_report(
	source_contract: Dict[str, Any] | None = None,
	*,
	promotion_id: str = "s7_manual_uat_evidence_promotion",
	generated_at: str = "",
	reviewer: str = "",
	json_artifact_path: str = DEFAULT_MANUAL_UAT_PROMOTION_JSON_PATH,
	markdown_artifact_path: str = DEFAULT_MANUAL_UAT_PROMOTION_MARKDOWN_PATH,
	contract_owner: str = "s7_manual_uat_evidence_promotion",
) -> Dict[str, Any]:
	source = _clean_dict(source_contract)
	bundle = _source_bundle(source)
	import_batch = _clean_dict(bundle.get("import_batch_contract"))
	archive_index = _clean_dict(bundle.get("archive_index_contract"))
	import_records = _records_by_scenario(import_batch.get("records"))
	archive_records = _records_by_scenario(archive_index.get("records"))
	source_records = _clean_records(bundle.get("source_capture_records"))
	bundle_roundtrip_complete = bool(bundle.get("roundtrip_complete"))
	bundle_release_ready = bool(bundle.get("release_ready"))
	record_evaluations: List[Dict[str, Any]] = []
	for source_record in source_records:
		scenario_id = _clean_text(source_record.get("scenario_id")) or "unknown"
		import_record = _clean_dict(import_records.get(scenario_id))
		archive_record = _clean_dict(archive_records.get(scenario_id))
		blocking_reasons = _record_blocking_reasons(
			source_record=source_record,
			import_record=import_record,
			archive_record=archive_record,
			bundle_roundtrip_complete=bundle_roundtrip_complete,
			bundle_release_ready=bundle_release_ready,
		)
		evidence_class = classify_manual_uat_evidence_record(source_record)
		record_evaluations.append(
			{
				"scenario_id": scenario_id,
				"evidence_class": evidence_class,
				"evidence_mode": _clean_text(source_record.get("evidence_mode")) or "none",
				"capture_source": _clean_text(source_record.get("capture_source")) or "none",
				"reviewer": _clean_text(source_record.get("reviewer")),
				"captured_at": _clean_text(source_record.get("captured_at")),
				"promotion_intent": _clean_text(source_record.get("promotion_intent")) or "none",
				"release_boundary": _clean_text(source_record.get("release_boundary")) or "none",
				"operator_attestation_present": bool(_clean_text(source_record.get("operator_attestation"))),
				"sample_marker_present": _sample_marker_present(source_record),
				"import_parse_status": _clean_text(import_record.get("parse_status")) or "missing",
				"archive_complete": bool(archive_record.get("archive_complete")),
				"archive_release_blocking": bool(archive_record.get("release_blocking")),
				"promotion_eligible": not blocking_reasons,
				"blocking_reasons": blocking_reasons,
			}
		)
	blocking_reasons = _promotion_blocking_reasons(record_evaluations=record_evaluations, bundle=bundle)
	promotion_eligible = bool(record_evaluations and not blocking_reasons)
	evidence_classes = [_clean_text(record.get("evidence_class")) for record in record_evaluations]
	return {
		"type": MANUAL_UAT_PROMOTION_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"promotion_id": _clean_text(promotion_id),
		"generated_at": _clean_text(generated_at) or _utc_now(),
		"reviewer": _clean_text(reviewer),
		"json_artifact_path": _clean_text(json_artifact_path),
		"markdown_artifact_path": _clean_text(markdown_artifact_path),
		"json_artifact_written": False,
		"markdown_artifact_written": False,
		"source_contract_type": _source_contract_type(source),
		"source_bundle_type": _clean_text(bundle.get("type")) or "unknown",
		"source_bundle_id": _clean_text(bundle.get("bundle_id")),
		"source_bundle_roundtrip_complete": bundle_roundtrip_complete,
		"source_bundle_release_ready": bundle_release_ready,
		"expected_scenario_ids": _clean_list(bundle.get("expected_scenario_ids")),
		"expected_scenario_count": int(bundle.get("expected_scenario_count") or 0),
		"capture_record_count": len(source_records),
		"evidence_class_counts": _count_values(evidence_classes),
		"evidence_mode_counts": _count_values([record.get("evidence_mode") for record in source_records]),
		"capture_source_counts": _count_values([record.get("capture_source") for record in source_records]),
		"promotion_eligible": promotion_eligible,
		"release_ready": promotion_eligible,
		"release_boundary": "none" if promotion_eligible else PROMOTION_RELEASE_BOUNDARY,
		"promotion_blocking_reasons": blocking_reasons,
		"record_evaluations": record_evaluations,
		"sample_record_ids": [
			_clean_text(record.get("scenario_id"))
			for record in record_evaluations
			if _clean_text(record.get("evidence_class")) == EVIDENCE_CLASS_SAMPLE_FIXTURE
		],
		"operator_record_ids": [
			_clean_text(record.get("scenario_id"))
			for record in record_evaluations
			if _clean_text(record.get("evidence_class")) == EVIDENCE_CLASS_OPERATOR_CAPTURED
		],
		"unsafe_record_ids": [
			_clean_text(record.get("scenario_id"))
			for record in record_evaluations
			if _clean_text(record.get("evidence_class")) == EVIDENCE_CLASS_UNKNOWN_OR_UNSAFE
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


def render_manual_uat_evidence_promotion_markdown(promotion_report: Dict[str, Any]) -> str:
	report = dict(promotion_report or {})
	lines: List[str] = ["# S7 Manual UAT Evidence Promotion Report", ""]
	lines.append("## Promotion Metadata")
	lines.append("")
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"promotion_id",
		"generated_at",
		"reviewer",
		"source_contract_type",
		"source_bundle_type",
		"source_bundle_id",
		"source_bundle_roundtrip_complete",
		"source_bundle_release_ready",
		"expected_scenario_count",
		"capture_record_count",
		"promotion_eligible",
		"release_ready",
		"release_boundary",
		"json_artifact_path",
		"markdown_artifact_path",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(report.get(field))} |")
	lines.extend(["", "## Promotion Boundary", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Blocking reasons | {_md_cell(_join(report.get('promotion_blocking_reasons')))} |")
	lines.append(f"| Sample records | {_md_cell(_join(report.get('sample_record_ids')))} |")
	lines.append(f"| Operator records | {_md_cell(_join(report.get('operator_record_ids')))} |")
	lines.append(f"| Unsafe records | {_md_cell(_join(report.get('unsafe_record_ids')))} |")
	lines.extend(["", "## Record Evaluation", ""])
	lines.append("| Scenario | Class | Mode | Source | Intent | Attested | Import | Archive complete | Promotion | Blocking reasons |")
	lines.append("|---|---|---|---|---|---|---|---|---|---|")
	for record in report.get("record_evaluations") or []:
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
					_md_cell(record.get("promotion_intent")),
					_md_cell(record.get("operator_attestation_present")),
					_md_cell(record.get("import_parse_status")),
					_md_cell(record.get("archive_complete")),
					_md_cell(record.get("promotion_eligible")),
					_md_cell(_join(record.get("blocking_reasons"))),
				]
			)
			+ " |"
		)
	if not report.get("record_evaluations"):
		lines.append("| none | none | none | none | none | False | none | False | False | source_capture_records_missing |")
	return "\n".join(lines).strip() + "\n"


def write_manual_uat_evidence_promotion_files(
	source_contract: Dict[str, Any] | None = None,
	*,
	json_path: str = DEFAULT_MANUAL_UAT_PROMOTION_JSON_PATH,
	markdown_path: str = DEFAULT_MANUAL_UAT_PROMOTION_MARKDOWN_PATH,
	promotion_id: str = "s7_manual_uat_evidence_promotion",
	generated_at: str = "",
	reviewer: str = "",
) -> Dict[str, Any]:
	report = build_manual_uat_evidence_promotion_report(
		source_contract,
		promotion_id=promotion_id,
		generated_at=generated_at,
		reviewer=reviewer,
		json_artifact_path=json_path,
		markdown_artifact_path=markdown_path,
	)
	json_target = Path(report["json_artifact_path"])
	markdown_target = Path(report["markdown_artifact_path"])
	if not json_target.is_absolute():
		json_target = Path.cwd() / json_target
	if not markdown_target.is_absolute():
		markdown_target = Path.cwd() / markdown_target
	json_target.parent.mkdir(parents=True, exist_ok=True)
	markdown_target.parent.mkdir(parents=True, exist_ok=True)
	json_target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_target.write_text(render_manual_uat_evidence_promotion_markdown(report), encoding="utf-8")
	written = dict(report)
	written["json_artifact_path"] = str(json_target)
	written["markdown_artifact_path"] = str(markdown_target)
	written["json_artifact_written"] = json_target.exists()
	written["markdown_artifact_written"] = markdown_target.exists()
	written["json_artifact_size_bytes"] = json_target.stat().st_size if json_target.exists() else 0
	written["markdown_artifact_size_bytes"] = markdown_target.stat().st_size if markdown_target.exists() else 0
	return written
