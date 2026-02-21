from __future__ import annotations

from typing import Any, Dict, List, Optional

ASSERTION_KEYS: List[str] = [
    "report_alignment_pass",
    "dimension_alignment_pass",
    "metric_alignment_pass",
    "time_scope_alignment_pass",
    "filter_alignment_pass",
    "output_shape_pass",
    "clarification_policy_pass",
    "loop_policy_pass",
]

ASSERTION_SHORT = {
    "report_alignment_pass": "R",
    "dimension_alignment_pass": "D",
    "metric_alignment_pass": "M",
    "time_scope_alignment_pass": "T",
    "filter_alignment_pass": "F",
    "output_shape_pass": "O",
    "clarification_policy_pass": "C",
    "loop_policy_pass": "L",
}

FULL_SEMANTIC_CASES = {
    "FIN-01",
    "FIN-02",
    "FIN-03",
    "FIN-04",
    "SAL-01",
    "SAL-02",
    "STK-01",
    "STK-02",
    "HR-01",
    "OPS-01",
    "COR-01",
    "DET-01",
    "DOC-01",
    "CFG-02",
    "CFG-03",
    "EXP-01",
}

FILTER_CLAR_CASES = {"ENT-01", "ENT-02"}
SHAPE_ONLY_CASES = {"WR-01", "WR-02", "WR-03", "WR-04", "OBS-01", "OBS-02", "ERR-01", "CFG-01"}

READ_LIKE_CASES = FULL_SEMANTIC_CASES | FILTER_CLAR_CASES

OUTPUT_FAIL_IDS = {
    "output_mode_mismatch",
    "kpi_shape_mismatch",
    "top_n_not_applied",
    "top_n_order_mismatch",
    "minimal_columns_missing",
}


def _lower_text(v: Any) -> str:
    return str(v or "").strip().lower()


def is_meta_clarification(text: str) -> bool:
    t = _lower_text(text)
    if not t:
        return False
    markers = (
        "should i prioritize",
        "prioritize the requested metric",
        "metric or grouping",
        "specify one concrete metric or grouping",
    )
    return any(m in t for m in markers)


def required_assertions_for_case(case_id: str) -> List[str]:
    if case_id in FULL_SEMANTIC_CASES:
        return list(ASSERTION_KEYS)
    if case_id in FILTER_CLAR_CASES:
        return [
            "report_alignment_pass",
            "filter_alignment_pass",
            "output_shape_pass",
            "clarification_policy_pass",
            "loop_policy_pass",
        ]
    if case_id in SHAPE_ONLY_CASES:
        return [
            "output_shape_pass",
            "clarification_policy_pass",
            "loop_policy_pass",
        ]
    return list(ASSERTION_KEYS)


def _failed_check_ids(actual: Dict[str, Any]) -> List[str]:
    gate = actual.get("result_quality_gate") if isinstance(actual.get("result_quality_gate"), dict) else {}
    failed = gate.get("failed_checks") if isinstance(gate.get("failed_checks"), list) else []
    out: List[str] = []
    for item in failed:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("id") or "").strip()
        if cid:
            out.append(cid)
    return out


def _is_blocker_clarification(actual: Dict[str, Any]) -> bool:
    if not bool(actual.get("clarification")):
        return False
    pending_mode = str(actual.get("pending_mode") or "").strip().lower()
    text = _lower_text(actual.get("assistant_text"))
    pstate = actual.get("pending_state") if isinstance(actual.get("pending_state"), dict) else {}
    options = pstate.get("options") if isinstance(pstate.get("options"), list) else []
    clar_opts = pstate.get("clarification_options") if isinstance(pstate.get("clarification_options"), list) else []

    if pending_mode == "need_filters":
        return True

    if pending_mode != "planner_clarify":
        return False

    markers = (
        "does not support",
        "can’t apply",
        "can't apply",
        "which exact value should i use",
        "multiple matches",
        "which one should i use",
        "switch to another compatible report",
        "should i switch",
    )
    if any(m in text for m in markers):
        return True

    if options and len(options) >= 2:
        return True
    if clar_opts and len(clar_opts) >= 2 and set(_lower_text(x) for x in clar_opts) != {"yes", "no"}:
        return True

    return False


