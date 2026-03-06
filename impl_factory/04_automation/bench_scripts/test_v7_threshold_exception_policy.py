from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/threshold_exception_policy.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_threshold_exception_policy_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load threshold_exception_policy module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7ThresholdExceptionPolicyTests(unittest.TestCase):
    def test_customer_outstanding_amount_threshold_filters_rows_and_aggregate(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Customer Ledger Summary",
            "table": {
                "columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "closing_balance", "label": "Outstanding Amount", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"party": "All Customers", "closing_balance": 87912000.0},
                    {"party": "Shwe Li Road Mobile Wholesale", "closing_balance": 16218000.0},
                    {"party": "Latha Mobile Wholesale", "closing_balance": 15830000.0},
                    {"party": "City Mobile Mart", "closing_balance": 1800000.0},
                ],
            },
        }
        spec = {
            "task_class": "threshold_exception_list",
            "group_by": ["customer"],
            "dimensions": ["customer"],
            "filters": {
                "_threshold_rule": {
                    "metric": "outstanding_amount",
                    "comparator": "gt",
                    "value": 10_000_000.0,
                    "value_present": True,
                }
            },
        }

        out = mod.apply_threshold_exception_filter(payload=payload, business_spec=spec)
        rows = out["table"]["rows"]
        self.assertEqual(
            [r.get("party") for r in rows],
            ["Shwe Li Road Mobile Wholesale", "Latha Mobile Wholesale"],
        )
        self.assertTrue(bool(out.get("_threshold_rule_applied")))

    def test_overdue_invoice_threshold_filters_status_and_amount(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Latest Sales Invoice",
            "table": {
                "columns": [
                    {"fieldname": "name", "label": "Sales Invoice Number", "fieldtype": "Link"},
                    {"fieldname": "customer", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "grand_total", "label": "Grand Total", "fieldtype": "Currency"},
                    {"fieldname": "status", "label": "Status", "fieldtype": "Data"},
                ],
                "rows": [
                    {"name": "ACC-SINV-0001", "customer": "A", "grand_total": 6000000.0, "status": "Overdue"},
                    {"name": "ACC-SINV-0002", "customer": "B", "grand_total": 6500000.0, "status": "Paid"},
                    {"name": "ACC-SINV-0003", "customer": "C", "grand_total": 2000000.0, "status": "Overdue"},
                ],
            },
        }
        spec = {
            "task_class": "threshold_exception_list",
            "group_by": ["invoice"],
            "dimensions": ["invoice"],
            "filters": {
                "_threshold_rule": {
                    "metric": "invoice_amount",
                    "comparator": "gt",
                    "value": 5_000_000.0,
                    "value_present": True,
                    "exception_terms": ["overdue"],
                }
            },
        }

        out = mod.apply_threshold_exception_filter(payload=payload, business_spec=spec)
        rows = out["table"]["rows"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].get("name"), "ACC-SINV-0001")

    def test_warehouse_stock_balance_threshold_excludes_aggregate_row(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Warehouse Wise Stock Balance",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"warehouse": "All Warehouses - MMOB", "stock_balance": 618229000.0},
                    {"warehouse": "Stores - MMOB", "stock_balance": 0.0},
                    {"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399386000.0},
                    {"warehouse": "Finished Goods - MMOB", "stock_balance": 0.0},
                ],
            },
        }
        spec = {
            "task_class": "threshold_exception_list",
            "group_by": ["warehouse"],
            "dimensions": ["warehouse"],
            "filters": {
                "_threshold_rule": {
                    "metric": "stock_balance",
                    "comparator": "lt",
                    "value": 50_000_000.0,
                    "value_present": True,
                }
            },
        }

        out = mod.apply_threshold_exception_filter(payload=payload, business_spec=spec)
        rows = out["table"]["rows"]
        self.assertEqual(
            [r.get("warehouse") for r in rows],
            ["Stores - MMOB", "Finished Goods - MMOB"],
        )

    def test_threshold_filter_updates_source_table_for_followups(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Warehouse Wise Stock Balance",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"warehouse": "All Warehouses - MMOB", "stock_balance": 618229000.0},
                    {"warehouse": "Stores - MMOB", "stock_balance": 0.0},
                ],
            },
            "_source_table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                    {"fieldname": "company", "label": "Company", "fieldtype": "Link"},
                ],
                "rows": [
                    {"warehouse": "All Warehouses - MMOB", "stock_balance": 618229000.0, "company": "MMOB"},
                    {"warehouse": "Stores - MMOB", "stock_balance": 0.0, "company": "MMOB"},
                ],
            },
        }
        spec = {
            "task_class": "threshold_exception_list",
            "group_by": ["warehouse"],
            "dimensions": ["warehouse"],
            "filters": {
                "_threshold_rule": {
                    "metric": "stock_balance",
                    "comparator": "lt",
                    "value": 50_000_000.0,
                    "value_present": True,
                }
            },
        }

        out = mod.apply_threshold_exception_filter(payload=payload, business_spec=spec)
        source_rows = out["_source_table"]["rows"]
        self.assertEqual(len(source_rows), 1)
        self.assertEqual(source_rows[0].get("warehouse"), "Stores - MMOB")
        self.assertTrue(bool(out.get("_threshold_rule_applied")))
        self.assertEqual(str(out.get("_threshold_primary_dimension") or ""), "warehouse")
        self.assertEqual(str(out.get("_threshold_metric") or ""), "stock_balance")
        self.assertIsInstance(out.get("_threshold_rule"), dict)


if __name__ == "__main__":
    unittest.main()
