from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ai_assistant_ui.ai_core.v7.capability_registry import report_semantics_contract


def quality_has_repairable_failure_class(quality: Dict[str, Any], classes: List[str]) -> bool:
    q = quality if isinstance(quality, dict) else {}
    wanted = {str(x or "").strip().lower() for x in list(classes or []) if str(x or "").strip()}
    if not wanted:
        return False
    repairable_classes = {
        str(x or "").strip().lower()
        for x in list(q.get("repairable_failure_classes") or [])
        if str(x or "").strip()
    }
    if repairable_classes:
        return bool(repairable_classes & wanted)

    failed_ids = [str(x or "") for x in list(q.get("failed_check_ids") or [])]
    return any(
        x.endswith("_non_empty_rows")
        or x.endswith("_kpi_payload_shape")
        or x.endswith("_trend_has_time_axis")
        or x.endswith("_minimal_columns_present")
        or x.endswith("_requested_dimensions_present")
        or x.endswith("_document_filter_applied")
        or x.endswith("_actual_sales_not_opportunity_metric")
        or x.endswith("_output_mode_payload_alignment")
        for x in failed_ids
    )


def should_switch_candidate_on_repairable(
    *,
    quality: Dict[str, Any],
    intent: str,
    task_class: str,
    candidate_cursor: int,
    candidate_reports: List[str],
    candidate_switch_attempts: int,
) -> bool:
    if str(quality.get("verdict") or "").strip() != "REPAIRABLE_FAIL":
        return False
    if str(intent or "").strip().upper() == "TRANSFORM_LAST":
        return False
    if candidate_cursor + 1 >= len(list(candidate_reports or [])):
        return False
    if int(candidate_switch_attempts) >= 4:
        return False
    switch_classes = ["shape", "data", "constraint", "semantic"]
    if str(task_class or "").strip().lower() == "list_latest_records":
        switch_classes = ["shape", "data", "constraint"]
    return quality_has_repairable_failure_class(quality, classes=switch_classes)


