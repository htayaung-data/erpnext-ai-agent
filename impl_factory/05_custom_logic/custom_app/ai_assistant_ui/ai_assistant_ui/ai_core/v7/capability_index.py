from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from ai_assistant_ui.ai_core.v7.capability_registry import apply_registry_overrides
from ai_assistant_ui.ai_core.v7.capability_schema import (
    DEFAULT_FRESHNESS_HOURS,
    SCHEMA_VERSION,
    build_capability_row,
    utc_now_iso,
    validate_capability_row,
)

_REQ_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_REQ_TTL_SECONDS = 1800
_CAPABILITY_INDEX_VERSION = "v1.0"


def _as_dict_requirements(req: Any) -> Dict[str, Any]:
    if isinstance(req, dict):
        return {
            "required_filter_names": list(req.get("required_filter_names") or []),
            "filters_definition": list(req.get("filters_definition") or []),
            "raw_type": str(req.get("raw_type") or ""),
        }
    return {
        "required_filter_names": list(getattr(req, "required_filter_names", []) or []),
        "filters_definition": list(getattr(req, "filters_definition", []) or []),
        "raw_type": str(getattr(req, "raw_type", "") or ""),
    }


def _get_requirements_cached(report_name: str, *, user: Optional[str]) -> Dict[str, Any]:
    now = time.time()
    key = f"{str(user or '').strip()}::{str(report_name or '').strip()}"
    cached = _REQ_CACHE.get(key)
    if cached and (now - cached[0] <= _REQ_TTL_SECONDS):
        return dict(cached[1])

    from ai_assistant_ui.ai_core.fac.requirements import get_report_requirements

    req_obj = get_report_requirements(report_name, user=user)
    req = _as_dict_requirements(req_obj)
    _REQ_CACHE[key] = (now, dict(req))
    return req


def build_capability_index(
    *,
    reports: List[Dict[str, Any]],
    requirements_by_report: Optional[Dict[str, Any]] = None,
    user: Optional[str] = None,
    generated_at_utc: Optional[str] = None,
    freshness_hours: int = DEFAULT_FRESHNESS_HOURS,
) -> Dict[str, Any]:
    reports_in = [r for r in (reports or []) if isinstance(r, dict) and str(r.get("name") or "").strip()]
    req_by = dict(requirements_by_report or {})
    rows: List[Dict[str, Any]] = []
    req_attached = 0
    validation_errors: Dict[str, List[str]] = {}
    known_requirements_count = 0
    fresh_rows = 0
    high_confidence_rows = 0

    snapshot_time = str(generated_at_utc or "").strip() or utc_now_iso()

    for report in reports_in:
        name = str(report.get("name") or "").strip()
        req = req_by.get(name)
        if req is None:
            try:
                req = _get_requirements_cached(name, user=user)
            except Exception:
                req = {"required_filter_names": [], "filters_definition": [], "raw_type": "requirements:error"}
        req_attached += 1
        req_norm = _as_dict_requirements(req)

        row = build_capability_row(
            report=report,
            requirements=req_norm,
            generated_at_utc=snapshot_time,
            freshness_hours=freshness_hours,
        )
        row = apply_registry_overrides(row)
        errs = validate_capability_row(row)
        if errs:
            validation_errors[name] = errs
        if not bool(row.get("requirements_unknown")):
            known_requirements_count += 1
        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        if bool(meta.get("fresh")):
            fresh_rows += 1
        try:
            conf = float(meta.get("confidence") or 0.0)
        except Exception:
            conf = 0.0
        if conf >= 0.60:
            high_confidence_rows += 1
        rows.append(row)

    by_name = {r["report_name"]: r for r in rows if r.get("report_name")}
    return {
        "_phase": "phase2_capability_index",
        "schema_version": SCHEMA_VERSION,
        "capability_index_version": _CAPABILITY_INDEX_VERSION,
        "generated_at_utc": snapshot_time,
        "freshness_hours": int(max(1, freshness_hours)),
        "report_count": len(rows),
        "known_requirements_count": known_requirements_count,
        "high_confidence_count": high_confidence_rows,
        "fresh_count": fresh_rows,
        "validation_error_count": len(validation_errors),
        "validation_errors": validation_errors,
        "reports": rows,
        "reports_by_name": by_name,
        "built_from": {
            "reports_input_count": len(reports_in),
            "requirements_attached_count": req_attached,
        },
    }

