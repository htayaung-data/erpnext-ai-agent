from __future__ import annotations

import copy
import json
import re
from typing import Any, Dict, List, Optional, Set

try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover - local tests without Frappe
    frappe = None

from ai_assistant_ui.ai_core.ontology_normalization import (
    canonical_metric,
    canonical_dimension,
    infer_filter_kinds,
    infer_reference_value,
    infer_transform_ambiguities,
    known_dimension,
    metric_domain,
)

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
    out["task_class"] = str(out.get("task_class") or "analytical_read").strip().lower() or "analytical_read"
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


def _norm_text(text: Any) -> str:
    return " ".join(str(text or "").strip().lower().replace("_", " ").split())


def _first_int_in_text(text: Any) -> int:
    m = re.search(r"\b(\d{1,3})\b", str(text or ""))
    if not m:
        return 0
    try:
        return int(m.group(1))
    except Exception:
        return 0


def _message_has_explicit_time_words(message: str) -> bool:
    txt = _norm_text(message)
    if not txt:
        return False
    return bool(
        re.search(
            r"\b(?:today|yesterday|tomorrow|this month|last month|this week|last week|this year|last year|as of)\b",
            txt,
        )
    )


def _message_dimensions(message: str) -> List[str]:
    msg = str(message or "").strip()
    if not msg:
        return []
    allowed = {"customer", "supplier", "item", "warehouse", "company", "territory"}
    out: List[str] = []
    seen: Set[str] = set()

    direct = str(canonical_dimension(msg) or "").strip().lower()
    if direct in allowed and direct not in seen:
        seen.add(direct)
        out.append(direct)

    inferred = [str(x).strip().lower() for x in list(infer_filter_kinds(msg) or []) if str(x).strip()]
    for d in inferred:
        if d in allowed and d not in seen:
            seen.add(d)
            out.append(d)
    return out


def _projection_column_candidates(active_result: Dict[str, Any]) -> List[str]:
    result = active_result if isinstance(active_result, dict) else {}
    source_columns = [c for c in list(result.get("source_columns") or []) if isinstance(c, dict)]
    out: List[str] = []
    seen: Set[str] = set()
    for col in source_columns:
        label = _norm_text(col.get("label"))
        fieldname = _norm_text(col.get("fieldname"))
        canonical = label or fieldname
        if not canonical:
            continue
        if canonical in seen:
            continue
        seen.add(canonical)
        out.append(canonical)
    return out


def _message_projection_columns(message: str, active_result: Dict[str, Any]) -> List[str]:
    txt = _norm_text(message)
    if not txt:
        return []
    matches: List[str] = []
    seen: Set[str] = set()
    for candidate in sorted(_projection_column_candidates(active_result), key=len, reverse=True):
        if len(candidate) < 4:
            continue
        if candidate not in txt:
            continue
        if any(candidate in existing for existing in matches):
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        matches.append(candidate)
    return matches


def _semantic_column_keys(*, group_by: List[str], metric: str) -> Set[str]:
    out: Set[str] = set()
    for raw in list(group_by or []):
        key = _norm_text(raw)
        if key:
            out.add(key)
    metric_key = _norm_text(metric)
    if metric_key:
        out.add(metric_key)
    return out


def _message_transform_ambiguities(message: str) -> List[str]:
    return [str(x).strip().lower() for x in list(infer_transform_ambiguities(message) or []) if str(x).strip()]


def _explicit_message_projection_columns(*, message: str, requested_columns: List[str], semantic_column_keys: Set[str]) -> List[str]:
    txt = _norm_text(message)
    if not txt:
        return []
    out: List[str] = []
    seen: Set[str] = set()
    for raw in sorted([str(x or "").strip() for x in list(requested_columns or []) if str(x or "").strip()], key=len, reverse=True):
        s = str(raw or "").strip()
        key = _norm_text(s)
        if (not s) or (not key) or (key in semantic_column_keys):
            continue
        if key not in txt:
            continue
        key_tokens = set(key.split())
        if any(key == existing or key_tokens < set(existing.split()) for existing in seen):
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def _preferred_subject_from_dimension(dim: str) -> str:
    d = str(dim or "").strip().lower()
    if d == "item":
        return "products"
    if not d:
        return ""
    return f"{d}s"


