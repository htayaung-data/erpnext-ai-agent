from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from semantic_assertions import evaluate_case_assertions
from run_phase6_canary_uat import pass_rule


class ComparisonReplaySemanticsTests(unittest.TestCase):
    def test_comparison_case_uses_manifest_behavior_class_for_required_assertions(self) -> None:
        actual = {
            "assistant_title": "Sales Analytics",
            "assistant_type": "report_table",
            "assistant_text": "",
            "pending_mode": None,
            "clarification": False,
            "rows": 1,
            "columns": 3,
            "column_labels": ["Territory", "Yangon", "Mandalay"],
            "quality_failed_check_ids": [],
            "result_quality_gate": {"failed_checks": [], "verdict": "PASS"},
            "expected_behavior_class": "comparison",
            "expected_manifest_expected": {
                "comparison_contract": {
                    "expected_title": "Sales Analytics",
                    "shape_mode": "side_by_side_entities",
                    "entity_count": 2,
                    "required_label_groups": [["territory", "metric"], ["yangon"], ["mandalay"]],
                }
            },
            "business_request_spec": {
                "task_class": "comparison",
                "task_type": "comparison",
                "metric": "revenue",
                "group_by": ["territory"],
                "domain": "sales",
                "filters": {
                    "_comparison_rule": {
                        "time_structure": "same_period",
                        "compared_values": ["Yangon", "Mandalay"],
                    }
                },
                "output_contract": {"mode": "comparison"},
            },
        }
        semantic = evaluate_case_assertions("CMPC-01", actual)
        self.assertTrue(bool(semantic.get("required_pass")))
        self.assertEqual(semantic.get("assertions", {}).get("dimension_alignment_pass"), True)
        self.assertEqual(semantic.get("assertions", {}).get("metric_alignment_pass"), True)

    def test_comparison_pass_rule_accepts_manifest_declared_comparison_case(self) -> None:
        actual = {
            "assistant_title": "Sales Analytics",
            "assistant_type": "report_table",
            "assistant_text": "",
            "pending_mode": None,
            "clarification": False,
            "rows": 1,
            "columns": 3,
            "column_labels": ["Territory", "Yangon", "Mandalay"],
            "quality_failed_check_ids": [],
            "result_quality_gate": {"failed_checks": [], "verdict": "PASS"},
            "expected_behavior_class": "comparison",
            "expected_manifest_expected": {
                "metric": "revenue",
                "group_by": ["territory"],
                "output_mode": "comparison",
                "comparison_contract": {
                    "expected_title": "Sales Analytics",
                    "shape_mode": "side_by_side_entities",
                    "entity_count": 2,
                    "required_label_groups": [["territory", "metric"], ["yangon"], ["mandalay"]],
                },
            },
            "expected_manifest_tags": ["comparison", "sales", "territory", "same_period"],
            "business_request_spec": {
                "task_class": "comparison",
                "task_type": "comparison",
                "metric": "revenue",
                "group_by": ["territory"],
                "domain": "sales",
                "filters": {
                    "_comparison_rule": {
                        "time_structure": "same_period",
                        "compared_values": ["Yangon", "Mandalay"],
                    }
                },
                "output_contract": {"mode": "comparison"},
            },
        }
        semantic = evaluate_case_assertions("CMPC-01", actual)
        ok, note = pass_rule("CMPC-01", actual, semantic)
        self.assertTrue(ok)
        self.assertEqual(note, "")

    def test_comparison_clarification_case_accepts_blocker_question_by_behavior_class(self) -> None:
        actual = {
            "assistant_type": "text",
            "assistant_text": "Which business measure should I use for the comparison?",
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
            "expected_behavior_class": "clarification_blocker",
        }
        semantic = evaluate_case_assertions("CMPC-11", actual)
        ok, note = pass_rule("CMPC-11", actual, semantic)
        self.assertTrue(ok)
        self.assertEqual(note, "")

    def test_comparison_case_fails_wrong_visible_report_title(self) -> None:
        actual = {
            "assistant_title": "Sales Payment Summary",
            "assistant_type": "report_table",
            "assistant_text": "",
            "pending_mode": None,
            "clarification": False,
            "rows": 1,
            "columns": 3,
            "column_labels": ["Territory", "Yangon", "Mandalay"],
            "quality_failed_check_ids": [],
            "result_quality_gate": {"failed_checks": [], "verdict": "PASS"},
            "expected_behavior_class": "comparison",
            "expected_manifest_expected": {
                "comparison_contract": {
                    "expected_title": "Sales Analytics",
                    "shape_mode": "side_by_side_entities",
                    "entity_count": 2,
                    "required_label_groups": [["territory", "metric"], ["yangon"], ["mandalay"]],
                }
            },
            "expected_manifest_tags": ["comparison", "sales", "territory", "same_period"],
            "business_request_spec": {
                "task_class": "comparison",
                "task_type": "comparison",
                "domain": "sales",
                "metric": "revenue",
                "group_by": ["territory"],
                "filters": {
                    "_comparison_rule": {
                        "time_structure": "same_period",
                        "compared_values": ["Yangon", "Mandalay"],
                    }
                },
                "output_contract": {"mode": "comparison"},
            },
        }
        semantic = evaluate_case_assertions("CMPC-01", actual)
        self.assertFalse(bool(semantic.get("required_pass")))
        self.assertEqual(semantic.get("assertions", {}).get("report_alignment_pass"), False)

    def test_same_period_comparison_case_fails_non_comparison_grade_shape(self) -> None:
        actual = {
            "assistant_title": "Supplier Ledger Summary",
            "assistant_type": "report_table",
            "assistant_text": "",
            "pending_mode": None,
            "clarification": False,
            "rows": 2,
            "columns": 2,
            "column_labels": ["Supplier", "Purchase Amount"],
            "quality_failed_check_ids": [],
            "result_quality_gate": {"failed_checks": [], "verdict": "PASS"},
            "expected_behavior_class": "comparison",
            "expected_manifest_expected": {
                "comparison_contract": {
                    "expected_title": "Supplier Ledger Summary",
                    "shape_mode": "side_by_side_entities",
                    "entity_count": 2,
                    "required_label_groups": [["supplier", "metric"], ["sunflower accessories co"], ["golden dragon trading co. ltd"]],
                }
            },
            "expected_manifest_tags": ["comparison", "purchasing", "supplier", "same_period"],
            "business_request_spec": {
                "task_class": "comparison",
                "task_type": "comparison",
                "domain": "purchasing",
                "metric": "purchase_amount",
                "group_by": ["supplier"],
                "filters": {
                    "_comparison_rule": {
                        "time_structure": "same_period",
                        "compared_values": ["Sunflower Accessories Co.", "Golden Dragon Trading Co. Ltd."],
                    }
                },
                "output_contract": {"mode": "comparison"},
            },
        }
        semantic = evaluate_case_assertions("CMPC-06", actual)
        self.assertFalse(bool(semantic.get("required_pass")))
        self.assertEqual(semantic.get("assertions", {}).get("output_shape_pass"), False)

    def test_month_over_month_case_fails_without_period_semantics(self) -> None:
        actual = {
            "assistant_title": "Sales Analytics",
            "assistant_type": "report_table",
            "assistant_text": "",
            "pending_mode": None,
            "clarification": False,
            "rows": 1,
            "columns": 2,
            "column_labels": ["Territory", "Revenue"],
            "quality_failed_check_ids": [],
            "result_quality_gate": {"failed_checks": [], "verdict": "PASS"},
            "expected_behavior_class": "comparison",
            "expected_manifest_expected": {
                "comparison_contract": {
                    "expected_title": "Sales Analytics",
                    "shape_mode": "period_comparison",
                    "minimum_rows": 2,
                    "allow_single_row_with_labels": True,
                    "required_label_groups": [
                        ["month", "period"],
                        ["revenue", "current"],
                        ["previous", "delta", "change", "difference", "growth", "mom"],
                    ],
                }
            },
            "expected_manifest_tags": ["comparison", "sales", "territory", "month_over_month"],
            "business_request_spec": {
                "task_class": "comparison",
                "task_type": "comparison",
                "domain": "sales",
                "metric": "revenue",
                "group_by": ["territory"],
                "filters": {
                    "_comparison_rule": {
                        "time_structure": "month_over_month",
                        "compared_values": [],
                    }
                },
                "output_contract": {"mode": "comparison"},
            },
        }
        semantic = evaluate_case_assertions("CMPC-09", actual)
        self.assertFalse(bool(semantic.get("required_pass")))
        self.assertEqual(semantic.get("assertions", {}).get("output_shape_pass"), False)

    def test_period_comparison_case_fails_when_redundant_total_metric_column_is_present(self) -> None:
        actual = {
            "assistant_title": "Sales Analytics",
            "assistant_type": "report_table",
            "assistant_text": "",
            "pending_mode": None,
            "clarification": False,
            "rows": 1,
            "columns": 4,
            "column_labels": ["Territory", "Revenue", "Feb 2026", "Mar 2026"],
            "quality_failed_check_ids": [],
            "result_quality_gate": {"failed_checks": [], "verdict": "PASS"},
            "expected_behavior_class": "comparison",
            "expected_manifest_expected": {
                "comparison_contract": {
                    "expected_title": "Sales Analytics",
                    "shape_mode": "period_comparison",
                    "minimum_rows": 1,
                    "allow_single_row_with_labels": True,
                    "required_label_groups": [["territory"], ["feb 2026"], ["mar 2026"]],
                    "forbidden_label_groups": [["revenue"]],
                }
            },
            "expected_manifest_tags": ["comparison", "sales", "territory", "monthly_period_vs_period"],
            "business_request_spec": {
                "task_class": "comparison",
                "task_type": "comparison",
                "domain": "sales",
                "metric": "revenue",
                "group_by": ["territory"],
                "filters": {
                    "_comparison_rule": {
                        "time_structure": "monthly_period_vs_period",
                        "month_refs": [
                            {"month_name": "march", "year": 2026, "label": "Mar 2026"},
                            {"month_name": "february", "year": 2026, "label": "Feb 2026"},
                        ],
                    }
                },
                "output_contract": {"mode": "comparison"},
            },
        }
        semantic = evaluate_case_assertions("CMPC-08", actual)
        self.assertFalse(bool(semantic.get("required_pass")))
        self.assertEqual(semantic.get("assertions", {}).get("output_shape_pass"), False)

    def test_comparison_case_fails_without_declared_comparison_contract(self) -> None:
        actual = {
            "assistant_title": "Sales Analytics",
            "assistant_type": "report_table",
            "assistant_text": "",
            "pending_mode": None,
            "clarification": False,
            "rows": 2,
            "columns": 2,
            "column_labels": ["Territory", "Revenue"],
            "quality_failed_check_ids": [],
            "result_quality_gate": {"failed_checks": [], "verdict": "PASS"},
            "expected_behavior_class": "comparison",
            "expected_manifest_expected": {},
            "business_request_spec": {
                "task_class": "comparison",
                "task_type": "comparison",
                "metric": "revenue",
                "group_by": ["territory"],
                "domain": "sales",
                "output_contract": {"mode": "comparison"},
            },
        }
        semantic = evaluate_case_assertions("CMPC-01", actual)
        self.assertFalse(bool(semantic.get("required_pass")))
        self.assertEqual(semantic.get("assertions", {}).get("report_alignment_pass"), False)
        self.assertEqual(semantic.get("assertions", {}).get("output_shape_pass"), False)


if __name__ == "__main__":
    unittest.main()
