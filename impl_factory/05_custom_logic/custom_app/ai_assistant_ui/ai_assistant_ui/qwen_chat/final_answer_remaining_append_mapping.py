from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .final_answer_emission_dry_run import (
	ANSWER_TYPE_BUSINESS_FACTUAL,
	ANSWER_TYPE_CONTROL,
	ANSWER_TYPE_GOVERNED_REPORT,
	ANSWER_TYPE_LOW_LEVEL,
	ANSWER_TYPE_POLICY_BOUNDARY,
	ANSWER_TYPE_TRACE,
	ANSWER_TYPE_VISIBLE_CONTEXT,
	AUTHORIZED_APPEND_SITES,
	EMISSION_PATH_INVENTORY,
	EXCLUDED_APPEND_SITES,
	build_final_answer_emission_dry_run_report,
)


FINAL_ANSWER_REMAINING_APPEND_MAPPING_CONTRACT_TYPE = "qwen_ec4q_remaining_append_mapping_contract"
FINAL_ANSWER_REMAINING_APPEND_MAPPING_SLICE_ID = "ec_4q_a_remaining_append_mapping"
DEFAULT_EC4Q_OUT_DIR = "impl_factory/00_governance/current_docs/generated/ec_4q_a_remaining_append_mapping"
DEFAULT_EC4Q_REPORT_JSON = "qwen_ec4q_a_remaining_append_mapping_report.json"
DEFAULT_EC4Q_REPORT_MARKDOWN = "qwen_ec4q_a_remaining_append_mapping_report.md"

RECOMMENDATION_READY = "enterprise_cleanup_ec_4q_a_ready_for_counterpart_review"
RECOMMENDATION_BLOCKED = "enterprise_cleanup_ec_4q_a_blocked_need_mapping_fix"

DECISION_MIGRATE = "migrate"
DECISION_EXEMPT_WITH_CONTRACT = "exempt_with_explicit_contract"
DECISION_DEFER_DUPLICATE_OR_INACTIVE = "defer_duplicate_or_inactive"
DECISION_MONITOR_ONLY = "monitor_only"
DECISION_BLOCKING = "blocking_until_fixed"


