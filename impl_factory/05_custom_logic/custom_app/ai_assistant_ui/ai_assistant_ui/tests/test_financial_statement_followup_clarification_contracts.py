import sys
import types
import unittest


def _fake_get_all(doctype, *args, **kwargs):
	if doctype == "Company":
		if kwargs.get("pluck") == "name":
			return ["Mingalar Mobile Distribution Co., Ltd."]
		return [{"name": "Mingalar Mobile Distribution Co., Ltd."}]
	if doctype == "Fiscal Year":
		return [
			{
				"name": "FY-2026",
				"year_start_date": "2025-04-01",
				"year_end_date": "2026-03-31",
			}
		]
	return []


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = _fake_get_all
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.contracts import build_fresh_query_interpretation_contract
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


if __name__ == "__main__":
	unittest.main()
