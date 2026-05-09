from __future__ import annotations

from pathlib import Path
import unittest

from erp_workspace_ui.workspace_governance_manifest import (
    ACTION_MANIFEST,
    NATIVE_EXCEPTION_POLICIES,
    ROUTE_MANIFEST,
)
from erp_workspace_ui.workspace_registry import get_sales_workspace_definition, get_workspace_by_route


APP_ROOT = Path(__file__).resolve().parents[1]
DOC_ROOT = APP_ROOT.parent / "_docs" / "erp-ui-customization"

PROTECTED_WORKLIST_ROUTES = {
    "sales-console-worklist/quotation_directory",
    "sales-console-worklist/quotations_waiting_action",
    "sales-console-worklist/quotations_awaiting_approval",
    "sales-console-worklist/expiring_quotations",
    "sales-console-worklist/sales_order_directory",
    "sales-console-worklist/open_orders",
    "sales-console-worklist/sales_orders_pending_fulfillment",
    "sales-console-worklist/partially_delivered_orders",
    "sales-console-worklist/orders_due_soon",
    "sales-console-worklist/orders_blocked_by_approval",
    "sales-console-worklist/customer_follow_up_tasks",
    "sales-console-worklist/invoices_outstanding",
    "sales-console-worklist/sales_returns_in_progress",
    "sales-console-worklist/customer_directory",
    "sales-console-worklist/customer_detail/<customer>",
    "sales-console-worklist/customer_editor",
    "sales-console-worklist/customer_editor/<customer>",
    "sales-console-worklist/item_directory",
    "sales-console-worklist/item_detail/<item>",
}

PROTECTED_REPORT_ROUTES = {
    "sales-console-report/sales_analytics",
    "sales-console-report/sales_order_analysis",
    "sales-console-report/trend_analysis",
    "sales-console-report/quotation_trends",
    "sales-console-report/lost_quotations",
    "sales-console-report/collections_status",
    "sales-console-report/payment_terms_status_sales_order",
    "sales-console-report/item_wise_sales_history",
}

PROTECTED_NATIVE_FORM_ROUTES = {
    "Form/Quotation",
    "Form/Sales Order",
    "Form/Delivery Note",
    "Form/Sales Invoice",
}

REQUIRED_SALES_ACTIONS = {
    "sales-overview-new-quotation",
    "sales-overview-new-sales-order",
    "sales-overview-open-customer",
    "sales-overview-open-item",
    "sales-overview-queue-card-navigation",
    "sales-overview-report-shortcut-navigation",
    "sales-worklist-refresh",
    "sales-worklist-reset",
    "sales-worklist-apply",
    "sales-report-apply",
    "sales-report-reset",
    "sales-report-refresh",
    "sales-report-back",
    "sales-report-row-drilldown",
    "sales-document-row-open",
    "sales-profile-row-open",
    "sales-customer-detail-managed-document-open",
    "sales-new-quotation",
    "sales-new-sales-order",
    "sales-create-customer",
    "sales-edit-customer",
    "sales-back-customers",
    "sales-back-items",
    "sales-managed-form-native-lifecycle",
}


