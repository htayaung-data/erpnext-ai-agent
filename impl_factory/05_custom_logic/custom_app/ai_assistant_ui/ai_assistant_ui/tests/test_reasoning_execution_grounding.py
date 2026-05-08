from collections import UserDict
import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat import reasoning_execution as subject


def _activation_contract():
	return {
		"activation_state": "eligible",
		"grounded_context_available": True,
		"grounded_source_request_id": "grounded-risk-1",
		"grounded_source_kind": "report",
		"grounded_source_name": "Accounts Receivable Aging",
		"grounded_family_id": "accounts_receivable",
		"grounded_artifact_type": "normalized_family_artifact",
		"grounded_source_reports": ["Accounts Receivable Aging"],
		"grounded_capability_id": "accounts_receivable_read",
		"grounding_summary": {
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"report_date": "2026-05-05",
			"response_policy_mode": "grounded_analysis",
		},
		"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
		"route_target": "reasoning_lane",
	}


def _activation_contract_accounts_payable():
	contract = _activation_contract()
	contract.update(
		{
			"grounded_source_request_id": "grounded-ap-1",
			"grounded_source_name": "Accounts Payable Aging",
			"grounded_family_id": "accounts_payable",
			"grounded_source_reports": ["Accounts Payable Aging"],
			"grounded_capability_id": "accounts_payable_read",
		}
	)
	return contract


def _activation_contract_profit_and_loss():
	return {
		"activation_state": "eligible",
		"grounded_context_available": True,
		"grounded_source_request_id": "grounded-pnl-1",
		"grounded_source_kind": "report",
		"grounded_source_name": "Profit and Loss Statement",
		"grounded_family_id": "financial_statement",
		"grounded_artifact_type": "normalized_family_artifact",
		"grounded_source_reports": ["Profit and Loss Statement"],
		"grounded_capability_id": "financial_statement_read",
		"grounding_summary": {
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"report_date": "2026-05-05",
			"response_policy_mode": "grounded_analysis",
		},
		"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
		"route_target": "reasoning_lane",
	}


def _activation_contract_cash_flow():
	contract = _activation_contract_profit_and_loss()
	contract.update(
		{
			"grounded_source_request_id": "grounded-cash-flow-1",
			"grounded_source_name": "Cash Flow",
			"grounded_source_reports": ["Cash Flow"],
		}
	)
	return contract


def _activation_contract_cash_flow_recommendation():
	return {
		"activation_state": "eligible",
		"grounded_context_available": True,
		"grounded_source_request_id": "grounded-cash-flow-1",
		"grounded_source_kind": "report",
		"grounded_source_name": "Cash Flow",
		"grounded_family_id": "financial_statement",
		"grounded_artifact_type": "normalized_family_artifact",
		"grounded_source_reports": ["Cash Flow"],
		"grounded_capability_id": "financial_statement_read",
		"grounding_summary": {
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"report_date": "2026-05-05",
			"response_policy_mode": "grounded_analysis",
		},
		"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
		"recommendation_allowed": True,
		"recommendation_policy_basis": ["financial_statement_read", "current_statement_evidence"],
		"route_target": "reasoning_lane",
	}


def _activation_contract_ar_ap_working_capital():
	return {
		"activation_state": "eligible",
		"grounded_context_available": True,
		"grounded_source_request_id": "grounded-ar-ap-health-1",
		"grounded_source_kind": "report",
		"grounded_source_name": "AR / AP Working Capital Health",
		"grounded_family_id": "working_capital",
		"grounded_artifact_type": "normalized_family_artifact",
		"grounded_source_reports": ["Accounts Receivable Aging", "Accounts Payable Aging"],
		"grounded_capability_id": "working_capital_health_read",
		"grounding_summary": {
			"company": "Mingalar Mobile Distribution Co., Ltd.",
			"report_date": "2026-05-06",
			"response_policy_mode": "grounded_analysis",
		},
		"allowed_reasoning_types": ["interpretation", "explanation", "recommendation", "continuation_detail"],
		"route_target": "reasoning_lane",
	}


def _semantic_activation_result():
	return {
		"status": "accepted",
		"intent": {
			"reasoning_type": "interpretation",
			"detail_level": "expanded",
			"presentation_style": "bullet",
			"response_mode": "consultant_interpretation",
			"evidence_policy": "current_result_only",
			"answer_obligation": "explain_grounded_meaning",
		},
	}


def _semantic_activation_result_recommendation():
	return {
		"status": "accepted",
		"intent": {
			"reasoning_type": "recommendation",
			"detail_level": "expanded",
			"presentation_style": "bullet",
			"response_mode": "consultant_recommendation",
			"evidence_policy": "current_result_only",
			"answer_obligation": "recommend_grounded_next_steps",
		},
	}


def _semantic_activation_result_current_result_continuation():
	return {
		"status": "accepted",
		"intent": {
			"reasoning_type": "continuation_detail",
			"detail_level": "expanded",
			"presentation_style": "bullet",
			"response_mode": "consultant_interpretation",
			"evidence_policy": "current_result_only",
			"answer_obligation": "expand_grounded_detail",
		},
	}


def _semantic_activation_result_evidence_expansion_continuation():
	return {
		"status": "accepted",
		"intent": {
			"reasoning_type": "continuation_detail",
			"detail_level": "expanded",
			"presentation_style": "bullet",
			"response_mode": "consultant_detail",
			"evidence_policy": "evidence_expansion_preferred",
			"answer_obligation": "expand_grounded_detail",
		},
	}


def _latest_grounded_turn():
	return {
		"grounded": True,
		"source_name": "Accounts Receivable Aging",
		"returned_schema": ["Customer", "Outstanding", "Total Due", "Overdue"],
		"row_count": 10,
		"table_rows": [
			{
				"Customer": "Capital Telecom (NPT)",
				"Outstanding": "97,309,500",
				"Total Due": "63,654,500",
				"Overdue": "35,274,500",
			},
			{
				"Customer": "35th Street Mobile Wholesale",
				"Outstanding": "84,837,000",
				"Total Due": "82,527,000",
				"Overdue": "58,212,000",
			},
		],
	}


def _latest_grounded_turn_profit_and_loss():
	return {
		"grounded": True,
		"trace_request_id": "grounded-pnl-1",
		"source_name": "Profit and Loss Statement",
		"returned_schema": ["account", "label", "amount", "parent_account", "currency"],
		"row_count": 5,
		"table_rows": [
			{"account": "Income - MMOB", "label": "Income", "amount": "78,654,000", "currency": "MMK"},
			{"account": "Direct Income - MMOB", "label": "Direct Income", "amount": "78,654,000", "currency": "MMK"},
			{"account": "Sales - MMOB", "label": "Sales", "amount": "78,654,000", "currency": "MMK"},
			{
				"account": "Cost of Goods Sold - MMOB",
				"label": "Cost of Goods Sold",
				"amount": "51,764,064.95",
				"parent_account": "Stock Expenses - MMOB",
				"currency": "MMK",
			},
			{"account": "Salary - MMOB", "label": "Salary", "amount": "20,450,000", "currency": "MMK"},
		],
	}


def _latest_assistant_payload():
	return {
		"title": "Accounts Receivable Aging as of 2026-05-05",
		"answer_text": (
			"Outstanding Total 790,855,000 MMK. Total Amount Due 724,170,000 MMK. "
			"Current Bucket 156,941,000 MMK. Overdue Total 567,229,000 MMK. "
			"Overdue Ratio 71.7%. Capital Telecom (NPT) 97,309,500 outstanding, "
			"63,654,500 total due, 35,274,500 overdue. 35th Street Mobile Wholesale "
			"84,837,000 outstanding, 82,527,000 total due, 58,212,000 overdue."
		),
	}


def _latest_assistant_payload_title_only():
	return {
		"title": "Accounts Receivable Aging as of 2026-05-05",
	}


