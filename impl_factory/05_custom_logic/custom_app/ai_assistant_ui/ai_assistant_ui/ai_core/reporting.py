from __future__ import annotations

from typing import Any, Dict, Optional

import frappe

from ai_assistant_ui.ai_core.tools.report_tools import top_customers_by_revenue_last_month


def top_customers_by_revenue_last_month_tool(n: int, *, session_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Backwards-compatible facade.
    """
    return top_customers_by_revenue_last_month(n=int(n or 5), session_name=session_name, user=frappe.session.user)
