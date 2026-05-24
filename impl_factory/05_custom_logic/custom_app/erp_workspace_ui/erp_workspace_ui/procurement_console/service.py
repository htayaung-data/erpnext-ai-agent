from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

from erp_workspace_ui.workspace_registry import get_procurement_workspace_definition


PROCUREMENT_ROLES = frozenset({"Purchase User", "Purchase Manager", "Purchase Master Manager"})
QUICK_FIND_MIN_QUERY_LENGTH = 2
QUICK_FIND_DEFAULT_LIMIT = 12
QUICK_FIND_MAX_LIMIT = 18
QUICK_FIND_GROUP_ORDER = (
	"suppliers",
	"buying_items",
	"purchase_requests",
	"rfqs",
	"supplier_quotations",
	"purchase_orders",
	"reports",
)
QUICK_FIND_GROUP_LABELS = {
	"suppliers": "Suppliers",
	"buying_items": "Buying Items",
	"purchase_requests": "Purchase Requests",
	"rfqs": "RFQs",
	"supplier_quotations": "Supplier Quotations",
	"purchase_orders": "Purchase Orders",
	"reports": "Reports",
}
QUICK_FIND_REPORTS = (
	{
		"key": "procurement_reports_index",
		"title": "Procurement Reports",
		"description": "Open the governed Procurement report catalog.",
		"boundary": "Productized report index only.",
	},
	{
		"key": "supplier_quotation_comparison",
		"title": "Quote Comparison",
		"description": "Compare supplier offers by price, validity, supplier, item, and RFQ.",
		"boundary": "Read-only sourcing review.",
	},
	{
		"key": "purchase_order_analysis",
		"title": "Purchase Order Analysis",
		"description": "Review ordered value, receiving posture, billing posture, suppliers, and items.",
		"boundary": "Read-only buyer visibility.",
	},
	{
		"key": "demand_to_order_coverage",
		"title": "Demand-to-Order Coverage",
		"description": "Track purchase demand that is ordered, partial, or still open.",
		"boundary": "Read-only demand coverage.",
	},
	{
		"key": "item_purchase_history",
		"title": "Item Purchase History",
		"description": "Review buying history by item, supplier, and order reference.",
		"boundary": "Read-only price review.",
	},
)


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
		"This Procurement Console surface is not available in the current phase.",
	)


def build_sidebar(context: dict[str, object] | None = None) -> dict[str, object]:
	workspace = get_procurement_workspace_definition()
	sidebar = workspace.get("sidebar") or {}
	items = list(workspace.get("fallback_items") or [])
	sidebar_state = state(
		"ready",
		"Procurement Console ready",
		"Buyer workbench queues are available for procurement roles.",
	) if not context or has_procurement_access(context) else restricted_state()
	return {
		"workspace_id": workspace.get("workspace_id"),
		"title": workspace.get("title"),
		"mode_label": workspace.get("mode_label"),
		"scope_label": "Buyer workbench" if not context or has_procurement_access(context) else "Restricted",
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
		"state": sidebar_state,
	}


def _base_payload(context: dict[str, object], payload_state: dict[str, str]) -> dict[str, object]:
	return {
		"workspace": procurement_workspace_public_context(),
		"context": context,
		"scope": {
			"scope_mode": "procurement_role_scope" if has_procurement_access(context) else "restricted",
			"default_routing_enabled": has_procurement_access(context),
		},
		"state": payload_state,
		"navigation": {
			"items": list(get_procurement_workspace_definition().get("fallback_items") or []),
		},
		"sidebar": build_sidebar(context),
		"work": {},
		"directories": {},
		"queues": {},
		"insights": {},
		"reports_catalog": [],
		"create_actions": [],
		"action_targets": {},
		"fetched_at": str(now_datetime()),
	}


@frappe.whitelist()
def get_procurement_console_bootstrap() -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	if not has_procurement_access(context):
		return _base_payload(context, restricted_state())
	payload = _base_payload(context, state(
		"ready",
		"Procurement Console ready",
		"Buyer workbench queues are available for procurement roles.",
	))
	payload.update(_build_phase1_overview())
	payload.update(_build_create_action_payload(context))
	# Manager readiness is intentionally loaded asynchronously by the Overview
	# frontend so the primary workbench is usable before the heavier readiness scan.
	return payload