def _latest_assistant_payload_visible_aging_table():
	return {
		"title": "Accounts Receivable Aging as of 2026-05-05",
		"answer_text": (
			"Accounts Receivable Aging as of 2026-05-05\n\n"
			"Summary\n\n"
			"| Metric | Value (MMK) |\n"
			"| --- | --- |\n"
			"| Outstanding Total | 790,855,000 |\n"
			"| Total Amount Due | 724,170,000 |\n"
			"| Current Bucket (0-30) | 156,941,000 |\n"
			"| Overdue Total (31+) | 567,229,000 |\n"
			"| Overdue Ratio | 71.7% |\n\n"
			"Bucket Totals\n\n"
			"| Bucket | Amount (MMK) |\n"
			"| --- | --- |\n"
			"| <0 | 0 |\n"
			"| 0-30 | 156,941,000 |\n"
			"| 31-60 | 156,631,500 |\n"
			"| 61-90 | 195,783,000 |\n"
			"| 91-120 | 91,725,000 |\n"
			"| 121-Above | 123,089,500 |\n\n"
			"Top Customers\n\n"
			"| Customer | Outstanding (MMK) | Total Due (MMK) | Overdue (31+) (MMK) |\n"
			"| --- | --- | --- | --- |\n"
			"| Capital Telecom (NPT) | 97,309,500 | 63,654,500 | 35,274,500 |\n"
			"| 35th Street Mobile Wholesale | 84,837,000 | 82,527,000 | 58,212,000 |\n"
			"| Bayint Naung Wholesale Mobile | 82,687,000 | 67,717,000 | 31,249,000 |\n"
		),
	}


def _latest_assistant_payload_visible_ap_aging_table():
	return {
		"title": "Accounts Payable Aging as of 2026-05-06",
		"answer_text": (
			"Accounts Payable Aging as of 2026-05-06\n\n"
			"Summary\n\n"
			"| Metric | Value (MMK) |\n"
			"| --- | --- |\n"
			"| Outstanding Total | 929,916,600 |\n"
			"| Total Amount Due | 878,396,600 |\n"
			"| Current Bucket (0-30) | 279,575,000 |\n"
			"| Overdue Total (31+) | 598,821,600 |\n"
			"| Overdue Ratio | 64.4% |\n\n"
			"Bucket Totals\n\n"
			"| Bucket | Amount (MMK) |\n"
			"| --- | --- |\n"
			"| 0-30 | 279,575,000 |\n"
			"| 61-90 | 304,835,000 |\n"
			"| 91-120 | 76,837,000 |\n"
			"| 121-Above | 143,017,500 |\n\n"
			"Top Suppliers\n\n"
			"| Supplier | Outstanding (MMK) | Total Due (MMK) | Overdue (31+) (MMK) |\n"
			"| --- | --- | --- | --- |\n"
			"| Myanmar Tech Import Services | 268,298,000 | 250,568,000 | 193,478,000 |\n"
			"| Sunflower Accessories Co. | 228,576,500 | 222,526,500 | 151,301,500 |\n"
			"| Golden Dragon Trading Co. Ltd. | 224,780,600 | 197,040,600 | 118,060,600 |\n"
		),
	}


def _latest_family_artifact_aging_sections():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"family_id": "aging",
		"artifact_type": "normalized_family_artifact",
		"source_reports": ["Accounts Receivable Aging"],
		"sections": {
			"summary": {
				"outstanding_total": 790855000.0,
				"total_amount_due": 724170000.0,
				"current_bucket_0_30": 156941000.0,
				"overdue_total": 567229000.0,
				"overdue_ratio": 0.717,
			},
			"bucket_totals": {
				"0_30": 156941000.0,
				"31_60": 156631500.0,
				"61_90": 195783000.0,
				"91_120": 91725000.0,
				"121_above": 123089500.0,
			},
			"parties": [
				{
					"party": "Capital Telecom (NPT)",
					"outstanding": 97309500.0,
					"total_due": 63654500.0,
					"overdue": 35274500.0,
				},
				{
					"party": "35th Street Mobile Wholesale",
					"outstanding": 84837000.0,
					"total_due": 82527000.0,
					"overdue": 58212000.0,
				},
			],
		},
	}


def _latest_family_artifact_aging_bucket_only_sections():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"family_id": "aging",
		"artifact_type": "normalized_family_artifact",
		"source_reports": ["Accounts Receivable Summary"],
		"sections": {
			"parties": [
				{
					"party": "Capital Telecom (NPT)",
					"outstanding": 97309500.0,
					"total_due": 63654500.0,
					"bucket_0_30": 28380000.0,
					"bucket_31_60": 12776500.0,
					"bucket_61_90": 15480000.0,
					"bucket_91_120": 2974000.0,
					"bucket_121_above": 4044000.0,
				},
				{
					"party": "35th Street Mobile Wholesale",
					"outstanding": 84837000.0,
					"total_due": 82527000.0,
					"bucket_0_30": 24315000.0,
					"bucket_31_60": 12820000.0,
					"bucket_61_90": 8000000.0,
					"bucket_91_120": 12392000.0,
					"bucket_121_above": 25000000.0,
				},
				{
					"party": "Taunggyi City Mobile",
					"outstanding": 37010000.0,
					"total_due": 37010000.0,
					"bucket_0_30": 0.0,
					"bucket_31_60": 8680000.0,
					"bucket_61_90": 22680000.0,
					"bucket_91_120": 5650000.0,
					"bucket_121_above": 0.0,
				},
			],
		},
	}


def _latest_family_artifact_profit_and_loss():
	return {
		"family_id": "financial_statement",
		"artifact_type": "normalized_family_artifact",
		"source_reports": ["Profit and Loss Statement"],
		"capability_id": "financial_statement_read",
		"metrics": {
			"statement_type": "profit_and_loss",
			"total_income": 91480000.0,
			"total_expense": 102779942.84,
			"net_profit": -11299942.84,
		},
		"sections": {
			"summary": [
				{"metric": "Total Income", "amount": 91480000.0},
				{"metric": "Total Expense", "amount": 102779942.84},
				{"metric": "Net Profit", "amount": -11299942.84},
			],
			"income": [
				{"account": "Income - MMOB", "label": "Income", "amount": 91480000.0, "currency": "MMK", "indent": 0},
				{"account": "Sales - MMOB", "label": "Sales", "amount": 91480000.0, "currency": "MMK", "parent_account": "Income - MMOB", "indent": 1},
			],
			"expense": [
				{"account": "Expenses - MMOB", "label": "Expenses", "amount": 102779942.84, "currency": "MMK", "indent": 0},
				{"account": "Stock Expenses - MMOB", "label": "Stock Expenses", "amount": 71679942.84, "currency": "MMK", "parent_account": "Expenses - MMOB", "indent": 1},
				{"account": "Cost of Goods Sold - MMOB", "label": "Cost of Goods Sold", "amount": 65245820.70, "currency": "MMK", "parent_account": "Stock Expenses - MMOB", "indent": 2},
				{"account": "Salary - MMOB", "label": "Salary", "amount": 20450000.0, "currency": "MMK", "parent_account": "Indirect Expenses - MMOB", "indent": 2},
				{"account": "Stock Adjustment - MMOB", "label": "Stock Adjustment", "amount": 6434122.14, "currency": "MMK", "parent_account": "Stock Expenses - MMOB", "indent": 2},
			],
			"lines": [
				{"account": "Income - MMOB", "label": "Income", "amount": 91480000.0, "currency": "MMK"},
				{"account": "Cost of Goods Sold - MMOB", "label": "Cost of Goods Sold", "amount": 65245820.70, "currency": "MMK"},
			],
		},
	}


def _latest_family_artifact_cash_flow():
	return {
		"family_id": "financial_statement",
		"artifact_type": "normalized_family_artifact",
		"source_reports": ["Cash Flow"],
		"capability_id": "financial_statement_read",
		"metrics": {
			"statement_type": "cash_flow",
			"net_cash_from_operations": 60548100.0,
			"net_cash_from_investing": 0.0,
			"net_cash_from_financing": -76539100.0,
			"net_change_in_cash": -15991000.0,
		},
		"sections": {
			"summary": [
				{"metric": "Net Cash from Operations", "amount": 60548100.0},
				{"metric": "Net Cash from Investing", "amount": 0.0},
				{"metric": "Net Cash from Financing", "amount": -76539100.0},
				{"metric": "Net Change in Cash", "amount": -15991000.0},
			],
			"operations": [
				{"line": "Net Change in Inventory", "amount": 60552287.09, "currency": "MMK"},
				{"line": "Net Change in Accounts Receivable", "amount": -45995000.0, "currency": "MMK"},
				{"line": "Net Change in Payroll and Accrued Expenses", "amount": 20450000.0, "currency": "MMK"},
			],
			"financing": [
				{"line": "Net Change in Equity", "amount": -76539100.0, "currency": "MMK"},
			],
		},
	}