PATH_DECISIONS: Dict[str, Dict[str, Any]] = {
	"service_append_message_wrapper": {
		"answer_class": "wrapper",
		"active_import_status": "active_low_level_infrastructure",
		"direct_append_count": 0,
		"pre_helper_payload_behavior": "not_applicable_low_level_role_wrapper",
		"post_helper_payload_behavior": "not_applicable_low_level_role_wrapper",
		"leak_risk": "monitor_high",
		"decision": DECISION_MONITOR_ONLY,
		"required_test_before_closure": "source inventory keeps wrapper separate from direct answer lanes",
	},
	"frontdoor_lane_root_duplicate": {
		"answer_class": "duplicate/inactive",
		"active_import_status": "compatibility_facade_not_imported_by_service",
		"direct_append_count": 0,
		"pre_helper_payload_behavior": "not_applicable_compatibility_facade",
		"post_helper_payload_behavior": "not_applicable_compatibility_facade",
		"leak_risk": "closed_by_ec4u_facade_import_audit",
		"decision": DECISION_DEFER_DUPLICATE_OR_INACTIVE,
		"required_test_before_closure": "import audit proves service imports package frontdoor lane and root duplicate has no direct assistant append",
	},
	"visible_context_trace_inspection": {
		"answer_class": "trace/debug",
		"active_import_status": "active_runtime_diagnostic",
		"direct_append_count": 1,
		"pre_helper_payload_behavior": "trace inspection contract before append",
		"post_helper_payload_behavior": "diagnostic trace render only",
		"leak_risk": "low",
		"decision": DECISION_EXEMPT_WITH_CONTRACT,
		"required_test_before_closure": "trace/debug answer exposes authority status and does not emit business claim",
	},
	"artifact_boundary_evidence_answer": {
		"answer_class": "business factual",
		"active_import_status": "active_runtime_lane",
		"direct_append_count": 1,
		"pre_helper_payload_behavior": "evidence/narrative payloads can be appended before answer",
		"post_helper_payload_behavior": "audit envelope after append",
		"leak_risk": "medium_high_business",
		"decision": DECISION_MIGRATE,
		"required_test_before_closure": "missing artifact/grounded authority blocks with no assistant or evidence leak",
	},
	"artifact_boundary_grounded_evidence_refusal": {
		"answer_class": "policy boundary/refusal",
		"active_import_status": "active_runtime_lane",
		"direct_append_count": 1,
		"pre_helper_payload_behavior": "boundary/recovery payloads before answer",
		"post_helper_payload_behavior": "audit envelope after append",
		"leak_risk": "medium",
		"decision": DECISION_MIGRATE,
		"required_test_before_closure": "bounded refusal uses policy_boundary_refusal and no post-block payload leak",
	},
	"artifact_boundary_enrichment_refusal": {
		"answer_class": "policy boundary/refusal",
		"active_import_status": "active_runtime_lane",
		"direct_append_count": 1,
		"pre_helper_payload_behavior": "boundary/recovery payloads before answer",
		"post_helper_payload_behavior": "audit envelope after append",
		"leak_risk": "medium",
		"decision": DECISION_MIGRATE,
		"required_test_before_closure": "bounded enrichment refusal uses policy_boundary_refusal and no post-block payload leak",
	},
	"nbu_presentation_safe_response": {
		"answer_class": "control/meta",
		"active_import_status": "active_runtime_lane",
		"direct_append_count": 1,
		"pre_helper_payload_behavior": "nbu trace/activation/execution path before answer",
		"post_helper_payload_behavior": "audit only if interaction_contract exists",
		"leak_risk": "medium",
		"decision": DECISION_EXEMPT_WITH_CONTRACT,
		"required_test_before_closure": "explicit control_meta_authority required even when interaction_contract is missing",
	},
	"local_followup_transform": {
		"answer_class": "visible context",
		"active_import_status": "active_runtime_helper",
		"direct_append_count": 1,
		"pre_helper_payload_behavior": "transformed answer is appended before caller audit",
		"post_helper_payload_behavior": "caller builds audit from latest assistant payload",
		"leak_risk": "medium_high_business",
		"decision": DECISION_MIGRATE,
		"required_test_before_closure": "local transform uses visible-context authority before append and blocks without return-text leak",
	},
	"clarification_show_options": {
		"answer_class": "clarification/control",
		"active_import_status": "active_runtime_lane",
		"direct_append_count": 1,
		"pre_helper_payload_behavior": "control contracts before answer",
		"post_helper_payload_behavior": "pending clarification stored after answer",
		"leak_risk": "low",
		"decision": DECISION_EXEMPT_WITH_CONTRACT,
		"required_test_before_closure": "explicit control_meta_authority and non-business answer classification",
	},
	"clarification_pending_reask_or_stop": {
		"answer_class": "clarification/control",
		"active_import_status": "active_runtime_lane",
		"direct_append_count": 1,
		"pre_helper_payload_behavior": "control contracts before answer",
		"post_helper_payload_behavior": "pending clarification stored after answer when still active",
		"leak_risk": "low",
		"decision": DECISION_EXEMPT_WITH_CONTRACT,
		"required_test_before_closure": "explicit control_meta_authority and non-business answer classification",
	},
	"recovery_guidance_answer": {
		"answer_class": "control/meta",
		"active_import_status": "active_runtime_lane",
		"direct_append_count": 1,
		"pre_helper_payload_behavior": "repair contracts before answer",
		"post_helper_payload_behavior": "observability/performance/audit after answer",
		"leak_risk": "medium",
		"decision": DECISION_EXEMPT_WITH_CONTRACT,
		"required_test_before_closure": "explicit control_meta_authority and audit before answer or authorized helper",
	},
	"service_prior_branch_clarification_restore": {
		"answer_class": "clarification/control",
		"active_import_status": "active_service_path",
		"direct_append_count": 1,
		"pre_helper_payload_behavior": "control payloads before answer",
		"post_helper_payload_behavior": "no final authority",
		"leak_risk": "low",
		"decision": DECISION_EXEMPT_WITH_CONTRACT,
		"required_test_before_closure": "explicit control_meta_authority for prior-branch restore",
	},
	"service_compound_continue_completed": {
		"answer_class": "control/meta",
		"active_import_status": "active_service_path",
		"direct_append_count": 1,
		"pre_helper_payload_behavior": "compound control payloads before answer",
		"post_helper_payload_behavior": "audit envelope after answer",
		"leak_risk": "medium",
		"decision": DECISION_EXEMPT_WITH_CONTRACT,
		"required_test_before_closure": "authorized control emission or equivalent pre-append control authority",
	},
	"service_compound_stop": {
		"answer_class": "control/meta",
		"active_import_status": "active_service_path",
		"direct_append_count": 1,
		"pre_helper_payload_behavior": "compound cancellation payloads before answer",
		"post_helper_payload_behavior": "audit envelope after answer",
		"leak_risk": "medium",
		"decision": DECISION_EXEMPT_WITH_CONTRACT,
		"required_test_before_closure": "authorized control emission or equivalent pre-append control authority",
	},
}

