import json
import frappe

HIDDEN_STATE_TOOL = "__state__"


def assert_session_access(session_doc):
    user = frappe.session.user
    if user == "Administrator":
        return
    if getattr(session_doc, "owner", None) != user:
        raise frappe.PermissionError("Not permitted.")


def build_session_doc_for_user(title=None):
    user = frappe.session.user
    title = (title or "").strip()[:140] or "New Chat"
    return frappe.get_doc({"doctype": "AI Chat Session", "title": title, "owner": user, "messages": []})


def list_user_sessions(limit=50):
    user = frappe.session.user
    return frappe.get_all(
        "AI Chat Session",
        filters={"owner": user},
        fields=["name", "title", "modified"],
        order_by="modified desc",
        limit=int(limit or 50),
    )


def get_session_messages(session_doc, limit=200):
    out = []
    for row in (session_doc.get("messages") or [])[-int(limit or 200):]:
        out.append(
            {"name": row.name, "role": row.role, "content": row.content, "creation": getattr(row, "creation", None)}
        )
    return out


def _safe_json_loads(s):
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def load_state_from_messages(messages):
    base = {
        "language": "en",
        "company": None,
        "last_report": None,
        "last_filters": None,
        "last_date_range": None,
        "pending_actions": [],
    }
    if not messages:
        return base

    for m in reversed(messages):
        if m.get("role") != "tool":
            continue
        j = _safe_json_loads(m.get("content"))
        if isinstance(j, dict) and j.get("tool") == HIDDEN_STATE_TOOL and j.get("ui_hidden") is True:
            st = j.get("state") or {}
            for k, v in base.items():
                st.setdefault(k, v)
            if not isinstance(st.get("pending_actions"), list):
                st["pending_actions"] = []
            return st

    return base


def upsert_hidden_state_message(session_doc, state: dict):
    payload = {"tool": HIDDEN_STATE_TOOL, "ui_hidden": True, "state": state or {}}
    session_doc.append("messages", {"role": "tool", "content": json.dumps(payload, ensure_ascii=False, default=str)})
