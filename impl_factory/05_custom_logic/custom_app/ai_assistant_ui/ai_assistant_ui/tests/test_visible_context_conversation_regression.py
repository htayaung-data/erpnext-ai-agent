import json
import unittest
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.semantic_reasoning_activation import (
	interpret_reasoning_activation_semantically,
)
from ai_assistant_ui.qwen_chat.visible_context_followup_activation import (
	try_activate_visible_context_followup_response,
)


def _assistant_message(text: str) -> Dict[str, Any]:
	return {
		"role": "assistant",
		"content": json.dumps({"type": "text", "text": text, "format": "markdown"}),
	}


def _shadow_payload(
	*,
	authority_class: str = "",
	requested_action: str = "",
	target_reference: str = "",
	candidate_composite_family_ids: List[str] | None = None,
) -> Dict[str, Any]:
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
		"request_id": "req-conversation-shadow",
		"selected_candidate_id": "candidate-1" if candidates else "",
		"candidate_interpretations": candidates,
		"authority_plan": {"authority_class": authority_class} if authority_class else {},
		"conversation_action_decision": {"action": "ask_clarification"},
	}


@dataclass
class ConversationTurnResult:
	handled: bool
	payload: Dict[str, Any] | None
	answer: str
	payloads: List[Dict[str, Any]]

	def latest_payload(self, payload_type: str) -> Dict[str, Any]:
		for payload in reversed(self.payloads):
			if payload.get("type") == payload_type:
				return payload
		return {}

	@property
	def trace(self) -> Dict[str, Any]:
		return self.latest_payload("qwen_visible_context_followup_trace_contract")

	@property
	def execution_path(self) -> Dict[str, Any]:
		return self.latest_payload("qwen_execution_path")


class VisibleConversationHarness:
	def __init__(self):
		self.session_doc: Dict[str, Any] = {"messages": []}

	def assistant(self, text: str) -> None:
		self.session_doc.setdefault("messages", []).append(_assistant_message(text))

	def ask(
		self,
		raw_message: str,
		*,
		current_artifact: Dict[str, Any] | None = None,
		authority_class: str = "",
		requested_action: str = "",
		target_reference: str = "",
		candidate_composite_family_ids: List[str] | None = None,
		reasoning_type: str = "",
	) -> ConversationTurnResult:
		messages = []
		payloads = []

		def append_message(session_doc, role, text):
			messages.append((role, text))
			session_doc.setdefault("messages", []).append({"role": role, "content": text})

		def append_payload(session_doc, payload):
			payloads.append(payload)
			session_doc.setdefault("messages", []).append({"role": "tool", "content": json.dumps(payload)})

		def save_session(session_doc, **kwargs):
			session_doc["saved"] = True

		reasoning_semantic_result = None
		if reasoning_type:
			reasoning_semantic_result = SimpleNamespace(
				status="accepted",
				intent=SimpleNamespace(reasoning_type=reasoning_type),
			)

		handled, payload = try_activate_visible_context_followup_response(
			session_doc=self.session_doc,
			request_id="req-visible-conversation",
			session_id="session-visible-conversation",
			user_id="user@example.com",
			site_name="erpai_prj1",
			raw_message=raw_message,
			current_artifact=current_artifact or {},
			reasoning_semantic_result=reasoning_semantic_result,
			append_message=append_message,
			append_tool_payload=append_payload,
			assistant_text_payload=lambda text: text,
			save_session=save_session,
			additional_tool_payloads=[
				_shadow_payload(
					authority_class=authority_class,
					requested_action=requested_action,
					target_reference=target_reference,
					candidate_composite_family_ids=candidate_composite_family_ids,
				)
			],
		)
		return ConversationTurnResult(
			handled=handled,
			payload=payload,
			answer="\n".join(message[1] for message in messages if message[0] == "assistant"),
			payloads=payloads,
		)


