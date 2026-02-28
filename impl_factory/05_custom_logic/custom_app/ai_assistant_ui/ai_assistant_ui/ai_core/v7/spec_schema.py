from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ai_assistant_ui.ai_core.ontology_normalization import known_metric
from ai_assistant_ui.ai_core.v7.contract_registry import (
    allowed_spec_values,
    canonical_dimensions,
    default_clarification_question,
    domain_from_dimension,
)

ALLOWED_INTENTS = {x.upper() for x in allowed_spec_values("intents")}
ALLOWED_TASK_TYPES = allowed_spec_values("task_types")
ALLOWED_TASK_CLASSES = allowed_spec_values("task_classes")
ALLOWED_AGGREGATIONS = allowed_spec_values("aggregations")
ALLOWED_TIME_MODES = allowed_spec_values("time_modes")
ALLOWED_OUTPUT_MODES = allowed_spec_values("output_modes")
ALLOWED_DOMAINS = allowed_spec_values("domains")


def default_business_request_spec() -> Dict[str, Any]:
    return {
        "intent": "READ",
        "task_type": "detail",
        "task_class": "analytical_read",
        "domain": "unknown",
        "subject": "",
        "metric": "",
        "dimensions": [],
        "aggregation": "none",
        "group_by": [],
        "time_scope": {"mode": "none", "value": ""},
        "filters": {},
        "top_n": 0,
        "output_contract": {"mode": "detail", "minimal_columns": []},
        "ambiguities": [],
        "needs_clarification": False,
        "clarification_question": "",
        "confidence": 0.0,
    }


def _as_clean_str_list(value: Any, *, limit: int = 12) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    seen = set()
    for item in value[: max(0, int(limit))]:
        s = str(item or "").strip()
        if not s:
            continue
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out


def _normalize_intent(raw: Any) -> str:
    s = str(raw or "").strip().upper()
    if s == "TRANSFORM":
        return "TRANSFORM_LAST"
    if s == "WRITE":
        return "WRITE_DRAFT"
    return s


def _canonical_dimension(raw: Any) -> str:
    s = str(raw or "").strip().lower().replace(" ", "_")
    if not s:
        return ""
    allowed = canonical_dimensions()
    if s in allowed:
        return s
    return ""


def _default_task_class() -> str:
    if "analytical_read" in ALLOWED_TASK_CLASSES:
        return "analytical_read"
    return next(iter(ALLOWED_TASK_CLASSES or []), "analytical_read")


def _infer_task_class(*, spec: Dict[str, Any], raw_task_class: str) -> str:
    raw = str(raw_task_class or "").strip().lower()

    default_class = _default_task_class()
    raw_is_allowed = bool(raw and raw in ALLOWED_TASK_CLASSES)
    if raw_is_allowed and raw != default_class:
        # Explicit non-default classes from parser are preserved.
        return raw

    intent = str(spec.get("intent") or "").strip().upper()
    task_type = str(spec.get("task_type") or "").strip().lower()
    aggregation = str(spec.get("aggregation") or "").strip().lower()
    metric = str(spec.get("metric") or "").strip()
    subject = str(spec.get("subject") or "").strip()
    output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    output_mode = str(output_contract.get("mode") or "").strip().lower()
    try:
        top_n = int(spec.get("top_n") or 0)
    except Exception:
        top_n = 0

    group_by = [str(x).strip() for x in list(spec.get("group_by") or []) if str(x).strip()]
    dimensions = [str(x).strip() for x in list(spec.get("dimensions") or []) if str(x).strip()]
    minimal_columns = [str(x).strip() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()]
    has_projection_shape = bool(group_by or dimensions or minimal_columns)
    has_known_metric = bool(str(known_metric(metric) or "").strip() or str(known_metric(subject) or "").strip())

    inferred = default_class

    if intent == "TRANSFORM_LAST" and ("transform_followup" in ALLOWED_TASK_CLASSES):
        inferred = "transform_followup"

    elif (
        (top_n > 0)
        and (aggregation == "none")
        and (task_type in {"detail", "ranking"})
        and (not has_known_metric)
        and ("list_latest_records" in ALLOWED_TASK_CLASSES)
    ):
        inferred = "list_latest_records"

    elif (
        (top_n > 0)
        and (output_mode == "top_n")
        and (task_type in {"detail", "ranking", "kpi"})
        and (not group_by)
        and ("list_latest_records" in ALLOWED_TASK_CLASSES)
    ):
        # Keep record-list execution class when the request is top-n record listing
        # shape, even if parser provided aggregate/metric hints.
        inferred = "list_latest_records"

    elif (
        (task_type == "detail")
        and (output_mode == "detail")
        and has_projection_shape
        and ("detail_projection" in ALLOWED_TASK_CLASSES)
    ):
        inferred = "detail_projection"

    if inferred != default_class:
        return inferred
    if raw_is_allowed:
        return raw
    return default_class


