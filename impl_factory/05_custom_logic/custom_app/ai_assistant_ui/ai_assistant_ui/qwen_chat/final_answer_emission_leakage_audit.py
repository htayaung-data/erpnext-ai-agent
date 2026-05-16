from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .final_answer_emission_dry_run import (
	AUTHORIZED_APPEND_SITES,
	EXCLUDED_APPEND_SITES,
	MIGRATED_AUTHORIZED_PATHS,
	RISK_HIGH,
	build_final_answer_emission_dry_run_report,
)


FINAL_ANSWER_EMISSION_LEAKAGE_AUDIT_CONTRACT_TYPE = "qwen_ec4n_final_answer_emission_leakage_audit"
FINAL_ANSWER_EMISSION_LEAKAGE_AUDIT_SLICE_ID = "ec_4n_final_answer_emission_leakage_audit"
DEFAULT_EC4N_OUT_DIR = "impl_factory/00_governance/current_docs/generated/ec_4n_final_answer_emission_leakage_audit"
DEFAULT_EC4N_REPORT_JSON = "qwen_ec4n_final_answer_emission_leakage_audit_report.json"
DEFAULT_EC4N_REPORT_MARKDOWN = "qwen_ec4n_final_answer_emission_leakage_audit_report.md"

RECOMMENDATION_READY = "enterprise_cleanup_ec_4n_ready_for_counterpart_review"
RECOMMENDATION_BLOCKED = "enterprise_cleanup_ec_4n_blocked_need_leak_fix"

LEAK_STATUS_PASS = "pass"
LEAK_STATUS_NOT_APPLICABLE = "not_applicable"
LEAK_STATUS_POTENTIAL_LEAK = "potential_leak"

BLOCKED_LEAK_CHECKS = [
	"no_assistant_message",
	"no_returned_answer_text",
	"no_tool_trace_answer_text",
	"no_business_artifact_rendered_narrative_grounded_payload",
	"no_post_helper_payload_after_block",
	"single_blocked_authorized_emission_contract",
	"explicit_final_authority_block_reason",
]

BUSINESS_PAYLOAD_PATTERNS = {
	"frontdoor_render_result.to_payload": "frontdoor render payload can contain answer_text before authority validation",
	"reasoning_execution.to_payload": "reasoning execution payload can contain answer_text before authority validation",
	"_append_outcome_payloads": "NBU outcome payload append can include artifact/rendered/narrative/grounded evidence before authority validation",
	"append_compiled_attempt_artifacts": "compiled attempt artifacts are written before authorized emission validation",
	"tool_trace_message(": "tool trace is written before authorized emission validation",
	"grounded_turn_payload": "grounded-turn payload may be written before authorized emission validation",
	"rendered_response_payload": "rendered response payload may be written before authorized emission validation",
	"narrative_contract_payload": "narrative payload may be written before authorized emission validation",
}

SAFE_PREAUTH_PATTERNS = {
	"append_knowledge_boundary_contract",
	"record_phase55_observability_event",
	"record_phase6_observability_event",
	"record_phase6_performance_metric",
	"interaction_contract.to_payload",
	"frontdoor_semantic_result.to_payload",
	"frontdoor_contract.to_payload",
	"clarification_response_contract.to_payload",
	"provisional_response_policy_contract.to_payload",
	"reasoning_activation_contract.to_payload",
	"reasoning_semantic_result.to_payload",
	"provisional_response_policy_contract.to_payload",
	"reasoning_followup_resolution.to_payload",
	"model_role_observability",
	"model_role_strict_readiness",
	"followup_resolution.to_payload",
	"execution_path.to_payload",
	"activation_contract",
	"assessment",
	"execution_path.to_payload",
}

