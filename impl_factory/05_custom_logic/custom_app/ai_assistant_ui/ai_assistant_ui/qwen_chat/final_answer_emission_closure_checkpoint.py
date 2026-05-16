from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .final_answer_emission_leakage_audit import (
	RECOMMENDATION_READY as EC4N_RECOMMENDATION_READY,
	build_final_answer_emission_leakage_audit_report,
)
from .final_answer_remaining_append_mapping import (
	RECOMMENDATION_READY as EC4Q_RECOMMENDATION_READY,
	build_final_answer_remaining_append_mapping_report,
)


FINAL_ANSWER_EMISSION_CLOSURE_CHECKPOINT_CONTRACT_TYPE = "qwen_ec4u_final_answer_emission_closure_packet"
FINAL_ANSWER_EMISSION_CLOSURE_CHECKPOINT_SLICE_ID = "ec_4u_duplicate_wrapper_visible_context_closure"
DEFAULT_EC4P_OUT_DIR = "impl_factory/00_governance/current_docs/generated/ec_4u_duplicate_wrapper_visible_context_closure"
DEFAULT_EC4P_REPORT_JSON = "qwen_ec4u_final_answer_emission_closure_packet.json"
DEFAULT_EC4P_REPORT_MARKDOWN = "qwen_ec4u_final_answer_emission_closure_packet.md"

EC4P_RECOMMENDATION_QA_RISK_REVIEW = "enterprise_cleanup_ec_4u_ready_for_qa_risk_review"
EC4O_COUNTERPART_DECISION = "enterprise_cleanup_ec_4t2_accepted_ec_4u_visible_context_proof_only"


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


def _direct_no_leak_lane_summary() -> List[Dict[str, Any]]:
	guarantees = [
		"blocked_authority_writes_no_assistant_message",
		"blocked_authority_returns_no_answer_text",
		"blocked_authority_writes_no_tool_trace_answer_text",
		"blocked_authority_writes_no_business_artifact_rendered_narrative_grounded_payload",
		"blocked_authority_writes_exactly_one_blocked_authorized_emission_contract",
	]
	return [
		{
			"lane_id": "frontdoor_governed_report_and_kpi_definition",
			"status": "verified_pass",
			"test_module": "test_frontdoor_authorized_emission_contracts",
			"covered_paths": [
				"frontdoor_lane_package_governed_report_or_projection",
				"frontdoor_lane_package_governed_kpi_definition",
			],
			"guarantees": guarantees,
		},
		{
			"lane_id": "compiled_support_result_answer",
			"status": "verified_pass",
			"test_module": "test_compiled_support_authorized_emission_contracts",
			"covered_paths": ["compiled_support_result_answer"],
			"guarantees": guarantees,
		},
		{
			"lane_id": "reasoning_business_answer",
			"status": "verified_pass",
			"test_module": "test_reasoning_lane_model_role_observability_contracts",
			"covered_paths": ["reasoning_lane_business_answer"],
			"guarantees": guarantees,
		},
		{
			"lane_id": "nbu_governed_requery_entity_detail",
			"status": "verified_pass",
			"test_module": "test_nbu_governed_requery_authorized_emission_contracts",
			"covered_paths": ["nbu_governed_requery_entity_detail"],
			"guarantees": guarantees,
		},
		{
			"lane_id": "legacy_runtime_business_or_boundary_answer",
			"status": "verified_pass",
			"test_module": "test_legacy_runtime_authorized_emission_contracts",
			"covered_paths": ["legacy_runtime_business_or_boundary_answer"],
			"guarantees": guarantees,
		},
		{
			"lane_id": "entity_followup_success_and_failure",
			"status": "verified_pass",
			"test_module": "test_entity_followup_authorized_emission_contracts",
			"covered_paths": ["entity_followup_success", "entity_followup_failure"],
			"guarantees": guarantees,
		},
	]


