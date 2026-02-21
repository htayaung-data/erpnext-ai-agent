from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from ai_assistant_ui.ai_core.ontology_normalization import (
    DIMENSION_ALIAS_MAP,
    METRIC_ALIAS_MAP,
    canonical_dimension,
    canonical_metric,
)

VERDICT_PASS = "PASS"
VERDICT_REPAIRABLE_FAIL = "REPAIRABLE_FAIL"
VERDICT_HARD_FAIL = "HARD_FAIL"


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _table_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    table = payload.get("table") if isinstance(payload.get("table"), dict) else {}
    rows = table.get("rows") if isinstance(table.get("rows"), list) else []
    return [r for r in rows if isinstance(r, dict)]


def _table_columns(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    table = payload.get("table") if isinstance(payload.get("table"), dict) else {}
    cols = table.get("columns") if isinstance(table.get("columns"), list) else []
    return [c for c in cols if isinstance(c, dict)]


def _check_id(check_name: str, index: int) -> str:
    return f"QG{index:02d}_{check_name}"


def _norm_token(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", " ")


def _minimal_aliases(token: str) -> List[str]:
    t = _norm_token(token)
    if not t:
        return []
    aliases = {t}

    metric = canonical_metric(t)
    if metric and metric in METRIC_ALIAS_MAP:
        aliases.add(metric.replace("_", " "))
        for a in METRIC_ALIAS_MAP.get(metric, []):
            n = _norm_token(a)
            if n:
                aliases.add(n)

    dim = canonical_dimension(t)
    if dim and dim in DIMENSION_ALIAS_MAP:
        aliases.add(dim.replace("_", " "))
        for a in DIMENSION_ALIAS_MAP.get(dim, []):
            n = _norm_token(a)
            if n:
                aliases.add(n)

    # Common business-table variants.
    metric_alias_expansions = {
        "revenue": {"sales", "sales amount", "sales value"},
        "sold quantity": {"qty", "quantity", "stock qty"},
        "outstanding amount": {"amount due", "total amount due", "outstanding"},
        "stock balance": {"balance", "balance qty", "item balance"},
    }
    for base, extra in metric_alias_expansions.items():
        if _norm_token(base) in aliases:
            for a in extra:
                aliases.add(_norm_token(a))

    return sorted(a for a in aliases if a)


def _has_minimal_column(col_names: List[str], target: str) -> bool:
    names = [_norm_token(x) for x in (col_names or []) if _norm_token(x)]
    aliases = _minimal_aliases(target)
    if not names or not aliases:
        return False
    for n in names:
        for a in aliases:
            if (a == n) or (a in n) or (n in a):
                return True
    return False


def _is_numeric_col(col: Dict[str, Any], rows: List[Dict[str, Any]]) -> bool:
    ft = str(col.get("fieldtype") or "").strip().lower()
    if ft in {"currency", "float", "int", "percent", "number"}:
        return True
    fn = str(col.get("fieldname") or "").strip()
    if not fn:
        return False
    sample = []
    for r in rows[:30]:
        if isinstance(r, dict) and (fn in r):
            sample.append(r.get(fn))
    non_empty = [v for v in sample if str(v or "").strip() != ""]
    if not non_empty:
        return False
    numeric = 0
    for v in non_empty:
        s = str(v).replace(",", "").strip()
        try:
            float(s)
            numeric += 1
        except Exception:
            pass
    return numeric * 2 >= len(non_empty)


def _looks_like_time_col(col: Dict[str, Any]) -> bool:
    fn = _norm_token(col.get("fieldname"))
    lb = _norm_token(col.get("label"))
    text = f"{fn} {lb}".strip()
    time_tokens = ("date", "week", "month", "quarter", "year", "period")
    return any(t in text for t in time_tokens)


def _extract_document_id(filters: Dict[str, Any]) -> str:
    for _, v in (filters or {}).items():
        s = str(v or "").strip()
        if s and re.search(r"\b[A-Z]{2,}-[A-Z0-9]+-\d{4}-\d+\b", s):
            return s
    return ""


def _document_id_applied(doc_id: str, cols: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> bool:
    if not doc_id:
        return True
    # Generic row-wide check: all detected doc-like IDs in the result must match requested doc.
    values = set()
    for r in rows:
        if not isinstance(r, dict):
            continue
        for v in r.values():
            s = str(v or "").strip()
            if s and re.search(r"\b[A-Z]{2,}-[A-Z0-9]+-\d{4}-\d+\b", s):
                values.add(s)
    if not values:
        return False
    return len(values) == 1 and str(next(iter(values))).strip() == doc_id


def evaluate_quality_gate(
    *,
    business_spec: Dict[str, Any],
    resolved: Dict[str, Any],
    payload: Dict[str, Any],
    repeated_call_guard_triggered: bool,
) -> Dict[str, Any]:
    """
    Deterministic Phase-4 semantic/output gate.
    Returns PASS | REPAIRABLE_FAIL | HARD_FAIL with failed check IDs.
    """
    spec = business_spec if isinstance(business_spec, dict) else {}
    res = resolved if isinstance(resolved, dict) else {}
    out = payload if isinstance(payload, dict) else {"type": "text", "text": str(payload)}

    checks: List[Dict[str, Any]] = []
    hard_fail_ids: List[str] = []
    repairable_ids: List[str] = []

    def add_check(*, name: str, ok: bool, severity: str, detail: str) -> None:
        cid = _check_id(name, len(checks) + 1)
        checks.append({"id": cid, "check": name, "ok": bool(ok), "severity": severity, "detail": detail})
        if ok:
            return
        if severity == "hard":
            hard_fail_ids.append(cid)
        else:
            repairable_ids.append(cid)

    # Check 1: resolver blocker should not proceed as normal PASS.
    needs_clar = bool(res.get("needs_clarification"))
    add_check(
        name="resolver_blocker_absent",
        ok=not needs_clar,
        severity="hard",
        detail="resolver.needs_clarification must be false for direct execution",
    )

    # Check 2: anti-loop guard.
    add_check(
        name="loop_guard_not_triggered",
        ok=not bool(repeated_call_guard_triggered),
        severity="hard",
        detail="repeated-call guard must not trigger",
    )

    payload_type = str(out.get("type") or "").strip().lower()
    text_value = str(out.get("text") or "").strip().lower()
    is_no_data_text = payload_type == "text" and bool(text_value)
    add_check(
        name="payload_type_supported",
        ok=payload_type in {"text", "report_table"},
        severity="repairable",
        detail="payload.type must be text or report_table",
    )

    selected_report = str(res.get("selected_report") or "").strip()
    output_report = str(out.get("report_name") or "").strip()
    is_direct_doc_lookup = bool(out.get("_direct_document_lookup"))
    if payload_type == "report_table" and selected_report and (not is_direct_doc_lookup):
        add_check(
            name="selected_report_alignment",
            ok=(not output_report) or (output_report == selected_report),
            severity="repairable",
            detail="output report should align with selected report",
        )

    task_type = str(spec.get("task_type") or "").strip().lower()
    output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    output_mode = str(output_contract.get("mode") or "").strip().lower()
    top_n = int(spec.get("top_n") or 0) if str(spec.get("top_n") or "0").strip().isdigit() else 0
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}

    if (output_mode in {"top_n", "detail", "kpi"}) and (not needs_clar):
        add_check(
            name="output_mode_payload_alignment",
            ok=(payload_type == "report_table") or is_no_data_text,
            severity="repairable",
            detail="business output modes top_n/detail/kpi should return report_table",
        )

    rows = _table_rows(out)
    cols = _table_columns(out)
    if payload_type == "report_table" and task_type in {"ranking", "detail", "kpi"}:
        add_check(
            name="non_empty_rows",
            ok=len(rows) > 0,
            severity="repairable",
            detail="report_table should contain rows for business ask",
        )

    doc_id = _extract_document_id(filters)
    if payload_type == "report_table" and doc_id:
        add_check(
            name="document_filter_applied",
            ok=_document_id_applied(doc_id, cols, rows),
            severity="repairable",
            detail="document-id constrained asks must return rows for the requested document only",
        )

    if payload_type == "report_table" and task_type == "trend":
        has_time = any(_looks_like_time_col(c) for c in cols if isinstance(c, dict))
        add_check(
            name="trend_has_time_axis",
            ok=has_time,
            severity="repairable",
            detail="trend output should include a temporal axis column (date/week/month/quarter/year)",
        )

    if payload_type == "report_table" and output_mode == "top_n" and top_n > 0:
        add_check(
            name="top_n_bound",
            ok=len(rows) <= top_n,
            severity="repairable",
            detail="top_n output should not exceed requested rank size",
        )

    minimal_columns = [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()]
    if payload_type == "report_table":
        if output_mode == "kpi":
            add_check(
                name="kpi_payload_shape",
                ok=(len(rows) == 1 and len(cols) >= 1),
                severity="repairable",
                detail="kpi output should be a single-row report_table",
            )
        elif minimal_columns and (not is_direct_doc_lookup):
            col_names = []
            for c in cols:
                col_names.append(str(c.get("fieldname") or "").strip())
                col_names.append(str(c.get("label") or "").strip())
            missing = [c for c in minimal_columns if not _has_minimal_column(col_names, c)]
            ok_minimal = len(missing) == 0
            if not ok_minimal:
                # Generic fallback: for dynamic column labels (e.g. warehouse-specific balance columns),
                # accept when table still has one business dimension and one numeric measure.
                has_numeric = any(_is_numeric_col(c, rows) for c in cols if isinstance(c, dict))
                has_dimension = any((not _is_numeric_col(c, rows)) for c in cols if isinstance(c, dict))
                if has_numeric and has_dimension and len(missing) <= max(1, len(minimal_columns) // 2):
                    ok_minimal = True
            add_check(
                name="minimal_columns_present",
                ok=ok_minimal,
                severity="repairable",
                detail=f"missing minimal columns: {missing}",
            )

    if hard_fail_ids:
        verdict = VERDICT_HARD_FAIL
    elif repairable_ids:
        verdict = VERDICT_REPAIRABLE_FAIL
    else:
        verdict = VERDICT_PASS

    failed_ids = [c["id"] for c in checks if not bool(c.get("ok"))]
    return {
        "verdict": verdict,
        "failed_check_ids": failed_ids,
        "hard_fail_check_ids": hard_fail_ids,
        "repairable_check_ids": repairable_ids,
        "checks": checks,
    }


def make_quality_gate_tool_message(*, tool: str, mode: str, quality: Dict[str, Any]) -> str:
    obj = quality if isinstance(quality, dict) else {}
    return json.dumps(
        {
            "type": "v7_quality_gate",
            "phase": "phase4",
            "mode": str(mode or "").strip(),
            "tool": str(tool or "").strip(),
            "verdict": str(obj.get("verdict") or ""),
            "failed_check_ids": list(obj.get("failed_check_ids") or []),
            "hard_fail_check_ids": list(obj.get("hard_fail_check_ids") or []),
            "repairable_check_ids": list(obj.get("repairable_check_ids") or []),
        },
        ensure_ascii=False,
        default=str,
    )
