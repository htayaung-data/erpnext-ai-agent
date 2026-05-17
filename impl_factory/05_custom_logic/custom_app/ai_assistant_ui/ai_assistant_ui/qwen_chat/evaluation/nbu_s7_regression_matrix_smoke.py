from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
	return str(value or "").strip()


def _lower(value: Any) -> str:
	return _text(value).lower()


def _assert_no_internal_language(answer_text: str, *, context: str) -> None:
	lower = _lower(answer_text)
	internal_markers = {
		"qwen_",
		"runtime",
		"contract",
		"artifact",
		"governed boundary",
		"governed evidence",
		"governed support",
		"accounts_receivable_read",
		"customer_risk_as_of",
		"supplier_master_read",
		"compiled_first_turn",
		"erp_business_reasoning",
	}
	leaked = sorted(marker for marker in internal_markers if marker in lower)
	if leaked:
		raise RuntimeError(
			f"NBU-S7 {context} leaked internal language {leaked!r}: {answer_text[:320]}"
		)


def _new_session(*, title: str):
	import frappe

	from ai_assistant_ui.qwen_chat.service import QWEN_SESSION_DOCTYPE

	doc = frappe.new_doc(QWEN_SESSION_DOCTYPE)
	doc.title = title
	doc.insert(ignore_permissions=False)
	frappe.db.commit()
	return doc


def _latest_answer_text(session_name: str) -> str:
	import frappe

	from ai_assistant_ui.qwen_chat.service import QWEN_SESSION_DOCTYPE, _latest_assistant_payload

	session_doc = frappe.get_doc(QWEN_SESSION_DOCTYPE, session_name)
	return _text(_latest_assistant_payload(session_doc).get("text"))


def run_nbu_s7_same_session_fresh_query_smoke() -> Dict[str, Any]:
	"""Verify self-contained questions reset stale context in one conversation.

	This smoke intentionally asserts business-visible behavior instead of an
	internal route name. The user contract is that a new complete ERP question
	is answered as a fresh governed request, even when older AR, supplier, or
	document context exists in the same chat.
	"""

	import frappe

	from ai_assistant_ui.qwen_chat.service import QWEN_SESSION_DOCTYPE, handle_qwen_user_message

	doc = _new_session(title="NBU-S7 Same Session Fresh Query")
	turns = [
		{
			"message": "show customer risk",
			"must_include": ["Accounts Receivable Aging", "Top Customers"],
			"must_not_include": ["Supplier Names", "Last 10 Sales Invoices"],
		},
		{
			"message": "show me suppliers",
			"must_include": ["Suppliers Found", "Shwe Taung Electronics Supply"],
			"must_not_include": ["Accounts Receivable Aging", "Last 10 Sales Invoices"],
		},
		{
			"message": "show me sale invoices",
			"must_include": ["Last 10 Sales Invoices", "ACC-SINV-2026-00205"],
			"must_not_include": ["Supplier Names", "Accounts Receivable Aging"],
		},
		{
			"message": "Top 7 Customers by Revenue Last Month",
			"must_include": ["top 7 customers", "revenue", "Capital Telecom (NPT)"],
			"must_not_include": ["ACC-SINV-2026-00205", "Supplier Names", "Accounts Receivable Aging"],
		},
	]
	results = []
	try:
		for turn in turns:
			message = str(turn["message"])
			ok, payload = handle_qwen_user_message(
				session_name=doc.name,
				message=message,
				user="Administrator",
			)
			if not ok:
				raise RuntimeError(f"NBU-S7 fresh-query reset failed on `{message}`.")
			answer_text = _latest_answer_text(doc.name)
			answer_lower = answer_text.lower()
			missing = [
				expected
				for expected in turn["must_include"]
				if str(expected).lower() not in answer_lower
			]
			if missing:
				raise RuntimeError(
					f"NBU-S7 fresh-query reset missing {missing!r} for `{message}`: {answer_text[:320]}"
				)
			stale_hits = [
				stale
				for stale in turn["must_not_include"]
				if str(stale).lower() in answer_lower
			]
			if stale_hits:
				raise RuntimeError(
					f"NBU-S7 fresh-query reset leaked stale context {stale_hits!r} for `{message}`: {answer_text[:320]}"
				)
			_assert_no_internal_language(answer_text, context=f"fresh query `{message}`")
			results.append(
				{
					"message": message,
					"mode": _text((payload or {}).get("mode")),
					"answer": answer_text[:240],
				}
			)
		return {
			"ok": True,
			"session": doc.name,
			"results": results,
		}
	finally:
		try:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()


