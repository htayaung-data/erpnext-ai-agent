from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .final_answer_emission_dry_run import build_final_answer_emission_dry_run_report
from .natural_business_understanding_contracts import CONTRACT_VERSION
from .runtime_metadata_contract import (
	COMPLIANCE_COMPLIANT,
	COMPLIANCE_NOT_APPLICABLE,
	COMPLIANCE_UNKNOWN,
	LANE_CLASS_AI_REASONING,
	LANE_CLASS_AI_SEMANTIC,
	LANE_CLASS_CONTROL_META,
	LANE_CLASS_DETERMINISTIC_REPORT,
	LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT,
	LANE_CLASS_ERROR_FALLBACK,
	LANE_CLASS_GOVERNED_TOOL_RUNTIME,
	LANE_CLASS_MODEL_BACKED_HELPER,
	LANE_CLASS_POLICY_BOUNDARY,
	LANE_CLASS_SHADOW_OBSERVER,
	METADATA_STATUS_COVERED,
	METADATA_STATUS_MISSING,
	METADATA_STATUS_PARTIAL,
	ROLE_CONTROL_META,
	ROLE_DETERMINISTIC,
	ROLE_GOVERNED_TOOL_RUNTIME,
	ROLE_HEAVY_REASONING,
	ROLE_LIGHT_SEMANTIC,
	ROLE_MODEL_BACKED_HELPER,
	ROLE_NOT_APPLICABLE,
	ROLE_POLICY_BOUNDARY,
	ROLE_SHADOW_OBSERVER,
	STRICT_STATUS_NOT_APPLICABLE,
	STRICT_STATUS_NOT_READY_MISSING_METADATA,
	STRICT_STATUS_READY,
	STRICT_STATUS_SOFT_BLOCK,
	expected_role_for_lane_class,
)

STRICT_READINESS_SOFT_GATE_CONTRACT_TYPE = "qwen_strict_readiness_soft_gate_dry_run_contract"
SLICE_ID = "ec_7g_b_strict_readiness_soft_gate_dry_run"
RUNTIME_EFFECT_NONE = "none"

SOFT_GATE_PASS = "soft_gate_pass"
SOFT_GATE_WARN = "soft_gate_warn"
SOFT_GATE_BLOCK_RELEASE = "soft_gate_block_release"
NOT_APPLICABLE_DETERMINISTIC = "not_applicable_deterministic"
NOT_APPLICABLE_CONTROL = "not_applicable_control"

DEFAULT_REPORT_MD = "qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.md"
DEFAULT_REPORT_JSON = "qwen_erp_ec_7g_b_strict_readiness_soft_gate_dry_run_report_2026-05-19.json"
DEFAULT_REPORT_DIR = "impl_factory/00_governance/current_docs"
QWEN_CHAT_RELATIVE_DIR = "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat"
ASSISTANT_APPEND_NEEDLE = "append_" + "message" + "(session_doc, " + chr(34) + "assistant" + chr(34)

DETERMINISTIC_CLASSES = {LANE_CLASS_DETERMINISTIC_REPORT, LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT}
CONTROL_CLASSES = {LANE_CLASS_CONTROL_META, LANE_CLASS_ERROR_FALLBACK, LANE_CLASS_POLICY_BOUNDARY}
AI_PROVENANCE_CLASSES = {
	LANE_CLASS_AI_SEMANTIC,
	LANE_CLASS_AI_REASONING,
	LANE_CLASS_SHADOW_OBSERVER,
	LANE_CLASS_MODEL_BACKED_HELPER,
	LANE_CLASS_GOVERNED_TOOL_RUNTIME,
}
HELPER_TOOL_CLASSES = {LANE_CLASS_MODEL_BACKED_HELPER, LANE_CLASS_GOVERNED_TOOL_RUNTIME}

REQUIRED_LANE_FIELDS = (
	"lane_id",
	"lane_class",
	"model_role",
	"expected_lane_class",
	"expected_model_role",
	"metadata_status",
	"strict_readiness_status",
	"strict_enforcement_ready",
	"fallback_used",
	"fallback_reason",
	"role_compliance",
	"authority_source",
	"final_answer_authority_status",
	"final_answer_authority_source",
	"preflight_status",
	"probe_evidence_slice",
	"soft_gate_decision",
	"reason",
	"release_readiness_impact",
	"observed_metadata",
	"expected_metadata",
	"runtime_effect",
)