def looks_like_system_error_text(payload: Dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    typ = str(payload.get("type") or "").strip().lower()
    if typ not in {"text", "error"}:
        return False
    txt = str(payload.get("text") or payload.get("message") or "").strip().lower()
    if not txt:
        return False
    patterns = (
        "is mandatory",
        "not found",
        "must be greater than",
        "must be less than",
        "traceback",
        "exception",
        "error:",
        "sql",
    )
    return any(p in txt for p in patterns)


def unsupported_message_from_spec(spec: Dict[str, Any]) -> str:
    subject = str(spec.get("subject") or "").strip()
    metric = str(spec.get("metric") or "").strip()
    if subject or metric:
        return (
            "I couldn't reliably produce that result with current report coverage. "
            f"Requested scope: subject='{subject or 'unspecified'}', metric='{metric or 'unspecified'}'. "
            "Please refine the target report/filters and retry."
        )
    return (
        "I couldn't reliably produce that result with current report coverage. "
        "Please refine the request (target report/filters), and I'll retry."
    )


def is_low_signal_read_spec(spec: Dict[str, Any]) -> bool:
    s = spec if isinstance(spec, dict) else {}
    intent = str(s.get("intent") or "").strip().upper()
    if intent and intent != "READ":
        return False
    if str(s.get("task_class") or "").strip().lower() == "transform_followup":
        return False
    if isinstance(s.get("filters"), dict) and bool(s.get("filters")):
        return False
    if list(s.get("group_by") or []) or list(s.get("dimensions") or []):
        return False
    try:
        if int(s.get("top_n") or 0) > 0:
            return False
    except Exception:
        pass
    ts = s.get("time_scope") if isinstance(s.get("time_scope"), dict) else {}
    if str(ts.get("mode") or "none").strip().lower() not in {"", "none"}:
        return False
    metric = str(s.get("metric") or "").strip()
    if metric:
        return False
    output_contract = s.get("output_contract") if isinstance(s.get("output_contract"), dict) else {}
    if list(output_contract.get("minimal_columns") or []):
        return False
    subject = str(s.get("subject") or "").strip().lower()
    if not subject:
        return True
    tokens = re.findall(r"[a-z0-9]+", subject)
    if not tokens:
        return True
    generic = {"report", "reports", "data", "result", "results", "detail", "details", "information", "show", "view"}
    non_generic = [t for t in tokens if t not in generic]
    return len(non_generic) == 0


def has_explicit_time_scope(spec: Dict[str, Any]) -> bool:
    ts = spec.get("time_scope") if isinstance(spec.get("time_scope"), dict) else {}
    mode = str(ts.get("mode") or "none").strip().lower()
    value = str(ts.get("value") or "").strip()
    return bool((mode not in {"", "none"}) or value)


def requested_minimal_columns(spec: Dict[str, Any]) -> List[str]:
    output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    return [str(x).strip() for x in list(output_contract.get("minimal_columns") or []) if str(x or "").strip()]


def normalized_message_text(message: str) -> str:
    return " ".join(str(message or "").strip().lower().replace("_", " ").split())


def humanize_fieldname(fieldname: str) -> str:
    return " ".join(str(fieldname or "").strip().lower().replace("_", " ").split())


def metadata_requested_columns(
    *,
    message: str,
    selected_report: str,
    last_result_payload: Optional[Dict[str, Any]],
) -> List[str]:
    msg = normalized_message_text(message)
    if not msg or not str(selected_report or "").strip():
        return []

    candidates: List[str] = []
    contract = report_semantics_contract(selected_report)
    presentation = contract.get("presentation") if isinstance(contract.get("presentation"), dict) else {}
    column_roles = presentation.get("column_roles") if isinstance(presentation.get("column_roles"), dict) else {}
    for role_group in ("dimensions", "metrics"):
        role_map = column_roles.get(role_group) if isinstance(column_roles.get(role_group), dict) else {}
        for canonical_name in list(role_map.keys()):
            s = humanize_fieldname(str(canonical_name or ""))
            if s:
                candidates.append(s)
    for raw in list(presentation.get("transform_safe_columns") or []):
        s = humanize_fieldname(str(raw or ""))
        if s:
            candidates.append(s)

    if isinstance(last_result_payload, dict) and str(last_result_payload.get("report_name") or "").strip().lower() == str(selected_report or "").strip().lower():
        for col in list(last_result_payload.get("_source_columns") or []):
            if not isinstance(col, dict):
                continue
            for raw in (col.get("label"), col.get("fieldname")):
                s = humanize_fieldname(str(raw or ""))
                if s:
                    candidates.append(s)

    out: List[str] = []
    seen = set()
    for cand in sorted(candidates, key=len, reverse=True):
        if len(cand) < 4:
            continue
        if cand not in msg:
            continue
        cand_tokens = set(cand.split())
        if any(cand == existing or cand_tokens < set(existing.split()) for existing in out):
            continue
        if cand in seen:
            continue
        seen.add(cand)
        out.append(cand)
    return out


def enrich_minimal_columns_from_report_metadata(
    *,
    spec_obj: Dict[str, Any],
    message: str,
    selected_report: str,
    last_result_payload: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    spec = dict(spec_obj or {})
    requested = metadata_requested_columns(
        message=message,
        selected_report=selected_report,
        last_result_payload=last_result_payload,
    )
    if not requested:
        return spec

    output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    current = [str(x).strip() for x in list(output_contract.get("minimal_columns") or []) if str(x or "").strip()]
    base_semantics = {
        humanize_fieldname(x)
        for x in (list(spec.get("group_by") or []) + ([spec.get("metric")] if str(spec.get("metric") or "").strip() else []))
        if str(x or "").strip()
    }
    merged: List[str] = []
    seen = set()
    for raw in current + requested:
        s = str(raw or "").strip()
        key = humanize_fieldname(s)
        if (not s) or (not key) or (key in seen):
            continue
        seen.add(key)
        merged.append(s)

    explicit_extra = any(humanize_fieldname(x) not in base_semantics for x in merged)
    if not explicit_extra:
        return spec

    spec["output_contract"] = dict(output_contract)
    spec["output_contract"]["minimal_columns"] = merged[:12]
    return spec


def is_projection_followup_request(spec: Dict[str, Any]) -> bool:
    s = spec if isinstance(spec, dict) else {}
    if requested_minimal_columns(s):
        return True
    task_class = str(s.get("task_class") or "").strip().lower()
    output_mode = str(((s.get("output_contract") or {}).get("mode") or "")).strip().lower()
    return bool(task_class == "detail_projection" and output_mode == "detail")


def has_report_table_rows(payload: Optional[Dict[str, Any]]) -> bool:
    p = payload if isinstance(payload, dict) else {}
    if str(p.get("type") or "").strip().lower() != "report_table":
        return False
    table = p.get("table") if isinstance(p.get("table"), dict) else {}
    rows = table.get("rows") if isinstance(table.get("rows"), list) else []
    cols = table.get("columns") if isinstance(table.get("columns"), list) else []
    return bool(rows and cols)


def sanitize_user_payload(*, payload: Dict[str, Any], business_spec: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload or {})
    typ = str(out.get("type") or "").strip().lower()
    if typ == "text":
        txt = str(out.get("text") or "").strip()
        if txt:
            lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
            if len(lines) > 1 and len(set(lines)) == 1:
                txt = lines[0]
            out["text"] = txt
        if looks_like_system_error_text({"type": "text", "text": out.get("text")}):
            out["text"] = unsupported_message_from_spec(business_spec)
            out.pop("_pending_state", None)
    elif typ == "error":
        out = {"type": "text", "text": unsupported_message_from_spec(business_spec)}
    return out