def _latest_family_artifact_balance_sheet():
	return {
		"family_id": "financial_statement",
		"artifact_type": "normalized_family_artifact",
		"source_reports": ["Balance Sheet"],
		"capability_id": "financial_statement_read",
		"metrics": {
			"statement_type": "balance_sheet",
			"total_assets": 1845564663.71,
			"total_liabilities": 1290195600.0,
			"total_equity": 550818250.80,
		},
		"sections": {
			"summary": [
				{"metric": "Total Assets", "amount": 1845564663.71},
				{"metric": "Total Liabilities", "amount": 1290195600.0},
				{"metric": "Total Equity", "amount": 550818250.80},
			],
			"assets": [
				{"account": "Application of Funds (Assets) - MMOB", "label": "Application of Funds (Assets)", "amount": 1845564663.71, "currency": "MMK", "indent": 0},
				{"account": "Current Assets - MMOB", "label": "Current Assets", "amount": 1536026886.43, "currency": "MMK", "parent_account": "Application of Funds (Assets) - MMOB", "indent": 1},
				{"account": "Debtors - MMOB", "label": "Debtors", "amount": 790855000.0, "currency": "MMK", "parent_account": "Current Assets - MMOB", "indent": 2},
				{"account": "Stock In Hand - MMOB", "label": "Stock In Hand", "amount": 675171886.43, "currency": "MMK", "parent_account": "Current Assets - MMOB", "indent": 2},
				{"account": "Capital Equipment - MMOB", "label": "Capital Equipment", "amount": 290000000.0, "currency": "MMK", "parent_account": "Application of Funds (Assets) - MMOB", "indent": 1},
			],
			"liabilities": [
				{"account": "Source of Funds (Liabilities) - MMOB", "label": "Source of Funds (Liabilities)", "amount": 1290195600.0, "currency": "MMK", "indent": 0},
				{"account": "Current Liabilities - MMOB", "label": "Current Liabilities", "amount": 1200195600.0, "currency": "MMK", "parent_account": "Source of Funds (Liabilities) - MMOB", "indent": 1},
				{"account": "Accounts Payable - MMOB", "label": "Accounts Payable", "amount": 947266600.0, "currency": "MMK", "parent_account": "Current Liabilities - MMOB", "indent": 2},
				{"account": "Creditors - MMOB", "label": "Creditors", "amount": 906366600.0, "currency": "MMK", "parent_account": "Accounts Payable - MMOB", "indent": 3},
				{"account": "Bank Overdraft Account - MMOB", "label": "Bank Overdraft Account", "amount": 118000000.0, "currency": "MMK", "parent_account": "Loans (Liabilities) - MMOB", "indent": 2},
				{"account": "Unsecured Loans - MMOB", "label": "Unsecured Loans", "amount": 98900000.0, "currency": "MMK", "parent_account": "Loans (Liabilities) - MMOB", "indent": 2},
			],
			"equity": [
				{"account": "Opening Balance Equity - MMOB", "label": "Opening Balance Equity", "amount": 415437000.0, "currency": "MMK"},
			],
		},
	}


def _latest_family_artifact_ar_ap_working_capital():
	return {
		"family_id": "working_capital",
		"artifact_type": "normalized_family_artifact",
		"source_reports": ["Accounts Receivable Aging", "Accounts Payable Aging"],
		"capability_id": "working_capital_health_read",
		"sections": {
			"summary": [
				{"metric": "Accounts Receivable Outstanding", "value": 803681000.0},
				{"metric": "Accounts Payable Outstanding", "value": 929916600.0},
				{"metric": "Net AR minus AP", "value": -126235600.0},
				{"metric": "AR Overdue Ratio", "value": 72.1},
				{"metric": "AP Overdue Ratio", "value": 64.4},
			],
			"parties": [
				{"party": "Capital Telecom (NPT)", "outstanding": 97309500.0, "overdue": 35274500.0},
				{"party": "Myanmar Tech Import Services", "outstanding": 268298000.0, "overdue": 193478000.0},
			],
		},
	}


def _latest_assistant_payload_profit_and_loss_title_only():
	return {
		"title": "Profit and Loss Statement (2026-04-01 to 2026-05-05)",
	}


def _latest_assistant_payload_cash_flow_title_only():
	return {
		"title": "Cash Flow (2026-04-01 to 2026-05-05)",
	}


def _latest_assistant_payload_balance_sheet_title_only():
	return {
		"title": "Balance Sheet (2026-04-01 to 2026-05-05)",
	}


def _latest_assistant_payload_ar_ap_working_capital_title_only():
	return {
		"title": "AR/AP Working Capital Health as of 2026-05-06",
	}