NON_GOALS = [
	"no_runtime_enforcement",
	"no_runtime_blocking",
	"no_user_facing_behavior_change",
	"no_routing_or_model_change",
	"no_answer_text_change",
	"no_report_selection_change",
	"no_final_answer_authority_change",
	"no_strict_enforcement_approval",
	"no_staging_commit_push_or_deployment",
	"no_ux_filter_mi_family_expansion_or_service_refactor",
]


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _bool(value: Any) -> bool:
	if isinstance(value, bool):
		return value
	return _clean_text(value).lower() in {"true", "1", "yes"}


def _project_path(root_path: str | Path | None, relative_path: str | Path) -> Path:
	root = Path(root_path or ".")
	path = Path(relative_path)
	return path if path.is_absolute() else root / path


def _git_value(root_path: str | Path | None, args: Sequence[str], default: str = "unknown") -> str:
	try:
		completed = subprocess.run(
			["git", *args],
			cwd=str(Path(root_path or ".")),
			check=True,
			capture_output=True,
			text=True,
		)
		return completed.stdout.strip() or default
	except Exception:
		return default


def _lane(
	lane_id: str,
	lane_class: str,
	*,
	model_role: str | None = None,
	metadata_status: str = METADATA_STATUS_COVERED,
	strict_readiness_status: str = STRICT_STATUS_READY,
	strict_enforcement_ready: bool = True,
	fallback_used: bool = False,
	fallback_reason: str = "",
	role_compliance: str = COMPLIANCE_COMPLIANT,
	authority_source: str = "runtime_metadata",
	final_answer_authority_status: str = "not_applicable",
	final_answer_authority_source: str = "not_applicable",
	preflight_status: str = "passed",
	probe_evidence_slice: str = "EC-7F",
) -> Dict[str, Any]:
	resolved_model_role = model_role or expected_role_for_lane_class(lane_class)
	return {
		"lane_id": lane_id,
		"lane_class": lane_class,
		"model_role": resolved_model_role,
		"expected_lane_class": lane_class,
		"expected_model_role": expected_role_for_lane_class(lane_class),
		"metadata_status": metadata_status,
		"strict_readiness_status": strict_readiness_status,
		"strict_enforcement_ready": bool(strict_enforcement_ready),
		"fallback_used": bool(fallback_used),
		"fallback_reason": _clean_text(fallback_reason),
		"role_compliance": role_compliance,
		"authority_source": authority_source,
		"final_answer_authority_status": final_answer_authority_status,
		"final_answer_authority_source": final_answer_authority_source,
		"preflight_status": preflight_status,
		"probe_evidence_slice": probe_evidence_slice,
		"metadata_source": "ec_7f_runtime_probe_closure",
		"answer_mode": "runtime_metadata_provenance",
	}


