import unittest

from ai_assistant_ui.qwen_chat.filter_readiness_contract import (
	FILTER_READINESS_CONTRACT_TYPE,
	build_filter_readiness_contract,
	render_filter_readiness_boundary,
)


def _ar_comparison_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"title": "Accounts Receivable Summary",
		"report_name": "Accounts Receivable Summary",
		"sections": {
			"comparison_rows": [
				{
					"party": "35th Street Mobile Wholesale",
					"outstanding_amount": "84.8 MMK Million",
					"overdue_amount": "58.2 MMK Million",
					"overdue_intensity": "68.6%",
				},
				{
					"party": "Ko Nay Lin Mobile Center",
					"outstanding_amount": "63.1 MMK Million",
					"overdue_amount": "37.3 MMK Million",
					"overdue_intensity": "59.1%",
				},
			]
		},
	}


def _supplier_invoice_detail_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"title": "Purchase Invoice List",
		"report_name": "Purchase Invoice List",
		"sections": {
			"documents": [
				{
					"invoice": "ACC-PINV-2026-00306",
					"posting_date": "2026-03-07",
					"due_date": "2026-04-06",
					"status": "Overdue",
					"outstanding_amount": "40.7 MMK Million",
				}
			]
		},
	}


def _product_revenue_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"title": "Top 7 Products by Revenue",
		"sections": {
			"top_items": [
				{"rank": 1, "product": "Samsung Galaxy A15 (6GB 128GB)", "revenue": "341.21"},
				{"rank": 2, "product": "Xiaomi Redmi Note 13 (8GB 256GB)", "revenue": "281.77"},
			]
		},
	}


def _cogs_source_document_artifact():
	return {
		"type": "qwen_normalized_family_artifact_contract",
		"title": "Profit and Loss Statement - Cost of Goods Sold source detail",
		"report_name": "GL Entry Account Detail",
		"sections": {
			"documents": [
				{"source_document": "Delivery Note MAT-DN-2026-00339", "net_line_impact": "13.5", "share_of_line": "20.6%"},
				{"source_document": "Delivery Note MAT-DN-2026-00336", "net_line_impact": "11.3", "share_of_line": "17.3%"},
			]
		},
	}


class FilterReadinessContractTests(unittest.TestCase):
	def test_missing_visible_region_field_keeps_visible_boundary_contract(self):
		contract = build_filter_readiness_contract(
			raw_message="All above customers are from Yangon Region?",
			artifact_payload=_ar_comparison_artifact(),
		)

		self.assertEqual(contract["type"], FILTER_READINESS_CONTRACT_TYPE)
		self.assertEqual(contract["status"], "missing_filter_evidence")
		self.assertEqual(contract["requested_filter_keys"], ["customer", "territory"])
		self.assertEqual(contract["missing_visible_field_keys"], ["customer", "territory"])
		self.assertEqual(contract["unsupported_filter_keys"], ["territory"])
		self.assertIn("party", contract["visible_field_keys"])
		self.assertIn("customer", contract["supported_dimension_keys"])
		self.assertIn("Accounts Receivable Summary", contract["source_report_names"])

		answer = render_filter_readiness_boundary(contract)
		self.assertIn("Visible evidence covers: Party, Outstanding Amount, Overdue Amount, Overdue Intensity.", answer)
		self.assertIn("Fields needed: Customer, Territory.", answer)

	def test_supplier_requested_from_invoice_detail_requires_governed_view_not_guessing(self):
		contract = build_filter_readiness_contract(
			raw_message="who is second supplier in the above context?",
			artifact_payload=_supplier_invoice_detail_artifact(),
		)

		self.assertEqual(contract["status"], "requires_governed_filtered_view")
		self.assertEqual(contract["missing_visible_field_keys"], ["supplier"])
		self.assertEqual(contract["unsupported_filter_keys"], [])
		self.assertIn("supplier", contract["supported_dimension_keys"])

	def test_visible_product_field_is_ready_from_artifact(self):
		contract = build_filter_readiness_contract(
			raw_message="who is second product in the above table?",
			artifact_payload=_product_revenue_artifact(),
		)

		self.assertEqual(contract["status"], "ready_from_visible_artifact")
		self.assertEqual(contract["missing_visible_field_keys"], [])
		self.assertIn("product", contract["visible_field_keys"])

	def test_cogs_source_document_field_is_visible_even_when_financial_report_metadata_differs(self):
		contract = build_filter_readiness_contract(
			raw_message="who is first source document in the above context?",
			artifact_payload=_cogs_source_document_artifact(),
		)

		self.assertEqual(contract["status"], "ready_from_visible_artifact")
		self.assertEqual(contract["requested_filter_keys"], ["source_document"])
		self.assertIn("source_document", contract["visible_field_keys"])

	def test_accounts_receivable_report_title_does_not_create_account_filter(self):
		contract = build_filter_readiness_contract(
			raw_message="Explain the overdue risk in this accounts receivable summary.",
			artifact_payload=_ar_comparison_artifact(),
		)

		self.assertEqual(contract["status"], "no_filter_requested")
		self.assertEqual(contract["requested_filter_keys"], [])


if __name__ == "__main__":
	unittest.main()
