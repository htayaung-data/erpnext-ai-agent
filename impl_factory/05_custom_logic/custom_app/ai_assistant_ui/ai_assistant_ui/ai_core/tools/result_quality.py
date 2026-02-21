from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

_NUMERIC_FIELDTYPES = {"currency", "float", "int", "percent", "number"}
_STOP_TOKENS = {"by", "the", "a", "an", "for", "of", "to", "in", "on", "and", "with"}
_METRIC_QTY_TOKENS = {"qty", "quantity", "count", "units", "unit"}
_METRIC_VALUE_TOKENS = {
    "amount",
    "value",
    "total",
    "revenue",
    "sales",
    "balance",
    "outstanding",
    "price",
    "cost",
    "payable",
    "receivable",
}
_METRIC_AGGREGATE_TOKENS = {"total", "value", "amount", "balance", "outstanding"}
_METRIC_DIRECTION_CONFLICTS = (
    ("sold", "received"),
    ("sold", "required"),
    ("sold", "pending"),
    ("received", "required"),
    ("received", "pending"),
    ("in", "out"),
    ("credit", "debit"),
    ("payable", "receivable"),
    ("purchase", "sales"),
)
_METRIC_STATE_TOKENS = {
    "sold",
    "received",
    "required",
    "pending",
    "transferred",
    "delivered",
    "billed",
    "ordered",
    "returned",
    "issued",
    "consumed",
    "produced",
}
_TOKEN_ALIAS_CANONICAL = {
    "amount": "amount",
    "value": "amount",
    "total": "amount",
    "revenue": "amount",
    "sales": "amount",
    "sale": "amount",
    "net": "amount",
    "balance": "amount",
    "outstanding": "amount",
    "payable": "amount",
    "receivable": "amount",
    "cost": "amount",
    "price": "amount",
    "qty": "quantity",
    "quantity": "quantity",
    "quantities": "quantity",
    "count": "quantity",
    "unit": "quantity",
    "units": "quantity",
    "volume": "quantity",
    "customer": "customer",
    "customers": "customer",
    "client": "customer",
    "clients": "customer",
    "party": "customer",
    "parties": "customer",
    "item": "item",
    "items": "item",
    "product": "item",
    "products": "item",
    "sku": "item",
    "material": "item",
    "materials": "item",
    "warehouse": "warehouse",
    "warehouses": "warehouse",
    "store": "warehouse",
    "stores": "warehouse",
    "location": "warehouse",
    "locations": "warehouse",
    "company": "company",
    "companies": "company",
    "business": "company",
    "organization": "company",
    "organisation": "company",
    "employee": "employee",
    "employees": "employee",
    "staff": "employee",
}
_MONTH_TOKENS = {
    "jan",
    "january",
    "feb",
    "february",
    "mar",
    "march",
    "apr",
    "april",
    "may",
    "jun",
    "june",
    "jul",
    "july",
    "aug",
    "august",
    "sep",
    "sept",
    "september",
    "oct",
    "october",
    "nov",
    "november",
    "dec",
    "december",
}


def _is_empty(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str):
        return not v.strip()
    if isinstance(v, (list, tuple, set, dict)):
        return len(v) == 0
    return False


def _as_number(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _norm_text(s: Any) -> str:
    t = str(s or "").strip().lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())


def _tokens(s: Any) -> List[str]:
    out: List[str] = []
    seen = set()
    for tok in _norm_text(s).split():
        if len(tok) <= 1:
            continue
        if tok in _STOP_TOKENS:
            continue
        if tok not in seen:
            seen.add(tok)
            out.append(tok)
        canon = _TOKEN_ALIAS_CANONICAL.get(tok)
        if canon and canon not in seen:
            seen.add(canon)
            out.append(canon)
    return out


def _col_aliases(col: Dict[str, Any]) -> List[str]:
    vals = []
    fn = str(col.get("fieldname") or "").strip()
    lb = str(col.get("label") or "").strip()
    if fn:
        vals.append(fn)
    if lb:
        vals.append(lb)
    return vals


