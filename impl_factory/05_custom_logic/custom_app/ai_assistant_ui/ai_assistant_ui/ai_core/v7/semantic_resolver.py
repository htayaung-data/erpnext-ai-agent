from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Set

from ai_assistant_ui.ai_core.ontology_normalization import (
    canonical_dimension,
    canonical_domain,
    canonical_metric,
    infer_filter_kinds,
    metric_domain,
)


def _non_empty(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, dict, tuple, set)):
        return bool(v)
    return True


def _extract_filter_kinds(filters: Dict[str, Any]) -> List[str]:
    kinds: Set[str] = set()
    for k, v in (filters or {}).items():
        if not _non_empty(v):
            continue
        for kind in infer_filter_kinds(k):
            kinds.add(kind)
    return sorted(kinds)


def _canonical_dim(value: Any) -> str:
    d = canonical_dimension(value)
    return str(d or "").strip().lower()


def _tokens(value: Any) -> Set[str]:
    raw = str(value or "").strip().lower()
    if not raw:
        return set()
    stop = {"the", "and", "for", "with", "from", "that", "this", "those", "these", "last", "this", "month", "week", "year", "today"}
    out: Set[str] = set()
    for t in re.findall(r"[a-z0-9]+", raw):
        if len(t) < 3:
            continue
        if t in stop:
            continue
        out.add(t)
    return out


def _extract_spec_semantics(spec: Dict[str, Any]) -> Dict[str, Any]:
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    group_by = [str(x).strip().lower() for x in list(spec.get("group_by") or []) if str(x or "").strip()]
    output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    dimensions = [str(x).strip().lower() for x in list(spec.get("dimensions") or []) if str(x or "").strip()]

    requested_dims: Set[str] = set()
    for raw in dimensions + group_by:
        dim = _canonical_dim(raw)
        if dim:
            requested_dims.add(dim)

    time_scope = spec.get("time_scope") if isinstance(spec.get("time_scope"), dict) else {}
    time_mode = str(time_scope.get("mode") or "none").strip().lower()
    metric = canonical_metric(spec.get("metric"))
    domain_raw = canonical_domain(spec.get("domain"))
    subject_raw = canonical_domain(spec.get("subject"))
    domain_unspecified = {"", "unknown", "none", "generic", "general", "cross_functional"}
    if domain_raw in domain_unspecified:
        domain = metric_domain(metric) or (subject_raw if subject_raw not in domain_unspecified else "") or "unknown"
    else:
        domain = domain_raw

    return {
        "filters": filters,
        "hard_filter_kinds": _extract_filter_kinds(filters),
        "requested_dimensions": sorted(requested_dims),
        "task_type": str(spec.get("task_type") or "").strip().lower(),
        "output_mode": str(output_contract.get("mode") or "").strip().lower(),
        "aggregation": str(spec.get("aggregation") or "").strip().lower(),
        "time_mode": time_mode,
        "domain": domain,
        "metric": metric,
        "subject_tokens": sorted(_tokens(spec.get("subject"))),
    }


def _required_kind_satisfied(*, kind: str, spec_sem: Dict[str, Any], spec_filters: Dict[str, Any]) -> bool:
    k = str(kind or "").strip().lower()
    if not k:
        return True

    for fk, fv in (spec_filters or {}).items():
        fk_lc = str(fk or "").strip().lower()
        if (k in fk_lc) and _non_empty(fv):
            return True

    time_mode = str(spec_sem.get("time_mode") or "none").strip().lower()
    has_time_scope = time_mode in {"range", "relative", "as_of"}
    if k in {"date", "from_date", "to_date", "report_date", "start_year", "end_year", "year"}:
        return has_time_scope
    if k == "fiscal_year":
        return False
    return False


def _cap_domains(cap: Dict[str, Any]) -> Set[str]:
    semantics = cap.get("semantics") if isinstance(cap.get("semantics"), dict) else {}
    hints = semantics.get("domain_hints") if isinstance(semantics.get("domain_hints"), list) else cap.get("domain_tags") or []
    out: Set[str] = set()
    for h in list(hints or []):
        s = str(h or "").strip().lower()
        if s:
            out.add(s)
    return out


