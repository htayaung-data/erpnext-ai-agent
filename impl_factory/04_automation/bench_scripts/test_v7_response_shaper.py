from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/response_shaper.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_response_shaper_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load response_shaper module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7ResponseShaperTests(unittest.TestCase):
    def test_minimal_columns_keeps_group_by_dimension_when_contract_is_stale(self):
        mod = _load_module()
        spec = {
            "metric": "stock balance",
            "group_by": ["item"],
            "output_contract": {"mode": "detail", "minimal_columns": ["warehouse", "stock balance"]},
        }
        cols = list(mod._minimal_columns(spec))
        cols_lc = [str(x).strip().lower() for x in cols]
        self.assertIn("item", cols_lc)
        self.assertIn("warehouse", cols_lc)
        self.assertIn("stock balance", cols_lc)

    def test_project_table_does_not_shift_labels_when_middle_column_is_missing(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse"},
                    {"fieldname": "item_code", "label": "Item Code"},
                ],
                "rows": [
                    {"warehouse": "Yangon Main Warehouse - MMOB", "item_code": "ACC-AUD-SAM-EAR35"},
                ],
            },
        }
        spec = {
            "metric": "xqz_metric_foo",
            "group_by": ["item"],
            "output_contract": {"mode": "detail", "minimal_columns": ["warehouse", "xqz_metric_foo", "item"]},
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
        labels = [str(c.get("label") or "").strip().lower() for c in cols]
        self.assertIn("warehouse", labels)
        self.assertIn("item", labels)
        self.assertNotIn("xqz metric foo", labels)

    def test_metric_binding_rejects_non_numeric_column(self):
        mod = _load_module()
        columns = [
            {"fieldname": "warehouse", "label": "Warehouse"},
            {"fieldname": "item_code", "label": "Item Code"},
            {"fieldname": "projected_qty", "label": "Projected Qty", "fieldtype": "Float"},
        ]
        rows = [
            {
                "warehouse": "Yangon Main Warehouse - MMOB",
                "item_code": "ACC-AUD-SAM-EAR35",
                "projected_qty": 280,
            },
        ]
        bindings = list(mod._match_column_indexes(columns, rows, ["stock balance"]))
        matched_fieldnames = []
        for idx, _wanted in bindings:
            matched_fieldnames.append(str(columns[idx].get("fieldname") or "").strip().lower())
        self.assertNotIn("item_code", matched_fieldnames)

    def test_minimal_columns_prioritizes_dimensions_then_metric(self):
        mod = _load_module()
        spec = {
            "metric": "stock balance",
            "group_by": ["item"],
            "dimensions": ["item"],
            "output_contract": {"mode": "detail", "minimal_columns": ["warehouse", "stock balance"]},
        }
        cols = [str(x).strip().lower() for x in list(mod._minimal_columns(spec))]
        self.assertGreaterEqual(len(cols), 3)
        self.assertEqual(cols[0], "item")
        self.assertEqual(cols[1], "stock balance")
        self.assertEqual(cols[2], "warehouse")


if __name__ == "__main__":
    unittest.main()
