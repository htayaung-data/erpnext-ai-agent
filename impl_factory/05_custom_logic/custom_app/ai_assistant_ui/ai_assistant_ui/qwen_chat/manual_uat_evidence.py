from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Iterable, List

from .natural_business_understanding_contracts import CONTRACT_VERSION
from .regression_scenario_packs import (
	EXECUTION_DETERMINISTIC_CONTRACT,
	EXECUTION_MANUAL_BROWSER_UAT,
	build_regression_scenario_contract,
	build_regression_scenario_pack_contract,
)
from .regression_suite_governance import BLOCKING_MANUAL, BLOCKING_RELEASE


MANUAL_UAT_CHECKLIST_CONTRACT_TYPE = "qwen_manual_uat_checklist_contract"
MANUAL_UAT_CHECKLIST_ROW_CONTRACT_TYPE = "qwen_manual_uat_checklist_row_contract"
MANUAL_UAT_EVIDENCE_CONTRACT_TYPE = "qwen_manual_uat_evidence_contract"
MANUAL_UAT_RELEASE_SUMMARY_CONTRACT_TYPE = "qwen_manual_uat_release_summary_contract"

MANUAL_UAT_EVIDENCE_SUITE_ID = "s7_manual_uat_evidence_contracts"

MANUAL_UAT_STATUS_PASS = "pass"
MANUAL_UAT_STATUS_FAIL = "fail"
MANUAL_UAT_STATUS_BLOCKED = "blocked"
MANUAL_UAT_STATUS_NOT_RUN = "not_run"
VALID_MANUAL_UAT_STATUSES = {
	MANUAL_UAT_STATUS_PASS,
	MANUAL_UAT_STATUS_FAIL,
	MANUAL_UAT_STATUS_BLOCKED,
	MANUAL_UAT_STATUS_NOT_RUN,
}

REQUIRED_CHECKLIST_ROW_FIELDS = [
	"scenario_id",
	"pack_id",
	"manual_uat_prompt",
	"expected_route",
	"expected_artifact_family",
	"expected_entity_type",
	"expected_row_reference",
	"expected_authority_source",
	"expected_policy_boundary",
	"expected_model_role_lane",
	"expected_answer_mode",
	"pass_criteria",
	"blocking_level",
	"execution_mode",
]

REQUIRED_EVIDENCE_FIELDS = [
	"scenario_id",
	"pack_id",
	"manual_uat_prompt",
	"expected_route",
	"expected_artifact_family",
	"expected_entity_type",
	"expected_row_reference",
	"expected_authority_source",
	"expected_policy_boundary",
	"expected_model_role_lane",
	"expected_answer_mode",
	"observed_answer_summary",
	"observed_trace_fields",
	"observed_model_role_fields",
	"uat_status",
	"blocking_level",
	"failure_reason",
	"reviewed_at",
]

REQUIRED_OBSERVED_TRACE_KEYS = [
	"route",
	"artifact_family",
	"entity_type",
	"row_reference",
	"authority_source",
	"policy_boundary",
	"answer_mode",
]

REQUIRED_OBSERVED_MODEL_ROLE_KEYS = [
	"model_role_lane",
	"lane",
	"model_role",
	"expected_model_role",
	"role_compliance",
]


_EXPECTED_TO_OBSERVED_TRACE_KEYS = {
	"expected_route": "route",
	"expected_artifact_family": "artifact_family",
	"expected_entity_type": "entity_type",
	"expected_row_reference": "row_reference",
	"expected_authority_source": "authority_source",
	"expected_policy_boundary": "policy_boundary",
	"expected_answer_mode": "answer_mode",
}


_WILDCARD_EXPECTED_VALUES = {
	"varies_by_scenario",
	"scenario_declared_authority",
	"scenario_declared_boundary",
	"scenario_declared_model_role_lane",
	"selected_visible_artifact",
	"selected_visible_entity_type",
	"selected_visible_row_reference",
	"none_or_selected_boundary",
}


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


def _scenario_value(scenario: Dict[str, Any], key: str) -> Any:
	if key in scenario:
		return scenario.get(key)
	expected = _clean_dict(scenario.get("expected"))
	return expected.get(key)


def _normalized_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
	if _clean_text(scenario.get("type")):
		return dict(scenario)
	return build_regression_scenario_contract(scenario)


def _missing_checklist_fields(row: Dict[str, Any]) -> List[str]:
	missing: List[str] = []
	for field in REQUIRED_CHECKLIST_ROW_FIELDS:
		value = row.get(field)
		if field == "pass_criteria":
			if not _clean_list(value):
				missing.append(field)
		elif not _clean_text(value):
			missing.append(field)
	return missing