EXCLUDED_EC4Q_SOURCE_APPEND_SITES = [
	{
		"site_id": "conversation_control_smoke_seed_direct_assistant",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/evaluation/conversation_control_smokes.py",
		"line_reference": "2334",
		"source_classification": "excluded_evaluation_smoke_append_site",
		"exclusion_reason": "Evaluation/smoke fixture helper, not active user-facing runtime emission.",
	},
	{
		"site_id": "conversation_control_smoke_pending_question_1",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/evaluation/conversation_control_smokes.py",
		"line_reference": "3063",
		"source_classification": "excluded_evaluation_smoke_append_site",
		"exclusion_reason": "Evaluation/smoke pending-clarification fixture helper, not active user-facing runtime emission.",
	},
	{
		"site_id": "conversation_control_smoke_pending_question_2",
		"relative_file_path": "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/evaluation/conversation_control_smokes.py",
		"line_reference": "3162",
		"source_classification": "excluded_evaluation_smoke_append_site",
		"exclusion_reason": "Evaluation/smoke pending-clarification fixture helper, not active user-facing runtime emission.",
	},
]


VISIBLE_CONTEXT_ALLOWED_ADDITIONAL_PAYLOAD_SOURCES = [
	{
		"source_name": "nbu_shadow_tool_payloads",
		"source_classification": "control_shadow_payload",
		"allowed_payload_families": [
			"natural_business_understanding_trace",
			"nbu_shadow_observation",
			"conversation_control_evidence",
		],
		"business_answer_text_allowed": False,
	},
	{
		"source_name": "sequence_cleanup_tool_payloads",
		"source_classification": "compound_control_payload",
		"allowed_payload_families": [
			"compound_request_assessment",
			"compound_sequence_decision",
			"conversation_control_decision",
		],
		"business_answer_text_allowed": False,
	},
	{
		"source_name": "empty_payload_list",
		"source_classification": "no_payload",
		"allowed_payload_families": [],
		"business_answer_text_allowed": False,
	},
]


def _utc_now() -> str:
	return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _clean_text(value: Any) -> str:
	return str(value or "").strip()


def _project_path(root_path: str | Path, relative_path: str | Path) -> Path:
	root = Path(root_path or ".")
	path = Path(relative_path)
	return path if path.is_absolute() else root / path


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


def _source_append_sites(root_path: Path) -> List[Dict[str, Any]]:
	qwen_root = root_path / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat"
	rows: List[Dict[str, Any]] = []
	for path in sorted(qwen_root.rglob("*.py")):
		if "__pycache__" in path.parts:
			continue
		relative = str(path.relative_to(root_path))
		for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
			if '"assistant"' not in line and "'assistant'" not in line:
				continue
			if "append_message(" not in line and "_append_message(" not in line:
				continue
			rows.append(
				{
					"relative_file_path": relative,
					"line": line_no,
					"source": line.strip(),
				}
			)
	return rows


