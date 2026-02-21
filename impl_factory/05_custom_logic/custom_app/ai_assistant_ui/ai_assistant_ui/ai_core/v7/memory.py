from __future__ import annotations

import copy
import json
import re
from typing import Any, Dict, List, Optional, Set

try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover - local tests without Frappe
    frappe = None

_DOC_ID_REGEX = re.compile(r"\b[A-Z]{2,}-[A-Z0-9]+-\d{4}-\d+\b")
_DOC_FILTER_KEYS = (
    "invoice",
    "sales_invoice",
    "purchase_invoice",
    "voucher_no",
    "document_id",
    "reference_name",
    "name",
)


def _safe_json_obj(raw: Any) -> Dict[str, Any]:
    s = str(raw or "").strip()
    if not (s.startswith("{") and s.endswith("}")):
        return {}
    try:
        obj = json.loads(s)
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _clone_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return copy.deepcopy(spec)
    except Exception:
        return dict(spec or {})


def _ensure_spec_shape(spec: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(spec or {})
    out["subject"] = str(out.get("subject") or "").strip()
    out["metric"] = str(out.get("metric") or "").strip()
    out["task_type"] = str(out.get("task_type") or "detail").strip().lower() or "detail"
    out["aggregation"] = str(out.get("aggregation") or "none").strip().lower() or "none"
    out["group_by"] = [str(x).strip() for x in list(out.get("group_by") or []) if str(x).strip()][:10]
    try:
        out["top_n"] = max(0, int(out.get("top_n") or 0))
    except Exception:
        out["top_n"] = 0

    filters = out.get("filters") if isinstance(out.get("filters"), dict) else {}
    out["filters"] = dict(filters)

    ts = out.get("time_scope") if isinstance(out.get("time_scope"), dict) else {}
    out["time_scope"] = {
        "mode": str(ts.get("mode") or "none").strip().lower() or "none",
        "value": str(ts.get("value") or "").strip(),
    }

    oc = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
    cols = [str(x).strip() for x in list(oc.get("minimal_columns") or []) if str(x).strip()][:12]
    out["output_contract"] = {
        "mode": str(oc.get("mode") or "detail").strip().lower() or "detail",
        "minimal_columns": cols,
    }
    return out


def _tokenize(text: str) -> Set[str]:
    words = re.findall(r"[a-z0-9_]+", str(text or "").strip().lower())
    return {w for w in words if len(w) >= 3}


def _topic_signature_from_spec(spec: Dict[str, Any]) -> Set[str]:
    bits: List[str] = [
        str(spec.get("subject") or ""),
        str(spec.get("metric") or ""),
        str(spec.get("task_type") or ""),
        str(spec.get("aggregation") or ""),
        " ".join([str(x) for x in list(spec.get("group_by") or [])]),
        " ".join([str(k) for k in list((spec.get("filters") or {}).keys())]),
    ]
    ts = spec.get("time_scope") if isinstance(spec.get("time_scope"), dict) else {}
    bits.append(str(ts.get("mode") or ""))
    bits.append(str(ts.get("value") or ""))
    return _tokenize(" ".join([x for x in bits if x]))


def _topic_signature_from_state(topic: Dict[str, Any]) -> Set[str]:
    bits = [
        str(topic.get("subject") or ""),
        str(topic.get("metric") or ""),
        " ".join([str(x) for x in list(topic.get("group_by") or [])]),
        " ".join([str(k) for k in list((topic.get("filters") or {}).keys())]),
    ]
    ts = topic.get("time_scope") if isinstance(topic.get("time_scope"), dict) else {}
    bits.append(str(ts.get("mode") or ""))
    bits.append(str(ts.get("value") or ""))
    return _tokenize(" ".join([x for x in bits if x]))


def _spec_signal_strength(spec: Dict[str, Any]) -> int:
    score = 0
    if str(spec.get("subject") or "").strip():
        score += 1
    if str(spec.get("metric") or "").strip():
        score += 1
    if list(spec.get("group_by") or []):
        score += 1
    if isinstance(spec.get("filters"), dict) and bool(spec.get("filters")):
        score += 1
    ts = spec.get("time_scope") if isinstance(spec.get("time_scope"), dict) else {}
    if str(ts.get("mode") or "none").strip().lower() not in ("", "none"):
        score += 1
    if str(ts.get("value") or "").strip():
        score += 1
    try:
        if int(spec.get("top_n") or 0) > 0:
            score += 1
    except Exception:
        pass
    return score


def _time_scope_missing(spec: Dict[str, Any]) -> bool:
    ts = spec.get("time_scope") if isinstance(spec.get("time_scope"), dict) else {}
    mode = str(ts.get("mode") or "none").strip().lower()
    value = str(ts.get("value") or "").strip()
    return (mode in ("", "none")) and (not value)


def _extract_doc_id_from_filters(filters: Dict[str, Any]) -> str:
    f = filters if isinstance(filters, dict) else {}
    for k, v in f.items():
        if str(k or "").strip().lower() not in _DOC_FILTER_KEYS:
            continue
        s = str(v or "").strip()
        if s and _DOC_ID_REGEX.search(s):
            return s
    return ""


def _extract_doc_id_from_payload(payload: Dict[str, Any]) -> str:
    out = payload if isinstance(payload, dict) else {}
    if str(out.get("type") or "").strip().lower() != "report_table":
        return ""
    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
    rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
    if not rows:
        return ""

    values: List[str] = []
    for r in rows[:30]:
        for s_raw in list((r or {}).values()):
            s = str(s_raw or "").strip()
            if s and _DOC_ID_REGEX.search(s):
                values.append(s)

    uniq = sorted(set(values))
    return uniq[0] if len(uniq) == 1 else ""


def get_topic_state(*, session_name: Optional[str]) -> Dict[str, Any]:
    """Load latest persisted topic state from tool messages."""
    if (not session_name) or (frappe is None):
        return {}
    try:
        session_doc = frappe.get_doc("AI Chat Session", session_name)
    except Exception:
        return {}

    for m in reversed(session_doc.get("messages") or []):
        if str(m.role or "").strip().lower() != "tool":
            continue
        obj = _safe_json_obj(m.content)
        if obj.get("type") != "v7_topic_state":
            continue
        st = obj.get("state")
        return st if isinstance(st, dict) else {}
    return {}


def apply_memory_context(
    *,
    business_spec: Dict[str, Any],
    message: str,
    topic_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Context binder without phrase dictionaries.
    It carries prior validated context only when current spec is underspecified.
    """
    spec = _ensure_spec_shape(_clone_spec(business_spec if isinstance(business_spec, dict) else {}))
    state = topic_state if isinstance(topic_state, dict) else {}
    prev_topic = state.get("active_topic") if isinstance(state.get("active_topic"), dict) else {}
    prev_result = state.get("active_result") if isinstance(state.get("active_result"), dict) else {}

    prev_filters = prev_topic.get("filters") if isinstance(prev_topic.get("filters"), dict) else {}
    prev_time_scope = prev_topic.get("time_scope") if isinstance(prev_topic.get("time_scope"), dict) else {}
    prev_group_by = [str(x).strip() for x in list(prev_topic.get("group_by") or []) if str(x).strip()][:10]
    prev_top_n = int(prev_topic.get("top_n") or 0) if str(prev_topic.get("top_n") or "0").strip().isdigit() else 0
    prev_metric = str(prev_topic.get("metric") or "").strip()
    prev_subject = str(prev_topic.get("subject") or "").strip()
    prev_result_doc_id = str(prev_result.get("document_id") or "").strip()

    curr_sig = _topic_signature_from_spec(spec)
    prev_sig = _topic_signature_from_state(prev_topic)
    curr_strength = _spec_signal_strength(spec)
    prev_strength = 0
    if prev_topic:
        prev_stub = {
            "subject": prev_subject,
            "metric": prev_metric,
            "group_by": prev_group_by,
            "filters": prev_filters,
            "time_scope": prev_time_scope,
            "top_n": prev_top_n,
        }
        prev_strength = _spec_signal_strength(prev_stub)

    overlap_ratio = 0.0
    if curr_sig and prev_sig:
        overlap_ratio = float(len(curr_sig & prev_sig)) / float(max(1, len(curr_sig | prev_sig)))

    # Topic switch only if user provided strong fresh spec with low overlap.
    topic_switched = bool(prev_topic and curr_strength >= 3 and prev_strength >= 2 and overlap_ratio < 0.10)

    anchors_applied: List[str] = []

    # Only anchor when current turn is structurally underspecified.
    can_anchor = bool(prev_topic) and (not topic_switched) and (curr_strength <= 2)
    if can_anchor:
        if not str(spec.get("subject") or "").strip() and prev_subject:
            spec["subject"] = prev_subject
            anchors_applied.append("subject")

        if not str(spec.get("metric") or "").strip() and prev_metric:
            spec["metric"] = prev_metric
            anchors_applied.append("metric")

        if not list(spec.get("group_by") or []) and prev_group_by:
            spec["group_by"] = prev_group_by[:10]
            anchors_applied.append("group_by")

        if int(spec.get("top_n") or 0) <= 0 and prev_top_n > 0:
            spec["top_n"] = prev_top_n
            if spec["output_contract"].get("mode") == "detail":
                spec["output_contract"]["mode"] = "top_n"
            anchors_applied.append("top_n")

        if _time_scope_missing(spec) and prev_time_scope:
            spec["time_scope"] = dict(prev_time_scope)
            anchors_applied.append("time_scope")

        curr_filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
        if prev_filters:
            merged = dict(curr_filters)
            for k, v in prev_filters.items():
                if k not in merged and v not in (None, "", []):
                    merged[k] = v
            if merged != curr_filters:
                spec["filters"] = merged
                anchors_applied.append("filters")

        has_doc_filter = bool(_extract_doc_id_from_filters(spec.get("filters") or {}))
        if (not has_doc_filter) and prev_result_doc_id and spec.get("task_type") == "detail":
            if "document_id" not in (spec.get("filters") or {}):
                spec["filters"]["document_id"] = prev_result_doc_id
                anchors_applied.append("document_id")

    # Keep output contract aligned with resolved semantic fields.
    oc = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    wanted = [str(x).strip() for x in list(oc.get("minimal_columns") or []) if str(x).strip()]
    if not wanted:
        if list(spec.get("group_by") or []):
            wanted.extend([str(x).strip() for x in list(spec.get("group_by") or []) if str(x).strip()])
        metric = str(spec.get("metric") or "").strip()
        if metric:
            wanted.append(metric)
        if wanted:
            spec["output_contract"] = dict(oc)
            spec["output_contract"]["minimal_columns"] = wanted[:12]

    # Update context strength after anchoring.
    anchored_strength = _spec_signal_strength(spec)
    message_words = len([w for w in str(message or "").split() if w.strip()])

    meta = {
        "memory_version": "phase6_topic_memory_v2_generic",
        "prev_domain": str((prev_topic.get("domain") if isinstance(prev_topic, dict) else "") or "").strip(),
        "curr_domain": "",
        "topic_switched": bool(topic_switched),
        "anchors_applied": anchors_applied,
        "corrections_applied": [],
        "curr_strength": curr_strength,
        "anchored_strength": anchored_strength,
        "overlap_ratio": round(overlap_ratio, 4),
        "message_words": message_words,
    }
    return {"spec": spec, "meta": meta}


def build_topic_state(
    *,
    previous_state: Dict[str, Any],
    business_spec: Dict[str, Any],
    resolved: Dict[str, Any],
    payload: Dict[str, Any],
    clarification_decision: Dict[str, Any],
    memory_meta: Dict[str, Any],
    message: str,
) -> Dict[str, Any]:
    prev = previous_state if isinstance(previous_state, dict) else {}
    spec = _ensure_spec_shape(business_spec if isinstance(business_spec, dict) else {})
    res = resolved if isinstance(resolved, dict) else {}
    out = payload if isinstance(payload, dict) else {}
    clar = clarification_decision if isinstance(clarification_decision, dict) else {}
    mm = memory_meta if isinstance(memory_meta, dict) else {}

    report_name = str(res.get("selected_report") or out.get("report_name") or "").strip()
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    time_scope = spec.get("time_scope") if isinstance(spec.get("time_scope"), dict) else {"mode": "none", "value": ""}
    doc_id = _extract_doc_id_from_filters(filters) or _extract_doc_id_from_payload(out)
    scaled_unit = str(out.get("_scaled_unit") or "").strip().lower()
    output_mode = str(out.get("_output_mode") or "").strip().lower() or str((spec.get("output_contract") or {}).get("mode") or "").strip().lower()

    kept_filters: Dict[str, Any] = {}
    for k, v in (filters or {}).items():
        if v not in (None, "", []):
            kept_filters[str(k)] = v

    topic_key = "|".join(
        [
            str(spec.get("subject") or "").strip().lower(),
            str(spec.get("metric") or "").strip().lower(),
            report_name.lower(),
        ]
    )

    return {
        "active_topic": {
            "topic_key": topic_key,
            "domain": str(spec.get("subject") or report_name or "").strip().lower()[:64],
            "subject": str(spec.get("subject") or "").strip(),
            "metric": str(spec.get("metric") or "").strip(),
            "group_by": [str(x).strip() for x in list(spec.get("group_by") or []) if str(x).strip()][:10],
            "top_n": int(spec.get("top_n") or 0) if str(spec.get("top_n") or "0").strip().isdigit() else 0,
            "report_name": report_name,
            "filters": kept_filters,
            "time_scope": dict(time_scope),
        },
        "active_result": {
            "result_id": str(doc_id or report_name or topic_key),
            "report_name": report_name,
            "document_id": str(doc_id or ""),
            "group_by": [str(x).strip() for x in list(spec.get("group_by") or []) if str(x).strip()][:10],
            "top_n": int(spec.get("top_n") or 0) if str(spec.get("top_n") or "0").strip().isdigit() else 0,
            "filters": kept_filters,
            "time_scope": dict(time_scope),
            "scaled_unit": scaled_unit,
            "output_mode": output_mode,
        },
        "unresolved_blocker": {
            "present": bool(clar.get("should_clarify")),
            "reason": str(clar.get("reason") or ""),
            "question": str(clar.get("question") or ""),
        },
        "correction_context": {
            "last_corrections": list(mm.get("corrections_applied") or []),
        },
        "turn_meta": {
            "topic_switched": bool(mm.get("topic_switched")),
            "anchors_applied": list(mm.get("anchors_applied") or []),
            "message_preview": str(message or "").strip()[:180],
        },
        "previous_topic_key": str(((prev.get("active_topic") or {}).get("topic_key") or "")).strip(),
        "version": "phase6_topic_memory_v2_generic",
    }


def make_topic_state_tool_message(*, tool: str, mode: str, state: Dict[str, Any], memory_meta: Dict[str, Any]) -> str:
    return json.dumps(
        {
            "type": "v7_topic_state",
            "phase": "phase6",
            "mode": str(mode or "").strip(),
            "tool": str(tool or "").strip(),
            "state": state if isinstance(state, dict) else {},
            "memory_meta": memory_meta if isinstance(memory_meta, dict) else {},
        },
        ensure_ascii=False,
        default=str,
    )


def build_turn_memory(*, pending_state: Dict[str, Any], last_result: Dict[str, Any]) -> Dict[str, Any]:
    """Backward-compatible helper retained for earlier imports."""
    return {
        "pending_mode": str((pending_state or {}).get("mode") or ""),
        "has_last_result": bool(last_result),
        "_phase": "phase6_topic_memory_v2_generic",
    }