def run_nbu_s7_visible_context_latest_artifact_smoke() -> Dict[str, Any]:
	"""Verify generic rank/list follow-ups bind to the latest visible artifact.

	This protects the broad NBU behavior the user sees in the browser: after a
	supplier list, "who is second" must use that supplier list; after sales
	invoices, the same wording must switch to the latest invoice table.
	"""

	import frappe

	from ai_assistant_ui.qwen_chat.service import QWEN_SESSION_DOCTYPE, handle_qwen_user_message

	doc = _new_session(title="NBU-S7 Visible Context Latest Artifact")
	results: Dict[str, Any] = {"session": doc.name}
	try:
		ok, supplier_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show me suppliers",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("NBU-S7 visible context failed on supplier list request.")
		supplier_list_text = _latest_answer_text(doc.name)
		if "Shwe Taung Electronics Supply" not in supplier_list_text:
			raise RuntimeError(f"NBU-S7 supplier list did not include expected supplier: {supplier_list_text[:240]}")

		ok, supplier_rank_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="who is second in the above list?",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("NBU-S7 visible context failed on supplier rank follow-up.")
		supplier_rank_text = _latest_answer_text(doc.name)
		if "Shwe Taung Electronics Supply" not in supplier_rank_text:
			raise RuntimeError(f"NBU-S7 supplier rank follow-up did not use supplier list: {supplier_rank_text[:240]}")
		if "35th Street Mobile Wholesale" in supplier_rank_text:
			raise RuntimeError(f"NBU-S7 supplier rank follow-up reused stale customer context: {supplier_rank_text[:240]}")
		_assert_no_internal_language(supplier_rank_text, context="supplier rank follow-up")

		ok, invoice_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show me sale invoices",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("NBU-S7 visible context failed on sales invoice table request.")
		invoice_text = _latest_answer_text(doc.name)
		if "ACC-SINV-2026-00205" not in invoice_text:
			raise RuntimeError(f"NBU-S7 sales invoice table did not include expected invoice: {invoice_text[:240]}")

		ok, invoice_rank_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="who is in second position in the above table?",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("NBU-S7 visible context failed on invoice rank follow-up.")
		invoice_rank_text = _latest_answer_text(doc.name)
		if "ACC-SINV-2026-00205" not in invoice_rank_text:
			raise RuntimeError(f"NBU-S7 invoice rank follow-up did not use latest invoice table: {invoice_rank_text[:240]}")
		if "Shwe Taung Electronics Supply" in invoice_rank_text:
			raise RuntimeError(f"NBU-S7 invoice rank follow-up reused stale supplier context: {invoice_rank_text[:240]}")
		_assert_no_internal_language(invoice_rank_text, context="invoice rank follow-up")

		return {
			"ok": True,
			"session": doc.name,
			"supplier_list_mode": _text((supplier_payload or {}).get("mode")),
			"supplier_rank_mode": _text((supplier_rank_payload or {}).get("mode")),
			"invoice_table_mode": _text((invoice_payload or {}).get("mode")),
			"invoice_rank_mode": _text((invoice_rank_payload or {}).get("mode")),
			"supplier_rank_answer": supplier_rank_text[:240],
			"invoice_rank_answer": invoice_rank_text[:240],
		}
	finally:
		try:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()


def run_nbu_s7_safe_boundary_language_smoke() -> Dict[str, Any]:
	"""Verify unsupported decision/prediction asks fail politely without internals."""

	import frappe

	from ai_assistant_ui.qwen_chat.service import QWEN_SESSION_DOCTYPE, handle_qwen_user_message

	doc = _new_session(title="NBU-S7 Safe Boundary Language")
	results: Dict[str, Any] = {"session": doc.name}
	try:
		ok, initial_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="show customer risk",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("NBU-S7 safe boundary failed on customer risk setup.")

		ok, prediction_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="will the first customer default next month?",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("NBU-S7 safe boundary failed on prediction turn.")
		prediction_text = _latest_answer_text(doc.name)
		prediction_lower = prediction_text.lower()
		if not any(marker in prediction_lower for marker in ("can't", "cannot", "need", "prediction", "predict")):
			raise RuntimeError(f"NBU-S7 prediction boundary sounded too definitive: {prediction_text[:320]}")
		if "will default" in prediction_lower and "can't" not in prediction_lower and "cannot" not in prediction_lower:
			raise RuntimeError(f"NBU-S7 prediction boundary appeared to make an unsafe prediction: {prediction_text[:320]}")
		_assert_no_internal_language(prediction_text, context="prediction boundary")

		ok, recommendation_payload = handle_qwen_user_message(
			session_name=doc.name,
			message="who should we collect from first?",
			user="Administrator",
		)
		if not ok:
			raise RuntimeError("NBU-S7 safe boundary failed on collection recommendation turn.")
		recommendation_text = _latest_answer_text(doc.name)
		recommendation_lower = recommendation_text.lower()
		if not any(marker in recommendation_lower for marker in ("can't", "cannot", "business rule", "policy", "evidence")):
			raise RuntimeError(f"NBU-S7 collection boundary did not explain the decision limit: {recommendation_text[:320]}")
		_assert_no_internal_language(recommendation_text, context="collection recommendation boundary")

		return {
			"ok": True,
			"session": doc.name,
			"initial_mode": _text((initial_payload or {}).get("mode")),
			"prediction_mode": _text((prediction_payload or {}).get("mode")),
			"recommendation_mode": _text((recommendation_payload or {}).get("mode")),
			"prediction_answer": prediction_text[:240],
			"recommendation_answer": recommendation_text[:240],
		}
	finally:
		try:
			frappe.delete_doc(QWEN_SESSION_DOCTYPE, doc.name, ignore_permissions=False)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
