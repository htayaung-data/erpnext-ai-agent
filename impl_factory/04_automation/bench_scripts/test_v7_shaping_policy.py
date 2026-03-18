from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/shaping_policy.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_shaping_policy_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load shaping_policy module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7ShapingPolicyTests(unittest.TestCase):
    def test_sanitize_error_payload_maps_to_unsupported_text(self):
        mod = _load_module()
        out = mod.sanitize_user_payload(
            payload={"type": "error", "text": "Traceback: boom"},
            business_spec={"subject": "invoices", "metric": "revenue"},
        )
        self.assertEqual(str(out.get("type") or ""), "text")
        self.assertIn("couldn't reliably produce that result", str(out.get("text") or "").lower())

    def test_sanitize_text_collapses_duplicate_lines(self):
        mod = _load_module()
        out = mod.sanitize_user_payload(
            payload={"type": "text", "text": "Which warehouse should I use?\nWhich warehouse should I use?\n"},
            business_spec={},
        )
        self.assertEqual(str(out.get("text") or ""), "Which warehouse should I use?")

    def test_sanitize_text_preserves_write_confirmation_text(self):
        mod = _load_module()
        expected = "Confirmed. Deleted **ToDo** `TD-0001`."
        out = mod.sanitize_user_payload(
            payload={"type": "text", "text": expected},
            business_spec={},
        )
        self.assertEqual(str(out.get("text") or ""), expected)

    def test_sanitize_report_table_payload_keeps_table_unchanged(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [{"fieldname": "customer", "label": "Customer"}],
                "rows": [{"customer": "ABC"}],
            },
        }
        out = mod.sanitize_user_payload(payload=payload, business_spec={})
        self.assertEqual(str(out.get("type") or ""), "report_table")
        self.assertEqual(out.get("table"), payload.get("table"))

    def test_enrich_minimal_columns_preserves_period_comparison_columns(self):
        mod = _load_module()
        spec_obj = {
            "task_class": "comparison",
            "task_type": "comparison",
            "metric": "revenue",
            "group_by": ["territory"],
            "output_contract": {
                "mode": "comparison",
                "minimal_columns": ["territory", "Feb 2026", "Mar 2026"],
            },
            "filters": {
                "territory": "Yangon",
                "_comparison_rule": {
                    "metric": "revenue",
                    "dimension": "territory",
                    "time_structure": "monthly_period_vs_period",
                    "month_refs": [
                        {"month_name": "march", "year": 2026, "label": "March 2026"},
                        {"month_name": "february", "year": 2026, "label": "February 2026"},
                    ],
                    "single_entity_kind": "territory",
                    "single_entity_value": "Yangon",
                },
            },
        }
        out = mod.enrich_minimal_columns_from_report_metadata(
            spec_obj=spec_obj,
            message="Compare Yangon revenue in March 2026 vs February 2026",
            selected_report="Sales Analytics",
            last_result_payload=None,
        )
        output_contract = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
        self.assertEqual(
            [str(x).strip() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["territory", "Feb 2026", "Mar 2026"],
        )


if __name__ == "__main__":
    unittest.main()
