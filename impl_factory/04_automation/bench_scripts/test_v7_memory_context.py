from __future__ import annotations

import sys
import unittest
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MEMORY_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/memory.py"
_spec = importlib.util.spec_from_file_location("v7_memory_module", str(MEMORY_PATH))
if _spec is None or _spec.loader is None:
    raise RuntimeError("Unable to load v7 memory module")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
apply_memory_context = _mod.apply_memory_context
build_topic_state = _mod.build_topic_state


def _base_spec() -> dict:
    return {
        "intent": "READ",
        "task_type": "detail",
        "domain": "unknown",
        "subject": "",
        "metric": "",
        "aggregation": "none",
        "group_by": [],
        "filters": {},
        "time_scope": {"mode": "none", "value": ""},
        "top_n": 0,
        "output_contract": {"mode": "detail", "minimal_columns": []},
    }


class V7MemoryContextTests(unittest.TestCase):
    def test_anchors_domain_for_underspecified_followup(self):
        spec = _base_spec()
        spec.update(
            {
                "task_type": "kpi",
                "metric": "outstanding amount",
                "output_contract": {"mode": "kpi", "minimal_columns": []},
            }
        )
        state = {
            "active_topic": {
                "domain": "finance",
                "subject": "accounts receivable",
                "metric": "count of party",
                "group_by": [],
                "filters": {"party_type": "Customer"},
                "time_scope": {"mode": "as_of", "value": "today"},
                "top_n": 0,
            },
            "active_result": {},
        }
        out = apply_memory_context(business_spec=spec, message="So how much in total?", topic_state=state)
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}

        self.assertEqual(str(merged.get("domain") or ""), "finance")
        self.assertIn("domain", list(meta.get("anchors_applied") or []))

    def test_does_not_anchor_domain_on_strong_topic_switch(self):
        spec = _base_spec()
        spec.update(
            {
                "domain": "sales",
                "subject": "customer sales by territory",
                "metric": "revenue",
                "filters": {"territory": "Yangon"},
                "task_type": "ranking",
                "output_contract": {"mode": "top_n", "minimal_columns": ["territory", "revenue"]},
                "top_n": 5,
            }
        )
        state = {
            "active_topic": {
                "domain": "finance",
                "subject": "accounts payable",
                "metric": "outstanding amount",
                "group_by": ["supplier"],
                "filters": {"party_type": "Supplier"},
                "time_scope": {"mode": "as_of", "value": "today"},
                "top_n": 0,
            },
            "active_result": {},
        }
        out = apply_memory_context(business_spec=spec, message="Top 5 territories by revenue", topic_state=state)
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}

        self.assertEqual(str(merged.get("domain") or ""), "sales")
        self.assertTrue(bool(meta.get("topic_switched")))
        self.assertNotIn("domain", list(meta.get("anchors_applied") or []))

    def test_followup_can_infer_group_by_dimension_from_message(self):
        spec = _base_spec()
        spec.update(
            {
                "domain": "inventory",
                "subject": "stock balance",
                "metric": "stock balance",
                "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
                "task_type": "detail",
                "output_contract": {"mode": "detail", "minimal_columns": []},
            }
        )
        state = {
            "active_topic": {
                "domain": "inventory",
                "subject": "stock balance",
                "metric": "stock balance",
                "group_by": [],
                "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
                "time_scope": {"mode": "as_of", "value": "today"},
                "top_n": 0,
            },
            "active_result": {},
        }
        out = apply_memory_context(
            business_spec=spec,
            message="I mean stock per item in Yangon Main Warehouse",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}

        group_by = [str(x).strip().lower() for x in list(merged.get("group_by") or []) if str(x).strip()]
        self.assertIn("item", group_by)
        corrections = list(meta.get("corrections_applied") or [])
        self.assertTrue(
            ("group_by_from_message_dimension" in corrections) or ("group_by_from_message_semantics" in corrections)
        )

    def test_followup_adds_item_dimension_even_when_warehouse_already_requested(self):
        spec = _base_spec()
        spec.update(
            {
                "domain": "inventory",
                "subject": "stock balance in warehouse",
                "metric": "stock balance",
                "dimensions": ["warehouse"],
                "group_by": ["warehouse"],
                "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
                "task_type": "detail",
                "output_contract": {"mode": "detail", "minimal_columns": ["warehouse", "stock balance"]},
            }
        )
        state = {
            "active_topic": {
                "domain": "inventory",
                "subject": "stock balance in warehouse",
                "metric": "stock balance",
                "group_by": ["warehouse"],
                "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
                "time_scope": {"mode": "as_of", "value": "today"},
                "top_n": 0,
            },
            "active_result": {},
        }
        out = apply_memory_context(
            business_spec=spec,
            message="I mean stock per item in Yangon Main Warehouse",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        group_by = [str(x).strip().lower() for x in list(merged.get("group_by") or []) if str(x).strip()]
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        minimal_cols = [
            str(x).strip().lower()
            for x in list(output_contract.get("minimal_columns") or [])
            if str(x).strip()
        ]
        self.assertIn("item", group_by)
        self.assertNotIn("warehouse", group_by)
        self.assertIn("item", minimal_cols)

    def test_granularity_refinement_followup_requires_fresh_read(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "TRANSFORM_LAST",
                "domain": "inventory",
                "subject": "stock balance",
                "metric": "stock balance",
                "group_by": [],
                "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
                "task_type": "detail",
                "task_class": "transform_followup",
                "output_contract": {"mode": "detail", "minimal_columns": ["warehouse", "stock balance", "item"]},
                "ambiguities": [],
            }
        )
        state = {
            "active_topic": {
                "domain": "inventory",
                "subject": "stock balance",
                "metric": "stock balance",
                "task_class": "detail_projection",
                "group_by": [],
                "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
                "time_scope": {"mode": "as_of", "value": "today"},
                "top_n": 0,
                "report_name": "Warehouse Wise Stock Balance",
            },
            "active_result": {
                "report_name": "Warehouse Wise Stock Balance",
                "output_mode": "detail",
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="I mean stock balance per item in Yangon Main Warehouse",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        self.assertEqual(str(merged.get("intent") or ""), "READ")
        self.assertEqual(str(merged.get("task_class") or ""), "detail_projection")
        self.assertEqual(str(merged.get("task_type") or ""), "detail")
        self.assertIn("item", [str(x).strip().lower() for x in list(merged.get("group_by") or []) if str(x).strip()])
        self.assertIn("granularity_refinement_requires_read", list(meta.get("corrections_applied") or []))

    def test_latest_record_doctype_followup_suppresses_metric_inference(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "list_latest_records",
                "domain": "sales",
                "subject": "sales invoices",
                "metric": "revenue",
                "filters": {"doctype": "Sales Invoice"},
                "top_n": 7,
                "output_contract": {"mode": "top_n", "minimal_columns": ["revenue"]},
            }
        )
        out = apply_memory_context(
            business_spec=spec,
            message="Show me the latest 7 Sales Invoice",
            topic_state={},
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        self.assertEqual(str(merged.get("metric") or ""), "")
        self.assertEqual(list(merged.get("dimensions") or []), [])
        self.assertEqual(list(merged.get("group_by") or []), [])
        oc = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        self.assertEqual(list(oc.get("minimal_columns") or []), [])
        self.assertIn("latest_record_doctype_suppresses_metric_inference", list(meta.get("corrections_applied") or []))

    def test_followup_reuses_previous_filter_for_same_reference(self):
        spec = _base_spec()
        spec.update(
            {
                "domain": "inventory",
                "subject": "stock balance",
                "metric": "stock balance",
                "filters": {"warehouse": "same warehouse"},
                "task_type": "detail",
                "output_contract": {"mode": "detail", "minimal_columns": ["warehouse", "stock balance"]},
            }
        )
        state = {
            "active_topic": {
                "domain": "inventory",
                "subject": "stock balance",
                "metric": "stock balance",
                "group_by": [],
                "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
                "time_scope": {"mode": "as_of", "value": "today"},
                "top_n": 0,
            },
            "active_result": {},
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Show stock balance in the same warehouse",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}

        filters = merged.get("filters") if isinstance(merged.get("filters"), dict) else {}
        self.assertEqual(str(filters.get("warehouse") or ""), "Yangon Main Warehouse - MMOB")
        self.assertIn("filter_reference", list(meta.get("anchors_applied") or []))

    def test_followup_updates_top_n_from_explicit_numeric_correction(self):
        spec = _base_spec()
        state = {
            "active_topic": {
                "domain": "inventory",
                "subject": "stock balance",
                "metric": "stock balance",
                "group_by": ["warehouse"],
                "filters": {},
                "time_scope": {"mode": "as_of", "value": "today"},
                "top_n": 3,
            },
            "active_result": {
                "output_mode": "top_n",
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="I mean top 5",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        self.assertEqual(int(merged.get("top_n") or 0), 5)
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        self.assertEqual(str(output_contract.get("mode") or ""), "top_n")
        self.assertIn("top_n_from_message_followup", list(meta.get("corrections_applied") or []))

    def test_build_topic_state_persists_source_columns(self):
        state = build_topic_state(
            previous_state={},
            business_spec={
                "task_class": "analytical_read",
                "subject": "products",
                "metric": "revenue",
                "group_by": ["item"],
                "top_n": 10,
                "filters": {},
                "time_scope": {"mode": "relative", "value": "last_month"},
                "output_contract": {"mode": "top_n", "minimal_columns": ["item", "revenue"]},
            },
            resolved={"selected_report": "Item-wise Sales Register"},
            payload={
                "type": "report_table",
                "report_name": "Item-wise Sales Register",
                "_output_mode": "top_n",
                "_source_columns": [
                    {"fieldname": "item_code", "label": "Item Code", "fieldtype": "Link"},
                    {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data"},
                    {"fieldname": "amount", "label": "Amount", "fieldtype": "Currency"},
                ],
            },
            clarification_decision={"should_clarify": False},
            memory_meta={},
            message="Top 10 Products by revenue last month",
        )
        active_result = state.get("active_result") if isinstance(state.get("active_result"), dict) else {}
        source_columns = [c for c in list(active_result.get("source_columns") or []) if isinstance(c, dict)]
        labels = [str(c.get("label") or "").strip().lower() for c in source_columns]
        self.assertIn("item name", labels)
        self.assertIn("amount", labels)

    def test_build_topic_state_infers_threshold_primary_dimension_from_report_contract(self):
        state = build_topic_state(
            previous_state={},
            business_spec={
                "task_class": "threshold_exception_list",
                "subject": "overdue sales invoices",
                "metric": "invoice amount",
                "group_by": [],
                "top_n": 0,
                "filters": {
                    "_threshold_rule": {
                        "metric": "invoice_amount",
                        "comparator": "gt",
                        "value": 5000000.0,
                        "value_present": True,
                    }
                },
                "time_scope": {"mode": "none", "value": ""},
                "output_contract": {"mode": "detail", "minimal_columns": ["sales invoice number", "grand total"]},
            },
            resolved={"selected_report": "Latest Sales Invoice"},
            payload={
                "type": "report_table",
                "report_name": "Latest Sales Invoice",
                "_output_mode": "detail",
                "_source_columns": [
                    {"fieldname": "name", "label": "Sales Invoice Number", "fieldtype": "Link"},
                    {"fieldname": "grand_total", "label": "Grand Total", "fieldtype": "Currency"},
                ],
            },
            clarification_decision={"should_clarify": False},
            memory_meta={},
            message="Show overdue sales invoices above 5000000",
        )
        active_topic = state.get("active_topic") if isinstance(state.get("active_topic"), dict) else {}
        active_result = state.get("active_result") if isinstance(state.get("active_result"), dict) else {}
        self.assertEqual(list(active_topic.get("group_by") or []), ["invoice"])
        self.assertEqual(list(active_result.get("group_by") or []), ["invoice"])

    def test_build_topic_state_uses_payload_title_when_threshold_report_name_missing(self):
        state = build_topic_state(
            previous_state={},
            business_spec={
                "task_class": "threshold_exception_list",
                "subject": "warehouses",
                "metric": "stock balance",
                "group_by": [],
                "top_n": 0,
                "filters": {
                    "_threshold_rule": {
                        "metric": "stock_balance",
                        "comparator": "gt",
                        "value": 100000000.0,
                        "value_present": True,
                    }
                },
                "time_scope": {"mode": "none", "value": ""},
                "output_contract": {"mode": "detail", "minimal_columns": ["warehouse", "stock balance"]},
            },
            resolved={"selected_report": ""},
            payload={
                "type": "report_table",
                "title": "Warehouse Wise Stock Balance",
                "_output_mode": "detail",
                "_source_columns": [
                    {"fieldname": "name", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
            },
            clarification_decision={"should_clarify": False},
            memory_meta={},
            message="Show warehouses with stock balance above 100000000",
        )
        active_topic = state.get("active_topic") if isinstance(state.get("active_topic"), dict) else {}
        active_result = state.get("active_result") if isinstance(state.get("active_result"), dict) else {}
        self.assertEqual(str(active_topic.get("report_name") or ""), "Warehouse Wise Stock Balance")
        self.assertEqual(list(active_topic.get("group_by") or []), ["warehouse"])
        self.assertEqual(str(active_result.get("report_name") or ""), "Warehouse Wise Stock Balance")
        self.assertEqual(list(active_result.get("group_by") or []), ["warehouse"])

    def test_projection_followup_reuses_active_report_context_from_source_columns(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "READ",
                "task_type": "ranking",
                "task_class": "list_latest_records",
                "subject": "products",
                "metric": "",
                "group_by": ["item"],
                "top_n": 5,
                "time_scope": {"mode": "none", "value": ""},
                "output_contract": {"mode": "top_n", "minimal_columns": ["item"]},
            }
        )
        state = {
            "active_topic": {
                "domain": "sales",
                "subject": "products",
                "metric": "revenue",
                "task_class": "analytical_read",
                "group_by": ["item"],
                "filters": {"company": "Mingalar Mobile Distribution Co., Ltd."},
                "time_scope": {"mode": "relative", "value": "last_month"},
                "top_n": 10,
                "report_name": "Item-wise Sales Register",
            },
            "active_result": {
                "report_name": "Item-wise Sales Register",
                "output_mode": "top_n",
                "source_columns": [
                    {"fieldname": "item_code", "label": "Item Code", "fieldtype": "Link"},
                    {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data"},
                    {"fieldname": "amount", "label": "Amount", "fieldtype": "Currency"},
                ],
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Show the previous table with Item Name",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        self.assertEqual(str(merged.get("metric") or ""), "revenue")
        self.assertEqual(int(merged.get("top_n") or 0), 10)
        self.assertEqual((merged.get("time_scope") or {}).get("value"), "last_month")
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        minimal_cols = [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()]
        self.assertEqual(str(output_contract.get("mode") or ""), "top_n")
        self.assertIn("item", minimal_cols)
        self.assertIn("revenue", minimal_cols)
        self.assertIn("item name", minimal_cols)
        self.assertIn("projection_columns", list(meta.get("anchors_applied") or []))
        self.assertIn("projection_followup_from_active_report", list(meta.get("corrections_applied") or []))

    def test_fresh_explicit_read_resets_stale_shape_and_transform_carryover(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "READ",
                "task_type": "ranking",
                "task_class": "analytical_read",
                "subject": "products",
                "metric": "sold quantity",
                "group_by": ["item"],
                "top_n": 10,
                "time_scope": {"mode": "relative", "value": "last_month"},
                "output_contract": {"mode": "top_n", "minimal_columns": ["item", "sold quantity", "item name"]},
                "ambiguities": ["transform_sort:asc", "transform_scale:million"],
            }
        )
        state = {
            "active_topic": {
                "domain": "sales",
                "subject": "products",
                "metric": "sold quantity",
                "task_class": "analytical_read",
                "group_by": ["item"],
                "filters": {},
                "time_scope": {"mode": "relative", "value": "last_month"},
                "top_n": 10,
                "report_name": "Item-wise Sales Register",
            },
            "active_result": {
                "report_name": "Item-wise Sales Register",
                "output_mode": "top_n",
                "source_columns": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link"},
                    {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data"},
                    {"fieldname": "qty", "label": "Sold Quantity", "fieldtype": "Float"},
                ],
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Top 10 products by sold quantity last month",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        minimal_cols = [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()]
        self.assertEqual(minimal_cols, ["item", "sold quantity"])
        self.assertEqual(
            [str(x).strip().lower() for x in list(merged.get("ambiguities") or []) if str(x).strip()],
            ["transform_sort:desc"],
        )
        self.assertNotIn("projection_followup_from_active_report", list(meta.get("corrections_applied") or []))
        self.assertIn("fresh_read_contract_reset", list(meta.get("corrections_applied") or []))

    def test_fresh_explicit_read_keeps_explicit_projection_columns(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "READ",
                "task_type": "ranking",
                "task_class": "analytical_read",
                "subject": "products",
                "metric": "sold quantity",
                "group_by": ["item"],
                "top_n": 10,
                "time_scope": {"mode": "relative", "value": "last_month"},
                "output_contract": {"mode": "top_n", "minimal_columns": ["item", "sold quantity", "item name"]},
                "ambiguities": ["transform_scale:million"],
            }
        )
        state = {
            "active_topic": {
                "domain": "sales",
                "subject": "products",
                "metric": "sold quantity",
                "task_class": "analytical_read",
                "group_by": ["item"],
                "filters": {},
                "time_scope": {"mode": "relative", "value": "last_month"},
                "top_n": 10,
                "report_name": "Item-wise Sales Register",
            },
            "active_result": {
                "report_name": "Item-wise Sales Register",
                "output_mode": "top_n",
                "source_columns": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link"},
                    {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data"},
                    {"fieldname": "qty", "label": "Sold Quantity", "fieldtype": "Float"},
                ],
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Top 10 products by sold quantity last month, show with Item Name",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        minimal_cols = [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()]
        self.assertEqual(minimal_cols, ["item", "sold quantity", "item name"])

    def test_fresh_latest_record_read_resets_stale_topic_carryover(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "list_latest_records",
                "subject": "invoices",
                "metric": "",
                "group_by": [],
                "top_n": 7,
                "time_scope": {"mode": "none", "value": ""},
                "output_contract": {"mode": "top_n", "minimal_columns": []},
            }
        )
        state = {
            "active_topic": {
                "domain": "inventory",
                "subject": "stock balance",
                "metric": "stock balance",
                "task_class": "analytical_read",
                "group_by": ["warehouse"],
                "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
                "time_scope": {"mode": "as_of", "value": "today"},
                "top_n": 3,
                "report_name": "Warehouse Wise Stock Balance",
            },
            "active_result": {
                "report_name": "Warehouse Wise Stock Balance",
                "output_mode": "top_n",
                "source_columns": [
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Show me the latest 7 Invoice",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        self.assertTrue(bool(meta.get("topic_switched")))
        self.assertEqual(str(merged.get("subject") or ""), "invoices")
        self.assertEqual(str(merged.get("metric") or ""), "")
        self.assertEqual(list(merged.get("group_by") or []), [])
        self.assertEqual(int(merged.get("top_n") or 0), 7)
        self.assertEqual(merged.get("filters") or {}, {})

    def test_explicit_read_rebinds_metric_and_dimension_from_message_semantics(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "READ",
                "task_type": "ranking",
                "task_class": "analytical_read",
                "subject": "products",
                "metric": "sold quantity",
                "group_by": ["item"],
                "top_n": 10,
                "time_scope": {"mode": "relative", "value": "last_month"},
                "output_contract": {"mode": "top_n", "minimal_columns": ["item", "sold quantity", "supplier", "purchase amount"]},
                "ambiguities": ["transform_sort:desc"],
            }
        )
        state = {
            "active_topic": {
                "domain": "sales",
                "subject": "products",
                "metric": "sold quantity",
                "task_class": "analytical_read",
                "group_by": ["item"],
                "filters": {},
                "time_scope": {"mode": "relative", "value": "last_month"},
                "top_n": 10,
                "report_name": "Item-wise Sales Register",
            },
            "active_result": {
                "report_name": "Item-wise Sales Register",
                "output_mode": "top_n",
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Top 10 suppliers by purchase amount last month",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        self.assertEqual(str(merged.get("subject") or ""), "suppliers")
        self.assertEqual(str(merged.get("metric") or ""), "purchase amount")
        self.assertEqual(list(merged.get("group_by") or []), ["supplier"])
        self.assertEqual(str(merged.get("domain") or ""), "purchasing")
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["supplier", "purchase amount"],
        )
        self.assertIn("metric_from_message_semantics", list(meta.get("corrections_applied") or []))
        self.assertIn("group_by_from_message_semantics", list(meta.get("corrections_applied") or []))

    def test_strong_fresh_ranking_read_does_not_get_recast_as_projection_followup(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "READ",
                "task_type": "ranking",
                "task_class": "transform_followup",
                "subject": "products",
                "metric": "sold quantity",
                "group_by": ["item"],
                "top_n": 10,
                "time_scope": {"mode": "relative", "value": "last_month"},
                "output_contract": {"mode": "top_n", "minimal_columns": ["item", "sold quantity", "customer", "revenue"]},
            }
        )
        state = {
            "active_topic": {
                "domain": "sales",
                "subject": "products",
                "metric": "sold quantity",
                "task_class": "analytical_read",
                "group_by": ["item"],
                "filters": {},
                "time_scope": {"mode": "relative", "value": "last_month"},
                "top_n": 10,
                "report_name": "Item-wise Sales Register",
            },
            "active_result": {
                "report_name": "Item-wise Sales Register",
                "output_mode": "top_n",
                "source_columns": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link"},
                    {"fieldname": "customer", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "amount", "label": "Revenue", "fieldtype": "Currency"},
                ],
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Top 7 Customers by Revenue Last Month",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        self.assertEqual(str(merged.get("subject") or ""), "customers")
        self.assertEqual(str(merged.get("metric") or ""), "revenue")
        self.assertEqual(list(merged.get("group_by") or []), ["customer"])
        self.assertEqual(int(merged.get("top_n") or 0), 7)
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["customer", "revenue"],
        )
        self.assertNotIn("projection_followup_from_active_report", list(meta.get("corrections_applied") or []))
        self.assertIn("top_n_from_message_semantics", list(meta.get("corrections_applied") or []))

    def test_low_signal_transform_followup_rebinds_to_active_topic(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "TRANSFORM_LAST",
                "task_type": "kpi",
                "task_class": "transform_followup",
                "subject": "purchase amount",
                "metric": "purchase amount",
                "group_by": [],
                "top_n": 0,
                "time_scope": {"mode": "none", "value": ""},
                "output_contract": {"mode": "kpi", "minimal_columns": ["purchase amount"]},
                "ambiguities": ["transform_scale:million"],
            }
        )
        state = {
            "active_topic": {
                "domain": "inventory",
                "subject": "warehouses",
                "metric": "stock balance",
                "task_class": "analytical_read",
                "group_by": ["warehouse"],
                "filters": {},
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 3,
                "report_name": "Warehouse Wise Stock Balance",
            },
            "active_result": {
                "report_name": "Warehouse Wise Stock Balance",
                "output_mode": "top_n",
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Show in Million",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        self.assertEqual(str(merged.get("subject") or ""), "warehouses")
        self.assertEqual(str(merged.get("metric") or ""), "stock balance")
        self.assertEqual(list(merged.get("group_by") or []), ["warehouse"])
        self.assertEqual(int(merged.get("top_n") or 0), 3)
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        self.assertEqual(str(output_contract.get("mode") or ""), "top_n")
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["warehouse", "stock balance"],
        )
        self.assertIn("followup_rebind_to_active_topic", list(meta.get("corrections_applied") or []))

    def test_threshold_top_n_followup_rebind_switches_detail_result_to_top_n_mode(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "TRANSFORM_LAST",
                "task_type": "detail",
                "task_class": "transform_followup",
                "subject": "",
                "metric": "",
                "domain": "unknown",
                "group_by": [],
                "top_n": 0,
                "time_scope": {"mode": "none", "value": ""},
                "output_contract": {"mode": "detail", "minimal_columns": []},
                "ambiguities": [],
            }
        )
        state = {
            "active_topic": {
                "domain": "finance",
                "subject": "customers",
                "metric": "outstanding amount",
                "task_class": "threshold_exception_list",
                "group_by": ["customer"],
                "filters": {
                    "_threshold_rule": {
                        "metric": "outstanding_amount",
                        "comparator": "gt",
                        "value": 10_000_000.0,
                        "value_present": True,
                    }
                },
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 0,
                "report_name": "Customer Ledger Summary",
            },
            "active_result": {
                "report_name": "Customer Ledger Summary",
                "output_mode": "detail",
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Top 5 only",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        self.assertEqual(str(merged.get("subject") or ""), "customers")
        self.assertEqual(str(merged.get("metric") or ""), "outstanding amount")
        self.assertEqual(list(merged.get("group_by") or []), ["customer"])
        self.assertEqual(int(merged.get("top_n") or 0), 5)
        self.assertEqual(str(output_contract.get("mode") or ""), "top_n")
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["customer", "outstanding amount"],
        )
        self.assertIn("followup_rebind_to_active_topic", list(meta.get("corrections_applied") or []))

    def test_threshold_top_n_followup_rebind_infers_sparse_group_by_and_metric_from_report_contract(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "TRANSFORM_LAST",
                "task_type": "detail",
                "task_class": "transform_followup",
                "subject": "",
                "metric": "",
                "domain": "unknown",
                "group_by": [],
                "top_n": 0,
                "time_scope": {"mode": "none", "value": ""},
                "output_contract": {"mode": "detail", "minimal_columns": []},
                "ambiguities": [],
            }
        )
        state = {
            "active_topic": {
                "domain": "inventory",
                "subject": "warehouses",
                "metric": "",
                "task_class": "threshold_exception_list",
                "group_by": [],
                "filters": {
                    "_threshold_rule": {
                        "metric": "stock_balance",
                        "comparator": "gt",
                        "value": 100_000_000.0,
                        "value_present": True,
                    }
                },
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 0,
                "report_name": "Warehouse Wise Stock Balance",
            },
            "active_result": {
                "report_name": "Warehouse Wise Stock Balance",
                "output_mode": "detail",
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Top 3 only",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        self.assertEqual(str(merged.get("subject") or ""), "warehouses")
        self.assertEqual(str(merged.get("metric") or ""), "stock balance")
        self.assertEqual(list(merged.get("group_by") or []), ["warehouse"])
        self.assertEqual(int(merged.get("top_n") or 0), 3)
        self.assertEqual(str(output_contract.get("mode") or ""), "top_n")
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["warehouse", "stock balance"],
        )
        self.assertEqual(str(merged.get("intent") or ""), "TRANSFORM_LAST")
        self.assertEqual(str(merged.get("task_class") or ""), "transform_followup")
        self.assertIn("threshold_followup_rebind_to_transform_last", list(meta.get("corrections_applied") or []))
        self.assertIn("followup_rebind_to_active_topic", list(meta.get("corrections_applied") or []))

    def test_fresh_threshold_read_does_not_treat_threshold_value_as_top_n(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "threshold_exception_list",
                "subject": "customers",
                "metric": "outstanding amount",
                "domain": "finance",
                "group_by": ["customer"],
                "top_n": 0,
                "filters": {
                    "_threshold_rule": {
                        "metric": "outstanding_amount",
                        "comparator": "gt",
                        "value": 2800000.0,
                        "value_present": True,
                    }
                },
                "time_scope": {"mode": "none", "value": ""},
                "output_contract": {"mode": "detail", "minimal_columns": ["customer", "outstanding amount"]},
                "ambiguities": [],
            }
        )
        state = {
            "active_topic": {
                "domain": "finance",
                "subject": "customers",
                "metric": "outstanding amount",
                "task_class": "threshold_exception_list",
                "group_by": ["customer"],
                "filters": {
                    "_threshold_rule": {
                        "metric": "outstanding_amount",
                        "comparator": "gt",
                        "value": 1000000.0,
                        "value_present": True,
                    }
                },
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 0,
                "report_name": "Customer Ledger Summary",
            },
            "active_result": {
                "report_name": "Customer Ledger Summary",
                "output_mode": "detail",
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Show customers with outstanding amount above 2,800,000.00",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        filters = merged.get("filters") if isinstance(merged.get("filters"), dict) else {}
        rule = filters.get("_threshold_rule") if isinstance(filters.get("_threshold_rule"), dict) else {}
        self.assertEqual(int(merged.get("top_n") or 0), 0)
        self.assertEqual(float(rule.get("value") or 0.0), 2800000.0)
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["customer", "outstanding amount"],
        )

    def test_threshold_projection_only_followup_matches_raw_source_field_alias(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "TRANSFORM_LAST",
                "task_type": "detail",
                "task_class": "transform_followup",
                "subject": "",
                "metric": "",
                "domain": "unknown",
                "group_by": [],
                "top_n": 0,
                "time_scope": {"mode": "none", "value": ""},
                "output_contract": {"mode": "detail", "minimal_columns": []},
                "ambiguities": [],
            }
        )
        state = {
            "active_topic": {
                "domain": "sales",
                "subject": "overdue sales invoices",
                "metric": "",
                "task_class": "threshold_exception_list",
                "group_by": [],
                "filters": {
                    "_threshold_rule": {
                        "metric": "invoice_amount",
                        "comparator": "gt",
                        "value": 5_000_000.0,
                        "value_present": True,
                    }
                },
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 0,
                "report_name": "Latest Sales Invoice",
            },
            "active_result": {
                "report_name": "Latest Sales Invoice",
                "output_mode": "detail",
                "source_columns": [
                    {"fieldname": "name", "label": "Sales Invoice Number", "fieldtype": "Link"},
                    {"fieldname": "grand_total", "label": "Invoice Amount", "fieldtype": "Currency"},
                    {"fieldname": "customer", "label": "Customer", "fieldtype": "Link"},
                ],
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Show only sales invoice number and grand total",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        self.assertEqual(str(merged.get("subject") or ""), "overdue sales invoices")
        self.assertEqual(str(merged.get("metric") or ""), "invoice amount")
        self.assertEqual(list(merged.get("group_by") or []), ["invoice"])
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["sales invoice number", "grand total"],
        )
        self.assertEqual(str(merged.get("intent") or ""), "TRANSFORM_LAST")
        self.assertEqual(str(merged.get("task_class") or ""), "transform_followup")
        self.assertIn("threshold_projection_followup_to_transform_last", list(meta.get("corrections_applied") or []))
        self.assertIn("projection_only_followup_to_active_topic", list(meta.get("corrections_applied") or []))

    def test_contribution_projection_followup_rebinds_to_transform_last(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "TRANSFORM_LAST",
                "task_type": "detail",
                "task_class": "transform_followup",
                "subject": "",
                "metric": "",
                "domain": "unknown",
                "group_by": [],
                "top_n": 0,
                "time_scope": {"mode": "none", "value": ""},
                "output_contract": {"mode": "detail", "minimal_columns": []},
                "ambiguities": [],
            }
        )
        state = {
            "active_topic": {
                "domain": "sales",
                "subject": "customers",
                "metric": "revenue",
                "task_class": "contribution_share",
                "group_by": ["customer"],
                "filters": {
                    "_contribution_rule": {
                        "metric": "revenue",
                        "basis": "of_total",
                        "contribution_terms": ["share_of_total"],
                    }
                },
                "time_scope": {"mode": "relative", "value": "last_month"},
                "top_n": 10,
                "report_name": "Customer Ledger Summary",
            },
            "active_result": {
                "report_name": "Customer Ledger Summary",
                "output_mode": "top_n",
                "source_columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "invoiced_amount", "label": "Revenue", "fieldtype": "Currency"},
                    {"fieldname": "contribution_share", "label": "Contribution Share", "fieldtype": "Data"},
                ],
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Show only customer and contribution share",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        self.assertEqual(str(merged.get("intent") or ""), "TRANSFORM_LAST")
        self.assertEqual(str(merged.get("task_class") or ""), "transform_followup")
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["customer", "contribution share"],
        )
        self.assertIn("contribution_projection_followup_to_transform_last", list(meta.get("corrections_applied") or []))

    def test_ranking_direction_followup_preserves_prior_top_n_contract(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "TRANSFORM_LAST",
                "task_type": "ranking",
                "task_class": "transform_followup",
                "subject": "warehouses",
                "metric": "stock balance",
                "group_by": ["warehouse"],
                "top_n": 3,
                "time_scope": {"mode": "none", "value": ""},
                "output_contract": {"mode": "detail", "minimal_columns": ["warehouse", "stock balance"]},
                "ambiguities": ["transform_sort:desc"],
            }
        )
        state = {
            "active_topic": {
                "domain": "inventory",
                "subject": "warehouses",
                "metric": "stock balance",
                "task_class": "analytical_read",
                "group_by": ["warehouse"],
                "filters": {},
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 3,
                "report_name": "Warehouse Wise Stock Balance",
            },
            "active_result": {
                "report_name": "Warehouse Wise Stock Balance",
                "output_mode": "top_n",
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="I mean Top",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        self.assertEqual(str(merged.get("intent") or ""), "READ")
        self.assertEqual(str(merged.get("subject") or ""), "warehouses")
        self.assertEqual(str(merged.get("metric") or ""), "stock balance")
        self.assertEqual(list(merged.get("group_by") or []), ["warehouse"])
        self.assertEqual(int(merged.get("top_n") or 0), 3)
        self.assertEqual(
            [str(x).strip().lower() for x in list(merged.get("ambiguities") or []) if str(x).strip()],
            ["transform_sort:desc"],
        )
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        self.assertEqual(str(output_contract.get("mode") or ""), "top_n")
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["warehouse", "stock balance"],
        )
        self.assertIn("ranking_direction_from_message_followup", list(meta.get("corrections_applied") or []))

    def test_ranking_direction_followup_does_not_get_overwritten_by_generic_low_signal_rebind(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "TRANSFORM_LAST",
                "task_type": "ranking",
                "task_class": "transform_followup",
                "subject": "warehouses",
                "metric": "",
                "domain": "inventory",
                "group_by": [],
                "top_n": 3,
                "time_scope": {"mode": "none", "value": ""},
                "output_contract": {"mode": "detail", "minimal_columns": []},
                "ambiguities": ["transform_sort:desc"],
            }
        )
        state = {
            "active_topic": {
                "domain": "inventory",
                "subject": "warehouses",
                "metric": "stock balance",
                "task_class": "analytical_read",
                "group_by": ["warehouse"],
                "filters": {},
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 3,
                "report_name": "Warehouse Wise Stock Balance",
            },
            "active_result": {
                "report_name": "Warehouse Wise Stock Balance",
                "output_mode": "top_n",
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="I mean Top",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        self.assertEqual(str(merged.get("metric") or ""), "stock balance")
        self.assertEqual(list(merged.get("group_by") or []), ["warehouse"])
        self.assertEqual(
            [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()],
            ["warehouse", "stock balance"],
        )
        self.assertNotIn("followup_rebind_to_active_topic", list((out.get("meta") or {}).get("corrections_applied") or []))

    def test_projection_only_followup_narrows_to_explicit_requested_columns(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "TRANSFORM_LAST",
                "task_type": "detail",
                "task_class": "transform_followup",
                "subject": "products",
                "metric": "sold quantity",
                "group_by": ["item"],
                "top_n": 10,
                "time_scope": {"mode": "relative", "value": "last_month"},
                "output_contract": {"mode": "top_n", "minimal_columns": ["item", "sold quantity", "item name"]},
                "ambiguities": ["transform_projection:only"],
            }
        )
        state = {
            "active_topic": {
                "domain": "sales",
                "subject": "products",
                "metric": "sold quantity",
                "task_class": "analytical_read",
                "group_by": ["item"],
                "filters": {},
                "time_scope": {"mode": "relative", "value": "last_month"},
                "top_n": 10,
                "report_name": "Item-wise Sales Register",
            },
            "active_result": {
                "report_name": "Item-wise Sales Register",
                "output_mode": "top_n",
                "source_columns": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link"},
                    {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data"},
                    {"fieldname": "qty", "label": "Sold Quantity", "fieldtype": "Float"},
                ],
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Give me Item Name and Sold Qty only",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        minimal_cols = [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()]
        self.assertEqual(minimal_cols, ["item name", "sold quantity"])

    def test_projection_only_followup_can_narrow_to_single_dimension_alias(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "TRANSFORM_LAST",
                "task_type": "detail",
                "task_class": "transform_followup",
                "subject": "customers",
                "metric": "revenue",
                "group_by": ["customer"],
                "top_n": 7,
                "time_scope": {"mode": "relative", "value": "last_month"},
                "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "revenue"]},
                "ambiguities": ["transform_projection:only"],
            }
        )
        state = {
            "active_topic": {
                "domain": "sales",
                "subject": "customers",
                "metric": "revenue",
                "task_class": "analytical_read",
                "group_by": ["customer"],
                "filters": {},
                "time_scope": {"mode": "relative", "value": "last_month"},
                "top_n": 7,
                "report_name": "Customer Ledger Summary",
            },
            "active_result": {
                "report_name": "Customer Ledger Summary",
                "output_mode": "top_n",
                "source_columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "amount", "label": "Revenue", "fieldtype": "Currency"},
                ],
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="Give me Customer Name only",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        minimal_cols = [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()]
        self.assertEqual(minimal_cols, ["customer"])
        self.assertIn("projection_only_followup_to_active_topic", list(meta.get("corrections_applied") or []))

    def test_detail_constraint_metric_is_not_readded_as_minimal_column(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "domain": "operations",
                "subject": "material requests",
                "metric": "open requests",
                "group_by": [],
                "time_scope": {"mode": "none", "value": ""},
                "filters": {"status": "open", "context": "production"},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
                "ambiguities": ["transform_projection:only"],
            }
        )
        out = apply_memory_context(
            business_spec=spec,
            message="What are the open material requests for production",
            topic_state={},
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        minimal_cols = [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()]
        self.assertEqual(minimal_cols, [])

    def test_build_topic_state_persists_effective_threshold_metric(self):
        state = build_topic_state(
            previous_state={},
            business_spec={
                "intent": "READ",
                "task_type": "detail",
                "task_class": "threshold_exception_list",
                "domain": "sales",
                "subject": "overdue sales invoices",
                "metric": "",
                "group_by": [],
                "filters": {
                    "_threshold_rule": {
                        "metric": "invoice_amount",
                        "comparator": "gt",
                        "value": 5000000.0,
                        "value_present": True,
                        "exception_terms": ["overdue"],
                    }
                },
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
            },
            resolved={"selected_report": "Latest Sales Invoice"},
            payload={
                "type": "report_table",
                "report_name": "Latest Sales Invoice",
                "_source_columns": [
                    {"fieldname": "name", "label": "Sales Invoice Number"},
                    {"fieldname": "grand_total", "label": "Grand Total"},
                ],
            },
            clarification_decision={},
            memory_meta={},
            message="Show overdue sales invoices above 5000000",
        )
        active_topic = state.get("active_topic") if isinstance(state.get("active_topic"), dict) else {}
        self.assertEqual(str(active_topic.get("metric") or ""), "invoice amount")
        self.assertEqual(list(active_topic.get("group_by") or []), ["invoice"])

    def test_build_topic_state_prefers_threshold_metric_for_threshold_followup(self):
        state = build_topic_state(
            previous_state={},
            business_spec={
                "intent": "TRANSFORM_LAST",
                "task_type": "detail",
                "task_class": "transform_followup",
                "domain": "finance",
                "subject": "sales invoices",
                "metric": "revenue",
                "group_by": ["invoice"],
                "filters": {
                    "_threshold_rule": {
                        "metric": "invoice_amount",
                        "comparator": "gt",
                        "value": 5000000.0,
                        "value_present": True,
                    }
                },
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 5,
                "output_contract": {"mode": "top_n", "minimal_columns": ["invoice", "invoice amount"]},
            },
            resolved={"selected_report": "Latest Sales Invoice"},
            payload={
                "type": "report_table",
                "report_name": "Latest Sales Invoice",
                "_source_columns": [
                    {"fieldname": "name", "label": "Sales Invoice Number"},
                    {"fieldname": "grand_total", "label": "Grand Total"},
                ],
            },
            clarification_decision={},
            memory_meta={},
            message="Top 5 only",
        )
        active_topic = state.get("active_topic") if isinstance(state.get("active_topic"), dict) else {}
        self.assertEqual(str(active_topic.get("metric") or ""), "invoice amount")

    def test_threshold_value_followup_updates_existing_threshold_rule(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "analytical_read",
                "subject": "",
                "metric": "",
                "group_by": [],
                "dimensions": [],
                "filters": {},
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
            }
        )
        state = {
            "active_topic": {
                "domain": "inventory",
                "subject": "items",
                "metric": "stock quantity",
                "task_class": "threshold_exception_list",
                "task_type": "detail",
                "group_by": ["item"],
                "filters": {
                    "warehouse": "Yangon Main Warehouse - MMOB",
                    "_threshold_rule": {
                        "metric": "stock_quantity",
                        "comparator": "lt",
                        "value": 10.0,
                        "raw_value": "10",
                        "value_present": True,
                    },
                },
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 0,
                "report_name": "Stock Balance",
            },
            "active_result": {
                "report_name": "Stock Balance",
                "output_mode": "detail",
                "source_columns": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link"},
                    {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data"},
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "bal_qty", "label": "Stock Quantity", "fieldtype": "Float"},
                ],
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="I mean 20",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        filters = merged.get("filters") if isinstance(merged.get("filters"), dict) else {}
        rule = filters.get("_threshold_rule") if isinstance(filters.get("_threshold_rule"), dict) else {}
        output_contract = merged.get("output_contract") if isinstance(merged.get("output_contract"), dict) else {}
        minimal_cols = [str(x).strip().lower() for x in list(output_contract.get("minimal_columns") or []) if str(x).strip()]
        self.assertEqual(str(merged.get("task_class") or ""), "threshold_exception_list")
        self.assertEqual(str(merged.get("metric") or ""), "stock quantity")
        self.assertEqual(list(merged.get("group_by") or []), ["item"])
        self.assertEqual(str(filters.get("warehouse") or ""), "Yangon Main Warehouse - MMOB")
        self.assertEqual(float(rule.get("value") or 0.0), 20.0)
        self.assertEqual(str(rule.get("raw_value") or ""), "20")
        self.assertEqual(minimal_cols, ["item", "stock quantity"])
        self.assertEqual(list(merged.get("ambiguities") or []), [])
        self.assertNotIn("followup_rebind_to_active_topic", list(meta.get("corrections_applied") or []))

    def test_threshold_value_followup_allows_short_numeric_correction_at_moderate_strength(self):
        spec = _base_spec()
        spec.update(
            {
                "intent": "READ",
                "task_type": "detail",
                "task_class": "threshold_exception_list",
                "domain": "inventory",
                "subject": "items",
                "metric": "stock quantity",
                "group_by": ["item"],
                "filters": {},
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 0,
                "output_contract": {"mode": "detail", "minimal_columns": []},
            }
        )
        state = {
            "active_topic": {
                "domain": "inventory",
                "subject": "items",
                "metric": "stock quantity",
                "task_class": "threshold_exception_list",
                "task_type": "detail",
                "group_by": ["item"],
                "filters": {
                    "warehouse": "Yangon Main Warehouse - MMOB",
                    "_threshold_rule": {
                        "metric": "stock_quantity",
                        "comparator": "lt",
                        "value": 10.0,
                        "raw_value": "10",
                        "value_present": True,
                    },
                },
                "time_scope": {"mode": "none", "value": ""},
                "top_n": 0,
                "report_name": "Stock Balance",
            },
            "active_result": {
                "report_name": "Stock Balance",
                "output_mode": "detail",
                "source_columns": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link"},
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "bal_qty", "label": "Stock Quantity", "fieldtype": "Float"},
                ],
            },
        }
        out = apply_memory_context(
            business_spec=spec,
            message="I mean 20",
            topic_state=state,
        )
        merged = out.get("spec") if isinstance(out.get("spec"), dict) else {}
        meta = out.get("meta") if isinstance(out.get("meta"), dict) else {}
        filters = merged.get("filters") if isinstance(merged.get("filters"), dict) else {}
        rule = filters.get("_threshold_rule") if isinstance(filters.get("_threshold_rule"), dict) else {}
        self.assertEqual(str(merged.get("task_class") or ""), "threshold_exception_list")
        self.assertEqual(float(rule.get("value") or 0.0), 20.0)
        self.assertIn("threshold_value_from_message_followup", list(meta.get("corrections_applied") or []))


if __name__ == "__main__":
    unittest.main()