def _cap_dimensions(cap: Dict[str, Any]) -> Set[str]:
    semantics = cap.get("semantics") if isinstance(cap.get("semantics"), dict) else {}
    hints = semantics.get("dimension_hints") if isinstance(semantics.get("dimension_hints"), list) else cap.get("dimension_tags") or []
    out: Set[str] = set()
    for h in list(hints or []):
        dim = _canonical_dim(h)
        if dim:
            out.add(dim)
    return out


def _cap_metrics(cap: Dict[str, Any]) -> Set[str]:
    semantics = cap.get("semantics") if isinstance(cap.get("semantics"), dict) else {}
    hints = semantics.get("metric_hints") if isinstance(semantics.get("metric_hints"), list) else cap.get("metric_tags") or []
    out: Set[str] = set()
    for h in list(hints or []):
        m = canonical_metric(h)
        if m:
            out.add(m)
    return out


def _cap_primary_dimension(cap: Dict[str, Any]) -> str:
    semantics = cap.get("semantics") if isinstance(cap.get("semantics"), dict) else {}
    primary = str(semantics.get("primary_dimension") or cap.get("primary_dimension") or "").strip().lower()
    return primary


def _cap_constraints(cap: Dict[str, Any]) -> Dict[str, Any]:
    constraints = cap.get("constraints") if isinstance(cap.get("constraints"), dict) else {}
    if constraints:
        return constraints
    return {
        "supported_filter_kinds": list(cap.get("supported_filter_kinds") or []),
        "required_filter_kinds": list(cap.get("required_filter_kinds") or []),
        "requirements_unknown": bool(cap.get("requirements_unknown")),
    }


def _cap_meta(cap: Dict[str, Any]) -> Dict[str, Any]:
    return cap.get("metadata") if isinstance(cap.get("metadata"), dict) else {}


