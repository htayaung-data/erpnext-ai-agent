from __future__ import annotations

import json
import datetime as dt
from typing import Any, Dict, Optional


def _json_default(o: Any):
    try:
        if isinstance(o, (dt.date, dt.datetime)):
            return o.isoformat()
        try:
            import decimal
            if isinstance(o, decimal.Decimal):
                return float(o)
        except Exception:
            pass
        return str(o)
    except Exception:
        return "<non-serializable>"


def _try_parse_json(s: str) -> Optional[Dict[str, Any]]:
    if not s:
        return None
    ss = s.strip()
    if not (ss.startswith("{") and ss.endswith("}")):
        return None
    try:
        obj = json.loads(ss)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def get_pending_state(session_doc) -> Optional[Dict[str, Any]]:
    """
    Reads newest-to-oldest tool messages for:
      {"type":"pending_state","state":{...}} or {"type":"pending_state","cleared":true}
    Returns latest pending state or None.
    """
    for m in reversed(session_doc.get("messages") or []):
        if (m.role or "").lower() != "tool":
            continue
        obj = _try_parse_json(m.content or "")
        if not obj:
            continue
        if obj.get("type") != "pending_state":
            continue
        if obj.get("cleared"):
            return None
        st = obj.get("state")
        return st if isinstance(st, dict) else None
    return None


def make_pending_state_message(state: Optional[Dict[str, Any]] = None, *, cleared: bool = False) -> str:
    try:
        if cleared:
            return json.dumps({"type": "pending_state", "cleared": True}, ensure_ascii=False, default=_json_default)
        return json.dumps({"type": "pending_state", "state": state or {}}, ensure_ascii=False, default=_json_default)
    except Exception:
        # never break chat on pending-state serialization
        return json.dumps({"type": "pending_state", "cleared": True}, ensure_ascii=False, default=str)