HELPER_OCCURRENCE_BY_PATH = {
	"reasoning_lane_guardrail_boundary": 2,
	"legacy_runtime_business_or_boundary_answer": 2,
	"artifact_boundary_grounded_evidence_refusal": 2,
	"artifact_boundary_enrichment_refusal": 3,
	"clarification_pending_reask_or_stop": 2,
	"service_prior_branch_clarification_restore": 2,
	"service_compound_continue_completed": 2,
	"service_compound_stop": 2,
}

SCAN_START_ANCHOR_BY_PATH = {
	"frontdoor_lane_package_governed_report_or_projection": "def handle_frontdoor_turn(",
	"frontdoor_lane_package_governed_kpi_definition": "def handle_frontdoor_turn(",
	"compiled_support_result_answer": "def handle_compiled_first_turn_result(",
	"reasoning_lane_business_answer": 'if reasoning_execution.status == "answered":',
	"reasoning_lane_guardrail_boundary": "reasoning_boundary_answer = build_reasoning_boundary_answer",
	"entity_followup_failure": "def try_entity_detail_followup(",
	"entity_followup_success": "def try_entity_detail_followup(",
	"nbu_governed_requery_entity_detail": "def try_activate_nbu_governed_requery_response(",
	"legacy_runtime_client_error": "except QwenRuntimeClientError",
	"legacy_runtime_business_or_boundary_answer": "grounded_validation_failed = (",
	"artifact_boundary_evidence_answer": "EC-4R1 evidence authority checkpoint",
	"artifact_boundary_grounded_evidence_refusal": "EC-4R1 grounded-boundary authority checkpoint",
	"artifact_boundary_enrichment_refusal": "EC-4R1 enrichment-boundary authority checkpoint",
	"local_followup_transform": "EC-4R2 local-transform authority checkpoint",
	"runtime_gate_out_of_scope_boundary": "EC-4S1 runtime-gate authority checkpoint",
	"service_out_of_scope_domain_boundary": "EC-4S2 service policy-boundary authority checkpoint",
	"service_known_unsupported_erp_domain_boundary": "EC-4S2 service policy-boundary authority checkpoint",
	"service_prior_branch_clarification_restore": "def _emit_service_control_answer(",
	"service_compound_continue_completed": "def _emit_service_control_answer(",
	"service_compound_stop": "def _emit_service_control_answer(",
	"visible_context_trace_inspection": "def try_activate_visible_context_trace_inspection_response(",
	"nbu_presentation_safe_response": "def try_activate_nbu_presentation_response(",
	"clarification_show_options": 'if clarification_decision == "show_options":',
	"clarification_pending_reask_or_stop": 'if clarification_decision in {"reask_pending_clarification", "meta_question", "empty_ack"}:',
	"recovery_guidance_answer": "def handle_recovery_guidance_response(",
}

