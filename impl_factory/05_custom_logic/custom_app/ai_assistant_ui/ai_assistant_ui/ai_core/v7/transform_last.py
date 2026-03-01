from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ai_assistant_ui.ai_core.ontology_normalization import (
    known_dimension,
    known_metric,
    metric_column_aliases,
    semantic_aliases,
)


def _table(payload: Dict[str, Any]) -> Dict[str, Any]:
    return payload.get("table") if isinstance(payload.get("table"), dict) else {}


def _columns(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [c for c in list(_table(payload).get("columns") or []) if isinstance(c, dict)]


def _rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [r for r in list(_table(payload).get("rows") or []) if isinstance(r, dict)]


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


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", " ")


def _is_numeric_col(col: Dict[str, Any], rows: List[Dict[str, Any]]) -> bool:
    ft = str(col.get("fieldtype") or "").strip().lower()
    if ft in {"currency", "float", "int", "number", "percent"}:
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


def _match_score(text: str, alias: str) -> int:
    txt = _norm(text)
    a = _norm(alias)
    if not txt or not a:
        return -10**9
    if txt == a:
        return 100
    if a in txt.split():
        return 80
    if a in txt:
        return 60
    return -10**9


def _metric_column(spec: Dict[str, Any], cols: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> Optional[str]:
    metric_raw = str(spec.get("metric") or "").strip()
    aliases: List[str] = []
    seen = set()
    for source in (
        [metric_raw],
        list(metric_column_aliases(metric_raw) or []),
        list(semantic_aliases(metric_raw, exclude_generic_metric_terms=True) or []),
    ):
        for value in source:
            s = _norm(value)
            if (not s) or (s in seen):
                continue
            seen.add(s)
            aliases.append(s)

    best_fn: Optional[str] = None
    best_score = -10**9
    for c in cols:
        fn = str(c.get("fieldname") or "").strip()
        if not fn or not _is_numeric_col(c, rows):
            continue
        text = f"{_norm(fn)} {_norm(c.get('label'))}".strip()
        score = -10**9
        for alias in aliases:
            score = max(score, _match_score(text, alias))
        if score > best_score:
            best_score = score
            best_fn = fn

    if best_fn is not None and best_score > -10**9:
        return best_fn

    for c in cols:
        fn = str(c.get("fieldname") or "").strip().lower()
        if any(k in fn for k in ("amount", "total", "revenue", "qty", "quantity", "balance")):
            return str(c.get("fieldname") or "").strip()
    if cols:
        return str(cols[-1].get("fieldname") or "").strip()
    return None


def _dim_column(spec: Dict[str, Any], cols: List[Dict[str, Any]]) -> Optional[str]:
    group_by = [str(x).strip().lower() for x in list(spec.get("group_by") or []) if str(x).strip()]
    for gb in group_by:
        for c in cols:
            fn = str(c.get("fieldname") or "").strip().lower()
            lb = str(c.get("label") or "").strip().lower()
            if gb == fn or gb == lb or gb in fn or gb in lb:
                return str(c.get("fieldname") or "").strip()
    if cols:
        return str(cols[0].get("fieldname") or "").strip()
    return None


def _column_satisfies_wanted(col: Dict[str, Any], wanted: str) -> bool:
    text = f"{_norm(col.get('fieldname'))} {_norm(col.get('label'))}".strip()
    aliases: List[str] = []
    metric = str(known_metric(wanted) or "").strip()
    dim = str(known_dimension(wanted) or "").strip()
    wanted_norm = _norm(wanted)
    wanted_tokens = set(wanted_norm.split())
    canonical_norm = _norm(metric or dim)
    if metric:
        aliases.extend(metric_column_aliases(metric))
        aliases.extend(semantic_aliases(metric, exclude_generic_metric_terms=True))
    elif dim:
        aliases.extend(semantic_aliases(dim))
    else:
        aliases.extend(semantic_aliases(wanted))
    aliases.append(str(wanted or ""))
    for alias in aliases:
        alias_norm = _norm(alias)
        alias_tokens = set(alias_norm.split())
        if wanted_norm and canonical_norm and wanted_norm != canonical_norm:
            if alias_tokens and alias_tokens < wanted_tokens:
                continue
        if _match_score(text, alias) > -10**9:
            return True
    return False


def _needs_source_promotion(spec: Dict[str, Any], cols: List[Dict[str, Any]]) -> bool:
    output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    wanted: List[str] = []
    seen = set()
    for source in (
        list(spec.get("group_by") or []),
        list(spec.get("dimensions") or []),
        [spec.get("metric")],
        list(output_contract.get("minimal_columns") or []),
    ):
        for value in source:
            s = str(value or "").strip()
            if (not s) or (s.lower() in seen):
                continue
            seen.add(s.lower())
            wanted.append(s)
    if not wanted:
        return False
    for target in wanted:
        if not any(_column_satisfies_wanted(c, target) for c in cols):
            return True
    return False


def apply_transform_last(*, payload: Dict[str, Any], business_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic transform-last operations for report-table payloads.
    """
    out = dict(payload or {})
    spec = business_spec if isinstance(business_spec, dict) else {}
    if str(out.get("type") or "").strip().lower() != "report_table":
        return out

    ambiguities = [str(x).strip().lower() for x in list(spec.get("ambiguities") or []) if str(x).strip()]
    scale_million = any(a == "transform_scale:million" for a in ambiguities)
    is_transform_intent = str(spec.get("intent") or "").strip().upper() == "TRANSFORM_LAST"
    if (not is_transform_intent) and (not scale_million):
        return out

    source_table = out.get("_source_table") if isinstance(out.get("_source_table"), dict) else {}
    cols = _columns(out)
    rows = _rows(out)
    if source_table and _needs_source_promotion(spec, cols):
        out["table"] = {
            "columns": [c for c in list(source_table.get("columns") or []) if isinstance(c, dict)],
            "rows": [r for r in list(source_table.get("rows") or []) if isinstance(r, dict)],
        }
        cols = _columns(out)
        rows = _rows(out)
    if not rows:
        return out

    output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    mode = str(output_contract.get("mode") or "").strip().lower()
    try:
        top_n = int(spec.get("top_n") or 0)
    except Exception:
        top_n = 0

    metric_fn = _metric_column(spec, cols, rows)
    dim_fn = _dim_column(spec, cols)
    sort_desc = any(a == "transform_sort:desc" for a in ambiguities)
    sort_asc = any(a == "transform_sort:asc" for a in ambiguities)
    has_explicit_metric = bool(str(spec.get("metric") or "").strip())
    aggregation = str(spec.get("aggregation") or "").strip().lower()
    metric_text = str(spec.get("metric") or "").strip().lower()
    explicit_total_request = (
        aggregation in {"sum", "avg", "average", "count", "min", "max"}
        or any(k in metric_text for k in ("total", "sum", "count", "number", "average", "avg"))
    )
    already_scaled = str(out.get("_scaled_unit") or "").strip().lower() == "million"
    stored_output_mode = str(out.get("_output_mode") or "").strip().lower()
    pure_scale_followup = scale_million and (not sort_desc) and (not sort_asc)
    pure_scale_repeat = already_scaled and scale_million and (not sort_desc) and (not sort_asc)
    if pure_scale_repeat and stored_output_mode == "top_n":
        return out
    if already_scaled and scale_million and (not sort_desc) and (not sort_asc) and (not explicit_total_request):
        if stored_output_mode in {"top_n", "detail"}:
            return out
    minimal_columns = [str(x).strip() for x in list(output_contract.get("minimal_columns") or []) if str(x or "").strip()]
    has_dimension_request = bool(list(spec.get("group_by") or []) or list(spec.get("dimensions") or []) or minimal_columns)
    explicit_aggregate_only = bool(
        aggregation in {"sum", "avg", "average", "count", "min", "max"}
        and top_n <= 0
        and (not has_dimension_request)
    )
    if pure_scale_followup and (not explicit_aggregate_only) and stored_output_mode in {"top_n", "detail"}:
        mode = stored_output_mode
    if (mode == "kpi") and scale_million and (len(rows) > 1) and (not explicit_total_request):
        mode = "detail"

    if mode == "top_n" and top_n > 0 and metric_fn:
        rows_n = list(rows)
        if has_explicit_metric or sort_desc or sort_asc:
            rows_n = sorted(rows_n, key=lambda r: _to_float(r.get(metric_fn)), reverse=not sort_asc)
        out["table"] = {"columns": cols, "rows": rows_n[:top_n]}
        out["_transform_last_applied"] = "top_n"
        rows = _rows(out)

    if mode == "kpi" and metric_fn:
        total = 0.0
        for r in rows:
            total += _to_float(r.get(metric_fn))
        out["table"] = {
            "columns": [
                {"fieldname": "metric", "label": "Metric"},
                {"fieldname": "value", "label": "Value"},
            ],
            "rows": [{"metric": metric_fn, "value": total}],
        }
        out["_transform_last_applied"] = "kpi_total"
        rows = _rows(out)

    # detail/default transform: keep only dimension+metric when both are known.
    if (mode not in ("kpi", "top_n")) and dim_fn and metric_fn and dim_fn != metric_fn:
        picked_cols = []
        for c in cols:
            fn = str(c.get("fieldname") or "").strip()
            if fn in (dim_fn, metric_fn):
                picked_cols.append(c)
        if picked_cols:
            out["table"] = {
                "columns": picked_cols,
                "rows": [{dim_fn: r.get(dim_fn), metric_fn: r.get(metric_fn)} for r in rows],
            }
            out["_transform_last_applied"] = "detail_project"

    # Optional global sort on metric for transformed table.
    cols = _columns(out)
    rows = _rows(out)
    metric_fn2 = _metric_column(spec, cols, rows)
    if rows and metric_fn2 and (sort_desc or sort_asc):
        rows2 = sorted(rows, key=lambda r: _to_float((r or {}).get(metric_fn2)), reverse=sort_desc)
        out["table"] = {"columns": cols, "rows": rows2}
        out["_transform_last_applied"] = str(out.get("_transform_last_applied") or "sort")

    # Scale numeric measures to million when requested.
    if scale_million:
        if str(out.get("_scaled_unit") or "").strip().lower() == "million":
            return out
        cols = _columns(out)
        rows = _rows(out)
        if rows:
            numeric_fns = []
            for c in cols:
                fn = str(c.get("fieldname") or "").strip()
                if not fn:
                    continue
                ft = str(c.get("fieldtype") or "").strip().lower()
                if ft in ("currency", "float", "int", "number", "percent"):
                    numeric_fns.append(fn)
                    continue
                # heuristic fallback
                if any(k in fn.lower() for k in ("amount", "revenue", "value", "total", "outstanding", "balance", "qty", "quantity")):
                    numeric_fns.append(fn)
            if not numeric_fns:
                if metric_fn2:
                    numeric_fns = [metric_fn2]
            scaled_rows = []
            for r in rows:
                row = dict(r)
                for fn in numeric_fns:
                    if fn in row:
                        row[fn] = _to_float(row.get(fn)) / 1_000_000.0
                scaled_rows.append(row)
            out["table"] = {"columns": cols, "rows": scaled_rows}
            out["_transform_last_applied"] = str(out.get("_transform_last_applied") or "scale_million")
            out["_scaled_unit"] = "million"
    return out


def make_transform_tool_message(*, tool: str, mode: str, payload: Dict[str, Any]) -> str:
    obj = payload if isinstance(payload, dict) else {}
    return json.dumps(
        {
            "type": "v7_transform_last",
            "phase": "phase5",
            "mode": str(mode or "").strip(),
            "tool": str(tool or "").strip(),
            "applied": str(obj.get("_transform_last_applied") or ""),
        },
        ensure_ascii=False,
        default=str,
    )
