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
    "CMP-01",
    "TRN-01",
    "STK-01",
    "STK-02",
    "STK-03",
    "HR-01",
    "OPS-01",
    "COR-01",
    "DET-01",
    "DOC-01",
    "LST-01",
    "CFG-02",
    "CFG-03",
    "EXP-01",
    "TEC-01",
    "TEC-02",
    "TEC-03",
    "TEC-04",
    "TEC-05",
    "TEC-06",
    "TEC-07",
    "TEC-08",
    "TES-01",
    "TES-02",
    "TES-03",
    "TES-04",
    "TES-05",
    "TES-06",
    "TES-07",
    "TES-08",
    "TEI-01",
    "TEI-02",
    "TEI-03",
    "TEI-04",
    "TEI-05",
    "TEI-06",
    "TEI-07",
    "TEI-08",
    "TEK-01",
    "TEK-02",
    "TEK-03",
    "TEK-04",
    "TEK-05",
    "TEK-06",
    "TEK-07",
    "TEK-08",
    "TEW-01",
    "TEW-02",
    "TEW-03",
    "TEW-04",
    "TEW-05",
    "TEW-06",
    "CSC-01",
    "CSC-02",
    "CSC-03",
    "CSC-04",
    "CSC-05",
    "CSC-06",
    "CSC-07",
    "CSC-08",
    "CSC-09",
    "CSC-10",
    "CSS-01",
    "CSS-02",
    "CSS-03",
    "CSS-04",
    "CSS-05",
    "CSS-06",
    "CSS-07",
    "CSS-08",
    "CSS-09",
    "CSS-10",
    "CSI-01",
    "CSI-02",
    "CSI-03",
    "CSI-04",
    "CSI-05",
    "CSI-06",
    "CSI-07",
    "CSI-08",
}

FILTER_CLAR_CASES = {"ENT-01", "ENT-02"}
SHAPE_ONLY_CASES = {
    "WR-01",
    "WR-02",
    "WR-03",
    "WR-04",
    "OBS-01",
    "OBS-02",
    "ERR-01",
    "CFG-01",
    "TEU-01",
    "TEU-02",
    "TEU-03",
    "TEU-04",
    "TEU-05",
    "TEU-06",
    "CSU-01",
    "CSU-02",
    "CSU-03",
    "CSU-04",
    "CSU-05",
    "CSU-06",
    "CSU-07",
    "CSU-08",
}

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
    return required_assertions_for_case_with_actual(case_id, {})


def _expected_behavior_class(actual: Dict[str, Any]) -> str:
    return str(actual.get("expected_behavior_class") or "").strip().lower()


def required_assertions_for_case_with_actual(case_id: str, actual: Dict[str, Any]) -> List[str]:
    behavior_class = _expected_behavior_class(actual)
    if case_id.startswith("CMPC-") and behavior_class:
        if behavior_class in {"comparison", "correction_rebind"}:
            return list(ASSERTION_KEYS)
        if behavior_class in {"transform_last_result", "clarification_blocker"}:
            return [
                "report_alignment_pass",
                "output_shape_pass",
                "clarification_policy_pass",
                "loop_policy_pass",
            ]
        if behavior_class == "error_envelope":
            return [
                "output_shape_pass",
                "clarification_policy_pass",
                "loop_policy_pass",
            ]
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


def _comparison_spec(actual: Dict[str, Any]) -> Dict[str, Any]:
    spec = actual.get("business_request_spec")
    return spec if isinstance(spec, dict) else {}


def _comparison_contract(actual: Dict[str, Any]) -> Dict[str, Any]:
    expected = actual.get("expected_manifest_expected")
    if not isinstance(expected, dict):
        return {}
    contract = expected.get("comparison_contract")
    return contract if isinstance(contract, dict) else {}


def _comparison_expected_title(actual: Dict[str, Any]) -> str:
    contract = _comparison_contract(actual)
    return _lower_text(contract.get("expected_title"))


def _comparison_shape_mode(actual: Dict[str, Any]) -> str:
    contract = _comparison_contract(actual)
    return _lower_text(contract.get("shape_mode"))


def _comparison_entity_count(actual: Dict[str, Any]) -> int:
    contract = _comparison_contract(actual)
    try:
        return int(contract.get("entity_count") or 0)
    except Exception:
        return 0


def _comparison_minimum_rows(actual: Dict[str, Any]) -> int:
    contract = _comparison_contract(actual)
    try:
        return int(contract.get("minimum_rows") or 0)
    except Exception:
        return 0


def _comparison_allow_single_row_with_labels(actual: Dict[str, Any]) -> bool:
    contract = _comparison_contract(actual)
    return bool(contract.get("allow_single_row_with_labels"))


def _comparison_required_label_groups(actual: Dict[str, Any]) -> List[List[str]]:
    contract = _comparison_contract(actual)
    groups = contract.get("required_label_groups")
    if not isinstance(groups, list):
        return []
    out: List[List[str]] = []
    for group in groups:
        if not isinstance(group, list):
            continue
        cleaned = [_lower_text(x) for x in group if _lower_text(x)]
        if cleaned:
            out.append(cleaned)
    return out


def _comparison_forbidden_label_groups(actual: Dict[str, Any]) -> List[List[str]]:
    contract = _comparison_contract(actual)
    groups = contract.get("forbidden_label_groups")
    if not isinstance(groups, list):
        return []
    out: List[List[str]] = []
    for group in groups:
        if not isinstance(group, list):
            continue
        cleaned = [_lower_text(x) for x in group if _lower_text(x)]
        if cleaned:
            out.append(cleaned)
    return out


