from __future__ import annotations

import calendar
import datetime as dt
from dataclasses import dataclass


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


def last_month_range(today: dt.date | None = None) -> DateRange:
    """Return the first and last date of the previous calendar month."""
    if today is None:
        today = dt.date.today()

    year = today.year
    month = today.month

    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1

    last_day = calendar.monthrange(prev_year, prev_month)[1]
    start = dt.date(prev_year, prev_month, 1)
    end = dt.date(prev_year, prev_month, last_day)
    return DateRange(start=start, end=end)
