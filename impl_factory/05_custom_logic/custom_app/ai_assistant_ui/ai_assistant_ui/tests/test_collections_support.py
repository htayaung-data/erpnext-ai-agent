import unittest
from unittest.mock import patch

from ai_assistant_ui.qwen_chat.collections_support import compute_collection_ratio_by_sales_invoice_period


class TestCollectionsSupport(unittest.TestCase):
	def test_collection_ratio_uses_allocated_receipts_against_invoice_period(self):
		with patch(
			"ai_assistant_ui.qwen_chat.collections_support.frappe.db.sql",
			side_effect=[
				[{"invoice_count": 4, "sales_invoice_grand_total": 2000000}],
				[{"allocated_customer_receipt_amount": 1500000}],
			],
		):
			result = compute_collection_ratio_by_sales_invoice_period(
				company="Mingalar Mobile Distribution Co., Ltd.",
				from_date="2026-03-01",
				to_date="2026-03-31",
			)
		self.assertEqual(result.get("invoice_count"), 4)
		self.assertEqual(result.get("sales_invoice_grand_total"), 2000000.0)
		self.assertEqual(result.get("allocated_customer_receipt_amount"), 1500000.0)
		self.assertEqual(result.get("collection_ratio"), 0.75)


if __name__ == "__main__":
	unittest.main()
