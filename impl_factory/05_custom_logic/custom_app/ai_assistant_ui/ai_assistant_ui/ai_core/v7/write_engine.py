from __future__ import annotations

import json
import uuid
from typing import Any, Callable, Dict, Optional

_EXECUTED_IDEMPOTENCY_KEYS = set()

_CONFIRM_WORDS = {"confirm", "yes", "proceed", "approve", "execute", "do it", "ok", "okay"}
_CANCEL_WORDS = {"cancel", "no", "stop", "abort", "discard"}


def _safe_str(v: Any) -> str:
    return str(v or "").strip()


def is_explicit_confirm(decision: str) -> bool:
    s = _safe_str(decision).lower()
    return any(w in s for w in _CONFIRM_WORDS)


def is_explicit_cancel(decision: str) -> bool:
    s = _safe_str(decision).lower()
    return any(w in s for w in _CANCEL_WORDS)


def create_write_draft(
    *,
    doctype: str,
    operation: str,
    payload: Dict[str, Any],
    user: Optional[str],
    summary: str = "",
    idempotency_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Phase-7 isolated write draft state machine entry.
    """
    doc = _safe_str(doctype)
    op = _safe_str(operation).lower()
    body = payload if isinstance(payload, dict) else {}
    idem = _safe_str(idempotency_key) or uuid.uuid4().hex

    pending = {
        "mode": "write_confirmation",
        "write_draft": {
            "doctype": doc,
            "operation": op,
            "payload": body,
            "summary": _safe_str(summary)[:280],
            "requested_by": _safe_str(user),
            "idempotency_key": idem,
        },
    }
    text = f"Draft ready: {op} {doc}. Confirm to execute or cancel."
    return {
        "type": "text",
        "text": text,
        "_pending_state": pending,
        "_phase": "phase7_write_engine",
    }


def _simulated_execute(draft: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "success",
        "doctype": draft.get("doctype"),
        "operation": draft.get("operation"),
        "idempotency_key": draft.get("idempotency_key"),
    }


def execute_write_flow(
    *,
    draft: Dict[str, Any],
    decision: str,
    execute_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Phase-7 write safety contract:
    - no execution without explicit confirm
    - explicit cancel clears pending
    - idempotency blocks duplicate execution
    """
    d = draft if isinstance(draft, dict) else {}
    write_draft = d.get("write_draft") if isinstance(d.get("write_draft"), dict) else d

    if not write_draft:
        return {
            "type": "text",
            "text": "No pending write draft found.",
            "_phase": "phase7_write_engine",
            "_clear_pending_state": True,
        }

    if is_explicit_cancel(decision):
        return {
            "type": "text",
            "text": "Write action cancelled.",
            "_phase": "phase7_write_engine",
            "_clear_pending_state": True,
        }

    if not is_explicit_confirm(decision):
        return {
            "type": "text",
            "text": "Write draft is pending. Please confirm or cancel.",
            "_phase": "phase7_write_engine",
            "_pending_state": {"mode": "write_confirmation", "write_draft": write_draft},
        }

    idem = _safe_str(write_draft.get("idempotency_key"))
    if idem and idem in _EXECUTED_IDEMPOTENCY_KEYS:
        return {
            "type": "text",
            "text": "This write action was already executed (idempotency guard).",
            "_phase": "phase7_write_engine",
            "_clear_pending_state": True,
            "_write_result": {"status": "duplicate_blocked", "idempotency_key": idem},
        }

    runner = execute_fn or _simulated_execute
    try:
        result = runner(write_draft)
    except Exception as exc:
        return {
            "type": "text",
            "text": "Write execution failed safely. Draft remains pending.",
            "_phase": "phase7_write_engine",
            "_pending_state": {"mode": "write_confirmation", "write_draft": write_draft},
            "_write_result": {"status": "error", "error": str(exc)[:220]},
        }

    if idem:
        _EXECUTED_IDEMPOTENCY_KEYS.add(idem)
    return {
        "type": "text",
        "text": "Write action executed successfully.",
        "_phase": "phase7_write_engine",
        "_clear_pending_state": True,
        "_write_result": result if isinstance(result, dict) else {"status": "success"},
    }


def make_write_engine_tool_message(*, tool: str, decision: str, output: Dict[str, Any]) -> str:
    out = output if isinstance(output, dict) else {}
    return json.dumps(
        {
            "type": "v7_write_engine",
            "phase": "phase7",
            "tool": _safe_str(tool),
            "decision": _safe_str(decision).lower(),
            "cleared_pending": bool(out.get("_clear_pending_state")),
            "has_pending": isinstance(out.get("_pending_state"), dict),
            "has_write_result": isinstance(out.get("_write_result"), dict),
        },
        ensure_ascii=False,
        default=str,
    )