def build_manual_uat_checklist_row(scenario: Dict[str, Any]) -> Dict[str, Any]:
	entry = _normalized_scenario(scenario)
	execution_mode = _clean_text(entry.get("execution_mode")) or EXECUTION_DETERMINISTIC_CONTRACT
	blocking_level = _clean_text(entry.get("blocking_level"))
	row = {
		"type": MANUAL_UAT_CHECKLIST_ROW_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"scenario_id": _clean_text(entry.get("scenario_id")),
		"pack_id": _clean_text(entry.get("pack_id")),
		"family": _clean_text(entry.get("family")),
		"turns": _clean_list(entry.get("turns")),
		"manual_uat_prompt": _clean_text(entry.get("manual_uat_prompt")),
		"expected_route": _clean_text(_scenario_value(entry, "expected_route")),
		"expected_artifact_family": _clean_text(_scenario_value(entry, "expected_artifact_family")),
		"expected_entity_type": _clean_text(_scenario_value(entry, "expected_entity_type")),
		"expected_row_reference": _clean_text(_scenario_value(entry, "expected_row_reference")),
		"expected_authority_source": _clean_text(_scenario_value(entry, "expected_authority_source")),
		"expected_policy_boundary": _clean_text(_scenario_value(entry, "expected_policy_boundary")),
		"expected_model_role_lane": _clean_text(_scenario_value(entry, "expected_model_role_lane")),
		"expected_answer_mode": _clean_text(_scenario_value(entry, "expected_answer_mode")),
		"pass_criteria": _clean_list(entry.get("pass_criteria")),
		"blocking_level": blocking_level,
		"execution_mode": execution_mode,
		"manual_only": execution_mode == EXECUTION_MANUAL_BROWSER_UAT,
		"deterministic_reference": execution_mode == EXECUTION_DETERMINISTIC_CONTRACT,
		"release_blocking_reference": blocking_level == BLOCKING_RELEASE,
		"manual_acceptance_required": blocking_level == BLOCKING_MANUAL or execution_mode == EXECUTION_MANUAL_BROWSER_UAT,
	}
	missing_fields = _missing_checklist_fields(row)
	row["missing_fields"] = missing_fields
	row["row_complete"] = not missing_fields
	return row


def build_manual_uat_checklist_contract(
	*,
	registry: Iterable[Dict[str, Any]] | None = None,
	contract_owner: str = "s7_manual_uat_evidence_contract",
	created_at: str = "",
) -> Dict[str, Any]:
	pack_contract = build_regression_scenario_pack_contract(registry=registry)
	rows = [build_manual_uat_checklist_row(scenario) for scenario in pack_contract.get("scenarios", [])]
	manual_rows = [row for row in rows if bool(row.get("manual_only"))]
	deterministic_rows = [row for row in rows if bool(row.get("deterministic_reference"))]
	incomplete_rows = [_clean_text(row.get("scenario_id")) or "unknown" for row in rows if not row.get("row_complete")]
	return {
		"type": MANUAL_UAT_CHECKLIST_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"source_scenario_pack_type": pack_contract.get("type"),
		"source_scenario_pack_complete": bool(pack_contract.get("contract_complete")),
		"contract_complete": bool(pack_contract.get("contract_complete")) and not incomplete_rows and bool(rows),
		"row_count": len(rows),
		"manual_only_row_count": len(manual_rows),
		"deterministic_reference_row_count": len(deterministic_rows),
		"manual_only_scenario_ids": [_clean_text(row.get("scenario_id")) for row in manual_rows],
		"deterministic_reference_scenario_ids": [_clean_text(row.get("scenario_id")) for row in deterministic_rows],
		"incomplete_rows": incomplete_rows,
		"rows": rows,
		"created_at": _clean_text(created_at) or _utc_now(),
	}


def _observed_model_role_lane(observed_model_role_fields: Dict[str, Any]) -> str:
	explicit = _clean_text(observed_model_role_fields.get("model_role_lane"))
	if explicit:
		return explicit
	lane = _clean_text(observed_model_role_fields.get("lane"))
	role = _clean_text(observed_model_role_fields.get("model_role"))
	if lane and role:
		return f"{lane}:{role}"
	return ""


def _expected_matches(expected: str, observed: str) -> bool:
	expected_text = _clean_text(expected)
	observed_text = _clean_text(observed)
	if not expected_text:
		return True
	if expected_text in _WILDCARD_EXPECTED_VALUES:
		return bool(observed_text)
	return expected_text == observed_text