def _is_numeric_column(col: Dict[str, Any], rows: List[Dict[str, Any]]) -> bool:
    ftype = str(col.get("fieldtype") or "").strip().lower()
    if ftype in _NUMERIC_FIELDTYPES:
        return True
    fn = col.get("fieldname")
    if not fn:
        return False
    sample = [r.get(fn) for r in rows[:30] if isinstance(r, dict) and fn in r]
    if not sample:
        return False
    non_empty = [v for v in sample if not _is_empty(v)]
    if not non_empty:
        return False
    numeric = [v for v in non_empty if _as_number(v) is not None]
    return len(numeric) * 2 >= len(non_empty)


def _score_hint_to_column(col: Dict[str, Any], hint: str) -> float:
    h_norm = _norm_text(hint)
    if not h_norm:
        return 0.0

    best = 0.0
    h_toks = set(_tokens(h_norm))
    for alias in _col_aliases(col):
        a_norm = _norm_text(alias)
        if not a_norm:
            continue
        if a_norm == h_norm:
            return 1.0
        if h_norm in a_norm or a_norm in h_norm:
            best = max(best, 0.85)
        a_toks = set(_tokens(a_norm))
        if h_toks and a_toks:
            overlap = len(h_toks & a_toks)
            if overlap:
                best = max(best, overlap / float(max(len(h_toks), len(a_toks))))
    return best


