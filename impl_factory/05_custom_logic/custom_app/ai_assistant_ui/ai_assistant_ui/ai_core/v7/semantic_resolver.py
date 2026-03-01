from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Set

from ai_assistant_ui.ai_core.ontology_normalization import (
    canonical_dimension,
    canonical_metric,
    known_metric,
    metric_domain,
)
from ai_assistant_ui.ai_core.v7.constraint_engine import build_constraint_set
from ai_assistant_ui.ai_core.v7.contract_registry import clarification_question_for_filter_kind
from ai_assistant_ui.ai_core.v7.contract_registry import default_clarification_question


def _non_empty(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, dict, tuple, set)):
        return bool(v)
    return True


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
    out = build_constraint_set(business_spec=spec, topic_state={})
    out["aggregation"] = str(spec.get("aggregation") or "").strip().lower()
    return out


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
    # Read engine can deterministically materialize these required filters:
    # - temporal fields via timeframe defaults
    # - company via user/system defaults
    # So resolver should not down-rank valid candidates when user omits them.
    if k in {"date", "from_date", "to_date", "report_date", "start_year", "end_year", "year", "fiscal_year", "company"}:
        return True
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


def _cap_presentation(cap: Dict[str, Any]) -> Dict[str, Any]:
    return cap.get("presentation") if isinstance(cap.get("presentation"), dict) else {}


def _score_candidate(spec_sem: Dict[str, Any], cap: Dict[str, Any], semantic_context: Dict[str, Any]) -> Dict[str, Any]:
    constraints = _cap_constraints(cap)
    meta = _cap_meta(cap)
    cap_filters = {str(x or "").strip().lower() for x in list(constraints.get("supported_filter_kinds") or []) if str(x or "").strip()}
    cap_req_kinds = {str(x or "").strip().lower() for x in list(constraints.get("required_filter_kinds") or []) if str(x or "").strip()}
    requirements_unknown = bool(constraints.get("requirements_unknown"))
    time_support = cap.get("time_support") if isinstance(cap.get("time_support"), dict) else {}

    score = int(round(float(meta.get("confidence") or 0.0) * 100.0))
    reasons: List[str] = [f"confidence_base={score}"]
    hard_blockers: List[str] = []
    tie_break_score = 0

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
    presentation = _cap_presentation(cap)
    task_type = str(spec_sem.get("task_type") or "").strip().lower()
    task_class = str(spec_sem.get("task_class") or "").strip().lower() or "analytical_read"
    output_mode = str(spec_sem.get("output_mode") or "").strip().lower()
    if requested_dims:
        if cap_primary_dim and cap_primary_dim not in requested_dims:
            score -= 36
            reasons.append("primary_dimension_mismatch(-36)")
            if task_type in {"ranking", "detail", "comparison"} and task_class != "list_latest_records":
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
                if task_type in {"ranking", "detail", "comparison"} and task_class != "list_latest_records":
                    hard_blockers.append("unsupported_dimension")
        else:
            score -= 18
            reasons.append("dimension_unknown(-18)")
            if (
                task_type in {"ranking", "detail", "comparison"}
                and output_mode != "kpi"
                and (not cap_primary_dim or cap_primary_dim not in requested_dims)
                and task_class != "list_latest_records"
            ):
                hard_blockers.append("unsupported_dimension")

    requested_domain = str(spec_sem.get("domain") or "").strip().lower()
    cap_domains = _cap_domains(cap)
    if requested_domain and requested_domain != "unknown":
        if requested_domain in cap_domains:
            score += 20
            reasons.append("domain_match(+20)")
        elif cap_domains:
            score -= 30
            reasons.append("domain_mismatch(-30)")

    # Metadata-grounded nudges from DB semantic catalog retrieval.
    ctx = semantic_context if isinstance(semantic_context, dict) else {}
    preferred_domains = {
        str(x).strip().lower()
        for x in list(ctx.get("preferred_domains") or [])
        if str(x).strip()
    }
    preferred_dims = {
        str(x).strip().lower()
        for x in list(ctx.get("preferred_dimensions") or [])
        if str(x).strip()
    }
    preferred_filter_kinds = {
        str(x).strip().lower()
        for x in list(ctx.get("preferred_filter_kinds") or [])
        if str(x).strip()
    }
    if preferred_domains and cap_domains:
        if cap_domains & preferred_domains:
            score += 10
            reasons.append("catalog_domain_alignment(+10)")
        else:
            score -= 8
            reasons.append("catalog_domain_mismatch(-8)")
    if preferred_dims and cap_dims:
        if cap_dims & preferred_dims:
            score += 8
            reasons.append("catalog_dimension_alignment(+8)")
        else:
            score -= 6
            reasons.append("catalog_dimension_mismatch(-6)")
    if preferred_filter_kinds and cap_filters:
        if cap_filters & preferred_filter_kinds:
            score += 6
            reasons.append("catalog_filter_alignment(+6)")

    requested_metric_raw = str(spec_sem.get("metric") or "").strip().lower()
    requested_metric = str(canonical_metric(requested_metric_raw) or requested_metric_raw).strip().lower()
    metric_is_known = bool(str(known_metric(requested_metric_raw) or "").strip())
    cap_metrics = _cap_metrics(cap)
    if requested_metric and requested_metric not in {"unspecified", "none"}:
        if not metric_is_known:
            score -= 2
            reasons.append("metric_unmapped_soft(-2)")
        elif cap_metrics:
            if requested_metric in cap_metrics:
                score += 26
                reasons.append("metric_match(+26)")
            else:
                score -= 28
                reasons.append("metric_mismatch(-28)")
                if task_type in {"ranking", "detail", "comparison", "kpi"} and task_class != "list_latest_records":
                    hard_blockers.append("unsupported_metric")
                req_metric_domain = str(metric_domain(requested_metric) or "").strip().lower()
                cap_metric_domains = {
                    str(metric_domain(m) or "").strip().lower()
                    for m in cap_metrics
                    if str(metric_domain(m) or "").strip()
                }
                if (
                    req_metric_domain
                    and cap_metric_domains
                    and req_metric_domain not in cap_metric_domains
                    and task_type in {"ranking", "detail", "comparison"}
                    and task_class != "list_latest_records"
                ):
                    hard_blockers.append("metric_domain_mismatch")
        else:
            score -= 6
            reasons.append("metric_unknown(-6)")

    # Subject lexical signals are tie-break only (non-primary), never hard blockers.
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
            tie_break_score = min(8, len(overlap) * 2)
            reasons.append(f"subject_tiebreak(+{tie_break_score})")

    if task_type == "ranking" and output_mode == "top_n":
        supports_ranking = presentation.get("supports_ranking")
        result_grain = str(presentation.get("result_grain") or "").strip().lower()
        if supports_ranking is True:
            score += 6
            reasons.append("ranking_supported(+6)")
        elif supports_ranking is False:
            score -= 24
            reasons.append("ranking_not_supported(-24)")
            hard_blockers.append("ranking_not_supported")
        if requested_dims:
            if cap_primary_dim and cap_primary_dim in requested_dims:
                score += 12
                reasons.append("ranking_primary_dimension_match(+12)")
            elif not cap_primary_dim:
                score -= 18
                reasons.append("ranking_primary_dimension_unknown(-18)")
            if result_grain == "summary" and cap_primary_dim and cap_primary_dim in requested_dims:
                score += 4
                reasons.append("ranking_summary_grain_match(+4)")
            elif result_grain == "detail" and cap_primary_dim and cap_primary_dim not in requested_dims:
                score -= 10
                reasons.append("ranking_detail_grain_mismatch(-10)")
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

    if task_class == "list_latest_records":
        if bool(time_support.get("any")):
            score += 16
            reasons.append("latest_records_time_ready(+16)")
        else:
            score -= 22
            reasons.append("latest_records_time_missing(-22)")
        if cap_primary_dim:
            score += 4
            reasons.append("latest_records_primary_dimension(+4)")

    missing_required_values: List[str] = []
    spec_filters = spec_sem.get("filters") if isinstance(spec_sem.get("filters"), dict) else {}
    for kind in sorted(cap_req_kinds):
        if _required_kind_satisfied(kind=kind, spec_sem=spec_sem, spec_filters=spec_filters):
            continue
        missing_required_values.append(kind)

    if missing_required_values:
        score -= min(35, len(missing_required_values) * 12)
        reasons.append("required_filter_value_missing")

    return {
        "report_name": str(cap.get("report_name") or cap.get("name") or "").strip(),
        "score": int(score),
        "tie_break_score": int(tie_break_score),
        "confidence": round(float(meta.get("confidence") or 0.0), 4),
        "fresh": bool(meta.get("fresh", True)),
        "reasons": reasons,
        "hard_blockers": sorted(list(set(hard_blockers))),
        "supported_filter_kinds": sorted(cap_filters),
        "required_filter_kinds": sorted(cap_req_kinds),
        "missing_required_filter_values": missing_required_values,
    }


