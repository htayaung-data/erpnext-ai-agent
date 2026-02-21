from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ai_assistant_ui.ai_core.fac.catalog import list_reports_for_user
from ai_assistant_ui.ai_core.v7.capability_index import build_capability_index
from ai_assistant_ui.ai_core.v7.capability_schema import DEFAULT_FRESHNESS_HOURS, utc_now_iso

_DRIFT_SAMPLE_LIMIT = 80


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _parse_previous_snapshot(previous_snapshot: Any) -> Dict[str, Any]:
    if not isinstance(previous_snapshot, dict):
        return {}
    if isinstance(previous_snapshot.get("index"), dict):
        return dict(previous_snapshot)
    if isinstance(previous_snapshot.get("reports"), list):
        return {"index": dict(previous_snapshot)}
    return {}


def _index_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    if isinstance(payload.get("index"), dict):
        return dict(payload.get("index") or {})
    if isinstance(payload.get("reports"), list):
        return dict(payload)
    return {}


def _row_report_name(row: Dict[str, Any]) -> str:
    return str(row.get("report_name") or row.get("name") or "").strip()


def _row_report_family(row: Dict[str, Any]) -> str:
    return str(row.get("report_family") or row.get("module") or "Unknown").strip() or "Unknown"


def _row_confidence(row: Dict[str, Any]) -> float:
    meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    return _as_float(meta.get("confidence"), 0.0)


def _row_fingerprint(row: Dict[str, Any]) -> str:
    meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    return str(meta.get("fingerprint") or "").strip()


def _row_requirements_unknown(row: Dict[str, Any]) -> bool:
    if "requirements_unknown" in row:
        return bool(row.get("requirements_unknown"))
    constraints = row.get("constraints") if isinstance(row.get("constraints"), dict) else {}
    return bool(constraints.get("requirements_unknown"))


def _row_is_fresh(row: Dict[str, Any]) -> bool:
    meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    return bool(meta.get("fresh"))


def compute_capability_coverage(index: Dict[str, Any], *, min_confidence: float = 0.60) -> Dict[str, Any]:
    rows = [r for r in list(index.get("reports") or []) if isinstance(r, dict) and _row_report_name(r)]
    active_rows = [r for r in rows if not bool(r.get("disabled"))]

    family_totals: Dict[str, int] = {}
    family_covered: Dict[str, int] = {}
    unknown_reports: List[str] = []
    low_confidence_reports: List[str] = []
    stale_reports: List[str] = []

    for row in active_rows:
        family = _row_report_family(row)
        family_totals[family] = family_totals.get(family, 0) + 1

        report_name = _row_report_name(row)
        conf = _row_confidence(row)
        unknown = _row_requirements_unknown(row)
        fresh = _row_is_fresh(row)
        covered = (not unknown) and (conf >= float(min_confidence))

        if covered:
            family_covered[family] = family_covered.get(family, 0) + 1
        if unknown:
            unknown_reports.append(report_name)
        if conf < float(min_confidence):
            low_confidence_reports.append(report_name)
        if not fresh:
            stale_reports.append(report_name)

    family_names = sorted(family_totals.keys())
    covered_families = [fam for fam in family_names if family_covered.get(fam, 0) > 0]

    family_coverage_rate = (len(covered_families) / len(family_names)) if family_names else 0.0
    report_coverage_rate = (
        sum(family_covered.values()) / len(active_rows)
        if active_rows
        else 0.0
    )

    families: List[Dict[str, Any]] = []
    for fam in family_names:
        total = family_totals.get(fam, 0)
        covered = family_covered.get(fam, 0)
        rate = (covered / total) if total else 0.0
        families.append(
            {
                "family": fam,
                "total_reports": int(total),
                "covered_reports": int(covered),
                "coverage_rate": round(rate, 4),
            }
        )

    return {
        "min_confidence": round(float(min_confidence), 4),
        "active_report_count": len(active_rows),
        "active_report_family_count": len(family_names),
        "covered_report_count": int(sum(family_covered.values())),
        "covered_report_family_count": len(covered_families),
        "report_coverage_rate": round(report_coverage_rate, 4),
        "family_coverage_rate": round(family_coverage_rate, 4),
        "family_gate_pass_95": bool(family_coverage_rate >= 0.95),
        "families": families,
        "unknown_capability_count": len(unknown_reports),
        "low_confidence_count": len(low_confidence_reports),
        "stale_count": len(stale_reports),
        "unknown_reports_sample": sorted(unknown_reports)[:_DRIFT_SAMPLE_LIMIT],
        "low_confidence_sample": sorted(low_confidence_reports)[:_DRIFT_SAMPLE_LIMIT],
        "stale_sample": sorted(stale_reports)[:_DRIFT_SAMPLE_LIMIT],
    }


