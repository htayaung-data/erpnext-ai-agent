import sys
import types
import unittest
from unittest.mock import patch


def _fake_get_all(doctype, *args, **kwargs):
	if doctype == "Company":
		if kwargs.get("pluck") == "name":
			return ["Mingalar Mobile Distribution Co., Ltd."]
		return [{"name": "Mingalar Mobile Distribution Co., Ltd."}]
	if doctype == "Fiscal Year":
		return [
			{
				"name": "FY-2025",
				"year_start_date": "2024-04-01",
				"year_end_date": "2025-03-31",
			},
			{
				"name": "FY-2026",
				"year_start_date": "2025-04-01",
				"year_end_date": "2026-03-31",
			},
			{
				"name": "FY-2027",
				"year_start_date": "2026-04-01",
				"year_end_date": "2027-03-31",
			},
		]
	if doctype == "Period Closing Voucher":
		return [
			{
				"name": "PCV-2025-0001",
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"fiscal_year": "FY-2025",
				"period_start_date": "2024-04-01",
				"period_end_date": "2025-03-31",
				"transaction_date": "2025-03-31",
				"gle_processing_status": "Completed",
			}
		]
	return []


if "frappe" not in sys.modules:
	fake_frappe = types.ModuleType("frappe")
	fake_frappe.get_all = _fake_get_all
	fake_frappe.conf = {}
	fake_frappe.local = types.SimpleNamespace(site="")
	fake_frappe.db = types.SimpleNamespace(exists=lambda *args, **kwargs: False)
	sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.contracts import build_fresh_query_interpretation_contract
from ai_assistant_ui.qwen_chat.boundary_support import financial_statement_section_direct_evidence_answer
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import (
	_apply_clarification_resolution_to_interpretation,
	_deterministic_family_surface_interpretation,
	_message_requests_generic_financial_statement,
	_reconcile_generic_financial_statement_request_from_message,
)


