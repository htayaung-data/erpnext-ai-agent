from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .manual_uat_evidence import (
	MANUAL_UAT_EVIDENCE_CONTRACT_TYPE,
	MANUAL_UAT_RELEASE_SUMMARY_CONTRACT_TYPE,
	MANUAL_UAT_STATUS_BLOCKED,
	MANUAL_UAT_STATUS_FAIL,
	MANUAL_UAT_STATUS_NOT_RUN,
	MANUAL_UAT_STATUS_PASS,
	VALID_MANUAL_UAT_STATUSES,
	build_manual_uat_evidence_record,
	build_manual_uat_release_summary,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .regression_scenario_packs import (
	S7_REGRESSION_SCENARIO_REGISTRY,
	build_regression_scenario_contract,
)
from .regression_suite_governance import BLOCKING_MANUAL, BLOCKING_RELEASE


MANUAL_UAT_ARCHIVE_RECORD_CONTRACT_TYPE = "qwen_manual_uat_archive_record_contract"
MANUAL_UAT_ARCHIVE_INDEX_CONTRACT_TYPE = "qwen_manual_uat_archive_index_contract"
MANUAL_UAT_ARCHIVE_SUITE_ID = "s7_manual_uat_evidence_archive_contracts"

DEFAULT_MANUAL_UAT_ARCHIVE_JSON_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_evidence_archive.json"
)
DEFAULT_MANUAL_UAT_ARCHIVE_MARKDOWN_PATH = (
	"impl_factory/00_governance/current_docs/generated/"
	"qwen_s7_manual_uat_evidence_archive.md"
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


def _scenario_map(registry: Iterable[Dict[str, Any]] | None = None) -> Dict[str, Dict[str, Any]]:
	scenarios: Dict[str, Dict[str, Any]] = {}
	for entry in registry or S7_REGRESSION_SCENARIO_REGISTRY:
		if not isinstance(entry, dict):
			continue
		scenario = build_regression_scenario_contract(entry)
		scenario_id = _clean_text(scenario.get("scenario_id"))
		if scenario_id:
			scenarios[scenario_id] = scenario
	return scenarios


def _scenario_ids(registry: Iterable[Dict[str, Any]] | None = None) -> List[str]:
	return list(_scenario_map(registry).keys())


def _input_status(import_record: Dict[str, Any], default_status: str = MANUAL_UAT_STATUS_NOT_RUN) -> str:
	return _clean_text(import_record.get("uat_status")) or _clean_text(import_record.get("status")) or default_status


def _observed_model_role_lane(observed_model_role_fields: Dict[str, Any]) -> str:
	explicit = _clean_text(observed_model_role_fields.get("model_role_lane"))
	if explicit:
		return explicit
	lane = _clean_text(observed_model_role_fields.get("lane"))
	model_role = _clean_text(observed_model_role_fields.get("model_role"))
	if lane and model_role:
		return f"{lane}:{model_role}"
	return ""


def _archive_status_counts(records: List[Dict[str, Any]]) -> Dict[str, int]:
	counts = {status: 0 for status in sorted(VALID_MANUAL_UAT_STATUSES)}
	for record in records:
		status = _clean_text(record.get("status"))
		if status in counts:
			counts[status] += 1
	return counts


def _duplicate_values(values: List[str]) -> List[str]:
	return sorted({value for value in values if value and values.count(value) > 1})


def _unknown_scenario_record(
	import_record: Dict[str, Any],
	*,
	reviewed_at: str,
	reviewer: str,
) -> Dict[str, Any]:
	scenario_id = _clean_text(import_record.get("scenario_id")) or "unknown"
	status = _input_status(import_record, default_status=MANUAL_UAT_STATUS_BLOCKED)
	observed_trace_fields = _clean_dict(import_record.get("observed_trace_fields"))
	observed_model_role_fields = _clean_dict(import_record.get("observed_model_role_fields"))
	missing_fields = ["registered_scenario"]
	mismatches = [
		{
			"field": "scenario_id",
			"expected": "registered_s7_scenario_id",
			"observed": scenario_id,
		}
	]
	return {
		"type": MANUAL_UAT_ARCHIVE_RECORD_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"archive_id": f"manual-uat:{scenario_id}",
		"scenario_id": scenario_id,
		"scenario_registered": False,
		"unknown_scenario": True,
		"scenario_pack": "",
		"family": "",
		"reviewer": _clean_text(import_record.get("reviewer")) or _clean_text(reviewer),
		"reviewed_at": _clean_text(import_record.get("reviewed_at")) or _clean_text(reviewed_at),
		"status": status,
		"status_valid": status in VALID_MANUAL_UAT_STATUSES,
		"blocking_level": BLOCKING_RELEASE,
		"answer_evidence_present": bool(_clean_text(import_record.get("observed_answer_summary"))),
		"trace_evidence_present": bool(observed_trace_fields),
		"model_role_evidence_present": bool(observed_model_role_fields),
		"policy_evidence_present": bool(_clean_text(observed_trace_fields.get("policy_boundary"))),
		"authority_evidence_present": bool(_clean_text(observed_trace_fields.get("authority_source"))),
		"observed_answer_mode": _clean_text(observed_trace_fields.get("answer_mode")),
		"observed_policy_boundary": _clean_text(observed_trace_fields.get("policy_boundary")),
		"observed_authority_source": _clean_text(observed_trace_fields.get("authority_source")),
		"observed_entity_type": _clean_text(observed_trace_fields.get("entity_type")),
		"observed_row_reference": _clean_text(observed_trace_fields.get("row_reference")),
		"observed_model_role": _clean_text(observed_model_role_fields.get("model_role")),
		"observed_model_role_lane": _observed_model_role_lane(observed_model_role_fields),
		"expected_answer_mode": "",
		"expected_policy_boundary": "",
		"expected_model_role_lane": "",
		"expected_authority_source": "",
		"expected_entity_type": "",
		"expected_row_reference": "",
		"mismatches": mismatches,
		"missing_fields": missing_fields,
		"release_blocking": True,
		"archive_complete": False,
		"evidence_record": {},
	}


def build_manual_uat_archive_record(
	import_record: Dict[str, Any],
	*,
	registry: Iterable[Dict[str, Any]] | None = None,
	reviewed_at: str = "",
	reviewer: str = "",
) -> Dict[str, Any]:
	"""Build one archived UAT evidence row from the scenario registry and observed evidence."""
	source = dict(import_record or {})
	scenario_id = _clean_text(source.get("scenario_id"))
	scenario = _scenario_map(registry).get(scenario_id)
	record_reviewed_at = _clean_text(source.get("reviewed_at")) or _clean_text(reviewed_at) or _utc_now()
	record_reviewer = _clean_text(source.get("reviewer")) or _clean_text(reviewer)
	if not scenario:
		return _unknown_scenario_record(source, reviewed_at=record_reviewed_at, reviewer=record_reviewer)

	observed_trace_fields = _clean_dict(source.get("observed_trace_fields"))
	observed_model_role_fields = _clean_dict(source.get("observed_model_role_fields"))
	status = _input_status(source)
	evidence_record = build_manual_uat_evidence_record(
		scenario,
		observed_answer_summary=_clean_text(source.get("observed_answer_summary")),
		observed_trace_fields=observed_trace_fields,
		observed_model_role_fields=observed_model_role_fields,
		uat_status=status,
		failure_reason=_clean_text(source.get("failure_reason")),
		reviewed_at=record_reviewed_at,
		reviewer=record_reviewer,
	)
	blocking_level = _clean_text(evidence_record.get("blocking_level"))
	release_blocking = bool(
		evidence_record.get("release_blocking_failure")
		or (
			blocking_level in {BLOCKING_RELEASE, BLOCKING_MANUAL}
			and not bool(evidence_record.get("evidence_complete"))
		)
	)
	return {
		"type": MANUAL_UAT_ARCHIVE_RECORD_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"archive_id": f"manual-uat:{scenario_id}",
		"scenario_id": scenario_id,
		"scenario_registered": True,
		"unknown_scenario": False,
		"scenario_pack": _clean_text(evidence_record.get("pack_id")),
		"family": _clean_text(evidence_record.get("family")),
		"reviewer": record_reviewer,
		"reviewed_at": record_reviewed_at,
		"status": status,
		"status_valid": bool(evidence_record.get("status_valid")),
		"blocking_level": blocking_level,
		"manual_only": bool(evidence_record.get("manual_only")),
		"deterministic_reference": bool(evidence_record.get("deterministic_reference")),
		"answer_evidence_present": bool(_clean_text(evidence_record.get("observed_answer_summary"))),
		"trace_evidence_present": bool(observed_trace_fields),
		"model_role_evidence_present": bool(observed_model_role_fields),
		"policy_evidence_present": bool(_clean_text(observed_trace_fields.get("policy_boundary"))),
		"authority_evidence_present": bool(_clean_text(observed_trace_fields.get("authority_source"))),
		"observed_answer_mode": _clean_text(observed_trace_fields.get("answer_mode")),
		"observed_policy_boundary": _clean_text(observed_trace_fields.get("policy_boundary")),
		"observed_authority_source": _clean_text(observed_trace_fields.get("authority_source")),
		"observed_entity_type": _clean_text(observed_trace_fields.get("entity_type")),
		"observed_row_reference": _clean_text(observed_trace_fields.get("row_reference")),
		"observed_model_role": _clean_text(observed_model_role_fields.get("model_role")),
		"observed_model_role_lane": _observed_model_role_lane(observed_model_role_fields),
		"expected_answer_mode": _clean_text(evidence_record.get("expected_answer_mode")),
		"expected_policy_boundary": _clean_text(evidence_record.get("expected_policy_boundary")),
		"expected_model_role_lane": _clean_text(evidence_record.get("expected_model_role_lane")),
		"expected_authority_source": _clean_text(evidence_record.get("expected_authority_source")),
		"expected_entity_type": _clean_text(evidence_record.get("expected_entity_type")),
		"expected_row_reference": _clean_text(evidence_record.get("expected_row_reference")),
		"mismatches": list(evidence_record.get("field_mismatches") or []),
		"missing_fields": list(evidence_record.get("missing_fields") or []),
		"release_blocking": release_blocking,
		"archive_complete": bool(evidence_record.get("evidence_complete")),
		"evidence_record": evidence_record,
	}


def build_manual_uat_archive_index(
	import_records: Iterable[Dict[str, Any]] | None = None,
	*,
	registry: Iterable[Dict[str, Any]] | None = None,
	expected_scenario_ids: Iterable[str] | None = None,
	archive_id: str = "s7_manual_uat_evidence_archive",
	generated_at: str = "",
	reviewer: str = "",
	json_artifact_path: str = DEFAULT_MANUAL_UAT_ARCHIVE_JSON_PATH,
	markdown_artifact_path: str = DEFAULT_MANUAL_UAT_ARCHIVE_MARKDOWN_PATH,
	contract_owner: str = "s7_manual_uat_evidence_archive",
) -> Dict[str, Any]:
	generated_at_text = _clean_text(generated_at) or _utc_now()
	records = [
		build_manual_uat_archive_record(record, registry=registry, reviewed_at=generated_at_text, reviewer=reviewer)
		for record in _clean_records(import_records)
	]
	expected_ids = (
		[_clean_text(value) for value in expected_scenario_ids if _clean_text(value)]
		if expected_scenario_ids is not None
		else _scenario_ids(registry)
	)
	registered_evidence_records = [
		record.get("evidence_record")
		for record in records
		if bool(record.get("scenario_registered")) and isinstance(record.get("evidence_record"), dict)
	]
	release_summary = build_manual_uat_release_summary(
		evidence_records=registered_evidence_records,
		registry=registry,
		expected_scenario_ids=expected_ids,
		contract_owner=contract_owner,
		created_at=generated_at_text,
	)
	archive_scenario_ids = [_clean_text(record.get("scenario_id")) for record in records]
	duplicate_archive_record_ids = _duplicate_values(archive_scenario_ids)
	unknown_scenario_ids = sorted(
		{
			_clean_text(record.get("scenario_id"))
			for record in records
			if bool(record.get("unknown_scenario"))
		}
	)
	archive_incomplete_ids = sorted(
		{
			_clean_text(record.get("scenario_id"))
			for record in records
			if not bool(record.get("archive_complete"))
		}
	)
	blocking_failure_ids = sorted(
		set(_clean_list(release_summary.get("blocking_failure_scenario_ids")))
		| set(unknown_scenario_ids)
		| set(duplicate_archive_record_ids)
	)
	status_counts = _archive_status_counts(records)
	archive_complete = bool(
		release_summary.get("checklist_contract_complete")
		and not unknown_scenario_ids
		and not duplicate_archive_record_ids
	)
	release_ready = bool(release_summary.get("release_ready") and archive_complete)
	return {
		"type": MANUAL_UAT_ARCHIVE_INDEX_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"archive_id": _clean_text(archive_id),
		"generated_at": generated_at_text,
		"reviewer": _clean_text(reviewer),
		"source_evidence_contract": MANUAL_UAT_EVIDENCE_CONTRACT_TYPE,
		"source_release_summary_contract": MANUAL_UAT_RELEASE_SUMMARY_CONTRACT_TYPE,
		"json_artifact_path": _clean_text(json_artifact_path),
		"markdown_artifact_path": _clean_text(markdown_artifact_path),
		"json_artifact_written": False,
		"markdown_artifact_written": False,
		"expected_scenario_count": len(expected_ids),
		"expected_scenario_ids": expected_ids,
		"archived_record_count": len(records),
		"registered_record_count": len([record for record in records if bool(record.get("scenario_registered"))]),
		"unknown_record_count": len(unknown_scenario_ids),
		"passed_scenario_count": status_counts.get(MANUAL_UAT_STATUS_PASS, 0),
		"failed_scenario_count": status_counts.get(MANUAL_UAT_STATUS_FAIL, 0),
		"blocked_scenario_count": status_counts.get(MANUAL_UAT_STATUS_BLOCKED, 0),
		"not_run_scenario_count": status_counts.get(MANUAL_UAT_STATUS_NOT_RUN, 0),
		"status_counts": status_counts,
		"unknown_scenario_ids": unknown_scenario_ids,
		"duplicate_archive_record_ids": duplicate_archive_record_ids,
		"archive_incomplete_scenario_ids": archive_incomplete_ids,
		"missing_evidence_scenario_ids": _clean_list(release_summary.get("missing_evidence_scenario_ids")),
		"blocking_failure_scenario_ids": blocking_failure_ids,
		"release_ready": release_ready,
		"archive_complete": archive_complete,
		"release_summary_contract": release_summary,
		"records": records,
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


def render_manual_uat_archive_markdown(index_contract: Dict[str, Any]) -> str:
	contract = dict(index_contract or {})
	lines: List[str] = ["# S7 Manual UAT Evidence Archive", ""]
	lines.append("## Archive Metadata")
	lines.append("")
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for field in [
		"archive_id",
		"generated_at",
		"reviewer",
		"expected_scenario_count",
		"archived_record_count",
		"registered_record_count",
		"unknown_record_count",
		"archive_complete",
		"release_ready",
		"json_artifact_path",
		"markdown_artifact_path",
	]:
		lines.append(f"| {_md_cell(field)} | {_md_cell(contract.get(field))} |")
	lines.extend(["", "## Release Boundary", ""])
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	lines.append(f"| Missing evidence | {_md_cell(_join(contract.get('missing_evidence_scenario_ids')))} |")
	lines.append(f"| Blocking failures | {_md_cell(_join(contract.get('blocking_failure_scenario_ids')))} |")
	lines.append(f"| Unknown scenarios | {_md_cell(_join(contract.get('unknown_scenario_ids')))} |")
	lines.append(f"| Duplicate archive records | {_md_cell(_join(contract.get('duplicate_archive_record_ids')))} |")
	lines.append(f"| Archive incomplete scenarios | {_md_cell(_join(contract.get('archive_incomplete_scenario_ids')))} |")
	lines.extend(["", "## Status Counts", ""])
	lines.append("| Status | Count |")
	lines.append("|---|---:|")
	for status, count in sorted(_clean_dict(contract.get("status_counts")).items()):
		lines.append(f"| {_md_cell(status)} | {int(count or 0)} |")
	lines.extend(["", "## Archive Records", ""])
	lines.append(
		"| Scenario | Pack | Status | Release blocking | Archive complete | "
		"Policy | Authority | Model role lane | Missing | Mismatches |"
	)
	lines.append("|---|---|---|---|---|---|---|---|---|---|")
	for record in contract.get("records") or []:
		if not isinstance(record, dict):
			continue
		mismatch_fields = [
			_clean_text(mismatch.get("field"))
			for mismatch in record.get("mismatches") or []
			if isinstance(mismatch, dict)
		]
		lines.append(
			"| "
			+ " | ".join(
				[
					_md_cell(record.get("scenario_id")),
					_md_cell(record.get("scenario_pack")),
					_md_cell(record.get("status")),
					_md_cell(record.get("release_blocking")),
					_md_cell(record.get("archive_complete")),
					_md_cell(record.get("observed_policy_boundary") or record.get("expected_policy_boundary")),
					_md_cell(record.get("observed_authority_source") or record.get("expected_authority_source")),
					_md_cell(record.get("observed_model_role_lane") or record.get("expected_model_role_lane")),
					_md_cell(_join(record.get("missing_fields"))),
					_md_cell(_join(mismatch_fields)),
				]
			)
			+ " |"
		)
	if not contract.get("records"):
		lines.append("| none | none | none | False | False | none | none | none | none | none |")
	return "\n".join(lines).strip() + "\n"


def write_manual_uat_archive_files(
	import_records: Iterable[Dict[str, Any]] | None = None,
	*,
	json_path: str = DEFAULT_MANUAL_UAT_ARCHIVE_JSON_PATH,
	markdown_path: str = DEFAULT_MANUAL_UAT_ARCHIVE_MARKDOWN_PATH,
	registry: Iterable[Dict[str, Any]] | None = None,
	expected_scenario_ids: Iterable[str] | None = None,
	archive_id: str = "s7_manual_uat_evidence_archive",
	generated_at: str = "",
	reviewer: str = "",
) -> Dict[str, Any]:
	index = build_manual_uat_archive_index(
		import_records,
		registry=registry,
		expected_scenario_ids=expected_scenario_ids,
		archive_id=archive_id,
		generated_at=generated_at,
		reviewer=reviewer,
		json_artifact_path=json_path,
		markdown_artifact_path=markdown_path,
	)
	json_target = Path(index["json_artifact_path"])
	markdown_target = Path(index["markdown_artifact_path"])
	if not json_target.is_absolute():
		json_target = Path.cwd() / json_target
	if not markdown_target.is_absolute():
		markdown_target = Path.cwd() / markdown_target
	json_target.parent.mkdir(parents=True, exist_ok=True)
	markdown_target.parent.mkdir(parents=True, exist_ok=True)
	json_target.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_target.write_text(render_manual_uat_archive_markdown(index), encoding="utf-8")
	written = dict(index)
	written["json_artifact_path"] = str(json_target)
	written["markdown_artifact_path"] = str(markdown_target)
	written["json_artifact_written"] = json_target.exists()
	written["markdown_artifact_written"] = markdown_target.exists()
	written["json_artifact_size_bytes"] = json_target.stat().st_size if json_target.exists() else 0
	written["markdown_artifact_size_bytes"] = markdown_target.stat().st_size if markdown_target.exists() else 0
	return written
