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
from erp_workspace_ui.workspace_registry import get_procurement_workspace_definition, get_sales_workspace_definition


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

    def test_productized_pages_do_not_declare_generic_native_primary_row_actions(self):
        for action in ACTION_MANIFEST:
            action_key = str(action.get("action_key") or "")
            source_route = str(action.get("source_route") or "")
            label = str(action.get("label") or action.get("label_pattern") or "")
            if action_key == "open_erp_form" or label == "Open ERP Form":
                self.assertEqual("governed_native_action", action["classification"], action)
                self.assertEqual("procurement-secondary-native-open-v1", action.get("native_exception_ref"), action)
                self.assertNotIn("worklist/*", source_route, action)
                self.assertIn("Secondary", str(action.get("notes") or ""), action)
            if action_key == "row:*:open_record" and source_route.startswith("procurement-console-worklist"):
                self.assertEqual("productized_navigation", action["classification"], action)
                self.assertNotEqual("form", action.get("target_kind"), action)

    def test_forbidden_mutation_labels_are_listed_and_guarded(self):
        required = {"Submit", "Cancel", "Amend", "Approve", "Reject", "Receive", "Bill", "Pay", "Set Default Supplier", "Update Item Price", "Delete"}
        self.assertTrue(required.issubset(set(FORBIDDEN_MUTATION_LABELS)))
        guarded_workspaces = {guard["workspace_id"] for guard in FORBIDDEN_MUTATION_GUARDS}
        self.assertEqual({"sales", "procurement"}, guarded_workspaces)
        for guard in FORBIDDEN_MUTATION_GUARDS:
            self.assertEqual(set(FORBIDDEN_MUTATION_LABELS), set(guard["labels"]), guard)
            self.assertIn("native-exception-policy-v1.md", guard["policy_doc"], guard)

    def test_registry_route_keys_exist_in_manifest(self):
        sales_routes = get_sales_workspace_definition()["routes"]
        procurement_routes = get_procurement_workspace_definition()["routes"]
        sales_manifest_keys = route_keys_by_workspace("sales")
        procurement_manifest_keys = route_keys_by_workspace("procurement")

        for key, value in sales_routes.items():
            if key.endswith("_path"):
                continue
            self.assertIn(value, sales_manifest_keys, key)
        for key, value in procurement_routes.items():
            if key.endswith("_path"):
                continue
            self.assertIn(value, procurement_manifest_keys, key)

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
            "procurement-console-po-follow-up",
            "procurement-console-purchase-request-review",
            "Form/Material Request/new-purchase",
        }:
            self.assertIn(expected, procurement_keys)


if __name__ == "__main__":
    unittest.main()
