from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/constraint_engine.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_constraint_engine_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load v7 constraint engine module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7ConstraintEngineTests(unittest.TestCase):
    def test_build_constraint_set_infers_domain_without_turning_unknown_filter_key_into_hard_kind(self):
        mod = _load_module()
        spec = {
            "domain": "unknown",
            "subject": "Top 5 by revenue last month",
            "metric": "revenue",
            "task_type": "ranking",
            "group_by": ["Customer"],
            "dimensions": [],
            "filters": {"cost_center": "Main - MMOB"},
            "time_scope": {"mode": "relative", "value": "last_month"},
            "output_contract": {"mode": "top_n", "minimal_columns": []},
        }
        out = mod.build_constraint_set(business_spec=spec, topic_state={})
        self.assertEqual(str(out.get("domain") or ""), "sales")
        self.assertIn("customer", list(out.get("requested_dimensions") or []))
        self.assertNotIn("cost_center", list(out.get("hard_filter_kinds") or []))
        self.assertEqual(str(out.get("time_mode") or ""), "relative")

    def test_build_constraint_set_keeps_followup_bindings_from_topic_state(self):
        mod = _load_module()
        spec = {
            "domain": "unknown",
            "subject": "",
            "metric": "",
            "task_type": "detail",
            "filters": {},
            "group_by": [],
            "dimensions": [],
            "time_scope": {"mode": "none", "value": ""},
            "output_contract": {"mode": "detail", "minimal_columns": []},
        }
        topic_state = {
            "previous_topic_key": "topic_a",
            "active_topic": {"topic_key": "topic_b", "filters": {"company": "MMOB"}},
            "active_result": {"result_id": "result_123"},
        }
        out = mod.build_constraint_set(business_spec=spec, topic_state=topic_state)
        fb = out.get("followup_bindings") if isinstance(out.get("followup_bindings"), dict) else {}
        self.assertEqual(str(fb.get("previous_topic_key") or ""), "topic_a")
        self.assertEqual(str(fb.get("active_topic_key") or ""), "topic_b")
        self.assertEqual(str(fb.get("active_result_id") or ""), "result_123")
        af = out.get("active_filter_context") if isinstance(out.get("active_filter_context"), dict) else {}
        self.assertEqual(str(af.get("company") or ""), "MMOB")

    def test_build_constraint_set_infers_dimension_from_subject_when_missing(self):
        mod = _load_module()
        spec = {
            "domain": "unknown",
            "subject": "Top 5 products by received quantity last month",
            "metric": "received quantity",
            "task_type": "ranking",
            "group_by": [],
            "dimensions": [],
            "filters": {"company": "MMOB"},
            "time_scope": {"mode": "relative", "value": "last_month"},
            "output_contract": {"mode": "top_n", "minimal_columns": []},
        }
        out = mod.build_constraint_set(business_spec=spec, topic_state={})
        req_dims = [str(x) for x in list(out.get("requested_dimensions") or [])]
        self.assertIn("item", req_dims)

    def test_build_constraint_set_infers_metric_from_subject_when_missing_metric_field(self):
        mod = _load_module()
        spec = {
            "domain": "unknown",
            "subject": "Top 5 products by received quantity last month",
            "metric": "",
            "task_type": "ranking",
            "group_by": [],
            "dimensions": [],
            "filters": {"company": "MMOB"},
            "time_scope": {"mode": "relative", "value": "last_month"},
            "output_contract": {"mode": "top_n", "minimal_columns": []},
        }
        out = mod.build_constraint_set(business_spec=spec, topic_state={})
        self.assertEqual(str(out.get("metric") or ""), "received_quantity")
        self.assertEqual(str(out.get("domain") or ""), "purchasing")

    def test_build_constraint_set_keeps_task_class_and_latest_sort_intent(self):
        mod = _load_module()
        spec = {
            "domain": "unknown",
            "subject": "show latest invoices",
            "metric": "latest",
            "task_type": "ranking",
            "task_class": "list_latest_records",
            "group_by": [],
            "dimensions": [],
            "filters": {"company": "MMOB"},
            "time_scope": {"mode": "relative", "value": "this_month"},
            "top_n": 7,
            "output_contract": {"mode": "top_n", "minimal_columns": []},
        }
        out = mod.build_constraint_set(business_spec=spec, topic_state={})
        self.assertEqual(str(out.get("task_class") or ""), "list_latest_records")
        self.assertEqual(str(out.get("sort_intent") or ""), "latest_desc")
        self.assertEqual(int(out.get("requested_limit") or 0), 7)

    def test_build_constraint_set_does_not_make_unknown_filter_key_hard_blocker(self):
        mod = _load_module()
        spec = {
            "domain": "operations",
            "subject": "open requests",
            "metric": "open requests",
            "task_type": "detail",
            "filters": {"production_stage": "Cutting"},
            "group_by": [],
            "dimensions": [],
            "time_scope": {"mode": "none", "value": ""},
            "output_contract": {"mode": "detail", "minimal_columns": []},
        }
        out = mod.build_constraint_set(business_spec=spec, topic_state={})
        self.assertNotIn("production_stage", list(out.get("hard_filter_kinds") or []))

    def test_build_constraint_set_does_not_treat_unknown_subject_as_metric(self):
        mod = _load_module()
        spec = {
            "domain": "unknown",
            "subject": "invoice",
            "metric": "",
            "task_type": "detail",
            "task_class": "list_latest_records",
            "group_by": [],
            "dimensions": [],
            "filters": {},
            "time_scope": {"mode": "none", "value": ""},
            "top_n": 7,
            "output_contract": {"mode": "top_n", "minimal_columns": []},
        }
        out = mod.build_constraint_set(business_spec=spec, topic_state={})
        self.assertEqual(str(out.get("metric") or ""), "")
        self.assertEqual(str(out.get("sort_intent") or ""), "latest_desc")


if __name__ == "__main__":
    unittest.main()