def _cogs_source_detail_text() -> str:
	return """Here is the source-detail breakdown for Cost of Goods Sold from Profit and Loss Statement.

Breakdown by source document

Source document	Net line impact (MMK Million)	Share of line
Delivery Note MAT-DN-2026-00339	13.5 MMK Million	20.6%
Delivery Note MAT-DN-2026-00336	11.3 MMK Million	17.3%
Delivery Note MAT-DN-2026-00337	11.2 MMK Million	17.1%
Delivery Note MAT-DN-2026-00338	5.5 MMK Million	8.4%
Delivery Note MAT-DN-2026-00335	3.5 MMK Million	5.3%
Sales Invoice ACC-SINV-2026-00776	3.4 MMK Million	5.2%
Sales Invoice ACC-SINV-2026-00779	3.1 MMK Million	4.8%
Delivery Note MAT-DN-2026-00334	2.8 MMK Million	4.3%
"""


def _ar_top_10_text() -> str:
	return """Accounts Receivable Aging as of 2026-05-10

Top 10 Customers

Customer	Outstanding (MMK)	Total Due (MMK)	Overdue (31+) (MMK)
Capital Telecom (NPT)	97,309,500	63,654,500	35,274,500
Bayint Naung Wholesale Mobile	95,513,000	69,287,000	33,559,000
35th Street Mobile Wholesale	84,837,000	82,527,000	58,212,000
Ko Nay Lin Mobile Center	63,125,000	63,125,000	37,335,000
Latha Mobile Wholesale	49,352,000	49,352,000	33,372,000
Mandalay Accessories Wholesale	38,320,000	33,090,000	29,430,000
Mandalay Mobile Hub	38,100,000	38,100,000	28,280,000
Taunggyi City Mobile	37,010,000	37,010,000	37,010,000
Shwe Li Road Mobile Wholesale	36,850,000	36,850,000	36,850,000
Hlaing Tharyar Mobile Corner	34,648,000	34,648,000	34,648,000
"""


def _ar_overdue_comparison_text() -> str:
	return """Here is the comparison from Accounts Receivable Summary.

Comparison table

Party	Outstanding (MMK Million)	Overdue (MMK Million)	Overdue intensity
35th Street Mobile Wholesale	84.8 MMK Million	58.2 MMK Million	68.6%
Ko Nay Lin Mobile Center	63.1 MMK Million	37.3 MMK Million	59.1%
Taunggyi City Mobile	37 MMK Million	37 MMK Million	100%
Shwe Li Road Mobile Wholesale	36.9 MMK Million	36.9 MMK Million	100%
Capital Telecom (NPT)	97.3 MMK Million	35.3 MMK Million	36.2%
Hlaing Tharyar Mobile Corner	34.6 MMK Million	34.6 MMK Million	100%
Bayint Naung Wholesale Mobile	95.5 MMK Million	33.6 MMK Million	35.1%
"""


def _ap_top_5_text() -> str:
	return """Accounts Payable Aging as of 2026-05-10

Top 5 Suppliers

Supplier	Outstanding (MMK)	Total Due (MMK)	Overdue (31+) (MMK)
Myanmar Tech Import Services	268,298,000	250,568,000	193,478,000
Sunflower Accessories Co.	228,576,500	222,526,500	191,621,500
Golden Dragon Trading Co. Ltd.	224,780,600	197,040,600	118,060,600
Mandalay Device Wholesale	75,408,500	75,408,500	75,408,500
Shwe Taung Electronics Supply	57,710,000	57,710,000	29,810,000
"""


def _supplier_invoice_breakdown_text() -> str:
	return """Sunflower Accessories Co. is the rank 2 entry in the table above.

Deeper approved ERP detail:

Breakdown by invoice

Invoice	Posting Date	Due Date	Status	Invoice Total	Outstanding amount (MMK Million)	Share of selected balance
ACC-PINV-2026-00306	2026-03-07	2026-04-06	Overdue	44,730,000	40.7 MMK Million	17.8%
ACC-PINV-2026-00053	2026-01-13	2026-02-15	Overdue	37,000,000	33.5 MMK Million	14.7%
ACC-PINV-2026-00058	2026-01-31	2026-02-15	Overdue	28,150,000	22.2 MMK Million	9.7%
"""