def _known_site_keys() -> set[tuple[str, int]]:
	keys: set[tuple[str, int]] = set()
	for item in [
		*EMISSION_PATH_INVENTORY,
		*AUTHORIZED_APPEND_SITES,
		*EXCLUDED_APPEND_SITES,
		*EXCLUDED_EC4Q_SOURCE_APPEND_SITES,
	]:
		relative = _clean_text(item.get("relative_file_path"))
		line_reference = _clean_text(item.get("line_reference"))
		for token in line_reference.replace(",", "-").split("-"):
			if token.strip().isdigit():
				keys.add((relative, int(token.strip())))
	return keys


def _unclassified_source_append_sites(root_path: Path) -> List[Dict[str, Any]]:
	known = _known_site_keys()
	unclassified: List[Dict[str, Any]] = []
	for row in _source_append_sites(root_path):
		key = (_clean_text(row.get("relative_file_path")), int(row.get("line") or 0))
		if key not in known:
			unclassified.append(row)
	return unclassified


def _decision_counts(rows: List[Dict[str, Any]]) -> Dict[str, int]:
	counts: Dict[str, int] = {}
	for row in rows:
		decision = _clean_text(row.get("decision")) or "unknown"
		counts[decision] = counts.get(decision, 0) + 1
	return counts


def _path_row(item: Dict[str, Any]) -> Dict[str, Any]:
	path_id = _clean_text(item.get("path_id"))
	decision = dict(PATH_DECISIONS.get(path_id) or {})
	return {
		"path_id": path_id,
		"relative_file_path": _clean_text(item.get("relative_file_path")),
		"function_name": _clean_text(item.get("function_name")),
		"line_reference": _clean_text(item.get("line_reference")),
		"active_import_status": _clean_text(decision.get("active_import_status")),
		"direct_append_count": int(decision.get("direct_append_count") or 0),
		"answer_type": _clean_text(item.get("answer_type")),
		"answer_class": _clean_text(decision.get("answer_class")),
		"current_authority_behavior": _clean_text(item.get("authority_availability_status")),
		"audit_timing": _clean_text(item.get("audit_timing")),
		"pre_helper_payload_behavior": _clean_text(decision.get("pre_helper_payload_behavior")),
		"post_helper_payload_behavior": _clean_text(decision.get("post_helper_payload_behavior")),
		"leak_risk": _clean_text(decision.get("leak_risk")),
		"decision": _clean_text(decision.get("decision")),
		"required_test_before_closure": _clean_text(decision.get("required_test_before_closure")),
		"risk_level": _clean_text(item.get("risk_level")),
		"requires_hard_gate": bool(item.get("requires_hard_gate")),
	}


