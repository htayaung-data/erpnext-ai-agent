from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from ai_assistant_ui.ai_core.ontology_normalization import (
    known_dimension,
    known_metric,
    metric_column_aliases,
    semantic_aliases,
)
from ai_assistant_ui.ai_core.v7.capability_registry import report_semantics_contract

_DOC_ID_REGEX = re.compile(r"\b[A-Z]{2,}-[A-Z0-9]+-\d{4}-\d+\b")


def _norm(text: Any) -> str:
    return str(text or "").strip().lower().replace("_", " ")


def _to_float(v: Any) -> float:
    try:
        if v is None:
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).replace(",", "").strip()
        return float(s) if s else 0.0
    except Exception:
        return 0.0


def _is_numeric_col(col: Dict[str, Any], rows: List[Dict[str, Any]]) -> bool:
    ft = str(col.get("fieldtype") or "").strip().lower()
    if ft in {"currency", "float", "int", "percent", "number"}:
        return True
    fn = str(col.get("fieldname") or "").strip()
    if not fn:
        return False
    sample = []
    for r in rows[:30]:
        if isinstance(r, dict) and fn in r:
            sample.append(r.get(fn))
    non_empty = [v for v in sample if str(v or "").strip() != ""]
    if not non_empty:
        return False
    numeric = 0
    for v in non_empty:
        try:
            float(str(v).replace(",", "").strip())
            numeric += 1
        except Exception:
            pass
    return numeric * 2 >= len(non_empty)


def _minimal_columns(spec: Dict[str, Any]) -> List[str]:
    oc = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    contract_cols = [str(x).strip() for x in list(oc.get("minimal_columns") or []) if str(x).strip()]
    group_by_cols = [str(x).strip() for x in list(spec.get("group_by") or []) if str(x).strip()]
    dimension_cols = [str(x).strip() for x in list(spec.get("dimensions") or []) if str(x).strip()]
    metric_col = str(spec.get("metric") or "").strip()
    ambiguities = [str(x).strip().lower() for x in list(spec.get("ambiguities") or []) if str(x or "").strip()]
    projection_only = bool("transform_projection:only" in ambiguities)

    # Semantic ordering for detail outputs:
    # 1) requested dimensions (group_by/dimensions), 2) requested metric, 3) remaining contract hints.
    merged: List[str] = []
    seen = set()

    def _append_unique(value: str) -> None:
        s = str(value or "").strip()
        if not s:
            return
        key = s.lower()
        if key in seen:
            return
        seen.add(key)
        merged.append(s)

    if projection_only and contract_cols:
        for c in contract_cols:
            _append_unique(c)
        return merged[:12]
    for c in group_by_cols:
        _append_unique(c)
    for c in dimension_cols:
        _append_unique(c)
    _append_unique(metric_col)
    for c in contract_cols:
        _append_unique(c)

    return merged[:12]


def _report_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    report_name = str(payload.get("report_name") or payload.get("title") or "").strip()
    return report_semantics_contract(report_name)


def _contract_role_fieldnames(report_contract: Dict[str, Any], role_type: str, role_name: str) -> List[str]:
    contract = report_contract if isinstance(report_contract, dict) else {}
    presentation = contract.get("presentation") if isinstance(contract.get("presentation"), dict) else {}
    column_roles = presentation.get("column_roles") if isinstance(presentation.get("column_roles"), dict) else {}
    role_map = column_roles.get(role_type) if isinstance(column_roles.get(role_type), dict) else {}
    values = role_map.get(role_name) if isinstance(role_map.get(role_name), list) else []
    return [str(x).strip() for x in values if str(x or "").strip()]


def _aggregate_dimension_values(report_contract: Dict[str, Any]) -> List[str]:
    contract = report_contract if isinstance(report_contract, dict) else {}
    presentation = contract.get("presentation") if isinstance(contract.get("presentation"), dict) else {}
    values = presentation.get("aggregate_dimension_values") if isinstance(presentation.get("aggregate_dimension_values"), list) else []
    return [str(x).strip() for x in values if str(x or "").strip()]


