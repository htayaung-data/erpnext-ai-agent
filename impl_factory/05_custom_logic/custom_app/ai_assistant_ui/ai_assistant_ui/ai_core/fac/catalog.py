from __future__ import annotations

from typing import Any, Dict, List, Optional

import frappe

from ai_assistant_ui.ai_core.fac.client import fac_report_list


def _normalize_report_list(raw: Any) -> List[Dict[str, Any]]:
    # FAC shape (seen in your system):
    # {success: true, result: {success: true, reports: [...]}}
    if isinstance(raw, dict):
        payload = raw
        if isinstance(payload.get("result"), dict):
            payload = payload["result"]
        if isinstance(payload.get("message"), dict):
            payload = payload["message"]

        reports = payload.get("reports") or payload.get("data") or payload.get("result")
        if isinstance(reports, list):
            out = []
            for r in reports:
                if isinstance(r, dict):
                    out.append(r)
            return out

    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]

    return []


def list_reports_for_user(
    *,
    user: Optional[str] = None,
    module: Optional[str] = None,
    report_type: Optional[str] = None,
    include_disabled: bool = False,
) -> List[Dict[str, Any]]:
    user = user or frappe.session.user
    raw = fac_report_list(module=module, report_type=report_type, user=user)
    reports = _normalize_report_list(raw)

    cleaned: List[Dict[str, Any]] = []
    for r in reports:
        name = r.get("report_name") or r.get("name")
        if not name:
            continue
        disabled = int(r.get("disabled") or 0)
        if disabled and not include_disabled:
            continue
        cleaned.append(
            {
                "name": name,
                "report_type": r.get("report_type"),
                "module": r.get("module"),
                "is_standard": r.get("is_standard"),
                "disabled": disabled,
            }
        )

    # de-dup by name
    seen = set()
    uniq = []
    for r in cleaned:
        if r["name"] in seen:
            continue
        seen.add(r["name"])
        uniq.append(r)

    return uniq
