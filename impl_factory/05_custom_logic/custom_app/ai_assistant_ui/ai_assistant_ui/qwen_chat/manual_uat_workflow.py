from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Iterable, List

from .manual_uat_evidence import (
	MANUAL_UAT_STATUS_BLOCKED,
	MANUAL_UAT_STATUS_PASS,
	build_manual_uat_checklist_contract,
	build_manual_uat_checklist_row,
	build_manual_uat_evidence_record,
	build_manual_uat_release_summary,
)
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .regression_scenario_packs import build_regression_scenario_pack_contract


MANUAL_UAT_WORKFLOW_CONTRACT_TYPE = "qwen_manual_uat_execution_workflow_contract"
MANUAL_UAT_WORKFLOW_STAGE_CONTRACT_TYPE = "qwen_manual_uat_execution_workflow_stage_contract"
MANUAL_UAT_WORKFLOW_PACK_CONTRACT_TYPE = "qwen_manual_uat_execution_workflow_pack_contract"

MANUAL_UAT_WORKFLOW_SUITE_ID = "s7_manual_uat_workflow_contracts"

STAGE_PREPARE_CHECKLIST = "prepare_checklist"
STAGE_EXECUTE_PROMPT_SEQUENCE = "execute_prompt_sequence"
STAGE_CAPTURE_ANSWER = "capture_answer"
STAGE_CAPTURE_TRACE = "capture_trace"
STAGE_CAPTURE_MODEL_ROLE = "capture_model_role"
STAGE_VALIDATE_EVIDENCE = "validate_evidence"
STAGE_SUMMARIZE_RELEASE = "summarize_release"
STAGE_BLOCK_OR_ACCEPT = "block_or_accept"

WORKFLOW_STAGE_SEQUENCE = [
	STAGE_PREPARE_CHECKLIST,
	STAGE_EXECUTE_PROMPT_SEQUENCE,
	STAGE_CAPTURE_ANSWER,
	STAGE_CAPTURE_TRACE,
	STAGE_CAPTURE_MODEL_ROLE,
	STAGE_VALIDATE_EVIDENCE,
	STAGE_SUMMARIZE_RELEASE,
	STAGE_BLOCK_OR_ACCEPT,
]

REQUIRED_ANSWER_CAPTURE_FIELDS = [
	"observed_answer_summary",
	"reviewer",
	"reviewed_at",
]

REQUIRED_TRACE_CAPTURE_FIELDS = [
	"route",
	"artifact_family",
	"entity_type",
	"row_reference",
	"authority_source",
	"policy_boundary",
	"answer_mode",
]

REQUIRED_MODEL_ROLE_CAPTURE_FIELDS = [
	"model_role_lane",
	"lane",
	"model_role",
	"expected_model_role",
	"role_compliance",
]