def default_lane_evidence_rows() -> List[Dict[str, Any]]:
	rows: List[Dict[str, Any]] = []
	for lane_id in (
		"frontdoor_semantic_classification",
		"fresh_query_interpretation",
		"followup_interpretation",
		"semantic_reasoning_activation",
		"semantic_repair_intent",
	):
		rows.append(
			_lane(
				lane_id,
				LANE_CLASS_AI_SEMANTIC,
				model_role=ROLE_LIGHT_SEMANTIC,
				authority_source="semantic_runtime_metadata",
				probe_evidence_slice="EC-7F-B",
			)
		)
	rows.extend(
		[
			_lane(
				"business_reasoning_answer",
				LANE_CLASS_AI_REASONING,
				model_role=ROLE_HEAVY_REASONING,
				authority_source="reasoning_runtime_metadata",
				final_answer_authority_status="passed",
				final_answer_authority_source="reasoning_business_authority",
				probe_evidence_slice="EC-7F-C",
			),
			_lane(
				"nbu_shadow_observation",
				LANE_CLASS_SHADOW_OBSERVER,
				model_role=ROLE_SHADOW_OBSERVER,
				authority_source="shadow_observer_runtime_metadata",
				final_answer_authority_status="observe_only",
				final_answer_authority_source="not_applicable_shadow_observer",
				probe_evidence_slice="EC-7F-C",
			),
		]
	)
	for lane_id in ("frontdoor_render", "clarification_system", "artifact_narrative"):
		rows.append(
			_lane(
				lane_id,
				LANE_CLASS_MODEL_BACKED_HELPER,
				model_role=ROLE_MODEL_BACKED_HELPER,
				authority_source="model_backed_helper_runtime_metadata",
				final_answer_authority_status="provenance_only",
				final_answer_authority_source="not_applicable_helper_metadata",
				probe_evidence_slice="EC-7F-D-A",
			)
		)
	for lane_id in ("composite_reads", "fresh_query_compiled_read_runtime"):
		rows.append(
			_lane(
				lane_id,
				LANE_CLASS_GOVERNED_TOOL_RUNTIME,
				model_role=ROLE_GOVERNED_TOOL_RUNTIME,
				authority_source="governed_tool_runtime_metadata",
				final_answer_authority_status="provenance_only",
				final_answer_authority_source="not_applicable_tool_metadata",
				probe_evidence_slice="EC-7F-D-A",
			)
		)
	for lane_id, lane_class, authority_source in (
		("compiled_support_result_answer", LANE_CLASS_DETERMINISTIC_REPORT, "governed_erp_report"),
		("legacy_runtime_business_or_boundary_answer", LANE_CLASS_DETERMINISTIC_REPORT, "governed_erp_report"),
		("artifact_boundary", LANE_CLASS_DETERMINISTIC_REPORT, "governed_artifact_authority"),
		("local_followup_transform", LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT, "visible_context_grounded_authority"),
		("entity_followup", LANE_CLASS_DETERMINISTIC_REPORT, "deterministic_tool"),
		("nbu_governed_requery_entity_detail", LANE_CLASS_DETERMINISTIC_REPORT, "deterministic_tool"),
		("visible_context_followup", LANE_CLASS_DETERMINISTIC_VISIBLE_CONTEXT, "visible_context_authority"),
	):
		rows.append(
			_lane(
				lane_id,
				lane_class,
				model_role=ROLE_DETERMINISTIC,
				strict_readiness_status=STRICT_STATUS_NOT_APPLICABLE,
				strict_enforcement_ready=False,
				role_compliance=COMPLIANCE_NOT_APPLICABLE,
				authority_source=authority_source,
				final_answer_authority_status="passed",
				final_answer_authority_source=authority_source,
				probe_evidence_slice="EC-7F-E",
			)
		)
	for lane_id in ("runtime_gate", "service_policy_control_responses"):
		rows.append(
			_lane(
				lane_id,
				LANE_CLASS_POLICY_BOUNDARY,
				model_role=ROLE_POLICY_BOUNDARY,
				strict_readiness_status=STRICT_STATUS_NOT_APPLICABLE,
				strict_enforcement_ready=False,
				role_compliance=COMPLIANCE_NOT_APPLICABLE,
				authority_source="policy_boundary",
				final_answer_authority_status="bounded",
				final_answer_authority_source="policy_boundary",
				preflight_status="bounded",
				probe_evidence_slice="EC-7F-E",
			)
		)
	for lane_id, authority_source in (
		("clarification_control", "control_meta"),
		("nbu_safe_response_activation", "control_meta"),
		("visible_context_trace_inspection", "trace_debug"),
	):
		rows.append(
			_lane(
				lane_id,
				LANE_CLASS_CONTROL_META,
				model_role=ROLE_CONTROL_META,
				strict_readiness_status=STRICT_STATUS_NOT_APPLICABLE,
				strict_enforcement_ready=False,
				role_compliance=COMPLIANCE_NOT_APPLICABLE,
				authority_source=authority_source,
				final_answer_authority_status="passed",
				final_answer_authority_source=authority_source,
				probe_evidence_slice="EC-7F-E",
			)
		)
	return rows


