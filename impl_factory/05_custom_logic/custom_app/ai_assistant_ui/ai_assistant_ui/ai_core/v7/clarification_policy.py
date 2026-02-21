from __future__ import annotations

import json
from typing import Any, Dict

ALLOWED_BLOCKER_REASONS = {
    "missing_required_filter_value",
    "hard_constraint_not_supported",
    "entity_no_match",
    "entity_ambiguous",
    "no_candidate",
    "low_confidence_candidate",
    "resolver_pipeline_error",
}

_META_QUESTION_PHRASES = (
    "metric or grouping",
    "grouping or metric",
    "which metric",
    "which grouping",
)


def _sanitize_question(text: str, *, reason: str) -> str:
    q = str(text or "").strip()
    q_lc = q.lower()
    if (not q) or any(p in q_lc for p in _META_QUESTION_PHRASES):
        if reason == "missing_required_filter_value":
            return "Which required filter value should I use (for example company, warehouse, customer, or supplier)?"
        if reason == "hard_constraint_not_supported":
            return "I could not match all requested constraints in one report. Which constraint should I prioritize?"
        if reason == "entity_no_match":
            return "I couldn't find a matching value for that filter. Which exact value should I use?"
        if reason == "entity_ambiguous":
            return "I found multiple matches for that filter. Which one should I use?"
        return "Please provide one concrete missing detail so I can run the correct report."
    return q[:280]


def should_clarify(*, blocker: Dict[str, Any]) -> bool:
    """
    Backward-compatible boolean helper.
    """
    return bool((blocker or {}).get("should_clarify"))


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
    spec_needs = bool(spec.get("needs_clarification"))
    should = bool((resolver_needs or spec_needs) and (reason in ALLOWED_BLOCKER_REASONS or reason == ""))
    question_raw = str(res.get("clarification_question") or spec.get("clarification_question") or "").strip()
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
