from __future__ import annotations

import calendar
import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, Optional

import frappe


@dataclass(frozen=True)
class DateRange:
    start: dt.date
    end: dt.date

    @property
    def start_str(self) -> str:
        return self.start.isoformat()

    @property
    def end_str(self) -> str:
        return self.end.isoformat()


def last_month_range(today: Optional[dt.date] = None) -> DateRange:
    today = today or dt.date.today()
    if today.month == 1:
        y, m = today.year - 1, 12
    else:
        y, m = today.year, today.month - 1
    last_day = calendar.monthrange(y, m)[1]
    return DateRange(start=dt.date(y, m, 1), end=dt.date(y, m, last_day))


def this_month_range(today: Optional[dt.date] = None) -> DateRange:
    """
    Current month date range.
    """
    today = today or dt.date.today()
    y, m = today.year, today.month
    last_day = calendar.monthrange(y, m)[1]
    return DateRange(start=dt.date(y, m, 1), end=dt.date(y, m, last_day))


def resolve_default_company() -> Optional[str]:
    """
    Many reports require company; try user default, global default, then first Company record.
    """
    try:
        c = frappe.defaults.get_user_default("Company")
        if c:
            return c
    except Exception:
        pass

    try:
        c = frappe.defaults.get_global_default("company")
        if c:
            return c
    except Exception:
        pass

    try:
        rows = frappe.get_all("Company", fields=["name"], limit=1)
        if rows:
            return rows[0]["name"]
    except Exception:
        pass

    return None


def apply_sales_analytics_defaults(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sales Analytics typically requires:
      tree_type, doc_type, value_quantity, from_date, to_date, company, range, curves
    We enforce safe defaults when missing.
    """
    out = dict(filters or {})

    out.setdefault("tree_type", "Customer")
    out.setdefault("doc_type", "Sales Invoice")
    out.setdefault("value_quantity", "Value")
    out.setdefault("range", "Monthly")
    out.setdefault("curves", "Total Only")

    if not out.get("company"):
        company = resolve_default_company()
        if company:
            out["company"] = company

    return out
