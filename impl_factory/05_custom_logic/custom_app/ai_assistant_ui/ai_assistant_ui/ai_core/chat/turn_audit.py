from __future__ import annotations

import datetime as dt
from threading import local
from typing import Any, Dict, Optional

_CTX = local()

_PLAN_KEYS = (
    "action",
    "report_name",
    "filters",
    "export",
    "needs_clarification",
    "ask",
    "filters_so_far",
    "operation",
    "params",
    "doctype",
    "payload",
    "confirmation_text",
    "post_transform",
    "llm_meta",
)
_SPEC_KEYS = (
    "intent",
    "task_type",
    "subject",
    "metric",
    "aggregation",
    "group_by",
    "time_scope",
    "filters",
    "top_n",
    "output_contract",
    "ambiguities",
    "needs_clarification",
    "clarification_question",
    "llm_meta",
)
_QUALITY_KEYS = (
    "verdict",
    "failed_checks",
    "context",
    "attempt_count",
    "decision_path",
)


def _is_date_like(x: Any) -> bool:
    try:
        return isinstance(x, (dt.date, dt.datetime))
    except Exception:
        return False


def _json_safe(obj: Any) -> Any:
    try:
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if _is_date_like(obj):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {str(k): _json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [_json_safe(v) for v in obj]
        return str(obj)
    except Exception:
        return str(obj)


def _prune_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in _PLAN_KEYS:
        if k in plan:
            out[k] = plan.get(k)
    return _json_safe(out)


def _prune_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in _SPEC_KEYS:
        if k in spec:
            out[k] = spec.get(k)
    return _json_safe(out)


def _prune_quality(gate: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in _QUALITY_KEYS:
        if k in gate:
            out[k] = gate.get(k)
    return _json_safe(out)


def _get_ctx() -> Dict[str, Any]:
    cur = getattr(_CTX, "planner_output", None)
    return cur if isinstance(cur, dict) else {}


def _set_ctx(ctx: Dict[str, Any]) -> None:
    _CTX.planner_output = _json_safe(ctx if isinstance(ctx, dict) else {})


def set_last_planner_output(plan: Dict[str, Any], *, source: str = "report_qa_start") -> None:
    try:
        if isinstance(plan, dict):
            pruned = _prune_plan(plan)
            ctx = _get_ctx()
            hist = ctx.get("plan_history") if isinstance(ctx.get("plan_history"), list) else []
            hist.append({"source": str(source), "plan": pruned})
            ctx["source"] = str(source)
            ctx["plan"] = pruned
            ctx["plan_history"] = hist[-5:]
            _set_ctx(ctx)
    except Exception:
        _set_ctx({"source": str(source), "plan": {"action": "unknown"}})


def set_last_business_request_spec(spec: Dict[str, Any], *, source: str = "report_qa_start") -> None:
    try:
        if isinstance(spec, dict):
            ctx = _get_ctx()
            ctx["business_request_spec"] = {"source": str(source), "spec": _prune_spec(spec)}
            _set_ctx(ctx)
    except Exception:
        pass


def set_last_result_quality_gate(gate: Dict[str, Any], *, source: str = "report_qa_start") -> None:
    try:
        if isinstance(gate, dict):
            ctx = _get_ctx()
            ctx["result_quality_gate"] = {"source": str(source), "gate": _prune_quality(gate)}
            _set_ctx(ctx)
    except Exception:
        pass


def pop_last_planner_output() -> Optional[Dict[str, Any]]:
    out = getattr(_CTX, "planner_output", None)
    if hasattr(_CTX, "planner_output"):
        delattr(_CTX, "planner_output")
    return out if isinstance(out, dict) else None


def clear_last_planner_output() -> None:
    if hasattr(_CTX, "planner_output"):
        delattr(_CTX, "planner_output")