@frappe.whitelist()
def get_procurement_console_sidebar_context() -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	payload_state = state(
		"ready",
		"Procurement Console ready",
		"Buyer workbench queues are available for procurement roles.",
	) if has_procurement_access(context) else restricted_state()
	return {
		"workspace": procurement_workspace_public_context(),
		"context": context,
		"scope": {
			"scope_mode": "procurement_role_scope" if has_procurement_access(context) else "restricted",
			"default_routing_enabled": has_procurement_access(context),
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
	if len(needle) < 2:
		return {
			"state": "idle",
			"query": needle,
			"message": "Type at least 2 characters to search suppliers, purchase requests, RFQs, quotations, and purchase orders.",
			"results": [],
		}

	results = _build_procurement_workspace_search_results(needle, limit)
	if not results:
		return {
			"state": "empty",
			"query": needle,
			"message": "No visible Procurement Console records match this search yet.",
			"results": [],
		}
	return {
		"state": "ready",
		"query": needle,
		"message": f"{len(results)} Procurement Console result{'s' if len(results) != 1 else ''} found.",
		"results": results,
	}


@frappe.whitelist()
def get_procurement_quick_find_suggestions(query: str, limit: int = QUICK_FIND_DEFAULT_LIMIT) -> dict[str, object]:
	ensure_authenticated()
	context = build_context()
	needle = _normalize_quick_find_query(query)
	if not has_procurement_access(context):
		return {
			"state": "restricted",
			"query": needle,
			"message": "Procurement Quick Find is restricted to procurement roles.",
			"groups": [],
			"results": [],
		}
	if len(needle) < QUICK_FIND_MIN_QUERY_LENGTH:
		return {
			"state": "idle",
			"query": needle,
			"message": "Type at least 2 characters to find suppliers, items, requests, RFQs, quotations, purchase orders, or reports.",
			"groups": [],
			"results": [],
		}

	bounded_limit = _quick_find_limit(limit)
	results = _build_procurement_quick_find_results(needle, bounded_limit)
	if not results:
		return {
			"state": "empty",
			"query": needle,
			"message": "No visible Procurement records match this search. Use directory filters for broader queue review.",
			"groups": [],
			"results": [],
		}
	return {
		"state": "ready",
		"query": needle,
		"message": f"{len(results)} visible Procurement result{'s' if len(results) != 1 else ''} found.",
		"groups": _quick_find_groups(results),
		"results": results,
	}


def _normalize_quick_find_query(query: object) -> str:
	return " ".join(cstr(query).replace("\x00", " ").split())[:80]


def _quick_find_limit(limit: object) -> int:
	try:
		value = int(limit or QUICK_FIND_DEFAULT_LIMIT)
	except Exception:
		value = QUICK_FIND_DEFAULT_LIMIT
	return max(1, min(QUICK_FIND_MAX_LIMIT, value))


def _build_procurement_quick_find_results(query: str, limit: int) -> list[dict[str, object]]:
	from . import common

	per_group_limit = max(2, min(5, limit))
	results: list[dict[str, object]] = []
	seen: set[tuple[str, str]] = set()
	for plan in _quick_find_plans():
		doctype = cstr(plan.get("doctype")).strip()
		if not doctype or not common.can_read(doctype):
			continue
		for row in _quick_find_rows(plan, query, per_group_limit):
			name = cstr(row.get("name")).strip()
			key = (cstr(plan.get("result_type")), name)
			if not name or key in seen:
				continue
			seen.add(key)
			results.append(_quick_find_result(plan, row))
			if len(results) >= limit:
				return results[:limit]
	for report_result in _quick_find_report_results(query, max(2, min(5, limit))):
		key = ("report", cstr(report_result.get("name")))
		if key in seen:
			continue
		seen.add(key)
		results.append(report_result)
		if len(results) >= limit:
			return results[:limit]
	return results[:limit]


def _quick_find_plans() -> list[dict[str, object]]:
	return [
		{
			"result_type": "supplier",
			"group_key": "suppliers",
			"doctype": "Supplier",
			"fields": ["name", "supplier_name", "supplier_group", "disabled", "modified"],
			"parent_fields": ["name", "supplier_name", "supplier_group"],
			"title_field": "supplier_name",
			"subtitle_fields": ["supplier_group"],
			"action_label": "Open supplier",
			"target": {"kind": "page", "route": "procurement-console-supplier"},
		},
		{
			"result_type": "buying_item",
			"group_key": "buying_items",
			"doctype": "Item",
			"fields": ["name", "item_name", "item_group", "brand", "stock_uom", "disabled", "modified"],
			"parent_fields": ["name", "item_name", "item_group", "brand"],
			"filters": [["Item", "is_purchase_item", "=", 1]],
			"title_field": "item_name",
			"subtitle_fields": ["item_group", "brand"],
			"action_label": "Open item",
			"target": {"kind": "page", "route": "procurement-console-item"},
		},
		{
			"result_type": "purchase_request",
			"group_key": "purchase_requests",
			"doctype": "Material Request",
			"fields": ["name", "title", "material_request_type", "status", "schedule_date", "company", "modified"],
			"parent_fields": ["name", "title", "status", "company"],
			"child_specs": [{"doctype": "Material Request Item", "parent_field": "parent", "fields": ["item_code", "item_name", "warehouse"]}],
			"filters": [["Material Request", "material_request_type", "=", "Purchase"]],
			"title_field": "name",
			"subtitle_fields": ["title", "status"],
			"action_label": "Review request",
			"target": {"kind": "page", "route": "procurement-console-purchase-request-review"},
		},
		{
			"result_type": "rfq",
			"group_key": "rfqs",
			"doctype": "Request for Quotation",
			"fields": ["name", "subject", "company", "status", "schedule_date", "modified"],
			"parent_fields": ["name", "subject", "company", "status"],
			"child_specs": [
				{"doctype": "Request for Quotation Supplier", "parent_field": "parent", "fields": ["supplier", "supplier_name"]},
				{"doctype": "Request for Quotation Item", "parent_field": "parent", "fields": ["item_code", "item_name", "warehouse", "material_request"]},
			],
			"title_field": "name",
			"subtitle_fields": ["subject", "status"],
			"action_label": "Review RFQ",
			"target": {"kind": "page", "route": "procurement-console-rfq-review"},
		},
		{
			"result_type": "supplier_quotation",
			"group_key": "supplier_quotations",
			"doctype": "Supplier Quotation",
			"fields": ["name", "supplier", "supplier_name", "status", "transaction_date", "valid_till", "grand_total", "currency", "modified"],
			"parent_fields": ["name", "supplier", "supplier_name", "status"],
			"child_specs": [{"doctype": "Supplier Quotation Item", "parent_field": "parent", "fields": ["item_code", "item_name", "request_for_quotation", "material_request"]}],
			"title_field": "name",
			"subtitle_fields": ["supplier_name", "supplier", "status"],
			"action_label": "Review quotation",
			"target": {"kind": "page", "route": "procurement-console-supplier-quotation-review"},
		},
		{
			"result_type": "purchase_order",
			"group_key": "purchase_orders",
			"doctype": "Purchase Order",
			"fields": ["name", "supplier", "supplier_name", "status", "workflow_state", "schedule_date", "transaction_date", "grand_total", "currency", "per_received", "per_billed", "modified"],
			"parent_fields": ["name", "supplier", "supplier_name", "status", "workflow_state"],
			"child_specs": [{"doctype": "Purchase Order Item", "parent_field": "parent", "fields": ["item_code", "item_name", "warehouse", "material_request", "supplier_quotation"]}],
			"title_field": "name",
			"subtitle_fields": ["supplier_name", "supplier", "status"],
			"action_label": "Open follow-up",
			"target": {"kind": "page", "route": "procurement-console-po-follow-up"},
		},
	]


def _quick_find_rows(plan: dict[str, object], query: str, limit: int) -> list[dict[str, object]]:
	from . import common

	doctype = cstr(plan.get("doctype")).strip()
	if not doctype:
		return []
	names = common.matching_parent_names_for_keyword(
		doctype,
		query,
		[cstr(field).strip() for field in plan.get("parent_fields") or []],
		list(plan.get("child_specs") or []),
		limit=max(limit * 4, 12),
	)
	if not names:
		return []
	filters = list(plan.get("filters") or [])
	filters.append([doctype, "name", "in", names[: max(limit * 4, 12)]])
	return common.get_list(
		doctype,
		fields=_available_fields(doctype, list(plan.get("fields") or ["name"])),
		filters=filters,
		order_by="modified desc",
		limit=limit,
	)


def _available_fields(doctype: str, fields: list[str]) -> list[str]:
	from . import common

	available = ["name"]
	seen = {"name"}
	for field in fields:
		fieldname = cstr(field).strip()
		if not fieldname or fieldname in seen:
			continue
		if fieldname == "name" or common.has_field(doctype, fieldname):
			available.append(fieldname)
			seen.add(fieldname)
	return available


def _quick_find_result(plan: dict[str, object], row: dict[str, object]) -> dict[str, object]:
	result_type = cstr(plan.get("result_type")).strip()
	group_key = cstr(plan.get("group_key")).strip()
	doctype = cstr(plan.get("doctype")).strip()
	name = cstr(row.get("name")).strip()
	title = cstr(row.get(cstr(plan.get("title_field")))).strip() or name
	subtitle = _join_values(row.get(field) for field in plan.get("subtitle_fields") or [])
	target = _target_with_name(dict(plan.get("target") or {}), name)
	preview = _quick_find_preview(result_type, row, target, cstr(plan.get("action_label")))
	return {
		"id": f"{result_type}:{name}",
		"result_type": result_type,
		"group_key": group_key,
		"group": QUICK_FIND_GROUP_LABELS.get(group_key, group_key.replace("_", " ").title()),
		"doctype": doctype,
		"name": name,
		"label": title,
		"title": title,
		"subtitle": subtitle,
		"meta": subtitle,
		"target": target,
		"preview": preview,
		"primary_action_label": cstr(plan.get("action_label")) or "Open",
	}


def _target_with_name(target: dict[str, object], name: str) -> dict[str, object]:
	if target.get("kind") == "page":
		payload = dict(target)
		payload["route_parts"] = [name]
		payload.setdefault("options", {})
		return payload
	return dict(target)


def _quick_find_preview(result_type: str, row: dict[str, object], target: dict[str, object], action_label: str) -> dict[str, object]:
	preview_builders = {
		"supplier": _supplier_quick_find_preview,
		"buying_item": _item_quick_find_preview,
		"purchase_request": _purchase_request_quick_find_preview,
		"rfq": _rfq_quick_find_preview,
		"supplier_quotation": _supplier_quotation_quick_find_preview,
		"purchase_order": _purchase_order_quick_find_preview,
	}
	builder = preview_builders.get(result_type)
	preview = builder(row) if builder else {"title": cstr(row.get("name")), "subtitle": "Procurement record", "facts": []}
	preview["target"] = target
	preview["primary_action_label"] = action_label or "Open"
	preview["boundary_note"] = preview.get("boundary_note") or "Productized Procurement route only. No native ERP form is opened."
	return preview


def _supplier_quick_find_preview(row: dict[str, object]) -> dict[str, object]:
	status = "Disabled" if cstr(row.get("disabled")) in {"1", "True", "true"} else "Active"
	return {
		"title": cstr(row.get("supplier_name")).strip() or cstr(row.get("name")),
		"subtitle": "Supplier buying context",
		"chips": [status],
		"facts": _facts(("Supplier ID", row.get("name")), ("Group", row.get("supplier_group")), ("Status", status)),
	}


def _item_quick_find_preview(row: dict[str, object]) -> dict[str, object]:
	status = "Disabled" if cstr(row.get("disabled")) in {"1", "True", "true"} else "Purchase-enabled"
	return {
		"title": cstr(row.get("item_name")).strip() or cstr(row.get("name")),
		"subtitle": "Item Buying Context",
		"chips": [status],
		"facts": _facts(("Item code", row.get("name")), ("Group", row.get("item_group")), ("Brand", row.get("brand")), ("UOM", row.get("stock_uom"))),
	}


def _purchase_request_quick_find_preview(row: dict[str, object]) -> dict[str, object]:
	return {
		"title": cstr(row.get("name")),
		"subtitle": cstr(row.get("title")).strip() or "Purchase request review",
		"chips": [cstr(row.get("status")).strip() or "Visible"],
		"facts": _facts(("Status", row.get("status")), ("Required by", row.get("schedule_date")), ("Company", row.get("company"))),
	}


def _rfq_quick_find_preview(row: dict[str, object]) -> dict[str, object]:
	return {
		"title": cstr(row.get("name")),
		"subtitle": cstr(row.get("subject")).strip() or "RFQ review",
		"chips": [cstr(row.get("status")).strip() or "Visible"],
		"facts": _facts(("Status", row.get("status")), ("Required by", row.get("schedule_date")), ("Company", row.get("company"))),
		"boundary_note": "Review RFQ in Procurement. Send remains governed by the deferred send policy.",
	}


def _supplier_quotation_quick_find_preview(row: dict[str, object]) -> dict[str, object]:
	return {
		"title": cstr(row.get("name")),
		"subtitle": cstr(row.get("supplier_name")).strip() or cstr(row.get("supplier")).strip() or "Supplier quotation review",
		"chips": [cstr(row.get("status")).strip() or "Visible"],
		"facts": _facts(("Supplier", row.get("supplier_name") or row.get("supplier")), ("Status", row.get("status")), ("Valid till", row.get("valid_till")), ("Total", _money_value(row))),
	}


def _purchase_order_quick_find_preview(row: dict[str, object]) -> dict[str, object]:
	status = cstr(row.get("workflow_state")).strip() or cstr(row.get("status")).strip() or "Visible"
	return {
		"title": cstr(row.get("name")),
		"subtitle": cstr(row.get("supplier_name")).strip() or cstr(row.get("supplier")).strip() or "Purchase order follow-up",
		"chips": [status],
		"facts": _facts(("Supplier", row.get("supplier_name") or row.get("supplier")), ("Status", status), ("Required by", row.get("schedule_date")), ("Total", _money_value(row)), ("Received", _percent_value(row.get("per_received"))), ("Billed", _percent_value(row.get("per_billed")))),
		"boundary_note": "Open buyer follow-up only. Receiving, billing, and payment remain outside this action.",
	}


def _quick_find_report_results(query: str, limit: int) -> list[dict[str, object]]:
	term = query.lower()
	results: list[dict[str, object]] = []
	for report in QUICK_FIND_REPORTS:
		search_text = " ".join([cstr(report.get("key")), cstr(report.get("title")), cstr(report.get("description")), cstr(report.get("boundary"))]).lower()
		if term not in search_text:
			continue
		key = cstr(report.get("key"))
		target = {"kind": "report_page", "report_key": key, "filters": {}}
		preview = {
			"title": cstr(report.get("title")),
			"subtitle": "Procurement report",
			"chips": ["Read-only"],
			"facts": _facts(("Purpose", report.get("description")), ("Boundary", report.get("boundary"))),
			"boundary_note": "Productized Procurement report route only. No native ERP report route is opened.",
			"target": target,
			"primary_action_label": "Open report",
		}
		results.append({
			"id": f"report:{key}",
			"result_type": "report",
			"group_key": "reports",
			"group": QUICK_FIND_GROUP_LABELS["reports"],
			"doctype": "Report",
			"name": key,
			"label": cstr(report.get("title")),
			"title": cstr(report.get("title")),
			"subtitle": cstr(report.get("description")),
			"meta": cstr(report.get("boundary")),
			"target": target,
			"preview": preview,
			"primary_action_label": "Open report",
		})
		if len(results) >= limit:
			break
	return results


def _quick_find_groups(results: list[dict[str, object]]) -> list[dict[str, object]]:
	groups: list[dict[str, object]] = []
	for group_key in QUICK_FIND_GROUP_ORDER:
		items = [item for item in results if item.get("group_key") == group_key]
		if items:
			groups.append({"key": group_key, "label": QUICK_FIND_GROUP_LABELS.get(group_key, group_key.replace("_", " ").title()), "results": items})
	return groups


def _facts(*pairs: tuple[str, object]) -> list[dict[str, str]]:
	facts: list[dict[str, str]] = []
	for label, value in pairs:
		text = cstr(value).strip()
		if text:
			facts.append({"label": label, "value": text})
	return facts[:6]


def _join_values(values: object) -> str:
	parts = [cstr(value).strip() for value in values if cstr(value).strip()]
	return " | ".join(parts[:3])


def _money_value(row: dict[str, object]) -> str:
	amount = cstr(row.get("grand_total")).strip()
	if not amount:
		return ""
	currency = cstr(row.get("currency")).strip()
	return f"{amount} {currency}".strip()


def _percent_value(value: object) -> str:
	text = cstr(value).strip()
	if not text:
		return ""
	try:
		number = float(text)
	except Exception:
		return text
	return f"{number:g}%"


def _build_procurement_workspace_search_results(query: str, limit: int) -> list[dict[str, object]]:
	from . import common

	per_doctype_limit = max(2, min(8, int(limit or 12)))
	search_plan = [
		{
			"doctype": "Supplier",
			"fields": ["name", "supplier_name", "supplier_group", "modified"],
			"search_fields": ["name", "supplier_name"],
			"queue_key": "supplier_directory",
			"keyword_field": "supplier_name",
			"label_field": "supplier_name",
			"meta_fields": ["supplier_group"],
		},
		{
			"doctype": "Item",
			"fields": ["name", "item_name", "item_group", "modified"],
			"search_fields": ["name", "item_name"],
			"queue_key": "buying_item_directory",
			"keyword_field": "item_name",
			"label_field": "item_name",
			"meta_fields": ["item_group"],
			"filters": [["Item", "is_purchase_item", "=", 1]],
		},
		{
			"doctype": "Material Request",
			"fields": ["name", "title", "material_request_type", "status", "modified"],
			"search_fields": ["name", "title"],
			"queue_key": "purchase_request_directory",
			"keyword_field": "name",
			"label_field": "name",
			"meta_fields": ["title", "status"],
			"filters": [["Material Request", "material_request_type", "=", "Purchase"]],
		},
		{
			"doctype": "Request for Quotation",
			"fields": ["name", "company", "status", "modified"],
			"search_fields": ["name"],
			"queue_key": "rfq_directory",
			"keyword_field": "name",
			"label_field": "name",
			"meta_fields": ["status", "company"],
		},
		{
			"doctype": "Supplier Quotation",
			"fields": ["name", "supplier", "supplier_name", "status", "modified"],
			"search_fields": ["name", "supplier", "supplier_name"],
			"queue_key": "supplier_quotation_directory",
			"keyword_field": "name",
			"label_field": "name",
			"meta_fields": ["supplier_name", "status"],
		},
		{
			"doctype": "Purchase Order",
			"fields": ["name", "supplier", "supplier_name", "status", "modified"],
			"search_fields": ["name", "supplier", "supplier_name"],
			"queue_key": "purchase_order_directory",
			"keyword_field": "name",
			"label_field": "name",
			"meta_fields": ["supplier_name", "status"],
		},
	]
	results: list[dict[str, object]] = []
	seen: set[tuple[str, str]] = set()
	for plan in search_plan:
		if not common.can_read(plan["doctype"]):
			continue
		for row in _search_procurement_rows(plan, query, per_doctype_limit):
			key = (cstr(plan["doctype"]), cstr(row.get("name")))
			if not key[1] or key in seen:
				continue
			seen.add(key)
			results.append(_search_result_from_row(plan, row))
			if len(results) >= int(limit or 12):
				return results
	return results[: int(limit or 12)]


def _search_procurement_rows(plan: dict[str, object], query: str, limit: int) -> list[dict[str, object]]:
	from . import common

	rows: list[dict[str, object]] = []
	base_filters = list(plan.get("filters") or [])
	for fieldname in plan.get("search_fields") or []:
		filters = list(base_filters)
		filters.append([cstr(plan["doctype"]), cstr(fieldname), "like", f"%{query}%"])
		rows.extend(common.get_list(cstr(plan["doctype"]), fields=list(plan.get("fields") or ["name"]), filters=filters, order_by="modified desc", limit=limit))
	return rows


def _search_result_from_row(plan: dict[str, object], row: dict[str, object]) -> dict[str, object]:
	name = cstr(row.get("name")).strip()
	label_field = cstr(plan.get("label_field")).strip()
	keyword_field = cstr(plan.get("keyword_field")).strip()
	label = cstr(row.get(label_field)).strip() or name
	keyword = cstr(row.get(keyword_field)).strip() or name
	meta_parts = [cstr(row.get(field)).strip() for field in plan.get("meta_fields") or []]
	meta = " | ".join(part for part in meta_parts if part)
	return {
		"doctype": plan.get("doctype"),
		"name": name,
		"label": label,
		"meta": meta,
		"target": {"kind": "worklist", "queue_key": plan.get("queue_key"), "filters": {"keyword": keyword}},
	}


def _build_phase1_overview() -> dict[str, object]:
	from . import items, purchase_order_follow_up, purchase_orders, requests, sourcing, suppliers

	requests_to_source = requests.count_purchase_requests_to_source()
	requests_total = requests.count_purchase_request_directory()
	orders_open = purchase_orders.count_purchase_orders_open()
	orders_total = purchase_orders.count_purchase_order_directory()
	orders_pending_approval = purchase_orders.count_purchase_orders_pending_approval()
	orders_follow_up = purchase_order_follow_up.build_purchase_order_follow_up_summary()
	orders_late = orders_follow_up["overdue"]
	orders_due_soon = orders_follow_up["due_soon"]
	orders_partially_received = orders_follow_up["partially_received"]
	orders_not_billed_visibility = orders_follow_up["billing_visibility"]
	orders_supplier_follow_up = orders_follow_up["supplier_follow_up"]
	suppliers_total = suppliers.count_visible_suppliers()
	buying_items_total = items.count_buying_items()
	rfqs_total = sourcing.count_rfq_directory()
	rfqs_awaiting_response = sourcing.count_rfqs_awaiting_supplier_response()
	supplier_quotations_total = sourcing.count_supplier_quotation_directory()
	supplier_quotations_to_compare = sourcing.count_supplier_quotations_to_compare()
	supplier_quotations_expiring = sourcing.count_supplier_quotations_expiring()

	return {
		"work": {
			"requests_to_source": {
				"state": "live",
				"value": requests_to_source,
				"note": "Submitted purchase requests not fully ordered.",
				"badgeClass": "attention" if requests_to_source else "review",
			},
			"purchase_orders_pending_approval": {
				"state": "live",
				"value": orders_pending_approval,
				"note": "Purchase Orders waiting on purchase approval.",
				"badgeClass": "blocker" if orders_pending_approval else "review",
			},
			"purchase_orders_late_or_unreceived": {
				"state": "live",
				"value": orders_late,
				"note": "Submitted Purchase Orders with overdue open item lines.",
				"badgeClass": "attention" if orders_late else "review",
			},
			"purchase_orders_due_soon": {
				"state": "live",
				"value": orders_due_soon,
				"note": "Open item lines due within seven days.",
				"badgeClass": "attention" if orders_due_soon else "review",
			},
			"purchase_orders_overdue": {
				"state": "live",
				"value": orders_late,
				"note": "Open item lines past required date.",
				"badgeClass": "blocker" if orders_late else "review",
			},
			"purchase_orders_partially_received": {
				"state": "live",
				"value": orders_partially_received,
				"note": "Orders with some receipt but incomplete fulfillment.",
				"badgeClass": "attention" if orders_partially_received else "review",
			},
			"purchase_orders_not_billed_visibility": {
				"state": "live",
				"value": orders_not_billed_visibility,
				"note": "Received orders not fully billed; read-only follow-up.",
				"badgeClass": "review",
			},
			"purchase_orders_supplier_follow_up": {
				"state": "live",
				"value": orders_supplier_follow_up,
				"note": "Orders needing buyer follow-up.",
				"badgeClass": "blocker" if orders_supplier_follow_up else "review",
			},
			"purchase_orders_open": {
				"state": "live",
				"value": orders_open,
				"note": "Submitted Purchase Orders still active.",
				"badgeClass": "review",
			},
			"rfqs_awaiting_supplier_response": {
				"state": "live",
				"value": rfqs_awaiting_response,
				"note": "Submitted RFQs with pending supplier responses.",
				"badgeClass": "attention" if rfqs_awaiting_response else "review",
			},
			"supplier_quotations_to_compare": {
				"state": "live",
				"value": supplier_quotations_to_compare,
				"note": "Submitted Supplier Quotations available for comparison.",
				"badgeClass": "attention" if supplier_quotations_to_compare else "review",
			},
			"supplier_quotations_expiring": {
				"state": "live",
				"value": supplier_quotations_expiring,
				"note": "Supplier Quotations expiring within seven days.",
				"badgeClass": "blocker" if supplier_quotations_expiring else "review",
			},
		},
		"directories": {
			"supplier_directory": {
				"state": "live",
				"value": suppliers_total,
				"note": "Supplier records visible to this user.",
				"badgeClass": "review",
			},
			"purchase_request_directory": {
				"state": "live",
				"value": requests_total,
				"note": "Purchase Material Requests visible to this user.",
				"badgeClass": "review",
			},
			"purchase_order_directory": {
				"state": "live",
				"value": orders_total,
				"note": "Purchase Orders visible to this user.",
				"badgeClass": "review",
			},
			"rfq_directory": {
				"state": "live",
				"value": rfqs_total,
				"note": "RFQ records visible to this user.",
				"badgeClass": "review",
			},
			"supplier_quotation_directory": {
				"state": "live",
				"value": supplier_quotations_total,
				"note": "Supplier Quotation records visible to this user.",
				"badgeClass": "review",
			},
			"buying_item_directory": {
				"state": "live",
				"value": buying_items_total,
				"note": "Purchase-enabled items visible to this user.",
				"badgeClass": "review",
			},
		},
		"queues": {
			"requests_to_source": requests_to_source,
			"purchase_orders_pending_approval": orders_pending_approval,
			"purchase_orders_late_or_unreceived": orders_late,
			"purchase_orders_due_soon": orders_due_soon,
			"purchase_orders_overdue": orders_late,
			"purchase_orders_partially_received": orders_partially_received,
			"purchase_orders_not_billed_visibility": orders_not_billed_visibility,
			"purchase_orders_supplier_follow_up": orders_supplier_follow_up,
			"purchase_orders_open": orders_open,
			"rfqs_awaiting_supplier_response": rfqs_awaiting_response,
			"supplier_quotations_to_compare": supplier_quotations_to_compare,
			"supplier_quotations_expiring": supplier_quotations_expiring,
		},
		"insights": {
			"requests_to_source": {
				"state": "live",
				"value": requests_to_source,
				"note": "Need sourcing action.",
			},
			"purchase_orders_pending_approval": {
				"state": "live",
				"value": orders_pending_approval,
				"note": "Need purchase approval review.",
			},
			"purchase_orders_late_or_unreceived": {
				"state": "live",
				"value": orders_late,
				"note": "Need supplier follow-up.",
			},
			"purchase_orders_due_soon": {
				"state": "live",
				"value": orders_due_soon,
				"note": "Need pre-due follow-up.",
			},
			"purchase_orders_overdue": {
				"state": "live",
				"value": orders_late,
				"note": "Need urgent follow-up.",
			},
			"purchase_orders_supplier_follow_up": {
				"state": "live",
				"value": orders_supplier_follow_up,
				"note": "Need buyer follow-up.",
			},
			"supplier_quotations_expiring": {
				"state": "live",
				"value": supplier_quotations_expiring,
				"note": "Need quote validity review.",
			},
		},
		"reports_catalog": [
			{
				"key": "supplier_quotation_comparison",
				"label": "Supplier Quotation Comparison",
				"description": "Governed comparison of quoted supplier prices and validity.",
			}
		],
	}


def _build_create_action_payload(context: dict[str, object]) -> dict[str, object]:
	from . import common

	# Supplier and Item master-data creation are deliberately deferred.
	# Phase 7D1 closes normal-role native ERP form escapes; create actions
	# must resolve to productized Procurement routes only.
	plan = [
		{
			"key": "new_purchase_request",
			"title": "New Purchase Request",
			"doctype": "Material Request",
			"target": {"kind": "page", "route": "procurement-console-purchase-request-form", "route_parts": ["new"]},
			"note": "Starts a managed Purchase Request draft.",
		},
		{
			"key": "new_rfq",
			"title": "New RFQ",
			"doctype": "Request for Quotation",
			"target": {"kind": "page", "route": "procurement-console-rfq-form", "route_parts": ["new"]},
			"note": "Starts a managed RFQ request.",
		},
		{
			"key": "new_supplier_quotation",
			"title": "New Supplier Quotation",
			"doctype": "Supplier Quotation",
			"target": {"kind": "page", "route": "procurement-console-supplier-quotation-form", "route_parts": ["new"]},
			"note": "Starts a managed Supplier Quotation draft.",
		},
		{
			"key": "new_purchase_order",
			"title": "New Purchase Order",
			"doctype": "Purchase Order",
			"target": {"kind": "page", "route": "procurement-console-purchase-order-form", "route_parts": ["new"]},
			"note": "Starts a managed Purchase Order draft.",
		},
	]
	actions: list[dict[str, object]] = []
	targets: dict[str, object] = {}
	for item in plan:
		doctype = cstr(item.get("doctype")).strip()
		if not doctype or not common.can_create(doctype):
			continue
		key = cstr(item.get("key")).strip()
		if key in {"new_purchase_request", "new_rfq", "new_supplier_quotation", "new_purchase_order"} and not common.can_write(doctype):
			continue
		actions.append(
			{
				"key": key,
				"title": item.get("title"),
				"label": item.get("title"),
				"variant": "primary" if key in {"new_purchase_request", "new_rfq", "new_supplier_quotation", "new_purchase_order"} else "secondary",
				"category": "create",
				"note": item.get("note"),
			}
		)
		target = item.get("target")
		if isinstance(target, dict) and target.get("kind") == "page":
			targets[key] = dict(target)
	return {"create_actions": actions, "action_targets": targets}