def detect_schema_drift(previous_snapshot: Dict[str, Any], current_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    prev_index = _index_from_payload(previous_snapshot)
    curr_index = _index_from_payload(current_snapshot)

    prev_rows = [r for r in list(prev_index.get("reports") or []) if isinstance(r, dict) and _row_report_name(r)]
    curr_rows = [r for r in list(curr_index.get("reports") or []) if isinstance(r, dict) and _row_report_name(r)]

    prev_by = {_row_report_name(r): r for r in prev_rows}
    curr_by = {_row_report_name(r): r for r in curr_rows}
    prev_names = set(prev_by.keys())
    curr_names = set(curr_by.keys())

    added = sorted(list(curr_names - prev_names))
    removed = sorted(list(prev_names - curr_names))
    changed: List[str] = []
    unchanged = 0

    for name in sorted(prev_names & curr_names):
        prev_fp = _row_fingerprint(prev_by[name])
        curr_fp = _row_fingerprint(curr_by[name])
        if prev_fp and curr_fp and (prev_fp == curr_fp):
            unchanged += 1
            continue
        if prev_fp == curr_fp:
            unchanged += 1
            continue
        changed.append(name)

    stale_now = sorted([_row_report_name(r) for r in curr_rows if not _row_is_fresh(r)])
    unknown_now = sorted([_row_report_name(r) for r in curr_rows if _row_requirements_unknown(r)])

    return {
        "previous_report_count": len(prev_rows),
        "current_report_count": len(curr_rows),
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
        "unchanged_count": int(unchanged),
        "stale_count": len(stale_now),
        "unknown_count": len(unknown_now),
        "added_sample": added[:_DRIFT_SAMPLE_LIMIT],
        "removed_sample": removed[:_DRIFT_SAMPLE_LIMIT],
        "changed_sample": changed[:_DRIFT_SAMPLE_LIMIT],
        "stale_sample": stale_now[:_DRIFT_SAMPLE_LIMIT],
        "unknown_sample": unknown_now[:_DRIFT_SAMPLE_LIMIT],
    }


def _make_alerts(*, coverage: Dict[str, Any], drift: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not bool(coverage.get("family_gate_pass_95")):
        out.append(
            {
                "severity": "error",
                "code": "capability_family_coverage_below_threshold",
                "message": (
                    f"Active report-family coverage is {coverage.get('family_coverage_rate')} "
                    "which is below required 0.95."
                ),
            }
        )
    if _as_int(coverage.get("stale_count")) > 0:
        out.append(
            {
                "severity": "warning",
                "code": "stale_capability_detected",
                "message": f"Stale capability rows detected: {coverage.get('stale_count')}.",
            }
        )
    if _as_int(coverage.get("unknown_capability_count")) > 0:
        out.append(
            {
                "severity": "warning",
                "code": "unknown_capability_detected",
                "message": (
                    "Capability rows with unknown metadata were found: "
                    f"{coverage.get('unknown_capability_count')}."
                ),
            }
        )
    if _as_int(drift.get("removed_count")) > 0:
        out.append(
            {
                "severity": "warning",
                "code": "capability_removed",
                "message": f"Reports removed since previous snapshot: {drift.get('removed_count')}.",
            }
        )
    return out


def build_capability_platform_payload(
    *,
    user: Optional[str],
    include_disabled: bool = False,
    max_reports: int = 260,
    previous_snapshot: Optional[Dict[str, Any]] = None,
    freshness_hours: int = DEFAULT_FRESHNESS_HOURS,
    min_confidence: float = 0.60,
) -> Dict[str, Any]:
    rows = list_reports_for_user(user=user, include_disabled=include_disabled)
    rows = [r for r in rows if isinstance(r, dict)]
    rows.sort(key=lambda r: str(r.get("name") or "").strip().lower())
    rows = rows[: max(1, int(max_reports))]

    index = build_capability_index(
        reports=rows,
        user=user,
        generated_at_utc=utc_now_iso(),
        freshness_hours=max(1, int(freshness_hours)),
    )
    prev_payload = _parse_previous_snapshot(previous_snapshot)
    coverage = compute_capability_coverage(index=index, min_confidence=float(min_confidence))
    drift = detect_schema_drift(prev_payload, {"index": index})
    alerts = _make_alerts(coverage=coverage, drift=drift)

    return {
        "_phase": "phase2_capability_platform",
        "executed_at_utc": utc_now_iso(),
        "job": {
            "name": "capability_ingestion_job",
            "source": "fac_erp_metadata",
            "user_scope": str(user or ""),
            "max_reports": int(max_reports),
            "include_disabled": bool(include_disabled),
            "freshness_hours": int(max(1, freshness_hours)),
            "min_confidence": round(float(min_confidence), 4),
        },
        "index": index,
        "coverage": coverage,
        "drift": drift,
        "alerts": alerts,
    }


def run_capability_ingestion_job(
    *,
    user: Optional[str] = None,
    include_disabled: bool = False,
    max_reports: int = 260,
    previous_snapshot: Optional[Dict[str, Any]] = None,
    freshness_hours: int = DEFAULT_FRESHNESS_HOURS,
    min_confidence: float = 0.60,
    include_rows: bool = True,
) -> Dict[str, Any]:
    """
    Bench-executable entry point for Phase 2 capability ingestion.
    Returns coverage + drift + alerts and (optionally) full rows.
    """
    payload = build_capability_platform_payload(
        user=user,
        include_disabled=bool(include_disabled),
        max_reports=int(max_reports),
        previous_snapshot=previous_snapshot if isinstance(previous_snapshot, dict) else None,
        freshness_hours=int(max(1, freshness_hours)),
        min_confidence=float(min_confidence),
    )
    if include_rows:
        return payload

    compact = dict(payload)
    index = compact.get("index") if isinstance(compact.get("index"), dict) else {}
    compact["index"] = {
        "schema_version": index.get("schema_version"),
        "capability_index_version": index.get("capability_index_version"),
        "generated_at_utc": index.get("generated_at_utc"),
        "report_count": index.get("report_count"),
        "known_requirements_count": index.get("known_requirements_count"),
        "high_confidence_count": index.get("high_confidence_count"),
        "fresh_count": index.get("fresh_count"),
        "validation_error_count": index.get("validation_error_count"),
    }
    return compact

