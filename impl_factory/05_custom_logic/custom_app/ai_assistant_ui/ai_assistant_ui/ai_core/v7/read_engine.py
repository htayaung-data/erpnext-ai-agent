from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover
    frappe = None

from ai_assistant_ui.ai_core.ontology_normalization import (
    canonical_metric,
    infer_filter_kinds,
    infer_output_flags,
    infer_record_doctype_candidates,
    infer_transform_ambiguities,
    infer_write_request,
    metric_domain,
)
try:
    from ai_assistant_ui.ai_core.tools_write import create_document, delete_document, update_document
except Exception:  # pragma: no cover
    def create_document(*args, **kwargs):
        raise RuntimeError("tools_write backend unavailable")

    def update_document(*args, **kwargs):
        raise RuntimeError("tools_write backend unavailable")

    def delete_document(*args, **kwargs):
        raise RuntimeError("tools_write backend unavailable")
from ai_assistant_ui.ai_core.v7.clarification_policy import evaluate_clarification, make_clarification_tool_message
from ai_assistant_ui.ai_core.v7.capability_registry import report_semantics_contract
from ai_assistant_ui.ai_core.v7.entity_resolution import resolve_entity_filters
from ai_assistant_ui.ai_core.v7.memory import (
    apply_memory_context,
    build_topic_state,
    get_topic_state,
    make_topic_state_tool_message,
)
from ai_assistant_ui.ai_core.v7.quality_gate import (
    VERDICT_HARD_FAIL,
    VERDICT_PASS,
    VERDICT_REPAIRABLE_FAIL,
    evaluate_quality_gate,
    make_quality_gate_tool_message,
)
from ai_assistant_ui.ai_core.v7.response_shaper import (
    format_numeric_values_for_display,
    make_response_shaper_tool_message,
    shape_response,
)
from ai_assistant_ui.ai_core.v7.resume_policy import (
    first_int_in_text as _resume_first_int_in_text,
    looks_like_scope_answer_text as _resume_looks_like_scope_answer_text,
    match_option_choice as _resume_match_option_choice,
    normalize_option_label as _resume_normalize_option_label,
    planner_option_actions as _resume_planner_option_actions,
    prepare_resume_from_pending as _resume_prepare_resume_from_pending,
    recover_latest_record_followup_spec as _resume_recover_latest_record_followup_spec,
)
from ai_assistant_ui.ai_core.v7.execution_loop_policy import (
    build_candidate_report_state as _loop_build_candidate_report_state,
    extract_auto_switch_pending as _loop_extract_auto_switch_pending,
    planner_plan as _loop_planner_plan,
    read_engine_tool_message as _loop_read_engine_tool_message,
    resolver_selected_step_trace as _loop_resolver_selected_step_trace,
)
from ai_assistant_ui.ai_core.v7.read_execution_runner import execute_read_loop as _runner_execute_read_loop
from ai_assistant_ui.ai_core.v7.session_result_state import (
    apply_active_result_meta as _state_apply_active_result_meta,
    capture_source_columns as _state_capture_source_columns,
    latest_active_result_meta as _state_latest_active_result_meta,
    load_last_result_payload as _state_load_last_result_payload,
)
from ai_assistant_ui.ai_core.v7.shaping_policy import (
    enrich_minimal_columns_from_report_metadata as _shape_enrich_minimal_columns_from_report_metadata,
    has_explicit_time_scope as _shape_has_explicit_time_scope,
    has_report_table_rows as _shape_has_report_table_rows,
    humanize_fieldname as _shape_humanize_fieldname,
    is_low_signal_read_spec as _shape_is_low_signal_read_spec,
    is_projection_followup_request as _shape_is_projection_followup_request,
    looks_like_system_error_text as _shape_looks_like_system_error_text,
    metadata_requested_columns as _shape_metadata_requested_columns,
    normalized_message_text as _shape_normalized_message_text,
    quality_has_repairable_failure_class as _shape_quality_has_repairable_failure_class,
    requested_minimal_columns as _shape_requested_minimal_columns,
    sanitize_user_payload as _shape_sanitize_user_payload,
    should_switch_candidate_on_repairable as _shape_should_switch_candidate_on_repairable,
    unsupported_message_from_spec as _shape_unsupported_message_from_spec,
)
from ai_assistant_ui.ai_core.v7.resolver_pipeline import make_resolver_tool_message, resolve_business_request
from ai_assistant_ui.ai_core.v7.spec_pipeline import generate_business_request_spec, make_spec_tool_message
from ai_assistant_ui.ai_core.v7.transform_last import apply_transform_last, make_transform_tool_message
from ai_assistant_ui.ai_core.v7.transform_followup_policy import (
    merge_transform_ambiguities_into_spec as _policy_merge_transform_ambiguities_into_spec,
    promote_spec_to_transform_followup as _policy_promote_spec_to_transform_followup,
    should_promote_to_transform_followup as _policy_should_promote_to_transform_followup,
)
from ai_assistant_ui.ai_core.v7.write_engine import (
    execute_write_flow,
    is_explicit_confirm,
    make_write_engine_tool_message,
)
from ai_assistant_ui.ai_core.v7.contract_registry import canonical_dimensions, default_clarification_question
try:
    from ai_assistant_ui.ai_core.tools.report_tools import run_fac_report
except Exception:  # pragma: no cover
    def run_fac_report(*args, **kwargs):
        raise RuntimeError("report_tools backend unavailable")
from ai_assistant_ui.ai_core.util_dates import extract_timeframe, today_date

_INTERNAL_RETRY_KEY = "__v7_internal_retry__"
_DOC_ID_PATTERNS = (
    r"\b[A-Z]{2,}-[A-Z0-9]+-\d{4}-\d+\b",       # ACC-SINV-2026-00013
    r"\b[A-Z]{2,}(?:-[A-Z0-9]{2,}){1,4}\b",     # SINV-0001, ACC-SINV-00013
)


def _as_payload(result: Any) -> Dict[str, Any]:
    if isinstance(result, dict):
        return dict(result)
    return {"type": "text", "text": str(result)}


def _append_tool_message(payload: Dict[str, Any], msg: str) -> Dict[str, Any]:
    out = dict(payload or {})
    msgs = list(out.get("_tool_messages") or [])
    msgs.append(str(msg))
    out["_tool_messages"] = msgs
    return out


