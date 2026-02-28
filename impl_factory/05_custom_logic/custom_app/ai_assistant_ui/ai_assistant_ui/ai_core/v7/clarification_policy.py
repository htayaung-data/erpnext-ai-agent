from __future__ import annotations

import json
from typing import Any, Dict

from ai_assistant_ui.ai_core.v7.contract_registry import (
    allowed_blocker_reasons,
    default_clarification_question,
)

ALLOWED_BLOCKER_REASONS = allowed_blocker_reasons()
_SOFT_EXECUTION_BLOCKERS = {
    "unsupported_metric",
    "metric_domain_mismatch",
    "primary_dimension_mismatch",
    "unsupported_dimension",
}


def _sanitize_question(text: str, *, reason: str) -> str:
    reason_lc = str(reason or "").strip().lower()
    q = str(text or "").strip()
    if not q:
        return default_clarification_question(reason_lc)
    # For resolver-level blocker reasons, enforce contract question templates.
    # Entity reasons can still carry contextual dynamic prompts/options.
    if reason_lc in {
        "missing_required_filter_value",
        "hard_constraint_not_supported",
        "resolver_pipeline_error",
    }:
        return default_clarification_question(reason_lc)
    return q[:280]


def should_clarify(*, blocker: Dict[str, Any]) -> bool:
    """
    Backward-compatible boolean helper.
    """
    return bool((blocker or {}).get("should_clarify"))


def _selected_candidate(resolved: Dict[str, Any]) -> Dict[str, Any]:
    res = resolved if isinstance(resolved, dict) else {}
    selected = str(res.get("selected_report") or "").strip()
    if not selected:
        return {}
    for c in list(res.get("candidate_reports") or []):
        if not isinstance(c, dict):
            continue
        if str(c.get("report_name") or "").strip() == selected:
            return c
    return {}


def _can_execute_despite_semantic_blockers(resolved: Dict[str, Any]) -> bool:
    cand = _selected_candidate(resolved)
    if not cand:
        return False
    missing_required = [str(x).strip() for x in list(cand.get("missing_required_filter_values") or []) if str(x).strip()]
    if missing_required:
        return False
    blockers = [str(x).strip().lower() for x in list(cand.get("hard_blockers") or []) if str(x).strip()]
    if not blockers:
        return False
    return all(b in _SOFT_EXECUTION_BLOCKERS for b in blockers)


def _should_clarify_record_type(spec: Dict[str, Any], resolved: Dict[str, Any]) -> bool:
    s = spec if isinstance(spec, dict) else {}
    r = resolved if isinstance(resolved, dict) else {}
    task_class = str(s.get("task_class") or "").strip().lower()
    hc = r.get("hard_constraints") if isinstance(r.get("hard_constraints"), dict) else {}
    domain = (
        str(hc.get("domain") or "").strip().lower()
        if "domain" in hc
        else str(s.get("domain") or "").strip().lower()
    )
    metric = (
        str(hc.get("metric") or "").strip().lower()
        if "metric" in hc
        else str(s.get("metric") or "").strip().lower()
    )
    dims = (
        list(hc.get("requested_dimensions") or [])
        if "requested_dimensions" in hc
        else list(s.get("dimensions") or [])
    )
    unknown_scope = (domain in {"", "unknown"}) and (not metric) and (len([d for d in dims if str(d).strip()]) == 0)
    if not unknown_scope:
        return False
    if task_class == "list_latest_records":
        return True
    if task_class == "detail_projection":
        oc = s.get("output_contract") if isinstance(s.get("output_contract"), dict) else {}
        minimal = [str(x).strip().lower() for x in list(oc.get("minimal_columns") or []) if str(x).strip()]
        id_like = any(("number" in m) or ("id" in m) for m in minimal)
        return id_like
    return False


def evaluate_clarification(
    *,
    business_spec: Dict[str, Any],
    resolved: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Phase-5 blocker-only clarification policy.
    """
    spec = business_spec if isinstance(business_spec, dict) else {}
    res = resolved if isinstance(resolved, dict) else {}

    reason = str(res.get("clarification_reason") or "").strip().lower()
    resolver_needs = bool(res.get("needs_clarification"))
    # Contract: blocker-only clarification is emitted by resolver reason codes.
    # Spec-level LLM ambiguity hints are non-authoritative and must not drive runtime clarification loops.
    should = bool(resolver_needs and (reason in ALLOWED_BLOCKER_REASONS))
    if should and reason == "hard_constraint_not_supported" and _can_execute_despite_semantic_blockers(res):
        should = False
        reason = ""
    question_raw = str(res.get("clarification_question") or spec.get("clarification_question") or "").strip()
    if (not should) and _should_clarify_record_type(spec, res):
        should = True
        reason = "no_candidate"
        question_raw = "Which record type should I list (for example Sales Invoice, Purchase Invoice, Sales Order)?"
    question = _sanitize_question(question_raw, reason=reason)

    return {
        "should_clarify": should,
        "reason": reason or ("needs_clarification" if should else ""),
        "question": question if should else "",
        "policy_version": "phase5_blocker_only_v1",
    }


def make_clarification_tool_message(*, tool: str, mode: str, decision: Dict[str, Any]) -> str:
    obj = decision if isinstance(decision, dict) else {}
    return json.dumps(
        {
            "type": "v7_clarification_policy",
            "phase": "phase5",
            "mode": str(mode or "").strip(),
            "tool": str(tool or "").strip(),
            "should_clarify": bool(obj.get("should_clarify")),
            "reason": str(obj.get("reason") or ""),
        },
        ensure_ascii=False,
        default=str,
    )
