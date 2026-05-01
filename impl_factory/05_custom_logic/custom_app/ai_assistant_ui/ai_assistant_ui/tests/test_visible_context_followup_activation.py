import json
import unittest

from ai_assistant_ui.qwen_chat.visible_context_followup_activation import (
	try_activate_visible_context_followup_response,
	visible_context_followup_requested,
)


def _assistant_message(text):
	return {"role": "assistant", "content": json.dumps({"type": "text", "text": text, "format": "markdown"})}


def _tool_message(payload):
	return {"role": "tool", "content": json.dumps(payload)}


def _ar_visible_text():
	return """Accounts Receivable Aging as of 2026-05-01

Summary
| Metric | Value (MMK) |
| --- | --- |
| Outstanding Total | 790,855,000 |

Top Customers
| Customer | Outstanding (MMK) | Total Due (MMK) | Overdue (31+) (MMK) |
| --- | --- | --- | --- |
| Capital Telecom (NPT) | 97,309,500 | 63,654,500 | 35,274,500 |
| 35th Street Mobile Wholesale | 84,837,000 | 82,527,000 | 58,212,000 |
| Bayint Naung Wholesale Mobile | 82,687,000 | 67,717,000 | 31,249,000 |
"""


def _ar_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"artifact_id": "ar-aging-1",
		"title": "Accounts Receivable Aging",
		"family_id": "accounts_receivable_aging",
		"sections": {
			"top_customers": [
				{
					"rank": 1,
					"customer": "Capital Telecom (NPT)",
					"outstanding_amount": 97309500,
					"total_due": 63654500,
					"overdue_amount": 35274500,
				},
				{
					"rank": 2,
					"customer": "35th Street Mobile Wholesale",
					"outstanding_amount": 84837000,
					"total_due": 82527000,
					"overdue_amount": 58212000,
				},
			]
		},
	}


def _supplier_list_text():
	return """7 Suppliers Found as of 2026-05-01

Supplier Names

Shan Yoma Electronics
Shwe Taung Electronics Supply
Mandalay Device Wholesale
Sunflower Accessories Co.
Myanmar Tech Import Services
"""


def _sales_invoice_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"artifact_id": "sales-invoices-1",
		"title": "Last 10 Sales Invoices",
		"family_id": "sales_invoice_read",
		"sections": {
			"documents": [
				{
					"rank": 1,
					"sales_invoice": "ACC-SINV-2026-00779",
					"posting_date": "2026-04-30",
					"customer": "City Mobile Mart",
					"grand_total": 4200000,
				},
				{
					"rank": 2,
					"sales_invoice": "ACC-SINV-2026-00205",
					"posting_date": "2026-04-30",
					"customer": "Capital Telecom (NPT)",
					"grand_total": 4375000,
				},
			]
		},
	}


def _balance_sheet_lines_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"artifact_id": "balance-sheet-lines-1",
		"title": "Balance Sheet",
		"family_id": "balance_sheet",
		"sections": {
			"rows": [
				{"rank": 1, "account": "Creditors", "amount": 906366600},
				{"rank": 2, "account": "Bank Overdraft Account", "amount": 118000000},
				{"rank": 3, "account": "Unsecured Loans", "amount": 98900000},
			]
		},
	}


def _stock_rows_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"artifact_id": "stock-rows-1",
		"title": "Stock by Warehouse",
		"family_id": "item_stock_by_warehouse",
		"sections": {
			"stock_rows": [
				{"rank": 1, "warehouse": "Mandalay Warehouse - MMOB", "qty": 53, "stock_value": 424000},
				{"rank": 2, "warehouse": "Yangon Showroom Counter - MMOB", "qty": 35, "stock_value": 280000},
			]
		},
	}


def _item_rows_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"artifact_id": "item-rows-1",
		"title": "Items by Stock",
		"family_id": "item_stock_summary",
		"sections": {
			"top_items": [
				{"rank": 1, "item_name": "Type-C Cable 2m Fast Charge", "qty": 88, "stock_value": 704000},
				{"rank": 2, "item_name": "Type-C Cable 1m Fast Charge", "qty": 587, "stock_value": 3228500},
			]
		},
	}


def _shadow_payload():
	return {
		"type": "qwen_natural_business_understanding_trace_contract",
		"request_id": "req-shadow",
		"conversation_action_decision": {"action": "ask_clarification"},
	}


