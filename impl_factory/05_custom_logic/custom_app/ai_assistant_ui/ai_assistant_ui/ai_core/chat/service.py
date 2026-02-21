from __future__ import annotations

import json
import datetime as dt
import hashlib
import time
import uuid
from typing import Any, Dict, Optional, Tuple, List

import frappe

from ai_assistant_ui.ai_core.chat.pending_state import get_pending_state, make_pending_state_message
from ai_assistant_ui.ai_core.chat.turn_audit import pop_last_planner_output, clear_last_planner_output
from ai_assistant_ui.ai_core.llm.report_planner import choose_pending_mode
from ai_assistant_ui.ai_core.tools.registry import ToolInvocation, run_tool


def _append_message(session_doc, role: str, content: Any) -> None:
    """
    Always store string content in the child table.
    Never allow non-string types to reach the DB layer.
    """
    if content is None:
        content = ""
    elif not isinstance(content, str):
        content = str(content)
    session_doc.append("messages", {"role": role, "content": content})


def _is_date_like(x: Any) -> bool:
    try:
        return isinstance(x, (dt.date, dt.datetime))
    except Exception:
        return False


def _make_json_safe(obj: Any) -> Any:
    """
    Recursively convert to JSON-safe primitives.
    MUST NOT throw.
    """
    try:
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj

        if _is_date_like(obj):
            try:
                return obj.isoformat()
            except Exception:
                return str(obj)

        try:
            import decimal
            if isinstance(obj, decimal.Decimal):
                return float(obj)
        except Exception:
            pass

        if isinstance(obj, dict):
            return {str(k): _make_json_safe(v) for k, v in obj.items()}

        if isinstance(obj, (list, tuple, set)):
            return [_make_json_safe(v) for v in obj]

        return str(obj)
    except Exception:
        return str(obj)


def _safe_json_dumps(obj: Any) -> str:
    """
    MUST NEVER throw. `default=str` is the final safety net.
    """
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        try:
            return json.dumps(str(obj), ensure_ascii=False)
        except Exception:
            return "{\"type\":\"text\",\"text\":\"Internal serialization error.\"}"


def _as_json_str(payload: Any) -> str:
    """
    MUST NEVER throw.
    Used to store assistant payloads (tables, text, etc.) safely.
    """
    try:
        if isinstance(payload, (dict, list)):
            return _safe_json_dumps(_make_json_safe(payload))
        return str(payload)
    except Exception:
        return "{\"type\":\"text\",\"text\":\"Internal serialization error.\"}"


def _sanitize_user_payload(payload: Any) -> Any:
    """
    Commercial UX rule: no internal leakage in user-visible assistant payloads.
    - remove debug blocks
    - remove raw filter fieldnames (internal)
    - remove orchestration keys
    """
    try:
        if not isinstance(payload, dict):
            return payload

        clean = dict(payload)

        # Internal-only fields
        clean.pop("debug", None)
        clean.pop("filters", None)

        # Never leak orchestration internals
        clean.pop("_tool_messages", None)
        clean.pop("_pending_state", None)
        clean.pop("_clear_pending_state", None)

        return clean
    except Exception:
        return payload


def _tool_result_message(tool: str, ok: bool, error: Optional[str] = None) -> str:
    obj: Dict[str, Any] = {"type": "tool_result", "tool": tool, "ok": bool(ok)}
    if error:
        obj["error"] = str(error)
    return _safe_json_dumps(obj)


