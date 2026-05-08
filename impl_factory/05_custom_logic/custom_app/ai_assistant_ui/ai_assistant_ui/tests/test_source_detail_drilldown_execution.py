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
		execute.assert_called_once()


if __name__ == "__main__":
	unittest.main()
