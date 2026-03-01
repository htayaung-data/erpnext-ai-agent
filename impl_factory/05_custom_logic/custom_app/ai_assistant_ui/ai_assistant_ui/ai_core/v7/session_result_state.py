from __future__ import annotations

from typing import Any, Callable, Dict, Optional


def latest_active_result_meta(*, session_doc: Any, safe_json_obj: Callable[[Any], Dict[str, Any]]) -> Dict[str, Any]:
    for message in reversed(session_doc.get("messages") or []):
        if str(message.role or "").strip().lower() != "tool":
            continue
        obj = safe_json_obj(message.content)
        if str(obj.get("type") or "").strip() != "v7_topic_state":
            continue
        state = obj.get("state") if isinstance(obj.get("state"), dict) else {}
        active_result = state.get("active_result") if isinstance(state.get("active_result"), dict) else {}
        return dict(active_result)
    return {}


def apply_active_result_meta(payload: Dict[str, Any], *, active_result_meta: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload or {})
    meta = active_result_meta if isinstance(active_result_meta, dict) else {}
    payload_report = str(out.get("report_name") or "").strip().lower()
    meta_report = str(meta.get("report_name") or "").strip().lower()
    report_matches = bool((not meta_report) or (payload_report and payload_report == meta_report))
    if not report_matches:
        return out
    scaled_unit = str(meta.get("scaled_unit") or "").strip().lower()
    if ("_scaled_unit" not in out) and scaled_unit:
        out["_scaled_unit"] = scaled_unit
    output_mode = str(meta.get("output_mode") or "").strip().lower()
    if ("_output_mode" not in out) and output_mode:
        out["_output_mode"] = output_mode
    return out


def load_last_result_payload(
    *,
    session_name: Optional[str],
    frappe_module: Any,
    safe_json_obj: Callable[[Any], Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if (not session_name) or (frappe_module is None):
        return None
    try:
        session_doc = frappe_module.get_doc("AI Chat Session", session_name)
    except Exception:
        return None

    active_result_meta = latest_active_result_meta(session_doc=session_doc, safe_json_obj=safe_json_obj)
    active_report_name = str(active_result_meta.get("report_name") or "").strip()

    def _assistant_report_payload(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if str(obj.get("type") or "").strip().lower() != "report_table":
            return None
        table = obj.get("table") if isinstance(obj.get("table"), dict) else {}
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        cols = table.get("columns") if isinstance(table.get("columns"), list) else []
        if not rows or not cols:
            return None
        out = {
            "type": "report_table",
            "report_name": str(obj.get("report_name") or "").strip(),
            "title": str(obj.get("title") or obj.get("report_name") or "Previous Result").strip(),
            "table": {"columns": cols, "rows": rows},
        }
        for key in ("_transform_last_applied", "_scaled_unit", "_output_mode", "_source_columns", "_source_table"):
            if key in obj:
                out[key] = obj.get(key)
        return apply_active_result_meta(out, active_result_meta=active_result_meta)

    if active_report_name:
        for message in reversed(session_doc.get("messages") or []):
            if str(message.role or "").strip().lower() != "assistant":
                continue
            obj = safe_json_obj(message.content)
            payload = _assistant_report_payload(obj)
            if not isinstance(payload, dict):
                continue
            if str(payload.get("report_name") or "").strip().lower() != active_report_name.lower():
                continue
            return payload

    for message in reversed(session_doc.get("messages") or []):
        if str(message.role or "").strip().lower() != "assistant":
            continue
        obj = safe_json_obj(message.content)
        payload = _assistant_report_payload(obj)
        if not isinstance(payload, dict):
            continue
        return payload

    for message in reversed(session_doc.get("messages") or []):
        if str(message.role or "").strip().lower() != "tool":
            continue
        obj = safe_json_obj(message.content)
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
        for key in ("_transform_last_applied", "_scaled_unit", "_output_mode"):
            if key in obj:
                out[key] = obj.get(key)
        return apply_active_result_meta(out, active_result_meta=active_result_meta)
    return None


def capture_source_columns(payload: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload or {})
    table = out.get("table") if isinstance(out.get("table"), dict) else {}
    cols = [col for col in list(table.get("columns") or []) if isinstance(col, dict)]
    rows = [row for row in list(table.get("rows") or []) if isinstance(row, dict)]
    if cols and (not list(out.get("_source_columns") or [])):
        out["_source_columns"] = [
            {
                "fieldname": str(col.get("fieldname") or "").strip(),
                "label": str(col.get("label") or col.get("fieldname") or "").strip(),
                "fieldtype": str(col.get("fieldtype") or "").strip(),
            }
            for col in cols
            if str(col.get("fieldname") or col.get("label") or "").strip()
        ][:40]
    if cols and rows and (not isinstance(out.get("_source_table"), dict)):
        out["_source_table"] = {
            "columns": [dict(col) for col in cols[:40]],
            "rows": [dict(row) for row in rows[:500]],
        }
    return out
