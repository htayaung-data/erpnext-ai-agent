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
        self.assertIn("item", minimal_cols)

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


if __name__ == "__main__":
    unittest.main()
