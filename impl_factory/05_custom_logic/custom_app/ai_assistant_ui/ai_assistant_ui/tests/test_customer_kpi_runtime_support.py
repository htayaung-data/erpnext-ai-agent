import sys
import types
import unittest
from unittest.mock import patch

fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = lambda *args, **kwargs: []
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
fake_frappe.db = types.SimpleNamespace(
	exists=lambda *args, **kwargs: False,
	get_value=lambda *args, **kwargs: None,
	sql=lambda *args, **kwargs: [],
)
fake_frappe.get_doc = lambda *args, **kwargs: None
fake_frappe.DoesNotExistError = type("DoesNotExistError", (Exception,), {})
fake_frappe.ValidationError = type("ValidationError", (Exception,), {})
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat.customer_kpi_runtime_support import (
	get_customer_receivable_snapshot,
	list_customer_kpi_rows,
	resolve_customer_scope_from_message,
)


class TestCustomerKpiRuntimeSupport(unittest.TestCase):
	def test_resolve_customer_scope_from_message_matches_longest_customer_alias(self):
		with patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support.frappe.get_all",
			return_value=[
				{"name": "Zegyo Mobile Supply House", "customer_name": "Zegyo Mobile Supply House"},
				{"name": "Zegyo Mobile", "customer_name": "Zegyo Mobile"},
			],
		):
			scope = resolve_customer_scope_from_message("what is overdue ratio for Zegyo Mobile Supply House as of today")
		self.assertEqual(scope.get("customer"), "Zegyo Mobile Supply House")
		self.assertEqual(scope.get("customer_name"), "Zegyo Mobile Supply House")
		self.assertTrue(scope.get("has_customer_scope"))

	def test_customer_receivable_snapshot_uses_matching_party_row(self):
		with patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support.execute_governed_report",
			return_value={"ok": True},
		), patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support._report_tool",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support._report_result",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support._report_rows",
			return_value=[
				{
					"party": "Zegyo Mobile Supply House",
					"outstanding": 495000,
					"total_due": 495000,
					"future_amount": 0,
					"range1": 495000,
					"range2": 0,
					"range3": 0,
					"range4": 0,
					"range5": 0,
				}
			],
		):
			snapshot = get_customer_receivable_snapshot(
				"Zegyo Mobile Supply House",
				customer_label="Zegyo Mobile Supply House",
				company="Mingalar Mobile Distribution Co., Ltd.",
				as_of_date="2026-04-10",
			)
		self.assertEqual(snapshot.get("report_date"), "2026-04-10")
		self.assertEqual(snapshot.get("metrics", {}).get("outstanding_total"), 495000.0)
		self.assertEqual(snapshot.get("metrics", {}).get("overdue_total"), 0.0)
		self.assertEqual(snapshot.get("metrics", {}).get("overdue_ratio"), 0.0)

	def test_customer_kpi_rows_join_receivable_and_credit_policy(self):
		def _fake_get_all(doctype, **kwargs):
			if doctype == "Customer":
				return [
					{"name": "Zegyo Mobile Supply House", "customer_name": "Zegyo Mobile Supply House"},
					{"name": "Bayint Naung Wholesale Mobile", "customer_name": "Bayint Naung Wholesale Mobile"},
				]
			if doctype == "Customer Credit Limit":
				return [
					{
						"parent": "Zegyo Mobile Supply House",
						"company": "Mingalar Mobile Distribution Co., Ltd.",
						"credit_limit": 10000000,
						"bypass_credit_limit_check": 0,
					},
					{
						"parent": "Bayint Naung Wholesale Mobile",
						"company": "Mingalar Mobile Distribution Co., Ltd.",
						"credit_limit": 10000000,
						"bypass_credit_limit_check": 0,
					},
				]
			return []

		with patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support.execute_governed_report",
			return_value={"ok": True},
		), patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support._report_tool",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support._report_result",
			return_value={},
		), patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support._report_rows",
			return_value=[
				{
					"party": "Zegyo Mobile Supply House",
					"outstanding": 495000,
					"total_due": 495000,
					"future_amount": 0,
					"range1": 495000,
					"range2": 0,
					"range3": 0,
					"range4": 0,
					"range5": 0,
				},
				{
					"party": "Bayint Naung Wholesale Mobile",
					"outstanding": 12000000,
					"total_due": 12000000,
					"future_amount": 0,
					"range1": 0,
					"range2": 4000000,
					"range3": 2000000,
					"range4": 1000000,
					"range5": 3000000,
				},
			],
		), patch(
			"ai_assistant_ui.qwen_chat.customer_kpi_runtime_support.frappe.get_all",
			side_effect=_fake_get_all,
		):
			rows = list_customer_kpi_rows(
				company="Mingalar Mobile Distribution Co., Ltd.",
				as_of_date="2026-04-10",
			)
		self.assertEqual(len(rows), 2)
		zegyo_row = next(row for row in rows if row.get("customer") == "Zegyo Mobile Supply House")
		bayint_row = next(row for row in rows if row.get("customer") == "Bayint Naung Wholesale Mobile")
		self.assertAlmostEqual(zegyo_row.get("credit_limit_utilization_ratio"), 0.0495)
		self.assertFalse(zegyo_row.get("credit_limit_exceeded"))
		self.assertAlmostEqual(bayint_row.get("overdue_ratio"), 0.8333333333333334)
		self.assertTrue(bayint_row.get("credit_limit_exceeded"))
		self.assertEqual(
			((bayint_row.get("credit_threshold_state") or {}).get("matched_band_label")),
			"limit_exceeded",
		)


if __name__ == "__main__":
	unittest.main()
