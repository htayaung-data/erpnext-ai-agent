from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List

from .manual_uat_evidence import (
	MANUAL_UAT_CHECKLIST_CONTRACT_TYPE,
	MANUAL_UAT_EVIDENCE_CONTRACT_TYPE,
	MANUAL_UAT_RELEASE_SUMMARY_CONTRACT_TYPE,
)


MANUAL_UAT_RENDERER_SUITE_ID = "s7_manual_uat_renderer_contracts"


def _clean_text(value: Any) -> str:
	text = str(value or "").strip()
	return text or "missing"


def _clean_bool(value: Any) -> str:
	return "True" if bool(value) else "False"


def _clean_list(values: Any) -> List[str]:
	if not isinstance(values, list):
		return []
	return [str(value).strip() for value in values if str(value).strip()]


def _clean_dict(value: Any) -> Dict[str, Any]:
	return dict(value) if isinstance(value, dict) else {}


def _display_list(values: Any) -> str:
	items = _clean_list(values)
	return ", ".join(items) if items else "none"


def _append_kv_table(lines: List[str], rows: Iterable[tuple[str, Any]]) -> None:
	lines.append("| Field | Value |")
	lines.append("|---|---|")
	for key, value in rows:
		lines.append(f"| {key} | {_clean_text(value)} |")


def _append_list(lines: List[str], values: Any, *, empty_text: str = "none") -> None:
	items = _clean_list(values)
	if not items:
		lines.append(f"- {empty_text}")
		return
	for value in items:
		lines.append(f"- {value}")


def _append_dict_table(lines: List[str], values: Any) -> None:
	clean_values = _clean_dict(values)
	if not clean_values:
		lines.append("| Field | Value |")
		lines.append("|---|---|")
		lines.append("| none | missing |")
		return
	_append_kv_table(lines, sorted(clean_values.items()))


def _expected_rows(record: Dict[str, Any]) -> List[tuple[str, Any]]:
	return [
		("Expected route", record.get("expected_route")),
		("Expected artifact family", record.get("expected_artifact_family")),
		("Expected entity type", record.get("expected_entity_type")),
		("Expected row reference", record.get("expected_row_reference")),
		("Expected authority source", record.get("expected_authority_source")),
		("Expected policy boundary", record.get("expected_policy_boundary")),
		("Expected model-role lane", record.get("expected_model_role_lane")),
		("Expected answer mode", record.get("expected_answer_mode")),
	]


def render_manual_uat_checklist_markdown(checklist_contract: Dict[str, Any]) -> str:
	checklist = deepcopy(checklist_contract) if isinstance(checklist_contract, dict) else {}
	lines: List[str] = ["**Manual UAT Checklist**", ""]
	_append_kv_table(
		lines,
		[
			("Contract type", checklist.get("type") or MANUAL_UAT_CHECKLIST_CONTRACT_TYPE),
			("Contract complete", _clean_bool(checklist.get("contract_complete"))),
			("Source scenario pack complete", _clean_bool(checklist.get("source_scenario_pack_complete"))),
			("Row count", checklist.get("row_count")),
			("Manual-only row count", checklist.get("manual_only_row_count")),
			("Deterministic reference row count", checklist.get("deterministic_reference_row_count")),
			("Incomplete rows", _display_list(checklist.get("incomplete_rows"))),
		],
	)
	for row in checklist.get("rows") or []:
		if not isinstance(row, dict):
			continue
		lines.extend(["", f"### Scenario: {_clean_text(row.get('scenario_id'))}", ""])
		_append_kv_table(
			lines,
			[
				("Pack", row.get("pack_id")),
				("Family", row.get("family")),
				("Execution mode", row.get("execution_mode")),
				("Blocking level", row.get("blocking_level")),
				("Manual-only", _clean_bool(row.get("manual_only"))),
				("Manual UAT prompt", row.get("manual_uat_prompt")),
			],
		)
		lines.extend(["", "Expected Contract Fields"])
		_append_kv_table(lines, _expected_rows(row))
		lines.extend(["", "Prompt Sequence"])
		_append_list(lines, row.get("turns"))
		lines.extend(["", "Pass Criteria"])
		_append_list(lines, row.get("pass_criteria"))
		lines.extend(["", "Evidence Capture Template"])
		_append_kv_table(
			lines,
			[
				("Observed answer summary", "required before pass"),
				("Observed trace fields", "route, artifact_family, entity_type, row_reference, authority_source, policy_boundary, answer_mode"),
				("Observed model-role fields", "model_role_lane, lane, model_role, expected_model_role, role_compliance"),
				("UAT status", "pass, fail, blocked, or not_run"),
				("Failure reason", "required for fail or blocked"),
				("Reviewed at", "required for pass, fail, or blocked"),
			],
		)
	return "\n".join(lines).strip()


