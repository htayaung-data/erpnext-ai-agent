app_name = "erp_workspace_ui"
app_title = "ERP Workspace UI"
app_publisher = "MEET"
app_description = "Enterprise ERPNext workspace and console UX"
app_email = "htayaung.data@gmail.com"
app_license = "mit"
app_home = "/desk/sales-console-home"

# This app owns UI workspace and page surfaces for the UI workstream.
# AI runtime and governed assistant orchestration remain in the assistant app.

# required_apps = []

app_include_css = "/assets/erp_workspace_ui/css/erp_workspace_ui.css"
app_include_js = [
	"/assets/erp_workspace_ui/js/erp_workspace_ui_boot.js",
	"/assets/erp_workspace_ui/js/runtime/console/workspace_console_runtime.js",
	"/assets/erp_workspace_ui/js/runtime/child_page/child_page_helpers.js",
	"/assets/erp_workspace_ui/js/runtime/child_page/child_page_sections.js",
	"/assets/erp_workspace_ui/js/runtime/child_page/child_page_details.js",
	"/assets/erp_workspace_ui/js/runtime/child_page/child_page_terms.js",
	"/assets/erp_workspace_ui/js/runtime/child_page/child_page_summaries.js",
	"/assets/erp_workspace_ui/js/runtime/child_page/child_page_observability.js",
	"/assets/erp_workspace_ui/js/runtime/child_page/child_page_shell.js",
	"/assets/erp_workspace_ui/js/runtime/child_page/child_page_shell_content.js",
	"/assets/erp_workspace_ui/js/runtime/child_page/child_page_runtime.js",
	"/assets/erp_workspace_ui/js/runtime/child_page/child_page_connections.js",
	"/assets/erp_workspace_ui/js/runtime/child_page/child_page_support.js",
	"/assets/erp_workspace_ui/js/runtime/child_page/child_page_sidebar.js",
]
doctype_js = {
	"Sales Order": "public/js/sales_order_form.js",
	"Quotation": "public/js/quotation_form.js",
	"Delivery Note": "public/js/delivery_note_form.js",
	"Sales Invoice": "public/js/sales_invoice_form.js",
}
on_session_creation = ["erp_workspace_ui.boot.sync_current_user_default_app"]
boot_session = ["erp_workspace_ui.boot.apply_role_based_boot_home"]

add_to_apps_screen = [
	{
		"name": app_name,
		"logo": "/assets/erp_workspace_ui/images/sales-console-logo.svg",
		"title": "Sales Console",
		"route": app_home,
		"has_permission": "erp_workspace_ui.boot.can_use_sales_console_app",
	}
]

# page_js = {"page": "public/js/file.js"}

# before_install = "erp_workspace_ui.install.before_install"
# after_install = "erp_workspace_ui.install.after_install"

# notification_config = "erp_workspace_ui.notifications.get_notification_config"

# before_tests = "erp_workspace_ui.install.before_tests"

# Sales-role landing is handled through the native Desk boot home page.
# Sales users first resolve to the launcher page, which then hands off to the
# real Sales Console page without colliding with the page route itself.
