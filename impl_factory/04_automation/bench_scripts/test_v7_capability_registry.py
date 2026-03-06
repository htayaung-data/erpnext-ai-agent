from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = (
    REPO_ROOT
    / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/capability_registry.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("capability_registry_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load capability_registry module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7CapabilityRegistryTests(unittest.TestCase):
    def test_supplier_ledger_override_adds_purchase_amount_metric(self):
        mod = _load_module()
        mod.clear_registry_override_cache()
        cap = {
            "report_name": "Supplier Ledger Summary",
            "metric_tags": ["outstanding_amount"],
            "semantics": {"metric_hints": ["outstanding_amount"]},
        }
        merged = mod.apply_registry_overrides(cap)
        self.assertEqual(
            merged.get("metric_tags"),
            ["outstanding_amount", "purchase_amount"],
        )
        semantics = merged.get("semantics") if isinstance(merged.get("semantics"), dict) else {}
        self.assertEqual(
            semantics.get("metric_hints"),
            ["outstanding_amount", "purchase_amount"],
        )
        self.assertEqual(str(merged.get("primary_dimension") or ""), "supplier")

    def test_report_semantics_contract_exposes_priority_report_column_roles(self):
        mod = _load_module()
        mod.clear_registry_override_cache()
        contract = mod.report_semantics_contract("Customer Ledger Summary")
        semantics = contract.get("semantics") if isinstance(contract.get("semantics"), dict) else {}
        presentation = contract.get("presentation") if isinstance(contract.get("presentation"), dict) else {}
        self.assertEqual(str(semantics.get("primary_dimension") or ""), "customer")
        self.assertEqual(semantics.get("contribution_metrics"), ["revenue"])
        self.assertEqual(semantics.get("threshold_metrics"), ["outstanding_amount"])
        self.assertEqual(semantics.get("supported_comparators"), ["gt", "gte", "lt", "lte"])
        column_roles = presentation.get("column_roles") if isinstance(presentation.get("column_roles"), dict) else {}
        metrics = column_roles.get("metrics") if isinstance(column_roles.get("metrics"), dict) else {}
        dimensions = column_roles.get("dimensions") if isinstance(column_roles.get("dimensions"), dict) else {}
        self.assertEqual(metrics.get("outstanding_amount"), ["closing_balance"])
        self.assertEqual(dimensions.get("customer"), ["party", "customer"])
        self.assertIn("contribution_share", list(presentation.get("contribution_safe_columns") or []))

    def test_invoice_latest_reports_expose_threshold_capable_contracts(self):
        mod = _load_module()
        mod.clear_registry_override_cache()
        sales = mod.report_semantics_contract("Latest Sales Invoice")
        sales_semantics = sales.get("semantics") if isinstance(sales.get("semantics"), dict) else {}
        sales_presentation = sales.get("presentation") if isinstance(sales.get("presentation"), dict) else {}
        self.assertEqual(str(sales_semantics.get("primary_dimension") or ""), "invoice")
        self.assertEqual(sales_semantics.get("threshold_metrics"), ["invoice_amount", "outstanding_amount"])
        self.assertEqual(sales_semantics.get("status_dimensions"), ["status", "due_date"])
        sales_roles = sales_presentation.get("column_roles") if isinstance(sales_presentation.get("column_roles"), dict) else {}
        sales_metrics = sales_roles.get("metrics") if isinstance(sales_roles.get("metrics"), dict) else {}
        self.assertEqual(sales_metrics.get("invoice_amount"), ["grand_total", "base_grand_total"])
        self.assertEqual(
            sales_presentation.get("exception_safe_columns"),
            ["name", "sales_invoice_number", "posting_date", "customer", "grand_total", "outstanding_amount", "status"],
        )

        purchase = mod.report_semantics_contract("Latest Purchase Invoice")
        purchase_semantics = purchase.get("semantics") if isinstance(purchase.get("semantics"), dict) else {}
        purchase_presentation = purchase.get("presentation") if isinstance(purchase.get("presentation"), dict) else {}
        self.assertEqual(str(purchase_semantics.get("primary_dimension") or ""), "invoice")
        self.assertEqual(purchase_semantics.get("threshold_metrics"), ["invoice_amount", "outstanding_amount"])
        self.assertEqual(
            purchase_presentation.get("exception_safe_columns"),
            ["name", "purchase_invoice_number", "posting_date", "supplier", "grand_total", "outstanding_amount", "status"],
        )

    def test_stock_balance_is_threshold_capable_and_other_inventory_detail_reports_are_not(self):
        mod = _load_module()
        mod.clear_registry_override_cache()

        stock_balance = mod.report_semantics_contract("Stock Balance")
        stock_semantics = stock_balance.get("semantics") if isinstance(stock_balance.get("semantics"), dict) else {}
        stock_presentation = stock_balance.get("presentation") if isinstance(stock_balance.get("presentation"), dict) else {}
        self.assertEqual(str(stock_semantics.get("primary_dimension") or ""), "item")
        self.assertEqual(stock_semantics.get("threshold_metrics"), ["stock_quantity"])
        stock_roles = stock_presentation.get("column_roles") if isinstance(stock_presentation.get("column_roles"), dict) else {}
        stock_metrics = stock_roles.get("metrics") if isinstance(stock_roles.get("metrics"), dict) else {}
        self.assertEqual(stock_metrics.get("stock_quantity"), ["bal_qty", "stock_qty", "actual_qty", "qty"])
        stock_dimensions = stock_roles.get("dimensions") if isinstance(stock_roles.get("dimensions"), dict) else {}
        self.assertEqual(stock_dimensions.get("item"), ["item", "item_code", "name", "item_name"])
        self.assertIn("item_name", list(stock_presentation.get("transform_safe_columns") or []))

        bundle = mod.report_semantics_contract("Product Bundle Balance")
        bundle_semantics = bundle.get("semantics") if isinstance(bundle.get("semantics"), dict) else {}
        self.assertEqual(bundle_semantics.get("threshold_metrics"), [])

        age_value = mod.report_semantics_contract("Warehouse wise Item Balance Age and Value")
        age_value_semantics = age_value.get("semantics") if isinstance(age_value.get("semantics"), dict) else {}
        self.assertEqual(age_value_semantics.get("threshold_metrics"), [])

    def test_contribution_metrics_are_declared_for_first_slice_reports(self):
        mod = _load_module()
        mod.clear_registry_override_cache()

        supplier = mod.report_semantics_contract("Supplier Ledger Summary")
        supplier_semantics = supplier.get("semantics") if isinstance(supplier.get("semantics"), dict) else {}
        self.assertEqual(supplier_semantics.get("contribution_metrics"), ["purchase_amount"])

        item_sales = mod.report_semantics_contract("Item-wise Sales Register")
        item_semantics = item_sales.get("semantics") if isinstance(item_sales.get("semantics"), dict) else {}
        item_presentation = item_sales.get("presentation") if isinstance(item_sales.get("presentation"), dict) else {}
        self.assertEqual(item_semantics.get("contribution_metrics"), ["revenue"])
        self.assertIn("contribution_share", list(item_presentation.get("contribution_safe_columns") or []))

    def test_unlisted_report_passes_through_unchanged(self):
        mod = _load_module()
        mod.clear_registry_override_cache()
        cap = {
            "report_name": "Unlisted Demo Report",
            "metric_tags": ["stock_balance"],
            "semantics": {"metric_hints": ["stock_balance"]},
        }
        merged = mod.apply_registry_overrides(cap)
        self.assertEqual(merged, cap)


if __name__ == "__main__":
    unittest.main()
