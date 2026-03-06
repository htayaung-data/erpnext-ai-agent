from __future__ import annotations

from typing import Any, Dict, List, Sequence

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


def _contribution_rule(spec: Dict[str, Any]) -> Dict[str, Any]:
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    rule = filters.get("_contribution_rule") if isinstance(filters.get("_contribution_rule"), dict) else {}
    metric = str(known_metric(rule.get("metric")) or rule.get("metric") or "").strip().lower()
    terms = [str(x).strip().lower() for x in list(rule.get("contribution_terms") or []) if str(x).strip()]
    return {
        "metric": metric,
        "basis": str(rule.get("basis") or "of_total").strip().lower() or "of_total",
        "contribution_terms": terms,
    }


def _contract_role_fieldnames(contract: Dict[str, Any], role_type: str, role_name: str) -> List[str]:
    presentation = contract.get("presentation") if isinstance(contract.get("presentation"), dict) else {}
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


def _is_numeric_column(col: Dict[str, Any]) -> bool:
    fieldtype = str(col.get("fieldtype") or "").strip().lower()
    return fieldtype in {"currency", "float", "int", "number", "percent"}


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
        if fieldname and (not _is_numeric_column(col)):
            return fieldname
    return ""


def _is_aggregate_dimension_value(value: Any, aggregate_values: Sequence[str]) -> bool:
    text = _norm(value)
    if not text:
        return False
    for candidate in aggregate_values:
        if text == _norm(candidate):
            return True
    return text in {"all", "total", "grand total"} or text.startswith("all ")


def _exclude_aggregate_rows(rows: List[Dict[str, Any]], *, dimension_fn: str, aggregate_values: Sequence[str]) -> List[Dict[str, Any]]:
    if not dimension_fn:
        return rows
    if not aggregate_values:
        aggregate_values = ["All"]
    non_aggregate = [
        row
        for row in rows
        if not _is_aggregate_dimension_value((row or {}).get(dimension_fn), aggregate_values)
    ]
    return non_aggregate or rows


def _ensure_contribution_column(columns: List[Dict[str, Any]], fieldname: str) -> List[Dict[str, Any]]:
    out = [dict(c) for c in columns if isinstance(c, dict)]
    if any(str(c.get("fieldname") or "").strip() == fieldname for c in out):
        return out
    out.append({"fieldname": fieldname, "label": "Contribution Share", "fieldtype": "Data"})
    return out


def _format_share(value: float) -> str:
    rounded = round(float(value), 1)
    if abs(rounded - round(rounded)) < 0.05:
        return f"{int(round(rounded))}%"
    return f"{rounded:.1f}%"


def apply_contribution_share(
    *,
    payload: Dict[str, Any],
    business_spec: Dict[str, Any],
) -> Dict[str, Any]:
    out = dict(payload or {})
    if str(out.get("type") or "").strip().lower() != "report_table":
        return out

    spec = business_spec if isinstance(business_spec, dict) else {}
    if str(spec.get("task_class") or "").strip().lower() != "contribution_share":
        return out

    rule = _contribution_rule(spec)
    metric = str(rule.get("metric") or "").strip().lower()
    if not metric:
        return out

    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    visible_columns = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
    visible_rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
    source_table = out.get("_source_table") if isinstance(out.get("_source_table"), dict) else {}
    source_columns = [c for c in list(source_table.get("columns") or []) if isinstance(c, dict)] or visible_columns
    source_rows = [r for r in list(source_table.get("rows") or []) if isinstance(r, dict)] or visible_rows
    if not source_columns or not source_rows:
        return out

    report_name = str(out.get("report_name") or out.get("title") or "").strip()
    contract = report_semantics_contract(report_name)
    metric_fn = _find_metric_fieldname(source_columns, contract, metric)
    dimension_fn = _find_dimension_fieldname(source_columns, contract, spec)
    if not metric_fn or not dimension_fn:
        return out

    aggregate_values = _aggregate_dimension_values(contract)
    source_rows = _exclude_aggregate_rows(source_rows, dimension_fn=dimension_fn, aggregate_values=aggregate_values)
    visible_rows = _exclude_aggregate_rows(visible_rows or source_rows, dimension_fn=dimension_fn, aggregate_values=aggregate_values)

    total_value = sum(_to_float(row.get(metric_fn)) for row in source_rows if isinstance(row, dict))
    if total_value <= 0.0:
        return out

    contribution_fn = "contribution_share"
    source_columns = _ensure_contribution_column(source_columns, contribution_fn)
    visible_columns = _ensure_contribution_column(visible_columns or source_columns, contribution_fn)

    def _annotate(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        annotated: List[Dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            enriched = dict(row)
            share_pct = (_to_float(row.get(metric_fn)) / total_value) * 100.0
            enriched[contribution_fn] = _format_share(share_pct)
            annotated.append(enriched)
        return annotated

    source_rows = _annotate(source_rows)
    visible_rows = _annotate(visible_rows)

    out["table"] = {
        "columns": visible_columns,
        "rows": visible_rows,
    }
    out["_source_table"] = {
        "columns": source_columns,
        "rows": source_rows,
    }
    out["_contribution_rule_applied"] = True
    out["_contribution_rule"] = {
        "metric": metric,
        "basis": str(rule.get("basis") or "of_total").strip().lower() or "of_total",
        "contribution_terms": [str(x).strip().lower() for x in list(rule.get("contribution_terms") or []) if str(x).strip()],
    }
    out["_contribution_primary_dimension"] = str(_primary_dimension_names(contract, spec)[0] if _primary_dimension_names(contract, spec) else "").strip().lower()
    out["_contribution_metric"] = metric
    out["_contribution_metric_fieldname"] = metric_fn
    out["_contribution_share_fieldname"] = contribution_fn
    out["_contribution_total_value"] = round(float(total_value), 6)
    return out
