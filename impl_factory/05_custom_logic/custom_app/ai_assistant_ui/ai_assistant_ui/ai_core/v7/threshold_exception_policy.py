from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional, Sequence, Set

from ai_assistant_ui.ai_core.ontology_normalization import known_dimension, known_metric
from ai_assistant_ui.ai_core.v7.capability_registry import report_semantics_contract


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", " ")


def _to_float(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).replace(",", "").strip()
        return float(text) if text else 0.0
    except Exception:
        return 0.0


def _safe_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    report_name = str(payload.get("report_name") or payload.get("title") or "").strip()
    return report_semantics_contract(report_name)


def _threshold_rule(spec: Dict[str, Any]) -> Dict[str, Any]:
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    rule = filters.get("_threshold_rule") if isinstance(filters.get("_threshold_rule"), dict) else {}
    metric = str(known_metric(rule.get("metric")) or rule.get("metric") or "").strip().lower()
    comparator = str(rule.get("comparator") or "").strip().lower()
    terms = {
        str(x).strip().lower()
        for x in list(rule.get("exception_terms") or [])
        if str(x).strip()
    }
    try:
        value = float(rule.get("value")) if rule.get("value") is not None else None
    except Exception:
        value = None
    return {
        "metric": metric,
        "comparator": comparator,
        "value": value,
        "value_present": bool(rule.get("value_present")),
        "exception_terms": terms,
    }


def _contract_role_fieldnames(contract: Dict[str, Any], role_type: str, role_name: str) -> List[str]:
    semantics = contract if isinstance(contract, dict) else {}
    presentation = semantics.get("presentation") if isinstance(semantics.get("presentation"), dict) else {}
    column_roles = presentation.get("column_roles") if isinstance(presentation.get("column_roles"), dict) else {}
    role_map = column_roles.get(role_type) if isinstance(column_roles.get(role_type), dict) else {}
    raw = role_map.get(role_name) if isinstance(role_map.get(role_name), list) else []
    return [str(x).strip().lower() for x in raw if str(x or "").strip()]


def _aggregate_dimension_values(contract: Dict[str, Any]) -> List[str]:
    presentation = contract.get("presentation") if isinstance(contract.get("presentation"), dict) else {}
    raw = presentation.get("aggregate_dimension_values") if isinstance(presentation.get("aggregate_dimension_values"), list) else []
    return [str(x).strip() for x in raw if str(x or "").strip()]


