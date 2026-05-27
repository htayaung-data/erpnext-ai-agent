from __future__ import annotations

import frappe


ERP_WORKSPACE_UI_APP = "erp_workspace_ui"
SALES_CONSOLE_APP = ERP_WORKSPACE_UI_APP
SALES_CONSOLE_ROUTE = "/desk/sales-console"
SALES_CONSOLE_APP_HOME = "/desk/sales-console-home"
SALES_CONSOLE_HOME_PAGE = "sales-console-home"
PROCUREMENT_CONSOLE_HOME_PAGE = "procurement-console-home"
WAREHOUSE_CONSOLE_HOME_PAGE = "warehouse-console"
DEFAULT_APP_EXCLUDED_USERS = {"Administrator"}
SALES_CONSOLE_ROLES = frozenset({"Sales Manager", "Sales User", "Sales Master Manager", "Sales Executive", "Key Account Sales"})
PROCUREMENT_CONSOLE_ROLES = frozenset({"Purchase User", "Purchase Manager", "Purchase Master Manager"})
WAREHOUSE_CONSOLE_ROLES = frozenset({"Warehouse Manager", "Warehouse User", "Stock Manager", "Stock User"})
WAREHOUSE_CONSOLE_BLOCKING_ROLES = SALES_CONSOLE_ROLES | PROCUREMENT_CONSOLE_ROLES | frozenset(
	{
		"System Manager",
		"Accounts Manager",
		"Accounts User",
		"Finance Manager",
		"Finance User",
		"HR Manager",
		"HR User",
		"Manufacturing Manager",
		"Manufacturing User",
		"Projects Manager",
		"Projects User",
		"Report Manager",
		"Workspace Manager",
	}
)
DEFAULT_APP_RULES = (
	(SALES_CONSOLE_APP, SALES_CONSOLE_ROLES),
)
DEFAULT_HOME_PAGE_RULES = (
	(SALES_CONSOLE_HOME_PAGE, SALES_CONSOLE_ROLES),
	(PROCUREMENT_CONSOLE_HOME_PAGE, PROCUREMENT_CONSOLE_ROLES),
)
MANAGED_DEFAULT_APPS = {app_name for app_name, _roles in DEFAULT_APP_RULES}
MANAGED_DESK_HOME_PAGES = {
	"sales-console",
	"sales-console-home",
	"procurement-console",
	"procurement-console-home",
	"warehouse-console",
}


def _current_user_roles(user: str) -> set[str]:
	try:
		return set(frappe.get_roles(user))
	except Exception:
		return set()


def resolve_default_app(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if not user or user == "Guest":
		return None

	if user in DEFAULT_APP_EXCLUDED_USERS:
		return None

	user_roles = _current_user_roles(user)
	for app_name, roles in DEFAULT_APP_RULES:
		if user_roles.intersection(roles):
			return app_name

	return None


def should_use_warehouse_console_home(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if not user or user == "Guest" or user in DEFAULT_APP_EXCLUDED_USERS:
		return False

	user_roles = _current_user_roles(user)
	return bool(user_roles.intersection(WAREHOUSE_CONSOLE_ROLES)) and not bool(
		user_roles.intersection(WAREHOUSE_CONSOLE_BLOCKING_ROLES)
	)


def resolve_default_home_page(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if not user or user == "Guest":
		return None

	if user in DEFAULT_APP_EXCLUDED_USERS:
		return None

	user_roles = _current_user_roles(user)
	for home_page, roles in DEFAULT_HOME_PAGE_RULES:
		if user_roles.intersection(roles):
			return home_page

	if should_use_warehouse_console_home(user):
		return WAREHOUSE_CONSOLE_HOME_PAGE

	return None


def can_use_sales_console_app() -> bool:
	return resolve_default_app() == SALES_CONSOLE_APP


def _get_current_user_default_app(user: str) -> str | None:
	return frappe.db.get_value("User", user, "default_app")


def _clear_stale_desktop_home_page(user: str) -> None:
	current_desktop_home = frappe.db.get_value(
		"DefaultValue",
		{"parent": user, "defkey": "desktop:home_page"},
		"defvalue",
	)
	if current_desktop_home in MANAGED_DESK_HOME_PAGES:
		frappe.defaults.clear_user_default("desktop:home_page", user=user)


def _sync_desktop_home_page(user: str, desired_page: str | None) -> None:
	current_desktop_home = frappe.db.get_value(
		"DefaultValue",
		{"parent": user, "defkey": "desktop:home_page"},
		"defvalue",
	)

	if desired_page:
		if current_desktop_home != desired_page:
			frappe.defaults.set_user_default("desktop:home_page", desired_page, user=user)
		return

	_clear_stale_desktop_home_page(user)


def sync_current_user_default_app(_login_manager=None) -> None:
	user = frappe.session.user if frappe.session else None
	if not user or user == "Guest":
		return

	desired_app = resolve_default_app(user)
	desired_home_page = resolve_default_home_page(user)
	current_app = _get_current_user_default_app(user)

	if desired_app:
		if current_app != desired_app:
			frappe.db.set_value("User", user, "default_app", desired_app, update_modified=False)
	else:
		if current_app in MANAGED_DEFAULT_APPS:
			frappe.db.set_value("User", user, "default_app", "", update_modified=False)

	_sync_desktop_home_page(user, desired_home_page)


def sync_managed_default_apps() -> dict[str, str | None]:
	updated: dict[str, str | None] = {}
	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User"},
		pluck="name",
	)

	for user in users:
		desired_app = resolve_default_app(user)
		desired_home_page = resolve_default_home_page(user)
		current_app = _get_current_user_default_app(user)

		if desired_app:
			if current_app != desired_app:
				frappe.db.set_value("User", user, "default_app", desired_app, update_modified=False)
				updated[user] = desired_app
		else:
			if current_app in MANAGED_DEFAULT_APPS:
				frappe.db.set_value("User", user, "default_app", "", update_modified=False)
				updated[user] = None

		_sync_desktop_home_page(user, desired_home_page)

	return updated


def apply_role_based_boot_home(bootinfo) -> None:
	"""Set the first Desk page from role policy, not only global defaults.

	Frappe's native boot path resolves ``boot.home_page`` from the global
	``desktop:home_page`` default. That ignores user-specific values, so
	workspace users can land on the wrong role console when the global app home
	points at a different workspace.

	We fix that here at the actual boot payload level, which is the value Desk
	uses on first render when the route is plain ``/desk``.
	"""

	user = frappe.session.user if frappe.session else None
	if not user or user == "Guest":
		return

	home_page = resolve_default_home_page(user)
	if home_page:
		bootinfo["home_page"] = home_page
