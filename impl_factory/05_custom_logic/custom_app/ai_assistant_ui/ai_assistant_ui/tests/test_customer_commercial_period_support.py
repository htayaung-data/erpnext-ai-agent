import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.customer_commercial_period_support import (
	list_customer_commercial_period_rows,
)


class TestCustomerCommercialPeriodSupport(unittest.TestCase):
	def test_list_customer_commercial_period_rows_aggregates_customer_metrics(self):
		fake_rows = [
			{
				"entity_grain": "customer",
				"customer": "Zegyo Mobile Supply House",
				"document_count": 3,
				"revenue_total": 9340000.0,
				"quantity_total": 30.0,
				"average_document_value": 3113333.3333333335,
			},
			{
				"entity_grain": "customer",
				"customer": "Hledan Mobile Trade Center",
				"document_count": 2,
				"revenue_total": 1700000.0,
				"quantity_total": 15.0,
				"average_document_value": 850000.0,
			},
		]
		with patch(
			"ai_assistant_ui.qwen_chat.customer_commercial_period_support.list_entity_period_commercial_rows",
			return_value=fake_rows,
		):
			rows = list_customer_commercial_period_rows(
				report_name="Sales Order List",
				company="Mingalar Mobile Distribution Co., Ltd.",
				from_date="2026-03-01",
				to_date="2026-03-31",
			)
		self.assertEqual(len(rows), 2)
		self.assertEqual(rows[0].get("customer"), "Zegyo Mobile Supply House")
		self.assertEqual(rows[0].get("document_count"), 3)
		self.assertEqual(rows[0].get("revenue_total"), 9340000.0)
		self.assertEqual(rows[0].get("quantity_total"), 30.0)
		self.assertAlmostEqual(rows[0].get("average_document_value"), 3113333.3333333335)
