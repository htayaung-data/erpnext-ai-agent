import sys
import types
import unittest
from unittest.mock import patch


fake_frappe = sys.modules.get("frappe") or types.ModuleType("frappe")
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.db = types.SimpleNamespace(
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_all = lambda *args, **kwargs: []
sys.modules["frappe"] = fake_frappe

from ai_assistant_ui.qwen_chat.customer_lifecycle_support import get_customer_lifecycle_snapshot


class TestCustomerLifecycleSupport(unittest.TestCase):
	def test_customer_lifecycle_snapshot_collects_created_and_first_transaction_dates(self):
		sql_results = [
			[{"first_date": "2026-03-30"}],
			[{"first_date": "2026-04-01"}],
		]
		with patch(
			"ai_assistant_ui.qwen_chat.customer_lifecycle_support.frappe.db.get_value",
			return_value="2026-03-29 05:00:00",
		), patch(
			"ai_assistant_ui.qwen_chat.customer_lifecycle_support.frappe.db.sql",
			side_effect=sql_results,
		):
			snapshot = get_customer_lifecycle_snapshot(
				"Zegyo Mobile Supply House",
				company="Mingalar Mobile Distribution Co., Ltd.",
				as_of_date="2026-04-10",
			)
		self.assertEqual(snapshot.get("customer_created_date"), "2026-03-29")
		self.assertEqual(snapshot.get("first_sales_order_date"), "2026-03-30")
		self.assertEqual(snapshot.get("first_sales_invoice_date"), "2026-04-01")
		self.assertEqual(snapshot.get("customer_created_tenure_days"), 12)
		self.assertEqual(snapshot.get("first_sales_order_tenure_days"), 11)
		self.assertEqual(snapshot.get("first_sales_invoice_tenure_days"), 9)


if __name__ == "__main__":
	unittest.main()
