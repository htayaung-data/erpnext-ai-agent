from typing import Any, Dict


def _text(value: Any) -> str:
	return str(value or "").strip()


def _run_composite_clarification_scenario(
	*,
	session_title: str,
	initial_message: str,
	basis_reply: str,
	period_reply: str,
	expected_ranking_terms: tuple[str, ...],
) -> Dict[str, Any]:
	"""Prove composite clarification answers resume the pending request.

	This guards the natural flow:
	1. user asks for a governed composite ranking but omits basis
	2. user answers the basis with a short ERP term such as "Sales Invoice"
	3. user answers the period with a short business term such as "Last Month"

	Those short replies must resolve the pending clarification, not open a fresh
	transaction listing or select a stale visible row.
	"""

	import frappe

	from ai_assistant_ui.qwen_chat.service import (
		QWEN_SESSION_DOCTYPE,
		_latest_assistant_payload,
		handle_qwen_user_message,
	)

	doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
	doc.title = session_title
	doc.insert(ignore_permissions=False)
	frappe.db.commit()
	results: Dict[str, Any] = {"session": doc.name}
	try:
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=initial_message,
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Initial composite ranking request failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		basis_text = _text(_latest_assistant_payload(session_doc).get("text"))
		basis_lower = basis_text.lower()
		if "sales invoice" not in basis_lower or "sales order" not in basis_lower:
			raise RuntimeError(f"Basis clarification did not show approved options: {basis_text[:240]}")
		results["basis_clarification_mode"] = _text((payload or {}).get("mode"))
		results["basis_clarification_answer"] = basis_text[:240]

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=basis_reply,
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Basis clarification reply failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		period_text = _text(_latest_assistant_payload(session_doc).get("text"))
		period_lower = period_text.lower()
		if "last 10 sales invoices" in period_lower:
			raise RuntimeError(f"Basis reply opened a transaction listing instead of resuming the ranking: {period_text[:240]}")
		if "last month" not in period_lower:
			raise RuntimeError(f"Basis reply did not continue to period clarification: {period_text[:240]}")
		results["period_clarification_mode"] = _text((payload or {}).get("mode"))
		results["period_clarification_answer"] = period_text[:240]

		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message=period_reply,
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("Period clarification reply failed.")
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		ranking_text = _text(_latest_assistant_payload(session_doc).get("text"))
		ranking_lower = ranking_text.lower()
		if "rank 10 is" in ranking_lower or "current erp result already shown" in ranking_lower:
			raise RuntimeError(f"Period reply selected stale visible context instead of resuming the ranking: {ranking_text[:240]}")
		if any(term not in ranking_lower for term in expected_ranking_terms):
			raise RuntimeError(f"Period reply did not return the expected composite ranking: {ranking_text[:240]}")
		results["ranking_mode"] = _text((payload or {}).get("mode"))
		results["ranking_answer"] = ranking_text[:240]
		return {"ok": True, **results}
	finally:
		try:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()


def run_composite_clarification_continuation_smoke() -> Dict[str, Any]:
	return {
		"ok": True,
		"scenarios": {
			"customer_revenue": _run_composite_clarification_scenario(
				session_title="Composite Clarification Continuation Smoke - Customers",
				initial_message="Top 7 Customers by Revenue",
				basis_reply="Sales Invoice",
				period_reply="Last Month",
				expected_ranking_terms=("customer", "revenue"),
			),
			"product_revenue": _run_composite_clarification_scenario(
				session_title="Composite Clarification Continuation Smoke - Products",
				initial_message="Top 10 Products by Revenue",
				basis_reply="Sales Invoice",
				period_reply="Last Month",
				expected_ranking_terms=("product", "revenue"),
			),
		},
	}