PATH_LEAK_EVIDENCE: Dict[str, Dict[str, Any]] = {
	"visible_context_followup_filter_boundary": {
		"blocked_probe_status": LEAK_STATUS_NOT_APPLICABLE,
		"blocked_probe_reason": "Policy boundary/filter-readiness path emits bounded refusals; missing-authority business block is not the expected branch.",
		"evidence_tests": ["test_visible_context_followup_activation", "test_visible_context_trace_inspection"],
	},
	"visible_context_followup_answer": {
		"blocked_probe_status": LEAK_STATUS_NOT_APPLICABLE,
		"blocked_probe_reason": "Visible-context resolved answers derive authority from visible trace; blocked missing-authority path is covered by helper contract rather than lane-specific business payloads.",
		"evidence_tests": ["test_visible_context_followup_activation", "test_visible_context_trace_inspection"],
	},
	"frontdoor_lane_package_governed_report_or_projection": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4O stages frontdoor render/runtime/artifact payloads inside authorized pre-assistant payloads and tests prove blocked authority writes no business payload leak.",
		"evidence_tests": ["test_frontdoor_authorized_emission_contracts"],
	},
	"frontdoor_lane_package_governed_kpi_definition": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4O stages governed KPI definition render/frontdoor payloads through the authorized helper and blocks missing registry evidence without business side-channel output.",
		"evidence_tests": ["test_frontdoor_authorized_emission_contracts"],
	},
	"compiled_support_result_answer": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4O stages compiled attempt artifacts, runtime trace, grounded turn, and integration payloads through authorized pre-assistant payloads.",
		"evidence_tests": ["test_compiled_support_authorized_emission_contracts"],
	},
	"reasoning_lane_business_answer": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4O stages reasoning execution payloads through authorized pre-assistant payloads, so missing authority blocks before answer_text reaches tool payloads.",
		"evidence_tests": ["test_reasoning_lane_model_role_observability_contracts"],
	},
	"reasoning_lane_guardrail_boundary": {
		"blocked_probe_status": LEAK_STATUS_NOT_APPLICABLE,
		"blocked_probe_reason": "Guardrail branch emits a bounded policy refusal with explicit policy-boundary authority; missing business authority is not the branch contract.",
		"evidence_tests": ["test_reasoning_lane_model_role_observability_contracts"],
	},
	"entity_followup_failure": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4M-A moved failure trace into authorized pre-assistant payloads and focused tests prove no blocked business payload leak.",
		"evidence_tests": ["test_entity_followup_authorized_emission_contracts"],
	},
	"entity_followup_success": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4M-A focused tests prove missing authority writes only a blocked emission contract and no artifact/rendered/narrative/grounded/trace payload.",
		"evidence_tests": ["test_entity_followup_authorized_emission_contracts"],
	},
	"nbu_governed_requery_entity_detail": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4O stages NBU outcome artifact/rendered/narrative/grounded payloads through authorized pre-assistant payloads and tests cover invalid grounded authority.",
		"evidence_tests": ["test_nbu_governed_requery_authorized_emission_contracts"],
	},
	"legacy_runtime_client_error": {
		"blocked_probe_status": LEAK_STATUS_NOT_APPLICABLE,
		"blocked_probe_reason": "Runtime client error is an explicit non-business error fallback path with control authority, not a missing business-authority block.",
		"evidence_tests": ["test_legacy_runtime_authorized_emission_contracts"],
	},
	"legacy_runtime_business_or_boundary_answer": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4O stages legacy runtime trace and grounded-turn payloads through authorized pre-assistant payloads; blocked business authority appends only the blocked emission contract.",
		"evidence_tests": ["test_legacy_runtime_authorized_emission_contracts"],
	},
	"artifact_boundary_evidence_answer": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4R1 stages artifact evidence, narrative, selected-entity, and clarification payloads through authorized pre-assistant payloads; missing governed authority writes only a blocked emission contract.",
		"evidence_tests": ["test_artifact_boundary_authorized_emission_contracts"],
	},
	"artifact_boundary_grounded_evidence_refusal": {
		"blocked_probe_status": LEAK_STATUS_NOT_APPLICABLE,
		"blocked_probe_reason": "Grounded-evidence artifact refusal emits a bounded policy-boundary answer with explicit boundary authority; generated recovery payloads are staged through the authorized helper.",
		"evidence_tests": ["test_artifact_boundary_authorized_emission_contracts"],
	},
	"artifact_boundary_enrichment_refusal": {
		"blocked_probe_status": LEAK_STATUS_NOT_APPLICABLE,
		"blocked_probe_reason": "Artifact-enrichment refusal emits a bounded policy-boundary answer with explicit boundary authority; generated recovery payloads are staged through the authorized helper.",
		"evidence_tests": ["test_artifact_boundary_authorized_emission_contracts"],
	},
	"local_followup_transform": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4R2 stages transformed render, artifact update, narrative, runtime trace, and execution payloads through authorized pre-assistant payloads; missing grounded authority writes only a blocked emission contract.",
		"evidence_tests": ["test_local_followup_authorized_emission_contracts"],
	},
	"runtime_gate_out_of_scope_boundary": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4S1 stages runtime-gate boundary and observability payloads through authorized pre-assistant payloads; missing boundary authority writes only a blocked emission contract.",
		"evidence_tests": ["test_runtime_gate_authorized_emission_contracts"],
	},
	"service_out_of_scope_domain_boundary": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4S2 stages service out-of-scope boundary, observability, and execution payloads through authorized pre-assistant payloads; missing boundary authority writes only a blocked emission contract.",
		"evidence_tests": ["test_service_policy_boundary_authorized_emission_contracts"],
	},
	"service_known_unsupported_erp_domain_boundary": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4S2 stages service known-unsupported ERP-domain boundary, observability, and execution payloads through authorized pre-assistant payloads; missing boundary authority writes only a blocked emission contract.",
		"evidence_tests": ["test_service_policy_boundary_authorized_emission_contracts"],
	},
	"visible_context_trace_inspection": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4T1 stages trace inspection, execution, and additional control payloads through authorized pre-assistant payloads before emitting trace_debug_answer.",
		"evidence_tests": ["test_control_authorized_emission_contracts", "test_visible_context_trace_inspection"],
	},
	"nbu_presentation_safe_response": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4T1 stages NBU trace, activation, execution, and optional audit payloads through authorized pre-assistant payloads before emitting control_meta_answer.",
		"evidence_tests": ["test_control_authorized_emission_contracts"],
	},
	"clarification_show_options": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4T1 stages clarification control, observability, boundary, execution, and pending signal payloads through authorized pre-assistant payloads.",
		"evidence_tests": ["test_control_authorized_emission_contracts"],
	},
	"clarification_pending_reask_or_stop": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4T1 emits pending clarification re-ask/stop as control_meta_answer and updates pending state only after authorized emission.",
		"evidence_tests": ["test_control_authorized_emission_contracts"],
	},
	"recovery_guidance_answer": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4T1 stages recovery guidance contracts, observability, performance, and audit payloads through authorized pre-assistant payloads.",
		"evidence_tests": ["test_control_authorized_emission_contracts"],
	},
	"service_prior_branch_clarification_restore": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4T2 stages prior-branch restore control payloads through the authorized service control helper; missing control authority writes only a blocked emission contract.",
		"evidence_tests": ["test_service_control_authorized_emission_contracts"],
	},
	"service_compound_continue_completed": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4T2 stages completed compound continuation control/audit payloads through the authorized service control helper.",
		"evidence_tests": ["test_service_control_authorized_emission_contracts"],
	},
	"service_compound_stop": {
		"blocked_probe_status": LEAK_STATUS_PASS,
		"blocked_probe_reason": "EC-4T2 stages compound cancellation control/audit payloads through the authorized service control helper.",
		"evidence_tests": ["test_service_control_authorized_emission_contracts"],
	},
}


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _project_path(root_path: str | Path, relative_path: str) -> Path:
	root = Path(root_path or ".")
	path = Path(relative_path)
	return path if path.is_absolute() else root / path