def _safe_json_obj(raw: Any) -> Dict[str, Any]:
    s = str(raw or "").strip()
    if not (s.startswith("{") and s.endswith("}")):
        return {}
    try:
        obj = json.loads(s)
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _norm_text(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def _entity_filter_values_from_spec(spec_obj: Dict[str, Any]) -> Dict[str, str]:
    spec = spec_obj if isinstance(spec_obj, dict) else {}
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    entity_dims = {str(x).strip().lower() for x in list(canonical_dimensions() or set()) if str(x).strip()}
    out: Dict[str, str] = {}
    for k, v in filters.items():
        key_raw = str(k or "").strip()
        key = _norm_text(key_raw)
        val = str(v or "").strip()
        if not key or not val:
            continue
        inferred_kinds = {
            str(x).strip().lower()
            for x in list(infer_filter_kinds(key_raw))
            if str(x).strip()
        }
        if inferred_kinds & entity_dims:
            out[key] = val
    return out


def _row_matches_entity_value(row: Dict[str, Any], target_value: str) -> bool:
    t = _norm_text(target_value)
    if not t:
        return False
    for _, cell in (row or {}).items():
        c = _norm_text(cell)
        if not c:
            continue
        if t == c or t in c or c in t:
            return True
    return False


def _apply_requested_entity_row_filters(*, payload: Dict[str, Any], business_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce requested entity filter values on returned table rows when the backend report
    ignores/under-applies filters. Generalized by spec filters, not report name.
    """
    out = dict(payload or {})
    if str(out.get("type") or "").strip().lower() != "report_table":
        return out
    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    rows = table.get("rows") if isinstance(table.get("rows"), list) else []
    if not rows or not isinstance(rows[0], dict):
        return out

    entity_filters = _entity_filter_values_from_spec(business_spec)
    if not entity_filters:
        return out

    filtered_rows = list(rows)
    applied_keys: List[str] = []
    for k, target in entity_filters.items():
        matches = [r for r in filtered_rows if isinstance(r, dict) and _row_matches_entity_value(r, target)]
        if matches and len(matches) < len(filtered_rows):
            filtered_rows = matches
            applied_keys.append(k)

    if not applied_keys:
        return out

    out_table = dict(table)
    out_table["rows"] = filtered_rows
    out["table"] = out_table
    out["_entity_row_filter_applied"] = True
    out["_entity_row_filter_keys"] = applied_keys
    return out


def _latest_active_result_meta(session_doc: Any) -> Dict[str, Any]:
    return _state_latest_active_result_meta(session_doc=session_doc, safe_json_obj=_safe_json_obj)


def _apply_active_result_meta(payload: Dict[str, Any], *, active_result_meta: Dict[str, Any]) -> Dict[str, Any]:
    return _state_apply_active_result_meta(payload, active_result_meta=active_result_meta)


def _merge_pinned_filters_into_spec(*, spec_obj: Dict[str, Any], plan_seed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministically enforces filter values already resolved in a pending-flow turn.
    This prevents a resumed question from re-parsing back to the old ambiguous raw value.
    """
    spec = dict(spec_obj or {})
    plan = plan_seed if isinstance(plan_seed, dict) else {}
    pinned_task_class = str(plan.get("task_class") or "").strip().lower()
    if pinned_task_class:
        spec["task_class"] = pinned_task_class

    try:
        pinned_top_n = int(plan.get("top_n") or 0)
    except Exception:
        pinned_top_n = 0
    if pinned_top_n > 0:
        spec["top_n"] = pinned_top_n
        oc = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
        oc2 = dict(oc)
        oc2["mode"] = "top_n"
        spec["output_contract"] = oc2

    pinned_output_mode = str(plan.get("output_mode") or "").strip().lower()
    if pinned_output_mode:
        oc = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
        oc2 = dict(oc)
        oc2["mode"] = pinned_output_mode
        spec["output_contract"] = oc2

    pinned_min_cols = [str(x).strip() for x in list(plan.get("minimal_columns") or []) if str(x or "").strip()]
    if pinned_min_cols:
        oc = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
        oc2 = dict(oc)
        current = [str(x).strip() for x in list(oc2.get("minimal_columns") or []) if str(x or "").strip()]
        if not current:
            oc2["minimal_columns"] = pinned_min_cols[:12]
            spec["output_contract"] = oc2

    pinned = plan.get("filters") if isinstance(plan.get("filters"), dict) else {}
    if not pinned:
        return spec

    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    merged = dict(filters)
    for k, v in pinned.items():
        key = str(k or "").strip()
        if not key:
            continue
        if v is None:
            continue
        if isinstance(v, str) and (not v.strip()):
            continue
        merged[key] = v
    spec["filters"] = merged
    return spec


def _load_last_result_payload(*, session_name: Optional[str]) -> Optional[Dict[str, Any]]:
    return _state_load_last_result_payload(
        session_name=session_name,
        frappe_module=frappe,
        safe_json_obj=_safe_json_obj,
    )


def _legacy_path_unavailable_payload() -> Dict[str, Any]:
    return {
        "type": "text",
        "text": (
            "I couldn't reliably produce that result with the current V7 runtime path. "
            "Please refine the request (target report/filters), and I'll retry."
        ),
    }


def _write_not_enabled_payload() -> Dict[str, Any]:
    return {
        "type": "text",
        "text": "Write-actions are disabled in this environment. Please ask an administrator to enable them.",
    }


def _tutor_capability_payload() -> Dict[str, Any]:
    return {
        "type": "text",
        "text": (
            "I can help with ERP business analytics across sales, purchasing, inventory, "
            "receivables, and payables. Examples: top customers/products, outstanding amounts, "
            "aging, warehouse stock, trends by week/month, and invoice/detail lookups."
        ),
    }


def _is_write_enabled() -> bool:
    if frappe is None:
        return False
    try:
        raw = frappe.conf.get("ai_assistant_write_enabled")
    except Exception:
        raw = None
    s = str(raw or "").strip().lower()
    if s in {"1", "true", "yes", "on"}:
        return True
    # Config may change at runtime; fall back to current site_config.json.
    try:
        import json

        cfg_path = frappe.get_site_path("site_config.json")
        with open(cfg_path, "r", encoding="utf-8") as fh:
            cfg = json.load(fh) if cfg_path else {}
        s2 = str((cfg or {}).get("ai_assistant_write_enabled") or "").strip().lower()
        if s2 in {"1", "true", "yes", "on"}:
            return True
    except Exception:
        pass
    return False


def _write_execute_fn(draft: Dict[str, Any]) -> Dict[str, Any]:
    op = str(draft.get("operation") or "").strip().lower()
    doctype = str(draft.get("doctype") or "").strip()
    payload = draft.get("payload") if isinstance(draft.get("payload"), dict) else {}
    if op == "delete":
        name = str(payload.get("name") or payload.get("id") or "").strip()
        if not doctype or not name:
            raise ValueError("delete requires doctype and name")
        return delete_document(doctype=doctype, name=name)
    if op == "create":
        if not doctype:
            raise ValueError("create requires doctype")
        return create_document(doctype=doctype, data=payload, submit=False, validate_only=False)
    if op == "update":
        name = str(payload.get("name") or payload.get("id") or "").strip()
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        if not doctype or not name:
            raise ValueError("update requires doctype and name")
        return update_document(doctype=doctype, name=name, data=data)
    raise ValueError(f"unsupported write operation: {op}")


def _build_write_draft_payload(*, message: str, spec: Dict[str, Any], user: Optional[str]) -> Optional[Dict[str, Any]]:
    write_req = infer_write_request(message)
    if str(write_req.get("intent") or "").strip().upper() != "WRITE_DRAFT":
        return None
    doctype = str(write_req.get("doctype") or "").strip()
    operation = str(write_req.get("operation") or "").strip().lower()
    doc_id = str(write_req.get("document_id") or "").strip()
    if not doctype or operation not in {"create", "update", "delete"}:
        return None

    draft_payload: Dict[str, Any] = {}
    if operation in {"delete", "update"} and doc_id:
        draft_payload["name"] = doc_id
    if operation == "create" and doctype == "ToDo":
        draft_payload = {"description": str(message or "").strip(), "status": "Open"}

    pending = {
        "mode": "write_confirmation",
        "write_draft": {
            "doctype": doctype,
            "operation": operation,
            "payload": draft_payload,
            "summary": f"{operation} {doctype}".strip(),
            "requested_by": str(user or "").strip(),
        },
    }
    if operation == "delete" and doctype == "ToDo" and doc_id:
        text = f"Delete ToDo with ID {doc_id}? Reply **confirm** to execute or **cancel** to stop."
    else:
        text = f"Confirm {operation} {doctype}? Reply **confirm** to execute or **cancel** to stop."
    return {"type": "text", "text": text, "_pending_state": pending}


def _draft_operation(payload: Optional[Dict[str, Any]]) -> str:
    obj = payload if isinstance(payload, dict) else {}
    pending = obj.get("_pending_state") if isinstance(obj.get("_pending_state"), dict) else {}
    write_draft = pending.get("write_draft") if isinstance(pending.get("write_draft"), dict) else {}
    return str(write_draft.get("operation") or "").strip().lower()


def _handle_write_confirmation(*, message: str, pending: Dict[str, Any], source: str) -> Dict[str, Any]:
    if is_explicit_confirm(message) and (not _is_write_enabled()):
        out = _write_not_enabled_payload()
        out["_clear_pending_state"] = True
        tool_msg = make_write_engine_tool_message(tool=source, decision=message, output=out)
        return _append_tool_message(out, tool_msg)

    out = execute_write_flow(
        draft=pending,
        decision=message,
        execute_fn=_write_execute_fn,
    )
    # Normalize user-visible wording to deterministic contract strings.
    wd = pending.get("write_draft") if isinstance(pending.get("write_draft"), dict) else {}
    doctype = str(wd.get("doctype") or "").strip()
    operation = str(wd.get("operation") or "").strip().lower()
    payload = wd.get("payload") if isinstance(wd.get("payload"), dict) else {}
    doc_id = str(payload.get("name") or payload.get("id") or "").strip()

    txt = str(out.get("text") or "").strip().lower()
    if "cancel" in txt:
        out["text"] = "Write action canceled."
    elif "pending" in txt:
        out["text"] = "Please reply with confirm or cancel."
    elif ("executed successfully" in txt) or ("success" in txt):
        if operation == "delete" and doctype == "ToDo" and doc_id:
            out["text"] = f"Confirmed. Deleted **ToDo** `{doc_id}`."
        else:
            out["text"] = "Confirmed. Write action executed."

    tool_msg = make_write_engine_tool_message(tool=source, decision=message, output=out)
    return _append_tool_message(out, tool_msg)


def _execute_selected_report_direct(
    *,
    message: str,
    selected_report: str,
    business_spec: Dict[str, Any],
    export: bool,
    session_name: Optional[str],
    user: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Execute resolved report deterministically from the selected capability.
    """
    report_name = str(selected_report or "").strip()
    if not report_name:
        return None
    try:
        from ai_assistant_ui.ai_core.fac.requirements import get_report_requirements
    except Exception:
        return None

    spec = business_spec if isinstance(business_spec, dict) else {}
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    req_obj: Any = {}
    try:
        req_obj = get_report_requirements(report_name, user=user)
    except Exception:
        req_obj = {}
    filters = _apply_required_time_defaults(filters=dict(filters), req=req_obj, message=message)
    try:
        out = run_fac_report(
            report_name=report_name,
            filters=dict(filters),
            session_name=session_name,
            user=str(user or ""),
            export=bool(export),
        )
        if isinstance(out, dict) and not out.get("report_name"):
            out["report_name"] = report_name
        return _as_payload(out)
    except Exception:
        return None


def _req_filters_def(req: Any) -> List[Dict[str, Any]]:
    if isinstance(req, dict):
        rows = req.get("filters_definition") or []
    else:
        rows = getattr(req, "filters_definition", []) or []
    return [x for x in list(rows or []) if isinstance(x, dict)]


def _req_required_filter_names(req: Any) -> List[str]:
    if isinstance(req, dict):
        rows = req.get("required_filter_names") or []
    else:
        rows = getattr(req, "required_filter_names", []) or []
    out: List[str] = []
    for x in list(rows or []):
        s = str(x or "").strip()
        if s:
            out.append(s)
    return out


def _req_pick_fieldname(filters_def: List[Dict[str, Any]], required_names: List[str], aliases: List[str]) -> str:
    by_name = {str(fd.get("fieldname") or "").strip().lower(): str(fd.get("fieldname") or "").strip() for fd in filters_def}
    req_lc = {str(x or "").strip().lower() for x in list(required_names or []) if str(x or "").strip()}
    for a in aliases:
        a_lc = str(a or "").strip().lower()
        if not a_lc:
            continue
        if a_lc in by_name:
            return by_name[a_lc]
        if a_lc in req_lc:
            return str(a).strip()
    # Fallback to required name that loosely matches alias tokens.
    for rn in required_names:
        rn_s = str(rn or "").strip()
        rn_lc = rn_s.lower()
        if not rn_s:
            continue
        if any(a in rn_lc for a in [x.lower() for x in aliases]):
            return rn_s
    return ""


def _empty_filter_value(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str):
        return not bool(v.strip())
    if isinstance(v, (list, tuple, set, dict)):
        return len(v) == 0
    return False


def _year_from_str_date(s: Any) -> Optional[int]:
    txt = str(s or "").strip()
    if not txt:
        return None
    m = re.match(r"^(\d{4})-\d{2}-\d{2}$", txt)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def _default_fiscal_year_name(ref_date) -> str:
    if frappe is None:
        return ""
    try:
        rows = frappe.get_all(
            "Fiscal Year",
            filters={
                "year_start_date": ["<=", ref_date.isoformat()],
                "year_end_date": [">=", ref_date.isoformat()],
            },
            fields=["name", "year_start_date"],
            limit=1,
            order_by="year_start_date desc",
        )
        if rows and isinstance(rows[0], dict):
            return str(rows[0].get("name") or "").strip()
    except Exception:
        pass
    try:
        rows = frappe.get_all("Fiscal Year", fields=["name"], limit=1, order_by="modified desc")
        if rows and isinstance(rows[0], dict):
            return str(rows[0].get("name") or "").strip()
    except Exception:
        pass
    return ""


def _apply_required_time_defaults(*, filters: Dict[str, Any], req: Any, message: str) -> Dict[str, Any]:
    """
    Preflight materialization for required temporal fields that are not directly
    represented in natural prompts (e.g. start_year/end_year).
    """
    out = dict(filters or {})
    filters_def = _req_filters_def(req)
    required_names = _req_required_filter_names(req)
    if not required_names:
        return out

    as_of_date, dr = extract_timeframe(str(message or ""), ref=today_date())
    base_year = today_date().year
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    if dr is not None:
        start_year = int(dr.start.year)
        end_year = int(dr.end.year)
    elif as_of_date is not None:
        start_year = int(as_of_date.year)
        end_year = int(as_of_date.year)

    # Backfill from existing explicit date filters if present.
    if start_year is None:
        for k in ("from_date", "start_date", "posting_date", "report_date", "to_date", "date"):
            yy = _year_from_str_date(out.get(k))
            if yy is not None:
                start_year = yy
                break
    if end_year is None:
        for k in ("to_date", "report_date", "posting_date", "from_date", "date"):
            yy = _year_from_str_date(out.get(k))
            if yy is not None:
                end_year = yy
                break

    # If only one side known, mirror it.
    if (start_year is None) and (end_year is not None):
        start_year = end_year
    if (end_year is None) and (start_year is not None):
        end_year = start_year
    if start_year is None:
        start_year = base_year
    if end_year is None:
        end_year = base_year

    # Explicit year filters (several naming conventions).
    start_year_key = _req_pick_fieldname(filters_def, required_names, ["start_year", "from_year"])
    end_year_key = _req_pick_fieldname(filters_def, required_names, ["end_year", "to_year"])
    year_key = _req_pick_fieldname(filters_def, required_names, ["year"])

    if start_year_key and _empty_filter_value(out.get(start_year_key)):
        out[start_year_key] = int(start_year)
    if end_year_key and _empty_filter_value(out.get(end_year_key)):
        out[end_year_key] = int(end_year)
    if year_key and _empty_filter_value(out.get(year_key)):
        out[year_key] = int(end_year)

    # Explicit fiscal year filters.
    fiscal_year_key = _req_pick_fieldname(filters_def, required_names, ["fiscal_year"])
    from_fy_key = _req_pick_fieldname(filters_def, required_names, ["from_fiscal_year", "fiscal_year_from"])
    to_fy_key = _req_pick_fieldname(filters_def, required_names, ["to_fiscal_year", "fiscal_year_to"])
    fy_value = _default_fiscal_year_name(today_date())
    if fy_value:
        if fiscal_year_key and _empty_filter_value(out.get(fiscal_year_key)):
            out[fiscal_year_key] = fy_value
        if from_fy_key and _empty_filter_value(out.get(from_fy_key)):
            out[from_fy_key] = fy_value
        if to_fy_key and _empty_filter_value(out.get(to_fy_key)):
            out[to_fy_key] = fy_value

    # Fill required company from user/system defaults when omitted.
    company_key = _req_pick_fieldname(filters_def, required_names, ["company", "company_name"])
    if company_key and _empty_filter_value(out.get(company_key)) and (frappe is not None):
        default_company = ""
        try:
            default_company = str((frappe.defaults.get_user_default("Company") or "")).strip()
        except Exception:
            default_company = ""
        if not default_company:
            try:
                rows = frappe.get_all("Company", fields=["name"], limit=1, order_by="modified desc")
                if rows and isinstance(rows[0], dict):
                    default_company = str(rows[0].get("name") or "").strip()
            except Exception:
                default_company = ""
        if default_company:
            out[company_key] = default_company

    return out


def _read_engine_tool_message(
    *,
    source_tool: str,
    mode: str,
    selected_report: str,
    selected_score: Any,
    max_steps: int,
    executed_steps: int,
    repeated_call_guard_triggered: bool,
    repair_attempts: int,
    quality_verdict: str,
    failed_check_ids: List[str],
    step_trace: List[Dict[str, Any]],
) -> str:
    return _loop_read_engine_tool_message(
        source_tool=source_tool,
        mode=mode,
        selected_report=selected_report,
        selected_score=selected_score,
        max_steps=max_steps,
        executed_steps=executed_steps,
        repeated_call_guard_triggered=repeated_call_guard_triggered,
        repair_attempts=repair_attempts,
        quality_verdict=quality_verdict,
        failed_check_ids=failed_check_ids,
        step_trace=step_trace,
    )


def _planner_plan(*, export: bool, pending_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return _loop_planner_plan(export=export, pending_state=pending_state)


def _quality_has_repairable_failure_class(quality: Dict[str, Any], classes: List[str]) -> bool:
    return _shape_quality_has_repairable_failure_class(quality, classes)


def _should_switch_candidate_on_repairable(
    *,
    quality: Dict[str, Any],
    intent: str,
    task_class: str,
    candidate_cursor: int,
    candidate_reports: List[str],
    candidate_switch_attempts: int,
) -> bool:
    return _shape_should_switch_candidate_on_repairable(
        quality=quality,
        intent=intent,
        task_class=task_class,
        candidate_cursor=candidate_cursor,
        candidate_reports=candidate_reports,
        candidate_switch_attempts=candidate_switch_attempts,
    )


def _normalize_option_label(value: str) -> str:
    return _resume_normalize_option_label(value)


def _match_option_choice(message: str, options: List[str]) -> str:
    return _resume_match_option_choice(message, options)


def _planner_option_actions(*, options: List[str], pending: Dict[str, Any]) -> Dict[str, str]:
    return _resume_planner_option_actions(options=options, pending=pending)


def _looks_like_scope_answer_text(text: str) -> bool:
    return _resume_looks_like_scope_answer_text(text)


def _first_int_in_text(text: str) -> int:
    return _resume_first_int_in_text(text)


def _recover_latest_record_followup_spec(
    *,
    spec_obj: Dict[str, Any],
    message: str,
    previous_topic_state: Dict[str, Any],
) -> Dict[str, Any]:
    return _resume_recover_latest_record_followup_spec(
        spec_obj=spec_obj,
        message=message,
        previous_topic_state=previous_topic_state,
        resolve_record_doctype_candidates=lambda msg, spec: _resolve_record_doctype_candidates(message=msg, spec=spec),
        resolve_explicit_doctype_name=_resolve_explicit_doctype_name,
        load_submittable_doctypes=_load_submittable_doctypes,
    )


def _has_actionable_spec_signal(spec: Dict[str, Any]) -> bool:
    s = spec if isinstance(spec, dict) else {}
    if str(s.get("intent") or "").strip().upper() in {"WRITE_DRAFT", "WRITE_CONFIRM", "TRANSFORM_LAST"}:
        return True
    if str(s.get("subject") or "").strip():
        return True
    if str(s.get("metric") or "").strip():
        return True
    if isinstance(s.get("filters"), dict) and bool(s.get("filters")):
        return True
    if list(s.get("dimensions") or []):
        return True
    if list(s.get("group_by") or []):
        return True
    if int(s.get("top_n") or 0) > 0:
        return True
    ts = s.get("time_scope") if isinstance(s.get("time_scope"), dict) else {}
    if str(ts.get("mode") or "").strip().lower() not in {"", "none"}:
        return True
    return False


def _is_new_business_request_structured(*, message: str, session_name: Optional[str]) -> bool:
    msg = str(message or "").strip()
    if not msg:
        return False
    try:
        parsed = generate_business_request_spec(
            message=msg,
            session_name=session_name,
            planner_plan={"action": "run_report"},
        )
    except Exception:
        return False
    spec = parsed.get("spec") if isinstance(parsed.get("spec"), dict) else {}
    return _has_actionable_spec_signal(spec)


def _prepare_resume_from_pending(
    *,
    message: str,
    pending: Dict[str, Any],
    session_name: Optional[str] = None,
) -> Dict[str, Any]:
    return _resume_prepare_resume_from_pending(
        message=message,
        pending=pending,
        session_name=session_name,
        is_new_business_request_structured=lambda msg, sess: _is_new_business_request_structured(message=msg, session_name=sess),
        resolve_record_doctype_candidates=lambda msg, spec: _resolve_record_doctype_candidates(message=msg, spec=spec),
        resolve_explicit_doctype_name=_resolve_explicit_doctype_name,
        load_submittable_doctypes=_load_submittable_doctypes,
        default_clarification_question_fn=default_clarification_question,
    )


def _extract_document_id_from_spec(spec: Dict[str, Any]) -> str:
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    for _, v in filters.items():
        s = str(v or "").strip()
        if not s:
            continue
        for rx in _DOC_ID_PATTERNS:
            m = re.search(rx, s.upper())
            if m:
                return str(m.group(0) or "").strip()
    return ""


def _detect_doc_doctype(spec: Dict[str, Any], doc_id: str) -> str:
    did = str(doc_id or "").strip().upper()
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    fkeys = {str(k or "").strip().lower() for k in list(filters.keys())}
    if ("sales_invoice" in fkeys) or ("invoice" in fkeys) or ("SINV" in did):
        return "Sales Invoice"
    if ("purchase_invoice" in fkeys) or ("bill" in fkeys) or ("PINV" in did):
        return "Purchase Invoice"
    return ""


@lru_cache(maxsize=1)
def _load_submittable_doctypes() -> List[str]:
    if frappe is None:
        return []
    rows: List[Dict[str, Any]] = []
    try:
        rows = frappe.get_all(
            "DocType",
            fields=["name"],
            filters={"istable": 0, "issingle": 0, "is_submittable": 1},
            order_by="name asc",
            limit_page_length=2000,
        )
    except Exception:
        rows = []
    if not rows:
        try:
            rows = frappe.get_all(
                "DocType",
                fields=["name"],
                filters={"istable": 0, "issingle": 0},
                order_by="name asc",
                limit_page_length=2000,
            )
        except Exception:
            rows = []
    out: List[str] = []
    seen = set()
    for row in list(rows or []):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        k = name.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(name)
    return out


def _resolve_explicit_doctype_name(value: str) -> str:
    typed = str(value or "").strip()
    if not typed:
        return ""
    typed_l = typed.lower()
    for dt in _load_submittable_doctypes():
        name = str(dt or "").strip()
        if name and name.lower() == typed_l:
            return name
    return typed


def _resolve_record_doctype_candidates(*, message: str, spec: Dict[str, Any]) -> List[str]:
    doctypes = [d for d in _load_submittable_doctypes() if str(d or "").strip()]
    if not doctypes:
        return []
    txt = str(message or "").strip()
    subj = str(spec.get("subject") or "").strip().lower()
    metric = str(spec.get("metric") or "").strip().lower()
    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}

    query_chunks: List[str] = [txt, subj, metric]
    for fk, fv in list(filters.items()):
        fk_l = str(fk or "").strip().lower()
        if any(t in fk_l for t in ("doctype", "record", "voucher")):
            query_chunks.append(str(fv or "").strip())
    domain = str(spec.get("domain") or "").strip().lower()
    if domain in {"", "unknown", "cross_functional"}:
        metric_hint = metric or str(canonical_metric(txt) or "").strip().lower()
        if metric_hint:
            domain = str(metric_domain(metric_hint) or "").strip().lower()
    return infer_record_doctype_candidates(
        query_parts=query_chunks,
        candidate_doctypes=doctypes,
        domain=domain,
    )


@lru_cache(maxsize=64)
def _doctype_field_names(doctype: str) -> List[str]:
    dt = str(doctype or "").strip()
    if not dt or (frappe is None):
        return []
    try:
        meta = frappe.get_meta(dt)
    except Exception:
        return []
    fields: List[str] = ["name"]
    for f in list(getattr(meta, "fields", []) or []):
        fname = str(getattr(f, "fieldname", "") or "").strip()
        if fname:
            fields.append(fname)
    out: List[str] = []
    seen = set()
    for f in fields:
        k = f.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(f)
    return out


def _pick_existing_field(field_names: List[str], candidates: List[str]) -> str:
    lowered = {str(f or "").strip().lower(): str(f or "").strip() for f in list(field_names or []) if str(f or "").strip()}
    for cand in list(candidates or []):
        c = str(cand or "").strip().lower()
        if c and c in lowered:
            return lowered[c]
    return ""


def _extract_record_limit(*, spec: Dict[str, Any], message: str) -> int:
    try:
        top_n = int(spec.get("top_n") or 0)
    except Exception:
        top_n = 0
    if top_n > 0:
        return max(1, min(top_n, 200))
    # Do not parse lexical latest/recent terms in core runtime; rely on parser top_n.
    return 20


def _direct_latest_records_payload(spec: Dict[str, Any], *, message: str = "") -> Optional[Dict[str, Any]]:
    if frappe is None:
        return None
    task_class = str(spec.get("task_class") or "").strip().lower()
    if task_class not in {"list_latest_records", "detail_projection"}:
        return None
    if str(spec.get("intent") or "READ").strip().upper() != "READ":
        return None

    filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
    doctype = ""
    explicit_dt = ""
    for k, v in list(filters.items()):
        key = str(k or "").strip().lower()
        if key in {"doctype", "document_type", "record_type", "voucher_type"}:
            explicit_dt = str(v or "").strip()
            if explicit_dt:
                break
    if explicit_dt:
        doctype = _resolve_explicit_doctype_name(explicit_dt)
    if not doctype:
        candidates = _resolve_record_doctype_candidates(message=message, spec=spec)
        if len(candidates) != 1:
            return None
        doctype = str(candidates[0] or "").strip()
    if not doctype:
        return None

    field_names = _doctype_field_names(doctype)
    if not field_names:
        return None

    date_field = _pick_existing_field(
        field_names,
        ["posting_date", "transaction_date", "bill_date", "date", "modified", "creation"],
    )
    amount_field = _pick_existing_field(
        field_names,
        ["grand_total", "base_grand_total", "rounded_total", "net_total", "base_net_total", "outstanding_amount", "paid_amount", "total"],
    )
    party_field = _pick_existing_field(field_names, ["customer", "supplier", "party"])
    company_field = _pick_existing_field(field_names, ["company"])
    status_field = _pick_existing_field(field_names, ["status", "docstatus"])

    fields: List[str] = []
    for fn in ["name", date_field, party_field, amount_field, company_field, status_field]:
        s = str(fn or "").strip()
        if not s:
            continue
        if s not in fields:
            fields.append(s)
    if "name" not in fields:
        fields.insert(0, "name")

    query_filters: Dict[str, Any] = {}
    field_lower_map = {str(f).strip().lower(): str(f).strip() for f in fields + field_names}
    for k, v in list(filters.items()):
        key = str(k or "").strip().lower()
        if not key:
            continue
        mapped = field_lower_map.get(key) or field_lower_map.get(key.replace(" ", "_"))
        if mapped and str(v or "").strip():
            query_filters[mapped] = v

    if date_field:
        as_of_date, dr = extract_timeframe(str(message or ""), ref=today_date())
        if dr is not None:
            query_filters[date_field] = ["between", [dr.start_str, dr.end_str]]
        elif as_of_date is not None:
            query_filters[date_field] = as_of_date.isoformat()

    limit = _extract_record_limit(spec=spec, message=message)
    order_fields = [f for f in [date_field, "modified", "creation"] if str(f or "").strip()]
    order_by = ", ".join([f"{f} desc" for f in order_fields]) if order_fields else "modified desc"

    try:
        rows = frappe.get_all(
            doctype,
            filters=query_filters,
            fields=fields,
            order_by=order_by,
            limit_page_length=limit,
        )
    except Exception:
        return None
    data_rows = [r for r in list(rows or []) if isinstance(r, dict)]

    output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
    minimal_columns = [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x or "").strip()]
    alias_sources: Dict[str, str] = {}
    for col in minimal_columns:
        col_norm = col.replace(" ", "_")
        alias_name = col_norm or col
        if col_norm in {"invoice_number", "voucher_number", "document_number", "record_number"} and ("name" in fields):
            alias_sources[alias_name] = "name"
            continue
        if ("number" in col_norm or col_norm.endswith("_id")) and ("name" in fields):
            alias_sources[alias_name] = "name"
            continue
        if col_norm in {"total_amount", "amount", "value"} and amount_field:
            alias_sources[alias_name] = amount_field
            continue
        if amount_field and any(tok in col_norm for tok in ("amount", "revenue", "value", "total")):
            alias_sources[alias_name] = amount_field
            continue
    if alias_sources:
        for row in data_rows:
            if not isinstance(row, dict):
                continue
            for alias_name, src in alias_sources.items():
                if alias_name in row:
                    continue
                row[alias_name] = row.get(src)
        for alias_name in alias_sources.keys():
            if alias_name not in fields:
                fields.append(alias_name)

    number_label = f"{doctype} Number"
    columns: List[Dict[str, Any]] = []
    for fn in fields:
        label = fn.replace("_", " ").title()
        fieldtype = "Data"
        if fn == "name":
            label = number_label
        if fn in alias_sources:
            label = fn.replace("_", " ").title()
        if fn == date_field:
            fieldtype = "Date"
        elif fn == amount_field:
            fieldtype = "Currency"
        elif fn in {"total_amount", "amount", "value"}:
            fieldtype = "Currency"
        elif fn == "docstatus":
            fieldtype = "Int"
        columns.append({"fieldname": fn, "label": label, "fieldtype": fieldtype})

    return {
        "type": "report_table",
        "report_name": doctype,
        "title": f"Latest {doctype}",
        "_direct_latest_records_lookup": True,
        "table": {
            "columns": columns,
            "rows": data_rows,
        },
    }


def _doc_get(doc: Any, key: str, default: Any = None) -> Any:
    if isinstance(doc, dict):
        return doc.get(key, default)
    try:
        return getattr(doc, key, default)
    except Exception:
        return default


def _direct_document_lookup_payload(spec: Dict[str, Any], *, message: str = "") -> Optional[Dict[str, Any]]:
    """
    Deterministic document-detail path for explicit document-id asks.
    This avoids report drift for invoice-detail retrieval.
    """
    if frappe is None:
        return None
    doc_id = _extract_document_id_from_spec(spec)
    if (not doc_id) and str(message or "").strip():
        msg_u = str(message or "").upper()
        for rx in _DOC_ID_PATTERNS:
            m_doc = re.search(rx, msg_u)
            if m_doc:
                doc_id = str(m_doc.group(0) or "").strip()
                break
    if not doc_id:
        return None
    doctype = _detect_doc_doctype(spec, doc_id)
    if not doctype:
        return None
    try:
        doc = frappe.get_doc(doctype, doc_id)
    except Exception:
        return {"type": "text", "text": f"No records found for document {doc_id}."}

    party_field = "customer" if doctype == "Sales Invoice" else "supplier"
    party_value = str(_doc_get(doc, party_field, "") or "").strip()
    posting_date = str(_doc_get(doc, "posting_date", "") or "").strip()
    grand_total = 0.0
    try:
        grand_total = float(_doc_get(doc, "grand_total", 0.0) or 0.0)
    except Exception:
        grand_total = 0.0
    outstanding = 0.0
    try:
        outstanding = float(_doc_get(doc, "outstanding_amount", 0.0) or 0.0)
    except Exception:
        outstanding = 0.0
    rows = []
    for it in list(_doc_get(doc, "items", []) or []):
        qty = 0.0
        amt = 0.0
        try:
            qty = float(_doc_get(it, "qty", 0.0) or 0.0)
        except Exception:
            qty = 0.0
        try:
            amt = float(_doc_get(it, "amount", 0.0) or 0.0)
        except Exception:
            amt = 0.0
        rows.append(
            {
                "invoice": doc_id,
                "invoice_number": doc_id,
                party_field: party_value,
                "posting_date": posting_date,
                "grand_total": grand_total,
                "item_code": str(_doc_get(it, "item_code", "") or "").strip(),
                "qty": qty,
                "amount": amt,
                "outstanding_amount": outstanding,
            }
        )
    if not rows:
        rows.append(
            {
                "invoice": doc_id,
                "invoice_number": doc_id,
                party_field: party_value,
                "posting_date": posting_date,
                "grand_total": grand_total,
                "item_code": "",
                "qty": 0.0,
                "amount": 0.0,
                "outstanding_amount": outstanding,
            }
        )
    return {
        "type": "report_table",
        "report_name": doctype,
        "title": f"{doctype} Details",
        "_direct_document_lookup": True,
        "table": {
            "columns": [
                {"fieldname": "invoice", "label": "Invoice"},
                {"fieldname": "invoice_number", "label": "Invoice Number"},
                {"fieldname": party_field, "label": party_field.replace("_", " ").title()},
                {"fieldname": "posting_date", "label": "Posting Date"},
                {"fieldname": "grand_total", "label": "Grand Total", "fieldtype": "Currency"},
                {"fieldname": "item_code", "label": "Item Code"},
                {"fieldname": "qty", "label": "Qty", "fieldtype": "Float"},
                {"fieldname": "amount", "label": "Amount", "fieldtype": "Currency"},
                {"fieldname": "outstanding_amount", "label": "Outstanding Amount", "fieldtype": "Currency"},
            ],
            "rows": rows,
        },
    }


def _extract_auto_switch_pending(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return _loop_extract_auto_switch_pending(payload)


def _looks_like_system_error_text(payload: Dict[str, Any]) -> bool:
    return _shape_looks_like_system_error_text(payload)


def _unsupported_message_from_spec(spec: Dict[str, Any]) -> str:
    return _shape_unsupported_message_from_spec(spec)


def _is_low_signal_read_spec(spec: Dict[str, Any]) -> bool:
    return _shape_is_low_signal_read_spec(spec)


def _has_explicit_time_scope(spec: Dict[str, Any]) -> bool:
    return _shape_has_explicit_time_scope(spec)


def _requested_minimal_columns(spec: Dict[str, Any]) -> List[str]:
    return _shape_requested_minimal_columns(spec)


def _normalized_message_text(message: str) -> str:
    return _shape_normalized_message_text(message)


def _humanize_fieldname(fieldname: str) -> str:
    return _shape_humanize_fieldname(fieldname)


def _metadata_requested_columns(
    *,
    message: str,
    selected_report: str,
    last_result_payload: Optional[Dict[str, Any]],
) -> List[str]:
    return _shape_metadata_requested_columns(
        message=message,
        selected_report=selected_report,
        last_result_payload=last_result_payload,
    )


def _enrich_minimal_columns_from_report_metadata(
    *,
    spec_obj: Dict[str, Any],
    message: str,
    selected_report: str,
    last_result_payload: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    return _shape_enrich_minimal_columns_from_report_metadata(
        spec_obj=spec_obj,
        message=message,
        selected_report=selected_report,
        last_result_payload=last_result_payload,
    )


def _is_projection_followup_request(spec: Dict[str, Any]) -> bool:
    return _shape_is_projection_followup_request(spec)


def _has_report_table_rows(payload: Optional[Dict[str, Any]]) -> bool:
    return _shape_has_report_table_rows(payload)


def _merge_transform_ambiguities_into_spec(*, spec_obj: Dict[str, Any], message: str) -> List[str]:
    return _policy_merge_transform_ambiguities_into_spec(spec_obj=spec_obj, message=message)


def _should_promote_to_transform_followup(
    *,
    message: str,
    spec_obj: Dict[str, Any],
    memory_meta: Dict[str, Any],
    last_result_payload: Optional[Dict[str, Any]],
) -> bool:
    spec = spec_obj if isinstance(spec_obj, dict) else {}
    return _policy_should_promote_to_transform_followup(
        message=message,
        spec_obj=spec,
        memory_meta=memory_meta,
        last_result_payload=last_result_payload,
        has_report_table_rows=_has_report_table_rows(last_result_payload),
        wants_projection_followup=_is_projection_followup_request(spec),
        has_explicit_time_scope=_has_explicit_time_scope(spec),
    )


def _promote_spec_to_transform_followup(
    *,
    spec_obj: Dict[str, Any],
    last_result_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _policy_promote_spec_to_transform_followup(
        spec_obj=spec_obj,
        last_result_payload=last_result_payload,
    )


def _sanitize_user_payload(*, payload: Dict[str, Any], business_spec: Dict[str, Any]) -> Dict[str, Any]:
    return _shape_sanitize_user_payload(payload=payload, business_spec=business_spec)


def _capture_source_columns(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _state_capture_source_columns(payload)


def execute_read_plan(*, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backward-compatible wrapper.
    """
    return execute_unified_read_turn(
        message=str((context or {}).get("message") or ""),
        session_name=(context or {}).get("session_name"),
        user=(context or {}).get("user"),
        export=bool((context or {}).get("export")),
        pending_state=(context or {}).get("pending_state") if isinstance((context or {}).get("pending_state"), dict) else None,
        source_tool=str((context or {}).get("source_tool") or "report_qa_start"),
    )


def execute_unified_read_turn(
    *,
    message: str,
    session_name: Optional[str],
    user: Optional[str],
    export: bool = False,
    pending_state: Optional[Dict[str, Any]] = None,
    source_tool: str = "report_qa_start",
    max_steps: int = 5,
) -> Dict[str, Any]:
    """
    Phase-6 unified read execution path:
    - one shared engine for start/continue
    - deterministic quality gate and loop guards
    - topic-state memory with follow-up anchors and correction handling
    """
    pending = pending_state if isinstance(pending_state, dict) else {}
    source = str(source_tool or "").strip() or "report_qa_start"
    mode = "continue" if source == "report_qa_continue" else "start"

    if mode == "continue" and isinstance(pending, dict):
        if str(pending.get("mode") or "").strip().lower() == "write_confirmation":
            return _handle_write_confirmation(message=message, pending=pending, source=source)

    clear_pending_on_success = False
    plan_seed_override: Optional[Dict[str, Any]] = None
    if mode == "continue" and pending:
        pending_resume = _prepare_resume_from_pending(message=message, pending=pending, session_name=session_name)
        if isinstance(pending_resume.get("payload"), dict):
            return dict(pending_resume.get("payload") or {})
        if bool(pending_resume.get("active")):
            message = str(pending_resume.get("resume_message") or message).strip()
            source = str(pending_resume.get("source") or "report_qa_start").strip() or "report_qa_start"
            mode = "continue" if source == "report_qa_continue" else "start"
            plan_seed_override = pending_resume.get("plan_seed") if isinstance(pending_resume.get("plan_seed"), dict) else None
            clear_pending_on_success = bool(pending_resume.get("clear_pending"))
            pending = {}

    export_requested = bool(export)
    plan_seed = _planner_plan(export=export_requested, pending_state=pending)
    if isinstance(plan_seed_override, dict):
        plan_seed = dict(plan_seed_override)

    spec_envelope = generate_business_request_spec(
        message=message,
        session_name=session_name,
        planner_plan=plan_seed,
    )
    spec_obj = spec_envelope.get("spec") if isinstance(spec_envelope.get("spec"), dict) else {}
    raw_spec_obj = dict(spec_obj)
    if not str(spec_obj.get("task_class") or "").strip():
        spec_obj["task_class"] = "analytical_read"

    # Deterministic write-intent normalization fallback from controlled ontology module.
    write_req = infer_write_request(message)
    if str(spec_obj.get("intent") or "").strip().upper() == "READ":
        if str(write_req.get("intent") or "").strip().upper() in {"WRITE_DRAFT", "WRITE_CONFIRM"}:
            spec_obj["intent"] = str(write_req.get("intent") or "").strip().upper()
            spec_obj["subject"] = str(write_req.get("doctype") or spec_obj.get("subject") or "").strip()
            filters = spec_obj.get("filters") if isinstance(spec_obj.get("filters"), dict) else {}
            doc_id = str(write_req.get("document_id") or "").strip()
            if doc_id and ("document_id" not in filters):
                filters["document_id"] = doc_id
            spec_obj["filters"] = filters
            spec_envelope["spec"] = spec_obj

    # Deterministic output flags from explicit user ask (e.g., download/export).
    output_flags = infer_output_flags(message)
    if bool(output_flags.get("include_download")):
        oc = spec_obj.get("output_contract") if isinstance(spec_obj.get("output_contract"), dict) else {}
        if not bool(oc.get("include_download")):
            oc = dict(oc)
            oc["include_download"] = True
            spec_obj["output_contract"] = oc
            spec_envelope["spec"] = spec_obj

    output_contract = spec_obj.get("output_contract") if isinstance(spec_obj.get("output_contract"), dict) else {}
    include_download = bool(output_contract.get("include_download"))
    export_requested = bool(export_requested or include_download)
    intent = str(spec_obj.get("intent") or "").strip().upper()
    if intent in {"WRITE_DRAFT", "WRITE_CONFIRM"}:
        draft_payload = _build_write_draft_payload(message=message, spec=spec_obj, user=user)
        if _draft_operation(draft_payload) == "delete":
            spec_tool_msg = make_spec_tool_message(tool=source, mode="v7", envelope=spec_envelope)
            return _append_tool_message(draft_payload, spec_tool_msg)
        if not _is_write_enabled():
            early = _write_not_enabled_payload()
            spec_tool_msg = make_spec_tool_message(tool=source, mode="v7", envelope=spec_envelope)
            return _append_tool_message(early, spec_tool_msg)
        if isinstance(draft_payload, dict):
            spec_tool_msg = make_spec_tool_message(tool=source, mode="v7", envelope=spec_envelope)
            return _append_tool_message(draft_payload, spec_tool_msg)
        early = {
            "type": "text",
            "text": "Please provide the target document and action clearly before confirm/cancel.",
        }
        spec_tool_msg = make_spec_tool_message(tool=source, mode="v7", envelope=spec_envelope)
        return _append_tool_message(early, spec_tool_msg)
    if intent == "TUTOR":
        early = _tutor_capability_payload()
        spec_tool_msg = make_spec_tool_message(tool=source, mode="v7", envelope=spec_envelope)
        return _append_tool_message(early, spec_tool_msg)

    previous_topic_state = get_topic_state(session_name=session_name)
    mem = apply_memory_context(
        business_spec=spec_obj,
        message=message,
        topic_state=previous_topic_state,
    )
    spec_obj = mem.get("spec") if isinstance(mem.get("spec"), dict) else spec_obj
    spec_obj = _recover_latest_record_followup_spec(
        spec_obj=spec_obj,
        message=message,
        previous_topic_state=previous_topic_state,
    )
    if isinstance(plan_seed, dict):
        spec_obj = _merge_pinned_filters_into_spec(spec_obj=spec_obj, plan_seed=plan_seed)
    memory_meta = mem.get("meta") if isinstance(mem.get("meta"), dict) else {}
    entity_resolution = resolve_entity_filters(filters=(spec_obj.get("filters") if isinstance(spec_obj.get("filters"), dict) else {}))
    if isinstance(entity_resolution.get("filters"), dict):
        spec_obj["filters"] = dict(entity_resolution.get("filters") or {})
    _merge_transform_ambiguities_into_spec(spec_obj=spec_obj, message=message)
    last_result_payload = _load_last_result_payload(session_name=session_name)
    if _should_promote_to_transform_followup(
        message=message,
        spec_obj=spec_obj,
        memory_meta=memory_meta,
        last_result_payload=last_result_payload,
    ):
        spec_obj = _promote_spec_to_transform_followup(spec_obj=spec_obj, last_result_payload=last_result_payload)
    entity_clarification = entity_resolution.get("clarification") if isinstance(entity_resolution.get("clarification"), dict) else None

    resolve_envelope = resolve_business_request(
        business_spec=spec_obj,
        message=message,
        user=user,
        topic_state=previous_topic_state,
    )
    resolve_tool_msg = make_resolver_tool_message(tool=source, mode="v7", envelope=resolve_envelope)
    resolved = resolve_envelope.get("resolved") if isinstance(resolve_envelope.get("resolved"), dict) else {}
    selected_report = str(resolved.get("selected_report") or "").strip()
    if selected_report:
        spec_obj = _enrich_minimal_columns_from_report_metadata(
            spec_obj=spec_obj,
            message=message,
            selected_report=selected_report,
            last_result_payload=last_result_payload,
        )
    spec_envelope["spec"] = spec_obj
    spec_tool_msg = make_spec_tool_message(tool=source, mode="v7", envelope=spec_envelope)
    clarify_decision = evaluate_clarification(
        business_spec=spec_obj,
        resolved=resolved,
    )
    if (mode == "start") and _is_low_signal_read_spec(raw_spec_obj):
        clarify_decision = {
            "should_clarify": True,
            "reason": "no_candidate",
            "question": "Which business report should I run, and for which timeframe?",
            "options": [],
            "policy_version": "phase5_blocker_only_v1",
        }
    if entity_clarification:
        clarify_decision = {
            "should_clarify": True,
            "reason": str(entity_clarification.get("reason") or "entity_no_match"),
            "question": str(entity_clarification.get("question") or "").strip(),
            "options": [str(x) for x in list(entity_clarification.get("options") or []) if str(x or "").strip()][:8],
            "target_filter_key": str(entity_clarification.get("filter_key") or "").strip(),
            "raw_value": str(entity_clarification.get("raw_value") or "").strip(),
            "policy_version": "phase5_blocker_only_v1",
        }
    if str(spec_obj.get("intent") or "").strip().upper() == "TRANSFORM_LAST":
        # Transform-last should operate on previous result without planner clarification.
        clarify_decision = {
            "should_clarify": False,
            "reason": "",
            "question": "",
            "policy_version": "phase5_blocker_only_v1",
        }
    selected_score = resolved.get("selected_score")
    candidate_state = _loop_build_candidate_report_state(resolved=resolved, selected_report=selected_report)
    candidate_reports = list(candidate_state.get("candidate_reports") or [])
    candidate_scores = dict(candidate_state.get("candidate_scores") or {})
    candidate_cursor = int(candidate_state.get("candidate_cursor") or 0)

    step_trace: List[Dict[str, Any]] = []
    top_candidates: List[Dict[str, Any]] = list(candidate_state.get("top_candidates") or [])
    step_trace.append(
        _loop_resolver_selected_step_trace(
            resolved=resolved,
            selected_report=selected_report,
            top_candidates=top_candidates,
        )
    )
    direct_doc_payload = _direct_document_lookup_payload(spec_obj, message=message)
    direct_latest_payload = _direct_latest_records_payload(spec_obj, message=message)
    if isinstance(direct_doc_payload, dict):
        # Explicit document-id asks are deterministic and should bypass planner
        # clarification, even when resolver confidence is low.
        clarify_decision = {
            "should_clarify": False,
            "reason": "",
            "question": "",
            "policy_version": "phase5_blocker_only_v1",
        }
    elif isinstance(direct_latest_payload, dict):
        # Record-list asks can be satisfied directly from transactional doctypes
        # when resolver/report coverage is missing for this behavior class.
        clarify_decision = {
            "should_clarify": False,
            "reason": "",
            "question": "",
            "policy_version": "phase5_blocker_only_v1",
        }
    clar_tool_msg = make_clarification_tool_message(tool=source, mode=mode, decision=clarify_decision)

    if bool(clarify_decision.get("should_clarify")):
        reason_lc = str(clarify_decision.get("reason") or "").strip().lower()
        pending_mode = "planner_clarify"
        if reason_lc in ("missing_required_filter_value", "entity_no_match", "entity_ambiguous"):
            pending_mode = "need_filters"
        clar_options = [str(x) for x in list(clarify_decision.get("options") or []) if str(x or "").strip()][:8]
        option_actions: Dict[str, str] = {}
        if pending_mode == "planner_clarify":
            if not clar_options:
                clar_options = ["Switch to compatible report", "Keep current scope"]
            option_actions = _planner_option_actions(options=clar_options, pending={})
        target_filter_key = str(clarify_decision.get("target_filter_key") or "").strip()
        raw_value = str(clarify_decision.get("raw_value") or "").strip()
        payload = {
            "type": "text",
            "text": str(clarify_decision.get("question") or "").strip(),
            "_pending_state": {
                "mode": pending_mode,
                "base_question": str(message or "").strip(),
                "report_name": str(selected_report or "").strip(),
                "filters_so_far": dict(spec_obj.get("filters") or {}) if isinstance(spec_obj.get("filters"), dict) else {},
                "clarification_question": str(clarify_decision.get("question") or "").strip(),
                "clarification_options": list(clar_options),
                "options": list(clar_options),
                "option_actions": dict(option_actions),
                "target_filter_key": target_filter_key,
                "raw_value": raw_value,
                "clarification_reason": reason_lc,
                "spec_so_far": {
                    "task_class": str(spec_obj.get("task_class") or "").strip().lower(),
                    "subject": str(spec_obj.get("subject") or "").strip(),
                    "metric": str(spec_obj.get("metric") or "").strip(),
                    "domain": str(spec_obj.get("domain") or "").strip(),
                    "top_n": int(spec_obj.get("top_n") or 0),
                    "output_contract": dict(spec_obj.get("output_contract") or {}) if isinstance(spec_obj.get("output_contract"), dict) else {},
                },
                "clarification_round": 1,
            },
        }
        quality = evaluate_quality_gate(
            business_spec=spec_obj,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        shaper_tool_msg = make_response_shaper_tool_message(tool=source, mode=mode, shaped_payload=payload)
        step_trace.append({"step": 0, "action": "clarify_blocker", "reason": clarify_decision.get("reason")})
        quality_tool_msg = make_quality_gate_tool_message(
            tool=source,
            mode=mode,
            quality=quality,
        )
        read_engine_msg = _read_engine_tool_message(
            source_tool=source,
            mode=mode,
            selected_report=selected_report,
            selected_score=selected_score,
            max_steps=max_steps,
            executed_steps=0,
            repeated_call_guard_triggered=False,
            repair_attempts=0,
            quality_verdict=str(quality.get("verdict") or ""),
            failed_check_ids=list(quality.get("failed_check_ids") or []),
            step_trace=step_trace,
        )
        topic_state = build_topic_state(
            previous_state=previous_topic_state,
            business_spec=spec_obj,
            resolved=resolved,
            payload=payload,
            clarification_decision=clarify_decision,
            memory_meta=memory_meta,
            message=message,
        )
        topic_tool_msg = make_topic_state_tool_message(tool=source, mode=mode, state=topic_state, memory_meta=memory_meta)
        payload = _append_tool_message(payload, spec_tool_msg)
        payload = _append_tool_message(payload, resolve_tool_msg)
        payload = _append_tool_message(payload, clar_tool_msg)
        payload = _append_tool_message(payload, shaper_tool_msg)
        payload = _append_tool_message(payload, quality_tool_msg)
        payload = _append_tool_message(payload, topic_tool_msg)
        return _append_tool_message(payload, read_engine_msg)

    loop_result = _runner_execute_read_loop(
        message=message,
        mode=mode,
        source=source,
        plan_seed=plan_seed,
        max_steps=max_steps,
        spec_obj=spec_obj,
        spec_envelope=spec_envelope,
        resolved=resolved,
        selected_report=selected_report,
        selected_score=selected_score,
        candidate_reports=candidate_reports,
        candidate_scores=candidate_scores,
        candidate_cursor=candidate_cursor,
        initial_step_trace=step_trace,
        previous_topic_state=previous_topic_state,
        session_name=session_name,
        user=user,
        export_requested=export_requested,
        direct_doc_payload=direct_doc_payload,
        direct_latest_payload=direct_latest_payload,
        clarify_decision=clarify_decision,
        internal_retry_key=_INTERNAL_RETRY_KEY,
        verdict_pass=VERDICT_PASS,
        verdict_hard_fail=VERDICT_HARD_FAIL,
        verdict_repairable_fail=VERDICT_REPAIRABLE_FAIL,
        execute_selected_report_direct_fn=_execute_selected_report_direct,
        legacy_path_unavailable_payload_fn=_legacy_path_unavailable_payload,
        load_last_result_payload_fn=_load_last_result_payload,
        extract_auto_switch_pending_fn=_extract_auto_switch_pending,
        capture_source_columns_fn=_capture_source_columns,
        as_payload_fn=_as_payload,
        apply_transform_last_fn=lambda payload, business_spec: apply_transform_last(payload=payload, business_spec=business_spec),
        looks_like_system_error_text_fn=_looks_like_system_error_text,
        make_transform_tool_message_fn=make_transform_tool_message,
        shape_response_fn=lambda payload, business_spec: shape_response(payload=payload, business_spec=business_spec),
        sanitize_user_payload_fn=_sanitize_user_payload,
        apply_requested_entity_row_filters_fn=_apply_requested_entity_row_filters,
        make_response_shaper_tool_message_fn=make_response_shaper_tool_message,
        evaluate_quality_gate_fn=evaluate_quality_gate,
        should_switch_candidate_on_repairable_fn=_should_switch_candidate_on_repairable,
        resolve_business_request_fn=lambda **kwargs: resolve_business_request(**kwargs),
        quality_has_repairable_failure_class_fn=_quality_has_repairable_failure_class,
        unsupported_message_from_spec_fn=_unsupported_message_from_spec,
        planner_option_actions_fn=_planner_option_actions,
        default_clarification_question_fn=default_clarification_question,
    )
    payload = loop_result.get("payload") if isinstance(loop_result.get("payload"), dict) else {"type": "text", "text": "No output generated."}
    quality = loop_result.get("quality") if isinstance(loop_result.get("quality"), dict) else {
        "verdict": VERDICT_HARD_FAIL,
        "failed_check_ids": ["QG00_NOT_EVALUATED"],
        "hard_fail_check_ids": ["QG00_NOT_EVALUATED"],
        "repairable_check_ids": [],
        "checks": [],
    }
    shaper_tool_msg = str(loop_result.get("shaper_tool_msg") or "")
    transform_tool_msg = str(loop_result.get("transform_tool_msg") or "")
    selected_report = str(loop_result.get("selected_report") or selected_report or "")
    selected_score = loop_result.get("selected_score")
    resolved = loop_result.get("resolved") if isinstance(loop_result.get("resolved"), dict) else resolved
    step_trace = [x for x in list(loop_result.get("step_trace") or []) if isinstance(x, dict)]
    executed_steps = int(loop_result.get("executed_steps") or 0)
    repair_attempts = int(loop_result.get("repair_attempts") or 0)
    repeated_guard = bool(loop_result.get("repeated_guard"))
    clarify_decision = loop_result.get("clarify_decision") if isinstance(loop_result.get("clarify_decision"), dict) else clarify_decision

    quality_tool_msg = make_quality_gate_tool_message(
        tool=source,
        mode=mode,
        quality=quality,
    )
    read_engine_msg = _read_engine_tool_message(
        source_tool=source,
        mode=mode,
        selected_report=selected_report,
        selected_score=selected_score,
        max_steps=max_steps,
        executed_steps=executed_steps,
        repeated_call_guard_triggered=repeated_guard,
        repair_attempts=repair_attempts,
        quality_verdict=str(quality.get("verdict") or ""),
        failed_check_ids=list(quality.get("failed_check_ids") or []),
        step_trace=step_trace,
    )
    topic_state = build_topic_state(
        previous_state=previous_topic_state,
        business_spec=spec_obj,
        resolved=resolved,
        payload=payload,
        clarification_decision=clarify_decision,
        memory_meta=memory_meta,
        message=message,
    )
    topic_tool_msg = make_topic_state_tool_message(tool=source, mode=mode, state=topic_state, memory_meta=memory_meta)

    payload = _sanitize_user_payload(payload=payload, business_spec=spec_obj)
    payload = format_numeric_values_for_display(payload)
    if clear_pending_on_success and (not isinstance(payload.get("_pending_state"), dict)):
        payload["_clear_pending_state"] = True
    payload = _append_tool_message(payload, spec_tool_msg)
    payload = _append_tool_message(payload, resolve_tool_msg)
    payload = _append_tool_message(payload, clar_tool_msg)
    if transform_tool_msg:
        payload = _append_tool_message(payload, transform_tool_msg)
    if shaper_tool_msg:
        payload = _append_tool_message(payload, shaper_tool_msg)
    payload = _append_tool_message(payload, quality_tool_msg)
    payload = _append_tool_message(payload, topic_tool_msg)
    return _append_tool_message(payload, read_engine_msg)