def _score_candidate(spec_sem: Dict[str, Any], cap: Dict[str, Any]) -> Dict[str, Any]:
    constraints = _cap_constraints(cap)
    meta = _cap_meta(cap)
    cap_filters = {str(x or "").strip().lower() for x in list(constraints.get("supported_filter_kinds") or []) if str(x or "").strip()}
    cap_req_kinds = {str(x or "").strip().lower() for x in list(constraints.get("required_filter_kinds") or []) if str(x or "").strip()}
    requirements_unknown = bool(constraints.get("requirements_unknown"))
    time_support = cap.get("time_support") if isinstance(cap.get("time_support"), dict) else {}

    score = int(round(float(meta.get("confidence") or 0.0) * 100.0))
    reasons: List[str] = [f"confidence_base={score}"]
    hard_blockers: List[str] = []

    if not bool(meta.get("fresh", True)):
        score -= 40
        reasons.append("stale_capability(-40)")
    else:
        reasons.append("fresh_capability(+0)")

    hard_filter_kinds = {str(x or "").strip().lower() for x in list(spec_sem.get("hard_filter_kinds") or []) if str(x or "").strip()}
    if requirements_unknown and hard_filter_kinds:
        score -= 20
        reasons.append("requirements_unknown_with_hard_filters(-20)")

    missing_constraint_kinds = sorted([k for k in hard_filter_kinds if k not in cap_filters])
    for kind in missing_constraint_kinds:
        hard_blockers.append(f"unsupported_filter_kind:{kind}")
    if missing_constraint_kinds:
        score -= 120
        reasons.append("hard_constraint_missing(-120)")
    elif hard_filter_kinds:
        delta = min(24, len(hard_filter_kinds) * 6)
        score += delta
        reasons.append(f"hard_constraint_supported(+{delta})")

    requested_dims = {str(x or "").strip().lower() for x in list(spec_sem.get("requested_dimensions") or []) if str(x or "").strip()}
    cap_dims = _cap_dimensions(cap)
    cap_primary_dim = _cap_primary_dimension(cap)
    task_type = str(spec_sem.get("task_type") or "").strip().lower()
    if requested_dims:
        if cap_primary_dim and cap_primary_dim not in requested_dims:
            score -= 36
            reasons.append("primary_dimension_mismatch(-36)")
            if task_type in {"ranking", "detail", "comparison"}:
                hard_blockers.append("primary_dimension_mismatch")
        if cap_dims:
            hits = sorted(list(requested_dims & cap_dims))
            if hits:
                delta = min(24, len(hits) * 8)
                score += delta
                reasons.append(f"dimension_match(+{delta})")
            else:
                score -= 28
                reasons.append("dimension_mismatch(-28)")
                if task_type in {"ranking", "detail", "comparison"}:
                    hard_blockers.append("unsupported_dimension")
        else:
            score -= 18
            reasons.append("dimension_unknown(-18)")

    requested_domain = str(spec_sem.get("domain") or "").strip().lower()
    cap_domains = _cap_domains(cap)
    if requested_domain and requested_domain != "unknown":
        if requested_domain in cap_domains:
            score += 20
            reasons.append("domain_match(+20)")
        elif cap_domains:
            score -= 30
            reasons.append("domain_mismatch(-30)")

    requested_metric = str(spec_sem.get("metric") or "").strip().lower()
    cap_metrics = _cap_metrics(cap)
    if requested_metric and requested_metric not in {"unspecified", "none"}:
        if cap_metrics:
            if requested_metric in cap_metrics:
                score += 26
                reasons.append("metric_match(+26)")
            else:
                score -= 18
                reasons.append("metric_mismatch(-18)")
        else:
            score -= 6
            reasons.append("metric_unknown(-6)")

    # Subject relevance scoring: keeps broad unseen phrasing anchored to
    # semantically relevant report families/names instead of random ties.
    subject_tokens = {str(x or "").strip().lower() for x in list(spec_sem.get("subject_tokens") or []) if str(x or "").strip()}
    if subject_tokens:
        report_name = str(cap.get("report_name") or cap.get("name") or "").strip().lower()
        report_family = str(cap.get("report_family") or cap.get("module") or "").strip().lower()
        cap_domains = _cap_domains(cap)
        cap_dims = _cap_dimensions(cap)
        token_pool: Set[str] = set()
        token_pool |= _tokens(report_name)
        token_pool |= _tokens(report_family)
        for d in cap_domains:
            token_pool |= _tokens(d)
        for d in cap_dims:
            token_pool |= _tokens(d)
        for m in cap_metrics:
            token_pool |= _tokens(m)
        overlap = sorted(list(subject_tokens & token_pool))
        if overlap:
            delta = min(24, len(overlap) * 8)
            score += delta
            reasons.append(f"subject_overlap(+{delta})")
        else:
            score -= 16
            reasons.append("subject_mismatch(-16)")
            if task_type in {"ranking", "detail", "comparison", "trend", "kpi"} and len(subject_tokens) >= 2:
                hard_blockers.append("subject_mismatch")

    output_mode = str(spec_sem.get("output_mode") or "").strip().lower()
    if task_type == "ranking" and output_mode == "top_n":
        if requested_dims and (requested_dims & cap_dims):
            score += 8
            reasons.append("ranking_dimension_ready(+8)")
        elif requested_dims:
            score -= 10
            reasons.append("ranking_dimension_missing(-10)")

    time_mode = str(spec_sem.get("time_mode") or "none").strip().lower()
    if time_mode in ("as_of", "relative", "range"):
        supports_range = bool(time_support.get("range"))
        supports_as_of = bool(time_support.get("as_of") or time_support.get("any"))
        if (time_mode == "range" and supports_range) or (time_mode in ("as_of", "relative") and supports_as_of):
            score += 8
            reasons.append("time_support(+8)")
        elif not bool(time_support.get("any")):
            hard_blockers.append("unsupported_time_scope")
            score -= 30
            reasons.append("time_not_supported(-30)")

    missing_required_values: List[str] = []
    spec_filters = spec_sem.get("filters") if isinstance(spec_sem.get("filters"), dict) else {}
    for kind in sorted(cap_req_kinds):
        if _required_kind_satisfied(kind=kind, spec_sem=spec_sem, spec_filters=spec_filters):
            continue
        if kind in {
            "company",
            "warehouse",
            "customer",
            "supplier",
            "item",
            "from_date",
            "to_date",
            "report_date",
            "date",
            "start_year",
            "end_year",
            "fiscal_year",
            "year",
        }:
            missing_required_values.append(kind)

    if missing_required_values:
        score -= min(35, len(missing_required_values) * 12)
        reasons.append("required_filter_value_missing")

    return {
        "report_name": str(cap.get("report_name") or cap.get("name") or "").strip(),
        "score": int(score),
        "confidence": round(float(meta.get("confidence") or 0.0), 4),
        "fresh": bool(meta.get("fresh", True)),
        "reasons": reasons,
        "hard_blockers": sorted(list(set(hard_blockers))),
        "supported_filter_kinds": sorted(cap_filters),
        "required_filter_kinds": sorted(cap_req_kinds),
        "missing_required_filter_values": missing_required_values,
    }


