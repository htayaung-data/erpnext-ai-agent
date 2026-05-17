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

from ai_assistant_ui.qwen_chat.contracts import NormalizedFamilyArtifactContract
from ai_assistant_ui.qwen_chat.family_adapters import build_normalized_family_artifact
from ai_assistant_ui.qwen_chat.family_rendering import render_normalized_family_response
from ai_assistant_ui.qwen_chat.fresh_query_interpreter import _family_narrative_prefers_rendered_response


class FinancialStatementRenderingContractsTest(unittest.TestCase):
	def _artifact(self, statement_type: str, metrics: dict, sections: dict) -> NormalizedFamilyArtifactContract:
		return NormalizedFamilyArtifactContract(
			request_id=f"statement-{statement_type}",
			family_id="financial_statement",
			artifact_type="normalized_family_artifact",
			source_reports=[
				{
					"profit_and_loss": "Profit and Loss Statement",
					"balance_sheet": "Balance Sheet",
					"cash_flow": "Cash Flow",
				}.get(statement_type, "Financial Statement")
			],
			period={"from_date": "2025-04-01", "to_date": "2026-04-16"},
			filters={"company": "Mingalar Mobile Distribution Co., Ltd."},
			dimensions={"statement_type": statement_type, "currency": "MMK"},
			metrics=metrics,
			sections=sections,
			warnings=[],
		)

	def test_financial_statement_renderer_uses_metadata_owned_title_when_source_report_missing(self):
		artifact = NormalizedFamilyArtifactContract(
			request_id="statement-title-fallback",
			family_id="financial_statement",
			artifact_type="normalized_family_artifact",
			source_reports=[],
			period={"from_date": "2025-04-01", "to_date": "2026-04-16"},
			filters={"company": "Mingalar Mobile Distribution Co., Ltd."},
			dimensions={"statement_type": "cash_flow", "currency": "MMK"},
			metrics={
				"net_cash_from_operations": -226835151.21,
				"net_cash_from_investing": -325010000,
				"net_cash_from_financing": 178753611.11,
				"net_change_in_cash": -373091540.10,
			},
			sections={
				"operations": [
					{"label": "Net Change in Accounts Payable", "account": "Net Change in Accounts Payable", "amount": 1082291100.00, "indent": 1},
				],
				"investing": [
					{"label": "Net Change in Fixed Asset", "account": "Net Change in Fixed Asset", "amount": -325010000.00, "indent": 1},
				],
				"financing": [
					{"label": "Net Change in Equity", "account": "Net Change in Equity", "amount": 178753611.11, "indent": 1},
				],
			},
			warnings=[],
		)
		rendered = render_normalized_family_response(
			request_id="render-title-fallback",
			artifact_contract=artifact,
		)
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("Cash Flow (2025-04-01 to 2026-04-16)", answer_text)

	def test_profit_and_loss_renderer_produces_deterministic_exact_summary(self):
		artifact = self._artifact(
			"profit_and_loss",
			{
				"total_income": 1458275000.04,
				"total_expense": 1372131695.50,
				"net_profit": 172154431.22,
			},
			{
				"income": [
					{"label": "Income", "account": "Income", "amount": 1458275000.04, "indent": 0},
					{"label": "Direct Income", "account": "Direct Income", "parent_account": "Income", "amount": 1458275000.04, "indent": 1},
					{"label": "Sales", "account": "Sales", "parent_account": "Direct Income", "amount": 1458275000.04, "indent": 2},
				],
				"expense": [
					{"label": "Expenses", "account": "Expenses", "amount": 1372131695.50, "indent": 0},
					{"label": "Stock Expenses", "account": "Stock Expenses", "parent_account": "Expenses", "amount": 984602148.60, "indent": 1},
					{"label": "Cost of Goods Sold", "account": "Cost of Goods Sold", "parent_account": "Stock Expenses", "amount": 980896626.46, "indent": 2},
					{"label": "Indirect Expenses", "account": "Indirect Expenses", "parent_account": "Expenses", "amount": 385608395.69, "indent": 1},
					{"label": "Salary", "account": "Salary", "parent_account": "Indirect Expenses", "amount": 232371000.00, "indent": 2},
					{"label": "Office Rent", "account": "Office Rent", "parent_account": "Indirect Expenses", "amount": 63970000.00, "indent": 2},
				],
			},
		)
		rendered = render_normalized_family_response(
			request_id="render-profit-loss",
			artifact_contract=artifact,
		)
		self.assertEqual(rendered.status, "rendered")
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn(
			"The Profit and Loss Statement for Mingalar Mobile Distribution Co., Ltd. for the period 2025-04-01 to 2026-04-16 shows total income of 1,458,275,000.04 MMK, total expenses of 1,372,131,695.50 MMK, and net profit of 172,154,431.22 MMK.",
			answer_text,
		)
		self.assertIn(
			"Key income lines: Sales (1,458,275,000.04 MMK).",
			answer_text,
		)
		self.assertIn(
			"Key expense lines: Cost of Goods Sold (980,896,626.46 MMK), Salary (232,371,000 MMK), Office Rent (63,970,000 MMK).",
			answer_text,
		)
		self.assertNotIn("| Expenses | 1,372,131,695.50 MMK |", answer_text)
		self.assertNotIn("| Stock Expenses | 984,602,148.60 MMK |", answer_text)
		self.assertNotIn("| Indirect Expenses | 385,608,395.69 MMK |", answer_text)
		self.assertNotIn("71.5%", answer_text)
		self.assertNotIn("Business implication", answer_text)

	def test_cash_flow_renderer_keeps_exact_amounts_without_shorthand(self):
		artifact = self._artifact(
			"cash_flow",
			{
				"net_cash_from_operations": -226835151.21,
				"net_cash_from_investing": -325010000,
				"net_cash_from_financing": 178753611.11,
				"net_change_in_cash": -373091540.10,
			},
			{
				"operations": [
					{"label": "Net Change in Accounts Payable", "account": "Net Change in Accounts Payable", "amount": 1082290000.00, "indent": 1},
					{"label": "Net Change in Inventory", "account": "Net Change in Inventory", "amount": -512980000.00, "indent": 1},
					{"label": "Net Change in Accounts Receivable", "account": "Net Change in Accounts Receivable", "amount": -883650000.00, "indent": 1},
				],
				"investing": [
					{"label": "Net Change in Fixed Asset", "account": "Net Change in Fixed Asset", "amount": -325010000.00, "indent": 1},
					{"label": "Cash Flow from Investing", "account": "Cash Flow from Investing", "amount": 0.00, "indent": 0},
				],
				"financing": [
					{"label": "Net Change in Equity", "account": "Net Change in Equity", "amount": 178753611.11, "indent": 1},
					{"label": "Cash Flow from Financing", "account": "Cash Flow from Financing", "amount": 0.00, "indent": 0},
				],
			},
		)
		rendered = render_normalized_family_response(
			request_id="render-cash-flow",
			artifact_contract=artifact,
		)
		self.assertEqual(rendered.status, "rendered")
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("-226,835,151.21 MMK", answer_text)
		self.assertIn("-325,010,000 MMK", answer_text)
		self.assertIn(
			"Key operating cash flow lines: Net Change in Accounts Payable (1,082,290,000 MMK), Net Change in Accounts Receivable (-883,650,000 MMK), Net Change in Inventory (-512,980,000 MMK).",
			answer_text,
		)
		self.assertIn(
			"Key investing cash flow lines: Net Change in Fixed Asset (-325,010,000 MMK).",
			answer_text,
		)
		self.assertNotIn("Cash Flow from Investing", answer_text)
		self.assertNotIn("Cash Flow from Financing", answer_text)
		self.assertNotIn("226.8 MMK", answer_text)
		self.assertNotIn("325.0 MMK", answer_text)
		self.assertNotIn("513.0 MMK", answer_text)
		self.assertNotIn("883.6 MMK", answer_text)

	def test_balance_sheet_renderer_prefers_leaf_lines_in_support_tables(self):
		artifact = self._artifact(
			"balance_sheet",
			{
				"total_asset": 2244439482.03,
				"total_liability": 1588217493.47,
				"total_equity": 582399011.11,
				"provisional_profit_or_loss": 147513777.04,
			},
			{
				"assets": [
					{"label": "Application of Funds (Assets)", "account": "Application of Funds (Assets)", "amount": 2244439482.03, "indent": 0},
					{"label": "Current Assets", "account": "Current Assets", "parent_account": "Application of Funds (Assets)", "amount": 1939364593.64, "indent": 1},
					{"label": "Debtors", "account": "Debtors", "parent_account": "Current Assets", "amount": 1037964500.00, "indent": 2},
					{"label": "Stock In Hand", "account": "Stock In Hand", "parent_account": "Current Assets", "amount": 781367351.38, "indent": 2},
					{"label": "Fixed Assets", "account": "Fixed Assets", "parent_account": "Application of Funds (Assets)", "amount": 305074888.39, "indent": 1},
				],
				"liabilities": [
					{"label": "Source of Funds (Liabilities)", "account": "Source of Funds (Liabilities)", "amount": 1588217493.47, "indent": 0},
					{"label": "Current Liabilities", "account": "Current Liabilities", "parent_account": "Source of Funds (Liabilities)", "amount": 1504066100.00, "indent": 1},
					{"label": "Creditors", "account": "Creditors", "parent_account": "Current Liabilities", "amount": 1280687100.00, "indent": 1},
					{"label": "Accounts Payable", "account": "Accounts Payable", "parent_account": "Creditors", "amount": 1301137100.00, "indent": 2},
					{"label": "Loans (Liabilities)", "account": "Loans (Liabilities)", "parent_account": "Source of Funds (Liabilities)", "amount": 166900000.00, "indent": 1},
				],
				"equity": [
					{"label": "Equity", "account": "Equity", "amount": 582399011.11, "indent": 0},
					{"label": "Opening Balance Equity", "account": "Opening Balance Equity", "parent_account": "Equity", "amount": 444190611.11, "indent": 1},
					{"label": "Capital Stock", "account": "Capital Stock", "parent_account": "Equity", "amount": 180000000.00, "indent": 1},
				],
			},
		)
		rendered = render_normalized_family_response(
			request_id="render-balance-sheet",
			artifact_contract=artifact,
		)
		self.assertEqual(rendered.status, "rendered")
		answer_text = str((rendered.contract.to_payload() if rendered.contract is not None else {}).get("answer_text") or "")
		self.assertIn("Key asset lines: Debtors (1,037,964,500 MMK), Stock In Hand (781,367,351.38 MMK).", answer_text)
		self.assertNotIn("| Application of Funds (Assets) | 2,244,439,482.03 MMK |", answer_text)
		self.assertNotIn("| Current Assets | 1,939,364,593.64 MMK |", answer_text)
		self.assertNotIn("| Source of Funds (Liabilities) | 1,588,217,493.47 MMK |", answer_text)
		self.assertNotIn("| Current Liabilities | 1,504,066,100 MMK |", answer_text)
		self.assertNotIn("| Creditors | 1,280,687,100 MMK |", answer_text)

	def test_financial_statement_prefers_rendered_response_without_analysis(self):
		self.assertTrue(
			_family_narrative_prefers_rendered_response(
				family_id="financial_statement",
				response_policy={
					"analysis_requested": False,
					"implication_allowed": False,
					"recommendation_allowed": False,
				},
			)
		)
		self.assertFalse(
			_family_narrative_prefers_rendered_response(
				family_id="financial_statement",
				response_policy={
					"analysis_requested": True,
					"implication_allowed": True,
					"recommendation_allowed": True,
				},
			)
		)

	def test_financial_statement_artifact_carries_governed_scope_runtime_policy(self):
		outcome = build_normalized_family_artifact(
			request_id="financial-statement-policy",
			compiler_contract={
				"request_id": "financial-statement-policy",
				"selected_report": "Profit and Loss Statement",
			},
			runtime_payload={
				"tool_trace": [
					{
						"tool": "erp_fac-generate_report",
						"detail_obj": {
							"report_name": "Profit and Loss Statement",
							"filters": {
								"company": "Mingalar Mobile Distribution Co., Ltd.",
								"from_date": "2025-04-01",
								"to_date": "2026-04-16",
								"periodicity": "Yearly",
							},
						},
						"output_obj": {
							"result": {
								"columns": [
									{"fieldname": "account"},
									{"fieldname": "total"},
								],
								"data": [
									{"account": "Sales", "currency": "MMK", "total": 1458275000.04},
									{"account": "Cost of Goods Sold", "currency": "MMK", "total": 980896626.46},
								],
							}
						},
					}
				]
			},
			intent_class="financial_statement",
			preferred_family_id="financial_statement",
		)
		self.assertEqual(outcome.status, "adapted")
		dimensions = outcome.artifact_contract.dimensions
		policy = dict(dimensions.get("governed_scope_runtime_policy") or {})
		self.assertEqual(dimensions.get("scope_id"), "profit_and_loss")
		self.assertEqual(dimensions.get("scope_class"), "financial_summary")
		self.assertEqual(policy.get("family_id"), "financial_statement")
		self.assertEqual(policy.get("scope_id"), "profit_and_loss")
		self.assertEqual(policy.get("scope_class"), "financial_summary")
		self.assertEqual(policy.get("compatibility_level"), "full_consumption")


if __name__ == "__main__":
	unittest.main()
