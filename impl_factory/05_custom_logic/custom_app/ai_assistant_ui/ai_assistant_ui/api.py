from __future__ import annotations

import frappe
from frappe.utils.file_lock import LockTimeoutError
from frappe.utils.synchronization import filelock

from ai_assistant_ui.qwen_chat.service import QWEN_SESSION_DOCTYPE, handle_qwen_user_message

def _get_qwen_session(session_name: str):
	doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, session_name)
	if doc.owner != frappe.session.user and not frappe.has_permission(QWEN_SESSION_DOCTYPE, "read", doc=doc):
		frappe.throw("Not permitted.")
	return doc


def _qwen_session_lock_name(session_name: str) -> str:
	return f"qwen_chat_session::{str(session_name or '').strip()}"


@frappe.whitelist()
def get_qwen_sessions():
	rows = frappe.get_all(
		QWEN_SESSION_DOCTYPE,
		filters={"owner": frappe.session.user},
		fields=["name", "title", "modified"],
		order_by="modified desc",
		limit=200,
	)
	return [{"name": r["name"], "title": (r.get("title") or r["name"])} for r in rows]


@frappe.whitelist()
def create_qwen_session(title: str | None = None):
	doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
	doc.title = (title or "New Qwen Chat").strip() or "New Qwen Chat"
	doc.insert(ignore_permissions=False)
	return {"name": doc.name, "title": doc.title}


@frappe.whitelist()
def rename_qwen_session(session_name: str, title: str):
	doc = _get_qwen_session(session_name)
	doc.title = (title or "").strip() or doc.title
	doc.save(ignore_permissions=False)
	return {"ok": True, "name": doc.name, "title": doc.title}


@frappe.whitelist()
def delete_qwen_session(session_name: str):
	doc = _get_qwen_session(session_name)
	frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
	return {"ok": True}


@frappe.whitelist()
def get_qwen_messages(session_name: str, debug: int | None = None):
	doc = _get_qwen_session(session_name)
	include_tool = bool(int(debug or 0))

	out = []
	for m in doc.get("messages") or []:
		role = (m.role or "").lower()
		if role == "tool" and not include_tool:
			continue
		out.append({"role": role, "content": m.content, "idx": m.idx})
	return out


@frappe.whitelist()
def qwen_chat_send(session_name: str, message: str):
	_get_qwen_session(session_name)

	try:
		with filelock(_qwen_session_lock_name(session_name), timeout=1):
			ok, payload = handle_qwen_user_message(
				session_name=session_name,
				message=message,
				user=frappe.session.user,
			)
	except LockTimeoutError:
		return {
			"ok": False,
			"error": "Please wait for the current Qwen response to finish before sending another message in this chat.",
		}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Qwen Assistant: qwen_chat_send crashed")
		return {"ok": False, "error": "Internal error. Please try again."}

	if ok:
		return payload if isinstance(payload, dict) else {"ok": True}
	return {"ok": False, "error": payload}