def _read_text(root_path: Path, relative_path: str) -> str:
	path = root_path / relative_path
	return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _git_branch(root_path: Path) -> str:
	try:
		return subprocess.check_output(
			["git", "branch", "--show-current"],
			cwd=str(root_path),
			text=True,
			stderr=subprocess.DEVNULL,
		).strip()
	except Exception:
		return ""


def _git_short_head(root_path: Path) -> str:
	try:
		return subprocess.check_output(
			["git", "rev-parse", "--short", "HEAD"],
			cwd=str(root_path),
			text=True,
			stderr=subprocess.DEVNULL,
		).strip()
	except Exception:
		return ""


def _git_status_count(root_path: Path) -> int:
	try:
		output = subprocess.check_output(
			["git", "status", "--short"],
			cwd=str(root_path),
			text=True,
			stderr=subprocess.DEVNULL,
		)
	except Exception:
		return 0
	return len([line for line in output.splitlines() if line.strip()])


def _line_numbers_containing(text: str, needle: str) -> List[int]:
	return [index for index, line in enumerate(text.splitlines(), start=1) if needle in line]


def _helper_lines_for_path(text: str, path_id: str) -> List[int]:
	lines = _line_numbers_containing(text, "emit_authorized_assistant_answer(")
	if not lines:
		return []
	occurrence = int(HELPER_OCCURRENCE_BY_PATH.get(path_id) or 1)
	if occurrence <= 1:
		return [lines[0]]
	if len(lines) >= occurrence:
		return [lines[occurrence - 1]]
	return [lines[-1]]