def normalize_business_request_spec(raw: Any) -> Tuple[Dict[str, Any], List[str]]:
    """
    Strict Phase-2 schema normalization.
    Returns (normalized_spec, schema_errors).
    """
    out = default_business_request_spec()
    errors: List[str] = []

    if not isinstance(raw, dict):
        errors.append("spec_not_object")
        return out, errors

    intent = _normalize_intent(raw.get("intent"))
    if intent in ALLOWED_INTENTS:
        out["intent"] = intent
    else:
        errors.append("intent_invalid")

    task_type = str(raw.get("task_type") or "").strip().lower()
    if task_type in ALLOWED_TASK_TYPES:
        out["task_type"] = task_type
    elif raw.get("task_type") not in (None, ""):
        errors.append("task_type_invalid")
    raw_task_class = str(raw.get("task_class") or "").strip().lower()
    if raw_task_class and raw_task_class not in ALLOWED_TASK_CLASSES:
        errors.append("task_class_invalid")

    aggregation = str(raw.get("aggregation") or "").strip().lower()
    if aggregation in ALLOWED_AGGREGATIONS:
        out["aggregation"] = aggregation
    elif raw.get("aggregation") not in (None, ""):
        errors.append("aggregation_invalid")

    out["subject"] = str(raw.get("subject") or "").strip()
    out["metric"] = str(raw.get("metric") or "").strip()
    out["group_by"] = _as_clean_str_list(raw.get("group_by"), limit=10)
    dims_raw = _as_clean_str_list(raw.get("dimensions"), limit=12)
    dims: List[str] = []
    seen_dims = set()
    for d in dims_raw:
        cd = _canonical_dimension(d)
        if not cd or cd in seen_dims:
            continue
        seen_dims.add(cd)
        dims.append(cd)
    out["dimensions"] = dims
    out["ambiguities"] = _as_clean_str_list(raw.get("ambiguities"), limit=10)

    domain = str(raw.get("domain") or "").strip().lower()
    if domain in ALLOWED_DOMAINS:
        out["domain"] = domain
    elif domain:
        errors.append("domain_invalid")

    time_scope = raw.get("time_scope") if isinstance(raw.get("time_scope"), dict) else {}
    if raw.get("time_scope") is not None and not isinstance(raw.get("time_scope"), dict):
        errors.append("time_scope_not_object")
    mode = str(time_scope.get("mode") or "").strip().lower()
    value = str(time_scope.get("value") or "").strip()
    if mode in ALLOWED_TIME_MODES:
        out["time_scope"] = {"mode": mode, "value": value}
    elif mode:
        errors.append("time_scope_mode_invalid")

    if isinstance(raw.get("filters"), dict):
        out["filters"] = dict(raw.get("filters") or {})
    elif raw.get("filters") not in (None, ""):
        errors.append("filters_not_object")

    try:
        top_n = int(raw.get("top_n") or 0)
    except Exception:
        top_n = 0
        if raw.get("top_n") not in (None, "", 0):
            errors.append("top_n_not_int")
    out["top_n"] = max(0, min(top_n, 200))

    output_contract = raw.get("output_contract") if isinstance(raw.get("output_contract"), dict) else {}
    if raw.get("output_contract") is not None and not isinstance(raw.get("output_contract"), dict):
        errors.append("output_contract_not_object")
    out_mode = str(output_contract.get("mode") or "").strip().lower()
    if out_mode in ALLOWED_OUTPUT_MODES:
        out["output_contract"]["mode"] = out_mode
    elif out_mode:
        errors.append("output_mode_invalid")
    out["output_contract"]["minimal_columns"] = _as_clean_str_list(output_contract.get("minimal_columns"), limit=12)

    out["needs_clarification"] = bool(raw.get("needs_clarification"))
    out["clarification_question"] = str(raw.get("clarification_question") or "").strip()[:280]
    try:
        confidence = float(raw.get("confidence") or 0.0)
    except Exception:
        confidence = 0.0
        if raw.get("confidence") not in (None, "", 0):
            errors.append("confidence_not_number")
    out["confidence"] = max(0.0, min(confidence, 1.0))
    if out["needs_clarification"] and not out["clarification_question"]:
        out["clarification_question"] = default_clarification_question("missing_required_filter_value")

    # Consistency normalization.
    if out["output_contract"]["mode"] == "top_n" and out["top_n"] <= 0:
        out["top_n"] = 5
    if out["top_n"] > 0 and out["output_contract"]["mode"] == "detail":
        out["output_contract"]["mode"] = "top_n"
    if out["output_contract"]["mode"] == "kpi" and out["aggregation"] == "none":
        out["aggregation"] = "sum"

    if not out["dimensions"]:
        inferred_dims: List[str] = []
        seen = set()
        for raw_dim in list(out.get("group_by") or []) + list(out["output_contract"].get("minimal_columns") or []):
            cd = _canonical_dimension(raw_dim)
            if not cd or cd in seen:
                continue
            seen.add(cd)
            inferred_dims.append(cd)
        out["dimensions"] = inferred_dims[:12]

    if out["domain"] == "unknown":
        dims = set([str(x or "").strip().lower() for x in list(out.get("dimensions") or []) if str(x or "").strip()])
        for d in ("customer", "supplier", "warehouse", "company"):
            if d not in dims:
                continue
            inferred = domain_from_dimension(d)
            if inferred:
                out["domain"] = inferred
                break

    if out["confidence"] <= 0.0:
        out["confidence"] = 0.7 if not errors else 0.4

    out["task_class"] = _infer_task_class(spec=out, raw_task_class=raw_task_class)

    return out, errors
