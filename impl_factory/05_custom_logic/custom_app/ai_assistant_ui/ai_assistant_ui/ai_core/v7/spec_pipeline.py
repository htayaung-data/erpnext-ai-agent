from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover - allows local unit tests without Frappe runtime
    frappe = None

from ai_assistant_ui.ai_core.llm.report_planner import choose_business_request_spec
from ai_assistant_ui.ai_core.ontology_normalization import (
    canonical_dimension,
    canonical_metric,
    infer_advisory_intents,
    infer_contribution_terms,
    infer_exception_terms,
    infer_record_doctype_candidates,
    is_detail_constraint_metric,
    known_comparator,
    known_dimension,
    known_metric,
)
from ai_assistant_ui.ai_core.util_dates import extract_timeframe, last_month_range, last_week_range, this_month_range, this_week_range, today_date
from ai_assistant_ui.ai_core.v7.contract_registry import (
    task_class_allowed_dimensions,
    threshold_dimension_metric_overrides,
    threshold_metric_defaults_by_dimension,
)
from ai_assistant_ui.ai_core.v7.entity_resolution import extract_entity_filters_from_message
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
    task_type = str(out.get("task_type") or "").strip().lower()
    task_class = str(out.get("task_class") or "").strip().lower()
    output_mode = str(oc.get("mode") or "").strip().lower()
    requested_metric = str(canonical_metric(out.get("metric") or "") or "").strip().lower()
    suppress_metric_projection = bool(requested_metric) and is_detail_constraint_metric(requested_metric) and (
        task_type == "detail" or output_mode == "detail"
    )
    subject_tokens = {
        tok
        for tok in re.findall(r"[a-z0-9]+", str(out.get("subject") or "").strip().lower())
        if tok
    }
    normalized_subject_tokens = set(subject_tokens)
    normalized_subject_tokens.update({tok[:-1] for tok in subject_tokens if len(tok) > 3 and tok.endswith("s")})
    generic_latest_tokens = {"detail", "details", "record", "records", "list", "latest", "recent", "newest", "unspecified"}

    cols = []
    seen = set()
    for x in list(oc.get("minimal_columns") or []):
        s = str(x or "").strip()
        if not s:
            continue
        k = s.lower()
        if suppress_metric_projection:
            canonical = str(canonical_metric(s) or "").strip().lower()
            if canonical == requested_metric:
                continue
        if task_class == "list_latest_records":
            col_tokens = {tok for tok in re.findall(r"[a-z0-9]+", k) if tok}
            normalized_col_tokens = set(col_tokens)
            normalized_col_tokens.update({tok[:-1] for tok in col_tokens if len(tok) > 3 and tok.endswith("s")})
            if col_tokens:
                stripped_tokens = normalized_col_tokens - generic_latest_tokens
                if (
                    (col_tokens & {"detail", "details", "record", "records"})
                    and (not stripped_tokens or stripped_tokens <= normalized_subject_tokens)
                ):
                    continue
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


def _message_has_latest_record_cue(message: str) -> bool:
    text = str(message or "").strip().lower()
    if not text:
        return False
    return bool(re.search(r"\b(?:latest|recent|most recent|newest)\b", text))


_THRESHOLD_VALUE_RE = re.compile(
    r"\b(?P<number>(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?)|(?:\d+(?:\.\d+)?))\b(?:\s*(?P<scale>million|mn))?",
    re.IGNORECASE,
)


def _extract_threshold_signal(message: str, *, spec: Dict[str, Any]) -> Dict[str, Any]:
    text = str(message or "").strip()
    if not text:
        return {}
    comparator = str(known_comparator(text) or "").strip().lower()
    exception_terms = [str(x).strip().lower() for x in infer_exception_terms(text) if str(x).strip()]
    if (not comparator) and (not exception_terms):
        return {}
    explicit_dimension = str(
        known_dimension(text)
        or known_dimension(spec.get("subject") or "")
        or known_dimension((list(spec.get("group_by") or []) + list(spec.get("dimensions") or []) + [""])[0])
        or ""
    ).strip().lower()
    metric = str(known_metric(spec.get("metric")) or "").strip().lower()
    if not metric:
        metric = str(known_metric(text) or "").strip().lower()
    if not metric:
        metric = str(known_metric(spec.get("subject")) or "").strip().lower()
    metric_defaults = threshold_metric_defaults_by_dimension()
    if (not metric) and explicit_dimension:
        metric = str(metric_defaults.get(explicit_dimension) or "").strip().lower()
    override_rules = threshold_dimension_metric_overrides()
    if explicit_dimension and metric:
        metric_text = str(known_metric(metric) or metric or "").strip().lower()
        next_metric = str((override_rules.get(explicit_dimension) or {}).get(metric_text) or "").strip().lower()
        if next_metric:
            metric = next_metric
    elif explicit_dimension and (not metric):
        next_metric = str((override_rules.get(explicit_dimension) or {}).get("") or "").strip().lower()
        if next_metric:
            metric = next_metric
    return {
        "metric": metric,
        "comparator": comparator or "",
        "exception_terms": exception_terms,
    }


