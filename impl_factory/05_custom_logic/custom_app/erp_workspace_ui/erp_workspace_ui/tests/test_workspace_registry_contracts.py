import json
from pathlib import Path
import unittest

from erp_workspace_ui import hooks
from erp_workspace_ui.workspace_registry import (
    get_active_workspace_definitions,
    get_finance_workspace_definition,
    get_procurement_workspace_definition,
    get_sales_workspace_definition,
    get_warehouse_workspace_definition,
    get_workspace_by_route,
    get_workspace_definition,
    get_workspace_roadmap,
)


class TestWorkspaceRegistryContracts(unittest.TestCase):
    def test_sales_console_freeze_routes_remain_canonical(self):
        workspace = get_sales_workspace_definition()

        self.assertEqual(workspace["workspace_id"], "sales")
        self.assertEqual(workspace["status"], "frozen")
        self.assertEqual(workspace["freeze_tag"], "sales-console-freeze-v1")
        self.assertEqual(
            workspace["routes"],
            {
                "launcher": "sales-console-home",
                "launcher_path": "/desk/sales-console-home",
                "home": "sales-console",
                "home_path": "/desk/sales-console",
                "worklist": "sales-console-worklist",
                "report": "sales-console-report",
            },
        )
        self.assertEqual(
            workspace["methods"]["bootstrap"],
            "erp_workspace_ui.sales_console.service.get_sales_console_bootstrap",
        )

    def test_sales_console_routes_resolve_to_registry_definition(self):
        for route_key in [
            "sales-console-home",
            "sales-console",
            "sales-console-worklist",
            "sales-console-report",
        ]:
            with self.subTest(route_key=route_key):
                workspace = get_workspace_by_route(route_key)
                self.assertIsNotNone(workspace)
                self.assertEqual(workspace["workspace_id"], "sales")

    def test_procurement_review_page_json_files_are_valid(self):
        app_root = Path(__file__).resolve().parents[1]
        pages = {
            "procurement_console_purchase_request_review": "procurement-console-purchase-request-review",
            "procurement_console_purchase_request_form": "procurement-console-purchase-request-form",
            "procurement_console_rfq_review": "procurement-console-rfq-review",
            "procurement_console_supplier_quotation_form": "procurement-console-supplier-quotation-form",
            "procurement_console_supplier_quotation_review": "procurement-console-supplier-quotation-review",
        }

        for folder, page_name in pages.items():
            with self.subTest(page=page_name):
                path = app_root / "erp_workspace_ui" / "page" / folder / f"{folder}.json"
                payload = json.loads(path.read_text())
                self.assertEqual(payload["doctype"], "Page")
                self.assertEqual(payload["name"], page_name)
                self.assertEqual(payload["page_name"], page_name)
                self.assertEqual(payload["module"], "ERP Workspace UI")
                self.assertEqual(payload["standard"], "Yes")

    def test_procurement_console_phase3_registry_definition(self):
        workspace = get_procurement_workspace_definition()

        self.assertEqual(workspace["workspace_id"], "procurement")
        self.assertEqual(workspace["status"], "phase_3")
        self.assertEqual(workspace["title"], "Procurement Console")
        self.assertEqual(
            workspace["routes"],
            {
                "launcher": "procurement-console-home",
                "launcher_path": "/desk/procurement-console-home",
                "home": "procurement-console",
                "home_path": "/desk/procurement-console",
                "worklist": "procurement-console-worklist",
                "report": "procurement-console-report",
                "po_follow_up": "procurement-console-po-follow-up",
                "supplier_detail": "procurement-console-supplier",
                "item_detail": "procurement-console-item",
                "purchase_request_review": "procurement-console-purchase-request-review",
                "purchase_request_form": "procurement-console-purchase-request-form",
                "rfq_review": "procurement-console-rfq-review",
                "supplier_quotation_form": "procurement-console-supplier-quotation-form",
                "supplier_quotation_review": "procurement-console-supplier-quotation-review",
                "purchase_order_form": "procurement-console-purchase-order-form",
            },
        )
        self.assertEqual(
            workspace["methods"]["bootstrap"],
            "erp_workspace_ui.procurement_console.service.get_procurement_console_bootstrap",
        )
        self.assertEqual(
            workspace["methods"]["worklist_context"],
            "erp_workspace_ui.procurement_console.worklist.get_procurement_console_worklist_context",
        )
        self.assertEqual(
            workspace["methods"]["purchase_request_review_context"],
            "erp_workspace_ui.procurement_console.document_reviews.get_purchase_request_review_context",
        )
        self.assertEqual(
            workspace["methods"]["managed_purchase_request_context"],
            "erp_workspace_ui.procurement_console.managed_purchase_request.get_managed_purchase_request_context",
        )
        self.assertEqual(
            workspace["methods"]["managed_purchase_request_save"],
            "erp_workspace_ui.procurement_console.managed_purchase_request.save_managed_purchase_request_draft",
        )
        self.assertEqual(
            workspace["methods"]["managed_purchase_request_item_defaults"],
            "erp_workspace_ui.procurement_console.managed_purchase_request.get_managed_purchase_request_item_defaults",
        )
        self.assertEqual(
            workspace["methods"]["managed_supplier_quotation_context"],
            "erp_workspace_ui.procurement_console.managed_supplier_quotation.get_managed_supplier_quotation_context",
        )
        self.assertEqual(
            workspace["methods"]["managed_supplier_quotation_save"],
            "erp_workspace_ui.procurement_console.managed_supplier_quotation.save_managed_supplier_quotation_draft",
        )
        self.assertEqual(
            workspace["methods"]["managed_supplier_quotation_item_defaults"],
            "erp_workspace_ui.procurement_console.managed_supplier_quotation.get_managed_supplier_quotation_item_defaults",
        )
        self.assertEqual(
            workspace["methods"]["rfq_review_context"],
            "erp_workspace_ui.procurement_console.document_reviews.get_rfq_review_context",
        )
        self.assertEqual(
            workspace["methods"]["supplier_quotation_review_context"],
            "erp_workspace_ui.procurement_console.document_reviews.get_supplier_quotation_review_context",
        )
        self.assertEqual(
            workspace["methods"]["report_context"],
            "erp_workspace_ui.procurement_console.report.get_procurement_console_report_context",
        )
        self.assertEqual(
            workspace["methods"]["po_follow_up_detail_context"],
            "erp_workspace_ui.procurement_console.purchase_order_detail.get_purchase_order_follow_up_detail_context",
        )
        self.assertEqual(
            workspace["methods"]["supplier_detail_context"],
            "erp_workspace_ui.procurement_console.supplier_detail.get_supplier_detail_context",
        )
        self.assertEqual(
            workspace["methods"]["item_detail_context"],
            "erp_workspace_ui.procurement_console.items.get_item_detail_context",
        )
        self.assertEqual(
            workspace["fallback_items"],
            [
                {
                    "key": "procurement_console_home",
                    "label": "Overview",
                    "icon": "home",
                    "target": {"kind": "page", "route": "procurement-console"},
                },
                {
                    "key": "supplier_directory",
                    "label": "Suppliers",
                    "icon": "customer",
                    "target": {"kind": "worklist", "queue_key": "supplier_directory"},
                },
                {
                    "key": "purchase_request_directory",
                    "label": "Purchase Requests",
                    "icon": "quotation",
                    "target": {"kind": "worklist", "queue_key": "purchase_request_directory"},
                },
                {
                    "key": "purchase_order_directory",
                    "label": "Purchase Orders",
                    "icon": "order",
                    "target": {"kind": "worklist", "queue_key": "purchase_order_directory"},
                },
                {
                    "key": "rfq_directory",
                    "label": "RFQs",
                    "icon": "quotation",
                    "target": {"kind": "worklist", "queue_key": "rfq_directory"},
                },
                {
                    "key": "supplier_quotation_directory",
                    "label": "Supplier Quotations",
                    "icon": "quotation",
                    "target": {"kind": "worklist", "queue_key": "supplier_quotation_directory"},
                },
                {
                    "key": "buying_item_directory",
                    "label": "Buying Items",
                    "icon": "item",
                    "target": {"kind": "worklist", "queue_key": "buying_item_directory"},
                },
                {
                    "key": "procurement_reports",
                    "label": "Reports",
                    "icon": "report",
                    "target": {"kind": "page", "route": "procurement-console-report"},
                },
            ],
        )



    def test_procurement_reports_sidebar_target_uses_report_index_route(self):
        workspace = get_procurement_workspace_definition()
        target = next(
            item["target"] for item in workspace["fallback_items"] if item["key"] == "procurement_reports"
        )

        self.assertEqual(target, {"kind": "page", "route": "procurement-console-report"})

    def test_procurement_quote_comparison_is_not_a_standalone_sidebar_item(self):
        workspace = get_procurement_workspace_definition()
        labels = [item["label"] for item in workspace["fallback_items"]]
        keys = [item["key"] for item in workspace["fallback_items"]]

        self.assertEqual(
            labels,
            ["Overview", "Suppliers", "Purchase Requests", "Purchase Orders", "RFQs", "Supplier Quotations", "Buying Items", "Reports"],
        )
        self.assertNotIn("Quote Comparison", labels)
        self.assertNotIn("supplier_quotation_comparison", keys)

    def test_procurement_console_routes_resolve_to_registry_definition(self):
        for route_key in [
            "procurement-console-home",
            "procurement-console",
            "procurement-console-worklist",
            "procurement-console-report",
            "procurement-console-po-follow-up",
            "procurement-console-purchase-request-form",
            "procurement-console-supplier-quotation-form",
            "procurement-console-supplier",
            "procurement-console-item",
        ]:
            with self.subTest(route_key=route_key):
                workspace = get_workspace_by_route(route_key)
                self.assertIsNotNone(workspace)
                self.assertEqual(workspace["workspace_id"], "procurement")

    def test_warehouse_console_w8c_registry_definition(self):
        workspace = get_warehouse_workspace_definition()

        self.assertEqual(workspace["workspace_id"], "warehouse")
        self.assertEqual(workspace["status"], "w8c_transfer_visibility")
        self.assertEqual(workspace["title"], "Warehouse Console")
        self.assertEqual(
            workspace["routes"],
            {
                "home": "warehouse-console",
                "home_path": "/desk/warehouse-console",
                "worklist": "warehouse-console-worklist",
                "worklist_path": "/desk/warehouse-console-worklist",
                "receiving": "warehouse-console-receiving",
                "receiving_path": "/desk/warehouse-console-receiving",
                "picking": "warehouse-console-picking",
                "picking_path": "/desk/warehouse-console-picking",
                "stock_exception": "warehouse-console-stock-exception",
                "stock_exception_path": "/desk/warehouse-console-stock-exception",
                "stock_posture": "warehouse-console-stock-posture",
                "stock_posture_path": "/desk/warehouse-console-stock-posture",
                "movement": "warehouse-console-movement",
                "movement_path": "/desk/warehouse-console-movement",
            },
        )
        self.assertEqual(
            workspace["methods"],
            {
                "overview": "erp_workspace_ui.warehouse_console.service.get_warehouse_console_overview",
                "inbound_queue": "erp_workspace_ui.warehouse_console.service.get_warehouse_inbound_receiving_queue",
                "outbound_queue": "erp_workspace_ui.warehouse_console.service.get_warehouse_outbound_picking_queue",
                "receiving_detail": "erp_workspace_ui.warehouse_console.service.get_warehouse_receiving_review",
                "picking_detail": "erp_workspace_ui.warehouse_console.service.get_warehouse_picking_review",
                "returns_work_hub": "erp_workspace_ui.warehouse_console.service.get_warehouse_returns_work_hub",
                "internal_transfer_workflow": "erp_workspace_ui.warehouse_console.service.get_warehouse_internal_transfer_workflow",
                "cycle_count_workflow": "erp_workspace_ui.warehouse_console.service.get_warehouse_cycle_count_workflow",
                "customer_return_intake_draft": "erp_workspace_ui.warehouse_console.service.save_warehouse_customer_return_intake_draft",
                "customer_return_manager_decision": "erp_workspace_ui.warehouse_console.service.save_warehouse_customer_return_manager_decision",
                "supplier_return_candidate_draft": "erp_workspace_ui.warehouse_console.service.save_warehouse_supplier_return_candidate_draft",
                "supplier_return_manager_decision": "erp_workspace_ui.warehouse_console.service.save_warehouse_supplier_return_manager_decision",
                "internal_transfer_candidate_draft": "erp_workspace_ui.warehouse_console.service.save_warehouse_internal_transfer_candidate_draft",
                "internal_transfer_manager_decision": "erp_workspace_ui.warehouse_console.service.save_warehouse_internal_transfer_manager_decision",
                "cycle_count_task_draft": "erp_workspace_ui.warehouse_console.service.save_warehouse_cycle_count_task_draft",
                "cycle_count_manager_decision": "erp_workspace_ui.warehouse_console.service.save_warehouse_cycle_count_manager_decision",
                "stock_exceptions": "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_exceptions",
                "stock_exception_review": "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_exception_review",
                "stock_posture_review": "erp_workspace_ui.warehouse_console.service.get_warehouse_stock_posture_review",
                "movement_visibility": "erp_workspace_ui.warehouse_console.service.get_warehouse_movement_visibility_queue",
                "movement_review": "erp_workspace_ui.warehouse_console.service.get_warehouse_movement_review",
                "transfer_visibility": "erp_workspace_ui.warehouse_console.service.get_warehouse_transfer_visibility_queue",
                "quick_find": "erp_workspace_ui.warehouse_console.service.get_warehouse_quick_find_suggestions",
                "workspace_search": "erp_workspace_ui.warehouse_console.service.search_warehouse_console_workspace",
                "sidebar_context": "erp_workspace_ui.warehouse_console.service.get_warehouse_console_sidebar_context",
            },
        )
        self.assertEqual(
            workspace["search"],
            {
                "enabled": True,
                "mode": "warehouse_sidebar_search",
                "placement": "sidebar_utility",
                "placeholder": "Find purchase orders, sales orders, items, warehouses, or movements",
            },
        )
        self.assertEqual(
            workspace["fallback_items"],
            [
                {
                    "key": "warehouse_console_home",
                    "label": "Overview",
                    "icon": "item",
                    "target": {"kind": "page", "route": "warehouse-console"},
                },
                {
                    "key": "inbound_receiving",
                    "label": "Inbound Receiving",
                    "icon": "quotation",
                    "target": {"kind": "worklist", "queue_key": "inbound_receiving"},
                },
                {
                    "key": "outbound_picking",
                    "label": "Outbound Picking",
                    "icon": "order",
                    "target": {"kind": "worklist", "queue_key": "outbound_picking"},
                },
                {
                    "key": "stock_exceptions",
                    "label": "Stock Exceptions",
                    "icon": "report",
                    "target": {"kind": "worklist", "queue_key": "stock_exceptions"},
                },
                {
                    "key": "returns_work_hub",
                    "label": "Returns",
                    "icon": "return",
                    "target": {"kind": "worklist", "queue_key": "returns_work_hub"},
                },
                {
                    "key": "internal_transfer_workflow",
                    "label": "Internal Transfer",
                    "icon": "stock",
                    "target": {"kind": "worklist", "queue_key": "internal_transfer_workflow"},
                },
                {
                    "key": "cycle_count_workflow",
                    "label": "Cycle Count",
                    "icon": "report",
                    "target": {"kind": "worklist", "queue_key": "cycle_count_workflow"},
                },
                {
                    "key": "movement_visibility",
                    "label": "Movement Visibility",
                    "icon": "stock",
                    "target": {"kind": "worklist", "queue_key": "movement_visibility"},
                },
                {
                    "key": "transfer_visibility",
                    "label": "Transfer Visibility",
                    "icon": "stock",
                    "target": {"kind": "worklist", "queue_key": "transfer_visibility"},
                },
            ],
        )

    def test_warehouse_console_w8b_route_resolves_to_registry_definition(self):
        for route_key in ["warehouse-console", "warehouse-console-worklist", "warehouse-console-receiving", "warehouse-console-picking", "warehouse-console-stock-exception", "warehouse-console-stock-posture", "warehouse-console-movement"]:
            with self.subTest(route_key=route_key):
                workspace = get_workspace_by_route(route_key)
                self.assertIsNotNone(workspace)
                self.assertEqual(workspace["workspace_id"], "warehouse")

    def test_finance_control_desk_f4_registry_definition(self):
        workspace = get_finance_workspace_definition()

        self.assertEqual(workspace["workspace_id"], "finance")
        self.assertEqual(workspace["status"], "f4_ar_aggregate_posture")
        self.assertEqual(workspace["title"], "Finance Control Desk")
        self.assertEqual(workspace["workspace_family"], "Finance & Accounting")
        self.assertEqual(workspace["mode_label"], "Finance & Accounting Workspace")
        self.assertEqual(
            workspace["routes"],
            {
                "home": "finance-control-desk",
                "home_path": "/desk/finance-control-desk",
            },
        )
        self.assertEqual(
            workspace["methods"],
            {
                "shell_context": "erp_workspace_ui.finance_accounting.service.get_finance_control_desk_shell_context",
                "overview_context": "erp_workspace_ui.finance_accounting.service.get_finance_control_desk_overview_context",
                "sidebar_context": "erp_workspace_ui.finance_accounting.service.get_finance_control_desk_sidebar_context",
                "workspace_search": "erp_workspace_ui.finance_accounting.service.search_finance_control_desk_workspace",
            },
        )
        self.assertEqual(workspace["managed_doctypes"], {})
        self.assertEqual(workspace["directory_queues_by_doctype"], {})
        self.assertEqual(
            workspace["search"],
            {
                "enabled": False,
                "mode": "finance_f4_ar_aggregate_posture_no_rows",
                "placement": "none",
                "placeholder": "Finance search is not active for AR aggregate posture",
            },
        )
        self.assertEqual(
            workspace["fallback_items"],
            [
                {
                    "key": "finance_control_desk_home",
                    "label": "Foundation",
                    "icon": "home",
                    "target": {"kind": "page", "route": "finance-control-desk"},
                },
            ],
        )

    def test_finance_control_desk_route_resolves_to_registry_definition(self):
        workspace = get_workspace_by_route("finance-control-desk")
        self.assertIsNotNone(workspace)
        self.assertEqual(workspace["workspace_id"], "finance")

    def test_finance_control_desk_page_json_file_is_valid(self):
        app_root = Path(__file__).resolve().parents[1]
        path = app_root / "erp_workspace_ui" / "page" / "finance_control_desk" / "finance_control_desk.json"
        payload = json.loads(path.read_text())

        self.assertEqual(payload["doctype"], "Page")
        self.assertEqual(payload["name"], "finance-control-desk")
        self.assertEqual(payload["page_name"], "finance-control-desk")
        self.assertEqual(payload["title"], "Finance Control Desk")
        self.assertEqual(payload["module"], "ERP Workspace UI")
        self.assertEqual(payload["standard"], "Yes")

    def test_workspace_route_and_method_values_are_unique(self):
        workspaces = get_active_workspace_definitions()
        route_values = []
        method_values = []
        for workspace in workspaces:
            route_values.extend(
                value for key, value in workspace["routes"].items() if not key.endswith("_path")
            )
            method_values.extend(workspace["methods"].values())

        self.assertEqual(len(route_values), len(set(route_values)))
        self.assertEqual(len(method_values), len(set(method_values)))

    def test_active_workspace_definitions_are_copy_safe(self):
        workspace = get_workspace_definition("sales")
        workspace["routes"]["home"] = "changed-locally"

        procurement = get_workspace_definition("procurement")
        procurement["routes"]["home"] = "changed-procurement-locally"

        warehouse = get_workspace_definition("warehouse")
        warehouse["routes"]["home"] = "changed-warehouse-locally"

        finance = get_workspace_definition("finance")
        finance["routes"]["home"] = "changed-finance-locally"

        self.assertEqual(get_sales_workspace_definition()["routes"]["home"], "sales-console")
        self.assertEqual(get_procurement_workspace_definition()["routes"]["home"], "procurement-console")
        self.assertEqual(get_warehouse_workspace_definition()["routes"]["home"], "warehouse-console")
        self.assertEqual(get_finance_workspace_definition()["routes"]["home"], "finance-control-desk")
        self.assertEqual(len(get_active_workspace_definitions()), 4)

    def test_roadmap_uses_matrix_names_and_explicit_name_reviews(self):
        roadmap = get_workspace_roadmap()
        matrix_names = [item["matrix_name"] for item in roadmap]

        self.assertEqual(
            matrix_names[:4],
            ["Sales Console", "Procurement Console", "Warehouse Console", "Finance Console"],
        )
        self.assertNotIn("Inventory Console", matrix_names)

        procurement = next(item for item in roadmap if item["workspace_id"] == "procurement")
        warehouse = next(item for item in roadmap if item["workspace_id"] == "warehouse")
        finance = next(item for item in roadmap if item["workspace_id"] == "finance")
        executive = next(item for item in roadmap if item["workspace_id"] == "executive")
        self.assertEqual(procurement["recommended_name"], "Procurement Console")
        self.assertEqual(procurement["status"], "phase_3")
        self.assertEqual(warehouse["recommended_name"], "Warehouse Console")
        self.assertEqual(warehouse["status"], "w8c_transfer_visibility")
        self.assertEqual(finance["recommended_name"], "Finance Control Desk")
        self.assertEqual(finance["status"], "f4_ar_aggregate_posture")
        self.assertEqual(executive["recommended_name"], "Management Daily Brief")
        self.assertEqual(executive["status"], "name_review")

    def test_hooks_still_keep_sales_as_default_home_and_app_screen(self):
        include_js = list(hooks.app_include_js)

        self.assertEqual(hooks.app_home, "/desk/sales-console-home")
        self.assertEqual(hooks.add_to_apps_screen[0]["title"], "Sales Console")
        self.assertLess(
            include_js.index("/assets/erp_workspace_ui/js/runtime/console/workspace_registry.js"),
            include_js.index("/assets/erp_workspace_ui/js/erp_workspace_ui_boot.js"),
        )


if __name__ == "__main__":
    unittest.main()