def _clarification_question_for_kind(kind: str) -> str:
    return clarification_question_for_filter_kind(kind)


def resolve_semantics(
    *,
    business_spec: Dict[str, Any],
    capability_index: Dict[str, Any],
    constraint_set: Dict[str, Any] | None = None,
    semantic_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    spec = business_spec if isinstance(business_spec, dict) else {}
    index = capability_index if isinstance(capability_index, dict) else {}
    reports = [r for r in list(index.get("reports") or []) if isinstance(r, dict)]
    spec_sem = (
        dict(constraint_set)
        if isinstance(constraint_set, dict) and bool(constraint_set)
        else _extract_spec_semantics(spec)
    )

    ctx = semantic_context if isinstance(semantic_context, dict) else {}
    scored: List[Dict[str, Any]] = []
    for cap in reports:
        scored.append(_score_candidate(spec_sem, cap, ctx))
    scored.sort(
        key=lambda x: (
            int(x.get("score") or -9999),
            int(x.get("tie_break_score") or 0),
            float(x.get("confidence") or 0.0),
            str(x.get("report_name") or ""),
        ),
        reverse=True,
    )

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
    elif clarification_reason:
        clarification_question = default_clarification_question(clarification_reason)

    return {
        "_phase": "phase3_semantic_resolver",
        "business_spec": spec,
        "hard_constraints": dict(spec_sem),
        "semantic_context": ctx,
        "candidate_reports": scored[:80],
        "selected_report": selected.get("report_name") or "",
        "selected_score": selected_score,
        "selected_confidence": round(selected_confidence, 4),
        "needs_clarification": needs_clarification,
        "clarification_reason": clarification_reason,
        "clarification_question": clarification_question,
    }
