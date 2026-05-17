import datetime as dt
import sys
import types
import unittest
from unittest.mock import patch


def _fake_get_all(doctype, *args, **kwargs):
	if doctype == "Company":
		if kwargs.get("pluck") == "name":
			return ["Mingalar Mobile Distribution Co., Ltd."]
		return [{"name": "Mingalar Mobile Distribution Co., Ltd."}]
	if doctype == "Fiscal Year":
		return [
			{
				"name": "2025-2026",
				"year_start_date": "2025-04-01",
				"year_end_date": "2026-03-31",
			},
			{
				"name": "2026-2027",
				"year_start_date": "2026-04-01",
				"year_end_date": "2027-03-31",
			},
		]
	if doctype == "Period Closing Voucher":
		return [
			{
				"name": "ACC-PCV-2026-00004",
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"fiscal_year": "2025-2026",
				"period_start_date": "2025-04-01",
				"period_end_date": "2026-03-31",
				"transaction_date": "2026-03-31",
				"gle_processing_status": "Completed",
			},
			{
				"name": "ACC-PCV-2026-00001",
				"company": "Mingalar Mobile Distribution Co., Ltd.",
				"fiscal_year": "2024-2025",
				"period_start_date": "2024-04-01",
				"period_end_date": "2025-03-31",
				"transaction_date": "2025-03-31",
				"gle_processing_status": "Completed",
			},
		]
	return []


fake_frappe = types.ModuleType("frappe")
fake_frappe.get_all = _fake_get_all
fake_frappe.conf = {}
fake_frappe.local = types.SimpleNamespace(site="")
sys.modules.setdefault("frappe", fake_frappe)

from ai_assistant_ui.qwen_chat import defaults_repository as defaults_repository_module  # noqa: E402


class FinancialStatementDefaultPeriodContractsTest(unittest.TestCase):
	def test_latest_closed_period_row_prefers_latest_completed_period(self):
		with patch.object(
			defaults_repository_module,
			"load_period_closing_voucher_rows",
			return_value=_fake_get_all("Period Closing Voucher"),
		):
			row = defaults_repository_module.latest_closed_period_row(company="Mingalar Mobile Distribution Co., Ltd.")
		self.assertEqual(row.get("name"), "ACC-PCV-2026-00004")
		self.assertEqual(row.get("period_end_date"), "2026-03-31")

	def test_open_fiscal_year_bounds_start_day_after_latest_closed_period(self):
		with patch.object(
			defaults_repository_module,
			"load_period_closing_voucher_rows",
			return_value=_fake_get_all("Period Closing Voucher"),
		), patch.object(
			defaults_repository_module,
			"load_fiscal_year_rows",
			return_value=_fake_get_all("Fiscal Year"),
		):
			start, end = defaults_repository_module.open_fiscal_year_bounds(
				today=dt.date(2026, 4, 16),
				company="Mingalar Mobile Distribution Co., Ltd.",
			)
		self.assertEqual(start, "2026-04-01")
		self.assertEqual(end, "2026-04-16")


if __name__ == "__main__":
	unittest.main()
