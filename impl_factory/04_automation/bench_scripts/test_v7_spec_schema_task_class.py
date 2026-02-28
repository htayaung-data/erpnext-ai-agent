from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/spec_schema.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_spec_schema_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load v7 spec schema module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7SpecSchemaTaskClassTests(unittest.TestCase):
    def test_infers_detail_projection_from_detail_shape(self):
        mod = _load_module()
        raw = {
            "intent": "READ",
            "task_type": "detail",
            "subject": "stock balance per item",
            "metric": "stock balance",
            "dimensions": ["item"],
            "group_by": ["item"],
            "output_contract": {"mode": "detail", "minimal_columns": ["item", "stock balance"]},
        }
        out, errs = mod.normalize_business_request_spec(raw)
        self.assertEqual(errs, [])
        self.assertEqual(str(out.get("task_class") or ""), "detail_projection")

    def test_infers_latest_list_for_top_n_without_known_metric(self):
        mod = _load_module()
        raw = {
            "intent": "READ",
            "task_type": "ranking",
            "subject": "latest invoices",
            "metric": "latest",
            "top_n": 7,
            "aggregation": "none",
            "output_contract": {"mode": "top_n", "minimal_columns": []},
        }
        out, errs = mod.normalize_business_request_spec(raw)
        self.assertEqual(errs, [])
        self.assertEqual(str(out.get("task_class") or ""), "list_latest_records")

    def test_keeps_explicit_task_class_when_valid(self):
        mod = _load_module()
        raw = {
            "intent": "READ",
            "task_type": "detail",
            "task_class": "detail_projection",
            "subject": "stock per item",
            "metric": "stock balance",
            "output_contract": {"mode": "detail", "minimal_columns": ["item", "stock balance"]},
        }
        out, errs = mod.normalize_business_request_spec(raw)
        self.assertEqual(errs, [])
        self.assertEqual(str(out.get("task_class") or ""), "detail_projection")

    def test_overrides_default_analytical_read_when_latest_shape_detected(self):
        mod = _load_module()
        raw = {
            "intent": "READ",
            "task_type": "detail",
            "task_class": "analytical_read",
            "subject": "invoice",
            "metric": "",
            "aggregation": "none",
            "top_n": 7,
            "output_contract": {"mode": "top_n", "minimal_columns": []},
        }
        out, errs = mod.normalize_business_request_spec(raw)
        self.assertEqual(errs, [])
        self.assertEqual(str(out.get("task_class") or ""), "list_latest_records")

    def test_latest_semantic_keeps_list_task_class_even_with_metric_and_sum(self):
        mod = _load_module()
        raw = {
            "intent": "READ",
            "task_type": "detail",
            "task_class": "analytical_read",
            "subject": "sales invoices",
            "metric": "total amount",
            "aggregation": "sum",
            "top_n": 7,
            "time_scope": {"mode": "relative", "value": "latest"},
            "output_contract": {"mode": "top_n", "minimal_columns": ["invoice_number", "posting_date", "total_amount"]},
        }
        out, errs = mod.normalize_business_request_spec(raw)
        self.assertEqual(errs, [])
        self.assertEqual(str(out.get("task_class") or ""), "list_latest_records")


if __name__ == "__main__":
    unittest.main()