def _supplier_entity_detail_text() -> str:
	return """Sunflower Accessories Co. Details

Profile

Field	Value
Name	Sunflower Accessories Co.
Code	Sunflower Accessories Co.
Group	Accessories Supplier

Recent Purchase Invoices

Invoice	Posting Date	Amount (MMK)	Outstanding (MMK)	Status
ACC-PINV-2026-00339	2026-05-19	6,430,000	6,430,000	Unpaid
ACC-PINV-2026-00340	2026-05-05	6,050,000	2,050,000	Partly Paid
ACC-PINV-2026-00336	2026-04-15	10,420,000	7,420,000	Partly Paid
"""


def _supplier_entity_detail_artifact() -> Dict[str, Any]:
	return {
		"type": "qwen_entity_detail_artifact",
		"family_id": "entity_detail",
		"dimensions": {
			"entity_type": "supplier",
			"entity_key": "Sunflower Accessories Co.",
			"entity_label": "Sunflower Accessories Co.",
		},
	}


def _product_revenue_text() -> str:
	return """Top 7 Products by Revenue Last Year

Rank	Product	Revenue (MMK)
1	Samsung Galaxy A15 (6GB 128GB)	341,209,000
2	Xiaomi Redmi Note 13 (8GB 256GB)	281,770,000
3	Power Bank 20000mAh	174,195,000
4	Apple iPhone 13 128GB	134,835,000
5	Samsung PD Charger 25W	72,170,500
6	JBL GO3 Bluetooth Speaker	67,472,000
7	Xiaomi Fast Charger 33W	65,799,000
"""


def _assert_visible_answer(
	testcase: unittest.TestCase,
	result: ConversationTurnResult,
	*,
	answer_contains: str,
	business_object_type: str,
	relation: str | None = None,
	mode: str = "visible_context_answer",
) -> None:
	testcase.assertTrue(result.handled)
	testcase.assertEqual(result.payload["mode"], mode)
	testcase.assertIn(answer_contains, result.answer)
	trace = result.trace
	testcase.assertEqual(trace.get("type"), "qwen_visible_context_followup_trace_contract")
	arbitration = trace.get("frame_arbitration") or {}
	observability = trace.get("authority_observability") or {}
	testcase.assertEqual(arbitration.get("status"), "resolved" if mode == "visible_context_answer" else "out_of_range")
	if relation:
		testcase.assertEqual(arbitration.get("relation"), relation)
	testcase.assertEqual(arbitration.get("selected_business_object_type"), business_object_type)
	testcase.assertEqual(observability.get("selected_business_object_type"), business_object_type)
	testcase.assertTrue(observability.get("selected_frame_id"))
	testcase.assertGreaterEqual(observability.get("candidate_frame_count") or 0, 1)
	execution_path = result.execution_path
	testcase.assertEqual(execution_path.get("path"), mode)
	testcase.assertFalse(execution_path.get("requires_runtime"))