def build_final_answer_remaining_append_mapping_report(
	*,
	root_path: str | Path = ".",
	reviewer: str = "codex_ec4q_a_mapping",
) -> Dict[str, Any]:
	root = Path(root_path).resolve()
	dry_run = build_final_answer_emission_dry_run_report(
		reviewer=reviewer,
		status_count=_git_status_count(root),
	)
	inventory = list(dry_run.get("emission_path_inventory") or [])
	rows = [_path_row(item) for item in inventory]
	missing_decision_path_ids = [
		row["path_id"]
		for row in rows
		if not row.get("decision")
	]
	unclassified_append_sites = _unclassified_source_append_sites(root)
	active_direct = int(dry_run.get("active_runtime_direct_assistant_append_count") or 0)
	wrapper_count = len([row for row in rows if row.get("answer_class") == "wrapper"])
	return {
		"type": FINAL_ANSWER_REMAINING_APPEND_MAPPING_CONTRACT_TYPE,
		"contract_version": "1.0",
		"slice_id": FINAL_ANSWER_REMAINING_APPEND_MAPPING_SLICE_ID,
		"created_at": _utc_now(),
		"reviewer": _clean_text(reviewer),
		"branch": _git_branch(root),
		"head": _git_short_head(root),
		"current_dirty_status_count": _git_status_count(root),
		"runtime_behavior_changed": False,
		"inventory_item_count": len(rows),
		"active_direct_assistant_append_count": active_direct,
		"low_level_wrapper_count": wrapper_count,
		"authorized_helper_sink_count": int(dry_run.get("authorized_runtime_append_sink_count") or 0),
		"excluded_non_runtime_count": int(dry_run.get("excluded_non_runtime_append_count") or 0),
		"count_correction_note": "inventory_item_count includes service_append_message_wrapper; active_direct_assistant_append_count excludes the low-level wrapper.",
		"decision_counts": _decision_counts(rows),
		"remaining_append_inventory": rows,
		"frontdoor_duplicate_closure": {
			"path_id": "frontdoor_lane_root_duplicate",
			"status": "closed_by_compatibility_facade",
			"active_import_status": PATH_DECISIONS["frontdoor_lane_root_duplicate"]["active_import_status"],
			"direct_append_count": PATH_DECISIONS["frontdoor_lane_root_duplicate"]["direct_append_count"],
			"decision": PATH_DECISIONS["frontdoor_lane_root_duplicate"]["decision"],
			"required_test_before_closure": PATH_DECISIONS["frontdoor_lane_root_duplicate"]["required_test_before_closure"],
		},
		"service_wrapper_closure": {
			"path_id": "service_append_message_wrapper",
			"status": "monitored_infrastructure_not_answer_lane",
			"decision": DECISION_MONITOR_ONLY,
			"hard_gate_at_wrapper": False,
			"reason": "The raw wrapper lacks answer type and authority context; EC-4 gates answer lanes above this layer.",
		},
		"visible_context_call_site_proof": {
			"status": "runtime_blocked_authority_probe_passed",
			"proof_type": "blocked_authority_runtime_probe",
			"allowed_additional_payload_sources": VISIBLE_CONTEXT_ALLOWED_ADDITIONAL_PAYLOAD_SOURCES,
			"release_blocking": False,
			"runtime_probe_guarantees": [
				"no_assistant_answer",
				"no_returned_answer_text",
				"no_business_evidence_tool_payload_leak",
				"exactly_one_blocked_authorized_emission_contract",
			],
			"evidence_tests": [
				"test_visible_context_blocked_authority_probe_writes_only_blocked_contract",
			],
			"limitation": "Runtime probe covers forced malformed visible-context authority; static source provenance remains as a conservative companion check.",
		},
		"source_append_scan": {
			"observed_source_append_site_count": len(_source_append_sites(root)),
			"explicit_ec4q_excluded_source_append_sites": EXCLUDED_EC4Q_SOURCE_APPEND_SITES,
			"unclassified_source_append_site_count": len(unclassified_append_sites),
			"unclassified_source_append_sites": unclassified_append_sites,
		},
		"proposed_sequence": [
			"EC-4U duplicate/wrapper closure",
			"EC-4U visible-context blocked-authority proof",
			"QA_Risk Auditor independent review packet",
		],
		"non_goals": [
			"no_runtime_migration_in_ec4q_a",
			"no_service_py_implementation_change",
			"no_model_role_strict_enforcement",
			"no_release_packaging_cleanup",
			"no_ux_mi_filter_or_family_expansion",
		],
		"final_recommendation": (
			RECOMMENDATION_READY
			if not missing_decision_path_ids and not unclassified_append_sites and len(rows) == 1 and active_direct == 0 and wrapper_count == 1
			else RECOMMENDATION_BLOCKED
		),
		"blocking_reasons": [
			*(["missing_path_decisions"] if missing_decision_path_ids else []),
			*(["unclassified_source_append_sites"] if unclassified_append_sites else []),
			*(["count_correction_mismatch"] if not (len(rows) == 1 and active_direct == 0 and wrapper_count == 1) else []),
		],
	}


