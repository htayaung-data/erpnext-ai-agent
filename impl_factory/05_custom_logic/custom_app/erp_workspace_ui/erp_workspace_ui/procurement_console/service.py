from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

from erp_workspace_ui.workspace_registry import get_procurement_workspace_definition


PROCUREMENT_ROLES = frozenset({"Purchase User", "Purchase Manager", "Purchase Master Manager"})


def ensure_authenticated() -> None:
	if getattr(frappe.session, "user", None) == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)


def current_user_roles(user: str | None = None) -> set[str]:
	try:
		return set(frappe.get_roles(user or getattr(frappe.session, "user", None)))
	except Exception:
		return set()


def has_procurement_access(context: dict[str, object] | None = None) -> bool:
	if context and "roles" in context:
		roles = set(context.get("roles") or [])
	else:
		roles = current_user_roles()
	return bool(roles.intersection(PROCUREMENT_ROLES))


def build_context() -> dict[str, object]:
	roles = sorted(current_user_roles())
	return {
		"user": getattr(frappe.session, "user", None),
		"roles": roles,
		"role_family": "Procurement",
		"role_variant": _role_variant(roles),
		"has_procurement_access": bool(set(roles).intersection(PROCUREMENT_ROLES)),
	}


def _role_variant(roles: list[str]) -> str:
	role_set = set(roles)
	if "Purchase Master Manager" in role_set:
		return "purchase_master_manager"
	if "Purchase Manager" in role_set:
		return "purchase_manager"
	if "Purchase User" in role_set:
		return "purchase_user"
	return "restricted"


def procurement_workspace_public_context() -> dict[str, object]:
	workspace = get_procurement_workspace_definition()
	return {
		"workspace_id": workspace.get("workspace_id"),
		"status": workspace.get("status"),
		"title": workspace.get("title"),
		"mode_label": workspace.get("mode_label"),
		"role_family": workspace.get("role_family"),
		"routes": workspace.get("routes"),
		"methods": workspace.get("methods"),
		"sidebar": workspace.get("sidebar"),
	}


def state(kind: str, title: str, detail: str) -> dict[str, str]:
	return {
		"kind": kind,
		"title": title,
		"detail": detail,
	}


def restricted_state() -> dict[str, str]:
	return state(
		"restricted",
		"Procurement Console is restricted",
		"This workspace is available only to procurement roles.",
	)


def unavailable_state() -> dict[str, str]:
	return state(
		"unavailable",
		"Procurement Console is not available yet",
		"The workspace foundation is ready, but buyer workbench pages are not enabled yet.",
	)


def build_sidebar(context: dict[str, object] | None = None) -> dict[str, object]:
	workspace = get_procurement_workspace_definition()
	sidebar = workspace.get("sidebar") or {}
	items = list(workspace.get("fallback_items") or [])
	return {
		"workspace_id": workspace.get("workspace_id"),
		"active_key": sidebar.get("home_key") or "procurement_console_home",
		"home_key": sidebar.get("home_key") or "procurement_console_home",
		"items": items,
		"sections": [
			{
				"key": sidebar.get("section_key") or "workspace",
				"label": sidebar.get("section_label") or "Workspace",
				"items": items,
			}
		],
		"state": restricted_state() if context and not has_procurement_access(context) else unavailable_state(),
	}


def _base_payload(context: dict[str, object], payload_state: dict[str, str]) -> dict[str, object]:
	return {
		"workspace": procurement_workspace_public_context(),
		"context": context,
		"scope": {
			"scope_mode": "procurement_role_scope" if has_procurement_access(context) else "restricted",
			"default_routing_enabled": False,
		},
		"state": payload_state,
		"navigation": {
			"items": list(get_procurement_workspace_definition().get("fallback_items") or []),
		},
		"sidebar": build_sidebar(context),
		"queues": [],
		"reports_catalog": [],
		"fetched_at": str(now_datetime()),
	}


@frappe.whitelist()
def get_procurement_console_bootstrap() -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	if not has_procurement_access(context):
		return _base_payload(context, restricted_state())
	return _base_payload(context, unavailable_state())


@frappe.whitelist()
def get_procurement_console_sidebar_context() -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	payload_state = unavailable_state() if has_procurement_access(context) else restricted_state()
	return {
		"workspace": procurement_workspace_public_context(),
		"context": context,
		"scope": {
			"scope_mode": "procurement_role_scope" if has_procurement_access(context) else "restricted",
			"default_routing_enabled": False,
		},
		"state": payload_state,
		"sidebar": build_sidebar(context),
		"fetched_at": str(now_datetime()),
	}


@frappe.whitelist()
def search_procurement_console_workspace(query: str, limit: int = 12) -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	needle = (query or "").strip()
	if not has_procurement_access(context):
		return {
			"state": "restricted",
			"query": needle,
			"message": "Procurement Console search is restricted to procurement roles.",
			"results": [],
		}
	return {
		"state": "unavailable",
		"query": needle,
		"message": "Procurement Console search is not available yet.",
		"results": [],
		"limit": limit,
	}
