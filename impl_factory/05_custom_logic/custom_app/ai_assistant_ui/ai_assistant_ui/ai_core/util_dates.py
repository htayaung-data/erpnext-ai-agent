from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from typing import Any, Optional, Tuple, Union


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


def today_date() -> dt.date:
    return dt.date.today()


def is_iso_date(s: str) -> bool:
    try:
        dt.date.fromisoformat(s)
        return True
    except Exception:
        return False


def _try_parse_dmy(s: str) -> Optional[dt.date]:
    # Accept DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r'^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})$', (s or '').strip())
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return dt.date(y, mo, d)
    except Exception:
        return None


def _month_bounds(any_day: dt.date) -> DateRange:
    start = any_day.replace(day=1)
    # next month start
    if start.month == 12:
        next_start = dt.date(start.year + 1, 1, 1)
    else:
        next_start = dt.date(start.year, start.month + 1, 1)
    end = next_start - dt.timedelta(days=1)
    return DateRange(start=start, end=end)


def last_month_range(ref: Optional[dt.date] = None) -> DateRange:
    ref = ref or today_date()
    first_this = ref.replace(day=1)
    prev_end = first_this - dt.timedelta(days=1)
    return _month_bounds(prev_end)


def this_month_range(ref: Optional[dt.date] = None) -> DateRange:
    ref = ref or today_date()
    return _month_bounds(ref)


def last_week_range(ref: Optional[dt.date] = None) -> DateRange:
    ref = ref or today_date()
    # Monday=0
    start_this_week = ref - dt.timedelta(days=ref.weekday())
    start_last = start_this_week - dt.timedelta(days=7)
    end_last = start_this_week - dt.timedelta(days=1)
    return DateRange(start=start_last, end=end_last)


def this_week_range(ref: Optional[dt.date] = None) -> DateRange:
    ref = ref or today_date()
    start = ref - dt.timedelta(days=ref.weekday())
    end = start + dt.timedelta(days=6)
    return DateRange(start=start, end=end)


def parse_natural_date(value: Any, *, ref: Optional[dt.date] = None) -> Optional[dt.date]:
    ref = ref or today_date()

    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value

    s = str(value).strip().lower()
    if not s:
        return None

    if s in ('today', 'as of today', 'asof today'):
        return ref
    if s == 'yesterday':
        return ref - dt.timedelta(days=1)
    if s == 'tomorrow':
        return ref + dt.timedelta(days=1)

    # ISO first
    if is_iso_date(s):
        return dt.date.fromisoformat(s)

    # D/M/Y
    dmy = _try_parse_dmy(s)
    if dmy:
        return dmy

    return None


def extract_timeframe(text: str, *, ref: Optional[dt.date] = None) -> Tuple[Optional[dt.date], Optional[DateRange]]:
    """Return (as_of_date, date_range). Prefer explicit 'as of' if present."""
    ref = ref or today_date()
    t = (text or '').strip().lower()

    # explicit as-of
    m = re.search(r'\bas\s+of\s+([a-z0-9\/-]+)\b', t)
    if m:
        d = parse_natural_date(m.group(1), ref=ref)
        if d:
            return d, None

    # explicit between/from-to ISO
    m2 = re.search(r'\b(?:from|between)\s+(\d{4}-\d{2}-\d{2})\s+(?:to|and)\s+(\d{4}-\d{2}-\d{2})\b', t)
    if m2:
        try:
            d1 = dt.date.fromisoformat(m2.group(1))
            d2 = dt.date.fromisoformat(m2.group(2))
            if d1 <= d2:
                return None, DateRange(d1, d2)
        except Exception:
            pass

    # common relative ranges
    if re.search(r'\blast\s+month\b', t):
        return None, last_month_range(ref)
    if re.search(r'\bthis\s+month\b', t):
        return None, this_month_range(ref)
    if re.search(r'\blast\s+week\b', t):
        return None, last_week_range(ref)
    if re.search(r'\bthis\s+week\b', t):
        return None, this_week_range(ref)

    # single-date hints
    if re.search(r'\btoday\b', t):
        return ref, None
    if re.search(r'\byesterday\b', t):
        return ref - dt.timedelta(days=1), None

    return None, None