def _primary_dimension_names(contract: Dict[str, Any], spec: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    seen = set()

    def _append(raw: Any) -> None:
        dim = str(known_dimension(raw) or raw or "").strip().lower()
        if not dim or dim in seen:
            return
        seen.add(dim)
        out.append(dim)

    semantics = contract.get("semantics") if isinstance(contract.get("semantics"), dict) else {}
    _append(semantics.get("primary_dimension"))
    for raw in list(spec.get("group_by") or []) + list(spec.get("dimensions") or []):
        _append(raw)
    return out


def _find_column_fieldname(
    columns: List[Dict[str, Any]],
    candidates: Sequence[str],
    *,
    numeric_required: bool = False,
) -> str:
    wanted = {_norm(x) for x in candidates if _norm(x)}
    if not wanted:
        return ""
    for col in columns:
        fieldname = str(col.get("fieldname") or "").strip()
        label = str(col.get("label") or "").strip()
        if not fieldname:
            continue
        if numeric_required and (not _is_numeric_column(col)):
            continue
        if _norm(fieldname) in wanted or _norm(label) in wanted:
            return fieldname
    return ""


def _find_metric_fieldname(columns: List[Dict[str, Any]], contract: Dict[str, Any], metric: str) -> str:
    canonical_metric = str(known_metric(metric) or metric or "").strip().lower()
    explicit = _contract_role_fieldnames(contract, "metrics", canonical_metric)
    fieldname = _find_column_fieldname(columns, explicit, numeric_required=True)
    if fieldname:
        return fieldname
    metric_norm = _norm(canonical_metric)
    for col in columns:
        fieldname = str(col.get("fieldname") or "").strip()
        label = str(col.get("label") or "").strip()
        if not fieldname or not _is_numeric_column(col):
            continue
        if metric_norm and (metric_norm in _norm(fieldname) or metric_norm in _norm(label)):
            return fieldname
    for col in columns:
        fieldname = str(col.get("fieldname") or "").strip()
        if fieldname and _is_numeric_column(col):
            return fieldname
    return ""


def _find_dimension_fieldname(columns: List[Dict[str, Any]], contract: Dict[str, Any], spec: Dict[str, Any]) -> str:
    for dim_name in _primary_dimension_names(contract, spec):
        explicit = _contract_role_fieldnames(contract, "dimensions", dim_name)
        fieldname = _find_column_fieldname(columns, explicit, numeric_required=False)
        if fieldname:
            return fieldname
    for col in columns:
        fieldname = str(col.get("fieldname") or "").strip()
        if not fieldname or _is_numeric_column(col):
            continue
        return fieldname
    return ""


def _find_status_fieldname(columns: List[Dict[str, Any]]) -> str:
    return _find_column_fieldname(columns, ["status"], numeric_required=False)


def _find_due_date_fieldname(columns: List[Dict[str, Any]]) -> str:
    return _find_column_fieldname(columns, ["due_date", "due date"], numeric_required=False)


def _is_numeric_column(col: Dict[str, Any]) -> bool:
    fieldtype = str(col.get("fieldtype") or "").strip().lower()
    return fieldtype in {"currency", "float", "int", "number", "percent"}


def _compare(lhs: float, comparator: str, rhs: float) -> bool:
    if comparator == "gt":
        return lhs > rhs
    if comparator == "gte":
        return lhs >= rhs
    if comparator == "lt":
        return lhs < rhs
    if comparator == "lte":
        return lhs <= rhs
    return False


def _is_aggregate_dimension_value(value: Any, aggregate_values: Sequence[str]) -> bool:
    text = _norm(value)
    if not text:
        return False
    for candidate in aggregate_values:
        if text == _norm(candidate):
            return True
    return text in {"all", "total", "grand total"} or text.startswith("all ")


def _exclude_aggregate_rows(rows: List[Dict[str, Any]], *, dimension_fn: str, aggregate_values: Sequence[str]) -> List[Dict[str, Any]]:
    if not dimension_fn or not aggregate_values:
        return rows
    non_aggregate = [r for r in rows if not _is_aggregate_dimension_value((r or {}).get(dimension_fn), aggregate_values)]
    return non_aggregate or rows


def _parse_date(value: Any) -> Optional[date]:
    text = str(value or "").strip().replace("/", "-")
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.date()
        except Exception:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except Exception:
        return None


def _row_is_overdue(
    row: Dict[str, Any],
    *,
    status_fn: str,
    due_date_fn: str,
    today: date,
) -> bool:
    status_text = _norm((row or {}).get(status_fn)) if status_fn else ""
    if "overdue" in status_text or "past due" in status_text:
        return True
    if status_text in {"paid", "cancelled", "canceled", "closed"}:
        return False
    if due_date_fn:
        due_date = _parse_date((row or {}).get(due_date_fn))
        if due_date is not None and due_date < today:
            return True
    return False


def _project_rows(rows: List[Dict[str, Any]], fieldnames: Sequence[str]) -> List[Dict[str, Any]]:
    keep = [str(x).strip() for x in fieldnames if str(x or "").strip()]
    return [{fn: row.get(fn) for fn in keep} for row in rows if isinstance(row, dict)]


def apply_threshold_exception_filter(
    *,
    payload: Dict[str, Any],
    business_spec: Dict[str, Any],
    today_fn: Callable[[], date] = date.today,
) -> Dict[str, Any]:
    out = dict(payload or {})
    if str(out.get("type") or "").strip().lower() != "report_table":
        return out

    spec = business_spec if isinstance(business_spec, dict) else {}
    if str(spec.get("task_class") or "").strip().lower() != "threshold_exception_list":
        return out

    rule = _threshold_rule(spec)
    metric = str(rule.get("metric") or "").strip().lower()
    comparator = str(rule.get("comparator") or "").strip().lower()
    threshold_value = rule.get("value")
    exception_terms: Set[str] = set(rule.get("exception_terms") or set())
    if not metric or (not comparator) or (threshold_value is None):
        return out

    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    visible_columns = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
    visible_rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
    source_table = out.get("_source_table") if isinstance(out.get("_source_table"), dict) else {}
    source_columns = [c for c in list(source_table.get("columns") or []) if isinstance(c, dict)] or visible_columns
    source_rows = [r for r in list(source_table.get("rows") or []) if isinstance(r, dict)] or visible_rows
    if not source_columns or not source_rows:
        return out

    contract = _safe_contract(out)
    metric_fn = _find_metric_fieldname(source_columns, contract, metric)
    if not metric_fn:
        return out
    dimension_fn = _find_dimension_fieldname(source_columns, contract, spec)
    aggregate_values = _aggregate_dimension_values(contract)
    filtered_source_rows = _exclude_aggregate_rows(source_rows, dimension_fn=dimension_fn, aggregate_values=aggregate_values)

    if "overdue" in exception_terms:
        status_fn = _find_status_fieldname(source_columns)
        due_date_fn = _find_due_date_fieldname(source_columns)
        if status_fn or due_date_fn:
            today = today_fn()
            filtered_source_rows = [
                row for row in filtered_source_rows
                if _row_is_overdue(row, status_fn=status_fn, due_date_fn=due_date_fn, today=today)
            ]

    filtered_source_rows = [
        row
        for row in filtered_source_rows
        if _compare(_to_float((row or {}).get(metric_fn)), comparator, float(threshold_value))
    ]

    visible_fieldnames = [str(c.get("fieldname") or "").strip() for c in visible_columns if str(c.get("fieldname") or "").strip()]
    filtered_visible_rows = _project_rows(filtered_source_rows, visible_fieldnames) if visible_fieldnames else filtered_source_rows

    out_table = dict(table)
    out_table["rows"] = filtered_visible_rows
    out["table"] = out_table
    if source_columns:
        out["_source_table"] = {
            "columns": [dict(c) for c in source_columns],
            "rows": [dict(r) for r in filtered_source_rows],
        }
    out["_threshold_rule_applied"] = True
    out["_threshold_rule"] = {
        "metric": metric,
        "comparator": comparator,
        "value": float(threshold_value),
        "value_present": True,
        "exception_terms": sorted(exception_terms),
    }
    primary_dimensions = _primary_dimension_names(contract, spec)
    out["_threshold_primary_dimension"] = str(primary_dimensions[0] if primary_dimensions else "").strip().lower()
    out["_threshold_metric"] = metric
    out["_threshold_metric_fieldname"] = metric_fn
    out["_threshold_comparator"] = comparator
    return out