def raw_assistant_append_scan(*, root_path: str | Path | None = None) -> List[Dict[str, Any]]:
	qwen_chat_dir = _project_path(root_path, QWEN_CHAT_RELATIVE_DIR)
	rows: List[Dict[str, Any]] = []
	if not qwen_chat_dir.exists():
		return rows
	for path in sorted(qwen_chat_dir.rglob("*.py")):
		lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
		for index, line in enumerate(lines, start=1):
			if ASSISTANT_APPEND_NEEDLE in line:
				rows.append(
					{
						"relative_file_path": str(path.relative_to(Path(root_path or "."))),
						"line": index,
						"source": line.strip(),
						"runtime_effect": RUNTIME_EFFECT_NONE,
					}
				)
	return rows


def _release_impact(decision: str) -> str:
	return {
		SOFT_GATE_PASS: "pass",
		SOFT_GATE_WARN: "warning",
		SOFT_GATE_BLOCK_RELEASE: "release_blocking",
	}.get(decision, "not_applicable")


def _is_missing_metadata(row: Dict[str, Any]) -> bool:
	return _clean_text(row.get("metadata_status")) in {
		METADATA_STATUS_MISSING,
		METADATA_STATUS_PARTIAL,
		"needs_runtime_probe",
	}


def _observed_metadata(row: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"lane_class": _clean_text(row.get("lane_class")),
		"model_role": _clean_text(row.get("model_role")),
		"metadata_status": _clean_text(row.get("metadata_status")),
		"strict_readiness_status": _clean_text(row.get("strict_readiness_status")),
		"strict_enforcement_ready": bool(row.get("strict_enforcement_ready")),
		"fallback_used": _bool(row.get("fallback_used")),
		"fallback_reason": _clean_text(row.get("fallback_reason")),
		"role_compliance": _clean_text(row.get("role_compliance")),
		"authority_source": _clean_text(row.get("authority_source")),
		"final_answer_authority_status": _clean_text(row.get("final_answer_authority_status")),
		"final_answer_authority_source": _clean_text(row.get("final_answer_authority_source")),
		"preflight_status": _clean_text(row.get("preflight_status")),
		"probe_evidence_slice": _clean_text(row.get("probe_evidence_slice")),
	}


def _expected_metadata(row: Dict[str, Any]) -> Dict[str, Any]:
	lane_class = _clean_text(row.get("expected_lane_class")) or _clean_text(row.get("lane_class"))
	expected_role = _clean_text(row.get("expected_model_role")) or expected_role_for_lane_class(lane_class)
	if lane_class in DETERMINISTIC_CLASSES:
		strict_readiness = STRICT_STATUS_NOT_APPLICABLE
		strict_ready = False
		final_authority = "passed"
	elif lane_class == LANE_CLASS_POLICY_BOUNDARY:
		strict_readiness = STRICT_STATUS_NOT_APPLICABLE
		strict_ready = False
		final_authority = "bounded"
	elif lane_class in {LANE_CLASS_CONTROL_META, LANE_CLASS_ERROR_FALLBACK}:
		strict_readiness = STRICT_STATUS_NOT_APPLICABLE
		strict_ready = False
		final_authority = "passed"
	else:
		strict_readiness = STRICT_STATUS_READY
		strict_ready = True
		final_authority = "provenance_only" if lane_class in HELPER_TOOL_CLASSES else "not_applicable"
	return {
		"lane_class": lane_class,
		"model_role": expected_role,
		"metadata_status": METADATA_STATUS_COVERED,
		"strict_readiness_status": strict_readiness,
		"strict_enforcement_ready": strict_ready,
		"fallback_used": False,
		"role_compliance": COMPLIANCE_COMPLIANT if lane_class in AI_PROVENANCE_CLASSES else COMPLIANCE_NOT_APPLICABLE,
		"authority_source_required": lane_class in DETERMINISTIC_CLASSES | CONTROL_CLASSES,
		"final_answer_authority_status": final_authority,
		"runtime_effect": RUNTIME_EFFECT_NONE,
	}


