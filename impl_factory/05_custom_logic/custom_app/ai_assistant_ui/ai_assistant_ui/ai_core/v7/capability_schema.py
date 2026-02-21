from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Set, Tuple

from ai_assistant_ui.ai_core.ontology_normalization import (
    infer_domain_hints_from_report,
    infer_filter_kinds,
    infer_metric_hints,
    infer_primary_dimension,
)

SCHEMA_VERSION = "v1"
DEFAULT_FRESHNESS_HOURS = 24

_TIME_KIND_SET = {
    "date",
    "from_date",
    "to_date",
    "report_date",
    "start_year",
    "end_year",
    "fiscal_year",
    "year",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_utc(value: str) -> datetime:
    s = str(value or "").strip()
    if not s:
        return datetime.now(timezone.utc)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def normalize_report_family(module: Any) -> str:
    name = str(module or "").strip()
    return name if name else "Unknown"


def detect_filter_kinds(*, fieldname: str, label: str, fieldtype: str, options: str) -> Set[str]:
    text = " ".join(
        (
            str(fieldname or "").strip(),
            str(label or "").strip(),
            str(fieldtype or "").strip(),
            str(options or "").strip(),
        )
    ).strip()
    return set(infer_filter_kinds(text))


def infer_dimension_hints(filter_kinds: Iterable[str]) -> List[str]:
    kinds = {str(x or "").strip().lower() for x in filter_kinds}
    dimensions: List[str] = []
    for dim in ("customer", "supplier", "item", "warehouse", "company"):
        if dim in kinds:
            dimensions.append(dim)
    return dimensions


def infer_domain_hints(*, filter_kinds: Iterable[str], report_family: str, report_name: str) -> List[str]:
    return infer_domain_hints_from_report(
        report_name=report_name,
        report_family=report_family,
        filter_kinds=filter_kinds,
    )


def infer_time_support(filter_kinds: Iterable[str]) -> Dict[str, bool]:
    kinds = {str(x or "").strip().lower() for x in filter_kinds}
    as_of = bool({"date", "report_date"} & kinds)
    date_range = bool("from_date" in kinds and "to_date" in kinds)
    fiscal_year = bool("fiscal_year" in kinds)
    year_window = bool("start_year" in kinds and "end_year" in kinds) or bool("year" in kinds)
    any_time = bool(as_of or date_range or fiscal_year or year_window)
    return {
        "as_of": as_of,
        "range": date_range,
        "fiscal_year": fiscal_year,
        "year_window": year_window,
        "any": any_time,
    }


def confidence_from_metadata(
    *,
    requirements_raw_type: str,
    required_filter_names: List[str],
    filters_definition: List[Dict[str, Any]],
) -> Tuple[float, List[str]]:
    raw_type = str(requirements_raw_type or "").strip().lower()
    has_filters = bool(filters_definition)
    has_required = bool(required_filter_names)
    score = 0.25
    reasons: List[str] = ["base=0.25"]

    if raw_type.startswith("requirements:"):
        score += 0.35
        reasons.append("fac_requirements_source")
    elif "fallback_report_metadata" in raw_type:
        score += 0.22
        reasons.append("report_metadata_fallback_source")
    elif raw_type:
        score += 0.10
        reasons.append("other_source")

    if has_filters:
        score += 0.25
        reasons.append("filters_definition_present")
    else:
        reasons.append("filters_definition_missing")

    if has_required:
        score += 0.10
        reasons.append("required_filters_present")
    else:
        reasons.append("required_filters_missing")

    if ("no_filters" in raw_type) and (not has_filters) and (not has_required):
        score = max(score, 0.62)
        reasons.append("known_no_filters_capability")

    score = max(0.05, min(score, 0.95))
    return round(score, 4), reasons


def make_capability_fingerprint(capability_row: Dict[str, Any]) -> str:
    payload = {
        "report_name": capability_row.get("report_name"),
        "report_family": capability_row.get("report_family"),
        "report_type": capability_row.get("report_type"),
        "constraints": capability_row.get("constraints") if isinstance(capability_row.get("constraints"), dict) else {},
        "time_support": capability_row.get("time_support") if isinstance(capability_row.get("time_support"), dict) else {},
        "semantics": capability_row.get("semantics") if isinstance(capability_row.get("semantics"), dict) else {},
    }
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_capability_row(
    *,
    report: Dict[str, Any],
    requirements: Dict[str, Any],
    generated_at_utc: str,
    freshness_hours: int = DEFAULT_FRESHNESS_HOURS,
) -> Dict[str, Any]:
    report_name = str(report.get("name") or "").strip()
    report_family = normalize_report_family(report.get("module"))
    report_type = str(report.get("report_type") or "").strip()
    is_standard = bool(report.get("is_standard"))
    disabled = bool(int(report.get("disabled") or 0))

    required_filter_names = [str(x) for x in list(requirements.get("required_filter_names") or []) if str(x or "").strip()]
    filter_rows = [x for x in list(requirements.get("filters_definition") or []) if isinstance(x, dict)]
    requirements_raw_type = str(requirements.get("raw_type") or "").strip()
    requirements_unknown = not bool(filter_rows or required_filter_names)
    if requirements_unknown and ("no_filters" in requirements_raw_type.lower()):
        requirements_unknown = False

    supported_filter_names: List[str] = []
    supported_filter_kinds: Set[str] = set()
    required_filter_kinds: Set[str] = set()
    normalized_filter_defs: List[Dict[str, Any]] = []

    required_by_name = {str(x or "").strip().lower() for x in required_filter_names if str(x or "").strip()}
    for row in filter_rows:
        fieldname = str(row.get("fieldname") or "").strip()
        label = str(row.get("label") or "").strip()
        fieldtype = str(row.get("fieldtype") or "").strip()
        options = str(row.get("options") or "").strip()
        reqd = row.get("reqd")
        if reqd is None:
            reqd = row.get("mandatory")
        if fieldname:
            supported_filter_names.append(fieldname)
        kinds = detect_filter_kinds(fieldname=fieldname, label=label, fieldtype=fieldtype, options=options)
        supported_filter_kinds.update(kinds)
        if fieldname.lower() in required_by_name:
            required_filter_kinds.update(kinds)
        normalized_filter_defs.append(
            {
                "fieldname": fieldname,
                "label": label,
                "fieldtype": fieldtype,
                "options": options,
                "reqd": 1 if int(reqd or 0) == 1 else 0,
            }
        )

    for req_name in required_filter_names:
        required_filter_kinds.update(
            detect_filter_kinds(fieldname=req_name, label=req_name, fieldtype="", options="")
        )

    supported_filter_kinds_sorted = sorted(supported_filter_kinds)
    required_filter_kinds_sorted = sorted(required_filter_kinds)
    time_support = infer_time_support(supported_filter_kinds_sorted)
    dimension_hints = infer_dimension_hints(supported_filter_kinds_sorted)
    domain_hints = infer_domain_hints(
        filter_kinds=supported_filter_kinds_sorted,
        report_family=report_family,
        report_name=report_name,
    )
    metric_hints = infer_metric_hints(
        report_name=report_name,
        report_family=report_family,
        supported_filter_names=supported_filter_names,
        supported_filter_kinds=supported_filter_kinds_sorted,
    )
    primary_dimension = infer_primary_dimension(report_name)
    confidence, confidence_reasons = confidence_from_metadata(
        requirements_raw_type=requirements_raw_type,
        required_filter_names=required_filter_names,
        filters_definition=filter_rows,
    )

    gen_dt = parse_iso_utc(generated_at_utc)
    fresh_until_dt = gen_dt + timedelta(hours=max(1, int(freshness_hours)))
    now_dt = datetime.now(timezone.utc)
    age_seconds = max(0, int((now_dt - gen_dt).total_seconds()))
    fresh = now_dt <= fresh_until_dt

    row: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "report_name": report_name,
        "report_family": report_family,
        "report_type": report_type,
        "is_standard": is_standard,
        "disabled": disabled,
        "constraints": {
            "required_filter_names": required_filter_names,
            "supported_filter_names": sorted(list(dict.fromkeys(supported_filter_names))),
            "required_filter_kinds": required_filter_kinds_sorted,
            "supported_filter_kinds": supported_filter_kinds_sorted,
            "filters_definition": normalized_filter_defs,
            "required_filter_count": len(required_filter_names),
            "requirements_raw_type": requirements_raw_type,
            "requirements_unknown": requirements_unknown,
        },
        "time_support": time_support,
        "semantics": {
            "domain_hints": domain_hints,
            "dimension_hints": dimension_hints,
            "metric_hints": metric_hints,
            "primary_dimension": primary_dimension,
        },
        "metadata": {
            "generated_at_utc": gen_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "fresh_until_utc": fresh_until_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "age_seconds": age_seconds,
            "fresh": fresh,
            "confidence": confidence,
            "confidence_reasons": confidence_reasons,
            "source": {
                "catalog": "fac_report_list",
                "requirements": requirements_raw_type or "unknown",
            },
        },
        # Backward-compatible accessors used by existing resolver/read engine internals.
        "name": report_name,
        "module": report_family,
        "required_filter_names": required_filter_names,
        "requirements_raw_type": requirements_raw_type,
        "requirements_unknown": requirements_unknown,
        "supported_filter_kinds": supported_filter_kinds_sorted,
        "required_filter_kinds": required_filter_kinds_sorted,
        "domain_tags": domain_hints,
        "dimension_tags": dimension_hints,
        "metric_tags": metric_hints,
        "primary_dimension": primary_dimension,
    }
    row["metadata"]["fingerprint"] = make_capability_fingerprint(row)
    return row


def validate_capability_row(row: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(row, dict):
        return ["row_not_object"]

    if str(row.get("schema_version") or "") != SCHEMA_VERSION:
        errors.append("schema_version_invalid")
    if not str(row.get("report_name") or "").strip():
        errors.append("report_name_missing")
    if not isinstance(row.get("constraints"), dict):
        errors.append("constraints_missing")
    if not isinstance(row.get("time_support"), dict):
        errors.append("time_support_missing")
    if not isinstance(row.get("semantics"), dict):
        errors.append("semantics_missing")
    meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    if not meta:
        errors.append("metadata_missing")
    else:
        conf = meta.get("confidence")
        try:
            conf_f = float(conf)
        except Exception:
            conf_f = -1.0
        if conf_f < 0.0 or conf_f > 1.0:
            errors.append("confidence_out_of_range")
        if not str(meta.get("generated_at_utc") or "").strip():
            errors.append("generated_at_missing")
        if not str(meta.get("fresh_until_utc") or "").strip():
            errors.append("fresh_until_missing")
        if not str(meta.get("fingerprint") or "").strip():
            errors.append("fingerprint_missing")

    return errors
