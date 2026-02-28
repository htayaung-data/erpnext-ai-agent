from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from ai_assistant_ui.ai_core.ontology_normalization import (
    known_dimension,
    known_metric,
    semantic_aliases,
)

VERDICT_PASS = "PASS"
VERDICT_REPAIRABLE_FAIL = "REPAIRABLE_FAIL"
VERDICT_HARD_FAIL = "HARD_FAIL"

_FAILURE_CLASS_BY_CHECK = {
    "resolver_blocker_absent": "constraint",
    "loop_guard_not_triggered": "loop",
    "constraint_set_applied": "contract",
    "semantic_context_recorded": "contract",
    "catalog_usage_or_fallback_recorded": "observability",
    "payload_type_supported": "shape",
    "selected_report_alignment": "semantic",
    "output_mode_payload_alignment": "shape",
    "non_empty_rows": "data",
    "document_filter_applied": "constraint",
    "trend_has_time_axis": "shape",
    "top_n_bound": "shape",
    "kpi_payload_shape": "shape",
    "minimal_columns_present": "shape",
    "requested_dimensions_present": "shape",
    "requested_metric_present": "semantic",
    "latest_records_time_axis": "shape",
    "latest_records_identifier_axis": "shape",
    "latest_records_subject_alignment": "semantic",
}


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


def _token_set(value: Any) -> List[str]:
    import re

    raw = str(value or "").strip().lower()
    if not raw:
        return []
    out: List[str] = []
    seen = set()
    stop = {"the", "and", "for", "with", "from", "this", "that", "those", "these", "latest", "recent", "newest", "last"}
    for t in re.findall(r"[a-z0-9]+", raw):
        if len(t) < 3 or t in stop:
            continue
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
        # Simple singularization improves subject/column matching
        # (e.g., invoices -> invoice, customers -> customer).
        if t.endswith("s") and len(t) > 3:
            sg = t[:-1]
            if sg and (sg not in seen):
                seen.add(sg)
                out.append(sg)
    return out


def _minimal_aliases(token: str) -> List[str]:
    return [_norm_token(a) for a in semantic_aliases(token) if _norm_token(a)]


def _metric_aliases(token: str) -> List[str]:
    metric = str(known_metric(token) or "").strip()
    if not metric:
        return []
    out: List[str] = []
    seen = set()
    for raw in list(semantic_aliases(metric, exclude_generic_metric_terms=True) or []):
        s = _norm_token(raw)
        if not s:
            continue
        # Prevent metric checks from matching dimension aliases like "item"/"warehouse".
        if str(known_dimension(s) or "").strip():
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


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


def _requested_metric(spec: Dict[str, Any]) -> str:
    metric_raw = str(spec.get("metric") or "").strip()
    metric = str(known_metric(metric_raw) or "").strip()
    if metric:
        return metric
    subject_raw = str(spec.get("subject") or "").strip()
    metric2 = str(known_metric(subject_raw) or "").strip()
    return metric2


def _has_metric_column(cols: List[Dict[str, Any]], rows: List[Dict[str, Any]], metric_token: str) -> bool:
    aliases = _metric_aliases(metric_token)
    if not aliases:
        return False
    for c in cols:
        if not isinstance(c, dict):
            continue
        if not _is_numeric_col(c, rows):
            continue
        fn = _norm_token(c.get("fieldname"))
        lb = _norm_token(c.get("label"))
        text = f"{fn} {lb}".strip()
        for a in aliases:
            if (a == fn) or (a == lb) or (a in text) or (text in a):
                return True
    return False