def _extract_threshold_rule(message: str, *, spec: Dict[str, Any]) -> Dict[str, Any]:
    text = str(message or "").strip()
    signal = _extract_threshold_signal(message, spec=spec)
    if not signal:
        return {}
    match = _THRESHOLD_VALUE_RE.search(text)
    if not match:
        return {}
    raw_number = str(match.group("number") or "").strip()
    if not raw_number:
        return {}
    try:
        numeric_value = float(raw_number.replace(",", ""))
    except Exception:
        return {}
    scale = str(match.group("scale") or "").strip().lower()
    if scale in {"million", "mn"}:
        numeric_value *= 1_000_000.0
    metric = str(signal.get("metric") or "").strip().lower()
    if not metric:
        return {}
    return {
        "metric": metric,
        "comparator": str(signal.get("comparator") or "").strip().lower(),
        "value": round(float(numeric_value), 6),
        "raw_value": str(match.group(0) or "").strip(),
        "exception_terms": list(signal.get("exception_terms") or []),
    }


def _threshold_missing_filter_kind(*, spec: Dict[str, Any], threshold_rule: Dict[str, Any]) -> str:
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    metric = str(known_metric((threshold_rule or {}).get("metric")) or (threshold_rule or {}).get("metric") or spec.get("metric") or "").strip().lower()
    group_by = {str(x).strip().lower() for x in list(spec.get("group_by") or []) if str(x or "").strip()}
    dimensions = {str(x).strip().lower() for x in list(spec.get("dimensions") or []) if str(x or "").strip()}
    if metric == "stock_quantity" and (("item" in group_by) or ("item" in dimensions)):
        if not str(filters.get("warehouse") or "").strip():
            return "warehouse"
    return ""


