from __future__ import annotations

import frappe


SALES_CONSOLE_APP = "erp_workspace_ui"
SALES_CONSOLE_ROUTE = "/desk/sales-console"
SALES_CONSOLE_APP_HOME = "/desk/sales-console-home"
SALES_CONSOLE_HOME_PAGE = "sales-console-home"
DEFAULT_APP_EXCLUDED_USERS = {"Administrator"}
DEFAULT_APP_RULES = (
	(SALES_CONSOLE_APP, {"Sales Manager", "Sales User", "Sales Master Manager", "Sales Executive", "Key Account Sales"}),
)
MANAGED_DEFAULT_APPS = {app_name for app_name, _roles in DEFAULT_APP_RULES}
MANAGED_DESK_HOME_PAGES = {"sales-console", "sales-console-home"}


def resolve_default_app(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if not user or user == "Guest":
		return None

	if user in DEFAULT_APP_EXCLUDED_USERS:
		return None

	user_roles = set(frappe.get_roles(user))
	for app_name, roles in DEFAULT_APP_RULES:
		if user_roles.intersection(roles):
			return app_name

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
	current_app = _get_current_user_default_app(user)

	if desired_app:
		if current_app != desired_app:
			frappe.db.set_value("User", user, "default_app", desired_app, update_modified=False)
		_sync_desktop_home_page(user, SALES_CONSOLE_HOME_PAGE)
		return

	if current_app in MANAGED_DEFAULT_APPS:
		frappe.db.set_value("User", user, "default_app", "", update_modified=False)
	_sync_desktop_home_page(user, None)


def sync_managed_default_apps() -> dict[str, str | None]:
	updated: dict[str, str | None] = {}
	users = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User"},
		pluck="name",
	)

	for user in users:
		desired_app = resolve_default_app(user)
		current_app = _get_current_user_default_app(user)

		if desired_app:
			if current_app != desired_app:
				frappe.db.set_value("User", user, "default_app", desired_app, update_modified=False)
				updated[user] = desired_app
			_sync_desktop_home_page(user, SALES_CONSOLE_HOME_PAGE)
			continue

		if current_app in MANAGED_DEFAULT_APPS:
			frappe.db.set_value("User", user, "default_app", "", update_modified=False)
			updated[user] = None
		_sync_desktop_home_page(user, None)

	return updated


def apply_role_based_boot_home(bootinfo) -> None:
	"""Set the first Desk page from role policy, not only global defaults.

	Frappe's native boot path resolves ``boot.home_page`` from the global
	``desktop:home_page`` default. That ignores user-specific values, so sales
	users would still land on the generic workspace desktop even when their
	per-user defaults were correct.

	We fix that here at the actual boot payload level, which is the value Desk
	uses on first render when the route is plain ``/desk``.
	"""

	user = frappe.session.user if frappe.session else None
	if not user or user == "Guest":
		return

	if resolve_default_app(user) == SALES_CONSOLE_APP:
		bootinfo["home_page"] = SALES_CONSOLE_HOME_PAGE