def _match_column_indexes(
    columns: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    wanted: List[str],
    report_contract: Dict[str, Any] | None = None,
) -> List[Tuple[int, str]]:
    if not columns:
        return []
    wanted_pairs = [(str(w).strip(), _norm(w)) for w in wanted if _norm(w)]
    if not wanted_pairs:
        return []

    alias_expansions: Dict[str, List[str]] = {}
    for _, w in wanted_pairs:
        alias_expansions[w] = [_norm(a) for a in semantic_aliases(w, exclude_generic_metric_terms=True) if _norm(a)]

    chosen: List[Tuple[int, str]] = []
    used = set()
    for raw_wanted, w in wanted_pairs:
        aliases = alias_expansions.get(w) or [w]
        metric = known_metric(w)
        dim = known_dimension(w)
        raw_wanted_norm = _norm(raw_wanted)
        wanted_tokens = set(raw_wanted_norm.split())
        canonical_norm = _norm(metric or dim)
        column_aliases = [_norm(a) for a in metric_column_aliases(metric) if _norm(a)] if metric else []
        explicit_fieldnames = []
        if metric:
            explicit_fieldnames = [str(x).strip().lower() for x in _contract_role_fieldnames(report_contract or {}, "metrics", metric)]
        elif dim:
            if raw_wanted_norm == canonical_norm:
                explicit_fieldnames = [str(x).strip().lower() for x in _contract_role_fieldnames(report_contract or {}, "dimensions", dim)]
        filtered_aliases: List[str] = []
        for alias in aliases:
            alias_norm = _norm(alias)
            alias_tokens = set(alias_norm.split())
            if raw_wanted_norm and canonical_norm and raw_wanted_norm != canonical_norm:
                if alias_tokens and alias_tokens < wanted_tokens:
                    continue
            filtered_aliases.append(alias_norm)
        aliases = filtered_aliases or [w]
        best_idx = None
        best_score = -10**9
        for idx, c in enumerate(columns):
            if idx in used:
                continue
            fn = _norm(c.get("fieldname"))
            lb = _norm(c.get("label"))
            txt = f"{fn} {lb}".strip()
            score = -10**9
            if explicit_fieldnames and fn in explicit_fieldnames:
                score = 140 if metric else 130
            for a in aliases:
                if not a:
                    continue
                curr = -10**9
                if (a == fn) or (a == lb):
                    curr = 90
                elif re.search(rf"(?<!\\w){re.escape(a)}(?!\\w)", txt):
                    curr = 70
                elif len(a) >= 5 and (a in txt):
                    curr = 50
                if curr > score:
                    score = curr
            if metric and score < 0 and _is_numeric_col(c, rows):
                fallback_score = -10**9
                for alias in column_aliases:
                    if not alias:
                        continue
                    curr = -10**9
                    if (alias == fn) or (alias == lb):
                        curr = 42
                    elif re.search(rf"(?<!\\w){re.escape(alias)}(?!\\w)", txt):
                        curr = 36
                    elif len(alias) >= 5 and (alias in txt):
                        curr = 30
                    if curr > fallback_score:
                        fallback_score = curr
                if fallback_score > score:
                    score = fallback_score
            if score < 0:
                continue
            is_numeric = _is_numeric_col(c, rows)
            if metric:
                if not is_numeric:
                    continue
                score += 18
            if dim:
                score += 8 if (not is_numeric) else -4
            if score > best_score:
                best_score = score
                best_idx = idx
        if best_idx is not None:
            chosen.append((best_idx, raw_wanted))
            used.add(best_idx)

    return chosen