def _requested_dimensions_from_spec(spec: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in list(spec.get("group_by") or []) + list(spec.get("dimensions") or []):
        dim = str(known_dimension(raw) or "").strip().lower()
        if (not dim) or (dim in seen):
            continue
        seen.add(dim)
        out.append(dim)
    return out


def _threshold_unsupported_reason(message: str, *, spec: Dict[str, Any], signal: Dict[str, Any], threshold_rule: Dict[str, Any]) -> str:
    advisory_intents = infer_advisory_intents(message)
    if advisory_intents:
        return "advisory_analysis_not_supported"
    matches = list(_THRESHOLD_VALUE_RE.finditer(str(message or "")))
    if len(matches) > 1:
        return "range_threshold_not_supported"
    allowed_dims = task_class_allowed_dimensions("threshold_exception_list")
    if not allowed_dims:
        allowed_dims = {"customer", "supplier", "invoice", "item", "warehouse"}
    requested_dims = set(_requested_dimensions_from_spec(spec))
    explicit_dimension = str(known_dimension(message) or "").strip().lower()
    if explicit_dimension:
        requested_dims.add(explicit_dimension)
    if any(d and d not in allowed_dims for d in requested_dims):
        return "unsupported_grouping_not_supported"
    return ""


def _extract_contribution_signal(message: str, *, spec: Dict[str, Any]) -> Dict[str, Any]:
    text = str(message or "").strip()
    if not text:
        return {}
    contribution_terms = [str(x).strip().lower() for x in infer_contribution_terms(text) if str(x).strip()]
    primary_contribution_terms = {"share_of_total", "contribution_share"}
    has_primary_contribution_intent = bool(set(contribution_terms) & primary_contribution_terms)
    metric_from_message = str(known_metric(text) or "").strip().lower()
    metric = metric_from_message
    if not metric:
        metric = str(known_metric(spec.get("metric")) or "").strip().lower()
    if not metric:
        metric = str(known_metric(spec.get("subject")) or "").strip().lower()
    dimension_from_message = str(known_dimension(message) or "").strip().lower()
    explicit_dimension = str(
        dimension_from_message
        or known_dimension(spec.get("subject") or "")
        or known_dimension((list(spec.get("group_by") or []) + list(spec.get("dimensions") or []) + [""])[0])
        or ""
    ).strip().lower()
    advisory_intents = [str(x).strip().lower() for x in infer_advisory_intents(text) if str(x).strip()]
    if not contribution_terms:
        if advisory_intents and (metric or explicit_dimension):
            contribution_terms = ["share_of_total"]
            has_primary_contribution_intent = True
        else:
            return {}
    elif (not has_primary_contribution_intent) and (not advisory_intents):
        # Do not hijack non-contribution classes (for example plain comparison prompts).
        return {}
    return {
        "metric": metric,
        "explicit_dimension": explicit_dimension,
        "metric_from_message": metric_from_message,
        "dimension_from_message": dimension_from_message,
        "contribution_terms": contribution_terms,
    }


def _extract_contribution_rule(message: str, *, spec: Dict[str, Any]) -> Dict[str, Any]:
    signal = _extract_contribution_signal(message, spec=spec)
    if not signal:
        return {}
    return {
        "metric": str(signal.get("metric") or "").strip().lower(),
        "basis": "of_total",
        "contribution_terms": list(signal.get("contribution_terms") or []),
    }


def _contribution_missing_filter_kind(*, spec: Dict[str, Any], contribution_rule: Dict[str, Any], signal: Optional[Dict[str, Any]] = None) -> str:
    sig = signal if isinstance(signal, dict) else {}
    if not str(sig.get("metric_from_message") or "").strip():
        return "contribution_metric"
    if not str(sig.get("dimension_from_message") or "").strip():
        return "contribution_dimension"
    metric = str(known_metric((contribution_rule or {}).get("metric")) or (contribution_rule or {}).get("metric") or spec.get("metric") or "").strip().lower()
    group_by = {str(x).strip().lower() for x in list(spec.get("group_by") or []) if str(x or "").strip()}
    dimensions = {str(x).strip().lower() for x in list(spec.get("dimensions") or []) if str(x or "").strip()}
    if not metric:
        return "contribution_metric"
    if not (group_by or dimensions):
        return "contribution_dimension"
    return ""


def _contribution_unsupported_reason(message: str, *, spec: Dict[str, Any], contribution_rule: Dict[str, Any]) -> str:
    if infer_advisory_intents(message):
        return "advisory_analysis_not_supported"
    contribution_terms = [str(x).strip().lower() for x in infer_contribution_terms(message) if str(x).strip()]
    if "comparison_request" in contribution_terms:
        return "comparison_not_supported"
    if "cumulative_share" in contribution_terms:
        return "cumulative_share_not_supported"
    allowed_dims = task_class_allowed_dimensions("contribution_share")
    if not allowed_dims:
        allowed_dims = {"customer", "supplier", "item"}
    requested_dims = set(_requested_dimensions_from_spec(spec))
    explicit_dimension = str(known_dimension(message) or "").strip().lower()
    if explicit_dimension:
        requested_dims.add(explicit_dimension)
    if any(d and d not in allowed_dims for d in requested_dims):
        return "unsupported_grouping_not_supported"
    return ""


def _normalize_contribution_share_class(spec: Dict[str, Any], *, message: str) -> Dict[str, Any]:
    out = dict(spec or {})
    if str(out.get("intent") or "").strip().upper() != "READ":
        return out
    if _message_has_latest_record_cue(message):
        return out
    signal = _extract_contribution_signal(message, spec=out)
    if not signal:
        return out

    explicit_dimension = str(signal.get("explicit_dimension") or "").strip().lower()
    contribution_rule = _extract_contribution_rule(message, spec=out)
    filters = out.get("filters") if isinstance(out.get("filters"), dict) else {}
    filters = dict(filters)
    filters["_contribution_rule"] = contribution_rule or {
        "metric": str(signal.get("metric") or "").strip().lower(),
        "basis": "of_total",
        "contribution_terms": list(signal.get("contribution_terms") or []),
    }

    if explicit_dimension == "customer" and (not str(out.get("subject") or "").strip()):
        out["subject"] = "customers"
    elif explicit_dimension == "supplier" and (not str(out.get("subject") or "").strip()):
        out["subject"] = "suppliers"
    elif explicit_dimension == "item" and (not str(out.get("subject") or "").strip()):
        out["subject"] = "items"

    if explicit_dimension and (not list(out.get("dimensions") or [])):
        out["dimensions"] = [explicit_dimension]
    if explicit_dimension and (not list(out.get("group_by") or [])):
        out["group_by"] = [explicit_dimension]

    entity_filters = extract_entity_filters_from_message(
        message=message,
        allowed_kinds=["company", "customer", "supplier", "item"],
    )
    for key, value in entity_filters.items():
        if key not in filters and str(value or "").strip():
            filters[key] = value

    unsupported_reason = _contribution_unsupported_reason(message, spec=out, contribution_rule=contribution_rule)
    if unsupported_reason:
        filters["_contribution_unsupported_reason"] = unsupported_reason
    missing_filter_kind = _contribution_missing_filter_kind(
        spec=out,
        contribution_rule=contribution_rule or filters.get("_contribution_rule") or {},
        signal=signal,
    )
    if missing_filter_kind:
        filters["_contribution_missing_filter_kind"] = missing_filter_kind

    out["filters"] = filters
    out["task_class"] = "contribution_share"
    out["aggregation"] = "none"
    metric = str((contribution_rule or {}).get("metric") or signal.get("metric") or out.get("metric") or "").strip()
    out["metric"] = metric
    try:
        top_n = int(out.get("top_n") or 0)
    except Exception:
        top_n = 0
    if top_n > 0:
        out["task_type"] = "ranking"
        output_mode = "top_n"
    else:
        out["task_type"] = "detail"
        output_mode = "detail"
    if str(out.get("domain") or "").strip().lower() in {"", "unknown"}:
        metric_lc = str(known_metric(metric) or metric or "").strip().lower()
        if explicit_dimension in {"customer", "item"} or metric_lc == "revenue":
            out["domain"] = "sales"
        elif explicit_dimension == "supplier" or metric_lc == "purchase_amount":
            out["domain"] = "purchasing"
    output_contract = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
    output_contract = dict(output_contract)
    output_contract["mode"] = output_mode
    out["output_contract"] = output_contract
    return out


def _normalize_threshold_exception_class(spec: Dict[str, Any], *, message: str) -> Dict[str, Any]:
    out = dict(spec or {})
    if str(out.get("intent") or "").strip().upper() != "READ":
        return out
    if _message_has_latest_record_cue(message):
        return out
    try:
        if int(out.get("top_n") or 0) > 0:
            return out
    except Exception:
        pass
    signal = _extract_threshold_signal(message, spec=out)
    if not signal:
        return out
    explicit_dimension = str(canonical_dimension(message) or canonical_dimension(out.get("subject") or "") or "").strip().lower()
    threshold_rule = _extract_threshold_rule(message, spec=out)
    filters = out.get("filters") if isinstance(out.get("filters"), dict) else {}
    filters = dict(filters)
    if threshold_rule:
        filters["_threshold_rule"] = threshold_rule
    else:
        filters["_threshold_rule"] = {
            "metric": str(signal.get("metric") or "").strip().lower(),
            "comparator": str(signal.get("comparator") or "").strip().lower(),
            "exception_terms": list(signal.get("exception_terms") or []),
            "value_present": False,
        }
    if explicit_dimension == "warehouse" and (not str(out.get("subject") or "").strip()):
        out["subject"] = "warehouses"
    elif explicit_dimension == "item" and (not str(out.get("subject") or "").strip()):
        out["subject"] = "items"
    elif explicit_dimension == "invoice" and (not str(out.get("subject") or "").strip()):
        out["subject"] = "invoices"

    if explicit_dimension and (not list(out.get("dimensions") or [])):
        out["dimensions"] = [explicit_dimension]
    if explicit_dimension and (not list(out.get("group_by") or [])):
        out["group_by"] = [explicit_dimension]

    entity_filters = extract_entity_filters_from_message(
        message=message,
        allowed_kinds=["warehouse", "customer", "supplier", "company", "territory"],
    )
    for key, value in entity_filters.items():
        if key not in filters and str(value or "").strip():
            filters[key] = value
    unsupported_reason = _threshold_unsupported_reason(message, spec=out, signal=signal, threshold_rule=threshold_rule)
    if unsupported_reason:
        filters["_threshold_unsupported_reason"] = unsupported_reason
    missing_filter_kind = _threshold_missing_filter_kind(spec=out, threshold_rule=threshold_rule or filters.get("_threshold_rule") or {})
    if missing_filter_kind:
        filters["_threshold_missing_filter_kind"] = missing_filter_kind
    out["filters"] = filters
    out["task_class"] = "threshold_exception_list"
    out["task_type"] = "detail"
    out["aggregation"] = "none"
    out["top_n"] = 0
    out["metric"] = str((threshold_rule or {}).get("metric") or signal.get("metric") or out.get("metric") or "").strip()
    if str(out.get("domain") or "").strip().lower() in {"", "unknown"}:
        metric = str(known_metric(out.get("metric")) or out.get("metric") or "").strip().lower()
        if metric == "stock_quantity":
            out["domain"] = "inventory"
        elif metric == "invoice_amount":
            out["domain"] = "sales" if "sales" in str(message or "").lower() else "unknown"
    output_contract = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
    output_contract = dict(output_contract)
    output_contract["mode"] = "detail"
    out["output_contract"] = output_contract
    return out


@lru_cache(maxsize=1)
def _load_submittable_doctypes() -> List[str]:
    if frappe is None:
        return []
    rows: List[Dict[str, Any]] = []
    try:
        rows = frappe.get_all(
            "DocType",
            fields=["name"],
            filters={"istable": 0, "issingle": 0, "is_submittable": 1},
            order_by="name asc",
            limit_page_length=2000,
        )
    except Exception:
        rows = []
    out: List[str] = []
    seen = set()
    for row in list(rows or []):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(name)
    return out


def _first_int_in_text(message: str) -> int:
    match = re.search(r"\b(\d{1,3})\b", str(message or ""))
    if not match:
        return 0
    try:
        return int(match.group(1))
    except Exception:
        return 0


def _doctype_domain(doctype: str) -> str:
    dt = str(doctype or "").strip().lower()
    if not dt:
        return ""
    if "purchase" in dt or "supplier" in dt:
        return "purchasing"
    if "sales" in dt or "customer" in dt:
        return "sales"
    if "stock" in dt or "inventory" in dt or "warehouse" in dt:
        return "inventory"
    return ""


def _normalize_explicit_latest_record_doctype(spec: Dict[str, Any], *, message: str) -> Dict[str, Any]:
    out = dict(spec or {})
    if str(out.get("intent") or "").strip().upper() != "READ":
        return out
    if not _message_has_latest_record_cue(message):
        return out

    candidate_doctypes = _load_submittable_doctypes()
    if not candidate_doctypes:
        return out

    query_parts = [
        str(message or "").strip(),
        str(out.get("subject") or "").strip(),
        str(out.get("metric") or "").strip(),
    ]
    domain = str(out.get("domain") or "").strip().lower()
    candidates = infer_record_doctype_candidates(
        query_parts=query_parts,
        candidate_doctypes=candidate_doctypes,
        domain=domain,
    )
    if len(candidates) != 1:
        return out

    chosen = str(candidates[0] or "").strip()
    if not chosen:
        return out

    filters = out.get("filters") if isinstance(out.get("filters"), dict) else {}
    filtered = {
        str(k): v
        for k, v in filters.items()
        if str(k or "").strip().lower() not in {"doctype", "document_type", "record_type", "voucher_type"}
    }
    filtered["doctype"] = chosen
    out["filters"] = filtered
    out["task_class"] = "list_latest_records"
    out["task_type"] = "detail"
    out["aggregation"] = "none"
    out["metric"] = ""
    out["dimensions"] = []
    out["group_by"] = []
    out["ambiguities"] = []
    out["needs_clarification"] = False
    out["clarification_question"] = ""
    out["subject"] = str(out.get("subject") or "invoices").strip() or "invoices"
    if str(out.get("domain") or "").strip().lower() in {"", "unknown"}:
        inferred_domain = _doctype_domain(chosen)
        if inferred_domain:
            out["domain"] = inferred_domain
    explicit_top_n = _first_int_in_text(message)
    if explicit_top_n > 0:
        top_n = explicit_top_n
    else:
        try:
            top_n = int(out.get("top_n") or 0)
        except Exception:
            top_n = 0
    if top_n > 0:
        out["top_n"] = max(1, min(top_n, 200))
    out["output_contract"] = {
        "mode": "top_n",
        "minimal_columns": [],
    }
    return out


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
    if _message_has_latest_record_cue(message):
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
        normalized = _normalize_threshold_exception_class(normalized, message=message)
        normalized = _normalize_contribution_share_class(normalized, message=message)
        normalized = _normalize_task_class_for_explicit_ranking(normalized, message=message)
        normalized = _normalize_explicit_latest_record_doctype(normalized, message=message)
        normalized = _normalize_minimal_columns(normalized)
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