def _label_groups_present(actual: Dict[str, Any], groups: List[List[str]]) -> bool:
    if not groups:
        return True
    labels = [_lower_text(x) for x in list(actual.get("column_labels") or []) if _lower_text(x)]
    if not labels:
        return False
    for group in groups:
        if not any(any(option in label for option in group) for label in labels):
            return False
    return True


def _label_groups_absent(actual: Dict[str, Any], groups: List[List[str]]) -> bool:
    if not groups:
        return True
    labels = [_lower_text(x) for x in list(actual.get("column_labels") or []) if _lower_text(x)]
    if not labels:
        return True
    for group in groups:
        if any(any(option in label for option in group) for label in labels):
            return False
    return True


def _comparison_report_alignment_ok(actual: Dict[str, Any]) -> bool:
    contract = _comparison_contract(actual)
    if not contract:
        return False
    expected_title = _comparison_expected_title(actual)
    if not expected_title:
        return True
    return _lower_text(actual.get("assistant_title")) == expected_title


def _comparison_output_shape_ok(actual: Dict[str, Any]) -> bool:
    contract = _comparison_contract(actual)
    if not contract:
        return False
    if _lower_text(actual.get("assistant_type")) != "report_table":
        return False
    try:
        rows = int(actual.get("rows") or 0)
    except Exception:
        rows = 0
    if rows <= 0:
        return False

    shape_mode = _comparison_shape_mode(actual)
    required_label_groups = _comparison_required_label_groups(actual)
    forbidden_label_groups = _comparison_forbidden_label_groups(actual)
    labels_ok = _label_groups_present(actual, required_label_groups) and _label_groups_absent(actual, forbidden_label_groups)

    if shape_mode == "row_count_equals_entity_count":
        entity_count = _comparison_entity_count(actual)
        if entity_count <= 0:
            return False
        return rows == entity_count and labels_ok

    if shape_mode == "side_by_side_entities":
        entity_count = _comparison_entity_count(actual)
        if entity_count <= 0:
            return False
        try:
            columns = int(actual.get("columns") or 0)
        except Exception:
            columns = 0
        return rows == 1 and columns == (entity_count + 1) and labels_ok

    if shape_mode == "period_comparison":
        minimum_rows = _comparison_minimum_rows(actual)
        if minimum_rows > 0 and rows >= minimum_rows and labels_ok:
            return True
        if rows == 1 and _comparison_allow_single_row_with_labels(actual) and labels_ok:
            return True
        return False

    return labels_ok


def _is_blocker_clarification(actual: Dict[str, Any]) -> bool:
    if not bool(actual.get("clarification")):
        return False
    pending_mode = str(actual.get("pending_mode") or "").strip().lower()
    pstate = actual.get("pending_state") if isinstance(actual.get("pending_state"), dict) else {}
    options = pstate.get("options") if isinstance(pstate.get("options"), list) else []
    clar_opts = pstate.get("clarification_options") if isinstance(pstate.get("clarification_options"), list) else []
    failed_ids = set(str(x).strip() for x in list(actual.get("quality_failed_check_ids") or []) if str(x).strip())

    if pending_mode == "need_filters":
        return True

    if pending_mode != "planner_clarify":
        return False

    blocker_ids = {
        "required_filter_missing",
        "time_scope_missing",
        "dimension_alignment_mismatch",
        "metric_alignment_mismatch",
        "unsupported_action_in_read_loop",
        "blocked_report_selected_again",
        "output_mode_mismatch",
    }
    if failed_ids & blocker_ids:
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
    expected_behavior_class = _expected_behavior_class(actual)
    is_cmp_family = case_id.startswith("CMPC-") and bool(expected_behavior_class)
    has_cmp_contract = bool(_comparison_contract(actual))
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

    if is_cmp_family and expected_behavior_class in {"comparison", "correction_rebind"}:
        assertions["dimension_alignment_pass"] = dim_pass
        assertions["metric_alignment_pass"] = metric_pass
        assertions["time_scope_alignment_pass"] = time_pass
        assertions["filter_alignment_pass"] = filter_pass
    elif case_id in FULL_SEMANTIC_CASES:
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
    if is_cmp_family and expected_behavior_class == "error_envelope":
        assertions["report_alignment_pass"] = None
    elif case_id in SHAPE_ONLY_CASES:
        assertions["report_alignment_pass"] = None
    else:
        report_pass = True
        if case_id in READ_LIKE_CASES or is_cmp_family:
            if assistant_type == "report_table":
                report_pass = True
            elif clarification and blocker_clar:
                report_pass = True
            else:
                report_pass = False
            if "unsupported_action_in_read_loop" in failed_ids or "blocked_report_selected_again" in failed_ids:
                report_pass = False
            if is_cmp_family and has_cmp_contract:
                report_pass = report_pass and _comparison_report_alignment_ok(actual)
        assertions["report_alignment_pass"] = report_pass

    # Output shape: respect quality gate failures and basic type sanity.
    if case_id in READ_LIKE_CASES or is_cmp_family:
        if assistant_type not in ("report_table", "text", "error"):
            output_pass = False
    else:
        if assistant_type not in ("report_table", "text", "error", "observe"):
            output_pass = False
    if case_id == "DOC-01" and assistant_type == "report_table" and rows <= 0:
        output_pass = False
    if is_cmp_family and expected_behavior_class in {"comparison", "correction_rebind"} and (not has_cmp_contract):
        assertions["report_alignment_pass"] = False
        output_pass = False
    elif is_cmp_family and has_cmp_contract:
        output_pass = output_pass and _comparison_output_shape_ok(actual)
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

    required = required_assertions_for_case_with_actual(case_id, actual)
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