def _project_table(payload: Dict[str, Any], wanted: List[str], report_contract: Dict[str, Any] | None = None) -> Dict[str, Any]:
    out = dict(payload or {})
    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
    rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
    if not cols or not rows or not wanted:
        return out

    bindings = _match_column_indexes(cols, rows, wanted, report_contract)
    if not bindings:
        return out

    projected_cols: List[Dict[str, Any]] = []
    seen_fieldnames = set()
    for i, desired in bindings:
        base_col = cols[i] if isinstance(cols[i], dict) else {}
        fieldname = str(base_col.get("fieldname") or "").strip().lower()
        if fieldname and fieldname in seen_fieldnames:
            continue
        if fieldname:
            seen_fieldnames.add(fieldname)
        new_col = dict(base_col)
        desired = str(desired or "").strip()
        if desired:
            new_col["label"] = desired.replace("_", " ").title()
        projected_cols.append(new_col)
    projected_rows: List[Dict[str, Any]] = []
    for r in rows:
        nr: Dict[str, Any] = {}
        for c in projected_cols:
            fn = str(c.get("fieldname") or "").strip()
            if fn:
                nr[fn] = r.get(fn)
        projected_rows.append(nr)

    out["table"] = {"columns": projected_cols, "rows": projected_rows}
    return out


def _detect_metric_column(
    columns: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    spec: Dict[str, Any],
    report_contract: Dict[str, Any] | None = None,
) -> str:
    metric = str(spec.get("metric") or "").strip()
    canonical_metric_name = str(known_metric(metric) or "").strip()
    explicit_fieldnames = [
        str(x).strip().lower()
        for x in _contract_role_fieldnames(report_contract or {}, "metrics", canonical_metric_name)
    ] if canonical_metric_name else []
    for c in columns:
        fn = str(c.get("fieldname") or "").strip()
        if explicit_fieldnames and fn.lower() in explicit_fieldnames:
            return fn
    if metric:
        for c in columns:
            fn = str(c.get("fieldname") or "").strip()
            lb = str(c.get("label") or "").strip()
            if _norm(metric) in _norm(f"{fn} {lb}"):
                return fn
    for c in columns:
        if _is_numeric_col(c, rows):
            fn = str(c.get("fieldname") or "").strip()
            if fn:
                return fn
    return ""


