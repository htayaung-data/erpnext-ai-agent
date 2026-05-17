import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.evidence_response_support import (
	grounded_artifact_direct_evidence_response,
)
from ai_assistant_ui.qwen_chat.source_detail_drilldown_execution import (
	build_source_detail_drilldown_payload_from_artifact_line,
)


def _profit_and_loss_artifact():
	return {
		"family_id": "financial_statement",
		"capability_id": "financial_statement_read",
		"title": "Profit and Loss Statement",
		"source_reports": ["Profit and Loss Statement"],
		"filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
		"period": {"from_date": "2026-04-01", "to_date": "2026-05-08"},
		"metrics": {
			"total_income": "91,480,000",
			"total_expense": "102,894,942.84",
			"net_profit": "-11,414,942.84",
		},
		"sections": {
			"expense": [
				{
					"account": "Cost of Goods Sold - MMOB",
					"label": "Cost of Goods Sold",
					"amount": "65,360,820.70",
					"parent_account": "Stock Expenses - MMOB",
					"currency": "MMK",
				}
			]
		},
		"dimensions": {"currency": "MMK"},
	}


def _source_detail_report_payload():
	return {
		"ok": True,
		"tool_trace": [
			{
				"output_obj": {
					"result": {
						"data": [
							{
								"posting_date": "2026-05-08",
								"voucher_type": "Delivery Note",
								"voucher_no": "MAT-DN-2026-00339",
								"debit": "40,000,000.00",
								"credit": "0",
							},
							{
								"posting_date": "2026-05-08",
								"voucher_type": "Delivery Note",
								"voucher_no": "MAT-DN-2026-00340",
								"debit": "25,360,820.70",
								"credit": "0",
							},
						]
					}
				}
			}
		],
	}


def _accounts_receivable_artifact():
	return {
		"family_id": "accounts_receivable",
		"capability_id": "accounts_receivable_read",
		"title": "Accounts Receivable Aging as of 2026-05-08",
		"source_reports": ["Accounts Receivable Aging"],
		"filters": {"company": "Mingalar Mobile Distribution Co., Ltd.", "as_of_date": "2026-05-08"},
		"period": {"as_of_date": "2026-05-08"},
		"sections": {
			"ranked_rows": [
				{
					"rank": 2,
					"party": "Ko Nay Lin Mobile Center",
					"customer": "Ko Nay Lin Mobile Center",
					"outstanding_amount": "63,125,000",
					"overdue_amount": "37,335,000",
					"overdue_intensity": "59.1%",
				}
			]
		},
	}


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
								"customer": "Ko Nay Lin Mobile Center",
								"grand_total": "40,000,000",
								"outstanding_amount": "33,125,000",
								"status": "Overdue",
							},
							{
								"name": "SINV-2026-00018",
								"posting_date": "2026-04-15",
								"due_date": "2026-05-15",
								"customer": "Ko Nay Lin Mobile Center",
								"grand_total": "30,000,000",
								"outstanding_amount": "30,000,000",
								"status": "Overdue",
							},
						]
					}
				}
			}
		],
	}


class SourceDetailDrilldownExecutionTests(unittest.TestCase):
	def test_artifact_line_drilldown_executes_registered_source_detail_report(self):
		artifact = _profit_and_loss_artifact()
		row = dict(artifact["sections"]["expense"][0])
		with patch(
			"ai_assistant_ui.qwen_chat.source_detail_drilldown_execution.execute_governed_report",
			return_value=_source_detail_report_payload(),
		) as execute:
			payload = build_source_detail_drilldown_payload_from_artifact_line(
				artifact_payload=artifact,
				focused_row=row,
				user_id="Administrator",
			)

		self.assertIn("source-detail breakdown", payload["answer_text"])
		self.assertIn("GL Entry Account Detail", payload["answer_text"])
		self.assertIn("MAT-DN-2026-00339", payload["answer_text"])
		self.assertIn("Net line impact", payload["answer_text"])
		execute.assert_called_once()
		self.assertEqual(execute.call_args.kwargs["filters"]["account"], "Cost of Goods Sold - MMOB")

	def test_first_turn_cogs_detail_uses_source_detail_before_summary_only_fallback(self):
		artifact = _profit_and_loss_artifact()
		interaction_contract = SimpleNamespace(user_id="Administrator", site_name="erpai_prj1")
		response_policy_contract = SimpleNamespace(to_runtime_payload=lambda: {})
		with patch(
			"ai_assistant_ui.qwen_chat.source_detail_drilldown_execution.execute_governed_report",
			return_value=_source_detail_report_payload(),
		) as execute:
			response = grounded_artifact_direct_evidence_response(
				request_id="req-1",
				session_id="session-1",
				interaction_contract=interaction_contract,
				response_policy_contract=response_policy_contract,
				raw_message="Tell me more about COGS",
				artifact_payload=artifact,
				grounded_turn={"grounded": True, "source_name": "Profit and Loss Statement"},
			)

		self.assertIn("source-detail breakdown", response["answer_text"])
		self.assertIn("Breakdown by source document", response["answer_text"])
		self.assertIn("MAT-DN-2026-00339", response["answer_text"])
		self.assertTrue(response["rendered_response_payload"]["source_detail_drilldown"])
		selection = response["selected_entity_activation_payload"]
		self.assertEqual(selection["type"], "qwen_nbu_current_artifact_answer_activation_contract")
		self.assertEqual(selection["activation_mode"], "source_detail_selected_row")
		self.assertEqual(selection["resolved_entity"]["entity_label"], "Cost of Goods Sold - MMOB")
		execute.assert_called_once()

	def test_ar_party_drilldown_executes_sales_invoice_source_detail(self):
		artifact = _accounts_receivable_artifact()
		row = dict(artifact["sections"]["ranked_rows"][0])
		with patch(
			"ai_assistant_ui.qwen_chat.source_detail_drilldown_execution.execute_governed_report",
			return_value=_sales_invoice_detail_payload(),
		) as execute:
			payload = build_source_detail_drilldown_payload_from_artifact_line(
				artifact_payload=artifact,
				focused_row=row,
				user_id="Administrator",
			)

		self.assertIn("source-detail breakdown", payload["answer_text"])
		self.assertIn("Sales Invoice List", payload["answer_text"])
		self.assertIn("SINV-2026-00042", payload["answer_text"])
		self.assertIn("Due Date", payload["answer_text"])
		self.assertIn("Outstanding amount", payload["answer_text"])
		self.assertIn("63.1 MMK million", payload["answer_text"])
		execute.assert_called_once()
		self.assertEqual(execute.call_args.kwargs["filters"]["customer"], "Ko Nay Lin Mobile Center")
		self.assertEqual(execute.call_args.kwargs["filters"]["to_date"], "2026-05-08")


if __name__ == "__main__":
	unittest.main()