def _is_authorized_raw_append(item: Dict[str, Any]) -> bool:
	path = _clean_text(item.get("relative_file_path")).replace("\\", "/")
	return path.endswith("qwen_chat/authorized_emission.py")


def _raw_append_regression_rows(raw_scan: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
	rows: List[Dict[str, Any]] = []
	for item in raw_scan:
		if _is_authorized_raw_append(item):
			continue
		rows.append(
			classify_soft_gate_lane(
				{
					"lane_id": "raw_assistant_append_scan_regression",
					"lane_class": LANE_CLASS_CONTROL_META,
					"model_role": ROLE_CONTROL_META,
					"metadata_status": METADATA_STATUS_MISSING,
					"strict_readiness_status": STRICT_STATUS_NOT_READY_MISSING_METADATA,
					"strict_enforcement_ready": False,
					"fallback_used": False,
					"role_compliance": COMPLIANCE_UNKNOWN,
					"authority_source": "",
					"final_answer_authority_status": "failed",
					"final_answer_authority_source": "raw_assistant_append_scan",
					"preflight_status": "failed",
					"probe_evidence_slice": "EC-7G-B-A",
					"raw_append_scan_regression": True,
					"raw_append_site": dict(item),
				}
			)
		)
	return rows


def classify_soft_gate_lane(row: Dict[str, Any]) -> Dict[str, Any]:
	result = dict(row or {})
	lane_class = _clean_text(result.get("lane_class"))
	model_role = _clean_text(result.get("model_role"))
	metadata_status = _clean_text(result.get("metadata_status"))
	strict_readiness_status = _clean_text(result.get("strict_readiness_status"))
	fallback_used = _bool(result.get("fallback_used"))
	role_compliance = _clean_text(result.get("role_compliance")) or COMPLIANCE_UNKNOWN
	authority_source = _clean_text(result.get("authority_source"))
	final_authority_status = _clean_text(result.get("final_answer_authority_status"))
	preflight_status = _clean_text(result.get("preflight_status"))
	strict_ready_flag = bool(result.get("strict_enforcement_ready"))

	decision = SOFT_GATE_WARN
	reason = "metadata requires release-readiness review"
	if bool(result.get("direct_assistant_append_regression")):
		decision = SOFT_GATE_BLOCK_RELEASE
		reason = "active direct assistant append inventory regressed"
	elif final_authority_status in {"missing", "blocked", "failed", "missing_authority", "incomplete_authority"}:
		decision = SOFT_GATE_BLOCK_RELEASE
		reason = "final-answer authority failure blocks release readiness"
	elif lane_class in HELPER_TOOL_CLASSES and final_authority_status == "satisfied_by_helper_metadata":
		decision = SOFT_GATE_BLOCK_RELEASE
		reason = "helper/tool provenance cannot satisfy final-answer business authority"
	elif lane_class in DETERMINISTIC_CLASSES:
		if model_role != ROLE_DETERMINISTIC or not authority_source:
			decision = SOFT_GATE_BLOCK_RELEASE
			reason = "deterministic lane is missing explicit deterministic authority metadata"
		else:
			decision = NOT_APPLICABLE_DETERMINISTIC
			reason = "deterministic lane is explicit and not an AI strict-enforcement target"
	elif lane_class == LANE_CLASS_POLICY_BOUNDARY:
		if model_role != ROLE_POLICY_BOUNDARY or authority_source != "policy_boundary" or preflight_status != "bounded":
			decision = SOFT_GATE_BLOCK_RELEASE
			reason = "policy-boundary lane lacks bounded policy authority"
		else:
			decision = NOT_APPLICABLE_CONTROL
			reason = "policy boundary is explicit and not an AI strict-enforcement target"
	elif lane_class in {LANE_CLASS_CONTROL_META, LANE_CLASS_ERROR_FALLBACK}:
		if not authority_source:
			decision = SOFT_GATE_BLOCK_RELEASE
			reason = "control/error lane lacks explicit non-business authority"
		else:
			decision = NOT_APPLICABLE_CONTROL
			reason = "control/error lane is explicit and not an AI strict-enforcement target"
	elif lane_class in AI_PROVENANCE_CLASSES:
		if strict_readiness_status == STRICT_STATUS_READY and (fallback_used or _is_missing_metadata(result)):
			decision = SOFT_GATE_BLOCK_RELEASE
			reason = "AI/helper provenance claims strict-ready while fallback or missing metadata is present"
		elif strict_ready_flag and strict_readiness_status != STRICT_STATUS_READY:
			decision = SOFT_GATE_BLOCK_RELEASE
			reason = "strict_enforcement_ready flag contradicts strict-readiness status"
		elif _is_missing_metadata(result) or fallback_used or strict_readiness_status in {
			STRICT_STATUS_SOFT_BLOCK,
			STRICT_STATUS_NOT_READY_MISSING_METADATA,
		}:
			decision = SOFT_GATE_WARN
			reason = "AI/helper provenance is degraded or missing metadata; release review required, runtime remains unaffected"
		elif strict_readiness_status == STRICT_STATUS_READY and role_compliance == COMPLIANCE_COMPLIANT:
			decision = SOFT_GATE_PASS
			reason = "complete provenance is strict-ready for soft-gate consideration only"

	result.setdefault("lane_id", "unknown_lane")
	result.setdefault("expected_lane_class", lane_class)
	result.setdefault("expected_model_role", expected_role_for_lane_class(lane_class))
	result.setdefault("fallback_reason", "")
	result.setdefault("probe_evidence_slice", "unknown")
	result.setdefault("final_answer_authority_source", "unknown")
	result["lane_class"] = lane_class
	result["model_role"] = model_role
	result["metadata_status"] = metadata_status
	result["strict_readiness_status"] = strict_readiness_status
	result["strict_enforcement_ready"] = strict_ready_flag
	result["fallback_used"] = fallback_used
	result["role_compliance"] = role_compliance
	result["authority_source"] = authority_source
	result["final_answer_authority_status"] = final_authority_status
	result["preflight_status"] = preflight_status
	result["soft_gate_decision"] = decision
	result["reason"] = reason
	result["release_readiness_impact"] = _release_impact(decision)
	result["runtime_effect"] = RUNTIME_EFFECT_NONE
	result["observed_metadata"] = _observed_metadata(result)
	result["expected_metadata"] = _expected_metadata(result)
	for field in REQUIRED_LANE_FIELDS:
		result.setdefault(field, "")
	return result


def _summary_counts(lane_results: Sequence[Dict[str, Any]]) -> Dict[str, int]:
	counts = {
		NOT_APPLICABLE_CONTROL: 0,
		NOT_APPLICABLE_DETERMINISTIC: 0,
		SOFT_GATE_BLOCK_RELEASE: 0,
		SOFT_GATE_PASS: 0,
		SOFT_GATE_WARN: 0,
	}
	for row in lane_results:
		decision = _clean_text(row.get("soft_gate_decision"))
		counts[decision] = counts.get(decision, 0) + 1
	return dict(sorted(counts.items()))


def _direct_append_inventory(inventory_report: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"active_runtime_direct_assistant_append_count": int(inventory_report.get("active_runtime_direct_assistant_append_count") or 0),
		"inventory_count": int(inventory_report.get("inventory_count") or 0),
		"migrated_authorized_paths_length": len(list(inventory_report.get("migrated_authorized_paths") or [])),
		"authorized_runtime_append_sink_count": int(inventory_report.get("authorized_runtime_append_sink_count") or 0),
		"excluded_non_runtime_append_count": int(inventory_report.get("excluded_non_runtime_append_count") or 0),
	}


def build_strict_readiness_soft_gate_dry_run_report(
	*,
	root_path: str | Path | None = ".",
	branch: str = "",
	head: str = "",
	lane_rows: Sequence[Dict[str, Any]] | None = None,
	inventory_report: Dict[str, Any] | None = None,
	raw_scan_rows: Sequence[Dict[str, Any]] | None = None,
	generated_at: str | None = None,
) -> Dict[str, Any]:
	inventory = dict(inventory_report or build_final_answer_emission_dry_run_report(reviewer="codex_ec7g_b"))
	direct_inventory = _direct_append_inventory(inventory)
	raw_scan = [dict(item) for item in (raw_scan_rows if raw_scan_rows is not None else raw_assistant_append_scan(root_path=root_path))]
	rows = [classify_soft_gate_lane(row) for row in list(lane_rows or default_lane_evidence_rows())]
	rows.extend(_raw_append_regression_rows(raw_scan))
	if direct_inventory["active_runtime_direct_assistant_append_count"] != 0:
		rows.append(
			classify_soft_gate_lane(
				{
					"lane_id": "direct_assistant_append_inventory_regression",
					"lane_class": LANE_CLASS_CONTROL_META,
					"model_role": ROLE_CONTROL_META,
					"metadata_status": METADATA_STATUS_MISSING,
					"strict_readiness_status": STRICT_STATUS_NOT_READY_MISSING_METADATA,
					"strict_enforcement_ready": False,
					"fallback_used": False,
					"role_compliance": COMPLIANCE_UNKNOWN,
					"authority_source": "",
					"final_answer_authority_status": "failed",
					"final_answer_authority_source": "direct_append_inventory",
					"preflight_status": "failed",
					"probe_evidence_slice": "EC-3/EC-7G-B",
					"direct_assistant_append_regression": True,
				}
			)
		)
	release_blockers = [row for row in rows if row.get("soft_gate_decision") == SOFT_GATE_BLOCK_RELEASE]
	warnings = [row for row in rows if row.get("soft_gate_decision") == SOFT_GATE_WARN]
	return {
		"type": STRICT_READINESS_SOFT_GATE_CONTRACT_TYPE,
		"contract_version": CONTRACT_VERSION,
		"slice_id": SLICE_ID,
		"runtime_effect": RUNTIME_EFFECT_NONE,
		"strict_enforcement_enabled": False,
		"branch": branch or _git_value(root_path, ["branch", "--show-current"]),
		"head": head or _git_value(root_path, ["rev-parse", "--short", "HEAD"]),
		"generated_at": generated_at or _utc_now(),
		"summary_counts": _summary_counts(rows),
		"direct_assistant_append_inventory": direct_inventory,
		"raw_assistant_append_scan": raw_scan,
		"ec7f_probe_closure_evidence": {
			"closure_report": "qwen_erp_ec_7f_f_runtime_metadata_probe_closure_2026-05-19.md",
			"metadata_probe_group_passed": 86,
			"authorized_emission_checks_passed": 13,
			"final_answer_inventory_expected": "0 / 1 / 27",
		},
		"lane_results": rows,
		"release_blockers": release_blockers,
		"warnings": warnings,
		"non_goals": list(NON_GOALS),
		"final_decision": (
			"ec_7g_b_soft_gate_dry_run_blocked_requires_release_readiness_fix"
			if release_blockers
			else "ec_7g_b_soft_gate_dry_run_ready_for_counterpart_review"
		),
	}


def render_strict_readiness_soft_gate_markdown(report: Dict[str, Any]) -> str:
	lines: List[str] = [
		"# EC-7G-B Strict-Readiness Soft-Gate Dry-Run Report",
		"",
		f"Decision: {report.get('final_decision')}",
		"",
		f"Generated: {report.get('generated_at')}",
		f"Branch: {report.get('branch')}",
		f"Head: {report.get('head')}",
		f"Runtime effect: `{report.get('runtime_effect')}`",
		f"Strict enforcement enabled: `{bool(report.get('strict_enforcement_enabled'))}`",
		"",
		"## Scope",
		"",
		"EC-7G-B is observe/report-only. It does not enforce, block runtime, change routing, change model behavior, change report selection, change answer text, or change final-answer authority.",
		"",
		"## Summary Counts",
		"",
		"| Classification | Count |",
		"|---|---:|",
	]
	for decision, count in dict(report.get("summary_counts") or {}).items():
		lines.append(f"| `{decision}` | {count} |")
	inventory = dict(report.get("direct_assistant_append_inventory") or {})
	lines.extend(
		[
			"",
			"## Direct Assistant Append Inventory",
			"",
			f"- Active runtime direct assistant append count: `{inventory.get('active_runtime_direct_assistant_append_count')}`",
			f"- Inventory count: `{inventory.get('inventory_count')}`",
			f"- Migrated authorized paths length: `{inventory.get('migrated_authorized_paths_length')}`",
			f"- Authorized runtime append sink count: `{inventory.get('authorized_runtime_append_sink_count')}`",
			f"- Excluded non-runtime append count: `{inventory.get('excluded_non_runtime_append_count')}`",
			"",
			"## Raw Assistant Append Scan",
			"",
		]
	)
	for item in list(report.get("raw_assistant_append_scan") or []):
		lines.append(f"- `{_clean_text(item.get('relative_file_path'))}:{int(item.get('line') or 0)}` `{_clean_text(item.get('source'))}`")
	if not list(report.get("raw_assistant_append_scan") or []):
		lines.append("- No raw assistant append sinks found.")
	lines.extend(
		[
			"",
			"## EC-7F Probe Closure Evidence",
			"",
			f"- Closure report: `{dict(report.get('ec7f_probe_closure_evidence') or {}).get('closure_report')}`",
			f"- Metadata/probe group: `{dict(report.get('ec7f_probe_closure_evidence') or {}).get('metadata_probe_group_passed')} passed`",
			f"- Authorized-emission checks: `{dict(report.get('ec7f_probe_closure_evidence') or {}).get('authorized_emission_checks_passed')} passed`",
			"",
			"## Lane Results",
			"",
			"| Lane | Class | Role | Metadata | Strict readiness | Fallback | Authority | Decision | Impact |",
			"|---|---|---|---|---|---|---|---|---|",
		]
	)
	for row in list(report.get("lane_results") or []):
		lines.append(
			"| {lane} | {lane_class} | {role} | {metadata} | {strict} | {fallback} | {authority} | {decision} | {impact} |".format(
				lane=_clean_text(row.get("lane_id")),
				lane_class=_clean_text(row.get("lane_class")),
				role=_clean_text(row.get("model_role")),
				metadata=_clean_text(row.get("metadata_status")),
				strict=_clean_text(row.get("strict_readiness_status")),
				fallback=str(bool(row.get("fallback_used"))).lower(),
				authority=_clean_text(row.get("final_answer_authority_status")),
				decision=_clean_text(row.get("soft_gate_decision")),
				impact=_clean_text(row.get("release_readiness_impact")),
			)
		)
	lines.extend(["", "## Release Blockers"])
	blockers = list(report.get("release_blockers") or [])
	if blockers:
		for row in blockers:
			lines.append(f"- `{_clean_text(row.get('lane_id'))}`: {_clean_text(row.get('reason'))}")
	else:
		lines.append("- None.")
	lines.extend(["", "## Warnings"])
	warnings = list(report.get("warnings") or [])
	if warnings:
		for row in warnings:
			lines.append(f"- `{_clean_text(row.get('lane_id'))}`: {_clean_text(row.get('reason'))}")
	else:
		lines.append("- None.")
	lines.extend(["", "## Non-Goals"])
	for non_goal in list(report.get("non_goals") or []):
		lines.append(f"- `{_clean_text(non_goal)}`")
	lines.extend(["", "## Final Recommendation", "", f"`{_clean_text(report.get('final_decision'))}`", ""])
	return "\n".join(lines)


def write_strict_readiness_soft_gate_reports(
	*,
	root_path: str | Path | None = ".",
	out_dir: str | Path = DEFAULT_REPORT_DIR,
) -> Dict[str, Any]:
	report = build_strict_readiness_soft_gate_dry_run_report(root_path=root_path)
	target_dir = _project_path(root_path, out_dir)
	target_dir.mkdir(parents=True, exist_ok=True)
	json_path = target_dir / DEFAULT_REPORT_JSON
	markdown_path = target_dir / DEFAULT_REPORT_MD
	report["report_json_artifact_path"] = str(json_path)
	report["report_markdown_artifact_path"] = str(markdown_path)
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_path.write_text(render_strict_readiness_soft_gate_markdown(report) + "\n", encoding="utf-8")
	return report
