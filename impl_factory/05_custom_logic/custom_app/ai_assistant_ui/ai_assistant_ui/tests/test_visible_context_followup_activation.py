import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.visible_context_followup_activation import (
	try_activate_visible_context_followup_response,
	visible_context_followup_requested,
)
from ai_assistant_ui.qwen_chat.natural_business_understanding_request_classification import (
	artifact_level_visible_context_requested,
	visible_context_target_reference,
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


def _ar_comparison_text():
	return """Here is the comparison from Accounts Receivable Summary.

Comparison table

| Party | Outstanding | Overdue | Overdue intensity |
| --- | ---: | ---: | ---: |
| 35th Street Mobile Wholesale | 84.8 MMK Million | 58.2 MMK Million | 68.6% |
| Ko Nay Lin Mobile Center | 63.1 MMK Million | 37.3 MMK Million | 59.1% |
| Taunggyi City Mobile | 37 MMK Million | 37 MMK Million | 100% |
"""


def _customer_revenue_ranking_text():
	return """Top 7 Customers by Revenue Last Year

| Rank | Customer | Revenue (MMK) |
| ---: | --- | ---: |
| 1 | Capital Telecom (NPT) | 182,486,500 |
| 2 | Bayint Naung Wholesale Mobile | 177,612,500 |
| 3 | 35th Street Mobile Wholesale | 146,669,000 |
"""


def _product_million_ranking_text():
	return """Top 7 Products by Revenue (2025-04-01 to 2026-03-31)

Top Ranked Rows

| Rank | Product | Revenue (MMK Million) |
| ---: | --- | ---: |
| 1 | Samsung Galaxy A15 (6GB 128GB) | 341.21 |
| 2 | Xiaomi Redmi Note 13 (8GB 256GB) | 281.77 |
| 3 | Power Bank 20000mAh | 174.19 |
"""


def _product_plain_ranking_text():
	return """For 2025-04-01 to 2026-03-31, here are the top 7 products by revenue based on sales invoices.

| Rank | Product | Revenue (MMK) |
| --- | --- | --- |
| 1 | Samsung Galaxy A15 (6GB 128GB) | 341,209,000 |
| 2 | Xiaomi Redmi Note 13 (8GB 256GB) | 281,770,000 |
| 3 | Power Bank 20000mAh | 174,195,000 |
"""


def _invoice_breakdown_answer_text():
	return """Ko Nay Lin Mobile Center is the rank 2 entry in the table above.

Deeper approved ERP detail:

Breakdown by invoice

| Invoice | Posting Date | Due Date | Status | Invoice Total | Outstanding amount | Share of selected balance |
| --- | --- | --- | --- | --- | ---: | ---: |
| ACC-SINV-2026-00699 | 2026-03-13 | 2026-04-12 | Overdue | 24,500,000 | 21.5 MMK Million | 49.9% |
| ACC-SINV-2026-00689 | 2026-02-19 | 2026-03-21 | Overdue | 12,340,000 | 7.3 MMK Million | 17% |
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


def _ar_artifact_with_source_detail_filters():
	artifact = _ar_artifact()
	artifact["filters"] = {
		"company": "Mingalar Mobile Distribution Co., Ltd.",
		"as_of_date": "2026-05-08",
	}
	artifact["period"] = {"as_of_date": "2026-05-08"}
	artifact["source_reports"] = ["Accounts Receivable Aging"]
	return artifact


def _sales_invoice_detail_payload():
	return {
		"ok": True,
		"tool_trace": [
			{
				"output_obj": {
					"result": {
						"data": [
							{
								"name": "SINV-2026-00042",
								"posting_date": "2026-05-01",
								"due_date": "2026-05-31",
								"customer": "35th Street Mobile Wholesale",
								"grand_total": "84,837,000",
								"outstanding_amount": "58,212,000",
								"status": "Overdue",
							}
						]
					}
				}
			}
		],
	}


def _raw_summary_table_payload():
	return {
		"data": [
			["Outstanding Total", "790,855,000 MMK"],
			["Total Amount Due", "724,170,000 MMK"],
		],
	}


def _ar_unsorted_parties_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"artifact_id": "ar-aging-parties-1",
		"title": "Accounts Receivable Aging",
		"family_id": "accounts_receivable_aging",
		"sections": {
			"parties": [
				{"party": "Capital Telecom (NPT)", "party_type": "Customer", "outstanding": 97309500},
				{"party": "Aung Aung Telecom", "party_type": "Customer", "outstanding": 24260000},
				{"party": "35th Street Mobile Wholesale", "party_type": "Customer", "outstanding": 84837000},
			]
		},
	}


def _ap_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"artifact_id": "ap-aging-1",
		"title": "Accounts Payable Aging",
		"family_id": "accounts_payable_aging",
		"sections": {
			"top_suppliers": [
				{
					"rank": 1,
					"supplier": "Myanmar Tech Import Services",
					"outstanding_amount": 268298000,
					"total_due": 250568000,
					"overdue_amount": 193478000,
				},
				{
					"rank": 2,
					"supplier": "Sunflower Accessories Co.",
					"outstanding_amount": 222526500,
					"total_due": 222526500,
					"overdue_amount": 136661500,
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


def _sales_invoice_detail_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"artifact_id": "sales-invoice-detail-1",
		"request_id": "sales-invoice-detail-1",
		"title": "ACC-SINV-2026-00194 Detail",
		"family_id": "entity_detail",
		"dimensions": {
			"entity_type": "sales_invoice",
			"entity_label": "ACC-SINV-2026-00194",
			"entity_key": "ACC-SINV-2026-00194",
		},
		"sections": {
			"document_row": {
				"sales_invoice": "ACC-SINV-2026-00194",
				"customer": "Zegyo Mobile Supply House",
			},
			"delivery_proof": [
				{
					"proof_state": "direct_delivery_proven_via_linked_delivery_note",
					"submitted_delivery_notes": ["MAT-DN-2026-00011"],
					"submitted_delivery_dates": ["2026-03-30"],
				}
			],
		},
	}


def _customer_detail_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"artifact_id": "customer-detail-1",
		"request_id": "customer-detail-1",
		"title": "Zegyo Mobile Supply House Details",
		"family_id": "entity_detail",
		"dimensions": {
			"entity_type": "customer",
			"entity_label": "Zegyo Mobile Supply House",
			"entity_key": "Zegyo Mobile Supply House",
		},
		"sections": {
			"profile": [
				{"label": "Name", "value": "Zegyo Mobile Supply House"},
				{"label": "Code", "value": "Zegyo Mobile Supply House"},
				{"label": "Group", "value": "Wholesale"},
			],
			"lifecycle": [
				{"label": "Customer Created Date", "value": "2026-03-30"},
				{"label": "Tenure from Customer Created (2026-05-03)", "value": "34 days"},
				{"label": "First Sales Order Date", "value": "2026-03-30"},
				{"label": "Tenure from First Sales Order (2026-05-03)", "value": "34 days"},
			],
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


def _shadow_payload(
	*,
	authority_class="",
	requested_action="",
	governed_requery_plan=None,
	target_reference="",
	candidate_composite_family_ids=None,
):
	candidates = []
	if requested_action:
		candidate = {"candidate_id": "candidate-1", "requested_action": requested_action}
		if target_reference:
			candidate["target_reference"] = target_reference
		if candidate_composite_family_ids is not None:
			candidate["candidate_composite_family_ids"] = list(candidate_composite_family_ids)
		candidates.append(candidate)
	return {
		"type": "qwen_natural_business_understanding_trace_contract",
		"request_id": "req-shadow",
		"selected_candidate_id": "candidate-1" if candidates else "",
		"candidate_interpretations": candidates,
		"authority_plan": {"authority_class": authority_class} if authority_class else {},
		"conversation_action_decision": {"action": "ask_clarification"},
		"governed_requery_plan": governed_requery_plan or {},
	}


def _reasoning_result(reasoning_type=""):
	if not reasoning_type:
		return None
	return SimpleNamespace(
		status="accepted",
		intent=SimpleNamespace(reasoning_type=reasoning_type),
	)


class VisibleContextFollowupActivationTests(unittest.TestCase):
	def _activate(
		self,
		*,
		session_doc,
		raw_message,
		current_artifact=None,
		clear_callback=None,
		authority_class="",
		requested_action="",
		reasoning_type="",
		governed_requery_plan=None,
		target_reference="",
		candidate_composite_family_ids=None,
	):
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
			reasoning_semantic_result=_reasoning_result(reasoning_type),
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=lambda text: text,
			save_session=save_session,
			clear_pending_clarification_signal=clear_callback,
			additional_tool_payloads=[
				_shadow_payload(
					authority_class=authority_class,
					requested_action=requested_action,
					governed_requery_plan=governed_requery_plan,
					target_reference=target_reference,
					candidate_composite_family_ids=candidate_composite_family_ids,
				)
			],
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

	def test_fresh_temporal_ranking_query_is_not_treated_as_last_visible_row(self):
		self.assertFalse(visible_context_followup_requested("Top 10 Products by Revenue Last Month"))
		handled, payload, messages, _payloads = self._activate(
			session_doc={"messages": [_assistant_message(_ar_visible_text())]},
			raw_message="Top 10 Products by Revenue Last Month",
		)
		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertFalse(any("Rank 2 is" in message[1] or "last visible row" in message[1] for message in messages))

	def test_ranked_entity_detail_request_is_visible_context_not_fresh_query(self):
		self.assertTrue(visible_context_followup_requested("give me more information about rank 2 suppliers"))

	def test_ranked_row_identity_does_not_defer_to_local_followup_shadow_plan(self):
		session_doc = {"messages": [_tool_message(_ap_artifact())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is second in the above table?",
			current_artifact=_ap_artifact(),
			requested_action="show",
			governed_requery_plan={
				"status": "ready_shadow",
				"planner_mode": "entity_detail_requery",
				"target_route": "local_followup",
				"shadow_execution_ready": True,
				"target_entity": {
					"entity_type": "supplier",
					"name": "Sunflower Accessories Co.",
				},
			},
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is Sunflower Accessories Co.", answer)

	def test_ranked_entity_detail_request_defers_to_governed_detail_lane(self):
		session_doc = {"messages": [_tool_message(_ap_artifact())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="give me more information about rank 2 suppliers",
			current_artifact=_ap_artifact(),
			requested_action="detail",
			governed_requery_plan={
				"status": "ready_shadow",
				"planner_mode": "entity_detail_requery",
				"target_route": "entity_detail",
				"shadow_execution_ready": True,
				"target_entity": {
					"entity_type": "supplier",
					"name": "Sunflower Accessories Co.",
				},
			},
		)
		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertEqual(messages, [])

	def test_presentation_only_million_request_is_not_visible_row_followup(self):
		self.assertFalse(visible_context_followup_requested("Show in Million"))
		self.assertFalse(visible_context_followup_requested("Show as Million"))

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

	def test_safe_read_row_identity_does_not_expand_into_reasoning_style_explanation(self):
		session_doc = {"messages": [_tool_message(_ap_artifact())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is second in the above table?",
			current_artifact=_ap_artifact(),
			authority_class="safe_read",
			requested_action="show",
			reasoning_type="interpretation",
			governed_requery_plan={
				"status": "ready_shadow",
				"planner_mode": "entity_detail_requery",
				"target_route": "local_followup",
				"shadow_execution_ready": True,
				"target_entity": {
					"entity_type": "supplier",
					"name": "Sunflower Accessories Co.",
				},
			},
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is Sunflower Accessories Co.", answer)
		self.assertNotIn("Why this stands out", answer)

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

	def test_typed_artifact_wins_over_newer_raw_summary_rows_for_rank_reference(self):
		session_doc = {"messages": [_tool_message(_ar_artifact()), _tool_message(_raw_summary_table_payload())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is in second position in the above table?",
			current_artifact={},
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is 35th Street Mobile Wholesale", answer)
		self.assertNotIn("Total Amount Due", answer)

	def test_visible_ranked_table_wins_over_generic_unsorted_party_rows(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text()), _tool_message(_ar_unsorted_parties_artifact())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is in second position in the above table?",
			current_artifact={},
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is 35th Street Mobile Wholesale", answer)
		self.assertNotIn("Aung Aung Telecom", answer)

	def test_latest_assistant_comparison_table_has_context_authority_over_prior_report(self):
		session_doc = {"messages": [_tool_message(_ar_artifact()), _assistant_message(_ar_comparison_text())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is second in the above table?",
			current_artifact=_ar_artifact(),
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is Ko Nay Lin Mobile Center", answer)
		self.assertNotIn("Bayint Naung Wholesale Mobile", answer)

	def test_selected_comparison_row_with_million_values_gets_consultant_risk_signal(self):
		session_doc = {"messages": [_tool_message(_ar_artifact()), _assistant_message(_ar_comparison_text())]}
		handled, _payload, _messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is second in the above table?",
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
		self.assertIn("Ko Nay Lin Mobile Center", answer)
		self.assertIn("Why this stands out from the visible row", answer)
		self.assertIn("37.3 MMK Million is overdue", answer)
		self.assertIn("59.1% of the outstanding balance", answer)
		self.assertIn("Consultant takeaway", answer)

	def test_latest_top_ranked_rows_table_has_context_authority_over_stale_supplier_selection(self):
		stale_supplier_selection = {
			"type": "qwen_nbu_current_artifact_answer_activation_contract",
			"activation_mode": "visible_context_answer",
			"resolved_rank": 2,
			"resolved_entity": {
				"entity_type": "supplier",
				"entity_label": "Sunflower Accessories Co.",
				"entity_key": "Sunflower Accessories Co.",
				"row": {
					"rank": 2,
					"supplier": "Sunflower Accessories Co.",
					"outstanding_amount": 228576500,
				},
			},
		}
		session_doc = {
			"messages": [
				_tool_message(_ap_artifact()),
				_tool_message(stale_supplier_selection),
				_assistant_message(_product_million_ranking_text()),
			]
		}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is second in the above table?",
			current_artifact=_ap_artifact(),
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is Xiaomi Redmi Note 13", answer)
		self.assertNotIn("Sunflower Accessories Co.", answer)

	def test_latest_plain_product_table_has_context_authority_over_prior_comparison_table(self):
		session_doc = {
			"messages": [
				_assistant_message(_ar_comparison_text()),
				_assistant_message(_product_plain_ranking_text()),
			]
		}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is second in the above table?",
			current_artifact=_ar_artifact(),
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is Xiaomi Redmi Note 13", answer)
		self.assertNotIn("Ko Nay Lin Mobile Center", answer)

	def test_latest_plain_product_table_wins_over_prior_invoice_breakdown_answer(self):
		session_doc = {
			"messages": [
				_assistant_message(_ar_comparison_text()),
				_assistant_message(_invoice_breakdown_answer_text()),
				_assistant_message(_product_plain_ranking_text()),
			]
		}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is second in the above table?",
			current_artifact=_ar_artifact(),
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is Xiaomi Redmi Note 13", answer)
		self.assertNotIn("ACC-SINV-2026-00689", answer)
		self.assertNotIn("Ko Nay Lin Mobile Center", answer)

	def test_artifact_set_field_question_does_not_use_stale_selected_entity(self):
		stale_supplier_selection = {
			"type": "qwen_nbu_current_artifact_answer_activation_contract",
			"activation_mode": "visible_context_answer",
			"resolved_rank": 2,
			"resolved_entity": {
				"entity_type": "supplier",
				"entity_label": "Sunflower Accessories Co.",
				"entity_key": "Sunflower Accessories Co.",
				"row": {
					"rank": 2,
					"supplier": "Sunflower Accessories Co.",
					"outstanding_amount": 228576500,
					"overdue_amount": 192031500,
				},
			},
		}
		session_doc = {
			"messages": [
				_tool_message(stale_supplier_selection),
				_assistant_message(_customer_revenue_ranking_text()),
			]
		}
		self.assertEqual(visible_context_target_reference("All above 7 customers are from Yangon Region?"), "current_artifact")
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="All above 7 customers are from Yangon Region?",
			current_artifact=_ap_artifact(),
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_boundary")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("I can't verify that from the table above.", answer)
		self.assertIn("Territory", answer)
		self.assertNotIn("Sunflower Accessories Co.", answer)

	def test_prediction_boundary_uses_visible_row_facts_without_nbu_authority_trace(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="will the first customer default next month?",
			current_artifact=_ar_artifact(),
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_boundary")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("can't safely predict", answer)
		self.assertIn("Capital Telecom (NPT)", answer)
		self.assertNotIn("Rank 1 is Capital Telecom", answer)

	def test_ambiguous_deictic_question_asks_business_row_clarification(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}
		self.assertEqual(visible_context_target_reference("why is this customer risky?"), "selected_entity")
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

	def test_artifact_level_summary_question_yields_to_reasoning_lane(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}
		message = "Explain the overdue risk in this accounts receivable summary."
		self.assertTrue(artifact_level_visible_context_requested(message))
		self.assertEqual(visible_context_target_reference(message), "current_artifact")
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message=message,
			current_artifact=_ar_artifact(),
		)
		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertFalse(messages)

	def test_generic_artifact_meaning_question_yields_to_reasoning_lane(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}
		message = "what does this mean"
		self.assertTrue(artifact_level_visible_context_requested(message))
		self.assertEqual(visible_context_target_reference(message), "current_artifact")
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message=message,
			current_artifact=_ar_artifact(),
		)
		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertFalse(messages)

	def test_generic_artifact_risk_question_yields_to_reasoning_lane(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}
		message = "why is this risky?"
		self.assertTrue(artifact_level_visible_context_requested(message))
		self.assertEqual(visible_context_target_reference(message), "current_artifact")
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message=message,
			current_artifact=_ar_artifact(),
		)
		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertFalse(messages)

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
			authority_class="safe_explanation",
			requested_action="explain",
			governed_requery_plan={
				"status": "ready_shadow",
				"planner_mode": "entity_detail_requery",
				"target_route": "entity_detail",
				"shadow_execution_ready": True,
				"target_entity": {
					"entity_type": "customer",
					"name": "35th Street Mobile Wholesale",
				},
			},
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("35th Street Mobile Wholesale", answer)
		self.assertIn("rank 2", answer.lower())
		self.assertIn("Why this stands out from the visible row", answer)
		self.assertIn("68.6% of the outstanding balance", answer)
		self.assertIn("Consultant takeaway", answer)
		self.assertIn("Facts from that row", answer)
		self.assertIn("This is based only on the table above.", answer)

	def test_selected_row_reason_question_uses_invoice_drilldown_when_source_filters_are_proven(self):
		artifact = _ar_artifact_with_source_detail_filters()
		session_doc = {"messages": [_tool_message(artifact)]}
		handled, _payload, _messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is second in the above table?",
			current_artifact=artifact,
		)
		self.assertTrue(handled)
		with patch(
			"ai_assistant_ui.qwen_chat.source_detail_drilldown_execution.execute_governed_report",
			return_value=_sales_invoice_detail_payload(),
		) as execute:
			handled, payload, messages, _payloads = self._activate(
				session_doc=session_doc,
				raw_message="why is this customer risky?",
				current_artifact=artifact,
				authority_class="safe_explanation",
				requested_action="explain",
			)

		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Visible row signal", answer)
		self.assertIn("Deeper approved ERP detail", answer)
		self.assertIn("Sales Invoice List", answer)
		self.assertIn("SINV-2026-00042", answer)
		self.assertIn("Due Date", answer)
		execute.assert_called_once()
		self.assertEqual(execute.call_args.kwargs["filters"]["customer"], "35th Street Mobile Wholesale")
		self.assertEqual(execute.call_args.kwargs["filters"]["to_date"], "2026-05-08")

	def test_reason_style_supplier_question_uses_visible_payable_signals(self):
		session_doc = {"messages": [_tool_message(_ap_artifact())]}
		handled, _payload, _messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is second in the above table?",
			current_artifact=_ap_artifact(),
		)
		self.assertTrue(handled)
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="why is this supplier concerning?",
			current_artifact=_ap_artifact(),
			authority_class="safe_explanation",
			requested_action="explain",
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Sunflower Accessories Co.", answer)
		self.assertIn("Why this stands out from the visible row", answer)
		self.assertIn("136.7 MMK Million is overdue", answer)
		self.assertIn("61.4% of the outstanding balance", answer)
		self.assertIn("Consultant takeaway", answer)
		self.assertIn("Facts from that row", answer)

	def test_reasoning_explanation_overrides_detail_shadow_for_visible_row_signal(self):
		session_doc = {"messages": [_tool_message(_ar_artifact())]}
		handled, _payload, _messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is second in the above table?",
			current_artifact=_ar_artifact(),
		)
		self.assertTrue(handled)
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="why is this customer risky?",
			current_artifact=_ar_artifact(),
			authority_class="safe_read",
			requested_action="detail",
			reasoning_type="explanation",
			governed_requery_plan={
				"status": "ready_shadow",
				"planner_mode": "entity_detail_requery",
				"target_route": "entity_detail",
				"shadow_execution_ready": True,
				"target_entity": {
					"entity_type": "customer",
					"name": "35th Street Mobile Wholesale",
				},
			},
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("35th Street Mobile Wholesale", answer)
		self.assertIn("Why this stands out from the visible row", answer)
		self.assertIn("58.2 MMK Million is overdue", answer)

	def test_selected_entity_composite_context_uses_visible_row_explanation(self):
		session_doc = {"messages": [_tool_message(_ar_artifact())]}
		handled, _payload, _messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is second in the above table?",
			current_artifact=_ar_artifact(),
		)
		self.assertTrue(handled)
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="why is this customer risky?",
			current_artifact=_ar_artifact(),
			authority_class="safe_read",
			requested_action="show",
			target_reference="selected_entity",
			candidate_composite_family_ids=["customer_risk_as_of"],
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("35th Street Mobile Wholesale", answer)
		self.assertIn("Why this stands out from the visible row", answer)
		self.assertIn("58.2 MMK Million is overdue", answer)

	def test_prediction_question_returns_boundary_not_visible_fact_answer(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="will the first customer default next month?",
			authority_class="prediction",
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
			authority_class="recommendation",
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_boundary")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("can't choose who you should collect from first", answer)
		self.assertIn("Facts from the table above for Rank 1", answer)
		self.assertIn("Capital Telecom (NPT)", answer)
		self.assertIn("collection-priority policy", answer)

	def test_causal_question_returns_boundary_not_unsupported_cause_claim(self):
		session_doc = {"messages": [_assistant_message(_ar_visible_text())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="what caused the first customer's risk to increase?",
			authority_class="causal_driver_analysis",
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

	def test_entity_detail_evidence_followup_yields_to_artifact_boundary(self):
		session_doc = {"messages": [_tool_message(_sales_invoice_artifact())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="items from this invoices are already delivered?",
			current_artifact=_sales_invoice_detail_artifact(),
		)
		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertFalse(messages)

	def test_entity_detail_delivery_date_followup_yields_to_artifact_boundary(self):
		session_doc = {"messages": [_tool_message(_sales_invoice_artifact())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="what it was delivered",
			current_artifact=_sales_invoice_detail_artifact(),
		)
		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertFalse(messages)

	def test_entity_detail_tenure_clarification_yields_to_artifact_boundary(self):
		session_doc = {"messages": [_tool_message(_customer_detail_artifact())]}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="what is this customer's tenure?",
			current_artifact=_customer_detail_artifact(),
		)
		self.assertFalse(handled)
		self.assertIsNone(payload)
		self.assertFalse(messages)

	def test_latest_supplier_table_wins_over_stale_customer_focus_for_rank_reference(self):
		stale_customer_selection = {
			"type": "qwen_nbu_current_artifact_answer_activation_contract",
			"resolved_rank": 2,
			"resolved_entity": {
				"entity_type": "customer",
				"entity_key": "35th Street Mobile Wholesale",
				"entity_label": "35th Street Mobile Wholesale",
				"row": {
					"rank": 2,
					"customer": "35th Street Mobile Wholesale",
					"outstanding_amount": 84837000,
				},
			},
		}
		session_doc = {
			"messages": [
				_tool_message(_ar_artifact()),
				_tool_message(stale_customer_selection),
				_tool_message(_ap_artifact()),
			]
		}
		handled, payload, messages, _payloads = self._activate(
			session_doc=session_doc,
			raw_message="who is in rank 2 suppliers?",
			current_artifact=_ar_artifact(),
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_answer")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("Rank 2 is Sunflower Accessories Co.", answer)
		self.assertNotIn("35th Street Mobile Wholesale", answer)

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
			authority_class="recommendation",
		)
		self.assertTrue(handled)
		self.assertEqual(payload["mode"], "visible_context_boundary")
		answer = "\n".join(message[1] for message in messages)
		self.assertIn("can't make an action recommendation", answer)
		self.assertIn("Type-C Cable 2m Fast Charge", answer)
		self.assertIn("relevant decision policy", answer)


if __name__ == "__main__":
	unittest.main()