class FinancialStatementFollowupClarificationContractsTest(unittest.TestCase):
	def test_generic_financial_statement_request_is_detected_without_variant(self):
		self.assertTrue(_message_requests_generic_financial_statement("show me financial statement"))
		self.assertTrue(_message_requests_generic_financial_statement("show me statement"))
		self.assertTrue(_message_requests_generic_financial_statement("show me management report"))
		self.assertFalse(_message_requests_generic_financial_statement("show me balance sheet"))
		self.assertFalse(_message_requests_generic_financial_statement("P & L statement"))

	def test_deterministic_surface_fallback_preserves_missing_variant_for_generic_statement_request(self):
		interpretation = _deterministic_family_surface_interpretation(
			request_id="financial-statement-generic",
			session_id="session-1",
			message="show me financial statement",
			confidence_threshold=0.72,
		)
		self.assertIsNotNone(interpretation)
		self.assertEqual(interpretation.intent_class, "financial_statement")
		self.assertEqual(list(interpretation.candidate_capability_ids), ["financial_statement_read"])
		self.assertEqual(list(interpretation.candidate_reports), [])
		self.assertEqual(interpretation.requested_time_scope, "open_fiscal_year_to_date")
		self.assertIn("ambiguous_report", list(interpretation.ambiguity_flags))

	def test_generic_statement_request_clears_stale_statement_variant_from_interpretation(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="financial-statement-stale",
			session_id="session-1",
			intent_class="financial_statement",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=["Profit and Loss Statement"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="open_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={"statement_variant": "profit_and_loss"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.95,
		)
		reconciled = _reconcile_generic_financial_statement_request_from_message(
			message="show me financial statement",
			interpretation=interpretation,
		)
		self.assertIsNotNone(reconciled)
		self.assertEqual(reconciled.intent_class, "financial_statement")
		self.assertEqual(list(reconciled.candidate_reports), [])
		self.assertEqual(reconciled.requested_time_scope, "open_fiscal_year_to_date")
		self.assertNotIn("statement_variant", dict(reconciled.extracted_slots))
		self.assertIn("ambiguous_report", list(reconciled.ambiguity_flags))

	def test_explicit_statement_variant_is_preserved(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="financial-statement-explicit",
			session_id="session-1",
			intent_class="financial_statement",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=["Balance Sheet"],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="open_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={"statement_variant": "balance_sheet"},
			ambiguity_flags=[],
			ambiguity_reason="",
			confidence=0.95,
		)
		reconciled = _reconcile_generic_financial_statement_request_from_message(
			message="give me balance sheet",
			interpretation=interpretation,
		)
		self.assertEqual(list(reconciled.candidate_reports), ["Balance Sheet"])
		self.assertEqual(reconciled.requested_time_scope, "open_fiscal_year_to_date")
		self.assertEqual(dict(reconciled.extracted_slots).get("statement_variant"), "balance_sheet")

	def test_clarified_statement_variant_backfills_report_from_canonical_slot(self):
		interpretation = build_fresh_query_interpretation_contract(
			request_id="financial-statement-clarified-slot",
			session_id="session-1",
			intent_class="financial_statement",
			candidate_capability_ids=["financial_statement_read"],
			candidate_reports=[],
			requested_dimensions=[],
			requested_metrics=[],
			requested_time_scope="open_fiscal_year_to_date",
			requested_presentation=[],
			extracted_slots={},
			ambiguity_flags=["ambiguous_report"],
			ambiguity_reason="Financial statement requests require an explicit statement view before execution.",
			confidence=0.95,
		)
		reconciled = _apply_clarification_resolution_to_interpretation(
			interpretation=interpretation,
			clarification_resolution={
				"decision": "resolved_option",
				"resolved_slot": {
					"statement_variant": "profit_and_loss",
				},
			},
		)
		self.assertEqual(list(reconciled.candidate_reports), ["Profit and Loss Statement"])
		self.assertEqual(dict(reconciled.extracted_slots).get("statement_variant"), "profit_and_loss")
		self.assertNotIn("ambiguous_report", list(reconciled.ambiguity_flags))

	def test_frontdoor_session_flow_does_not_swallow_bare_statement_reask(self):
		from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import interpret_front_door_semantically

		with patch(
			"ai_assistant_ui.qwen_chat.frontdoor_intent_gate.call_qwen_runtime_frontdoor_interpretation",
			return_value={
				"interpretation": {
					"intent_class": "session_flow",
					"confidence": 0.96,
					"reason": "The user appears to continue the current context.",
				},
				"agent_meta": {},
			},
		), patch(
			"ai_assistant_ui.qwen_chat.frontdoor_intent_gate.interpret_fresh_query_semantically",
			return_value=types.SimpleNamespace(
				status="accepted",
				confidence_threshold=0.72,
				interpretation=types.SimpleNamespace(
					candidate_capability_ids=["financial_statement_read"],
					candidate_reports=[],
					confidence=0.93,
				),
			),
		):
			result = interpret_front_door_semantically(
				request_id="frontdoor-statement-reask",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me statement",
				recent_messages=[],
				grounded_context_available=True,
			)
		self.assertEqual(result.status, "guardrailed_to_route_onward")
		self.assertIsNotNone(result.intent)
		self.assertEqual(result.intent.intent_class, "route_onward")

	def test_frontdoor_session_flow_uses_deterministic_fresh_query_guard_when_runtime_crosscheck_degrades(self):
		from ai_assistant_ui.qwen_chat.frontdoor_intent_gate import interpret_front_door_semantically

		with patch(
			"ai_assistant_ui.qwen_chat.frontdoor_intent_gate.call_qwen_runtime_frontdoor_interpretation",
			return_value={
				"interpretation": {
					"intent_class": "session_flow",
					"confidence": 0.96,
					"reason": "The user appears to continue the current context.",
				},
				"agent_meta": {},
			},
		), patch(
			"ai_assistant_ui.qwen_chat.frontdoor_intent_gate.interpret_fresh_query_semantically",
			return_value=types.SimpleNamespace(
				status="runtime_error",
				confidence_threshold=0.72,
				interpretation=None,
				runtime_error="temporary runtime degradation",
			),
		):
			result = interpret_front_door_semantically(
				request_id="frontdoor-statement-reask-degraded",
				session_id="session-1",
				user_id="Administrator",
				site_name="erpai_prj1",
				message="show me statement",
				recent_messages=[],
				grounded_context_available=True,
			)
		self.assertEqual(result.status, "guardrailed_to_route_onward")
		self.assertIsNotNone(result.intent)
		self.assertEqual(result.intent.intent_class, "route_onward")

	def test_balance_sheet_liability_section_followup_answers_from_current_artifact(self):
		answer = financial_statement_section_direct_evidence_answer(
			raw_message="Explain more about Liabilities",
			artifact_payload={
				"family_id": "financial_statement",
				"dimensions": {
					"statement_type": "balance_sheet",
					"currency": "MMK",
				},
				"metrics": {
					"total_liability": 1290195600,
				},
				"sections": {
					"liabilities": [
						{"label": "Creditors", "amount": 906366600},
						{"label": "Bank Overdraft Account", "amount": 118000000},
						{"label": "Unsecured Loans", "amount": 98900000},
					]
				},
			},
		)
		self.assertIn("Liabilities in the current Balance Sheet total 1,290,195,600 MMK", answer)
		self.assertIn("Creditors", answer)
		self.assertIn("Bank Overdraft Account", answer)
		self.assertIn("current financial statement result", answer)

	def test_balance_sheet_liability_section_followup_supports_natural_more_wording(self):
		answer = financial_statement_section_direct_evidence_answer(
			raw_message="tell me more about Liabilities",
			artifact_payload={
				"family_id": "financial_statement",
				"dimensions": {
					"statement_type": "balance_sheet",
					"currency": "MMK",
				},
				"metrics": {
					"total_liability": 1290195600,
				},
				"sections": {
					"liabilities": [
						{"label": "Creditors", "amount": 906366600},
						{"label": "Bank Overdraft Account", "amount": 118000000},
					]
				},
			},
		)
		self.assertIn("Liabilities in the current Balance Sheet", answer)
		self.assertIn("Creditors", answer)

	def test_statement_section_followup_does_not_capture_statement_switch(self):
		answer = financial_statement_section_direct_evidence_answer(
			raw_message="Cash Flow",
			artifact_payload={
				"family_id": "financial_statement",
				"dimensions": {
					"statement_type": "balance_sheet",
					"currency": "MMK",
				},
				"metrics": {
					"total_asset": 1845564663.71,
				},
				"sections": {
					"assets": [
						{"label": "Cash", "amount": 68534000},
					]
				},
			},
		)
		self.assertEqual(answer, "")


if __name__ == "__main__":
	unittest.main()
