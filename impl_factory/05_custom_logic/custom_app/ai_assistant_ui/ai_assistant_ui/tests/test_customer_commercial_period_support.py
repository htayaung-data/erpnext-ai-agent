import types
import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.customer_commercial_period_support import (
	list_customer_commercial_period_rows,
)


class TestCustomerCommercialPeriodSupport(unittest.TestCase):
	def test_list_customer_commercial_period_rows_aggregates_customer_metrics(self):
		fake_rows = [
			{
				"customer": "Zegyo Mobile Supply House",
				"document_count": 3,
				"revenue_total": 9340000.0,
				"quantity_total": 30.0,
			},
			{
				"customer": "Hledan Mobile Trade Center",
				"document_count": 2,
				"revenue_total": 1700000.0,
				"quantity_total": 15.0,
			},
		]
		fake_frappe = types.SimpleNamespace(
			db=types.SimpleNamespace(sql=lambda *args, **kwargs: fake_rows),
		)
		with patch(
			"ai_assistant_ui.qwen_chat.customer_commercial_period_support.frappe",
			fake_frappe,
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
