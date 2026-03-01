from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def read_engine_tool_message(
    *,
    source_tool: str,
    mode: str,
    selected_report: str,
    selected_score: Any,
    max_steps: int,
    executed_steps: int,
    repeated_call_guard_triggered: bool,
    repair_attempts: int,
    quality_verdict: str,
    failed_check_ids: List[str],
    step_trace: List[Dict[str, Any]],
) -> str:
    return json.dumps(
        {
            "type": "v7_read_engine",
            "phase": "phase6",
            "mode": str(mode or "").strip(),
            "tool": str(source_tool or "").strip(),
            "selected_report": str(selected_report or "").strip(),
            "selected_score": selected_score,
            "max_steps": int(max_steps),
            "executed_steps": int(executed_steps),
            "repair_attempts": int(repair_attempts),
            "quality_verdict": str(quality_verdict or ""),
            "failed_check_ids": list(failed_check_ids or []),
            "repeated_call_guard_triggered": bool(repeated_call_guard_triggered),
            "step_trace": step_trace[:6],
        },
        ensure_ascii=False,
        default=str,
    )


def planner_plan(*, export: bool, pending_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    pending = pending_state if isinstance(pending_state, dict) else {}
    if pending:
        return {
            "action": "run_report",
            "report_name": pending.get("report_name"),
            "filters": pending.get("filters_so_far") if isinstance(pending.get("filters_so_far"), dict) else {},
        }
    return {"action": "run_report", "export": bool(export)}


def build_candidate_report_state(*, resolved: Dict[str, Any], selected_report: str) -> Dict[str, Any]:
    candidate_reports: List[str] = []
    feasible_candidate_reports: List[str] = []
    candidate_scores: Dict[str, Any] = {}
    top_candidates: List[Dict[str, Any]] = []

    for candidate in list(resolved.get("candidate_reports") or []):
        if not isinstance(candidate, dict):
            continue
        report_name = str(candidate.get("report_name") or "").strip()
        if not report_name:
            continue
        hard_blockers = [str(x).strip() for x in list(candidate.get("hard_blockers") or []) if str(x).strip()]
        if report_name not in candidate_reports:
            candidate_reports.append(report_name)
            candidate_scores[report_name] = candidate.get("score")
        if (not hard_blockers) and (report_name not in feasible_candidate_reports):
            feasible_candidate_reports.append(report_name)
        if len(top_candidates) < 6:
            top_candidates.append(
                {
                    "report_name": report_name,
                    "score": candidate.get("score"),
                    "hard_blockers": hard_blockers,
                    "missing_required_filter_values": [
                        str(x).strip() for x in list(candidate.get("missing_required_filter_values") or []) if str(x).strip()
                    ],
                    "reasons": [str(x) for x in list(candidate.get("reasons") or []) if str(x).strip()][:6],
                }
            )

    if feasible_candidate_reports:
        candidate_reports = list(feasible_candidate_reports)
    if selected_report and selected_report not in candidate_reports:
        candidate_reports.insert(0, selected_report)
    candidate_cursor = candidate_reports.index(selected_report) if (selected_report and selected_report in candidate_reports) else 0

    return {
        "candidate_reports": candidate_reports,
        "candidate_scores": candidate_scores,
        "candidate_cursor": candidate_cursor,
        "top_candidates": top_candidates,
    }


def resolver_selected_step_trace(
    *,
    resolved: Dict[str, Any],
    selected_report: str,
    top_candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "step": 0,
        "action": "resolver_selected",
        "requested_metric": str((resolved.get("hard_constraints") or {}).get("metric") or ""),
        "requested_dimensions": list((resolved.get("hard_constraints") or {}).get("requested_dimensions") or []),
        "selected_report": str(selected_report or ""),
        "top_candidates": top_candidates,
    }


def extract_auto_switch_pending(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    out = payload if isinstance(payload, dict) else {}
    pending = out.get("_pending_state") if isinstance(out.get("_pending_state"), dict) else None
    if not isinstance(pending, dict):
        return None
    if str(pending.get("mode") or "").strip() != "planner_clarify":
        return None
    quality_clarification = pending.get("quality_clarification") if isinstance(pending.get("quality_clarification"), dict) else {}
    if str(quality_clarification.get("intent") or "").strip() != "switch_report":
        return None
    try:
        switch_attempt = int(quality_clarification.get("switch_attempt") or 0)
    except Exception:
        switch_attempt = 0
    if switch_attempt >= 1:
        return None
    return pending