class VisibleContextConversationRegressionTests(unittest.TestCase):
	def test_cogs_source_document_rank_sequence_preserves_same_table(self):
		chat = VisibleConversationHarness()
		chat.assistant(_cogs_source_detail_text())

		first_lookup = chat.ask("who is second in the above table?")
		_assert_visible_answer(
			self,
			first_lookup,
			answer_contains="Delivery Note MAT-DN-2026-00336",
			business_object_type="document",
		)

		repeated_lookup = chat.ask("who is second in same table?")
		_assert_visible_answer(
			self,
			repeated_lookup,
			answer_contains="Delivery Note MAT-DN-2026-00336",
			business_object_type="document",
			relation="same_table",
		)

	def test_repeated_above_table_can_recover_from_visible_trace_frame(self):
		chat = VisibleConversationHarness()
		chat.assistant(_cogs_source_detail_text())
		first_lookup = chat.ask("who is second in the above table?")
		_assert_visible_answer(
			self,
			first_lookup,
			answer_contains="Delivery Note MAT-DN-2026-00336",
			business_object_type="document",
		)
		chat.session_doc["messages"] = [
			message
			for message in chat.session_doc["messages"]
			if "Breakdown by source document" not in str(message.get("content", ""))
		]

		repeated_lookup = chat.ask("who is second in the above table?")

		_assert_visible_answer(
			self,
			repeated_lookup,
			answer_contains="Delivery Note MAT-DN-2026-00336",
			business_object_type="document",
		)
		arbitration = repeated_lookup.trace.get("frame_arbitration") or {}
		self.assertEqual(arbitration.get("selected_evidence_scope"), "visible_rendered_table")
		self.assertEqual(arbitration.get("selected_recovery_source"), "visible_context_trace_frame")
		self.assertIn("recovery:visible_context_trace_frame", arbitration.get("candidate_frames", [{}])[0].get("match_reasons", []))
		observability = repeated_lookup.trace.get("authority_observability") or {}
		self.assertEqual(observability.get("selected_recovery_source"), "visible_context_trace_frame")

	def test_missing_typed_detail_does_not_fall_back_to_stale_source_table(self):
		chat = VisibleConversationHarness()
		chat.assistant(_cogs_source_detail_text())
		cogs_lookup = chat.ask("who is second in the above table?")
		_assert_visible_answer(
			self,
			cogs_lookup,
			answer_contains="Delivery Note MAT-DN-2026-00336",
			business_object_type="document",
		)

		chat.assistant(_ap_top_5_text())
		supplier_lookup = chat.ask("who is second in the above table?")
		_assert_visible_answer(
			self,
			supplier_lookup,
			answer_contains="Sunflower Accessories Co.",
			business_object_type="supplier",
		)

		missing_invoice = chat.ask("who is second invoice in the above context?")

		self.assertTrue(missing_invoice.handled)
		self.assertEqual(missing_invoice.payload["mode"], "visible_context_boundary")
		self.assertIn("no visible invoice table", missing_invoice.answer)
		self.assertIn("should not reuse an older table", missing_invoice.answer)
		self.assertNotIn("Delivery Note MAT-DN-2026-00336", missing_invoice.answer)
		self.assertNotIn("Rank 2 is Sunflower Accessories Co.", missing_invoice.answer)
		arbitration = missing_invoice.trace.get("frame_arbitration") or {}
		self.assertEqual(arbitration.get("status"), "missing_requested_object")
		self.assertEqual(arbitration.get("relation"), "detail_table")
		self.assertEqual(arbitration.get("requested_object_label"), "invoice")
		self.assertGreaterEqual(arbitration.get("candidate_frame_count") or 0, 1)
		self.assertTrue(arbitration.get("rejected_frames"))
		self.assertEqual(arbitration.get("rejected_frames")[0].get("rejection_reason"), "requested_object_type_mismatch")
		observability = missing_invoice.trace.get("authority_observability") or {}
		self.assertEqual(observability.get("requested_object_label"), "invoice")
		self.assertGreaterEqual(observability.get("rejected_frame_count") or 0, 1)
		self.assertFalse(missing_invoice.execution_path.get("requires_runtime"))

	def test_ar_comparison_out_of_range_stays_on_latest_visible_table(self):
		chat = VisibleConversationHarness()
		chat.assistant(_ar_top_10_text())
		chat.assistant(_ar_overdue_comparison_text())

		fourth_lookup = chat.ask("who is fourth in the above table?")
		_assert_visible_answer(
			self,
			fourth_lookup,
			answer_contains="Shwe Li Road Mobile Wholesale",
			business_object_type="party",
		)

		out_of_range = chat.ask("give me more about Rank 11 customer")
		self.assertTrue(out_of_range.handled)
		self.assertEqual(out_of_range.payload["mode"], "visible_context_out_of_range")
		self.assertIn("only 7 visible rows", out_of_range.answer)
		self.assertIn("Rank 7: Bayint Naung Wholesale Mobile", out_of_range.answer)
		self.assertNotIn("Rank 10:", out_of_range.answer)
		self.assertEqual((out_of_range.trace.get("resolution") or {}).get("status"), "out_of_range")
		arbitration = out_of_range.trace.get("frame_arbitration") or {}
		self.assertEqual(arbitration.get("status"), "resolved")
		self.assertEqual(arbitration.get("selected_business_object_type"), "party")
		self.assertFalse(out_of_range.execution_path.get("requires_runtime"))

	def test_ap_supplier_invoice_sequence_preserves_relation_and_response_shape(self):
		chat = VisibleConversationHarness()
		chat.assistant(_ap_top_5_text())
		chat.assistant(_supplier_invoice_breakdown_text())

		same_table_invoice = chat.ask("who is second in same table?")
		_assert_visible_answer(
			self,
			same_table_invoice,
			answer_contains="ACC-PINV-2026-00053",
			business_object_type="invoice",
			relation="same_table",
		)

		parent_supplier = chat.ask(
			"who is second supplier in the above context?",
			requested_action="detail",
			target_reference="selected_entity",
			candidate_composite_family_ids=["accounts_payable_invoice_detail"],
		)
		_assert_visible_answer(
			self,
			parent_supplier,
			answer_contains="Rank 2 is Sunflower Accessories Co.",
			business_object_type="supplier",
		)
		self.assertIn("Current row facts", parent_supplier.answer)
		self.assertNotIn("Deeper approved ERP detail", parent_supplier.answer)
		self.assertNotIn("ACC-PINV-2026-00053", parent_supplier.answer)

		detail_invoice = chat.ask("who is second invoice in the above context?")
		_assert_visible_answer(
			self,
			detail_invoice,
			answer_contains="ACC-PINV-2026-00053",
			business_object_type="invoice",
			relation="detail_table",
		)

	def test_entity_detail_current_artifact_does_not_block_visible_invoice_rank_lookup(self):
		chat = VisibleConversationHarness()
		chat.assistant(_supplier_entity_detail_text())

		detail_invoice = chat.ask(
			"who is second invoice in the above context?",
			current_artifact=_supplier_entity_detail_artifact(),
		)

		_assert_visible_answer(
			self,
			detail_invoice,
			answer_contains="ACC-PINV-2026-00340",
			business_object_type="invoice",
			relation="detail_table",
		)

	def test_cross_context_switching_keeps_previous_and_typed_tables_distinct(self):
		chat = VisibleConversationHarness()
		chat.assistant(_ar_top_10_text())
		chat.assistant(_product_revenue_text())

		product_lookup = chat.ask("who is second in the above table?")
		_assert_visible_answer(
			self,
			product_lookup,
			answer_contains="Xiaomi Redmi Note 13",
			business_object_type="item",
		)

		chat.assistant(_ap_top_5_text())
		previous_table = chat.ask("who is second in previous table?")
		_assert_visible_answer(
			self,
			previous_table,
			answer_contains="Xiaomi Redmi Note 13",
			business_object_type="item",
			relation="previous_table",
		)

		supplier_lookup = chat.ask("who is second supplier in the above context?")
		_assert_visible_answer(
			self,
			supplier_lookup,
			answer_contains="Sunflower Accessories Co.",
			business_object_type="supplier",
		)

		product_typed_lookup = chat.ask("who is second product in the previous product table?")
		_assert_visible_answer(
			self,
			product_typed_lookup,
			answer_contains="Xiaomi Redmi Note 13",
			business_object_type="item",
		)

	def test_business_intent_boundaries_are_enforced_from_visible_evidence(self):
		chat = VisibleConversationHarness()
		chat.assistant(_ar_top_10_text())
		chat.assistant(_ar_overdue_comparison_text())

		recommendation = chat.ask("who should we collect from first?")
		self.assertTrue(recommendation.handled)
		self.assertEqual(recommendation.payload["mode"], "visible_context_boundary")
		self.assertIn("can't turn it into a recommended action", recommendation.answer)
		self.assertIn("Visible facts for Rank 1 (35th Street Mobile Wholesale)", recommendation.answer)
		self.assertEqual((recommendation.trace.get("resolution") or {}).get("authority_intent"), "recommendation_boundary")
		self.assertFalse(recommendation.execution_path.get("requires_runtime"))

		causal = chat.ask("what caused the first customer's risk to increase?")
		self.assertTrue(causal.handled)
		self.assertEqual(causal.payload["mode"], "visible_context_boundary")
		self.assertIn("can't attribute cause from this single displayed result", causal.answer)
		self.assertIn("trend, event trail, or transaction history", causal.answer)
		self.assertEqual((causal.trace.get("resolution") or {}).get("authority_intent"), "causal_boundary")
		self.assertFalse(causal.execution_path.get("requires_runtime"))

		filter_check = chat.ask("All above customers are from Yangon Region?")
		self.assertTrue(filter_check.handled)
		self.assertEqual(filter_check.payload["mode"], "visible_context_boundary")
		self.assertIn("does not include the requested fields", filter_check.answer)
		self.assertIn("Visible evidence covers: Party, Outstanding Amount, Overdue Amount, Overdue Intensity.", filter_check.answer)
		self.assertIn("Fields needed: Customer, Territory.", filter_check.answer)
		self.assertNotIn("Asia Connect Logistics", filter_check.answer)
		filter_contract = filter_check.latest_payload("qwen_filter_readiness_contract")
		self.assertEqual(filter_contract["status"], "missing_filter_evidence")
		self.assertEqual(filter_contract["requested_filter_keys"], ["customer", "territory"])
		self.assertEqual(filter_contract["missing_visible_field_keys"], ["customer", "territory"])
		self.assertEqual(filter_contract["unsupported_filter_keys"], ["territory"])
		self.assertFalse(filter_check.execution_path.get("requires_runtime"))

	def test_artifact_level_reasoning_after_old_selection_does_not_use_stale_row(self):
		chat = VisibleConversationHarness()
		chat.assistant(_cogs_source_detail_text())
		selected_cogs_row = chat.ask("who is second in the above table?")
		_assert_visible_answer(
			self,
			selected_cogs_row,
			answer_contains="Delivery Note MAT-DN-2026-00336",
			business_object_type="document",
		)
		chat.assistant(_ar_top_10_text())
		chat.assistant(_ar_overdue_comparison_text())

		explanation = chat.ask(
			"Explain the overdue risk in this accounts receivable summary.",
			reasoning_type="explanation",
		)

		self.assertFalse(explanation.handled)
		self.assertNotIn("Delivery Note MAT-DN-2026-00336", explanation.answer)

	def test_generic_more_insight_anchors_to_working_capital_metadata(self):
		with patch(
			"ai_assistant_ui.qwen_chat.semantic_reasoning_activation.call_qwen_runtime_reasoning_activation_interpretation"
		) as runtime_call:
			result = interpret_reasoning_activation_semantically(
				request_id="ux-s6e-more-insight-anchor",
				session_id="ux-s6e",
				user_id="Administrator",
				site_name="test.local",
				message="Give me more insight",
				recent_messages=[],
				latest_grounded_turn={
					"grounded": True,
					"source_kind": "report",
					"source_name": "AR/AP Working Capital Health",
					"artifact_family_id": "working_capital_health",
					"artifact_type": "normalized_family_artifact",
					"artifact_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
					"row_count": 5,
				},
				latest_family_artifact={
					"family_id": "working_capital_health",
					"artifact_type": "normalized_family_artifact",
					"source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
					"capability_id": "working_capital_health_read",
				},
				latest_assistant_payload={"title": "AR/AP Working Capital Health"},
				activation_contract={
					"activation_state": "eligible",
					"grounded_context_available": True,
					"grounded_source_kind": "report",
					"grounded_source_name": "AR/AP Working Capital Health",
					"grounded_family_id": "working_capital_health",
					"grounded_artifact_type": "normalized_family_artifact",
					"grounded_source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
					"grounded_capability_id": "working_capital_health_read",
					"allowed_reasoning_types": [
						"interpretation",
						"explanation",
						"recommendation",
						"continuation_detail",
					],
					"route_target": "reasoning_lane",
				},
			)
		self.assertEqual(result.status, "accepted")
		self.assertIsNotNone(result.intent)
		self.assertEqual(result.intent.reasoning_type, "continuation_detail")
		self.assertEqual(result.intent.answer_goal, "expand_detail")
		self.assertEqual(result.intent.target_reference, "current_result")
		self.assertEqual(result.agent_meta.get("activation_source"), "governed_followup_metadata")
		runtime_call.assert_not_called()


if __name__ == "__main__":
	unittest.main()
