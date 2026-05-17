from __future__ import annotations

import frappe


SALES_CONSOLE_PAGE = "sales-console"
SALES_HOME_ROLES = {
	"Sales Manager",
	"Sales User",
	"Sales Master Manager",
	"Sales Executive",
	"Key Account Sales",
}


def set_sales_home_page(bootinfo) -> None:
	if frappe.session.user == "Guest":
		return

	user_roles = set(frappe.get_roles(frappe.session.user))
	if not user_roles.intersection(SALES_HOME_ROLES):
		return

	if not frappe.db.exists("Page", SALES_CONSOLE_PAGE):
		return

	try:
		page = frappe.desk.desk_page.get(SALES_CONSOLE_PAGE)
	except (frappe.DoesNotExistError, frappe.PermissionError):
		frappe.clear_last_message()
		return

	bootinfo["home_page"] = SALES_CONSOLE_PAGE
	docs = bootinfo.get("docs") or []
	if not any(getattr(doc, "doctype", None) == "Page" and getattr(doc, "name", None) == SALES_CONSOLE_PAGE for doc in docs):
		docs.append(page)
		bootinfo["docs"] = docs
