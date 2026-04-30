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

from ai_assistant_ui.qwen_chat.governed_report_executor import execute_governed_report


class TestGovernedReportExecutorContracts(unittest.TestCase):
	def test_direct_query_skips_company_filter_when_doctype_does_not_support_it(self):
		report_spec = {
			"grounding_mode": "direct_query",
			"direct_query": {
				"doctype": "Customer",
				"fields": ["name", "customer_name", "creation"],
				"date_field": "creation",
				"default_limit": 5,
			},
			"required_filters": [],
			"defaultable_filters": [],
		}
		with patch(
			"ai_assistant_ui.qwen_chat.governed_report_executor.get_report_spec",
			return_value=report_spec,
		), patch(
			"ai_assistant_ui.qwen_chat.governed_report_executor.frappe.get_all",
			return_value=[{"name": "CUST-001", "customer_name": "Customer One", "creation": "2026-03-30 00:00:00"}],
		) as mocked_get_all:
			payload = execute_governed_report(
				report_name="Customer Master List",
				filters={
					"company": "Mingalar Mobile Distribution Co., Ltd.",
					"to_date": "2026-04-10",
				},
				user="Administrator",
			)
		self.assertTrue(payload.get("ok"), payload)
		self.assertEqual(
			mocked_get_all.call_args.kwargs.get("filters"),
			{
				"creation": ["<=", "2026-04-10"],
			},
		)


if __name__ == "__main__":
	unittest.main()
