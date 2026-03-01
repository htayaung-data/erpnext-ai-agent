from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover - allows local unit tests without Frappe runtime
    frappe = None

from ai_assistant_ui.ai_core.llm.report_planner import choose_business_request_spec
from ai_assistant_ui.ai_core.ontology_normalization import canonical_dimension, canonical_metric
from ai_assistant_ui.ai_core.util_dates import extract_timeframe, last_month_range, last_week_range, this_month_range, this_week_range, today_date
from ai_assistant_ui.ai_core.v7.spec_schema import default_business_request_spec, normalize_business_request_spec


def _build_time_context(ref_date) -> Dict[str, Dict[str, str]]:
    return {
        "last_month": {"from": last_month_range(ref_date).start_str, "to": last_month_range(ref_date).end_str},
        "this_month": {"from": this_month_range(ref_date).start_str, "to": this_month_range(ref_date).end_str},
        "last_week": {"from": last_week_range(ref_date).start_str, "to": last_week_range(ref_date).end_str},
        "this_week": {"from": this_week_range(ref_date).start_str, "to": this_week_range(ref_date).end_str},
    }


def _safe_parse_json_dict(raw: Any) -> Dict[str, Any]:
    s = str(raw or "").strip()
    if not (s.startswith("{") and s.endswith("}")):
        return {}
    try:
        obj = json.loads(s)
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _assistant_context_text(raw: str) -> str:
    obj = _safe_parse_json_dict(raw)
    if not obj:
        return str(raw or "").strip()[:1200]
    typ = str(obj.get("type") or "").strip().lower()
    if typ == "text":
        return str(obj.get("text") or "").strip()[:1200]
    if typ == "report_table":
        title = str(obj.get("title") or obj.get("report_name") or "Report").strip()
        table = obj.get("table") if isinstance(obj.get("table"), dict) else {}
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        cols = table.get("columns") if isinstance(table.get("columns"), list) else []
        labels: List[str] = []
        for c in cols[:8]:
            if not isinstance(c, dict):
                continue
            lb = str(c.get("label") or c.get("fieldname") or "").strip()
            if lb:
                labels.append(lb)
        return f"Shown report: {title}. Rows={len(rows)}. Columns={labels}"[:1200]
    return str(raw or "").strip()[:1200]


def _recent_user_assistant(session_doc, limit: int = 5) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    msgs = session_doc.get("messages") or []
    for m in reversed(msgs):
        role = str(m.role or "").strip().lower()
        if role not in ("user", "assistant"):
            continue
        content = str(m.content or "").strip()
        if not content:
            continue
        if role == "assistant":
            content = _assistant_context_text(content)
        out.append({"role": role, "content": content[:1200]})
        if len(out) >= max(2, int(limit) * 2):
            break
    return list(reversed(out))


def _last_result_meta(session_doc) -> Optional[Dict[str, Any]]:
    msgs = session_doc.get("messages") or []
    active_report_name = ""
    active_source_columns: List[Dict[str, Any]] = []
    for m in reversed(msgs):
        if str(m.role or "").strip().lower() != "tool":
            continue
        obj = _safe_parse_json_dict(m.content)
        if obj.get("type") != "v7_topic_state":
            continue
        state = obj.get("state") if isinstance(obj.get("state"), dict) else {}
        active_result = state.get("active_result") if isinstance(state.get("active_result"), dict) else {}
        active_report_name = str(active_result.get("report_name") or "").strip()
        for c in list(active_result.get("source_columns") or []):
            if not isinstance(c, dict):
                continue
            active_source_columns.append(
                {
                    "fieldname": c.get("fieldname"),
                    "label": c.get("label"),
                    "fieldtype": c.get("fieldtype"),
                }
            )
        break

    if active_report_name:
        for m in reversed(msgs):
            if str(m.role or "").strip().lower() != "assistant":
                continue
            obj = _safe_parse_json_dict(m.content)
            if str(obj.get("type") or "").strip().lower() != "report_table":
                continue
            report_name = str(obj.get("report_name") or "").strip()
            if report_name.lower() != active_report_name.lower():
                continue
            table = obj.get("table") if isinstance(obj.get("table"), dict) else {}
            cols = table.get("columns") if isinstance(table.get("columns"), list) else []
            out_cols = [
                {
                    "fieldname": c.get("fieldname"),
                    "label": c.get("label"),
                    "fieldtype": c.get("fieldtype"),
                }
                for c in cols
                if isinstance(c, dict)
            ]
            if active_source_columns:
                out_cols = active_source_columns
            return {
                "report_name": report_name,
                "columns": out_cols,
            }

    for m in reversed(msgs):
        if str(m.role or "").strip().lower() != "tool":
            continue
        obj = _safe_parse_json_dict(m.content)
        if obj.get("type") not in ("last_result",):
            continue
        table = obj.get("table") if isinstance(obj.get("table"), dict) else {}
        cols = table.get("columns") if isinstance(table.get("columns"), list) else []
        return {
            "report_name": obj.get("report_name"),
            "columns": [
                {
                    "fieldname": c.get("fieldname"),
                    "label": c.get("label"),
                    "fieldtype": c.get("fieldtype"),
                }
                for c in cols
                if isinstance(c, dict)
            ],
        }
    return None


def _load_session_context(session_name: Optional[str]) -> Dict[str, Any]:
    if (not session_name) or (frappe is None):
        return {"recent_messages": [], "last_result_meta": None, "has_last_result": False}
    try:
        session_doc = frappe.get_doc("AI Chat Session", session_name)
    except Exception:
        return {"recent_messages": [], "last_result_meta": None, "has_last_result": False}
    last_meta = _last_result_meta(session_doc)
    return {
        "recent_messages": _recent_user_assistant(session_doc, limit=5),
        "last_result_meta": last_meta,
        "has_last_result": bool(last_meta),
    }


