import unittest

from ai_assistant_ui.qwen_chat.customer_boundary_answer_support import (
	customer_boundary_direct_evidence_answer,
)


class CustomerBoundaryAnswerSupportTests(unittest.TestCase):
	def test_customer_boundary_answer_returns_credit_limit_status(self) -> None:
		answer = customer_boundary_direct_evidence_answer(
			typed_request={"requested_metrics": ["credit_limit_status"]},
			artifact={
				"metrics": {
					"outstanding_total": 12500000,
					"credit_limit": 75000000,
					"credit_limit_available": 62500000,
					"credit_limit_configured": True,
				},
				"sections": {
					"credit_policy": [
						{"label": "Company", "value": "Mingalar Mobile Distribution Co., Ltd."},
					]
				},
			},
			dimensions={"entity_label": "Ko Nay Lin Mobile Center"},
			clarification_required=False,
			clarification_reason_type="",
		)
		self.assertIn("within the configured credit limit", answer.lower())
		self.assertIn("62,500,000", answer)

	def test_customer_boundary_answer_returns_boundary_clarification_when_available(self) -> None:
		answer = customer_boundary_direct_evidence_answer(
			typed_request={"entity_question_type": "customer_lifecycle_date"},
			artifact={
				"sections": {
					"credit_policy": [
						{"label": "Company", "value": "Mingalar Mobile Distribution Co., Ltd."},
					]
				},
			},
			dimensions={"entity_label": "Zegyo Mobile Supply House"},
			clarification_required=True,
			clarification_reason_type="customer_operational_document_missing",
		)
		self.assertIn("exact sales document or date basis", answer.lower())
		self.assertIn("first sales order date", answer.lower())
		self.assertIn("specific sales order or sales invoice", answer.lower())


if __name__ == "__main__":
	unittest.main()
