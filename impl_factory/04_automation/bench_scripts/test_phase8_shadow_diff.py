from __future__ import annotations

import unittest

from phase8_shadow_diff import build_shadow_diff


class Phase8ShadowDiffTests(unittest.TestCase):
    def test_shadow_diff_counts_improved_and_regressed(self):
        v2 = {
            "results": [
                {"id": "A", "pass": False, "actual": {"assistant_type": "text", "pending_mode": "planner_clarify", "rows": 0}},
                {"id": "B", "pass": True, "actual": {"assistant_type": "report_table", "pending_mode": None, "rows": 2}},
            ]
        }
        v3 = {
            "results": [
                {"id": "A", "pass": True, "actual": {"assistant_type": "report_table", "pending_mode": None, "rows": 3}},
                {"id": "B", "pass": False, "actual": {"assistant_type": "text", "pending_mode": "need_filters", "rows": 0}},
            ]
        }
        out = build_shadow_diff(v2, v3)
        summary = out.get("summary") or {}
        self.assertEqual(summary.get("improved"), 1)
        self.assertEqual(summary.get("regressed"), 1)
        self.assertEqual(summary.get("total_cases"), 2)


if __name__ == "__main__":
    unittest.main()

