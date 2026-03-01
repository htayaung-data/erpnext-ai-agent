from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ai_assistant_ui.ai_core.llm.report_planner import choose_candidate_report
from ai_assistant_ui.ai_core.v7.constraint_engine import build_constraint_set
from ai_assistant_ui.ai_core.v7.db_semantic_catalog import retrieve_db_semantic_context
from ai_assistant_ui.ai_core.util_dates import last_month_range, last_week_range, this_month_range, this_week_range, today_date
from ai_assistant_ui.ai_core.v7.capability_platform import build_capability_platform_payload
from ai_assistant_ui.ai_core.v7.plan_compiler import compile_execution_plan
from ai_assistant_ui.ai_core.v7.semantic_resolver import resolve_semantics
from ai_assistant_ui.ai_core.v7.contract_registry import default_clarification_question


def _build_time_context(ref_date) -> Dict[str, Dict[str, str]]:
    return {
        "last_month": {"from": last_month_range(ref_date).start_str, "to": last_month_range(ref_date).end_str},
        "this_month": {"from": this_month_range(ref_date).start_str, "to": this_month_range(ref_date).end_str},
        "last_week": {"from": last_week_range(ref_date).start_str, "to": last_week_range(ref_date).end_str},
        "this_week": {"from": this_week_range(ref_date).start_str, "to": this_week_range(ref_date).end_str},
    }