def _scan_start_line(text: str, path_id: str, helper_line: int) -> int:
	anchor = _clean_text(SCAN_START_ANCHOR_BY_PATH.get(path_id))
	if not anchor:
		return 1
	lines = text.splitlines()
	for index in range(helper_line - 1, 0, -1):
		if anchor in lines[index - 1]:
			return index
	return 1


def _pre_helper_lines(text: str, *, path_id: str, helper_line: int) -> List[Dict[str, Any]]:
	if helper_line <= 0:
		return []
	start_line = _scan_start_line(text, path_id, helper_line)
	results: List[Dict[str, Any]] = []
	for index, line in enumerate(text.splitlines(), start=1):
		if index < start_line:
			continue
		if index >= helper_line:
			break
		stripped = line.strip()
		if not stripped:
			continue
		if any(token in stripped for token in ("append_tool_payload(", "append_message(", "append_compiled_attempt_artifacts(", "_append_outcome_payloads(")):
			patterns = [
				pattern
				for pattern in BUSINESS_PAYLOAD_PATTERNS
				if pattern in stripped
			]
			is_safe_known = any(pattern in stripped for pattern in SAFE_PREAUTH_PATTERNS)
			results.append(
				{
					"line": index,
					"source": stripped,
					"business_payload_patterns": patterns,
					"known_safe_contract_payload": bool(is_safe_known and not patterns),
				}
			)
	return results


def _is_authorized_emitted_guarded(lines: List[str], line_index: int) -> bool:
	for index in range(line_index - 1, max(0, line_index - 8), -1):
		if "if authorized_emission.emitted" in lines[index - 1].strip():
			return True
	return False


def _post_helper_payload_lines(text: str, *, helper_line: int) -> List[Dict[str, Any]]:
	if helper_line <= 0:
		return []
	results: List[Dict[str, Any]] = []
	lines = text.splitlines()
	for index, line in enumerate(lines, start=1):
		if index <= helper_line:
			continue
		stripped = line.strip()
		if stripped.startswith("return "):
			break
		if stripped.startswith("def "):
			break
		if any(token in stripped for token in ("append_tool_payload(", "append_message(", "append_knowledge_boundary_observability(")):
			results.append(
				{
					"line": index,
					"source": stripped,
					"guarded_by_authorized_emission": _is_authorized_emitted_guarded(lines, index),
				}
			)
	return results