STAGE_INSTRUCTIONS = {
	STAGE_PREPARE_CHECKLIST: "Generate the checklist row from the governed scenario registry before browser execution.",
	STAGE_EXECUTE_PROMPT_SEQUENCE: "Run the scenario prompt sequence in the browser/chat UI exactly as declared.",
	STAGE_CAPTURE_ANSWER: "Record a concise observed answer summary, reviewer, and review timestamp.",
	STAGE_CAPTURE_TRACE: "Record route, artifact, entity, row/rank, authority, policy, and answer-mode fields from the latest trace.",
	STAGE_CAPTURE_MODEL_ROLE: "Record model-role lane, observed role, expected role, and compliance fields.",
	STAGE_VALIDATE_EVIDENCE: "Build and validate evidence through the S7-6C evidence contract.",
	STAGE_SUMMARIZE_RELEASE: "Generate release summary only from evidence records.",
	STAGE_BLOCK_OR_ACCEPT: "Accept release readiness only when the evidence summary has no blockers.",
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


def _missing_from_dict(values: Dict[str, Any], required_fields: Iterable[str], *, prefix: str = "") -> List[str]:
	missing: List[str] = []
	for field in required_fields:
		if not _clean_text(values.get(field)):
			missing.append(f"{prefix}{field}" if prefix else field)
	return missing


def _required_capture_fields_for_stage(stage_id: str) -> List[str]:
	if stage_id == STAGE_CAPTURE_ANSWER:
		return list(REQUIRED_ANSWER_CAPTURE_FIELDS)
	if stage_id == STAGE_CAPTURE_TRACE:
		return [f"observed_trace_fields.{field}" for field in REQUIRED_TRACE_CAPTURE_FIELDS]
	if stage_id == STAGE_CAPTURE_MODEL_ROLE:
		return [f"observed_model_role_fields.{field}" for field in REQUIRED_MODEL_ROLE_CAPTURE_FIELDS]
	if stage_id == STAGE_VALIDATE_EVIDENCE:
		return ["uat_status", "failure_reason_if_fail_or_blocked"]
	if stage_id == STAGE_SUMMARIZE_RELEASE:
		return ["evidence_records"]
	if stage_id == STAGE_BLOCK_OR_ACCEPT:
		return ["manual_uat_release_summary.release_ready"]
	return []


def build_manual_uat_workflow_stage(stage_id: str) -> Dict[str, Any]:
	stage = _clean_text(stage_id)
	return {
		"type": MANUAL_UAT_WORKFLOW_STAGE_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"stage_id": stage,
		"operator_instruction": STAGE_INSTRUCTIONS.get(stage, ""),
		"required_capture_fields": _required_capture_fields_for_stage(stage),
		"evidence_builder": "build_manual_uat_evidence_record" if stage == STAGE_VALIDATE_EVIDENCE else "none",
		"failure_handling_rule": (
			"Missing answer, trace, or model-role capture cannot pass; mark blocked and record failure reason."
			if stage in {STAGE_CAPTURE_ANSWER, STAGE_CAPTURE_TRACE, STAGE_CAPTURE_MODEL_ROLE, STAGE_VALIDATE_EVIDENCE}
			else "Follow the declared scenario workflow."
		),
		"release_blocking_rule": (
			"Release readiness is decided only by the manual UAT release summary."
			if stage in {STAGE_SUMMARIZE_RELEASE, STAGE_BLOCK_OR_ACCEPT}
			else "Evidence gaps remain release-blocking until validated."
		),
	}


def build_manual_uat_execution_workflow(scenario: Dict[str, Any]) -> Dict[str, Any]:
	row = build_manual_uat_checklist_row(scenario)
	stages = [build_manual_uat_workflow_stage(stage_id) for stage_id in WORKFLOW_STAGE_SEQUENCE]
	required_capture_fields = []
	for stage in stages:
		required_capture_fields.extend(stage.get("required_capture_fields") or [])
	return {
		"type": MANUAL_UAT_WORKFLOW_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"workflow_id": f"manual_uat_workflow:{row.get('scenario_id')}",
		"source_checklist_contract": "qwen_manual_uat_checklist_contract",
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
		"blocking_level": row.get("blocking_level"),
		"execution_mode": row.get("execution_mode"),
		"execution_stages": stages,
		"stage_sequence": list(WORKFLOW_STAGE_SEQUENCE),
		"required_capture_fields": required_capture_fields,
		"evidence_builder": "build_manual_uat_evidence_record",
		"failure_handling_rule": "If answer, trace, or model-role capture is missing, force blocked evidence.",
		"release_blocking_rule": "Release acceptance is allowed only from a release-ready evidence summary.",
		"workflow_complete": bool(row.get("row_complete")) and len(stages) == len(WORKFLOW_STAGE_SEQUENCE),
		"created_at": _utc_now(),
	}


def build_manual_uat_workflow_pack_contract(
	*,
	registry: Iterable[Dict[str, Any]] | None = None,
	contract_owner: str = "s7_manual_uat_execution_workflow",
) -> Dict[str, Any]:
	scenario_pack = build_regression_scenario_pack_contract(registry=registry)
	checklist = build_manual_uat_checklist_contract(registry=registry)
	workflows = [build_manual_uat_execution_workflow(row) for row in checklist.get("rows", [])]
	incomplete_workflows = [
		_clean_text(workflow.get("scenario_id")) or "unknown"
		for workflow in workflows
		if not bool(workflow.get("workflow_complete"))
	]
	return {
		"type": MANUAL_UAT_WORKFLOW_PACK_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"contract_owner": _clean_text(contract_owner),
		"source_scenario_pack_complete": bool(scenario_pack.get("contract_complete")),
		"source_checklist_complete": bool(checklist.get("contract_complete")),
		"contract_complete": bool(scenario_pack.get("contract_complete"))
		and bool(checklist.get("contract_complete"))
		and bool(workflows)
		and not incomplete_workflows,
		"workflow_count": len(workflows),
		"incomplete_workflows": incomplete_workflows,
		"workflow_ids": [_clean_text(workflow.get("workflow_id")) for workflow in workflows],
		"scenario_ids": [_clean_text(workflow.get("scenario_id")) for workflow in workflows],
		"workflows": workflows,
		"created_at": _utc_now(),
	}


def _workflow_as_scenario(workflow: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"scenario_id": workflow.get("scenario_id"),
		"pack_id": workflow.get("pack_id"),
		"family": workflow.get("family"),
		"turns": list(workflow.get("turns") or []),
		"manual_uat_prompt": workflow.get("manual_uat_prompt"),
		"expected_route": workflow.get("expected_route"),
		"expected_artifact_family": workflow.get("expected_artifact_family"),
		"expected_entity_type": workflow.get("expected_entity_type"),
		"expected_row_reference": workflow.get("expected_row_reference"),
		"expected_authority_source": workflow.get("expected_authority_source"),
		"expected_policy_boundary": workflow.get("expected_policy_boundary"),
		"expected_model_role_lane": workflow.get("expected_model_role_lane"),
		"expected_answer_mode": workflow.get("expected_answer_mode"),
		"pass_criteria": list(workflow.get("pass_criteria") or []),
		"blocking_level": workflow.get("blocking_level"),
		"execution_mode": workflow.get("execution_mode"),
	}


def _workflow_missing_capture_fields(
	*,
	observed_answer_summary: str,
	observed_trace_fields: Dict[str, Any] | None,
	observed_model_role_fields: Dict[str, Any] | None,
	reviewer: str,
	reviewed_at: str,
) -> List[str]:
	missing = []
	if not _clean_text(observed_answer_summary):
		missing.append("observed_answer_summary")
	if not _clean_text(reviewer):
		missing.append("reviewer")
	if not _clean_text(reviewed_at):
		missing.append("reviewed_at")
	missing.extend(
		_missing_from_dict(_clean_dict(observed_trace_fields), REQUIRED_TRACE_CAPTURE_FIELDS, prefix="observed_trace_fields.")
	)
	missing.extend(
		_missing_from_dict(
			_clean_dict(observed_model_role_fields),
			REQUIRED_MODEL_ROLE_CAPTURE_FIELDS,
			prefix="observed_model_role_fields.",
		)
	)
	return missing


def build_manual_uat_evidence_from_workflow(
	workflow: Dict[str, Any],
	*,
	observed_answer_summary: str = "",
	observed_trace_fields: Dict[str, Any] | None = None,
	observed_model_role_fields: Dict[str, Any] | None = None,
	uat_status: str = MANUAL_UAT_STATUS_PASS,
	failure_reason: str = "",
	reviewer: str = "",
	reviewed_at: str = "",
) -> Dict[str, Any]:
	clean_workflow = dict(workflow or {})
	requested_status = _clean_text(uat_status) or MANUAL_UAT_STATUS_PASS
	missing_capture_fields = _workflow_missing_capture_fields(
		observed_answer_summary=observed_answer_summary,
		observed_trace_fields=observed_trace_fields,
		observed_model_role_fields=observed_model_role_fields,
		reviewer=reviewer,
		reviewed_at=reviewed_at,
	)
	final_status = requested_status
	final_failure_reason = _clean_text(failure_reason)
	if requested_status == MANUAL_UAT_STATUS_PASS and missing_capture_fields:
		final_status = MANUAL_UAT_STATUS_BLOCKED
		final_failure_reason = (
			final_failure_reason
			or "Required UAT capture fields are missing: " + ", ".join(missing_capture_fields)
		)
	record = build_manual_uat_evidence_record(
		_workflow_as_scenario(clean_workflow),
		observed_answer_summary=observed_answer_summary,
		observed_trace_fields=observed_trace_fields,
		observed_model_role_fields=observed_model_role_fields,
		uat_status=final_status,
		failure_reason=final_failure_reason,
		reviewer=reviewer,
		reviewed_at=reviewed_at,
	)
	record["workflow_id"] = clean_workflow.get("workflow_id")
	record["workflow_requested_status"] = requested_status
	record["workflow_final_status"] = final_status
	record["workflow_missing_capture_fields"] = missing_capture_fields
	record["workflow_capture_complete"] = not missing_capture_fields
	record["workflow_forced_blocked"] = requested_status == MANUAL_UAT_STATUS_PASS and final_status == MANUAL_UAT_STATUS_BLOCKED
	return record


def build_manual_uat_release_summary_from_workflow_evidence(
	*,
	evidence_records: Iterable[Dict[str, Any]],
	expected_scenario_ids: Iterable[str] | None = None,
	registry: Iterable[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
	return build_manual_uat_release_summary(
		evidence_records=evidence_records,
		expected_scenario_ids=expected_scenario_ids,
		registry=registry,
		contract_owner="s7_manual_uat_execution_workflow",
	)
