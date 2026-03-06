from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = (
    REPO_ROOT
    / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/ontology_normalization.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("ontology_normalization_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load ontology_normalization module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7OntologyNormalizationTests(unittest.TestCase):
    def test_generated_ontology_path_is_loaded(self):
        mod = _load_module()
        generated_payload = {
            "schema_version": "ontology_generated_v1",
            "version": "generated_v1",
            "metric_aliases": {"gmv": ["gmv", "gross merchandise value"]},
            "metric_domain_map": {"gmv": "sales"},
            "domain_aliases": {"sales": ["sales"]},
            "dimension_aliases": {"customer": ["customer"]},
            "primary_dimension_aliases": {"customer": ["customer-wise", "customer"]},
            "filter_kind_aliases": {"company": ["company"]},
            "write_operation_aliases": {},
            "write_doctype_aliases": {},
            "export_aliases": {},
            "generic_metric_terms": [],
        }

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "generated.json"
            path.write_text(json.dumps(generated_payload, ensure_ascii=False), encoding="utf-8")
            old = os.environ.get("AI_ASSISTANT_V7_ONTOLOGY_GENERATED")
            try:
                os.environ["AI_ASSISTANT_V7_ONTOLOGY_GENERATED"] = str(path)
                mod.clear_ontology_cache()
                self.assertEqual(mod.canonical_metric("gross merchandise value"), "gmv")
                self.assertEqual(mod.metric_domain("gmv"), "sales")
            finally:
                if old is None:
                    os.environ.pop("AI_ASSISTANT_V7_ONTOLOGY_GENERATED", None)
                else:
                    os.environ["AI_ASSISTANT_V7_ONTOLOGY_GENERATED"] = old
                mod.clear_ontology_cache()

    def test_infer_metric_hints_distinguishes_projected_qty_from_stock_balance(self):
        mod = _load_module()
        mod.clear_ontology_cache()

        projected = mod.infer_metric_hints(
            report_name="Stock Projected Qty",
            report_family="Stock",
            supported_filter_names=["warehouse", "item", "company"],
            supported_filter_kinds=["warehouse", "item", "company"],
        )
        self.assertIn("projected_quantity", projected)
        self.assertNotIn("stock_balance", projected)

        balance = mod.infer_metric_hints(
            report_name="Stock Balance",
            report_family="Stock",
            supported_filter_names=["warehouse", "item", "company", "from_date", "to_date"],
            supported_filter_kinds=["warehouse", "item", "company", "from_date", "to_date"],
        )
        self.assertIn("stock_balance", balance)

    def test_infer_transform_ambiguities_detects_million_scale(self):
        mod = _load_module()
        mod.clear_ontology_cache()
        amb = list(mod.infer_transform_ambiguities("Show total amount as million"))
        self.assertIn("transform_scale:million", amb)

    def test_infer_transform_ambiguities_does_not_false_match_million_inside_column(self):
        mod = _load_module()
        mod.clear_ontology_cache()
        amb = list(mod.infer_transform_ambiguities("Give me Customer Column only"))
        self.assertEqual(amb, ["transform_projection:only"])

    def test_infer_reference_value_detects_same_reference(self):
        mod = _load_module()
        mod.clear_ontology_cache()
        self.assertEqual(mod.infer_reference_value("same warehouse"), "same")
        self.assertEqual(mod.infer_reference_value("Yangon Main Warehouse - MMOB"), "")

    def test_metric_normalization_distinguishes_outstanding_and_purchase_amount(self):
        mod = _load_module()
        mod.clear_ontology_cache()
        self.assertEqual(mod.canonical_metric("outstanding amount"), "outstanding_amount")
        self.assertEqual(mod.known_metric("outstanding amount"), "outstanding_amount")
        self.assertEqual(mod.canonical_metric("purchase amount"), "purchase_amount")
        self.assertEqual(mod.known_metric("purchase amount"), "purchase_amount")
        self.assertEqual(mod.metric_domain("purchase amount"), "purchasing")

    def test_open_requests_is_treated_as_detail_constraint_metric(self):
        mod = _load_module()
        mod.clear_ontology_cache()
        self.assertTrue(mod.is_detail_constraint_metric("open requests"))
        self.assertFalse(mod.is_detail_constraint_metric("revenue"))

    def test_threshold_exception_ontology_keys_and_metrics_are_present(self):
        mod = _load_module()
        mod.clear_ontology_cache()
        catalog = mod.get_ontology_catalog()
        comparator_aliases = catalog.get("comparator_aliases") if isinstance(catalog.get("comparator_aliases"), dict) else {}
        exception_aliases = catalog.get("exception_term_aliases") if isinstance(catalog.get("exception_term_aliases"), dict) else {}
        contribution_aliases = catalog.get("contribution_term_aliases") if isinstance(catalog.get("contribution_term_aliases"), dict) else {}
        self.assertIn("gt", comparator_aliases)
        self.assertIn("lt", comparator_aliases)
        self.assertIn("overdue", exception_aliases)
        self.assertIn("share_of_total", contribution_aliases)
        self.assertEqual(mod.canonical_metric("grand total"), "invoice_amount")
        self.assertEqual(mod.metric_domain("invoice amount"), "finance")
        self.assertEqual(mod.canonical_metric("qty on hand"), "stock_quantity")
        self.assertEqual(mod.metric_domain("stock quantity"), "inventory")
        self.assertEqual(mod.known_comparator("above 5,000,000"), "gt")
        self.assertEqual(mod.known_comparator("at most 20"), "lte")
        self.assertEqual(mod.infer_exception_terms("show overdue invoices above 5,000,000"), ["overdue"])
        self.assertEqual(mod.infer_contribution_terms("show customers share of total revenue"), ["share_of_total"])
        self.assertIn("contribution_share", mod.infer_contribution_terms("show supplier contribution share of total purchase amount"))
        self.assertEqual(mod.infer_exception_terms("show low stock items"), ["low_stock"])
        self.assertIn("causal_analysis", mod.infer_advisory_intents("Why are these overdue invoices risky?"))
        self.assertIn("risk_assessment", mod.infer_advisory_intents("Why are these overdue invoices risky?"))

    def test_sales_invoice_number_does_not_collapse_to_revenue_metric(self):
        mod = _load_module()
        mod.clear_ontology_cache()
        self.assertNotEqual(mod.canonical_metric("sales invoice number"), "revenue")
        self.assertEqual(mod.known_dimension("sales invoice number"), "invoice")


if __name__ == "__main__":
    unittest.main()