def _requested_dimension_names(spec: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in list(spec.get("group_by") or []) + list(spec.get("dimensions") or []):
        value = str(raw or "").strip()
        if not value:
            continue
        dim = str(known_dimension(value) or value).strip().lower()
        if (not dim) or (dim in seen):
            continue
        seen.add(dim)
        out.append(dim)
    return out


def _detect_requested_dimension_column(
    columns: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    spec: Dict[str, Any],
    report_contract: Dict[str, Any] | None = None,
) -> str:
    requested = _requested_dimension_names(spec)
    if not requested:
        return ""
    bindings = _match_column_indexes(columns, rows, requested, report_contract)
    for idx, _ in bindings:
        fn = str((columns[idx] or {}).get("fieldname") or "").strip()
        if fn:
            return fn
    return ""


def _is_aggregate_dimension_value(value: Any, aggregate_values: List[str] | None = None) -> bool:
    txt = _norm(value)
    if not txt:
        return False
    for candidate in list(aggregate_values or []):
        cand = _norm(candidate)
        if cand and txt == cand:
            return True
    return txt in {"all", "total", "grand total"} or txt.startswith("all ")


def _aggregate_rows_by_dimension(
    *,
    columns: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    dimension_fn: str,
    metric_fn: str,
    aggregate_dimension_values: List[str] | None = None,
) -> List[Dict[str, Any]]:
    if not dimension_fn or not metric_fn:
        return rows
    if dimension_fn == metric_fn:
        return rows

    grouped: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    distinct_non_aggregate = set()
    aggregate_keys = set()

    for row in rows:
        key_value = str((row or {}).get(dimension_fn) or "").strip()
        if not key_value:
            continue
        key_norm = _norm(key_value)
        if key_norm not in grouped:
            grouped[key_norm] = {dimension_fn: key_value, metric_fn: 0.0}
            order.append(key_norm)
        grouped[key_norm][metric_fn] = _to_float(grouped[key_norm].get(metric_fn)) + _to_float((row or {}).get(metric_fn))
        for col in columns:
            fn = str(col.get("fieldname") or "").strip()
            if not fn or fn == metric_fn:
                continue
            if fn == dimension_fn:
                grouped[key_norm][fn] = key_value
                continue
            current = grouped[key_norm].get(fn)
            candidate = (row or {}).get(fn)
            if current in (None, "", []) and candidate not in (None, "", []):
                grouped[key_norm][fn] = candidate
        if _is_aggregate_dimension_value(key_value, aggregate_dimension_values):
            aggregate_keys.add(key_norm)
        else:
            distinct_non_aggregate.add(key_norm)

    keys = [k for k in order if (k in grouped)]
    if distinct_non_aggregate:
        keys = [k for k in keys if k not in aggregate_keys]
    return [grouped[k] for k in keys]


def _sort_direction(spec: Dict[str, Any]) -> str:
    ambiguities = [str(x).strip().lower() for x in list(spec.get("ambiguities") or []) if str(x).strip()]
    if "transform_sort:asc" in ambiguities and "transform_sort:desc" not in ambiguities:
        return "asc"
    return "desc"


def _temporal_sort_value(value: Any) -> float:
    s = str(value or "").strip()
    if not s:
        return float("-inf")
    s_norm = s.replace("/", "-")
    # ISO-like values.
    try:
        if len(s_norm) == 10 and re.match(r"^\d{4}-\d{2}-\d{2}$", s_norm):
            return float(datetime.strptime(s_norm, "%Y-%m-%d").timestamp())
        if re.match(r"^\d{4}-\d{2}$", s_norm):
            return float(datetime.strptime(s_norm + "-01", "%Y-%m-%d").timestamp())
        if re.match(r"^\d{4}-W\d{2}$", s_norm):
            year = int(s_norm[0:4])
            week = int(s_norm[6:8])
            return float(datetime.fromisocalendar(year, week, 1).timestamp())
        # Tolerate full datetime string.
        return float(datetime.fromisoformat(s_norm.replace("Z", "+00:00")).timestamp())
    except Exception:
        return float("-inf")


def _detect_temporal_column(columns: List[Dict[str, Any]]) -> str:
    preferred: List[str] = []
    fallback: List[str] = []
    for c in columns:
        fn = str(c.get("fieldname") or "").strip()
        if not fn:
            continue
        ft = str(c.get("fieldtype") or "").strip().lower()
        lb = _norm(c.get("label"))
        txt = f"{_norm(fn)} {lb}".strip()
        if ft in {"date", "datetime"}:
            preferred.append(fn)
            continue
        if any(t in txt for t in ("date", "time", "week", "month", "quarter", "year")):
            fallback.append(fn)
    if preferred:
        return preferred[0]
    if fallback:
        return fallback[0]
    return ""


def _apply_top_n(payload: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload or {})
    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
    rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
    if not cols or not rows:
        return out

    try:
        n = max(0, int(spec.get("top_n") or 0))
    except Exception:
        n = 0
    if n <= 0:
        return out

    def _sorted_rows_for(columns: List[Dict[str, Any]], rows_in: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not columns or not rows_in:
            return []
        task_class = str(spec.get("task_class") or "").strip().lower()
        if task_class == "list_latest_records":
            temporal_fn = _detect_temporal_column(columns)
            if temporal_fn:
                return sorted(rows_in, key=lambda r: _temporal_sort_value((r or {}).get(temporal_fn)), reverse=True)
            return list(rows_in)

        report_contract = _report_contract(out)
        metric_fn = _detect_metric_column(columns, rows_in, spec, report_contract)
        dimension_fn = _detect_requested_dimension_column(columns, rows_in, spec, report_contract)
        ranked_rows = list(rows_in)
        if metric_fn and dimension_fn:
            ranked_rows = _aggregate_rows_by_dimension(
                columns=columns,
                rows=ranked_rows,
                dimension_fn=dimension_fn,
                metric_fn=metric_fn,
                aggregate_dimension_values=_aggregate_dimension_values(report_contract),
            )
        direction = _sort_direction(spec)
        if metric_fn:
            return sorted(ranked_rows, key=lambda r: _to_float((r or {}).get(metric_fn)), reverse=(direction != "asc"))
        return ranked_rows

    def _apply_payload_scale_to_rows(columns: List[Dict[str, Any]], rows_in: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if str(out.get("_scaled_unit") or "").strip().lower() != "million":
            return list(rows_in)
        if not columns or not rows_in:
            return list(rows_in)
        numeric_fns: List[str] = []
        for c in columns:
            fn = str(c.get("fieldname") or "").strip()
            if not fn:
                continue
            ft = str(c.get("fieldtype") or "").strip().lower()
            if ft in ("currency", "float", "int", "number", "percent"):
                numeric_fns.append(fn)
                continue
            if any(k in fn.lower() for k in ("amount", "revenue", "value", "total", "outstanding", "balance", "qty", "quantity")):
                numeric_fns.append(fn)
        scaled_rows: List[Dict[str, Any]] = []
        for r in rows_in:
            row = dict(r)
            for fn in numeric_fns:
                if fn in row:
                    row[fn] = _to_float(row.get(fn)) / 1_000_000.0
            scaled_rows.append(row)
        return scaled_rows

    rows_sorted = _sorted_rows_for(cols, rows)
    if len(rows_sorted) < n:
        source_table = out.get("_source_table") if isinstance(out.get("_source_table"), dict) else {}
        source_cols = [c for c in list(source_table.get("columns") or []) if isinstance(c, dict)]
        source_rows = [r for r in list(source_table.get("rows") or []) if isinstance(r, dict)]
        current_fieldnames = [str(c.get("fieldname") or "").strip() for c in cols if str(c.get("fieldname") or "").strip()]
        source_fieldnames = {str(c.get("fieldname") or "").strip() for c in source_cols if str(c.get("fieldname") or "").strip()}
        if source_cols and source_rows and current_fieldnames and all(fn in source_fieldnames for fn in current_fieldnames):
            projected_source_rows = [
                {fn: r.get(fn) for fn in current_fieldnames}
                for r in source_rows
                if isinstance(r, dict)
            ]
            projected_source_rows = _apply_payload_scale_to_rows(cols, projected_source_rows)
            source_sorted = _sorted_rows_for(cols, projected_source_rows)
            if len(source_sorted) >= len(rows_sorted):
                rows_sorted = source_sorted
    out["table"] = {"columns": cols, "rows": rows_sorted[:n]}
    return out


def _apply_kpi(payload: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload or {})
    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
    rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
    if not cols or not rows:
        return out

    metric_fn = _detect_metric_column(cols, rows, spec, _report_contract(out))
    metric_label = str(spec.get("metric") or metric_fn or "value").strip() or "value"
    total = 0.0
    if metric_fn:
        for r in rows:
            total += _to_float((r or {}).get(metric_fn))
    else:
        # Last resort: sum all numeric-looking cells.
        for r in rows:
            for v in (r or {}).values():
                total += _to_float(v)

    out["table"] = {
        "columns": [
            {"fieldname": "metric", "label": "Metric", "fieldtype": "Data"},
            {"fieldname": "value", "label": "Value", "fieldtype": "Float"},
        ],
        "rows": [{"metric": metric_label, "value": total}],
    }
    out["title"] = out.get("title") or "KPI"
    return out


def _extract_document_id(spec: Dict[str, Any]) -> str:
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    for _, v in filters.items():
        s = str(v or "").strip()
        if s and _DOC_ID_REGEX.search(s):
            return s
    return ""


def _apply_document_row_filter(payload: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = _extract_document_id(spec)
    if not doc_id:
        return payload

    out = dict(payload or {})
    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
    rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
    if not cols or not rows:
        return out

    filtered: List[Dict[str, Any]] = []
    for r in rows:
        if any(str(v or "").strip() == doc_id for v in (r or {}).values()):
            filtered.append(r)
    if filtered:
        out["table"] = {"columns": cols, "rows": filtered}
    return out


def _effective_output_mode(payload: Dict[str, Any], spec: Dict[str, Any]) -> str:
    oc = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    mode = str(oc.get("mode") or "detail").strip().lower()
    if str(spec.get("intent") or "").strip().upper() != "TRANSFORM_LAST":
        return mode

    stored_output_mode = str(payload.get("_output_mode") or "").strip().lower()
    if stored_output_mode not in {"top_n", "detail"}:
        return mode

    ambiguities = [str(x).strip().lower() for x in list(spec.get("ambiguities") or []) if str(x or "").strip()]
    scale_only_followup = bool(
        "transform_scale:million" in ambiguities
        and "transform_sort:asc" not in ambiguities
        and "transform_sort:desc" not in ambiguities
    )
    if not scale_only_followup:
        return mode

    minimal_columns = [str(x).strip() for x in list(oc.get("minimal_columns") or []) if str(x or "").strip()]
    has_dimension_request = bool(list(spec.get("group_by") or []) or list(spec.get("dimensions") or []) or minimal_columns)
    try:
        top_n = int(spec.get("top_n") or 0)
    except Exception:
        top_n = 0
    aggregation = str(spec.get("aggregation") or "").strip().lower()
    explicit_aggregate_only = bool(
        aggregation in {"sum", "avg", "average", "count", "min", "max"}
        and top_n <= 0
        and (not has_dimension_request)
    )
    if explicit_aggregate_only:
        return mode
    return stored_output_mode


def shape_response(*, payload: Dict[str, Any], business_spec: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload or {})
    if str(out.get("type") or "").strip().lower() != "report_table":
        return out
    if bool(out.get("_direct_document_lookup")):
        # Keep deterministic document-detail payload intact.
        return out

    spec = business_spec if isinstance(business_spec, dict) else {}
    mode = _effective_output_mode(out, spec)
    report_contract = _report_contract(out)

    out = _apply_document_row_filter(out, spec)

    wanted = _minimal_columns(spec)
    if wanted:
        out = _project_table(out, wanted, report_contract)

    if mode == "top_n":
        out = _apply_top_n(out, spec)
    elif mode == "kpi":
        out = _apply_kpi(out, spec)

    return out


def _looks_numeric_value(v: Any) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    s = str(v or "").strip()
    if not s:
        return False
    s2 = s.replace(",", "")
    try:
        float(s2)
        return True
    except Exception:
        return False


def format_numeric_values_for_display(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Apply comma separators and 2 decimals to numeric table values."""
    out = dict(payload or {})
    if str(out.get("type") or "").strip().lower() != "report_table":
        return out

    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
    rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
    if not cols or not rows:
        return out

    new_rows: List[Dict[str, Any]] = []
    for r in rows:
        nr = dict(r)
        for c in cols:
            fn = str(c.get("fieldname") or "").strip()
            if not fn or fn not in nr:
                continue
            val = nr.get(fn)
            if not _looks_numeric_value(val):
                continue
            num = _to_float(val)
            nr[fn] = f"{num:,.2f}"
        new_rows.append(nr)

    out["table"] = {"columns": cols, "rows": new_rows}
    return out


def make_response_shaper_tool_message(*, tool: str, mode: str, shaped_payload: Dict[str, Any]) -> str:
    obj = shaped_payload if isinstance(shaped_payload, dict) else {}
    return json.dumps(
        {
            "type": "v7_response_shaper",
            "phase": "phase5",
            "mode": str(mode or "").strip(),
            "tool": str(tool or "").strip(),
            "payload_type": str(obj.get("type") or ""),
            "report_name": str(obj.get("report_name") or ""),
            "title": str(obj.get("title") or ""),
        },
        ensure_ascii=False,
        default=str,
    )