def _evidence_missing_fields(record: Dict[str, Any]) -> List[str]:
	missing: List[str] = []
	status = _clean_text(record.get("uat_status"))
	for field in REQUIRED_EVIDENCE_FIELDS:
		if field in {"observed_trace_fields", "observed_model_role_fields"}:
			if status == MANUAL_UAT_STATUS_PASS and not _clean_dict(record.get(field)):
				missing.append(field)
		elif field in {"observed_answer_summary", "reviewed_at"}:
			if status in {MANUAL_UAT_STATUS_PASS, MANUAL_UAT_STATUS_FAIL, MANUAL_UAT_STATUS_BLOCKED} and not _clean_text(record.get(field)):
				missing.append(field)
		elif field == "failure_reason":
			if status in {MANUAL_UAT_STATUS_FAIL, MANUAL_UAT_STATUS_BLOCKED} and not _clean_text(record.get(field)):
				missing.append(field)
		elif not _clean_text(record.get(field)):
			missing.append(field)
	if status == MANUAL_UAT_STATUS_PASS:
		trace_fields = _clean_dict(record.get("observed_trace_fields"))
		model_fields = _clean_dict(record.get("observed_model_role_fields"))
		missing.extend([f"observed_trace_fields.{key}" for key in REQUIRED_OBSERVED_TRACE_KEYS if not _clean_text(trace_fields.get(key))])
		missing.extend([f"observed_model_role_fields.{key}" for key in REQUIRED_OBSERVED_MODEL_ROLE_KEYS if not _clean_text(model_fields.get(key))])
	return missing


def _field_mismatches(record: Dict[str, Any]) -> List[Dict[str, str]]:
	if _clean_text(record.get("uat_status")) != MANUAL_UAT_STATUS_PASS:
		return []
	mismatches: List[Dict[str, str]] = []
	trace_fields = _clean_dict(record.get("observed_trace_fields"))
	for expected_key, observed_key in _EXPECTED_TO_OBSERVED_TRACE_KEYS.items():
		expected = _clean_text(record.get(expected_key))
		observed = _clean_text(trace_fields.get(observed_key))
		if not _expected_matches(expected, observed):
			mismatches.append({"field": expected_key, "expected": expected, "observed": observed})
	model_fields = _clean_dict(record.get("observed_model_role_fields"))
	expected_role_lane = _clean_text(record.get("expected_model_role_lane"))
	observed_role_lane = _observed_model_role_lane(model_fields)
	if not _expected_matches(expected_role_lane, observed_role_lane):
		mismatches.append(
			{"field": "expected_model_role_lane", "expected": expected_role_lane, "observed": observed_role_lane}
		)
	return mismatches


def build_manual_uat_evidence_record(
	scenario: Dict[str, Any],
	*,
	observed_answer_summary: str = "",
	observed_trace_fields: Dict[str, Any] | None = None,
	observed_model_role_fields: Dict[str, Any] | None = None,
	uat_status: str = MANUAL_UAT_STATUS_NOT_RUN,
	failure_reason: str = "",
	reviewed_at: str = "",
	reviewer: str = "",
) -> Dict[str, Any]:
	row = build_manual_uat_checklist_row(scenario)
	status = _clean_text(uat_status) or MANUAL_UAT_STATUS_NOT_RUN
	record = {
		"type": MANUAL_UAT_EVIDENCE_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"scenario_id": row.get("scenario_id"),
		"pack_id": row.get("pack_id"),
		"family": row.get("family"),
		"turns": list(row.get("turns") or []),
		"manual_uat_prompt": row.get("manual_uat_prompt"),
		"expected_route": row.get("expected_route"),
		"expected_artifact_family": row.get("expected_artifact_family"),
		"expected_entity_type": row.get("expected_entity_type"),
		"expected_row_reference": row.get("expected_row_reference"),
		"expected_authority_source": row.get("expected_authority_source"),
		"expected_policy_boundary": row.get("expected_policy_boundary"),
		"expected_model_role_lane": row.get("expected_model_role_lane"),
		"expected_answer_mode": row.get("expected_answer_mode"),
		"pass_criteria": list(row.get("pass_criteria") or []),
		"observed_answer_summary": _clean_text(observed_answer_summary),
		"observed_trace_fields": _clean_dict(observed_trace_fields),
		"observed_model_role_fields": _clean_dict(observed_model_role_fields),
		"uat_status": status,
		"status_valid": status in VALID_MANUAL_UAT_STATUSES,
		"blocking_level": row.get("blocking_level"),
		"failure_reason": _clean_text(failure_reason),
		"reviewed_at": _clean_text(reviewed_at),
		"reviewer": _clean_text(reviewer),
		"manual_only": bool(row.get("manual_only")),
		"deterministic_reference": bool(row.get("deterministic_reference")),
	}
	missing_fields = _evidence_missing_fields(record)
	field_mismatches = _field_mismatches(record)
	record["missing_fields"] = missing_fields
	record["field_mismatches"] = field_mismatches
	record["evidence_complete"] = bool(
		record["status_valid"]
		and status == MANUAL_UAT_STATUS_PASS
		and not missing_fields
		and not field_mismatches
	)
	record["release_blocking_failure"] = bool(
		row.get("blocking_level") in {BLOCKING_RELEASE, BLOCKING_MANUAL}
		and (status != MANUAL_UAT_STATUS_PASS or bool(missing_fields) or bool(field_mismatches) or not record["status_valid"])
	)
	return record


