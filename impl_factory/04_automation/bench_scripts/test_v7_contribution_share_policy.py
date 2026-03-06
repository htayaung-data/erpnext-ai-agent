from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/contribution_share_policy.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_contribution_share_policy_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load contribution_share_policy module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7ContributionSharePolicyTests(unittest.TestCase):
    def test_customer_revenue_contribution_share_adds_percentage_column(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Customer Ledger Summary",
            "table": {
                "columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "invoiced_amount", "label": "Revenue", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"party": "A", "invoiced_amount": 60.0},
                    {"party": "B", "invoiced_amount": 40.0},
                ],
            },
        }
        spec = {
            "task_class": "contribution_share",
            "group_by": ["customer"],
            "dimensions": ["customer"],
            "filters": {
                "_contribution_rule": {
                    "metric": "revenue",
                    "basis": "of_total",
                    "contribution_terms": ["share_of_total"],
                }
            },
        }

        out = mod.apply_contribution_share(payload=payload, business_spec=spec)
        rows = out["table"]["rows"]
        self.assertEqual([r.get("contribution_share") for r in rows], ["60%", "40%"])
        self.assertTrue(bool(out.get("_contribution_rule_applied")))

    def test_item_revenue_contribution_share_updates_source_table_for_followups(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Item-wise Sales Register",
            "table": {
                "columns": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link"},
                    {"fieldname": "amount", "label": "Revenue", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"item_code": "ITM-001", "amount": 70.0},
                    {"item_code": "ITM-002", "amount": 30.0},
                ],
            },
        }
        spec = {
            "task_class": "contribution_share",
            "group_by": ["item"],
            "dimensions": ["item"],
            "filters": {
                "_contribution_rule": {
                    "metric": "revenue",
                    "basis": "of_total",
                    "contribution_terms": ["contribution_share"],
                }
            },
        }

        out = mod.apply_contribution_share(payload=payload, business_spec=spec)
        source_rows = out["_source_table"]["rows"]
        self.assertEqual(source_rows[0].get("contribution_share"), "70%")
        self.assertEqual(source_rows[1].get("contribution_share"), "30%")
        self.assertEqual(str(out.get("_contribution_metric") or ""), "revenue")
        self.assertEqual(str(out.get("_contribution_primary_dimension") or ""), "item")


if __name__ == "__main__":
    unittest.main()
