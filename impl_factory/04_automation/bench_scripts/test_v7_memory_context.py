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
        self.assertIn("group_by_from_message_dimension", list(meta.get("corrections_applied") or []))

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


if __name__ == "__main__":
    unittest.main()
