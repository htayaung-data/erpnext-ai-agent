from __future__ import annotations

import frappe

from ai_assistant_ui.ai_core.chat.service import handle_user_message

SESSION_DOCTYPE = "AI Chat Session"


def _get_session(session_name: str):
    doc = frappe.get_doc(SESSION_DOCTYPE, session_name)
    if doc.owner != frappe.session.user and not frappe.has_permission(SESSION_DOCTYPE, "read", doc=doc):
        frappe.throw("Not permitted.")
    return doc


@frappe.whitelist()
def get_sessions():
    rows = frappe.get_all(
        SESSION_DOCTYPE,
        filters={"owner": frappe.session.user},
        fields=["name", "title", "modified"],
        order_by="modified desc",
        limit=200,
    )
    return [{"name": r["name"], "title": (r.get("title") or r["name"])} for r in rows]


@frappe.whitelist()
def create_session(title: str | None = None):
    doc = frappe.new_doc(SESSION_DOCTYPE)
    doc.title = (title or "New Chat").strip() or "New Chat"
    doc.insert(ignore_permissions=False)
    return {"name": doc.name, "title": doc.title}


@frappe.whitelist()
def rename_session(session_name: str, title: str):
    doc = _get_session(session_name)
    doc.title = (title or "").strip() or doc.title
    doc.save(ignore_permissions=False)
    return {"ok": True, "name": doc.name, "title": doc.title}


@frappe.whitelist()
def delete_session(session_name: str):
    doc = _get_session(session_name)
    frappe.delete_doc(SESSION_DOCTYPE, doc.name, ignore_permissions=False)
    return {"ok": True}


@frappe.whitelist()
def get_messages(session_name: str, debug: int | None = None):
    """
    Commercial default: return ONLY user+assistant messages.
    debug=1: include internal tool/audit messages (developer only).
    """
    doc = _get_session(session_name)
    include_tool = bool(int(debug or 0))

    out = []
    for m in doc.get("messages") or []:
        role = (m.role or "").lower()
        if role == "tool" and not include_tool:
            continue
        out.append({"role": role, "content": m.content, "idx": m.idx})
    return out


@frappe.whitelist()
def chat_send(session_name: str, message: str):
    _get_session(session_name)

    try:
        ok, err_or_payload = handle_user_message(
            session_name=session_name,
            message=message,
            user=frappe.session.user,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "AI Assistant: chat_send crashed")
        return {"ok": False, "error": "Internal error. Please try again."}

    if ok:
        return {"ok": True}
    return {"ok": False, "error": err_or_payload}
