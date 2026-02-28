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
        self.assertIn("Show me the latest 7 Invoice", str(out.get("resume_message") or ""))
        self.assertIn("Sales Invoice", str(out.get("resume_message") or ""))

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
                    spec_obj=spec,
                    memory_meta=memory_meta,
                    last_result_payload=last_result,
                )
            )
        )
        promoted = mod._promote_spec_to_transform_followup(spec_obj=spec)
        self.assertEqual(str(promoted.get("intent") or ""), "TRANSFORM_LAST")
        self.assertEqual(str(promoted.get("task_class") or ""), "transform_followup")


if __name__ == "__main__":
    unittest.main()
