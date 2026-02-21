from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

import frappe


@dataclass
class NormalizedReport:
    columns: List[Dict[str, Any]]  # each: {label, fieldname, fieldtype?, options?}
    rows: List[Dict[str, Any]]     # dict rows keyed by fieldname
    raw_type: str                  # debug: "dict", "list", "tuple", ...


def _as_number(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, bool):
        return None
    if isinstance(v, str):
        s = v.strip().replace(",", "")
        if s == "":
            return None
        try:
            return float(s)
        except Exception:
            return None
    return None


def _parse_column_string(col: str) -> Dict[str, Any]:
    """
    Frappe report columns often look like:
      "Customer:Link/Customer:200"
      "Total:Currency:120"
      "Jan 2026:Currency:120"
    We'll extract label + best-effort type/options.
    """
    parts = col.split(":")
    label = parts[0].strip() if parts else col.strip()

    fieldtype = None
    options = None

    if len(parts) >= 2:
        type_part = parts[1].strip()
        # Link/Customer pattern
        if type_part.startswith("Link/"):
            fieldtype = "Link"
            options = type_part.split("/", 1)[1] if "/" in type_part else None
        else:
            fieldtype = type_part or None

    fieldname = frappe.scrub(label) or "col"
    out: Dict[str, Any] = {"label": label, "fieldname": fieldname}
    if fieldtype:
        out["fieldtype"] = fieldtype
    if options:
        out["options"] = options
    return out


def _normalize_columns(columns_raw: Any) -> List[Dict[str, Any]]:
    if not columns_raw:
        return []

    cols: List[Dict[str, Any]] = []
    if isinstance(columns_raw, (list, tuple)):
        for c in columns_raw:
            if isinstance(c, dict):
                label = c.get("label") or c.get("name") or c.get("fieldname") or "Column"
                fieldname = c.get("fieldname") or frappe.scrub(str(label)) or "col"
                col = {"label": label, "fieldname": fieldname}
                # keep common metadata if present
                for k in ("fieldtype", "options", "width", "type"):
                    if k in c and c.get(k) is not None:
                        # normalize "type" -> "fieldtype"
                        if k == "type" and "fieldtype" not in col:
                            col["fieldtype"] = c.get(k)
                        else:
                            col[k] = c.get(k)
                cols.append(col)
            elif isinstance(c, str):
                cols.append(_parse_column_string(c))
            else:
                cols.append({"label": str(c), "fieldname": frappe.scrub(str(c)) or "col"})
        return cols

    # single string
    if isinstance(columns_raw, str):
        return [_parse_column_string(columns_raw)]

    # unknown
    return [{"label": "Column", "fieldname": "column"}]


def _rows_to_dicts(rows_raw: Any, columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not rows_raw:
        return []

    # If already list of dicts, map keys to fieldnames best-effort
    if isinstance(rows_raw, list) and rows_raw and all(isinstance(r, dict) for r in rows_raw):
        out: List[Dict[str, Any]] = []
        col_fieldnames = [c.get("fieldname") for c in columns if c.get("fieldname")]
        for r in rows_raw:
            rr: Dict[str, Any] = {}
            # keep original keys, but also try to align with known col fieldnames
            for k, v in r.items():
                rr[str(k)] = v
            # if columns are known but row uses labels, try to map
            for c in columns:
                label = c.get("label")
                fieldname = c.get("fieldname")
                if label in r and fieldname and fieldname not in rr:
                    rr[fieldname] = r.get(label)
            # ensure columns exist as keys if present
            for fn in col_fieldnames:
                if fn and fn not in rr:
                    rr[fn] = rr.get(fn)
            out.append(rr)
        return out

    # If rows are list-of-lists, align by index with columns
    if isinstance(rows_raw, (list, tuple)) and rows_raw and all(isinstance(r, (list, tuple)) for r in rows_raw):
        out2: List[Dict[str, Any]] = []
        fieldnames = [c.get("fieldname") or f"col_{i}" for i, c in enumerate(columns)]
        for r in rows_raw:
            rr = {}
            for i, v in enumerate(r):
                fn = fieldnames[i] if i < len(fieldnames) else f"col_{i}"
                rr[fn] = v
            out2.append(rr)
        return out2

    # If it's a plain list, treat each element as a single-column row
    if isinstance(rows_raw, list):
        fn = columns[0]["fieldname"] if columns else "value"
        return [{fn: v} for v in rows_raw]

    return []


def normalize_fac_report(raw: Any) -> NormalizedReport:
    """
    FAC generate_report may return:
      - dict: {"columns": ..., "result": ...}
      - dict: {"message": {"columns": ..., "result": ...}}
      - list/tuple: [columns, rows] or (columns, rows)
      - list containing a dict payload
    This function normalizes into (columns, rows-as-dicts).
    """
    raw_type = type(raw).__name__

    # Unwrap list-with-single-dict (some APIs do this)
    if isinstance(raw, list) and len(raw) == 1 and isinstance(raw[0], dict):
        raw = raw[0]
        raw_type = f"{raw_type}->dict"

    columns_raw = None
    rows_raw = None

    if isinstance(raw, dict):
        payload = raw
        # Some endpoints wrap the real payload in "message"
        if isinstance(payload.get("message"), dict):
            payload = payload["message"]

        columns_raw = payload.get("columns") or payload.get("column") or payload.get("fields")
        rows_raw = (
            payload.get("result")
            or payload.get("data")
            or payload.get("rows")
            or payload.get("values")
        )

    elif isinstance(raw, (list, tuple)):
        # Common shape: (columns, rows) or [columns, rows]
        if len(raw) >= 2 and isinstance(raw[0], (list, tuple)) and isinstance(raw[1], (list, tuple)):
            columns_raw, rows_raw = raw[0], raw[1]
        else:
            # Sometimes it's only rows with no columns.
            rows_raw = list(raw)

    # Normalize columns; if missing, infer generic columns from first row
    columns = _normalize_columns(columns_raw)

    if not columns and rows_raw:
        # infer from dict keys or list length
        if isinstance(rows_raw, list) and rows_raw:
            if isinstance(rows_raw[0], dict):
                columns = [{"label": k, "fieldname": frappe.scrub(k)} for k in rows_raw[0].keys()]
            elif isinstance(rows_raw[0], (list, tuple)):
                columns = [{"label": f"Column {i+1}", "fieldname": f"col_{i}"} for i in range(len(rows_raw[0]))]
            else:
                columns = [{"label": "Value", "fieldname": "value"}]

    rows = _rows_to_dicts(rows_raw, columns)

    return NormalizedReport(columns=columns, rows=rows, raw_type=raw_type)


def sum_numeric_fields(row: Dict[str, Any], exclude: Sequence[str] = ()) -> float:
    total = 0.0
    for k, v in row.items():
        if k in exclude:
            continue
        n = _as_number(v)
        if n is None:
            continue
        total += n
    return total
