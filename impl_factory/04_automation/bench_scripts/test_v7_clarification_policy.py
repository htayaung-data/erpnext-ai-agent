from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/clarification_policy.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_clarification_policy_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load clarification_policy module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7ClarificationPolicyTests(unittest.TestCase):
    def test_reason_driven_question_for_hard_constraint(self):
        mod = _load_module()
        out = mod.evaluate_clarification(
            business_spec={},
            resolved={
                "needs_clarification": True,
                "clarification_reason": "hard_constraint_not_supported",
                "clarification_question": "Which metric and grouping should I use?",
            },
        )
        self.assertTrue(bool(out.get("should_clarify")))
        self.assertEqual(str(out.get("reason") or ""), "hard_constraint_not_supported")
        q = str(out.get("question") or "").lower()
        self.assertIn("switch", q)
        self.assertIn("keep", q)

    def test_entity_reason_keeps_contextual_question(self):
        mod = _load_module()
        out = mod.evaluate_clarification(
            business_spec={},
            resolved={
                "needs_clarification": True,
                "clarification_reason": "entity_ambiguous",
                "clarification_question": "I found multiple warehouses. Which one should I use?",
            },
        )
        self.assertTrue(bool(out.get("should_clarify")))
        self.assertIn("multiple warehouses", str(out.get("question") or "").lower())

    def test_spec_only_clarification_does_not_trigger_without_resolver_reason(self):
        mod = _load_module()
        out = mod.evaluate_clarification(
            business_spec={
                "needs_clarification": True,
                "clarification_question": "I found multiple warehouses matching MMOB. Which exact warehouse should I use?",
            },
            resolved={
                "needs_clarification": False,
                "clarification_reason": "",
                "clarification_question": "",
            },
        )
        self.assertFalse(bool(out.get("should_clarify")))
        self.assertEqual(str(out.get("reason") or ""), "")

    def test_soft_semantic_blocker_does_not_force_clarification(self):
        mod = _load_module()
        out = mod.evaluate_clarification(
            business_spec={},
            resolved={
                "needs_clarification": True,
                "clarification_reason": "hard_constraint_not_supported",
                "selected_report": "Item-wise Sales Register",
                "candidate_reports": [
                    {
                        "report_name": "Item-wise Sales Register",
                        "hard_blockers": ["unsupported_metric"],
                        "missing_required_filter_values": [],
                    }
                ],
            },
        )
        self.assertFalse(bool(out.get("should_clarify")))
        self.assertEqual(str(out.get("reason") or ""), "")

    def test_missing_required_filter_still_requires_clarification(self):
        mod = _load_module()
        out = mod.evaluate_clarification(
            business_spec={},
            resolved={
                "needs_clarification": True,
                "clarification_reason": "hard_constraint_not_supported",
                "selected_report": "Stock Balance",
                "candidate_reports": [
                    {
                        "report_name": "Stock Balance",
                        "hard_blockers": ["unsupported_metric"],
                        "missing_required_filter_values": ["warehouse"],
                    }
                ],
            },
        )
        self.assertTrue(bool(out.get("should_clarify")))
        self.assertEqual(str(out.get("reason") or ""), "hard_constraint_not_supported")

    def test_latest_records_under_specified_triggers_record_type_clarification(self):
        mod = _load_module()
        out = mod.evaluate_clarification(
            business_spec={
                "task_class": "list_latest_records",
                "domain": "unknown",
                "metric": "",
                "dimensions": [],
                "subject": "invoice",
            },
            resolved={
                "needs_clarification": False,
                "clarification_reason": "",
                "hard_constraints": {
                    "domain": "unknown",
                    "metric": "",
                    "requested_dimensions": [],
                },
            },
        )
        self.assertTrue(bool(out.get("should_clarify")))
        self.assertEqual(str(out.get("reason") or ""), "no_candidate")
        self.assertIn("record type", str(out.get("question") or "").lower())

    def test_detail_projection_id_like_under_specified_triggers_record_type_clarification(self):
        mod = _load_module()
        out = mod.evaluate_clarification(
            business_spec={
                "task_class": "detail_projection",
                "domain": "unknown",
                "metric": "",
                "dimensions": [],
                "subject": "invoices",
                "output_contract": {"mode": "detail", "minimal_columns": ["invoice_number"]},
            },
            resolved={
                "needs_clarification": False,
                "clarification_reason": "",
                "hard_constraints": {
                    "domain": "unknown",
                    "metric": "",
                    "requested_dimensions": [],
                },
            },
        )
        self.assertTrue(bool(out.get("should_clarify")))
        self.assertEqual(str(out.get("reason") or ""), "no_candidate")


if __name__ == "__main__":
    unittest.main()