def build_manual_uat_release_summary(
	*,
	evidence_records: Iterable[Dict[str, Any]],
	registry: Iterable[Dict[str, Any]] | None = None,
	expected_scenario_ids: Iterable[str] | None = None,
	contract_owner: str = "s7_manual_uat_evidence_contract",
	created_at: str = "",
) -> Dict[str, Any]:
	created_at_text = _clean_text(created_at) or _utc_now()
	checklist = build_manual_uat_checklist_contract(registry=registry, created_at=created_at_text)
	all_expected_ids = [_clean_text(row.get("scenario_id")) for row in checklist.get("rows", [])]
	expected_ids = [_clean_text(value) for value in expected_scenario_ids] if expected_scenario_ids is not None else all_expected_ids
	expected_ids = [value for value in expected_ids if value]
	records = [dict(record) for record in evidence_records if isinstance(record, dict)]
	records_by_id: Dict[str, Dict[str, Any]] = {}
	duplicate_evidence_ids: List[str] = []
	for record in records:
		scenario_id = _clean_text(record.get("scenario_id"))
		if not scenario_id:
			continue
		if scenario_id in records_by_id:
			duplicate_evidence_ids.append(scenario_id)
		records_by_id[scenario_id] = record
	missing_evidence_ids = [scenario_id for scenario_id in expected_ids if scenario_id not in records_by_id]
	status_counts = {status: 0 for status in sorted(VALID_MANUAL_UAT_STATUSES)}
	invalid_status_ids: List[str] = []
	incomplete_evidence_ids: List[str] = []
	field_mismatch_ids: List[str] = []
	blocking_failure_ids: List[str] = []
	for scenario_id in expected_ids:
		record = records_by_id.get(scenario_id)
		if not record:
			continue
		status = _clean_text(record.get("uat_status"))
		if status in status_counts:
			status_counts[status] += 1
		else:
			invalid_status_ids.append(scenario_id)
		if not bool(record.get("evidence_complete")):
			incomplete_evidence_ids.append(scenario_id)
		if record.get("field_mismatches"):
			field_mismatch_ids.append(scenario_id)
		if bool(record.get("release_blocking_failure")):
			blocking_failure_ids.append(scenario_id)
	blocking_failure_ids.extend(missing_evidence_ids)
	blocking_failure_ids.extend(invalid_status_ids)
	blocking_failure_ids.extend(duplicate_evidence_ids)
	blocking_failure_ids = sorted(set(blocking_failure_ids))
	release_ready = bool(expected_ids) and not blocking_failure_ids and not incomplete_evidence_ids and not missing_evidence_ids
	return {
		"type": MANUAL_UAT_RELEASE_SUMMARY_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"checklist_contract_complete": bool(checklist.get("contract_complete")),
		"expected_scenario_count": len(expected_ids),
		"evidence_record_count": len(records),
		"release_ready": release_ready,
		"status_counts": status_counts,
		"missing_evidence_scenario_ids": missing_evidence_ids,
		"invalid_status_scenario_ids": sorted(set(invalid_status_ids)),
		"incomplete_evidence_scenario_ids": sorted(set(incomplete_evidence_ids)),
		"field_mismatch_scenario_ids": sorted(set(field_mismatch_ids)),
		"duplicate_evidence_scenario_ids": sorted(set(duplicate_evidence_ids)),
		"blocking_failure_scenario_ids": blocking_failure_ids,
		"manual_only_scenario_ids": checklist.get("manual_only_scenario_ids") or [],
		"deterministic_reference_scenario_ids": checklist.get("deterministic_reference_scenario_ids") or [],
		"created_at": created_at_text,
	}
