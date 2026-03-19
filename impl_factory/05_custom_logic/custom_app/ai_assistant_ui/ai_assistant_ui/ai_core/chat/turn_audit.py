from __future__ import annotations

import datetime as dt
import json
from threading import local
from typing import Any, Dict, List, Optional

from ai_assistant_ui.ai_core.v7.capability_registry import registry_version as capability_registry_version

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


def _safe_json_obj(raw: Any) -> Dict[str, Any]:
    s = str(raw or "").strip()
    if not (s.startswith("{") and s.endswith("}")):
        return {}
    try:
        obj = json.loads(s)
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _tool_payloads(tool_messages: List[str]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for raw in list(tool_messages or []):
        obj = _safe_json_obj(raw)
        typ = str(obj.get("type") or "").strip()
        if typ:
            out[typ] = obj
    return out


def _planner_plan(planner_output: Dict[str, Any]) -> Dict[str, Any]:
    plan = planner_output.get("plan") if isinstance(planner_output.get("plan"), dict) else {}
    return plan if isinstance(plan, dict) else {}


def _planner_spec(planner_output: Dict[str, Any]) -> Dict[str, Any]:
    spec_wrap = planner_output.get("business_request_spec") if isinstance(planner_output.get("business_request_spec"), dict) else {}
    spec = spec_wrap.get("spec") if isinstance(spec_wrap.get("spec"), dict) else {}
    return spec if isinstance(spec, dict) else {}


def _planner_quality(planner_output: Dict[str, Any]) -> Dict[str, Any]:
    gate_wrap = planner_output.get("result_quality_gate") if isinstance(planner_output.get("result_quality_gate"), dict) else {}
    gate = gate_wrap.get("gate") if isinstance(gate_wrap.get("gate"), dict) else {}
    return gate if isinstance(gate, dict) else {}


def _write_context(
    *,
    spec: Dict[str, Any],
    pending_state_to_set: Optional[Dict[str, Any]],
    user_payload: Dict[str, Any],
) -> Dict[str, str]:
    pending = pending_state_to_set if isinstance(pending_state_to_set, dict) else {}
    wd = pending.get("write_draft") if isinstance(pending.get("write_draft"), dict) else {}
    if wd:
        return {
            "doctype": str(wd.get("doctype") or "").strip(),
            "operation": str(wd.get("operation") or "").strip().lower(),
        }

    wr = user_payload.get("_write_result") if isinstance(user_payload.get("_write_result"), dict) else {}
    payload = wr.get("payload") if isinstance(wr.get("payload"), dict) else {}
    doctype = str(wr.get("doctype") or spec.get("subject") or "").strip()
    operation = str(wr.get("operation") or "").strip().lower()
    if payload and (not doctype):
        doctype = str(payload.get("doctype") or "").strip()
    return {"doctype": doctype, "operation": operation}


def _security_outcome(
    *,
    spec: Dict[str, Any],
    tool_objs: Dict[str, Dict[str, Any]],
    user_payload: Dict[str, Any],
    pending_state_to_set: Optional[Dict[str, Any]],
    clear_pending: bool,
) -> Dict[str, Any]:
    intent = str(spec.get("intent") or "").strip().upper()
    pending = pending_state_to_set if isinstance(pending_state_to_set, dict) else {}
    pending_mode = str(pending.get("mode") or "").strip().lower()
    write_tool = tool_objs.get("v7_write_engine") if isinstance(tool_objs.get("v7_write_engine"), dict) else {}
    write_result = user_payload.get("_write_result") if isinstance(user_payload.get("_write_result"), dict) else {}
    text = str(user_payload.get("text") or "").strip().lower()
    ctx = _write_context(spec=spec, pending_state_to_set=pending, user_payload=user_payload)

    if (
        intent not in {"WRITE_DRAFT", "WRITE_CONFIRM"}
        and pending_mode != "write_confirmation"
        and not write_tool
        and not write_result
    ):
        return {
            "status": "not_applicable",
            "category": "read_only",
            "requires_confirmation": False,
        }

    base = {
        "category": "write_safety",
        "requires_confirmation": bool(pending_mode == "write_confirmation"),
        "doctype": str(ctx.get("doctype") or "").strip(),
        "operation": str(ctx.get("operation") or "").strip(),
    }

    if "disabled in this environment" in text:
        return dict(base, status="blocked_disabled", requires_confirmation=False)
    if pending_mode == "write_confirmation":
        return dict(base, status="confirmation_required", requires_confirmation=True)

    result_status = str(write_result.get("status") or "").strip().lower()
    if result_status == "duplicate_blocked":
        return dict(base, status="blocked_idempotency", requires_confirmation=False)
    if result_status == "error":
        return dict(base, status="execution_error", requires_confirmation=True)
    if result_status == "success":
        return dict(base, status="executed", requires_confirmation=False)

    decision = str(write_tool.get("decision") or "").strip().lower()
    if clear_pending and ("cancel" in decision or "canceled" in text or "cancelled" in text):
        return dict(base, status="canceled", requires_confirmation=False)
    if clear_pending and (text.startswith("confirmed.") or "executed" in text):
        return dict(base, status="executed", requires_confirmation=False)
    if "confirm or cancel" in text:
        return dict(base, status="confirmation_required", requires_confirmation=True)

    return dict(base, status="observed_unclassified", requires_confirmation=bool(pending_mode == "write_confirmation"))


def build_turn_audit_envelope(
    *,
    turn_id: str,
    planner_output: Optional[Dict[str, Any]],
    tool_messages: Optional[List[str]],
    error_envelope: Optional[Dict[str, Any]],
    latency_ms: int,
    final_response_hash: str,
    user_payload: Optional[Dict[str, Any]] = None,
    pending_state_to_set: Optional[Dict[str, Any]] = None,
    clear_pending: bool = False,
) -> Dict[str, Any]:
    planner = planner_output if isinstance(planner_output, dict) else {}
    payload = user_payload if isinstance(user_payload, dict) else {}
    tool_objs = _tool_payloads(tool_messages or [])
    plan = _planner_plan(planner)
    planner_spec = _planner_spec(planner)
    planner_quality = _planner_quality(planner)
    spec_tool = tool_objs.get("v7_business_request_spec") if isinstance(tool_objs.get("v7_business_request_spec"), dict) else {}
    quality_tool = tool_objs.get("v7_quality_gate") if isinstance(tool_objs.get("v7_quality_gate"), dict) else {}
    read_engine = tool_objs.get("v7_read_engine") if isinstance(tool_objs.get("v7_read_engine"), dict) else {}
    engine_route = tool_objs.get("engine_route") if isinstance(tool_objs.get("engine_route"), dict) else {}

    spec = spec_tool.get("spec") if isinstance(spec_tool.get("spec"), dict) else {}
    if not spec:
        spec = planner_spec
    quality = dict(planner_quality)
    if quality_tool:
        quality = {
            "verdict": str(quality_tool.get("verdict") or quality.get("verdict") or ""),
            "failed_check_ids": list(quality_tool.get("failed_check_ids") or []),
            "failed_failure_classes": list(quality_tool.get("failed_failure_classes") or []),
            "repairable_failure_classes": list(quality_tool.get("repairable_failure_classes") or []),
            "hard_failure_classes": list(quality_tool.get("hard_failure_classes") or []),
            "hard_fail_check_ids": list(quality_tool.get("hard_fail_check_ids") or []),
            "repairable_check_ids": list(quality_tool.get("repairable_check_ids") or []),
        }
    else:
        quality = {
            "verdict": str(quality.get("verdict") or ""),
            "failed_check_ids": [
                str((fc or {}).get("id") or "").strip()
                for fc in list(quality.get("failed_checks") or [])
                if isinstance(fc, dict) and str((fc or {}).get("id") or "").strip()
            ],
            "failed_failure_classes": [],
            "repairable_failure_classes": [],
            "hard_failure_classes": [],
            "hard_fail_check_ids": [],
            "repairable_check_ids": [],
        }

    plan_meta = plan.get("llm_meta") if isinstance(plan.get("llm_meta"), dict) else {}
    spec_meta = spec.get("llm_meta") if isinstance(spec.get("llm_meta"), dict) else {}
    err = error_envelope if isinstance(error_envelope, dict) else {}
    trace_id = str(err.get("trace_id") or turn_id).strip() or str(turn_id or "").strip()
    fallback_plan = bool(plan_meta.get("fallback_used"))
    fallback_spec = bool(spec_meta.get("fallback_used"))

    return _json_safe(
        {
            "schema_version": "turn_audit_envelope_v1",
            "trace_id": trace_id,
            "engine_version": str(engine_route.get("executed_engine") or "v7").strip(),
            "engine_mode": str(engine_route.get("effective_mode") or "").strip(),
            "model_version": {
                "plan": str(plan_meta.get("model_version") or "").strip(),
                "spec": str(spec_meta.get("model_version") or "").strip(),
            },
            "prompt_version": {
                "plan": str(plan_meta.get("prompt_version") or "").strip(),
                "spec": str(spec_meta.get("prompt_version") or "").strip(),
            },
            "capability_version": str(capability_registry_version() or "").strip(),
            "fallback_used": {
                "plan": fallback_plan,
                "spec": fallback_spec,
                "any": bool(fallback_plan or fallback_spec),
            },
            "security_outcome": _security_outcome(
                spec=spec,
                tool_objs=tool_objs,
                user_payload=payload,
                pending_state_to_set=pending_state_to_set,
                clear_pending=bool(clear_pending),
            ),
            "selected_candidate": {
                "report_name": str(read_engine.get("selected_report") or "").strip(),
                "score": read_engine.get("selected_score"),
            },
            "execution_plan": _prune_plan(plan),
            "validation_result": {
                "schema_valid": bool(spec_tool.get("schema_valid")) if spec_tool else None,
                "schema_errors": list(spec_tool.get("schema_errors") or []) if spec_tool else [],
                "quality_verdict": str(quality.get("verdict") or "").strip(),
                "failed_check_ids": list(quality.get("failed_check_ids") or []),
                "failed_failure_classes": list(quality.get("failed_failure_classes") or []),
                "repairable_failure_classes": list(quality.get("repairable_failure_classes") or []),
                "hard_failure_classes": list(quality.get("hard_failure_classes") or []),
                "error_code": str(err.get("code") or "").strip(),
            },
            "latency_ms": int(latency_ms or 0),
            "final_response_hash": str(final_response_hash or "").strip(),
        }
    )


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
