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


if __name__ == "__main__":
    unittest.main()

