from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from semantic_assertions import evaluate_case_assertions
from run_phase6_canary_uat import pass_rule


class ContributionShareReplaySemanticsTests(unittest.TestCase):
    def test_customer_contribution_case_is_treated_as_full_semantic_case(self) -> None:
        actual = {
            "assistant_type": "report_table",
            "assistant_text": "",
            "pending_mode": None,
            "clarification": False,
            "rows": 2,
            "columns": 3,
            "column_labels": ["Customer", "Revenue", "Contribution Share"],
            "quality_failed_check_ids": [],
            "result_quality_gate": {"failed_checks": [], "verdict": "PASS"},
        }
        semantic = evaluate_case_assertions("CSC-01", actual)
        self.assertTrue(bool(semantic.get("required_pass")))
        self.assertEqual(semantic.get("assertions", {}).get("dimension_alignment_pass"), True)
        self.assertEqual(semantic.get("assertions", {}).get("metric_alignment_pass"), True)

    def test_customer_contribution_pass_rule_accepts_contribution_share_table(self) -> None:
        actual = {
            "assistant_type": "report_table",
            "assistant_text": "",
            "pending_mode": None,
            "clarification": False,
            "rows": 2,
            "columns": 3,
            "column_labels": ["Customer", "Revenue", "Contribution Share"],
            "quality_failed_check_ids": [],
            "result_quality_gate": {"failed_checks": [], "verdict": "PASS"},
        }
        semantic = evaluate_case_assertions("CSC-01", actual)
        ok, note = pass_rule("CSC-01", actual, semantic)
        self.assertTrue(ok)
        self.assertEqual(note, "")

    def test_contribution_clarification_case_accepts_single_blocker_question(self) -> None:
        actual = {
            "assistant_type": "text",
            "assistant_text": "Which business measure should I use for the contribution share?",
            "pending_mode": "planner_clarify",
            "clarification": True,
            "rows": 0,
            "columns": 0,
            "column_labels": [],
            "quality_failed_check_ids": ["required_filter_missing"],
            "result_quality_gate": {
                "failed_checks": [{"id": "required_filter_missing"}],
                "verdict": "PENDING_CLARIFICATION",
            },
            "pending_state": {"options": ["revenue", "purchase amount"]},
        }
        semantic = evaluate_case_assertions("CSU-01", actual)
        ok, note = pass_rule("CSU-01", actual, semantic)
        self.assertTrue(ok)
        self.assertEqual(note, "")


if __name__ == "__main__":
    unittest.main()