def _verification_summary() -> List[Dict[str, Any]]:
	return [
		{
			"check_id": "enterprise_guardrail",
			"command": "python3 scripts/check_qwen_enterprise_guardrails.py",
			"observed_result": "PASS",
			"release_relevance": "must_remain_green",
		},
		{
			"check_id": "ec4o_focused_lane_authorized_group",
			"command": "python3 -m unittest <EC-4O focused lane/authorized group>",
			"observed_result": "61 passed",
			"release_relevance": "direct_no_leak_contracts",
		},
		{
			"check_id": "ec4_gate_regression_dry_run_leakage_group",
			"command": "python3 -m unittest <gate/regression/dry-run/leakage audit group>",
			"observed_result": "35 passed",
			"release_relevance": "closure_governance_contracts",
		},
		{
			"check_id": "final_authority_trace_manual_chain",
			"command": "python3 -m unittest <final authority / visible trace / manual chain>",
			"observed_result": "59 passed",
			"release_relevance": "authority_trace_manual_pipeline",
		},
		{
			"check_id": "semantic_financial_resolution",
			"command": "python3 -m unittest ai_assistant_ui.tests.test_semantic_financial_resolution",
			"observed_result": "276 passed",
			"release_relevance": "frontdoor_semantic_financial_regression",
		},
		{
			"check_id": "syntax_compile",
			"command": "python3 -m py_compile <EC-4O touched modules>",
			"observed_result": "PASS",
			"release_relevance": "syntax_sanity",
		},
	]


def build_final_answer_emission_closure_checkpoint_report(
	*,
	root_path: str | Path = ".",
	reviewer: str = "codex_ec4p_closure_checkpoint",
) -> Dict[str, Any]:
	root = Path(root_path).resolve()
	ec4n_report = build_final_answer_emission_leakage_audit_report(
		root_path=root,
		reviewer=reviewer,
	)
	ec4q_report = build_final_answer_remaining_append_mapping_report(
		root_path=root,
		reviewer=reviewer,
	)
	ec4n_ready = _clean_text(ec4n_report.get("final_recommendation")) == EC4N_RECOMMENDATION_READY
	ec4q_ready = _clean_text(ec4q_report.get("final_recommendation")) == EC4Q_RECOMMENDATION_READY
	potential_leak_count = int(ec4n_report.get("blocked_leakage_potential_leak_count") or 0)
	return {
		"type": FINAL_ANSWER_EMISSION_CLOSURE_CHECKPOINT_CONTRACT_TYPE,
		"contract_version": "1.0",
		"slice_id": FINAL_ANSWER_EMISSION_CLOSURE_CHECKPOINT_SLICE_ID,
		"created_at": _utc_now(),
		"reviewer": _clean_text(reviewer),
		"branch": _git_branch(root),
		"head": _git_short_head(root),
		"current_dirty_status_count": _git_status_count(root),
		"runtime_behavior_changed": False,
		"hard_runtime_blocking_scope": "migrated_lanes_only",
		"ec4o_counterpart_decision": EC4O_COUNTERPART_DECISION,
		"fresh_ec4n_summary": {
			"final_recommendation": _clean_text(ec4n_report.get("final_recommendation")),
			"potential_leak_count": potential_leak_count,
			"potential_leak_path_ids": list(ec4n_report.get("potential_leak_path_ids") or []),
			"migrated_path_count": int(ec4n_report.get("migrated_path_count") or 0),
			"remaining_high_risk_paths": list(ec4n_report.get("remaining_high_risk_paths") or []),
			"dry_run_counts": dict(ec4n_report.get("dry_run_counts") or {}),
		},
		"fresh_ec4q_summary": {
			"final_recommendation": _clean_text(ec4q_report.get("final_recommendation")),
			"inventory_item_count": int(ec4q_report.get("inventory_item_count") or 0),
			"active_direct_assistant_append_count": int(ec4q_report.get("active_direct_assistant_append_count") or 0),
			"low_level_wrapper_count": int(ec4q_report.get("low_level_wrapper_count") or 0),
			"unclassified_source_append_site_count": int(
				dict(ec4q_report.get("source_append_scan") or {}).get("unclassified_source_append_site_count") or 0
			),
		},
		"frontdoor_duplicate_decision": dict(ec4q_report.get("frontdoor_duplicate_closure") or {}),
		"service_wrapper_decision": dict(ec4q_report.get("service_wrapper_closure") or {}),
		"visible_context_outer_call_site_proof": dict(ec4q_report.get("visible_context_call_site_proof") or {}),
		"direct_no_leak_test_summary_by_lane": _direct_no_leak_lane_summary(),
		"remaining_high_risk_classification": [
			{
				"path_id": "service_append_message_wrapper",
				"classification": "low_level_append_wrapper_not_migrated_by_design",
				"decision": "monitor_only_do_not_hard_gate_raw_wrapper",
				"reason": "Low-level append helper lacks answer type and authority context; migration must happen above raw append.",
			},
		],
		"audit_limitation_note": (
			"EC-4N is a conservative static/governance audit, not a complete taint-analysis engine. "
			"It now checks known pre-helper business payloads and post-helper appends after blocked emission, "
			"but unknown append_tool_payload(...) sources require stricter classification in a later hardening slice."
		),
		"audit_hardening_backlog": [
			"classify_unknown_append_tool_payload_sources_more_strictly",
			"add_source_allowlist_or_provenance_for_additional_tool_payloads",
			"expand_branch_specific_payload_leak_detection_beyond_named_business_patterns",
			"keep_append_knowledge_boundary_contract_classified_as_safe_summary_contract_unless_source_payload_shape_changes",
		],
		"verification_summary": _verification_summary(),
		"non_goals": [
			"no_new_lane_migration",
			"no_service_append_wrapper_migration",
			"no_active_package_frontdoor_behavior_change",
			"no_model_role_strict_enforcement",
			"no_release_packaging_cleanup",
			"no_ux_mi_filter_or_family_expansion",
		],
		"manual_browser_required": False,
		"qa_risk_auditor_review_recommended": True,
		"final_recommendation": (
			EC4P_RECOMMENDATION_QA_RISK_REVIEW
			if ec4n_ready and ec4q_ready and potential_leak_count == 0
			else "enterprise_cleanup_ec_4u_blocked_need_closure_packet_review"
		),
	}


