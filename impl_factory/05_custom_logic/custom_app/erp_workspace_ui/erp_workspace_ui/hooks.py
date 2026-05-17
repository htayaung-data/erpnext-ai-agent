app_name = "erp_workspace_ui"
app_title = "ERP Workspace UI"
app_publisher = "MEET"
app_description = "Enterprise ERPNext workspace and console UX"
app_email = "htayaung.data@gmail.com"
app_license = "mit"

# This app owns UI workspace and page surfaces for the UI workstream.
# AI runtime and governed assistant orchestration remain in the assistant app.

# required_apps = []

app_include_css = "/assets/erp_workspace_ui/css/erp_workspace_ui.css"
app_include_js = "/assets/erp_workspace_ui/js/erp_workspace_ui_boot.js"
doctype_js = {"Sales Order": "public/js/sales_order_form.js"}

# page_js = {"page": "public/js/file.js"}

# before_install = "erp_workspace_ui.install.before_install"
# after_install = "erp_workspace_ui.install.after_install"

# notification_config = "erp_workspace_ui.notifications.get_notification_config"

# before_tests = "erp_workspace_ui.install.before_tests"

# Keep the console page available, but do not force it during Desk boot.
# A broken custom home page can block all access to the app shell.
# We will reintroduce this hook after the console route is verified end-to-end.
# boot_session = ["erp_workspace_ui.boot.set_sales_home_page"]
