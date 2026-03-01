from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = REPO_ROOT / "impl_factory/05_custom_logic/custom_app/ai_assistant_ui"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

MODULE_PATH = APP_ROOT / "ai_assistant_ui/ai_core/v7/response_shaper.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("v7_response_shaper_module", str(MODULE_PATH))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load response_shaper module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class V7ResponseShaperTests(unittest.TestCase):
    def test_minimal_columns_keeps_group_by_dimension_when_contract_is_stale(self):
        mod = _load_module()
        spec = {
            "metric": "stock balance",
            "group_by": ["item"],
            "output_contract": {"mode": "detail", "minimal_columns": ["warehouse", "stock balance"]},
        }
        cols = list(mod._minimal_columns(spec))
        cols_lc = [str(x).strip().lower() for x in cols]
        self.assertIn("item", cols_lc)
        self.assertIn("warehouse", cols_lc)
        self.assertIn("stock balance", cols_lc)

    def test_project_table_does_not_shift_labels_when_middle_column_is_missing(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse"},
                    {"fieldname": "item_code", "label": "Item Code"},
                ],
                "rows": [
                    {"warehouse": "Yangon Main Warehouse - MMOB", "item_code": "ACC-AUD-SAM-EAR35"},
                ],
            },
        }
        spec = {
            "metric": "xqz_metric_foo",
            "group_by": ["item"],
            "output_contract": {"mode": "detail", "minimal_columns": ["warehouse", "xqz_metric_foo", "item"]},
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
        labels = [str(c.get("label") or "").strip().lower() for c in cols]
        self.assertIn("warehouse", labels)
        self.assertIn("item", labels)
        self.assertNotIn("xqz metric foo", labels)

    def test_metric_binding_rejects_non_numeric_column(self):
        mod = _load_module()
        columns = [
            {"fieldname": "warehouse", "label": "Warehouse"},
            {"fieldname": "item_code", "label": "Item Code"},
            {"fieldname": "projected_qty", "label": "Projected Qty", "fieldtype": "Float"},
        ]
        rows = [
            {
                "warehouse": "Yangon Main Warehouse - MMOB",
                "item_code": "ACC-AUD-SAM-EAR35",
                "projected_qty": 280,
            },
        ]
        bindings = list(mod._match_column_indexes(columns, rows, ["stock balance"]))
        matched_fieldnames = []
        for idx, _wanted in bindings:
            matched_fieldnames.append(str(columns[idx].get("fieldname") or "").strip().lower())
        self.assertNotIn("item_code", matched_fieldnames)

    def test_minimal_columns_prioritizes_dimensions_then_metric(self):
        mod = _load_module()
        spec = {
            "metric": "stock balance",
            "group_by": ["item"],
            "dimensions": ["item"],
            "output_contract": {"mode": "detail", "minimal_columns": ["warehouse", "stock balance"]},
        }
        cols = [str(x).strip().lower() for x in list(mod._minimal_columns(spec))]
        self.assertGreaterEqual(len(cols), 3)
        self.assertEqual(cols[0], "item")
        self.assertEqual(cols[1], "stock balance")
        self.assertEqual(cols[2], "warehouse")

    def test_shape_response_binds_revenue_to_amount_when_report_is_item_sales_detail(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Item-wise Sales Register",
            "title": "Item-wise Sales Register",
            "table": {
                "columns": [
                    {"fieldname": "item_code", "label": "Item Code", "fieldtype": "Link"},
                    {"fieldname": "amount", "label": "Amount", "fieldtype": "Currency"},
                    {"fieldname": "customer", "label": "Customer", "fieldtype": "Link"},
                ],
                "rows": [
                    {"item_code": "SPH-APP-IP14-128", "amount": 7800000.0, "customer": "Capital Telecom"},
                    {"item_code": "SPH-SAM-A15-6/128", "amount": 6800000.0, "customer": "Capital Telecom"},
                ],
            },
        }
        spec = {
            "metric": "revenue",
            "group_by": ["item"],
            "dimensions": ["item"],
            "top_n": 10,
            "task_type": "ranking",
            "output_contract": {"mode": "top_n", "minimal_columns": ["item", "revenue"]},
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
        labels = [str(c.get("label") or "").strip().lower() for c in cols]
        fieldnames = [str(c.get("fieldname") or "").strip().lower() for c in cols]
        self.assertEqual(labels, ["item", "revenue"])
        self.assertEqual(fieldnames, ["item_code", "amount"])
        rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].get("item_code"), "SPH-APP-IP14-128")
        self.assertEqual(float(rows[0].get("amount") or 0.0), 7800000.0)

    def test_shape_response_binds_outstanding_amount_to_closing_balance(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Customer Ledger Summary",
            "title": "Customer Ledger Summary",
            "table": {
                "columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "invoiced_amount", "label": "Invoiced Amount", "fieldtype": "Currency"},
                    {"fieldname": "closing_balance", "label": "Closing Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"party": "Customer A", "invoiced_amount": 1000.0, "closing_balance": 400.0},
                    {"party": "Customer B", "invoiced_amount": 900.0, "closing_balance": 700.0},
                ],
            },
        }
        spec = {
            "metric": "outstanding amount",
            "group_by": ["customer"],
            "dimensions": ["customer"],
            "top_n": 10,
            "task_type": "ranking",
            "output_contract": {"mode": "top_n", "minimal_columns": ["customer", "outstanding amount"]},
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
        labels = [str(c.get("label") or "").strip().lower() for c in cols]
        fieldnames = [str(c.get("fieldname") or "").strip().lower() for c in cols]
        self.assertEqual(labels, ["customer", "outstanding amount"])
        self.assertEqual(fieldnames, ["party", "closing_balance"])
        rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
        self.assertEqual(rows[0].get("party"), "Customer B")
        self.assertEqual(float(rows[0].get("closing_balance") or 0.0), 700.0)

    def test_shape_response_uses_supplier_contract_roles_for_purchase_amount(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Supplier Ledger Summary",
            "title": "Supplier Ledger Summary",
            "table": {
                "columns": [
                    {"fieldname": "party", "label": "Supplier", "fieldtype": "Link"},
                    {"fieldname": "invoiced_amount", "label": "Purchase Amount", "fieldtype": "Currency"},
                    {"fieldname": "closing_balance", "label": "Closing Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"party": "Supplier A", "invoiced_amount": 1200.0, "closing_balance": 100.0},
                    {"party": "Supplier B", "invoiced_amount": 2400.0, "closing_balance": 700.0},
                ],
            },
        }
        spec = {
            "metric": "purchase amount",
            "group_by": ["supplier"],
            "dimensions": ["supplier"],
            "top_n": 10,
            "task_type": "ranking",
            "output_contract": {"mode": "top_n", "minimal_columns": ["supplier", "purchase amount"]},
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
        rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
        self.assertEqual(
            [str(c.get("fieldname") or "").strip().lower() for c in cols],
            ["party", "invoiced_amount"],
        )
        self.assertEqual(
            [(str(r.get("party") or ""), float(r.get("invoiced_amount") or 0.0)) for r in rows],
            [("Supplier B", 2400.0), ("Supplier A", 1200.0)],
        )

    def test_shape_response_dedupes_alias_equivalent_supplier_columns(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Supplier Ledger Summary",
            "title": "Supplier Ledger Summary",
            "table": {
                "columns": [
                    {"fieldname": "party", "label": "Supplier", "fieldtype": "Link"},
                    {"fieldname": "supplier", "label": "Supplier", "fieldtype": "Link"},
                    {"fieldname": "closing_balance", "label": "Outstanding Amount", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"party": "Supplier A", "supplier": "Supplier A", "closing_balance": 1000.0},
                    {"party": "Supplier B", "supplier": "Supplier B", "closing_balance": 700.0},
                ],
            },
        }
        spec = {
            "metric": "outstanding amount",
            "group_by": ["supplier"],
            "dimensions": ["supplier"],
            "top_n": 10,
            "task_type": "ranking",
            "output_contract": {"mode": "top_n", "minimal_columns": ["supplier", "outstanding amount"]},
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
        self.assertEqual(
            [str(c.get("fieldname") or "").strip().lower() for c in cols],
            ["party", "closing_balance"],
        )

    def test_top_n_aggregates_requested_dimension_and_honors_lowest_direction(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Stock Balance",
            "title": "Stock Balance",
            "table": {
                "columns": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link"},
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "bal_qty", "label": "Balance Qty", "fieldtype": "Float"},
                ],
                "rows": [
                    {"item_code": "ITEM-001", "warehouse": "Warehouse A", "bal_qty": 4.0},
                    {"item_code": "ITEM-002", "warehouse": "Warehouse A", "bal_qty": 6.0},
                    {"item_code": "ITEM-003", "warehouse": "Warehouse B", "bal_qty": 2.0},
                    {"item_code": "ITEM-004", "warehouse": "Warehouse C", "bal_qty": 5.0},
                    {"item_code": "ITEM-005", "warehouse": "All Warehouses - MMOB", "bal_qty": 99.0},
                ],
            },
        }
        spec = {
            "metric": "stock balance",
            "group_by": ["warehouse"],
            "dimensions": ["warehouse"],
            "top_n": 2,
            "task_type": "ranking",
            "output_contract": {"mode": "top_n", "minimal_columns": ["warehouse", "stock balance"]},
            "ambiguities": ["transform_sort:asc"],
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
        self.assertEqual(
            [(str(r.get("warehouse") or ""), float(r.get("bal_qty") or 0.0)) for r in rows],
            [("Warehouse B", 2.0), ("Warehouse C", 5.0)],
        )

    def test_top_n_uses_report_contract_aggregate_dimension_values(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Warehouse Wise Stock Balance",
            "title": "Warehouse Wise Stock Balance",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"warehouse": "All Warehouses - MMOB", "stock_balance": 618277000.0},
                    {"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399386000.0},
                    {"warehouse": "Mandalay Warehouse - MMOB", "stock_balance": 166006000.0},
                ],
            },
        }
        spec = {
            "metric": "stock balance",
            "group_by": ["warehouse"],
            "dimensions": ["warehouse"],
            "top_n": 2,
            "task_type": "ranking",
            "output_contract": {"mode": "top_n", "minimal_columns": ["warehouse", "stock balance"]},
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
        self.assertEqual(
            [(str(r.get("warehouse") or ""), float(r.get("stock_balance") or 0.0)) for r in rows],
            [
                ("Yangon Main Warehouse - MMOB", 399386000.0),
                ("Mandalay Warehouse - MMOB", 166006000.0),
            ],
        )

    def test_top_n_backfills_from_source_table_after_aggregate_row_exclusion(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Warehouse Wise Stock Balance",
            "title": "Warehouse Wise Stock Balance",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"warehouse": "All Warehouses - MMOB", "stock_balance": 618277000.0},
                    {"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399386000.0},
                    {"warehouse": "Mandalay Warehouse - MMOB", "stock_balance": 166006000.0},
                ],
            },
            "_source_table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"warehouse": "All Warehouses - MMOB", "stock_balance": 618277000.0},
                    {"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399386000.0},
                    {"warehouse": "Mandalay Warehouse - MMOB", "stock_balance": 166006000.0},
                    {"warehouse": "Yangon Showroom Counter - MMOB", "stock_balance": 52885000.0},
                ],
            },
        }
        spec = {
            "metric": "stock balance",
            "group_by": ["warehouse"],
            "dimensions": ["warehouse"],
            "top_n": 3,
            "task_type": "ranking",
            "output_contract": {"mode": "top_n", "minimal_columns": ["warehouse", "stock balance"]},
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
        self.assertEqual(
            [(str(r.get("warehouse") or ""), float(r.get("stock_balance") or 0.0)) for r in rows],
            [
                ("Yangon Main Warehouse - MMOB", 399386000.0),
                ("Mandalay Warehouse - MMOB", 166006000.0),
                ("Yangon Showroom Counter - MMOB", 52885000.0),
            ],
        )

    def test_top_n_backfill_preserves_existing_million_scale(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Warehouse Wise Stock Balance",
            "title": "Warehouse Wise Stock Balance",
            "_scaled_unit": "million",
            "table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"warehouse": "All Warehouses - MMOB", "stock_balance": 618.277},
                    {"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399.386},
                    {"warehouse": "Mandalay Warehouse - MMOB", "stock_balance": 166.006},
                ],
            },
            "_source_table": {
                "columns": [
                    {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link"},
                    {"fieldname": "stock_balance", "label": "Stock Balance", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"warehouse": "All Warehouses - MMOB", "stock_balance": 618277000.0},
                    {"warehouse": "Yangon Main Warehouse - MMOB", "stock_balance": 399386000.0},
                    {"warehouse": "Mandalay Warehouse - MMOB", "stock_balance": 166006000.0},
                    {"warehouse": "Yangon Showroom Counter - MMOB", "stock_balance": 52885000.0},
                ],
            },
        }
        spec = {
            "metric": "stock balance",
            "group_by": ["warehouse"],
            "dimensions": ["warehouse"],
            "top_n": 3,
            "task_type": "ranking",
            "output_contract": {"mode": "top_n", "minimal_columns": ["warehouse", "stock balance"]},
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
        self.assertEqual(
            [(str(r.get("warehouse") or ""), float(r.get("stock_balance") or 0.0)) for r in rows],
            [
                ("Yangon Main Warehouse - MMOB", 399.386),
                ("Mandalay Warehouse - MMOB", 166.006),
                ("Yangon Showroom Counter - MMOB", 52.885),
            ],
        )

    def test_transform_last_scale_followup_preserves_prior_top_n_mode(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "report_name": "Customer Ledger Summary",
            "title": "Customer Ledger Summary",
            "_output_mode": "top_n",
            "_scaled_unit": "million",
            "_transform_last_applied": "top_n",
            "table": {
                "columns": [
                    {"fieldname": "party", "label": "Customer", "fieldtype": "Link"},
                    {"fieldname": "closing_balance", "label": "Outstanding Amount", "fieldtype": "Currency"},
                ],
                "rows": [
                    {"party": "Customer A", "closing_balance": 16.22},
                    {"party": "Customer B", "closing_balance": 15.83},
                ],
            },
        }
        spec = {
            "intent": "TRANSFORM_LAST",
            "task_class": "transform_followup",
            "task_type": "kpi",
            "aggregation": "sum",
            "metric": "outstanding amount",
            "group_by": ["customer"],
            "top_n": 10,
            "dimensions": [],
            "ambiguities": ["transform_scale:million"],
            "output_contract": {"mode": "kpi", "minimal_columns": ["customer", "outstanding amount"]},
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        cols = [c for c in list(table.get("columns") or []) if isinstance(c, dict)]
        rows = [r for r in list(table.get("rows") or []) if isinstance(r, dict)]
        self.assertEqual(
            [str(c.get("fieldname") or "").strip().lower() for c in cols],
            ["party", "closing_balance"],
        )
        self.assertEqual(
            [(str(r.get("party") or ""), float(r.get("closing_balance") or 0.0)) for r in rows],
            [("Customer A", 16.22), ("Customer B", 15.83)],
        )

    def test_project_table_prefers_specific_item_name_over_generic_item_dimension(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link"},
                    {"fieldname": "total_qty", "label": "Sold Quantity", "fieldtype": "Float"},
                    {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data"},
                ],
                "rows": [
                    {"item_code": "ACC-001", "total_qty": 206.0, "item_name": "Type-C Cable 1m Fast Charge"},
                ],
            },
        }
        spec = {
            "group_by": ["item"],
            "metric": "sold quantity",
            "ambiguities": ["transform_projection:only"],
            "output_contract": {"mode": "top_n", "minimal_columns": ["item name", "sold quantity"]},
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        self.assertEqual(
            [str(c.get("label") or "") for c in list(table.get("columns") or []) if isinstance(c, dict)],
            ["Item Name", "Sold Quantity"],
        )

    def test_projection_only_can_return_single_explicit_column(self):
        mod = _load_module()
        payload = {
            "type": "report_table",
            "table": {
                "columns": [
                    {"fieldname": "item_code", "label": "Item", "fieldtype": "Link"},
                    {"fieldname": "total_qty", "label": "Sold Quantity", "fieldtype": "Float"},
                    {"fieldname": "item_name", "label": "Item Name", "fieldtype": "Data"},
                ],
                "rows": [
                    {"item_code": "ACC-001", "total_qty": 206.0, "item_name": "Type-C Cable 1m Fast Charge"},
                ],
            },
        }
        spec = {
            "group_by": ["item"],
            "metric": "sold quantity",
            "ambiguities": ["transform_projection:only"],
            "output_contract": {"mode": "top_n", "minimal_columns": ["item name"]},
        }
        shaped = mod.shape_response(payload=payload, business_spec=spec)
        table = shaped.get("table") if isinstance(shaped.get("table"), dict) else {}
        self.assertEqual(
            [str(c.get("label") or "") for c in list(table.get("columns") or []) if isinstance(c, dict)],
            ["Item Name"],
        )


if __name__ == "__main__":
    unittest.main()