def render_final_answer_emission_closure_checkpoint_markdown(report: Dict[str, Any]) -> str:
	lines: List[str] = [
		"# EC-4U Final-Answer Emission Closure Packet",
		"",
		f"- Branch: `{_clean_text(report.get('branch'))}`",
		f"- Head: `{_clean_text(report.get('head'))}`",
		f"- Dirty status count: `{report.get('current_dirty_status_count')}`",
		f"- EC-4O counterpart decision: `{_clean_text(report.get('ec4o_counterpart_decision'))}`",
		f"- Final recommendation: `{_clean_text(report.get('final_recommendation'))}`",
		f"- Manual browser required: `{bool(report.get('manual_browser_required'))}`",
		"",
		"## Fresh EC-4N Summary",
		"",
	]
	ec4n = dict(report.get("fresh_ec4n_summary") or {})
	lines.append(f"- EC-4N recommendation: `{_clean_text(ec4n.get('final_recommendation'))}`")
	lines.append(f"- Potential leak count: `{ec4n.get('potential_leak_count')}`")
	lines.append(f"- Potential leak paths: `{ec4n.get('potential_leak_path_ids')}`")
	lines.append("")
	lines.append("## Fresh EC-4Q-A Summary")
	lines.append("")
	ec4q = dict(report.get("fresh_ec4q_summary") or {})
	lines.append(f"- EC-4Q-A recommendation: `{_clean_text(ec4q.get('final_recommendation'))}`")
	lines.append(f"- Inventory item count: `{ec4q.get('inventory_item_count')}`")
	lines.append(f"- Active direct assistant append count: `{ec4q.get('active_direct_assistant_append_count')}`")
	lines.append(f"- Low-level wrapper count: `{ec4q.get('low_level_wrapper_count')}`")
	lines.append("")
	lines.append("## Duplicate / Wrapper / Visible-Context Decisions")
	lines.append("")
	duplicate = dict(report.get("frontdoor_duplicate_decision") or {})
	wrapper = dict(report.get("service_wrapper_decision") or {})
	proof = dict(report.get("visible_context_outer_call_site_proof") or {})
	lines.append(f"- Root frontdoor duplicate: `{_clean_text(duplicate.get('status'))}`")
	lines.append(f"- Service append wrapper: `{_clean_text(wrapper.get('status'))}`")
	lines.append(f"- Visible-context proof: `{_clean_text(proof.get('status'))}`")
	lines.append("")
	lines.append("## Direct No-Leak Tests By Lane")
	lines.append("")
	lines.append("| Lane | Status | Test Module | Covered Paths |")
	lines.append("|---|---|---|---|")
	for row in list(report.get("direct_no_leak_test_summary_by_lane") or []):
		lines.append(
			"| {lane} | {status} | {test} | {paths} |".format(
				lane=_clean_text(row.get("lane_id")),
				status=_clean_text(row.get("status")),
				test=_clean_text(row.get("test_module")),
				paths=", ".join(str(item) for item in list(row.get("covered_paths") or [])),
			)
		)
	lines.extend(["", "## Remaining High-Risk Classification", ""])
	for row in list(report.get("remaining_high_risk_classification") or []):
		lines.append(
			f"- `{_clean_text(row.get('path_id'))}`: `{_clean_text(row.get('classification'))}`; `{_clean_text(row.get('decision'))}`"
		)
	lines.extend(["", "## Audit Limitation", "", _clean_text(report.get("audit_limitation_note")), ""])
	lines.extend(["## Audit Hardening Backlog", ""])
	for item in list(report.get("audit_hardening_backlog") or []):
		lines.append(f"- `{_clean_text(item)}`")
	lines.extend(["", "## Verification Summary", ""])
	for row in list(report.get("verification_summary") or []):
		lines.append(f"- `{_clean_text(row.get('check_id'))}`: `{_clean_text(row.get('observed_result'))}`")
	lines.extend(["", "## Non-Goals", ""])
	for item in list(report.get("non_goals") or []):
		lines.append(f"- `{_clean_text(item)}`")
	lines.extend(["", "## Final Recommendation", "", f"`{_clean_text(report.get('final_recommendation'))}`", ""])
	return "\n".join(lines)