def _business_payload_risks(lines: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
	risks: List[Dict[str, Any]] = []
	for item in lines:
		patterns = list(item.get("business_payload_patterns") or [])
		if patterns:
			risks.append(
				{
					"line": item.get("line"),
					"source": item.get("source"),
					"risk_reasons": [BUSINESS_PAYLOAD_PATTERNS[pattern] for pattern in patterns],
				}
			)
		elif not item.get("known_safe_contract_payload"):
			source = _clean_text(item.get("source"))
			if (
				"append_message(" in source
				and '"user"' not in source
				and "'user'" not in source
			):
				risks.append(
					{
						"line": item.get("line"),
						"source": source,
						"risk_reasons": ["pre-authority payload append needs explicit leak classification"],
					}
				)
	return risks


def _post_helper_payload_risks(lines: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
	return [
		{
			"line": item.get("line"),
			"source": item.get("source"),
			"risk_reasons": ["post-helper payload append is not guarded by authorized_emission.emitted"],
		}
		for item in lines
		if not item.get("guarded_by_authorized_emission")
	]


def _path_audit_row(root_path: Path, migrated_path: Dict[str, Any]) -> Dict[str, Any]:
	path_id = _clean_text(migrated_path.get("path_id"))
	relative_file_path = _clean_text(migrated_path.get("relative_file_path"))
	text = _read_text(root_path, relative_file_path)
	helper_lines = _helper_lines_for_path(text, path_id)
	helper_line = helper_lines[0] if helper_lines else 0
	pre_helper_payload_lines = _pre_helper_lines(text, path_id=path_id, helper_line=helper_line)
	post_helper_payload_lines = _post_helper_payload_lines(text, helper_line=helper_line)
	source_risks = _business_payload_risks(pre_helper_payload_lines)
	post_helper_risks = _post_helper_payload_risks(post_helper_payload_lines)
	evidence = dict(PATH_LEAK_EVIDENCE.get(path_id) or {})
	declared_status = _clean_text(evidence.get("blocked_probe_status")) or LEAK_STATUS_POTENTIAL_LEAK
	status = (
		LEAK_STATUS_POTENTIAL_LEAK
		if (source_risks or post_helper_risks) and declared_status == LEAK_STATUS_PASS
		else declared_status
	)
	if status == LEAK_STATUS_PASS:
		checks = {check: "pass" for check in BLOCKED_LEAK_CHECKS}
	elif status == LEAK_STATUS_NOT_APPLICABLE:
		checks = {check: "not_applicable" for check in BLOCKED_LEAK_CHECKS}
	else:
		checks = {
			"no_assistant_message": "covered_by_helper_or_lane_tests",
			"no_returned_answer_text": "covered_by_lane_tests_or_pending_stronger_probe",
			"no_tool_trace_answer_text": "needs_leak_fix_or_targeted_probe",
			"no_business_artifact_rendered_narrative_grounded_payload": "needs_leak_fix_or_targeted_probe",
			"no_post_helper_payload_after_block": "needs_leak_fix_or_targeted_probe",
			"single_blocked_authorized_emission_contract": "covered_by_helper_or_lane_tests",
			"explicit_final_authority_block_reason": "covered_by_helper_or_lane_tests",
		}
	return {
		"path_id": path_id,
		"relative_file_path": relative_file_path,
		"function_name": _clean_text(migrated_path.get("function_name")),
		"answer_type": _clean_text(migrated_path.get("answer_type")),
		"migration_slice": _clean_text(migrated_path.get("migration_slice")),
		"helper_call_lines": helper_lines,
		"helper_call_count": len(helper_lines),
		"blocked_leakage_status": status,
		"blocked_probe_reason": _clean_text(evidence.get("blocked_probe_reason")),
		"evidence_tests": list(evidence.get("evidence_tests") or []),
		"blocked_leakage_checks": checks,
		"pre_helper_payload_lines": pre_helper_payload_lines,
		"pre_helper_business_payload_risks": source_risks,
		"post_helper_payload_lines": post_helper_payload_lines,
		"post_helper_payload_risks": post_helper_risks,
	}


def _remaining_high_risk_paths(dry_run_report: Dict[str, Any]) -> List[Dict[str, Any]]:
	inventory = {
		_clean_text(item.get("path_id")): item
		for item in list(dry_run_report.get("emission_path_inventory") or [])
	}
	return [
		{
			"path_id": path_id,
			"risk_level": RISK_HIGH,
			"relative_file_path": _clean_text(inventory.get(path_id, {}).get("relative_file_path")),
			"classification": (
				"low_level_append_wrapper_not_migrated_by_design"
				if path_id == "service_append_message_wrapper"
				else "duplicate_frontdoor_drift_not_active_package_lane"
			),
			"ec4n_decision": "classify_only_do_not_migrate_in_ec4n",
		}
		for path_id in list(dry_run_report.get("high_risk_paths") or [])
	]


def build_final_answer_emission_leakage_audit_report(
	*,
	root_path: str | Path = ".",
	reviewer: str = "codex_ec4n_leakage_audit",
) -> Dict[str, Any]:
	root = Path(root_path).resolve()
	dry_run_report = build_final_answer_emission_dry_run_report(
		reviewer=reviewer,
		status_count=_git_status_count(root),
	)
	migrated_rows = [_path_audit_row(root, item) for item in MIGRATED_AUTHORIZED_PATHS]
	missing_evidence = [
		row["path_id"]
		for row in migrated_rows
		if not row.get("blocked_probe_reason") or not row.get("evidence_tests")
	]
	potential_leaks = [
		row["path_id"]
		for row in migrated_rows
		if row.get("blocked_leakage_status") == LEAK_STATUS_POTENTIAL_LEAK
	]
	pass_count = len([row for row in migrated_rows if row.get("blocked_leakage_status") == LEAK_STATUS_PASS])
	na_count = len([row for row in migrated_rows if row.get("blocked_leakage_status") == LEAK_STATUS_NOT_APPLICABLE])
	ready = not missing_evidence and not potential_leaks
	return {
		"type": FINAL_ANSWER_EMISSION_LEAKAGE_AUDIT_CONTRACT_TYPE,
		"contract_version": "1.0",
		"slice_id": FINAL_ANSWER_EMISSION_LEAKAGE_AUDIT_SLICE_ID,
		"created_at": _utc_now(),
		"reviewer": _clean_text(reviewer),
		"branch": _git_branch(root),
		"head": _git_short_head(root),
		"current_dirty_status_count": _git_status_count(root),
		"scope": "EC-4 checkpoint audit across migrated authorized-emission lanes; no new lane migration.",
		"runtime_behavior_changed": False,
		"hard_runtime_blocking_enabled": False,
		"migrated_path_count": len(migrated_rows),
		"migrated_path_ids": [row["path_id"] for row in migrated_rows],
		"blocked_leakage_checklist": list(BLOCKED_LEAK_CHECKS),
		"blocked_leakage_pass_count": pass_count,
		"blocked_leakage_not_applicable_count": na_count,
		"blocked_leakage_potential_leak_count": len(potential_leaks),
		"potential_leak_path_ids": potential_leaks,
		"missing_evidence_path_ids": missing_evidence,
		"migrated_lane_audit": migrated_rows,
		"remaining_high_risk_paths": _remaining_high_risk_paths(dry_run_report),
		"dry_run_counts": {
			"active_runtime_direct_assistant_append_count": dry_run_report.get("active_runtime_direct_assistant_append_count"),
			"authorized_runtime_append_sink_count": dry_run_report.get("authorized_runtime_append_sink_count"),
			"excluded_non_runtime_append_count": dry_run_report.get("excluded_non_runtime_append_count"),
			"total_source_assistant_append_sites_observed": dry_run_report.get("total_source_assistant_append_sites_observed"),
			"high_risk_paths": dry_run_report.get("high_risk_paths"),
			"migrated_authorized_path_count": len(dry_run_report.get("migrated_authorized_paths") or []),
		},
		"authorized_append_sites": list(AUTHORIZED_APPEND_SITES),
		"excluded_append_sites": list(EXCLUDED_APPEND_SITES),
		"non_goals": [
			"no_new_lane_migration",
			"no_service_append_wrapper_migration",
			"no_root_frontdoor_duplicate_cleanup",
			"no_model_role_strict_enforcement",
			"no_release_packaging_cleanup",
		],
		"final_recommendation": RECOMMENDATION_READY if ready else RECOMMENDATION_BLOCKED,
		"recommendation_reason": (
			"All migrated lanes have explicit blocked-emission leakage evidence or accepted not-applicable classification."
			if ready
			else "At least one migrated lane still has potential pre-authority tool/evidence leakage risk and needs a focused fix before further lane migration."
		),
	}


def render_final_answer_emission_leakage_audit_markdown(report: Dict[str, Any]) -> str:
	lines: List[str] = [
		"# EC-4N Final-Answer Emission Leakage Audit",
		"",
		f"- Branch: `{_clean_text(report.get('branch'))}`",
		f"- Head: `{_clean_text(report.get('head'))}`",
		f"- Dirty status count: `{report.get('current_dirty_status_count')}`",
		f"- Runtime behavior changed: `{bool(report.get('runtime_behavior_changed'))}`",
		f"- Final recommendation: `{_clean_text(report.get('final_recommendation'))}`",
		f"- Migrated path count: `{report.get('migrated_path_count')}`",
		f"- Potential leak count: `{report.get('blocked_leakage_potential_leak_count')}`",
		"",
		"## Dry-Run Counts",
		"",
	]
	for key, value in dict(report.get("dry_run_counts") or {}).items():
		lines.append(f"- `{key}`: `{value}`")
	lines.extend(
		[
			"",
			"## Migrated Lane Audit",
			"",
			"| Path | Slice | Status | Evidence | Risk count |",
			"|---|---|---|---|---:|",
		]
	)
	for row in list(report.get("migrated_lane_audit") or []):
		lines.append(
			"| {path} | {slice_id} | {status} | {tests} | {risk_count} |".format(
				path=_clean_text(row.get("path_id")),
				slice_id=_clean_text(row.get("migration_slice")),
				status=_clean_text(row.get("blocked_leakage_status")),
				tests=", ".join(str(item) for item in list(row.get("evidence_tests") or [])),
				risk_count=len(list(row.get("pre_helper_business_payload_risks") or [])),
			)
		)
	lines.extend(["", "## Potential Leak Paths"])
	for path_id in list(report.get("potential_leak_path_ids") or []):
		lines.append(f"- `{_clean_text(path_id)}`")
	lines.extend(["", "## Remaining High-Risk Paths"])
	for row in list(report.get("remaining_high_risk_paths") or []):
		lines.append(
			f"- `{_clean_text(row.get('path_id'))}`: `{_clean_text(row.get('classification'))}`"
		)
	lines.extend(["", "## Non-Goals"])
	for non_goal in list(report.get("non_goals") or []):
		lines.append(f"- `{_clean_text(non_goal)}`")
	lines.extend(["", "## Final Recommendation", "", f"`{_clean_text(report.get('final_recommendation'))}`", ""])
	return "\n".join(lines)


def write_final_answer_emission_leakage_audit_files(
	*,
	root_path: str | Path = ".",
	out_dir: str | Path = DEFAULT_EC4N_OUT_DIR,
	reviewer: str = "codex_ec4n_leakage_audit",
) -> Dict[str, Any]:
	report = build_final_answer_emission_leakage_audit_report(root_path=root_path, reviewer=reviewer)
	target_dir = _project_path(root_path, out_dir)
	target_dir.mkdir(parents=True, exist_ok=True)
	json_path = target_dir / DEFAULT_EC4N_REPORT_JSON
	markdown_path = target_dir / DEFAULT_EC4N_REPORT_MARKDOWN
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_path.write_text(render_final_answer_emission_leakage_audit_markdown(report), encoding="utf-8")
	report["report_json_artifact_path"] = str(json_path)
	report["report_markdown_artifact_path"] = str(markdown_path)
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	return report


def main(argv: List[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Generate the EC-4N final-answer emission leakage audit report.")
	parser.add_argument("--root-path", default=".")
	parser.add_argument("--out-dir", default=DEFAULT_EC4N_OUT_DIR)
	parser.add_argument("--reviewer", default="codex_ec4n_leakage_audit")
	args = parser.parse_args(argv)
	report = write_final_answer_emission_leakage_audit_files(
		root_path=args.root_path,
		out_dir=args.out_dir,
		reviewer=args.reviewer,
	)
	print(json.dumps(report, indent=2, sort_keys=True))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
