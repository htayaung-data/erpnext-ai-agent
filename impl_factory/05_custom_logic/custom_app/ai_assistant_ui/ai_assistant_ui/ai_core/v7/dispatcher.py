from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional

try:
    import frappe  # type: ignore
except Exception:  # pragma: no cover - allows local tests without Frappe runtime
    frappe = None

from ai_assistant_ui.ai_core.v7.runtime import report_qa_continue_v7, report_qa_start_v7


def is_report_qa_tool(name: str) -> bool:
    return str(name or "").strip() in ("report_qa_start", "report_qa_continue")


def _call_tool(fn: Callable[..., Dict[str, Any]], *, args: Dict[str, Any], session_name: Optional[str], user: Optional[str]) -> Dict[str, Any]:
    kwargs = dict(args or {})
    if "session_name" in fn.__code__.co_varnames:
        kwargs["session_name"] = session_name
    if "user" in fn.__code__.co_varnames:
        default_user = getattr(getattr(frappe, "session", None), "user", None) if frappe is not None else None
        kwargs["user"] = user or default_user
    out = fn(**kwargs)
    return out if isinstance(out, dict) else {"type": "text", "text": str(out)}


def _append_route_message(
    payload: Dict[str, Any],
    *,
    mode: str,
    tool: str,
    executed_engine: str,
    route: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    out = dict(payload or {})
    msgs = list(out.get("_tool_messages") or [])
    route = route if isinstance(route, dict) else {}
    msgs.append(
        json.dumps(
            {
                "type": "engine_route",
                "phase": "phase8",
                "mode": mode,
                "tool": tool,
                "executed_engine": executed_engine,
                "configured_mode": str(route.get("configured_mode") or mode),
                "effective_mode": str(route.get("effective_mode") or mode),
                "canary_percent": route.get("canary_percent"),
                "canary_bucket": route.get("bucket"),
            },
            ensure_ascii=False,
        )
    )
    out["_tool_messages"] = msgs
    return out


def dispatch_report_qa(*, tool_name: str, args: Dict[str, Any], session_name: Optional[str], user: Optional[str]) -> Dict[str, Any]:
    name = str(tool_name or "").strip()

    if name == "report_qa_start":
        v7_fn: Callable[..., Dict[str, Any]] = report_qa_start_v7
    elif name == "report_qa_continue":
        v7_fn = report_qa_continue_v7
    else:
        raise KeyError(f"Unsupported report_qa tool: {name}")

    return _append_route_message(
        _call_tool(v7_fn, args=args, session_name=session_name, user=user),
        mode="v7_active",
        tool=name,
        executed_engine="v7",
        route={"configured_mode": "v7_active", "effective_mode": "v7_active"},
    )