def _now_iso_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hash_payload(payload: Any) -> str:
    s = _as_json_str(payload)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _response_snapshot(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        txt = str(payload or "").strip()
        return {"type": "text", "preview": txt[:280]}

    typ = str(payload.get("type") or "text")
    if typ == "report_table":
        table = payload.get("table") if isinstance(payload.get("table"), dict) else {}
        cols = table.get("columns") if isinstance(table.get("columns"), list) else []
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        return {
            "type": "report_table",
            "title": payload.get("title"),
            "rows": len(rows),
            "columns": len(cols),
            "download_count": len(payload.get("downloads") or []),
        }
    if typ in ("text", "error"):
        return {"type": typ, "preview": str(payload.get("text") or "").strip()[:280]}
    return {"type": typ}


def _intent_from_turn(
    *,
    planner_output: Optional[Dict[str, Any]],
    invocation: ToolInvocation,
    pending_mode: str,
    user_payload: Dict[str, Any],
) -> str:
    plan = planner_output.get("plan") if isinstance(planner_output, dict) else {}
    action = str((plan or {}).get("action") or "").strip().lower()
    if action == "run_report":
        return "EXPORT" if (user_payload.get("downloads") or []) else "READ"
    if action == "transform_last":
        return "TRANSFORM"
    if action == "write_draft":
        return "WRITE_DRAFT"
    if action == "clarify":
        return "READ"

    if pending_mode == "write_confirmation":
        return "WRITE_CONFIRM"
    if invocation.name == "report_qa_continue":
        return "READ"
    if (user_payload.get("downloads") or []):
        return "EXPORT"
    return "READ"


def _tool_invocation_summary(invocation: ToolInvocation, *, pending_mode: str, pending_overridden: bool) -> Dict[str, Any]:
    return {
        "tool": invocation.name,
        "arg_keys": sorted([str(k) for k in (invocation.args or {}).keys()]),
        "pending_mode": pending_mode or None,
        "pending_overridden": bool(pending_overridden),
    }


def _safe_user_error_text(code: str) -> str:
    if code == "EMPTY_MESSAGE":
        return "Please enter a message."
    return "I couldn’t process that request right now. Please try again."


def _error_envelope(*, code: str, stage: str, trace_id: str, message: str = "") -> Dict[str, Any]:
    out = {
        "type": "error_envelope",
        "code": str(code),
        "stage": str(stage),
        "trace_id": str(trace_id),
        "user_safe_message": _safe_user_error_text(code),
    }
    msg = str(message or "").strip()
    if msg:
        out["internal_error"] = msg[:280]
    return out


def _audit_turn_message(
    *,
    turn_id: str,
    session_name: str,
    user: str,
    message_text: str,
    started_ts: float,
    invocation: ToolInvocation,
    pending_mode: str,
    pending_overridden: bool,
    planner_output: Optional[Dict[str, Any]],
    user_payload: Dict[str, Any],
    error_envelope: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    elapsed_ms = int(max(0.0, (time.time() - started_ts) * 1000.0))
    intent = _intent_from_turn(
        planner_output=planner_output,
        invocation=invocation,
        pending_mode=pending_mode,
        user_payload=user_payload,
    )
    result_hash = _hash_payload(user_payload)
    return {
        "type": "audit_turn",
        "version": "1.0",
        "ts": _now_iso_utc(),
        "turn_id": turn_id,
        "session_name": session_name,
        "user": user,
        "message_preview": (message_text or "").strip()[:240],
        "intent": intent,
        "planner_output": planner_output,
        "tool_invocation_summary": _tool_invocation_summary(
            invocation,
            pending_mode=pending_mode,
            pending_overridden=pending_overridden,
        ),
        "result_meta": {
            "payload_type": str(user_payload.get("type") or "text"),
            "payload_hash_sha256": result_hash,
            "duration_ms": elapsed_ms,
        },
        "user_visible_response": _response_snapshot(user_payload),
        "error_envelope": error_envelope,
    }


def _recent_user_assistant(session_doc, limit: int = 5) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for m in reversed(session_doc.get("messages") or []):
        role = (m.role or "").lower()
        if role not in ("user", "assistant"):
            continue
        content = (m.content or "").strip()
        if not content:
            continue
        out.append({"role": role, "content": content[:1200]})
        if len(out) >= limit:
            break
    return list(reversed(out))


def _pending_mode(pending: Optional[Dict[str, Any]]) -> str:
    if not isinstance(pending, dict):
        return ""
    return str(pending.get("mode") or "").strip().lower()


def _is_write_confirmation_reply(msg: str) -> bool:
    s = str(msg or "").strip().lower()
    if not s:
        return False
    tokens = ("confirm", "yes", "proceed", "cancel", "stop", "no", "abort", "do it", "ok", "okay")
    return any(t in s for t in tokens)


def handle_user_message(
    *,
    session_name: str,
    message: str,
    user: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Main entrypoint from api.chat_send.
    Must never crash the request from serialization.
    """
    user = user or frappe.session.user
    msg = (message or "").strip()
    turn_id = uuid.uuid4().hex[:12]
    started_ts = time.time()
    if not msg:
        return False, _safe_user_error_text("EMPTY_MESSAGE")

    session_doc = frappe.get_doc("AI Chat Session", session_name)

    # set title if new
    if (session_doc.title or "").strip() in ("", "New Chat"):
        session_doc.title = (msg[:60] + "…") if len(msg) > 60 else msg

    # 1) save user message
    _append_message(session_doc, "user", msg)

    # 2) decide tool invocation
    pending = get_pending_state(session_doc)
    inv: ToolInvocation
    pending_overridden = False
    pending_mode = _pending_mode(pending)
    if pending:
        if pending_mode == "write_confirmation":
            mode = "continue_pending" if _is_write_confirmation_reply(msg) else "start_new"
        else:
            mode = choose_pending_mode(
                user_message=msg,
                pending_state=pending,
                recent_messages=_recent_user_assistant(session_doc),
            )
        if mode == "continue_pending":
            inv = ToolInvocation(name="report_qa_continue", args={"message": msg, "pending_state": pending})
        else:
            # ChatGPT-style topic switching: abandon previous pending flow.
            inv = ToolInvocation(name="report_qa_start", args={"message": msg})
            pending_overridden = True
    else:
        inv = ToolInvocation(name="report_qa_start", args={"message": msg})

    # 3) execute tool
    clear_last_planner_output()
    try:
        result = run_tool(inv, session_name=session_name, user=user)
        if not isinstance(result, dict):
            raise ValueError("Tool returned non-dict payload.")
        _append_message(session_doc, "tool", _tool_result_message(inv.name, ok=True))
    except Exception as e:
        trace_id = uuid.uuid4().hex[:12]
        err = str(e or "")
        frappe.log_error(frappe.get_traceback(), f"AI Assistant: turn failed [{trace_id}]")
        _append_message(session_doc, "tool", _tool_result_message(inv.name, ok=False, error="failed"))
        err_env = _error_envelope(code="TOOL_EXECUTION_FAILED", stage="run_tool", trace_id=trace_id, message=err)
        _append_message(session_doc, "tool", _safe_json_dumps(err_env))
        user_payload = {"type": "error", "text": _safe_user_error_text("TOOL_EXECUTION_FAILED")}
        _append_message(
            session_doc,
            "tool",
            _safe_json_dumps(
                _audit_turn_message(
                    turn_id=turn_id,
                    session_name=session_name,
                    user=str(user),
                    message_text=msg,
                    started_ts=started_ts,
                    invocation=inv,
                    pending_mode=pending_mode,
                    pending_overridden=pending_overridden,
                    planner_output=pop_last_planner_output(),
                    user_payload=user_payload,
                    error_envelope=err_env,
                )
            ),
        )
        _append_message(session_doc, "assistant", _safe_json_dumps(user_payload))
        session_doc.save()
        return False, _safe_user_error_text("TOOL_EXECUTION_FAILED")

    # 4) allow tools to emit hidden tool/audit messages
    tool_msgs: List[str] = []
    try:
        raw_tool_msgs = result.pop("_tool_messages", None)
        if isinstance(raw_tool_msgs, list):
            tool_msgs = [str(x) for x in raw_tool_msgs if x is not None]
    except Exception:
        tool_msgs = []

    for tm in tool_msgs:
        _append_message(session_doc, "tool", tm)

    # 5) pending state updates
    pending_state_to_set = result.pop("_pending_state", None)
    clear_pending = bool(result.pop("_clear_pending_state", False))

    if pending_overridden:
        _append_message(session_doc, "tool", make_pending_state_message(cleared=True))

    if clear_pending:
        _append_message(session_doc, "tool", make_pending_state_message(cleared=True))
    elif isinstance(pending_state_to_set, dict):
        _append_message(session_doc, "tool", make_pending_state_message(state=pending_state_to_set))

    # 6) save assistant message (sanitize first)
    result = _sanitize_user_payload(result)
    planner_output = pop_last_planner_output()
    _append_message(session_doc, "assistant", _as_json_str(result))
    _append_message(
        session_doc,
        "tool",
        _safe_json_dumps(
            _audit_turn_message(
                turn_id=turn_id,
                session_name=session_name,
                user=str(user),
                message_text=msg,
                started_ts=started_ts,
                invocation=inv,
                pending_mode=pending_mode,
                pending_overridden=pending_overridden,
                planner_output=planner_output,
                user_payload=result if isinstance(result, dict) else {"type": "text", "text": str(result)},
                error_envelope=None,
            )
        ),
    )
    session_doc.save()

    return True, _as_json_str(result)
