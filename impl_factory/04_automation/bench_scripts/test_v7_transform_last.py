from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/transform_last.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_transform_last_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load transform_last module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7TransformLastTests(unittest.TestCase):
    def test_scale_million_applies_for_read_when_transform_hint_present(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "customer", "label": "Customer", "fieldtype": "Data"},
                    {"fieldname": "total_amount", "label": "Total Amount", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"customer": "A", "total_amount": 1_500_000.0},
                    {"customer": "B", "total_amount": 500_000.0},
                ],
            },
        }
        spec = {
            "intent": "READ",
            "task_type": "detail",
            "task_class": "analytical_read",
            "output_contract": {"mode": "detail", "minimal_columns": ["customer", "total_amount"]},
            "ambiguities": ["transform_scale:million"],
        }
        out = mod.apply_transform_last(payload=payload, business_spec=spec)
        table = out.get("table") if isinstance(out.get("table"), dict) else {}
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        self.assertEqual(str(out.get("_scaled_unit") or ""), "million")
        self.assertEqual(float(rows[0].get("total_amount") or 0.0), 1.5)
        self.assertEqual(float(rows[1].get("total_amount") or 0.0), 0.5)

    def test_scale_million_on_outstanding_ranking_keeps_visible_rank_order(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "closing_balance", "label": "Outstanding Amount", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"party": "A", "closing_balance": 16_218_000.0},
                    {"party": "B", "closing_balance": 15_830_000.0},
                    {"party": "C", "closing_balance": 11_530_000.0},
                    {"party": "D", "closing_balance": 8_305_000.0},
                    {"party": "E", "closing_balance": 7_534_000.0},
                ],
            },
            "_source_table": {
                "columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "opening_balance", "label": "Opening Balance", "fieldtype": "Currency"},
                    {"fieldname": "closing_balance", "label": "Closing Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"party": "A", "opening_balance": 0.0, "closing_balance": 16_218_000.0},
                    {"party": "B", "opening_balance": 0.0, "closing_balance": 15_830_000.0},
                    {"party": "C", "opening_balance": 2_500_000.0, "closing_balance": 11_530_000.0},
                    {"party": "D", "opening_balance": 0.0, "closing_balance": 8_305_000.0},
                    {"party": "E", "opening_balance": 0.0, "closing_balance": 7_534_000.0},
                ],
            },
        }
        spec = {
            "intent": "TRANSFORM_LAST",
            "task_type": "ranking",
            "task_class": "transform_followup",
            "metric": "outstanding amount",
            "group_by": ["customer"],
            "top_n": 5,
            "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "outstanding amount"]},
            "ambiguities": ["transform_scale:million"],
        }
        out = mod.apply_transform_last(payload=payload, business_spec=spec)
        table = out.get("table") if isinstance(out.get("table"), dict) else {}
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        self.assertEqual([str(r.get("party") or "") for r in rows], ["A", "B", "C", "D", "E"])
        self.assertEqual(float(rows[0].get("closing_balance") or 0.0), 16.218)
        self.assertEqual(float(rows[3].get("closing_balance") or 0.0), 8.305)

    def test_repeat_scale_million_is_idempotent_for_visible_top_n_table(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "closing_balance", "label": "Outstanding Amount", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"party": "A", "closing_balance": 16.22},
                    {"party": "B", "closing_balance": 15.83},
                ],
            },
            "_scaled_unit": "million",
            "_output_mode": "top_n",
            "_transform_last_applied": "top_n",
            "_source_table": {
                "columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "opening_balance", "label": "Opening Balance", "fieldtype": "Currency"},
                    {"fieldname": "closing_balance", "label": "Closing Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"party": "A", "opening_balance": 0.0, "closing_balance": 16_218_000.0},
                    {"party": "B", "opening_balance": 0.0, "closing_balance": 15_830_000.0},
                ],
            },
        }
        spec = {
            "intent": "TRANSFORM_LAST",
            "task_type": "kpi",
            "task_class": "transform_followup",
            "metric": "outstanding amount",
            "aggregation": "sum",
            "group_by": ["customer"],
            "top_n": 10,
            "output_contract": {"mode": "kpi", "minimal_columns": ["customer", "outstanding amount"]},
            "ambiguities": ["transform_scale:million"],
        }
        out = mod.apply_transform_last(payload=payload, business_spec=spec)
        table = out.get("table") if isinstance(out.get("table"), dict) else {}
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        self.assertEqual([str(c.get("fieldname") or "") for c in list(table.get("columns") or [])], ["party", "closing_balance"])
        self.assertEqual([str(r.get("party") or "") for r in rows], ["A", "B"])
        self.assertEqual(str(out.get("_scaled_unit") or ""), "million")

    def test_first_scale_followup_uses_prior_top_n_mode_instead_of_kpi(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "_output_mode": "top_n",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399_386_000.0},
                    {"warehouse": "Mandalay Warehouse - MMOB", "stock_balance": 166_006_000.0},
                    {"warehouse": "Yangon Showroom Counter - MMOB", "stock_balance": 52_885_000.0},
                ],
            },
        }
        spec = {
            "intent": "TRANSFORM_LAST",
            "task_type": "kpi",
            "task_class": "transform_followup",
            "metric": "stock balance",
            "group_by": ["warehouse"],
            "top_n": 3,
            "dimensions": [],
            "ambiguities": ["transform_scale:million"],
            "output_contract": {"mode": "kpi", "minimal_columns": ["warehouse", "stock balance"]},
        }
        out = mod.apply_transform_last(payload=payload, business_spec=spec)
        table = out.get("table") if isinstance(out.get("table"), dict) else {}
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        self.assertEqual([str(c.get("fieldname") or "") for c in list(table.get("columns") or [])], ["warehouse", "stock_balance"])
        self.assertEqual([str(r.get("warehouse") or "") for r in rows], [
            "Yangon Main Warehouse - MMOB",
            "Mandalay Warehouse - MMOB",
            "Yangon Showroom Counter - MMOB",
        ])
        self.assertEqual(float(rows[0].get("stock_balance") or 0.0), 399.386)
        self.assertEqual(str(out.get("_scaled_unit") or ""), "million")

    def test_transform_last_promotes_hidden_source_when_specific_projection_column_missing(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link"},
                    {"fieldname": "total_qty", "label": "Sold Quantity", "fieldtype": "Float"},
                ],
                "rows": [
                    {"item_code": "ACC-001", "total_qty": 206.0},
                    {"item_code": "ACC-002", "total_qty": 103.0},
                ],
            },
            "_source_table": {
                "columns": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link"},
                    {"fieldname": "total_qty", "label": "Sold Quantity", "fieldtype": "Float"},
                    {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data"},
                ],
                "rows": [
                    {"item_code": "ACC-001", "total_qty": 206.0, "item_name": "Type-C Cable 1m Fast Charge"},
                    {"item_code": "ACC-002", "total_qty": 103.0, "item_name": "TPU Case Galaxy A15"},
                ],
            },
        }
        spec = {
            "intent": "TRANSFORM_LAST",
            "task_type": "ranking",
            "task_class": "transform_followup",
            "subject": "products",
            "metric": "sold quantity",
            "group_by": ["item"],
            "top_n": 10,
            "output_contract": {"mode": "top_n", "minimal_columns": ["item", "sold quantity", "item name"]},
            "ambiguities": [],
        }
        out = mod.apply_transform_last(payload=payload, business_spec=spec)
        table = out.get("table") if isinstance(out.get("table"), dict) else {}
        cols = [str(c.get("fieldname") or "") for c in list(table.get("columns") or []) if isinstance(c, dict)]
        self.assertIn("item_name", cols)


if __name__ == "__main__":
    unittest.main()
