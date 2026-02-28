from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from ai_assistant_ui.ai_core.ontology_normalization import (
    known_dimension,
    known_metric,
    semantic_aliases,
)

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

    for c in group_by_cols:
        _append_unique(c)
    for c in dimension_cols:
        _append_unique(c)
    _append_unique(metric_col)
    for c in contract_cols:
        _append_unique(c)

    return merged[:12]


def _match_column_indexes(columns: List[Dict[str, Any]], rows: List[Dict[str, Any]], wanted: List[str]) -> List[Tuple[int, str]]:
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
        best_idx = None
        best_score = -10**9
        for idx, c in enumerate(columns):
            if idx in used:
                continue
            fn = _norm(c.get("fieldname"))
            lb = _norm(c.get("label"))
            txt = f"{fn} {lb}".strip()
            score = -10**9
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


def _project_table(payload: Dict[str, Any], wanted: List[str]) -> Dict[str, Any]:
    out = dict(payload or {})
    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
    rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
    if not cols or not rows or not wanted:
        return out

    bindings = _match_column_indexes(cols, rows, wanted)
    if not bindings:
        return out

    projected_cols: List[Dict[str, Any]] = []
    for i, desired in bindings:
        base_col = cols[i] if isinstance(cols[i], dict) else {}
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


def _detect_metric_column(columns: List[Dict[str, Any]], rows: List[Dict[str, Any]], spec: Dict[str, Any]) -> str:
    metric = str(spec.get("metric") or "").strip()
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

    task_class = str(spec.get("task_class") or "").strip().lower()
    if task_class == "list_latest_records":
        temporal_fn = _detect_temporal_column(cols)
        if temporal_fn:
            rows_sorted = sorted(rows, key=lambda r: _temporal_sort_value((r or {}).get(temporal_fn)), reverse=True)
        else:
            rows_sorted = list(rows)
    else:
        metric_fn = _detect_metric_column(cols, rows, spec)
        if metric_fn:
            rows_sorted = sorted(rows, key=lambda r: _to_float((r or {}).get(metric_fn)), reverse=True)
        else:
            rows_sorted = list(rows)
    out["table"] = {"columns": cols, "rows": rows_sorted[:n]}
    return out


def _apply_kpi(payload: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload or {})
    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
    rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
    if not cols or not rows:
        return out

    metric_fn = _detect_metric_column(cols, rows, spec)
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


def shape_response(*, payload: Dict[str, Any], business_spec: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload or {})
    if str(out.get("type") or "").strip().lower() != "report_table":
        return out
    if bool(out.get("_direct_document_lookup")):
        # Keep deterministic document-detail payload intact.
        return out

    spec = business_spec if isinstance(business_spec, dict) else {}
    mode = str(((spec.get("output_contract") or {}).get("mode") or "detail")).strip().lower()

    out = _apply_document_row_filter(out, spec)

    wanted = _minimal_columns(spec)
    if wanted:
        out = _project_table(out, wanted)

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
