from __future__ import annotations

from typing import Any, Optional

import frappe


def get_fac_api(user: Optional[str] = None):
    """
    Import FAC's FrappeAssistantAPI with fallbacks (FAC import paths have varied).
    """
    user = user or frappe.session.user

    # Try the most likely imports first.
    try:
        from frappe_assistant_core.api import FrappeAssistantAPI  # type: ignore
        return FrappeAssistantAPI(user)
    except Exception:
        pass

    try:
        from frappe_assistant_core.api.frappe_assistant_api import FrappeAssistantAPI  # type: ignore
        return FrappeAssistantAPI(user)
    except Exception as e:
        # If FAC is installed this should not happen; raise a clear error.
        raise RuntimeError(
            "Unable to import FrappeAssistantAPI from frappe_assistant_core. "
            "Check that frappe_assistant_core is installed and available on PYTHONPATH."
        ) from e


def fac_generate_report(
    report_name: str,
    filters: dict | None = None,
    fmt: str = "json",
    user: Optional[str] = None,
) -> Any:
    """
    Call FAC generate_report. Return value shape varies across versions/environments,
    so downstream code must normalize it.
    """
    api = get_fac_api(user=user)
    # FAC expects: generate_report(report_name, filters=..., format="json|csv|excel")
    return api.generate_report(report_name, filters=filters or {}, format=fmt)