def render_final_answer_remaining_append_mapping_markdown(report: Dict[str, Any]) -> str:
	lines: List[str] = [
		"# EC-4Q-A Remaining Append Mapping",
		"",
		f"- Branch: `{_clean_text(report.get('branch'))}`",
		f"- Head: `{_clean_text(report.get('head'))}`",
		f"- Dirty status count: `{report.get('current_dirty_status_count')}`",
		f"- Final recommendation: `{_clean_text(report.get('final_recommendation'))}`",
		f"- Inventory item count: `{report.get('inventory_item_count')}`",
		f"- Active direct assistant append count: `{report.get('active_direct_assistant_append_count')}`",
		f"- Low-level wrapper count: `{report.get('low_level_wrapper_count')}`",
		f"- Authorized helper sink count: `{report.get('authorized_helper_sink_count')}`",
		f"- Excluded non-runtime count: `{report.get('excluded_non_runtime_count')}`",
		"",
		"## Inventory",
		"",
		"| Path | Class | Authority | Leak Risk | Decision | Required Test |",
		"|---|---|---|---|---|---|",
	]
	for row in list(report.get("remaining_append_inventory") or []):
		lines.append(
			"| {path} | {klass} | {authority} | {risk} | {decision} | {test} |".format(
				path=_clean_text(row.get("path_id")),
				klass=_clean_text(row.get("answer_class")),
				authority=_clean_text(row.get("current_authority_behavior")),
				risk=_clean_text(row.get("leak_risk")),
				decision=_clean_text(row.get("decision")),
				test=_clean_text(row.get("required_test_before_closure")),
			)
		)
	lines.extend(["", "## Duplicate And Wrapper Closure", ""])
	duplicate = dict(report.get("frontdoor_duplicate_closure") or {})
	wrapper = dict(report.get("service_wrapper_closure") or {})
	lines.append(
		f"- `{_clean_text(duplicate.get('path_id'))}`: `{_clean_text(duplicate.get('status'))}`; direct appends `{duplicate.get('direct_append_count')}`"
	)
	lines.append(
		f"- `{_clean_text(wrapper.get('path_id'))}`: `{_clean_text(wrapper.get('status'))}`; hard gate at wrapper `{bool(wrapper.get('hard_gate_at_wrapper'))}`"
	)
	lines.extend(["", "## Visible Context Call-Site Proof", ""])
	proof = dict(report.get("visible_context_call_site_proof") or {})
	lines.append(f"- Status: `{_clean_text(proof.get('status'))}`")
	lines.append(f"- Proof type: `{_clean_text(proof.get('proof_type'))}`")
	lines.append(f"- Release blocking: `{bool(proof.get('release_blocking'))}`")
	lines.append(f"- Limitation: {_clean_text(proof.get('limitation'))}")
	lines.extend(["", "## Proposed Sequence", ""])
	for item in list(report.get("proposed_sequence") or []):
		lines.append(f"- `{_clean_text(item)}`")
	lines.extend(["", "## Non-Goals", ""])
	for item in list(report.get("non_goals") or []):
		lines.append(f"- `{_clean_text(item)}`")
	lines.extend(["", "## Final Recommendation", "", f"`{_clean_text(report.get('final_recommendation'))}`", ""])
	return "\n".join(lines)


def write_final_answer_remaining_append_mapping_files(
	*,
	root_path: str | Path = ".",
	out_dir: str | Path = DEFAULT_EC4Q_OUT_DIR,
	reviewer: str = "codex_ec4q_a_mapping",
) -> Dict[str, Any]:
	report = build_final_answer_remaining_append_mapping_report(root_path=root_path, reviewer=reviewer)
	target_dir = _project_path(root_path, out_dir)
	target_dir.mkdir(parents=True, exist_ok=True)
	json_path = target_dir / DEFAULT_EC4Q_REPORT_JSON
	markdown_path = target_dir / DEFAULT_EC4Q_REPORT_MARKDOWN
	report["report_json_artifact_path"] = str(json_path)
	report["report_markdown_artifact_path"] = str(markdown_path)
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_path.write_text(render_final_answer_remaining_append_mapping_markdown(report), encoding="utf-8")
	return report


def main(argv: List[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Generate the EC-4Q-A remaining append mapping report.")
	parser.add_argument("--root-path", default=".")
	parser.add_argument("--out-dir", default=DEFAULT_EC4Q_OUT_DIR)
	parser.add_argument("--reviewer", default="codex_ec4q_a_mapping")
	args = parser.parse_args(argv)
	report = write_final_answer_remaining_append_mapping_files(
		root_path=args.root_path,
		out_dir=args.out_dir,
		reviewer=args.reviewer,
	)
	print(json.dumps(report, indent=2, sort_keys=True))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