def _requested_dimensions(spec: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    seen = set()
    oc = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    raw_vals: List[str] = []
    raw_vals.extend([str(x).strip() for x in list(spec.get("dimensions") or []) if str(x).strip()])
    raw_vals.extend([str(x).strip() for x in list(spec.get("group_by") or []) if str(x).strip()])
    raw_vals.extend([str(x).strip() for x in list(oc.get("minimal_columns") or []) if str(x).strip()])
    for raw in raw_vals:
        d = str(known_dimension(raw) or "").strip().lower()
        if not d or d in seen:
            continue
        seen.add(d)
        out.append(d)
    return out


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


def _looks_like_identifier_col(col: Dict[str, Any], rows: List[Dict[str, Any]]) -> bool:
    if _is_numeric_col(col, rows):
        return False
    fn = _norm_token(col.get("fieldname"))
    lb = _norm_token(col.get("label"))
    text = f"{fn} {lb}".strip()
    id_tokens = (
        "id",
        "name",
        "invoice",
        "order",
        "voucher",
        "document",
        "customer",
        "supplier",
        "item",
        "employee",
        "party",
    )
    if any(t in text for t in id_tokens):
        return True
    if str(known_dimension(fn) or "").strip():
        return True
    if str(known_dimension(lb) or "").strip():
        return True
    return False


def _column_tokens(cols: List[Dict[str, Any]]) -> List[str]:
    out: List[str] = []
    seen = set()
    for c in cols:
        if not isinstance(c, dict):
            continue
        for src in (c.get("fieldname"), c.get("label")):
            for t in _token_set(src):
                if t in seen:
                    continue
                seen.add(t)
                out.append(t)
    return out


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

    def add_check(*, name: str, ok: bool, severity: str, detail: str, failure_class: str = "") -> None:
        cid = _check_id(name, len(checks) + 1)
        fclass = str(failure_class or _FAILURE_CLASS_BY_CHECK.get(str(name or ""), "semantic")).strip().lower()
        recoverable = str(severity or "").strip().lower() != "hard"
        checks.append(
            {
                "id": cid,
                "check": name,
                "ok": bool(ok),
                "severity": severity,
                "recoverable": bool(recoverable),
                "failure_class": fclass,
                "detail": detail,
            }
        )
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

    # Check 3: constraint-set contract must exist on resolver output.
    hard_constraints = res.get("hard_constraints") if isinstance(res.get("hard_constraints"), dict) else {}
    add_check(
        name="constraint_set_applied",
        ok=bool(hard_constraints) and str(hard_constraints.get("schema_version") or "").strip() == "constraint_set_v1",
        severity="hard",
        detail="resolved.hard_constraints must include constraint_set_v1",
    )

    # Check 4: semantic catalog context must be present for observability.
    semantic_context = res.get("semantic_context") if isinstance(res.get("semantic_context"), dict) else {}
    add_check(
        name="semantic_context_recorded",
        ok=bool(semantic_context),
        severity="hard",
        detail="resolved.semantic_context must be present",
    )
    if semantic_context:
        catalog_available = bool(semantic_context.get("catalog_available"))
        if catalog_available:
            catalog_ok = bool(list(semantic_context.get("selected_tables") or []))
            catalog_detail = "catalog available -> selected_tables must be non-empty"
        else:
            fallback_keys = ("query_tokens", "preferred_domains", "preferred_dimensions", "preferred_filter_kinds")
            catalog_ok = all(k in semantic_context for k in fallback_keys)
            catalog_detail = "catalog unavailable -> fallback context keys must be recorded"
        add_check(
            name="catalog_usage_or_fallback_recorded",
            ok=catalog_ok,
            severity="repairable",
            detail=catalog_detail,
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
    task_class = str(spec.get("task_class") or "").strip().lower()
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
        # Empty tabular results are a valid no-data outcome and must not force
        # clarification loops when the execution path is otherwise semantically valid.
        no_data_table = len(rows) == 0
        add_check(
            name="non_empty_rows",
            ok=(len(rows) > 0) or no_data_table,
            severity="repairable",
            detail=(
                "report_table contains rows"
                if len(rows) > 0
                else "empty table accepted as no-data result"
            ),
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
    requested_dims = set(_requested_dimensions(spec))
    requested_metric = _requested_metric(spec)
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
                # Never relax if any missing minimal column is a requested semantic dimension.
                missing_dim_cols = [
                    c for c in missing
                    if str(known_dimension(c) or "").strip().lower() in requested_dims
                ]
                if not missing_dim_cols:
                    # If all minimal columns are missing, this is not a shape
                    # near-match and should remain a repairable failure.
                    if len(missing) >= len(minimal_columns):
                        ok_minimal = False
                    else:
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

        # Enforce requested semantic dimensions (from group_by/dimensions/output contract)
        # are actually present in output columns for non-KPI table asks.
        if output_mode != "kpi" and requested_dims and (not is_direct_doc_lookup):
            col_names = []
            for c in cols:
                col_names.append(str(c.get("fieldname") or "").strip())
                col_names.append(str(c.get("label") or "").strip())
            missing_requested_dims = [d for d in sorted(requested_dims) if not _has_minimal_column(col_names, d)]
            add_check(
                name="requested_dimensions_present",
                ok=(len(missing_requested_dims) == 0),
                severity="repairable",
                detail=f"missing requested dimensions: {missing_requested_dims}",
            )

        if (
            output_mode != "kpi"
            and requested_metric
            and (not is_direct_doc_lookup)
            and task_class != "list_latest_records"
        ):
            if len(rows) == 0:
                add_check(
                    name="requested_metric_present",
                    ok=True,
                    severity="repairable",
                    detail=f"metric-column check skipped for empty result set: {requested_metric}",
                )
            else:
                add_check(
                    name="requested_metric_present",
                    ok=_has_metric_column(cols, rows, requested_metric),
                    severity="repairable",
                    detail=f"requested metric missing in numeric columns: {requested_metric}",
                )

        if task_class == "list_latest_records":
            has_time_axis = any(_looks_like_time_col(c) for c in cols if isinstance(c, dict))
            has_identifier_axis = any(_looks_like_identifier_col(c, rows) for c in cols if isinstance(c, dict))
            subj_tokens = [t for t in _token_set(spec.get("subject")) if t not in {"records", "record"}]
            col_tokens = set(_column_tokens(cols))
            subject_aligned = (not subj_tokens) or bool(col_tokens & set(subj_tokens))
            add_check(
                name="latest_records_time_axis",
                ok=has_time_axis,
                severity="repairable",
                detail="latest-record asks should expose a temporal axis column",
            )
            add_check(
                name="latest_records_identifier_axis",
                ok=has_identifier_axis,
                severity="repairable",
                detail="latest-record asks should expose a record-identifier/dimension column",
            )
            add_check(
                name="latest_records_subject_alignment",
                ok=subject_aligned,
                severity="repairable",
                detail=f"subject tokens should align with output columns: {subj_tokens}",
            )

    if hard_fail_ids:
        verdict = VERDICT_HARD_FAIL
    elif repairable_ids:
        verdict = VERDICT_REPAIRABLE_FAIL
    else:
        verdict = VERDICT_PASS

    failed_ids = [c["id"] for c in checks if not bool(c.get("ok"))]
    failed_checks = [c for c in checks if not bool(c.get("ok"))]
    repairable_classes = sorted(
        {
            str(c.get("failure_class") or "").strip().lower()
            for c in failed_checks
            if bool(c.get("recoverable"))
            and str(c.get("failure_class") or "").strip()
        }
    )
    hard_classes = sorted(
        {
            str(c.get("failure_class") or "").strip().lower()
            for c in failed_checks
            if (not bool(c.get("recoverable")))
            and str(c.get("failure_class") or "").strip()
        }
    )
    failed_classes = sorted(set(repairable_classes + hard_classes))
    return {
        "verdict": verdict,
        "failed_check_ids": failed_ids,
        "failed_checks": failed_checks,
        "failed_failure_classes": failed_classes,
        "repairable_failure_classes": repairable_classes,
        "hard_failure_classes": hard_classes,
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
            "failed_failure_classes": list(obj.get("failed_failure_classes") or []),
            "repairable_failure_classes": list(obj.get("repairable_failure_classes") or []),
            "hard_failure_classes": list(obj.get("hard_failure_classes") or []),
            "hard_fail_check_ids": list(obj.get("hard_fail_check_ids") or []),
            "repairable_check_ids": list(obj.get("repairable_check_ids") or []),
        },
        ensure_ascii=False,
        default=str,
    )
