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

    def test_generate_business_request_spec_normalizes_contribution_share_class(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "ranking",
                "task_class": "analytical_read",
                "domain": "unknown",
                "subject": "customers",
                "metric": "revenue",
                "dimensions": ["customer"],
                "aggregation": "sum",
                "group_by": ["customer"],
                "time_scope": {"mode": "relative", "value": "last_month"},
                "filters": {},
                "top_n": 10,
                "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "revenue"]},
                "ambiguities": [],
                "needs_clarification": False,
                "clarification_question": "",
                "confidence": 0.8,
            }
            mod._load_session_context = lambda session_name: {
                "recent_messages": [],
                "last_result_meta": None,
                "has_last_result": False,
            }
            env = mod.generate_business_request_spec(
                message="Top 10 customers contribution share of total revenue last month",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            rule = filters.get("_contribution_rule") if isinstance(filters.get("_contribution_rule"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "contribution_share")
            self.assertEqual(str(spec.get("task_type") or ""), "ranking")
            self.assertEqual(str(spec.get("metric") or ""), "revenue")
            self.assertEqual(str(spec.get("domain") or ""), "sales")
            self.assertEqual(str(rule.get("metric") or ""), "revenue")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_contribution_share_without_dimension_sets_missing_dimension(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "unknown",
                "subject": "",
                "metric": "",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
                message="Show contribution share",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "contribution_share")
            self.assertEqual(str(filters.get("_contribution_missing_filter_kind") or ""), "contribution_metric")
            self.assertEqual(str(filters.get("_contribution_unsupported_reason") or ""), "")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_contribution_share_with_metric_but_no_dimension_sets_missing_dimension(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "unknown",
                "subject": "",
                "metric": "",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
                message="Show contribution share of total revenue",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            rule = filters.get("_contribution_rule") if isinstance(filters.get("_contribution_rule"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "contribution_share")
            self.assertEqual(str(rule.get("metric") or ""), "revenue")
            self.assertEqual(str(filters.get("_contribution_missing_filter_kind") or ""), "contribution_dimension")
            self.assertEqual(str(filters.get("_contribution_unsupported_reason") or ""), "")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_contribution_share_requires_metric_even_when_llm_infers_it(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "sales",
                "subject": "customers",
                "metric": "revenue",
                "dimensions": ["customer"],
                "aggregation": "none",
                "group_by": ["customer"],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
                message="Show contribution share",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "contribution_share")
            self.assertEqual(str(filters.get("_contribution_missing_filter_kind") or ""), "contribution_metric")
            self.assertEqual(str(filters.get("_contribution_unsupported_reason") or ""), "")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_contribution_share_requires_dimension_even_when_llm_infers_it(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "sales",
                "subject": "customers",
                "metric": "revenue",
                "dimensions": ["customer"],
                "aggregation": "none",
                "group_by": ["customer"],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
                message="Show contribution share of total revenue",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            rule = filters.get("_contribution_rule") if isinstance(filters.get("_contribution_rule"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "contribution_share")
            self.assertEqual(str(rule.get("metric") or ""), "revenue")
            self.assertEqual(str(filters.get("_contribution_missing_filter_kind") or ""), "contribution_dimension")
            self.assertEqual(str(filters.get("_contribution_unsupported_reason") or ""), "")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_marks_territory_share_as_unsupported_grouping(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "sales",
                "subject": "",
                "metric": "revenue",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "relative", "value": "last_month"},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
                message="Show revenue share by territory last month",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "contribution_share")
            self.assertEqual(str(filters.get("_contribution_unsupported_reason") or ""), "unsupported_grouping_not_supported")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_contribution_allowed_dimensions_are_contract_driven(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        orig_allowed_dims = getattr(mod, "task_class_allowed_dimensions", None)
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "sales",
                "subject": "",
                "metric": "revenue",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "relative", "value": "last_month"},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
            mod.task_class_allowed_dimensions = (
                lambda task_class: {"customer", "supplier", "item", "territory"}
                if str(task_class or "").strip().lower() == "contribution_share"
                else set()
            )
            env = mod.generate_business_request_spec(
                message="Show revenue share by territory last month",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "contribution_share")
            self.assertEqual(str(filters.get("_contribution_unsupported_reason") or ""), "")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session
            if orig_allowed_dims is not None:
                mod.task_class_allowed_dimensions = orig_allowed_dims

    def test_generate_business_request_spec_marks_concentrated_advisory_as_unsupported(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "sales",
                "subject": "customers",
                "metric": "revenue",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
                message="Which customers are too concentrated in revenue?",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "contribution_share")
            self.assertEqual(str(filters.get("_contribution_unsupported_reason") or ""), "advisory_analysis_not_supported")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_marks_share_comparison_as_unsupported(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "sales",
                "subject": "customers",
                "metric": "",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
                message="Compare customer share this month vs last month",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "contribution_share")
            self.assertEqual(str(filters.get("_contribution_unsupported_reason") or ""), "comparison_not_supported")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_does_not_hijack_plain_comparison_into_contribution(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "comparison",
                "task_class": "comparison",
                "domain": "sales",
                "subject": "sales",
                "metric": "revenue",
                "dimensions": ["territory"],
                "aggregation": "none",
                "group_by": ["territory"],
                "time_scope": {"mode": "relative", "value": "last_month"},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "comparison", "minimal_columns": []},
                "ambiguities": [],
                "needs_clarification": False,
                "clarification_question": "",
                "confidence": 0.8,
            }
            mod._load_session_context = lambda session_name: {
                "recent_messages": [],
                "last_result_meta": None,
                "has_last_result": False,
            }
            env = mod.generate_business_request_spec(
                message="Compare Yangon and Mandalay sales last month by territory",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            self.assertNotEqual(str(spec.get("task_class") or ""), "contribution_share")
            self.assertEqual(filters.get("_contribution_rule"), None)
            self.assertEqual(str(filters.get("_contribution_unsupported_reason") or ""), "")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_normalizes_incomplete_threshold_prompt(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "sales",
                "subject": "customers",
                "metric": "",
                "dimensions": ["customer"],
                "aggregation": "none",
                "group_by": ["customer"],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
                message="Show customers above threshold",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "threshold_exception_list")
            rule = spec.get("filters", {}).get("_threshold_rule") if isinstance(spec.get("filters"), dict) else {}
            self.assertFalse(bool(rule.get("value_present")))
            self.assertEqual(str(rule.get("comparator") or ""), "gt")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_normalizes_threshold_exception_class(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "finance",
                "subject": "customers",
                "metric": "outstanding amount",
                "dimensions": ["customer"],
                "aggregation": "none",
                "group_by": ["customer"],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": ["customer", "outstanding amount"]},
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
                message="Show customers with outstanding amount above 10,000,000",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "threshold_exception_list")
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            rule = filters.get("_threshold_rule") if isinstance(filters.get("_threshold_rule"), dict) else {}
            self.assertEqual(str(rule.get("metric") or ""), "outstanding_amount")
            self.assertEqual(str(rule.get("comparator") or ""), "gt")
            self.assertEqual(float(rule.get("value") or 0.0), 10000000.0)
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_parses_formatted_threshold_decimal_without_range_flag(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "finance",
                "subject": "customers",
                "metric": "outstanding amount",
                "dimensions": ["customer"],
                "aggregation": "none",
                "group_by": ["customer"],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": ["customer", "outstanding amount"]},
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
                message="Show customers with outstanding amount above 2,800,000.00",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            rule = filters.get("_threshold_rule") if isinstance(filters.get("_threshold_rule"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "threshold_exception_list")
            self.assertEqual(float(rule.get("value") or 0.0), 2800000.0)
            self.assertEqual(str(filters.get("_threshold_unsupported_reason") or ""), "")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_enriches_threshold_invoice_metric(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "unknown",
                "subject": "",
                "metric": "revenue",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
                message="Show overdue sales invoices above 5000000",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "threshold_exception_list")
            self.assertEqual(str(spec.get("metric") or ""), "invoice_amount")
            self.assertEqual(list(spec.get("group_by") or []), ["invoice"])
            self.assertEqual(str(spec.get("domain") or ""), "sales")
            rule = spec.get("filters", {}).get("_threshold_rule") if isinstance(spec.get("filters"), dict) else {}
            self.assertEqual(str(rule.get("metric") or ""), "invoice_amount")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_threshold_domain_uses_contract_mapping_without_sales_keyword(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        orig_domain_from_dimension = getattr(mod, "domain_from_dimension", None)
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "unknown",
                "subject": "",
                "metric": "revenue",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
            mod.domain_from_dimension = (
                lambda dim: "finance"
                if str(dim or "").strip().lower() == "invoice"
                else ""
            )
            env = mod.generate_business_request_spec(
                message="Show overdue invoices above 5000000",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "threshold_exception_list")
            self.assertEqual(str(spec.get("metric") or ""), "invoice_amount")
            self.assertEqual(str(spec.get("domain") or ""), "finance")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session
            if orig_domain_from_dimension is not None:
                mod.domain_from_dimension = orig_domain_from_dimension

    def test_generate_business_request_spec_enriches_threshold_item_metric_and_warehouse_filter(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        orig_extract = mod.extract_entity_filters_from_message
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "unknown",
                "subject": "",
                "metric": "",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
            mod.extract_entity_filters_from_message = lambda **kwargs: {
                "warehouse": "Yangon Main Warehouse - MMOB"
            }
            env = mod.generate_business_request_spec(
                message="Show items with stock below 20 in Main warehouse",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "threshold_exception_list")
            self.assertEqual(str(spec.get("metric") or ""), "stock_quantity")
            self.assertEqual(list(spec.get("group_by") or []), ["item"])
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            self.assertEqual(str(filters.get("warehouse") or ""), "Yangon Main Warehouse - MMOB")
            rule = filters.get("_threshold_rule") if isinstance(filters.get("_threshold_rule"), dict) else {}
            self.assertEqual(str(rule.get("metric") or ""), "stock_quantity")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session
            mod.extract_entity_filters_from_message = orig_extract

    def test_generate_business_request_spec_marks_missing_warehouse_for_item_stock_threshold(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "unknown",
                "subject": "",
                "metric": "",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
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
                message="Show items below 20",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "threshold_exception_list")
            self.assertEqual(str(filters.get("_threshold_missing_filter_kind") or ""), "warehouse")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_marks_threshold_range_as_unsupported_first_slice(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "finance",
                "subject": "customers",
                "metric": "outstanding amount",
                "dimensions": ["customer"],
                "aggregation": "none",
                "group_by": ["customer"],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": ["customer", "outstanding amount"]},
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
                message="Show customers above 10000000 but below 20000000 and grouped by territory",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            filters = spec.get("filters") if isinstance(spec.get("filters"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "threshold_exception_list")
            self.assertEqual(str(filters.get("_threshold_unsupported_reason") or ""), "range_threshold_not_supported")
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_keeps_latest_records_class_for_latest_record_cue(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "ranking",
                "task_class": "list_latest_records",
                "domain": "finance",
                "subject": "invoices",
                "metric": "invoice details",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {},
                "top_n": 7,
                "output_contract": {"mode": "top_n", "minimal_columns": ["invoice details"]},
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
                message="Show me the latest 7 Invoice",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "list_latest_records")
            output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
            self.assertEqual(list(output_contract.get("minimal_columns") or []), [])
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_pins_explicit_latest_purchase_doctype_from_message(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        orig_load_doctypes = mod._load_submittable_doctypes
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "list_latest_records",
                "domain": "unknown",
                "subject": "invoices",
                "metric": "invoice details",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {"doctype": "Sales Invoice"},
                "top_n": 0,
                "output_contract": {"mode": "top_n", "minimal_columns": ["invoice details"]},
                "ambiguities": [],
                "needs_clarification": False,
                "clarification_question": "",
                "confidence": 0.7,
            }
            mod._load_session_context = lambda session_name: {
                "recent_messages": [{"role": "assistant", "content": "Latest Sales Invoice"}],
                "last_result_meta": {"report_name": "Latest Sales Invoice", "columns": []},
                "has_last_result": True,
            }
            mod._load_submittable_doctypes = lambda: ["Sales Invoice", "Purchase Invoice"]
            env = mod.generate_business_request_spec(
                message="Show me the latest Purchase 7 Invoice",
                session_name="browser-session",
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            self.assertEqual(str(spec.get("task_class") or ""), "list_latest_records")
            self.assertEqual(str((spec.get("filters") or {}).get("doctype") or ""), "Purchase Invoice")
            self.assertEqual(str(spec.get("domain") or ""), "purchasing")
            self.assertEqual(int(spec.get("top_n") or 0), 7)
            self.assertEqual(str(spec.get("metric") or ""), "")
            self.assertEqual(list(spec.get("group_by") or []), [])
            self.assertEqual(list(spec.get("dimensions") or []), [])
            output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
            self.assertEqual(list(output_contract.get("minimal_columns") or []), [])
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session
            mod._load_submittable_doctypes = orig_load_doctypes

    def test_generate_business_request_spec_keeps_concrete_latest_record_identifier_projection(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "list_latest_records",
                "domain": "sales",
                "subject": "sales invoices",
                "metric": "",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {"doctype": "Sales Invoice"},
                "top_n": 7,
                "output_contract": {"mode": "top_n", "minimal_columns": ["invoice number"]},
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
                message="Show me the latest 7 Sales Invoice",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
            self.assertEqual(list(output_contract.get("minimal_columns") or []), ["invoice number"])
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session

    def test_generate_business_request_spec_suppresses_detail_constraint_metric_from_minimal_columns(self):
        mod = _load_module()
        orig_choose = mod.choose_business_request_spec
        orig_load_session = mod._load_session_context
        try:
            mod.choose_business_request_spec = lambda **kwargs: {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "operations",
                "subject": "material requests",
                "metric": "open requests",
                "dimensions": [],
                "aggregation": "none",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {"status": "open", "context": "production"},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": ["open requests"]},
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
                message="What are the open material requests for production",
                session_name=None,
                planner_plan=None,
            )
            spec = env.get("spec") if isinstance(env.get("spec"), dict) else {}
            output_contract = spec.get("output_contract") if isinstance(spec.get("output_contract"), dict) else {}
            self.assertEqual(list(output_contract.get("minimal_columns") or []), [])
        finally:
            mod.choose_business_request_spec = orig_choose
            mod._load_session_context = orig_load_session


if __name__ == "__main__":
    unittest.main()
