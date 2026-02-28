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
    infer_filter_kinds,
    infer_output_flags,
    infer_record_doctype_candidates,
    infer_transform_ambiguities,
    infer_write_request,
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
from ai_assistant_ui.ai_core.v7.resolver_pipeline import make_resolver_tool_message, resolve_business_request
from ai_assistant_ui.ai_core.v7.spec_pipeline import generate_business_request_spec, make_spec_tool_message
from ai_assistant_ui.ai_core.v7.transform_last import apply_transform_last, make_transform_tool_message
from ai_assistant_ui.ai_core.v7.write_engine import execute_write_flow, make_write_engine_tool_message
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
    for m in reversed(session_doc.get("messages") or []):
        if str(m.role or "").strip().lower() != "tool":
            continue
        obj = _safe_json_obj(m.content)
        obj_type = str(obj.get("type") or "").strip()
        if obj_type != "v7_topic_state":
            continue
        state = obj.get("state") if isinstance(obj.get("state"), dict) else {}
        active_result = state.get("active_result") if isinstance(state.get("active_result"), dict) else {}
        return dict(active_result)
    return {}


def _apply_active_result_meta(payload: Dict[str, Any], *, active_result_meta: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload or {})
    meta = active_result_meta if isinstance(active_result_meta, dict) else {}
    scaled_unit = str(meta.get("scaled_unit") or "").strip().lower()
    if ("_scaled_unit" not in out) and scaled_unit:
        out["_scaled_unit"] = scaled_unit
    output_mode = str(meta.get("output_mode") or "").strip().lower()
    if ("_output_mode" not in out) and output_mode:
        out["_output_mode"] = output_mode
    return out


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
    if (not session_name) or (frappe is None):
        return None
    try:
        session_doc = frappe.get_doc("AI Chat Session", session_name)
    except Exception:
        return None
    active_result_meta = _latest_active_result_meta(session_doc)

    # Prefer the latest assistant-visible report table (already shaped for user intent).
    for m in reversed(session_doc.get("messages") or []):
        if str(m.role or "").strip().lower() != "assistant":
            continue
        obj = _safe_json_obj(m.content)
        if str(obj.get("type") or "").strip().lower() != "report_table":
            continue
        table = obj.get("table") if isinstance(obj.get("table"), dict) else {}
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        cols = table.get("columns") if isinstance(table.get("columns"), list) else []
        if not rows or not cols:
            continue
        out = {
            "type": "report_table",
            "report_name": str(obj.get("report_name") or "").strip(),
            "title": str(obj.get("title") or obj.get("report_name") or "Previous Result").strip(),
            "table": {"columns": cols, "rows": rows},
        }
        for k in ("_transform_last_applied", "_scaled_unit", "_output_mode"):
            if k in obj:
                out[k] = obj.get(k)
        return _apply_active_result_meta(out, active_result_meta=active_result_meta)

    # Fallback to raw tool last_result snapshot.
    for m in reversed(session_doc.get("messages") or []):
        if str(m.role or "").strip().lower() != "tool":
            continue
        obj = _safe_json_obj(m.content)
        if obj.get("type") != "last_result":
            continue
        table = obj.get("table") if isinstance(obj.get("table"), dict) else {}
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        cols = table.get("columns") if isinstance(table.get("columns"), list) else []
        if not rows or not cols:
            continue
        report_name = str(obj.get("report_name") or "").strip()
        out = {
            "type": "report_table",
            "report_name": report_name,
            "title": report_name or "Previous Result",
            "table": {"columns": cols, "rows": rows},
        }
        for k in ("_transform_last_applied", "_scaled_unit", "_output_mode"):
            if k in obj:
                out[k] = obj.get(k)
        return _apply_active_result_meta(out, active_result_meta=active_result_meta)
    return None


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


def _handle_write_confirmation(*, message: str, pending: Dict[str, Any], source: str) -> Dict[str, Any]:
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
    return json.dumps(
        {
            "type": "v7_read_engine",
            "phase": "phase6",
            "mode": str(mode or "").strip(),
            "tool": str(source_tool or "").strip(),
            "selected_report": str(selected_report or "").strip(),
            "selected_score": selected_score,
            "max_steps": int(max_steps),
            "executed_steps": int(executed_steps),
            "repair_attempts": int(repair_attempts),
            "quality_verdict": str(quality_verdict or ""),
            "failed_check_ids": list(failed_check_ids or []),
            "repeated_call_guard_triggered": bool(repeated_call_guard_triggered),
            "step_trace": step_trace[:6],
        },
        ensure_ascii=False,
        default=str,
    )