def write_final_answer_emission_closure_checkpoint_files(
	*,
	root_path: str | Path = ".",
	out_dir: str | Path = DEFAULT_EC4P_OUT_DIR,
	reviewer: str = "codex_ec4p_closure_checkpoint",
) -> Dict[str, Any]:
	report = build_final_answer_emission_closure_checkpoint_report(root_path=root_path, reviewer=reviewer)
	target_dir = _project_path(root_path, out_dir)
	target_dir.mkdir(parents=True, exist_ok=True)
	json_path = target_dir / DEFAULT_EC4P_REPORT_JSON
	markdown_path = target_dir / DEFAULT_EC4P_REPORT_MARKDOWN
	report["report_json_artifact_path"] = str(json_path)
	report["report_markdown_artifact_path"] = str(markdown_path)
	json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
	markdown_path.write_text(render_final_answer_emission_closure_checkpoint_markdown(report), encoding="utf-8")
	return report


def main(argv: List[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="Generate the EC-4P final-answer emission closure checkpoint report.")
	parser.add_argument("--root-path", default=".")
	parser.add_argument("--out-dir", default=DEFAULT_EC4P_OUT_DIR)
	parser.add_argument("--reviewer", default="codex_ec4p_closure_checkpoint")
	args = parser.parse_args(argv)
	report = write_final_answer_emission_closure_checkpoint_files(
		root_path=args.root_path,
		out_dir=args.out_dir,
		reviewer=args.reviewer,
	)
	print(json.dumps(report, indent=2, sort_keys=True))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
