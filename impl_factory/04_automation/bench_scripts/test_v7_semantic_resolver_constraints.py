from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/semantic_resolver.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_semantic_resolver_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load v7 semantic resolver module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7SemanticResolverConstraintTests(unittest.TestCase):
    def test_missing_required_unknown_filter_kind_triggers_dynamic_clarification(self):
        mod = _load_module()
        capability_index = {
            "reports": [
                {
                    "report_name": "Cost Center Sales Summary",
                    "constraints": {
                        "supported_filter_kinds": ["company", "cost_center", "date"],
                        "required_filter_kinds": ["cost_center"],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["sales"],
                        "dimension_hints": ["customer"],
                        "metric_hints": ["revenue"],
                        "primary_dimension": "customer",
                    },
                    "metadata": {"confidence": 0.91, "fresh": True},
                    "time_support": {"as_of": True, "range": True, "any": True},
                }
            ]
        }
        spec = {
            "domain": "sales",
            "subject": "top customers by revenue",
            "metric": "revenue",
            "task_type": "ranking",
            "filters": {"company": "MMOB"},
            "group_by": ["customer"],
            "dimensions": ["customer"],
            "time_scope": {"mode": "relative", "value": "last_month"},
            "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "revenue"]},
        }
        constraint_set = {
            "schema_version": "constraint_set_v1",
            "domain": "sales",
            "metric": "revenue",
            "task_type": "ranking",
            "output_mode": "top_n",
            "time_mode": "relative",
            "filters": {"company": "MMOB"},
            "hard_filter_kinds": ["company"],
            "requested_dimensions": ["customer"],
            "subject_tokens": ["top", "customers", "revenue"],
            "followup_bindings": {"active_topic_key": "t1", "active_result_id": "r1"},
            "active_filter_context": {"company": "MMOB"},
        }

        out = mod.resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
        )
        self.assertTrue(bool(out.get("needs_clarification")))
        self.assertEqual(str(out.get("clarification_reason") or ""), "missing_required_filter_value")
        q = str(out.get("clarification_question") or "").lower()
        self.assertIn("cost center", q)
        hc = out.get("hard_constraints") if isinstance(out.get("hard_constraints"), dict) else {}
        fb = hc.get("followup_bindings") if isinstance(hc.get("followup_bindings"), dict) else {}
        self.assertEqual(str(fb.get("active_result_id") or ""), "r1")

    def test_subject_lexical_signal_is_tie_break_only(self):
        mod = _load_module()
        capability_index = {
            "reports": [
                {
                    "report_name": "Customer Revenue Summary",
                    "constraints": {
                        "supported_filter_kinds": ["company", "date"],
                        "required_filter_kinds": [],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["sales"],
                        "dimension_hints": ["customer"],
                        "metric_hints": ["revenue"],
                        "primary_dimension": "customer",
                    },
                    "metadata": {"confidence": 0.85, "fresh": True},
                    "time_support": {"as_of": True, "range": True, "any": True},
                }
            ]
        }
        spec = {
            "domain": "sales",
            "subject": "completely unrelated words",
            "metric": "revenue",
            "task_type": "kpi",
            "filters": {"company": "MMOB"},
            "group_by": ["customer"],
            "dimensions": ["customer"],
            "time_scope": {"mode": "relative", "value": "last_month"},
            "output_contract": {"mode": "kpi", "minimal_columns": ["revenue"]},
        }
        constraint_set = {
            "schema_version": "constraint_set_v1",
            "domain": "sales",
            "metric": "revenue",
            "task_type": "kpi",
            "output_mode": "kpi",
            "time_mode": "relative",
            "filters": {"company": "MMOB"},
            "hard_filter_kinds": ["company"],
            "requested_dimensions": ["customer"],
            "subject_tokens": ["unrelated", "words"],
            "followup_bindings": {},
            "active_filter_context": {"company": "MMOB"},
        }
        out = mod.resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
            semantic_context={"catalog_available": False},
        )
        cands = [c for c in list(out.get("candidate_reports") or []) if isinstance(c, dict)]
        self.assertTrue(bool(cands))
        # No lexical hard blocker should be emitted.
        self.assertNotIn("subject_mismatch", list(cands[0].get("hard_blockers") or []))
        # Tie-break score should be non-negative and not dominate hard constraints.
        self.assertGreaterEqual(int(cands[0].get("tie_break_score") or 0), 0)

    def test_metric_domain_mismatch_blocks_incompatible_candidate(self):
        mod = _load_module()
        capability_index = {
            "reports": [
                {
                    "report_name": "Supplier-Wise Sales Analytics",
                    "constraints": {
                        "supported_filter_kinds": ["company", "date"],
                        "required_filter_kinds": [],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["sales"],
                        "dimension_hints": ["supplier"],
                        "metric_hints": ["revenue"],
                        "primary_dimension": "supplier",
                    },
                    "metadata": {"confidence": 0.92, "fresh": True},
                    "time_support": {"as_of": True, "range": True, "any": True},
                },
                {
                    "report_name": "Item-wise Purchase Register",
                    "constraints": {
                        "supported_filter_kinds": ["company", "date", "item"],
                        "required_filter_kinds": [],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["purchasing"],
                        "dimension_hints": ["item"],
                        "metric_hints": [],
                        "primary_dimension": "item",
                    },
                    "metadata": {"confidence": 0.75, "fresh": True},
                    "time_support": {"as_of": True, "range": True, "any": True},
                },
            ]
        }
        spec = {
            "domain": "purchasing",
            "subject": "top products by received quantity",
            "metric": "received quantity",
            "task_type": "ranking",
            "filters": {"company": "MMOB"},
            "group_by": ["item"],
            "dimensions": ["item"],
            "time_scope": {"mode": "relative", "value": "last_month"},
            "output_contract": {"mode": "top_n", "minimal_columns": ["item", "received quantity"]},
        }
        constraint_set = {
            "schema_version": "constraint_set_v1",
            "domain": "purchasing",
            "metric": "received_quantity",
            "task_type": "ranking",
            "output_mode": "top_n",
            "time_mode": "relative",
            "filters": {"company": "MMOB"},
            "hard_filter_kinds": ["company"],
            "requested_dimensions": ["item"],
            "subject_tokens": ["top", "products", "received", "quantity"],
            "followup_bindings": {},
            "active_filter_context": {"company": "MMOB"},
        }
        out = mod.resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
        )
        cands = [c for c in list(out.get("candidate_reports") or []) if isinstance(c, dict)]
        self.assertTrue(bool(cands))
        by_name = {str(c.get("report_name") or ""): c for c in cands}
        sales_cand = by_name.get("Supplier-Wise Sales Analytics") or {}
        self.assertIn("metric_domain_mismatch", list(sales_cand.get("hard_blockers") or []))
        self.assertEqual(str(out.get("selected_report") or ""), "Item-wise Purchase Register")

    def test_dimension_unknown_is_blocker_for_detail_when_dimension_is_requested(self):
        mod = _load_module()
        capability_index = {
            "reports": [
                {
                    "report_name": "Warehouse Wise Stock Balance",
                    "constraints": {
                        "supported_filter_kinds": ["warehouse", "company"],
                        "required_filter_kinds": [],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["inventory"],
                        "dimension_hints": [],
                        "metric_hints": ["stock_balance"],
                        "primary_dimension": "warehouse",
                    },
                    "metadata": {"confidence": 0.95, "fresh": True},
                    "time_support": {"as_of": True, "range": False, "any": True},
                }
            ]
        }
        spec = {
            "domain": "inventory",
            "subject": "stock per item",
            "metric": "stock balance",
            "task_type": "detail",
            "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
            "group_by": ["item"],
            "dimensions": ["item"],
            "time_scope": {"mode": "as_of", "value": "today"},
            "output_contract": {"mode": "detail", "minimal_columns": ["item", "stock balance"]},
        }
        constraint_set = {
            "schema_version": "constraint_set_v1",
            "domain": "inventory",
            "metric": "stock_balance",
            "task_type": "detail",
            "output_mode": "detail",
            "time_mode": "as_of",
            "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
            "hard_filter_kinds": ["warehouse"],
            "requested_dimensions": ["item"],
            "subject_tokens": ["stock", "item"],
            "followup_bindings": {},
            "active_filter_context": {"warehouse": "Yangon Main Warehouse - MMOB"},
        }
        out = mod.resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
        )
        cands = [c for c in list(out.get("candidate_reports") or []) if isinstance(c, dict)]
        self.assertTrue(bool(cands))
        self.assertIn("unsupported_dimension", list(cands[0].get("hard_blockers") or []))

    def test_metric_mismatch_is_blocker_for_detail_requests(self):
        mod = _load_module()
        capability_index = {
            "reports": [
                {
                    "report_name": "Stock Projected Qty",
                    "constraints": {
                        "supported_filter_kinds": ["warehouse", "item", "company"],
                        "required_filter_kinds": [],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["inventory"],
                        "dimension_hints": ["item", "warehouse"],
                        "metric_hints": ["projected_quantity"],
                        "primary_dimension": "item",
                    },
                    "metadata": {"confidence": 0.99, "fresh": True},
                    "time_support": {"as_of": True, "range": False, "any": True},
                }
            ]
        }
        spec = {
            "domain": "inventory",
            "subject": "stock balance per item",
            "metric": "stock balance",
            "task_type": "detail",
            "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
            "group_by": ["item"],
            "dimensions": ["item"],
            "time_scope": {"mode": "as_of", "value": "today"},
            "output_contract": {"mode": "detail", "minimal_columns": ["item", "stock balance"]},
        }
        constraint_set = {
            "schema_version": "constraint_set_v1",
            "domain": "inventory",
            "metric": "stock_balance",
            "task_type": "detail",
            "output_mode": "detail",
            "time_mode": "as_of",
            "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
            "hard_filter_kinds": ["warehouse"],
            "requested_dimensions": ["item"],
            "subject_tokens": ["stock", "balance", "item"],
            "followup_bindings": {},
            "active_filter_context": {"warehouse": "Yangon Main Warehouse - MMOB"},
        }
        out = mod.resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
        )
        cands = [c for c in list(out.get("candidate_reports") or []) if isinstance(c, dict)]
        self.assertTrue(bool(cands))
        self.assertIn("unsupported_metric", list(cands[0].get("hard_blockers") or []))

    def test_metric_strictness_prefers_stock_balance_over_projected_quantity(self):
        mod = _load_module()
        capability_index = {
            "reports": [
                {
                    "report_name": "Stock Projected Qty",
                    "constraints": {
                        "supported_filter_kinds": ["warehouse", "item", "company"],
                        "required_filter_kinds": [],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["inventory"],
                        "dimension_hints": ["item", "warehouse"],
                        "metric_hints": ["projected_quantity"],
                        "primary_dimension": "item",
                    },
                    "metadata": {"confidence": 0.99, "fresh": True},
                    "time_support": {"as_of": True, "range": False, "any": True},
                },
                {
                    "report_name": "Stock Balance",
                    "constraints": {
                        "supported_filter_kinds": ["warehouse", "item", "company", "date", "from_date", "to_date"],
                        "required_filter_kinds": [],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["inventory"],
                        "dimension_hints": ["item", "warehouse"],
                        "metric_hints": ["stock_balance"],
                        "primary_dimension": "item",
                    },
                    "metadata": {"confidence": 0.90, "fresh": True},
                    "time_support": {"as_of": True, "range": True, "any": True},
                },
            ]
        }
        spec = {
            "domain": "inventory",
            "subject": "stock balance per item",
            "metric": "stock balance",
            "task_type": "detail",
            "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
            "group_by": ["item"],
            "dimensions": ["item"],
            "time_scope": {"mode": "as_of", "value": "today"},
            "output_contract": {"mode": "detail", "minimal_columns": ["item", "stock balance"]},
        }
        constraint_set = {
            "schema_version": "constraint_set_v1",
            "domain": "inventory",
            "metric": "stock_balance",
            "task_type": "detail",
            "output_mode": "detail",
            "time_mode": "as_of",
            "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
            "hard_filter_kinds": ["warehouse"],
            "requested_dimensions": ["item"],
            "subject_tokens": ["stock", "balance", "item"],
            "followup_bindings": {},
            "active_filter_context": {"warehouse": "Yangon Main Warehouse - MMOB"},
        }
        out = mod.resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
        )
        self.assertEqual(str(out.get("selected_report") or ""), "Stock Balance")

    def test_autofill_required_time_and_company_does_not_demote_stock_balance(self):
        mod = _load_module()
        capability_index = {
            "reports": [
                {
                    "report_name": "Stock Balance",
                    "constraints": {
                        "supported_filter_kinds": ["warehouse", "item", "company", "date", "from_date", "to_date"],
                        "required_filter_kinds": ["company", "date", "from_date", "to_date"],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["inventory"],
                        "dimension_hints": ["item", "warehouse"],
                        "metric_hints": ["stock_balance"],
                        "primary_dimension": "item",
                    },
                    "metadata": {"confidence": 0.82, "fresh": True},
                    "time_support": {"as_of": True, "range": True, "any": True},
                },
                {
                    "report_name": "Incorrect Balance Qty After Transaction",
                    "constraints": {
                        "supported_filter_kinds": ["warehouse", "item", "company"],
                        "required_filter_kinds": ["company", "item"],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["inventory"],
                        "dimension_hints": ["item", "warehouse"],
                        "metric_hints": ["stock_balance"],
                        "primary_dimension": "item",
                    },
                    "metadata": {"confidence": 0.82, "fresh": True},
                    "time_support": {"as_of": True, "range": False, "any": True},
                },
            ]
        }
        spec = {
            "domain": "inventory",
            "subject": "stock balanced per item",
            "metric": "stock balanced",
            "task_type": "detail",
            "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
            "group_by": ["item"],
            "dimensions": ["item"],
            "time_scope": {"mode": "none", "value": ""},
            "output_contract": {"mode": "detail", "minimal_columns": ["item", "stock balance"]},
        }
        constraint_set = {
            "schema_version": "constraint_set_v1",
            "domain": "inventory",
            "metric": "stock_balance",
            "task_type": "detail",
            "output_mode": "detail",
            "time_mode": "none",
            "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
            "hard_filter_kinds": ["warehouse"],
            "requested_dimensions": ["item"],
            "subject_tokens": ["stock", "balanced", "item"],
            "followup_bindings": {},
            "active_filter_context": {},
        }
        out = mod.resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
        )
        self.assertEqual(str(out.get("selected_report") or ""), "Stock Balance")

    def test_list_latest_records_allows_unknown_metric_without_metric_blocker(self):
        mod = _load_module()
        capability_index = {
            "reports": [
                {
                    "report_name": "Sales Invoice Trends",
                    "constraints": {
                        "supported_filter_kinds": ["company", "date", "from_date", "to_date", "customer"],
                        "required_filter_kinds": [],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["sales"],
                        "dimension_hints": ["customer"],
                        "metric_hints": ["revenue"],
                        "primary_dimension": "customer",
                    },
                    "metadata": {"confidence": 0.78, "fresh": True},
                    "time_support": {"as_of": True, "range": True, "any": True},
                }
            ]
        }
        spec = {
            "domain": "sales",
            "subject": "latest invoices",
            "metric": "latest",
            "task_type": "ranking",
            "task_class": "list_latest_records",
            "filters": {"company": "MMOB"},
            "group_by": [],
            "dimensions": [],
            "time_scope": {"mode": "relative", "value": "this_month"},
            "top_n": 7,
            "output_contract": {"mode": "top_n", "minimal_columns": []},
        }
        constraint_set = {
            "schema_version": "constraint_set_v1",
            "domain": "sales",
            "metric": "latest",
            "task_type": "ranking",
            "task_class": "list_latest_records",
            "output_mode": "top_n",
            "requested_limit": 7,
            "sort_intent": "latest_desc",
            "time_mode": "relative",
            "filters": {"company": "MMOB"},
            "hard_filter_kinds": ["company"],
            "requested_dimensions": [],
            "subject_tokens": ["latest", "invoices"],
            "followup_bindings": {},
            "active_filter_context": {"company": "MMOB"},
        }
        out = mod.resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
        )
        cands = [c for c in list(out.get("candidate_reports") or []) if isinstance(c, dict)]
        self.assertTrue(bool(cands))
        self.assertNotIn("unsupported_metric", list(cands[0].get("hard_blockers") or []))

    def test_list_latest_records_prefers_time_ready_candidate(self):
        mod = _load_module()
        capability_index = {
            "reports": [
                {
                    "report_name": "Generic Summary",
                    "constraints": {
                        "supported_filter_kinds": ["company"],
                        "required_filter_kinds": [],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["sales"],
                        "dimension_hints": ["customer"],
                        "metric_hints": ["revenue"],
                        "primary_dimension": "customer",
                    },
                    "metadata": {"confidence": 0.85, "fresh": True},
                    "time_support": {"as_of": False, "range": False, "any": False},
                },
                {
                    "report_name": "Sales Invoice Trends",
                    "constraints": {
                        "supported_filter_kinds": ["company", "date", "from_date", "to_date"],
                        "required_filter_kinds": [],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["sales"],
                        "dimension_hints": ["customer"],
                        "metric_hints": ["revenue"],
                        "primary_dimension": "customer",
                    },
                    "metadata": {"confidence": 0.78, "fresh": True},
                    "time_support": {"as_of": True, "range": True, "any": True},
                },
            ]
        }
        spec = {
            "domain": "sales",
            "subject": "latest invoices",
            "metric": "latest",
            "task_type": "ranking",
            "task_class": "list_latest_records",
            "filters": {"company": "MMOB"},
            "group_by": [],
            "dimensions": [],
            "time_scope": {"mode": "relative", "value": "this_month"},
            "top_n": 7,
            "output_contract": {"mode": "top_n", "minimal_columns": []},
        }
        constraint_set = {
            "schema_version": "constraint_set_v1",
            "domain": "sales",
            "metric": "latest",
            "task_type": "ranking",
            "task_class": "list_latest_records",
            "output_mode": "top_n",
            "requested_limit": 7,
            "sort_intent": "latest_desc",
            "time_mode": "relative",
            "filters": {"company": "MMOB"},
            "hard_filter_kinds": ["company"],
            "requested_dimensions": [],
            "subject_tokens": ["latest", "invoices"],
            "followup_bindings": {},
            "active_filter_context": {"company": "MMOB"},
        }
        out = mod.resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
        )
        self.assertEqual(str(out.get("selected_report") or ""), "Sales Invoice Trends")

    def test_unmapped_metric_term_is_soft_penalty_not_hard_blocker(self):
        mod = _load_module()
        capability_index = {
            "reports": [
                {
                    "report_name": "Item-wise Sales Register",
                    "constraints": {
                        "supported_filter_kinds": ["company", "date", "from_date", "to_date", "item"],
                        "required_filter_kinds": [],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["sales"],
                        "dimension_hints": ["item"],
                        "metric_hints": ["revenue", "sold_quantity"],
                        "primary_dimension": "item",
                    },
                    "metadata": {"confidence": 0.9, "fresh": True},
                    "time_support": {"as_of": True, "range": True, "any": True},
                }
            ]
        }
        spec = {
            "domain": "sales",
            "subject": "sales by item this month",
            "metric": "sales",
            "task_type": "detail",
            "task_class": "detail_projection",
            "filters": {"company": "MMOB"},
            "group_by": ["item"],
            "dimensions": ["item"],
            "time_scope": {"mode": "relative", "value": "this_month"},
            "output_contract": {"mode": "detail", "minimal_columns": ["item", "sales"]},
        }
        constraint_set = {
            "schema_version": "constraint_set_v1",
            "domain": "sales",
            "metric": "sales",
            "task_type": "detail",
            "task_class": "detail_projection",
            "output_mode": "detail",
            "requested_limit": 0,
            "sort_intent": "",
            "time_mode": "relative",
            "filters": {"company": "MMOB"},
            "hard_filter_kinds": ["company"],
            "requested_dimensions": ["item"],
            "subject_tokens": ["sales", "item", "month"],
            "followup_bindings": {},
            "active_filter_context": {"company": "MMOB"},
        }
        out = mod.resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
        )
        self.assertEqual(str(out.get("selected_report") or ""), "Item-wise Sales Register")
        cands = [c for c in list(out.get("candidate_reports") or []) if isinstance(c, dict)]
        self.assertTrue(bool(cands))
        self.assertNotIn("unsupported_metric", list(cands[0].get("hard_blockers") or []))

    def test_ranking_prefers_declared_primary_dimension_over_generic_hint_match(self):
        mod = _load_module()
        capability_index = {
            "reports": [
                {
                    "report_name": "Customer Ledger Summary",
                    "constraints": {
                        "supported_filter_kinds": ["company", "customer", "date", "from_date", "to_date"],
                        "required_filter_kinds": ["company", "date", "from_date", "to_date"],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["sales", "finance"],
                        "dimension_hints": ["customer", "company"],
                        "metric_hints": ["revenue"],
                        "primary_dimension": "customer",
                    },
                    "metadata": {"confidence": 0.82, "fresh": True},
                    "time_support": {"as_of": True, "range": True, "any": True},
                },
                {
                    "report_name": "Payment Terms Status for Sales Order",
                    "constraints": {
                        "supported_filter_kinds": ["company", "customer", "date", "item"],
                        "required_filter_kinds": ["company", "date"],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["sales"],
                        "dimension_hints": ["customer", "item", "company"],
                        "metric_hints": ["revenue", "sold_quantity"],
                        "primary_dimension": "",
                    },
                    "metadata": {"confidence": 0.82, "fresh": True},
                    "time_support": {"as_of": True, "range": True, "any": True},
                },
            ]
        }
        spec = {
            "domain": "sales",
            "subject": "top customers by revenue",
            "metric": "revenue",
            "task_type": "ranking",
            "filters": {"company": "MMOB"},
            "group_by": ["customer"],
            "dimensions": ["customer"],
            "time_scope": {"mode": "relative", "value": "last_month"},
            "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "revenue"]},
        }
        constraint_set = {
            "schema_version": "constraint_set_v1",
            "domain": "sales",
            "metric": "revenue",
            "task_type": "ranking",
            "output_mode": "top_n",
            "filters": {"company": "MMOB"},
            "hard_filter_kinds": ["company"],
            "requested_dimensions": ["customer"],
            "subject_tokens": ["top", "customers", "revenue"],
            "followup_bindings": {},
            "active_filter_context": {"company": "MMOB"},
            "time_mode": "relative",
        }
        out = mod.resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
        )
        self.assertEqual(str(out.get("selected_report") or ""), "Customer Ledger Summary")
        cands = [c for c in list(out.get("candidate_reports") or []) if isinstance(c, dict)]
        by_name = {str(c.get("report_name") or ""): c for c in cands}
        self.assertIn("ranking_primary_dimension_match(+12)", list(by_name["Customer Ledger Summary"].get("reasons") or []))
        self.assertIn("ranking_primary_dimension_unknown(-18)", list(by_name["Payment Terms Status for Sales Order"].get("reasons") or []))

    def test_ranking_blocks_report_declared_not_ranking_capable(self):
        mod = _load_module()
        capability_index = {
            "reports": [
                {
                    "report_name": "Warehouse Wise Stock Balance",
                    "constraints": {
                        "supported_filter_kinds": ["company", "warehouse"],
                        "required_filter_kinds": ["company"],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["inventory"],
                        "dimension_hints": ["warehouse"],
                        "metric_hints": ["stock_balance"],
                        "primary_dimension": "warehouse",
                    },
                    "presentation": {
                        "supports_ranking": True,
                        "result_grain": "summary",
                    },
                    "metadata": {"confidence": 0.8, "fresh": True},
                    "time_support": {"as_of": True, "range": False, "any": True},
                },
                {
                    "report_name": "Product Bundle Balance",
                    "constraints": {
                        "supported_filter_kinds": ["company", "warehouse", "item"],
                        "required_filter_kinds": ["company"],
                        "requirements_unknown": False,
                    },
                    "semantics": {
                        "domain_hints": ["inventory"],
                        "dimension_hints": ["item", "warehouse"],
                        "metric_hints": ["stock_balance"],
                        "primary_dimension": "item",
                    },
                    "presentation": {
                        "supports_ranking": False,
                        "result_grain": "detail",
                    },
                    "metadata": {"confidence": 0.92, "fresh": True},
                    "time_support": {"as_of": True, "range": False, "any": True},
                },
            ]
        }
        spec = {
            "domain": "inventory",
            "subject": "top warehouses by stock balance",
            "metric": "stock balance",
            "task_type": "ranking",
            "filters": {"company": "MMOB"},
            "group_by": ["warehouse"],
            "dimensions": ["warehouse"],
            "time_scope": {"mode": "as_of", "value": "today"},
            "output_contract": {"mode": "top_n", "minimal_columns": ["warehouse", "stock balance"]},
        }
        constraint_set = {
            "schema_version": "constraint_set_v1",
            "domain": "inventory",
            "metric": "stock_balance",
            "task_type": "ranking",
            "output_mode": "top_n",
            "filters": {"company": "MMOB"},
            "hard_filter_kinds": ["company"],
            "requested_dimensions": ["warehouse"],
            "subject_tokens": ["top", "warehouses", "stock", "balance"],
            "followup_bindings": {},
            "active_filter_context": {"company": "MMOB"},
            "time_mode": "as_of",
        }
        out = mod.resolve_semantics(
            business_spec=spec,
            capability_index=capability_index,
            constraint_set=constraint_set,
        )
        self.assertEqual(str(out.get("selected_report") or ""), "Warehouse Wise Stock Balance")
        cands = [c for c in list(out.get("candidate_reports") or []) if isinstance(c, dict)]
        by_name = {str(c.get("report_name") or ""): c for c in cands}
        self.assertIn("ranking_not_supported(-24)", list(by_name["Product Bundle Balance"].get("reasons") or []))
        self.assertIn("ranking_not_supported", list(by_name["Product Bundle Balance"].get("hard_blockers") or []))


if __name__ == "__main__":
    unittest.main()
