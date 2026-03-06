from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/quality_gate.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_quality_gate_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load quality gate module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7QualityGateConstraintTests(unittest.TestCase):
    def test_constraint_and_semantic_context_checks_are_enforced(self):
        mod = _load_module()
        spec = {
            "task_type": "kpi",
            "filters": {},
            "output_contract": {"mode": "kpi", "minimal_columns": []},
        }
        resolved = {
            "needs_clarification": False,
            "selected_report": "Customer Revenue",
            "hard_constraints": {"schema_version": "constraint_set_v1"},
            "semantic_context": {"catalog_available": False, "query_tokens": [], "preferred_domains": [], "preferred_dimensions": [], "preferred_filter_kinds": []},
        }
        payload = {
            "type": "report_table",
            "report_name": "Customer Revenue",
            "table": {
                "columns": [{"fieldname": "metric", "label": "Metric"}, {"fieldname": "value", "label": "Value"}],
                "rows": [{"metric": "revenue", "value": 1000}],
            },
        }
        out = mod.evaluate_quality_gate(
            business_spec=spec,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        checks = [c for c in list(out.get("checks") or []) if isinstance(c, dict)]
        names = {str(c.get("check") or ""): bool(c.get("ok")) for c in checks}
        self.assertIn("constraint_set_applied", names)
        self.assertIn("semantic_context_recorded", names)
        self.assertIn("catalog_usage_or_fallback_recorded", names)
        self.assertTrue(bool(names.get("constraint_set_applied")))
        self.assertTrue(bool(names.get("semantic_context_recorded")))
        self.assertTrue(bool(names.get("catalog_usage_or_fallback_recorded")))

    def test_missing_requested_dimension_column_fails_minimal_columns(self):
        mod = _load_module()
        spec = {
            "task_type": "detail",
            "subject": "stock balance per item",
            "metric": "stock balance",
            "dimensions": ["item"],
            "group_by": ["item"],
            "filters": {"warehouse": "Yangon Main Warehouse - MMOB"},
            "output_contract": {"mode": "detail", "minimal_columns": ["item", "stock balance"]},
        }
        resolved = {
            "needs_clarification": False,
            "selected_report": "Stock Projected Qty",
            "hard_constraints": {"schema_version": "constraint_set_v1"},
            "semantic_context": {
                "catalog_available": False,
                "query_tokens": [],
                "preferred_domains": [],
                "preferred_dimensions": [],
                "preferred_filter_kinds": [],
            },
        }
        payload = {
            "type": "report_table",
            "report_name": "Stock Projected Qty",
            "table": {
                "columns": [{"fieldname": "warehouse", "label": "Warehouse"}, {"fieldname": "projected_qty", "label": "Projected Qty"}],
                "rows": [{"warehouse": "Yangon Main Warehouse - MMOB", "projected_qty": 10}],
            },
        }
        out = mod.evaluate_quality_gate(
            business_spec=spec,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        checks = [c for c in list(out.get("checks") or []) if isinstance(c, dict)]
        by_name = {str(c.get("check") or ""): c for c in checks}
        mc = by_name.get("minimal_columns_present") or {}
        rd = by_name.get("requested_dimensions_present") or {}
        rm = by_name.get("requested_metric_present") or {}
        self.assertFalse(bool(mc.get("ok")))
        self.assertFalse(bool(rd.get("ok")))
        self.assertFalse(bool(rm.get("ok")))
        self.assertIn("shape", list(out.get("repairable_failure_classes") or []))
        self.assertIn("semantic", list(out.get("repairable_failure_classes") or []))
        self.assertEqual(str(out.get("verdict") or ""), "REPAIRABLE_FAIL")

    def test_empty_table_is_valid_no_data_without_metric_column_failure(self):
        mod = _load_module()
        spec = {
            "task_type": "detail",
            "subject": "material requests",
            "metric": "open requests",
            "dimensions": ["item"],
            "group_by": ["item"],
            "filters": {"status": "open", "context": "production"},
            "output_contract": {"mode": "detail", "minimal_columns": ["item"]},
        }
        resolved = {
            "needs_clarification": False,
            "selected_report": "Work Order Summary",
            "hard_constraints": {"schema_version": "constraint_set_v1"},
            "semantic_context": {
                "catalog_available": False,
                "query_tokens": [],
                "preferred_domains": [],
                "preferred_dimensions": [],
                "preferred_filter_kinds": [],
            },
        }
        payload = {
            "type": "report_table",
            "report_name": "Work Order Summary",
            "table": {
                "columns": [
                    {"fieldname": "name", "label": "Id"},
                    {"fieldname": "production_item", "label": "Production Item"},
                ],
                "rows": [],
            },
        }
        out = mod.evaluate_quality_gate(
            business_spec=spec,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        checks = [c for c in list(out.get("checks") or []) if isinstance(c, dict)]
        by_name = {str(c.get("check") or ""): c for c in checks}
        self.assertTrue(bool((by_name.get("non_empty_rows") or {}).get("ok")))
        self.assertTrue(bool((by_name.get("requested_metric_present") or {}).get("ok")))
        self.assertEqual(str(out.get("verdict") or ""), "PASS")

    def test_threshold_warehouse_dimension_can_use_name_field(self):
        mod = _load_module()
        spec = {
            "task_type": "detail",
            "task_class": "threshold_exception_list",
            "subject": "warehouses",
            "metric": "stock balance",
            "dimensions": ["warehouse"],
            "group_by": ["warehouse"],
            "filters": {
                "_threshold_rule": {
                    "metric": "stock_balance",
                    "comparator": "lt",
                    "value": 50_000_000.0,
                    "value_present": True,
                }
            },
            "output_contract": {"mode": "detail", "minimal_columns": []},
        }
        resolved = {
            "needs_clarification": False,
            "selected_report": "Warehouse Wise Stock Balance",
            "hard_constraints": {"schema_version": "constraint_set_v1"},
            "semantic_context": {
                "catalog_available": False,
                "query_tokens": [],
                "preferred_domains": [],
                "preferred_dimensions": [],
                "preferred_filter_kinds": [],
            },
        }
        payload = {
            "type": "report_table",
            "report_name": "Warehouse Wise Stock Balance",
            "_threshold_rule_applied": True,
            "_threshold_metric_fieldname": "stock_balance",
            "table": {
                "columns": [
                    {"fieldname": "name", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"name": "Stores - MMOB", "stock_balance": 0.0},
                    {"name": "Finished Goods - MMOB", "stock_balance": 0.0},
                ],
            },
        }
        out = mod.evaluate_quality_gate(
            business_spec=spec,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        self.assertEqual(str(out.get("verdict") or ""), "PASS")

    def test_contribution_share_requires_contribution_column_and_consistent_values(self):
        mod = _load_module()
        spec = {
            "task_type": "ranking",
            "task_class": "contribution_share",
            "subject": "customers",
            "metric": "revenue",
            "dimensions": ["customer"],
            "group_by": ["customer"],
            "filters": {
                "_contribution_rule": {
                    "metric": "revenue",
                    "basis": "of_total",
                    "contribution_terms": ["share_of_total"],
                }
            },
            "top_n": 10,
            "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "revenue", "contribution share"]},
        }
        resolved = {
            "needs_clarification": False,
            "selected_report": "Customer Ledger Summary",
            "hard_constraints": {"schema_version": "constraint_set_v1"},
            "semantic_context": {
                "catalog_available": False,
                "query_tokens": [],
                "preferred_domains": [],
                "preferred_dimensions": [],
                "preferred_filter_kinds": [],
            },
        }
        payload = {
            "type": "report_table",
            "report_name": "Customer Ledger Summary",
            "_contribution_rule_applied": True,
            "_contribution_metric_fieldname": "invoiced_amount",
            "_contribution_share_fieldname": "contribution_share",
            "_contribution_total_value": 100.0,
            "table": {
                "columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "invoiced_amount", "label": "Revenue", "fieldtype": "Currency"},
                    {"fieldname": "contribution_share", "label": "Contribution Share", "fieldtype": "Data"},
                ],
                "rows": [
                    {"party": "A", "invoiced_amount": 60.0, "contribution_share": "60%"},
                    {"party": "B", "invoiced_amount": 40.0, "contribution_share": "40%"},
                ],
            },
        }
        out = mod.evaluate_quality_gate(
            business_spec=spec,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        self.assertEqual(str(out.get("verdict") or ""), "PASS")

    def test_latest_records_requires_time_and_identifier_axes(self):
        mod = _load_module()
        spec = {
            "task_type": "detail",
            "task_class": "list_latest_records",
            "subject": "invoice",
            "metric": "",
            "dimensions": [],
            "group_by": [],
            "filters": {},
            "top_n": 7,
            "output_contract": {"mode": "top_n", "minimal_columns": []},
        }
        resolved = {
            "needs_clarification": False,
            "selected_report": "Payment Period Based On Invoice Date",
            "hard_constraints": {"schema_version": "constraint_set_v1"},
            "semantic_context": {
                "catalog_available": False,
                "query_tokens": [],
                "preferred_domains": [],
                "preferred_dimensions": [],
                "preferred_filter_kinds": [],
            },
        }
        payload = {
            "type": "report_table",
            "report_name": "Payment Period Based On Invoice Date",
            "table": {"columns": [], "rows": []},
        }
        out = mod.evaluate_quality_gate(
            business_spec=spec,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        checks = [c for c in list(out.get("checks") or []) if isinstance(c, dict)]
        by_name = {str(c.get("check") or ""): c for c in checks}
        self.assertFalse(bool((by_name.get("latest_records_time_axis") or {}).get("ok")))
        self.assertFalse(bool((by_name.get("latest_records_identifier_axis") or {}).get("ok")))
        self.assertEqual(str(out.get("verdict") or ""), "REPAIRABLE_FAIL")

    def test_single_missing_minimal_column_does_not_auto_pass_fallback(self):
        mod = _load_module()
        spec = {
            "task_type": "detail",
            "subject": "invoice numbers",
            "metric": "",
            "dimensions": [],
            "group_by": [],
            "filters": {},
            "output_contract": {"mode": "detail", "minimal_columns": ["invoice_number"]},
        }
        resolved = {
            "needs_clarification": False,
            "selected_report": "Tax Withholding Details",
            "hard_constraints": {"schema_version": "constraint_set_v1"},
            "semantic_context": {
                "catalog_available": False,
                "query_tokens": [],
                "preferred_domains": [],
                "preferred_dimensions": [],
                "preferred_filter_kinds": [],
            },
        }
        payload = {
            "type": "report_table",
            "report_name": "Tax Withholding Details",
            "table": {
                "columns": [
                    {"fieldname": "supplier_invoice_no", "label": "Supplier Invoice No"},
                    {"fieldname": "supplier_invoice_date", "label": "Supplier Invoice Date"},
                    {"fieldname": "total_amount", "label": "Total Amount", "fieldtype": "Currency"},
                ],
                "rows": [],
            },
        }
        out = mod.evaluate_quality_gate(
            business_spec=spec,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        checks = [c for c in list(out.get("checks") or []) if isinstance(c, dict)]
        by_name = {str(c.get("check") or ""): c for c in checks}
        self.assertFalse(bool((by_name.get("minimal_columns_present") or {}).get("ok")))
        self.assertEqual(str(out.get("verdict") or ""), "REPAIRABLE_FAIL")

    def test_latest_records_subject_alignment_handles_plural_tokens(self):
        mod = _load_module()
        spec = {
            "task_type": "detail",
            "task_class": "list_latest_records",
            "subject": "invoices",
            "metric": "",
            "dimensions": [],
            "group_by": [],
            "filters": {},
            "top_n": 7,
            "output_contract": {"mode": "top_n", "minimal_columns": ["invoice_number", "posting_date"]},
        }
        resolved = {
            "needs_clarification": False,
            "selected_report": "Sales Invoice",
            "hard_constraints": {"schema_version": "constraint_set_v1"},
            "semantic_context": {
                "catalog_available": False,
                "query_tokens": [],
                "preferred_domains": [],
                "preferred_dimensions": [],
                "preferred_filter_kinds": [],
            },
        }
        payload = {
            "type": "report_table",
            "report_name": "Sales Invoice",
            "table": {
                "columns": [
                    {"fieldname": "invoice_number", "label": "Invoice Number"},
                    {"fieldname": "posting_date", "label": "Posting Date"},
                ],
                "rows": [{"invoice_number": "ACC-SINV-2026-00013", "posting_date": "2026-02-17"}],
            },
        }
        out = mod.evaluate_quality_gate(
            business_spec=spec,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        checks = [c for c in list(out.get("checks") or []) if isinstance(c, dict)]
        by_name = {str(c.get("check") or ""): c for c in checks}
        self.assertTrue(bool((by_name.get("latest_records_subject_alignment") or {}).get("ok")))

    def test_threshold_exception_quality_checks_pass_for_valid_customer_outstanding_result(self):
        mod = _load_module()
        spec = {
            "task_type": "detail",
            "task_class": "threshold_exception_list",
            "subject": "customers",
            "metric": "outstanding amount",
            "dimensions": ["customer"],
            "group_by": ["customer"],
            "filters": {
                "_threshold_rule": {
                    "metric": "outstanding_amount",
                    "comparator": "gt",
                    "value": 10_000_000.0,
                    "value_present": True,
                }
            },
            "output_contract": {"mode": "detail", "minimal_columns": ["customer", "outstanding amount"]},
        }
        resolved = {
            "needs_clarification": False,
            "selected_report": "Customer Ledger Summary",
            "hard_constraints": {"schema_version": "constraint_set_v1"},
            "semantic_context": {
                "catalog_available": False,
                "query_tokens": [],
                "preferred_domains": [],
                "preferred_dimensions": [],
                "preferred_filter_kinds": [],
            },
        }
        payload = {
            "type": "report_table",
            "report_name": "Customer Ledger Summary",
            "_threshold_rule_applied": True,
            "_threshold_metric_fieldname": "closing_balance",
            "_threshold_comparator": "gt",
            "table": {
                "columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "closing_balance", "label": "Outstanding Amount", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"party": "Shwe Li Road Mobile Wholesale", "closing_balance": 16218000.0},
                    {"party": "Latha Mobile Wholesale", "closing_balance": 15830000.0},
                ],
            },
        }
        out = mod.evaluate_quality_gate(
            business_spec=spec,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        checks = [c for c in list(out.get("checks") or []) if isinstance(c, dict)]
        by_name = {str(c.get("check") or ""): c for c in checks}
        self.assertTrue(bool((by_name.get("threshold_rule_applied") or {}).get("ok")))
        self.assertTrue(bool((by_name.get("threshold_primary_dimension_alignment") or {}).get("ok")))
        self.assertTrue(bool((by_name.get("threshold_comparator_respected") or {}).get("ok")))
        self.assertTrue(bool((by_name.get("threshold_aggregate_rows_excluded") or {}).get("ok")))
        self.assertEqual(str(out.get("verdict") or ""), "PASS")

    def test_threshold_exception_quality_fails_when_comparator_not_respected(self):
        mod = _load_module()
        spec = {
            "task_type": "detail",
            "task_class": "threshold_exception_list",
            "subject": "customers",
            "metric": "outstanding amount",
            "dimensions": ["customer"],
            "group_by": ["customer"],
            "filters": {
                "_threshold_rule": {
                    "metric": "outstanding_amount",
                    "comparator": "gt",
                    "value": 10_000_000.0,
                    "value_present": True,
                }
            },
            "output_contract": {"mode": "detail", "minimal_columns": ["customer", "outstanding amount"]},
        }
        resolved = {
            "needs_clarification": False,
            "selected_report": "Customer Ledger Summary",
            "hard_constraints": {"schema_version": "constraint_set_v1"},
            "semantic_context": {
                "catalog_available": False,
                "query_tokens": [],
                "preferred_domains": [],
                "preferred_dimensions": [],
                "preferred_filter_kinds": [],
            },
        }
        payload = {
            "type": "report_table",
            "report_name": "Customer Ledger Summary",
            "_threshold_rule_applied": True,
            "_threshold_metric_fieldname": "closing_balance",
            "_threshold_comparator": "gt",
            "table": {
                "columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "closing_balance", "label": "Outstanding Amount", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"party": "City Mobile Mart", "closing_balance": 1800000.0},
                ],
            },
        }
        out = mod.evaluate_quality_gate(
            business_spec=spec,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        checks = [c for c in list(out.get("checks") or []) if isinstance(c, dict)]
        by_name = {str(c.get("check") or ""): c for c in checks}
        self.assertFalse(bool((by_name.get("threshold_comparator_respected") or {}).get("ok")))
        self.assertEqual(str(out.get("verdict") or ""), "REPAIRABLE_FAIL")

    def test_threshold_exception_quality_fails_when_aggregate_row_leaks(self):
        mod = _load_module()
        spec = {
            "task_type": "detail",
            "task_class": "threshold_exception_list",
            "subject": "warehouses",
            "metric": "stock balance",
            "dimensions": ["warehouse"],
            "group_by": ["warehouse"],
            "filters": {
                "_threshold_rule": {
                    "metric": "stock_balance",
                    "comparator": "lt",
                    "value": 50_000_000.0,
                    "value_present": True,
                }
            },
            "output_contract": {"mode": "detail", "minimal_columns": ["warehouse", "stock balance"]},
        }
        resolved = {
            "needs_clarification": False,
            "selected_report": "Warehouse Wise Stock Balance",
            "hard_constraints": {"schema_version": "constraint_set_v1"},
            "semantic_context": {
                "catalog_available": False,
                "query_tokens": [],
                "preferred_domains": [],
                "preferred_dimensions": [],
                "preferred_filter_kinds": [],
            },
        }
        payload = {
            "type": "report_table",
            "report_name": "Warehouse Wise Stock Balance",
            "_threshold_rule_applied": True,
            "_threshold_metric_fieldname": "stock_balance",
            "_threshold_comparator": "lt",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"warehouse": "All Warehouses - MMOB", "stock_balance": 0.0},
                    {"warehouse": "Stores - MMOB", "stock_balance": 0.0},
                ],
            },
        }
        out = mod.evaluate_quality_gate(
            business_spec=spec,
            resolved=resolved,
            payload=payload,
            repeated_call_guard_triggered=False,
        )
        checks = [c for c in list(out.get("checks") or []) if isinstance(c, dict)]
        by_name = {str(c.get("check") or ""): c for c in checks}
        self.assertFalse(bool((by_name.get("threshold_aggregate_rows_excluded") or {}).get("ok")))
        self.assertEqual(str(out.get("verdict") or ""), "REPAIRABLE_FAIL")


if __name__ == "__main__":
    unittest.main()
