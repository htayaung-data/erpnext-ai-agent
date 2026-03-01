from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ai_assistant_ui.ai_core.ontology_normalization import (
    canonical_metric,
    infer_filter_kinds,
    infer_transform_ambiguities,
)
from ai_assistant_ui.ai_core.util_dates import extract_timeframe, today_date

_DOC_ID_PATTERNS = (
    r"\b[A-Z]{2,}-[A-Z0-9]+-\d{4}-\d+\b",
    r"\b[A-Z]{2,}(?:-[A-Z0-9]{2,}){1,4}\b",
)


def merge_transform_ambiguities_into_spec(*, spec_obj: Dict[str, Any], message: str) -> List[str]:
    spec = spec_obj if isinstance(spec_obj, dict) else {}
    hints = [str(x).strip().lower() for x in list(infer_transform_ambiguities(message)) if str(x or "").strip()]
    if not hints:
        return []
    existing = [str(x).strip().lower() for x in list(spec.get("ambiguities") or []) if str(x or "").strip()]
    merged: List[str] = []
    seen = set()
    for value in existing + hints:
        if not value or value in seen:
            continue
        seen.add(value)
        merged.append(value)
    spec["ambiguities"] = merged[:12]
    return hints


def message_followup_semantic_strength(message: str) -> int:
    txt = str(message or "").strip()
    if not txt:
        return 0
    score = 0
    if str(canonical_metric(txt) or "").strip():
        score += 1
    as_of_date, date_range = extract_timeframe(txt, ref=today_date())
    if as_of_date is not None or date_range is not None:
        score += 1
    kinds = {
        str(x).strip().lower()
        for x in list(infer_filter_kinds(txt))
        if str(x).strip()
    }
    scoped_filter_kinds = {
        kind
        for kind in kinds
        if kind not in {"date", "from_date", "to_date", "report_date", "start_year", "end_year", "fiscal_year", "year"}
    }
    if scoped_filter_kinds:
        score += 1
    if re.search(r"\b(?:top|latest)\s+\d+\b", txt.lower()):
        score += 1
    if any(re.search(pattern, txt) for pattern in _DOC_ID_PATTERNS):
        score += 1
    return score


def should_promote_to_transform_followup(
    *,
    message: str,
    spec_obj: Dict[str, Any],
    memory_meta: Dict[str, Any],
    last_result_payload: Optional[Dict[str, Any]],
    has_report_table_rows: bool,
    wants_projection_followup: bool,
    has_explicit_time_scope: bool,
) -> bool:
    spec = spec_obj if isinstance(spec_obj, dict) else {}
    if str(spec.get("intent") or "").strip().upper() != "READ":
        return False
    if not has_report_table_rows:
        return False

    ambiguities = [str(x).strip().lower() for x in list(spec.get("ambiguities") or []) if str(x or "").strip()]
    has_transform_hint = any(a.startswith("transform_") for a in ambiguities)
    has_sort_direction_hint = any(a in {"transform_sort:asc", "transform_sort:desc"} for a in ambiguities)
    task_type = str(spec.get("task_type") or "").strip().lower()
    aggregation = str(spec.get("aggregation") or "").strip().lower()
    wants_aggregate = bool(task_type == "kpi" or aggregation in {"sum", "avg", "average", "count", "min", "max"})
    prior_output_mode = str((last_result_payload or {}).get("_output_mode") or "").strip().lower()

    mm = memory_meta if isinstance(memory_meta, dict) else {}
    anchors_applied = [str(x).strip() for x in list(mm.get("anchors_applied") or []) if str(x or "").strip()]
    try:
        curr_strength = int(mm.get("curr_strength") or 9)
    except Exception:
        curr_strength = 9
    try:
        overlap_ratio = float(mm.get("overlap_ratio") or 0.0)
    except Exception:
        overlap_ratio = 0.0

    weak_current_turn = curr_strength <= 2
    anchored_followup = bool(anchors_applied)
    short_followup_message = message_followup_semantic_strength(message) <= 2
    contextual_followup = anchored_followup or overlap_ratio >= 0.25
    fresh_time_scoped_read = has_explicit_time_scope and (not anchored_followup) and (not weak_current_turn)

    if fresh_time_scoped_read and (not has_transform_hint) and (not wants_projection_followup):
        return False
    if has_sort_direction_hint and prior_output_mode == "top_n":
        return False

    if has_transform_hint and (weak_current_turn or anchored_followup or (short_followup_message and contextual_followup)):
        return True
    if wants_aggregate and (anchored_followup or overlap_ratio >= 0.25) and (weak_current_turn or short_followup_message):
        return True
    if wants_projection_followup and (weak_current_turn or anchored_followup or (short_followup_message and contextual_followup)):
        return True
    return False


def promote_spec_to_transform_followup(
    *,
    spec_obj: Dict[str, Any],
    last_result_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    spec = dict(spec_obj or {})
    spec["intent"] = "TRANSFORM_LAST"
    spec["task_class"] = "transform_followup"
    prior_payload = last_result_payload if isinstance(last_result_payload, dict) else {}
    prior_output_mode = str(prior_payload.get("_output_mode") or "").strip().lower()
    prior_scaled_unit = str(prior_payload.get("_scaled_unit") or "").strip().lower()
    ambiguities = [str(x).strip().lower() for x in list(spec.get("ambiguities") or []) if str(x or "").strip()]
    scale_only_followup = bool(
        any(a == "transform_scale:million" for a in ambiguities)
        and (not any(a in {"transform_sort:asc", "transform_sort:desc"} for a in ambiguities))
    )
    task_type = str(spec.get("task_type") or "").strip().lower()
    if task_type not in {"kpi", "detail", "ranking"}:
        spec["task_type"] = "detail"
    if prior_output_mode in {"top_n", "detail"} and (scale_only_followup or prior_scaled_unit == "million"):
        spec["task_type"] = "ranking" if prior_output_mode == "top_n" else "detail"
        oc = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
        oc2 = dict(oc)
        oc2["mode"] = prior_output_mode
        spec["output_contract"] = oc2
    elif str(spec.get("task_type") or "").strip().lower() == "kpi":
        aggregation = str(spec.get("aggregation") or "").strip().lower()
        if aggregation in {"", "none"}:
            spec["aggregation"] = "sum"
    return spec