def _planner_plan(*, export: bool, pending_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    pending = pending_state if isinstance(pending_state, dict) else {}
    if pending:
        return {
            "action": "run_report",
            "report_name": pending.get("report_name"),
            "filters": pending.get("filters_so_far") if isinstance(pending.get("filters_so_far"), dict) else {},
        }
    return {"action": "run_report", "export": bool(export)}


def _quality_has_repairable_failure_class(quality: Dict[str, Any], classes: List[str]) -> bool:
    q = quality if isinstance(quality, dict) else {}
    wanted = {str(x or "").strip().lower() for x in list(classes or []) if str(x or "").strip()}
    if not wanted:
        return False
    repairable_classes = {
        str(x or "").strip().lower()
        for x in list(q.get("repairable_failure_classes") or [])
        if str(x or "").strip()
    }
    if repairable_classes:
        return bool(repairable_classes & wanted)

    # Backward-compat fallback for older quality payloads without failure classes.
    failed_ids = [str(x or "") for x in list(q.get("failed_check_ids") or [])]
    return any(
        x.endswith("_non_empty_rows")
        or x.endswith("_kpi_payload_shape")
        or x.endswith("_trend_has_time_axis")
        or x.endswith("_minimal_columns_present")
        or x.endswith("_requested_dimensions_present")
        or x.endswith("_document_filter_applied")
        or x.endswith("_actual_sales_not_opportunity_metric")
        or x.endswith("_output_mode_payload_alignment")
        for x in failed_ids
    )


def _should_switch_candidate_on_repairable(
    *,
    quality: Dict[str, Any],
    intent: str,
    task_class: str,
    candidate_cursor: int,
    candidate_reports: List[str],
    candidate_switch_attempts: int,
) -> bool:
    if str(quality.get("verdict") or "").strip() != VERDICT_REPAIRABLE_FAIL:
        return False
    if str(intent or "").strip().upper() == "TRANSFORM_LAST":
        return False
    if candidate_cursor + 1 >= len(list(candidate_reports or [])):
        return False
    if int(candidate_switch_attempts) >= 4:
        return False
    switch_classes = ["shape", "data", "constraint", "semantic"]
    if str(task_class or "").strip().lower() == "list_latest_records":
        # For list-latest flows, semantic subject checks can be noisy and cause
        # over-switching to unrelated reports; prefer staying on the current best
        # candidate unless shape/data constraints are clearly repairable.
        switch_classes = ["shape", "data", "constraint"]
    return _quality_has_repairable_failure_class(
        quality,
        classes=switch_classes,
    )


def _normalize_option_label(value: str) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").replace("-", " ").split())


def _match_option_choice(message: str, options: List[str]) -> str:
    msg = str(message or "").strip()
    if (not msg) or (not options):
        return ""
    normalized = [str(x).strip() for x in list(options or []) if str(x or "").strip()]
    if not normalized:
        return ""
    msg_norm = _normalize_option_label(msg)

    m_idx = re.search(r"\b(\d{1,2})\b", msg_norm)
    if m_idx:
        try:
            idx = int(m_idx.group(1)) - 1
        except Exception:
            idx = -1
        if 0 <= idx < len(normalized):
            return normalized[idx]

    for opt in normalized:
        opt_norm = _normalize_option_label(opt)
        if msg_norm == opt_norm:
            return opt
    for opt in normalized:
        opt_norm = _normalize_option_label(opt)
        if opt_norm and (opt_norm in msg_norm or msg_norm in opt_norm):
            return opt
    return ""


def _planner_option_actions(*, options: List[str], pending: Dict[str, Any]) -> Dict[str, str]:
    p = pending if isinstance(pending, dict) else {}
    raw_map = p.get("option_actions") if isinstance(p.get("option_actions"), dict) else {}
    out: Dict[str, str] = {}
    for k, v in raw_map.items():
        key = _normalize_option_label(str(k or ""))
        val = str(v or "").strip().lower()
        if key and val:
            out[key] = val
    if out:
        return out
    vals = [str(x).strip() for x in list(options or []) if str(x or "").strip()]
    if len(vals) >= 2:
        out[_normalize_option_label(vals[0])] = "switch_report"
        out[_normalize_option_label(vals[1])] = "keep_current"
    return out


def _looks_like_scope_answer_text(text: str) -> bool:
    toks = [t for t in re.findall(r"[A-Za-z0-9_]+", str(text or "").strip().lower()) if t]
    if not toks:
        return False
    if len(toks) > 4:
        return False
    if any(t.isdigit() for t in toks):
        return False
    return True


def _first_int_in_text(text: str) -> int:
    m = re.search(r"\b(\d{1,3})\b", str(text or ""))
    if not m:
        return 0
    try:
        return int(m.group(1))
    except Exception:
        return 0


def _recover_latest_record_followup_spec(
    *,
    spec_obj: Dict[str, Any],
    message: str,
    previous_topic_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Recover list-latest follow-ups when pending-state is missing but topic-state
    still indicates an unresolved record-type clarification.
    """
    spec = dict(spec_obj or {})
    prev = previous_topic_state if isinstance(previous_topic_state, dict) else {}
    active_topic = prev.get("active_topic") if isinstance(prev.get("active_topic"), dict) else {}
    unresolved = prev.get("unresolved_blocker") if isinstance(prev.get("unresolved_blocker"), dict) else {}

    if not bool(unresolved.get("present")):
        return spec
    if not _looks_like_scope_answer_text(message):
        return spec
    active_task = str(active_topic.get("task_class") or "").strip().lower()
    active_subject = str(active_topic.get("subject") or "").strip().lower()
    unresolved_q = str(unresolved.get("question") or "").strip().lower()
    likely_record_type_followup = (
        active_task == "list_latest_records"
        or ("invoice" in active_subject)
        or ("record type" in unresolved_q)
    )
    if not likely_record_type_followup:
        return spec

    infer_spec = {
        "subject": str(active_topic.get("subject") or spec.get("subject") or "").strip(),
        "metric": str(active_topic.get("metric") or spec.get("metric") or "").strip(),
        "filters": dict(spec.get("filters") or {}) if isinstance(spec.get("filters"), dict) else {},
        "domain": str(active_topic.get("domain") or spec.get("domain") or "").strip(),
    }
    dt_candidates = _resolve_record_doctype_candidates(message=message, spec=infer_spec)
    typed = str(message or "").strip().lower()
    all_doctypes = _load_submittable_doctypes()
    exact = [dt for dt in all_doctypes if str(dt or "").strip().lower() == typed]
    if exact:
        dt_candidates = [str(exact[0] or "").strip()]
    if not dt_candidates:
        return spec

    chosen = str(dt_candidates[0] or "").strip()
    if len(dt_candidates) > 1:
        domain_hint = str(active_topic.get("domain") or infer_spec.get("domain") or "").strip().lower()
        if domain_hint == "sales":
            for dt in dt_candidates:
                if "sales" in str(dt or "").strip().lower():
                    chosen = str(dt or "").strip()
                    break
        elif domain_hint in {"purchasing", "purchase"}:
            for dt in dt_candidates:
                if "purchase" in str(dt or "").strip().lower():
                    chosen = str(dt or "").strip()
                    break
    if not chosen:
        return spec

    out = dict(spec)
    out["intent"] = "READ"
    out["task_type"] = "detail"
    out["task_class"] = "list_latest_records"
    out["output_mode"] = "top_n"

    filters = dict(out.get("filters") or {}) if isinstance(out.get("filters"), dict) else {}
    filters["doctype"] = chosen
    out["filters"] = filters

    try:
        top_n = int(out.get("top_n") or active_topic.get("top_n") or 0)
    except Exception:
        top_n = 0
    if top_n <= 0:
        top_n = _first_int_in_text(str((prev.get("turn_meta") or {}).get("message_preview") or ""))
    if top_n <= 0:
        top_n = 20
    out["top_n"] = max(1, min(top_n, 200))

    oc = dict(out.get("output_contract") or {}) if isinstance(out.get("output_contract"), dict) else {}
    oc["mode"] = "top_n"
    out["output_contract"] = oc

    if not str(out.get("subject") or "").strip():
        out["subject"] = str(active_topic.get("subject") or "invoices").strip()
    if not str(out.get("domain") or "").strip():
        out["domain"] = str(active_topic.get("domain") or infer_spec.get("domain") or "sales").strip()
    return out


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
    """
    Handles blocker-only follow-up continuations in a deterministic way:
    - need_filters with entity options/value
    - planner_clarify with natural switch/keep choice
    Returns either a clarified payload or a start-mode resume plan.
    """
    p = pending if isinstance(pending, dict) else {}
    mode = str(p.get("mode") or "").strip().lower()
    base_question = str(p.get("base_question") or "").strip()
    if mode not in {"need_filters", "planner_clarify"}:
        return {"active": False}
    if not base_question:
        return {"active": False}

    options = [str(x).strip() for x in list(p.get("options") or p.get("clarification_options") or []) if str(x or "").strip()]
    report_name = str(p.get("report_name") or "").strip()
    filters_so_far = dict(p.get("filters_so_far") or {}) if isinstance(p.get("filters_so_far"), dict) else {}
    spec_so_far = p.get("spec_so_far") if isinstance(p.get("spec_so_far"), dict) else {}
    pending_reason = str(p.get("clarification_reason") or "").strip().lower()
    target_filter_key = str(p.get("target_filter_key") or "").strip()
    raw_input = str(message or "").strip()
    new_request_decision: Optional[bool] = None

    def _plan_seed_from_pending_spec(*, include_filters: bool) -> Dict[str, Any]:
        seed: Dict[str, Any] = {"action": "run_report"}
        task_class = str(spec_so_far.get("task_class") or "").strip().lower()
        if task_class:
            seed["task_class"] = task_class
        try:
            top_n = int(spec_so_far.get("top_n") or 0)
        except Exception:
            top_n = 0
        if top_n > 0:
            seed["top_n"] = top_n
            seed["output_mode"] = "top_n"
        oc = spec_so_far.get("output_contract") if isinstance(spec_so_far.get("output_contract"), dict) else {}
        minimal_columns = [str(x).strip() for x in list(oc.get("minimal_columns") or []) if str(x or "").strip()]
        if minimal_columns:
            seed["minimal_columns"] = minimal_columns[:12]
        if include_filters and filters_so_far:
            seed["filters"] = dict(filters_so_far)
        return seed

    def _is_new_request() -> bool:
        nonlocal new_request_decision
        if new_request_decision is None:
            new_request_decision = _is_new_business_request_structured(message=raw_input, session_name=session_name)
        return bool(new_request_decision)

    if mode == "planner_clarify":
        planner_options = options or ["Switch to compatible report", "Keep current scope"]
        option_actions = _planner_option_actions(options=planner_options, pending=p)
        chosen = _match_option_choice(raw_input, planner_options)
        if not chosen:
            if _looks_like_scope_answer_text(raw_input):
                merged = f"{base_question}. {raw_input}".strip()
                seed = _plan_seed_from_pending_spec(include_filters=False)
                infer_spec: Dict[str, Any] = {
                    "subject": str(spec_so_far.get("subject") or "").strip(),
                    "metric": str(spec_so_far.get("metric") or "").strip(),
                    "filters": dict(filters_so_far),
                    "domain": str(spec_so_far.get("domain") or "").strip(),
                }
                doctype_candidates = _resolve_record_doctype_candidates(message=raw_input, spec=infer_spec)
                explicit_doctype = _resolve_explicit_doctype_name(raw_input)
                if explicit_doctype:
                    all_doctypes = _load_submittable_doctypes()
                    if explicit_doctype in all_doctypes:
                        doctype_candidates = [explicit_doctype]
                if not doctype_candidates:
                    pending_task_class = str(spec_so_far.get("task_class") or "").strip().lower()
                    is_record_type_followup = (
                        pending_task_class == "list_latest_records"
                        or ("invoice" in str(base_question or "").strip().lower())
                    )
                    if is_record_type_followup and explicit_doctype:
                        # Handle concise follow-up answers like "Sales Invoice"
                        # deterministically in pending clarifications.
                        doctype_candidates = [explicit_doctype]
                synthetic_query = merged
                if len(doctype_candidates) == 1:
                    chosen_doctype = str(doctype_candidates[0] or "").strip()
                    seed_filters = dict(seed.get("filters") or {})
                    seed_filters["doctype"] = chosen_doctype
                    seed["filters"] = seed_filters
                    seed["task_class"] = "list_latest_records"
                    seed["output_mode"] = "top_n"
                    try:
                        top_n = int(spec_so_far.get("top_n") or 0)
                    except Exception:
                        top_n = 0
                    if top_n <= 0:
                        top_n = _first_int_in_text(base_question)
                    if top_n > 0:
                        seed["top_n"] = max(1, min(top_n, 200))
                        synthetic_query = f"Show me the latest {seed['top_n']} {chosen_doctype}"
                    else:
                        synthetic_query = f"Show me the latest records for {chosen_doctype}"
                return {
                    "active": True,
                    "resume_message": synthetic_query,
                    "plan_seed": seed,
                    "clear_pending": True,
                    "source": "report_qa_start",
                }
            if pending_reason == "no_candidate":
                merged = f"{base_question}. {raw_input}".strip()
                return {
                    "active": True,
                    "resume_message": merged,
                    "plan_seed": _plan_seed_from_pending_spec(include_filters=False),
                    "clear_pending": True,
                    "source": "report_qa_start",
                }
            if _is_new_request():
                return {
                    "active": True,
                    "resume_message": raw_input,
                    "plan_seed": {"action": "run_report"},
                    "clear_pending": True,
                    "source": "report_qa_start",
                }
            # Treat free-text reply as a refinement for the same blocked request.
            # This prevents clarification loops when users answer with concrete
            # scope (e.g., "Sales Invoice") instead of clicking switch/keep options.
            merged = f"{base_question}. {raw_input}".strip()
            return {
                "active": True,
                "resume_message": merged,
                "plan_seed": _plan_seed_from_pending_spec(include_filters=False),
                "clear_pending": True,
                "source": "report_qa_start",
            }
        chosen_action = str(option_actions.get(_normalize_option_label(chosen)) or "").strip().lower()
        if chosen_action == "keep_current":
            return {
                "active": False,
                "payload": {
                    "type": "text",
                    "text": default_clarification_question("missing_required_filter_value"),
                    "_clear_pending_state": True,
                },
            }
        return {
            "active": True,
            "resume_message": base_question,
            "plan_seed": dict(_plan_seed_from_pending_spec(include_filters=True), report_name=report_name),
            "clear_pending": True,
            "source": "report_qa_start",
        }

    if mode == "need_filters":
        selected_value = ""
        if options:
            selected_value = _match_option_choice(raw_input, options)
            if not selected_value:
                if _is_new_request():
                    return {
                        "active": True,
                        "resume_message": raw_input,
                        "plan_seed": {"action": "run_report"},
                        "clear_pending": True,
                        "source": "report_qa_start",
                    }
                text = default_clarification_question("entity_ambiguous")
                return {
                    "active": False,
                    "payload": {
                        "type": "text",
                        "text": text,
                        "_pending_state": {
                            "mode": "need_filters",
                            "base_question": base_question,
                            "report_name": report_name,
                            "filters_so_far": filters_so_far,
                            "clarification_question": text,
                            "clarification_options": options,
                            "options": options,
                            "target_filter_key": target_filter_key,
                            "clarification_round": int(p.get("clarification_round") or 1),
                        },
                    },
                }
        else:
            if _is_new_request():
                return {
                    "active": True,
                    "resume_message": raw_input,
                    "plan_seed": {"action": "run_report"},
                    "clear_pending": True,
                    "source": "report_qa_start",
                }
            selected_value = raw_input

        if target_filter_key and selected_value:
            filters_so_far[target_filter_key] = selected_value
        elif selected_value:
            # Fallback: update the first available filter key when key metadata is missing.
            for k in list(filters_so_far.keys()):
                if str(k or "").strip():
                    filters_so_far[k] = selected_value
                    break

        return {
            "active": True,
            "resume_message": base_question,
            "plan_seed": {
                "action": "run_report",
                "report_name": report_name,
                "filters": filters_so_far,
            },
            "clear_pending": True,
            "source": "report_qa_start",
        }

    return {"active": False}


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
    """
    Detect internal quality clarification where v2 asks:
    "Should I switch to another compatible report?".
    This is not a true business blocker, so v7 may auto-accept once.
    """
    out = payload if isinstance(payload, dict) else {}
    pending = out.get("_pending_state") if isinstance(out.get("_pending_state"), dict) else None
    if not isinstance(pending, dict):
        return None
    if str(pending.get("mode") or "").strip() != "planner_clarify":
        return None
    qc = pending.get("quality_clarification") if isinstance(pending.get("quality_clarification"), dict) else {}
    if str(qc.get("intent") or "").strip() != "switch_report":
        return None
    try:
        switch_attempt = int(qc.get("switch_attempt") or 0)
    except Exception:
        switch_attempt = 0
    if switch_attempt >= 1:
        return None
    return pending


def _looks_like_system_error_text(payload: Dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    typ = str(payload.get("type") or "").strip().lower()
    if typ not in {"text", "error"}:
        return False
    txt = str(payload.get("text") or payload.get("message") or "").strip().lower()
    if not txt:
        return False
    patterns = (
        "is mandatory",
        "not found",
        "must be greater than",
        "must be less than",
        "traceback",
        "exception",
        "error:",
        "sql",
    )
    return any(p in txt for p in patterns)


def _unsupported_message_from_spec(spec: Dict[str, Any]) -> str:
    subject = str(spec.get("subject") or "").strip()
    metric = str(spec.get("metric") or "").strip()
    if subject or metric:
        return (
            "I couldn't reliably produce that result with current report coverage. "
            f"Requested scope: subject='{subject or 'unspecified'}', metric='{metric or 'unspecified'}'. "
            "Please refine the target report/filters and retry."
        )
    return "I couldn't reliably produce that result with current report coverage. Please refine the request (target report/filters), and I'll retry."


def _is_low_signal_read_spec(spec: Dict[str, Any]) -> bool:
    s = spec if isinstance(spec, dict) else {}
    intent = str(s.get("intent") or "").strip().upper()
    if intent and intent != "READ":
        return False
    if str(s.get("task_class") or "").strip().lower() == "transform_followup":
        return False
    if isinstance(s.get("filters"), dict) and bool(s.get("filters")):
        return False
    if list(s.get("group_by") or []) or list(s.get("dimensions") or []):
        return False
    try:
        if int(s.get("top_n") or 0) > 0:
            return False
    except Exception:
        pass
    ts = s.get("time_scope") if isinstance(s.get("time_scope"), dict) else {}
    if str(ts.get("mode") or "none").strip().lower() not in {"", "none"}:
        return False
    metric = str(s.get("metric") or "").strip()
    if metric:
        return False
    oc = s.get("output_contract") if isinstance(s.get("output_contract"), dict) else {}
    if list(oc.get("minimal_columns") or []):
        return False
    subject = str(s.get("subject") or "").strip().lower()
    if not subject:
        return True
    tokens = re.findall(r"[a-z0-9]+", subject)
    if not tokens:
        return True
    generic = {"report", "reports", "data", "result", "results", "detail", "details", "information", "show", "view"}
    non_generic = [t for t in tokens if t not in generic]
    return len(non_generic) == 0


def _has_explicit_time_scope(spec: Dict[str, Any]) -> bool:
    ts = spec.get("time_scope") if isinstance(spec.get("time_scope"), dict) else {}
    mode = str(ts.get("mode") or "none").strip().lower()
    value = str(ts.get("value") or "").strip()
    return bool((mode not in {"", "none"}) or value)


def _has_report_table_rows(payload: Optional[Dict[str, Any]]) -> bool:
    p = payload if isinstance(payload, dict) else {}
    if str(p.get("type") or "").strip().lower() != "report_table":
        return False
    table = p.get("table") if isinstance(p.get("table"), dict) else {}
    rows = table.get("rows") if isinstance(table.get("rows"), list) else []
    cols = table.get("columns") if isinstance(table.get("columns"), list) else []
    return bool(rows and cols)


def _merge_transform_ambiguities_into_spec(*, spec_obj: Dict[str, Any], message: str) -> List[str]:
    spec = spec_obj if isinstance(spec_obj, dict) else {}
    hints = [str(x).strip().lower() for x in list(infer_transform_ambiguities(message)) if str(x or "").strip()]
    if not hints:
        return []
    existing = [str(x).strip().lower() for x in list(spec.get("ambiguities") or []) if str(x or "").strip()]
    merged: List[str] = []
    seen = set()
    for x in existing + hints:
        if not x or x in seen:
            continue
        seen.add(x)
        merged.append(x)
    spec["ambiguities"] = merged[:12]
    return hints


def _should_promote_to_transform_followup(
    *,
    spec_obj: Dict[str, Any],
    memory_meta: Dict[str, Any],
    last_result_payload: Optional[Dict[str, Any]],
) -> bool:
    spec = spec_obj if isinstance(spec_obj, dict) else {}
    if str(spec.get("intent") or "").strip().upper() != "READ":
        return False
    if str(spec.get("task_class") or "").strip().lower() == "transform_followup":
        return False
    if not _has_report_table_rows(last_result_payload):
        return False
    if _has_explicit_time_scope(spec):
        return False

    ambiguities = [str(x).strip().lower() for x in list(spec.get("ambiguities") or []) if str(x or "").strip()]
    has_transform_hint = any(a.startswith("transform_") for a in ambiguities)
    task_type = str(spec.get("task_type") or "").strip().lower()
    aggregation = str(spec.get("aggregation") or "").strip().lower()
    wants_aggregate = bool(task_type == "kpi" or aggregation in {"sum", "avg", "average", "count", "min", "max"})

    mm = memory_meta if isinstance(memory_meta, dict) else {}
    anchors_applied = [str(x).strip() for x in list(mm.get("anchors_applied") or []) if str(x or "").strip()]
    try:
        curr_strength = int(mm.get("curr_strength") or 9)
    except Exception:
        curr_strength = 9
    weak_current_turn = curr_strength <= 2
    anchored_followup = bool(anchors_applied)

    if has_transform_hint and (weak_current_turn or anchored_followup):
        return True
    if wants_aggregate and weak_current_turn and anchored_followup:
        return True
    return False


def _promote_spec_to_transform_followup(*, spec_obj: Dict[str, Any]) -> Dict[str, Any]:
    spec = dict(spec_obj or {})
    spec["intent"] = "TRANSFORM_LAST"
    spec["task_class"] = "transform_followup"
    task_type = str(spec.get("task_type") or "").strip().lower()
    if task_type not in {"kpi", "detail", "ranking"}:
        spec["task_type"] = "detail"
    if str(spec.get("task_type") or "").strip().lower() == "kpi":
        aggregation = str(spec.get("aggregation") or "").strip().lower()
        if aggregation in {"", "none"}:
            spec["aggregation"] = "sum"
    return spec


def _sanitize_user_payload(*, payload: Dict[str, Any], business_spec: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload or {})
    typ = str(out.get("type") or "").strip().lower()
    if typ == "text":
        txt = str(out.get("text") or "").strip()
        if txt:
            lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
            if len(lines) > 1 and len(set(lines)) == 1:
                txt = lines[0]
            out["text"] = txt
        if _looks_like_system_error_text({"type": "text", "text": out.get("text")}):
            out["text"] = _unsupported_message_from_spec(business_spec)
            out.pop("_pending_state", None)
    elif typ == "error":
        out = {"type": "text", "text": _unsupported_message_from_spec(business_spec)}
    return out


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
        if not _is_write_enabled():
            early = _write_not_enabled_payload()
            spec_tool_msg = make_spec_tool_message(tool=source, mode="v7", envelope=spec_envelope)
            return _append_tool_message(early, spec_tool_msg)
        draft_payload = _build_write_draft_payload(message=message, spec=spec_obj, user=user)
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
        spec_obj=spec_obj,
        memory_meta=memory_meta,
        last_result_payload=last_result_payload,
    ):
        spec_obj = _promote_spec_to_transform_followup(spec_obj=spec_obj)
    entity_clarification = entity_resolution.get("clarification") if isinstance(entity_resolution.get("clarification"), dict) else None
    spec_envelope["spec"] = spec_obj
    spec_tool_msg = make_spec_tool_message(tool=source, mode="v7", envelope=spec_envelope)

    resolve_envelope = resolve_business_request(
        business_spec=spec_obj,
        message=message,
        user=user,
        topic_state=previous_topic_state,
    )
    resolve_tool_msg = make_resolver_tool_message(tool=source, mode="v7", envelope=resolve_envelope)
    resolved = resolve_envelope.get("resolved") if isinstance(resolve_envelope.get("resolved"), dict) else {}
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
    selected_report = str(resolved.get("selected_report") or "").strip()
    selected_score = resolved.get("selected_score")
    candidate_reports = []
    feasible_candidate_reports = []
    candidate_scores: Dict[str, Any] = {}
    for c in list(resolved.get("candidate_reports") or []):
        if not isinstance(c, dict):
            continue
        nm = str(c.get("report_name") or "").strip()
        if not nm:
            continue
        hard_blockers = [str(x).strip() for x in list(c.get("hard_blockers") or []) if str(x).strip()]
        if nm not in candidate_reports:
            candidate_reports.append(nm)
            candidate_scores[nm] = c.get("score")
        if (not hard_blockers) and (nm not in feasible_candidate_reports):
            feasible_candidate_reports.append(nm)
    if feasible_candidate_reports:
        candidate_reports = list(feasible_candidate_reports)
    if selected_report and selected_report not in candidate_reports:
        candidate_reports.insert(0, selected_report)
    candidate_cursor = candidate_reports.index(selected_report) if (selected_report and selected_report in candidate_reports) else 0

    seen_signatures = set()
    executed_steps = 0
    repair_attempts = 0
    candidate_switch_attempts = 0
    repeated_guard = False
    step_trace: List[Dict[str, Any]] = []
    top_candidates: List[Dict[str, Any]] = []
    for c in list(resolved.get("candidate_reports") or [])[:6]:
        if not isinstance(c, dict):
            continue
        top_candidates.append(
            {
                "report_name": str(c.get("report_name") or "").strip(),
                "score": c.get("score"),
                "hard_blockers": [str(x).strip() for x in list(c.get("hard_blockers") or []) if str(x).strip()],
                "missing_required_filter_values": [
                    str(x).strip() for x in list(c.get("missing_required_filter_values") or []) if str(x).strip()
                ],
                "reasons": [str(x) for x in list(c.get("reasons") or []) if str(x).strip()][:6],
            }
        )
    step_trace.append(
        {
            "step": 0,
            "action": "resolver_selected",
            "requested_metric": str((resolved.get("hard_constraints") or {}).get("metric") or ""),
            "requested_dimensions": list((resolved.get("hard_constraints") or {}).get("requested_dimensions") or []),
            "selected_report": str(selected_report or ""),
            "top_candidates": top_candidates,
        }
    )
    payload: Dict[str, Any] = {"type": "text", "text": "No output generated."}
    quality: Dict[str, Any] = {
        "verdict": VERDICT_HARD_FAIL,
        "failed_check_ids": ["QG00_NOT_EVALUATED"],
        "hard_fail_check_ids": ["QG00_NOT_EVALUATED"],
        "repairable_check_ids": [],
        "checks": [],
    }
    shaper_tool_msg = ""
    transform_tool_msg = ""
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

    for step_no in range(1, max(1, int(max_steps)) + 1):
        sig = f"{mode}|{source}|{selected_report}|{str(message or '').strip().lower()}|{json.dumps(plan_seed, sort_keys=True, default=str)}"
        if sig in seen_signatures:
            repeated_guard = True
            step_trace.append({"step": step_no, "action": "guard_stop", "signature_repeated": True})
            payload = {
                "type": "text",
                "text": "I couldn't progress this request safely due to a repeated execution path. Please restate the request in one sentence.",
            }
            quality = evaluate_quality_gate(
                business_spec=(spec_envelope.get("spec") if isinstance(spec_envelope.get("spec"), dict) else {}),
                resolved=resolved,
                payload=payload,
                repeated_call_guard_triggered=True,
            )
            break

        seen_signatures.add(sig)
        if mode == "continue":
            out = _execute_selected_report_direct(
                message=message,
                selected_report=selected_report,
                business_spec=spec_obj,
                export=export_requested,
                session_name=session_name,
                user=user,
            )
            if out is None:
                out = _legacy_path_unavailable_payload()
                action = "continue_unavailable"
            else:
                action = "direct_selected_report_continue"
        else:
            if str(spec_obj.get("intent") or "").strip().upper() == "TRANSFORM_LAST":
                from_last = _load_last_result_payload(session_name=session_name)
                if isinstance(from_last, dict):
                    out = from_last
                    action = "transform_from_last_result"
                else:
                    out = {
                        "type": "text",
                        "text": "I need a previous result in this chat to apply that transform.",
                    }
                    action = "transform_without_prior_result"
            elif isinstance(direct_doc_payload, dict):
                out = dict(direct_doc_payload)
                action = "direct_document_lookup"
            elif isinstance(direct_latest_payload, dict):
                out = dict(direct_latest_payload)
                action = "direct_latest_records_lookup"
            else:
                out = _execute_selected_report_direct(
                    message=message,
                    selected_report=selected_report,
                    business_spec=spec_obj,
                    export=export_requested,
                    session_name=session_name,
                    user=user,
                )
                if out is None:
                    out = _legacy_path_unavailable_payload()
                    action = "direct_selected_report_failed"
                else:
                    action = "direct_selected_report"

        executed_steps += 1
        auto_pending = _extract_auto_switch_pending(out if isinstance(out, dict) else {})
        if auto_pending is not None:
            qc = auto_pending.get("quality_clarification") if isinstance(auto_pending.get("quality_clarification"), dict) else {}
            suggested_report = str(
                qc.get("suggested_report")
                or qc.get("report_name")
                or auto_pending.get("report_name")
                or ""
            ).strip()
            switched = False

            if suggested_report:
                if suggested_report not in candidate_reports:
                    # Quality-triggered switching may only select resolver-feasible candidates.
                    suggested_report = ""
                if suggested_report in candidate_reports and (candidate_switch_attempts < 4):
                    suggested_idx = candidate_reports.index(suggested_report)
                    if suggested_idx != candidate_cursor or suggested_report != selected_report:
                        candidate_switch_attempts += 1
                        candidate_cursor = suggested_idx
                        selected_report = suggested_report
                        selected_score = candidate_scores.get(selected_report, selected_score)
                        resolved = dict(resolved)
                        resolved["selected_report"] = selected_report
                        resolved["selected_score"] = selected_score
                        switched = True
                        step_trace.append(
                            {
                                "step": step_no,
                                "action": "auto_switch_report_from_quality_pending",
                                "selected_report": selected_report,
                                "switch_attempt": candidate_switch_attempts,
                            }
                        )
                        continue

            if (not switched) and (candidate_cursor + 1 < len(candidate_reports)) and (candidate_switch_attempts < 4):
                candidate_switch_attempts += 1
                candidate_cursor += 1
                selected_report = candidate_reports[candidate_cursor]
                selected_score = candidate_scores.get(selected_report, selected_score)
                resolved = dict(resolved)
                resolved["selected_report"] = selected_report
                resolved["selected_score"] = selected_score
                step_trace.append(
                    {
                        "step": step_no,
                        "action": "auto_switch_next_candidate_from_quality_pending",
                        "selected_report": selected_report,
                        "switch_attempt": candidate_switch_attempts,
                    }
                )
                continue

            out = _legacy_path_unavailable_payload()
            step_trace.append({"step": step_no, "action": "auto_switch_pending_exhausted", "applied": False})
        wants_retry = bool(out.get(_INTERNAL_RETRY_KEY))
        step_trace.append({"step": step_no, "action": action, "retry_requested": wants_retry})
        out.pop(_INTERNAL_RETRY_KEY, None)
        payload = apply_transform_last(payload=_as_payload(out), business_spec=spec_obj)
        if _looks_like_system_error_text(payload):
            payload = {
                "type": "text",
                "text": "I hit a report execution issue for this request. Please adjust one filter (date/company/warehouse) and retry.",
            }
        transform_tool_msg = make_transform_tool_message(tool=source, mode=mode, payload=payload)
        payload = shape_response(payload=payload, business_spec=spec_obj)
        payload = _sanitize_user_payload(payload=payload, business_spec=spec_obj)
        payload = _apply_requested_entity_row_filters(payload=payload, business_spec=spec_obj)
        shaper_tool_msg = make_response_shaper_tool_message(tool=source, mode=mode, shaped_payload=payload)
        # Delegate output may resolve a different concrete report than resolver guess.
        # Align selected_report to executed payload for deterministic quality checks.
        payload_report = str(payload.get("report_name") or "").strip()
        if payload_report:
            selected_report = payload_report
            resolved = dict(resolved)
            resolved["selected_report"] = payload_report
            if payload_report not in candidate_reports:
                candidate_reports.append(payload_report)
            try:
                candidate_cursor = candidate_reports.index(payload_report)
            except Exception:
                pass

        quality = evaluate_quality_gate(
            business_spec=spec_obj,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        q_table = payload.get("table") if isinstance(payload.get("table"), dict) else {}
        q_rows = q_table.get("rows") if isinstance(q_table.get("rows"), list) else []
        q_cols = q_table.get("columns") if isinstance(q_table.get("columns"), list) else []
        step_trace.append(
            {
                "step": step_no,
                "quality_verdict": quality.get("verdict"),
                "failed_check_ids": list(quality.get("failed_check_ids") or []),
                "report_name": str(payload.get("report_name") or selected_report or ""),
                "row_count": len(q_rows),
                "column_labels": [
                    str((c.get("label") or c.get("fieldname") or "")).strip()
                    for c in q_cols[:10]
                    if isinstance(c, dict)
                ],
            }
        )

        if wants_retry and repair_attempts < 1:
            repair_attempts += 1
            continue

        if quality.get("verdict") == VERDICT_PASS:
            break

        if quality.get("verdict") == VERDICT_HARD_FAIL:
            break

        if _should_switch_candidate_on_repairable(
            quality=quality,
            intent=str(spec_obj.get("intent") or "").strip().upper(),
            task_class=str(spec_obj.get("task_class") or "").strip().lower(),
            candidate_cursor=candidate_cursor,
            candidate_reports=candidate_reports,
            candidate_switch_attempts=candidate_switch_attempts,
        ):
            candidate_switch_attempts += 1
            candidate_cursor += 1
            selected_report = candidate_reports[candidate_cursor]
            selected_score = candidate_scores.get(selected_report, selected_score)
            resolved = dict(resolved)
            resolved["selected_report"] = selected_report
            resolved["selected_score"] = selected_score
            step_trace.append(
                {
                    "step": step_no,
                    "action": "switch_candidate_after_quality_fail",
                    "selected_report": selected_report,
                }
            )
            continue

        # REPAIRABLE_FAIL path: one bounded replan/repair attempt maximum.
        if (
            quality.get("verdict") == VERDICT_REPAIRABLE_FAIL
            and (repair_attempts < 1)
            and str(spec_obj.get("intent") or "").strip().upper() != "TRANSFORM_LAST"
        ):
            repair_attempts += 1
            # Mark plan seed to allow exactly one deterministic replan signature.
            plan_seed["_repair_attempt"] = repair_attempts
            resolve_envelope = resolve_business_request(
                business_spec=spec_obj,
                user=user,
                topic_state=previous_topic_state,
            )
            resolved = resolve_envelope.get("resolved") if isinstance(resolve_envelope.get("resolved"), dict) else {}
            selected_report = str(resolved.get("selected_report") or "").strip()
            selected_score = resolved.get("selected_score")
            continue

        break

    # Final bounded fallback: avoid returning broken empty/wrong-shaped tables to users.
    if quality.get("verdict") == VERDICT_REPAIRABLE_FAIL:
        if str(spec_obj.get("intent") or "").strip().upper() == "TRANSFORM_LAST":
            pass
        else:
            if _quality_has_repairable_failure_class(
                quality,
                classes=["shape", "data", "constraint", "semantic"],
            ):
                unsupported = _unsupported_message_from_spec(spec_obj)
                clarify_text = default_clarification_question("hard_constraint_not_supported")
                planner_options = ["Switch to compatible report", "Keep current scope"]
                option_actions = _planner_option_actions(options=planner_options, pending={})
                payload = {
                    "type": "text",
                    "text": f"{unsupported} {clarify_text}",
                    "_pending_state": {
                        "mode": "planner_clarify",
                        "base_question": str(message or "").strip(),
                        "report_name": str(selected_report or "").strip(),
                        "filters_so_far": dict(spec_obj.get("filters") or {}) if isinstance(spec_obj.get("filters"), dict) else {},
                        "clarification_question": f"{unsupported} {clarify_text}",
                        "clarification_options": list(planner_options),
                        "options": list(planner_options),
                        "option_actions": dict(option_actions),
                        "clarification_reason": "hard_constraint_not_supported",
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
                clarify_decision = {
                    "should_clarify": True,
                    "reason": "hard_constraint_not_supported",
                    "question": f"{unsupported} {clarify_text}",
                    "policy_version": "phase5_blocker_only_v1",
                }
                quality = evaluate_quality_gate(
                    business_spec=spec_obj,
                    resolved=resolved,
                    payload=payload,
                    repeated_call_guard_triggered=False,
                )

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