def _spec_requested_dimensions(spec: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    dims = [str(x).strip() for x in list(spec.get("dimensions") or []) if str(x).strip()]
    group_by = [str(x).strip() for x in list(spec.get("group_by") or []) if str(x).strip()]
    oc = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    minimal = [str(x).strip() for x in list(oc.get("minimal_columns") or []) if str(x).strip()]
    for raw in dims + group_by + minimal:
        d = str(known_dimension(raw) or "").strip().lower()
        if not d or d in seen:
            continue
        seen.add(d)
        out.append(d)
    return out


def _filter_dimensions(filters: Dict[str, Any]) -> Set[str]:
    out: Set[str] = set()
    for k in list((filters or {}).keys()):
        kinds = [str(x).strip().lower() for x in list(infer_filter_kinds(k) or []) if str(x).strip()]
        for kind in kinds:
            if kind in {"customer", "supplier", "item", "warehouse", "company", "territory"}:
                out.add(kind)
    return out


def _resolve_reference_filters(*, filters: Dict[str, Any], prev_filters: Dict[str, Any]) -> Dict[str, Any]:
    current = filters if isinstance(filters, dict) else {}
    previous = prev_filters if isinstance(prev_filters, dict) else {}
    if (not current) or (not previous):
        return {"filters": dict(current), "applied": []}

    out = dict(current)
    applied: List[str] = []
    for key, value in current.items():
        prev_value = previous.get(key)
        if prev_value in (None, "", []):
            continue
        if isinstance(value, list):
            if len(value) != 1:
                continue
            ref_code = infer_reference_value(value[0])
            if ref_code == "same":
                out[key] = prev_value
                applied.append(str(key))
            continue
        ref_code = infer_reference_value(value)
        if ref_code == "same":
            out[key] = prev_value
            applied.append(str(key))
    return {"filters": out, "applied": applied}


def _topic_signature_from_spec(spec: Dict[str, Any]) -> Set[str]:
    bits: List[str] = [
        str(spec.get("subject") or ""),
        str(spec.get("metric") or ""),
        str(spec.get("task_type") or ""),
        str(spec.get("task_class") or ""),
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
    prev_domain = str(prev_topic.get("domain") or "").strip().lower()
    prev_result_doc_id = str(prev_result.get("document_id") or "").strip()
    incoming_output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    incoming_requested_columns = [
        str(x).strip() for x in list(incoming_output_contract.get("minimal_columns") or []) if str(x).strip()
    ]

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
    corrections_applied: List[str] = []
    prev_semantic_column_keys = _semantic_column_keys(group_by=prev_group_by, metric=prev_metric)
    projection_columns = [
        c
        for c in _message_projection_columns(message, prev_result)
        if _norm_text(c) not in prev_semantic_column_keys
    ]
    wants_projection_from_active_report = bool(
        prev_topic
        and prev_result
        and (not topic_switched)
        and projection_columns
    )

    # Resolve deictic filter references like "same warehouse" to the prior
    # validated filter value for that same filter key when the topic is stable.
    if prev_topic and (not topic_switched):
        current_filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
        reference_resolution = _resolve_reference_filters(filters=current_filters, prev_filters=prev_filters)
        resolved_filters = reference_resolution.get("filters") if isinstance(reference_resolution.get("filters"), dict) else current_filters
        applied_refs = [str(x).strip() for x in list(reference_resolution.get("applied") or []) if str(x).strip()]
        if applied_refs and resolved_filters != current_filters:
            spec["filters"] = resolved_filters
            anchors_applied.append("filter_reference")

    # Only anchor when current turn is structurally underspecified.
    can_anchor = bool(prev_topic) and (not topic_switched) and (curr_strength <= 2)
    if can_anchor:
        curr_domain = str(spec.get("domain") or "").strip().lower()
        if (not curr_domain or curr_domain == "unknown") and prev_domain:
            spec["domain"] = prev_domain
            anchors_applied.append("domain")

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

    requested_top_n = _first_int_in_text(message)
    if (
        prev_topic
        and (not topic_switched)
        and prev_top_n > 0
        and requested_top_n > 0
        and requested_top_n != int(spec.get("top_n") or 0)
        and curr_strength <= 2
    ):
        spec["top_n"] = max(1, min(requested_top_n, 200))
        oc = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
        spec["output_contract"] = dict(oc)
        spec["output_contract"]["mode"] = "top_n"
        corrections_applied.append("top_n_from_message_followup")

    current_transform_ambiguities = _message_transform_ambiguities(message)
    projection_only_followup = bool("transform_projection:only" in current_transform_ambiguities)
    ranking_direction_followup = bool(
        prev_topic
        and prev_result
        and (not topic_switched)
        and any(a in {"transform_sort:asc", "transform_sort:desc"} for a in current_transform_ambiguities)
        and int(prev_top_n or 0) > 0
        and curr_strength <= 4
        and (
            str(spec.get("intent") or "").strip().upper() == "TRANSFORM_LAST"
            or int(spec.get("top_n") or 0) <= 0
            or (not list(spec.get("group_by") or []))
        )
    )
    msg_metric_canonical = str(canonical_metric(message) or "").strip().lower()
    explicit_metric = msg_metric_canonical if msg_metric_canonical and msg_metric_canonical != _norm_text(message).replace(" ", "_") else ""
    explicit_dims = [str(x).strip().lower() for x in _message_dimensions(message)]
    strong_fresh_ranking_read = bool(
        str(spec.get("intent") or "").strip().upper() == "READ"
        and curr_strength >= 3
        and (explicit_metric or explicit_dims)
        and (requested_top_n > 0 or _message_has_explicit_time_words(message))
    )

    if strong_fresh_ranking_read:
        wants_projection_from_active_report = False

    explicit_read_rebind = bool(
        str(spec.get("intent") or "").strip().upper() == "READ"
        and curr_strength >= 3
        and (explicit_metric or explicit_dims)
    )
    if explicit_read_rebind:
        if explicit_metric:
            current_metric = str(canonical_metric(spec.get("metric") or "") or "").strip().lower()
            if explicit_metric != current_metric:
                spec["metric"] = explicit_metric.replace("_", " ")
                corrections_applied.append("metric_from_message_semantics")
                inferred_domain = str(metric_domain(explicit_metric) or "").strip().lower()
                if inferred_domain:
                    spec["domain"] = inferred_domain
                    corrections_applied.append("domain_from_metric_semantics")
        if explicit_dims:
            current_dims = _spec_requested_dimensions(spec)
            target_dims = [d for d in explicit_dims if d]
            if target_dims and target_dims != current_dims:
                spec["group_by"] = target_dims[:10]
                corrections_applied.append("group_by_from_message_semantics")
                subject = _preferred_subject_from_dimension(target_dims[0])
                if subject:
                    spec["subject"] = subject
                    corrections_applied.append("subject_from_message_dimension")
        if requested_top_n > 0 and requested_top_n != int(spec.get("top_n") or 0):
            spec["top_n"] = max(1, min(requested_top_n, 200))
            corrections_applied.append("top_n_from_message_semantics")
        oc_bind = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
        base_cols = [str(x).strip() for x in list(spec.get("group_by") or []) if str(x).strip()]
        metric_text = str(spec.get("metric") or "").strip()
        if metric_text:
            base_cols.append(metric_text)
        explicit_projection_cols = _explicit_message_projection_columns(
            message=message,
            requested_columns=incoming_requested_columns,
            semantic_column_keys=_semantic_column_keys(group_by=list(spec.get("group_by") or []), metric=metric_text),
        )
        spec["output_contract"] = dict(oc_bind)
        if int(spec.get("top_n") or 0) > 0:
            spec["output_contract"]["mode"] = "top_n"
        spec["output_contract"]["minimal_columns"] = list(dict.fromkeys(base_cols + explicit_projection_cols))[:12]

    explicit_read_reset = bool(
        str(spec.get("intent") or "").strip().upper() == "READ"
        and curr_strength >= 3
        and (not wants_projection_from_active_report)
    )
    if explicit_read_reset:
        existing_ambiguities = [str(x).strip().lower() for x in list(spec.get("ambiguities") or []) if str(x or "").strip()]
        non_transform_ambiguities = [x for x in existing_ambiguities if not x.startswith("transform_")]
        spec["ambiguities"] = list(dict.fromkeys(non_transform_ambiguities + current_transform_ambiguities))[:12]

        semantic_cols: List[str] = []
        for raw in list(spec.get("group_by") or []):
            s = str(raw or "").strip()
            if s:
                semantic_cols.append(s)
        metric = str(spec.get("metric") or "").strip()
        if metric:
            semantic_cols.append(metric)

        oc_reset = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
        current_cols = [str(x).strip() for x in list(oc_reset.get("minimal_columns") or []) if str(x or "").strip()]
        explicit_projection_cols = _explicit_message_projection_columns(
            message=message,
            requested_columns=current_cols,
            semantic_column_keys=_semantic_column_keys(group_by=list(spec.get("group_by") or []), metric=metric),
        )
        normalized_cols: List[str] = []
        seen_cols: Set[str] = set()
        for raw in semantic_cols + explicit_projection_cols:
            s = str(raw or "").strip()
            key = _norm_text(s)
            if (not s) or (not key) or (key in seen_cols):
                continue
            seen_cols.add(key)
            normalized_cols.append(s)
        spec["output_contract"] = dict(oc_reset)
        if int(spec.get("top_n") or 0) > 0:
            spec["output_contract"]["mode"] = "top_n"
        elif str(spec.get("task_type") or "").strip().lower() == "kpi":
            spec["output_contract"]["mode"] = "kpi"
        else:
            spec["output_contract"]["mode"] = "detail"
        spec["output_contract"]["minimal_columns"] = normalized_cols[:12]
        corrections_applied.append("fresh_read_contract_reset")

    if ranking_direction_followup:
        spec["intent"] = "READ"
        spec["subject"] = prev_subject or str(spec.get("subject") or "").strip()
        spec["metric"] = prev_metric or str(spec.get("metric") or "").strip()
        spec["domain"] = prev_domain or str(spec.get("domain") or "").strip().lower()
        spec["group_by"] = prev_group_by[:10]
        spec["top_n"] = prev_top_n
        if prev_time_scope:
            spec["time_scope"] = dict(prev_time_scope)
        if prev_filters:
            spec["filters"] = dict(prev_filters)
        spec["task_type"] = "ranking"
        spec["task_class"] = str(prev_topic.get("task_class") or spec.get("task_class") or "analytical_read").strip().lower()
        existing_ambiguities = [str(x).strip().lower() for x in list(spec.get("ambiguities") or []) if str(x or "").strip()]
        non_transform_ambiguities = [x for x in existing_ambiguities if not x.startswith("transform_")]
        spec["ambiguities"] = list(dict.fromkeys(non_transform_ambiguities + current_transform_ambiguities))[:12]
        oc_rank = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
        base_cols: List[str] = []
        for raw in prev_group_by:
            s = str(raw or "").strip()
            if s:
                base_cols.append(s)
        if prev_metric:
            base_cols.append(prev_metric)
        spec["output_contract"] = dict(oc_rank)
        spec["output_contract"]["mode"] = "top_n"
        spec["output_contract"]["minimal_columns"] = list(dict.fromkeys(base_cols))[:12]
        corrections_applied.append("ranking_direction_from_message_followup")
        wants_projection_from_active_report = False

    projection_only_active_followup = bool(
        prev_topic
        and prev_result
        and (not topic_switched)
        and projection_only_followup
    )
    if projection_only_active_followup:
        spec["subject"] = prev_subject or str(spec.get("subject") or "").strip()
        spec["metric"] = prev_metric or str(spec.get("metric") or "").strip()
        spec["domain"] = prev_domain or str(spec.get("domain") or "").strip().lower()
        spec["group_by"] = prev_group_by[:10]
        if prev_top_n > 0:
            spec["top_n"] = prev_top_n
            spec["task_type"] = "ranking"
        if prev_time_scope:
            spec["time_scope"] = dict(prev_time_scope)
        if prev_filters:
            spec["filters"] = dict(prev_filters)
        spec["task_class"] = str(prev_topic.get("task_class") or spec.get("task_class") or "analytical_read").strip().lower()
        output_mode = str(prev_result.get("output_mode") or "").strip().lower()
        oc_proj = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
        current = [str(x).strip() for x in list(oc_proj.get("minimal_columns") or []) if str(x).strip()]
        base_cols: List[str] = []
        for raw in prev_group_by:
            s = str(raw or "").strip()
            if s:
                base_cols.append(s)
        if prev_metric:
            base_cols.append(prev_metric)
        explicit_requested_cols = _explicit_message_projection_columns(
            message=message,
            requested_columns=current + base_cols + projection_columns,
            semantic_column_keys=set(),
        )
        projection_only_cols = list(explicit_requested_cols)
        prev_metric_canonical = str(canonical_metric(prev_metric) or "").strip().lower()
        if prev_metric and (
            _norm_text(message).find(_norm_text(prev_metric)) >= 0
            or (msg_metric_canonical and prev_metric_canonical and msg_metric_canonical == prev_metric_canonical)
        ):
            projection_only_cols.append(prev_metric)
        if projection_only_cols:
            merged_cols: List[str] = []
            seen_cols: Set[str] = set()
            for raw in projection_only_cols:
                s = str(raw or "").strip()
                key = _norm_text(s)
                if (not s) or (not key) or (key in seen_cols):
                    continue
                seen_cols.add(key)
                merged_cols.append(s)
            spec["output_contract"] = dict(oc_proj)
            spec["output_contract"]["mode"] = output_mode or str(oc_proj.get("mode") or "detail").strip().lower() or "detail"
            spec["output_contract"]["minimal_columns"] = merged_cols[:12]
            corrections_applied.append("projection_only_followup_to_active_topic")
            wants_projection_from_active_report = False

    low_signal_followup_rebind = bool(
        prev_topic
        and prev_result
        and (not topic_switched)
        and curr_strength <= 2
        and (current_transform_ambiguities or projection_columns or requested_top_n > 0)
    )
    if low_signal_followup_rebind:
        spec["subject"] = prev_subject or str(spec.get("subject") or "").strip()
        spec["metric"] = prev_metric or str(spec.get("metric") or "").strip()
        spec["domain"] = prev_domain or str(spec.get("domain") or "").strip().lower()
        spec["group_by"] = prev_group_by[:10]
        if requested_top_n > 0:
            spec["top_n"] = max(1, min(requested_top_n, 200))
        elif prev_top_n > 0:
            spec["top_n"] = prev_top_n
        if prev_time_scope:
            spec["time_scope"] = dict(prev_time_scope)
        if prev_filters:
            spec["filters"] = dict(prev_filters)
        spec["task_class"] = str(prev_topic.get("task_class") or spec.get("task_class") or "analytical_read").strip().lower()
        if int(spec.get("top_n") or 0) > 0:
            spec["task_type"] = "ranking"
        output_mode = str(prev_result.get("output_mode") or "").strip().lower()
        oc_follow = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
        base_cols: List[str] = []
        for raw in prev_group_by:
            s = str(raw or "").strip()
            if s:
                base_cols.append(s)
        if prev_metric:
            base_cols.append(prev_metric)
        merged_cols: List[str] = []
        seen_cols: Set[str] = set()
        explicit_requested_cols = _explicit_message_projection_columns(
            message=message,
            requested_columns=base_cols + projection_columns,
            semantic_column_keys=set(),
        )
        projection_only_cols = list(explicit_requested_cols)
        prev_metric_canonical = str(canonical_metric(prev_metric) or "").strip().lower()
        if projection_only_followup and prev_metric and (
            _norm_text(message).find(_norm_text(prev_metric)) >= 0
            or (msg_metric_canonical and prev_metric_canonical and msg_metric_canonical == prev_metric_canonical)
        ):
            projection_only_cols.append(prev_metric)
        selected_cols = projection_only_cols if (projection_only_followup and projection_only_cols) else (base_cols + projection_columns)
        for raw in selected_cols:
            s = str(raw or "").strip()
            key = _norm_text(s)
            if (not s) or (not key) or (key in seen_cols):
                continue
            seen_cols.add(key)
            merged_cols.append(s)
        spec["output_contract"] = dict(oc_follow)
        spec["output_contract"]["mode"] = output_mode or str(oc_follow.get("mode") or "detail").strip().lower() or "detail"
        spec["output_contract"]["minimal_columns"] = merged_cols[:12]
        corrections_applied.append("followup_rebind_to_active_topic")

    if wants_projection_from_active_report:
        spec["subject"] = prev_subject or str(spec.get("subject") or "").strip()
        spec["metric"] = prev_metric or str(spec.get("metric") or "").strip()
        spec["domain"] = prev_domain or str(spec.get("domain") or "").strip().lower()
        spec["group_by"] = prev_group_by[:10]
        if prev_top_n > 0:
            spec["top_n"] = prev_top_n
            spec["task_type"] = "ranking"
        if prev_time_scope:
            spec["time_scope"] = dict(prev_time_scope)
        if prev_filters:
            spec["filters"] = dict(prev_filters)
        spec["task_class"] = str(prev_topic.get("task_class") or spec.get("task_class") or "analytical_read").strip().lower()
        output_mode = str(prev_result.get("output_mode") or "").strip().lower()
        oc = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
        current = [str(x).strip() for x in list(oc.get("minimal_columns") or []) if str(x).strip()]
        base_cols: List[str] = []
        for raw in prev_group_by:
            s = str(raw or "").strip()
            if s:
                base_cols.append(s)
        if prev_metric:
            base_cols.append(prev_metric)
        merged_cols: List[str] = []
        seen_cols: Set[str] = set()
        explicit_requested_cols = _explicit_message_projection_columns(
            message=message,
            requested_columns=current + base_cols + projection_columns,
            semantic_column_keys=set(),
        )
        projection_only_cols = list(explicit_requested_cols)
        prev_metric_canonical = str(canonical_metric(prev_metric) or "").strip().lower()
        if projection_only_followup and prev_metric and (
            _norm_text(message).find(_norm_text(prev_metric)) >= 0
            or (msg_metric_canonical and prev_metric_canonical and msg_metric_canonical == prev_metric_canonical)
        ):
            projection_only_cols.append(prev_metric)
        selected_cols = projection_only_cols if (projection_only_followup and projection_only_cols) else (base_cols + projection_columns + current)
        for raw in selected_cols:
            s = str(raw or "").strip()
            key = _norm_text(s)
            if (not s) or (not key) or (key in seen_cols):
                continue
            seen_cols.add(key)
            merged_cols.append(s)
        spec["output_contract"] = dict(oc)
        spec["output_contract"]["mode"] = output_mode or str(oc.get("mode") or "detail").strip().lower() or "detail"
        spec["output_contract"]["minimal_columns"] = merged_cols[:12]
        anchors_applied.append("projection_columns")
        corrections_applied.append("projection_followup_from_active_report")

    # Deterministic dimension correction from explicit message semantics.
    # This is contract/ontology-driven and avoids ad-hoc phrase routing.
    msg_dims = _message_dimensions(message)
    req_dims = _spec_requested_dimensions(spec)
    filter_dims = _filter_dimensions(spec.get("filters") if isinstance(spec.get("filters"), dict) else {})
    if msg_dims:
        target_dims = [d for d in msg_dims if d not in filter_dims]
        if not target_dims:
            target_dims = list(msg_dims)
        missing_dims = [d for d in target_dims if d not in req_dims]
        if missing_dims:
            group_by = [str(x).strip() for x in list(spec.get("group_by") or []) if str(x).strip()]
            merged_group_by = list(dict.fromkeys(group_by + missing_dims))
            if merged_group_by != group_by:
                spec["group_by"] = merged_group_by[:10]
                corrections_applied.append("group_by_from_message_dimension")
            oc = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
            mode = str(oc.get("mode") or "detail").strip().lower() or "detail"
            if mode == "kpi":
                spec["output_contract"] = dict(oc)
                spec["output_contract"]["mode"] = "detail"
                corrections_applied.append("output_mode_from_kpi_to_detail")
            if missing_dims:
                oc2 = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
                wanted2 = [str(x).strip() for x in list(oc2.get("minimal_columns") or []) if str(x).strip()]
                merged_wanted = list(dict.fromkeys(wanted2 + missing_dims))
                if merged_wanted != wanted2:
                    spec["output_contract"] = dict(oc2)
                    spec["output_contract"]["minimal_columns"] = merged_wanted[:12]
                    corrections_applied.append("minimal_columns_from_message_dimension")

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
        "prev_domain": prev_domain,
        "curr_domain": str(spec.get("domain") or "").strip().lower(),
        "topic_switched": bool(topic_switched),
        "anchors_applied": anchors_applied,
        "corrections_applied": corrections_applied,
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
    source_columns = []
    for col in list(out.get("_source_columns") or []):
        if not isinstance(col, dict):
            continue
        fieldname = str(col.get("fieldname") or "").strip()
        label = str(col.get("label") or "").strip()
        if not fieldname and not label:
            continue
        source_columns.append(
            {
                "fieldname": fieldname,
                "label": label,
                "fieldtype": str(col.get("fieldtype") or "").strip(),
            }
        )

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
            "domain": str(spec.get("domain") or "").strip().lower(),
            "subject": str(spec.get("subject") or "").strip(),
            "metric": str(spec.get("metric") or "").strip(),
            "task_class": str(spec.get("task_class") or "analytical_read").strip().lower(),
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
            "task_class": str(spec.get("task_class") or "analytical_read").strip().lower(),
            "group_by": [str(x).strip() for x in list(spec.get("group_by") or []) if str(x).strip()][:10],
            "top_n": int(spec.get("top_n") or 0) if str(spec.get("top_n") or "0").strip().isdigit() else 0,
            "filters": kept_filters,
            "time_scope": dict(time_scope),
            "scaled_unit": scaled_unit,
            "output_mode": output_mode,
            "source_columns": source_columns[:40],
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