def render_manual_uat_evidence_record_markdown(evidence_record: Dict[str, Any]) -> str:
	record = deepcopy(evidence_record) if isinstance(evidence_record, dict) else {}
	lines: List[str] = ["**Manual UAT Evidence Record**", ""]
	_append_kv_table(
		lines,
		[
			("Contract type", record.get("type") or MANUAL_UAT_EVIDENCE_CONTRACT_TYPE),
			("Scenario", record.get("scenario_id")),
			("Pack", record.get("pack_id")),
			("UAT status", record.get("uat_status")),
			("Status valid", _clean_bool(record.get("status_valid"))),
			("Evidence complete", _clean_bool(record.get("evidence_complete"))),
			("Release blocking failure", _clean_bool(record.get("release_blocking_failure"))),
			("Blocking level", record.get("blocking_level")),
			("Reviewed at", record.get("reviewed_at")),
			("Reviewer", record.get("reviewer")),
		],
	)
	lines.extend(["", "Expected Contract Fields"])
	_append_kv_table(lines, _expected_rows(record))
	lines.extend(["", "Observed Answer Summary", "", _clean_text(record.get("observed_answer_summary"))])
	lines.extend(["", "Observed Trace Fields"])
	_append_dict_table(lines, record.get("observed_trace_fields"))
	lines.extend(["", "Observed Model-Role Fields"])
	_append_dict_table(lines, record.get("observed_model_role_fields"))
	lines.extend(["", "Missing Evidence"])
	_append_list(lines, record.get("missing_fields"))
	lines.extend(["", "Field Mismatches"])
	mismatches = record.get("field_mismatches") if isinstance(record.get("field_mismatches"), list) else []
	if not mismatches:
		lines.append("- none")
	else:
		for mismatch in mismatches:
			if isinstance(mismatch, dict):
				lines.append(
					f"- {mismatch.get('field', 'unknown')}: expected {mismatch.get('expected', 'missing')}, observed {mismatch.get('observed', 'missing')}"
				)
	lines.extend(["", "Failure Reason", "", _clean_text(record.get("failure_reason"))])
	return "\n".join(lines).strip()


def render_manual_uat_release_summary_markdown(summary_contract: Dict[str, Any]) -> str:
	summary = deepcopy(summary_contract) if isinstance(summary_contract, dict) else {}
	lines: List[str] = ["**Manual UAT Release Summary**", ""]
	_append_kv_table(
		lines,
		[
			("Contract type", summary.get("type") or MANUAL_UAT_RELEASE_SUMMARY_CONTRACT_TYPE),
			("Checklist contract complete", _clean_bool(summary.get("checklist_contract_complete"))),
			("Release ready", _clean_bool(summary.get("release_ready"))),
			("Expected scenario count", summary.get("expected_scenario_count")),
			("Evidence record count", summary.get("evidence_record_count")),
		],
	)
	lines.extend(["", "Status Counts"])
	_append_dict_table(lines, summary.get("status_counts"))
	lines.extend(["", "Blocking Failures"])
	_append_list(lines, summary.get("blocking_failure_scenario_ids"))
	lines.extend(["", "Missing Evidence"])
	_append_list(lines, summary.get("missing_evidence_scenario_ids"))
	lines.extend(["", "Incomplete Evidence"])
	_append_list(lines, summary.get("incomplete_evidence_scenario_ids"))
	lines.extend(["", "Field Mismatch Evidence"])
	_append_list(lines, summary.get("field_mismatch_scenario_ids"))
	lines.extend(["", "Duplicate Evidence"])
	_append_list(lines, summary.get("duplicate_evidence_scenario_ids"))
	lines.extend(["", "Manual-Only Scenarios"])
	_append_list(lines, summary.get("manual_only_scenario_ids"))
	return "\n".join(lines).strip()


def render_manual_uat_pack_markdown(
	checklist_contract: Dict[str, Any],
	*,
	evidence_records: Iterable[Dict[str, Any]] | None = None,
	summary_contract: Dict[str, Any] | None = None,
) -> str:
	checklist = deepcopy(checklist_contract) if isinstance(checklist_contract, dict) else {}
	records = [deepcopy(record) for record in evidence_records or [] if isinstance(record, dict)]
	summary = deepcopy(summary_contract) if isinstance(summary_contract, dict) else {}
	sections = [render_manual_uat_checklist_markdown(checklist)]
	for record in records:
		sections.append(render_manual_uat_evidence_record_markdown(record))
	if summary:
		sections.append(render_manual_uat_release_summary_markdown(summary))
	return "\n\n---\n\n".join(section for section in sections if section).strip()
