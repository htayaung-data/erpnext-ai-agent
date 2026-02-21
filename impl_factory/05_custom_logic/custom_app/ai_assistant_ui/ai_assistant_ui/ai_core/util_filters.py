from __future__ import annotations

import datetime as dt
import re
from typing import Any, Dict, List, Optional, Tuple


_REL_TODAY = re.compile(r"\btoday\b", re.I)
_REL_YESTERDAY = re.compile(r"\byesterday\b", re.I)
_REL_THIS_MONTH = re.compile(r"\bthis\s+month\b", re.I)
_REL_LAST_MONTH = re.compile(r"\blast\s+month\b", re.I)


def today_str() -> str:
    return dt.date.today().isoformat()


def _is_iso_date(s: str) -> bool:
    try:
        dt.date.fromisoformat(s)
        return True
    except Exception:
        return False


def _month_range(d: dt.date) -> Tuple[str, str]:
    first = d.replace(day=1)
    if first.month == 12:
        next_first = first.replace(year=first.year + 1, month=1)
    else:
        next_first = first.replace(month=first.month + 1)
    last = next_first - dt.timedelta(days=1)
    return first.isoformat(), last.isoformat()


def resolve_relative_date_range(text: str) -> Optional[Tuple[str, str]]:
    t = (text or "").strip().lower()
    today = dt.date.today()

    if _REL_LAST_MONTH.search(t):
        # previous month range
        first_this_month = today.replace(day=1)
        last_prev_month = first_this_month - dt.timedelta(days=1)
        return _month_range(last_prev_month)

    if _REL_THIS_MONTH.search(t):
        return _month_range(today)

    if _REL_YESTERDAY.search(t):
        y = today - dt.timedelta(days=1)
        s = y.isoformat()
        return (s, s)

    if _REL_TODAY.search(t):
        s = today.isoformat()
        return (s, s)

    return None


def resolve_relative_date_value(text: str) -> Optional[str]:
    rng = resolve_relative_date_range(text)
    if not rng:
        return None
    # for as_on_date/report_date type fields: use end of range
    return rng[1]


def normalize_filters_for_requirements(
    *,
    question: str,
    planned_filters: Dict[str, Any],
    filters_definition: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Returns (normalized_filters, error_message).
    - Removes unknown filter keys
    - Converts relative date words to ISO dates
    - Maps generic keys like 'date' into actual report fields if possible
    - Normalizes MultiSelectList values into lists
    """

    fdefs = {d.get("fieldname"): d for d in (filters_definition or []) if isinstance(d, dict) and d.get("fieldname")}
    allowed = set(fdefs.keys())

    out: Dict[str, Any] = {}

    # 1) keep only allowed keys (but allow a couple of generic aliases we can map)
    incoming = dict(planned_filters or {})
    generic_date = incoming.pop("date", None)
    incoming_date_range = incoming.pop("date_range", None)

    for k, v in incoming.items():
        if k not in allowed:
            continue
        out[k] = v

    # 2) map generic date signals into correct fields based on report filter schema
    date_signal = None
    if isinstance(generic_date, str) and generic_date.strip():
        date_signal = generic_date.strip()
    elif isinstance(incoming_date_range, str) and incoming_date_range.strip():
        date_signal = incoming_date_range.strip()

    # also detect from the question if planner didn't pass it
    if not date_signal:
        date_signal = question

    # If report has from_date/to_date, fill them when missing
    if ("from_date" in allowed or "to_date" in allowed) and (not out.get("from_date") or not out.get("to_date")):
        rng = resolve_relative_date_range(date_signal)
        if rng:
            out.setdefault("from_date", rng[0])
            out.setdefault("to_date", rng[1])

    # If report has as_on_date/report_date, fill when missing
    for single_date_field in ("as_on_date", "report_date"):
        if single_date_field in allowed and not out.get(single_date_field):
            v = resolve_relative_date_value(date_signal)
            if v:
                out[single_date_field] = v

    # 3) normalize Date field values (must be ISO)
    for fn, d in fdefs.items():
        if d.get("fieldtype") != "Date":
            continue
        if fn not in out or out[fn] is None:
            continue
        v = out[fn]
        if isinstance(v, str):
            s = v.strip()
            # allow relative words here too
            rel = resolve_relative_date_value(s)
            if rel:
                out[fn] = rel
            elif not _is_iso_date(s):
                return out, f"Invalid Date for {fn}: {s}"

    # 4) normalize MultiSelectList into list
    for fn, d in fdefs.items():
        if d.get("fieldtype") != "MultiSelectList":
            continue
        if fn not in out or out[fn] is None:
            continue
        v = out[fn]
        if isinstance(v, str):
            s = v.strip()
            out[fn] = [s] if s else []
        elif isinstance(v, (tuple, set)):
            out[fn] = list(v)
        elif not isinstance(v, list):
            out[fn] = [v]

    return out, None