class ReasoningExecutionGroundingTests(unittest.TestCase):
	def test_reasoning_context_exposes_visible_numeric_evidence_catalog(self):
		context = subject._build_reasoning_context(
			activation_contract=_activation_contract(),
			semantic_activation_result=_semantic_activation_result(),
			latest_grounded_turn=_latest_grounded_turn(),
			latest_family_artifact={},
			latest_assistant_payload=_latest_assistant_payload(),
			presentation_preferences={"bullet": True},
		)

		catalog = context.get("evidence_catalog") or {}
		self.assertIn("790855000", catalog.get("visible_number_tokens") or [])
		self.assertIn("790.86", catalog.get("visible_number_tokens") or [])
		self.assertIn("71.7", catalog.get("visible_number_tokens") or [])
		self.assertIn("97309500", catalog.get("visible_number_tokens") or [])
		self.assertEqual(catalog.get("numeric_grounding_mode"), "visible_result_first")
		self.assertEqual(context.get("consultant_response_mode"), "consultant_interpretation")
		self.assertEqual(context.get("evidence_policy"), "current_result_only")
		self.assertEqual(context.get("answer_obligation"), "explain_grounded_meaning")
		self.assertEqual(context.get("answer_goal"), "explain")
		self.assertEqual(context.get("evidence_depth"), "current_result_only")
		self.assertEqual(context.get("business_role"), "business_consultant")
		self.assertEqual(context.get("target_reference"), "current_result")
		self.assertEqual(context.get("risk_level"), "factual_only")

	def test_reasoning_context_uses_latest_visible_assistant_message_as_evidence(self):
		context = subject._build_reasoning_context(
			activation_contract=_activation_contract(),
			semantic_activation_result=_semantic_activation_result(),
			latest_grounded_turn=_latest_grounded_turn(),
			latest_family_artifact={},
			latest_assistant_payload={},
			recent_messages=[
				{"role": "user", "content": "show customer risk"},
				{
					"role": "assistant",
					"content": (
						"Accounts Receivable Aging. Outstanding Total 790,855,000 MMK. "
						"Overdue Total 567,229,000 MMK. Overdue Ratio 71.7%."
					),
				},
			],
			presentation_preferences={"bullet": True},
		)

		catalog = context.get("evidence_catalog") or {}
		self.assertIn("790855000", catalog.get("visible_number_tokens") or [])
		self.assertIn("567229000", catalog.get("visible_number_tokens") or [])
		self.assertIn("71.7", catalog.get("visible_number_tokens") or [])

	def test_runtime_output_with_unsupported_number_uses_visible_evidence_fallback(self):
		def fake_runtime(**_kwargs):
			return {
				"payload": {
					"answer_text": "- The top accounts exceed 400 MMK Million, so collection pressure is severe.",
					"supported_claims": [
						{
							"claim": "The top accounts exceed 400 MMK Million.",
							"support": "The current ERP result shows that total.",
						}
					],
					"recommendations": [],
					"speculation_flags": [],
					"confidence": 0.9,
					"reason": "Grounded interpretation.",
				},
				"agent_meta": {},
			}

		with patch.object(subject, "call_qwen_runtime_reasoning_render", side_effect=fake_runtime) as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-grounding-1",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="what does this mean? discuss with bullet points",
				recent_messages=[],
				activation_contract=_activation_contract(),
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact={},
				latest_assistant_payload=_latest_assistant_payload_visible_aging_table(),
				presentation_preferences={"bullet": True},
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_consultant_interpretation"))
		self.assertIn("Accounts Receivable Aging as of 2026-05-05", result.answer_text)
		self.assertIn("Key findings", result.answer_text)
		self.assertIn("Collection pressure is structural", result.answer_text)
		self.assertIn("overdue balances", result.answer_text)
		self.assertIn("Deep overdue exposure", result.answer_text)
		self.assertIn("top three listed customers", result.answer_text)
		self.assertIn("overdue intensity", result.answer_text)
		self.assertIn("61-90", result.answer_text)
		self.assertIn("71.7%", result.answer_text)
		self.assertIn("Consultant takeaway", result.answer_text)
		self.assertIn("Recommended next step", result.answer_text)
		self.assertIn("Would you like me to compare the listed customers", result.answer_text)
		self.assertIn("MMK million", result.answer_text)
		self.assertNotIn("400", result.answer_text)
		self.assertNotIn("supporting ERP detail view", result.answer_text)

	def test_visible_consultant_next_step_falls_back_to_executable_party_prompt_without_capability_slot(self):
		def fake_runtime(**_kwargs):
			return {
				"payload": {
					"answer_text": "- Unsupported answer mentions 400 MMK Million.",
					"supported_claims": [
						{
							"claim": "Unsupported answer mentions 400 MMK Million.",
							"support": "Unsupported test value.",
						}
					],
					"recommendations": [],
					"speculation_flags": [],
					"confidence": 0.8,
					"reason": "Synthetic unsupported-number payload for fallback testing.",
				},
				"agent_meta": {},
			}

		activation_contract = _activation_contract()
		activation_contract.pop("grounded_capability_id", None)
		with patch.object(subject, "call_qwen_runtime_reasoning_render", side_effect=fake_runtime) as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-grounding-no-capability-next-step",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="what does this mean? discuss with bullet points",
				recent_messages=[],
				activation_contract=activation_contract,
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact={},
				latest_assistant_payload=_latest_assistant_payload_visible_aging_table(),
				presentation_preferences={"bullet": True},
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_consultant_interpretation"))
		self.assertIn("Recommended next step", result.answer_text)
		self.assertIn("Would you like me to compare the listed customers", result.answer_text)
		self.assertEqual(
			(result.reasoning_contract.get("offered_next_actions") or [{}])[0].get("action_id"),
			"compare_listed_parties_by_overdue_and_intensity",
		)
		self.assertEqual(
			(result.reasoning_contract.get("offered_next_actions") or [{}])[0].get("entity_scope"),
			"customers",
		)
		self.assertNotIn("supporting ERP detail view", result.answer_text)

	def test_financial_statement_interpretation_uses_statement_metrics_before_generic_table(self):
		def fake_runtime(**_kwargs):
			return {
				"payload": {
					"answer_text": "- The current result implies 400 MMK Million of unsupported pressure.",
					"supported_claims": [
						{
							"claim": "The current result implies 400 MMK Million of unsupported pressure.",
							"support": "Unsupported test value.",
						}
					],
					"recommendations": [],
					"speculation_flags": [],
					"confidence": 0.8,
					"reason": "Synthetic unsupported-number payload for fallback testing.",
				},
				"agent_meta": {},
			}

		with patch.object(subject, "call_qwen_runtime_reasoning_render", side_effect=fake_runtime) as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-financial-statement-consultant-pnl",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="what does this mean? discuss as business consultant",
				recent_messages=[],
				activation_contract=_activation_contract_profit_and_loss(),
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn=_latest_grounded_turn_profit_and_loss(),
				latest_family_artifact=_latest_family_artifact_profit_and_loss(),
				latest_assistant_payload=_latest_assistant_payload_profit_and_loss_title_only(),
				presentation_preferences={"bullet": True},
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_consultant_interpretation"))
		self.assertIn("Executive diagnosis", result.answer_text)
		self.assertIn("Expenses exceed income", result.answer_text)
		self.assertIn("Expense burden", result.answer_text)
		self.assertIn("Net margin", result.answer_text)
		self.assertIn("Cost of Goods Sold", result.answer_text)
		self.assertIn("Consultant takeaway", result.answer_text)
		self.assertIn("Management priorities", result.answer_text)
		self.assertIn("profit-recovery target", result.answer_text)
		self.assertIn("Start with Cost of Goods Sold", result.answer_text)
		self.assertNotIn("400", result.answer_text)
		self.assertNotIn("Bucket Totals", result.answer_text)
		self.assertNotIn("largest visible expense driver is Expenses", result.answer_text)
		self.assertNotIn("Indent", result.answer_text)

	def test_cash_flow_interpretation_uses_cash_flow_metrics(self):
		context = subject._build_reasoning_context(
			activation_contract=_activation_contract_profit_and_loss(),
			semantic_activation_result=_semantic_activation_result(),
			latest_grounded_turn=_latest_grounded_turn_profit_and_loss(),
			latest_family_artifact=_latest_family_artifact_cash_flow(),
			latest_assistant_payload=_latest_assistant_payload_cash_flow_title_only(),
			presentation_preferences={"bullet": True},
		)

		payload = subject._build_visible_evidence_fallback_payload(
			reasoning_type="interpretation",
			grounding_context=context,
			latest_grounded_turn=_latest_grounded_turn_profit_and_loss(),
			presentation_preferences={"bullet": True},
		)

		self.assertIn("Operations generated positive cash", payload.get("answer_text") or "")
		self.assertIn("Financing cash flow", payload.get("answer_text") or "")
		self.assertIn("Investing cash flow is zero", payload.get("answer_text") or "")
		self.assertIn("largest visible operating movement", payload.get("answer_text") or "")
		self.assertIn("Executive diagnosis", payload.get("answer_text") or "")
		self.assertIn("Management priorities", payload.get("answer_text") or "")
		self.assertIn("Protect the positive operating cash base", payload.get("answer_text") or "")
		self.assertIn("Treat Net Change in Accounts Receivable as a working-capital lever", payload.get("answer_text") or "")
		self.assertNotIn("timing distribution", payload.get("answer_text") or "")

	def test_financial_statement_consultant_interpretation_uses_deterministic_renderer_before_runtime(self):
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-cash-flow-consultant-interpretation",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="what does this mean? Discuss as Business consultant",
				recent_messages=[],
				activation_contract=_activation_contract_cash_flow(),
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn=_latest_grounded_turn_profit_and_loss(),
				latest_family_artifact=_latest_family_artifact_cash_flow(),
				latest_assistant_payload=_latest_assistant_payload_cash_flow_title_only(),
				presentation_preferences={"bullet": True},
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_consultant_interpretation"))
		self.assertIn("Executive diagnosis", result.answer_text)
		self.assertIn("Operations generated positive cash", result.answer_text)
		self.assertIn("Management priorities", result.answer_text)
		self.assertIn("Net Change in Accounts Receivable", result.answer_text)
		self.assertNotIn("stay afloat", result.answer_text)

	def test_cash_flow_recommendation_uses_deterministic_financial_statement_consultant(self):
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-cash-flow-recommendation",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="evaluate the cash flow and recommend what to do",
				recent_messages=[],
				activation_contract=_activation_contract_cash_flow_recommendation(),
				semantic_activation_result=_semantic_activation_result_recommendation(),
				latest_grounded_turn=_latest_grounded_turn_profit_and_loss(),
				latest_family_artifact=_latest_family_artifact_cash_flow(),
				latest_assistant_payload=_latest_assistant_payload_cash_flow_title_only(),
				presentation_preferences={"bullet": True},
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_financial_statement_recommendation"))
		self.assertIn("Recommended next steps", result.answer_text)
		self.assertIn("Executive diagnosis", result.answer_text)
		self.assertIn("Management priorities", result.answer_text)
		self.assertIn("Separate operating cash", result.answer_text)
		self.assertIn("receivable movement", result.answer_text)
		self.assertIn("financing outflow", result.answer_text)
		self.assertTrue(result.reasoning_contract.get("recommendations"))
		self.assertNotIn("I stopped rather than guess", result.answer_text)

	def test_balance_sheet_interpretation_uses_balance_sheet_metrics(self):
		context = subject._build_reasoning_context(
			activation_contract=_activation_contract_profit_and_loss(),
			semantic_activation_result=_semantic_activation_result(),
			latest_grounded_turn=_latest_grounded_turn_profit_and_loss(),
			latest_family_artifact=_latest_family_artifact_balance_sheet(),
			latest_assistant_payload=_latest_assistant_payload_balance_sheet_title_only(),
			presentation_preferences={"bullet": True},
		)

		payload = subject._build_visible_evidence_fallback_payload(
			reasoning_type="interpretation",
			grounding_context=context,
			latest_grounded_turn=_latest_grounded_turn_profit_and_loss(),
			presentation_preferences={"bullet": True},
		)

		self.assertIn("Liabilities are", payload.get("answer_text") or "")
		self.assertIn("Equity funds", payload.get("answer_text") or "")
		self.assertIn("largest visible asset line", payload.get("answer_text") or "")
		self.assertIn("largest visible liability line", payload.get("answer_text") or "")
		self.assertIn("Executive diagnosis", payload.get("answer_text") or "")
		self.assertIn("Management priorities", payload.get("answer_text") or "")
		self.assertIn("liability-heavy", payload.get("answer_text") or "")
		self.assertIn("Manage leverage before growth", payload.get("answer_text") or "")
		self.assertIn("Debtors", payload.get("answer_text") or "")
		self.assertIn("Creditors", payload.get("answer_text") or "")
		self.assertNotIn("Application of Funds", payload.get("answer_text") or "")
		self.assertNotIn("Source of Funds", payload.get("answer_text") or "")
		self.assertNotIn("timing distribution", payload.get("answer_text") or "")

	def test_general_interpretation_does_not_reuse_prior_row_focus(self):
		def fake_runtime(**_kwargs):
			return {
				"payload": {
					"answer_text": "- This result implies 400 MMK Million of unrelated exposure.",
					"supported_claims": [
						{
							"claim": "This result implies 400 MMK Million of unrelated exposure.",
							"support": "The current ERP result shows that amount.",
						}
					],
					"recommendations": [],
					"speculation_flags": [],
					"confidence": 0.8,
					"reason": "Synthetic unsupported-number payload for fallback testing.",
				},
				"agent_meta": {},
			}

		with patch.object(subject, "call_qwen_runtime_reasoning_render", side_effect=fake_runtime):
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-general-interpretation-no-prior-row-focus",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="what does this mean?",
				recent_messages=[],
				activation_contract=_activation_contract(),
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact=_latest_family_artifact_aging_sections(),
				latest_assistant_payload=_latest_assistant_payload_visible_aging_table(),
				presentation_preferences={"bullet": True},
				prior_answer_text="Mandalay Accessories Wholesale had a prior line-item answer.",
			)

		self.assertEqual(result.status, "answered")
		self.assertIn("business reading", result.answer_text)
		self.assertIn("Executive diagnosis", result.answer_text)
		self.assertIn("Key findings", result.answer_text)
		self.assertIn("Management priorities", result.answer_text)
		self.assertIn("Collection pressure is structural", result.answer_text)
		self.assertIn("overdue balances", result.answer_text)
		self.assertIn("cash-timing control problem", result.answer_text)
		self.assertIn("Run the overdue balance as a weekly operating control", result.answer_text)
		self.assertNotIn("The follow-up is about Mandalay Accessories Wholesale", result.answer_text)
		self.assertNotIn("supporting ERP detail view", result.answer_text)

	def test_accounts_payable_aging_consultant_uses_supplier_payment_language(self):
		context = subject._build_reasoning_context(
			activation_contract=_activation_contract_accounts_payable(),
			semantic_activation_result=_semantic_activation_result(),
			latest_grounded_turn={"grounded": True, "source_name": "Accounts Payable Aging", "table_rows": []},
			latest_family_artifact={},
			latest_assistant_payload=_latest_assistant_payload_visible_ap_aging_table(),
			presentation_preferences={"bullet": True},
		)

		payload = subject._build_visible_evidence_fallback_payload(
			reasoning_type="interpretation",
			grounding_context=context,
			latest_grounded_turn={"grounded": True, "source_name": "Accounts Payable Aging", "table_rows": []},
			presentation_preferences={"bullet": True},
		)

		answer = payload.get("answer_text") or ""
		self.assertIn("Supplier payment pressure is structural", answer)
		self.assertIn("payables are overdue", answer)
		self.assertIn("supplier-payment timing and concentration problem", answer)
		self.assertIn("settlement intensity", answer)
		self.assertIn("Would you like me to compare the listed suppliers", answer)
		self.assertNotIn("Collection pressure is structural", answer)
		self.assertNotIn("receivables are overdue", answer)
		self.assertNotIn("listed parties by overdue", answer)

	def test_runtime_output_with_unsupported_number_uses_grounded_rows_when_visible_text_is_sparse(self):
		def fake_runtime(**_kwargs):
			return {
				"payload": {
					"answer_text": "- The result shows 584.1 MMK Million of unsupported concentration.",
					"supported_claims": [
						{
							"claim": "Unsupported concentration is 584.1 MMK Million.",
							"support": "Unsupported derived number.",
						}
					],
					"recommendations": [],
					"speculation_flags": [],
					"confidence": 0.9,
					"reason": "Grounded interpretation.",
				},
				"agent_meta": {},
			}

		with patch.object(subject, "call_qwen_runtime_reasoning_render", side_effect=fake_runtime):
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-grounding-sparse-visible",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="what does this mean?",
				recent_messages=[
					{"role": "assistant", "content": "Accounts Receivable Aging"}
				],
				activation_contract=_activation_contract(),
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact={},
				latest_assistant_payload=_latest_assistant_payload_title_only(),
				presentation_preferences={"bullet": True},
			)

		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("visible_evidence_fallback"))
		self.assertIn("35th Street Mobile Wholesale", result.answer_text)
		self.assertIn("84,837,000", result.answer_text)
		self.assertNotIn("584.1", result.answer_text)

	def test_runtime_output_with_visible_numbers_is_accepted(self):
		def fake_runtime(**_kwargs):
			return {
				"payload": {
					"answer_text": (
						"- Receivables are under pressure because 567,229,000 MMK is overdue, "
						"which is 71.7% of the receivable base.\n"
						"- Capital Telecom (NPT) is the largest visible exposure at 97.31 MMK Million."
					),
					"supported_claims": [
						{
							"claim": "Overdue receivables are material.",
							"support": "Overdue Total is 567,229,000 MMK and Overdue Ratio is 71.7%.",
						},
						{
							"claim": "The largest visible customer exposure is Capital Telecom (NPT).",
							"support": "Its outstanding amount is 97.31 MMK Million.",
						},
					],
					"recommendations": [],
					"speculation_flags": [],
					"confidence": 0.91,
					"reason": "All numeric claims are present in the current ERP result.",
				},
				"agent_meta": {"engine": "test"},
			}

		with patch.object(subject, "call_qwen_runtime_reasoning_render", side_effect=fake_runtime):
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-grounding-2",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="what does this mean? discuss with bullet points",
				recent_messages=[],
				activation_contract=_activation_contract(),
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact={},
				latest_assistant_payload=_latest_assistant_payload(),
				presentation_preferences={"bullet": True},
			)

		self.assertEqual(result.status, "answered")
		self.assertIn("567,229,000", result.answer_text)
		self.assertIn("97.31 MMK Million", result.answer_text)
		self.assertNotIn("182.15 MMK Million", result.answer_text)

	def test_accepted_runtime_answer_gets_contextual_next_step_when_visible_table_supports_it(self):
		def fake_runtime(**_kwargs):
			return {
				"payload": {
					"answer_text": (
						"- Receivables are under pressure because 567,229,000 MMK is overdue, "
						"which is 71.7% of the receivable base."
					),
					"supported_claims": [
						{
							"claim": "Overdue receivables are material.",
							"support": "Overdue Total is 567,229,000 MMK and Overdue Ratio is 71.7%.",
						}
					],
					"recommendations": [],
					"speculation_flags": [],
					"confidence": 0.91,
					"reason": "All numeric claims are present in the current ERP result.",
				},
				"agent_meta": {"engine": "test"},
			}

		with patch.object(subject, "call_qwen_runtime_reasoning_render", side_effect=fake_runtime):
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-grounding-accepted-runtime-next-step",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="what does this mean? discuss with bullet points",
				recent_messages=[],
				activation_contract=_activation_contract(),
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact={},
				latest_assistant_payload=_latest_assistant_payload_visible_aging_table(),
				presentation_preferences={"bullet": True},
			)

		self.assertEqual(result.status, "answered")
		self.assertFalse(result.agent_meta.get("visible_evidence_fallback"))
		self.assertIn("Recommended next step", result.answer_text)
		self.assertIn("Would you like me to compare the listed customers", result.answer_text)
		self.assertEqual(
			(result.reasoning_contract.get("offered_next_actions") or [{}])[0].get("action_id"),
			"compare_listed_parties_by_overdue_and_intensity",
		)
		self.assertNotIn("supporting ERP detail view", result.answer_text)

	def test_continuation_executes_prior_offered_party_comparison_action(self):
		prior_contract = {
			"type": "qwen_erp_business_reasoning_contract",
			"reasoning_type": "interpretation",
			"grounding_source_request_id": "grounded-risk-1",
			"grounding_source_kind": "report",
			"grounding_family_id": "accounts_receivable",
			"grounding_artifact_type": "normalized_family_artifact",
			"grounding_source_reports": ["Accounts Receivable Aging"],
			"grounding_sufficient": True,
			"grounding_gaps": [],
			"allowed_to_answer": True,
			"supported_claims": [],
			"recommendations": [],
			"offered_next_actions": [
				{
					"action_id": "compare_listed_parties_by_overdue_and_intensity",
					"execution_mode": "current_governed_artifact",
					"comparison_metrics": ["overdue_amount", "overdue_intensity"],
				}
			],
			"speculation_flags": [],
		}
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-execute-prior-party-next-action",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="yes please",
				recent_messages=[],
				activation_contract=_activation_contract(),
				semantic_activation_result=_semantic_activation_result_current_result_continuation(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact=_latest_family_artifact_aging_sections(),
				latest_assistant_payload=_latest_assistant_payload_visible_aging_table(),
				presentation_preferences={"bullet": True},
				prior_reasoning_contract=prior_contract,
				prior_answer_text="Would you like me to compare the listed parties by overdue amount and overdue intensity next?",
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("executed_prior_offered_next_action"))
		self.assertIn("Comparison table", result.answer_text)
		self.assertIn("35th Street Mobile Wholesale", result.answer_text)
		self.assertIn("Capital Telecom (NPT)", result.answer_text)
		self.assertIn("overdue intensity", result.answer_text)
		self.assertNotIn("Recommended next step", result.answer_text)
		self.assertFalse(result.reasoning_contract.get("offered_next_actions"))

	def test_continuation_derives_party_comparison_from_aging_bucket_rows(self):
		prior_contract = {
			"type": "qwen_erp_business_reasoning_contract",
			"reasoning_type": "interpretation",
			"grounding_source_request_id": "grounded-risk-1",
			"grounding_source_kind": "report",
			"grounding_family_id": "accounts_receivable",
			"grounding_artifact_type": "normalized_family_artifact",
			"grounding_source_reports": ["Accounts Receivable Summary"],
			"grounding_sufficient": True,
			"grounding_gaps": [],
			"allowed_to_answer": True,
			"supported_claims": [],
			"recommendations": [],
			"offered_next_actions": [
				{
					"action_id": "compare_listed_parties_by_overdue_and_intensity",
					"execution_mode": "current_governed_artifact",
					"comparison_metrics": ["overdue_amount", "overdue_intensity"],
				}
			],
			"speculation_flags": [],
		}
		activation_contract = _activation_contract()
		activation_contract["grounded_source_name"] = "Accounts Receivable Summary"
		activation_contract["grounded_source_reports"] = ["Accounts Receivable Summary"]
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-execute-prior-party-next-action-buckets",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="yes please",
				recent_messages=[],
				activation_contract=activation_contract,
				semantic_activation_result=_semantic_activation_result_current_result_continuation(),
				latest_grounded_turn={
					"grounded": True,
					"trace_request_id": "grounded-risk-1",
					"source_name": "Accounts Receivable Summary",
					"table_rows": [],
				},
				latest_family_artifact=_latest_family_artifact_aging_bucket_only_sections(),
				latest_assistant_payload=_latest_assistant_payload_visible_aging_table(),
				presentation_preferences={"bullet": True},
				prior_reasoning_contract=prior_contract,
				prior_answer_text="Would you like me to compare the listed parties by overdue amount and overdue intensity next?",
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("executed_prior_offered_next_action"))
		self.assertIn("Comparison table", result.answer_text)
		self.assertIn("35th Street Mobile Wholesale", result.answer_text)
		self.assertIn("Taunggyi City Mobile", result.answer_text)
		self.assertIn("58.2 MMK million", result.answer_text)
		self.assertFalse(result.reasoning_contract.get("offered_next_actions"))

	def test_continuation_executes_prior_offered_working_capital_side_by_side_action(self):
		prior_contract = {
			"type": "qwen_erp_business_reasoning_contract",
			"reasoning_type": "interpretation",
			"grounding_source_request_id": "grounded-ar-ap-health-1",
			"grounding_source_kind": "report",
			"grounding_family_id": "working_capital",
			"grounding_artifact_type": "normalized_family_artifact",
			"grounding_source_reports": ["Accounts Receivable Aging", "Accounts Payable Aging"],
			"grounding_sufficient": True,
			"grounding_gaps": [],
			"allowed_to_answer": True,
			"supported_claims": [],
			"recommendations": [],
			"offered_next_actions": [
				{
					"action_id": "compare_ar_ap_pressure_side_by_side",
					"execution_mode": "current_governed_artifact",
				}
			],
			"speculation_flags": [],
		}
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-execute-prior-ar-ap-next-action",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="yes please",
				recent_messages=[],
				activation_contract=_activation_contract_ar_ap_working_capital(),
				semantic_activation_result=_semantic_activation_result_current_result_continuation(),
				latest_grounded_turn={"grounded": True, "source_name": "AR / AP Working Capital Health", "table_rows": []},
				latest_family_artifact=_latest_family_artifact_ar_ap_working_capital(),
				latest_assistant_payload=_latest_assistant_payload_ar_ap_working_capital_title_only(),
				presentation_preferences={"bullet": True},
				prior_reasoning_contract=prior_contract,
				prior_answer_text="Would you like me to compare the customer collection pressure and supplier payment pressure side by side next?",
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("executed_prior_offered_next_action"))
		self.assertIn("side-by-side pressure comparison", result.answer_text)
		self.assertIn("Receivables", result.answer_text)
		self.assertIn("Payables", result.answer_text)
		self.assertIn("Comparison table", result.answer_text)

	def test_current_result_continuation_uses_deterministic_renderer_without_runtime(self):
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-current-result-continuation",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="make the prior explanation clearer",
				recent_messages=[],
				activation_contract=_activation_contract(),
				semantic_activation_result=_semantic_activation_result_current_result_continuation(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact=_latest_family_artifact_aging_sections(),
				latest_assistant_payload=_latest_assistant_payload_title_only(),
				presentation_preferences={"bullet": True},
				prior_reasoning_contract={
					"type": "qwen_erp_business_reasoning_contract",
					"reasoning_type": "interpretation",
					"allowed_to_answer": True,
					"grounding_sufficient": True,
					"grounding_source_request_id": "grounded-risk-1",
					"grounding_family_id": "accounts_receivable",
					"grounding_source_reports": ["Accounts Receivable Aging"],
				},
				prior_answer_text="Prior grounded consultant answer.",
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_current_result_continuation"))
		self.assertIn("Accounts Receivable Aging as of 2026-05-05", result.answer_text)
		self.assertIn("Key findings", result.answer_text)
		self.assertIn("heaviest timing bucket", result.answer_text)
		self.assertIn("61-90", result.answer_text)
		self.assertIn("Consultant takeaway", result.answer_text)
		self.assertIn("Recommended next step", result.answer_text)
		self.assertIn("Would you like me to compare the listed customers", result.answer_text)

	def test_current_result_continuation_accepts_mapping_like_prior_contract(self):
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-current-result-continuation-mapping",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="make the prior explanation clearer",
				recent_messages=[],
				activation_contract=_activation_contract(),
				semantic_activation_result=_semantic_activation_result_current_result_continuation(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact=_latest_family_artifact_aging_sections(),
				latest_assistant_payload=_latest_assistant_payload_title_only(),
				presentation_preferences={"bullet": True},
				prior_reasoning_contract=UserDict(
					{
						"type": "qwen_erp_business_reasoning_contract",
						"reasoning_type": "interpretation",
						"allowed_to_answer": True,
						"grounding_sufficient": True,
						"grounding_source_request_id": "grounded-risk-1",
						"grounding_family_id": "accounts_receivable",
						"grounding_source_reports": ["Accounts Receivable Aging"],
					}
				),
				prior_answer_text="Prior grounded consultant answer.",
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_current_result_continuation"))

	def test_current_result_continuation_uses_party_artifact_when_summary_sections_are_absent(self):
		artifact = _latest_family_artifact_aging_sections()
		artifact["sections"] = {
			"parties": [
				{
					"party": "Capital Telecom (NPT)",
					"outstanding": 97309500.0,
					"total_due": 63654500.0,
					"invoiced": 159741500.0,
					"paid": 62432000.0,
					"bucket_31_60": 14844500.0,
					"bucket_61_90": 13412000.0,
					"bucket_121_above": 4044000.0,
				},
				{
					"party": "35th Street Mobile Wholesale",
					"outstanding": 84837000.0,
					"total_due": 82527000.0,
					"invoiced": 123627000.0,
					"paid": 38790000.0,
					"bucket_31_60": 12820000.0,
					"bucket_61_90": 8000000.0,
					"bucket_121_above": 25000000.0,
				},
			]
		}
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-current-result-continuation-party-artifact",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="make the prior explanation clearer",
				recent_messages=[],
				activation_contract=_activation_contract(),
				semantic_activation_result=_semantic_activation_result_current_result_continuation(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact=artifact,
				latest_assistant_payload=_latest_assistant_payload_title_only(),
				presentation_preferences={"bullet": True},
				prior_reasoning_contract={
					"type": "qwen_erp_business_reasoning_contract",
					"reasoning_type": "interpretation",
					"allowed_to_answer": True,
					"grounding_sufficient": True,
					"grounding_source_request_id": "grounded-risk-1",
					"grounding_family_id": "accounts_receivable",
					"grounding_source_reports": ["Accounts Receivable Aging"],
				},
				prior_answer_text="Prior grounded consultant answer.",
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertIn("heaviest aging bucket across listed parties", result.answer_text)
		self.assertIn("highest Invoiced", result.answer_text)

	def test_evidence_expansion_continuation_can_follow_prior_grounded_answer_without_reasoning_contract(self):
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-grounded-answer-continuation",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="give me more detail by breaking down the result",
				recent_messages=[],
				activation_contract=_activation_contract(),
				semantic_activation_result=_semantic_activation_result_evidence_expansion_continuation(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact=_latest_family_artifact_aging_sections(),
				latest_assistant_payload=_latest_assistant_payload_visible_aging_table(),
				presentation_preferences={"bullet": True},
				prior_answer_text="Prior grounded ERP answer from the same result.",
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_current_result_continuation"))
		self.assertIn("business reading", result.answer_text)
		self.assertIn("Consultant takeaway", result.answer_text)
		self.assertNotIn("supporting ERP detail view", result.answer_text)

	def test_evidence_expansion_continuation_keeps_broad_working_capital_focus(self):
		prior_answer = (
			"AR/AP Working Capital Health as of 2026-05-06. "
			"Accounts Receivable Outstanding is 803,681,000. "
			"Accounts Payable Outstanding is 929,916,600. "
			"Net AR minus AP is -126,235,600. "
			"AR Overdue Ratio is 72.1%. AP Overdue Ratio is 64.4%. "
			"Payables exceed receivables and both overdue ratios are material."
		)
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-broad-working-capital-continuation",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="give me more consultant views",
				recent_messages=[],
				activation_contract=_activation_contract_ar_ap_working_capital(),
				semantic_activation_result=_semantic_activation_result_evidence_expansion_continuation(),
				latest_grounded_turn={"grounded": True, "source_name": "AR / AP Working Capital Health", "table_rows": []},
				latest_family_artifact=_latest_family_artifact_ar_ap_working_capital(),
				latest_assistant_payload=_latest_assistant_payload_ar_ap_working_capital_title_only(),
				presentation_preferences={"bullet": True},
				prior_answer_text=prior_answer,
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_current_result_continuation"))
		self.assertNotIn("The follow-up is about Accounts Receivable Outstanding", result.answer_text)
		self.assertIn("business reading", result.answer_text)
		self.assertIn("Executive diagnosis", result.answer_text)
		self.assertIn("working-capital squeeze", result.answer_text)
		self.assertIn("synchronized on both sides", result.answer_text)
		self.assertIn("Key findings", result.answer_text)
		self.assertIn("Supplier obligations exceed customer receivables", result.answer_text)
		self.assertIn("two-sided working-capital stress", result.answer_text)
		self.assertIn("Using the overdue ratios", result.answer_text)
		self.assertIn("one working-capital plan", result.answer_text)
		self.assertIn("Management priorities", result.answer_text)
		self.assertIn("Pair AR recovery with AP settlement planning", result.answer_text)
		self.assertIn("Run a two-track weekly control", result.answer_text)
		self.assertIn("negative AR/AP gap", result.answer_text)
		self.assertIn("Recommended next step", result.answer_text)
		self.assertIn("Would you like me to compare the customer collection pressure", result.answer_text)
		self.assertIn("MMK million", result.answer_text)
		self.assertNotIn("supporting ERP detail view", result.answer_text)
		supported_claims = result.reasoning_contract.get("supported_claims") or []
		self.assertTrue(any("Pair AR recovery with AP settlement planning" in str(item.get("claim") or "") for item in supported_claims))
		self.assertTrue(any("Run a two-track weekly control" in str(item.get("claim") or "") for item in supported_claims))

	def test_working_capital_consultant_interpretation_uses_artifact_metrics_when_visible_table_is_not_latest(self):
		artifact = {
			"family_id": "composite_working_capital_health",
			"artifact_type": "normalized_composite_family_artifact",
			"source_reports": ["Accounts Receivable Summary", "Accounts Payable Summary"],
			"capability_id": "composite::working_capital_health",
			"metrics": {
				"accounts_receivable_outstanding_total": 803681000.0,
				"accounts_payable_outstanding_total": 929916600.0,
				"net_receivable_minus_payable": -126235600.0,
				"accounts_receivable_overdue_ratio": 72.9,
				"accounts_payable_overdue_ratio": 68.8,
			},
			"sections": {
				"summary": [],
			},
		}
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-working-capital-artifact-metrics-continuation",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="Evaluate above data as Business Consultant",
				recent_messages=[],
				activation_contract=_activation_contract_ar_ap_working_capital(),
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn={
					"grounded": True,
					"source_name": "AR / AP Working Capital Health",
					"returned_schema": ["Party", "Outstanding Amount", "Total Amount Due"],
					"row_count": 7,
					"table_rows": [
						{
							"Party": "Myanmar Tech Import Services",
							"Outstanding Amount": 268298000.0,
							"Total Amount Due": 250568000.0,
						},
					],
				},
				latest_family_artifact=artifact,
				latest_assistant_payload=_latest_assistant_payload_ar_ap_working_capital_title_only(),
				presentation_preferences={"bullet": True},
				prior_answer_text="Here is the business reading from AR/AP Working Capital Health.",
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_consultant_interpretation"))
		self.assertIn("working-capital squeeze", result.answer_text)
		self.assertIn("Supplier obligations exceed customer receivables", result.answer_text)
		self.assertIn("two-sided working-capital stress", result.answer_text)
		self.assertIn("Management priorities", result.answer_text)
		self.assertNotIn("This answer is limited", result.answer_text)

	def test_consultant_continuation_keeps_all_key_findings_as_bullets_without_explicit_bullet_preference(self):
		prior_answer = (
			"AR/AP Working Capital Health as of 2026-05-06. "
			"Accounts Receivable Outstanding is 803,681,000. "
			"Accounts Payable Outstanding is 929,916,600. "
			"Net AR minus AP is -126,235,600. "
			"AR Overdue Ratio is 72.1%. AP Overdue Ratio is 64.4%. "
			"Payables exceed receivables and both overdue ratios are material."
		)
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-broad-working-capital-continuation-layout",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="give me more consultant views",
				recent_messages=[],
				activation_contract=_activation_contract_ar_ap_working_capital(),
				semantic_activation_result=_semantic_activation_result_evidence_expansion_continuation(),
				latest_grounded_turn={"grounded": True, "source_name": "AR / AP Working Capital Health", "table_rows": []},
				latest_family_artifact=_latest_family_artifact_ar_ap_working_capital(),
				latest_assistant_payload=_latest_assistant_payload_ar_ap_working_capital_title_only(),
				presentation_preferences={},
				prior_answer_text=prior_answer,
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertIn("Executive diagnosis\n\n- This is a working-capital squeeze", result.answer_text)
		self.assertIn("Key findings\n\n- Supplier obligations exceed customer receivables", result.answer_text)
		self.assertIn("\n\n- Net AR minus AP is -126.2 MMK million", result.answer_text)
		self.assertIn("\n\n- This is two-sided working-capital stress", result.answer_text)
		self.assertIn("\n\n- Consultant takeaway:", result.answer_text)
		self.assertIn("\n\nManagement priorities\n\n- Pair AR recovery with AP settlement planning", result.answer_text)
		self.assertIn("\n\n- Run a two-track weekly control", result.answer_text)
		self.assertNotIn("Key findings\n\nSupplier obligations exceed customer receivables", result.answer_text)

	def test_evidence_expansion_continuation_preserves_prior_line_item_focus(self):
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-grounded-line-item-continuation",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="give me more detail by breaking down the result",
				recent_messages=[],
				activation_contract=_activation_contract_profit_and_loss(),
				semantic_activation_result=_semantic_activation_result_evidence_expansion_continuation(),
				latest_grounded_turn=_latest_grounded_turn_profit_and_loss(),
				latest_family_artifact=_latest_family_artifact_profit_and_loss(),
				latest_assistant_payload=_latest_assistant_payload_profit_and_loss_title_only(),
				presentation_preferences={"bullet": True},
				prior_answer_text=(
					"Cost of Goods Sold is shown under Expense in the current Profit And Loss. "
					"Amount: 51,764,064.95 MMK. Account: Cost of Goods Sold - MMOB."
				),
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_current_result_continuation"))
		self.assertIn("Cost of Goods Sold", result.answer_text)
		self.assertIn("51,764,064.95", result.answer_text)
		self.assertNotIn("Direct Income - MMOB", result.answer_text)

	def test_contextual_followup_preserves_prior_line_item_even_when_semantic_type_is_broad(self):
		prior_contract = {
			"type": "qwen_erp_business_reasoning_contract",
			"reasoning_type": "continuation_detail",
			"grounding_source_request_id": "grounded-pnl-1",
			"grounding_source_kind": "report",
			"grounding_family_id": "financial_statement",
			"grounding_artifact_type": "normalized_family_artifact",
			"grounding_source_reports": ["Profit and Loss Statement"],
			"grounding_sufficient": True,
			"grounding_gaps": [],
			"allowed_to_answer": True,
			"supported_claims": [],
			"recommendations": [],
			"offered_next_actions": [],
			"speculation_flags": ["runtime_repaired_to_prior_grounded_row_detail"],
		}
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-grounded-line-item-relaxed-continuation",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="give me more detail about that, by breaking down details",
				recent_messages=[],
				activation_contract=_activation_contract_profit_and_loss(),
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn=_latest_grounded_turn_profit_and_loss(),
				latest_family_artifact=_latest_family_artifact_profit_and_loss(),
				latest_assistant_payload=_latest_assistant_payload_profit_and_loss_title_only(),
				presentation_preferences={"bullet": True},
				prior_reasoning_contract=prior_contract,
				prior_answer_text=(
					"Cost of Goods Sold is shown under Expense in the current Profit And Loss. "
					"Amount: 51,764,064.95 MMK. Account: Cost of Goods Sold - MMOB."
				),
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_contextual_row_detail_continuation"))
		self.assertIn("Cost of Goods Sold", result.answer_text)
		self.assertIn("51,764,064.95", result.answer_text)
		self.assertNotIn("profit-recovery target", result.answer_text)

	def test_contextual_followup_uses_prior_reasoning_claims_when_latest_grounded_answer_is_broad(self):
		prior_contract = {
			"type": "qwen_erp_business_reasoning_contract",
			"reasoning_type": "continuation_detail",
			"grounding_source_request_id": "grounded-pnl-1",
			"grounding_source_kind": "report",
			"grounding_family_id": "financial_statement",
			"grounding_artifact_type": "normalized_family_artifact",
			"grounding_source_reports": ["Profit and Loss Statement"],
			"grounding_sufficient": True,
			"grounding_gaps": [],
			"allowed_to_answer": True,
			"supported_claims": [
				{
					"claim": "The follow-up is about Cost of Goods Sold from Profit and Loss Statement.",
					"support": "The prior grounded answer and a current result row refer to Cost of Goods Sold.",
				}
			],
			"recommendations": [],
			"offered_next_actions": [],
			"speculation_flags": ["runtime_repaired_to_prior_grounded_row_detail"],
		}
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-grounded-line-item-claim-continuation",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="give me more detail about that, by breaking down details",
				recent_messages=[],
				activation_contract=_activation_contract_profit_and_loss(),
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn=_latest_grounded_turn_profit_and_loss(),
				latest_family_artifact=_latest_family_artifact_profit_and_loss(),
				latest_assistant_payload=_latest_assistant_payload_profit_and_loss_title_only(),
				presentation_preferences={"bullet": True},
				prior_reasoning_contract=prior_contract,
				prior_answer_text=(
					"Profit and Loss Statement shows total income, total expenses, and net profit."
				),
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_contextual_row_detail_continuation"))
		self.assertIn("Cost of Goods Sold", result.answer_text)
		self.assertIn("51,764,064.95", result.answer_text)
		self.assertNotIn("profit-recovery target", result.answer_text)

	def test_contextual_followup_can_use_unambiguous_prior_row_answer_without_repair_flag(self):
		prior_contract = {
			"type": "qwen_erp_business_reasoning_contract",
			"reasoning_type": "continuation_detail",
			"grounding_source_request_id": "grounded-pnl-1",
			"grounding_source_kind": "report",
			"grounding_family_id": "financial_statement",
			"grounding_artifact_type": "normalized_family_artifact",
			"grounding_source_reports": ["Profit and Loss Statement"],
			"grounding_sufficient": True,
			"grounding_gaps": [],
			"allowed_to_answer": True,
			"supported_claims": [],
			"recommendations": [],
			"speculation_flags": [],
		}
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-grounded-line-item-unflagged-continuation",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="give me more detail about that, by breaking down details",
				recent_messages=[],
				activation_contract=_activation_contract_profit_and_loss(),
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn=_latest_grounded_turn_profit_and_loss(),
				latest_family_artifact=_latest_family_artifact_profit_and_loss(),
				latest_assistant_payload=_latest_assistant_payload_profit_and_loss_title_only(),
				presentation_preferences={"bullet": True},
				prior_reasoning_contract=prior_contract,
				prior_answer_text=(
					"Cost of Goods Sold is shown under Expense in the current Profit And Loss. "
					"Amount: 51,764,064.95 MMK. Share of income: 65.9%."
				),
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_contextual_row_detail_continuation"))
		self.assertIn("Cost of Goods Sold", result.answer_text)
		self.assertIn("51,764,064.95", result.answer_text)
		self.assertNotIn("profit-recovery target", result.answer_text)

	def test_contextual_followup_prefers_prior_answer_subject_over_later_category_mentions(self):
		prior_contract = {
			"type": "qwen_erp_business_reasoning_contract",
			"reasoning_type": "continuation_detail",
			"grounding_source_request_id": "grounded-pnl-1",
			"grounding_source_kind": "report",
			"grounding_family_id": "financial_statement",
			"grounding_artifact_type": "normalized_family_artifact",
			"grounding_source_reports": ["Profit and Loss Statement"],
			"grounding_sufficient": True,
			"grounding_gaps": [],
			"allowed_to_answer": True,
			"supported_claims": [],
			"recommendations": [],
			"speculation_flags": [],
		}
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-grounded-line-item-subject-priority",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="give me more detail about that, by breaking down details",
				recent_messages=[],
				activation_contract=_activation_contract_profit_and_loss(),
				semantic_activation_result=_semantic_activation_result(),
				latest_grounded_turn=_latest_grounded_turn_profit_and_loss(),
				latest_family_artifact=_latest_family_artifact_profit_and_loss(),
				latest_assistant_payload=_latest_assistant_payload_profit_and_loss_title_only(),
				presentation_preferences={"bullet": True},
				prior_reasoning_contract=prior_contract,
				prior_answer_text=(
					"Cost of Goods Sold is shown under Expense in the current Profit And Loss. "
					"Amount: 51,764,064.95 MMK. Share of income: 65.9%. "
					"Business category: Stock Expenses. This line is a material driver."
				),
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "answered")
		self.assertTrue(result.agent_meta.get("deterministic_contextual_row_detail_continuation"))
		self.assertIn("Cost of Goods Sold", result.answer_text)
		self.assertIn("51,764,064.95", result.answer_text)
		self.assertNotIn("Stock Expenses from Profit and Loss", result.answer_text)
		self.assertNotIn("profit-recovery target", result.answer_text)

	def test_evidence_expansion_continuation_without_prior_answer_still_fails_closed(self):
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-grounded-answer-continuation-no-prior",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="give me more detail by breaking down the result",
				recent_messages=[],
				activation_contract=_activation_contract(),
				semantic_activation_result=_semantic_activation_result_evidence_expansion_continuation(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact=_latest_family_artifact_aging_sections(),
				latest_assistant_payload=_latest_assistant_payload_visible_aging_table(),
				presentation_preferences={"bullet": True},
				prior_answer_text="",
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "insufficient_grounding")
		self.assertIn("missing_prior_reasoning_contract", result.reasoning_contract.get("grounding_gaps") or [])

	def test_current_result_only_continuation_without_prior_reasoning_contract_still_fails_closed(self):
		with patch.object(subject, "call_qwen_runtime_reasoning_render") as runtime_call:
			result = subject.execute_erp_business_reasoning(
				request_id="reasoning-current-result-no-prior-contract",
				session_id="reasoning-grounding",
				user_id="Administrator",
				message="make this clearer",
				recent_messages=[],
				activation_contract=_activation_contract(),
				semantic_activation_result=_semantic_activation_result_current_result_continuation(),
				latest_grounded_turn=_latest_grounded_turn(),
				latest_family_artifact=_latest_family_artifact_aging_sections(),
				latest_assistant_payload=_latest_assistant_payload_visible_aging_table(),
				presentation_preferences={"bullet": True},
				prior_answer_text="Prior grounded ERP answer from the same result.",
			)

		runtime_call.assert_not_called()
		self.assertEqual(result.status, "insufficient_grounding")
		self.assertIn("missing_prior_reasoning_contract", result.reasoning_contract.get("grounding_gaps") or [])


if __name__ == "__main__":
	unittest.main()
