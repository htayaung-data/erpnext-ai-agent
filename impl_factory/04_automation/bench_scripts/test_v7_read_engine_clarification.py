from __future__ import annotations

import importlib.util
import types
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/read_engine.py"


def _load_module():
    if "frappe" not in sys.modules:
        sys.modules["frappe"] = types.ModuleType("frappe")
    spec = importlib.util.spec_from_file_location("v7_read_engine_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load read_engine module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7ReadEngineClarificationTests(unittest.TestCase):
    def test_low_signal_read_spec_detection(self):
        mod = _load_module()
        self.assertTrue(
            bool(
                mod._is_low_signal_read_spec(
                    {
                        "intent": "READ",
                        "task_type": "detail",
                        "task_class": "analytical_read",
                        "subject": "show report",
                        "metric": "",
                        "filters": {},
                        "group_by": [],
                        "dimensions": [],
                        "time_scope": {"mode": "none", "value": ""},
                        "top_n": 0,
                        "output_contract": {"mode": "detail", "minimal_columns": []},
                    }
                )
            )
        )
        self.assertFalse(
            bool(
                mod._is_low_signal_read_spec(
                    {
                        "intent": "READ",
                        "task_type": "detail",
                        "task_class": "detail_projection",
                        "subject": "stock balance",
                        "metric": "stock balance",
                        "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
                        "group_by": ["item"],
                        "dimensions": ["item"],
                        "time_scope": {"mode": "relative", "value": "this_month"},
                        "top_n": 0,
                        "output_contract": {"mode": "detail", "minimal_columns": ["item", "stock balance"]},
                    }
                )
            )
        )

    def test_planner_clarify_accepts_index_switch_response(self):
        mod = _load_module()
        pending = {
            "mode": "planner_clarify",
            "base_question": "Show gross margin by item group for last month",
            "report_name": "Stock Analytics",
            "filters_so_far": {},
            "options": ["Switch to compatible report", "Keep current scope"],
            "option_actions": {
                "Switch to compatible report": "switch_report",
                "Keep current scope": "keep_current",
            },
            "clarification_round": 1,
        }
        out = mod._prepare_resume_from_pending(message="1", pending=pending)
        self.assertTrue(bool(out.get("active")))
        self.assertEqual(str(out.get("resume_message") or ""), str(pending.get("base_question") or ""))

    def test_planner_clarify_accepts_exact_keep_current_response(self):
        mod = _load_module()
        pending = {
            "mode": "planner_clarify",
            "base_question": "Show gross margin by item group for last month",
            "report_name": "Stock Analytics",
            "filters_so_far": {},
            "options": ["Switch to compatible report", "Keep current scope"],
            "option_actions": {
                "Switch to compatible report": "switch_report",
                "Keep current scope": "keep_current",
            },
            "clarification_round": 1,
        }
        out = mod._prepare_resume_from_pending(message="Keep current scope", pending=pending)
        self.assertFalse(bool(out.get("active")))
        payload = out.get("payload") if isinstance(out.get("payload"), dict) else {}
        self.assertEqual(str(payload.get("type") or ""), "text")
        self.assertTrue(bool(payload.get("_clear_pending_state")))

    def test_planner_clarify_free_text_refines_base_question(self):
        mod = _load_module()
        pending = {
            "mode": "planner_clarify",
            "base_question": "Show gross margin by item group for last month",
            "report_name": "Stock Analytics",
            "filters_so_far": {},
            "options": ["Switch to compatible report", "Keep current scope"],
            "option_actions": {
                "Switch to compatible report": "switch_report",
                "Keep current scope": "keep_current",
            },
            "clarification_round": 1,
        }
        out = mod._prepare_resume_from_pending(message="hmm", pending=pending)
        self.assertTrue(bool(out.get("active")))
        merged = str(out.get("resume_message") or "")
        self.assertIn("Show gross margin by item group for last month", merged)
        self.assertIn("hmm", merged)

    def test_planner_clarify_no_candidate_prefers_refinement_even_if_new_request(self):
        mod = _load_module()
        pending = {
            "mode": "planner_clarify",
            "base_question": "Show me the latest 7 Invoice",
            "clarification_reason": "no_candidate",
            "spec_so_far": {"task_class": "list_latest_records", "top_n": 7, "output_contract": {"mode": "top_n", "minimal_columns": []}},
            "options": ["Switch to compatible report", "Keep current scope"],
            "option_actions": {
                "Switch to compatible report": "switch_report",
                "Keep current scope": "keep_current",
            },
            "clarification_round": 1,
        }
        orig = mod._is_new_business_request_structured
        try:
            mod._is_new_business_request_structured = lambda **kwargs: True
            out = mod._prepare_resume_from_pending(message="Sales Invoice", pending=pending)
        finally:
            mod._is_new_business_request_structured = orig
        self.assertTrue(bool(out.get("active")))
        self.assertIn("Show me the latest 7 Sales Invoice", str(out.get("resume_message") or ""))
        self.assertIn("Sales Invoice", str(out.get("resume_message") or ""))

    def test_planner_clarify_no_candidate_metric_invoice_answer_resolves_latest_sales_invoice(self):
        mod = _load_module()

        class _FakeFrappe:
            @staticmethod
            def get_all(doctype, **kwargs):
                if doctype != "DocType":
                    return []
                return [
                    {"name": "Sales Invoice"},
                    {"name": "Purchase Invoice"},
                    {"name": "Sales Order"},
                ]

        mod.frappe = _FakeFrappe()
        mod._load_submittable_doctypes.cache_clear()
        pending = {
            "mode": "planner_clarify",
            "base_question": "Show me the Latest 7 Invoice",
            "clarification_reason": "no_candidate",
            "spec_so_far": {
                "task_class": "list_latest_records",
                "subject": "invoices",
                "metric": "invoice details",
                "domain": "finance",
                "top_n": 7,
                "output_contract": {"mode": "top_n", "minimal_columns": []},
            },
            "options": ["Switch to compatible report", "Keep current scope"],
            "option_actions": {
                "Switch to compatible report": "switch_report",
                "Keep current scope": "keep_current",
            },
            "clarification_round": 1,
        }
        out = mod._prepare_resume_from_pending(message="revenue Invoice", pending=pending)
        self.assertTrue(bool(out.get("active")))
        resumed = str(out.get("resume_message") or "")
        self.assertIn("latest 7 Sales Invoice", resumed)

    def test_planner_clarify_most_recent_variant_pins_explicit_doctype_even_when_task_class_drifted(self):
        mod = _load_module()
        orig_frappe = mod.frappe
        mod.frappe = None
        mod._load_submittable_doctypes.cache_clear()
        pending = {
            "mode": "planner_clarify",
            "base_question": "Show me the most recent 7 Invoice",
            "clarification_reason": "no_candidate",
            "spec_so_far": {
                "task_class": "detail_projection",
                "subject": "invoices",
                "metric": "invoice details",
                "domain": "finance",
                "top_n": 7,
                "output_contract": {"mode": "top_n", "minimal_columns": []},
            },
            "options": ["Switch to compatible report", "Keep current scope"],
            "option_actions": {
                "Switch to compatible report": "switch_report",
                "Keep current scope": "keep_current",
            },
            "clarification_round": 1,
        }
        try:
            out = mod._prepare_resume_from_pending(message="Sales Invoice", pending=pending)
        finally:
            mod.frappe = orig_frappe
            mod._load_submittable_doctypes.cache_clear()
        self.assertTrue(bool(out.get("active")))
        resumed = str(out.get("resume_message") or "")
        self.assertIn("latest 7 Sales Invoice", resumed)
        seed = out.get("plan_seed") if isinstance(out.get("plan_seed"), dict) else {}
        self.assertEqual(str(seed.get("task_class") or ""), "list_latest_records")
        self.assertEqual(str(seed.get("output_mode") or ""), "top_n")
        self.assertEqual(int(seed.get("top_n") or 0), 7)
        filters = seed.get("filters") if isinstance(seed.get("filters"), dict) else {}
        self.assertEqual(str(filters.get("doctype") or ""), "Sales Invoice")

    def test_merge_pinned_filters_overrides_ambiguous_raw_filter(self):
        mod = _load_module()
        spec_obj = {"filters": {"warehouse": "MMOB", "company": "MMOB"}}
        plan_seed = {"filters": {"warehouse": "Yangon Main Warehouse - MMOB"}}
        out = mod._merge_pinned_filters_into_spec(spec_obj=spec_obj, plan_seed=plan_seed)
        filters = out.get("filters") if isinstance(out.get("filters"), dict) else {}
        self.assertEqual(str(filters.get("warehouse") or ""), "Yangon Main Warehouse - MMOB")
        self.assertEqual(str(filters.get("company") or ""), "MMOB")

    def test_merge_plan_seed_pins_task_shape_for_resume(self):
        mod = _load_module()
        spec_obj = {
            "task_class": "analytical_read",
            "top_n": 0,
            "output_contract": {"mode": "detail", "minimal_columns": []},
            "filters": {},
        }
        plan_seed = {
            "task_class": "list_latest_records",
            "top_n": 7,
            "output_mode": "top_n",
            "minimal_columns": ["invoice number"],
        }
        out = mod._merge_pinned_filters_into_spec(spec_obj=spec_obj, plan_seed=plan_seed)
        self.assertEqual(str(out.get("task_class") or ""), "list_latest_records")
        self.assertEqual(int(out.get("top_n") or 0), 7)
        oc = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
        self.assertEqual(str(oc.get("mode") or ""), "top_n")
        self.assertEqual(list(oc.get("minimal_columns") or []), ["invoice number"])

    def test_merge_plan_seed_skips_generic_latest_record_projection_hints(self):
        mod = _load_module()
        spec_obj = {
            "task_class": "analytical_read",
            "top_n": 0,
            "output_contract": {"mode": "detail", "minimal_columns": []},
            "filters": {},
        }
        plan_seed = {
            "task_class": "list_latest_records",
            "top_n": 7,
            "output_mode": "top_n",
            "minimal_columns": ["invoice details"],
        }
        out = mod._merge_pinned_filters_into_spec(spec_obj=spec_obj, plan_seed=plan_seed)
        oc = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
        self.assertEqual(str(out.get("task_class") or ""), "list_latest_records")
        self.assertEqual(str(oc.get("mode") or ""), "top_n")
        self.assertEqual(list(oc.get("minimal_columns") or []), [])

    def test_load_last_result_preserves_visible_table_and_hidden_source_snapshot(self):
        mod = _load_module()

        class _Message:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        assistant_payload = {
            "type": "report_table",
            "report_name": "Item-wise Sales Register",
            "title": "Item-wise Sales Register",
            "table": {
                "columns": [
                    {"fieldname": "item_code", "label": "Item"},
                    {"fieldname": "amount", "label": "Revenue"},
                ],
                "rows": [{"item_code": "A", "amount": "10.00"}],
            },
            "_source_columns": [
                {"fieldname": "item_code", "label": "Item Code", "fieldtype": "Link"},
                {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data"},
                {"fieldname": "amount", "label": "Amount", "fieldtype": "Currency"},
            ],
            "_source_table": {
                "columns": [
                    {"fieldname": "item_code", "label": "Item Code"},
                    {"fieldname": "item_name", "label": "Item Name"},
                    {"fieldname": "amount", "label": "Amount"},
                ],
                "rows": [{"item_code": "A", "item_name": "Alpha", "amount": 10}],
            },
            "_contribution_rule_applied": True,
            "_contribution_rule": {
                "metric": "revenue",
                "basis": "of_total",
                "contribution_terms": ["share_of_total", "contribution_share"],
            },
            "_contribution_metric": "revenue",
            "_contribution_metric_fieldname": "amount",
            "_contribution_share_fieldname": "contribution_share",
            "_contribution_primary_dimension": "item",
            "_contribution_total_value": 10.0,
        }
        topic_state = {
            "type": "v7_topic_state",
            "state": {
                "active_result": {
                    "scaled_unit": "million",
                    "output_mode": "top_n",
                }
            },
        }

        class _FakeSession:
            def get(self, key):
                if key == "messages":
                    return [
                        _Message("assistant", mod.json.dumps(assistant_payload)),
                        _Message("tool", mod.json.dumps(topic_state)),
                    ]
                return []

        class _FakeFrappe:
            @staticmethod
            def get_doc(doctype, name):
                return _FakeSession()

        mod.frappe = _FakeFrappe()
        out = mod._load_last_result_payload(session_name="browser-session")
        table = out.get("table") if isinstance(out.get("table"), dict) else {}
        cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
        rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
        labels = [str(c.get("label") or "").strip().lower() for c in cols]
        self.assertEqual(labels, ["item", "revenue"])
        self.assertEqual(str(rows[0].get("item_code") or ""), "A")
        source_table = out.get("_source_table") if isinstance(out.get("_source_table"), dict) else {}
        source_rows = [r for r in list(source_table.get("rows") or []) if isinstance(r, dict)]
        self.assertEqual(str(source_rows[0].get("item_name") or ""), "Alpha")
        self.assertEqual(str(out.get("_scaled_unit") or ""), "million")
        self.assertEqual(str(out.get("_output_mode") or ""), "top_n")
        self.assertTrue(bool(out.get("_contribution_rule_applied")))
        self.assertEqual(str(out.get("_contribution_metric") or ""), "revenue")
        self.assertEqual(str(out.get("_contribution_primary_dimension") or ""), "item")
        self.assertEqual(str(out.get("_contribution_metric_fieldname") or ""), "amount")

    def test_load_last_result_prefers_payload_matching_active_report(self):
        mod = _load_module()

        class _Message:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        supplier_payload = {
            "type": "report_table",
            "report_name": "Supplier Ledger Summary",
            "title": "Supplier Ledger Summary",
            "table": {
                "columns": [{"fieldname": "party", "label": "Supplier"}, {"fieldname": "closing_balance", "label": "Outstanding Amount"}],
                "rows": [{"party": "Supplier A", "closing_balance": 100.0}],
            },
        }
        warehouse_payload = {
            "type": "report_table",
            "report_name": "Warehouse Wise Stock Balance",
            "title": "Warehouse Wise Stock Balance",
            "table": {
                "columns": [{"fieldname": "warehouse", "label": "Warehouse"}, {"fieldname": "stock_balance", "label": "Stock Balance"}],
                "rows": [{"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399386000.0}],
            },
        }
        topic_state = {
            "type": "v7_topic_state",
            "state": {
                "active_result": {
                    "report_name": "Warehouse Wise Stock Balance",
                    "output_mode": "top_n",
                }
            },
        }

        class _FakeSession:
            def get(self, key):
                if key == "messages":
                    return [
                        _Message("assistant", mod.json.dumps(supplier_payload)),
                        _Message("assistant", mod.json.dumps(warehouse_payload)),
                        _Message("tool", mod.json.dumps(topic_state)),
                    ]
                return []

        class _FakeFrappe:
            @staticmethod
            def get_doc(doctype, name):
                return _FakeSession()

        mod.frappe = _FakeFrappe()
        out = mod._load_last_result_payload(session_name="browser-session")
        self.assertEqual(str(out.get("report_name") or ""), "Warehouse Wise Stock Balance")
        self.assertEqual(str(out.get("_output_mode") or ""), "top_n")

    def test_load_last_result_prefers_active_report_over_newer_mismatched_assistant_payload(self):
        mod = _load_module()

        class _Message:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        warehouse_payload = {
            "type": "report_table",
            "report_name": "Warehouse Wise Stock Balance",
            "title": "Warehouse Wise Stock Balance",
            "table": {
                "columns": [{"fieldname": "warehouse", "label": "Warehouse"}, {"fieldname": "stock_balance", "label": "Stock Balance"}],
                "rows": [{"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399386000.0}],
            },
        }
        supplier_payload = {
            "type": "report_table",
            "report_name": "Supplier Ledger Summary",
            "title": "Supplier Ledger Summary",
            "table": {
                "columns": [{"fieldname": "party", "label": "Supplier"}, {"fieldname": "closing_balance", "label": "Outstanding Amount"}],
                "rows": [{"party": "Supplier A", "closing_balance": 100.0}],
            },
        }
        topic_state = {
            "type": "v7_topic_state",
            "state": {
                "active_result": {
                    "report_name": "Warehouse Wise Stock Balance",
                    "output_mode": "top_n",
                }
            },
        }

        class _FakeSession:
            def get(self, key):
                if key == "messages":
                    return [
                        _Message("assistant", mod.json.dumps(warehouse_payload)),
                        _Message("assistant", mod.json.dumps(supplier_payload)),
                        _Message("tool", mod.json.dumps(topic_state)),
                    ]
                return []

        class _FakeFrappe:
            @staticmethod
            def get_doc(doctype, name):
                return _FakeSession()

        mod.frappe = _FakeFrappe()
        out = mod._load_last_result_payload(session_name="browser-session")
        self.assertEqual(str(out.get("report_name") or ""), "Warehouse Wise Stock Balance")
        self.assertEqual(str(out.get("_output_mode") or ""), "top_n")

    def test_load_last_result_does_not_overlay_stale_scaled_meta_from_different_report(self):
        mod = _load_module()

        class _Message:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        warehouse_payload = {
            "type": "report_table",
            "report_name": "Warehouse Wise Stock Balance",
            "title": "Warehouse Wise Stock Balance",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse"},
                    {"fieldname": "stock_balance", "label": "Stock Balance"},
                ],
                "rows": [{"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399386000.0}],
            },
        }
        topic_state = {
            "type": "v7_topic_state",
            "state": {
                "active_result": {
                    "report_name": "Supplier Ledger Summary",
                    "scaled_unit": "million",
                    "output_mode": "top_n",
                }
            },
        }

        class _FakeSession:
            def get(self, key):
                if key == "messages":
                    return [
                        _Message("assistant", mod.json.dumps(warehouse_payload)),
                        _Message("tool", mod.json.dumps(topic_state)),
                    ]
                return []

        class _FakeFrappe:
            @staticmethod
            def get_doc(doctype, name):
                return _FakeSession()

        mod.frappe = _FakeFrappe()
        out = mod._load_last_result_payload(session_name="browser-session")
        self.assertEqual(str(out.get("report_name") or ""), "Warehouse Wise Stock Balance")
        self.assertEqual(str(out.get("_scaled_unit") or ""), "")

    def test_apply_requested_entity_row_filters_reduces_to_selected_warehouse(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [{"fieldname": "name", "label": "Warehouse"}, {"fieldname": "stock_balance", "label": "Stock Balance"}],
                "rows": [
                    {"name": "All Warehouses - MMOB", "stock_balance": 618277000},
                    {"name": "Yangon Main Warehouse - MMOB", "stock_balance": 399386000},
                    {"name": "Mandalay Warehouse - MMOB", "stock_balance": 166006000},
                ],
            },
        }
        spec_obj = {"filters": {"warehouse": "Yangon Main Warehouse"}}
        out = mod._apply_requested_entity_row_filters(payload=payload, business_spec=spec_obj)
        table = out.get("table") if isinstance(out.get("table"), dict) else {}
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        self.assertEqual(len(rows), 1)
        self.assertEqual(str(rows[0].get("name") or ""), "Yangon Main Warehouse - MMOB")
        self.assertTrue(bool(out.get("_entity_row_filter_applied")))

    def test_apply_requested_entity_row_filters_supports_entity_lists(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [{"fieldname": "territory", "label": "Territory"}, {"fieldname": "revenue", "label": "Revenue"}],
                "rows": [
                    {"territory": "Yangon", "revenue": 28754000},
                    {"territory": "Mandalay", "revenue": 18060000},
                    {"territory": "Bago", "revenue": 17168000},
                ],
            },
        }
        spec_obj = {"filters": {"territory": ["Yangon", "Mandalay"]}}
        out = mod._apply_requested_entity_row_filters(payload=payload, business_spec=spec_obj)
        table = out.get("table") if isinstance(out.get("table"), dict) else {}
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        self.assertEqual(
            [str(row.get("territory") or "") for row in rows if isinstance(row, dict)],
            ["Yangon", "Mandalay"],
        )
        self.assertTrue(bool(out.get("_entity_row_filter_applied")))

    def test_apply_requested_entity_row_filters_matches_supplier_names_with_punctuation_variants(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [{"fieldname": "supplier", "label": "Supplier"}, {"fieldname": "purchase_amount", "label": "Purchase Amount"}],
                "rows": [
                    {"supplier": "Golden Dragon Trading Co. Ltd.", "purchase_amount": 172434600},
                    {"supplier": "Sunflower Accessories Co.", "purchase_amount": 132960500},
                    {"supplier": "Myanmar Tech Import Services", "purchase_amount": 108942300},
                ],
            },
        }
        spec_obj = {"filters": {"supplier": ["Sunflower Accessories Co", "Golden Dragon Trading Co. Ltd"]}}
        out = mod._apply_requested_entity_row_filters(payload=payload, business_spec=spec_obj)
        table = out.get("table") if isinstance(out.get("table"), dict) else {}
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        self.assertEqual(
            [str(row.get("supplier") or "") for row in rows if isinstance(row, dict)],
            ["Golden Dragon Trading Co. Ltd.", "Sunflower Accessories Co."],
        )
        self.assertTrue(bool(out.get("_entity_row_filter_applied")))

    def test_apply_same_period_comparison_shape_aggregates_duplicate_item_rows(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [{"fieldname": "item", "label": "Item"}, {"fieldname": "revenue", "label": "Revenue"}],
                "rows": [
                    {"item": "SPH-SAM-A15-6/128", "revenue": 13600000},
                    {"item": "SPH-SAM-A15-6/128", "revenue": 14960000},
                    {"item": "SPH-XMI-RN13-8/256", "revenue": 18250000},
                    {"item": "SPH-XMI-RN13-8/256", "revenue": 20810000},
                    {"item": "SPH-OPP-A58-6/128", "revenue": 17360000},
                ],
            },
        }
        spec_obj = {
            "task_class": "comparison",
            "metric": "revenue",
            "group_by": ["item"],
            "dimensions": ["item"],
            "filters": {
                "item": ["SPH-SAM-A15-6/128", "SPH-XMI-RN13-8/256"],
                "_comparison_rule": {
                    "metric": "revenue",
                    "dimension": "item",
                    "time_structure": "same_period",
                    "compared_values": ["SPH-SAM-A15-6/128", "SPH-XMI-RN13-8/256"],
                },
            },
        }
        out = mod._apply_same_period_comparison_shape(payload=payload, business_spec=spec_obj)
        table = out.get("table") if isinstance(out.get("table"), dict) else {}
        columns = table.get("columns") if isinstance(table.get("columns"), list) else []
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        self.assertEqual(
            [str(col.get("label") or "") for col in columns if isinstance(col, dict)],
            ["Item", "SPH-SAM-A15-6/128", "SPH-XMI-RN13-8/256"],
        )
        self.assertEqual(
            rows,
            [
                {"item": "Revenue", "compare_1": 28560000.0, "compare_2": 39060000.0},
            ],
        )
        self.assertEqual(out.get("_source_columns"), columns)
        self.assertTrue(bool(out.get("_same_period_comparison_shape_applied")))

    def test_apply_period_comparison_shape_drops_redundant_total_metric_column(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "territory", "label": "Territory"},
                    {"fieldname": "revenue", "label": "Revenue"},
                    {"fieldname": "feb_2026", "label": "Feb 2026"},
                    {"fieldname": "mar_2026", "label": "Mar 2026"},
                ],
                "rows": [
                    {"territory": "Yangon", "revenue": 12123500, "feb_2026": 6306500, "mar_2026": 5817000},
                ],
            },
        }
        spec_obj = {
            "task_class": "comparison",
            "metric": "revenue",
            "group_by": ["territory"],
            "dimensions": ["territory"],
            "filters": {
                "territory": "Yangon",
                "_comparison_rule": {
                    "metric": "revenue",
                    "dimension": "territory",
                    "time_structure": "monthly_period_vs_period",
                    "month_refs": [
                        {"month_name": "march", "year": 2026, "label": "Mar 2026"},
                        {"month_name": "february", "year": 2026, "label": "Feb 2026"},
                    ],
                    "single_entity_kind": "territory",
                    "single_entity_value": "Yangon",
                },
            },
        }
        out = mod._apply_same_period_comparison_shape(payload=payload, business_spec=spec_obj)
        table = out.get("table") if isinstance(out.get("table"), dict) else {}
        columns = table.get("columns") if isinstance(table.get("columns"), list) else []
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        self.assertEqual(
            [str(col.get("label") or "") for col in columns if isinstance(col, dict)],
            ["Territory", "Feb 2026", "Mar 2026"],
        )
        self.assertEqual(
            rows,
            [{"territory": "Yangon", "feb_2026": 6306500, "mar_2026": 5817000}],
        )
        self.assertTrue(bool(out.get("_period_comparison_shape_applied")))

    def test_apply_comparison_execution_defaults_sets_sales_analytics_filters(self):
        mod = _load_module()
        spec_obj = {
            "task_class": "comparison",
            "metric": "revenue",
            "group_by": ["territory"],
            "dimensions": ["territory"],
            "time_scope": {"mode": "none", "value": ""},
        }
        filters = {
            "territory": "Yangon",
            "_comparison_rule": {
                "metric": "revenue",
                "dimension": "territory",
                "time_structure": "monthly_period_vs_period",
                "month_refs": [
                    {"month_name": "march", "year": 2026, "label": "March 2026"},
                    {"month_name": "february", "year": 2026, "label": "February 2026"},
                ],
            },
        }
        out = mod._apply_comparison_execution_defaults(
            report_name="Sales Analytics",
            filters=filters,
            business_spec=spec_obj,
        )
        self.assertEqual(str(out.get("tree_type") or ""), "Territory")
        self.assertEqual(str(out.get("doc_type") or ""), "Sales Invoice")
        self.assertEqual(str(out.get("value_quantity") or ""), "Value")
        self.assertEqual(str(out.get("range") or ""), "Monthly")
        self.assertEqual(str(out.get("curves") or ""), "Billed Amount")
        self.assertEqual(str(out.get("from_date") or ""), "2026-02-01")
        self.assertEqual(str(out.get("to_date") or ""), "2026-03-31")

    def test_apply_comparison_execution_defaults_suppresses_multi_value_entity_filters_for_same_period(self):
        mod = _load_module()
        spec_obj = {
            "task_class": "comparison",
            "metric": "revenue",
            "group_by": ["customer"],
            "dimensions": ["customer"],
            "time_scope": {"mode": "relative", "value": "last_month"},
        }
        out = mod._apply_comparison_execution_defaults(
            report_name="Customer Ledger Summary",
            filters={
                "customer": ["Shwe Li Road Mobile Wholesale", "Latha Mobile Wholesale"],
                "_comparison_rule": {
                    "metric": "revenue",
                    "dimension": "customer",
                    "time_structure": "same_period",
                    "compared_values": ["Shwe Li Road Mobile Wholesale", "Latha Mobile Wholesale"],
                    "month_refs": [],
                },
            },
            business_spec=spec_obj,
        )
        self.assertNotIn("customer", out)
        self.assertNotIn("party", out)
        self.assertEqual(str(out.get("from_date") or ""), "2026-02-01")
        self.assertEqual(str(out.get("to_date") or ""), "2026-02-28")

    def test_realign_comparison_followup_scale_preserves_same_period_context(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "detail_projection",
            "task_type": "detail",
            "domain": "unknown",
            "subject": "sales",
            "metric": "amount",
            "group_by": ["territory"],
            "dimensions": ["territory"],
            "top_n": 0,
            "time_scope": {"mode": "none", "value": ""},
            "filters": {"locations": ["Yangon", "Mandalay"]},
            "output_contract": {"mode": "detail", "minimal_columns": ["territory", "amount"]},
            "ambiguities": ["transform_scale:million"],
        }
        last_result = {
            "type": "report_table",
            "report_name": "Sales Analytics",
            "_output_mode": "comparison",
            "_same_period_comparison_shape_applied": True,
            "table": {
                "columns": [
                    {"fieldname": "territory", "label": "Territory", "fieldtype": "Data"},
                    {"fieldname": "compare_1", "label": "Yangon", "fieldtype": "Float"},
                    {"fieldname": "compare_2", "label": "Mandalay", "fieldtype": "Float"},
                ],
                "rows": [{"territory": "Revenue", "compare_1": 6306500.0, "compare_2": 8680000.0}],
            },
        }
        previous_state = {
            "active_topic": {
                "task_class": "comparison",
                "task_type": "comparison",
                "subject": "territories",
                "metric": "revenue",
                "domain": "sales",
                "group_by": ["territory"],
                "filters": {
                    "territory": ["Yangon", "Mandalay"],
                    "_comparison_rule": {
                        "metric": "revenue",
                        "dimension": "territory",
                        "time_structure": "same_period",
                        "compared_values": ["Yangon", "Mandalay"],
                    },
                },
                "time_scope": {"mode": "relative", "value": "last_month"},
                "report_name": "Sales Analytics",
            },
            "active_result": {
                "report_name": "Sales Analytics",
                "output_mode": "comparison",
            },
        }

        out = mod._realign_comparison_followup_to_last_result(
            message="Show in Million",
            spec_obj=spec,
            last_result_payload=last_result,
            previous_topic_state=previous_state,
        )
        self.assertEqual(str(out.get("intent") or ""), "READ")
        self.assertEqual(str(out.get("task_class") or ""), "comparison")
        self.assertEqual(str(out.get("task_type") or ""), "comparison")
        self.assertEqual(str(out.get("domain") or ""), "sales")
        self.assertEqual(str(out.get("metric") or ""), "revenue")
        self.assertEqual(list(out.get("group_by") or []), ["territory"])
        self.assertEqual(out.get("time_scope"), {"mode": "relative", "value": "last_month"})
        self.assertEqual((out.get("filters") or {}).get("territory"), ["Yangon", "Mandalay"])
        output_contract = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
        self.assertEqual(str(output_contract.get("mode") or ""), "comparison")
        self.assertEqual(list(output_contract.get("minimal_columns") or []), [])

    def test_realign_comparison_followup_scale_promotes_to_transform_followup_without_losing_comparison_mode(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "detail_projection",
            "task_type": "detail",
            "domain": "unknown",
            "subject": "sales",
            "metric": "amount",
            "group_by": ["territory"],
            "dimensions": ["territory"],
            "top_n": 0,
            "time_scope": {"mode": "none", "value": ""},
            "filters": {"locations": ["Yangon", "Mandalay"]},
            "output_contract": {"mode": "detail", "minimal_columns": ["territory", "amount"]},
            "ambiguities": ["transform_scale:million"],
        }
        memory_meta = {"curr_strength": 1, "anchors_applied": ["followup_rebind_to_active_topic"], "overlap_ratio": 0.5}
        last_result = {
            "type": "report_table",
            "report_name": "Sales Analytics",
            "_output_mode": "comparison",
            "_same_period_comparison_shape_applied": True,
            "table": {
                "columns": [
                    {"fieldname": "territory", "label": "Territory", "fieldtype": "Data"},
                    {"fieldname": "compare_1", "label": "Yangon", "fieldtype": "Float"},
                    {"fieldname": "compare_2", "label": "Mandalay", "fieldtype": "Float"},
                ],
                "rows": [{"territory": "Revenue", "compare_1": 6306500.0, "compare_2": 8680000.0}],
            },
        }
        previous_state = {
            "active_topic": {
                "task_class": "comparison",
                "task_type": "comparison",
                "subject": "territories",
                "metric": "revenue",
                "domain": "sales",
                "group_by": ["territory"],
                "filters": {
                    "territory": ["Yangon", "Mandalay"],
                    "_comparison_rule": {
                        "metric": "revenue",
                        "dimension": "territory",
                        "time_structure": "same_period",
                        "compared_values": ["Yangon", "Mandalay"],
                    },
                },
                "time_scope": {"mode": "relative", "value": "last_month"},
                "report_name": "Sales Analytics",
            },
            "active_result": {
                "report_name": "Sales Analytics",
                "output_mode": "comparison",
            },
        }

        realigned = mod._realign_comparison_followup_to_last_result(
            message="Show in Million",
            spec_obj=spec,
            last_result_payload=last_result,
            previous_topic_state=previous_state,
        )
        self.assertTrue(
            bool(
                mod._should_promote_to_transform_followup(
                    message="Show in Million",
                    spec_obj=realigned,
                    memory_meta=memory_meta,
                    last_result_payload=last_result,
                )
            )
        )
        promoted = mod._promote_spec_to_transform_followup(spec_obj=realigned, last_result_payload=last_result)
        output_contract = promoted.get("output_contract") if isinstance(promoted.get("output_contract"), dict) else {}
        self.assertEqual(str(promoted.get("intent") or ""), "TRANSFORM_LAST")
        self.assertEqual(str(promoted.get("task_class") or ""), "transform_followup")
        self.assertEqual(str(output_contract.get("mode") or ""), "comparison")
        self.assertEqual(list(output_contract.get("minimal_columns") or []), [])

    def test_realign_period_comparison_followup_scale_preserves_period_columns(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "detail_projection",
            "task_type": "detail",
            "domain": "unknown",
            "subject": "sales",
            "metric": "amount",
            "group_by": ["territory"],
            "dimensions": ["territory"],
            "top_n": 0,
            "time_scope": {"mode": "none", "value": ""},
            "filters": {"territory": "Yangon"},
            "output_contract": {"mode": "detail", "minimal_columns": ["territory", "amount"]},
            "ambiguities": ["transform_scale:million"],
        }
        last_result = {
            "type": "report_table",
            "report_name": "Sales Analytics",
            "_output_mode": "comparison",
            "_period_comparison_shape_applied": True,
            "table": {
                "columns": [
                    {"fieldname": "entity", "label": "Territory", "fieldtype": "Data"},
                    {"fieldname": "feb_2026", "label": "Feb 2026", "fieldtype": "Float"},
                    {"fieldname": "mar_2026", "label": "Mar 2026", "fieldtype": "Float"},
                ],
                "rows": [{"entity": "Yangon", "feb_2026": 6306500.0, "mar_2026": 5817000.0}],
            },
        }
        previous_state = {
            "active_topic": {
                "task_class": "comparison",
                "task_type": "comparison",
                "subject": "territories",
                "metric": "revenue",
                "domain": "sales",
                "group_by": ["territory"],
                "filters": {
                    "territory": "Yangon",
                    "_comparison_rule": {
                        "metric": "revenue",
                        "dimension": "territory",
                        "time_structure": "monthly_period_vs_period",
                        "month_refs": [
                            {"month_name": "february", "year": 2026, "label": "February 2026"},
                            {"month_name": "march", "year": 2026, "label": "March 2026"},
                        ],
                        "single_entity_kind": "territory",
                        "single_entity_value": "Yangon",
                    },
                },
                "time_scope": {"mode": "relative", "value": "last_month"},
                "report_name": "Sales Analytics",
            },
            "active_result": {
                "report_name": "Sales Analytics",
                "output_mode": "comparison",
            },
        }

        realigned = mod._realign_comparison_followup_to_last_result(
            message="Show in Million",
            spec_obj=spec,
            last_result_payload=last_result,
            previous_topic_state=previous_state,
        )
        self.assertEqual(str(realigned.get("intent") or ""), "READ")
        self.assertEqual(str(realigned.get("task_class") or ""), "comparison")
        self.assertEqual(str(realigned.get("task_type") or ""), "comparison")
        output_contract = realigned.get("output_contract") if isinstance(realigned.get("output_contract"), dict) else {}
        self.assertEqual(str(output_contract.get("mode") or ""), "comparison")
        self.assertEqual(list(output_contract.get("minimal_columns") or []), ["Territory", "Feb 2026", "Mar 2026"])

    def test_realign_period_comparison_followup_scale_promotes_without_losing_comparison_mode(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "detail_projection",
            "task_type": "detail",
            "domain": "unknown",
            "subject": "sales",
            "metric": "amount",
            "group_by": ["territory"],
            "dimensions": ["territory"],
            "top_n": 0,
            "time_scope": {"mode": "none", "value": ""},
            "filters": {"territory": "Yangon"},
            "output_contract": {"mode": "detail", "minimal_columns": ["territory", "amount"]},
            "ambiguities": ["transform_scale:million"],
        }
        memory_meta = {"curr_strength": 1, "anchors_applied": ["followup_rebind_to_active_topic"], "overlap_ratio": 0.5}
        last_result = {
            "type": "report_table",
            "report_name": "Sales Analytics",
            "_output_mode": "comparison",
            "_period_comparison_shape_applied": True,
            "table": {
                "columns": [
                    {"fieldname": "entity", "label": "Territory", "fieldtype": "Data"},
                    {"fieldname": "feb_2026", "label": "Feb 2026", "fieldtype": "Float"},
                    {"fieldname": "mar_2026", "label": "Mar 2026", "fieldtype": "Float"},
                ],
                "rows": [{"entity": "Yangon", "feb_2026": 6306500.0, "mar_2026": 5817000.0}],
            },
        }
        previous_state = {
            "active_topic": {
                "task_class": "comparison",
                "task_type": "comparison",
                "subject": "territories",
                "metric": "revenue",
                "domain": "sales",
                "group_by": ["territory"],
                "filters": {
                    "territory": "Yangon",
                    "_comparison_rule": {
                        "metric": "revenue",
                        "dimension": "territory",
                        "time_structure": "month_over_month",
                        "month_refs": [
                            {"month_name": "march", "year": 2026, "label": "March 2026"},
                        ],
                        "single_entity_kind": "territory",
                        "single_entity_value": "Yangon",
                    },
                },
                "time_scope": {"mode": "relative", "value": "last_month"},
                "report_name": "Sales Analytics",
            },
            "active_result": {
                "report_name": "Sales Analytics",
                "output_mode": "comparison",
            },
        }

        realigned = mod._realign_comparison_followup_to_last_result(
            message="Show in Million",
            spec_obj=spec,
            last_result_payload=last_result,
            previous_topic_state=previous_state,
        )
        self.assertTrue(
            bool(
                mod._should_promote_to_transform_followup(
                    message="Show in Million",
                    spec_obj=realigned,
                    memory_meta=memory_meta,
                    last_result_payload=last_result,
                )
            )
        )
        promoted = mod._promote_spec_to_transform_followup(spec_obj=realigned, last_result_payload=last_result)
        output_contract = promoted.get("output_contract") if isinstance(promoted.get("output_contract"), dict) else {}
        self.assertEqual(str(promoted.get("intent") or ""), "TRANSFORM_LAST")
        self.assertEqual(str(promoted.get("task_class") or ""), "transform_followup")
        self.assertEqual(str(output_contract.get("mode") or ""), "comparison")
        self.assertEqual(list(output_contract.get("minimal_columns") or []), ["Territory", "Feb 2026", "Mar 2026"])

    def test_realign_comparison_followup_preserves_same_period_correction_rebind(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "comparison",
            "task_type": "comparison",
            "domain": "sales",
            "subject": "territories",
            "metric": "revenue",
            "group_by": ["territory"],
            "dimensions": ["territory"],
            "top_n": 0,
            "time_scope": {"mode": "none", "value": ""},
            "filters": {
                "territory": ["Yangon", "Bago"],
                "_comparison_rule": {
                    "metric": "revenue",
                    "dimension": "territory",
                    "time_structure": "same_period",
                    "compared_values": ["Yangon", "Bago"],
                },
            },
            "output_contract": {"mode": "comparison", "minimal_columns": ["territory", "revenue"]},
            "ambiguities": [],
        }
        last_result = {
            "type": "report_table",
            "report_name": "Sales Analytics",
            "_output_mode": "comparison",
            "_same_period_comparison_shape_applied": True,
            "table": {
                "columns": [
                    {"fieldname": "territory", "label": "Territory", "fieldtype": "Data"},
                    {"fieldname": "compare_1", "label": "Yangon", "fieldtype": "Float"},
                    {"fieldname": "compare_2", "label": "Mandalay", "fieldtype": "Float"},
                ],
                "rows": [{"territory": "Revenue", "compare_1": 6306500.0, "compare_2": 8680000.0}],
            },
        }
        previous_state = {
            "active_topic": {
                "task_class": "comparison",
                "task_type": "comparison",
                "subject": "territories",
                "metric": "revenue",
                "domain": "sales",
                "group_by": ["territory"],
                "filters": {
                    "territory": ["Yangon", "Mandalay"],
                    "_comparison_rule": {
                        "metric": "revenue",
                        "dimension": "territory",
                        "time_structure": "same_period",
                        "compared_values": ["Yangon", "Mandalay"],
                    },
                },
                "time_scope": {"mode": "relative", "value": "last_month"},
                "report_name": "Sales Analytics",
            },
            "active_result": {
                "report_name": "Sales Analytics",
                "output_mode": "comparison",
            },
        }

        out = mod._realign_comparison_followup_to_last_result(
            message="Actually compare Yangon and Bago instead",
            spec_obj=spec,
            last_result_payload=last_result,
            previous_topic_state=previous_state,
        )
        filters = out.get("filters") if isinstance(out.get("filters"), dict) else {}
        rule = filters.get("_comparison_rule") if isinstance(filters.get("_comparison_rule"), dict) else {}
        self.assertEqual(filters.get("territory"), ["Yangon", "Bago"])
        self.assertEqual(list(rule.get("compared_values") or []), ["Yangon", "Bago"])
        self.assertEqual(out.get("time_scope"), {"mode": "relative", "value": "last_month"})

    def test_resolve_record_doctype_candidates_ambiguous_invoice(self):
        mod = _load_module()

        class _FakeFrappe:
            @staticmethod
            def get_all(doctype, **kwargs):
                if doctype != "DocType":
                    return []
                return [
                    {"name": "Sales Invoice"},
                    {"name": "Purchase Invoice"},
                    {"name": "Sales Order"},
                ]

        mod.frappe = _FakeFrappe()
        mod._load_submittable_doctypes.cache_clear()
        spec = {
            "intent": "READ",
            "task_class": "list_latest_records",
            "subject": "latest invoice",
            "metric": "",
            "domain": "unknown",
            "filters": {},
        }
        out = mod._resolve_record_doctype_candidates(message="Show me the latest 7 Invoice", spec=spec)
        self.assertIn("Sales Invoice", out)
        self.assertIn("Purchase Invoice", out)

    def test_resolve_record_doctype_candidates_exact_sales_invoice(self):
        mod = _load_module()

        class _FakeFrappe:
            @staticmethod
            def get_all(doctype, **kwargs):
                if doctype != "DocType":
                    return []
                return [
                    {"name": "Sales Invoice"},
                    {"name": "Purchase Invoice"},
                    {"name": "Sales Order"},
                ]

        mod.frappe = _FakeFrappe()
        mod._load_submittable_doctypes.cache_clear()
        spec = {
            "intent": "READ",
            "task_class": "list_latest_records",
            "subject": "sales invoice",
            "metric": "",
            "domain": "sales",
            "filters": {},
        }
        out = mod._resolve_record_doctype_candidates(message="Sales Invoice", spec=spec)
        self.assertEqual(out, ["Sales Invoice"])

    def test_resolve_record_doctype_candidates_uses_metric_domain_to_break_invoice_tie(self):
        mod = _load_module()

        class _FakeFrappe:
            @staticmethod
            def get_all(doctype, **kwargs):
                if doctype != "DocType":
                    return []
                return [
                    {"name": "Sales Invoice"},
                    {"name": "Purchase Invoice"},
                    {"name": "Sales Order"},
                ]

        mod.frappe = _FakeFrappe()
        mod._load_submittable_doctypes.cache_clear()
        spec = {
            "intent": "READ",
            "task_class": "list_latest_records",
            "subject": "invoices",
            "metric": "revenue",
            "domain": "unknown",
            "filters": {},
        }
        out = mod._resolve_record_doctype_candidates(message="revenue Invoice", spec=spec)
        self.assertEqual(out, ["Sales Invoice"])

    def test_resolve_record_doctype_candidates_uses_message_metric_when_pending_metric_missing(self):
        mod = _load_module()

        class _FakeFrappe:
            @staticmethod
            def get_all(doctype, **kwargs):
                if doctype != "DocType":
                    return []
                return [
                    {"name": "Sales Invoice"},
                    {"name": "Purchase Invoice"},
                    {"name": "Sales Order"},
                ]

        mod.frappe = _FakeFrappe()
        mod._load_submittable_doctypes.cache_clear()
        spec = {
            "intent": "READ",
            "task_class": "list_latest_records",
            "subject": "invoices",
            "metric": "",
            "domain": "unknown",
            "filters": {},
        }
        out = mod._resolve_record_doctype_candidates(message="revenue Invoice", spec=spec)
        self.assertEqual(out, ["Sales Invoice"])

    def test_resolve_record_doctype_candidates_handles_plural_and_sale_sales_variants(self):
        mod = _load_module()

        class _FakeFrappe:
            @staticmethod
            def get_all(doctype, **kwargs):
                if doctype != "DocType":
                    return []
                return [
                    {"name": "Sales Invoice"},
                    {"name": "Purchase Invoice"},
                    {"name": "Sales Order"},
                ]

        mod.frappe = _FakeFrappe()
        mod._load_submittable_doctypes.cache_clear()
        spec = {
            "intent": "READ",
            "task_class": "list_latest_records",
            "subject": "sales invoice",
            "metric": "",
            "domain": "sales",
            "filters": {},
        }
        out = mod._resolve_record_doctype_candidates(message="give me latest sale invoices", spec=spec)
        self.assertEqual(out, ["Sales Invoice"])

    def test_direct_latest_records_payload_uses_doctype_rows(self):
        mod = _load_module()

        class _Field:
            def __init__(self, fieldname):
                self.fieldname = fieldname

        class _Meta:
            def __init__(self):
                self.fields = [
                    _Field("posting_date"),
                    _Field("customer"),
                    _Field("grand_total"),
                    _Field("company"),
                    _Field("status"),
                ]

        class _FakeFrappe:
            @staticmethod
            def get_all(doctype, **kwargs):
                if doctype == "DocType":
                    return [{"name": "Sales Invoice"}, {"name": "Purchase Invoice"}]
                if doctype == "Sales Invoice":
                    return [
                        {
                            "name": "ACC-SINV-2026-00013",
                            "posting_date": "2026-02-21",
                            "customer": "aaaa",
                            "grand_total": 53200,
                            "company": "MMOB",
                            "status": "Paid",
                        },
                        {
                            "name": "ACC-SINV-2026-00012",
                            "posting_date": "2026-02-20",
                            "customer": "City Mobile Mart",
                            "grand_total": 1800000,
                            "company": "MMOB",
                            "status": "Unpaid",
                        },
                    ]
                return []

            @staticmethod
            def get_meta(doctype):
                if doctype == "Sales Invoice":
                    return _Meta()
                return _Meta()

        mod.frappe = _FakeFrappe()
        mod._load_submittable_doctypes.cache_clear()
        mod._doctype_field_names.cache_clear()
        spec = {
            "intent": "READ",
            "task_class": "list_latest_records",
            "subject": "latest invoices",
            "metric": "",
            "domain": "sales",
            "top_n": 7,
            "filters": {"company": "MMOB"},
            "output_contract": {
                "mode": "top_n",
                "minimal_columns": ["invoice_number", "customer", "posting_date", "total_amount"],
            },
        }
        payload = mod._direct_latest_records_payload(spec, message="Show me the latest 7 Sales Invoice from this month")
        self.assertIsInstance(payload, dict)
        self.assertEqual(str(payload.get("type") or ""), "report_table")
        self.assertEqual(str(payload.get("report_name") or ""), "Sales Invoice")
        table = payload.get("table") if isinstance(payload.get("table"), dict) else {}
        cols = table.get("columns") if isinstance(table.get("columns"), list) else []
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        labels = [str(c.get("label") or "") for c in cols if isinstance(c, dict)]
        self.assertIn("Sales Invoice Number", labels)
        self.assertIn("Total Amount", labels)
        self.assertTrue(len(rows) >= 1)
        self.assertIn("total_amount", list(rows[0].keys()))

        spec_with_spaced_columns = dict(spec)
        spec_with_spaced_columns["output_contract"] = {
            "mode": "top_n",
            "minimal_columns": ["Invoice Number", "Customer", "Posting Date", "Total Amount"],
        }
        payload2 = mod._direct_latest_records_payload(
            spec_with_spaced_columns,
            message="give me 7 latest sales invoices and show total amount as Million",
        )
        self.assertIsInstance(payload2, dict)
        table2 = payload2.get("table") if isinstance(payload2.get("table"), dict) else {}
        rows2 = table2.get("rows") if isinstance(table2.get("rows"), list) else []
        self.assertTrue(len(rows2) >= 1)
        keys2 = [str(x).strip().lower() for x in list(rows2[0].keys())]
        self.assertIn("total_amount", keys2)

    def test_direct_latest_records_payload_falls_back_when_doctype_meta_unavailable(self):
        mod = _load_module()

        class _FakeFrappe:
            @staticmethod
            def get_all(doctype, **kwargs):
                if doctype == "DocType":
                    return [{"name": "Sales Invoice"}]
                if doctype == "Sales Invoice":
                    return [
                        {
                            "name": "ACC-SINV-2026-00013",
                            "modified": "2026-02-21 10:05:00",
                        }
                    ]
                return []

            @staticmethod
            def get_meta(doctype):
                raise RuntimeError("meta unavailable")

        mod.frappe = _FakeFrappe()
        mod._load_submittable_doctypes.cache_clear()
        mod._doctype_field_names.cache_clear()
        spec = {
            "intent": "READ",
            "task_class": "list_latest_records",
            "subject": "latest invoices",
            "metric": "",
            "domain": "sales",
            "top_n": 7,
            "filters": {"doctype": "Sales Invoice"},
            "output_contract": {"mode": "top_n", "minimal_columns": []},
        }
        payload = mod._direct_latest_records_payload(spec, message="Show me the latest 7 Sales Invoice")
        self.assertIsInstance(payload, dict)
        self.assertEqual(str(payload.get("type") or ""), "report_table")
        table = payload.get("table") if isinstance(payload.get("table"), dict) else {}
        cols = table.get("columns") if isinstance(table.get("columns"), list) else []
        rows = table.get("rows") if isinstance(table.get("rows"), list) else []
        labels = [str(c.get("label") or "") for c in cols if isinstance(c, dict)]
        self.assertIn("Sales Invoice Number", labels)
        self.assertTrue(any("time" in str(lb).lower() or "date" in str(lb).lower() for lb in labels))
        self.assertTrue(len(rows) >= 1)

    def test_direct_latest_records_payload_adds_modified_time_when_meta_has_no_date_fields(self):
        mod = _load_module()

        class _Meta:
            def __init__(self):
                self.fields = []

        class _FakeFrappe:
            @staticmethod
            def get_all(doctype, **kwargs):
                if doctype == "DocType":
                    return [{"name": "Sales Invoice"}]
                if doctype == "Sales Invoice":
                    return [
                        {
                            "name": "ACC-SINV-2026-00013",
                            "modified": "2026-02-21 10:05:00",
                        }
                    ]
                return []

            @staticmethod
            def get_meta(doctype):
                return _Meta()

        mod.frappe = _FakeFrappe()
        mod._load_submittable_doctypes.cache_clear()
        mod._doctype_field_names.cache_clear()
        spec = {
            "intent": "READ",
            "task_class": "list_latest_records",
            "subject": "latest invoices",
            "metric": "",
            "domain": "sales",
            "top_n": 7,
            "filters": {"doctype": "Sales Invoice"},
            "output_contract": {"mode": "top_n", "minimal_columns": []},
        }
        payload = mod._direct_latest_records_payload(spec, message="Show me the latest 7 Sales Invoice")
        self.assertIsInstance(payload, dict)
        self.assertEqual(str(payload.get("type") or ""), "report_table")
        table = payload.get("table") if isinstance(payload.get("table"), dict) else {}
        cols = table.get("columns") if isinstance(table.get("columns"), list) else []
        labels = [str(c.get("label") or "") for c in cols if isinstance(c, dict)]
        self.assertIn("Modified Time", labels)

    def test_shape_response_keeps_temporal_column_for_latest_records_projection(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Sales Invoice",
            "table": {
                "columns": [
                    {"fieldname": "name", "label": "Invoice Id"},
                    {"fieldname": "modified", "label": "Modified Time", "fieldtype": "Datetime"},
                ],
                "rows": [
                    {"name": "ACC-SINV-2026-00013", "modified": "2026-02-21 10:05:00"},
                    {"name": "ACC-SINV-2026-00012", "modified": "2026-02-20 09:05:00"},
                ],
            },
        }
        spec = {
            "intent": "READ",
            "task_class": "list_latest_records",
            "top_n": 7,
            "output_contract": {"mode": "top_n", "minimal_columns": ["invoice id"]},
        }
        out = mod.shape_response(payload=payload, business_spec=spec)
        table = out.get("table") if isinstance(out.get("table"), dict) else {}
        cols = table.get("columns") if isinstance(table.get("columns"), list) else []
        labels = [str(c.get("label") or "") for c in cols if isinstance(c, dict)]
        self.assertIn("Invoice Id", labels)
        self.assertIn("Modified Time", labels)

    def test_quality_repairable_class_detection(self):
        mod = _load_module()
        quality = {
            "repairable_failure_classes": ["shape"],
            "failed_check_ids": [],
        }
        self.assertTrue(
            bool(
                mod._quality_has_repairable_failure_class(
                    quality,
                    classes=["shape", "data"],
                )
            )
        )

    def test_should_switch_candidate_on_repairable_for_followup_turns(self):
        mod = _load_module()
        quality = {
            "verdict": "REPAIRABLE_FAIL",
            "repairable_failure_classes": ["shape"],
            "failed_check_ids": [],
        }
        ok = mod._should_switch_candidate_on_repairable(
            quality=quality,
            intent="READ",
            task_class="detail_projection",
            candidate_cursor=0,
            candidate_reports=["Warehouse Wise Stock Balance", "Stock Balance"],
            candidate_switch_attempts=0,
        )
        self.assertTrue(bool(ok))

    def test_promote_transform_followup_for_anchored_kpi_with_million_hint(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "analytical_read",
            "task_type": "kpi",
            "aggregation": "sum",
            "time_scope": {"mode": "none", "value": ""},
            "ambiguities": ["transform_scale:million"],
        }
        memory_meta = {
            "curr_strength": 2,
            "anchors_applied": ["domain", "filters", "top_n"],
        }
        last_result = {
            "type": "report_table",
            "table": {
                "columns": [{"fieldname": "total_amount", "label": "Total Amount"}],
                "rows": [{"total_amount": 100.0}],
            },
        }
        self.assertTrue(
            bool(
                mod._should_promote_to_transform_followup(
                    message="Show as million",
                    spec_obj=spec,
                    memory_meta=memory_meta,
                    last_result_payload=last_result,
                )
            )
        )
        promoted = mod._promote_spec_to_transform_followup(spec_obj=spec)
        self.assertEqual(str(promoted.get("intent") or ""), "TRANSFORM_LAST")
        self.assertEqual(str(promoted.get("task_class") or ""), "transform_followup")

    def test_promote_transform_followup_for_projection_only_followup(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "detail_projection",
            "task_type": "detail",
            "aggregation": "none",
            "time_scope": {"mode": "none", "value": ""},
            "output_contract": {"mode": "detail", "minimal_columns": ["customer", "revenue"]},
            "ambiguities": [],
        }
        memory_meta = {
            "curr_strength": 2,
            "anchors_applied": ["metric", "group_by", "top_n", "time_scope"],
        }
        last_result = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "customer", "label": "Customer"},
                    {"fieldname": "revenue", "label": "Revenue"},
                    {"fieldname": "posting_date", "label": "Posting Date"},
                ],
                "rows": [{"customer": "A", "revenue": 100.0, "posting_date": "2026-02-01"}],
            },
        }
        self.assertTrue(
            bool(
                mod._should_promote_to_transform_followup(
                    message="Show only customer and revenue columns",
                    spec_obj=spec,
                    memory_meta=memory_meta,
                    last_result_payload=last_result,
                )
            )
        )

    def test_promote_transform_followup_allows_anchored_time_scope_for_transform(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "analytical_read",
            "task_type": "ranking",
            "aggregation": "none",
            "time_scope": {"mode": "relative", "value": "last_month"},
            "output_contract": {"mode": "top_n", "minimal_columns": []},
            "ambiguities": ["transform_scale:million"],
        }
        memory_meta = {
            "curr_strength": 1,
            "anchors_applied": ["metric", "group_by", "top_n", "time_scope"],
        }
        last_result = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "customer", "label": "Customer"},
                    {"fieldname": "revenue", "label": "Revenue"},
                ],
                "rows": [{"customer": "A", "revenue": 1000000.0}],
            },
        }
        self.assertTrue(
            bool(
                mod._should_promote_to_transform_followup(
                    message="Show as million",
                    spec_obj=spec,
                    memory_meta=memory_meta,
                    last_result_payload=last_result,
                )
            )
        )

    def test_does_not_promote_rank_direction_change_on_limited_top_n_result(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "analytical_read",
            "task_type": "ranking",
            "aggregation": "none",
            "time_scope": {"mode": "none", "value": ""},
            "output_contract": {"mode": "top_n", "minimal_columns": ["warehouse", "stock balance"]},
            "ambiguities": ["transform_sort:desc"],
        }
        memory_meta = {
            "curr_strength": 3,
            "anchors_applied": [],
            "overlap_ratio": 0.7,
        }
        last_result = {
            "_output_mode": "top_n",
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse"},
                    {"fieldname": "stock_balance", "label": "Stock Balance"},
                ],
                "rows": [
                    {"warehouse": "Stores - MMOB", "stock_balance": 0.0},
                    {"warehouse": "Work In Progress - MMOB", "stock_balance": 0.0},
                    {"warehouse": "Finished Goods - MMOB", "stock_balance": 0.0},
                ],
            },
        }
        self.assertFalse(
            bool(
                mod._should_promote_to_transform_followup(
                    message="I mean Top",
                    spec_obj=spec,
                    memory_meta=memory_meta,
                    last_result_payload=last_result,
                )
            )
        )

    def test_does_not_promote_transform_followup_for_explicit_new_granularity_refinement(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "detail_projection",
            "task_type": "detail",
            "aggregation": "none",
            "domain": "inventory",
            "subject": "stock balance",
            "metric": "stock balance",
            "dimensions": ["warehouse"],
            "group_by": [],
            "time_scope": {"mode": "none", "value": ""},
            "output_contract": {"mode": "detail", "minimal_columns": ["stock balance", "warehouse", "item"]},
            "ambiguities": [],
        }
        memory_meta = {
            "curr_strength": 2,
            "anchors_applied": ["topic_overlap"],
            "overlap_ratio": 0.7,
        }
        last_result = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse"},
                    {"fieldname": "stock_balance", "label": "Stock Balance"},
                ],
                "rows": [{"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399386000.0}],
            },
        }
        self.assertFalse(
            bool(
                mod._should_promote_to_transform_followup(
                    message="I mean stock balance per item in Yangon Main Warehouse",
                    spec_obj=spec,
                    memory_meta=memory_meta,
                    last_result_payload=last_result,
                )
            )
        )

    def test_realign_transform_followup_to_read_refinement_for_new_dimension(self):
        mod = _load_module()
        spec = {
            "intent": "TRANSFORM_LAST",
            "task_class": "transform_followup",
            "task_type": "detail",
            "domain": "inventory",
            "subject": "stock balance",
            "metric": "stock balance",
            "dimensions": ["warehouse"],
            "group_by": [],
            "time_scope": {"mode": "none", "value": ""},
            "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
            "output_contract": {"mode": "detail", "minimal_columns": ["stock balance", "warehouse", "item"]},
            "ambiguities": [],
        }
        last_result = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse"},
                    {"fieldname": "stock_balance", "label": "Stock Balance"},
                ],
                "rows": [{"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399386000.0}],
            },
        }
        out = mod._realign_transform_followup_to_read_refinement(
            message="I mean stock balance per item in Yangon Main Warehouse",
            spec_obj=spec,
            last_result_payload=last_result,
        )
        self.assertEqual(str(out.get("intent") or ""), "READ")
        self.assertEqual(str(out.get("task_class") or ""), "detail_projection")
        dims = [str(x).strip().lower() for x in list(out.get("dimensions") or []) if str(x).strip()]
        self.assertIn("item", dims)

    def test_promote_transform_followup_for_short_transform_message_with_context_filled_spec(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "analytical_read",
            "task_type": "ranking",
            "aggregation": "sum",
            "domain": "sales",
            "subject": "customers",
            "metric": "revenue",
            "group_by": ["customer"],
            "top_n": 10,
            "time_scope": {"mode": "relative", "value": "last_month"},
            "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "revenue"]},
            "ambiguities": ["transform_scale:million"],
        }
        memory_meta = {
            "curr_strength": 6,
            "anchors_applied": [],
            "overlap_ratio": 0.625,
        }
        last_result = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "customer", "label": "Customer"},
                    {"fieldname": "revenue", "label": "Revenue"},
                ],
                "rows": [{"customer": "A", "revenue": 1000000.0}],
            },
        }
        self.assertTrue(
            bool(
                mod._should_promote_to_transform_followup(
                    message="Show as Million",
                    spec_obj=spec,
                    memory_meta=memory_meta,
                    last_result_payload=last_result,
                )
            )
        )

    def test_promote_transform_followup_when_parser_already_marks_task_class_but_intent_is_read(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "transform_followup",
            "task_type": "ranking",
            "aggregation": "sum",
            "domain": "sales",
            "subject": "products",
            "metric": "sold quantity",
            "group_by": ["item"],
            "top_n": 10,
            "time_scope": {"mode": "relative", "value": "last_month"},
            "output_contract": {"mode": "top_n", "minimal_columns": ["item name"]},
            "ambiguities": ["transform_projection:only"],
        }
        memory_meta = {
            "curr_strength": 6,
            "anchors_applied": ["projection_columns"],
            "overlap_ratio": 0.6667,
        }
        last_result = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "item", "label": "Item"},
                    {"fieldname": "sold_quantity", "label": "Sold Quantity"},
                    {"fieldname": "item_name", "label": "Item Name"},
                ],
                "rows": [{"item": "A", "sold_quantity": 10.0, "item_name": "Alpha"}],
            },
        }
        self.assertTrue(
            bool(
                mod._should_promote_to_transform_followup(
                    message="Give me item name only",
                    spec_obj=spec,
                    memory_meta=memory_meta,
                    last_result_payload=last_result,
                )
            )
        )

    def test_do_not_promote_transform_followup_for_fresh_transform_bearing_read(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "analytical_read",
            "task_type": "ranking",
            "aggregation": "sum",
            "domain": "finance",
            "subject": "accounts receivable",
            "metric": "outstanding_amount",
            "group_by": ["customer"],
            "top_n": 10,
            "time_scope": {"mode": "relative", "value": "last_month"},
            "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "outstanding_amount"]},
            "ambiguities": ["transform_scale:million"],
        }
        memory_meta = {
            "curr_strength": 6,
            "anchors_applied": [],
            "overlap_ratio": 0.0,
        }
        last_result = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "customer", "label": "Customer"},
                    {"fieldname": "revenue", "label": "Revenue"},
                ],
                "rows": [{"customer": "A", "revenue": 1000000.0}],
            },
        }
        self.assertFalse(
            bool(
                mod._should_promote_to_transform_followup(
                    message="Top 10 accounts receivable customers in million last month",
                    spec_obj=spec,
                    memory_meta=memory_meta,
                    last_result_payload=last_result,
                )
            )
        )

    def test_realign_contribution_followup_top_n_only_keeps_metric_and_contribution_share(self):
        mod = _load_module()
        spec = {
            "intent": "TRANSFORM_LAST",
            "task_class": "transform_followup",
            "task_type": "ranking",
            "domain": "sales",
            "subject": "customers",
            "metric": "revenue",
            "group_by": ["customer"],
            "dimensions": ["customer"],
            "top_n": 10,
            "time_scope": {"mode": "relative", "value": "last_month"},
            "filters": {
                "_contribution_rule": {
                    "metric": "revenue",
                    "basis": "of_total",
                    "contribution_terms": ["share_of_total", "contribution_share"],
                }
            },
            "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "contribution share"]},
            "ambiguities": ["transform_projection:only", "transform_sort:desc"],
        }
        memory_meta = {"curr_strength": 4}
        last_result = {
            "type": "report_table",
            "report_name": "Customer Ledger Summary",
            "_output_mode": "top_n",
            "_contribution_rule_applied": True,
            "_contribution_metric": "revenue",
            "_contribution_primary_dimension": "customer",
        }
        previous_state = {
            "active_topic": {
                "task_class": "contribution_share",
                "subject": "customers",
                "metric": "revenue",
                "domain": "sales",
                "group_by": ["customer"],
                "top_n": 10,
                "report_name": "Customer Ledger Summary",
                "filters": {
                    "_contribution_rule": {
                        "metric": "revenue",
                        "basis": "of_total",
                        "contribution_terms": ["share_of_total", "contribution_share"],
                    }
                },
                "time_scope": {"mode": "relative", "value": "last_month"},
            },
            "active_result": {
                "report_name": "Customer Ledger Summary",
                "output_mode": "top_n",
            },
        }

        out = mod._realign_contribution_followup_to_last_result(
            message="Top 5 only",
            spec_obj=spec,
            memory_meta=memory_meta,
            last_result_payload=last_result,
            previous_topic_state=previous_state,
        )

        output_contract = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
        self.assertEqual(str(out.get("task_class") or ""), "transform_followup")
        self.assertEqual(int(out.get("top_n") or 0), 5)
        self.assertEqual(str(output_contract.get("mode") or ""), "top_n")
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["customer", "revenue", "contribution share"],
        )
        self.assertNotIn("transform_projection:only", [str(x).strip().lower() for x in list(out.get("ambiguities") or []) if str(x).strip()])

    def test_realign_contribution_followup_scale_preserves_contribution_context(self):
        mod = _load_module()
        spec = {
            "intent": "TRANSFORM_LAST",
            "task_class": "transform_followup",
            "task_type": "ranking",
            "domain": "sales",
            "subject": "customers",
            "metric": "revenue",
            "group_by": ["customer"],
            "dimensions": ["customer"],
            "top_n": 10,
            "time_scope": {"mode": "none", "value": ""},
            "filters": {},
            "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "revenue"]},
            "ambiguities": ["transform_scale:million"],
        }
        memory_meta = {"curr_strength": 4}
        last_result = {
            "type": "report_table",
            "report_name": "Customer Ledger Summary",
            "_output_mode": "top_n",
            "_contribution_rule_applied": True,
            "_contribution_metric": "revenue",
            "_contribution_primary_dimension": "customer",
        }
        previous_state = {
            "active_topic": {
                "task_class": "contribution_share",
                "subject": "customers",
                "metric": "revenue",
                "domain": "sales",
                "group_by": ["customer"],
                "top_n": 10,
                "report_name": "Customer Ledger Summary",
                "filters": {
                    "_contribution_rule": {
                        "metric": "revenue",
                        "basis": "of_total",
                        "contribution_terms": ["share_of_total", "contribution_share"],
                    }
                },
                "time_scope": {"mode": "relative", "value": "last_month"},
            },
            "active_result": {
                "report_name": "Customer Ledger Summary",
                "output_mode": "top_n",
            },
        }

        out = mod._realign_contribution_followup_to_last_result(
            message="Show in Million",
            spec_obj=spec,
            memory_meta=memory_meta,
            last_result_payload=last_result,
            previous_topic_state=previous_state,
        )

        filters = out.get("filters") if isinstance(out.get("filters"), dict) else {}
        output_contract = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
        self.assertEqual(str(out.get("task_class") or ""), "transform_followup")
        self.assertEqual(str(out.get("domain") or ""), "sales")
        self.assertEqual(out.get("time_scope"), {"mode": "relative", "value": "last_month"})
        self.assertTrue(isinstance(filters.get("_contribution_rule"), dict))
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["customer", "revenue", "contribution share"],
        )
        self.assertEqual(str(output_contract.get("mode") or ""), "top_n")

    def test_realign_contribution_followup_scale_uses_active_result_fallback_context(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "analytical_read",
            "task_type": "ranking",
            "domain": "sales",
            "subject": "customers",
            "metric": "revenue",
            "group_by": ["customer"],
            "dimensions": ["customer"],
            "top_n": 10,
            "time_scope": {"mode": "none", "value": ""},
            "filters": {},
            "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "revenue"]},
            "ambiguities": ["transform_scale:million"],
        }
        memory_meta = {"curr_strength": 4}
        last_result = {
            "type": "report_table",
            "report_name": "Customer Ledger Summary",
            "_output_mode": "top_n",
            "_contribution_rule_applied": True,
            "_contribution_rule": {
                "metric": "revenue",
                "basis": "of_total",
                "contribution_terms": ["share_of_total", "contribution_share"],
            },
            "_contribution_metric": "revenue",
            "_contribution_primary_dimension": "customer",
        }
        previous_state = {
            "active_topic": {
                "task_class": "transform_followup",
                "subject": "customers",
                "metric": "revenue",
                "domain": "sales",
                "group_by": ["customer"],
                "top_n": 10,
                "report_name": "Customer Ledger Summary",
                "filters": {},
                "time_scope": {"mode": "none", "value": ""},
            },
            "active_result": {
                "task_class": "contribution_share",
                "report_name": "Customer Ledger Summary",
                "output_mode": "top_n",
                "filters": {
                    "_contribution_rule": {
                        "metric": "revenue",
                        "basis": "of_total",
                        "contribution_terms": ["share_of_total", "contribution_share"],
                    }
                },
                "time_scope": {"mode": "relative", "value": "last_month"},
            },
        }

        out = mod._realign_contribution_followup_to_last_result(
            message="Show in Million",
            spec_obj=spec,
            memory_meta=memory_meta,
            last_result_payload=last_result,
            previous_topic_state=previous_state,
        )

        filters = out.get("filters") if isinstance(out.get("filters"), dict) else {}
        output_contract = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
        self.assertEqual(str(out.get("task_class") or ""), "transform_followup")
        self.assertEqual(str(out.get("domain") or ""), "sales")
        self.assertEqual(out.get("time_scope"), {"mode": "relative", "value": "last_month"})
        self.assertTrue(isinstance(filters.get("_contribution_rule"), dict))
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["customer", "revenue", "contribution share"],
        )
        self.assertEqual(str(output_contract.get("mode") or ""), "top_n")

    def test_realign_contribution_followup_projection_keeps_share_column(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "analytical_read",
            "task_type": "ranking",
            "domain": "sales",
            "subject": "customers",
            "metric": "revenue",
            "group_by": ["customer"],
            "dimensions": ["customer"],
            "top_n": 10,
            "time_scope": {"mode": "relative", "value": "last_month"},
            "filters": {},
            "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "revenue"]},
            "ambiguities": ["transform_projection:only"],
        }
        memory_meta = {"curr_strength": 4}
        last_result = {
            "type": "report_table",
            "report_name": "Customer Ledger Summary",
            "_output_mode": "top_n",
            "_contribution_rule_applied": True,
            "_contribution_metric": "revenue",
            "_contribution_primary_dimension": "customer",
        }
        previous_state = {
            "active_topic": {
                "task_class": "contribution_share",
                "subject": "customers",
                "metric": "revenue",
                "domain": "sales",
                "group_by": ["customer"],
                "top_n": 10,
                "report_name": "Customer Ledger Summary",
                "filters": {
                    "_contribution_rule": {
                        "metric": "revenue",
                        "basis": "of_total",
                        "contribution_terms": ["share_of_total", "contribution_share"],
                    }
                },
                "time_scope": {"mode": "relative", "value": "last_month"},
            },
            "active_result": {
                "report_name": "Customer Ledger Summary",
                "output_mode": "top_n",
            },
        }

        out = mod._realign_contribution_followup_to_last_result(
            message="Show only customer, revenue and contribution share",
            spec_obj=spec,
            memory_meta=memory_meta,
            last_result_payload=last_result,
            previous_topic_state=previous_state,
        )
        output_contract = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["customer", "revenue", "contribution share"],
        )

    def test_realign_contribution_followup_scale_rebinds_when_metric_is_share_alias(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_class": "analytical_read",
            "task_type": "ranking",
            "domain": "unknown",
            "subject": "items",
            "metric": "contribution share",
            "group_by": ["item"],
            "dimensions": ["item"],
            "top_n": 10,
            "time_scope": {"mode": "none", "value": ""},
            "filters": {},
            "output_contract": {"mode": "top_n", "minimal_columns": ["item", "contribution share"]},
            "ambiguities": ["transform_scale:million"],
        }
        memory_meta = {"curr_strength": 4}
        last_result = {
            "type": "report_table",
            "report_name": "Item-wise Sales Register",
            "_output_mode": "top_n",
            "_contribution_rule_applied": True,
            "_contribution_rule": {
                "metric": "revenue",
                "basis": "of_total",
                "contribution_terms": ["share_of_total", "contribution_share"],
            },
            "_contribution_metric": "revenue",
            "_contribution_primary_dimension": "item",
        }
        previous_state = {
            "active_topic": {
                "task_class": "contribution_share",
                "subject": "items",
                "metric": "revenue",
                "domain": "sales",
                "group_by": ["item"],
                "top_n": 10,
                "report_name": "Item-wise Sales Register",
                "filters": {
                    "_contribution_rule": {
                        "metric": "revenue",
                        "basis": "of_total",
                        "contribution_terms": ["share_of_total", "contribution_share"],
                    }
                },
                "time_scope": {"mode": "relative", "value": "last_month"},
            },
            "active_result": {
                "task_class": "contribution_share",
                "report_name": "Item-wise Sales Register",
                "output_mode": "top_n",
                "filters": {
                    "_contribution_rule": {
                        "metric": "revenue",
                        "basis": "of_total",
                        "contribution_terms": ["share_of_total", "contribution_share"],
                    }
                },
                "time_scope": {"mode": "relative", "value": "last_month"},
            },
        }

        out = mod._realign_contribution_followup_to_last_result(
            message="Show in Million",
            spec_obj=spec,
            memory_meta=memory_meta,
            last_result_payload=last_result,
            previous_topic_state=previous_state,
        )
        output_contract = out.get("output_contract") if isinstance(out.get("output_contract"), dict) else {}
        filters = out.get("filters") if isinstance(out.get("filters"), dict) else {}
        self.assertEqual(str(out.get("task_class") or ""), "transform_followup")
        self.assertEqual(str(out.get("metric") or ""), "revenue")
        self.assertEqual(str(out.get("domain") or ""), "sales")
        self.assertEqual(out.get("time_scope"), {"mode": "relative", "value": "last_month"})
        self.assertTrue(isinstance(filters.get("_contribution_rule"), dict))
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["item", "revenue", "contribution share"],
        )

    def test_threshold_precheck_does_not_reference_active_result(self):
        mod = _load_module()
        out = mod._threshold_precheck(
            message="Top customers by revenue",
            business_spec={"task_class": "contribution_share", "filters": {}},
            previous_topic_state={"active_topic": {"task_class": "contribution_share"}},
        )
        self.assertTrue(isinstance(out, dict))

    def test_comparison_precheck_clarifies_missing_month_anchor(self):
        mod = _load_module()
        out = mod._comparison_precheck(
            message="Show Yangon revenue month over month",
            business_spec={
                "task_class": "comparison",
                "filters": {
                    "_comparison_missing_filter_kind": "comparison_month_anchor",
                },
            },
            previous_topic_state={},
        )
        clarify = out.get("clarify_decision") if isinstance(out.get("clarify_decision"), dict) else {}
        self.assertTrue(bool(clarify.get("should_clarify")))
        self.assertEqual(str(clarify.get("target_filter_key") or ""), "comparison_month_anchor")
        self.assertEqual(
            str(clarify.get("question") or ""),
            str(mod.clarification_question_for_filter_kind("comparison_month_anchor") or ""),
        )

    def test_comparison_precheck_returns_weekly_unsupported_payload(self):
        mod = _load_module()
        out = mod._comparison_precheck(
            message="Compare Yangon revenue week over week",
            business_spec={
                "task_class": "comparison",
                "subject": "territories",
                "metric": "revenue",
                "filters": {
                    "_comparison_unsupported_reason": "weekly_period_comparison_not_supported",
                },
            },
            previous_topic_state={},
        )
        payload = out.get("payload") if isinstance(out.get("payload"), dict) else {}
        self.assertEqual(str(payload.get("type") or ""), "error")
        self.assertIn("week over week", str(payload.get("text") or "").lower())
        tool_messages = [str(x) for x in list(payload.get("_tool_messages") or []) if str(x or "").strip()]
        self.assertTrue(any("COMPARISON_WEEKLY_UNSUPPORTED" in msg for msg in tool_messages))

    def test_comparison_precheck_returns_quarterly_unsupported_payload(self):
        mod = _load_module()
        out = mod._comparison_precheck(
            message="Compare Yangon revenue quarter over quarter",
            business_spec={
                "task_class": "comparison",
                "subject": "territories",
                "metric": "revenue",
                "filters": {
                    "_comparison_unsupported_reason": "quarterly_period_comparison_not_supported",
                },
            },
            previous_topic_state={},
        )
        payload = out.get("payload") if isinstance(out.get("payload"), dict) else {}
        self.assertEqual(str(payload.get("type") or ""), "error")
        self.assertIn("quarter over quarter", str(payload.get("text") or "").lower())
        tool_messages = [str(x) for x in list(payload.get("_tool_messages") or []) if str(x or "").strip()]
        self.assertTrue(any("COMPARISON_QUARTERLY_UNSUPPORTED" in msg for msg in tool_messages))

    def test_delete_draft_keeps_confirmation_stage_when_write_disabled(self):
        mod = _load_module()
        orig_is_write_enabled = mod._is_write_enabled
        orig_generate_business_request_spec = mod.generate_business_request_spec
        orig_infer_write_request = mod.infer_write_request
        try:
            mod._is_write_enabled = lambda: False
            mod.generate_business_request_spec = lambda **kwargs: {
                "spec": {
                    "intent": "READ",
                    "task_class": "analytical_read",
                    "filters": {},
                    "output_contract": {"mode": "detail", "minimal_columns": []},
                }
            }
            mod.infer_write_request = lambda message: {
                "intent": "WRITE_DRAFT",
                "operation": "delete",
                "doctype": "ToDo",
                "document_id": "TD-0001",
                "confidence": 0.9,
            }
            out = mod.execute_unified_read_turn(
                message="Delete ToDo TD-0001",
                session_name="UT-WR-02",
                user="Administrator",
            )
        finally:
            mod._is_write_enabled = orig_is_write_enabled
            mod.generate_business_request_spec = orig_generate_business_request_spec
            mod.infer_write_request = orig_infer_write_request

        pending = out.get("_pending_state") if isinstance(out.get("_pending_state"), dict) else {}
        write_draft = pending.get("write_draft") if isinstance(pending.get("write_draft"), dict) else {}
        self.assertEqual(str(out.get("type") or ""), "text")
        self.assertEqual(str(pending.get("mode") or ""), "write_confirmation")
        self.assertEqual(str(write_draft.get("operation") or ""), "delete")
        self.assertIn("Reply **confirm**", str(out.get("text") or ""))

    def test_create_draft_still_blocks_when_write_disabled(self):
        mod = _load_module()
        orig_is_write_enabled = mod._is_write_enabled
        orig_generate_business_request_spec = mod.generate_business_request_spec
        orig_infer_write_request = mod.infer_write_request
        try:
            mod._is_write_enabled = lambda: False
            mod.generate_business_request_spec = lambda **kwargs: {
                "spec": {
                    "intent": "READ",
                    "task_class": "analytical_read",
                    "filters": {},
                    "output_contract": {"mode": "detail", "minimal_columns": []},
                }
            }
            mod.infer_write_request = lambda message: {
                "intent": "WRITE_DRAFT",
                "operation": "create",
                "doctype": "ToDo",
                "document_id": "",
                "confidence": 0.9,
            }
            out = mod.execute_unified_read_turn(
                message="Create a ToDo for follow-up",
                session_name="UT-WR-01",
                user="Administrator",
            )
        finally:
            mod._is_write_enabled = orig_is_write_enabled
            mod.generate_business_request_spec = orig_generate_business_request_spec
            mod.infer_write_request = orig_infer_write_request

        self.assertEqual(str(out.get("type") or ""), "text")
        self.assertIn("Write-actions are disabled", str(out.get("text") or ""))
        self.assertFalse(isinstance(out.get("_pending_state"), dict))

    def test_confirmed_delete_blocks_execution_when_write_disabled(self):
        mod = _load_module()
        orig_is_write_enabled = mod._is_write_enabled
        try:
            mod._is_write_enabled = lambda: False
            out = mod._handle_write_confirmation(
                message="confirm",
                pending={
                    "mode": "write_confirmation",
                    "write_draft": {
                        "doctype": "ToDo",
                        "operation": "delete",
                        "payload": {"name": "TD-0001"},
                    },
                },
                source="report_qa_continue",
            )
        finally:
            mod._is_write_enabled = orig_is_write_enabled

        self.assertEqual(str(out.get("type") or ""), "text")
        self.assertIn("Write-actions are disabled", str(out.get("text") or ""))
        self.assertTrue(bool(out.get("_clear_pending_state")))

    def test_confirmed_delete_executes_when_write_enabled(self):
        mod = _load_module()
        orig_is_write_enabled = mod._is_write_enabled
        orig_write_execute_fn = mod._write_execute_fn
        try:
            mod._is_write_enabled = lambda: True
            mod._write_execute_fn = lambda draft: {"status": "success", "name": "TD-0001"}
            out = mod._handle_write_confirmation(
                message="confirm",
                pending={
                    "mode": "write_confirmation",
                    "write_draft": {
                        "doctype": "ToDo",
                        "operation": "delete",
                        "payload": {"name": "TD-0001"},
                    },
                },
                source="report_qa_continue",
            )
        finally:
            mod._is_write_enabled = orig_is_write_enabled
            mod._write_execute_fn = orig_write_execute_fn

        self.assertEqual(str(out.get("type") or ""), "text")
        self.assertEqual(str(out.get("text") or ""), "Confirmed. Deleted **ToDo** `TD-0001`.")
        self.assertTrue(bool(out.get("_clear_pending_state")))

    def test_enrich_minimal_columns_from_selected_report_metadata(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_type": "ranking",
            "task_class": "analytical_read",
            "subject": "products",
            "metric": "sold quantity",
            "group_by": ["item"],
            "top_n": 10,
            "output_contract": {"mode": "top_n", "minimal_columns": ["item", "sold quantity"]},
        }
        out = mod._enrich_minimal_columns_from_report_metadata(
            spec_obj=spec,
            message="Top 10 products by sold quantity last month with Item Name",
            selected_report="Item-wise Sales Register",
            last_result_payload=None,
        )
        minimal_cols = [
            str(x).strip().lower()
            for x in list((out.get("output_contract") or {}).get("minimal_columns") or [])
            if str(x).strip()
        ]
        self.assertEqual(minimal_cols, ["item", "sold quantity", "item name"])

    def test_enrich_minimal_columns_prefers_specific_metric_name_over_generic_amount(self):
        mod = _load_module()
        spec = {
            "intent": "READ",
            "task_type": "ranking",
            "task_class": "analytical_read",
            "subject": "suppliers",
            "metric": "purchase amount",
            "group_by": ["supplier"],
            "top_n": 10,
            "output_contract": {"mode": "top_n", "minimal_columns": ["supplier", "purchase amount"]},
        }
        out = mod._enrich_minimal_columns_from_report_metadata(
            spec_obj=spec,
            message="Top 10 suppliers by purchase amount last month",
            selected_report="Supplier Ledger Summary",
            last_result_payload=None,
        )
        minimal_cols = [
            str(x).strip().lower()
            for x in list((out.get("output_contract") or {}).get("minimal_columns") or [])
            if str(x).strip()
        ]
        self.assertEqual(minimal_cols, ["supplier", "purchase amount"])


if __name__ == "__main__":
    unittest.main()
