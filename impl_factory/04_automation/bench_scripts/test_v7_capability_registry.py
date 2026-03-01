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
        column_roles = presentation.get("column_roles") if isinstance(presentation.get("column_roles"), dict) else {}
        metrics = column_roles.get("metrics") if isinstance(column_roles.get("metrics"), dict) else {}
        dimensions = column_roles.get("dimensions") if isinstance(column_roles.get("dimensions"), dict) else {}
        self.assertEqual(metrics.get("outstanding_amount"), ["closing_balance"])
        self.assertEqual(dimensions.get("customer"), ["party", "customer"])

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