def _requirements_by_report(index: Dict[str, Any], candidate_names: Dict[str, bool]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for row in list(index.get("reports") or []):
        if not isinstance(row, dict):
            continue
        name = str(row.get("report_name") or row.get("name") or "").strip()
        if not name or not candidate_names.get(name):
            continue
        constraints = row.get("constraints") if isinstance(row.get("constraints"), dict) else {}
        out[name] = {
            "required_filter_names": list(constraints.get("required_filter_names") or []),
            "filters_definition": list(constraints.get("filters_definition") or []),
        }
    return out


def _llm_rerank_selected_report(*, message: str, resolved: Dict[str, Any], index: Dict[str, Any]) -> str:
    if not str(message or "").strip():
        return ""
    selected_report = str(resolved.get("selected_report") or "").strip()
    candidate_rows = [c for c in list(resolved.get("candidate_reports") or []) if isinstance(c, dict)]
    if selected_report:
        for cand in candidate_rows:
            if str(cand.get("report_name") or "").strip() != selected_report:
                continue
            if (not list(cand.get("hard_blockers") or [])) and (not list(cand.get("missing_required_filter_values") or [])):
                # Deterministic resolver winner takes precedence whenever it is already feasible.
                return ""
            break
    feasible = [
        c
        for c in candidate_rows
        if (not list(c.get("hard_blockers") or []))
    ]
    if len(feasible) < 2:
        return ""

    feasible_names: Dict[str, bool] = {}
    score_by_name: Dict[str, float] = {}
    reports: List[Dict[str, Any]] = []
    by_name = index.get("reports_by_name") if isinstance(index.get("reports_by_name"), dict) else {}
    for cand in feasible[:40]:
        name = str(cand.get("report_name") or "").strip()
        if not name or feasible_names.get(name):
            continue
        feasible_names[name] = True
        try:
            score_by_name[name] = float(cand.get("score") or 0.0)
        except Exception:
            score_by_name[name] = 0.0
        row = by_name.get(name) if isinstance(by_name.get(name), dict) else {}
        reports.append(
            {
                "name": name,
                "module": row.get("report_family") or row.get("module"),
                "report_type": row.get("report_type"),
                "required_filter_names": list((row.get("constraints") or {}).get("required_filter_names") or []),
                "required_filter_kinds": list((row.get("constraints") or {}).get("required_filter_kinds") or []),
                "supported_filter_kinds": list((row.get("constraints") or {}).get("supported_filter_kinds") or []),
                "domain_hints": list((row.get("semantics") or {}).get("domain_hints") or []),
                "dimension_hints": list((row.get("semantics") or {}).get("dimension_hints") or []),
                "metric_hints": list((row.get("semantics") or {}).get("metric_hints") or []),
                "primary_dimension": str((row.get("semantics") or {}).get("primary_dimension") or ""),
            }
        )
    if len(reports) < 2:
        return ""

    try:
        llm_pick = choose_candidate_report(
            user_message=str(message or ""),
            business_spec=resolved.get("business_spec") if isinstance(resolved.get("business_spec"), dict) else {},
            candidate_reports=reports,
        )
    except Exception:
        return ""

    if not isinstance(llm_pick, dict):
        return ""
    chosen = str(llm_pick.get("selected_report") or "").strip()
    if chosen and feasible_names.get(chosen):
        # Keep model-assisted rerank bounded to near-top feasible candidates.
        # This prevents low-score drift away from deterministic semantic ranking.
        if score_by_name:
            best = max(score_by_name.values())
            chosen_score = score_by_name.get(chosen, -1e9)
            if chosen_score < (best - 2.0):
                return ""
        return chosen
    return ""


def resolve_business_request(
    *,
    business_spec: Dict[str, Any],
    message: str = "",
    user: Optional[str],
    topic_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    spec = business_spec if isinstance(business_spec, dict) else {}
    state = topic_state if isinstance(topic_state, dict) else {}
    try:
        platform_payload = build_capability_platform_payload(
            user=user,
            include_disabled=False,
            max_reports=260,
            previous_snapshot=None,
            freshness_hours=24,
            min_confidence=0.60,
        )
        index = platform_payload.get("index") if isinstance(platform_payload.get("index"), dict) else {}
        coverage = platform_payload.get("coverage") if isinstance(platform_payload.get("coverage"), dict) else {}
        drift = platform_payload.get("drift") if isinstance(platform_payload.get("drift"), dict) else {}
        alerts = [a for a in list(platform_payload.get("alerts") or []) if isinstance(a, dict)]
        constraint_set = build_constraint_set(
            business_spec=spec,
            topic_state=state,
        )
        semantic_context = retrieve_db_semantic_context(
            business_spec=spec,
            constraint_set=constraint_set,
            top_k=6,
        )
        resolved = resolve_semantics(
            business_spec=spec,
            capability_index=index,
            constraint_set=constraint_set,
            semantic_context=semantic_context,
        )
        # Do not allow unconstrained planner override at runtime. Any model-assisted
        # rerank is allowed only within resolver-feasible candidates.
        reranked_report = _llm_rerank_selected_report(message=message, resolved=resolved, index=index)
        reranked_by = "llm_candidate_ranker" if reranked_report else ""
        if reranked_report:
            resolved = dict(resolved)
            resolved["selected_report"] = reranked_report
            for c in list(resolved.get("candidate_reports") or []):
                if not isinstance(c, dict):
                    continue
                if str(c.get("report_name") or "").strip() == reranked_report:
                    resolved["selected_score"] = c.get("score")
                    break
            resolved["reranked_by"] = reranked_by
        plan = compile_execution_plan(resolved=resolved)
        meta = {
            "phase": "phase3_resolver_pipeline",
            "resolver_ok": True,
            "report_count": int(index.get("report_count") or 0),
            "reports_scanned": int(index.get("report_count") or 0),
            "selected_report": str(resolved.get("selected_report") or ""),
            "needs_clarification": bool(resolved.get("needs_clarification")),
            "coverage_family_rate": coverage.get("family_coverage_rate"),
            "coverage_report_rate": coverage.get("report_coverage_rate"),
            "drift_changed_count": drift.get("changed_count"),
            "alert_count": len(alerts),
            "reranked_by": str(resolved.get("reranked_by") or ""),
            "constraint_domain": str(constraint_set.get("domain") or ""),
            "constraint_task_class": str(constraint_set.get("task_class") or ""),
            "constraint_hard_filter_kinds_count": len(list(constraint_set.get("hard_filter_kinds") or [])),
            "constraint_requested_dimensions_count": len(list(constraint_set.get("requested_dimensions") or [])),
            "db_semantic_catalog_available": bool(semantic_context.get("catalog_available")),
            "db_semantic_selected_table_count": len(list(semantic_context.get("selected_tables") or [])),
            "db_semantic_join_path_count": len(list(semantic_context.get("join_paths") or [])),
        }
        return {
            "index_meta": {
                "report_count": int(index.get("report_count") or 0),
                "reports_scanned": int(index.get("report_count") or 0),
                "built_from": index.get("built_from") if isinstance(index.get("built_from"), dict) else {},
                "coverage": coverage,
                "drift": drift,
                "alerts": alerts,
            },
            "constraint_set": constraint_set,
            "semantic_context": semantic_context,
            "resolved": resolved,
            "plan": plan,
            "meta": meta,
        }
    except Exception as exc:
        fallback_constraint_set = build_constraint_set(business_spec=spec, topic_state=state)
        fallback_semantic_context = retrieve_db_semantic_context(
            business_spec=spec,
            constraint_set=fallback_constraint_set,
            top_k=6,
        )
        fallback_resolved = {
            "_phase": "phase3_semantic_resolver_fallback",
            "business_spec": spec,
            "hard_constraints": fallback_constraint_set,
            "semantic_context": fallback_semantic_context,
            "candidate_reports": [],
            "selected_report": "",
            "selected_score": None,
            "needs_clarification": True,
            "clarification_reason": "resolver_pipeline_error",
            "clarification_question": default_clarification_question("resolver_pipeline_error"),
        }
        fallback_plan = compile_execution_plan(resolved=fallback_resolved)
        return {
            "index_meta": {"report_count": 0, "built_from": {}},
            "constraint_set": fallback_constraint_set,
            "semantic_context": fallback_semantic_context,
            "resolved": fallback_resolved,
            "plan": fallback_plan,
            "meta": {
                "phase": "phase3_resolver_pipeline",
                "resolver_ok": False,
                "error": str(exc)[:200],
                "report_count": 0,
                "reports_scanned": 0,
                "selected_report": "",
                "needs_clarification": True,
            },
        }


def make_resolver_tool_message(*, tool: str, mode: str, envelope: Dict[str, Any]) -> str:
    resolved = envelope.get("resolved") if isinstance(envelope.get("resolved"), dict) else {}
    plan = envelope.get("plan") if isinstance(envelope.get("plan"), dict) else {}
    constraint_set = envelope.get("constraint_set") if isinstance(envelope.get("constraint_set"), dict) else {}
    semantic_context = envelope.get("semantic_context") if isinstance(envelope.get("semantic_context"), dict) else {}
    candidates = list(resolved.get("candidate_reports") or [])
    top_candidates = []
    for c in candidates[:3]:
        if not isinstance(c, dict):
            continue
        top_candidates.append(
            {
                "report_name": c.get("report_name"),
                "score": c.get("score"),
                "hard_blockers": c.get("hard_blockers") or [],
            }
        )

    payload = {
        "type": "v7_semantic_resolution",
        "phase": "phase3",
        "mode": str(mode or "").strip(),
        "tool": str(tool or "").strip(),
        "resolver_ok": bool(((envelope.get("meta") or {}).get("resolver_ok"))),
        "selected_report": resolved.get("selected_report") or "",
        "selected_score": resolved.get("selected_score"),
        "needs_clarification": bool(resolved.get("needs_clarification")),
        "clarification_reason": resolved.get("clarification_reason") or "",
        "plan_action": plan.get("action") or "",
        "constraint_domain": str(constraint_set.get("domain") or ""),
        "constraint_task_class": str(constraint_set.get("task_class") or ""),
        "constraint_hard_filter_kinds_count": len(list(constraint_set.get("hard_filter_kinds") or [])),
        "db_semantic_catalog_available": bool(semantic_context.get("catalog_available")),
        "db_semantic_selected_table_count": len(list(semantic_context.get("selected_tables") or [])),
        "top_candidates": top_candidates,
    }
    return json.dumps(payload, ensure_ascii=False, default=str)