class TestSalesFreezeProtectionContract(unittest.TestCase):
    def sales_routes(self):
        return {route["route_key"]: route for route in ROUTE_MANIFEST if route["workspace_id"] == "sales"}

    def sales_actions(self):
        return {action["manifest_key"]: action for action in ACTION_MANIFEST if action["workspace_id"] == "sales"}

    def test_sales_freeze_v2_package_is_the_current_protection_baseline(self):
        package = (DOC_ROOT / "sales-console-frozen-protection-package-2026-05-09.md").read_text()

        self.assertIn("Freeze marker tag: `sales-console-freeze-v2`", package)
        self.assertIn("Status: Frozen and protected", package)
        self.assertIn("Previous historical freeze tag: `sales-console-freeze-v1`", package)
        self.assertIn("must not be treated as the current protected baseline", package)

    def test_sales_registry_entry_owns_canonical_workspace_routes(self):
        workspace = get_sales_workspace_definition()

        self.assertEqual("sales", workspace["workspace_id"])
        self.assertEqual("frozen", workspace["status"])
        self.assertEqual(
            {
                "launcher": "sales-console-home",
                "launcher_path": "/desk/sales-console-home",
                "home": "sales-console",
                "home_path": "/desk/sales-console",
                "worklist": "sales-console-worklist",
                "report": "sales-console-report",
            },
            workspace["routes"],
        )

        for route_key in ("sales-console-home", "sales-console", "sales-console-worklist", "sales-console-report"):
            with self.subTest(route_key=route_key):
                resolved = get_workspace_by_route(route_key)
                self.assertIsNotNone(resolved)
                self.assertEqual("sales", resolved["workspace_id"])

    def test_sales_protected_routes_are_manifested(self):
        routes = self.sales_routes()
        required_routes = {
            "sales-console-home",
            "sales-console",
            "sales-console-worklist",
            "sales-console-report",
            *PROTECTED_WORKLIST_ROUTES,
            *PROTECTED_REPORT_ROUTES,
            *PROTECTED_NATIVE_FORM_ROUTES,
        }

        self.assertTrue(required_routes.issubset(routes.keys()), sorted(required_routes - routes.keys()))

    def test_sales_worklist_and_report_routes_keep_expected_shells(self):
        routes = self.sales_routes()

        for route_key in PROTECTED_WORKLIST_ROUTES:
            with self.subTest(route_key=route_key):
                route = routes[route_key]
                self.assertIn(route["classification"], {"productized_worklist", "productized_detail", "managed_create_edit"})
                self.assertNotIn("procurement", route["route_pattern"])
                self.assertNotEqual("report_page_shell", route["expected_shell"])

        for route_key in PROTECTED_REPORT_ROUTES:
            with self.subTest(route_key=route_key):
                route = routes[route_key]
                self.assertEqual("productized_report", route["classification"])
                self.assertEqual("report_page_shell", route["expected_shell"])
                self.assertNotIn("procurement", route["route_pattern"])

    def test_sales_native_exception_list_matches_freeze_package(self):
        routes = self.sales_routes()
        policy = NATIVE_EXCEPTION_POLICIES["sales-managed-document-forms-v1"]

        self.assertEqual("sales", policy["workspace_id"])
        self.assertEqual("approved_sales_freeze", policy["status"])
        self.assertEqual(
            PROTECTED_NATIVE_FORM_ROUTES,
            {
                route_key
                for route_key, route in routes.items()
                if route.get("native_exception_ref") == "sales-managed-document-forms-v1"
            },
        )
        for route_key in PROTECTED_NATIVE_FORM_ROUTES:
            with self.subTest(route_key=route_key):
                route = routes[route_key]
                self.assertEqual("managed_create_edit", route["classification"])
                self.assertEqual("child_page_managed_form", route["expected_shell"])

    def test_sales_actions_are_classified_and_safe_for_frozen_surfaces(self):
        actions = self.sales_actions()

        self.assertTrue(REQUIRED_SALES_ACTIONS.issubset(actions.keys()), sorted(REQUIRED_SALES_ACTIONS - actions.keys()))
        for action in actions.values():
            with self.subTest(action=action["manifest_key"]):
                self.assertNotEqual("not_allowed_leakage", action["classification"])
                self.assertNotIn("procurement", str(action.get("target_route_pattern") or ""))
                if action["classification"] == "governed_native_action":
                    self.assertEqual("sales-managed-document-forms-v1", action.get("native_exception_ref"))
                if action["target_kind"] in {"new_doc", "managed_form", "native_form_lifecycle"}:
                    self.assertEqual("sales-managed-document-forms-v1", action.get("native_exception_ref"))

    def test_sales_worklist_filter_commands_remain_in_place_shell_actions(self):
        actions = self.sales_actions()
        for manifest_key, classification in {
            "sales-worklist-apply": "productized_primary_action",
            "sales-worklist-reset": "productized_secondary_action",
            "sales-worklist-refresh": "productized_secondary_action",
        }.items():
            with self.subTest(action=manifest_key):
                action = actions[manifest_key]
                self.assertEqual("sales-console-worklist/*", action["source_route"])
                self.assertEqual(classification, action["classification"])
                self.assertEqual("current_shell", action["target_kind"])

    def test_sales_report_command_order_is_manifested(self):
        ordered = [
            action["action_key"]
            for action in ACTION_MANIFEST
            if action["workspace_id"] == "sales"
            and action["source_route"] == "sales-console-report/*"
            and action["target_kind"] in {"current_shell", "page"}
        ]

        self.assertEqual(["apply_filters", "reset_filters", "refresh", "back_to_console"], ordered)

    def test_sales_routes_are_not_accidentally_mapped_to_procurement_or_generic_workspaces(self):
        for route in self.sales_routes().values():
            with self.subTest(route=route["route_key"]):
                self.assertEqual("sales", route["owning_adapter"])
                self.assertNotIn("procurement-console", route["route_pattern"])
                self.assertNotIn("generic", route["route_key"])


if __name__ == "__main__":
    unittest.main()