def _column_tokens(col: Dict[str, Any]) -> List[str]:
    toks: List[str] = []
    for alias in _col_aliases(col):
        toks.extend(_tokens(alias))
    # de-dup preserving order
    out: List[str] = []
    seen = set()
    for t in toks:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _numeric_columns(columns: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for col in columns:
        fn = str(col.get("fieldname") or "").strip()
        if not fn:
            continue
        if _is_numeric_column(col, rows):
            out.append(col)
    return out


def _has_any(tokens: List[str], vocab: set) -> bool:
    return any(t in vocab for t in tokens)


def _looks_like_time_bucket(col: Dict[str, Any]) -> bool:
    toks = _column_tokens(col)
    if not toks:
        return False
    if any(t in _MONTH_TOKENS for t in toks):
        return True
    for alias in _col_aliases(col):
        a = str(alias or "").strip().lower()
        if not a:
            continue
        if re.search(r"\b(19|20)\d{2}\b", a):
            return True
        if re.search(r"\bq[1-4]\b", a):
            return True
        if re.search(r"\b\d{4}[-/]\d{1,2}\b", a):
            return True
    return False


def _metric_semantic_conflict(metric_hint: str, col: Dict[str, Any]) -> bool:
    hint_toks = _tokens(metric_hint)
    col_toks = _column_tokens(col)
    if not hint_toks or not col_toks:
        return False

    hint_qty = _has_any(hint_toks, _METRIC_QTY_TOKENS)
    hint_value = _has_any(hint_toks, _METRIC_VALUE_TOKENS)
    col_qty = _has_any(col_toks, _METRIC_QTY_TOKENS)
    col_value = _has_any(col_toks, _METRIC_VALUE_TOKENS)

    # Quantity-vs-value mismatch is a hard semantic conflict.
    if (hint_qty and col_value) or (hint_value and col_qty):
        return True

    # Explicit directional or domain conflicts.
    hint_set = set(hint_toks)
    col_set = set(col_toks)
    for a, b in _METRIC_DIRECTION_CONFLICTS:
        if (a in hint_set and b in col_set) or (b in hint_set and a in col_set):
            return True
    return False


def _fallback_metric_column(
    columns: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    metric_hint: str,
) -> Optional[str]:
    if not metric_hint:
        return None
    numeric_cols = _numeric_columns(columns, rows)
    if len(numeric_cols) == 1:
        col = numeric_cols[0]
        if _metric_semantic_conflict(metric_hint, col):
            return None
        hint_toks_single = _tokens(metric_hint)
        if _has_any(hint_toks_single, _METRIC_QTY_TOKENS):
            hint_state_single = {t for t in hint_toks_single if t in _METRIC_STATE_TOKENS}
            if hint_state_single:
                col_state_single = {t for t in _column_tokens(col) if t in _METRIC_STATE_TOKENS}
                if not (hint_state_single & col_state_single):
                    return None
        return str(col.get("fieldname") or "").strip() or None
    if len(numeric_cols) < 2:
        return None

    hint_toks = _tokens(metric_hint)
    hint_qty = _has_any(hint_toks, _METRIC_QTY_TOKENS)
    hint_value = _has_any(hint_toks, _METRIC_VALUE_TOKENS)
    hint_state = {t for t in hint_toks if t in _METRIC_STATE_TOKENS}

    ranked: List[Tuple[float, str]] = []
    for col in numeric_cols:
        fn = str(col.get("fieldname") or "").strip()
        if not fn:
            continue
        if _metric_semantic_conflict(metric_hint, col):
            continue
        col_toks = _column_tokens(col)
        col_state = {t for t in col_toks if t in _METRIC_STATE_TOKENS}
        if hint_qty and hint_state and not (hint_state & col_state):
            continue
        score = _score_hint_to_column(col, metric_hint)
        if hint_qty and _has_any(col_toks, _METRIC_QTY_TOKENS):
            score += 0.35
        if hint_value and _has_any(col_toks, _METRIC_VALUE_TOKENS):
            score += 0.35
        if _has_any(col_toks, _METRIC_AGGREGATE_TOKENS):
            score += 0.20
        if _looks_like_time_bucket(col):
            score -= 0.40
        ranked.append((score, fn))

    if not ranked:
        return None
    ranked.sort(key=lambda x: x[0], reverse=True)
    top_score, top_fn = ranked[0]
    second_score = ranked[1][0] if len(ranked) > 1 else float("-inf")
    if top_score < 0.35:
        return None
    if (top_score - second_score) < 0.20:
        return None
    return top_fn


def _resolve_metric_column(
    columns: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    metric_hint: str,
) -> Tuple[Optional[str], bool]:
    direct = _match_column(columns, rows, metric_hint, prefer_numeric=True, min_score=0.6) if metric_hint else None
    if direct:
        col = _find_column_by_fieldname(columns, direct)
        if isinstance(col, dict) and (not _metric_semantic_conflict(metric_hint, col)):
            return direct, False
    fallback = _fallback_metric_column(columns, rows, metric_hint)
    return fallback, bool(fallback)


def _match_column(
    columns: List[Dict[str, Any]],
    rows: List[Dict[str, Any]],
    hint: str,
    *,
    prefer_numeric: Optional[bool] = None,
    min_score: float = 0.01,
) -> Optional[str]:
    if not hint:
        return None
    ranked: List[Tuple[float, str]] = []
    for col in columns:
        fn = str(col.get("fieldname") or "").strip()
        if not fn:
            continue
        if prefer_numeric is True and not _is_numeric_column(col, rows):
            continue
        if prefer_numeric is False and _is_numeric_column(col, rows):
            continue
        score = _score_hint_to_column(col, hint)
        if score >= float(min_score):
            ranked.append((score, fn))
    if not ranked:
        return None
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked[0][1]


def _find_column_by_fieldname(columns: List[Dict[str, Any]], fieldname: str) -> Optional[Dict[str, Any]]:
    for c in columns:
        if str(c.get("fieldname") or "").strip() == str(fieldname or "").strip():
            return c
    return None


def _is_desc_sorted(rows: List[Dict[str, Any]], fieldname: str) -> bool:
    nums: List[float] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        n = _as_number(r.get(fieldname))
        if n is None:
            continue
        nums.append(n)
    if len(nums) <= 1:
        return True
    for i in range(1, len(nums)):
        if nums[i] > nums[i - 1]:
            return False
    return True


def _fail(check_id: str, message: str, *, severity: str = "repairable") -> Dict[str, Any]:
    return {"id": check_id, "severity": severity, "message": message}


def _as_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def evaluate_result_quality(
    *,
    business_request_spec: Dict[str, Any],
    result_payload: Dict[str, Any],
    applied_filters: Dict[str, Any],
) -> Dict[str, Any]:
    spec = business_request_spec if isinstance(business_request_spec, dict) else {}
    output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    output_mode = str(output_contract.get("mode") or "detail").strip().lower()
    task_type = str(spec.get("task_type") or "detail").strip().lower()
    top_n = max(0, min(_as_int(spec.get("top_n"), 0), 500))
    metric_hint = str(spec.get("metric") or "").strip()
    group_hints = [str(x).strip() for x in (spec.get("group_by") or []) if str(x).strip()]
    if not group_hints and task_type == "ranking":
        subj = str(spec.get("subject") or "").strip()
        if subj:
            group_hints = [subj]

    failed: List[Dict[str, Any]] = []

    spec_filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    for k, v in spec_filters.items():
        if _is_empty(v):
            continue
        if _is_empty((applied_filters or {}).get(k)):
            failed.append(_fail("required_filter_missing", f"Requested filter `{k}` was not applied.", severity="hard"))

    time_scope = spec.get("time_scope") if isinstance(spec.get("time_scope"), dict) else {}
    time_mode = str(time_scope.get("mode") or "none").strip().lower()
    if time_mode in ("as_of", "range"):
        has_date_filter = any(("date" in str(k).lower()) and (not _is_empty(v)) for k, v in (applied_filters or {}).items())
        if not has_date_filter:
            failed.append(_fail("time_scope_missing", "Requested time scope was not applied in filters.", severity="hard"))

    typ = str((result_payload or {}).get("type") or "").strip().lower()
    if typ != "report_table":
        if output_mode == "kpi" and typ == "text":
            pass
        else:
            failed.append(_fail("output_mode_mismatch", f"Expected `{output_mode}` output but received `{typ or 'unknown'}`.", severity="hard"))
        return {
            "verdict": "HARD_FAIL" if failed else "PASS",
            "failed_checks": failed,
            "context": {"output_mode": output_mode},
        }

    table = result_payload.get("table") if isinstance(result_payload.get("table"), dict) else {}
    columns = table.get("columns") if isinstance(table.get("columns"), list) else []
    rows = table.get("rows") if isinstance(table.get("rows"), list) else []
    row_dicts = [r for r in rows if isinstance(r, dict)]

    strict_metric_required = bool(metric_hint) and (
        output_mode in ("kpi", "top_n")
        or task_type in ("kpi", "ranking")
        or top_n > 0
    )
    strict_dimension_required = bool(group_hints) and (
        output_mode in ("top_n",)
        or task_type in ("ranking",)
        or top_n > 0
    )

    metric_col, metric_col_fallback = _resolve_metric_column(columns, row_dicts, metric_hint)
    if strict_metric_required and not metric_col:
        failed.append(_fail("metric_alignment_mismatch", f"Could not align requested metric `{metric_hint}` with returned columns."))

    if strict_dimension_required:
        dim_ok = False
        for g in group_hints:
            if _match_column(columns, row_dicts, g, prefer_numeric=False):
                dim_ok = True
                break
        if not dim_ok:
            failed.append(_fail("dimension_alignment_mismatch", "Could not align requested grouping/dimension with returned columns."))

    if top_n > 0:
        if len(row_dicts) > top_n:
            failed.append(_fail("top_n_not_applied", f"Expected at most {top_n} rows but got {len(row_dicts)}."))
        if metric_col and not _is_desc_sorted(row_dicts, metric_col):
            failed.append(_fail("top_n_order_mismatch", f"Rows are not sorted descending by `{metric_col}`."))

    if output_mode == "kpi":
        if len(row_dicts) > 1:
            failed.append(_fail("kpi_shape_mismatch", f"KPI output expected <=1 row but got {len(row_dicts)}."))

    minimal_cols = [str(x).strip() for x in (output_contract.get("minimal_columns") or []) if str(x).strip()]
    if output_mode in ("kpi", "top_n") and minimal_cols:
        missing_min: List[str] = []
        metric_hint_norm = _norm_text(metric_hint)
        for c in minimal_cols:
            matched = _match_column(columns, row_dicts, c, min_score=0.5)
            if matched:
                continue
            # If metric alignment succeeded via deterministic single-numeric fallback,
            # treat the requested metric minimal column as satisfied.
            if metric_col_fallback and metric_col and metric_hint_norm and _norm_text(c) == metric_hint_norm:
                continue
            missing_min.append(c)
        if missing_min:
            failed.append(_fail("minimal_columns_missing", f"Missing expected columns: {', '.join(missing_min)}."))

    hard = [c for c in failed if c.get("severity") == "hard"]
    if hard:
        verdict = "HARD_FAIL"
    elif failed:
        verdict = "REPAIRABLE_FAIL"
    else:
        verdict = "PASS"

    return {
        "verdict": verdict,
        "failed_checks": failed,
        "context": {
            "metric_column": metric_col,
            "metric_column_fallback": bool(metric_col_fallback),
            "output_mode": output_mode,
            "top_n": top_n,
            "row_count": len(row_dicts),
        },
    }


def _project_columns(payload: Dict[str, Any], wanted_fieldnames: List[str]) -> Dict[str, Any]:
    out = dict(payload or {})
    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    cols = table.get("columns") if isinstance(table.get("columns"), list) else []
    rows = table.get("rows") if isinstance(table.get("rows"), list) else []

    keep = [fn for fn in wanted_fieldnames if _find_column_by_fieldname(cols, fn)]
    if not keep:
        return payload

    out_cols = [c for c in cols if str(c.get("fieldname") or "") in keep]
    out_rows: List[Dict[str, Any]] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        out_rows.append({k: r.get(k) for k in keep})
    out["table"] = {"columns": out_cols, "rows": out_rows}
    return out


def try_local_quality_repair(
    *,
    business_request_spec: Dict[str, Any],
    result_payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[str]]:
    if not isinstance(result_payload, dict) or str(result_payload.get("type") or "").strip().lower() != "report_table":
        return result_payload, []

    spec = business_request_spec if isinstance(business_request_spec, dict) else {}
    output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    output_mode = str(output_contract.get("mode") or "detail").strip().lower()
    top_n = max(0, min(_as_int(spec.get("top_n"), 0), 500))
    metric_hint = str(spec.get("metric") or "").strip()
    minimal_cols = [str(x).strip() for x in (output_contract.get("minimal_columns") or []) if str(x).strip()]

    out = dict(result_payload)
    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    cols = table.get("columns") if isinstance(table.get("columns"), list) else []
    rows = [r for r in (table.get("rows") if isinstance(table.get("rows"), list) else []) if isinstance(r, dict)]
    steps: List[str] = []

    metric_col, _metric_col_fallback = _resolve_metric_column(cols, rows, metric_hint)

    if output_mode in ("top_n",) and top_n > 0:
        if metric_col:
            rows.sort(key=lambda r: _as_number(r.get(metric_col)) if _as_number(r.get(metric_col)) is not None else float("-inf"), reverse=True)
            steps.append(f"sorted_desc_by:{metric_col}")
        if len(rows) > top_n:
            rows = rows[:top_n]
            steps.append(f"limit_top_n:{top_n}")
        out["table"] = {"columns": cols, "rows": rows}

    if output_mode == "kpi":
        if metric_col:
            total = 0.0
            used = 0
            for r in rows:
                n = _as_number(r.get(metric_col))
                if n is None:
                    continue
                total += n
                used += 1
            if used > 0:
                out["table"] = {
                    "columns": [
                        _find_column_by_fieldname(cols, metric_col)
                        or {"label": metric_col, "fieldname": metric_col, "fieldtype": "Float"}
                    ],
                    "rows": [{metric_col: total}],
                }
                out["title"] = out.get("title") or "KPI"
                steps.append(f"kpi_total:{metric_col}")

    if minimal_cols:
        keep_fns: List[str] = []
        source_cols = out.get("table", {}).get("columns") if isinstance(out.get("table"), dict) else cols
        source_rows = out.get("table", {}).get("rows") if isinstance(out.get("table"), dict) else rows
        if not isinstance(source_cols, list):
            source_cols = cols
        if not isinstance(source_rows, list):
            source_rows = rows
        for hint in minimal_cols:
            fn = _match_column(source_cols, [r for r in source_rows if isinstance(r, dict)], hint, min_score=0.5)
            if fn and fn not in keep_fns:
                keep_fns.append(fn)
        if keep_fns:
            out = _project_columns(out, keep_fns)
            steps.append("project_minimal_columns")

    return out, steps


def format_quality_feedback(gate: Dict[str, Any]) -> str:
    failed = gate.get("failed_checks") if isinstance(gate.get("failed_checks"), list) else []
    if not failed:
        return "No failed checks."
    parts: List[str] = []
    for f in failed[:6]:
        cid = str(f.get("id") or "check")
        msg = str(f.get("message") or "").strip()
        if msg:
            parts.append(f"{cid}: {msg}")
        else:
            parts.append(cid)
    return " | ".join(parts)