def _normalize_minimal_columns(spec: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(spec or {})
    oc = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
    cols = []
    seen = set()
    for x in list(oc.get("minimal_columns") or []):
        s = str(x or "").strip()
        if not s:
            continue
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        cols.append(s)
    out["output_contract"] = dict(oc)
    out["output_contract"]["minimal_columns"] = cols[:12]
    return out


def _message_has_explicit_time_scope(message: str) -> bool:
    text = str(message or "").strip()
    if not text:
        return False
    as_of_date, date_range = extract_timeframe(text, ref=today_date())
    if as_of_date or date_range:
        return True
    lowered = text.lower()
    if re.search(r"\b(?:fiscal year|fy|quarter|q[1-4]|\d{4})\b", lowered):
        return True
    return False


def _message_has_explicit_top_n(message: str) -> bool:
    text = str(message or "").strip().lower()
    if not text:
        return False
    return bool(re.search(r"\b(?:top|latest|lowest|bottom)\s+\d+\b", text))


def _should_suppress_last_result_meta_for_message(message: str) -> bool:
    text = str(message or "").strip()
    if not text:
        return False
    explicit_metric = bool(str(canonical_metric(text) or "").strip())
    explicit_dimension = bool(str(canonical_dimension(text) or "").strip())
    explicit_top_n = _message_has_explicit_top_n(text)
    explicit_time_scope = _message_has_explicit_time_scope(text)
    strong_axes = int(explicit_metric) + int(explicit_dimension) + int(explicit_top_n) + int(explicit_time_scope)
    return strong_axes >= 2


def _suppress_unrequested_time_scope(spec: Dict[str, Any], *, message: str) -> Dict[str, Any]:
    out = dict(spec or {})
    ts = out.get("time_scope") if isinstance(out.get("time_scope"), dict) else {}
    mode = str(ts.get("mode") or "").strip().lower()
    if mode not in {"relative", "as_of", "range"}:
        return out
    if _message_has_explicit_time_scope(message):
        return out
    out["time_scope"] = {"mode": "none", "value": ""}
    return out


def _normalize_task_class_for_explicit_ranking(spec: Dict[str, Any], *, message: str) -> Dict[str, Any]:
    out = dict(spec or {})
    task_class = str(out.get("task_class") or "").strip().lower()
    if task_class != "list_latest_records":
        return out
    if str(out.get("intent") or "").strip().upper() != "READ":
        return out
    if str(out.get("task_type") or "").strip().lower() != "ranking":
        return out
    try:
        top_n = int(out.get("top_n") or 0)
    except Exception:
        top_n = 0
    metric = str(canonical_metric(out.get("metric") or message) or "").strip()
    requested_dims = [
        str(x).strip()
        for x in list(out.get("group_by") or []) + list(out.get("dimensions") or [])
        if str(x).strip()
    ]
    explicit_dimension = str(canonical_dimension(message) or "").strip()
    if top_n <= 0 or not metric:
        return out
    if not (requested_dims or explicit_dimension):
        return out
    out["task_class"] = "analytical_read"
    return out


def generate_business_request_spec(
    *,
    message: str,
    session_name: Optional[str],
    planner_plan: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    session_ctx = _load_session_context(session_name)
    suppress_last_result_meta = _should_suppress_last_result_meta_for_message(message)
    ref_date = today_date()
    today_iso = ref_date.isoformat()
    time_ctx = _build_time_context(ref_date)
    plan = planner_plan if isinstance(planner_plan, dict) else {}

    attempts: List[Dict[str, Any]] = []
    last_spec = default_business_request_spec()
    schema_errors: List[str] = []

    for outer_attempt in (1, 2):
        raw = choose_business_request_spec(
            user_message=str(message or ""),
            recent_messages=session_ctx.get("recent_messages") or [],
            planner_plan=plan,
            has_last_result=bool(session_ctx.get("has_last_result")) and (not suppress_last_result_meta),
            today_iso=today_iso,
            time_context=time_ctx,
            last_result_meta=None if suppress_last_result_meta else session_ctx.get("last_result_meta"),
        )
        normalized, errs = normalize_business_request_spec(raw)
        normalized = _normalize_minimal_columns(normalized)
        normalized = _normalize_task_class_for_explicit_ranking(normalized, message=message)
        normalized = _suppress_unrequested_time_scope(normalized, message=message)
        attempts.append(
            {
                "outer_attempt": outer_attempt,
                "schema_errors": list(errs),
                "llm_meta": (raw.get("llm_meta") if isinstance(raw, dict) else {}),
            }
        )
        last_spec = normalized
        schema_errors = list(errs)
        if not schema_errors:
            break

    meta = {
        "phase": "phase2_spec_pipeline",
        "schema_valid": len(schema_errors) == 0,
        "schema_errors": schema_errors,
        "outer_attempt_count": len(attempts),
        "attempts": attempts,
    }
    return {"spec": last_spec, "meta": meta}


def make_spec_tool_message(*, tool: str, mode: str, envelope: Dict[str, Any]) -> str:
    payload = {
        "type": "v7_business_request_spec",
        "phase": "phase2",
        "mode": str(mode or "").strip(),
        "tool": str(tool or "").strip(),
        "schema_valid": bool(((envelope.get("meta") or {}).get("schema_valid"))),
        "schema_errors": ((envelope.get("meta") or {}).get("schema_errors") or []),
        "outer_attempt_count": int(((envelope.get("meta") or {}).get("outer_attempt_count") or 0)),
        "spec": envelope.get("spec") if isinstance(envelope.get("spec"), dict) else default_business_request_spec(),
    }
    return json.dumps(payload, ensure_ascii=False, default=str)
