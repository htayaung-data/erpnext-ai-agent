import sys
import types
import unittest


def _fake_get_all(doctype, *args, **kwargs):
	if doctype == "Company":
		if kwargs.get("pluck") == "name":
			return ["Enterprise Co"]
		return [{"name": "Enterprise Co"}]
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
				"company": "Enterprise Co",
				"fiscal_year": "FY-2025",
				"period_start_date": "2024-04-01",
				"period_end_date": "2025-03-31",
				"transaction_date": "2025-03-31",
				"gle_processing_status": "Completed",
			}
		]
	return []


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = _fake_get_all
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.artifact_narrative import _artifact_narrative_system_prompt
from ai_assistant_ui.qwen_chat.response_policy import derive_response_policy


class TestResponsePolicyAndNarrativeContracts(unittest.TestCase):
	def test_statement_question_without_analysis_stays_factual(self):
		policy = derive_response_policy(
			raw_message="show me balance sheet",
			analysis_requested=False,
			followup_mode="new_query",
			self_contained=True,
		)
		self.assertEqual(policy.get("answer_style"), "statement_question")
		self.assertFalse(policy.get("implication_allowed"))
		self.assertFalse(policy.get("recommendation_allowed"))
		self.assertNotIn("implication", list(policy.get("structure") or []))

	def test_statement_question_with_analysis_allows_implication(self):
		policy = derive_response_policy(
			raw_message="analyze the balance sheet",
			analysis_requested=True,
			followup_mode="new_query",
			self_contained=True,
		)
		self.assertEqual(policy.get("answer_style"), "statement_question")
		self.assertTrue(policy.get("implication_allowed"))
		self.assertTrue(policy.get("recommendation_allowed"))
		self.assertIn("implication", list(policy.get("structure") or []))

	def test_financial_statement_narrative_prompt_enforces_exact_units(self):
		prompt = _artifact_narrative_system_prompt(
			family_id="financial_statement",
			source_reports=["Balance Sheet"],
			response_policy={
				"answer_style": "statement_question",
				"implication_allowed": False,
				"recommendation_allowed": False,
				"direct_answer_first": True,
			},
		)
		self.assertIn("Use the exact amounts and units already shown", prompt)
		self.assertIn("Do not rescale full MMK amounts", prompt)
		self.assertIn("Do not add a 'Business implication' section", prompt)


if __name__ == "__main__":
	unittest.main()
