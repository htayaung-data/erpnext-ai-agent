from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
	return str(value or "").strip()


def run_nbu_governed_requery_smoke() -> Dict[str, Any]:
	"""Run a live smoke for NBU-governed requery from visible context.

	The smoke proves the FC6 path: a user can start from a visible AR table,
	select a row naturally, then ask for a compatible field missing from that
	table. The assistant should use an approved entity-detail lookup instead of
	repeating row facts or falling into route clarification.
	"""

	import frappe

	from ai_assistant_ui.qwen_chat.service import (
		QWEN_SESSION_DOCTYPE,
		_latest_assistant_payload,
		handle_qwen_user_message,
	)

	doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
	doc.title = "NBU Governed Requery Smoke"
	doc.insert(ignore_permissions=False)
	frappe.db.commit()
	results: Dict[str, Any] = {"session": doc.name}
	try:
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show customer risk",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Initial customer-risk request failed.")
		results["initial_mode"] = _text((payload or {}).get("mode"))

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="who is in second position in the above table?",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Visible-row selection failed before requery.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		selection_text = _text(_latest_assistant_payload(session_doc).get("text"))
		if "35th Street Mobile Wholesale" not in selection_text:
			raise RuntimeError(f"Selection did not resolve the expected row: {selection_text[:240]}")
		results["selection_mode"] = _text((payload or {}).get("mode"))
		results["selection_answer"] = selection_text[:240]

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="what is the credit limit of that customer?",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Governed requery follow-up failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		answer_text = _text(_latest_assistant_payload(session_doc).get("text"))
		answer_lower = answer_text.lower()
		if "credit limit" not in answer_lower:
			raise RuntimeError(f"Governed requery did not answer credit-limit evidence: {answer_text[:240]}")
		if "35th street mobile wholesale" not in answer_lower:
			raise RuntimeError(f"Governed requery lost the selected customer context: {answer_text[:240]}")
		if "clarification needed" in answer_lower or "accounts_receivable_read" in answer_lower:
			raise RuntimeError(f"Governed requery exposed an internal or template fallback: {answer_text[:240]}")
		results["requery_mode"] = _text((payload or {}).get("mode"))
		results["requery_answer"] = answer_text[:240]

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show me top 10 suppliers by AP",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("AP supplier ranking request failed.")
		results["ap_supplier_mode"] = _text((payload or {}).get("mode"))

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="give me more information about rank 2 suppliers",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Supplier rank detail follow-up failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		supplier_detail_text = _text(_latest_assistant_payload(session_doc).get("text"))
		supplier_detail_lower = supplier_detail_text.lower()
		if "sunflower accessories" not in supplier_detail_lower:
			raise RuntimeError(f"Supplier detail follow-up did not use latest AP supplier table: {supplier_detail_text[:240]}")
		if "35th street mobile wholesale" in supplier_detail_lower:
			raise RuntimeError(f"Supplier detail follow-up reused stale AR customer focus: {supplier_detail_text[:240]}")
		if "supplier" not in supplier_detail_lower:
			raise RuntimeError(f"Supplier detail follow-up did not return supplier detail evidence: {supplier_detail_text[:240]}")
		results["supplier_detail_mode"] = _text((payload or {}).get("mode"))
		results["supplier_detail_answer"] = supplier_detail_text[:240]
		return {"ok": True, **results}
	finally:
		try:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
