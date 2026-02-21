from __future__ import annotations

from typing import Any, Dict


def compile_execution_plan(*, resolved: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase-2 compiler:
    turn semantic resolver output into strict execution intent.
    """
    obj = resolved if isinstance(resolved, dict) else {}
    spec = obj.get("business_spec") if isinstance(obj.get("business_spec"), dict) else {}
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    selected = str(obj.get("selected_report") or "").strip()
    needs_clar = bool(obj.get("needs_clarification"))
    clar_q = str(obj.get("clarification_question") or "").strip()
    reason = str(obj.get("clarification_reason") or "").strip()
    selected_score = obj.get("selected_score")

    if needs_clar or not selected:
        return {
            "action": "clarify",
            "report_name": selected,
            "filters_so_far": dict(filters),
            "ask": {"question": clar_q or "Could you clarify the missing business detail so I can run the right report?"},
            "needs_clarification": True,
            "_phase": "phase2_plan_compiler",
            "_clarification_reason": reason or "no_candidate",
            "_selected_score": selected_score,
        }

    return {
        "action": "run_report",
        "report_name": selected,
        "filters": dict(filters),
        "needs_clarification": False,
        "_phase": "phase2_plan_compiler",
        "_selected_score": selected_score,
        "_candidate_count": len(list(obj.get("candidate_reports") or [])),
    }