def inspect_composite_clarification_continuation_state() -> Dict[str, Any]:
	"""Return diagnostics for the composite clarification continuation flow."""

	import json
	import frappe

	from ai_assistant_ui.qwen_chat.clarification_resolution import get_clarification_state
	from ai_assistant_ui.qwen_chat.clarification_resolution import clarification_resolved_continuation_message
	from ai_assistant_ui.qwen_chat.service import (
		QWEN_SESSION_DOCTYPE,
		_latest_assistant_payload,
		_resolved_clarification_runtime_message,
		handle_qwen_user_message,
	)
	from types import SimpleNamespace

	doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
	doc.title = "Composite Clarification Continuation Diagnostics"
	doc.insert(ignore_permissions=False)
	frappe.db.commit()
	results: Dict[str, Any] = {"session": doc.name}
	try:
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="Top 7 Customers by Revenue",
			user="Administrator",
		)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		state = get_clarification_state(session_doc)
		results["turn1_ok"] = ok
		results["turn1_mode"] = _text((payload or {}).get("mode"))
		results["turn1_answer"] = _text(_latest_assistant_payload(session_doc).get("text"))[:500]
		results["turn1_pending_signal"] = dict(state.pending_signal or {}) if state.has_pending else {}
		results["turn1_sales_invoice_continuation_message"] = clarification_resolved_continuation_message(
			signal_payload=dict(state.pending_signal or {}) if state.has_pending else {},
			resolved_option="Sales Invoice",
		)
		results["turn1_service_sales_invoice_runtime_message"] = _resolved_clarification_runtime_message(
			raw_message="Sales Invoice",
			pending_clarification_signal=dict(state.pending_signal or {}) if state.has_pending else {},
			clarification_response_contract=SimpleNamespace(decision="resolved_option", resolved_option="Sales Invoice"),
		)
		results["turn1_tool_signals"] = [
			json.loads(row.content)
			for row in list(getattr(session_doc, "messages", []) or [])
			if _text(getattr(row, "role", "")) == "tool"
			and _text(getattr(row, "content", "")).startswith("{")
			and _text(json.loads(row.content).get("type")) == "qwen_clarification_signal_contract"
		][-3:]
		ok, payload = handle_qwen_user_message(
			session_name=doc.name,
			message="Sales Invoice",
			user="Administrator",
		)
		session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, doc.name)
		state = get_clarification_state(session_doc)
		results["turn2_ok"] = ok
		results["turn2_mode"] = _text((payload or {}).get("mode"))
		results["turn2_answer"] = _text(_latest_assistant_payload(session_doc).get("text"))[:500]
		results["turn2_pending_signal"] = dict(state.pending_signal or {}) if state.has_pending else {}
		results["turn2_tool_payload_types"] = [
			_text(json.loads(row.content).get("type"))
			for row in list(getattr(session_doc, "messages", []) or [])[-20:]
			if _text(getattr(row, "role", "")) == "tool"
			and _text(getattr(row, "content", "")).startswith("{")
		]
		results["turn2_clarification_resolution"] = [
			json.loads(row.content)
			for row in list(getattr(session_doc, "messages", []) or [])
			if _text(getattr(row, "role", "")) == "tool"
			and _text(getattr(row, "content", "")).startswith("{")
			and _text(json.loads(row.content).get("type")) == "qwen_clarification_resolution_contract"
		][-3:]
		results["turn2_conversation_control"] = [
			json.loads(row.content)
			for row in list(getattr(session_doc, "messages", []) or [])
			if _text(getattr(row, "role", "")) == "tool"
			and _text(getattr(row, "content", "")).startswith("{")
			and _text(json.loads(row.content).get("type")) == "qwen_conversation_control_decision_contract"
		][-3:]
		results["turn2_compiled_request"] = [
			json.loads(row.content)
			for row in list(getattr(session_doc, "messages", []) or [])
			if _text(getattr(row, "role", "")) == "tool"
			and _text(getattr(row, "content", "")).startswith("{")
			and _text(json.loads(row.content).get("type")) == "qwen_compiled_query_request_contract"
		][-3:]
		results["turn2_frontdoor_contracts"] = [
			json.loads(row.content)
			for row in list(getattr(session_doc, "messages", []) or [])
			if _text(getattr(row, "role", "")) == "tool"
			and _text(getattr(row, "content", "")).startswith("{")
			and _text(json.loads(row.content).get("type")) == "qwen_front_door_intent_gate_contract"
		][-3:]
		return {"ok": True, **results}
	finally:
		try:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
