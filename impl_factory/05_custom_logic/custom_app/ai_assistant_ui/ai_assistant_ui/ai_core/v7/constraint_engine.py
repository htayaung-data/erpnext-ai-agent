from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from ai_assistant_ui.ai_core.ontology_normalization import (
    canonical_dimension,
    canonical_domain,
    infer_filter_kinds,
    known_dimension,
    known_metric,
    metric_domain,
)


_UNKNOWN_DOMAINS = {"", "unknown", "none", "generic", "general", "cross_functional"}
_STOP_TOKENS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "those",
    "these",
    "last",
    "month",
    "week",
    "year",
    "today",
}


def _non_empty(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, tuple, set, dict)):
        return bool(v)
    return True


def _tokens(value: Any) -> List[str]:
    raw = str(value or "").strip().lower()
    if not raw:
        return []
    out: List[str] = []
    seen: Set[str] = set()
    for t in re.findall(r"[a-z0-9_]+", raw):
        if len(t) < 3:
            continue
        if t in _STOP_TOKENS:
            continue
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _normalize_time_mode(spec: Dict[str, Any]) -> str:
    ts = spec.get("time_scope") if isinstance(spec.get("time_scope"), dict) else {}
    mode = str(ts.get("mode") or "none").strip().lower()
    if mode in {"as_of", "range", "relative", "none"}:
        return mode
    return "none"


def _requested_dimensions(spec: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    group_by = [str(x).strip() for x in list(spec.get("group_by") or []) if str(x).strip()]
    dimensions = [str(x).strip() for x in list(spec.get("dimensions") or []) if str(x).strip()]
    output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    minimal_cols = [str(x).strip() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()]
    for raw in dimensions + group_by + minimal_cols:
        cd = known_dimension(raw)
        s = str(cd or "").strip().lower()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    if not out:
        subject_dim = known_dimension(spec.get("subject"))
        sdim = str(subject_dim or "").strip().lower()
        if sdim and sdim not in seen:
            seen.add(sdim)
            out.append(sdim)
    return out


def _resolved_metric(spec: Dict[str, Any]) -> str:
    # Only ontology-known metrics may become hard metric constraints.
    # This prevents subject nouns (e.g., "invoice") from being treated as
    # synthetic metrics and contaminating resolver decisions.
    metric = str(known_metric(spec.get("metric")) or "").strip().lower()
    if metric:
        return metric
    subject_metric = str(known_metric(spec.get("subject")) or "").strip().lower()
    if subject_metric:
        return subject_metric
    return ""


def _hard_filter_kinds(filters: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    for k, v in (filters or {}).items():
        if not _non_empty(v):
            continue
        inferred = [str(x).strip().lower() for x in infer_filter_kinds(k) if str(x).strip()]
        # Hard constraints should only include ontology-recognized filter kinds.
        # Unknown raw keys stay as user filters but do not become hard blockers.
        kinds = list(dict.fromkeys(inferred))
        for kind in kinds:
            if kind in seen:
                continue
            seen.add(kind)
            out.append(kind)
    return out


def _active_filter_context(topic_state: Dict[str, Any]) -> Dict[str, Any]:
    state = topic_state if isinstance(topic_state, dict) else {}
    active_topic = state.get("active_topic") if isinstance(state.get("active_topic"), dict) else {}
    prev_filters = active_topic.get("filters") if isinstance(active_topic.get("filters"), dict) else {}
    out: Dict[str, Any] = {}
    for k, v in (prev_filters or {}).items():
        if _non_empty(v):
            out[str(k)] = v
    return out


def _resolve_domain(*, spec: Dict[str, Any], requested_dimensions: List[str], topic_state: Dict[str, Any]) -> str:
    metric = _resolved_metric(spec)
    domain_raw = canonical_domain(spec.get("domain"))
    if domain_raw not in _UNKNOWN_DOMAINS:
        return str(domain_raw).strip().lower()

    metric_dom = str(metric_domain(metric) or "").strip().lower()
    if metric_dom and metric_dom not in _UNKNOWN_DOMAINS:
        return metric_dom

    for d in list(requested_dimensions or []):
        if d == "customer":
            return "sales"
        if d == "supplier":
            return "purchasing"
        if d == "warehouse":
            return "inventory"
        if d == "company":
            return "finance"

    state = topic_state if isinstance(topic_state, dict) else {}
    active_topic = state.get("active_topic") if isinstance(state.get("active_topic"), dict) else {}
    prev_domain = canonical_domain(active_topic.get("domain"))
    if prev_domain and prev_domain not in _UNKNOWN_DOMAINS:
        return str(prev_domain).strip().lower()
    return "unknown"


def build_constraint_set(*, business_spec: Dict[str, Any], topic_state: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Deterministic Phase-3 constraint contract built from normalized business spec.
    """
    spec = business_spec if isinstance(business_spec, dict) else {}
    state = topic_state if isinstance(topic_state, dict) else {}
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    req_dims = _requested_dimensions(spec)
    metric = _resolved_metric(spec)
    subject = str(spec.get("subject") or "").strip()
    task_type = str(spec.get("task_type") or "").strip().lower()
    task_class = str(spec.get("task_class") or "").strip().lower() or "analytical_read"
    output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    output_mode = str(output_contract.get("mode") or "").strip().lower()
    time_mode = _normalize_time_mode(spec)
    try:
        requested_limit = max(0, int(spec.get("top_n") or 0))
    except Exception:
        requested_limit = 0
    sort_intent = "latest_desc" if task_class == "list_latest_records" else ""

    active_topic = state.get("active_topic") if isinstance(state.get("active_topic"), dict) else {}
    active_result = state.get("active_result") if isinstance(state.get("active_result"), dict) else {}
    followup_bindings = {
        "active_topic_key": str(active_topic.get("topic_key") or "").strip(),
        "previous_topic_key": str(state.get("previous_topic_key") or "").strip(),
        "active_result_id": str(active_result.get("result_id") or "").strip(),
    }

    return {
        "schema_version": "constraint_set_v1",
        "domain": _resolve_domain(spec=spec, requested_dimensions=req_dims, topic_state=state),
        "metric": str(metric or "").strip().lower(),
        "task_type": task_type,
        "task_class": task_class,
        "output_mode": output_mode,
        "requested_limit": requested_limit,
        "sort_intent": sort_intent,
        "time_mode": time_mode,
        "filters": dict(filters),
        "hard_filter_kinds": _hard_filter_kinds(filters),
        "requested_dimensions": req_dims,
        "subject_tokens": _tokens(subject),
        "followup_bindings": followup_bindings,
        "active_filter_context": _active_filter_context(state),
    }