class VisibleContextFollowupActivationTests(unittest.TestCase):
	def _activate(self, *, session_doc, raw_message, current_artifact=None, clear_callback=None):
		messages = []
		payloads = []

		def append_message(session_doc, role, text):
			messages.append((role, text))
			session_doc.setdefault("messages", []).append({"role": role, "content": text})

		def append_payload(session_doc, payload):
			payloads.append(payload)
			session_doc.setdefault("messages", []).append(_tool_message(payload))

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		handled, payload = try_activate_visible_context_followup_response(
			session_doc=session_doc,
			request_id="req-visible-context",
			session_id="session-1",
			user_id="user@example.com",
			site_name="erpai_prj1",
			raw_message=raw_message,
			current_artifact=current_artifact or {},
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=lambda text: text,
			save_session=save_session,
			clear_pending_clarification_signal=clear_callback,
			additional_tool_payloads=[_shadow_payload()],
		)
		return handled, payload, messages, payloads

	def test_fresh_business_query_is_not_intercepted(self):
		self.assertFalse(visible_context_followup_requested("show customer risk"))
		handled, payload, _messages, _payloads = self._activate(
			session_doc={"messages": []},
			raw_message="show customer risk",
		)
		self.assertFalse(handled)
		self.assertIsNone(payload)

	def test_answers_second_row_from_visible_markdown_without_route_clarification(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}
		handled, payload, messages, payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is in second position in the above table?",
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		self.assertTrue(any("Rank 2 is 35th Street Mobile Wholesale" in message[1] for message in messages))
		self.assertTrue(any("Overdue Amount: 58,212,000 MMK" in message[1] for message in messages))
		self.assertFalse(any("customer_risk_as_of" in message[1] for message in messages))
		self.assertTrue(any(row.get("type") == "qwen_visible_context_followup_trace_contract" for row in payloads))

	def test_clears_stale_pending_clarification_when_visible_row_is_answered(self):
		session_doc = {"messages": [_tool_message(_ar_artifact())]}
		cleared = {"value": False}

		def clear_pending(session_doc):
			cleared["value"] = True
			session_doc["pending_cleared"] = True

		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="explain rank 2",
			current_artifact=_ar_artifact(),
			clear_callback=clear_pending,
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		self.assertTrue(cleared["value"])
		self.assertTrue(any("35th Street Mobile Wholesale" in message[1] for message in messages))

	def test_ambiguous_deictic_question_asks_business_row_clarification(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="why is this customer risky?",
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_clarification")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("I need which row you mean", answer)
		self.assertIn("Rank 1: Capital Telecom (NPT)", answer)
		self.assertIn("Rank 2: 35th Street Mobile Wholesale", answer)
		self.assertNotIn("accounts_receivable_read", answer)

	def test_selected_row_focus_supports_later_this_customer_followup(self):
		session_doc = {"messages": [_tool_message(_ar_artifact())]}
		handled, _payload, _messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="explain rank 2",
			current_artifact=_ar_artifact(),
		)
		self.assertTrue(handled)
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="why is this customer risky?",
			current_artifact=_ar_artifact(),
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("35th Street Mobile Wholesale", answer)
		self.assertIn("rank 2", answer.lower())
		self.assertIn("Visible evidence from that row", answer)

	def test_prediction_question_returns_boundary_not_visible_fact_answer(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="will the first customer default next month?",
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_boundary")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("can't safely predict", answer)
		self.assertIn("Capital Telecom (NPT)", answer)
		self.assertIn("approved prediction model or policy", answer)
		self.assertNotIn("Rank 1 is Capital Telecom", answer)

	def test_recommendation_question_returns_policy_boundary_with_current_evidence(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who should we collect from first?",
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_boundary")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("can't choose who you should collect from first", answer)
		self.assertIn("Current visible evidence for Rank 1", answer)
		self.assertIn("Capital Telecom (NPT)", answer)
		self.assertIn("collection-priority policy", answer)

	def test_causal_question_returns_boundary_not_unsupported_cause_claim(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="what caused the first customer's risk to increase?",
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_boundary")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("can't prove what caused the change", answer)
		self.assertIn("trend, payment-behavior, or transaction-history", answer)

	def test_answers_second_supplier_from_plain_visible_name_list(self):
		session_doc = {"messages": [_assistant_message(_supplier_list_text())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is second in the above list?",
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is Shwe Taung Electronics Supply", answer)
		self.assertNotIn("supplier_master_read", answer)
		self.assertNotIn("Clarification Needed", answer)

	def test_sales_invoice_document_rows_use_generic_document_identity(self):
		session_doc = {"messages": [_tool_message(_sales_invoice_artifact())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is in second position in the above table?",
			current_artifact=_sales_invoice_artifact(),
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is ACC-SINV-2026-00205", answer)
		self.assertIn("Customer: Capital Telecom (NPT)", answer)
		self.assertIn("Grand Total: 4,375,000 MMK", answer)

	def test_financial_statement_account_rows_use_account_identity(self):
		session_doc = {"messages": [_tool_message(_balance_sheet_lines_artifact())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="explain rank 2 in liabilities",
			current_artifact=_balance_sheet_lines_artifact(),
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is Bank Overdraft Account", answer)
		self.assertIn("Amount: 118,000,000 MMK", answer)

	def test_stock_rows_use_warehouse_identity(self):
		session_doc = {"messages": [_tool_message(_stock_rows_artifact())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="what is in second warehouse?",
			current_artifact=_stock_rows_artifact(),
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is Yangon Showroom Counter - MMOB", answer)
		self.assertIn("Qty: 35", answer)
		self.assertIn("Stock Value: 280,000 MMK", answer)

	def test_item_action_recommendation_returns_generic_policy_boundary(self):
		session_doc = {"messages": [_tool_message(_item_rows_artifact())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="should we reorder the first item?",
			current_artifact=_item_rows_artifact(),
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_boundary")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("can't make an action recommendation", answer)
		self.assertIn("Type-C Cable 2m Fast Charge", answer)
		self.assertIn("relevant decision policy", answer)


if __name__ == "__main__":
	unittest.main()
