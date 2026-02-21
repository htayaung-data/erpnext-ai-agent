from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import frappe

from ai_assistant_ui.ai_core.fac.client import fac_generate_report, fac_report_requirements
from ai_assistant_ui.ai_core.fac.normalize import (
    normalize_report_output,
    normalize_requirements_output,
    pick_total_field,
    sum_numeric_row,
)
from ai_assistant_ui.ai_core.fac.filters import last_month_range, apply_sales_analytics_defaults
from ai_assistant_ui.ai_core.fac.exports import save_table_exports


def run_fac_report(
    *,
    report_name: str,
    filters: Dict[str, Any],
    session_name: Optional[str] = None,
    user: Optional[str] = None,
    export: bool = False,
) -> Dict[str, Any]:
    user = user or frappe.session.user

    req_debug: Dict[str, Any] = {}
    try:
        raw_req = fac_report_requirements(report_name, user=user)
        req = normalize_requirements_output(raw_req)
        req_debug = {
            "requirements_raw_type": req.raw_type,
            "required_filters": req.required_filter_names,
        }
    except Exception:
        req_debug = {"requirements_error": "unavailable"}

    effective_filters = dict(filters or {})
    if report_name == "Sales Analytics":
        effective_filters = apply_sales_analytics_defaults(effective_filters)

    raw = fac_generate_report(report_name, filters=effective_filters, fmt="json", user=user)
    norm = normalize_report_output(raw)

    downloads: List[Dict[str, str]] = []
    if export and norm.rows:
        d = save_table_exports(
            basename=frappe.scrub(report_name) or "report",
            columns=norm.columns,
            rows=norm.rows,
            attach_to_doctype="AI Chat Session",
            attach_to_name=session_name,
            private=True,
        )
        if d.get("csv"):
            downloads.append({"label": "Download CSV", "format": "csv", "url": d["csv"]})
        if d.get("xlsx"):
            downloads.append({"label": "Download XLSX", "format": "xlsx", "url": d["xlsx"]})

    return {
        "type": "report_table",
        "report_name": report_name,
        "title": report_name,
        "filters": effective_filters,
        "debug": {"fac_report_raw_type": norm.raw_type, **req_debug},
        "table": {"columns": norm.columns, "rows": norm.rows},
        "downloads": downloads,
    }


def top_customers_by_revenue_last_month(
    *,
    n: int = 5,
    export: bool = False,
    session_name: Optional[str] = None,
    user: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Returns table data always.
    Only creates downloadable files when export=True.
    """
    user = user or frappe.session.user
    n = max(1, min(int(n or 5), 100))

    dr = last_month_range()
    filters = {
        "tree_type": "Customer",
        "doc_type": "Sales Invoice",
        "value_quantity": "Value",
        "from_date": dr.start_str,
        "to_date": dr.end_str,
        "range": "Monthly",
        # IMPORTANT: Do NOT force 'Total Only' here; it can collapse rows in some setups.
        # We'll rely on the report's normal output and compute totals robustly.
        "curves": "all",
    }

    payload = run_fac_report(
        report_name="Sales Analytics",
        filters=filters,
        session_name=session_name,
        user=user,
        export=False,  # export final top-N table, not raw report
    )

    cols = payload.get("table", {}).get("columns") or []
    rows = payload.get("table", {}).get("rows") or []

    # Identify customer column
    customer_fn = None
    for c in cols:
        label = (c.get("label") or "").lower()
        fn = (c.get("fieldname") or "").lower()
        if "customer" in label or fn == "customer":
            customer_fn = c.get("fieldname")
            break
    if not customer_fn and cols:
        customer_fn = cols[0].get("fieldname")

    total_fn = pick_total_field(cols)

    ranked: List[Tuple[str, float]] = []
    for r in rows:
        cust = r.get(customer_fn) if customer_fn else None
        if cust is None:
            continue
        cust_str = str(cust).strip()
        if not cust_str or cust_str.lower() in ("total", "grand total"):
            continue

        if total_fn and r.get(total_fn) is not None:
            revenue = sum_numeric_row({total_fn: r.get(total_fn)})
        else:
            revenue = sum_numeric_row(r, exclude=[customer_fn] if customer_fn else [])

        if revenue > 0:
            ranked.append((cust_str, revenue))

    ranked.sort(key=lambda x: x[1], reverse=True)
    top = ranked[:n]

    if not top:
        # No hallucination: just say no data
        return {
            "type": "text",
            "text": f"No customer revenue found for {dr.start_str} to {dr.end_str}.",
        }

    out_cols = [
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer"},
        {"label": "Revenue", "fieldname": "revenue", "fieldtype": "Currency"},
    ]
    out_rows = [{"customer": c, "revenue": v} for c, v in top]

    downloads: List[Dict[str, str]] = []
    if export:
        exports = save_table_exports(
            basename="top_customers_last_month",
            columns=out_cols,
            rows=out_rows,
            attach_to_doctype="AI Chat Session",
            attach_to_name=session_name,
            private=True,
        )
        if exports.get("csv"):
            downloads.append({"label": "Download CSV", "format": "csv", "url": exports.get("csv")})
        if exports.get("xlsx"):
            downloads.append({"label": "Download XLSX", "format": "xlsx", "url": exports.get("xlsx")})

    return {
        "type": "report_table",
        "title": f"Top {len(out_rows)} customers by revenue (last month)",
        "subtitle": f"{dr.start_str} to {dr.end_str}",
        "debug": payload.get("debug"),
        "table": {"columns": out_cols, "rows": out_rows},
        "downloads": downloads,
    }
