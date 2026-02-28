from __future__ import annotations

from typing import Any, Dict

from ai_assistant_ui.ai_core.v7.contract_registry import default_clarification_question


def compile_execution_plan(*, resolved: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase-2 compiler:
    turn semantic resolver output into strict execution intent.
    """
    obj = resolved if isinstance(resolved, dict) else {}
    spec = obj.get("business_spec") if isinstance(obj.get("business_spec"), dict) else {}
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    hard_constraints = obj.get("hard_constraints") if isinstance(obj.get("hard_constraints"), dict) else {}
    selected = str(obj.get("selected_report") or "").strip()
    needs_clar = bool(obj.get("needs_clarification"))
    clar_q = str(obj.get("clarification_question") or "").strip()
    reason = str(obj.get("clarification_reason") or "").strip()
    selected_score = obj.get("selected_score")

    if needs_clar or not selected:
        default_q = default_clarification_question(reason or "no_candidate")
        return {
            "action": "clarify",
            "report_name": selected,
            "filters_so_far": dict(filters),
            "task_class": str(hard_constraints.get("task_class") or spec.get("task_class") or "analytical_read"),
            "ask": {"question": clar_q or default_q},
            "needs_clarification": True,
            "_phase": "phase2_plan_compiler",
            "_clarification_reason": reason or "no_candidate",
            "_selected_score": selected_score,
        }

    return {
        "action": "run_report",
        "report_name": selected,
        "filters": dict(filters),
        "task_class": str(hard_constraints.get("task_class") or spec.get("task_class") or "analytical_read"),
        "requested_limit": int(hard_constraints.get("requested_limit") or 0),
        "sort_intent": str(hard_constraints.get("sort_intent") or "").strip().lower(),
        "needs_clarification": False,
        "_phase": "phase2_plan_compiler",
        "_selected_score": selected_score,
        "_candidate_count": len(list(obj.get("candidate_reports") or [])),
    }