def _clarification_question_for_kind(kind: str) -> str:
    k = str(kind or "").strip().lower()
    if k == "company":
        return "Which company should I use?"
    if k == "warehouse":
        return "Which warehouse should I use?"
    if k == "customer":
        return "Which customer should I use?"
    if k == "supplier":
        return "Which supplier should I use?"
    if k == "item":
        return "Which item should I use?"
    if k in {"from_date", "to_date", "date", "report_date"}:
        return "Which date range should I use?"
    if k in {"start_year", "end_year", "year", "fiscal_year"}:
        return "Which fiscal year or year range should I use?"
    return "Which missing filter value should I use?"


def resolve_semantics(*, business_spec: Dict[str, Any], capability_index: Dict[str, Any]) -> Dict[str, Any]:
    spec = business_spec if isinstance(business_spec, dict) else {}
    index = capability_index if isinstance(capability_index, dict) else {}
    reports = [r for r in list(index.get("reports") or []) if isinstance(r, dict)]
    spec_sem = _extract_spec_semantics(spec)

    scored: List[Dict[str, Any]] = []
    for cap in reports:
        scored.append(_score_candidate(spec_sem, cap))
    scored.sort(key=lambda x: (int(x.get("score") or -9999), float(x.get("confidence") or 0.0), str(x.get("report_name") or "")), reverse=True)

    feasible_non_missing = [
        c for c in scored if (not list(c.get("hard_blockers") or [])) and (not list(c.get("missing_required_filter_values") or []))
    ]
    feasible_any = [c for c in scored if not list(c.get("hard_blockers") or [])]

    if feasible_non_missing:
        selected = feasible_non_missing[0]
    elif feasible_any:
        selected = feasible_any[0]
    else:
        selected = scored[0] if scored else {}

    selected_score = int(selected.get("score") or -9999) if selected.get("report_name") else None
    hard_blockers = list(selected.get("hard_blockers") or [])
    missing_required_values = list(selected.get("missing_required_filter_values") or [])
    selected_confidence = float(selected.get("confidence") or 0.0)

    needs_clarification = False
    clarification_reason = ""
    if not selected.get("report_name"):
        needs_clarification = True
        clarification_reason = "no_candidate"
    elif hard_blockers:
        needs_clarification = True
        clarification_reason = "hard_constraint_not_supported"
    elif missing_required_values:
        needs_clarification = True
        clarification_reason = "missing_required_filter_value"
    elif selected_confidence < 0.30:
        needs_clarification = True
        clarification_reason = "low_confidence_candidate"

    clarification_question = ""
    if clarification_reason == "missing_required_filter_value" and missing_required_values:
        clarification_question = _clarification_question_for_kind(missing_required_values[0])
    elif clarification_reason == "hard_constraint_not_supported":
        clarification_question = (
            "I could not find a capability-feasible report for the requested constraints. "
            "Please refine the required filters or business scope."
        )
    elif clarification_reason in ("no_candidate", "low_confidence_candidate"):
        clarification_question = "Please specify the business domain and target metric so I can choose the right report."

    return {
        "_phase": "phase2_semantic_resolver",
        "business_spec": spec,
        "hard_constraints": {
            "hard_filter_kinds": spec_sem.get("hard_filter_kinds"),
            "time_mode": spec_sem.get("time_mode"),
            "requested_dimensions": spec_sem.get("requested_dimensions"),
            "domain": spec_sem.get("domain"),
        },
        "candidate_reports": scored[:80],
        "selected_report": selected.get("report_name") or "",
        "selected_score": selected_score,
        "selected_confidence": round(selected_confidence, 4),
        "needs_clarification": needs_clarification,
        "clarification_reason": clarification_reason,
        "clarification_question": clarification_question,
    }
