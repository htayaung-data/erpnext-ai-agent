from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
	return str(value or "").strip()


def _assert_no_route_clarification(answer_text: str, *, context: str) -> None:
	answer_lower = answer_text.lower()
	if "clarification needed" in answer_lower:
		raise RuntimeError(f"{context} returned a user-facing route clarification: {answer_text[:240]}")
	for leaked_token in (
		"accounts_receivable_read",
		"customer_risk_as_of",
		"supplier_master_read",
		"sales_invoice_read",
	):
		if leaked_token in answer_lower:
			raise RuntimeError(f"{context} leaked internal route option {leaked_token}: {answer_text[:240]}")


def run_visible_context_followup_smoke() -> Dict[str, Any]:
	"""Run a controlled live-session smoke for visible row/rank follow-ups.

	This intentionally creates and deletes its own temporary Qwen session. It does
	not inspect real user conversations.
	"""

	import frappe

	from ai_assistant_ui.qwen_chat.service import (
		QWEN_SESSION_DOCTYPE,
		_latest_assistant_payload,
		get_clarification_state,
		handle_qwen_user_message,
	)

	doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
	doc.title = "Visible Context Followup Smoke"
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
			raise RuntimeError("Second-position visible follow-up failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		second_text = _text(_latest_assistant_payload(session_doc).get("text"))
		second_lower = second_text.lower()
		if "rank 2" not in second_lower or "35th street mobile wholesale" not in second_lower:
			raise RuntimeError(f"Second-position visible follow-up returned unexpected answer: {second_text[:240]}")
		_assert_no_route_clarification(second_text, context="Customer-risk second-position visible follow-up")
		if get_clarification_state(session_doc).has_pending:
			raise RuntimeError("Visible follow-up left a pending clarification signal.")
		results["second_position_mode"] = _text((payload or {}).get("mode"))
		results["second_position_answer"] = second_text[:240]

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="why is this customer risky?",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Selected-customer visible follow-up failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		risk_text = _text(_latest_assistant_payload(session_doc).get("text"))
		risk_lower = risk_text.lower()
		if "35th street mobile wholesale" not in risk_lower:
			raise RuntimeError(f"Selected-customer follow-up did not keep the selected row focus: {risk_text[:240]}")
		if "rank 2" not in risk_lower:
			raise RuntimeError(f"Selected-customer follow-up did not preserve the selected rank: {risk_text[:240]}")
		results["selected_customer_mode"] = _text((payload or {}).get("mode"))
		results["selected_customer_answer"] = risk_text[:240]

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="will the first customer default next month?",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Prediction-boundary visible follow-up failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		prediction_text = _text(_latest_assistant_payload(session_doc).get("text"))
		prediction_lower = prediction_text.lower()
		if "can't safely predict" not in prediction_lower:
			raise RuntimeError(f"Prediction follow-up did not return a safe boundary: {prediction_text[:240]}")
		if "capital telecom" not in prediction_lower:
			raise RuntimeError(f"Prediction boundary did not retain visible row evidence: {prediction_text[:240]}")
		results["prediction_boundary_mode"] = _text((payload or {}).get("mode"))
		results["prediction_boundary_answer"] = prediction_text[:240]

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="who should we collect from first?",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Recommendation-boundary visible follow-up failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		recommendation_text = _text(_latest_assistant_payload(session_doc).get("text"))
		recommendation_lower = recommendation_text.lower()
		if "can't choose who you should collect from first" not in recommendation_lower:
			raise RuntimeError(f"Recommendation follow-up did not return a safe boundary: {recommendation_text[:240]}")
		if "collection-priority policy" not in recommendation_lower:
			raise RuntimeError(f"Recommendation boundary did not explain the policy requirement: {recommendation_text[:240]}")
		results["recommendation_boundary_mode"] = _text((payload or {}).get("mode"))
		results["recommendation_boundary_answer"] = recommendation_text[:240]

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show me suppliers",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Same-session supplier fresh-query breakout failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		same_session_supplier_text = _text(_latest_assistant_payload(session_doc).get("text"))
		same_session_supplier_lower = same_session_supplier_text.lower()
		if "suppliers found" not in same_session_supplier_lower or "shwe taung electronics supply" not in same_session_supplier_lower:
			raise RuntimeError(f"Same-session supplier request did not replace old AR context: {same_session_supplier_text[:240]}")
		_assert_no_route_clarification(same_session_supplier_text, context="Same-session supplier fresh-query breakout")
		if get_clarification_state(session_doc).has_pending:
			raise RuntimeError("Same-session supplier fresh-query breakout left a pending clarification signal.")
		results["same_session_supplier_mode"] = _text((payload or {}).get("mode"))
		results["same_session_supplier_answer"] = same_session_supplier_text[:240]

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="who is second in the above list?",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Same-session supplier visible-list follow-up failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		same_session_supplier_second_text = _text(_latest_assistant_payload(session_doc).get("text"))
		if "rank 2" not in same_session_supplier_second_text.lower() or "shwe taung electronics supply" not in same_session_supplier_second_text.lower():
			raise RuntimeError(
				f"Same-session supplier follow-up did not use latest supplier list: {same_session_supplier_second_text[:240]}"
			)
		_assert_no_route_clarification(
			same_session_supplier_second_text,
			context="Same-session supplier second-position follow-up",
		)
		results["same_session_supplier_second_mode"] = _text((payload or {}).get("mode"))
		results["same_session_supplier_second_answer"] = same_session_supplier_second_text[:240]

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show me sale invoices",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Same-session sales-invoice fresh-query breakout failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		same_session_invoice_text = _text(_latest_assistant_payload(session_doc).get("text"))
		same_session_invoice_lower = same_session_invoice_text.lower()
		if "sales invoices" not in same_session_invoice_lower or "acc-sinv" not in same_session_invoice_lower:
			raise RuntimeError(f"Same-session sales-invoice request did not replace prior context: {same_session_invoice_text[:240]}")
		if "nearest erp options" in same_session_invoice_lower:
			raise RuntimeError(f"Same-session sales-invoice request fell into stale recovery: {same_session_invoice_text[:240]}")
		_assert_no_route_clarification(same_session_invoice_text, context="Same-session sales-invoice fresh-query breakout")
		results["same_session_invoice_mode"] = _text((payload or {}).get("mode"))
		results["same_session_invoice_answer"] = same_session_invoice_text[:240]

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="who is in second position in the above table?",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Same-session sales-invoice visible-table follow-up failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		same_session_invoice_second_text = _text(_latest_assistant_payload(session_doc).get("text"))
		if "rank 2" not in same_session_invoice_second_text.lower() or "acc-sinv" not in same_session_invoice_second_text.lower():
			raise RuntimeError(
				f"Same-session invoice follow-up did not use latest invoice table: {same_session_invoice_second_text[:240]}"
			)
		_assert_no_route_clarification(
			same_session_invoice_second_text,
			context="Same-session invoice second-position follow-up",
		)
		results["same_session_invoice_second_mode"] = _text((payload or {}).get("mode"))
		results["same_session_invoice_second_answer"] = same_session_invoice_second_text[:240]

		supplier_doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		supplier_doc.title = "Visible Context Supplier Smoke"
		supplier_doc.insert(ignore_permissions=False)
		frappe.db.commit()
		results["supplier_session"] = supplier_doc.name
		try:
			ok, _payload = handle_qwen_user_message(
				session_name=supplier_doc.name,
				message="show me suppliers",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Initial supplier-list request failed.")
			ok, payload = handle_qwen_user_message(
				session_name=supplier_doc.name,
				message="who is second in the above list?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Supplier-list visible follow-up failed.")
			supplier_session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, supplier_doc.name)
			supplier_answer = _text(_latest_assistant_payload(supplier_session_doc).get("text"))
			if "rank 2" not in supplier_answer.lower() or "shwe taung electronics supply" not in supplier_answer.lower():
				raise RuntimeError(f"Supplier-list visible follow-up returned unexpected answer: {supplier_answer[:240]}")
			_assert_no_route_clarification(supplier_answer, context="Supplier-list visible follow-up")
			results["supplier_second_position_mode"] = _text((payload or {}).get("mode"))
			results["supplier_second_position_answer"] = supplier_answer[:240]
		finally:
			try:
				frappe.delete_doc(QWEN_SESSION_DOCTYPE, supplier_doc.name, ignore_permissions=False)
				frappe.db.commit()
			except Exception:
				frappe.db.rollback()

		invoice_doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
		invoice_doc.title = "Visible Context Invoice Smoke"
		invoice_doc.insert(ignore_permissions=False)
		frappe.db.commit()
		results["invoice_session"] = invoice_doc.name
		try:
			ok, _payload = handle_qwen_user_message(
				session_name=invoice_doc.name,
				message="show me sale invoices",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Initial sales-invoice request failed.")
			ok, payload = handle_qwen_user_message(
				session_name=invoice_doc.name,
				message="who is in second position in the above table?",
				user="Administrator",
			)
			if not ok:
				raise RuntimeError("Sales-invoice visible follow-up failed.")
			invoice_session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, invoice_doc.name)
			invoice_answer = _text(_latest_assistant_payload(invoice_session_doc).get("text"))
			if "rank 2" not in invoice_answer.lower() or "acc-sinv" not in invoice_answer.lower():
				raise RuntimeError(f"Sales-invoice visible follow-up returned unexpected answer: {invoice_answer[:240]}")
			_assert_no_route_clarification(invoice_answer, context="Sales-invoice visible follow-up")
			results["invoice_second_position_mode"] = _text((payload or {}).get("mode"))
			results["invoice_second_position_answer"] = invoice_answer[:240]
		finally:
			try:
				frappe.delete_doc(QWEN_SESSION_DOCTYPE, invoice_doc.name, ignore_permissions=False)
				frappe.db.commit()
			except Exception:
				frappe.db.rollback()
		return {"ok": True, **results}
	finally:
		try:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
