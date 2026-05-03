import unittest

from erp_workspace_ui import hooks
from erp_workspace_ui.workspace_registry import (
    get_active_workspace_definitions,
    get_sales_workspace_definition,
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

        self.assertIsNone(get_workspace_by_route("procurement-console"))

    def test_active_workspace_definitions_are_copy_safe(self):
        workspace = get_workspace_definition("sales")
        workspace["routes"]["home"] = "changed-locally"

        self.assertEqual(get_sales_workspace_definition()["routes"]["home"], "sales-console")
        self.assertEqual(len(get_active_workspace_definitions()), 1)

    def test_roadmap_uses_matrix_names_and_explicit_name_reviews(self):
        roadmap = get_workspace_roadmap()
        matrix_names = [item["matrix_name"] for item in roadmap]

        self.assertEqual(
            matrix_names[:4],
            ["Sales Console", "Procurement Console", "Warehouse Console", "Finance Console"],
        )
        self.assertNotIn("Inventory Console", matrix_names)

        finance = next(item for item in roadmap if item["workspace_id"] == "finance")
        executive = next(item for item in roadmap if item["workspace_id"] == "executive")
        self.assertEqual(finance["recommended_name"], "Finance Control Desk")
        self.assertEqual(finance["status"], "name_review")
        self.assertEqual(executive["recommended_name"], "Management Daily Brief")
        self.assertEqual(executive["status"], "name_review")

    def test_hooks_load_registry_before_shared_boot_runtime(self):
        include_js = list(hooks.app_include_js)

        self.assertEqual(hooks.app_home, "/desk/sales-console-home")
        self.assertEqual(hooks.add_to_apps_screen[0]["title"], "Sales Console")
        self.assertLess(
            include_js.index("/assets/erp_workspace_ui/js/runtime/console/workspace_registry.js"),
            include_js.index("/assets/erp_workspace_ui/js/erp_workspace_ui_boot.js"),
        )


if __name__ == "__main__":
    unittest.main()
