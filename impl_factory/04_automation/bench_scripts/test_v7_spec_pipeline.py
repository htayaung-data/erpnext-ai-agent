from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/spec_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_spec_pipeline_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load spec_pipeline module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7SpecPipelineTests(unittest.TestCase):
    def test_load_session_context_prefers_active_topic_report_over_stale_last_result(self):
        mod = _load_module()

        class _Message:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        stale_last_result = {
            "type": "last_result",
            "report_name": "Supplier Ledger Summary",
            "table": {
                "columns": [
                    {"fieldname": "party", "label": "Supplier", "fieldtype": "Link"},
                    {"fieldname": "invoiced_amount", "label": "Purchase Amount", "fieldtype": "Currency"},
                ]
            },
        }
        warehouse_report = {
            "type": "report_table",
            "report_name": "Warehouse Wise Stock Balance",
            "title": "Warehouse Wise Stock Balance",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
                "rows": [{"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399386000.0}],
            },
        }
        topic_state = {
            "type": "v7_topic_state",
            "state": {
                "active_result": {
                    "report_name": "Warehouse Wise Stock Balance",
                    "source_columns": [
                        {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                        {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                        {"fieldname": "company", "label": "Company", "fieldtype": "Link"},
                    ],
                }
            },
        }

        class _FakeSession:
            def get(self, key):
                if key == "messages":
                    return [
                        _Message("tool", mod.json.dumps(stale_last_result)),
                        _Message("assistant", mod.json.dumps(warehouse_report)),
                        _Message("tool", mod.json.dumps(topic_state)),
                    ]
                return []

        class _FakeFrappe:
            @staticmethod
            def get_doc(doctype, name):
                return _FakeSession()

        orig_frappe = mod.frappe
        try:
            mod.frappe = _FakeFrappe()
            ctx = mod._load_session_context("browser-session")
        finally:
            mod.frappe = orig_frappe

        last_meta = ctx.get("last_result_meta") if isinstance(ctx.get("last_result_meta"), dict) else {}
        self.assertEqual(str(last_meta.get("report_name") or ""), "Warehouse Wise Stock Balance")
        cols = [c for c in list(last_meta.get("columns") or []) if isinstance(c, dict)]
        self.assertEqual(
            [str(c.get("fieldname") or "").strip().lower() for c in cols],
            ["warehouse", "stock_balance", "company"],
        )

    def test_generate_business_request_spec_clears_invented_time_scope(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "ranking",
                "task_class": "analytical_read",
                "domain": "inventory",
                "subject": "warehouses",
                "metric": "stock balance",
                "dimensions": ["warehouse"],
                "aggregation": "sum",
                "group_by": ["warehouse"],
                "time_scope": {"mode": "relative", "value": "last_month"},
                "filters": {},
                "top_n": 3,
                "output_contract": {"mode": "top_n", "minimal_columns": ["warehouse", "stock balance"]},
                "ambiguities": ["transform_sort:asc"],
                "needs_clarification": False,
                "clarification_question": "",
                "confidence": 0.7,
            }
            mod._load_session_context = lambda session_name: {
                "recent_messages": [],
                "last_result_meta": None,
                "has_last_result": False,
            }
            env = mod.generate_business_request_spec(
                message="Lowest 3 warehouses by stock balance",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            self.assertEqual(spec.get("time_scope"), {"mode": "none", "value": ""})
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_keeps_explicit_time_scope(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "ranking",
                "task_class": "analytical_read",
                "domain": "purchasing",
                "subject": "suppliers",
                "metric": "purchase amount",
                "dimensions": ["supplier"],
                "aggregation": "sum",
                "group_by": ["supplier"],
                "time_scope": {"mode": "relative", "value": "last_month"},
                "filters": {},
                "top_n": 10,
                "output_contract": {"mode": "top_n", "minimal_columns": ["supplier", "purchase amount"]},
                "ambiguities": [],
                "needs_clarification": False,
                "clarification_question": "",
                "confidence": 0.7,
            }
            mod._load_session_context = lambda session_name: {
                "recent_messages": [],
                "last_result_meta": None,
                "has_last_result": False,
            }
            env = mod.generate_business_request_spec(
                message="Top 10 suppliers by purchase amount last month",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            self.assertEqual(spec.get("time_scope"), {"mode": "relative", "value": "last_month"})
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_suppresses_stale_last_result_meta_for_strong_explicit_read(self):
        mod = _load_module()
        captured = {}
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            def _fake_choose(**kwargs):
                captured.update(kwargs)
                return {
                    "intent": "READ",
                    "task_type": "ranking",
                    "task_class": "analytical_read",
                    "domain": "purchasing",
                    "subject": "suppliers",
                    "metric": "purchase amount",
                    "dimensions": ["supplier"],
                    "aggregation": "sum",
                    "group_by": ["supplier"],
                    "time_scope": {"mode": "relative", "value": "last_month"},
                    "filters": {},
                    "top_n": 10,
                    "output_contract": {"mode": "top_n", "minimal_columns": ["supplier", "purchase amount"]},
                    "ambiguities": [],
                    "needs_clarification": False,
                    "clarification_question": "",
                    "confidence": 0.7,
                }
            mod.choose_business_request_spec = _fake_choose
            mod._load_session_context = lambda session_name: {
                "recent_messages": [{"role": "user", "content": "Top 10 products by sold quantity last month"}],
                "last_result_meta": {"report_name": "Item-wise Sales Register", "columns": [{"fieldname": "item_code", "label": "Item"}]},
                "has_last_result": True,
            }
            mod.generate_business_request_spec(
                message="Top 10 suppliers by purchase amount last month",
                session_name="browser-session",
                planner_plan=None,
            )
            self.assertFalse(bool(captured.get("has_last_result")))
            self.assertIsNone(captured.get("last_result_meta"))
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_normalizes_latest_records_misclassification_for_explicit_ranking(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "ranking",
                "task_class": "list_latest_records",
                "domain": "inventory",
                "subject": "warehouses",
                "metric": "stock balance",
                "dimensions": ["warehouse"],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 3,
                "output_contract": {"mode": "top_n", "minimal_columns": ["stock balance", "warehouse"]},
                "ambiguities": ["transform_sort:desc"],
                "needs_clarification": False,
                "clarification_question": "",
                "confidence": 0.7,
            }
            mod._load_session_context = lambda session_name: {
                "recent_messages": [],
                "last_result_meta": None,
                "has_last_result": False,
            }
            env = mod.generate_business_request_spec(
                message="Top 3 warehouses by stock balance",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "analytical_read")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session


if __name__ == "__main__":
    unittest.main()
