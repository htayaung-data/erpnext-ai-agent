from __future__ import annotations

import re
import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ----------------------------
# Data classes
# ----------------------------

@dataclass
class NormalizedRequirements:
    required_filter_names: List[str]
    filters_definition: List[Dict[str, Any]]
    raw_type: str = "unknown"


@dataclass
class NormalizedReport:
    columns: List[Dict[str, Any]]
    rows: List[Dict[str, Any]]
    chart: Optional[Dict[str, Any]] = None
    report_summary: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None
    raw_type: str = "unknown"


# Backward-compatible alias (some modules may import this name)
NormalizedReportOutput = NormalizedReport


# ----------------------------
# Helpers: JSON-safe conversion
# ----------------------------

def _is_date_like(x: Any) -> bool:
    try:
        return isinstance(x, (dt.date, dt.datetime))
    except Exception:
        return False


def make_json_safe(obj: Any) -> Any:
    """
    Deep conversion to JSON-safe primitives.
    Ensures report outputs can be serialized/stored safely (dates, decimals, sets, etc.).
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    if _is_date_like(obj):
        try:
            return obj.isoformat()
        except Exception:
            return str(obj)

    try:
        import decimal
        if isinstance(obj, decimal.Decimal):
            return float(obj)
    except Exception:
        pass

    # frappe._dict behaves like dict; normal dicts too
    if isinstance(obj, dict):
        return {str(k): make_json_safe(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [make_json_safe(v) for v in obj]

    return str(obj)


def _unwrap_fac_payload(raw: Any) -> Tuple[Any, str]:
    """
    FAC output envelopes vary. Unwrap common patterns:
      {success, result:{...}}
      {message:{...}}
    """
    payload = raw
    tag = "raw"

    if isinstance(payload, dict):
        if isinstance(payload.get("result"), dict):
            payload = payload["result"]
            tag = "result"
        if isinstance(payload.get("message"), dict):
            payload = payload["message"]
            tag = "message"

    return payload, tag


# ----------------------------
# Helpers: columns/rows normalization
# ----------------------------

def _slug_fieldname(label: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", (label or "").strip().lower())
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "col"


def _normalize_columns(cols: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(cols, list):
        return out

    for c in cols:
        if isinstance(c, dict):
            d = {str(k): make_json_safe(v) for k, v in c.items()}
            if not d.get("fieldname"):
                label = str(d.get("label") or d.get("name") or "Column")
                d["fieldname"] = _slug_fieldname(label)
                d.setdefault("label", label)
            out.append(d)
            continue

        if isinstance(c, str):
            # ERPNext sometimes uses "Label:Type/Options"
            label = c.split(":")[0].strip() if ":" in c else c.strip()
            fn = _slug_fieldname(label)
            out.append({"label": label, "fieldname": fn, "fieldtype": None})
            continue

    return out


def _rows_from_any(cols: List[Dict[str, Any]], rows_raw: Any) -> List[Dict[str, Any]]:
    if not isinstance(rows_raw, list):
        return []

    # Ideal: list of dicts
    if rows_raw and isinstance(rows_raw[0], dict):
        return [make_json_safe(r) for r in rows_raw if isinstance(r, dict)]

    # Common: list of lists/tuples -> map to columns
    if rows_raw and isinstance(rows_raw[0], (list, tuple)):
        fns = [c.get("fieldname") for c in cols]
        out: List[Dict[str, Any]] = []
        for r in rows_raw:
            if not isinstance(r, (list, tuple)):
                continue
            d: Dict[str, Any] = {}
            for i, v in enumerate(r):
                fn = fns[i] if i < len(fns) and fns[i] else f"col_{i+1}"
                d[str(fn)] = make_json_safe(v)
            out.append(d)
        return out

    # Fallback: stringify
    return [{"value": make_json_safe(r)} for r in rows_raw]


# ----------------------------
# Public API expected by other modules
# ----------------------------

def normalize_requirements_output(raw: Any) -> NormalizedRequirements:
    payload, tag = _unwrap_fac_payload(raw)

    required: List[str] = []
    filters_def: List[Dict[str, Any]] = []

    if isinstance(payload, dict):
        f = payload.get("filters") or payload.get("filters_definition") or payload.get("filter_list")
        if isinstance(f, list):
            for it in f:
                if isinstance(it, dict):
                    filters_def.append({str(k): make_json_safe(v) for k, v in it.items()})

        r = payload.get("required_filters") or payload.get("required") or payload.get("required_filter_names")
        if isinstance(r, list):
            required = [str(x) for x in r if x]

    # If required list missing, infer from filter definitions (reqd/mandatory)
    if not required and filters_def:
        for d in filters_def:
            fn = d.get("fieldname")
            if not fn:
                continue
            reqd = d.get("reqd")
            if reqd is None:
                reqd = d.get("mandatory")
            try:
                if int(reqd or 0) == 1:
                    required.append(str(fn))
            except Exception:
                pass

    # de-dup
    seen = set()
    req2 = []
    for x in required:
        if x in seen:
            continue
        seen.add(x)
        req2.append(x)

    return NormalizedRequirements(
        required_filter_names=req2,
        filters_definition=filters_def,
        raw_type=f"requirements:{tag}",
    )


def normalize_report_output(raw: Any) -> NormalizedReport:
    payload, tag = _unwrap_fac_payload(raw)

    if not isinstance(payload, dict):
        return NormalizedReport(columns=[], rows=[], message=str(payload), raw_type=f"report:{tag}:non_dict")

    cols_raw = payload.get("columns") or payload.get("cols")
    rows_raw = payload.get("result") or payload.get("rows") or payload.get("data")

    cols = _normalize_columns(cols_raw)
    rows = _rows_from_any(cols, rows_raw)

    chart = payload.get("chart")
    chart = make_json_safe(chart) if isinstance(chart, (dict, list)) else None

    report_summary = payload.get("report_summary")
    report_summary = make_json_safe(report_summary) if isinstance(report_summary, (dict, list)) else None

    msg = payload.get("message")
    msg = str(msg) if msg else None

    return NormalizedReport(
        columns=cols,
        rows=rows,
        chart=chart if isinstance(chart, dict) else None,
        report_summary=report_summary if isinstance(report_summary, list) else None,
        message=msg,
        raw_type=f"report:{tag}",
    )


# ----------------------------
# Backward-compatible utilities expected by report_tools.py
# ----------------------------

def pick_total_field(columns: List[Dict[str, Any]]) -> Optional[str]:
    """
    Heuristic: pick a "total" numeric field from columns.
    Used by summary / top-N style tools.
    """
    if not columns:
        return None

    # strong candidates
    preferred = {
        "total", "grand_total", "base_grand_total",
        "outstanding_amount", "outstanding",
        "balance", "amount", "net_total",
    }

    for c in columns:
        fn = (c.get("fieldname") or "").strip()
        if fn.lower() in preferred:
            return fn

    # any field containing 'total'
    for c in columns:
        fn = (c.get("fieldname") or "").strip()
        if "total" in fn.lower():
            return fn

    # fallback: last column fieldname
    return (columns[-1].get("fieldname") or "").strip() or None


def _to_float(x: Any) -> float:
    try:
        if x is None:
            return 0.0
        if isinstance(x, (int, float)):
            return float(x)
        try:
            import decimal
            if isinstance(x, decimal.Decimal):
                return float(x)
        except Exception:
            pass
        s = str(x).replace(",", "").strip()
        return float(s) if s else 0.0
    except Exception:
        return 0.0


def sum_numeric_row(row: Dict[str, Any], columns: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> float:
    """
    Sum numeric values in a row (often month buckets + total).
    Signature is tolerant to different call styles.
    """
    if not isinstance(row, dict):
        return 0.0

    ex = set([e for e in (exclude or []) if e])
    total = 0.0

    if columns:
        for k in columns:
            if not k or k in ex:
                continue
            total += _to_float(row.get(k))
        return total

    for k, v in row.items():
        if k in ex:
            continue
        total += _to_float(v)

    return total