def evaluate_case_assertions(case_id: str, actual: Dict[str, Any]) -> Dict[str, Any]:
    failed_ids = set(_failed_check_ids(actual))
    gate = actual.get("result_quality_gate") if isinstance(actual.get("result_quality_gate"), dict) else {}
    pending_state = actual.get("pending_state") if isinstance(actual.get("pending_state"), dict) else {}
    clarification = bool(actual.get("clarification"))
    meta = is_meta_clarification(str(actual.get("assistant_text") or ""))
    blocker_clar = _is_blocker_clarification(actual)
    assistant_type = str(actual.get("assistant_type") or "").strip().lower()
    pending_mode = str(actual.get("pending_mode") or "").strip().lower()
    rows = 0
    try:
        rows = int(actual.get("rows") or 0)
    except Exception:
        rows = 0

    assertions: Dict[str, Optional[bool]] = {k: None for k in ASSERTION_KEYS}

    # Base semantic checks from deterministic quality gate IDs.
    dim_pass = "dimension_alignment_mismatch" not in failed_ids
    metric_pass = "metric_alignment_mismatch" not in failed_ids
    time_pass = "time_scope_missing" not in failed_ids
    filter_pass = "required_filter_missing" not in failed_ids
    output_pass = (len(failed_ids & OUTPUT_FAIL_IDS) == 0)

    if case_id in FULL_SEMANTIC_CASES:
        assertions["dimension_alignment_pass"] = dim_pass
        assertions["metric_alignment_pass"] = metric_pass
        assertions["time_scope_alignment_pass"] = time_pass
        assertions["filter_alignment_pass"] = filter_pass
    elif case_id in FILTER_CLAR_CASES:
        assertions["dimension_alignment_pass"] = None
        assertions["metric_alignment_pass"] = None
        assertions["time_scope_alignment_pass"] = None
        assertions["filter_alignment_pass"] = filter_pass
    elif case_id in SHAPE_ONLY_CASES:
        assertions["dimension_alignment_pass"] = None
        assertions["metric_alignment_pass"] = None
        assertions["time_scope_alignment_pass"] = None
        assertions["filter_alignment_pass"] = None

    # Report alignment: either tabular execution succeeded, or clarification is a true blocker.
    if case_id in SHAPE_ONLY_CASES:
        assertions["report_alignment_pass"] = None
    else:
        report_pass = True
        if case_id in READ_LIKE_CASES:
            if assistant_type == "report_table":
                report_pass = True
            elif clarification and blocker_clar:
                report_pass = True
            else:
                report_pass = False
            if "unsupported_action_in_read_loop" in failed_ids or "blocked_report_selected_again" in failed_ids:
                report_pass = False
        assertions["report_alignment_pass"] = report_pass

    # Output shape: respect quality gate failures and basic type sanity.
    if case_id in READ_LIKE_CASES:
        if assistant_type not in ("report_table", "text", "error"):
            output_pass = False
    else:
        if assistant_type not in ("report_table", "text", "error", "observe"):
            output_pass = False
    if case_id == "DOC-01" and assistant_type == "report_table" and rows <= 0:
        output_pass = False
    assertions["output_shape_pass"] = output_pass

    # Clarification policy.
    if meta:
        clar_policy_pass = False
    elif case_id == "CFG-01":
        clar_policy_pass = bool(clarification and pending_mode == "planner_clarify")
    elif case_id == "WR-02":
        clar_policy_pass = bool(clarification and pending_mode == "write_confirmation")
    elif case_id in FILTER_CLAR_CASES:
        clar_policy_pass = bool(clarification and blocker_clar)
    elif clarification:
        clar_policy_pass = blocker_clar
    else:
        clar_policy_pass = True
    assertions["clarification_policy_pass"] = clar_policy_pass

    # Loop policy.
    clar_round = 0
    try:
        clar_round = int(pending_state.get("clarification_round") or 0)
    except Exception:
        clar_round = 0
    loop_pass = clar_round <= 1
    assertions["loop_policy_pass"] = loop_pass

    required = required_assertions_for_case(case_id)
    required_pass = True
    for key in required:
        val = assertions.get(key)
        if val is not True:
            required_pass = False
            break

    short_parts = []
    for key in ASSERTION_KEYS:
        tag = ASSERTION_SHORT[key]
        val = assertions.get(key)
        if val is True:
            short_parts.append(f"{tag}=PASS")
        elif val is False:
            short_parts.append(f"{tag}=FAIL")
        else:
            short_parts.append(f"{tag}=NA")

    return {
        "assertions": assertions,
        "required_assertions": required,
        "required_pass": required_pass,
        "summary": ", ".join(short_parts),
        "failed_check_ids": sorted(list(failed_ids)),
        "quality_verdict": str(gate.get("verdict") or ""),
        "meta_clarification": meta,
        "blocker_clarification": blocker_clar,
    }
