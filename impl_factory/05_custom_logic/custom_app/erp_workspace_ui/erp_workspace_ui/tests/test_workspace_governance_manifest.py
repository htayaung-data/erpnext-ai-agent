from __future__ import annotations

from pathlib import Path
import unittest

from erp_workspace_ui.workspace_governance_manifest import (
    ACTION_MANIFEST,
    FORBIDDEN_MUTATION_GUARDS,
    FORBIDDEN_MUTATION_LABELS,
    NATIVE_EXCEPTION_POLICIES,
    ROUTE_MANIFEST,
    VALID_ACTION_CLASSIFICATIONS,
    VALID_ROUTE_CLASSIFICATIONS,
    VALID_STATE_KINDS,
    route_keys_by_workspace,
    validate_manifest,
)
from erp_workspace_ui.workspace_registry import (
    get_procurement_workspace_definition,
    get_sales_workspace_definition,
    get_warehouse_workspace_definition,
)


APP_ROOT = Path(__file__).resolve().parents[1]


class TestWorkspaceGovernanceManifest(unittest.TestCase):
    def test_manifest_self_validates(self):
        self.assertEqual([], validate_manifest())

    def test_route_classification_values_are_approved(self):
        self.assertIn("productized_overview", VALID_ROUTE_CLASSIFICATIONS)
        self.assertIn("governed_native_exception", VALID_ROUTE_CLASSIFICATIONS)
        for route in ROUTE_MANIFEST:
            self.assertIn(route["classification"], VALID_ROUTE_CLASSIFICATIONS, route)
            self.assertTrue(route["workspace_id"], route)
            self.assertTrue(route["route_key"], route)
            self.assertTrue(route["route_pattern"], route)
            self.assertTrue(route["owning_adapter"], route)
            self.assertTrue(route["expected_shell"], route)

    def test_action_classification_values_are_approved(self):
        self.assertIn("governed_native_action", VALID_ACTION_CLASSIFICATIONS)
        self.assertIn("forbidden_mutation", VALID_ACTION_CLASSIFICATIONS)
        for action in ACTION_MANIFEST:
            self.assertIn(action["classification"], VALID_ACTION_CLASSIFICATIONS, action)
            self.assertTrue(action["manifest_key"], action)
            self.assertTrue(action["workspace_id"], action)
            self.assertTrue(action["source_route"], action)
            self.assertTrue(action["action_key"], action)
            self.assertTrue(action["target_kind"], action)
            self.assertTrue(action.get("label") or action.get("label_pattern"), action)

    def test_state_kinds_are_strict_shared_core_contract(self):
        self.assertEqual({"ready", "empty", "restricted", "unavailable", "error"}, set(VALID_STATE_KINDS))

    def test_governed_native_routes_and_actions_have_policy_references(self):
        for route in ROUTE_MANIFEST:
            if route["classification"] == "governed_native_exception":
                self.assertIn(route.get("native_exception_ref"), NATIVE_EXCEPTION_POLICIES, route)
        for action in ACTION_MANIFEST:
            if action["classification"] == "governed_native_action":
                self.assertIn(action.get("native_exception_ref"), NATIVE_EXCEPTION_POLICIES, action)

    def test_procurement_actions_do_not_declare_normal_role_native_form_escapes(self):
        forbidden_labels = {"Open ERP Form", "Open ERP Supplier Form", "Open ERP Item Form", "Advanced ERP Form"}
        forbidden_keys = {"open_erp_form", "open_supplier_form", "open_item_form", "advanced_erp_form"}
        for action in ACTION_MANIFEST:
            action_key = str(action.get("action_key") or "")
            source_route = str(action.get("source_route") or "")
            label = str(action.get("label") or action.get("label_pattern") or "")
            if action["workspace_id"] == "procurement":
                self.assertNotIn(action_key, forbidden_keys, action)
                self.assertNotIn(label, forbidden_labels, action)
                self.assertNotEqual("form", action.get("target_kind"), action)
            if action_key == "row:*:open_record" and source_route.startswith("procurement-console-worklist"):
                self.assertEqual("productized_navigation", action["classification"], action)
                self.assertNotEqual("form", action.get("target_kind"), action)

    def test_forbidden_mutation_labels_are_listed_and_guarded(self):
        required = {"Submit", "Cancel", "Amend", "Approve", "Reject", "Receive", "Bill", "Pay", "Set Default Supplier", "Update Item Price", "Delete"}
        self.assertTrue(required.issubset(set(FORBIDDEN_MUTATION_LABELS)))
        guarded_workspaces = {guard["workspace_id"] for guard in FORBIDDEN_MUTATION_GUARDS}
        self.assertEqual({"sales", "procurement", "warehouse"}, guarded_workspaces)
        for guard in FORBIDDEN_MUTATION_GUARDS:
            self.assertEqual(set(FORBIDDEN_MUTATION_LABELS), set(guard["labels"]), guard)
            self.assertIn("native-exception-policy-v1.md", guard["policy_doc"], guard)

    def test_procurement_rfq_send_readiness_is_allowed_but_send_is_blocked(self):
        actions = {action["manifest_key"]: action for action in ACTION_MANIFEST if action["workspace_id"] == "procurement"}

        readiness = actions["procurement-managed-rfq-recipient-readiness"]
        self.assertEqual("productized_secondary_action", readiness["classification"])
        self.assertEqual("current_shell", readiness["target_kind"])
        self.assertIn("Read-only", readiness["notes"])

        review_readiness = actions["procurement-rfq-review-recipient-readiness"]
        self.assertEqual("productized_secondary_action", review_readiness["classification"])
        self.assertEqual("current_shell", review_readiness["target_kind"])
        self.assertIn("Read-only", review_readiness["notes"])

        send = actions["procurement-managed-rfq-email-blocked"]
        self.assertEqual("disabled", send["target_kind"])
        self.assertEqual("Send RFQ", send["label"])
        self.assertIn("blocked", send["notes"].lower())

        review_send = actions["procurement-rfq-review-email-blocked"]
        self.assertEqual("disabled", review_send["target_kind"])
        self.assertEqual("Send RFQ", review_send["label"])
        self.assertIn("blocked", review_send["notes"].lower())

    def test_procurement_supplier_readiness_actions_are_productized(self):
        actions = {action["manifest_key"]: action for action in ACTION_MANIFEST if action["workspace_id"] == "procurement"}

        view = actions["procurement-supplier-readiness-view"]
        self.assertEqual("productized_secondary_action", view["classification"])
        self.assertEqual("current_shell", view["target_kind"])
        self.assertIn("readiness", view["notes"].lower())

        save = actions["procurement-supplier-readiness-save"]
        self.assertEqual("productized_secondary_action", save["classification"])
        self.assertEqual("current_shell", save["target_kind"])
        self.assertEqual("Save Readiness", save["label"])
        self.assertIn("no Supplier, Contact, User, email", save["notes"])
        self.assertNotEqual("form", save["target_kind"])

    def test_procurement_item_buying_profile_actions_are_productized(self):
        actions = {action["manifest_key"]: action for action in ACTION_MANIFEST if action["workspace_id"] == "procurement"}

        view = actions["procurement-item-buying-profile-view"]
        self.assertEqual("productized_secondary_action", view["classification"])
        self.assertEqual("current_shell", view["target_kind"])
        self.assertEqual("Buying Procurement Context", view["label"])
        self.assertIn("item buying profile", view["notes"].lower())

        save = actions["procurement-item-buying-profile-save"]
        self.assertEqual("productized_secondary_action", save["classification"])
        self.assertEqual("current_shell", save["target_kind"])
        self.assertEqual("Save Context", save["label"])
        self.assertIn("no Item, Item Supplier, Item Price, Default Supplier", save["notes"])
        self.assertNotEqual("form", save["target_kind"])

    def test_procurement_manager_readiness_actions_are_productized_read_only(self):
        actions = {action["manifest_key"]: action for action in ACTION_MANIFEST if action["workspace_id"] == "procurement"}

        overview = actions["procurement-manager-readiness-view"]
        self.assertEqual("productized_secondary_action", overview["classification"])
        self.assertEqual("current_shell", overview["target_kind"])
        self.assertIn("read-only", overview["notes"].lower())
        self.assertIn("no lifecycle", overview["notes"].lower())

        page = actions["procurement-page-readiness-view"]
        self.assertEqual("productized_secondary_action", page["classification"])
        self.assertEqual("current_shell", page["target_kind"])
        self.assertIn("read-only", page["notes"].lower())

        fix = actions["procurement-readiness-productized-fix-link"]
        self.assertEqual("productized_navigation", fix["classification"])
        self.assertEqual("page", fix["target_kind"])
        self.assertEqual("/desk/procurement-console-*", fix["target_route_pattern"])
        self.assertNotIn("Form", str(fix))

    def test_registry_route_keys_exist_in_manifest(self):
        workspace_pairs = [
            (get_sales_workspace_definition()["routes"], route_keys_by_workspace("sales")),
            (get_procurement_workspace_definition()["routes"], route_keys_by_workspace("procurement")),
            (get_warehouse_workspace_definition()["routes"], route_keys_by_workspace("warehouse")),
        ]

        for routes, manifest_keys in workspace_pairs:
            for key, value in routes.items():
                if key.endswith("_path"):
                    continue
                self.assertIn(value, manifest_keys, key)

    def test_warehouse_w3_routes_and_actions_are_read_only(self):
        warehouse_routes = [route for route in ROUTE_MANIFEST if route["workspace_id"] == "warehouse"]
        self.assertEqual(
            [
                "warehouse-console",
                "warehouse-console-worklist",
                "warehouse-console-worklist/inbound_receiving",
            ],
            [route["route_key"] for route in warehouse_routes],
        )
        self.assertEqual("productized_overview", warehouse_routes[0]["classification"])
        self.assertEqual("productized_worklist", warehouse_routes[1]["classification"])
        self.assertEqual("productized_worklist", warehouse_routes[2]["classification"])
        self.assertEqual("/desk/warehouse-console", warehouse_routes[0]["route_pattern"])
        self.assertEqual("/desk/warehouse-console-worklist/inbound-receiving", warehouse_routes[2]["route_pattern"])
        for route in warehouse_routes:
            self.assertNotEqual("governed_native_exception", route["classification"])
            self.assertIsNone(route.get("native_exception_ref"), route)

        warehouse_actions = {
            action["manifest_key"]: action
            for action in ACTION_MANIFEST
            if action["workspace_id"] == "warehouse"
        }
        self.assertEqual(
            {
                "warehouse-overview-refresh",
                "warehouse-overview-open-inbound",
                "warehouse-inbound-refresh",
                "warehouse-inbound-reset",
                "warehouse-inbound-apply",
                "warehouse-inbound-view-lines",
                "warehouse-sidebar-overview-navigation",
                "warehouse-sidebar-inbound-navigation",
            },
            set(warehouse_actions),
        )
        self.assertEqual("current_shell", warehouse_actions["warehouse-overview-refresh"]["target_kind"])
        self.assertEqual("worklist", warehouse_actions["warehouse-overview-open-inbound"]["target_kind"])
        self.assertEqual("current_shell", warehouse_actions["warehouse-inbound-view-lines"]["target_kind"])
        self.assertEqual("worklist", warehouse_actions["warehouse-sidebar-inbound-navigation"]["target_kind"])
        for action in warehouse_actions.values():
            self.assertNotIn(action["target_kind"], {"form", "report", "list", "new_doc"}, action)
            self.assertIsNone(action.get("native_exception_ref"), action)

    def test_procurement_home_routing_for_purchase_roles_is_owner_approved(self):
        boot_source = (APP_ROOT / "boot.py").read_text()
        self.assertIn("(PROCUREMENT_CONSOLE_HOME_PAGE, PROCUREMENT_CONSOLE_ROLES)", boot_source)
        self.assertIn("PROCUREMENT_CONSOLE_HOME_PAGE = \"procurement-console-home\"", boot_source)
        self.assertIn("procurement-console-home", route_keys_by_workspace("procurement"))
        procurement_home = next(route for route in ROUTE_MANIFEST if route["route_key"] == "procurement-console-home")
        self.assertIn("Owner-approved", procurement_home["notes"])

    def test_sales_remains_frozen_until_recovery_phase_intentionally_changes_it(self):
        sales = get_sales_workspace_definition()
        self.assertEqual("frozen", sales["status"])
        self.assertEqual("sales-console-freeze-v1", sales["freeze_tag"])
        self.assertIn("sales-console", route_keys_by_workspace("sales"))

    def test_sales_overview_quick_actions_are_manifest_declared(self):
        source = (APP_ROOT / "erp_workspace_ui" / "page" / "sales_console" / "sales_console.js").read_text()
        service_source = (APP_ROOT / "sales_console" / "service.py").read_text()
        expected = {
            "new_quotation": ("governed_native_action", "new_doc", "sales-managed-document-forms-v1"),
            "new_sales_order": ("governed_native_action", "new_doc", "sales-managed-document-forms-v1"),
            "open_customer": ("productized_navigation", "worklist", None),
            "open_item": ("productized_navigation", "worklist", None),
        }
        actions = {
            action["action_key"]: action
            for action in ACTION_MANIFEST
            if action["workspace_id"] == "sales" and action["source_route"] == "sales-console"
        }

        self.assertNotIn("new_opportunity", source)
        self.assertNotIn("new_opportunity", service_source)
        for action_key, (classification, target_kind, native_ref) in expected.items():
            self.assertIn(f'key: "{action_key}"', source)
            self.assertIn(action_key, service_source)
            self.assertIn(action_key, actions)
            self.assertEqual(classification, actions[action_key]["classification"])
            self.assertEqual(target_kind, actions[action_key]["target_kind"])
            if native_ref:
                self.assertEqual(native_ref, actions[action_key]["native_exception_ref"])

        self.assertEqual("/desk/sales-console-worklist/customer-directory", actions["open_customer"]["target_route_pattern"])
        self.assertEqual("/desk/sales-console-worklist/item-directory", actions["open_item"]["target_route_pattern"])

    def test_sales_customer_detail_activity_open_is_manifest_declared(self):
        action = next(
            item
            for item in ACTION_MANIFEST
            if item["manifest_key"] == "sales-customer-detail-managed-document-open"
        )

        self.assertEqual("sales-console-worklist/customer_detail/<customer>", action["source_route"])
        self.assertEqual("row:*:open_record", action["action_key"])
        self.assertEqual("productized_navigation", action["classification"])
        self.assertEqual("managed_form", action["target_kind"])
        self.assertEqual("sales-managed-document-forms-v1", action["native_exception_ref"])
        self.assertNotIn("Open ERP Form", action.get("label") or "")

    def test_sales_manifest_does_not_declare_unapproved_native_fallbacks(self):
        for action in ACTION_MANIFEST:
            if action["workspace_id"] != "sales":
                continue
            self.assertNotIn(action["action_key"], {"open_native_list", "open_native_report"}, action)
            self.assertNotEqual("Open Standard List", action.get("label"), action)
            self.assertNotEqual("Open Standard Report", action.get("label"), action)
            if action["target_kind"] in {"form", "report", "list"}:
                self.assertEqual("governed_native_action", action["classification"], action)
                self.assertEqual("sales-managed-document-forms-v1", action.get("native_exception_ref"), action)

    def test_not_allowed_leakage_requires_repair_owner_and_status(self):
        for route in ROUTE_MANIFEST:
            if route["classification"] == "not_allowed_leakage":
                self.assertTrue(route.get("repair_owner"), route)
                self.assertTrue(route.get("repair_status"), route)
        for action in ACTION_MANIFEST:
            if action["classification"] == "not_allowed_leakage":
                self.assertTrue(action.get("repair_owner"), action)
                self.assertTrue(action.get("repair_status"), action)

    def test_manifest_covers_sales_and_procurement_current_surfaces(self):
        sales_keys = route_keys_by_workspace("sales")
        procurement_keys = route_keys_by_workspace("procurement")
        for expected in {
            "sales-console-worklist/quotation_directory",
            "sales-console-worklist/sales_order_directory",
            "sales-console-worklist/customer_detail/<customer>",
            "sales-console-worklist/customer_editor",
            "sales-console-worklist/item_detail/<item>",
            "sales-console-report/sales_order_analysis",
            "Form/Sales Order",
        }:
            self.assertIn(expected, sales_keys)
        for expected in {
            "procurement-console-worklist/purchase_request_directory",
            "procurement-console-worklist/rfq_directory",
            "procurement-console-worklist/supplier_quotation_directory",
            "procurement-console-report",
            "procurement-console-report/supplier_quotation_comparison",
            "procurement-console-report/purchase_order_analysis",
            "procurement-console-report/demand_to_order_coverage",
            "procurement-console-report/item_purchase_history",
            "procurement-console-po-follow-up",
            "procurement-console-purchase-request-review",
            "procurement-console-purchase-request-form",
            "procurement-console-rfq-form",
            "procurement-console-supplier-quotation-form",
            "procurement-console-purchase-order-form",
        }:
            self.assertIn(expected, procurement_keys)
        self.assertNotIn("Form/Material Request/new-purchase", procurement_keys)


    def test_procurement_managed_purchase_request_actions_are_productized(self):
        actions = {
            item["manifest_key"]: item
            for item in ACTION_MANIFEST
            if item["manifest_key"] in {
                "procurement-new-purchase-request",
                "procurement-worklist-new-purchase-request",
                "procurement-managed-pr-save-draft",
            }
        }

        self.assertEqual("productized_navigation", actions["procurement-new-purchase-request"]["classification"])
        self.assertEqual("page", actions["procurement-new-purchase-request"]["target_kind"])
        self.assertEqual("/desk/procurement-console-purchase-request-form/new", actions["procurement-new-purchase-request"]["target_route_pattern"])
        self.assertEqual("/desk/procurement-console-purchase-request-form/new", actions["procurement-worklist-new-purchase-request"]["target_route_pattern"])
        self.assertEqual("productized_primary_action", actions["procurement-managed-pr-save-draft"]["classification"])
        self.assertNotIn("procurement-managed-pr-open-native", {item["manifest_key"] for item in ACTION_MANIFEST})

    def test_procurement_managed_rfq_output_actions_are_productized(self):
        actions = {
            item["manifest_key"]: item
            for item in ACTION_MANIFEST
            if item["manifest_key"] in {
                "procurement-new-rfq",
                "procurement-worklist-new-rfq",
                "procurement-managed-rfq-save-draft",
                "procurement-managed-rfq-preview-output",
                "procurement-managed-rfq-download-pdf",
                "procurement-managed-rfq-email-blocked",
                "procurement-rfq-review-preview-output",
                "procurement-rfq-review-download-pdf",
                "procurement-rfq-review-recipient-readiness",
                "procurement-rfq-review-email-blocked",
            }
        }

        self.assertEqual("productized_navigation", actions["procurement-new-rfq"]["classification"])
        self.assertEqual("/desk/procurement-console-rfq-form/new", actions["procurement-new-rfq"]["target_route_pattern"])
        self.assertEqual("/desk/procurement-console-rfq-form/new", actions["procurement-worklist-new-rfq"]["target_route_pattern"])
        self.assertEqual("productized_primary_action", actions["procurement-managed-rfq-save-draft"]["classification"])
        self.assertNotIn("procurement-managed-rfq-open-native", {item["manifest_key"] for item in ACTION_MANIFEST})
        self.assertEqual("productized_secondary_action", actions["procurement-managed-rfq-preview-output"]["classification"])
        self.assertEqual("controlled_pdf_endpoint", actions["procurement-managed-rfq-download-pdf"]["target_kind"])
        self.assertEqual("disabled", actions["procurement-managed-rfq-email-blocked"]["target_kind"])
        self.assertEqual("productized_secondary_action", actions["procurement-rfq-review-preview-output"]["classification"])
        self.assertEqual("controlled_pdf_endpoint", actions["procurement-rfq-review-download-pdf"]["target_kind"])
        self.assertEqual("productized_secondary_action", actions["procurement-rfq-review-recipient-readiness"]["classification"])
        self.assertEqual("disabled", actions["procurement-rfq-review-email-blocked"]["target_kind"])

    def test_procurement_managed_supplier_quotation_actions_are_productized(self):
        actions = {
            item["manifest_key"]: item
            for item in ACTION_MANIFEST
            if item["manifest_key"] in {
                "procurement-new-supplier-quotation",
                "procurement-worklist-new-supplier-quotation",
                "procurement-managed-sq-save-draft",
            }
        }

        self.assertEqual("productized_navigation", actions["procurement-new-supplier-quotation"]["classification"])
        self.assertEqual("page", actions["procurement-new-supplier-quotation"]["target_kind"])
        self.assertEqual("/desk/procurement-console-supplier-quotation-form/new", actions["procurement-new-supplier-quotation"]["target_route_pattern"])
        self.assertEqual("/desk/procurement-console-supplier-quotation-form/new", actions["procurement-worklist-new-supplier-quotation"]["target_route_pattern"])
        self.assertEqual("productized_primary_action", actions["procurement-managed-sq-save-draft"]["classification"])
        self.assertNotIn("procurement-managed-sq-open-native", {item["manifest_key"] for item in ACTION_MANIFEST})

    def test_procurement_managed_purchase_order_output_actions_are_productized(self):
        actions = {
            item["manifest_key"]: item
            for item in ACTION_MANIFEST
            if item["manifest_key"] in {
                "procurement-new-purchase-order",
                "procurement-worklist-new-purchase-order",
                "procurement-managed-po-save-draft",
                "procurement-managed-po-preview-output",
                "procurement-managed-po-download-pdf",
                "procurement-managed-po-email-blocked",
            }
        }

        self.assertEqual("productized_navigation", actions["procurement-new-purchase-order"]["classification"])
        self.assertEqual("/desk/procurement-console-purchase-order-form/new", actions["procurement-new-purchase-order"]["target_route_pattern"])
        self.assertEqual("/desk/procurement-console-purchase-order-form/new", actions["procurement-worklist-new-purchase-order"]["target_route_pattern"])
        self.assertEqual("productized_primary_action", actions["procurement-managed-po-save-draft"]["classification"])
        self.assertNotIn("procurement-managed-po-open-native", {item["manifest_key"] for item in ACTION_MANIFEST})
        self.assertEqual("productized_secondary_action", actions["procurement-managed-po-preview-output"]["classification"])
        self.assertEqual("controlled_pdf_endpoint", actions["procurement-managed-po-download-pdf"]["target_kind"])
        self.assertEqual("disabled", actions["procurement-managed-po-email-blocked"]["target_kind"])

    def test_procurement_reports_index_card_action_is_productized_navigation(self):
        actions = {
            item["manifest_key"]: item
            for item in ACTION_MANIFEST
            if item["manifest_key"] in {
                "procurement-report-index-open-quote-comparison",
                "procurement-report-index-open-purchase-order-analysis",
                "procurement-report-index-open-demand-coverage",
                "procurement-report-index-open-item-purchase-history",
            }
        }

        quote_action = actions["procurement-report-index-open-quote-comparison"]
        self.assertEqual("procurement", quote_action["workspace_id"])
        self.assertEqual("procurement-console-report", quote_action["source_route"])
        self.assertEqual("open_supplier_quotation_comparison", quote_action["action_key"])
        self.assertEqual("productized_navigation", quote_action["classification"])
        self.assertEqual("report_page", quote_action["target_kind"])
        self.assertEqual(
            "/desk/procurement-console-report/supplier-quotation-comparison",
            quote_action["target_route_pattern"],
        )
        self.assertIsNone(quote_action.get("native_exception_ref"))

        po_action = actions["procurement-report-index-open-purchase-order-analysis"]
        self.assertEqual("open_purchase_order_analysis", po_action["action_key"])
        self.assertEqual("productized_navigation", po_action["classification"])
        self.assertEqual("report_page", po_action["target_kind"])
        self.assertEqual(
            "/desk/procurement-console-report/purchase-order-analysis",
            po_action["target_route_pattern"],
        )
        self.assertIsNone(po_action.get("native_exception_ref"))

        demand_action = actions["procurement-report-index-open-demand-coverage"]
        self.assertEqual("open_demand_to_order_coverage", demand_action["action_key"])
        self.assertEqual("productized_navigation", demand_action["classification"])
        self.assertEqual("report_page", demand_action["target_kind"])
        self.assertEqual(
            "/desk/procurement-console-report/demand-to-order-coverage",
            demand_action["target_route_pattern"],
        )
        self.assertIsNone(demand_action.get("native_exception_ref"))

        item_history_action = actions["procurement-report-index-open-item-purchase-history"]
        self.assertEqual("open_item_purchase_history", item_history_action["action_key"])
        self.assertEqual("productized_navigation", item_history_action["classification"])
        self.assertEqual("report_page", item_history_action["target_kind"])
        self.assertEqual(
            "/desk/procurement-console-report/item-purchase-history",
            item_history_action["target_route_pattern"],
        )
        self.assertIsNone(item_history_action.get("native_exception_ref"))

    def test_procurement_purchase_order_analysis_drilldowns_are_productized(self):
        action = next(
            item
            for item in ACTION_MANIFEST
            if item["manifest_key"] == "procurement-report-purchase-order-analysis-drilldown"
        )

        self.assertEqual("procurement", action["workspace_id"])
        self.assertEqual("procurement-console-report/purchase_order_analysis", action["source_route"])
        self.assertEqual("productized_navigation", action["classification"])
        self.assertEqual("page", action["target_kind"])
        self.assertEqual("/desk/procurement-console-*", action["target_route_pattern"])
        self.assertIsNone(action.get("native_exception_ref"))

    def test_procurement_demand_coverage_drilldowns_are_productized(self):
        action = next(
            item
            for item in ACTION_MANIFEST
            if item["manifest_key"] == "procurement-report-demand-coverage-drilldown"
        )

        self.assertEqual("procurement", action["workspace_id"])
        self.assertEqual("procurement-console-report/demand_to_order_coverage", action["source_route"])
        self.assertEqual("productized_navigation", action["classification"])
        self.assertEqual("page", action["target_kind"])
        self.assertEqual("/desk/procurement-console-*", action["target_route_pattern"])
        self.assertIsNone(action.get("native_exception_ref"))

    def test_procurement_item_purchase_history_drilldowns_are_productized(self):
        action = next(
            item
            for item in ACTION_MANIFEST
            if item["manifest_key"] == "procurement-report-item-purchase-history-drilldown"
        )

        self.assertEqual("procurement", action["workspace_id"])
        self.assertEqual("procurement-console-report/item_purchase_history", action["source_route"])
        self.assertEqual("productized_navigation", action["classification"])
        self.assertEqual("page", action["target_kind"])
        self.assertEqual("/desk/procurement-console-*", action["target_route_pattern"])
        self.assertIsNone(action.get("native_exception_ref"))


if __name__ == "__main__":
    unittest.main()
